"""
The one-shot dashboard pipeline: case -> dashboard -> VLM -> parse -> score.

This is the C0 controller of RQ2 and the workhorse of RQ1/RQ3/RQ4. The agentic
controllers (M3) reuse everything here except the single-turn call.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from vlmrca.agent.trajectory import Episode, TrajectoryWriter, Turn
from vlmrca.eval.metrics import summarize
from vlmrca.eval.scoring import is_granularity_aware_hit
from RQs.RQ1.src.renderer.dashboard import CaseRenderView, DashboardConfig, compile_dashboard
from vlmrca.upstream import normalize_service, parse_answer, upstream_commit
from vlmrca.vlm.client import call_vlm
from vlmrca.vlm.configs import VLMConfig, get_config
from vlmrca.vlm.prompt import build_prompt


def score_prediction(predicted: List[str], case) -> Dict[str, Any]:
    """
    Score a ranked prediction against a case, honouring multi-root-cause labels.

    AegisLab cases usually list several acceptable root causes. Per the upstream
    Aegislab convention, credit is given for the best-ranked prediction that
    matches ANY accepted label, and service-level leniency (upstream's
    is_service_level_hit) lets a pod name match its service.
    """
    accepted = [case.ground_truth]
    accepted += list((case.metadata or {}).get("ground_truth_candidates", []) or [])
    accepted_norm = {normalize_service(a) for a in accepted if a}

    rank = None
    for i, p in enumerate(predicted[:5], start=1):
        pn = normalize_service(p)
        if pn in accepted_norm or any(
            is_granularity_aware_hit(pn, a) for a in accepted_norm
        ):
            rank = i
            break

    return {
        "predicted": predicted[:5],
        "rank": rank,
        "mrr": (1.0 / rank) if rank else 0.0,
        "top1": rank == 1,
        "top3": bool(rank and rank <= 3),
        "top5": bool(rank and rank <= 5),
        "ac1": float(bool(rank and rank <= 1)),
        "ac3": float(bool(rank and rank <= 3)),
        "ac5": float(bool(rank and rank <= 5)),
        "avg3": (
            sum(float(bool(rank and rank <= k)) for k in range(1, 4)) / 3.0
        ),
        "avg5": (
            sum(float(bool(rank and rank <= k)) for k in range(1, 6)) / 5.0
        ),
        "accepted": sorted(accepted_norm),
    }


def _render_cached(
    view: CaseRenderView,
    cfg: DashboardConfig,
    case_id: str,
    cache_dir: Optional[Path],
):
    """
    Render the dashboard, or load a byte-identical prior render from disk.

    The renderer is pure and deterministic in (view, cfg) (invariant 3), so a
    render is fully addressed by (case_id, cfg.fingerprint()). Caching lets an
    N-model bake-off or an inference re-run reuse one render instead of
    recompiling matplotlib every time. Returns (png_bytes, manifest, hit).

    When caching is enabled the manifest is round-tripped through JSON on the
    miss path too, so the first (miss) run and later (hit) runs feed the model
    an identical prompt. With no cache dir, legacy behaviour is preserved exactly.
    """
    if cache_dir is None:
        png, manifest = compile_dashboard(view, cfg)
        return png, manifest, False

    cache_dir = Path(cache_dir)
    key = f"{case_id}__{cfg.fingerprint()}"
    png_path = cache_dir / f"{key}.png"
    man_path = cache_dir / f"{key}.manifest.json"
    if png_path.exists() and man_path.exists():
        return png_path.read_bytes(), json.loads(man_path.read_text()), True

    png, manifest = compile_dashboard(view, cfg)
    cache_dir.mkdir(parents=True, exist_ok=True)
    man_json = json.dumps(manifest, indent=2, default=str)
    png_path.write_bytes(png)
    man_path.write_text(man_json)
    return png, json.loads(man_json), False


def run_one_case(
    case,
    model: str | VLMConfig = "mock",
    dashboard_cfg: Optional[DashboardConfig] = None,
    modality: str = "hybrid",
    experiment: str = "smoke",
    render_dir: Optional[Path] = None,
    render_cache_dir: Optional[Path] = None,
) -> Episode:
    """Render, ask, parse, score — one case, one turn."""
    dashboard_cfg = dashboard_cfg or DashboardConfig()
    # A VLMConfig may be passed instead of a tag when an arm overrides model
    # settings (thinking on, a longer budget). The episode still records the tag.
    model_tag = model.tag if isinstance(model, VLMConfig) else model
    t0 = time.time()

    view = CaseRenderView.from_case(case)
    png, manifest, cache_hit = _render_cached(
        view, dashboard_cfg, case.case_id, render_cache_dir
    )

    image_refs: List[str] = []
    if render_dir is not None:
        render_dir = Path(render_dir)
        render_dir.mkdir(parents=True, exist_ok=True)
        img_path = render_dir / f"{case.case_id}__{dashboard_cfg.name}.png"
        img_path.write_bytes(png)
        (render_dir / f"{case.case_id}__{dashboard_cfg.name}.manifest.json").write_text(
            json.dumps(manifest, indent=2, default=str)
        )
        image_refs.append(str(img_path))

    built = build_prompt(view, png, manifest, case, modality=modality)
    prompt_chars = sum(len(p["text"]) for p in built["parts"] if p["type"] == "text")

    err = None
    stop_reason = None
    try:
        resp = call_vlm(built["parts"], model=model, system=built["system"])
        text = resp.text
        tin, tout, lat = resp.input_tokens, resp.output_tokens, resp.latency_s
        stop_reason = (resp.raw or {}).get("stopReason") or (resp.raw or {}).get("finish_reason")
    except Exception as exc:  # noqa: BLE001
        err = f"{type(exc).__name__}: {exc}"
        text, tin, tout, lat = "", 0, 0, 0.0

    predicted = parse_answer(text) if text else []
    scored = score_prediction(predicted, case)

    turn = Turn(
        turn_idx=0,
        action="answer",
        prompt_chars=prompt_chars,
        response=text,
        input_tokens=tin,
        output_tokens=tout,
        latency_s=lat,
        images=image_refs,
        error=err,
    )
    return Episode(
        case_id=case.case_id,
        dataset=case.dataset,
        model=model_tag,
        experiment=experiment,
        ground_truth=case.ground_truth,
        fault_type=case.fault_type,
        predicted=scored["predicted"],
        mrr=scored["mrr"],
        top1=scored["top1"],
        top3=scored["top3"],
        top5=scored["top5"],
        ac1=scored["ac1"],
        ac3=scored["ac3"],
        ac5=scored["ac5"],
        avg3=scored["avg3"],
        avg5=scored["avg5"],
        # A model that answers with no parseable ranking is a pipeline failure,
        # not a wrong answer; keeping the two apart is what the M1 parse gate reads.
        parse_ok=bool(predicted) and err is None,
        turns=[turn],
        total_input_tokens=tin,
        total_output_tokens=tout,
        wall_clock_s=time.time() - t0,
        config_fingerprint=dashboard_cfg.fingerprint(),
        upstream_commit=upstream_commit(),
        extra={
            "modality": modality,
            "rank": scored["rank"],
            "error": err,
            "stop_reason": stop_reason,
            "render_cache_hit": cache_hit,
        },
    )


def _failed_episode(case, model, experiment, cfg, exc) -> Episode:
    """
    A crashed case, recorded rather than lost.

    parse_ok is False so it counts against the parse-rate gate — a run with
    crashes should not look clean.
    """
    return Episode(
        case_id=getattr(case, "case_id", "unknown"),
        dataset=getattr(case, "dataset", "unknown"),
        model=model,
        experiment=experiment,
        ground_truth=getattr(case, "ground_truth", ""),
        fault_type=getattr(case, "fault_type", ""),
        parse_ok=False,
        config_fingerprint=cfg.fingerprint(),
        upstream_commit=upstream_commit(),
        extra={"error": f"{type(exc).__name__}: {exc}", "crashed": True},
    )


def run_experiment(
    cases: Iterable,
    model: str = "mock",
    dashboard_cfg: Optional[DashboardConfig] = None,
    modality: str = "hybrid",
    experiment: str = "smoke",
    out_dir: Optional[Path] = None,
    save_renders: bool = True,
    render_cache_dir: Optional[Path] = None,
    verbose: bool = True,
    model_cfg: Optional[VLMConfig] = None,
    max_consecutive_failures: int = 5,
) -> Dict[str, Any]:
    """
    Run the pipeline over a set of cases and write trajectories + summary.

    `max_consecutive_failures` aborts the run when the backend has plainly gone
    away. Without it a dead server is indistinguishable from a bad model: the
    qwen3.6-27b bake-off cell lost its vLLM server after case 3, failed the
    remaining 17 cases in about seven seconds each, scored every one of them 0,
    and reported MRR 0.050 -- a number that then reached a devlog and a design
    doc as if it measured the model. Partial results are still written, so an
    aborted run is resumable and honest about its own coverage.
    """
    dashboard_cfg = dashboard_cfg or DashboardConfig()
    out_dir = Path(out_dir or Path("results") / experiment)
    out_dir.mkdir(parents=True, exist_ok=True)
    traj_dir = out_dir / "trajectories"
    render_dir = (out_dir / "renders") if save_renders else None

    header = {
        "experiment": experiment,
        "model": model,
        "modality": modality,
        "dashboard_config": asdict(dashboard_cfg),
        "config_fingerprint": dashboard_cfg.fingerprint(),
        "upstream_commit": upstream_commit(),
        "model_config": asdict(model_cfg or get_config(model)),
    }

    episodes: List[Episode] = []
    consecutive_failures = 0
    aborted: Optional[str] = None
    with TrajectoryWriter(traj_dir / f"{experiment}__{model}.jsonl", header=header) as w:
        for i, case in enumerate(cases, start=1):
            try:
                ep = run_one_case(
                    case,
                    model=model_cfg or model,
                    dashboard_cfg=dashboard_cfg,
                    modality=modality,
                    experiment=experiment,
                    render_dir=render_dir,
                    render_cache_dir=render_cache_dir,
                )
            except Exception as exc:  # noqa: BLE001
                # One malformed case must not discard the whole run. A crash at
                # case 7 of 20 previously lost the six completed results as well,
                # because the summary is only written at the end.
                ep = _failed_episode(case, model, experiment, dashboard_cfg, exc)
                print(f"[{i:3d}] CRASH {case.case_id}: {type(exc).__name__}: {exc}", flush=True)
            w.write_episode(ep)
            episodes.append(ep)
            if verbose:
                mark = "ok " if ep.parse_ok else "ERR"
                print(
                    f"[{i:3d}] {mark} {ep.case_id:<44} gt={ep.ground_truth:<22} "
                    f"pred={(ep.predicted or ['-'])[0]:<22} rr={ep.mrr:.2f} "
                    f"tok={ep.total_input_tokens + ep.total_output_tokens}",
                    flush=True,
                )

            # A call that never reached the model is a backend failure, not a
            # wrong answer. Any parsed response resets the counter.
            if (ep.extra or {}).get("error") and not ep.predicted:
                consecutive_failures += 1
            else:
                consecutive_failures = 0
            if max_consecutive_failures and consecutive_failures >= max_consecutive_failures:
                aborted = (
                    f"{consecutive_failures} consecutive backend failures at case {i}; "
                    f"last error: {(ep.extra or {}).get('error')}"
                )
                print(f"\nABORTED: {aborted}", flush=True)
                print(
                    f"  {len(episodes)} of the requested cases completed and were written.\n"
                    f"  Check the vLLM server log before trusting anything in this run.",
                    flush=True,
                )
                break

    if render_cache_dir is not None and verbose:
        hits = sum(1 for e in episodes if (e.extra or {}).get("render_cache_hit"))
        print(f"render cache: {hits} hit / {len(episodes) - hits} miss "
              f"({render_cache_dir})", flush=True)

    summary = summarize([e.to_json() for e in episodes])
    summary["experiment"] = experiment
    summary["model"] = model
    summary["modality"] = modality
    summary["dashboard_config"] = asdict(dashboard_cfg)
    summary["model_config"] = asdict(model_cfg or get_config(model))
    if aborted:
        # Stated in the summary, not only on stdout, so a partial run cannot be
        # aggregated later as if it had covered the whole case list.
        summary["aborted"] = aborted
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary

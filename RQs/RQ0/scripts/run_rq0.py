#!/usr/bin/env python3
"""Resumable RQ0 inference runner for validation, determinism and formal runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from vlmrca.eval.run_experiment import score_prediction
from vlmrca.processed import load_processed_case
from vlmrca.render.dashboard import CaseRenderView, compile_dashboard, opaque_incident_id
from vlmrca.render.presets import make_dashboard_config
from vlmrca.rq0.evidence import (
    InputArm,
    build_canonical_evidence,
    build_rq0_prompt,
    evidence_text,
    representation_audit,
    structured_jsonl,
)
from vlmrca.upstream import check_upstream_pin, parse_answer
from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens
from vlmrca.vlm.configs import get_config

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_equal_information_equal_compute_v1"
ARM_BY_LETTER: Dict[str, InputArm] = {
    "A": "visual_text_topology",
    "B": "text_only",
    "C": "flat_structured",
}
ORDERS = ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")


class GPUMonitor:
    """Sample GPU activity/memory during one request without requiring NVML."""

    def __init__(self, interval_s: float = 0.25):
        self.interval_s = interval_s
        self.samples: List[tuple[float, float, float]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self):
        def sample() -> None:
            while not self._stop.is_set():
                start = time.monotonic()
                try:
                    out = subprocess.run(
                        [
                            "nvidia-smi",
                            "--query-gpu=utilization.gpu,memory.used",
                            "--format=csv,noheader,nounits",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    util, memory = out.stdout.strip().splitlines()[0].split(",")[:2]
                    self.samples.append((start, float(util), float(memory)))
                except Exception:
                    pass
                self._stop.wait(self.interval_s)

        self._thread = threading.Thread(target=sample, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def summary(self) -> Dict[str, Any]:
        active = sum(
            self.interval_s for _ts, util, _memory in self.samples if util > 0
        )
        return {
            "gpu_active_time_s_sampled": round(active, 3),
            "peak_gpu_memory_mib_sampled": max(
                (memory for _ts, _util, memory in self.samples), default=None
            ),
            "gpu_samples": len(self.samples),
            "gpu_sampling_interval_s": self.interval_s,
        }


def _sha(data: bytes | str | Path) -> str:
    if isinstance(data, Path):
        raw = data.read_bytes()
    else:
        raw = data.encode() if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()


def _implementation_hash() -> str:
    # Hash canonical post-migration paths. Historical digests are retained in
    # their original artifacts and mapped by the contract-migration manifest.
    paths = [
        "RQs/vlmrca/processed.py",
        "RQs/vlmrca/render/dashboard.py",
        "RQs/vlmrca/render/kpi_select.py",
        "RQs/vlmrca/render/onset.py",
        "RQs/vlmrca/render/panels.py",
        "RQs/vlmrca/render/presets.py",
        "RQs/vlmrca/rq0/evidence.py",
        "RQs/vlmrca/vlm/client.py",
        "RQs/vlmrca/eval/run_experiment.py",
        "RQs/RQ0/scripts/run_rq0.py",
    ]
    digest = hashlib.sha256()
    for relative in paths:
        path = ROOT / relative
        digest.update(relative.encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def _git_state() -> Dict[str, Any]:
    """Freeze the exact local source state, including an uncommitted patch."""
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        diff = subprocess.run(
            ["git", "diff", "--binary", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
        return {
            "git_head": head,
            "git_dirty": bool(status),
            "git_status_sha256": _sha(status),
            "git_tracked_diff_sha256": _sha(diff),
        }
    except Exception as exc:  # noqa: BLE001
        return {"git_state_error": f"{type(exc).__name__}: {exc}"}


def _case_rows(roster: Dict[str, Any], partition: str, datasets: Iterable[str]):
    for dataset in datasets:
        values = roster["partitions"][partition].get(dataset, [])
        for value in values:
            yield dataset, value["case_id"] if isinstance(value, dict) else value


def _order(opaque_id: str) -> str:
    return ORDERS[int(hashlib.sha256(opaque_id.encode()).hexdigest(), 16) % len(ORDERS)]


def _balanced_formal_orders(roster: Dict[str, Any]) -> Dict[str, str]:
    """Exactly 40 incidents per order within each 240-case dataset."""
    mapping = {}
    for items in roster["partitions"]["formal"].values():
        ordered = sorted(
            (item["opaque_incident_id"] for item in items),
            key=lambda opaque: hashlib.sha256(opaque.encode()).hexdigest(),
        )
        for index, opaque in enumerate(ordered):
            mapping[opaque] = ORDERS[index % len(ORDERS)]
    return mapping


def _completed(path: Path) -> set[tuple[str, str]]:
    done = set()
    if not path.is_file():
        return done
    for line in path.read_text(errors="replace").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("record_type") == "episode":
            done.add((record["case_id"], record["arm"]))
    return done


def _write_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        handle.flush()


def _append_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()


def _conversation(
    case_id: str,
    opaque_id: str,
    arm: str,
    built: Dict[str, Any],
    image_ref: str | None,
    response: str,
    result: Dict[str, Any],
) -> str:
    parts = []
    for part in built["parts"]:
        if part["type"] == "image":
            parts.append(f"[image: {image_ref}]")
        else:
            parts.append(part["text"])
    return (
        f"# RQ0 conversation — {opaque_id} — {arm}\n\n"
        f"Private evaluator case id: `{case_id}`\n\n"
        "## System\n\n"
        + built["system"]
        + "\n\n## User\n\n"
        + "\n\n".join(parts)
        + "\n\n## Assistant\n\n"
        + (response or "[no response]")
        + "\n\n## Result\n\n```json\n"
        + json.dumps(result, indent=2, ensure_ascii=False, default=str)
        + "\n```\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="mock")
    parser.add_argument(
        "--partition", choices=("development", "validation", "formal"), default="validation"
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["re2_ob", "aiops2022", "aiops2025"],
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--replicate", default="main")
    parser.add_argument("--out-root", type=Path, default=ROOT / "RQs/RQ0/results")
    parser.add_argument("--max-consecutive-infrastructure-failures", type=int, default=5)
    args = parser.parse_args()

    roster = json.loads(
        (ROOT / "RQs" / "RQ0" / "configs" / "partition_roster.json").read_text()
    )
    formal_orders = _balanced_formal_orders(roster)
    selected = list(_case_rows(roster, args.partition, args.datasets))
    if args.limit:
        selected = selected[: args.limit]
    cfg = make_dashboard_config("rq0_v6")
    model_cfg = get_config(args.model)
    run_name = f"{args.model}__{args.partition}__{args.replicate}"
    run_dir = args.out_root / EXPERIMENT / run_name
    trajectory = run_dir / "trajectories" / "episodes.jsonl"
    detailed_log = run_dir / "logs" / "detailed.jsonl"
    brief_log = run_dir / "logs" / "brief.log"
    completed = _completed(trajectory)
    run_dir.mkdir(parents=True, exist_ok=True)

    qualification_dir = (
        args.out_root / EXPERIMENT / f"qualification_{args.partition}"
    )
    qualification_report_path = qualification_dir / "qualification_report.json"
    qualification_report_sha256 = None
    qualification_inventory_sha256 = None
    qualification_token_budget_sha256 = None
    qualification_determinism_sha256: Dict[str, str] = {}
    use_frozen_qualification = False
    if args.partition == "formal":
        if not qualification_report_path.is_file():
            raise RuntimeError("formal inference blocked: qualification report is absent")
        qualification_bytes = qualification_report_path.read_bytes()
        qualification_report = json.loads(qualification_bytes)
        if (
            not qualification_report.get("all_passed")
            or qualification_report.get("requested") != 720
            or qualification_report.get("formal_roster_sha256")
            != roster["formal_roster_sha256"]
        ):
            raise RuntimeError(
                "formal inference blocked: full 720-case qualification did not pass"
            )
        qualification_report_sha256 = _sha(qualification_bytes)
        inventory_path = qualification_dir / "artifact_inventory.json"
        if not inventory_path.is_file():
            raise RuntimeError("formal inference blocked: artifact inventory is absent")
        inventory_bytes = inventory_path.read_bytes()
        inventory = json.loads(inventory_bytes)
        if (
            not inventory.get("all_passed")
            or inventory.get("case_count") != 720
            or inventory.get("file_count") != 2880
            or inventory.get("formal_roster_sha256")
            != roster["formal_roster_sha256"]
            or inventory.get("qualification_report_sha256")
            != qualification_report_sha256
        ):
            raise RuntimeError(
                "formal inference blocked: frozen artifact inventory did not pass"
            )
        qualification_inventory_sha256 = _sha(inventory_bytes)
        token_budget_path = qualification_dir / f"token_budget_{args.model}.json"
        if not token_budget_path.is_file():
            raise RuntimeError(
                f"formal inference blocked: {args.model} token-budget qualification is absent"
            )
        token_budget_bytes = token_budget_path.read_bytes()
        token_budget = json.loads(token_budget_bytes)
        if (
            not token_budget.get("all_fit")
            or token_budget.get("model") != args.model
            or token_budget.get("requested_cases") != 720
            or token_budget.get("requested_prompts") != 2160
            or token_budget.get("max_model_len") != 32768
            or token_budget.get("max_output_tokens") != 16384
            or token_budget.get("artifact_inventory_sha256")
            != qualification_inventory_sha256
            or token_budget.get("evidence_serializer_sha256")
            != _sha(ROOT / "RQs" / "vlmrca" / "rq0" / "evidence.py")
        ):
            raise RuntimeError(
                f"formal inference blocked: {args.model} token-budget gate did not pass"
            )
        qualification_token_budget_sha256 = _sha(token_budget_bytes)
        determinism_dir = args.out_root / EXPERIMENT / "qualification_determinism"
        for scope in ("same_process", "cross_process"):
            determinism_path = determinism_dir / f"{args.model}__{scope}.json"
            if not determinism_path.is_file():
                raise RuntimeError(
                    f"formal inference blocked: {args.model} {scope} "
                    "determinism report is absent"
                )
            determinism_bytes = determinism_path.read_bytes()
            determinism = json.loads(determinism_bytes)
            if (
                not determinism.get("pass")
                or determinism.get("expected_pairs") != 60
                or determinism.get("n_paired") != 60
                or determinism.get("n_mismatched") != 0
                or not determinism.get("input_artifacts_identical")
                or not determinism.get("predictions_and_mrr_identical")
            ):
                raise RuntimeError(
                    f"formal inference blocked: {args.model} {scope} "
                    "determinism gate did not pass"
                )
            qualification_determinism_sha256[scope] = _sha(determinism_bytes)
        use_frozen_qualification = True

    header = {
        "record_type": "header",
        "experiment": EXPERIMENT,
        "model": args.model,
        "partition": args.partition,
        "replicate": args.replicate,
        "datasets": args.datasets,
        "requested_cases": len(selected),
        "requested_calls": len(selected) * 3,
        "model_config": asdict(model_cfg),
        "dashboard_config": asdict(cfg),
        "upstream_pin": check_upstream_pin(),
        "formal_roster_sha256": roster["formal_roster_sha256"],
        "qualification_report_sha256": qualification_report_sha256,
        "qualification_inventory_sha256": qualification_inventory_sha256,
        "qualification_token_budget_sha256": qualification_token_budget_sha256,
        "qualification_determinism_sha256": qualification_determinism_sha256,
        "implementation_sha256": _implementation_hash(),
        "experiment_config_sha256": _sha(
            (
                ROOT
                / "RQs"
                / "RQ0"
                / "configs"
                / "experiments"
                / "rq0_equal_information_equal_compute.yaml"
            )
            .read_bytes()
        ),
        "checkpoint_lock_sha256": _sha(
            (ROOT / "RQs" / "RQ0" / "configs" / "checkpoint_lock.json").read_bytes()
        ),
        "software_lock_sha256": _sha(
            (ROOT / "RQs" / "RQ0" / "configs" / "software_lock.json").read_bytes()
        ),
        "upstream_pin_file_sha256": _sha(
            (ROOT / "configs" / "upstream_pin.yaml").read_bytes()
        ),
        "server_launcher_sha256": _sha(
            (
                ROOT
                / "RQs"
                / "RQ0"
                / "scripts"
                / "vllm_vlm"
                / "serve_rq0_local.sh"
            ).read_bytes()
        ),
        "registered_inference_runtime": {
            "dtype": "bfloat16",
            "quantization": None,
            "max_model_len": 32768,
            "max_tokens": 16384,
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": 42,
            "async_scheduling": False,
            "gpu_memory_utilization": 0.65,
            "max_num_seqs": 8,
            "tensor_parallel_size": 1,
            "enable_prefix_caching": False,
            "enable_chunked_prefill": False,
            "use_flashinfer_sampler": False,
            "batch_invariant": False,
            "cublas_workspace_config": ":4096:8",
            "gdn_prefill_backend": "triton",
            "moe_backend": "triton",
            "triton_force_first_config": True,
            "max_videos_per_prompt": 0,
            "enforce_eager": True,
        },
        **_git_state(),
    }
    if not trajectory.exists():
        _write_jsonl(trajectory, header)
    if not detailed_log.exists():
        _write_jsonl(detailed_log, header)

    writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rq0-writer")
    rows: List[Dict[str, Any]] = []
    infrastructure_streak = 0
    calls_total = len(selected) * 3
    calls_seen = len(completed)
    next_report = 0.05

    try:
        for dataset, case_id in selected:
            case = load_processed_case(dataset, case_id)
            if use_frozen_qualification:
                opaque = opaque_incident_id(case_id)
                png = (qualification_dir / "renders" / f"{opaque}.png").read_bytes()
                manifest = json.loads(
                    (qualification_dir / "renders" / f"{opaque}.manifest.json").read_text()
                )
                ceb = json.loads(
                    (qualification_dir / "evidence" / f"{opaque}.ceb.json").read_text()
                )
                audit = json.loads(
                    (qualification_dir / "evidence" / f"{opaque}.audit.json").read_text()
                )
            else:
                view = CaseRenderView.from_case(case)
                png, manifest = compile_dashboard(view, cfg)
                ceb = build_canonical_evidence(manifest)
                audit = representation_audit(ceb)
            if not audit["parity_ok"]:
                raise RuntimeError(f"fact parity failed for {case_id}")
            opaque = ceb["opaque_incident_id"]

            render_path = run_dir / "renders" / f"{opaque}.png"
            manifest_path = run_dir / "renders" / f"{opaque}.manifest.json"
            ceb_path = run_dir / "evidence" / f"{opaque}.ceb.json"
            audit_path = run_dir / "evidence" / f"{opaque}.audit.json"
            for path in (render_path, manifest_path, ceb_path, audit_path):
                path.parent.mkdir(parents=True, exist_ok=True)
            futures = [
                writer.submit(render_path.write_bytes, png),
                writer.submit(
                    manifest_path.write_text,
                    json.dumps(manifest, indent=2, ensure_ascii=False),
                ),
                writer.submit(
                    ceb_path.write_text, json.dumps(ceb, indent=2, ensure_ascii=False)
                ),
                writer.submit(
                    audit_path.write_text, json.dumps(audit, indent=2, ensure_ascii=False)
                ),
            ]

            order = formal_orders[opaque] if args.partition == "formal" else _order(opaque)
            for letter in order:
                arm = ARM_BY_LETTER[letter]
                if (case_id, arm) in completed:
                    continue
                built = build_rq0_prompt(ceb, png, arm)
                prompt_text = "\n".join(
                    part["text"] for part in built["parts"] if part["type"] == "text"
                )
                accounting_started = time.time()
                text_input_tokens = count_vllm_prompt_tokens(
                    built["parts"], model_cfg, built["system"], text_only=True
                )
                preflight_input_tokens = (
                    count_vllm_prompt_tokens(
                        built["parts"], model_cfg, built["system"], text_only=False
                    )
                    if arm == "visual_text_topology"
                    else text_input_tokens
                )
                token_accounting_wall_s = time.time() - accounting_started
                started = time.time()
                error = None
                response_text = ""
                input_tokens = output_tokens = 0
                latency_s = 0.0
                finish_reason = None
                with GPUMonitor() as gpu:
                    try:
                        response = call_vlm(
                            built["parts"], model=model_cfg, system=built["system"]
                        )
                        response_text = response.text
                        input_tokens = response.input_tokens
                        output_tokens = response.output_tokens
                        latency_s = response.latency_s
                        finish_reason = (response.raw or {}).get(
                            "stopReason"
                        ) or (response.raw or {}).get("finish_reason")
                    except Exception as exc:  # noqa: BLE001
                        error = f"{type(exc).__name__}: {exc}"
                predicted = parse_answer(response_text) if response_text else []
                scores = score_prediction(predicted, case)
                truncated = finish_reason in {"length", "max_tokens"}
                if error:
                    status = "infrastructure_failure"
                    infrastructure_streak += 1
                elif truncated:
                    status = "model_truncation"
                    infrastructure_streak = 0
                elif not predicted:
                    status = "model_parse_failure"
                    infrastructure_streak = 0
                else:
                    status = "success"
                    infrastructure_streak = 0
                record: Dict[str, Any] = {
                    "record_type": "episode",
                    "case_id": case_id,
                    "opaque_incident_id": opaque,
                    "dataset": dataset,
                    "ground_truth": case.ground_truth,
                    "fault_type": case.fault_type,
                    "model": args.model,
                    "partition": args.partition,
                    "replicate": args.replicate,
                    "arm": arm,
                    "arm_order": order,
                    "status": status,
                    "error": error,
                    "parse_ok": bool(predicted) and not error,
                    "truncated": truncated,
                    "finish_reason": finish_reason,
                    "predicted": scores["predicted"],
                    "rank": scores["rank"],
                    "mrr": scores["mrr"],
                    "ac1": scores["ac1"],
                    "ac3": scores["ac3"],
                    "ac5": scores["ac5"],
                    "avg3": scores["avg3"],
                    "avg5": scores["avg5"],
                    "input_tokens": input_tokens,
                    "preflight_input_tokens": preflight_input_tokens,
                    "text_input_tokens": text_input_tokens,
                    "image_input_tokens": (
                        max(0, preflight_input_tokens - text_input_tokens)
                        if arm == "visual_text_topology"
                        and preflight_input_tokens is not None
                        and text_input_tokens is not None
                        else 0
                        if arm != "visual_text_topology"
                        else None
                    ),
                    "server_token_count_match": (
                        input_tokens == preflight_input_tokens
                        if preflight_input_tokens is not None and input_tokens
                        else None
                    ),
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "prompt_text_chars": len(prompt_text),
                    "wall_time_s": round(time.time() - started, 6),
                    "token_accounting_wall_s": round(token_accounting_wall_s, 6),
                    "provider_latency_s": latency_s,
                    **gpu.summary(),
                    "ceb_hash": ceb["ceb_hash"],
                    "fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
                    "renderer_version": int(manifest.get("renderer_version") or 6),
                    "renderer_fingerprint": manifest["config_fingerprint"],
                    "leakage_audit_ok": True,
                    "prompt_text_sha256": _sha(prompt_text),
                    "image_sha256": _sha(png) if arm == "visual_text_topology" else None,
                    "response": response_text,
                }
                rows.append(record)
                calls_seen += 1
                writer.submit(_write_jsonl, trajectory, record)
                writer.submit(_write_jsonl, detailed_log, record)
                conversation_path = run_dir / "conversations" / f"{opaque}__{arm}.md"
                conversation_path.parent.mkdir(parents=True, exist_ok=True)
                writer.submit(
                    conversation_path.write_text,
                    _conversation(
                        case_id,
                        opaque,
                        arm,
                        built,
                        str(render_path) if arm == "visual_text_topology" else None,
                        response_text,
                        record,
                    ),
                )

                progress = calls_seen / max(calls_total, 1)
                if progress >= next_report or calls_seen == calls_total:
                    successful = [row for row in rows if row["status"] != "infrastructure_failure"]
                    brief = {
                        "progress": round(progress, 4),
                        "completed_calls": calls_seen,
                        "requested_calls": calls_total,
                        "recent_valid_n": len(successful),
                        "recent_mrr": (
                            sum(row["mrr"] for row in successful) / len(successful)
                            if successful
                            else None
                        ),
                        "recent_ac1": (
                            sum(row["ac1"] for row in successful) / len(successful)
                            if successful
                            else None
                        ),
                        "recent_ac3": (
                            sum(row["ac3"] for row in successful) / len(successful)
                            if successful
                            else None
                        ),
                        "recent_ac5": (
                            sum(row["ac5"] for row in successful) / len(successful)
                            if successful
                            else None
                        ),
                        "recent_avg3": (
                            sum(row["avg3"] for row in successful) / len(successful)
                            if successful
                            else None
                        ),
                        "recent_avg5": (
                            sum(row["avg5"] for row in successful) / len(successful)
                            if successful
                            else None
                        ),
                        "note": "Monitoring only; partial metrics cannot select configs, stop, or replace cases.",
                    }
                    line = json.dumps(brief, ensure_ascii=False)
                    print(line, flush=True)
                    writer.submit(_append_text, brief_log, line + "\n")
                    while next_report <= progress:
                        next_report += 0.05

                if (
                    args.max_consecutive_infrastructure_failures
                    and infrastructure_streak
                    >= args.max_consecutive_infrastructure_failures
                ):
                    raise RuntimeError(
                        f"aborting after {infrastructure_streak} consecutive infrastructure failures"
                    )
            for future in futures:
                future.result()
    finally:
        writer.shutdown(wait=True)

    print(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "new_calls": len(rows),
                "completed_calls": len(_completed(trajectory)),
                "requested_calls": calls_total,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

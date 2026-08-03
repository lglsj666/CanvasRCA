#!/usr/bin/env python3
"""Development-only D/A/B runner for nonredundant modality allocation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
from scipy.stats import wilcoxon

from RQs.RQ0.scripts.run_rq0 import GPUMonitor
from vlmrca.eval.run_experiment import score_prediction
from vlmrca.processed import load_processed_case
from vlmrca.render.dashboard import CaseRenderView, compile_dashboard
from vlmrca.render.presets import make_dashboard_config
from vlmrca.rq0.evidence import (
    AllocationArm,
    allocation_representation_audit,
    build_allocation_prompt,
    build_canonical_evidence,
)
from vlmrca.upstream import check_upstream_pin, parse_answer
from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens
from vlmrca.vlm.configs import get_config

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_nonredundant_modality_allocation_v1"
ROSTER_PATH = ROOT / "RQs/RQ0/configs/nonredundant_allocation_development_roster.json"
CONFIG_PATH = ROOT / "RQs/RQ0/configs/experiments/rq0_nonredundant_modality_allocation_v1.yaml"
ARM_BY_LETTER: Dict[str, AllocationArm] = {
    "D": "allocated_visual_text",
    "A": "duplicated_visual_text",
    "B": "full_text_only",
}
ORDERS = ("DAB", "DBA", "ADB", "ABD", "BDA", "BAD")
SCORING_CONTRACT = "CanvasRCAGranularityAwareScoringV1"


def _sha(value: bytes | str | Path) -> str:
    if isinstance(value, Path):
        raw = value.read_bytes()
    else:
        raw = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n")


def _append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, default=str) + "\n")
        handle.flush()


def _completed(path: Path) -> set[tuple[str, str]]:
    done: set[tuple[str, str]] = set()
    if not path.exists():
        return done
    for line in path.read_text(errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("record_type") == "episode":
            done.add((row["case_id"], row["arm"]))
    return done


def _rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return [
        row
        for line in path.read_text(errors="replace").splitlines()
        if (row := json.loads(line)).get("record_type") == "episode"
    ]


def _balanced_orders(selections: List[Dict[str, Any]]) -> Dict[str, str]:
    ordered = sorted(
        (row["opaque_incident_id"] for row in selections),
        key=lambda value: hashlib.sha256(value.encode()).hexdigest(),
    )
    return {opaque: ORDERS[index % len(ORDERS)] for index, opaque in enumerate(ordered)}


def _smoke_selection(selections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    chosen = []
    for dataset in ("aegislab", "aiops2022", "aiops2025"):
        chosen.append(next(row for row in selections if row["dataset"] == dataset))
    return chosen


def _conversation(
    row: Dict[str, Any], built: Dict[str, Any], image_path: Path | None, result: Dict[str, Any]
) -> str:
    user_parts = []
    for part in built["parts"]:
        if part["type"] == "image":
            user_parts.append(f"[image: {image_path}]")
        else:
            user_parts.append(part["text"])
    return (
        f"# Allocation conversation — {row['opaque_incident_id']} — {row['arm']}\n\n"
        f"Private evaluator case id: `{row['case_id']}`\n\n"
        "## System\n\n"
        + built["system"]
        + "\n\n## User\n\n"
        + "\n\n".join(user_parts)
        + "\n\n## Assistant\n\n"
        + (row.get("response") or "[no response]")
        + "\n\n## Result\n\n```json\n"
        + json.dumps(result, indent=2, ensure_ascii=False, default=str)
        + "\n```\n"
    )


def _paired(rows: List[Dict[str, Any]], left: str, right: str) -> Dict[str, Any]:
    indexed = {(row["case_id"], row["arm"]): row for row in rows}
    case_ids = sorted({row["case_id"] for row in rows})
    shared = [
        case_id
        for case_id in case_ids
        if (case_id, left) in indexed and (case_id, right) in indexed
    ]
    deltas = np.asarray(
        [indexed[(case_id, left)]["mrr"] - indexed[(case_id, right)]["mrr"] for case_id in shared],
        dtype=float,
    )
    if len(deltas) and not np.allclose(deltas, 0):
        p_value = float(wilcoxon(deltas, zero_method="wilcox").pvalue)
    else:
        p_value = 1.0 if len(deltas) else None
    sd = float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0
    by_dataset: Dict[str, float] = {}
    for dataset in sorted({indexed[(case_id, left)]["dataset"] for case_id in shared}):
        values = [
            indexed[(case_id, left)]["mrr"] - indexed[(case_id, right)]["mrr"]
            for case_id in shared
            if indexed[(case_id, left)]["dataset"] == dataset
        ]
        by_dataset[dataset] = float(np.mean(values))
    return {
        "left": left,
        "right": right,
        "n": len(shared),
        "delta_mrr": float(np.mean(deltas)) if len(deltas) else None,
        "improved": int(np.sum(deltas > 0)),
        "degraded": int(np.sum(deltas < 0)),
        "tied": int(np.sum(deltas == 0)),
        "wilcoxon_p_descriptive": p_value,
        "paired_cohens_d": float(np.mean(deltas) / sd) if sd else 0.0,
        "delta_by_dataset": by_dataset,
    }


def summarize(path: Path, expected_cases: int, mode: str) -> Dict[str, Any]:
    rows = _rows(path)
    arms = {}
    for arm in ARM_BY_LETTER.values():
        chosen = [row for row in rows if row["arm"] == arm]
        valid = [row for row in chosen if row["status"] != "infrastructure_failure"]
        arms[arm] = {
            "n": len(chosen),
            "mrr": float(np.mean([row["mrr"] for row in valid])) if valid else None,
            "ac1": float(np.mean([row["ac1"] for row in valid])) if valid else None,
            "ac3": float(np.mean([row["ac3"] for row in valid])) if valid else None,
            "ac5": float(np.mean([row["ac5"] for row in valid])) if valid else None,
            "avg3": float(np.mean([row["avg3"] for row in valid])) if valid else None,
            "avg5": float(np.mean([row["avg5"] for row in valid])) if valid else None,
            "parse_rate": float(np.mean([row["parse_ok"] for row in chosen])) if chosen else None,
            "infrastructure_failures": sum(
                row["status"] == "infrastructure_failure" for row in chosen
            ),
            "mean_input_tokens": float(np.mean([row["input_tokens"] for row in valid])) if valid else None,
            "mean_output_tokens": float(np.mean([row["output_tokens"] for row in valid])) if valid else None,
            "mean_wall_time_s": float(np.mean([row["wall_time_s"] for row in valid])) if valid else None,
        }
    d_minus_b = _paired(rows, "allocated_visual_text", "full_text_only")
    d_minus_a = _paired(rows, "allocated_visual_text", "duplicated_visual_text")
    gate_failures: List[str] = []
    if mode == "main" and len(rows) == expected_cases * 3:
        if (d_minus_b["delta_mrr"] or 0.0) < 0.05:
            gate_failures.append("D_minus_B_below_0.05")
        if d_minus_b["improved"] - d_minus_b["degraded"] < 3:
            gate_failures.append("D_minus_B_direction_margin_below_3")
        if any(value <= -0.10 for value in d_minus_b["delta_by_dataset"].values()):
            gate_failures.append("D_minus_B_dataset_reverse_at_or_below_-0.10")
        if (d_minus_a["delta_mrr"] or 0.0) <= 0:
            gate_failures.append("D_does_not_beat_A")
        if any((value["parse_rate"] or 0.0) < 0.95 for value in arms.values()):
            gate_failures.append("parse_rate_below_0.95")
        if any(value["infrastructure_failures"] for value in arms.values()):
            gate_failures.append("infrastructure_pairing_incomplete")
    else:
        gate_failures.append("main_run_incomplete_or_smoke_only")
    return {
        "schema_version": "RQ0AllocationSummaryV1",
        "scope": "exposed_development_only_nonconfirmatory",
        "n_calls": len(rows),
        "expected_calls": expected_cases * 3,
        "arms": arms,
        "comparisons": {"D_minus_B": d_minus_b, "D_minus_A": d_minus_a},
        "gate": {
            "pass_for_this_model": not gate_failures,
            "failures": gate_failures,
            "interpretation": "development mechanism qualification; never confirmatory",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=("qwen3.6-27b", "gemma-4-26b-a4b"))
    parser.add_argument("--mode", choices=("smoke", "main"), default="smoke")
    parser.add_argument("--replicate", default=None)
    parser.add_argument("--out-root", type=Path, default=ROOT / "RQs/RQ0/results")
    parser.add_argument("--max-consecutive-infrastructure-failures", type=int, default=3)
    args = parser.parse_args()

    roster = json.loads(ROSTER_PATH.read_text())
    selections = list(roster["selections"])
    if args.mode == "smoke":
        selections = _smoke_selection(selections)
    orders = _balanced_orders(roster["selections"])
    replicate = args.replicate or args.mode
    run_dir = args.out_root / EXPERIMENT / f"{args.model}__development__{replicate}"
    trajectory = run_dir / "trajectories/episodes.jsonl"
    detailed = run_dir / "logs/detailed.jsonl"
    brief = run_dir / "logs/brief.log"
    completed = _completed(trajectory)
    model_cfg = get_config(args.model)
    renderer_cfg = make_dashboard_config("rq0_v7_edge_key")

    header = {
        "record_type": "header",
        "schema_version": "RQ0AllocationRunContractV1",
        "experiment": EXPERIMENT,
        "scope": "exposed_development_only_nonconfirmatory",
        "model": args.model,
        "mode": args.mode,
        "replicate": replicate,
        "requested_cases": len(selections),
        "requested_calls": len(selections) * 3,
        "arms": ARM_BY_LETTER,
        "orders": ORDERS,
        "model_config": asdict(model_cfg),
        "renderer_config": asdict(renderer_cfg),
        "roster_sha256": _sha(ROSTER_PATH),
        "experiment_config_sha256": _sha(CONFIG_PATH),
        "serializer_sha256": _sha(ROOT / "RQs/vlmrca/rq0/evidence.py"),
        "scorer_sha256": _sha(ROOT / "RQs/vlmrca/eval/scoring.py"),
        "scoring_contract": SCORING_CONTRACT,
        "upstream_pin": check_upstream_pin(),
        "formal_or_reserve_cases_used": False,
        "partial_results_may_select_or_stop": False,
        "runtime": {
            "dtype": "bfloat16",
            "quantization": None,
            "max_model_len": 32768,
            "max_tokens": 16384,
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": 42,
            "thinking": False,
            "gpu_memory_utilization": 0.65,
            "enforce_eager": True,
        },
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "run_contract.json", header)
    if not trajectory.exists():
        _append_jsonl(trajectory, header)
    if not detailed.exists():
        _append_jsonl(detailed, header)

    infrastructure_streak = 0
    calls_seen = len(completed)
    requested_calls = len(selections) * 3
    for selection in selections:
        dataset = selection["dataset"]
        case_id = selection["private_case_id"]
        opaque = selection["opaque_incident_id"]
        case = load_processed_case(dataset, case_id)
        png, manifest = compile_dashboard(CaseRenderView.from_case(case), renderer_cfg)
        ceb = build_canonical_evidence(manifest)
        if ceb["opaque_incident_id"] != opaque:
            raise RuntimeError(f"opaque-id mismatch for {case_id}")
        audit = allocation_representation_audit(ceb)
        if not (
            audit["a_b_text_byte_identical"]
            and audit["common_summary_byte_identical_all_arms"]
            and audit["source_fact_inventory_equal_all_arms"]
        ):
            raise RuntimeError(f"allocation parity audit failed for {case_id}")
        image_path = run_dir / "renders" / f"{opaque}.png"
        _write_json(run_dir / "renders" / f"{opaque}.manifest.json", manifest)
        _write_json(run_dir / "evidence" / f"{opaque}.ceb.json", ceb)
        _write_json(run_dir / "evidence" / f"{opaque}.allocation_audit.json", audit)
        image_path.parent.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(png)

        order = orders[opaque]
        for letter in order:
            arm = ARM_BY_LETTER[letter]
            if (case_id, arm) in completed:
                continue
            built = build_allocation_prompt(ceb, png, arm)
            prompt_text = "\n".join(
                part["text"] for part in built["parts"] if part["type"] == "text"
            )
            leakage_values: Iterable[str] = (
                case_id,
                dataset,
                case.fault_type,
                str(int(case.timestamp)),
            )
            leakage_ok = not any(value and value in prompt_text for value in leakage_values)
            if not leakage_ok:
                raise RuntimeError(f"model-visible leakage detected for {case_id}")
            text_tokens = count_vllm_prompt_tokens(
                built["parts"], model_cfg, built["system"], text_only=True
            )
            preflight_tokens = count_vllm_prompt_tokens(
                built["parts"], model_cfg, built["system"], text_only=False
            )
            if preflight_tokens + model_cfg.max_tokens > 32768:
                raise RuntimeError(
                    f"qualified context budget exceeded for {case_id}/{arm}: "
                    f"{preflight_tokens}+{model_cfg.max_tokens}>32768"
                )
            started = time.time()
            response_text = ""
            input_tokens = output_tokens = 0
            finish_reason = None
            provider_latency_s = 0.0
            error = None
            with GPUMonitor() as gpu:
                try:
                    response = call_vlm(built["parts"], model=model_cfg, system=built["system"])
                    response_text = response.text
                    input_tokens = response.input_tokens
                    output_tokens = response.output_tokens
                    provider_latency_s = response.latency_s
                    finish_reason = (response.raw or {}).get("finish_reason") or (
                        response.raw or {}
                    ).get("stopReason")
                except Exception as exc:  # noqa: BLE001
                    error = f"{type(exc).__name__}: {exc}"
            predicted = parse_answer(response_text) if response_text else []
            score = score_prediction(predicted, case)
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
            row = {
                "record_type": "episode",
                "experiment": EXPERIMENT,
                "model": args.model,
                "mode": args.mode,
                "replicate": replicate,
                "dataset": dataset,
                "case_id": case_id,
                "opaque_incident_id": opaque,
                "ground_truth": case.ground_truth,
                "fault_type": case.fault_type,
                "arm": arm,
                "arm_order": order,
                "status": status,
                "error": error,
                "parse_ok": bool(predicted) and not error,
                "truncated": truncated,
                "finish_reason": finish_reason,
                **score,
                "input_tokens": input_tokens,
                "preflight_input_tokens": preflight_tokens,
                "text_input_tokens": text_tokens,
                "image_input_tokens": max(0, preflight_tokens - text_tokens),
                "server_token_count_match": input_tokens == preflight_tokens if input_tokens else None,
                "output_tokens": output_tokens,
                "wall_time_s": round(time.time() - started, 6),
                "provider_latency_s": provider_latency_s,
                **gpu.summary(),
                "ceb_hash": ceb["ceb_hash"],
                "source_fact_inventory_hash": ceb["atomic_fact_inventory_hash"],
                "common_summary_sha256": audit["common_summary_sha256"],
                "dense_appendix_sha256": audit["dense_appendix_sha256"],
                "prompt_text_sha256": _sha(prompt_text),
                "image_sha256": _sha(png) if arm != "full_text_only" else None,
                "renderer_version": manifest["renderer_version"],
                "renderer_fingerprint": manifest["config_fingerprint"],
                "leakage_audit_ok": leakage_ok,
                "scoring_contract": SCORING_CONTRACT,
                "response": response_text,
            }
            _append_jsonl(trajectory, row)
            _append_jsonl(detailed, row)
            conversation_path = run_dir / "conversations" / f"{opaque}__{arm}.md"
            conversation_path.parent.mkdir(parents=True, exist_ok=True)
            conversation_path.write_text(
                _conversation(
                    row,
                    built,
                    image_path if arm != "full_text_only" else None,
                    score,
                )
            )
            calls_seen += 1
            progress = {
                "completed_calls": calls_seen,
                "requested_calls": requested_calls,
                "progress": round(calls_seen / requested_calls, 4),
                "note": "partial development results cannot select configs, stop, or replace cases",
            }
            with brief.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(progress) + "\n")
            print(json.dumps(progress), flush=True)
            if (
                args.max_consecutive_infrastructure_failures
                and infrastructure_streak >= args.max_consecutive_infrastructure_failures
            ):
                raise RuntimeError(
                    f"aborting after {infrastructure_streak} consecutive infrastructure failures"
                )

    summary = summarize(trajectory, len(selections), args.mode)
    _write_json(run_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

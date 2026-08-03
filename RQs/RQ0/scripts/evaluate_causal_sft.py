#!/usr/bin/env python3
"""Paired base/adapter evaluation on frozen development-heldout SFT cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "RQs"))

from vlmrca.config_paths import resolve_project_path  # noqa: E402
from RQs.RQ0.scripts.run_rq0 import GPUMonitor  # noqa: E402
from vlmrca.eval.run_experiment import score_prediction  # noqa: E402
from vlmrca.processed import load_processed_case  # noqa: E402
from vlmrca.rq0.evidence import build_rq0_prompt  # noqa: E402
from vlmrca.training.causal_sft import sha256_json  # noqa: E402
from vlmrca.upstream import parse_answer  # noqa: E402
from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens  # noqa: E402
from vlmrca.vlm.configs import get_config  # noqa: E402


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n")


def _append_jsonl(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, default=str) + "\n")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _append_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(value)


def _balanced_condition_orders(records: List[Dict[str, Any]]) -> Dict[str, tuple[str, str]]:
    ordered = sorted(
        (row["opaque_incident_id"] for row in records),
        key=lambda opaque: hashlib.sha256(f"{opaque}:sft-eval-order".encode()).hexdigest(),
    )
    return {
        opaque: (("base", "adapter") if index % 2 == 0 else ("adapter", "base"))
        for index, opaque in enumerate(ordered)
    }


def _conversation(
    record: Dict[str, Any], condition: str, built: Dict[str, Any], response: str, result: Dict[str, Any]
) -> str:
    parts = []
    for part in built["parts"]:
        parts.append(
            f"[image: {record['files']['image']}]"
            if part["type"] == "image"
            else part["text"]
        )
    return (
        f"# Causal SFT pilot evaluation — {record['opaque_incident_id']} — {condition}\n\n"
        f"Private evaluator case id: `{record['private_case_id']}`\n\n"
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


def _summarize(rows: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "schema_version": "CausalIntegrationSFTPilotEvaluationV1",
        "n_calls": len(rows),
        "conditions": {},
        "datasets": {},
    }
    for condition in ("base", "adapter"):
        selected = [row for row in rows if row["condition"] == condition]
        summary["conditions"][condition] = {
            "n": len(selected),
            "mrr": sum(row["mrr"] for row in selected) / len(selected),
            "ac1": sum(row["ac1"] for row in selected) / len(selected),
            "ac3": sum(row["ac3"] for row in selected) / len(selected),
            "ac5": sum(row["ac5"] for row in selected) / len(selected),
            "avg3": sum(row["avg3"] for row in selected) / len(selected),
            "avg5": sum(row["avg5"] for row in selected) / len(selected),
            "parse_rate": sum(bool(row["parse_ok"]) for row in selected) / len(selected),
            "infrastructure_failures": sum(
                row["status"] == "infrastructure_failure" for row in selected
            ),
            "mean_input_tokens": sum(row["input_tokens"] for row in selected) / len(selected),
            "mean_output_tokens": sum(row["output_tokens"] for row in selected) / len(selected),
            "mean_wall_time_s": sum(row["wall_time_s"] for row in selected) / len(selected),
        }
    indexed = {(row["opaque_incident_id"], row["condition"]): row for row in rows}
    pairs = [
        (indexed[(opaque, "base")], indexed[(opaque, "adapter")])
        for opaque in sorted({row["opaque_incident_id"] for row in rows})
        if (opaque, "base") in indexed and (opaque, "adapter") in indexed
    ]
    deltas = [adapter["mrr"] - base["mrr"] for base, adapter in pairs]
    summary["paired"] = {
        "n": len(pairs),
        "delta_mrr_adapter_minus_base": sum(deltas) / len(deltas),
        "improved": sum(value > 0 for value in deltas),
        "degraded": sum(value < 0 for value in deltas),
        "tied": sum(value == 0 for value in deltas),
        "top1_changed": sum(
            (base.get("predicted") or [None])[0]
            != (adapter.get("predicted") or [None])[0]
            for base, adapter in pairs
        ),
    }
    for dataset in sorted({row["dataset"] for row in rows}):
        dataset_rows = [row for row in rows if row["dataset"] == dataset]
        values = {}
        for condition in ("base", "adapter"):
            selected = [row for row in dataset_rows if row["condition"] == condition]
            values[condition] = sum(row["mrr"] for row in selected) / len(selected)
        values["delta_mrr_adapter_minus_base"] = values["adapter"] - values["base"]
        summary["datasets"][dataset] = values

    gate = config["pilot"]["promotion_gate"]
    failures = []
    if summary["paired"]["delta_mrr_adapter_minus_base"] < float(
        gate["minimum_macro_delta_mrr"]
    ):
        failures.append("macro_delta_mrr_below_registered_minimum")
    if summary["conditions"]["adapter"]["parse_rate"] < float(gate["minimum_parse_rate"]):
        failures.append("adapter_parse_rate_below_registered_minimum")
    if any(
        value["delta_mrr_adapter_minus_base"]
        < float(gate["maximum_dataset_reverse_delta_mrr"])
        for value in summary["datasets"].values()
    ):
        failures.append("dataset_reverse_effect_exceeds_registered_limit")
    if gate["require_zero_infrastructure_failures"] and any(
        values["infrastructure_failures"]
        for values in summary["conditions"].values()
    ):
        failures.append("infrastructure_failure_present")
    summary["promotion_gate"] = {
        "registered": gate,
        "failures": failures,
        "pass": not failures,
        "interpretation": "development-only pilot promotion gate; not confirmatory evidence",
    }
    summary["status_counts"] = dict(sorted(Counter(row["status"] for row in rows).items()))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter-path", type=Path, required=True)
    parser.add_argument("--adapter-name", default="canvasrca-causal-sft-pilot")
    parser.add_argument("--run-name", default="paired_main")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "RQs/RQ0/configs/training/causal_integration_sft_v1.yaml",
    )
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    adapter_path = args.adapter_path.resolve()
    roster_path = resolve_project_path(ROOT, config["derived_roster"])
    roster = json.loads(roster_path.read_text())
    records = list(roster["selections"]["pilot_eval"])
    expected_partition = config["pilot"].get(
        "evaluation_stage_partition", "development_heldout"
    )
    if len(records) != 12 or any(
        row["stage_partition"] != expected_partition for row in records
    ):
        raise RuntimeError(
            "pilot eval must be the frozen 12-case development-heldout selection"
        )
    if not (adapter_path / "adapter_config.json").is_file():
        raise RuntimeError(f"adapter is incomplete: {adapter_path}")
    for record in records:
        for name, relative in record["files"].items():
            if _sha_file(ROOT / relative) != record["file_sha256"][name]:
                raise RuntimeError(f"frozen eval artifact drift: {relative}")
    condition_orders = _balanced_condition_orders(records)

    result_root = ROOT / config["pilot"]["result_root"] / "evaluation" / args.run_name
    result_root.mkdir(parents=True, exist_ok=False)
    base_cfg = get_config("qwen3.6-27b")
    adapter_cfg = replace(
        base_cfg, tag="qwen3.6-27b-causal-sft-pilot", model_id=args.adapter_name
    )
    contract = {
        "schema_version": "CausalIntegrationSFTPilotEvalContractV1",
        "scope": "development_only_nonconfirmatory_model_selection",
        "config_sha256": _sha_file(args.config.resolve()),
        "roster_sha256": roster["roster_sha256"],
        "selection_sha256": sha256_json(records),
        "adapter_path": str(adapter_path),
        "adapter_config_sha256": _sha_file(adapter_path / "adapter_config.json"),
        "adapter_model_sha256": _sha_file(adapter_path / "adapter_model.safetensors"),
        "base_model_config": asdict(base_cfg),
        "adapter_model_config": asdict(adapter_cfg),
        "conditions": ["base", "adapter"],
        "condition_order": "opaque_hash_balanced",
        "promotion_gate": config["pilot"]["promotion_gate"],
        "formal_or_reserve_cases_used": False,
    }
    _write_json(result_root / "run_contract.json", contract)
    trajectory = result_root / "trajectories/episodes.jsonl"
    detailed = result_root / "logs/detailed.jsonl"
    brief = result_root / "logs/brief.log"
    _append_jsonl(trajectory, {"record_type": "header", **contract})
    _append_jsonl(detailed, {"record_type": "header", **contract})
    writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="sft-eval-writer")
    rows: List[Dict[str, Any]] = []
    next_report = 0.05
    try:
        for record in records:
            case = load_processed_case(record["dataset"], record["private_case_id"])
            png = (ROOT / record["files"]["image"]).read_bytes()
            ceb = json.loads((ROOT / record["files"]["ceb"]).read_text())
            built = build_rq0_prompt(ceb, png, "visual_text_topology")
            for condition in condition_orders[record["opaque_incident_id"]]:
                model_cfg = base_cfg if condition == "base" else adapter_cfg
                started = time.time()
                error = None
                response = ""
                input_tokens = output_tokens = 0
                preflight = count_vllm_prompt_tokens(
                    built["parts"], model_cfg, system=built["system"]
                )
                with GPUMonitor() as monitor:
                    try:
                        completion = call_vlm(
                            built["parts"], model=model_cfg, system=built["system"]
                        )
                        response = completion.text
                        input_tokens = completion.input_tokens
                        output_tokens = completion.output_tokens
                    except Exception as exc:  # noqa: BLE001
                        error = f"{type(exc).__name__}: {exc}"
                predicted = parse_answer(response) if response else []
                scored = score_prediction(predicted, case)
                row = {
                    "record_type": "episode",
                    "dataset": record["dataset"],
                    "case_id": record["private_case_id"],
                    "opaque_incident_id": record["opaque_incident_id"],
                    "stage_partition": record["stage_partition"],
                    "condition": condition,
                    "status": "ok" if error is None else "infrastructure_failure",
                    "error": error,
                    "parse_ok": bool(predicted) and error is None,
                    "predicted": scored["predicted"],
                    "rank": scored["rank"],
                    "mrr": scored["mrr"],
                    "ac1": scored["ac1"],
                    "ac3": scored["ac3"],
                    "ac5": scored["ac5"],
                    "avg3": scored["avg3"],
                    "avg5": scored["avg5"],
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "preflight_input_tokens": preflight,
                    "server_token_count_match": preflight == input_tokens,
                    "wall_time_s": time.time() - started,
                    **monitor.summary(),
                }
                rows.append(row)
                writer.submit(_append_jsonl, trajectory, row)
                writer.submit(_append_jsonl, detailed, {"event": "evaluation_case", **row})
                writer.submit(
                    _write_text,
                    result_root / "conversations" / f"{record['opaque_incident_id']}__{condition}.md",
                    _conversation(record, condition, built, response, row),
                )
                progress = len(rows) / (len(records) * 2)
                if progress + 1e-12 >= next_report or len(rows) == len(records) * 2:
                    line = (
                        f"{len(rows)}/{len(records)*2} ({progress:.1%}) "
                        f"base_mrr={sum(r['mrr'] for r in rows if r['condition']=='base')/max(1,sum(r['condition']=='base' for r in rows)):.4f} "
                        f"adapter_mrr={sum(r['mrr'] for r in rows if r['condition']=='adapter')/max(1,sum(r['condition']=='adapter' for r in rows)):.4f}\n"
                    )
                    writer.submit(_append_text, brief, line)
                    print(line, end="", flush=True)
                    while next_report <= progress + 1e-12:
                        next_report += 0.05
    finally:
        writer.shutdown(wait=True)

    summary = _summarize(rows, config)
    promoted = None
    if summary["promotion_gate"]["pass"]:
        best_root = ROOT / config["pilot"]["best_root"]
        best_root.parent.mkdir(parents=True, exist_ok=True)
        if best_root.exists():
            raise RuntimeError(f"refusing to overwrite existing best adapter: {best_root}")
        shutil.copytree(
            adapter_path,
            best_root,
            ignore=shutil.ignore_patterns("trainer_state.pt"),
        )
        promoted = str(best_root.relative_to(ROOT))
    summary["promoted_best_adapter"] = promoted
    _write_json(result_root / "summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

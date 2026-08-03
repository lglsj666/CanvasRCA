#!/usr/bin/env python3
"""Collect frozen base-model rollouts for the causal SFT v2 train pool."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
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

CONFIG_PATH = ROOT / "RQs/RQ0/configs/training/causal_integration_sft_v2.yaml"


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _append(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(value)


def _records(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    indexed = {
        row["opaque_incident_id"]: row
        for row in plan["rollout_pool"] + plan["smoke_rollout"]
    }
    return [indexed[key] for key in sorted(indexed)]


def main() -> int:
    config = yaml.safe_load(CONFIG_PATH.read_text())
    plan_path = resolve_project_path(ROOT, config["candidate_plan"])
    plan = json.loads(plan_path.read_text())
    declared = plan["candidate_plan_sha256"]
    unsigned = {key: value for key, value in plan.items() if key != "candidate_plan_sha256"}
    if sha256_json(unsigned) != declared:
        raise RuntimeError("candidate plan hash does not verify")
    records = _records(plan)
    result_root = ROOT / config["base_rollout_root"]
    result_root.mkdir(parents=True, exist_ok=False)
    model = get_config("qwen3.6-27b")
    contract = {
        "schema_version": "CausalIntegrationSFTV2BaseRolloutContractV1",
        "scope": "development_train_only_target_construction",
        "created_before_model_call": True,
        "config_sha256": _sha_file(CONFIG_PATH),
        "candidate_plan_sha256": declared,
        "selected_records_sha256": sha256_json(records),
        "model_config": asdict(model),
        "arm": "visual_text_topology",
        "maximum_admissible_input_tokens": 16384,
        "formal_or_reserve_cases_used": False,
    }
    _write_json(result_root / "run_contract.json", contract)
    trajectories = result_root / "trajectories/episodes.jsonl"
    detailed = result_root / "logs/detailed.jsonl"
    brief = result_root / "logs/brief.log"
    _append(trajectories, json.dumps({"record_type": "header", **contract}) + "\n")
    _append(detailed, json.dumps({"record_type": "header", **contract}) + "\n")
    writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="v2-rollout-writer")
    rows = []
    started_all = time.time()
    try:
        for index, record in enumerate(records, start=1):
            case = load_processed_case(record["dataset"], record["private_case_id"])
            png = (ROOT / record["files"]["image"]).read_bytes()
            ceb = json.loads((ROOT / record["files"]["ceb"]).read_text())
            built = build_rq0_prompt(ceb, png, "visual_text_topology")
            preflight = count_vllm_prompt_tokens(
                built["parts"], model, system=built["system"]
            )
            if preflight is None:
                raise RuntimeError(
                    "live vLLM token counting failed; verify VLLM_BASE_URL before any model call"
                )
            started = time.time()
            response = ""
            error = None
            input_tokens = output_tokens = 0
            if preflight > 16384:
                status = "token_ineligible"
                error = f"preflight_input_tokens={preflight} exceeds 16384"
                gpu = {}
            else:
                with GPUMonitor() as monitor:
                    try:
                        completion = call_vlm(
                            built["parts"], model=model, system=built["system"]
                        )
                        response = completion.text
                        input_tokens = completion.input_tokens
                        output_tokens = completion.output_tokens
                        status = "ok"
                    except Exception as exc:  # noqa: BLE001
                        error = f"{type(exc).__name__}: {exc}"
                        status = "infrastructure_failure"
                gpu = monitor.summary()
            predicted = parse_answer(response) if response else []
            scored = score_prediction(predicted, case)
            row = {
                "record_type": "episode",
                "dataset": record["dataset"],
                "case_id": record["private_case_id"],
                "opaque_incident_id": record["opaque_incident_id"],
                "source_stage_partition": record["stage_partition"],
                "status": status,
                "error": error,
                "parse_ok": bool(predicted) and status == "ok",
                "predicted": scored["predicted"],
                "rank": scored["rank"],
                "mrr": scored["mrr"],
                "ac1": scored["ac1"],
                "ac3": scored["ac3"],
                "ac5": scored["ac5"],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "preflight_input_tokens": preflight,
                "server_token_count_match": (
                    preflight == input_tokens if status == "ok" else None
                ),
                "wall_time_s": time.time() - started,
                **gpu,
            }
            rows.append(row)
            writer.submit(_append, trajectories, json.dumps(row, ensure_ascii=False) + "\n")
            writer.submit(_append, detailed, json.dumps({"event": "base_rollout", **row}, ensure_ascii=False) + "\n")
            conversation = (
                f"# Causal SFT v2 base rollout — {record['opaque_incident_id']}\n\n"
                f"## System\n\n{built['system']}\n\n## User\n\n"
                f"[image: {record['files']['image']}]\n\n"
                + "\n\n".join(part.get("text", "") for part in built["parts"] if part["type"] == "text")
                + f"\n\n## Assistant\n\n{response or '[no response]'}\n"
            )
            writer.submit(
                lambda p, value: p.parent.mkdir(parents=True, exist_ok=True) or p.write_text(value),
                result_root / "conversations" / f"{record['opaque_incident_id']}.md",
                conversation,
            )
            line = (
                f"{index}/{len(records)} ({index/len(records):.1%}) "
                f"ok={sum(r['status']=='ok' for r in rows)} "
                f"base_ac1={sum(r['ac1'] for r in rows)/len(rows):.4f} "
                f"elapsed_s={time.time()-started_all:.1f}\n"
            )
            writer.submit(_append, brief, line)
            print(line, end="", flush=True)
    finally:
        writer.shutdown(wait=True)
    summary = {
        "schema_version": "CausalIntegrationSFTV2BaseRolloutSummaryV1",
        "n": len(rows),
        "status_counts": dict(sorted(__import__("collections").Counter(row["status"] for row in rows).items())),
        "parse_rate": sum(row["parse_ok"] for row in rows) / len(rows),
        "ac1": sum(row["ac1"] for row in rows) / len(rows),
        "per_dataset": {
            dataset: {
                "n": len(selected := [row for row in rows if row["dataset"] == dataset]),
                "ok": sum(row["status"] == "ok" for row in selected),
                "base_correct": sum(row["mrr"] == 1 for row in selected),
                "base_wrong": sum(row["status"] == "ok" and row["mrr"] != 1 for row in selected),
            }
            for dataset in sorted({row["dataset"] for row in rows})
        },
        "wall_time_s": time.time() - started_all,
    }
    _write_json(result_root / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

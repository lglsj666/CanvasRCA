#!/usr/bin/env python3
"""Verify every frozen formal RQ0 prompt fits the registered 32k/16k budget."""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict

from vlmrca.rq0.evidence import build_rq0_prompt
from vlmrca.vlm.client import count_vllm_prompt_tokens
from vlmrca.vlm.configs import get_config

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_equal_information_equal_compute_v1"
MAX_MODEL_LEN = 32768
MAX_OUTPUT_TOKENS = 16384


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _one(
    model: str,
    qualification: Path,
    dataset: str,
    opaque: str,
) -> Dict[str, Any]:
    cfg = get_config(model)
    png = (qualification / "renders" / f"{opaque}.png").read_bytes()
    ceb = json.loads(
        (qualification / "evidence" / f"{opaque}.ceb.json").read_text()
    )
    counts = {}
    failures = []
    for arm in ("visual_text_topology", "text_only", "flat_structured"):
        built = build_rq0_prompt(ceb, png, arm)
        count = count_vllm_prompt_tokens(
            built["parts"], cfg, built["system"], text_only=False
        )
        counts[arm] = count
        if count is None:
            failures.append(f"{arm}: /tokenize failed")
        elif count + MAX_OUTPUT_TOKENS > MAX_MODEL_LEN:
            failures.append(
                f"{arm}: input={count} + output={MAX_OUTPUT_TOKENS} "
                f"> context={MAX_MODEL_LEN}"
            )
    return {
        "dataset": dataset,
        "opaque_incident_id": opaque,
        "input_tokens": counts,
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.workers <= 4:
        raise ValueError("--workers must be in [1, 4]")

    qualification = ROOT / "RQs/RQ0/results" / EXPERIMENT / "qualification_formal"
    static_report = json.loads(
        (qualification / "qualification_report.json").read_text()
    )
    inventory_path = qualification / "artifact_inventory.json"
    inventory = json.loads(inventory_path.read_text())
    if not static_report.get("all_passed") or not inventory.get("all_passed"):
        raise RuntimeError("static qualification/inventory has not passed")

    jobs = [
        (record["dataset"], record["opaque_incident_id"])
        for record in static_report["records"]
    ]
    records = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(_one, args.model, qualification, dataset, opaque): (
                dataset,
                opaque,
            )
            for dataset, opaque in jobs
        }
        for index, future in enumerate(as_completed(futures), start=1):
            dataset, opaque = futures[future]
            try:
                record = future.result()
            except Exception as exc:  # noqa: BLE001
                record = {
                    "dataset": dataset,
                    "opaque_incident_id": opaque,
                    "input_tokens": {},
                    "failures": [f"{type(exc).__name__}: {exc}"],
                    "status": "fail",
                }
            records.append(record)
            if index == 1 or index % 36 == 0 or index == len(jobs):
                failed = sum(item["status"] != "pass" for item in records)
                print(f"[{index}/{len(jobs)}] failures={failed}", flush=True)

    records.sort(key=lambda row: (row["dataset"], row["opaque_incident_id"]))
    arm_max = {
        arm: max(
            (
                int(row["input_tokens"][arm])
                for row in records
                if row["input_tokens"].get(arm) is not None
            ),
            default=None,
        )
        for arm in ("visual_text_topology", "text_only", "flat_structured")
    }
    failed = [row for row in records if row["status"] != "pass"]
    report = {
        "schema_version": 1,
        "model": args.model,
        "max_model_len": MAX_MODEL_LEN,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "requested_cases": len(jobs),
        "requested_prompts": len(jobs) * 3,
        "passed_cases": len(jobs) - len(failed),
        "failed_cases": len(failed),
        "all_fit": not failed and len(jobs) == 720,
        "max_input_tokens_by_arm": arm_max,
        "artifact_inventory_sha256": _sha(inventory_path),
        "evidence_serializer_sha256": _sha(
            ROOT / "RQs" / "vlmrca" / "rq0" / "evidence.py"
        ),
        "records": records,
    }
    out = qualification / f"token_budget_{args.model}.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "out": str(out),
                "requested_cases": report["requested_cases"],
                "failed_cases": report["failed_cases"],
                "all_fit": report["all_fit"],
                "max_input_tokens_by_arm": arm_max,
            },
            indent=2,
        )
    )
    if not report["all_fit"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

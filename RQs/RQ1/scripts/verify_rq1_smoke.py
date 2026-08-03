#!/usr/bin/env python3
"""Verify the zero-infrastructure-failure RQ1 partition-aware smoke."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash
from rq1lib.settings import assert_execution_config, load_yaml_config

EXPECTED_ARMS = {"T", "V", "H"}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractError(f"{path} is not a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--prepared-index", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    assert_execution_config(config)
    roster = _load(args.roster)
    index = _load(args.prepared_index)
    call_paths = sorted((args.run_root / "calls").glob("*.json"))
    calls = [_load(path) for path in call_paths]
    expected_count = int(index["task_count"]) * len(EXPECTED_ARMS)
    if len(calls) != expected_count:
        raise ContractError(
            f"smoke call count differs: actual={len(calls)} expected={expected_count}"
        )
    expected_config_hash = stable_hash(config)
    expected_roster_hash = stable_hash(roster)
    units: dict[tuple[str, str], set[str]] = {}
    infra = 0
    parse = 0
    truncation = 0
    for call in calls:
        if (
            call.get("model") != args.model
            or call.get("experiment_id") != config["experiment_id"]
            or call.get("experiment_config_hash") != expected_config_hash
            or call.get("roster_contract_hash") != expected_roster_hash
            or call.get("roster_assignment_hash") != roster["assignment_hash"]
        ):
            raise ContractError("smoke call contract differs from config/roster/model")
        arm = str(call.get("arm"))
        if arm not in EXPECTED_ARMS:
            raise ContractError(f"unexpected smoke arm {arm}")
        key = (str(call["opaque_incident_id"]), str(call["query_id"]))
        units.setdefault(key, set()).add(arm)
        if call.get("status") == "infrastructure_error":
            infra += 1
            continue
        if call.get("status") != "completed":
            raise ContractError("smoke call has unknown status")
        for field in (
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "wall_time_s",
            "gpu_active_time_s",
            "peak_gpu_memory_bytes",
            "gpu_accounting_samples",
        ):
            if call.get(field) is None:
                raise ContractError(f"completed smoke call lacks {field}")
        parse += int(bool(call.get("parse_ok")))
        truncation += int(bool(call.get("truncated")))
    if any(arms != EXPECTED_ARMS for arms in units.values()):
        raise ContractError("smoke does not contain complete paired T/V/H units")
    if infra:
        raise ContractError(f"smoke has {infra} infrastructure failures")

    inventory = {
        str(path.relative_to(args.run_root)): sha256_bytes(path.read_bytes())
        for path in call_paths
    }
    inference = config["inference"]
    payload = {
        "schema_version": "RQ1VisOpsSmokeQualificationV1",
        "status": "passed",
        "model": args.model,
        "experiment_id": config["experiment_id"],
        "experiment_config_hash": expected_config_hash,
        "roster_contract_hash": expected_roster_hash,
        "roster_assignment_hash": roster["assignment_hash"],
        "prepared_artifact_inventory_hash": index["artifact_inventory_hash"],
        "calls": len(calls),
        "paired_units": len(units),
        "infrastructure_failures": infra,
        "parse_rate_diagnostic_only": parse / len(calls),
        "truncations_diagnostic_only": truncation,
        "correctness_is_gate": False,
        "parse_acceptance_is_gate": False,
        "accounting_complete": True,
        "max_model_len": inference["max_model_len"],
        "max_tokens": inference["max_tokens"],
        "call_artifact_inventory_sha256": stable_hash(inventory),
    }
    payload["qualification_sha256"] = stable_hash(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

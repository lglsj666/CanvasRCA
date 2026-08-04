#!/usr/bin/env python3
"""Verify the complete main/sham, Stage-1/Stage-2 RQ1b3 smoke pipeline."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash
from rq1lib.settings import assert_execution_config, load_yaml_config


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractError(f"{path} is not a JSON object")
    return payload


def _calls(root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    if not (root / "summary.json").is_file():
        raise ContractError(f"smoke run is incomplete under {root}")
    paths = sorted((root / "calls").glob("*.json"))
    inventory = {
        str(path.relative_to(root)): sha256_bytes(path.read_bytes()) for path in paths
    }
    inventory["summary.json"] = sha256_bytes((root / "summary.json").read_bytes())
    return [_load(path) for path in paths], inventory


def _accounting_complete(record: Mapping[str, Any]) -> bool:
    return all(
        record.get(field) is not None
        for field in (
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "wall_time_s",
            "gpu_active_time_s",
            "peak_gpu_memory_bytes",
            "gpu_accounting_samples",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--prepared-index", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--main-stage1", type=Path, required=True)
    parser.add_argument("--main-stage2", type=Path, required=True)
    parser.add_argument("--sham-stage1", type=Path, required=True)
    parser.add_argument("--sham-stage2", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    assert_execution_config(config)
    task_profile = str(config.get("visops", {}).get("task_profile"))
    if task_profile not in {
        "two_stage_onset_ledger_v1",
        "two_stage_onset_ledger_v2",
    }:
        raise ContractError("RQ1b3 smoke verifier requires the onset-ledger profile")
    expected_transport = str(config["contracts"]["structured_output_transport"])
    roster = _load(args.roster)
    index = _load(args.prepared_index)
    task_count = int(index.get("task_count", -1))
    incident_count = int(index.get("n_cases", -1))
    if task_count != incident_count or incident_count != 3:
        raise ContractError("RQ1b3 smoke requires one task for each of three cases")
    config_hash = stable_hash(config)
    roster_hash = stable_hash(roster)
    if (
        index.get("experiment_id") != config["experiment_id"]
        or index.get("experiment_config_hash") != config_hash
        or index.get("roster_contract_hash") != roster_hash
        or index.get("roster_assignment_hash") != roster.get("assignment_hash")
    ):
        raise ContractError("RQ1b3 smoke index differs from config or roster")

    cells: dict[str, list[dict[str, Any]]] = {}
    inventory: dict[str, Any] = {}
    for name, root in (
        ("main_stage1", args.main_stage1),
        ("main_stage2", args.main_stage2),
        ("sham_stage1", args.sham_stage1),
        ("sham_stage2", args.sham_stage2),
    ):
        cells[name], cell_inventory = _calls(root)
        inventory[name] = cell_inventory
    expected_counts = {
        "main_stage1": task_count * 3,
        "main_stage2": task_count * 4,
        "sham_stage1": task_count * 2,
        "sham_stage2": task_count * 2,
    }
    for name, expected in expected_counts.items():
        if len(cells[name]) != expected:
            raise ContractError(
                f"{name} call count {len(cells[name])} differs from {expected}"
            )

    infra = 0
    truncations = 0
    for name, records in cells.items():
        for record in records:
            if (
                record.get("experiment_id") != config["experiment_id"]
                or record.get("experiment_config_hash") != config_hash
                or record.get("roster_contract_hash") != roster_hash
                or record.get("roster_assignment_hash") != roster.get("assignment_hash")
                or record.get("model") != args.model
            ):
                raise ContractError(f"{name} contains a foreign call contract")
            if record.get("status") == "infrastructure_error":
                infra += 1
                continue
            if record.get("status") != "completed":
                raise ContractError(f"{name} contains an unknown call status")
            if record.get("parse_ok") is not True:
                raise ContractError(f"{name} contains a parse failure")
            if record.get("structured_output_transport") != expected_transport:
                raise ContractError(f"{name} contains a foreign output transport")
            if task_profile == "two_stage_onset_ledger_v2" and not record.get(
                "guided_regex_sha256"
            ):
                raise ContractError(f"{name} lacks its guided-regex hash")
            if not _accounting_complete(record):
                raise ContractError(f"{name} lacks token/GPU accounting")
            truncations += int(bool(record.get("truncated")))

    if infra:
        raise ContractError(f"RQ1b3 smoke has {infra} infrastructure failures")
    for record in cells["main_stage1"]:
        if (
            record.get("stage") != "stage1_observe_compose"
            or record.get("condition") != "main"
            or record.get("arm") not in {"T", "V", "H"}
            or record.get("public_answer_type") != "panel_onset_ledger"
        ):
            raise ContractError("main Stage-1 smoke contract differs")
    for record in cells["sham_stage1"]:
        if (
            record.get("stage") != "stage1_observe_compose"
            or record.get("condition") != "row_sham"
            or record.get("arm") not in {"V", "H"}
        ):
            raise ContractError("sham Stage-1 smoke contract differs")
    for name in ("main_stage2", "sham_stage2"):
        for record in cells[name]:
            if (
                record.get("stage") != "stage2_select_from_frozen_ledger"
                or record.get("original_image_or_text_access") is not False
                or record.get("public_answer_type") != "sorted_string_set"
            ):
                raise ContractError(f"{name} Stage-2 evidence boundary differs")
    main_experimental = [
        row for row in cells["main_stage2"] if not row.get("oracle_diagnostic")
    ]
    oracle = [row for row in cells["main_stage2"] if row.get("oracle_diagnostic")]
    if (
        {str(row.get("arm")) for row in main_experimental} != {"T", "V", "H"}
        or any(row.get("condition") != "main" for row in main_experimental)
        or len(oracle) != incident_count
        or any(
            row.get("arm") != "O" or row.get("condition") != "oracle" for row in oracle
        )
    ):
        raise ContractError("main Stage-2 experimental/oracle cells differ")
    if any(
        row.get("arm") not in {"V", "H"}
        or row.get("condition") != "row_sham"
        or row.get("oracle_diagnostic")
        for row in cells["sham_stage2"]
    ):
        raise ContractError("sham Stage-2 cell differs")
    oracle_accuracy = sum(bool(row.get("correct")) for row in oracle) / len(oracle)
    minimum_oracle = float(
        config["gates"]["rq1b3_smoke"]["oracle_stage2_exact_accuracy_minimum"]
    )
    if oracle_accuracy < minimum_oracle:
        raise ContractError(
            f"oracle Stage-2 accuracy {oracle_accuracy:.6f} below {minimum_oracle:.6f}"
        )

    inference = config["inference"]
    payload = {
        "schema_version": "RQ1VisOpsSmokeQualificationV1",
        "status": "passed",
        "model": args.model,
        "experiment_id": config["experiment_id"],
        "experiment_config_hash": config_hash,
        "roster_contract_hash": roster_hash,
        "roster_assignment_hash": roster["assignment_hash"],
        "prepared_artifact_inventory_hash": index["artifact_inventory_hash"],
        "calls": sum(len(records) for records in cells.values()),
        "paired_units": task_count,
        "main_stage1_calls": len(cells["main_stage1"]),
        "main_stage2_calls": len(cells["main_stage2"]),
        "sham_stage1_calls": len(cells["sham_stage1"]),
        "sham_stage2_calls": len(cells["sham_stage2"]),
        "infrastructure_failures": infra,
        "parse_rate_diagnostic_only": 1.0,
        "structured_output_contract_verified": True,
        "answer_types_verified": ["panel_onset_ledger"],
        "stage2_original_evidence_access_verified_false": True,
        "oracle_stage2_exact_accuracy": oracle_accuracy,
        "truncations_diagnostic_only": truncations,
        "correctness_is_gate": False,
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

#!/usr/bin/env python3
"""Freeze the preregistered Gemma operation router from a valid RQ1b mapping."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash
from rq1lib.settings import assert_execution_config, load_yaml_config

PRIMARY_MODEL = "gemma-4-26b-a4b"
ARM_TIE_ORDER = ("T", "V", "H")
ANALYSIS_SCHEMA = "RQ1VisOpsPairedAnalysisV3"


def _registered_operations(config: dict[str, Any]) -> set[str]:
    families = dict(config.get("visops", {}).get("operation_families") or {})
    return {
        str(operation)
        for operations in families.values()
        for operation in operations
    }


def freeze_router(
    analysis: dict[str, Any],
    *,
    analysis_sha256: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Return a deterministic router artifact or fail closed."""

    if analysis.get("schema_version") != ANALYSIS_SCHEMA:
        raise ContractError("router source is not the registered V3 analysis")
    if analysis.get("status") != "valid" or not analysis.get(
        "confirmatory_claim_allowed"
    ):
        raise ContractError("router source analysis did not pass every model gate")
    if analysis.get("expected_arms") != ["T", "V", "H"]:
        raise ContractError("router source arms differ from registered T/V/H")

    models = dict(analysis.get("models") or {})
    if PRIMARY_MODEL not in models:
        raise ContractError("router source lacks the registered primary Gemma model")
    primary = dict(models[PRIMARY_MODEL])
    if primary.get("status") != "valid" or not primary.get(
        "confirmatory_claim_allowed"
    ):
        raise ContractError("primary Gemma mapping is not valid")
    if int(primary.get("included_incidents", -1)) != 90:
        raise ContractError("primary Gemma mapping did not retain all 90 incidents")
    if primary.get("parse_rate_failures"):
        raise ContractError("primary Gemma mapping has a parse-rate failure")
    if float(primary.get("infrastructure_exclusion", {}).get("fraction", -1)) > 0.05:
        raise ContractError("primary Gemma infrastructure exclusion exceeds 5%")

    registered = _registered_operations(config)
    per_operation = dict(primary.get("per_operation") or {})
    if set(per_operation) != registered:
        raise ContractError(
            "analysis operation inventory differs from config: "
            f"analysis={sorted(per_operation)} registered={sorted(registered)}"
        )

    choices: dict[str, dict[str, Any]] = {}
    for operation in sorted(registered):
        report = dict(per_operation[operation])
        query_level = dict(report.get("query_level_descriptive") or {})
        arms = dict(query_level.get("arms") or {})
        accuracies = {
            arm: float(dict(arms.get(arm) or {}).get("accuracy", -1.0))
            for arm in ARM_TIE_ORDER
        }
        if any(value < 0.0 or value > 1.0 for value in accuracies.values()):
            raise ContractError(f"{operation}: invalid mapping accuracy {accuracies}")
        best = max(accuracies.values())
        selected = next(arm for arm in ARM_TIE_ORDER if accuracies[arm] == best)
        case_accuracies = {
            arm: float(
                dict(report.get("case_level", {}).get("arms", {}).get(arm) or {}).get(
                    "case_macro_accuracy", -1.0
                )
            )
            for arm in ARM_TIE_ORDER
        }
        if any(value < 0.0 or value > 1.0 for value in case_accuracies.values()):
            raise ContractError(
                f"{operation}: invalid case-level mapping accuracy {case_accuracies}"
            )
        choices[operation] = {
            "selected_arm": selected,
            "mapping_query_accuracy": accuracies,
            "mapping_case_macro_accuracy": case_accuracies,
            "selection_reason": (
                "highest_accuracy"
                if sum(value == best for value in accuracies.values()) == 1
                else "exact_tie_resolved_by_T_then_V_then_H"
            ),
        }

    payload: dict[str, Any] = {
        "schema_version": "RQ1VisOpsRouterV1",
        "status": "frozen",
        "decision": "DD-26",
        "source_experiment_id": config["experiment_id"],
        "source_experiment_config_hash": stable_hash(config),
        "source_analysis_schema": ANALYSIS_SCHEMA,
        "source_analysis_sha256": analysis_sha256,
        "mapping_model": PRIMARY_MODEL,
        "architecture_control_policy": "qwen_uses_identical_gemma_router",
        "selection_metric": "per_operation_query_accuracy",
        "tie_order": list(ARM_TIE_ORDER),
        "operations": choices,
    }
    payload["router_contract_sha256"] = stable_hash(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    assert_execution_config(config)
    analysis_bytes = args.analysis.read_bytes()
    analysis = json.loads(analysis_bytes)
    if not isinstance(analysis, dict):
        raise ContractError("source analysis is not an object")
    payload = freeze_router(
        analysis,
        analysis_sha256=sha256_bytes(analysis_bytes),
        config=config,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

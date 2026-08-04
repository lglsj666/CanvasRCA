#!/usr/bin/env python3
"""Evaluate the frozen RQ1b operation router on the disjoint gate roster."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import analyze_rq1_visops as base
from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash
from rq1lib.settings import assert_execution_config, load_yaml_config

RQ_ROOT = Path(__file__).resolve().parents[1]
ROOT = RQ_ROOT.parents[1]
PRIMARY_MODEL = "gemma-4-26b-a4b"
ARM_TIE_ORDER = ("T", "V", "H")
STRUCTURAL_FAMILIES = {
    "temporal_scanning",
    "topology_path",
    "cross_modal_alignment",
}


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise base.AnalysisError(f"{path} is not a JSON object")
    return payload


def _validate_router(router: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    if (
        router.get("schema_version") != "RQ1VisOpsRouterV1"
        or router.get("status") != "frozen"
        or router.get("mapping_model") != PRIMARY_MODEL
        or router.get("architecture_control_policy")
        != "qwen_uses_identical_gemma_router"
        or router.get("tie_order") != list(ARM_TIE_ORDER)
    ):
        raise base.AnalysisError("frozen router contract differs")
    operations = dict(router.get("operations") or {})
    registered = {
        str(operation)
        for values in config["visops"]["operation_families"].values()
        for operation in values
    }
    if set(operations) != registered:
        raise base.AnalysisError("frozen router operation inventory differs")
    if any(
        dict(choice).get("selected_arm") not in ARM_TIE_ORDER
        for choice in operations.values()
    ):
        raise base.AnalysisError("frozen router contains an unknown arm")
    unhashed = dict(router)
    expected = unhashed.pop("router_contract_sha256", None)
    if expected != stable_hash(unhashed):
        raise base.AnalysisError("frozen router self-hash differs")


def _eligible_units(
    records: Sequence[Mapping[str, Any]],
    model: str,
    *,
    maximum_exclusion_fraction: float,
) -> dict[tuple[str, str], dict[str, Mapping[str, Any]]]:
    indexed = base._validate_and_index(records)
    if model not in indexed:
        raise base.AnalysisError(f"gate records lack model {model}")
    units = indexed[model]
    incidents = {incident for incident, _query in units}
    infrastructure = {
        incident
        for (incident, _query), arms in units.items()
        if any(row.get("status") == "infrastructure_error" for row in arms.values())
    }
    fraction = len(infrastructure) / len(incidents)
    if fraction > maximum_exclusion_fraction:
        raise base.AnalysisError(
            f"model {model} infrastructure exclusion {fraction:.6f} exceeds "
            f"{maximum_exclusion_fraction:.6f}"
        )
    return {
        key: dict(arms) for key, arms in units.items() if key[0] not in infrastructure
    }


def _case_vectors(
    units: Mapping[tuple[str, str], Mapping[str, Mapping[str, Any]]],
    keys: Sequence[tuple[str, str]],
    lhs_selector: Callable[[Mapping[str, Mapping[str, Any]]], str],
    rhs_selector: Callable[[Mapping[str, Mapping[str, Any]]], str],
) -> tuple[list[str], list[float], list[float]]:
    by_case: dict[str, tuple[list[float], list[float]]] = defaultdict(lambda: ([], []))
    for key in keys:
        incident, _query = key
        arms = units[key]
        lhs_arm = lhs_selector(arms)
        rhs_arm = rhs_selector(arms)
        by_case[incident][0].append(base._validated_score(arms[lhs_arm]))
        by_case[incident][1].append(base._validated_score(arms[rhs_arm]))
    if not by_case:
        raise base.AnalysisError("gate comparison has no eligible cases")
    cases = sorted(by_case)
    lhs = [statistics.fmean(by_case[case][0]) for case in cases]
    rhs = [statistics.fmean(by_case[case][1]) for case in cases]
    return cases, lhs, rhs


def _comparison(
    units: Mapping[tuple[str, str], Mapping[str, Mapping[str, Any]]],
    keys: Sequence[tuple[str, str]],
    *,
    lhs_selector: Callable[[Mapping[str, Mapping[str, Any]]], str],
    rhs_selector: Callable[[Mapping[str, Mapping[str, Any]]], str],
    lhs_name: str,
    rhs_name: str,
    include_inference: bool,
) -> dict[str, Any]:
    cases, lhs, rhs = _case_vectors(units, keys, lhs_selector, rhs_selector)
    report = base._case_paired_comparison(
        lhs,
        rhs,
        lhs_arm=lhs_name,
        rhs_arm=rhs_name,
        include_inference=include_inference,
    )
    report["case_ids_reported"] = False
    report["queries"] = len(keys)
    report["cases"] = len(cases)
    return report


def _p_below(report: Mapping[str, Any], threshold: float) -> bool:
    test = dict(report.get("wilcoxon_signed_rank") or {})
    value = test.get("p_value")
    return (
        bool(test.get("available"))
        and isinstance(value, (int, float))
        and (float(value) < threshold)
    )


def analyze_gate_records(
    records: Sequence[Mapping[str, Any]],
    *,
    router: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply the frozen router and registered thresholds without refitting."""

    _validate_router(router, config)
    maximum_exclusion = float(
        config["integrity"][
            "maximum_paired_whole_case_infrastructure_exclusion_fraction"
        ]
    )
    minimum_parse = float(config["integrity"]["minimum_parse_rate"])
    fixed = base.analyze_records(
        records,
        maximum_exclusion_fraction=maximum_exclusion,
        minimum_parse_rate=minimum_parse,
    )
    choices = {
        operation: str(choice["selected_arm"])
        for operation, choice in dict(router["operations"]).items()
    }
    selected_structural = sorted(
        operation
        for operation, arm in choices.items()
        if arm != "T"
        and any(
            operation in operations
            for family, operations in config["visops"]["operation_families"].items()
            if family in STRUCTURAL_FAMILIES
        )
    )

    def routed(arms: Mapping[str, Mapping[str, Any]]) -> str:
        operation = base._required_string(arms["T"], "operation")
        return choices[operation]

    def fixed_arm(name: str) -> Callable[[Mapping[str, Mapping[str, Any]]], str]:
        return lambda _arms: name

    model_reports: dict[str, Any] = {}
    for model, fixed_model in fixed["models"].items():
        units = _eligible_units(
            records,
            model,
            maximum_exclusion_fraction=maximum_exclusion,
        )
        ordered = sorted(units)
        structural_keys = [
            key
            for key in ordered
            if base._required_string(units[key]["T"], "operation")
            in selected_structural
        ]
        structural = _comparison(
            units,
            structural_keys,
            lhs_selector=routed,
            rhs_selector=fixed_arm("T"),
            lhs_name="R",
            rhs_name="T",
            include_inference=True,
        )

        per_dataset: dict[str, Any] = {}
        datasets = sorted(
            {
                base._optional_analysis_metadata(units[key]["T"], "analysis_dataset")
                for key in structural_keys
            }
            - {None}
        )
        for dataset in datasets:
            dataset_keys = [
                key
                for key in structural_keys
                if base._optional_analysis_metadata(units[key]["T"], "analysis_dataset")
                == dataset
            ]
            per_dataset[str(dataset)] = _comparison(
                units,
                dataset_keys,
                lhs_selector=routed,
                rhs_selector=fixed_arm("T"),
                lhs_name="R",
                rhs_name="T",
                include_inference=False,
            )

        fixed_accuracies = {
            arm: float(
                fixed_model["primary_case_level"]["arms"][arm]["case_macro_accuracy"]
            )
            for arm in ARM_TIE_ORDER
        }
        best_accuracy = max(fixed_accuracies.values())
        best_fixed = next(
            arm for arm in ARM_TIE_ORDER if fixed_accuracies[arm] == best_accuracy
        )
        routed_vs_best = _comparison(
            units,
            ordered,
            lhs_selector=routed,
            rhs_selector=fixed_arm(best_fixed),
            lhs_name="R",
            rhs_name=best_fixed,
            include_inference=True,
        )

        exact_control = fixed_model["per_family"]["exact_lookup"]["case_level"][
            "comparisons"
        ]["V-T"]
        exact_delta = float(exact_control["delta_case_macro_accuracy"])
        positive_datasets = sum(
            float(report["delta_case_macro_accuracy"]) > 0.0
            for report in per_dataset.values()
        )
        no_material_reverse = all(
            float(report["delta_case_macro_accuracy"]) > -0.10
            for report in per_dataset.values()
        )
        checks = {
            "integrity": bool(fixed_model["confirmatory_claim_allowed"]),
            "non_text_structural_operation_selected": bool(selected_structural),
            "structural_delta_at_least_0_10": float(
                structural["delta_case_macro_accuracy"]
            )
            >= 0.10,
            "structural_wilcoxon_p_below_0_05": _p_below(structural, 0.05),
            "structural_positive_in_at_least_two_datasets": positive_datasets >= 2,
            "no_dataset_at_or_below_minus_0_10": no_material_reverse,
            "exact_lookup_T_not_worse_than_V_by_more_than_0_05": exact_delta <= 0.05,
            "routed_minus_best_fixed_at_least_0_05": float(
                routed_vs_best["delta_case_macro_accuracy"]
            )
            >= 0.05,
            "routed_vs_best_fixed_wilcoxon_p_below_0_05": _p_below(
                routed_vs_best, 0.05
            ),
        }
        model_reports[model] = {
            "status": "passed" if all(checks.values()) else "failed",
            "checks": checks,
            "selected_structural_operations": selected_structural,
            "structural_routed_vs_text": structural,
            "structural_routed_vs_text_per_dataset": per_dataset,
            "fixed_arm_case_macro_accuracy": fixed_accuracies,
            "best_fixed_arm": best_fixed,
            "routed_vs_best_fixed": routed_vs_best,
            "exact_lookup_control": {
                "comparison": "V-T",
                "delta_case_macro_accuracy": exact_delta,
                "threshold": "V-T <= 0.05",
                "passed": exact_delta <= 0.05,
            },
            "fixed_arm_analysis": fixed_model,
        }

    if PRIMARY_MODEL not in model_reports:
        raise base.AnalysisError("gate analysis lacks the primary Gemma model")
    integrity_complete = bool(fixed["confirmatory_claim_allowed"])
    primary_passed = model_reports[PRIMARY_MODEL]["status"] == "passed"
    status = (
        "incomplete_model_gate"
        if not integrity_complete
        else "passed"
        if primary_passed
        else "failed"
    )
    payload: dict[str, Any] = {
        "schema_version": "RQ1VisOpsIndependentGateAnalysisV1",
        "status": status,
        "primary_model": PRIMARY_MODEL,
        "primary_gate_passed": integrity_complete and primary_passed,
        "architecture_control_changes_primary_decision": False,
        "mapping_and_gate_are_disjoint": True,
        "router_refit_on_gate": False,
        "router_contract_sha256": router["router_contract_sha256"],
        "router_source_analysis_sha256": router["source_analysis_sha256"],
        "selected_structural_operations": selected_structural,
        "thresholds": {
            "structural_routed_minus_text": 0.10,
            "structural_wilcoxon_alpha": 0.05,
            "positive_dataset_count": 2,
            "dataset_material_reverse_floor": -0.10,
            "exact_lookup_V_minus_T_ceiling": 0.05,
            "routed_minus_best_fixed": 0.05,
            "routed_vs_best_fixed_wilcoxon_alpha": 0.05,
            "minimum_parse_rate": minimum_parse,
            "maximum_infrastructure_exclusion_fraction": maximum_exclusion,
        },
        "models": model_reports,
        "fixed_arm_analysis_status": fixed["status"],
        "confidence_intervals_reported": False,
    }
    payload["analysis_contract_sha256"] = stable_hash(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--router", type=Path, required=True)
    parser.add_argument("--private-roster", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    assert_execution_config(config)
    configured_router = (
        ROOT / config["contracts"]["frozen_operation_router"]
    ).resolve()
    if args.router.resolve() != configured_router:
        raise ContractError("gate analyzer router differs from registered config")
    router_bytes = args.router.read_bytes()
    if (
        sha256_bytes(router_bytes)
        != config["contracts"]["frozen_operation_router_file_sha256"]
    ):
        raise ContractError("gate analyzer router file hash differs")
    router = json.loads(router_bytes)

    records = base.load_call_records(args.inputs)
    private_roster = _load_object(args.private_roster)
    records = base.enrich_records_from_private_roster(records, private_roster)
    report = analyze_gate_records(records, router=router, config=config)
    report["evaluator_only_metadata_enrichment"] = {
        "applied": True,
        "roster_assignment_hash": private_roster["assignment_hash"],
        "private_case_ids_in_report": False,
    }
    report["source_call_inventory_sha256"] = stable_hash(
        sorted(
            (
                {
                    "model": row["model"],
                    "opaque_incident_id": row["opaque_incident_id"],
                    "query_id": row["query_id"],
                    "arm": row["arm"],
                    "source_file_sha256": sha256_bytes(
                        Path(str(row["_source_path"])).read_bytes()
                    ),
                }
                for row in records
            ),
            key=lambda item: (
                item["model"],
                item["opaque_incident_id"],
                item["query_id"],
                item["arm"],
            ),
        )
    )
    serialized = canonical_json(report) + "\n"
    output = args.output.resolve()
    results_root = (RQ_ROOT / "results").resolve()
    if results_root not in output.parents:
        raise base.AnalysisError("gate analysis output must be below RQ1 results")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialized, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Registered incident-level analysis for RQ1b2 compositional complexity."""

from __future__ import annotations

import argparse
import json
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import analyze_rq1_visops as base
from rq1lib.settings import assert_execution_config, load_yaml_config

RQ_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_MODEL = "gemma-4-26b-a4b"
ARMS = ("T", "V", "H")
LOW = "raw_temporal_onset_low"
HIGH = "raw_temporal_onset_high"


def _eligible_units(
    records: Sequence[Mapping[str, Any]],
    model: str,
    *,
    maximum_exclusion_fraction: float,
) -> dict[tuple[str, str], dict[str, Mapping[str, Any]]]:
    indexed = base._validate_and_index(records)
    if model not in indexed:
        raise base.AnalysisError(f"records lack model {model}")
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


def _temporal_by_incident(
    units: Mapping[tuple[str, str], Mapping[str, Mapping[str, Any]]],
) -> dict[str, dict[str, Mapping[str, Mapping[str, Any]]]]:
    by_incident: dict[str, dict[str, Mapping[str, Mapping[str, Any]]]] = {}
    for (incident, _query), arms in units.items():
        operation = base._required_string(arms["T"], "operation")
        if operation not in {LOW, HIGH}:
            continue
        operations = by_incident.setdefault(incident, {})
        if operation in operations:
            raise base.AnalysisError(
                f"incident {incident} has duplicate {operation} queries"
            )
        operations[operation] = arms
    partial = sorted(
        incident
        for incident, operations in by_incident.items()
        if set(operations) != {LOW, HIGH}
    )
    if partial:
        raise base.AnalysisError(
            f"temporal low/high pairing differs for incidents {partial}"
        )
    if not by_incident:
        raise base.AnalysisError("no paired temporal low/high incidents")
    return by_incident


def _score(arms: Mapping[str, Mapping[str, Any]], arm: str) -> float:
    return base._validated_score(arms[arm])


def _comparison(
    lhs: Sequence[float],
    rhs: Sequence[float],
    *,
    lhs_name: str,
    rhs_name: str,
    include_inference: bool,
) -> dict[str, Any]:
    return base._case_paired_comparison(
        lhs,
        rhs,
        lhs_arm=lhs_name,
        rhs_arm=rhs_name,
        include_inference=include_inference,
    )


def _interaction_report(
    high_effects: Sequence[float],
    low_effects: Sequence[float],
    *,
    include_inference: bool,
) -> dict[str, Any]:
    if len(high_effects) != len(low_effects) or not high_effects:
        raise base.AnalysisError("complexity interaction vectors are unequal or empty")
    interactions = [high - low for high, low in zip(high_effects, low_effects)]
    report: dict[str, Any] = {
        "paired_cases": len(interactions),
        "high_visual_minus_text_mean": statistics.fmean(high_effects),
        "low_visual_minus_text_mean": statistics.fmean(low_effects),
        "interaction_mean": statistics.fmean(interactions),
        "positive_cases": sum(value > 0 for value in interactions),
        "negative_cases": sum(value < 0 for value in interactions),
        "tied_cases": sum(value == 0 for value in interactions),
        "inferential_statistics_reported": include_inference,
    }
    if include_inference:
        report["wilcoxon_signed_rank"] = base._wilcoxon_pratt(interactions)
        report.update(base._cohen_dz(interactions))
    return report


def _p_below(report: Mapping[str, Any], threshold: float) -> bool:
    test = dict(report.get("wilcoxon_signed_rank") or {})
    value = test.get("p_value")
    return bool(test.get("available")) and isinstance(value, (int, float)) and (
        float(value) < threshold
    )


def _temporal_report(
    temporal: Mapping[str, Mapping[str, Mapping[str, Mapping[str, Any]]]],
    *,
    include_inference: bool,
) -> dict[str, Any]:
    incidents = sorted(temporal)
    low = {
        arm: [_score(temporal[incident][LOW], arm) for incident in incidents]
        for arm in ARMS
    }
    high = {
        arm: [_score(temporal[incident][HIGH], arm) for incident in incidents]
        for arm in ARMS
    }
    high_vt = _comparison(
        high["V"],
        high["T"],
        lhs_name="V_high",
        rhs_name="T_high",
        include_inference=include_inference,
    )
    low_vt = _comparison(
        low["V"],
        low["T"],
        lhs_name="V_low",
        rhs_name="T_low",
        include_inference=include_inference,
    )
    high_effects = [left - right for left, right in zip(high["V"], high["T"])]
    low_effects = [left - right for left, right in zip(low["V"], low["T"])]

    policy = [
        statistics.fmean((low["T"][index], high["V"][index]))
        for index in range(len(incidents))
    ]
    fixed = {
        arm: [
            statistics.fmean((low[arm][index], high[arm][index]))
            for index in range(len(incidents))
        ]
        for arm in ARMS
    }
    fixed_accuracy = {arm: statistics.fmean(values) for arm, values in fixed.items()}
    best_value = max(fixed_accuracy.values())
    best_arm = next(arm for arm in ARMS if fixed_accuracy[arm] == best_value)
    policy_vs_best = _comparison(
        policy,
        fixed[best_arm],
        lhs_name="policy_low_T_high_V",
        rhs_name=f"fixed_{best_arm}",
        include_inference=include_inference,
    )
    query_high = base._query_paired_comparison(
        high["V"], high["T"], lhs_arm="V_high", rhs_arm="T_high"
    )
    return {
        "unit": "opaque_incident_id",
        "paired_cases": len(incidents),
        "case_ids_reported": False,
        "high_visual_vs_text": high_vt,
        "low_visual_vs_text": low_vt,
        "complexity_interaction": _interaction_report(
            high_effects, low_effects, include_inference=include_inference
        ),
        "high_query_discordance": query_high,
        "fixed_arm_temporal_accuracy": fixed_accuracy,
        "best_fixed_arm": best_arm,
        "policy_low_T_high_V_vs_best_fixed": policy_vs_best,
        "secondary_comparisons": {
            level: {
                f"{lhs}-{rhs}": _comparison(
                    values[lhs],
                    values[rhs],
                    lhs_name=f"{lhs}_{level}",
                    rhs_name=f"{rhs}_{level}",
                    include_inference=include_inference,
                )
                for lhs, rhs in (("H", "T"), ("H", "V"))
            }
            for level, values in (("low", low), ("high", high))
        },
    }


def _analyze_model(
    records: Sequence[Mapping[str, Any]],
    *,
    model: str,
    fixed_model_report: Mapping[str, Any],
    config: Mapping[str, Any],
    confirmatory: bool,
) -> dict[str, Any]:
    maximum_exclusion = float(
        config["integrity"][
            "maximum_paired_whole_case_infrastructure_exclusion_fraction"
        ]
    )
    units = _eligible_units(
        records, model, maximum_exclusion_fraction=maximum_exclusion
    )
    temporal = _temporal_by_incident(units)
    temporal_report = _temporal_report(temporal, include_inference=True)

    per_dataset: dict[str, Any] = {}
    datasets = sorted(
        {
            base._optional_analysis_metadata(operations[LOW]["T"], "analysis_dataset")
            for operations in temporal.values()
        }
        - {None}
    )
    for dataset in datasets:
        subset = {
            incident: operations
            for incident, operations in temporal.items()
            if base._optional_analysis_metadata(
                operations[LOW]["T"], "analysis_dataset"
            )
            == dataset
        }
        per_dataset[str(dataset)] = _temporal_report(
            subset, include_inference=False
        )

    high = temporal_report["high_visual_vs_text"]
    interaction = temporal_report["complexity_interaction"]
    discordance = temporal_report["high_query_discordance"]
    policy = temporal_report["policy_low_T_high_V_vs_best_fixed"]
    if confirmatory:
        positive_datasets = sum(
            float(report["high_visual_vs_text"]["delta_case_macro_accuracy"]) > 0
            for report in per_dataset.values()
        )
        checks = {
            "integrity": bool(fixed_model_report["confirmatory_claim_allowed"]),
            "P1_high_V_minus_T_at_least_0_10": float(
                high["delta_case_macro_accuracy"]
            )
            >= 0.10,
            "P1_pratt_p_below_0_05": _p_below(high, 0.05),
            "P2_interaction_at_least_0_10": float(interaction["interaction_mean"])
            >= 0.10,
            "P2_pratt_p_below_0_05": _p_below(interaction, 0.05),
            "P3_policy_above_best_fixed_at_least_0_05": float(
                policy["delta_case_macro_accuracy"]
            )
            >= 0.05,
            "P3_pratt_p_below_0_05": _p_below(policy, 0.05),
            "high_V_minus_T_positive_in_at_least_two_datasets": (
                positive_datasets >= 2
            ),
            "no_dataset_high_V_minus_T_at_or_below_minus_0_10": all(
                float(report["high_visual_vs_text"]["delta_case_macro_accuracy"])
                > -0.10
                for report in per_dataset.values()
            ),
        }
    else:
        checks = {
            "integrity": bool(fixed_model_report["confirmatory_claim_allowed"]),
            "high_V_minus_T_at_least_0_05": float(
                high["delta_case_macro_accuracy"]
            )
            >= 0.05,
            "complexity_interaction_positive": float(interaction["interaction_mean"])
            > 0.0,
            "high_visual_repairs_exceed_breaks": int(discordance["repairs"])
            > int(discordance["breaks"]),
        }
    status = (
        "incomplete_integrity"
        if not checks["integrity"]
        else "passed"
        if all(checks.values())
        else "failed"
    )
    return {
        "status": status,
        "checks": checks,
        "temporal_primary": temporal_report,
        "temporal_per_dataset": per_dataset,
        "exact_lookup_control": fixed_model_report["per_operation"].get(
            "metric_exact_lookup"
        ),
        "topology_secondary": {
            operation: fixed_model_report["per_operation"][operation]
            for operation in (
                "directed_shortest_path_low",
                "directed_shortest_path_high",
            )
            if operation in fixed_model_report["per_operation"]
        },
        "all_tasks_fixed_arm_analysis": fixed_model_report,
    }


def analyze_compositional_records(
    records: Sequence[Mapping[str, Any]], *, config: Mapping[str, Any]
) -> dict[str, Any]:
    """Apply the frozen RQ1b2 development or independent-gate decision rule."""

    stage = str(config["execution"].get("stage") or "")
    confirmatory = "independent_gate" in stage
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
    model_reports = {
        model: _analyze_model(
            records,
            model=model,
            fixed_model_report=fixed_model,
            config=config,
            confirmatory=confirmatory,
        )
        for model, fixed_model in fixed["models"].items()
    }
    if PRIMARY_MODEL not in model_reports:
        raise base.AnalysisError("RQ1b2 analysis lacks primary Gemma")
    primary_status = model_reports[PRIMARY_MODEL]["status"]
    return {
        "schema_version": "RQ1b2CompositionalAnalysisV1",
        "status": primary_status,
        "analysis_stage": "independent_gate" if confirmatory else "development",
        "primary_model": PRIMARY_MODEL,
        "primary_gate_passed": primary_status == "passed",
        "qualification_gates_external": True,
        "primary_inferential_unit": "opaque_incident_id",
        "pratt_zero_method": True,
        "confidence_intervals_reported": False,
        "models": model_reports,
    }


def _markdown_summary(report: Mapping[str, Any]) -> str:
    lines = [
        "# RQ1b2 compositional-complexity analysis",
        "",
        f"- stage: `{report['analysis_stage']}`",
        f"- status: `{report['status']}`",
        f"- primary model: `{report['primary_model']}`",
        "- inferential unit: opaque incident (queries are not independent)",
        "",
        "| Model | High V-T | Interaction | Policy-best fixed | Repairs / breaks | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for model, model_report in report["models"].items():
        temporal = model_report["temporal_primary"]
        high = temporal["high_visual_vs_text"]["delta_case_macro_accuracy"]
        interaction = temporal["complexity_interaction"]["interaction_mean"]
        policy = temporal["policy_low_T_high_V_vs_best_fixed"][
            "delta_case_macro_accuracy"
        ]
        discordance = temporal["high_query_discordance"]
        lines.append(
            f"| {model} | {high:+.4f} | {interaction:+.4f} | {policy:+.4f} | "
            f"{discordance['repairs']} / {discordance['breaks']} | "
            f"{model_report['status']} |"
        )
    lines.extend(
        [
            "",
            (
                "The development gate is descriptive and does not use a p-value "
                "for promotion. The disjoint 150-case gate applies the registered "
                "Pratt-Wilcoxon tests."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--private-roster", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    assert_execution_config(config)
    records = base.load_call_records(args.inputs)
    private_roster = base._load_json(args.private_roster.resolve())
    records = base.enrich_records_from_private_roster(records, private_roster)
    report = analyze_compositional_records(records, config=config)
    report["evaluator_only_metadata_enrichment"] = {
        "applied": True,
        "roster_assignment_hash": private_roster["assignment_hash"],
        "private_case_ids_in_report": False,
    }
    serialized = json.dumps(
        report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
    )
    for path in (args.output.resolve(), args.markdown_output.resolve()):
        if RQ_ROOT.resolve() / "results" not in path.parents:
            raise base.AnalysisError("analysis output must be below RQs/RQ1/results/")
        path.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized + "\n", encoding="utf-8")
    args.markdown_output.write_text(_markdown_summary(report), encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

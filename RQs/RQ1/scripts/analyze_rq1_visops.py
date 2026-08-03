#!/usr/bin/env python3
"""Strict paired analysis for RQ1 RCA-VisOps call artifacts.

Calls are integrity-paired by ``(model, opaque_incident_id, query_id)``, but the
primary inferential unit is the opaque incident.  Query scores are first
averaged within each incident and arm before paired significance tests or
effect sizes are computed.  A single infrastructure failure excludes the
affected incident's complete T/V/H query set for that model.  Parse failures,
truncations, and otherwise invalid model outputs are model outcomes and remain
in the accuracy denominator.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import warnings
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

EXPECTED_ARMS = ("T", "V", "H")
COMPARISONS = (("V", "T"), ("H", "T"), ("H", "V"))
DEFAULT_MAX_INFRASTRUCTURE_EXCLUSION_FRACTION = 0.05
DEFAULT_MINIMUM_PARSE_RATE = 0.95
RQ_ROOT = Path(__file__).resolve().parents[1]


class AnalysisError(RuntimeError):
    """Raised when result artifacts cannot support the registered analysis."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"cannot read call record {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AnalysisError(f"call record is not a JSON object: {path}")
    return payload


def discover_call_files(inputs: Sequence[Path]) -> list[Path]:
    """Resolve call JSONs without accidentally ingesting cell summaries."""

    discovered: set[Path] = set()
    for supplied in inputs:
        path = supplied.resolve()
        if path.is_file():
            discovered.add(path)
            continue
        if not path.is_dir():
            raise AnalysisError(f"input does not exist: {path}")
        if path.name == "calls":
            candidates = path.glob("*.json")
        elif (path / "calls").is_dir():
            candidates = (path / "calls").glob("*.json")
        else:
            candidates = path.rglob("calls/*.json")
        discovered.update(candidate.resolve() for candidate in candidates)
    files = sorted(discovered)
    if not files:
        raise AnalysisError("no runner call JSON files were found")
    return files


def load_call_records(inputs: Sequence[Path]) -> list[dict[str, Any]]:
    """Load runner call records and attach their audit-only source paths."""

    records: list[dict[str, Any]] = []
    for path in discover_call_files(inputs):
        record = _load_json(path)
        record["_source_path"] = str(path)
        records.append(record)
    return records


def enrich_records_from_private_roster(
    records: Iterable[Mapping[str, Any]],
    private_roster: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Attach evaluator-only analysis strata without exposing private case IDs.

    The returned records are copies.  Only ``analysis_dataset`` and
    ``analysis_leakage_group_id`` cross the private-roster boundary.
    """

    if private_roster.get("schema_version") != "RQ1PrivateRosterV1":
        raise AnalysisError("unsupported private roster schema")
    if private_roster.get("private") is not True:
        raise AnalysisError("private roster is not marked private=true")
    if private_roster.get("status") != "frozen":
        raise AnalysisError("private roster status must be frozen")
    assignment_hash = private_roster.get("assignment_hash")
    if (
        not isinstance(assignment_hash, str)
        or len(assignment_hash) != 64
        or any(character not in "0123456789abcdef" for character in assignment_hash)
    ):
        raise AnalysisError("private roster assignment_hash is malformed")
    cases = private_roster.get("cases")
    if not isinstance(cases, list) or not cases:
        raise AnalysisError("private roster cases must be a non-empty list")
    if private_roster.get("n_cases") != len(cases):
        raise AnalysisError("private roster n_cases differs from cases")

    by_opaque: dict[str, tuple[str, str | None]] = {}
    for index, case in enumerate(cases):
        if not isinstance(case, Mapping):
            raise AnalysisError(f"private roster cases[{index}] is not an object")
        opaque = case.get("opaque_incident_id")
        private_case_id = case.get("private_case_id")
        dataset = case.get("analysis_dataset")
        leakage_group = case.get("analysis_leakage_group_id")
        if not isinstance(opaque, str) or not opaque:
            raise AnalysisError(
                f"private roster cases[{index}] lacks opaque_incident_id"
            )
        if opaque in by_opaque:
            raise AnalysisError("private roster contains duplicate opaque incident IDs")
        if not isinstance(private_case_id, str) or not private_case_id:
            raise AnalysisError(f"private roster cases[{index}] lacks private_case_id")
        if not isinstance(dataset, str) or not dataset:
            raise AnalysisError(f"private roster cases[{index}] lacks analysis_dataset")
        if leakage_group is not None and (
            not isinstance(leakage_group, str) or not leakage_group
        ):
            raise AnalysisError(
                f"private roster cases[{index}] has invalid analysis_leakage_group_id"
            )
        # Deliberately do not retain private_case_id in this mapping.
        by_opaque[opaque] = (dataset, leakage_group)

    enriched: list[dict[str, Any]] = []
    for record in records:
        if "private_case_id" in record:
            raise AnalysisError("call record must never contain private_case_id")
        opaque = _required_string(record, "opaque_incident_id")
        if record.get("roster_assignment_hash") != assignment_hash:
            raise AnalysisError(
                f"call roster_assignment_hash differs from private roster for {opaque}"
            )
        metadata = by_opaque.get(opaque)
        if metadata is None:
            raise AnalysisError(
                f"private roster has no mapping for opaque incident {opaque}"
            )
        dataset, leakage_group = metadata
        expected = {
            "analysis_dataset": dataset,
            "analysis_leakage_group_id": leakage_group,
        }
        copy = dict(record)
        for field, value in expected.items():
            if field in record and record.get(field) != value:
                raise AnalysisError(
                    f"call {field} differs from private roster for {opaque}"
                )
            copy[field] = value
        if "private_case_id" in copy:  # defensive invariant
            raise AnalysisError("private_case_id crossed the evaluator-only boundary")
        enriched.append(copy)
    if not enriched:
        raise AnalysisError("no call records supplied for private-roster enrichment")
    return enriched


def _required_string(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise AnalysisError(
            f"call record {record.get('_source_path', '<memory>')} lacks {field}"
        )
    return value


def _optional_analysis_metadata(record: Mapping[str, Any], field: str) -> str | None:
    value = record.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise AnalysisError(
            f"call record {record.get('_source_path', '<memory>')} has invalid {field}"
        )
    return value


def _validated_score(record: Mapping[str, Any]) -> float:
    """Return a binary model score without complete-case filtering."""

    if record.get("status") != "completed":
        raise AnalysisError("only completed records may be scored")
    score = record.get("score")
    if isinstance(score, bool):
        score = float(score)
    if not isinstance(score, (int, float)) or not math.isfinite(float(score)):
        raise AnalysisError(
            "completed call has no finite score: "
            f"{record.get('_source_path', '<memory>')}"
        )
    value = float(score)
    if value not in {0.0, 1.0}:
        raise AnalysisError(f"VisOps score must be binary, got {value}")
    # Parse failures are invalid outputs and cannot be rewarded.  A response
    # marked truncated is still retained and uses the runner's deterministic
    # score; for example, a complete answer may precede a truncated rationale.
    if not bool(record.get("parse_ok")) and value != 0.0:
        raise AnalysisError("parse-failed output cannot have score 1")
    correct = record.get("correct")
    if correct is not None and bool(correct) != bool(value):
        raise AnalysisError("correct and score fields disagree")
    return value


def _validate_and_index(
    records: Iterable[Mapping[str, Any]],
) -> dict[str, dict[tuple[str, str], dict[str, Mapping[str, Any]]]]:
    """Build ``model -> (incident, query) -> arm -> record`` with parity checks."""

    indexed: dict[str, dict[tuple[str, str], dict[str, Mapping[str, Any]]]] = (
        defaultdict(lambda: defaultdict(dict))
    )
    for record in records:
        model = _required_string(record, "model")
        incident = _required_string(record, "opaque_incident_id")
        query = _required_string(record, "query_id")
        arm = _required_string(record, "arm")
        if arm not in EXPECTED_ARMS:
            raise AnalysisError(f"unexpected RQ1 VisOps arm {arm!r}")
        status = _required_string(record, "status")
        if status not in {"completed", "infrastructure_error"}:
            raise AnalysisError(f"unknown call status {status!r}")
        if status == "completed":
            _validated_score(record)
        key = (incident, query)
        if arm in indexed[model][key]:
            raise AnalysisError(f"duplicate call for {(model, incident, query, arm)}")
        indexed[model][key][arm] = record

    if not indexed:
        raise AnalysisError("no call records supplied")

    required = set(EXPECTED_ARMS)
    for model, units in indexed.items():
        for (incident, query), arms in units.items():
            if set(arms) != required:
                missing = sorted(required - set(arms))
                extra = sorted(set(arms) - required)
                raise AnalysisError(
                    f"unpaired call set for {(model, incident, query)}: "
                    f"missing={missing} extra={extra}"
                )
            # The question and fact inventory must be identical across arms.
            for field in ("query_hash", "fact_inventory_hash"):
                values = {arms[arm].get(field) for arm in EXPECTED_ARMS}
                if None in values or len(values) != 1:
                    raise AnalysisError(
                        f"cross-arm {field} mismatch for {(model, incident, query)}"
                    )
            families = {_required_string(arms[arm], "family") for arm in EXPECTED_ARMS}
            operations = {
                _required_string(arms[arm], "operation") for arm in EXPECTED_ARMS
            }
            if len(families) != 1 or len(operations) != 1:
                raise AnalysisError(
                    f"cross-arm operation metadata mismatch for {(model, incident, query)}"
                )
            for field in ("analysis_dataset", "analysis_leakage_group_id"):
                values = {
                    _optional_analysis_metadata(arms[arm], field)
                    for arm in EXPECTED_ARMS
                }
                if len(values) != 1:
                    raise AnalysisError(
                        f"cross-arm {field} mismatch for {(model, incident, query)}"
                    )

        # Dataset and leakage-group metadata describe incidents, not queries.
        # If present, they must remain stable across every query for that case.
        for field in ("analysis_dataset", "analysis_leakage_group_id"):
            by_incident: dict[str, set[str | None]] = defaultdict(set)
            for (incident, _query), arms in units.items():
                by_incident[incident].add(_optional_analysis_metadata(arms["T"], field))
            unstable = sorted(
                incident for incident, values in by_incident.items() if len(values) != 1
            )
            if unstable:
                raise AnalysisError(
                    f"{field} changes across queries for model {model}: {unstable}"
                )
        datasets = [
            _optional_analysis_metadata(arms["T"], "analysis_dataset")
            for arms in units.values()
        ]
        if any(value is not None for value in datasets) and any(
            value is None for value in datasets
        ):
            raise AnalysisError(
                f"analysis_dataset is only partially recorded for model {model}"
            )
    return indexed


def _accuracy(values: Sequence[float]) -> float:
    if not values:
        raise AnalysisError("cannot compute accuracy on an empty analysis set")
    return sum(values) / len(values)


def _cohen_dz(differences: Sequence[float]) -> dict[str, Any]:
    if len(differences) < 2:
        return {"cohen_dz": None, "cohen_dz_status": "undefined_n_lt_2"}
    mean = statistics.fmean(differences)
    standard_deviation = statistics.stdev(differences)
    if standard_deviation == 0.0:
        if mean == 0.0:
            return {"cohen_dz": 0.0, "cohen_dz_status": "all_differences_zero"}
        return {"cohen_dz": None, "cohen_dz_status": "undefined_zero_sd"}
    return {"cohen_dz": mean / standard_deviation, "cohen_dz_status": "computed"}


def _wilcoxon_pratt(differences: Sequence[float]) -> dict[str, Any]:
    if not differences:
        raise AnalysisError("cannot run paired test on an empty analysis set")
    if all(value == 0.0 for value in differences):
        return {
            "available": True,
            "zero_method": "pratt",
            "alternative": "two-sided",
            "statistic": 0.0,
            "p_value": 1.0,
            "status": "all_differences_zero",
        }
    try:
        from scipy.stats import wilcoxon
    except ImportError:
        return {
            "available": False,
            "zero_method": "pratt",
            "alternative": "two-sided",
            "statistic": None,
            "p_value": None,
            "status": "scipy_unavailable",
        }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = wilcoxon(
            differences,
            zero_method="pratt",
            alternative="two-sided",
            method="auto",
        )
    return {
        "available": True,
        "zero_method": "pratt",
        "alternative": "two-sided",
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "status": "computed",
    }


def _query_paired_comparison(
    lhs: Sequence[float], rhs: Sequence[float], *, lhs_arm: str, rhs_arm: str
) -> dict[str, Any]:
    if len(lhs) != len(rhs) or not lhs:
        raise AnalysisError("paired comparison received unequal or empty vectors")
    repairs = sum(left == 1.0 and right == 0.0 for left, right in zip(lhs, rhs))
    breaks = sum(left == 0.0 and right == 1.0 for left, right in zip(lhs, rhs))
    ties_both_correct = sum(
        left == 1.0 and right == 1.0 for left, right in zip(lhs, rhs)
    )
    ties_both_incorrect = sum(
        left == 0.0 and right == 0.0 for left, right in zip(lhs, rhs)
    )
    count = len(lhs)
    differences = [left - right for left, right in zip(lhs, rhs)]
    report = {
        "lhs_arm": lhs_arm,
        "rhs_arm": rhs_arm,
        "paired_queries": count,
        "lhs_accuracy": _accuracy(lhs),
        "rhs_accuracy": _accuracy(rhs),
        "delta_accuracy": statistics.fmean(differences),
        "repairs": repairs,
        "breaks": breaks,
        "ties": ties_both_correct + ties_both_incorrect,
        "ties_both_correct": ties_both_correct,
        "ties_both_incorrect": ties_both_incorrect,
        "repair_rate": repairs / count,
        "break_rate": breaks / count,
        "net_correction_count": repairs - breaks,
        "net_correction_rate": (repairs - breaks) / count,
        "analysis_role": "descriptive_query_level",
        "inferential_statistics_reported": False,
    }
    return report


def _case_paired_comparison(
    lhs: Sequence[float],
    rhs: Sequence[float],
    *,
    lhs_arm: str,
    rhs_arm: str,
    include_inference: bool,
) -> dict[str, Any]:
    if len(lhs) != len(rhs) or not lhs:
        raise AnalysisError("paired comparison received unequal or empty case vectors")
    count = len(lhs)
    differences = [left - right for left, right in zip(lhs, rhs)]
    improved = sum(value > 0.0 for value in differences)
    degraded = sum(value < 0.0 for value in differences)
    tied = sum(value == 0.0 for value in differences)
    report: dict[str, Any] = {
        "lhs_arm": lhs_arm,
        "rhs_arm": rhs_arm,
        "paired_cases": count,
        "lhs_case_macro_accuracy": _accuracy(lhs),
        "rhs_case_macro_accuracy": _accuracy(rhs),
        "delta_case_macro_accuracy": statistics.fmean(differences),
        "improved_cases": improved,
        "degraded_cases": degraded,
        "tied_cases": tied,
        "improve_rate": improved / count,
        "degrade_rate": degraded / count,
        "net_improved_case_count": improved - degraded,
        "inferential_statistics_reported": include_inference,
    }
    if include_inference:
        report["wilcoxon_signed_rank"] = _wilcoxon_pratt(differences)
        report.update(_cohen_dz(differences))
    return report


def _arm_report(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    scores = [_validated_score(record) for record in records]
    parsed = sum(bool(record.get("parse_ok")) for record in records)

    def mean_metric(field: str) -> dict[str, Any]:
        values = [
            float(record[field])
            for record in records
            if isinstance(record.get(field), (int, float))
            and not isinstance(record.get(field), bool)
            and math.isfinite(float(record[field]))
        ]
        return {
            "mean": statistics.fmean(values) if values else None,
            "observed": len(values),
            "missing": len(records) - len(values),
        }

    return {
        "queries": len(scores),
        "accuracy": _accuracy(scores),
        "parse_rate": parsed / len(records),
        "parse_failure_count": len(records) - parsed,
        "truncation_count": sum(bool(record.get("truncated")) for record in records),
        "invalid_model_output_count": sum(
            not bool(record.get("parse_ok")) for record in records
        ),
        "efficiency": {
            field: mean_metric(field)
            for field in (
                "input_tokens",
                "output_tokens",
                "total_tokens",
                "wall_time_s",
                "gpu_active_time_s",
            )
        },
    }


def _query_scope_report(
    units: Mapping[tuple[str, str], Mapping[str, Mapping[str, Any]]],
    ordered_keys: Sequence[tuple[str, str]],
) -> dict[str, Any]:
    records_by_arm = {
        arm: [units[key][arm] for key in ordered_keys] for arm in EXPECTED_ARMS
    }
    scores_by_arm = {
        arm: [_validated_score(record) for record in records_by_arm[arm]]
        for arm in EXPECTED_ARMS
    }
    return {
        "analysis_role": "descriptive_only",
        "unit": "query",
        "arms": {arm: _arm_report(records_by_arm[arm]) for arm in EXPECTED_ARMS},
        "comparisons": {
            f"{lhs}-{rhs}": _query_paired_comparison(
                scores_by_arm[lhs],
                scores_by_arm[rhs],
                lhs_arm=lhs,
                rhs_arm=rhs,
            )
            for lhs, rhs in COMPARISONS
        },
    }


def _case_score_vectors(
    units: Mapping[tuple[str, str], Mapping[str, Mapping[str, Any]]],
    ordered_keys: Sequence[tuple[str, str]],
) -> tuple[list[str], dict[str, list[float]], dict[str, int]]:
    by_case: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {arm: [] for arm in EXPECTED_ARMS}
    )
    for key in ordered_keys:
        incident, _query = key
        for arm in EXPECTED_ARMS:
            by_case[incident][arm].append(_validated_score(units[key][arm]))
    case_ids = sorted(by_case)
    scores_by_arm = {
        arm: [_accuracy(by_case[incident][arm]) for incident in case_ids]
        for arm in EXPECTED_ARMS
    }
    query_counts = {incident: len(by_case[incident]["T"]) for incident in case_ids}
    return case_ids, scores_by_arm, query_counts


def _case_scope_report(
    units: Mapping[tuple[str, str], Mapping[str, Mapping[str, Any]]],
    ordered_keys: Sequence[tuple[str, str]],
    *,
    analysis_role: str,
    include_inference: bool,
) -> dict[str, Any]:
    case_ids, scores_by_arm, query_counts = _case_score_vectors(units, ordered_keys)
    return {
        "analysis_role": analysis_role,
        "unit": "opaque_incident",
        "cases": len(case_ids),
        "queries": len(ordered_keys),
        "queries_per_case": {
            "minimum": min(query_counts.values()),
            "maximum": max(query_counts.values()),
            "mean": statistics.fmean(query_counts.values()),
        },
        "arms": {
            arm: {
                "cases": len(case_ids),
                "case_macro_accuracy": _accuracy(scores_by_arm[arm]),
            }
            for arm in EXPECTED_ARMS
        },
        "comparisons": {
            f"{lhs}-{rhs}": _case_paired_comparison(
                scores_by_arm[lhs],
                scores_by_arm[rhs],
                lhs_arm=lhs,
                rhs_arm=rhs,
                include_inference=include_inference,
            )
            for lhs, rhs in COMPARISONS
        },
    }


def _leakage_group_counts(
    units: Mapping[tuple[str, str], Mapping[str, Mapping[str, Any]]],
    ordered_keys: Sequence[tuple[str, str]],
) -> dict[str, int] | None:
    case_groups: dict[str, str | None] = {}
    for key in ordered_keys:
        incident, _query = key
        case_groups[incident] = _optional_analysis_metadata(
            units[key]["T"], "analysis_leakage_group_id"
        )
    observed = [value for value in case_groups.values() if value is not None]
    if not observed:
        return None
    counts: dict[str, int] = defaultdict(int)
    for value in observed:
        counts[value] += 1
    return dict(sorted(counts.items()))


def _analyze_model(
    model: str,
    units: Mapping[tuple[str, str], Mapping[str, Mapping[str, Any]]],
    *,
    maximum_exclusion_fraction: float,
    minimum_parse_rate: float,
) -> dict[str, Any]:
    requested_incidents = sorted({incident for incident, _query in units})
    infrastructure_incidents = sorted(
        {
            incident
            for (incident, _query), arms in units.items()
            if any(
                record.get("status") == "infrastructure_error"
                for record in arms.values()
            )
        }
    )
    fraction = len(infrastructure_incidents) / len(requested_incidents)
    if fraction > maximum_exclusion_fraction:
        raise AnalysisError(
            f"model {model} infrastructure exclusion fraction {fraction:.6f} exceeds "
            f"registered maximum {maximum_exclusion_fraction:.6f}"
        )
    excluded = set(infrastructure_incidents)
    eligible = {key: arms for key, arms in units.items() if key[0] not in excluded}
    if not eligible:
        raise AnalysisError(
            f"model {model} has no paired queries after infrastructure exclusion"
        )

    ordered_keys = sorted(eligible)
    query_level = _query_scope_report(eligible, ordered_keys)
    primary_case_level = _case_scope_report(
        eligible,
        ordered_keys,
        analysis_role="primary_inferential",
        include_inference=True,
    )
    families = sorted(
        {_required_string(eligible[key]["T"], "family") for key in ordered_keys}
    )
    per_family: dict[str, Any] = {}
    for family in families:
        family_keys = [
            key
            for key in ordered_keys
            if _required_string(eligible[key]["T"], "family") == family
        ]
        per_family[family] = {
            "case_level": _case_scope_report(
                eligible,
                family_keys,
                analysis_role="stratified_case_level",
                include_inference=True,
            ),
            "query_level_descriptive": _query_scope_report(eligible, family_keys),
        }

    dataset_values = {
        _optional_analysis_metadata(eligible[key]["T"], "analysis_dataset")
        for key in ordered_keys
    }
    per_dataset: dict[str, Any] | None = None
    if dataset_values != {None}:
        per_dataset = {}
        for dataset in sorted(value for value in dataset_values if value is not None):
            dataset_keys = [
                key
                for key in ordered_keys
                if _optional_analysis_metadata(eligible[key]["T"], "analysis_dataset")
                == dataset
            ]
            dataset_report = {
                "analysis_role": "descriptive_dataset_breakdown",
                "case_level": _case_scope_report(
                    eligible,
                    dataset_keys,
                    analysis_role="descriptive_dataset_case_level",
                    include_inference=False,
                ),
                "query_level_descriptive": _query_scope_report(eligible, dataset_keys),
            }
            group_counts = _leakage_group_counts(eligible, dataset_keys)
            if group_counts is not None:
                dataset_report["analysis_leakage_group_case_counts"] = group_counts
            per_dataset[dataset] = dataset_report

    arm_reports = query_level["arms"]
    parse_failures = {
        arm: report["parse_rate"]
        for arm, report in arm_reports.items()
        if report["parse_rate"] < minimum_parse_rate
    }
    return {
        "status": "valid" if not parse_failures else "incomplete_parse_rate",
        "confirmatory_claim_allowed": not parse_failures,
        "minimum_parse_rate": minimum_parse_rate,
        "parse_rate_failures": parse_failures,
        "model": model,
        "call_integrity_pairing_key": ["model", "opaque_incident_id", "query_id"],
        "primary_inferential_unit": "opaque_incident_id",
        "requested_incidents": len(requested_incidents),
        "requested_queries": len(units),
        "included_incidents": len(requested_incidents) - len(infrastructure_incidents),
        "included_queries": len(eligible),
        "infrastructure_exclusion": {
            "policy": "whole_incident_across_T_V_H",
            "incident_ids": infrastructure_incidents,
            "count": len(infrastructure_incidents),
            "fraction": fraction,
            "maximum_fraction": maximum_exclusion_fraction,
        },
        "primary_case_level": primary_case_level,
        "query_level_descriptive": query_level,
        "per_family": per_family,
        "per_dataset": per_dataset,
    }


def analyze_records(
    records: Iterable[Mapping[str, Any]],
    *,
    maximum_exclusion_fraction: float = DEFAULT_MAX_INFRASTRUCTURE_EXCLUSION_FRACTION,
    minimum_parse_rate: float = DEFAULT_MINIMUM_PARSE_RATE,
) -> dict[str, Any]:
    """Analyze fully paired calls, failing closed on integrity violations."""

    if not 0.0 <= maximum_exclusion_fraction <= 1.0:
        raise AnalysisError("maximum exclusion fraction must lie in [0, 1]")
    if not 0.0 <= minimum_parse_rate <= 1.0:
        raise AnalysisError("minimum parse rate must lie in [0, 1]")
    indexed = _validate_and_index(records)
    return {
        "schema_version": "RQ1VisOpsPairedAnalysisV2",
        "status": "valid",
        "expected_arms": list(EXPECTED_ARMS),
        "primary_inferential_unit": "opaque_incident_id",
        "query_level_statistics_role": "descriptive_only",
        "infrastructure_exclusion_maximum_fraction": maximum_exclusion_fraction,
        "minimum_parse_rate": minimum_parse_rate,
        "parse_truncation_and_invalid_output_policy": "retained_as_model_outcomes",
        "confidence_intervals_reported": False,
        "models": {
            model: _analyze_model(
                model,
                units,
                maximum_exclusion_fraction=maximum_exclusion_fraction,
                minimum_parse_rate=minimum_parse_rate,
            )
            for model, units in sorted(indexed.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        type=Path,
        nargs="+",
        help="cell directory, calls directory, or individual call JSON",
    )
    parser.add_argument("--output", type=Path, help="optional analysis JSON output")
    parser.add_argument(
        "--private-roster",
        type=Path,
        help=(
            "optional frozen RQ1PrivateRosterV1 used only by this offline evaluator "
            "to attach dataset and leakage-group strata"
        ),
    )
    parser.add_argument(
        "--maximum-infrastructure-exclusion-fraction",
        type=float,
        default=DEFAULT_MAX_INFRASTRUCTURE_EXCLUSION_FRACTION,
    )
    parser.add_argument(
        "--minimum-parse-rate",
        type=float,
        default=DEFAULT_MINIMUM_PARSE_RATE,
    )
    args = parser.parse_args()
    records = load_call_records(args.inputs)
    private_roster_assignment_hash: str | None = None
    if args.private_roster is not None:
        private_roster = _load_json(args.private_roster.resolve())
        records = enrich_records_from_private_roster(records, private_roster)
        private_roster_assignment_hash = str(private_roster["assignment_hash"])
    report = analyze_records(
        records,
        maximum_exclusion_fraction=args.maximum_infrastructure_exclusion_fraction,
        minimum_parse_rate=args.minimum_parse_rate,
    )
    report["evaluator_only_metadata_enrichment"] = {
        "applied": args.private_roster is not None,
        "roster_assignment_hash": private_roster_assignment_hash,
        "private_case_ids_in_report": False,
    }
    serialized = json.dumps(
        report,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    )
    if args.output:
        output = args.output.resolve()
        results_root = (RQ_ROOT / "results").resolve()
        if results_root not in output.parents:
            raise AnalysisError("analysis output must be below RQs/RQ1/results/")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

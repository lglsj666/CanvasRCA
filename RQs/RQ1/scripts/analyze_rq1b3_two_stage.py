#!/usr/bin/env python3
"""Analyze the registered RQ1b3 two-stage development or gate cell."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from rq1lib.contracts import ContractError, canonical_json, stable_hash
from rq1lib.scoring import normalize_panel_onset_ledger
from rq1lib.settings import load_yaml_config
from run_rq1_visops import (
    _load_json,
    _prepared_calls,
    _prepared_roots_from_index,
)
from run_rq1b3_stage2 import _load_oracle

ROOT = Path(__file__).resolve().parents[3]
RQ_ROOT = ROOT / "RQs/RQ1"


def _read_calls(root: Path) -> list[dict[str, Any]]:
    if not (root / "summary.json").is_file():
        raise ContractError(f"incomplete run root: {root}")
    calls = [_load_json(path) for path in sorted((root / "calls").glob("*.json"))]
    if not calls:
        raise ContractError(f"run root contains no calls: {root}")
    return calls


def _index(
    records: Sequence[Mapping[str, Any]], *, arms: set[str]
) -> dict[tuple[str, str], Mapping[str, Any]]:
    out: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in records:
        arm = str(row.get("arm"))
        if arm not in arms:
            continue
        key = (str(row["opaque_incident_id"]), arm)
        if key in out:
            raise ContractError(f"duplicate result unit {key}")
        out[key] = row
    return out


def _valid_ledger(record: Mapping[str, Any]) -> dict[str, Any] | None:
    if record.get("status") != "completed" or record.get("parse_ok") is not True:
        return None
    try:
        return {"panels": normalize_panel_onset_ledger(record["predicted_answer"])}
    except ContractError:
        return None


def _ledger_metrics(
    predicted: Mapping[str, Any] | None, oracle: Mapping[str, Any]
) -> dict[str, Any]:
    gold = {row["panel_id"]: row for row in oracle["panels"]}
    observed = (
        {row["panel_id"]: row for row in predicted["panels"]}
        if predicted is not None
        else {}
    )
    exact = 0
    full_exact = 0
    false_onset = 0
    missed_onset = 0
    off_by_one = 0
    sign_errors = 0
    support_errors = 0
    omitted = 0
    raw_errors: list[float] = []
    panel_errors: dict[str, float] = {}
    for panel, expected in gold.items():
        actual = observed.get(panel)
        if actual is None:
            omitted += 1
            error = 16.0
        else:
            expected_onset = expected["onset"]
            actual_onset = actual["onset"]
            if expected_onset == actual_onset:
                exact += 1
                error = 0.0
            elif expected_onset is None and actual_onset is not None:
                false_onset += 1
                error = 16.0
            elif expected_onset is not None and actual_onset is None:
                missed_onset += 1
                error = 16.0
            else:
                error = abs(float(actual_onset) - float(expected_onset))
                if error == 1.0:
                    off_by_one += 1
            if expected.get("sign") != actual.get("sign"):
                sign_errors += 1
            if expected.get("support_bins") != actual.get("support_bins"):
                support_errors += 1
            if expected == actual:
                full_exact += 1
        raw_errors.append(error)
        panel_errors[panel] = error / 16.0
    return {
        "panel_onset_accuracy": exact / len(gold),
        "panel_full_entry_accuracy": full_exact / len(gold),
        "exact_ledger": full_exact == len(gold),
        "false_onset_rate": false_onset / len(gold),
        "missed_onset_rate": missed_onset / len(gold),
        "off_by_one_rate": off_by_one / len(gold),
        "sign_error_rate": sign_errors / len(gold),
        "support_error_rate": support_errors / len(gold),
        "omission_rate": omitted / len(gold),
        "raw_onset_error": statistics.fmean(raw_errors),
        "normalized_onset_error": statistics.fmean(raw_errors) / 16.0,
        "panel_errors": panel_errors,
    }


def _mean(values: Sequence[float]) -> float:
    return statistics.fmean(values) if values else float("nan")


def _oracle_stage2_accuracy_minimum(config: Mapping[str, Any]) -> float:
    """Read the frozen protocol key without silently accepting a misspelling."""

    two_stage = config.get("two_stage")
    if not isinstance(two_stage, Mapping):
        raise ContractError("RQ1b3 config lacks the two_stage contract")
    value = two_stage.get("oracle_stage_2_accuracy_minimum")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ContractError(
            "RQ1b3 config lacks numeric oracle_stage_2_accuracy_minimum"
        )
    return float(value)


def _paired_test(left: Sequence[float], right: Sequence[float]) -> dict[str, Any]:
    if len(left) != len(right) or not left:
        raise ContractError("paired test requires equal non-empty vectors")
    differences = [a - b for a, b in zip(left, right)]
    mean = statistics.fmean(differences)
    sd = statistics.stdev(differences) if len(differences) > 1 else 0.0
    dz = mean / sd if sd else (0.0 if mean == 0 else math.copysign(math.inf, mean))
    if all(value == 0 for value in differences):
        p_value = 1.0
    else:
        from scipy.stats import wilcoxon

        p_value = float(
            wilcoxon(
                differences,
                zero_method="pratt",
                alternative="two-sided",
                method="auto",
            ).pvalue
        )
    return {
        "n": len(differences),
        "delta": mean,
        "pratt_wilcoxon_two_sided_p": p_value,
        "paired_cohens_dz": dz,
        "improve": sum(value > 0 for value in differences),
        "degrade": sum(value < 0 for value in differences),
        "tie": sum(value == 0 for value in differences),
    }


def _integrity(
    records: Sequence[Mapping[str, Any]], *, incident_total: int
) -> dict[str, Any]:
    complete = [row for row in records if row.get("status") == "completed"]
    infra_incidents = {
        str(row["opaque_incident_id"])
        for row in records
        if row.get("status") == "infrastructure_error"
    }
    return {
        "calls": len(records),
        "completed": len(complete),
        "infrastructure_failures": len(records) - len(complete),
        "paired_incident_exclusion_fraction": len(infra_incidents) / incident_total,
        "parse_rate": (
            sum(bool(row.get("parse_ok")) for row in complete) / len(complete)
            if complete
            else 0.0
        ),
        "truncations": sum(bool(row.get("truncated")) for row in complete),
    }


def _position_slope(
    metrics: Mapping[tuple[str, str], Mapping[str, Any]],
    order: Mapping[str, list[str]],
    arm: str,
) -> float:
    positions: list[float] = []
    errors: list[float] = []
    for (incident, record_arm), row in metrics.items():
        if record_arm != arm:
            continue
        for position, panel in enumerate(order[incident]):
            positions.append(float(position))
            errors.append(float(row["panel_errors"][panel]))
    if not positions or statistics.pvariance(positions) == 0:
        return float("nan")
    x_mean = statistics.fmean(positions)
    y_mean = statistics.fmean(errors)
    covariance = statistics.fmean(
        (x - x_mean) * (y - y_mean) for x, y in zip(positions, errors)
    )
    return covariance / statistics.pvariance(positions)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--private-roster", type=Path, required=True)
    parser.add_argument("--prepared-index", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--main-stage1", type=Path, required=True)
    parser.add_argument("--main-stage2", type=Path, required=True)
    parser.add_argument("--sham-stage1", type=Path, required=True)
    parser.add_argument("--sham-stage2", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    roster = _load_json(args.roster)
    private_roster = _load_json(args.private_roster)
    roots, prepared_index = _prepared_roots_from_index(
        args.prepared_index, config=config, roster=roster
    )
    main_expected = _prepared_calls(roots, "ALL", config=config, condition="main")
    sham_expected = _prepared_calls(roots, "ALL", config=config, condition="row_sham")
    incidents = sorted({str(row["opaque_incident_id"]) for row in main_expected})
    if (
        len(main_expected) != len(incidents) * 3
        or len(sham_expected) != len(incidents) * 2
    ):
        raise ContractError("prepared main/sham call inventory is incomplete")
    datasets = {
        str(row["opaque_incident_id"]): str(row["analysis_dataset"])
        for row in private_roster["cases"]
    }
    if set(datasets) != set(incidents):
        raise ContractError("private roster and prepared incidents differ")

    main_stage1_records = _read_calls(args.main_stage1)
    sham_stage1_records = _read_calls(args.sham_stage1)
    main_stage2_records = _read_calls(args.main_stage2)
    sham_stage2_records = _read_calls(args.sham_stage2)
    main_stage1 = _index(main_stage1_records, arms={"T", "V", "H"})
    sham_stage1 = _index(sham_stage1_records, arms={"V", "H"})
    main_stage2 = _index(main_stage2_records, arms={"T", "V", "H", "O"})
    sham_stage2 = _index(sham_stage2_records, arms={"V", "H"})
    expected_sizes = {
        "main_stage1": (len(main_stage1), len(incidents) * 3),
        "sham_stage1": (len(sham_stage1), len(incidents) * 2),
        "main_stage2": (len(main_stage2), len(incidents) * 4),
        "sham_stage2": (len(sham_stage2), len(incidents) * 2),
    }
    if any(actual != expected for actual, expected in expected_sizes.values()):
        raise ContractError(f"RQ1b3 result-cell sizes differ: {expected_sizes}")

    oracle_by_incident: dict[str, dict[str, Any]] = {}
    for row in main_expected:
        incident = str(row["opaque_incident_id"])
        if incident not in oracle_by_incident:
            oracle_by_incident[incident] = _load_oracle(row)[0]
    main_metrics: dict[tuple[str, str], dict[str, Any]] = {}
    sham_metrics: dict[tuple[str, str], dict[str, Any]] = {}
    for key, record in main_stage1.items():
        main_metrics[key] = _ledger_metrics(
            _valid_ledger(record), oracle_by_incident[key[0]]
        )
    for key, record in sham_stage1.items():
        sham_metrics[key] = _ledger_metrics(
            _valid_ledger(record), oracle_by_incident[key[0]]
        )

    main_efficacy_incidents = [
        incident
        for incident in incidents
        if all(
            main_stage1[(incident, arm)].get("status") == "completed"
            and main_stage2[(incident, arm)].get("status") == "completed"
            for arm in ("T", "V", "H")
        )
    ]
    final_vectors = {
        arm: [
            float(bool(main_stage2[(incident, arm)].get("correct")))
            for incident in main_efficacy_incidents
        ]
        for arm in ("T", "V", "H")
    }
    ledger_vectors = {
        arm: [
            float(main_metrics[(incident, arm)]["panel_onset_accuracy"])
            for incident in main_efficacy_incidents
        ]
        for arm in ("T", "V", "H")
    }
    error_vectors = {
        arm: [
            float(main_metrics[(incident, arm)]["normalized_onset_error"])
            for incident in main_efficacy_incidents
        ]
        for arm in ("T", "V", "H")
    }
    final_h_t = _paired_test(final_vectors["H"], final_vectors["T"])
    ledger_h_t = _paired_test(ledger_vectors["H"], ledger_vectors["T"])
    repairs = sum(
        main_stage2[(incident, "H")].get("correct") is True
        and main_stage2[(incident, "T")].get("correct") is not True
        for incident in main_efficacy_incidents
    )
    breaks = sum(
        main_stage2[(incident, "T")].get("correct") is True
        and main_stage2[(incident, "H")].get("correct") is not True
        for incident in main_efficacy_incidents
    )
    oracle_accuracy = _mean(
        [
            float(bool(main_stage2[(incident, "O")].get("correct")))
            for incident in incidents
        ]
    )

    per_dataset: dict[str, Any] = {}
    for dataset in sorted(set(datasets.values())):
        selected = [
            incident
            for incident in main_efficacy_incidents
            if datasets[incident] == dataset
        ]
        per_dataset[dataset] = {
            "n": len(selected),
            "final_accuracy": {
                arm: _mean(
                    [
                        float(bool(main_stage2[(incident, arm)].get("correct")))
                        for incident in selected
                    ]
                )
                for arm in ("T", "V", "H")
            },
            "ledger_panel_accuracy": {
                arm: _mean(
                    [
                        float(main_metrics[(incident, arm)]["panel_onset_accuracy"])
                        for incident in selected
                    ]
                )
                for arm in ("T", "V", "H")
            },
        }
        per_dataset[dataset]["final_h_minus_t"] = (
            per_dataset[dataset]["final_accuracy"]["H"]
            - per_dataset[dataset]["final_accuracy"]["T"]
        )

    main_order: dict[str, list[str]] = {}
    sham_order: dict[str, list[str]] = {}
    for root in roots:
        manifest = _load_json(root / "manifest.json")
        incident = str(manifest["opaque_incident_id"])
        record = manifest["tasks"][0]
        main_meta = _load_json(root / record["public_files"]["visual_manifest"])
        sham_meta = _load_json(root / record["public_files"]["visual_sham_manifest"])
        main_order[incident] = list(
            main_meta["primitive_manifest"]["series_panel_order"]
        )
        sham_order[incident] = list(
            sham_meta["primitive_manifest"]["series_panel_order"]
        )
    sham_diagnostics: dict[str, Any] = {}
    for arm in ("V", "H"):
        stage1_agreement = []
        final_agreement = []
        main_accuracy = []
        sham_accuracy = []
        main_top = []
        sham_top = []
        for incident in incidents:
            main_ledger = _valid_ledger(main_stage1[(incident, arm)])
            sham_ledger = _valid_ledger(sham_stage1[(incident, arm)])
            stage1_agreement.append(main_ledger == sham_ledger)
            main_answer = main_stage2[(incident, arm)].get("predicted_answer")
            sham_answer = sham_stage2[(incident, arm)].get("predicted_answer")
            final_agreement.append(main_answer == sham_answer)
            main_accuracy.append(bool(main_stage2[(incident, arm)].get("correct")))
            sham_accuracy.append(bool(sham_stage2[(incident, arm)].get("correct")))
            main_top.append(
                isinstance(main_answer, list) and main_order[incident][0] in main_answer
            )
            sham_top.append(
                isinstance(sham_answer, list) and sham_order[incident][0] in sham_answer
            )
        sham_diagnostics[arm] = {
            "stage1_exact_ledger_agreement": _mean(
                [float(value) for value in stage1_agreement]
            ),
            "final_answer_agreement": _mean(
                [float(value) for value in final_agreement]
            ),
            "main_final_accuracy": _mean([float(value) for value in main_accuracy]),
            "sham_final_accuracy": _mean([float(value) for value in sham_accuracy]),
            "sham_minus_main_final_accuracy": _mean(
                [float(value) for value in sham_accuracy]
            )
            - _mean([float(value) for value in main_accuracy]),
            "main_top_row_selection_rate": _mean([float(value) for value in main_top]),
            "sham_top_row_selection_rate": _mean([float(value) for value in sham_top]),
            "main_panel_position_error_slope": _position_slope(
                main_metrics, main_order, arm
            ),
            "sham_panel_position_error_slope": _position_slope(
                sham_metrics, sham_order, arm
            ),
        }

    integrity = {
        "main_stage1": _integrity(main_stage1_records, incident_total=len(incidents)),
        "main_stage2": _integrity(main_stage2_records, incident_total=len(incidents)),
        "sham_stage1": _integrity(sham_stage1_records, incident_total=len(incidents)),
        "sham_stage2": _integrity(sham_stage2_records, incident_total=len(incidents)),
    }
    minimum_parse = float(config["integrity"]["minimum_parse_rate"])
    maximum_exclusion = float(
        config["integrity"][
            "maximum_paired_whole_case_infrastructure_exclusion_fraction"
        ]
    )
    integrity_passed = all(
        cell["parse_rate"] >= minimum_parse
        and cell["paired_incident_exclusion_fraction"] <= maximum_exclusion
        for cell in integrity.values()
    )
    development = config["gates"]["rq1b3_development"]
    gate_checks = {
        "final_h_minus_t_at_least_0.05": final_h_t["delta"] >= 0.05,
        "ledger_h_minus_t_at_least_0.05": ledger_h_t["delta"] >= 0.05,
        "hybrid_repairs_exceed_breaks": repairs > breaks,
        "hybrid_mean_ledger_error_below_text": _mean(error_vectors["H"])
        < _mean(error_vectors["T"]),
        "oracle_stage2_accuracy_at_least_0.95": oracle_accuracy
        >= _oracle_stage2_accuracy_minimum(config),
        "integrity_passed": integrity_passed,
    }
    passed = all(gate_checks.values())
    result = {
        "schema_version": "RQ1B3TwoStageAnalysisV1",
        "status": "valid_passed" if passed else "valid_failed",
        "experiment_id": config["experiment_id"],
        "model": args.model,
        "confirmatory": False,
        "p_value_is_gate": False,
        "n_roster": len(incidents),
        "n_main_paired": len(main_efficacy_incidents),
        "final_accuracy": {arm: _mean(final_vectors[arm]) for arm in ("T", "V", "H")},
        "ledger_panel_accuracy": {
            arm: _mean(ledger_vectors[arm]) for arm in ("T", "V", "H")
        },
        "normalized_ledger_error": {
            arm: _mean(error_vectors[arm]) for arm in ("T", "V", "H")
        },
        "final_hybrid_minus_text": final_h_t,
        "ledger_hybrid_minus_text": ledger_h_t,
        "hybrid_repairs": repairs,
        "hybrid_breaks": breaks,
        "oracle_stage2_accuracy": oracle_accuracy,
        "per_dataset": per_dataset,
        "row_sham_diagnostics": sham_diagnostics,
        "integrity": integrity,
        "gate_checks": gate_checks,
        "gate_status": "passed" if passed else "failed",
        "registered_requirements": list(development["requirements"]),
        "experiment_config_hash": stable_hash(config),
        "roster_contract_hash": stable_hash(roster),
        "roster_assignment_hash": roster["assignment_hash"],
        "prepared_artifact_inventory_hash": prepared_index["artifact_inventory_hash"],
        "confidence_intervals_reported": False,
    }
    result["analysis_contract_sha256"] = stable_hash(result)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(canonical_json(result) + "\n", encoding="utf-8")
    markdown = f"""# RQ1b3 two-stage analysis — {args.model}

- Status: **{result["status"]}**
- Paired incidents: {result["n_main_paired"]} / {result["n_roster"]}
- Final accuracy T/V/H: {result["final_accuracy"]["T"]:.4f} / {result["final_accuracy"]["V"]:.4f} / {result["final_accuracy"]["H"]:.4f}
- Final H−T: {final_h_t["delta"]:+.4f} (diagnostic Pratt-Wilcoxon p={final_h_t["pratt_wilcoxon_two_sided_p"]:.6g}; p is not a development gate)
- Stage-1 panel accuracy T/V/H: {result["ledger_panel_accuracy"]["T"]:.4f} / {result["ledger_panel_accuracy"]["V"]:.4f} / {result["ledger_panel_accuracy"]["H"]:.4f}
- Stage-1 H−T: {ledger_h_t["delta"]:+.4f}
- H repairs / breaks: {repairs} / {breaks}
- Oracle Stage-2 accuracy: {oracle_accuracy:.4f}
- Gate checks: `{json.dumps(gate_checks, sort_keys=True)}`

This exposed-development analysis uses no confidence interval and no p-value
promotion threshold. Passing only authorizes the already-frozen independent
gate; it is not confirmatory evidence.
"""
    args.output_markdown.write_text(markdown, encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

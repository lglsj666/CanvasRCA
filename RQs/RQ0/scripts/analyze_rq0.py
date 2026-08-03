#!/usr/bin/env python3
"""Registered RQ0 analysis: paired MRR, Holm tests and decision rubric."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import stats

from vlmrca.rq0.evidence import atomic_fact_records
from vlmrca.upstream import is_service_level_hit, normalize_service

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_equal_information_equal_compute_v1"
A = "visual_text_topology"
B = "text_only"
C = "flat_structured"


def _episodes(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record.get("record_type") == "episode":
            rows.append(record)
    return rows


def _header(path: Path) -> Dict[str, Any]:
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record.get("record_type") == "header":
            return record
    return {}


def _mean(rows: List[Dict[str, Any]], key: str) -> float:
    return float(np.mean([float(row.get(key, 0.0)) for row in rows])) if rows else 0.0


def _fmt(value: Any, spec: str = ".4f") -> str:
    return format(float(value), spec) if value is not None else "n/a"


def _holm(p_values: List[float]) -> List[float]:
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [1.0] * len(p_values)
    running = 0.0
    m = len(p_values)
    for rank, (index, value) in enumerate(indexed):
        candidate = min(1.0, (m - rank) * value)
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted


def _paired(
    rows: List[Dict[str, Any]], left: str, right: str
) -> Tuple[Dict[str, Any], List[str]]:
    by_key = {
        (row["dataset"], row["case_id"], row["arm"]): row for row in rows
    }
    case_ids = sorted({(row["dataset"], row["case_id"]) for row in rows})
    paired = []
    excluded = []
    for dataset, case_id in case_ids:
        a = by_key.get((dataset, case_id, left))
        b = by_key.get((dataset, case_id, right))
        if not a or not b or a["status"] == "infrastructure_failure" or b["status"] == "infrastructure_failure":
            excluded.append(f"{dataset}:{case_id}")
            continue
        paired.append((a, b))
    xa = np.array([float(a["mrr"]) for a, _b in paired])
    xb = np.array([float(b["mrr"]) for _a, b in paired])
    delta = xa - xb
    if len(delta) >= 5 and not np.allclose(delta, 0):
        statistic, p_value = stats.wilcoxon(xa, xb)
        statistic, p_value = float(statistic), float(p_value)
    else:
        statistic, p_value = None, 1.0
    sd = float(np.std(delta, ddof=1)) if len(delta) > 1 else 0.0
    by_dataset: Dict[str, List[float]] = defaultdict(list)
    for (a, _b), value in zip(paired, delta):
        by_dataset[a["dataset"]].append(float(value))
    result = {
        "left": left,
        "right": right,
        "n_paired": len(paired),
        "n_excluded_infrastructure": len(excluded),
        "mrr_left": float(xa.mean()) if len(xa) else None,
        "mrr_right": float(xb.mean()) if len(xb) else None,
        "delta_mrr": float(delta.mean()) if len(delta) else None,
        "macro_dataset_delta_mrr": (
            float(np.mean([np.mean(value) for value in by_dataset.values()]))
            if by_dataset
            else None
        ),
        "paired_sd": sd,
        "cohens_dz": float(delta.mean() / sd) if sd > 0 else 0.0,
        "wilcoxon_stat": statistic,
        "p_value": p_value,
        "delta_by_dataset": {
            key: float(np.mean(value)) for key, value in sorted(by_dataset.items())
        },
    }
    return result, excluded


def _effect_modifiers(
    rows: List[Dict[str, Any]], left: str, right: str
) -> Dict[str, Any]:
    by_key = {
        (row["dataset"], row["case_id"], row["arm"]): row for row in rows
    }
    records = []
    qualification = ROOT / "RQs/RQ0/results" / EXPERIMENT / "qualification_formal"
    for dataset, case_id in sorted(
        {(row["dataset"], row["case_id"]) for row in rows}
    ):
        a = by_key.get((dataset, case_id, left))
        b = by_key.get((dataset, case_id, right))
        if (
            not a
            or not b
            or a["status"] == "infrastructure_failure"
            or b["status"] == "infrastructure_failure"
        ):
            continue
        ceb_path = (
            qualification / "evidence" / f"{a['opaque_incident_id']}.ceb.json"
        )
        if not ceb_path.is_file():
            continue
        ceb = json.loads(ceb_path.read_text())
        evidence_services = {
            str(series["service"]) for series in ceb["metric_series"]
        }
        evidence_services.update(
            str(item["service"]) for item in ceb["propagation"]["services"]
        )
        evidence_services.update(
            str(item.get("service"))
            for item in ceb["log_summary"]["entries"]
            if item.get("service")
        )
        evidence_services.update(
            str(item.get("service"))
            for item in ceb["trace_summary"]["entries"]
            if item.get("service")
        )
        gt = normalize_service(a["ground_truth"])
        root_covered = any(
            is_service_level_hit(normalize_service(service), gt)
            or is_service_level_hit(gt, normalize_service(service))
            for service in evidence_services
        )
        n_prop = len(ceb["propagation"]["services"])
        edge_count = len(ceb["propagation"]["directed_call_edges"])
        omitted_edge_count = int(ceb["propagation"].get("omitted_edges") or 0)
        total_bins = sum(len(series["values"]) for series in ceb["metric_series"])
        missing_bins = sum(
            sum(value is None for value in series["values"])
            for series in ceb["metric_series"]
        )
        root = str(a["ground_truth"])
        root_level = (
            "node"
            if root.startswith(("node-", "worker"))
            else "pod"
            if root.rsplit("-", 1)[-1].isdigit()
            else "service"
        )
        records.append(
            {
                "delta": float(a["mrr"]) - float(b["mrr"]),
                "dataset": a["dataset"],
                "fault_type": a["fault_type"],
                "root_cause_level": root_level,
                "root_evidence_coverage": str(bool(root_covered)).lower(),
                "trace_presence": str(not ceb["missingness"]["traces_missing"]).lower(),
                "candidate_count": len(ceb["candidates"]),
                "topology_edge_coverage": (
                    edge_count / (edge_count + omitted_edge_count)
                    if edge_count + omitted_edge_count
                    else (1.0 if n_prop <= 1 else 0.0)
                ),
                "visual_density_fact_count": len(atomic_fact_records(ceb)),
                "missing_rate": missing_bins / total_bins if total_bins else 1.0,
            }
        )
    categorical = {}
    for field in (
        "dataset",
        "fault_type",
        "root_cause_level",
        "root_evidence_coverage",
        "trace_presence",
    ):
        groups: Dict[str, List[float]] = defaultdict(list)
        for record in records:
            groups[str(record[field])].append(record["delta"])
        categorical[field] = {
            key: {"n": len(values), "mean_delta_mrr": float(np.mean(values))}
            for key, values in sorted(groups.items())
        }
    continuous = {}
    for field in (
        "candidate_count",
        "topology_edge_coverage",
        "visual_density_fact_count",
        "missing_rate",
    ):
        x = np.array([float(record[field]) for record in records])
        y = np.array([record["delta"] for record in records])
        if len(x) >= 3 and len(set(x)) > 1:
            rho, p_value = stats.spearmanr(x, y)
            rho = float(rho) if math.isfinite(float(rho)) else None
            p_value = float(p_value) if math.isfinite(float(p_value)) else None
        else:
            rho = p_value = None
        continuous[field] = {
            "n": len(x),
            "spearman_rho": rho,
            "p_value_descriptive_unadjusted": p_value,
        }
    return {
        "n": len(records),
        "categorical": categorical,
        "continuous": continuous,
    }


def _model_summary(model: str, trajectory: Path) -> Dict[str, Any]:
    rows = _episodes(trajectory)
    header = _header(trajectory)
    expected = 720 * 3
    by_arm = {arm: [row for row in rows if row["arm"] == arm] for arm in (A, B, C)}
    arm_summary = {}
    for arm, arm_rows in by_arm.items():
        dataset_mrr = {
            dataset: _mean([row for row in arm_rows if row["dataset"] == dataset], "mrr")
            for dataset in sorted({row["dataset"] for row in arm_rows})
        }
        arm_summary[arm] = {
            "n": len(arm_rows),
            "mrr": _mean(arm_rows, "mrr"),
            "macro_dataset_mrr": float(np.mean(list(dataset_mrr.values())))
            if dataset_mrr
            else None,
            "mrr_by_dataset": dataset_mrr,
            "ac1": _mean(arm_rows, "ac1"),
            "ac3": _mean(arm_rows, "ac3"),
            "ac5": _mean(arm_rows, "ac5"),
            "avg3": _mean(arm_rows, "avg3"),
            "avg5": _mean(arm_rows, "avg5"),
            "parse_rate": float(
                np.mean([bool(row.get("parse_ok")) for row in arm_rows])
            )
            if arm_rows
            else 0.0,
            "truncation_rate": float(
                np.mean([bool(row.get("truncated")) for row in arm_rows])
            )
            if arm_rows
            else 0.0,
            "infrastructure_error_rate": float(
                np.mean(
                    [row.get("status") == "infrastructure_failure" for row in arm_rows]
                )
            )
            if arm_rows
            else 0.0,
            "avg_input_tokens": _mean(arm_rows, "input_tokens"),
            "avg_text_input_tokens": _mean(
                [row for row in arm_rows if row.get("text_input_tokens") is not None],
                "text_input_tokens",
            ),
            "avg_image_input_tokens": _mean(
                [row for row in arm_rows if row.get("image_input_tokens") is not None],
                "image_input_tokens",
            ),
            "avg_output_tokens": _mean(arm_rows, "output_tokens"),
            "avg_total_tokens": _mean(arm_rows, "total_tokens"),
            "avg_wall_time_s": _mean(arm_rows, "wall_time_s"),
            "avg_gpu_active_time_s_sampled": _mean(
                arm_rows, "gpu_active_time_s_sampled"
            ),
            "avg_peak_gpu_memory_mib_sampled": _mean(
                [
                    row
                    for row in arm_rows
                    if row.get("peak_gpu_memory_mib_sampled") is not None
                ],
                "peak_gpu_memory_mib_sampled",
            ),
        }

    ab, excluded_ab = _paired(rows, A, B)
    ac, excluded_ac = _paired(rows, A, C)
    adjusted = _holm([ab["p_value"], ac["p_value"]])
    ab["holm_adjusted_p"] = adjusted[0]
    ac["holm_adjusted_p"] = adjusted[1]
    effect_modifiers = {
        "A_minus_B": _effect_modifiers(rows, A, B),
        "A_minus_C": _effect_modifiers(rows, A, C),
    }

    # Agreement/discordance are descriptive and use cases with all three
    # infrastructure-valid arms.
    table = defaultdict(dict)
    for row in rows:
        table[(row["dataset"], row["case_id"])][row["arm"]] = row
    complete = [
        values
        for values in table.values()
        if all(
            arm in values and values[arm]["status"] != "infrastructure_failure"
            for arm in (A, B, C)
        )
    ]
    agreement = {
        "n_complete_triplets": len(complete),
        "top1_agreement_a_b": float(
            np.mean(
                [
                    (x[A].get("predicted") or [None])[0]
                    == (x[B].get("predicted") or [None])[0]
                    for x in complete
                ]
            )
        )
        if complete
        else None,
        "top1_agreement_a_c": float(
            np.mean(
                [
                    (x[A].get("predicted") or [None])[0]
                    == (x[C].get("predicted") or [None])[0]
                    for x in complete
                ]
            )
        )
        if complete
        else None,
        "mean_top5_jaccard_a_b": float(
            np.mean(
                [
                    len(set(x[A].get("predicted") or []) & set(x[B].get("predicted") or []))
                    / max(
                        1,
                        len(
                            set(x[A].get("predicted") or [])
                            | set(x[B].get("predicted") or [])
                        ),
                    )
                    for x in complete
                ]
            )
        )
        if complete
        else None,
        "mean_top5_jaccard_a_c": float(
            np.mean(
                [
                    len(set(x[A].get("predicted") or []) & set(x[C].get("predicted") or []))
                    / max(
                        1,
                        len(
                            set(x[A].get("predicted") or [])
                            | set(x[C].get("predicted") or [])
                        ),
                    )
                    for x in complete
                ]
            )
        )
        if complete
        else None,
        "a_correct_b_wrong": sum(x[A]["ac1"] > x[B]["ac1"] for x in complete),
        "a_wrong_b_correct": sum(x[A]["ac1"] < x[B]["ac1"] for x in complete),
        "a_correct_c_wrong": sum(x[A]["ac1"] > x[C]["ac1"] for x in complete),
        "a_wrong_c_correct": sum(x[A]["ac1"] < x[C]["ac1"] for x in complete),
    }

    protocol_failures: List[str] = []
    roster = json.loads(
        (ROOT / "RQs" / "RQ0" / "configs" / "partition_roster.json").read_text()
    )
    expected_cases = {
        (dataset, item["case_id"])
        for dataset, items in roster["partitions"]["formal"].items()
        for item in items
    }
    observed_cases = {(row.get("dataset"), row.get("case_id")) for row in rows}
    observed_keys = [
        (row.get("dataset"), row.get("case_id"), row.get("arm")) for row in rows
    ]
    if len(rows) != expected:
        protocol_failures.append(f"episode_count={len(rows)} expected={expected}")
    if len(set(observed_keys)) != expected:
        protocol_failures.append(
            f"unique_case_arm_count={len(set(observed_keys))} expected={expected}"
        )
    if observed_cases != expected_cases:
        protocol_failures.append(
            f"formal_case_set_mismatch missing={len(expected_cases - observed_cases)} "
            f"unexpected={len(observed_cases - expected_cases)}"
        )
    if any(
        {
            row["arm"]
            for row in rows
            if row.get("dataset") == dataset and row.get("case_id") == case_id
        }
        != {A, B, C}
        for dataset, case_id in expected_cases
    ):
        protocol_failures.append("one_or_more_cases_do_not_have_exactly_three_arms")
    if any(
        row.get("partition") != "formal"
        or row.get("model") != model
        or row.get("renderer_version") != 6
        or not row.get("leakage_audit_ok")
        for row in rows
    ):
        protocol_failures.append("row_metadata_or_leakage_audit_mismatch")
    if any(
        row.get("preflight_input_tokens") is None
        or not isinstance(row.get("input_tokens"), int)
        or row["input_tokens"] <= 0
        or row.get("server_token_count_match") is not True
        for row in rows
    ):
        protocol_failures.append("token_accounting_missing_or_mismatched")
    if header.get("formal_roster_sha256") != roster["formal_roster_sha256"]:
        protocol_failures.append("trajectory_header_roster_hash_mismatch")

    qualification_path = (
        ROOT
        / "RQs/RQ0/results"
        / EXPERIMENT
        / "qualification_formal"
        / "qualification_report.json"
    )
    if not qualification_path.is_file():
        protocol_failures.append("formal_static_qualification_report_absent")
    else:
        qualification_bytes = qualification_path.read_bytes()
        qualification = json.loads(qualification_bytes)
        if (
            not qualification.get("all_passed")
            or qualification.get("requested") != 720
            or qualification.get("failed") != 0
            or qualification.get("formal_roster_sha256")
            != roster["formal_roster_sha256"]
        ):
            protocol_failures.append("formal_static_qualification_not_passed")
        if header.get("qualification_report_sha256") != hashlib.sha256(
            qualification_bytes
        ).hexdigest():
            protocol_failures.append("trajectory_header_qualification_hash_mismatch")
        inventory_path = qualification_path.parent / "artifact_inventory.json"
        if not inventory_path.is_file():
            protocol_failures.append("formal_artifact_inventory_absent")
        else:
            inventory_bytes = inventory_path.read_bytes()
            inventory = json.loads(inventory_bytes)
            if (
                not inventory.get("all_passed")
                or inventory.get("case_count") != 720
                or inventory.get("file_count") != 2880
            ):
                protocol_failures.append("formal_artifact_inventory_not_passed")
            if header.get("qualification_inventory_sha256") != hashlib.sha256(
                inventory_bytes
            ).hexdigest():
                protocol_failures.append("trajectory_header_inventory_hash_mismatch")
            token_budget_path = (
                qualification_path.parent / f"token_budget_{model}.json"
            )
            if not token_budget_path.is_file():
                protocol_failures.append("formal_token_budget_gate_absent")
            else:
                token_budget_bytes = token_budget_path.read_bytes()
                token_budget = json.loads(token_budget_bytes)
                if (
                    not token_budget.get("all_fit")
                    or token_budget.get("requested_cases") != 720
                    or token_budget.get("requested_prompts") != 2160
                ):
                    protocol_failures.append("formal_token_budget_gate_not_passed")
                if header.get(
                    "qualification_token_budget_sha256"
                ) != hashlib.sha256(token_budget_bytes).hexdigest():
                    protocol_failures.append(
                        "trajectory_header_token_budget_hash_mismatch"
                    )

    qualification_complete = bool(
        not protocol_failures
        and all(summary["parse_rate"] >= 0.95 for summary in arm_summary.values())
        and len(set(excluded_ab) | set(excluded_ac)) / 720 <= 0.01
    )
    supported = bool(
        qualification_complete
        and ab["macro_dataset_delta_mrr"] is not None
        and ac["macro_dataset_delta_mrr"] is not None
        and ab["macro_dataset_delta_mrr"] >= 0.05
        and ac["macro_dataset_delta_mrr"] >= 0.05
        and ab["holm_adjusted_p"] < 0.05
        and ac["holm_adjusted_p"] < 0.05
        and all(value > -0.05 for value in ab["delta_by_dataset"].values())
        and all(value > -0.05 for value in ac["delta_by_dataset"].values())
    )
    return {
        "model": model,
        "n_rows": len(rows),
        "expected_rows": expected,
        "arm_summary": arm_summary,
        "comparisons": {"A_minus_B": ab, "A_minus_C": ac},
        "agreement": agreement,
        "effect_modifiers": effect_modifiers,
        "protocol_integrity_failures": protocol_failures,
        "qualification_complete": qualification_complete,
        "rq0_supported": supported,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models", nargs="+", default=["qwen3.6-27b", "gemma-4-26b-a4b"]
    )
    parser.add_argument("--replicate", default="main")
    args = parser.parse_args()
    root = ROOT / "RQs/RQ0/results" / EXPERIMENT
    summaries = []
    for model in args.models:
        path = (
            root
            / f"{model}__formal__{args.replicate}"
            / "trajectories"
            / "episodes.jsonl"
        )
        if path.is_file():
            summaries.append(_model_summary(model, path))
    overall = {
        "schema_version": 1,
        "models_requested": args.models,
        "models_analyzed": [summary["model"] for summary in summaries],
        "model_summaries": summaries,
        "rq0_generalized_supported": bool(
            len(summaries) == 2 and all(summary["rq0_supported"] for summary in summaries)
        ),
        "no_confidence_intervals_reported": True,
    }
    out = root / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    (out / "rq0_analysis.json").write_text(json.dumps(overall, indent=2))
    md = [
        "# RQ0 equal-information/equal-compute results",
        "",
        f"Models analyzed: {', '.join(overall['models_analyzed']) or 'none'}",
        "",
        "| model | A MRR | B MRR | C MRR | Δ A−B | p Holm | Δ A−C | p Holm | supported |",
        "|---|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for summary in summaries:
        arms = summary["arm_summary"]
        ab = summary["comparisons"]["A_minus_B"]
        ac = summary["comparisons"]["A_minus_C"]
        md.append(
            f"| {summary['model']} | {_fmt(arms[A]['macro_dataset_mrr'])} | "
            f"{_fmt(arms[B]['macro_dataset_mrr'])} | {_fmt(arms[C]['macro_dataset_mrr'])} | "
            f"{_fmt(ab['macro_dataset_delta_mrr'], '+.4f')} | {_fmt(ab['holm_adjusted_p'], '.4g')} | "
            f"{_fmt(ac['macro_dataset_delta_mrr'], '+.4f')} | {_fmt(ac['holm_adjusted_p'], '.4g')} | "
            f"{'yes' if summary['rq0_supported'] else 'no'} |"
        )
    md.extend(
        [
            "",
            "The table follows the preregistered +0.05 practical-effect threshold, "
            "paired Wilcoxon tests with Holm correction, per-dataset reversal gate, "
            "and parse/infrastructure completeness gates. No confidence intervals are reported.",
            "",
            f"Cross-architecture generalized support: "
            f"**{'yes' if overall['rq0_generalized_supported'] else 'no'}**.",
        ]
    )
    (out / "summary.md").write_text("\n".join(md) + "\n")
    print(json.dumps(overall, indent=2))


if __name__ == "__main__":
    main()

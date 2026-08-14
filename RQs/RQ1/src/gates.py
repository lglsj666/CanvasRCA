"""RQ1 qualification definitions, verification, and paired analysis."""

from __future__ import annotations

import math
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import mean, stdev
from typing import Any

from scipy.stats import wilcoxon

from unified_scripts import stable_hash

from .exps import ExperimentSpec, is_rca_task
from .utils import ROOT, RQ1Error, RunPaths, artifact_contract


@dataclass(frozen=True)
class BoundedQualification:
    name: str
    call_cap: int
    timeout_seconds: int
    correctness_is_pass_condition: bool = False

    def validate(self) -> None:
        absolute = 18 if self.name == "smoke" else 36
        timeout = 600 if self.name == "smoke" else 1200
        if self.call_cap > absolute or self.timeout_seconds > timeout:
            raise RQ1Error(f"{self.name} exceeds the global bounded-qualification rule")


def qualification_contracts(config: Mapping[str, Any]) -> tuple[BoundedQualification, ...]:
    runtime = config["runtime"]
    values = (
        BoundedQualification("smoke", int(runtime["smoke_call_cap"]), int(runtime["smoke_timeout_seconds"])),
        BoundedQualification("gate", int(runtime["gate_call_cap"]), int(runtime["gate_timeout_seconds"])),
    )
    for value in values:
        value.validate()
    return values


def paired_statistics(values: Sequence[float]) -> dict[str, float | int | None]:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return {"n": 0, "delta": None, "p": None, "cohens_dz": None}
    nonzero = [value for value in finite if value != 0.0]
    p = 1.0
    if nonzero:
        try:
            p = float(wilcoxon(finite, zero_method="pratt", alternative="two-sided").pvalue)
        except ValueError:
            p = 1.0
    sd = stdev(finite) if len(finite) > 1 else 0.0
    delta = mean(finite)
    return {"n": len(finite), "delta": delta, "p": p, "cohens_dz": delta / sd if sd else 0.0}


def analyze_stage_pair(
    direct_records: Sequence[Mapping[str, Any]], two_stage_records: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Describe matched two-stage minus direct-RCA performance and cost."""

    headline = set(map(str, config["data"]["headline_datasets"]))
    def indexed(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str, str, str], Mapping[str, Any]]:
        return {
            (str(row.get("model")), str(row.get("opaque_incident_id")),
             str(row.get("arm")), str(row.get("analysis_dataset"))): row
            for row in rows if row.get("status") == "completed"
            and str(row.get("analysis_dataset")) in headline and row.get("score")
        }
    direct, staged = indexed(direct_records), indexed(two_stage_records)
    common, union = set(direct) & set(staged), set(direct) | set(staged)
    metrics = ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")
    def cost(row: Mapping[str, Any], field: str) -> float:
        if field == "calls":
            return float(len(row.get("stages") or ()))
        return sum(float(stage.get(field) or 0) for stage in row.get("stages") or ())
    models: dict[str, Any] = {}
    for model in sorted({key[0] for key in common}):
        model_keys = [key for key in common if key[0] == model]
        models[model] = {"by_arm": {}, "by_dataset_mrr": {}}
        for arm in sorted({key[2] for key in model_keys}):
            keys = [key for key in model_keys if key[2] == arm]
            models[model]["by_arm"][arm] = {
                "performance_two_minus_one": {
                    metric: paired_statistics([
                        float(staged[key]["score"][metric]) - float(direct[key]["score"][metric])
                        for key in keys
                    ]) for metric in metrics
                },
                "cost_two_minus_one": {
                    field: paired_statistics([cost(staged[key], field) - cost(direct[key], field) for key in keys])
                    for field in ("calls", "total_tokens", "wall_time_s")
                },
            }
        for dataset in sorted({key[3] for key in model_keys}):
            keys = [key for key in model_keys if key[3] == dataset]
            models[model]["by_dataset_mrr"][dataset] = paired_statistics([
                float(staged[key]["score"]["mrr"]) - float(direct[key]["score"]["mrr"])
                for key in keys
            ])
    result = {
        "schema_version": "RQ1StageArchitectureComparisonV1",
        "comparison": "matched_rca_two_stage-minus-direct_rca_one_stage",
        "interpretation": "descriptive architecture comparison; not an isolated causal stage-count effect",
        "paired_cells": len(common), "unpaired_cells": len(union - common),
        "complete": bool(common) and common == union, "by_model": models,
    }
    result["analysis_sha256"] = stable_hash(result)
    return result


def holm(rows: Mapping[str, Mapping[str, Any]]) -> dict[str, float | None]:
    ordered = sorted((float(row["p"]), name) for name, row in rows.items() if row.get("p") is not None)
    adjusted: dict[str, float | None] = {name: None for name in rows}
    running = 0.0
    total = len(ordered)
    for index, (p, name) in enumerate(ordered):
        running = max(running, min(1.0, p * (total - index)))
        adjusted[name] = running
    return adjusted


def _parse_rates(records: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    values: dict[str, list[bool]] = defaultdict(list)
    for record in records:
        if record.get("status") != "completed" or not record.get("stages"):
            continue
        values[str(record["arm"])].append(all(bool(stage.get("parse")) for stage in record["stages"]))
    return {arm: sum(rows) / len(rows) for arm, rows in sorted(values.items()) if rows}


def _stage_parse_rates(records: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    values: dict[str, dict[int, list[bool]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        if record.get("status") != "completed":
            continue
        for stage in record.get("stages", ()):
            values[str(record["arm"])][int(stage["stage"])].append(bool(stage.get("parse")))
    return {arm: {f"stage_{stage}": sum(rows) / len(rows) for stage, rows in sorted(stages.items())}
            for arm, stages in sorted(values.items())}


def _accounting(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    output = {}
    for arm in sorted({str(record.get("arm")) for record in records}):
        stages = [stage for record in records if record.get("status") == "completed" and str(record.get("arm")) == arm
                  for stage in record.get("stages", ())]
        if not stages:
            continue
        def average(key: str) -> float | None:
            values = [float(row[key]) for row in stages if row.get(key) is not None]
            return mean(values) if values else None
        output[arm] = {
            "calls": sum("input_tokens" in row for row in stages),
            "avg_input_tokens": average("input_tokens"), "avg_text_tokens": average("text_tokens"),
            "avg_image_tokens": average("image_tokens"), "avg_output_tokens": average("output_tokens"),
            "avg_total_tokens": average("total_tokens"), "avg_wall_time_s": average("wall_time_s"),
            "avg_gpu_active_time_s": average("gpu_active_time_s"),
            "peak_gpu_memory_bytes": max((int(row["peak_gpu_memory_bytes"]) for row in stages
                                           if row.get("peak_gpu_memory_bytes") is not None), default=None),
            "truncation_rate": sum(bool(row.get("truncated")) for row in stages) / len(stages),
        }
    return output


def _ledger_metrics(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_arm: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        stages = record.get("stages") or ()
        if record.get("status") == "completed" and stages:
            ledger = stages[0].get("normalized") or {}
            if isinstance(ledger, Mapping):
                by_arm[str(record["arm"])].append(ledger)
    result = {}
    for arm, ledgers in sorted(by_arm.items()):
        supported = [int((row.get("binding_audit") or {}).get("supported_observations") or 0) for row in ledgers]
        unsupported = [int((row.get("binding_audit") or {}).get("unsupported_observations") or 0) for row in ledgers]
        total = sum(supported) + sum(unsupported)
        region_counts: dict[str, int] = defaultdict(int)
        for ledger in ledgers:
            observations = list(ledger.get("observations") or ())
            observations.extend(
                observation
                for query in ledger.get("ledgers") or () if isinstance(query, Mapping)
                for observation in query.get("observations") or ()
            )
            for observation in observations:
                if isinstance(observation, Mapping) and str(observation.get("region")) in {"M", "L", "R", "G"}:
                    region_counts[str(observation["region"])] += 1
        region_total = sum(region_counts.values())
        result[arm] = {
            "stage1_ledgers": len(ledgers),
            "observation_grounding_precision": sum(supported) / total if total else 0.0,
            "avg_grounded_observations": mean(supported) if supported else 0.0,
            "unsupported_claim_rate": sum(unsupported) / total if total else 0.0,
            "avg_validated_directed_edges": mean([len(row.get("directed_edges") or ()) for row in ledgers]),
            "avg_validated_temporal_relations": mean([len(row.get("temporal_relations") or ()) for row in ledgers]),
            "selected_region_counts": dict(sorted(region_counts.items())),
            "selected_region_share": {
                region: count / region_total for region, count in sorted(region_counts.items())
            } if region_total else {},
        }
    return result


def _visual_metrics(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate renderer-side visual density without treating it as attention."""

    result: dict[str, Any] = {}
    for arm in sorted({str(record.get("arm")) for record in records}):
        rows = [record.get("visual_diagnostic") or {} for record in records
                if record.get("status") == "completed" and str(record.get("arm")) == arm]
        if not rows:
            continue
        def average(key: str) -> float | None:
            values = [float(row[key]) for row in rows if row.get(key) is not None]
            return mean(values) if values else None
        result[arm] = {
            "records": len(rows), "image_rate": mean([float(row.get("image_count") or 0) > 0 for row in rows]),
            "avg_blank_patch_fraction": average("blank_patch_fraction"),
            "avg_evidence_patch_fraction": average("evidence_patch_fraction"),
            "avg_incident_evidence_patch_fraction": average("incident_evidence_patch_fraction"),
            "avg_encoded_region_patch_fraction": average("encoded_region_patch_fraction"),
            "avg_mean_ink_fraction": average("mean_ink_fraction"),
            "attention_statuses": sorted({str(row.get("attention_status")) for row in rows}),
            "attention_artifacts": sum(int(row.get("attention_artifacts") or 0) for row in rows),
        }
    return result


def _arm_means(records: Sequence[Mapping[str, Any]], metric: str) -> dict[str, float]:
    by_arm: dict[str, list[float]] = defaultdict(list)
    for record in records:
        value = (record.get("score") or {}).get(metric)
        if record.get("status") == "completed" and value is not None:
            by_arm[str(record["arm"])].append(float(value))
    return {arm: mean(values) for arm, values in sorted(by_arm.items()) if values}


def _nested_score_arm_means(
    records: Sequence[Mapping[str, Any]], metric: str,
) -> dict[str, dict[str, float]]:
    by_arm: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        values = (record.get("score") or {}).get(metric)
        if record.get("status") != "completed" or not isinstance(values, Mapping):
            continue
        for key, value in values.items():
            if value is not None:
                by_arm[str(record["arm"])][str(key)].append(float(value))
    return {
        arm: {key: mean(values) for key, values in sorted(metrics.items()) if values}
        for arm, metrics in sorted(by_arm.items())
    }


def _comparison(records: Sequence[Mapping[str, Any]], left: str, right: str, metric: str) -> dict[str, Any]:
    table: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for record in records:
        value = (record.get("score") or {}).get(metric)
        if record.get("status") == "completed" and value is not None:
            table[(str(record["model"]), str(record["opaque_incident_id"]))][str(record["arm"])] = float(value)
    differences = [row[left] - row[right] for row in table.values() if left in row and right in row]
    return {"left": left, "right": right, "metric": metric, **paired_statistics(differences)}


def _whole_case_filter(
    records: Sequence[Mapping[str, Any]],
    arms: Sequence[str],
    expected_case_keys: Sequence[tuple[str, str]] | None = None,
) -> tuple[list[Mapping[str, Any]], dict[str, Any]]:
    table: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for key in expected_case_keys or ():
        table[(str(key[0]), str(key[1]))]
    for record in records:
        table[(str(record.get("model")), str(record.get("opaque_incident_id")))].append(record)
    excluded = {key for key, rows in table.items() if any(row.get("status") == "infrastructure_error" for row in rows)}
    ineligible = {key for key, rows in table.items() if any(row.get("status") == "protocol_ineligible" for row in rows)}
    required = set(arms)
    incomplete = {key for key, rows in table.items() if {str(row.get("arm")) for row in rows} != required}
    kept = [row for key, rows in table.items() if key not in excluded | ineligible | incomplete for row in rows]
    total = len(table)
    return kept, {
        "total_cases": total, "included_cases": len({(r.get('model'), r.get('opaque_incident_id')) for r in kept}),
        "infrastructure_excluded_cases": len(excluded),
        "infrastructure_exclusion_rate": len(excluded) / total if total else 0.0,
        "protocol_ineligible_cases": len(ineligible), "incomplete_pair_cases": len(incomplete),
    }


def _rr(predictions: Sequence[str], entity: str) -> float:
    try:
        return 1.0 / (list(predictions).index(entity) + 1)
    except ValueError:
        return 0.0


def _rbo_at_k(left: Sequence[str], right: Sequence[str], *, depth: int = 5, p: float = 0.9) -> float:
    """Finite extrapolated rank-biased overlap, padded only by absent ranks."""

    if not left and not right:
        return 1.0
    depth = min(depth, max(len(left), len(right)))
    agreements = []
    for rank in range(1, depth + 1):
        agreements.append(len(set(left[:rank]) & set(right[:rank])) / rank)
    return (1 - p) * sum(value * p ** index for index, value in enumerate(agreements)) + agreements[-1] * p ** depth


def _ledger_semantic_set(record: Mapping[str, Any]) -> set[str]:
    observations = ((record.get("stages") or [{}])[0].get("normalized") or {}).get("observations") or ()
    keys = ("region", "entity_ids", "field", "attributes", "relative_bins", "values", "unit")
    return {json.dumps({key: row.get(key) for key in keys}, sort_keys=True) for row in observations}


def _counterfactual_cvi(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    table: dict[tuple[str, str], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for record in records:
        table[(str(record.get("model")), str(record.get("opaque_incident_id")))][str(record.get("arm"))] = record
    values: list[float] = []
    targeted_changes = 0
    top1_changes = 0
    rbo_distances: list[float] = []
    neutral_rbo_distances: list[float] = []
    ledger_jaccards: list[float] = []
    benefit = harm = 0
    paired = 0
    for row in table.values():
        factual = row.get("H_factual")
        targeted = row.get("H_targeted")
        placebo = row.get("H_placebo")
        neutral = row.get("H_neutral")
        if not factual or not targeted or not placebo or not neutral:
            continue
        factual_rank = list(map(str, (factual.get("score") or {}).get("numeric_predictions") or ()))
        vfs: dict[str, float] = {}
        for name, condition in (("targeted", targeted), ("placebo", placebo)):
            pair = list(map(str, condition.get("counterfactual_pair") or ()))
            if len(pair) != 2:
                break
            donor, recipient = pair
            changed_rank = list(map(str, (condition.get("score") or {}).get("numeric_predictions") or ()))
            vfs[name] = 0.5 * (
                _rr(changed_rank, recipient) - _rr(factual_rank, recipient)
                + _rr(factual_rank, donor) - _rr(changed_rank, donor)
            )
        if len(vfs) != 2:
            continue
        values.append(vfs["targeted"] - vfs["placebo"])
        paired += 1
        target_rank = list(map(str, (targeted.get("score") or {}).get("numeric_predictions") or ()))
        targeted_changes += int(target_rank != factual_rank)
        top1_changes += int((target_rank[:1] or [None]) != (factual_rank[:1] or [None]))
        neutral_rank = list(map(str, (neutral.get("score") or {}).get("numeric_predictions") or ()))
        rbo_distances.append(1 - _rbo_at_k(factual_rank, target_rank))
        neutral_rbo_distances.append(1 - _rbo_at_k(factual_rank, neutral_rank))
        factual_obs, target_obs = _ledger_semantic_set(factual), _ledger_semantic_set(targeted)
        union = factual_obs | target_obs
        ledger_jaccards.append(len(factual_obs & target_obs) / len(union) if union else 1.0)
        delta_mrr = float((targeted.get("score") or {}).get("mrr") or 0) - float((factual.get("score") or {}).get("mrr") or 0)
        benefit += int(delta_mrr > 0); harm += int(delta_mrr < 0)
    return {
        **paired_statistics(values), "paired_cases": paired,
        "targeted_top1_change_rate": top1_changes / paired if paired else 0.0,
        "targeted_top5_change_rate": targeted_changes / paired if paired else 0.0,
        "mean_one_minus_rbo_at_5": mean(rbo_distances) if rbo_distances else 0.0,
        "neutral_mean_one_minus_rbo_at_5": mean(neutral_rbo_distances) if neutral_rbo_distances else 0.0,
        "mean_ledger_semantic_jaccard": mean(ledger_jaccards) if ledger_jaccards else 0.0,
        "visual_benefit_rate": benefit / paired if paired else 0.0,
        "visual_harm_rate": harm / paired if paired else 0.0,
    }


def _factorial_effect(records: Sequence[Mapping[str, Any]], region: str, metric: str) -> dict[str, Any]:
    table: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for row in records:
        value = (row.get("score") or {}).get(metric)
        if row.get("status") == "completed" and value is not None:
            table[(str(row.get("model")), str(row.get("opaque_incident_id")))][str(row.get("arm"))] = float(value)
    values = []
    for cells in table.values():
        visual = [value for arm, value in cells.items() if f"{region}v" in arm]
        textual = [value for arm, value in cells.items() if f"{region}t" in arm]
        if len(visual) == len(textual) == 8:
            values.append(mean(visual) - mean(textual))
    return {"region": region, "metric": metric, **paired_statistics(values)}


def analyze_records(
    records: Sequence[Mapping[str, Any]],
    spec: ExperimentSpec,
    config: Mapping[str, Any],
    *,
    expected_models: Sequence[str] | None = None,
    expected_case_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    models = sorted(
        set(map(str, expected_models))
        if expected_models is not None
        else {str(record.get("model")) for record in records}
    )
    if len(models) > 1:
        result = {
            "schema_version": "RQ1AnalysisV4",
            "experiment": spec.name,
            "by_model": {
                model: analyze_records(
                    [row for row in records if str(row.get("model")) == model],
                    spec,
                    config,
                    expected_models=(model,),
                    expected_case_ids=expected_case_ids,
                )
                for model in models
            },
        }
        result["complete"] = all(row["complete"] for row in result["by_model"].values())
        result["analysis_sha256"] = stable_hash(result)
        return result
    expected_case_keys = (
        tuple((models[0], str(case_id)) for case_id in expected_case_ids)
        if expected_case_ids is not None and len(models) == 1
        else None
    )
    filtered, exclusion = _whole_case_filter(records, spec.arms, expected_case_keys)
    total = len(records)
    headline_datasets = set(map(str, config["data"]["headline_datasets"]))
    headline = [row for row in filtered if str(row.get("analysis_dataset")) in headline_datasets]
    parse_rates = _parse_rates(filtered)
    result: dict[str, Any] = {
        "schema_version": "RQ1AnalysisV5",
        "experiment": spec.name,
        "task": spec.task,
        "records": total,
        "whole_case_exclusion": exclusion,
        "parse_rate_by_arm": parse_rates,
        "stage_parse_rate_by_arm": _stage_parse_rates(filtered),
        "headline_datasets": sorted(headline_datasets),
        "headline_arm_means": _arm_means(headline, spec.primary_metric),
        "all_slice_arm_means": _arm_means(filtered, spec.primary_metric),
        "accounting_by_arm": _accounting(filtered),
        "stage1_ledger_metrics_by_arm": (
            {} if spec.task == "root_cause_direct" else _ledger_metrics(filtered)
        ),
        "visual_processing_diagnostics_by_arm": _visual_metrics(filtered),
        "attention_diagnostics": {
            "status": "same_prefill_qk_probe",
            "artifacts": sum(
                len((stage.get("attention_probe") or {}).get("artifacts") or ())
                for row in filtered for stage in row.get("stages") or ()
            ),
            "extra_model_calls": 0,
            "interpretation": "model-internal Q-to-visual-K attention is correlational; counterfactuals remain causal evidence",
        },
    }
    if is_rca_task(spec):
        if spec.task == "root_cause_counterfactual":
            pairs = (("H_targeted", "H_factual"), ("H_placebo", "H_factual"), ("H_neutral", "H_factual"))
            primary_keys = ("H_targeted-H_factual", "H_placebo-H_factual")
        elif spec.task == "root_cause_handoff":
            pairs = (("L_vis", "L_txt"), ("L_hyb", "L_txt"), ("L_hyb", "L_vis"))
            primary_keys = ("L_vis-L_txt", "L_hyb-L_txt")
        else:
            pairs = (("R", "T"), ("R", "F"), ("V", "T"), ("H", "T"), ("R", "H"), ("T", "F"))
            primary_keys = ("R-T", "R-F")
        comparisons = {f"{left}-{right}": _comparison(headline, left, right, "mrr") for left, right in pairs}
        adjusted = holm({key: comparisons[key] for key in primary_keys})
        for key, value in adjusted.items():
            comparisons[key]["holm_adjusted_p"] = value
        threshold = float(config["analysis"]["rca_minimum_effect"])
        result["comparisons"] = comparisons
        if spec.task == "root_cause_counterfactual":
            result["cvi"] = _counterfactual_cvi(headline)
            cvi_threshold = float(config["analysis"].get("counterfactual_cvi_minimum", 0.05))
            result["primary_supported"] = (
                result["cvi"].get("delta") is not None
                and result["cvi"]["delta"] >= cvi_threshold
                and result["cvi"].get("p") is not None and result["cvi"]["p"] < 0.05
                and result["cvi"]["targeted_top1_change_rate"] >= float(config["analysis"]["counterfactual_top1_change_minimum"])
                and result["cvi"]["targeted_top5_change_rate"] >= float(config["analysis"]["counterfactual_top5_change_minimum"])
                and result["cvi"]["mean_one_minus_rbo_at_5"] >= float(config["analysis"]["counterfactual_rank_distance_minimum"])
            )
        else:
            result["primary_supported"] = all(
                comparisons[key].get("delta") is not None
                and comparisons[key]["delta"] >= threshold
                and comparisons[key].get("holm_adjusted_p") is not None
                and comparisons[key]["holm_adjusted_p"] < 0.05
                for key in primary_keys
            )
        result["by_dataset"] = {
            dataset: {
                "records": len(subset),
                "arm_means": _arm_means(subset, "mrr"),
                "comparisons": {f"{left}-{right}": _comparison(subset, left, right, "mrr") for left, right in pairs},
            }
            for dataset in sorted({str(row.get("analysis_dataset")) for row in filtered})
            if (subset := [row for row in filtered if str(row.get("analysis_dataset")) == dataset])
        }
        if spec.task in {"root_cause_ranking", "root_cause_direct"}:
            reverse_effects = {
                dataset: {
                    key: result["by_dataset"][dataset]["comparisons"][key].get("delta")
                    for key in primary_keys
                }
                for dataset in sorted(headline_datasets) if dataset in result["by_dataset"]
            }
            result["headline_dataset_reverse_effects"] = reverse_effects
            result["primary_supported"] = bool(result["primary_supported"]) and all(
                delta is not None and delta > -threshold
                for values in reverse_effects.values() for delta in values.values()
            )
        result["by_fault"] = {
            fault: {"records": len(subset), "arm_means": _arm_means(subset, "mrr")}
            for fault in sorted({str(row.get("analysis_fault_type")) for row in headline})
            if (subset := [row for row in headline if str(row.get("analysis_fault_type")) == fault])
        }
    else:
        text_arm = "T" if spec.name == "legacy_q9" else "Mt-Rt-Lt-Gt"
        qa_metrics = (
            "complete_chain_accuracy", "correct_prefix_accuracy", "step_accuracy",
            "level_1_complete_chain_accuracy", "level_2_complete_chain_accuracy",
            "level_3_complete_chain_accuracy", "eligible_question_count",
        )
        result["qa_metric_arm_means"] = {
            metric: {
                "headline": _arm_means(headline, metric),
                "all_slices": _arm_means(filtered, metric),
            }
            for metric in qa_metrics
        }
        result["template_complete_chain_accuracy_by_arm"] = {
            "headline": _nested_score_arm_means(headline, "template_complete_chain_accuracy"),
            "all_slices": _nested_score_arm_means(filtered, "template_complete_chain_accuracy"),
        }
        result["comparisons"] = {
            "P-T": _comparison(headline, "P", text_arm, spec.primary_metric),
            "V-P": _comparison(headline, "V", "P", spec.primary_metric),
            "V-T": _comparison(headline, "V", text_arm, spec.primary_metric),
            "H-T": _comparison(headline, "H", text_arm, spec.primary_metric),
            "H-V": _comparison(headline, "H", "V", spec.primary_metric),
        }
        if spec.name != "legacy_q9":
            result["visual_main_effects"] = {
                region: _factorial_effect(headline, region, spec.primary_metric) for region in ("M", "L", "R", "G")
            }
            result["comparisons"]["factorial_all_visual-minus-all_text"] = _comparison(
                headline, "Mv-Rv-Lv-Gv", "Mt-Rt-Lt-Gt", spec.primary_metric,
            )
        result["by_dataset"] = {
            dataset: {
                "records": len(subset),
                "arm_means": _arm_means(subset, spec.primary_metric),
                "level_arm_means": {
                    metric: _arm_means(subset, metric)
                    for metric in qa_metrics if metric.startswith("level_")
                },
                "template_arm_means": _nested_score_arm_means(
                    subset, "template_complete_chain_accuracy",
                ),
            }
            for dataset in sorted({str(row.get("analysis_dataset")) for row in filtered})
            if (subset := [row for row in filtered if str(row.get("analysis_dataset")) == dataset])
        }
    minimum_parse = float(config["runtime"]["parse_rate_minimum"])
    result["complete"] = (
        bool(parse_rates) and all(value >= minimum_parse for value in parse_rates.values())
        and exclusion["infrastructure_exclusion_rate"] <= float(config["runtime"]["whole_case_infrastructure_exclusion_maximum"])
        and exclusion["incomplete_pair_cases"] == 0
    )
    result["analysis_sha256"] = stable_hash(result)
    return result


def verify_result_root(paths: RunPaths, config: Mapping[str, Any],
                       prepared_paths: RunPaths | None = None) -> dict[str, Any]:
    qualification_contracts(config)
    prepared_paths = prepared_paths or paths
    index_path = prepared_paths.prepared / "index.json"
    if not index_path.is_file():
        raise RQ1Error("prepared index is missing")
    index = json.loads(index_path.read_text())
    missing: list[str] = []
    integrity_errors: list[str] = []
    unsigned_index = dict(index)
    recorded_index_hash = unsigned_index.pop("index_sha256", None)
    if not recorded_index_hash or stable_hash(unsigned_index) != recorded_index_hash:
        integrity_errors.append("prepared/index.json")
    current_freeze = artifact_contract(
        config=config,
        code_files=tuple(sorted((ROOT / "RQs/RQ1/src").rglob("*.py"))),
    )
    if current_freeze["freeze_sha256"] != index.get("runtime_freeze", {}).get("freeze_sha256"):
        integrity_errors.append("runtime_freeze")
    for item in index.get("cases", ()):
        item_missing = False
        for key in ("public", "private", "full_image", "qa_full_image", "routed_image"):
            path = prepared_paths.root / item[key]
            if not path.is_file():
                missing.append(f"prepared:{path.relative_to(prepared_paths.root)}")
                item_missing = True
        for values in item.get("qa_region_images", {}).values():
            for relative in values:
                path = prepared_paths.root / relative
                if not path.is_file():
                    missing.append(f"prepared:{path.relative_to(prepared_paths.root)}")
                    item_missing = True
        for relative in item.get("variant_images", {}).values():
            path = prepared_paths.root / relative
            if not path.is_file():
                missing.append(f"prepared:{path.relative_to(prepared_paths.root)}")
                item_missing = True
        if item_missing:
            continue
        public = json.loads((prepared_paths.root / item["public"]).read_text(encoding="utf-8"))
        private = json.loads((prepared_paths.root / item["private"]).read_text(encoding="utf-8"))
        checks = {
            "public_sha256": stable_hash(public),
            "private_sha256": stable_hash(private),
            "full_image_sha256": stable_hash((prepared_paths.root / item["full_image"]).read_bytes()),
            "qa_full_image_sha256": stable_hash((prepared_paths.root / item["qa_full_image"]).read_bytes()),
            "routed_image_sha256": stable_hash((prepared_paths.root / item["routed_image"]).read_bytes()),
        }
        for key, observed in checks.items():
            if observed != item.get(key):
                integrity_errors.append(f"{item.get('opaque_incident_id')}:{key}")
        for name, relative in item.get("variant_images", {}).items():
            observed = stable_hash((prepared_paths.root / relative).read_bytes())
            if observed != item.get("variant_image_sha256", {}).get(name):
                integrity_errors.append(f"{item.get('opaque_incident_id')}:variant:{name}")
        observed_regions = {
            region: [stable_hash((prepared_paths.root / relative).read_bytes()) for relative in values]
            for region, values in item.get("qa_region_images", {}).items()
        }
        if observed_regions != item.get("qa_region_image_sha256"):
            integrity_errors.append(f"{item.get('opaque_incident_id')}:qa_region_images")
    trajectories = list(paths.trajectories.rglob("*.json"))
    for path in trajectories:
        if not path.with_suffix(".md").is_file():
            missing.append(str(path.with_suffix(".md").relative_to(paths.root)))
        record = json.loads(path.read_text(encoding="utf-8"))
        for key in ("call_key", "representation_hash", "runtime_freeze_sha256"):
            if not record.get(key):
                integrity_errors.append(f"{path.relative_to(paths.root)}:missing_{key}")
        if record.get("runtime_freeze_sha256") != index.get("runtime_freeze", {}).get("freeze_sha256"):
            integrity_errors.append(f"{path.relative_to(paths.root)}:runtime_freeze")
        calls = list(record.get("stages") or ())
        if isinstance(record.get("call"), Mapping):
            calls.append(record["call"])
        for call in calls:
            prompt_has_image = any(
                part.get("type") == "image"
                for part in (call.get("prompt") or {}).get("parts") or ()
            )
            probe = call.get("attention_probe") or {}
            if prompt_has_image and probe.get("status") != "collected_same_prefill":
                integrity_errors.append(f"{path.relative_to(paths.root)}:missing_attention")
            for artifact in probe.get("artifacts") or ():
                for key, hash_key in (("grid_path", "grid_sha256"), ("overlay_path", "overlay_sha256")):
                    artifact_path = paths.root / artifact[key]
                    if not artifact_path.is_file():
                        missing.append(str(artifact_path.relative_to(paths.root)))
                        continue
                    value = (json.loads(artifact_path.read_text()) if key == "grid_path"
                             else artifact_path.read_bytes())
                    if stable_hash(value) != artifact[hash_key]:
                        integrity_errors.append(f"{artifact_path.relative_to(paths.root)}:hash")
        recorded = record.pop("record_sha256", None)
        if not recorded or stable_hash(record) != recorded:
            integrity_errors.append(str(path.relative_to(paths.root)))
    result = {
        "schema_version": "RQ1VerificationV2",
        "prepared_experiment_id": index.get("experiment_id"),
        "prepared_cases": len(index.get("cases", ())),
        "trajectories": len(trajectories),
        "missing": sorted(missing),
        "integrity_errors": sorted(integrity_errors),
        "passed": not missing and not integrity_errors,
    }
    result["verification_sha256"] = stable_hash(result)
    return result

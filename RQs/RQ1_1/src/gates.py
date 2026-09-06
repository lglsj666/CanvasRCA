"""RQ1.1 result aggregation, paired statistics, and artifact verification."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
from collections import Counter, defaultdict
from statistics import mean
from typing import Any, Mapping, Sequence

import numpy as np

from unified_scripts import stable_hash
from vlmrca.vlm.performance import summarize_call_performance

from .utils import RunPaths

REGIONS = ("M", "R", "L", "G")
FACTORIAL_ARM_REGIONS = {
    "T": (), "MV": ("M",), "TCV": ("R",), "LV": ("L",), "TPV": ("G",),
    "V_MR": ("M", "R"), "V_ML": ("M", "L"), "V_MG": ("M", "G"),
    "V_RL": ("R", "L"), "V_RG": ("R", "G"), "V_LG": ("L", "G"),
    "V_MRL": ("M", "R", "L"), "V_MRG": ("M", "R", "G"),
    "V_MLG": ("M", "L", "G"), "V_RLG": ("R", "L", "G"),
    "V": REGIONS,
}


def _paired_statistics(deltas: Sequence[float]) -> dict[str, Any]:
    values = np.asarray(deltas, dtype=float)
    if not len(values):
        return {"n": 0, "delta": None, "wilcoxon_p": None, "cohens_dz": None}
    p = None
    try:
        from scipy.stats import wilcoxon
        p = float(wilcoxon(values, zero_method="pratt", alternative="two-sided").pvalue)
    except (ValueError, ImportError):
        p = 1.0 if np.all(values == 0) else None
    sd = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    return {
        "n": len(values), "delta": float(np.mean(values)), "wilcoxon_p": p,
        "cohens_dz": float(np.mean(values) / sd) if sd else (0.0 if np.mean(values) == 0 else None),
        "improve": int(np.sum(values > 0)), "degrade": int(np.sum(values < 0)), "tie": int(np.sum(values == 0)),
    }


def _holm(rows: Mapping[str, Mapping[str, Any]]) -> dict[str, float | None]:
    valid = sorted((float(row["wilcoxon_p"]), name) for name, row in rows.items() if row.get("wilcoxon_p") is not None)
    output: dict[str, float | None] = {name: None for name in rows}
    running = 0.0
    count = len(valid)
    for rank, (p, name) in enumerate(valid):
        running = max(running, min(1.0, p * (count - rank)))
        output[name] = running
    return output


def _calls(row: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    calls = []
    for stage in row.get("stages", ()):
        if "planner" in stage:
            calls.extend((stage.get("planner") or {}, stage.get("analysis") or {}))
        else:
            calls.append(stage)
    return calls


def _has_registered_generation_target(call: Mapping[str, Any]) -> bool:
    """Whether the normalized answer contains an alphanumeric target token."""

    normalized = call.get("normalized") or {}
    values: list[Any] = list(normalized.get("services") or ())
    for step in normalized.get("steps") or ():
        values.extend((step or {}).get("values") or ())
    return any(re.search(r"[A-Za-z0-9]", str(value)) for value in values)


def _ranking(row: Mapping[str, Any]) -> list[str]:
    stages = list(row.get("stages") or ())
    return list(map(str, ((stages[-1].get("normalized") if stages else {}) or {}).get("services") or ()))


def _rbo5(left: Sequence[str], right: Sequence[str], p: float = 0.9) -> float:
    score = 0.0
    for depth in range(1, 6):
        overlap = len(set(left[:depth]) & set(right[:depth])) / depth
        score += (1.0 - p) * p ** (depth - 1) * overlap
    return score + p**5 * len(set(left[:5]) & set(right[:5])) / 5


def _counterfactual_analysis(records: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> dict[str, Any]:
    table: dict[tuple[str, str], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in records:
        if row.get("status") == "completed":
            table[(str(row["model"]), str(row["opaque_incident_id"]))][str(row["arm"])] = row
    output = {}
    for model in sorted({key[0] for key in table}):
        for scope in ("headline", *config["data"]["allowed_datasets"]):
            values = []
            for (row_model, _case), arms in table.items():
                if row_model != model or set(arms) != {"V_FACTUAL", "V_TARGETED", "V_PLACEBO", "V_NEUTRAL"}:
                    continue
                factual = arms["V_FACTUAL"]
                if scope == "headline" and factual.get("analysis_dataset") not in config["data"]["headline_datasets"]:
                    continue
                if scope != "headline" and factual.get("analysis_dataset") != scope:
                    continue
                ranks = {arm: _ranking(row) for arm, row in arms.items()}
                vfs = {}
                for condition in ("TARGETED", "PLACEBO"):
                    donor, recipient = map(str, arms[f"V_{condition}"].get("counterfactual_pair") or (None, None))
                    rr = lambda ranking, entity: 1 / (ranking.index(entity) + 1) if entity in ranking else 0.0
                    vfs[condition] = .5 * (rr(ranks[f"V_{condition}"], recipient) - rr(ranks["V_FACTUAL"], recipient)
                                            + rr(ranks["V_FACTUAL"], donor) - rr(ranks[f"V_{condition}"], donor))
                values.append({"cvi": vfs["TARGETED"] - vfs["PLACEBO"], "ranks": ranks, "arms": arms})
            deltas = [row["cvi"] for row in values]
            stats = _paired_statistics(deltas)
            stats.update({
                "mechanism_threshold_passed": stats["delta"] is not None and stats["delta"] >= float(config["analysis"]["counterfactual_minimum_effect"]) and stats["wilcoxon_p"] is not None and stats["wilcoxon_p"] < .05,
                "targeted_top1_change_rate": mean(float(row["ranks"]["V_TARGETED"][:1] != row["ranks"]["V_FACTUAL"][:1]) for row in values) if values else None,
                "targeted_top5_change_rate": mean(float(row["ranks"]["V_TARGETED"] != row["ranks"]["V_FACTUAL"]) for row in values) if values else None,
                "targeted_one_minus_rbo5": mean(1 - _rbo5(row["ranks"]["V_TARGETED"], row["ranks"]["V_FACTUAL"]) for row in values) if values else None,
                "neutral_one_minus_rbo5": mean(1 - _rbo5(row["ranks"]["V_NEUTRAL"], row["ranks"]["V_FACTUAL"]) for row in values) if values else None,
                "targeted_visual_benefit_rate": mean(float(row["arms"]["V_TARGETED"]["score"]["mrr"] > row["arms"]["V_FACTUAL"]["score"]["mrr"]) for row in values) if values else None,
                "targeted_visual_harm_rate": mean(float(row["arms"]["V_TARGETED"]["score"]["mrr"] < row["arms"]["V_FACTUAL"]["score"]["mrr"]) for row in values) if values else None,
            })
            output[f"{model}:{scope}"] = stats
    return output


def _attention_means(calls: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    probes = [call.get("attention_probe") or {} for call in calls]
    probes = [probe for probe in probes if probe.get("status") == "collected_same_prefill"]
    if not probes:
        return {
            "avg_visual_attention_mass": None,
            "avg_nonvisual_attention_mass": None,
            "avg_text_mapping_coverage": None,
            "avg_dashboard_header_attention_mass": None,
            "first_patch_attention_argmax_rate": None,
            "first_patch_weighted_value_argmax_rate": None,
        }
    header, attention_first, contribution_first = [], [], []
    prefill_density: dict[str, list[float]] = defaultdict(list)
    generation_density: dict[str, list[float]] = defaultdict(list)
    text_focus: dict[str, list[float]] = defaultdict(list)
    generation_text_focus: dict[str, list[float]] = defaultdict(list)
    for probe in probes:
        for label, row in (probe.get("text_regions") or {}).items():
            if row.get("normalized_focus") is not None:
                text_focus[str(label)].append(float(row["normalized_focus"]))
        for artifact in probe.get("image_artifacts") or ():
            diagnostics = artifact.get("diagnostics") or {}
            mass = diagnostics.get("global_region_mass") or {}
            if "dashboard_header_band" in mass:
                header.append(float(mass["dashboard_header_band"]))
            for region, value in (diagnostics.get("region_density_lift") or {}).items():
                if region in REGIONS and value is not None:
                    prefill_density[region].append(float(value))
            attention_first.append(float(
                (artifact.get("attention_peak_diagnostics") or {}).get("argmax_patch_index") == 0
            ))
            contribution_first.append(float(
                (artifact.get("weighted_value_peak_diagnostics") or {}).get("argmax_patch_index") == 0
            ))
        generation = probe.get("generation_target_attention") or {}
        if generation.get("status") == "collected":
            for label, row in (generation.get("text_regions") or {}).items():
                if row.get("normalized_focus") is not None:
                    generation_text_focus[str(label)].append(float(row["normalized_focus"]))
            for artifact in generation.get("image_artifacts") or ():
                for region, value in ((artifact.get("diagnostics") or {}).get("region_density_lift") or {}).items():
                    if region in REGIONS and value is not None:
                        generation_density[region].append(float(value))
    return {
        "avg_visual_attention_mass": mean(float(probe.get("visual_attention_mass") or 0.0) for probe in probes),
        "avg_nonvisual_attention_mass": mean(float(probe.get("nonvisual_attention_mass") or 0.0) for probe in probes),
        "avg_text_mapping_coverage": mean(float(probe.get("text_mapping_coverage") or 0.0) for probe in probes),
        "avg_dashboard_header_attention_mass": mean(header) if header else None,
        "first_patch_attention_argmax_rate": mean(attention_first) if attention_first else None,
        "first_patch_weighted_value_argmax_rate": mean(contribution_first) if contribution_first else None,
        "prefill_region_density_lift": {
            region: mean(prefill_density[region]) if prefill_density[region] else None for region in REGIONS
        },
        "generation_region_density_lift": {
            region: mean(generation_density[region]) if generation_density[region] else None for region in REGIONS
        },
        "text_region_normalized_focus": {
            label: mean(values) for label, values in sorted(text_focus.items())
        },
        "generation_text_region_normalized_focus": {
            label: mean(values) for label, values in sorted(generation_text_focus.items())
        },
        "generation_target_attention_rate": mean(float(
            (probe.get("generation_target_attention") or {}).get("status") == "collected"
        ) for probe in probes),
    }


def _group_means(
    records: Sequence[Mapping[str, Any]], *, by_fault: bool = False,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        key = (str(row.get("model")), str(row.get("arm")), str(row.get("analysis_dataset")))
        if by_fault:
            key = (*key, str(row.get("analysis_fault_type") or "unknown"))
        grouped[key].append(row)
    output = []
    for key, values in sorted(grouped.items()):
        model, arm, dataset, *fault = key
        completed = [row for row in values if row.get("status") == "completed"]
        eligible = [row for row in values if row.get("status") != "protocol_ineligible"]
        scores = [row.get("score") or {} for row in completed]
        calls = [call for row in completed for call in _calls(row)]
        case_tokens = [
            {
                name: sum(int(call.get(name) or 0) for call in _calls(row))
                for name in ("input_tokens", "output_tokens", "total_tokens")
            }
            for row in completed
        ]
        traces = [row.get("reasoning_trace") or {} for row in completed if row.get("reasoning_trace")]
        metric_names = sorted({key for score in scores for key, value in score.items() if isinstance(value, (int, float))})
        metric_means = {
            name: mean(
                float(score[name])
                for score in scores
                if isinstance(score.get(name), (int, float))
            )
            for name in metric_names
        }
        summary = {
            "model": model, "arm": arm, "dataset": dataset,
            "records": len(values), "completed": len(completed),
            "protocol_ineligible": len(values) - len(eligible),
            "error_rate": 1.0 - len(completed) / len(eligible) if eligible else 0.0,
            "model_output_valid_rate": mean(float(row.get("model_output_valid", True)) for row in completed) if completed else None,
            **metric_means,
            "avg_input_tokens": mean(int(call.get("input_tokens") or 0) for call in calls) if calls else None,
            "avg_output_tokens": mean(int(call.get("output_tokens") or 0) for call in calls) if calls else None,
            "avg_total_tokens": mean(int(call.get("total_tokens") or 0) for call in calls) if calls else None,
            "avg_case_input_tokens": mean(row["input_tokens"] for row in case_tokens) if case_tokens else None,
            "avg_case_output_tokens": mean(row["output_tokens"] for row in case_tokens) if case_tokens else None,
            "avg_case_total_tokens": mean(row["total_tokens"] for row in case_tokens) if case_tokens else None,
            "avg_model_calls_per_case": mean(int(row.get("model_calls") or 0) for row in completed) if completed else None,
            "avg_facts_per_input_token": mean(
                float(row.get("fact_count") or 0) / max(1, token["input_tokens"])
                for row, token in zip(completed, case_tokens, strict=True)
            ) if case_tokens else None,
            "avg_grounded_typed_claim_precision": mean(
                float(trace["grounded_typed_claim_precision"])
                for trace in traces if trace.get("grounded_typed_claim_precision") is not None
            ) if any(trace.get("grounded_typed_claim_precision") is not None for trace in traces) else None,
            "root_evidence_citation_rate": mean(
                float(trace.get("root_evidence_cited", False)) for trace in traces
            ) if traces else None,
            "avg_unsupported_typed_claims": mean(
                len(trace.get("unsupported_typed_claims") or ()) for trace in traces
            ) if traces else None,
            "truncation_rate": mean(float(bool(call.get("truncated"))) for call in calls) if calls else None,
            **summarize_call_performance(calls),
            **_attention_means(calls),
        }
        if fault:
            summary["fault_type"] = fault[0]
        output.append(summary)
    return output


def _comparisons(records: Sequence[Mapping[str, Any]], config: Mapping[str, Any], metric: str) -> dict[str, Any]:
    index = {
        (str(row.get("model")), str(row.get("opaque_incident_id")), str(row.get("arm"))): {
            "score": float((row.get("score") or {}).get(metric, 0.0)),
            "dataset": str(row.get("analysis_dataset")),
            "row": row,
        }
        for row in records if row.get("status") == "completed" and metric in (row.get("score") or {})
    }
    output: dict[str, Any] = {}
    arms = set(key[2] for key in index)
    if metric == "mrr":
        primary = [tuple(pair) for pair in config["analysis"]["primary_rca_comparisons"]]
        negative = [
            tuple(config["analysis"]["negative_control_comparison"]),
            tuple(config["analysis"]["hybrid_control_comparison"]),
            *map(tuple, config["analysis"]["compact_text_comparisons"]),
        ]
    else:
        primary = [
            (f"L{level}_PATHV", f"L{level}_T") for level in (1, 2, 3)
        ] + [
            (f"L{level}_CONTEXTV", f"L{level}_T") for level in (1, 2, 3)
        ] + [
            (f"L{level}_V", f"L{level}_PATHV") for level in (1, 2, 3)
        ] + [(f"L{level}_T", "L1_T") for level in (2, 3, 4)]
        negative = [(f"L{level}_S", f"L{level}_T") for level in (1, 2, 3, 4)]
    datasets = sorted({value["dataset"] for value in index.values()})
    scopes = ["headline", *datasets]
    headline = set(map(str, config["data"]["headline_datasets"]))
    for model in sorted(set(key[0] for key in index)):
        for scope in scopes:
            family = {}
            for left, right in (*primary, *negative):
                if left not in arms or right not in arms:
                    continue
                left_cases = {
                    key[1] for key, value in index.items()
                    if key[0] == model and key[2] == left
                    and (value["dataset"] in headline if scope == "headline" else value["dataset"] == scope)
                }
                right_cases = {
                    key[1] for key, value in index.items()
                    if key[0] == model and key[2] == right
                    and (value["dataset"] in headline if scope == "headline" else value["dataset"] == scope)
                }
                cases = sorted(left_cases & right_cases)
                name = f"{model}:{scope}:{left}-{right}"
                output[name] = _paired_statistics([
                    index[(model, case, left)]["score"] - index[(model, case, right)]["score"]
                    for case in cases
                ])
                if metric == "mrr" and cases:
                    pairs = [
                        (index[(model, case, left)]["row"], index[(model, case, right)]["row"])
                        for case in cases
                    ]
                    left_top1 = [float((left_row.get("score") or {}).get("ac@1", 0.0)) for left_row, _ in pairs]
                    right_top1 = [float((right_row.get("score") or {}).get("ac@1", 0.0)) for _, right_row in pairs]
                    ranks = [(_ranking(left_row), _ranking(right_row)) for left_row, right_row in pairs]
                    output[name].update({
                        "repair_rate_at_1": mean(float(a == 1 and b == 0) for a, b in zip(left_top1, right_top1, strict=True)),
                        "break_rate_at_1": mean(float(a == 0 and b == 1) for a, b in zip(left_top1, right_top1, strict=True)),
                        "top1_flip_rate": mean(float((a[:1] != b[:1])) for a, b in ranks),
                        "top5_jaccard": mean(
                            len(set(a[:5]) & set(b[:5])) / max(1, len(set(a[:5]) | set(b[:5]))) for a, b in ranks
                        ),
                        "top5_rbo": mean(_rbo5(a, b) for a, b in ranks),
                    })
                if (left, right) in primary:
                    family[name] = output[name]
            adjusted = _holm(family)
            for name, value in adjusted.items():
                output[name]["holm_adjusted_p"] = value
            for left, right in negative:
                name = f"{model}:{scope}:{left}-{right}"
                if name in output:
                    output[name]["holm_adjusted_p"] = output[name].get("wilcoxon_p")
    return output


def _tool_summary(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        for stage in row.get("stages", ()):
            observation = stage.get("tool_observation")
            if observation:
                grouped[(str(row.get("model")), str(row.get("arm")), str(observation.get("tool")))].append(observation)
    return [{
        "model": key[0], "arm": key[1], "tool": key[2], "calls": len(values),
        "valid_rate": mean(float(row.get("status") == "ok") for row in values),
        "empty_result_rate": mean(float(int(row.get("returned_rows") or 0) == 0) for row in values),
        "avg_matched_rows": mean(int(row.get("matched_rows") or 0) for row in values),
        "avg_returned_rows": mean(int(row.get("returned_rows") or 0) for row in values),
    } for key, values in sorted(grouped.items())]


def _case_token_total(row: Mapping[str, Any]) -> int:
    return sum(int(call.get("total_tokens") or 0) for call in _calls(row))


def _case_input_tokens(row: Mapping[str, Any]) -> int:
    return sum(int(call.get("input_tokens") or 0) for call in _calls(row))


def _token_efficiency(records: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> list[dict[str, Any]]:
    complete = {
        (str(row.get("model")), str(row.get("opaque_incident_id")), str(row.get("arm"))): row
        for row in records if row.get("status") == "completed" and "mrr" in (row.get("score") or {})
    }
    headline = set(map(str, config["data"]["headline_datasets"]))
    output = []
    for model in sorted({key[0] for key in complete}):
        arms = sorted({key[2] for key in complete if key[0] == model and key[2] != "T"})
        for arm in arms:
            cases = sorted({
                key[1] for key, row in complete.items()
                if key[0] == model and key[2] == arm and str(row.get("analysis_dataset")) in headline
                and (model, key[1], "T") in complete
            })
            if not cases:
                continue
            arm_rows = [complete[(model, case, arm)] for case in cases]
            text_rows = [complete[(model, case, "T")] for case in cases]
            token_delta = [_case_input_tokens(a) - _case_input_tokens(t) for a, t in zip(arm_rows, text_rows, strict=True)]
            rr_delta = [
                float((a.get("score") or {})["mrr"]) - float((t.get("score") or {})["mrr"])
                for a, t in zip(arm_rows, text_rows, strict=True)
            ]
            mean_token_delta, mean_rr_delta = mean(token_delta), mean(rr_delta)
            if mean_token_delta < 0 and mean_rr_delta >= 0:
                category = "pareto_improvement"
            elif mean_token_delta < 0 and mean_rr_delta > -0.05:
                category = "accuracy_preserving_compression"
            elif mean_token_delta < 0 and mean_rr_delta <= -0.05:
                category = "harmful_compression"
            elif mean_rr_delta >= 0.05:
                category = "accuracy_gain_without_compression"
            else:
                category = "no_registered_efficiency_gain"
            output.append({
                "model": model, "arm": arm, "n": len(cases),
                "paired_input_token_delta": _paired_statistics(token_delta),
                "paired_mrr_delta": _paired_statistics(rr_delta),
                "mean_input_token_ratio_to_text": mean(
                    _case_input_tokens(a) / max(1, _case_input_tokens(t))
                    for a, t in zip(arm_rows, text_rows, strict=True)
                ),
                "mrr_per_1000_input_tokens": mean(
                    float((row.get("score") or {})["mrr"]) * 1000 / max(1, _case_input_tokens(row))
                    for row in arm_rows
                ),
                "input_tokens_per_accumulated_rr": (
                    sum(_case_input_tokens(row) for row in arm_rows)
                    / sum(float((row.get("score") or {})["mrr"]) for row in arm_rows)
                    if sum(float((row.get("score") or {})["mrr"]) for row in arm_rows) else None
                ),
                "classification": category,
            })
    return output


def _qa_path_summary(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, int, int, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        if row.get("status") != "completed" or not row.get("question"):
            continue
        question = row["question"]
        path = "->".join(map(str, question["region_path"]))
        grouped[(
            str(row.get("model")), str(row.get("qa_condition")), path,
            int(question["perception_difficulty"]), int(question["reasoning_difficulty"]),
            str(question["reasoning_family"]),
        )].append(row)
    output = []
    for key, values in sorted(grouped.items()):
        correct = sum(float((row.get("score") or {}).get("complete_chain_accuracy", 0.0)) for row in values)
        output.append({
            "model": key[0], "condition": key[1], "path": key[2],
            "perception_difficulty": key[3], "reasoning_difficulty": key[4],
            "reasoning_family": key[5], "n": len(values),
            "complete_chain_accuracy": correct / len(values),
            "step_accuracy": mean(float((row.get("score") or {}).get("step_accuracy", 0.0)) for row in values),
            "correct_prefix_accuracy": mean(float((row.get("score") or {}).get("correct_prefix_accuracy", 0.0)) for row in values),
            "model_output_error_rate": mean(float(not row.get("model_output_valid", True)) for row in values),
            "unsupported_value_rate": mean(float((row.get("qa_value_support") or {}).get("unsupported_value_rate", 0.0)) for row in values),
            "input_tokens_per_correct_chain": (
                sum(_case_input_tokens(row) for row in values) / correct if correct else None
            ),
        })
    return output


def analyze_direct_multi(
    direct: Sequence[Mapping[str, Any]], multi: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Paired secondary analysis of multi-stage versus direct RCA.

    This comparison is intentionally separate from either experiment's
    primary visual-versus-text family.  Pairing is by model, opaque case and
    representation arm; repair/break use AC@1 while the paired effect uses MRR.
    """

    def index(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str, str], Mapping[str, Any]]:
        return {
            (str(row.get("model")), str(row.get("opaque_incident_id")), str(row.get("arm"))): row
            for row in rows
            if row.get("status") == "completed" and "mrr" in (row.get("score") or {})
        }

    direct_index, multi_index = index(direct), index(multi)
    common = set(direct_index) & set(multi_index)
    headline = set(map(str, config["data"]["headline_datasets"]))
    datasets = sorted({
        str(direct_index[key].get("analysis_dataset")) for key in common
    })
    rows: list[dict[str, Any]] = []
    for model in sorted({key[0] for key in common}):
        for scope in ("headline", *datasets):
            family: dict[str, dict[str, Any]] = {}
            for arm in config["experiments"]["direct_rca"]["arms"]:
                keys = sorted(
                    key for key in common
                    if key[0] == model and key[2] == arm
                    and (
                        str(direct_index[key].get("analysis_dataset")) in headline
                        if scope == "headline"
                        else str(direct_index[key].get("analysis_dataset")) == scope
                    )
                )
                if not keys:
                    continue
                direct_mrr = [float((direct_index[key].get("score") or {})["mrr"]) for key in keys]
                multi_mrr = [float((multi_index[key].get("score") or {})["mrr"]) for key in keys]
                stats = _paired_statistics([right - left for left, right in zip(direct_mrr, multi_mrr, strict=True)])
                direct_top1 = [float((direct_index[key].get("score") or {}).get("ac@1", 0.0)) for key in keys]
                multi_top1 = [float((multi_index[key].get("score") or {}).get("ac@1", 0.0)) for key in keys]
                direct_tokens = [_case_token_total(direct_index[key]) for key in keys]
                multi_tokens = [_case_token_total(multi_index[key]) for key in keys]
                name = f"{model}:{scope}:{arm}:multi-direct"
                row = {
                    "comparison": name, "model": model, "scope": scope, "arm": arm,
                    **stats,
                    "direct_mrr": mean(direct_mrr), "multi_stage_mrr": mean(multi_mrr),
                    "repair_rate_at_1": mean(float(left == 0 and right == 1) for left, right in zip(direct_top1, multi_top1, strict=True)),
                    "break_rate_at_1": mean(float(left == 1 and right == 0) for left, right in zip(direct_top1, multi_top1, strict=True)),
                    "direct_avg_case_tokens": mean(direct_tokens),
                    "multi_stage_avg_case_tokens": mean(multi_tokens),
                    "token_cost_ratio": (
                        mean(multi_tokens) / mean(direct_tokens) if mean(direct_tokens) else None
                    ),
                }
                rows.append(row)
                family[name] = row
            adjusted = _holm(family)
            for row in rows:
                if row["comparison"] in adjusted:
                    row["holm_adjusted_p"] = adjusted[row["comparison"]]
    result = {
        "schema_version": "RQ1_1CrossExperimentAnalysisV1",
        "pairing_key": ["model", "opaque_incident_id", "arm"],
        "metric": "multi_stage_mrr_minus_direct_mrr",
        "repair_break_metric": "ac@1",
        "paired_records": len(common),
        "direct_completed_records": len(direct_index),
        "multi_stage_completed_records": len(multi_index),
        "rows": rows,
    }
    result["analysis_sha256"] = stable_hash(result)
    return result


def _case_metric(row: Mapping[str, Any], metric: str) -> float | None:
    if metric == "infrastructure_error":
        return float(row.get("status") != "completed")
    if row.get("status") != "completed":
        return None
    if metric == "mrr":
        return float((row.get("score") or {}).get("mrr", 0.0))
    if metric == "input_tokens":
        return float(sum(int(call.get("input_tokens") or 0) for call in _calls(row)))
    raise KeyError(metric)


def analyze_factorial_rca(
    records: Sequence[Mapping[str, Any]], config: Mapping[str, Any],
) -> dict[str, Any]:
    """Four-region conditional effects, interactions, and Shapley values."""

    arm_for = {frozenset(regions): arm for arm, regions in FACTORIAL_ARM_REGIONS.items()}
    index = {
        (str(row.get("model")), str(row.get("opaque_incident_id")), str(row.get("arm"))): row
        for row in records if str(row.get("arm")) in FACTORIAL_ARM_REGIONS
    }
    headline = set(map(str, config["data"]["headline_datasets"]))
    per_case: list[dict[str, Any]] = []
    for model, case in sorted({(key[0], key[1]) for key in index}):
        rows = {arm: index.get((model, case, arm)) for arm in FACTORIAL_ARM_REGIONS}
        if any(row is None for row in rows.values()):
            continue
        dataset = str(next(iter(rows.values())).get("analysis_dataset"))
        for metric in ("mrr", "input_tokens", "infrastructure_error"):
            values = {frozenset(FACTORIAL_ARM_REGIONS[arm]): _case_metric(row, metric) for arm, row in rows.items()}
            if any(value is None for value in values.values()):
                continue
            numeric = {key: float(value) for key, value in values.items()}
            main = {}
            shapley = {}
            for region in REGIONS:
                others = tuple(value for value in REGIONS if value != region)
                deltas = []
                phi = 0.0
                for size in range(len(others) + 1):
                    for subset in itertools.combinations(others, size):
                        base = frozenset(subset)
                        delta = numeric[base | {region}] - numeric[base]
                        deltas.append(delta)
                        coefficient = math.factorial(size) * math.factorial(3 - size) / math.factorial(4)
                        phi += coefficient * delta
                main[region] = mean(deltas)
                shapley[region] = phi
            interactions = {}
            for left, right in itertools.combinations(REGIONS, 2):
                remaining = tuple(value for value in REGIONS if value not in {left, right})
                values_ij = []
                for size in range(len(remaining) + 1):
                    for subset in itertools.combinations(remaining, size):
                        base = frozenset(subset)
                        values_ij.append(
                            numeric[base | {left, right}] - numeric[base | {left}]
                            - numeric[base | {right}] + numeric[base]
                        )
                interactions[f"{left}:{right}"] = mean(values_ij)
            per_case.append({
                "model": model, "opaque_incident_id": case, "dataset": dataset,
                "metric": metric, "conditional_main_effect": main,
                "shapley_contribution": shapley, "second_order_interaction": interactions,
                "all_visual_minus_text": numeric[frozenset(REGIONS)] - numeric[frozenset()],
            })
    summaries = []
    datasets = sorted({row["dataset"] for row in per_case})
    for model in sorted({row["model"] for row in per_case}):
        for scope in ("headline", *datasets):
            for metric in ("mrr", "input_tokens", "infrastructure_error"):
                selected = [
                    row for row in per_case if row["model"] == model and row["metric"] == metric
                    and (row["dataset"] in headline if scope == "headline" else row["dataset"] == scope)
                ]
                if not selected:
                    continue
                main_rows = {
                    region: _paired_statistics([row["conditional_main_effect"][region] for row in selected])
                    for region in REGIONS
                }
                adjusted = _holm(main_rows) if metric == "mrr" else {region: None for region in REGIONS}
                summaries.append({
                    "model": model, "scope": scope, "metric": metric, "n": len(selected),
                    "conditional_main_effect": {
                        region: {**main_rows[region], "holm_adjusted_p": adjusted[region]}
                        for region in REGIONS
                    },
                    "mean_shapley_contribution": {
                        region: mean(row["shapley_contribution"][region] for row in selected) for region in REGIONS
                    },
                    "second_order_interaction": {
                        pair: _paired_statistics([row["second_order_interaction"][pair] for row in selected])
                        for pair in selected[0]["second_order_interaction"]
                    },
                    "all_visual_minus_text": _paired_statistics([
                        row["all_visual_minus_text"] for row in selected
                    ]),
                })
    result = {
        "schema_version": "RQ1_1FactorialRCAAnalysisV1",
        "region_order": list(REGIONS), "factorial_cells": FACTORIAL_ARM_REGIONS,
        "per_case": per_case, "summaries": summaries,
    }
    result["analysis_sha256"] = stable_hash(result)
    return result


def _spearman(left: Sequence[float], right: Sequence[float]) -> dict[str, Any]:
    if len(left) < 3 or len(set(left)) < 2 or len(set(right)) < 2:
        return {"n": len(left), "rho": None, "p": None}
    try:
        from scipy.stats import spearmanr
        value = spearmanr(left, right)
        return {"n": len(left), "rho": float(value.statistic), "p": float(value.pvalue)}
    except ImportError:
        return {"n": len(left), "rho": None, "p": None}


def _qa_attention_density(row: Mapping[str, Any]) -> tuple[float | None, float | None]:
    selected = set(map(str, row.get("visual_regions") or ()))
    relevant = set(map(str, (row.get("question") or {}).get("region_path") or ()))
    required, irrelevant = [], []
    for call in _calls(row):
        for artifact in ((call.get("attention_probe") or {}).get("image_artifacts") or ()):
            density = (artifact.get("diagnostics") or {}).get("region_density_lift") or {}
            required.extend(float(value) for region, value in density.items() if region in selected & relevant and value is not None)
            irrelevant.extend(float(value) for region, value in density.items() if region in selected - relevant and value is not None)
    return (mean(required) if required else None, mean(irrelevant) if irrelevant else None)


def analyze_perception_rca(
    rca_records: Sequence[Mapping[str, Any]], qa_records: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Join matched perception and one-stage RCA without claiming mediation."""

    qa_complete = [row for row in qa_records if row.get("status") == "completed"]
    t_by_level = {
        (str(row["model"]), str(row["opaque_incident_id"]), int((row.get("question") or {})["perception_difficulty"])): row
        for row in qa_complete if row.get("qa_condition") == "T"
    }
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in qa_complete:
        grouped[(str(row["model"]), str(row["opaque_incident_id"]), str(row["mapped_rca_arm"]))].append(row)
    rca_index = {
        (str(row["model"]), str(row["opaque_incident_id"]), str(row["arm"])): row
        for row in rca_records if row.get("status") == "completed"
    }
    profiles = []
    for key, rows in sorted(grouped.items()):
        rca = rca_index.get(key)
        if rca is None:
            continue
        levels: dict[int, float] = {}
        reasoning: dict[int, list[float]] = defaultdict(list)
        region_steps: dict[str, list[float]] = defaultdict(list)
        baseline = []
        required_density, irrelevant_density = [], []
        for row in rows:
            level = int((row.get("question") or {})["perception_difficulty"])
            score = row.get("score") or {}
            levels[level] = mean([levels[level], float(score["complete_chain_accuracy"])]) if level in levels else float(score["complete_chain_accuracy"])
            reasoning[int((row.get("question") or {})["reasoning_difficulty"])].append(float(score["complete_chain_accuracy"]))
            for region, value in zip((row.get("question") or {}).get("region_path") or (), score.get("step_scores") or (), strict=True):
                region_steps[str(region)].append(float(value))
            t_row = t_by_level.get((key[0], key[1], level))
            if t_row is not None:
                baseline.append(float((t_row.get("score") or {})["complete_chain_accuracy"])
                                )
            req, irr = _qa_attention_density(row)
            if req is not None:
                required_density.append(req)
            if irr is not None:
                irrelevant_density.append(irr)
        perception = mean(levels.values())
        baseline_perception = mean(baseline) if baseline else None
        rr = float((rca.get("score") or {}).get("mrr", 0.0))
        t_rca = rca_index.get((key[0], key[1], "T"))
        t_rr = float((t_rca.get("score") or {}).get("mrr", 0.0)) if t_rca else None
        p_delta = perception - baseline_perception if baseline_perception is not None else None
        r_delta = rr - t_rr if t_rr is not None else None
        quadrant = None
        if p_delta is not None and r_delta is not None:
            quadrant = ("perception_improved" if p_delta > 0 else "perception_degraded" if p_delta < 0 else "perception_tied")
            quadrant += "/" + ("rca_improved" if r_delta > 0 else "rca_degraded" if r_delta < 0 else "rca_tied")
        profiles.append({
            "schema_version": "PerceptionProfileV1", "model": key[0],
            "opaque_incident_id": key[1], "representation": key[2],
            "dataset": str(rca.get("analysis_dataset")),
            "perception_aggregate": perception,
            "text_baseline_perception": baseline_perception,
            **{f"l{level}_complete_chain": levels.get(level) for level in range(1, 5)},
            "complete_chain_by_reasoning_difficulty": {
                f"R{level}": mean(reasoning[level]) if reasoning[level] else None for level in range(1, 4)
            },
            "step_accuracy_by_region": {
                region: mean(region_steps[region]) if region_steps[region] else None for region in REGIONS
            },
            "prefix_length_proxy": sum(
                float((row.get("score") or {}).get("correct_prefix_accuracy", 0.0)) for row in rows
            ) / len(rows),
            "required_region_attention_density_lift": mean(required_density) if required_density else None,
            "irrelevant_region_attention_density_lift": mean(irrelevant_density) if irrelevant_density else None,
            "qa_model_output_error_rate": mean(float(not row.get("model_output_valid", True)) for row in rows),
            "qa_input_tokens": sum(sum(int(call.get("input_tokens") or 0) for call in _calls(row)) for row in rows),
            "reciprocal_rank": rr, "rca_top1": float((rca.get("score") or {}).get("ac@1", 0.0)),
            "perception_delta_vs_level_matched_text": p_delta,
            "rr_delta_vs_text": r_delta, "quadrant": quadrant,
            "reasoning_trace": rca.get("reasoning_trace"),
        })
    headline = set(map(str, config["data"]["headline_datasets"]))
    relations = []
    datasets = sorted({row["dataset"] for row in profiles})
    for model in sorted({row["model"] for row in profiles}):
        for scope in ("headline", *datasets):
            scoped = [
                row for row in profiles if row["model"] == model
                and (row["dataset"] in headline if scope == "headline" else row["dataset"] == scope)
            ]
            for representation in sorted({row["representation"] for row in scoped}):
                selected = [row for row in scoped if row["representation"] == representation]
                changed = [row for row in selected if row["perception_delta_vs_level_matched_text"] is not None and row["rr_delta_vs_text"] is not None]
                correct = [row for row in selected if row["perception_aggregate"] == 1.0]
                incorrect = [row for row in selected if row["perception_aggregate"] < 1.0]
                attention = [row for row in selected if row["required_region_attention_density_lift"] is not None]
                level_relations = {}
                for level in range(1, 5):
                    field = f"l{level}_complete_chain"
                    values = [row for row in selected if row[field] is not None]
                    level_relations[f"L{level}"] = _spearman(
                        [row[field] for row in values], [row["reciprocal_rank"] for row in values]
                    )
                region_relations = {}
                for region in REGIONS:
                    values = [row for row in selected if row["step_accuracy_by_region"][region] is not None]
                    region_relations[region] = _spearman(
                        [row["step_accuracy_by_region"][region] for row in values],
                        [row["reciprocal_rank"] for row in values],
                    )
                subsets = {
                    "all": selected,
                    "text_non_saturated": [row for row in selected if row["text_baseline_perception"] is not None and row["text_baseline_perception"] < 1.0],
                    "perception_changed": [row for row in selected if row["perception_delta_vs_level_matched_text"] not in (None, 0.0)],
                    "rca_changed": [row for row in selected if row["rr_delta_vs_text"] not in (None, 0.0)],
                }
                relations.append({
                    "model": model, "scope": scope, "representation": representation,
                    "perception_vs_rr": _spearman(
                        [row["perception_aggregate"] for row in selected],
                        [row["reciprocal_rank"] for row in selected],
                    ),
                    "change_score": _spearman(
                        [row["perception_delta_vs_level_matched_text"] for row in changed],
                        [row["rr_delta_vs_text"] for row in changed],
                    ),
                    "level_vs_rr": level_relations,
                    "region_step_vs_rr": region_relations,
                    "required_attention_vs_perception": _spearman(
                        [row["required_region_attention_density_lift"] for row in attention],
                        [row["perception_aggregate"] for row in attention],
                    ),
                    "required_attention_vs_rr": _spearman(
                        [row["required_region_attention_density_lift"] for row in attention],
                        [row["reciprocal_rank"] for row in attention],
                    ),
                    "p_rca_top1_given_qa_correct": mean(row["rca_top1"] for row in correct) if correct else None,
                    "p_rca_top1_given_qa_incorrect": mean(row["rca_top1"] for row in incorrect) if incorrect else None,
                    "quadrant_counts": dict(Counter(row["quadrant"] for row in changed)),
                    "registered_subset_sizes": {name: len(values) for name, values in subsets.items()},
                })
    representative = []
    for quadrant in sorted({row["quadrant"] for row in profiles if row["quadrant"]}):
        candidates = sorted(
            (row for row in profiles if row["quadrant"] == quadrant),
            key=lambda row: (-(abs(row["perception_delta_vs_level_matched_text"]) + abs(row["rr_delta_vs_text"])), row["opaque_incident_id"]),
        )[:3]
        representative.extend(candidates)
    result = {
        "schema_version": "RQ1_1PerceptionRCAJointAnalysisV1",
        "interpretation": "paired_association_and_representation_intervention_not_hidden_cot_or_causal_mediation",
        "profiles": profiles, "relations": relations,
        "reasoning_trace_representatives": representative,
    }
    result["analysis_sha256"] = stable_hash(result)
    return result


def analyze_records(records: Sequence[Mapping[str, Any]], spec: Any, config: Mapping[str, Any]) -> dict[str, Any]:
    ineligible = [row for row in records if row.get("status") == "protocol_ineligible"]
    errors = [row for row in records if row.get("status") not in {"completed", "protocol_ineligible"}]
    model_output_errors = [
        row for row in records
        if row.get("status") == "completed" and not row.get("model_output_valid", True)
    ]
    timeout_errors = [row for row in errors if "timeout" in str(row.get("error")).casefold()]
    token_errors = [row for row in errors if "context" in str(row.get("error")).casefold() or "token" in str(row.get("error")).casefold()]
    persistence_errors = [
        row for row in errors
        if any(term in str(row.get("error")).casefold() for term in ("persist", "write", "hash", "file"))
    ]
    vllm_errors = [
        row for row in errors
        if any(term in str(row.get("error")).casefold() for term in ("vllm", "http", "connection", "server"))
    ]
    metric = "mrr" if spec.primary_metric == "mrr" else "complete_chain_accuracy"
    complete = [row for row in records if row.get("status") == "completed"]
    result = {
        "schema_version": "RQ1_1AnalysisV1", "experiment": spec.name,
        "records": len(records), "completed": len(complete), "protocol_ineligible": len(ineligible),
        "infrastructure_errors": len(errors),
        "model_output_errors": len(model_output_errors),
        "whole_record_error_rate": len(errors) / (len(records) - len(ineligible)) if len(records) > len(ineligible) else 0.0,
        "error_classes": {
            "vllm_or_transport": len(vllm_errors), "timeout": len(timeout_errors),
            "token_or_context": len(token_errors), "persistence_or_integrity": len(persistence_errors),
            "model_parse_or_schema": len(model_output_errors),
            "other_infrastructure": len(errors) - len(set(map(id, vllm_errors + timeout_errors + token_errors + persistence_errors))),
        },
        "performance_cost_runtime": _group_means(records),
        "per_fault_breakdown": _group_means(records, by_fault=True),
        "tool_usage": _tool_summary(records),
        "paired_comparisons": _comparisons(records, config, metric),
        "token_efficiency": _token_efficiency(records, config) if spec.task == "direct_rca" else [],
        "qa_path_breakdown": _qa_path_summary(records) if spec.task == "direct_qa" else [],
        "parse_rate": (
            (len(complete) - len(model_output_errors)) / len(complete) if complete else 0.0
        ),
    }
    result["eligible_for_claim"] = (
        result["whole_record_error_rate"] <= float(config["runtime"]["whole_case_infrastructure_exclusion_maximum"])
        and result["parse_rate"] >= float(config["runtime"]["parse_rate_minimum"])
    )
    if spec.task == "direct_rca":
        result["factorial_analysis"] = analyze_factorial_rca(records, config)
    if spec.task == "counterfactual_rca":
        result["counterfactual_analysis"] = _counterfactual_analysis(records, config)
    result["analysis_sha256"] = stable_hash(result)
    return result


def verify_result_root(paths: RunPaths, config: Mapping[str, Any], prepared_paths: RunPaths) -> dict[str, Any]:
    errors: list[str] = []
    index_path = prepared_paths.prepared / "index.json"
    if not index_path.is_file():
        errors.append("missing_prepared_index")
        return {"passed": False, "errors": errors}
    index = json.loads(index_path.read_text())
    unsigned = dict(index); recorded = unsigned.pop("index_sha256", None)
    if stable_hash(unsigned) != recorded:
        errors.append("prepared_index_hash_mismatch")
    for item in index.get("cases", ()):
        for key, hash_key in (("public", "public_sha256"), ("private", "private_sha256"), ("full_image", "full_image_sha256")):
            path = prepared_paths.root / item[key]
            if not path.is_file():
                errors.append(f"missing:{item['opaque_incident_id']}:{key}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != item[hash_key]:
                errors.append(f"hash:{item['opaque_incident_id']}:{key}")
        for arm, relative in item.get("counterfactual_images", {}).items():
            path = prepared_paths.root / relative
            expected = (item.get("counterfactual_image_sha256") or {}).get(arm)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                errors.append(f"counterfactual_hash:{item['opaque_incident_id']}:{arm}")
    trajectory_count = 0
    for path in paths.trajectories.glob("*/*/*.json"):
        trajectory_count += 1
        try:
            row = json.loads(path.read_text())
            recorded_hash = row.pop("record_sha256", None)
            if stable_hash(row) != recorded_hash:
                errors.append(f"trajectory_hash:{path.relative_to(paths.root)}")
            if not path.with_suffix(".md").is_file():
                errors.append(f"missing_conversation:{path.relative_to(paths.root)}")
            if row.get("status") == "completed":
                for call_index, call in enumerate(_calls(row), 1):
                    probe = call.get("attention_probe") or {}
                    prefix = f"attention:{path.relative_to(paths.root)}:{call_index}"
                    if (
                        probe.get("status") != "collected_same_prefill"
                        or probe.get("same_prefill") is not True
                        or int(probe.get("extra_model_calls", -1)) != 0
                    ):
                        errors.append(f"{prefix}:contract")
                        continue
                    visual = float(probe.get("visual_attention_mass", -1.0))
                    nonvisual = float(probe.get("nonvisual_attention_mass", -1.0))
                    if not math.isclose(visual + nonvisual, 1.0, rel_tol=0.0, abs_tol=1e-4):
                        errors.append(f"{prefix}:mass")
                    expected_images = sum(part.get("type") == "image" for part in call.get("parts", ()))
                    image_artifacts = list(probe.get("image_artifacts") or ())
                    if len(image_artifacts) != expected_images:
                        errors.append(f"{prefix}:image_count")
                    generation = probe.get("generation_target_attention") or {}
                    if (
                        generation.get("status") != "collected"
                        or int(generation.get("target_token_count") or 0) < 1
                    ) and _has_registered_generation_target(call):
                        errors.append(f"{prefix}:generation_target_attention")
                    elif generation.get("status") == "collected":
                        relative = generation.get("text_attention_path")
                        target = paths.root / str(relative or "__missing__")
                        if not relative or not target.is_file():
                            errors.append(f"{prefix}:missing_generation_text")
                        elif stable_hash(json.loads(target.read_text())) != generation.get("text_attention_sha256"):
                            errors.append(f"{prefix}:hash_generation_text")
                        if len(generation.get("image_artifacts") or ()) != expected_images:
                            errors.append(f"{prefix}:generation_image_count")
                    for key in ("raw_probe", "text_attention"):
                        relative = probe.get(f"{key}_path")
                        target = paths.root / str(relative or "__missing__")
                        if not relative or not target.is_file():
                            errors.append(f"{prefix}:missing_{key}")
                        else:
                            payload = json.loads(target.read_text())
                            if stable_hash(payload) != probe.get(f"{key}_sha256"):
                                errors.append(f"{prefix}:hash_{key}")
                    for artifact_index, artifact in enumerate(image_artifacts):
                        if any(
                            not isinstance(artifact.get(key), Mapping)
                            for key in (
                                "attention_peak_diagnostics",
                                "value_norm_peak_diagnostics",
                                "weighted_value_peak_diagnostics",
                            )
                        ):
                            errors.append(f"{prefix}:image{artifact_index}:missing_value_diagnostics")
                        for key in ("grid", "overlay"):
                            relative = artifact.get(f"{key}_path")
                            target = paths.root / str(relative or "__missing__")
                            if not relative or not target.is_file():
                                errors.append(f"{prefix}:image{artifact_index}:missing_{key}")
                            elif key == "grid":
                                if stable_hash(json.loads(target.read_text())) != artifact.get("grid_sha256"):
                                    errors.append(f"{prefix}:image{artifact_index}:hash_grid")
                            elif hashlib.sha256(target.read_bytes()).hexdigest() != artifact.get("overlay_sha256"):
                                errors.append(f"{prefix}:image{artifact_index}:hash_overlay")
                    for artifact_index, artifact in enumerate(generation.get("image_artifacts") or ()):
                        for key in ("grid", "overlay"):
                            relative = artifact.get(f"{key}_path")
                            target = paths.root / str(relative or "__missing__")
                            if not relative or not target.is_file():
                                errors.append(f"{prefix}:generation_image{artifact_index}:missing_{key}")
                            elif key == "grid" and stable_hash(json.loads(target.read_text())) != artifact.get("grid_sha256"):
                                errors.append(f"{prefix}:generation_image{artifact_index}:hash_grid")
                            elif key == "overlay" and hashlib.sha256(target.read_bytes()).hexdigest() != artifact.get("overlay_sha256"):
                                errors.append(f"{prefix}:generation_image{artifact_index}:hash_overlay")
        except json.JSONDecodeError:
            errors.append(f"invalid_json:{path.relative_to(paths.root)}")
    return {
        "schema_version": "RQ1_1VerificationV1", "passed": not errors,
        "errors": errors[:100], "error_count": len(errors),
        "prepared_cases": len(index.get("cases", ())), "trajectory_records": trajectory_count,
    }

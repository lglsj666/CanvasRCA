"""RQ1.1 result aggregation, paired statistics, and artifact verification."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from statistics import mean
from typing import Any, Mapping, Sequence

import numpy as np

from unified_scripts import stable_hash

from .utils import RunPaths


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
    for probe in probes:
        for artifact in probe.get("image_artifacts") or ():
            mass = (artifact.get("diagnostics") or {}).get("global_region_mass") or {}
            if "dashboard_header_band" in mass:
                header.append(float(mass["dashboard_header_band"]))
            attention_first.append(float(
                (artifact.get("attention_peak_diagnostics") or {}).get("argmax_patch_index") == 0
            ))
            contribution_first.append(float(
                (artifact.get("weighted_value_peak_diagnostics") or {}).get("argmax_patch_index") == 0
            ))
    return {
        "avg_visual_attention_mass": mean(float(probe.get("visual_attention_mass") or 0.0) for probe in probes),
        "avg_nonvisual_attention_mass": mean(float(probe.get("nonvisual_attention_mass") or 0.0) for probe in probes),
        "avg_text_mapping_coverage": mean(float(probe.get("text_mapping_coverage") or 0.0) for probe in probes),
        "avg_dashboard_header_attention_mass": mean(header) if header else None,
        "first_patch_attention_argmax_rate": mean(attention_first) if attention_first else None,
        "first_patch_weighted_value_argmax_rate": mean(contribution_first) if contribution_first else None,
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
        scores = [row.get("score") or {} for row in completed]
        calls = [call for row in completed for call in _calls(row)]
        case_tokens = [
            {
                name: sum(int(call.get(name) or 0) for call in _calls(row))
                for name in ("input_tokens", "output_tokens", "total_tokens")
            }
            for row in completed
        ]
        metric_names = sorted({key for score in scores for key, value in score.items() if isinstance(value, (int, float))})
        summary = {
            "model": model, "arm": arm, "dataset": dataset,
            "records": len(values), "completed": len(completed),
            "error_rate": 1.0 - len(completed) / len(values) if values else 0.0,
            "model_output_valid_rate": mean(float(row.get("model_output_valid", True)) for row in completed) if completed else None,
            **{key: mean(float(score.get(key, 0.0)) for score in scores) if scores else None for key in metric_names},
            "avg_input_tokens": mean(int(call.get("input_tokens") or 0) for call in calls) if calls else None,
            "avg_output_tokens": mean(int(call.get("output_tokens") or 0) for call in calls) if calls else None,
            "avg_total_tokens": mean(int(call.get("total_tokens") or 0) for call in calls) if calls else None,
            "avg_case_input_tokens": mean(row["input_tokens"] for row in case_tokens) if case_tokens else None,
            "avg_case_output_tokens": mean(row["output_tokens"] for row in case_tokens) if case_tokens else None,
            "avg_case_total_tokens": mean(row["total_tokens"] for row in case_tokens) if case_tokens else None,
            "avg_model_calls_per_case": mean(int(row.get("model_calls") or 0) for row in completed) if completed else None,
            "truncation_rate": mean(float(bool(call.get("truncated"))) for call in calls) if calls else None,
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
        }
        for row in records if row.get("status") == "completed" and metric in (row.get("score") or {})
    }
    output: dict[str, Any] = {}
    arms = set(key[2] for key in index)
    if metric == "mrr":
        primary = [tuple(pair) for pair in config["analysis"]["primary_rca_comparisons"]]
        negative = [tuple(config["analysis"]["negative_control_comparison"])]
    else:
        primary = [(f"L{level}", "L1") for level in (2, 3, 4)]
        negative = []
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


def analyze_records(records: Sequence[Mapping[str, Any]], spec: Any, config: Mapping[str, Any]) -> dict[str, Any]:
    errors = [row for row in records if row.get("status") != "completed"]
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
        "records": len(records), "completed": len(complete),
        "infrastructure_errors": len(errors),
        "model_output_errors": len(model_output_errors),
        "whole_record_error_rate": len(errors) / len(records) if records else 0.0,
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
        "parse_rate": (
            (len(complete) - len(model_output_errors)) / len(complete) if complete else 0.0
        ),
    }
    result["eligible_for_claim"] = (
        result["whole_record_error_rate"] <= float(config["runtime"]["whole_case_infrastructure_exclusion_maximum"])
        and result["parse_rate"] >= float(config["runtime"]["parse_rate_minimum"])
    )
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
        except json.JSONDecodeError:
            errors.append(f"invalid_json:{path.relative_to(paths.root)}")
    return {
        "schema_version": "RQ1_1VerificationV1", "passed": not errors,
        "errors": errors[:100], "error_count": len(errors),
        "prepared_cases": len(index.get("cases", ())), "trajectory_records": trajectory_count,
    }

"""RQ2 verification, response surfaces, attribution ledgers, and selections."""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from unified_scripts import stable_hash
from vlmrca.vlm.performance import summarize_call_performance

from .utils import RQ2Error


def _mean(values: Sequence[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _metric(record: Mapping[str, Any]) -> float:
    score = record.get("score") or {}
    return float(score.get("mrr", score.get("complete_chain", 0.0)))


def _cell(record: Mapping[str, Any]) -> str:
    if record.get("tool_profile") and record.get("tool_transport"):
        return f"{record['tool_profile']}:{record['tool_transport']}"
    return str(record["unit_id"]).split("__", 1)[0]


def _spec_cell(spec: Mapping[str, Any]) -> str:
    if spec.get("design_id"):
        return str(spec["design_id"])
    metric_key = {
        "small_multiple_lines": "ML", "heatmap": "MH", "overlay_lines": "MO",
    }.get(str(spec.get("metric_encoding")), "M?")
    return "_".join((
        metric_key,
        str(spec.get("trace_encoding") or "trace_dumbbell"),
        str(spec.get("log_encoding") or "template_frequency_timeline"),
        "GM" if spec.get("topology_encoding") == "adjacency_matrix" else "GN",
        str(spec.get("layout_family") or "modality_grouped"),
        str(spec.get("footprint_policy") or "balanced"),
        f"G{spec.get('grid_columns', 12)}x{spec.get('grid_rows', 8)}",
    ))


DESIGN_FEATURES = (
    "metric_lines", "metric_overlay", "trace_bars", "log_matrix", "topology_matrix", "topology_edge_table",
    "propagation_timeline", "layout_entity", "layout_temporal",
    "layout_topology_centered", "order_salience", "order_topology",
    "footprint_compact", "footprint_detailed", "colorblind_skin",
    "coordination_entity", "coordination_time", "metric_common_scale",
    "cell_resolution", "raster_resolution", "legibility", "grid_aspect", "gutter",
    "cell_resolution_squared", "raster_resolution_squared", "legibility_squared", "gutter_squared",
)
DESIGN_INTERACTIONS = (
    ("metric_lines", "cell_resolution"), ("topology_matrix", "layout_topology_centered"),
    ("footprint_detailed", "grid_aspect"), ("cell_resolution", "footprint_detailed"),
    ("metric_lines", "layout_entity"), ("topology_matrix", "layout_entity"),
    ("coordination_entity", "layout_entity"),
    ("metric_overlay", "cell_resolution"),
)


def _feature_row(spec: Mapping[str, Any]) -> dict[str, float]:
    layout = str(spec.get("layout_family") or "modality_grouped")
    footprint = str(spec.get("footprint_policy") or "balanced")
    columns, rows = float(spec.get("grid_columns", 12)), float(spec.get("grid_rows", 8))
    cell = (float(spec.get("cell_edge_px", 256)) - 304.0) / 144.0
    raster = (float(spec.get("raster_scale", 1.0)) - 1.125) / .375
    legibility = (float(spec.get("legibility_scale", 1.0)) - 1.025) / .225
    gutter = (float(spec.get("gutter_px", 12)) - 18.0) / 14.0
    effect = lambda value, base, level: 1.0 if value == level else -1.0 if value == base else 0.0
    return {
        "metric_lines": effect(spec.get("metric_encoding"), "heatmap", "small_multiple_lines"),
        "metric_overlay": effect(spec.get("metric_encoding"), "heatmap", "overlay_lines"),
        "trace_bars": effect(spec.get("trace_encoding"), "trace_dumbbell", "trace_baseline_fault_bars"),
        "log_matrix": effect(spec.get("log_encoding"), "template_frequency_timeline", "template_time_matrix"),
        "topology_matrix": effect(spec.get("topology_encoding"), "node_link", "adjacency_matrix"),
        "topology_edge_table": effect(spec.get("topology_encoding"), "node_link", "edge_table"),
        "propagation_timeline": effect(spec.get("propagation_encoding"), "propagation_rows", "propagation_timeline"),
        "layout_entity": effect(layout, "modality_grouped", "entity_grouped"),
        "layout_temporal": effect(layout, "modality_grouped", "salience_first"),
        "layout_topology_centered": effect(layout, "modality_grouped", "topology_centered"),
        "order_salience": effect(spec.get("entity_order"), "stable_id", "salience_onset"),
        "order_topology": effect(spec.get("entity_order"), "stable_id", "topology_bfs"),
        "footprint_compact": effect(footprint, "balanced", "compact"),
        "footprint_detailed": effect(footprint, "balanced", "detailed"),
        "colorblind_skin": effect(spec.get("style_skin"), "canonical", "colorblind"),
        "coordination_entity": effect(spec.get("coordination_mode"), "none", "shared_entity"),
        "coordination_time": effect(spec.get("coordination_mode"), "none", "shared_time"),
        "metric_common_scale": effect(spec.get("metric_scale_policy"), "per_card_raw", "common_robust"),
        "cell_resolution": cell,
        "raster_resolution": raster,
        "legibility": legibility,
        "grid_aspect": columns / rows,
        "gutter": gutter,
        "cell_resolution_squared": cell * cell,
        "raster_resolution_squared": raster * raster,
        "legibility_squared": legibility * legibility,
        "gutter_squared": gutter * gutter,
    }


def _response_surface(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Fit the same hierarchical linear response surface within every case."""

    names = (*DESIGN_FEATURES, *(f"{left}×{right}" for left, right in DESIGN_INTERACTIONS))
    coefficients: dict[tuple[str, str], list[float]] = defaultdict(list)
    curves: dict[tuple[str, str], list[tuple[float, float, float]]] = defaultdict(list)
    groups: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        if row.get("status") == "complete":
            groups[(str(row.get("task")), str(row.get("model")), str(row.get("dataset")), str(row.get("opaque_incident_id")))].append(row)
    for (task, _model, _dataset, _case), rows in groups.items():
        matrix, targets = [], []
        for row in rows:
            features = _feature_row(row.get("design_spec") or {})
            values = [1.0, *(features[name] for name in DESIGN_FEATURES)]
            values.extend(features[left] * features[right] for left, right in DESIGN_INTERACTIONS)
            matrix.append(values); targets.append(_metric(row))
        if len(matrix) >= len(names) + 1:
            beta = np.linalg.lstsq(np.asarray(matrix), np.asarray(targets), rcond=None)[0][1:]
            for name, value in zip(names, beta):
                coefficients[(task, name)].append(float(value))
        for factor in ("cell_edge_px", "gutter_px", "raster_scale", "legibility_scale"):
            anchor_rows = [
                row for row in rows
                if str((row.get("design_spec") or {}).get("design_role")) in {"baseline", f"curve:{factor}"}
            ]
            points = sorted({float((row.get("design_spec") or {}).get(factor)) for row in anchor_rows})
            if len(points) >= 3:
                values = [statistics.fmean(_metric(row) for row in anchor_rows if float((row.get("design_spec") or {}).get(factor)) == point) for point in points]
                scaled = np.asarray(points, dtype=float); scaled = (scaled - scaled.mean()) / (float(np.ptp(scaled)) or 1.0)
                curve = np.polyfit(scaled, np.asarray(values), deg=2)
                curves[(task, factor)].append((float(curve[1]), float(curve[0]), float(points[int(np.argmax(values))])))
    main, interactions = [], []
    for (task, name), values in sorted(coefficients.items()):
        row = {"task": task, "feature": name, **_paired_stats(values)}
        (interactions if "×" in name else main).append(row)
    for task in {row["task"] for row in main}:
        _holm([row for row in main if row["task"] == task])
    for task in {row["task"] for row in interactions}:
        _holm([row for row in interactions if row["task"] == task])
    curve_rows = [
        {
            "task": task, "factor": factor, "n_cases": len(values),
            "mean_linear_slope": _mean([row[0] for row in values]),
            "mean_quadratic_curvature": _mean([row[1] for row in values]),
            "mean_case_optimum_observed": _mean([row[2] for row in values]),
        }
        for (task, factor), values in sorted(curves.items())
    ]
    return {"main_effects": main, "registered_interactions": interactions, "continuous_curves": curve_rows}


def composer_attribution(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Audit exact-anchor sibling credit without mistaking it for causality."""

    siblings: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        audit = row.get("composer_attribution") or {}
        if audit.get("kind") == "matched_sibling" and audit.get("anchor_state_hash"):
            key = (
                str(row.get("model")), str(row.get("dataset")),
                str(row.get("opaque_incident_id")), str(audit["anchor_state_hash"]),
                str(audit.get("action")),
            )
            siblings[key].append(row)
    credit_rows = []
    for key, rows in sorted(siblings.items()):
        if len(rows) < 2:
            continue
        utilities = [_metric(row) for row in rows]
        for index, row in enumerate(rows):
            audit = row["composer_attribution"]
            credit_rows.append({
                "model": key[0], "dataset": key[1], "case": key[2],
                "anchor_state_hash": key[3], "action": key[4],
                "action_value": audit.get("action_value"),
                "rr_credit": utilities[index] - statistics.fmean(utilities[:index] + utilities[index + 1:]),
                "input_tokens": float((row.get("call") or {}).get("input_tokens") or 0),
                "grounding": (row.get("grounding") or {}).get("grounded_mention_precision"),
            })
    ledgers: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        audit = row.get("composer_attribution") or {}
        if audit.get("kind") == "telescoping" and audit.get("ledger_id"):
            ledgers[(str(row.get("model")), str(row.get("opaque_incident_id")), str(audit["ledger_id"]))].append(row)
    telescoping = []
    for key, rows in sorted(ledgers.items()):
        ordered = sorted(rows, key=lambda row: int(row["composer_attribution"]["stage_index"]))
        values = [_metric(row) for row in ordered]
        deltas = [values[index] - values[index - 1] for index in range(1, len(values))]
        telescoping.append({
            "model": key[0], "case": key[1], "ledger_id": key[2],
            "stage_deltas": deltas, "total_delta": values[-1] - values[0] if values else 0.0,
            "accounting_residual": (sum(deltas) - (values[-1] - values[0])) if values else 0.0,
        })
    reversions: dict[tuple[str, ...], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    checkpoints: dict[tuple[str, ...], dict[str, float]] = defaultdict(dict)
    interactions_2x2: dict[tuple[str, ...], dict[tuple[int, int], float]] = defaultdict(dict)
    for row in records:
        audit = row.get("composer_attribution") or {}
        common = (str(row.get("model")), str(row.get("dataset")), str(row.get("opaque_incident_id")))
        if audit.get("kind") == "component_reversion":
            key = (*common, str(audit.get("intervention_id")), str(audit.get("component")))
            reversions[key][str(audit.get("role"))] = row
        if row.get("composer_checkpoint"):
            checkpoints[common][str(row["composer_checkpoint"])] = _metric(row)
        if audit.get("kind") == "component_interaction_2x2":
            key = (*common, str(audit.get("interaction_id")))
            interactions_2x2[key][(int(audit.get("left_on", 0)), int(audit.get("right_on", 0)))] = _metric(row)
    reversion_rows = []
    for key, values in sorted(reversions.items()):
        if {"final", "reverted"} <= values.keys():
            reversion_rows.append({
                "model": key[0], "dataset": key[1], "case": key[2],
                "intervention_id": key[3], "component": key[4],
                "controlled_effect": _metric(values["final"]) - _metric(values["reverted"]),
            })
    checkpoint_order = ("base", "sft", "preference", "rl")
    checkpoint_rows = []
    for key, values in sorted(checkpoints.items()):
        present = [name for name in checkpoint_order if name in values]
        checkpoint_rows.append({
            "model": key[0], "dataset": key[1], "case": key[2],
            "checkpoint_scores": values,
            "successive_deltas": {
                f"{left}_to_{right}": values[right] - values[left]
                for left, right in zip(present, present[1:])
            },
        })
    interaction_rows = []
    for key, values in sorted(interactions_2x2.items()):
        required = ((0, 0), (1, 0), (0, 1), (1, 1))
        if all(cell in values for cell in required):
            interaction_rows.append({
                "model": key[0], "dataset": key[1], "case": key[2],
                "interaction_id": key[3],
                "difference_in_differences": (
                    values[(1, 1)] - values[(0, 1)]
                    - values[(1, 0)] + values[(0, 0)]
                ),
            })
    return {
        "checkpoint_deltas": checkpoint_rows,
        "matched_sibling_credit": credit_rows,
        "controlled_component_reversions": reversion_rows,
        "registered_component_interactions": interaction_rows,
        "ordered_telescoping": telescoping,
    }


def _paired_stats(differences: Sequence[float]) -> dict[str, Any]:
    values = list(map(float, differences))
    if not values:
        return {"n": 0, "mean_delta": None, "cohens_dz": None, "p": None}
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    try:
        from scipy.stats import wilcoxon

        p = 1.0 if all(value == 0 for value in values) else float(
            wilcoxon(values, zero_method="pratt", alternative="two-sided").pvalue
        )
    except (ImportError, ValueError):
        p = None
    return {
        "n": len(values), "mean_delta": _mean(values),
        "cohens_dz": (_mean(values) / sd if sd else 0.0), "p": p,
    }


def _holm(rows: list[dict[str, Any]]) -> None:
    available = sorted(
        ((index, float(row["p"])) for index, row in enumerate(rows) if row.get("p") is not None),
        key=lambda item: item[1],
    )
    running = 0.0; count = len(available)
    for rank, (index, value) in enumerate(available):
        running = max(running, min(1.0, value * (count - rank)))
        rows[index]["holm_adjusted_p"] = running


def _group_summary(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        groups[(str(record.get("model")), str(record.get("dataset")), str(record.get("task")), _cell(record))].append(record)
    output = []
    for key, rows in sorted(groups.items()):
        completed = [row for row in rows if row.get("status") == "complete"]
        calls = [row.get("call") or {} for row in completed]
        grounding = [row.get("grounding") or {} for row in completed if row.get("task") == "one_stage_rca"]
        grounded_precision = [
            float(value["grounded_mention_precision"])
            for value in grounding if value.get("grounded_mention_precision") is not None
        ]
        output.append({
            "model": key[0], "dataset": key[1], "task": key[2], "arm": key[3],
            "n": len(rows), "complete": len(completed),
            "error_rate": 1 - len(completed) / len(rows),
            "parse_rate": (
                sum(not bool(row.get("model_output_error")) for row in completed) / len(completed)
                if completed else None
            ),
            "score": _mean([_metric(row) for row in completed]),
            "input_tokens": _mean([float(call.get("input_tokens") or 0) for call in calls]),
            "output_tokens": _mean([float(call.get("output_tokens") or 0) for call in calls]),
            "image_tokens": _mean([float(call.get("image_tokens") or 0) for call in calls]),
            "grounded_mention_precision": _mean(grounded_precision),
            "unsupported_structured_mentions": sum(
                len(value.get("unsupported_structured_mentions") or ()) for value in grounding
            ),
            "root_evidence_citation_rate": _mean([
                float(bool(value.get("root_evidence_cited")))
                for value in grounding if value.get("root_evidence_available")
            ]),
            **summarize_call_performance(calls),
        })
    return output


def _observed_outcome_oracle_gap(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Descriptive in-sample upper bound, not a deployable or unbiased oracle."""
    rca = [row for row in records if row.get("task") == "one_stage_rca" and row.get("status") == "complete"]
    output = []
    groups = {(str(row["model"]), str(row["dataset"])) for row in rca}
    for model, dataset in sorted(groups):
        rows = [row for row in rca if row["model"] == model and row["dataset"] == dataset]
        cells = sorted({_cell(row) for row in rows})
        cell_means = {
            cell: statistics.fmean(_metric(row) for row in rows if _cell(row) == cell)
            for cell in cells
        }
        by_case: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            by_case[str(row["opaque_incident_id"])].append(_metric(row))
        best_fixed = max(cell_means.values()) if cell_means else None
        oracle = _mean([max(values) for values in by_case.values() if values])
        output.append({
            "model": model, "dataset": dataset,
            "best_fixed_cell": max(cell_means, key=cell_means.get) if cell_means else None,
            "best_fixed_mrr": best_fixed,
            "observed_outcome_oracle_mrr": oracle,
            "observed_outcome_oracle_gap": (
                oracle - best_fixed if oracle is not None and best_fixed is not None else None
            ),
            "interpretation": (
                "optimistic in-sample headroom: each case is assigned the design that already "
                "achieved its best sampled outcome; this is not a deployable selector result"
            ),
        })
    return output


def _paired_arm_comparisons(
    records: Sequence[Mapping[str, Any]], baseline: str,
    arms: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    complete = [row for row in records if row.get("status") == "complete"]
    selected_arms = list(arms) if arms is not None else sorted({_cell(row) for row in complete if _cell(row) != baseline})
    output = []
    for task in sorted({str(row.get("task")) for row in complete}):
        for arm in selected_arms:
            pairs: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
            for row in complete:
                if row.get("task") == task and _cell(row) in {baseline, arm}:
                    pairs[(str(row["model"]), str(row["dataset"]), str(row["opaque_incident_id"]))][_cell(row)] = _metric(row)
            differences = [values[arm] - values[baseline] for values in pairs.values() if arm in values and baseline in values]
            if differences:
                output.append({"task": task, "arm": arm, "baseline": baseline, **_paired_stats(differences)})
        _holm([row for row in output if row["task"] == task])
    return output


def _content_twin_comparisons(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    policies = sorted({str(row.get("content_policy")) for row in records})
    for task in sorted({str(row.get("task")) for row in records}):
        for policy in policies:
            pairs: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
            for row in records:
                if row.get("status") != "complete" or row.get("task") != task or row.get("content_policy") != policy:
                    continue
                pairs[(str(row["model"]), str(row["dataset"]), str(row["opaque_incident_id"]))][str(row.get("twin"))] = _metric(row)
            for canvas in ("canvas_reflow", "canvas_blank"):
                differences = [values[canvas] - values["text"] for values in pairs.values() if {canvas, "text"} <= values.keys()]
                if differences:
                    output.append({
                        "task": task, "policy": policy, "contrast": f"{canvas}_minus_text",
                        **_paired_stats(differences),
                    })
            differences = [values["canvas_reflow"] - values["canvas_blank"] for values in pairs.values() if {"canvas_reflow", "canvas_blank"} <= values.keys()]
            if differences:
                output.append({"task": task, "policy": policy, "contrast": "reflow_minus_blank", **_paired_stats(differences)})
        _holm([row for row in output if row["task"] == task])
    return output


def _tool_representation_analysis(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Separate within-tool transport effects from between-tool selection effects."""

    complete = [row for row in records if row.get("status") == "complete"]
    profiles = sorted({str(row.get("tool_profile")) for row in complete})
    within: list[dict[str, Any]] = []
    for profile in profiles:
        for model in sorted({str(row.get("model")) for row in complete}):
            for dataset in sorted({str(row.get("dataset")) for row in complete}):
                pairs: dict[str, dict[str, float]] = defaultdict(dict)
                for row in complete:
                    if (str(row.get("tool_profile")), str(row.get("model")), str(row.get("dataset"))) != (profile, model, dataset):
                        continue
                    pairs[str(row["opaque_incident_id"])][str(row.get("tool_transport"))] = _metric(row)
                deltas = [values["canvas"] - values["text"] for values in pairs.values() if {"canvas", "text"} <= values.keys()]
                if deltas:
                    within.append({
                        "profile": profile, "model": model, "dataset": dataset,
                        "contrast": "canvas_minus_text", **_paired_stats(deltas),
                    })
    for model in {row["model"] for row in within}:
        _holm([row for row in within if row["model"] == model])

    between: list[dict[str, Any]] = []
    interactions: list[dict[str, Any]] = []
    baseline = "SIRCL_STAR_FUSED"
    for profile in (value for value in profiles if value != baseline):
        transport_deltas: dict[str, dict[tuple[str, str, str], float]] = {}
        for transport in ("text", "canvas"):
            cells: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
            for row in complete:
                if str(row.get("tool_transport")) == transport and str(row.get("tool_profile")) in {baseline, profile}:
                    key = (str(row["model"]), str(row["dataset"]), str(row["opaque_incident_id"]))
                    cells[key][str(row["tool_profile"])] = _metric(row)
            deltas = {key: values[profile] - values[baseline] for key, values in cells.items() if {profile, baseline} <= values.keys()}
            transport_deltas[transport] = deltas
            between.append({
                "profile": profile, "baseline": baseline, "transport": transport,
                **_paired_stats(list(deltas.values())),
            })
        keys = set(transport_deltas["text"]).intersection(transport_deltas["canvas"])
        interactions.append({
            "profile": profile,
            "contrast": "(profile_minus_fused)_canvas_minus_(profile_minus_fused)_text",
            **_paired_stats([
                transport_deltas["canvas"][key] - transport_deltas["text"][key]
                for key in keys
            ]),
        })
    _holm(between); _holm(interactions)
    return {
        "within_tool_canvas_text": within,
        "between_tool_vs_fused": between,
        "tool_by_representation_interaction": interactions,
        "causal_scope": (
            "within-tool Canvas/Text contrasts isolate representation at equal selected facts; "
            "between-tool contrasts intentionally change selected evidence"
        ),
    }


def _attention(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, float]]] = defaultdict(list)
    for record in records:
        probe = ((record.get("call") or {}).get("attention_probe") or {})
        for image in probe.get("image_artifacts") or ():
            diagnostics = image.get("diagnostics") or {}
            density = diagnostics.get("region_attention_per_pixel") or {}
            groups[(str(record.get("model")), str(record.get("task")), _cell(record))].append(
                {region: float(value) for region, value in density.items() if value is not None}
            )
    output = []
    for key, rows in sorted(groups.items()):
        regions = sorted({region for row in rows for region in row})
        output.append({
            "model": key[0], "task": key[1], "arm": key[2], "n_images": len(rows),
            "mean_attention_per_pixel": {
                region: _mean([row[region] for row in rows if region in row]) for region in regions
            },
        })
    return output


def _select_d(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rca = [row for row in records if row.get("task") == "one_stage_rca" and row.get("status") == "complete"]
    cells = sorted({_cell(row) for row in rca})
    scored = []
    for cell in cells:
        macro = []
        for model in sorted({str(row["model"]) for row in rca}):
            for dataset in sorted({str(row["dataset"]) for row in rca}):
                values = [_metric(row) for row in rca if _cell(row) == cell and row["model"] == model and row["dataset"] == dataset]
                if values:
                    macro.append(statistics.fmean(values))
        calls = [row.get("call") or {} for row in rca if _cell(row) == cell]
        exemplar = next(row for row in rca if _cell(row) == cell)
        scored.append({
            "cell_id": cell, "macro_mrr": _mean(macro),
            "input_tokens": _mean([float(call.get("input_tokens") or 0) for call in calls]),
            "spec": exemplar["design_spec"],
        })
    if not scored:
        raise RQ2Error("cannot select D* without completed development records")
    best_mrr = max(float(row["macro_mrr"]) for row in scored)
    eligible = [row for row in scored if best_mrr - float(row["macro_mrr"]) <= 0.01]
    chosen = sorted(eligible, key=lambda row: (float(row["input_tokens"] or math.inf), row["cell_id"]))[0]
    structural_spec = {**dict(chosen["spec"]), "fact_inventory_hash": ""}
    d_alt_row = max(
        (row for row in scored if row["cell_id"] != chosen["cell_id"]),
        key=lambda row: float(np.linalg.norm(
            np.asarray(list(_feature_row(row["spec"]).values()))
            - np.asarray(list(_feature_row(chosen["spec"]).values()))
        )),
    )
    d_alt = {**dict(d_alt_row["spec"]), "fact_inventory_hash": ""}
    confirmation = [chosen]
    mandatory_roles = {
        "anchor:metric_encoding:heatmap",
        "anchor:metric_encoding:small_multiple_lines",
        "anchor:metric_encoding:overlay_lines",
    }
    for row in sorted(scored, key=lambda value: value["cell_id"]):
        if str((row.get("spec") or {}).get("design_role")) in mandatory_roles:
            if row["cell_id"] not in {value["cell_id"] for value in confirmation}:
                confirmation.append(row)
    remaining = [row for row in scored if row["cell_id"] != chosen["cell_id"]]
    remaining = [row for row in remaining if row["cell_id"] not in {value["cell_id"] for value in confirmation}]
    while remaining and len(confirmation) < 16:
        candidate = max(
            remaining,
            key=lambda row: min(
                float(np.linalg.norm(np.asarray(list(_feature_row(row["spec"]).values())) - np.asarray(list(_feature_row(old["spec"]).values()))))
                for old in confirmation
            ),
        )
        confirmation.append(candidate); remaining.remove(candidate)
    return {
        "schema_version": "CanvasRCARQ2SelectionV1", "status": "d_star_frozen",
        "d_star_cell_id": chosen["cell_id"], "d_star": structural_spec,
        "d_alt_cell_id": d_alt_row["cell_id"], "d_alt": d_alt,
        "c_star_policy": "FULL", "selection_table": scored,
        "confirmation_design_ids": [row["cell_id"] for row in confirmation],
    }


def _select_c(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    # DENSE_M24 is an expanded-evidence mechanism pair, not a compression
    # candidate.  It remains in the reported twin comparisons but cannot win C*.
    rows = [
        row for row in records
        if row.get("task") == "one_stage_rca"
        and row.get("twin") == "canvas_reflow"
        and row.get("status") == "complete"
        and row.get("content_policy") != "DENSE_M24"
    ]
    policies = sorted({str(row["content_policy"]) for row in rows})
    by_policy: dict[str, dict[tuple[str, str], float]] = {}
    for policy in policies:
        by_policy[policy] = {}
        for model in sorted({str(row["model"]) for row in rows}):
            for dataset in sorted({str(row["dataset"]) for row in rows}):
                values = [_metric(row) for row in rows if row["content_policy"] == policy and row["model"] == model and row["dataset"] == dataset]
                if values:
                    by_policy[policy][(model, dataset)] = statistics.fmean(values)
    if "FULL" not in by_policy:
        raise RQ2Error("content selection requires FULL CanvasTwin")
    table = []
    for policy in policies:
        deltas = [by_policy[policy][key] - value for key, value in by_policy["FULL"].items() if key in by_policy[policy]]
        calls = [row.get("call") or {} for row in rows if row["content_policy"] == policy]
        table.append({
            "policy": policy, "macro_mrr": _mean(list(by_policy[policy].values())),
            "minimum_model_dataset_delta": min(deltas) if deltas else None,
            "mean_input_tokens": _mean([float(call.get("input_tokens") or 0) for call in calls]),
            "eligible": bool(deltas) and min(deltas) >= -0.05 and (_mean(deltas) or 0) >= -0.05,
        })
    eligible = [row for row in table if row["eligible"]]
    chosen = sorted(eligible, key=lambda row: (float(row["mean_input_tokens"] or math.inf), -float(row["macro_mrr"] or 0), row["policy"]))[0] if eligible else next(row for row in table if row["policy"] == "FULL")
    exemplar = next(row for row in records if row.get("design_spec"))
    structural_spec = {**dict(exemplar["design_spec"]), "fact_inventory_hash": ""}
    return {
        "schema_version": "CanvasRCARQ2SelectionV1", "status": "c_star_frozen",
        "d_star_cell_id": _spec_cell(structural_spec), "d_star": structural_spec,
        "c_star_policy": chosen["policy"], "selection_table": table,
    }


def analyze_records(
    records: Sequence[Mapping[str, Any]], experiment: str,
    config: Mapping[str, Any], *, select: bool = False,
) -> dict[str, Any]:
    abandoned = set(map(str, config.get("abandoned_tasks", {})))
    ignored = [record for record in records if str(record.get("task")) in abandoned]
    records = [record for record in records if str(record.get("task")) not in abandoned]
    complete = [record for record in records if record.get("status") == "complete"]
    parsed = [record for record in complete if not record.get("model_output_error")]
    error_categories: dict[str, int] = defaultdict(int)
    for record in records:
        if record.get("status") != "complete":
            message = str(record.get("error") or "infrastructure_error").casefold()
            category = "timeout" if "timeout" in message else "vllm_response" if any(token in message for token in ("http", "vllm", "connection")) else "infrastructure_other"
            error_categories[category] += 1
        elif record.get("model_output_error"):
            error_categories["format_parse"] += 1
    result: dict[str, Any] = {
        "schema_version": "CanvasRCARQ2AnalysisV1", "experiment": experiment,
        "records": len(records), "complete": len(complete),
        "abandoned_records_ignored": len(ignored),
        "infrastructure_error_rate": 1 - len(complete) / len(records) if records else 0.0,
        "parse_rate": len(parsed) / len(complete) if complete else 0.0,
        "error_categories": dict(sorted(error_categories.items())),
        "groups": _group_summary(records), "attention": _attention(complete),
    }
    if experiment == "exp_equal_fact_design":
        response = _response_surface(complete)
        result["design_main_effects"] = response["main_effects"]
        result["registered_interactions"] = response["registered_interactions"]
        result["continuous_response_curves"] = response["continuous_curves"]
        result["observed_outcome_oracle_gap"] = _observed_outcome_oracle_gap(complete)
        if select:
            result["selection"] = _select_d(complete)
    elif experiment == "exp_content_budget_twins":
        # Within-policy Canvas/Text twins are the only equal-information
        # comparisons in this experiment.
        result["canvas_text_comparisons"] = _content_twin_comparisons(complete)
        if select:
            result["selection"] = _select_c(complete)
    elif experiment == "exp_downstream_transfer":
        result["arm_comparisons"] = _paired_arm_comparisons(complete, "T_FULL")
        result["compact_text_controls"] = {
            "full": _paired_arm_comparisons(complete, "T_FULL", arms=("C_FULL",)),
            "selected": _paired_arm_comparisons(complete, "C_STAR_TEXT", arms=("C_STAR_COMPACT", "C_STAR_CANVAS")),
            "dense": _paired_arm_comparisons(complete, "DENSE_TEXT", arms=("DENSE_COMPACT", "DENSE_CANVAS")),
        }
    elif experiment == "exp_tool_representation":
        result["tool_representation"] = _tool_representation_analysis(complete)
    return result


def verify_result_root(result_root: Path, prepared_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    index_path = prepared_root / "prepared" / "index.json"
    if not index_path.is_file():
        raise RQ2Error("prepared index is missing")
    index = json.loads(index_path.read_text()); unsigned = dict(index)
    if stable_hash({key: value for key, value in unsigned.items() if key != "index_sha256"}) != index["index_sha256"]:
        raise RQ2Error("prepared index hash mismatch")
    errors, records, parse_errors, abandoned_records = [], 0, 0, 0
    abandoned = set(map(str, config.get("abandoned_tasks", {})))
    for path in (result_root / "trajectories").rglob("*.json"):
        record = json.loads(path.read_text()); recorded = record.pop("record_sha256", None)
        if str(record.get("task")) in abandoned:
            abandoned_records += 1
            continue
        if recorded is None or stable_hash(record) != recorded:
            errors.append(f"record hash mismatch: {path}")
        parse_errors += int(bool(record.get("model_output_error")))
        records += 1
    error_records = 0
    for path in (result_root / "trajectories").rglob("*.json"):
        record = json.loads(path.read_text())
        if str(record.get("task")) in abandoned:
            continue
        if record.get("status") != "complete":
            error_records += 1
    rate = error_records / records if records else 0.0
    parse_rate = (records - parse_errors) / records if records else 0.0
    passed = (
        bool(records)
        and not errors
        and rate <= float(config["runtime"]["whole_case_infrastructure_exclusion_maximum"])
        and parse_rate >= float(config["runtime"]["parse_rate_minimum"])
    )
    return {
        "schema_version": "CanvasRCARQ2VerificationV1",
        "status": "passed" if passed else "failed",
        "records": records, "infrastructure_errors": error_records,
        "abandoned_records_ignored": abandoned_records,
        "infrastructure_error_rate": rate, "parse_errors": parse_errors,
        "parse_rate": parse_rate, "integrity_errors": errors,
    }


__all__ = ["analyze_records", "composer_attribution", "verify_result_root"]

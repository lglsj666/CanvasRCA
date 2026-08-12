"""RQ1 experiment definitions, evidence preparation, arms, and prompts."""

from __future__ import annotations

import io
import itertools
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from typing import Any, Iterable, Literal, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont

from unified_scripts import canonical_json, stable_hash
from vlmrca.processed import load_processed_case, load_processed_private
from RQs.RQ1.src.renderer.dashboard import (
    RENDERER_VERSION,
    CaseRenderView,
    compile_dashboard,
    crop_dashboard_evidence_regions,
    opaque_incident_id,
)
from RQs.RQ1.src.renderer.presets import make_dashboard_config
from RQs.RQ1.src.renderer.kpi_select import score_series
from RQs.RQ1.src.renderer.onset import pod_to_service, service_level_projection
from vlmrca.rq0.evidence import build_canonical_evidence
from vlmrca.vlm.client import image_part, text_part

from .utils import RQ1Error, audit_visible, numeric_entity_map

Region = Literal["M", "L", "R", "G"]
RCA_ARMS = ("T", "F", "V", "P", "H", "R")
REGIONS: tuple[Region, ...] = ("M", "R", "L", "G")
PROMPT_REGION_ORDER: tuple[Region, ...] = REGIONS
ENTITY_ID_NOTE = "Service names, pod names, and node names are represented by numeric IDs."
VISUAL_PATCH_GRID = (16, 16)
TEMPLATE_VALUE_KINDS = {
    "M_direct_read": ("entity_id",), "L_direct_read": ("scalar_value",),
    "R_direct_read": ("scalar_value",), "G_direct_read": ("scalar_value",),
    "M_L_link": ("entity_id", "scalar_value"), "M_R_link": ("entity_id", "scalar_value"),
    "M_G_link": ("entity_id", "scalar_value"), "L_R_link": ("entity_id", "scalar_value"),
    "L_G_link": ("entity_id", "scalar_value"), "R_G_link": ("entity_id", "scalar_value"),
    "M_locator_chain": ("entity_id", "scalar_value", "scalar_value"),
    "R_locator_chain": ("entity_id", "scalar_value", "scalar_value"),
    "L_locator_chain": ("entity_id", "scalar_value", "scalar_value"),
    "G_locator_chain": ("entity_id", "scalar_value", "scalar_value"),
}

QA_EVIDENCE_GUIDE = """Evidence structure and fields:
- M (metrics): renderer-v12 metric panels identify a panel, numeric entity and metric; curves use 64 relative bins and the printed line reports baseline, peak and signed peak-z at dashboard precision.
- R (traces): the visible table reports numeric entity, p95 before/during, relative change and error percentage when available.
- L (logs): the visible table reports numeric entity and either error counts/fraction or pre/during volume change.
- G (topology): the propagation plot prints entity onset/severity/source and the edge key lists every directed caller -> callee edge. For target X, U -> X is upstream and X -> D is downstream.
Relative bins are case-local. `missing`/`null` means unavailable evidence, never numeric zero. Metric and trace anomaly magnitudes come from different instruments and must not be compared as if they shared a scale. Text evidence is ordered M -> R -> L -> G."""

RCA_EVIDENCE_GUIDE = """Incident-evidence structure and fields:
- C/common: `candidate_set` is exhaustive and ordered; `evidence_schema` and `selection_summary` describe the label-blind renderer/selector, not a diagnosis; `evidence_legends` defines IDs, time and edges.
- M/metrics: `metric_series_64` gives panel/rank, numeric entity ID, diagnostic metric name, 64 relative values, an explicit missing mask, pre-fault baseline, peak and signed robust deviation. `observation_window` and `estimated_fault_window` use relative time only.
- R/traces: `trace_summary_entry` reports the entity, p95 before/during the incident, relative change and error fraction when available. These fields describe request-path behavior, not automatically the fault origin.
- L/logs: `log_summary_entry` reports entity-level error/event counts, totals, fractions, changes and normalized templates when available.
- G/topology: `propagation_service` reports relative onset, severity and evidence source; `directed_call_edge` is caller -> callee. If A calls B, a fault in B may propagate symptoms back to A.
The text and flat transports present incident regions in M -> R -> L -> G order, with topology last. The visual dashboard keeps its frozen spatial layout but encodes the same facts. Numeric IDs are case-local: 3 digits denote services, 4 digits nodes and 5 digits pods. `null`/`missing` is explicit absence, not zero."""

RCA_METHOD_GUIDE = """RCA method:
A fault in one component can propagate to dependent components, causing them to appear degraded even though they are not the root cause. Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS. Prefer a candidate with direct local evidence, temporally plausible onset and topology-consistent propagation over an upstream or co-affected symptom. Check metric, trace and log agreement when those regions are available, but do not invent a missing modality or require all modalities. Consider service, pod and node candidates at their stated granularity. Actively test the strongest alternative and contradictory evidence before finalizing a rank."""

STAGE2_LEDGER_GUIDE = """Normalized-ledger fields:
Stage 1 selected compact human-readable record keys; the host then copied the exact matching public attributes and at most four selected metric-bin values into `observations`. `temporal_relations` and `directed_edges` are deterministically derived only from selected, grounded topology rows. `missing_evidence` records selected explicit-absence facts. `binding_audit` is host-validation metadata, not incident evidence. Only grounded rows retained by the host may support a diagnosis."""

SIRCL_VERIFY_GUIDE = """Use this VERIFY procedure internally before emitting JSON; do not print its headers or working:
INITIAL: Produce a preliminary ranked list of root-cause candidates (top 3, in order). Determine why the top-1 candidate is the leading hypothesis.
VERIFY: Form exactly two verification questions about the INITIAL top-1 candidate. Each must be answerable using only the normalized ledger. Test one strongest supporting relation and one plausible contradiction, propagation explanation, or alternative origin; answer both from exact ledger observations or relations.
REVISE: If either verification answer contradicts the INITIAL top-1, revise the ranking. Otherwise keep it only when both verifications support it.
The final JSON ranking must reflect the REVISE outcome."""


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    task: str
    stages: int
    arms: tuple[str, ...]
    primary_metric: str


@dataclass(frozen=True)
class Question:
    query_id: str
    level: int
    regions: tuple[Region, ...]
    template: str
    text: str
    answer_steps: tuple[tuple[str, ...], ...]

    def public(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "reasoning_level": self.level,
            "region_path": list(self.regions),
            "template": self.template,
            "question": self.text,
        }

    def private(self) -> dict[str, Any]:
        return {**self.public(), "answer_steps": [list(step) for step in self.answer_steps]}


@dataclass(frozen=True)
class PreparedCase:
    public: Mapping[str, Any]
    private: Mapping[str, Any]
    full_png: bytes
    qa_full_png: bytes
    routed_png: bytes
    pixel_text_pngs: tuple[bytes, ...]
    qa_region_pngs: Mapping[str, tuple[bytes, ...]]
    variant_pngs: Mapping[str, bytes]


def _patch_region(layout: str, x: float, y: float, *, base_ratio: float) -> str:
    """Map one normalized patch centre to a model-visible evidence region."""

    if layout == "controlled":
        return "M" if x < 0.5 and y < 0.52 else "L" if y < 0.52 else "R" if x < 0.5 else "G"
    if layout.startswith("crop_") and layout[-1:] in REGIONS:
        return layout[-1]
    if layout == "dashboard":
        if y >= base_ratio:
            return "G"  # horizontal caller->callee identity key
        split, propagation_end = 0.746, base_ratio * 0.542
        if x < split:
            return "M"
        if y < propagation_end:
            return "G"
        return "L" if y < propagation_end + (base_ratio - propagation_end) / 2 else "R"
    return "ledger"


def visual_patch_atlas(
    png: bytes,
    *,
    layout: str,
    dashboard_base_ratio: float = 1.0,
    grid: tuple[int, int] = VISUAL_PATCH_GRID,
    font_point_size: float | None = None,
) -> dict[str, Any]:
    """Build a deterministic renderer-side patch atlas without a model call.

    The atlas is a diagnostic coordinate system, not an approximation of a
    model's private image tokenizer.  It supports blank/evidence density,
    region-level ledger maps, and optional externally captured attention.
    """

    image = Image.open(io.BytesIO(png)).convert("RGB")
    columns, rows = grid
    sampled = image.resize((columns * 12, rows * 12), Image.Resampling.BOX)
    backgrounds = ((255, 255, 255), (248, 250, 252), (236, 239, 241))
    patches: list[dict[str, Any]] = []
    region_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in range(rows):
        for column in range(columns):
            crop = sampled.crop((column * 12, row * 12, (column + 1) * 12, (row + 1) * 12))
            pixels = list(crop.getdata())
            ink = sum(
                min(sum((int(channel) - background[index]) ** 2 for index, channel in enumerate(pixel))
                    for background in backgrounds) > 18**2
                for pixel in pixels
            ) / len(pixels)
            region = _patch_region(
                layout, (column + 0.5) / columns, (row + 0.5) / rows,
                base_ratio=max(0.0, min(1.0, dashboard_base_ratio)),
            )
            patch = {
                "index": row * columns + column, "row": row, "column": column,
                "region": region, "ink_fraction": round(ink, 6), "blank": ink < 0.015,
            }
            patches.append(patch)
            region_rows[region].append(patch)
    region_stats = {
        region: {
            "patches": len(values),
            "patch_share": len(values) / len(patches),
            "evidence_patch_fraction": sum(not value["blank"] for value in values) / len(values),
            "mean_ink_fraction": sum(value["ink_fraction"] for value in values) / len(values),
        }
        for region, values in sorted(region_rows.items())
    }
    atlas = {
        "schema_version": "VisualPatchAtlasV1", "layout": layout,
        "image_sha256": stable_hash(png), "image_size": list(image.size),
        "grid": [columns, rows], "patch_coordinate_semantics": "model_agnostic_normalized_grid",
        "blank_patch_fraction": sum(value["blank"] for value in patches) / len(patches),
        "evidence_patch_fraction": sum(not value["blank"] for value in patches) / len(patches),
        "mean_ink_fraction": sum(value["ink_fraction"] for value in patches) / len(patches),
        "font_point_size": font_point_size, "regions": region_stats, "patches": patches,
    }
    atlas["atlas_sha256"] = stable_hash(atlas)
    return atlas


def attention_diagnostics(artifact: Mapping[str, Any], atlas: Mapping[str, Any]) -> dict[str, Any]:
    """Score an externally captured attention grid against the renderer atlas."""

    if artifact.get("image_sha256") != atlas.get("image_sha256"):
        raise RQ1Error("attention artifact image hash differs from its patch atlas")
    if list(artifact.get("grid") or ()) != list(atlas.get("grid") or ()):
        raise RQ1Error("attention artifact grid differs from its patch atlas")
    weights = list(artifact.get("weights") or ())
    patches = list(atlas.get("patches") or ())
    if len(weights) != len(patches) or not weights:
        raise RQ1Error("attention artifact weight count differs from its patch atlas")
    values = [float(value) for value in weights]
    if any(not math.isfinite(value) or value < 0 for value in values) or sum(values) <= 0:
        raise RQ1Error("attention weights must be finite, non-negative, and non-zero")
    total = sum(values)
    normalized = [value / total for value in values]
    mass: dict[str, float] = defaultdict(float)
    for patch, value in zip(patches, normalized, strict=True):
        mass[str(patch["region"])] += value
    entropy = -sum(value * math.log(value) for value in normalized if value > 0)
    top_count = max(1, math.ceil(len(values) * 0.10))
    top = sorted(range(len(values)), key=lambda index: (-values[index], index))[:top_count]
    required = set(map(str, artifact.get("required_regions") or ()))
    return {
        "schema_version": "VisualAttentionDiagnosticsV1",
        "attention_source": str(artifact.get("attention_source") or "external_instrumented_forward"),
        "correlational_only": True, "causal_claim_authorized": False,
        "region_attention_mass": dict(sorted(mass.items())),
        "normalized_region_focus": {
            region: value / float(atlas["regions"][region]["patch_share"])
            for region, value in sorted(mass.items()) if atlas["regions"][region]["patch_share"]
        },
        "required_region_attention_mass": sum(mass.get(region, 0.0) for region in required) if required else None,
        "blank_attention_mass": sum(value for patch, value in zip(patches, normalized, strict=True) if patch["blank"]),
        "normalized_attention_entropy": entropy / math.log(len(normalized)) if len(normalized) > 1 else 0.0,
        "top_10pct_patch_indices": top,
        "top_10pct_evidence_precision": sum(not patches[index]["blank"] for index in top) / len(top),
    }


def render_attention_overlay(png: bytes, artifact: Mapping[str, Any], atlas: Mapping[str, Any]) -> bytes:
    """Overlay an externally supplied attention grid on the exact source PNG."""

    attention_diagnostics(artifact, atlas)
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    columns, rows = map(int, atlas["grid"])
    values = list(map(float, artifact["weights"])); maximum = max(values) or 1.0
    for index, value in enumerate(values):
        row, column = divmod(index, columns)
        alpha = round(190 * value / maximum)
        if alpha:
            draw.rectangle(
                (round(column * image.width / columns), round(row * image.height / rows),
                 round((column + 1) * image.width / columns), round((row + 1) * image.height / rows)),
                fill=(239, 68, 68, alpha),
            )
    stream = io.BytesIO(); Image.alpha_composite(image, overlay).convert("RGB").save(stream, format="PNG")
    return stream.getvalue()


def is_rca_task(spec: ExperimentSpec) -> bool:
    return spec.task.startswith("root_cause_") or spec.task == "root_cause_ranking"


def experiment_registry(config: Mapping[str, Any]) -> dict[str, ExperimentSpec]:
    registry: dict[str, ExperimentSpec] = {}
    for name, value in config["experiments"].items():
        arms = value["arms"]
        if arms == "factorial_16_plus_P_V_H":
            arms = tuple(factorial_cells()) + ("P", "V", "H")
        registry[name] = ExperimentSpec(
            name=name,
            task=str(value["task"]),
            stages=int(value["stages"]),
            arms=tuple(map(str, arms)),
            primary_metric=str(value.get("primary_metric") or "complete_chain_accuracy"),
        )
    return registry


def dashboard_config(config: Mapping[str, Any]):
    expected = int(config["renderer"]["required_version"])
    if RENDERER_VERSION != expected:
        raise RQ1Error(f"RQ1 requires renderer-v{expected}, found v{RENDERER_VERSION}")
    return make_dashboard_config(
        config["renderer"]["preset"],
        overrides=dict(config["renderer"]["overrides"]),
        name="rq1c_renderer_v12_numeric_identity",
    )


def _entities(view: CaseRenderView) -> set[str]:
    """Exact renderer-v12 entity universe from the inherited RQ1c protocol."""

    entities = {str(value) for value in view.services if value is not None and str(value)}
    entities.update(str(value) for value in view.graph.nodes if value is not None and str(value))
    entities.update(str(series.service) for series in score_series(view.metrics_df, view.services))
    if view.logs_df is not None and "container_name" in view.logs_df:
        entities.update(str(value) for value in view.logs_df["container_name"].dropna() if str(value))
    if view.traces_df is not None and "service_name" in view.traces_df:
        entities.update(str(value) for value in view.traces_df["service_name"].dropna() if str(value))
    projected = service_level_projection(view.graph, view.metadata.get("node_pod_map"))
    entities.update(str(value) for value in projected.nodes if value is not None and str(value))
    node_pod_map = view.metadata.get("node_pod_map") or {}
    entities.update(str(value) for value in node_pod_map if value is not None and str(value))
    for pods in node_pod_map.values():
        entities.update(str(value) for value in (pods or ()) if value is not None and str(value))
    return entities


def _display_number(value: Any) -> str | None:
    """Match the compact precision used by the dashboard's visible labels."""

    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return None
    absolute = abs(number)
    if absolute >= 1e9:
        return f"{number / 1e9:.1f}G"
    if absolute >= 1e6:
        return f"{number / 1e6:.1f}M"
    if absolute >= 1e3:
        return f"{number / 1e3:.1f}k"
    if absolute >= 10:
        return f"{number:.0f}"
    if absolute >= 0.01:
        return f"{number:.2f}"
    return f"{number:.1e}"


def _display_z(value: Any) -> str | None:
    if value is None:
        return None
    number = float(value)
    return ("+" if number >= 0 else "-") + ">=999" if abs(number) >= 999 else f"{number:+.1f}"


def _display_minute(seconds: Any) -> str | None:
    if seconds is None:
        return None
    return f"{float(seconds) / 60:.1f}".rstrip("0").rstrip(".") + "m"


def _atomic_fact(region: str, field: str, payload: Mapping[str, Any], *,
                 entities: Iterable[str] = (), bins: Iterable[int] = (),
                 unit: str | None = None) -> dict[str, Any]:
    core = {
        "region": region,
        "field": field,
        "payload": dict(payload),
        "entity_ids": list(map(str, entities)),
        "relative_bins": list(map(int, bins)),
        "unit": unit,
    }
    return {"fact_id": "F" + stable_hash(core)[:16].upper(), **core}


def _metric_unit(metric_name: str) -> str:
    text = metric_name.casefold()
    if any(token in text for token in ("second", "latency", "duration")):
        return "source_time_unit"
    if any(token in text for token in ("byte", "memory", "rss", "working_set")):
        return "bytes_or_source_native"
    if any(token in text for token in ("percent", "ratio", "utilization")):
        return "ratio_or_source_native"
    if any(token in text for token in ("count", "total", "requests", "errors")):
        return "count_or_source_native"
    return "source_native"


def build_visible_rca_packet(
    ceb: Mapping[str, Any], renderer_fingerprint: str,
    rendered_metric_names: Mapping[str, str] | None = None,
    source_manifest_hash: str | None = None,
) -> dict[str, Any]:
    """Compile only semantic facts encoded by the dashboard at visible precision."""

    candidates = list(map(str, ceb.get("candidates") or ()))
    if not candidates or any(not value.isdigit() for value in candidates):
        raise RQ1Error("RCA candidates must be case-local numeric IDs")
    metrics = list(ceb.get("metric_series") or ())
    if len(metrics) != 12 or any(len(row.get("values") or ()) != 64 for row in metrics):
        raise RQ1Error("renderer-v12 RCA packet requires twelve complete 64-bin metric series")
    facts = [
        _atomic_fact("C", "candidate_set", {"fixed_order": candidates, "count": len(candidates)}, entities=candidates),
        _atomic_fact("C", "evidence_schema", {
            "schema_version": "RCAEvidencePacketV1",
            "opaque_incident_id": ceb["opaque_incident_id"],
            "selection_summary": dict(ceb.get("selection_summary") or {}),
        }),
        _atomic_fact("C", "evidence_legends", {
            "entity_ids": ENTITY_ID_NOTE,
            "directed_edges": "A directed edge caller -> callee means caller invokes callee.",
            "relative_time": "All times are relative to the observation-window start; metric sequences use 64 equal-width bins and null means missing.",
            "source_comparability": "Trace-derived and metric-derived anomaly scores use different instruments and are not directly comparable.",
        }),
        _atomic_fact("M", "observation_window", dict(ceb.get("observation_window") or {}), unit="relative_seconds"),
        _atomic_fact("M", "estimated_fault_window", {
            "fault_window_start_rel_min_display": _display_minute((ceb.get("fault_window_rel_s") or [None, None])[0]),
            "fault_window_end_rel_min_display": _display_minute((ceb.get("fault_window_rel_s") or [None, None])[1]),
        }, unit="displayed_relative_minutes"),
    ]
    for row in metrics:
        values = [_display_number(value) for value in row.get("values") or ()]
        if len(values) != 64:
            raise RQ1Error("RCA visible metric sequence must contain 64 bins")
        payload = {
            "panel_id": row.get("panel_id"), "rank": row.get("rank"),
            "service": str(row.get("service")),
            "metric": (rendered_metric_names or {}).get(str(row.get("panel_id")), str(row.get("metric"))),
            "values": values, "missing_mask": list(row.get("missing_mask") or ()),
            "baseline": _display_number(row.get("baseline")),
            "peak": _display_number(row.get("peak")), "signed_z": _display_z(row.get("signed_z")),
        }
        facts.append(_atomic_fact("M", "metric_series_64", payload,
                                  entities=(payload["service"],), bins=range(64),
                                  unit=_metric_unit(str(payload.get("metric") or ""))))
    for region, summary_name, field in (
        ("L", "log_summary", "log_summary_entry"),
        ("R", "trace_summary", "trace_summary_entry"),
    ):
        summary = dict(ceb.get(summary_name) or {})
        facts.append(_atomic_fact(region, summary_name + "_meta", {
            key: value for key, value in summary.items() if key != "entries"
        }))
        for index, source in enumerate(summary.get("entries") or ()):
            payload = {"entry_index": index, **dict(source)}
            payload.pop("rendered_service", None)
            if region == "L":
                for key in ("error_pct", "change_pct"):
                    if payload.get(key) is not None:
                        payload[key] = f"{float(payload[key]):.1f}"
            else:
                payload.pop("spans", None)
                for key in ("p95_pre_ms", "p95_during_ms"):
                    payload[key] = _display_number(payload.get(key))
                if payload.get("delta_pct") is not None:
                    payload["delta_pct"] = f"{float(payload['delta_pct']):.0f}"
                if payload.get("error_pct") is not None:
                    payload["error_pct"] = f"{float(payload['error_pct']):.1f}"
            entity = str(payload.get("service") or "")
            facts.append(_atomic_fact(
                region, field, payload, entities=(entity,) if entity else (),
                unit="count_and_fraction" if region == "L" else "milliseconds_and_fraction",
            ))
    propagation = dict(ceb.get("propagation") or {})
    facts.append(_atomic_fact("G", "propagation_meta", {
        key: propagation.get(key) for key in ("mode", "omitted_services", "omitted_edges")
    }))
    for source in propagation.get("services") or ():
        payload = dict(source)
        payload["onset_rel_min_display"] = _display_minute(payload.pop("onset_rel_s", None))
        payload["severity_z_display"] = _display_z(payload.pop("severity_z", None))
        payload["evidence_source_display"] = {"trace": "T", "metric": "M"}.get(
            str(payload.pop("evidence_source", "none")), "none")
        entity = str(payload.get("service"))
        facts.append(_atomic_fact("G", "propagation_service", payload, entities=(entity,),
                                  unit="displayed_minutes_and_z_source"))
    for index, edge in enumerate(propagation.get("directed_call_edges") or ()):
        payload = {"edge_index": index, "caller": str(edge["caller"]), "callee": str(edge["callee"])}
        facts.append(_atomic_fact("G", "directed_call_edge", payload,
                                  entities=(payload["caller"], payload["callee"])))
    missing = dict(ceb.get("missingness") or {})
    for region, key in (("L", "logs_missing"), ("R", "traces_missing"), ("G", "propagation_missing")):
        facts.append(_atomic_fact(region, "explicit_missingness", {key: bool(missing.get(key))}))
    facts = sorted(facts, key=lambda fact: (fact["region"], fact["field"], fact["fact_id"]))
    inventory = stable_hash(facts)
    packet = {
        "schema_version": "RCAEvidencePacketV1", "opaque_incident_id": ceb["opaque_incident_id"],
        "candidates": candidates, "facts": facts,
        "source_manifest_hash": source_manifest_hash or stable_hash(ceb),
        "renderer_fingerprint": renderer_fingerprint, "fact_inventory_hash": inventory,
    }
    packet["packet_hash"] = stable_hash(packet)
    return packet


def packet_regions(packet: Mapping[str, Any], regions: Iterable[str]) -> list[dict[str, Any]]:
    wanted = set(regions)
    return [dict(fact) for fact in packet["facts"] if str(fact["region"]) in wanted]


def _prompt_packet_regions(
    packet: Mapping[str, Any], regions: Iterable[str] = PROMPT_REGION_ORDER,
) -> list[dict[str, Any]]:
    """Return facts in the registered SIRCL* prompt order, without changing facts."""

    wanted = set(regions)
    rank = {region: index for index, region in enumerate(PROMPT_REGION_ORDER)}
    selected = packet_regions(packet, wanted)
    return sorted(
        selected,
        key=lambda fact: (
            rank.get(str(fact["region"]), len(rank)),
            str(fact["field"]),
            str(fact["fact_id"]),
        ),
    )


def _natural_fact_line(fact: Mapping[str, Any]) -> str:
    names = {
        "M": "Metric/time evidence", "L": "Log evidence",
        "R": "Trace evidence", "G": "Directed-topology evidence",
    }
    return (
        f"{names.get(str(fact['region']), 'Incident evidence')}; field={fact['field']}; "
        f"entities={canonical_json(fact['entity_ids'])}; "
        f"relative_bins={canonical_json(fact['relative_bins'])}; "
        f"unit={canonical_json(fact.get('unit'))}; details={canonical_json(fact['payload'])}"
    )


def _packet_text(packet: Mapping[str, Any], regions: Iterable[str] = REGIONS) -> str:
    selected = tuple(regions)
    heading = ("=== COMPLETE INCIDENT EVIDENCE B ===" if set(selected) == set(REGIONS)
               else "=== ROUTED LOG AND TRACE EVIDENCE ===" if set(selected) == {"L", "R"}
               else "=== INCIDENT EVIDENCE TEXT FRAGMENTS ===")
    lines = [heading]
    lines.extend(_natural_fact_line(fact) for fact in _prompt_packet_regions(packet, selected))
    return "\n".join(lines) + "\n"


def _packet_text_lines_by_region(packet: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """Return the exact T-arm natural-language fact lines, partitioned by region.

    The pixel-text control consumes this function so it cannot silently drift
    onto the flat JSONL serializer or a second natural-language summary.
    """

    return {
        region: tuple(
            _natural_fact_line(fact) for fact in _prompt_packet_regions(packet, (region,))
        )
        for region in REGIONS
    }


def _packet_text_region_blocks(
    packet: Mapping[str, Any],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Preserve the exact T-arm line order while adding M/L/R/G headings."""

    blocks: list[tuple[str, list[str]]] = []
    for fact in _prompt_packet_regions(packet, PROMPT_REGION_ORDER):
        region = str(fact["region"])
        if not blocks or blocks[-1][0] != region:
            blocks.append((region, []))
        blocks[-1][1].append(_natural_fact_line(fact))
    return tuple((region, tuple(lines)) for region, lines in blocks)


def _qa_incident_text(
    packet: Mapping[str, Any], regions: Iterable[str] = PROMPT_REGION_ORDER,
) -> str:
    """Return only the frozen Q&A incident-fact lines in M/R/L/G order."""

    return "\n".join(
        _natural_fact_line(fact) for fact in _prompt_packet_regions(packet, regions)
    ) + "\n"


def _packet_flat_records(packet: Mapping[str, Any]) -> list[tuple[str, str]]:
    facts = _prompt_packet_regions(packet, PROMPT_REGION_ORDER)
    return [
        (str(fact["region"]), canonical_json({
            "line_index": index,
            **{key: fact[key] for key in ("region", "field", "payload", "entity_ids", "relative_bins", "unit")},
        }) + "\n")
        for index, fact in enumerate(facts)
    ]


def _packet_flat(packet: Mapping[str, Any]) -> str:
    return "".join(line for _region, line in _packet_flat_records(packet))


def build_qa_packet(rca_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Index the renderer-v12 incident facts once for every formal Q&A arm."""

    facts = [dict(fact) for fact in _prompt_packet_regions(rca_packet, PROMPT_REGION_ORDER)]
    if not any(fact["field"] == "directed_call_edge" for fact in facts):
        # Renderer-v12 prints this absence explicitly in the directed-edge key.
        # Give T/P the same visible fact instead of treating an empty edge list
        # as either an eligibility failure or an implicit hidden value.
        facts.append(_atomic_fact("G", "directed_edge_key_status", {"status": "none"}))
        facts = _prompt_packet_regions({"facts": facts}, PROMPT_REGION_ORDER)
    lines = [_natural_fact_line(fact) for fact in facts]
    primitive = {
        "M": "metric_panel_or_relative_time_axis", "R": "R1_visible_trace_table",
        "L": "G1_visible_log_table", "G": "propagation_panel_or_directed_edge_key",
    }
    mappings = {
        fact["fact_id"]: {
            "T_QA": {"source_line": index + 1, "text_sha256": stable_hash(lines[index])},
            "P_QA": {"source_line": index + 1, "image_primitive": "lossless_wrapped_text_line"},
            "V_QA": {"renderer_primitive": primitive[str(fact["region"])],
                     "visible_record_key": _public_record_key(fact)},
            "factorial_region": str(fact["region"]),
        }
        for index, fact in enumerate(facts)
    }
    packet = {
        "schema_version": "QAEvidenceIndexV1",
        "opaque_incident_id": rca_packet["opaque_incident_id"],
        "facts": facts, "fact_mappings": mappings,
        "fact_inventory_hash": stable_hash(facts),
        "entity_inventory": sorted({str(value) for fact in facts for value in fact.get("entity_ids") or ()}),
        "edge_inventory": sorted(
            f"{fact['payload']['caller']}->{fact['payload']['callee']}"
            for fact in facts if fact["field"] == "directed_call_edge"
        ),
        "equality_dimensions": ["numeric_entity_id", "metric_64_bin_display", "missingness",
                                "unit", "display_precision", "log", "trace", "directed_edge",
                                "relative_time", "legend_in_common_prompt"],
    }
    packet["evidence_text_sha256"] = stable_hash(_qa_incident_text(packet))
    packet["packet_hash"] = stable_hash(packet)
    return packet


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def _wrap_visible_line(draw: ImageDraw.ImageDraw, line: str, font: ImageFont.ImageFont,
                       max_width: int) -> list[str]:
    """Losslessly wrap one evidence line to its measured on-canvas width."""

    remaining = line
    output: list[str] = []
    while remaining:
        if draw.textlength(remaining, font=font) <= max_width:
            output.append(remaining)
            break
        low, high = 1, len(remaining)
        while low < high:
            midpoint = (low + high + 1) // 2
            if draw.textlength(remaining[:midpoint], font=font) <= max_width:
                low = midpoint
            else:
                high = midpoint - 1
        if low < 1:
            raise RQ1Error("pixel-text font cannot fit one character")
        output.append(remaining[:low])
        remaining = remaining[low:]
    return output or [""]


def compile_pixel_text_pages(packet: Mapping[str, Any]) -> tuple[bytes, ...]:
    """Render the T-arm natural-language facts into deterministic M/L/R/G pages.

    This intentionally simple transport is the ``P`` pseudo-dashboard arm. It
    contains the same incident-evidence semantics as ``T`` and must never be
    described as the real renderer-v12 telemetry dashboard.
    """

    width, height, margin, line_height = 1800, 1600, 32, 24
    font = _font(17)
    title_font = _font(22, bold=True)
    titles = {"M": "M — METRICS", "L": "L — LOGS", "R": "R — TRACES", "G": "G — TOPOLOGY"}
    page_capacity = (height - 3 * margin - 32) // line_height
    pages: list[bytes] = []
    source_text = _qa_incident_text(packet)
    for region, source_lines in _packet_text_region_blocks(packet):
        probe = Image.new("RGB", (width, height), "white")
        probe_draw = ImageDraw.Draw(probe)
        wrapped: list[str] = []
        for line in source_lines:
            wrapped.extend(_wrap_visible_line(probe_draw, line, font, width - 2 * margin))
        for start in range(0, len(wrapped), page_capacity):
            image = Image.new("RGB", (width, height), "#FFFFFF")
            draw = ImageDraw.Draw(image)
            draw.text((margin, margin), titles[region], fill="#102027", font=title_font)
            for row, line in enumerate(wrapped[start:start + page_capacity]):
                draw.text((margin, 2 * margin + 24 + row * line_height), line, fill="#111827", font=font)
            stream = io.BytesIO()
            image.save(stream, format="PNG", optimize=False, compress_level=6)
            pages.append(stream.getvalue())
    if not pages or len(pages) > 8:
        raise RQ1Error(f"pixel-text transport requires {len(pages)} pages; expected 1..8")
    if stable_hash(source_text) != packet.get("evidence_text_sha256", stable_hash(source_text)):
        raise RQ1Error("pixel-text source differs from the frozen T_QA evidence fragment")
    return tuple(pages)


def _qa_text(packet: Mapping[str, Any], regions: Iterable[str] = PROMPT_REGION_ORDER) -> str:
    return _qa_incident_text(packet, regions)


def _routed_image(png: bytes, manifest: Mapping[str, Any], config: Any) -> bytes:
    """Neutralize log/trace regions; retain metric and topology pixels."""

    kinds = {str(panel.get("kind")) for panel in manifest.get("panels", ())}
    required = {"metric", "propagation", "logs", "traces", "direct_identity_edge_key"}
    if not required <= kinds:
        raise RQ1Error(f"routed source lacks required visible regions: {sorted(required - kinds)}")
    image = Image.open(io.BytesIO(png)).convert("RGB")
    width, height = image.size
    base_height = int(config.long_side_px * config.canvas_aspect)
    left, top = round(width * 0.746), round(base_height * 0.542)
    draw = ImageDraw.Draw(image)
    draw.rectangle((left, top, width, base_height), fill="#F8FAFC")
    mid = top + (base_height - top) // 2
    placeholder_font = _font(18, bold=True)
    draw.text((left + 18, top + 18), "LOGS — EVIDENCE IN TEXT", fill="#37474F", font=placeholder_font)
    draw.text((left + 18, mid + 18), "TRACES — EVIDENCE IN TEXT", fill="#37474F", font=placeholder_font)
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=6)
    return output.getvalue()


def _neutral_image(png: bytes, config: Any) -> bytes:
    """Preserve registered canvas geometry while removing incident evidence."""

    source = Image.open(io.BytesIO(png)).convert("RGB")
    image = Image.new("RGB", source.size, "#F8FAFC")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    base = int(config.long_side_px * config.canvas_aspect)
    draw.text((24, 20), "NEUTRAL SHAM — FIXED LAYOUT, NO INCIDENT-SPECIFIC EVIDENCE", fill="#37474F", font=_font(18, bold=True))
    split = round(width * 0.746)
    for row in range(4):
        for column in range(3):
            x1, x2 = 20 + column * (split - 30) // 3, 15 + (column + 1) * (split - 30) // 3
            y1, y2 = 70 + row * (base - 90) // 4, 65 + (row + 1) * (base - 90) // 4
            draw.rectangle((x1, y1, x2, y2), outline="#CFD8DC", width=2, fill="#FFFFFF")
            draw.line((x1 + 20, (y1 + y2) // 2, x2 - 20, (y1 + y2) // 2), fill="#B0BEC5", width=2)
    draw.rectangle((split + 10, 70, width - 18, base - 15), outline="#CFD8DC", width=2, fill="#FFFFFF")
    if height > base:
        draw.rectangle((20, base + 10, width - 18, height - 12), outline="#CFD8DC", width=2, fill="#FFFFFF")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=6)
    return output.getvalue()


def _visual_score_rows(ceb: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Frozen label-blind evidence/degree score for counterfactual selection."""

    panel_count: dict[str, int] = {}
    max_z: dict[str, float] = {}
    for row in ceb.get("metric_series") or ():
        entity = str(row.get("service"))
        panel_count[entity] = panel_count.get(entity, 0) + 1
        try:
            max_z[entity] = max(max_z.get(entity, 0.0), min(20.0, abs(float(row.get("signed_z") or 0.0))))
        except (TypeError, ValueError):
            pass
    degree: dict[str, int] = {}
    for edge in (ceb.get("propagation") or {}).get("directed_call_edges") or ():
        for entity in (str(edge["caller"]), str(edge["callee"])):
            degree[entity] = degree.get(entity, 0) + 1
    onset = {str(row.get("service")): row.get("onset_rel_s")
             for row in (ceb.get("propagation") or {}).get("services") or ()}
    entities = sorted(set(panel_count) | set(degree) | set(onset))
    rows = []
    for entity in entities:
        early = 0.0 if onset.get(entity) is None else 1.0 / (1.0 + max(0.0, float(onset[entity])))
        rows.append({
            "entity": entity, "panel_count": panel_count.get(entity, 0),
            "degree": degree.get(entity, 0), "max_abs_z": max_z.get(entity, 0.0),
            "score": panel_count.get(entity, 0) + degree.get(entity, 0) + max_z.get(entity, 0.0) / 10 + early,
        })
    return sorted(rows, key=lambda row: (-row["score"], row["entity"]))


def _counterfactual_pairs(ceb: Mapping[str, Any]) -> dict[str, Any]:
    candidate_ids = set(map(str, ceb.get("candidates") or ()))
    rows = [row for row in _visual_score_rows(ceb) if row["entity"] in candidate_ids]
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[len(str(row["entity"]))].append(row)
    eligible_groups = [group for group in groups.values() if len(group) >= 4]
    if not eligible_groups:
        return {"eligible": False, "reason": "fewer_than_four_same_granularity_candidate_visual_entities",
                "scores": rows, "all_pairs_candidate_scoped": True}
    rows = min(eligible_groups, key=lambda group: (-len(group), len(str(group[0]["entity"]))))
    targeted = (rows[0]["entity"], rows[-1]["entity"])
    weak = rows[max(1, len(rows) // 2):]
    pair_candidates = []
    for left, right in itertools.combinations(weak, 2):
        if {left["entity"], right["entity"]} == set(targeted):
            continue
        distance = (abs(left["score"] - right["score"])
                    + abs(left["panel_count"] - right["panel_count"])
                    + abs(left["degree"] - right["degree"]))
        pair_candidates.append((distance, left["entity"], right["entity"]))
    if not pair_candidates:
        return {"eligible": False, "reason": "no_matched_weak_placebo_pair", "scores": rows}
    _, left, right = min(pair_candidates)
    selected = [*targeted, left, right]
    if any(entity not in candidate_ids for entity in selected) or len({len(entity) for entity in selected}) != 1:
        raise RQ1Error("counterfactual pairs escaped candidate/granularity scope")
    return {"eligible": True, "targeted": list(targeted), "placebo": [left, right], "scores": rows,
            "all_pairs_candidate_scoped": True, "same_granularity": True}


def _qa_display_mapping(
    view: CaseRenderView, mapping: Mapping[str, str], opaque_id: str,
) -> tuple[dict[str, str], dict[str, str]]:
    """Extend, never rewrite, frozen IDs for renderer-created service aliases.

    Renderer-v12 projects pod-level topology names to services. Those projected
    names are not always present in the original entity universe, so the RCA
    renderer historically fell back to a natural service label in rare rows.
    Q&A must keep the RCA artifacts unchanged while still satisfying its
    numeric-identity contract; add deterministic unused three-digit IDs only
    for those Q&A renderer aliases.
    """

    extended = dict(mapping)
    aliases = sorted({pod_to_service(value) for value in _entities(view)} - set(extended))
    used = set(extended.values())
    available = [str(value) for value in range(100, 1000) if str(value) not in used]
    available.sort(key=lambda value: stable_hash(f"{opaque_id}:qa-service-alias:{value}"))
    if len(aliases) > len(available):
        raise RQ1Error("Q&A service-alias identity space is exhausted")
    kinds = {}
    for alias, numeric in zip(aliases, available, strict=False):
        extended[alias] = numeric
        kinds[alias] = "service"
    return extended, kinds


def prepare_case(dataset: str, case_id: str, config: Mapping[str, Any]) -> PreparedCase:
    """Compile label-blind RCA/Q&A packets and images, then open labels privately."""

    case = load_processed_case(dataset, case_id)
    view = CaseRenderView.from_case(case)
    # Preserve the exact renderer-v12 presentation identity. Dataset-split
    # roster identifiers remain a separate unified-selection concern.
    opaque_id = opaque_incident_id(case_id)
    mapping, granularities = numeric_entity_map(_entities(view), opaque_id, int(config["seed"]))
    numeric_view = replace(view, entity_display_labels=mapping)
    renderer_cfg = dashboard_config(config)
    full_png, manifest = compile_dashboard(numeric_view, renderer_cfg)
    ceb = build_canonical_evidence(manifest)
    rca_packet = build_visible_rca_packet(
        ceb, str(manifest["config_fingerprint"]),
        source_manifest_hash=stable_hash(manifest),
    )
    qa_mapping, qa_extra_granularities = _qa_display_mapping(view, mapping, opaque_id)
    qa_full_png, qa_manifest = compile_dashboard(
        replace(view, entity_display_labels=qa_mapping), renderer_cfg,
    )
    if qa_manifest.get("config_fingerprint") != manifest.get("config_fingerprint"):
        raise RQ1Error("Q&A renderer-v12 configuration differs from the RCA renderer")
    qa_ceb = build_canonical_evidence(qa_manifest)
    qa_packet = build_qa_packet(build_visible_rca_packet(
        qa_ceb, str(qa_manifest["config_fingerprint"]),
        source_manifest_hash=stable_hash(qa_manifest),
    ))
    pixel_text_pngs = compile_pixel_text_pages(qa_packet)
    qa_region_pngs, qa_crop_audit = crop_dashboard_evidence_regions(qa_full_png, renderer_cfg)
    routed_png = _routed_image(full_png, manifest, renderer_cfg)
    inverse = {numeric: natural for natural, numeric in mapping.items()}

    def swapped_png(left: str, right: str) -> bytes:
        if left == right or left not in inverse or right not in inverse:
            raise RQ1Error("counterfactual pair is not a valid numeric-identity swap")
        swapped = dict(mapping)
        swapped[inverse[left]], swapped[inverse[right]] = right, left
        image, changed_manifest = compile_dashboard(replace(view, entity_display_labels=swapped), renderer_cfg)
        if changed_manifest.get("config_fingerprint") != manifest.get("config_fingerprint"):
            raise RQ1Error("counterfactual renderer configuration drifted")
        if stable_hash(image) == stable_hash(full_png):
            raise RQ1Error("counterfactual swap produced a factual no-op image")
        return image

    selection = _counterfactual_pairs(ceb)
    variants = {"neutral": _neutral_image(full_png, renderer_cfg)}
    if selection["eligible"]:
        variants["targeted"] = swapped_png(*selection["targeted"])
        variants["placebo"] = swapped_png(*selection["placebo"])
        if stable_hash(variants["targeted"]) == stable_hash(variants["placebo"]):
            raise RQ1Error("targeted and placebo counterfactual images are identical")
    base_ratio = min(1.0, int(renderer_cfg.long_side_px * renderer_cfg.canvas_aspect) / Image.open(io.BytesIO(full_png)).height)
    font_size = float(config["renderer"]["overrides"]["uniform_detail_font_pt"])
    visual_atlases = {
        "full": visual_patch_atlas(full_png, layout="dashboard", dashboard_base_ratio=base_ratio,
                                   font_point_size=font_size),
        "qa_full": visual_patch_atlas(qa_full_png, layout="dashboard", dashboard_base_ratio=base_ratio,
                                       font_point_size=font_size),
        "routed": visual_patch_atlas(routed_png, layout="dashboard", dashboard_base_ratio=base_ratio,
                                     font_point_size=font_size),
        "qa_regions": {
            region: [visual_patch_atlas(value, layout=f"crop_{region}", font_point_size=font_size)
                     for value in pages]
            for region, pages in qa_region_pngs.items()
        },
        "pixel_text": [
            visual_patch_atlas(value, layout="pixel_text", font_point_size=17.0)
            for value in pixel_text_pngs
        ],
        **{
            name: visual_patch_atlas(value, layout="dashboard", dashboard_base_ratio=base_ratio,
                                     font_point_size=font_size)
            for name, value in variants.items()
        },
    }
    legacy_questions, reasoning_questions = questions_for_case(qa_packet, opaque_id)
    public = {
        "schema_version": "RQ1PreparedCaseV6",
        "opaque_incident_id": opaque_id,
        "renderer_version": RENDERER_VERSION,
        "rca_packet": rca_packet,
        "qa_packet": qa_packet,
        "legacy_questions": [question.public() for question in legacy_questions],
        "reasoning_questions": [question.public() for question in reasoning_questions],
        "counterfactual": {key: value for key, value in selection.items() if key not in {"targeted", "placebo"}},
        "full_image_sha256": stable_hash(full_png),
        "qa_full_image_sha256": stable_hash(qa_full_png),
        "routed_image_sha256": stable_hash(routed_png),
        "pixel_text_image_sha256": [stable_hash(value) for value in pixel_text_pngs],
        "qa_region_image_sha256": {
            region: [stable_hash(value) for value in pages]
            for region, pages in qa_region_pngs.items()
        },
        "qa_region_crop_audit": qa_crop_audit,
        "representation_roles": {
            "V": "unchanged_rca_renderer_v12_real_telemetry_dashboard",
            "V_QA": "renderer_v12_real_telemetry_dashboard_with_complete_numeric_aliases",
            "P_QA": "exact_T_QA_pixel_text_pseudo_dashboard",
            "T_QA": "native_incident_fact_text",
            "H_QA": "strict_V_QA_image_then_exact_T_QA_text",
            "factorial_visual": "renderer_v12_source_crops",
            "controlled_canvas": "archived_diagnostic_only_not_generated",
        },
        "variant_image_sha256": {name: stable_hash(value) for name, value in variants.items()},
        "visual_evidence_atlases": visual_atlases,
    }
    # Only after every visible packet/image and its equality audit exist may the
    # evaluator-private half be opened for scoring.
    public["representation_audit"] = audit_representation_equality(
        rca_packet, qa_packet, full_png, qa_full_png, routed_png, pixel_text_pngs, qa_region_pngs,
        *variants.values()
    )
    evaluator = load_processed_private(dataset, case_id)
    labels = dict(evaluator.get("labels") or {})
    accepted = [str(labels.get("root_cause") or "")]
    accepted.extend(map(str, labels.get("root_cause_candidates") or ()))
    private = {
        "schema_version": "RQ1PrivateEvaluatorV2",
        "opaque_incident_id": opaque_id,
        "dataset": dataset,
        "fault_type": str(labels.get("fault_type") or evaluator.get("fault_type")
                          or (evaluator.get("event") or {}).get("fault_type") or "unknown"),
        "source_case_id": case_id,
        "numeric_to_natural": {numeric: natural for natural, numeric in mapping.items()},
        "qa_numeric_to_natural": {numeric: natural for natural, numeric in qa_mapping.items()},
        "entity_granularity": granularities,
        "qa_extra_entity_granularity": qa_extra_granularities,
        "accepted_labels": sorted(set(filter(None, accepted))),
        "legacy_questions": [question.private() for question in legacy_questions],
        "reasoning_questions": [question.private() for question in reasoning_questions],
        "counterfactual_pairs": {
            "eligible": bool(selection["eligible"]),
            "targeted": list(selection.get("targeted") or ()),
            "placebo": list(selection.get("placebo") or ()),
            "selector_audit": selection,
        },
    }
    private_markers = (
        case_id, dataset, labels.get("root_cause"),
        (evaluator.get("event") or {}).get("absolute_timestamp"),
        (case.metadata or {}).get("processed_path"),
    )
    # Preserve the inherited RCA audit scope while making the corrected Q&A
    # contract fail closed on every renderer-created service alias as well.
    audit_visible(public, (*private_markers, *mapping.keys()))
    audit_visible({
        "qa_packet": qa_packet,
        "legacy_questions": public["legacy_questions"],
        "reasoning_questions": public["reasoning_questions"],
    }, (*private_markers, *qa_mapping.keys()))
    return PreparedCase(public=public, private=private, full_png=full_png, qa_full_png=qa_full_png,
                        routed_png=routed_png, pixel_text_pngs=pixel_text_pngs,
                        qa_region_pngs=qa_region_pngs, variant_pngs=variants)


def common_shell(packet: Mapping[str, Any]) -> str:
    lines = [
        "You are diagnosing one microservice incident from label-blind telemetry.",
        "Use only the supplied evidence and the exhaustive candidate IDs below.",
        "Candidate IDs in fixed order: " + canonical_json(packet["candidates"]),
        "A directed edge A -> B means A calls B; symptoms can propagate from B back to A.",
        "Times are relative to t=0; null means an explicitly missing observation.",
        ENTITY_ID_NOTE,
    ]
    lines.extend(
        f"Common evidence ({fact['field']}): {canonical_json(fact['payload'])}"
        for fact in packet["facts"] if fact["region"] == "C"
    )
    return "\n".join(lines) + "\n"


def visual_diagnostic_for_arm(arm: str, task: str, public: Mapping[str, Any]) -> dict[str, Any]:
    """Return a small, no-extra-call visual profile for one existing arm."""

    atlases = public.get("visual_evidence_atlases") or {}
    if task in {"direct_visops", "cross_region_reasoning"}:
        if arm == "P":
            values = list(atlases.get("pixel_text") or ())
            return {"image_count": len(values), "image_role": "pixel_text_pseudo_dashboard",
                    "atlas_sha256": [value["atlas_sha256"] for value in values],
                    "visual_regions": [], "attention_status": "required_same_prefill_probe_pending"}
        if arm in {"V", "H"}:
            atlas = atlases["qa_full"]
            return {"image_count": 1, "image_role": "renderer_v12_real_dashboard",
                    "atlas_sha256": atlas["atlas_sha256"], "visual_regions": list(REGIONS),
                    "blank_patch_fraction": atlas["blank_patch_fraction"],
                    "evidence_patch_fraction": atlas["evidence_patch_fraction"],
                    "attention_status": "required_same_prefill_probe_pending"}
        visual = tuple(region for region in REGIONS if region in _cell_visual_regions(arm))
        if not visual:
            return {"image_count": 0, "visual_regions": [], "attention_status": "not_applicable_text_only"}
        selected = [atlas for region in visual for atlas in atlases["qa_regions"][region]]
        return {
            "image_count": len(selected), "image_role": "renderer_v12_region_crops",
            "atlas_sha256": [atlas["atlas_sha256"] for atlas in selected],
            "visual_regions": list(visual),
            "blank_patch_fraction": sum(atlas["blank_patch_fraction"] for atlas in selected) / len(selected),
            "attention_status": "required_same_prefill_probe_pending",
        }
    if arm == "P":
        pixel_atlases = list(atlases.get("pixel_text") or ())
        return {
            "image_count": len(pixel_atlases),
            "image_role": "pixel_text_pseudo_dashboard",
            "atlas_sha256": [value["atlas_sha256"] for value in pixel_atlases],
            "blank_patch_fraction": (
                sum(value["blank_patch_fraction"] for value in pixel_atlases) / len(pixel_atlases)
                if pixel_atlases else None
            ),
            "attention_status": "required_same_prefill_probe_pending",
        }
    role = {
        "V": "full", "H": "full", "R": "routed", "H_factual": "full",
        "H_targeted": "targeted", "H_placebo": "placebo", "H_neutral": "neutral",
    }.get(arm)
    if role is None:
        return {
            "image_count": int(arm in {"L_vis", "L_hyb"}), "image_role": "dynamic_ledger" if arm in {"L_vis", "L_hyb"} else None,
            "attention_status": "required_same_prefill_probe_pending" if arm in {"L_vis", "L_hyb"} else "not_applicable_text_only",
        }
    atlas = atlases[role]
    return {
        "image_count": 1, "image_role": role, "atlas_sha256": atlas["atlas_sha256"],
        "blank_patch_fraction": atlas["blank_patch_fraction"],
        "evidence_patch_fraction": atlas["evidence_patch_fraction"],
        "mean_ink_fraction": atlas["mean_ink_fraction"],
        "font_point_size": atlas["font_point_size"],
        "region_evidence_patch_fraction": {
            region: row["evidence_patch_fraction"] for region, row in atlas["regions"].items()
        },
        "attention_status": "required_same_prefill_probe_pending",
    }


def factorial_cells() -> list[str]:
    return [
        "-".join(f"{region}{'v' if bit else 't'}" for region, bit in zip(REGIONS, bits, strict=True))
        for bits in itertools.product((False, True), repeat=4)
    ]


def _cell_visual_regions(cell: str) -> set[Region]:
    values: set[Region] = set()
    for item in cell.split("-"):
        if len(item) == 2 and item[1] == "v" and item[0] in REGIONS:
            values.add(item[0])  # type: ignore[arg-type]
    return values


def balanced_arm_order(arms: Sequence[str], opaque_id: str, experiment: str) -> tuple[str, ...]:
    """Deterministic cyclic Latin-square order with balanced reversal."""

    values = tuple(arms)
    digest = int(stable_hash(f"{experiment}:{opaque_id}:arm-order"), 16)
    shift = digest % len(values)
    ordered = values[shift:] + values[:shift]
    return tuple(reversed(ordered)) if (digest // len(values)) % 2 else ordered


def representation_parts(
    arm: str,
    packet: Mapping[str, Any],
    full_png: bytes,
    routed_png: bytes,
    config: Mapping[str, Any],
    variants: Mapping[str, bytes] | None = None,
    pixel_text_pngs: Sequence[bytes] = (),
) -> list[dict[str, Any]]:
    """Compose one equal-fact arm; H is strictly image A followed by text B."""

    text_b = _packet_text(packet)
    shell = common_shell(packet)
    if arm == "T":
        incident = [text_part(text_b)]
    elif arm == "F":
        incident = [text_part(_packet_flat(packet))]
    elif arm == "V":
        incident = [image_part(full_png)]
    elif arm == "P":
        pages = tuple(pixel_text_pngs) or compile_pixel_text_pages(packet)
        incident = [image_part(page) for page in pages]
    elif arm == "H":
        incident = [image_part(full_png), text_part(text_b)]
    elif arm == "R":
        incident = [image_part(routed_png), text_part(_packet_text(packet, ("L", "R")))]
    elif arm == "H_factual":
        incident = [image_part(full_png), text_part(text_b)]
    elif arm in {"H_targeted", "H_placebo", "H_neutral"}:
        key = arm.removeprefix("H_")
        if not variants or key not in variants:
            raise RQ1Error(f"missing counterfactual image {key!r}")
        incident = [image_part(variants[key]), text_part(text_b)]
    else:
        raise RQ1Error(f"unknown RQ1 arm {arm!r}")
    return [*incident, text_part(shell)]


def qa_representation_parts(
    arm: str, packet: Mapping[str, Any], full_png: bytes,
    pixel_text_pngs: Sequence[bytes], region_pngs: Mapping[str, Sequence[bytes]],
) -> list[dict[str, Any]]:
    """Compile formal T/P/V/H and actual renderer-crop factorial Q&A arms."""

    text = _qa_text(packet)
    all_text, all_visual = "Mt-Rt-Lt-Gt", "Mv-Rv-Lv-Gv"
    if arm in {"T", all_text}:
        return [text_part(text)]
    if arm == "P":
        return [image_part(page) for page in pixel_text_pngs]
    if arm == "V":
        return [image_part(full_png)]
    if arm == "H":
        return [image_part(full_png), text_part(text)]
    if arm not in factorial_cells():
        raise RQ1Error(f"unknown Q&A arm {arm!r}")
    visual = set(_cell_visual_regions(arm))
    textual = [region for region in REGIONS if region not in visual]
    parts = [
        image_part(page) for region in REGIONS if region in visual
        for page in region_pngs.get(region, ())
    ]
    if visual and not parts:
        raise RQ1Error(f"Q&A factorial arm {arm} has no renderer-v12 crop")
    if textual:
        parts.append(text_part(_qa_text(packet, textual)))
    if arm == all_visual and any(part["type"] != "image" for part in parts):
        raise RQ1Error("all-visual factorial cell contains nonvisual incident evidence")
    return parts


def audit_representation_equality(rca_packet: Mapping[str, Any], qa_packet: Mapping[str, Any],
                                  full_png: bytes, qa_full_png: bytes, routed_png: bytes,
                                  pixel_text_pngs: Sequence[bytes],
                                  region_pngs: Mapping[str, Sequence[bytes]],
                                  *variants: bytes) -> dict[str, Any]:
    facts = list(rca_packet["facts"])
    inventory = stable_hash(facts)
    if inventory != rca_packet.get("fact_inventory_hash"):
        raise RQ1Error("RCA packet fact inventory hash drifted")
    qfacts = list(qa_packet["facts"])
    if stable_hash(qfacts) != qa_packet.get("fact_inventory_hash"):
        raise RQ1Error("Q&A packet fact inventory hash drifted")
    if Image.open(io.BytesIO(full_png)).size != Image.open(io.BytesIO(routed_png)).size:
        raise RQ1Error("routed image geometry differs from the full dashboard")
    if any(Image.open(io.BytesIO(value)).size != Image.open(io.BytesIO(full_png)).size for value in variants):
        raise RQ1Error("counterfactual image geometry differs from the factual dashboard")
    if not pixel_text_pngs or len(pixel_text_pngs) > 8 or any(
        not value.startswith(b"\x89PNG\r\n\x1a\n") for value in pixel_text_pngs
    ):
        raise RQ1Error("pixel-text transport is not a bounded PNG sequence")
    if set(region_pngs) != set(REGIONS) or any(
        not pages or any(not value.startswith(b"\x89PNG\r\n\x1a\n") for value in pages)
        for pages in region_pngs.values()
    ):
        raise RQ1Error("renderer-v12 Q&A region crops are incomplete")
    qa_t = qa_representation_parts("T", qa_packet, qa_full_png, pixel_text_pngs, region_pngs)
    qa_p = qa_representation_parts("P", qa_packet, qa_full_png, pixel_text_pngs, region_pngs)
    qa_v = qa_representation_parts("V", qa_packet, qa_full_png, pixel_text_pngs, region_pngs)
    qa_h = qa_representation_parts("H", qa_packet, qa_full_png, pixel_text_pngs, region_pngs)
    if qa_h != [*qa_v, *qa_t]:
        raise RQ1Error("Q&A H is not strict image-first A+B")
    if qa_v != [image_part(qa_full_png)] or qa_p != [image_part(page) for page in pixel_text_pngs]:
        raise RQ1Error("Q&A V/P transport differs from renderer-v12/exact-T sources")
    for cell in factorial_cells():
        qa_representation_parts(cell, qa_packet, qa_full_png, pixel_text_pngs, region_pngs)
    rca_text_b = _packet_text(rca_packet).encode()
    qa_text_b = _qa_text(qa_packet).encode()
    t_fact_lines = tuple(qa_text_b.decode().splitlines())
    pixel_fact_lines = tuple(
        line for _region, lines in _packet_text_region_blocks(qa_packet)
        for line in lines
    )
    pixel_source_lines = pixel_fact_lines
    if pixel_source_lines != t_fact_lines:
        raise RQ1Error("pixel-text source is not the exact T-arm natural-language fact sequence")
    if stable_hash(_qa_text(qa_packet)) != qa_packet.get("evidence_text_sha256"):
        raise RQ1Error("T_QA differs from the canonical incident-evidence fragment")
    if set(qa_packet.get("fact_mappings") or ()) != {fact["fact_id"] for fact in qfacts}:
        raise RQ1Error("Q&A fact-to-representation index is incomplete")
    h_parts = representation_parts("H", rca_packet, full_png, routed_png, {}, {})
    if h_parts[0]["png"] != full_png or str(h_parts[1]["text"]).encode() != rca_text_b:
        raise RQ1Error("RCA H is not strict image-first A+B")
    r_fact_ids = {fact["fact_id"] for fact in facts}
    if len(r_fact_ids) != len(facts):
        raise RQ1Error("RCA fact IDs are not unique")
    common_ids = {fact["fact_id"] for fact in facts if fact["region"] == "C"}
    incident_ids = r_fact_ids - common_ids
    routed_visual = {fact["fact_id"] for fact in facts if fact["region"] in {"M", "G"}}
    routed_text = {fact["fact_id"] for fact in facts if fact["region"] in {"L", "R"}}
    if routed_visual & routed_text or routed_visual | routed_text != incident_ids:
        raise RQ1Error("routed RCA transport is not an exact-once partition")
    if not any(
        fact["field"] == "evidence_schema"
        and isinstance(fact.get("payload"), Mapping)
        and isinstance(fact["payload"].get("selection_summary"), Mapping)
        for fact in facts if fact["region"] == "C"
    ):
        raise RQ1Error("dashboard selection metadata is absent from the common shell")
    image_hidden_metric_keys = {"observed_counts", "onset_bin", "onset_rel_s", "persistence_bins"}
    if any(image_hidden_metric_keys & set(fact["payload"])
           for fact in facts if fact["field"] == "metric_series_64"):
        raise RQ1Error("non-rendered metric metadata escaped into the RCA text/flat arms")
    return {
        "passed": True, "rca_fact_inventory_hash": inventory, "rca_fact_count": len(facts),
        "qa_fact_inventory_hash": qa_packet["fact_inventory_hash"], "qa_fact_count": len(qfacts),
        "H_is_strict_A_plus_B": True, "qa_H_is_strict_V_plus_T": True,
        "T_P_V_atomic_fact_equality": True,
        "P_transport": "exact_T_text_rendered_as_pixels",
        "P_source_fact_text_hash": stable_hash("\n".join(pixel_fact_lines) + "\n"),
        "T_fact_text_hash": stable_hash("\n".join(t_fact_lines) + "\n"),
        "P_source_text_hash": stable_hash("\n".join(pixel_source_lines) + "\n"),
        "T_incident_text_hash": stable_hash(qa_text_b.decode()),
        "RCA_T_incident_text_hash": stable_hash(rca_text_b.decode()),
        "P_image_count": len(pixel_text_pngs),
        "qa_P_source_text_sha256": qa_packet["evidence_text_sha256"],
        "qa_V_image_sha256": stable_hash(qa_full_png),
        "qa_H_image_sha256": stable_hash(qa_h[0]["png"]),
        "qa_H_text_sha256": stable_hash(qa_h[1]["text"]),
        "qa_controlled_canvas_formal": False,
        "qa_factorial_visual_source": "renderer_v12_source_crops",
        "qa_factorial_cells": 16, "R_exact_once_by_region": True,
        "R_visual_fact_ids": sorted(routed_visual), "R_text_fact_ids": sorted(routed_text),
        "common_fact_ids": sorted(common_ids),
        "fact_locations": {
            arm: {fact["fact_id"]: (
                "common_shell" if fact["region"] == "C" else
                "image+text" if arm == "H" else
                "image" if arm in {"V", "P"} or (arm == "R" and fact["region"] in {"M", "G"}) else
                "text" if arm in {"T", "R"} else "json_pointer")
                for fact in facts}
            for arm in RCA_ARMS
        },
        "qa_fact_locations": {
            cell: {fact["fact_id"]: (
                "image+text" if cell == "H" else
                "image" if cell in {"P", "V", "Mv-Rv-Lv-Gv"} or (
                    cell not in {"T", "Mt-Rt-Lt-Gt"} and f"{fact['region']}v" in cell
                ) else "text") for fact in qfacts}
            for cell in [*factorial_cells(), "P", "V", "H"]
        },
    }


def _neighbors(edges: Sequence[Mapping[str, Any]], entity: str) -> tuple[list[str], list[str]]:
    upstream = sorted({str(edge["caller"]) for edge in edges if str(edge["callee"]) == entity})
    downstream = sorted({str(edge["callee"]) for edge in edges if str(edge["caller"]) == entity})
    return upstream, downstream


def _at(row: Mapping[str, Any], field: str, index: int) -> str:
    values = list(row.get(field) or ())
    value = values[index] if index < len(values) else None
    return "missing" if value is None else str(value)


def _pick_template(pool: Sequence[Question], opaque_id: str, level: int) -> Question:
    grouped: dict[str, list[Question]] = defaultdict(list)
    for question in pool:
        grouped[question.template].append(question)
    templates = sorted(grouped)
    if not templates:
        raise RQ1Error(f"case has no eligible Level-{level} cross-region question")
    digest = int(stable_hash(f"{opaque_id}:L{level}:template"), 16)
    template = templates[digest % len(templates)]
    choices = grouped[template]
    return choices[(digest // len(templates)) % len(choices)]


def _unique_anchor(
    rows: Sequence[Mapping[str, Any]], fields: Sequence[str], predicate: Any | None = None,
) -> tuple[Mapping[str, Any], int, str, str] | None:
    """Return the first display-unique value in frozen field/bin/value order."""

    for field in fields:
        for bin_index in range(16):
            buckets: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
            for row in rows:
                values = list(row.get(field) or ())
                value = values[bin_index] if bin_index < len(values) else None
                shown = "missing" if value is None else str(value)
                if shown != "missing":
                    buckets[shown].append(row)
            for shown in sorted(buckets):
                matches = buckets[shown]
                if len(matches) == 1 and (predicate is None or predicate(matches[0])):
                    return matches[0], bin_index, field, shown
    return None


def _explicit_multihop(edges: Sequence[Mapping[str, Any]]) -> list[str] | None:
    adjacency: dict[str, list[str]] = defaultdict(list)
    nodes = set()
    for edge in edges:
        caller, callee = str(edge["caller"]), str(edge["callee"])
        adjacency[caller].append(callee); nodes.update((caller, callee))
    for source in sorted(nodes):
        queue = [[source]]
        while queue:
            path = queue.pop(0)
            if 3 <= len(path) <= 4:
                return path
            if len(path) < 4:
                queue.extend(path + [target] for target in sorted(set(adjacency[path[-1]])) if target not in path)
    return None


def _direct_lookup(rows: Sequence[Mapping[str, Any]], fields: Sequence[str],
                   opaque_id: str, salt: str) -> tuple[Mapping[str, Any], int, str, str]:
    """Choose one reproducible displayed cell, preferring an informative nonzero value."""

    candidates: list[tuple[Mapping[str, Any], int, str, str]] = []
    for row in rows:
        for field in fields:
            for bin_index, value in enumerate(row.get(field) or ()):
                if value is not None and str(value) != "missing":
                    candidates.append((row, bin_index, field, str(value)))
    if not candidates:
        raise RQ1Error(f"no displayed cell is eligible for {salt}")
    populated = [item for item in candidates if (_number(item[3]) or 0.0) != 0.0]
    pool = populated or candidates
    return pool[int(stable_hash(f"{opaque_id}:{salt}"), 16) % len(pool)]


def _archived_controlled_questions_for_case(packet: Mapping[str, Any], opaque_id: str) -> tuple[list[Question], list[Question]]:
    """Build Legacy-Q9 plus the registered 4/6/4-template reasoning ladder."""

    metrics = list(packet["regions"]["M"])
    logs = list(packet["regions"]["L"])
    traces = list(packet["regions"]["R"])
    edges = list(packet["regions"]["G"])
    if not metrics or not logs or not traces:
        raise RQ1Error("controlled packet lacks an M/L/R region row")
    service_traces = [row for row in traces if row.get("row_kind") == "service"]
    edge_traces = [row for row in traces if row.get("row_kind") == "edge"]
    trace_by_entity = {str(row["entity"]): row for row in service_traces}
    log_by_entity = {str(row["entity"]): row for row in logs}
    edge_by_id = {str(row["edge_id"]): row for row in edges}
    edge_maps = [{"caller": row["caller"], "callee": row["callee"]} for row in edges]
    metric, metric_bin, metric_field, metric_value = _direct_lookup(
        metrics, ("values_16",), opaque_id, "legacy_metric_exact",
    )
    log, log_bin, log_field, log_value = _direct_lookup(
        logs, ("event_count_16", "error_count_16"), opaque_id, "legacy_log_exact",
    )
    trace, trace_bin, trace_field, trace_value = _direct_lookup(
        service_traces, ("span_count_16", "error_count_16", "max_p95_ms_16"),
        opaque_id, "legacy_trace_exact",
    )
    edge = (edges[int(stable_hash(f"{opaque_id}:legacy_edge"), 16) % len(edges)]
            if edges else {"edge_id": "missing", "caller": "missing", "callee": "missing"})
    upstream, downstream = _neighbors(edge_maps, str(metric["entity"]))
    onset_rows = [row for row in metrics if row.get("onset_bin_64") is not None]
    earliest = min((int(row["onset_bin_64"]) for row in onset_rows), default=None)
    earliest_entities = sorted(str(row["entity"]) for row in onset_rows if int(row["onset_bin_64"]) == earliest)
    longest = max((int(row.get("persistence_bins_64") or 0) for row in metrics), default=0)
    longest_entities = sorted(str(row["entity"]) for row in metrics if int(row.get("persistence_bins_64") or 0) == longest)
    path = _explicit_multihop(edges)
    all_entities = sorted({str(row.get("entity")) for row in [*metrics, *logs, *service_traces]})
    coverage = {entity: sum((any(str(row.get("entity")) == entity for row in metrics),
                             any(str(row.get("entity")) == entity for row in logs),
                             any(str(row.get("entity")) == entity for row in service_traces)))
                for entity in all_entities}
    maximum_coverage = max(coverage.values(), default=0)
    aligned = sorted(entity for entity, count in coverage.items() if count == maximum_coverage)
    maximum_missing = max((int(row.get("missing_bins_64") or 0) for row in metrics), default=0)
    missing_entities = sorted(str(row["entity"]) for row in metrics if int(row.get("missing_bins_64") or 0) == maximum_missing)
    q9 = [
        Question("q1", 1, ("M",), "metric_exact_lookup", f"In M read panel {metric['panel_id']} for entity {metric['entity']} at bin {metric_bin}.", ((metric_value,),)),
        Question("q2", 1, ("L",), "log_exact_lookup", f"In L read {log_field.removesuffix('_16')} for entity {log['entity']} at bin {log_bin}.", ((log_value,),)),
        Question("q3", 1, ("R",), "trace_exact_lookup", f"In R read {trace_field.removesuffix('_16')} for entity {trace['entity']} at bin {trace_bin}.", ((trace_value,),)),
        Question("q4", 1, ("M",), "earliest_onset", "Which entity or tied entities have the earliest displayed onset_bin_64? Return missing if none is shown.", (tuple(earliest_entities) or ("missing",),)),
        Question("q5", 1, ("M",), "longest_persistence", "Which entity or tied entities have the largest displayed persistence_bins_64?", (tuple(longest_entities) or ("missing",),)),
        Question("q6", 1, ("G",), "directed_edge", "Return the first G edge as caller->callee, or missing.", ((f"{edge['caller']}->{edge['callee']}" if edges else "missing",),)),
        Question("q7", 1, ("G",), "multi_hop_path", "Return the lexicographically first supplied caller->callee path of two or three edges as an ordered ID list, or missing.", (tuple(path) if path else ("missing",),)),
        Question("q8", 1, ("M",), "entity_modality_alignment", "Across M, L, and service rows in R, which entity or tied entities occur in the greatest number of regions?", (tuple(aligned) or ("missing",),)),
        Question("q9", 1, ("M",), "metric_missingness", "Which entity or tied entities have the largest displayed missing_bins_64?", (tuple(missing_entities) or ("missing",),)),
    ]
    level1 = _pick_template([
        replace(q9[0], template="M_direct_bin"), replace(q9[1], query_id="q1", template="L_direct_bin"),
        replace(q9[2], query_id="q1", template="R_direct_bin"),
        Question("q1", 1, ("G",), "G_direct_neighbors", f"Return every direct upstream=ID and downstream=ID for {metric['entity']} in supplied G.", (tuple([f"upstream={v}" for v in upstream] + [f"downstream={v}" for v in downstream]) or ("missing",),)),
    ], opaque_id, 1)

    links: list[Question] = []
    e_anchor = _unique_anchor(edge_traces, ("max_p95_ms_16", "error_count_16", "span_count_16"))
    for template, region, predicate, target_field in (
        ("M_L_link", "L", lambda row: str(row["entity"]) in log_by_entity, "event_count_16"),
        ("M_R_link", "R", lambda row: str(row["entity"]) in trace_by_entity, "span_count_16"),
        ("M_G_link", "G", lambda row: any(_neighbors(edge_maps, str(row["entity"])),), ""),
    ):
        anchor = _unique_anchor(metrics, ("values_16",), predicate)
        if not anchor:
            continue
        row, anchor_bin, field, shown = anchor; owner = str(row["entity"]); target_bin = (anchor_bin + 1) % 16
        prefix = f"Step 1 (M): at bin {anchor_bin}, find the unique entity whose {field} value is {shown}."
        if region == "G":
            ups, downs = _neighbors(edge_maps, owner)
            links.append(Question("q2", 2, ("M", "G"), template, prefix + " Step 2 (G): return every direct neighbor.", ((owner,), tuple([f"upstream={v}" for v in ups] + [f"downstream={v}" for v in downs]))))
        else:
            target_row = log_by_entity[owner] if region == "L" else trace_by_entity[owner]
            links.append(Question("q2", 2, ("M", region), template, prefix + f" Step 2 ({region}): read its {target_field.removesuffix('_16')} at bin {target_bin}.", ((owner,), (_at(target_row, target_field, target_bin),))))
    for template, region, predicate, target_field in (
        ("L_R_link", "R", lambda row: str(row["entity"]) in trace_by_entity, "span_count_16"),
        ("L_G_link", "G", lambda row: any(_neighbors(edge_maps, str(row["entity"])),), ""),
    ):
        anchor = _unique_anchor(logs, ("error_count_16", "event_count_16"), predicate)
        if not anchor:
            continue
        row, anchor_bin, field, shown = anchor; owner = str(row["entity"])
        prefix = f"Step 1 (L): at bin {anchor_bin}, find the unique entity whose {field} value is {shown}."
        if region == "G":
            ups, downs = _neighbors(edge_maps, owner)
            links.append(Question("q2", 2, ("L", "G"), template, prefix + " Step 2 (G): return every direct neighbor.", ((owner,), tuple([f"upstream={v}" for v in ups] + [f"downstream={v}" for v in downs]))))
        else:
            target_bin = (anchor_bin + 1) % 16
            links.append(Question("q2", 2, ("L", "R"), template, prefix + f" Step 2 (R): read its {target_field.removesuffix('_16')} at bin {target_bin}.", ((owner,), (_at(trace_by_entity[owner], target_field, target_bin),))))
    if e_anchor:
        erow, anchor_bin, field, shown = e_anchor
        edge_id = str(erow["edge_id"]); resolved = edge_by_id[edge_id]
        links.append(Question("q2", 2, ("R", "G"), "R_G_link",
            f"Step 1 (R): at bin {anchor_bin}, find the unique edge row whose {field} value is {shown}. Step 2 (G): resolve it and return caller=ID and callee=ID.",
            ((edge_id,), (f"caller={resolved['caller']}", f"callee={resolved['callee']}"))))
    level2 = _pick_template(links, opaque_id, 2)

    chains: list[Question] = []
    anchor = _unique_anchor(metrics, ("values_16",),
                            lambda row: str(row["entity"]) in log_by_entity and str(row["entity"]) in trace_by_entity)
    if anchor:
        row, anchor_bin, field, shown = anchor; owner = str(row["entity"])
        lrow, rrow = log_by_entity[owner], trace_by_entity[owner]
        prefix = f"Step 1 (M): at bin {anchor_bin}, find the unique entity whose {field} value is {shown}."
        errors = [int(value) for value in lrow["error_count_16"]]; selected_bin = errors.index(max(errors))
        chains.append(Question("q3", 3, ("M", "L", "R"), "M_L_R_chain",
            prefix + " Step 2 (L): find the earliest bin with that entity's maximum error_count. Step 3 (R): for the same entity at that bin read max_p95_ms.",
            ((owner,), (str(selected_bin),), (_at(rrow, "max_p95_ms_16", selected_bin),))))
    anchor = _unique_anchor(metrics, ("values_16",), lambda row: (
        len(_neighbors(edge_maps, str(row["entity"]))[1]) == 1
        and _neighbors(edge_maps, str(row["entity"]))[1][0] in log_by_entity
    ))
    if anchor:
        row, anchor_bin, field, shown = anchor; owner = str(row["entity"])
        target = next(value for value in _neighbors(edge_maps, owner)[1] if value in log_by_entity)
        target_bin = (anchor_bin + 1) % 16
        chains.append(Question("q3", 3, ("M", "G", "L"), "M_G_L_chain",
            f"Step 1 (M): at bin {anchor_bin}, find the unique entity whose {field} value is {shown}. Step 2 (G): follow its only displayed downstream edge. Step 3 (L): read that callee's error_count at bin {target_bin}.",
            ((owner,), (target,), (_at(log_by_entity[target], "error_count_16", target_bin),))))
    anchor = _unique_anchor(metrics, ("values_16",), lambda row: len(
        (trace_by_entity.get(str(row["entity"])) or {}).get("associated_edge_ids") or ()
    ) == 1)
    if anchor:
        row, anchor_bin, field, shown = anchor; owner = str(row["entity"]); rrow = trace_by_entity[owner]
        edge_id = str(rrow["associated_edge_ids"][0]); resolved = edge_by_id[edge_id]
        other = str(resolved["callee"] if str(resolved["caller"]) == owner else resolved["caller"])
        chains.append(Question("q3", 3, ("M", "R", "G"), "M_R_G_chain",
            f"Step 1 (M): at bin {anchor_bin}, find the unique entity whose {field} value is {shown}. Step 2 (R): read its smallest associated edge ID. Step 3 (G): resolve the other endpoint.",
            ((owner,), (edge_id,), (other,))))
    anchor = _unique_anchor(logs, ("error_count_16", "event_count_16"), lambda row: len(
        (trace_by_entity.get(str(row["entity"])) or {}).get("associated_edge_ids") or ()
    ) == 1)
    if anchor:
        anchor_log, anchor_bin, field, shown = anchor; owner = str(anchor_log["entity"]); rrow = trace_by_entity[owner]
        edge_id = str(rrow["associated_edge_ids"][0]); resolved = edge_by_id[edge_id]
        other = str(resolved["callee"] if str(resolved["caller"]) == owner else resolved["caller"])
        chains.append(Question("q3", 3, ("L", "R", "G"), "L_R_G_chain",
            f"Step 1 (L): at bin {anchor_bin}, find the unique entity whose {field} value is {shown}. Step 2 (R): read its smallest associated edge ID. Step 3 (G): resolve it and return the other endpoint.",
            ((owner,), (edge_id,), (other,))))
    level3 = _pick_template(chains, opaque_id, 3)
    return q9, [replace(level1, query_id="q1"), replace(level2, query_id="q2"), replace(level3, query_id="q3")]


def _qa_rows(packet: Mapping[str, Any], field: str) -> list[dict[str, Any]]:
    return [dict(fact["payload"]) for fact in packet["facts"] if fact["field"] == field]


def _shown_field(row: Mapping[str, Any], preferred: Sequence[str]) -> tuple[str, str]:
    for field in preferred:
        if field in row and not isinstance(row[field], (list, dict)):
            return field, "missing" if row[field] is None else str(row[field])
    raise RQ1Error("renderer-visible row lacks a registered readable scalar")


def questions_for_case(packet: Mapping[str, Any], opaque_id: str) -> tuple[list[Question], list[Question]]:
    """Build Q9 and dependent Level-1/2/3 questions from renderer-visible rows."""

    metrics, logs = _qa_rows(packet, "metric_series_64"), _qa_rows(packet, "log_summary_entry")
    traces, edges = _qa_rows(packet, "trace_summary_entry"), _qa_rows(packet, "directed_call_edge")
    propagation = _qa_rows(packet, "propagation_service")
    if not metrics or not logs or not traces or not propagation:
        raise RQ1Error("renderer-v12 Q&A requires visible M/L/R rows and propagation readouts")

    def pick(rows: Sequence[Any], salt: str) -> Any:
        return rows[int(stable_hash(f"{opaque_id}:{salt}"), 16) % len(rows)]

    def scalar(row: Mapping[str, Any], region: str) -> tuple[str, str]:
        if region == "G":
            return _shown_field(
                row, ("onset_rel_min_display", "severity_z_display", "evidence_source_display"),
            )
        choices = (("peak", "baseline", "signed_z") if region == "M" else
                   ("error_logs", "error_count", "total_logs", "total", "error_pct", "n_pre", "n_during", "change_pct") if region == "L" else
                   ("p95_during_ms", "p95_pre_ms", "delta_pct", "error_pct"))
        return _shown_field(row, choices)

    def label(region: str, row: Mapping[str, Any]) -> str:
        return (f"panel {row['panel_id']}" if region == "M" else
                f"propagation row {int(row.get('rank') or 0)}" if region == "G" else
                f"visible row {int(row.get('entry_index') or 0) + 1}")

    metric, log, trace = pick(metrics, "legacy-M"), pick(logs, "legacy-L"), pick(traces, "legacy-R")
    edge = min(edges, key=lambda row: int(row.get("edge_index") or 0)) if edges else None
    log_field, log_value = scalar(log, "L"); trace_field, trace_value = scalar(trace, "R")
    grow = pick(propagation, "legacy-G") if propagation else {"service": "missing", "onset_rel_min_display": None}
    gfield, gvalue = _shown_field(grow, ("onset_rel_min_display", "severity_z_display", "evidence_source_display"))
    log_meta = (_qa_rows(packet, "log_summary_meta") or [{"mode": "none"}])[0]
    window = (_qa_rows(packet, "observation_window") or [{"duration_rel_s": None}])[0]
    q9 = [
        Question("q1", 1, ("M",), "metric_panel_entity", f"Which entity ID is printed in metric panel {metric['panel_id']}?", ((str(metric["service"]),),)),
        Question("q2", 1, ("M",), "metric_printed_peak", f"Read the printed peak value under panel {metric['panel_id']}.", ((str(metric.get("peak") or "missing"),),)),
        Question("q3", 1, ("M",), "window_duration", "Read the dashboard-header window duration in seconds; return the number without the s unit.", ((str(window.get("duration_rel_s") or "missing"),),)),
        Question("q4", 1, ("L",), "log_table_cell", f"In the visible log row for entity {log['service']}, read {log_field}.", ((log_value,),)),
        Question("q5", 1, ("R",), "trace_table_cell", f"In the visible trace row for entity {trace['service']}, read {trace_field}.", ((trace_value,),)),
        Question("q6", 1, ("G",), "directed_edge",
                 f"Read edge-key row {int(edge.get('edge_index') or 0) + 1} as caller->callee."
                 if edge else "The visible directed-edge key explicitly reports no displayed edge. Return none.",
                 ((f"{edge['caller']}->{edge['callee']}" if edge else "none",),)),
        Question("q7", 1, ("G",), "propagation_readout", f"For propagation entity {grow['service']}, read {gfield}.", ((gvalue,),)),
        Question("q8", 1, ("M",), "metric_printed_baseline", f"Read the printed baseline value under panel {metric['panel_id']}.", ((str(metric.get("baseline") or "missing"),),)),
        Question("q9", 1, ("L",), "log_display_mode", "Is the visible log panel in errors, volume, or none mode? Return one of those words.", ((str(log_meta.get("mode") or "none"),),)),
    ]
    metric_by = {str(row["service"]): row for row in metrics}
    log_by = {str(row["service"]): row for row in logs}
    trace_by = {str(row["service"]): row for row in traces}
    propagation_by = {str(row["service"]): row for row in propagation}
    propagation_visible_rank = {
        str(row["service"]): str(row.get("rank") or index)
        for index, row in enumerate(propagation, 1)
    }
    sources = {"M": metric_by, "L": log_by, "R": trace_by}
    edge_rows = [{"caller": str(row["caller"]), "callee": str(row["callee"])} for row in edges]
    level1_pool = [
        Question("q1", 1, ("M",), "M_direct_read", f"In M, return the entity printed in panel {metric['panel_id']}.", ((str(metric["service"]),),)),
        Question("q1", 1, ("L",), "L_direct_read", f"In L, read {log_field} for entity {log['service']}.", ((log_value,),)),
        Question("q1", 1, ("R",), "R_direct_read", f"In R, read {trace_field} for entity {trace['service']}.", ((trace_value,),)),
    ]
    direct_g = pick(propagation, "level1-G")
    direct_g_field, direct_g_value = _shown_field(
        direct_g, ("onset_rel_min_display", "severity_z_display", "evidence_source_display"),
    )
    level1_pool.append(Question("q1", 1, ("G",), "G_direct_read",
        f"In G, read {direct_g_field} for propagation entity {direct_g['service']}.",
        ((direct_g_value,),)))
    level1 = _pick_template(level1_pool, opaque_id, 1)

    links: list[Question] = []
    for left, right, template in (("M", "L", "M_L_link"), ("M", "R", "M_R_link"),
                                  ("L", "R", "L_R_link")):
        common = sorted(set(sources[left]) & set(sources[right]))
        if common:
            entity = pick(common, template); source = sources[left][entity]
            field, value = scalar(sources[right][entity], right)
            links.append(Question("q2", 2, (left, right), template,
                f"Step 1 ({left}): read the entity ID from {label(left, source)}. Step 2 ({right}): using that ID, read {field}.",
                ((entity,), (value,))))
    for left, template in (("M", "M_G_link"), ("L", "L_G_link"), ("R", "R_G_link")):
        eligible = sorted(set(sources[left]) & set(propagation_by))
        if eligible:
            entity = pick(eligible, template)
            field, value = _shown_field(
                propagation_by[entity], ("onset_rel_min_display", "severity_z_display", "evidence_source_display"),
            )
            links.append(Question("q2", 2, (left, "G"), template,
                f"Step 1 ({left}): read the entity ID from {label(left, sources[left][entity])}. Step 2 (G): using that ID, read {field} from its propagation row.",
                ((entity,), (value,))))
    level2 = _pick_template(links, opaque_id, 2)

    chains: list[Question] = []
    source_rows = {**sources, "G": propagation_by}

    def locator(region: str, entity: str) -> tuple[str, str]:
        row = source_rows[region][entity]
        if region == "G":
            return "propagation-row rank", propagation_visible_rank[entity]
        if region == "M":
            return "panel ID", str(row["panel_id"])
        return "row number", str(int(row.get("entry_index") or 0) + 1)

    region_order = ("M", "R", "L", "G")
    for start in region_order:
        template = f"{start}_locator_chain"
        choices: list[tuple[str, str, list[str]]] = []
        for pivot in ("G", *region_order):
            if pivot == start:
                continue
            for target in region_order:
                if target in {start, pivot}:
                    continue
                common = sorted(set(source_rows[start]) & set(source_rows[pivot]) & set(source_rows[target]))
                if common:
                    choices.append((pivot, target, common))
        if not choices:
            for pivot in ("G", *region_order):
                if pivot == start:
                    continue
                common = sorted(set(source_rows[start]) & set(source_rows[pivot]))
                if common:
                    choices.append((pivot, start, common))
        if not choices:
            continue
        pivot, target, common = pick(choices, f"{template}:path")
        entity = pick(common, f"{template}:{pivot}:{target}")
        locator_name, locator_value = locator(pivot, entity)
        field, value = scalar(source_rows[target][entity], target)
        chains.append(Question("q3", 3, (start, pivot, target), template,
            f"Step 1 ({start}): read the entity ID from {label(start, source_rows[start][entity])}. "
            f"Step 2 ({pivot}): using that ID, read its visible {locator_name}. "
            f"Step 3 ({target}): using that locator to recover the {pivot} entity, read {field} for it in {target}.",
            ((entity,), (locator_value,), (value,))))
    level3 = _pick_template(chains, opaque_id, 3)
    return q9, [replace(level1, query_id="q1"), replace(level2, query_id="q2"), replace(level3, query_id="q3")]


QA_SYSTEM = """You are answering label-free telemetry questions from a common renderer-v12 evidence packet. Use only the supplied evidence. Service names, pod names, and node names are represented by numeric IDs. A directed topology edge caller -> callee means the caller invokes the callee. Relative bins are case-local. Return exactly one JSON object matching ReasoningPacketResponseV2. The answers array must contain exactly one answer for each supplied query_id in supplied order. Do not add prose, markdown, or hidden chain-of-thought. Each requested step must contain only the step number, region code, and normalized string values.""" + "\n\n" + QA_EVIDENCE_GUIDE

TYPED_OBSERVE_SYSTEM = """You are Stage 1, Observe and Connect, for the common renderer-v12 Q&A evidence. Use only the supplied M/R/L/G evidence. Fill every fixed q1/q2/q3 step slot with one compact visible-record selector. Use record_key=M1 for a metric panel, L:<numeric entity> for a log row, R:<numeric entity> for a trace row, G:<numeric entity> for a propagation row and all incident edges touching that entity, or G:<caller>-><callee> for one directed edge. `field` may name the visible scalar needed by the question or be null. The host copies exact public values. Never answer the questions, copy arrays, invent query IDs, emit private fact IDs, root cause, prose, markdown, or chain-of-thought. Return exactly the schema-defined selector object.""" + "\n\n" + QA_EVIDENCE_GUIDE

TYPED_ANSWER_SYSTEM = """You are Stage 2, Answer, for renderer-v12 cross-region telemetry questions. The typed Stage-1 public-record ledger and registered question contracts are your only incident evidence. A directed edge caller -> callee means caller is upstream and callee is downstream. Later steps must use the entity resolved by the preceding step. Follow every public value_kind exactly and return ReasoningPacketResponseV3 with exactly one answer per supplied query in supplied order. Do not emit a full ledger row, prose, markdown, or hidden chain-of-thought.""" + "\n\n" + QA_EVIDENCE_GUIDE

OBSERVE_SYSTEM = """You are Stage 1, Observe and Connect, for a microservice root-cause analysis.
Use only the supplied incident evidence. Service names, pod names, and node names are represented by numeric IDs. A directed edge caller -> callee means the caller invokes the callee. Relative bins and relative seconds are measured from the supplied case-local window start; missing is evidence, not zero.

Return one CompactRecordKeyLedgerV4 JSON object containing at most 16 unique, diagnostically strongest selectors. Every selector must contain one nonempty `record_key` copied or constructed only from a visible record label, plus `relative_bins`. Select evidence; do not transcribe raw values, arrays, attributes, units, relations, candidate-support lists, or a comprehensive inventory. The host deterministically binds each key to exactly one public evidence record and copies its exact scalar attributes and selected values.

Use exactly these human-readable key forms: a visible metric panel `[M1]` becomes `M1`; a log row for entity `91643` becomes `L:91643`; a trace row for entity `69070` becomes `R:69070`; a propagation row for entity `4867` becomes `G:4867`; and a visible directed edge `4867 -> 30493` becomes `G:4867->30493`. Explicitly missing log or trace evidence uses `L:missing` or `R:missing`. Metric selectors may name zero to four especially diagnostic `relative_bins`; zero bins selects only the registered baseline/peak/deviation summary. Every nonmetric selector must use an empty bin list. The key itself identifies the record: never put an entity ID anywhere else and never return a null or empty key. Prefer evidence that distinguishes an origin from propagated symptoms, cover available M/R/L/G regions when diagnostic, and do not list every service or panel merely because it is visible.
Never emit a final root-cause ranking, a query ID, an opaque fact ID, a hash, the original entity name, an absolute time, a dataset name, or free-form chain-of-thought. Do not add markdown or prose outside the JSON object.""" + "\n\n" + RCA_EVIDENCE_GUIDE + "\n\n" + RCA_METHOD_GUIDE

DIAGNOSE_SYSTEM = """You are Stage 2, Diagnose, for a microservice root-cause analysis. The normalized Stage-1 ledger in the user message is your only incident evidence. You cannot access the original dashboard, original evidence text, original structured records, representation arm, dataset, case identifier, labels, or failed raw Stage-1 output. Distinguish an originating fault from propagated symptoms and rank only IDs from the supplied exhaustive candidate list. The host has removed every observation or relation that could not be matched to the frozen evidence packet; unsupported-claim counts are audit warnings, not incident facts.

Return exactly one JSON object with no markdown or preamble: {\"services\":[\"123\",\"456\"],\"reason\":\"one concise evidence-grounded sentence\",\"confidence\":\"high|medium|low\"}. The services array must contain one to five unique candidate IDs in descending root-cause likelihood.""" + "\n\n" + STAGE2_LEDGER_GUIDE + "\n\n" + RCA_METHOD_GUIDE + "\n\n" + SIRCL_VERIFY_GUIDE

DIRECT_DIAGNOSE_SYSTEM = """You are directly diagnosing one microservice incident from the supplied label-blind telemetry representation. Use only that incident evidence and rank only IDs from its exhaustive candidate list. You cannot access the representation arm, dataset, case identifier, labels, natural entity names, or any private evaluator field.

Return exactly one JSON object with no markdown or preamble: {\"services\":[\"123\",\"456\"],\"reason\":\"one concise evidence-grounded sentence\",\"confidence\":\"high|medium|low\"}. The services array must contain one to five unique candidate IDs in descending root-cause likelihood.""" + "\n\n" + RCA_EVIDENCE_GUIDE + "\n\n" + RCA_METHOD_GUIDE + "\n\n" + SIRCL_VERIFY_GUIDE


def stage1_prompt(spec: ExperimentSpec, public: Mapping[str, Any]) -> str:
    if spec.task == "root_cause_direct":
        return "Directly rank the most likely root-cause candidate IDs now."
    if is_rca_task(spec):
        return "Select and return the registered compact evidence ledger now."
    questions = public["legacy_questions"] if spec.task == "direct_visops" else public["reasoning_questions"]
    if spec.name == "typed_two_stage":
        typed = []
        for question in questions:
            kinds = TEMPLATE_VALUE_KINDS[str(question["template"])]
            typed.append({**dict(question), "answer_contract": [
                {"step": index, "region": region, "value_kind": kind}
                for index, (region, kind) in enumerate(zip(question["region_path"], kinds, strict=True), 1)
            ]})
        return "Questions, registered paths, and answer contracts:\n" + canonical_json(typed)
    return "Questions:\n" + canonical_json(questions)


def _ordered_stage2_ledger(ledger: Mapping[str, Any]) -> dict[str, Any]:
    """Serialize region-bearing ledger rows in M -> R -> L -> G order."""

    rank = {region: index for index, region in enumerate(PROMPT_REGION_ORDER)}
    ordered = dict(ledger)
    for key in ("observations", "missing_evidence"):
        rows = ledger.get(key)
        if isinstance(rows, list):
            ordered[key] = sorted(
                (dict(row) if isinstance(row, Mapping) else row for row in rows),
                key=lambda row: rank.get(str(row.get("region")), len(rank))
                if isinstance(row, Mapping) else len(rank),
            )
    return ordered


def stage2_prompt(spec: ExperimentSpec, stage1: Mapping[str, Any], candidates: Sequence[str],
                  questions: Sequence[Mapping[str, Any]] = ()) -> str:
    if is_rca_task(spec):
        return canonical_json({
            "schema_version": "RQ1Stage2InputV2", "candidate_ids_in_fixed_order": list(candidates),
            "normalized_evidence_ledger": _ordered_stage2_ledger(stage1),
        })
    typed = []
    for question in questions:
        kinds = TEMPLATE_VALUE_KINDS[str(question["template"])]
        typed.append({**dict(question), "answer_contract": [
            {"step": index, "region": region, "value_kind": kind}
            for index, (region, kind) in enumerate(zip(question["region_path"], kinds, strict=True), 1)
        ]})
    return "Questions and contracts:\n" + canonical_json(typed) + "\nTyped raw-record ledger:\n" + canonical_json(stage1)


def _qa_schema(*, typed_questions: Sequence[Mapping[str, Any]] = (),
               typed_answer: bool = False) -> dict[str, Any]:
    step_properties: dict[str, Any] = {
        "step": {"type": "integer", "minimum": 1, "maximum": 3},
        "region": {"enum": list(REGIONS)},
        "values": {"type": "array", "items": {"type": "string"}},
    }
    if typed_answer:
        step_properties["value_kind"] = {
            "enum": sorted({kind for values in TEMPLATE_VALUE_KINDS.values() for kind in values})
        }
    answer_step = {"type": "object", "additionalProperties": False,
                   "required": list(step_properties), "properties": step_properties}
    if typed_questions:
        selector = {"type": "object", "additionalProperties": False,
                    "required": ["record_key", "field"],
                    "properties": {
                        "record_key": {"type": "string"},
                        "field": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    }}
        properties = {}
        for question in typed_questions:
            query_id = str(question["query_id"])
            step_names = [f"s{index}" for index in range(1, len(question["region_path"]) + 1)]
            properties[query_id] = {
                "type": "object", "additionalProperties": False,
                "required": step_names,
                "properties": {
                    name: selector for name in step_names
                },
            }
        name = "typed_question_record_selector_v6"
    else:
        row = {"type": "object", "additionalProperties": False,
               "required": ["query_id", "answer"],
               "properties": {"query_id": {"type": "string", "pattern": "^q[1-9]$"},
                              "answer": {"type": "object", "additionalProperties": False,
                                         "required": ["steps"], "properties": {
                                             "steps": {"type": "array", "minItems": 1, "maxItems": 3, "items": answer_step}}}}}
        properties = {"answers": {"type": "array", "minItems": 3, "maxItems": 9, "items": row}}
        name = "reasoning_packet_response_v3" if typed_answer else "reasoning_packet_response_v2"
    return {"type": "json_schema", "json_schema": {"name": name, "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": list(properties), "properties": properties,
    }}}


def response_schema(spec: ExperimentSpec, stage: int,
                    questions: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    if is_rca_task(spec) and (stage == 2 or spec.task == "root_cause_direct"):
        return {
            "type": "json_schema",
            "json_schema": {"name": "diagnosis", "strict": True, "schema": {
                "type": "object", "additionalProperties": False,
                "required": ["services", "reason", "confidence"],
                "properties": {
                    # xgrammar 0.2.3 does not implement uniqueItems and some
                    # string-size constraints. The deterministic validator
                    # below enforces uniqueness, numeric IDs and nonempty text
                    # before scoring; keep the server grammar portable.
                    "services": {"type": "array", "minItems": 1, "maxItems": 5,
                                 "items": {"type": "string"}},
                    "reason": {"type": "string"},
                    "confidence": {"enum": ["high", "medium", "low"]},
                },
            }},
        }
    if is_rca_task(spec):
        selector = {
            "type": "object",
            "additionalProperties": False,
            "required": ["record_key", "relative_bins"],
            "properties": {
                "record_key": {"type": "string"},
                "relative_bins": {"type": "array", "maxItems": 4,
                                  "items": {"type": "integer", "minimum": 0, "maximum": 63}},
            },
        }
        properties = {"selectors": {"type": "array", "minItems": 1,
                                     "maxItems": 16, "items": selector}}
        return {"type": "json_schema", "json_schema": {
            "name": "compact_record_key_ledger_v4", "strict": True,
            "schema": {"type": "object", "additionalProperties": False,
                       "required": ["selectors"], "properties": properties},
        }}
    return _qa_schema(typed_questions=questions if spec.name == "typed_two_stage" and stage == 1 else (),
                      typed_answer=spec.name == "typed_two_stage" and stage == 2)


def ledger_images(ledger: Mapping[str, Any]) -> tuple[bytes, ...]:
    """Losslessly paginate the complete canonical ledger across at most 8 images."""

    payload = canonical_json(ledger)
    chunks = [payload[index:index + 100] for index in range(0, len(payload), 100)] or [""]
    pages = [chunks[index:index + 52] for index in range(0, len(chunks), 52)]
    if len(pages) > 8:
        raise RQ1Error(f"normalized ledger needs {len(pages)} images; registered maximum is 8")
    if "".join(line for page in pages for line in page) != payload:
        raise RQ1Error("visual ledger pagination is not lossless")
    output: list[bytes] = []
    for page_index, lines in enumerate(pages, start=1):
        image = Image.new("RGB", (1600, 1000), "#F8FAFC")
        draw = ImageDraw.Draw(image)
        draw.text((24, 18), f"NORMALIZED EVIDENCE LEDGER — PAGE {page_index}/{len(pages)} — SAME FACTS AS TEXT", fill="#102027", font=_font(20, bold=True))
        for index, line in enumerate(lines):
            draw.text((24, 58 + 18 * index), line, fill="#263238", font=_font(15))
        stream = io.BytesIO()
        image.save(stream, format="PNG", optimize=False, compress_level=6)
        output.append(stream.getvalue())
    return tuple(output)


def ledger_image(ledger: Mapping[str, Any]) -> bytes:
    """Compatibility helper for static PNG checks; real handoff uses every page."""

    return ledger_images(ledger)[0]


def handoff_parts(arm: str, ledger: Mapping[str, Any], candidates: Sequence[str]) -> list[dict[str, Any]]:
    ordered = _ordered_stage2_ledger(ledger)
    text = canonical_json(ordered)
    boards = ledger_images(ordered)
    shell = "Rank the root cause from this normalized ledger. Candidates: " + canonical_json(list(candidates))
    if arm == "L_txt":
        evidence = [text_part(text)]
    elif arm == "L_vis":
        evidence = [image_part(board) for board in boards]
    elif arm == "L_hyb":
        evidence = [*(image_part(board) for board in boards), text_part(text)]
    else:
        raise RQ1Error(f"unknown handoff arm {arm!r}")
    return [*evidence, text_part(shell)]


_NUMBER = re.compile(r"^\s*(?:>=|<=|>|<)?\s*(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*([kmg])?\s*$", re.I)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    match = _NUMBER.fullmatch(str(value))
    if not match:
        return None
    return float(match.group(1)) * {None: 1.0, "k": 1e3, "m": 1e6, "g": 1e9}[match.group(2).lower() if match.group(2) else None]


def _same_scalar(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    a, b = _number(left), _number(right)
    if a is not None and b is not None:
        return math.isclose(a, b, rel_tol=0.01, abs_tol=max(0.01, abs(b) * 0.01))
    left_text, right_text = str(left).strip().casefold(), str(right).strip().casefold()
    if left_text == right_text:
        return True
    # Metric titles are middle-elided in the registered dashboard.  Treat the
    # exact visible prefix/suffix as the same displayed value, without guessing
    # any hidden middle text.
    for shortened, complete in ((left_text, right_text), (right_text, left_text)):
        if shortened.count("~") == 1:
            prefix, suffix = shortened.split("~")
            if complete.startswith(prefix) and complete.endswith(suffix):
                return True
    # The dashboard renders capped z scores as +/- >=999.  Models often copy
    # the visible cap as the scalar 999; this is a representation-equivalent
    # statement, not access to the uncapped source value.
    for capped, scalar in ((left_text, right), (right_text, left)):
        match = re.fullmatch(r"([+-]?)>=999", capped)
        number = _number(scalar)
        if match and number is not None and abs(number) == 999:
            return (match.group(1) != "-") == (number >= 0)
    return False


def _public_record_key(fact: Mapping[str, Any]) -> str | None:
    """Return the unique key composed only from labels visible in every arm."""

    payload, field, region = fact["payload"], str(fact["field"]), str(fact["region"])
    if field == "metric_series_64":
        return str(payload["panel_id"])
    if field == "log_summary_entry":
        return f"L:{payload['service']}"
    if field == "trace_summary_entry":
        return f"R:{payload['service']}"
    if field == "propagation_service":
        return f"G:{payload['service']}"
    if field == "directed_call_edge":
        return f"G:{payload['caller']}->{payload['callee']}"
    if field == "explicit_missingness" and region in {"L", "R"}:
        return f"{region}:missing"
    return None


def _normalize_record_key(value: Any) -> str:
    """Normalize harmless typography without guessing an unmentioned record."""

    key = str(value or "").strip()
    panel = re.fullmatch(r"M0*([1-9][0-9]*)", key, flags=re.IGNORECASE)
    if panel:
        return f"M{int(panel.group(1))}"
    entity = re.fullmatch(r"([LRG])\s*:\s*([0-9]{3,5}|missing)", key, flags=re.IGNORECASE)
    if entity:
        return f"{entity.group(1).upper()}:{entity.group(2).lower() if entity.group(2).lower() == 'missing' else entity.group(2)}"
    edge = re.fullmatch(r"G\s*:\s*([0-9]{3,5})\s*(?:->|→)\s*([0-9]{3,5})", key, flags=re.IGNORECASE)
    if edge:
        return f"G:{edge.group(1)}->{edge.group(2)}"
    return key


def _public_record_index(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    """Build a fail-closed unique index over model-visible public facts."""

    index: dict[str, Mapping[str, Any]] = {}
    for fact in packet["facts"]:
        key = _public_record_key(fact)
        if key is None:
            continue
        if key in index:
            raise RQ1Error(f"duplicate public Stage-1 record key: {key}")
        index[key] = fact
    return index


def normalize_stage1_ledger(raw: Mapping[str, Any], packet: Mapping[str, Any]) -> dict[str, Any]:
    """Bind nonempty public record keys, then copy exact values deterministically."""

    if raw.get("schema_version") == "Stage1FailureV2":
        return {"schema_version": "Stage1FailureV2", "failure": "parse_error"}
    public_index, selected, unsupported = _public_record_index(packet), {}, 0
    for item in list(raw.get("selectors") or ())[:16]:
        if not isinstance(item, Mapping):
            unsupported += 1
            continue
        record_key = _normalize_record_key(item.get("record_key"))
        fact = public_index.get(record_key)
        try:
            bins = list(map(int, item.get("relative_bins") or ()))
        except (TypeError, ValueError):
            unsupported += 1
            continue
        if (fact is None or len(bins) > 4 or len(bins) != len(set(bins))
                or any(not 0 <= value < 64 for value in bins)
                or (fact["field"] != "metric_series_64" and bins)):
            unsupported += 1
            continue
        bins = sorted(bins)
        key = (str(fact["fact_id"]), tuple(bins))
        selected.setdefault(key, {"fact": fact, "bins": bins})
    observations, selected_facts = [], []
    for row in selected.values():
        fact, bins, payload = row["fact"], row["bins"], row["fact"]["payload"]
        attributes = {key: value for key, value in payload.items()
                      if key not in {"values", "missing_mask"}}
        source_values = payload.get("values")
        observations.append({
            "observation_id": f"O{len(observations) + 1:02d}",
            "region": fact["region"], "entity_ids": list(map(str, fact.get("entity_ids") or ())),
            "field": fact["field"], "attributes": attributes, "relative_bins": bins,
            "values": [source_values[index] for index in bins] if bins else [],
            "unit": fact.get("unit"), "supports": [], "opposes": [],
        })
        selected_facts.append(fact)
    edges = [{"caller": str(f["payload"]["caller"]), "callee": str(f["payload"]["callee"])}
             for f in selected_facts if f["field"] == "directed_call_edge"]
    onset_rows = sorted(
        ((value, str(f["payload"]["service"])) for f in selected_facts
         if f["field"] == "propagation_service"
         and (value := _number(f["payload"].get("onset_rel_min_display"))) is not None),
    )
    temporal = [{"earlier_entity_id": left[1], "later_entity_id": right[1]}
                for left, right in zip(onset_rows, onset_rows[1:]) if left[0] < right[0]]
    missing = [{"region": f["region"], "missing": bool(next(iter(f["payload"].values())))}
               for f in selected_facts if f["field"] == "explicit_missingness"]
    return {
        "schema_version": "NormalizedEvidenceLedgerV4", "observations": observations,
        "temporal_relations": temporal, "directed_edges": edges, "conflicts": [],
        "missing_evidence": missing,
        "binding_audit": {"supported_observations": len(observations),
                          "unsupported_observations": unsupported,
                          "supported_selectors": len(selected),
                          "unsupported_selectors": unsupported,
                          "selector_interface": "visible_record_key_v1",
                          "validated_temporal_relations": len(temporal),
                          "validated_directed_edges": len(edges)},
    }


def _typed_selector_records(packet: Mapping[str, Any], region: str,
                            selector: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Bind a model-selected visible row to exact public values without labels."""

    entity = selector.get("entity_id")
    edge = selector.get("edge_id")
    panel = selector.get("panel_id")
    row_index = selector.get("row_index")
    field = selector.get("field")
    visible_aliases = {
        "M": {"bins": "values_16", "values": "values_16"},
        "L": {"events": "event_count_16", "errors": "error_count_16"},
        "R": {"spans": "span_count_16", "errors": "error_count_16",
              "p95ms": "max_p95_ms_16"},
    }
    if field is not None:
        field = visible_aliases.get(region, {}).get(str(field), str(field))
    bins = list(selector.get("relative_bins") or ())
    rows = list(packet["regions"][region])
    if region == "G":
        if str(field) == "neighbor_roles":
            field = None
        if panel is not None or row_index is not None or field is not None or bins:
            return []
        if edge is not None and entity is None:
            rows = [row for row in rows if str(row.get("edge_id")) == str(edge)]
        elif entity is not None and edge is None:
            rows = [row for row in rows if str(entity) in {str(row.get("caller")), str(row.get("callee"))}]
            if not rows:
                visible_entities = {
                    str(row["entity"]) for visible_region in ("M", "L", "R")
                    for row in packet["regions"][visible_region] if row.get("entity") is not None
                }
                if str(entity) in visible_entities:
                    return [{"record_kind": "topology_no_incident_edge",
                             "entity_id": str(entity), "edge_id": None,
                             "field": "incident_edges", "relative_bin": None,
                             "displayed_values": ["none"], "unit": None,
                             "caller": None, "callee": None}]
        else:
            return []
        return [{"record_kind": "topology_edge", "entity_id": None,
                 "edge_id": str(row["edge_id"]), "field": None, "relative_bin": None,
                 "displayed_values": [], "unit": None, "caller": str(row["caller"]),
                 "callee": str(row["callee"])} for row in rows][:32]

    if (entity is None) == (edge is None) or field is None:
        return []
    if entity is not None:
        rows = [row for row in rows if str(row.get("entity")) == str(entity)]
    else:
        rows = [row for row in rows if str(row.get("edge_id")) == str(edge)]
    if panel is not None:
        rows = [row for row in rows if str(row.get("panel_id")) == str(panel)]
    if row_index is not None:
        rows = [row for row in rows if row.get("entry_index") == int(row_index)]
    if len(rows) != 1 or field not in rows[0]:
        return []
    row, value = rows[0], rows[0][str(field)]
    entity_id = str(row["entity"]) if row.get("entity") is not None else None
    edge_id = str(row["edge_id"]) if row.get("edge_id") is not None else None
    unit = (row.get("unit") if region == "M" else
            "ms" if str(field).startswith("max_p95") else
            "count" if "count" in str(field) else "displayed")

    def record(relative_bin: int | None, displayed: Sequence[Any]) -> dict[str, Any]:
        return {"record_kind": "fact", "entity_id": entity_id, "edge_id": edge_id,
                "field": str(field), "relative_bin": relative_bin,
                "displayed_values": ["missing" if item is None else str(item) for item in displayed],
                "unit": None if unit is None else str(unit), "caller": None, "callee": None}

    if isinstance(value, list) and str(field).endswith("_16"):
        selected = bins or list(range(len(value)))
        if len(set(selected)) != len(selected) or any(index < 0 or index >= len(value) for index in selected):
            return []
        return [record(index, [value[index]]) for index in selected]
    if bins:
        return []
    return [record(None, value if isinstance(value, list) else [value])]


def normalize_typed_qa_ledger(raw: Mapping[str, Any], questions: Sequence[Mapping[str, Any]],
                              packet: Mapping[str, Any]) -> dict[str, Any]:
    """Bind fixed record-key slots to exact renderer-visible public facts."""

    expected = {str(question["query_id"]): question for question in questions}
    if set(raw) != set(expected):
        raise RQ1Error("typed selector object does not contain exactly q1/q2/q3")
    normalized, supported, unsupported = [], 0, 0
    public_index = _public_record_index(packet)
    for query_id, question in expected.items():
        row = raw.get(query_id)
        path = list(map(str, question["region_path"]))
        step_names = [f"s{index}" for index in range(1, len(path) + 1)]
        if not isinstance(row, Mapping) or set(row) != set(step_names):
            raise RQ1Error(f"typed selector slots differ for {query_id}")
        observations = []
        for index, (step_name, region) in enumerate(zip(step_names, path, strict=True), 1):
            selector = row[step_name]
            if not isinstance(selector, Mapping) or set(selector) != {"record_key", "field"}:
                raise RQ1Error(f"typed selector fields differ for {query_id}.{step_name}")
            key, requested = _normalize_record_key(selector["record_key"]), selector.get("field")
            fact = public_index.get(key)
            facts = [] if fact is None or str(fact["region"]) != region else [fact]
            entity_match = re.fullmatch(r"G:([0-9]{3,5})", key)
            if region == "G" and entity_match:
                entity = entity_match.group(1)
                facts = [fact for fact in packet["facts"] if fact["region"] == "G" and (
                    (fact["field"] == "propagation_service" and str(fact["payload"].get("service")) == entity)
                    or (fact["field"] == "directed_call_edge" and entity in {
                        str(fact["payload"].get("caller")), str(fact["payload"].get("callee"))})
                )]
            if requested is not None and not any(str(requested) in fact["payload"] for fact in facts):
                facts = []
            records = [{"record_key": _public_record_key(fact), "region": region,
                        "field": fact["field"], "payload": dict(fact["payload"]),
                        "entity_ids": list(fact.get("entity_ids") or ()), "unit": fact.get("unit")}
                       for fact in facts]
            supported += bool(records)
            unsupported += not bool(records)
            observations.append({"step": index, "region": region,
                                 "selector": dict(selector), "supported": bool(records),
                                 "records": records})
        normalized.append({"query_id": query_id, "observations": observations})
    return {"schema_version": "Stage1TypedLedgerTransferV5", "ledgers": normalized,
            "binding_audit": {"supported_steps": supported, "unsupported_steps": unsupported}}


def validate_diagnosis(payload: Mapping[str, Any], candidates: Sequence[str]) -> dict[str, Any]:
    if set(payload) != {"services", "reason", "confidence"}:
        raise RQ1Error("diagnosis fields differ from registered schema")
    services = payload.get("services")
    if not isinstance(services, list) or not 1 <= len(services) <= 5 or len(services) != len(set(map(str, services))):
        raise RQ1Error("diagnosis services must be one to five unique IDs")
    if any(re.fullmatch(r"[0-9]{3,5}", str(value)) is None for value in services):
        raise RQ1Error("diagnosis contains a non-numeric entity ID")
    if not isinstance(payload.get("reason"), str) or not payload["reason"].strip():
        raise RQ1Error("diagnosis reason is empty")
    if payload.get("confidence") not in {"high", "medium", "low"}:
        raise RQ1Error("diagnosis confidence is invalid")
    # Unknown but well-formed numeric IDs remain model outcomes and misses.
    return dict(payload)


def validate_qa_response(payload: Mapping[str, Any], questions: Sequence[Mapping[str, Any]], *, typed: bool = False) -> dict[str, Any]:
    answers = payload.get("answers")
    expected = [str(question["query_id"]) for question in questions]
    if not isinstance(answers, list) or [str(row.get("query_id")) for row in answers if isinstance(row, Mapping)] != expected:
        raise RQ1Error("Q&A response query order or membership differs")
    for row, question in zip(answers, questions, strict=True):
        steps = (row.get("answer") or {}).get("steps") if isinstance(row, Mapping) else None
        path = list(map(str, question["region_path"]))
        if not isinstance(steps, list) or len(steps) != len(path):
            raise RQ1Error("Q&A response step count differs")
        if [step.get("step") for step in steps] != list(range(1, len(path) + 1)):
            raise RQ1Error("Q&A response step sequence differs")
        if [str(step.get("region")) for step in steps] != path:
            raise RQ1Error("Q&A response region path differs")
        if any(not isinstance(step.get("values"), list) or not all(isinstance(value, str) for value in step["values"]) for step in steps):
            raise RQ1Error("Q&A response values are not string arrays")
        if typed:
            kinds = TEMPLATE_VALUE_KINDS[str(question["template"])]
            if [str(step.get("value_kind")) for step in steps] != list(kinds):
                raise RQ1Error("typed Q&A response value-kind contract differs")
    return dict(payload)


def score_reasoning(response: Mapping[str, Any], private_questions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    answer_rows = response.get("answers")
    rows = {str(row.get("query_id")): row for row in answer_rows or [] if isinstance(row, Mapping)}
    membership_ok = isinstance(answer_rows, list) and len(rows) == len(private_questions) and set(rows) == {
        str(question["query_id"]) for question in private_questions
    }
    scores: list[float] = []
    prefix: list[float] = []
    step_scores: list[float] = []
    by_level: dict[int, list[float]] = {1: [], 2: [], 3: []}
    for question in private_questions:
        expected = [list(map(str, values)) for values in question["answer_steps"]]
        observed = (rows.get(str(question["query_id"]), {}).get("answer") or {}).get("steps", [])
        normalized = [list(map(str, row.get("values", []))) for row in observed if isinstance(row, Mapping)]
        ordered_values = str(question.get("template")) == "multi_hop_path"
        matched = [
            index < len(observed) and observed[index].get("step") == index + 1
            and observed[index].get("region") == question["region_path"][index]
            and (normalized[index] == target if ordered_values else set(normalized[index]) == set(target))
            for index, target in enumerate(expected)
        ] if membership_ok else [False] * len(expected)
        complete = float(len(normalized) == len(expected) and all(matched))
        scores.append(complete)
        by_level[int(question["reasoning_level"])].append(complete)
        prefix.append(sum(itertools.takewhile(bool, matched)) / len(expected) if expected else 0.0)
        step_scores.extend(map(float, matched))
    return {
        "complete_chain_accuracy": sum(scores) / len(scores) if scores else 0.0,
        "correct_prefix_accuracy": sum(prefix) / len(prefix) if prefix else 0.0,
        "step_accuracy": sum(step_scores) / len(step_scores) if step_scores else 0.0,
        "query_membership_valid": float(membership_ok),
        **{f"level_{level}_complete_chain_accuracy": sum(values) / len(values) if values else 0.0
           for level, values in by_level.items()},
    }

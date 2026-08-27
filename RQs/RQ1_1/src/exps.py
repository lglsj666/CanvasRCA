"""RQ1.1 evidence preparation, representations, questions, tools, and prompts.

The module is an edited copy-successor of RQ1.  Its RQ-local renderer began as
the byte-identical v12 snapshot and now carries the explicitly authorized v13
timestamp, topology-context, and display-format fixes.
"""

from __future__ import annotations

import faulthandler
import hashlib
import io
import itertools
import json
import math
import os
import re
import signal
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from unified_scripts import canonical_json, stable_hash
from unified_scripts.dataset_segmentation import CaseRecord, DatasetSegmentationConfig
from vlmrca.processed import load_processed_case, load_processed_private
from vlmrca.evidence import build_canonical_evidence
from vlmrca.vlm.client import image_part, text_part

from RQs.RQ1_1.src.renderer.dashboard import (
    DASHBOARD_PROPAGATION_END,
    DASHBOARD_SIDE_SPLIT,
    RENDERER_VERSION,
    CaseRenderView,
    compile_dashboard,
    crop_dashboard_evidence_regions,
)
from RQs.RQ1_1.src.renderer.kpi_select import score_series
from RQs.RQ1_1.src.renderer.onset import pod_to_service
from RQs.RQ1_1.src.renderer.presets import make_dashboard_config

from .utils import RQ1Error, audit_visible, numeric_entity_map

if hasattr(signal, "SIGUSR1"):
    faulthandler.register(signal.SIGUSR1, all_threads=True)

Region = Literal["M", "R", "L", "G"]
REGIONS: tuple[Region, ...] = ("M", "R", "L", "G")
RCA_ARMS = ("T", "V", "S", "LV", "MV", "TCV", "TPV")
QA_ARMS = ("L1", "L2", "L3", "L4")
ENTITY_ID_NOTE = "Service names, pod names, and node names are represented by numeric IDs."

RCA_GUIDE = """Evidence guide:
- M (metrics) contains 64 relative bins, explicit missingness, units, baseline, peak, and signed robust deviation.
- R (traces) contains request/span counts, errors, p95 latency, operation names, and relative bins.
- L (logs) is a readable Denum-inspired template graph. LT identifiers are case-local; bins, multiplicity, severity, and every diagnostic number are retained.
- G (topology) contains concrete directed caller -> callee edges. A -> B means A calls B; symptoms in A can originate in B.
- Missing/null is absence, not numeric zero. All entity IDs are case-local and all times are relative.

RCA method:
Rank the origin of the incident rather than the loudest downstream symptom. Compare temporal onset, local metric/log/trace evidence, and topology-consistent propagation. Test the strongest competing origin and contradictory evidence. Return only candidates from the exhaustive candidate list.
"""

QA_GUIDE = """Answer a deterministic dashboard-reading chain. M=metrics, R=traces, L=logs, G=directed topology. Follow the listed region order: each step after the first applies to the entity obtained in the preceding step. Return displayed values exactly; `missing` is a valid value. Do not provide free-text reasoning."""

TOOL_GUIDE = """At each step choose exactly one tool call. Tools accept only case-local numeric entity IDs and relative bins. They never expose labels, dataset names, raw case IDs, absolute time, or fault type.
- search_metrics(entity_id?, metric?, start_bin?, end_bin?)
- search_traces(entity_id?, operation?, start_bin?, end_bin?)
- search_logs(entity_id?, template_id?, start_bin?, end_bin?)
- search_topology(entity_id?, direction=both|upstream|downstream)
Use the new observation to update, not merely repeat, the temporary root-cause ranking.
"""


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    task: str
    arms: tuple[str, ...]
    primary_metric: str
    calls_per_case_arm: int
    steps: int = 1


@dataclass(frozen=True)
class Question:
    query_id: str
    level: int
    regions: tuple[Region, ...]
    text: str
    answer_steps: tuple[tuple[str, ...], ...]
    supporting_fact_ids: tuple[tuple[str, ...], ...]

    def public(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "reasoning_level": self.level,
            "region_path": list(self.regions),
            "question": self.text,
        }

    def private(self) -> dict[str, Any]:
        return {
            **self.public(),
            "answer_steps": [list(values) for values in self.answer_steps],
            "supporting_fact_ids": [list(values) for values in self.supporting_fact_ids],
        }


@dataclass(frozen=True)
class PreparedCase:
    public: Mapping[str, Any]
    private: Mapping[str, Any]
    full_png: bytes
    screenshot_pngs: tuple[bytes, ...]
    region_pngs: Mapping[str, tuple[bytes, ...]]


def experiment_registry(config: Mapping[str, Any]) -> dict[str, ExperimentSpec]:
    result = {}
    for name, row in config["experiments"].items():
        result[name] = ExperimentSpec(
            name=name,
            task=str(row["task"]),
            arms=tuple(map(str, row["arms"])),
            primary_metric=str(row["primary_metric"]),
            calls_per_case_arm=int(row["model_calls_per_case_arm"]),
            steps=int(row.get("steps", 1)),
        )
    return result


def dashboard_config(config: Mapping[str, Any]):
    if int(config["renderer"]["required_version"]) != RENDERER_VERSION:
        raise RQ1Error("RQ1.1 renderer version differs from registered renderer-v13")
    return make_dashboard_config(
        config["renderer"]["preset"],
        overrides=dict(config["renderer"]["overrides"]),
        name="rq1_1_renderer_v13_numeric_identity",
    )


def _entities(view: CaseRenderView) -> set[str]:
    values = {str(v) for v in view.services if v is not None and str(v)}
    values.update(str(v) for v in view.graph.nodes if v is not None and str(v))
    values.update(str(row.service) for row in score_series(view.metrics_df, view.services))
    if view.logs_df is not None and "container_name" in view.logs_df:
        values.update(map(str, view.logs_df["container_name"].dropna()))
    if view.traces_df is not None and "service_name" in view.traces_df:
        values.update(map(str, view.traces_df["service_name"].dropna()))
    node_pod = view.metadata.get("node_pod_map") or {}
    values.update(map(str, node_pod))
    for pods in node_pod.values():
        values.update(map(str, pods or ()))
    # The propagation renderer projects pod/container identities onto their
    # service-level names before drawing its rows.  Those projected identities
    # are model-visible even when they were not members of the original
    # candidate or graph-node universe, so they must be assigned case-local
    # numeric IDs too.  Otherwise a numeric dashboard can silently retain names
    # such as ``shippingservice`` in the G panel and in the equal-information
    # text packet.
    values.update(pod_to_service(value) for value in tuple(values))
    return values


def _anonymize_text(value: Any, mapping: Mapping[str, str]) -> str:
    text = str(value or "")
    for natural in sorted(mapping, key=len, reverse=True):
        if natural:
            text = re.sub(re.escape(natural), mapping[natural], text, flags=re.IGNORECASE)
    return text


ANSI_RE = re.compile(r"\x1b(?:[@-_][0-?]*[ -/]*[@-~]|\[[0-?]*[ -/]*[@-~])")
TOKEN_RE = re.compile(
    r"(?P<uuid>\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b)"
    r"|(?P<ip>\b(?:\d{1,3}\.){3}\d{1,3}\b)"
    r"|(?P<hex>\b0x[0-9a-fA-F]+\b)"
    r"|(?P<num>(?<![A-Za-z0-9_])-?(?:\d+\.\d+|\d+)(?:[eE][+-]?\d+)?(?![A-Za-z0-9_]))"
)


def _normalize_message(value: Any, mapping: Mapping[str, str]) -> str:
    text = ANSI_RE.sub("", _anonymize_text(value, mapping)).strip()
    text = re.sub(r"^(?:\d{4}-\d\d-\d\d[T ]\S+\s+)", "", text)
    return re.sub(r"\s+", " ", text)


def _tokenize_template(message: str) -> tuple[str, list[dict[str, str]]]:
    counters: Counter[str] = Counter()
    tokens: list[dict[str, str]] = []

    def replace_token(match: re.Match[str]) -> str:
        kind = str(match.lastgroup)
        counters[kind] += 1
        placeholder = f"{{{kind}{counters[kind]}}}"
        tokens.append({"placeholder": placeholder, "kind": kind, "value": match.group(0)})
        return placeholder

    return TOKEN_RE.sub(replace_token, message), tokens


def _encode_series(values: Sequence[str]) -> dict[str, Any]:
    if not values:
        return {"encoding": "values", "values": []}
    if len(set(values)) == 1:
        return {"encoding": "constant", "value": values[0], "count": len(values)}
    runs: list[list[Any]] = []
    for value in values:
        if runs and runs[-1][0] == value:
            runs[-1][1] += 1
        else:
            runs.append([value, 1])
    if len(runs) <= len(values) // 2:
        return {"encoding": "rle", "runs": runs}
    try:
        numbers = [float(v) for v in values]
        deltas = [numbers[i] - numbers[i - 1] for i in range(1, len(numbers))]
        canonical_numbers = all(format(number, ".15g") == raw for number, raw in zip(numbers, values, strict=True))
        if canonical_numbers and len(set(round(v, 12) for v in deltas)) <= max(2, len(deltas) // 3):
            return {"encoding": "base_deltas", "base": values[0], "deltas": deltas}
    except ValueError:
        pass
    return {"encoding": "values", "values": list(values)}


def _decode_series(value: Mapping[str, Any]) -> list[str]:
    encoding = value["encoding"]
    if encoding == "constant":
        return [str(value["value"])] * int(value["count"])
    if encoding == "rle":
        return [str(item) for item, count in value["runs"] for _ in range(int(count))]
    if encoding == "base_deltas":
        current = float(value["base"])
        output = [str(value["base"])]
        for delta in value["deltas"]:
            current += float(delta)
            output.append(format(current, ".15g"))
        return output
    return list(map(str, value.get("values") or ()))


def _restore_template(template: str, tokens: Sequence[Mapping[str, str]]) -> str:
    text = template
    for token in tokens:
        text = text.replace(str(token["placeholder"]), str(token["value"]), 1)
    return text


def build_denum_log_graph(
    logs: pd.DataFrame, mapping: Mapping[str, str], *, bins: int = 64,
) -> dict[str, Any]:
    """Build a readable, losslessly decodable Denum-inspired public log graph."""

    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    if logs is not None and not logs.empty:
        clock = pd.to_numeric(logs.get("timestamp"), errors="coerce")
        finite = clock[np.isfinite(clock)]
        lo = float(finite.min()) if len(finite) else 0.0
        hi = float(finite.max()) if len(finite) else lo
        width = max(hi - lo, 1.0)
        for index, source in logs.iterrows():
            stamp = float(clock.loc[index]) if np.isfinite(clock.loc[index]) else lo
            relative_bin = min(bins - 1, max(0, int((stamp - lo) / width * bins)))
            entity = mapping.get(str(source.get("container_name") or ""), "missing")
            message = _normalize_message(source.get("message"), mapping)
            template, tokens = _tokenize_template(message)
            rows.append({
                "entity_id": entity,
                "relative_bin": relative_bin,
                "level": str(source.get("level") or "unknown").casefold(),
                "template": template,
                "tokens": tokens,
                "normalized_message": message,
            })

    templates = {text: f"LT{index:02d}" for index, text in enumerate(sorted({r["template"] for r in rows}), 1)}
    grouped: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["entity_id"], templates[row["template"]], row["relative_bin"], row["level"])].append(row)

    entries = []
    reconstructed: Counter[tuple[str, int, str, str]] = Counter()
    original: Counter[tuple[str, int, str, str]] = Counter()
    for (entity, template_id, relative_bin, level), events in sorted(grouped.items()):
        template = events[0]["template"]
        placeholders = [token["placeholder"] for token in events[0]["tokens"]]
        columns = {
            placeholder: _encode_series([
                next((token["value"] for token in event["tokens"] if token["placeholder"] == placeholder), "missing")
                for event in events
            ])
            for placeholder in placeholders
        }
        decoded = {key: _decode_series(value) for key, value in columns.items()}
        for position, event in enumerate(events):
            token_rows = [
                {"placeholder": placeholder, "value": decoded[placeholder][position]}
                for placeholder in placeholders
            ]
            rebuilt = _restore_template(template, token_rows)
            reconstructed[(entity, relative_bin, level, rebuilt)] += 1
            original[(entity, relative_bin, level, event["normalized_message"])] += 1
        entries.append({
            "entity_id": entity,
            "template_id": template_id,
            "template": template,
            "relative_bin": relative_bin,
            "level": level,
            "count": len(events),
            "numeric_variables": columns,
        })
    if original != reconstructed:
        raise RQ1Error("Denum semantic round-trip failed")
    source_chars = sum(len(row["normalized_message"]) for row in rows)
    graph = {
        "schema_version": "DenumReadableLogGraphV1",
        "binary_output": False,
        "relative_bins": bins,
        "templates": [
            {"template_id": templates[text], "template": text}
            for text in sorted(templates)
        ],
        "entries": entries,
        "event_count": len(rows),
        "template_count": len(templates),
        "source_characters": source_chars,
        "graph_characters": 0,
        "semantic_round_trip": True,
    }
    graph["graph_characters"] = len(canonical_json(graph))
    graph["character_compression_ratio"] = (
        graph["graph_characters"] / source_chars if source_chars else 0.0
    )
    lexical = re.compile(r"\w+|[^\w\s]", re.UNICODE)
    source_token_count = sum(len(lexical.findall(row["normalized_message"])) for row in rows)
    graph_token_count = len(lexical.findall(canonical_json(graph)))
    graph["tokenizer_contract"] = "DenumDiagnosticTokenizerV1"
    graph["source_token_count"] = source_token_count
    graph["graph_token_count"] = graph_token_count
    graph["tokenizer_token_compression_ratio"] = (
        graph_token_count / source_token_count if source_token_count else 0.0
    )
    graph["graph_hash"] = stable_hash(graph)
    graph["_processing_time_s"] = time.perf_counter() - started
    return graph


def denum_visible_rows(graph: Mapping[str, Any], limit: int = 8) -> list[dict[str, Any]]:
    entries = sorted(
        graph.get("entries") or (),
        key=lambda row: (-int(row["count"]), str(row["template_id"]), str(row["entity_id"]), int(row["relative_bin"])),
    )[:limit]
    output = []
    for source in entries:
        columns = dict(source.get("numeric_variables") or {})
        preview = {}
        for placeholder in sorted(columns)[:3]:
            values = _decode_series(columns[placeholder])
            frequencies = Counter(values)
            preview[placeholder] = {
                "sample_count": len(values),
                "first": values[0] if values else "missing",
                "last": values[-1] if values else "missing",
                "distinct_count": len(frequencies),
                "most_common": [list(item) for item in sorted(
                    frequencies.items(), key=lambda item: (-item[1], item[0]),
                )[:2]],
            }
        output.append({
            key: source[key]
            for key in ("entity_id", "template_id", "template", "relative_bin", "level", "count")
        } | {
            "numeric_preview": preview,
            "omitted_numeric_variables": max(0, len(columns) - len(preview)),
            "full_numeric_series_available_via_search_logs": bool(columns),
        })
    return output


def denum_text(graph: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> str:
    lines = ["DenumLogTextV1 (readable text/graph; no binary encoding)"]
    for row in rows:
        lines.append(
            f"{row['template_id']} entity={row['entity_id']} bin={row['relative_bin']:02d} "
            f"level={row['level']} count={row['count']} template={json.dumps(row['template'])} "
            f"numeric_preview={canonical_json(row['numeric_preview'])} "
            f"omitted_numeric_variables={row['omitted_numeric_variables']} "
            f"full_series_via_search_logs={str(row['full_numeric_series_available_via_search_logs']).lower()}"
        )
    if not rows:
        lines.append("logs=missing")
    return "\n".join(lines) + "\n"


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    choices = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in choices:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    output: list[str] = []
    rest = text
    while rest:
        if draw.textbbox((0, 0), rest, font=font)[2] <= width:
            output.append(rest)
            break
        low, high = 1, len(rest)
        while low < high:
            midpoint = (low + high + 1) // 2
            if draw.textbbox((0, 0), rest[:midpoint], font=font)[2] <= width:
                low = midpoint
            else:
                high = midpoint - 1
        end = low
        output.append(rest[:end])
        rest = rest[end:]
    return output or [""]


def overlay_denum_log_region(
    png: bytes, config: Any, graph: Mapping[str, Any], rows: Sequence[Mapping[str, Any]],
) -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
    """Replace only renderer-v13's L rectangle with its readable Denum projection."""

    image = Image.open(io.BytesIO(png)).convert("RGB")
    base_height = int(config.long_side_px * config.canvas_aspect)
    split = round(image.width * DASHBOARD_SIDE_SPLIT)
    start = round(base_height * DASHBOARD_PROPAGATION_END)
    end = start + (base_height - start) // 2
    box = (split, start, image.width, end)
    draw = ImageDraw.Draw(image)
    draw.rectangle(box, fill="white", outline="#455a64", width=2)
    title_font, body_font = _font(17, True), _font(11)
    x, y = split + 12, start + 8
    draw.text((x, y), "L — DENUM-READABLE LOG GRAPH", fill="#20343e", font=title_font)
    y += 26
    max_width = image.width - x - 10
    line_height = 14
    selected: list[dict[str, Any]] = []
    for row in rows:
        raw = denum_text(graph, [row]).splitlines()[1]
        wrapped = _wrap(draw, raw, body_font, max_width)
        if y + line_height * len(wrapped) > end - 5:
            continue
        selected.append(dict(row))
        for line in wrapped:
            draw.text((x, y), line, fill="#263238", font=body_font)
            y += line_height
    if rows and not selected:
        raise RQ1Error("no complete Denum visible row fits registered renderer-v13 L region")
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=False, compress_level=6)
    output = stream.getvalue()
    audit = {
        "schema_version": "DenumLogVisualRowsV1",
        "source_image_sha256": hashlib.sha256(png).hexdigest(),
        "output_image_sha256": hashlib.sha256(output).hexdigest(),
        "box_px": list(box),
        "graph_hash": graph["graph_hash"],
        "candidate_rows_hash": stable_hash(rows),
        "visible_rows_hash": stable_hash(selected),
        "visible_row_count": len(selected),
        "renderer_source_modified": False,
    }
    return output, audit, selected


def _display_number(value: Any) -> str | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not math.isfinite(number):
        return None
    return format(number, ".4g")


def _display_z(value: Any) -> str | None:
    rendered = _display_number(value)
    return None if rendered is None else rendered


def _display_minute(value: Any) -> str | None:
    try:
        return f"{float(value) / 60.0:+.1f}m"
    except (TypeError, ValueError):
        return None


def _metric_unit(metric: str) -> str:
    name = metric.casefold()
    if any(word in name for word in ("latency", "duration", "p50", "p95", "p99")):
        return "milliseconds_or_source_unit"
    if any(word in name for word in ("rate", "ratio", "util", "percent")):
        return "ratio_or_percent"
    return "source_unit"


def _atomic_fact(region: str, field: str, payload: Mapping[str, Any], *, entities: Iterable[str] = (), bins: Iterable[int] = (), unit: str | None = None) -> dict[str, Any]:
    body = {
        "region": region,
        "field": field,
        "entity_ids": sorted(set(map(str, entities))),
        "relative_bins": sorted(set(map(int, bins))),
        "unit": unit,
        "payload": dict(payload),
    }
    return {"fact_id": hashlib.sha256(canonical_json(body).encode()).hexdigest()[:16], **body}


def build_visible_packet(
    ceb: Mapping[str, Any], renderer_fingerprint: str, source_manifest_hash: str,
) -> dict[str, Any]:
    """RQ1.1 renderer-v13 semantic fact contract."""

    candidates = list(map(str, ceb.get("candidates") or ()))
    metrics = list(ceb.get("metric_series") or ())
    if (
        not candidates
        or candidates != sorted(set(candidates))
        or any(not value.isdigit() for value in candidates)
    ):
        raise RQ1Error("renderer candidate inventory is not numeric and exhaustive")
    if len(metrics) != 12 or any(len(row.get("values") or ()) != 64 for row in metrics):
        raise RQ1Error("renderer-v13 packet requires twelve 64-bin metric series")
    facts = [
        _atomic_fact("C", "candidate_set", {"fixed_order": candidates, "count": len(candidates)}, entities=candidates),
        _atomic_fact("C", "evidence_legends", {
            "entity_ids": ENTITY_ID_NOTE,
            "directed_edges": "caller -> callee means caller invokes callee",
            "relative_time": "64 equal relative bins; null is missing",
            "source_comparability": "metric and trace anomaly scales are not directly comparable",
        }),
        _atomic_fact("M", "observation_window", dict(ceb.get("observation_window") or {}), unit="relative_seconds"),
        _atomic_fact("M", "estimated_fault_window", {
            "start": _display_minute((ceb.get("fault_window_rel_s") or [None, None])[0]),
            "end": _display_minute((ceb.get("fault_window_rel_s") or [None, None])[1]),
        }, unit="displayed_relative_minutes"),
    ]
    for row in metrics:
        values = [_display_number(value) for value in row.get("values") or ()]
        payload = {
            "panel_id": row.get("panel_id"), "rank": row.get("rank"),
            "service": str(row.get("service")), "metric": str(row.get("metric")),
            "values": values, "missing_mask": list(row.get("missing_mask") or ()),
            "baseline": _display_number(row.get("baseline")),
            "peak": _display_number(row.get("peak")), "signed_z": _display_z(row.get("signed_z")),
        }
        facts.append(_atomic_fact(
            "M", "metric_series_64", payload, entities=(payload["service"],),
            bins=range(64), unit=_metric_unit(payload["metric"]),
        ))
    summary = dict(ceb.get("trace_summary") or {})
    facts.append(_atomic_fact("R", "trace_summary_meta", {key: value for key, value in summary.items() if key != "entries"}))
    for index, source in enumerate(summary.get("entries") or ()):
        payload = {"entry_index": index, **dict(source)}
        payload.pop("rendered_service", None)
        payload.pop("spans", None)
        for key in ("p95_pre_ms", "p95_during_ms"):
            payload[key] = _display_number(payload.get(key))
        if payload.get("delta_pct") is not None:
            rounded_delta = round(float(payload["delta_pct"]))
            payload["delta_pct"] = "0" if rounded_delta == 0 else str(rounded_delta)
        if payload.get("error_pct") is not None:
            payload["error_pct"] = f"{float(payload['error_pct']):.1f}"
        entity = str(payload.get("service") or "")
        facts.append(_atomic_fact("R", "trace_summary_entry", payload, entities=(entity,) if entity else (), unit="milliseconds_and_fraction"))
    propagation = dict(ceb.get("propagation") or {})
    facts.append(_atomic_fact("G", "propagation_meta", {
        key: propagation.get(key)
        for key in (
            "mode", "selection_mode", "context_services",
            "omitted_services", "omitted_edges",
        )
    }))
    for source in propagation.get("services") or ():
        payload = dict(source)
        payload["onset_rel_min_display"] = _display_minute(payload.pop("onset_rel_s", None))
        payload["severity_z_display"] = _display_z(payload.pop("severity_z", None))
        payload["evidence_source_display"] = {"trace": "R", "metric": "M"}.get(str(payload.pop("evidence_source", "none")), "none")
        entity = str(payload.get("service"))
        facts.append(_atomic_fact("G", "propagation_service", payload, entities=(entity,), unit="displayed_minutes_and_z_source"))
    for index, edge in enumerate(propagation.get("directed_call_edges") or ()):
        payload = {"edge_index": index, "caller": str(edge["caller"]), "callee": str(edge["callee"])}
        facts.append(_atomic_fact("G", "directed_call_edge", payload, entities=(payload["caller"], payload["callee"])))
    missing = dict(ceb.get("missingness") or {})
    for region, key in (("R", "traces_missing"), ("G", "propagation_missing")):
        facts.append(_atomic_fact(region, "explicit_missingness", {key: bool(missing.get(key))}))
    visible_entities = {
        str(entity)
        for fact in facts
        for entity in fact.get("entity_ids", ())
    }
    outside_candidates = sorted(visible_entities.difference(candidates))
    if outside_candidates:
        raise RQ1Error(
            "model-visible entity IDs are absent from the exhaustive candidate set: "
            + ",".join(outside_candidates[:10])
        )
    facts.sort(key=lambda fact: (str(fact["region"]), str(fact["field"]), str(fact["fact_id"])))
    packet = {
        "schema_version": "RQ1_1EvidencePacketV1", "opaque_incident_id": ceb["opaque_incident_id"],
        "candidates": candidates, "facts": facts, "source_manifest_hash": source_manifest_hash,
        "renderer_fingerprint": renderer_fingerprint, "fact_inventory_hash": stable_hash(facts),
    }
    packet["packet_hash"] = stable_hash(packet)
    return packet


def _replace_log_facts(packet: Mapping[str, Any], graph: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    facts = [dict(fact) for fact in packet["facts"] if fact["region"] != "L"]
    facts.append(_atomic_fact("L", "denum_log_meta", {
        key: graph[key] for key in ("schema_version", "binary_output", "event_count", "template_count", "semantic_round_trip")
    }))
    for row in rows:
        facts.append(_atomic_fact(
            "L", "denum_log_template", row,
            entities=(row["entity_id"],), bins=(row["relative_bin"],), unit="count_and_bounded_numeric_preview",
        ))
    if not rows:
        facts.append(_atomic_fact("L", "explicit_missingness", {"logs_missing": True}))
    facts.sort(key=lambda fact: (str(fact["region"]), str(fact["field"]), str(fact["fact_id"])))
    output = {**dict(packet), "facts": facts, "fact_inventory_hash": stable_hash(facts)}
    output["packet_hash"] = stable_hash({key: value for key, value in output.items() if key != "packet_hash"})
    return output


def _natural_fact_line(fact: Mapping[str, Any]) -> str:
    labels = {"M": "Metric", "R": "Trace", "L": "Log", "G": "Topology"}
    return (
        f"{labels.get(str(fact['region']), 'Common')} evidence; field={fact['field']}; "
        f"entities={canonical_json(fact['entity_ids'])}; bins={canonical_json(fact['relative_bins'])}; "
        f"unit={canonical_json(fact.get('unit'))}; details={canonical_json(fact['payload'])}"
    )


def packet_text(packet: Mapping[str, Any], regions: Iterable[str] = REGIONS) -> str:
    wanted = set(regions)
    order = {region: index for index, region in enumerate(REGIONS)}
    facts = sorted(
        (fact for fact in packet["facts"] if fact["region"] in wanted),
        key=lambda fact: (order[str(fact["region"])], str(fact["field"]), str(fact["fact_id"])),
    )
    return "=== INCIDENT EVIDENCE (M/R/L/G) ===\n" + "\n".join(map(_natural_fact_line, facts)) + "\n"


def tagged_text_part(text: str, label: str) -> dict[str, Any]:
    """Attach analysis-only spans without changing model-visible text bytes."""

    part = text_part(text)
    spans: list[dict[str, Any]] = []
    cursor = 0
    evidence_labels = {
        "Metric evidence;": "M", "Trace evidence;": "R",
        "Log evidence;": "L", "Topology evidence;": "G",
    }
    for line in text.splitlines(keepends=True):
        line_label = label
        for prefix, region in evidence_labels.items():
            if line.startswith(prefix):
                line_label = region
                break
        if line.startswith("Candidate IDs"):
            line_label = "candidates"
        elif line.startswith("Entity names") or line.startswith("Service names"):
            line_label = "legend"
        elif line.startswith("Common evidence;"):
            line_label = "common"
        spans.append({"label": line_label, "start": cursor, "end": cursor + len(line)})
        cursor += len(line)
    if cursor < len(text):
        spans.append({"label": label, "start": cursor, "end": len(text)})
    part["attention_region"] = label
    part["attention_spans"] = spans or [{"label": label, "start": 0, "end": len(text)}]
    return part


def _wrap_visible_line(
    draw: ImageDraw.ImageDraw, line: str, font: ImageFont.ImageFont, max_width: int,
) -> list[str]:
    """Losslessly wrap one T-arm line using the inherited pixel-text geometry."""

    remaining, output = line, []
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


def compile_text_screenshot(text: str, max_pages: int = 8) -> tuple[bytes, ...]:
    """Render the exact T fragment with RQ1's mature pixel-text transport.

    The inherited 1800x1600 geometry, fonts, line height, measured wrapping,
    PNG encoding, and page bound are retained.  Unlike a semantic summary,
    every source line—including its M/R/L/G evidence prefix—is transported in
    its original order.  Page wrapping changes pixels, never source bytes.
    """

    width, height, margin, line_height = 1800, 1600, 32, 24
    font = _font(17)
    probe = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(probe)
    wrapped = [
        line
        for raw in text.splitlines()
        for line in _wrap_visible_line(draw, raw, font, width - 2 * margin)
    ]
    page_capacity = (height - 2 * margin) // line_height
    pages: list[bytes] = []
    for start in range(0, len(wrapped), page_capacity):
        if len(pages) >= max_pages:
            raise RQ1Error("T incident fragment exceeds eight lossless screenshot pages")
        image = Image.new("RGB", (width, height), "#FFFFFF")
        page_draw = ImageDraw.Draw(image)
        for row, line in enumerate(wrapped[start:start + page_capacity]):
            page_draw.text(
                (margin, margin + row * line_height), line,
                fill="#111827", font=font,
            )
        stream = io.BytesIO()
        image.save(stream, format="PNG", optimize=False, compress_level=6)
        pages.append(stream.getvalue())
    if not pages:
        raise RQ1Error("T incident fragment is empty")
    return tuple(pages)


def _metric_tool_rows(view: CaseRenderView, mapping: Mapping[str, str]) -> list[dict[str, Any]]:
    frame = view.metrics_df
    if frame is None or frame.empty:
        return []
    output = []
    for column in sorted(c for c in frame.columns if c != "timestamp"):
        values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
        chunks = np.array_split(values, 64)
        binned = [_display_number(np.nanmedian(chunk)) if np.isfinite(chunk).any() else None for chunk in chunks]
        natural = next((entity for entity in sorted(mapping, key=len, reverse=True) if str(column).startswith(entity + "_")), "")
        entity = mapping.get(natural, "missing")
        metric = _anonymize_text(str(column)[len(natural) + 1:] if natural else column, mapping)
        output.append({"entity_id": entity, "metric": metric, "values": binned, "missing_mask": [v is None for v in binned]})
    return output


def _trace_tool_rows(view: CaseRenderView, mapping: Mapping[str, str]) -> list[dict[str, Any]]:
    frame = view.traces_df
    if frame is None or frame.empty:
        return []
    clock = pd.to_numeric(frame["timestamp"], errors="coerce")
    finite = clock[np.isfinite(clock)]
    lo, hi = (float(finite.min()), float(finite.max())) if len(finite) else (0.0, 0.0)
    width = max(hi - lo, 1.0)
    rows = []
    for (service, operation), group in frame.groupby(["service_name", "operation_name"], dropna=False):
        bins = [0] * 64
        errors = [0] * 64
        latencies: list[list[float]] = [[] for _ in range(64)]
        for index, row in group.iterrows():
            stamp = float(clock.loc[index]) if np.isfinite(clock.loc[index]) else lo
            bucket = min(63, max(0, int((stamp - lo) / width * 64)))
            bins[bucket] += 1
            status = str(row.get("status_code") or "").casefold()
            errors[bucket] += int("error" in status or status.startswith("5"))
            duration = pd.to_numeric(pd.Series([row.get("duration_ms")]), errors="coerce").iloc[0]
            if np.isfinite(duration):
                latencies[bucket].append(float(duration))
        rows.append({
            "entity_id": mapping.get(str(service), "missing"),
            "operation": _anonymize_text(operation, mapping),
            "spans": bins,
            "errors": errors,
            "p95_ms": [_display_number(np.percentile(value, 95)) if value else None for value in latencies],
        })
    return sorted(rows, key=lambda row: (str(row["entity_id"]), str(row["operation"])))


def _topology_tool_rows(view: CaseRenderView, mapping: Mapping[str, str]) -> list[dict[str, str]]:
    return sorted(
        ({"caller": mapping.get(str(a), "missing"), "callee": mapping.get(str(b), "missing")} for a, b in view.graph.edges),
        key=lambda row: (row["caller"], row["callee"]),
    )


def _common_shell(packet: Mapping[str, Any]) -> str:
    common = [fact for fact in packet["facts"] if fact["region"] == "C"]
    return (
        ENTITY_ID_NOTE + "\nCandidate IDs (exhaustive, fixed order): " + canonical_json(packet["candidates"]) + "\n" +
        "\n".join(_natural_fact_line(fact) for fact in common) + "\n"
    )


def _region_rows(packet: Mapping[str, Any], region: str) -> list[Mapping[str, Any]]:
    return [fact for fact in packet["facts"] if fact["region"] == region]


def _first_region_entity(packet: Mapping[str, Any], region: Region) -> tuple[str, tuple[str, ...], str]:
    """Return a label-blind entity anchor selected by a visible region-local key."""

    rows = _region_rows(packet, region)
    if region == "M":
        eligible = [row for row in rows if row["field"] == "metric_series_64"]
        row = min(eligible, key=lambda item: str(item["payload"].get("panel_id"))) if eligible else None
        cue = "read the entity ID in the lexicographically smallest metric panel ID"
    elif region == "R":
        eligible = [row for row in rows if row["field"] == "trace_summary_entry"]
        row = min(eligible, key=lambda item: int(item["payload"].get("entry_index", 10**9))) if eligible else None
        cue = "read the entity ID in the first displayed trace summary row"
    elif region == "L":
        eligible = [row for row in rows if row["field"] == "denum_log_template"]
        row = min(
            eligible,
            key=lambda item: (
                str(item["payload"].get("template_id")),
                int(item["payload"].get("relative_bin", 10**9)),
            ),
        ) if eligible else None
        cue = "read the entity ID in the lowest LT-ID/relative-bin log row"
    else:
        eligible = [row for row in rows if row["field"] == "directed_call_edge"]
        row = min(eligible, key=lambda item: int(item["payload"].get("edge_index", 10**9))) if eligible else None
        cue = "read the caller ID of the first displayed directed edge"
    if row is None or not row.get("entity_ids"):
        return "missing", tuple(), cue
    if region == "G":
        entity = str(row["payload"]["caller"])
    else:
        entity = str(row["entity_ids"][0])
    return entity, (str(row["fact_id"]),), cue


def _step_value(
    packet: Mapping[str, Any], region: Region, entity: str, *, has_next: bool,
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """Read one displayed region fact and carry its entity into the next step."""

    rows = [fact for fact in _region_rows(packet, region) if entity in fact.get("entity_ids", ())]
    if region == "M" and rows:
        row = next((item for item in rows if item["field"] == "metric_series_64"), rows[0])
        payload = row["payload"]
        value = (
            entity,
            str(payload.get("panel_id") or "missing"),
            str(payload.get("metric") or "missing"),
            str(payload.get("peak") or "missing"),
            str(payload.get("signed_z") or "missing"),
        )
        return value, (str(row["fact_id"]),), "report entity ID, panel ID, metric, displayed peak, and displayed signed-z"
    if region == "R" and rows:
        row = next((item for item in rows if item["field"] == "trace_summary_entry"), rows[0])
        payload = row["payload"]
        value = (
            entity,
            str(payload.get("p95_during_ms") or "missing"),
            str(payload.get("error_pct") or "missing"),
        )
        return value, (str(row["fact_id"]),), "report entity ID, displayed during-window p95, and error percentage"
    if region == "L" and rows:
        row = next((item for item in rows if item["field"] == "denum_log_template"), rows[0])
        payload = row["payload"]
        value = (
            entity,
            str(payload.get("template_id") or "missing"),
            str(payload.get("relative_bin", "missing")),
            str(payload.get("level") or "missing"),
            str(payload.get("count", "missing")),
        )
        return value, (str(row["fact_id"]),), "report entity ID, LT template ID, relative bin, level, and count"
    if region == "G":
        edges = [fact for fact in _region_rows(packet, "G") if fact["field"] == "directed_call_edge"]
        upstream = sorted({str(fact["payload"]["caller"]) for fact in edges if str(fact["payload"]["callee"]) == entity})
        downstream = sorted({str(fact["payload"]["callee"]) for fact in edges if str(fact["payload"]["caller"]) == entity})
        support = tuple(str(fact["fact_id"]) for fact in edges if entity in fact.get("entity_ids", ()))
        if has_next:
            choices = sorted([(value, "upstream") for value in upstream] + [(value, "downstream") for value in downstream])
            if choices:
                neighbor, direction = choices[0]
                return (neighbor, direction), support, "select the lexicographically smallest direct neighbor and report neighbor ID plus direction"
            return ("missing", "missing"), support, "report missing because no direct neighbor is displayed"
        value = (entity, "upstream", *upstream, "|", "downstream", *downstream)
        return value, support, "report entity ID, all sorted upstream IDs, '|', and all sorted downstream IDs"
    return (entity, "missing"), tuple(str(row["fact_id"]) for row in rows), "report entity ID and missing"


def questions_for_case(packet: Mapping[str, Any], opaque_id: str, seed: int = 42) -> tuple[list[Question], list[Question]]:
    """Build all 64 ordered-region templates and select one per level label-blindly."""

    pools: dict[int, list[Question]] = defaultdict(list)
    for level in range(1, 5):
        for path in itertools.permutations(REGIONS, level):
            anchor, anchor_support, anchor_cue = _first_region_entity(packet, path[0])
            answers: list[tuple[str, ...]] = []
            supports: list[tuple[str, ...]] = []
            instructions = [
                f"Start in {path[0]}: {anchor_cue}. This is the current entity for Step 1."
            ]
            current = anchor
            for index, region in enumerate(path, 1):
                value, support, detail = _step_value(
                    packet, region, current, has_next=index < len(path),
                )
                answers.append(value)
                supports.append(tuple(dict.fromkeys((*anchor_support, *support))) if index == 1 else support)
                instructions.append(f"Step {index} ({region}): for the current entity, {detail}.")
                if index < len(path):
                    current = str(value[0])
                    instructions.append(
                        f"Carry the first returned value from Step {index} as the current entity for Step {index + 1}."
                    )
            code = "".join(path)
            pools[level].append(Question(
                query_id=f"L{level}-{code}", level=level, regions=path,
                text="\n".join(instructions), answer_steps=tuple(answers),
                supporting_fact_ids=tuple(supports),
            ))
    expected = {1: 4, 2: 12, 3: 24, 4: 24}
    if {level: len(pool) for level, pool in pools.items()} != expected:
        raise RQ1Error("direct-QA template registry is incomplete")
    selected = []
    for level in range(1, 5):
        digest = hashlib.sha256(f"{seed}:{opaque_id}:{level}".encode()).digest()
        selected.append(pools[level][int.from_bytes(digest, "big") % len(pools[level])])
    return [question for level in range(1, 5) for question in pools[level]], selected


def prepare_case(dataset: str, case_id: str, config: Mapping[str, Any], opaque_id: str | None = None) -> PreparedCase:
    prep_started = time.perf_counter()

    def mark(stage: str) -> None:
        print(
            f"[rq1.1-prepare] pid={os.getpid()} dataset={dataset} stage={stage} "
            f"elapsed_s={time.perf_counter() - prep_started:.3f}",
            flush=True,
        )

    mark("start")
    case = load_processed_case(dataset, case_id)
    mark("case_loaded")
    if opaque_id is None:
        split = DatasetSegmentationConfig.load(config["unified"]["segmentation"])
        opaque_id = split.opaque_id(CaseRecord(dataset, case_id, Path(".")))
    view = replace(CaseRenderView.from_case(case), case_id=opaque_id)
    mapping, granularities = numeric_entity_map(_entities(view), opaque_id, int(config["seed"]))
    numeric_view = replace(view, entity_display_labels=mapping)
    renderer_cfg = dashboard_config(config)
    source_png, manifest = compile_dashboard(numeric_view, renderer_cfg)
    mark("dashboard_compiled")
    denum_graph = build_denum_log_graph(view.logs_df, mapping, bins=int(config["external_methods"]["denum"]["relative_bins"]))
    mark("denum_graph_built")
    denum_processing_time_s = float(denum_graph.pop("_processing_time_s"))
    visible_log_candidates = denum_visible_rows(
        denum_graph, int(config["external_methods"]["denum"]["visible_template_limit"]),
    )
    full_png, denum_visual_audit, visible_logs = overlay_denum_log_region(
        source_png, renderer_cfg, denum_graph, visible_log_candidates,
    )
    mark("denum_overlay_rendered")
    ceb = build_canonical_evidence(manifest)
    # ``manifest.services`` is inherited from the dataset's historical
    # candidate field.  Its granularity is inconsistent across datasets (for
    # example, AIOPS-2022 contains pods/nodes but omits service identities),
    # while the dashboard and tools legitimately expose all three entity
    # granularities.  The registered candidate list must therefore be the
    # complete label-blind entity universe used to build the case-local ID
    # mapping, not that legacy subset.  This also guarantees that every entity
    # the model can observe or retrieve is a legal ranking candidate.
    ceb = {**ceb, "candidates": sorted(set(mapping.values()))}

    packet = build_visible_packet(
        ceb, str(manifest["config_fingerprint"]), stable_hash(manifest)
    )
    packet = _replace_log_facts(packet, denum_graph, visible_logs)
    text_b = packet_text(packet)
    screenshot_pngs = compile_text_screenshot(text_b)
    mark("pixel_text_compiled")
    region_pngs, crop_audit = crop_dashboard_evidence_regions(full_png, renderer_cfg)
    templates, selected = questions_for_case(packet, opaque_id, int(config["seed"]))
    mark("regions_and_questions_compiled")

    metric_tools = _metric_tool_rows(view, mapping)
    mark("metric_tool_indexed")
    trace_tools = _trace_tool_rows(view, mapping)
    mark("trace_tool_indexed")
    topology_tools = _topology_tool_rows(view, mapping)
    mark("topology_tool_indexed")
    tool_index = {
        "schema_version": "RQ1_1CanonicalToolIndexV1",
        "metrics": metric_tools,
        "traces": trace_tools,
        "logs": denum_graph,
        "topology": topology_tools,
    }
    tool_index["tool_index_hash"] = stable_hash(tool_index)
    representation = representation_audit(packet, full_png, screenshot_pngs, region_pngs, text_b)
    public = {
        "schema_version": "RQ1_1PreparedPublicV1",
        "opaque_incident_id": opaque_id,
        "renderer_version": RENDERER_VERSION,
        "packet": packet,
        "tool_index": tool_index,
        "all_question_templates": [q.public() for q in templates],
        "selected_questions": [q.public() for q in selected],
        "representation_audit": representation,
        "denum_audit": {
            "graph_hash": denum_graph["graph_hash"],
            "semantic_round_trip": denum_graph["semantic_round_trip"],
            "character_compression_ratio": denum_graph["character_compression_ratio"],
            "tokenizer_contract": denum_graph["tokenizer_contract"],
            "tokenizer_token_compression_ratio": denum_graph["tokenizer_token_compression_ratio"],
            "source_characters": denum_graph["source_characters"],
            "graph_characters": denum_graph["graph_characters"],
            "event_count": denum_graph["event_count"],
            "template_count": denum_graph["template_count"],
            "visual": denum_visual_audit,
        },
        "full_image_sha256": hashlib.sha256(full_png).hexdigest(),
        "screenshot_image_sha256": [hashlib.sha256(value).hexdigest() for value in screenshot_pngs],
        "region_image_sha256": {key: [hashlib.sha256(value).hexdigest() for value in values] for key, values in region_pngs.items()},
        "region_crop_audit": crop_audit,
    }

    # Labels and natural identities are opened only after every model-visible
    # artifact and tool index has been compiled.
    evaluator = load_processed_private(dataset, case_id)
    labels = dict(evaluator.get("labels") or {})
    accepted = [str(labels.get("root_cause") or "")]
    accepted.extend(map(str, labels.get("root_cause_candidates") or ()))
    private = {
        "schema_version": "RQ1_1PrivateEvaluatorV1",
        "opaque_incident_id": opaque_id,
        "dataset": dataset,
        "source_case_id": case_id,
        "fault_type": str(labels.get("fault_type") or evaluator.get("fault_type") or "unknown"),
        "numeric_to_natural": {numeric: natural for natural, numeric in mapping.items()},
        "entity_granularity": granularities,
        "accepted_labels": sorted(set(filter(None, accepted))),
        "selected_questions": [q.private() for q in selected],
        "denum_processing_time_s": denum_processing_time_s,
    }
    markers = (
        case_id, dataset, labels.get("root_cause"),
        (evaluator.get("event") or {}).get("absolute_timestamp"),
        (case.metadata or {}).get("processed_path"),
    )
    audit_visible(public, (*markers, *mapping.keys()))
    mark("complete")
    return PreparedCase(public, private, full_png, screenshot_pngs, region_pngs)


def representation_audit(
    packet: Mapping[str, Any], full_png: bytes, screenshot_pngs: Sequence[bytes],
    region_pngs: Mapping[str, Sequence[bytes]], text_b: str,
) -> dict[str, Any]:
    if set(region_pngs) != set(REGIONS):
        raise RQ1Error("renderer crops do not cover M/R/L/G")
    if not full_png.startswith(b"\x89PNG") or any(not value.startswith(b"\x89PNG") for value in screenshot_pngs):
        raise RQ1Error("visual transport is not PNG")
    inventory = stable_hash(packet["facts"])
    if inventory != packet["fact_inventory_hash"]:
        raise RQ1Error("packet inventory hash drifted")
    arm_map = {
        "T": {region: "text" for region in REGIONS},
        "V": {region: "visual" for region in REGIONS},
        "S": {region: "pixel_text" for region in REGIONS},
        "LV": {region: "visual" if region == "L" else "text" for region in REGIONS},
        "MV": {region: "visual" if region == "M" else "text" for region in REGIONS},
        "TCV": {region: "visual" if region == "R" else "text" for region in REGIONS},
        "TPV": {region: "visual" if region == "G" else "text" for region in REGIONS},
    }
    return {
        "schema_version": "RQ1_1RepresentationEqualityV1",
        "fact_inventory_hash_by_arm": {arm: inventory for arm in arm_map},
        "encoding_by_arm": arm_map,
        "t_incident_fragment_sha256": hashlib.sha256(text_b.encode()).hexdigest(),
        "s_source_text_sha256": hashlib.sha256(text_b.encode()).hexdigest(),
        "s_equals_t_bytes": True,
        "crops_are_source_pixels": True,
        "visual_facts_repeated_in_mixed_text": False,
    }


def balanced_arm_order(arms: Sequence[str], opaque_id: str, experiment: str) -> tuple[str, ...]:
    values = tuple(arms)
    # A bounded smoke may intentionally assign no arm to a model/dataset cell.
    # Such a cell consumes zero calls and must be skipped, not sent through the
    # rotation arithmetic below.
    if not values:
        return ()
    digest = int(stable_hash(f"{experiment}:{opaque_id}:arm-order"), 16)
    shift = digest % len(values)
    ordered = values[shift:] + values[:shift]
    return tuple(reversed(ordered)) if (digest // len(values)) % 2 else ordered


def representation_parts(arm: str, prepared: PreparedCase) -> list[dict[str, Any]]:
    packet, regions = prepared.public["packet"], prepared.region_pngs
    if arm == "T":
        incident = [tagged_text_part(packet_text(packet), "evidence_header")]
    elif arm == "V":
        full = image_part(prepared.full_png)
        full["attention_region"] = "dashboard"
        full["attention_region_boxes"] = prepared.public["region_crop_audit"]["crop_boxes_px"]
        incident = [full]
    elif arm == "S":
        incident = []
        for page, value in enumerate(prepared.screenshot_pngs, 1):
            part = image_part(value); part.update(attention_region="pixel_text", attention_page=page)
            incident.append(part)
    else:
        visual_region = {"LV": "L", "MV": "M", "TCV": "R", "TPV": "G"}.get(arm)
        if visual_region is None:
            raise RQ1Error(f"unknown RQ1.1 representation arm {arm}")
        incident = []
        for page, value in enumerate(regions[visual_region], 1):
            part = image_part(value); part.update(attention_region=visual_region, attention_page=page)
            incident.append(part)
        incident.append(tagged_text_part(
            packet_text(packet, [region for region in REGIONS if region != visual_region]),
            "evidence_header",
        ))
    return [*incident, tagged_text_part(_common_shell(packet), "common")]


def direct_rca_prompt(packet: Mapping[str, Any]) -> str:
    return RCA_GUIDE + "\nOutput exactly one JSON object: " + canonical_json({
        "services": ["candidate-id", "candidate-id"], "reason": "brief evidence-grounded explanation", "confidence": "high|medium|low"
    })


def qa_prompt(question: Mapping[str, Any]) -> str:
    return QA_GUIDE + "\nQuestion:\n" + str(question["question"]) + "\nOutput schema: " + canonical_json({
        "steps": [{"region": region, "values": ["displayed-value"]} for region in question["region_path"]]
    })


def planner_prompt(packet: Mapping[str, Any], step: int, history: Sequence[Mapping[str, Any]]) -> str:
    return (
        RCA_GUIDE + "\n" + TOOL_GUIDE + f"\nThis is step {step} of exactly 3. "
        "Select one tool whose result best distinguishes the current leading hypothesis from an alternative.\n"
        "Prior trajectory: " + canonical_json(history) + "\nOutput one tool call JSON."
    )


def analysis_prompt(packet: Mapping[str, Any], step: int, history: Sequence[Mapping[str, Any]], observation: Mapping[str, Any]) -> str:
    return (
        RCA_GUIDE + f"\nThis is analysis stage for step {step} of exactly 3. "
        "Update a ranked list using the new tool result and prior evidence.\n"
        "Prior trajectory: " + canonical_json(history) + "\nTool observation: " + canonical_json(observation) +
        "\nOutput JSON with temporary_services, analysis, confidence."
    )


def multi_stage_analysis_parts(
    arm: str, prepared: PreparedCase, step: int,
    history: Sequence[Mapping[str, Any]], observation: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Replay one arm in the stateless post-tool analysis request."""

    packet = prepared.public["packet"]
    return [
        *representation_parts(arm, prepared),
        tagged_text_part(analysis_prompt(packet, step, history, observation), "task_history_tool"),
    ]


def rca_schema() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "RCAAnswer", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["services", "reason", "confidence"],
        "properties": {
            "services": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"type": "string"}},
            "reason": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
    }}}


def qa_schema(level: int) -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": f"L{level}Answer", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["steps"],
        "properties": {"steps": {"type": "array", "minItems": level, "maxItems": level, "items": {
            "type": "object", "additionalProperties": False, "required": ["region", "values"],
            "properties": {"region": {"type": "string", "enum": list(REGIONS)}, "values": {"type": "array", "items": {"type": "string"}}},
        }}},
    }}}


def planner_schema() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "ToolAction", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["tool", "arguments"],
        "properties": {
            "tool": {"type": "string", "enum": ["search_metrics", "search_traces", "search_logs", "search_topology"]},
            "arguments": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "entity_id": {"type": "string"}, "metric": {"type": "string"},
                    "operation": {"type": "string"}, "template_id": {"type": "string"},
                    "start_bin": {"type": "integer", "minimum": 0, "maximum": 63},
                    "end_bin": {"type": "integer", "minimum": 0, "maximum": 63},
                    "direction": {"type": "string", "enum": ["both", "upstream", "downstream"]},
                },
            },
        },
    }}}


def temporary_schema() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "TemporaryRanking", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["temporary_services", "analysis", "confidence"],
        "properties": {
            "temporary_services": {"type": "array", "minItems": 1, "maxItems": 5, "items": {"type": "string"}},
            "analysis": {"type": "string"}, "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        },
    }}}


def validate_diagnosis(payload: Mapping[str, Any], candidates: Sequence[str]) -> dict[str, Any]:
    services = payload.get("services")
    if not isinstance(services, list) or not 1 <= len(services) <= 5:
        raise RQ1Error("RCA response requires one to five services")
    normalized = list(dict.fromkeys(map(str, services)))
    if any(value not in candidates for value in normalized):
        raise RQ1Error("RCA response contains an unknown case-local ID")
    confidence = str(payload.get("confidence"))
    if confidence not in {"high", "medium", "low"}:
        raise RQ1Error("invalid RCA confidence")
    return {"services": normalized, "reason": str(payload.get("reason") or ""), "confidence": confidence}


def validate_temporary(payload: Mapping[str, Any], candidates: Sequence[str]) -> dict[str, Any]:
    values = payload.get("temporary_services")
    if not isinstance(values, list) or not values:
        raise RQ1Error("temporary ranking is missing")
    services = list(dict.fromkeys(map(str, values)))[:5]
    if any(value not in candidates for value in services):
        raise RQ1Error("temporary ranking contains an unknown ID")
    confidence = str(payload.get("confidence"))
    if confidence not in {"high", "medium", "low"}:
        raise RQ1Error("invalid temporary confidence")
    return {"temporary_services": services, "analysis": str(payload.get("analysis") or ""), "confidence": confidence}


def validate_qa(payload: Mapping[str, Any], question: Mapping[str, Any]) -> dict[str, Any]:
    steps = payload.get("steps")
    regions = list(question["region_path"])
    if not isinstance(steps, list) or len(steps) != len(regions):
        raise RQ1Error("QA response step count differs from reasoning level")
    output = []
    for expected, row in zip(regions, steps, strict=True):
        if not isinstance(row, Mapping) or str(row.get("region")) != expected:
            raise RQ1Error("QA response region order drifted")
        values = row.get("values")
        if not isinstance(values, list):
            raise RQ1Error("QA step values must be a list")
        output.append({"region": expected, "values": list(map(str, values))})
    return {"steps": output}


def score_qa(response: Mapping[str, Any], private_question: Mapping[str, Any]) -> dict[str, Any]:
    expected = [list(map(str, row)) for row in private_question["answer_steps"]]
    actual = [list(map(str, row["values"])) for row in response["steps"]]
    step = [float(left == right) for left, right in zip(actual, expected, strict=True)]
    prefix = []
    running = True
    for value in step:
        running = running and bool(value)
        prefix.append(float(running))
    return {
        "complete_chain_accuracy": float(all(step)),
        "step_accuracy": sum(step) / len(step),
        "correct_prefix_accuracy": sum(prefix) / len(prefix),
        "step_scores": step,
    }


def _bounded(rows: Sequence[Mapping[str, Any]], row_limit: int, char_limit: int) -> list[dict[str, Any]]:
    output = []
    size = 2
    for row in rows[:row_limit]:
        value = dict(row)
        encoded = canonical_json(value)
        if size + len(encoded) > char_limit:
            break
        output.append(value)
        size += len(encoded) + 1
    return output


def execute_tool(
    action: Mapping[str, Any], tool_index: Mapping[str, Any], config: Mapping[str, Any],
) -> dict[str, Any]:
    name = str(action.get("tool") or "")
    args = dict(action.get("arguments") or {})
    row_limit = int(config["external_methods"]["denum"]["tool_row_limit"])
    char_limit = int(config["external_methods"]["denum"]["tool_character_limit"])
    entity = str(args.get("entity_id") or "")
    start, end = int(args.get("start_bin", 0)), int(args.get("end_bin", 63))
    if start < 0 or end > 63 or start > end:
        return {"status": "invalid_arguments", "tool": name, "rows": []}
    if name == "search_metrics":
        rows = [dict(row) for row in tool_index["metrics"] if not entity or row["entity_id"] == entity]
        metric = str(args.get("metric") or "")
        if metric:
            rows = [row for row in rows if metric.casefold() in str(row["metric"]).casefold()]
        for row in rows:
            row["values"], row["missing_mask"] = row["values"][start:end + 1], row["missing_mask"][start:end + 1]
    elif name == "search_traces":
        rows = [dict(row) for row in tool_index["traces"] if not entity or row["entity_id"] == entity]
        operation = str(args.get("operation") or "")
        if operation:
            rows = [row for row in rows if operation.casefold() in str(row["operation"]).casefold()]
        for row in rows:
            for key in ("spans", "errors", "p95_ms"):
                row[key] = row[key][start:end + 1]
    elif name == "search_logs":
        rows = [dict(row) for row in tool_index["logs"]["entries"] if not entity or row["entity_id"] == entity]
        template_id = str(args.get("template_id") or "")
        if template_id:
            rows = [row for row in rows if row["template_id"] == template_id]
        rows = [row for row in rows if start <= int(row["relative_bin"]) <= end]
    elif name == "search_topology":
        direction = str(args.get("direction") or "both")
        if direction not in {"both", "upstream", "downstream"}:
            return {"status": "invalid_arguments", "tool": name, "rows": []}
        rows = [dict(row) for row in tool_index["topology"]]
        if entity and direction == "upstream":
            rows = [row for row in rows if row["callee"] == entity]
        elif entity and direction == "downstream":
            rows = [row for row in rows if row["caller"] == entity]
        elif entity:
            rows = [row for row in rows if entity in (row["caller"], row["callee"])]
    else:
        return {"status": "invalid_tool", "tool": name, "rows": []}
    bounded = _bounded(rows, row_limit, char_limit)
    return {
        "schema_version": "RQ1_1ToolObservationV1", "status": "ok",
        "tool": name, "arguments": args, "rows": bounded,
        "matched_rows": len(rows), "returned_rows": len(bounded),
    }

"""Label-blind narrowing for dense RQ1 log and trace time slices.

The processed corpus stores absolute clocks and, for traces, correlation IDs.
Those fields are useful while joining parent and child spans but must never
enter a model-visible artifact.  This module is the one-way boundary: it accepts
telemetry-only frames and emits immutable, relative-time aggregate records.

Callers are responsible for narrowing a labelled ``DataCase`` to telemetry
before calling this module.  In particular, no case ID, dataset name, label,
fault type, injection timestamp, or source path is accepted by the public data
classes below.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
from vlmrca.render.onset import pod_to_service, service_level_projection

from .contracts import ContractError, assert_label_blind, stable_hash

DENSE_SLICE_SCHEMA = "DenseTelemetryTimeSlicesV2"
DEFAULT_TIME_BINS = 64

_TEMPLATE_DYNAMIC_RE = re.compile(
    r"(?:\b[0-9a-f]{8,}\b|\b\d{1,4}(?:[-/:.]\d{1,4})+\b|\b\d+(?:\.\d+)?\b)",
    re.IGNORECASE,
)
_TRACE_COLUMN_ALIASES = {
    "timestamp": ("timestamp_seconds", "timestamp", "startTimeMillis", "startTime"),
    "trace_id": ("trace_id", "traceID"),
    "span_id": ("span_id", "spanID"),
    "parent_span_id": ("parent_span_id", "parentSpanID", "parent_span"),
    "service_name": ("service_name", "serviceName", "entity_canonical", "cmdb_id"),
    "duration_ms": ("duration_ms",),
    "status_code": ("status_code", "statusCode", "attr.status_code"),
}


def _finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _round(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def _normalize_template(message: Any) -> str:
    normalized = " ".join(str(message or "").strip().lower().split())
    return _TEMPLATE_DYNAMIC_RE.sub("<v>", normalized)


def _template_id(template: str) -> str:
    """Return a stable ID for a label-blind, dynamic-value-normalized template."""

    return "LT-" + hashlib.sha256(template.encode("utf-8")).hexdigest()[:12].upper()


def _status_is_error(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if text in {"", "0", "0.0", "ok", "unset", "none", "nan", "success"}:
        return False
    number = _finite_float(value)
    return bool(number is not None and number >= 400) or any(
        marker in text for marker in ("error", "fail", "fatal", "panic")
    )


def _log_is_error(level: Any, message: Any) -> bool:
    text = f"{level or ''} {message or ''}".lower()
    return any(marker in text for marker in ("error", "fatal", "panic", "exception"))


def _resolve_entity(raw: Any, candidates: set[str]) -> str | None:
    value = str(raw or "").strip()
    if not value:
        return None
    if value in candidates:
        return value
    projected = pod_to_service(value)
    return projected if projected in candidates else None


def _bin_index(relative_s: float, duration_s: float, bin_count: int) -> int | None:
    if relative_s < 0 or relative_s > duration_s:
        return None
    if relative_s == duration_s:
        return bin_count - 1
    width = duration_s / bin_count
    return min(bin_count - 1, max(0, int(relative_s / width)))


@dataclass(frozen=True)
class DenseLogBin:
    service: str
    relative_bin: int
    bin_center_rel_s: float
    event_count: int
    error_count: int
    dominant_template_id: str | None
    dominant_template: str | None
    dominant_template_count: int


@dataclass(frozen=True)
class DenseTraceServiceBin:
    service: str
    relative_bin: int
    bin_center_rel_s: float
    span_count: int
    error_count: int
    latency_p95_ms: float | None


@dataclass(frozen=True)
class DenseTraceEdgeBin:
    caller: str
    callee: str
    relative_bin: int
    bin_center_rel_s: float
    span_count: int
    error_count: int
    latency_p95_ms: float | None


@dataclass(frozen=True)
class DenseTelemetryTimeSlices:
    """The only dense-timeline object accepted by the V2 evidence compiler."""

    opaque_incident_id: str
    duration_rel_s: float
    bin_count: int
    candidates: tuple[str, ...]
    directed_call_edges: tuple[tuple[str, str], ...]
    log_bins: tuple[DenseLogBin, ...]
    trace_service_bins: tuple[DenseTraceServiceBin, ...]
    trace_edge_bins: tuple[DenseTraceEdgeBin, ...]
    audit: Mapping[str, Any]
    schema_version: str = DENSE_SLICE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema_version != DENSE_SLICE_SCHEMA:
            raise ContractError(
                f"unsupported dense slice schema {self.schema_version!r}"
            )
        if (
            self.bin_count <= 0
            or not math.isfinite(self.duration_rel_s)
            or self.duration_rel_s <= 0
        ):
            raise ContractError(
                "dense slice requires a positive finite relative duration"
            )
        if len(self.candidates) != len(set(self.candidates)) or not self.candidates:
            raise ContractError("dense slice candidates must be non-empty and unique")
        candidate_set = set(self.candidates)
        for edge in self.directed_call_edges:
            if len(edge) != 2 or edge[0] == edge[1] or not set(edge) <= candidate_set:
                raise ContractError(f"invalid dense-slice edge {edge!r}")
        expected_log = len(self.candidates) * self.bin_count
        expected_trace = len(self.candidates) * self.bin_count
        expected_edge = len(self.directed_call_edges) * self.bin_count
        if len(self.log_bins) != expected_log:
            raise ContractError(
                f"log timeline is not dense: {len(self.log_bins)} != {expected_log}"
            )
        if len(self.trace_service_bins) != expected_trace:
            raise ContractError(
                f"trace service timeline is not dense: {len(self.trace_service_bins)} != {expected_trace}"
            )
        if len(self.trace_edge_bins) != expected_edge:
            raise ContractError(
                f"trace edge timeline is not dense: {len(self.trace_edge_bins)} != {expected_edge}"
            )
        expected_service_cells = {
            (service, index)
            for service in self.candidates
            for index in range(self.bin_count)
        }
        if {
            (row.service, row.relative_bin) for row in self.log_bins
        } != expected_service_cells:
            raise ContractError(
                "log timeline cells differ from candidate × relative-bin grid"
            )
        if {
            (row.service, row.relative_bin) for row in self.trace_service_bins
        } != expected_service_cells:
            raise ContractError(
                "trace timeline cells differ from candidate × relative-bin grid"
            )
        expected_edge_cells = {
            (caller, callee, index)
            for caller, callee in self.directed_call_edges
            for index in range(self.bin_count)
        }
        if {
            (row.caller, row.callee, row.relative_bin) for row in self.trace_edge_bins
        } != expected_edge_cells:
            raise ContractError(
                "trace-edge timeline cells differ from edge × relative-bin grid"
            )
        for row in (*self.log_bins, *self.trace_service_bins, *self.trace_edge_bins):
            if not 0 <= row.relative_bin < self.bin_count:
                raise ContractError("dense slice contains an out-of-range relative bin")
            if not 0 <= row.bin_center_rel_s <= self.duration_rel_s:
                raise ContractError(
                    "dense slice contains an out-of-range relative time"
                )
        for row in self.log_bins:
            if (
                row.event_count < 0
                or not 0 <= row.error_count <= row.event_count
                or not 0 <= row.dominant_template_count <= row.event_count
            ):
                raise ContractError("dense log timeline contains invalid counts")
        for row in (*self.trace_service_bins, *self.trace_edge_bins):
            if row.span_count < 0 or not 0 <= row.error_count <= row.span_count:
                raise ContractError("dense trace timeline contains invalid counts")
            if row.latency_p95_ms is not None and row.latency_p95_ms < 0:
                raise ContractError("dense trace timeline contains negative latency")
        assert_label_blind(self.public_dict(), context="dense telemetry slice")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "opaque_incident_id": self.opaque_incident_id,
            "duration_rel_s": self.duration_rel_s,
            "bin_count": self.bin_count,
            "candidates": list(self.candidates),
            "directed_call_edges": [
                {"caller": caller, "callee": callee}
                for caller, callee in self.directed_call_edges
            ],
            "log_bins": [row.__dict__ for row in self.log_bins],
            "trace_service_bins": [row.__dict__ for row in self.trace_service_bins],
            "trace_edge_bins": [row.__dict__ for row in self.trace_edge_bins],
            "audit": dict(self.audit),
        }

    @property
    def slice_hash(self) -> str:
        return stable_hash(self.public_dict())

    @property
    def content_hash(self) -> str:
        """Identity-free hash used for label-blind deterministic selection."""

        payload = self.public_dict()
        payload.pop("opaque_incident_id", None)
        return stable_hash(payload)


def narrow_trace_link_frame(raw: pd.DataFrame) -> pd.DataFrame:
    """Whitelist raw processed trace columns needed for parent-child joining.

    The returned frame has no source paths, raw dataset fields, anomaly flags,
    or labels.  Its absolute clock and correlation IDs are intermediate-only;
    ``build_dense_time_slices`` removes both before returning a public slice.
    """

    selected: dict[str, pd.Series] = {}
    for target, aliases in _TRACE_COLUMN_ALIASES.items():
        source = next((name for name in aliases if name in raw.columns), None)
        selected[target] = (
            raw[source].copy()
            if source is not None
            else pd.Series(None, index=raw.index)
        )
    out = pd.DataFrame(selected)
    out["timestamp"] = pd.to_numeric(out["timestamp"], errors="coerce")
    # Only fallbacks are potentially non-second clocks. Canonical processed
    # frames always provide timestamp_seconds, but normalize defensively.
    finite = out["timestamp"].dropna().abs()
    if len(finite):
        magnitude = float(finite.median())
        if magnitude > 1e17:
            out["timestamp"] /= 1e9
        elif magnitude > 1e14:
            out["timestamp"] /= 1e6
        elif magnitude > 1e11:
            out["timestamp"] /= 1e3
    out["duration_ms"] = pd.to_numeric(out["duration_ms"], errors="coerce")
    for column in (
        "trace_id",
        "span_id",
        "parent_span_id",
        "service_name",
        "status_code",
    ):
        out[column] = out[column].fillna("").astype(str)
    return out.dropna(subset=["timestamp"]).reset_index(drop=True)


def read_narrow_trace_parquet(path: Path) -> pd.DataFrame:
    """Read only whitelisted trace-link columns from a processed parquet file."""

    import pyarrow.parquet as pq

    resolved = Path(path).resolve()
    available = set(pq.read_schema(resolved).names)
    selected = sorted(
        {
            source
            for aliases in _TRACE_COLUMN_ALIASES.values()
            if (source := next((name for name in aliases if name in available), None))
            is not None
        }
    )
    return narrow_trace_link_frame(pd.read_parquet(resolved, columns=selected))


def build_dense_time_slices(
    *,
    opaque_incident_id: str,
    candidates: Sequence[str],
    observation_start_s: float,
    observation_end_s: float,
    logs_df: pd.DataFrame,
    trace_link_df: pd.DataFrame,
    graph: nx.DiGraph,
    bin_count: int = DEFAULT_TIME_BINS,
) -> DenseTelemetryTimeSlices:
    """Narrow telemetry into complete relative-time log/trace matrices.

    Selection and aggregation use no incident label.  Every candidate and every
    observed topology edge receives every time bin, including explicit zeros.
    """

    start = _finite_float(observation_start_s)
    end = _finite_float(observation_end_s)
    if start is None or end is None or end <= start:
        raise ContractError(
            "dense timeline requires a finite increasing observation range"
        )
    if bin_count <= 0:
        raise ContractError("dense timeline bin_count must be positive")
    ordered_candidates = tuple(
        sorted({str(value) for value in candidates if str(value)})
    )
    candidate_set = set(ordered_candidates)
    duration = end - start
    width = duration / bin_count
    centers = tuple(_round((index + 0.5) * width) for index in range(bin_count))

    projected = service_level_projection(graph, None)
    edges = tuple(
        sorted(
            {
                (caller, callee)
                for raw_caller, raw_callee in projected.edges()
                if (caller := _resolve_entity(raw_caller, candidate_set)) is not None
                and (callee := _resolve_entity(raw_callee, candidate_set)) is not None
                and caller != callee
            }
        )
    )

    log_counts: Counter[tuple[str, int]] = Counter()
    log_errors: Counter[tuple[str, int]] = Counter()
    log_templates: dict[tuple[str, int], Counter[str]] = defaultdict(Counter)
    dropped_logs = 0
    if logs_df is not None and not logs_df.empty:
        required = {"timestamp", "container_name", "message"}
        if not required <= set(logs_df.columns):
            raise ContractError(
                f"narrow log frame lacks columns {sorted(required - set(logs_df.columns))}"
            )
        for row in logs_df.itertuples(index=False):
            service = _resolve_entity(getattr(row, "container_name", ""), candidate_set)
            timestamp = _finite_float(getattr(row, "timestamp", None))
            if service is None or timestamp is None:
                dropped_logs += 1
                continue
            relative = timestamp - start
            index = _bin_index(relative, duration, bin_count)
            if index is None:
                dropped_logs += 1
                continue
            key = (service, index)
            message = getattr(row, "message", "")
            level = getattr(row, "level", "")
            log_counts[key] += 1
            log_errors[key] += int(_log_is_error(level, message))
            log_templates[key][_normalize_template(message)] += 1

    trace_service_count: Counter[tuple[str, int]] = Counter()
    trace_service_errors: Counter[tuple[str, int]] = Counter()
    trace_service_latency: dict[tuple[str, int], list[float]] = defaultdict(list)
    trace_edge_count: Counter[tuple[str, str, int]] = Counter()
    trace_edge_errors: Counter[tuple[str, str, int]] = Counter()
    trace_edge_latency: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    dropped_traces = 0
    unmatched_parents = 0
    observed_edges: set[tuple[str, str]] = set()
    if trace_link_df is not None and not trace_link_df.empty:
        required = {
            "timestamp",
            "trace_id",
            "span_id",
            "parent_span_id",
            "service_name",
            "duration_ms",
            "status_code",
        }
        if not required <= set(trace_link_df.columns):
            raise ContractError(
                f"narrow trace-link frame lacks columns {sorted(required - set(trace_link_df.columns))}"
            )
        frame = trace_link_df.sort_values(
            ["trace_id", "timestamp", "span_id"], kind="mergesort"
        ).reset_index(drop=True)
        span_service: dict[tuple[str, str], str] = {}
        for row in frame.itertuples(index=False):
            service = _resolve_entity(row.service_name, candidate_set)
            if service is not None and row.trace_id and row.span_id:
                span_service.setdefault((row.trace_id, row.span_id), service)
        for row in frame.itertuples(index=False):
            service = _resolve_entity(row.service_name, candidate_set)
            timestamp = _finite_float(row.timestamp)
            if service is None or timestamp is None:
                dropped_traces += 1
                continue
            index = _bin_index(timestamp - start, duration, bin_count)
            if index is None:
                dropped_traces += 1
                continue
            latency = _finite_float(row.duration_ms)
            error = int(_status_is_error(row.status_code))
            service_key = (service, index)
            trace_service_count[service_key] += 1
            trace_service_errors[service_key] += error
            if latency is not None:
                trace_service_latency[service_key].append(latency)

            if not row.trace_id or not row.parent_span_id:
                continue
            caller = span_service.get((row.trace_id, row.parent_span_id))
            if caller is None:
                unmatched_parents += 1
                continue
            if caller == service:
                continue
            observed_edges.add((caller, service))
            edge_key = (caller, service, index)
            trace_edge_count[edge_key] += 1
            trace_edge_errors[edge_key] += error
            if latency is not None:
                trace_edge_latency[edge_key].append(latency)

    # Parent-child trace relations are themselves observed topology.  Include
    # them alongside the static graph so their time slices are never discarded.
    edges = tuple(sorted(set(edges) | observed_edges))

    log_bins: list[DenseLogBin] = []
    trace_service_bins: list[DenseTraceServiceBin] = []
    for service in ordered_candidates:
        for index, center in enumerate(centers):
            log_key = (service, index)
            templates = log_templates.get(log_key, Counter())
            dominant_template = min(
                templates,
                key=lambda value: (-templates[value], value),
                default=None,
            )
            log_bins.append(
                DenseLogBin(
                    service=service,
                    relative_bin=index,
                    bin_center_rel_s=float(center),
                    event_count=int(log_counts[log_key]),
                    error_count=int(log_errors[log_key]),
                    dominant_template_id=_template_id(dominant_template)
                    if dominant_template is not None
                    else None,
                    dominant_template=dominant_template,
                    dominant_template_count=int(templates[dominant_template])
                    if dominant_template is not None
                    else 0,
                )
            )
            trace_key = (service, index)
            latencies = trace_service_latency.get(trace_key, [])
            trace_service_bins.append(
                DenseTraceServiceBin(
                    service=service,
                    relative_bin=index,
                    bin_center_rel_s=float(center),
                    span_count=int(trace_service_count[trace_key]),
                    error_count=int(trace_service_errors[trace_key]),
                    latency_p95_ms=_round(float(np.percentile(latencies, 95)))
                    if latencies
                    else None,
                )
            )

    trace_edge_bins: list[DenseTraceEdgeBin] = []
    for caller, callee in edges:
        for index, center in enumerate(centers):
            key = (caller, callee, index)
            latencies = trace_edge_latency.get(key, [])
            trace_edge_bins.append(
                DenseTraceEdgeBin(
                    caller=caller,
                    callee=callee,
                    relative_bin=index,
                    bin_center_rel_s=float(center),
                    span_count=int(trace_edge_count[key]),
                    error_count=int(trace_edge_errors[key]),
                    latency_p95_ms=_round(float(np.percentile(latencies, 95)))
                    if latencies
                    else None,
                )
            )

    audit = {
        "selection": "all_candidates_all_bins_label_blind",
        "time_semantics": "relative_seconds_from_observation_start_t0",
        "template_semantics": "opaque_hash_of_dynamic_value_normalized_message",
        "edge_semantics": "parent_span_service_calls_child_span_service",
        "dropped_log_records": dropped_logs,
        "dropped_trace_records": dropped_traces,
        "unmatched_parent_spans": unmatched_parents,
    }
    return DenseTelemetryTimeSlices(
        opaque_incident_id=opaque_incident_id,
        duration_rel_s=_round(duration) or duration,
        bin_count=bin_count,
        candidates=ordered_candidates,
        directed_call_edges=edges,
        log_bins=tuple(log_bins),
        trace_service_bins=tuple(trace_service_bins),
        trace_edge_bins=tuple(trace_edge_bins),
        audit=audit,
    )


def synthetic_dense_time_slices(
    *,
    opaque_incident_id: str = "INC-0123456789AB",
    candidates: Sequence[str] = ("svc-a", "svc-b", "svc-c", "svc-d"),
) -> DenseTelemetryTimeSlices:
    """Small deterministic fixture that exercises log and trace-edge timelines."""

    logs = pd.DataFrame(
        [
            {
                "timestamp": 1010.0,
                "container_name": "svc-a",
                "message": "request ok 17",
                "level": "info",
            },
            {
                "timestamp": 1025.0,
                "container_name": "svc-a",
                "message": "request failed 23",
                "level": "error",
            },
            {
                "timestamp": 1045.0,
                "container_name": "svc-c",
                "message": "retry 99",
                "level": "warn",
            },
        ]
    )
    traces = pd.DataFrame(
        [
            {
                "timestamp": 1020.0,
                "trace_id": "trace-a",
                "span_id": "span-a",
                "parent_span_id": "",
                "service_name": "svc-a",
                "duration_ms": 5.0,
                "status_code": "0",
            },
            {
                "timestamp": 1021.0,
                "trace_id": "trace-a",
                "span_id": "span-b",
                "parent_span_id": "span-a",
                "service_name": "svc-b",
                "duration_ms": 15.0,
                "status_code": "0",
            },
            {
                "timestamp": 1022.0,
                "trace_id": "trace-a",
                "span_id": "span-c",
                "parent_span_id": "span-b",
                "service_name": "svc-c",
                "duration_ms": 25.0,
                "status_code": "error",
            },
        ]
    )
    graph = nx.DiGraph([("svc-a", "svc-b"), ("svc-b", "svc-c"), ("svc-a", "svc-d")])
    return build_dense_time_slices(
        opaque_incident_id=opaque_incident_id,
        candidates=candidates,
        observation_start_s=1000.0,
        observation_end_s=1080.0,
        logs_df=logs,
        trace_link_df=traces,
        graph=graph,
        bin_count=8,
    )

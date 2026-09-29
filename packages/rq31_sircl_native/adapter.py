"""Minimal public-schema adapter that actually calls the selected SIRCL code."""
from __future__ import annotations

from typing import Any

import pandas as pd

from .original.src.data.base import DataCase
from .original.src.telemetry_analyzers.extractors.log_regex_simplerca import (
    score_logs_simplerca,
)
from .original.src.telemetry_analyzers.extractors.trace_spans import (
    build_tracediag_span_features,
)
from .original.src.telemetry_analyzers.metrics_variants import MetricsVariantZ

_PUBLIC_EPOCH_OFFSET_S = 1_700_000_000.0


def build_public_case(native: Any, *, duration_scale: float = 1.0) -> DataCase:
    """Narrow RQ2.1 public telemetry to the original label-free DataCase API."""
    metrics = native.metrics_df.copy()
    traces = native.traces_df.copy()
    logs = native.logs_df.copy()
    if "timestamp" in metrics:
        metrics["timestamp"] = (
            pd.to_numeric(metrics["timestamp"], errors="coerce") + _PUBLIC_EPOCH_OFFSET_S
        )
    if "_rq21_time_s" in traces:
        traces["timestamp"] = (
            pd.to_numeric(traces["_rq21_time_s"], errors="coerce") + _PUBLIC_EPOCH_OFFSET_S
        )
    if "duration_ms" in traces:
        traces["duration_ms"] = (
            pd.to_numeric(traces["duration_ms"], errors="coerce") * float(duration_scale)
        )
    if "_rq21_time_s" in logs:
        logs["timestamp"] = (
            pd.to_numeric(logs["_rq21_time_s"], errors="coerce") + _PUBLIC_EPOCH_OFFSET_S
        )
    return DataCase(
        metrics_df=metrics,
        traces_df=traces,
        logs_df=logs,
        services=sorted(map(str, native.services)),
        timestamp=float(native.analysis_start_s) + _PUBLIC_EPOCH_OFFSET_S,
    )


def run_selected_native(native: Any) -> dict[str, str]:
    """Execute the hash-copied MET-Z/TRC-L/LOG-R implementations unchanged."""
    case = build_public_case(native)
    return {
        "MET-Z": MetricsVariantZ().get_metrics_context(case),
        "TRC-L": build_tracediag_span_features(case),
        "LOG-R": score_logs_simplerca(case),
    }


def run_selected_adapted(native: Any, *, duration_scale: float) -> dict[str, str]:
    """Call the same originals after the registered public duration projection."""
    case = build_public_case(native, duration_scale=duration_scale)
    return {
        "MET-Z": MetricsVariantZ().get_metrics_context(case),
        "TRC-L": build_tracediag_span_features(case),
        "LOG-R": score_logs_simplerca(case),
    }

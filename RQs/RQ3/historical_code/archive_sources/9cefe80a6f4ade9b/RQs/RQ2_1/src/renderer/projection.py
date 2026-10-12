"""RQ2.1 public statistics: byte-inherited computation, selection independent."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .panels import _fmt, _split_by_window, _unit_for_span


def project_metric(series, metrics_df, analysis_window, *, time_bins=64):
    ts = pd.to_numeric(metrics_df["timestamp"], errors="coerce").astype("float64").to_numpy()
    vals = pd.to_numeric(metrics_df[series.column], errors="coerce").astype("float64").to_numpy()
    # Selected SIRCL MET-Z statistics, computed before visual binning.
    met_z: dict[str, Any] = {
        "regular_mean": None, "regular_std_dev": None,
        "current_mean": None, "current_std_dev": None,
        "deviation_sigma": None, "fluctuating_3sigma": False,
    }
    if analysis_window is not None:
        split, end = map(float, analysis_window)
        regular = vals[(ts < split) & np.isfinite(ts) & np.isfinite(vals)]
        current = vals[(ts >= split) & (ts <= end) & np.isfinite(ts) & np.isfinite(vals)]
        if len(regular) >= 2 and len(current) >= 1:
            mean0, std0 = float(np.mean(regular)), float(np.std(regular))
            mean1, std1 = float(np.mean(current)), float(np.std(current))
            deviation = abs(mean1 - mean0) / std0 if std0 > 0 else None
            met_z = {
                "regular_mean": mean0, "regular_std_dev": std0,
                "current_mean": mean1, "current_std_dev": std1,
                "deviation_sigma": deviation,
                "fluctuating_3sigma": bool(deviation is not None and deviation > 3.0),
            }

    # RQ0 serializes the same fixed-width bins represented by image pixels.
    # Median aggregation is deterministic, robust to duplicate timestamps, and
    # keeps missingness explicit instead of interpolating it away.
    bin_values = None
    bin_counts = None
    bin_centers_s = None
    if time_bins > 0 and len(ts):
        finite_t = ts[np.isfinite(ts)]
        if finite_t.size:
            lo_t, hi_t = float(finite_t.min()), float(finite_t.max())
            if hi_t <= lo_t:
                hi_t = lo_t + 1.0
            edges = np.linspace(lo_t, hi_t, time_bins + 1)
            idx = np.clip(np.searchsorted(edges, ts, side="right") - 1, 0, time_bins - 1)
            bvals = np.full(time_bins, np.nan, dtype="float64")
            bcounts = np.zeros(time_bins, dtype="int64")
            for bi in range(time_bins):
                keep = (idx == bi) & np.isfinite(vals) & np.isfinite(ts)
                bcounts[bi] = int(keep.sum())
                if bcounts[bi]:
                    bvals[bi] = float(np.median(vals[keep]))
            ts = (edges[:-1] + edges[1:]) / 2
            vals = bvals
            bin_values = bvals
            bin_counts = bcounts
            bin_centers_s = (ts - lo_t) / _unit_for_span(hi_t - lo_t)


    return {
        "panel_id": "M0", "kind": "metric", "service": series.service,
        "metric": series.metric, "signed_z": round(series.signed_z, 3),
        "score": round(series.score, 3), "peak_value": series.peak_value,
        "baseline_mean": series.baseline_mean, "baseline_std": series.baseline_std,
        "sircl_met_z": {
            key: (_fmt(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else value)
            for key, value in met_z.items()
        },
        "time_bin_centers_rel_s": bin_centers_s.tolist() if bin_centers_s is not None else [],
        "values": bin_values.tolist() if bin_values is not None else [],
        "observed_counts": bin_counts.tolist() if bin_counts is not None else [],
    }

def project_traces(traces_df, fault_window, full_range, *, include_unranked=True):
    entries: list[dict[str, Any]] = []
    required = {"service_name", "span_id", "parent_span_id", "duration_ms"}
    if traces_df is not None and not traces_df.empty and required <= set(traces_df.columns):
        pre, during = _split_by_window(traces_df, fault_window, full_range)

        def aggregate(frame: pd.DataFrame) -> pd.DataFrame:
            keys = ["service_name", "operation_name"]
            if frame is None or frame.empty:
                return pd.DataFrame(columns=[*keys, "count", "exl_p95", "inl_p95"])
            work = frame.copy()
            if "operation_name" not in work:
                work["operation_name"] = "default"
            work["operation_name"] = work["operation_name"].fillna("default").astype(str)
            inclusive = pd.to_numeric(work["duration_ms"], errors="coerce").fillna(0.0)
            parent_sum = (
                pd.DataFrame({"parent": work["parent_span_id"].astype(str), "duration": inclusive})
                .groupby("parent")["duration"].sum()
            )
            child = work["span_id"].astype(str).map(parent_sum).fillna(0.0)
            work["_inl"], work["_exl"] = inclusive, (inclusive - child).clip(lower=0.0)
            return work.groupby(keys).agg(
                count=("_exl", "size"),
                exl_p95=("_exl", lambda value: float(np.percentile(value, 95))),
                inl_p95=("_inl", lambda value: float(np.percentile(value, 95))),
            ).reset_index()

        base, fault = aggregate(pre), aggregate(during)
        keys = ["service_name", "operation_name"]
        merged = fault.merge(base, on=keys, how="left", suffixes=("_fault", "_base")).fillna(0.0)
        if not merged.empty:
            count_base = merged["count_base"].astype(float)
            count_fault = merged["count_fault"].astype(float)
            exl_base = merged["exl_p95_base"].astype(float)
            exl_fault = merged["exl_p95_fault"].astype(float)
            merged["count_lfc"] = np.log2((count_fault + 1.0) / (count_base + 1.0))
            merged["latency_lfc"] = np.log2((exl_fault + 1.0) / (exl_base + 1.0))
            usable = (count_base > 0) & (exl_base > 0)
            merged["rank_score"] = np.where(
                usable,
                merged["count_lfc"].clip(lower=0.0) + merged["latency_lfc"].clip(lower=0.0),
                0.0,
            )
            if not include_unranked:
                merged = merged[merged["rank_score"] > 0]
            merged = merged.sort_values(
                ["rank_score", "service_name", "operation_name"], ascending=[False, True, True]
            )
            for _, row in merged.iterrows():
                entries.append({
                    "service": str(row["service_name"]),
                    "operation": str(row["operation_name"]),
                    "count_base": int(row["count_base"]),
                    "count_fault": int(row["count_fault"]),
                    "exl_p95_base_ms": round(float(row["exl_p95_base"]), 2),
                    "exl_p95_fault_ms": round(float(row["exl_p95_fault"]), 2),
                    "inl_p95_fault_ms": round(float(row["inl_p95_fault"]), 2),
                    "count_lfc": round(float(row["count_lfc"]), 2),
                    "latency_lfc": round(float(row["latency_lfc"]), 2),
                    "rank_score": round(float(row["rank_score"]), 2),
                })


    return entries

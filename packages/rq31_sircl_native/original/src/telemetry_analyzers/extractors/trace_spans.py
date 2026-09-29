"""
Per-(service, operation) span anomaly features — used by T3 (TraceVariantL).

Latency features:
    InL  = inclusive latency (span's own duration, including children)
    ExL  = exclusive latency (InL − sum of child InLs); the time *not* spent
           waiting on downstream calls

Per operation, anomaly scores use bounded log₂-fold-change of count and
exclusive-latency p95 between the baseline and fault windows:
    count_lfc   = log₂((count_fault   + 1) / (count_base   + 1))
    latency_lfc = log₂((exl_p95_fault + 1) / (exl_p95_base + 1))
    rank_score  = max(0, count_lfc) + max(0, latency_lfc)

The +1 smoothing keeps base=0 cases bounded; the additive form lets either
signal surface a single-modality anomaly. rank_score is only computed for
operations with count_base > 0; operations new in the fault window
(count_base = 0) get rank_score = 0 and are excluded from the candidate list.

The output also surfaces paired raw `count_base`/`count_fault` and
`exl_p95_base`/`exl_p95_fault` so the model can sanity-check the LFC values.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

from ...data.base import DataCase
from ._timestamps import trace_time_seconds

def _split_by_onset(case: DataCase) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = case.traces_df
    if df.empty:
        return df.iloc[0:0], df
    ts_seconds = trace_time_seconds(df, anchor=case.timestamp)
    if ts_seconds.notna().sum() == 0:
        return df.iloc[0:0], df.iloc[0:0]
    t_a = float(case.timestamp)
    return df.loc[ts_seconds < t_a].copy(), df.loc[ts_seconds >= t_a].copy()

def _compute_exl(spans: pd.DataFrame) -> pd.Series:
    """ExL[span] = InL[span] − Σ InL[child] (formula)."""
    if spans.empty or "span_id" not in spans.columns or "parent_span_id" not in spans.columns:
        return pd.Series([], dtype=float)
    inl = pd.to_numeric(spans["duration_ms"], errors="coerce").fillna(0.0)
    spans = spans.assign(_inl=inl.values)
    child_sum = (
        spans.groupby("parent_span_id")["_inl"]
             .sum()
             .reindex(spans["span_id"], fill_value=0.0)
             .reset_index(drop=True)
    )
    exl = (spans["_inl"].values - child_sum.values).clip(min=0.0)
    return pd.Series(exl, index=spans.index)

def _agg_per_op(
    spans: pd.DataFrame, exl: pd.Series, key_cols: List[str]
) -> pd.DataFrame:
    if spans.empty:
        return pd.DataFrame(columns=key_cols + ["count", "exl_p95", "inl_p95"])
    work = spans[key_cols].copy()
    work["_exl"] = exl.values
    work["_inl"] = pd.to_numeric(spans["duration_ms"], errors="coerce").fillna(0.0).values
    out = (
        work.groupby(key_cols)
            .agg(count=("_exl", "size"),
                 exl_p95=("_exl", lambda x: float(np.percentile(x, 95)) if len(x) else 0.0),
                 inl_p95=("_inl", lambda x: float(np.percentile(x, 95)) if len(x) else 0.0))
            .reset_index()
    )
    return out

def build_tracediag_span_features(case: DataCase) -> str:
    df = case.traces_df
    if df.empty:
        return "No traces available."

    needed = {"span_id", "parent_span_id", "service_name", "duration_ms"}
    if not needed.issubset(df.columns):
        return "Trace data lacks required columns (span_id, parent_span_id, service_name, duration_ms)."

    if "operation_name" not in df.columns:
        df = df.assign(operation_name="default")

    baseline, fault = _split_by_onset(case)
    if fault.empty:
        return "No spans in the fault window."

    f_exl = _compute_exl(fault)
    b_exl = _compute_exl(baseline) if not baseline.empty else pd.Series([], dtype=float)

    keys = ["service_name", "operation_name"]
    f_agg = _agg_per_op(fault, f_exl, keys)
    b_agg = _agg_per_op(baseline, b_exl, keys) if not baseline.empty else pd.DataFrame(
        columns=keys + ["count", "exl_p95", "inl_p95"]
    )

    merged = f_agg.merge(b_agg, on=keys, how="left", suffixes=("_fault", "_base"))
    merged["count_base"] = merged["count_base"].fillna(0)
    merged["exl_p95_base"] = merged["exl_p95_base"].fillna(0.0)
    merged["inl_p95_base"] = merged["inl_p95_base"].fillna(0.0)

    # Bounded log₂-fold-change with +1 smoothing (no infinities for base=0):
    # doubling → +1, halving → −1, no-change → 0.
    f_count = merged["count_fault"].astype(float)
    b_count = merged["count_base"].astype(float)
    f_lat = merged["exl_p95_fault"].astype(float)
    b_lat = merged["exl_p95_base"].astype(float)
    merged["count_lfc"] = np.log2((f_count + 1.0) / (b_count + 1.0))
    merged["latency_lfc"] = np.log2((f_lat + 1.0) / (b_lat + 1.0))

    # rank_score is computed ONLY for operations seen in the baseline window.
    # Operations new in the fault window (count_base=0) carry the LFC display
    # values for transparency but get rank_score=0 — they're often single-span
    # noise (e.g., a stray health-check call in a long-tail bucket) and would
    # dominate the ranking purely on the magnitude of `log₂(big/1)`.
    has_baseline = (b_count > 0) & (b_lat > 0)
    raw_score = (
        merged["count_lfc"].clip(lower=0.0)
        + merged["latency_lfc"].clip(lower=0.0)
    )
    merged["rank_score"] = np.where(has_baseline, raw_score, 0.0)

    candidates = merged[merged["rank_score"] > 0]
    if candidates.empty:
        return "No anomalous spans with usable baseline (rank_score = 0)."
    candidates = candidates.sort_values("rank_score", ascending=False).head(40)

    parts: List[str] = [
        "Per-(service, operation) span features: "
        "ExL_p95 (exclusive latency, own time excluding children), "
        "InL_p95 (inclusive latency, own + children), "
        "count_lfc = log₂((count_fault + 1) / (count_base + 1)), "
        "latency_lfc = log₂((exl_p95_fault + 1) / (exl_p95_base + 1)), "
        "rank_score = max(0, count_lfc) + max(0, latency_lfc). "
        "Bounded; doubling = +1, halving = −1; rows with both signals positive "
        "are most anomalous.",
        "",
        "service,operation,count_base,count_fault,"
        "exl_p95_base,exl_p95_fault,inl_p95_fault,"
        "count_lfc,latency_lfc,rank_score",
    ]
    for _, row in candidates.iterrows():
        op_short = str(row["operation_name"]).replace(",", " ")[:60]
        parts.append(
            f"{row['service_name']},{op_short},"
            f"{int(row['count_base'])},{int(row['count_fault'])},"
            f"{row['exl_p95_base']:.1f},{row['exl_p95_fault']:.1f},{row['inl_p95_fault']:.1f},"
            f"{row['count_lfc']:.2f},{row['latency_lfc']:.2f},{row['rank_score']:.2f}"
        )

    return "\n".join(parts)

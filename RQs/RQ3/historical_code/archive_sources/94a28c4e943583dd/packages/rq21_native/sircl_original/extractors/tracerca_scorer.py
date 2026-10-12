"""
Per-operation Support-Confidence-Jaccard — used by T4 (TraceVariantTR).

Reference (read-only, internal only):
  src/baselines/original_implementations/non_llm/rcaeval_e2e/tracerca.py:45-98

Algorithm:
  1. Build operation label = service_name + "_" + operation_name.
  2. Split spans by case.timestamp → baseline_df, fault_df (in epoch seconds).
  3. For each operation, compute baseline mean & std of duration_ms.
  4. For each fault span: abnormal = duration_ms >= (mean + 3 × std).
  5. For each operation in fault window:
       support    = abnormal_count(op) / total_abnormal_count
       confidence = abnormal_count(op) / total_count(op)
       ji         = 2·s·c / (s + c)
  6. Rank operations by ji, drop NaN.

Treats anomaly as a *presence pattern* across spans rather than a magnitude —
orthogonal to per-span ExL/InL latency-magnitude features.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

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


def _operation_slo(spans: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
    """Per-operation (mean, std) of duration_ms over the baseline window."""
    out: Dict[str, Tuple[float, float]] = {}
    if spans.empty:
        return out
    for op, grp in spans.groupby("operation"):
        d = pd.to_numeric(grp["duration_ms"], errors="coerce").dropna()
        if d.empty:
            continue
        out[op] = (float(d.mean()), float(d.std(ddof=0)))
    return out


def score_operations_jaccard(case: DataCase) -> str:
    df = case.traces_df
    if df.empty:
        return "No traces available."
    if "service_name" not in df.columns or "duration_ms" not in df.columns:
        return "Trace data lacks service_name or duration_ms."

    if "operation_name" not in df.columns:
        df = df.assign(operation_name="default")

    df = df.copy()
    df["operation"] = df["service_name"].astype(str) + "_" + df["operation_name"].astype(str)

    baseline, fault = _split_by_onset(case)
    if fault.empty:
        return "No spans in the fault window."
    fault = fault.copy()
    fault["operation"] = fault["service_name"].astype(str) + "_" + fault["operation_name"].astype(str)

    if baseline.empty:
        return "No baseline spans (cannot compute SLO; TraceRCA degenerate)."
    baseline = baseline.copy()
    baseline["operation"] = baseline["service_name"].astype(str) + "_" + baseline["operation_name"].astype(str)

    slo = _operation_slo(baseline)
    if not slo:
        return "Baseline window had no spans for SLO computation."

    # Mark abnormal flag per fault span
    fault["mean"] = fault["operation"].map(lambda op: slo.get(op, (np.nan, np.nan))[0])
    fault["std"] = fault["operation"].map(lambda op: slo.get(op, (np.nan, np.nan))[1])
    fault_dur = pd.to_numeric(fault["duration_ms"], errors="coerce")
    fault["abnormal"] = fault_dur >= (fault["mean"] + 3.0 * fault["std"])
    fault["abnormal"] = fault["abnormal"].fillna(False).astype(int)

    total_abnormal = int(fault["abnormal"].sum())
    if total_abnormal == 0:
        return "No abnormal spans (all fault-window durations within μ+3σ of baseline)."

    rows: List[Dict[str, object]] = []
    for op, grp in fault.groupby("operation"):
        ab_n = int(grp["abnormal"].sum())
        if ab_n == 0:
            continue
        total_n = len(grp)
        support = ab_n / total_abnormal
        confidence = ab_n / total_n
        denom = support + confidence
        ji = (2.0 * support * confidence / denom) if denom > 0 else 0.0
        if np.isnan(ji):
            continue
        rows.append({
            "operation": op,
            "abnormal_n": ab_n,
            "total_n": total_n,
            "support": support,
            "confidence": confidence,
            "jaccard": ji,
        })

    if not rows:
        return "No operations with abnormal spans."
    rows.sort(key=lambda r: r["jaccard"], reverse=True)

    parts: List[str] = [
        "Per-operation 3σ-anomaly Jaccard index "
        "(span abnormal if duration_ms ≥ baseline μ + 3σ; "
        "support = abnormal_in_op / total_abnormal; "
        "confidence = abnormal_in_op / total_in_op; "
        "Jaccard = 2·support·confidence / (support + confidence)).",
        "",
        "operation,abnormal_n,total_n,support,confidence,jaccard",
    ]
    for r in rows[:40]:
        op_short = str(r["operation"]).replace(",", " ")[:80]
        parts.append(
            f"{op_short},{r['abnormal_n']},{r['total_n']},"
            f"{r['support']:.3f},{r['confidence']:.3f},{r['jaccard']:.3f}"
        )

    return "\n".join(parts)

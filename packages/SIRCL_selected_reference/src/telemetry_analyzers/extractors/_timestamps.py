"""
Time-unit normalization helpers for trace and log dataframes.

The repo's `DataCase` schema preserves loader-native fields by design — but
RE2 traces have an all-NaN `timestamp` column (real time is in `startTime`
microseconds and `startTimeMillis` milliseconds) and RE2 logs ship
nanosecond-resolution timestamps (vs. AIOPS-2022's epoch-second timestamps).
Comparing those raw values against `case.timestamp` (always epoch seconds)
silently corrupts every fault-window split that the feature extractors do.

This module exposes two functions used by all 8 trace + log extractors so
unit detection lives in one place. The split logic itself (`< t_a` vs
`>= t_a`) is unchanged — only the LHS gets normalized to seconds.

Detection by magnitude (heuristic; epoch-anchored):
    > 1e15  → nanoseconds   (e.g. 1.7e18 = 2024 in ns)
    > 1e12  → microseconds  (e.g. 1.7e15 = 2024 in μs)
    > 1e10  → milliseconds  (e.g. 1.7e12 = 2024 in ms)
    > 1e8   → seconds       (e.g. 1.7e9  = 2024 in s)
    else    → NaN (unrecognized)
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

def _detect_factor(magnitude: float) -> Optional[float]:
    """Return the divisor that converts `magnitude` to epoch seconds.

    None if the magnitude is implausibly small (treated as missing).
    """
    if not np.isfinite(magnitude):
        return None
    a = abs(magnitude)
    if a > 1e15:
        return 1e9   # ns → s
    if a > 1e12:
        return 1e6   # μs → s
    if a > 1e10:
        return 1e3   # ms → s
    if a > 1e8:
        return 1.0   # already seconds
    return None

def normalize_to_seconds(
    series: pd.Series,
    *,
    anchor: Optional[float] = None,
) -> pd.Series:
    """Normalize a numeric Series to epoch seconds with magnitude auto-detection.

    Args:
        series: any numeric-coercible Series.
        anchor: optional reference epoch-second value. If provided, used as a
            tiebreaker when detection is ambiguous (e.g., we expect the median
            normalized timestamp to be within 24 h of `anchor`).

    Returns Series of float seconds; NaN where the input is missing or its
    magnitude doesn't plausibly match any time unit.
    """
    numeric = pd.to_numeric(series, errors="coerce")
    finite = numeric.dropna()
    if finite.empty:
        return numeric.astype(float)

    median_mag = float(finite.abs().median())
    factor = _detect_factor(median_mag)
    if factor is None:
        return pd.Series(np.nan, index=series.index, dtype=float)

    out = (numeric / factor).astype(float)

    if anchor is not None and np.isfinite(anchor):
        # Sanity check: median should land within +/- 24 h of anchor; if not,
        # try the next-finer / next-coarser factor and pick whichever lands closer.
        candidate_factors = [factor]
        if factor < 1e9:
            candidate_factors.append(factor * 1e3)
        if factor > 1.0:
            candidate_factors.append(factor / 1e3)
        best = factor
        best_dist = abs((numeric / factor).dropna().median() - anchor)
        for f in candidate_factors[1:]:
            cand = (numeric / f).dropna().median()
            d = abs(cand - anchor)
            if d < best_dist:
                best, best_dist = f, d
        if best != factor:
            out = (numeric / best).astype(float)

    return out

def trace_time_seconds(
    traces_df: pd.DataFrame,
    *,
    anchor: Optional[float] = None,
) -> pd.Series:
    """Per-span timestamp in epoch seconds.

    Tries columns in order: `timestamp` (numeric, non-NaN) → `startTime` →
    `startTimeMillis` → `startTime_unix_nano`. Each column is normalized via
    magnitude auto-detection; we accept the first column whose finite ratio
    exceeds 50% of rows.

    Returns float Series aligned to `traces_df.index`. All NaN if no usable
    column is found.
    """
    if traces_df is None or traces_df.empty:
        return pd.Series([], dtype=float)

    candidates = [
        "timestamp",
        "startTime",
        "startTimeMillis",
        "startTime_unix_nano",
        "time",
    ]
    n = len(traces_df)
    for col in candidates:
        if col not in traces_df.columns:
            continue
        normed = normalize_to_seconds(traces_df[col], anchor=anchor)
        finite_frac = float(normed.notna().sum()) / max(1, n)
        if finite_frac >= 0.5:
            return normed
    return pd.Series(np.nan, index=traces_df.index, dtype=float)

def log_time_seconds(
    logs_df: pd.DataFrame,
    *,
    anchor: Optional[float] = None,
) -> pd.Series:
    """Per-log-line timestamp in epoch seconds. Similar to `trace_time_seconds`
    but tries log-conventional column names."""
    if logs_df is None or logs_df.empty:
        return pd.Series([], dtype=float)

    candidates = ["timestamp", "time", "ts", "@timestamp"]
    n = len(logs_df)
    for col in candidates:
        if col not in logs_df.columns:
            continue
        normed = normalize_to_seconds(logs_df[col], anchor=anchor)
        finite_frac = float(normed.notna().sum()) / max(1, n)
        if finite_frac >= 0.5:
            return normed
    return pd.Series(np.nan, index=logs_df.index, dtype=float)

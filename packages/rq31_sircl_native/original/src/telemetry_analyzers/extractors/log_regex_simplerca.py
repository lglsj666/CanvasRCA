"""
Per-service error-keyword frequency-ratio score — used by L2 (LogVariantR).

Scoring (per service):
  ERROR_KWS = {error, fail, exception, timeout, refused}; case-insensitive regex.

  baseline_err_freq = baseline_error_count / baseline_window_minutes
  current_err_freq  = current_error_count  / fault_window_minutes
  baseline_log_freq = baseline_total_logs  / baseline_window_minutes
  current_log_freq  = current_total_logs   / fault_window_minutes

  score components:
    (a) +100   if baseline_err_freq == 0 and current_err_freq > 0   (new errors)
    (b) +50 × (current/baseline) if baseline_err_freq > 0           (error spike ratio)
    (c) +20    if baseline_log_freq == 0 and current_log_freq > 0   (logs appeared)
    (d) +30 × (1 − current/baseline) if baseline_log_freq > 0
        and current/baseline < 1                                    (volume drop)

  When no baseline window is available (no logs before onset), fall back to
  `score = error_count × 10`.

Times are normalized to epoch seconds via the shared helper so RE2 (ns-resolution
log timestamps) and AIOPS-2022 (s-resolution) work without per-dataset branches.
"""

from __future__ import annotations

import re
from typing import Dict, List

import pandas as pd

from ...data.base import DataCase
from ._timestamps import log_time_seconds

ERROR_KWS = ("error", "fail", "exception", "timeout", "refused")
_ERROR_PATTERN = re.compile("|".join(ERROR_KWS), re.IGNORECASE)

def _window_minutes(ts_seconds: pd.Series) -> float:
    finite = ts_seconds.dropna()
    if finite.empty:
        return 1.0
    span = float(finite.max() - finite.min())
    return max(span / 60.0, 1.0)

def _count_errors(df: pd.DataFrame) -> int:
    if df.empty or "message" not in df.columns:
        return 0
    return int(sum(bool(_ERROR_PATTERN.search(str(m))) for m in df["message"]))

def _split_by_onset(case: DataCase):
    df = case.logs_df
    if df.empty:
        return df.iloc[0:0], df, pd.Series(dtype=float), pd.Series(dtype=float)
    ts_seconds = log_time_seconds(df, anchor=case.timestamp)
    if ts_seconds.notna().sum() == 0:
        return df.iloc[0:0], df.copy(), pd.Series(dtype=float), ts_seconds
    t_a = float(case.timestamp)
    base_mask = ts_seconds < t_a
    fault_mask = ts_seconds >= t_a
    return (
        df.loc[base_mask].copy(),
        df.loc[fault_mask].copy(),
        ts_seconds[base_mask],
        ts_seconds[fault_mask],
    )

def score_logs_simplerca(case: DataCase) -> str:
    if case.logs_df.empty or "container_name" not in case.logs_df.columns:
        return "No logs available."

    baseline, fault, base_ts, fault_ts = _split_by_onset(case)
    if fault.empty:
        return "No log lines in the fault window."

    base_minutes = _window_minutes(base_ts)
    fault_minutes = _window_minutes(fault_ts)

    # Per-service baseline stats
    base_err_per_min: Dict[str, float] = {}
    base_total_per_min: Dict[str, float] = {}
    if not baseline.empty:
        for svc, grp in baseline.groupby("container_name"):
            base_err_per_min[svc] = _count_errors(grp) / base_minutes
            base_total_per_min[svc] = len(grp) / base_minutes

    rows: List[Dict[str, object]] = []
    for svc, grp in fault.groupby("container_name"):
        err_count = _count_errors(grp)
        cur_err_per_min = err_count / fault_minutes
        cur_total_per_min = len(grp) / fault_minutes

        base_err = base_err_per_min.get(svc, 0.0)
        base_total = base_total_per_min.get(svc, 0.0)

        score = 0.0
        components: List[str] = []

        if not baseline.empty:
            # Error frequency component
            if base_err == 0.0 and cur_err_per_min > 0.0:
                score += 100.0
                components.append("new_errors:+100")
            elif base_err > 0.0:
                ratio = cur_err_per_min / base_err
                score += ratio * 50.0
                components.append(f"err_ratio×50:{ratio:.2f}={ratio*50:.1f}")

            # Volume component
            if base_total == 0.0 and cur_total_per_min > 0.0:
                score += 20.0
                components.append("logs_appeared:+20")
            elif base_total > 0.0:
                vol_ratio = cur_total_per_min / base_total
                if vol_ratio < 1.0:
                    drop = (1.0 - vol_ratio) * 30.0
                    score += drop
                    components.append(f"vol_drop×30:{vol_ratio:.2f}={drop:.1f}")
        else:
            # No baseline available
            score = float(err_count) * 10.0
            components.append(f"raw_count×10:{err_count}={score:.1f}")

        if score > 0.0:
            rows.append({
                "service": svc,
                "score": score,
                "errors": err_count,
                "total_lines": len(grp),
                "components": "; ".join(components),
            })

    if not rows:
        return "No services scored above zero (no error/volume signal)."

    rows.sort(key=lambda r: r["score"], reverse=True)
    parts: List[str] = [
        "Per-service score from 5-keyword error regex {error|fail|exception|timeout|refused} "
        "with baseline-vs-fault frequency-ratio components: "
        "+100 for new errors; +50 × (cur/base) for error spike ratio; "
        "+20 for logs-appeared-from-zero; +30 × (1 − cur/base) for volume drop.",
        "",
        "service,score,errors,total_lines,components",
    ]
    for r in rows:
        parts.append(
            f"{r['service']},{r['score']:.1f},{r['errors']},{r['total_lines']},{r['components']}"
        )

    silent = sorted(set(case.services) - set(r["service"] for r in rows))
    if silent:
        parts.append("")
        parts.append(f"# silent (no error/volume signal): {', '.join(silent)}")
    return "\n".join(parts)

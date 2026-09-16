"""
M1-MA — metrics tool (ThinkFL-style 3σ-fluctuation CSV).

Only the MA variant and its base class are carried over here; sibling metric
variants that pulled in ``sklearn`` and other helpers are intentionally omitted
since MA does not need them. The ``MetricsVariant`` ABC, ``_ThinkFLCSVBase`` and
``MetricsVariantMA`` bodies are unchanged from the reference implementation.

What it computes (per service)
------------------------------
Splits each service's metric columns into a baseline window (before a
trace-derived anomaly onset ``t_a``) and a current/fault window (from ``t_a``
onward). A metric column is reported when its current mean deviates from its
baseline mean by more than ``sigma`` (default 3) baseline standard deviations.
Reported metrics are emitted as a small CSV per service, ranked by deviation
magnitude.

  paper_source : ThinkFL §Eq. 6–7

Input: ``case.metrics_df`` — wide-format, columns ``timestamp`` + ``{service}_{metric}``.
Output: a text block, one ``--- {service} ---`` section per service.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from .data_case import DataCase


class MetricsVariant(ABC):
    """Common interface for all metrics tool variants."""

    @abstractmethod
    def get_metrics_context(self, case: DataCase) -> str:
        """Return the full metrics section text for all services in the case."""
        ...


# ===================================================================== #
#  MA — ThinkFL-style 3σ fluctuation CSV                                #
# ===================================================================== #

class _ThinkFLCSVBase(MetricsVariant):
    """
    Base class for ThinkFL-style 3σ CSV output with configurable split method.
    Subclasses override _get_split_time() to determine the baseline/anomalous boundary.
    """

    def __init__(self, sigma: float = 3.0):
        self._sigma = sigma

    def _get_split_time(self, case: DataCase) -> float:
        raise NotImplementedError

    def get_metrics_context(self, case: DataCase) -> str:
        df = case.metrics_df
        if df.empty:
            return "No metrics data available."

        t_a = self._get_split_time(case)
        ts_col = self._find_ts_col(df)
        if ts_col is not None:
            baseline_df = df[df[ts_col] < t_a].drop(columns=[ts_col])
            current_df = df[df[ts_col] >= t_a].drop(columns=[ts_col])
        else:
            n = len(df)
            baseline_df = df.iloc[: n // 2]
            current_df = df.iloc[n // 2:]

        if baseline_df.empty or current_df.empty:
            return "Insufficient data for fluctuation analysis."

        parts: list[str] = []
        for svc in sorted(case.services):
            svc_cols = [c for c in baseline_df.columns if c.startswith(f"{svc}_")]
            if not svc_cols:
                parts.append(f"--- {svc} ---")
                parts.append(f"No metrics found for service '{svc}'.")
                continue

            rows = []
            for col in svc_cols:
                metric = col[len(svc) + 1:]
                b = pd.to_numeric(baseline_df[col], errors="coerce").dropna().values
                c = pd.to_numeric(current_df[col], errors="coerce").dropna().values
                if len(b) < 2 or len(c) < 1:
                    continue
                b_mean, b_std = float(np.mean(b)), float(np.std(b))
                c_mean, c_std = float(np.mean(c)), float(np.std(c))
                if b_std == 0:
                    continue
                if abs(c_mean - b_mean) > self._sigma * b_std:
                    rows.append({
                        "key": f"{svc}.{metric}",
                        "regular_mean": round(b_mean, 2),
                        "regular_std_dev": round(b_std, 2),
                        "current_mean": round(c_mean, 2),
                        "current_std_dev": round(c_std, 2),
                        "_deviation": abs(c_mean - b_mean) / b_std,
                    })

            parts.append(f"--- {svc} ---")
            if not rows:
                parts.append("No fluctuating metrics found.")
            else:
                rows.sort(key=lambda r: r["_deviation"], reverse=True)
                lines = ["key,regular_mean,regular_std_dev,current_mean,current_std_dev"]
                for r in rows:
                    lines.append(
                        f"{r['key']},{r['regular_mean']},{r['regular_std_dev']},"
                        f"{r['current_mean']},{r['current_std_dev']}"
                    )
                parts.append("\n".join(lines))

        return "\n".join(parts)

    @staticmethod
    def _find_ts_col(df: pd.DataFrame):
        for c in ("timestamp", "time", "ts", "t"):
            if c in df.columns:
                return c
        return None


class MetricsVariantMA(_ThinkFLCSVBase):
    """ThinkFL CSV with trace-derived anomaly onset (ThinkFL-faithful)."""

    def _get_split_time(self, case: DataCase) -> float:
        from .anomaly_onset import detect_onset_from_traces
        return detect_onset_from_traces(case)


def score_metrics_thinkfl(case: DataCase) -> str:
    """Module-level convenience wrapper mirroring the trace/log tool signatures."""
    return MetricsVariantMA().get_metrics_context(case)

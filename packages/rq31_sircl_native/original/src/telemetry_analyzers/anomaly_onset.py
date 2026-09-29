"""
Data-driven anomaly onset detection — no fault injection timestamp required.

Two detection methods:
- detect_onset_from_traces: trace latency spike detection
- detect_onset_from_metrics: change point detection (BOCPD) on metrics

Both return a timestamp (float) to split metrics into baseline/anomalous periods.
Fallback: midpoint of the data timestamp range.
"""

from __future__ import annotations

import logging
from functools import partial
from itertools import islice
from typing import Optional

import numpy as np
import scipy.stats as ss
from numpy.linalg import inv

import pandas as pd

from ..data.base import DataCase


# ===================================================================== #
#  Multivariate BOCPD                                                   #
# ===================================================================== #

class _MultivariateT:
    """Multivariate Student T posterior predictive."""

    def __init__(self, dims: int = 1, dof: int = 0, kappa: int = 1):
        if dof == 0:
            dof = dims + 1
        self.t = 0
        self.dims = dims
        self.dof = np.array([dof])
        self.kappa = np.array([kappa])
        self.mu = np.array([[0] * dims])
        self.scale = np.array([np.identity(dims)])

    def pdf(self, data: np.ndarray):
        self.t += 1
        t_dof = self.dof - self.dims + 1
        expanded = np.expand_dims((self.kappa * t_dof) / (self.kappa + 1), (1, 2))
        ret = np.empty(self.t)
        for i, (df, loc, shape) in islice(
            enumerate(zip(t_dof, self.mu, inv(expanded * self.scale))), self.t
        ):
            ret[i] = ss.multivariate_t.pdf(x=data, df=df, loc=loc, shape=shape)
        return ret

    def update_theta(self, data: np.ndarray, **kwargs):
        centered = data - self.mu
        self.scale = np.concatenate([
            self.scale[:1],
            inv(
                inv(self.scale)
                + np.expand_dims(self.kappa / (self.kappa + 1), (1, 2))
                * (np.expand_dims(centered, 2) @ np.expand_dims(centered, 1))
            ),
        ])
        self.mu = np.concatenate([
            self.mu[:1],
            (np.expand_dims(self.kappa, 1) * self.mu + data)
            / np.expand_dims(self.kappa + 1, 1),
        ])
        self.dof = np.concatenate([self.dof[:1], self.dof + 1])
        self.kappa = np.concatenate([self.kappa[:1], self.kappa + 1])


def _constant_hazard(lam, r):
    return 1 / lam * np.ones(r.shape)


def _online_changepoint_detection(data, hazard_fn, likelihood):
    """Bayesian Online Change Point Detection."""
    maxes = np.zeros(len(data) + 1)
    R = np.zeros((len(data) + 1, len(data) + 1))
    R[0, 0] = 1
    for t, x in enumerate(data):
        predprobs = likelihood.pdf(x)
        H = hazard_fn(np.array(range(t + 1)))
        R[1: t + 2, t + 1] = R[0: t + 1, t] * predprobs * (1 - H)
        R[0, t + 1] = np.sum(R[0: t + 1, t] * predprobs * H)
        total = np.sum(R[:, t + 1])
        if total > 0:
            R[:, t + 1] /= total
        likelihood.update_theta(x, t=t)
        maxes[t] = R[:, t].argmax()
    return R, maxes


def _find_cps(maxes):
    """Find change points from BOCPD maxes array."""
    cps = []
    for i in range(1, len(maxes)):
        if abs(maxes[i] - maxes[i - 1]) > 1:
            cps.append((i, abs(maxes[i] - maxes[i - 1])))
    return cps

logger = logging.getLogger(__name__)


def _get_timestamp_range(df: pd.DataFrame) -> tuple[Optional[float], Optional[float]]:
    """Get (min, max) timestamp from a DataFrame with a timestamp column."""
    for col in ("timestamp", "time", "ts"):
        if col in df.columns:
            ts = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(ts) > 0:
                return float(ts.min()), float(ts.max())
    return None, None


def _midpoint_fallback(case: DataCase) -> float:
    """Fallback: midpoint of the metrics timestamp range."""
    t_min, t_max = _get_timestamp_range(case.metrics_df)
    if t_min is not None and t_max is not None:
        return (t_min + t_max) / 2
    return case.timestamp  # last resort


# ===================================================================== #
#  Trace latency spike detection                                        #
# ===================================================================== #

def detect_onset_from_traces(case: DataCase, window_sec: float = 60.0) -> float:
    """
    Detect anomaly onset from trace latency spikes.

    Computes P90 latency of entry spans in sliding windows, detects
    when latency exceeds baseline + 3σ. Returns the timestamp of the
    first anomalous window.

    Falls back to midpoint if no traces or no spike detected.
    """
    traces = case.traces_df
    if traces.empty or "duration_ms" not in traces.columns:
        logger.debug("No trace data; falling back to midpoint")
        return _midpoint_fallback(case)

    # Get entry spans (frontend or root spans)
    entry_spans = _get_entry_spans(traces)
    if entry_spans.empty or len(entry_spans) < 10:
        logger.debug("Too few entry spans (%d); falling back to midpoint", len(entry_spans))
        return _midpoint_fallback(case)

    ts_col = "timestamp" if "timestamp" in entry_spans.columns else None
    if ts_col is None:
        return _midpoint_fallback(case)

    entry_spans = entry_spans.sort_values(ts_col)
    timestamps = pd.to_numeric(entry_spans[ts_col], errors="coerce").values
    latencies = pd.to_numeric(entry_spans["duration_ms"], errors="coerce").values

    valid = np.isfinite(timestamps) & np.isfinite(latencies)
    timestamps, latencies = timestamps[valid], latencies[valid]
    if len(timestamps) < 10:
        return _midpoint_fallback(case)

    # Sliding window P90 latency
    t_min, t_max = timestamps[0], timestamps[-1]
    window_starts = np.arange(t_min, t_max - window_sec + 1, window_sec / 2)
    if len(window_starts) < 4:
        return _midpoint_fallback(case)

    p90s = []
    window_times = []
    for ws in window_starts:
        mask = (timestamps >= ws) & (timestamps < ws + window_sec)
        if np.sum(mask) >= 3:
            p90s.append(float(np.percentile(latencies[mask], 90)))
            window_times.append(ws + window_sec / 2)

    if len(p90s) < 4:
        return _midpoint_fallback(case)

    p90s = np.array(p90s)
    window_times = np.array(window_times)

    # Baseline: first 30% of windows
    n_baseline = max(2, int(len(p90s) * 0.3))
    baseline = p90s[:n_baseline]
    b_mean = float(np.mean(baseline))
    b_std = float(np.std(baseline))
    if b_std == 0:
        b_std = b_mean * 0.1 if b_mean > 0 else 1.0

    threshold = b_mean + 3 * b_std

    # Find first window exceeding threshold
    for i in range(n_baseline, len(p90s)):
        if p90s[i] > threshold:
            t_a = float(window_times[i])
            logger.debug("Trace onset detected at t=%.1f (P90=%.1f > threshold=%.1f)", t_a, p90s[i], threshold)
            return t_a

    logger.debug("No trace latency spike detected; falling back to midpoint")
    return _midpoint_fallback(case)


def _get_entry_spans(traces: pd.DataFrame) -> pd.DataFrame:
    """Get entry-point spans (frontend service or root spans)."""
    # Try frontend service first
    if "service_name" in traces.columns:
        frontend = traces[traces["service_name"].str.contains("frontend", case=False, na=False)]
        if len(frontend) >= 10:
            return frontend

    # Fallback: root spans (no parent)
    if "parent_span_id" in traces.columns:
        root_mask = traces["parent_span_id"].isna() | \
                    traces["parent_span_id"].astype(str).isin(["", "nan", "None"])
        roots = traces[root_mask]
        if len(roots) >= 10:
            return roots

    return traces.head(0)


# ===================================================================== #
#  Change point detection on metrics                                    #
# ===================================================================== #

def detect_onset_from_metrics(case: DataCase) -> float:
    """
    Detect anomaly onset via Multivariate BOCPD on latency/error metrics.
    Returns the first detected change point, or the midpoint if none found.
    """
    df = case.metrics_df
    if df.empty:
        return _midpoint_fallback(case)

    ts_col = None
    for c in ("timestamp", "time", "ts"):
        if c in df.columns:
            ts_col = c
            break
    if ts_col is None:
        return _midpoint_fallback(case)

    timestamps = pd.to_numeric(df[ts_col], errors="coerce").values

    # Select latency + error metrics
    latency_error_cols = [
        c for c in df.columns if c != ts_col and (
            "latency" in c.lower() or
            "duration" in c.lower() or
            "request_duration" in c.lower() or
            "_error" in c.lower() or
            ".http.5" in c.lower()  # HTTP 5xx error counts
        )
    ]

    if not latency_error_cols:
        latency_error_cols = [c for c in df.columns if "istio_request" in c.lower()]

    if not latency_error_cols:
        logger.debug("No latency/error metrics found; falling back to midpoint")
        return _midpoint_fallback(case)

    # Prepare data for BOCPD
    # Aggregate to per-service-type signals to keep dimensionality manageable
    # (raw AIOPS-2022 has 300+ latency/error cols; BOCPD is O(n²×d³))
    signal_df = df[latency_error_cols].apply(pd.to_numeric, errors="coerce")
    signal_df = signal_df.ffill().fillna(0)

    # Group columns by service type and aggregate to mean per service
    import re as _re
    svc_signals: dict[str, list] = {}
    for col in signal_df.columns:
        m = _re.match(r'^(.+?)-\d+_', col)
        svc_type = m.group(1) if m else col.split("_")[0]
        svc_signals.setdefault(svc_type, []).append(col)

    # Create low-dimensional signal: mean of latency/error per service type.
    # Hard cap at MAX_BOCPD_DIMS: _MultivariateT.pdf() does O(T²×d³) matrix
    # inversions, so keep only the top-10 most-varying service-type signals.
    MAX_BOCPD_DIMS = 10
    agg_cols = []
    for svc_type, cols in sorted(svc_signals.items()):
        agg_cols.append(signal_df[cols].mean(axis=1))
    if not agg_cols:
        return _midpoint_fallback(case)

    agg_df = pd.concat(agg_cols, axis=1)

    # Drop constant columns and normalize to [0, 1]
    non_const = agg_df.loc[:, agg_df.nunique() > 1]
    if non_const.empty:
        return _midpoint_fallback(case)

    # If more dimensions than cap, keep the top-variance ones
    if non_const.shape[1] > MAX_BOCPD_DIMS:
        top_cols = non_const.var().nlargest(MAX_BOCPD_DIMS).index
        non_const = non_const[top_cols]

    for c in non_const.columns:
        c_min, c_max = non_const[c].min(), non_const[c].max()
        c_range = c_max - c_min
        if c_range == 0 or np.isnan(c_range):
            non_const[c] = 0
        else:
            non_const[c] = (non_const[c] - c_min) / c_range

    data_array = non_const.fillna(0).to_numpy()
    if len(data_array) < 5 or data_array.shape[1] == 0:
        return _midpoint_fallback(case)

    try:
        R, maxes = _online_changepoint_detection(
            data_array,
            partial(_constant_hazard, 50),
            _MultivariateT(dims=data_array.shape[1]),
        )
        cps = _find_cps(maxes)
        anomalies = [p[0] for p in cps]

        if anomalies:
            cp_idx = int(anomalies[0])
            if cp_idx < len(timestamps):
                t_a = float(timestamps[cp_idx])
                logger.debug("BOCPD onset at index %d, t=%.1f", cp_idx, t_a)
                return t_a
    except Exception as e:
        logger.warning("BOCPD failed: %s; falling back to midpoint", e)

    logger.debug("No change point detected; falling back to midpoint")
    return _midpoint_fallback(case)

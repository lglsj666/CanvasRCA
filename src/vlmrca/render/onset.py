"""
Per-service anomaly onset: *when* each service started misbehaving.

The rest of the renderer answers "how badly" -- peak deviation, ranked. That
ordering cannot separate an origin from its victims, because a victim often
deviates harder than the thing that broke it (a saturated database moves its own
CPU by a little and the latency of every service queuing behind it by a lot).
What separates them is order of arrival, and nothing in the pipeline computed it
before this module.

Two sources, in preference order:

* **Traces.** Spans carry microsecond timestamps, and there are 86k-1.2M of them
  per case, so binning them gives a per-service latency curve at whatever
  resolution the case can support. This is the only usable clock on the datasets
  the project screens against: AegisLab's metrics arrive every 15 s and its
  inferred fault window is a median 12 s wide -- one sample, which orders
  nothing.
* **Metrics**, for services the traces never mention (databases, queues and
  message brokers appear in metric tables but rarely as span emitters).

Nothing here may touch the injection timestamp. Baselines are anchored on the
telemetry-derived fault window, exactly as `infer_fault_window` is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from vlmrca.render.kpi_select import (
    MIN_BASELINE_VALID,
    Z_CAP,
    ScoredSeries,
    _baseline_slice,
    valid_deviation,
)

OnsetSource = Literal["trace", "metric", "none"]

# Target number of bins across the case window. Enough that onsets separated by a
# couple of hops are distinguishable, few enough that each bin holds sufficient
# spans for a stable p95.
TARGET_BINS = 48
MIN_BIN_SEC = 5.0
MAX_BIN_SEC = 60.0

# Spans needed in a bin before its p95 is trusted.
MIN_SPANS_PER_BIN = 3

# Baseline bins needed before the pre-fault window is used; below this the first
# 30% of a service's populated bins stands in.
MIN_BASELINE_BINS = 4
BASELINE_FRAC = 0.30

# A service whose baseline latency is genuinely constant would divide by zero and
# call every subsequent wobble infinite. Floor sigma relative to the mean.
SIGMA_FLOOR_FRAC = 0.10

# Share of a metric series' eventual peak that its first crossing must reach.
# The metric path is the noisier of the two and it competes for the same rows as
# the trace path, so it is held to the stricter rule.
METRIC_ONSET_PEAK_FRAC = 0.50

# How anomalous a service's best series must be before its onset is reported at
# all. A 3-sigma floor sounds conservative and is not: in a 104-service case
# dozens of services own some series that wanders 3 sigma once, they all "onset"
# in the first seconds of the window, and they fill every row ahead of the
# services that actually broke. Selected panels on AegisLab run to a median |z|
# near 180, so 3 is indistinguishable from quiet.
MIN_METRIC_ONSET_SCORE = 10.0

# Pod suffixes: `svc-0` (StatefulSet ordinal) and `svc-6f94c8fb-xk2p9`
# (Deployment replicaset hash + pod suffix).
_ORDINAL_SUFFIX = re.compile(r"^(.+?)-\d+$")
_REPLICASET_SUFFIX = re.compile(r"^(.+?)-[0-9a-f]{6,10}-[0-9a-z]{5}$")
# Physical machines, which are not services and must not be folded into one.
_WORKER_NODE = re.compile(r"^(node|worker)-?\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class ServiceOnset:
    """When one service's telemetry first went out of band, and how it was found."""

    service: str
    onset_ts: Optional[float]  # epoch seconds; None = nothing crossed
    peak_z: float
    source: OnsetSource
    n_samples: int  # spans (trace) or valid points (metric)


def pod_to_service(name: str) -> str:
    """
    Collapse a pod or container name to its service.

    Metric entities, trace `service_name`s and call-graph nodes are three
    different naming universes -- AegisLab's graph carries 104 nodes covering 30
    service-level names, 47 pods and 6 physical workers. Onsets have to be keyed
    on something all three can be projected onto, or the propagation panel joins
    nothing.
    """
    s = str(name)
    if _WORKER_NODE.match(s):
        return s
    m = _REPLICASET_SUFFIX.match(s)
    if m:
        return m.group(1)
    m = _ORDINAL_SUFFIX.match(s)
    if m:
        return m.group(1)
    return s


def service_level_projection(graph, node_pod_map: Optional[Dict] = None):
    """
    Project a call graph onto service-level names.

    Drops physical worker nodes and the hosting edges that attach to them: those
    say which machine ran a pod, not who called whom, and a propagation story
    told along them is meaningless.
    """
    import networkx as nx

    hosted = set()
    if node_pod_map:
        for node, pods in sorted(node_pod_map.items()):
            hosted.add(str(node))
            if isinstance(pods, (list, tuple, set)):
                hosted.update(str(p) for p in pods)

    out = nx.DiGraph()
    for n in sorted(graph.nodes()):
        if _WORKER_NODE.match(str(n)):
            continue
        out.add_node(pod_to_service(n))
    for a, b in sorted(graph.edges()):
        if _WORKER_NODE.match(str(a)) or _WORKER_NODE.match(str(b)):
            continue
        # A worker->pod hosting edge survives the name test when the worker is
        # named something other than `node-N`; node_pod_map names them outright.
        if node_pod_map and str(a) in node_pod_map:
            continue
        sa, sb = pod_to_service(a), pod_to_service(b)
        if sa != sb:  # replica-to-replica calls collapse to a self-loop
            out.add_edge(sa, sb)
    return out


def _bin_seconds(span: float) -> float:
    if not np.isfinite(span) or span <= 0:
        return MIN_BIN_SEC
    return float(np.clip(span / TARGET_BINS, MIN_BIN_SEC, MAX_BIN_SEC))


def _first_crossing(
    centres: np.ndarray,
    values: np.ndarray,
    baseline_mask: np.ndarray,
    k_sigma: float,
) -> Tuple[Optional[float], float]:
    """
    First bin whose value clears mu + k sigma and stays there.

    Persistence matters because a single slow bin is the normal texture of tail
    latency; requiring the next populated bin to cross as well rejects that
    without rejecting a fault that resolves quickly, which is what the doubled
    threshold exemption is for.
    """
    base = values[baseline_mask]
    base = base[np.isfinite(base)]
    if base.size == 0:
        return None, 0.0
    mu = float(np.mean(base))
    sigma = float(np.std(base))
    sigma = max(sigma, SIGMA_FLOOR_FRAC * abs(mu))
    if sigma <= 0:
        return None, 0.0

    post = np.flatnonzero(~baseline_mask & np.isfinite(values))
    if post.size == 0:
        return None, 0.0
    z = (values[post] - mu) / sigma
    peak_z = float(np.clip(np.nanmax(z), -Z_CAP, Z_CAP)) if z.size else 0.0

    for i, pos in enumerate(post):
        if z[i] < k_sigma:
            continue
        is_last = i + 1 >= post.size
        if z[i] >= 2 * k_sigma or is_last or z[i + 1] >= k_sigma:
            return float(centres[pos]), peak_z
    return None, peak_z


def _trace_onsets(
    traces_df: pd.DataFrame,
    fault_window: Optional[Tuple[float, float]],
    full_range: Optional[Tuple[float, float]],
    k_sigma: float,
) -> Dict[str, ServiceOnset]:
    """Per-service p95 span latency, binned, first crossing per service."""
    from vlmrca.render.panels import resolve_time_seconds

    if traces_df is None or traces_df.empty:
        return {}
    if "service_name" not in traces_df.columns or "duration_ms" not in traces_df.columns:
        return {}

    ts = resolve_time_seconds(traces_df, full_range or fault_window)
    if ts is None:
        return {}
    dur = pd.to_numeric(traces_df["duration_ms"], errors="coerce")
    svc = traces_df["service_name"].astype(str).map(pod_to_service)

    frame = pd.DataFrame({"t": ts.to_numpy(), "dur": dur.to_numpy(), "svc": svc.to_numpy()})
    frame = frame[np.isfinite(frame["t"]) & np.isfinite(frame["dur"])]
    if frame.empty:
        return {}

    lo = float(full_range[0]) if full_range else float(frame["t"].min())
    hi = float(full_range[1]) if full_range else float(frame["t"].max())
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return {}
    frame = frame[(frame["t"] >= lo) & (frame["t"] <= hi)]
    if frame.empty:
        return {}

    bin_sec = _bin_seconds(hi - lo)
    frame["bin"] = ((frame["t"] - lo) // bin_sec).astype("int64")

    # One pass over every span in the case.
    agg = frame.groupby(["svc", "bin"])["dur"].agg(p95=lambda d: d.quantile(0.95), n="size")
    agg = agg[agg["n"] >= MIN_SPANS_PER_BIN]
    if agg.empty:
        return {}

    n_bins = int((hi - lo) // bin_sec) + 1
    centres = lo + (np.arange(n_bins) + 0.5) * bin_sec

    out: Dict[str, ServiceOnset] = {}
    for service in sorted(agg.index.get_level_values("svc").unique()):
        sub = agg.loc[service]
        values = np.full(n_bins, np.nan, dtype="float64")
        idx = sub.index.to_numpy()
        keep = (idx >= 0) & (idx < n_bins)
        values[idx[keep]] = sub["p95"].to_numpy()[keep]
        populated = np.flatnonzero(np.isfinite(values))
        if populated.size < 2:
            continue

        # Baseline is everything before the estimated fault window.
        #
        # The tempting alternative -- cut at a fixed leading fraction, to leave
        # more room for onsets to spread out and order themselves -- measured
        # worse, and instructively so. These traces carry real pre-injection
        # wander, and an earlier cut reads that wander as onset: on the AegisLab
        # mysql-partition case it promoted eight services that were merely noisy
        # early and pushed the injected `mysql` out of the panel entirely, from
        # first place.
        #
        # The cost is that onsets bunch in the first bins after the cut. That is
        # mostly honest rather than a defect: an injected fault reaches everything
        # it is going to reach within a bin or two, and call-graph propagation is
        # a sub-second phenomenon that no 10 s binning can resolve. What this
        # panel can show is which services were affected and the coarse order
        # when a fault ramps -- not a millisecond causal chain.
        baseline_mask = np.zeros(n_bins, dtype=bool)
        if fault_window is not None:
            baseline_mask = centres < float(fault_window[0])
        if int(np.isfinite(values[baseline_mask]).sum()) < MIN_BASELINE_BINS:
            cut = max(1, int(populated.size * BASELINE_FRAC))
            baseline_mask = np.zeros(n_bins, dtype=bool)
            baseline_mask[populated[:cut]] = True

        onset_ts, peak_z = _first_crossing(centres, values, baseline_mask, k_sigma)
        n_spans = int(sub["n"].sum())
        if onset_ts is None:
            continue
        out[service] = ServiceOnset(
            service=service,
            onset_ts=onset_ts,
            peak_z=peak_z,
            source="trace",
            n_samples=n_spans,
        )
    return out


def _metric_onsets(
    metrics_df: pd.DataFrame,
    scored: Sequence[ScoredSeries],
    k_sigma: float,
) -> Dict[str, ServiceOnset]:
    """
    First crossing of the best-scoring series per service.

    Deliberately not `peak_idx`: the peak is where a fault is worst, which is
    routinely minutes after it began, and using it would order services by
    severity while claiming to order them by time.
    """
    if metrics_df is None or metrics_df.empty or "timestamp" not in metrics_df.columns:
        return {}
    ts = pd.to_numeric(metrics_df["timestamp"], errors="coerce").astype("float64").to_numpy()
    # Where the scorer stopped calling rows nominal. Upstream centres each case
    # window on the injection, so this is also roughly where a fault can start.
    base_cut = _baseline_slice(len(metrics_df)).stop

    best: Dict[str, ScoredSeries] = {}
    for s in scored:
        if s.score < MIN_METRIC_ONSET_SCORE or s.baseline_valid < MIN_BASELINE_VALID:
            continue
        key = pod_to_service(s.service)
        if key not in best or s.score > best[key].score:
            best[key] = s

    out: Dict[str, ServiceOnset] = {}
    for service in sorted(best):
        s = best[service]
        dev, idx = valid_deviation(metrics_df, s)
        if dev.size == 0:
            continue
        peak_pos = int(np.searchsorted(idx, s.peak_idx))
        if peak_pos >= dev.size or idx[peak_pos] != s.peak_idx:
            continue
        # Half the peak, not a quarter, and it has to hold. A 3-sigma floor put
        # a dozen services at the top of the ordering on their own baseline
        # noise, ahead of every service with a real trace-derived onset -- which
        # inverts the one thing this panel exists to show. A first crossing is
        # only worth reporting if it is a recognisable share of what that series
        # eventually does.
        thresh = max(k_sigma, METRIC_ONSET_PEAK_FRAC * dev[peak_pos])
        crossings = np.flatnonzero(dev >= thresh)
        # Only after the baseline region. A crossing inside it is noise by
        # construction -- those very samples are what defined "normal" -- and
        # reporting one produced onsets at "+0.0m", i.e. a fault that began
        # before the window did, which then sorted straight to the top row.
        crossings = crossings[(crossings <= peak_pos) & (idx[crossings] >= base_cut)]
        first = None
        for pos in crossings:
            if pos == peak_pos or (pos + 1 < dev.size and dev[pos + 1] >= thresh):
                first = int(pos)
                break
        if first is None:
            continue
        row = int(idx[first])
        if not (0 <= row < len(ts)) or not np.isfinite(ts[row]):
            continue
        out[service] = ServiceOnset(
            service=service,
            onset_ts=float(ts[row]),
            peak_z=float(min(s.score, Z_CAP)),
            source="metric",
            n_samples=int(s.n_valid),
        )
    return out


def compute_service_onsets(
    traces_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    scored: Sequence[ScoredSeries],
    fault_window: Optional[Tuple[float, float]],
    full_range: Optional[Tuple[float, float]],
    services: Sequence[str],
    k_sigma: float = 3.0,
) -> Dict[str, ServiceOnset]:
    """
    Onset per service, traces first and metrics filling the gaps.

    Every service in `services` gets an entry, including a `source="none"` one
    when nothing crossed: "we looked and saw nothing" and "we never looked" have
    to be distinguishable, or the panel silently omits quiet services and the
    reader reads absence as evidence.
    """
    onsets = dict(_trace_onsets(traces_df, fault_window, full_range, k_sigma))
    for service, entry in _metric_onsets(metrics_df, scored, k_sigma).items():
        onsets.setdefault(service, entry)

    for raw in services:
        key = pod_to_service(raw)
        onsets.setdefault(
            key, ServiceOnset(service=key, onset_ts=None, peak_z=0.0, source="none", n_samples=0)
        )
    return {k: onsets[k] for k in sorted(onsets)}


def onset_order(onsets: Dict[str, ServiceOnset]) -> List[ServiceOnset]:
    """Services that have an onset, earliest first; ties broken by severity."""
    detected = [o for o in onsets.values() if o.onset_ts is not None]
    detected.sort(key=lambda o: (o.onset_ts, -o.peak_z, o.service))
    return detected

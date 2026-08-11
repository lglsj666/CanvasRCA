"""
KPI selection: choose which of ~50-5000 metric series earn a panel.

This is the highest-leverage knob in the whole dashboard (RQ1 axis A): a panel
budget of 12 out of 5000 AegisLab series means selection, not rendering, decides
whether the evidence is even visible.

Rankers here reimplement the *scoring* logic of the upstream text variants
(k-sigma in MetricsVariantMA/MB, robust scaling in BaroAnalyzer) rather than
calling them, because those emit formatted CSV text; we need the numeric score
per column plus the anomaly window to drive shading and topology colouring.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

Ranker = Literal["ksigma", "robust", "coverage"]

# How the panel budget is spent, once every series has a score. Separated from
# `Ranker` because scoring a series and allocating the budget are different
# decisions -- "coverage" was previously a Ranker value, which conflated them.
# That spelling still works and maps to coverage_first with every slot reserved.
Selector = Literal["topk", "coverage_first"]

# Deviation scores are clipped here so a near-zero baseline cannot produce a
# 1e9 "z-score" that both dominates ranking and prints as garbage on a panel.
Z_CAP = 999.0
SPREAD_FLOOR_FRAC = 1e-3

# Baseline points needed before a column's own spread is trusted. The old floor
# was 3, which is where the "flat baseline" epidemic came from: three samples of
# a slow-moving counter look perfectly flat, the spread collapses to the
# magnitude floor, and the series scores >=999z on noise. A quarter of all v0
# panels carried that sentinel, and they crowded out series with real excursions.
#
# It cannot simply be raised to "enough for a std", because sparse is normal
# here: AegisLab columns carry 8-96 valid samples in a 1064-row frame by
# construction, and dropping them would empty the dashboard on the project's
# primary screening dataset. Hence the two-tier rule in score_series -- trust the
# column's own spread above this, borrow the family's below it.
MIN_BASELINE_VALID = 8

# When borrowing, how much of the family's typical relative spread to require.
# Half: enough to stop a 3-sample flat read from scoring 999z, loose enough that a
# genuinely quieter member of a noisy family still registers as anomalous.
FAMILY_FLOOR_FRAC = 0.5


@dataclass
class ScoredSeries:
    """One metric column, with everything the renderer needs to draw it."""

    column: str
    service: str
    metric: str
    score: float
    peak_idx: int
    peak_value: float
    baseline_mean: float
    baseline_std: float
    n_valid: int = 0
    baseline_valid: int = 0

    @property
    def signed_z(self) -> float:
        """Peak deviation in baseline sigmas, sign preserved (drops matter too)."""
        if self.baseline_std <= 0:
            return 0.0
        z = (self.peak_value - self.baseline_mean) / self.baseline_std
        return float(np.clip(z, -Z_CAP, Z_CAP))


def split_service_metric(column: str, services: Sequence[str]) -> Tuple[str, str]:
    """
    Split a wide-format column ``{service}_{metric}`` into its parts.

    Service names themselves contain underscores in several datasets, so match
    against the known service list longest-first instead of splitting on "_".
    """
    for svc in sorted(services, key=len, reverse=True):
        if column.startswith(svc + "_"):
            return svc, column[len(svc) + 1 :]
    if "_" in column:
        head, tail = column.split("_", 1)
        return head, tail
    return column, column


def _baseline_slice(n: int, fault_frac: float = 0.5) -> slice:
    """
    Rows treated as nominal when computing deviation.

    Upstream loaders centre each case's window on the injection, so the leading
    portion is nominal. Using a fraction rather than an absolute index keeps this
    correct across datasets with different window lengths.
    """
    cut = max(3, int(n * fault_frac))
    return slice(0, cut)


def _column_stats(vals: np.ndarray, base: slice, ranker: Ranker):
    """Baseline centre and spread for one column, plus the counts behind them."""
    baseline = vals[base]
    baseline = baseline[~np.isnan(baseline)]
    if ranker == "robust":
        centre = float(np.median(baseline)) if baseline.size else np.nan
        mad = float(np.median(np.abs(baseline - centre))) if baseline.size else np.nan
        spread = mad * 1.4826  # MAD → sigma-equivalent, as BaroAnalyzer does
    else:
        centre = float(np.mean(baseline)) if baseline.size else np.nan
        spread = float(np.std(baseline)) if baseline.size else np.nan
    return centre, spread, baseline.size


def _family_relative_spreads(
    metrics_df: pd.DataFrame,
    cols: Sequence[str],
    services: Sequence[str],
    base: slice,
    ranker: Ranker,
    min_baseline_valid: int = MIN_BASELINE_VALID,
) -> Dict[str, float]:
    """
    Median relative spread (spread / magnitude) per metric family, over the
    columns well-sampled enough to measure it honestly.

    A thinly-sampled column has no usable noise estimate of its own, but its
    family siblings do -- `hubble_http_request_duration_p50_seconds` on one
    service is the same instrument as on another. Borrowing the family's typical
    noise is what stops three flat samples from reading as a 999-sigma event.
    """
    per_family: Dict[str, List[float]] = {}
    for col in cols:
        vals = pd.to_numeric(metrics_df[col], errors="coerce").astype("float64").to_numpy()
        centre, spread, n_base = _column_stats(vals, base, ranker)
        if n_base < min_baseline_valid:
            continue
        if not np.isfinite(spread) or spread <= 0:
            continue
        finite = vals[np.isfinite(vals)]
        scale = float(np.max(np.abs(finite))) if finite.size else 0.0
        scale = max(scale, abs(centre) if np.isfinite(centre) else 0.0)
        if scale <= 0:
            continue
        _, metric = split_service_metric(col, services)
        per_family.setdefault(metric_family(metric), []).append(spread / scale)
    return {fam: float(np.median(v)) for fam, v in sorted(per_family.items())}


def score_series(
    metrics_df: pd.DataFrame,
    services: Sequence[str],
    fault_frac: float = 0.5,
    ranker: Ranker = "ksigma",
) -> List[ScoredSeries]:
    """Score every numeric metric column by how anomalous it looks."""
    if metrics_df is None or metrics_df.empty:
        return []

    cols = [c for c in metrics_df.columns if c != "timestamp"]
    n = len(metrics_df)
    base = _baseline_slice(n, fault_frac)
    out: List[ScoredSeries] = []

    # One pass to learn what each metric family's noise looks like, before any
    # column with too few baseline points asks to borrow it.
    family_rel_spread = _family_relative_spreads(
        metrics_df, cols, services, base, ranker
    )
    baseline_slots = max(0, int(base.stop or 0) - int(base.start or 0))
    if not family_rel_spread and 3 <= baseline_slots < MIN_BASELINE_VALID:
        # A short-but-dense incident can have thousands of observations and
        # hundreds of metric series compressed onto fewer than 16 unique
        # timestamps. The normal eight-point reliability floor then rejects
        # every column and manufactures an empty dashboard even though the
        # telemetry is present. Calibrate relative spread across metric-family
        # siblings using the available >=3 baseline timestamps only in this
        # all-or-nothing short-window case. The per-series path below still
        # borrows/floors against that family distribution; it never invents a
        # label-aware panel or interpolates a missing value.
        family_rel_spread = _family_relative_spreads(
            metrics_df,
            cols,
            services,
            base,
            ranker,
            min_baseline_valid=3,
        )

    for col in cols:
        raw = pd.to_numeric(metrics_df[col], errors="coerce")
        vals = raw.astype("float64").to_numpy()
        if np.all(np.isnan(vals)):
            continue
        centre, spread, n_base = _column_stats(vals, base, ranker)
        if n_base < 3:
            continue

        # A perfectly flat baseline makes z undefined, and dividing by a raw
        # epsilon yields scores of ~1e9 that swamp the ranking and print as
        # nonsense on the panel. Floor the spread at a fraction of the series'
        # own magnitude instead: a counter that sits at 0 then ticks to 2 scores
        # highly but comparably to other series, and a series that never moves
        # scores 0.
        finite = vals[np.isfinite(vals)]
        scale = float(np.max(np.abs(finite))) if finite.size else 0.0
        scale = max(scale, abs(centre) if np.isfinite(centre) else 0.0)

        svc, metric = split_service_metric(col, services)
        degenerate = not np.isfinite(spread) or spread <= 0
        if n_base < MIN_BASELINE_VALID or degenerate:
            # Either too few points to trust this column's own spread, or a
            # spread of exactly zero. Both are the same problem -- no usable
            # noise estimate -- and the family's typical noise answers both.
            # Preferred over the magnitude floor below because it compares a
            # series against the instrument it came from rather than against
            # its own scale, which is what makes the resulting z's comparable
            # across the ranking.
            rel = family_rel_spread.get(metric_family(metric))
            if rel is not None and scale > 0:
                floor = FAMILY_FLOOR_FRAC * rel * scale
                if degenerate or spread < floor:
                    spread = floor
            elif n_base < MIN_BASELINE_VALID:
                # Thinly sampled *and* no comparable sibling: nothing to rank it
                # against. Declining beats inventing a score.
                continue
        if not np.isfinite(spread) or spread <= 0:
            spread = SPREAD_FLOOR_FRAC * scale if scale > 0 else np.inf

        dev = np.abs(vals - centre) / spread
        dev = np.where(np.isnan(dev), 0.0, dev)
        peak_idx = int(np.nanargmax(dev))
        score = float(min(dev[peak_idx], Z_CAP))
        if not np.isfinite(score) or score <= 0:
            continue

        out.append(
            ScoredSeries(
                column=col,
                service=svc,
                metric=metric,
                score=score,
                peak_idx=peak_idx,
                peak_value=float(vals[peak_idx]),
                baseline_mean=centre,
                baseline_std=float(spread) if np.isfinite(spread) else 0.0,
                n_valid=int(np.isfinite(vals).sum()),
                baseline_valid=int(n_base),
            )
        )

    out.sort(key=lambda s: s.score, reverse=True)
    return out


_PERCENTILE_SUFFIX = re.compile(r"_p\d{1,3}(_|$)")
_TRAILING_NUM = re.compile(r"[_.]\d+$")


def metric_family(metric: str) -> str:
    """
    Collapse a metric name to its family, so percentile variants group together.

    ``hubble_http_request_duration_p50_seconds``, ``..._p90_seconds`` and
    ``..._p99_seconds`` are three views of one phenomenon. Treating them as
    distinct lets a single incident consume the entire panel budget.
    """
    m = _PERCENTILE_SUFFIX.sub("_", metric)
    m = _TRAILING_NUM.sub("", m)
    return m.strip("_")


def select_panels(
    scored: List[ScoredSeries],
    budget: int,
    ranker: Ranker = "ksigma",
    services: Optional[Sequence[str]] = None,
    max_per_family: int = 0,
    max_per_service: int = 0,
    selector: Selector = "topk",
    coverage_services: int = 0,
) -> List[ScoredSeries]:
    """
    Pick ``budget`` series to draw.

    Three failure modes this guards against, all observed on real cases:

    * One *metric family* consuming every panel. On an AegisLab case, plain
      top-K filled all 12 panels with HTTP latency percentiles of the same
      request path while the actual cause (a MySQL fault) got no panel at all.
      ``max_per_family`` caps that redundancy.
    * One noisy service consuming every panel. ``max_per_service`` caps that.
    * The injected service getting no panel at all, which measurement showed is
      not an edge case: at ``budget=12`` with plain top-K it happens on **34 of
      100** AegisLab cases. ``selector="coverage_first"`` addresses it directly.

    ``coverage_first`` reserves ``coverage_services`` slots for distinct
    services -- the best series of each, services ordered by their best score --
    then spends whatever is left on plain top-K. The two extremes are the
    incumbents: ``coverage_services=0`` is top-K, and ``coverage_services >=
    budget`` is the round-robin that ``ranker="coverage"`` has always done.

    Why it is parameterised rather than fixed at one of those extremes, measured
    over 100 AegisLab cases (share of cases where the injected service gets a
    panel / mean services shown / mean services given >= 2 panels):

        budget 12, top-K          66%   6.0 svc   2.4 with depth
        budget 12, round-robin    82%  12.0 svc   0.0 with depth
        budget 30, top-K          82%  12.1 svc   5.3 with depth
        budget 30, reserve 20     90%  20.3 svc   3.7 with depth
        budget 30, round-robin    96%  30.0 svc   0.0 with depth

    Round-robin maximises coverage and destroys depth completely -- and depth is
    what distinguishes an origin from a victim, since a service failing for its
    own reasons usually moves several of its series at once. The reserve is the
    dial between the two, which is why it is an RQ1 axis and not a constant.

    Note the residual: coverage is bounded by how many services the budget can
    reach, not by the ranking. The injected service is never unrankable (its
    median rank among ~51 services is 3-4, and no alternative service-level
    score -- sum of top 3, mean of top 3, count above z=10, median -- beats the
    current max). So the lever is the budget, not a cleverer score.

    All of these default off, so plain top-K remains the RQ4 ablation baseline.
    """
    if budget <= 0 or not scored:
        return []

    # Back-compat: "coverage" used to be a Ranker value meaning round-robin.
    if ranker == "coverage" and selector == "topk":
        selector, coverage_services = "coverage_first", budget

    if max_per_family or max_per_service:
        kept: List[ScoredSeries] = []
        fam_count: Dict[str, int] = {}
        svc_count: Dict[str, int] = {}
        overflow: List[ScoredSeries] = []
        for s in scored:
            fam = metric_family(s.metric)
            if max_per_family and fam_count.get(fam, 0) >= max_per_family:
                overflow.append(s)
                continue
            if max_per_service and svc_count.get(s.service, 0) >= max_per_service:
                overflow.append(s)
                continue
            kept.append(s)
            fam_count[fam] = fam_count.get(fam, 0) + 1
            svc_count[s.service] = svc_count.get(s.service, 0) + 1
            if len(kept) >= budget and selector != "coverage_first":
                break
        # If the caps starved the budget, refill from what they excluded rather
        # than render a half-empty dashboard.
        if len(kept) < budget:
            kept.extend(overflow[: budget - len(kept)])
        scored = kept

    if selector != "coverage_first":
        return scored[:budget]

    # Reserve slots for distinct services, best series of each. `scored` is
    # already sorted by descending score, so first-seen is that service's best
    # and the services are visited in order of their best series.
    reserve = min(coverage_services if coverage_services > 0 else budget, budget)
    picked: List[ScoredSeries] = []
    seen_services: set = set()
    used: set = set()
    for i, s in enumerate(scored):
        if len(picked) >= reserve:
            break
        if s.service in seen_services:
            continue
        seen_services.add(s.service)
        picked.append(s)
        used.add(i)

    # Spend the remainder on depth: the best still-unused series overall,
    # which is what lets one service show several correlated signals.
    for i, s in enumerate(scored):
        if len(picked) >= budget:
            break
        if i not in used:
            picked.append(s)

    # Draw in score order regardless of how a panel was earned, so [M1] is
    # still the most anomalous panel and the prompt's guide stays true.
    picked.sort(key=lambda s: abs(s.score), reverse=True)
    return picked[:budget]


def service_anomaly_scores(scored: List[ScoredSeries]) -> Dict[str, float]:
    """Per-service anomaly score = its most deviant series. Drives node colouring."""
    agg: Dict[str, float] = {}
    for s in scored:
        agg[s.service] = max(agg.get(s.service, 0.0), s.score)
    return agg


def valid_deviation(
    metrics_df: pd.DataFrame, series: ScoredSeries
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Deviation of a series in sigmas, restricted to the rows it actually has data
    on, plus those rows' positions in the frame.

    Everything that walks along a series -- expanding a fault window, finding a
    first crossing -- has to step between *samples*, not between rows. A column
    populated on 10 of 1064 rows has a NaN on both sides of nearly every sample,
    so a row-space walk stops immediately and reports a one-sample event.
    """
    vals = pd.to_numeric(metrics_df[series.column], errors="coerce").astype("float64").to_numpy()
    idx = np.flatnonzero(np.isfinite(vals))
    if idx.size == 0 or series.baseline_std <= 0:
        return np.empty(0, dtype="float64"), idx
    dev = np.abs(vals[idx] - series.baseline_mean) / series.baseline_std
    dev = np.where(np.isfinite(dev), dev, 0.0)
    return dev, idx


def infer_fault_window(
    metrics_df: pd.DataFrame,
    scored: List[ScoredSeries],
    top_k: int = 3,
) -> Optional[Tuple[float, float]]:
    """
    Estimate the fault window as the sustained excursion around the most
    anomalous series' peak.

    Taking min/max over several series' peaks would shade almost the whole
    canvas whenever two series peak at opposite ends, which tells the model
    nothing. Expanding outward from a single peak while the deviation stays
    elevated gives a band that actually marks the disturbance.

    Derived from telemetry only, never from ground-truth metadata — a window
    computed from the label would paint the answer onto the image.
    """
    if metrics_df is None or metrics_df.empty or not scored:
        return None
    if "timestamp" not in metrics_df.columns:
        return None
    ts = pd.to_numeric(metrics_df["timestamp"], errors="coerce").astype("float64").to_numpy()
    n = len(ts)
    if n < 3:
        return None

    best_span: Optional[Tuple[int, int]] = None
    for s in scored[:top_k]:
        if s.baseline_std <= 0 or not (0 <= s.peak_idx < n):
            continue
        # Walk between consecutive *samples*. In row space a single NaN neighbour
        # halts the expansion, which is why the shaded band was one sample wide
        # on the sparse datasets -- 2.6% of the window, about 8 px, indis-
        # tinguishable from a bar.
        dev, idx = valid_deviation(metrics_df, s)
        if dev.size == 0:
            continue
        peak_pos = int(np.searchsorted(idx, s.peak_idx))
        if peak_pos >= dev.size or idx[peak_pos] != s.peak_idx:
            continue
        peak = dev[peak_pos]
        if peak <= 0:
            continue
        thresh = max(3.0, 0.25 * peak)

        lo = hi = peak_pos
        while lo - 1 >= 0 and dev[lo - 1] >= thresh:
            lo -= 1
        while hi + 1 < dev.size and dev[hi + 1] >= thresh:
            hi += 1
        # Pad in sample steps, then map back to frame positions.
        pad_s = max(1, dev.size // 60)
        lo = int(idx[max(0, lo - pad_s)])
        hi = int(idx[min(dev.size - 1, hi + pad_s)])
        if best_span is None or (hi - lo) > (best_span[1] - best_span[0]):
            best_span = (lo, hi)

    if best_span is None:
        return None
    lo, hi = best_span
    if not (np.isfinite(ts[lo]) and np.isfinite(ts[hi])):
        return None
    return float(ts[lo]), float(ts[hi])

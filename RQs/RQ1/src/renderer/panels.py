"""
Individual dashboard panels. Each draws onto a caller-supplied matplotlib Axes
and returns a manifest entry describing what it drew, so downstream agent tools
can address a panel by id and the leakage test can inspect every string that
reached the image.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from matplotlib.ticker import FuncFormatter

from RQs.RQ1.src.renderer import style
from RQs.RQ1.src.renderer.kpi_select import Z_CAP, ScoredSeries
from RQs.RQ1.src.renderer.onset import pod_to_service as _pod_to_service

# |z| at or above which a series is drawn in the alarm colour.
HOT_Z = 10.0

# Below this many valid samples, draw point markers as well as the line. The
# metric tables are pivots over a union timestamp index, so a column is only
# populated on the timestamps its own scraper wrote: AegisLab's HTTP latency
# series carry 10 valid samples in a 1064-row frame. Without markers the reader
# cannot tell a sparsely-sampled series from a densely-sampled flat one, and the
# line between two samples 400 s apart is interpolation, not measurement.
SPARSE_MARKER_MAX = 200

# The propagation panel's x range is the time axis plus two reserved margins,
# both in units of the time axis: a left gutter holding the service names and a
# right one holding each row's "+2.4m z=41t" readout. Both live inside the data
# limits on purpose. Drawn outside the axes -- as ordinary tick labels and
# annotations -- the names spilled left into the neighbouring metric panels and
# the readouts were clipped off by the figure edge, which is the same defect
# twice: text placed without reference to the box it has to fit in.
ROW_NAME_MARGIN = 1.0
# Sized for the longest readout the panel can produce, "+37.8m z>=999m" at 14
# characters. At 0.5 the clipped-z rows lost their trailing source tag, so a
# reader could not tell a trace measurement from a metric one on exactly the
# rows where the distinction matters most.
ROW_READOUT_MARGIN = 0.62

# Characters the propagation panel's title can hold before the side column runs
# out. Measured, not derived: 56 fit and 61 clipped at prop12's 1568px layout,
# and prop30's side column is narrower still in pixels.
PROP_TITLE_CHARS = 50

# Minimum shaded-band width, as a fraction of the x range. The inferred window is
# frequently one sample wide (~8 px in a 324 px column), which reads as a bar
# rather than an interval. Only the ink is widened; the manifest keeps the
# inferred timestamps, so nothing downstream inherits a cosmetic number.
MIN_BAND_FRAC = 0.01


def _time_unit(ts: np.ndarray) -> float:
    """
    Divisor converting a timestamp column to seconds.

    Metric tables arrive in seconds, milliseconds or nanoseconds depending on
    the dataset; inferring from the window span keeps the x axis in real minutes
    either way.
    """
    finite = ts[np.isfinite(ts)]
    if finite.size < 2:
        return 1.0
    span = float(finite[-1] - finite[0])
    return _unit_for_span(span)


def _unit_for_span(span: float) -> float:
    if not np.isfinite(span) or span <= 0:
        return 1.0
    for scale in (1.0, 1e3, 1e6, 1e9):
        if span / scale < 86_400 * 7:  # no case window is longer than a week
            return scale
    return 1e9


def _shown(entries, total: int) -> str:
    """Say when a table is truncated; absence otherwise reads as evidence."""
    if total and len(entries) < total:
        return f" (top {len(entries)} of {total})"
    return ""


def _display_entity(name: Any, display_labels: Optional[Dict[str, str]]) -> str:
    """Resolve an entity's case-local display label without changing semantics."""
    raw = str(name)
    return str((display_labels or {}).get(raw, raw))


def _elide(s: str, n: int) -> str:
    """Shorten from the middle, keeping the distinguishing tail."""
    s = str(s)
    if len(s) <= n:
        return s
    head = max(1, (n - 1) // 2)
    return s[:head] + "~" + s[-(n - head - 1):]


def _elide_distinct(names: Sequence[str], n: int) -> List[str]:
    """
    Elide to ``n`` characters without collapsing two services into one string.

    ``_elide`` keeps the tail, which is the right default for metric names
    (the percentile or resource is the discriminating part). It is exactly
    wrong for AegisLab service names, where every entry ends in ``-service``
    and the middle is what distinguishes them: ``ts-consign-price-service``
    and ``ts-consign-service`` both render ``ts-cons~-service``, identically,
    and a reader resolving topology node 9 vs node 11 through the legend
    cannot tell which is which. Measured across the 100-case pool, 95 of them
    contained at least one such pair.

    So: elide from the middle, then re-cut any colliding group from the head,
    which preserves the qualifier instead of the shared suffix.
    """
    rendered = [_elide(s, n) for s in names]
    groups: Dict[str, set] = {}
    for src, out in zip(names, rendered):
        groups.setdefault(out, set()).add(src)
    collided = {out for out, srcs in groups.items() if len(srcs) > 1}
    if not collided:
        return rendered
    return [
        (src if len(src) <= n else src[: n - 1] + "~") if out in collided else out
        for src, out in zip(names, rendered)
    ]


def _luminance(rgba) -> float:
    r, g, b = rgba[0], rgba[1], rgba[2]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _relax_overlaps(
    pos: Dict[str, Any], min_sep: Optional[float] = None, iterations: int = 60
) -> Dict[str, Any]:
    """
    Push apart nodes that spring_layout placed on top of each other.

    Overlap is not cosmetic here: an occluded node hides its anomaly shading and
    its number, and which node gets buried is arbitrary, so the highest-signal
    service is as likely to vanish as any other.

    The separation adapts to node count. A fixed 0.30 is comfortable for RE2-OB's
    10 services but exceeds what a [-1,1] canvas can pack for AegisLab's 25,
    where forcing it would flatten the graph into a lattice and destroy the call
    structure the panel exists to show. Overlap is worth fixing; a distorted
    topology is not worth trading for it.
    """
    keys = list(pos)
    if len(keys) < 2:
        return pos
    if min_sep is None:
        # ~2x the drawn node radius (node_size=340pt² spans roughly 0.07 units),
        # capped by what the canvas can actually pack.
        min_sep = min(0.30, 1.5 / np.sqrt(len(keys)))
    p = {k: np.array(pos[k], dtype="float64") for k in keys}
    for _ in range(iterations):
        moved = False
        for i, a in enumerate(keys):
            for b in keys[i + 1 :]:
                d = p[a] - p[b]
                dist = float(np.hypot(*d))
                if dist < 1e-9:
                    # Exactly coincident: separate along a deterministic axis.
                    d = np.array([min_sep / 2, 0.0])
                    dist = min_sep / 2
                if dist < min_sep:
                    push = (min_sep - dist) / 2 * (d / dist)
                    p[a] = p[a] + push
                    p[b] = p[b] - push
                    moved = True
        if not moved:
            break
    return {k: tuple(v) for k, v in p.items()}


def _to_seconds(delta: float) -> float:
    """
    Normalise a timestamp delta to seconds.

    Loaders emit epochs in seconds (RE2, AegisLab) or nanoseconds (some trace
    tables), so a raw subtraction can be off by 1e9 and produce absurd axis
    labels. Infer the unit from the magnitude of a single case's span.
    """
    if not np.isfinite(delta) or delta <= 0:
        return 0.0
    for scale in (1.0, 1e3, 1e6, 1e9):
        if delta / scale < 86_400 * 7:  # a case window is never longer than a week
            return delta / scale
    return delta / 1e9


def _fmt(v: float) -> str:
    """Compact numeric label that stays legible at 7pt."""
    if v is None or not np.isfinite(v):
        return "n/a"
    a = abs(v)
    if a >= 1e9:
        return f"{v/1e9:.1f}G"
    if a >= 1e6:
        return f"{v/1e6:.1f}M"
    if a >= 1e3:
        return f"{v/1e3:.1f}k"
    if a >= 10:
        return f"{v:.0f}"
    if a >= 0.01:
        return f"{v:.2f}"
    return f"{v:.1e}"


def render_metric_panel(
    ax,
    panel_id: str,
    metrics_df: pd.DataFrame,
    series: ScoredSeries,
    fault_window: Optional[Tuple[float, float]] = None,
    normalize: bool = False,
    annotate_extreme: bool = True,
    shade_fault: bool = True,
    title_chars: int = 52,
    time_bins: int = 0,
    relative_manifest: bool = True,
    display_labels: Optional[Dict[str, str]] = None,
    typography: Optional[style.Typography] = None,
) -> Dict[str, Any]:
    """
    One metric time series.

    The printed max-|z| under the title is deliberate: VisualTimeAnomaly found
    that rendering hurts *point* anomalies because a single-sample spike occupies
    one pixel column. Printing the peak deviation keeps that magnitude readable
    even when the pixels lose it.
    """
    typo = typography or style.DEFAULT_TYPOGRAPHY
    ts = pd.to_numeric(metrics_df["timestamp"], errors="coerce").astype("float64").to_numpy()
    vals = pd.to_numeric(metrics_df[series.column], errors="coerce").astype("float64").to_numpy()

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

    plot_vals = vals
    if normalize and series.baseline_std > 0:
        plot_vals = (vals - series.baseline_mean) / series.baseline_std

    # Plot against elapsed time, not row index. Sampling is not uniform in every
    # case (one RE2-OB case carries 1186 rows over 929 s, with a duplicate-
    # timestamp tail), and in index space the shaded fault window then lands
    # nowhere near the excursion it is supposed to mark — the dashboard ends up
    # arguing against its own ground truth. Time is the one coordinate the data,
    # the band and the ticks can all share.
    t0 = ts[0] if len(ts) and np.isfinite(ts[0]) else 0.0
    unit = _time_unit(ts)
    x = (ts - t0) / unit
    # Every panel on this dashboard was selected for being anomalous, so a 3-sigma
    # threshold would paint them all red and the colour would carry no information.
    # Reserve red for severe excursions so the split is meaningful.
    is_hot = abs(series.signed_z) >= HOT_Z
    # Drop the gaps rather than handing them to matplotlib, which breaks the line
    # at every NaN. These frames are pivots over a union timestamp index, so a
    # column populated on 10 of 1064 rows became 10 zero-length segments: a panel
    # with no visible data at all, on the dataset the project screens against.
    valid = np.isfinite(x) & np.isfinite(plot_vals)
    n_valid = int(valid.sum())
    ax.plot(
        x[valid],
        plot_vals[valid],
        lw=0.9,
        color=style.ANOMALY_LINE if is_hot else style.NORMAL_LINE,
        solid_capstyle="round",
        # Where samples are scarce, show where they actually are: the segment
        # joining two samples minutes apart is interpolation, and a reader
        # judging an onset time needs to know which is which.
        marker="." if 0 < n_valid < SPARSE_MARKER_MAX else None,
        ms=2.4,
        markerfacecolor=style.ANOMALY_LINE if is_hot else style.NORMAL_LINE,
        markeredgewidth=0,
    )

    if shade_fault and fault_window is not None and len(ts) > 1:
        lo = (fault_window[0] - t0) / unit
        hi = (fault_window[1] - t0) / unit
        if hi > lo:
            # Widen the ink, never the number: an interval thinner than the eye
            # resolves reads as a bar and stops looking like a span of time.
            span = float(x[valid][-1] - x[valid][0]) if n_valid > 1 else 0.0
            floor = MIN_BAND_FRAC * span
            if floor > 0 and (hi - lo) < floor:
                mid = (lo + hi) / 2
                lo_draw, hi_draw = mid - floor / 2, mid + floor / 2
            else:
                lo_draw, hi_draw = lo, hi
            ax.axvspan(
                lo_draw, hi_draw, color=style.FAULT_SHADE, alpha=style.FAULT_SHADE_ALPHA, lw=0
            )
            # A short window can shade fewer pixels than the eye resolves, so
            # mark its edges explicitly rather than relying on the fill alone.
            for edge in (lo, hi):
                ax.axvline(edge, color=style.ANOMALY_LINE, lw=0.5, alpha=0.55)

    if len(plot_vals) and np.isfinite(plot_vals).any():
        deviations = np.abs(plot_vals - series.baseline_mean)
        peak_plot_idx = int(np.nanargmax(deviations))
    else:
        peak_plot_idx = -1
    if annotate_extreme and 0 <= peak_plot_idx < len(plot_vals):
        py = plot_vals[peak_plot_idx]
        if np.isfinite(py):
            ax.plot([x[peak_plot_idx]], [py], marker="v", ms=3.0, color=style.ANOMALY_LINE)

    # Budget the title to the column it is drawn in. These were fixed at 22 and
    # 26 characters, sized for the 3-column 1568px grid; at 5 columns the same
    # string overruns into the neighbouring panel's title, and at the row end
    # into the log/trace table headers -- "..._p99_seco" + "Log signals" merging
    # into one garbled line. AegisLab's OTel names
    # (hubble_http_request_duration_p50_seconds) are long enough that this was
    # close to the median panel, not an edge case. Same failure as the legend
    # column: a character budget that does not know how wide its column is.
    prefix = f"[{panel_id}] "
    body = max(12, title_chars - len(prefix))
    # Metric names carry the discriminating detail (which percentile, which
    # resource), but the service name is what the task is actually asking
    # about, so give it the larger share when space is tight.
    svc_chars = max(8, int(body * 0.45))
    metric_chars = max(8, body - svc_chars - 3)  # 3 for the " · " separator
    displayed_service = _display_entity(series.service, display_labels)
    rendered_service = _elide(displayed_service, svc_chars)
    rendered_metric = _elide(series.metric, metric_chars)
    ax.set_title(
        f"{prefix}{rendered_service} · {rendered_metric}",
        fontsize=typo.panel_title,
        color=style.TEXT,
        pad=2.0,
        loc="left",
    )
    sign = "+" if series.signed_z >= 0 else "-"
    if abs(series.signed_z) >= Z_CAP:
        # Do not print the clip sentinel as if it were a measurement: a flat
        # baseline makes z undefined, and "999z" outranking a genuine 400z
        # excursion is an artefact the model should be able to discount.
        zpart = f"peak {sign}>={Z_CAP:.0f}z (flat baseline)"
    else:
        zpart = f"peak {sign}{abs(series.signed_z):.1f}z"
    sub = f"{zpart}   {_fmt(series.baseline_mean)} -> {_fmt(series.peak_value)}"
    # Below the axes, not inside them: at 7pt an in-axes annotation sits on top
    # of the data it is describing.
    ax.text(
        0.0,
        -0.30,
        sub,
        transform=ax.transAxes,
        fontsize=typo.annotation,
        color=style.MUTED,
        va="top",
        ha="left",
    )

    ax.grid(True, alpha=0.5)
    ax.margins(x=0.01)
    # Relative-minute ticks read off the same time coordinate as the data, so
    # they stay correct when sampling is uneven.
    if len(x) > 1 and np.isfinite(x[-1]) and x[-1] > 0:
        ticks = [0.0, x[-1] / 2, x[-1]]
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{t/60:.0f}m" for t in ticks], fontsize=typo.tick)
    else:
        ax.set_xticks([])
    # Large-magnitude series otherwise carry their scale in a 7pt "1e7" offset
    # label above the axis, which is easy to drop when reading the values.
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: _fmt(v)))
    ax.tick_params(axis="both", length=2, pad=1, labelsize=typo.tick)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    time_range = None
    if len(ts):
        time_range = [float(x[0]), float(x[-1])] if relative_manifest else [float(ts[0]), float(ts[-1])]
    return {
        "panel_id": panel_id,
        "kind": "metric",
        "service": displayed_service,
        "rendered_service": rendered_service,
        "metric": series.metric,
        "rendered_metric": rendered_metric,
        "column": (
            f"{displayed_service}_{series.metric}"
            if display_labels
            else series.column
        ),
        "signed_z": round(series.signed_z, 3),
        "score": round(series.score, 3),
        "peak_value": series.peak_value,
        "baseline_mean": series.baseline_mean,
        "baseline_std": series.baseline_std,
        "printed_summary": {
            "signed_z": zpart,
            "baseline": _fmt(series.baseline_mean),
            "peak": _fmt(series.peak_value),
        },
        "normalized": bool(normalize),
        "n_samples": n_valid,
        "time_range_rel_s": time_range,
        "plot_x_rel_s": x.tolist(),
        "fault_window_plot_x_rel_s": (
            [(float(fault_window[0]) - t0) / unit,
             (float(fault_window[1]) - t0) / unit]
            if fault_window is not None else None
        ),
        "time_bin_centers_rel_s": bin_centers_s.tolist() if bin_centers_s is not None else None,
        "values": bin_values.tolist() if bin_values is not None else None,
        "observed_counts": bin_counts.tolist() if bin_counts is not None else None,
    }


def render_topology_panel(
    ax,
    panel_id: str,
    graph,
    anomaly_scores: Dict[str, float],
    label_mode: str = "numbered",
    colored: bool = True,
    max_nodes: int = 25,
    typography: Optional[style.Typography] = None,
) -> Dict[str, Any]:
    """
    Service dependency graph, nodes shaded by anomaly score.

    Dense topologies (AegisLab Train-Ticket, 40+ services) are truncated to the
    most anomalous subgraph with an explicit "N more hidden" note — silently
    dropping nodes would let the model conclude a service is absent when it was
    merely cropped.
    """
    import networkx as nx

    typo = typography or style.DEFAULT_TYPOGRAPHY

    nodes = list(graph.nodes())
    hidden = 0
    if len(nodes) > max_nodes:
        ranked = sorted(nodes, key=lambda n: anomaly_scores.get(n, 0.0), reverse=True)
        keep = set(ranked[:max_nodes])
        hidden = len(nodes) - len(keep)
        graph = graph.subgraph(keep).copy()
        nodes = list(graph.nodes())

    nodes = sorted(nodes)
    # Deterministic layout: spring_layout with a fixed seed and a stable node
    # ordering, so the same topology always draws identically (golden tests).
    ordered = nx.DiGraph()
    ordered.add_nodes_from(nodes)
    ordered.add_edges_from(sorted(graph.edges()))
    pos = _relax_overlaps(nx.spring_layout(ordered, seed=17, k=0.9, iterations=120))

    raw = np.array([anomaly_scores.get(n, 0.0) for n in nodes], dtype="float64")
    # Rank, not magnitude. Anomaly scores span orders of magnitude, and both a
    # linear scale (everything but the worst renders white) and log1p (a cluster
    # of high scores all saturate to the same maroon) stop discriminating.
    # Ranking guarantees the ramp is used evenly however the scores are spread.
    order = np.argsort(np.argsort(raw))
    scores = order / max(len(raw) - 1, 1)

    labels = {n: str(i + 1) for i, n in enumerate(nodes)}

    nx.draw_networkx_edges(
        ordered,
        pos,
        ax=ax,
        edge_color="#9aa0a6",
        width=0.7,
        arrows=True,
        arrowsize=7,
        node_size=340,
    )
    # Draw least-anomalous first so the node that matters most ends up on top.
    # Alphabetical draw order meant the true root cause was occluded by an
    # unrelated neighbour in most cases.
    draw_order = list(np.argsort(raw))
    cmap = __import__("matplotlib").colormaps[style.NODE_CMAP]
    for idx in draw_order:
        n = nodes[idx]
        face = cmap(scores[idx]) if colored else "#cfd8dc"
        collection = nx.draw_networkx_nodes(
            ordered,
            pos,
            ax=ax,
            nodelist=[n],
            node_color=[face],
            node_size=340,
            edgecolors=style.NODE_EDGE,
            linewidths=0.6,
        )
        # Nodes near the axes edge are otherwise sliced flat by the frame.
        collection.set_clip_on(False)
        # Dark fills need light text; #111 on a saturated maroon is unreadable.
        lum = _luminance(face) if colored else 1.0
        ax.text(
            pos[n][0],
            pos[n][1],
            labels[n] if label_mode == "numbered" else n,
            fontsize=typo.tick if label_mode == "numbered" else max(style.MIN_FONT_PT, typo.tick - 1.0),
            color="#ffffff" if lum < 0.5 else "#111111",
            ha="center",
            va="center",
            zorder=10,
            clip_on=False,
        )
    # set_axis_off leaves the limits at node *centres*, clipping the outermost
    # circles even when there is empty canvas beyond them.
    ax.margins(0.18)

    title = "Service call graph (A -> B: A calls B)"
    if colored:
        title += " · shade = anomaly"
    ax.set_title(title, fontsize=typo.panel_title, color=style.TEXT, loc="left", pad=3)
    ax.set_axis_off()
    if hidden:
        # Reserve an empty band at the bottom for the caption. The spring layout
        # regularly parks a node on the lower frame, and the caption was being
        # drawn straight through it in 8 of 8 sampled AegisLab cases -- the word
        # "anomalous" printed across a node circle. Extending the data ylim
        # downward pushes every node up in axes-fraction terms without moving
        # the axes box or rescaling the graph.
        y0, y1 = ax.get_ylim()
        ax.set_ylim(y0 - 0.16 * (y1 - y0), y1)
        ax.text(
            0.99,
            0.01,
            f"{hidden} less-anomalous services hidden",
            transform=ax.transAxes,
            fontsize=typo.annotation,
            color=style.MUTED,
            ha="right",
            va="bottom",
        )

    return {
        "panel_id": panel_id,
        "kind": "topology",
        "label_mode": label_mode,
        "node_order": nodes,
        "node_labels": labels,
        "hidden_nodes": hidden,
        "anomaly_scores": {n: round(anomaly_scores.get(n, 0.0), 3) for n in nodes},
    }


def render_propagation_panel(
    ax,
    panel_id: str,
    onsets: Dict[str, Any],
    graph,
    anomaly_scores: Dict[str, float],
    full_range: Optional[Tuple[float, float]] = None,
    fault_window: Optional[Tuple[float, float]] = None,
    max_rows: int = 14,
    row_chars: int = 26,
    max_edges: int = 12,
    relative_manifest: bool = True,
    display_labels: Optional[Dict[str, str]] = None,
    typography: Optional[style.Typography] = None,
) -> Dict[str, Any]:
    """
    Anomaly propagation: which service went bad first, and along which call edges.

    Rows are services ordered by onset time, earliest at the top, drawn against
    the same elapsed-minutes axis as the metric panels. A marker sits at the
    onset and a bar runs from there to the end of the window; arrows in the left
    gutter connect a caller to a callee it depends on.

    Why rows and not a graph drawing: the existing topology panel is a spring
    layout of up to 25 nodes, and on AegisLab's 104-service topology it renders
    as a hairball a reader cannot trace an edge through. Ordered rows of labelled
    text are the one structure this project has evidence VLMs read reliably (the
    legend and log tables), and ordering *is* the finding here, so the layout and
    the message agree.

    Note the direction of the story: A -> B means A calls B, so latency
    propagates from B back to A. An origin is therefore early and usually
    downstream, which is exactly what magnitude-ranked views hide -- a saturated
    database moves its own metrics far less than the services queued behind it.
    """
    typo = typography or style.DEFAULT_TYPOGRAPHY

    # Select by severity, display by onset.
    #
    # Selecting by earliest onset was the original design, on the reasoning that
    # magnitude truncation discards a quiet early origin. Measured on 30 AegisLab
    # cases it is the reverse that holds: ranking the same services by magnitude
    # puts the injected one at median rank 2.0 against onset's 5.5 (top-3 79% vs
    # 42%, worse on 15 of 20 discordant pairs, Wilcoxon p=0.014). Onset is not
    # the better locator here, so it must not be the filter -- filtering on it
    # dropped the true cause out of the panel entirely on 6 of 30 cases.
    #
    # It remains the better *narrative* axis, and it is information the severity
    # ranking does not carry, so it orders the rows that severity chose. The
    # reader gets a set likely to contain the cause plus the sequence it moved in.
    # Severity here means the same thing it means everywhere else on the
    # dashboard -- the per-service anomaly score behind the panel ranking and the
    # legend's z -- not the onset-derived z. Ranking on the latter quietly
    # selected a different set: a service can deviate enormously and still have a
    # weak or undetectable onset (it emits no spans, or its crossing fails the
    # stricter metric rule), and on the AIOPS cases the single worst-deviating
    # service was dropped for exactly that reason while fourteen milder ones
    # filled the rows. That made the panel strictly worse than the Service index
    # it replaces.
    proj: Dict[str, float] = {}
    for raw, sc in sorted(anomaly_scores.items()):
        key = _pod_to_service(raw)
        proj[key] = max(proj.get(key, 0.0), float(sc))

    def _severity(o) -> float:
        return max(proj.get(o.service, 0.0), float(getattr(o, "peak_z", 0.0)))

    candidates = [o for o in onsets.values() if _severity(o) > 0]
    kept = sorted(candidates, key=lambda o: (-_severity(o), o.service))[:max_rows]
    n_detected = len(candidates)
    # Rows with an onset are ordered by it; those without have no place on the
    # timeline, so they sit at the bottom, named and scored but explicitly undated.
    rows_all = sorted(
        kept,
        key=lambda o: (
            o.onset_ts is None,
            o.onset_ts if o.onset_ts is not None else 0.0,
            -_severity(o),
            o.service,
        ),
    )
    mode = "onset"
    if not any(o.onset_ts is not None for o in rows_all):
        rows_all = []
    if not rows_all:
        # Nothing crossed anywhere: cases with no traces and quiet metrics. Say
        # so and fall back to magnitude, rather than drawing an empty panel that
        # reads as "no services were affected".
        mode = "rank_fallback"
        rows_all = sorted(
            (o for o in onsets.values() if anomaly_scores.get(o.service, 0.0) > 0),
            key=lambda o: (-anomaly_scores.get(o.service, 0.0), o.service),
        )[:max_rows]
        n_detected = len(rows_all)

    shown = rows_all
    omitted = max(0, n_detected - len(shown))

    if not shown:
        ax.text(
            0.5, 0.5, "no anomaly onset detectable", transform=ax.transAxes,
            fontsize=typo.annotation, color=style.MUTED, ha="center", va="center",
        )
        ax.set_title("Anomaly propagation", fontsize=typo.panel_title,
                     color=style.TEXT, loc="left", pad=3)
        ax.set_axis_off()
        return {
            "panel_id": panel_id, "kind": "propagation", "mode": "empty",
            "rows": [], "omitted_services": 0, "edges": [], "omitted_edges": 0,
        }

    # Time axis shared with the metric panels: elapsed from window start.
    t0 = full_range[0] if full_range else min(o.onset_ts for o in shown if o.onset_ts)
    t1 = full_range[1] if full_range else max(o.onset_ts for o in shown if o.onset_ts)
    span = max(float(t1) - float(t0), 1.0)
    unit = _unit_for_span(span)
    x_max = span / unit

    names = [_display_entity(o.service, display_labels) for o in shown]
    labels = _elide_distinct(names, row_chars)
    row_y = {o.service: len(shown) - 1 - i for i, o in enumerate(shown)}

    # Rank within the panel, matching the topology panel's semantics: colour
    # says "how severe relative to the others here", never an absolute z.
    sev = np.array([o.peak_z for o in shown], dtype="float64")
    rank = np.argsort(np.argsort(sev)) / max(len(sev) - 1, 1)
    cmap = __import__("matplotlib").colormaps[style.NODE_CMAP]

    if fault_window is not None:
        lo = (float(fault_window[0]) - float(t0)) / unit
        hi = (float(fault_window[1]) - float(t0)) / unit
        if hi > lo:
            ax.axvspan(lo, hi, color=style.FAULT_SHADE, alpha=style.FAULT_SHADE_ALPHA, lw=0,
                       zorder=0)

    for i, o in enumerate(shown):
        y = row_y[o.service]
        face = cmap(0.15 + 0.85 * rank[i])
        if o.onset_ts is not None:
            x = (float(o.onset_ts) - float(t0)) / unit
            # Bar from onset to the end of the window: the fault does not stop
            # at its onset, and a bare dot invites reading it as an instant.
            ax.plot([x, x_max], [y, y], lw=2.6, color=face, solid_capstyle="butt",
                    zorder=3, alpha=0.85)
            ax.plot([x], [y], marker="o", ms=4.2, color=face,
                    markeredgecolor=style.NODE_EDGE, markeredgewidth=0.5, zorder=4)
        else:
            ax.plot([0, x_max], [y, y], lw=1.0, color="#cfd8dc", zorder=2)

    # Call edges between shown rows. An edge whose ends onset in the same bin
    # depicts no step in time, so those go last: with the budget spent on them
    # the panel drew a dozen arcs that all said "these two are related" and none
    # that said "this one moved first".
    edge_pairs: List[Tuple[str, str, float]] = []
    if graph is not None:
        for a, b in sorted(graph.edges()):
            if a in row_y and b in row_y and a != b:
                oa, ob = onsets.get(a), onsets.get(b)
                if oa is None or ob is None:
                    continue
                if oa.onset_ts is None or ob.onset_ts is None:
                    continue
                edge_pairs.append((a, b, abs(float(oa.onset_ts) - float(ob.onset_ts))))
    # Only edges whose ends onset at different times get drawn. Same-bin edges
    # are the majority on a dense case and they all start and end at the same x,
    # so they stack into one unreadable knot -- a vision review found eight of
    # them crossing inside a 130px band, individually traceable only at 4x zoom.
    # They also carry the least: an arrow that depicts no step in time says only
    # "these two are connected", which the row set already implies. The
    # relationships stay in the manifest and the text arm regardless.
    stepped = [e for e in edge_pairs if e[2] > 0]
    stepped.sort(key=lambda e: (e[2], e[0], e[1]))
    drawn_edges = stepped[:max_edges]
    omitted_edges = len(edge_pairs) - len(drawn_edges)

    for a, b, _gap in drawn_edges:
        ya, yb = row_y[a], row_y[b]
        xa = (float(onsets[a].onset_ts) - float(t0)) / unit
        xb = (float(onsets[b].onset_ts) - float(t0)) / unit
        # Drawn from callee to caller, the direction the symptom travels.
        ax.annotate(
            "",
            xy=(xa, ya), xytext=(xb, yb),
            arrowprops=dict(arrowstyle="->", color="#7a8a99", lw=0.7,
                            connectionstyle="arc3,rad=0.22", shrinkA=3, shrinkB=3),
            zorder=1,
        )

    ax.set_yticks([])
    for i, o in enumerate(shown):
        ax.text(
            -ROW_NAME_MARGIN * x_max, row_y[o.service], f"{i+1}. {labels[i]}",
            fontsize=typo.tick, color=style.TEXT, va="center", ha="left",
        )
    ax.set_xlim(-ROW_NAME_MARGIN * x_max, (1.0 + ROW_READOUT_MARGIN) * x_max)
    ax.set_ylim(-0.8, len(shown) - 0.2)

    if x_max > 0:
        ticks = [0.0, x_max / 2, x_max]
        ax.set_xticks(ticks)
        ax.set_xticklabels([f"{t/60:.0f}m" for t in ticks], fontsize=typo.tick)
    ax.tick_params(axis="x", length=2, pad=1, labelsize=typo.tick)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.grid(True, axis="x", alpha=0.5)

    # Onset time and severity printed per row: colour and position both survive
    # rasterisation badly, and the model is asked to reason about order.
    for i, o in enumerate(shown):
        y = row_y[o.service]
        if o.onset_ts is not None:
            rel = (float(o.onset_ts) - float(t0)) / unit / 60.0
            tag = {"trace": "T", "metric": "M"}.get(getattr(o, "source", ""), "")
            # Never print the clip sentinel as a measurement (DD-10): a flat
            # baseline makes z undefined, and "999" outranking a real 400 is an
            # artefact the reader should be able to discount.
            # The side column's right margin is intentionally narrow. Keep the
            # row readout compact enough to fit at the uniform 9.5pt detail
            # size; the caption below defines these numbers as z scores.
            zpart = f"≥{Z_CAP:.0f}" if o.peak_z >= Z_CAP else f"{o.peak_z:.0f}"
            rel_text = f"{rel:.1f}".rstrip("0").rstrip(".")
            txt = f"{rel_text}m {zpart}{tag}"
        else:
            txt = "no onset"
        ax.text(
            x_max * 1.04, y, txt,
            fontsize=typo.annotation, color=style.MUTED, va="center", ha="left",
        )

    # Short by necessity: this title is drawn from the axes' left edge and the
    # side column runs out at roughly 56 characters (narrower still at prop30's
    # 5-column grid), so a longer one is silently cut off at the figure edge.
    # The selection criterion lives in the omitted-services caption instead.
    title = "Anomaly propagation — earliest onset first"
    if mode == "rank_fallback":
        title = "Anomaly propagation — by anomaly rank"
    ax.set_title(
        _elide(title, PROP_TITLE_CHARS),
        fontsize=typo.panel_title, color=style.TEXT, loc="left", pad=3,
    )

    # A trace-derived z and a metric-derived z measure different instruments and
    # are not on one scale; the suffix says which, and this says why it matters.
    notes = ["readout: onset · z + source", "T=trace, M=metric; z not comparable"]
    omissions = []
    if omitted:
        omissions.append(f"{omitted} less-anomalous omitted")
    if omitted_edges:
        omissions.append(f"{omitted_edges} edges not drawn")
    if omissions:
        # A second short line stays inside the side column. Joining every note
        # onto one line reached the figure's right edge on 12/30 RQ1b5 cases;
        # the clipping was unrelated to entity names but still made those
        # dashboards look malformed.
        notes.append(" · ".join(omissions))
    if notes:
        # Below the axes: an in-axes note lands on the bottom row's bar.
        ax.text(
            0.0, -0.16, "\n".join(notes), transform=ax.transAxes,
            fontsize=typo.annotation, color=style.MUTED, va="top", ha="left",
        )

    manifest_rows = []
    for i, o in enumerate(shown):
        if o.onset_ts is not None:
            rel = (float(o.onset_ts) - float(t0)) / unit / 60.0
            onset_display = f"{rel:.1f}".rstrip("0").rstrip(".") + "m"
            severity_display = f"≥{Z_CAP:.0f}" if o.peak_z >= Z_CAP else f"{o.peak_z:.0f}"
            source_display = {"trace": "T", "metric": "M"}.get(
                getattr(o, "source", ""), "none"
            )
        else:
            onset_display, severity_display, source_display = "no onset", "none", "none"
        manifest_rows.append({
            "rank": i + 1,
            "service": _display_entity(o.service, display_labels),
            "rendered_service": labels[i],
            "onset_rel_min": round((float(o.onset_ts) - float(t0)) / unit / 60.0, 2)
            if o.onset_ts is not None else None,
            "peak_z": round(float(o.peak_z), 3),
            "source": getattr(o, "source", "none"),
            "onset_display": onset_display,
            "severity_display": severity_display,
            "source_display": source_display,
            "callers": [
                _display_entity(name, display_labels)
                for name in sorted(graph.predecessors(o.service))
            ] if graph is not None and o.service in graph else [],
            "callees": [
                _display_entity(name, display_labels)
                for name in sorted(graph.successors(o.service))
            ] if graph is not None and o.service in graph else [],
        })

    return {
        "panel_id": panel_id,
        "kind": "propagation",
        "mode": mode,
        "rows": manifest_rows,
        "omitted_services": int(omitted),
        "edges": [
            [
                _display_entity(a, display_labels),
                _display_entity(b, display_labels),
            ]
            for a, b, _ in drawn_edges
        ],
        "omitted_edges": int(omitted_edges),
    }


def render_legend_panel(
    ax,
    panel_id: str,
    nodes: Sequence[str],
    anomaly_scores: Dict[str, float],
    row_chars: int = 26,
    typography: Optional[style.Typography] = None,
) -> Dict[str, Any]:
    """
    Number → service-name table. Makes numbered topology labels resolvable.

    "Resolvable" is the whole job: if two nodes render the same name the
    topology panel stops being interpretable, which is one of the few things
    the dashboard offers that a serialised metric table does not.
    """
    typo = typography or style.DEFAULT_TYPOGRAPHY
    ax.set_axis_off()
    ax.set_title("Service index", fontsize=typo.panel_title, color=style.TEXT, loc="left", pad=3)
    # Budget the whole rendered row, not just the name. Eliding the name and
    # *then* appending " z=NNN" pushed the score past the panel edge for long
    # service names -- on one case the ground-truth rows rendered as "z=" with
    # no digits at all, and on another two columns collided so that "z=8" and
    # "15." read as the single wrong number "z=43915".
    ncol = 2 if len(nodes) > 12 else 1
    row_width = row_chars if ncol == 2 else int(row_chars * 1.3)
    prefixes = [f"{i+1:>2}. " for i in range(len(nodes))]
    # Clipped at Z_CAP upstream, but guard the width anyway: an unclipped value
    # would silently re-open the overflow this fixes.
    suffixes = [f" z={min(anomaly_scores.get(n, 0.0), 9999.0):.0f}" for n in nodes]
    name_width = max(
        8,
        row_width - max((len(p) for p in prefixes), default=4)
        - max((len(s) for s in suffixes), default=6),
    )
    names = _elide_distinct(list(nodes), name_width)
    rows = [p + nm + s for p, nm, s in zip(prefixes, names, suffixes)]
    # Any residual ambiguity is recorded rather than hidden: two nodes sharing a
    # rendered name is a defect in the panel's only purpose, and it should be
    # auditable from the manifest instead of needing another vision review.
    ambiguous = sorted(
        {nm for nm in names if names.count(nm) > 1}
    )
    per = (len(rows) + ncol - 1) // ncol if ncol > 1 else len(rows)
    for c in range(ncol):
        chunk = rows[c * per : (c + 1) * per]
        ax.text(
            0.01 + c * 0.52,
            0.98,
            "\n".join(chunk),
            transform=ax.transAxes,
            fontsize=typo.table if ncol == 1 else max(style.MIN_FONT_PT, typo.table - 0.7),
            color=style.TEXT,
            va="top",
            ha="left",
            family="DejaVu Sans Mono",
            linespacing=1.3,
        )
    return {
        "panel_id": panel_id,
        "kind": "legend",
        "entries": list(nodes),
        "rendered_names": names,
        "ambiguous_names": ambiguous,
    }


ERROR_PATTERN = r"error|exception|fail|timeout|refused|fatal|panic|denied|unavailable"


TIME_COLUMNS = ("timestamp", "startTime", "startTimeMillis", "start_time", "time")
UNIT_SCALES = (1.0, 1e3, 1e6, 1e9)


def resolve_time_seconds(
    df: pd.DataFrame, reference: Optional[Tuple[float, float]]
) -> Optional[pd.Series]:
    """
    Get a log/trace table's event time in the same units as the metric axis.

    Neither the column nor the unit is consistent across datasets: RE2-OB traces
    leave ``timestamp`` entirely NaN and keep microseconds in ``startTime``,
    while its logs use nanosecond ``timestamp``. Rather than guessing from
    magnitude, try each candidate column at each unit scale and keep whichever
    lands inside the known metric window — a wrong guess then fails loudly as
    "no overlap" instead of silently emptying the during-fault group.
    """
    if df is None or df.empty or reference is None:
        return None
    ref_lo, ref_hi = reference
    span = max(ref_hi - ref_lo, 1.0)
    best: Optional[pd.Series] = None
    best_frac = 0.0
    for col in TIME_COLUMNS:
        if col not in df.columns:
            continue
        raw = pd.to_numeric(df[col], errors="coerce")
        if not raw.notna().any():
            continue
        for scale in UNIT_SCALES:
            cand = raw / scale
            frac = float(((cand >= ref_lo - span) & (cand <= ref_hi + span)).mean())
            if frac > best_frac:
                best, best_frac = cand, frac
        if best_frac > 0.5:
            break
    return best if best_frac > 0.1 else None


def _split_by_window(
    df: pd.DataFrame,
    fault_window: Optional[Tuple[float, float]],
    full_range: Optional[Tuple[float, float]] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Partition rows into (pre-fault, in-fault) using the estimated window."""
    empty = df.iloc[0:0] if df is not None else df
    if df is None or df.empty or fault_window is None:
        return df, empty
    ts = resolve_time_seconds(df, full_range or fault_window)
    if ts is None:
        return df, empty
    inside = ((ts >= fault_window[0]) & (ts <= fault_window[1])).fillna(False)
    return df.loc[~inside], df.loc[inside]


def _rate_table(
    pre: pd.DataFrame, during: pd.DataFrame, key: str, top_n: int
) -> List[Dict[str, Any]]:
    """Per-entity volume before vs during the fault window, ranked by shift."""
    if pre is None or key not in getattr(pre, "columns", []):
        return []
    a = pre[key].value_counts()
    b = during[key].value_counts() if during is not None and not during.empty else a.iloc[0:0]
    entities = sorted(set(a.index) | set(b.index))
    rows = []
    for e in entities:
        n_pre, n_dur = int(a.get(e, 0)), int(b.get(e, 0))
        # Rates, since the two windows differ in length.
        rows.append({"service": str(e), "n_pre": n_pre, "n_during": n_dur})
    for r in rows:
        base = max(r["n_pre"], 1)
        r["change_pct"] = round((r["n_during"] - r["n_pre"]) / base * 100, 1)
    rows.sort(key=lambda r: abs(r["change_pct"]), reverse=True)
    return rows[:top_n]


def render_log_panel(
    ax,
    panel_id: str,
    logs_df: pd.DataFrame,
    fault_window: Optional[Tuple[float, float]] = None,
    full_range: Optional[Tuple[float, float]] = None,
    top_n: int = 8,
    row_chars: int = 24,
    compact_columns: bool = False,
    display_labels: Optional[Dict[str, str]] = None,
    typography: Optional[style.Typography] = None,
) -> Dict[str, Any]:
    """
    Log evidence as a text table: error counts if the corpus has any, otherwise
    the shift in log volume per service.

    Several datasets (RE2-OB among them) emit purely informational logs with no
    error strings at all, so an error-only panel would be permanently blank.
    Volume shift is the signal that actually exists there, and it generalises:
    a service that stops logging is as diagnostic as one that starts erroring.

    Log text is discrete high-entropy data — what VisualTimeAnomaly found images
    handle worst — so this is a compact table, and the hybrid condition also
    passes it as prompt text.
    """
    typo = typography or style.DEFAULT_TYPOGRAPHY
    ax.set_axis_off()

    entries: List[Dict[str, Any]] = []
    mode = "none"
    n_services = 0
    if logs_df is not None and not logs_df.empty and "message" in logs_df.columns:
        svc_col = "container_name" if "container_name" in logs_df.columns else None
        if svc_col:
            n_services = int(logs_df[svc_col].nunique())
        msg = logs_df["message"].astype(str)
        err_mask = msg.str.contains(ERROR_PATTERN, case=False, regex=True, na=False)
        if svc_col and bool(err_mask.any()):
            mode = "errors"
            counts = logs_df.loc[err_mask, svc_col].value_counts()
            totals = logs_df[svc_col].value_counts()
            for svc, cnt in counts.head(top_n).items():
                total = int(totals.get(svc, 0))
                entries.append(
                    {
                        "service": str(svc),
                        "error_logs": int(cnt),
                        "total_logs": total,
                        "error_pct": round(cnt / total * 100, 2) if total else 0.0,
                    }
                )
        elif svc_col:
            mode = "volume"
            pre, during = _split_by_window(logs_df, fault_window, full_range)
            entries = _rate_table(pre, during, svc_col, top_n)

    displayed_names = []
    for entry in entries:
        entry["service"] = _display_entity(entry["service"], display_labels)
        displayed_names.append(entry["service"])
    rendered_names = _elide_distinct(displayed_names, row_chars)
    for entry, rendered in zip(entries, rendered_names):
        entry["rendered_service"] = rendered

    if mode == "errors":
        title = f"Log signals — error lines by service{_shown(entries, n_services)}"
        widths = (6, 7, 6) if compact_columns else (7, 9, 7)
        lines = [
            f"{'service':<{row_chars}}{'err':>{widths[0]}}"
            f"{'total':>{widths[1]}}{'err%':>{widths[2]}}"
        ]
        for e in entries:
            lines.append(
                f"{e['rendered_service']:<{row_chars}}{e['error_logs']:>{widths[0]}}"
                f"{e['total_logs']:>{widths[1]}}{e['error_pct']:>{widths[2]}.1f}"
            )
        body = "\n".join(lines)
    elif mode == "volume" and entries:
        title = f"Log signals — volume shift, no error lines{_shown(entries, n_services)}"
        widths = (6, 7, 6) if compact_columns else (8, 8, 8)
        lines = [
            f"{'service':<{row_chars}}{'pre':>{widths[0]}}"
            f"{'during':>{widths[1]}}{'chg%':>{widths[2]}}"
        ]
        for e in entries:
            lines.append(
                f"{e['rendered_service']:<{row_chars}}{e['n_pre']:>{widths[0]}}"
                f"{e['n_during']:>{widths[1]}}{e['change_pct']:>{widths[2]}.1f}"
            )
        body = "\n".join(lines)
    else:
        title = "Log signals"
        body = "no log data available"

    ax.set_title(title, fontsize=typo.panel_title, color=style.TEXT, loc="left", pad=3)
    ax.text(
        0.01,
        0.95,
        body,
        transform=ax.transAxes,
        fontsize=typo.table,
        color=style.TEXT,
        va="top",
        ha="left",
        family="DejaVu Sans Mono",
        linespacing=1.4,
    )
    return {
        "panel_id": panel_id,
        "kind": "logs",
        "mode": mode,
        "entries": entries,
        "service_count": n_services,
        "omitted_services": max(0, n_services - len(entries)),
    }


def render_trace_panel(
    ax,
    panel_id: str,
    traces_df: pd.DataFrame,
    fault_window: Optional[Tuple[float, float]] = None,
    full_range: Optional[Tuple[float, float]] = None,
    top_n: int = 8,
    row_chars: int = 22,
    compact_columns: bool = False,
    display_labels: Optional[Dict[str, str]] = None,
    typography: Optional[style.Typography] = None,
) -> Dict[str, Any]:
    """
    Per-service span latency before vs during the fault window.

    Absolute p95 mostly reflects which service is intrinsically slow; the delta
    reflects what the incident did, which is the question being asked.
    """
    typo = typography or style.DEFAULT_TYPOGRAPHY
    ax.set_axis_off()

    entries: List[Dict[str, Any]] = []
    n_trace_services = 0
    if traces_df is not None and not traces_df.empty and "service_name" in traces_df.columns:
        n_trace_services = int(traces_df["service_name"].nunique())
        pre, during = _split_by_window(traces_df, fault_window, full_range)

        def p95(sub):
            d = pd.to_numeric(sub.get("duration_ms"), errors="coerce")
            return float(np.nanpercentile(d, 95)) if d.notna().any() else float("nan")

        def err_pct(sub):
            s = sub.get("status_code")
            if s is None or not len(sub):
                return 0.0
            v = s.astype(str).str.upper()
            return float((v.str.contains("ERROR") | v.isin(["2", "2.0", "500", "503"])).mean() * 100)

        pre_g = {k: v for k, v in pre.groupby("service_name")} if pre is not None and not pre.empty else {}
        dur_g = {k: v for k, v in during.groupby("service_name")} if during is not None and not during.empty else {}
        for svc in sorted(set(pre_g) | set(dur_g)):
            a, b = pre_g.get(svc), dur_g.get(svc)
            pa = p95(a) if a is not None else float("nan")
            pb = p95(b) if b is not None else float("nan")
            delta = (pb - pa) / pa * 100 if np.isfinite(pa) and np.isfinite(pb) and pa > 0 else float("nan")
            entries.append(
                {
                    "service": str(svc),
                    "p95_pre_ms": pa,
                    "p95_during_ms": pb,
                    "delta_pct": round(delta, 1) if np.isfinite(delta) else None,
                    "error_pct": round(err_pct(b) if b is not None else 0.0, 2),
                    "spans": int(len(a) if a is not None else 0) + int(len(b) if b is not None else 0),
                }
            )
        entries.sort(
            key=lambda e: abs(e["delta_pct"]) if e["delta_pct"] is not None else 0.0,
            reverse=True,
        )
        entries = entries[:top_n]

    displayed_names = []
    for entry in entries:
        entry["service"] = _display_entity(entry["service"], display_labels)
        displayed_names.append(entry["service"])
    rendered_names = _elide_distinct(displayed_names, row_chars)
    for entry, rendered in zip(entries, rendered_names):
        entry["rendered_service"] = rendered

    ax.set_title(
        f"Trace signals — p95 latency pre/during ms{_shown(entries, n_trace_services)}",
        fontsize=typo.panel_title,
        color=style.TEXT,
        loc="left",
        pad=3,
    )

    if entries:
        widths = (7, 7, 6, 5) if compact_columns else (9, 9, 8, 6)
        lines = [
            f"{'service':<{row_chars}}{'pre':>{widths[0]}}"
            f"{'during':>{widths[1]}}{'chg%':>{widths[2]}}{'err%':>{widths[3]}}"
        ]
        for e in entries:
            d = f"{e['delta_pct']:.0f}" if e["delta_pct"] is not None else "n/a"
            lines.append(
                f"{e['rendered_service']:<{row_chars}}{_fmt(e['p95_pre_ms']):>{widths[0]}}"
                f"{_fmt(e['p95_during_ms']):>{widths[1]}}{d:>{widths[2]}}"
                f"{e['error_pct']:>{widths[3]}.1f}"
            )
        body = "\n".join(lines)
    else:
        body = "no trace spans available"

    ax.text(
        0.01,
        0.95,
        body,
        transform=ax.transAxes,
        fontsize=typo.table,
        color=style.TEXT,
        va="top",
        ha="left",
        family="DejaVu Sans Mono",
        linespacing=1.4,
    )
    return {
        "panel_id": panel_id,
        "kind": "traces",
        "entries": entries,
        "service_count": n_trace_services,
        "omitted_services": max(0, n_trace_services - len(entries)),
    }

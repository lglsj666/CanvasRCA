"""
The dashboard compiler: DataCase -> (PNG bytes, panel manifest).

Every RQ1 design axis is a field on DashboardConfig, which is what makes the
RQ4 ablation matrix free: an ablation is one config field flipped, not new code.

Leakage discipline: compile_dashboard never receives a DataCase. It receives a
CaseRenderView, a struct that structurally cannot carry ground_truth. Any future
renderer feature therefore cannot accidentally draw the answer.
"""

from __future__ import annotations

import hashlib
import io
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import pandas as pd  # noqa: E402

from vlmrca.render import panels, style  # noqa: E402
from vlmrca.render.edge_key import (  # noqa: E402
    edge_key_extra_height,
    render_topology_edge_key,
    render_topology_edge_key_large,
)
from vlmrca.render.kpi_select import (  # noqa: E402
    Ranker,
    Selector,
    ScoredSeries,
    infer_fault_window,
    score_series,
    select_panels,
    service_anomaly_scores,
)
from vlmrca.render.onset import compute_service_onsets, service_level_projection  # noqa: E402


# Bump whenever a change alters rendered output for an unchanged config: a
# layout fix, a new panel kind, a change to how a series is drawn. It feeds
# DashboardConfig.fingerprint(), so bumping it invalidates the render cache and
# gives the new images a distinct id in every trajectory. Leave it alone for
# refactors that cannot move a pixel.
#
#   1  as-built through 2026-07-25 (every committed result to date)
#   2  topology caption no longer overlapped by a node; legend column sized
#      from the widest rendered string; coverage_first selector added
#   3  metric-panel titles budgeted against column width instead of a fixed
#      22/26 characters, which overran into the neighbouring panel (and into
#      the log/trace headers) at grid_cols=5
#   4  legend rows budgeted against the side column and elided so two services
#      never render the same string; 95 of 100 AegisLab cases previously had at
#      least one pair a reader could not tell apart
#   5  sparse series are drawn instead of vanishing. These frames are pivots over
#      a union timestamp index, so a column holds data only on the timestamps its
#      own scraper wrote -- 8 to 96 valid samples in a 1064-row AegisLab frame.
#      matplotlib broke the line at every NaN between them, so the panels carried
#      no visible trace at all and the only ink was a fault band one sample wide.
#      Three fixes, one defect: plot the valid samples (with markers when scarce),
#      stop the scorer preferring columns too thinly sampled to have a spread
#      (they scored >=999z on noise and took a quarter of all panels), and expand
#      the fault window between samples rather than between rows. Also adds the
#      propagation panel behind topology="propagation".
#   6  RQ0 leakage-safe identity/time contract. Model-visible dashboards use an
#      opaque incident id, relative time only, and can render the exact 64-bin
#      series serialized in CanonicalEvidenceBundleV1.
#   7  development-only explicit directional edge-key axis. Renderer-v6 curved
#      propagation edges failed the atomic grounding check on both VLMs; the
#      large key passed the post-hoc operational legibility gate on both.
RENDERER_VERSION = 7


# --------------------------------------------------------------------------- #
# Leakage-safe input                                                          #
# --------------------------------------------------------------------------- #

# Metadata keys the renderer may see. Everything else is dropped, whatever it is
# called -- see CaseRenderView.from_case. Add a key here only after checking what
# every loader puts under it on every dataset.
#
#   node_pod_map  physical worker node -> pods it hosts. Deployment topology, the
#                 same information a `kubectl get pods -o wide` would give an SRE
#                 before anyone knew a fault existed. Used to resolve pod names
#                 to service names for the propagation panel.
SAFE_META = frozenset({"node_pod_map"})


@dataclass
class CaseRenderView:
    """
    Everything the renderer may see. Deliberately has no ground_truth field.

    Build it with ``CaseRenderView.from_case``; that constructor is the single
    place where a labelled DataCase is narrowed to unlabelled telemetry.
    """

    case_id: str
    dataset: str
    metrics_df: pd.DataFrame
    logs_df: pd.DataFrame
    traces_df: pd.DataFrame
    graph: nx.DiGraph
    services: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_case(cls, case) -> "CaseRenderView":
        # Whitelist, not blacklist. The previous blacklist matched keys exactly,
        # and upstream loaders name their label fields freely: AegisLab ships
        # `injection_ground_truth` (a dict holding the answer service outright)
        # and AIOPS-2025 ships `service`, `fault_description`, `key_metrics` and
        # more. None of those matched a banned key, so all of them survived into
        # the view. Nothing read view.metadata at the time, so no run leaked --
        # but the next feature to reach for `node_pod_map` would have.
        safe_meta = {k: v for k, v in (case.metadata or {}).items() if k in SAFE_META}
        return cls(
            case_id=case.case_id,
            dataset=case.dataset,
            metrics_df=case.metrics_df,
            logs_df=case.logs_df,
            traces_df=case.traces_df,
            graph=case.graph,
            services=list(case.services),
            metadata=safe_meta,
        )


# --------------------------------------------------------------------------- #
# The RQ1 design space                                                        #
# --------------------------------------------------------------------------- #


@dataclass
class DashboardConfig:
    """One point in the dashboard design space. Every field is an RQ1/RQ4 axis."""

    name: str = "v0"

    # A — KPI selection
    panel_budget: int = 12
    ranker: Ranker = "ksigma"
    # Redundancy caps, 0 = off. Off by default: capping *looked* obviously right
    # (without it, an AegisLab case filled all 12 panels with one metric family
    # and the true cause got none), but the one A/B run so far mildly disfavours
    # it — MRR 0.746 capped vs 0.797 uncapped, n=20, delta CI [-0.177, 0.046].
    # Kept as an RQ1 axis to screen properly at n=100 rather than shipped as a
    # default on reasoning alone. See DD-11.
    max_per_family: int = 0
    max_per_service: int = 0
    # How the budget is allocated once every series is scored. "topk" is the
    # incumbent; "coverage_first" reserves `coverage_services` slots for
    # distinct services before spending the rest on depth.
    #
    # Measured on 100 AegisLab cases: plain top-K at budget 12 leaves the
    # injected service with no metric panel on 34 of them. Round-robin lifts
    # that to 82% covered but drops depth to zero -- no service keeps a second
    # panel, and several correlated series moving together is often what marks
    # an origin rather than a victim. See select_panels for the full frontier.
    selector: Selector = "topk"
    coverage_services: int = 0  # 0 = off; >= panel_budget = full round-robin

    # B — layout
    layout: Literal["small_multiples", "overplot"] = "small_multiples"
    grid_cols: int = 3

    # C — topology
    #
    # "propagation" swaps the call-graph drawing for an onset-ordered timeline:
    # same slot, same question (which service is the origin), different claim
    # about what answers it. The graph shades nodes by how badly each service
    # deviated; the timeline orders them by when each one started. Magnitude
    # ranks victims above origins whenever the origin degrades quietly and its
    # callers queue up behind it, which is the common shape of a saturation
    # fault. Kept as a level of the same axis so the two are directly comparable
    # in screening rather than confounded with a layout change.
    topology: Literal["none", "plain", "colored", "propagation"] = "colored"
    topology_labels: Literal["numbered", "names"] = "numbered"
    max_topology_nodes: int = 25
    # Rows in the propagation panel. Read only when topology == "propagation".
    max_propagation_rows: int = 14
    # Duplicate the same caller->callee facts as an explicit rank-pair key.
    # The default keeps all legacy dashboard pixels unchanged; large is the
    # development candidate qualified by rq0_topology_edge_key_v2.
    topology_edge_key: Literal["none", "compact", "large"] = "none"
    show_legend_table: bool = True

    # D — annotation
    shade_fault_window: bool = True
    annotate_extremes: bool = True
    normalize_panels: bool = False

    # E — resolution (long side in px; 1568 ~= 1.15k image tokens on Anthropic)
    long_side_px: int = 1568

    # F — auxiliary modality panels
    show_logs: bool = True
    show_traces: bool = True

    # RQ0 leakage and fact-equivalence controls. Identity/time redaction is the
    # v6 default for every newly rendered dashboard. ``metric_time_bins=0``
    # retains legacy sampling; the rq0_v6 preset fixes it to 64.
    redact_identity: bool = True
    relative_time_only: bool = True
    metric_time_bins: int = 0

    def fingerprint(self) -> str:
        """
        Stable id for cache keys and result directories.

        RENDERER_VERSION is part of the hash because the config alone does not
        identify an image. A layout fix changes the pixels while every field
        stays equal, so the content-addressed render cache would keep serving
        pre-fix PNGs and two runs would carry the same config_fingerprint while
        having seen different dashboards -- incomparable, but indistinguishable
        in the results. Bump RENDERER_VERSION on any change that alters output.
        """
        import hashlib

        payload = dict(asdict(self))
        payload["_renderer_version"] = RENDERER_VERSION
        blob = json.dumps(payload, sort_keys=True)
        return hashlib.md5(blob.encode()).hexdigest()[:10]


def opaque_incident_id(case_id: str) -> str:
    """Stable label-blind public id; the private roster retains the mapping."""
    return "INC-" + hashlib.sha256(str(case_id).encode("utf-8")).hexdigest()[:12].upper()


# --------------------------------------------------------------------------- #
# Compiler                                                                    #
# --------------------------------------------------------------------------- #


def _side_column_px(width_px: int, cols: int, left: float, right: float, wspace: float) -> float:
    """
    Rendered width of the auxiliary column, in pixels.

    Worth deriving rather than approximating, because `wspace` is not free space
    taken from somewhere else -- matplotlib sizes the gutters as a fraction of
    the mean axes width and shrinks every column to pay for them. Ignoring it
    overstates this column by 23-25%, and the character budgets computed from it
    then overrun: the Service index was budgeting 38 monospace characters into
    room for 31, so a long name in the left column printed straight through the
    right column's row number.

    With n panels of total ratio R across a span W, the gutters take
    (n-1)*wspace*mean_cell, and mean_cell is itself (W - gutters)/n; solving that
    for the gutter total gives the expression below.
    """
    n = cols + 1
    span = right - left
    ratio_total = cols * 1.0 + 1.25
    gutters = span * (n - 1) * wspace / (n + (n - 1) * wspace)
    return width_px * (span - gutters) * 1.25 / ratio_total


def compile_dashboard(
    view: CaseRenderView, cfg: Optional[DashboardConfig] = None
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Render one case to a single PNG plus a panel manifest.

    Pure and deterministic in (view, cfg): the same inputs always produce
    byte-comparable output, which is what golden-image tests rely on.
    """
    cfg = cfg or DashboardConfig()
    style.apply_rc(matplotlib)

    scored = score_series(view.metrics_df, view.services, ranker=cfg.ranker)
    chosen = select_panels(
        scored,
        cfg.panel_budget,
        ranker=cfg.ranker,
        services=view.services,
        max_per_family=cfg.max_per_family,
        max_per_service=cfg.max_per_service,
        selector=cfg.selector,
        coverage_services=cfg.coverage_services,
    )
    anomaly = service_anomaly_scores(scored)
    fault_window = infer_fault_window(view.metrics_df, scored) if cfg.shade_fault_window else None

    # The metric time axis is the reference clock: log and trace tables carry
    # their own columns and units, and are aligned onto this range.
    full_range: Optional[Tuple[float, float]] = None
    if view.metrics_df is not None and not view.metrics_df.empty and "timestamp" in view.metrics_df.columns:
        _t = pd.to_numeric(view.metrics_df["timestamp"], errors="coerce").dropna()
        if len(_t):
            full_range = (float(_t.iloc[0]), float(_t.iloc[-1]))
    if fault_window is None and full_range is not None:
        # Auxiliary panels still need a split point to show change; fall back to
        # the midpoint of the window when no excursion was detectable.
        mid = (full_range[0] + full_range[1]) / 2
        aux_window: Optional[Tuple[float, float]] = (mid, full_range[1])
    else:
        aux_window = fault_window

    n_metric = len(chosen)
    cols = max(1, cfg.grid_cols)
    metric_rows = (n_metric + cols - 1) // cols if n_metric else 0

    # Onsets cost a pass over every span in the case, so only the config that
    # draws them pays for it.
    onsets: Dict[str, Any] = {}
    service_graph = None
    if cfg.topology == "propagation":
        service_graph = service_level_projection(view.graph, view.metadata.get("node_pod_map"))
        onsets = compute_service_onsets(
            traces_df=view.traces_df,
            metrics_df=view.metrics_df,
            scored=scored,
            fault_window=fault_window,
            full_range=full_range,
            services=sorted(service_graph.nodes()) or view.services,
        )

    side_panels = []
    if cfg.topology == "propagation":
        side_panels.append("propagation")
    elif cfg.topology != "none":
        side_panels.append("topology")
    if cfg.show_legend_table:
        side_panels.append("legend")
    if cfg.show_logs:
        side_panels.append("logs")
    if cfg.show_traces:
        side_panels.append("traces")

    # Canvas: metrics occupy the left 2/3, auxiliary panels stack on the right.
    aspect = 0.66
    width_px = cfg.long_side_px
    height_px = int(width_px * aspect)
    fig = plt.figure(figsize=(width_px / style.DPI, height_px / style.DPI), dpi=style.DPI)

    # hspace is generous because each metric panel carries a caption *below* its
    # axes; tighter spacing runs that caption into the next row's title.
    gs = fig.add_gridspec(
        nrows=max(metric_rows, len(side_panels), 1),
        ncols=cols + 1,
        left=0.045,
        right=0.985,
        top=0.895,
        bottom=0.075,
        wspace=0.30,
        hspace=0.95,
        width_ratios=[1.0] * cols + [1.25],
    )

    # Characters a metric-panel title can hold without running into the next
    # column. The grid spans `right - left`, divided into `cols` metric columns
    # plus a 1.25-wide side column, with wspace between them.
    #
    # TITLE_CHAR_EM is calibrated, not derived: the 3-column 1568px layout was
    # reviewed and found free of title collisions at its hand-tuned budget of
    # 22 + 26 + separator, so the constant is set to reproduce ~54 characters
    # in a 324px column and everything else scales from that known-good point.
    # A purely nominal 0.55 em advance for DejaVu Sans predicts overflow there,
    # which the rendered images contradict -- matplotlib draws the title from
    # the axes' left edge and the wspace gutter absorbs a little overhang.
    grid_frac = 0.985 - 0.045
    col_frac = grid_frac / (cols + 1.25) / (1.0 + 0.30 / (cols + 1.25))
    col_px = width_px * col_frac
    char_px = style.FONT_PANEL_TITLE * (style.DPI / 72.0) * style.TITLE_CHAR_EM
    title_chars = max(16, int(col_px / char_px))

    # The side column is 1.25 units wide and holds the legend, which sets its
    # rows in DejaVu Sans Mono at FONT_TABLE - 0.7 when it splits into two
    # columns. Monospace advance is a known 0.602 em, so this needs no
    # calibration -- unlike the proportional panel titles.
    side_px = _side_column_px(width_px, cols, 0.045, 0.985, 0.30)
    legend_char_px = (style.FONT_TABLE - 0.7) * (style.DPI / 72.0) * 0.602
    # The two text columns start at axes fractions 0.01 and 0.53, so each gets
    # slightly over half; budget against the half, which is the tighter of the two.
    legend_row_chars = max(18, int(side_px / 2 / legend_char_px))

    # The propagation panel's name gutter is its own fraction of the same side
    # column, so it needs its own budget: reusing the legend's (sized for two
    # columns of monospace) spilled long service names left out of the aux
    # column and across the metric panels.
    prop_total = panels.ROW_NAME_MARGIN + 1.0 + panels.ROW_READOUT_MARGIN
    prop_name_px = side_px * (panels.ROW_NAME_MARGIN / prop_total)
    prop_char_px = style.FONT_TICK * (style.DPI / 72.0) * style.TITLE_CHAR_EM
    prop_row_chars = max(12, int(prop_name_px / prop_char_px) - 4)  # 4 for "12. "

    manifest_panels: List[Dict[str, Any]] = []

    # Header — opaque identity and relative window only. Never labels, dataset
    # names, source paths, or absolute timestamps.
    ts_range = ""
    if view.metrics_df is not None and not view.metrics_df.empty and "timestamp" in view.metrics_df.columns:
        t = pd.to_numeric(view.metrics_df["timestamp"], errors="coerce").dropna()
        if len(t):
            unit = panels._time_unit(t.to_numpy(dtype="float64"))
            duration_s = max(0.0, (float(t.iloc[-1]) - float(t.iloc[0])) / unit)
            ts_range = f"  |  window t=0–{duration_s:.0f}s ({len(t)} source rows)"
    public_id = opaque_incident_id(view.case_id) if cfg.redact_identity else view.case_id
    dataset_suffix = "" if cfg.redact_identity else f"  ({view.dataset})"
    fig.text(
        0.045,
        0.985,
        f"RCA dashboard — incident {public_id}{dataset_suffix}{ts_range}",
        fontsize=style.FONT_TITLE,
        color=style.TEXT,
        va="top",
        ha="left",
        weight="bold",
    )
    fig.text(
        0.045,
        0.952,
        f"{len(view.services)} services · {len(chosen)} of {len(scored)} metric series shown, ranked by peak deviation "
        f"from pre-fault baseline ({cfg.ranker}) · shaded band = estimated fault window · "
        f"red trace = |z| >= {panels.HOT_Z:.0f} · x-axis = minutes from window start",
        fontsize=style.FONT_ANNOT,
        color=style.MUTED,
        va="top",
        ha="left",
    )

    # Metric small multiples.
    if cfg.layout == "small_multiples":
        for i, s in enumerate(chosen):
            r, c = divmod(i, cols)
            ax = fig.add_subplot(gs[r, c])
            manifest_panels.append(
                panels.render_metric_panel(
                    ax,
                    panel_id=f"M{i+1}",
                    metrics_df=view.metrics_df,
                    series=s,
                    fault_window=fault_window,
                    normalize=cfg.normalize_panels,
                    annotate_extreme=cfg.annotate_extremes,
                    shade_fault=cfg.shade_fault_window,
                    title_chars=title_chars,
                    time_bins=cfg.metric_time_bins,
                    relative_manifest=cfg.relative_time_only,
                )
            )
    else:
        ax = fig.add_subplot(gs[0:max(metric_rows, 1), 0:cols])
        manifest_panels.append(_render_overplot(ax, view, chosen, fault_window, cfg))

    # Auxiliary column.
    topo_nodes: Sequence[str] = sorted(view.graph.nodes())
    n_rows_grid = max(metric_rows, len(side_panels), 1)
    # The propagation strip needs roughly twice a graph thumbnail's height to
    # keep its rows above the 7pt floor, and it can only have it if the side
    # column has a spare row -- which it does when the prop presets drop the
    # legend, whose job the strip does inline. The cursor has to advance by the
    # span, not by one: spanning without advancing drew the log table straight
    # through the strip's lower half.
    prop_span = 2 if ("propagation" in side_panels and len(side_panels) < n_rows_grid) else 1
    row = 0
    for kind in side_panels:
        span = prop_span if kind == "propagation" else 1
        ax = fig.add_subplot(gs[row : min(row + span, n_rows_grid), cols])
        row = min(row + span, n_rows_grid - 1) if row + span >= n_rows_grid else row + span
        if kind == "topology":
            entry = panels.render_topology_panel(
                ax,
                panel_id="T1",
                graph=view.graph,
                anomaly_scores=anomaly,
                label_mode=cfg.topology_labels,
                colored=(cfg.topology == "colored"),
                max_nodes=cfg.max_topology_nodes,
            )
            topo_nodes = entry["node_order"]
            manifest_panels.append(entry)
        elif kind == "propagation":
            manifest_panels.append(
                panels.render_propagation_panel(
                    ax,
                    panel_id="P1",
                    onsets=onsets,
                    graph=service_graph,
                    anomaly_scores=anomaly,
                    full_range=full_range,
                    fault_window=fault_window,
                    max_rows=cfg.max_propagation_rows,
                    row_chars=prop_row_chars,
                    relative_manifest=cfg.relative_time_only,
                )
            )
        elif kind == "legend":
            manifest_panels.append(
                panels.render_legend_panel(
                    ax, "L1", topo_nodes, anomaly, row_chars=legend_row_chars
                )
            )
        elif kind == "logs":
            manifest_panels.append(
                panels.render_log_panel(ax, "G1", view.logs_df, fault_window=aux_window, full_range=full_range)
            )
        elif kind == "traces":
            manifest_panels.append(
                panels.render_trace_panel(ax, "R1", view.traces_df, fault_window=aux_window, full_range=full_range)
            )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    plt.close(fig)
    png = buf.getvalue()

    if cfg.topology_edge_key != "none":
        if cfg.topology != "propagation":
            raise ValueError("topology_edge_key requires topology='propagation'")
        edge_manifest = {"panels": manifest_panels}
        png = (
            render_topology_edge_key_large(png, edge_manifest)
            if cfg.topology_edge_key == "large"
            else render_topology_edge_key(png, edge_manifest)
        )
        height_px += edge_key_extra_height(cfg.topology_edge_key)

    if fault_window and full_range and cfg.relative_time_only:
        time_unit = panels._unit_for_span(full_range[1] - full_range[0])
        manifest_fault_window = [
            (float(fault_window[0]) - full_range[0]) / time_unit,
            (float(fault_window[1]) - full_range[0]) / time_unit,
        ]
    else:
        manifest_fault_window = list(fault_window) if fault_window else None

    manifest = _json_safe({
        "opaque_incident_id": public_id,
        "renderer_version": RENDERER_VERSION,
        "config_name": cfg.name,
        "config_fingerprint": cfg.fingerprint(),
        "config": asdict(cfg),
        "image_px": [width_px, height_px],
        "services": list(view.services),
        "source_metric_rows": int(len(view.metrics_df)),
        "window_duration_s": (
            (full_range[1] - full_range[0])
            / panels._unit_for_span(full_range[1] - full_range[0])
            if full_range
            else None
        ),
        "metric_series_scored": int(len(scored)),
        "metric_series_shown": int(len(chosen)),
        "metric_ranker": cfg.ranker,
        "hot_z_threshold": float(panels.HOT_Z),
        "fault_window_rel_s": manifest_fault_window,
        "service_anomaly_scores": {k: round(v, 3) for k, v in sorted(anomaly.items())},
        "panels": manifest_panels,
    })
    return png, manifest


def _json_safe(obj):
    """Replace non-finite floats with None so manifests are valid JSON."""
    import math

    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def _render_overplot(ax, view, chosen: List[ScoredSeries], fault_window, cfg) -> Dict[str, Any]:
    """All selected series on shared axes — the RQ1 layout comparator."""
    import numpy as np

    for s in chosen:
        vals = pd.to_numeric(view.metrics_df[s.column], errors="coerce").astype("float64").to_numpy()
        if s.baseline_std > 0:
            vals = (vals - s.baseline_mean) / s.baseline_std
        # Same gap handling as the small-multiples path: matplotlib breaks a line
        # at every NaN, and these columns are mostly NaN by construction.
        idx = np.arange(len(vals))
        valid = np.isfinite(vals)
        ax.plot(idx[valid], vals[valid], lw=0.8, label=f"{s.service}·{s.metric}")
    ax.legend(fontsize=style.FONT_TICK, ncol=2, loc="upper left", framealpha=0.9)
    ax.set_title("All selected KPIs (z-scored, shared axes)", fontsize=style.FONT_PANEL_TITLE, loc="left")
    ax.grid(True, alpha=0.5)
    return {
        "panel_id": "M-ALL",
        "kind": "metric_overplot",
        "series": [{"service": s.service, "metric": s.metric, "signed_z": round(s.signed_z, 3)} for s in chosen],
    }


DASHBOARD_V0 = DashboardConfig(name="v0")

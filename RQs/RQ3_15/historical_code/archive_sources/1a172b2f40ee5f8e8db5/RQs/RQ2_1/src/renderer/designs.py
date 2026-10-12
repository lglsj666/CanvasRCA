"""RQ2.1 card encodings and deterministic whole-card composition.

Inputs are selected public packets and an inherited S0 raster, never a case or
tool scorer. Every intervention has an explicit dispatch; unknown designs fail.
"""

from __future__ import annotations

import hashlib
import io
import math
import re
import textwrap
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ..utils import DesignInfeasible, ProtocolError

SILHOUETTES = (
    "S0",
    "S_M_HEATMAP",
    "S_M_TIME_BARS",
    "S_M_OVERLAY",
    "S_R_PAIRED_BARS",
    "S_R_DUMBBELL",
    "S_L_MATRIX",
    "S_G_MATRIX",
    "S_G_LAYERED",
    "S_TABLE",
    "S_COMPACT_MIX",
    "S_DENSITY_COMPACT",
)
COMPACT_DENSITY_V1 = {"baseline": "S0", "gap_scale": 0.5, "minimum_gap_px": 6}
COMPOSITIONS = (
    "D0",
    "D_COMPACT",
    "D_AIRY",
    "D_ENTITY",
    "D_TOPOLOGY_CENTER",
    "D_ONSET_ORDER",
    "D_LANDSCAPE",
    "D_PORTRAIT",
    "D_SCALE_075",
    "D_SCALE_125",
    "D_SCALE_150",
)
PALETTE = ("#2166ac", "#b2182b", "#15803d")


def png_bytes(image):
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=False, compress_level=6)
    return out.getvalue()


def font(size, bold=False):
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", max(7, int(size)))


def number(value):
    if value is None:
        return float("nan")
    try:
        return float(value)
    except (ValueError, TypeError):
        return float("nan")


def onset_number(value):
    text = str(value or "")
    return number(text[:-1]) if re.fullmatch(r"[+-]?\d+(?:\.\d+)?m", text) else number(value)


def contain_tile(source, size):
    """Uniform scaling preserves glyph and plot aspect; unused space is neutral."""
    scale = min(size[0] / source.width, size[1] / source.height)
    resized = source.resize(
        (max(1, round(source.width * scale)), max(1, round(source.height * scale))),
        Image.Resampling.LANCZOS,
    )
    tile = Image.new("RGB", size, "white")
    tile.paste(resized, ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2))
    return tile


def fit_lines(draw, text, face, width):
    """Lossless wrapping, including an individual long identifier."""
    result = []
    for logical in str(text).splitlines() or [""]:
        rest = logical
        while rest:
            if draw.textlength(rest, font=face) <= width:
                result.append(rest)
                break
            lo, hi = 1, len(rest)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if draw.textlength(rest[:mid], font=face) <= width:
                    lo = mid
                else:
                    hi = mid - 1
            if draw.textlength(rest[:lo], font=face) > width:
                raise DesignInfeasible("one glyph exceeds card width")
            result.append(rest[:lo])
            rest = rest[lo:]
        if not logical:
            result.append("")
    return result


def neutralize_header(png, aspect):
    image = Image.open(io.BytesIO(png)).convert("RGB")
    base = int(image.width * aspect)
    box = (0, round(base * 0.039), image.width, round(base * 0.068))
    draw = ImageDraw.Draw(image)
    draw.rectangle(box, fill="white")
    caption = (
        "Selected telemetry evidence · shaded band = telemetry-estimated analysis window · "
        "red metric trace = large absolute deviation · x-axis = minutes from window start"
    )
    face = font(12)
    if draw.textlength(caption, font=face) > image.width * 0.91:
        raise DesignInfeasible("neutral header exceeds fixed width")
    draw.text((round(image.width * 0.045), box[1] + 4), caption, fill="#666666", font=face)
    # Registered caption-only calibration. Do not retain claims about how a
    # different selector ranked or supplied the displayed graph rows.
    split = round(image.width * 0.746)
    title_box = [split, round(base * 0.088), image.width, round(base * 0.105)]
    footer_box = [split, round(base * 0.507), image.width, round(base * 0.558)]
    for area in (title_box, footer_box):
        draw.rectangle(area, fill="white")
    draw.text(
        (split + 12, title_box[1] + 2),
        "G — selected public onset evidence",
        font=font(12),
        fill="#263238",
    )
    for i, line in enumerate(
        (
            "readout: onset · z + source",
            "T/R=trace, M=metric; z not comparable",
            "Use caller → callee key for call direction.",
        )
    ):
        draw.text(
            (split + 12, footer_box[1] + 4 + 14 * i),
            line,
            font=font(10),
            fill="#666666",
        )
    return png_bytes(image), {
        "caption_box": list(box),
        "caption_boxes": [list(box), title_box, footer_box],
        "box": [0, 0, image.width, round(base * 0.088)],
    }


def card_manifest(packet, size, aspect=0.76):
    """Fixed parent card membership. G includes its original bottom edge key."""
    w, h = size
    from .dashboard import DASHBOARD_PROPAGATION_END, DASHBOARD_SIDE_SPLIT

    base, split = int(w * aspect), round(w * DASHBOARD_SIDE_SPLIT)
    top, prop_end = round(base * 0.088), round(base * DASHBOARD_PROPAGATION_END)
    log_end = prop_end + (base - prop_end) // 2
    metric_facts = sorted(
        (f for f in packet["facts"] if f["field"] == "metric_series_64"),
        key=lambda f: f["payload"]["rank"],
    )
    cards = []
    for row in range(math.ceil(len(metric_facts) / 3)):
        y0 = top if row == 0 else round(base * (0.316 + (row - 1) * 0.234))
        y1 = base if row == 3 else round(base * (0.316 + row * 0.234))
        facts = metric_facts[row * 3 : (row + 1) * 3]
        cards.append(
            {
                "card_id": f"M_ROW_{row + 1}",
                "region": "M",
                "boxes": [[0, y0, split, y1]],
                "facts": facts,
            }
        )
    for region, boxes in (
        ("G", [[split, top, w, prop_end], [0, base, w, h]]),
        ("L", [[split, prop_end, w, log_end]]),
        ("R", [[split, log_end, w, base]]),
    ):
        cards.append(
            {
                "card_id": region,
                "region": region,
                "boxes": boxes,
                "facts": [f for f in packet["facts"] if f["region"] == region],
            }
        )
    for card in cards:
        card["box"] = card["boxes"][0]
        card["fact_ids"] = [r["fact_id"] for r in card["facts"]]
        card["entity_ids"] = sorted({e for r in card["facts"] for e in r["entity_ids"]})
        related = {
            r["payload"]["service"]: onset_number(r["payload"].get("onset_rel_min_display"))
            for r in packet["facts"]
            if r["field"] == "propagation_service"
        }
        card["onset"] = min(
            (related[e] for e in card["entity_ids"] if e in related and math.isfinite(related[e])),
            default=None,
        )
    return {
        "schema": "RQ21CardCanvasV1",
        "size": list(size),
        "base_height": base,
        "fact_inventory_hash": packet["fact_inventory_hash"],
        "cards": cards,
        "common_fact_ids": [
            f["fact_id"]
            for f in packet["facts"]
            if f["field"]
            not in {
                "metric_series_64",
                "trace_summary_entry",
                "denum_log_template",
                "propagation_service",
                "directed_call_edge",
            }
        ],
    }


def raster_figure(fig, width, height):
    fig.canvas.draw()
    # Clip checks are performed on real text extents, not on manifest strings.
    renderer = fig.canvas.get_renderer()
    for text in fig.findobj(matplotlib.text.Text):
        if not text.get_visible() or not text.get_text():
            continue
        box = text.get_window_extent(renderer)
        if box.x0 < -1 or box.y0 < -1 or box.x1 > width + 1 or box.y1 > height + 1:
            plt.close(fig)
            raise DesignInfeasible(
                f"chart text exceeds {width}x{height}: {text.get_text()!r} at {tuple(round(v, 1) for v in box.bounds)}"
            )
    data = np.asarray(fig.canvas.buffer_rgba()).copy()
    plt.close(fig)
    return Image.fromarray(data).convert("RGB")


def metric_summary(payload):
    z = payload.get("sircl_met_z", {})
    return (
        f"baseline={payload.get('baseline')} peak={payload.get('peak')} z={payload.get('signed_z')}\n"
        f"MET-Z mean {z.get('regular_mean')}→{z.get('current_mean')}; "
        f"std {z.get('regular_std_dev')}→{z.get('current_std_dev')}"
    )


def metric_tile(card, mode, width, height, duration):
    facts = sorted(card["facts"], key=lambda r: r["payload"]["rank"])
    payloads = [f["payload"] for f in facts]
    groups = []
    for f in facts:
        compatible = next(
            (
                g
                for g in groups
                if len(g) < 3 and g[0]["unit"] == f["unit"] and g[0]["payload"]["metric"] == f["payload"]["metric"]
            ),
            None,
        )
        if mode == "S_M_OVERLAY" and compatible is not None:
            compatible.append(f)
        else:
            groups.append([f])
    fig = plt.figure(figsize=(width / 100, height / 100), dpi=100, facecolor="white")
    axes = fig.subplots(1, max(1, len(groups)), squeeze=False)[0]
    bottom = 0.30 + 0.06 * max(map(len, groups), default=1)
    fig.subplots_adjust(left=0.065, right=0.975, bottom=bottom, top=0.76, wspace=0.45)
    overlay_count = 0
    for ax, group in zip(axes, groups):
        labels, summaries = [], []
        for index, f in enumerate(group):
            p = f["payload"]
            vals = np.array([number(v) for v in p["values"]])
            x = (np.arange(64) + 0.5) / 64 * duration / 60
            label = f"{p['panel_id']} {p['service']} {p['metric']}"
            labels.append(label)
            summaries.append(metric_summary(p))
            if mode in {"S_M_HEATMAP", "S_COMPACT_MIX"}:
                good = vals[np.isfinite(vals)]
                lo, hi = (float(good.min()), float(good.max())) if len(good) else (0, 1)
                cmap = plt.get_cmap("viridis").copy()
                cmap.set_bad("#eeeeee")
                ax.imshow(
                    np.ma.masked_invalid(vals[None, :]),
                    cmap=cmap,
                    aspect="auto",
                    origin="lower",
                    extent=[0, duration / 60, 0, 1],
                    vmin=lo,
                    vmax=hi if hi > lo else lo + 1,
                )
                ax.set_yticks([])
                ax.text(
                    0.01,
                    0.03,
                    f"min {lo:.3g}; max {hi:.3g}",
                    transform=ax.transAxes,
                    fontsize=7,
                    color="black",
                    bbox={"facecolor": "white", "alpha": 0.85, "pad": 1},
                )
            elif mode == "S_M_TIME_BARS":
                ax.bar(x, vals, width=duration / 60 / 64 * 0.9, color=PALETTE[index])
            else:
                finite = np.isfinite(vals)
                ax.plot(
                    x[finite],
                    vals[finite],
                    lw=1.25,
                    marker=".",
                    markersize=2.5,
                    color=PALETTE[index],
                    label=p["service"],
                )
        if len(group) > 1:
            ax.legend(loc="best", fontsize=7)
            overlay_count += len(group)
            labels = [
                ", ".join(f"{f['payload']['panel_id']} {f['payload']['service']}" for f in group),
                group[0]["payload"]["metric"],
            ]
        label_text = "\n".join(textwrap.fill(v, max(18, int(width / len(groups) / 9))) for v in labels)
        ax.set_title(label_text, fontsize=8, loc="left", pad=5)
        ax.tick_params(labelsize=7)
        ax.set_xlim(0, duration / 60)
        ax.set_xticks([0, duration / 120, duration / 60])
        ax.set_xlabel("relative minutes", fontsize=7)
        unit = (
            str(group[0]["unit"] or "source value")
            .replace("milliseconds_or_source_unit", "source unit")
            .replace("_", " ")
        )
        ax.text(
            0.99,
            0.98,
            textwrap.fill(unit, 24),
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=6,
        )
        measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        # Measure actual glyph widths (points converted to 100-DPI pixels),
        # rather than assuming a fixed characters-per-line approximation.
        summary = "\n".join(
            line
            for value in summaries
            for line in fit_lines(measure, value, font(9), int(ax.get_position().width * width) - 10)
        )
        ax.text(0, -0.47, summary, transform=ax.transAxes, va="top", fontsize=6.4)
        ax.grid(axis="x", alpha=0.15)
    tile = raster_figure(fig, width, height)
    return tile, {
        "overlay_series": overlay_count,
        "series": len(payloads),
        "bins_per_series": 64,
    }


def text_tile(title, texts, width, height, *, minimum=8):
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    face, titleface = font(minimum), font(minimum + 3, True)
    lines = []
    for text in texts:
        lines.extend(fit_lines(draw, text, face, width - 20))
    line_height = minimum + 3
    if 32 + len(lines) * line_height > height - 8:
        raise DesignInfeasible("complete card text exceeds its registered footprint")
    draw.text((8, 5), title, fill="#20343e", font=titleface)
    y = 29
    for line in lines:
        draw.text((8, y), line, fill="#263238", font=face)
        y += line_height
    return image


def trace_tile(card, mode, width, height):
    from .panels import _elide, _fmt

    rows = sorted(
        (r["payload"] for r in card["facts"] if r["field"] == "trace_summary_entry"),
        key=lambda r: r["entry_index"],
    )
    if not rows:
        return text_tile("R — traces", ["No selected trace entries."], width, height), {}
    fig = plt.figure(figsize=(width / 100, height / 100), dpi=100)
    ax = fig.subplots()
    fig.subplots_adjust(left=0.49, right=0.96, bottom=0.18, top=0.85)
    for i, p in enumerate(rows):
        b, c = number(p["exl_p95_base_ms"]), number(p["exl_p95_fault_ms"])
        if mode == "S_R_PAIRED_BARS":
            ax.barh(i - 0.13, b, height=0.24, color=PALETTE[0])
            ax.barh(i + 0.13, c, height=0.24, color=PALETTE[1])
        else:
            ax.plot([b, c], [i, i], color="#999999", lw=1)
            ax.scatter([b, c], [i, i], c=PALETTE[:2], s=12)
        label = (
            f"{p['service']} {_elide(p['operation'], 18)}\ncount {p['count_base']}→{p['count_fault']}; "
            f"ExL {_fmt(b)}→{_fmt(c)}\n"
            f"dC={p['count_lfc']:.1f} dX={p['latency_lfc']:.1f} score={p['rank_score']:.1f}"
        )
        ax.text(
            -0.04,
            i,
            label,
            transform=ax.get_yaxis_transform(),
            ha="right",
            va="center",
            fontsize=6,
        )
    ax.invert_yaxis()
    ax.set_yticks([])
    ax.tick_params(labelsize=7)
    maximum = max([number(p[k]) for p in rows for k in ("exl_p95_base_ms", "exl_p95_fault_ms")] + [1])
    ax.set_xlim(0, maximum * 1.2)
    ax.set_xticks([0, maximum / 2, maximum], ["0", _fmt(maximum / 2), _fmt(maximum)])
    ax.set_xlabel("exclusive latency p95 (ms)", fontsize=7)
    ax.set_title("R — baseline (blue) / current (red)", loc="left", fontsize=8)
    return raster_figure(fig, width, height), {}


def log_tile(card, width, height):
    from ..exps import denum_visual_text

    rows = [r["payload"] for r in card["facts"] if r["field"] == "denum_log_template"]
    strip_height = max(35, min(65, height // 4))
    labels = [denum_visual_text(r) for r in rows]
    text = text_tile(
        "L — template × relative bin; shade = count",
        labels,
        width,
        height - strip_height,
    )
    out = Image.new("RGB", (width, height), "white")
    out.paste(text, (0, strip_height))
    draw = ImageDraw.Draw(out)
    if rows:
        max_count = max(r["count"] for r in rows)
        for i, row in enumerate(rows):
            x = 8 + row["relative_bin"] / 64 * (width - 16)
            y = 3 + i / len(rows) * (strip_height - 12)
            shade = int(240 - 180 * row["count"] / max(1, max_count))
            draw.rectangle(
                [x, y, x + (width - 16) / 64, y + (strip_height - 12) / len(rows)],
                fill=(shade, shade, 245),
            )
        draw.text(
            (8, strip_height - 12),
            "bins 0 … 63; exact bin/count below",
            fill="#263238",
            font=font(8),
        )
    return out, {}


def graph_tile(card, mode, width, height):
    nodes = sorted(
        (f["payload"] for f in card["facts"] if f["field"] == "propagation_service"),
        key=lambda r: r["rank"],
    )
    edges = [f["payload"] for f in card["facts"] if f["field"] == "directed_call_edge"]
    if not nodes:
        return text_tile("G — directed topology", ["No selected nodes or edges."], width, height), {}
    graph = nx.DiGraph()
    graph.add_nodes_from(p["service"] for p in nodes)
    graph.add_edges_from((p["caller"], p["callee"]) for p in edges)
    if set(graph) != {p["service"] for p in nodes}:
        raise ProtocolError("edge endpoint lacks selected node")
    names = sorted(graph, key=int)
    fig = plt.figure(figsize=(width / 100, height / 100), dpi=100)
    ax = fig.add_axes([0.14, 0.48, 0.77, 0.41])
    if mode in {"S_G_MATRIX", "S_COMPACT_MIX"}:
        ax.imshow(nx.to_numpy_array(graph, nodelist=names), cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks(range(len(names)), names, rotation=90, fontsize=6)
        ax.set_yticks(range(len(names)), names, fontsize=6)
        ax.set_xlabel("callee → columns", fontsize=7)
        ax.set_ylabel("caller → rows", fontsize=7)
    else:
        # Condensation supplies layer order only; original cycles and all edges
        # are drawn on the original graph, never replaced by a spanning tree.
        components = list(nx.strongly_connected_components(graph))
        condensed = nx.condensation(graph, components)
        layers = list(nx.topological_generations(condensed))
        positions = {}
        for depth, layer in enumerate(layers):
            members = sorted(n for component in layer for n in condensed.nodes[component]["members"])
            for i, name in enumerate(members):
                positions[name] = ((i + 1) / (len(members) + 1), -depth)
        nx.draw_networkx(
            graph,
            positions,
            ax=ax,
            node_size=210,
            font_size=6,
            node_color="#e4f0ff",
            edge_color="#53738c",
            arrows=True,
            arrowsize=9,
            connectionstyle="arc3,rad=0.13",
        )
        ax.margins(0.18)
        ax.set_axis_off()
    ax.set_title("G — caller → callee", fontsize=9)
    texts = [
        f"{p['service']} onset={p.get('onset_rel_min_display')} z={p.get('severity_z_display')} {p.get('evidence_source_display')}"
        for p in nodes
    ]
    drawheight = int(height * 0.39)
    note = text_tile("Node evidence", texts, width, drawheight, minimum=8)
    tile = raster_figure(fig, width, height)
    tile.paste(note, (0, height - drawheight))
    return tile, {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "isolated_nodes": list(nx.isolates(graph)),
    }


def table_tile(card, width, height):
    if card["region"] == "M":
        facts = sorted(card["facts"], key=lambda f: f["payload"]["rank"])
        out = Image.new("RGB", (width, height), "white")
        draw, face = ImageDraw.Draw(out), font(8)
        cell_width = width // max(1, len(facts))
        for column, fact in enumerate(facts):
            p = fact["payload"]
            left = column * cell_width + 5
            title = f"{p['panel_id']} {p['service']} {p['metric']}"
            title_lines = fit_lines(draw, title, font(9, True), cell_width - 10)
            y = 5
            for line in title_lines:
                draw.text((left, y), line, font=font(9, True), fill="#20343e")
                y += 12
            summary = fit_lines(draw, metric_summary(p), face, cell_width - 10)
            for line in summary:
                draw.text((left, y), line, font=face, fill="#455a64")
                y += 11
            y += 5
            for index, value in enumerate(p["values"]):
                col, row = index % 4, index // 4
                text = f"{index:02d}:{'missing' if p['missing_mask'][index] else value}"
                x = left + col * (cell_width - 10) / 4
                if draw.textlength(text, font=face) > (cell_width - 10) / 4:
                    raise DesignInfeasible("exact metric table value exceeds cell width")
                if y + row * 11 + 11 > height - 5:
                    raise DesignInfeasible("complete 64-bin metric table exceeds card height")
                draw.text((x, y + row * 11), text, font=face, fill="#263238")
        return out, {"bins_per_series": 64, "table_columns_per_series": 4}
    from ..exps import denum_visual_text
    from .panels import _elide, _fmt

    rows = []
    for fact in sorted(
        (
            f
            for f in card["facts"]
            if f["field"]
            in {
                "trace_summary_entry",
                "denum_log_template",
                "propagation_service",
                "directed_call_edge",
            }
        ),
        key=lambda f: f["payload"].get("entry_index", f["payload"].get("rank", 0)),
    ):
        p = fact["payload"]
        if card["region"] == "R":
            rows.append(
                f"{p['service']} {_elide(p['operation'], 18)}\ncount {p['count_base']}→{p['count_fault']}; ExL {_fmt(p['exl_p95_base_ms'])}→{_fmt(p['exl_p95_fault_ms'])}\n"
                f"dC={p['count_lfc']:.1f}; dX={p['latency_lfc']:.1f}; score={p['rank_score']:.1f}"
            )
        elif card["region"] == "L":
            rows.append(denum_visual_text(p))
        elif fact["field"] == "propagation_service":
            rows.append(
                f"{p['service']} onset={p.get('onset_rel_min_display')} z={p.get('severity_z_display')} {p.get('evidence_source_display')}"
            )
        else:
            rows.append(f"{p['caller']} → {p['callee']}")
    return text_tile(
        f"{card['region']} — evidence table",
        rows or ["No selected records; evidence unavailable."],
        width,
        height,
    ), {}


def encode_card(card, silhouette, size, duration):
    width, height = size
    mode = silhouette
    if silhouette == "S_COMPACT_MIX":
        mode = {
            "M": "S_M_HEATMAP",
            "R": "S_R_DUMBBELL",
            "L": "S_L_MATRIX",
            "G": "S_G_MATRIX",
        }[card["region"]]
    if mode == "S_TABLE":
        return table_tile(card, width, height)
    if card["region"] == "M" and mode.startswith("S_M_"):
        return metric_tile(card, mode, width, height, duration)
    if card["region"] == "R" and mode.startswith("S_R_"):
        return trace_tile(card, mode, width, height)
    if card["region"] == "L" and mode == "S_L_MATRIX":
        return log_tile(card, width, height)
    if card["region"] == "G" and mode.startswith("S_G_"):
        return graph_tile(card, mode, width, height)
    return None, {}  # Explicitly untreated card: preserve its inherited pixels.


def duration_seconds(packet):
    row = next(f["payload"] for f in packet["facts"] if f["field"] == "observation_window")
    return float(row["duration_rel_s"])


def compact_white_corridors(image, axis, *, metric_seams=False, spec=None):
    """Translate intact strips across whitespace; never resize an axis or glyph.

    Called only for text rows or metric inter-panel seams, never inside the
    connected topology plot. The outer footprint and leading margin stay fixed.
    """
    spec = dict(COMPACT_DENSITY_V1 if spec is None else spec)
    if spec != COMPACT_DENSITY_V1 or axis not in (0, 1):
        raise ProtocolError("unregistered internal-density definition")
    data = np.asarray(image.convert("RGB"))
    samples = data[:: max(1, image.height // 64), :: max(1, image.width // 64)].reshape(-1, 3)
    colors, counts = np.unique(samples, axis=0, return_counts=True)
    background = colors[int(counts.argmax())]
    if np.any(background < 240):
        raise ProtocolError("density packing requires a light uniform background")
    white = np.all(data == background, axis=(1 - axis, 2))
    cuts = np.flatnonzero(np.diff(np.r_[False, white, False].astype(int)))
    gaps = [
        (int(a), int(b))
        for a, b in zip(cuts[::2], cuts[1::2])
        if a > 0 and b < len(white) and b - a > spec["minimum_gap_px"]
    ]
    if metric_seams:
        # Only the two gutters separating the three inherited mini-panels.
        selected = set()
        for seam in (len(white) / 3, 2 * len(white) / 3):
            eligible = [g for g in gaps if abs((g[0] + g[1]) / 2 - seam) <= len(white) / 12]
            if eligible:
                selected.add(min(eligible, key=lambda g: (abs((g[0] + g[1]) / 2 - seam), g)))
        gaps = sorted(selected)
    keep = np.ones(len(white), dtype=bool)
    removed = []
    for start, end in gaps:
        remaining = max(spec["minimum_gap_px"], math.ceil((end - start) * spec["gap_scale"]))
        keep[start + remaining : end] = False
        removed.append({"source": [start, end], "remaining_px": remaining})
    result = np.empty_like(data)
    result[:] = background
    count = int(keep.sum())
    if axis == 0:
        result[:count, :, :] = data[keep, :, :]
    else:
        result[:, :count, :] = data[:, keep, :]
    before_ink = data[np.any(data != background, axis=2)].tobytes()
    after_ink = result[np.any(result != background, axis=2)].tobytes()
    if before_ink != after_ink:
        raise ProtocolError("density packing changed nonwhite evidence pixels")
    runs = np.flatnonzero(np.diff(np.r_[False, keep, False].astype(int)))
    strips, destination = [], 0
    for start, end in zip(runs[::2], runs[1::2]):
        strips.append({"source": [int(start), int(end)], "destination_start": destination})
        destination += int(end - start)
    occupied = np.flatnonzero(~white)
    old_extent = int(occupied[-1] - occupied[0] + 1) if len(occupied) else 0
    saved = int((~keep).sum())
    return Image.fromarray(result), {
        "axis": axis,
        "background_rgb": background.tolist(),
        "gaps": removed,
        "strips": strips,
        "saved_gap_px": saved,
        "occupied_extent_before_px": old_extent,
        "occupied_extent_after_px": old_extent - saved,
        "ink_sha256": hashlib.sha256(before_ink).hexdigest(),
        "ink_bytes_preserved": True,
        "changed": bool(saved),
    }


def compact_internal_dashboard(png, manifest, spec=None):
    if manifest.get("unrendered_regions"):
        raise DesignInfeasible("density cannot invent evidence missing from S0")
    if manifest.get("silhouette") != "S0":
        raise ProtocolError("density control must start from S0, not another encoding")
    image = Image.open(io.BytesIO(png)).convert("RGB")
    audits = {}
    for card in manifest["cards"]:
        rows = []
        for index, bounds in enumerate(card["boxes"]):
            # The connected G plot is an indivisible geometric object. Its
            # separate explicit-edge ledger is text and can be packed safely.
            if card["region"] == "G" and index == 0:
                continue
            # Preserve existing panel frames; they are not inter-row content.
            inset = 4 if card["region"] in {"L", "G"} else 0
            x, y, a, b = bounds
            inner = [x + inset, y + inset, a - inset, b - inset]
            tile, audit = compact_white_corridors(
                image.crop(tuple(inner)),
                1 if card["region"] == "M" else 0,
                metric_seams=card["region"] == "M",
                spec=spec,
            )
            image.paste(tile, (inner[0], inner[1]))
            rows.append({"box": bounds, "interior_box": inner, **audit})
        audits[card["card_id"]] = {
            "drawn_fact_ids": card["fact_ids"],
            "footprints": rows,
        }
    result = png_bytes(image)
    return result, {
        **manifest,
        "silhouette": "S_DENSITY_COMPACT",
        "encoding_audit": audits,
        "density": {
            "spec": dict(spec or COMPACT_DENSITY_V1),
            "coordinate_space": "encoding_before_composition",
            "parent_png_sha256": hashlib.sha256(png).hexdigest(),
        },
        "image_sha256": hashlib.sha256(result).hexdigest(),
    }


def encode_dashboard(png, manifest, packet, silhouette, *, density=None):
    if silhouette not in SILHOUETTES:
        raise ProtocolError("unknown silhouette")
    if silhouette == "S_DENSITY_COMPACT":
        return compact_internal_dashboard(png, manifest, density)
    if silhouette == "S0":
        if manifest.get("unrendered_regions"):
            raise DesignInfeasible("selected facts do not fit the S0 footprint")
        return png, dict(manifest)
    image = Image.open(io.BytesIO(png)).convert("RGB")
    audits, repaired = {}, set()
    for card in manifest["cards"]:
        x0, y0, x1, y1 = card["box"]
        tile, audit = encode_card(card, silhouette, (x1 - x0, y1 - y0), duration_seconds(packet))
        if tile is None:
            continue
        image.paste(tile, (x0, y0))
        # G's complete explicit edge key remains at its D0 position; it is
        # also a component of the single logical G card during composition.
        audits[card["card_id"]] = {**audit, "drawn_fact_ids": card["fact_ids"]}
        repaired.add(card["region"])
    if set(manifest.get("unrendered_regions", [])) - repaired:
        raise DesignInfeasible("this encoding does not redraw every incomplete region")
    result = png_bytes(image)
    return result, {
        **manifest,
        "silhouette": silhouette,
        "encoding_audit": audits,
        "image_sha256": hashlib.sha256(result).hexdigest(),
        "unrendered_regions": [],
    }


def target_size(size, composition):
    w, h = size
    if composition.startswith("D_SCALE_"):
        scale = {"D_SCALE_075": 0.75, "D_SCALE_125": 1.25, "D_SCALE_150": 1.5}[composition]
        return round(w * scale), round(h * scale)
    if composition in {"D_LANDSCAPE", "D_PORTRAIT"}:
        ratio = 4 / 3 if composition == "D_LANDSCAPE" else 2 / 3
        # Integer width search; never exceed the registered pixel budget.
        center = round(math.sqrt(w * h * ratio))
        candidates = [(x, min(w * h // x, round(x / ratio))) for x in range(max(1, center - 4), center + 5)]
        return min(candidates, key=lambda s: (abs(s[0] / s[1] - ratio), -(s[0] * s[1])))
    return w, h


def composition_boxes(manifest, composition):
    if composition not in COMPOSITIONS:
        raise ProtocolError("unknown composition")
    w, h = target_size(manifest["size"], composition)
    if composition in {"D0", "D_COMPACT", "D_AIRY"} or composition.startswith("D_SCALE_"):
        sx, sy = w / manifest["size"][0], h / manifest["size"][1]
        return (w, h), {
            c["card_id"]: [[round(x * sx), round(y * sy), round(a * sx), round(b * sy)] for x, y, a, b in c["boxes"]]
            for c in manifest["cards"]
        }
    cards = list(manifest["cards"])
    if composition == "D_TOPOLOGY_CENTER":
        gap, top = 12, round(h * 0.105)
        cw = (w - 4 * gap) // 3
        ch = (h - top - 4 * gap) // 3
        result = {"G": [[2 * gap + cw, top + gap, 2 * gap + 2 * cw, h - gap]]}
        others = sorted((c for c in cards if c["region"] != "G"), key=lambda c: c["card_id"])
        for i, card in enumerate(others):
            col, row = (0 if i < 3 else 2), i % 3
            x, y = gap + col * (cw + gap), top + gap + row * (ch + gap)
            result[card["card_id"]] = [[x, y, x + cw, y + ch]]
        return (w, h), result
    if composition == "D_ENTITY":
        cards.sort(key=lambda c: (min(map(int, c["entity_ids"]), default=10**9), c["card_id"]))
    elif composition == "D_ONSET_ORDER":
        cards.sort(key=lambda c: (c["onset"] is None, c["onset"] or 0, c["card_id"]))
    else:
        cards.sort(key=lambda c: ("MRLG".index(c["region"]), c["card_id"]))
    # Deterministic two-column shelf packing. The G footprint receives two
    # grid heights; card boundaries, membership and chart axes remain fixed.
    weights = {c["card_id"]: (2 if c["region"] == "G" else 1) for c in cards}
    total = sum(weights.values())
    rows = math.ceil(total / 2)
    factor = 0.5 if composition == "D_COMPACT" else 1.5 if composition == "D_AIRY" else 1
    gap = round(16 * factor)
    top = round(h * 0.105)
    cw, ch = (w - 3 * gap) // 2, (h - top - (rows + 1) * gap) // rows
    occupied = set()
    boxes = {}
    # Allocate the tall card first, but use its position in the requested order
    # to choose an anchor. This avoids fragmentation masquerading as infeasibility.
    placement_order = sorted(cards, key=lambda c: (-weights[c["card_id"]], cards.index(c)))
    for card in placement_order:
        span = weights[card["card_id"]]
        legal = [
            (r, c)
            for r in range(rows - span + 1)
            for c in range(2)
            if all((r + dy, c) not in occupied for dy in range(span))
        ]
        if not legal:
            raise DesignInfeasible("whole-card grid packing has no legal placement")
        preferred = cards.index(card)
        r, c = min(legal, key=lambda rc: (abs(rc[0] * 2 + rc[1] - preferred), rc))
        occupied.update((r + dy, c) for dy in range(span))
        x, y = gap + c * (cw + gap), top + gap + r * (ch + gap)
        boxes[card["card_id"]] = [[x, y, x + cw, y + span * ch + (span - 1) * gap]]
    return (w, h), boxes


def validate_boxes(size, cards):
    rectangles = []
    for card in cards:
        for box in card["boxes"]:
            x, y, a, b = box
            if not (0 <= x < a <= size[0] and 0 <= y < b <= size[1]):
                raise ProtocolError("card outside canvas")
            if any(max(x, q[0]) < min(a, q[2]) and max(y, q[1]) < min(b, q[3]) for q in rectangles):
                raise ProtocolError("card footprints overlap")
            rectangles.append(box)


def compose_dashboard(png, manifest, packet, composition):
    size, boxes = composition_boxes(manifest, composition)
    if composition == "D0":
        return png, dict(manifest)
    old = Image.open(io.BytesIO(png)).convert("RGB")
    cards = [{**c, "boxes": boxes[c["card_id"]], "box": boxes[c["card_id"]][0]} for c in manifest["cards"]]
    validate_boxes(size, cards)
    if composition.startswith("D_SCALE_"):
        image = old.resize(size, Image.Resampling.LANCZOS)
    elif composition in {"D_COMPACT", "D_AIRY"}:
        image = old.copy()
        factor = 0.5 if composition == "D_COMPACT" else 1.5
        for card in cards:
            for x, y, a, b in card["boxes"]:
                source = old.crop((x, y, a, b))
                # Adjust non-content perimeter only; never crop ink. The
                # baseline perimeter is measured from the inherited raster.
                data = np.asarray(source)
                ink = np.any(data < 235, axis=2)
                ys, xs = np.where(ink)
                if not len(xs):
                    continue
                box = (
                    int(xs.min()),
                    int(ys.min()),
                    int(xs.max()) + 1,
                    int(ys.max()) + 1,
                )
                left, top = round(box[0] * factor), round(box[1] * factor)
                right, bottom = (
                    round((source.width - box[2]) * factor),
                    round((source.height - box[3]) * factor),
                )
                content = source.crop(box)
                target = (source.width - left - right, source.height - top - bottom)
                if min(target) <= 0:
                    raise DesignInfeasible("padding leaves no content area")
                image.paste("white", (x, y, a, b))
                image.paste(contain_tile(content, target), (x + left, y + top))
    else:
        image = Image.new("RGB", size, "white")
        header = old.crop((0, 0, old.width, round(manifest["base_height"] * 0.088)))
        image.paste(contain_tile(header, (size[0], round(size[1] * 0.095))), (0, 0))
        for before, after in zip(manifest["cards"], cards):
            x, y, a, b = after["box"]
            width, height = a - x, b - y
            tile, _ = encode_card(
                before,
                manifest["silhouette"],
                (width, height),
                duration_seconds(packet),
            )
            if tile is None:
                source = old.crop(tuple(before["box"]))
                if before["region"] == "G":
                    edges = [f["payload"] for f in before["facts"] if f["field"] == "directed_call_edge"]
                    ledger_lines = [f"{r['caller']} → {r['callee']}" for r in edges] or ["No selected directed edges."]
                    columns = max(1, width // 175)
                    ledger_lines = [
                        "     ".join(ledger_lines[i : i + columns]) for i in range(0, len(ledger_lines), columns)
                    ]
                    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
                    line_count = sum(len(fit_lines(measure, line, font(8), width - 20)) for line in ledger_lines)
                    ledger_height = 44 + 11 * line_count
                    if ledger_height >= height / 2:
                        raise DesignInfeasible("complete G edge key exceeds its allocated footprint")
                    tile = Image.new("RGB", (width, height), "white")
                    tile.paste(contain_tile(source, (width, height - ledger_height)), (0, 0))
                    ledger = text_tile(
                        "Caller → callee",
                        ledger_lines,
                        width,
                        ledger_height,
                        minimum=8,
                    )
                    if manifest["silhouette"] == "S_DENSITY_COMPACT":
                        ledger, _ = compact_white_corridors(ledger, 0, spec=manifest["density"]["spec"])
                    tile.paste(ledger, (0, height - ledger_height))
                else:
                    tile = contain_tile(source, (width, height))
            image.paste(tile, (x, y))
    result = png_bytes(image)
    sx, sy = size[0] / manifest["size"][0], size[1] / manifest["size"][1]
    header = {"box": [0, 0, size[0], round(size[1] * 0.095)]}
    if composition.startswith("D_SCALE_") or composition in {"D_COMPACT", "D_AIRY"}:
        original_header = manifest.get("header", {}).get(
            "box", [0, 0, old.width, round(manifest["base_height"] * 0.088)]
        )
        header = {"box": [round(v * (sx if i % 2 == 0 else sy)) for i, v in enumerate(original_header)]}
    return result, {
        **manifest,
        "composition": composition,
        "size": list(size),
        "cards": cards,
        "header": header,
        "source_size": manifest["size"],
        "source_to_output_scale": [sx, sy],
        "pixel_budget_delta": size[0] * size[1] - old.width * old.height,
        "image_sha256": hashlib.sha256(result).hexdigest(),
    }


def region_geometry(manifest):
    regions = defaultdict(list)
    for card in manifest["cards"]:
        regions[card["region"]].extend(card["boxes"])
    regions["header"] = [
        manifest.get("header", {}).get("box", [0, 0, manifest["size"][0], int(manifest["size"][1] * 0.08)])
    ]
    return dict(regions)

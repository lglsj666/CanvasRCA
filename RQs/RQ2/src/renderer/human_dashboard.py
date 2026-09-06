"""Human-readable composite renderer for the RQ2 dashboard design space.

The audit unit remains an atomic fact.  The visual unit is a coordinated panel
that can contain several compatible facts.  This is intentionally separate
from the sparse one-fact-per-panel control retained in ``designs.py``.
"""

from __future__ import annotations

import io
import math
import statistics
from contextvars import ContextVar
from dataclasses import asdict
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont
from unified_scripts import stable_hash

REGION_NAMES = {
    "M": "METRICS · ALIGNED ANOMALY LANES",
    "R": "TRACES · RATE / EXCLUSIVE LATENCY",
    "L": "LOGS · COMPRESSED EVENT PATTERNS",
    "G": "TOPOLOGY · CALL EDGES / PROPAGATION",
}
BG = "#eef3f7"
PANEL = "#ffffff"

# The original composite renderer used 8--11 pt detail labels even on a
# 3,228-pixel-wide canvas.  That made tick labels and legends difficult to
# read after the whole dashboard was fitted to a normal screen.  Keep a
# renderer-wide readability baseline, then apply the registered relative
# ``legibility_scale`` on top of it.  ContextVar keeps concurrent renders from
# leaking one design's scale into another.
_BASE_FONT_SCALE = 1.18
_FONT_SCALE: ContextVar[float] = ContextVar("rq2_dashboard_font_scale", default=_BASE_FONT_SCALE)


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    try:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        scaled = round(float(size) * _FONT_SCALE.get())
        return ImageFont.truetype(name, max(9, scaled))
    except OSError:
        return ImageFont.load_default()


def _palette(name: str) -> dict[str, str]:
    if name == "colorblind":
        return {
            "text": "#111827", "muted": "#52616b", "border": "#9aa9b4",
            "grid": "#dce4e9", "metric": "#0072b2", "fault": "#f6c7b7",
            "edge": "#d55e00", "node": "#f0e442", "missing": "#aeb8c0",
            "base": "#009e73", "current": "#cc79a7",
        }
    return {
        "text": "#15242d", "muted": "#5c6c76", "border": "#8fa0aa",
        "grid": "#dfe7eb", "metric": "#1f78b4", "fault": "#f8d7cd",
        "edge": "#df5b3f", "node": "#f2bd5c", "missing": "#aeb8c0",
        "base": "#2a9d8f", "current": "#d1495b",
    }


def _tile_bbox(spec: Any, placement: Any) -> tuple[int, int, int, int]:
    left = spec.gutter_px + placement.column * (spec.cell_edge_px + spec.gutter_px)
    top = spec.header_px + spec.gutter_px + placement.row * (spec.cell_edge_px + spec.gutter_px)
    width = placement.width_cells * spec.cell_edge_px + (placement.width_cells - 1) * spec.gutter_px
    height = placement.height_cells * spec.cell_edge_px + (placement.height_cells - 1) * spec.gutter_px
    return left, top, left + width, top + height


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None or value == "":
        return "missing"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "-" if number < 0 else ""
    number = abs(number)
    for scale, suffix in ((1e9, "G"), (1e6, "M"), (1e3, "k")):
        if number >= scale:
            return f"{sign}{number / scale:.{digits}g}{suffix}"
    return f"{sign}{number:.{digits}g}"


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    words = str(text).split()
    if not words:
        return [""]
    rows: list[str] = []
    line = words[0]
    for word in words[1:]:
        candidate = f"{line} {word}"
        if draw.textlength(candidate, font=font) <= width:
            line = candidate
        else:
            rows.append(line)
            line = word
    rows.append(line)
    return rows


def _lossless_fit(
    draw: ImageDraw.ImageDraw, text: str, width: int, *, start: int = 15, floor: int = 9,
) -> tuple[ImageFont.ImageFont, list[str]]:
    for size in range(start, floor - 1, -1):
        font = _font(size)
        rows = _wrap(draw, text, font, width)
        if len(rows) <= 2:
            return font, rows
    return _font(floor), _wrap(draw, text, _font(floor), width)


def _single_line_font(
    draw: ImageDraw.ImageDraw, text: str, width: int, *, start: int = 12, floor: int = 8,
) -> ImageFont.ImageFont:
    for size in range(start, floor - 1, -1):
        font = _font(size)
        if draw.textlength(text, font=font) <= width:
            return font
    return _font(floor)


def _dashed(
    draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float],
    *, fill: str, width: int = 2, dash: int = 8,
) -> None:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length <= 0:
        return
    ux, uy = dx / length, dy / length
    cursor = 0.0
    while cursor < length:
        stop = min(length, cursor + dash)
        draw.line((start[0] + ux * cursor, start[1] + uy * cursor,
                   start[0] + ux * stop, start[1] + uy * stop), fill=fill, width=width)
        cursor += dash * 1.8


def _fault_bins(facts: Sequence[Mapping[str, Any]]) -> tuple[float, float] | None:
    window = next((fact for fact in facts if fact.get("field") == "estimated_fault_window"), None)
    duration = next((fact for fact in facts if fact.get("field") == "observation_window"), None)
    if not window or not duration:
        return None
    try:
        seconds = float((duration.get("payload") or {})["duration_rel_s"])
        start = float(str((window.get("payload") or {})["start"]).lstrip("+").rstrip("m")) * 60
        end = float(str((window.get("payload") or {})["end"]).lstrip("+").rstrip("m")) * 60
        return max(0.0, min(63.0, 63 * start / seconds)), max(0.0, min(63.0, 63 * end / seconds))
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def _metric_z(payload: Mapping[str, Any], values: Sequence[float | None]) -> list[float | None]:
    met = payload.get("sircl_met_z") or {}
    try:
        center, spread = float(met["regular_mean"]), abs(float(met["regular_std_dev"]))
    except (KeyError, TypeError, ValueError):
        numeric = [value for value in values if value is not None]
        center = statistics.median(numeric) if numeric else 0.0
        deviations = [abs(value - center) for value in numeric]
        spread = 1.4826 * statistics.median(deviations) if deviations else 1.0
    if spread < 1e-12:
        numeric = [value for value in values if value is not None]
        spread = max((abs(value - center) for value in numeric), default=0.0)
        if spread < 1e-12:
            # A genuinely constant series has a well-defined visual shape: a
            # horizontal 0-sigma line.  Use a neutral unit denominator instead
            # of treating absent variation as a rendering failure.
            spread = 1.0
    return [None if value is None else (value - center) / spread for value in values]


def _metric_panel(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int],
    facts: Sequence[Mapping[str, Any]], encoding: str, colors: Mapping[str, str],
    scale_policy: str,
) -> dict[str, list[dict[str, Any]]]:
    x0, y0, x1, y1 = box
    rows = [fact for fact in facts if fact.get("field") == "metric_series_64"]
    meta = [fact for fact in facts if fact not in rows]
    result = {str(fact["fact_id"]): [] for fact in facts}
    if not rows:
        draw.text((x0 + 18, y0 + 55), "No metric series in this evidence card.", font=_font(15), fill=colors["muted"])
        return result
    context_parts = []
    context_parts.append(
        "scale=baseline z, clipped ±12σ" if scale_policy == "common_robust"
        else "scale=local raw range"
    )
    for fact in meta:
        payload = fact.get("payload") or {}
        if fact.get("field") == "estimated_fault_window":
            context_parts.append(f"fault window {payload.get('start')}…{payload.get('end')}")
        elif fact.get("field") == "observation_window":
            context_parts.append(f"duration {_fmt(payload.get('duration_rel_s'))}s · source rows {payload.get('source_metric_rows')}")
    context_text = " · ".join(context_parts)
    content_top, content_bottom = y0 + 68, y1 - 31
    lane_h = max(72, (content_bottom - content_top) // len(rows))
    label_w = min(260, max(190, (x1 - x0) // 4))
    plot_left, plot_right = x0 + label_w, x1 - 16
    fault = _fault_bins(facts)
    if encoding == "overlay_lines":
        if scale_policy != "common_robust":
            raise ValueError("overlay metric panels require the shared baseline-z scale")
        series_colors = (
            "#0072B2", "#D55E00", "#009E73", "#CC79A7",
            "#E69F00", "#56B4E9", "#000000", "#7A5195",
        )
        columns = 2 if len(rows) > 4 else 1
        per_column = math.ceil(len(rows) / columns)
        legend_row_h = 68
        legend_top = y0 + 81
        legend_bottom = legend_top + per_column * legend_row_h
        if legend_bottom > y1 - 185:
            raise ValueError("dense metric card is too short for its legend and plot")
        column_width = (x1 - x0 - 28) / columns
        draw.text(
            (x0 + 14, y0 + 39),
            f"{len(rows)} aligned series on one shared baseline-z axis · exact raw anchors in legend",
            font=_single_line_font(
                draw,
                f"{len(rows)} aligned series on one shared baseline-z axis · exact raw anchors in legend",
                x1 - x0 - 28, start=12, floor=8,
            ), fill=colors["muted"],
        )
        if context_text:
            context_font = _single_line_font(draw, context_text, x1 - x0 - 28, start=11, floor=8)
            if draw.textlength(context_text, font=context_font) > x1 - x0 - 28:
                raise ValueError("metric context cannot fit its registered silhouette")
            draw.text((x0 + 14, y0 + 60), context_text, font=context_font, fill=colors["muted"])
        for index, fact in enumerate(rows):
            payload = fact.get("payload") or {}
            column, local_row = index // per_column, index % per_column
            lx = x0 + 14 + column * column_width
            ly = legend_top + local_row * legend_row_h
            color = series_colors[index % len(series_colors)]
            draw.line((lx, ly + 8, lx + 28, ly + 8), fill=color, width=4)
            draw.ellipse((lx + 11, ly + 4, lx + 19, ly + 12), fill=color)
            label = f"{payload.get('panel_id')} {payload.get('service')} · {payload.get('metric')}"
            label_font, label_lines = _lossless_fit(
                draw, label, int(column_width - 48), start=12, floor=8,
            )
            if len(label_lines) > 2:
                raise ValueError("dense metric legend cannot fit without losing its full label")
            for line_index, line in enumerate(label_lines):
                draw.text(
                    (lx + 36, ly + line_index * (label_font.size + 1)),
                    line, font=label_font, fill=colors["text"],
                )
            anchor = (
                f"base {_fmt(payload.get('baseline'))}  peak {_fmt(payload.get('peak'))}  "
                f"z {_fmt(payload.get('signed_z'))}"
            )
            draw.text(
                (lx + 36, ly + 43), anchor,
                font=_single_line_font(draw, anchor, int(column_width - 48), start=10, floor=8),
                fill=colors["muted"],
            )
        graph_left, graph_right = x0 + 62, x1 - 18
        graph_top, graph_bottom = legend_bottom + 15, y1 - 50
        if graph_bottom - graph_top < 110:
            raise ValueError("overlay metric legend leaves insufficient plot height")
        if fault:
            fx0 = graph_left + fault[0] / 63 * (graph_right - graph_left)
            fx1 = graph_left + fault[1] / 63 * (graph_right - graph_left)
            draw.rectangle((fx0, graph_top, fx1, graph_bottom), fill=colors["fault"])
        for level in (-12, -10, 0, 10, 12):
            gy = graph_bottom - (level + 12) / 24 * (graph_bottom - graph_top)
            draw.line((graph_left, gy, graph_right, gy), fill=colors["grid"], width=1)
            if level in {-12, 0, 12}:
                draw.text((x0 + 15, gy - 8), f"{level:+d}σ" if level else "0", font=_font(12), fill=colors["muted"])
        for row_index, fact in enumerate(rows):
            payload = fact.get("payload") or {}
            values: list[float | None] = []
            for raw in payload.get("values") or ():
                try:
                    values.append(float(raw))
                except (TypeError, ValueError):
                    values.append(None)
            display_values = _metric_z(payload, values)
            color = series_colors[row_index % len(series_colors)]
            previous: tuple[int, tuple[float, float]] | None = None
            primitives: list[dict[str, Any]] = []
            for index, value in enumerate(display_values):
                x = graph_left + index / max(1, len(display_values) - 1) * (graph_right - graph_left)
                if value is None:
                    draw.rectangle((x - 1, graph_bottom + 3, x + 1, graph_bottom + 8), fill=colors["missing"])
                    primitives.append({"bin": index, "bbox": [x - 1, graph_bottom + 3, x + 1, graph_bottom + 8], "missing": True})
                    continue
                clipped = max(-12.0, min(12.0, value))
                y = graph_bottom - (clipped + 12) / 24 * (graph_bottom - graph_top)
                point = (x, y)
                if previous:
                    gap = index - previous[0]
                    if gap == 1:
                        draw.line((*previous[1], *point), fill=color, width=3)
                    elif gap <= 3:
                        _dashed(draw, previous[1], point, fill=color, width=2)
                if index % 8 == row_index % 8:
                    draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=color)
                if value < -12 or value > 12:
                    direction = -1 if value > 12 else 1
                    draw.polygon(((x, y), (x - 4, y + direction * 7), (x + 4, y + direction * 7)), fill=color)
                previous = index, point
                primitives.append({"bin": index, "point": [x, y], "display_value": value, "clipped": value < -12 or value > 12, "missing": False})
            result[str(fact["fact_id"])].append({
                "kind": "overlay_lines", "series_index": row_index,
                "bbox": [graph_left, graph_top, graph_right, graph_bottom],
                "bin_primitives": primitives,
            })
        draw.text((graph_left, y1 - 34), "b0", font=_font(13), fill=colors["muted"])
        draw.text((graph_right - 34, y1 - 34), "b63", font=_font(13), fill=colors["muted"])
        for fact in meta:
            result[str(fact["fact_id"])].append({"kind": "metric_context", "bbox": [x0 + 8, y0 + 31, x1 - 8, y0 + 52]})
        return result
    if context_text:
        context_font = _single_line_font(draw, context_text, x1 - x0 - 28, start=12, floor=8)
        if draw.textlength(context_text, font=context_font) > x1 - x0 - 28:
            raise ValueError("metric context cannot fit its registered silhouette")
        draw.text((x0 + 14, y0 + 40), context_text, font=context_font, fill=colors["muted"])
    for row_index, fact in enumerate(rows):
        payload = fact.get("payload") or {}
        top = content_top + row_index * lane_h
        bottom = min(content_bottom, top + lane_h - 6)
        title = f"{payload.get('panel_id')}  {payload.get('service')} · {payload.get('metric')}"
        font, title_rows = _lossless_fit(draw, title, label_w - 24, start=14)
        if len(title_rows) > 2:
            raise ValueError("metric label cannot fit its registered silhouette")
        ty = top + 3
        for line in title_rows:
            draw.text((x0 + 14, ty), line, font=font, fill=colors["text"])
            ty += font.size + 1
        summary_lines = [
            f"base {_fmt(payload.get('baseline'))} · peak {_fmt(payload.get('peak'))}",
            f"z {_fmt(payload.get('signed_z'))}",
        ]
        values: list[float | None] = []
        for raw in payload.get("values") or ():
            try:
                values.append(float(raw))
            except (TypeError, ValueError):
                values.append(None)
        robust_values = _metric_z(payload, values)
        if scale_policy == "common_robust":
            display_values = robust_values
            low, high = -12.0, 12.0
            axis_labels = ("+12σ", "0", "−12σ")
        else:
            numeric = [value for value in values if value is not None]
            low, high = (min(numeric), max(numeric)) if numeric else (0.0, 1.0)
            if high == low:
                high = low + 1.0
            display_values = values
            axis_labels = (_fmt(high), _fmt((high + low) / 2), _fmt(low))
        clip_signs = [
            0 if value is None or low <= value <= high else (1 if value > high else -1)
            for value in display_values
        ]
        offscale_count = sum(sign != 0 for sign in clip_signs)
        if offscale_count:
            summary_lines[1] += f" · off-scale bins {offscale_count}"
        for summary_index, summary in enumerate(summary_lines):
            summary_font = _single_line_font(draw, summary, label_w - 24, start=10, floor=7)
            if draw.textlength(summary, font=summary_font) > label_w - 24:
                raise ValueError("metric summary cannot fit its registered silhouette")
            draw.text(
                (x0 + 14, bottom - 34 + summary_index * 16), summary,
                font=summary_font, fill=colors["muted"],
            )
        strip_y, graph_top, graph_bottom = bottom - 18, top + 7, bottom - 31
        if fault:
            fx0 = plot_left + fault[0] / 63 * (plot_right - plot_left)
            fx1 = plot_left + fault[1] / 63 * (plot_right - plot_left)
            draw.rectangle((fx0, graph_top, fx1, strip_y), fill=colors["fault"])
        zero_y = (graph_top + graph_bottom) / 2
        for level in (-10, 0, 10):
            gy = zero_y - level / 12 * (graph_bottom - graph_top) / 2
            draw.line((plot_left, gy, plot_right, gy), fill=colors["grid"], width=1)
        primitives: list[dict[str, Any]] = []
        if encoding == "heatmap":
            cell = (plot_right - plot_left) / max(1, len(display_values))
            for index, value in enumerate(display_values):
                left = plot_left + index * cell
                right = plot_left + (index + 1) * cell
                if value is None:
                    color = colors["missing"]
                else:
                    level = (value - low) / (high - low)
                    strength = min(1.0, abs(level - .5) * 2)
                    color = colors["metric"] if level >= .5 else colors["base"]
                    if strength < .25:
                        color = colors["grid"]
                draw.rectangle((left, graph_top + 8, right, graph_bottom - 8), fill=color)
                primitives.append({"bin": index, "bbox": [left, graph_top + 8, right, graph_bottom - 8], "missing": value is None})
        else:
            previous: tuple[int, tuple[float, float]] | None = None
            for index, value in enumerate(display_values):
                x = plot_left + index / max(1, len(display_values) - 1) * (plot_right - plot_left)
                if value is None:
                    draw.rectangle((x - 1, strip_y, x + 1, strip_y + 5), fill=colors["missing"])
                    primitives.append({"bin": index, "bbox": [x - 1, strip_y, x + 1, strip_y + 5], "missing": True})
                    continue
                clipped = max(low, min(high, value))
                y = graph_bottom - (clipped - low) / (high - low) * (graph_bottom - graph_top)
                point = (x, y)
                if previous:
                    gap = index - previous[0]
                    if gap == 1:
                        draw.line((*previous[1], *point), fill=colors["metric"], width=3)
                    elif gap <= 3:
                        _dashed(draw, previous[1], point, fill=colors["metric"], width=2)
                draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=colors["metric"])
                is_clipped = value < low or value > high
                previous_sign = clip_signs[index - 1] if index else 0
                next_sign = clip_signs[index + 1] if index + 1 < len(clip_signs) else 0
                if is_clipped and (clip_signs[index] != previous_sign or clip_signs[index] != next_sign):
                    direction = -1 if value > high else 1
                    draw.polygon(((x, y), (x - 5, y + direction * 8), (x + 5, y + direction * 8)), fill=colors["current"])
                previous = index, point
                primitives.append({"bin": index, "point": [x, y], "display_value": value, "clipped": is_clipped, "missing": False})
        draw.text((plot_left + 3, graph_top), axis_labels[0], font=_font(12), fill=colors["muted"])
        draw.text((plot_left + 3, zero_y - 13), axis_labels[1], font=_font(12), fill=colors["muted"])
        draw.text((plot_left + 3, graph_bottom - 16), axis_labels[2], font=_font(12), fill=colors["muted"])
        draw.text((plot_left, bottom - 18), "b0", font=_font(13), fill=colors["muted"])
        draw.text((plot_right - 34, bottom - 18), "b63", font=_font(13), fill=colors["muted"])
        result[str(fact["fact_id"])].append({"kind": encoding, "bbox": [x0 + 8, top, x1 - 8, bottom], "bin_primitives": primitives})
    for fact in meta:
        result[str(fact["fact_id"])].append({"kind": "metric_context", "bbox": [x0 + 8, y0 + 31, x1 - 8, y0 + 52]})
    return result


def _trace_panel(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], facts: Sequence[Mapping[str, Any]],
    encoding: str, colors: Mapping[str, str],
) -> dict[str, list[dict[str, Any]]]:
    x0, y0, x1, y1 = box
    rows = [fact for fact in facts if fact.get("field") == "trace_summary_entry"]
    meta = [fact for fact in facts if fact not in rows]
    result = {str(fact["fact_id"]): [] for fact in facts}
    context_parts = []
    for fact in meta:
        payload = fact.get("payload") or {}
        if fact.get("field") == "trace_summary_meta":
            context_parts.append(f"services {payload.get('service_count')} · omitted {payload.get('omitted_services')}")
        elif fact.get("field") == "explicit_missingness":
            context_parts.append(f"traces missing={payload.get('traces_missing')}")
    if context_parts:
        draw.text((x0 + 14, y0 + 40), " · ".join(context_parts), font=_font(12), fill=colors["muted"])
    width = x1 - x0
    count_labels = [
        f"{(fact.get('payload') or {}).get('count_base')} → {(fact.get('payload') or {}).get('count_fault')}  "
        f"Δlog2={_fmt((fact.get('payload') or {}).get('count_lfc'))}"
        for fact in rows
    ]
    latency_labels = [
        f"{_fmt((fact.get('payload') or {}).get('exl_p95_base_ms'))} → "
        f"{_fmt((fact.get('payload') or {}).get('exl_p95_fault_ms'))}  "
        f"Δlog2={_fmt((fact.get('payload') or {}).get('latency_lfc'))}"
        for fact in rows
    ]
    count_font, latency_font = _font(13), _font(12)
    count_width = max((draw.textlength(value, font=count_font) for value in count_labels), default=0)
    latency_width = max((draw.textlength(value, font=latency_font) for value in latency_labels), default=0)
    table_layout = count_width <= width * .15 and latency_width <= width * .29
    header = (
        "entity / operation       count baseline → fault       exclusive p95 ms baseline → fault"
        if table_layout else
        "Each row: entity / operation; request count baseline → fault; exclusive p95 latency baseline → fault"
    )
    header_font = _single_line_font(draw, header, width - 28, start=13, floor=8)
    draw.text((x0 + 14, y0 + 61), header, font=header_font, fill=colors["muted"])
    top = y0 + 86
    row_h = max(30, (y1 - top - 18) // max(1, len(rows)))
    p95_values = [float((fact.get("payload") or {}).get(key) or 0) for fact in rows for key in ("exl_p95_base_ms", "exl_p95_fault_ms")]
    scale = math.log1p(max(p95_values or [1.0]))
    for index, fact in enumerate(rows):
        payload = fact.get("payload") or {}; y = top + index * row_h
        draw.line((x0 + 12, y + row_h - 2, x1 - 12, y + row_h - 2), fill=colors["grid"], width=1)
        operation = f"{payload.get('service')} · {payload.get('operation')}"
        operation_width = int(width * .47) if table_layout else width - 28
        font = _single_line_font(draw, operation, operation_width, start=15, floor=7)
        if draw.textlength(operation, font=font) > operation_width:
            raise ValueError("trace entity/operation label cannot fit its registered silhouette")
        draw.text((x0 + 14, y + 3), operation, font=font, fill=colors["text"])
        value_y = y + max(7, min(18, row_h // 5))
        count_label = f"{payload.get('count_base')} → {payload.get('count_fault')}  Δlog2={_fmt(payload.get('count_lfc'))}"
        base, fault = float(payload.get("exl_p95_base_ms") or 0), float(payload.get("exl_p95_fault_ms") or 0)
        label = f"{_fmt(base)} → {_fmt(fault)}  Δlog2={_fmt(payload.get('latency_lfc'))}"
        if table_layout:
            draw.text((x0 + width * .51, value_y), count_label, font=count_font, fill=colors["text"])
            draw.text((x0 + width * .68, value_y - 4), label, font=latency_font, fill=colors["text"])
            left, right = x0 + width * .69, x1 - 18
        else:
            count_y, latency_y = y + 25, y + 43
            compact_count = _single_line_font(draw, f"count {count_label}", width - 28, start=12, floor=8)
            compact_latency = _single_line_font(draw, f"exclusive p95 ms {label}", width - 28, start=11, floor=8)
            draw.text((x0 + 14, count_y), f"count {count_label}", font=compact_count, fill=colors["text"])
            draw.text((x0 + 14, latency_y), f"exclusive p95 ms {label}", font=compact_latency, fill=colors["text"])
            left, right = x0 + width * .53, x1 - 18
        xb = left + math.log1p(base) / max(scale, 1e-9) * (right - left)
        xf = left + math.log1p(fault) / max(scale, 1e-9) * (right - left)
        if encoding == "trace_baseline_fault_bars":
            bar_y = y + max(31, row_h - 14 if not table_layout else row_h - 25)
            draw.line((left, bar_y - 4, xb, bar_y - 4), fill=colors["base"], width=5)
            draw.line((left, bar_y + 4, xf, bar_y + 4), fill=colors["current"], width=5)
        else:
            bar_y = y + max(29, row_h - 14 if not table_layout else row_h - 25)
            draw.line((xb, bar_y, xf, bar_y), fill=colors["border"], width=2)
            draw.ellipse((xb - 4, bar_y - 4, xb + 4, bar_y + 4), fill=colors["base"])
            draw.ellipse((xf - 4, bar_y - 4, xf + 4, bar_y + 4), fill=colors["current"])
        result[str(fact["fact_id"])].append({"kind": encoding, "bbox": [x0 + 10, y, x1 - 10, y + row_h]})
    for fact in meta:
        result[str(fact["fact_id"])].append({"kind": "trace_context", "bbox": [x0 + 8, y0 + 29, x1 - 8, y0 + 52]})
    return result


def _log_panel(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], facts: Sequence[Mapping[str, Any]],
    encoding: str, colors: Mapping[str, str],
) -> dict[str, list[dict[str, Any]]]:
    x0, y0, x1, y1 = box
    rows = [fact for fact in facts if fact.get("field") == "denum_log_template"]
    meta = [fact for fact in facts if fact not in rows]
    result = {str(fact["fact_id"]): [] for fact in facts}
    top = y0 + 54
    if not rows:
        draw.text((x0 + 15, top), "No retained log pattern; explicit missingness is preserved.", font=_font(12), fill=colors["muted"])
    content_bottom = y1 - (34 if meta else 8)
    row_h = (content_bottom - top) // max(1, len(rows))
    if rows and row_h < 64:
        raise ValueError("log rows cannot fit their registered silhouette")
    for index, fact in enumerate(rows):
        payload = fact.get("payload") or {}; y = top + index * row_h
        draw.line((x0 + 12, y + row_h - 2, x1 - 12, y + row_h - 2), fill=colors["grid"], width=1)
        lead = f"{payload.get('template_id')}  entity {payload.get('entity_id')}  b{payload.get('relative_bin')}  count {payload.get('count')}  level {payload.get('level')}"
        template = str(payload.get("template") or "")
        preview = payload.get("numeric_preview") or {}
        preview_text = ""
        if preview:
            preview_text = "numeric " + "; ".join(
                f"{name}: first={row.get('first')} last={row.get('last')} n={row.get('sample_count')}"
                for name, row in sorted(preview.items()) if isinstance(row, Mapping)
            )
        log_r = payload.get("log_r") or {}
        change = ""
        if log_r:
            components = ", ".join(map(str, log_r.get("components") or ())) or "none"
            change = (
                f"LOG-R  error rate {_fmt(log_r.get('error_rate_base'))}→{_fmt(log_r.get('error_rate_fault'))}  "
                f"event rate {_fmt(log_r.get('log_rate_base'))}→{_fmt(log_r.get('log_rate_fault'))}  signals {components}"
            )
        timeline_y = y + row_h - 30
        text_blocks = [
            (lead, True, colors["text"]), (template, False, colors["text"]),
            *(([(change, False, colors["current"])]) if change else []),
            *(([(preview_text, False, colors["muted"])]) if preview_text else []),
        ]
        fitted = None
        for size in range(14, 6, -1):
            normal, bold = _font(size), _font(size, True)
            wrapped = [(_wrap(draw, text, bold if is_bold else normal, x1 - x0 - 28), is_bold, color) for text, is_bold, color in text_blocks]
            line_height = max(10, normal.getbbox("Ag")[3] - normal.getbbox("Ag")[1] + 2)
            if sum(len(lines) for lines, _bold, _color in wrapped) * line_height <= timeline_y - y - 10:
                fitted = normal, bold, wrapped, line_height
                break
        if fitted is None:
            raise ValueError("log text cannot fit its registered silhouette")
        normal, bold, wrapped, line_height = fitted
        cursor = y + 3
        for lines, is_bold, color in wrapped:
            for line in lines:
                draw.text((x0 + 14, cursor), line, font=bold if is_bold else normal, fill=color)
                cursor += line_height
        if log_r and row_h >= 240 and timeline_y - cursor >= 125:
            # A sparse case may contain only one retained template.  Use the
            # otherwise empty middle of its silhouette to visualize the
            # already-present LOG-R rate facts; this adds no evidence and
            # avoids concentrating every glyph in the first few lines.
            chart_top = cursor + 8
            chart_bottom = timeline_y - 25
            draw.rounded_rectangle(
                (x0 + 14, chart_top, x1 - 14, chart_bottom), radius=8,
                fill="#f8fafb", outline=colors["grid"], width=2,
            )
            draw.text((x0 + 28, chart_top + 12), "LOG-R RATE COMPARISON", font=_font(14, True), fill=colors["muted"])
            chart_left, chart_right = x0 + 190, x1 - 34
            measures = (
                ("error rate", log_r.get("error_rate_base"), log_r.get("error_rate_fault")),
                ("event rate", log_r.get("log_rate_base"), log_r.get("log_rate_fault")),
            )
            available = max(80, chart_bottom - chart_top - 46)
            for measure_index, (label, base_value, fault_value) in enumerate(measures):
                row_y = chart_top + 43 + (measure_index + .5) * available / len(measures)
                try:
                    base_number = max(0.0, float(base_value or 0.0))
                    fault_number = max(0.0, float(fault_value or 0.0))
                except (TypeError, ValueError):
                    base_number = fault_number = 0.0
                scale = max(base_number, fault_number, 1e-12)
                base_x = chart_left + base_number / scale * (chart_right - chart_left)
                fault_x = chart_left + fault_number / scale * (chart_right - chart_left)
                draw.text((x0 + 28, row_y - 13), label, font=_font(14, True), fill=colors["text"])
                draw.line((chart_left, row_y - 5, chart_right, row_y - 5), fill=colors["grid"], width=2)
                draw.line((chart_left, row_y + 7, chart_right, row_y + 7), fill=colors["grid"], width=2)
                draw.line((chart_left, row_y - 5, base_x, row_y - 5), fill=colors["base"], width=8)
                draw.line((chart_left, row_y + 7, fault_x, row_y + 7), fill=colors["current"], width=8)
                draw.text(
                    (chart_left, row_y + 15),
                    f"baseline {_fmt(base_number)}   fault {_fmt(fault_number)}",
                    font=_font(12), fill=colors["muted"],
                )
        left, right = x0 + 16, x1 - 18
        draw.line((left, timeline_y, right, timeline_y), fill=colors["grid"], width=3)
        active = max(0, min(63, int(payload.get("relative_bin") or 0)))
        active_x = left + active / 63 * (right - left)
        draw.ellipse((active_x - 6, timeline_y - 6, active_x + 6, timeline_y + 6), fill=colors["current"])
        draw.text((left, timeline_y + 8), "b0", font=_font(12), fill=colors["muted"])
        draw.text((right - 31, timeline_y + 8), "b63", font=_font(12), fill=colors["muted"])
        if encoding == "template_time_matrix":
            left, right = x0 + (x1 - x0) * .72, x1 - 18
            cell = (right - left) / 64
            active = max(0, min(63, int(payload.get("relative_bin") or 0)))
            for bin_index in range(64):
                fill = colors["current"] if bin_index == active else colors["grid"]
                draw.rectangle((left + bin_index * cell, timeline_y - 11, left + (bin_index + 1) * cell, timeline_y - 5), fill=fill)
        result[str(fact["fact_id"])].append({"kind": encoding, "bbox": [x0 + 10, y, x1 - 10, y + row_h]})
    for fact in meta:
        payload = fact.get("payload") or {}
        meta_text = f"source events={payload.get('event_count', 'n/a')} · templates={payload.get('template_count', 'n/a')} · semantic round-trip={payload.get('semantic_round_trip', 'n/a')}"
        meta_font = _single_line_font(draw, meta_text, x1 - x0 - 28, start=11, floor=8)
        if draw.textlength(meta_text, font=meta_font) > x1 - x0 - 28:
            raise ValueError("log metadata cannot fit its registered silhouette")
        draw.text((x0 + 14, y1 - 20), meta_text, font=meta_font, fill=colors["muted"])
        result[str(fact["fact_id"])].append({"kind": "log_context", "bbox": [x0 + 10, y1 - 20, x1 - 10, y1 - 5]})
    return result


def _arrow(draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float], color: str) -> None:
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    draw.line((*start, *end), fill=color, width=3)
    for offset in (-.48, .48):
        tip = (end[0] - 11 * math.cos(angle + offset), end[1] - 11 * math.sin(angle + offset))
        draw.line((*end, *tip), fill=color, width=3)


def _shortened_edge(
    start: tuple[float, float], end: tuple[float, float], padding: float = 31.0,
) -> tuple[tuple[float, float], tuple[float, float]]:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length <= 2 * padding:
        return start, end
    ux, uy = dx / length, dy / length
    return ((start[0] + ux * padding, start[1] + uy * padding),
            (end[0] - ux * padding, end[1] - uy * padding))


def _graph_positions(nodes: Sequence[str], edges: Sequence[tuple[str, str]], box: tuple[int, int, int, int]) -> dict[str, tuple[float, float]]:
    x0, y0, x1, y1 = box
    indegree = {node: 0 for node in nodes}; outgoing = {node: [] for node in nodes}
    for caller, callee in edges:
        outgoing.setdefault(caller, []).append(callee); indegree[callee] = indegree.get(callee, 0) + 1
    level = {node: 0 for node in nodes}; queue = sorted(node for node in nodes if indegree.get(node, 0) == 0)
    visited = set()
    while queue:
        node = queue.pop(0); visited.add(node)
        for child in sorted(outgoing.get(node, ())):
            level[child] = max(level.get(child, 0), level[node] + 1)
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(visited) != len(nodes):
        level = {node: index % 3 for index, node in enumerate(nodes)}
    groups: dict[int, list[str]] = {}
    for node in nodes:
        groups.setdefault(level.get(node, 0), []).append(node)
    max_level = max(groups or {0: []})
    positions = {}
    for layer, values in sorted(groups.items()):
        x = x0 + (layer + .5) / (max_level + 1) * (x1 - x0)
        for index, node in enumerate(sorted(values)):
            y = y0 + (index + 1) / (len(values) + 1) * (y1 - y0)
            positions[node] = (x, y)
    return positions


def _topology_panel(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], facts: Sequence[Mapping[str, Any]],
    encoding: str, propagation_encoding: str, colors: Mapping[str, str],
) -> dict[str, list[dict[str, Any]]]:
    x0, y0, x1, y1 = box
    edge_facts = [fact for fact in facts if fact.get("field") == "directed_call_edge"]
    prop_facts = sorted(
        (fact for fact in facts if fact.get("field") == "propagation_service"),
        key=lambda fact: int((fact.get("payload") or {}).get("rank") or 10**9),
    )
    meta = [fact for fact in facts if fact not in edge_facts and fact not in prop_facts]
    result = {str(fact["fact_id"]): [] for fact in facts}
    split = x0 + int((x1 - x0) * .55)

    def draw_edge_grid(
        area: tuple[float, float, float, float], *, start_size: int = 13,
    ) -> dict[str, list[float]]:
        left, top, right, bottom = area
        labels = [f"{fact['payload']['caller']} → {fact['payload']['callee']}" for fact in edge_facts]
        if not labels:
            return {}
        selected: tuple[int, int, ImageFont.ImageFont, int] | None = None
        for columns in range(1, min(5, len(labels)) + 1):
            rows = math.ceil(len(labels) / columns)
            cell_width = (right - left) / columns
            widest = max(labels, key=lambda value: draw.textlength(value, font=_font(start_size)))
            font = _single_line_font(draw, widest, int(cell_width - 8), start=start_size, floor=8)
            line_height = max(12, font.getbbox("Ag")[3] - font.getbbox("Ag")[1] + 3)
            if draw.textlength(widest, font=font) <= cell_width - 8 and rows * line_height <= bottom - top:
                selected = columns, rows, font, line_height
                break
        if selected is None:
            raise ValueError("directed-edge table cannot fit its registered topology silhouette")
        columns, rows, font, line_height = selected
        cell_width = (right - left) / columns
        geometry: dict[str, list[float]] = {}
        for index, fact in enumerate(edge_facts):
            column, row = index // rows, index % rows
            ex, ey = left + column * cell_width, top + row * line_height
            label = labels[index]
            draw.text((ex, ey), label, font=font, fill=colors["text"])
            geometry[str(fact["fact_id"])] = [ex, ey, ex + draw.textlength(label, font=font), ey + line_height]
        return geometry

    context_parts = []
    for fact in meta:
        payload = fact.get("payload") or {}
        if fact.get("field") == "propagation_meta":
            context_parts.append(
                f"mode={payload.get('mode')} · selection={payload.get('selection_mode')} · "
                f"omitted services={payload.get('omitted_services')} · omitted edges={payload.get('omitted_edges')} · "
                f"context={','.join(map(str, payload.get('context_services') or ())) or 'none'}"
            )
        elif fact.get("field") == "explicit_missingness":
            context_parts.append(f"propagation missing={payload.get('propagation_missing')}")
    if context_parts:
        font, lines = _lossless_fit(draw, " · ".join(context_parts), x1 - x0 - 28, start=11, floor=9)
        for index, line in enumerate(lines[:2]):
            draw.text((x0 + 14, y0 + 33 + index * (font.size + 1)), line, font=font, fill=colors["muted"])
    graph_box = (x0 + 16, y0 + 84, split - 15, y0 + int((y1 - y0) * .67))
    edge_rows_top = graph_box[3] + 12
    edges = [(str(fact["payload"]["caller"]), str(fact["payload"]["callee"])) for fact in edge_facts]
    nodes = sorted({node for edge in edges for node in edge})
    if encoding == "adjacency_matrix" and nodes:
        size = max(10, min((graph_box[2] - graph_box[0] - 70) // len(nodes), (graph_box[3] - graph_box[1] - 30) // len(nodes)))
        left, top = graph_box[0] + 65, graph_box[1] + 20
        index = {node: i for i, node in enumerate(nodes)}
        for i, node in enumerate(nodes):
            draw.text((left + i * size, graph_box[1]), node, font=_font(10), fill=colors["text"])
            draw.text((graph_box[0], top + i * size), node, font=_font(10), fill=colors["text"])
        for fact in edge_facts:
            caller, callee = str(fact["payload"]["caller"]), str(fact["payload"]["callee"])
            cell = (left + index[callee] * size, top + index[caller] * size,
                    left + (index[callee] + 1) * size - 1, top + (index[caller] + 1) * size - 1)
            draw.rectangle(cell, fill=colors["edge"])
            result[str(fact["fact_id"])].append({"kind": "matrix_cell", "bbox": list(cell)})
    elif encoding == "edge_table":
        edge_geometry = draw_edge_grid(graph_box, start_size=13)
        for fact in edge_facts:
            result[str(fact["fact_id"])].append({
                "kind": "edge_table_row", "bbox": edge_geometry[str(fact["fact_id"])],
            })
    elif nodes:
        positions = _graph_positions(nodes, edges, graph_box)
        for fact in edge_facts:
            caller, callee = str(fact["payload"]["caller"]), str(fact["payload"]["callee"])
            start, end = _shortened_edge(positions[caller], positions[callee])
            _arrow(draw, start, end, colors["edge"])
            result[str(fact["fact_id"])].append({"kind": "directed_arrow", "start": list(start), "end": list(end)})
        for node, (x, y) in positions.items():
            draw.rounded_rectangle((x - 27, y - 14, x + 27, y + 14), radius=8, fill=colors["node"], outline=colors["border"], width=2)
            draw.text((x - draw.textlength(node, font=_font(12, True)) / 2, y - 8), node, font=_font(12, True), fill=colors["text"])
    else:
        draw.text((graph_box[0], graph_box[1]), "No directed edges among displayed entities.", font=_font(11), fill=colors["muted"])

    draw.text((x0 + 16, edge_rows_top), "EXACT EDGE LEDGER  caller → callee", font=_font(12, True), fill=colors["muted"])
    ledger_geometry = draw_edge_grid(
        (x0 + 16, edge_rows_top + 19, split - 15, y1 - 12), start_size=12,
    )
    for fact in edge_facts:
        if not result[str(fact["fact_id"])]:
            result[str(fact["fact_id"])].append({
                "kind": "edge_ledger", "bbox": ledger_geometry[str(fact["fact_id"])],
            })

    draw.line((split, y0 + 40, split, y1 - 12), fill=colors["grid"], width=2)
    draw.text((split + 16, y0 + 79), "EARLIEST ANOMALY ONSET", font=_font(13, True), fill=colors["muted"])
    prop_top = y0 + 105
    row_h = max(21, (y1 - prop_top - 24) // max(1, len(prop_facts)))
    onset_values = []
    for fact in prop_facts:
        raw = (fact.get("payload") or {}).get("onset_rel_min_display")
        try:
            onset_values.append(float(str(raw).lstrip("+").rstrip("m")))
        except (TypeError, ValueError):
            pass
    onset_low, onset_high = (min(onset_values), max(onset_values)) if onset_values else (0.0, 1.0)
    onset_span = onset_high - onset_low or 1.0
    for index, fact in enumerate(prop_facts):
        payload = fact.get("payload") or {}; y = prop_top + index * row_h
        rank = payload.get("rank")
        rank_text = "–" if rank is None else str(rank)
        onset_text = str(payload.get("onset_rel_min_display") or "none")
        text = (
            f"{rank_text:>2}.  {payload.get('service')}   onset {onset_text:>7}   "
            f"z {_fmt(payload.get('severity_z_display')):>6}   "
            f"src {payload.get('evidence_source_display') or 'none'}"
        )
        draw.text((split + 16, y), text, font=_font(13), fill=colors["text"])
        if propagation_encoding == "propagation_timeline":
            raw = payload.get("onset_rel_min_display")
            try:
                onset = float(str(raw).lstrip("+").rstrip("m"))
            except (TypeError, ValueError):
                onset = None
            line_left, line_right = split + int((x1 - split) * .66), x1 - 18
            line_y = y + row_h - 7
            draw.line((line_left, line_y, line_right, line_y), fill=colors["grid"], width=2)
            if onset is not None:
                ox = line_left + (onset - onset_low) / onset_span * (line_right - line_left)
                draw.ellipse((ox - 4, line_y - 4, ox + 4, line_y + 4), fill=colors["current"])
        draw.line((split + 14, y + row_h - 2, x1 - 14, y + row_h - 2), fill=colors["grid"], width=1)
        result[str(fact["fact_id"])].append({"kind": "propagation_row", "bbox": [split + 12, y, x1 - 12, y + row_h]})
    for fact in meta:
        result[str(fact["fact_id"])].append({"kind": "topology_context", "bbox": [x0 + 10, y0 + 28, x1 - 10, y0 + 67]})
    return result


def render_human_dashboard(packet: Mapping[str, Any], spec: Any, program: Any) -> tuple[bytes, dict[str, Any]]:
    """Render with the registered relative legibility factor."""

    baseline = float(getattr(spec, "typography_baseline_scale", _BASE_FONT_SCALE))
    font_token = _FONT_SCALE.set(baseline * float(spec.legibility_scale))
    try:
        return _render_human_dashboard(packet, spec, program)
    finally:
        _FONT_SCALE.reset(font_token)


def _render_human_dashboard(packet: Mapping[str, Any], spec: Any, program: Any) -> tuple[bytes, dict[str, Any]]:
    """Render a composite dashboard and its exact fact-to-primitive manifest."""

    colors = _palette(spec.style_skin)
    image = Image.new("RGB", spec.logical_canvas_size, BG)
    draw = ImageDraw.Draw(image)
    draw.text((spec.gutter_px, 8), "TELEMETRY DIAGNOSTIC OVERVIEW", font=_font(29, True), fill=colors["text"])
    draw.text((spec.gutter_px, 46), "M metrics · R traces · L logs · G directed topology · relative 64-bin time · missing ≠ zero", font=_font(15), fill=colors["muted"])
    scale_legend = (
        "baseline-z scale clipped at ±12σ; triangles bracket off-scale runs"
        if spec.metric_scale_policy == "common_robust"
        else "local raw-value scale"
    )
    draw.text(
        (spec.gutter_px, 69),
        f"Service, pod, and node names use case-local numeric IDs. Dashed links cross short missing gaps; {scale_legend}.",
        font=_font(13), fill=colors["muted"],
    )

    all_facts = {str(fact["fact_id"]): fact for fact in packet.get("facts") or ()}
    cards = {card.card_id: card for card in program.cards}
    silhouettes = {item.card_id: item for item in program.silhouettes}
    mapping: list[dict[str, Any]] = []
    card_rows: list[dict[str, Any]] = []
    for placement in program.placements:
        card, silhouette = cards[placement.card_id], silhouettes[placement.card_id]
        box = _tile_bbox(spec, placement)
        draw.rounded_rectangle(box, radius=10, fill=PANEL, outline=colors["border"], width=2)
        card_title = REGION_NAMES[card.region]
        if card.semantic_type == "metric_bundle" and silhouette.encoding == "overlay_lines":
            card_title = "METRICS · SHARED-AXIS MULTI-SERIES OVERLAY"
        marker_reserve = 122 if spec.coordination_mode in {"shared_entity", "shared_time"} else 0
        title_width = box[2] - box[0] - 28 - marker_reserve
        title_font = _single_line_font(draw, card_title, title_width, start=20, floor=9)
        if draw.textlength(card_title, font=title_font) > title_width:
            raise ValueError(f"card title cannot fit its silhouette: {card_title}")
        draw.text((box[0] + 14, box[1] + 9), card_title, font=title_font, fill=colors["text"])
        if spec.coordination_mode == "shared_entity":
            for index, entity in enumerate(card.entity_ids[:6]):
                value = int(stable_hash({"entity": entity})[:6], 16)
                color = f"#{64 + value % 128:02x}{64 + (value >> 7) % 128:02x}{64 + (value >> 14) % 128:02x}"
                draw.rectangle((box[2] - 18 - index * 18, box[1] + 12, box[2] - 7 - index * 18, box[1] + 23), fill=color)
        elif spec.coordination_mode == "shared_time":
            marker_left, marker_right = box[2] - 116, box[2] - 12
            draw.line((marker_left, box[1] + 20, marker_right, box[1] + 20), fill=colors["border"], width=2)
            for fraction in (0, .25, .5, .75, 1):
                x = marker_left + fraction * (marker_right - marker_left)
                draw.line((x, box[1] + 16, x, box[1] + 24), fill=colors["border"], width=1)
        facts = [all_facts[fact_id] for fact_id in card.fact_ids]
        if card.semantic_type == "metric_bundle":
            geometry = _metric_panel(draw, box, facts, silhouette.encoding, colors, spec.metric_scale_policy)
        elif card.semantic_type == "trace_bundle":
            geometry = _trace_panel(draw, box, facts, silhouette.encoding, colors)
        elif card.semantic_type == "log_bundle":
            geometry = _log_panel(draw, box, facts, silhouette.encoding, colors)
        elif card.semantic_type == "topology_bundle":
            geometry = _topology_panel(draw, box, facts, silhouette.encoding, spec.propagation_encoding, colors)
        else:
            raise ValueError(f"human composite renderer received unsupported card {card.semantic_type}")
        for fact_id in card.fact_ids:
            mapping.append({
                "fact_id": fact_id, "card_id": card.card_id,
                "silhouette_id": silhouette.silhouette_id,
                "primitive": silhouette.encoding,
                "primitive_geometry": geometry.get(fact_id, []), "bbox": list(box),
            })
        card_rows.append({"card": asdict(card), "silhouette": asdict(silhouette), "placement": asdict(placement), "bbox": list(box)})

    expected = sorted(fact_id for card in program.cards for fact_id in card.fact_ids)
    if sorted(row["fact_id"] for row in mapping) != expected or len(mapping) != len(expected):
        raise ValueError("human composite render is not exact-once")
    def scale_geometry(value: Any, factor: float, key: str | None = None) -> Any:
        if isinstance(value, Mapping):
            return {name: scale_geometry(item, factor, str(name)) for name, item in value.items()}
        if isinstance(value, list):
            if key in {"bbox", "point", "start", "end"}:
                return [round(float(item) * factor) for item in value]
            return [scale_geometry(item, factor) for item in value]
        return value

    if spec.raster_scale != 1.0:
        image = image.resize(spec.canvas_size, Image.Resampling.LANCZOS)
        for row in mapping:
            row["bbox"] = scale_geometry(row["bbox"], spec.raster_scale, "bbox")
            row["primitive_geometry"] = scale_geometry(row["primitive_geometry"], spec.raster_scale)
        for row in card_rows:
            row["bbox"] = scale_geometry(row["bbox"], spec.raster_scale, "bbox")
    card_boxes = {row["card"]["card_id"]: row["bbox"] for row in card_rows}
    out_of_bounds: list[str] = []
    card_overflow: list[str] = []

    def geometry_boxes(value: Any) -> list[list[float]]:
        found: list[list[float]] = []
        if isinstance(value, Mapping):
            for name, item in value.items():
                if name == "bbox" and isinstance(item, list) and len(item) == 4:
                    found.append(item)
                elif name in {"point", "start", "end"} and isinstance(item, list) and len(item) == 2:
                    found.append([item[0], item[1], item[0], item[1]])
                else:
                    found.extend(geometry_boxes(item))
        elif isinstance(value, list):
            for item in value:
                found.extend(geometry_boxes(item))
        return found

    canvas_width, canvas_height = spec.canvas_size
    for row in mapping:
        owner = card_boxes[row["card_id"]]
        for primitive_box in geometry_boxes(row["primitive_geometry"]):
            if primitive_box[0] < 0 or primitive_box[1] < 0 or primitive_box[2] > canvas_width or primitive_box[3] > canvas_height:
                out_of_bounds.append(row["fact_id"])
            if primitive_box[0] < owner[0] or primitive_box[1] < owner[1] or primitive_box[2] > owner[2] or primitive_box[3] > owner[3]:
                card_overflow.append(row["fact_id"])
    out_of_bounds = sorted(set(out_of_bounds)); card_overflow = sorted(set(card_overflow))
    if out_of_bounds or card_overflow:
        raise ValueError(
            f"render geometry clipping detected: canvas={out_of_bounds}, card={card_overflow}"
        )
    stream = io.BytesIO(); image.save(stream, format="PNG", optimize=False, compress_level=6)
    selected = [all_facts[fact_id] for fact_id in expected]
    common = [fact for fact in packet.get("facts") or () if fact.get("region") == "C"]
    full_visible = sorted((*common, *selected), key=lambda fact: (str(fact.get("region")), str(fact.get("field")), str(fact.get("fact_id"))))
    manifest = {
        "schema_version": "CanvasRCARQ2HumanCompositeRenderManifestV1",
        "spec": asdict(spec), "cell_id": spec.cell_id,
        "program_hash": program.program_hash, "canvas_size": list(spec.canvas_size),
        "grid": {"columns": spec.grid_columns, "rows": spec.grid_rows, "logical_cell_edge_px": spec.cell_edge_px, "logical_gutter_px": spec.gutter_px, "raster_scale": spec.raster_scale},
        "cards": card_rows, "fact_mapping": mapping,
        "source_packet_fact_inventory_hash": packet["fact_inventory_hash"],
        "fact_inventory_hash": stable_hash(full_visible), "visual_fact_inventory_hash": stable_hash(selected),
        "selected_fact_id_hash": program.selected_fact_inventory_hash,
        "common_fact_inventory_hash": stable_hash(common),
        "card_silhouette_bijection": {"status": "passed", "cards": len(program.cards), "silhouettes": len(program.silhouettes)},
        "packing_audit": {"status": "passed", "mode": spec.packing_mode, "occupancy": program.occupancy, "empty_cells": program.empty_cells, "overlap_cells": 0, "footprint_downgrades": program.footprint_downgrades},
        "clipping_audit": {
            "status": "passed", "out_of_bounds_fact_ids": out_of_bounds,
            "card_local_overflow": bool(card_overflow), "card_overflow_fact_ids": card_overflow,
        },
        "label_blind": True,
    }
    manifest["manifest_sha256"] = stable_hash(manifest)
    return stream.getvalue(), manifest


__all__ = ["render_human_dashboard"]

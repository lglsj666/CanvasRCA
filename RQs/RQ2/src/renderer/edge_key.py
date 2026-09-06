"""Model-readable directional edge keys for propagation dashboards."""

from __future__ import annotations

import io
import math
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def propagation_rank_edges(manifest: Dict[str, Any]) -> List[Tuple[int, int]]:
    """Return all caller->callee edges whose endpoints are in shown rows."""
    propagation = next(
        panel for panel in manifest["panels"] if panel.get("kind") == "propagation"
    )
    rows = propagation.get("rows") or []
    ranks = {str(row["service"]): int(row["rank"]) for row in rows}
    edges = set()
    for row in rows:
        service = str(row["service"])
        for callee in row.get("callees") or []:
            if str(callee) in ranks:
                edges.add((ranks[service], ranks[str(callee)]))
        for caller in row.get("callers") or []:
            if str(caller) in ranks:
                edges.add((ranks[str(caller)], ranks[service]))
    return sorted(edges)


def propagation_identity_edges(manifest: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Return all direct caller->callee identity pairs among displayed rows."""
    propagation = next(
        panel for panel in manifest["panels"] if panel.get("kind") == "propagation"
    )
    rows = propagation.get("rows") or []
    shown = {str(row["service"]) for row in rows}
    edges: set[Tuple[str, str]] = set()
    for row in rows:
        service = str(row["service"])
        for callee in row.get("callees") or []:
            if str(callee) in shown:
                edges.add((service, str(callee)))
        for caller in row.get("callers") or []:
            if str(caller) in shown:
                edges.add((str(caller), service))
    return sorted(edges)


def identity_edge_key_extra_height(manifest: Dict[str, Any]) -> int:
    """Height for a lossless one-edge-per-line identity key."""
    return max(180, 104 + 31 * max(1, len(propagation_identity_edges(manifest))))


def identity_edge_key_horizontal_extra_height(
    manifest: Dict[str, Any], columns: int = 2
) -> int:
    """Height for a compact, complete, row-major direct-edge strip."""
    n_columns = max(1, int(columns))
    line_count = max(1, len(propagation_identity_edges(manifest)))
    rows = math.ceil(line_count / n_columns)
    return max(126, 76 + 24 * rows)


def edge_key_extra_height(variant: str) -> int:
    if variant == "compact":
        return 116
    if variant == "large":
        return 248
    if variant == "none":
        return 0
    raise ValueError(f"unknown topology edge-key variant {variant!r}")


def render_topology_edge_key(png: bytes, manifest: Dict[str, Any]) -> bytes:
    """Append a compact, directional rank-pair key without changing base pixels."""
    source = Image.open(io.BytesIO(png)).convert("RGB")
    strip_height = edge_key_extra_height("compact")
    output = Image.new("RGB", (source.width, source.height + strip_height), "white")
    output.paste(source, (0, 0))
    draw = ImageDraw.Draw(output)
    title_font = ImageFont.truetype(FONT_BOLD, 21)
    body_font = ImageFont.truetype(FONT, 18)
    y0 = source.height + 8
    draw.line(
        (40, source.height + 1, source.width - 40, source.height + 1),
        fill="#607d8b",
        width=2,
    )
    draw.text(
        (48, y0),
        "DIRECTED CALL-EDGE KEY — caller rank → callee rank",
        font=title_font,
        fill="#17212b",
    )
    edges = propagation_rank_edges(manifest)
    if edges:
        tokens = [f"{caller}→{callee}" for caller, callee in edges]
        midpoint = (len(tokens) + 1) // 2
        lines = ["   ".join(tokens[:midpoint]), "   ".join(tokens[midpoint:])]
    else:
        lines = ["none among the services shown in the propagation panel", ""]
    draw.text((48, y0 + 34), lines[0], font=body_font, fill="#263238")
    if lines[1]:
        draw.text((48, y0 + 64), lines[1], font=body_font, fill="#263238")
    buffer = io.BytesIO()
    output.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def render_topology_edge_key_large(png: bytes, manifest: Dict[str, Any]) -> bytes:
    """Append the qualified large key for low visual-token-count architectures."""
    source = Image.open(io.BytesIO(png)).convert("RGB")
    strip_height = edge_key_extra_height("large")
    output = Image.new("RGB", (source.width, source.height + strip_height), "white")
    output.paste(source, (0, 0))
    draw = ImageDraw.Draw(output)
    title_font = ImageFont.truetype(FONT_BOLD, 29)
    body_font = ImageFont.truetype(FONT_BOLD, 31)
    y0 = source.height + 9
    draw.rectangle(
        (32, source.height + 3, source.width - 32, output.height - 8),
        fill="#f5f9fc",
        outline="#455a64",
        width=3,
    )
    draw.text(
        (52, y0 + 6),
        "DIRECTED CALL-EDGE KEY — CALLER RANK → CALLEE RANK",
        font=title_font,
        fill="#10212f",
    )
    edges = propagation_rank_edges(manifest)
    if edges:
        tokens = [f"{caller}→{callee}" for caller, callee in edges]
        lines = [tokens[index : index + 5] for index in range(0, len(tokens), 5)]
    else:
        lines = [["NONE AMONG THE SERVICES SHOWN IN THE PROPAGATION PANEL"]]
    for index, line in enumerate(lines[:4]):
        draw.text(
            (52, y0 + 59 + index * 43),
            "     ".join(line),
            font=body_font,
            fill="#17212b",
        )
    buffer = io.BytesIO()
    output.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def render_topology_identity_edge_key_large(
    png: bytes,
    manifest: Dict[str, Any],
    *,
    numeric_ids: bool,
) -> Tuple[bytes, Dict[str, Any]]:
    """Append every direct edge using the same identities printed in panels.

    Unlike the legacy rank key, this key needs no separate row-number lookup.
    It is deliberately one edge per line and grows vertically rather than
    omitting relationships. The audit payload records the exact PIL bounds so
    an overlong natural-name pair cannot silently leave the canvas.
    """
    source = Image.open(io.BytesIO(png)).convert("RGB")
    edges = propagation_identity_edges(manifest)
    strip_height = identity_edge_key_extra_height(manifest)
    output = Image.new("RGB", (source.width, source.height + strip_height), "white")
    output.paste(source, (0, 0))
    draw = ImageDraw.Draw(output)
    y0 = source.height + 9
    draw.rectangle(
        (32, source.height + 3, source.width - 32, output.height - 8),
        fill="#f5f9fc",
        outline="#455a64",
        width=3,
    )
    title_font = ImageFont.truetype(FONT_BOLD, 27)
    title = (
        "DIRECTED CALL-EDGE KEY — CALLER ENTITY ID → CALLEE ENTITY ID"
        if numeric_ids
        else "DIRECTED CALL-EDGE KEY — CALLER SERVICE → CALLEE SERVICE"
    )
    draw.text((52, y0 + 4), title, font=title_font, fill="#10212f")
    legend = (
        "IDs are case-local: 3 digits=service · 4 digits=node · 5 digits=pod"
        if numeric_ids
        else "Each line is one incident-specific caller → callee relationship"
    )
    draw.text(
        (52, y0 + 40),
        legend,
        font=ImageFont.truetype(FONT, 17),
        fill="#455a64",
    )

    lines = [f"{caller} → {callee}" for caller, callee in edges]
    if not lines:
        lines = ["NONE AMONG THE SERVICES SHOWN IN THE PROPAGATION PANEL"]
    left, right = 52, source.width - 52
    font_size = 20
    while font_size > 12:
        candidate = ImageFont.truetype(FONT_BOLD, font_size)
        if max(draw.textbbox((0, 0), line, font=candidate)[2] for line in lines) <= right - left:
            break
        font_size -= 1
    body_font = ImageFont.truetype(FONT_BOLD, font_size)
    line_height = 31
    bounds = []
    clipped = False
    for index, line in enumerate(lines):
        xy = (left, y0 + 70 + index * line_height)
        bbox = draw.textbbox(xy, line, font=body_font)
        bounds.append(list(bbox))
        if bbox[0] < 0 or bbox[1] < source.height or bbox[2] > output.width or bbox[3] > output.height:
            clipped = True
        draw.text(xy, line, font=body_font, fill="#17212b")

    buffer = io.BytesIO()
    output.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue(), {
        "kind": "direct_identity_edge_key",
        "edge_count": len(edges),
        "font_size_px": font_size,
        "line_count": len(lines),
        "text_bounds_px": bounds,
        "canvas_px": [output.width, output.height],
        "off_canvas_clipped": clipped,
    }


def render_topology_identity_edge_key_horizontal(
    png: bytes,
    manifest: Dict[str, Any],
    *,
    numeric_ids: bool,
    columns: int = 2,
) -> Tuple[bytes, Dict[str, Any]]:
    """Append every direct edge in a balanced horizontal multi-column strip.

    The former one-edge-per-row key was intentionally oversized for a narrow
    perception probe. It made topology visually dominate the complete RCA
    dashboard. This production candidate preserves every relation, but lays
    them out row-major across the available width with evidence text at roughly
    the same pixel size as the Matplotlib detail typography.
    """
    source = Image.open(io.BytesIO(png)).convert("RGB")
    edges = propagation_identity_edges(manifest)
    n_columns = max(1, int(columns))
    strip_height = identity_edge_key_horizontal_extra_height(manifest, n_columns)
    output = Image.new("RGB", (source.width, source.height + strip_height), "white")
    output.paste(source, (0, 0))
    draw = ImageDraw.Draw(output)
    y0 = source.height + 7
    left = 42
    right = source.width - 42
    draw.rectangle(
        (32, source.height + 3, source.width - 32, output.height - 8),
        fill="#f8fafc",
        outline="#78909c",
        width=2,
    )

    title = "DIRECTED CALL EDGES — CALLER → CALLEE"
    draw.text(
        (left, y0 + 2),
        title,
        font=ImageFont.truetype(FONT_BOLD, 16),
        fill="#17212b",
    )
    legend = (
        "Case-local IDs: 3 digits=service · 4 digits=node · 5 digits=pod"
        if numeric_ids
        else "Each pair is one incident-specific caller → callee relationship"
    )
    draw.text(
        (left, y0 + 25),
        legend,
        font=ImageFont.truetype(FONT, 13),
        fill="#455a64",
    )

    lines = [f"{caller} → {callee}" for caller, callee in edges]
    if not lines:
        lines = ["NONE AMONG THE DISPLAYED PROPAGATION SERVICES"]
    rows = math.ceil(len(lines) / n_columns)
    cell_width = (right - left) / n_columns
    body_size = 14
    while body_size > 11:
        candidate = ImageFont.truetype(FONT, body_size)
        max_width = max(draw.textbbox((0, 0), line, font=candidate)[2] for line in lines)
        if max_width <= cell_width - 24:
            break
        body_size -= 1
    body_font = ImageFont.truetype(FONT, body_size)
    bounds = []
    clipped = False
    for index, line in enumerate(lines):
        row = index // n_columns
        column = index % n_columns
        xy = (int(left + column * cell_width), y0 + 51 + row * 24)
        bbox = draw.textbbox(xy, line, font=body_font)
        bounds.append(list(bbox))
        if (
            bbox[0] < 0
            or bbox[1] < source.height
            or bbox[2] > output.width
            or bbox[3] > output.height
        ):
            clipped = True
        draw.text(xy, line, font=body_font, fill="#17212b")

    buffer = io.BytesIO()
    output.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue(), {
        "kind": "direct_identity_edge_key",
        "layout": "horizontal",
        "columns": n_columns,
        "row_count": rows,
        "edge_count": len(edges),
        "font_size_px": body_size,
        "line_count": len(lines),
        "text_bounds_px": bounds,
        "canvas_px": [output.width, output.height],
        "off_canvas_clipped": clipped,
    }

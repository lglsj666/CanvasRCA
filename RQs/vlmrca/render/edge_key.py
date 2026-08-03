"""Model-readable directional edge keys for propagation dashboards."""

from __future__ import annotations

import io
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

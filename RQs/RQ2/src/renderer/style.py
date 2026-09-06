"""
Visual language for the dashboards.

Two constraints drive every choice here, both from the VLM-perception literature
rather than from human aesthetics:

* ChartQAPro shows the dominant VLM chart failure is legend/axis/curve
  correspondence, so series are labelled directly in their own panel title and
  a shared legend is never the only way to identify a series.
* VLMs read rasterised text far worse than humans at the same pixel size, so
  MIN_FONT_PT is a hard floor enforced by tests, not a suggestion.
"""

from __future__ import annotations

from dataclasses import dataclass

# Hard floor — below this, VLM transcription accuracy collapses. Enforced by
# tests/test_renderer_golden.py and probed by the render-reviewer agent.
MIN_FONT_PT = 7.0

FONT_TITLE = 12.0
FONT_PANEL_TITLE = 8.5
# Mean glyph advance as a fraction of the font size, used to budget panel-title
# characters against column width. Calibrated against the 3-column 1568px
# layout, which a vision review confirmed collision-free at ~54 title
# characters in a 324px column; a nominal 0.55 em would predict overflow there.
TITLE_CHAR_EM = 0.50
FONT_TICK = 7.0
FONT_ANNOT = 7.5
FONT_TABLE = 7.5

# Colour-blind-safe, high contrast on white. Colour never carries information
# alone; it always duplicates something stated in text.
NORMAL_LINE = "#3b6ea5"
ANOMALY_LINE = "#c1442e"
FAULT_SHADE = "#e8b4a8"
FAULT_SHADE_ALPHA = 0.35
GRID = "#d8d8d8"
TEXT = "#1a1a1a"
MUTED = "#666666"

# Topology node colouring by anomaly score (low → high).
NODE_CMAP = "OrRd"
NODE_EDGE = "#333333"

DPI = 100


@dataclass(frozen=True)
class Palette:
    normal: str = NORMAL_LINE
    anomaly: str = ANOMALY_LINE
    shade: str = FAULT_SHADE
    grid: str = GRID
    text: str = TEXT
    muted: str = MUTED


PALETTE = Palette()


@dataclass(frozen=True)
class Typography:
    """Resolved font sizes for one dashboard configuration."""

    title: float = FONT_TITLE
    panel_title: float = FONT_PANEL_TITLE
    tick: float = FONT_TICK
    annotation: float = FONT_ANNOT
    table: float = FONT_TABLE


DEFAULT_TYPOGRAPHY = Typography()


def resolve_typography(uniform_detail_font_pt: float = 0.0) -> Typography:
    """Return legacy typography or a VLM-readable uniform detail scale.

    The main incident title keeps a modest hierarchy. Every evidence-bearing
    detail below it—panel titles, axes, annotations, log rows, and trace rows—
    receives the same requested point size so topology does not win attention
    merely because its labels are larger.
    """
    if uniform_detail_font_pt <= 0:
        return DEFAULT_TYPOGRAPHY
    detail = max(float(uniform_detail_font_pt), MIN_FONT_PT)
    return Typography(
        title=max(FONT_TITLE, detail * 1.35),
        panel_title=detail,
        tick=detail,
        annotation=detail,
        table=detail,
    )


def apply_rc(mpl, typography: Typography = DEFAULT_TYPOGRAPHY) -> None:
    """Global matplotlib settings shared by every panel."""
    mpl.rcParams.update(
        {
            "figure.dpi": DPI,
            "savefig.dpi": DPI,
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#888888",
            "axes.linewidth": 0.6,
            "axes.titlesize": typography.panel_title,
            "axes.labelsize": typography.tick,
            "xtick.labelsize": typography.tick,
            "ytick.labelsize": typography.tick,
            "grid.color": GRID,
            "grid.linewidth": 0.4,
            "legend.fontsize": typography.tick,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            # Determinism: no hash-seed-dependent font fallback ordering.
            "svg.hashsalt": "vlmrca",
        }
    )

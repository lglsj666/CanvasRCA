"""Measured 4096-square preset. Existing registered components, no selector."""
import os
import subprocess
import tempfile
from pathlib import Path

from .operations.dashboard_policy import apply, validate, MAX_CARDS, SIDE
from .utils import RENDERER, ROOT, compile_design, node_link_layout, read, validate_evidence, write

PADDING, GAP, TOP = 24, 16, 86
PROFILE = "source_reflow_v3"


def default_components(evidence):
    defaults = {"metric": "metric.line", "trace": "trace.paired_bars", "log": "log.timeline",
                "graph": "graph.node_link", "inventory": "inventory.identities",
                "comparison": "comparison.paired", "events": "events.onset",
                "contrast": "contrast.quantile_contrast", "scope": "scope.matrix",
                "trace_profile": "trace_profile.quantiles", "literal": "literal.text"}
    out = {}
    for card in evidence["cards"]:
        kind, data = card["kind"], card["data"]
        if kind == "trace_joint":
            component = ("trace_joint.budget_complete" if "sampling_budget" in data else
                         "trace_joint.complete_marginals" if "complete" in data else "trace_joint.marginals")
        elif kind == "diagnostic":
            component = "diagnostic.compact" if data.get("sparse") else "diagnostic.matrix"
        else:
            component = defaults.get(kind)
        if component is None:
            raise ValueError(f"No fixed-canvas default component for {kind}; supply an explicit design")
        out[card["id"]] = component
    return out


def layout_from_measurements(evidence, components, measurements):
    """Choose readable columns with greatest measured content area.

    Heights come from real component DOM. Do not shrink or remove evidence.
    """
    validate_evidence(evidence)
    cards = evidence["cards"]
    if len(cards) > MAX_CARDS:
        raise ValueError("Dashboard exceeds 28 cards; select evidence explicitly before rendering")
    if set(components) != {c["id"] for c in cards}:
        raise ValueError("Component map must cover every selected card exactly once")
    trials, feasible = [], []
    for columns in range(min(4, len(cards)), 0, -1):
        width = (SIDE - 2 * PADDING - GAP * (columns - 1)) // columns
        matches = [m for m in measurements if m["region_width"] == width]
        if len(matches) != 1:
            raise ValueError("Missing or ambiguous real DOM measurement width")
        rows = matches[0]["cards"]
        if len(rows) != len(cards) or {r["card"] for r in rows} != set(components):
            raise ValueError("DOM measurement must cover every selected card exactly once")
        byid = {r["card"]: r for r in rows}
        if any(r["overflow"] or r["min_font"] < 17.999 or r["width"] != width for r in rows):
            trials.append(f"{columns} columns: clipped content or insufficient font")
            continue
        if any(type(r["height"]) is not int or r["height"] < 96 for r in rows):
            raise ValueError("Invalid measured card height")
        heights, children = [], []
        for start in range(0, len(cards), columns):
            group = cards[start:start + columns]
            heights.append(max(byid[c["id"]]["height"] for c in group) + 2)
            panels = []
            for card in group:
                panel = {"id": "p_" + card["id"], "type": "panel", "card": card["id"],
                         "component": components[card["id"]]}
                if panel["component"] == "graph.node_link":
                    panel["node_layout"] = "layered_grid"
                panels.append(panel)
            # Last-row widths remain equal to measured widths.
            panels += [{"id": f"empty_{start}_{j}", "type": "spacer"}
                       for j in range(len(group), columns)]
            children.append({"id": f"row_{start}", "type": "row", "weights": [1] * columns,
                             "children": panels})
        required = sum(heights) + GAP * (len(heights) - 1)
        if required > SIDE - TOP - PADDING:
            trials.append(f"{columns} columns: needs {required}px below header")
            continue
        design = {"schema": "DashboardDesignV1", "theme": "dark", "font_size": 18,
                  "gap": GAP, "padding": PADDING, "readable_cards": PROFILE,
                  "readability_audit": "VisibleSourceV1", "graph": {"show_isolates": True},
                  "tree": {"id": "dashboard", "type": "column", "weights": heights,
                           "children": children}, "bindings": [],
                  "indexing": {"visible": True, "start": 1}}
        apply(design)
        geometry = compile_design(evidence, design)
        for rect in geometry["rectangles"]:
            if rect["height"] < byid[rect["card"]]["height"] or rect["width"] < width:
                raise ValueError("Layout rounded below measured component size")
        # Prefer actual content area, not the area of artificially stretched
        # card backgrounds. Geometry alone decides; there is no model feedback.
        content_area = sum(r["width"] * r.get("raw_height", r["height"]) for r in rows)
        feasible.append((content_area, columns, design))
    if feasible:
        return max(feasible, key=lambda item: item[:2])[2]
    raise ValueError("Selected cards do not fit 4096x4096 at readable size; " + "; ".join(trials))


def preset(evidence):
    """CPU/browser measurement only; no new evidence or model calls."""
    validate_evidence(evidence)
    probe = {}; apply(probe); validate(evidence, probe)
    components = default_components(evidence)
    widths = [(SIDE - 2 * PADDING - GAP * (n - 1)) // n
              for n in range(min(4, len(evidence["cards"])), 0, -1)]
    layouts = {str(w): {c["id"]: node_link_layout(c, w, 18, tight=True)
                       for c in evidence["cards"] if c["kind"] == "graph"} for w in widths}
    from .main import node_runtime
    parent = ROOT / "build/renderer_previews"
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fixed_measure_", dir=parent) as tmp:
        tmp = Path(tmp)
        write(tmp / "evidence.json", evidence)
        write(tmp / "jobs.json", [{"evidence": str(tmp / "evidence.json"),
            "output": str(tmp / "measurements.json"), "components": components,
            "full_width_cards": list(components), "node_layouts": layouts,
            "region_widths": widths, "profile": PROFILE, "font_size": 18,
            "indexing": {"visible": True, "start": 1}}])
        env = dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=str(ROOT / "build/renderer_tooling/browsers"))
        result = subprocess.run([str(node_runtime()), str(RENDERER / "web/dist/measure.mjs"),
                                 str(tmp / "jobs.json")], cwd=RENDERER / "web", env=env,
                                capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError("Component measurement failed: " + result.stderr[-3000:])
        return layout_from_measurements(evidence, components, read(tmp / "measurements.json")["measurements"])

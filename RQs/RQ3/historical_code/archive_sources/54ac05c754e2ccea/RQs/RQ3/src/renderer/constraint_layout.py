"""RQ3-only continuous split layouts over unchanged evidence-card renderers.

Content and encoding are explicit inputs, never optimized using private labels.
Feasible split ratios are projected analytically; no stochastic coordinate
solver or model request is needed. This is not a Penrose/Scout reproduction.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from typing import Any

from unified_scripts import canonical_json, stable_hash
from .capacity import rendering_profile
from .designs import DashboardSpecV3, EvidenceCardV1, _encoding

SCHEMA = "RQ3ConstraintLayoutV1"
MAX_CARDS = 12


@dataclass(frozen=True)
class PixelSilhouetteV1:
    silhouette_id: str
    card_id: str
    fact_inventory_hash: str
    encoding: str


@dataclass(frozen=True)
class PixelPlacementV1:
    silhouette_id: str
    card_id: str
    pixel_bbox: tuple[int, int, int, int]


@dataclass(frozen=True)
class PixelDashboardProgramV1:
    spec: DashboardSpecV3
    cards: tuple[EvidenceCardV1, ...]
    silhouettes: tuple[PixelSilhouetteV1, ...]
    placements: tuple[PixelPlacementV1, ...]
    selected_fact_inventory_hash: str
    layout_tree_json: str
    projection_json: str

    @property
    def program_hash(self):
        return stable_hash(asdict(self))

    @property
    def layout_audit(self):
        return audit_pixel_program(self)


def _tree(node, known, seen, depth=0):
    if depth > MAX_CARDS or not isinstance(node, dict):
        raise ValueError("layout tree must be a bounded JSON object")
    if set(node) == {"card"}:
        card = node["card"]
        if not isinstance(card, str) or card not in known or card in seen:
            raise ValueError("unknown or repeated layout card")
        seen.add(card)
        return {"card": card}
    if set(node) != {"axis", "ratio", "children"}:
        raise ValueError("split needs exactly axis, ratio and children")
    if node["axis"] not in ("x", "y"):
        raise ValueError("split axis must be x or y")
    ratio = node["ratio"]
    if type(ratio) not in (int, float) or not math.isfinite(ratio) or not .05 <= ratio <= .95:
        raise ValueError("split ratio must be a finite number in [0.05, 0.95]")
    children = node["children"]
    if not isinstance(children, list) or len(children) != 2:
        raise ValueError("split must have exactly two children")
    return {"axis": node["axis"], "ratio": float(ratio),
            "children": [_tree(child, known, seen, depth + 1) for child in children]}


def _frontier(options):
    """Minimal bounding-box Pareto envelope, without dropping feasible options."""
    result, smallest_height = [], math.inf
    for width, height in sorted(set(options)):
        if height < smallest_height:
            result.append((width, height))
            smallest_height = height
    if not result or len(result) > 512:
        raise ValueError("layout feasibility envelope is empty or exceeds safe CPU bound")
    return result


def _envelopes(node, sizes, gutter, cache, path="root"):
    if "card" in node:
        result = _frontier(sizes[node["card"]])
    else:
        left, right = [_envelopes(child, sizes, gutter, cache, path + str(i))
                       for i, child in enumerate(node["children"])]
        result = _frontier((a[0] + b[0] + gutter, max(a[1], b[1]))
                           if node["axis"] == "x" else
                           (max(a[0], b[0]), a[1] + b[1] + gutter)
                           for a in left for b in right)
    cache[path] = result
    return result


def _place(node, bounds, cache, gutter, placements, projection, path="root"):
    x0, y0, x1, y1 = bounds
    if "card" in node:
        placements.append(PixelPlacementV1("S-" + node["card"], node["card"], bounds))
        return
    axis = 0 if node["axis"] == "x" else 1
    extent = (x1 - x0, y1 - y0)
    available = extent[axis] - gutter
    wanted = round(available * node["ratio"])
    feasible = []
    for a in cache[path + "0"]:
        for b in cache[path + "1"]:
            low, high = a[axis], available - b[axis]
            if low <= high and max(a[1 - axis], b[1 - axis]) <= extent[1 - axis]:
                split = min(max(wanted, low), high)
                feasible.append((abs(split - wanted), split, low, high, a, b))
    if not feasible:
        raise ValueError("layout tree cannot fit complete cards in the selected canvas")
    _distance, split, low, high, _a, _b = min(feasible)
    first, second = list(bounds), list(bounds)
    first[axis + 2] = bounds[axis] + split
    second[axis] = first[axis + 2] + gutter
    projection.append({"path": path, "axis": node["axis"], "requested_ratio": node["ratio"],
                       "realized_ratio": split / available, "available_px": available,
                       "first_extent_px": split, "feasible_interval_px": [low, high],
                       "projected": split != wanted})
    for i, box in enumerate((first, second)):
        _place(node["children"][i], tuple(box), cache, gutter, placements, projection, path + str(i))


def compile_constraint_program(packet, spec, cards, tree, *, encodings=None):
    """Compile a fully selected packet; never select, drop or rewrite a fact."""
    cards = tuple(cards)
    ids = {c.card_id for c in cards}
    if not 1 <= len(cards) <= MAX_CARDS or len(ids) != len(cards):
        raise ValueError("constraint layout needs 1..12 unique selected cards")
    if spec.content_policy != "FULL" or spec.packing_mode != "reflow":
        raise ValueError("constraint layout accepts explicit FULL selection only")
    facts = {str(f["fact_id"]): f for f in packet["facts"]}
    selected = [fid for c in cards for fid in c.fact_ids]
    visible = {fid for fid, f in facts.items() if f["region"] != "C"}
    if len(facts) != len(packet["facts"]) or len(selected) != len(set(selected)) or set(selected) != visible:
        raise ValueError("selected packet/card facts are not an exact-once inventory")
    if spec.fact_inventory_hash and spec.fact_inventory_hash != packet["fact_inventory_hash"]:
        raise ValueError("constraint spec/packet fact hash mismatch")
    if stable_hash(packet["facts"]) != packet["fact_inventory_hash"]:
        raise ValueError("constraint packet facts changed after hashing")
    for card in cards:
        bound = sorted((facts[fid] for fid in card.fact_ids), key=lambda f: str(f["fact_id"]))
        if stable_hash(bound) != card.fact_inventory_hash or any(f["region"] != card.region for f in bound):
            raise ValueError("constraint card facts changed after binding")
    seen = set()
    tree = _tree(tree, ids, seen)
    if seen != ids:
        raise ValueError("layout tree omits a selected card")
    encodings = {} if encodings is None else dict(encodings)
    if not set(encodings) <= ids:
        raise ValueError("encoding override contains an unknown card")
    silhouettes, sizes = [], {}
    for card in cards:
        encoding = encodings.get(card.card_id, _encoding(card, spec))
        if encoding not in card.allowed_encodings:
            raise ValueError("encoding is not supported by this card")
        if encoding == "overlay_lines" and spec.metric_scale_policy != "common_robust":
            raise ValueError("overlay requires the common robust scale")
        profile = rendering_profile(card, facts, spec)
        sizes[card.card_id] = [(w * spec.cell_edge_px + (w - 1) * spec.gutter_px,
                                h * spec.cell_edge_px + (h - 1) * spec.gutter_px)
                               for w, h in profile["footprints_by_encoding"][encoding]]
        silhouettes.append(PixelSilhouetteV1("S-" + card.card_id, card.card_id,
                                           card.fact_inventory_hash, encoding))
    cache = {}
    _envelopes(tree, sizes, spec.gutter_px, cache)
    width, height = spec.logical_canvas_size
    bounds = (spec.gutter_px, spec.header_px + spec.gutter_px,
              width - spec.gutter_px, height - spec.gutter_px)
    if not any(w <= bounds[2] - bounds[0] and h <= bounds[3] - bounds[1] for w, h in cache["root"]):
        raise ValueError("layout tree cannot fit complete cards in the selected canvas")
    placements, projection = [], []
    _place(tree, bounds, cache, spec.gutter_px, placements, projection)
    program = PixelDashboardProgramV1(spec, cards, tuple(silhouettes), tuple(placements),
                                     stable_hash(sorted(selected)), canonical_json(tree), canonical_json(projection))
    audit_pixel_program(program)
    return program


def audit_pixel_program(program):
    """Independently check realized logical-pixel geometry at the render boundary."""
    spec = program.spec
    width, height = spec.logical_canvas_size
    viewport = (spec.gutter_px, spec.header_px + spec.gutter_px,
                width - spec.gutter_px, height - spec.gutter_px)
    ids = [c.card_id for c in program.cards]
    rows = list(program.placements)
    if sorted(r.card_id for r in rows) != sorted(ids) or len(set(ids)) != len(ids):
        raise ValueError("pixel placement/card bijection failed")
    if sorted(s.card_id for s in program.silhouettes) != sorted(ids):
        raise ValueError("pixel silhouette/card bijection failed")
    silhouettes = {s.card_id: s for s in program.silhouettes}
    for card in program.cards:
        item = silhouettes[card.card_id]
        if item.fact_inventory_hash != card.fact_inventory_hash or item.encoding not in card.allowed_encodings:
            raise ValueError("pixel silhouette changes card facts or encoding")
    if any(p.silhouette_id != silhouettes[p.card_id].silhouette_id for p in rows):
        raise ValueError("pixel placement/silhouette identity mismatch")
    for i, row in enumerate(rows):
        box = row.pixel_bbox
        if len(box) != 4 or any(type(v) is not int for v in box):
            raise ValueError("layout coordinates must be integer logical pixels")
        x0, y0, x1, y1 = box
        if not (viewport[0] <= x0 < x1 <= viewport[2] and viewport[1] <= y0 < y1 <= viewport[3]):
            raise ValueError("pixel card leaves content viewport")
        for other in rows[:i]:
            a, b, c, d = other.pixel_bbox
            if min(x1, c) > max(x0, a) and min(y1, d) > max(y0, b):
                raise ValueError("pixel cards overlap")
    area = sum((r.pixel_bbox[2] - r.pixel_bbox[0]) * (r.pixel_bbox[3] - r.pixel_bbox[1]) for r in rows)
    viewport_area = (viewport[2] - viewport[0]) * (viewport[3] - viewport[1])
    geometry = sorted((r.card_id, list(r.pixel_bbox)) for r in rows)
    return {"schema": SCHEMA, "status": "passed", "mode": "continuous_split_tree",
            "coordinate_space": "logical_pixels_before_raster_scaling", "viewport": list(viewport),
            "occupied_area_px": area, "viewport_area_px": viewport_area,
            "occupancy": area / viewport_area, "overlap_area_px": 0,
            "pixel_geometry_hash": stable_hash(geometry), "projection": json.loads(program.projection_json),
            "requested_tree": json.loads(program.layout_tree_json)}


def render_constraint_dashboard(packet, spec, cards, tree, *, encodings=None, metric_geometry=None):
    """Same real card painters and audits; new coordinates and per-card encoding."""
    from .human_dashboard import render_human_dashboard
    program = compile_constraint_program(packet, spec, cards, tree, encodings=encodings)
    return render_human_dashboard(packet, spec, program, metric_geometry=metric_geometry)

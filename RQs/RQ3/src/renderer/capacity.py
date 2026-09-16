"""RQ3 content-aware silhouette constraints, not a second evidence selector.

The catalogue and packer use these same rules. Measurements include complete
log payloads (not directory previews). Final pixel/primitive audits remain
mandatory: a capacity menu alone is not a rendering-integrity certificate.
"""
from collections import OrderedDict
from dataclasses import asdict, is_dataclass
import math
from threading import RLock

from PIL import Image, ImageDraw
from unified_scripts import stable_hash

LOG_EXTENSIONS = ((4, 4), (6, 4), (8, 4), (8, 6), (12, 8), (12, 12))
CAPACITY_POLICY = "content_aware_log_overlay_v1"
_PROFILES = OrderedDict()
_LOCK = RLock()


def _log_height(facts, width, font_scale):
    from . import human_dashboard as hd
    token = hd._FONT_SCALE.set(font_scale)
    try:
        draw = ImageDraw.Draw(Image.new("L", (1, 1)))
        normal, bold = hd._font(7), hd._font(7, True)
        line_height = max(10, normal.getbbox("Ag")[3] - normal.getbbox("Ag")[1] + 2)
        rows = [f for f in facts if f.get("field") == "denum_log_template"]
        meta = [f for f in facts if f not in rows]
        row_height = 64
        for row in rows:
            blocks = hd._log_text_blocks(row.get("payload") or {}, hd._palette("canonical"))
            lines = sum(len(hd._wrap(draw, text, bold if heavy else normal, width - 28))
                        for text, heavy, _color in blocks)
            row_height = max(row_height, lines * line_height + 40)
        for fact in meta:
            p = fact.get("payload") or {}
            text = f"source events={p.get('event_count', 'n/a')} · templates={p.get('template_count', 'n/a')} · semantic round-trip={p.get('semantic_round_trip', 'n/a')}"
            if draw.textlength(text, font=hd._font(8)) > width - 28:
                return math.inf
        return 54 + (34 if meta else 8) + len(rows) * row_height
    finally:
        hd._FONT_SCALE.reset(token)


def rendering_profile(card, facts, spec=None):
    """Return a fresh JSON-safe profile; cache only bounded small measurements.

    Baseline options remain first-class. Extra log sizes are available only
    when *none* of a card's baseline options holds its complete text. Raster
    scaling never enters fitting: it scales the finished logical canvas.
    """
    from .designs import DashboardSpecV3
    spec = spec or DashboardSpecV3()
    value = asdict(card) if is_dataclass(card) else card
    selected = [facts[fid] for fid in value["fact_ids"]]
    geometry = (spec.cell_edge_px, spec.gutter_px,
                spec.typography_baseline_scale * spec.legibility_scale)
    key = stable_hash([CAPACITY_POLICY, value, selected, geometry])
    with _LOCK:
        cached = _PROFILES.get(key)
        if cached is not None:
            _PROFILES.move_to_end(key)
    if cached is None:
        sizes = tuple(tuple(size) for size in value["footprint_options"])
        if value["semantic_type"] == "log_bundle":
            needed = {}

            def feasible(size):
                w, h = size
                if w not in needed:
                    needed[w] = _log_height(selected, w * geometry[0] + (w - 1) * geometry[1], geometry[2])
                return needed[w] <= h * geometry[0] + (h - 1) * geometry[1]

            fitted = tuple(size for size in sizes if feasible(size))
            sizes = fitted or tuple(size for size in LOG_EXTENSIONS if feasible(size))
        cached = tuple((encoding, tuple(size for size in sizes if
                            not (value["semantic_type"] == "metric_bundle" and encoding == "overlay_lines")
                            or (size[0] >= 4 and size[1] >= 4)))
                       for encoding in value["allowed_encodings"])
        with _LOCK:
            _PROFILES[key] = cached
            _PROFILES.move_to_end(key)
            while len(_PROFILES) > 2048:
                _PROFILES.popitem(last=False)
    union = sorted({size for _, sizes in cached for size in sizes}, key=lambda s: (math.prod(s), s))
    return {"encodings": [e for e, sizes in cached if sizes],
            "footprints": [list(s) for s in union],
            "footprints_by_encoding": {e: [list(s) for s in sizes] for e, sizes in cached},
            "capacity_policy": CAPACITY_POLICY}

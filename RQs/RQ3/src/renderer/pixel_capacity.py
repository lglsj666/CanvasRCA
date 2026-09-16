"""Measure real painter capacity in pixels, independently of grid footprints.

The old footprint menu is retained for historical programs. New split-tree
programs can request measured capacity. Trial renderings are CPU-only, omit
no facts, and use the same fonts, plot geometry and text-overlap audit as the
final painter. A measured box is a feasible sample, not a global minimum.
"""
from collections import OrderedDict
from dataclasses import asdict
from threading import RLock
from types import SimpleNamespace

from PIL import Image, ImageDraw
from unified_scripts import stable_hash
from . import human_dashboard as hd
from .layout_audit import AuditedDraw

_CACHE = OrderedDict()
_LOCK = RLock()
POLICY = "actual_painter_pixel_capacity_v1"


def measured_envelopes(card, encoding, facts, spec, metric_geometry=None):
    selected = [facts[fid] for fid in card.fact_ids]
    relevant = {f["payload"]["panel_id"]: metric_geometry["series"][f["payload"]["panel_id"]]
                for f in selected if f["field"] == "metric_series_64"} if metric_geometry else None
    context = sorted((f for f in facts.values() if f['field'] in ('estimated_fault_window', 'observation_window')),
                     key=lambda f: f['fact_id']) if spec.metric_context_policy == 'selected_packet' else []
    key = stable_hash([POLICY, asdict(card), encoding, selected, asdict(spec), relevant, context])
    with _LOCK:
        if key in _CACHE:
            _CACHE.move_to_end(key)
            return [tuple(v) for v in _CACHE[key]]
    width, height = spec.logical_canvas_size
    maximum_h = height - spec.header_px - 2 * spec.gutter_px - 128
    maximum_w = width - 2 * spec.gutter_px - 24
    colors = hd._palette(spec.style_skin)
    options = []
    def fits(w, h):
        image = Image.new("RGB", (w, h), hd.BG)
        draw = AuditedDraw(ImageDraw.Draw(image))
        try:
            geometry = hd.paint_card(draw, (0, 0, w, h), card,
                SimpleNamespace(encoding=encoding), facts, colors, spec, metric_geometry)
            from .card_families import audit_family_geometry
            audit_family_geometry({"canvas_size": [w,h], "cards": [], "fact_mapping": [
                {"bbox": [0,0,w,h], "primitive_geometry": value} for value in geometry.values()]})
            return all(geometry.get(fid) for fid in card.fact_ids)
        except ValueError as exc:
            message = str(exc)
            if any(term in message for term in ("fit", "height", "short", "width", "leaves", "overlap", "reserved", "insufficient")):
                return False
            raise
    for w in sorted({v for v in (384, 512, 768, 1024, 1280, 1536, maximum_w) if 256 <= v <= maximum_w}):
        lo, hi = 160, maximum_h
        if not fits(w, hi): continue
        while hi - lo > 16:
            mid = (lo + hi) // 2
            if fits(w, mid): hi = mid
            else: lo = mid + 1
        if fits(w, hi): options.append((w, hi))
    frontier = [a for a in options if not any(b != a and b[0] <= a[0] and b[1] <= a[1] for b in options)]
    with _LOCK:
        _CACHE[key] = tuple(frontier)
        while len(_CACHE) > 256: _CACHE.popitem(last=False)
    return frontier

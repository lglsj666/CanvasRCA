"""Typed outer cards with unchanged real-chart facets and continuous layout.

This module groups an already selected packet; it never ranks evidence. A
compound silhouette may contain several chart facets, but has exactly one
public card identity and fact inventory. All times are public relative bins.
"""
from dataclasses import asdict, dataclass, replace
import io
import re
from types import SimpleNamespace

from PIL import Image, ImageDraw
from unified_scripts import stable_hash
from . import human_dashboard as hd
from .capacity import rendering_profile
from .constraint_layout import _tree, _envelopes, _place
from .designs import _make_card, _encoding
from .layout_audit import AuditedDraw

FAMILIES = ("modality", "temporal", "per_case", "evidence")
REGIONS = "MRLG"
TYPES = dict(zip(REGIONS, ("metric_bundle", "trace_bundle", "log_bundle", "topology_bundle")))
SCHEMA = "RQ3CardSilhouetteFamiliesV2"


@dataclass(frozen=True)
class EvidenceCardV2:
    card_id: str
    family: str
    fact_ids: tuple[str, ...]
    fact_inventory_hash: str
    regions: tuple[str, ...]
    entity_ids: tuple[str, ...]
    time_bins: tuple[int, int] | None = None
    chronological_index: int | None = None


def _facts(packet):
    facts = packet["facts"]
    if stable_hash(facts) != packet["fact_inventory_hash"]:
        raise ValueError("packet facts changed after hashing")
    if len({f["fact_id"] for f in facts}) != len(facts):
        raise ValueError("duplicate packet fact identity")
    if any(f["region"] not in (*REGIONS, "C") for f in facts):
        raise ValueError("unknown evidence region")
    return {f["fact_id"]: f for f in facts if f["region"] != "C"}


def make_family_cards(packet, family, *, groups=None, windows=None):
    """Explicitly partition selected facts; temporal inputs must be scoped.

    Temporal windows are disjoint inclusive bin intervals. A case-wide metric
    or trace summary cannot be pretended to describe a shorter instant. Such
    inputs require a separate source-based temporal projection before calling
    this renderer. Empty declared windows are errors, not silently omitted.
    """
    facts = _facts(packet)
    if family not in FAMILIES or not facts:
        raise ValueError("unknown card family or empty evidence")
    if groups is not None and family != "evidence":
        raise ValueError("explicit groups belong to the evidence family")
    if windows is not None and family != "temporal":
        raise ValueError("time windows belong to the temporal family")
    ranges = None
    if family == "modality":
        groups = [[fid for fid in sorted(facts) if facts[fid]["region"] == r] for r in REGIONS]
        groups = [g for g in groups if g]
    elif family == "per_case":
        groups = [sorted(facts)]
    elif family == "evidence":
        groups = [[fid] for fid in sorted(facts)] if groups is None else groups
    else:
        if not isinstance(windows, (list, tuple)) or not windows:
            raise ValueError("temporal cards need explicit windows")
        ranges = []
        for w in windows:
            if (not isinstance(w, (list, tuple)) or len(w) != 2
                    or any(type(v) is not int for v in w) or not 0 <= w[0] <= w[1] <= 63):
                raise ValueError("temporal window must use relative bins 0..63")
            ranges.append(tuple(w))
        ranges.sort()
        if any(a[1] >= b[0] for a, b in zip(ranges, ranges[1:])):
            raise ValueError("temporal windows overlap")
        groups = [[] for _ in ranges]
        for fid, fact in sorted(facts.items()):
            bins = fact.get("relative_bins") or []
            if not bins or any(type(b) is not int or not 0 <= b <= 63 for b in bins):
                raise ValueError("untimed fact needs a source-based temporal projection")
            matches = [i for i, (lo, hi) in enumerate(ranges) if all(lo <= b <= hi for b in bins)]
            if len(matches) != 1:
                raise ValueError("fact spans or falls outside declared temporal windows")
            if fact.get("field") == "denum_log_template" and bins != [fact["payload"].get("relative_bin")]:
                raise ValueError("log payload and temporal scope disagree")
            if fact.get("field") == "denum_log_template" and fact["payload"].get("log_r"):
                raise ValueError("case-wide LOG-R cannot be assigned to one temporal interval")
            groups[matches[0]].append(fid)
    if (not isinstance(groups, (list, tuple)) or not 1 <= len(groups) <= 12
            or any(not isinstance(g, (list, tuple)) or not g for g in groups)):
        raise ValueError("need 1..12 nonempty evidence groups")
    assigned = [fid for group in groups for fid in group]
    if any(not isinstance(fid, str) for fid in assigned):
        raise ValueError("fact identities must be strings")
    if len(assigned) != len(set(assigned)) or set(assigned) != set(facts):
        raise ValueError("card partition must cover selected evidence exactly once")
    output = []
    for i, group in enumerate(groups):
        rows = [facts[fid] for fid in sorted(group)]
        output.append(EvidenceCardV2(
            f"EC{i + 1:02d}", family, tuple(sorted(group)), stable_hash(rows),
            tuple(r for r in REGIONS if any(f["region"] == r for f in rows)),
            tuple(sorted({str(e) for f in rows for e in f.get("entity_ids", [])})),
            ranges[i] if ranges else None, i + 1 if ranges else None))
    return tuple(output)


def balanced_tree(ids, axis="y"):
    if not ids:
        raise ValueError("empty layout")
    if len(ids) == 1:
        return {"card": ids[0]}
    midpoint = (len(ids) + 1) // 2
    return {"axis": axis, "ratio": midpoint / len(ids), "children": [
        balanced_tree(ids[:midpoint], "x" if axis == "y" else "y"),
        balanced_tree(ids[midpoint:], "x" if axis == "y" else "y")]}


def metric_left_stack_tree(cards):
    """Version1 layout: present M left, present R/L/G in order on the right.

    Absent regions have no card and consume no space; facts are never removed.
    The complete four-region case exactly reproduces SEARCH-19's explicit tree.
    """
    cards=tuple(cards);by_region={}
    if not cards:raise ValueError('metric-left layout needs nonempty modality cards')
    for card in cards:
        if card.family!='modality' or len(card.regions)!=1 or card.regions[0] not in REGIONS:
            raise ValueError('metric-left layout requires single-region modality cards')
        region=card.regions[0]
        if region in by_region or card.card_id in by_region.values():raise ValueError('duplicate layout card/region')
        by_region[region]=card.card_id
    def stack(ids):
        if len(ids)==1:return {'card':ids[0]}
        return {'axis':'y','ratio':1/len(ids),'children':[{'card':ids[0]},stack(ids[1:])]}
    others=[by_region[r] for r in 'RLG' if r in by_region]
    if 'M' not in by_region:return stack(others)
    metric={'card':by_region['M']}
    return {'axis':'x','ratio':.6,'children':[metric,stack(others)]} if others else metric


def _checked_tree(tree, ids):
    seen = set()
    result = _tree(tree, set(ids), seen)
    if seen != set(ids):
        raise ValueError("layout omits selected content")
    return result


def _allocate(tree, cache, bounds, gap):
    if not any(w <= bounds[2] - bounds[0] and h <= bounds[3] - bounds[1] for w, h in cache["root"]):
        raise ValueError("complete card contents cannot fit this layout")
    placements, projection = [], []
    _place(tree, bounds, cache, gap, placements, projection)
    return {p.card_id: p.pixel_bbox for p in placements}, projection


def render_family_dashboard(packet, spec, cards, tree=None, *, facet_trees=None,
                            encodings=None, metric_geometry=None, card_headings=None):
    """Render all four families using the same tested plot/trace/log painters."""
    facts = _facts(packet)
    cards = tuple(cards)
    if not cards or len({c.card_id for c in cards}) != len(cards) or len(cards) > 12:
        raise ValueError("invalid outer card set")
    if spec.content_policy != "FULL" or spec.packing_mode != "reflow":
        raise ValueError("family renderer accepts explicit FULL selection only")
    if spec.fact_inventory_hash and spec.fact_inventory_hash != packet["fact_inventory_hash"]:
        raise ValueError("spec/packet hash mismatch")
    assigned = [fid for c in cards for fid in c.fact_ids]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(facts):
        raise ValueError("outer card facts are not exact-once")
    # Reconstruct the grouping contract to validate hashes, ownership and time.
    families = {c.family for c in cards}
    if len(families) != 1:
        raise ValueError("a family comparison uses one declared grouping family")
    family = next(iter(families))
    rebuilt = make_family_cards(packet, family,
        groups=[list(c.fact_ids) for c in cards] if family == "evidence" else None,
        windows=[c.time_bins for c in cards] if family == "temporal" else None)
    if cards != rebuilt:
        raise ValueError("card metadata differs from its canonical fact grouping")
    ids = [c.card_id for c in cards]
    tree = _checked_tree(balanced_tree(ids) if tree is None else tree, ids)
    facet_trees, encodings, card_headings = facet_trees or {}, encodings or {}, card_headings or {}
    if not set(facet_trees) <= set(ids) or not set(encodings) <= set(ids):
        raise ValueError("unknown card override")
    if not set(card_headings) <= set(ids):
        raise ValueError("heading refers to unknown card")
    safe_heading = re.compile(r"(?:SERVICE [0-9]{3}|NODE [0-9]{4}|POD [0-9]{5}|OTHER [MRLG])")
    if any(not isinstance(value, str) or not safe_heading.fullmatch(value)
           for value in card_headings.values()):
        raise ValueError("unsafe candidate-binding card heading")
    pad, header = 12, 104
    token = hd._FONT_SCALE.set(spec.typography_baseline_scale * spec.legibility_scale)
    try:
        card_sizes, components = {}, {}
        for card in cards:
            facets, sizes, choices = {}, {}, {}
            overrides = encodings.get(card.card_id, {})
            if not set(overrides) <= set(card.regions):
                raise ValueError("encoding refers to absent region")
            for region in card.regions:
                bound = [facts[fid] for fid in card.fact_ids if facts[fid]["region"] == region]
                facet = replace(_make_card(bound, region, TYPES[region]), card_id=region)
                encoding = overrides.get(region, _encoding(facet, spec))
                if encoding not in facet.allowed_encodings:
                    raise ValueError("unsupported facet encoding")
                if encoding == "overlay_lines" and spec.metric_scale_policy != "common_robust":
                    raise ValueError("overlay requires common robust scale")
                profile = rendering_profile(facet, facts, spec)
                options = profile["footprints_by_encoding"][encoding]
                sizes[region] = [(w * spec.cell_edge_px + (w - 1) * spec.gutter_px,
                                  h * spec.cell_edge_px + (h - 1) * spec.gutter_px) for w, h in options]
                if spec.pixel_capacity_policy == "measured":
                    from .pixel_capacity import measured_envelopes
                    sizes[region] = measured_envelopes(facet, encoding, facts, spec, metric_geometry)
                    if not sizes[region]: raise ValueError("selected facet has no measured feasible size")
                facets[region], choices[region] = facet, encoding
            inner = _checked_tree(facet_trees.get(card.card_id, balanced_tree(list(facets))), facets)
            cache = {}
            envelope = _envelopes(inner, sizes, spec.gutter_px, cache)
            card_sizes[card.card_id] = [(w + 2 * pad, h + header + 2 * pad) for w, h in envelope]
            components[card.card_id] = (facets, choices, inner, cache)
        outer_cache = {}
        _envelopes(tree, card_sizes, spec.gutter_px, outer_cache)
        width, height = spec.logical_canvas_size
        viewport = (spec.gutter_px, spec.header_px + spec.gutter_px,
                    width - spec.gutter_px, height - spec.gutter_px)
        boxes, projection = _allocate(tree, outer_cache, viewport, spec.gutter_px)
        image = Image.new("RGB", (width, height), hd.BG)
        draw = AuditedDraw(ImageDraw.Draw(image))
        colors = hd._palette(spec.style_skin)
        draw.text((spec.gutter_px, 8), "TELEMETRY DIAGNOSTIC OVERVIEW", font=hd._font(29, True), fill=colors["text"])
        draw.text((spec.gutter_px, 69), "M metrics · R traces · L logs · G directed topology · case-local numeric IDs",
                  font=hd._font(13), fill=colors["muted"])
        mapping, card_rows, regions = [], [], []
        for card in cards:
            box = boxes[card.card_id]
            draw.set_owner(card.card_id, box)
            draw.rounded_rectangle(box, radius=12, fill=hd.PANEL, outline=colors["border"], width=3)
            if card.family == "temporal":
                number = str(card.chronological_index)
                number_font = hd._font(34, True)
                draw.text((box[0] + pad, box[1] + 8), number, font=number_font, fill=colors["current"])
                label_x = box[0] + pad + draw.textlength(number, font=number_font) + 20
                heading = f"Relative bins {card.time_bins[0]}–{card.time_bins[1]}"
            else:
                label_x = box[0] + pad
                heading = {"modality": " / ".join(card.regions), "per_case": "INCIDENT EVIDENCE",
                           "evidence": "EVIDENCE BUNDLE"}[card.family]
            heading = card_headings.get(card.card_id, heading)
            if spec.card_label_policy == "visible_id_v1":
                if not re.fullmatch(r"EC(?:0[1-9]|1[0-2])", card.card_id):
                    raise ValueError("visible card ID must be an anonymous EC01..EC12 label")
                heading = f"{card.card_id} · {heading}"
            font = hd._single_line_font(draw, heading, box[2] - label_x - pad, start=20, floor=12)
            draw.text((label_x, box[1] + 18), heading, font=font, fill=colors["text"])
            content = (box[0] + pad, box[1] + header, box[2] - pad, box[3] - pad)
            facets, choices, inner, cache = components[card.card_id]
            facet_boxes, inner_projection = _allocate(inner, cache, content, spec.gutter_px)
            facet_rows = []
            for region, facet in facets.items():
                silhouette = SimpleNamespace(encoding=choices[region])
                geometry = hd.paint_card(draw, facet_boxes[region], facet, silhouette, facts, colors, spec, metric_geometry)
                for fid in facet.fact_ids:
                    primitives = geometry.get(fid, [])
                    if not primitives:
                        raise ValueError("selected fact has no visible primitive")
                    mapping.append({"fact_id": fid, "card_id": card.card_id, "silhouette_id": "S-" + card.card_id,
                                    "region": region, "bbox": list(facet_boxes[region]),
                                    "primitive": choices[region], "primitive_geometry": primitives})
                facet_rows.append({"region": region, "encoding": choices[region], "bbox": list(facet_boxes[region])})
                regions.append({"region": region, "card_id": card.card_id, "bbox": list(facet_boxes[region])})
            card_rows.append({"card": asdict(card), "silhouette_id": "S-" + card.card_id, "bbox": list(box),
                              "facets": facet_rows, "facet_projection": inner_projection,
                              "heading_bbox": [box[0], box[1], box[2], box[1] + header],
                              **({"heading": heading} if card.card_id in card_headings else {})})
        if sorted(m["fact_id"] for m in mapping) != sorted(facts):
            raise ValueError("painted fact inventory mismatch")
        manifest = {"schema_version": SCHEMA, "family": family, "spec": asdict(spec),
                    "cards": card_rows, "fact_mapping": mapping, "region_facets": regions,
                    "canvas_size": list(spec.canvas_size), "logical_canvas_size": [width, height],
                    "source_packet_fact_inventory_hash": packet["fact_inventory_hash"],
                    "visual_fact_inventory_hash": stable_hash([facts[fid] for fid in sorted(facts)]),
                    "card_silhouette_bijection": {"status": "passed", "cards": len(cards), "silhouettes": len(cards)},
                    "clipping_audit": {"status": "passed", "label_count": draw.label_count},
                    "requested_tree": tree, "outer_projection": projection,
                    "coordinate_space": "final_raster_pixels"}
        if spec.metric_summary_policy == 'observations_only_v1':
            from copy import deepcopy
            visible = [deepcopy(facts[fid]) for fid in sorted(facts)]
            withheld = []
            for fact in visible:
                if fact['field'] == 'metric_series_64' and 'signed_z' in fact['payload']:
                    del fact['payload']['signed_z']
                    withheld.append({'fact_id': fact['fact_id'], 'pointer': '/payload/signed_z'})
            manifest['withheld_fields'] = withheld
            manifest['visual_fact_inventory_hash'] = stable_hash(visible)
        manifest["program_hash"] = stable_hash([SCHEMA, asdict(spec), [asdict(c) for c in cards], tree,
                                                   facet_trees, encodings, card_headings])
        if spec.raster_scale != 1:
            image = image.resize(spec.canvas_size, Image.Resampling.LANCZOS)
            manifest = scale_pixel_geometry(manifest, spec.raster_scale)
        audit_family_geometry(manifest)
        manifest["pixel_geometry_hash"] = stable_hash({"canvas": manifest["canvas_size"],
            "cards": manifest["cards"], "facts": manifest["fact_mapping"]})
        if metric_geometry is not None:
            manifest["metric_source_geometry_hash"] = stable_hash(metric_geometry)
        stream = io.BytesIO()
        image.save(stream, format="PNG", optimize=False, compress_level=6)
        manifest["manifest_sha256"] = stable_hash(manifest)
        return stream.getvalue(), manifest
    finally:
        hd._FONT_SCALE.reset(token)


def scale_pixel_geometry(value, factor, key=None):
    """Scale actual drawing coordinates, never values/time/config parameters."""
    if isinstance(value, dict):
        return {k: scale_pixel_geometry(v, factor, k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        if key and (key.endswith("bbox") or key in {"point", "start", "end"}):
            return [round(float(v) * factor) for v in value]
        return [scale_pixel_geometry(v, factor) for v in value]
    return value


def audit_family_geometry(manifest):
    """Check actual facet/primitive containment and nonoverlap after scaling."""
    width, height = manifest["canvas_size"]
    def contains(a, b):
        return a[0] <= b[0] <= b[2] <= a[2] and a[1] <= b[1] <= b[3] <= a[3]
    def check_boxes(rows, bounds):
        for i, a in enumerate(rows):
            if not contains(bounds, a) or a[0] >= a[2] or a[1] >= a[3]:
                raise ValueError("card/facet leaves its pixel bounds")
            if any(min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1]) for b in rows[:i]):
                raise ValueError("card/facet pixel overlap")
    def geometry(value):
        if isinstance(value, dict):
            for key, v in value.items():
                if key.endswith("bbox") and isinstance(v, list) and len(v) == 4:
                    yield v
                elif key in {"point", "start", "end"} and isinstance(v, list) and len(v) == 2:
                    yield [*v, *v]
                else:
                    yield from geometry(v)
        elif isinstance(value, list):
            for v in value:
                yield from geometry(v)
    check_boxes([c["bbox"] for c in manifest["cards"]], (0, 0, width, height))
    for card in manifest["cards"]:
        check_boxes([card["heading_bbox"], *(f["bbox"] for f in card["facets"])], card["bbox"])
    for row in manifest["fact_mapping"]:
        if any(not contains(row["bbox"], box) for box in geometry(row["primitive_geometry"])):
            raise ValueError("fact primitive leaves its facet")


def attention_metadata(manifest):
    """Compound cards assign attention to real regional facets, not outer boxes."""
    audit_family_geometry(manifest)
    boxes = {r: [f["bbox"] for f in manifest["region_facets"] if f["region"] == r] for r in REGIONS}
    boxes = {r: b for r, b in boxes.items() if b}
    return {"attention_region": "dashboard", "attention_region_boxes": boxes,
            "attention_visual_regions": list(boxes),
            "attention_header_box": [0, 0, manifest["canvas_size"][0],
                                     round(manifest["spec"]["header_px"] * manifest["spec"]["raster_scale"])],
            "attention_renderer_geometry": {"canvas_size": manifest["canvas_size"],
                "card_heading_boxes": [c["heading_bbox"] for c in manifest["cards"]]}}

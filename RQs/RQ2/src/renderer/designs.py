"""RQ2 evidence-card and silhouette dashboard DSL.

A label-blind public fact packet is partitioned into EvidenceCardV1 objects.
One card may contain several compatible atomic facts (for example four aligned
metric series), while every fact still appears in exactly one card and every
selected card becomes exactly one SilhouetteV1.  This separates the audit unit
from the visual panel without weakening exact-once evidence accounting.
"""

from __future__ import annotations

import io
import math
import random
import re
from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from unified_scripts import canonical_json, stable_hash

REGIONS = ("M", "R", "L", "G")
NEUTRAL = "#f7f9fb"
METRIC_ENCODINGS = ("heatmap", "small_multiple_lines", "overlay_lines")
TRACE_ENCODINGS = ("trace_dumbbell", "trace_baseline_fault_bars")
LOG_ENCODINGS = ("template_frequency_timeline", "template_time_matrix")
TOPOLOGY_ENCODINGS = ("node_link", "adjacency_matrix", "edge_table")
PROPAGATION_ENCODINGS = ("propagation_rows", "propagation_timeline")
LAYOUT_FAMILIES = ("modality_grouped", "entity_grouped", "salience_first", "topology_centered")
ENTITY_ORDERS = ("stable_id", "salience_onset", "topology_bfs")
FOOTPRINT_POLICIES = ("compact", "balanced", "detailed")
STYLE_SKINS = ("canonical", "colorblind")
COORDINATION_MODES = ("none", "shared_entity", "shared_time")
METRIC_SCALE_POLICIES = ("per_card_raw", "common_robust")
PACKING_MODES = ("reflow", "blank")
SELECTION_RULES = ("balanced_coverage", "salience", "entity_diversity", "hash_random")
PANEL_COMPOSITIONS = ("human_composite", "sparse_atomic_control")
CANVAS_SIZE = (3072, 2160)


@dataclass(frozen=True)
class EvidenceCardV1:
    card_id: str
    region: str
    semantic_type: str
    fact_ids: tuple[str, ...]
    fact_inventory_hash: str
    entity_ids: tuple[str, ...]
    selection_score: float
    required_for_interpretation: bool
    allowed_encodings: tuple[str, ...]
    footprint_options: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        if self.region not in REGIONS:
            raise ValueError(f"invalid evidence-card region {self.region}")
        if not self.fact_ids or len(self.fact_ids) != len(set(self.fact_ids)):
            raise ValueError("an evidence card needs unique facts")
        if not self.allowed_encodings or not self.footprint_options:
            raise ValueError("an evidence card needs an encoding and footprint")


@dataclass(frozen=True)
class SilhouetteV1:
    silhouette_id: str
    card_id: str
    fact_inventory_hash: str
    encoding: str
    width_cells: int
    height_cells: int

    @property
    def area_cells(self) -> int:
        return self.width_cells * self.height_cells


@dataclass(frozen=True)
class CardPlacementV1:
    silhouette_id: str
    card_id: str
    column: int
    row: int
    width_cells: int
    height_cells: int


@dataclass(frozen=True)
class DashboardSpecV3:
    design_id: str = ""
    design_role: str = "silhouette_screen"
    panel_composition: str = "human_composite"
    content_policy: str = "FULL"
    selection_rule: str = "balanced_coverage"
    metric_encoding: str = "small_multiple_lines"
    trace_encoding: str = "trace_dumbbell"
    log_encoding: str = "template_frequency_timeline"
    topology_encoding: str = "node_link"
    propagation_encoding: str = "propagation_rows"
    layout_family: str = "modality_grouped"
    entity_order: str = "stable_id"
    footprint_policy: str = "balanced"
    packing_mode: str = "reflow"
    coordination_mode: str = "none"
    metric_scale_policy: str = "common_robust"
    grid_columns: int = 12
    grid_rows: int = 8
    cell_edge_px: int = 256
    gutter_px: int = 12
    header_px: int = 92
    raster_scale: float = 1.0
    legibility_scale: float = 1.0
    typography_baseline_scale: float = 1.18
    style_skin: str = "canonical"
    renderer_parent_hash: str = ""
    fact_inventory_hash: str = ""

    def __post_init__(self) -> None:
        choices = (
            (self.metric_encoding, METRIC_ENCODINGS, "metric encoding"),
            (self.trace_encoding, TRACE_ENCODINGS, "trace encoding"),
            (self.log_encoding, LOG_ENCODINGS, "log encoding"),
            (self.topology_encoding, TOPOLOGY_ENCODINGS, "topology encoding"),
            (self.propagation_encoding, PROPAGATION_ENCODINGS, "propagation encoding"),
            (self.layout_family, LAYOUT_FAMILIES, "layout family"),
            (self.entity_order, ENTITY_ORDERS, "entity order"),
            (self.footprint_policy, FOOTPRINT_POLICIES, "footprint policy"),
            (self.selection_rule, SELECTION_RULES, "selection rule"),
            (self.packing_mode, PACKING_MODES, "packing mode"),
            (self.coordination_mode, COORDINATION_MODES, "coordination mode"),
            (self.metric_scale_policy, METRIC_SCALE_POLICIES, "metric scale policy"),
            (self.style_skin, STYLE_SKINS, "style skin"),
            (self.panel_composition, PANEL_COMPOSITIONS, "panel composition"),
        )
        for value, allowed, label in choices:
            if value not in allowed:
                raise ValueError(f"unsupported {label} {value}")
        if self.metric_encoding == "overlay_lines" and self.metric_scale_policy != "common_robust":
            raise ValueError("overlay_lines requires a shared common_robust baseline-z scale")
        if not 6 <= self.grid_columns <= 18 or not 4 <= self.grid_rows <= 12:
            raise ValueError("grid dimensions are outside registered bounds")
        if not 160 <= self.cell_edge_px <= 448:
            raise ValueError("cell_edge_px must be in [160, 448]")
        if not 4 <= self.gutter_px <= 32 or not 64 <= self.header_px <= 140:
            raise ValueError("gutter/header is outside registered bounds")
        if not 0.75 <= float(self.raster_scale) <= 1.5:
            raise ValueError("raster_scale must be in [0.75, 1.5]")
        if not 0.8 <= float(self.legibility_scale) <= 1.25:
            raise ValueError("legibility_scale must be in [0.8, 1.25]")
        if not math.isclose(float(self.typography_baseline_scale), 1.18):
            raise ValueError("RQ2 human-composite typography baseline is frozen at 1.18")
        _parse_content_policy(self.content_policy)

    @property
    def cell_id(self) -> str:
        return self.design_id or "_".join((
            self.layout_family, self.footprint_policy,
            f"G{self.grid_columns}x{self.grid_rows}", f"P{self.cell_edge_px}",
            self.metric_encoding, self.trace_encoding, self.log_encoding,
            self.topology_encoding, self.propagation_encoding,
            self.coordination_mode, self.metric_scale_policy,
        ))

    @property
    def logical_canvas_size(self) -> tuple[int, int]:
        width = self.grid_columns * self.cell_edge_px + (self.grid_columns + 1) * self.gutter_px
        height = self.header_px + self.grid_rows * self.cell_edge_px + (self.grid_rows + 1) * self.gutter_px
        return width, height

    @property
    def canvas_size(self) -> tuple[int, int]:
        width, height = self.logical_canvas_size
        return round(width * self.raster_scale), round(height * self.raster_scale)

    @property
    def capacity_cells(self) -> int:
        return self.grid_columns * self.grid_rows

    def fingerprint(self) -> str:
        return stable_hash(asdict(self))

    def structural_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for key in ("design_id", "design_role", "renderer_parent_hash", "fact_inventory_hash"):
            value.pop(key, None)
        return value


DashboardSpecV2 = DashboardSpecV3
DashboardSpecV1 = DashboardSpecV3


@dataclass(frozen=True)
class DashboardProgramV1:
    spec: DashboardSpecV3
    cards: tuple[EvidenceCardV1, ...]
    silhouettes: tuple[SilhouetteV1, ...]
    placements: tuple[CardPlacementV1, ...]
    selected_fact_inventory_hash: str
    occupancy: float
    empty_cells: int
    footprint_downgrades: int = 0

    @property
    def program_hash(self) -> str:
        return stable_hash(asdict(self))


def _parse_content_policy(policy: str) -> tuple[float, str]:
    if policy == "FULL":
        return 1.0, "balanced_coverage"
    match = re.fullmatch(r"B(25|50|75)_(COVERAGE|SALIENCE|DIVERSITY|RANDOM)", policy)
    if not match:
        raise ValueError(f"unknown evidence-card policy {policy}")
    rule = {
        "COVERAGE": "balanced_coverage", "SALIENCE": "salience",
        "DIVERSITY": "entity_diversity", "RANDOM": "hash_random",
    }[match.group(2)]
    return int(match.group(1)) / 100.0, rule


def policy_regions(policy: str) -> tuple[str, ...]:
    _parse_content_policy(policy)
    return REGIONS


def _fact_score(fact: Mapping[str, Any]) -> float:
    payload = fact.get("payload") or {}
    for value in (
        payload.get("signed_z"), payload.get("score"),
        (payload.get("log_r") or {}).get("score"), payload.get("count"),
        payload.get("severity_z_display"),
    ):
        try:
            return abs(float(str(value).removeprefix("+").removesuffix("m")))
        except (TypeError, ValueError):
            pass
    return 0.0


def _card_contract(semantic_type: str) -> tuple[tuple[str, ...], tuple[tuple[int, int], ...]]:
    contracts = {
        "metric_bundle": (METRIC_ENCODINGS, ((3, 3), (4, 3), (4, 4))),
        "trace_bundle": (TRACE_ENCODINGS, ((4, 2), (4, 3), (4, 4))),
        "log_bundle": (LOG_ENCODINGS, ((3, 2), (4, 2), (4, 3), (4, 4))),
        "topology_bundle": (TOPOLOGY_ENCODINGS, ((3, 3), (4, 4), (4, 6))),
        "metric_series": (METRIC_ENCODINGS, ((1, 1), (2, 1), (2, 2))),
        "trace_entry": (TRACE_ENCODINGS, ((2, 1), (2, 2), (3, 2))),
        "log_template": (LOG_ENCODINGS, ((2, 2), (3, 2), (3, 3))),
        "topology_graph": (TOPOLOGY_ENCODINGS, ((3, 2), (3, 3), (4, 3))),
        "propagation_order": (PROPAGATION_ENCODINGS, ((3, 2), (3, 3), (4, 3))),
    }
    return contracts.get(semantic_type, (("annotated_text",), ((2, 1), (2, 2), (3, 2))))


def _make_card(facts: Sequence[Mapping[str, Any]], region: str, semantic_type: str, required: bool = False) -> EvidenceCardV1:
    fact_ids = tuple(sorted(str(fact["fact_id"]) for fact in facts))
    entities = tuple(sorted({str(entity) for fact in facts for entity in fact.get("entity_ids") or ()}))
    encodings, footprints = _card_contract(semantic_type)
    if semantic_type == "log_bundle":
        row_count = sum(fact.get("field") == "denum_log_template" for fact in facts)
        if row_count <= 1:
            footprints = ((3, 2), (4, 2))
        elif row_count == 2:
            footprints = ((3, 2), (4, 2), (4, 3))
    if semantic_type == "metric_series":
        payload = facts[0].get("payload") or {}
        label = f"{payload.get('panel_id')} {payload.get('service')} {payload.get('metric')}"
        if len(label) > 42:
            footprints = tuple(size for size in footprints if size[0] >= 2)
    identity = stable_hash({"region": region, "semantic_type": semantic_type, "fact_ids": fact_ids})[:12]
    return EvidenceCardV1(
        card_id=f"{region}C-{identity}", region=region, semantic_type=semantic_type,
        fact_ids=fact_ids,
        fact_inventory_hash=stable_hash(sorted(facts, key=lambda row: str(row["fact_id"]))),
        entity_ids=entities,
        selection_score=max((_fact_score(fact) for fact in facts), default=0.0),
        required_for_interpretation=required,
        allowed_encodings=encodings, footprint_options=footprints,
    )


def _build_sparse_atomic_cards(packet: Mapping[str, Any]) -> tuple[EvidenceCardV1, ...]:
    """Retain the superseded one-fact-per-card layout as an explicit control."""
    facts = [fact for fact in packet.get("facts") or () if fact.get("region") in REGIONS]
    by_region = {region: [fact for fact in facts if fact.get("region") == region] for region in REGIONS}
    cards: list[EvidenceCardV1] = []
    groups = (
        ("M", "metric_series_64", "metric_series", "metric_context"),
        ("R", "trace_summary_entry", "trace_entry", "trace_context"),
        ("L", "denum_log_template", "log_template", "log_context"),
    )
    for region, field, row_type, meta_type in groups:
        rows = [fact for fact in by_region[region] if fact.get("field") == field]
        cards.extend(_make_card([fact], region, row_type) for fact in rows)
        meta = [fact for fact in by_region[region] if fact not in rows]
        if meta:
            cards.append(_make_card(meta, region, meta_type, True))
    edges = [fact for fact in by_region["G"] if fact.get("field") == "directed_call_edge"]
    graph_meta = [fact for fact in by_region["G"] if fact.get("field") in {"propagation_meta", "explicit_missingness"}]
    if edges or graph_meta:
        cards.append(_make_card((*edges, *graph_meta), "G", "topology_graph", True))
    propagation = [fact for fact in by_region["G"] if fact.get("field") == "propagation_service"]
    if propagation:
        cards.append(_make_card(propagation, "G", "propagation_order"))
    used = {fact_id for card in cards for fact_id in card.fact_ids}
    rest = [fact for fact in by_region["G"] if str(fact["fact_id"]) not in used]
    if rest:
        cards.append(_make_card(rest, "G", "topology_context", True))
    expected = {str(fact["fact_id"]) for fact in facts}
    assigned = [fact_id for card in cards for fact_id in card.fact_ids]
    if set(assigned) != expected or len(assigned) != len(expected):
        raise ValueError("evidence-card partition is not exact")
    return tuple(sorted(cards, key=lambda card: (REGIONS.index(card.region), card.card_id)))


def build_evidence_cards(
    packet: Mapping[str, Any], panel_composition: str = "human_composite",
    metric_bundle_size: int = 4,
) -> tuple[EvidenceCardV1, ...]:
    """Create an exact partition whose default cards are human-readable panels."""

    if panel_composition == "sparse_atomic_control":
        return _build_sparse_atomic_cards(packet)
    if panel_composition != "human_composite":
        raise ValueError(f"unknown panel composition {panel_composition}")
    if metric_bundle_size not in {4, 8}:
        raise ValueError("metric bundles must contain four normal or eight dense series")
    facts = [fact for fact in packet.get("facts") or () if fact.get("region") in REGIONS]
    by_region = {
        region: [fact for fact in facts if fact.get("region") == region]
        for region in REGIONS
    }
    cards: list[EvidenceCardV1] = []

    metric_rows = sorted(
        (fact for fact in by_region["M"] if fact.get("field") == "metric_series_64"),
        key=lambda fact: (
            int((fact.get("payload") or {}).get("rank") or 10**9),
            str(fact["fact_id"]),
        ),
    )
    metric_meta = [fact for fact in by_region["M"] if fact not in metric_rows]
    for index in range(0, len(metric_rows), metric_bundle_size):
        bundle = metric_rows[index:index + metric_bundle_size]
        if index == 0:
            bundle = [*bundle, *metric_meta]
        cards.append(_make_card(bundle, "M", "metric_bundle", index == 0))
    if not metric_rows and metric_meta:
        cards.append(_make_card(metric_meta, "M", "metric_bundle", True))

    trace_rows = sorted(
        by_region["R"],
        key=lambda fact: (
            fact.get("field") != "trace_summary_entry",
            int((fact.get("payload") or {}).get("entry_index") or 10**9),
            str(fact["fact_id"]),
        ),
    )
    if trace_rows:
        cards.append(_make_card(trace_rows, "R", "trace_bundle", True))

    log_rows = sorted(
        by_region["L"],
        key=lambda fact: (
            fact.get("field") != "denum_log_template",
            -int((fact.get("payload") or {}).get("count") or 0),
            str(fact["fact_id"]),
        ),
    )
    if log_rows:
        cards.append(_make_card(log_rows, "L", "log_bundle", True))

    graph_rows = sorted(
        by_region["G"],
        key=lambda fact: (
            {"directed_call_edge": 0, "propagation_service": 1}.get(str(fact.get("field")), 2),
            int((fact.get("payload") or {}).get("rank") or 10**9),
            str(fact["fact_id"]),
        ),
    )
    if graph_rows:
        cards.append(_make_card(graph_rows, "G", "topology_bundle", True))

    expected = {str(fact["fact_id"]) for fact in facts}
    assigned = [fact_id for card in cards for fact_id in card.fact_ids]
    if set(assigned) != expected or len(assigned) != len(expected):
        raise ValueError("composite evidence-card partition is not exact")
    return tuple(sorted(cards, key=lambda card: (REGIONS.index(card.region), card.card_id)))


def _select_cards(cards: Sequence[EvidenceCardV1], spec: DashboardSpecV3) -> tuple[EvidenceCardV1, ...]:
    ratio, registered_rule = _parse_content_policy(spec.content_policy)
    if ratio == 1.0:
        return tuple(cards)
    rule = registered_rule
    required = list(dict.fromkeys(card for card in cards if card.required_for_interpretation))
    minimum_area = {card.card_id: min(math.prod(size) for size in card.footprint_options) for card in cards}
    target_area = max(
        sum(minimum_area[card.card_id] for card in required),
        math.ceil(sum(minimum_area.values()) * ratio),
    )
    selected = list(required)
    remaining = [card for card in cards if card not in selected]
    if rule == "salience":
        ordered = sorted(remaining, key=lambda card: (-card.selection_score, card.card_id))
    elif rule == "hash_random":
        ordered = sorted(remaining, key=lambda card: (stable_hash({"seed": 42, "card_id": card.card_id}), card.card_id))
    elif rule == "entity_diversity":
        ordered, pool = [], list(remaining)
        covered = {entity for card in selected for entity in card.entity_ids}
        while pool:
            chosen = min(pool, key=lambda card: (-len(set(card.entity_ids) - covered), -card.selection_score, REGIONS.index(card.region), card.card_id))
            ordered.append(chosen); covered.update(chosen.entity_ids); pool.remove(chosen)
    else:
        pools = {region: sorted((card for card in remaining if card.region == region), key=lambda card: (-card.selection_score, card.card_id)) for region in REGIONS}
        ordered = []
        while any(pools.values()):
            for region in REGIONS:
                if pools[region]:
                    ordered.append(pools[region].pop(0))
    for card in ordered:
        if sum(minimum_area[value.card_id] for value in selected) >= target_area:
            break
        selected.append(card)
    return tuple(sorted(selected, key=lambda card: (REGIONS.index(card.region), card.card_id)))


def _encoding(card: EvidenceCardV1, spec: DashboardSpecV3) -> str:
    if card.semantic_type in {"metric_series", "metric_bundle"}:
        return spec.metric_encoding
    if card.semantic_type in {"topology_graph", "topology_bundle"}:
        return spec.topology_encoding
    if card.semantic_type in {"trace_entry", "trace_bundle"}:
        return spec.trace_encoding
    if card.semantic_type in {"log_template", "log_bundle"}:
        return spec.log_encoding
    if card.semantic_type == "propagation_order":
        return spec.propagation_encoding
    return card.allowed_encodings[0]


def _footprints(card: EvidenceCardV1, policy: str) -> tuple[tuple[int, int], ...]:
    values = sorted(set(card.footprint_options), key=lambda size: (size[0] * size[1], size))
    if policy == "compact":
        return tuple(values)
    if policy == "detailed":
        return tuple(reversed(values))
    middle = len(values) // 2
    return tuple((values[middle], *reversed(values[:middle])))


def _entity_order(packet: Mapping[str, Any], cards: Sequence[EvidenceCardV1], mode: str) -> dict[str, int]:
    entities = sorted({entity for card in cards for entity in card.entity_ids})
    if mode == "salience_onset":
        scores = {
            entity: max((card.selection_score for card in cards if entity in card.entity_ids), default=0.0)
            for entity in entities
        }
        ordered = sorted(entities, key=lambda entity: (-scores[entity], entity))
    elif mode == "topology_bfs":
        edges = [
            (str(fact["payload"]["caller"]), str(fact["payload"]["callee"]))
            for fact in packet.get("facts") or () if fact.get("field") == "directed_call_edge"
        ]
        adjacent = {entity: set() for entity in entities}
        indegree = {entity: 0 for entity in entities}
        for caller, callee in edges:
            adjacent.setdefault(caller, set()).add(callee)
            adjacent.setdefault(callee, set()).add(caller)
            indegree[callee] = indegree.get(callee, 0) + 1
            indegree.setdefault(caller, 0)
        roots = sorted(entities, key=lambda entity: (indegree.get(entity, 0), entity))
        ordered, seen = [], set()
        for root in roots:
            queue = [root]
            while queue:
                entity = queue.pop(0)
                if entity in seen:
                    continue
                seen.add(entity); ordered.append(entity)
                queue.extend(sorted(adjacent.get(entity, ())))
    else:
        ordered = entities
    return {entity: index for index, entity in enumerate(ordered)}


def _card_sort_key(
    card: EvidenceCardV1, family: str, area: int, entity_rank: Mapping[str, int],
) -> tuple[Any, ...]:
    # Composite topology goes first so wide 16×6 canvases retain a contiguous
    # graph panel; metric bundles then fill the remaining overview columns.
    if card.semantic_type == "topology_bundle":
        return (-1, -area, card.card_id)
    entity = card.entity_ids[0] if card.entity_ids else "~"
    rank = entity_rank.get(entity, len(entity_rank))
    if family == "entity_grouped":
        return rank, REGIONS.index(card.region), -area, -card.selection_score, card.card_id
    if family == "salience_first":
        return -card.selection_score, -area, REGIONS.index(card.region), entity, card.card_id
    if family == "topology_centered":
        return (0 if card.region == "G" else 1), rank, -area, -card.selection_score, card.card_id
    return REGIONS.index(card.region), rank, -area, -card.selection_score, card.card_id


def _positions(spec: DashboardSpecV3, width: int, height: int, *, centered: bool) -> list[tuple[int, int]]:
    values = [(x, y) for y in range(spec.grid_rows - height + 1) for x in range(spec.grid_columns - width + 1)]
    if centered:
        cx, cy = spec.grid_columns / 2, spec.grid_rows / 2
        values.sort(key=lambda p: (abs(p[0] + width / 2 - cx) + abs(p[1] + height / 2 - cy), p[1], p[0]))
    return values


def compile_dashboard_program(packet: Mapping[str, Any], spec: DashboardSpecV3) -> DashboardProgramV1:
    if spec.fact_inventory_hash and spec.fact_inventory_hash != packet.get("fact_inventory_hash"):
        raise ValueError("DashboardSpec fact inventory does not match packet")
    catalog = build_evidence_cards(
        packet, spec.panel_composition,
        metric_bundle_size=8 if spec.metric_encoding == "overlay_lines" else 4,
    )
    cards = _select_cards(catalog, spec)
    if spec.packing_mode == "blank" and spec.content_policy != "FULL":
        full = compile_dashboard_program(
            packet, replace(spec, content_policy="FULL", packing_mode="reflow"),
        )
        selected_ids = {card.card_id for card in cards}
        silhouettes = tuple(value for value in full.silhouettes if value.card_id in selected_ids)
        placements = tuple(value for value in full.placements if value.card_id in selected_ids)
        occupied = sum(value.width_cells * value.height_cells for value in placements)
        fact_ids = sorted(fact_id for card in cards for fact_id in card.fact_ids)
        return DashboardProgramV1(
            spec, cards, silhouettes, placements, stable_hash(fact_ids),
            occupied / spec.capacity_cells, spec.capacity_cells - occupied,
            full.footprint_downgrades,
        )
    # A budgeted reflow is the registered reclaimed-space treatment: after
    # selection, remaining cards may grow only through their already-audited
    # legal footprints.  FULL and BLANK retain the design's footprint policy,
    # so this does not change the equal-fact encoding experiment or fabricate
    # new evidence merely to fill space.
    reclaim_space = spec.packing_mode == "reflow" and spec.content_policy != "FULL"
    effective_footprint_policy = "detailed" if reclaim_space else spec.footprint_policy
    preferences = {}
    for card in cards:
        options = _footprints(card, effective_footprint_policy)
        if spec.metric_encoding == "overlay_lines" and card.semantic_type == "metric_bundle":
            # Every overlay card reserves a lossless legend above its shared
            # plot.  At the registered minimum 160 px cell size even a
            # four-series legend is a few pixels too tall for the generic 3x3
            # metric silhouette, while the existing 4x4 option is valid for
            # both four- and eight-series bundles.  Restrict packing to
            # feasible silhouettes before first-fit placement.
            # Use the card's complete registered option set here: the balanced
            # policy intentionally omits its largest option for ordinary
            # cards, but that option is the minimum feasible overlay size.
            options = tuple(
                size for size in card.footprint_options
                if size[0] >= 4 and size[1] >= 4
            )
        if not options:
            raise ValueError(f"no feasible silhouette for {card.card_id}")
        preferences[card.card_id] = options
    indices = {card.card_id: 0 for card in cards}

    def total_area() -> int:
        return sum(math.prod(preferences[card.card_id][indices[card.card_id]]) for card in cards)

    def shrink_one() -> bool:
        candidates = []
        for card in cards:
            options, index = preferences[card.card_id], indices[card.card_id]
            if index + 1 < len(options):
                current, smaller = math.prod(options[index]), math.prod(options[index + 1])
                candidates.append((current - smaller, -card.selection_score, card.card_id))
        if not candidates:
            return False
        _saving, _score, card_id = max(candidates)
        indices[card_id] += 1
        return True

    while total_area() > spec.capacity_cells:
        if not shrink_one():
            raise ValueError("selected evidence-card minimum footprints exceed grid capacity")

    def try_pack(*, exhaustive: bool = False) -> tuple[set[tuple[int, int]], list[SilhouetteV1], list[CardPlacementV1]] | None:
        occupied: set[tuple[int, int]] = set(); silhouettes = []; placements = []
        entity_rank = _entity_order(packet, cards, spec.entity_order)
        ordered = sorted(
            cards,
            # Preserve the registered layout semantics first, then use larger
            # silhouettes first within the same semantic group to reduce
            # fragmentation.  Putting area first would silently collapse the
            # four layout families into nearly the same first-fit packing.
            key=lambda card: _card_sort_key(
                card, spec.layout_family,
                math.prod(preferences[card.card_id][indices[card.card_id]]),
                entity_rank,
            ),
        )
        if exhaustive and len(ordered) <= 8:
            choices = []
            for card in ordered:
                width, height = preferences[card.card_id][indices[card.card_id]]
                centered = spec.layout_family == "topology_centered" and card.region == "G"
                candidates = []
                for column, row in _positions(spec, width, height, centered=centered):
                    cells = tuple(
                        (column + dx, row + dy)
                        for dy in range(height) for dx in range(width)
                    )
                    mask = sum(1 << (cy * spec.grid_columns + cx) for cx, cy in cells)
                    candidates.append((column, row, mask))
                choices.append((card, width, height, candidates))
            solution: list[tuple[Any, int, int, int, int]] = []
            visited: set[tuple[int, int]] = set()
            search_nodes = 0

            def place(index: int, occupied_mask: int) -> bool:
                nonlocal search_nodes
                search_nodes += 1
                if search_nodes > 250_000:
                    return False
                if index == len(choices):
                    return True
                state = (index, occupied_mask)
                if state in visited:
                    return False
                card, width, height, candidates = choices[index]
                for column, row, mask in candidates:
                    if mask & occupied_mask:
                        continue
                    solution.append((card, column, row, width, height))
                    if place(index + 1, occupied_mask | mask):
                        return True
                    solution.pop()
                visited.add(state)
                return False

            if not place(0, 0):
                return None
            for card, column, row, width, height in solution:
                cells = {(column + dx, row + dy) for dx in range(width) for dy in range(height)}
                silhouette = SilhouetteV1(
                    f"S-{card.card_id}", card.card_id, card.fact_inventory_hash,
                    _encoding(card, spec), width, height,
                )
                silhouettes.append(silhouette)
                placements.append(CardPlacementV1(
                    silhouette.silhouette_id, card.card_id, column, row, width, height,
                ))
                occupied.update(cells)
            return occupied, silhouettes, placements
        for card in ordered:
            width, height = preferences[card.card_id][indices[card.card_id]]
            placed = False
            centered = spec.layout_family == "topology_centered" and card.region == "G"
            for column, row in _positions(spec, width, height, centered=centered):
                cells = {(column + dx, row + dy) for dx in range(width) for dy in range(height)}
                if cells & occupied:
                    continue
                silhouette = SilhouetteV1(f"S-{card.card_id}", card.card_id, card.fact_inventory_hash, _encoding(card, spec), width, height)
                silhouettes.append(silhouette)
                placements.append(CardPlacementV1(silhouette.silhouette_id, card.card_id, column, row, width, height))
                occupied.update(cells); placed = True; break
            if not placed:
                return None
        return occupied, silhouettes, placements

    packed = try_pack()
    if packed is None:
        packed = try_pack(exhaustive=True)
    while packed is None and shrink_one():
        packed = try_pack()
        if packed is None:
            packed = try_pack(exhaustive=True)
    if packed is None:
        raise ValueError("selected evidence cards cannot be packed without overlap")
    occupied, silhouettes, placements = packed
    if len(cards) != len(silhouettes) or {c.card_id for c in cards} != {s.card_id for s in silhouettes}:
        raise ValueError("EvidenceCard-to-Silhouette bijection failed")
    fact_ids = sorted(fact_id for card in cards for fact_id in card.fact_ids)
    return DashboardProgramV1(
        spec, cards, tuple(silhouettes), tuple(placements), stable_hash(fact_ids),
        len(occupied) / spec.capacity_cells, spec.capacity_cells - len(occupied),
        sum(indices.values()),
    )


def validate_card_silhouette_bijection(program: DashboardProgramV1) -> None:
    cards = {card.card_id: card for card in program.cards}
    silhouettes = {item.card_id: item for item in program.silhouettes}
    if set(cards) != set(silhouettes) or len(program.cards) != len(program.silhouettes):
        raise ValueError("dashboard does not contain one silhouette per selected card")
    for card_id, card in cards.items():
        if silhouettes[card_id].fact_inventory_hash != card.fact_inventory_hash:
            raise ValueError(f"card/silhouette fact mismatch for {card_id}")


def _anchor_specs(parent_hash: str, fact_hash: str) -> list[DashboardSpecV3]:
    base = DashboardSpecV3(renderer_parent_hash=parent_hash, fact_inventory_hash=fact_hash)
    anchors = [replace(base, design_role="anchor:metric_encoding:small_multiple_lines")]
    anchors.extend(
        replace(base, design_role=f"anchor:metric_encoding:{encoding}", metric_encoding=encoding)
        for encoding in ("heatmap", "overlay_lines")
    )
    for value in (160, 192, 224, 256, 288, 320, 384, 448):
        anchors.append(replace(base, design_role="curve:cell_edge_px", cell_edge_px=value))
    for columns, rows in ((10, 10), (12, 8), (16, 6)):
        anchors.append(replace(base, design_role="anchor:grid_shape", grid_columns=columns, grid_rows=rows))
    for value in (4, 12, 22, 32):
        anchors.append(replace(base, design_role="curve:gutter_px", gutter_px=value))
    for value in (.75, 1.0, 1.25, 1.5):
        anchors.append(replace(base, design_role="curve:raster_scale", raster_scale=value))
    for value in (.8, 1.0, 1.25):
        anchors.append(replace(base, design_role="curve:legibility_scale", legibility_scale=value))
    unique = {stable_hash(spec.structural_dict()): spec for spec in anchors}
    return [unique[key] for key in sorted(unique)]


def _design_vector(spec: DashboardSpecV3) -> np.ndarray:
    categories = (
        (spec.metric_encoding, METRIC_ENCODINGS),
        (spec.trace_encoding, TRACE_ENCODINGS),
        (spec.log_encoding, LOG_ENCODINGS),
        (spec.topology_encoding, TOPOLOGY_ENCODINGS),
        (spec.propagation_encoding, PROPAGATION_ENCODINGS),
        (spec.layout_family, LAYOUT_FAMILIES),
        (spec.entity_order, ENTITY_ORDERS),
        (spec.footprint_policy, FOOTPRINT_POLICIES),
        (spec.coordination_mode, COORDINATION_MODES),
        (spec.metric_scale_policy, METRIC_SCALE_POLICIES),
        (spec.style_skin, STYLE_SKINS),
    )
    values = [1.0]
    for value, levels in categories:
        values.extend(
            1.0 if value == level else -1.0 if value == levels[0] else 0.0
            for level in levels[1:]
        )
    continuous = (
        (spec.cell_edge_px - 304.0) / 144.0,
        (spec.gutter_px - 18.0) / 14.0,
        (spec.raster_scale - 1.125) / .375,
        (spec.legibility_scale - 1.025) / .225,
        (spec.grid_columns / spec.grid_rows - 1.5) / 1.0,
    )
    values.extend(continuous)
    values.extend(value * value for value in continuous[:4])
    return np.asarray(values, dtype=float)


def space_filling_specs(
    parent_hash: str, fact_hash: str, *, seed: int = 42,
    points: int = 48, candidate_pool_size: int = 2048,
) -> tuple[DashboardSpecV3, ...]:
    """Constrained exact D-optimal panel with registered continuous anchors."""
    anchors = _anchor_specs(parent_hash, fact_hash)
    if points < len(anchors):
        raise ValueError(f"design needs at least {len(anchors)} registered anchors")
    rng = random.Random(seed); grids = ((10, 10), (12, 8), (16, 6)); candidates = {}
    for _ in range(candidate_pool_size):
        columns, rows = rng.choice(grids)
        metric_encoding = rng.choice(METRIC_ENCODINGS)
        spec = DashboardSpecV3(
            metric_encoding=metric_encoding,
            trace_encoding=rng.choice(TRACE_ENCODINGS),
            log_encoding=rng.choice(LOG_ENCODINGS),
            topology_encoding=rng.choice(TOPOLOGY_ENCODINGS),
            propagation_encoding=rng.choice(PROPAGATION_ENCODINGS),
            layout_family=rng.choice(LAYOUT_FAMILIES),
            entity_order=rng.choice(ENTITY_ORDERS),
            footprint_policy=rng.choice(FOOTPRINT_POLICIES),
            grid_columns=columns, grid_rows=rows,
            cell_edge_px=rng.randint(160, 448), gutter_px=rng.randint(4, 32),
            raster_scale=rng.uniform(.75, 1.5),
            legibility_scale=rng.uniform(.8, 1.25),
            coordination_mode=rng.choice(COORDINATION_MODES),
            metric_scale_policy=(
                "common_robust" if metric_encoding == "overlay_lines"
                else rng.choice(METRIC_SCALE_POLICIES)
            ),
            style_skin=rng.choice(STYLE_SKINS),
            renderer_parent_hash=parent_hash, fact_inventory_hash=fact_hash,
        )
        candidates.setdefault(stable_hash(spec.structural_dict()), spec)
    selected = list(anchors)
    for spec in selected:
        candidates.pop(stable_hash(spec.structural_dict()), None)
    ridge = np.eye(len(_design_vector(selected[0]))) * 1e-8
    information = ridge + sum((np.outer(_design_vector(spec), _design_vector(spec)) for spec in selected), start=np.zeros_like(ridge))
    while len(selected) < points:
        inverse = np.linalg.pinv(information)
        key, choice = max(
            candidates.items(),
            key=lambda item: (float(_design_vector(item[1]) @ inverse @ _design_vector(item[1])), item[0]),
        )
        vector = _design_vector(choice)
        selected.append(choice); candidates.pop(key)
        information += np.outer(vector, vector)
    return tuple(replace(spec, design_id=f"D{index:03d}") for index, spec in enumerate(selected))


@dataclass(frozen=True)
class ComposerActionV1:
    action: str
    arguments: Mapping[str, Any]


@dataclass(frozen=True)
class ComposerStateV1:
    case_evidence_hash: str
    partial_spec: Mapping[str, Any]
    remaining_fact_budget: int
    remaining_pixel_budget: int
    remaining_token_budget: int
    available_card_ids: tuple[str, ...] = ()
    history: tuple[Mapping[str, Any], ...] = ()
    renderer_hash: str = ""
    solver_hash: str = ""
    prompt_hash: str = ""
    scorer_hash: str = ""

    @property
    def state_hash(self) -> str:
        return stable_hash(asdict(self))


COMPOSER_ACTION_ORDER = (
    "select_evidence_cards", "select_silhouettes", "place_silhouettes",
    "choose_canvas_style", "validate_and_render",
)


def composer_sft_actions(program: DashboardProgramV1) -> tuple[ComposerActionV1, ...]:
    return (
        ComposerActionV1("select_evidence_cards", {
            "content_policy": program.spec.content_policy,
            "selection_rule": program.spec.selection_rule,
            "selected_card_ids": [card.card_id for card in program.cards],
        }),
        ComposerActionV1("select_silhouettes", {"silhouettes": [asdict(value) for value in program.silhouettes]}),
        ComposerActionV1("place_silhouettes", {
            "layout_family": program.spec.layout_family,
            "entity_order": program.spec.entity_order,
            "grid_columns": program.spec.grid_columns,
            "grid_rows": program.spec.grid_rows,
            "placements": [asdict(value) for value in program.placements],
        }),
        ComposerActionV1("choose_canvas_style", {
            "cell_edge_px": program.spec.cell_edge_px,
            "gutter_px": program.spec.gutter_px,
            "header_px": program.spec.header_px,
            "style_skin": program.spec.style_skin,
        }),
        ComposerActionV1("validate_and_render", {"program_hash": program.program_hash, "occupancy": program.occupancy}),
    )


def apply_composer_action(state: ComposerStateV1, action: ComposerActionV1) -> ComposerStateV1:
    index = len(state.history)
    expected = COMPOSER_ACTION_ORDER[index] if index < len(COMPOSER_ACTION_ORDER) else None
    if action.action != expected:
        raise ValueError(f"expected composer action {expected}, received {action.action}")
    arguments = dict(action.arguments); partial = dict(state.partial_spec)
    if action.action == "select_evidence_cards":
        chosen = tuple(map(str, arguments.get("selected_card_ids") or ()))
        if len(chosen) != len(set(chosen)) or not set(chosen) <= set(state.available_card_ids):
            raise ValueError("Composer selected unknown or duplicate evidence cards")
    elif action.action == "select_silhouettes":
        rows = list(arguments.get("silhouettes") or ()); chosen = set(partial.get("selected_card_ids") or ())
        if len(rows) != len(chosen) or {str(row.get("card_id")) for row in rows} != chosen:
            raise ValueError("Composer must emit exactly one silhouette per selected card")
    elif action.action == "place_silhouettes":
        rows = list(arguments.get("placements") or ()); chosen = set(partial.get("selected_card_ids") or ())
        if len(rows) != len(chosen) or {str(row.get("card_id")) for row in rows} != chosen:
            raise ValueError("Composer must place every silhouette exactly once")
    partial.update(arguments)
    history = (*state.history, {"action": action.action, "arguments": arguments})
    return replace(state, partial_spec=partial, history=history)


def replay_composer_sft_trace(initial: ComposerStateV1, actions: Iterable[ComposerActionV1]) -> ComposerStateV1:
    state = initial
    for action in actions:
        state = apply_composer_action(state, action)
    if len(state.history) != len(COMPOSER_ACTION_ORDER):
        raise ValueError("Composer trace did not finalize")
    return state


def compile_composer_sft_example(initial: ComposerStateV1, program: DashboardProgramV1) -> dict[str, Any]:
    state = initial; transitions = []
    for action in composer_sft_actions(program):
        before = state.state_hash; state = apply_composer_action(state, action)
        transitions.append({"action": asdict(action), "before_state_hash": before, "after_state_hash": state.state_hash})
    return {
        "schema_version": "CanvasRCAComposerSFTExampleV2",
        "case_evidence_hash": initial.case_evidence_hash,
        "target_design_id": program.spec.cell_id,
        "target_program_hash": program.program_hash,
        "card_silhouette_bijection": True,
        "transitions": transitions, "final_state_hash": state.state_hash,
    }


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", max(7, size))
    except OSError:
        return ImageFont.load_default()


def _pt(spec: DashboardSpecV3, size: float) -> int:
    """Relative legibility is independent of raster upsampling."""

    return max(7, round(size * spec.legibility_scale))


def _entity_color(entity: str) -> str:
    value = int(stable_hash({"entity": entity})[:6], 16)
    return f"#{64 + value % 128:02x}{64 + (value >> 7) % 128:02x}{64 + (value >> 14) % 128:02x}"


def _arrow(draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float], color: str, width: int = 2) -> None:
    draw.line((*start, *end), fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 9 + width
    for offset in (-0.55, 0.55):
        point = (
            end[0] - length * math.cos(angle + offset),
            end[1] - length * math.sin(angle + offset),
        )
        draw.line((*end, *point), fill=color, width=width)


def _wrap_lossless(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    output = []
    for source in text.splitlines() or [""]:
        if not source:
            output.append(""); continue
        while source:
            low, high = 1, len(source)
            while low < high:
                middle = (low + high + 1) // 2
                if draw.textlength(source[:middle], font=font) <= width:
                    low = middle
                else:
                    high = middle - 1
            output.append(source[:low]); source = source[low:]
    return output


def _palette(name: str) -> dict[str, str]:
    return {
        "canonical": {"text": "#14242e", "muted": "#657580", "border": "#365260", "metric": "#d64c35", "edge": "#e56a45", "node": "#f3c06b", "missing": "#d9dee2"},
        "colorblind": {"text": "#171717", "muted": "#646464", "border": "#4d4d4d", "metric": "#0072b2", "edge": "#d55e00", "node": "#f0e442", "missing": "#d7d7d7"},
    }[name]


def _tile_bbox(spec: DashboardSpecV3, placement: CardPlacementV1) -> tuple[int, int, int, int]:
    left = spec.gutter_px + placement.column * (spec.cell_edge_px + spec.gutter_px)
    top = spec.header_px + spec.gutter_px + placement.row * (spec.cell_edge_px + spec.gutter_px)
    width = placement.width_cells * spec.cell_edge_px + (placement.width_cells - 1) * spec.gutter_px
    height = placement.height_cells * spec.cell_edge_px + (placement.height_cells - 1) * spec.gutter_px
    return left, top, left + width, top + height


def _draw_metric_card(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fact: Mapping[str, Any],
    encoding: str, palette: Mapping[str, str], spec: DashboardSpecV3,
    common_scale: tuple[float, float] | None,
) -> dict[str, Any]:
    x0, y0, x1, y1 = box; payload = fact.get("payload") or {}
    label_font = _font(_pt(spec, 10), True)
    labels = _wrap_lossless(draw, f"{payload.get('panel_id')} · {payload.get('service')} · {payload.get('metric')}", label_font, x1 - x0 - 18)
    if len(labels) > 3:
        raise ValueError("metric label needs a wider silhouette")
    label_y = y0 + 31
    for line in labels:
        draw.text((x0 + 9, label_y), line, font=label_font, fill=palette["text"]); label_y += 12
    draw.text((x0 + 9, label_y + 1), f"peak={payload.get('peak')} z={payload.get('signed_z')} unit={fact.get('unit')}", font=_font(_pt(spec, 8)), fill=palette["muted"])
    values = []
    for raw in payload.get("values") or ():
        try:
            values.append(float(raw))
        except (TypeError, ValueError):
            values.append(None)
    numeric = [value for value in values if value is not None]
    low, high = common_scale if common_scale is not None else ((min(numeric), max(numeric)) if numeric else (0.0, 1.0))
    span = high - low or 1.0
    left, top, right, bottom = x0 + 10, label_y + 19, x1 - 10, y1 - 30
    primitives = []
    if encoding == "heatmap":
        cell = (right - left) / max(1, len(values))
        for index, value in enumerate(values):
            bx0, bx1 = round(left + index * cell), round(left + (index + 1) * cell)
            if value is None:
                color = palette["missing"]
            else:
                level = (value - low) / span
                color = f"#{int(245 - 25 * level):02x}{int(245 - 145 * level):02x}{int(250 - 175 * level):02x}"
            draw.rectangle((bx0, top, max(bx0 + 1, bx1), bottom), fill=color)
            primitives.append({"bin": index, "bbox": [bx0, top, max(bx0 + 1, bx1), bottom], "missing": value is None})
    else:
        segment: list[tuple[float, float]] = []
        for index, value in enumerate(values):
            x = left + index * (right - left) / max(1, len(values) - 1)
            if value is None:
                if len(segment) > 1:
                    draw.line(segment, fill=palette["metric"], width=3)
                segment = []
                draw.line((x, bottom - 5, x, bottom), fill=palette["missing"], width=2)
                primitives.append({"bin": index, "bbox": [round(x - 1), bottom - 5, round(x + 1), bottom], "missing": True})
                continue
            y = bottom - (value - low) / span * max(1, bottom - top)
            segment.append((x, y)); primitives.append({"bin": index, "point": [round(x, 2), round(y, 2)], "missing": False})
        if len(segment) > 1:
            draw.line(segment, fill=palette["metric"], width=3)
    anchors = [index for index in (0, 16, 32, 48, 63) if index < len(values)]
    anchor_text = "  ".join(f"b{index}={values[index] if values[index] is not None else 'missing'}" for index in anchors)
    draw.text((left, y1 - 23), anchor_text, font=_font(_pt(spec, 7)), fill=palette["text"])
    draw.text((right - 120, top), f"scale {low:g}..{high:g}", font=_font(_pt(spec, 7)), fill=palette["muted"])
    return {"kind": encoding, "bin_primitives": primitives, "displayed_anchor_bins": anchors, "scale": [low, high]}


def _draw_topology_card(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], facts: Sequence[Mapping[str, Any]],
    encoding: str, palette: Mapping[str, str], spec: DashboardSpecV3,
) -> dict[str, list[dict[str, Any]]]:
    x0, y0, x1, y1 = box
    edges = [fact for fact in facts if fact.get("field") == "directed_call_edge"]
    nodes = sorted({str(fact["payload"][key]) for fact in edges for key in ("caller", "callee")})
    left, top, right, bottom = x0 + 12, y0 + 38, x1 - 12, y1 - 34
    geometry: dict[str, list[dict[str, Any]]] = {str(fact["fact_id"]): [] for fact in facts}
    meta_facts = [fact for fact in facts if fact.get("field") != "directed_call_edge"]
    meta_text = " | ".join(
        f"{fact.get('field')}={canonical_json(fact.get('payload') or {})}" for fact in meta_facts
    )
    if meta_text:
        font = _font(_pt(spec, 7)); lines = _wrap_lossless(draw, meta_text, font, x1-x0-18)
        if len(lines) > 3:
            raise ValueError("topology metadata needs a larger silhouette")
        start_y = y1 - 9 - 10 * len(lines)
        for index, line in enumerate(lines):
            draw.text((x0+9,start_y+10*index),line,font=font,fill=palette["muted"])
        for fact in meta_facts:
            geometry[str(fact["fact_id"])].append({"kind":"topology_meta_text","bbox":[x0+9,start_y,x1-9,y1-9]})
    if not edges:
        draw.text((left, top), "No directed edge is present in this card.", font=_font(_pt(spec, 11)), fill=palette["muted"])
        return geometry
    if encoding == "edge_table":
        y = top
        for fact in edges:
            payload = fact["payload"]
            text = f"{payload['caller']}  →  {payload['callee']}"
            draw.text((left, y), text, font=_font(_pt(spec, 11), True), fill=palette["text"])
            geometry[str(fact["fact_id"])].append({"kind": "edge_table_row", "bbox": [left, y, right, y + 15]})
            y += 17
        return geometry
    if encoding == "adjacency_matrix":
        label_width = max(48, max(len(node) for node in nodes) * _pt(spec, 6))
        size = max(8, min((right - left - label_width) // max(1, len(nodes)), (bottom - top - 18) // max(1, len(nodes))))
        index = {node: position for position, node in enumerate(nodes)}; matrix_left = left + label_width
        for position, node in enumerate(nodes):
            draw.text((matrix_left + position * size, top - 15), node, font=_font(_pt(spec, 7)), fill=palette["text"])
            draw.text((left, top + position * size), node, font=_font(_pt(spec, 7)), fill=palette["text"])
        for fact in edges:
            caller, callee = str(fact["payload"]["caller"]), str(fact["payload"]["callee"])
            bx, by = matrix_left + index[callee] * size, top + index[caller] * size
            draw.rectangle((bx, by, bx + size - 1, by + size - 1), fill=palette["edge"])
            geometry[str(fact["fact_id"])].append({"kind": "matrix_cell", "bbox": [bx, by, bx + size - 1, by + size - 1]})
    else:
        cx, cy = (left + right) / 2, (top + bottom) / 2; radius = max(20, min(right - left, bottom - top) * .34)
        positions = {node: (cx + radius * math.cos(2 * math.pi * i / len(nodes)), cy + radius * math.sin(2 * math.pi * i / len(nodes))) for i, node in enumerate(nodes)}
        for fact in edges:
            start, end = positions[str(fact["payload"]["caller"])], positions[str(fact["payload"]["callee"])]
            _arrow(draw, start, end, palette["edge"], 2)
            geometry[str(fact["fact_id"])].append({"kind": "directed_arrow", "start": list(start), "end": list(end)})
        for node, (x, y) in positions.items():
            draw.ellipse((x - 14, y - 14, x + 14, y + 14), fill=palette["node"], outline=palette["border"])
            label = node
            draw.text((x - max(12, len(label) * 3), y - 5), label, font=_font(_pt(spec, 7), True), fill=palette["text"])
    return geometry


def _draw_trace_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fact: Mapping[str, Any], encoding: str, palette: Mapping[str, str], spec: DashboardSpecV3) -> dict[str, Any]:
    x0, y0, x1, y1 = box; payload = fact.get("payload") or {}
    font = _font(_pt(spec, 9)); bold = _font(_pt(spec, 10), True)
    title_lines = _wrap_lossless(draw, f"entity={payload.get('service')} op={payload.get('operation')}", bold, x1-x0-18)
    if len(title_lines) > 3: raise ValueError("trace title needs a larger silhouette")
    for index,line in enumerate(title_lines): draw.text((x0+9,y0+33+12*index),line,font=bold,fill=palette["text"])
    pairs = [
        ("count", payload.get("count_base"), payload.get("count_fault")),
        ("exclusive p95 ms", payload.get("exl_p95_base_ms"), payload.get("exl_p95_fault_ms")),
    ]
    rows = []
    for row_index, (label, before, after) in enumerate(pairs):
        y = y0 + 58 + 12*(len(title_lines)-1) + row_index * max(38, (y1 - y0 - 80) // 2)
        draw.text((x0 + 9, y), f"{label}: {before} → {after}", font=font, fill=palette["text"])
        try:
            left_value, right_value = float(before), float(after); maximum = max(abs(left_value), abs(right_value), 1.0)
        except (TypeError, ValueError):
            left_value = right_value = 0.0; maximum = 1.0
        start, end = x0 + 12, x1 - 12
        if encoding == "trace_dumbbell":
            xb = start + abs(left_value) / maximum * (end - start)
            xa = start + abs(right_value) / maximum * (end - start)
            draw.line((xb, y + 22, xa, y + 22), fill=palette["border"], width=3)
            draw.ellipse((xb - 5, y + 17, xb + 5, y + 27), fill=palette["node"])
            draw.ellipse((xa - 5, y + 17, xa + 5, y + 27), fill=palette["metric"])
        else:
            xb = start + abs(left_value) / maximum * (end - start)
            xa = start + abs(right_value) / maximum * (end - start)
            draw.rectangle((start, y + 17, xb, y + 24), fill=palette["node"])
            draw.rectangle((start, y + 28, xa, y + 35), fill=palette["metric"])
        rows.append({"field": label, "bbox": [start, y + 17, end, y + 35], "base": before, "fault": after})
    return {"kind": encoding, "rows": rows}


def _draw_log_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fact: Mapping[str, Any], encoding: str, palette: Mapping[str, str], spec: DashboardSpecV3) -> dict[str, Any]:
    x0, y0, x1, y1 = box; payload = fact.get("payload") or {}
    font = _font(_pt(spec, 8)); bold = _font(_pt(spec, 10), True)
    draw.text((x0 + 9, y0 + 33), f"{payload.get('template_id')} entity={payload.get('entity_id')} count={payload.get('count')} bin={payload.get('relative_bin')}", font=bold, fill=palette["text"])
    line_y = y0 + 51
    template = str(payload.get("template") or "")
    template_lines = _wrap_lossless(draw, template, font, x1-x0-18)
    if len(template_lines)>5: raise ValueError("log template needs a larger silhouette")
    for line in template_lines:
        draw.text((x0 + 9, line_y), line, font=font, fill=palette["text"]); line_y += 11
    left, right = x0 + 10, x1 - 10
    preview_rows = []
    for name, row in sorted((payload.get("numeric_preview") or {}).items()):
        if isinstance(row, Mapping):
            preview_rows.append(
                f"{name}(n={row.get('sample_count')},first={row.get('first')},last={row.get('last')},"
                f"distinct={row.get('distinct_count')},top={canonical_json(row.get('most_common') or [])})"
            )
        else:
            preview_rows.append(f"{name}={canonical_json(row)}")
    preview = ";".join(preview_rows) or "{}"
    preview_lines = _wrap_lossless(draw, f"numeric={preview}", _font(_pt(spec,7)), x1-x0-18)
    if len(preview_lines)>3: raise ValueError("log numeric preview needs a larger silhouette")
    preview_y=y1-8-9*len(preview_lines)
    timeline_y = min(preview_y - 22, line_y + 5)
    if timeline_y < line_y: raise ValueError("log card content needs a larger silhouette")
    bin_index = max(0, min(63, int(payload.get("relative_bin") or 0)))
    if encoding == "template_time_matrix":
        cell = (right - left) / 64
        for index in range(64):
            color = palette["edge"] if index == bin_index else palette["missing"]
            draw.rectangle((round(left + index * cell), timeline_y, round(left + (index + 1) * cell), timeline_y + 18), fill=color)
    else:
        draw.line((left, timeline_y + 9, right, timeline_y + 9), fill=palette["border"], width=2)
        x = left + bin_index / 63 * (right - left)
        radius = min(12, 4 + int(math.log2(max(1, int(payload.get("count") or 1)))))
        draw.ellipse((x - radius, timeline_y + 9 - radius, x + radius, timeline_y + 9 + radius), fill=palette["edge"])
    for index,line in enumerate(preview_lines): draw.text((left,preview_y+9*index),line,font=_font(_pt(spec,7)),fill=palette["muted"])
    return {"kind": encoding, "relative_bin": bin_index, "timeline_bbox": [left, timeline_y, right, timeline_y + 18]}


def _draw_propagation_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], facts: Sequence[Mapping[str, Any]], encoding: str, palette: Mapping[str, str], spec: DashboardSpecV3) -> dict[str, list[dict[str, Any]]]:
    x0, y0, x1, y1 = box; ordered = sorted(facts, key=lambda row: int((row.get("payload") or {}).get("rank", 10**9)))
    geometry: dict[str, list[dict[str, Any]]] = {}
    if encoding == "propagation_rows":
        return _draw_text_card(draw, box, facts, "propagation_order", palette, spec)
    onsets = []
    for fact in ordered:
        raw = str((fact.get("payload") or {}).get("onset_rel_min_display") or "")
        try: onsets.append(float(raw.removeprefix("+").removesuffix("m")))
        except ValueError: onsets.append(None)
    numeric = [value for value in onsets if value is not None]; low, high = (min(numeric), max(numeric)) if numeric else (0.0, 1.0); span = high-low or 1.0
    for index, (fact, onset) in enumerate(zip(ordered, onsets, strict=True)):
        payload = fact.get("payload") or {}; y = y0 + 35 + index * max(12, (y1-y0-45)//max(1,len(ordered)))
        draw.text((x0+9,y), str(payload.get("service")), font=_font(_pt(spec, 8)), fill=palette["text"])
        start=x0+70; end=x1-10; x=start if onset is None else start+(onset-low)/span*(end-start)
        draw.line((start,y+5,end,y+5),fill=palette["missing"],width=2); draw.ellipse((x-4,y+1,x+4,y+9),fill=palette["edge"])
        geometry[str(fact["fact_id"])]=[{"kind":"onset_point","point":[x,y+5],"display":payload.get("onset_rel_min_display")}]
    return geometry


def _draw_text_card(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int],
    facts: Sequence[Mapping[str, Any]], semantic_type: str,
    palette: Mapping[str, str], spec: DashboardSpecV3,
) -> dict[str, list[dict[str, Any]]]:
    x0, y0, x1, y1 = box
    if semantic_type == "propagation_order":
        lines = []
        for fact in sorted(facts, key=lambda row: int((row.get("payload") or {}).get("rank", 10**9))):
            payload = fact.get("payload") or {}
            lines.append(
                f"rank={payload.get('rank')} entity={payload.get('service')} "
                f"onset={payload.get('onset_rel_min_display')} severity={payload.get('severity_z_display')} "
                f"source={payload.get('evidence_source_display')}"
            )
        text = "\n".join(lines)
    else:
        text = "\n".join(f"{fact.get('field')}: {canonical_json(fact.get('payload') or {})}" for fact in facts)
    for size in (12, 11, 10, 9, 8, 7):
        font = _font(_pt(spec, size)); lines = _wrap_lossless(draw, text, font, x1 - x0 - 18)
        line_height = max(9, font.getbbox("Ag")[3] - font.getbbox("Ag")[1] + 2)
        if len(lines) * line_height <= y1 - y0 - 43:
            y = y0 + 34
            for line in lines:
                draw.text((x0 + 9, y), line, font=font, fill=palette["text"]); y += line_height
            return {str(fact["fact_id"]): [{"kind": "text_rows", "bbox": [x0 + 9, y0 + 34, x1 - 9, y]}] for fact in facts}
    raise ValueError("card content cannot fit its silhouette without clipping")


def render_dashboard_design(packet: Mapping[str, Any], spec: DashboardSpecV3) -> tuple[bytes, dict[str, Any]]:
    program = compile_dashboard_program(packet, spec); validate_card_silhouette_bijection(program)
    if spec.panel_composition == "human_composite":
        from .human_dashboard import render_human_dashboard

        return render_human_dashboard(packet, spec, program)
    palette = _palette(spec.style_skin); image = Image.new("RGB", spec.logical_canvas_size, NEUTRAL); draw = ImageDraw.Draw(image)
    draw.text((spec.gutter_px, 12), "RCA DASHBOARD — EVIDENCE CARDS ON A SILHOUETTE GRID", font=_font(_pt(spec, 28), True), fill=palette["text"])
    draw.text((spec.gutter_px, 50), "Each selected evidence card maps to exactly one visual silhouette · 3 digits=service · 4 digits=node · 5 digits=pod · relative time only · missing ≠ zero", font=_font(_pt(spec, 14)), fill=palette["muted"])
    draw.text((spec.gutter_px, 70), f"coordination={spec.coordination_mode} · metric scale={spec.metric_scale_policy} · caller → callee uses arrow direction", font=_font(_pt(spec, 9)), fill=palette["muted"])
    all_facts = {str(fact["fact_id"]): fact for fact in packet.get("facts") or ()}
    metric_values = []
    if spec.metric_scale_policy == "common_robust":
        for fact in all_facts.values():
            if fact.get("field") == "metric_series_64":
                for value in (fact.get("payload") or {}).get("values") or ():
                    try: metric_values.append(float(value))
                    except (TypeError, ValueError): pass
    common_scale = (min(metric_values), max(metric_values)) if metric_values else None
    cards = {card.card_id: card for card in program.cards}; silhouettes = {value.card_id: value for value in program.silhouettes}
    mapping, card_rows = [], []
    for placement in program.placements:
        card, silhouette = cards[placement.card_id], silhouettes[placement.card_id]; box = _tile_bbox(spec, placement)
        draw.rectangle(box, fill="white", outline=palette["border"], width=2)
        draw.text((box[0] + 8, box[1] + 8), f"{card.region} · {card.semantic_type} · {silhouette.encoding} · {placement.width_cells}×{placement.height_cells}", font=_font(_pt(spec, 13), True), fill=palette["text"])
        if spec.coordination_mode == "shared_entity" and card.entity_ids:
            color = _entity_color(card.entity_ids[0]); marker = (box[2]-22, box[1]+8, box[2]-8, box[1]+22)
            draw.rectangle(marker, fill=color, outline=palette["border"])
        elif spec.coordination_mode == "shared_time" and card.region in {"M", "R", "L", "G"}:
            draw.line((box[0]+8, box[1]+27, box[2]-8, box[1]+27), fill=palette["border"], width=2)
            for fraction in (0, .25, .5, .75, 1):
                x=box[0]+8+fraction*(box[2]-box[0]-16); draw.line((x,box[1]+24,x,box[1]+30),fill=palette["border"],width=1)
        facts = [all_facts[fact_id] for fact_id in card.fact_ids]
        if card.semantic_type == "metric_series":
            primitive = {str(facts[0]["fact_id"]): [_draw_metric_card(draw, box, facts[0], silhouette.encoding, palette, spec, common_scale)]}
        elif card.semantic_type == "trace_entry":
            primitive = {str(facts[0]["fact_id"]): [_draw_trace_card(draw, box, facts[0], silhouette.encoding, palette, spec)]}
        elif card.semantic_type == "log_template":
            primitive = {str(facts[0]["fact_id"]): [_draw_log_card(draw, box, facts[0], silhouette.encoding, palette, spec)]}
        elif card.semantic_type == "topology_graph":
            primitive = _draw_topology_card(draw, box, facts, silhouette.encoding, palette, spec)
        elif card.semantic_type == "propagation_order":
            primitive = _draw_propagation_card(draw, box, facts, silhouette.encoding, palette, spec)
        else:
            primitive = _draw_text_card(draw, box, facts, card.semantic_type, palette, spec)
        for fact_id in card.fact_ids:
            mapping.append({"fact_id": fact_id, "card_id": card.card_id, "silhouette_id": silhouette.silhouette_id, "primitive": silhouette.encoding, "primitive_geometry": primitive.get(fact_id, []), "bbox": list(box)})
        card_rows.append({"card": asdict(card), "silhouette": asdict(silhouette), "placement": asdict(placement), "bbox": list(box)})
    mapped = [str(row["fact_id"]) for row in mapping]; expected = sorted(fact_id for card in program.cards for fact_id in card.fact_ids)
    if sorted(mapped) != expected or len(mapped) != len(set(mapped)):
        raise ValueError("rendered card facts are not exact-once")
    width, height = spec.logical_canvas_size
    if any(row["bbox"][0] < 0 or row["bbox"][1] < 0 or row["bbox"][2] > width or row["bbox"][3] > height for row in mapping):
        raise ValueError("a silhouette leaves the canvas")
    if spec.raster_scale != 1.0:
        image = image.resize(spec.canvas_size, Image.Resampling.LANCZOS)
        for row in (*mapping, *card_rows):
            row["bbox"] = [round(value * spec.raster_scale) for value in row["bbox"]]
    stream = io.BytesIO(); image.save(stream, format="PNG", optimize=False, compress_level=6)
    selected = [all_facts[fact_id] for fact_id in expected]; common = [fact for fact in packet.get("facts") or () if fact.get("region") == "C"]
    full_visible = sorted((*common, *selected), key=lambda fact: (str(fact.get("region")), str(fact.get("field")), str(fact.get("fact_id"))))
    manifest = {
        "schema_version": "CanvasRCARQ2CardGridRenderManifestV1",
        "spec": asdict(spec), "cell_id": spec.cell_id, "program_hash": program.program_hash,
        "canvas_size": list(spec.canvas_size),
        "grid": {"columns": spec.grid_columns, "rows": spec.grid_rows, "logical_cell_edge_px": spec.cell_edge_px, "logical_gutter_px": spec.gutter_px, "raster_scale": spec.raster_scale},
        "cards": card_rows, "fact_mapping": mapping,
        "source_packet_fact_inventory_hash": packet["fact_inventory_hash"],
        "fact_inventory_hash": stable_hash(full_visible),
        "visual_fact_inventory_hash": stable_hash(selected),
        "selected_fact_id_hash": program.selected_fact_inventory_hash,
        "common_fact_inventory_hash": stable_hash(common),
        "card_silhouette_bijection": {"status": "passed", "cards": len(program.cards), "silhouettes": len(program.silhouettes)},
        "packing_audit": {"status": "passed", "mode": spec.packing_mode, "occupancy": program.occupancy, "empty_cells": program.empty_cells, "overlap_cells": 0, "footprint_downgrades": program.footprint_downgrades},
        "clipping_audit": {"status": "passed", "out_of_bounds_fact_ids": [], "card_local_overflow": False},
        "label_blind": True,
    }
    manifest["manifest_sha256"] = stable_hash(manifest)
    return stream.getvalue(), manifest


__all__ = [
    "CANVAS_SIZE", "COMPOSER_ACTION_ORDER", "CardPlacementV1", "ComposerActionV1",
    "ComposerStateV1", "DashboardProgramV1", "DashboardSpecV1", "DashboardSpecV2",
    "DashboardSpecV3", "EvidenceCardV1", "PANEL_COMPOSITIONS", "REGIONS", "SilhouetteV1",
    "apply_composer_action", "build_evidence_cards", "compile_composer_sft_example",
    "compile_dashboard_program", "composer_sft_actions", "policy_regions",
    "render_dashboard_design", "replay_composer_sft_trace", "space_filling_specs",
    "validate_card_silhouette_bijection",
]

"""CPU-only geometry and real-painter regression tests for the RQ3 renderer."""
from copy import deepcopy
from dataclasses import replace
import io
import random

from PIL import Image
import pytest
from unified_scripts import stable_hash
from .constraint_layout import compile_constraint_program, render_constraint_dashboard, audit_pixel_program
from .designs import DashboardSpecV3, _make_card, compile_dashboard_program
from .human_dashboard import render_human_dashboard


def packet_cards(count=4):
    facts = [{"fact_id": f"f{i}", "region": "G", "field": "directed_call_edge",
              "payload": {"caller": str(100 + i), "callee": str(101 + i), "edge_index": i},
              "entities": [str(100 + i), str(101 + i)]} for i in range(count)]
    cards = tuple(replace(_make_card([f], "G", "topology_bundle"),
                          card_id=f"G{i:03d}", footprint_options=((2, 2), (3, 1)))
                  for i, f in enumerate(facts))
    return {"facts": facts, "fact_inventory_hash": stable_hash(facts)}, cards


def tree_for(cards, axis="x", ratio=.5):
    if len(cards) == 1:
        return {"card": cards[0].card_id}
    mid = len(cards) // 2
    return {"axis": axis, "ratio": ratio,
            "children": [tree_for(cards[:mid], "y" if axis == "x" else "x"),
                         tree_for(cards[mid:], "y" if axis == "x" else "x")]}


def test_continuous_ratio_changes_geometry_not_facts():
    packet, cards = packet_cards()
    spec = DashboardSpecV3()
    a = compile_constraint_program(packet, spec, cards, tree_for(cards, ratio=.432))
    b = compile_constraint_program(packet, spec, cards, tree_for(cards, ratio=.613))
    assert a.selected_fact_inventory_hash == b.selected_fact_inventory_hash
    assert a.layout_audit["pixel_geometry_hash"] != b.layout_audit["pixel_geometry_hash"]
    assert a.layout_audit["projection"][0]["realized_ratio"] == pytest.approx(.432, abs=.001)
    assert a.program_hash == compile_constraint_program(packet, spec, cards, tree_for(cards, ratio=.432)).program_hash


def test_pixel_quantization_reports_noop():
    packet, cards = packet_cards(2)
    a = compile_constraint_program(packet, DashboardSpecV3(), cards, tree_for(cards, ratio=.5))
    b = compile_constraint_program(packet, DashboardSpecV3(), cards, tree_for(cards, ratio=.50000001))
    assert a.program_hash != b.program_hash
    assert a.layout_audit["pixel_geometry_hash"] == b.layout_audit["pixel_geometry_hash"]


def test_projection_retains_all_cards():
    packet, cards = packet_cards(2)
    program = compile_constraint_program(packet, DashboardSpecV3(), cards, tree_for(cards, ratio=.05))
    assert program.layout_audit["projection"][0]["projected"]
    assert {p.card_id for p in program.placements} == {c.card_id for c in cards}


@pytest.mark.parametrize("value", [None, True, False, "0.5", float("nan"), float("inf"), -.2, 0., 1.])
def test_invalid_ratios_fail(value):
    packet, cards = packet_cards(2)
    with pytest.raises(ValueError, match="ratio"):
        compile_constraint_program(packet, DashboardSpecV3(), cards, tree_for(cards, ratio=value))


@pytest.mark.parametrize("kind", ["repeat", "unknown", "omitted", "extra_field", "axis", "cycle"])
def test_tree_rejects_silent_interpretation(kind):
    packet, cards = packet_cards(2)
    tree = tree_for(cards)
    if kind == "repeat": tree["children"][1] = tree["children"][0]
    if kind == "unknown": tree["children"][1] = {"card": "not-a-card"}
    if kind == "omitted": tree = tree["children"][0]
    if kind == "extra_field": tree["secret"] = "answer"
    if kind == "axis": tree["axis"] = "diagonal"
    if kind == "cycle": tree["children"][0] = tree
    with pytest.raises(ValueError): compile_constraint_program(packet, DashboardSpecV3(), cards, tree)


def test_exact_once_and_hash_binding():
    packet, cards = packet_cards(2)
    with pytest.raises(ValueError, match="exact-once"):
        compile_constraint_program(packet, DashboardSpecV3(), cards[:1], tree_for(cards[:1]))
    bad = deepcopy(packet)
    bad["facts"][0]["payload"]["caller"] = "999"
    with pytest.raises(ValueError, match="hashing"):
        compile_constraint_program(bad, DashboardSpecV3(), cards, tree_for(cards))
    bad["fact_inventory_hash"] = stable_hash(bad["facts"])
    with pytest.raises(ValueError, match="binding"):
        compile_constraint_program(bad, DashboardSpecV3(), cards, tree_for(cards))
    with pytest.raises(ValueError, match="encoding"):
        compile_constraint_program(packet, DashboardSpecV3(), cards, tree_for(cards), encodings={cards[0].card_id: "heatmap"})


def test_infeasible_does_not_delete_cards():
    packet, cards = packet_cards(2)
    cards = tuple(replace(c, footprint_options=((18, 12),)) for c in cards)
    with pytest.raises(ValueError, match="cannot fit"):
        compile_constraint_program(packet, DashboardSpecV3(), cards, tree_for(cards))


def test_independent_audit_detects_overlap_and_boundary():
    packet, cards = packet_cards(2)
    p = compile_constraint_program(packet, DashboardSpecV3(), cards, tree_for(cards))
    bad = replace(p, placements=(p.placements[0], replace(p.placements[1], pixel_bbox=p.placements[0].pixel_bbox)))
    with pytest.raises(ValueError, match="overlap"): audit_pixel_program(bad)
    bad = replace(p, placements=(replace(p.placements[0], pixel_bbox=(0, 0, 50, 50)), p.placements[1]))
    with pytest.raises(ValueError, match="viewport"): audit_pixel_program(bad)


def test_random_layouts_have_no_overlap():
    rng = random.Random(42)
    for count in range(1, 9):
        packet, cards = packet_cards(count)
        for _ in range(12):
            tree = tree_for(cards, rng.choice(("x", "y")), rng.uniform(.05, .95))
            p = compile_constraint_program(packet, DashboardSpecV3(grid_rows=12), cards, tree)
            assert 0 < p.layout_audit["occupancy"] <= 1
            assert p.layout_audit["overlap_area_px"] == 0


def test_real_painter_distinct_layouts_and_per_card_encodings():
    packet, cards = packet_cards(2)
    spec = DashboardSpecV3(grid_rows=4)
    options = {cards[0].card_id: "node_link", cards[1].card_id: "edge_table"}
    a, ma = render_constraint_dashboard(packet, spec, cards, tree_for(cards, ratio=.45), encodings=options)
    b, mb = render_constraint_dashboard(packet, spec, cards, tree_for(cards, ratio=.65), encodings=options)
    assert Image.open(io.BytesIO(a)).size == spec.canvas_size
    assert a != b
    assert ma["visual_fact_inventory_hash"] == mb["visual_fact_inventory_hash"]
    assert {f["primitive"] for f in ma["fact_mapping"]} == {"node_link", "edge_table"}
    assert all(f["primitive_geometry"] for f in ma["fact_mapping"])
    assert ma["clipping_audit"]["status"] == "passed"


def test_existing_grid_renderer_still_deterministic():
    packet, cards = packet_cards(2)
    cards = tuple(replace(c, footprint_options=((6, 4),)) for c in cards)
    spec = DashboardSpecV3(topology_encoding="edge_table")
    program = compile_dashboard_program(packet, spec, explicit_cards=cards)
    first = render_human_dashboard(packet, spec, program)
    assert first == render_human_dashboard(packet, spec, program)
    assert first[1]["packing_audit"]["mode"] == "reflow"

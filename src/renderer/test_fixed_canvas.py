"""Small policy regression; real rendering is separately sampled, not full-suite."""
from copy import deepcopy

import pytest

from .exps import preset as legacy_preset
from .fixed_canvas import default_components, layout_from_measurements
from .operations import apply_operations
from .operations.dashboard_policy import apply
from .tests import sample
from .utils import compile_design, digest


def metric_cards(count):
    card = sample()["cards"][0]
    cards = []
    for i in range(count):
        item = deepcopy(card); item["id"] = f"M{i + 1}"
        cards.append(item)
    return {"schema": "CanvasEvidenceV1", "cards": cards}


def measurements(evidence, height=512):
    return [{"region_width": width, "cards": [{"card": c["id"], "width": width,
        "height": height, "overflow": [], "min_font": 18} for c in evidence["cards"]]}
        for width in (1000, 1338, 2016, 4048)]


def test_28_cards_fit_deterministically_without_mutation():
    evidence = metric_cards(28); before = digest(evidence)
    d = layout_from_measurements(evidence, default_components(evidence), measurements(evidence))
    scene = compile_design(evidence, d)
    assert (scene["width"], scene["height"]) == (4096, 4096)
    assert len(scene["rectangles"]) == 28 and digest(evidence) == before
    assert scene == compile_design(deepcopy(evidence), deepcopy(d))
    assert all(r["width"] == 1000 and r["height"] >= 512 for r in scene["rectangles"])


def test_29_cards_rejected_without_selection():
    e = metric_cards(29)
    with pytest.raises(ValueError, match="28 cards"):
        layout_from_measurements(e, default_components(e), measurements(e))
    # An explicit hand-built layout is subject to the same policy.
    d = legacy_preset(e); apply(d)
    with pytest.raises(ValueError, match="28 cards"):
        compile_design(e, d)


def test_subsequent_operations_cannot_bypass_policy():
    e = sample(); d = legacy_preset(e)
    d, _ = apply_operations(e, d, [{"op": "dashboard_policy", "args": {}}])
    for op in [{"op": "resolution", "args": {"scale": 2}},
               {"op": "viewport", "args": {"width": 8192, "height": 4096}}]:
        with pytest.raises(ValueError, match="4096x4096"):
            apply_operations(e, d, [op])


def test_overflow_or_too_tall_is_rejected_not_shrunk():
    e = metric_cards(28); components = default_components(e)
    with pytest.raises(ValueError, match="do not fit"):
        layout_from_measurements(e, components, measurements(e, height=900))
    rows = measurements(e)
    for size in rows:
        size["cards"][0]["overflow"] = ["long label"]
    with pytest.raises(ValueError, match="do not fit"):
        layout_from_measurements(e, components, rows)


def test_historical_design_geometry_and_inventory_unchanged():
    e = sample(); d = legacy_preset(e)
    scene = compile_design(e, d)
    assert scene["width"] == 1800 and "dashboard_policy" not in d
    assert len(scene["rectangles"]) == len(e["cards"])


def test_sparse_layout_uses_measured_content_not_stretched_backgrounds():
    e = metric_cards(8)
    d = layout_from_measurements(e, default_components(e), measurements(e, height=640))
    scene = compile_design(e, d)
    # One column is too tall. Two columns use the greatest content area
    # of the feasible options, avoiding four skinny mostly empty cards per row.
    assert all(r["width"] == 2016 for r in scene["rectangles"])

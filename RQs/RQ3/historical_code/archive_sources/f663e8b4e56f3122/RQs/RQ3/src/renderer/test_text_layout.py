"""Pure CPU tests of the RQ3-local renderer, without inference or source data."""
import pytest
from PIL import Image, ImageDraw

from . import human_dashboard as dashboard
from .layout_audit import AuditedDraw


def _log_fixture(length):
    from .designs import _make_card
    from unified_scripts import stable_hash
    facts = [{"fact_id": "L1", "region": "L", "field": "denum_log_template", "entity_ids": ["123"],
              "payload": {"entity_id": "123", "template_id": "LT01", "relative_bin": 4,
                          "count": 2, "level": "ERROR", "template": "request= " + "1,234,567 " * length}}]
    return {"facts": facts, "fact_inventory_hash": stable_hash(facts)}, _make_card(facts, "L", "log_bundle")


@pytest.mark.parametrize("text", ["long diagnostic detail " * 80,
                                   'id={"numbers":[1234567890,504,1.2]}' * 20,
                                   "AV ffi 中文 العربية e\u0301 " * 20])
def test_wrap_width_cache_preserves_exact_shaped_prefixes(text):
    import re
    font = dashboard._font(9)
    draw = ImageDraw.Draw(Image.new("RGB", (320, 240)))
    rows, line = [], ""
    # Frozen predecessor algorithm, including its character-level checks.
    for word in re.findall(r"\S+\s*|\s+", text):
        if line and draw.textlength(line + word, font=font) > 240:
            rows.append(line)
            line = ""
        for character in word:
            if line and draw.textlength(line + character, font=font) > 240:
                rows.append(line)
                line = ""
            assert draw.textlength(character, font=font) <= 240
            line += character
    if line:
        rows.append(line)
    assert dashboard._wrap(draw, text, font, 240) == rows
    assert "".join(rows) == text


def test_log_profile_measures_full_content_and_does_not_mutate_facts():
    from copy import deepcopy
    from dataclasses import replace
    from .capacity import rendering_profile, _log_height
    from .designs import DashboardSpecV3, compile_dashboard_program
    packet, card = _log_fixture(1200)
    before = deepcopy(packet)
    facts = {f["fact_id"]: f for f in packet["facts"]}
    profile = rendering_profile(card, facts)
    spec = DashboardSpecV3()
    options = profile["footprints_by_encoding"][spec.log_encoding]
    assert options and not any(tuple(s) in card.footprint_options for s in options)
    assert profile == rendering_profile(card, facts, replace(spec, raster_scale=1.5))
    compiled = compile_dashboard_program(packet, spec, explicit_cards=(card,))
    assert compiled.cards == (card,) and tuple(compiled.cards[0].fact_ids) == ("L1",)
    selected = compiled.placements[0]
    assert [selected.width_cells, selected.height_cells] in options
    box = dashboard._tile_bbox(spec, selected)
    assert _log_height(packet["facts"], box[2] - box[0], 1.18) <= box[3] - box[1]
    canvas = Image.new("RGB", spec.logical_canvas_size)
    draw = AuditedDraw(ImageDraw.Draw(canvas))
    draw.set_owner(card.card_id, box)
    mapping = dashboard._log_panel(draw, box, packet["facts"], spec.log_encoding, dashboard._palette("canonical"))
    assert set(mapping) == {"L1"} and draw.label_count > 0
    assert packet == before
    # Content changes must miss the cache even when the caller supplied a stale
    # fact-inventory hash; the profile is bound to actual source payloads too.
    facts["L1"]["payload"]["template"] = "ok"
    small = rendering_profile(card, facts)
    assert all(tuple(s) in card.footprint_options for s in small["footprints"])


def test_capacity_keeps_encoding_constraints_and_no_grid_growth():
    from dataclasses import replace
    from .capacity import rendering_profile
    from .designs import DashboardSpecV3, _make_card, _footprints, compile_dashboard_program
    facts = [{"fact_id": "M1", "region": "M", "field": "metric_series_64", "payload": {}, "entity_ids": ["123"]}]
    card = _make_card(facts, "M", "metric_bundle")
    profile = rendering_profile(card, {"M1": facts[0]})
    assert profile["footprints_by_encoding"]["overlay_lines"] == [[4, 4]]
    assert [3, 3] in profile["footprints_by_encoding"]["small_multiple_lines"]
    assert _footprints(card, "compact") == ((3, 3),)
    a = replace(card, card_id="A", footprint_options=((8, 8), (9, 9)))
    b = replace(card, card_id="B", fact_ids=("M2",), footprint_options=((8, 8), (9, 9)))
    packet = {"facts": facts + [{**facts[0], "fact_id": "M2"}]}
    spec = DashboardSpecV3(footprint_policy="compact")
    with pytest.raises(ValueError, match="minimum footprints exceed grid"):
        compile_dashboard_program(packet, spec, explicit_cards=(a, b))
    assert (spec.grid_columns, spec.grid_rows) == (12, 8)


def test_unrenderable_profile_remains_explicit(monkeypatch):
    from . import capacity
    from .designs import DashboardSpecV3, compile_dashboard_program
    packet, card = _log_fixture(11)
    monkeypatch.setattr(capacity, "_log_height", lambda *args: float("inf"))
    capacity._PROFILES.clear()
    try:
        profile = capacity.rendering_profile(card, {f["fact_id"]: f for f in packet["facts"]})
        assert profile["encodings"] == [] and profile["footprints"] == []
        with pytest.raises(ValueError, match="no feasible silhouette"):
            compile_dashboard_program(packet, DashboardSpecV3(), explicit_cards=(card,))
        assert packet["facts"][0]["payload"]["template"]
    finally:
        capacity._PROFILES.clear()


def test_ink_audit_preserves_pixels_and_rejects_overlap_and_overflow():
    original = Image.new("RGB", (200, 100), "white")
    checked = original.copy()
    raw, audit = ImageDraw.Draw(original), AuditedDraw(ImageDraw.Draw(checked))
    font = dashboard._font(12)
    for draw in (raw, audit):
        draw.text((10, 10), "M610 66009", font=font, fill="black")
    assert original.tobytes() == checked.tobytes()
    with pytest.raises(ValueError, match="text overlaps"):
        audit.text((10, 10), "M610 66009", font=font, fill="black")
    audit.set_owner("small", (0, 0, 20, 20))
    with pytest.raises(ValueError, match="text leaves card"):
        audit.text((15, 10), "66009", font=font, fill="black")


def test_ink_audit_checks_placed_bitmap_not_offscreen_origin():
    audit = AuditedDraw(ImageDraw.Draw(Image.new("RGB", (100, 100))))
    mask = Image.new("L", (10, 10), 255)
    audit.bitmap((10, 10), mask, fill="black")
    audit.bitmap((30, 10), mask, fill="black")
    assert audit.label_count == 2
    with pytest.raises(ValueError, match="text overlaps"):
        audit.bitmap((12, 10), mask, fill="black")


@pytest.mark.parametrize("height", [70, 120, 400])
def test_metric_label_uses_real_height_losslessly(height):
    draw = ImageDraw.Draw(Image.new("RGB", (400, 500)))
    title = "M610  66009 · container_network_transmit_packets.eth0"
    old_font, old_rows = dashboard._lossless_fit(draw, title, 174, start=14)
    assert len(old_rows) > 2
    font, rows = dashboard._lossless_fit(draw, title, 174, start=14, height=height)
    assert "".join(rows) == title
    assert all(draw.textlength(row, font=font) <= 174 for row in rows)
    assert max(i * (font.size + 1) + font.getbbox(row)[3]
               for i, row in enumerate(rows)) <= height
    assert font.size >= old_font.size


@pytest.mark.parametrize("height", [240, 792])
def test_long_metric_name_does_not_touch_summary(monkeypatch, height):
    draw = ImageDraw.Draw(Image.new("RGB", (792, height)))
    original, boxes = draw.text, []

    def capture(xy, text, **kwargs):
        boxes.append(draw.textbbox(xy, text, font=kwargs["font"]))
        return original(xy, text, **kwargs)

    monkeypatch.setattr(draw, "text", capture)
    monkeypatch.setattr(dashboard, "_metric_z", lambda p, v, g: v)
    fact = {"fact_id": "metric", "field": "metric_series_64", "payload": {
        "panel_id": "M610", "service": "66009",
        "metric": "container_network_transmit_packets.eth0", "values": [1.] * 64,
        "baseline": 1., "peak": 1., "signed_z": 0.}}
    result = dashboard._metric_panel(draw, (0, 0, 792, height), [fact],
                                    "small_multiple_lines", dashboard._palette("canonical"),
                                    "common_robust", {})
    labels = [b for b in boxes if b[0] == 14 and b[1] >= 68]
    assert all(a[3] <= b[1] for a, b in zip(labels, labels[1:]))
    assert len(result["metric"][0]["bin_primitives"]) == 64
    assert all(0 <= b[0] <= b[2] <= 792 and 0 <= b[1] <= b[3] <= height for b in boxes)
    fact["payload"]["metric"] = "a" * 10000
    with pytest.raises(ValueError, match="metric label cannot fit"):
        dashboard._metric_panel(draw, (0, 0, 792, height), [fact],
                                "small_multiple_lines", dashboard._palette("canonical"),
                                "common_robust", {})

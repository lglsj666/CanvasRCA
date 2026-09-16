"""CPU regressions for RQ3-only continuous visual encoding; no model calls."""
from copy import deepcopy

import pytest
from PIL import Image, ImageColor, ImageDraw
from RQs.RQ3.src.renderer import human_dashboard as render


@pytest.mark.parametrize("skin", ["default", "colorblind"])
def test_heatmap_has_no_three_sigma_dead_band(skin):
    colors = render._palette(skin)
    values = [-12., -6., -2., -1., 0., 1., 2., 6., 12.]
    pixels = [render._heatmap_color(v, -12., 12., colors) for v in values]
    assert len(set(pixels)) == len(values)
    assert pixels[0] == ImageColor.getrgb(colors["base"])
    assert pixels[-1] == ImageColor.getrgb(colors["metric"])
    assert pixels[4] == ImageColor.getrgb(colors["grid"])
    assert render._heatmap_color(20., -12., 12., colors) == pixels[-1]
    assert render._heatmap_color(-20., -12., 12., colors) == pixels[0]
    center = pixels[4]
    distance = lambda rgb: sum(abs(a - b) for a, b in zip(rgb, center, strict=True))
    assert [distance(p) for p in pixels[4:]] == sorted(distance(p) for p in pixels[4:])


def test_heatmap_pixels_bind_values_and_do_not_paint_unobserved_bins(monkeypatch):
    colors = render._palette("default")
    values = [None, -2., -1., 0., 1., 2.] + [0.] * 58
    fact = {"fact_id": "metric", "field": "metric_series_64", "payload": {
        "panel_id": "M01", "service": "123", "metric": "cpu", "values": values,
        "baseline": 0., "peak": 2., "signed_z": 2., "sircl_met_z": {},
    }}
    original = deepcopy(fact)
    monkeypatch.setattr(render, "_metric_z", lambda payload, values, geometry: values)
    image = Image.new("RGB", (1000, 500), "white")
    result = render._metric_panel(ImageDraw.Draw(image), (0, 0, 1000, 500), [fact], "heatmap", colors, "common_robust", {})
    bins = result["metric"][0]["bin_primitives"]
    assert {b["bin"] for b in bins} == set(range(1, 64))
    for item in bins:
        x0, y0, x1, y1 = item["bbox"]
        assert image.getpixel((int((x0 + x1) / 2), int((y0 + y1) / 2))) == tuple(item["color_rgb"])
        assert item["display_value"] == values[item["bin"]]
    assert fact == original


@pytest.mark.parametrize("value,low,high", [(float("nan"), -12, 12), (0, 1, 1), (0, 2, 1)])
def test_heatmap_rejects_invalid_scale(value, low, high):
    with pytest.raises(ValueError):
        render._heatmap_color(value, low, high, render._palette("default"))


@pytest.mark.parametrize("count", [1, 12, 18, 24])
def test_matrix_axes_preserve_full_ids_without_overlapping(count):
    nodes = [str(10000 + i) for i in range(count)]
    image = Image.new("RGB", (500, 500), "white")
    left, top, size, labels = render._matrix_axes(ImageDraw.Draw(image), (10, 10, 490, 490), nodes, "black")
    assert set(labels) == set(nodes)
    for index, node in enumerate(nodes):
        row, col = labels[node]["row"], labels[node]["column"]
        assert all(10 <= v <= 490 for box in (row, col) for v in box)
        assert row[2] < left and col[3] < top
        assert top + index * size <= row[1] < row[3] <= top + (index + 1) * size
        assert left + index * size <= col[0] < col[2] <= left + (index + 1) * size
        for box in (row, col):
            assert image.crop(tuple(box)).getextrema()[0][0] < 255


def test_matrix_cell_direction_and_unchanged_edge_ledger():
    facts = [{"fact_id": f"edge-{i}", "field": "directed_call_edge",
              "payload": {"caller": str(10000 + i), "callee": str(10020 + i)}} for i in range(12)]
    original = deepcopy(facts)
    image = Image.new("RGB", (1000, 1000), "white")
    result = render._topology_panel(ImageDraw.Draw(image), (0, 0, 1000, 1000), facts,
                                    "adjacency_matrix", "propagation_timeline", render._palette("default"))
    assert facts == original and set(result) == {f["fact_id"] for f in facts}
    for fact in facts:
        cell = result[fact["fact_id"]][0]
        x0, y0, x1, y1 = cell["bbox"]
        row, col = cell["caller_label_bbox"], cell["callee_label_bbox"]
        assert y0 <= (row[1] + row[3]) / 2 <= y1
        assert x0 <= (col[0] + col[2]) / 2 <= x1
        assert image.getpixel((int((x0+x1)/2), int((y0+y1)/2))) == ImageColor.getrgb(render._palette("default")["edge"])


def test_matrix_axes_fail_instead_of_overprinting_when_too_small():
    draw = ImageDraw.Draw(Image.new("RGB", (100, 100), "white"))
    with pytest.raises(ValueError, match="cannot fit"):
        render._matrix_axes(draw, (0, 0, 100, 100), [str(10000+i) for i in range(24)], "black")


def test_matrix_capacity_failure_is_distinct_from_implementation_error():
    from RQs.RQ3.src.exps import render_capacity_failure
    assert render_capacity_failure(ValueError("matrix IDs cannot fit the registered topology silhouette"))
    assert not render_capacity_failure(ValueError("matrix axes require nodes"))


@pytest.mark.parametrize('dataset,divisor', [('aiops2022',1000.),('aiops2025',1000.),
    ('aegislab',1000.),('re2_ob',1.),('re2_tt',1.)])
def test_tournament_trace_display_unit_projection(dataset,divisor):
    from RQs.RQ3.src.exps import _atomic_fact,POOL_VERSION,project_trace_ms,stable_hash
    payload={'exl_p95_base_ms':1000.,'exl_p95_fault_ms':2500.,'inl_p95_fault_ms':4000.,
             'count_base':4,'count_fault':8,'dX':1.32,'dC':1.,'rank_score':2.32}
    fact=_atomic_fact('R','trace_summary_entry',payload,entities=['123'],unit='ms')
    pool={'compiler_version':POOL_VERSION,'facts':[fact],'fact_inventory_hash':stable_hash([fact])}
    original=deepcopy(pool);projected,audit=project_trace_ms(pool,dataset)
    expected={**payload,**{k:payload[k]/divisor for k in
              ('exl_p95_base_ms','exl_p95_fault_ms','inl_p95_fault_ms')}}
    assert pool==original and projected['facts'][0]['payload']==expected
    assert audit['source_hash']==pool['fact_inventory_hash']
    assert audit['policy']==('aegis_stored_us_to_ms_v2' if dataset=='aegislab' else ('jaeger_us_to_ms_v1' if divisor==1000 else 'processor_native_ms_v1'))
    assert projected['fact_inventory_hash']==stable_hash(projected['facts'])
    with pytest.raises(ValueError,match='already projected'):project_trace_ms(projected,dataset)
    with pytest.raises(ValueError,match='unqualified'):project_trace_ms(pool,'unknown')


@pytest.mark.parametrize('value',[float('nan'),float('inf'),-1.,True])
def test_trace_projection_rejects_bad_durations(value):
    from RQs.RQ3.src.exps import POOL_VERSION,project_trace_ms,stable_hash
    fact={'field':'trace_summary_entry','payload':{'exl_p95_base_ms':value}}
    pool={'compiler_version':POOL_VERSION,'facts':[fact],'fact_inventory_hash':stable_hash([fact])}
    with pytest.raises(ValueError):project_trace_ms(pool,'re2_ob')

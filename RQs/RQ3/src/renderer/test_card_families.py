"""Synthetic CPU family contracts plus real-painter integration; no inference."""
from copy import deepcopy
from dataclasses import replace
import io

import pytest
from PIL import Image
from unified_scripts import stable_hash
from .card_families import (make_family_cards, render_family_dashboard, balanced_tree,
                            audit_family_geometry, attention_metadata)
from .designs import DashboardSpecV3


def test_long_unbroken_log_text_never_overflows():
    from PIL import ImageDraw
    from .human_dashboard import _wrap,_font
    draw=ImageDraw.Draw(Image.new("RGB",(400,100)))
    value='{"numeric_series":['+'1234567890,'*150+']}'
    font=_font(12);lines=_wrap(draw,value,font,120)
    assert ''.join(lines)==value
    assert all(draw.textlength(line,font=font)<=120 for line in lines)


def sample(log_only=False):
    rows = [{"fact_id": f"L{i}", "field": "denum_log_template", "region": "L", "entity_ids": ["123"],
             "relative_bins": [b], "payload": {"entity_id": "123", "template_id": "LT01", "template": "request failed",
                 "count": i + 1, "relative_bin": b, "level": "error"}} for i, b in enumerate((4, 41))]
    if not log_only:
        rows.append({"fact_id": "G0", "field": "directed_call_edge", "region": "G", "entity_ids": ["123", "456"],
                     "relative_bins": [], "payload": {"edge_index": 0, "caller": "123", "callee": "456"}})
    return {"opaque_incident_id": "INC-TEST", "candidates": ["123", "456"],
            "facts": rows, "fact_inventory_hash": stable_hash(rows)}


@pytest.mark.parametrize("family,count", [("modality", 2), ("per_case", 1), ("evidence", 3)])
def test_grouping_changes_structure_not_facts(family, count):
    packet = sample()
    cards = make_family_cards(packet, family)
    assert len(cards) == count
    assert sorted(fid for c in cards for fid in c.fact_ids) == sorted(f["fact_id"] for f in packet["facts"])
    if family == "per_case":
        assert cards[0].regions == ("L", "G")


def test_explicit_evidence_can_combine_regions():
    cards = make_family_cards(sample(), "evidence", groups=[["G0", "L0"], ["L1"]])
    assert cards[0].regions == ("L", "G")
    assert cards[1].regions == ("L",)


def test_measured_pixels_fit_compound_content_without_grid_footprints():
    p=sample();cards=make_family_cards(p,'per_case')
    spec=DashboardSpecV3(grid_columns=8,grid_rows=6,metric_scale_policy='per_card_raw',
        topology_space_policy='content_adaptive',pixel_capacity_policy='measured')
    png,manifest=render_family_dashboard(p,spec,cards)
    assert len(manifest['fact_mapping'])==len(p['facts'])
    assert png==render_family_dashboard(p,spec,cards)[0]
    audit_family_geometry(manifest)


def test_adaptive_topology_omits_empty_onset_space_not_facts():
    p=sample();p['facts']=[p['facts'][-1]];p['fact_inventory_hash']=stable_hash(p['facts'])
    cards=make_family_cards(p,'modality')
    spec=DashboardSpecV3(topology_space_policy='content_adaptive')
    png,manifest=render_family_dashboard(p,spec,cards)
    assert len(manifest['fact_mapping'])==1 and manifest['fact_mapping'][0]['fact_id']=='G0'
    assert png!=render_family_dashboard(p,replace(spec,topology_space_policy='fixed_split'),cards)[0]
    with pytest.raises(ValueError): replace(spec,topology_space_policy='unregistered')


@pytest.mark.parametrize("groups", [[], [["L0"]], [["L0", "L0"], ["L1", "G0"]], [["L0", "L1", "bad"]]])
def test_no_hidden_selection_or_duplication(groups):
    with pytest.raises(ValueError):
        make_family_cards(sample(), "evidence", groups=groups)


def test_time_order_is_not_input_order():
    cards = make_family_cards(sample(True), "temporal", windows=[(32, 63), (0, 31)])
    assert [c.chronological_index for c in cards] == [1, 2]
    assert [c.fact_ids for c in cards] == [("L0",), ("L1",)]
    assert cards[0].time_bins == (0, 31)


@pytest.mark.parametrize("windows", [[(0, 41), (41, 63)], [(0, 3)], [(False, 63)], [(0, 64)], [(0, 10), (11, 12), (13, 63)]])
def test_bad_or_empty_time_windows_fail(windows):
    with pytest.raises(ValueError):
        make_family_cards(sample(True), "temporal", windows=windows)


def test_untimed_evidence_is_not_relabelled_as_snapshot():
    p = sample(True)
    p['facts'][0]['payload']['log_r']={'log_rate_base':1,'log_rate_fault':2}
    p['fact_inventory_hash']=stable_hash(p['facts'])
    with pytest.raises(ValueError,match='case-wide LOG-R'):
        make_family_cards(p,'temporal',windows=[(0,63)])
    from RQs.RQ3.src.exps import project_temporal_logs
    for f in p['facts']:f['unit']='event_count'
    p['fact_inventory_hash']=stable_hash(p['facts'])
    clean,audit=project_temporal_logs(p)
    assert p['facts'][0]['payload']['log_r'] and 'log_r' not in clean['facts'][0]['payload']
    assert clean['fact_inventory_hash']!=p['fact_inventory_hash'] and len(audit['bindings'])==2
    assert len(make_family_cards(clean,'temporal',windows=[(0,63)]))==1
    with pytest.raises(ValueError, match="untimed"):
        make_family_cards(sample(), "temporal", windows=[(0, 63)])
    p = sample(True)
    p["facts"][0]["relative_bins"] = [0, 4, 41]
    p["fact_inventory_hash"] = stable_hash(p["facts"])
    with pytest.raises(ValueError, match="spans"):
        make_family_cards(p, "temporal", windows=[(0, 31), (32, 63)])


@pytest.mark.parametrize("family", ["modality", "per_case", "evidence", "temporal"])
def test_every_family_draws_real_png_with_exact_outer_bijection(family):
    p = sample(family == "temporal")
    cards = make_family_cards(p, family, windows=[(0, 31), (32, 63)] if family == "temporal" else None)
    spec = DashboardSpecV3(grid_rows=12, topology_encoding="edge_table", fact_inventory_hash=p["fact_inventory_hash"])
    png, manifest = render_family_dashboard(p, spec, cards)
    assert Image.open(io.BytesIO(png)).size == spec.canvas_size
    assert manifest["card_silhouette_bijection"] == {"status": "passed", "cards": len(cards), "silhouettes": len(cards)}
    assert len(manifest["cards"]) == len(cards)
    assert {f["fact_id"] for f in manifest["fact_mapping"]} == {f["fact_id"] for f in p["facts"]}
    assert all(f["primitive_geometry"] for f in manifest["fact_mapping"])
    audit_family_geometry(manifest)
    metadata = attention_metadata(manifest)
    assert metadata["attention_region_boxes"]["L"]
    assert png == render_family_dashboard(p, spec, cards)[0]


def test_continuous_outer_ratio_changes_actual_pixels():
    p = sample(True)
    cards = make_family_cards(p, "temporal", windows=[(0, 31), (32, 63)])
    a = balanced_tree([c.card_id for c in cards])
    b = {**a, "ratio": .65}
    png_a, ma = render_family_dashboard(p, DashboardSpecV3(), cards, a)
    png_b, mb = render_family_dashboard(p, DashboardSpecV3(), cards, b)
    assert png_a != png_b
    assert ma["visual_fact_inventory_hash"] == mb["visual_fact_inventory_hash"]
    assert ma["pixel_geometry_hash"] != mb["pixel_geometry_hash"]


def test_hash_and_time_index_tampering_fail():
    p = sample(True)
    cards = make_family_cards(p, "temporal", windows=[(0, 31), (32, 63)])
    bad = (replace(cards[0], chronological_index=2), cards[1])
    with pytest.raises(ValueError, match="metadata"):
        render_family_dashboard(p, DashboardSpecV3(), bad)
    with pytest.raises(ValueError):
        render_family_dashboard(p, DashboardSpecV3(), cards, {})
    p["facts"][0]["payload"]["count"] = 999
    with pytest.raises(ValueError, match="hashing"):
        make_family_cards(p, "temporal", windows=[(0, 31), (32, 63)])


def test_attention_uses_scaled_facets_not_compound_card():
    p = sample()
    cards = make_family_cards(p, "per_case")
    _, m = render_family_dashboard(p, DashboardSpecV3(grid_rows=12, raster_scale=1.25, topology_encoding="edge_table"), cards)
    a = attention_metadata(m)
    assert set(a["attention_region_boxes"]) == {"L", "G"}
    assert a["attention_region_boxes"]["L"][0] != m["cards"][0]["bbox"]
    bad = deepcopy(m)
    bad["fact_mapping"][0]["primitive_geometry"][0]["bbox"] = [0, 0, 99999, 99999]
    with pytest.raises(ValueError, match="primitive"):
        audit_family_geometry(bad)
def test_safe_log_rate_chart_keeps_labels_above_timeline():
    from PIL import Image,ImageDraw
    from . import human_dashboard as hd
    from .layout_audit import AuditedDraw
    charts=[]
    class Draw(AuditedDraw):
        def rounded_rectangle(self,box,**kwargs):
            self.chart=box;charts.append(box);return self.draw.rounded_rectangle(box,**kwargs)
        def text(self,xy,text,**kwargs):
            if text.startswith('baseline '):
                bounds=self.draw.textbbox(xy,text,font=kwargs['font'])
                assert bounds[3] <= self.chart[3]
            return super().text(xy,text,**kwargs)
    fact={'fact_id':'log','field':'denum_log_template','payload':{
        'entity_id':'100','template_id':'LT01','relative_bin':3,'count':4,'level':'error',
        'template':'request failed with timeout ' * 25,
        'log_r':{'error_rate_base':0,'error_rate_fault':1,'log_rate_base':2,'log_rate_fault':4}}}
    for height in (550,800,1100):
        draw=Draw(ImageDraw.Draw(Image.new('RGB',(900,height))))
        hd._log_panel(draw,(0,0,900,height),[fact],'template_frequency_timeline',hd._palette('default'),True)
    assert charts

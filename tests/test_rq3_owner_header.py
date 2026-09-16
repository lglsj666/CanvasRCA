"""SEARCH23: measured owner/name typography, no inference or private labels."""
from copy import deepcopy
from dataclasses import replace
import pytest
from PIL import Image, ImageDraw
from RQs.RQ3.src.renderer.human_dashboard import _paint_owner_header, _metric_panel, _palette
from RQs.RQ3.src.renderer.designs import DashboardSpecV3
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.utils import ROOT


@pytest.mark.parametrize('owner,role',[('123','SERVICE'),('4012','NODE'),('12223','POD')])
def test_identity_font_independent_of_suffix_length(owner,role):
    image=Image.new('RGB',(700,350),'white');draw=ImageDraw.Draw(image)
    p={'panel_id':'M1319','service':owner,'metric':'cpu'}
    short=_paint_owner_header(draw,p,(10,10,270,180),'black')
    p['metric']='node_network_receive_bytes_total.some_operation_123.456'
    long=_paint_owner_header(draw,p,(10,10,270,180),'black')
    assert short[0]==long[0]
    assert role+' '+owner in long[0]['text']
    assert ''.join(x['text'] for x in long[1:])==p['metric']
    assert all(10<=x['bbox'][0]<=x['bbox'][2]<=270 and 10<=x['bbox'][1]<=x['bbox'][3]<=180 for x in long)
    assert long[1]['bbox'][1]>long[0]['bbox'][3]


def test_fixed_owner_overflow_rejects_without_drawing():
    image=Image.new('RGB',(500,300),'white');before=image.tobytes()
    with pytest.raises(ValueError,match='owner header'):
        _paint_owner_header(ImageDraw.Draw(image),{'panel_id':'M01','service':'12345','metric':'cpu'},(0,0,10,20),'black')
    assert image.tobytes()==before
    with pytest.raises(ValueError,match='metric name'):
        _paint_owner_header(ImageDraw.Draw(image),{'panel_id':'M01','service':'12345','metric':'x'*1000},(0,0,250,100),'black')
    assert image.tobytes()==before


def test_header_preserves_every_source_point_and_packet():
    p={'panel_id':'M01','service':'4012','metric':'node_cpu_usage_rate','values':[1.]*32+[2.]*32,
       'baseline':1.,'peak':2.,'signed_z':10.,'sircl_met_z':{}}
    f={'fact_id':'mf','region':'M','field':'metric_series_64','entity_ids':['4012'],'payload':p}
    before=deepcopy(f)
    source={'series':{'M01':{'status':'source_met_z','regular_mean':1.,'regular_std_dev':.1,
                            'display_binding':{},'source_values':p['values']}}}
    def render(policy):
        image=Image.new('RGB',(1200,900),'white')
        geometry=_metric_panel(ImageDraw.Draw(image),(0,0,1200,900),[f],'small_multiple_lines',
                               _palette('canonical'),'per_card_raw',source,label_policy=policy)
        return image,geometry['mf']
    old,g0=render('typed_owner_v1');new,g1=render('owner_header_v2')
    assert f==before and old.tobytes()!=new.tobytes()
    assert [x for x in g1 if 'bin_primitives' in x]==g0
    assert old.crop((260,0,1200,900)).tobytes()==new.crop((260,0,1200,900)).tobytes()
    assert any(x['kind']=='metric_owner_label' for x in g1)
    with pytest.raises(ValueError,match='separate metric lanes'):
        _metric_panel(ImageDraw.Draw(new),(0,0,1200,900),[f],'overlay_lines',_palette('canonical'),
                      'common_robust',source,label_policy='owner_header_v2')


def test_typography_config_changes_only_registered_display_option():
    old=load_config(ROOT/'RQs/RQ3/configs/search_typed_overview_v1.yaml')
    new=load_config(ROOT/'RQs/RQ3/configs/search_owner_header_v1.yaml')
    assert old['solver']==new['solver'] and old['harness']==new['harness']
    a=deepcopy(old['search']);b=deepcopy(new['search'])
    assert a['render_overrides'].pop('metric_label_policy')=='typed_owner_v1'
    assert b['render_overrides'].pop('metric_label_policy')=='owner_header_v2'
    assert a==b
    assert DashboardSpecV3().fingerprint()!=replace(DashboardSpecV3(),metric_label_policy='owner_header_v2').fingerprint()


def test_measured_capacity_skips_small_boxes_instead_of_aborting():
    from RQs.RQ3.src.renderer import human_dashboard as hd
    from RQs.RQ3.src.renderer.designs import _make_card
    from RQs.RQ3.src.renderer.pixel_capacity import measured_envelopes
    p={'panel_id':'M1413','service':'4012','metric':'node_network_receive_bytes_total','values':[1.]*64,
       'baseline':1.,'peak':1.,'signed_z':0.,'sircl_met_z':{}}
    f={'fact_id':'mf','region':'M','field':'metric_series_64','entity_ids':['4012'],'payload':p}
    source={'series':{'M1413':{'status':'source_met_z','regular_mean':1.,'regular_std_dev':.1,
                             'display_binding':{},'source_values':p['values']}}}
    spec=DashboardSpecV3(metric_label_policy='owner_header_v2',metric_scale_policy='per_card_raw',
                        pixel_capacity_policy='measured',legibility_scale=1.25)
    token=hd._FONT_SCALE.set(spec.typography_baseline_scale*spec.legibility_scale)
    try:
        boxes=measured_envelopes(_make_card([f],'M','metric_bundle'),'small_multiple_lines',{'mf':f},spec,source)
        assert boxes and min(w for w,h in boxes)>512
    finally:hd._FONT_SCALE.reset(token)

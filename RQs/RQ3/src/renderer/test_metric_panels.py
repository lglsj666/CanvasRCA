"""SEARCH28 layout-only facets preserve selected source values and default pixels."""
from copy import deepcopy
from dataclasses import replace
import math
import pytest
from PIL import Image, ImageDraw
from .metric_panels import lane_box
from .designs import DashboardSpecV3
from .human_dashboard import _metric_panel, _palette


@pytest.mark.parametrize('count',[1,2,3,20,29,30])
def test_facets_are_ordered_bounded_nonoverlapping(count):
    box=(20,40,2420,4040)
    boxes=[lane_box(box,count,i,2) for i in range(count)]
    for i,(x0,y0,x1,y1) in enumerate(boxes):
        assert 20<=x0<x1<=2420 and 108<=y0<y1<=4009
        assert all(math.isfinite(v) for v in (x0,y0,x1,y1))
        for a,b,c,d in boxes[i+1:]:
            assert min(x1,c)<=max(x0,a) or min(y1,d)<=max(y0,b)
    assert boxes==sorted(boxes,key=lambda b:(b[0],b[1]))


@pytest.mark.parametrize('columns',[True,False,0,3,2.,'2',None])
def test_invalid_column_type_and_count(columns):
    with pytest.raises(ValueError):replace(DashboardSpecV3(),metric_panel_columns=columns)
    with pytest.raises(ValueError):lane_box((0,0,2400,4000),20,0,columns)


def test_capacity_and_encoding_fail_closed():
    for box,count,index in [((0,0,600,800),2,0),((0,0,2400,200),20,0),
                            ((0,0,float('nan'),900),2,0),((0,0,2400,900),2,2)]:
        with pytest.raises(ValueError):lane_box(box,count,index,2)
    with pytest.raises(ValueError,match='separate lanes'):
        DashboardSpecV3(metric_encoding='overlay_lines',metric_panel_columns=2)
    base=DashboardSpecV3()
    assert base.fingerprint()!=replace(base,metric_panel_columns=2).fingerprint()


@pytest.mark.parametrize('encoding',['small_multiple_lines','heatmap'])
def test_actual_facet_values_identity_and_one_column_replay(encoding):
    rows=[]
    for i in range(5):
        rows.append({'fact_id':f'f{i}','field':'metric_series_64','payload':{
            'panel_id':f'M{i:02d}','service':str(1000+i),'metric':'cpu_observed',
            'baseline':1.,'peak':3.,'signed_z':2.,'values':[None,1.,None,3.]*16}})
    original=deepcopy(rows)
    source={'series':{f['payload']['panel_id']:{'status':'source_met_z',
        'regular_mean':1.,'regular_std_dev':.1,'display_binding':{},
        'source_values':f['payload']['values']} for f in rows}}
    source_before=deepcopy(source)
    def paint(columns=None):
        image=Image.new('RGB',(2400,1800),'white')
        options={} if columns is None else {'panel_columns':columns}
        g=_metric_panel(ImageDraw.Draw(image),(0,0,2400,1800),rows,encoding,
            _palette('canonical'),'per_card_raw',source,row_order='owner_then_metric',
            label_policy='owner_header_v2',**options)
        return image.tobytes(),g
    default,a=paint();explicit,b=paint(1);facets,c=paint(2);replay,d=paint(2)
    assert default==explicit and a==b and facets!=default and facets==replay and c==d
    assert original==rows and source_before==source
    for fid in a:
        old=next(g for g in a[fid] if 'bin_primitives' in g)
        new=next(g for g in c[fid] if 'bin_primitives' in g)
        projection=lambda g:[(p['bin'],p['display_value'],p['clipped']) for p in g['bin_primitives']]
        assert projection(old)==projection(new)
        assert len(new['bin_primitives'])==32
        assert [g.get('text') for g in a[fid] if 'text' in g]==[g.get('text') for g in c[fid] if 'text' in g]
        for p in new['bin_primitives']:
            coords=p.get('point',p.get('bbox'))
            assert all(math.isfinite(v) for v in coords)


def test_search_configuration_changes_only_columns():
    from RQs.RQ3.src.main import load_config
    from RQs.RQ3.src.utils import ROOT
    a=load_config(ROOT/'RQs/RQ3/configs/search_owner_header_v1.yaml')
    b=load_config(ROOT/'RQs/RQ3/configs/search_metric_facets_v1.yaml')
    assert b['search']['render_overrides'].pop('metric_panel_columns')==2
    assert a==b


def test_actual_scale_audited_capacity_does_not_shrink_owner_column():
    from . import human_dashboard as hd
    from .layout_audit import AuditedDraw
    payload={'panel_id':'M01','service':'12345','metric':'process_cpu_time',
             'baseline':1.,'peak':3.,'signed_z':2.,'values':[1.]*32+[3.]*32}
    facts=[{'fact_id':f'f{i}','field':'metric_series_64','payload':{**payload,'panel_id':f'M{i:02d}'}} for i in range(20)]
    source={'series':{f['payload']['panel_id']:{'status':'source_met_z','regular_mean':1.,
        'regular_std_dev':.1,'display_binding':{},'source_values':f['payload']['values']} for f in facts}}
    token=hd._FONT_SCALE.set(1.18*1.25)
    try:
        img=Image.new('RGB',(1280,3900),'white');draw=AuditedDraw(ImageDraw.Draw(img))
        g=_metric_panel(draw,(0,0,1280,3900),facts,'small_multiple_lines',_palette('canonical'),
            'per_card_raw',source,label_policy='owner_header_v2',panel_columns=2)
        assert len(g)==20 and draw.label_count>100
        assert all(p['font_size_px']>=21 for rows in g.values() for p in rows if 'font_size_px' in p)
    finally:hd._FONT_SCALE.reset(token)

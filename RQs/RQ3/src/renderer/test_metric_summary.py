"""SEARCH31 suppresses one derived label, not source curves or native pixels."""
from copy import deepcopy
from dataclasses import replace
import io
import pytest
from PIL import Image, ImageDraw, ImageChops
from unified_scripts import stable_hash
from .designs import DashboardSpecV3
from .human_dashboard import _metric_panel, _palette
from .card_families import make_family_cards, render_family_dashboard


def metric_packet():
    facts = []
    for i in range(3):
        facts.append(dict(fact_id=f'M{i}', region='M', field='metric_series_64',
            entity_ids=[str(1234+i)], relative_bins=list(range(64)), unit='observed',
            payload=dict(panel_id=f'M{i:02d}', service=str(1234+i), metric='cpu_time',
                         baseline=1., peak=3., signed_z=100+i,
                         values=[None, 1., None, 3.] * 16)))
    return dict(opaque_incident_id='INC-TEST', candidates=['1234','1235','1236'],
                facts=facts, fact_inventory_hash=stable_hash(facts))


def source_geometry(packet):
    return {'series':{f['payload']['panel_id']:{'status':'source_met_z',
        'regular_mean':1.,'regular_std_dev':.1,'display_binding':{},
        'source_values':f['payload']['values']} for f in packet['facts']}}


@pytest.mark.parametrize('encoding',['small_multiple_lines','heatmap'])
def test_only_z_text_changes_and_curves_are_identical(encoding):
    packet=metric_packet(); saved=deepcopy(packet)
    def paint(policy=None):
        img=Image.new('RGB',(1200,900),'white'); draw=ImageDraw.Draw(img); texts=[]
        native=draw.text
        def record(xy,text,*args,**kwargs):
            texts.append((xy,text,kwargs.get('font').size))
            return native(xy,text,*args,**kwargs)
        draw.text=record
        options={} if policy is None else {'summary_policy':policy}
        geom=_metric_panel(draw,(0,0,1200,900),packet['facts'],encoding,
            _palette('canonical'),'per_card_raw',source_geometry(packet),label_policy='owner_header_v2',**options)
        return img,geom,texts
    a,ga,ta=paint(); b,gb,tb=paint('native'); c,gc,tc=paint('observations_only_v1')
    assert a.tobytes()==b.tobytes() and ga==gb==gc and ta==tb
    assert packet==saved
    z=[row for row in ta if row[1].startswith('z ')]
    assert len(z)==3 and tc==[row for row in ta if not row[1].startswith('z ')]
    diff=ImageChops.difference(a,c)
    assert diff.getbbox()
    mask=ImageDraw.Draw(diff)
    for (x,y),text,size in z: mask.rectangle((x,y,x+260,y+size+6),fill=(0,0,0))
    assert diff.getbbox() is None


@pytest.mark.parametrize('scale,encoding',[('common_robust','small_multiple_lines'),
    ('zero_origin_raw','heatmap'),('per_card_raw','overlay_lines')])
def test_unsupported_summary_axis_combination_fails(scale,encoding):
    with pytest.raises(ValueError,match='raw separate metric lanes'):
        _metric_panel(ImageDraw.Draw(Image.new('RGB',(1200,900))), (0,0,1200,900),
            metric_packet()['facts'],encoding,_palette('canonical'),scale,{},
            summary_policy='observations_only_v1')
    with pytest.raises(ValueError): replace(DashboardSpecV3(),metric_summary_policy='guess')


def test_manifest_retains_source_and_hashes_visible_projection():
    packet=metric_packet(); before=deepcopy(packet)
    spec=DashboardSpecV3(metric_scale_policy='per_card_raw',metric_label_policy='owner_header_v2')
    cards=make_family_cards(packet,'modality')
    source=source_geometry(packet); saved=deepcopy(source)
    png,orig=render_family_dashboard(packet,spec,cards,metric_geometry=source)
    changed,m=render_family_dashboard(packet,replace(spec,metric_summary_policy='observations_only_v1'),cards,metric_geometry=source)
    assert png!=changed and packet==before and orig['fact_mapping']==m['fact_mapping']
    expected=deepcopy(packet['facts'])
    for f in expected: del f['payload']['signed_z']
    assert m['visual_fact_inventory_hash']==stable_hash(expected)
    assert m['source_packet_fact_inventory_hash']==packet['fact_inventory_hash']
    assert m['withheld_fields']==[{'fact_id':f['fact_id'],'pointer':'/payload/signed_z'} for f in expected]
    assert Image.open(io.BytesIO(png)).size==Image.open(io.BytesIO(changed)).size
    assert png==render_family_dashboard(packet,spec,cards,metric_geometry=source)[0] and source==saved


def test_config_and_prompt_change_only_registered_summary():
    from RQs.RQ3.src.main import load_config
    from RQs.RQ3.src.utils import ROOT
    from RQs.RQ3.src.exps import search_solver_parts
    from RQs.RQ3.src.tests import fixture_packet
    a=load_config(ROOT/'RQs/RQ3/configs/search_unanchored_v1.yaml')
    b=load_config(ROOT/'RQs/RQ3/configs/search_observations_v1.yaml')
    assert b['search']['render_overrides'].pop('metric_summary_policy')=='observations_only_v1'
    assert b['search']['conditions'][0]['prompt']=='evidence_observations_v1'
    b['search']['conditions'][0]['prompt']='evidence_whole_window_v1'
    assert a==b
    packet=fixture_packet()
    parts=search_solver_parts(packet,b'png',{},prompt_policy='evidence_observations_v1')
    prior=search_solver_parts(packet,b'png',{},prompt_policy='evidence_whole_window_v1')
    assert parts[1:3]==prior[1:3] and parts[4:]==prior[4:]
    assert 'large z-score' not in parts[0]['text'] and 'large z but' not in parts[3]['text']
    assert 'z is signed standardized peak' not in parts[3]['text']

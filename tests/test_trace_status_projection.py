"""New public trace evidence, isolated from immutable pools and private data."""
from copy import deepcopy
import io

import pandas as pd
import pytest
from PIL import Image
from unified_scripts import stable_hash
from RQs.RQ3.src.exps import trace_status_rows, project_trace_status
from RQs.RQ3.src.renderer.designs import DashboardSpecV3
from RQs.RQ3.src.renderer.card_families import make_family_cards, render_family_dashboard, audit_family_geometry
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.utils import ROOT


def source():
    return pd.DataFrame({'timestamp': [0.,1.,2.,3.,4.,5.],
        'service_name': ['svc-a']*4+['svc-b']*2,
        'operation_name': ['svc-a/Read']*4+['svc-b/Write']*2,
        'status_code': ['0','13','14','13','200.0','Error'],
        'anomal': [True]*6, 'fault_type': ['PRIVATE']*6})


def packet():
    facts=[{'fact_id':'M1','region':'M','field':'context','payload':{},'entity_ids':[]},
           {'fact_id':'R0','region':'R','field':'trace_summary_entry','payload':{},'entity_ids':['123']}]
    return {'opaque_incident_id':'INC-SYNTHETIC','facts':facts,'candidates':['123','456'],
            'fact_inventory_hash':stable_hash(facts)}


def test_status_counts_and_private_column_isolation():
    frame=source(); original=frame.copy(deep=True)
    result=trace_status_rows(frame,{'svc-a':'123','svc-b':'456'},(0,5))
    assert result['source_rows']==result['eligible_rows']==6
    assert result['rows'][0]['status_counts']=={'0':1,'13':2,'14':1}
    assert result['rows'][1]['status_counts']=={'200':1,'Error':1}
    for row in result['rows']:
        assert sum(row['status_counts'].values())==row['count']
        assert all(sum(v)==row['status_counts'][k] for k,v in row['code_bin_counts'].items())
        assert 'svc-' not in row['operation']
    frame['anomal']=False; frame['fault_type']='OTHER'; frame['ground_truth']='svc-a'
    assert result==trace_status_rows(frame,{'svc-a':'123','svc-b':'456'},(0,5))
    pd.testing.assert_frame_equal(original,source())


def test_no_status_means_no_change_and_no_fabricated_zero():
    frame=source(); frame['status_code']=['0','Ok','OK','Unset','201','']
    result=trace_status_rows(frame,{'svc-a':'123','svc-b':'456'},(0,5))
    assert result['rows']==[] and result['skipped_rows']==1
    p=packet(); assert project_trace_status(p,result)[0] is p
    assert trace_status_rows(pd.DataFrame(),{},None)['source_rows']==0
    frame['timestamp']=float('nan')
    assert trace_status_rows(frame,{'svc-a':'123','svc-b':'456'},(0,5))['clock_status']=='no_public_overlap'


def test_projection_is_r_only_and_does_not_mutate():
    p=packet(); previous=deepcopy(p)
    stats=trace_status_rows(source(),{'svc-a':'123','svc-b':'456'},(0,5))
    out,audit=project_trace_status(p,stats)
    assert p==previous and audit['applied']
    assert out['facts'][0]==p['facts'][0] and out['candidates']==p['candidates']
    assert len(out['facts'])==3
    assert all('nondefault_count' not in f['payload'] and 'source_rows_hash' not in f['payload']
               for f in out['facts'])
    assert out['fact_inventory_hash']==stable_hash(out['facts'])


@pytest.mark.parametrize('mutation',['owner','schema','limit','range'])
def test_bad_sources_fail_closed(mutation):
    frame=source(); limit=6; interval=(0,5)
    if mutation=='owner':frame.loc[0,'service_name']='not-public'
    if mutation=='schema':frame=frame.drop(columns='status_code')
    if mutation=='limit':limit=7
    if mutation=='range':interval=(2,2)
    with pytest.raises(ValueError):trace_status_rows(frame,{'svc-a':'123','svc-b':'456'},interval,limit)


@pytest.mark.parametrize('legibility_scale',[.8,1.,1.25])
def test_real_painter_count_binding_geometry_and_determinism(legibility_scale):
    p,_=project_trace_status(packet(),trace_status_rows(source(),{'svc-a':'123','svc-b':'456'},(0,5)))
    p['facts']=[f for f in p['facts'] if f['region']=='R'];p['fact_inventory_hash']=stable_hash(p['facts'])
    for f in p['facts']:
        f['payload']['operation']='group/query/gyp/aggregation-'*5
    p['fact_inventory_hash']=stable_hash(p['facts'])
    spec=DashboardSpecV3(trace_axis_policy='observed_status_timeline_v1',legibility_scale=legibility_scale)
    cards=make_family_cards(p,'modality'); png,m=render_family_dashboard(p,spec,cards)
    assert png==render_family_dashboard(p,spec,cards)[0]
    audit_family_geometry(m)
    assert Image.open(io.BytesIO(png)).size==spec.canvas_size
    assert len(m['fact_mapping'])==2
    assert all(r['primitive_geometry'][0]['kind']=='observed_status_stack' for r in m['fact_mapping'])
    p['facts'][0]['payload']['count']+=1;p['fact_inventory_hash']=stable_hash(p['facts'])
    with pytest.raises(ValueError,match='conservation'):
        render_family_dashboard(p,spec,make_family_cards(p,'modality'))


def test_config_keeps_model_and_prompt_projections():
    old=load_config(ROOT/'RQs/RQ3/configs/tournament_ac1_v2.yaml')
    new=load_config(ROOT/'RQs/RQ3/configs/tournament_trace_status_v1.yaml')
    for key in ('composer','solver','unified','harness'):assert old[key]==new[key]
    for key in ('prompt','model_request_profiles','completion_policy','transport'):
        assert old['tournament'][key]==new['tournament'][key]
    assert new['tournament']['next_stage']=='complete'

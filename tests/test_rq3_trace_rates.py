"""SEARCH25 public denominator, immutable derived facts and actual PNG checks."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
import json
import math
import pandas as pd
import pytest
from RQs.RQ3.src.exps import _atomic_fact,project_trace_rates,search_solver_parts
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.utils import ROOT,stable_hash
from RQs.RQ3.src.renderer.trace_axis import source_trace_exposure,rate_lines
from RQs.RQ3.src.renderer.designs import DashboardSpecV3
from RQs.RQ3.src.renderer.card_families import make_family_cards,render_family_dashboard,audit_family_geometry


def packet(n0=90,n1=20):
    f=_atomic_fact('R','trace_summary_entry',{'entry_index':0,'service':'123','operation':'rpc',
        'count_base':n0,'count_fault':n1,'count_lfc':-2.,'exl_p95_base_ms':2.,
        'exl_p95_fault_ms':20.,'inl_p95_fault_ms':40.,'latency_lfc':3.},entities=('123',))
    return {'opaque_incident_id':'INC-TEST','candidates':['123','456','789'],'facts':[f],
            'fact_inventory_hash':stable_hash([f])}


def exposure():
    return {'status':'finite_source_trace_range','baseline_s':540.,'current_s':60.,
            'source_range_s':600.,'source_finite_rows':110}


def test_rate_projection_keeps_all_native_fields_and_changes_derived_direction():
    p=packet();before=deepcopy(p);d=exposure();old_d=deepcopy(d)
    out,a=project_trace_rates(p,d)
    assert p==before and d==old_d and out['candidates']==p['candidates']
    src=p['facts'][0];derived=out['facts'][0];r=derived['payload']['observed_span_rate']
    assert {k:v for k,v in derived['payload'].items() if k!='observed_span_rate'}==src['payload']
    assert r=={'baseline_minutes':9.,'current_minutes':1.,'baseline_per_minute':10.,'current_per_minute':20.,'ratio':2.}
    assert src['payload']['count_fault']<src['payload']['count_base'] and r['current_per_minute']>r['baseline_per_minute']
    assert src['fact_id']!=derived['fact_id'] and a['bindings']==[{'source':src['fact_id'],'derived':derived['fact_id']}]
    assert a['exposure']==d and out['fact_inventory_hash']==stable_hash(out['facts'])
    assert project_trace_rates(p,d)==(out,a)
    with pytest.raises(ValueError):project_trace_rates(out,d)
    p['facts'][0]['payload']['count_base']=100
    with pytest.raises(ValueError):project_trace_rates(p,d)


@pytest.mark.parametrize('count',[0,1,20])
def test_zero_counts_are_not_pseudocounts(count):
    p,_=project_trace_rates(packet(0,count),exposure());r=p['facts'][0]['payload']['observed_span_rate']
    assert r['baseline_per_minute']==0 and r['current_per_minute']==count and r['ratio'] is None
    assert 'no baseline events' in rate_lines(p['facts'][0]['payload'])


@pytest.mark.parametrize('bad',[0,-1,float('nan'),float('inf'),True])
def test_invalid_exposure_fails(bad):
    d=exposure();d['baseline_s']=bad
    with pytest.raises(ValueError):project_trace_rates(packet(),d)


def test_no_traces_do_not_invent_rate():
    p=packet();p['facts']=[];p['fact_inventory_hash']=stable_hash([])
    out,a=project_trace_rates(p,{'status':'no_source_trace_range'})
    assert out['facts']==[] and a['bindings']==[]
    with pytest.raises(ValueError):project_trace_rates(packet(),{'status':'no_source_trace_range'})


def test_public_duration_uses_complement_and_no_private_anchor(monkeypatch):
    from RQs.RQ3.src.renderer import panels
    view=SimpleNamespace(traces_df=pd.DataFrame({'safe':[1,2,3]}),metrics_df=pd.DataFrame({'timestamp':[100.,700.]}))
    monkeypatch.setattr(panels,'resolve_time_seconds',lambda *_:[100.,300.,700.,float('nan')])
    d=source_trace_exposure(view,(400.,600.))
    assert d=={'status':'finite_source_trace_range','baseline_s':400.,'current_s':200.,'source_range_s':600.,'source_finite_rows':3}
    assert source_trace_exposure(view,(400.,800.))['current_s']==300.
    assert source_trace_exposure(view,(800.,900.))['status']=='no_source_trace_range'
    assert source_trace_exposure(view,(0.,900.))['status']=='no_source_trace_range'
    assert source_trace_exposure(view,None)['status']=='no_source_trace_range'
    for bad in [(600,400),(100,float('nan'))]:
        with pytest.raises(ValueError):source_trace_exposure(view,bad)


def test_rate_pixels_primitive_binding_and_legacy_replay():
    p=packet();spec=DashboardSpecV3(trace_axis_policy='labeled_latency_axis_v1')
    old=render_family_dashboard(p,spec,make_family_cards(p,'modality'))
    out,_=project_trace_rates(p,exposure());new_spec=replace(spec,trace_axis_policy='labeled_rate_axis_v1')
    png,m=render_family_dashboard(out,new_spec,make_family_cards(out,'modality'))
    assert png!=old[0] and png==render_family_dashboard(out,new_spec,make_family_cards(out,'modality'))[0]
    assert old==render_family_dashboard(p,spec,make_family_cards(p,'modality'))
    assert m['fact_mapping'][0]['primitive_geometry'][0]['observed_span_rate']==out['facts'][0]['payload']['observed_span_rate']
    audit_family_geometry(m)
    with pytest.raises(ValueError):render_family_dashboard(out,spec,make_family_cards(out,'modality'))
    out['facts'][0]['payload']['observed_span_rate']['current_per_minute']=999
    with pytest.raises(ValueError):rate_lines(out['facts'][0]['payload'])


def test_rate_static_guide_keeps_prompt_candidates_and_runtime():
    p,_=project_trace_rates(packet(),exposure())
    old=search_solver_parts(p,b'cpu',{},log_summary=True,prompt_policy='evidence_bound_membership_v1')
    new=search_solver_parts(p,b'cpu',{},log_summary=True,prompt_policy='evidence_rate_v1')
    assert old[:3]==new[:3]
    assert new[3]['text']==old[3]['text']+'\n'+(ROOT/'RQs/RQ3/configs/prompts/trace_rate_guide_v1.txt').read_text()
    assert json.loads(new[1]['text'].split('\n')[-1])==p['candidates']
    assert 'observed_span_rate' not in '\n'.join(x['text'] for x in new if 'text' in x)
    a=load_config(ROOT/'RQs/RQ3/configs/search_owner_header_v1.yaml');b=load_config(ROOT/'RQs/RQ3/configs/search_trace_rates_v1.yaml')
    assert a['unified']==b['unified'] and a['solver']==b['solver'] and a['harness']==b['harness']
    assert a['search']['selectors']==b['search']['selectors'] and a['search']['conditions'][0]['request_profile']==b['search']['conditions'][0]['request_profile']
    assert not b['execution_enabled'] and b['search']['max_batch_calls']==24

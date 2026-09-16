"""SEARCH24 projections and moved unchanged numeric/trace-unit CPU tests."""
from copy import deepcopy
import json
import pytest
from RQs.RQ3.src.tests import fixture_packet
from RQs.RQ3.src.exps import _atomic_fact, project_whole_window, search_solver_parts
from RQs.RQ3.src.utils import stable_hash, ROOT


def test_numeric_units_do_not_fragment_templates():
    from RQs.RQ3.src.exps import log_template
    a,va=log_template("Request finished in 1.2876ms status=504")
    b,vb=log_template("Request finished in 2.9999ms status=200")
    assert a==b
    assert "1.2876" in va.values() and "2.9999" in vb.values()
    assert va!=vb


def test_trace_unit_projection_is_local_bound_and_once():
    from RQs.RQ3.src.exps import project_trace_ms, POOL_VERSION
    p=fixture_packet();p['compiler_version']=POOL_VERSION
    p['facts'].append(_atomic_fact('R','trace_summary_entry',{'service':'123','operation':'rpc',
        'exl_p95_base_ms':1000.,'exl_p95_fault_ms':2500.,'inl_p95_fault_ms':3500.,'latency_lfc':1.32},entities=('123',)))
    p['fact_inventory_hash']=stable_hash(p['facts']);old=deepcopy(p)
    out,audit=project_trace_ms(p,'aiops2025');assert p==old and out['candidates']==p['candidates']
    assert out['facts'][:-1]==p['facts'][:-1] and out['facts'][-1]['payload']['exl_p95_fault_ms']==2.5
    assert out['facts'][-1]['payload']['latency_lfc']==1.32 and audit['bindings'][0]['source']!=audit['bindings'][0]['derived']
    assert project_trace_ms(p,'aiops2022')[0]==out
    with pytest.raises(ValueError):project_trace_ms(out,'aiops2025')
    with pytest.raises(ValueError):project_trace_ms(p,'re2_ob')
    p['facts'][-1]['payload']['exl_p95_fault_ms']=float('nan');p['fact_inventory_hash']=stable_hash(p['facts'])
    with pytest.raises(ValueError):project_trace_ms(p,'aiops2025')


def test_whole_window_projection_retains_exact_public_evidence():
    p=fixture_packet()
    p['facts'] += [_atomic_fact('M','estimated_fault_window',{'start':'+20m','end':'+25m'}),
                   _atomic_fact('M','observation_window',{'duration_rel_s':3600}),
                   _atomic_fact('G','propagation_service',{'rank':1,'onset':'+20m'},entities=('123',))]
    p['fact_inventory_hash']=stable_hash(p['facts']);before=deepcopy(p)
    out,audit=project_whole_window(p)
    assert p==before and out['candidates']==p['candidates']
    assert out['facts']==[f for f in p['facts'] if f['field'] not in ('estimated_fault_window','propagation_service')]
    assert out['fact_inventory_hash']==stable_hash(out['facts'])==audit['retained_fact_hash']
    assert len(audit['removed_heuristic_fact_ids'])==2
    assert project_whole_window(p)==(out,audit)
    with pytest.raises(ValueError):project_whole_window(out)
    p['facts'][0]['payload']['rank']=1000
    with pytest.raises(ValueError):project_whole_window(p)


def test_whole_window_prompt_has_candidates_not_incident_text():
    p=fixture_packet();png=b'cpu-only'
    parts=search_solver_parts(p,png,{},log_summary=True,prompt_policy='evidence_whole_window_v1')
    assert len(parts)==4 and sum('png' in x for x in parts)==1
    assert json.loads(parts[1]['text'].split('\n')[-1])==p['candidates']
    root=ROOT/'RQs/RQ3/configs/prompts'
    assert parts[0]['text']==(root/'whole_window_task_v1.txt').read_text()
    assert parts[3]['text']==(root/'whole_window_guide_v1.txt').read_text()+'\n'+(root/'membership_guide_v1.txt').read_text()
    assert 'Events far from' not in parts[0]['text'] and 'entire observation' in parts[0]['text']
    assert 'estimated_fault_window' not in '\n'.join(x['text'] for x in parts if 'text' in x)


def test_unanchored_source_bins_do_not_paint_a_band():
    from RQs.RQ3.src.renderer.human_dashboard import _fault_bins
    p=fixture_packet()
    p['facts'] += [_atomic_fact('M','estimated_fault_window',{'start':'+20m','end':'+25m'}),
                   _atomic_fact('M','observation_window',{'duration_rel_s':3600})]
    p['fact_inventory_hash']=stable_hash(p['facts'])
    assert _fault_bins(p['facts'])==(21.,26.25)
    out,_=project_whole_window(p)
    assert _fault_bins(out['facts']) is None


def test_temporal_configs_keep_runtime_and_data_contract():
    from RQs.RQ3.src.main import load_config
    old=load_config(ROOT/'RQs/RQ3/configs/search_owner_header_v1.yaml')
    for name in ('whole_window','unanchored'):
        cfg=load_config(ROOT/f'RQs/RQ3/configs/search_{name}_v1.yaml')
        assert cfg['unified']==old['unified'] and cfg['solver']==old['solver']
        assert cfg['harness']==old['harness'] and not cfg['execution_enabled']
        assert cfg['search']['render_overrides']==old['search']['render_overrides']
        assert cfg['search']['max_batch_calls']==24 and cfg['search']['concurrency']==4
        assert cfg['search']['conditions'][0]['request_profile']==old['search']['conditions'][0]['request_profile']

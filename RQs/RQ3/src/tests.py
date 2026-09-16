"""CPU-only regression tests for RQ3. No model requests in this module."""
from __future__ import annotations

from dataclasses import asdict
from copy import deepcopy

import pytest
from unified_scripts import stable_hash
from .main import load_config
from .utils import (
    CallLedger, RQ3SegmentationAdapter, allocate_groups, attribution,
    components, cost_reward, holm, paired_statistics, rloo_advantages,
)
from .exps import (
    ComposerProgramV1, DesignInterventionV1, _atomic_fact,
    default_design, evidence_cards, fixed_designs, observation, parse_program,
    portable_intervention, render_program, select_packet,
    build_catalog, composer_messages,
)
from .gates import (parent_integrity, audit_split, audit_render, validate_rollout_probability,
                    audit_catalog, audit_catalog_inventory)


class ByteTokenizer:
    """Deterministic conservative test tokenizer; real qualification uses Qwen."""
    def encode(self, text, **kwargs):
        return list(text.encode())

    def decode(self, tokens, **kwargs):
        return bytes(tokens).decode(errors="ignore")

    def apply_chat_template(self, messages, **kwargs):
        from unified_scripts import canonical_json
        return {"input_ids": self.encode(canonical_json(messages) + "<assistant>")}


def selector_suite_fixture():
    p=fixture_packet(); p['facts']=[]; p['pool_coverage']={'public_membership':True}
    p['facts'].extend([
        _atomic_fact('M','observation_window',{'duration_rel_s':640.,'source_metric_rows':64},unit='relative_seconds'),
        _atomic_fact('M','estimated_fault_window',{'start':'+5.3m','end':'+7.5m'},unit='displayed_relative_minutes'),
    ])
    for i in range(40):
        owner=str(100+i%10); a=10.; b=10.+(40-i)/10; sd=1.; after=1.
        if i==35: after=100.
        values=[10.+(j%2)*.1 for j in range(64)]
        if i==36: values=[10.]*32+[40.]*32
        p['facts'].append(_atomic_fact('M','metric_series_64',{'panel_id':f'M{i+1:02}',
            'rank':i+1,'service':owner,'metric':'latency' if i%2 else 'cpu_usage',
            'values':values,'baseline':a,'peak':max(values),'signed_z':b-a,'missing_mask':[False]*64,
            'sircl_met_z':{'regular_mean':a,'current_mean':b,'regular_std_dev':sd,
                          'current_std_dev':after,'deviation_sigma':b-a}},entities=[owner],bins=range(64),unit='source_unit'))
    for i in range(8):
        p['facts'].append(_atomic_fact('R','trace_summary_entry',{'service':str(100+i),'operation':f'OP{i}',
            'entry_index':i,'rank_score':100-i,'count_base':200,'count_fault':200,
            'exl_p95_base_ms':10.,'exl_p95_fault_ms':90. if i==7 else 11.,
            'inl_p95_fault_ms':100.,'latency_lfc':1.,'count_lfc':0.},entities=[str(100+i)]))
    for i in range(5):
        for bin_ in range(4):
            count=(40 if bin_==3 else 1) if i==4 else 50
            p['facts'].append(_atomic_fact('L','denum_log_template',{'entity_id':'107','template_id':f'LT{i}',
                'template':f'normal template {i}','relative_bin':bin_,'level':'info','count':count,
                'log_r':{'score':10-i}},entities=['107'],bins=[bin_]))
    for i in range(9):
        p['facts'].append(_atomic_fact('G','directed_call_edge',{'caller':str(100+i),'callee':str(101+i),'edge_index':i},
            entities=[str(100+i),str(101+i)]))
    for i in range(10):
        p['facts'].append(_atomic_fact('G','propagation_service',{'service':str(100+i),'rank':i+1,
            'onset_rel_min_display':f'+{5+i/10:.1f}m'},entities=[str(100+i)]))
    p['candidates']=[str(100+i) for i in range(10)];p['fact_inventory_hash']=stable_hash(p['facts'])
    return p


@pytest.mark.parametrize('policy',('diagnostic_cover_v2','variance_shift_v2','window_change_v2','trace_self_time_v2','log_surprise_v2','propagation_frontier_v2','heterogeneous_consensus_v1','temporal_episode_cover_v1','counter_rate_change_v1','incident_window_pattern_v1','source_first_bundle_v1','spectral_saliency_v1','near_anchor_impulse_v1','sustained_tail_v1','rank_band_rescue_v1','candidate_round_robin_v1','metric_family_portfolio_v1','topology_separator_v1','lagged_source_v1','peer_residual_v1'))
def test_selection_only_deterministic_fact_preserving_budget(policy):
    from collections import Counter
    from .exps import search_select, selection_only_context, select_diagnostic_evidence
    p=selector_suite_fixture(); before=deepcopy(p); anchor,_=search_select(p,'balanced_additive_v1')
    result,audit=search_select(p,policy)
    reverse=deepcopy(p); reverse['facts'].reverse(); reverse['fact_inventory_hash']=stable_hash(reverse['facts'])
    assert result['facts']==search_select(reverse,policy)[0]['facts']
    assert p==before and result['candidates']==p['candidates']
    assert all(f in p['facts'] for f in result['facts'])
    assert len({f['fact_id'] for f in result['facts']})==len(result['facts'])
    count=Counter(f['field'] for f in result['facts'])
    assert all(count[k]==n for k,n in audit['budgets'].items())
    assert audit['budgets']=={k:sum(f['field']==k for f in anchor['facts']) for k in audit['budgets']}
    ctx=selection_only_context(p); ctx['source_hash']='changed'
    with pytest.raises(ValueError,match='context mismatch'):select_diagnostic_evidence(p,policy,ctx)
    with pytest.raises(ValueError,match='budget anchor'):search_select(p,policy,24)


def test_selection_only_mechanisms_reach_distinct_signals():
    from .exps import search_select
    p=selector_suite_fixture(); packets={k:search_select(p,k)[0] for k in
        ('balanced_additive_v1','diagnostic_cover_v2','variance_shift_v2','window_change_v2','trace_self_time_v2','log_surprise_v2')}
    def has(policy,field,key,value):return any(f['field']==field and f['payload'][key]==value for f in packets[policy]['facts'])
    assert has('variance_shift_v2','metric_series_64','panel_id','M36')
    assert has('window_change_v2','metric_series_64','panel_id','M37')
    assert has('trace_self_time_v2','trace_summary_entry','operation','OP7')
    assert has('log_surprise_v2','denum_log_template','template_id','LT4')
    assert not has('balanced_additive_v1','trace_summary_entry','operation','OP7')
    assert len({stable_hash(sorted(f['fact_id'] for f in p['facts'])) for p in packets.values()})==len(packets)


def test_successor_selection_mechanisms_are_real_and_distinct():
    from .exps import search_select
    p=selector_suite_fixture()
    # A rate burst without the largest level shift exercises the counter path.
    metric=next(f for f in p['facts'] if f['field']=='metric_series_64' and f['payload']['panel_id']=='M31')
    payload=deepcopy(metric['payload']);payload.update(metric='request_count_total',values=list(range(32))+[31+20*(i+1) for i in range(32)])
    replacement=_atomic_fact('M','metric_series_64',payload,entities=metric['entity_ids'],bins=range(64),unit=metric['unit'])
    p['facts']=[replacement if f is metric else f for f in p['facts']];p['fact_inventory_hash']=stable_hash(p['facts'])
    policies=('heterogeneous_consensus_v1','temporal_episode_cover_v1','counter_rate_change_v1')
    packets={policy:search_select(p,policy)[0] for policy in policies}
    signatures={policy:stable_hash(sorted(f['fact_id'] for f in packet['facts'])) for policy,packet in packets.items()}
    assert len(set(signatures.values()))==len(policies)
    assert any(f['fact_id']==replacement['fact_id'] for f in packets['counter_rate_change_v1']['facts'])


def test_window_source_and_spectral_successors_are_distinct_and_public_only():
    from .exps import search_select
    p=selector_suite_fixture()
    # A short oscillatory incident differs from the step already exercised by
    # window_change_v2 and from the cumulative counter fixture above.
    metric=next(f for f in p['facts'] if f['field']=='metric_series_64' and f['payload']['panel_id']=='M30')
    payload=deepcopy(metric['payload']);payload['values']=[10.]*31+[10.,300.,-200.,320.,-190.,290.,-180.,10.]+[10.]*25
    replacement=_atomic_fact('M','metric_series_64',payload,entities=metric['entity_ids'],bins=range(64),unit=metric['unit'])
    p['facts']=[replacement if f is metric else f for f in p['facts']];p['fact_inventory_hash']=stable_hash(p['facts'])
    policies=('incident_window_pattern_v1','source_first_bundle_v1','spectral_saliency_v1')
    packets={policy:search_select(p,policy)[0] for policy in policies}
    signatures={policy:stable_hash(sorted(f['fact_id'] for f in packet['facts'])) for policy,packet in packets.items()}
    assert len(set(signatures.values()))>=2
    assert any(f['fact_id']==replacement['fact_id'] for f in packets['spectral_saliency_v1']['facts'])
    assert all(packet['candidates']==p['candidates'] for packet in packets.values())


def test_log_surprise_excludes_unreadable_expanded_templates_without_truncation():
    from .exps import search_select
    p=selector_suite_fixture()
    target=next(f for f in p['facts'] if f['field']=='denum_log_template' and f['payload']['template_id']=='LT4')
    target['payload']['template']='expanded-ticket-list-'+'{opaque} '*400
    # Fact identity is content-derived in production; rebuild this synthetic
    # fixture through the same constructor rather than accepting a stale hash.
    replacement=_atomic_fact('L','denum_log_template',target['payload'],entities=['107'],
                             bins=[target['payload']['relative_bin']])
    p['facts']=[replacement if f is target else f for f in p['facts']]
    p['fact_inventory_hash']=stable_hash(p['facts'])
    result,audit=search_select(p,'log_surprise_v2')
    logs=[f for f in result['facts'] if f['field']=='denum_log_template']
    assert len(logs)==audit['budgets']['denum_log_template']
    assert all(len(f['payload']['template'])<=1024 for f in logs)
    assert all(f['payload']['template']!='expanded-ticket-list-'+'{opaque} '*400 for f in logs)


def test_selection_window_native_cost_equivalence_and_gaps():
    import numpy as np
    from .exps import selection_window_score
    from packages.rq3_selection_native.adapted.costl2 import CostL2
    from .utils import ROOT,sha_file
    root=ROOT/'packages/rq3_selection_native'
    assert sha_file(root/'original/costl2.py')=='eddf850c9aee63382296f0fa27e523b77bdaba2215a395ec7aa06941729ca8b8'
    assert (root/'adapted/costl2.py').read_text()==(root/'original/costl2.py').read_text().replace('from ruptures.costs import','from .exceptions import').replace('from ruptures.base import','from .base import')
    rng=np.random.default_rng(42)
    for gaps in (False,True):
        y=np.r_[rng.normal(size=32),rng.normal(4,1,size=32)]
        values=[None if gaps and i%3==1 else float(v) for i,v in enumerate(y)]
        observed=np.array([v for v in values if v is not None]);denom=CostL2().fit(observed).error(0,len(observed))
        best=0.
        for width in (4,8,16):
            for cut in range(width,65-width):
                a=np.array([v for v in values[cut-width:cut] if v is not None]);b=np.array([v for v in values[cut:cut+width] if v is not None])
                if min(len(a),len(b))<2:continue
                cost=CostL2().fit(np.r_[a,b]);gain=cost.error(0,len(a)+len(b))-cost.error(0,len(a))-cost.error(len(a),len(a)+len(b))
                best=max(best,gain/denom)
        assert selection_window_score(values)['score']==pytest.approx(best,rel=1e-10)
    for values in ([None]*64,[1.]*64,[True]*64,[float('nan')]*64):assert not selection_window_score(values)['eligible']


def test_selection_only_no_nan_no_private_access_and_config_guard():
    from .exps import SELECTION_ONLY_POLICIES,search_select,selection_number
    from .main import validate_selection_only_config
    from .utils import ROOT
    for value in ('na','nan','inf',True,None): assert selection_number(value) is None
    assert selection_number('-1.5k')==-1500
    p=selector_suite_fixture()
    for f in p['facts']:
        if f['field']=='metric_series_64':f['payload']['sircl_met_z']={}
    p['fact_inventory_hash']=stable_hash(p['facts'])
    for policy in SELECTION_ONLY_POLICIES:
        result,_=search_select(p,policy);assert all(f in p['facts'] for f in result['facts'])
    cfg=load_config(ROOT/'RQs/RQ3/configs/tournament_selection_only_v4.yaml')
    for path,value in [('grouping_policy','different'),('diagnostic_transport','metric_text_with_rlg_visual_v1'),('metric_limit',24)]:
        wrong=deepcopy(cfg);wrong['search'][path]=value
        with pytest.raises(ValueError,match='non-selection'):validate_selection_only_config(wrong)


def test_selection_preview_resolves_relative_paths_without_model_calls(monkeypatch,tmp_path):
    from pathlib import Path
    from types import SimpleNamespace
    from . import main,utils
    rows=[{'dataset':d,'opaque_incident_id':str(i)} for i,d in enumerate(('aegislab','aiops2022','aiops2025'))]
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main,'validate_selection_only_config',lambda c:{'method_configs':{'test':'config'}})
    monkeypatch.setattr(utils,'tournament_register',lambda c:SimpleNamespace(state=lambda:{'models':{'m':{'eligible':['0','1','2']}}}))
    monkeypatch.setattr(main,'RQ3SegmentationAdapter',lambda c:SimpleNamespace(build=lambda:{}))
    monkeypatch.setattr(utils,'partition_rows',lambda *a:rows)
    monkeypatch.setattr(main,'read_json',lambda p:{'cases':rows})
    monkeypatch.setattr(main,'load_config',lambda p:{})
    jobs=[]
    def capture(fn,items):
        jobs.extend(items)
        return [[] for _ in items]
    monkeypatch.setattr(main,'pinned_process_map',capture)
    result=main.preview_selection_suite({},Path('source'),Path('output'))
    assert len(jobs)==3 and result['model_calls']==0
    assert all(j[1]==tmp_path/'source' and j[2]==tmp_path/'output' for j in jobs)
    assert (tmp_path/'output/summary.json').exists()


@pytest.fixture(autouse=True)
def synthetic_plot_geometry(monkeypatch):
    from . import exps
    original=exps.source_metric_geometry
    fixture={'schema':'CPUFixtureMetricGeometry','series':{f'M{i:02d}':{
        'status':'baseline_unavailable','regular_mean':None,'regular_std_dev':None,
        'source_values':[float(j%8+i-1) for j in range(64)],
        'display_binding':{'regular_mean':None,'regular_std_dev':None}} for i in range(1,5)}}
    monkeypatch.setattr(exps,'source_metric_geometry',lambda opaque:fixture if opaque=='INC-TEST' else original(opaque))




def fixture_packet():
    facts=[]
    for i in range(4):
        entity=str(100+i)
        facts.append(_atomic_fact("M","metric_series_64",{
            "panel_id":f"M{i+1:02d}","rank":i+1,"service":entity,"metric":"cpu_usage",
            "values":[float(j%8+i) for j in range(64)],"missing_mask":[False]*64,
            "baseline":1.,"peak":10.,"signed_z":5.,"sircl_met_z":{},
        },entities=(entity,),bins=range(64),unit="fraction"))
    facts.append(_atomic_fact("G","directed_call_edge",{"caller":"100","callee":"101","edge_index":0},entities=("100","101")))
    return {"opaque_incident_id":"INC-TEST","candidates":[str(100+i) for i in range(4)],
            "facts":facts,"fact_inventory_hash":stable_hash(facts)}


def test_parent_config_unchanged():
    parent_integrity()


def test_tournament_fixed_prompt_forbids_incident_text():
    from .exps import search_solver_parts,validate_tournament_parts
    packet=fixture_packet();cfg=load_config();cards=evidence_cards(packet,cfg)
    p,png,manifest=render_program(packet,cards,ComposerProgramV1(tuple(c.card_id for c in cards),default_design()))
    parts=search_solver_parts(p,png,manifest,prompt_policy='tournament_frozen_v1')
    system,ids=validate_tournament_parts(parts)
    assert ids==p['candidates'] and 'Kubernetes' in system
    for i in (0,1,3,4):
        changed=deepcopy(parts);changed[i]['text']+=' Diagnostic hint.'
        with pytest.raises(ValueError):validate_tournament_parts(changed)


def test_tournament_hybrid_metric_transport_is_disjoint_and_fixed():
    from .exps import (search_solver_parts, validate_tournament_parts,
                       tournament_metric_text_v1, tournament_visual_packet)
    packet=fixture_packet()
    packet['facts'][0]['payload']['values'][2]=None
    packet['facts'][0]['payload']['missing_mask'][2]=True
    packet['fact_inventory_hash']=stable_hash(packet['facts'])
    visual=tournament_visual_packet(packet,'M')
    parts=search_solver_parts(packet,b'png',{},prompt_policy='tournament_hybrid_metric_v1')
    system,ids=validate_tournament_parts(parts)
    assert ids==packet['candidates'] and 'Kubernetes' in system
    assert [p['type'] for p in parts]==['text','text','image','text','text','text']
    assert parts[3]['text']==tournament_metric_text_v1(packet)
    first_observed=parts[3]['text'].split('[M02]',1)[0]
    assert 'b2=' not in first_observed and 'missing' not in parts[3]['text'].lower() and 'null' not in parts[3]['text'].lower()
    text_ids={f['fact_id'] for f in packet['facts'] if f['region']=='M'}
    visual_ids={f['fact_id'] for f in visual['facts'] if f['region']!='C'}
    assert text_ids and visual_ids and text_ids.isdisjoint(visual_ids)
    assert text_ids|visual_ids=={f['fact_id'] for f in packet['facts'] if f['region']!='C'}
    for index in (0,1,4,5):
        changed=deepcopy(parts);changed[index]['text']+=' changed'
        with pytest.raises(ValueError):validate_tournament_parts(changed)
    changed=deepcopy(parts);changed[3]['text']+='\nTrace evidence; forbidden'
    with pytest.raises(ValueError,match='registered text modality'):validate_tournament_parts(changed)


def test_tournament_hybrid_trace_transport_is_disjoint_and_fixed():
    from .exps import (search_solver_parts, validate_tournament_parts,
                       tournament_trace_text_v1, tournament_visual_packet, _atomic_fact)
    packet=fixture_packet(); packet['facts'].append(_atomic_fact('R','trace_summary_entry',{
        'entry_index':0,'service':'100','operation':'GET /api/items/123','count_base':10,'count_fault':4,
        'count_lfc':-1.32,'exl_p95_base_ms':2.5,'exl_p95_fault_ms':25.,
        'inl_p95_fault_ms':31.,'latency_lfc':3.32,'rank_score':3.32},entities=('100',),
        unit='counts_milliseconds_and_log2_fold_change'))
    packet['fact_inventory_hash']=stable_hash(packet['facts'])
    visual=tournament_visual_packet(packet,'R')
    parts=search_solver_parts(packet,b'png',{},prompt_policy='tournament_hybrid_trace_v1')
    system,ids=validate_tournament_parts(parts)
    assert ids==packet['candidates'] and 'Kubernetes' in system
    assert parts[3]['text']==tournament_trace_text_v1(packet)
    assert 'inclusive_p95_current_ms=31.0' in parts[3]['text']
    text_ids={f['fact_id'] for f in packet['facts'] if f['region']=='R'}
    visual_ids={f['fact_id'] for f in visual['facts'] if f['region']!='C'}
    assert text_ids and visual_ids and text_ids.isdisjoint(visual_ids)
    assert text_ids|visual_ids=={f['fact_id'] for f in packet['facts'] if f['region']!='C'}
    no_trace=fixture_packet(); visual=tournament_visual_packet(no_trace,'R',require_text=False)
    parts=search_solver_parts(no_trace,b'png',{},prompt_policy='tournament_hybrid_trace_v1')
    assert parts[3]['text'].endswith('selected_trace_rows=0\n')
    assert validate_tournament_parts(parts)[1]==no_trace['candidates']
    assert {f['fact_id'] for f in visual['facts'] if f['region']!='C'}=={
        f['fact_id'] for f in no_trace['facts'] if f['region']!='C'}


def test_tournament_hybrid_log_transport_is_disjoint_and_fixed():
    from .exps import (search_solver_parts, validate_tournament_parts,
                       tournament_log_text_v1, tournament_visual_packet, _atomic_fact)
    packet=fixture_packet();packet['facts'].append(_atomic_fact('L','denum_log_template',{
        'entity_id':'100','template_id':'LT03','relative_bin':7,'count':4,'level':'error',
        'template':'request timed out after {num1} ms | observed variable summaries: num1: n=4 values=1200×4',
        'numeric_preview':{},'omitted_numeric_variables':0,
        'log_r':{'log_rate_base':1.0,'log_rate_fault':4.0,'error_count_base':0,
                 'error_count_fault':4,'error_rate_base':0.0,'error_rate_fault':4.0,
                 'score':104.0,'components':['new_errors:+100']}},entities=('100',),bins=(7,),
        unit='event_count_and_numeric_summary'))
    packet['fact_inventory_hash']=stable_hash(packet['facts'])
    visual=tournament_visual_packet(packet,'L')
    parts=search_solver_parts(packet,b'png',{},prompt_policy='tournament_hybrid_log_v1')
    system,ids=validate_tournament_parts(parts)
    assert ids==packet['candidates'] and 'Kubernetes' in system
    assert parts[3]['text']==tournament_log_text_v1(packet)
    assert '[LT03] SERVICE 100' in parts[3]['text'] and 'error_rate_fault=4.0' in parts[3]['text']
    text_ids={f['fact_id'] for f in packet['facts'] if f['region']=='L'}
    visual_ids={f['fact_id'] for f in visual['facts'] if f['region']!='C'}
    assert text_ids and visual_ids and text_ids.isdisjoint(visual_ids)
    assert text_ids|visual_ids=={f['fact_id'] for f in packet['facts'] if f['region']!='C'}
    no_log=fixture_packet();visual=tournament_visual_packet(no_log,'L',require_text=False)
    parts=search_solver_parts(no_log,b'png',{},prompt_policy='tournament_hybrid_log_v1')
    assert parts[3]['text'].endswith('selected_log_rows=0\n')
    assert validate_tournament_parts(parts)[1]==no_log['candidates']
    assert {f['fact_id'] for f in visual['facts'] if f['region']!='C'}=={
        f['fact_id'] for f in no_log['facts'] if f['region']!='C'}


def test_tournament_hybrid_topology_transport_is_disjoint_and_fixed():
    from .exps import (search_solver_parts, validate_tournament_parts,
                       tournament_topology_text_v1, tournament_visual_packet, _atomic_fact)
    packet=fixture_packet();packet['facts'].append(_atomic_fact('G','propagation_service',{
        'rank':2,'service':'102','onset_rel_min_display':'3.5','severity_z_display':'7.2',
        'evidence_source_display':'M'},entities=('102',),unit='relative_minutes_and_z'))
    packet['fact_inventory_hash']=stable_hash(packet['facts'])
    visual=tournament_visual_packet(packet,'G',require_text=False)
    parts=search_solver_parts(packet,b'png',{},prompt_policy='tournament_hybrid_topology_v1')
    system,ids=validate_tournament_parts(parts)
    assert ids==packet['candidates'] and 'Kubernetes' in system
    assert parts[3]['text']==tournament_topology_text_v1(packet)
    assert 'caller=100 -> callee=101' in parts[3]['text']
    assert '[G-O002] SERVICE 102' in parts[3]['text'] and 'estimated_onset_rel_min=3.5' in parts[3]['text']
    text_ids={f['fact_id'] for f in packet['facts'] if f['region']=='G'}
    visual_ids={f['fact_id'] for f in visual['facts'] if f['region']!='C'}
    assert text_ids and visual_ids and text_ids.isdisjoint(visual_ids)
    assert text_ids|visual_ids=={f['fact_id'] for f in packet['facts'] if f['region']!='C'}
    for index in (0,1,4,5):
        changed=deepcopy(parts);changed[index]['text']+=' changed'
        with pytest.raises(ValueError):validate_tournament_parts(changed)


def test_hybrid_tournament_keeps_original_coverage_identity():
    from .utils import ROOT, read_json, stable_hash as rq_hash, tournament_register
    config=load_config(ROOT/'RQs/RQ3/configs/tournament_full_metric_text_rlg_v3.yaml')
    before=read_json(ROOT/'RQs/RQ3/results/tournament_v1/coverage/contract.json')
    register=tournament_register(config)
    after=read_json(register.root/'contract.json')
    assert before==after and rq_hash(before)==rq_hash(after)
    assert config['tournament']['transport']['max_text_evidence_modalities']==1
    assert config['tournament']['coverage_transport']['max_text_evidence_modalities']==0


@pytest.mark.parametrize('tag',['qwen3.8-27b','gemma-4-26b-a4b'])
def test_tournament_model_specific_recipes_with_same_parts(monkeypatch,tmp_path,tag):
    from types import SimpleNamespace
    from .main import request
    from .utils import ROOT,read_json
    from .exps import search_solver_parts
    from vlmrca.vlm import client
    cfg=load_config(ROOT/'RQs/RQ3/configs/tournament_v1.yaml')
    cfg['solver'].update(model_tag=tag,request_profile=cfg['tournament']['model_request_profiles'][tag])
    monkeypatch.setenv('CANVASRCA_ATTENTION_PROBE','0');monkeypatch.setenv('CANVASRCA_VLLM_CONFIG',str(ROOT/cfg['unified']['inference']))
    monkeypatch.setattr(client,'count_vllm_prompt_tokens',lambda *a,**kw:3 if kw.get('text_only') else 4)
    monkeypatch.setattr(client,'call_vlm',lambda *a,**kw:SimpleNamespace(text='{}',raw={'finish_reason':'stop'},input_tokens=4,output_tokens=1,latency_s=.1,performance={}))
    parts=search_solver_parts(fixture_packet(),b'png',{},prompt_policy='tournament_frozen_v1')
    request(cfg,CallLedger(tmp_path/'calls.sqlite',None),'unit',parts,'solver',tmp_path)
    envelope=read_json(tmp_path/'prompts/unit.json')
    assert ('Gemma' in envelope['model']['model_id'] or 'gemma' in envelope['model']['model_id'])==(tag=='gemma-4-26b-a4b')
    assert envelope['model']['max_tokens']==8192 and envelope['model']['thinking'] is False
    assert ('request_adapter' in envelope)==(tag=='qwen3.8-27b')


@pytest.mark.parametrize('experiment,spent,remaining', [('exp_composer_learning',13,2),('exp_frozen_solver_generalization',11,2),('exp_selection_design_attribution',17,1)])
def test_forward_renderer_smoke_preserves_cumulative_budget(experiment,spent,remaining):
    from .main import smoke_execution_shape
    from .gates import assert_formal_authorized
    assert smoke_execution_shape(experiment,True)==(('solver',),remaining) and spent+remaining<=18
    assert 'composer' in smoke_execution_shape(experiment)[0]
    with pytest.raises(PermissionError):assert_formal_authorized({**load_config(),'execution_enabled':True,'qualification_renderer_repair':True})


def test_local_design_controls_do_not_change_selection_or_budget():
    from .main import local_design_intervention
    fixed=ComposerProgramV1(('M001',),default_design());d={**default_design(),'raster_scale':1.5,'layout_family':'entity_grouped'}
    learned=ComposerProgramV1(('G001','M002'),d);task={'dataset':'aiops2022','case_id':'a'}
    tasks={'a':{'stage':'eval','dataset':'aiops2022','case_id':'a'},'b':{'stage':'eval','dataset':'aiops2022','case_id':'b'}}
    for policy in ('encoding','layout','resolution','hash_random','wrong_case_design'):
        def source(*args,**kwargs):return {'status':'valid','program':asdict(fixed)}
        result=local_design_intervention(policy,learned,fixed,task,tasks,source)
        assert result.selection==learned.selection
        if policy=='hash_random':assert result.design['grid_rows']==d['grid_rows'] and result.design['raster_scale']==1.5
        if policy=='resolution':assert result.design=={**d,'raster_scale':fixed.design['raster_scale']}
    assert local_design_intervention('wrong_case_design',learned,fixed,task,tasks,lambda *a,**k:{'status':'program_failure'}) is None


def test_eval_twins_interventions_use_actual_proposal_not_default(tmp_path,monkeypatch):
    from . import main
    from .utils import write_json,sha_file,read_json
    from pathlib import Path
    monkeypatch.setattr(main,'ROOT',tmp_path)
    cfg=load_config();out=tmp_path/'RQs/RQ3/results/formal';packet=fixture_packet();cards=evidence_cards(packet,cfg)
    fixed=ComposerProgramV1(tuple(c.card_id for c in cards),default_design())
    learned=ComposerProgramV1((cards[0].card_id,),{**default_design(),'raster_scale':1.25})
    selected,png,manifest=render_program(packet,cards,learned)
    write_json(out/'private/frozen_fixed_design.json',{'design':fixed.design})
    paths={'packet':'source.packet.json','manifest':'source.manifest.json','image':'source.png'}
    write_json(out/paths['packet'],selected);write_json(out/paths['manifest'],manifest);(out/paths['image']).write_bytes(png)
    (out/'conversation.md').write_text('CPU fixture, not a model result')
    record={'response':'{}'};record['record_hash']=stable_hash(record);record['artifact_hashes']={'conversation.md':sha_file(out/'conversation.md')}
    write_json(out/'source.record.json',record)
    identity={'stage':'eval','role':'composer','dataset':'aiops2022','case_id':'a','policy':'RL_COST_42'}
    key=stable_hash(identity);task={**identity,'call_key':key,'max_new_calls':1};tasks={key:task}
    row={'task':task,'case':packet['opaque_incident_id'],'status':'valid','program':asdict(learned),'record_path':'source.record.json',
         'record_hash':record['record_hash'],'render':paths,'render_hashes':{p:sha_file(out/p) for p in paths.values()}}
    row['outcome_hash']=stable_hash(row);write_json(out/'outcomes'/f'{key}.json',row)
    payload=catalog_payload(packet,cfg,ByteTokenizer());included=set();hydrate=main.hydrate
    def admitted_only(value,*,available_only=True):
        assert available_only is True
        return hydrate(value,available_only=available_only)
    monkeypatch.setattr(main,'hydrate',admitted_only)
    def include(path):included.add(str(Path(path)));return str(Path(path).relative_to(tmp_path))
    results={}
    for policy in ('U10','U01','TextTwin','ScreenshotTwin','identical_repeat','identical_repeat_second'):
        request={'stage':'local_intervention' if policy.startswith('identical') else 'attribution','role':'solver',
                 'dataset':'aiops2022','case_id':'a','policy':policy,'call_key':policy}
        entry={'case':packet['opaque_incident_id']}
        parts,visible=main._evaluation_input(cfg,request,entry,payload,out,include,tasks)
        assert not entry.get('uncalled_status');results[policy]=(parts,visible)
        assert entry['composer_record_hash']==record['record_hash']
        assert visible['fact_inventory_hash']==(packet['fact_inventory_hash'] if policy=='U01' else selected['fact_inventory_hash'])
    assert results['identical_repeat']==results['identical_repeat_second']
    assert next(p['png'] for p in results['identical_repeat'][0] if 'png' in p)==png
    assert read_json(out/'inputs/U10_manifest.json')['rq3_program']['design']==fixed.design
    assert read_json(out/'inputs/U01_manifest.json')['rq3_program']['design']==learned.design
    assert str(out/'source.record.json') in included
    row.update(status='program_failure',error='no legal card');row.pop('outcome_hash');row['outcome_hash']=stable_hash(row)
    write_json(out/'outcomes'/f'{key}.json',row);entry={'case':packet['opaque_incident_id']}
    assert main._evaluation_input(cfg,request,entry,payload,out,include,tasks)==(None,None)
    assert entry['uncalled_status']=='not_called_invalid_program'


def test_preparation_compatibility_is_specific_not_a_hash_bypass(tmp_path,monkeypatch):
    from . import utils
    monkeypatch.setattr(utils,'ROOT',tmp_path)
    renderer=tmp_path/'RQs/RQ3/src/renderer/designs.py';renderer.parent.mkdir(parents=True);renderer.write_text('fixed')
    proof={'status':'passed','before':{'pool':'old'},'after':{'pool':'new','renderer':utils.sha_file(renderer)}}
    utils.write_json(tmp_path/'RQs/RQ3/results/renderer_sort_repair_v1/compatibility.json',proof)
    assert utils.preparation_identity_matches('old','new','pool')
    assert not utils.preparation_identity_matches('unrelated','new','pool')
    assert not utils.preparation_identity_matches('old','different','pool')
    renderer.write_text('different')
    assert not utils.preparation_identity_matches('old','new','pool')
    proof.update(accepted_before={'pool':['old','older']},after_files={str(renderer.relative_to(tmp_path)):utils.sha_file(renderer)})
    utils.write_json(tmp_path/'RQs/RQ3/results/numeric_geometry_repair_v1/compatibility.json',proof)
    assert utils.preparation_identity_matches('older','new','pool')
    assert not utils.preparation_identity_matches('anything','new','pool')
    renderer.write_text('unqualified modification')
    assert not utils.preparation_identity_matches('older','new','pool')


def test_analysis_requires_and_exports_all_eval_arms(tmp_path,monkeypatch):
    """Synthetic CPU arithmetic/export check, never formal model evidence."""
    from . import utils,main
    cfg=load_config();out=tmp_path/'RQs/RQ3/results/cpu_fixture';monkeypatch.setattr(utils,'ROOT',tmp_path)
    packet=fixture_packet();outcomes=[]
    metrics=main.rca_scorer(cfg).score([],[]).as_dict()
    utils.write_json(out/'private/frozen_fixed_design.json',{'design':default_design()})
    def add(case,dataset,policy,stage='eval',fraction=None):
        task={'stage':stage,'role':'solver','dataset':dataset,'case_id':case,'policy':policy,'fraction':fraction}
        task['call_key']=stable_hash(task)
        outcomes.append({'task':task,'case':case,'status':'design_infeasible','input_tokens':0,'output_tokens':0,'metrics':metrics})
    fixed=cfg['experiments']['exp_frozen_solver_generalization']['fixed'];learned=cfg['experiments']['exp_frozen_solver_generalization']['learned']
    for dataset,count in (('aiops2022',100),('aiops2025',100),('aegislab',100),('re2_ob',90),('re2_tt',90)):
        for i in range(count):
            case=f'INC-{dataset}-{i}'
            payload=catalog_payload(packet,cfg,ByteTokenizer())
            utils.write_json(out/'prepared/eval/public'/f'{case}.json',payload)
            utils.write_json(out/'prepared/eval/private'/f'{case}.json',{'numeric_to_natural':{str(100+j):f'svc{j}' for j in range(4)},
                'accepted':['svc0'],'fault_type':'CPU fixture','granularity':{f'svc{j}':'service' for j in range(4)}})
            utils.write_json(out/'fixed_baselines/public'/f'{case}.json',{'packet':packet})
            for policy in fixed+learned:add(case,dataset,policy)
            for policy in ('U10','U01','TextTwin','ScreenshotTwin'):add(case,dataset,policy,'attribution')
    add('INC-aiops2022-0','aiops2022','SFT','validation',.25)
    monkeypatch.setattr(utils.RQ3SegmentationAdapter,'build',lambda self:{})
    monkeypatch.setattr(utils,'registered_schedule',lambda *a:{'tasks':[r['task'] for r in outcomes]})
    monkeypatch.setattr(main,'verified_phase_outcomes',lambda *a:outcomes)
    files=utils.analyze_formal(cfg,out,{'phases':[{'kind':'solver'}]})
    assert all(p.is_file() for p in files)
    assert utils.read_json(out/'analysis/summary.json')['eval_cases']==480
    import pandas as pd
    assert len(pd.read_csv(out/'analysis/performance_cost_runtime.csv'))==50
    assert len(pd.read_csv(out/'analysis/paired_hypotheses.csv'))==7
    assert pd.read_csv(out/'analysis/conditional_attribution.csv').total.eq(0).all()


def test_formal_work_spec_checks_exact_phase_and_private_input_binding(tmp_path,monkeypatch):
    from . import utils
    from .utils import write_json,sha_file,verify_work_spec
    monkeypatch.setattr(utils,'ROOT',tmp_path)
    root=tmp_path/'RQs/RQ3/results/run';root.mkdir(parents=True)
    public=root/'public.json';private=root/'private.json';parts=root/'parts.json'
    write_json(public,{'split_hash':'split','pool':{'opaque_incident_id':'INC-A','candidates':['100']}})
    write_json(private,{'dataset':'aiops2022','case_id':'a','opaque_incident_id':'INC-A'})
    write_json(parts,{'parts':[{'type':'text','text':'100'}],'candidates':['100'],'fact_inventory_hash':'facts'})
    task={'role':'solver','stage':'validation','dataset':'aiops2022','case_id':'a','policy':'SFT','call_key':'key'}
    phase={'id':'validation_SFT_solver','kind':'solver','details':{'partition':'validation'},'call_keys':['key']}
    paths={k:str(p.relative_to(tmp_path)) for k,p in [('prepared_public',public),('prepared_private',private),('parts_path',parts)]}
    spec={'phase_id':phase['id'],'role':'solver','partition':'validation','split_hash':'split','plan_hash':'plan',
          'entries':[{'task':task,'case':'INC-A','sampling_seed':42,**paths}],
          'artifact_hashes':{str(p.relative_to(tmp_path)):sha_file(p) for p in [public,private,parts]}}
    def seal(value):return {**value,'spec_hash':stable_hash({k:v for k,v in value.items() if k!='spec_hash'})}
    split={'split_hash':'split','validation':[{'dataset':'aiops2022','case_id':'a','opaque_incident_id':'INC-A'}]}
    plan={'plan_hash':'plan','phases':[phase]};schedule={'tasks':[task]}
    assert verify_work_spec(seal(spec),split,schedule,plan,root)==spec['entries']
    with pytest.raises(ValueError,match='omits/duplicates'):
        verify_work_spec(seal({**spec,'entries':spec['entries']*2}),split,schedule,plan,root)
    changed=deepcopy(spec);changed['entries'][0]['case']='INC-B'
    with pytest.raises(ValueError,match='opaque'):
        verify_work_spec(seal(changed),split,schedule,plan,root)
    write_json(private,{'dataset':'aiops2025','case_id':'b','opaque_incident_id':'INC-A'})
    changed=deepcopy(spec);changed['artifact_hashes'][paths['prepared_private']]=sha_file(private)
    with pytest.raises(ValueError,match='public/private'):
        verify_work_spec(seal(changed),split,schedule,plan,root)


def test_formal_worker_invalid_proposal_retains_zero_call_outcome_and_resume(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from . import main,utils
    from .utils import write_json,read_json
    cfg=load_config();cfg['execution_enabled']=True
    monkeypatch.setattr(main,'ROOT',tmp_path)
    monkeypatch.setattr(main,'RQ3SegmentationAdapter',lambda c:SimpleNamespace(build=lambda:{}))
    monkeypatch.setattr(utils,'registered_schedule',lambda *_:{})
    monkeypatch.setattr(utils,'formal_phase_plan',lambda *_:{})
    monkeypatch.setattr(utils,'verify_work_spec',lambda s,*_:s['entries'])
    monkeypatch.setattr(main,'request',lambda *a,**k:pytest.fail('invalid proposal called Solver'))
    root=tmp_path/'RQs/RQ3/results/unit';source=tmp_path/'spec.json'
    entry={'task':{'call_key':'abc'},'case':'INC-A','uncalled_status':'not_called_invalid_program',
           'composer_record_hash':'composer','error':'unknown card'}
    spec={'role':'solver','phase_id':'example','partition':'train','spec_hash':'hash','entries':[entry],'artifact_hashes':{}}
    write_json(source,spec);main.formal_worker(cfg,source,root)
    outcome=read_json(root/'outcomes/abc.json')
    assert outcome['status']=='not_called_invalid_program' and outcome['record_path'] is None
    assert outcome['metrics']['mrr']==0 and read_json(root/'phase_results/example.json')['status']=='complete'
    before=(root/'outcomes/abc.json').read_bytes();main.formal_worker(cfg,source,root)
    assert (root/'outcomes/abc.json').read_bytes()==before
    write_json(source,{**spec,'entries':[{**entry,'case':'INC-B'}]})
    with pytest.raises(ValueError,match='committed input'):
        main.formal_worker(cfg,source,root)


def test_pool_only_preparation_reuses_and_resumes_without_tokenizer(tmp_path,monkeypatch):
    import os
    from . import main, exps
    from .utils import pool_contract, read_json, write_json
    cfg=load_config(); packet=fixture_packet()
    private={'opaque_incident_id':'INC-TEST','dataset':'aiops2022','case_id':'case'}
    row=dict(private); calls=[]
    monkeypatch.setattr(os,'sched_setaffinity',lambda *_:None)
    monkeypatch.setattr(exps,'build_pool',lambda *a:(calls.append(a) or packet,private))
    monkeypatch.setattr(main,'materialize_catalog',lambda *a:pytest.fail('pool-only tokenized'))
    from . import utils as utility
    monkeypatch.setattr(utility,'pool_contract',lambda c:'pool-contract')
    output=tmp_path/'compiled'
    main._prepare_lane(cfg,output,'train',[row],'split','pool-contract',0,True)
    assert len(calls)==1
    before=(output/'public/INC-TEST.json').read_bytes()
    main._prepare_lane(cfg,output,'train',[row],'split','pool-contract',0,True)
    assert len(calls)==1 and before==(output/'public/INC-TEST.json').read_bytes()
    reuse={'INC-TEST':{key:str(output/key/'INC-TEST.json') for key in ('public','private')}}
    successor=tmp_path/'reused'
    main._prepare_lane(cfg,successor,'train',[row],'split','pool-contract',0,True,reuse)
    assert len(calls)==1 and read_json(successor/'public/INC-TEST.json')['pool']==packet
    write_json(successor/'private/INC-TEST.json',{**private,'altered':True})
    with pytest.raises(ValueError,match='pool content/compiler'):
        main._prepare_lane(cfg,successor,'train',[row],'split','pool-contract',0,True)
    assert pool_contract(load_config()) != pool_contract({**load_config(),'seed':43})
    identity_config=load_config();identity_config['harness']['entity_identity_policy']='public_entity_identity_v2'
    assert pool_contract(identity_config)!=pool_contract(load_config())


def test_strong_baseline_parts_text_compact_tpv_and_pixels():
    import io
    import numpy as np
    from PIL import Image
    from .exps import fixed_baseline_parts, solver_parts
    from .utils import ROOT, sha_file
    from .gates import audit_fixed_baseline
    from RQs.RQ1_1.src.exps import packet_text
    from vlmrca.evidence import compact_evidence_text, parse_compact_evidence, semantic_packet_facts
    packet=fixture_packet(); image=Image.new('RGB',(400,400),'white')
    boxes={'M':[[0,20,200,200]],'R':[[200,20,400,200]],'L':[[0,200,200,400]],'G':[[200,200,400,400]]}
    for region,color in zip(('M','R','L','G'),('red','blue','yellow','green')):
        image.paste(color,boxes[region][0])
    stream=io.BytesIO();image.save(stream,format='PNG');png=stream.getvalue()
    parent='RQs/RQ1_1/src/exps.py'
    manifest={'schema_version':'RQ3FixedBaselineV1','uses_smoke_harness':False,
        'fact_inventory_hash':packet['fact_inventory_hash'],'full_image_sha256':stable_hash(png),
        'region_crop_audit':{'source_image_px':[400,400],'crop_boxes_px':boxes},
        'parent_hashes':{parent:sha_file(ROOT/parent)}}
    t=fixed_baseline_parts(packet,png,manifest,'T_FIXED')
    c=fixed_baseline_parts(packet,png,manifest,'C_FIXED')
    tpv=fixed_baseline_parts(packet,png,manifest,'TPV_FIXED')
    assert t[:2]==c[:2]==tpv[:2]==solver_parts(packet,kind='text')[:2]
    assert t[-1]['text']==packet_text(packet)
    assert c[-1]['text']==compact_evidence_text(packet)
    assert parse_compact_evidence(c[-1]['text'])==semantic_packet_facts(packet)
    assert tpv[-1]['text']==packet_text(packet,('M','R','L'))
    assert 'Topology evidence;' not in tpv[-1]['text']
    assert all('png' not in p for p in t+c)
    visual=[p for p in tpv if 'png' in p];assert len(visual)==1
    assert visual[0]['attention_visual_regions']==['G']
    pixels=np.array(Image.open(io.BytesIO(visual[0]['png'])))
    np.testing.assert_array_equal(pixels[200:,200:],np.array(image)[200:,200:])
    assert (pixels[:200]==255).all() and (pixels[:,:200]==255).all()
    with pytest.raises(ValueError,match='facts changed'):
        audit_fixed_baseline({**packet,'facts':[]},png,manifest)
    with pytest.raises(ValueError,match='image hash'):
        audit_fixed_baseline(packet,png+b'x',manifest)
    with pytest.raises(ValueError,match='parent changed'):
        audit_fixed_baseline(packet,png,{**manifest,'parent_hashes':{parent:'wrong'}})
    with pytest.raises(ValueError,match='unknown inherited'):
        fixed_baseline_parts(packet,png,manifest,'D_FIXED')


def test_program_execution_does_not_turn_renderer_bugs_into_negative_rewards(monkeypatch):
    from . import exps, gates
    cfg=load_config();packet=fixture_packet();cards=evidence_cards(packet,cfg)
    program=ComposerProgramV1((cards[0].card_id,),default_design())
    from unified_scripts import canonical_json
    raw=canonical_json(asdict(program))
    failure,data=exps.execute_composer_program('invalid JSON',packet,cards,cfg)
    assert failure['status']=='program_failure' and failure['failure_stage']=='DSL' and data is None
    def capacity(*args):raise ValueError('metric label cannot fit its registered silhouette')
    monkeypatch.setattr(exps,'render_program',capacity)
    failure,data=exps.execute_composer_program(raw,packet,cards,cfg)
    assert failure['failure_stage']=='render_capacity' and data is None
    def bug(*args):raise ValueError('selected evidence was lost or duplicated')
    monkeypatch.setattr(exps,'render_program',bug)
    with pytest.raises(ValueError,match='lost or duplicated'):
        exps.execute_composer_program(raw,packet,cards,cfg)
    monkeypatch.setattr(exps,'render_program',lambda *args:(packet,b'png',{}))
    monkeypatch.setattr(gates,'audit_render',bug)
    with pytest.raises(ValueError,match='lost or duplicated'):
        exps.execute_composer_program(raw,packet,cards,cfg)


def test_real_cpu_rloo_backward_updates_only_policy_and_commits_one_batch(monkeypatch,tmp_path):
    import torch
    from . import exps, gates
    cfg=load_config();cfg.update(execution_enabled=True,actual_train_counts={'aiops2022':1,'aiops2025':1})
    cfg['rloo_checkpoint_provenance']={'batch_index':0,'source_envelope_hash':'audited'}
    class TinyPolicy(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.lora_A=torch.nn.ModuleDict({name:torch.nn.Linear(1,2,bias=False) for name in ('policy','reference')})
            with torch.no_grad():
                self.lora_A['policy'].weight.copy_(torch.tensor([[.3],[.1]]))
                self.lora_A['reference'].weight.copy_(torch.tensor([[.1],[.2]]))
            self.lora_A['reference'].requires_grad_(False)
            self.active='policy'
        def set_adapter(self,name):self.active=name
    model=TinyPolicy();before=model.lora_A['policy'].weight.detach().clone()
    reference=model.lora_A['reference'].weight.detach().clone()
    def logprobs(active,prompt,completion):
        distribution=torch.log_softmax(active.lora_A[active.active].weight.flatten(),0)
        return distribution[torch.tensor(completion)]
    monkeypatch.setattr(exps,'load_trainable_composer',lambda *a:(model,None,['lora_A']))
    monkeypatch.setattr(exps,'completion_logprobs',logprobs)
    monkeypatch.setattr(exps,'seed_training',lambda *a:None)
    monkeypatch.setattr(gates,'audit_training_rows',lambda *a:'cpu-split')
    groups=[]
    for dataset in ('aiops2022','aiops2025'):
        rollouts=[]
        for token,reward in zip((0,1,0,1),(1.,0.,.5,-1.)):
            old=logprobs(model,[2],[token]).detach().tolist()
            rollouts.append({'policy_version':'p0','completion_ids':[token],'prompt_ids':[2],
                'sampled_logprobs':old,'reward':reward,
                'sampling':{'temperature':1.,'top_p':1.,'top_k':-1,'min_p':0.,'grammar':None}})
        groups.append({'dataset':dataset,'case_id':'train','partition':'train','rollouts':rollouts})
    saved=[]
    def save(policy,optimizer,path,state):
        saved.append(state);assert optimizer.state_dict()['state'];return path
    monkeypatch.setattr(exps,'save_training_checkpoint',save)
    result=exps.update_rloo_batch(cfg,groups,'policy','reference',tmp_path/'checkpoint','p0')
    assert result==tmp_path/'checkpoint' and len(saved)==1
    assert not torch.equal(before,model.lora_A['policy'].weight)
    assert torch.equal(reference,model.lora_A['reference'].weight)
    assert model.lora_A['reference'].weight.grad is None
    assert saved[0]['optimization_passes']==1 and saved[0]['batch_index']==0
    assert saved[0]['source_envelope_hash']=='audited'
    assert __import__('math').isfinite(saved[0]['loss'])


def test_qualification_reference_reuses_only_identical_base_input(tmp_path, monkeypatch):
    from . import main, gates
    from .exps import composer_parts, COMPOSER_SYSTEM
    from .utils import write_json
    cfg=load_config(); payload=catalog_payload(fixture_packet(),cfg,ByteTokenizer())
    _,cards=main.hydrate(payload)
    program=ComposerProgramV1((cards[0].card_id,),default_design())
    from unified_scripts import canonical_json
    record={'response':canonical_json(asdict(program)), 'record_hash':'checked', 'policy_version':'BASE'}
    root=tmp_path/'RQs/RQ3/results/prior'; path=root/'programs/call.json'
    result={'status':'valid','case':'INC-TEST','call_key':'call',
            'response_record_hash':'checked','program':asdict(program)}
    write_json(path,result);write_json(root/'trajectories/call.json',record)
    envelope={'system':COMPOSER_SYSTEM,'parts':composer_parts(payload['observation'])}
    write_json(root/'prompts/call.json',envelope)
    monkeypatch.setattr(main,'ROOT',tmp_path)
    verified=[];monkeypatch.setattr(gates,'audit_call_artifacts',lambda d,p:verified.append(p))
    assert main.qualification_reference(path,payload,cfg)['status']=='valid'
    assert verified==[root]
    envelope['parts'][0]['text']+='changed'
    write_json(root/'prompts/call.json',envelope)
    with pytest.raises(ValueError,match='same isolated case/input'):
        main.qualification_reference(path,payload,cfg)




def test_obsolete_or_unprojected_pool_cannot_reenter_catalog():
    from .gates import audit_public_pool
    from .exps import POOL_VERSION
    pool=fixture_packet();pool["schema_version"]="RQ3EvidencePoolV1"
    with pytest.raises(ValueError,match="obsolete public pool"):
        audit_public_pool(pool)
    pool["compiler_version"]=POOL_VERSION
    pool["facts"][0]["payload"]["metric"]="container_last_seen"
    with pytest.raises(ValueError,match="unprojected absolute clock"):
        audit_public_pool(pool)
    pool["facts"][0]["payload"]["metric"]+="_relative_s"
    pool["facts"][0]["unit"]="seconds_relative_to_public_clock_reference"
    audit_public_pool(pool)


def test_catalog_meta_preview_keeps_boolean_value():
    from .exps import _catalog_preview
    cfg=load_config();f=_atomic_fact("R","explicit_missingness",{"traces_missing":False})
    packet={"facts":[f]};card=evidence_cards(packet,cfg)[0]
    preview=_catalog_preview(card,{f["fact_id"]:f},ByteTokenizer(),200)
    assert '"traces_missing":false' in preview["preview"]


def test_training_mode_checkpointing_and_zero_dropout():
    torch = pytest.importorskip("torch")
    from .exps import policy_training_mode
    class Policy(torch.nn.Module):
        def __init__(self, probability):
            super().__init__()
            self.dropout = torch.nn.Dropout(probability)
            self.active_adapter = None
        def set_adapter(self, name):
            self.active_adapter = name
    model = Policy(0)
    model.eval()
    policy_training_mode(model)
    assert model.training and model.active_adapter == "policy"
    with pytest.raises(ValueError, match="dropout"):
        policy_training_mode(Policy(.1))


def test_training_contract_tracks_recipe_not_permission_flag():
    from .exps import training_contract
    cfg = load_config()
    before = training_contract(cfg, "isolated-split")
    cfg["execution_enabled"] = not cfg["execution_enabled"]
    assert training_contract(cfg, "isolated-split") == before
    cfg["rl"]["learning_rate"] *= 2
    assert training_contract(cfg, "isolated-split") != before
    assert training_contract(load_config(), "different-split") != before
    branch=load_config();branch['training_branch']='RL_COST_42'
    cost=training_contract(branch,'isolated-split')
    branch['training_branch']='RL_RR_42'
    assert training_contract(branch,'isolated-split')!=cost


def test_optimizer_rejects_non_policy_trainables():
    torch = pytest.importorskip("torch")
    from .exps import optimizer_parameters
    class Adapter(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.lora_A = torch.nn.ModuleDict({"policy":torch.nn.Linear(2,2,bias=False),
                                              "reference":torch.nn.Linear(2,2,bias=False)})
            self.lora_A.reference.requires_grad_(False)
    model = torch.nn.ModuleDict({"language_model":Adapter()})
    assert optimizer_parameters(model) == [model["language_model"].lora_A.policy.weight]
    model["language_model"].lora_A.reference.requires_grad_(True)
    with pytest.raises(ValueError, match="unexpected trainable"):
        optimizer_parameters(model)


def test_probability_alignment_reports_real_numeric_discrepancy():
    from .gates import probability_alignment
    good=probability_alignment([-1.,-2.],[-1.01,-1.99])
    assert good["status"]=="passed" and good["token_count"]==2
    assert good["mean_absolute_logprob_error"]==pytest.approx(.01)
    assert probability_alignment([-1.,-2.],[-1.2,-2.2])["status"]=="failed"
    for old,new in [([],[]),([-1.],[-1.,-2.]),([-1.],[float('nan')]),([-1.],[.1])]:
        with pytest.raises(ValueError,match="probability vectors"):
            probability_alignment(old,new)


def test_readiness_matches_base_and_named_adapter_exactly(monkeypatch):
    import io,json,urllib.request
    from .main import smoke_server_ready
    monkeypatch.setattr(urllib.request,"urlopen",lambda *args,**kwargs:
                        io.BytesIO(json.dumps({"data":[{"id":"base"},{"id":"QUAL_LORA"}]}).encode()))
    assert smoke_server_ready("http://127.0.0.1:8123/v1","test-key","base","QUAL_LORA")
    with pytest.raises(RuntimeError,match="identity"):
        smoke_server_ready("http://127.0.0.1:8123/v1","test-key","base")
    with pytest.raises(RuntimeError,match="identity"):
        smoke_server_ready("http://127.0.0.1:8123/v1","test-key","base","other")


def test_formal_format_examples_refuse_validation(tmp_path,monkeypatch):
    from . import main,gates
    from .utils import write_json
    cfg = load_config()
    split = {"split_hash":"isolated","train":[]}
    monkeypatch.setattr(main.RQ3SegmentationAdapter,"build",lambda self:split)
    monkeypatch.setattr(gates,"audit_split",lambda data:None)
    write_json(tmp_path/"prepared/index.json",{"partition":"validation","split_hash":"isolated","cases":[]})
    with pytest.raises(ValueError,match="training preparation"):
        main.format_examples(cfg,tmp_path/"prepared",tmp_path/"out")


def test_format_targets_rebuild_catalogue_from_full_pool(tmp_path,monkeypatch):
    from . import main,gates,exps
    from .utils import write_json,read_json
    cfg = load_config()
    members = [{"dataset":d,"case_id":d,"opaque_incident_id":f"INC-{d}"} for d in ("aiops2022","aiops2025")]
    split = {"split_hash":"isolated","train":members}
    monkeypatch.setattr(main.RQ3SegmentationAdapter,"build",lambda self:split)
    monkeypatch.setattr(gates,"audit_split",lambda data:None)
    monkeypatch.setattr(gates,"audit_catalog",lambda *args:None)
    monkeypatch.setattr(gates,"audit_training_rows",lambda *args:"isolated")
    observed = []
    def complete_pool(payload,*,available_only=True):
        assert available_only is False
        return {"all_facts":True},("first","outside_shortlist")
    def examples(pool,cards,config,seed,*,limit):
        assert pool["all_facts"] and cards == ("first","outside_shortlist") and limit == 1
        observed.append(seed)
        return [{"program":{},"messages":[],"observation_hash":"cpu-fixture"}]
    monkeypatch.setattr(main,"hydrate",complete_pool)
    monkeypatch.setattr(exps,"legal_sft_examples",examples)
    rows = [{**r,"public":f"public/{r['opaque_incident_id']}.json"} for r in members]
    write_json(tmp_path/"prepared/index.json",{"partition":"train","split_hash":"isolated","cases":rows})
    for row in rows:write_json(tmp_path/"prepared"/row["public"],{"catalog_contract":"fixed"})
    result = main.format_examples(cfg,tmp_path/"prepared",tmp_path/"out",qualification=True,workers=1)
    assert len(result) == 2 and len(observed) == 2
    assert read_json(tmp_path/"out/index.json")["examples_hash"] == stable_hash(result)
    assert main.format_examples(cfg,tmp_path/"prepared",tmp_path/"out",qualification=True,workers=1) == result
    assert len(observed) == 2  # completed targets are reused, not regenerated


def test_rloo_batch_boundaries_cover_each_traversal_exactly():
    from .utils import rloo_batches
    cfg = load_config()
    split = {"split_hash":"CPU-fixture","train":[],"validation":[]}
    for dataset in ("aiops2022","aiops2025"):
        for partition,count in (("train",150),("validation",70)):
            split[partition].extend({"dataset":dataset,"case_id":f"{dataset}-{partition}-{i}",
                         "opaque_incident_id":f"INC-{dataset}-{partition}-{i}"} for i in range(count))
    batches = rloo_batches(split,cfg,"RL_COST_42")
    assert len(batches) == 32
    assert [b["end"] for b in batches if b["validation_fraction"]] == [225,450,675,900]
    assert max(len(b["cases"]) for b in batches) == 30
    observed = [(r["dataset"],r["case_id"],r["traversal"]) for b in batches for r in b["cases"]]
    assert len(observed) == len(set(observed)) == 900
    other = rloo_batches(split,cfg,"RL_COST_43")
    assert other[0]["cases"] != batches[0]["cases"]
    assert set(observed) == {(r["dataset"],r["case_id"],r["traversal"]) for b in other for r in b["cases"]}


def test_training_checkpoint_cpu_optimizer_and_rng_roundtrip(tmp_path):
    torch = pytest.importorskip("torch")
    import random
    import numpy as np
    from .exps import seed_training, save_training_checkpoint, restore_optimizer
    class Tiny(torch.nn.Linear):
        def save_pretrained(self, path, **kwargs):
            assert kwargs["selected_adapters"] == ["policy"]
            (path / "policy").mkdir()
            torch.save(self.state_dict(), path / "policy/test_weights.pt")
    seed_training(42)
    model = Tiny(2, 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.0001)
    model(torch.ones(1,2)).sum().backward()
    optimizer.step()
    path = save_training_checkpoint(model, optimizer, tmp_path / "complete", {"step":1})
    expected = (random.random(), np.random.random(), torch.rand(1).item())
    optimizer.param_groups[0]["lr"] = 1
    seed_training(99)
    state = restore_optimizer(optimizer, path)
    observed = (random.random(), np.random.random(), torch.rand(1).item())
    assert state["step"] == 1 and observed == expected
    assert optimizer.param_groups[0]["lr"] == .0001
    assert all(v["step"].device.type == "cpu" for v in optimizer.state.values())
    (path / "policy/test_weights.pt").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="hash mismatch"):
        restore_optimizer(optimizer, path)


def test_composer_adapter_is_bound_to_weight_bytes(tmp_path, monkeypatch):
    from . import main
    from .utils import write_json, sha_file
    monkeypatch.setattr(main, "ROOT", tmp_path)
    cfg = load_config()
    checkpoint = tmp_path / "RQs/RQ3/results/train/step-1"
    adapter = checkpoint / "policy"
    adapter.mkdir(parents=True)
    write_json(adapter / "adapter_config.json", {"r":16,"lora_alpha":32})
    (adapter / "adapter_model.safetensors").write_bytes(b"CPU artifact identity fixture, not model weights")
    files = {str(p.relative_to(checkpoint)):sha_file(p) for p in adapter.iterdir()}
    write_json(checkpoint / "checkpoint.json", {"complete":True,"files":files})
    cfg["composer_active_adapter"] = {"checkpoint":str(checkpoint),"name":"SFT_check"}
    observed = main.composer_adapter(cfg)
    assert observed["name"] == "SFT_check" and observed["files"] == files
    (adapter / "adapter_model.safetensors").write_bytes(b"wrong version")
    with pytest.raises(ValueError, match="hash mismatch"):
        main.composer_adapter(cfg)


def test_smoke_repair_keeps_old_counts_and_scopes_interruption(tmp_path):
    counter = CallLedger(tmp_path / "calls.sqlite", scope="learning", scope_limit=18)
    old, _ = counter.begin("old_case", "hash-old", "solver")
    new, _ = counter.begin("repair_case", "hash-new", "solver")
    counter.interrupt_scope("repair window ended", key_prefix="repair_")
    with counter.connect() as db:
        assert dict(db.execute("SELECT id,state FROM calls")) == {old:"started",new:"interrupted"}
    counter.finish(old, {"original":True})
    assert counter.summary() == {"complete":1,"interrupted":1}
    with pytest.raises(ValueError, match="mismatch"):
        counter.begin("old_case", "hash-old", "composer")
    for i in range(16):
        call, _ = counter.begin(f"next_{i}", str(i), "composer")
        counter.finish(call,{"index":i})
    with pytest.raises(RuntimeError, match="smoke call limit"):
        counter.begin("one_too_many", "extra", "composer")




def test_standalone_scorer_without_external_repo(monkeypatch):
    import sys
    from .main import rca_scorer
    monkeypatch.setitem(sys.modules, 'vlmrca.upstream', None)
    scorer = rca_scorer(load_config())
    assert scorer.score(['other', 'checkout-7dd9cb8687-abcde'], ['checkout']).mrr == .5
    assert scorer.score(['checkout'], ['checkout-7dd9cb8687-abcde']).mrr == 0
    assert scorer.score(['node-1'], ['node-2']).mrr == 0
    assert scorer.score(['node-1'], ['node-1']).mrr == 1


def test_smoke_readiness_authentication_and_http_failures(monkeypatch):
    import io
    import urllib.request
    import urllib.error
    from .main import smoke_server_ready
    def opened(request, timeout):
        assert request.full_url == 'http://127.0.0.1:8123/v1/models'
        assert request.get_header('Authorization') == 'Bearer test-key'
        return io.BytesIO(b'{"data":[{"id":"test-model"}]}')
    monkeypatch.setattr(urllib.request, 'urlopen', opened)
    assert smoke_server_ready('http://127.0.0.1:8123/v1', 'test-key', 'test-model')
    with pytest.raises(RuntimeError, match='identity'):
        smoke_server_ready('http://127.0.0.1:8123/v1', 'test-key', 'wrong-model')
    def unauthorized(*args, **kwargs):
        raise urllib.error.HTTPError('local', 401, 'Unauthorized', {}, None)
    monkeypatch.setattr(urllib.request, 'urlopen', unauthorized)
    with pytest.raises(RuntimeError, match='HTTP 401'):
        smoke_server_ready('http://127.0.0.1:8123/v1', 'test-key', 'test-model')
    def starting(*args, **kwargs):
        raise urllib.error.URLError(ConnectionRefusedError())
    monkeypatch.setattr(urllib.request, 'urlopen', starting)
    assert not smoke_server_ready('http://127.0.0.1:8123/v1', 'test-key', 'test-model')


def test_split_isolation_real_metadata():
    config=load_config()
    split=RQ3SegmentationAdapter(config).build(require_targets=False)
    audit_split(split)
    assert config["data"]["targets"] == {d: {"train":150,"validation":70} for d in ("aiops2022","aiops2025")}
    from .utils import require_split_targets
    if split["targets_met"]:
        require_split_targets(split, config)
    else:
        with pytest.raises(ValueError, match="not materialized"):
            RQ3SegmentationAdapter(config).build()


def test_log_bins_use_common_clock():
    import pandas as pd
    from .exps import readable_log_graph
    logs = pd.DataFrame({"timestamp":[25., 50.], "container_name":["svc", "svc"],
                         "message":["status 200", "status 500"], "level":[None, float('nan')]})
    graph = readable_log_graph(logs, {"svc":"123"}, public_range=(0., 100.))
    assert sorted(e['relative_bin'] for e in graph['entries']) == [16, 32]
    assert all(e['level']=='unknown' for e in graph['entries'])


def test_calendar_metadata_cannot_become_diagnostic_numeric_series():
    import pandas as pd
    from .exps import readable_log_graph
    logs=pd.DataFrame({'timestamp':[1.], 'container_name':['svc'],
                       'message':['deadline 2026-09-09T10:22:30Z request latency=250ms status=504'], 'level':['error']})
    graph=readable_log_graph(logs,{'svc':'123'},public_range=(0.,2.))
    from unified_scripts import canonical_json
    serialized=canonical_json(graph)
    assert '2026' not in serialized and '10:22' not in serialized
    assert '250' in serialized and '504' in serialized


def test_cached_artifacts_detect_loss_and_tamper(tmp_path):
    from .gates import audit_call_artifacts
    from .utils import atomic_write, sha_file
    record = {"response":"actual", "call_key":"x"}
    record['record_hash'] = stable_hash(record)
    target = tmp_path / "raw.json"; atomic_write(target,b'raw')
    record['artifact_hashes'] = {"raw.json":sha_file(target)}
    assert audit_call_artifacts(record,tmp_path)['status']=='passed'
    bad = deepcopy(record); bad['response']='changed'
    with pytest.raises(ValueError):audit_call_artifacts(bad,tmp_path)
    atomic_write(target,b'corrupt')
    with pytest.raises(ValueError):audit_call_artifacts(record,tmp_path)


def test_call_role_and_interruption_are_not_silent_retries(tmp_path):
    ledger=CallLedger(tmp_path/'calls.sqlite',20,scope='test',scope_limit=18)
    i,_=ledger.begin('a','h','composer');ledger.finish(i,{'done':True})
    assert ledger.cached('a','h','composer')=={'done':True}
    with pytest.raises(ValueError):ledger.cached('a','h','solver')
    ledger.begin('b','h','solver');ledger.interrupt_scope('worker stopped')
    with pytest.raises(RuntimeError):ledger.cached('b','h','solver')
    assert ledger.summary()=={'complete':1,'interrupted':1}


def test_training_membership_cannot_be_forged(monkeypatch):
    from .gates import audit_training_rows
    config=load_config();split=RQ3SegmentationAdapter(config).build(require_targets=False)
    # Membership-only CPU fixture; the live path still requires exact quotas.
    monkeypatch.setattr(RQ3SegmentationAdapter, "build", lambda self: split)
    real={**split['train'][0],'partition':'train'}
    audit_training_rows(config,[real])
    fake={**real,'case_id':split['eval'][real['dataset']][0]}
    with pytest.raises(ValueError):audit_training_rows(config,[fake])


def test_search_log_projection_is_explicit_and_keeps_source():
    from .exps import project_log_summaries
    import json
    packet=fixture_packet(); values=["9223372036854775807", "9223372036854775806"]
    variables={"{num1}":{"encoding":"values","values":values},
               "{ip1}":{"encoding":"values","values":["10.0.0.1","10.0.0.2"]}}
    packet['facts'].append(_atomic_fact('L','denum_log_template',
        {'template':'status {num1} peer {ip1} | numeric series='+json.dumps(variables),
         'entity_id':'100','relative_bin':4,'count':2,'template_id':'LT01'},entities=('100',),bins=(4,)))
    packet['fact_inventory_hash']=stable_hash(packet['facts']);before=deepcopy(packet)
    derived,audit=project_log_summaries(packet);text=derived['facts'][-1]['payload']['template']
    assert packet==before and not audit['lossless'] and '10.0.0.1' not in text
    assert values[0] in text and values[1] in text and 'ip1: n=2 distinct=2' in text
    assert stable_hash(derived['facts'])==derived['fact_inventory_hash']!=packet['fact_inventory_hash']
    assert derived['facts'][:-1]==packet['facts'][:-1]
    packet['facts'][-1]['payload']['count']=3
    with pytest.raises(ValueError,match='multiplicity'):project_log_summaries(packet)


@pytest.mark.parametrize('policy',['inherited_v1','grounded_v1','concise_v1','evidence_bound_v1','evidence_bound_hosting_v1','evidence_bound_membership_v1','evidence_semantics_v1','evidence_reason_first_v1'])
def test_search_candidates_stay_text_without_diagnostic_common_facts(policy):
    from .exps import search_solver_parts
    packet=fixture_packet()
    packet['facts'].append(_atomic_fact('C','private_test_sentinel',{'value':'MUST_NOT_ENTER_PROMPT'}))
    packet['fact_inventory_hash']=stable_hash(packet['facts'])
    parts=search_solver_parts(packet,b'png',{'canvas_size':[100,100]},log_summary=True,prompt_policy=policy)
    text='\n'.join(p['text'] for p in parts if p['type']=='text')
    assert 'MUST_NOT_ENTER_PROMPT' not in text and all(x in parts[1]['text'] for x in packet['candidates'])
    assert len([p for p in parts if 'png' in p])==1 and 'cpu_usage' not in text
    assert 'Log variable summaries' in text and 'run-length or base/delta' not in text


def test_search_semantics_changes_only_static_reading_guide():
    from .exps import search_solver_parts
    packet=fixture_packet();before=deepcopy(packet)
    a=search_solver_parts(packet,b'png',{'canvas_size':[100,100]},prompt_policy='evidence_bound_membership_v1')
    b=search_solver_parts(packet,b'png',{'canvas_size':[100,100]},prompt_policy='evidence_semantics_v1')
    assert packet==before and len(a)==len(b)
    changed=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    assert changed==[3] and b[3]['text'].startswith(a[3]['text'])
    assert 'current event rate / baseline event rate, NOT the fraction lost' in b[3]['text']
    assert 'rrt means average application response latency' in b[3]['text']
    assert 'working_set_bytes' in b[3]['text'] and a[1]==b[1]


def test_reason_first_changes_only_output_example_and_not_incident():
    import json
    from .exps import search_solver_parts
    p=fixture_packet();before=deepcopy(p)
    a=search_solver_parts(p,b'png',{'canvas_size':[100,100]},prompt_policy='evidence_bound_membership_v1')
    b=search_solver_parts(p,b'png',{'canvas_size':[100,100]},prompt_policy='evidence_reason_first_v1')
    assert p==before and a[1:]==b[1:]
    start='Return only JSON: ';suffix='. The reason should'
    left=a[0]['text'].split(start);right=b[0]['text'].split(start)
    assert left[0]==right[0] and left[1].split(suffix)[1]==right[1].split(suffix)[1]
    old=json.loads(left[1].split(suffix)[0]);new=json.loads(right[1].split(suffix)[0])
    assert old==new and list(new)==['reason','services','confidence']


@pytest.mark.parametrize('lfc,base,current,route',[(3,20,20,'trace_only_v1'),(2.99,100,100,'ranked_membership_v1'),
    (5,19,100,'ranked_membership_v1'),(5,100,19,'ranked_membership_v1'),('nan',100,100,'ranked_membership_v1')])
def test_public_trace_routing_has_no_outcome_dependency(lfc,base,current,route):
    from .exps import search_select
    p=fixture_packet();p['pool_coverage']={'public_membership':True}
    p['facts'].append(_atomic_fact('R','trace_summary_entry',{'rank_score':9,'latency_lfc':lfc,
        'count_base':base,'count_fault':current,'service':'100','entry_index':0},entities=('100',)))
    p['fact_inventory_hash']=stable_hash(p['facts']);before=deepcopy(p)
    result,audit=search_select(p,'trace_strength_route_v1')
    assert p==before and result==search_select(p,route)[0] and audit['route']==route
    assert bool(audit['trigger_fact_ids'])==(route=='trace_only_v1') and result['candidates']==p['candidates']
    p['facts']=[f for f in p['facts'] if f['region']!='R'];p['fact_inventory_hash']=stable_hash(p['facts'])
    assert search_select(p,'trace_strength_route_v1')[0]==search_select(p,'ranked_membership_v1')[0]


def test_resource_balanced_slots_and_fallback_are_public_and_immutable():
    from .exps import search_select,resource_metric_family
    p=fixture_packet();p['facts']=[];p['pool_coverage']={'public_membership':True}
    names=[('123','disk_total','other'),('123','fs_inodes','other'),
           ('1000','system.load.5','cpu'),('12345','pod_cpu_usage','cpu'),
           ('2000','node_memory_usage_rate','memory'),('12345','container_memory_rss','memory'),
           ('123','rrt','latency'),('123','rrt_max','latency'),('124','rrt','latency'),
           ('3000','system.io.avg_q_sz','io'),('3000','system.io.await','io'),('125','raft_apply_wait','io')]
    for i,(entity,name,family) in enumerate(names):
        f=_atomic_fact('M','metric_series_64',{'rank':i+1,'service':entity,'metric':name},entities=(entity,))
        assert resource_metric_family(f)==family
        p['facts'].append(f)
    p['fact_inventory_hash']=stable_hash(p['facts']);before=deepcopy(p)
    result,audit=search_select(p,'resource_balance_v1')
    chosen=[f['payload']['rank'] for f in result['facts'] if f['region']=='M']
    assert chosen==[3,4,5,6,7,9,10,12] and p==before
    assert result['candidates']==p['candidates'] and len(set(audit['selected_ids']))==8
    reverse=deepcopy(p);reverse['facts'].reverse();reverse['fact_inventory_hash']=stable_hash(reverse['facts'])
    assert search_select(reverse,'resource_balance_v1')[0]==result
    for kept in (0,1,2,5):
        q=deepcopy(p);q['facts']=q['facts'][:kept];q['fact_inventory_hash']=stable_hash(q['facts'])
        picked=search_select(q,'resource_balance_v1')[0]['facts']
        assert {f['fact_id'] for f in picked}=={f['fact_id'] for f in q['facts']}
    with pytest.raises(ValueError,match='eight'):search_select(p,'resource_balance_v1',4)


@pytest.mark.parametrize('nodes',[0,2,40])
def test_node_overview_is_additive_and_never_uses_private_roots(nodes):
    from .exps import search_select
    p=fixture_packet();p['facts']=[];p['pool_coverage']={'public_membership':True}
    for i in range(8+2*nodes):
        entity='123' if i<8 else str(1000+(i-8)//2)
        metric='other' if i<8 else ('node_cpu_usage' if i%2==0 else 'node_memory_usage_rate')
        p['facts'].append(_atomic_fact('M','metric_series_64',{'service':entity,'metric':metric,'rank':i+1},entities=(entity,)))
    p['fact_inventory_hash']=stable_hash(p['facts']);before=deepcopy(p)
    if nodes==40:
        with pytest.raises(ValueError,match='64-series'):search_select(p,'node_overview_v1')
    else:
        result=search_select(p,'node_overview_v1')[0]
        assert result['facts']==p['facts'] and result['candidates']==p['candidates']
        assert all(f in result['facts'] for f in search_select(p,'ranked_membership_v1')[0]['facts'])
        reverse=deepcopy(p);reverse['facts'].reverse();reverse['fact_inventory_hash']=stable_hash(reverse['facts'])
        assert search_select(reverse,'node_overview_v1')[0]['facts']==result['facts']
    assert p==before


@pytest.mark.parametrize('policy',['coverage_v1','coverage_membership_v1'])
def test_search_selection_real_manipulation_and_public_identity(policy):
    from .exps import search_select,search_solver_parts
    packet={**fixture_packet(),'pool_coverage':{'public_membership':True}};packet['facts']=[]
    for i in range(12):
        p={'panel_id':f'M{i:02d}','rank':i+1,'service':'100' if i<8 else '101',
           'metric':'cpu_usage' if i<8 else 'memory_usage','sircl_met_z':{'deviation_sigma':str(i)}}
        packet['facts'].append(_atomic_fact('M','metric_series_64',p,entities=(p['service'],)))
    packet['fact_inventory_hash']=stable_hash(packet['facts']);before=deepcopy(packet)
    a,aa=search_select(packet,'ranked_v1');b,bb=search_select(packet,policy)
    c,cc=search_select(packet,'local_contrast_v1')
    assert packet==before and len(aa['selected_ids'])==len(bb['selected_ids'])==len(cc['selected_ids'])==8
    assert aa['selected_ids']!=bb['selected_ids'] and cc['selected_ids']!=aa['selected_ids']
    assert a['candidates']==b['candidates']==c['candidates']==packet['candidates']
    reverse=deepcopy(packet);reverse['facts'].reverse();reverse['fact_inventory_hash']=stable_hash(reverse['facts'])
    assert search_select(reverse,policy)[1]['selected_ids']==bb['selected_ids']
    parts=search_solver_parts(fixture_packet(),b'png',{'canvas_size':[100,100]},prompt_policy='grounded_v1')
    assert 'Evidence discipline' in parts[0]['text'] and 'cpu_usage' not in ''.join(p.get('text','') for p in parts)
    with pytest.raises(ValueError):search_select(packet,'unknown')
    larger,more=search_select(packet,policy,metric_limit=10)
    assert sum(f['field']=='metric_series_64' for f in larger['facts'])==10
    assert more['metric_limit']==10 and set(bb['selected_ids'])<=set(more['selected_ids'])
    with pytest.raises(ValueError):search_select(packet,policy,metric_limit=65)
    with pytest.raises(ValueError):search_solver_parts(fixture_packet(),b'png',{},prompt_policy='unknown')


def test_predecessor_qualification_routes_are_fail_closed():
    from .main import preview,smoke_worker,qualify_storage
    for function,args in ((preview,(None,)*3),(smoke_worker,(None,)*6),
                          (qualify_storage,(None,)*2)):
        with pytest.raises(PermissionError,match='archived'):function(*args)


def test_hosting_selection_changes_only_public_relationships():
    from .exps import search_select,search_solver_parts
    p=fixture_packet();p['pool_coverage']={'public_hosting':True}
    host=_atomic_fact('G','public_hosting_edge',{'node':'1234','pod':'12345'},entities=('1234','12345'))
    p['facts'].append(host);p['fact_inventory_hash']=stable_hash(p['facts']);before=deepcopy(p)
    a,_=search_select(p,'ranked_v1');b,_=search_select(p,'ranked_hosting_v1')
    assert p==before and b['facts']==a['facts']+[host] and a['candidates']==b['candidates']
    reverse=deepcopy(p);reverse['facts'].reverse();reverse['fact_inventory_hash']=stable_hash(reverse['facts'])
    assert search_select(reverse,'ranked_hosting_v1')[1]['selected_ids']==search_select(p,'ranked_hosting_v1')[1]['selected_ids']
    parts=search_solver_parts(a,b'png',{},prompt_policy='evidence_bound_hosting_v1')
    assert 'node N hosts pods' in parts[3]['text'] and '12345' not in parts[3]['text']
    p['pool_coverage']['public_hosting']=False
    with pytest.raises(ValueError,match='lacks public hosting'):search_select(p,'ranked_hosting_v1')


def test_membership_cross_source_selection_and_bound_candidates():
    from .exps import search_select
    p=fixture_packet();p['pool_coverage']={'public_membership':True};p['candidates']+=['123','12345']
    p['facts'] += [_atomic_fact('G','public_name_membership',{'service':'123','pod':'12345'},entities=('123','12345')),
        _atomic_fact('R','trace_summary_entry',{'service':'123','rank_score':100},entities=('123',))]
    p['facts'] += [_atomic_fact('R','trace_summary_entry',{'service':'123','rank_score':100+i},entities=('123',)) for i in range(1,11)]
    p['facts'].append(_atomic_fact('L','denum_log_template',{'entity_id':'12345','template_id':'LT01','template':'request failed','count':3},entities=('12345',)))
    f=deepcopy(p['facts'][0]);f['payload'].update(rank=99,panel_id='M99',service='12345',metric='pod_cpu_usage',
        sircl_met_z={'regular_mean':.04,'current_mean':.4,'regular_std_dev':.005,'deviation_sigma':67})
    p['facts'].append(_atomic_fact('M',f['field'],f['payload'],entities=('12345',)))
    p['fact_inventory_hash']=stable_hash(p['facts']);before=deepcopy(p)
    a,_=search_select(p,'ranked_membership_v1',1);b,_=search_select(p,'cross_source_membership_v1',1)
    assert a['facts']!=b['facts'] and p==before and a['candidates']==b['candidates']==p['candidates']
    assert next(f for f in b['facts'] if f['field']=='metric_series_64')['payload']['service']=='12345'
    assert any(f['field']=='public_name_membership' for f in b['facts'])
    expected=sorted([f for f in p['facts'] if f['region']=='R'],key=lambda f:(-f['payload']['rank_score'],f['fact_id']))[:8]
    for policy,regions in [('trace_only_v1',set('R')),('trace_graph_v1',set('RG')),('trace_logs_graph_v1',set('RLG'))]:
        subset,audit=search_select(p,policy)
        assert p==before and subset['candidates']==p['candidates'] and audit['candidates_unchanged']
        assert {f['region'] for f in subset['facts']}==regions
        assert [f for f in subset['facts'] if f['region']=='R']==expected
        assert stable_hash(subset['facts'])==subset['fact_inventory_hash']
    with pytest.raises(ValueError,match='observed trace evidence'):search_select(fixture_packet(),'trace_only_v1')


def test_search_unlimited_accounting_retains_bounded_batches(tmp_path):
    from .main import load_config
    from .utils import ROOT
    cfg=load_config(ROOT/'RQs/RQ3/configs/search_first_v1.yaml')
    assert cfg['solver']['attention']=='off' and cfg['execution_enabled'] is False
    assert cfg['budget']['hard_limit'] is None and cfg['search']['max_batch_calls']==18
    counter=CallLedger(tmp_path/'calls.sqlite',None,scope='batch',scope_limit=2)
    for i in range(2):
        key,_=counter.begin(str(i),str(i),'solver');counter.finish(key,{'i':i})
    assert CallLedger(tmp_path/'calls.sqlite',None).summary()=={'complete':2}
    with pytest.raises(RuntimeError,match='smoke call limit'):counter.begin('extra','x','solver')
    with pytest.raises(ValueError,match='cannot change'):CallLedger(tmp_path/'calls.sqlite',40000)


@pytest.mark.parametrize('binding',['legacy_v1','enum_top5_v1'])
@pytest.mark.parametrize('profile',['legacy_v1','card_nonthinking_v1','card_thinking_low_v1','card_nonthinking_reason_first_v1','card_nonthinking_unpenalized_v1'])
@pytest.mark.parametrize('typed',[False,True])
def test_search_solver_attention_off_persists_without_probe(monkeypatch,tmp_path,profile,binding,typed):
    from types import SimpleNamespace
    from . import main
    from .exps import search_solver_parts
    from vlmrca.vlm import client
    from vlmrca.vlm import configs as cfg_module
    config=load_config();config['solver'].update(attention='off',request_profile=profile,candidate_binding=binding)
    config['search']={'enabled':True}
    solver_cfg=cfg_module.get_config('qwen3.8-27b',max_tokens=8192)
    solver_cfg.thinking=profile=='card_thinking_low_v1'
    monkeypatch.setattr(cfg_module,'get_config',lambda *a,**k:solver_cfg)
    monkeypatch.setenv('CANVASRCA_ATTENTION_PROBE','0')
    recipe=SimpleNamespace(model=lambda tag:{'max_model_len':40960},source_sha256='cpu-only')
    monkeypatch.setattr(main.VLLMInferenceConfig,'load',lambda *a,**k:recipe)
    monkeypatch.setattr(client,'count_vllm_prompt_tokens',lambda *a,**kw:3 if kw.get('text_only') else 4)
    import openai
    observed={}
    monkeypatch.setenv('VLLM_BASE_URL','http://127.0.0.1:8000/v1')
    monkeypatch.setattr(openai,'OpenAI',lambda **kw:None)
    monkeypatch.setattr(client,'assert_request_sampling',lambda **kw:None)
    def stream(_client,kwargs,*a):
        observed.update(kwargs)
        return SimpleNamespace(text='{}',raw={'finish_reason':'stop','reasoning_text':'Reasoning sentinel' if solver_cfg.thinking else ''},input_tokens=4,
                               output_tokens=1,latency_s=.1,performance={})
    monkeypatch.setattr(client,'_call_openai_streaming',stream)
    monkeypatch.setattr(client,'call_vlm',lambda parts,cfg,system,**kw:client._call_openai(
        parts,cfg,system,response_format=kw['response_format'],record_performance=True))
    parts=search_solver_parts(fixture_packet(),b'png',{'canvas_size':[100,100]},prompt_policy='evidence_candidate_types_v1' if typed else 'inherited_v1')
    ledger=CallLedger(tmp_path/'calls.sqlite',None)
    record=main.request(config,ledger,'solver',parts,'solver',tmp_path)
    services=observed['response_format']['json_schema']['schema']['properties']['services']
    if profile=='card_nonthinking_reason_first_v1':
        from .exps import rca_schema
        schema=observed['response_format']['json_schema']['schema']
        assert list(schema['properties'])==schema['required']==['reason','services','confidence']
        assert list(rca_schema()['json_schema']['schema']['properties'])==['services','reason','confidence']
    if binding=='enum_top5_v1':
        assert services['items']['enum']==fixture_packet()['candidates']
        assert services['minItems']==services['maxItems']==min(5,len(fixture_packet()['candidates']))
    else:assert 'enum' not in services['items']
    assert record['attention']=={'status':'disabled_by_protocol'} and not (tmp_path/'attention').exists()
    assert (tmp_path/'conversations/solver.md').is_file()
    template={'enable_thinking':solver_cfg.thinking,'preserve_thinking':False}
    if solver_cfg.thinking:template['reasoning_effort']='low'
    assert observed['extra_body']['chat_template_kwargs']==template
    if profile in ('card_nonthinking_v1','card_thinking_low_v1','card_nonthinking_reason_first_v1','card_nonthinking_unpenalized_v1'):
        assert (observed['temperature'],observed['top_p'],observed['presence_penalty'])==((1.,.95,0.) if solver_cfg.thinking else (.7,.8,0. if profile=='card_nonthinking_unpenalized_v1' else 1.5))
        assert {k:observed['extra_body'][k] for k in ('top_k','min_p','repetition_penalty')}=={'top_k':20,'min_p':0.,'repetition_penalty':1.}
        assert main.read_json(tmp_path/'prompts/solver.json')['request_adapter']['name']==profile
    else:assert (observed['temperature'],observed['top_p'])==(1.,.95) and 'presence_penalty' not in observed
    assert ('Reasoning sentinel' in (tmp_path/'conversations/solver.md').read_text())==solver_cfg.thinking
    monkeypatch.setattr(client,'count_vllm_prompt_tokens',lambda *a,**kw:pytest.fail('resume submitted preflight'))
    assert main.request(config,ledger,'solver',parts,'solver',tmp_path)==record
    if typed and binding=='enum_top5_v1':
        bad=deepcopy(parts);bad[1]['text']='[["123","node"]]'
        with pytest.raises(ValueError,match='unsafe typed candidate binding'):
            main.request(config,ledger,'bad',bad,'solver',tmp_path)


@pytest.mark.parametrize('typed',[False,True])
def test_search_worker_preserves_input_identity_and_rejects_eval(monkeypatch,tmp_path,typed):
    import json
    from types import SimpleNamespace
    from . import main, gates
    from .utils import read_json, write_json, sha_file
    cfg=load_config();cfg.update(search={'enabled':True,'max_batch_calls':2,'concurrency':1})
    cfg['solver']['attention']='off';cfg['budget']['hard_limit']=None
    monkeypatch.setattr(main,'ROOT',tmp_path)
    monkeypatch.setattr(main,'RQ3SegmentationAdapter',lambda c:SimpleNamespace(build=lambda:{'train':[{'opaque_incident_id':'INC-TRAIN'}]}))
    monkeypatch.setattr(gates,'audit_call_artifacts',lambda *a:None)
    calls=[]
    def answer(*args,**kwargs):
        calls.append(args[3]);return {'response':'{"services":["100"],"reason":"check","confidence":"low"}',
            'record_hash':'cpu','artifact_key':'cpu','input_tokens':4,'output_tokens':2}
    monkeypatch.setattr(main,'request',answer)
    parts=[{'type':'text','text':'static'},{'type':'text','text':'Candidates:\n["100","200"]'},
           {'type':'image','image_path':'image.png'}]
    if typed:parts[1]['text']='Candidates:\n[["100","service"],["200","service"]]'
    (tmp_path/'image.png').write_bytes(b'cpu-only')
    write_json(tmp_path/'parts.json',parts)
    write_json(tmp_path/'private.json',{'opaque_incident_id':'INC-TRAIN','numeric_to_natural':{'100':'a','200':'b'},'accepted':['a']})
    spec={'batch_id':'cpu','config_hash':stable_hash(cfg),'review_status':'passed',
          'tasks':[{'case':'INC-TRAIN','variant':'V','parts':'parts.json','private':'private.json','candidates':['100','200']}],
          'artifact_hashes':{p:sha_file(tmp_path/p) for p in ('image.png','parts.json','private.json')}}
    spec['spec_hash']=stable_hash(spec);write_json(tmp_path/'spec.json',spec)
    out=tmp_path/'RQs/RQ3/results/search_first_v1/cpu'
    main.search_worker(cfg,tmp_path/'spec.json',out)
    assert len(calls)==1 and calls[0][-1]['png']==b'cpu-only'
    assert read_json(out/'summary.json')['outcomes'][0]['metrics']['mrr']==1
    spec['tasks'][0]['case']='INC-EVAL';spec['spec_hash']=stable_hash({k:v for k,v in spec.items() if k!='spec_hash'})
    write_json(tmp_path/'spec.json',spec)
    with pytest.raises(ValueError,match='train population'):main.search_worker(cfg,tmp_path/'spec.json',out)
    assert len(calls)==1


def test_search_worker_accepts_registered_hybrid_candidate_slot(monkeypatch,tmp_path):
    from types import SimpleNamespace
    from . import main, gates
    from .exps import search_solver_parts
    from .utils import write_json, sha_file
    cfg=load_config();cfg.update(search={'enabled':True,'max_batch_calls':2,'concurrency':1})
    cfg['solver'].update(attention='off',prompt_template='rq21_visual_structure_v1')
    cfg['budget']['hard_limit']=None
    monkeypatch.setattr(main,'ROOT',tmp_path)
    monkeypatch.setattr(main,'RQ3SegmentationAdapter',lambda c:SimpleNamespace(build=lambda:{'train':[{'opaque_incident_id':'INC-TRAIN'}]}))
    monkeypatch.setattr(gates,'audit_call_artifacts',lambda *a:None)
    observed=[]
    monkeypatch.setattr(main,'request',lambda *args,**kwargs:(observed.append(args[3]) or {
        'response':'{"services":["100"],"reason":"check","confidence":"low"}',
        'record_hash':'cpu','artifact_key':'cpu','input_tokens':4,'output_tokens':2}))
    packet=fixture_packet()
    parts=search_solver_parts(packet,b'cpu-only',{},prompt_policy='tournament_hybrid_metric_v1')
    for part in parts:
        if 'png' in part:
            part.pop('png');part['image_path']='image.png'
    (tmp_path/'image.png').write_bytes(b'cpu-only');write_json(tmp_path/'parts.json',parts)
    write_json(tmp_path/'private.json',{'opaque_incident_id':'INC-TRAIN',
        'numeric_to_natural':{'100':'a','101':'b','102':'c','103':'d'},'accepted':['a']})
    spec={'batch_id':'cpu','config_hash':stable_hash(cfg),'review_status':'passed',
          'tasks':[{'case':'INC-TRAIN','variant':'hybrid','parts':'parts.json','private':'private.json',
                    'candidates':packet['candidates']}],
          'artifact_hashes':{p:sha_file(tmp_path/p) for p in ('image.png','parts.json','private.json')}}
    spec['spec_hash']=stable_hash(spec);write_json(tmp_path/'spec.json',spec)
    main.search_worker(cfg,tmp_path/'spec.json',tmp_path/'RQs/RQ3/results/search_first_v1/cpu')
    assert len(observed)==1 and [part['type'] for part in observed[0]]==['text','text','image','text','text','text']


def test_solver_prompt_task_first_without_old_design_condition():
    from .exps import solver_parts
    packet=fixture_packet()
    parts=solver_parts(packet,kind='text')
    text='\n'.join(p['text'] for p in parts)
    assert parts[0]['text'].startswith('A fault has occurred')
    assert 'How to read' not in text and 'top-24' not in text


def test_solver_attention_tags_do_not_change_chat_bytes():
    from .exps import solver_parts
    from vlmrca.vlm.client import _openai_messages
    for kind in ('text','compact'):
        parts=solver_parts(fixture_packet(),kind=kind)
        plain=[{k:v for k,v in p.items() if not k.startswith('attention_')} for p in parts]
        assert _openai_messages(parts,'system') == _openai_messages(plain,'system')
        spans=parts[-1]['attention_spans']
        assert {'M','G'} <= {s['label'] for s in spans}
        assert spans[0]['start']==0 and spans[-1]['end']==len(parts[-1]['text'])
        assert all(a['end']==b['start'] for a,b in zip(spans,spans[1:]))


def test_solver_guide_matches_connected_line_renderer():
    from .exps import solver_parts
    parts=solver_parts(fixture_packet(),b'png',{'canvas_size':[100,100]},kind='canvas')
    guide=parts[-1]['text']
    assert 'Solid lines show metric time-series trends' in guide
    assert 'dashed line bridges' not in guide and 'gray bin marks' not in guide
    assert '- `missing`, `none`, `null`, `na`' not in guide


def test_request_persists_failure_and_resumes_without_server(monkeypatch,tmp_path):
    from types import SimpleNamespace
    from . import main, gates
    from vlmrca.vlm import client
    config=load_config();packet=fixture_packet();cards=evidence_cards(packet,config)
    obs=observation(packet,cards,config,ByteTokenizer())
    from .exps import composer_parts
    parts=composer_parts(obs)
    recipe=SimpleNamespace(model=lambda tag:{'max_model_len':40960},source_sha256='config')
    monkeypatch.setattr(main,'composer_recipe',lambda config:(recipe,'rq3-composer-9b'))
    monkeypatch.setattr(gates,'validate_composer_input',lambda *a:[1,2,3])
    monkeypatch.setattr(client,'count_vllm_prompt_tokens',lambda *a,**kw:3)
    raw={'sampled_logprobs':[{'token':'token_id:7','logprob':-.3}], 'finish_reason':'stop'}
    monkeypatch.setattr(client,'call_vlm',lambda *a,**kw:SimpleNamespace(text='{}',raw=raw,input_tokens=3,
        output_tokens=1,latency_s=.1,performance={}))
    ledger=CallLedger(tmp_path/'calls.sqlite')
    record=main.request(config,ledger,'a',parts,'composer',tmp_path)
    def unavailable(*a,**kw):raise AssertionError('resume contacted server')
    monkeypatch.setattr(client,'count_vllm_prompt_tokens',unavailable)
    assert main.request(config,ledger,'a',parts,'composer',tmp_path)==record
    monkeypatch.setattr(client,'count_vllm_prompt_tokens',lambda *a,**kw:3)
    raw['sampled_logprobs'][0]['token']='guessed_string'
    with pytest.raises(ValueError):main.request(config,ledger,'b',parts,'composer',tmp_path)
    assert (tmp_path/'conversations/b.md').exists()
    assert (tmp_path/'trajectories/b.raw.json').exists()
    assert ledger.summary()=={'complete':1,'infrastructure_failure':1}
    original=(tmp_path/'trajectories/b.raw.json').read_bytes()
    raw['sampled_logprobs'][0]['token']='token_id:7'
    retried=main.request(config,ledger,'b',parts,'composer',tmp_path,retry=True)
    assert retried['artifact_key']=='b__call3'
    assert (tmp_path/'trajectories/b.raw.json').read_bytes()==original
    assert (tmp_path/'conversations/b__call3.md').is_file()
    assert ledger.summary()=={'complete':2,'infrastructure_failure':1}
    monkeypatch.setattr(client,'count_vllm_prompt_tokens',unavailable)
    assert main.request(config,ledger,'b',parts,'composer',tmp_path)==retried


def test_recover_fully_written_reply_without_resubmission(tmp_path):
    from .utils import write_json, sha_file
    ledger=CallLedger(tmp_path/'calls.sqlite',10,scope='formal')
    call_id,_=ledger.begin('a','input','solver')
    evidence=tmp_path/'conversations/a.md';evidence.parent.mkdir();evidence.write_text('complete wrong model answer')
    record={'request_hash':'input','role':'solver','call_key':'a','attempt_id':call_id,
            'response':'wrong root cause but complete reply'}
    record['record_hash']=stable_hash(record)
    record['artifact_hashes']={'conversations/a.md':sha_file(evidence)}
    write_json(tmp_path/'trajectories/a.json',record)
    second,_=ledger.begin('b','input2','solver')
    assert ledger.recover_persisted(tmp_path)=={'recovered_without_generation':[call_id],
                                              'interrupted_spent_calls':[second]}
    assert ledger.cached('a','input','solver')['response']==record['response']
    with pytest.raises(RuntimeError):ledger.cached('b','input2','solver')
    assert ledger.cached('b','input2','solver',retry=True) is None
    assert ledger.summary()=={'complete':1,'interrupted':1}


def test_recovery_rejects_corrupt_reply_and_running_retry(tmp_path):
    from .utils import write_json
    ledger=CallLedger(tmp_path/'calls.sqlite',10,scope='formal')
    call_id,_=ledger.begin('a','input','solver')
    with pytest.raises(RuntimeError):ledger.cached('a','input','solver',retry=True)
    write_json(tmp_path/'trajectories/a.json',{'request_hash':'input','role':'solver','call_key':'a',
        'attempt_id':call_id,'record_hash':'fake','artifact_hashes':{'absent':'fake'}})
    with pytest.raises(ValueError):ledger.recover_persisted(tmp_path)
    assert ledger.summary()=={'started':1}


def test_transitive_groups_and_allocation():
    rows=[{"case_id":str(i),"source":"s","event":str(i),"start":i,"end":i+1.1} for i in range(3)]
    assert len(components(rows))==1
    result=allocate_groups([rows],2,1)
    assert not result["train"] and not result["validation"] and len(result["unused"])==3


def test_durable_budget_and_resume(tmp_path):
    ledger=CallLedger(tmp_path/"calls.sqlite",2)
    i,cached=ledger.begin("a","hash","composer");assert cached is None
    with pytest.raises(RuntimeError):ledger.begin("a","hash","composer",retry=True)
    ledger.finish(i,{"value":1})
    assert ledger.begin("a","hash","composer")[1]=={"value":1}
    with pytest.raises(ValueError):ledger.begin("a","different","composer")
    i,_=ledger.begin("b","hash","solver");ledger.finish(i,{"error":"power"},"interrupted")
    with pytest.raises(RuntimeError):ledger.begin("b","hash","solver",retry=True)
    assert sum(ledger.summary().values())==2


def test_reward_and_loo():
    reference={k:10 for k in ("composer_input","composer_output","solver_input","solver_output")}
    assert cost_reward(1,reference,reference)["reward"]==pytest.approx(.98)
    assert cost_reward(.5,{k:1000 for k in reference},reference)["reward"]==pytest.approx(.46)
    assert cost_reward(.5,reference,reference,True)["reward"]==.5
    assert sum(rloo_advantages([0,0,0,1]))==pytest.approx(0)
    assert rloo_advantages([.5]*4)==[0]*4
    with pytest.raises(ValueError):rloo_advantages([1,2])


def test_program_selection_and_render_deterministic():
    packet=fixture_packet();cfg=load_config();cards=evidence_cards(packet,cfg)
    program=ComposerProgramV1(tuple(c.card_id for c in cards),{**default_design(),"grid_rows":12})
    parsed=parse_program(asdict(program),cards,cfg)
    assert parsed.selection==program.selection
    subset,png,manifest=render_program(packet,cards,program)
    assert png==render_program(packet,cards,program)[1]
    audit_render(packet,cards,program,manifest)
    assert subset["facts"]==packet["facts"]
    assert observation(packet,cards,cfg,ByteTokenizer()).constraints["catalog_coverage"]["omitted_cards"]==0


def test_program_rejects_invented_cards_and_free_text():
    cfg=load_config();cards=evidence_cards(fixture_packet(),cfg)
    p=asdict(ComposerProgramV1(("unknown",),default_design()))
    with pytest.raises(ValueError):parse_program(p,cards,cfg)
    p["selection"]=[cards[0].card_id];p["reason"]="ground truth"
    with pytest.raises(Exception):parse_program(p,cards,cfg)


def test_selection_design_interventions_and_pixel_effect():
    pool=fixture_packet();cards=evidence_cards(pool,load_config())
    fixed=ComposerProgramV1((cards[0].card_id,),{**default_design(),"grid_rows":12})
    learned=ComposerProgramV1(tuple(c.card_id for c in cards),{**fixed.design,"raster_scale":1.2})
    hybrid=portable_intervention(fixed,learned,DesignInterventionV1("learned","fixed",{}))
    assert hybrid.selection==learned.selection and hybrid.design==fixed.design
    assert select_packet(pool,cards,hybrid)[0]["facts"]==select_packet(pool,cards,learned)[0]["facts"]
    assert render_program(pool,cards,hybrid)[1]!=render_program(pool,cards,learned)[1]
    effect=attribution(.1,.3,.2,.6)
    assert effect["content_at_fixed"]+effect["design_at_fixed"]+effect["interaction"]==pytest.approx(effect["total"])


def test_registered_families_and_statistics():
    assert len(fixed_designs())==12
    assert len({stable_hash(d["design"]) for d in fixed_designs()})==12
    assert holm([.01,.04,.1])==pytest.approx([.03,.08,.1])
    assert paired_statistics([1,1],[1,1])["p"]==1


def test_sampling_and_policy_version():
    r={"policy_version":"v1","sampling":{"temperature":1.,"top_p":1.,"top_k":-1,"min_p":0.,"grammar":None},
       "completion_ids":[1,2],"sampled_logprobs":[-.2,-.3]}
    validate_rollout_probability(r,"v1")
    with pytest.raises(ValueError):validate_rollout_probability(r,"v2")
    r["sampling"]["top_p"]=.95
    with pytest.raises(ValueError):validate_rollout_probability(r,"v1")


def test_full_training_disabled():
    from .gates import assert_formal_authorized
    with pytest.raises(PermissionError):assert_formal_authorized(load_config())


def test_registered_call_budget():
    from collections import Counter
    from .utils import registered_schedule, read_json, ROOT
    cfg=load_config()
    split={p:[{"dataset":d,"case_id":f"{p}_{i}","opaque_incident_id":f"{d}_{p}_{i}"}
              for d in ("aiops2022","aiops2025") for i in range(n)]
           for p,n in (("train",150),("validation",70))}
    # Synthetic identities exercise counting only; no candidate becomes a real split.
    split.update(eval=read_json(ROOT / cfg["eval_roster"])["datasets"], split_hash="CPU-budget-fixture")
    expected = 300*3*4*2*3 + 140*12 + 140*3*4*2 + 140*2*2 + 7680 + 3120
    assert expected == cfg["budget"]["planned"] == 38000
    assert cfg["budget"]["hard_limit"] == 40000
    assert cfg["budget"]["reserve"] == 2000 and cfg["budget"]["status"] == "ready"
    assert cfg["execution_enabled"] is False
    schedule=registered_schedule(split,cfg)
    assert schedule["new_calls_max"] == 38000 and schedule["eval_count"] == 480
    assert Counter(t["stage"] for t in schedule["tasks"]) == {
        "rl":21600,"validation":3920,"fixed_validation":1680,
        "eval":7680,"attribution":1920,"local_intervention":1200,
    }
    assert len({t["call_key"] for t in schedule["tasks"]}) == 38000
    over=deepcopy(cfg); over["budget"]["reserve"] += 1
    with pytest.raises(ValueError, match="hard call limit"):
        registered_schedule(split,over)
    cfg["budget"]["planned"] -= 1
    with pytest.raises(ValueError, match="planned call-budget overflow"):
        registered_schedule(split,cfg)


def test_exact_balanced_quota_rejects_shortage_and_asymmetry():
    from .utils import require_split_targets
    cfg=load_config()
    split={p:[{"dataset":d} for d in ("aiops2022","aiops2025") for _ in range(n)]
           for p,n in (("train",150),("validation",70))}
    require_split_targets(split,cfg)
    split["train"].pop()
    with pytest.raises(ValueError, match="not materialized"):
        require_split_targets(split,cfg)
    cfg["data"]["targets"]["aiops2025"]["train"]=149
    with pytest.raises(ValueError, match="equal train"):
        require_split_targets(split,cfg)


def test_formal_phase_plan_contains_whole_registered_study():
    from .utils import formal_phase_plan
    cfg=load_config()
    split={p:[{'dataset':d,'case_id':f'{p}-{i}','opaque_incident_id':f'{d}-{p}-{i}'}
              for d in ('aiops2022','aiops2025') for i in range(n)]
           for p,n in (('train',150),('validation',70))}
    split.update(split_hash='cpu-split',eval={d:[f'eval-{i}' for i in range(n)] for d,n in
                 [('aiops2022',100),('aiops2025',100),('aegislab',100),('re2_ob',90),('re2_tt',90)]})
    plan=formal_phase_plan(split,cfg); phases=plan['phases']
    assert plan['new_calls_max']==38000
    assert sum(len(p['call_keys']) for p in phases if p['kind']=='rloo_update')==0
    assert sum(p['kind']=='rloo_update' for p in phases)==96
    assert sum(len(p['call_keys']) for p in phases if p['details'].get('partition')=='train')==21600
    names=[p['id'] for p in phases]
    assert names.index('freeze_validation_selected_policies')<names.index('prepare_eval')
    assert names.index('validation_SFT_solver')<names.index('freeze_cost_reference')
    assert names[-1]=='verify_analyze_report'
    assert all(not p['requires'] or names.index(p['requires'][0])<i for i,p in enumerate(phases))


def test_cost_reference_requires_exact_sft_validation_and_positive_means():
    from .utils import frozen_cost_reference, validate_validation_population
    split={'split_hash':'test','validation':[{'dataset':d,'case_id':str(i)}
           for d in ('aiops2022','aiops2025') for i in range(2)]}
    rows=[{**r,'partition':'validation','checkpoint':'SFT','policy':'SFT',
           'tokens':{'composer_input':100,'composer_output':20,'solver_input':200,'solver_output':10}}
          for r in split['validation']]
    rows[0]['tokens'].update(solver_input=0,solver_output=0)
    result=frozen_cost_reference(rows,split)
    assert result['means']['solver_input']==150
    assert result['means']['solver_output']==7.5
    assert result['reference_hash']==stable_hash({k:v for k,v in result.items() if k!='reference_hash'})
    for wrong in (rows[:-1],rows+[rows[0]], [{**rows[0],'partition':'eval'},*rows[1:]]):
        with pytest.raises(ValueError,match='validation population'):
            validate_validation_population(wrong,split)
    with pytest.raises(ValueError,match='completed SFT'):
        frozen_cost_reference([{**r,'infrastructure_error':True} for r in rows],split)
    with pytest.raises(ValueError,match='positive cost'):
        frozen_cost_reference([{**r,'tokens':{**r['tokens'],'solver_input':0}} for r in rows],split)
    with pytest.raises(ValueError,match='token accounting'):
        frozen_cost_reference([{**r,'tokens':{**r['tokens'],'solver_input':float('nan')}} for r in rows],split)


def test_format_example_reader_counts_cross_dataset_case_ids_and_rejects_duplicates(tmp_path):
    from .utils import read_format_examples, write_json, sha_file
    rows=[{'dataset':d,'case_id':'shared-name','partition':'train'} for d in ('aiops2022','aiops2025')]
    write_json(tmp_path/'private/rows.json',{'examples':rows,'examples_hash':stable_hash(rows)})
    item={'path':'private/rows.json','sha256':sha_file(tmp_path/'private/rows.json')}
    index={'files':[item],'examples':2,'cases':2,'examples_hash':stable_hash(rows)}
    write_json(tmp_path/'index.json',index)
    assert read_format_examples(tmp_path)[1]==rows
    write_json(tmp_path/'index.json',{**index,'files':[item,item]})
    with pytest.raises(ValueError,match='duplication'):read_format_examples(tmp_path)
    write_json(tmp_path/'index.json',index)
    (tmp_path/'private/rows.json').write_text('broken')
    with pytest.raises(ValueError,match='hash/path'):read_format_examples(tmp_path)


def test_sft_resume_ignores_partial_but_never_silently_skips_corrupt_latest(tmp_path):
    from .utils import sft_resume_checkpoint, verified_checkpoint, write_json, sha_file
    from .exps import training_contract
    cfg=load_config();examples=[{'row':i} for i in range(30)]
    assert sft_resume_checkpoint(tmp_path,examples,cfg,'split')==(None,False)
    files={}
    for step in (1,2):
        path=tmp_path/f'step-{step:05d}'
        for name in ('policy/adapter_config.json','policy/adapter_model.safetensors','training_state.pt'):
            file=path/name;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(b'cpu-fixture')
            files[name]=sha_file(file)
        write_json(path/'checkpoint.json',{'complete':True,'stage':'SFT','step':step,'cursor':30*step,
            'data_hash':stable_hash(examples),'training_contract':training_contract(cfg,'split'),'files':files})
    partial=tmp_path/'step-00003.partial-not-published';partial.mkdir()
    (partial/'checkpoint.json').write_text('incomplete')
    newest,finished=sft_resume_checkpoint(tmp_path,examples,cfg,'split')
    assert newest.name=='step-00002' and finished
    assert verified_checkpoint(newest,stage='SFT')['cursor']==60
    with pytest.raises(ValueError,match='identity mismatch'):
        sft_resume_checkpoint(tmp_path,examples+[{'row':31}],cfg,'split')
    (newest/'training_state.pt').write_bytes(b'power-loss-corruption')
    with pytest.raises(ValueError,match='missing/corrupt'):
        sft_resume_checkpoint(tmp_path,examples,cfg,'split')


def test_rloo_batch_assembly_binds_four_samples_and_preserves_invalid():
    from .utils import registered_schedule, rloo_batches, frozen_cost_reference, assemble_rloo_groups
    cfg=load_config()
    for d in cfg['data']['targets']:cfg['data']['targets'][d]={'train':2,'validation':1}
    split={p:[{'dataset':d,'case_id':f'{p}{i}','opaque_incident_id':f'{d}_{p}{i}'}
              for d in ('aiops2022','aiops2025') for i in range(n)]
           for p,n in (('train',2),('validation',1))}
    split.update(split_hash='test',eval={d:['e'] for d in ('aiops2022','aiops2025','aegislab','re2_ob','re2_tt')})
    tokens={'composer_input':100,'composer_output':20,'solver_input':200,'solver_output':10}
    ref=frozen_cost_reference([{**r,'partition':'validation','checkpoint':'SFT','policy':'SFT','tokens':tokens}
                              for r in split['validation']],split)
    schedule=registered_schedule(split,cfg);batch=rloo_batches(split,cfg,'RL_COST_42')[0]
    payload=catalog_payload(fixture_packet(),cfg,ByteTokenizer());obs=payload['observation']
    observations={r['opaque_incident_id']:obs for r in batch['cases']}
    crows={};srows={}
    for row in batch['cases']:
        for sample in range(4):
            pair={t['role']:t for t in schedule['tasks'] if t['stage']=='rl' and t['policy']=='RL_COST_42'
                and t['dataset']==row['dataset'] and t['case_id']==row['case_id']
                and t['traversal']==row['traversal'] and t['sample']==sample}
            ct,st=pair['composer'],pair['solver'];valid=sample!=3
            cr={'call_key':ct['call_key'],'role':'composer','policy_version':'p1','record_hash':'cr'+ct['call_key'],
                'completion_ids':[1,2],'prompt_ids':[5,6],'sampled_logprobs':[-.3,-.4],
                'sampling':{'temperature':1.,'top_p':1.,'top_k':-1,'min_p':0.,'grammar':None},
                'input_tokens':100,'output_tokens':20}
            crows[ct['call_key']]={'task':ct,'status':'valid' if valid else 'program_failure',
                'record':cr,'observation_hash':stable_hash(obs),'case':row['opaque_incident_id'],
                'program':{'selection':['card'],'design':{}} if valid else None}
            sr={'call_key':st['call_key'],'role':'solver','record_hash':'sr'+st['call_key'],
                'input_tokens':200,'output_tokens':10} if valid else None
            srows[st['call_key']]={'task':st,'status':'complete' if valid else 'not_called_invalid_program',
                'record':sr,'composer_record_hash':cr['record_hash'],'metrics':{'mrr':1. if sample==0 else 0.}}
    groups=assemble_rloo_groups(cfg,split,batch,schedule,crows,srows,observations,ref,'p1')
    assert len(groups)==3 and all(len(g['rollouts'])==4 for g in groups)
    for g in groups:
        assert [r['reward'] for r in g['rollouts']]==[.98,-.02,-.02,-1.]
        assert g['rollouts'][-1]['tokens']['solver_input']==0
        assert not g['rollouts'][-1]['program_valid']
    with pytest.raises(ValueError,match='on-policy|off-policy'):
        assemble_rloo_groups(cfg,split,batch,schedule,crows,srows,observations,ref,'p2')
    key=next(iter(srows));changed=deepcopy(srows);changed[key]['composer_record_hash']='another_sample'
    with pytest.raises(ValueError,match='another Composer sample'):
        assemble_rloo_groups(cfg,split,batch,schedule,crows,changed,observations,ref,'p1')
    changed=deepcopy(srows);changed[key]['status']='infrastructure_failure'
    with pytest.raises(ValueError,match='infrastructure'):
        assemble_rloo_groups(cfg,split,batch,schedule,crows,changed,observations,ref,'p1')
    changed=deepcopy(srows);changed.pop(key)
    with pytest.raises(ValueError,match='missing, repeated or extra'):
        assemble_rloo_groups(cfg,split,batch,schedule,crows,changed,observations,ref,'p1')


def test_phase_journal_lock_dependencies_integrity_and_resume(tmp_path):
    from .utils import PhaseJournal
    plan={'phases':[{'id':'a','requires':[]},{'id':'b','requires':['a']}]}
    plan['plan_hash']=stable_hash(plan)
    with PhaseJournal(tmp_path,plan) as journal:
        with pytest.raises(BlockingIOError):
            with PhaseJournal(tmp_path,plan):pass
        with pytest.raises(ValueError,match='dependency'):journal.begin('b')
        assert journal.begin('a')
        artifact=tmp_path/'output.json';artifact.write_text('committed evidence')
        journal.finish('a',[artifact],{'status':'complete'})
        assert journal.completed('a') and journal.begin('a') is False
        assert journal.begin('b')
    with PhaseJournal(tmp_path,plan) as resumed:
        assert resumed.begin('b')
        assert len(__import__('json').loads((tmp_path/'phases/b.json').read_text())['attempts'])==2
        artifact.write_text('corrupted')
        with pytest.raises(ValueError,match='missing/corrupt'):resumed.completed('a')
    with pytest.raises(RuntimeError):resumed.completed('a')


def large_catalog_packet(n=80):
    pool = fixture_packet(); facts = pool["facts"]
    for i in range(n):
        entity = str(100+i%4)
        facts.extend([
            _atomic_fact("M", "metric_series_64", {"metric": f"metric_{i}", "values": [1.]*64}, entities=(entity,), bins=range(64)),
            _atomic_fact("R", "trace_summary_entry", {"operation": f"rpc_{i}", "rank_score": i/100}, entities=(entity,)),
            _atomic_fact("L", "denum_log_template", {"entity_id": entity, "template_id": f"LT{i}", "relative_bin": i%64,
                "level": "error", "count": 10, "template": "status=504 after 1.2ms " + "long diagnostic detail "*500,
                "numeric_variables": {"raw": list(range(100))}}, entities=(entity,), bins=(i%64,)),
            _atomic_fact("G", "directed_call_edge", {"caller": entity, "callee": str(100+(i+1)%4), "edge_index": i+1},
                         entities=(entity,str(100+(i+1)%4))),
        ])
    pool["fact_inventory_hash"] = stable_hash(facts)
    return pool


def catalog_payload(pool, cfg, tokenizer):
    cards = evidence_cards(pool, cfg)
    obs, audit = build_catalog(pool, cards, cfg, tokenizer)
    return {"pool": pool, "cards": [asdict(c) for c in cards], "observation": asdict(obs), "catalog_audit": audit}


def test_catalog_budget_whole_chat_and_retained_pool():
    from .utils import chat_token_ids
    pool = large_catalog_packet(); cfg = load_config(); before = deepcopy(pool)
    payload = catalog_payload(pool, cfg, ByteTokenizer())
    result = audit_catalog(payload, cfg, ByteTokenizer(), verify_contract=False)
    assert pool == before
    assert result["input_tokens"] <= cfg["harness"]["catalog_input_token_target"]
    assert result["input_tokens"] == len(chat_token_ids(ByteTokenizer(), composer_messages(payload["observation"])))
    assert result["input_tokens"] + result["output_reserved_tokens"] + result["context_guard_tokens"] <= result["max_model_len"]
    assert {r["region"] for r in payload["observation"]["cards"]} == set("MRLG")
    assert payload["catalog_audit"]["omitted_card_ids"]
    assert any(r["preview_shortened"] for r in payload["observation"]["cards"])
    assert payload["catalog_audit"]["serialized_prompt_truncated"] is False


def test_catalog_deterministic_anonymous_and_binding():
    from .main import hydrate
    pool = large_catalog_packet(20); cfg = load_config()
    a = catalog_payload(pool, cfg, ByteTokenizer())
    shuffled = deepcopy(pool); shuffled["facts"].reverse()
    b = catalog_payload(shuffled, cfg, ByteTokenizer())
    assert a["observation"] == b["observation"]
    _, available = hydrate(a)
    assert {c.card_id for c in available} == {r["card_id"] for r in a["observation"]["cards"]}
    omitted = a["catalog_audit"]["omitted_card_ids"][0]
    with pytest.raises(ValueError):
        parse_program(asdict(ComposerProgramV1((omitted,), default_design())), available, cfg)
    corrupted = deepcopy(a); corrupted["observation"]["cards"][0]["entities"] = ["invented"]
    with pytest.raises(ValueError): audit_catalog_inventory(corrupted)


def test_catalog_oversize_common_shell_fails_without_truncating():
    pool = large_catalog_packet(4); cfg = load_config()
    pool["candidates"] = [str(i) for i in range(10000)]
    with pytest.raises(ValueError, match="mandatory candidates"):
        catalog_payload(pool, cfg, ByteTokenizer())


def test_catalog_context_changes_budget_not_model_recipe():
    from .utils import composer_input_budget
    cfg = load_config(); original = deepcopy(cfg["composer"])
    assert composer_input_budget(cfg) == 16384
    assert cfg["composer"] == original
    cfg["composer"]["max_model_len"] = 14000
    assert composer_input_budget(cfg) == 14000-4096-1024
    payload = catalog_payload(fixture_packet(), cfg, ByteTokenizer())
    assert payload["catalog_audit"]["input_tokens"] <= 14000-4096-1024


def test_log_cards_keep_entity_template_and_numeric_facts():
    pool = large_catalog_packet(20); cards = evidence_cards(pool, load_config())
    facts = {f["fact_id"]: f for f in pool["facts"]}
    for card in cards:
        if card.region == "L":
            groups = {(facts[i]["payload"]["entity_id"], facts[i]["payload"]["template_id"]) for i in card.fact_ids}
            assert len(groups) == 1
    flattened = [fid for c in cards for fid in c.fact_ids]
    assert len(flattened) == len(set(flattened)) == len(pool["facts"])


def test_over_budget_request_never_contacts_server(monkeypatch, tmp_path):
    from .main import request
    from .exps import composer_parts
    from . import utils
    from vlmrca.vlm import client
    cfg = load_config()
    payload = catalog_payload(fixture_packet(), cfg, ByteTokenizer())
    obs = deepcopy(payload["observation"])
    obs["cards"][0]["preview"] = "oversized directory "*10000
    monkeypatch.setattr(utils, "composer_tokenizer", lambda config: ByteTokenizer())
    def forbidden(*args, **kwargs):
        pytest.fail("an oversized Composer input contacted vLLM")
    monkeypatch.setattr(client, "count_vllm_prompt_tokens", forbidden)
    monkeypatch.setattr(client, "call_vlm", forbidden)
    with pytest.raises(ValueError, match="exceeds budget before contacting"):
        request(cfg, None, "oversize-test", composer_parts(obs), "composer", tmp_path)


def test_sampling_prefers_diversity_not_only_high_score():
    from dataclasses import replace
    from .exps import _catalog_order
    cfg = load_config(); cards = evidence_cards(large_catalog_packet(24), cfg)
    cards = tuple(replace(c, selection_score=1e9 if c.region=="L" else 0) for c in cards)
    stream = list(_catalog_order(cards, cfg))
    assert [c.region for c in stream[:4]] == list("MRLG")
    log_cards = [c for c in stream if c.region=="L"]
    assert len({c.entity_ids for c in log_cards[:4]}) == 4
    assert len(stream) == len(cards) == len({c.card_id for c in stream})


def test_trace_catalog_uses_actual_trcl_rank_score():
    cfg = load_config(); cfg["harness"]["trace_bundle_size"] = 1
    facts = [_atomic_fact("R", "trace_summary_entry", {"operation": f"rpc_{i}", "rank_score": score},
                          entities=("123",)) for i, score in enumerate((.2, 4., None))]
    pool = {"facts": facts, "candidates": ["123"], "fact_inventory_hash": stable_hash(facts)}
    from .exps import _catalog_order
    cards = evidence_cards(pool, cfg)
    ordered = list(_catalog_order(cards, cfg))
    assert ordered[0].selection_score == 4.
    assert sorted(c.selection_score for c in cards) == [0., .2, 4.]


def test_fixed_design_selection_exact_population_and_no_eval():
    from .utils import select_fixed_validation
    split={'split_hash':'fixture','validation':[{'dataset':d,'case_id':str(i)}
           for d in ('aiops2022','aiops2025') for i in range(2)]}
    rows=[{**r,'partition':'validation','design':d,'checkpoint':d,'reciprocal_rank':rr,
           'total_tokens':tokens,'executable':1,'infrastructure_error':False}
          for d,rr,tokens in [('F01',.5,150),('F02',.5,100)] for r in split['validation']]
    result=select_fixed_validation(rows,split,['F01','F02'])
    assert result['selected']=='F02'
    with pytest.raises(ValueError):select_fixed_validation(rows[:-1],split,['F01','F02'])
    wrong=deepcopy(rows);wrong[0]['partition']='eval'
    with pytest.raises(ValueError):select_fixed_validation(wrong,split,['F01','F02'])
    wrong=deepcopy(rows);wrong[0]['infrastructure_error']=True
    with pytest.raises(ValueError):select_fixed_validation(wrong,split,['F01','F02'])
    wrong=deepcopy(rows)
    for r in wrong:r.update(executable=0,reciprocal_rank=0,total_tokens=0)
    with pytest.raises(ValueError,match='no fixed design'):select_fixed_validation(wrong,split,['F01','F02'])


def test_learning_phase_policy_uses_previous_update_not_future(monkeypatch,tmp_path):
    from . import main as entry
    cfg=load_config();split=RQ3SegmentationAdapter(cfg).build()
    life=object.__new__(entry.LearningLifecycle);life.config=cfg;life.split=split
    monkeypatch.setattr(life,'checkpoint',lambda policy,batch=None:tmp_path/f'{policy}_{batch}')
    first={'details':{'branch':'RL_COST_42','batch_index':0}}
    version,path=life.phase_policy(first)
    assert version=='RL_COST_42_v000' and path.name=='SFT_None'
    second={'details':{'branch':'RL_COST_42','batch_index':1}}
    assert life.phase_policy(second)==('RL_COST_42_v001',tmp_path/'RL_COST_42_0')
    from .utils import rloo_batches
    quarter=next(b for b in rloo_batches(split,cfg,'RL_COST_42') if b['validation_fraction']==.25)
    version,path=life.phase_policy({'details':{'policy':'RL_COST_42','fraction':.25}})
    assert path.name==f"RL_COST_42_{quarter['index']}" and version.endswith(f"v{quarter['index']+1:03d}")


def test_rl_retention_waits_for_commit_and_preserves_validation_best(tmp_path,monkeypatch):
    from . import utils
    from .utils import write_json,sha_file,read_json,verified_checkpoint,retain_rl_checkpoints
    monkeypatch.setattr(utils,'ROOT',tmp_path);cfg=load_config();branch='RL_COST_42'
    cfg['rl']['branches']={branch:42};root=tmp_path/'models'/branch
    for index in range(21):
        path=root/f'batch-{index:03d}';files={}
        for name in ('policy/adapter_config.json','policy/adapter_model.safetensors','training_state.pt'):
            member=path/name;member.parent.mkdir(parents=True,exist_ok=True);member.write_text(str(index));files[name]=sha_file(member)
        write_json(path/'checkpoint.json',{'complete':True,'stage':'RLOO','batch_index':index,'files':files})
        phase=tmp_path/'phases'/f'{branch}_batch_{index:03d}_update.json'
        write_json(phase,{'status':'running'});retain_rl_checkpoints(cfg,tmp_path)
        if index:assert (root/f'batch-{index-1:03d}'/'training_state.pt').is_file()
        write_json(phase,{'status':'complete'})
        if index in (7,15):
            label=f'{branch}_v{index+1:03d}';rows=[{'dataset':d,'case_id':'a','partition':'validation',
                'checkpoint':label,'objective':1. if index==7 else 0.} for d in ('aiops2022','aiops2025')]
            write_json(tmp_path/'private/validation'/f'{label}.json',{'rows':rows,
                'checkpoint':str(path.relative_to(tmp_path)),'checkpoint_sha256':sha_file(path/'checkpoint.json')})
        retain_rl_checkpoints(cfg,tmp_path)
    assert sorted(p.parent.name for p in root.glob('batch-*/training_state.pt'))==['batch-019','batch-020']
    best=root/'best-for-eval/batch-007';assert verified_checkpoint(best,allow_inference_only=True)['inference_only']
    with pytest.raises(ValueError,match='missing adapter/optimizer'):verified_checkpoint(best)
    old=read_json(root/'batch-007/checkpoint.json')
    assert sha_file(best/'policy/adapter_model.safetensors')==old['files']['policy/adapter_model.safetensors']


@pytest.mark.parametrize('full',[False,True])
def test_learning_lifecycle_resume_does_not_claim_complete_rq(monkeypatch,tmp_path,full):
    from . import main as entry
    from . import gates
    from .utils import read_json,write_json
    cfg=load_config();cfg['execution_enabled']=True
    life=object.__new__(entry.FormalLifecycle if full else entry.LearningLifecycle);life.config=cfg;life.output=tmp_path
    phases=[{'id':p,'kind':p,'requires':[before] if before else [],'call_keys':[],'details':{}}
            for p,before in [('prepare_train_validation',None),('train_SFT','prepare_train_validation'),
                             ('freeze_validation_selected_policies','train_SFT'),('prepare_eval','freeze_validation_selected_policies')]]
    life.plan={'phases':phases};life.plan['plan_hash']=stable_hash(life.plan)
    monkeypatch.setattr(gates,'parent_integrity',lambda:None);calls=[]
    def execute(phase):
        calls.append(phase['id']);path=tmp_path/f"{phase['id']}.json"
        write_json(path,{'committed':True});return [path],{'status':'complete'}
    monkeypatch.setattr(life,'execute',execute)
    first=life.run();assert len(calls)==(4 if full else 3)
    assert first['manual_final_audit_required'] if full else not first['rq3_complete']
    assert life.run()==first and len(calls)==(4 if full else 3)
    assert (tmp_path/'phases/prepare_eval.json').exists()==full
    assert read_json(tmp_path/'phases/train_SFT.json')['status']=='complete'
    (tmp_path/'train_SFT.json').write_text('{}')
    with pytest.raises(ValueError,match='corrupt'):life.run()


def test_catalogue_cache_tracks_science_not_training_dispatch(monkeypatch):
    from .utils import catalogue_contract
    from . import exps
    cfg=load_config();before=catalogue_contract(cfg)
    operational=deepcopy(cfg);operational.update(execution_enabled=True,training_seed=43)
    assert catalogue_contract(operational)==before
    operational['harness']['catalog_preview_tokens']+=1
    assert catalogue_contract(operational)!=before
    monkeypatch.setattr(exps,'COMPOSER_SYSTEM',exps.COMPOSER_SYSTEM+' Changed instructions.')
    assert catalogue_contract(cfg)!=before


def test_eval_preparation_requires_all_validation_frozen_policies(monkeypatch,tmp_path):
    from . import utils
    from .utils import partition_rows,write_json,sha_file
    cfg=load_config();split={'split_hash':'split','eval':{d:[f'{d}_{i}' for i in range(n)]
         for d,n in [('aiops2022',100),('aiops2025',100),('aegislab',100),('re2_ob',90),('re2_tt',90)]}}
    monkeypatch.setattr(utils,'ROOT',tmp_path)
    monkeypatch.setattr(utils,'formal_phase_plan',lambda *args:{'plan_hash':'plan'})
    monkeypatch.setattr(utils,'verified_checkpoint',lambda *args,**kwargs:None)
    with pytest.raises(ValueError,match='frozen validation'):partition_rows(cfg,split,'eval')
    root=tmp_path/'RQs/RQ3/results/test';freeze=root/'private/frozen_policies.json'
    checkpoint=root/'models/frozen';write_json(checkpoint/'checkpoint.json',{'complete':True})
    spec={'checkpoint':str(checkpoint.relative_to(tmp_path)),'checkpoint_sha256':sha_file(checkpoint/'checkpoint.json')}
    body={'split_hash':'split','plan_hash':'plan','evaluation_used':False,'policies':{
        p:({'checkpoint':None} if p=='BASE' else spec) for p in cfg['experiments']['exp_frozen_solver_generalization']['learned']}}
    cfg['evaluation_freeze']=str(freeze.relative_to(tmp_path));write_json(freeze,body)
    state={'status':'running','plan_hash':'plan','artifact_hashes':{'private/frozen_policies.json':sha_file(freeze)}}
    write_json(root/'phases/freeze_validation_selected_policies.json',state)
    with pytest.raises(ValueError,match='not committed'):partition_rows(cfg,split,'eval')
    state['status']='complete';write_json(root/'phases/freeze_validation_selected_policies.json',state)
    from unified_scripts import canonical_json
    for d,ids in split['eval'].items():
        path=tmp_path/cfg['processed_root']/'private'/d/'manifest.jsonl'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('\n'.join(canonical_json({'case_id':c,'opaque_incident_id':f'INC-{d}-{i}'}) for i,c in enumerate(ids)))
    rows=partition_rows(cfg,split,'eval');assert len(rows)==480
    assert set(r['dataset'] for r in rows)==set(split['eval'])
    tc={**cfg,'solver':{**cfg['solver'],'attention':'off'},'tournament':{
        'schema':'RQ3EliminationTournamentV1','roster':cfg['eval_roster'],'cases':480,'optimizer_eval_overlap_allowed':False}}
    write_json(tmp_path/cfg['eval_roster'],{'datasets':split['eval']})
    split['eval_roster_sha256']=sha_file(tmp_path/cfg['eval_roster'])
    assert partition_rows(tc,split,'tournament')==rows
    tc['tournament']['optimizer_eval_overlap_allowed']=True
    with pytest.raises(ValueError,match='explicit contract'):partition_rows(tc,split,'tournament')
    tc['tournament']['optimizer_eval_overlap_allowed']=False;split['eval_roster_sha256']='changed'
    with pytest.raises(ValueError,match='protected split'):partition_rows(tc,split,'tournament')
    body['evaluation_used']=True;write_json(freeze,body)
    with pytest.raises(ValueError,match='isolated validation'):partition_rows(cfg,split,'eval')

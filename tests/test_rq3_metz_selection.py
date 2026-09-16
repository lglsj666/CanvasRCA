"""SEARCH26 public score/coverage semantics; no model calls or private data."""
from copy import deepcopy
import pytest
from RQs.RQ3.src.exps import search_select
from RQs.RQ3.src.utils import stable_hash,ROOT
from RQs.RQ3.src.main import load_config


def pool():
    facts=[]
    for i in range(12):
        owner='123' if i<10 else str(124+i)
        facts.append({'fact_id':f'M{i:03}','region':'M','field':'metric_series_64','entity_ids':[owner],
                      'payload':{'panel_id':f'M{i:03}','rank':i+1,'service':owner,'metric':'latency',
                                 'sircl_met_z':{'deviation_sigma':str(i)}}})
    return {'facts':facts,'fact_inventory_hash':stable_hash(facts),'candidates':['123','134','135'],
            'pool_coverage':{'public_membership':True}}


def select(p,policy):
    p['fact_inventory_hash']=stable_hash(p['facts'])
    return search_select(p,policy)[0]


def test_metz_priority_changes_selected_facts_preserves_source_and_candidates():
    p=pool();before=deepcopy(p)
    a=select(p,'metz_overview_v1');b=select(p,'node_overview_v1')
    assert [f['payload']['rank'] for f in a['facts']]==list(range(12,4,-1))
    assert a['facts']!=b['facts'] and p==before and a['candidates']==p['candidates']
    assert all(f in p['facts'] for f in a['facts'])
    p['facts'].reverse();assert select(p,'metz_overview_v1')['facts']==a['facts']


def test_coverage_prefers_new_owner_among_valid_scores_not_missing():
    p=pool();p['facts'][0]['payload']['sircl_met_z']['deviation_sigma']='99'
    a=select(p,'metz_coverage_overview_v1')
    assert [f['payload']['service'] for f in a['facts'][:3]]==['123','135','134']
    p['facts'][-1]['payload']['sircl_met_z']['deviation_sigma']=None
    b=select(p,'metz_coverage_overview_v1')
    assert '135' not in [f['payload']['service'] for f in b['facts']]
    assert len(b['facts'])==8


@pytest.mark.parametrize('bad',[None,True,False,'nan','inf','1e999','-2',{},'unknown'])
def test_missing_invalid_scores_keep_native_fallback_without_fabricating_values(bad):
    p=pool()
    for f in p['facts']:f['payload']['sircl_met_z']['deviation_sigma']=bad
    for policy in ('metz_overview_v1','metz_coverage_overview_v1'):
        a=select(p,policy);assert a['facts']==p['facts'][:8]
        assert all(f['payload']['sircl_met_z']['deviation_sigma']==bad for f in a['facts'])


def test_overview_keeps_all_registered_node_references_and_bound():
    p=pool()
    for i,name in enumerate(('node_cpu_usage','node_memory_usage_rate')):
        f=deepcopy(p['facts'][0]);f['fact_id']=f'M{20+i}';f['payload'].update(panel_id=f'M{20+i}',rank=20+i,service='1234',metric=name)
        f['entity_ids']=['1234'];p['facts'].append(f)
    p['candidates'].append('1234')
    for policy in ('metz_overview_v1','metz_coverage_overview_v1'):
        a=select(p,policy)
        assert 8<=len(a['facts'])<=10 and all(f in a['facts'] for f in p['facts'][-2:])
        assert len({f['fact_id'] for f in a['facts']})==len(a['facts'])
        with pytest.raises(ValueError,match='eight-series'):search_select(p,policy,16)


def test_registered_runtime_and_static_inputs_are_unchanged():
    a=load_config(ROOT/'RQs/RQ3/configs/search_owner_header_v1.yaml')
    b=load_config(ROOT/'RQs/RQ3/configs/search_metz_overview_v1.yaml')
    assert a['solver']==b['solver'] and a['harness']==b['harness']
    x=deepcopy(a['search']);y=deepcopy(b['search'])
    x.pop('selectors');y.pop('selectors');x.pop('max_batch_calls');y.pop('max_batch_calls')
    assert x==y and b['search']['max_batch_calls']==48


@pytest.mark.parametrize('score',['70.8k','334707524.3G','15M','1e3','1.2e2k'])
def test_native_formatted_score_suffix_is_not_dropped(score):
    p=pool();p['facts'][0]['payload']['sircl_met_z']['deviation_sigma']=score
    for policy in ('metz_overview_v1','metz_coverage_overview_v1'):
        a=select(p,policy);assert a['facts'][0]==p['facts'][0]


def test_zero_score_is_valid_and_precedes_missing_even_when_native_rank_is_later():
    p=pool()
    for f in p['facts']:f['payload']['sircl_met_z']['deviation_sigma']=None
    p['facts'][-1]['payload']['sircl_met_z']['deviation_sigma']='0'
    for policy in ('metz_overview_v1','metz_coverage_overview_v1'):
        assert select(p,policy)['facts'][0]==p['facts'][-1]

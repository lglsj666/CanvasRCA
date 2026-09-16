"""Native Drain/source bindings and six-row selection; no private labels/models."""
from copy import deepcopy
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from packages.rq21_native.log_adapter import rank_log_templates
from packages.rq21_native.sircl_adapted.extractors.log_template_freq import build_torai_template_freq


def source():
    rows=[]
    for i in range(9):
        rows.extend({'container_name':f'svc{i}','message':f'worker unit {i} handled {j} requests',
                     'timestamp':j+5.,'level':'info'} for j in range(i+2))
    rows.append({'container_name':'svc0','message':'old baseline error','timestamp':0.,'level':'error'})
    return pd.DataFrame(rows)


def test_native_differential_original_and_adapted():
    from RQs.RQ2_1.src.tests import original_component, native_fixture
    fixture=native_fixture();original=original_component('extractors/log_template_freq.py')
    assert original.build_torai_template_freq(SimpleNamespace(logs_df=fixture.logs_df,
        timestamp=fixture.analysis_start_s,services=fixture.services))==build_torai_template_freq(fixture)
    data=source();before=data.copy(deep=True)
    safe=data.assign(_rq21_time_s=data.timestamp,_source_row=np.arange(len(data)))
    expected=build_torai_template_freq(SimpleNamespace(logs_df=safe,analysis_start_s=5),structured=True)
    got=rank_log_templates(data,data.timestamp,[5,20])
    assert got['rows']==expected and sum(r['count'] for r in expected)==len(data)-1
    pd.testing.assert_frame_equal(data,before)


def test_invalid_nan_duplicate_index_and_window(tmp_path,monkeypatch):
    data=source();data.index=[0]*len(data);times=data.timestamp.to_numpy().copy();times[0]=np.nan
    result=rank_log_templates(data,times,[5,8]);indices=[i for r in result['rows'] for i in r['source_rows']]
    assert len(set(indices))==len(indices) and 0 not in indices
    assert all(5<=times[i]<=8 for i in indices) and result['excluded_rows']>0
    assert rank_log_templates(data,times,None)['rows']==[]
    with pytest.raises(ValueError):rank_log_templates(data,times,[10,5])
    with pytest.raises(ValueError):rank_log_templates(data,times[:-1],[5,8])
    with pytest.raises(ValueError):rank_log_templates(data,times[:,None],[5,8])
    monkeypatch.chdir(tmp_path);(tmp_path/'drain3.ini').write_text('[DRAIN]\nsim_th=0.9')
    with pytest.raises(ValueError,match='configuration'):rank_log_templates(data,times,[5,8])


def pool_and_native():
    from RQs.RQ3.src.exps import readable_log_graph,native_log_bindings,_atomic_fact,stable_hash
    data=source();mapping={f'svc{i}':str(111+i) for i in range(9)}
    graph=readable_log_graph(data,mapping,public_range=(0,20))
    facts=[]
    for e in graph['entries']:
        payload={k:v for k,v in e.items() if k!='numeric_variables'}
        facts.append(_atomic_fact('L','denum_log_template',payload,entities=(e['entity_id'],),bins=(e['relative_bin'],)))
    return {'facts':facts,'fact_inventory_hash':stable_hash(facts),'candidates':list(mapping.values()),
            'pool_coverage':{'public_membership':True}},native_log_bindings(data,mapping,(0,20),(5,20))


def test_native_binding_and_selector_uses_six_distinct_templates():
    from RQs.RQ3.src.exps import search_select
    pool,native=pool_and_native();before=deepcopy(pool)
    got,audit=search_select(pool,'sircl_log_freq6_v1',8,native_selection=native)
    assert len(got['facts'])==6 and len(audit['native_selected_ids'])==6 and not audit['fill_ids']
    assert {f['payload']['entity_id'] for f in got['facts']}=={str(i) for i in range(114,120)}
    assert all(f['payload']['relative_bin']>=16 for f in got['facts'])
    assert sum(r['source_count'] for r in native['rows'])==native['bound_events']
    assert pool==before
    prior,_=search_select(pool,'node_overview_v1',8)
    assert {f['fact_id'] for f in got['facts']}!={f['fact_id'] for f in prior['facts']}


def test_binding_missing_or_excess_count_fails_not_fallback():
    from RQs.RQ3.src.exps import search_select
    pool,native=pool_and_native()
    bad=deepcopy(native);bad['rows'][0]['template']='not in source'
    with pytest.raises(ValueError,match='absent'):search_select(pool,'sircl_log_freq6_v1',8,native_selection=bad)
    bad=deepcopy(native);bad['rows'][0]['source_count']=10**6
    with pytest.raises(ValueError,match='multiplicity'):search_select(pool,'sircl_log_freq6_v1',8,native_selection=bad)
    with pytest.raises(ValueError,match='bindings'):search_select(pool,'sircl_log_freq6_v1',8)


def test_empty_native_has_explicit_unique_parent_fill():
    from RQs.RQ3.src.exps import search_select,native_log_bindings
    pool,_=pool_and_native();native=native_log_bindings(pd.DataFrame(),{},None,None)
    got,audit=search_select(pool,'sircl_log_freq6_v1',8,native_selection=native)
    assert len(got['facts'])==6 and len(audit['fill_ids'])==6 and not audit['native_selected_ids']


def test_native_binding_requires_canonical_clock_and_owner():
    from RQs.RQ3.src.exps import native_log_bindings
    data=source()
    with pytest.raises(ValueError,match='timestamp'):native_log_bindings(data.drop(columns='timestamp'),{},(0,20),(5,20))
    with pytest.raises(ValueError,match='entity map'):native_log_bindings(data,{},(0,20),(5,20))

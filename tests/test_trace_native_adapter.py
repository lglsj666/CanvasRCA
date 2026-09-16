"""SIRCL support/confidence differential tests; no model or private labels."""
from copy import deepcopy
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from packages.rq21_native.trace_adapter import rank_trace_operations
from packages.rq21_native.sircl_adapted.extractors.tracerca_scorer import score_operations_jaccard


def source():
    return pd.DataFrame({'service_name':['a']*6+['b']*6+['c']*6,
        'operation_name':['get']*18, '_rq21_time_s':list(range(6))*3,
        'duration_ms':[1,2,3,7,8,9,1,2,3,4,4,4,2,2,2,2,2,2]})


def test_exact_source_algorithm_and_constant_behavior():
    data=source();before=data.copy(deep=True)
    expected=score_operations_jaccard(SimpleNamespace(traces_df=data,analysis_start_s=3),structured=True)
    got=rank_trace_operations(data,data['_rq21_time_s'],[3,5])
    assert [{k:v for k,v in r.items() if k not in ('service','operation_name')} for r in got['rows']]==expected
    assert [r['operation'] for r in got['rows']]==['a_get','c_get']
    assert all(r['confidence']==1 for r in got['rows'])  # native >= marks unchanged constant periods
    pd.testing.assert_frame_equal(data,before)


def test_window_nan_default_operation_and_collision():
    data=source().drop(columns='operation_name');times=data['_rq21_time_s'].to_numpy(dtype=float);times[0]=np.nan
    got=rank_trace_operations(data,times,[3,4]);assert got['excluded_rows']==4
    assert all(r['operation_name']=='default' for r in got['rows'])
    assert rank_trace_operations(data,times,None)['rows']==[]
    assert rank_trace_operations(data,times,[0,4])['rows']==[]
    collision=pd.DataFrame({'service_name':['a_b','a'],'operation_name':['c','b_c'],'duration_ms':[1,2]})
    with pytest.raises(ValueError,match='collision'):rank_trace_operations(collision,[0,1],[.5,1])
    with pytest.raises(ValueError):rank_trace_operations(data,times,[5,3])


def test_source_scale_does_not_change_ranking():
    a=source();b=source();b['duration_ms']*=1000
    assert rank_trace_operations(a,a['_rq21_time_s'],[3,5])==rank_trace_operations(b,b['_rq21_time_s'],[3,5])


def test_native_selection_changes_eight_trace_entries_without_mutation():
    from RQs.RQ3.src.exps import search_select, stable_hash
    facts=[{'fact_id':f'm{i}','region':'M','field':'metric_series_64','entity_ids':['111'],
            'payload':{'rank':i,'panel_id':f'M{i}','service':'111','metric':'cpu'}} for i in range(8)]
    facts += [{'fact_id':f'r{i}','region':'R','field':'trace_summary_entry','entity_ids':['111'],
        'payload':{'service':'111','operation':f'rpc_{i}','rank_score':10-i,'entry_index':i}} for i in range(10)]
    pool={'facts':facts,'fact_inventory_hash':stable_hash(facts),'candidates':['111'],'pool_coverage':{'public_membership':True}}
    before=deepcopy(pool);native={'rows':[{'service':'111','operation':f'rpc_{i}'} for i in range(9,-1,-1)],'status':'ranked'}
    packet,audit=search_select(pool,'sircl_trace_sc8_v1',8,native_selection=native)
    assert {f['fact_id'] for f in packet['facts'] if f['region']=='R'}=={f'r{i}' for i in range(2,10)}
    assert audit['fill_ids']==[] and pool==before
    native={'rows':[{'service':'222','operation':'outside_pool'},{'service':'111','operation':'rpc_9'}]}
    packet,audit=search_select(pool,'sircl_trace_sc8_v1',8,native_selection=native)
    assert len(audit['fill_ids'])==7 and len(audit['unbound_native_rows'])==1
    assert audit['native_selected_ids']==['r9'] and pool==before
    with pytest.raises(ValueError):search_select(pool,'sircl_trace_sc8_v1',8)


def test_empty_trace_source_keeps_other_modalities():
    from RQs.RQ3.src.exps import search_select,stable_hash
    pool={'facts':[],'fact_inventory_hash':stable_hash([]),'candidates':['111'],'pool_coverage':{'public_membership':True}}
    packet,audit=search_select(pool,'sircl_trace_sc8_v1',8,native_selection={'rows':[],'status':'no_native_rank'})
    assert not packet['facts'] and not audit['fill_ids']

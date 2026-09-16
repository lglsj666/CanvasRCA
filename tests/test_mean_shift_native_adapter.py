"""SIRCL MA source parity, sparse clocks and actual selection; CPU only."""
from copy import deepcopy
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from packages.rq21_native.mean_shift_adapter import rank_mean_shift_metrics
from packages.rq21_native.sircl_adapted.metrics.metrics_ma import MetricsVariantMA


def frame():
    return pd.DataFrame({'timestamp':range(8),
        'svc_rise':[1,2,3,2,10,12,14,11],
        'svc_drop':[101,102,103,102,1,2,3,2],
        'svc_steady':[1,2,3,2,1,2,3,2],
        'svc_constant':[1,1,1,1,20,20,20,20]})


def test_source_differential_and_strict_signed_mean_shift():
    from RQs.RQ2_1.src.tests import original_component
    original=original_component('metrics/metrics_ma.py').MetricsVariantMA()
    original._get_split_time=lambda case:case.analysis_start_s  # identical safe split, original numeric body
    data=frame();before=data.copy(deep=True)
    safe=SimpleNamespace(metrics_df=data,services=['svc'],timestamp=4,analysis_start_s=4)
    assert original.get_metrics_context(safe)==MetricsVariantMA().get_metrics_context(safe)
    native=MetricsVariantMA().get_metrics_context(safe,structured=True)
    got=rank_mean_shift_metrics(data,[4,7])
    assert got['ranks']==['svc_drop','svc_rise']
    assert got['rows']==[{k:v for k,v in r.items() if k not in ('key','service','metric')} for r in native]
    assert set(got['excluded'])=={'svc_steady','svc_constant'}
    pd.testing.assert_frame_equal(before,data)


def test_sparse_bad_clocks_numeric_strings_and_end_bound():
    dense=frame();data=pd.concat([dense,dense],ignore_index=True)
    data.loc[8:,'timestamp']+=8
    data.loc[8:,'svc_rise']=1000000
    data=data.astype(str)
    assert rank_mean_shift_metrics(data,[4,7])==rank_mean_shift_metrics(dense,[4,7])
    data.loc[8,'timestamp']='nan';data.loc[9,'timestamp']='inf'
    assert rank_mean_shift_metrics(data,[4,7])==rank_mean_shift_metrics(dense,[4,7])
    sparse=pd.concat([dense,dense],ignore_index=True)
    sparse.loc[:7,'svc_drop']=np.nan;sparse.loc[8:,'svc_rise']=np.nan
    sparse.loc[8:,'timestamp']=range(8)
    assert rank_mean_shift_metrics(sparse,[4,7])['ranks']==['svc_drop','svc_rise']


def test_threshold_and_prefix_collision_independent_of_names():
    data=pd.DataFrame({'timestamp':[0,1,2,3], 'a_cpu':[-1,1,3,3],
        'a_b_cpu':[-1,1,3.001,3.001], 'bad':[np.inf]*4})
    got=rank_mean_shift_metrics(data,[2,3])
    assert got['ranks']==['a_b_cpu']  # exactly 3σ must not pass
    assert got['excluded']['bad']=='insufficient_finite_period_samples'
    assert rank_mean_shift_metrics(data.rename(columns={'a_b_cpu':'plain'}),[2,3])['ranks']==['plain']


def test_invalid_input_and_no_window():
    data=frame()
    assert rank_mean_shift_metrics(data,None)['ranks']==[]
    for window in ([7,4],[np.nan,7]):
        with pytest.raises(ValueError):rank_mean_shift_metrics(data,window)
    with pytest.raises(ValueError):rank_mean_shift_metrics(data.rename(columns={'svc_drop':'svc_rise'}),[4,7])
    with pytest.raises(ValueError):rank_mean_shift_metrics(data.drop(columns='timestamp'),[4,7])


def test_sustained_shift_complement_at_formal_24_series_budget():
    from packages.rq21_native.baro_adapter import rank_finite_metrics
    data={'timestamp':range(8)}
    data.update({f'sustained_{i}':[-1,1,-1,1,40+i/10,41+i/10,40+i/10,41+i/10] for i in range(24)})
    data.update({f'spike_{i}':[-1,1,-1,1,100+i,0,0,0] for i in range(6)})
    data=pd.DataFrame(data)
    ma=rank_mean_shift_metrics(data,[4,7])['ranks'][:24]
    baro=rank_finite_metrics(data,[4,7])['ranks'][:24]
    assert len(ma)==len(baro)==24 and set(ma)!=set(baro)
    assert all(c.startswith('sustained_') for c in ma)
    assert len([c for c in baro if c.startswith('spike_')])==6


def test_no_eligible_and_unrepresentable_numeric_state():
    data=pd.DataFrame({'timestamp':[0,1,2,3],'all_nan':[np.nan]*4,'constant':[1]*4})
    result=rank_mean_shift_metrics(data,[2,3])
    assert result['status']=='no_eligible_series' and not result['ranks']
    assert len(result['excluded'])==2
    data['huge']=[1e308,-1e308,1.,2.]
    with pytest.raises(FloatingPointError):rank_mean_shift_metrics(data,[2,3])


def test_top24_selection_binding_and_explicit_fill():
    from RQs.RQ3.src.exps import search_select,stable_hash
    facts=[{'fact_id':f'f{i}','field':'metric_series_64','region':'M','entity_ids':[str(100+i)],
        'payload':{'panel_id':f'M{i:02d}','rank':i,'service':str(100+i),'metric':'cpu'}} for i in range(1,31)]
    pool={'facts':facts,'fact_inventory_hash':stable_hash(facts),'candidates':[str(100+i) for i in range(1,31)],
          'pool_coverage':{'public_membership':True}}
    before=deepcopy(pool)
    native={'ranks':[f'M{i:02d}' for i in range(30,0,-1)],'excluded':{},'status':'ranked'}
    packet,audit=search_select(pool,'sircl_ma24_v1',24,native_selection=native)
    assert {f['fact_id'] for f in packet['facts']}=={f'f{i}' for i in range(7,31)}
    assert not audit['fill_ids'] and pool==before
    native['ranks']=['M30'];packet,audit=search_select(pool,'sircl_ma24_v1',24,native_selection=native)
    assert len(audit['fill_ids'])==23 and len(packet['facts'])==24
    for ranks in (['M99'],['M30','M30']):
        with pytest.raises(ValueError):search_select(pool,'sircl_ma24_v1',24,native_selection={**native,'ranks':ranks})
    with pytest.raises(ValueError):search_select(pool,'sircl_ma24_v1',24)

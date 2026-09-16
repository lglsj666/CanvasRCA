"""Native BARO parity and RQ3 binding; CPU only, no label-based decisions."""
from copy import deepcopy
import numpy as np
import pandas as pd
import pytest
from packages.rq21_native.baro_adapter import rank_finite_metrics
from packages.rq21_native.baro_original.root_cause_analysis import robust_scorer


def frame():
    return pd.DataFrame({'timestamp': range(8),
        'rise_cpu': [1, 2, 3, 2, 10, 12, 14, 11],
        'drop_mem': [101, 102, 103, 102, 1, 2, 3, 2],
        'steady': [3, 4, 5, 4, 3, 4, 5, 4],
        'constant': [1] * 8})


def test_native_dense_order_and_signed_direction():
    data = frame(); before = data.copy(deep=True)
    expected = robust_scorer(data.rename(columns={'timestamp': 'time'}), inject_time=4)['ranks']
    got = rank_finite_metrics(data, [4, 7])
    assert got['ranks'] == expected == ['rise_cpu', 'steady', 'drop_mem']
    assert got['excluded'] == {'constant': 'native_constant_period_filter'}
    pd.testing.assert_frame_equal(data, before)


def test_sparse_alignment_preserves_observations_not_zero_filling():
    dense = frame(); sparse = dense.reindex(range(16))
    sparse['timestamp'] = list(range(4)) + list(range(8, 12)) + list(range(4, 8)) + list(range(12, 16))
    # Move different columns' existing samples into previously empty rows.
    for col in ['drop_mem', 'steady']:
        sparse.loc[8:15, col] = sparse.loc[:7, col].to_numpy()
        sparse.loc[:7, col] = np.nan
    sparse.loc[8:11, 'timestamp'] = range(4)
    sparse.loc[12:15, 'timestamp'] = range(8, 12)
    assert rank_finite_metrics(sparse, [8, 15])['ranks'] == rank_finite_metrics(dense, [4, 7])['ranks']
    assert rank_finite_metrics(dense, None)['ranks'] == []


def test_input_checks_and_period_support():
    data = frame(); data['bad'] = [np.inf] * 8
    got = rank_finite_metrics(data, [4, 7])
    assert got['excluded']['bad'] == 'insufficient_finite_period_samples'
    for window in ([7, 4], [np.nan, 7]):
        with pytest.raises(ValueError): rank_finite_metrics(data, window)
    with pytest.raises(ValueError): rank_finite_metrics(data.rename(columns={'bad':'steady'}), [4, 7])


def test_selection_uses_native_panels_and_does_not_mutate_pool():
    from RQs.RQ3.src.exps import search_select, stable_hash
    facts = [{'fact_id':f'f{i}', 'field':'metric_series_64','region':'M','entity_ids':[str(100+i)],
              'payload':{'panel_id':f'M{i:02d}','rank':i,'service':str(100+i),'metric':'cpu'}} for i in range(1, 31)]
    pool={'facts':facts,'fact_inventory_hash':stable_hash(facts),'candidates':[str(100+i) for i in range(1,31)],
          'pool_coverage':{'public_membership':True}}
    before=deepcopy(pool)
    native={'ranks':[f'M{i:02d}' for i in range(30, 0, -1)],'excluded':{},'status':'ranked'}
    packet,audit=search_select(pool,'baro_native24_v1',24,native_selection=native)
    assert {f['fact_id'] for f in packet['facts']}=={f'f{i}' for i in range(7,31)}
    assert audit['fill_ids']==[] and audit['source_hash']==pool['fact_inventory_hash'] and pool==before
    native['ranks']=['M30']
    packet,audit=search_select(pool,'baro_native24_v1',24,native_selection=native)
    assert len(audit['fill_ids'])==23 and len(packet['facts'])==24
    with pytest.raises(ValueError):search_select(pool,'baro_native24_v1',24)


def test_moved_generic_helpers_keep_contracts():
    from unified_scripts.dataset_segmentation import connected_row_groups
    from RQs.RQ3.src.utils import components, chat_token_ids
    rows=[{'event':'','source':'a','start':i,'end':i+1} for i in range(3)]
    assert components(rows)==[rows]
    assert connected_row_groups([1,2,4],lambda a,b:abs(a-b)==1)==[[1,2],[4]]
    class Tokenizer:
        def apply_chat_template(self,*args,**kwargs):return {'input_ids':[[1,2,3]]}
    assert chat_token_ids(Tokenizer(),[])==[1,2,3]

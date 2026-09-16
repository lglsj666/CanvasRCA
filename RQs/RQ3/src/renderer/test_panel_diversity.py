"""Native panel-ranking endpoint, continuous novelty and public binding checks."""
from copy import deepcopy
import math
import pytest
from .kpi_select import diverse_panel_indices
from RQs.RQ3.src.exps import search_select, _atomic_fact, evidence_cards
from RQs.RQ3.src.tests import fixture_packet
from RQs.RQ3.src.main import load_config
from unified_scripts import stable_hash


@pytest.mark.parametrize('weight', [0., .25, .5, .75, 1.])
def test_soft_diversity_is_deterministic_and_preserves_values(weight):
    x = [float(i) for i in range(64)]; data = [x, [2*v+1 for v in x], [float(i%3) for i in range(64)]]
    before = deepcopy(data)
    a, steps = diverse_panel_indices(data, ['123']*3, ['a','b','c'], 2, weight)
    assert len(a) == len(set(a)) == len(steps) == 2 and data == before
    assert (a, steps) == diverse_panel_indices(data, ['123']*3, ['a','b','c'], 2, weight)
    assert a[0] == 0 and all(math.isfinite(s['priority']) for s in steps)
    assert a == ([0, 1] if weight == 1 else [0, 2])


@pytest.mark.parametrize('values,owner,similar', [([float(i) for i in range(64)], '123', True),
    ([float(-i) for i in range(64)], '123', False), ([float(i) for i in range(64)], '456', False),
    ([None]*57+list(range(7)), '123', False), ([None]*32+list(range(32)), '123', False)])
def test_similarity_never_invents_overlap_or_cross_owner_identity(values, owner, similar):
    _, steps = diverse_panel_indices([list(range(64)), values], ['123',owner], ['a','b'], 2, .75)
    assert (steps[1]['similarity'] > .99) == similar
    assert (steps[1]['witness'] == 'a') == similar


@pytest.mark.parametrize('a,b,expected', [(0.,0.,1.),(0.,1.,0.),(1.,2.,0.),(1e308,1e308,1.),(1e-320,2e-320,0.)])
def test_constant_and_extreme_values(a,b,expected):
    _, steps = diverse_panel_indices([[a]*64,[b]*64], ['123']*2, ['a','b'], 2, .75)
    assert steps[1]['similarity'] == expected


@pytest.mark.parametrize('bad', [True,False,None,'0.75',-.1,1.1,float('nan'),float('inf')])
def test_invalid_weight_fails(bad):
    with pytest.raises(ValueError, match='weight'):
        diverse_panel_indices([], [], [], 2, bad)


@pytest.mark.parametrize('bad', [True,'not-a-number','nan','inf',float('nan'),float('inf')])
def test_invalid_bin_fails(bad):
    with pytest.raises(ValueError, match='numeric'):
        diverse_panel_indices([[bad]*64], ['123'], ['a'], 2, .75)


def test_empty_and_invalid_binding():
    assert diverse_panel_indices([], [], [], 2, .75) == ([], [])
    with pytest.raises(ValueError): diverse_panel_indices([[1.]*64], [], ['a'], 2, .75)
    with pytest.raises(ValueError): diverse_panel_indices([[1.]*63], ['123'], ['a'], 2, .75)
    with pytest.raises(ValueError): diverse_panel_indices([], [], [], True, .75)


def test_canonical_numeric_strings_keep_values_and_nulls():
    data = [[None]+[float(i) for i in range(63)], [None]+[float(i*2) for i in range(63)]]
    strings = [[None if v is None else f'{v:.6e}' for v in values] for values in data]
    before = deepcopy(strings)
    assert diverse_panel_indices(data, ['123']*2, ['a','b'], 2, .75) == diverse_panel_indices(strings, ['123']*2, ['a','b'], 2, .75)
    assert strings == before


def test_public_dispatch_default_endpoint_and_real_change():
    p = fixture_packet(); p['facts'] = []; p['pool_coverage'] = {'public_membership':True}
    for i, values in enumerate([list(range(64)),list(range(64)),[float(i%3) for i in range(64)]]):
        payload = dict(panel_id=f'M{i+1:02d}', rank=i+1, service='100', metric=f'counter{i}', values=values)
        p['facts'].append(_atomic_fact('M','metric_series_64',payload,entities=('100',)))
    p['fact_inventory_hash'] = stable_hash(p['facts']); before = deepcopy(p)
    native, _ = search_select(p,'ranked_membership_v1',2)
    same, _ = search_select(p,'shape_diversity_v1',2,1.)
    new, audit = search_select(p,'shape_diversity_v1',2,.75)
    assert p == before and native == same and new != native
    assert audit['source_hash'] == p['fact_inventory_hash'] and len(audit['diversity_steps']) == 2
    assert new['candidates'] == native['candidates'] and all(f in p['facts'] for f in new['facts'])
    rev = deepcopy(p); rev['facts'].reverse(); rev['fact_inventory_hash'] = stable_hash(rev['facts'])
    assert search_select(rev,'shape_diversity_v1',2,.75)[0] == new
    with pytest.raises(ValueError): search_select(p,'ranked_membership_v1',2,.75)
    p['fact_inventory_hash'] = 'corrupt'
    with pytest.raises(ValueError, match='inventory'): search_select(p,'shape_diversity_v1',2,.75)


def test_topology_sort_tie_preserves_previously_defined_order():
    # Moved from core tests, unchanged assertions; renderer-owned ordering.
    from dataclasses import replace
    from itertools import product
    from .designs import _card_sort_key
    cards=evidence_cards(fixture_packet(),load_config());top=next(c for c in cards if c.region=='G')
    other=next(c for c in cards if c.region=='M');rank={e:i for i,e in enumerate(fixture_packet()['candidates'])};undefined=0
    for family,area,score in product(('entity_grouped','salience_first','topology_centered','modality_grouped'),(6,9,12),(0.,1.,3.)):
        a=replace(other,selection_score=score);before=(-1,-area,top.card_id);b=_card_sort_key(a,family,area,rank)
        now=_card_sort_key(top,family,area,rank)
        sorted([now,b])
        try:expected=before<b
        except TypeError:undefined+=1;assert now<b
        else:assert (now<b)==expected
    assert undefined>0

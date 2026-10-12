"""Sparse public-region sets must not require non-existent cards."""
from itertools import combinations
from types import SimpleNamespace
import pytest
from .card_families import metric_left_stack_tree,_checked_tree

SUBSETS=[r for n in range(1,5) for r in combinations('MRLG',n)]

def cards(regions):
    return [SimpleNamespace(card_id=f'EC{i+1:02d}',family='modality',regions=(r,)) for i,r in enumerate(regions)]

@pytest.mark.parametrize('regions',SUBSETS)
def test_all_present_region_subsets_exact_once(regions):
    items=cards(regions);tree=metric_left_stack_tree(items)
    assert _checked_tree(tree,[c.card_id for c in items])==tree
    assert metric_left_stack_tree(list(reversed(items)))==tree
    if len(regions)==1:assert tree=={'card':'EC01'}
    elif 'M' in regions:assert tree['axis']=='x' and tree['ratio']==.6 and tree['children'][0]=={'card':'EC01'}
    else:assert tree['axis']=='y'

def test_complete_tree_preserves_original_four_card_coordinates():
    assert metric_left_stack_tree(cards('MRLG'))=={
        'axis':'x','ratio':.6,'children':[{'card':'EC01'},
        {'axis':'y','ratio':1/3,'children':[{'card':'EC02'},
        {'axis':'y','ratio':.5,'children':[{'card':'EC03'},{'card':'EC04'}]}]}]}
    assert metric_left_stack_tree(cards('MG'))=={'axis':'x','ratio':.6,'children':[{'card':'EC01'},{'card':'EC02'}]}

def test_invalid_card_family_or_duplicate_fails_without_deleting():
    for rows in ([],cards('MM'),cards('X'),[SimpleNamespace(card_id='E',family='per_case',regions=('M','G'))],
                 [SimpleNamespace(card_id='same',family='modality',regions=(r,)) for r in 'MG']):
        with pytest.raises(ValueError):metric_left_stack_tree(rows)

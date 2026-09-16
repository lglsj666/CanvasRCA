"""Shared numeric/peer-summary contracts; no dataset or private labels."""
import math
from copy import deepcopy

import pytest

from vlmrca.peer_metrics import display_number, peer_shift_residuals


@pytest.mark.parametrize('value,expected', [('1.5k', 1500), ('-2M', -2e6), ('+3e-2G', 3e7),
    (0, 0), (True, None), ('missing', None), (None, None), ('NaN', None),
    ('inf', None), ('1e309', None), ('3 ms', None), ('1..2', None)])
def test_display_number(value, expected):
    assert display_number(value, None) == expected


def rows(after, *, key=('cpu', 'percent', 'node')):
    return [{'key': key, 'owner': str(i), 'before': 10, 'after': x, 'spread': 0}
            for i, x in enumerate(after)]


def test_unique_change_and_common_mode():
    raw = rows([30, 10, 10, 10]); saved = deepcopy(raw)
    result = peer_shift_residuals(raw)
    assert raw == saved and result[0]['residual'] == pytest.approx(.25, rel=1e-14)
    assert all(r['residual'] == 0 for r in result[1:])
    assert all(r['residual'] == 0 for r in peer_shift_residuals(rows([30] * 4)))


def test_duplicate_owner_not_an_independent_peer():
    raw = rows([30, 10]); raw += [deepcopy(raw[1])] * 20
    assert all(r['residual'] is None for r in peer_shift_residuals(raw))
    raw = rows([30, 10, 10]); baseline = peer_shift_residuals(raw)
    assert peer_shift_residuals(raw + [deepcopy(raw[2])] * 20)[0] == baseline[0]


def test_missing_negative_spread_and_semantic_group_separation():
    raw = rows([30, 10, 10, 10]); raw[1]['before'] = None
    raw[2]['spread'] = -1; raw[3]['key'] = ('cpu', 'percent', 'pod')
    assert all(r['residual'] is None for r in peer_shift_residuals(raw))


def test_scale_order_sign_and_overflow_stability():
    raw = rows([30, 10, 10, 10]); expected = peer_shift_residuals(raw)
    scaled = deepcopy(raw)
    for row in scaled:
        for k in ('before', 'after', 'spread'):
            row[k] *= 1e300
    for actual, wanted in zip(peer_shift_residuals(scaled), expected):
        assert actual['peer_count'] == wanted['peer_count']
        assert actual == pytest.approx(wanted, rel=1e-14, abs=1e-14)
    assert peer_shift_residuals(list(reversed(raw))) == list(reversed(expected))
    raw = rows([0, 0, 0]); raw[0].update(before=0, after=0)
    assert all(r['residual'] is None or math.isfinite(r['residual']) for r in peer_shift_residuals(raw))
    with pytest.raises(ValueError):
        peer_shift_residuals(raw, min_other_owners=1)

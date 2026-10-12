"""Numerical and finite-distribution checks; no RCA outcomes or model calls."""
import itertools
from fractions import Fraction
import numpy as np
import pytest
from .bounded_mean import BET_FRACTIONS, group_mean_test, holm_adjust


def test_zero_and_single_group_cannot_fake_independent_evidence():
    assert group_mean_test(np.zeros(87), np.ones(87))['p_value'] == 1
    assert group_mean_test([5], [5])['p_value'] == pytest.approx(1)


def test_extremes_symmetry_order_and_batch():
    sizes = np.ones(220, dtype=int)
    batch = np.stack([sizes, -sizes, np.zeros(220)])
    result = group_mean_test(batch, sizes)
    assert result['p_value'][0] < .001
    assert result['p_value'][0] == pytest.approx(result['p_value'][1])
    assert result['p_value'][2] == 1
    assert np.isfinite(result['log_e']).all()
    np.testing.assert_allclose(result['p_value'], group_mean_test(batch[:, ::-1], sizes[::-1])['p_value'])


def test_unequal_groups_keep_case_weighting():
    result = group_mean_test([1, -1, 0], [1, 5, 2])
    assert result['mean_difference'] == 0
    assert np.mean([1, -1/5, 0]) != 0  # The alternative group-weighted target differs.


def test_rational_null_oracle_allows_heterogeneous_nonzero_group_means():
    # Independent bounded groups with expectations +.6, -.4, -.2: only the
    # overall mean is zero. Exact rational expectation verifies the weak null.
    sizes = [1, 2, 1]
    probabilities = [Fraction(4, 5), Fraction(2, 5), Fraction(2, 5)]
    bets = [Fraction(2*j+1, 32) * sign for sign in (1, -1) for j in range(16)]
    expected_e = Fraction(0)
    for signs in itertools.product((-1, 1), repeat=3):
        values = [s*n for s, n in zip(signs, sizes)]
        products = []
        for bet in bets:
            product = Fraction(1)
            for value in values:product *= 1 + bet * Fraction(value, max(sizes))
            products.append(product)
        exact_e = sum(products) / len(products)
        floating = group_mean_test(values, sizes)
        assert np.exp(floating['log_e']) == pytest.approx(float(exact_e), abs=1e-13)
        weight = Fraction(1)
        for sign, prob in zip(signs, probabilities):weight *= prob if sign == 1 else 1-prob
        expected_e += weight * exact_e
    assert expected_e <= 1


@pytest.mark.parametrize('sums,sizes', [([], []), ([1], [0]), ([0], [1.5]), ([2], [1]), ([np.nan], [1]), ([0, 1], [1])])
def test_invalid_bounds_are_rejected(sums, sizes):
    with pytest.raises(ValueError):group_mean_test(sums, sizes)


def test_holm_preserves_family_and_order():
    np.testing.assert_allclose(holm_adjust([.01, .04, .03]), [.03, .06, .06])
    np.testing.assert_allclose(holm_adjust([[1, 0], [.03, .04]]), [[1, 0], [.06, .06]])
    with pytest.raises(ValueError):holm_adjust([.02, np.nan])


def test_predeclared_grid_is_not_fitted_to_outcomes():
    assert len(BET_FRACTIONS) == 16
    assert BET_FRACTIONS == tuple((2*j+1)/32 for j in range(16))

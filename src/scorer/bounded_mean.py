"""Fixed-sample paired mean inference, separate from RCA/QA score computation.

Under independence of registered event groups, this fixed mixture tests the
weak null sum(E[group_sum]) == 0 without a symmetry or common-mean assumption.
It is not an anytime-valid test and must not be tuned on diagnostic results.
See the RQ4.1 statistics amendment for the elementary expectation proof.
"""
from __future__ import annotations

import numpy as np


METHOD = 'fixed_bounded_group_mean_mixture_v1'
BET_FRACTIONS = tuple((2 * j + 1) / 32 for j in range(16))


def group_mean_test(group_sums, group_sizes):
    """Last axis contains group sums; each paired case score is in [-1, 1].

    Size weights remain inside group sums. Do NOT substitute group means.
    Fixed bets use a common scale, max(group_sizes), to preserve the original
    case-weighted estimand even with unequal sizes and heterogeneous means.
    Returns numpy arrays (scalars for a single comparison); no CI is produced.
    """
    sums = np.asarray(group_sums, dtype=np.float64)
    sizes = np.asarray(group_sizes, dtype=np.float64)
    if sizes.ndim != 1 or not len(sizes) or not np.all(np.isfinite(sizes)):
        raise ValueError('A nonempty finite group-size vector is required')
    if np.any(sizes < 1) or np.any(sizes != np.floor(sizes)):
        raise ValueError('Group sizes must be positive integers')
    if sums.ndim < 1 or sums.shape[-1] != len(sizes):
        raise ValueError('Last axis must match the registered groups')
    if not np.all(np.isfinite(sums)) or np.any(np.abs(sums) > sizes):
        raise ValueError('Group sums must respect their registered score bounds')
    bets = np.asarray(BET_FRACTIONS)
    bets = np.concatenate((bets, -bets)) / sizes.max()
    log_products = np.log1p(sums[..., None, :] * bets[:, None]).sum(axis=-1)
    maximum = log_products.max(axis=-1)
    log_e = maximum + np.log(np.exp(log_products - maximum[..., None]).mean(axis=-1))
    # 1/E is a valid fixed-sample p-value by Markov's inequality. Clamping an
    # underflow upward is conservative; returning an infinity is unnecessary.
    p = np.exp(np.maximum(-np.maximum(log_e, 0), np.log(np.finfo(float).tiny)))
    return {'p_value': p, 'log_e': log_e,
            'mean_difference': sums.sum(axis=-1) / sizes.sum()}


def holm_adjust(p_values):
    """One complete registered family on the last axis; no dropping tests."""
    p = np.asarray(p_values, dtype=np.float64)
    if p.ndim < 1 or not p.shape[-1] or not np.all(np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError('Finite p-values in [0, 1] required')
    order = np.argsort(p, axis=-1, kind='stable')
    ranked = np.take_along_axis(p, order, axis=-1)
    adjusted = np.minimum(1, np.maximum.accumulate(ranked * np.arange(p.shape[-1], 0, -1), axis=-1))
    return np.take_along_axis(adjusted, np.argsort(order, axis=-1), axis=-1)


def simulate_registered_stress(registration, seed, *, replicates=2000, family_size=1, progress=None):
    """Outcome-free reproduction of a supplied bounded-score stress design.

    This consumes only group memberships/counts and stress-law definitions,
    never model responses, historical rankings, accepted roots or QA answers.
    family_size power is a conservative Bonferroni screen, not simulated Holm
    joint power. The original nominal-level calibration alarm is unchanged.
    """
    if registration['rejection_threshold'] != .05 or registration['calibration_alarm_threshold'] != .07:
        raise ValueError('This revision preserves alpha=.05 and alarm=.07')
    if replicates != 2000 or family_size not in (2, 6):
        raise ValueError('Use the frozen replicate count and comparison family')
    sizes = np.array([len(v) for _, v in sorted(registration['groups'].items())], dtype=int)
    if not len(sizes) or np.any(sizes < 1):raise ValueError('Empty event groups')
    offsets = np.r_[0, np.cumsum(sizes)[:-1]]
    membership = np.repeat(np.arange(len(sizes)), sizes)
    shifts = np.asarray(registration['shifts'], dtype=float)
    if not np.array_equal(shifts, [0, .02, .03, .05]):raise ValueError('Registered shifts changed')
    cells = []
    rng = np.random.default_rng(seed)
    for spec in registration['cells']:
        law, zero, rho, scaling = spec
        if law not in ('symmetric', 'skew_positive', 'skew_negative') or zero not in (0., .75) or rho not in (0., .5, 1.):
            raise ValueError('Unknown registered stress law')
        if scaling not in ('constant', 'sqrt_n', 'inverse_sqrt_n'):raise ValueError('Unknown scaling')
        reject = np.zeros(len(shifts), dtype=int)
        family_screen = np.zeros(len(shifts), dtype=int)
        means = np.zeros(len(shifts))
        scale = np.ones(len(sizes)) if scaling == 'constant' else np.sqrt(sizes) if scaling == 'sqrt_n' else 1 / np.sqrt(sizes)
        scale /= scale.max()
        for start in range(0, replicates, 64):
            batch = min(64, replicates - start)
            def draw(n):
                x = np.where(rng.random((batch, n)) < (.5 if law == 'symmetric' else .2),
                             1. if law == 'symmetric' else .8, -1. if law == 'symmetric' else -.2)
                if law == 'skew_negative':x = -x
                if zero:x *= rng.random((batch, n)) >= zero
                return x
            a, b = np.sqrt(rho), np.sqrt(1-rho)
            values = (a * draw(len(sizes))[:, membership] + b * draw(int(sizes.sum()))) / (a+b)
            values *= scale[membership]
            for i, shift in enumerate(shifts):
                bounded = np.clip(values + shift, -1, 1)
                group_sums = np.add.reduceat(bounded, offsets, axis=1)
                p = group_mean_test(group_sums, sizes)['p_value']
                reject[i] += np.count_nonzero(p <= .05)
                family_screen[i] += np.count_nonzero(p <= .05 / family_size)
                means[i] += bounded.mean(axis=1).sum()
        cell = {'law': law, 'zero_inflation': zero, 'shared_variance_fraction': rho, 'scale': scaling,
                'null_rejection_rate': float(reject[0] / replicates),
                'power_by_shift': {str(s): float(reject[i] / replicates) for i, s in enumerate(shifts) if i},
                'bonferroni_screen_power_by_shift': {str(s): float(family_screen[i] / replicates) for i, s in enumerate(shifts) if i},
                'realized_mean_by_shift': {str(s): float(means[i] / replicates) for i, s in enumerate(shifts)}}
        cells.append(cell)
        if progress is not None:progress(len(cells), len(registration['cells']))
    peak = max(c['null_rejection_rate'] for c in cells)
    return {'status': 'passed' if peak <= .07 else 'uncalibrated', 'method': METHOD, 'seed': seed,
            'cases': int(sizes.sum()), 'event_groups': len(sizes), 'group_sizes': sizes.tolist(),
            'replicates': replicates, 'cells': cells, 'max_null_rejection_rate': peak,
            'family_size': family_size, 'alpha': .05, 'alarm': .07, 'observed_results_read': False,
            'assumption': 'independent fixed event groups; within-group dependence arbitrary',
            'power_note': 'Passing calibration does not establish useful power at shifts .02/.03/.05',
            'llm_calls': 0, 'confidence_intervals_reported': False}

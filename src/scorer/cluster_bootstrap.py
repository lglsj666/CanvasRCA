"""Prospective, fixed-sample event-cluster bootstrap-t inference.

This is an asymptotic bootstrap, not a distribution-free finite-sample test.
RCA/QA scores, groups and registered families remain the caller's responsibility.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import binom

METHOD = 'paired_cluster_ratio_bootstrap_t_equal_tails_v1'


class ClusterBootstrap:
    """Bootstrap complete (group sum, group size) pairs using fixed draw counts."""
    def __init__(self, sizes, counts):
        self.sizes = np.asarray(sizes, dtype=float)
        self.counts = np.asarray(counts, dtype=float)
        n = self.sizes
        if n.ndim != 1 or len(n) < 2 or not np.isfinite(n).all() or np.any(n < 1) or np.any(n != np.floor(n)):
            raise ValueError('At least two positive integer group sizes required')
        w = self.counts
        if w.ndim != 2 or w.shape[1] != len(n) or len(w) < 1 or not np.isfinite(w).all():
            raise ValueError('Bootstrap count matrix has invalid dimensions')
        if np.any(w < 0) or np.any(w != np.floor(w)) or np.any(w.sum(axis=1) != len(n)):
            raise ValueError('Each draw must resample exactly G intact groups')
        self.total = n.sum()
        self.factor = len(n)/(len(n)-1)
        self.bootstrap_n = w @ n
        self.bootstrap_n2 = w @ (n*n)

    @classmethod
    def from_seed(cls, sizes, *, draws=4999, seed):
        if draws < 1:raise ValueError('Positive bootstrap count required')
        g = len(sizes)
        rng = np.random.default_rng(seed)
        return cls(sizes, rng.multinomial(g, np.full(g, 1/g), size=draws))

    def test(self, group_sums):
        """Compute centered equal-tail bootstrap-t p-values along the last axis.

        Resample sums AND sizes together. Recompute the ratio mean and its
        cluster sandwich standard error in every draw. Do not clip centered
        bootstrap residuals or discard draws with zero bootstrap variance.
        """
        data = np.asarray(group_sums, dtype=float)
        if data.ndim < 1 or data.shape[-1] != len(self.sizes) or not np.isfinite(data).all():
            raise ValueError('Finite sums matching the registered groups required')
        if np.any(np.abs(data) > self.sizes):raise ValueError('Paired-score bounds exceeded')
        shape = data.shape[:-1]
        sums = data.reshape(-1, len(self.sizes)).T
        means = sums.sum(axis=0)/self.total
        residuals = sums-self.sizes[:, None]*means
        denominator2 = self.factor*np.sum(residuals**2, axis=0)
        observed = np.divide(sums.sum(axis=0), np.sqrt(denominator2),
                             out=np.zeros_like(means), where=denominator2 > 0)
        w = self.counts
        bs = w @ residuals
        bm = bs/self.bootstrap_n[:, None]
        rr = w @ (residuals**2)
        rn = w @ (residuals*self.sizes[:, None])
        nn = self.bootstrap_n2[:, None]
        variance = rr-2*bm*rn+bm**2*nn
        tolerance = 1e-12*np.maximum(rr+2*np.abs(bm*rn)+bm**2*nn, np.finfo(float).tiny)
        if np.any(variance < -tolerance):raise ArithmeticError('Negative bootstrap variance beyond roundoff')
        variance = np.where(variance <= tolerance, 0, variance)
        bt = np.divide(bs, np.sqrt(self.factor*variance), out=np.zeros_like(bs), where=variance > 0)
        zero = variance == 0
        magnitude = w @ np.abs(residuals)
        nonzero_sum = np.abs(bs) > 1e-12*np.maximum(magnitude, np.finfo(float).tiny)
        bt = np.where(zero & nonzero_sum, np.copysign(np.inf, bs), bt)
        lower = (1+np.sum(bt <= observed[None, :]+1e-12, axis=0))/(len(w)+1)
        upper = (1+np.sum(bt >= observed[None, :]-1e-12, axis=0))/(len(w)+1)
        p = np.minimum(1, 2*np.minimum(lower, upper))
        # A degenerate empirical sample cannot supply a bootstrap variance;
        # conservatively decline significance rather than emit a fake p=0.
        p = np.where(denominator2 == 0, 1, p)
        return {'p_value': p.reshape(shape), 'mean_difference': means.reshape(shape),
                't_observed': observed.reshape(shape),
                'degenerate_sample': (denominator2 == 0).reshape(shape),
                'degenerate_draw_fraction': zero.mean(axis=0).reshape(shape)}


def binomial_oracle_power(n, delta, alpha=.05):
    """Exact one-sided NP oracle for D in {-1,+1}, p0=.5, p1=(1+delta)/2.

    This is a hard example, NOT a power bound for every telemetry population.
    It gives the most favorable test the effect direction and both laws in
    advance. Any level-alpha test has no greater power for this simple pair.
    """
    if int(n) != n or n < 1 or not 0 < delta < 1 or not 0 < alpha < 1:
        raise ValueError('Invalid binomial power inputs')
    k = int(binom.isf(alpha, n, .5))
    gamma = (alpha-binom.sf(k, n, .5))/binom.pmf(k, n, .5)
    if not -1e-10 <= gamma <= 1+1e-10:raise ArithmeticError('Oracle boundary randomization')
    gamma = float(np.clip(gamma, 0, 1))
    p1 = (1+delta)/2
    return {'n': n, 'delta': delta, 'alpha': alpha, 'boundary': k,
            'boundary_randomization': gamma,
            'null_rejection': float(binom.sf(k, n, .5)+gamma*binom.pmf(k, n, .5)),
            'oracle_power': float(binom.sf(k, n, p1)+gamma*binom.pmf(k, n, p1))}


def simulate_bootstrap_stress(registration, *, seed, bootstrap_seed, family_size, progress=None):
    """Same 54 registered stress laws; independent new simulation bank.

    Common bootstrap indices are fixed independently of simulated outcomes.
    All cases in a group stay together. Two banks vary both random streams.
    """
    if registration['rejection_threshold'] != .05 or registration['calibration_alarm_threshold'] != .07:
        raise ValueError('Keep original alpha and calibration alarm')
    if registration['shifts'] != [0., .02, .03, .05]:raise ValueError('Keep original shifts')
    if family_size not in (2, 6):raise ValueError('Registered QA or RCA family required')
    sizes = np.array([len(v) for _, v in sorted(registration['groups'].items())])
    membership = np.repeat(np.arange(len(sizes)), sizes)
    offsets = np.r_[0, np.cumsum(sizes)[:-1]]
    engine = ClusterBootstrap.from_seed(sizes, draws=4999, seed=bootstrap_seed)
    rng = np.random.default_rng(seed)
    rows = []
    shifts = np.array(registration['shifts'])
    for law, zero, rho, scaling in registration['cells']:
        if law not in ('symmetric','skew_positive','skew_negative') or zero not in (0., .75) or rho not in (0., .5, 1.):
            raise ValueError('Unknown stress law')
        if scaling not in ('constant','sqrt_n','inverse_sqrt_n'):raise ValueError('Unknown stress scale')
        scale = np.ones(len(sizes)) if scaling == 'constant' else np.sqrt(sizes) if scaling == 'sqrt_n' else 1/np.sqrt(sizes)
        scale /= scale.max()
        rejection = np.zeros(4, int); family = np.zeros(4, int); means = np.zeros(4)
        degenerate = np.zeros(4, int); degenerate_draws = np.zeros(4)
        for start in range(0, 2000, 64):
            batch = min(64, 2000-start)
            def draw(n):
                v = np.where(rng.random((batch, n)) < (.5 if law == 'symmetric' else .2),
                             1. if law == 'symmetric' else .8, -1. if law == 'symmetric' else -.2)
                if law == 'skew_negative':v = -v
                if zero:v *= rng.random((batch, n)) >= zero
                return v
            a,b = np.sqrt(rho),np.sqrt(1-rho)
            values = (a*draw(len(sizes))[:, membership]+b*draw(int(sizes.sum())))/(a+b)
            values *= scale[membership]
            bounded = np.clip(values[:, None, :]+shifts[None, :, None], -1, 1)
            group_sums = np.add.reduceat(bounded, offsets, axis=-1)
            result = engine.test(group_sums)
            p = result['p_value']
            rejection += np.sum(p <= .05, axis=0)
            family += np.sum(p <= .05/family_size, axis=0)
            means += bounded.mean(axis=-1).sum(axis=0)
            degenerate += result['degenerate_sample'].sum(axis=0)
            degenerate_draws += result['degenerate_draw_fraction'].sum(axis=0)
        rows.append({'law':law,'zero_inflation':zero,'shared_variance_fraction':rho,'scale':scaling,
            'null_rejection_rate':float(rejection[0]/2000),
            'power_by_nominal_shift':{str(s):float(rejection[i]/2000) for i,s in enumerate(shifts) if i},
            'bonferroni_screen_power_by_nominal_shift':{str(s):float(family[i]/2000) for i,s in enumerate(shifts) if i},
            'realized_mean_by_nominal_shift':{str(s):float(means[i]/2000) for i,s in enumerate(shifts)},
            'degenerate_samples':degenerate.tolist(),'degenerate_draw_fraction':(degenerate_draws/2000).tolist()})
        if progress is not None:progress(len(rows),len(registration['cells']))
    peak = max(r['null_rejection_rate'] for r in rows)
    return {'method':METHOD,'status':'passed' if peak <= .07 else 'uncalibrated','cases':int(sizes.sum()),
        'event_groups':len(sizes),'seed':seed,'bootstrap_seed':bootstrap_seed,'replicates':2000,'bootstrap_draws':4999,
        'max_null_rejection_rate':peak,'cells':rows,'alpha':.05,'alarm':.07,'family_size':family_size,
        'no_finite_sample_distribution_free_guarantee':True,'observed_results_read':False,'llm_calls':0}

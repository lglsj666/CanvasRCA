import numpy as np
import pytest
from .cluster_bootstrap import ClusterBootstrap, binomial_oracle_power


def test_fast_statistic_matches_direct_whole_group_resampling():
    sizes=np.array([1,3,2,1]);sums=np.array([.8,-.3,-1.,.4])
    engine=ClusterBootstrap.from_seed(sizes,draws=99,seed=112)
    n=sizes.sum();g=len(sizes);mean=sums.sum()/n;res=sums-sizes*mean
    observed=sums.sum()/np.sqrt(g/(g-1)*np.sum(res**2))
    draws=[]
    for row in engine.counts:
        indices=np.repeat(np.arange(g),row.astype(int));r=res[indices];w=sizes[indices]
        total=r.sum();mu=total/w.sum();var=g/(g-1)*np.sum((r-w*mu)**2)
        draws.append(total/np.sqrt(var) if var>1e-25 else np.sign(total)*np.inf if abs(total)>1e-12 else 0)
    draws=np.array(draws)
    expected=min(1,2*min((1+sum(draws<=observed+1e-12))/100,(1+sum(draws>=observed-1e-12))/100))
    actual=engine.test(sums)
    assert actual['t_observed']==pytest.approx(observed)
    assert actual['p_value']==expected
    assert actual['mean_difference']==mean


def test_batch_symmetry_and_group_permutation_with_matched_draws():
    sizes=np.array([1,2,1,3]);sums=np.array([.9,-.5,.1,1.])
    a=ClusterBootstrap.from_seed(sizes,draws=199,seed=33)
    values=np.stack([sums,-sums,np.zeros(4)])
    result=a.test(values);order=[2,0,3,1]
    b=ClusterBootstrap(sizes[order],a.counts[:,order])
    np.testing.assert_allclose(result['p_value'],b.test(values[:,order])['p_value'])
    assert result['p_value'][0]==result['p_value'][1]
    assert result['p_value'][2]==1


def test_degenerate_observations_decline_significance():
    engine=ClusterBootstrap.from_seed([1]*20,draws=99,seed=7)
    r=engine.test(np.stack([np.zeros(20),np.ones(20)]))
    assert np.array_equal(r['p_value'],[1,1])
    assert r['degenerate_sample'].all()


def test_clear_nonconstant_signal_and_determinism():
    a=ClusterBootstrap.from_seed([1]*100,draws=999,seed=24)
    b=ClusterBootstrap.from_seed([1]*100,draws=999,seed=24)
    values=np.linspace(.01,.9,100)
    assert a.test(values)['p_value']<=.01
    assert a.test(values)['p_value']==b.test(values)['p_value']


@pytest.mark.parametrize('sizes,counts',[([1],[[1]]),([1,0],[[1,1]]),([1,1],[[.5,1.5]]),([1,1],[[1,0]])])
def test_invalid_resampling_fails(sizes,counts):
    with pytest.raises(ValueError):ClusterBootstrap(sizes,counts)


def test_unknown_or_out_of_bounds_scores_fail():
    engine=ClusterBootstrap.from_seed([1,2],draws=19,seed=8)
    for sums in ([1,np.nan],[1,3],[1]):
        with pytest.raises(ValueError):engine.test(sums)


def test_exact_binomial_oracle_size_and_known_single_observation():
    a=binomial_oracle_power(1,.03)
    assert a['null_rejection']==pytest.approx(.05)
    assert a['oracle_power']==pytest.approx(.0515)
    assert binomial_oracle_power(87,.03)['oracle_power']<.15
    assert binomial_oracle_power(10000,.03)['oracle_power']>.80

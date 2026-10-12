"""CPU checks of the SEARCH29 public-only prototype, no models or labels."""
from copy import deepcopy
import pytest
from RQs.RQ3.scripts.probe_range_supplement import range_score, propose
from RQs.RQ3.src.utils import stable_hash


@pytest.mark.parametrize('values,score', [([0.]*64,0.),([5.]*64,0.),
    ([None]*64,0.),([None]*57+[1.,2.,3.,4.,5.,6.,7.],0.),
    ([1.]*32+[3.]*32,.5),([-3.]*32+[-1.]*32,.5),([-1.]*32+[1.]*32,1.)])
def test_finite_range(values,score):
    assert range_score(values)==pytest.approx(score)
    before=deepcopy(values)
    assert range_score([None if v is None else v*1000 for v in values])==pytest.approx(score)
    assert values==before


@pytest.mark.parametrize('values', [[0.]*63,[True]*64,[float('nan')]*64,
    [float('inf')]*64,['broken']*64,['NaN']*64,['1e309']*64])
def test_invalid(values):
    with pytest.raises(ValueError): range_score(values)


def test_serialized_numbers_and_extreme_finite_range():
    assert range_score(['1e-2']*32+['3e-2']*32)==pytest.approx(.5)
    assert range_score([-1e308]*32+[1e308]*32)==pytest.approx(1.)
    assert range_score(['1']*64)==0.


def test_public_binding_retention_and_coverage_priority():
    def fact(i,owner,values):
        return {'fact_id':str(i),'field':'metric_series_64','region':'M',
                'entity_ids':[owner],'payload':{'service':owner,'metric':'cpu_usage',
                  'rank':i,'values':values}}
    a=fact(1,'123',[1.]*32+[2.]*32); b=fact(2,'123',[0.]*32+[100.]*32)
    c=fact(3,'124',[1.]*32+[1.1]*32)
    make=lambda facts:{'facts':facts,'fact_inventory_hash':stable_hash(facts),
                       'candidates':['123','124'],'opaque_incident_id':'INC-CPU'}
    pool=make([a,b,c]); anchor=make([a]); saved=deepcopy((pool,anchor))
    result,audit=propose(pool,anchor,1)
    assert [r['fact_id'] for r in result['facts']]==['1','3']
    assert audit[0]['owner']=='124' and (pool,anchor)==saved
    assert propose(make([c,a,b]),anchor,1)==(result,audit)
    result,audit=propose(pool,anchor,12)
    assert len(audit)==2 and len({(a['owner'],a['family']) for a in audit})==2
    with pytest.raises(ValueError): propose(pool,anchor,True)
    bad=deepcopy(pool);bad['facts'][0]['payload']['values'][0]=22
    with pytest.raises(ValueError,match='unbound'):propose(bad,anchor)

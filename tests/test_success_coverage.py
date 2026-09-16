"""Shared shrinking-cohort accounting: synthetic outcomes, no models or labels."""
from copy import deepcopy
import pytest
from vlmrca.run_state import SuccessCoverageRegister, write_json, sha_file


def setup(tmp_path):
    contract={'models':['a','b'],'cases':['c1','c2','c3','ref'],
              'levels':[1,3,5],'threshold_cases':['c1','c2','c3'],'threshold_count':2}
    return SuccessCoverageRegister(tmp_path/'study',contract,tmp_path),contract


def rows(tmp_path, round_id, model, results):
    values=[]
    for case,rank in results.items():
        path=tmp_path/f'{round_id}_{model}_{case}.json'
        write_json(path,{'case':case,'model':model,'rank':rank})
        values.append({'case':case,'hits':{str(k):0<rank<=k for k in (1,3,5)},
                       'artifacts':{path.name:sha_file(path)}})
    return values


def test_model_specific_thresholds_retirement_and_resume(tmp_path):
    reg,c=setup(tmp_path); method={'id':'first','request_contract':'frozen'}
    first=reg.register(method)
    assert first['cohorts']=={'a':sorted(c['cases']),'b':sorted(c['cases'])}
    a=rows(tmp_path,first['id'],'a',{'c1':1,'c2':1,'c3':4,'ref':1})
    reg.commit(first['id'],'a',a)
    state=reg.state()
    assert state['models']['a']['level']==5 and state['models']['a']['complete']
    assert state['models']['b']['level']==1 and len(state['models']['b']['eligible'])==4
    assert not state['complete']
    with pytest.raises(ValueError,match='finish'):reg.register({'id':'second'})
    again=SuccessCoverageRegister(tmp_path/'study',c,tmp_path)
    assert again.register(method)==first
    assert again.commit(first['id'],'a',a)==reg.commit(first['id'],'a',a)
    reg.commit(first['id'],'b',rows(tmp_path,first['id'],'b',{'c1':1,'c2':0,'c3':3,'ref':1}))
    second=reg.register({'id':'second'})
    assert second['cohorts']=={'a':[],'b':['c2','c3']}
    reg.commit(second['id'],'a',[])
    reg.commit(second['id'],'b',rows(tmp_path,second['id'],'b',{'c2':1,'c3':0}))
    state=reg.state()
    assert state['complete']
    assert state['models']['b']['success_methods']['c3']['3']==['first']
    assert state['models']['b']['success_methods']['c3']['1']==[]
    with pytest.raises(ValueError,match='already complete'):reg.register({'id':'third'})


def test_reject_partial_duplicate_retired_changed_and_nonmonotone(tmp_path):
    reg,c=setup(tmp_path)
    with pytest.raises(ValueError,match='complete population'):
        reg.register({'id':'first'}, {'a':['c1'],'b':['c1']})
    first=reg.register({'id':'first'})
    values=rows(tmp_path,first['id'],'a',{i:1 if i=='c1' else 0 for i in c['cases']})
    for invalid in (values[:-1],values+[values[0]]):
        with pytest.raises(ValueError,match='incomplete or duplicate'):reg.commit(first['id'],'a',invalid)
    changed=deepcopy(values);changed[0]['hits']={'1':True,'3':False,'5':True}
    with pytest.raises(ValueError,match='monotone'):reg.commit(first['id'],'a',changed)
    changed=deepcopy(values);changed[0]['artifacts']={'../outside':'wrong'}
    with pytest.raises(ValueError,match='source changed'):reg.commit(first['id'],'a',changed)
    reg.commit(first['id'],'a',values)
    reg.commit(first['id'],'b',rows(tmp_path,first['id'],'b',{i:0 for i in c['cases']}))
    with pytest.raises(ValueError,match='retired'):
        reg.register({'id':'second'},{'a':['c1'],'b':['c2']})
    second=reg.register({'id':'second'},{'a':['c2'],'b':['c2']})
    assert second['cohorts']['a']==['c2']
    altered={**c,'threshold_count':1}
    with pytest.raises(ValueError,match='immutable'):
        SuccessCoverageRegister(tmp_path/'study',altered,tmp_path)


def test_recovered_call_replaces_status_not_attempt_history(tmp_path):
    from vlmrca.run_state import DurableCallRegister
    ledger=DurableCallRegister(tmp_path/'calls.sqlite',None,scope='one')
    first,_=ledger.begin('a','same','solver')
    ledger.finish(first,{'error':'network'},'infrastructure_failure')
    assert ledger.latest_states()=={'a':'infrastructure_failure'}
    retry,_=ledger.begin('a','same','solver',retry=True)
    ledger.finish(retry,{'response':'immutable'})
    assert ledger.latest_states()=={'a':'complete'}
    assert ledger.summary()=={'infrastructure_failure':1,'complete':1}
    assert DurableCallRegister(tmp_path/'calls.sqlite',None,scope='two').latest_states()=={}


def grouped_setup(tmp_path, sizes=(5,5,5)):
    groups={f'd{d}':[f'd{d}c{i}' for i in range(n)] for d,n in enumerate(sizes)}
    cases=[i for ids in groups.values() for i in ids]
    contract={'models':['a','b'],'cases':cases,'levels':[1,3,5],
              'threshold_cases':cases,'threshold_count':1}
    return SuccessCoverageRegister(tmp_path/'study',contract,tmp_path),contract,groups


def finish_grouped_round(tmp_path, reg, groups, counts):
    r=reg.register({'id':'first'})
    for model,limits in counts.items():
        values={case:1 if i<limits[d] else 2 for d,ids in enumerate(groups.values()) for i,case in enumerate(ids)}
        reg.commit(r['id'],model,rows(tmp_path,r['id'],model,values))
    return r


def test_ac1_group_completion_stops_with_unsolved_cases_and_no_ac5_stage(tmp_path):
    reg,contract,groups=grouped_setup(tmp_path)
    finish_grouped_round(tmp_path,reg,groups,{'a':[4,4,4],'b':[5,5,3]})
    legacy=reg.state()
    assert legacy['complete']  # Old AC@5 success is NOT the successor gate.
    before={str(p.relative_to(reg.root)):p.read_bytes() for p in reg.root.rglob('*.json')}
    policy=reg.adopt_top1_completion(groups)
    state=reg.state()
    assert state['completion_policy_hash']==policy['hash']
    assert not state['complete']
    a,b=state['models']['a'],state['models']['b']
    assert a['level']==b['level']==1
    assert a['complete'] and a['eligible']==[] and len(a['unresolved'])==3
    assert len(a['retired'])==12 and not set(a['retired'])&set(a['unresolved'])
    assert not b['complete'] and len(b['eligible'])==2  # 13/15 pooled is insufficient.
    assert b['group_coverage']['d2']=={'successes':3,'cases':5,'required':4,'complete':False}
    for m in contract['models']:
        assert state['models'][m]['success_methods']==legacy['models'][m]['success_methods']
    for name,data in before.items():
        if name!='state.json':assert (reg.root/name).read_bytes()==data
    with pytest.raises(ValueError,match='retired'):
        reg.register({'id':'illegal'}, {'a':[a['unresolved'][0]],'b':b['eligible']})
    r=reg.register({'id':'second'})
    assert r['completion_policy_hash']==policy['hash'] and r['levels']=={'a':1,'b':1}
    assert r['cohorts']=={'a':[],'b':['d2c3','d2c4']}
    reg.commit(r['id'],'a',[])
    assert not reg.state()['complete']
    reg.commit(r['id'],'b',rows(tmp_path,r['id'],'b',{'d2c3':1,'d2c4':2}))
    final=reg.state()
    assert final['complete'] and len(final['models']['b']['unresolved'])==1
    assert final['models']['b']['success_methods']['d2c4']['1']==[]
    assert final['models']['b']['success_methods']['d2c4']['5']==['first','second']
    with pytest.raises(ValueError,match='already complete'):reg.register({'id':'third'})
    resumed=SuccessCoverageRegister(reg.root,contract,tmp_path)
    assert resumed.state()==final
    assert resumed.adopt_top1_completion(groups)==policy


@pytest.mark.parametrize('size,below,required',[(90,71,72),(100,79,80),(7,5,6)])
def test_group_threshold_uses_integer_ceiling(tmp_path,size,below,required):
    reg,contract,groups=grouped_setup(tmp_path,(size,))
    finish_grouped_round(tmp_path,reg,groups,{'a':[below],'b':[required]})
    reg.adopt_top1_completion(groups)
    state=reg.state()
    assert state['models']['a']['group_coverage']['d0']['required']==required
    assert not state['models']['a']['complete'] and state['models']['b']['complete']


def test_migration_rejects_pending_and_modified_source(tmp_path):
    reg,c,groups=grouped_setup(tmp_path)
    r=reg.register({'id':'first'})
    with pytest.raises(ValueError,match='pending'):reg.adopt_top1_completion(groups)
    for m in c['models']:reg.commit(r['id'],m,rows(tmp_path,r['id'],m,{i:0 for i in c['cases']}))
    (tmp_path/'round_0001_a_d0c0.json').write_text('corrupt')
    with pytest.raises(ValueError,match='source changed'):reg.adopt_top1_completion(groups)
    assert not (reg.root/'top1_completion_v2.json').exists()


@pytest.mark.parametrize('change',['missing','duplicate','empty','fraction','bool'])
def test_migration_rejects_invalid_group_partition(tmp_path,change):
    reg,c,groups=grouped_setup(tmp_path)
    n,d=4,5
    if change=='missing':groups.pop('d0')
    if change=='duplicate':groups['d1'].append(groups['d0'][0])
    if change=='empty':groups['empty']=[]
    if change=='fraction':n=6
    if change=='bool':n=True
    with pytest.raises(ValueError):reg.adopt_top1_completion(groups,n,d)


def test_policy_is_immutable_and_old_history_remains_integrity_checked(tmp_path):
    reg,c,groups=grouped_setup(tmp_path)
    finish_grouped_round(tmp_path,reg,groups,{'a':[1,1,1],'b':[1,1,1]})
    reg.adopt_top1_completion(groups)
    with pytest.raises(ValueError,match='immutable'):reg.adopt_top1_completion(groups,3,5)
    path=reg.root/'round_0001/a.json';value=__import__('json').loads(path.read_text())
    value['rows'][0]['hits']['1']=False
    from unified_scripts import stable_hash
    value['hash']=stable_hash({k:v for k,v in value.items() if k!='hash'})
    write_json(path,value)
    with pytest.raises(ValueError,match='predecessor history'):reg.state()


def test_new_round_requires_policy_and_migration_recovers_stale_state_file(tmp_path):
    reg,c,groups=grouped_setup(tmp_path)
    finish_grouped_round(tmp_path,reg,groups,{'a':[1,1,1],'b':[1,1,1]})
    policy=reg.adopt_top1_completion(groups)
    expected=reg.state()
    write_json(reg.root/'state.json',{'stale':True})
    assert reg.adopt_top1_completion(groups)==policy
    assert __import__('json').loads((reg.root/'state.json').read_text())==expected
    r=reg.register({'id':'second'})
    path=reg.root/'top1_completion_v2.json';saved=path.read_bytes();path.unlink()
    with pytest.raises(ValueError,match='policy missing'):reg.state()
    path.write_bytes(saved)
    from unified_scripts import stable_hash
    r.pop('completion_policy_hash');r['hash']=stable_hash({k:v for k,v in r.items() if k!='hash'})
    write_json(reg.root/r['id']/'registration.json',r)
    with pytest.raises(ValueError,match='active completion policy'):reg.state()

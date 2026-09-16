"""Existing state/cohort tests moved unchanged except qualified imports."""
import pytest
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.utils import stable_hash,write_json

def test_gpu_lease_blocks_double_start_and_releases(monkeypatch,tmp_path):
    import fcntl
    import os
    from RQs.RQ3.src import utils
    monkeypatch.setattr(utils,'ROOT',tmp_path)
    @utils.owned_gpu_process
    def enter(*,_gpu_lease_fd):return os.fstat(_gpu_lease_fd).st_ino
    inode=enter();path=tmp_path/'RQs/RQ3/results/gpu_owner.lock'
    with path.open('a+') as other:
        fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):enter()
    assert enter()==inode


def test_phase_recovery_only_retries_interrupted_same_keys(monkeypatch,tmp_path):
    from RQs.RQ3.src import utils
    monkeypatch.setattr(utils,'ROOT',tmp_path)
    cfg=load_config();root=tmp_path/'RQs/RQ3/results/formal';root.mkdir(parents=True)
    ledger=utils.CallLedger(root.parent/'calls.sqlite',scope=root.name)
    ledger.begin('interrupted','request-a','composer')
    done,_=ledger.begin('done','request-b','composer');ledger.finish(done,{'actual':'complete'})
    spec={'entries':[{'task':{'call_key':key}} for key in ('interrupted','done')]};spec['spec_hash']=stable_hash(spec)
    recovered,audit=utils.reconcile_phase_calls(cfg,spec,root)
    assert recovered['reconciled_retry_keys']==['interrupted']
    assert recovered['entries']==spec['entries'] and len(audit['interrupted_spent_calls'])==1
    assert ledger.summary()=={'complete':1,'interrupted':1}
    again,_=utils.reconcile_phase_calls(cfg,spec,root);assert again==recovered
    failed,_=ledger.begin('bad','request-c','solver');ledger.finish(failed,{'error':'persistent'},'infrastructure_failure')
    bad={'entries':[{'task':{'call_key':'bad'}}]};bad['spec_hash']=stable_hash(bad)
    with pytest.raises(RuntimeError,match='inspect before retry'):utils.reconcile_phase_calls(cfg,bad,root)


def test_attention_archive_lossless_single_probe_and_immutable(tmp_path):
    from RQs.RQ3.src.utils import archive_response_attention,archive_derived_attention,read_json,write_json,sha_file
    from unified_scripts import canonical_json
    probe={'request_id':'actual-request','weights':[.0001234567891234,.9998765432108766]*1000,
           'generation_target_attention':{'status':'collected','values':[0.,1e-30,12345678901234567]}}
    original={'attention_probe':probe,'finish_reason':'stop','choices':[{'content':'unchanged response'}]}
    raw,files=archive_response_attention(original,tmp_path,'call')
    ref=raw['attention_probe'];assert original['attention_probe'] is probe and raw['choices']==original['choices']
    path=tmp_path/ref['artifact_path'];assert read_json(path)==probe and sha_file(path)==ref['sha256']
    assert len(canonical_json(raw))<len(canonical_json(original))/4
    transient=path.with_suffix('');write_json(transient,probe)
    derived=path.parent/'prefill_text.json';write_json(derived,{'complete_weights':probe['weights']})
    result=archive_derived_attention([transient,derived])
    assert result[0]==path and not transient.exists() and read_json(result[1])['complete_weights']==probe['weights']
    assert sha_file(path)==ref['sha256'] and files==[path]
    with pytest.raises(ValueError,match='changed'):archive_response_attention({'attention_probe':{'different':1}},tmp_path,'call')


def test_callable_fingerprint_ignores_line_moves_but_not_logic():
    import types
    from RQs.RQ3.src.utils import callable_fingerprint
    def f(x):return x+3
    moved=types.FunctionType(f.__code__.replace(co_firstlineno=90000,co_filename='relocated.py'),f.__globals__)
    assert callable_fingerprint(f)==callable_fingerprint(moved)
    changed=types.FunctionType(f.__code__.replace(co_consts=(None,4)),f.__globals__)
    assert callable_fingerprint(f)!=callable_fingerprint(changed)


def test_search_cohort_offset_preserves_prefix_and_distinct_training_groups():
    from RQs.RQ3.src.main import search_cohort_rows
    rows=[{'dataset':d,'opaque_incident_id':f'{d}-{i}','leakage_group':f'{d}-{i//2}',
           'source':str(i%3)} for d in ('aiops2022','aiops2025') for i in range(14)]
    def pick(n,offset=0):return search_cohort_rows({'search':{'cases_per_dataset':n,'case_offset':offset}}, {'train':rows})
    first=pick(2);next_=pick(3,2);whole=pick(5)
    assert {r['opaque_incident_id'] for r in whole}=={r['opaque_incident_id'] for r in first+next_}
    assert not {r['leakage_group'] for r in first}&{r['leakage_group'] for r in next_}
    assert next_==search_cohort_rows({'search':{'cases_per_dataset':3,'case_offset':2}}, {'train':list(reversed(rows))})
    assert len(next_)==6 and len({r['leakage_group'] for r in next_})==6
    for n,offset in [(0,0),(1,-1),(True,0),(1,0.5),(8,0),(2,6)]:
        with pytest.raises(ValueError):pick(n,offset)

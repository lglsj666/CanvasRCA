"""RQ3 AC@1-only configuration and migration routing; no model calls."""
from types import SimpleNamespace

import pytest

from RQs.RQ3.src import utils
from RQs.RQ3.src.main import load_config, manage_tournament


def configs():
    root=utils.ROOT/'RQs/RQ3/configs'
    return load_config(root/'tournament_v1.yaml'),load_config(root/'tournament_ac1_v2.yaml')


def fake_population(tmp_path,monkeypatch):
    old,new=configs()
    counts=new['tournament']['completion_policy']['dataset_cases']
    members=[{'dataset':d,'opaque_incident_id':f'{d}-{i}'} for d,n in counts.items() for i in range(n)]
    for relative in [old['tournament']['prepared_pool_manifest'],
                     *[v for k,v in old['tournament']['prompt'].items() if k.endswith('_file')]]:
        p=tmp_path/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('unchanged fixture')
    monkeypatch.setattr(utils,'ROOT',tmp_path)
    monkeypatch.setattr(utils,'RQ3SegmentationAdapter',lambda _:SimpleNamespace(build=lambda:{'eval_roster_sha256':'fixed'}))
    monkeypatch.setattr(utils,'partition_rows',lambda *_:members)
    return old,new,members


def test_successor_changes_only_tournament_policy():
    old,new=configs()
    assert {k:v for k,v in old.items() if k!='tournament'}=={k:v for k,v in new.items() if k!='tournament'}
    for key in ('models','model_request_profiles','roster','prompt','prepared_pool_manifest','transport','success_levels'):
        assert old['tournament'][key]==new['tournament'][key]
    assert new['tournament']['next_stage']=='complete'
    assert new['tournament']['top1_successes_required'] is None


@pytest.mark.parametrize('version',['tournament_v1.yaml','tournament_ac1_v2.yaml'])
def test_real_partition_contract_accepts_both_recorded_versions(tmp_path,monkeypatch,version):
    cfg=load_config(utils.ROOT/'RQs/RQ3/configs'/version)
    monkeypatch.setattr(utils,'ROOT',tmp_path)
    path=tmp_path/cfg['eval_roster'];path.parent.mkdir(parents=True);path.write_text('protected roster')
    split={'eval_roster_sha256':utils.sha_file(path)}
    sentinel=[{'opaque_incident_id':'same frozen population'}]
    monkeypatch.setattr(utils,'canonical_eval_rows',lambda *_:sentinel)
    assert utils.partition_rows(cfg,split,'tournament') is sentinel
    cfg['tournament']['optimizer_eval_overlap_allowed']=True
    with pytest.raises(ValueError,match='explicit contract'):utils.partition_rows(cfg,split,'tournament')


def test_explicit_migration_required_and_old_round_lineage_kept(tmp_path,monkeypatch):
    old,new,_=fake_population(tmp_path,monkeypatch)
    original=utils.tournament_register(old)
    before=(original.root/'contract.json').read_bytes()
    with pytest.raises(ValueError,match='migrated'):utils.tournament_register(new)
    state=manage_tournament(new,'adopt-policy')
    assert not state['complete'] and state['rounds']==0
    assert (original.root/'contract.json').read_bytes()==before
    reg=utils.tournament_register(new)
    assert utils.tournament_register(old).state()==reg.state()  # Old status cannot silently switch back.
    assert manage_tournament(new,'adopt-policy')==state
    with pytest.raises(ValueError,match='explicit AC@1-only'):manage_tournament(old,'register')
    r=manage_tournament(new,'register')
    assert r['completion_policy_hash']==reg.completion_policy()['hash']
    assert len(r['cohorts']['qwen3.8-27b'])==480


@pytest.mark.parametrize('change',['fraction','omit_re2','count','next','pooled','model','roster'])
def test_successor_rejects_wrong_gate_or_population(tmp_path,monkeypatch,change):
    old,new,members=fake_population(tmp_path,monkeypatch)
    t=new['tournament']
    if change=='fraction':t['completion_policy']['numerator']=3
    if change=='omit_re2':t['threshold_datasets'].remove('re2_tt')
    if change=='count':t['completion_policy']['dataset_cases']['re2_ob']=100
    if change=='next':t['next_stage']='ac_at_5'
    if change=='pooled':t['top1_successes_required']=384
    if change=='model':t['models']=['qwen3.8-27b']
    if change=='roster':members.pop()
    with pytest.raises(ValueError):utils.tournament_register(new,allow_policy_migration=True)

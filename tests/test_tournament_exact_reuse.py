"""No-op methods reuse immutable replies, including wrong ones, without calls."""
from copy import deepcopy
import pytest
from RQs.RQ3.src import utils


def fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(utils,'ROOT',tmp_path)
    root=tmp_path/'RQs/RQ3/results/tournament_v1';old=root/'first/qwen';new=root/'next/qwen'
    parts=[{'type':'text','text':'instructions'},{'type':'image','png':b'PNG'}]
    env={'system':'fixed','model':{'name':'qwen','seed':42},'schema':{'n':5}}
    request={**env,'parts':[parts[0],{'type':'image','image_path':'renders/key.png','image_sha256':utils.stable_hash(b'PNG')}]}
    utils.write_json(old/'prompts/key.json',request);utils.atomic_write(old/'renders/key.png',b'PNG')
    utils.atomic_write(old/'conversations/key.md',b'original conversation')
    record={'response':'wrong but complete','call_key':'old','artifact_key':'key','attention':{'status':'disabled_by_protocol'}}
    record['record_hash']=utils.stable_hash(record)
    record['artifact_hashes']={p:utils.sha_file(old/p) for p in ('prompts/key.json','renders/key.png','conversations/key.md')}
    source=old/'trajectories/key.json';utils.write_json(source,record)
    ref={'record':str(source.relative_to(tmp_path)),'sha256':utils.sha_file(source)}
    return old,new,parts,env,ref


def test_exact_noop_preserves_original_bytes_and_resumes(tmp_path,monkeypatch):
    old,new,parts,env,ref=fixture(tmp_path,monkeypatch)
    for _ in range(2):
        result=utils.reuse_tournament_call(ref,parts,env,new)
        assert result['call_key']=='old' and result['response']=='wrong but complete'
    for path in old.rglob('*'):
        if path.is_file():assert path.read_bytes()==(new/path.relative_to(old)).read_bytes()


@pytest.mark.parametrize('change',['model','text','image','schema'])
def test_different_request_cannot_reuse(tmp_path,monkeypatch,change):
    old,new,parts,env,ref=fixture(tmp_path,monkeypatch)
    if change=='model':env['model']['name']='gemma'
    if change=='schema':env['schema']['n']=3
    if change=='text':parts[0]['text']='changed'
    if change=='image':parts[1]['png']=b'OTHER'
    with pytest.raises(ValueError):utils.reuse_tournament_call(ref,parts,env,new)
    assert not new.exists()


def test_corrupt_source_or_destination_rejected(tmp_path,monkeypatch):
    old,new,parts,env,ref=fixture(tmp_path,monkeypatch)
    utils.atomic_write(new/'renders/key.png',b'collision')
    with pytest.raises(ValueError,match='collision'):utils.reuse_tournament_call(ref,parts,env,new)
    utils.atomic_write(old/'renders/key.png',b'corrupt')
    with pytest.raises(ValueError,match='corrupt'):utils.reuse_tournament_call(ref,parts,env,new)

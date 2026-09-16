"""CPU storage tests, independent of any research-question orchestration."""
import json
import os
from pathlib import Path

import pytest

from vlmrca.training import (file_hash, prune_checkpoints, retain_periodic_checkpoints,
                            snapshot_inference_checkpoint)


def test_completion_probability_alignment_includes_stop_token():
    """Generic training helper: exact causal alignment includes the final token."""
    torch = pytest.importorskip("torch")
    pytest.importorskip("trl")
    from types import SimpleNamespace
    from vlmrca.training import completion_logprobs
    class Model(torch.nn.Module):
        device = "cpu"
        def forward(self,input_ids,attention_mask,logits_to_keep,use_cache):
            assert input_ids.tolist() == [[1,2,3,4,5]] and not use_cache
            assert logits_to_keep == 3
            logits = torch.zeros(1,3,8,requires_grad=True)
            logits = logits + torch.arange(8)[None,None,:] * torch.tensor([1.,2.,3.])[None,:,None]
            return SimpleNamespace(logits=logits)
    result = completion_logprobs(Model(),[1,2,3],[4,5])
    expected = torch.stack((torch.log_softmax(torch.arange(8).float(),0)[4],
                            torch.log_softmax(torch.arange(8).float()*2,0)[5]))
    torch.testing.assert_close(result,expected)
    (-result.mean()).backward()


def checkpoint(root, name, step, **extra):
    path = root/name
    path.mkdir(parents=True)
    files = {}
    for relative in ('policy/adapter_config.json', 'policy/adapter_model.safetensors', 'training_state.pt'):
        member = path/relative
        member.parent.mkdir(exist_ok=True)
        member.write_bytes(f'cpu-fixture-step-{step}'.encode())
        files[relative] = file_hash(member)
    (path/'checkpoint.json').write_text(json.dumps({'complete': True, 'step': step, 'files': files, **extra}))
    return path


def test_rolling_retention_every_update_and_resume_pin(tmp_path):
    for step in range(1, 44):
        checkpoint(tmp_path, f'step-{step:05d}', step)
        report = retain_periodic_checkpoints(tmp_path)
        assert set(report['kept']) == {f'step-{s:05d}' for s in range(20, step+1, 20)} | {f'step-{step:05d}'}
    assert sorted(p.name for p in tmp_path.glob('step-*')) == ['step-00020', 'step-00040', 'step-00043']
    checkpoint(tmp_path, 'step-00044.partial-crash', 44)
    retain_periodic_checkpoints(tmp_path)
    assert (tmp_path/'step-00044.partial-crash').exists()


def test_verify_new_checkpoint_before_pruning_old(tmp_path):
    old = checkpoint(tmp_path, 'step-00019', 19)
    new = checkpoint(tmp_path, 'step-00020', 20)
    (new/'training_state.pt').write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='corrupt'):
        retain_periodic_checkpoints(tmp_path)
    assert (old/'training_state.pt').is_file()


@pytest.mark.parametrize('preserve,inference_only', [(False, False), (True, False), (False, True)])
def test_interrupted_pruning_recovery(tmp_path, monkeypatch, preserve, inference_only):
    old = checkpoint(tmp_path, 'step-00019', 19)
    new = checkpoint(tmp_path, 'step-00020', 20)
    if inference_only:
        for path in (old, new):
            marker = path/'checkpoint.json'; state = json.loads(marker.read_text())
            del state['files']['training_state.pt']; (path/'training_state.pt').unlink()
            state['inference_only'] = True; marker.write_text(json.dumps(state))
    original = Path.unlink
    def interrupted(path, *args, **kwargs):
        result = original(path, *args, **kwargs)
        if path == old/('policy/adapter_model.safetensors' if preserve else 'checkpoint.json'):
            raise OSError('simulated power loss')
        return result
    monkeypatch.setattr(Path, 'unlink', interrupted)
    with pytest.raises(OSError, match='power loss'):
        retain_periodic_checkpoints(tmp_path, preserve_markers=preserve)
    monkeypatch.setattr(Path, 'unlink', original)
    retain_periodic_checkpoints(tmp_path, preserve_markers=preserve)
    assert (old/'checkpoint.json').exists() == preserve
    assert not (old/'training_state.pt').exists()


def test_retention_refuses_symlink_and_unknown_files(tmp_path):
    old = checkpoint(tmp_path, 'step-00019', 19)
    checkpoint(tmp_path, 'step-00020', 20)
    (old/'unowned.txt').write_text('user data')
    with pytest.raises(ValueError, match='unregistered'):
        retain_periodic_checkpoints(tmp_path)
    (old/'unowned.txt').unlink()
    (old/'external').symlink_to(tmp_path.parent)
    with pytest.raises(ValueError, match='symlink'):
        retain_periodic_checkpoints(tmp_path)
    assert (old/'training_state.pt').is_file()


def test_rl_offset_markers_and_lightweight_best(tmp_path):
    first = checkpoint(tmp_path, 'batch-007', 8, stage='RLOO', batch_index=7)
    best = snapshot_inference_checkpoint(first, tmp_path/'best-for-eval'/'batch-007')
    assert not (best/'training_state.pt').exists()
    assert os.stat(best/'policy/adapter_model.safetensors').st_ino == os.stat(first/'policy/adapter_model.safetensors').st_ino
    original = (first/'checkpoint.json').read_bytes()
    for index in (18, 19, 20):
        checkpoint(tmp_path, f'batch-{index:03d}', index+1, stage='RLOO', batch_index=index)
    report = retain_periodic_checkpoints(tmp_path, prefix='batch-', index_offset=1, preserve_markers=True)
    assert report['kept'] == ['batch-019', 'batch-020']
    assert (first/'checkpoint.json').read_bytes() == original
    assert not (first/'training_state.pt').exists()
    assert (best/'policy/adapter_model.safetensors').is_file()
    retain_periodic_checkpoints(tmp_path, prefix='batch-', index_offset=1, preserve_markers=True)
    newer = snapshot_inference_checkpoint(tmp_path/'batch-020', tmp_path/'best-for-eval'/'batch-020')
    prune_checkpoints(best.parent, {newer}, prefix='batch-')
    assert not best.exists() and newer.is_dir()

"""Durable training checkpoints and bounded retention.

These helpers contain no experiment, model, dataset or evaluation policy.
Callers supply the owner directory and the checkpoints still needed by them.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import random
import re
import tempfile

from unified_scripts.raw_data_processor import _fsync_directory, _write_json


def language_lora_targets(model):
    """All language Linear modules, including GDN projections; not only q/v."""
    import torch
    targets = []
    for name,module in model.named_modules():
        if isinstance(module,torch.nn.Linear) and any(x in name for x in ("language_model", "model.layers")):
            if not any(x in name for x in ("visual", "vision", "embed", "lm_head")):
                targets.append(name)
    if not targets:
        raise ValueError("no verified language-only LoRA targets")
    return targets


def seed_training(seed):
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def completion_logprobs(model, prompt_ids, completion_ids):
    """TRL logprobs on sampled IDs including EOS; full-support sampling, never retokenized text."""
    import torch
    from trl.trainer.utils import selective_log_softmax
    if not prompt_ids or not completion_ids:
        raise ValueError("empty prompt or completion IDs")
    ids=torch.tensor([prompt_ids+completion_ids],device=model.device)
    outputs=model(input_ids=ids,attention_mask=torch.ones_like(ids),
                  logits_to_keep=len(completion_ids)+1,use_cache=False)
    logits=outputs.logits[:,:-1,:].float()
    if logits.shape[1] != len(completion_ids):
        raise ValueError("model logits/completion alignment mismatch")
    result = selective_log_softmax(logits,ids[:,-len(completion_ids):]).squeeze(0)
    if not torch.isfinite(result).all():
        raise ValueError("non-finite training log probabilities")
    return result


def file_hash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save_training_checkpoint(model, optimizer, output, state):
    """Fsync then atomically publish a complete adapter/optimizer/RNG directory."""
    import numpy as np
    import torch
    output = Path(output)
    if output.exists():
        raise ValueError('refuse to overwrite a checkpoint')
    output.parent.mkdir(parents=True, exist_ok=True)
    pending = Path(tempfile.mkdtemp(prefix=output.name+'.partial-', dir=output.parent))
    model.save_pretrained(pending, selected_adapters=['policy'], safe_serialization=True)
    torch.save({'optimizer': optimizer.state_dict(), 'torch_rng': torch.get_rng_state(),
                'cuda_rng': torch.cuda.get_rng_state_all(), 'python_rng': random.getstate(),
                'numpy_rng': np.random.get_state()}, pending/'training_state.pt')
    files = {str(p.relative_to(pending)): file_hash(p) for p in sorted(pending.rglob('*')) if p.is_file()}
    _write_json(pending/'checkpoint.json', {**state, 'files': files, 'complete': True,
                'peak_vram_bytes': torch.cuda.max_memory_allocated() if torch.cuda.is_available() else None})
    for path in pending.rglob('*'):
        if path.is_file():
            with path.open('rb') as stream:
                os.fsync(stream.fileno())
    for path in sorted((p for p in pending.rglob('*') if p.is_dir()), reverse=True):
        _fsync_directory(path)
    _fsync_directory(pending)
    os.replace(pending, output)
    _fsync_directory(output.parent)
    return output


def restore_optimizer(optimizer, checkpoint):
    import numpy as np
    import torch
    checkpoint = Path(checkpoint)
    state = json.loads((checkpoint/'checkpoint.json').read_text())
    if state.get('complete') is not True:
        raise ValueError('partial checkpoint')
    for relative, digest in state['files'].items():
        path = (checkpoint/relative).resolve()
        if not path.is_relative_to(checkpoint.resolve()) or file_hash(path) != digest:
            raise ValueError('checkpoint hash mismatch')
    # Only locally produced, inventory-verified state is unpickled. Let PyTorch
    # cast optimizer tensors: noncapturable AdamW step counters belong on CPU.
    tensors = torch.load(checkpoint/'training_state.pt', map_location='cpu', weights_only=False)
    optimizer.load_state_dict(tensors['optimizer'])
    torch.set_rng_state(tensors['torch_rng']); torch.cuda.set_rng_state_all(tensors['cuda_rng'])
    random.setstate(tensors['python_rng']); np.random.set_state(tensors['numpy_rng'])
    return state


def prune_checkpoints(root, keep, *, prefix='step-', preserve_markers=False):
    """Delete only inventoried checkpoint payloads; keep latest and explicit pins.

    Caller must own an idle or exclusively controlled training directory. A
    durable per-target receipt precedes unlinking, so interrupted pruning can
    finish safely. Retained checkpoints are verified before any deletion.
    RL callers preserve immutable markers referenced by committed phase logs.
    """
    root = Path(root)
    if root.is_symlink() or not root.is_dir() or root.resolve() == Path('/'):
        raise ValueError('unsafe checkpoint owner')
    root = root.resolve()
    pattern = re.compile(re.escape(prefix)+r'\d+')
    candidates = sorted(p for p in root.iterdir() if pattern.fullmatch(p.name))
    keep = {Path(p).resolve() for p in keep}
    if not keep or not keep <= {p.resolve() for p in candidates}:
        raise ValueError('retention must name existing checkpoints in this owner')
    inventory = {}
    for path in candidates:
        if path.is_symlink() or not path.is_dir() or any(p.is_symlink() for p in path.rglob('*')):
            raise ValueError('symlink/non-directory in checkpoint inventory')
        marker = path/'checkpoint.json'
        if marker.exists():
            state, marker_hash = json.loads(marker.read_text()), file_hash(marker)
        else:
            receipt = root/'retention'/(path.name+'.json')
            if path in keep or preserve_markers or receipt.is_symlink() or not receipt.is_file():
                raise ValueError('checkpoint marker missing without a deletion receipt')
            previous = json.loads(receipt.read_text())
            if previous.get('checkpoint') != path.name or previous.get('preserve_marker') is not False:
                raise ValueError('invalid interrupted deletion receipt')
            state = {'complete': True, 'files': previous['files'],
                     'inference_only': previous.get('inference_only', False)}
            marker_hash = previous['checkpoint_sha256']
        if state.get('complete') is not True:
            raise ValueError('uncommitted checkpoint in retention inventory')
        files = state['files']
        required = {'policy/adapter_config.json', 'policy/adapter_model.safetensors'}
        if not state.get('inference_only'):
            required.add('training_state.pt')
        if not required <= files.keys():
            raise ValueError('incomplete checkpoint inventory')
        if any(not (path/f).resolve().is_relative_to(path) for f in files):
            raise ValueError('checkpoint member escapes owner')
        actual = {str(p.relative_to(path)) for p in path.rglob('*') if p.is_file()}
        if actual - (set(files) | {'checkpoint.json'}):
            raise ValueError('unregistered file in checkpoint directory')
        inventory[path] = (state, marker_hash)
        if path in keep:
            for relative, digest in files.items():
                if not (path/relative).is_file() or file_hash(path/relative) != digest:
                    raise ValueError('retained checkpoint missing/corrupt')
    report = {'kept': sorted(p.name for p in keep), 'removed': [], 'freed_bytes': 0}
    receipts = root/'retention'
    if receipts.is_symlink():
        raise ValueError('retention receipts must remain inside owner')
    for path, (state, digest) in inventory.items():
        if path in keep:
            continue
        receipt = receipts/(path.name+'.json')
        if receipt.is_symlink():
            raise ValueError('symlink retention receipt')
        planned = {'checkpoint': path.name, 'checkpoint_sha256': digest, 'files': state['files'],
                   'preserve_marker': preserve_markers}
        if state.get('inference_only'):
            planned['inference_only'] = True
        if receipt.exists():
            old = json.loads(receipt.read_text())
            if any(old.get(k) != v for k, v in planned.items()):
                raise ValueError('retention receipt identity changed')
        else:
            if any(not (path/f).is_file() for f in state['files']):
                raise ValueError('unexplained missing checkpoint payload')
            _write_json(receipt, {**planned, 'status': 'planned'})
            _fsync_directory(receipts)
        removed = 0
        for relative in state['files']:
            member = path/relative
            if member.exists():
                removed += member.stat().st_size
                member.unlink()
        if not preserve_markers and (path/'checkpoint.json').exists():
            removed += (path/'checkpoint.json').stat().st_size
            (path/'checkpoint.json').unlink()
        for directory in sorted((p for p in path.rglob('*') if p.is_dir()), reverse=True):
            directory.rmdir()
        if not preserve_markers:
            path.rmdir()
        else:
            _fsync_directory(path)
        _fsync_directory(root)
        _write_json(receipt, {**planned, 'status': 'complete'})
        report['removed'].append(path.name); report['freed_bytes'] += removed
    return report


def retain_periodic_checkpoints(root, interval=20, *, prefix='step-', index_offset=0, preserve_markers=False):
    """Keep periodic optimizer updates and the latest complete working state."""
    if type(interval) is not int or interval < 1:
        raise ValueError('checkpoint interval must be a positive integer')
    root = Path(root)
    if not root.exists():
        return {'kept': [], 'removed': [], 'freed_bytes': 0}
    numbered = [(int(p.name[len(prefix):])+index_offset, p) for p in root.iterdir()
                if re.fullmatch(re.escape(prefix)+r'\d+', p.name)]
    if not numbered:
        return {'kept': [], 'removed': [], 'freed_bytes': 0}
    latest = max(numbered)[1]
    keep = {p for step, p in numbered if step > 0 and step % interval == 0} | {latest}
    return prune_checkpoints(root, keep, prefix=prefix, preserve_markers=preserve_markers)


def snapshot_inference_checkpoint(source, target):
    """Keep a validation-selected policy without a historical optimizer copy.

    Hard links preserve immutable adapter bytes without duplicating them while
    their training checkpoint still exists. The parent marker hash binds the
    exact evaluated policy; this artifact must never resume optimization.
    """
    source, target = Path(source), Path(target)
    state = json.loads((source/'checkpoint.json').read_text())
    parent = file_hash(source/'checkpoint.json')
    names = ('policy/adapter_config.json', 'policy/adapter_model.safetensors')
    if state.get('complete') is not True or state.get('inference_only'):
        raise ValueError('inference snapshot requires a committed training checkpoint')
    files = {name: state['files'][name] for name in names}
    for name, digest in files.items():
        if (source/name).is_symlink() or file_hash(source/name) != digest:
            raise ValueError('inference snapshot source changed')
    if target.exists():
        saved = json.loads((target/'checkpoint.json').read_text())
        if saved.get('parent_checkpoint_sha256') != parent or saved.get('files') != files:
            raise ValueError('inference snapshot identity changed')
        for name, digest in files.items():
            if file_hash(target/name) != digest:
                raise ValueError('inference snapshot corrupt')
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = Path(tempfile.mkdtemp(prefix=target.name+'.partial-', dir=target.parent))
    (pending/'policy').mkdir()
    for name in names:
        os.link(source/name, pending/name)
    _write_json(pending/'checkpoint.json', {**state, 'files': files, 'inference_only': True,
                                          'parent_checkpoint_sha256': parent})
    _fsync_directory(pending/'policy'); _fsync_directory(pending)
    os.replace(pending, target); _fsync_directory(target.parent)
    return target


def chat_token_ids(tokenizer, messages):
    """Normalize one non-thinking chat tokenization across Transformers versions."""
    value = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, enable_thinking=False)
    if hasattr(value, 'keys'):
        value = value['input_ids']
    if hasattr(value, 'tolist'):
        value = value.tolist()
    if value and isinstance(value[0], list):
        if len(value) != 1:
            raise ValueError('expected one prompt')
        value = value[0]
    if not value or not all(isinstance(x, int) for x in value):
        raise ValueError('unrecognized chat tokenizer output')
    return value

"""Portable registration and durable small-file state; no dataset imports."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'RQs/RQ3_8'
DATA = BASE / 'preparation/export_v1'
RESULTS = BASE / 'results/operational_v1'
ARMS = ('T_SELECTED', 'T_FULL', 'G_SELECTED', 'G_FULL', 'READOUT_FULL', 'LINE_FULL', 'LINE_BOUND', 'LINE_PAIRS')
MODELS = ('qwen3.8-27b', 'gemma-4-31b')
VERSION = 'rq38-operational-v1'
METRICS = ('mrr', 'ac@1', 'ac@3', 'ac@5', 'avg@3', 'avg@5')


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode()).hexdigest()


def save(path, value):
    from vlmrca.run_state import atomic_write
    atomic_write(Path(path), (json.dumps(value, indent=2, ensure_ascii=False,
                                       allow_nan=False) + '\n').encode())


def identity(model, oid, arm, smoke=False):
    return digest([VERSION, model, oid, arm, 'smoke' if smoke else 'formal'])


def terminal(model, oid, arm, smoke=False):
    path = RESULTS / 'flags' / (identity(model, oid, arm, smoke) + '.json')
    return read(path) if path.is_file() else None


def source_contract():
    files = list((BASE/'src').glob('*.py')) + list((BASE/'configs').glob('*'))
    files += list((BASE/'descriptions').glob('*.md'))
    files += [ROOT/'docs/experiment_plans/CanvasRCA_RQ3_8_Nibi_Plan.md']
    files += list((ROOT/'src/renderer').rglob('*.py'))
    files += list((ROOT/'src/renderer/configs').glob('*.json'))
    files += list((ROOT/'src/renderer/web').glob('*.tsx'))
    files += list((ROOT/'src/renderer/web/components').glob('*.tsx'))
    files += list((ROOT/'src/renderer/web/components').glob('*.ts'))
    files += [ROOT/'src/renderer/web/style.css', ROOT/'src/renderer/web/package-lock.json']
    files += [ROOT/'src/vlmrca/vlm/client.py', ROOT/'src/vlmrca/vlm/configs.py',
              ROOT/'src/unified_scripts/vllm_inference.py',ROOT/'src/vlmrca/run_state.py',
              ROOT/'src/unified_scripts/rca_scorer.py',ROOT/'configs/rca_scorer.yaml',
              ROOT/'RQs/RQ3_1/src/main.py',ROOT/'RQs/RQ2/src/utils.py']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(files))}

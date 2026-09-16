"""CPU regression for the SFT validation worker's cold tokenizer initialization."""
import ast
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.utils import composer_tokenizer


def main():
    source = Path('RQs/RQ3/src/main.py').read_text()
    worker = next(node for node in ast.parse(source).body
                  if isinstance(node, ast.FunctionDef) and node.name == 'formal_worker')
    warmup = next(node.lineno for node in ast.walk(worker)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                  and node.func.id == 'composer_tokenizer')
    threads = next(node.lineno for node in ast.walk(worker)
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == 'ThreadPoolExecutor')
    assert warmup < threads
    cfg = load_config('RQs/RQ3/results/formal_balanced_v1/private/runtime_config.yaml')
    tokenizer = composer_tokenizer(cfg)
    sample = 'M16 entity=123 metric=latency; select C01 and C02.'
    expected = tokenizer.encode(sample)
    def run(_):
        actual = composer_tokenizer(cfg)
        assert actual is tokenizer
        assert actual.encode(sample) == expected
    with ThreadPoolExecutor(max_workers=36) as pool:
        list(pool.map(run, range(140)))
    print('PASS: one tokenizer initialized before 36 threads; 140 identical tokenizations')


if __name__ == '__main__':
    main()

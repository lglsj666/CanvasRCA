"""Prove the startup-only diff before reusing already verified preparation."""
import hashlib
import subprocess
import sys
from RQs.RQ3.src.main import load_config
from RQs.RQ3.src.utils import ROOT, catalogue_contract, pool_contract, read_json, sha_file, write_json


def main():
    prior = ROOT / 'RQs/RQ3/results/source_bins_repair_v1/compatibility.json'
    proof = read_json(prior)
    insertion = ("    if role=='composer':\n"
                 "        from .utils import composer_tokenizer\n"
                 "        composer_tokenizer(config)  # Initialize lazy imports/cache before request threads race.\n")
    changes = {'RQs/RQ3/src/main.py': (insertion, ''),
               'RQs/RQ3/src/utils.py': (",'validation_startup_repair_v1'", '')}
    for relative, digest in proof['after_files'].items():
        body = (ROOT / relative).read_bytes()
        if relative in changes:
            new, old = changes[relative]
            assert body.count(new.encode()) == 1
            body = body.replace(new.encode(), old.encode(), 1)
        assert hashlib.sha256(body).hexdigest() == digest, relative
    subprocess.run([sys.executable, 'RQs/RQ3/scripts/check_validation_tokenizer_threads.py'], check=True)
    cfg = load_config('RQs/RQ3/results/formal_balanced_v1/private/runtime_config.yaml')
    current = {'catalogue': catalogue_contract(cfg), 'pool': pool_contract(cfg)}
    assert current == proof['after'], 'input compiler identity changed'
    report = {**proof, 'scope': 'same preparation; tokenizer startup-order repair only; no Solver qualification',
              'after_files': {p: sha_file(ROOT / p) for p in proof['after_files']},
              'evidence': {str(prior.relative_to(ROOT)): sha_file(prior)},
              'startup_diff': {'main': 'preload identical tokenizer before 36 request threads',
                               'utils': 'register this exact-source compatibility proof'},
              'regression': '140 CPU tokenizations, 36 threads, one tokenizer; passed'}
    target = ROOT / 'RQs/RQ3/results/validation_startup_repair_v1/compatibility.json'
    if target.exists():
        assert read_json(target) == report, 'do not overwrite different repair proof'
    else:
        write_json(target, report)
    print('PASS: exact operational diff; pool/catalogue identities unchanged; original evidence preserved')


if __name__ == '__main__':
    main()

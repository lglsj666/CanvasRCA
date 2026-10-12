"""One explicitly authorized reset; exact targets, no symlink traversal or backups."""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'RQs/RQ3/results/tournament_v1'
AUDIT = STUDY / 'reset_20260913'
NAMES = (
    'round_0002_baro24_v1', 'round_0003_trace_sc8_v1',
    'round_0004_log_freq6_v1', 'round_0005_ma24_v1',
    'round_0006_log_freq6_extension_v1', 'round_0007_trace_sc8_extension_v1',
    'round_0008_baro24_extension_v1', 'round_0009_ma24_extension_v1',
    'round_0010_trace_status6_v1',
    'coverage/round_0002', 'coverage/round_0003', 'coverage/round_0004',
    'coverage/round_0005', 'coverage/round_0006', 'coverage/round_0007',
    'coverage/round_0008', 'coverage/round_0009', 'coverage/round_0010',
    'coverage/state.json', 'coverage/top1_completion_v2.json',
    'diagnostics_through05', 'diagnostics_through05.log', 'diagnostics_through05_v2.log',
    'log_freq6_extension_compatibility_v2.log', 'log_freq6_extension_gallery.log',
    'log_freq6_extension_gallery_v2.log', 'log_freq6_qualification', 'ma24_qualification',
    'logs/20260913_ac1_completion_policy.md',
)
PROTECTED = ('round_0001', 'round_0001_unitfix_v2', 'pools',
             'coverage/round_0001', 'coverage/contract.json')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def tree_files(path):
    if path.is_symlink():
        raise ValueError(f'symlink is not an authorized reset target: {path}')
    if path.is_file():
        return [path]
    files = []
    for directory, dirs, names in os.walk(path, followlinks=False):
        for name in dirs + names:
            child = Path(directory) / name
            if child.is_symlink():
                raise ValueError(f'refusing symlink traversal: {child}')
        files.extend(Path(directory) / name for name in names)
    return sorted(files)


def inventory(names, *, hashes):
    result = {}
    for name in names:
        path = STUDY / name
        if path.resolve() != path or not path.is_relative_to(STUDY):
            raise ValueError('target path changed')
        if not path.exists():
            continue
        for file in tree_files(path):
            row = {'bytes': file.stat().st_size}
            if hashes:
                row['sha256'] = sha(file)
            result[str(file.relative_to(STUDY))] = row
    return result


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix('.tmp').open('w') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    path.with_suffix('.tmp').replace(path)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('action', choices=['plan', 'apply'])
    args = cli.parse_args()
    manifest = AUDIT / 'deletion_manifest.json'
    if args.action == 'plan':
        if manifest.exists():
            raise ValueError('reset plan already exists; inspect it rather than overwrite')
        # Protect every round-1 and pool byte, not just a directory name.
        protected = inventory(PROTECTED, hashes=True)
        targets = inventory(NAMES, hashes=False)
        if not protected or not targets:
            raise ValueError('missing protection inventory or deletion targets')
        save(manifest, {'authorization': 'user ordered rounds 2–10 deletion and full-remaining restart',
                        'targets': list(NAMES), 'files': targets, 'protected': protected})
        print({'planned_files': len(targets), 'protected_files': len(protected),
               'delete_bytes': sum(r['bytes'] for r in targets.values())}, flush=True)
        return
    plan = json.loads(manifest.read_text())
    if plan['targets'] != list(NAMES):
        raise ValueError('unexpected deletion scope')
    if inventory(PROTECTED, hashes=True) != plan['protected']:
        raise ValueError('protected files changed before reset')
    current = inventory(NAMES, hashes=False)
    if any(plan['files'].get(k) != v for k, v in current.items()):
        raise ValueError('unplanned or changed file in deletion scope')
    # A partial interrupted deletion can safely continue over the exact allowlist.
    for name in NAMES:
        path = STUDY / name
        if path.is_symlink():
            raise ValueError('symlink substituted after audit')
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    if inventory(NAMES, hashes=False):
        raise ValueError('deletion incomplete')
    if inventory(PROTECTED, hashes=True) != plan['protected']:
        raise ValueError('protected files changed after reset')
    save(AUDIT / 'deletion_complete.json', {'status': 'complete',
         'deleted_bytes': sum(r['bytes'] for r in plan['files'].values()),
         'deleted_files': len(plan['files']), 'protected_files': len(plan['protected']),
         'protected_byte_identity': True, 'backups_of_deleted_results': False})
    print('DELETION_COMPLETE_PROTECTED_BYTES_IDENTICAL', flush=True)


if __name__ == '__main__':
    main()

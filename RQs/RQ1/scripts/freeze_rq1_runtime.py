#!/usr/bin/env python3
"""Freeze the exact RQ1 runtime file tree for one registered experiment."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml
from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash
from rq1lib.settings import assert_execution_config, load_yaml_config

ROOT = Path(__file__).resolve().parents[3]


def _config_chain(path: Path) -> list[Path]:
    resolved = path.resolve()
    if ROOT not in resolved.parents:
        raise ContractError("experiment config must be inside the project")
    payload = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ContractError(f"configuration is not an object: {resolved}")
    parent = payload.get("extends")
    return (
        [*_config_chain(resolved.parent / str(parent)), resolved]
        if parent
        else [resolved]
    )


def runtime_paths(config_path: Path) -> list[Path]:
    """Return every code/config file whose drift would change an RQ1 call."""

    candidates: set[Path] = set(_config_chain(config_path))
    for base, patterns in (
        (ROOT / "RQs/RQ1/scripts", ("*.py", "*.sh")),
        (ROOT / "RQs/RQ1/configs/schemas", ("*.json",)),
        (ROOT / "RQs/vlmrca", ("*.py",)),
    ):
        for pattern in patterns:
            candidates.update(base.rglob(pattern))
    for path in (
        ROOT / "RQs/RQ0/configs/checkpoint_lock.json",
        ROOT / "venvs/requirements-infer.txt",
        ROOT / "venvs/requirements-tools.txt",
    ):
        candidates.add(path)
    files = sorted(path.resolve() for path in candidates if path.is_file())
    if not files:
        raise ContractError("runtime tree is empty")
    return files


def runtime_manifest(config_path: Path) -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): sha256_bytes(path.read_bytes())
        for path in runtime_paths(config_path)
    }


def verify_runtime_manifest(manifest: dict[str, Any]) -> str:
    if not manifest:
        raise ContractError("code freeze runtime manifest is empty")
    actual: dict[str, str] = {}
    for relative, expected in sorted(manifest.items()):
        path = (ROOT / relative).resolve()
        if ROOT not in path.parents or not path.is_file():
            raise ContractError(f"frozen runtime file is absent or unsafe: {relative}")
        digest = sha256_bytes(path.read_bytes())
        if digest != expected:
            raise ContractError(f"frozen runtime file drifted: {relative}")
        actual[relative] = digest
    return stable_hash(actual)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    assert_execution_config(config)
    manifest = runtime_manifest(args.config)
    tree_hash = stable_hash(manifest)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    payload = {
        "schema_version": "RQ1CodeFreezeV1",
        "status": "frozen",
        "experiment_id": config["experiment_id"],
        "experiment_config_hash": stable_hash(config),
        "git_commit": commit,
        "working_tree_policy": "rq1_runtime_files_match_frozen_tree_hash",
        "runtime_tree_sha256": tree_hash,
        "runtime_files": manifest,
    }
    payload["freeze_contract_sha256"] = stable_hash(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

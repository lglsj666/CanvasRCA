"""Freeze the global vLLM config and its reusable implementation hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from unified_scripts import PROJECT_ROOT, stable_hash
from unified_scripts.vllm_inference import VLLMInferenceConfig

DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts/contracts/vllm_inference.lock.json"


def build_lock() -> dict:
    config = VLLMInferenceConfig.load()
    paths = (
        config.source,
        PROJECT_ROOT / "src/unified_scripts/vllm_inference.py",
        PROJECT_ROOT / "src/vlmrca/vlm/client.py",
        PROJECT_ROOT / "src/vlmrca/vlm/configs.py",
        PROJECT_ROOT / "src/vlmrca/vlm/runtime_contract.py",
        PROJECT_ROOT / "scripts/vllm_vlm/serve_canvasrca_nibi.sh",
    )
    payload = {
        "schema_version": "CanvasRCAVLLMLockV4",
        "config": config.audit_record(),
        "files": {str(path.relative_to(PROJECT_ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        "models": {tag: config.model(tag) for tag in ("qwen3.6-27b", "gemma-4-26b-a4b")},
    }
    payload["lock_sha256"] = stable_hash(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = build_lock()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        return 0 if args.out.is_file() and args.out.read_text() == text else 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

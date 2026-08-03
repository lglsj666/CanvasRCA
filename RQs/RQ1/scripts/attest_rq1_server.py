#!/usr/bin/env python3
"""Verify the live RQ1 vLLM endpoint and write its frozen attestation."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import urllib.request
from pathlib import Path
from typing import Any

import torch
from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash
from rq1lib.settings import assert_execution_config, load_yaml_config

ROOT = Path(__file__).resolve().parents[3]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractError(f"{path} is not a JSON object")
    return payload


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Authorization": "Bearer EMPTY"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read())
    if not isinstance(payload, dict):
        raise ContractError(f"server returned a non-object from {url}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--checkpoint-lock",
        type=Path,
        default=ROOT / "RQs/RQ0/configs/checkpoint_lock.json",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load_yaml_config(args.config)
    assert_execution_config(config)
    entries = (config["models"]["primary"], config["models"]["architecture_control"])
    try:
        model_entry = next(entry for entry in entries if entry["tag"] == args.model)
    except StopIteration as exc:
        raise ContractError(f"model is not registered for RQ1: {args.model}") from exc
    lock = _load(args.checkpoint_lock)
    locked = lock.get("models", {}).get(args.model)
    if not isinstance(locked, dict):
        raise ContractError(f"checkpoint lock lacks model {args.model}")
    checkpoint = (ROOT / model_entry["checkpoint"]).resolve()
    if checkpoint != Path(locked["local_path"]).resolve():
        raise ContractError("registered checkpoint differs from checkpoint lock")
    expected_files = {
        "config.json": locked["config_sha256"],
        "model.safetensors.index.json": locked["index_sha256"],
        "tokenizer_config.json": locked["tokenizer_config_sha256"],
    }
    for relative, expected in expected_files.items():
        path = checkpoint / relative
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
            raise ContractError(f"checkpoint file differs from lock: {path}")

    health_url = args.base_url.rstrip("/") + "/health"
    with urllib.request.urlopen(health_url, timeout=30) as response:
        if response.status != 200:
            raise ContractError(f"vLLM health endpoint returned {response.status}")
    models = _get_json(args.base_url.rstrip("/") + "/v1/models")
    live_ids = sorted(
        str(row.get("id")) for row in models.get("data", []) if row.get("id")
    )
    if model_entry["served_model_name"] not in live_ids:
        raise ContractError(
            f"live served model differs: expected={model_entry['served_model_name']} actual={live_ids}"
        )

    inference = config["inference"]
    payload = {
        "schema_version": "RQ1ServerAttestationV1",
        "status": "passed",
        "model_tag": args.model,
        "served_model_name": model_entry["served_model_name"],
        "live_model_ids": live_ids,
        "checkpoint_revision": locked["revision"],
        "checkpoint_manifest_sha256": stable_hash(locked),
        "tokenizer_manifest_sha256": locked["tokenizer_config_sha256"],
        "checkpoint_config_sha256": locked["config_sha256"],
        "checkpoint_index_sha256": locked["index_sha256"],
        "dtype": config["models"]["dtype"],
        "quantization": config["models"]["quantization"],
        "max_model_len": inference["max_model_len"],
        "gpu_memory_utilization": inference["gpu_memory_utilization"],
        "max_num_seqs": inference["max_num_seqs"],
        "max_images_per_prompt": inference["max_images_per_prompt"],
        "max_videos_per_prompt": inference["max_videos_per_prompt"],
        "generation_config": inference["generation_config"],
        "tensor_parallel_size": inference["tensor_parallel_size"],
        "cublas_workspace_config": inference["cublas_workspace_config"],
        "trust_remote_code": inference["trust_remote_code"],
        "enable_log_requests": inference["enable_log_requests"],
        "extra_server_args": inference["extra_server_args"],
        "enable_prefix_caching": inference["enable_prefix_caching"],
        "enable_chunked_prefill": inference["enable_chunked_prefill"],
        "async_scheduling": inference["async_scheduling"],
        "enforce_eager": inference["enforce_eager"],
        "use_flashinfer_sampler": inference["use_flashinfer_sampler"],
        "gdn_prefill_backend": inference["gdn_prefill_backend"],
        "moe_backend": inference["moe_backend"],
        "triton_force_first_config": inference["triton_force_first_config"],
        "batch_invariant": model_entry["batch_invariant"],
        "vllm_version": importlib.metadata.version("vllm"),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "gpu_name": torch.cuda.get_device_name(0),
        "launcher": "RQs/RQ1/scripts/vllm_vlm/serve_rq1_local.sh",
        "launcher_sha256": sha256_bytes(
            (ROOT / "RQs/RQ1/scripts/vllm_vlm/serve_rq1_local.sh").read_bytes()
        ),
        "vllm_batch_invariant_env": os.environ.get("VLLM_BATCH_INVARIANT"),
    }
    payload["attestation_sha256"] = stable_hash(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

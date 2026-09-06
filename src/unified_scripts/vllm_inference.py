"""Unified, extensible vLLM inference configuration and launcher arguments."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import ConfigError, FrozenConfig, canonical_json, project_path


class VLLMInferenceConfig(FrozenConfig):
    """Frozen base recipe with explicit, hash-recorded experiment adapters."""

    DEFAULT_PATH = "configs/vllm_inference.yaml"
    SCHEMA_VERSION = "CanvasRCAVLLMInferenceConfigV11"

    @classmethod
    def load(cls, path=None, *, adapter=None):
        """Load the explicitly selected deployment profile.

        Callers that name the canonical default still honor
        ``CANVASRCA_VLLM_CONFIG``. This keeps the experiment code identical on
        Nibi and local WSL while making profile selection visible and
        hash-recorded rather than inferred from the hostname.
        """

        override = os.environ.get("CANVASRCA_VLLM_CONFIG")
        is_default = path is None or project_path(path).resolve() == project_path(cls.DEFAULT_PATH).resolve()
        selected = override if override and is_default else path
        return super().load(selected, adapter=adapter)

    def validate(self) -> None:
        common = self.data.get("common")
        models = self.data.get("models")
        if not isinstance(common, Mapping) or not isinstance(models, Mapping):
            raise ConfigError("vLLM config requires common and models mappings")
        required = {
            "dtype": "bfloat16",
            "quantization": None,
            "temperature": 1.0,
            "top_p": 0.95,
            "seed": 42,
            "max_model_len": 40960,
            "max_tokens": 16384,
            "max_num_seqs": 256,
        }
        drift = {key: (common.get(key), value) for key, value in required.items() if common.get(key) != value}
        if drift:
            raise ConfigError(f"frozen inference fields drifted: {drift}")
        deployment = self.data.get("deployment")
        if not isinstance(deployment, Mapping) or deployment.get("profile") not in {"nibi", "local"}:
            raise ConfigError("vLLM config requires deployment.profile=nibi|local")
        expected_gpu = None if deployment["profile"] == "nibi" else 0.75
        if common.get("gpu_memory_utilization", "missing") != expected_gpu:
            raise ConfigError(
                f"{deployment['profile']} profile requires "
                f"gpu_memory_utilization={expected_gpu!r}"
            )
        for key in ("python", "vllm_bin"):
            if not str(deployment.get(key) or ""):
                raise ConfigError(f"deployment.{key} is required")
        for tag in ("qwen3.8-27b", "gemma-4-26b-a4b"):
            if tag not in models:
                raise ConfigError(f"missing registered model: {tag}")
        qwen = models["qwen3.8-27b"]
        if qwen.get("mm_processor_kwargs") is not None:
            raise ConfigError("Qwen must use its native image processor policy")
        compact_json = {"backend": "xgrammar", "disable_any_whitespace": True}
        for tag in ("qwen3.8-27b", "gemma-4-26b-a4b"):
            if models[tag].get("structured_outputs_config") != compact_json:
                raise ConfigError(
                    f"{tag} must use xgrammar with arbitrary JSON whitespace disabled"
                )
    def model(self, tag: str) -> dict[str, Any]:
        models = self.data["models"]
        if tag not in models:
            raise ConfigError(f"unknown model tag: {tag}")
        spec = {**dict(self.data["common"]), **dict(models[tag])}
        # Multiple one-GPU Slurm jobs can share a physical Nibi node.  The
        # frozen port is the portable default; a launcher-selected localhost
        # port is deployment metadata and must be applied consistently to the
        # server argument vector and live-server attestation.
        port_override = os.environ.get("CANVASRCA_VLLM_PORT")
        if port_override:
            try:
                port = int(port_override)
            except ValueError as exc:
                raise ConfigError("CANVASRCA_VLLM_PORT must be an integer") from exc
            if not 1024 <= port <= 65535:
                raise ConfigError("CANVASRCA_VLLM_PORT must be in [1024, 65535]")
            spec["port"] = port
            spec["base_url"] = f"http://{spec['host']}:{port}/v1"
        return spec

    def model_path(self, tag: str) -> Path:
        spec = self.model(tag)
        env_name = spec.get("model_path_env")
        configured = os.environ.get(str(env_name)) if env_name else None
        return project_path(configured or spec["model_path"])

    def server_argv(self, tag: str) -> list[str]:
        """Return vLLM CLI arguments; null fields are intentionally omitted."""

        spec = self.model(tag)
        flags: list[tuple[str, str, str]] = [
            ("--served-model-name", "served_model_name", "text"),
            ("--host", "host", "text"),
            ("--port", "port", "text"),
            ("--dtype", "dtype", "text"),
            ("--generation-config", "generation_config", "text"),
            ("--max-model-len", "max_model_len", "text"),
            ("--max-num-seqs", "max_num_seqs", "text"),
            ("--tensor-parallel-size", "tensor_parallel_size", "text"),
            ("--seed", "seed", "text"),
            ("--mm-processor-cache-gb", "mm_processor_cache_gb", "text"),
            ("--gpu-memory-utilization", "gpu_memory_utilization", "text"),
            ("--mm-processor-kwargs", "mm_processor_kwargs", "json"),
            ("--structured-outputs-config", "structured_outputs_config", "json"),
            ("--default-chat-template-kwargs", "default_chat_template_kwargs", "json"),
            ("--gdn-prefill-backend", "gdn_prefill_backend", "text"),
            ("--moe-backend", "moe_backend", "text"),
        ]
        argv = [str(self.model_path(tag))]
        for flag, key, encoding in flags:
            value = spec.get(key)
            if value is None:
                continue
            argv.extend([flag, canonical_json(value) if encoding == "json" else str(value)])
        bool_flags = {
            "enable_chunked_prefill": "--enable-chunked-prefill",
            "enable_prefix_caching": "--enable-prefix-caching",
            "enforce_eager": "--enforce-eager",
            "trust_remote_code": "--trust-remote-code",
        }
        for key, flag in bool_flags.items():
            if spec.get(key):
                argv.append(flag)
        if not spec.get("enable_chunked_prefill", False):
            argv.append("--no-enable-chunked-prefill")
        argv.append("--async-scheduling" if spec.get("async_scheduling") else "--no-async-scheduling")
        if not spec.get("enable_prefix_caching", False):
            argv.append("--no-enable-prefix-caching")
        if not spec.get("enable_log_requests", True):
            argv.append("--no-enable-log-requests")
        argv.extend(
            [
                "--limit-mm-per-prompt",
                canonical_json(
                    {
                        "image": int(spec["max_images_per_prompt"]),
                        "video": int(spec["max_videos_per_prompt"]),
                    }
                ),
            ]
        )
        argv.extend(map(str, spec.get("extra_server_args") or ()))
        return argv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=("qwen3.8-27b", "gemma-4-26b-a4b"))
    parser.add_argument("--config", default=VLLMInferenceConfig.DEFAULT_PATH)
    parser.add_argument("--format", choices=("json", "argv"), default="json")
    args = parser.parse_args(argv)
    config = VLLMInferenceConfig.load(args.config)
    if args.format == "argv":
        print("\n".join(config.server_argv(args.model)))
    else:
        print(json.dumps({"audit": config.audit_record(), "model": config.model(args.model)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Compatibility facade over the global Nibi vLLM contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from unified_scripts import PROJECT_ROOT, project_path
from unified_scripts.vllm_inference import VLLMInferenceConfig

ROOT = PROJECT_ROOT
DEFAULT_CONTRACT = ROOT / VLLMInferenceConfig.DEFAULT_PATH


class VLLMRuntimeContractError(ValueError):
    pass


def load_runtime_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    try:
        return dict(VLLMInferenceConfig.load(path).data)
    except Exception as error:
        raise VLLMRuntimeContractError(str(error)) from error


def contract_sha256(path: str | Path = DEFAULT_CONTRACT) -> str:
    return VLLMInferenceConfig.load(path).source_sha256


def resolved_model_runtime(model_tag: str, path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    config = VLLMInferenceConfig.load(path)
    value = config.model(model_tag)
    value["protocol_version"] = config.data["protocol_version"]
    value["runtime_contract_sha256"] = config.source_sha256
    value["effective_runtime_sha256"] = config.effective_hash()
    return value


def assert_request_sampling(*, temperature: float | None, top_p: float | None, seed: int | None) -> None:
    common = VLLMInferenceConfig.load().data["common"]
    observed = (temperature, top_p, seed)
    expected = (common["temperature"], common["top_p"], common["seed"])
    if observed != expected:
        raise VLLMRuntimeContractError(f"request sampling drifted: observed={observed}, expected={expected}")


def assert_result_root_not_archived(result_root: str | Path) -> None:
    resolved = project_path(result_root).resolve()
    if ROOT not in resolved.parents:
        raise VLLMRuntimeContractError("result root escapes the project")
    if any(part.startswith("_archive") for part in resolved.relative_to(ROOT).parts):
        raise VLLMRuntimeContractError("archived result roots cannot be resumed")


def assert_successor_execution_authorized(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(project_path(path).read_text())
    if not isinstance(payload, dict) or payload.get("execution_enabled") is not True:
        raise VLLMRuntimeContractError("experiment execution is not enabled")
    return payload

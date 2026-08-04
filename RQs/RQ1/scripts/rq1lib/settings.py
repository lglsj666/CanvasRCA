"""RQ1 config/schema loading and execution interlocks."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from .contracts import ContractError, sha256_bytes, stable_hash

ROOT = Path(__file__).resolve().parents[4]


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], Mapping)
            and isinstance(value, Mapping)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_yaml_config(path: Path) -> dict[str, Any]:
    path = Path(path).resolve()
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractError(f"configuration {path} is not a mapping")
    extends = payload.pop("extends", None)
    if extends is not None:
        if not isinstance(extends, str) or not extends:
            raise ContractError(
                "configuration extends must be a relative non-empty path"
            )
        parent = (path.parent / extends).resolve()
        if parent == path or path.parent not in parent.parents:
            raise ContractError("configuration extends escapes its config directory")
        payload = _deep_merge(load_yaml_config(parent), payload)
    return payload


def _assert_common_config(config: Mapping[str, Any]) -> None:
    if config.get("schema_version") != "RQ1ExperimentConfigV1":
        raise ContractError("unsupported RQ1 experiment config schema")
    contracts = dict(config.get("contracts") or {})
    if contracts.get("prompt_hybrid_composition") != "A_PLUS_B":
        raise ContractError("RQ1 hybrid prompt must be frozen as A_PLUS_B")
    if contracts.get("exact_fact_inventory_equality") != "required":
        raise ContractError("RQ1 exact fact parity must be required")
    task_profile = str(config.get("visops", {}).get("task_profile", "legacy_visops_v2"))
    if task_profile == "two_stage_onset_ledger_v2":
        structured_required = {
            "prompt_answer_contract": "compact_task_specific_regex_v3",
            "structured_output_transport": (
                "vllm_structured_outputs_regex_no_whitespace"
            ),
        }
    elif str(config.get("experiment_id", "")).endswith("_v2") or task_profile in {
        "answer_hidden_compositional_v1",
        "two_stage_onset_ledger_v1",
    }:
        structured_required = {
            "prompt_answer_contract": "type_specific_json_v2",
            "structured_output_transport": "openai_response_format_json_schema",
        }
    else:
        structured_required = {}
    if structured_required:
        structured_mismatches = {
            key: (contracts.get(key), value)
            for key, value in structured_required.items()
            if contracts.get(key) != value
        }
        if structured_mismatches:
            raise ContractError(
                f"RQ1 v2 structured-output contract differs: {structured_mismatches}"
            )
    if contracts.get("canonical_source_required_for_execution") != (
        "CanonicalEvidenceStoreV2WithDenseLogAndTraceTimeSlices"
    ):
        raise ContractError("RQ1 execution must require the dense V2 evidence store")
    router_relative = contracts.get("frozen_operation_router")
    if router_relative is not None:
        router_path = (ROOT / str(router_relative)).resolve()
        if ROOT not in router_path.parents or not router_path.is_file():
            raise ContractError("RQ1 frozen operation router is absent or unsafe")
        router_bytes = router_path.read_bytes()
        expected_file_hash = contracts.get("frozen_operation_router_file_sha256")
        if sha256_bytes(router_bytes) != expected_file_hash:
            raise ContractError("RQ1 frozen operation router file hash differs")
        router = json.loads(router_bytes)
        if (
            router.get("schema_version") != "RQ1VisOpsRouterV1"
            or router.get("status") != "frozen"
            or router.get("mapping_model") != "gemma-4-26b-a4b"
            or router.get("architecture_control_policy")
            != "qwen_uses_identical_gemma_router"
        ):
            raise ContractError("RQ1 frozen operation router contract differs")
        expected_contract_hash = contracts.get(
            "frozen_operation_router_contract_sha256"
        )
        if router.get("router_contract_sha256") != expected_contract_hash:
            raise ContractError("RQ1 frozen router contract hash differs from config")
        unhashed = dict(router)
        unhashed.pop("router_contract_sha256", None)
        if stable_hash(unhashed) != expected_contract_hash:
            raise ContractError("RQ1 frozen router self-hash is invalid")
    if task_profile == "answer_hidden_compositional_v1":
        expected_operations = {
            "exact_lookup": {"metric_exact_lookup"},
            "temporal_scanning": set(),
            "topology_path": set(),
            "cross_modal_alignment": set(),
            "missingness_uncertainty": set(),
            "answer_hidden_temporal_composition": {
                "raw_temporal_onset_low",
                "raw_temporal_onset_high",
            },
            "answer_hidden_relational_composition": {
                "directed_shortest_path_low",
                "directed_shortest_path_high",
            },
        }
    elif task_profile == "two_stage_onset_ledger_v1":
        expected_operations = {
            "exact_lookup": set(),
            "temporal_scanning": set(),
            "topology_path": set(),
            "cross_modal_alignment": set(),
            "missingness_uncertainty": set(),
            "answer_hidden_temporal_composition": {"panel_onset_ledger_high"},
            "answer_hidden_relational_composition": set(),
        }
    elif task_profile == "two_stage_onset_ledger_v2":
        expected_operations = {
            "exact_lookup": set(),
            "temporal_scanning": set(),
            "topology_path": set(),
            "cross_modal_alignment": set(),
            "missingness_uncertainty": set(),
            "answer_hidden_temporal_composition": {
                "panel_onset_ledger_high_compact"
            },
            "answer_hidden_relational_composition": set(),
        }
    else:
        expected_operations = {
            "exact_lookup": {
                "metric_exact_lookup",
                "log_exact_lookup",
                "trace_exact_lookup",
            },
            "temporal_scanning": {"earliest_onset", "longest_persistence"},
            "topology_path": {"directed_edge", "multi_hop_path"},
            "cross_modal_alignment": {"entity_modality_alignment"},
            "missingness_uncertainty": {"metric_missingness"},
        }
    actual_operations = {
        family: set(operations)
        for family, operations in dict(
            config.get("visops", {}).get("operation_families") or {}
        ).items()
    }
    if actual_operations != expected_operations:
        raise ContractError(
            "RQ1 registered VisOps operations differ from implemented operations: "
            f"actual={actual_operations} expected={expected_operations}"
        )
    integrity = dict(config.get("integrity") or {})
    if (
        float(
            integrity.get(
                "maximum_paired_whole_case_infrastructure_exclusion_fraction", -1
            )
        )
        != 0.05
    ):
        raise ContractError("RQ1 infrastructure exclusion ceiling must be 5%")
    inference = dict(config.get("inference") or {})
    expected = {
        "base_url": "http://127.0.0.1:8000/v1",
        "host": "0.0.0.0",
        "port": 8000,
        "vllm_python": "venvs/infer/bin/python",
        "max_model_len": 32768,
        "max_tokens": 16384,
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": 42,
        "disable_thinking": True,
        "gpu_memory_utilization": 0.65,
        "max_num_seqs": 8,
        "max_images_per_prompt": 8,
        "max_videos_per_prompt": 0,
        "generation_config": "vllm",
        "tensor_parallel_size": 1,
        "cublas_workspace_config": ":4096:8",
        "trust_remote_code": True,
        "enable_log_requests": False,
        "extra_server_args": [],
        "enable_prefix_caching": False,
        "enable_chunked_prefill": False,
        "async_scheduling": False,
        "enforce_eager": True,
        "use_flashinfer_sampler": False,
        "gdn_prefill_backend": "triton",
        "moe_backend": "triton",
        "triton_force_first_config": True,
        "request_timeout_sec": 1800,
        "wait_timeout_sec": 1800,
        "retry_attempts": 3,
    }
    mismatches = {
        key: (inference.get(key), value)
        for key, value in expected.items()
        if inference.get(key) != value
    }
    if mismatches:
        raise ContractError(
            f"RQ1 inference config differs from canonical values: {mismatches}"
        )
    models = dict(config.get("models") or {})
    primary = dict(models.get("primary") or {})
    control = dict(models.get("architecture_control") or {})
    if primary.get("batch_invariant") is not True:
        raise ContractError("Gemma must use batch_invariant=true")
    if primary.get("thinking_via_template") is not False:
        raise ContractError("Gemma must not receive a Qwen thinking-template switch")
    if control.get("batch_invariant") is not False:
        raise ContractError("Qwen3.6 must use batch_invariant=false")
    if control.get("thinking_via_template") is not True:
        raise ContractError("Qwen3.6 must receive its frozen thinking-template switch")
    if models.get("quantization", "missing") is not None:
        raise ContractError("RQ1 inference must remain unquantized")


def assert_static_config(config: Mapping[str, Any]) -> None:
    _assert_common_config(config)
    execution = dict(config.get("execution") or {})
    if execution.get("enabled") is not False:
        raise ContractError("checked-in static RQ1 config must keep execution disabled")
    if execution.get("training_allowed") is not False:
        raise ContractError("checked-in static RQ1 config must forbid training")
    if execution.get("heldout_access_allowed") is not False:
        raise ContractError("checked-in static RQ1 config must forbid heldout access")


def assert_execution_config(config: Mapping[str, Any]) -> None:
    """Validate a registered exposed-development inference configuration."""

    _assert_common_config(config)
    execution = dict(config.get("execution") or {})
    required = {
        "enabled": True,
        "long_running_inference_allowed": True,
        "training_allowed": False,
        "heldout_access_allowed": False,
    }
    mismatches = {
        key: (execution.get(key), value)
        for key, value in required.items()
        if execution.get(key) != value
    }
    if mismatches:
        raise ContractError(f"RQ1 registered execution flags differ: {mismatches}")
    partition = config.get("data", {}).get("allowed_partition")
    stage = str(execution.get("stage") or "")
    allowed = partition == "exposed_development_only" or (
        partition == "validation_smoke_only" and "smoke" in stage
    )
    if not allowed:
        raise ContractError(
            "RQ1b execution partition/stage combination is not authorized"
        )


def configure_registered_vllm_environment(config: Mapping[str, Any]) -> None:
    """Bind the unified client to the already-validated local RQ1 endpoint."""

    _assert_common_config(config)
    base_url = str(config["inference"]["base_url"])
    if base_url != "http://127.0.0.1:8000/v1":
        raise ContractError("RQ1 local vLLM endpoint differs from the registered URL")
    os.environ["VLLM_BASE_URL"] = base_url
    os.environ.setdefault("VLLM_API_KEY", "EMPTY")


def validate_schema_files(config: Mapping[str, Any], root: Path) -> dict[str, Any]:
    results: dict[str, Any] = {}
    locations = {
        field_name: config["contracts"][field_name]
        for field_name in (
            "query_spec_schema",
            "paired_view_schema",
            "evidence_ledger_schema",
            "private_answer_key_schema",
        )
    }
    locations.update(
        {
            field_name: config["data"][field_name]
            for field_name in (
                "exposure_ledger_schema",
                "private_selection_schema",
                "public_roster_schema",
                "private_roster_schema",
            )
        }
    )
    for field_name, configured_path in locations.items():
        relative = Path(str(configured_path))
        path = (root / relative).resolve()
        if root.resolve() not in path.parents:
            raise ContractError(f"schema path escapes project root: {path}")
        schema = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        results[field_name] = schema
    return results


def assert_runner_may_execute(
    config: Mapping[str, Any],
    roster: Mapping[str, Any],
    *,
    explicit_execute: bool,
) -> None:
    """Future runner interlock; current checked-in files cannot pass it."""

    if not explicit_execute:
        raise ContractError("runner requires an explicit --execute acknowledgement")
    assert_execution_config(config)
    if roster.get("status") != "frozen" or roster.get("execution_allowed") is not True:
        raise ContractError("RQ1 roster is not frozen and executable")
    if not roster.get("cases"):
        raise ContractError("RQ1 roster contains no cases")
    if not roster.get("assignment_hash") or not roster.get("exposure_ledger_lineage"):
        raise ContractError("RQ1 roster lacks frozen assignment/exposure lineage")

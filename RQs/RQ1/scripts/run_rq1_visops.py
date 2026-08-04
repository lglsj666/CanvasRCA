#!/usr/bin/env python3
"""Contract-aware, resumable RQ1 VisOps runner (execution locked by config)."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import threading
import time
from collections.abc import Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Self

from freeze_rq1_runtime import verify_runtime_manifest
from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash
from rq1lib.prompts import (
    build_prompt_bundle_from_artifacts,
    panel_ids_from_public_facts,
)
from rq1lib.scoring import parse_visops_response, score_visops_answer
from rq1lib.settings import (
    assert_runner_may_execute,
    configure_registered_vllm_environment,
    load_yaml_config,
)
from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens
from vlmrca.vlm.configs import get_config

ROOT = Path(__file__).resolve().parents[3]
RQ_ROOT = ROOT / "RQs/RQ1"
DEFAULT_CONFIG = RQ_ROOT / "configs/rq1_visops_v1.yaml"
DEFAULT_ROSTER = RQ_ROOT / "configs/rosters/rq1b_visops_exposed_development_v1.json"
ARM_TO_FRAGMENT = {"V": "visual_a", "T": "text_b", "H": "hybrid_a_plus_b"}
ARM_PERMUTATIONS = ("TVH", "THV", "VTH", "VHT", "HTV", "HVT")
TWO_STAGE_PROFILES = {"two_stage_onset_ledger_v1", "two_stage_onset_ledger_v2"}


class _GPUAccounting:
    """Sample NVML during one sequential request and integrate GPU utilization."""

    def __init__(self, interval_s: float = 0.05) -> None:
        self.interval_s = interval_s
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._samples: list[tuple[float, float, int]] = []
        self._error: Exception | None = None

    def __enter__(self) -> Self:
        def sample() -> None:
            try:
                import pynvml

                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                # Take a synchronized sample before the request starts.  Some
                # short text operations finish in less than the 50 ms sampling
                # interval; without this handshake the worker may observe only
                # the final sample and incorrectly classify a successful call
                # as an accounting/infrastructure failure.
                now = time.monotonic()
                utilization = float(pynvml.nvmlDeviceGetUtilizationRates(handle).gpu)
                memory = int(pynvml.nvmlDeviceGetMemoryInfo(handle).used)
                self._samples.append((now, utilization, memory))
                self._ready.set()
                while not self._stop.wait(self.interval_s):
                    now = time.monotonic()
                    utilization = float(
                        pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
                    )
                    memory = int(pynvml.nvmlDeviceGetMemoryInfo(handle).used)
                    self._samples.append((now, utilization, memory))
                now = time.monotonic()
                utilization = float(pynvml.nvmlDeviceGetUtilizationRates(handle).gpu)
                memory = int(pynvml.nvmlDeviceGetMemoryInfo(handle).used)
                self._samples.append((now, utilization, memory))
                pynvml.nvmlShutdown()
            except Exception as exc:  # noqa: BLE001 - accounting must fail closed
                self._error = exc
                self._ready.set()

        self._thread = threading.Thread(
            target=sample, name="rq1-gpu-accounting", daemon=True
        )
        self._thread.start()
        if not self._ready.wait(timeout=5):
            raise ContractError("GPU accounting did not initialize within 5 seconds")
        if self._error is not None:
            raise ContractError(f"GPU accounting failed to initialize: {self._error}")
        return self

    def __exit__(self, *_args: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def report(self) -> dict[str, Any]:
        if self._error is not None:
            raise ContractError(f"GPU accounting failed: {self._error}")
        if len(self._samples) < 2:
            raise ContractError("GPU accounting produced fewer than two samples")
        active = 0.0
        for left, right in zip(self._samples, self._samples[1:]):
            dt = max(0.0, right[0] - left[0])
            active += dt * ((left[1] + right[1]) / 200.0)
        return {
            "gpu_active_time_s": active,
            "peak_gpu_memory_bytes": max(sample[2] for sample in self._samples),
            "gpu_accounting_samples": len(self._samples),
            "gpu_accounting_method": "NVML utilization-weighted trapezoid at 50ms",
        }


def _arm_order(opaque_incident_id: str) -> str:
    digest = stable_hash(
        {
            "seed": 42,
            "purpose": "rq1b_arm_order",
            "opaque_incident_id": opaque_incident_id,
        }
    )
    return ARM_PERMUTATIONS[int(digest, 16) % len(ARM_PERMUTATIONS)]


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractError(f"{path} is not a JSON object")
    return payload


def _prepared_roots_from_index(
    path: Path,
    *,
    config: Mapping[str, Any],
    roster: Mapping[str, Any],
) -> tuple[list[Path], dict[str, Any]]:
    index = _load_json(path.resolve())
    if index.get("schema_version") != "RQ1PreparedRosterIndexV1":
        raise ContractError("unsupported prepared-roster index")
    if index.get("experiment_id") != config.get("experiment_id"):
        raise ContractError("prepared-roster index belongs to another experiment")
    if index.get("experiment_config_hash") != stable_hash(config):
        raise ContractError("prepared-roster index config hash drifted")
    if index.get("roster_assignment_hash") != roster.get("assignment_hash"):
        raise ContractError("prepared-roster index assignment hash drifted")
    if index.get("roster_contract_hash") != stable_hash(roster):
        raise ContractError("prepared-roster index roster contract drifted")
    cases = index.get("cases")
    if not isinstance(cases, list) or index.get("n_cases") != len(cases):
        raise ContractError("prepared-roster index case count differs")
    expected_hash = stable_hash(
        {key: value for key, value in index.items() if key != "artifact_inventory_hash"}
    )
    if index.get("artifact_inventory_hash") != expected_hash:
        raise ContractError("prepared-roster artifact inventory hash drifted")
    roots: list[Path] = []
    for row in cases:
        root = (ROOT / str(row["prepared_root"])).resolve()
        manifest = root / "manifest.json"
        if not manifest.is_file() or sha256_bytes(manifest.read_bytes()) != row.get(
            "manifest_sha256"
        ):
            raise ContractError(f"prepared manifest drift under {root}")
        roots.append(root)
    if len(roots) != len(set(roots)):
        raise ContractError("prepared-roster index contains duplicate roots")
    return roots, index


def _verify_qualification_report(
    path: Path | None,
    *,
    prepared_index: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if path is None:
        raise ContractError("execution requires --qualification-report")
    report = _load_json(path.resolve())
    required = {
        "schema_version": "RQ1VisOpsQualificationV1",
        "status": "passed",
        "experiment_id": config["experiment_id"],
        "experiment_config_hash": stable_hash(config),
        "artifact_inventory_hash": prepared_index["artifact_inventory_hash"],
        "parity_passed": True,
        "leakage_passed": True,
        "determinism_passed": True,
        "visual_review_passed": True,
    }
    mismatches = {
        key: (report.get(key), value)
        for key, value in required.items()
        if report.get(key) != value
    }
    if mismatches:
        raise ContractError(f"RQ1 qualification report differs: {mismatches}")
    return report


def _verify_smoke_report(
    path: Path | None,
    *,
    model: str,
    config: Mapping[str, Any],
) -> dict[str, Any] | None:
    if config.get("execution", {}).get("requires_smoke_qualification") is not True:
        return None
    if path is None:
        raise ContractError("full mapping execution requires --smoke-qualification")
    report = _load_json(path.resolve())
    required = {
        "schema_version": "RQ1VisOpsSmokeQualificationV1",
        "status": "passed",
        "model": model,
        "infrastructure_failures": 0,
        "max_model_len": config["inference"]["max_model_len"],
        "max_tokens": config["inference"]["max_tokens"],
    }
    mismatches = {
        key: (report.get(key), value)
        for key, value in required.items()
        if report.get(key) != value
    }
    if config.get("contracts", {}).get("prompt_answer_contract") in {
        "type_specific_json_v2",
        "compact_task_specific_regex_v3",
    }:
        task_profile = config.get("visops", {}).get("task_profile")
        answer_types = (
            ["number", "ordered_path", "sorted_string_set"]
            if task_profile == "answer_hidden_compositional_v1"
            else ["panel_onset_ledger"]
            if task_profile in TWO_STAGE_PROFILES
            else ["directed_edge", "number", "ordered_path", "sorted_string_set"]
        )
        structured_required = {
            "structured_output_contract_verified": True,
            "answer_types_verified": answer_types,
        }
        mismatches.update(
            {
                key: (report.get(key), value)
                for key, value in structured_required.items()
                if report.get(key) != value
            }
        )
    if mismatches:
        raise ContractError(f"RQ1 smoke qualification differs: {mismatches}")
    return report


def _verify_code_freeze(
    path: Path | None,
    *,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if path is None:
        raise ContractError("execution requires --code-freeze")
    report = _load_json(path.resolve())
    required = {
        "schema_version": "RQ1CodeFreezeV1",
        "status": "frozen",
        "experiment_id": config["experiment_id"],
        "experiment_config_hash": stable_hash(config),
        "working_tree_policy": "rq1_runtime_files_match_frozen_tree_hash",
    }
    mismatches = {
        key: (report.get(key), value)
        for key, value in required.items()
        if report.get(key) != value
    }
    if mismatches:
        raise ContractError(f"RQ1 code freeze differs: {mismatches}")
    for field in ("git_commit", "runtime_tree_sha256"):
        if not isinstance(report.get(field), str) or not report[field]:
            raise ContractError(f"RQ1 code freeze lacks {field}")
    manifest = report.get("runtime_files")
    if not isinstance(manifest, dict):
        raise ContractError("RQ1 code freeze lacks runtime_files")
    actual_tree_hash = verify_runtime_manifest(manifest)
    if actual_tree_hash != report["runtime_tree_sha256"]:
        raise ContractError("RQ1 frozen runtime tree hash differs from current files")
    return report


def _verify_public_files(root: Path, record: Mapping[str, Any]) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for name, relative in dict(record["public_files"]).items():
        path = (root / str(relative)).resolve()
        if root.resolve() not in path.parents:
            raise ContractError(f"prepared public path escapes root: {path}")
        if not path.is_file():
            raise ContractError(f"prepared public artifact is absent: {path}")
        expected = str(record["public_hashes"][name])
        actual = sha256_bytes(path.read_bytes())
        if actual != expected:
            raise ContractError(f"prepared public artifact drift: {path}")
        files[name] = path
    return files


def _load_private_index(root: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(root / "private/index.json")
    if payload.get("schema_version") != "RQ1PrivateAnswerIndexV1":
        raise ContractError("unsupported private answer index")
    out: dict[str, dict[str, Any]] = {}
    for row in payload.get("records") or []:
        path = (root / str(row["answer_key"])).resolve()
        if (root / "private").resolve() not in path.parents:
            raise ContractError("answer key escaped the private artifact tree")
        query_id = str(row["query_id"])
        if query_id in out:
            raise ContractError(f"duplicate private answer index entry for {query_id}")
        out[query_id] = {
            "path": path,
            "query_hash": str(row["query_hash"]),
            "sha256": str(row["answer_key_sha256"]),
        }
    return out


def _prepared_calls(
    prepared_roots: list[Path],
    arm: str,
    *,
    config: Mapping[str, Any],
    condition: str = "main",
) -> list[dict[str, Any]]:
    task_profile = config.get("visops", {}).get("task_profile")
    if condition not in {"main", "row_sham"}:
        raise ContractError(f"unknown RQ1 visual condition {condition!r}")
    if condition == "row_sham" and task_profile not in TWO_STAGE_PROFILES:
        raise ContractError("row-sham execution is restricted to RQ1b3")
    if condition == "row_sham" and arm == "T":
        raise ContractError("row-sham is registered only for V and H")
    answer_hidden = task_profile in {
        "answer_hidden_compositional_v1",
        "two_stage_onset_ledger_v1",
        "two_stage_onset_ledger_v2",
    }
    calls: list[dict[str, Any]] = []
    for root in prepared_roots:
        root = root.resolve()
        manifest = _load_json(root / "manifest.json")
        if manifest.get("schema_version") != "RQ1PreparedVisOpsManifestV1":
            raise ContractError(f"unsupported prepared manifest under {root}")
        tasks = list(manifest.get("tasks") or [])
        if int(manifest.get("task_count", -1)) != len(tasks):
            raise ContractError(f"prepared manifest task count differs under {root}")
        if manifest.get("evidence_store", {}).get("opaque_incident_id") != manifest.get(
            "opaque_incident_id"
        ):
            raise ContractError(
                f"prepared evidence-store identity differs under {root}"
            )
        private_index = _load_private_index(root)
        for record in tasks:
            files = _verify_public_files(root, record)
            task = _load_json(files["task"])
            query = dict(task["query"])
            if query.get("query_id") != record.get("query_id"):
                raise ContractError("prepared task query ID differs from manifest")
            if query.get("query_hash") != record.get("query_hash"):
                raise ContractError("prepared task query hash differs from manifest")
            if query.get("fact_inventory_hash") != record.get("fact_inventory_hash"):
                raise ContractError(
                    "prepared task inventory hash differs from manifest"
                )
            paired_audit = _load_json(files["paired_audit"])
            if (
                paired_audit.get("schema_version") != "PairedViewAuditV1"
                or paired_audit.get("query_hash") != query.get("query_hash")
                or paired_audit.get("fact_inventory_hash")
                != query.get("fact_inventory_hash")
                or paired_audit.get("parity_ok") is not True
                or paired_audit.get("leakage_ok") is not True
                or paired_audit.get("failures")
            ):
                raise ContractError(
                    f"prepared parity/leakage audit failed for {query['query_id']}"
                )
            visual_manifest_name = (
                "visual_sham_manifest" if condition == "row_sham" else "visual_manifest"
            )
            visual_name = "visual_sham" if condition == "row_sham" else "visual"
            prompt_contract_name = (
                "prompt_contract_sham" if condition == "row_sham" else "prompt_contract"
            )
            if any(
                name not in files
                for name in (visual_manifest_name, visual_name, prompt_contract_name)
            ):
                raise ContractError(
                    f"prepared task lacks registered {condition} visual artifacts"
                )
            visual_manifest = _load_json(files[visual_manifest_name])
            answer_hidden_task = answer_hidden and str(query["family"]).startswith(
                "answer_hidden_"
            )
            onset_ledger_task = (
                task_profile in TWO_STAGE_PROFILES
                and str(query["operation"])
                in {"panel_onset_ledger_high", "panel_onset_ledger_high_compact"}
            )
            expected_visual_schema = (
                "VisualViewV6OnsetLedger"
                if onset_ledger_task
                else "VisualViewV5AnswerHidden"
                if answer_hidden_task
                else "VisualViewV4"
            )
            expected_renderer = (
                str(config["contracts"]["renderer"])
                if answer_hidden_task
                else "RQ1VisualViewV4"
            )
            if (
                visual_manifest.get("schema_version") != expected_visual_schema
                or visual_manifest.get("query_hash") != query.get("query_hash")
                or visual_manifest.get("fact_inventory_hash")
                != query.get("fact_inventory_hash")
                or visual_manifest.get("primitive_manifest", {}).get("renderer")
                != expected_renderer
            ):
                raise ContractError(
                    f"prepared visual contract failed for {query['query_id']}"
                )
            text_bytes = files["text"].read_bytes()
            png_bytes = files[visual_name].read_bytes()
            prompts = build_prompt_bundle_from_artifacts(
                operation=str(query["operation"]),
                question=str(task["question"]),
                text_bytes=text_bytes,
                png_bytes=png_bytes,
                panel_ids=panel_ids_from_public_facts(task["facts"]),
            )
            frozen_prompt = _load_json(files[prompt_contract_name])
            if prompts.public_contract() != frozen_prompt:
                raise ContractError(f"prompt contract drift for {query['query_id']}")
            answer_entry = private_index.get(str(query["query_id"]))
            if answer_entry is None or not answer_entry["path"].is_file():
                raise ContractError(
                    f"private answer key absent for {query['query_id']}"
                )
            if answer_entry["query_hash"] != query["query_hash"]:
                raise ContractError(
                    f"private answer query hash differs for {query['query_id']}"
                )
            base = {
                "prepared_root": root,
                "opaque_incident_id": manifest["opaque_incident_id"],
                "evidence_store_schema": manifest["evidence_store"]["schema_version"],
                "task": task,
                "query": query,
                "prompt_system": prompts.system,
                "answer_contract": dict(prompts.answer_contract),
                "response_format": prompts.answer_contract["response_format"],
                "response_format_sha256": prompts.answer_contract[
                    "response_format_sha256"
                ],
                "guided_regex": prompts.answer_contract.get("guided_regex"),
                "guided_regex_sha256": prompts.answer_contract.get(
                    "guided_regex_sha256"
                ),
                "answer_path": answer_entry["path"],
                "answer_key_sha256": answer_entry["sha256"],
                "visual_sha256": sha256_bytes(png_bytes),
                "text_sha256": sha256_bytes(text_bytes),
                "condition": condition,
            }
            order = _arm_order(str(manifest["opaque_incident_id"]))
            eligible_order = (
                "".join(value for value in order if value in {"V", "H"})
                if condition == "row_sham"
                else order
            )
            selected_arms = eligible_order if arm == "ALL" else arm
            for selected_arm in selected_arms:
                fragment = getattr(prompts, ARM_TO_FRAGMENT[selected_arm])
                calls.append(
                    {
                        **base,
                        "arm": selected_arm,
                        "arm_order": order,
                        "arm_order_index": order.index(selected_arm),
                        "prompt_parts": list(fragment.parts),
                        "prompt_sha256": fragment.fragment_sha256,
                    }
                )
    keys = [
        (
            row["opaque_incident_id"],
            row["query"]["query_id"],
            row["arm"],
            row["condition"],
        )
        for row in calls
    ]
    if len(keys) != len(set(keys)):
        raise ContractError("prepared roots contain duplicate incident/query units")
    return sorted(
        calls,
        key=lambda row: (
            row["opaque_incident_id"],
            row["arm_order_index"],
            row["query"]["query_id"],
        ),
    )


def _assert_execution_store_is_qualified(
    calls: list[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> None:
    required = str(config["contracts"]["canonical_source_required_for_execution"])
    actual = sorted({str(row["evidence_store_schema"]) for row in calls})
    if actual != [required]:
        raise ContractError(
            "prepared evidence store is qualification-only: "
            f"actual={actual} required={required}"
        )


def _allowed_opaque_ids(roster: Mapping[str, Any]) -> set[str]:
    out: set[str] = set()
    for row in roster.get("cases") or []:
        if isinstance(row, str):
            out.add(row)
        elif isinstance(row, Mapping):
            value = row.get("opaque_incident_id")
            if value:
                out.add(str(value))
    return out


def _verify_model_config(model: str, config: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {
        str(config["models"]["primary"]["tag"]),
        str(config["models"]["architecture_control"]["tag"]),
    }
    if model not in allowed:
        raise ContractError(f"model {model!r} is not registered for RQ1")
    model_entry = (
        config["models"]["primary"]
        if model == config["models"]["primary"]["tag"]
        else config["models"]["architecture_control"]
    )
    resolved = get_config(model)
    expected = dict(config["inference"])
    checks = {
        "max_tokens": resolved.max_tokens,
        "temperature": resolved.temperature,
        "top_p": resolved.top_p,
        "seed": resolved.seed,
        "thinking": resolved.thinking,
        "thinking_via_template": resolved.thinking_via_template,
        "request_timeout_s": resolved.request_timeout_s,
    }
    wanted = {
        "max_tokens": expected["max_tokens"],
        "temperature": expected["temperature"],
        "top_p": expected["top_p"],
        "seed": expected["seed"],
        "thinking": not bool(expected["disable_thinking"]),
        "thinking_via_template": bool(model_entry["thinking_via_template"]),
        "request_timeout_s": float(expected["request_timeout_sec"]),
    }
    if checks != wanted:
        raise ContractError(
            f"unified VLM client config differs: actual={checks} expected={wanted}"
        )
    return {
        "tag": resolved.tag,
        "backend": resolved.backend,
        "model_id": resolved.model_id,
        **checks,
    }


def _verify_server_attestation(
    path: Path | None,
    *,
    model: str,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if path is None:
        raise ContractError("execution requires --server-attestation")
    payload = _load_json(path)
    expected = dict(config["inference"])
    model_batch = (
        config["models"]["primary"]["batch_invariant"]
        if model == config["models"]["primary"]["tag"]
        else config["models"]["architecture_control"]["batch_invariant"]
    )
    model_entry = (
        config["models"]["primary"]
        if model == config["models"]["primary"]["tag"]
        else config["models"]["architecture_control"]
    )
    required = {
        "model_tag": model,
        "served_model_name": model_entry["served_model_name"],
        "dtype": "bfloat16",
        "quantization": None,
        "max_model_len": expected["max_model_len"],
        "gpu_memory_utilization": expected["gpu_memory_utilization"],
        "max_num_seqs": expected["max_num_seqs"],
        "max_images_per_prompt": expected["max_images_per_prompt"],
        "max_videos_per_prompt": expected["max_videos_per_prompt"],
        "generation_config": expected["generation_config"],
        "tensor_parallel_size": expected["tensor_parallel_size"],
        "cublas_workspace_config": expected["cublas_workspace_config"],
        "trust_remote_code": expected["trust_remote_code"],
        "enable_log_requests": expected["enable_log_requests"],
        "extra_server_args": expected["extra_server_args"],
        "enable_prefix_caching": expected["enable_prefix_caching"],
        "enable_chunked_prefill": expected["enable_chunked_prefill"],
        "async_scheduling": expected["async_scheduling"],
        "enforce_eager": expected["enforce_eager"],
        "use_flashinfer_sampler": expected["use_flashinfer_sampler"],
        "gdn_prefill_backend": expected["gdn_prefill_backend"],
        "moe_backend": expected["moe_backend"],
        "triton_force_first_config": expected["triton_force_first_config"],
        "batch_invariant": model_batch,
    }
    mismatches = {
        key: (payload.get(key), value)
        for key, value in required.items()
        if payload.get(key) != value
    }
    if mismatches:
        raise ContractError(
            f"server attestation differs from registered runtime: {mismatches}"
        )
    for field in (
        "checkpoint_manifest_sha256",
        "tokenizer_manifest_sha256",
        "vllm_version",
        "torch_version",
        "cuda_version",
        "gpu_name",
    ):
        if not payload.get(field):
            raise ContractError(
                f"server attestation lacks required provenance field {field}"
            )
    return payload


def _preflight_context_budget(
    calls: list[dict[str, Any]], *, model: str, config: Mapping[str, Any]
) -> dict[str, Any]:
    """Tokenize every prompt and freeze any paired whole-case exclusions.

    A context overflow is an infrastructure incompatibility, not a model
    answer.  To preserve pairing and information equality, one overflowing
    arm/query excludes the incident's complete T/V/H query set.  The exclusion
    remains admissible only within the experiment's preregistered whole-case
    infrastructure ceiling; no replacement case is selected.
    """

    max_model_len = int(config["inference"]["max_model_len"])
    max_tokens = int(config["inference"]["max_tokens"])
    failures: list[dict[str, Any]] = []
    for index, row in enumerate(calls, start=1):
        input_tokens = count_vllm_prompt_tokens(
            row["prompt_parts"], model, system=row["prompt_system"]
        )
        if input_tokens is None or input_tokens <= 0:
            raise ContractError(
                "live vLLM tokenizer preflight failed before model execution"
            )
        row["preflight_input_tokens"] = int(input_tokens)
        if input_tokens + max_tokens > max_model_len:
            failures.append(
                {
                    "opaque_incident_id": row["opaque_incident_id"],
                    "query_id": row["query"]["query_id"],
                    "arm": row["arm"],
                    "input_tokens": int(input_tokens),
                    "max_tokens": max_tokens,
                    "max_model_len": max_model_len,
                }
            )
        if index == len(calls) or index % max(1, len(calls) // 10) == 0:
            print(f"context preflight [{index}/{len(calls)}]", flush=True)
    requested_incidents = sorted({row["opaque_incident_id"] for row in calls})
    excluded_incidents = sorted(
        {str(failure["opaque_incident_id"]) for failure in failures}
    )
    exclusion_fraction = len(excluded_incidents) / len(requested_incidents)
    maximum_exclusion = float(
        config["integrity"][
            "maximum_paired_whole_case_infrastructure_exclusion_fraction"
        ]
    )
    if exclusion_fraction > maximum_exclusion:
        compact = [
            f"{failure['opaque_incident_id']}/{failure['query_id']}/"
            f"{failure['arm']}={failure['input_tokens']}+{failure['max_tokens']}>"
            f"{failure['max_model_len']}"
            for failure in failures
        ]
        raise ContractError(
            "paired whole-case context exclusion exceeds registered ceiling: "
            f"{len(excluded_incidents)}/{len(requested_incidents)}="
            f"{exclusion_fraction:.6f}>{maximum_exclusion:.6f}; " + "; ".join(compact)
        )
    return {
        "schema_version": "RQ1ContextPreflightV1",
        "status": "passed_with_paired_exclusions" if failures else "passed",
        "model": model,
        "max_model_len": max_model_len,
        "max_tokens": max_tokens,
        "requested_incidents": len(requested_incidents),
        "excluded_incidents": excluded_incidents,
        "excluded_incident_count": len(excluded_incidents),
        "exclusion_fraction": exclusion_fraction,
        "maximum_exclusion_fraction": maximum_exclusion,
        "overflowing_calls": failures,
        "policy": "one_overflow_excludes_complete_incident_without_replacement",
    }


def _call_contract(
    row: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    roster: Mapping[str, Any],
    model: str,
    arm: str,
    model_config: Mapping[str, Any],
    server_attestation: Mapping[str, Any],
    qualification_report: Mapping[str, Any],
    smoke_report: Mapping[str, Any] | None,
    code_freeze: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": "RQ1VisOpsCallContractV2StructuredOutput",
        "experiment_id": config["experiment_id"],
        "opaque_incident_id": row["opaque_incident_id"],
        "query_id": row["query"]["query_id"],
        "query_hash": row["query"]["query_hash"],
        "fact_inventory_hash": row["query"]["fact_inventory_hash"],
        "evidence_store_schema": row["evidence_store_schema"],
        "model": model,
        "arm": arm,
        "arm_order": row["arm_order"],
        "arm_order_index": row["arm_order_index"],
        "prompt_sha256": row["prompt_sha256"],
        "public_answer_type": row["answer_contract"]["answer_type"],
        "structured_output_transport": row["answer_contract"].get(
            "structured_output_transport", "openai_response_format_json_schema"
        ),
        "response_format_sha256": row["response_format_sha256"],
        "guided_regex_sha256": row["guided_regex_sha256"],
        "visual_sha256": row["visual_sha256"],
        "text_sha256": row["text_sha256"],
        "answer_key_sha256": row["answer_key_sha256"],
        "preflight_input_tokens": row["preflight_input_tokens"],
        "experiment_config_hash": stable_hash(config),
        "roster_contract_hash": stable_hash(roster),
        "model_config": dict(model_config),
        "server_attestation_sha256": stable_hash(server_attestation),
        "qualification_report_sha256": stable_hash(qualification_report),
        "smoke_qualification_sha256": (
            stable_hash(smoke_report) if smoke_report is not None else None
        ),
        "code_freeze_sha256": stable_hash(code_freeze),
        "git_commit": code_freeze["git_commit"],
        "runtime_tree_sha256": code_freeze["runtime_tree_sha256"],
        "roster_assignment_hash": roster["assignment_hash"],
    }
    if config.get("visops", {}).get("task_profile") in TWO_STAGE_PROFILES:
        payload["stage"] = "stage1_observe_compose"
        payload["condition"] = row["condition"]
    payload["contract_hash"] = stable_hash(payload)
    payload["call_key"] = stable_hash(
        {
            "contract_hash": payload["contract_hash"],
            "query_hash": payload["query_hash"],
            "model": model,
            "arm": arm,
        }
    )[:24]
    return payload


def _existing_call(path: Path, contract: Mapping[str, Any]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    existing = _load_json(path)
    fields = ["call_key", "contract_hash", "query_hash", "model", "arm"]
    fields.extend(field for field in ("stage", "condition") if field in contract)
    for field in fields:
        if existing.get(field) != contract.get(field):
            raise ContractError(f"resume artifact {path} differs at {field}")
    if existing.get("status") not in {"completed", "infrastructure_error"}:
        raise ContractError(f"resume artifact {path} has unknown status")
    return existing


def _write_call_artifacts(output: Path, record: Mapping[str, Any]) -> None:
    call_path = output / "calls" / f"{record['call_key']}.json"
    conversation_path = output / "conversations" / f"{record['call_key']}.md"
    _atomic_write(call_path, (canonical_json(record) + "\n").encode("utf-8"))
    conversation = (
        f"# RQ1 VisOps conversation — {record['query_id']} — {record['arm']}\n\n"
        f"- opaque incident: `{record['opaque_incident_id']}`\n"
        f"- model: `{record['model']}`\n"
        f"- stage: `{record.get('stage', 'single_stage')}`\n"
        f"- condition: `{record.get('condition', 'main')}`\n"
        f"- prompt hash: `{record['prompt_sha256']}`\n"
        f"- visual hash: `{record['visual_sha256']}`\n"
        f"- text hash: `{record['text_sha256']}`\n\n"
        "## Response\n\n"
        f"{record.get('response_text') or ''}\n"
    )
    _atomic_write(conversation_path, conversation.encode("utf-8"))


def _summarize(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    complete = [row for row in records if row.get("status") == "completed"]
    parsed = [row for row in complete if row.get("parse_ok")]
    correct = [row for row in complete if row.get("correct")]
    count = len(records)
    return {
        "requested_calls": count,
        "completed_calls": len(complete),
        "infrastructure_errors": count - len(complete),
        "error_rate": (count - len(complete)) / count if count else 0.0,
        "parse_rate": len(parsed) / len(complete) if complete else 0.0,
        "accuracy": len(correct) / len(complete) if complete else 0.0,
        "avg_input_tokens": (
            sum(int(row.get("input_tokens") or 0) for row in complete) / len(complete)
            if complete
            else 0.0
        ),
        "avg_output_tokens": (
            sum(int(row.get("output_tokens") or 0) for row in complete) / len(complete)
            if complete
            else 0.0
        ),
        "avg_wall_time_s": (
            sum(float(row.get("wall_time_s") or 0) for row in complete) / len(complete)
            if complete
            else 0.0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--roster", type=Path, default=DEFAULT_ROSTER)
    parser.add_argument("--prepared-root", type=Path, action="append", default=[])
    parser.add_argument("--prepared-index", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--arm", choices=[*sorted(ARM_TO_FRAGMENT), "ALL"], required=True
    )
    parser.add_argument("--condition", choices=["main", "row_sham"], default="main")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--server-attestation", type=Path)
    parser.add_argument("--qualification-report", type=Path)
    parser.add_argument("--smoke-qualification", type=Path)
    parser.add_argument("--code-freeze", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.execute == args.dry_run:
        raise ContractError("choose exactly one of --execute or --dry-run")

    config = load_yaml_config(args.config)
    configure_registered_vllm_environment(config)
    roster = _load_json(args.roster)
    if bool(args.prepared_root) == bool(args.prepared_index):
        raise ContractError("choose exactly one of --prepared-root or --prepared-index")
    prepared_index: dict[str, Any] | None = None
    prepared_roots = args.prepared_root
    if args.prepared_index is not None:
        prepared_roots, prepared_index = _prepared_roots_from_index(
            args.prepared_index,
            config=config,
            roster=roster,
        )
    calls = _prepared_calls(
        prepared_roots, args.arm, config=config, condition=args.condition
    )
    model_config = _verify_model_config(args.model, config)

    dry_report = {
        "status": "dry_run_passed",
        "model": args.model,
        "arm": args.arm,
        "condition": args.condition,
        "prepared_roots": len(prepared_roots),
        "incidents": len({row["opaque_incident_id"] for row in calls}),
        "calls": len(calls),
        "execution_enabled": bool(config["execution"]["enabled"]),
        "experiment_config_hash": stable_hash(config),
        "roster_contract_hash": stable_hash(roster),
        "evidence_store_schemas": sorted(
            {str(row["evidence_store_schema"]) for row in calls}
        ),
        "required_execution_store_schema": config["contracts"][
            "canonical_source_required_for_execution"
        ],
        "model_config": model_config,
    }
    if args.dry_run:
        print(json.dumps(dry_report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    assert_runner_may_execute(config, roster, explicit_execute=args.execute)
    _assert_execution_store_is_qualified(calls, config)
    if prepared_index is None:
        raise ContractError("registered execution requires a frozen --prepared-index")
    qualification = _verify_qualification_report(
        args.qualification_report,
        prepared_index=prepared_index,
        config=config,
    )
    smoke = _verify_smoke_report(
        args.smoke_qualification,
        model=args.model,
        config=config,
    )
    code_freeze = _verify_code_freeze(args.code_freeze, config=config)
    server = _verify_server_attestation(
        args.server_attestation,
        model=args.model,
        config=config,
    )
    context_preflight = _preflight_context_budget(
        calls, model=args.model, config=config
    )
    allowed = _allowed_opaque_ids(roster)
    outside = sorted({row["opaque_incident_id"] for row in calls} - allowed)
    if outside:
        raise ContractError(
            f"prepared incidents are outside the frozen roster: {outside}"
        )
    if args.output is None:
        raise ContractError("execution requires --output")
    output = args.output.resolve()
    results_root = (RQ_ROOT / "results").resolve()
    if results_root not in output.parents:
        raise ContractError("RQ1 experiment output must be below RQs/RQ1/results/")
    output.mkdir(parents=True, exist_ok=True)
    _atomic_write(
        output / "context_preflight.json",
        (
            json.dumps(context_preflight, ensure_ascii=False, sort_keys=True, indent=2)
            + "\n"
        ).encode("utf-8"),
    )

    records: list[dict[str, Any]] = []
    pending: list[Future[None]] = []
    excluded_context_incidents = set(context_preflight["excluded_incidents"])
    started = time.time()
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="rq1-writer") as writer:
        for index, row in enumerate(calls, start=1):
            contract = _call_contract(
                row,
                config=config,
                roster=roster,
                model=args.model,
                arm=row["arm"],
                model_config=model_config,
                server_attestation=server,
                qualification_report=qualification,
                smoke_report=smoke,
                code_freeze=code_freeze,
            )
            call_path = output / "calls" / f"{contract['call_key']}.json"
            existing = _existing_call(call_path, contract)
            if existing is not None:
                records.append(existing)
                continue
            if row["opaque_incident_id"] in excluded_context_incidents:
                record = {
                    **contract,
                    "status": "infrastructure_error",
                    "operation": row["query"]["operation"],
                    "family": row["query"]["family"],
                    "response_text": "",
                    "predicted_answer": None,
                    "parse_ok": False,
                    "correct": False,
                    "score": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "wall_time_s": 0.0,
                    "model_latency_s": 0.0,
                    "gpu_active_time_s": 0.0,
                    "peak_gpu_memory_bytes": None,
                    "gpu_accounting_samples": 0,
                    "gpu_accounting_method": "not sampled: preflight exclusion",
                    "finish_reason": None,
                    "truncated": False,
                    "error": (
                        "ContextBudgetExceeded: incident excluded as a complete "
                        "paired case before model execution"
                    ),
                }
                records.append(record)
                pending.append(writer.submit(_write_call_artifacts, output, record))
                continue
            t0 = time.time()
            gpu_accounting = _GPUAccounting()
            try:
                with gpu_accounting:
                    response = call_vlm(
                        row["prompt_parts"],
                        model=args.model,
                        system=row["prompt_system"],
                        max_retries=int(config["inference"]["retry_attempts"]),
                        response_format=row["response_format"],
                        guided_regex=row["guided_regex"],
                    )
                gpu_report = gpu_accounting.report()
                predicted, parse_ok = parse_visops_response(response.text)
                # Load evaluator-private truth only after the model response exists.
                answer_key = _load_json(row["answer_path"])
                if (
                    answer_key.get("schema_version") != "PrivateAnswerKeyV1"
                    or answer_key.get("query_id") != row["query"]["query_id"]
                    or answer_key.get("query_hash") != row["query"]["query_hash"]
                    or sha256_bytes(row["answer_path"].read_bytes())
                    != row["answer_key_sha256"]
                ):
                    raise ContractError(
                        "private answer key drifted or belongs to another query"
                    )
                scored = (
                    score_visops_answer(predicted, answer_key)
                    if parse_ok
                    else {
                        "correct": False,
                        "score": 0.0,
                        "answer_type": answer_key.get("answer_type"),
                    }
                )
                finish_reason = (response.raw or {}).get("finish_reason") or (
                    response.raw or {}
                ).get("stopReason")
                record = {
                    **contract,
                    "status": "completed",
                    "operation": row["query"]["operation"],
                    "family": row["query"]["family"],
                    "response_text": response.text,
                    "predicted_answer": predicted,
                    "parse_ok": parse_ok,
                    "correct": scored["correct"],
                    "score": scored["score"],
                    "answer_type": scored["answer_type"],
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "total_tokens": response.total_tokens,
                    "wall_time_s": time.time() - t0,
                    "model_latency_s": response.latency_s,
                    **gpu_report,
                    "finish_reason": finish_reason,
                    "truncated": finish_reason in {"length", "max_tokens"},
                    "error": None,
                }
            except Exception as exc:  # noqa: BLE001 - persisted infrastructure boundary
                try:
                    gpu_report = gpu_accounting.report()
                except Exception:  # noqa: BLE001 - preserve primary failure
                    gpu_report = {
                        "gpu_active_time_s": None,
                        "peak_gpu_memory_bytes": None,
                        "gpu_accounting_samples": 0,
                        "gpu_accounting_method": "NVML accounting unavailable",
                    }
                record = {
                    **contract,
                    "status": "infrastructure_error",
                    "operation": row["query"]["operation"],
                    "family": row["query"]["family"],
                    "response_text": "",
                    "predicted_answer": None,
                    "parse_ok": False,
                    "correct": False,
                    "score": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "wall_time_s": time.time() - t0,
                    "model_latency_s": 0.0,
                    **gpu_report,
                    "finish_reason": None,
                    "truncated": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            records.append(record)
            pending.append(writer.submit(_write_call_artifacts, output, record))
            interval = max(1, len(calls) // 20)
            if index == len(calls) or index % interval == 0:
                current = _summarize(records)
                print(
                    f"[{index}/{len(calls)}] parse={current['parse_rate']:.3f} "
                    f"accuracy={current['accuracy']:.3f} errors={current['error_rate']:.3f}",
                    flush=True,
                )
        for future in pending:
            future.result()

    summary = {
        "schema_version": "RQ1VisOpsCellSummaryV1",
        "experiment_id": config["experiment_id"],
        "model": args.model,
        "arm": args.arm,
        "condition": args.condition,
        "arm_order_policy": "balanced_by_opaque_incident_hash",
        "per_arm": {
            arm: _summarize([record for record in records if record.get("arm") == arm])
            for arm in sorted(ARM_TO_FRAGMENT)
            if any(record.get("arm") == arm for record in records)
        },
        "experiment_config_hash": stable_hash(config),
        "roster_contract_hash": stable_hash(roster),
        "roster_assignment_hash": roster["assignment_hash"],
        "context_preflight": context_preflight,
        "elapsed_wall_time_s": time.time() - started,
        **_summarize(records),
    }
    _atomic_write(
        output / "summary.json",
        (
            json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8"),
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

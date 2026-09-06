"""Resumable RQ2 prepare, inference, analysis, and verification engine."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import multiprocessing as mp
import os
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, wait
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from unified_scripts import canonical_json, stable_hash
from unified_scripts.dataset_segmentation import CaseRecord, DatasetSegmentationConfig
from unified_scripts.vllm_inference import VLLMInferenceConfig
from vlmrca.vlm.attention_probe import (
    image_attention_diagnostics,
    map_groups_to_images,
    map_text_attention,
    render_overlay,
    warm_mapping_tokenizer,
)
from vlmrca.vlm.client import VLMResponse, call_vlm, count_vllm_prompt_tokens
from vlmrca.vlm.configs import get_config
from vlmrca.vlm.performance import RuntimePerformanceMonitor

from .exps import (
    DENSE_CONTENT_POLICY,
    EXPERIMENT_CONTENT_POLICIES,
    TOOL_PROFILES,
    TRANSFER_ARMS,
    DashboardSpecV1,
    PreparedCase,
    RCA_SYSTEM_ROLE,
    REGIONS,
    build_twins,
    build_tool_packet,
    factorial_parts,
    filter_packet,
    ground_reason,
    make_dashboard_spec,
    packed_operations,
    packed_qa_schema,
    prepare_case,
    rca_schema,
    rq2_qa_parts,
    rq2_rca_parts,
    score_packed_qa,
    transfer_parts,
    twin_parts,
    validate_diagnosis,
)
from .gates import analyze_records, verify_result_root
from .renderer.designs import (
    ComposerStateV1,
    build_evidence_cards,
    compile_composer_sft_example,
    compile_dashboard_program,
    policy_regions,
    space_filling_specs,
)
from .utils import (
    AsyncWriter,
    DEFAULT_CONFIG,
    ROOT,
    RQ2Error,
    RunPaths,
    atomic_write,
    load_yaml,
    materialize_v3_rosters,
    parse_json_object,
    scorer,
    write_json,
)

SOURCE_ROOT = ROOT / "RQs" / "RQ2" / "src"
ABANDONED_TASKS = frozenset({"packed_qa"})


def _active_tasks(config: Mapping[str, Any], experiment: str) -> tuple[str, ...]:
    """Return tasks registered for execution; retained QA code is inactive."""

    tasks = tuple(map(str, config["experiments"][experiment]["tasks"]))
    forbidden = ABANDONED_TASKS.intersection(tasks)
    if forbidden:
        raise RQ2Error(f"abandoned RQ2 tasks cannot be scheduled: {sorted(forbidden)}")
    if not tasks or any(task != "one_stage_rca" for task in tasks):
        raise RQ2Error(f"RQ2 active task registry must be RCA-only, got {tasks}")
    return tasks


def _vllm_config_path(config: Mapping[str, Any]) -> str:
    """Use the registered deployment profile without changing model settings."""

    return os.environ.get("CANVASRCA_VLLM_CONFIG", str(config["unified"]["vllm"]))


def _load_roster(path: Path, config: Mapping[str, Any]) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = [
        {"dataset": str(row.get("dataset") or dataset), **dict(row)}
        for dataset, values in payload.get("datasets", {}).items()
        for row in values
    ]
    if not rows:
        rows = list(payload.get("cases") or ())
    segmentation = DatasetSegmentationConfig.load(config["unified"]["segmentation"])
    result = []
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("dataset") or not row.get("case_id"):
            raise RQ2Error("preparation requires the evaluator-private roster with case IDs")
        dataset, case_id = str(row["dataset"]), str(row["case_id"])
        expected = segmentation.opaque_id(CaseRecord(dataset, case_id, Path(".")))
        opaque = str(row.get("opaque_incident_id") or expected)
        if opaque != expected:
            raise RQ2Error(f"roster opaque ID mismatch for {dataset}/{case_id}")
        result.append({"dataset": dataset, "case_id": case_id, "opaque_incident_id": opaque})
    return result


def _code_hashes() -> dict[str, str]:
    # Renderer sources have their own explicit contract section below. Keeping
    # this map to the six RQ package modules avoids recording identical hashes
    # twice while preserving the semantic renderer boundary.
    paths = sorted(SOURCE_ROOT.glob("*.py"))
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def _run_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    vllm_config = VLLMInferenceConfig.load(_vllm_config_path(config))
    if vllm_config.data["deployment"]["profile"] != "local":
        raise RQ2Error("DD-118 permits RQ2 execution only through the local WSL profile")
    launcher = "serve_canvasrca_local.sh"
    shared_runtime_sources = [
        ROOT / "src/unified_scripts/__init__.py",
        ROOT / "src/unified_scripts/dataset_segmentation.py",
        ROOT / "src/unified_scripts/rca_scorer.py",
        ROOT / "src/unified_scripts/vllm_inference.py",
        ROOT / "src/vlmrca/evidence.py",
        ROOT / "src/vlmrca/processed.py",
        ROOT / "src/vlmrca/upstream.py",
        ROOT / "src/vlmrca/eval/scoring.py",
        ROOT / "src/vlmrca/vlm/client.py",
        ROOT / "src/vlmrca/vlm/performance.py",
        ROOT / "src/vlmrca/vlm/attention_probe.py",
        ROOT / "src/vlmrca/vlm/attention_probe_bootstrap/sitecustomize.py",
        ROOT / "src/vlmrca/vlm/configs.py",
        ROOT / "src/vlmrca/vlm/runtime_contract.py",
        ROOT / "scripts/vllm_vlm/enable_attention_probe.sh",
        ROOT / "scripts/vllm_vlm" / launcher,
    ]
    unified_sources = {
        key: (vllm_config.source if key == "vllm" else ROOT / path)
        for key, path in config["unified"].items()
    }
    value = {
        "schema_version": "RQ2RunContractV1",
        "rq_config_sha256": stable_hash(config),
        "unified_config_sha256": {
            key: hashlib.sha256(path.read_bytes()).hexdigest()
            for key, path in unified_sources.items()
        },
        "unified_config_source": {
            key: str(path.relative_to(ROOT)) for key, path in unified_sources.items()
        },
        "deployment_profile": str(vllm_config.data["deployment"]["profile"]),
        "code_sha256": _code_hashes(),
        "shared_runtime_source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in shared_runtime_sources
        },
        "renderer_source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((SOURCE_ROOT / "renderer").rglob("*.py"))
        },
        "external_commits": {
            name: str(row["commit"])
            for name, row in (config.get("external_methods") or {}).items()
            if isinstance(row, Mapping) and row.get("commit")
        },
        "old_rq2_lineage_used": False,
    }
    value["contract_sha256"] = stable_hash(value)
    return value


def _persist_prepared(paths: RunPaths, prepared: PreparedCase) -> dict[str, Any]:
    opaque = str(prepared.public["opaque_incident_id"])
    public_path = paths.prepared / f"{opaque}.json"
    private_path = paths.private / f"{opaque}.json"
    full_path = paths.renders / f"{opaque}.dashboard.png"
    write_json(public_path, prepared.public)
    write_json(private_path, prepared.private)
    atomic_write(full_path, prepared.full_png)
    screenshot_paths = []
    for page, image in enumerate(prepared.screenshot_pngs, 1):
        path = paths.renders / f"{opaque}.screenshot-{page:02d}.png"
        atomic_write(path, image)
        screenshot_paths.append(path)
    return {
        "opaque_incident_id": opaque,
        "public": str(public_path.relative_to(paths.root)),
        "private": str(private_path.relative_to(paths.root)),
        "full_image": str(full_path.relative_to(paths.root)),
        "screenshot_images": [str(path.relative_to(paths.root)) for path in screenshot_paths],
        "public_sha256": hashlib.sha256(public_path.read_bytes()).hexdigest(),
        "private_sha256": hashlib.sha256(private_path.read_bytes()).hexdigest(),
        "full_image_sha256": hashlib.sha256(prepared.full_png).hexdigest(),
        "screenshot_image_sha256": [hashlib.sha256(value).hexdigest() for value in prepared.screenshot_pngs],
    }


def _prepare_roster_row(row: Mapping[str, str], config: Mapping[str, Any]) -> PreparedCase:
    """Compile one renderer-heavy case in an isolated process."""

    return prepare_case(row["dataset"], row["case_id"], config, row["opaque_incident_id"])


def _write_prepared_index(
    paths: RunPaths,
    experiment_id: str,
    entries: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
    *,
    complete: bool,
) -> dict[str, Any]:
    index = {
        "schema_version": "RQ2PreparedIndexV1",
        "experiment_id": experiment_id,
        "case_count": len(entries),
        "cases": sorted((dict(row) for row in entries), key=lambda row: row["opaque_incident_id"]),
        "run_contract": dict(contract),
        "preparation_complete": complete,
    }
    index["index_sha256"] = stable_hash(index)
    write_json(paths.prepared / ("index.json" if complete else "index.partial.json"), index)
    return index


def _resume_entries(
    paths: RunPaths, run_id: str, contract: Mapping[str, Any], expected: set[str],
) -> list[dict[str, Any]]:
    final, partial = paths.prepared / "index.json", paths.prepared / "index.partial.json"
    source = final if final.is_file() else partial if partial.is_file() else None
    if source is None:
        return []
    index = json.loads(source.read_text())
    recorded = index.get("index_sha256"); unsigned = dict(index); unsigned.pop("index_sha256", None)
    if recorded != stable_hash(unsigned) or index.get("experiment_id") != run_id:
        raise RQ2Error(f"invalid resumable prepared index: {source}")
    if (index.get("run_contract") or {}).get("contract_sha256") != contract.get("contract_sha256"):
        raise RQ2Error("prepared resume contract differs; use a new result ID or explicit compatibility audit")
    entries = list(index.get("cases") or ()); ids = [str(row.get("opaque_incident_id")) for row in entries]
    if index.get("case_count") != len(entries) or len(ids) != len(set(ids)) or not set(ids) <= expected:
        raise RQ2Error("prepared resume index contains duplicate or out-of-roster cases")
    for item in entries:
        _read_prepared(paths, item)
    if index.get("preparation_complete") and set(ids) != expected:
        raise RQ2Error("complete prepared index does not cover its assigned roster")
    return entries


def prepare(
    *, experiment_id: str, roster: Path, config_path: Path = DEFAULT_CONFIG,
    limit: int | None = None, output_shard_count: int = 1,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    rows = _load_roster(roster, config)
    if limit is not None:
        rows = rows[:limit]
    if output_shard_count < 1:
        raise RQ2Error("output shard count must be positive")
    contract = _run_contract(config)
    ids = [
        experiment_id if output_shard_count == 1 else f"{experiment_id}__shard-{index:04d}-of-{output_shard_count:04d}"
        for index in range(output_shard_count)
    ]
    paths = [RunPaths.build(value, config) for value in ids]
    assignments = {
        row["opaque_incident_id"]: int(hashlib.sha256(row["opaque_incident_id"].encode()).hexdigest(), 16)
        % output_shard_count
        for row in rows
    }
    workers = int(config["runtime"]["max_workers"])
    cpu_ids = _physical_cpu_ids(workers)
    expected = [
        {str(row["opaque_incident_id"]) for row in rows if assignments[row["opaque_incident_id"]] == shard}
        for shard in range(output_shard_count)
    ]
    entries = [
        _resume_entries(path, run_id, contract, wanted)
        for path, run_id, wanted in zip(paths, ids, expected, strict=True)
    ]
    done = {str(row["opaque_incident_id"]) for values in entries for row in values}
    row_iter = iter(row for row in rows if str(row["opaque_incident_id"]) not in done)
    # Matplotlib renderer state is process-global and is not thread-safe. Keep
    # one renderer task per isolated process in flight and persist every case
    # immediately so an interrupted local preparation remains resumable.
    # ``spawn`` is required here: the parent imports matplotlib plus numerical
    # runtimes before preparation.  Forking that process can inherit native
    # font/BLAS locks and leave workers sleeping forever on a futex.
    with ProcessPoolExecutor(
        max_workers=workers, mp_context=mp.get_context("spawn"),
        initializer=_pin_materializer, initargs=(cpu_ids,),
    ) as pool:
        futures = {
            pool.submit(_prepare_roster_row, row, config): row
            for row in itertools.islice(row_iter, workers)
        }
        while futures:
            finished, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in finished:
                row = futures.pop(future)
                prepared = future.result()
                shard = assignments[row["opaque_incident_id"]]
                entries[shard].append(_persist_prepared(paths[shard], prepared))
                _write_prepared_index(paths[shard], ids[shard], entries[shard], contract, complete=False)
                next_row = next(row_iter, None)
                if next_row is not None:
                    futures[pool.submit(_prepare_roster_row, next_row, config)] = next_row
    summaries = []
    for run_id, run_paths, values in zip(ids, paths, entries, strict=True):
        index = _write_prepared_index(run_paths, run_id, values, contract, complete=True)
        (run_paths.prepared / "index.partial.json").unlink(missing_ok=True)
        summaries.append({"experiment_id": run_id, "case_count": len(values), "index_sha256": index["index_sha256"]})
    return {"experiment_id": experiment_id, "case_count": len(rows), "shards": summaries}


def _read_prepared(paths: RunPaths, item: Mapping[str, Any]) -> PreparedCase:
    public_path, private_path = paths.root / item["public"], paths.root / item["private"]
    if hashlib.sha256(public_path.read_bytes()).hexdigest() != item["public_sha256"]:
        raise RQ2Error("prepared public artifact hash mismatch")
    if hashlib.sha256(private_path.read_bytes()).hexdigest() != item["private_sha256"]:
        raise RQ2Error("prepared private artifact hash mismatch")
    full = (paths.root / item["full_image"]).read_bytes()
    screenshots = tuple((paths.root / path).read_bytes() for path in item["screenshot_images"])
    if (
        hashlib.sha256(full).hexdigest() != item["full_image_sha256"]
        or [hashlib.sha256(value).hexdigest() for value in screenshots]
        != item["screenshot_image_sha256"]
    ):
        raise RQ2Error("prepared image artifact hash mismatch")
    return PreparedCase(
        json.loads(public_path.read_text()), json.loads(private_path.read_text()), full, screenshots
    )


def _parse(text: str) -> dict[str, Any]:
    return parse_json_object(text)


def _normalize_model_output(
    raw: str, validator: Any, fallback: Mapping[str, Any]
) -> tuple[dict[str, Any], str | None]:
    """Normalize a model answer without turning answer mistakes into infra failures."""

    try:
        return dict(validator(_parse(raw))), None
    except (RQ2Error, KeyError, TypeError, ValueError) as error:
        return dict(fallback), f"{type(error).__name__}: {error}"


def _finish_reason(response: VLMResponse) -> str:
    return str((response.raw or {}).get("finish_reason") or "unknown")


def _call(
    *, model: str, system: str, parts: list[dict[str, Any]], schema: Mapping[str, Any],
    config: Mapping[str, Any], partial_root: Path | None, metadata: Mapping[str, Any],
    attention_root: Path,
    after_response: Any | None = None,
) -> tuple[dict[str, Any], str]:
    adapter = config["inference_adapter"]
    model_cfg = get_config(model, max_tokens=int(adapter["max_tokens"]))
    vllm_config = VLLMInferenceConfig.load(_vllm_config_path(config))
    context = int(vllm_config.model(model)["max_model_len"])
    prompt_tokens = count_vllm_prompt_tokens(parts, model_cfg, system=system)
    text_tokens = count_vllm_prompt_tokens(parts, model_cfg, system=system, text_only=True)
    if prompt_tokens is None or text_tokens is None:
        raise RQ2Error("live tokenizer preflight failed")
    if prompt_tokens + model_cfg.max_tokens > context:
        raise RQ2Error(f"prompt plus output budget exceeds context: {prompt_tokens}+{model_cfg.max_tokens}>{context}")
    started = time.time()
    response = call_vlm(
        parts, model=model_cfg, system=system, max_retries=1,
        response_format=dict(schema), partial_output_dir=partial_root,
        partial_metadata=dict(metadata), record_performance=True,
    )
    if after_response is not None:
        after_response()
    finish = _finish_reason(response)
    request_id = str((response.raw or {}).get("request_id") or "")
    probe = (response.raw or {}).get("attention_probe")
    if not request_id or not isinstance(probe, Mapping):
        raise RQ2Error("request completed without required same-prefill multimodal attention")
    call_root = attention_root / hashlib.sha256(request_id.encode()).hexdigest()
    call_root.mkdir(parents=True, exist_ok=True)
    raw_path = call_root / "raw_probe.json"
    text_path = call_root / "text_attention.json"
    write_json(raw_path, probe)
    text_attention = map_text_attention(
        probe, vllm_config.model_path(model), system, parts,
    )
    if text_attention["unmatched_sources"]:
        raise RQ2Error(f"attention text-span mapping failed: {text_attention['unmatched_sources']}")
    write_json(text_path, text_attention)
    images = [(part, part["png"]) for part in parts if part["type"] == "image"]
    effective_model = vllm_config.model(model)
    mapped = map_groups_to_images(
        probe, [png for _, png in images],
        model_path=vllm_config.model_path(model),
        mm_processor_kwargs=effective_model.get("mm_processor_kwargs"),
    ) if images else []
    image_artifacts = []
    for index, ((part, png), artifact) in enumerate(zip(images, mapped, strict=True)):
        artifact = {**artifact, "diagnostics": image_attention_diagnostics(artifact, part, REGIONS)}
        grid_path = call_root / f"image_{index:02d}.json"
        overlay_path = call_root / f"image_{index:02d}.png"
        overlay = render_overlay(png, artifact)
        write_json(grid_path, artifact); atomic_write(overlay_path, overlay)
        image_artifacts.append({
            "image_index": index,
            "image_sha256": artifact["image_sha256"],
            "semantic_region": artifact["diagnostics"]["semantic_region"],
            "source_visual_tokens": artifact["source_visual_tokens"],
            "global_attention_mass": artifact["global_attention_mass"],
            "attention_peak_diagnostics": artifact["attention_peak_diagnostics"],
            "value_norm_peak_diagnostics": artifact["value_norm_peak_diagnostics"],
            "weighted_value_peak_diagnostics": artifact["weighted_value_peak_diagnostics"],
            "diagnostics": artifact["diagnostics"],
            "grid_path": str(grid_path.relative_to(attention_root.parents[2])),
            "overlay_path": str(overlay_path.relative_to(attention_root.parents[2])),
            "grid_sha256": stable_hash(artifact),
            "overlay_sha256": hashlib.sha256(overlay).hexdigest(),
        })
    generation_record: dict[str, Any] = {"status": "not_captured"}
    generation = probe.get("generation_target_attention")
    if isinstance(generation, Mapping) and generation.get("status") == "collected":
        target_probe = {
            **generation,
            "request_id": probe["request_id"], "model": probe["model"],
            "layer_name": probe["layer_name"], "image_token_id": probe["image_token_id"],
        }
        target_text = map_text_attention(
            target_probe, vllm_config.model_path(model), system, parts,
        )
        if target_text["unmatched_sources"]:
            raise RQ2Error(
                f"generation attention text-span mapping failed: {target_text['unmatched_sources']}"
            )
        target_text_path = call_root / "generation_target_text_attention.json"
        write_json(target_text_path, target_text)
        target_mapped = map_groups_to_images(
            target_probe, [png for _, png in images],
            model_path=vllm_config.model_path(model),
            mm_processor_kwargs=effective_model.get("mm_processor_kwargs"),
        ) if images else []
        target_images = []
        for index, ((part, png), artifact) in enumerate(zip(images, target_mapped, strict=True)):
            artifact = {**artifact, "diagnostics": image_attention_diagnostics(artifact, part, REGIONS)}
            grid_path = call_root / f"generation_target_image_{index:02d}.json"
            overlay_path = call_root / f"generation_target_image_{index:02d}.png"
            overlay = render_overlay(png, artifact)
            write_json(grid_path, artifact); atomic_write(overlay_path, overlay)
            target_images.append({
                "image_index": index, "image_sha256": artifact["image_sha256"],
                "semantic_region": artifact["diagnostics"]["semantic_region"],
                "source_visual_tokens": artifact["source_visual_tokens"],
                "global_attention_mass": artifact["global_attention_mass"],
                "diagnostics": artifact["diagnostics"],
                "grid_path": str(grid_path.relative_to(attention_root.parents[2])),
                "overlay_path": str(overlay_path.relative_to(attention_root.parents[2])),
                "grid_sha256": stable_hash(artifact),
                "overlay_sha256": hashlib.sha256(overlay).hexdigest(),
            })
        generation_record = {
            "status": "collected", "method": generation["method"],
            "target_fields": list(generation["target_fields"]),
            "target_token_count": int(generation["target_token_count"]),
            "target_token_seen": int(generation.get("target_token_seen") or generation["target_token_count"]),
            "target_token_attention_truncated": bool(generation.get("target_token_attention_truncated", False)),
            "target_token_ids": list(generation["target_token_ids"]),
            "target_token_text": list(generation["target_token_text"]),
            "visual_attention_mass": generation["visual_attention_mass"],
            "nonvisual_attention_mass": generation["nonvisual_attention_mass"],
            "text_regions": target_text["regions"],
            "text_mapping_coverage": target_text["mapping_coverage"],
            "text_attention_path": str(target_text_path.relative_to(attention_root.parents[2])),
            "text_attention_sha256": stable_hash(target_text),
            "image_artifacts": target_images,
            "same_generation_call": True, "extra_model_calls": 0,
            "correlational_only": True,
        }
    attention_record = {
        "status": "collected_same_prefill",
        "request_id": request_id,
        "method": probe["method"],
        "layer_name": probe["layer_name"],
        "visual_attention_mass": probe["visual_attention_mass"],
        "nonvisual_attention_mass": probe["nonvisual_attention_mass"],
        "text_mapping_coverage": text_attention["mapping_coverage"],
        "text_regions": text_attention["regions"],
        "raw_probe_path": str(raw_path.relative_to(attention_root.parents[2])),
        "raw_probe_sha256": stable_hash(probe),
        "text_attention_path": str(text_path.relative_to(attention_root.parents[2])),
        "text_attention_sha256": stable_hash(text_attention),
        "image_artifacts": image_artifacts,
        "generation_target_attention": generation_record,
        "extra_model_calls": 0,
        "same_prefill": True,
        "correlational_only": True,
        "causal_claim_authorized": False,
    }
    record = {
        "request_id": request_id,
        "system": system,
        "parts": [
            {"type": "text", "text": part["text"]} if part["type"] == "text" else
            {"type": "image", "sha256": hashlib.sha256(part["png"]).hexdigest(), "bytes": len(part["png"])}
            for part in parts
        ],
        "response_text": response.text,
        "input_tokens": response.input_tokens,
        "text_tokens": text_tokens,
        "image_tokens": prompt_tokens - text_tokens,
        "output_tokens": response.output_tokens,
        "total_tokens": response.total_tokens,
        "requested_max_tokens": model_cfg.max_tokens,
        "context_limit": context,
        "wall_time_s": time.time() - started,
        "model_latency_s": response.latency_s,
        "performance": response.performance,
        "finish_reason": finish,
        "truncated": finish.casefold() in {"length", "max_tokens", "max_output_tokens"},
        "attention_probe": attention_record,
    }
    return record, response.text


def _score_rca(prediction: Mapping[str, Any], private: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    inverse = dict(private["numeric_to_natural"])
    natural = [inverse[value] for value in prediction.get("services", ()) if value in inverse]
    result = scorer(config).score(natural, list(private["accepted_labels"])).as_dict()
    return {**result, "numeric_predictions": list(prediction.get("services", ())), "natural_predictions": natural}


def _conversation_header(experiment: str, model: str, opaque: str, arm: str) -> list[str]:
    return [f"# RQ2 {experiment}\n", f"- model: `{model}`\n- case: `{opaque}`\n- arm: `{arm}`\n"]


def _append_call(conversation: list[str], title: str, call: Mapping[str, Any]) -> None:
    conversation.extend([
        f"\n## {title}\n", "### System\n", str(call["system"]), "\n### User parts\n",
        canonical_json(call["parts"]), "\n### Raw response\n", str(call["response_text"]), "\n",
    ])


def _default_spec(config: Mapping[str, Any], packet: Mapping[str, Any]) -> DashboardSpecV1:
    factors = config["design_space"]["factors"]
    row = {key: values[0] for key, values in factors.items()}
    parent = hashlib.sha256(
        (ROOT / config["renderer"]["parent_provenance"]).read_bytes()
    ).hexdigest()
    return make_dashboard_spec(row, packet, parent)


def _load_selection(
    path: Path | None, config: Mapping[str, Any], packet: Mapping[str, Any], smoke: bool,
) -> tuple[DashboardSpecV1, str]:
    if path is None:
        if not smoke:
            raise RQ2Error("formal content/transfer execution requires a frozen selection artifact")
        return _default_spec(config, packet), "FULL"
    payload = json.loads(path.read_text())
    if payload.get("schema_version") != "CanvasRCARQ2SelectionV1":
        raise RQ2Error("unsupported RQ2 selection artifact")
    spec = DashboardSpecV1(**payload["d_star"])
    return spec, str(payload.get("c_star_policy") or "FULL")


def _unit_plan(
    experiment: str, prepared: PreparedCase, config: Mapping[str, Any], model: str,
    *, smoke: bool, selection_artifact: Path | None,
) -> list[dict[str, Any]]:
    packet = prepared.public["packet"]
    d_star, c_star = _load_selection(
        selection_artifact, config, packet,
        smoke or experiment == "exp_equal_fact_design",
    )
    active_tasks = _active_tasks(config, experiment)
    if experiment == "exp_equal_fact_design":
        parent = d_star.renderer_parent_hash
        registered = config["design_space"]["sampling"]
        specs = list(space_filling_specs(
            parent, packet["fact_inventory_hash"], seed=int(config["seed"]),
            points=int(registered["points"]),
            candidate_pool_size=int(registered["candidate_pool_size"]),
        ))
        if selection_artifact is not None and not smoke:
            frozen = json.loads(selection_artifact.read_text())
            wanted = set(map(str, frozen.get("confirmation_design_ids") or ()))
            if not wanted:
                raise RQ2Error("independent design run requires frozen confirmation_design_ids")
            specs = [spec for spec in specs if spec.cell_id in wanted]
            if {spec.cell_id for spec in specs} != wanted:
                raise RQ2Error("frozen confirmation design IDs do not match the registered panel")
        if smoke:
            wanted = set(config["smoke_plans"][experiment]["space_covering_design_ids"])
            specs = [spec for spec in specs if spec.cell_id in wanted]
        return [
            {"unit_id": f"{spec.cell_id}__{task}", "task": task, "spec": spec}
            for spec in specs for task in active_tasks
        ]
    if experiment == "exp_content_budget_twins":
        units = []
        d_alt = None
        if selection_artifact is not None:
            selection = json.loads(selection_artifact.read_text())
            if selection.get("d_alt"):
                d_alt = DashboardSpecV1(**selection["d_alt"])
        combinations = tuple(
            (twin, task)
            for twin in ("text", "canvas_reflow")
            for task in active_tasks
        )
        policies = EXPERIMENT_CONTENT_POLICIES
        if smoke:
            # Nine cells/model keep the shared smoke at 18 calls. Staggered
            # windows cover every registered policy, including dense M24.
            policies = (
                EXPERIMENT_CONTENT_POLICIES[:9]
                if model.startswith("qwen") else EXPERIMENT_CONTENT_POLICIES[-9:]
            )
        for policy_index, policy in enumerate(policies):
            selected = combinations
            if smoke:
                # Every model touches all nine policies. Across policies each
                # model covers both tasks and twins; the second model uses the
                # opposite transport for the same policy.
                offset = 0 if model.startswith("qwen") else 2
                selected = (combinations[(policy_index + offset) % len(combinations)],)
            units.extend(
                {"unit_id": f"{policy}__{twin}__{task}", "task": task,
                 "policy": policy, "twin": twin, "spec": d_star}
                for twin, task in selected
            )
            if not smoke and policy.startswith("B50_"):
                units.extend(
                    {"unit_id": f"{policy}__canvas_blank__{task}", "task": task,
                     "policy": policy, "twin": "canvas_blank", "spec": d_star}
                    for task in active_tasks
                )
                if d_alt is not None:
                    units.append({
                        "unit_id": f"{policy}__canvas_alt__one_stage_rca",
                        "task": "one_stage_rca", "policy": policy,
                        "twin": "canvas_alt", "spec": d_alt,
                    })
        return units
    if experiment == "exp_downstream_transfer":
        if active_tasks != ("one_stage_rca",):
            raise RQ2Error("downstream transfer is registered for one-stage RCA only")
        arms = TRANSFER_ARMS
        if smoke:
            arms = (
                TRANSFER_ARMS[:9]
                if model.startswith("qwen") else TRANSFER_ARMS[-9:]
            )
        return [
            {"unit_id": arm, "task": "one_stage_rca", "arm": arm,
             "spec": d_star, "policy": c_star}
            for arm in arms
        ]
    if experiment == "exp_tool_representation":
        if active_tasks != ("one_stage_rca",):
            raise RQ2Error("tool representation is registered for one-stage RCA only")
        return [
            {
                "unit_id": f"{profile}__{transport}", "task": "one_stage_rca",
                "tool_profile": profile, "tool_transport": transport, "spec": d_star,
            }
            for profile in TOOL_PROFILES for transport in ("text", "canvas")
        ]
    raise RQ2Error(f"unknown RQ2 experiment {experiment}")


def _evidence_for_unit(
    experiment: str, unit: Mapping[str, Any], prepared: PreparedCase,
) -> tuple[list[dict[str, Any]], Mapping[str, Any] | None, str]:
    if experiment == "exp_equal_fact_design":
        parts, manifest = factorial_parts(prepared, unit["spec"])
        return parts, manifest, "rq2_dashboard"
    if experiment == "exp_content_budget_twins":
        packing_mode = "blank" if unit["twin"] == "canvas_blank" else "reflow"
        twin = build_twins(prepared, unit["spec"], unit["policy"], packing_mode)
        return (
            twin_parts(prepared, twin, "text" if unit["twin"] == "text" else "canvas"),
            twin.canvas_manifest if unit["twin"] != "text" else None,
            "rq2_dashboard" if unit["twin"] != "text" else "text",
        )
    if experiment == "exp_tool_representation":
        packet = build_tool_packet(prepared.public["packet"], str(unit["tool_profile"]))
        twin = build_twins(prepared, unit["spec"], "FULL", source_packet_override=packet)
        transport = str(unit["tool_transport"])
        return (
            twin_parts(prepared, twin, transport),
            twin.canvas_manifest if transport == "canvas" else None,
            "rq2_dashboard" if transport == "canvas" else "text",
        )
    parts, manifest = transfer_parts(
        unit["arm"], prepared, unit["spec"], unit["policy"]
    )
    kind = {
        "T_FULL": "text", "C_FULL": "text", "S_FULL": "pixel_text", "V0": "parent_dashboard",
        "D_STAR": "rq2_dashboard", "D_STAR_SKIN": "rq2_dashboard",
        "D_STAR_SPATIAL_SHAM": "rq2_dashboard", "C_STAR_TEXT": "text",
        "C_STAR_SCREENSHOT": "pixel_text", "C_STAR_CANVAS": "rq2_dashboard",
        "C_STAR_COMPACT": "text", "DENSE_TEXT": "text", "DENSE_COMPACT": "text",
        "DENSE_CANVAS": "rq2_dashboard",
    }[unit["arm"]]
    return parts, manifest, kind


def _valid_record(path: Path, expected: Mapping[str, Any] | None = None) -> bool:
    if not path.is_file():
        return False
    try:
        record = json.loads(path.read_text())
        recorded = record.pop("record_sha256")
        return (
            record.get("status") == "complete"
            and stable_hash(record) == recorded
            and path.with_suffix(".md").is_file()
            and all(record.get(key) == value for key, value in (expected or {}).items())
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _prepared_fingerprints(prepared: PreparedCase) -> tuple[str, str]:
    evidence = stable_hash({
        "public": prepared.public,
        "full_image": hashlib.sha256(prepared.full_png).hexdigest(),
        "screenshot_images": [
            hashlib.sha256(value).hexdigest() for value in prepared.screenshot_pngs
        ],
    })
    return evidence, stable_hash(prepared.private)


def _resume_expectation(
    prepared: PreparedCase, experiment: str, model: str,
    unit: Mapping[str, Any], contract_hash: str,
) -> dict[str, Any]:
    evidence_hash, private_hash = _prepared_fingerprints(prepared)
    return {
        "contract_sha256": contract_hash, "experiment": experiment, "model": model,
        "opaque_incident_id": str(prepared.public["opaque_incident_id"]),
        "unit_id": str(unit["unit_id"]),
        "prepared_evidence_sha256": evidence_hash,
        "evaluator_private_sha256": private_hash,
    }


def _target_path(
    paths: RunPaths, experiment: str, model: str,
    prepared: PreparedCase, unit: Mapping[str, Any],
) -> Path:
    return (
        paths.trajectories / experiment / model
        / str(prepared.public["opaque_incident_id"])
        / f"{unit['unit_id']}.json"
    )


def _materialize_unit(
    experiment: str, model: str, prepared: PreparedCase,
    unit: Mapping[str, Any], contract_hash: str,
) -> dict[str, Any]:
    """Perform renderer/prompt work before occupying a request-driver slot."""

    materialization_started = time.perf_counter()
    opaque, unit_id = str(prepared.public["opaque_incident_id"]), str(unit["unit_id"])
    evidence_hash, private_hash = _prepared_fingerprints(prepared)
    record: dict[str, Any] = {
        "schema_version": "CanvasRCARQ2DesignOutcomeV1",
        "experiment": experiment, "model": model,
        "opaque_incident_id": opaque, "unit_id": unit_id,
        "task": unit["task"], "status": "complete",
        "contract_sha256": contract_hash,
        "prepared_evidence_sha256": evidence_hash,
        "evaluator_private_sha256": private_hash,
        "dataset": str(prepared.private["dataset"]),
        "fault_type": str(prepared.private.get("fault_type") or "unknown"),
        "design_spec": asdict(unit["spec"]) if "spec" in unit else None,
        "content_policy": unit.get("policy"),
        "twin": unit.get("twin"),
        "transfer_arm": unit.get("arm"),
        "tool_profile": unit.get("tool_profile"),
        "tool_transport": unit.get("tool_transport"),
    }
    evidence, manifest, representation_kind = _evidence_for_unit(experiment, unit, prepared)
    record["representation_materialization_s"] = time.perf_counter() - materialization_started
    record["renderer_invoked_during_materialization"] = manifest is not None
    record["representation_kind"] = representation_kind
    if experiment == "exp_content_budget_twins" and unit.get("policy") == DENSE_CONTENT_POLICY:
        packet = prepared.public["dense_packet"]
    else:
        packet = (
            filter_packet(
                prepared.public["packet"], policy_regions(unit["policy"]),
                (
                    fact_id
                    for card in compile_dashboard_program(
                        prepared.public["packet"],
                        replace(
                            unit["spec"], content_policy=unit["policy"],
                            fact_inventory_hash=prepared.public["packet"]["fact_inventory_hash"],
                        ),
                    ).cards
                    for fact_id in card.fact_ids
                ),
            )
            if "policy" in unit and experiment == "exp_content_budget_twins"
            else prepared.public["packet"]
        )
    if experiment == "exp_downstream_transfer" and unit.get("arm") in {"DENSE_TEXT", "DENSE_COMPACT", "DENSE_CANVAS"}:
        packet = prepared.public["dense_packet"]
    elif experiment == "exp_downstream_transfer" and unit.get("arm") in {"C_STAR_TEXT", "C_STAR_SCREENSHOT", "C_STAR_CANVAS", "C_STAR_COMPACT"}:
        selected_program = compile_dashboard_program(
            prepared.public["packet"],
            replace(
                unit["spec"], content_policy=unit["policy"],
                fact_inventory_hash=prepared.public["packet"]["fact_inventory_hash"],
            ),
        )
        packet = filter_packet(
            prepared.public["packet"], REGIONS,
            (fact_id for card in selected_program.cards for fact_id in card.fact_ids),
        )
    elif experiment == "exp_tool_representation":
        packet = build_tool_packet(prepared.public["packet"], str(unit["tool_profile"]))
        record["tool_selection_audit"] = dict(packet["tool_selection_audit"])
    if unit["task"] == "one_stage_rca":
        parts = rq2_rca_parts(evidence, packet, representation_kind)
        schema, system, gold = rca_schema(), RCA_SYSTEM_ROLE, None
    else:
        question, gold = packed_operations(prepared.public["packet"], packet)
        record["operation_question"] = question
        record["operation_gold"] = gold.as_dict()
        record["operation_answerability"] = dict(gold.answerable)
        parts = rq2_qa_parts(evidence, question, representation_kind)
        schema, system = packed_qa_schema(), "You are a precise telemetry dashboard reader."
    image = next((part["png"] for part in evidence if part["type"] == "image"), None)
    return {
        "prepared_private": prepared.private, "unit": dict(unit), "record": record,
        "parts": parts, "schema": schema, "system": system, "gold": gold,
        "packet": packet, "image": image, "manifest": manifest,
        "materializer_affinity": sorted(os.sched_getaffinity(0)),
    }


def _complete_materialized_unit(
    *, experiment: str, model: str, materialized: Mapping[str, Any],
    paths: RunPaths, config: Mapping[str, Any], writer: AsyncWriter,
    request_gate: threading.BoundedSemaphore | None = None,
    postprocess_gate: threading.BoundedSemaphore | None = None,
) -> dict[str, int]:
    unit, record = materialized["unit"], dict(materialized["record"])
    record["operational_scheduler"] = {
        "name": "bounded_cpu_gpu_pipeline_v1",
        "materializer_affinity": list(materialized["materializer_affinity"]),
    }
    opaque, unit_id = str(record["opaque_incident_id"]), str(record["unit_id"])
    target = paths.trajectories / experiment / model / opaque / f"{unit_id}.json"
    conversation = _conversation_header(experiment, model, opaque, unit_id)
    calls = 0
    try:
        if materialized["manifest"] is not None:
            image = materialized["image"]
            if not isinstance(image, bytes):
                raise RQ2Error("visual unit materialized without PNG bytes")
            image_path = paths.renders / experiment / opaque / f"{unit_id}.png"
            writer.bytes(image_path, image)
            record["render"] = {
                "path": str(image_path.relative_to(paths.root)),
                "sha256": hashlib.sha256(image).hexdigest(),
                "manifest": materialized["manifest"],
            }
        calls = 1
        request_entered = postprocess_entered = False
        if request_gate is not None:
            request_gate.acquire(); request_entered = True

        def transition_to_postprocess() -> None:
            nonlocal request_entered, postprocess_entered
            if request_gate is not None and request_entered:
                request_gate.release(); request_entered = False
            if postprocess_gate is not None:
                postprocess_gate.acquire(); postprocess_entered = True

        try:
            call, raw = _call(
                model=model, system=materialized["system"], parts=materialized["parts"],
                schema=materialized["schema"], config=config,
                partial_root=paths.root / "partial_responses",
                metadata={"experiment": experiment, "model": model, "case": opaque, "unit": unit_id},
                attention_root=paths.root / "attention" / experiment / model / opaque / unit_id,
                after_response=transition_to_postprocess if request_gate is not None else None,
            )
        finally:
            if request_gate is not None and request_entered:
                request_gate.release()
            if postprocess_gate is not None and postprocess_entered:
                postprocess_gate.release()
        _append_call(conversation, "Single model call", call)
        packet = materialized["packet"]
        if unit["task"] == "one_stage_rca":
            normalized, error = _normalize_model_output(
                raw, lambda value: validate_diagnosis(value, packet["candidates"]),
                {"services": [], "reason": "", "confidence": "low"},
            )
            record["score"] = _score_rca(normalized, materialized["prepared_private"], config)
            record["grounding"] = ground_reason(
                str(normalized.get("reason") or ""), packet, materialized["prepared_private"],
            )
        else:
            normalized, error = _normalize_model_output(raw, lambda value: value, {})
            record["score"] = score_packed_qa(normalized, materialized["gold"])
        record.update(model_output=normalized, model_output_error=error, call=call)
    except Exception as error:
        record.update(status="infrastructure_error", error=f"{type(error).__name__}: {error}")
        conversation.extend(["\n## Error\n", record["error"], "\n"])
    record["record_sha256"] = stable_hash(record)
    writer.json(target, record)
    writer.bytes(target.with_suffix(".md"), "".join(conversation).encode())
    return {
        "completed": int(record["status"] == "complete"),
        "errors": int(record["status"] != "complete"), "calls": calls, "skipped": 0,
    }


def _run_unit(
    *, experiment: str, model: str, prepared: PreparedCase, unit: Mapping[str, Any],
    paths: RunPaths, config: Mapping[str, Any], contract_hash: str,
    writer: AsyncWriter,
) -> dict[str, int]:
    """Compatibility wrapper used by focused tests and serial diagnostics."""

    target = _target_path(paths, experiment, model, prepared, unit)
    if _valid_record(target, _resume_expectation(
        prepared, experiment, model, unit, contract_hash,
    )):
        return {"completed": 0, "errors": 0, "calls": 0, "skipped": 1}
    try:
        materialized = _materialize_unit(experiment, model, prepared, unit, contract_hash)
    except Exception as error:
        opaque, unit_id = str(prepared.public["opaque_incident_id"]), str(unit["unit_id"])
        record = {
            "schema_version": "CanvasRCARQ2DesignOutcomeV1", "experiment": experiment,
            "model": model, "opaque_incident_id": opaque, "unit_id": unit_id,
            "task": unit["task"], "status": "infrastructure_error",
            "contract_sha256": contract_hash, "dataset": str(prepared.private["dataset"]),
            "fault_type": str(prepared.private.get("fault_type") or "unknown"),
            "error": f"{type(error).__name__}: {error}",
        }
        record["record_sha256"] = stable_hash(record)
        writer.json(target, record)
        writer.bytes(target.with_suffix(".md"), (
            "".join(_conversation_header(experiment, model, opaque, unit_id))
            + f"\n## Error\n{record['error']}\n"
        ).encode())
        return {"completed": 0, "errors": 1, "calls": 0, "skipped": 0}
    return _complete_materialized_unit(
        experiment=experiment, model=model, materialized=materialized,
        paths=paths, config=config, writer=writer,
    )


def _physical_cpu_ids(limit: int) -> tuple[int, ...]:
    """Select one allowed logical CPU from each distinct physical core."""

    allowed = sorted(os.sched_getaffinity(0))
    chosen: list[int] = []
    seen: set[tuple[str, str]] = set()
    for cpu in allowed:
        topology = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology")
        try:
            key = (
                (topology / "physical_package_id").read_text().strip(),
                (topology / "core_id").read_text().strip(),
            )
        except OSError:
            key = ("logical", str(cpu))
        if key in seen:
            continue
        seen.add(key); chosen.append(cpu)
        if len(chosen) == limit:
            break
    if len(chosen) < limit:
        raise RQ2Error(f"only {len(chosen)} independent CPU cores are available; need {limit}")
    return tuple(chosen)


def _pin_materializer(cpu_ids: tuple[int, ...]) -> None:
    """Pin every spawned materializer to a separate physical core."""

    identity = mp.current_process()._identity
    slot = ((identity[-1] if identity else os.getpid()) - 1) % len(cpu_ids)
    os.sched_setaffinity(0, {cpu_ids[slot]})


def _round_robin_case_tasks(
    tasks_by_case: Sequence[Sequence[tuple[PreparedCase, dict[str, Any]]]],
) -> list[tuple[PreparedCase, dict[str, Any]]]:
    """Interleave cases while preserving each case's registered unit order."""

    width = max((len(tasks) for tasks in tasks_by_case), default=0)
    return [
        case_tasks[index]
        for index in range(width)
        for case_tasks in tasks_by_case
        if index < len(case_tasks)
    ]


def _write_materialization_error(
    *, experiment: str, model: str, prepared: PreparedCase, unit: Mapping[str, Any],
    paths: RunPaths, contract_hash: str, error: Exception, writer: AsyncWriter,
) -> dict[str, int]:
    opaque, unit_id = str(prepared.public["opaque_incident_id"]), str(unit["unit_id"])
    record = {
        "schema_version": "CanvasRCARQ2DesignOutcomeV1", "experiment": experiment,
        "model": model, "opaque_incident_id": opaque, "unit_id": unit_id,
        "task": unit["task"], "status": "infrastructure_error",
        "contract_sha256": contract_hash, "dataset": str(prepared.private["dataset"]),
        "fault_type": str(prepared.private.get("fault_type") or "unknown"),
        "error": f"{type(error).__name__}: {error}",
        "operational_scheduler": {"name": "bounded_cpu_gpu_pipeline_v1"},
    }
    record["record_sha256"] = stable_hash(record)
    target = _target_path(paths, experiment, model, prepared, unit)
    writer.json(target, record)
    writer.bytes(target.with_suffix(".md"), (
        "".join(_conversation_header(experiment, model, opaque, unit_id))
        + f"\n## Error\n{record['error']}\n"
    ).encode())
    return {"completed": 0, "errors": 1, "calls": 0, "skipped": 0}


def _run_bounded_pipeline(
    *, tasks: Sequence[tuple[PreparedCase, dict[str, Any]]], experiment: str,
    model: str, paths: RunPaths, config: Mapping[str, Any], contract_hash: str,
    writer: AsyncWriter,
) -> tuple[list[dict[str, int]], dict[str, Any]]:
    """Overlap eight pinned CPU materializers with bounded vLLM request drivers."""

    skipped: list[dict[str, int]] = []
    pending: list[tuple[PreparedCase, dict[str, Any]]] = []
    for prepared, unit in tasks:
        expected = _resume_expectation(prepared, experiment, model, unit, contract_hash)
        if _valid_record(_target_path(paths, experiment, model, prepared, unit), expected):
            skipped.append({"completed": 0, "errors": 0, "calls": 0, "skipped": 1})
        else:
            pending.append((prepared, unit))
    if not pending:
        return skipped, {
            "name": "bounded_cpu_gpu_pipeline_v1", "materializer_workers": 0,
            "materializer_cpu_ids": [], "request_concurrency": 0, "prefetch_depth": 0,
            "case_interleaving": "round_robin_preserve_within_case_order",
        }

    cpu_workers = min(8, len(pending), int(config["runtime"]["max_workers"]))
    request_concurrency = int(config["runtime"]["request_concurrency"])
    # Driver threads mostly wait on network or on the eight-way attention
    # postprocessor.  A two-batch reserve prevents completed responses from
    # occupying every driver while the server still has runnable capacity.
    request_workers = min(len(pending), 2 * request_concurrency + cpu_workers)
    cpu_ids = _physical_cpu_ids(cpu_workers)
    prefetch_depth = min(len(pending), request_workers + 2 * cpu_workers)
    request_gate = threading.BoundedSemaphore(request_concurrency)
    postprocess_gate = threading.BoundedSemaphore(cpu_workers)
    scheduler = {
        "name": "bounded_cpu_gpu_pipeline_v1", "materializer_workers": cpu_workers,
        "materializer_cpu_ids": list(cpu_ids), "request_concurrency": request_concurrency,
        "request_driver_threads": request_workers, "attention_postprocess_workers": cpu_workers,
        "prefetch_depth": prefetch_depth,
        "case_interleaving": "round_robin_preserve_within_case_order",
    }
    rows = list(skipped)
    task_iter = iter(pending)
    materializing: dict[Any, tuple[PreparedCase, dict[str, Any]]] = {}
    requesting: dict[Any, tuple[PreparedCase, dict[str, Any]]] = {}

    with ProcessPoolExecutor(
        max_workers=cpu_workers, mp_context=mp.get_context("spawn"),
        initializer=_pin_materializer, initargs=(cpu_ids,),
    ) as cpu_pool, ThreadPoolExecutor(max_workers=request_workers) as request_pool:
        def fill() -> None:
            while len(materializing) + len(requesting) < prefetch_depth:
                task = next(task_iter, None)
                if task is None:
                    break
                prepared, unit = task
                future = cpu_pool.submit(
                    _materialize_unit, experiment, model, prepared, unit, contract_hash,
                )
                materializing[future] = task

        fill()
        while materializing or requesting:
            finished, _ = wait((*materializing, *requesting), return_when=FIRST_COMPLETED)
            for future in finished:
                if future in materializing:
                    prepared, unit = materializing.pop(future)
                    try:
                        materialized = future.result()
                    except Exception as error:
                        rows.append(_write_materialization_error(
                            experiment=experiment, model=model, prepared=prepared, unit=unit,
                            paths=paths, contract_hash=contract_hash, error=error, writer=writer,
                        ))
                    else:
                        request = request_pool.submit(
                            _complete_materialized_unit, experiment=experiment, model=model,
                            materialized=materialized, paths=paths, config=config, writer=writer,
                            request_gate=request_gate, postprocess_gate=postprocess_gate,
                        )
                        requesting[request] = (prepared, unit)
                else:
                    requesting.pop(future)
                    rows.append(future.result())
            fill()
    return rows, scheduler


def run(
    *, experiment_id: str, experiment: str, model: str,
    config_path: Path = DEFAULT_CONFIG, execute: bool = False,
    smoke: bool = False, prepared_experiment_id: str | None = None,
    selection_artifact: Path | None = None,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    if not execute:
        raise RQ2Error("model execution requires --execute")
    if not smoke and not config.get("execution_enabled"):
        raise RQ2Error("formal RQ2 execution remains disabled until smoke and freeze")
    if model not in config["runtime"]["models"]:
        raise RQ2Error(f"unregistered model {model}")
    paths = RunPaths.build(experiment_id, config)
    prepared_paths = RunPaths.build(prepared_experiment_id or experiment_id, config)
    index = json.loads((prepared_paths.prepared / "index.json").read_text())
    unsigned = dict(index); recorded = unsigned.pop("index_sha256")
    if stable_hash(unsigned) != recorded:
        raise RQ2Error("prepared index hash mismatch")
    contract = _run_contract(config)
    warm_mapping_tokenizer(
        VLLMInferenceConfig.load(_vllm_config_path(config)).model_path(model)
    )
    tasks_by_case: list[list[tuple[PreparedCase, dict[str, Any]]]] = []
    for item in index["cases"]:
        prepared = _read_prepared(prepared_paths, item)
        case_tasks = []
        for unit in _unit_plan(
            experiment, prepared, config, model, smoke=smoke,
            selection_artifact=selection_artifact,
        ):
            case_tasks.append((prepared, unit))
        tasks_by_case.append(case_tasks)
    if smoke:
        per_model_cap = int(config["smoke_plans"][experiment]["total_calls"]) // 2
        # Assign successive coverage units round-robin across the three smoke
        # datasets. This covers the registered arms/tasks without spending the
        # bounded smoke on one case or repeating only the first unit.
        tasks = [
            tasks_by_case[index % len(tasks_by_case)][
                index % len(tasks_by_case[index % len(tasks_by_case)])
            ]
            for index in range(min(per_model_cap, sum(map(len, tasks_by_case))))
        ]
    else:
        tasks = _round_robin_case_tasks(tasks_by_case)
    if smoke:
        # Streaming checkpoints are created when a request is initiated and
        # therefore count every interrupted request and retry under this one
        # logical two-model smoke ID.
        partial_root = paths.root / "partial_responses"
        initiated = len(tuple(partial_root.glob("*.json")))
        pending = 0
        for prepared, unit in tasks:
            target = (
                paths.trajectories / experiment / model
                / str(prepared.public["opaque_incident_id"])
                / f"{unit['unit_id']}.json"
            )
            pending += int(not _valid_record(
                target,
                _resume_expectation(
                    prepared, experiment, model, unit, contract["contract_sha256"],
                ),
            ))
        cap = int(config["smoke_plans"][experiment]["total_calls"])
        if initiated + pending > cap:
            raise RQ2Error(
                "logical smoke call budget would be exceeded: "
                f"initiated={initiated} pending={pending} cap={cap}"
            )
    writer = AsyncWriter(int(config["runtime"].get("max_workers", 8)))
    effective = VLLMInferenceConfig.load(_vllm_config_path(config)).model(model)
    metrics_cfg = config.get("performance_metrics") or {}
    monitor = RuntimePerformanceMonitor(
        str(effective["base_url"]), float(metrics_cfg.get("sample_interval_s", 1.0)),
        bool(metrics_cfg.get("enabled", True)),
    ).start()
    rows: list[dict[str, int]] = []
    try:
        rows, scheduler = _run_bounded_pipeline(
            tasks=tasks, experiment=experiment, model=model, paths=paths,
            config=config, contract_hash=contract["contract_sha256"], writer=writer,
        )
    finally:
        writer.drain()
        run_performance = monitor.stop(
            attempted_requests=sum(row["calls"] for row in rows),
            good_requests=sum(row["completed"] for row in rows),
        )
    summary = {
        "schema_version": "CanvasRCARQ2RunSummaryV1",
        "experiment_id": experiment_id, "prepared_experiment_id": prepared_experiment_id or experiment_id,
        "experiment": experiment, "model": model, "smoke": smoke,
        "assigned_units": len(tasks),
        "completed": sum(row["completed"] for row in rows),
        "infrastructure_errors": sum(row["errors"] for row in rows),
        "model_calls": sum(row["calls"] for row in rows),
        "resumed_records": sum(row["skipped"] for row in rows),
        "operational_scheduler": scheduler,
        "run_performance": run_performance,
        "run_contract": contract,
    }
    write_json(paths.root / f"run_{experiment}_{model}.json", summary)
    return summary


def mark_smoke_timeout(
    *, experiment_id: str, config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    """Finalize live streaming checkpoints after the aggregate supervisor fires."""

    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    changed = 0
    for path in (paths.root / "partial_responses").glob("*.json"):
        payload = json.loads(path.read_text())
        if payload.get("status") != "streaming":
            continue
        payload.update(
            status="timeout_partial",
            timeout_scope="complete_two_model_logical_smoke",
            timed_out_unix_s=time.time(),
        )
        write_json(path, payload)
        changed += 1
    marker = {
        "schema_version": "CanvasRCARQ2SmokeTimeoutV1",
        "experiment_id": experiment_id,
        "status": "aggregate_timeout_reached",
        "timeout_partial_checkpoints": changed,
        "recorded_unix_s": time.time(),
    }
    marker["marker_sha256"] = stable_hash(marker)
    write_json(paths.root / "smoke_timeout.json", marker)
    return marker


def audit_smoke(
    *, experiment_id: str, experiment: str,
    config_path: Path = DEFAULT_CONFIG, timeout_only: bool = False,
) -> dict[str, Any]:
    """Fail closed on hidden smoke errors while keeping parse diagnostic-only."""

    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    cap = int(config["smoke_plans"][experiment]["total_calls"])
    errors: list[str] = []
    partials = []
    for path in sorted((paths.root / "partial_responses").glob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid partial checkpoint {path.name}: {error}")
            continue
        partials.append(payload)
        status = str(payload.get("status") or "missing")
        allowed = {"completed", "timeout_partial"} if timeout_only else {"completed"}
        if status not in allowed:
            errors.append(f"partial checkpoint {path.name} has status {status}")
    if len(partials) > cap:
        errors.append(f"initiated calls {len(partials)} exceed registered cap {cap}")

    records = []
    for path in sorted((paths.trajectories / experiment).rglob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid trajectory {path}: {error}")
            continue
        recorded = payload.get("record_sha256")
        unsigned = {key: value for key, value in payload.items() if key != "record_sha256"}
        if not recorded or stable_hash(unsigned) != recorded:
            errors.append(f"trajectory hash mismatch: {path}")
        if payload.get("status") != "complete":
            errors.append(
                f"non-timeout trajectory error: {path}: "
                f"{payload.get('error') or payload.get('status')}"
            )
        records.append(payload)

    summaries = []
    for model in config["runtime"]["models"]:
        path = paths.root / f"run_{experiment}_{model}.json"
        if not path.is_file():
            if not timeout_only:
                errors.append(f"missing completed model phase summary: {model}")
            continue
        payload = json.loads(path.read_text())
        summaries.append(payload)
        if int(payload.get("infrastructure_errors") or 0):
            errors.append(f"{model} phase recorded infrastructure errors")
    if not timeout_only:
        expected = int(config["smoke_plans"][experiment]["total_calls"])
        assigned = sum(int(row.get("assigned_units") or 0) for row in summaries)
        if assigned != expected:
            errors.append(f"assigned smoke units {assigned} != registered {expected}")
        if len(partials) != expected:
            errors.append(f"initiated smoke calls {len(partials)} != registered {expected}")

    result = {
        "schema_version": "CanvasRCARQ2SmokeAuditV1",
        "experiment_id": experiment_id,
        "experiment": experiment,
        "status": "failed" if errors else ("passed_timeout_only" if timeout_only else "passed"),
        "timeout_only": timeout_only,
        "call_cap": cap,
        "initiated_calls": len(partials),
        "completed_trajectory_records": len(records),
        "completed_model_phases": [str(row.get("model")) for row in summaries],
        "parse_errors_diagnostic_only": sum(bool(row.get("model_output_error")) for row in records),
        "errors": errors,
    }
    result["audit_sha256"] = stable_hash(result)
    write_json(paths.root / "smoke_audit.json", result)
    return result


def analyse(
    *, experiment_id: str, experiment: str,
    config_path: Path = DEFAULT_CONFIG, select: bool = False,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    records = [
        json.loads(path.read_text())
        for path in (paths.trajectories / experiment).rglob("*.json")
    ]
    result = analyze_records(records, experiment, config, select=select)
    write_json(paths.root / f"summary_{experiment}.json", result)
    if result.get("selection"):
        write_json(paths.root / "selection.json", result["selection"])
    return result


def export_composer_seed(
    *, experiment_id: str, prepared_experiment_id: str | None = None,
    config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    """Export tool-grounding examples without performing training or inference."""

    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    prepared_paths = RunPaths.build(prepared_experiment_id or experiment_id, config)
    index = json.loads((prepared_paths.prepared / "index.json").read_text())
    unsigned = dict(index); recorded = unsigned.pop("index_sha256")
    if stable_hash(unsigned) != recorded:
        raise RQ2Error("prepared index hash mismatch")
    contract = _run_contract(config)
    registered = config["design_space"]["sampling"]
    examples = []
    for item in index["cases"]:
        prepared = _read_prepared(prepared_paths, item)
        packet = prepared.public["packet"]
        parent = hashlib.sha256((ROOT / config["renderer"]["parent_provenance"]).read_bytes()).hexdigest()
        specs = space_filling_specs(
            parent, packet["fact_inventory_hash"], seed=int(config["seed"]),
            points=int(registered["points"]),
            candidate_pool_size=int(registered["candidate_pool_size"]),
        )
        for spec in specs:
            program = compile_dashboard_program(packet, spec)
            catalog = build_evidence_cards(packet, spec.panel_composition)
            initial = ComposerStateV1(
                case_evidence_hash=str(packet["packet_hash"]),
                partial_spec={
                    "design_id": spec.design_id, "design_role": spec.design_role,
                    "renderer_parent_hash": spec.renderer_parent_hash,
                    "fact_inventory_hash": spec.fact_inventory_hash,
                },
                remaining_fact_budget=len(packet["facts"]),
                remaining_pixel_budget=spec.canvas_size[0] * spec.canvas_size[1],
                remaining_token_budget=32768,
                available_card_ids=tuple(card.card_id for card in catalog),
                renderer_hash=stable_hash(contract["renderer_source_sha256"]),
                solver_hash=contract["unified_config_sha256"]["vllm"],
                prompt_hash=contract["code_sha256"].get("RQs/RQ2/src/exps.py", ""),
                scorer_hash=contract["unified_config_sha256"]["scorer"],
            )
            examples.append({
                "opaque_incident_id": prepared.public["opaque_incident_id"],
                **compile_composer_sft_example(initial, program),
            })
    payload = {
        "schema_version": "CanvasRCAComposerSFTDatasetV2",
        "status": "tool_grounding_only_no_rca_reward",
        "run_contract_sha256": contract["contract_sha256"],
        "examples": examples,
    }
    payload["dataset_sha256"] = stable_hash(payload)
    write_json(paths.root / "composer_sft_seed_dataset.json", payload)
    return {key: value for key, value in payload.items() if key != "examples"} | {"example_count": len(examples)}


def verify(
    *, experiment_id: str, config_path: Path = DEFAULT_CONFIG,
    prepared_experiment_id: str | None = None,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    return verify_result_root(
        RunPaths.build(experiment_id, config).root,
        RunPaths.build(prepared_experiment_id or experiment_id, config).root,
        config,
    )


def materialize_rosters(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_yaml(config_path)
    data = config["data"]
    return materialize_v3_rosters(
        segmentation_path=ROOT / config["unified"]["segmentation"],
        rq1_private_roster=ROOT / data["source_rq1_roster"],
        smoke_source=ROOT / "RQs/RQ1_1/configs/rosters/rq1_1_smoke_private_v3.json",
        output_dir=ROOT / "RQs/RQ2/configs/rosters",
    )


def cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--experiment-id", required=True); prep.add_argument("--roster", type=Path, required=True)
    prep.add_argument("--limit", type=int); prep.add_argument("--output-shard-count", type=int, default=1)
    runner = sub.add_parser("run")
    runner.add_argument("--experiment-id", required=True); runner.add_argument("--prepared-experiment-id")
    runner.add_argument("--experiment", choices=tuple(load_yaml()["experiments"]), required=True)
    runner.add_argument("--model", required=True); runner.add_argument("--selection-artifact", type=Path)
    runner.add_argument("--execute", action="store_true"); runner.add_argument("--smoke", action="store_true")
    analysis = sub.add_parser("analyse")
    analysis.add_argument("--experiment-id", required=True); analysis.add_argument("--experiment", required=True)
    analysis.add_argument("--select", action="store_true")
    verifier = sub.add_parser("verify")
    verifier.add_argument("--experiment-id", required=True); verifier.add_argument("--prepared-experiment-id")
    composer = sub.add_parser("export-composer-seed")
    composer.add_argument("--experiment-id", required=True); composer.add_argument("--prepared-experiment-id")
    timeout_marker = sub.add_parser("mark-smoke-timeout")
    timeout_marker.add_argument("--experiment-id", required=True)
    smoke_audit = sub.add_parser("smoke-audit")
    smoke_audit.add_argument("--experiment-id", required=True)
    smoke_audit.add_argument("--experiment", choices=tuple(load_yaml()["experiments"]), required=True)
    smoke_audit.add_argument("--timeout-only", action="store_true")
    sub.add_parser("materialize-rosters")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        value = prepare(experiment_id=args.experiment_id, roster=args.roster, config_path=args.config, limit=args.limit, output_shard_count=args.output_shard_count)
    elif args.command == "run":
        value = run(experiment_id=args.experiment_id, prepared_experiment_id=args.prepared_experiment_id, experiment=args.experiment, model=args.model, config_path=args.config, execute=args.execute, smoke=args.smoke, selection_artifact=args.selection_artifact)
    elif args.command == "analyse":
        value = analyse(experiment_id=args.experiment_id, experiment=args.experiment, config_path=args.config, select=args.select)
    elif args.command == "export-composer-seed":
        value = export_composer_seed(experiment_id=args.experiment_id, prepared_experiment_id=args.prepared_experiment_id, config_path=args.config)
    elif args.command == "mark-smoke-timeout":
        value = mark_smoke_timeout(experiment_id=args.experiment_id, config_path=args.config)
    elif args.command == "smoke-audit":
        value = audit_smoke(experiment_id=args.experiment_id, experiment=args.experiment, config_path=args.config, timeout_only=args.timeout_only)
    elif args.command == "materialize-rosters":
        value = materialize_rosters(args.config)
    else:
        value = verify(experiment_id=args.experiment_id, prepared_experiment_id=args.prepared_experiment_id, config_path=args.config)
    print(json.dumps(value, indent=2, sort_keys=True))
    if args.command == "smoke-audit" and value["status"] == "failed":
        return 1
    if args.command == "run" and args.smoke and int(value["infrastructure_errors"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())

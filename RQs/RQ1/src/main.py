"""Compact command-line engine for every RQ1 experiment."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any, Mapping, Sequence

from unified_scripts import canonical_json, stable_hash
from vlmrca.vlm.client import VLMResponse, call_vlm, count_vllm_prompt_tokens, text_part
from vlmrca.vlm.configs import get_config
from vlmrca.vlm.runtime_contract import compatible_runtime_freezes, completed_record_is_compatible
from vlmrca.vlm.attention_probe import map_groups_to_images, render_overlay as render_probe_overlay
from unified_scripts.vllm_inference import VLLMInferenceConfig
from unified_scripts.dataset_segmentation import CaseRecord, DatasetSegmentationConfig

from .exps import (
    DIRECT_DIAGNOSE_SYSTEM,
    DIAGNOSE_SYSTEM,
    OBSERVE_SYSTEM,
    QA_SYSTEM,
    TYPED_ANSWER_SYSTEM,
    TYPED_OBSERVE_SYSTEM,
    PreparedCase,
    attention_diagnostics,
    balanced_arm_order,
    experiment_registry,
    handoff_parts,
    is_rca_task,
    prepare_case,
    representation_parts,
    render_attention_overlay,
    response_schema,
    normalize_stage1_ledger,
    normalize_typed_qa_ledger,
    qa_representation_parts,
    score_reasoning,
    stage1_prompt,
    stage2_prompt,
    validate_diagnosis,
    validate_qa_response,
    visual_diagnostic_for_arm,
)
from .gates import analyze_records, analyze_stage_pair, verify_result_root
from .utils import (
    AsyncWriter,
    DEFAULT_CONFIG,
    ROOT,
    RQ1Error,
    RunPaths,
    artifact_contract,
    load_yaml,
    parse_json_object,
    scorer,
    write_json,
)

SOURCE_FILES = tuple(sorted(
    path for path in (ROOT / "RQs/RQ1/src").rglob("*.py")
    if "__pycache__" not in path.parts
))


def _load_roster(path: Path, config: Mapping[str, Any]) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("datasets"), Mapping):
        rows = [
            ({"dataset": dataset, "case_id": row} if isinstance(row, str) else row)
            for dataset, values in payload["datasets"].items()
            for row in values
        ]
    else:
        rows = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise RQ1Error("roster must be a list or contain a cases list")
    normalized = []
    segmentation = DatasetSegmentationConfig.load(config["unified"]["segmentation"])
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("dataset") or not row.get("case_id"):
            raise RQ1Error("private roster rows require dataset and case_id")
        dataset, case_id = str(row["dataset"]), str(row["case_id"])
        expected = segmentation.opaque_id(CaseRecord(dataset, case_id, Path(".")))
        observed = str(row.get("opaque_incident_id") or expected)
        if observed != expected:
            raise RQ1Error(
                f"roster opaque ID mismatch for {dataset}/{case_id}: {observed} != {expected}"
            )
        normalized.append({"dataset": dataset, "case_id": case_id,
                           "opaque_incident_id": observed})
    return normalized


def _prepare_roster_row(row: Mapping[str, str], config: Mapping[str, Any]) -> PreparedCase:
    return prepare_case(row["dataset"], row["case_id"], config, row["opaque_incident_id"])


def _persist_prepared(paths: RunPaths, prepared: PreparedCase) -> dict[str, Any]:
    opaque = str(prepared.public["opaque_incident_id"])
    public_path, private_path = paths.prepared / f"{opaque}.json", paths.private / f"{opaque}.json"
    full_path = paths.renders / f"{opaque}.full.png"
    qa_full_path = paths.renders / f"{opaque}.qa-full.png"
    routed_path = paths.renders / f"{opaque}.routed.png"
    qa_region_paths = {
        region: [paths.renders / f"{opaque}.qa-renderer-{region}-{page:02d}.png"
                 for page in range(1, len(images) + 1)]
        for region, images in prepared.qa_region_pngs.items()
    }
    pixel_text_paths = [paths.renders / f"{opaque}.pixel-text-{index:02d}.png"
                        for index in range(1, len(prepared.pixel_text_pngs) + 1)]
    variant_paths = {name: paths.renders / f"{opaque}.{name}.png" for name in prepared.variant_pngs}
    write_json(public_path, prepared.public); write_json(private_path, prepared.private)
    from .utils import atomic_write
    atomic_write(full_path, prepared.full_png); atomic_write(qa_full_path, prepared.qa_full_png)
    atomic_write(routed_path, prepared.routed_png)
    for region, region_paths in qa_region_paths.items():
        for path, image in zip(region_paths, prepared.qa_region_pngs[region], strict=True):
            atomic_write(path, image)
    for path, image in zip(pixel_text_paths, prepared.pixel_text_pngs, strict=True):
        atomic_write(path, image)
    for name, path in variant_paths.items():
        atomic_write(path, prepared.variant_pngs[name])
    return {
        "opaque_incident_id": opaque,
        "public": str(public_path.relative_to(paths.root)), "private": str(private_path.relative_to(paths.root)),
        "full_image": str(full_path.relative_to(paths.root)),
        "qa_full_image": str(qa_full_path.relative_to(paths.root)),
        "routed_image": str(routed_path.relative_to(paths.root)),
        "qa_region_images": {region: [str(path.relative_to(paths.root)) for path in values]
                             for region, values in qa_region_paths.items()},
        "pixel_text_images": [str(path.relative_to(paths.root)) for path in pixel_text_paths],
        "variant_images": {name: str(path.relative_to(paths.root)) for name, path in variant_paths.items()},
        "public_sha256": stable_hash(prepared.public), "private_sha256": stable_hash(prepared.private),
        "full_image_sha256": stable_hash(prepared.full_png),
        "qa_full_image_sha256": stable_hash(prepared.qa_full_png),
        "routed_image_sha256": stable_hash(prepared.routed_png),
        "qa_region_image_sha256": {region: [stable_hash(value) for value in images]
                                   for region, images in prepared.qa_region_pngs.items()},
        "pixel_text_image_sha256": [stable_hash(value) for value in prepared.pixel_text_pngs],
        "variant_image_sha256": {name: stable_hash(value) for name, value in prepared.variant_pngs.items()},
    }


def _write_prepared_index(paths: RunPaths, experiment_id: str, entries: Sequence[Mapping[str, Any]],
                          freeze: Mapping[str, Any], *, partial: bool) -> dict[str, Any]:
    summary = {"schema_version": "RQ1PreparedIndexV6", "experiment_id": experiment_id,
               "case_count": len(entries),
               "cases": sorted((dict(row) for row in entries), key=lambda row: row["opaque_incident_id"]),
               "runtime_freeze": dict(freeze), "preparation_complete": not partial}
    summary["index_sha256"] = stable_hash(summary)
    write_json(paths.prepared / ("index.partial.json" if partial else "index.json"), summary)
    return summary


def prepare(
    *,
    experiment_id: str,
    roster: Path,
    config_path: Path = DEFAULT_CONFIG,
    limit: int | None = None,
    output_shard_count: int = 1,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    if output_shard_count < 1:
        raise RQ1Error("preparation output shard count must be positive")
    rows = _load_roster(roster, config)
    if limit is not None:
        rows = rows[:limit]
    freeze = artifact_contract(config=config, code_files=SOURCE_FILES)
    shard_ids = [experiment_id if output_shard_count == 1 else
                 f"{experiment_id}__shard-{index:04d}-of-{output_shard_count:04d}"
                 for index in range(output_shard_count)]
    paths = [RunPaths.build(value, config) for value in shard_ids]
    entries: list[list[dict[str, Any]]] = [[] for _ in shard_ids]
    assignments = {row["opaque_incident_id"]: int(hashlib.sha256(
        row["opaque_incident_id"].encode()).hexdigest(), 16) % output_shard_count for row in rows}
    missing = []
    for index, shard_paths in enumerate(paths):
        final_path = shard_paths.prepared / "index.json"
        partial_path = shard_paths.prepared / "index.partial.json"
        resume_path = final_path if final_path.is_file() else partial_path
        if resume_path.is_file():
            previous = json.loads(resume_path.read_text(encoding="utf-8"))
            if previous.get("runtime_freeze", {}).get("freeze_sha256") == freeze["freeze_sha256"]:
                for item in previous.get("cases") or ():
                    if assignments.get(str(item["opaque_incident_id"])) == index:
                        _read_prepared(shard_paths, item)
                        entries[index].append(dict(item))
    completed_ids = {row["opaque_incident_id"] for values in entries for row in values}
    missing = [row for row in rows if row["opaque_incident_id"] not in completed_ids]
    workers = max(1, min(4, int(config["runtime"]["max_workers"])))
    # Keep only one task per worker in flight.  Submitting the complete roster
    # up front made ProcessPoolExecutor wait for hundreds of queued cases after
    # the first preparation exception, hiding the real failure and preventing
    # partial indexes from advancing.
    row_iter = iter(missing)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for row in itertools.islice(row_iter, workers):
            futures[pool.submit(_prepare_roster_row, row, config)] = row
        while futures:
            finished, _pending = wait(futures, return_when=FIRST_COMPLETED)
            for future in finished:
                row, prepared = futures.pop(future), future.result()
                index = assignments[row["opaque_incident_id"]]
                entries[index].append(_persist_prepared(paths[index], prepared))
                _write_prepared_index(paths[index], shard_ids[index], entries[index], freeze, partial=True)
                next_row = next(row_iter, None)
                if next_row is not None:
                    futures[pool.submit(_prepare_roster_row, next_row, config)] = next_row
    summaries = []
    for shard_paths, shard_id, shard_entries in zip(paths, shard_ids, entries, strict=True):
        summaries.append(_write_prepared_index(shard_paths, shard_id, shard_entries, freeze, partial=False))
        (shard_paths.prepared / "index.partial.json").unlink(missing_ok=True)
    return summaries[0] if output_shard_count == 1 else {
        "schema_version": "RQ1PreparedShardSetV1", "experiment_id": experiment_id,
        "shard_count": output_shard_count, "case_count": sum(row["case_count"] for row in summaries),
        "shards": [{"experiment_id": row["experiment_id"], "case_count": row["case_count"],
                    "index_sha256": row["index_sha256"]} for row in summaries],
        "runtime_freeze": freeze,
    }


def _read_prepared(paths: RunPaths, item: Mapping[str, Any]) -> PreparedCase:
    public = json.loads((paths.root / item["public"]).read_text())
    private = json.loads((paths.root / item["private"]).read_text())
    full = (paths.root / item["full_image"]).read_bytes()
    qa_full = (paths.root / item["qa_full_image"]).read_bytes()
    routed = (paths.root / item["routed_image"]).read_bytes()
    qa_regions = {
        region: tuple((paths.root / rel).read_bytes() for rel in values)
        for region, values in item.get("qa_region_images", {}).items()
    }
    pixel_text = tuple((paths.root / rel).read_bytes() for rel in item.get("pixel_text_images", ()))
    variants = {name: (paths.root / rel).read_bytes() for name, rel in item.get("variant_images", {}).items()}
    if stable_hash(public) != item.get("public_sha256"):
        raise RQ1Error("prepared public artifact hash mismatch")
    if stable_hash(private) != item.get("private_sha256"):
        raise RQ1Error("prepared private artifact hash mismatch")
    if stable_hash(full) != item.get("full_image_sha256"):
        raise RQ1Error("prepared full-image index hash mismatch")
    if stable_hash(qa_full) != item.get("qa_full_image_sha256"):
        raise RQ1Error("prepared Q&A full-image index hash mismatch")
    if stable_hash(routed) != item.get("routed_image_sha256"):
        raise RQ1Error("prepared routed-image index hash mismatch")
    if {region: [stable_hash(value) for value in values] for region, values in qa_regions.items()} != item.get("qa_region_image_sha256"):
        raise RQ1Error("prepared Q&A region-image index hash mismatch")
    if [stable_hash(value) for value in pixel_text] != item.get("pixel_text_image_sha256"):
        raise RQ1Error("prepared pixel-text image index hash mismatch")
    if any(
        stable_hash(value) != item.get("variant_image_sha256", {}).get(name)
        for name, value in variants.items()
    ):
        raise RQ1Error("prepared counterfactual index hash mismatch")
    if (stable_hash(full) != public["full_image_sha256"]
            or stable_hash(qa_full) != public["qa_full_image_sha256"]
            or stable_hash(routed) != public["routed_image_sha256"]
            or {region: [stable_hash(value) for value in values] for region, values in qa_regions.items()}
               != public["qa_region_image_sha256"]
            or [stable_hash(value) for value in pixel_text] != public["pixel_text_image_sha256"]):
        raise RQ1Error("prepared image hash mismatch")
    expected_variants = public.get("variant_image_sha256", {})
    if any(stable_hash(value) != expected_variants.get(name) for name, value in variants.items()):
        raise RQ1Error("prepared counterfactual image hash mismatch")
    return PreparedCase(public=public, private=private, full_png=full, qa_full_png=qa_full,
                        routed_png=routed, pixel_text_pngs=pixel_text,
                        qa_region_pngs=qa_regions, variant_pngs=variants)


def _completed_target(path: Path, allowed_freezes: Sequence[str]) -> bool:
    """Accept hash-valid model outcomes and zero-call protocol exclusions."""

    if completed_record_is_compatible(path, allowed_freezes):
        return True
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        recorded_hash = record.pop("record_sha256", None)
    except (OSError, json.JSONDecodeError):
        return False
    if (record.get("status") != "protocol_ineligible"
            or not recorded_hash or stable_hash(record) != recorded_hash):
        return False
    keys = (
        "experiment_id", "experiment", "model", "execution_mode",
        "opaque_incident_id", "arm", "representation_hash",
        "runtime_freeze_sha256",
    )
    if any(key not in record for key in keys):
        return False
    contract = {key: record[key] for key in keys}
    if "registered_arm_order" in record:
        contract.update(
            registered_arm_order=record["registered_arm_order"],
            arm_order_index=record.get("arm_order_index"),
        )
    return record.get("call_key") == stable_hash(contract)[:24]


def _finish_reason(response: VLMResponse) -> Any:
    return (response.raw or {}).get("finish_reason") or (response.raw or {}).get("stopReason")


def _parts_hash(parts: Sequence[Mapping[str, Any]]) -> str:
    rows = []
    for part in parts:
        payload = part["png"] if part["type"] == "image" else str(part["text"]).encode()
        rows.append({"type": part["type"], "sha256": stable_hash(payload)})
    return stable_hash(rows)


def _request_contract(*, experiment_id: str, experiment: str, model: str,
                      execution_mode: str, opaque_incident_id: str, arm: str,
                      parts: Sequence[Mapping[str, Any]], runtime_freeze_sha256: str,
                      extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the content-addressed provenance shared by every RQ1 request path."""

    contract = {
        "experiment_id": experiment_id, "experiment": experiment, "model": model,
        "execution_mode": execution_mode, "opaque_incident_id": opaque_incident_id,
        "arm": arm, "representation_hash": _parts_hash(parts),
        "runtime_freeze_sha256": runtime_freeze_sha256,
        **dict(extra or {}),
    }
    contract["call_key"] = stable_hash(contract)[:24]
    return contract


def _prompt_record(system: str, parts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Persist the exact text and content hashes sent to the model."""

    return {
        "system": system,
        "parts": [
            {"type": "image", "sha256": stable_hash(part["png"])}
            if part["type"] == "image"
            else {"type": "text", "text": str(part["text"])}
            for part in parts
        ],
    }


def _prompt_markdown(stage: int, prompt: Mapping[str, Any]) -> str:
    return (
        f"\n## Stage {stage} prompt\n\n"
        "```json\n"
        + json.dumps(prompt, indent=2, sort_keys=True)
        + "\n```\n"
    )


def _model_call(
    *,
    model: str,
    system: str,
    parts: list[dict[str, Any]],
    schema: Mapping[str, Any],
    inference_adapter: Mapping[str, Any],
    context_limit: int,
    attention_output_root: Path,
    partial_output_root: Path | None = None,
    partial_metadata: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    started = time.time()
    max_tokens = int(inference_adapter["max_tokens"])
    model_config = get_config(model, max_tokens=max_tokens)
    prompt_tokens = count_vllm_prompt_tokens(parts, model_config, system=system)
    text_tokens = count_vllm_prompt_tokens(parts, model_config, system=system, text_only=True)
    if prompt_tokens is None or text_tokens is None:
        raise RQ1Error("live multimodal token accounting failed")
    if prompt_tokens + max_tokens > context_limit:
        raise RQ1Error(
            "prompt plus registered output budget exceeds context: "
            f"{prompt_tokens}+{max_tokens}>{context_limit}"
        )
    # call_vlm counts total attempts, not extra retries; one means one request.
    response = call_vlm(
        parts, model=model_config, system=system, max_retries=1,
        response_format=dict(schema), partial_output_dir=partial_output_root,
        partial_metadata={**dict(partial_metadata or {}), "prompt_sha256": _parts_hash(parts)},
    )
    finish_reason = _finish_reason(response)
    request_id = str((response.raw or {}).get("request_id") or "")
    probe = (response.raw or {}).get("attention_probe")
    attention_record: dict[str, Any]
    images = [part["png"] for part in parts if part["type"] == "image"]
    if images:
        if not isinstance(probe, Mapping):
            raise RQ1Error("visual request completed without required same-pass attention probe")
        mapped = map_groups_to_images(probe, images)
        call_root = attention_output_root / hashlib.sha256(request_id.encode()).hexdigest()
        call_root.mkdir(parents=True, exist_ok=True)
        write_json(call_root / "raw_probe.json", probe)
        artifacts = []
        for index, (png, artifact) in enumerate(zip(images, mapped, strict=True)):
            grid_path, overlay_path = call_root / f"image_{index:02d}.json", call_root / f"image_{index:02d}.png"
            write_json(grid_path, artifact); overlay_path.write_bytes(render_probe_overlay(png, artifact))
            artifacts.append({
                "image_index": index, "image_sha256": artifact["image_sha256"],
                "source_visual_tokens": artifact["source_visual_tokens"],
                "grid_path": str(grid_path.relative_to(attention_output_root.parents[2])),
                "overlay_path": str(overlay_path.relative_to(attention_output_root.parents[2])),
                "grid_sha256": stable_hash(artifact), "overlay_sha256": stable_hash(overlay_path.read_bytes()),
            })
        attention_record = {
            "status": "collected_same_prefill", "request_id": request_id,
            "method": probe["method"], "layer_name": probe["layer_name"],
            "extra_model_calls": 0, "correlational_only": True, "artifacts": artifacts,
        }
    else:
        attention_record = {"status": "not_applicable_text_only", "artifacts": [], "extra_model_calls": 0}
    record = {
        "request_id": request_id,
        "prompt": _prompt_record(system, parts),
        "response_text": response.text,
        "input_tokens": response.input_tokens,
        "text_tokens": text_tokens,
        "image_tokens": prompt_tokens - text_tokens,
        "tokenizer_input_tokens": prompt_tokens,
        "tokenizer_api_input_delta": prompt_tokens - response.input_tokens,
        "requested_max_tokens": max_tokens,
        "context_limit": context_limit,
        "context_headroom_tokens": context_limit - prompt_tokens - max_tokens,
        "inference_adapter": dict(inference_adapter),
        "output_tokens": response.output_tokens,
        "total_tokens": response.total_tokens,
        "wall_time_s": time.time() - started,
        "model_latency_s": response.latency_s,
        "finish_reason": finish_reason,
        "truncated": str(finish_reason).casefold() in {"length", "max_tokens", "max_output_tokens"},
        "gpu_active_time_s": None,
        "peak_gpu_memory_bytes": None,
        "attention_probe": attention_record,
    }
    return record, response.text


def _stage1_failure(text: str, error: Exception) -> dict[str, Any]:
    return {
        "schema_version": "Stage1FailureV2",
        "failure": "parse_error",
        "detail": str(error),
        "raw_response_bytes": len(text.encode()),
    }


def _sync_attention_status(
    record: dict[str, Any], public: Mapping[str, Any], paths: RunPaths,
) -> None:
    profile = record.get("visual_diagnostic")
    if not isinstance(profile, dict):
        return
    probes = [stage.get("attention_probe") for stage in record.get("stages") or ()]
    collected = [probe for probe in probes if isinstance(probe, Mapping) and probe.get("status") == "collected_same_prefill"]
    if collected:
        atlas_values = public.get("visual_evidence_atlases") or {}

        def flatten_atlases(value: Any) -> list[Mapping[str, Any]]:
            if isinstance(value, Mapping) and value.get("image_sha256"):
                return [value]
            if isinstance(value, Mapping):
                return [item for child in value.values() for item in flatten_atlases(child)]
            if isinstance(value, (list, tuple)):
                return [item for child in value for item in flatten_atlases(child)]
            return []

        atlases = flatten_atlases(atlas_values)
        diagnostics = []
        required_regions = list(profile.get("visual_regions") or ())
        for probe in collected:
            for artifact_ref in probe.get("artifacts") or ():
                artifact = json.loads((paths.root / artifact_ref["grid_path"]).read_text())
                atlas = next((value for value in atlases
                              if value.get("image_sha256") == artifact.get("image_sha256")), None)
                if atlas is not None:
                    candidate = {**artifact, "required_regions": required_regions}
                    report = attention_diagnostics(candidate, atlas)
                    artifact_ref["diagnostics"] = report; diagnostics.append(report)
        profile.update(
            attention_status="collected_same_prefill",
            attention_artifacts=sum(len(probe.get("artifacts") or ()) for probe in collected),
            attention_request_ids=[probe["request_id"] for probe in collected],
            attention_diagnostics=diagnostics,
        )


def _score_rca(prediction: Mapping[str, Any], private: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    numeric_to_natural = private["numeric_to_natural"]
    raw = prediction.get("services") if isinstance(prediction.get("services"), list) else []
    numeric = list(map(str, raw))[:5]
    # Preserve unknown predictions at their original ranks.  Dropping them
    # would incorrectly promote later valid candidates and inflate MRR.
    natural = [numeric_to_natural.get(value, f"__UNKNOWN_ID_AT_RANK_{index}__") for index, value in enumerate(numeric, 1)]
    metrics = scorer(config).score(natural, private["accepted_labels"]).as_dict()
    return {
        **metrics,
        "numeric_predictions": numeric,
        "natural_predictions": natural,
        "unknown_prediction_count": sum(value not in numeric_to_natural for value in numeric),
    }


def _case_arms(
    spec: Any, dataset: str, config: Mapping[str, Any], *, smoke: bool,
) -> tuple[str, ...]:
    """Return the full formal arms or this experiment's bounded smoke cells."""

    if not smoke:
        return tuple(spec.arms)
    plans = config.get("smoke_plans") or {}
    plan = plans.get(spec.name)
    if not isinstance(plan, Mapping):
        raise RQ1Error(f"missing unique smoke plan for {spec.name}")
    selected = tuple(map(str, plan.get(dataset) or ()))
    if not selected or not set(selected) <= set(spec.arms):
        raise RQ1Error(f"invalid smoke arms for {spec.name}/{dataset}: {selected}")
    return selected


def _run_partition(
    *,
    experiment_id: str,
    experiment: str,
    model: str,
    config_path: Path = DEFAULT_CONFIG,
    execute: bool = False,
    shard_index: int = 0,
    shard_count: int = 1,
    writer_workers: int | None = None,
    smoke: bool = False,
    prepared_experiment_id: str | None = None,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    if not execute or not config.get("execution_enabled"):
        raise RQ1Error("real execution requires --execute and execution_enabled: true")
    spec = experiment_registry(config)[experiment]
    inference_adapter = dict(config["inference_adapter"])
    inference_adapter["adapter_sha256"] = stable_hash(inference_adapter)
    context_limit = int(
        VLLMInferenceConfig.load(config["unified"]["vllm"])
        .model(model)["max_model_len"]
    )
    paths = RunPaths.build(experiment_id, config)
    prepared_id = prepared_experiment_id or experiment_id
    prepared_paths = RunPaths.build(prepared_id, config)
    call_options = {
        "inference_adapter": inference_adapter,
        "context_limit": context_limit,
        "attention_output_root": paths.root / "attention" / model / experiment,
        "partial_output_root": (
            paths.root / "partial_responses" / model / experiment if smoke else None
        ),
    }
    index = json.loads((prepared_paths.prepared / "index.json").read_text())
    if index.get("experiment_id") != prepared_id:
        raise RQ1Error("prepared index experiment ID mismatch")
    recorded_index_sha256 = index.get("index_sha256")
    unsigned_index = dict(index)
    unsigned_index.pop("index_sha256", None)
    if not recorded_index_sha256 or stable_hash(unsigned_index) != recorded_index_sha256:
        raise RQ1Error("prepared index integrity hash mismatch")
    current_freeze = artifact_contract(config=config, code_files=SOURCE_FILES)
    recorded_freeze = index.get("runtime_freeze", {})
    allowed_freezes = compatible_runtime_freezes(
        prepared_paths.root / "runtime_compatibility.json",
        str(recorded_freeze.get("freeze_sha256")), current_freeze["freeze_sha256"],
    )
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise RQ1Error("invalid shard index/count")
    items = [
        item for item in index["cases"]
        if int(hashlib.sha256(str(item["opaque_incident_id"]).encode()).hexdigest(), 16) % shard_count == shard_index
    ]
    writer = AsyncWriter(
        int(writer_workers if writer_workers is not None else config["runtime"]["max_workers"])
    )
    completed = 0
    protocol_ineligible = 0
    failures = 0
    model_calls = 0
    try:
        for item in items:
            prepared = _read_prepared(prepared_paths, item)
            opaque = str(prepared.public["opaque_incident_id"])
            case_arms = _case_arms(
                spec, str(prepared.private["dataset"]), config, smoke=smoke,
            )
            trajectory_root = paths.trajectories / experiment / model
            if spec.task == "root_cause_handoff":
                handoff_targets = {
                    arm: trajectory_root / f"{opaque}__{arm}.json" for arm in case_arms
                }
                if all(_completed_target(path, allowed_freezes) for path in handoff_targets.values()):
                    continue
                observer_parts = representation_parts(
                    "R", prepared.public["rca_packet"], prepared.full_png,
                    prepared.routed_png, config, prepared.variant_pngs,
                    prepared.pixel_text_pngs,
                )
                observer_parts.append(text_part(stage1_prompt(spec, prepared.public)))
                shared_contract = _request_contract(
                    experiment_id=experiment_id, experiment=experiment, model=model,
                    execution_mode="smoke" if smoke else "formal",
                    opaque_incident_id=opaque, arm="R_shared", parts=observer_parts,
                    runtime_freeze_sha256=current_freeze["freeze_sha256"],
                )
                shared_key = str(shared_contract["call_key"])
                shared_path = trajectory_root / "_shared_stage1" / f"{opaque}.json"
                if _completed_target(shared_path, allowed_freezes):
                    shared = json.loads(shared_path.read_text(encoding="utf-8"))
                    # A capacity-only runtime successor may reuse a completed
                    # predecessor Stage 1.  Reconstruct that immutable request
                    # contract with the freeze recorded by the shared result;
                    # new Stage-2 calls still use ``current_freeze`` below.
                    retained_freeze = str(shared.get("runtime_freeze_sha256") or "")
                    shared_contract = _request_contract(
                        experiment_id=experiment_id, experiment=experiment, model=model,
                        execution_mode="smoke" if smoke else "formal",
                        opaque_incident_id=opaque, arm="R_shared", parts=observer_parts,
                        runtime_freeze_sha256=retained_freeze,
                    )
                    shared_key = str(shared_contract["call_key"])
                    if any(shared.get(key) != value for key, value in shared_contract.items()):
                        raise RQ1Error("shared Stage-1 resume contract differs from current request")
                    call1, raw1 = dict(shared["call"]), str(shared["raw_response"])
                    ledger, stage1_parse = dict(shared["normalized"]), bool(shared["parse"])
                    if str(shared.get("shared_stage1_call_key")) != shared_key:
                        raise RQ1Error("shared Stage-1 call key differs from its request contract")
                else:
                    model_calls += 1
                    call1, raw1 = _model_call(
                        model=model, system=OBSERVE_SYSTEM, parts=observer_parts,
                        schema=response_schema(spec, 1), **call_options,
                        partial_metadata={"case": opaque, "arm": "R_shared", "stage": 1},
                    )
                    try:
                        ledger = normalize_stage1_ledger(
                            parse_json_object(raw1), prepared.public["rca_packet"]
                        )
                        stage1_parse = ledger.get("schema_version") != "Stage1FailureV2"
                    except Exception as error:
                        ledger, stage1_parse = _stage1_failure(raw1, error), False
                    shared = {
                        **shared_contract, "status": "completed",
                        "shared_stage1_call_key": shared_key,
                        "call": call1, "raw_response": raw1, "normalized": ledger, "parse": stage1_parse,
                    }
                    shared["record_sha256"] = stable_hash(shared)
                    write_json(shared_path, shared)
                    shared_path.with_suffix(".md").parent.mkdir(parents=True, exist_ok=True)
                    shared_path.with_suffix(".md").write_text(
                        "# Shared Stage 1\n" + _prompt_markdown(1, call1["prompt"]) + "\n## Response\n" + raw1,
                        encoding="utf-8",
                    )
                ordered_arms = balanced_arm_order(case_arms, opaque, experiment)
                for order_index, arm in enumerate(ordered_arms):
                    target = handoff_targets[arm]
                    if _completed_target(target, allowed_freezes):
                        continue
                    stage2_parts = handoff_parts(arm, ledger, prepared.public["rca_packet"]["candidates"])
                    contract = _request_contract(
                        experiment_id=experiment_id, experiment=experiment, model=model,
                        execution_mode="smoke" if smoke else "formal",
                        opaque_incident_id=opaque, arm=arm, parts=stage2_parts,
                        runtime_freeze_sha256=current_freeze["freeze_sha256"],
                        extra={"registered_arm_order": list(ordered_arms),
                               "arm_order_index": order_index,
                               "shared_stage1_call_key": shared_key},
                    )
                    record = {
                        **contract,
                        "analysis_dataset": prepared.private["dataset"],
                        "analysis_fault_type": prepared.private.get("fault_type", "unknown"),
                        "status": "completed", "stage1_reference": str(shared_path.relative_to(paths.root)),
                        "visual_diagnostic": visual_diagnostic_for_arm(arm, spec.task, prepared.public),
                        "stages": [{"stage": 1, "parse": stage1_parse, "shared_stage1_call_key": shared_key,
                                    "normalized": ledger}],
                    }
                    conversation = [
                        "# RQ1 ledger-handoff RCA\n",
                        f"- case: `{opaque}`\n- arm: `{arm}`\n- model: `{model}`\n",
                        f"- shared Stage 1: `{shared_path.relative_to(paths.root)}`\n",
                    ]
                    try:
                        model_calls += 1
                        call2, raw2 = _model_call(
                            model=model, system=DIAGNOSE_SYSTEM, parts=stage2_parts,
                            schema=response_schema(spec, 2), **call_options,
                            partial_metadata={"case": opaque, "arm": arm, "stage": 2},
                        )
                        try:
                            final = validate_diagnosis(
                                parse_json_object(raw2), prepared.public["rca_packet"]["candidates"]
                            )
                            stage2_parse = True
                        except Exception as error:
                            final, stage2_parse = _stage1_failure(raw2, error), False
                        record["stages"].append({**call2, "stage": 2, "parse": stage2_parse, "normalized": final})
                        record["score"] = _score_rca(final, prepared.private, config)
                        conversation.extend(
                            (
                                _prompt_markdown(2, call2["prompt"]),
                                "\n## Stage 2 response\n",
                                raw2,
                                "\n",
                            )
                        )
                        completed += 1
                    except Exception as error:
                        record.update(status="infrastructure_error", error=f"{type(error).__name__}: {error}")
                        failures += 1
                    _sync_attention_status(record, prepared.public, paths)
                    record["record_sha256"] = stable_hash(record)
                    writer.json(target, record)
                    writer.bytes(target.with_suffix(".md"), "".join(conversation).encode())
                continue
            ordered_arms = balanced_arm_order(case_arms, opaque, experiment)
            for order_index, arm in enumerate(ordered_arms):
                target = trajectory_root / f"{opaque}__{arm}.json"
                if _completed_target(target, allowed_freezes):
                    continue
                if (spec.task == "root_cause_counterfactual"
                        and not prepared.private["counterfactual_pairs"]["eligible"]):
                    # No arm-specific model input exists for an ineligible
                    # transplant case.  Record the frozen label-blind exclusion
                    # before attempting to resolve targeted/placebo images.
                    contract = _request_contract(
                        experiment_id=experiment_id, experiment=experiment, model=model,
                        execution_mode="smoke" if smoke else "formal",
                        opaque_incident_id=opaque, arm=arm, parts=(),
                        runtime_freeze_sha256=current_freeze["freeze_sha256"],
                        extra={"registered_arm_order": list(ordered_arms),
                               "arm_order_index": order_index},
                    )
                    record = {
                        **contract,
                        "analysis_dataset": prepared.private["dataset"],
                        "analysis_fault_type": prepared.private.get("fault_type", "unknown"),
                        "status": "protocol_ineligible",
                        "reason": "label_blind_counterfactual_selector_ineligible",
                        "model_calls": 0,
                    }
                    record["record_sha256"] = stable_hash(record)
                    writer.json(target, record)
                    writer.bytes(
                        target.with_suffix(".md"),
                        ("# Protocol-ineligible counterfactual case\n" + canonical_json(record)).encode(),
                    )
                    protocol_ineligible += 1
                    continue
                if is_rca_task(spec):
                    parts = representation_parts(
                        arm, prepared.public["rca_packet"], prepared.full_png,
                        prepared.routed_png, config, prepared.variant_pngs,
                        prepared.pixel_text_pngs,
                    )
                else:
                    parts = qa_representation_parts(
                        arm, prepared.public["qa_packet"], prepared.qa_full_png,
                        prepared.pixel_text_pngs, prepared.qa_region_pngs,
                    )
                parts.append(text_part(stage1_prompt(spec, prepared.public)))
                contract = _request_contract(
                    experiment_id=experiment_id, experiment=experiment, model=model,
                    execution_mode="smoke" if smoke else "formal",
                    opaque_incident_id=opaque, arm=arm, parts=parts,
                    runtime_freeze_sha256=current_freeze["freeze_sha256"],
                    extra={"registered_arm_order": list(ordered_arms),
                           "arm_order_index": order_index},
                )
                record: dict[str, Any] = {**contract, "status": "completed", "stages": []}
                record["analysis_dataset"] = prepared.private["dataset"]
                record["analysis_fault_type"] = prepared.private.get("fault_type", "unknown")
                record["visual_diagnostic"] = visual_diagnostic_for_arm(arm, spec.task, prepared.public)
                if spec.task == "root_cause_counterfactual":
                    record["counterfactual_pair"] = prepared.private["counterfactual_pairs"].get(
                        arm.removeprefix("H_"), []
                    )
                conversation = ["# RQ1 trajectory\n", f"- case: `{opaque}`\n- arm: `{arm}`\n- model: `{model}`\n"]
                try:
                    first_system = (DIRECT_DIAGNOSE_SYSTEM if spec.task == "root_cause_direct"
                                    else OBSERVE_SYSTEM if is_rca_task(spec)
                                    else TYPED_OBSERVE_SYSTEM if spec.name == "typed_two_stage"
                                    else QA_SYSTEM)
                    qa_questions = (
                        prepared.public["legacy_questions"] if spec.task == "direct_visops" else
                        prepared.public["reasoning_questions"] if not is_rca_task(spec) else ()
                    )
                    model_calls += 1
                    call1, raw1 = _model_call(
                        model=model, system=first_system, parts=parts,
                        schema=response_schema(spec, 1, qa_questions), **call_options,
                        partial_metadata={"case": opaque, "arm": arm, "stage": 1},
                    )
                    try:
                        stage1 = parse_json_object(raw1)
                        if spec.task == "root_cause_direct":
                            stage1 = validate_diagnosis(
                                stage1, prepared.public["rca_packet"]["candidates"]
                            )
                        elif is_rca_task(spec):
                            stage1 = normalize_stage1_ledger(stage1, prepared.public["rca_packet"])
                        elif spec.name == "typed_two_stage":
                            stage1 = normalize_typed_qa_ledger(
                                stage1, prepared.public["reasoning_questions"],
                                prepared.public["qa_packet"],
                            )
                        else:
                            questions = (prepared.public["legacy_questions"] if spec.task == "direct_visops"
                                         else prepared.public["reasoning_questions"])
                            stage1 = validate_qa_response(stage1, questions)
                        stage1_parse = True
                    except Exception as error:
                        stage1, stage1_parse = _stage1_failure(raw1, error), False
                    record["stages"].append({**call1, "stage": 1, "parse": stage1_parse, "normalized": stage1})
                    conversation.extend(
                        (
                            _prompt_markdown(1, call1["prompt"]),
                            "\n## Stage 1 response\n",
                            raw1,
                            "\n",
                        )
                    )
                    final = stage1
                    if spec.stages == 2:
                        questions = prepared.public["reasoning_questions"] if spec.name == "typed_two_stage" else ()
                        stage2_parts = [text_part(stage2_prompt(
                            spec, stage1, prepared.public["rca_packet"]["candidates"], questions,
                        ))]
                        system = (DIAGNOSE_SYSTEM if is_rca_task(spec)
                                  else TYPED_ANSWER_SYSTEM if spec.name == "typed_two_stage" else QA_SYSTEM)
                        model_calls += 1
                        call2, raw2 = _model_call(
                            model=model, system=system, parts=stage2_parts,
                            schema=response_schema(spec, 2, questions), **call_options,
                            partial_metadata={"case": opaque, "arm": arm, "stage": 2},
                        )
                        try:
                            final = parse_json_object(raw2)
                            if is_rca_task(spec):
                                final = validate_diagnosis(final, prepared.public["rca_packet"]["candidates"])
                            else:
                                final = validate_qa_response(
                                    final, prepared.public["reasoning_questions"], typed=spec.name == "typed_two_stage",
                                )
                            stage2_parse = True
                        except Exception as error:
                            final, stage2_parse = _stage1_failure(raw2, error), False
                        record["stages"].append({**call2, "stage": 2, "parse": stage2_parse, "normalized": final})
                        conversation.extend(
                            (
                                _prompt_markdown(2, call2["prompt"]),
                                "\n## Stage 2 response\n",
                                raw2,
                                "\n",
                            )
                        )
                    if is_rca_task(spec):
                        record["score"] = _score_rca(final, prepared.private, config)
                    else:
                        questions = (prepared.private["legacy_questions"] if spec.task == "direct_visops"
                                     else prepared.private["reasoning_questions"])
                        record["score"] = score_reasoning(final, questions)
                    completed += 1
                except Exception as error:
                    record.update(status="infrastructure_error", error=f"{type(error).__name__}: {error}")
                    failures += 1
                    conversation.extend(("\n## Infrastructure error\n", record["error"], "\n"))
                _sync_attention_status(record, prepared.public, paths)
                record["record_sha256"] = stable_hash(record)
                writer.json(target, record)
                writer.bytes(target.with_suffix(".md"), "".join(conversation).encode())
    finally:
        writer.drain()
    current_records = []
    for item in items:
        prepared = _read_prepared(prepared_paths, item)
        opaque = str(prepared.public["opaque_incident_id"])
        for arm in _case_arms(spec, str(prepared.private["dataset"]), config, smoke=smoke):
            target = paths.trajectories / experiment / model / f"{opaque}__{arm}.json"
            if target.is_file():
                try:
                    current_records.append(json.loads(target.read_text(encoding="utf-8")))
                except json.JSONDecodeError:
                    pass
    result = {
        "completed": sum(row.get("status") == "completed" for row in current_records),
        "protocol_ineligible": sum(
            row.get("status") == "protocol_ineligible" for row in current_records
        ),
        "terminal_records": sum(
            row.get("status") in {"completed", "protocol_ineligible"}
            for row in current_records
        ),
        "infrastructure_errors": sum(row.get("status") == "infrastructure_error" for row in current_records),
        "expected_records": sum(
            len(_case_arms(
                spec, str(_read_prepared(prepared_paths, item).private["dataset"]), config,
                smoke=smoke,
            ))
            for item in items
        ),
        "newly_completed": completed,
        "new_protocol_ineligible": protocol_ineligible,
        "new_infrastructure_errors": failures,
        "new_model_calls": model_calls,
        "execution_mode": "smoke" if smoke else "formal",
        "experiment": experiment,
        "model": model,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "assigned_cases": len(items),
        "prepared_experiment_id": prepared_id,
    }
    write_json(paths.root / f"run_{experiment}_{model}_shard{shard_index:03d}-of-{shard_count:03d}.json", result)
    if shard_count == 1:
        write_json(paths.root / f"run_{experiment}_{model}.json", result)
    return result


def _concurrency_partitions(
    shard_index: int, shard_count: int, request_concurrency: int,
) -> tuple[tuple[int, int], ...]:
    """Split one registered shard into disjoint case-level worker residues."""

    if request_concurrency < 1 or request_concurrency > 4:
        raise RQ1Error("request_concurrency must be between one and four")
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise RQ1Error("invalid shard index/count")
    combined_count = shard_count * request_concurrency
    return tuple(
        (shard_index + worker * shard_count, combined_count)
        for worker in range(request_concurrency)
    )


def run(
    *,
    experiment_id: str,
    experiment: str,
    model: str,
    config_path: Path = DEFAULT_CONFIG,
    execute: bool = False,
    shard_index: int = 0,
    shard_count: int = 1,
    smoke: bool = False,
    prepared_experiment_id: str | None = None,
) -> dict[str, Any]:
    """Run different cases concurrently while preserving each case's arm order."""

    config = load_yaml(config_path)
    request_concurrency = int(config["runtime"]["request_concurrency"])
    partitions = _concurrency_partitions(shard_index, shard_count, request_concurrency)
    if request_concurrency == 1:
        return _run_partition(
            experiment_id=experiment_id, experiment=experiment, model=model,
            config_path=config_path, execute=execute,
            shard_index=shard_index, shard_count=shard_count,
            smoke=smoke,
            prepared_experiment_id=prepared_experiment_id,
        )
    with ThreadPoolExecutor(max_workers=request_concurrency) as pool:
        futures = [
            pool.submit(
                _run_partition,
                experiment_id=experiment_id, experiment=experiment, model=model,
                config_path=config_path, execute=execute,
                shard_index=worker_index, shard_count=worker_count,
                writer_workers=1,
                smoke=smoke,
                prepared_experiment_id=prepared_experiment_id,
            )
            for worker_index, worker_count in partitions
        ]
        worker_results = [future.result() for future in futures]
    # Worker partitions are disjoint. Consolidate their summaries directly;
    # calling the runner again could retry an infrastructure-error target and
    # would violate the bounded-smoke request budget.
    result = {
        "completed": sum(int(row["completed"]) for row in worker_results),
        "protocol_ineligible": sum(
            int(row.get("protocol_ineligible", 0)) for row in worker_results
        ),
        "terminal_records": sum(
            int(row.get("terminal_records", row["completed"])) for row in worker_results
        ),
        "infrastructure_errors": sum(
            int(row["infrastructure_errors"]) for row in worker_results
        ),
        "expected_records": sum(int(row["expected_records"]) for row in worker_results),
        "newly_completed": sum(int(row["newly_completed"]) for row in worker_results),
        "new_protocol_ineligible": sum(
            int(row.get("new_protocol_ineligible", 0)) for row in worker_results
        ),
        "new_infrastructure_errors": sum(
            int(row["new_infrastructure_errors"]) for row in worker_results
        ),
        "new_model_calls": sum(int(row["new_model_calls"]) for row in worker_results),
        "execution_mode": "smoke" if smoke else "formal",
        "experiment": experiment,
        "model": model,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "assigned_cases": sum(int(row["assigned_cases"]) for row in worker_results),
        "prepared_experiment_id": prepared_experiment_id or experiment_id,
        "request_concurrency": request_concurrency,
        "concurrency_unit": "different_cases_within_case_arm_order_serial",
        "worker_partitions": [
            {"shard_index": index, "shard_count": count}
            for index, count in partitions
        ],
        "worker_newly_completed": sum(int(row["newly_completed"]) for row in worker_results),
        "worker_new_infrastructure_errors": sum(
            int(row["new_infrastructure_errors"]) for row in worker_results
        ),
        "worker_new_model_calls": sum(int(row["new_model_calls"]) for row in worker_results),
    }
    paths = RunPaths.build(experiment_id, config)
    write_json(
        paths.root / f"run_{experiment}_{model}_shard{shard_index:03d}-of-{shard_count:03d}.json",
        result,
    )
    if shard_count == 1:
        write_json(paths.root / f"run_{experiment}_{model}.json", result)
    return result


def analyse(*, experiment_id: str, experiment: str, config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    records = [json.loads(path.read_text()) for path in (paths.trajectories / experiment).glob("*/*.json")]
    spec = experiment_registry(config)[experiment]
    index = json.loads((paths.prepared / "index.json").read_text(encoding="utf-8"))
    expected_models = tuple(map(str, config["runtime"]["models"]))
    expected_case_ids = tuple(str(item["opaque_incident_id"]) for item in index["cases"])
    result = analyze_records(
        records,
        spec,
        config,
        expected_models=expected_models,
        expected_case_ids=expected_case_ids,
    )
    if spec.task == "root_cause_handoff":
        shared = [json.loads(path.read_text()) for path in
                  (paths.trajectories / experiment).glob("*/_shared_stage1/*.json")]
        calls = [row.get("call") or {} for row in shared]
        result["shared_stage1_accounting"] = {
            "calls": len(calls),
            "total_input_tokens": sum(int(row.get("input_tokens") or 0) for row in calls),
            "total_output_tokens": sum(int(row.get("output_tokens") or 0) for row in calls),
            "total_wall_time_s": sum(float(row.get("wall_time_s") or 0) for row in calls),
        }
    expected = {
        (model, str(item["opaque_incident_id"]), arm)
        for model in expected_models
        for item in index["cases"]
        for arm in spec.arms
    }
    observed = {
        (str(row.get("model")), str(row.get("opaque_incident_id")), str(row.get("arm")))
        for row in records
    }
    missing, unexpected = expected - observed, observed - expected
    result["artifact_completeness"] = {
        "expected_records": len(expected),
        "observed_records": len(observed),
        "missing_records": len(missing),
        "unexpected_records": len(unexpected),
        "missing_examples": sorted(missing)[:10],
        "unexpected_examples": sorted(unexpected)[:10],
    }
    result["complete"] = bool(result.get("complete")) and not missing and not unexpected
    result.pop("analysis_sha256", None)
    result["analysis_sha256"] = stable_hash(result)
    write_json(paths.summary, result)
    return result


def compare_stages(*, experiment_id: str, config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Compare matched direct and ledger-mediated RCA without claiming causality."""

    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    load = lambda name: [json.loads(path.read_text()) for path in
                         (paths.trajectories / name).glob("*/*.json")]
    result = analyze_stage_pair(load("direct_rca"), load("matched_rca"), config)
    write_json(paths.root / "stage_comparison_direct_vs_matched.json", result)
    return result


def verify(*, experiment_id: str, config_path: Path = DEFAULT_CONFIG,
           prepared_experiment_id: str | None = None) -> dict[str, Any]:
    config = load_yaml(config_path)
    result_paths = RunPaths.build(experiment_id, config)
    prepared_paths = RunPaths.build(prepared_experiment_id, config) if prepared_experiment_id else result_paths
    result = verify_result_root(result_paths, config, prepared_paths)
    write_json(RunPaths.build(experiment_id, config).root / "verification.json", result)
    return result


def attention_overlay(
    *, experiment_id: str, opaque_incident_id: str, image_role: str,
    artifact_path: Path, output: Path | None = None, config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    """Ingest an external attention grid and produce an auditable overlay."""

    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    index = json.loads((paths.prepared / "index.json").read_text(encoding="utf-8"))
    item = next((row for row in index["cases"] if row["opaque_incident_id"] == opaque_incident_id), None)
    if item is None:
        raise RQ1Error(f"unknown prepared incident {opaque_incident_id!r}")
    public = json.loads((paths.root / item["public"]).read_text(encoding="utf-8"))
    atlases = public.get("visual_evidence_atlases") or {}
    atlas = atlases.get(image_role)
    region_ref = None
    if image_role.startswith("qa_region_"):
        _, _, region, page_text = image_role.split("_", 3)
        page = int(page_text) - 1
        region_ref = (region, page)
        atlas = (atlases.get("qa_regions") or {}).get(region, [])[page]
    if not isinstance(atlas, Mapping):
        raise RQ1Error(f"prepared case has no visual atlas role {image_role!r}")
    if image_role == "full":
        image_path = paths.root / item["full_image"]
    elif image_role == "qa_full":
        image_path = paths.root / item["qa_full_image"]
    elif image_role == "routed":
        image_path = paths.root / item["routed_image"]
    elif region_ref is not None:
        image_path = paths.root / item["qa_region_images"][region_ref[0]][region_ref[1]]
    else:
        relative = (item.get("variant_images") or {}).get(image_role)
        if not relative:
            raise RQ1Error(f"prepared case has no image role {image_role!r}")
        image_path = paths.root / relative
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    diagnostics = attention_diagnostics(artifact, atlas)
    output = output or paths.root / "attention" / f"{opaque_incident_id}.{image_role}.overlay.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(render_attention_overlay(image_path.read_bytes(), artifact, atlas))
    report = {
        **diagnostics, "overlay": str(output.relative_to(paths.root)),
        "artifact_sha256": stable_hash(artifact), "atlas_sha256": atlas["atlas_sha256"],
    }
    write_json(output.with_suffix(".json"), report)
    return report


def cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("experiment_id")
    p_prepare.add_argument("roster", type=Path)
    p_prepare.add_argument("--limit", type=int)
    p_prepare.add_argument("--output-shard-count", type=int, default=1)
    p_run = sub.add_parser("run")
    p_run.add_argument("experiment_id")
    p_run.add_argument("experiment", choices=("legacy_q9", "cross_region", "typed_two_stage", "direct_rca", "matched_rca", "visual_counterfactual_rca", "ledger_handoff_rca"))
    p_run.add_argument("model")
    p_run.add_argument("--execute", action="store_true")
    p_run.add_argument("--smoke", action="store_true")
    p_run.add_argument("--shard-index", type=int, default=0)
    p_run.add_argument("--shard-count", type=int, default=1)
    p_run.add_argument("--prepared-experiment-id")
    p_analyse = sub.add_parser("analyse")
    p_analyse.add_argument("experiment_id")
    p_analyse.add_argument("experiment")
    p_compare = sub.add_parser("compare-stages")
    p_compare.add_argument("experiment_id")
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("experiment_id")
    p_verify.add_argument("--prepared-experiment-id")
    p_attention = sub.add_parser("attention-overlay")
    p_attention.add_argument("experiment_id")
    p_attention.add_argument("opaque_incident_id")
    p_attention.add_argument("image_role")
    p_attention.add_argument("artifact", type=Path)
    p_attention.add_argument("--output", type=Path)
    sub.add_parser("static")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(experiment_id=args.experiment_id, roster=args.roster,
                         config_path=args.config, limit=args.limit,
                         output_shard_count=args.output_shard_count)
    elif args.command == "run":
        result = run(
            experiment_id=args.experiment_id, experiment=args.experiment,
            model=args.model, config_path=args.config, execute=args.execute,
            shard_index=args.shard_index, shard_count=args.shard_count,
            smoke=args.smoke, prepared_experiment_id=args.prepared_experiment_id,
        )
    elif args.command == "analyse":
        result = analyse(experiment_id=args.experiment_id, experiment=args.experiment, config_path=args.config)
    elif args.command == "compare-stages":
        result = compare_stages(experiment_id=args.experiment_id, config_path=args.config)
    elif args.command == "verify":
        result = verify(
            experiment_id=args.experiment_id, config_path=args.config,
            prepared_experiment_id=args.prepared_experiment_id,
        )
    elif args.command == "attention-overlay":
        result = attention_overlay(
            experiment_id=args.experiment_id, opaque_incident_id=args.opaque_incident_id,
            image_role=args.image_role, artifact_path=args.artifact,
            output=args.output, config_path=args.config,
        )
    else:
        from .tests import run_static_checks

        result = run_static_checks(args.config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())

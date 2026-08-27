"""Resumable RQ1.1 prepare, inference, analysis, and verification engine."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import multiprocessing as mp
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any, Mapping, Sequence

from unified_scripts import canonical_json, stable_hash
from unified_scripts.dataset_segmentation import CaseRecord, DatasetSegmentationConfig
from unified_scripts.vllm_inference import VLLMInferenceConfig
from vlmrca.vlm.attention_probe import map_groups_to_images, map_text_attention, render_overlay
from vlmrca.vlm.client import VLMResponse, call_vlm, count_vllm_prompt_tokens
from vlmrca.vlm.configs import get_config

from .exps import (
    PreparedCase,
    balanced_arm_order,
    direct_rca_prompt,
    execute_tool,
    experiment_registry,
    multi_stage_analysis_parts,
    planner_prompt,
    planner_schema,
    prepare_case,
    qa_prompt,
    qa_schema,
    rca_schema,
    representation_parts,
    score_qa,
    temporary_schema,
    tagged_text_part,
    validate_diagnosis,
    validate_qa,
    validate_temporary,
)
from .gates import analyze_direct_multi, analyze_records, verify_result_root
from .utils import (
    AsyncWriter,
    DEFAULT_CONFIG,
    ROOT,
    RQ1Error,
    RunPaths,
    atomic_write,
    load_yaml,
    parse_json_object,
    scorer,
    write_json,
)

SOURCE_ROOT = ROOT / "RQs" / "RQ1_1" / "src"


def _load_roster(path: Path, config: Mapping[str, Any]) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = [row for values in payload.get("datasets", {}).values() for row in values]
    if not rows:
        rows = list(payload.get("cases") or ())
    segmentation = DatasetSegmentationConfig.load(config["unified"]["segmentation"])
    result = []
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("dataset") or not row.get("case_id"):
            raise RQ1Error("preparation requires the evaluator-private roster with case IDs")
        dataset, case_id = str(row["dataset"]), str(row["case_id"])
        expected = segmentation.opaque_id(CaseRecord(dataset, case_id, Path(".")))
        opaque = str(row.get("opaque_incident_id") or expected)
        if opaque != expected:
            raise RQ1Error(f"roster opaque ID mismatch for {dataset}/{case_id}")
        result.append({"dataset": dataset, "case_id": case_id, "opaque_incident_id": opaque})
    return result


def _code_hashes() -> dict[str, str]:
    paths = sorted(path for path in SOURCE_ROOT.rglob("*.py") if "__pycache__" not in path.parts)
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def _run_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    vllm_config = VLLMInferenceConfig.load(config["unified"]["vllm"])
    launcher = (
        "serve_canvasrca_local.sh"
        if vllm_config.data["deployment"]["profile"] == "local"
        else "serve_canvasrca_nibi.sh"
    )
    shared_runtime_sources = [
        ROOT / "src/unified_scripts/vllm_inference.py",
        ROOT / "src/vlmrca/vlm/client.py",
        ROOT / "src/vlmrca/vlm/attention_probe.py",
        ROOT / "src/vlmrca/vlm/attention_probe_bootstrap/sitecustomize.py",
        ROOT / "src/vlmrca/vlm/configs.py",
        ROOT / "src/vlmrca/vlm/runtime_contract.py",
        ROOT / "scripts/vllm_vlm" / launcher,
    ]
    unified_sources = {
        key: (vllm_config.source if key == "vllm" else ROOT / path)
        for key, path in config["unified"].items()
    }
    value = {
        "schema_version": "RQ1_1RunContractV1",
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
            key: str(value["commit"]) for key, value in config["external_methods"].items()
        },
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
    region_paths: dict[str, list[Path]] = {}
    for region, images in prepared.region_pngs.items():
        region_paths[region] = []
        for page, image in enumerate(images, 1):
            path = paths.renders / f"{opaque}.region-{region}-{page:02d}.png"
            atomic_write(path, image)
            region_paths[region].append(path)
    return {
        "opaque_incident_id": opaque,
        "public": str(public_path.relative_to(paths.root)),
        "private": str(private_path.relative_to(paths.root)),
        "full_image": str(full_path.relative_to(paths.root)),
        "screenshot_images": [str(path.relative_to(paths.root)) for path in screenshot_paths],
        "region_images": {key: [str(path.relative_to(paths.root)) for path in values] for key, values in region_paths.items()},
        "public_sha256": hashlib.sha256(public_path.read_bytes()).hexdigest(),
        "private_sha256": hashlib.sha256(private_path.read_bytes()).hexdigest(),
        "full_image_sha256": hashlib.sha256(prepared.full_png).hexdigest(),
        "screenshot_image_sha256": [hashlib.sha256(value).hexdigest() for value in prepared.screenshot_pngs],
        "region_image_sha256": {key: [hashlib.sha256(value).hexdigest() for value in values] for key, values in prepared.region_pngs.items()},
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
        "schema_version": "RQ1_1PreparedIndexV1",
        "experiment_id": experiment_id,
        "case_count": len(entries),
        "cases": sorted((dict(row) for row in entries), key=lambda row: row["opaque_incident_id"]),
        "run_contract": dict(contract),
        "preparation_complete": complete,
    }
    index["index_sha256"] = stable_hash(index)
    write_json(paths.prepared / ("index.json" if complete else "index.partial.json"), index)
    return index


def prepare(
    *, experiment_id: str, roster: Path, config_path: Path = DEFAULT_CONFIG,
    limit: int | None = None, output_shard_count: int = 1,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    rows = _load_roster(roster, config)
    if limit is not None:
        rows = rows[:limit]
    if output_shard_count < 1:
        raise RQ1Error("output shard count must be positive")
    contract = _run_contract(config)
    ids = [
        experiment_id if output_shard_count == 1 else f"{experiment_id}__shard-{index:04d}-of-{output_shard_count:04d}"
        for index in range(output_shard_count)
    ]
    paths = [RunPaths.build(value, config) for value in ids]
    entries: list[list[dict[str, Any]]] = [[] for _ in paths]
    assignments = {
        row["opaque_incident_id"]: int(hashlib.sha256(row["opaque_incident_id"].encode()).hexdigest(), 16)
        % output_shard_count
        for row in rows
    }
    workers = max(1, min(4, int(config["runtime"]["max_workers"])))
    row_iter = iter(rows)
    # Matplotlib renderer state is process-global and is not thread-safe. Keep
    # one renderer task per isolated process in flight and persist every case
    # immediately so an interrupted local preparation remains resumable.
    # ``spawn`` is required here: the parent imports matplotlib plus numerical
    # runtimes before preparation.  Forking that process can inherit native
    # font/BLAS locks and leave workers sleeping forever on a futex.
    with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
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
        raise RQ1Error("prepared public artifact hash mismatch")
    if hashlib.sha256(private_path.read_bytes()).hexdigest() != item["private_sha256"]:
        raise RQ1Error("prepared private artifact hash mismatch")
    full = (paths.root / item["full_image"]).read_bytes()
    screenshots = tuple((paths.root / path).read_bytes() for path in item["screenshot_images"])
    regions = {key: tuple((paths.root / path).read_bytes() for path in values) for key, values in item["region_images"].items()}
    return PreparedCase(
        json.loads(public_path.read_text()), json.loads(private_path.read_text()), full, screenshots, regions
    )


def _parse(text: str) -> dict[str, Any]:
    return parse_json_object(text)


def _normalize_model_output(
    raw: str, validator: Any, fallback: Mapping[str, Any]
) -> tuple[dict[str, Any], str | None]:
    """Normalize a model answer without turning answer mistakes into infra failures."""

    try:
        return dict(validator(_parse(raw))), None
    except (RQ1Error, KeyError, TypeError, ValueError) as error:
        return dict(fallback), f"{type(error).__name__}: {error}"


def _finish_reason(response: VLMResponse) -> str:
    return str((response.raw or {}).get("finish_reason") or "unknown")


def _image_attention_diagnostics(
    artifact: Mapping[str, Any], part: Mapping[str, Any],
) -> dict[str, Any]:
    """Aggregate one within-image grid over its registered semantic regions."""

    semantic = str(part.get("attention_region") or "unassigned_image")
    if semantic != "dashboard":
        return {
            "semantic_region": semantic,
            "within_image_region_mass": {semantic: 1.0},
            "global_region_mass": {semantic: float(artifact["global_attention_mass"])},
        }
    boxes = part.get("attention_region_boxes") or {}
    columns, rows = map(int, artifact["grid"])
    width, height = map(int, artifact["image_size_px"])
    region_mass = {
        region: 0.0
        for region in ("dashboard_header_band", "M", "R", "L", "G")
    }
    unassigned = 0.0
    for index, weight in enumerate(map(float, artifact["weights"])):
        row, column = divmod(index, columns)
        x, y = (column + 0.5) * width / columns, (row + 0.5) * height / rows
        # The historical 16x16 overlays visibly concentrated on their first
        # row.  At this resolution that row is the smallest honest title/header
        # mask: trying to draw a tighter pixel box would imply spatial
        # precision the visual-token grid does not possess.  Test it before the
        # inherited M/G crop boxes so header attention is no longer silently
        # counted as telemetry evidence.
        matched = "dashboard_header_band" if row == 0 else next((
            region for region in ("M", "R", "L", "G")
            if any(left <= x < right and top <= y < bottom for left, top, right, bottom in boxes.get(region, ()))
        ), None)
        if matched is None:
            unassigned += weight
        else:
            region_mass[matched] += weight
    region_mass["unassigned_image"] = unassigned
    global_mass = float(artifact["global_attention_mass"])
    return {
        "semantic_region": semantic,
        "within_image_region_mass": region_mass,
        "global_region_mass": {region: mass * global_mass for region, mass in region_mass.items()},
        "top_grid_row_mass": sum(map(float, artifact["weights"][:columns])),
        "top_left_grid_cell_mass": float(artifact["weights"][0]),
        "spatial_resolution_note": (
            "dashboard_header_band is the first row of the registered attention grid; "
            "it is not a pixel-exact title segmentation"
        ),
    }


def _call(
    *, model: str, system: str, parts: list[dict[str, Any]], schema: Mapping[str, Any],
    config: Mapping[str, Any], partial_root: Path | None, metadata: Mapping[str, Any],
    attention_root: Path,
) -> tuple[dict[str, Any], str]:
    adapter = config["inference_adapter"]
    model_cfg = get_config(model, max_tokens=int(adapter["max_tokens"]))
    vllm_config = VLLMInferenceConfig.load(config["unified"]["vllm"])
    context = int(vllm_config.model(model)["max_model_len"])
    prompt_tokens = count_vllm_prompt_tokens(parts, model_cfg, system=system)
    text_tokens = count_vllm_prompt_tokens(parts, model_cfg, system=system, text_only=True)
    if prompt_tokens is None or text_tokens is None:
        raise RQ1Error("live tokenizer preflight failed")
    if prompt_tokens + model_cfg.max_tokens > context:
        raise RQ1Error(f"prompt plus output budget exceeds context: {prompt_tokens}+{model_cfg.max_tokens}>{context}")
    started = time.time()
    response = call_vlm(
        parts, model=model_cfg, system=system, max_retries=1,
        response_format=dict(schema), partial_output_dir=partial_root,
        partial_metadata=dict(metadata),
    )
    finish = _finish_reason(response)
    request_id = str((response.raw or {}).get("request_id") or "")
    probe = (response.raw or {}).get("attention_probe")
    if not request_id or not isinstance(probe, Mapping):
        raise RQ1Error("request completed without required same-prefill multimodal attention")
    call_root = attention_root / hashlib.sha256(request_id.encode()).hexdigest()
    call_root.mkdir(parents=True, exist_ok=True)
    raw_path = call_root / "raw_probe.json"
    text_path = call_root / "text_attention.json"
    write_json(raw_path, probe)
    text_attention = map_text_attention(
        probe, vllm_config.model_path(model), system, parts,
    )
    if text_attention["unmatched_sources"]:
        raise RQ1Error(f"attention text-span mapping failed: {text_attention['unmatched_sources']}")
    write_json(text_path, text_attention)
    images = [(part, part["png"]) for part in parts if part["type"] == "image"]
    mapped = map_groups_to_images(probe, [png for _, png in images]) if images else []
    image_artifacts = []
    for index, ((part, png), artifact) in enumerate(zip(images, mapped, strict=True)):
        artifact = {**artifact, "diagnostics": _image_attention_diagnostics(artifact, part)}
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
    return [f"# RQ1.1 {experiment}\n", f"- model: `{model}`\n- case: `{opaque}`\n- arm: `{arm}`\n"]


def _append_call(conversation: list[str], title: str, call: Mapping[str, Any]) -> None:
    conversation.extend([
        f"\n## {title}\n", "### System\n", str(call["system"]), "\n### User parts\n",
        canonical_json(call["parts"]), "\n### Raw response\n", str(call["response_text"]), "\n",
    ])


def _smoke_arms(spec: Any, dataset: str, model: str, config: Mapping[str, Any]) -> tuple[str, ...]:
    plan = config["smoke_plans"][spec.name]
    if spec.name == "multi_stage_rca":
        return tuple(map(str, (plan.get(model) or {}).get(dataset) or ()))
    return tuple(map(str, plan.get(dataset) or ()))


def _run_case(
    *, prepared: PreparedCase, paths: RunPaths, spec: Any, experiment: str, model: str,
    config: Mapping[str, Any], contract_hash: str, smoke: bool, writer: AsyncWriter,
) -> dict[str, int]:
    opaque = str(prepared.public["opaque_incident_id"])
    dataset = str(prepared.private["dataset"])
    arms = _smoke_arms(spec, dataset, model, config) if smoke else spec.arms
    arms = balanced_arm_order(arms, opaque, experiment)
    root = paths.trajectories / experiment / model
    attention_root = paths.root / "attention" / model / experiment
    counts = {"completed": 0, "errors": 0, "calls": 0, "skipped": 0}
    for arm in arms:
        initiated_calls = 0
        target = root / f"{opaque}__{arm}.json"
        if target.is_file():
            try:
                if json.loads(target.read_text()).get("status") == "completed":
                    counts["skipped"] += 1
                    continue
            except json.JSONDecodeError:
                pass
        call_key = stable_hash({
            "contract": contract_hash, "experiment": experiment, "model": model,
            "case": opaque, "arm": arm, "smoke": smoke,
        })
        record: dict[str, Any] = {
            "schema_version": "RQ1_1TrajectoryV1", "experiment": experiment,
            "model": model, "opaque_incident_id": opaque, "arm": arm,
            "analysis_dataset": dataset, "analysis_fault_type": prepared.private.get("fault_type", "unknown"),
            "run_contract_sha256": contract_hash, "call_key": call_key,
            "status": "completed", "stages": [], "model_output_errors": [],
        }
        conversation = _conversation_header(experiment, model, opaque, arm)
        partial = paths.root / "partial_responses" / experiment / model if smoke else None
        try:
            if spec.task == "direct_rca":
                parts = representation_parts(arm, prepared)
                counts["calls"] += 1
                initiated_calls += 1
                call, raw = _call(
                    model=model, system=direct_rca_prompt(prepared.public["packet"]), parts=parts,
                    schema=rca_schema(), config=config, partial_root=partial,
                    metadata={"case": opaque, "arm": arm, "experiment": experiment},
                    attention_root=attention_root,
                )
                _append_call(conversation, "Direct RCA", call)
                final, output_error = _normalize_model_output(
                    raw,
                    lambda value: validate_diagnosis(value, prepared.public["packet"]["candidates"]),
                    {"services": [], "reason": "", "confidence": "low"},
                )
                if output_error:
                    record["model_output_errors"].append({"stage": 1, "error": output_error})
                record["stages"].append({
                    **call, "stage": 1, "parse": output_error is None,
                    "normalized": final, "output_error": output_error,
                })
                record["score"] = _score_rca(final, prepared.private, config)
            elif spec.task == "direct_qa":
                level = int(arm.removeprefix("L"))
                question = next(row for row in prepared.public["selected_questions"] if int(row["reasoning_level"]) == level)
                private_question = next(row for row in prepared.private["selected_questions"] if int(row["reasoning_level"]) == level)
                parts = [*representation_parts("V", prepared), tagged_text_part(qa_prompt(question), "task_question")]
                counts["calls"] += 1
                initiated_calls += 1
                call, raw = _call(
                    model=model, system=QA_GUIDE_SYSTEM, parts=parts, schema=qa_schema(level),
                    config=config, partial_root=partial,
                    metadata={"case": opaque, "arm": arm, "experiment": experiment},
                    attention_root=attention_root,
                )
                _append_call(conversation, "Direct QA", call)
                fallback = {"steps": [
                    {"region": region, "values": []} for region in question["region_path"]
                ]}
                final, output_error = _normalize_model_output(
                    raw, lambda value, question=question: validate_qa(value, question), fallback,
                )
                if output_error:
                    record["model_output_errors"].append({"stage": 1, "error": output_error})
                record["question"] = question
                record["stages"].append({
                    **call, "stage": 1, "parse": output_error is None,
                    "normalized": final, "output_error": output_error,
                })
                record["score"] = score_qa(final, private_question)
            else:
                history: list[dict[str, Any]] = []
                steps = spec.steps
                if smoke and arm != str(config["smoke_plans"]["multi_stage_rca"]["full_arm"]):
                    steps = 1
                    record["smoke_partial_protocol"] = "first_step_only"
                for step in range(1, steps + 1):
                    planner_parts = [
                        *representation_parts(arm, prepared),
                        tagged_text_part(planner_prompt(prepared.public["packet"], step, history), "task_history"),
                    ]
                    counts["calls"] += 1
                    initiated_calls += 1
                    call1, raw1 = _call(
                        model=model, system=PLANNER_SYSTEM, parts=planner_parts,
                        schema=planner_schema(), config=config, partial_root=partial,
                        metadata={"case": opaque, "arm": arm, "experiment": experiment, "step": step, "stage": "tool"},
                        attention_root=attention_root,
                    )
                    _append_call(conversation, f"Step {step} planner", call1)
                    action, planner_error = _normalize_model_output(
                        raw1, lambda value: value,
                        {"tool": "invalid_model_output", "arguments": {}},
                    )
                    if planner_error:
                        record["model_output_errors"].append({
                            "step": step, "stage": "planner", "error": planner_error,
                        })
                    observation = execute_tool(action, prepared.public["tool_index"], config)
                    conversation.extend(["\n### Host tool observation\n", canonical_json(observation), "\n"])
                    # Planner and analysis are separate stateless API calls.
                    # Replaying the identical arm representation here is the
                    # only way the ranking update can use the visual/text
                    # evidence that motivated the tool action; the tool result
                    # alone would collapse every arm into a text-only handoff.
                    analysis_parts = multi_stage_analysis_parts(
                        arm, prepared, step, history, observation,
                    )
                    counts["calls"] += 1
                    initiated_calls += 1
                    call2, raw2 = _call(
                        model=model, system=ANALYSIS_SYSTEM, parts=analysis_parts,
                        schema=temporary_schema(), config=config, partial_root=partial,
                        metadata={"case": opaque, "arm": arm, "experiment": experiment, "step": step, "stage": "analysis"},
                        attention_root=attention_root,
                    )
                    _append_call(conversation, f"Step {step} analysis", call2)
                    temporary, analysis_error = _normalize_model_output(
                        raw2,
                        lambda value: validate_temporary(value, prepared.public["packet"]["candidates"]),
                        {"temporary_services": [], "analysis": "", "confidence": "low"},
                    )
                    if analysis_error:
                        record["model_output_errors"].append({
                            "step": step, "stage": "analysis", "error": analysis_error,
                        })
                    stage = {
                        "step": step, "planner": {**call1, "parse": planner_error is None,
                        "output_error": planner_error}, "tool_action": action,
                        "tool_observation": observation,
                        "analysis": {**call2, "parse": analysis_error is None,
                        "output_error": analysis_error}, "temporary_ranking": temporary,
                    }
                    record["stages"].append(stage)
                    history.append({"step": step, "tool": action, "observation": observation, "temporary_ranking": temporary})
                if steps == 3:
                    last = record["stages"][-1]["temporary_ranking"]
                    final = {"services": last["temporary_services"], "reason": last["analysis"], "confidence": last["confidence"]}
                    record["final"] = final
                    record["score"] = _score_rca(final, prepared.private, config)
                else:
                    record["smoke_partial_complete"] = True
            counts["completed"] += 1
        except Exception as error:  # preserve every terminal failure as an auditable record
            record.update(status="infrastructure_error", error=f"{type(error).__name__}: {error}")
            conversation.extend(["\n## Error\n", record["error"], "\n"])
            counts["errors"] += 1
        record["model_output_valid"] = not record.get("model_output_errors")
        record["model_calls"] = initiated_calls
        record["record_sha256"] = stable_hash(record)
        writer.json(target, record)
        writer.bytes(target.with_suffix(".md"), "".join(conversation).encode())
    return counts


QA_GUIDE_SYSTEM = "You are a precise visual telemetry reader. Follow the requested region path and output only schema-valid JSON."
PLANNER_SYSTEM = "You are the action-selection phase of a bounded microservice RCA agent. Select exactly one registered tool call."
ANALYSIS_SYSTEM = "You are the evidence-analysis phase of a bounded microservice RCA agent. Update the temporary ranking from supplied public evidence only."


def run(
    *, experiment_id: str, experiment: str, model: str, config_path: Path = DEFAULT_CONFIG,
    execute: bool = False, shard_index: int = 0, shard_count: int = 1,
    smoke: bool = False, prepared_experiment_id: str | None = None,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    if not execute:
        raise RQ1Error("model execution requires --execute")
    if not smoke and not config.get("execution_enabled"):
        raise RQ1Error("formal execution remains disabled until smoke and freeze")
    if model not in config["runtime"]["models"]:
        raise RQ1Error(f"unregistered RQ1.1 model {model}")
    spec = experiment_registry(config)[experiment]
    result_paths = RunPaths.build(experiment_id, config)
    prepared_paths = RunPaths.build(prepared_experiment_id or experiment_id, config)
    index = json.loads((prepared_paths.prepared / "index.json").read_text())
    recorded = index.get("index_sha256")
    unsigned = dict(index); unsigned.pop("index_sha256", None)
    if stable_hash(unsigned) != recorded:
        raise RQ1Error("prepared index hash mismatch")
    items = [
        item for item in index["cases"]
        if int(hashlib.sha256(item["opaque_incident_id"].encode()).hexdigest(), 16) % shard_count == shard_index
    ]
    contract = _run_contract(config)
    concurrency = 1 if smoke else min(4, int(config["runtime"]["request_concurrency"]))
    writer = AsyncWriter(int(config["runtime"]["max_workers"]))

    def work(item: Mapping[str, Any]) -> dict[str, int]:
        return _run_case(
            prepared=_read_prepared(prepared_paths, item), paths=result_paths, spec=spec,
            experiment=experiment, model=model, config=config,
            contract_hash=contract["contract_sha256"], smoke=smoke, writer=writer,
        )

    try:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            rows = list(pool.map(work, items))
    finally:
        writer.drain()
    result = {
        "schema_version": "RQ1_1RunSummaryV1", "experiment_id": experiment_id,
        "prepared_experiment_id": prepared_experiment_id or experiment_id,
        "experiment": experiment, "model": model, "smoke": smoke,
        "shard_index": shard_index, "shard_count": shard_count,
        "assigned_cases": len(items),
        "completed": sum(row["completed"] for row in rows),
        "infrastructure_errors": sum(row["errors"] for row in rows),
        "model_calls": sum(row["calls"] for row in rows),
        "resumed_records": sum(row["skipped"] for row in rows),
        "run_contract": contract,
    }
    write_json(result_paths.root / f"run_{experiment}_{model}_shard{shard_index:03d}-of-{shard_count:03d}.json", result)
    return result


def analyse(*, experiment_id: str, experiment: str, config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    records = [json.loads(path.read_text()) for path in (paths.trajectories / experiment).glob("*/*.json")]
    result = analyze_records(records, experiment_registry(config)[experiment], config)
    write_json(paths.root / f"summary_{experiment}.json", result)
    return result


def analyse_suite(*, experiment_id: str, config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    load = lambda experiment: [
        json.loads(path.read_text())
        for path in (paths.trajectories / experiment).glob("*/*.json")
    ]
    result = analyze_direct_multi(load("direct_rca"), load("multi_stage_rca"), config)
    write_json(paths.root / "summary_direct_vs_multi_stage.json", result)
    return result


def verify(*, experiment_id: str, config_path: Path = DEFAULT_CONFIG, prepared_experiment_id: str | None = None) -> dict[str, Any]:
    config = load_yaml(config_path)
    result = verify_result_root(
        RunPaths.build(experiment_id, config), config,
        RunPaths.build(prepared_experiment_id or experiment_id, config),
    )
    write_json(RunPaths.build(experiment_id, config).root / "verification.json", result)
    return result


def mark_smoke_timeout(
    *, experiment_id: str, experiment: str, model: str,
    config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    """Finalize streaming checkpoints left by the bounded smoke supervisor."""

    config = load_yaml(config_path)
    root = RunPaths.build(experiment_id, config).root / "partial_responses" / experiment / model
    changed = 0
    for path in root.glob("*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("status") == "streaming":
            value["status"] = "timeout_partial"
            value["timeout_marked_unix_s"] = time.time()
            write_json(path, value)
            changed += 1
    return {"experiment_id": experiment_id, "experiment": experiment, "model": model, "timeout_partials": changed}


def cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("experiment_id"); p.add_argument("roster", type=Path); p.add_argument("--limit", type=int); p.add_argument("--output-shard-count", type=int, default=1)
    p = sub.add_parser("run")
    p.add_argument("experiment_id"); p.add_argument("experiment", choices=("direct_qa", "direct_rca", "multi_stage_rca")); p.add_argument("model")
    p.add_argument("--execute", action="store_true"); p.add_argument("--smoke", action="store_true"); p.add_argument("--shard-index", type=int, default=0); p.add_argument("--shard-count", type=int, default=1); p.add_argument("--prepared-experiment-id")
    p = sub.add_parser("analyse"); p.add_argument("experiment_id"); p.add_argument("experiment")
    p = sub.add_parser("analyse-suite"); p.add_argument("experiment_id")
    p = sub.add_parser("verify"); p.add_argument("experiment_id"); p.add_argument("--prepared-experiment-id")
    p = sub.add_parser("mark-smoke-timeout"); p.add_argument("experiment_id"); p.add_argument("experiment"); p.add_argument("model")
    sub.add_parser("static")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(experiment_id=args.experiment_id, roster=args.roster, config_path=args.config, limit=args.limit, output_shard_count=args.output_shard_count)
    elif args.command == "run":
        result = run(experiment_id=args.experiment_id, experiment=args.experiment, model=args.model, config_path=args.config, execute=args.execute, smoke=args.smoke, shard_index=args.shard_index, shard_count=args.shard_count, prepared_experiment_id=args.prepared_experiment_id)
    elif args.command == "analyse":
        result = analyse(experiment_id=args.experiment_id, experiment=args.experiment, config_path=args.config)
    elif args.command == "analyse-suite":
        result = analyse_suite(experiment_id=args.experiment_id, config_path=args.config)
    elif args.command == "verify":
        result = verify(experiment_id=args.experiment_id, config_path=args.config, prepared_experiment_id=args.prepared_experiment_id)
    elif args.command == "mark-smoke-timeout":
        result = mark_smoke_timeout(experiment_id=args.experiment_id, experiment=args.experiment, model=args.model, config_path=args.config)
    else:
        from .tests import run_static_checks
        result = run_static_checks(args.config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())

"""Resumable RQ1.1 prepare, inference, analysis, and verification engine."""

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
    REGIONS,
    PreparedCase,
    balanced_arm_order,
    build_reasoning_trace,
    counterfactual_rca_parts,
    direct_rca_parts,
    RCA_SYSTEM_ROLE,
    execute_tool,
    experiment_registry,
    multi_stage_analysis_parts,
    planner_prompt,
    planner_schema,
    prepare_case,
    qa_prompt,
    qa_arm_parts,
    representation_guide_part,
    qa_value_support,
    qa_schema,
    reasoning_trace_svg,
    rca_schema,
    representation_parts,
    score_qa,
    temporary_schema,
    tagged_text_part,
    validate_diagnosis,
    validate_qa,
    validate_temporary,
)
from .gates import analyze_perception_rca, analyze_records, verify_result_root
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


def _vllm_config_path(config: Mapping[str, Any]) -> str:
    """Resolve the explicit deployment projection selected by the environment."""

    return os.environ.get("CANVASRCA_VLLM_CONFIG", str(config["unified"]["vllm"]))


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
    # Renderer sources have their own explicit contract section below. Keeping
    # this map to the six RQ package modules avoids recording identical hashes
    # twice while preserving the semantic renderer boundary.
    paths = sorted(SOURCE_ROOT.glob("*.py"))
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def _run_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    vllm_config = VLLMInferenceConfig.load(_vllm_config_path(config))
    launcher = (
        "serve_canvasrca_local.sh"
        if vllm_config.data["deployment"]["profile"] == "local"
        else "serve_canvasrca_nibi.sh"
    )
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
    public_schedule_path = paths.prepared / "qa_schedules" / f"{opaque}.json"
    private_schedule_path = paths.private / "qa_schedules" / f"{opaque}.json"
    public_schedule = {
        "schema_version": "RQ1_1QASelectionScheduleV1",
        "opaque_incident_id": opaque,
        "selection_policy": "provisional_case_local_until_roster_finalize",
        "selected_questions": list(prepared.public.get("selected_questions") or ()),
    }
    private_schedule = {
        **public_schedule,
        "selected_questions": list(prepared.private.get("selected_questions") or ()),
    }
    write_json(public_schedule_path, public_schedule)
    write_json(private_schedule_path, private_schedule)
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
    variant_paths = {}
    for arm, image in prepared.counterfactual_pngs.items():
        path = paths.renders / f"{opaque}.counterfactual-{arm}.png"
        atomic_write(path, image); variant_paths[arm] = path
    return {
        "opaque_incident_id": opaque,
        "public": str(public_path.relative_to(paths.root)),
        "private": str(private_path.relative_to(paths.root)),
        "full_image": str(full_path.relative_to(paths.root)),
        "screenshot_images": [str(path.relative_to(paths.root)) for path in screenshot_paths],
        "region_images": {key: [str(path.relative_to(paths.root)) for path in values] for key, values in region_paths.items()},
        "counterfactual_images": {key: str(path.relative_to(paths.root)) for key, path in variant_paths.items()},
        "public_sha256": hashlib.sha256(public_path.read_bytes()).hexdigest(),
        "private_sha256": hashlib.sha256(private_path.read_bytes()).hexdigest(),
        "qa_public_schedule": str(public_schedule_path.relative_to(paths.root)),
        "qa_private_schedule": str(private_schedule_path.relative_to(paths.root)),
        "qa_public_schedule_sha256": hashlib.sha256(public_schedule_path.read_bytes()).hexdigest(),
        "qa_private_schedule_sha256": hashlib.sha256(private_schedule_path.read_bytes()).hexdigest(),
        "full_image_sha256": hashlib.sha256(prepared.full_png).hexdigest(),
        "screenshot_image_sha256": [hashlib.sha256(value).hexdigest() for value in prepared.screenshot_pngs],
        "region_image_sha256": {key: [hashlib.sha256(value).hexdigest() for value in values] for key, values in prepared.region_pngs.items()},
        "counterfactual_image_sha256": {key: hashlib.sha256(value).hexdigest() for key, value in prepared.counterfactual_pngs.items()},
        "qa_question_schedule": [
            {
                key: question[key] for key in (
                    "query_id", "perception_difficulty", "reasoning_difficulty",
                    "reasoning_family", "region_path", "requested_reasoning_difficulty",
                    "requested_region_path", "selection_fallback",
                )
            }
            for question in prepared.public["selected_questions"]
        ],
    }


def _finalize_balanced_qa_schedules(
    paths: Sequence[RunPaths], entries: Sequence[list[dict[str, Any]]], seed: int,
) -> dict[str, Any]:
    """Select one answerable question per P level across the complete roster.

    Scarce eligibility is handled before abundant cells.  The selected cell is
    then the least-used eligible (reasoning difficulty, ordered region path),
    with deterministic response-blind tie breaks.  This balances the realized
    questions rather than merely balancing requests that may later fall back.
    """

    records: dict[str, tuple[RunPaths, dict[str, Any], dict[int, dict[tuple[int, str], dict[str, Any]]]]] = {}
    for run_paths, shard_entries in zip(paths, entries, strict=True):
        for entry in shard_entries:
            opaque = str(entry["opaque_incident_id"])
            private = json.loads((run_paths.root / entry["private"]).read_text())
            pools: dict[int, dict[tuple[int, str], dict[str, Any]]] = {}
            for question in private.get("all_question_templates") or ():
                level = int(question["perception_difficulty"])
                cell = (int(question["reasoning_difficulty"]), "".join(question["region_path"]))
                prior = pools.setdefault(level, {}).get(cell)
                if prior is None or str(question["query_id"]) < str(prior["query_id"]):
                    pools[level][cell] = dict(question)
            records[opaque] = (run_paths, entry, pools)

    selected: dict[str, list[dict[str, Any]]] = {opaque: [] for opaque in records}
    level_audits: dict[str, Any] = {}
    for level in range(1, 5):
        availability: dict[tuple[int, str], int] = {}
        for _, _, pools in records.values():
            for cell in pools.get(level, {}):
                availability[cell] = availability.get(cell, 0) + 1
        counts: dict[tuple[int, str], int] = {}
        eligible = [opaque for opaque, (_, _, pools) in records.items() if pools.get(level)]
        eligible.sort(key=lambda opaque: (
            len(records[opaque][2][level]),
            hashlib.sha256(f"{seed}:{opaque}:P{level}:case".encode()).hexdigest(),
        ))
        for opaque in eligible:
            cells = records[opaque][2][level]
            cell = min(cells, key=lambda value: (
                counts.get(value, 0),
                sum(total for (reasoning, _), total in counts.items() if reasoning == value[0]),
                availability[value],
                hashlib.sha256(f"{seed}:{opaque}:P{level}:{value[0]}:{value[1]}".encode()).hexdigest(),
            ))
            question = dict(cells[cell])
            question.update(
                requested_reasoning_difficulty=question["reasoning_difficulty"],
                requested_region_path=list(question["region_path"]), selection_fallback=False,
            )
            selected[opaque].append(question)
            counts[cell] = counts.get(cell, 0) + 1
        values = list(counts.values())
        level_audits[str(level)] = {
            "eligible_cases": len(eligible), "covered_cells": len(counts),
            "minimum_cell_count": min(values) if values else 0,
            "maximum_cell_count": max(values) if values else 0,
            "reasoning_counts": {
                str(reasoning): sum(total for (value, _), total in counts.items() if value == reasoning)
                for reasoning in (1, 2, 3)
            },
            "cell_counts": {f"R{reasoning}:{path}": total for (reasoning, path), total in sorted(counts.items())},
        }

    for opaque, (run_paths, entry, _) in records.items():
        private_questions = sorted(selected[opaque], key=lambda row: int(row["perception_difficulty"]))
        public_questions = [
            {key: value for key, value in row.items() if key not in {"answer_steps", "supporting_fact_ids"}}
            for row in private_questions
        ]
        common = {
            "schema_version": "RQ1_1QASelectionScheduleV1", "opaque_incident_id": opaque,
            "selection_policy": "roster_balanced_visible_eligibility_v1",
        }
        public_payload = {**common, "selected_questions": public_questions}
        private_payload = {**common, "selected_questions": private_questions}
        public_path = run_paths.root / entry["qa_public_schedule"]
        private_path = run_paths.root / entry["qa_private_schedule"]
        write_json(public_path, public_payload); write_json(private_path, private_payload)
        entry["qa_public_schedule_sha256"] = hashlib.sha256(public_path.read_bytes()).hexdigest()
        entry["qa_private_schedule_sha256"] = hashlib.sha256(private_path.read_bytes()).hexdigest()
        entry["qa_question_schedule"] = [
            {key: question[key] for key in (
                "query_id", "perception_difficulty", "reasoning_difficulty", "reasoning_family",
                "region_path", "requested_reasoning_difficulty", "requested_region_path", "selection_fallback",
            )}
            for question in public_questions
        ]
    return {"schema_version": "RQ1_1QABalanceAuditV1", "levels": level_audits}


def _prepare_roster_row(row: Mapping[str, str], config: Mapping[str, Any]) -> PreparedCase:
    """Compile one renderer-heavy case in an isolated process."""

    return prepare_case(
        row["dataset"], row["case_id"], config, row["opaque_incident_id"],
        int(row["qa_selection_slot"]),
    )


def _write_prepared_index(
    paths: RunPaths,
    experiment_id: str,
    entries: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
    *,
    complete: bool, qa_balance_audit: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    index = {
        "schema_version": "RQ1_1PreparedIndexV1",
        "experiment_id": experiment_id,
        "case_count": len(entries),
        "cases": sorted((dict(row) for row in entries), key=lambda row: row["opaque_incident_id"]),
        "run_contract": dict(contract),
        "preparation_complete": complete,
    }
    if qa_balance_audit is not None:
        index["qa_balance_audit"] = dict(qa_balance_audit)
    index["index_sha256"] = stable_hash(index)
    write_json(paths.prepared / ("index.json" if complete else "index.partial.json"), index)
    return index


def _physical_cpu_ids(limit: int) -> tuple[int, ...]:
    chosen: list[int] = []
    seen: set[tuple[str, str]] = set()
    for cpu in sorted(os.sched_getaffinity(0)):
        topology = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology")
        try:
            key = ((topology / "physical_package_id").read_text().strip(),
                   (topology / "core_id").read_text().strip())
        except OSError:
            key = ("logical", str(cpu))
        if key not in seen:
            seen.add(key); chosen.append(cpu)
        if len(chosen) == limit:
            break
    if len(chosen) < limit:
        raise RQ1Error(f"only {len(chosen)} independent CPU cores are available; need {limit}")
    return tuple(chosen)


def _pin_prepare_worker(cpu_ids: tuple[int, ...]) -> None:
    identity = mp.current_process()._identity
    slot = ((identity[-1] if identity else os.getpid()) - 1) % len(cpu_ids)
    os.sched_setaffinity(0, {cpu_ids[slot]})


def _resume_entries(
    paths: RunPaths, run_id: str, contract: Mapping[str, Any], expected: set[str],
) -> tuple[list[dict[str, Any]], bool]:
    final, partial = paths.prepared / "index.json", paths.prepared / "index.partial.json"
    source = final if final.is_file() else partial if partial.is_file() else None
    if source is None:
        return [], False
    index = json.loads(source.read_text())
    recorded = index.get("index_sha256"); unsigned = dict(index); unsigned.pop("index_sha256", None)
    if recorded != stable_hash(unsigned) or index.get("experiment_id") != run_id:
        raise RQ1Error(f"invalid resumable prepared index: {source}")
    if (index.get("run_contract") or {}).get("contract_sha256") != contract.get("contract_sha256"):
        raise RQ1Error("prepared resume contract differs; use a new result ID or explicit compatibility audit")
    entries = list(index.get("cases") or ()); ids = [str(row.get("opaque_incident_id")) for row in entries]
    if index.get("case_count") != len(entries) or len(ids) != len(set(ids)) or not set(ids) <= expected:
        raise RQ1Error("prepared resume index contains duplicate or out-of-roster cases")
    for item in entries:
        _read_prepared(paths, item)
    complete = bool(index.get("preparation_complete"))
    if complete and set(ids) != expected:
        raise RQ1Error("complete prepared index does not cover its assigned roster")
    return entries, complete


def prepare(
    *, experiment_id: str, roster: Path, config_path: Path = DEFAULT_CONFIG,
    limit: int | None = None, output_shard_count: int = 1,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    rows = _load_roster(roster, config)
    if limit is not None:
        rows = rows[:limit]
    slots = {
        opaque: index for index, opaque in enumerate(sorted(str(row["opaque_incident_id"]) for row in rows))
    }
    rows = [{**row, "qa_selection_slot": slots[str(row["opaque_incident_id"])]} for row in rows]
    if output_shard_count < 1:
        raise RQ1Error("output shard count must be positive")
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
    resumed = [
        _resume_entries(path, run_id, contract, wanted)
        for path, run_id, wanted in zip(paths, ids, expected, strict=True)
    ]
    entries = [value[0] for value in resumed]
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
        initializer=_pin_prepare_worker, initargs=(cpu_ids,),
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
    qa_balance_audit = _finalize_balanced_qa_schedules(paths, entries, int(config["seed"]))
    summaries = []
    for run_id, run_paths, values in zip(ids, paths, entries, strict=True):
        index = _write_prepared_index(
            run_paths, run_id, values, contract, complete=True,
            qa_balance_audit=qa_balance_audit,
        )
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
    variants = {key: (paths.root / path).read_bytes() for key, path in item.get("counterfactual_images", {}).items()}
    actual = {
        "full": hashlib.sha256(full).hexdigest(),
        "screenshots": [hashlib.sha256(value).hexdigest() for value in screenshots],
        "regions": {
            key: [hashlib.sha256(value).hexdigest() for value in values]
            for key, values in regions.items()
        },
        "counterfactuals": {
            key: hashlib.sha256(value).hexdigest() for key, value in variants.items()
        },
    }
    expected = {
        "full": item["full_image_sha256"],
        "screenshots": item["screenshot_image_sha256"],
        "regions": item["region_image_sha256"],
        "counterfactuals": item.get("counterfactual_image_sha256", {}),
    }
    if actual != expected:
        raise RQ1Error("prepared image artifact hash mismatch")
    public, private = json.loads(public_path.read_text()), json.loads(private_path.read_text())
    if item.get("qa_public_schedule") and item.get("qa_private_schedule"):
        public_schedule_path = paths.root / item["qa_public_schedule"]
        private_schedule_path = paths.root / item["qa_private_schedule"]
        if hashlib.sha256(public_schedule_path.read_bytes()).hexdigest() != item.get("qa_public_schedule_sha256"):
            raise RQ1Error("prepared public QA schedule hash mismatch")
        if hashlib.sha256(private_schedule_path.read_bytes()).hexdigest() != item.get("qa_private_schedule_sha256"):
            raise RQ1Error("prepared private QA schedule hash mismatch")
        public_schedule = json.loads(public_schedule_path.read_text())
        private_schedule = json.loads(private_schedule_path.read_text())
        if public_schedule.get("opaque_incident_id") != public.get("opaque_incident_id"):
            raise RQ1Error("public QA schedule belongs to another case")
        if private_schedule.get("opaque_incident_id") != private.get("opaque_incident_id"):
            raise RQ1Error("private QA schedule belongs to another case")
        public["selected_questions"] = public_schedule["selected_questions"]
        private["selected_questions"] = private_schedule["selected_questions"]
        absent = [level for level in range(1, 5) if not any(
            int(row["perception_difficulty"]) == level for row in public["selected_questions"]
        )]
        public["qa_ineligible_levels"] = absent; private["qa_ineligible_levels"] = absent
    return PreparedCase(public, private, full, screenshots, regions, variants)


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


def _call(
    *, model: str, system: str, parts: list[dict[str, Any]], schema: Mapping[str, Any],
    config: Mapping[str, Any], partial_root: Path | None, metadata: Mapping[str, Any],
    attention_root: Path,
) -> tuple[dict[str, Any], str]:
    adapter = config["inference_adapter"]
    model_cfg = get_config(model, max_tokens=int(adapter["max_tokens"]))
    vllm_config = VLLMInferenceConfig.load(_vllm_config_path(config))
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
        partial_metadata=dict(metadata), record_performance=True,
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
            raise RQ1Error(
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
    return [f"# RQ1.1 {experiment}\n", f"- model: `{model}`\n- case: `{opaque}`\n- arm: `{arm}`\n"]


def _prepared_fingerprints(prepared: PreparedCase) -> tuple[str, str]:
    """Bind resume decisions to the actual evidence bytes and private labels."""

    images = {
        "full": hashlib.sha256(prepared.full_png).hexdigest(),
        "screenshots": [hashlib.sha256(value).hexdigest() for value in prepared.screenshot_pngs],
        "regions": {
            region: [hashlib.sha256(value).hexdigest() for value in values]
            for region, values in sorted(prepared.region_pngs.items())
        },
        "counterfactuals": {
            arm: hashlib.sha256(value).hexdigest()
            for arm, value in sorted(prepared.counterfactual_pngs.items())
        },
    }
    return stable_hash({"public": prepared.public, "images": images}), stable_hash(prepared.private)


def _valid_terminal_record(path: Path, expected: Mapping[str, Any]) -> bool:
    if not path.is_file() or not path.with_suffix(".md").is_file():
        return False
    try:
        record = json.loads(path.read_text()); recorded = record.pop("record_sha256")
        return (
            stable_hash(record) == recorded
            and record.get("status") in {"completed", "protocol_ineligible"}
            and all(record.get(key) == value for key, value in expected.items())
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _serialized_parts(parts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return the exact model-visible part projection persisted by `_call`."""

    return [
        {"type": "text", "text": part["text"]} if part["type"] == "text" else
        {
            "type": "image",
            "sha256": hashlib.sha256(part["png"]).hexdigest(),
            "bytes": len(part["png"]),
        }
        for part in parts
    ]


def _compatible_qa_terminal(
    path: Path, *, config: Mapping[str, Any], model: str, opaque: str, arm: str,
    question: Mapping[str, Any] | None, private_question: Mapping[str, Any] | None,
    parts: Sequence[Mapping[str, Any]] | None, mapped_rca_arm: str | None,
    visual_regions: Sequence[str],
) -> bool:
    """Accept only an explicitly registered, byte-identical Direct-QA request.

    The question-order repair changes the run-contract hash and, for a subset
    of cases, the QA schedule sidecar.  Unaffected predecessor responses remain
    valid only when this function can reproduce their complete model-visible
    request and their score under the current private answer.  No RCA terminal
    or merely similar prompt can pass this compatibility boundary.
    """

    allowed = set(map(
        str,
        (config.get("resume_compatibility") or {}).get(
            "direct_qa_predecessor_contract_sha256", ()
        ),
    ))
    if not allowed or not path.is_file() or not path.with_suffix(".md").is_file():
        return False
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        recorded_hash = record.pop("record_sha256")
        if stable_hash(record) != recorded_hash:
            return False
        if (
            record.get("run_contract_sha256") not in allowed
            or record.get("experiment") != "direct_qa"
            or record.get("model") != model
            or record.get("opaque_incident_id") != opaque
            or record.get("arm") != arm
        ):
            return False
        if question is None:
            return (
                record.get("status") == "protocol_ineligible"
                and int(record.get("model_calls", -1)) == 0
            )
        if private_question is None or parts is None:
            return False
        stages = record.get("stages") or ()
        if record.get("status") != "completed" or len(stages) != 1:
            return False
        stage = stages[0]
        if (
            record.get("question") != question
            or record.get("qa_condition") != arm.split("_", 1)[1]
            or record.get("mapped_rca_arm") != mapped_rca_arm
            or list(record.get("visual_regions") or ()) != list(visual_regions)
            or stage.get("system") != QA_GUIDE_SYSTEM
            or stage.get("parts") != _serialized_parts(parts)
        ):
            return False
        current_score = score_qa(stage.get("normalized") or {}, private_question)
        return record.get("score") == current_score
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, RQ1Error):
        return False


def _compatible_rca_terminal(
    path: Path, *, config: Mapping[str, Any], model: str, opaque: str, arm: str,
    prepared: PreparedCase,
) -> bool:
    """Reuse a predecessor Direct-RCA call only after exact reconstruction."""

    allowed = set(map(
        str,
        (config.get("resume_compatibility") or {}).get(
            "direct_rca_predecessor_contract_sha256", ()
        ),
    ))
    if not allowed or not path.is_file() or not path.with_suffix(".md").is_file():
        return False
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        recorded_hash = record.pop("record_sha256")
        if stable_hash(record) != recorded_hash:
            return False
        if (
            record.get("run_contract_sha256") not in allowed
            or record.get("experiment") != "direct_rca"
            or record.get("model") != model
            or record.get("opaque_incident_id") != opaque
            or record.get("arm") != arm
            or record.get("status") != "completed"
        ):
            return False
        stages = record.get("stages") or ()
        if len(stages) != 1:
            return False
        stage = stages[0]
        if (
            stage.get("system") != RCA_SYSTEM_ROLE
            or stage.get("parts") != _serialized_parts(direct_rca_parts(arm, prepared))
        ):
            return False
        current_score = _score_rca(stage.get("normalized") or {}, prepared.private, config)
        return record.get("score") == current_score
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, RQ1Error):
        return False


def _append_call(conversation: list[str], title: str, call: Mapping[str, Any]) -> None:
    conversation.extend([
        f"\n## {title}\n", "### System\n", str(call["system"]), "\n### User parts\n",
        canonical_json(call["parts"]), "\n### Raw response\n", str(call["response_text"]), "\n",
    ])


def _smoke_arms(spec: Any, dataset: str, model: str, config: Mapping[str, Any]) -> tuple[str, ...]:
    plan = config["smoke_plans"][spec.name]
    if model in plan:
        return tuple(map(str, (plan.get(model) or {}).get(dataset) or ()))
    return tuple(map(str, plan.get(dataset) or ()))


def _fatal_inference_transport(error: BaseException) -> bool:
    """Classify errors that mean the shared model server cannot serve more cells."""

    text = f"{type(error).__name__}: {error}".casefold()
    return any(marker in text for marker in (
        "enginedead", "engine dead", "enginecore encountered",
        "connection refused", "failed to connect", "couldn't connect",
        "all connection attempts failed", "server disconnected",
        "connection reset", "500 internal server error",
    ))


def _run_case(
    *, prepared: PreparedCase, paths: RunPaths, spec: Any, experiment: str, model: str,
    config: Mapping[str, Any], contract_hash: str, smoke: bool, writer: AsyncWriter,
    abort_event: threading.Event, abort_reasons: list[str], abort_lock: threading.Lock,
    arms_override: Sequence[str] | None = None,
    question_override: tuple[Mapping[str, Any], Mapping[str, Any]] | None = None,
    target_suffix: str = "",
) -> dict[str, int]:
    opaque = str(prepared.public["opaque_incident_id"])
    dataset = str(prepared.private["dataset"])
    arms = (
        tuple(arms_override)
        if arms_override is not None
        else _smoke_arms(spec, dataset, model, config) if smoke else spec.arms
    )
    if arms_override is None:
        arms = balanced_arm_order(arms, opaque, experiment)
    root = paths.trajectories / experiment / model
    attention_root = paths.root / "attention" / model / experiment
    counts = {"completed": 0, "errors": 0, "calls": 0, "skipped": 0}
    evidence_hash, private_hash = _prepared_fingerprints(prepared)
    for arm in arms:
        if abort_event.is_set():
            break
        initiated_calls = 0
        target = root / f"{opaque}{target_suffix}__{arm}.json"
        qa_level: int | None = None
        qa_question: Mapping[str, Any] | None = None
        qa_private_question: Mapping[str, Any] | None = None
        qa_parts: list[dict[str, Any]] | None = None
        qa_mapped_rca_arm: str | None = None
        qa_visual_regions: tuple[str, ...] = ()
        if spec.task == "direct_qa":
            qa_level = int(arm.split("_", 1)[0].removeprefix("L"))
            if question_override is None:
                public_by_level = {
                    int(row["perception_difficulty"]): row
                    for row in prepared.public["selected_questions"]
                }
                private_by_level = {
                    int(row["perception_difficulty"]): row
                    for row in prepared.private["selected_questions"]
                }
                if qa_level in public_by_level and qa_level in private_by_level:
                    qa_question = public_by_level[qa_level]
                    qa_private_question = private_by_level[qa_level]
            else:
                qa_question, qa_private_question = question_override
            if qa_question is not None:
                if int(qa_question["perception_difficulty"]) != qa_level:
                    raise RQ1Error("question perception difficulty differs from requested arm")
                evidence_parts, qa_mapped_rca_arm, qa_visual_regions = qa_arm_parts(
                    arm, qa_question, prepared
                )
                qa_parts = [
                    *representation_guide_part(
                        "S" if arm.endswith("_S") else arm,
                        qa_visual_regions,
                    ),
                    *evidence_parts,
                    tagged_text_part(qa_prompt(qa_question), "task_question"),
                ]
        call_key = stable_hash({
            "contract": contract_hash, "experiment": experiment, "model": model,
            "case": opaque, "arm": arm, "smoke": smoke, "question_instance": target_suffix,
            "prepared_evidence": evidence_hash, "evaluator_private": private_hash,
        })
        if _valid_terminal_record(target, {
            "call_key": call_key, "run_contract_sha256": contract_hash,
            "prepared_evidence_sha256": evidence_hash,
            "evaluator_private_sha256": private_hash,
        }):
            counts["skipped"] += 1
            continue
        if (
            not smoke and spec.task == "direct_qa"
            and _compatible_qa_terminal(
                target, config=config, model=model, opaque=opaque, arm=arm,
                question=qa_question, private_question=qa_private_question,
                parts=qa_parts, mapped_rca_arm=qa_mapped_rca_arm,
                visual_regions=qa_visual_regions,
            )
        ):
            counts["skipped"] += 1
            continue
        if (
            not smoke and spec.task == "direct_rca"
            and _compatible_rca_terminal(
                target, config=config, model=model, opaque=opaque, arm=arm,
                prepared=prepared,
            )
        ):
            counts["skipped"] += 1
            continue
        record: dict[str, Any] = {
            "schema_version": "RQ1_1TrajectoryV1", "experiment": experiment,
            "model": model, "opaque_incident_id": opaque, "arm": arm,
            "analysis_dataset": dataset, "analysis_fault_type": prepared.private.get("fault_type", "unknown"),
            "fact_count": len(prepared.public["packet"]["facts"]),
            "candidate_count": len(prepared.public["packet"]["candidates"]),
            "run_contract_sha256": contract_hash, "call_key": call_key,
            "prepared_evidence_sha256": evidence_hash,
            "evaluator_private_sha256": private_hash,
            "status": "completed", "stages": [], "model_output_errors": [],
        }
        conversation = _conversation_header(experiment, model, opaque, arm)
        partial = paths.root / "partial_responses" / experiment / model if smoke else None
        try:
            if spec.task in {"direct_rca", "counterfactual_rca"}:
                pairs = prepared.private.get("counterfactual_pairs") or {}
                if spec.task == "counterfactual_rca" and not pairs.get("eligible"):
                    record.update(status="protocol_ineligible", protocol_ineligible_reason=pairs.get("reason"), model_calls=0)
                    record["record_sha256"] = stable_hash(record); writer.json(target, record)
                    writer.bytes(target.with_suffix(".md"), "".join(conversation).encode()); continue
                parts = (counterfactual_rca_parts(arm, prepared) if spec.task == "counterfactual_rca"
                         else direct_rca_parts(arm, prepared))
                if spec.task == "counterfactual_rca":
                    condition = arm.removeprefix("V_").lower()
                    record["counterfactual_condition"] = condition
                    record["counterfactual_pair"] = list(pairs.get(condition) or ())
                counts["calls"] += 1
                initiated_calls += 1
                call, raw = _call(
                    model=model, system=RCA_SYSTEM_ROLE, parts=parts,
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
                record["reasoning_trace"] = build_reasoning_trace(
                    final, prepared.public["packet"], prepared.private,
                )
            elif spec.task == "direct_qa":
                level = int(qa_level)
                if qa_question is None or qa_private_question is None or qa_parts is None:
                    record.update(
                        status="protocol_ineligible",
                        protocol_ineligible_reason=(
                            f"no fully model-visible P{level} question can be derived "
                            "from this case's telemetry regions"
                        ),
                        perception_difficulty=level,
                        model_calls=0,
                    )
                    record["record_sha256"] = stable_hash(record)
                    writer.json(target, record)
                    writer.bytes(target.with_suffix(".md"), "".join(conversation).encode())
                    continue
                question, private_question = qa_question, qa_private_question
                parts = qa_parts
                mapped_rca_arm = str(qa_mapped_rca_arm)
                visual_regions = qa_visual_regions
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
                record["qa_condition"] = arm.split("_", 1)[1]
                record["mapped_rca_arm"] = mapped_rca_arm
                record["visual_regions"] = list(visual_regions)
                record["stages"].append({
                    **call, "stage": 1, "parse": output_error is None,
                    "normalized": final, "output_error": output_error,
                })
                record["score"] = score_qa(final, private_question)
                record["qa_value_support"] = qa_value_support(
                    final, prepared.public["packet"],
                )
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
            if _fatal_inference_transport(error):
                with abort_lock:
                    if not abort_reasons:
                        abort_reasons.append(record["error"])
                abort_event.set()
        record["model_output_valid"] = not record.get("model_output_errors")
        record["model_calls"] = initiated_calls
        record["record_sha256"] = stable_hash(record)
        writer.json(target, record)
        writer.bytes(target.with_suffix(".md"), "".join(conversation).encode())
        if abort_event.is_set():
            break
    return counts


QA_GUIDE_SYSTEM = "You are a precise telemetry-evidence reader. Follow the requested region path and output only schema-valid JSON."
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
    if spec.status != "active":
        raise RQ1Error(f"experiment {experiment} is {spec.status} and is not executable")
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
    # Transformers' lazy AutoTokenizer export is not thread-safe during the
    # first concurrent import. Load the exact registered mapping tokenizer in
    # the supervisor before request workers start; later calls reuse the same
    # cached object and produce identical tokenization.
    warm_mapping_tokenizer(
        VLLMInferenceConfig.load(_vllm_config_path(config)).model_path(model)
    )
    # Model-request drivers are deliberately separate from the eight CPU
    # preparation/artifact workers.  A deeper request queue lets GPU inference
    # overlap token preflight, attention aggregation and persistence without
    # changing any model-visible input or registered arm order in formal runs.
    request_concurrency = int(config["runtime"]["request_concurrency"])
    writer = AsyncWriter(int(config["runtime"]["max_workers"]))
    effective = VLLMInferenceConfig.load(_vllm_config_path(config)).model(model)
    metrics_cfg = config.get("performance_metrics") or {}
    monitor = RuntimePerformanceMonitor(
        str(effective["base_url"]), float(metrics_cfg.get("sample_interval_s", 1.0)),
        bool(metrics_cfg.get("enabled", True)),
    ).start()
    abort_event = threading.Event()
    abort_reasons: list[str] = []
    abort_lock = threading.Lock()

    work_items: list[tuple[Mapping[str, Any] | PreparedCase, tuple[str, ...] | None]] = []
    if smoke:
        # The logical smoke has nine registered cells per model.  Flatten those
        # cells so they exercise the same bounded request scheduler used by the
        # formal run instead of serialising three arms behind each case.
        for item in items:
            prepared = _read_prepared(prepared_paths, item)
            dataset = str(prepared.private["dataset"])
            for arm in _smoke_arms(spec, dataset, model, config):
                work_items.append((prepared, (arm,)))
    else:
        work_items = [(item, None) for item in items]

    def work(task: tuple[Mapping[str, Any] | PreparedCase, tuple[str, ...] | None]) -> dict[str, int]:
        if abort_event.is_set():
            return {"completed": 0, "errors": 0, "calls": 0, "skipped": 0}
        source, arms_override = task
        prepared = source if isinstance(source, PreparedCase) else _read_prepared(prepared_paths, source)
        return _run_case(
            prepared=prepared, paths=result_paths, spec=spec,
            experiment=experiment, model=model, config=config,
            contract_hash=contract["contract_sha256"], smoke=smoke, writer=writer,
            abort_event=abort_event, abort_reasons=abort_reasons, abort_lock=abort_lock,
            arms_override=arms_override,
        )

    rows: list[dict[str, int]] = []
    try:
        concurrency = max(1, min(len(work_items), request_concurrency))
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            rows = list(pool.map(work, work_items))
    finally:
        writer.drain()
        run_performance = monitor.stop(
            attempted_requests=sum(row["calls"] for row in rows),
            good_requests=sum(row["completed"] for row in rows),
        )
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
        "phase_aborted": abort_event.is_set(),
        "phase_abort_reason": abort_reasons[0] if abort_reasons else None,
        "run_performance": run_performance,
        "run_contract": contract,
    }
    write_json(result_paths.root / f"run_{experiment}_{model}_shard{shard_index:03d}-of-{shard_count:03d}.json", result)
    if abort_reasons:
        raise RQ1Error(f"fatal inference transport; phase stopped: {abort_reasons[0]}")
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
    result = analyze_perception_rca(load("direct_rca"), load("direct_qa"), config)
    write_json(paths.root / "summary_perception_rca_joint.json", result)
    view_root = paths.root / "reasoning_views"
    view_root.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(result.get("reasoning_trace_representatives") or (), 1):
        trace = row.get("reasoning_trace") or {}
        if trace:
            name = f"{index:02d}-{row['model']}-{row['opaque_incident_id']}-{row['representation']}.svg"
            atomic_write(view_root / name, reasoning_trace_svg(trace).encode("utf-8"))
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
    p.add_argument("experiment_id"); p.add_argument("experiment", choices=("direct_qa", "direct_rca", "one_stage_counterfactual_rca", "multi_stage_rca")); p.add_argument("model")
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

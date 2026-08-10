"""Compact command-line engine for every RQ1 experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from unified_scripts import stable_hash
from vlmrca.vlm.client import VLMResponse, call_vlm, count_vllm_prompt_tokens, text_part
from vlmrca.vlm.configs import get_config
from unified_scripts.vllm_inference import VLLMInferenceConfig

from .exps import (
    DIAGNOSE_SYSTEM,
    OBSERVE_SYSTEM,
    PreparedCase,
    experiment_registry,
    handoff_parts,
    is_rca_task,
    prepare_case,
    representation_parts,
    response_schema,
    normalize_stage1_ledger,
    score_reasoning,
    stage1_prompt,
    stage2_prompt,
)
from .gates import analyze_records, verify_result_root
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

SOURCE_FILES = tuple(sorted((ROOT / "RQs/RQ1/src").glob("*.py")))


def _load_roster(path: Path) -> list[dict[str, str]]:
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
    for row in rows:
        if not isinstance(row, Mapping) or not row.get("dataset") or not row.get("case_id"):
            raise RQ1Error("private roster rows require dataset and case_id")
        normalized.append({"dataset": str(row["dataset"]), "case_id": str(row["case_id"])})
    return normalized


def prepare(
    *,
    experiment_id: str,
    roster: Path,
    config_path: Path = DEFAULT_CONFIG,
    limit: int | None = None,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    rows = _load_roster(roster)
    if limit is not None:
        rows = rows[:limit]
    writer = AsyncWriter(int(config["runtime"]["max_workers"]))
    index: list[dict[str, Any]] = []
    try:
        for row in rows:
            prepared = prepare_case(row["dataset"], row["case_id"], config)
            opaque = str(prepared.public["opaque_incident_id"])
            public_path = paths.prepared / f"{opaque}.json"
            private_path = paths.private / f"{opaque}.json"
            full_path = paths.renders / f"{opaque}.full.png"
            routed_path = paths.renders / f"{opaque}.routed.png"
            variant_paths = {
                name: paths.renders / f"{opaque}.{name}.png"
                for name in prepared.variant_pngs
            }
            writer.json(public_path, prepared.public)
            writer.json(private_path, prepared.private)
            writer.bytes(full_path, prepared.full_png)
            writer.bytes(routed_path, prepared.routed_png)
            for name, path in variant_paths.items():
                writer.bytes(path, prepared.variant_pngs[name])
            index.append(
                {
                    "opaque_incident_id": opaque,
                    "public": str(public_path.relative_to(paths.root)),
                    "private": str(private_path.relative_to(paths.root)),
                    "full_image": str(full_path.relative_to(paths.root)),
                    "routed_image": str(routed_path.relative_to(paths.root)),
                    "variant_images": {name: str(path.relative_to(paths.root)) for name, path in variant_paths.items()},
                    "public_sha256": stable_hash(prepared.public),
                    "private_sha256": stable_hash(prepared.private),
                    "full_image_sha256": stable_hash(prepared.full_png),
                    "routed_image_sha256": stable_hash(prepared.routed_png),
                    "variant_image_sha256": {
                        name: stable_hash(value) for name, value in prepared.variant_pngs.items()
                    },
                }
            )
    finally:
        writer.drain()
    freeze = artifact_contract(config=config, code_files=SOURCE_FILES)
    summary = {
        "schema_version": "RQ1PreparedIndexV2",
        "experiment_id": experiment_id,
        "case_count": len(index),
        "cases": index,
        "runtime_freeze": freeze,
    }
    summary["index_sha256"] = stable_hash(summary)
    write_json(paths.prepared / "index.json", summary)
    return summary


def _read_prepared(paths: RunPaths, item: Mapping[str, Any]) -> PreparedCase:
    public = json.loads((paths.root / item["public"]).read_text())
    private = json.loads((paths.root / item["private"]).read_text())
    full = (paths.root / item["full_image"]).read_bytes()
    routed = (paths.root / item["routed_image"]).read_bytes()
    variants = {name: (paths.root / rel).read_bytes() for name, rel in item.get("variant_images", {}).items()}
    if stable_hash(public) != item.get("public_sha256"):
        raise RQ1Error("prepared public artifact hash mismatch")
    if stable_hash(private) != item.get("private_sha256"):
        raise RQ1Error("prepared private artifact hash mismatch")
    if stable_hash(full) != item.get("full_image_sha256"):
        raise RQ1Error("prepared full-image index hash mismatch")
    if stable_hash(routed) != item.get("routed_image_sha256"):
        raise RQ1Error("prepared routed-image index hash mismatch")
    if any(
        stable_hash(value) != item.get("variant_image_sha256", {}).get(name)
        for name, value in variants.items()
    ):
        raise RQ1Error("prepared counterfactual index hash mismatch")
    if stable_hash(full) != public["full_image_sha256"] or stable_hash(routed) != public["routed_image_sha256"]:
        raise RQ1Error("prepared image hash mismatch")
    expected_variants = public.get("variant_image_sha256", {})
    if any(stable_hash(value) != expected_variants.get(name) for name, value in variants.items()):
        raise RQ1Error("prepared counterfactual image hash mismatch")
    return PreparedCase(public=public, private=private, full_png=full, routed_png=routed, variant_pngs=variants)


def _completed_target(path: Path) -> bool:
    """Only completed model outcomes are terminal; infrastructure records retry."""
    if not path.is_file():
        return False
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("status") == "completed"
    except (OSError, json.JSONDecodeError):
        return False


def _finish_reason(response: VLMResponse) -> Any:
    return (response.raw or {}).get("finish_reason") or (response.raw or {}).get("stopReason")


def _parts_hash(parts: Sequence[Mapping[str, Any]]) -> str:
    rows = []
    for part in parts:
        payload = part["png"] if part["type"] == "image" else str(part["text"]).encode()
        rows.append({"type": part["type"], "sha256": stable_hash(payload)})
    return stable_hash(rows)


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
    response = call_vlm(parts, model=model_config, system=system, max_retries=1, response_format=dict(schema))
    record = {
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
        "finish_reason": _finish_reason(response),
    }
    return record, response.text


def _stage1_failure(text: str, error: Exception) -> dict[str, Any]:
    return {
        "schema_version": "Stage1FailureV2",
        "failure": "parse_error",
        "detail": str(error),
        "raw_response_sha256": stable_hash(text.encode()),
    }


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


def run(
    *,
    experiment_id: str,
    experiment: str,
    model: str,
    config_path: Path = DEFAULT_CONFIG,
    execute: bool = False,
    shard_index: int = 0,
    shard_count: int = 1,
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
    call_options = {
        "inference_adapter": inference_adapter,
        "context_limit": context_limit,
    }
    paths = RunPaths.build(experiment_id, config)
    index = json.loads((paths.prepared / "index.json").read_text())
    if index.get("experiment_id") != experiment_id:
        raise RQ1Error("prepared index experiment ID mismatch")
    recorded_index_sha256 = index.get("index_sha256")
    unsigned_index = dict(index)
    unsigned_index.pop("index_sha256", None)
    if not recorded_index_sha256 or stable_hash(unsigned_index) != recorded_index_sha256:
        raise RQ1Error("prepared index integrity hash mismatch")
    current_freeze = artifact_contract(config=config, code_files=SOURCE_FILES)
    recorded_freeze = index.get("runtime_freeze", {})
    if current_freeze["freeze_sha256"] != recorded_freeze.get("freeze_sha256"):
        raise RQ1Error(
            "prepared runtime freeze differs from current code/config/models; "
            "repeat the CPU preparation before inference"
        )
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise RQ1Error("invalid shard index/count")
    items = [
        item for item in index["cases"]
        if int(hashlib.sha256(str(item["opaque_incident_id"]).encode()).hexdigest(), 16) % shard_count == shard_index
    ]
    writer = AsyncWriter(int(config["runtime"]["max_workers"]))
    completed = 0
    failures = 0
    try:
        for item in items:
            prepared = _read_prepared(paths, item)
            opaque = str(prepared.public["opaque_incident_id"])
            trajectory_root = paths.trajectories / experiment / model
            if spec.task == "root_cause_handoff":
                handoff_targets = {
                    arm: trajectory_root / f"{opaque}__{arm}.json" for arm in spec.arms
                }
                if all(_completed_target(path) for path in handoff_targets.values()):
                    continue
                observer_parts = representation_parts(
                    "R", prepared.public["ceb"], prepared.full_png, prepared.routed_png,
                    config, prepared.variant_pngs,
                )
                observer_parts.append(text_part(stage1_prompt(spec, prepared.public)))
                call1, raw1 = _model_call(
                    model=model, system=OBSERVE_SYSTEM, parts=observer_parts,
                    schema=response_schema(spec, 1),
                    **call_options,
                )
                try:
                    ledger = normalize_stage1_ledger(parse_json_object(raw1), prepared.public["ceb"])
                    stage1_parse = True
                except Exception as error:
                    ledger, stage1_parse = _stage1_failure(raw1, error), False
                shared_key = stable_hash({"experiment": experiment, "model": model, "case": opaque, "observer": _parts_hash(observer_parts)})[:24]
                for arm in spec.arms:
                    target = handoff_targets[arm]
                    stage2_parts = handoff_parts(arm, ledger, prepared.public["ceb"]["candidates"])
                    record = {
                        "experiment_id": experiment_id, "experiment": experiment, "model": model,
                        "opaque_incident_id": opaque, "arm": arm, "shared_stage1_call_key": shared_key,
                        "analysis_dataset": prepared.private["dataset"],
                        "status": "completed", "stages": [{**call1, "stage": 1, "parse": stage1_parse, "normalized": ledger}],
                    }
                    conversation = [
                        "# RQ1 ledger-handoff RCA\n",
                        f"- case: `{opaque}`\n- arm: `{arm}`\n- model: `{model}`\n",
                        _prompt_markdown(1, call1["prompt"]),
                        "\n## Shared Stage 1 response\n",
                        raw1,
                        "\n",
                    ]
                    try:
                        call2, raw2 = _model_call(model=model, system=DIAGNOSE_SYSTEM, parts=stage2_parts, schema=response_schema(spec, 2), **call_options)
                        try:
                            final, stage2_parse = parse_json_object(raw2), True
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
                    record["record_sha256"] = stable_hash(record)
                    writer.json(target, record)
                    writer.bytes(target.with_suffix(".md"), "".join(conversation).encode())
                continue
            for arm in spec.arms:
                target = trajectory_root / f"{opaque}__{arm}.json"
                if _completed_target(target):
                    continue
                parts = representation_parts(
                    arm,
                    prepared.public["ceb"],
                    prepared.full_png,
                    prepared.routed_png,
                    config,
                    prepared.variant_pngs,
                )
                parts.append(text_part(stage1_prompt(spec, prepared.public)))
                contract = {
                    "experiment_id": experiment_id,
                    "experiment": experiment,
                    "model": model,
                    "opaque_incident_id": opaque,
                    "arm": arm,
                    "representation_hash": _parts_hash(parts),
                    "runtime_freeze_sha256": index["runtime_freeze"]["freeze_sha256"],
                }
                contract["call_key"] = stable_hash(contract)[:24]
                record: dict[str, Any] = {**contract, "status": "completed", "stages": []}
                record["analysis_dataset"] = prepared.private["dataset"]
                if spec.task == "root_cause_counterfactual":
                    record["counterfactual_pair"] = prepared.private["counterfactual_pairs"].get(
                        arm.removeprefix("H_"), []
                    )
                conversation = ["# RQ1 trajectory\n", f"- case: `{opaque}`\n- arm: `{arm}`\n- model: `{model}`\n"]
                try:
                    call1, raw1 = _model_call(model=model, system=OBSERVE_SYSTEM, parts=parts, schema=response_schema(spec, 1), **call_options)
                    try:
                        stage1 = parse_json_object(raw1)
                        if is_rca_task(spec):
                            stage1 = normalize_stage1_ledger(stage1, prepared.public["ceb"])
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
                        stage2_parts = [text_part(stage2_prompt(spec, stage1, prepared.public["ceb"]["candidates"]))]
                        system = DIAGNOSE_SYSTEM if is_rca_task(spec) else OBSERVE_SYSTEM
                        call2, raw2 = _model_call(model=model, system=system, parts=stage2_parts, schema=response_schema(spec, 2), **call_options)
                        try:
                            final = parse_json_object(raw2)
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
                        questions = prepared.private["questions"][:9 if spec.task == "direct_visops" else 3]
                        record["score"] = score_reasoning(final, questions)
                    completed += 1
                except Exception as error:
                    record.update(status="infrastructure_error", error=f"{type(error).__name__}: {error}")
                    failures += 1
                    conversation.extend(("\n## Infrastructure error\n", record["error"], "\n"))
                record["record_sha256"] = stable_hash(record)
                writer.json(target, record)
                writer.bytes(target.with_suffix(".md"), "".join(conversation).encode())
    finally:
        writer.drain()
    current_records = []
    for item in items:
        opaque = str(item["opaque_incident_id"])
        for arm in spec.arms:
            target = paths.trajectories / experiment / model / f"{opaque}__{arm}.json"
            if target.is_file():
                try:
                    current_records.append(json.loads(target.read_text(encoding="utf-8")))
                except json.JSONDecodeError:
                    pass
    result = {
        "completed": sum(row.get("status") == "completed" for row in current_records),
        "infrastructure_errors": sum(row.get("status") == "infrastructure_error" for row in current_records),
        "expected_records": len(items) * len(spec.arms),
        "newly_completed": completed,
        "new_infrastructure_errors": failures,
        "experiment": experiment,
        "model": model,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "assigned_cases": len(items),
    }
    write_json(paths.root / f"run_{experiment}_{model}_shard{shard_index:03d}-of-{shard_count:03d}.json", result)
    if shard_count == 1:
        write_json(paths.root / f"run_{experiment}_{model}.json", result)
    return result


def analyse(*, experiment_id: str, experiment: str, config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_yaml(config_path)
    paths = RunPaths.build(experiment_id, config)
    records = [json.loads(path.read_text()) for path in (paths.trajectories / experiment).glob("*/*.json")]
    spec = experiment_registry(config)[experiment]
    result = analyze_records(records, spec, config)
    index = json.loads((paths.prepared / "index.json").read_text(encoding="utf-8"))
    expected = {
        (model, str(item["opaque_incident_id"]), arm)
        for model in config["runtime"]["models"]
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
    result["analysis_sha256"] = stable_hash(result)
    write_json(paths.summary, result)
    return result


def verify(*, experiment_id: str, config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_yaml(config_path)
    result = verify_result_root(RunPaths.build(experiment_id, config), config)
    write_json(RunPaths.build(experiment_id, config).root / "verification.json", result)
    return result


def cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("experiment_id")
    p_prepare.add_argument("roster", type=Path)
    p_prepare.add_argument("--limit", type=int)
    p_run = sub.add_parser("run")
    p_run.add_argument("experiment_id")
    p_run.add_argument("experiment", choices=("legacy_q9", "cross_region", "typed_two_stage", "matched_rca", "visual_counterfactual_rca", "ledger_handoff_rca"))
    p_run.add_argument("model")
    p_run.add_argument("--execute", action="store_true")
    p_run.add_argument("--shard-index", type=int, default=0)
    p_run.add_argument("--shard-count", type=int, default=1)
    p_analyse = sub.add_parser("analyse")
    p_analyse.add_argument("experiment_id")
    p_analyse.add_argument("experiment")
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("experiment_id")
    sub.add_parser("static")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(experiment_id=args.experiment_id, roster=args.roster, config_path=args.config, limit=args.limit)
    elif args.command == "run":
        result = run(experiment_id=args.experiment_id, experiment=args.experiment, model=args.model, config_path=args.config, execute=args.execute, shard_index=args.shard_index, shard_count=args.shard_count)
    elif args.command == "analyse":
        result = analyse(experiment_id=args.experiment_id, experiment=args.experiment, config_path=args.config)
    elif args.command == "verify":
        result = verify(experiment_id=args.experiment_id, config_path=args.config)
    else:
        from .tests import run_static_checks

        result = run_static_checks(args.config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())

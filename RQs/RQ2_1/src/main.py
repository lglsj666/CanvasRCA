"""RQ2.1 local preparation, resumable execution and analysis.

Inference is explicitly authorization/qualification-gated; never use old RQ2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from unified_scripts import stable_hash

from .gates import bridge_display_audit, execution_gate, verify_parent_copy
from .utils import (
    ROOT,
    RQ_ROOT,
    AsyncWriter,
    CallLedger,
    DesignInfeasible,
    ProtocolError,
    RQ21SegmentationAdapter,
    RunLock,
    artifact_row,
    artifacts_valid,
    atomic_write,
    checkpoint_identity,
    code_fingerprint,
    conversation_text,
    formal_scope,
    inherit_renderer,
    load_config,
    persist_attention,
    read_json,
    relative,
    request_identity,
    sha_file,
    write_json,
)


def register(config):
    inherit_renderer()
    public, private = RQ21SegmentationAdapter(config).materialize()
    target = RQ_ROOT / "configs/rosters/public.json"
    if target.exists() and read_json(target) != public:
        raise ValueError("registered roster would change; explicit successor required")
    write_json(target, public)
    write_json(RQ_ROOT / "results/registration/private_roster.json", private)
    return {
        "status": "registered",
        "total": len(public["cases"]),
        "selection": sum(r["role"] == "selection" for r in public["cases"]),
        "roster_sha256": public["roster_sha256"],
    }


def prepare_selection_case(config, opaque):
    """CPU-only selection materialization; no renderer/inference fallback."""
    from .exps import (
        POLICIES,
        build_evidence_universe,
        native_selection_rankings,
        packet_text,
        project_selected_packet,
        render_selected_parent,
        select_evidence,
    )

    started = time.monotonic()
    from .utils import preparation_fingerprint

    root = RQ_ROOT / "results/prepared_selection" / opaque
    signature = preparation_fingerprint(config)
    marker = root / "summary.json"
    if marker.exists():
        cached = read_json(marker)
        if (
            cached.get("preparation_fingerprint") == signature
            and artifacts_valid(cached)
            and source_inputs_valid(cached)
        ):
            return {"case": opaque, "status": "reused_preparation", "model_calls": 0}
        if config["execution_enabled"]:
            raise ProtocolError(
                "prepared content changed; choose an explicit preparation successor before formal work"
            )
    universe, telemetry, parent, context = build_evidence_universe(opaque, config, with_render_context=True)
    rankings, native_audit = native_selection_rankings(telemetry, universe)
    write_json(root / "private/universe.json", asdict(universe))
    write_json(root / "private/native_rankings.json", native_audit)
    baseline = {r: set(v) for r, v in universe.parent_order.items()}
    summary = {
        "case": opaque,
        "pool_counts": dict(Counter(r["region"] for r in universe.items)),
        "region_quotas": universe.capacities,
        "policies": {},
        "model_calls": 0,
    }
    summary["source_inputs"] = source_input_inventory(config, opaque)
    for policy in POLICIES:
        selection = select_evidence(universe, policy, native_ranks=rankings.get(policy), seed=config["seed"])
        packet = project_selected_packet(universe, selection, parent)
        text = packet_text(packet)
        write_json(root / "packets" / f"{policy}.json", packet)
        atomic_write(root / "texts" / f"{policy}.txt", text.encode())
        write_json(root / "private/selections" / f"{policy}.json", asdict(selection))
        manifest = {}
        try:
            png, manifest = render_selected_parent(config, universe, selection, packet, context)
            suffix = ".carrier" if manifest.get("unrendered_regions") else ""
            atomic_write(root / "renders" / f"{policy}{suffix}.png", png)
            write_json(root / "renders" / f"{policy}{suffix}.json", manifest)
            if suffix:
                raise DesignInfeasible("selected complete log rows exceed the registered S0 L footprint")
            stale = root / "renders" / f"{policy}.infeasible.json"
            if stale.is_file():
                stale.unlink()  # Only this CPU materializer's superseded failure marker.
        except DesignInfeasible as error:
            write_json(
                root / "renders" / f"{policy}.infeasible.json",
                {
                    "reason": str(error),
                    "signature": signature,
                    "carrier_available": bool(manifest.get("unrendered_regions")),
                },
            )
        summary["policies"][policy] = {
            "fact_inventory_hash": packet["fact_inventory_hash"],
            "text_hash": stable_hash(text),
            "selected_set_changed": {r: set(v) != baseline[r] for r, v in selection.selected.items()},
            "fill_counts": {r: len(v) for r, v in selection.filled.items()},
            "native_unrenderable_count": len(
                native_audit.get(policy, {}).get("unrenderable_source_items", [])
            ),
        }
    summary["elapsed_seconds"] = time.monotonic() - started
    summary["status"] = "selection_materialized"
    summary["preparation_fingerprint"] = signature
    summary["artifacts"] = [
        artifact_row(p)
        for subdir in ("packets", "texts", "private", "renders")
        for p in sorted((root / subdir).rglob("*"))
        if p.is_file()
    ]
    write_json(root / "summary.json", summary)
    return summary


def source_input_inventory(config, opaque):
    private = read_json(RQ_ROOT / "results/registration/private_roster.json")
    row = next(r for r in private["cases"] if r["opaque_incident_id"] == opaque)
    from vlmrca.processed import processed_index

    location = processed_index(row["dataset"])[row["case_id"]]["path"]
    source = ROOT / config["data"]["processed_root"] / "public" / row["dataset"] / location
    paths = [p for p in source.rglob("*") if p.is_file() and not p.is_symlink()]
    if not paths:
        raise ProtocolError("canonical source inventory empty")
    parent = ROOT / config["data"]["parent_prepared"]
    paths += [
        parent / "prepared" / f"{opaque}.json",
        parent / "renders" / f"{opaque}.dashboard.png",
    ]
    return [artifact_row(p) for p in sorted(paths)]


def source_inputs_valid(cached):
    return artifacts_valid({"artifacts": cached.get("source_inputs", [])})


def materialize_unit(config, opaque, unit, *, allow_render=True):
    from .exps import request_parts
    from .renderer.designs import compose_dashboard, encode_dashboard

    base = RQ_ROOT / "results/prepared_selection" / opaque
    policy = unit["policy"]
    packet = read_json(base / "packets" / f"{policy}.json")
    if packet.get("packet_hash") != stable_hash(
        {k: v for k, v in packet.items() if k != "packet_hash"}
    ) or packet["fact_inventory_hash"] != stable_hash(packet["facts"]):
        raise ProtocolError("prepared evidence packet content hash mismatch")
    if unit["representation"] == "T":
        return packet, request_parts(packet), []
    infeasible = base / "renders" / f"{policy}.infeasible.json"
    suffix = ""
    if infeasible.exists():
        failure = read_json(infeasible)
        if unit["silhouette"] == "S0" or not failure.get("carrier_available"):
            raise DesignInfeasible(failure["reason"])
        suffix = ".carrier"
    manifest = read_json(base / "renders" / f"{policy}{suffix}.json")
    png = (base / "renders" / f"{policy}{suffix}.png").read_bytes()
    if hashlib.sha256(png).hexdigest() != manifest["image_sha256"]:
        raise ProtocolError("prepared selection image is corrupt")
    key = stable_hash(
        {
            "packet": packet["packet_hash"],
            "source": manifest["image_sha256"],
            "manifest": stable_hash(manifest),
            "S": unit["silhouette"],
            "D": unit["composition"],
            "code": code_fingerprint(),
        }
    )
    root = RQ_ROOT / "results/prepared_designs" / opaque / key
    target, sidecar = root / "dashboard.png", root / "manifest.json"
    failure = root / "infeasible.json"
    if failure.exists():
        raise DesignInfeasible(read_json(failure)["reason"])
    if target.exists() and sidecar.exists():
        cached = read_json(sidecar)
        if sha_file(target) == cached["image_sha256"]:
            return (
                packet,
                request_parts(packet, png=target.read_bytes(), manifest=cached),
                [target, sidecar],
            )
        raise ProtocolError("cached design image is corrupt; diagnose before regenerating")
    if not allow_render:
        raise ProtocolError("CPU design preparation must complete before model scheduling")
    try:
        png, manifest = encode_dashboard(
            png,
            manifest,
            packet,
            unit["silhouette"],
            density=config["silhouette_density"],
        )
        png, manifest = compose_dashboard(png, manifest, packet, unit["composition"])
    except DesignInfeasible as error:
        write_json(failure, {"reason": str(error), "unit": unit, "signature": key})
        raise
    atomic_write(target, png)
    write_json(sidecar, manifest)
    return packet, request_parts(packet, png=png, manifest=manifest), [target, sidecar]


def prepare_design_case(config, opaque, units):
    rows = []
    for unit in units:
        try:
            packet, parts, paths = materialize_unit(config, opaque, unit)
            rows.append(
                {
                    "arm": unit["arm"],
                    "status": "prepared",
                    "fact_inventory_hash": packet["fact_inventory_hash"],
                    "images": len([p for p in parts if p["type"] == "image"]),
                    "artifacts": [artifact_row(p) for p in paths],
                }
            )
        except DesignInfeasible as error:
            rows.append(
                {
                    "arm": unit["arm"],
                    "status": "design_infeasible",
                    "reason": str(error),
                }
            )
    return {"case": opaque, "rows": rows, "model_calls": 0}


def prepare_batch(config, cases, *, units=None, workers=None):
    """Whole cases on independent physical cores; bounded materializer queue."""
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor

    from .utils import physical_cores, pin_worker

    count = min(
        workers or config["scheduler"]["cpu_workers"],
        8,
        len(cases),
        len(physical_cores()),
    )
    ctx = mp.get_context("spawn")
    cores = ctx.Queue()
    for core in physical_cores()[:count]:
        cores.put(core)
    output = []
    with ProcessPoolExecutor(
        max_workers=count, mp_context=ctx, initializer=pin_worker, initargs=(cores,)
    ) as pool:
        pending, iterator = {}, iter(cases)

        def submit(case):
            args = (config, case) if units is None else (config, case, units)
            function = prepare_selection_case if units is None else prepare_design_case
            pending[pool.submit(function, *args)] = case

        for _ in range(min(count, len(cases))):
            submit(next(iterator))
        while pending:
            done = next(as_completed(pending))
            case = pending.pop(done)
            output.append(done.result())
            write_json(
                RQ_ROOT / "results/cpu_progress.json",
                {
                    "completed": len(output),
                    "total": len(cases),
                    "last_case": case,
                    "model_calls": 0,
                },
            )
            following = next(iterator, None)
            if following is not None:
                submit(following)
    cores.close()
    return {"cases": output, "model_calls": 0}


def load_terminal(path):
    if not Path(path).is_file():
        return None
    record = read_json(path)
    checksum = record.pop("record_sha256", None)
    if checksum != __import__("unified_scripts").stable_hash(record) or not artifacts_valid(record):
        raise ProtocolError(f"terminal artifact is corrupt: {relative(path)}")
    if record["status"] not in {
        "completed",
        "model_failure",
        "design_infeasible",
        "reused",
    }:
        return None
    return record


def private_score(config, opaque, prediction):
    from .exps import score_numeric
    from .utils import rq21_scorer

    # This reader is evaluator-only and runs after model-visible preparation.
    private = read_json(ROOT / config["data"]["parent_prepared"] / "private" / f"{opaque}.json")
    scorer = rq21_scorer(config)
    return score_numeric(prediction, private["numeric_to_natural"], private["accepted_labels"], scorer)


def try_bridge_reuse(config, opaque, model, parts, unit):
    if unit["policy"] != "P0" or unit["representation"] != "T":
        return None
    from .exps import RCA_SYSTEM_ROLE

    path = ROOT / config["data"]["parent_results"] / "trajectories/direct_rca" / model / f"{opaque}__T.json"
    record = read_json(path)
    checksum = record.pop("record_sha256")
    if stable_hash(record) != checksum:
        raise ProtocolError("original bridge record hash mismatch")
    stage = record["stages"][0]
    visible = [{"type": "text", "text": p["text"]} for p in parts]
    if stage["system"] != RCA_SYSTEM_ROLE or stage["parts"] != visible:
        return None
    if stage["requested_max_tokens"] != 8192 or record["model"] != model:
        raise ProtocolError("bridge model or output request adapter mismatch")
    return path, record


def execute_unit(
    config,
    experiment,
    model,
    opaque,
    unit,
    *,
    scope,
    ledger,
    requests,
    attention,
    stop,
    writer,
    deadline=None,
):
    """One request, with content dedup and durable raw response before analysis."""
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    from vlmrca.vlm.client import call_vlm, count_vllm_prompt_tokens
    from vlmrca.vlm.configs import get_config

    from .exps import RCA_SYSTEM_ROLE, parse_rca, rca_schema

    root = RQ_ROOT / "results" / scope
    target = root / "trajectories" / model / f"{opaque}__{unit['arm']}.json"
    current = load_terminal(target)
    if stop.is_set() or (deadline and time.monotonic() >= deadline):
        return {"status": "not_started", "case": opaque, "arm": unit["arm"]}
    runtime = VLLMInferenceConfig.load(ROOT / config["unified"]["vllm"])
    from urllib.parse import urlparse

    endpoint = runtime.model(model)["base_url"]
    if urlparse(endpoint).hostname not in {"127.0.0.1", "localhost", "::1", "0.0.0.0"}:
        raise ProtocolError("RQ2.1 requires a local vLLM endpoint, never a remote paid service")
    os.environ["VLLM_BASE_URL"] = endpoint
    identity = {
        "schema": "RQ21OutcomeV1",
        "experiment": experiment,
        "model": model,
        "case": opaque,
        "arm": unit["arm"],
        "unit": unit,
        "scope": scope,
    }

    def infeasible_result(reason):
        proof = root / "infeasible" / model / f"{opaque}__{unit['arm']}.json"
        write_json(proof, {**identity, "reason": reason, "model_calls": 0})
        record = {
            **identity,
            "status": "design_infeasible",
            "model_calls": 0,
            "design_signature": stable_hash([unit, code_fingerprint()]),
            "score": {
                "mrr": 0,
                **{k: 0 for k in ("ac@1", "ac@3", "ac@5", "avg@3", "avg@5")},
            },
            "artifacts": [artifact_row(proof)],
            "input_tokens": 0,
            "output_tokens": 0,
        }
        write_json(target, {**record, "record_sha256": stable_hash(record)})
        return {"status": "design_infeasible", "case": opaque, "arm": unit["arm"]}

    try:
        packet, parts, files = materialize_unit(config, opaque, unit, allow_render=False)
    except DesignInfeasible as error:
        if current and current.get("design_signature") != stable_hash([unit, code_fingerprint()]):
            raise ProtocolError("completed design target changed; explicit successor required")
        return infeasible_result(str(error))
    recipe = {
        **runtime.model(model),
        "checkpoint_identity": checkpoint_identity(str(runtime.model_path(model))),
    }
    key = request_identity(
        model,
        recipe,
        parts,
        RCA_SYSTEM_ROLE,
        rca_schema(),
        config["request_adapter"],
    )
    import io

    from PIL import Image

    pixels = sum(
        Image.open(io.BytesIO(p["png"])).width * Image.open(io.BytesIO(p["png"])).height
        for p in parts
        if p["type"] == "image"
    )
    identity.update(
        call_key=key,
        packet_hash=packet["packet_hash"],
        fact_count=len(packet["facts"]),
        image_pixels=pixels,
    )
    if current:
        if current.get("call_key") != key or current.get("unit") != unit:
            raise ProtocolError("completed target request changed; refuse silent resume")
        ledger.reconcile_terminal(target)
        return {"status": "already_complete", "case": opaque, "arm": unit["arm"]}
    # Serializes only identical complete requests; different arms/cases retain
    # the registered 36-way network concurrency.
    import fcntl

    key_path = RQ_ROOT / "results/request_locks" / f"{key}.lock"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with key_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        reuse = ledger.completed(key)
        bridge = None if reuse else try_bridge_reuse(config, opaque, model, parts, unit)
        if reuse or bridge:
            source = reuse if reuse else bridge[0]
            reference = read_json(source)
            stage = reference if reuse else reference["stages"][0]
            prediction, parse_error = parse_rca(stage.get("response_text", ""), packet["candidates"])
            conversation = root / "conversations" / model / f"{opaque}__{unit['arm']}.md"
            image_paths = [
                os.path.relpath(p, conversation.parent) for p in files if p.name == "dashboard.png"
            ]
            writer.bytes(
                conversation,
                conversation_text(
                    identity,
                    RCA_SYSTEM_ROLE,
                    parts,
                    stage.get("response_text", ""),
                    image_paths,
                ).encode(),
            ).result()
            record = {
                **identity,
                "status": "reused",
                "model_calls": 0,
                "source": relative(source),
                "source_kind": "rq21_request" if reuse else "original_bridge",
                "score": private_score(config, opaque, prediction),
                "parse_error": parse_error,
                "response_text": stage.get("response_text", ""),
                "input_tokens": stage.get("input_tokens", 0),
                "output_tokens": stage.get("output_tokens", 0),
                "text_tokens": stage.get("text_tokens", stage.get("text_input_tokens")),
                "image_tokens": stage.get("image_tokens", stage.get("image_input_tokens")),
                "attention_source": relative(source),
                "artifacts": [artifact_row(source), artifact_row(conversation)]
                + reference.get("artifacts", []),
            }
            for field in (
                "attention",
                "performance",
                "finish_reason",
                "truncated",
                "prediction",
                "requested_max_tokens",
            ):
                if field in stage:
                    record[field] = stage[field]
            write_json(target, {**record, "record_sha256": stable_hash(record)})
            return {"status": "reused", "case": opaque, "arm": unit["arm"]}
        cfg = get_config(model, max_tokens=int(config["request_adapter"]["max_tokens"]))
        attempt = None
        raw_path = root / "raw_responses" / f"{key}.json"
        try:
            request_path = root / "requests" / f"{key}.json"
            request_record = {
                "host_admission": requests.description(),
                "system": RCA_SYSTEM_ROLE,
                "parts": [{k: v for k, v in p.items() if k != "png"} for p in parts],
                "response_format": rca_schema(),
                "images": [
                    artifact_row(p) for p in files if p.suffix == ".png" and p.name == "dashboard.png"
                ],
                "recipe": recipe,
                "adapter": config["request_adapter"],
                "call_key": key,
                "sdk_max_retries": 0,
            }
            # Full input survives a timeout/power loss even before any response.
            writer.json(request_path, request_record).result()
            files.append(request_path)
            durable = read_json(raw_path) if raw_path.is_file() else None
            if durable:
                checksum = durable.pop("sha256", None)
                if stable_hash(durable) != checksum or durable["request"]["call_key"] != key:
                    raise ProtocolError("durable raw response mismatch")
                attempt = durable["attempt"]
                ledger.resume_response(attempt, key)
            with requests if durable is None else __import__("contextlib").nullcontext():
                if stop.is_set() or (deadline and time.monotonic() >= deadline):
                    if attempt is not None:
                        ledger.finish(attempt, "interrupted")
                    return {"status": "not_started", "case": opaque, "arm": unit["arm"]}
                if shutil.disk_usage(root.parent).free < config["scheduler"]["min_free_disk_gb"] * 10**9:
                    raise ProtocolError("disk reserve reached; stop new submissions and drain")
                total = (
                    durable["preflight_total"]
                    if durable
                    else count_vllm_prompt_tokens(parts, cfg, system=RCA_SYSTEM_ROLE)
                )
                textual = (
                    durable["preflight_text"]
                    if durable
                    else count_vllm_prompt_tokens(parts, cfg, system=RCA_SYSTEM_ROLE, text_only=True)
                )
                if total is None or textual is None:
                    raise ProtocolError("live token preflight unavailable")
                if (
                    total > config["request_adapter"]["input_limit"]
                    or total + cfg.max_tokens > runtime.model(model)["max_model_len"]
                ):
                    return infeasible_result(
                        f"context capacity: input {total}, reserved output {cfg.max_tokens}"
                    )
                if durable is None:
                    with requests.reserve(total + cfg.max_tokens):
                        if stop.is_set() or (deadline and time.monotonic() >= deadline):
                            return {"status": "not_started", "case": opaque, "arm": unit["arm"]}
                        attempt = ledger.begin(
                            key, scope, 18 if "smoke" in scope else None, result_path=relative(target)
                        )
                        response = call_vlm(
                            parts,
                            model=cfg,
                            system=RCA_SYSTEM_ROLE,
                            max_retries=1,
                            response_format=rca_schema(),
                            partial_output_dir=root / "partial_responses",
                            partial_metadata={**identity, "request_artifact": relative(request_path)},
                            record_performance=True,
                            allow_empty_completion=True,
                        )
            if durable:
                from types import SimpleNamespace

                response = SimpleNamespace(
                    text=durable["response_text"],
                    raw=durable["raw"],
                    performance=durable["performance"],
                    input_tokens=durable["input_tokens"],
                    output_tokens=durable["output_tokens"],
                )
            else:
                raw = {
                    "response_text": response.text,
                    "raw": response.raw,
                    "performance": response.performance,
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "request": identity,
                    "attempt": attempt,
                    "preflight_total": total,
                    "preflight_text": textual,
                }
                writer.json(raw_path, {**raw, "sha256": stable_hash(raw)}).result()
            files.append(raw_path)
            with attention:
                diagnostic, attention_files = persist_attention(
                    (response.raw or {}).get("attention_probe"),
                    parts,
                    RCA_SYSTEM_ROLE,
                    model,
                    runtime,
                    root / "attention" / key,
                    response_text=response.text,
                )
            files.extend(attention_files)
            prediction, parse_error = parse_rca(response.text, packet["candidates"])
            conversation = root / "conversations" / model / f"{opaque}__{unit['arm']}.md"
            image_paths = [
                os.path.relpath(p, conversation.parent) for p in files if p.name == "dashboard.png"
            ]
            pending = [
                writer.bytes(
                    conversation,
                    conversation_text(identity, RCA_SYSTEM_ROLE, parts, response.text, image_paths).encode(),
                ),
            ]
            for future in pending:
                future.result()
            files.append(conversation)
            finish = str((response.raw or {}).get("finish_reason", "unknown"))
            record = {
                **identity,
                "status": "model_failure" if parse_error else "completed",
                "model_calls": 1,
                "attempt": attempt,
                "score": private_score(config, opaque, prediction),
                "prediction": prediction,
                "response_text": response.text,
                "parse_error": parse_error,
                "finish_reason": finish,
                "truncated": finish in {"length", "max_tokens", "max_output_tokens"},
                "input_tokens": response.input_tokens,
                "text_tokens": textual,
                "image_tokens": total - textual,
                "output_tokens": response.output_tokens,
                "performance": response.performance,
                "attention": diagnostic,
                "effective_recipe": recipe,
                "requested_max_tokens": cfg.max_tokens,
                "artifacts": [artifact_row(p) for p in files],
            }
            writer.json(target, {**record, "record_sha256": stable_hash(record)}).result()
            ledger.finish(attempt, record["status"], relative(target))
            prior_error = root / "errors" / model / f"{opaque}__{unit['arm']}.json"
            if prior_error.is_file():
                # Retain the resolved error as history, not as an active failure.
                resolved = root / "resolved_errors" / model / f"{opaque}__{unit['arm']}__{attempt}.json"
                resolved.parent.mkdir(parents=True, exist_ok=True)
                os.replace(prior_error, resolved)
            return {"status": record["status"], "case": opaque, "arm": unit["arm"]}
        except Exception as error:
            if attempt is not None:
                ledger.finish(attempt, "infrastructure_failure")
            stop.set()
            write_json(
                root / "errors" / model / f"{opaque}__{unit['arm']}.json",
                {
                    **identity,
                    "exception": type(error).__name__,
                    "message": str(error),
                    "attempt": attempt,
                },
            )
            raise


def run_model(config, experiment, model, *, smoke=False, champions=None, cube=False):
    from .exps import cube_units, registered_units

    if cube and config.get("fixed_anchor"):
        raise ProtocolError("champion cube is not part of the fixed-anchor experiment")
    if not config["smoke_authorized" if smoke else "execution_enabled"]:
        raise ProtocolError("user review pending: requested model execution is disabled")
    if not execution_gate(config, formal=not smoke, smoke=smoke)["passed"]:
        raise ProtocolError("qualification prerequisites not met")
    if model not in config["models"]:
        raise ProtocolError("unregistered model")
    os.environ["CANVASRCA_VLLM_CONFIG"] = str(ROOT / config["unified"]["vllm"])
    os.environ["CANVASRCA_SDK_MAX_RETRIES"] = "0"
    roster = read_json(RQ_ROOT / "configs/rosters/public.json")["cases"]
    units = cube_units(champions) if cube else registered_units(config, experiment, champions)
    scope = f"{experiment}_smoke_v1" if smoke else formal_scope(config, experiment)
    root = RQ_ROOT / "results" / scope
    root.mkdir(parents=True, exist_ok=True)
    if smoke:
        plan = read_json(RQ_ROOT / "configs/smoke_plan.json")[experiment][model]
        tasks = [(r["case"], next(u for u in units if u["arm"] == r["arm"])) for r in plan]
        supervisor = read_json(root / "supervisor.json")
        remaining = supervisor["deadline_epoch"] - time.time()
        if remaining <= 0:
            return {"status": "timeout_only", "initiated": 0}
        deadline = time.monotonic() + remaining
    else:
        tasks = [(r["opaque_incident_id"], u) for r in roster for u in units]
        deadline = None
        if model == config["models"][1]:
            preceding = root / f"{config['models'][0]}.{'cube_completion' if cube else 'completion'}.json"
            if not preceding.exists() or not read_json(preceding).get("complete"):
                raise ProtocolError("first model must complete before the second starts")
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    from unified_scripts.token_admission import TokenAdmission

    requests = TokenAdmission.from_server_log(
        os.environ["CANVASRCA_ADMISSION_SERVER_LOG"],
        config["scheduler"]["request_concurrency"],
        sum(config["request_adapter"][k] for k in ("input_limit", "max_tokens")),
    )
    attention = threading.BoundedSemaphore(config["scheduler"]["attention_workers"])
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    from vlmrca.vlm.attention_probe import warm_mapping_tokenizer

    warm_mapping_tokenizer(str(VLLMInferenceConfig.load(ROOT / config["unified"]["vllm"]).model_path(model)))
    with RunLock(RQ_ROOT / "results/driver.lock"):
        ledger = CallLedger(
            RQ_ROOT / "results/call_ledger.sqlite",
            config["budgets"]["total_initiated_calls"],
        )
        ledger.recover_interrupted()
        counts = Counter()
        failures = []
        writer = AsyncWriter()
        with ThreadPoolExecutor(max_workers=2 * config["scheduler"]["request_concurrency"]) as pool:
            futures = [
                pool.submit(
                    execute_unit,
                    config,
                    experiment,
                    model,
                    case,
                    unit,
                    scope=scope,
                    ledger=ledger,
                    requests=requests,
                    attention=attention,
                    stop=stop,
                    writer=writer,
                    deadline=deadline,
                )
                for case, unit in tasks
            ]
            for future in as_completed(futures):
                try:
                    result = future.result()
                    counts[result["status"]] += 1
                except Exception as error:  # noqa: BLE001 — propagate worker failure after draining the queue
                    stop.set()
                    failures.append(f"{type(error).__name__}: {error}")
                write_json(
                    root / "progress.json",
                    {
                        "model": model,
                        "counts": dict(counts),
                        "planned": len(tasks),
                        "errors": failures[:5],
                        "time": time.time(),
                        "model_accuracy_hidden": True,
                    },
                )
        writer.drain()
        complete = not failures and counts["not_started"] == 0 and sum(counts.values()) == len(tasks)
        result = {
            "complete": complete,
            "counts": dict(counts),
            "planned": len(tasks),
            "errors": failures,
            "model": model,
            "experiment": experiment,
            "code": code_fingerprint(),
        }
        write_json(root / f"{model}.{'cube_completion' if cube else 'completion'}.json", result)
        return result


def champion_files():
    return {k: RQ_ROOT / "results/champions" / f"{k}.json" for k in ("P", "S", "D")}


def load_champions():
    result = {}
    for key, path in champion_files().items():
        if path.exists():
            row = read_json(path)
            checksum = row.pop("sha256")
            if stable_hash(row) != checksum:
                raise ProtocolError("sealed champion record changed")
            result[key] = row["choice"]
    return result


def select_champion(config, experiment):
    from .exps import choose_champion, registered_units
    from .utils import PRIMARY

    if config.get("fixed_anchor"):
        raise ProtocolError("champion selection is retired; all follow-up conditions use P0/S0/D0")

    stage = {
        "exp_evidence_selection": "P",
        "exp_silhouette_encoding": "S",
        "exp_canvas_composition": "D",
    }[experiment]
    path = champion_files()[stage]
    if path.exists():
        return read_json(path)
    root = RQ_ROOT / "results" / f"{experiment}_formal_v1"
    for model in config["models"]:
        marker = root / f"{model}.completion.json"
        if not marker.exists() or not read_json(marker)["complete"]:
            raise ProtocolError("both models must finish the entire stage before champion selection")
    roster = [
        r for r in read_json(RQ_ROOT / "configs/rosters/public.json")["cases"] if r["role"] == "selection"
    ]
    allowed = {d: [r["opaque_incident_id"] for r in roster if r["dataset"] == d] for d in PRIMARY}
    units = [u for u in registered_units(config, experiment, load_champions()) if u["representation"] == "V"]
    records = []
    for row in roster:
        for model in config["models"]:
            for unit in units:
                record = load_terminal(
                    root / "trajectories" / model / f"{row['opaque_incident_id']}__{unit['arm']}.json"
                )
                if record is None:
                    raise ProtocolError("missing selection target")
                records.append({**record, "dataset": row["dataset"]})
    baseline = {"P": "P0__V", "S": "S0", "D": "D0"}[stage]
    result = choose_champion(
        records,
        baseline,
        models=config["models"],
        datasets=PRIMARY,
        cases_by_dataset=allowed,
        settings=config["selection"],
    )
    result.update(
        choice=result["winner"].removesuffix("__V"),
        stage=stage,
        input_records_hash=stable_hash(records),
        reporting_cases_used=0,
    )
    result["sha256"] = stable_hash(result)
    write_json(path, result)
    return result


def build_smoke_plan(config):
    from .exps import registered_units
    from .utils import PRIMARY

    roster = read_json(RQ_ROOT / "configs/rosters/public.json")["cases"]
    cases = [
        min(
            (r["opaque_incident_id"] for r in roster if r["dataset"] == d and r["role"] == "selection"),
            key=lambda s: stable_hash([config["seed"], "smoke", s]),
        )
        for d in PRIMARY
    ]
    plan = {}
    for experiment in config["experiments"]:
        units = registered_units(config, experiment, {"P": "P0", "S": "S0"})
        plan[experiment] = {}
        for mi, model in enumerate(config["models"]):
            choices = [units[(i + mi * 9) % len(units)] for i in range(9)]
            plan[experiment][model] = [
                {"case": cases[i % 3], "arm": unit["arm"]} for i, unit in enumerate(choices)
            ]
    write_json(RQ_ROOT / "configs/smoke_plan.json", plan)
    return {"experiments": len(plan), "planned_calls_per_experiment": 18, "model_calls": 0}


def formal_suite(config):
    """Run only when explicitly enabled; never reselect using reporting scores."""
    from .exps import cube_units, registered_units

    if not config["execution_enabled"] or not execution_gate(config, formal=True)["passed"]:
        raise ProtocolError("formal suite remains disabled pending user review and all three smokes")
    all_cases = [r["opaque_incident_id"] for r in read_json(RQ_ROOT / "configs/rosters/public.json")["cases"]]
    fixed = bool(config.get("fixed_anchor"))
    if not fixed:
        prepare_batch(config, all_cases)
    # The fixed-anchor successor keeps the complete, already qualified selection
    # preparation and result tree. No raw processing or selector recomputation.
    for experiment in config.get("formal_order", config["experiments"]):
        champions = {} if fixed else load_champions()
        prepare_batch(config, all_cases, units=registered_units(config, experiment, champions))
        for model in config["models"]:
            run_phase(experiment, model, "formal")
        if not fixed:
            select_champion(config, experiment)
    if not fixed:
        experiment = "exp_canvas_composition"
        prepare_batch(config, all_cases, units=cube_units(load_champions()))
        for model in config["models"]:
            run_phase(experiment, model, "cube")
    return analyze_suite(config)


def run_phase(experiment, model, mode):
    """Forward a pause to the supervisor; drain it and never start the next phase."""
    import subprocess

    child = subprocess.Popen(
        ["bash", str(RQ_ROOT / "scripts/model_phase.sh"), experiment, model, mode],
        cwd=ROOT,
        start_new_session=True,
    )
    stopped = False

    def pause(*_):
        nonlocal stopped
        stopped = True
        if child.poll() is None:
            child.send_signal(signal.SIGTERM)  # The shell drains runner before stopping its server.

    prior = {sig: signal.signal(sig, pause) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        status = child.wait()
        if stopped or status:
            raise ProtocolError(f"phase paused/failed ({status}); resume valid completed targets")
    finally:
        for sig, handler in prior.items():
            signal.signal(sig, handler)


def analyze_suite(config):
    """Unseal reporting results only after the full registered design finished."""
    import csv
    import io

    import numpy as np

    from .exps import (
        analyze_outcomes,
        cube_units,
        holm,
        paired_statistics,
        registered_units,
    )

    fixed = bool(config.get("fixed_anchor"))
    champions = {} if fixed else load_champions()
    if not fixed and set(champions) != {"P", "S", "D"}:
        raise ProtocolError("analysis must wait for all three sealed champions")
    roster = read_json(RQ_ROOT / "configs/rosters/public.json")
    records = []
    for experiment in config["experiments"]:
        root = RQ_ROOT / "results" / formal_scope(config, experiment)
        units = registered_units(config, experiment, champions)
        if experiment == "exp_canvas_composition" and not fixed:
            units += cube_units(champions)
        for model in config["models"]:
            names = ["completion"] + (
                ["cube_completion"] if experiment == "exp_canvas_composition" and not fixed else []
            )
            if any(
                not (root / f"{model}.{name}.json").is_file()
                or not read_json(root / f"{model}.{name}.json").get("complete")
                for name in names
            ):
                raise ProtocolError("reporting scores remain sealed until every logical target finishes")
            for row in roster["cases"]:
                for unit in units:
                    record = load_terminal(
                        root / "trajectories" / model / f"{row['opaque_incident_id']}__{unit['arm']}.json"
                    )
                    if record is None or record["unit"] != unit:
                        raise ProtocolError("completed stage has a missing record")
                    records.append(record)
    result = analyze_outcomes(records, roster, config)
    if fixed:
        result["claims"] = (
            "fixed-anchor repeated-exposed evaluation; all five datasets; no champion selection"
        )
        numeric = ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5", "input_tokens", "output_tokens")
        macros = []
        for experiment in config["experiments"]:
            for model in config["models"]:
                for unit in registered_units(config, experiment):
                    rows = [
                        r
                        for r in result["aggregates"]
                        if r["experiment"] == experiment
                        and r["model"] == model
                        and r["arm"] == unit["arm"]
                        and r["subset"] == "all"
                        and r["dataset"] != "pooled_descriptive"
                    ]
                    if len(rows) != 5:
                        raise ProtocolError("five-dataset descriptive macro requires five nonempty datasets")
                    macros.append(
                        {
                            "experiment": experiment,
                            "model": model,
                            "arm": unit["arm"],
                            "dataset": "equal_five_dataset_macro",
                            "subset": "all",
                            "n": sum(r["n"] for r in rows),
                            **{
                                k: float(np.mean([r[k] for r in rows]))
                                if all(r.get(k) is not None for r in rows)
                                else None
                                for k in numeric
                            },
                        }
                    )
        result["dataset_macros"] = macros
    index = {(r["experiment"], r["model"], r["arm"], r["case"]): r for r in records}
    bridge, mechanisms = [], []
    from .exps import (
        parse_rca,
        reason_grounding,
        selection_diagnostics,
        summarize_mechanisms,
    )
    from .utils import is_granularity_aware_hit

    for model in config["models"]:
        for subset in ("selection", "main_report", "all"):
            selected = [
                r
                for r in roster["cases"]
                if subset == "all"
                or (
                    r["role"] == "selection"
                    if subset == "selection"
                    else r["role"] == "report" and r["dataset"] in {"aegislab", "aiops2022", "aiops2025"}
                )
            ]
            for rep in ("T", "V"):
                old, cal, final = [], [], []
                for row in selected:
                    case = row["opaque_incident_id"]
                    path = (
                        ROOT
                        / config["data"]["parent_results"]
                        / "trajectories/direct_rca"
                        / model
                        / f"{case}__{rep}.json"
                    )
                    reference = read_json(path)
                    checksum = reference.pop("record_sha256")
                    if stable_hash(reference) != checksum:
                        raise ProtocolError("bridge altered during reporting")
                    prediction, _ = parse_rca(reference["stages"][0]["response_text"])
                    old.append(private_score(config, case, prediction)["mrr"])
                    cal.append(index["exp_evidence_selection", model, f"P0__{rep}", case]["score"]["mrr"])
                    if not fixed:
                        final.append(index["exp_canvas_composition", model, "CUBE_111", case]["score"]["mrr"])
                contrasts = [("calibration", cal)] + ([] if fixed else [("final_design", final)])
                for name, values in contrasts:
                    bridge.append(
                        {
                            "model": model,
                            "subset": subset,
                            "bridge": rep,
                            "contrast": name,
                            **paired_statistics(values, old),
                        }
                    )
    for subset in ("selection", "main_report", "all"):
        holm([r for r in bridge if r["subset"] == subset])
    # Load the complete CPU pool once per case, not once per arm/model.
    from collections import defaultdict

    by_case = defaultdict(list)
    for record in records:
        by_case[record["case"]].append(record)
    metadata = {r["opaque_incident_id"]: r for r in roster["cases"]}
    for case, case_records in by_case.items():
        root = RQ_ROOT / "results/prepared_selection" / case
        universe = read_json(root / "private/universe.json")
        private = read_json(ROOT / config["data"]["parent_prepared"] / "private" / f"{case}.json")
        policies = {r["unit"]["policy"] for r in case_records}
        packets = {p: read_json(root / "packets" / f"{p}.json") for p in policies}
        diagnostics = {
            p: selection_diagnostics(
                universe,
                read_json(root / "private/selections" / f"{p}.json"),
                packets[p],
                private,
                is_granularity_aware_hit,
            )
            for p in policies
        }
        for record in case_records:
            diag = diagnostics[record["unit"]["policy"]]
            parsed, _ = parse_rca(record.get("response_text", ""))
            mentions = reason_grounding(parsed.get("reason", ""), packets[record["unit"]["policy"]])
            baseline = {
                "exp_evidence_selection": "P0__" + record["unit"]["representation"],
                "exp_silhouette_encoding": "S0",
                "exp_canvas_composition": "D0",
            }[record["experiment"]]
            reference = index[record["experiment"], record["model"], baseline, case]
            delta = record["score"]["mrr"] - reference["score"]["mrr"]
            missing = diag["metric_missing_fraction"]
            mechanisms.append(
                {
                    "case": case,
                    "model": record["model"],
                    "arm": record["arm"],
                    "experiment": record["experiment"],
                    "dataset": metadata[case]["dataset"],
                    "role": metadata[case]["role"],
                    **diag,
                    **mentions,
                    "mrr": record["score"]["mrr"],
                    "ac@1": record["score"]["ac@1"],
                    "input_tokens": record.get("input_tokens", 0),
                    "output_tokens": record.get("output_tokens", 0),
                    "root_cited": sorted(set(diag["root_ids"]) & set(mentions["supported_entity_mentions"])),
                    "ranking_transition": "repair" if delta > 0 else "break" if delta < 0 else "tie",
                    "missingness_band": "unavailable"
                    if missing is None
                    else "none"
                    if missing == 0
                    else "partial"
                    if missing < 0.5
                    else "majority",
                    "candidate_band": "<=50"
                    if diag["candidate_count"] <= 50
                    else "51-150"
                    if diag["candidate_count"] <= 150
                    else ">150",
                    "trace_coverage": diag["regions"]["R"]["selected_items"],
                    "graph_coverage": diag["regions"]["G"]["selected_items"],
                    "attention": record.get("attention", {}),
                    "attention_available": bool(record.get("attention")),
                    "visual_density_facts_per_megapixel": diag["fact_count"] * 1e6 / record["image_pixels"]
                    if record.get("image_pixels")
                    else None,
                }
            )
        del universe
    strata, correlations = summarize_mechanisms(mechanisms)
    result.update(
        champions=champions,
        fixed_anchor=config.get("fixed_anchor"),
        bridge_comparisons=bridge,
        literal_reason_grounding=mechanisms,
        strata=strata,
        attention_correlations=correlations,
        source_records_hash=stable_hash(records),
    )
    target = RQ_ROOT / "results" / ("analysis_p0_v2" if fixed else "analysis_v1")
    write_json(target / "summary.json", result)
    for name in (
        "aggregates",
        "paired_comparisons",
        "bridge_comparisons",
        "literal_reason_grounding",
        "event_group_sensitivity",
        "strata",
        "attention_correlations",
        *(["dataset_macros"] if fixed else []),
    ):
        rows = result[name]
        if rows:
            stream = io.StringIO()
            fields = sorted({k for r in rows for k in r})
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
            atomic_write(target / f"{name}.csv", stream.getvalue().encode())
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for experiment in config["experiments"]:
        lines = [
            f"# {experiment} findings\n",
            "Completed repeated-exposed evaluation. Fixed P0/S0/D0 anchors; no champion selection.\n"
            if fixed
            else "Completed repeated-exposed evaluation. Selection and reporting results are separate.\n",
            "All registered conditions, including no-ops and unsuccessful designs, are retained in the linked tables.\n",
            (
                f"[Complete performance/cost/runtime table](../results/{target.name}/aggregates.csv) · "
                f"[Paired tests](../results/{target.name}/paired_comparisons.csv)\n"
            ),
        ]
        for model in config["models"]:
            sample = [
                r
                for r in result["aggregates"]
                if r["experiment"] == experiment
                and r["model"] == model
                and r["subset"] == ("all" if fixed else "main_report")
                and r["dataset"] == "pooled_descriptive"
            ]
            fig, axes = plt.subplots(1, 2, figsize=(15, max(4, len(sample) * 0.3)), layout="constrained")
            y = np.arange(len(sample))
            axes[0].barh(y, [r["mrr"] for r in sample])
            axes[0].set_yticks(y, [r["arm"] for r in sample])
            axes[0].set_xlabel(
                "MRR (480 cases, descriptive pooled mean)" if fixed else "MRR (210 reporting cases)"
            )
            axes[1].barh(y, [r["input_tokens"] or 0 for r in sample], label="input")
            axes[1].barh(
                y,
                [r["output_tokens"] or 0 for r in sample],
                left=[r["input_tokens"] or 0 for r in sample],
                label="output",
            )
            axes[1].set_yticks(y, [r["arm"] for r in sample])
            axes[1].set_xlabel("Mean tokens (same model only)")
            axes[1].legend()
            image = target / f"{experiment}_{model}.png"
            fig.savefig(image, dpi=130)
            plt.close(fig)
            lines.append(f"\n## {model}\n\n![All arms](../results/{target.name}/{image.name})\n")
        lines.append(
            "\nAttention is correlational. Literal reason matching does not establish correct physical fault propagation. "
            "No confidence intervals are reported. Consult the per-dataset tests and exclusion/parse rates before making a recommendation.\n"
        )
        atomic_write(
            RQ_ROOT / "findings" / f"{experiment}_findings.md",
            "\n".join(lines).encode(),
        )
    return {
        "status": "complete",
        "summary": relative(target / "summary.json"),
        "records": len(records),
    }


def wait_server(config, model, pid=None):
    import urllib.error
    import urllib.request

    from unified_scripts.vllm_inference import VLLMInferenceConfig

    spec = VLLMInferenceConfig.load(ROOT / config["unified"]["vllm"]).model(model)
    request = urllib.request.Request(
        spec["base_url"].rstrip("/") + "/models",
        headers={"Authorization": f"Bearer {os.environ.get('VLLM_API_KEY', 'EMPTY')}"},
    )
    deadline = time.monotonic() + spec.get("wait_timeout_sec", 1800)
    while time.monotonic() < deadline:
        if pid and (
            not Path(f"/proc/{pid}/status").exists() or "State:\tZ" in Path(f"/proc/{pid}/status").read_text()
        ):
            raise ProtocolError("vLLM exited before readiness; inspect its server log")
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                names = {r["id"] for r in json.load(response)["data"]}
            if names != {spec["served_model_name"]}:
                raise ProtocolError("another model is already served at the registered endpoint")
            return {"ready": True, "model": model}
        except urllib.error.HTTPError as error:
            raise ProtocolError(f"vLLM readiness HTTP {error.code}; not a startup timeout") from error
        except OSError:
            time.sleep(2)
    raise ProtocolError("server did not become ready")


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "register",
            "audit-bridge",
            "check-inheritance",
            "gate",
            "prepare-selection",
            "prepare-batch",
            "prepare-designs",
            "run-model",
            "smoke-plan",
            "champion",
            "formal-suite",
            "formal-scope",
            "authorize",
            "wait-server",
        ),
    )
    parser.add_argument("--config")
    parser.add_argument("--case")
    parser.add_argument("--cases", nargs="+")
    parser.add_argument("--workers", type=int)
    parser.add_argument("--pid", type=int)
    parser.add_argument(
        "--experiment",
        choices=("exp_evidence_selection", "exp_silhouette_encoding", "exp_canvas_composition"),
    )
    parser.add_argument("--model", choices=("qwen3.8-27b", "gemma-4-26b-a4b"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--cube", action="store_true")
    parser.add_argument("--mode", choices=("formal", "smoke", "cube"), default="formal")
    args = parser.parse_args()
    config = load_config(args.config)
    os.environ["CANVASRCA_ROOT"] = str(ROOT)
    os.environ["CANVASRCA_PROCESSED_ROOT"] = str(ROOT / config["data"]["processed_root"])
    if args.command == "prepare-selection" and not args.case:
        parser.error("prepare-selection requires a registered selection --case")
    if args.command in {"prepare-selection", "prepare-batch", "prepare-designs"}:
        allowed = {
            r["opaque_incident_id"]
            for r in read_json(RQ_ROOT / "configs/rosters/public.json")["cases"]
            if r["role"] == "selection"
        }
        requested = args.cases or ([args.case] if args.case else [])
        if not requested or not set(requested) <= allowed:
            parser.error("CPU development materialization must use the registered selection set")
    if args.command in {"run-model", "champion", "prepare-designs"} and not args.experiment:
        parser.error("this command requires --experiment")
    if args.command == "run-model" and not args.model:
        parser.error("run-model requires --model")
    from .exps import registered_units

    actions = {
        "register": lambda: register(config),
        "audit-bridge": lambda: bridge_display_audit(config),
        "check-inheritance": verify_parent_copy,
        "gate": lambda: execution_gate(config),
        "prepare-selection": lambda: prepare_selection_case(config, args.case),
        "prepare-batch": lambda: prepare_batch(config, args.cases or [args.case], workers=args.workers),
        "prepare-designs": lambda: prepare_batch(
            config,
            args.cases or [args.case],
            workers=args.workers,
            units=registered_units(
                config,
                args.experiment,
                {} if config.get("fixed_anchor") else {"P": "P0", "S": "S0", **load_champions()},
            ),
        ),
        "run-model": lambda: run_model(
            config,
            args.experiment,
            args.model,
            smoke=args.smoke,
            cube=args.cube,
            champions={"P": "P0", "S": "S0"}
            if args.smoke or config.get("fixed_anchor")
            else load_champions(),
        ),
        "smoke-plan": lambda: build_smoke_plan(config),
        "champion": lambda: select_champion(config, args.experiment),
        "formal-suite": lambda: formal_suite(config),
        "authorize": lambda: execution_gate(config, formal=args.mode != "smoke", smoke=args.mode == "smoke"),
        "wait-server": lambda: wait_server(config, args.model, args.pid),
        "formal-scope": lambda: {"scope": formal_scope(config, args.experiment)},
    }
    result = actions[args.command]()
    if args.command == "formal-scope":
        print(result["scope"])
        return 0
    # Do not dump complete source requests, labels or rankings to progress logs.
    visible = {k: v for k, v in result.items() if k not in {"rows", "trace_display_source", "files"}}
    if "cases" in visible and isinstance(visible["cases"], list):
        visible["cases"] = [
            {k: row[k] for k in ("case", "status", "elapsed_seconds", "model_calls") if k in row}
            for row in visible["cases"]
        ]
    print(json.dumps(visible, indent=2))
    return 1 if result.get("passed") is False or result.get("complete") is False else 0


if __name__ == "__main__":
    raise SystemExit(cli())

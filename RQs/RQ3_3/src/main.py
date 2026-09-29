"""Explicit RQ3.3 CLI: register/prepare/qualify/run/decide/analyze.

No command starts on import. GPU execution requires `run --execute`, a frozen
registration, stage prerequisites and an already launched canonical server.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futures
import contextlib
import fcntl
import hashlib
import json
import os
import pickle
import signal
import threading
import time
from collections import defaultdict
from pathlib import Path

from unified_scripts import stable_hash
from .utils import (CONFIG, ROOT, PRIMARY, ContextInfeasible, NotApplicable,
                    OfflineTokens, load_config, prepare_public_context, read_json)
from . import exps, gates

_TOKENS = None


def configure_environment(config):
    expected = str((ROOT/config["unified"]["vllm"]).resolve())
    configured = os.environ.get("CANVASRCA_VLLM_CONFIG")
    if configured and str(Path(configured).resolve()) != expected:
        raise ValueError("different unified inference profile is active")
    os.environ["CANVASRCA_VLLM_CONFIG"] = expected
    os.environ["CANVASRCA_ATTENTION_ENABLED"] = "0"
    os.environ["CANVASRCA_ATTENTION_MODE"] = "off"
    os.environ["CANVASRCA_ATTENTION_PROBE"] = "0"
    os.environ["CANVASRCA_ATTENTION_PROBE_REQUIRED"] = "0"
    os.environ["OPENAI_MAX_RETRIES"] = "0"
    os.environ["CANVASRCA_SDK_MAX_RETRIES"] = "0"
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[variable] = "1"


@contextlib.contextmanager
def exclusive(path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"another RQ3.3 owner is active: {path}") from exc
        yield


def root_for(config, output=None):
    return Path(output).resolve() if output else ROOT/config["artifacts"]["root"]


def read_registration(config, root):
    value = read_json(root/"registration.json")
    if value["config"] != config:
        raise ValueError("registration configuration changed; version explicitly, do not mix")
    if value["contract"] != gates.source_contract(config):
        raise ValueError("source/config contract changed since registration; no silent resume migration")
    return value


def interleaved_sources(rows):
    queues = defaultdict(list)
    for row in rows:
        queues[(row["dataset"], row.get("source", row["case_id"]))].append(row)
    ordered = []
    while any(queues.values()):
        for key in sorted(queues):
            if queues[key]:
                ordered.append(queues[key].pop(0))
    return ordered


def _prepare_one(args):
    global _TOKENS
    from vlmrca.run_state import atomic_write, write_json
    row, config, root_name = args; root = Path(root_name)
    configure_environment(config)
    opaque = row["opaque_incident_id"]
    flag = root/"preparation_flags"/(opaque+".json")
    if flag.exists():
        return read_json(flag)
    started = time.monotonic()
    try:
        if _TOKENS is None:
            _TOKENS = OfflineTokens(config)
        tokens_ready = time.monotonic()
        public, private = prepare_public_context(row, config)
        public_ready = time.monotonic()
        public["selections"] = exps.prepare_selections(public, _TOKENS, config)
        # Short provenance inventory is sufficient for later targeted analysis.
        summary = {"opaque_incident_id": opaque, "status": "done", "elapsed_s": time.monotonic()-started,
            "observations": dict(__import__("collections").Counter(o["region"] for o in public["observations"])),
            "trace_audit": public["trace_audit"], "parent_provenance": public["parent_provenance"],
            "log_audit": public["log_audit"], "public_timings": public["timings"],
            "selection_timings": public["selection_timings"], "witness_pool_count": public["witness_pool_count"],
            "tokenizer_init_s": tokens_ready-started, "public_context_s": public_ready-tokens_ready,
            "all_selections_s": time.monotonic()-public_ready,
            "base_image_sha256": [hashlib.sha256(p["png"]).hexdigest() for p in public["base_parts"] if p["type"] == "image"],
            "selected": {k: [p["id"] for p in v.get("packs", [])] for k, v in public["selections"].items()}}
        atomic_write(root/"contexts"/(opaque+".pkl"), pickle.dumps(public, protocol=5))
        write_json(root/"private"/(opaque+".json"), private)
        write_json(flag, summary)  # commit only after both artifacts are durable
        return summary
    except Exception as exc:
        write_json(flag, {"opaque_incident_id": opaque, "status": "fail", "error": f"{type(exc).__name__}: {exc}",
                          "elapsed_s": time.monotonic()-started})
        raise


def prepare(config, registration, root, cohort, workers=8, limit=None):
    import multiprocessing as mp
    from vlmrca.run_state import physical_cpu_ids, pin_process_to_core, write_json
    if type(workers) is not int or not 1 <= workers <= 8:
        raise ValueError("worker count must be in 1..8")
    rows = registration["rosters"][cohort]
    if limit is not None:
        # CPU qualification only: one case from each dataset first.
        rows = interleaved_sources(rows)[:limit]
    pending = [r for r in interleaved_sources(rows) if not (root/"preparation_flags"/(r["opaque_incident_id"]+".json")).exists()]
    with exclusive(root/"prepare.lock"):
        result = []
        if pending:
            ctx = mp.get_context("spawn"); queue = ctx.Queue()
            cores = physical_cpu_ids()[:min(workers, len(pending))]
            if not cores:
                raise RuntimeError("no available physical CPU core")
            for core in cores:
                queue.put(core)
            pool = futures.ProcessPoolExecutor(max_workers=len(cores), mp_context=ctx,
                initializer=pin_process_to_core, initargs=(queue,))
            try:
                result = list(pool.map(_prepare_one, [(r, config, str(root)) for r in pending], chunksize=1))
            except BaseException:
                # Python 3.12 lacks terminate_workers(). Retain only this
                # executor's child handles; never pkill unrelated Python jobs.
                owned = list(pool._processes.values())
                pool.shutdown(wait=False, cancel_futures=True)
                for process in owned:
                    if process.is_alive():
                        process.terminate()
                for process in owned:
                    process.join(timeout=1)
                    if process.is_alive():
                        process.kill(); process.join(timeout=1)
                raise
            else:
                pool.shutdown(wait=True)
            finally:
                queue.close(); queue.join_thread()
    summary = {"cohort": cohort, "registered": len(rows), "newly_prepared": len(result),
               "flags": [read_json(root/"preparation_flags"/(r["opaque_incident_id"]+".json")) for r in rows]}
    write_json(root/"preparation_summaries"/(cohort+".json"), summary)
    return summary


def load_context(root, row):
    opaque = row["opaque_incident_id"]
    flag = read_json(root/"preparation_flags"/(opaque+".json"))
    if flag["status"] != "done":
        raise ValueError("case preparation failed; explicit retry-preparation is required")
    with (root/"contexts"/(opaque+".pkl")).open("rb") as handle:
        context = pickle.load(handle)
    if context.get("schema_version") != "WitnessPublicContextV1" or context.get("opaque_incident_id") != opaque:
        raise ValueError("wrong prepared context")
    return context, read_json(root/"private"/(opaque+".json"))


def read_lock(root, *, method=True):
    return read_json(root/("method_lock.json" if method else "variant_lock.json"))


def prerequisite(config, root, stage, smoke):
    # No GPU smoke or future stage silently chooses a winning method.
    if stage == "screen" and not smoke:
        previous = root/"stages/calibration/complete.json"
        if not previous.is_file():
            raise ValueError("finish semantic calibration before screening")
        summary = read_json(previous)
        if summary.get("terminal") != summary.get("registered") or not summary.get("registered"):
            raise ValueError("semantic calibration is not fully terminal")
        if summary.get("failed_units", 0):
            # Legacy completion markers have only an aggregate failed count.
            # Read small flags, never historical prompts/images or source cases.
            registration = read_json(root/"registration.json")
            rows = gates.completed_rows(root, gates.task_matrix(config, registration, "calibration"))
            counts = gates.terminal_failure_counts(rows)
            if counts["failed_units"] != summary["failed_units"]:
                raise ValueError("calibration completion marker and failure flags disagree")
    if stage in {"calibration", "screen"}:
        return None
    if smoke:
        return {"variant": "W_SEM_EXEC", "budget_tokens": 2048, "qualification_only": True}
    if stage == "budget":
        lock = read_lock(root, method=False)
        if not lock["screen_positive"]:
            raise ValueError("negative screen: bounded diagnostic only")
        return lock
    lock = read_lock(root)
    if stage == "diagnostic":
        decision_path = root/"expansion_decision.json"
        if lock["screen_positive"] and (not decision_path.exists() or read_json(decision_path)["passed"]):
            raise ValueError("two-call diagnostic is authorized only after negative development/check")
    elif stage == "check":
        if not lock["screen_positive"]:
            raise ValueError("negative screen cannot enter check")
    else:
        decision = read_json(root/"expansion_decision.json")
        if not decision["passed"]:
            raise ValueError("locked check did not qualify expansion")
    if stage == "events":
        audit = read_json(root/"capability_audit.json")
        if not audit.get("event_branch_qualified"):
            raise ValueError("event branch lacks source-supported linked event qualification")
    if stage in {"regression", "fresh"}:
        if not (root/"stages/effectiveness/complete.json").is_file():
            raise ValueError("finish registered eval before locked generalization")
    return lock


def calibration_runtime_compatibility(historical, current, runtime_config=None):
    """Accept only identical runtime metadata or the proven 1800->300s change.

    The entire historical YAML hash must be reproducible by changing that one
    operational field in the current YAML. Never ignore config_hash wholesale.
    Nothing here modifies the live recipe or the original request records.
    """
    if historical == current:
        return "identical"
    error = "historical calibration runtime differs; register a separate matched calibration"
    if {k: v for k, v in historical.items() if k != "config_hash"} != {
            k: v for k, v in current.items() if k != "config_hash"}:
        raise ValueError(error)
    from copy import deepcopy
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    runtime_config = runtime_config or VLLMInferenceConfig.load()
    actual = runtime_config.data
    if current.get("config_hash") != stable_hash(actual) or actual["common"].get("request_timeout_sec") != 300:
        raise ValueError(error)
    previous = deepcopy(actual)
    previous["common"]["request_timeout_sec"] = 1800
    if historical.get("config_hash") != stable_hash(previous):
        raise ValueError(error)
    return "request_timeout_1800_to_300_only"


def calibration_runtime_preflight(config, registration, root, models=None):
    """Inspect all small source runtime records before loading either GPU model."""
    from RQs.RQ3_1.src.main import _request_envelope
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    path = ROOT/config["data"]["calibration_manifest"] if config["data"].get("calibration_manifest") else root/"calibration_manifest.json"
    manifest = read_json(path)
    if manifest.get("status") != "audited" or not manifest.get("reviewer"):
        raise ValueError("source calibration not audited")
    runtime = VLLMInferenceConfig.load(); rows = []
    for model in models or config["models"]:
        current = _request_envelope(model)["effective_server"]
        for row in registration["rosters"][config["stages"]["calibration"]["cohort"]]:
            opaque = row["opaque_incident_id"]
            try:
                prior = manifest["cases"][opaque][model]["effective_server"]
                outcome = calibration_runtime_compatibility(prior, current, runtime)
            except (KeyError, ValueError) as exc:
                raise ValueError(f"calibration runtime preflight {model}/{opaque}: {exc}") from exc
            rows.append({"model": model, "case": opaque, "compatibility": outcome,
                         "historical_config_hash": prior["config_hash"], "current_config_hash": current["config_hash"]})
    return {"status": "passed", "records": rows, "model_calls": 0}


def compile_unit(task, config, root, context, private, lock, tokens):
    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    stage = task["stage"].removeprefix("smoke_"); arm = task["dimensions"]["arm"]
    condition = task["dimensions"].get("condition")
    selection = exps.selection_for(context, arm, lock, task["dimensions"].get("budget_tokens"))
    system = context["sircl_system"] if arm == "SIRCL_TEXT" else RCA_SYSTEM_ROLE
    audit = {}; effective = None
    if arm.startswith("SC_TEXT_"):
        path = ROOT/config["data"]["calibration_manifest"] if config["data"].get("calibration_manifest") else root/"calibration_manifest.json"
        manifest = read_json(path)
        if manifest.get("status") != "audited" or not manifest.get("reviewer"):
            raise ValueError("source calibration not audited")
        parts, system, effective = exps.calibrated_request(manifest, task["model"], task["case"]["opaque_incident_id"], arm)
    else:
        if condition in {"REMOVE_TARGET", "REMOVE_CONTROL"}:
            pair = exps.removal_pair(context, selection, private, tokens)
            target = pair["target" if condition == "REMOVE_TARGET" else "control"]
            selection["packs"] = [p for p in selection["packs"] if p["id"] != target]
            audit["removal"] = pair
        elif condition == "REANONYMIZE":
            context, selection, private, mapping = exps.reanonymized_context(context, selection, private, task["case"], config)
            audit["reanonymization"] = mapping
        elif condition and (condition.startswith("PAIR_") or condition.startswith("BIND_")):
            selection, intervention = exps.mechanism_selection(context, selection, condition, tokens, config, system)
            audit.update(intervention)
        parts = exps.compile_parts(context, arm, selection)
        if condition == "CANDIDATE_ORDER":
            parts = exps.candidate_order_parts(parts, context["candidates"], config["seed"])
        if stage == "diagnostic" and arm in {"VERIFY_SAME", "VERIFY_WITNESS"}:
            # Shared first output is evidence for *both* second-call controls;
            # no private score, correctness or root ID enters this message.
            first_task = {**task, "dimensions": {"arm": "FIRST_TPV"}}
            first_task["logical_key"] = gates.logical_key(first_task)
            flag = read_json(root/"flags"/(first_task["logical_key"]+".json"))
            if flag["status"] != "done":
                raise NotApplicable("shared first diagnosis unavailable")
            response = read_json(Path(flag["artifact_root"])/"outputs"/(flag["call_key"]+".json"))["response"]
            base = exps.inherited_parts(context)
            if arm == "VERIFY_WITNESS":
                base = exps.compile_parts(context, "W_G", selection)
            parts = exps.append_parts(base, "Previous diagnosis (a model proposal, not verified evidence):\n"+response+
                "\nReconsider the ranking against the supplied observations and return the same RCA JSON format.")
    # Historical calibration keeps the original identity convention and scorer
    # map; all other arms use the corrected public-metadata identity convention.
    calibration = context.get("historical_calibration")
    candidates = context["candidates"]
    if calibration is not None and (arm.startswith("SC_TEXT_") or arm == "TPV_BRIDGE"):
        private = private["historical_calibration_private"]
        candidates = calibration["candidates"]
        if arm == "TPV_BRIDGE":
            parts = calibration["base_parts"]
    okay, counts = tokens.fits(parts, system)
    if not okay:
        raise ContextInfeasible("intact registered request exceeds an effective model context")
    cohort = selection.get("cohort") if selection["variant"] in exps.COHORT_VARIANTS else None
    visible_observations = sorted({m for p in selection["packs"] for m in p["members"]})
    witness_visible = arm not in {"TPV", "TPV_BRIDGE", "FIRST_TPV", "REPEAT", "C_LEGACY", "SIRCL_TEXT", "P0_T_TWIN", "P0_MORE_TRUE", "VERIFY_SAME"} and not arm.startswith("SC_TEXT_")
    if not witness_visible:
        visible_observations, cohort = [], None
    projection = {"schema_version": "RQ33ProjectionV2", "variant": selection["variant"],
                  "budget": selection["budget_tokens"], "selected_packs": selection["packs"] if witness_visible else [],
                  "cohort": cohort, "visible_witness_observation_ids": visible_observations,
                  "qualified_cohort_candidates": len(context["cohorts"]),
                  "cohort_projection": ("marginal" if selection["variant"] == "W_COHORT_MARGINAL" else "joint") if cohort else None,
                  "source_hashes": context["source_hashes"],
                  "model_token_counts": counts, "intervention": audit}
    request = exps.bind_request(task, parts, system, projection)
    if effective is not None:
        calibration_runtime_compatibility(effective, request["envelope"]["effective_server"])
    request["private"] = private; request["candidates"] = candidates
    return request


def timeout_exception(exc):
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        if isinstance(exc, TimeoutError) or type(exc).__name__ in {"ReadTimeout", "ConnectTimeout", "WriteTimeout", "PoolTimeout", "APITimeoutError"}:
            return True
        exc = exc.__cause__ or exc.__context__
    return False


def _execute_one(task, request, config, root):
    from vlmrca.run_state import DurableCallRegister, write_json
    from RQs.RQ3_1.src.main import run_registered_call, score_response_callback
    logical = task["logical_key"]; flag_path = root/"flags"/(logical+".json")
    if flag_path.exists():
        return read_json(flag_path)
    bound = request["task"]
    projection = request["projection"]
    manipulation = {"cohort_included": projection["cohort"] is not None,
                    "cohort_source_available": projection["qualified_cohort_candidates"] > 0,
                    "cohort_projection": projection["cohort_projection"],
                    "visible_witness_count": len(projection["visible_witness_observation_ids"])}
    artifact_root = root/"stages"/task["stage"]/task["model"]
    reuse = stable_hash([request["input_identity"], task["case"]["opaque_incident_id"],
                         task["dimensions"].get("replicate", 0), task["ledger_scope"]])
    index = root/"reuse"/(reuse+".json")
    (root/"reuse").mkdir(parents=True, exist_ok=True)
    # Blocking per-identical-request lock, never serializes different inputs.
    with (root/"reuse"/(reuse+".lock")).open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        if index.exists():
            original = read_json(index)
            value = {**original, "logical_key": logical, "reused_from": original["logical_key"], "new_generation_calls": 0,
                     "manipulation": manipulation}
            write_json(flag_path, value)
            return value
        historical = compatible_bridge(config, request, task)
        if historical is not None:
            value = {**historical, "status": "done", "logical_key": logical,
                     "input_identity": request["input_identity"], "new_generation_calls": 0, "manipulation": manipulation}
            write_json(flag_path, value); write_json(index, value)
            return value
        ledger = DurableCallRegister(root/"calls.sqlite", limit=config["budget"]["hard_limit"],
            scope=task["ledger_scope"], scope_limit=18 if task["stage"].startswith("smoke_") else None)
        try:
            write_json(artifact_root/"projections"/(bound["call_key"]+".json"), request["projection"])
            result = run_registered_call(bound, request["parts"], request["envelope"], artifact_root,
                score_response=score_response_callback(request["private"], request["candidates"]), ledger=ledger)
            cost = read_json(artifact_root/"cost"/(bound["call_key"]+".json"))
            score = result["score"]; metrics = score.get("metrics") or score
            value = {"status": "done", "logical_key": logical, "call_key": bound["call_key"],
                "artifact_root": str(artifact_root), "model_status": result["status"],
                "metrics": {k: metrics[k] for k in ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")},
                "input_identity": request["input_identity"],
                "manipulation": manipulation,
                **{k: cost.get(k) for k in ("input_tokens", "output_tokens", "image_tokens", "text_tokens", "wall_time_s", "new_generation_calls")}}
            write_json(flag_path, value)
            write_json(index, value)
            return value

        except Exception as exc:
            is_timeout = timeout_exception(exc)
            cost_path = artifact_root/"cost"/(bound["call_key"]+".json")
            known_cost = read_json(cost_path) if cost_path.exists() else {}
            value = {"status": "fail", "logical_key": logical, "call_key": bound["call_key"],
                     "artifact_root": str(artifact_root), "failure_class": "request_timeout" if is_timeout else "infrastructure",
                     "error": f"{type(exc).__name__}: {exc}", "auto_retry": False,
                     "manipulation": manipulation,
                     **{k: known_cost.get(k) for k in ("input_tokens", "output_tokens", "image_tokens", "text_tokens", "wall_time_s")}}
            write_json(flag_path, value)
            if not is_timeout:
                raise
            return value


def compatible_bridge(config, request, task):
    """Optional exact-request historical reuse, never guessed from arm names.

    Manifest records are audited pointers to preserved original artifacts. Only
    byte-equal text/pixels, system/schema/runtime and the same scorer qualify.
    The original files are never rewritten. Replicates/smokes cannot use it.
    """
    path = config["data"].get("bridge_manifest")
    if not path or task["ledger_scope"] != "formal" or task["dimensions"].get("replicate", 0):
        return None
    manifest = read_json(ROOT/path)
    if manifest.get("status") != "audited" or not manifest.get("reviewer"):
        raise ValueError("historical bridge pointers are not audited")
    record = manifest.get("requests", {}).get(request["input_identity"])
    if record is None:
        return None
    actual = request["actual"]
    if record["model"] != task["model"] or record["opaque_incident_id"] != task["case"]["opaque_incident_id"]:
        raise ValueError("historical response identity mismatch")
    source = read_json(ROOT/record["input_path"])
    parts = []
    for part in source["parts"]:
        if part["type"] == "text":
            parts.append({"type": "text", "text": part["text"]})
        else:
            image = (ROOT/record["images_by_sha256"][part["sha256"]]).read_bytes()
            digest = hashlib.sha256(image).hexdigest()
            if digest != part["sha256"]:
                raise ValueError("historical image differs from original request")
            parts.append({"type": "image", "sha256": digest})
    descriptor = {"model": record["model"], "system": record["system"], "schema": record["schema"],
                  "effective_server": record["effective_server"], "parts": parts}
    if descriptor != actual:
        return None
    scorer_files = [ROOT/config["unified"]["scorer"], ROOT/"src/unified_scripts/rca_scorer.py"]
    scorer_hash = stable_hash({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in scorer_files})
    if record["scorer_hash"] != scorer_hash:
        return None
    old_root = (ROOT/record["artifact_root"]).resolve(); key = record["call_key"]
    required = [old_root/"outputs"/(key+".json"), old_root/"cost"/(key+".json"), ROOT/record["conversation_path"], ROOT/record["raw_response_path"]]
    if not all(p.is_file() for p in required):
        raise ValueError("historical bridge lacks preserved output/conversation/raw evidence")
    result, cost = read_json(required[0]), read_json(required[1])
    score = result["score"]; metrics = score.get("metrics") or score
    return {"call_key": key, "artifact_root": str(old_root), "historical_bridge": True,
            "model_status": result["status"], "metrics": {m: metrics[m] for m in ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")},
            **{k: cost.get(k) for k in ("input_tokens", "output_tokens", "image_tokens", "text_tokens", "wall_time_s")}}
def _reconcile_interrupted(root, scope):
    """Under exclusive owner lock, mark only unresolved started attempts.

    Completed ledger rows and their artifacts are not visited or rehashed.
    """
    from vlmrca.run_state import DurableCallRegister
    ledger = DurableCallRegister(root/"calls.sqlite", limit=40000, scope=scope)
    with ledger.connect() as db:
        prefix = scope+"/"
        db.execute("UPDATE calls SET state='interrupted', result=? WHERE state='started' AND substr(call_key,1,?)=?",
                   (json.dumps({"reason": "previous exclusive runner ended before commit"}), len(prefix), prefix))


def run(config, registration, root, stage, model, *, execute=False, smoke=False):
    from vlmrca.run_state import write_json
    tasks = gates.task_matrix(config, registration, stage, model, smoke)
    if not execute:
        return {"status": "planned_only", "tasks": len(tasks), "stage": stage, "model": model}
    if not tasks:
        raise ValueError("stage has no authorized cases; independent-event audit may be unavailable")
    # Scoring depends on the local upstream shim. Resolve it before launching
    # any inference so a missing checkout cannot strand completed generations.
    from vlmrca.eval.scoring import is_granularity_aware_hit
    if not is_granularity_aware_hit("scorer-preflight", "scorer-preflight"):
        raise RuntimeError("granularity-aware scorer preflight failed")
    lock = prerequisite(config, root, stage, smoke)
    if not smoke:
        experiment = config["stages"][stage]["experiment"]
        qualification = read_json(root/"qualification"/(experiment+".json"))
        if qualification.get("status") != "passed" or qualification.get("contract_hash") != stable_hash(registration["contract"]):
            raise ValueError("experiment has no current CPU/manual/bounded-smoke qualification")
    with exclusive(root/"run.lock"):
        # First action is tiny flag reads, BEFORE tokenizer/context construction.
        pending = [t for t in tasks if not (root/"flags"/(t["logical_key"]+".json")).exists()]
        if not pending:
            return {"status": "already_terminal", "tasks": len(tasks)}
        if stage == "calibration":
            write_json(root/"runtime_preflights"/("calibration_"+model+".json"),
                       calibration_runtime_preflight(config, registration, root, [model]))
        _reconcile_interrupted(root, pending[0]["ledger_scope"])
        tokens = OfflineTokens(config)
        stop = threading.Event()
        previous = {}
        def interrupt(signum, frame):
            stop.set()
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous[sig] = signal.signal(sig, interrupt)
        completed = len(tasks)-len(pending); inflight = {}; fatal = None
        executor = futures.ThreadPoolExecutor(max_workers=config["execution"]["request_concurrency"])
        current_id = None; context = private = None
        try:
            for task in pending:
                if stop.is_set():
                    break
                # Second-call diagnostic must wait for the shared FIRST_TPV.
                dependent = stage == "diagnostic" and task["dimensions"]["arm"] in {"VERIFY_SAME", "VERIFY_WITNESS"}
                while inflight and (len(inflight) >= config["execution"]["request_concurrency"] or dependent):
                    done, _ = futures.wait(inflight, return_when=futures.FIRST_COMPLETED)
                    for f in done:
                        f.result(); inflight.pop(f); completed += 1
                opaque = task["case"]["opaque_incident_id"]
                if current_id != opaque:
                    context, private = load_context(root, task["case"]); current_id = opaque
                try:
                    request = compile_unit(task, config, root, context, private, lock, tokens)
                except (NotApplicable, ContextInfeasible) as exc:
                    write_json(root/"flags"/(task["logical_key"]+".json"), {
                        "status": "not_applicable" if isinstance(exc, NotApplicable) else "design_infeasible",
                        "reason": str(exc), "logical_key": task["logical_key"], "new_generation_calls": 0})
                    completed += 1; continue
                f = executor.submit(_execute_one, task, request, config, root); inflight[f] = task
                for f in [f for f in inflight if f.done()]:
                    f.result(); inflight.pop(f); completed += 1
                print(f"[{stage}/{model}] terminal={completed}/{len(tasks)} inflight={len(inflight)}", flush=True)
            for f in futures.as_completed(inflight):
                f.result(); completed += 1
        except Exception as exc:
            fatal = exc; stop.set()
            for f in inflight:
                f.cancel()
        finally:
            executor.shutdown(wait=True, cancel_futures=True)
            for sig, handler in previous.items():
                signal.signal(sig, handler)
            write_json(root/"stages"/tasks[0]["stage"]/(model+"_progress.json"), {
                "tasks": len(tasks), "terminal": sum((root/"flags"/(t["logical_key"]+".json")).exists() for t in tasks),
                "paused": stop.is_set(), "fatal": str(fatal) if fatal else None})
        if fatal:
            raise fatal
        if not stop.is_set():
            all_tasks = gates.task_matrix(config, registration, stage, smoke=smoke)
            if all((root/"flags"/(t["logical_key"]+".json")).exists() for t in all_tasks):
                flags = [read_json(root/"flags"/(t["logical_key"]+".json")) for t in all_tasks]
                counts = gates.terminal_failure_counts(flags)
                write_json(root/"stages"/tasks[0]["stage"]/"complete.json", {"registered": len(all_tasks), "terminal": len(all_tasks), **counts})
        return {"stage": stage, "model": model, "terminal": completed, "paused": stop.is_set()}


def rows_for(config, registration, root, stage):
    return gates.completed_rows(root, gates.task_matrix(config, registration, stage))


def decide(config, registration, root, decision):
    if decision == "variant":
        value = gates.select_variant(rows_for(config, registration, root, "screen"), config)
        name = "variant_lock.json"
    elif decision == "budget":
        value = gates.lock_budget(read_lock(root, method=False), rows_for(config, registration, root, "screen"),
                                 rows_for(config, registration, root, "budget"), config)
        name = "method_lock.json"
    elif decision == "default-budget":
        value = {**read_lock(root, method=False), "schema_version": "RQ33MethodLockV1", "budget_compared": False}
        name = "method_lock.json"
    else:
        value = gates.check_expansion(rows_for(config, registration, root, "check"), config)
        audit = read_json(root/"capability_audit.json")
        value["source_semantics_audited"] = audit.get("status") == "passed" and bool(audit.get("reviewer"))
        value["passed"] &= value["source_semantics_audited"]
        name = "expansion_decision.json"
    value["contract_hash"] = stable_hash(registration["contract"])
    gates.immutable_json(root/name, value)
    return value


def analyze(config, registration, root, stage):
    from vlmrca.run_state import write_json
    rows = rows_for(config, registration, root, stage)
    comparisons = []; interactions = []; sensitivity = []; interaction_tests = []
    if stage == "screen":
        arms = [(a, "TPV") for a in exps.W_VARIANTS]+[("P0_MORE_TRUE", "TPV"),
                ("W_COHORT", "W_COHORT_MARGINAL"), ("W_COHORT_MARGINAL", "W_SEM_EXEC"),
                ("W_COHORT", "W_SEM_EXEC"), ("W_FRONT", "W_SEM_EXEC")]
    elif stage == "budget":
        variant = read_lock(root, method=False)["variant"]
        for row in rows:
            row["dimensions"] = {**row["dimensions"], "arm": row["dimensions"]["arm"]+"_B"+str(row["dimensions"]["budget_tokens"])}
        baseline = rows_for(config, registration, root, "screen")
        for row in baseline:
            arm = row["dimensions"]["arm"]
            if arm in {variant, "P0_MORE_TRUE", "TPV"}:
                row["dimensions"] = {**row["dimensions"], "arm": "W_G_B2048" if arm == variant else "P0_MORE_TRUE_B2048" if arm == "P0_MORE_TRUE" else "TPV"}
                rows.append(row)
        arms = [(a+"_B"+str(b), a+"_B2048") for a in ("W_G", "P0_MORE_TRUE") for b in (1024, 4096)]
        arms += [("W_G_B"+str(b), "P0_MORE_TRUE_B"+str(b)) for b in (1024, 2048, 4096)]
    elif stage in {"check", "effectiveness", "regression", "fresh"}:
        arms = [("W_G", a) for a in ("TPV", "SIRCL_TEXT", "P0_MORE_TRUE", "W_T")]
    elif stage == "organization":
        baseline = rows_for(config, registration, root, "effectiveness")
        ids = {r["case_id"] for r in rows}
        rows += [r for r in baseline if r["case_id"] in ids and r["dimensions"]["arm"] in {"W_T", "W_G"}]
        arms = [("W_T_FLAT", "W_T"), ("W_G_FLAT", "W_G"), ("W_G_SCREENSHOT", "W_T"),
                ("W_G_SCREENSHOT", "W_G"), ("W_G_RELAYOUT", "W_G_SCENE_CAL"), ("W_NO_SCOPE", "W_G"), ("W_NO_FLOW", "W_G")]
    elif stage == "events":
        arms = [("EVENT_GRAPH", "EVENT_SCREEN"), ("EVENT_GRAPH", "EVENT_TEXT")]
    elif stage == "diagnostic":
        arms = [("VERIFY_WITNESS", "VERIFY_SAME"), ("VERIFY_SAME", "REPEAT"), ("REPEAT", "FIRST_TPV")]
    elif stage in {"interventions", "binding", "pairs"}:
        baseline = rows_for(config, registration, root, "effectiveness") if stage != "pairs" else []
        ids = {r["case_id"] for r in rows}
        for row in rows:
            dimensions = dict(row["dimensions"])
            dimensions["arm"] += "_"+dimensions.pop("condition")
            row["dimensions"] = dimensions
        rows += [r for r in baseline if r["case_id"] in ids and r["dimensions"]["arm"] in {"W_T", "W_G"}]
        if stage == "pairs":
            arms = [("W_"+c+"_PAIR_"+s, "W_"+c+"_PAIR_00") for c in ("T", "G") for s in ("10", "01", "11")]
        else:
            arms = [("W_"+c+"_"+s, "W_"+c) for c in ("T", "G") for s in config["stages"][stage]["conditions"]]
            if stage == "binding":
                arms += [("W_"+c+"_BIND_LOCAL", "W_"+c+"_BIND_REMOTE") for c in ("T", "G")]
            else:
                arms += [("W_"+c+"_REMOVE_TARGET", "W_"+c+"_REMOVE_CONTROL") for c in ("T", "G")]
    elif stage == "calibration":
        arms = [("SC_TEXT_GUIDE_FIXED", "SC_TEXT_AS_RUN"), ("SC_TEXT_SOURCE_FIXED", "SC_TEXT_GUIDE_FIXED")]
    else:
        arms = []
    for model in config["models"]:
        # One shared complete-case denominator per model/stage family.
        family_arms = tuple(sorted({a for pair in arms for a in pair}))
        if not family_arms:
            continue
        pairs, excluded = gates.pairable(rows, family_arms, model)
        for a, b in arms:
            # Registered removals have a distinct applicability domain; a
            # missing target must not erase nonsemantic/repeat analyses.
            if stage in {"organization", "interventions", "events", "binding"}:
                pairs, excluded = gates.pairable(rows, (a, b), model)
            for population in (*PRIMARY, "re2_ob", "re2_tt", "primary_pooled", "aiops_combined", "all"):
                selected = [p for p in pairs if population == "all" or p[a]["dataset"] == population or
                            population == "primary_pooled" and p[a]["dataset"] in PRIMARY or
                            population == "aiops_combined" and p[a]["dataset"] in PRIMARY[:2]]
                comparisons.append({"model": model, "arm": a, "baseline": b, "population": population,
                    "excluded_case_ids": excluded, **gates.paired_statistics(selected, a, b)})
            grouped = gates.group_pairs(pairs, a, b, registration["groups"])
            sensitivity.append({"model": model, "arm": a, "baseline": b, **gates.paired_statistics(grouped, a, b)})
        if stage == "screen":
            interactions.append(gates.factorial(rows, model, {"00": "W_RAW", "10": "W_SEM", "01": "W_EXEC", "11": "W_SEM_EXEC"}))
        if stage == "pairs":
            for carrier in ("T", "G"):
                result = gates.factorial(rows, model, {k: "W_"+carrier+"_PAIR_"+k for k in ("00", "10", "01", "11")})
                result["interpretation"] = "RR_utility_interaction_not_Shannon_PID"
                interactions.append(result)
                interaction_tests.extend({"model": model, "carrier": carrier, **r}
                                         for r in gates.interaction_statistics(result, registration["groups"]))
        if stage in {"effectiveness", "regression", "fresh"}:
            interactions.append(gates.factorial(rows, model, {"00": "P0_T_TWIN", "10": "W_T", "01": "TPV", "11": "W_G"}))
    # Explicit broad family over arms, models and reported populations. No
    # post-result re-partitioning to improve significance.
    result = {"schema_version": "RQ33AnalysisV1", "stage": stage,
              "summary": gates.summarize(rows), "paired": gates.holm(comparisons),
              "event_group_sensitivity": gates.holm(sensitivity), "factorials": interactions,
              "utility_interaction_tests": gates.holm([r for r in interaction_tests if not r["event_group_sensitivity"]]),
              "utility_interaction_group_tests": gates.holm([r for r in interaction_tests if r["event_group_sensitivity"]]),
              "rows": rows, "confidence_intervals": "not_reported"}
    if stage == "budget":
        result["diagnostic_cost_curve"] = [{**r, "diagnostic_loss": 1-r["mrr"] if r["mrr"] is not None else None}
                                            for r in result["summary"]]
        result["curve_interpretation"] = "empirical_loss_cost_curve_not_Shannon_rate_distortion_or_MRR_per_token_selection"
    if stage == "screen":
        result["cohort_applicability"] = [r for model in config["models"] for r in gates.cohort_control_summary(rows, model)]
    if stage == "diagnostic":
        result["two_call_costs"] = []
        for model in config["models"]:
            for arm in ("REPEAT", "VERIFY_SAME", "VERIFY_WITNESS"):
                paired, excluded = gates.pairable(rows, ("FIRST_TPV", arm), model)
                for p in paired:
                    result["two_call_costs"].append({"model": model, "case_id": p[arm]["case_id"], "branch": arm,
                        "final_mrr": gates.metric(p[arm]), "excluded": excluded,
                        **{key: sum(p[a][key] for a in ("FIRST_TPV", arm)) if all(p[a].get(key) is not None for a in ("FIRST_TPV", arm)) else None
                           for key in ("input_tokens", "output_tokens", "wall_time_s")}})
    write_json(root/"analysis"/(stage+".json"), result)
    return {"stage": stage, "rows": len(rows), "path": str(root/"analysis"/(stage+".json"))}


def retry_flag(root, key, preparation=False):
    # Explicit target only; done flags cannot be reset by this command.
    from vlmrca.run_state import write_json
    folder = "preparation_flags" if preparation else "flags"
    if not key or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in key):
        raise ValueError("invalid flag identity")
    path = root/folder/(key+".json"); old = read_json(path)
    if old["status"] != "fail":
        raise ValueError("only a diagnosed failed target may be retried")
    archive = root/"retry_authorizations"/(str(time.time_ns())+"_"+key+".json")
    write_json(archive, old); path.unlink()
    return {"retry_enabled": key, "prior_flag": str(archive)}


def smoke_inputs(config, registration, root, stage):
    """Check local prerequisites before spending the smoke window loading GPUs."""
    cpu = read_json(root/"cpu_qualification.json")
    if cpu.get("status") != "passed" or cpu.get("contract_hash") != stable_hash(registration["contract"]):
        raise ValueError("current real-case CPU qualification is required before smoke")
    from vlmrca.eval.scoring import is_granularity_aware_hit
    if not is_granularity_aware_hit("scorer-preflight", "scorer-preflight"):
        raise RuntimeError("granularity-aware scorer preflight failed")
    tokens = OfflineTokens(config)
    lock = prerequisite(config, root, stage, True)
    contexts = {}
    for task in gates.task_matrix(config, registration, stage, smoke=True):
        key = task["case"]["opaque_incident_id"]
        if key not in contexts:
            contexts[key] = load_context(root, task["case"])
        context, private = contexts[key]
        try:
            compile_unit(task, config, root, context, private, lock, tokens)
        except (NotApplicable, ContextInfeasible):
            continue


def smoke(config, registration, root, experiment):
    """One experiment, two sequential owned servers, absolute 600s/18 calls.

    Future opt-in execution only. Refuse an existing server rather than stopping
    someone else's process. Hard deadline includes startup and all writes.
    """
    import subprocess
    import sys
    import urllib.error
    import urllib.request
    from vlmrca.run_state import DurableCallRegister, write_json
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    stages = {"exp_semantic_calibration": "calibration", "exp_witness_development": "screen",
              "exp_witness_effectiveness": "effectiveness", "exp_visual_and_diagnostic_mechanisms": "organization",
              "exp_witness_locked_generalization": "regression"}
    stage = stages[experiment]; started = time.monotonic(); deadline = started+600
    runtime = VLLMInferenceConfig.load(ROOT/config["unified"]["vllm"])
    report = {"status": "complete", "contract_hash": stable_hash(registration["contract"]), "completed_units": []}
    owned = []; handles = []
    destination = root/"smokes"/(experiment+".json")
    if destination.exists():
        raise ValueError("one logical smoke already recorded; inspect it, do not silently start another")
    ledger = DurableCallRegister(root/"calls.sqlite", limit=40000, scope="smoke:"+experiment, scope_limit=18)
    def cleanup():
        for process in reversed(owned):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        owned.clear()
    def deadline_hit(signum, frame):
        raise TimeoutError("absolute bounded-smoke wall deadline")
    previous = signal.signal(signal.SIGALRM, deadline_hit); signal.alarm(600)
    try:
        smoke_inputs(config, registration, root, stage)
        for model in config["models"]:
            url = runtime.model(model)["base_url"].rstrip("/")+"/models"
            probe = urllib.request.Request(url, headers={
                "Authorization": "Bearer " + os.environ.get("VLLM_API_KEY", "EMPTY")})
            try:
                with urllib.request.urlopen(probe, timeout=min(2, max(.1, deadline-time.monotonic()))) as response:
                    response.read()
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f"endpoint responded with HTTP {exc.code} before smoke server startup") from exc
            except OSError:
                pass
            else:
                raise RuntimeError("a server already owns the endpoint; smoke will not stop it")
            logfile = root/"smokes"/(experiment+"_"+model+"_server.log")
            logfile.parent.mkdir(parents=True, exist_ok=True); handle = logfile.open("ab"); handles.append(handle)
            server = subprocess.Popen(["bash", "scripts/vllm_vlm/serve_canvasrca_local.sh", model], cwd=ROOT,
                stdout=handle, stderr=subprocess.STDOUT, start_new_session=True); owned.append(server)
            while True:
                if server.poll() is not None:
                    raise RuntimeError("owned smoke server exited before readiness; inspect its log")
                try:
                    with urllib.request.urlopen(probe, timeout=2) as response:
                        models = json.load(response)
                    if runtime.model(model)["served_model_name"] not in [m["id"] for m in models["data"]]:
                        raise RuntimeError("wrong model at smoke endpoint")
                    break
                except urllib.error.HTTPError as exc:
                    raise RuntimeError(f"smoke server readiness returned HTTP {exc.code}") from exc
                except OSError:
                    time.sleep(2)
            command = [sys.executable, "-m", "RQs.RQ3_3.src.main", "--output", str(root),
                       "run", "--stage", stage, "--model", model, "--smoke", "--execute"]
            log = (root/"smokes"/(experiment+"_"+model+"_runner.log")).open("ab"); handles.append(log)
            runner = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            owned.append(runner)
            code = runner.wait(timeout=max(.1, deadline-time.monotonic()))
            if code:
                raise RuntimeError("bounded smoke runner failed; inspect logs and terminal flags")
            cleanup()
    except (TimeoutError, subprocess.TimeoutExpired):
        report["status"] = "bounded_timeout_only"
    except BaseException as exc:
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        signal.alarm(0); signal.signal(signal.SIGALRM, previous); cleanup()
        for handle in handles:
            handle.close()
        tasks = gates.task_matrix(config, registration, stage, smoke=True)
        flags = [read_json(root/"flags"/(t["logical_key"]+".json")) for t in tasks if (root/"flags"/(t["logical_key"]+".json")).exists()]
        report["completed_units"] = [f["logical_key"] for f in flags if f["status"] == "done"]
        # Request timeouts are infrastructure errors in smoke, unlike the global
        # 600s bounded outcome. Formal timeouts remain terminal-and-continue.
        if any(f["status"] == "fail" for f in flags):
            report["status"] = "failed"
        with ledger.connect() as db:
            prefix = "smoke:"+experiment+"/"
            report["initiated_calls"] = db.execute("SELECT count(*) FROM calls WHERE substr(call_key,1,?)=?", (len(prefix), prefix)).fetchone()[0]
        report["elapsed_s"] = time.monotonic()-started
        write_json(destination, report)
    return report


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--output", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("register")
    p = sub.add_parser("prepare"); p.add_argument("--cohort", default="screen"); p.add_argument("--workers", type=int, default=8); p.add_argument("--limit", type=int)
    p = sub.add_parser("run"); p.add_argument("--stage", required=True); p.add_argument("--model", required=True); p.add_argument("--execute", action="store_true"); p.add_argument("--smoke", action="store_true")
    p = sub.add_parser("decide"); p.add_argument("decision", choices=("variant", "budget", "default-budget", "expansion"))
    p = sub.add_parser("analyze"); p.add_argument("--stage", required=True)
    p = sub.add_parser("retry"); p.add_argument("--key", required=True); p.add_argument("--preparation", action="store_true")
    p = sub.add_parser("cpu-check"); p.add_argument("--seconds", type=int, default=1800)
    p = sub.add_parser("qualify"); p.add_argument("--experiment", required=True); p.add_argument("--manual-audit", type=Path, required=True)
    p = sub.add_parser("smoke"); p.add_argument("--experiment", required=True)
    p = sub.add_parser("calibration-manifest"); p.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(); config = load_config(args.config); configure_environment(config); root = root_for(config, args.output)
    if args.command == "register":
        result = gates.register_rosters(config, root)
        result = {"registration": str(root/"registration.json"), "cohorts": {k: len(v) for k, v in result["rosters"].items()}}
    elif args.command == "retry":
        result = retry_flag(root, args.key, args.preparation)
    else:
        registration = read_registration(config, root)
        if args.command == "prepare":
            result = prepare(config, registration, root, args.cohort, args.workers, args.limit)
        elif args.command == "run":
            result = run(config, registration, root, args.stage, args.model, execute=args.execute, smoke=args.smoke)
        elif args.command == "decide":
            result = decide(config, registration, root, args.decision)
        elif args.command == "analyze":
            result = analyze(config, registration, root, args.stage)
        elif args.command == "cpu-check":
            from .tests import cpu_qualification
            result = cpu_qualification(config, registration, root, args.seconds)
        elif args.command == "smoke":
            result = smoke(config, registration, root, args.experiment)
        elif args.command == "calibration-manifest":
            manifest = read_json(args.manifest)
            if manifest.get("status") != "audited" or not manifest.get("reviewer"):
                raise ValueError("calibration needs an actual source audit, not guessed patches")
            for row in registration["rosters"]["screen"]:
                for model in config["models"]:
                    for arm in ("SC_TEXT_AS_RUN", "SC_TEXT_GUIDE_FIXED", "SC_TEXT_SOURCE_FIXED"):
                        exps.calibrated_request(manifest, model, row["opaque_incident_id"], arm)
            gates.immutable_json(root/"calibration_manifest.json", manifest)
            result = {"manifest": str(root/"calibration_manifest.json"), "status": "registered"}
        else:
            from .tests import qualify
            result = qualify(config, registration, root, args.experiment, args.manual_audit)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    cli()

"""Resumable bounded preparation/inference; CLI never launches implicitly."""

import argparse
import concurrent.futures as cf
import json
import os
import pickle
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections import defaultdict

from . import exps, gates
from .utils import (
    METRICS,
    MODULE,
    ROOT,
    ZERO,
    DesignInfeasible,
    call_count,
    digest,
    endpoint_vacant,
    load_config,
    model_probe,
    read_json,
    reference_only,
    runtime_config,
    save_json,
    saved_prompt_path,
    stop_owned,
    terminal_flag,
)

_TOKENS = None


def source_context(config, row, tokens):
    """Cached public context first. Cold fallback processes this per-case only."""
    from RQs.RQ3_1.src.exps import _registered_trace_duration_projection

    source = ROOT / config["implementation"]["source_run"]
    root = ROOT / config["implementation"]["output_root"]
    oid = row["opaque_incident_id"]
    candidate = source / "contexts" / (oid + ".pkl")
    if candidate.exists():
        marker = read_json(source / "preparation_flags" / (oid + ".json"))
        if marker["status"] != "done":
            raise ValueError("Uncommitted parent context")
        context = pickle.loads(candidate.read_bytes())
    else:
        local = root / "contexts" / (oid + ".pkl")
        if local.exists() and (root / "preparation_flags" / (oid + ".json")).exists():
            context = pickle.loads(local.read_bytes())
        else:
            from RQs.RQ3_3.src.utils import prepare_public_context
            from RQs.RQ3_4.src.exps import prepare_integrated
            from RQs.RQ3_4.src.utils import metric_selection_metadata
            from vlmrca.run_state import atomic_write

            context, private = prepare_public_context(row, runtime_config(config))
            parent = read_json(ROOT / "RQs/RQ3_4/configs/integrated_round_v1.json")
            context["selection_metadata"] = metric_selection_metadata(
                context, row, parent
            )
            context["integrated"] = prepare_integrated(context, tokens, parent)
            atomic_write(local, pickle.dumps(context, protocol=5))
            save_json(root / "private" / (oid + ".json"), private)
            save_json(
                root / "preparation_flags" / (oid + ".json"),
                {"status": "done", "case": oid},
            )
    if (
        context.get("opaque_incident_id") != oid
        or context.get("integrated", {}).get("clock_projection_version")
        != "relative_clock_v1"
    ):
        raise ValueError("Wrong/stale public context")
    if context["prepared"].private:
        raise ValueError("Public prepared object contains private metadata")
    scale, provenance = _registered_trace_duration_projection(row["dataset"])
    if scale not in {1.0, 0.001}:
        raise ValueError("Unknown source duration unit")
    context["rq36_parent_trace_unit"] = "us" if scale == 0.001 else "ms"
    context["rq36_duration_source"] = provenance
    return context


def private_for(config, root, row):
    oid = row["opaque_incident_id"]
    for base in (root, ROOT / config["implementation"]["source_run"]):
        path = base / "private" / (oid + ".json")
        if path.exists():
            return read_json(path)
    raise FileNotFoundError("No evaluator-private record for prepared case")


def bridge_parts(entry):
    """Load saved model-visible input, not serialized evidence from an output."""
    base, key = ROOT / entry["root"], entry["call_key"]
    completion = read_json(base / "completed" / (key + ".json"))
    if completion["status"] != "complete":
        raise ValueError("Bridge has no complete original commit")
    prompt = read_json(saved_prompt_path(base, key))
    parts = []
    for part in prompt["parts"]:
        if part["type"] == "text":
            parts.append({"type": "text", "text": part["text"]})
        else:
            path = (base / part["image_path"]).resolve()
            if not path.is_relative_to(base.resolve()):
                raise ValueError("Bridge image escapes artifact root")
            parts.append({"type": "image", "png": path.read_bytes()})
    return parts, prompt


def reference_input(context, arm, parent, tokens):
    """Only absent bridges need the unchanged parent renderer recipe."""
    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    from RQs.RQ3_6.src.exps import (
        mechanism_parts,
        parent_unit_labels,
        prepare_mechanisms,
    )

    if arm == "TPV_REF":
        parts = parent_unit_labels(
            context["base_parts"], context["rq36_parent_trace_unit"]
        )
    elif arm == "B3_G_REF":
        prepare_mechanisms(context, parent, tokens)
        parts = mechanism_parts(context, "ALL_ID_G", parent)
    else:
        raise ValueError("Removed/unknown reference generation arm")
    return parts, RCA_SYSTEM_ROLE


def compile_case(arguments):
    """One public load per case, both processor objects persist per pinned worker."""
    global _TOKENS
    config, registration, targets = arguments
    from RQs.RQ3_3.src.exps import request_descriptor
    from RQs.RQ3_3.src.utils import OfflineTokens
    from vlmrca.run_state import atomic_write

    if _TOKENS is None:
        _TOKENS = OfflineTokens(runtime_config(config))
    root = ROOT / config["implementation"]["output_root"]
    row = targets[0]["case"]
    oid = row["opaque_incident_id"]
    # A frozen small per-case compiler cache is shared across arms and models.
    cache_tag = digest(registration["contract"])
    cache = root / "public_cache" / cache_tag / (oid + ".pkl")
    from .utils import measurement_definitions

    definitions = measurement_definitions(config)
    parent = read_json(ROOT / config["implementation"]["parent_config"])
    context = None
    if cache.exists():
        stored = pickle.loads(cache.read_bytes())
        view = stored["view"]
    else:
        context = source_context(config, row, _TOKENS)
        view = exps.make_view(context, parent, _TOKENS, definitions)
        # Certify the scientific anchor using the stored public T input only.
        reference = next(
            (
                registration["bridges"].get(digest([m, oid, "B3_T_REF"]))
                for m in config["models"]
                if registration["bridges"].get(digest([m, oid, "B3_T_REF"]))
            ),
            None,
        )
        if reference:
            old_parts, old_prompt = bridge_parts(reference)
            new_parts = [{"type": "text", "text": p["text"]} for p in view.parts]
            if new_parts != old_parts or old_prompt["system"] != view.system:
                raise ValueError(
                    "Reconstructed ALL_ID public anchor differs from saved B3_T; diagnose before inference"
                )
        atomic_write(cache, pickle.dumps({"view": view}, protocol=5))
    geometry, geometry_error = None, None
    if any(t["dimensions"]["arm"] in exps.VISUAL for t in targets):
        try:
            geometry = exps.scene(view, definitions, config["visual"])
        except DesignInfeasible as exc:
            geometry_error = str(exc)
    compiled = []
    request_cache = {}
    for task in targets:
        arm, encoding = task["dimensions"]["arm"], task["dimensions"]["encoding"]
        mode = "NATIVE" if encoding == "REPEAT" else encoding
        archive_only = reference_only(task, config)
        try:
            entry = registration["bridges"].get(digest([task["model"], oid, arm]))
            if archive_only and not entry:
                compiled.append(
                    (
                        task,
                        {
                            "reference_unavailable": "No completed historical reference; generation prohibited"
                        },
                    )
                )
                continue
            if entry:
                parts, prompt = bridge_parts(entry)
                system = prompt["system"]
                audit = {"arm": arm, "bridge": entry, "unchanged_original_input": True}
            elif arm.endswith("_REF"):
                context = context or source_context(config, row, _TOKENS)
                parts, system = reference_input(context, arm, parent, _TOKENS)
                audit = {"arm": arm, "bridge": None, "unchanged_parent_recipe": True}
            else:
                if arm in exps.VISUAL and geometry_error:
                    raise DesignInfeasible(geometry_error)
                key = (arm, mode)
                if key not in request_cache:
                    request_cache[key] = exps.parts_for(
                        view, definitions, config["visual"], arm, mode, geometry
                    )
                parts, audit = request_cache[key]
                system = view.system
            request = exps.compile_request(
                task, parts, view.candidates, system, audit, _TOKENS
            )
            if entry:
                previous = request_descriptor(
                    parts, prompt["system"], prompt, task["model"]
                )
                # Runtime, schema, complete input and original scorer must match.
                previous_reg = read_json(entry["registration"])
                scoring = [
                    p
                    for p in registration["contract"]
                    if "scor" in p and p.endswith((".py", ".yaml"))
                ]
                scoring_compatible = all(
                    previous_reg["contract"].get(p) == registration["contract"][p]
                    for p in scoring
                )
                if digest(previous) == request["input_identity"] and scoring_compatible:
                    request["bridge_reuse"] = entry
            if archive_only and not request.get("bridge_reuse"):
                compiled.append(
                    (
                        task,
                        {
                            "reference_unavailable": "Historical request/scorer incompatible; generation prohibited"
                        },
                    )
                )
                continue
            # Native B/C inputs share A's formal response; REPEAT has a different key.
            compiled.append((task, request))
        except DesignInfeasible as exc:
            field = "reference_unavailable" if archive_only else "design_infeasible"
            compiled.append((task, {field: str(exc)}))
        except FileNotFoundError as exc:
            if not archive_only:
                raise
            compiled.append(
                (task, {"reference_unavailable": f"Missing historical artifact: {exc}"})
            )
    return compiled


def reuse_identity(task, request):
    return digest(
        [
            task["model"],
            task["case"]["opaque_incident_id"],
            request["input_identity"],
            task["ledger_scope"],
            task["dimensions"]["replicate"],
        ]
    )


def execute(task, request, config, root):
    """Terminal flags commit after raw/prompt/image/conversation/score persistence."""
    import fcntl

    from RQs.RQ3_1.src.main import run_registered_call, score_response_callback
    from RQs.RQ3_3.src.main import timeout_exception
    from vlmrca.run_state import DurableCallRegister

    prior = terminal_flag(root, task)
    if prior:
        return prior
    flag_path = root / "flags" / (task["logical_key"] + ".json")
    common = {
        "logical_key": task["logical_key"],
        "dimensions": task["dimensions"],
        "model": task["model"],
        "case": task["case"]["opaque_incident_id"],
        "experiment": task["experiment_id"],
    }
    if "reference_unavailable" in request or (
        reference_only(task, config) and not request.get("bridge_reuse")
    ):
        value = {
            **common,
            "status": "fail",
            "failure_class": "reference_unavailable",
            "reason": request.get(
                "reference_unavailable",
                "Reference-only target has no compatible reuse; generation prohibited",
            ),
            "new_generation_calls": 0,
            "auto_retry": False,
        }
        # Not a model error or a zero-scored design: preserve missing metrics.
        save_json(flag_path, value)
        return value
    if "design_infeasible" in request:
        value = {
            **common,
            "status": "fail",
            "failure_class": "design_infeasible",
            "reason": request["design_infeasible"],
            "metrics": ZERO,
            "new_generation_calls": 0,
        }
        save_json(flag_path, value)
        return value
    destination = root / "stages" / task["stage"] / task["model"]
    key = request["task"]["call_key"]
    reuse = reuse_identity(task, request)
    index = root / "reuse" / (reuse + ".json")
    index.parent.mkdir(parents=True, exist_ok=True)
    projection_path = destination / "projections" / (key + ".json")
    save_json(projection_path, request["projection"])
    with index.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if index.exists():
            value = read_json(index)
            result = {
                **value,
                **common,
                "reused_from": value["logical_key"],
                "new_generation_calls": 0,
                "projection_path": str(projection_path),
            }
            save_json(flag_path, result)
            return result
        entry = request.get("bridge_reuse")
        if entry:
            artifact_root, artifact_key = ROOT / entry["root"], entry["call_key"]
            result = read_json(artifact_root / "outputs" / (artifact_key + ".json"))
            cost = read_json(artifact_root / "cost" / (artifact_key + ".json"))
        else:
            artifact_root, artifact_key = destination, key
            private = private_for(config, root, task["case"])
            ledger = DurableCallRegister(
                root / "calls.sqlite",
                limit=40000,
                scope=task["ledger_scope"],
                scope_limit=18 if task["stage"].startswith("smoke_") else None,
            )
            save_json(
                root / "activity" / (task["model"] + ".json"),
                {"state": "submitting_request", "unix": time.time(), "key": key},
            )
            try:
                result = run_registered_call(
                    request["task"],
                    request["parts"],
                    request["envelope"],
                    destination,
                    score_response=score_response_callback(
                        private, request["candidates"]
                    ),
                    ledger=ledger,
                )
                cost = read_json(destination / "cost" / (key + ".json"))
            except Exception as exc:
                timeout = timeout_exception(exc)
                result = {
                    **common,
                    "status": "fail",
                    "call_key": key,
                    "artifact_root": str(destination),
                    "failure_class": "request_timeout" if timeout else "infrastructure",
                    "error": f"{type(exc).__name__}: {exc}",
                    "auto_retry": False,
                }
                save_json(flag_path, result)
                if timeout:
                    save_json(index, result)
                if not timeout:
                    raise
                return result
        metrics = result["score"].get("metrics") or result["score"]
        value = {
            **common,
            "status": "done",
            "call_key": artifact_key,
            "artifact_root": str(artifact_root),
            "input_identity": request["input_identity"],
            "projection_path": str(destination / "projections" / (key + ".json")),
            "model_status": result["status"],
            "metrics": {k: metrics[k] for k in METRICS},
            **{
                k: cost.get(k)
                for k in (
                    "input_tokens",
                    "output_tokens",
                    "text_tokens",
                    "image_tokens",
                    "wall_time_s",
                )
            },
            "new_generation_calls": 0 if entry else cost.get("new_generation_calls", 1),
        }
        if entry:
            value["reused_from"] = entry
        save_json(index, value)
        save_json(flag_path, value)
        return value


def run(config, registration, root, experiment, model, smoke=False):
    from RQs.RQ3_3.src.main import exclusive, interleaved_sources
    from RQs.RQ3_6.src.main import close_pool, cpu_pool
    from RQs.RQ3_6.src.utils import interrupted_calls

    if model not in config["models"]:
        raise ValueError("Run exactly one registered model per process")
    gates.authorize(config, registration, root, experiment, smoke)
    targets = gates.tasks(config, registration, experiment, model=model, smoke=smoke)
    pending = [t for t in targets if terminal_flag(root, t) is None]
    if not pending:
        return {"state": "complete", "remaining": 0}
    stop = threading.Event()
    handlers = {
        s: signal.signal(s, lambda *_: stop.set())
        for s in (signal.SIGINT, signal.SIGTERM)
    }
    pool = core_queue = executor = None
    abort = False
    progress = root / "progress" / f"{experiment}_{model}.json"
    try:
        with exclusive(root / "run.lock"):
            interrupted_calls(root, pending[0]["ledger_scope"])
            grouped = defaultdict(list)
            for task in pending:
                grouped[task["case"]["opaque_incident_id"]].append(task)
            ordered = interleaved_sources(
                [items[0]["case"] for items in grouped.values()]
            )
            pool, core_queue, workers = cpu_pool(
                min(config["execution"]["workers"], len(ordered))
            )
            executor = cf.ThreadPoolExecutor(config["execution"]["concurrency"])
            rows = iter(ordered)
            preparing, calls = {}, set()
            finished = len(targets) - len(pending)
            completed = [
                f for t in targets if (f := terminal_flag(root, t)) is not None
            ]
            next_report = min(100, 5 * (int(100 * finished / len(targets)) // 5 + 1))
            while True:
                if (
                    shutil.disk_usage(root).free
                    < config["execution"]["min_free_disk_gib"] * 1024**3
                ):
                    raise OSError("Low disk; stop new submissions, drain requests")
                while (
                    not stop.is_set()
                    and len(preparing)
                    < min(workers, config["execution"]["prefetch_cases"])
                    and len(calls) < config["execution"]["concurrency"]
                ):
                    row = next(rows, None)
                    if row is None:
                        break
                    future = pool.submit(
                        compile_case,
                        (config, registration, grouped[row["opaque_incident_id"]]),
                    )
                    preparing[future] = row
                if not preparing and not calls:
                    break
                done, _ = cf.wait(
                    set(preparing) | calls, timeout=1, return_when=cf.FIRST_COMPLETED
                )
                for future in done:
                    if future in preparing:
                        del preparing[future]
                        compiled = future.result()
                        if not stop.is_set():
                            for task, request in compiled:
                                calls.add(
                                    executor.submit(
                                        execute, task, request, config, root
                                    )
                                )
                    else:
                        calls.remove(future)
                        completed.append(future.result())
                        finished += 1
                if done:
                    save_json(
                        progress,
                        {
                            "state": "draining" if stop.is_set() else "running",
                            "total": len(targets),
                            "terminal": finished,
                            "preparing": len(preparing),
                            "active_or_queued": len(calls),
                            "updated_unix": time.time(),
                        },
                    )
                if 100 * finished / len(targets) >= next_report:
                    scored = [f for f in completed if "metrics" in f]
                    print(
                        json.dumps(
                            {
                                "terminal": finished,
                                "total": len(targets),
                                "percent": next_report,
                                "metrics": {
                                    k: sum(f["metrics"][k] for f in scored)
                                    / len(scored)
                                    if scored
                                    else None
                                    for k in METRICS
                                },
                                "infra_missing": sum(
                                    "metrics" not in f for f in completed
                                ),
                            }
                        ),
                        flush=True,
                    )
                    next_report += 5
            state = "paused" if stop.is_set() else "complete"
            save_json(
                progress,
                {
                    "state": state,
                    "total": len(targets),
                    "terminal": finished,
                    "updated_unix": time.time(),
                },
            )
            if stop.is_set():
                raise InterruptedError("User pause; terminal units retained")
            return {"state": state, "total": len(targets), "terminal": finished}
    except BaseException:
        abort = True
        raise
    finally:
        if pool:
            close_pool(pool, core_queue, abort=abort)
        if executor:
            executor.shutdown(wait=True, cancel_futures=abort)
        for sig, handler in handlers.items():
            signal.signal(sig, handler)


def launch_model(config, registration, root, experiment, model, deadline, smoke=False):
    """Owned process groups only; separate ready/submitting records."""
    from unified_scripts.vllm_inference import VLLMInferenceConfig

    runtime = VLLMInferenceConfig.load(ROOT / config["unified"]["inference"])
    spec = runtime.model(model)
    if not endpoint_vacant(spec):
        raise RuntimeError("Existing server untouched; cannot claim ownership")
    if spec["request_timeout_sec"] != 300:
        raise ValueError("Frozen timeout must be 300 seconds")
    processes, handles = [], []
    try:
        for kind in ("server", "runner"):
            if time.time() >= deadline:
                raise TimeoutError("No process starts after the smoke deadline")
            path = root / "logs" / f"{experiment}_{model}_{kind}.log"
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = path.open("ab")
            handles.append(handle)
            argv = (
                ["bash", "scripts/vllm_vlm/serve_canvasrca_local.sh", model]
                if kind == "server"
                else [
                    sys.executable,
                    "-m",
                    MODULE,
                    "run",
                    "--experiment",
                    experiment,
                    "--model",
                    model,
                ]
                + (["--smoke"] if smoke else [])
            )
            process = subprocess.Popen(
                argv,
                cwd=ROOT,
                stdout=handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            processes.append(process)
            if kind == "server":
                start = time.monotonic()
                while not model_probe(spec):
                    if process.poll() is not None:
                        raise RuntimeError("Server exited during startup")
                    if time.time() >= deadline:
                        raise TimeoutError("Logical qualification deadline")
                    if time.monotonic() - start > spec["wait_timeout_sec"]:
                        raise RuntimeError("Server readiness infrastructure timeout")
                    time.sleep(2)
                save_json(
                    root / "activity" / (model + "_ready.json"),
                    {
                        "state": "server_ready",
                        "unix": time.time(),
                        "effective": spec,
                        "experiment": experiment,
                    },
                )
            else:
                code = process.wait(timeout=max(0.01, deadline - time.time()))
                if code:
                    raise RuntimeError(f"Runner exited with {code}")
    finally:
        for process in reversed(processes):
            stop_owned(process)
        for handle in handles:
            handle.close()


def supervise(config, registration, root, experiments, smoke=False):
    supervisor_started = time.time()
    from RQs.RQ3_3.src.main import exclusive

    from .tests import review

    if smoke and len(experiments) != 1:
        raise ValueError("One invocation is one complete logical smoke")
    if os.environ.get("CANVASRCA_VLLM_CONFIG") != str(
        ROOT / config["unified"]["inference"]
    ):
        raise ValueError("Source scripts/env_local.sh before running")

    def interrupt(*_):
        raise InterruptedError("Supervisor paused; stop only owned children")

    old = {s: signal.signal(s, interrupt) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        with exclusive(root / "queue.lock"):
            for experiment in experiments:
                if not smoke:
                    gates.authorize(config, registration, root, experiment)
                else:
                    cpu = read_json(root / "cpu_qualification.json")
                    if cpu["status"] != "passed" or cpu["contract_hash"] != digest(
                        registration["contract"]
                    ):
                        raise ValueError("Current CPU qualification required")
                started = supervisor_started if smoke else time.time()
                deadline = started + 600 if smoke else started + 365 * 86400
                report = {
                    "status": "passed",
                    "contract_hash": digest(registration["contract"]),
                    "started_unix": started,
                    "models_finished": [],
                }
                marker = root / "smokes" / (experiment + "_started.json")
                if smoke:
                    marker.parent.mkdir(parents=True, exist_ok=True)
                    if marker.exists():
                        original = read_json(marker)
                        if original["contract_hash"] != report["contract_hash"]:
                            repair = read_json(root / "smokes" / (experiment + "_repair.json"))
                            if (repair.get("previous_contract_hash") != original["contract_hash"]
                                or repair.get("contract_hash") != report["contract_hash"]
                                or not repair.get("reason")):
                                raise ValueError("Smoke repair needs explicit source-change provenance")
                        # One logical smoke: neither repair nor process restart
                        # resets its original wall-clock or SQLite call budget.
                        started, deadline = original["started_unix"], original["deadline_unix"]
                        if time.time() >= deadline:
                            raise ValueError("Logical smoke window exhausted; do not reset it")
                        report.update(started_unix=started, resumed_within_original_window=True)
                    else:
                        with marker.open("x") as f:
                            json.dump({**report, "deadline_unix": deadline}, f)
                save_json(
                    root / "queue_status.json",
                    {"state": "running", "experiment": experiment, "smoke": smoke},
                )
                try:
                    for model in config["models"]:
                        targets = gates.tasks(
                            config, registration, experiment, model=model, smoke=smoke
                        )
                        if any(terminal_flag(root, t) is None for t in targets):
                            launch_model(
                                config,
                                registration,
                                root,
                                experiment,
                                model,
                                deadline,
                                smoke,
                            )
                        report["models_finished"].append(model)
                    if smoke:
                        report["review"] = review(
                            config, registration, root, experiment
                        )
                        if time.time() >= deadline:
                            report["status"] = "bounded_timeout_only"
                            report["post_deadline_read_only_review"] = True
                except (TimeoutError, subprocess.TimeoutExpired):
                    report["status"] = "bounded_timeout_only" if smoke else "failed"
                except BaseException as exc:
                    report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
                    raise
                finally:
                    report["elapsed_s"] = time.time() - started
                    if smoke:
                        report["initiated_calls"] = call_count(
                            root, "rq37_smoke_" + experiment
                        )
                        if report["initiated_calls"] > 18:
                            report["status"] = "failed"
                        # Read saved failure records even if the bounded window expired.
                        report["review"] = review(
                            config, registration, root, experiment
                        )
                        if report["review"]["errors"]:
                            report["status"] = "failed"
                        save_json(root / "smokes" / (experiment + ".json"), report)
                    save_json(
                        root / "queue_status.json",
                        {
                            "state": report["status"],
                            "experiment": experiment,
                            "smoke": smoke,
                        },
                    )
                if report["status"] == "failed":
                    raise RuntimeError(
                        "Qualification or queue failed; no automatic repair calls"
                    )
    finally:
        for sig, handler in old.items():
            signal.signal(sig, handler)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "action",
        choices=("register", "cpu", "smoke", "run", "queue", "analyze", "review"),
    )
    p.add_argument("--experiment", choices=("A", "B", "C"), default="A")
    p.add_argument(
        "--experiments", nargs="+", choices=("A", "B", "C"), default=["A", "B"]
    )
    p.add_argument("--model")
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    config = load_config()
    root = ROOT / config["implementation"]["output_root"]
    root.mkdir(parents=True, exist_ok=True)
    registration = (
        gates.register(config, root)
        if args.action == "register"
        else read_json(root / "registration.json")
    )
    gates.assert_current(config, registration)
    if args.action == "register":
        from RQs.RQ3_6.src.utils import ensure_shared_ledger

        if not (ROOT / config["implementation"]["shared_ledger"]).is_file():
            raise ValueError(
                "Historical shared ledger missing; must not restart budget at zero"
            )
        ensure_shared_ledger(config, root)
        prior = call_count(root)
        if prior < config["budget"]["historical_expected_at_design"]:
            raise ValueError("Historical cumulative spend is unexpectedly smaller")
        if not (root / "budget_at_registration.json").exists() and (
            prior + config["budget"]["planned_new_upper"]
            > config["budget"]["hard_limit"]
        ):
            raise ValueError(
                "Actual cumulative count cannot accommodate registered upper bound"
            )
        if not (root / "budget_at_registration.json").exists():
            save_json(
                root / "budget_at_registration.json",
                {
                    "cumulative_calls": prior,
                    "shared_ledger": config["implementation"]["shared_ledger"],
                    "new_upper": config["budget"]["planned_new_upper"],
                },
            )
        result = {
            "registered": True,
            "historical_calls": prior,
            "new_upper": config["budget"]["planned_new_upper"],
        }
    elif args.action == "cpu":
        from .tests import cpu_qualification

        result = cpu_qualification(config, registration, root)
    elif args.action == "run":
        result = run(
            config, registration, root, args.experiment, args.model, args.smoke
        )
    elif args.action == "smoke":
        result = supervise(config, registration, root, [args.experiment], smoke=True)
    elif args.action == "queue":
        result = supervise(config, registration, root, args.experiments)
    elif args.action == "review":
        from .tests import review

        result = review(config, registration, root, args.experiment)
    else:
        result = gates.analyze(config, registration, root)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

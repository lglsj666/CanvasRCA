"""Explicit preparation, bounded qualification and resumable one-shot execution."""

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import pickle
import signal
import subprocess
import sys
import threading
import time
from contextlib import ExitStack
from pathlib import Path

from . import exps, gates
from .utils import (
    CONFIG,
    ROOT,
    VERSION,
    digest,
    instance_states,
    load_config,
    public_source,
    read_json,
    runtime_config,
    save_json,
)


class ContextCapacityError(ValueError):
    """Explicit non-model failure; never truncate evidence or score as zero."""

    def __init__(self, task, counts, limits):
        self.details = {
            "case": task["case"]["opaque_incident_id"],
            "arm": task["dimensions"]["arm"],
            "model_input_tokens": counts,
            "input_limits": limits,
        }
        super().__init__(
            "Registered intact input exceeds context: " + json.dumps(self.details)
        )


def terminal_flag(root, task):
    """Read one tiny commit marker, never rebuild a completed request."""
    path = root / "flags" / (task["logical_key"] + ".json")
    if not path.exists():
        return None
    flag = read_json(path)
    if flag["status"] not in {"done", "fail"}:
        raise ValueError("Unexpected formal unit status")
    if flag["status"] == "fail" and flag.get("failure_class") != "request_timeout":
        raise ValueError(
            "Infrastructure failure requires diagnosis, not automatic skip"
        )
    return flag


def load_context(root, row):
    name = row["opaque_incident_id"]
    if read_json(root / "preparation_flags" / (name + ".json"))["status"] != "done":
        raise ValueError("Preparation is not committed")
    with (root / "contexts" / (name + ".pkl")).open("rb") as stream:
        context = pickle.load(stream)
    return context, read_json(root / "private" / (name + ".json"))


def prepare_case(args):
    from RQs.RQ3_3.src.utils import OfflineTokens, prepare_public_context
    from RQs.RQ3_4.src.exps import prepare_integrated
    from RQs.RQ3_4.src.main import load_integrated_context
    from RQs.RQ3_4.src.utils import metric_selection_metadata
    from vlmrca.run_state import atomic_write

    row, config, output = args
    root, opaque = Path(output), row["opaque_incident_id"]
    flag = root / "preparation_flags" / (opaque + ".json")
    if flag.exists():
        return read_json(flag)
    started = time.monotonic()
    try:
        parent = ROOT / config["implementation"]["source_run"]
        cached = (parent / "preparation_flags" / (opaque + ".json")).exists()
        tokens = OfflineTokens(runtime_config(config))
        if cached:
            context, private = load_integrated_context(parent, row)
        else:
            context, private = prepare_public_context(row, runtime_config(config))
            from RQs.RQ3_3.src.exps import prepare_selections

            context["selections"] = prepare_selections(
                context, tokens, runtime_config(config)
            )
            oldconfig = read_json(ROOT / "RQs/RQ3_4/configs/integrated_round_v1.json")
            context["selection_metadata"] = metric_selection_metadata(
                context, row, oldconfig
            )
            context["integrated"] = prepare_integrated(context, tokens, oldconfig)
        inherited = time.monotonic()
        # Only natural identity mapping crosses this adapter, never labels.
        mapping = {v: k for k, v in private["numeric_to_natural"].items()}
        source = public_source(row, mapping, context["window"])
        request, audit = exps.request_packs(source, context["window"], config)
        states = instance_states(row, context["observations"], context["window"])
        scope = exps.scope_packs(source["ownership"], states, context["window"], config)
        selected, rejected = exps.choose_packs(request + scope, context, tokens, config)
        context["ole"] = {
            "version": VERSION,
            "selected": selected,
            "rejected": rejected,
            "pool_count": len(request) + len(scope),
            "source_audit": source["audit"],
            "request_audit": audit,
            "request_packs": len(request),
            "scope_packs": len(scope),
        }
        atomic_write(
            root / "contexts" / (opaque + ".pkl"), pickle.dumps(context, protocol=5)
        )
        save_json(root / "private" / (opaque + ".json"), private)
        save_json(root / "pool_audits" / (opaque + ".json"), context["ole"])
        value = {
            "status": "done",
            "opaque_incident_id": opaque,
            "elapsed_s": time.monotonic() - started,
            "inherited_s": inherited - started,
            "new_index_s": time.monotonic() - inherited,
            "reused_parent": cached,
            "selected": len(selected),
            "request_packs": len(request),
            "scope_packs": len(scope),
            "affinity": sorted(os.sched_getaffinity(0)),
        }
        save_json(flag, value)
        return value
    except Exception as exc:
        save_json(
            flag,
            {
                "status": "fail",
                "error": f"{type(exc).__name__}: {exc}",
                "auto_retry": False,
            },
        )
        raise


def prepare(config, registration, root, rows):
    import multiprocessing as mp

    from RQs.RQ3_3.src.main import exclusive, interleaved_sources
    from vlmrca.run_state import physical_cpu_ids, pin_process_to_core

    pending = [
        r
        for r in interleaved_sources(rows)
        if not (
            root / "preparation_flags" / (r["opaque_incident_id"] + ".json")
        ).exists()
    ]
    with exclusive(root / "prepare.lock"):
        if pending:
            ctx = mp.get_context("spawn")
            queue = ctx.Queue()
            cores = physical_cpu_ids()[: min(8, len(pending))]
            for core in cores:
                queue.put(core)
            pool = cf.ProcessPoolExecutor(
                len(cores),
                mp_context=ctx,
                initializer=pin_process_to_core,
                initargs=(queue,),
            )
            try:
                futures = [
                    pool.submit(prepare_case, (r, config, str(root))) for r in pending
                ]
                for future in cf.as_completed(futures):
                    print(json.dumps(future.result()), flush=True)
            except BaseException:
                processes = list(pool._processes.values())
                pool.shutdown(wait=False, cancel_futures=True)
                for p in processes:
                    if p.is_alive():
                        p.terminate()
                for p in processes:
                    p.join(timeout=2)
                    if p.is_alive():
                        p.kill()
                raise
            else:
                pool.shutdown(wait=True)
            finally:
                queue.close()
                queue.join_thread()
    flags = [
        read_json(root / "preparation_flags" / (r["opaque_incident_id"] + ".json"))
        for r in rows
    ]
    if any(f["status"] != "done" for f in flags):
        raise ValueError("Preparation failure is terminal; explicit repair required")
    return flags


def compile_unit(task, context, private, config, tokens, root):
    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    from RQs.RQ3_1.src.main import _request_envelope, bind_task_request
    from RQs.RQ3_3.src.exps import g_ledger, request_descriptor
    from unified_scripts import stable_hash
    from vlmrca.run_state import atomic_write

    arm = task["dimensions"]["arm"]
    mapping = {}
    if arm == "REANONYMIZE":
        path = root / "reanonymous" / (task["case"]["opaque_incident_id"] + ".pkl")
        if path.exists():
            with path.open("rb") as stream:
                context, private, mapping = pickle.load(stream)
        else:
            context, private, mapping = exps.reanonymize(
                context, private, task["case"], runtime_config(config)
            )
            atomic_write(path, pickle.dumps((context, private, mapping), protocol=5))
    parts, drawing = exps.parts_for(context, arm, config)
    exps.assert_safe_clocks(parts)
    system = context["sircl_system"] if arm == "SIRCL_IDS_NATIVE" else RCA_SYSTEM_ROLE
    fits, counts = tokens.fits(parts, system)
    if not fits:
        raise ContextCapacityError(
            task,
            counts,
            {
                m: tokens.runtime.model(m)["max_model_len"]
                - tokens.config["request"]["max_tokens"]
                for m in counts
            },
        )
    if sum(p["type"] == "image" for p in parts) > 1:
        raise ValueError("More than one image")
    envelope = _request_envelope(task["model"], system=system)
    envelope["policy_version"] = VERSION
    if envelope["effective_server"]["max_tokens"] != 8192:
        raise ValueError("Context-safe inherited output adapter changed")
    actual = request_descriptor(parts, system, envelope, task["model"])
    projection = {
        "schema_version": "RQ35ProjectionV1",
        "arm": arm,
        "model_token_counts": counts,
        "selected_packs": context["ole"]["selected"],
        "no_op": not context["ole"]["selected"],
        "source_audit": context["ole"]["source_audit"],
        "drawing": drawing,
        "id_mapping": mapping,
        "image_hashes": [
            hashlib.sha256(p["png"]).hexdigest() for p in parts if p["type"] == "image"
        ],
    }
    # Independent replicate identity is metadata, not a prompt/seed modification.
    replicate = arm if arm.startswith("REPEAT_") else None
    bound = bind_task_request(
        task,
        actual,
        stable_hash(projection),
        projection=projection,
        adapter_version=VERSION,
        version=VERSION,
    )
    return {
        "parts": parts,
        "envelope": envelope,
        "task": bound,
        "actual": actual,
        "input_identity": digest([actual, replicate]) if replicate else digest(actual),
        "projection": projection,
        "private": private,
        "candidates": context["candidates"],
        "g_ledger": g_ledger(context["prepared"].public["packet"])
        + (
            "\n"
            + exps.pack_text(
                context["ole"]["selected"], "joint" if arm == "NO_DERIVED" else "cond"
            )
            if drawing.get("joint_records")
            else ""
        ),
    }


def run(
    config,
    registration,
    root,
    experiment,
    model,
    smoke=False,
    phase="screen",
    candidate_repair=False,
    block_repair=False,
    gc_repair=False,
):
    from RQs.RQ3_3.src.main import exclusive
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_4.src.main import execute_integrated

    if model not in config["models"]:
        raise ValueError("Run exactly one registered model per process")
    if not smoke:
        authority = root / "formal_authorization.json"
        permitted = read_json(authority) if authority.exists() else {}
        if permitted.get("contract_hash") != digest(registration["contract"]) or [
            experiment,
            phase,
        ] not in permitted.get("authorized_stages", []):
            raise ValueError(
                "Only qualification authorized; no formal stage authorization"
            )
        qualification = read_json(root / "qualification" / (experiment + ".json"))
        if (
            qualification["status"] != "passed"
            or qualification["contract_hash"] != permitted["contract_hash"]
        ):
            raise ValueError("Current bounded qualification required")
    tasks = gates.tasks(config, registration, root, experiment, model, smoke, phase)
    policy = None
    if sum((candidate_repair, block_repair, gc_repair)) > 1:
        raise ValueError("Select only one repair supplement")
    if candidate_repair or block_repair or gc_repair:
        if not smoke:
            raise ValueError("Repair is qualification only")
        policy_fn = (
            gates.gc_repair_policy
            if gc_repair
            else gates.block_repair_policy
            if block_repair
            else gates.candidate_repair_policy
        )
        tasks_fn = (
            gates.gc_repair_tasks
            if gc_repair
            else gates.block_repair_tasks
            if block_repair
            else gates.candidate_repair_tasks
        )
        policy = policy_fn(root, registration, experiment)
        tasks = tasks_fn(config, registration, root, model)
    with exclusive(root / "run.lock"), ExitStack() as overrides:
        if policy:
            from unittest.mock import patch

            from RQs.RQ3_4.src import main as inherited

            def scoped_policy(target, stage, repair=False):
                if target != root or stage != experiment or repair:
                    raise ValueError("Repair capacity is restricted to this A process")
                return policy

            # Process-local operational adapter. It never edits the inherited
            # executor or changes model input, scoring, reuse or persistence.
            overrides.enter_context(
                patch.object(inherited, "smoke_policy", scoped_policy)
            )
        pending = [t for t in tasks if terminal_flag(root, t) is None]
        if not pending:
            return {"status": "already_terminal", "units": len(tasks)}
        from vlmrca.run_state import DurableCallRegister

        ledger = DurableCallRegister(
            root / "calls.sqlite", limit=40000, scope=pending[0]["ledger_scope"]
        )
        with ledger.connect() as db:
            prefix = pending[0]["ledger_scope"] + "/"
            db.execute(
                "UPDATE calls SET state='interrupted',result=? WHERE state='started' AND substr(call_key,1,?)=?",
                (
                    json.dumps(
                        {"reason": "previous exclusive owner exited before commit"}
                    ),
                    len(prefix),
                    prefix,
                ),
            )
        tokens = OfflineTokens(runtime_config(config))
        stop = threading.Event()
        previous = {
            s: signal.signal(s, lambda *_: stop.set())
            for s in (signal.SIGTERM, signal.SIGINT)
        }
        pool, inflight = cf.ThreadPoolExecutor(max_workers=36), {}
        current, completed, fatal = None, len(tasks) - len(pending), None
        try:
            for task in pending:
                if stop.is_set():
                    break
                while len(inflight) >= 36:
                    done, _ = cf.wait(inflight, return_when=cf.FIRST_COMPLETED)
                    for future in done:
                        future.result()
                        inflight.pop(future)
                        completed += 1
                if stop.is_set():
                    break
                opaque = task["case"]["opaque_incident_id"]
                if current != opaque:
                    context, private = load_context(root, task["case"])
                    current = opaque
                request = compile_unit(task, context, private, config, tokens, root)
                inflight[
                    pool.submit(execute_integrated, task, request, config, root)
                ] = task
                for future in [f for f in inflight if f.done()]:
                    future.result()
                    inflight.pop(future)
                    completed += 1
                print(
                    f"{experiment} {model} terminal={completed}/{len(tasks)} in_flight={len(inflight)}",
                    flush=True,
                )
            for future in cf.as_completed(inflight):
                future.result()
                completed += 1
        except BaseException as exc:  # noqa: BLE001 -- drain owned writes, then re-raise
            fatal = exc
            stop.set()
            for future in inflight:
                future.cancel()
        finally:
            pool.shutdown(wait=True, cancel_futures=True)
            for s, handler in previous.items():
                signal.signal(s, handler)
            save_json(
                root / "progress" / (tasks[0]["stage"] + "_" + model + ".json"),
                {
                    "planned": len(tasks),
                    "terminal": sum(
                        (root / "flags" / (t["logical_key"] + ".json")).exists()
                        for t in tasks
                    ),
                    "paused": stop.is_set(),
                    "fatal": str(fatal) if fatal else None,
                },
            )
        if fatal:
            raise fatal
        return {"status": "paused" if stop.is_set() else "complete", "units": completed}


def smoke(
    config,
    registration,
    root,
    experiment,
    candidate_repair=False,
    block_repair=False,
    gc_repair=False,
):
    import urllib.error
    import urllib.request

    from unified_scripts.vllm_inference import VLLMInferenceConfig
    from vlmrca.run_state import DurableCallRegister

    cpu = read_json(root / "cpu_qualification.json")
    if cpu["status"] != "passed" or cpu["contract_hash"] != digest(
        registration["contract"]
    ):
        raise ValueError("Current CPU qualification required")
    if contract_changed(config, registration):
        raise ValueError("Source changed since CPU qualification")
    destination = root / "smokes" / (experiment + ".json")
    marker = root / "smokes" / (experiment + "_started.json")
    policy = {"scope_limit": 18, "previous_calls": 0}
    if sum((candidate_repair, block_repair, gc_repair)) > 1:
        raise ValueError("Select only one repair supplement")
    repair_tasks = (
        gates.gc_repair_tasks
        if gc_repair
        else gates.block_repair_tasks
        if block_repair
        else gates.candidate_repair_tasks
    )
    if candidate_repair or block_repair or gc_repair:
        policy_fn = (
            gates.gc_repair_policy
            if gc_repair
            else gates.block_repair_policy
            if block_repair
            else gates.candidate_repair_policy
        )
        policy = policy_fn(root, registration, experiment)
        destination = (
            root
            / "repairs"
            / (
                "gc_clock_v1"
                if gc_repair
                else "lossless_blocks_v3"
                if block_repair
                else "candidate_once_v2"
            )
            / "report.json"
        )
        marker = destination.with_name("started.json")
        ledger = DurableCallRegister(root / "calls.sqlite", limit=40000)
        prefix = "rq35_smoke:" + experiment + "/"
        with ledger.connect() as db:
            count = db.execute(
                "SELECT count(*) FROM calls WHERE substr(call_key,1,?)=?",
                (len(prefix), prefix),
            ).fetchone()[0]
        if count != policy["previous_calls"]:
            raise ValueError("Repair may not reset or repeat already spent calls")
    if destination.exists() or marker.exists():
        raise ValueError("Logical smoke already initiated; no fresh call/time budget")
    marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.open("x") as stream:
        json.dump(
            {
                "started_unix": time.time(),
                "max_calls": policy["scope_limit"] - policy["previous_calls"],
                "max_seconds": 600,
            },
            stream,
        )
    runtime = VLLMInferenceConfig.load(ROOT / config["unified"]["inference"])
    started, processes, handles = time.monotonic(), [], []
    report = {"status": "complete", "contract_hash": digest(registration["contract"])}
    report["candidate_repair"] = candidate_repair
    report["block_repair"] = block_repair
    report["gc_repair"] = gc_repair
    log_root = destination.parent

    def cleanup():
        for p in reversed(processes):
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait(timeout=5)
        processes.clear()

    def alarm(*_):
        raise TimeoutError("600-second aggregate smoke deadline")

    old = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, 600)
    try:
        for model in config["models"]:
            model_spec = runtime.model(model)
            request = urllib.request.Request(
                model_spec["base_url"].rstrip("/") + "/models",
                headers={
                    "Authorization": "Bearer " + os.environ.get("VLLM_API_KEY", "EMPTY")
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=2):
                    pass
            except urllib.error.URLError as exc:
                if not isinstance(exc.reason, ConnectionRefusedError):
                    raise RuntimeError("Cannot establish endpoint ownership") from exc  # noqa: TRY004
            else:
                raise RuntimeError("Existing server left untouched")
            log = (log_root / (experiment + "_" + model + "_server.log")).open("ab")
            handles.append(log)
            server = subprocess.Popen(
                ["bash", "scripts/vllm_vlm/serve_canvasrca_local.sh", model],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            processes.append(server)
            while True:
                if server.poll() is not None:
                    raise RuntimeError("Canonical server exited; inspect log")
                try:
                    with urllib.request.urlopen(request, timeout=2) as response:
                        names = [x["id"] for x in json.load(response)["data"]]
                    if names != [model_spec["served_model_name"]]:
                        raise RuntimeError("Wrong served model")
                    break
                except urllib.error.URLError:
                    time.sleep(5)
            log = (log_root / (experiment + "_" + model + "_runner.log")).open("ab")
            handles.append(log)
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "RQs.RQ3_5.src.main",
                    "run",
                    "--experiment",
                    experiment,
                    "--model",
                    model,
                    "--smoke",
                ]
                + (["--candidate-repair"] if candidate_repair else [])
                + (["--block-repair"] if block_repair else [])
                + (["--gc-repair"] if gc_repair else []),
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            processes.append(child)
            if child.wait(timeout=max(0.1, 600 - (time.monotonic() - started))):
                raise RuntimeError("Smoke request/persistence phase failed")
            cleanup()
    except (TimeoutError, subprocess.TimeoutExpired):
        report["status"] = "bounded_timeout_only"
    except BaseException as exc:  # noqa: BLE001 -- persist interrupted smoke and clean owned processes
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)
        cleanup()
        for handle in handles:
            handle.close()
        flags = [
            read_json(root / "flags" / (t["logical_key"] + ".json"))
            for t in (
                repair_tasks(config, registration, root)
                if candidate_repair or block_repair or gc_repair
                else gates.tasks(config, registration, root, experiment, smoke=True)
            )
            if (root / "flags" / (t["logical_key"] + ".json")).exists()
        ]
        ledger = DurableCallRegister(root / "calls.sqlite", limit=40000)
        prefix = "rq35_smoke:" + experiment + "/"
        with ledger.connect() as db:
            report["initiated_calls"] = db.execute(
                "SELECT count(*) FROM calls WHERE substr(call_key,1,?)=?",
                (len(prefix), prefix),
            ).fetchone()[0]
        report.update(
            elapsed_s=time.monotonic() - started,
            flags=flags,
            completed_units=sum(f["status"] == "done" for f in flags),
            additional_calls=report["initiated_calls"] - policy["previous_calls"],
        )
        if report["initiated_calls"] > policy["scope_limit"] or any(
            f["status"] == "fail" for f in flags
        ):
            report["status"] = "failed"
        save_json(destination, report)
    if report["status"] == "failed":
        raise RuntimeError("Smoke failed; no automatic retry")
    from .tests import review_smoke

    if gc_repair:
        from .tests import review_gc_repair

        reviewed = review_gc_repair(config, registration, root)
        report["elapsed_s"] = time.monotonic() - started
        report["persistence_review_included"] = True
        save_json(destination, report)
        return reviewed
    if block_repair:
        from .tests import review_block_repair

        reviewed = review_block_repair(config, registration, root)
        report["elapsed_s"] = time.monotonic() - started
        report["persistence_review_included"] = True
        save_json(destination, report)
        return reviewed
    if candidate_repair:
        from .tests import review_candidate_repair

        reviewed = review_candidate_repair(config, registration, root)
        report["elapsed_s"] = time.monotonic() - started
        report["persistence_review_included"] = True
        save_json(destination, report)
        return reviewed
    return review_smoke(config, registration, root, experiment)


def contract_changed(config, registration):
    return gates.contract(config) != registration["contract"]


def formal_phase_state(config, registration, root, experiment, model):
    """Only small done/fail markers; completed requests are never rebuilt."""
    from collections import Counter

    counts = Counter()
    for task in gates.tasks(
        config, registration, root, experiment, model, phase="screen"
    ):
        flag = terminal_flag(root, task) or {"status": "pending"}
        counts[flag["status"]] += 1
    return {
        "planned": sum(counts.values()),
        "pending": counts["pending"],
        **dict(counts),
    }


def formal_queue(config, registration, root):
    """User-authorized A/B screen only; no automatic scientific expansion."""
    import shutil
    import urllib.error
    import urllib.request

    from RQs.RQ3_3.src.main import exclusive
    from unified_scripts.vllm_inference import VLLMInferenceConfig

    authority = read_json(root / "formal_authorization.json")
    expected = [[e["id"], "screen"] for e in config["experiments"][:2]]
    if (
        authority["contract_hash"] != digest(registration["contract"])
        or authority["authorized_stages"] != expected
    ):
        raise ValueError("Queue scope is not authorized")
    for experiment, _ in expected:
        q = read_json(root / "qualification" / (experiment + ".json"))
        if q["status"] != "passed" or q["contract_hash"] != authority["contract_hash"]:
            raise ValueError("Current qualification missing")
    capacity = read_json(root / "input_capacity_screen.json")
    if (
        capacity.get("status") != "passed"
        or capacity.get("contract_hash") != authority["contract_hash"]
    ):
        raise ValueError("Missing current screen input-capacity report")
    stop = threading.Event()
    handlers = {
        s: signal.signal(s, lambda *_: stop.set())
        for s in (signal.SIGINT, signal.SIGTERM)
    }
    logs = root / "logs"
    logs.mkdir(exist_ok=True)
    stamp = str(time.time_ns())
    state = {
        "pid": os.getpid(),
        "attempt": stamp,
        "started_unix": time.time(),
        "contract_hash": authority["contract_hash"],
    }
    cli = [sys.executable, "-u", "-m", "RQs.RQ3_5.src.main"]
    runtime = VLLMInferenceConfig.load(ROOT / config["unified"]["inference"])

    def update(status, **fields):
        state.update(state=status, updated_unix=time.time(), **fields)
        save_json(root / "formal_queue_status.json", state)
        save_json(logs / ("queue_" + stamp + ".json"), state)
        print(json.dumps(state), flush=True)

    def terminate_group(process):
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)

    def command(args, label, graceful=False):
        if stop.is_set():
            raise InterruptedError("User paused queue")
        if shutil.disk_usage(root).free < 10 * 1024**3:
            raise OSError("Less than 10 GiB available; submissions stopped")
        with (logs / (stamp + "_" + label + ".log")).open("ab") as stream:
            child = subprocess.Popen(
                cli + args,
                cwd=ROOT,
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            update(
                state["state"], child_pid=child.pid, child_log=str(Path(stream.name))
            )
            try:
                while child.poll() is None:
                    if stop.wait(5):
                        if graceful:
                            child.send_signal(signal.SIGTERM)
                            try:
                                child.wait(timeout=330)
                            except subprocess.TimeoutExpired:
                                pass
                        raise InterruptedError("User paused queue")
                if child.returncode:
                    raise RuntimeError(
                        f"{label} exited {child.returncode}; see {stream.name}"
                    )
            finally:
                terminate_group(child)
        if stop.is_set():
            raise InterruptedError("User paused queue")

    def model_phase(experiment, model):
        if not formal_phase_state(config, registration, root, experiment, model)[
            "pending"
        ]:
            update("phase_already_terminal", experiment=experiment, model=model)
            return
        spec = runtime.model(model)
        request = urllib.request.Request(
            spec["base_url"].rstrip("/") + "/models",
            headers={
                "Authorization": "Bearer " + os.environ.get("VLLM_API_KEY", "EMPTY")
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=2):
                pass
        except urllib.error.URLError as exc:
            if not isinstance(exc.reason, ConnectionRefusedError):
                raise RuntimeError("Cannot establish vacant endpoint") from exc  # noqa: TRY004
        else:
            raise RuntimeError("Existing model service left untouched")
        prefix = stamp + "_" + experiment + "_" + model
        with (logs / (prefix + "_server.log")).open("ab") as stream:
            server = subprocess.Popen(
                ["bash", "scripts/vllm_vlm/serve_canvasrca_local.sh", model],
                cwd=ROOT,
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            update(
                "starting_model",
                experiment=experiment,
                model=model,
                server_pid=server.pid,
                server_log=str(Path(stream.name)),
                child_pid=None,
            )
            try:
                deadline = time.monotonic() + spec["wait_timeout_sec"]
                while True:
                    if stop.is_set():
                        raise InterruptedError("User paused model startup")
                    if server.poll() is not None:
                        raise RuntimeError("Owned vLLM exited during startup")
                    try:
                        with urllib.request.urlopen(request, timeout=2) as response:
                            names = [m["id"] for m in json.load(response)["data"]]
                        if names != [spec["served_model_name"]]:
                            raise ValueError("Unexpected served model")
                        break
                    except urllib.error.URLError:
                        if time.monotonic() >= deadline:
                            raise TimeoutError("Server startup timeout") from None
                        stop.wait(5)
                save_json(
                    root / "attestations" / (prefix + ".json"),
                    {
                        "model": model,
                        "served_names": names,
                        "effective": spec,
                        "argv": runtime.server_argv(model),
                        "contract_hash": authority["contract_hash"],
                        "pid_operational_only": server.pid,
                        "ready_unix": time.time(),
                    },
                )
                update("running", child_pid=None)
                command(
                    [
                        "run",
                        "--experiment",
                        experiment,
                        "--model",
                        model,
                        "--phase",
                        "screen",
                    ],
                    prefix,
                    graceful=True,
                )
                phase = formal_phase_state(
                    config, registration, root, experiment, model
                )
                if phase["pending"]:
                    raise InterruptedError(
                        "Runner exited before all units were terminal"
                    )
                save_json(
                    root / "phase_complete" / (experiment + "_" + model + ".json"),
                    phase,
                )
            finally:
                terminate_group(server)
                update("model_stopped", server_pid=None, child_pid=None)

    owned = False
    try:
        with exclusive(root / "formal_queue.lock"):
            owned = True
            update("preparation", phase="screen", child_pid=None, server_pid=None)
            command(["prepare", "--phase", "screen"], "prepare_screen")
            update("source_audit", child_pid=None)
            if not (root / "analysis/source_availability.json").exists():
                command(["source-audit"], "source_audit")
            for experiment, _ in expected:
                for model in config["models"]:
                    model_phase(experiment, model)
                update("analyzing", experiment=experiment, model=None)
                command(
                    ["analyze", "--experiment", experiment, "--phase", "screen"],
                    "analyze_" + experiment,
                )
            update(
                "completed_screen_ab",
                child_pid=None,
                server_pid=None,
                next_action="Review complete screen results; no automatic check/C/D/test",
            )
    except InterruptedError as exc:
        if owned:
            update("paused", reason=str(exc), child_pid=None, server_pid=None)
    except BaseException as exc:
        if owned:
            update(
                "failed",
                error=f"{type(exc).__name__}: {exc}",
                child_pid=None,
                server_pid=None,
            )
        raise
    finally:
        for s, handler in handlers.items():
            signal.signal(s, handler)
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "register",
            "cpu",
            "prepare",
            "run",
            "smoke",
            "qualify",
            "review",
            "analyze",
            "source-audit",
            "qualify-candidate-dedup",
            "activate-screen",
            "queue",
            "repair-blocks",
        ],
    )
    parser.add_argument("--config", default=str(CONFIG))
    parser.add_argument("--experiment")
    parser.add_argument("--model")
    parser.add_argument("--phase", default="screen")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--candidate-repair", action="store_true")
    parser.add_argument("--block-repair", action="store_true")
    parser.add_argument("--gc-repair", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    root = ROOT / config["implementation"]["output_root"]
    root.mkdir(parents=True, exist_ok=True)
    from RQs.RQ3_3.src.main import configure_environment
    from RQs.RQ3_4.src.main import import_prior_accounting

    configure_environment(runtime_config(config))
    if args.command == "qualify-candidate-dedup":
        print(gates.qualify_candidate_dedup(config, root))
        return
    if args.command == "activate-screen":
        print(gates.activate_screen(config, root))
        return
    if args.command == "repair-blocks":
        from RQs.RQ3_3.src.main import exclusive

        with (
            exclusive(root / "formal_queue.lock"),
            exclusive(root / "run.lock"),
            exclusive(root / "prepare.lock"),
        ):
            print(gates.finalize_block_repair(config, root))
        return
    registration = gates.register(config, root)
    import_prior_accounting(config, root)
    if args.command == "register":
        print(root / "registration.json")
    elif args.command == "queue":
        print(formal_queue(config, registration, root))
    elif args.command in {"cpu", "qualify"}:
        from .tests import cpu_qualification

        cpu_qualification(config, registration, root)
        if args.command == "qualify":
            for cell in config["experiments"]:
                print(
                    json.dumps(smoke(config, registration, root, cell["id"])),
                    flush=True,
                )
    elif args.command == "prepare":
        prepare(
            config,
            registration,
            root,
            gates.stage_roster(config, registration, root, args.phase),
        )
    elif args.command == "run":
        print(
            run(
                config,
                registration,
                root,
                args.experiment,
                args.model,
                args.smoke,
                args.phase,
                args.candidate_repair,
                args.block_repair,
                args.gc_repair,
            )
        )
    elif args.command == "smoke":
        print(
            json.dumps(
                smoke(
                    config,
                    registration,
                    root,
                    args.experiment,
                    args.candidate_repair,
                    args.block_repair,
                    args.gc_repair,
                )
            ),
            flush=True,
        )
    elif args.command == "review":
        from .tests import review_smoke

        print(review_smoke(config, registration, root, args.experiment))
    elif args.command == "analyze":
        gates.analyze(config, registration, root, args.experiment, args.phase)
    elif args.command == "source-audit":
        gates.source_audit(config, registration, root)


if __name__ == "__main__":
    main()

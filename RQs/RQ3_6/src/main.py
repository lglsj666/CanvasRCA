"""Stage A executor: bounded CPU prefetch, durable one-shot calls, owned smoke."""

import argparse
import concurrent.futures as cf
import json
import multiprocessing as mp
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections import defaultdict

from . import exps, gates
from .utils import (
    MODULE,
    ROOT,
    call_count,
    digest,
    endpoint_vacant,
    ensure_shared_ledger,
    interrupted_calls,
    load_config,
    model_probe,
    read_json,
    runtime_config,
    save_json,
    stop_owned,
    terminal_flag,
)

_TOKENS = None


def load_context(config, row):
    from RQs.RQ3_1.src.exps import _registered_trace_duration_projection
    from RQs.RQ3_4.src.main import load_integrated_context

    context, private = load_integrated_context(
        ROOT / config["implementation"]["source_run"], row
    )
    scale, source = _registered_trace_duration_projection(row["dataset"])
    if scale not in {1.0, 0.001}:
        raise ValueError("Unregistered parent stored-duration unit")
    # Metadata drives only a source-attested unit label, never case routing.
    context["rq36_parent_trace_unit"] = "us" if scale == 0.001 else "ms"
    context["rq36_duration_source"] = source
    return context, private


def compile_case(args):
    """One loaded cache per case; tokenizers persist per core-pinned worker."""
    from RQs.RQ3_3.src.utils import OfflineTokens

    global _TOKENS
    config, tasks = args
    if _TOKENS is None:
        _TOKENS = OfflineTokens(runtime_config(config))
    context, private = load_context(config, tasks[0]["case"])
    if config.get("stage") == "B":
        exps.prepare_stage_b(context, config, _TOKENS)
    return [(t, exps.compile_unit(t, context, private, config, _TOKENS)) for t in tasks]


def cpu_pool(count):
    from vlmrca.run_state import physical_cpu_ids, pin_process_to_core

    ctx = mp.get_context("spawn")
    cores = physical_cpu_ids()[: min(8, count)]
    queue = ctx.Queue()
    for core in cores:
        queue.put(core)
    pool = cf.ProcessPoolExecutor(
        len(cores), mp_context=ctx, initializer=pin_process_to_core, initargs=(queue,)
    )
    return pool, queue, len(cores)


def close_pool(pool, queue, abort=False):
    if abort:
        workers = list(pool._processes.values())
        pool.shutdown(wait=False, cancel_futures=True)
        for process in workers:
            if process.is_alive():
                process.kill()
        for process in workers:
            process.join(timeout=5)
    else:
        pool.shutdown(wait=True, cancel_futures=True)
    queue.close()
    queue.join_thread()


def run(config, registration, root, model, smoke=False):
    from RQs.RQ3_3.src.main import exclusive, interleaved_sources
    from RQs.RQ3_4.src.main import execute_integrated

    gates.authorize_run(config, registration, root, smoke)
    all_tasks = gates.tasks(config, registration, model=model, smoke=smoke)
    with exclusive(root / "run.lock"):
        # Terminal units do not touch the 14GB parent cache, images or tokenizers.
        pending = [t for t in all_tasks if terminal_flag(root, t) is None]
        if not pending:
            return {"status": "already_terminal", "units": len(all_tasks)}
        interrupted_calls(root, pending[0]["ledger_scope"])
        grouped = defaultdict(list)
        for task in pending:
            grouped[task["case"]["opaque_incident_id"]].append(task)
        rows = interleaved_sources([items[0]["case"] for items in grouped.values()])
        cases = iter([grouped[row["opaque_incident_id"]] for row in rows])
        stop = threading.Event()
        handlers = {
            s: signal.signal(s, lambda *_: stop.set())
            for s in (signal.SIGINT, signal.SIGTERM)
        }
        pool, queue, width = cpu_pool(min(config["execution"]["workers"], len(grouped)))
        requests = cf.ThreadPoolExecutor(max_workers=config["execution"]["concurrency"])
        preparing, inflight = set(), set()
        done_count, fatal = len(all_tasks) - len(pending), None

        def submit_case():
            items = next(cases, None)
            if items is not None and not stop.is_set():
                preparing.add(pool.submit(compile_case, (config, items)))

        def collect(completed):
            nonlocal done_count
            for future in completed:
                future.result()
                inflight.remove(future)
                done_count += 1

        try:
            for _ in range(width):
                submit_case()
            while preparing and not stop.is_set():
                collect({f for f in inflight if f.done()})
                ready, _ = cf.wait(preparing, timeout=1, return_when=cf.FIRST_COMPLETED)
                for future in ready:
                    preparing.remove(future)
                    compiled = future.result()
                    submit_case()
                    for task, request in compiled:
                        if stop.is_set():
                            break
                        while len(inflight) >= config["execution"]["concurrency"]:
                            completed, _ = cf.wait(
                                inflight, return_when=cf.FIRST_COMPLETED
                            )
                            collect(completed)
                        collect({f for f in inflight if f.done()})
                        if (
                            shutil.disk_usage(root).free
                            < config["execution"]["min_free_disk_gib"] * 2**30
                        ):
                            raise OSError(
                                "Low disk: stop submissions and drain owned writes"
                            )
                        inflight.add(
                            requests.submit(
                                execute_integrated, task, request, config, root
                            )
                        )
                    print(
                        json.dumps(
                            {
                                "model": model,
                                "terminal": done_count,
                                "planned": len(all_tasks),
                                "inflight": len(inflight),
                                "prefetch_cases": len(preparing),
                            }
                        ),
                        flush=True,
                    )
            while inflight:
                completed, _ = cf.wait(inflight, return_when=cf.FIRST_COMPLETED)
                collect(completed)
        except BaseException as exc:  # noqa: BLE001 -- drain owned writes, persist then re-raise
            fatal = exc
            stop.set()
        finally:
            for future in inflight:
                future.cancel()
            close_pool(pool, queue, abort=stop.is_set())
            requests.shutdown(wait=True, cancel_futures=True)
            for sig, handler in handlers.items():
                signal.signal(sig, handler)
            save_json(
                root / "progress" / (all_tasks[0]["stage"] + "_" + model + ".json"),
                {
                    "planned": len(all_tasks),
                    "terminal": sum(
                        (root / "flags" / (t["logical_key"] + ".json")).exists()
                        for t in all_tasks
                    ),
                    "paused": stop.is_set(),
                    "error": repr(fatal) if fatal else None,
                },
            )
        if fatal:
            raise fatal
        return {
            "status": "paused" if stop.is_set() else "complete",
            "units": done_count,
        }


def smoke(config, registration, root, resume_repair=False):
    """One aggregate window; never attach to or kill an unrelated vLLM server."""
    from RQs.RQ3_3.src.main import exclusive
    from unified_scripts.vllm_inference import VLLMInferenceConfig

    from .tests import review

    gates.assert_current(config, registration)
    cpu = read_json(root / "cpu_qualification.json")
    h = digest(registration["contract"])
    if cpu["status"] != "passed" or cpu["contract_hash"] != h:
        raise ValueError("Current CPU qualification required")
    runtime = VLLMInferenceConfig.load(ROOT / config["unified"]["inference"])
    if os.environ.get("CANVASRCA_VLLM_CONFIG") != str(
        ROOT / config["unified"]["inference"]
    ):
        raise ValueError("Canonical launcher profile must equal registration")
    deadline = time.time() + config["qualification"]["max_seconds"]
    report = {"status": "complete", "contract_hash": h, "models_finished": []}
    destination = root / "smokes" / (config["experiment"] + ".json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    marker = destination.with_name(config["experiment"] + "_started.json")
    if resume_repair:
        repair = read_json(root / "repairs/image_provenance.json")
        window = read_json(marker)
        if repair["new_contract_hash"] != h or window["contract_hash"] != h:
            raise ValueError("Repair contract mismatch")
        deadline = window["deadline_unix"]
        if time.time() >= deadline:
            raise ValueError(
                "Original smoke deadline passed; no new model calls authorized"
            )
        report["resumed_same_window"] = True
    elif destination.exists() or marker.exists():
        raise ValueError("Logical smoke already initiated; cannot reset its budget")
    if not resume_repair:
        with marker.open("x") as stream:
            json.dump(
                {
                    "started_unix": time.time(),
                    "deadline_unix": deadline,
                    "contract_hash": h,
                    "max_calls": 18,
                    "max_seconds": 600,
                },
                stream,
            )
    processes, handles = [], []

    def cleanup():
        for process in reversed(processes):
            stop_owned(process)
        processes.clear()

    def expire(*_):
        raise TimeoutError("Aggregate 600-second smoke window exhausted")

    handlers = {s: signal.signal(s, expire) for s in (signal.SIGALRM,)}
    previous_stops = {
        s: signal.signal(
            s, lambda *_: (_ for _ in ()).throw(InterruptedError("Smoke interrupted"))
        )
        for s in (signal.SIGINT, signal.SIGTERM)
    }
    signal.setitimer(signal.ITIMER_REAL, max(0.01, deadline - time.time()))
    try:
        with exclusive(root / "smoke.lock"):
            for model in config["models"]:
                if all(
                    terminal_flag(root, t) is not None
                    for t in gates.tasks(config, registration, model=model, smoke=True)
                ):
                    report["models_finished"].append(model)
                    continue
                spec = runtime.model(model)
                if not endpoint_vacant(spec):
                    raise RuntimeError("Existing server left untouched")
                log = (destination.parent / (model + "_server.log")).open("ab")
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
                        raise RuntimeError(
                            "Canonical server exited; inspect server log"
                        )
                    if model_probe(spec):
                        break
                    time.sleep(5)
                save_json(
                    root / "attestations" / ("smoke_" + model + ".json"),
                    {
                        "model": model,
                        "effective": spec,
                        "argv": runtime.server_argv(model),
                        "profile": config["unified"]["inference"],
                        "contract_hash": h,
                        "ready_unix": time.time(),
                        "pid_operational_only": server.pid,
                    },
                )
                log = (destination.parent / (model + "_runner.log")).open("ab")
                handles.append(log)
                child = subprocess.Popen(
                    [sys.executable, "-m", MODULE, "run", "--model", model, "--smoke"],
                    cwd=ROOT,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                processes.append(child)
                if child.wait(timeout=max(0.01, deadline - time.time())):
                    raise RuntimeError("Request/persistence phase failed")
                report["models_finished"].append(model)
                cleanup()
            # Full persistence review is inside the same logical deadline.
            report["review"] = review(config, registration, root)
    except (TimeoutError, subprocess.TimeoutExpired):
        report["status"] = "bounded_timeout_only"
    except BaseException as exc:  # noqa: BLE001 -- preserve evidence and stop only owned processes
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        cleanup()
        for handle in handles:
            handle.close()
        for sig, handler in {**handlers, **previous_stops}.items():
            signal.signal(sig, handler)
        flags = [
            read_json(root / "flags" / (t["logical_key"] + ".json"))
            for t in gates.tasks(config, registration, smoke=True)
            if (root / "flags" / (t["logical_key"] + ".json")).exists()
        ]
        report.update(
            elapsed_s=time.time() - read_json(marker)["started_unix"],
            flags=flags,
            initiated_calls=call_count(root, "rq36_smoke:" + config["experiment"]),
        )
        if report["initiated_calls"] > 18 or any(f["status"] != "done" for f in flags):
            report["status"] = "failed"
        save_json(destination, report)
    if report["status"] == "failed":
        raise RuntimeError("Smoke failed; no automatic extra calls")
    # Post-deadline auditing may inspect saved outputs, never initiate requests.
    if "review" not in report:
        report["review"] = review(config, registration, root)
        report["post_deadline_read_only_review"] = True
        save_json(destination, report)
    save_json(
        root / "qualification.json",
        {
            "status": "passed",
            "contract_hash": h,
            "outcome": report["status"],
            "initiated_calls": report["initiated_calls"],
            "completed_units": len(flags),
            "manual_review_passed": False,
            "automatic_artifact_review": report["review"],
            "scope": "Stage "
            + config.get("stage", "A")
            + " only; no formal authorization or later-stage qualification",
        },
    )
    return report


def repair_image_provenance(config, root):
    """Repair post-response audit only, without regenerating any saved response."""
    from pathlib import Path

    from RQs.RQ3_1.src.main import audit_completion_artifacts
    from RQs.RQ3_3.src.exps import request_descriptor
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_4.src.main import response_audit

    from .tests import cpu_qualification

    registration = read_json(root / "registration.json")
    old = read_json(root / "smokes" / (config["experiment"] + ".json"))
    repair_root = root / "repairs"
    if (repair_root / "image_provenance.json").exists():
        raise ValueError("One-time recovery already performed")
    if old["status"] != "failed" or old["initiated_calls"] != 9:
        raise ValueError("Unexpected recovery population")
    if any(f.get("error") != "KeyError: 'image_hashes'" for f in old["flags"]):
        raise ValueError("Recovery cannot conceal other failures")
    save_json(repair_root / "registration_before.json", registration)
    save_json(repair_root / "smoke_before.json", old)
    save_json(
        repair_root / "cpu_before.json", read_json(root / "cpu_qualification.json")
    )
    tokens = OfflineTokens(runtime_config(config))
    by_key = {
        t["logical_key"]: t for t in gates.tasks(config, registration, smoke=True)
    }
    cache, recovered = {}, []
    for flag in old["flags"]:
        task = by_key[flag["logical_key"]]
        opaque = task["case"]["opaque_incident_id"]
        if opaque not in cache:
            cache[opaque] = load_context(config, task["case"])
        context, private = cache[opaque]
        request = exps.compile_unit(task, context, private, config, tokens)
        directory, key = Path(flag["artifact_root"]), flag["call_key"]
        audit_completion_artifacts(directory, key)
        prompt = read_json(directory / "prompts" / (key + ".json"))
        parts = [
            {"type": "text", "text": p["text"]}
            if p["type"] == "text"
            else {"type": "image", "png": (directory / p["image_path"]).read_bytes()}
            for p in prompt["parts"]
        ]
        actual = request_descriptor(parts, prompt["system"], prompt, task["model"])
        if actual != request["actual"]:
            raise ValueError("Repair changed the saved model request")
        result = read_json(directory / "outputs" / (key + ".json"))
        cost = read_json(directory / "cost" / (key + ".json"))
        audit = response_audit(request, result["response"])
        save_json(directory / "audits" / (key + ".json"), audit)
        metrics = result["score"].get("metrics") or result["score"]
        done = {
            "status": "done",
            "logical_key": flag["logical_key"],
            "call_key": key,
            "artifact_root": str(directory),
            "input_identity": request["input_identity"],
            "model_status": result["status"],
            "audit_status": audit["status"],
            "metrics": {
                k: metrics[k] for k in ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")
            },
            **{
                k: cost.get(k)
                for k in (
                    "input_tokens",
                    "output_tokens",
                    "text_tokens",
                    "image_tokens",
                    "wall_time_s",
                    "new_generation_calls",
                )
            },
            "recovery": "post_response_image_provenance_only; original prompt/output/completion unchanged",
        }
        save_json(root / "flags" / (task["logical_key"] + ".json"), done)
        recovered.append(key)
    previous_hash = digest(registration["contract"])
    registration["contract"] = gates.contract(config)
    save_json(root / "registration.json", registration)
    marker = root / "smokes" / (config["experiment"] + "_started.json")
    window = read_json(marker)
    window["contract_hash"] = digest(registration["contract"])
    save_json(marker, window)
    save_json(
        repair_root / "image_provenance.json",
        {
            "old_contract_hash": previous_hash,
            "new_contract_hash": digest(registration["contract"]),
            "recovered_calls": recovered,
            "new_model_calls": 0,
            "unchanged_actual_requests": True,
            "original_deadline_unix": window["deadline_unix"],
        },
    )
    cpu_qualification(config, registration, root)
    return smoke(config, registration, root, resume_repair=True)


def formal_queue():
    """Sequential registered families/models, flag-only resume, owned services."""
    from datetime import UTC, datetime

    from RQs.RQ3_3.src.main import exclusive
    from unified_scripts.vllm_inference import VLLMInferenceConfig

    base = ROOT / "RQs/RQ3_6/results/mechanisms_v2"
    base.mkdir(parents=True, exist_ok=True)
    state_path = base / "formal_queue_status.json"
    stop = threading.Event()
    handlers = {
        s: signal.signal(s, lambda *_: stop.set())
        for s in (signal.SIGTERM, signal.SIGINT)
    }
    state = {"pid": os.getpid(), "server_pid": 0, "runner_pid": 0}
    server = child = None

    def update(phase, **extra):
        state.update(state=phase, updated_utc=datetime.now(UTC).isoformat(), **extra)
        save_json(state_path, state)
        print(json.dumps(state), flush=True)

    try:
        with exclusive(base / "queue.lock"):
            configs = [
                ROOT / f"RQs/RQ3_6/configs/{family}_v2.json"
                for family in ("g_components", "scope_competition", "relation_binding")
            ]
            for path in configs:
                config = read_json(path)
                root = ROOT / config["implementation"]["output_root"]
                registration = read_json(root / "registration.json")
                gates.authorize_run(config, registration, root, False)
                capacity = read_json(root / "capacity_qualification.json")
                if capacity.get("status") != "passed" or capacity.get(
                    "contract_hash"
                ) != digest(registration["contract"]):
                    raise ValueError("All-case CPU capacity qualification required")
            for path in configs:
                config = read_json(path)
                root = ROOT / config["implementation"]["output_root"]
                registration = read_json(root / "registration.json")
                runtime = VLLMInferenceConfig.load(
                    ROOT / config["unified"]["inference"]
                )
                for model in config["models"]:
                    if stop.is_set():
                        raise InterruptedError("User paused queue")
                    tasks = gates.tasks(config, registration, model=model)
                    started = time.monotonic()
                    pending = [t for t in tasks if terminal_flag(root, t) is None]
                    update(
                        "resume_index",
                        family=config["family"],
                        model=model,
                        terminal=len(tasks) - len(pending),
                        planned=len(tasks),
                        resume_seconds=time.monotonic() - started,
                    )
                    if not pending:
                        continue
                    gates.authorize_run(config, registration, root, False)
                    spec = runtime.model(model)
                    if not endpoint_vacant(spec):
                        raise RuntimeError("Existing endpoint left untouched")
                    if os.environ.get("CANVASRCA_VLLM_CONFIG") != str(
                        ROOT / config["unified"]["inference"]
                    ):
                        raise ValueError("Queue launcher profile mismatch")
                    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
                    logs = root / "logs"
                    logs.mkdir(exist_ok=True)
                    server_path = logs / f"{stamp}_{model}_server.log"
                    runner_path = logs / f"{stamp}_{model}_runner.log"
                    with server_path.open("ab") as output:
                        server = subprocess.Popen(
                            [
                                "bash",
                                "scripts/vllm_vlm/serve_canvasrca_local.sh",
                                model,
                            ],
                            cwd=ROOT,
                            stdout=output,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                        )
                    update(
                        "starting_model",
                        server_pid=server.pid,
                        server_log=str(server_path),
                    )
                    deadline = time.monotonic() + spec["wait_timeout_sec"]
                    while not model_probe(spec):
                        if stop.is_set():
                            raise InterruptedError("User paused startup")
                        if server.poll() is not None:
                            raise RuntimeError("Owned model server exited")
                        if time.monotonic() >= deadline:
                            raise TimeoutError("Model startup timeout")
                        stop.wait(5)
                    save_json(
                        root / "attestations" / f"{stamp}_{model}.json",
                        {
                            "model": model,
                            "effective": spec,
                            "argv": runtime.server_argv(model),
                            "profile": config["unified"]["inference"],
                            "contract_hash": digest(registration["contract"]),
                            "pid_operational_only": server.pid,
                            "ready_unix": time.time(),
                            "server_log": str(server_path),
                        },
                    )
                    env = {**os.environ, "CANVASRCA_RQ36_CONFIG": str(path)}
                    with runner_path.open("ab") as output:
                        child = subprocess.Popen(
                            [sys.executable, "-m", MODULE, "run", "--model", model],
                            cwd=ROOT,
                            env=env,
                            stdout=output,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                        )
                    update("running", runner_pid=child.pid, runner_log=str(runner_path))
                    while child.poll() is None:
                        if stop.wait(5):
                            child.send_signal(signal.SIGTERM)
                            try:
                                child.wait(timeout=330)
                            except subprocess.TimeoutExpired:
                                stop_owned(child)
                            raise InterruptedError(
                                "User paused; submitted requests drained"
                            )
                        if server.poll() is not None:
                            raise RuntimeError(
                                "Owned model server died during inference"
                            )
                    if child.returncode:
                        raise RuntimeError(
                            "Runner failed; inspect preserved runner log"
                        )
                    if any(terminal_flag(root, t) is None for t in tasks):
                        raise RuntimeError("Runner ended with uncommitted units")
                    save_json(
                        root / "progress" / (model + "_complete.json"),
                        {
                            "planned": len(tasks),
                            "terminal": len(tasks),
                            "contract_hash": digest(registration["contract"]),
                        },
                    )
                    stop_owned(child)
                    child = None
                    stop_owned(server)
                    server = None
                    update("model_complete", runner_pid=0, server_pid=0)
            update("completed")
    except InterruptedError as exc:
        update("paused", reason=str(exc))
    except BaseException as exc:
        update("failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if child is not None:
            if child.poll() is None:
                child.send_signal(signal.SIGTERM)
                try:
                    child.wait(timeout=330)
                except subprocess.TimeoutExpired:
                    pass
            stop_owned(child)
        if server is not None:
            stop_owned(server)
        state.update(server_pid=0, runner_pid=0)
        save_json(state_path, state)
        for s, handler in handlers.items():
            signal.signal(s, handler)
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=[
            "register",
            "cpu",
            "smoke",
            "run",
            "review",
            "queue",
            "capacity",
            "repair-image-provenance",
        ],
    )
    parser.add_argument("--model")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    config = load_config()
    root = ROOT / config["implementation"]["output_root"]
    root.mkdir(parents=True, exist_ok=True)
    ensure_shared_ledger(config, root)
    if args.action == "queue":
        print(json.dumps(formal_queue()), flush=True)
        return
    if args.action == "repair-image-provenance":
        print(json.dumps(repair_image_provenance(config, root)), flush=True)
        return
    if args.action in {"register", "cpu"}:
        registration = gates.register(config, root)
        from RQs.RQ3_4.src.main import import_prior_accounting

        import_prior_accounting(config, root)
    else:
        registration = read_json(root / "registration.json")
        gates.assert_current(config, registration)
    if args.action == "register":
        result = {
            "status": "registered",
            "contract_hash": digest(registration["contract"]),
            "formal_calls_max": config["budget"]["formal_new_calls_max"],
        }
    elif args.action == "cpu":
        from .tests import cpu_qualification

        result = cpu_qualification(config, registration, root)
    elif args.action == "smoke":
        result = smoke(config, registration, root)
    elif args.action == "review":
        from .tests import review

        result = review(config, registration, root)
    elif args.action == "capacity":
        from .tests import capacity_qualification

        result = capacity_qualification(config, registration, root)
    else:
        if args.model not in config["models"]:
            raise ValueError("Run one registered model per process")
        result = run(config, registration, root, args.model, args.smoke)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

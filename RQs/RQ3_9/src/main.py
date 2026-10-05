"""Local, resumable four-condition pilot. Never starts a legacy RQ queue."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from copy import deepcopy
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time

from . import exps
from .utils import (ROOT, VERSION, MODEL, ARMS, config, path, read_json, write_json, sha_file,
                    stable_hash, immutable_json, exclusive, register, runtime, source_contract,
                    logical_key, flag, log)


def verify_clock(c, row, bundle):
    """Only timestamp-column metadata, not original raw telemetry reprocessing.

    Inherited panels.render_metric_panel takes the SAME wide metrics_df timestamp
    vector for every selected column, bins on finite timestamps (not on finite
    values), and exports identical 64 relative bins. Missing samples retain null.
    Public source provenance and this code path establish the common metric
    clock. Trace/log/onset clocks are explicitly NOT asserted to match it.
    """
    import pyarrow.parquet as pq
    import numpy as np
    source = path(c["parent"]) / "audit" / (row["opaque_incident_id"] + ".json")
    audit = read_json(source)
    directory = Path(audit["source"]["topology"]["source_directory"])
    if not directory.is_absolute():
        directory = ROOT / directory
    expected = ROOT / "build/local_processed_v3/public" / row["dataset"] / "cases" / row["opaque_incident_id"]
    if directory.resolve() != expected.resolve():
        raise ValueError("Unexpected public case clock source")
    file = directory / "metrics.parquet"
    table = pq.read_table(file, columns=["timestamp"])
    ts = np.asarray(table["timestamp"].to_numpy(), dtype=float)
    finite = ts[np.isfinite(ts)]
    metrics = [k for k in bundle["evidence"]["cards"] if k["kind"] == "metric"]
    verified = bool(finite.size > 1 and np.max(finite) > np.min(finite) and metrics
                    and all(k["data"]["bins"] == list(range(64)) for k in metrics))
    return {"verified": verified, "basis": "inherited common wide-frame timestamp, 64-bin producer",
            "timestamp_rows": len(ts), "finite_timestamp_rows": len(finite),
            "clock_digest": stable_hash([float(v) if np.isfinite(v) else None for v in ts]),
            "source_audit_hash": sha_file(source),
            "producer_sha256": sha_file(ROOT / "RQs/RQ1_1/src/renderer/panels.py"),
            "metric_only": True}


def prepare_one(args):
    c, row = args
    root = path(c["preparation"])
    oid = row["opaque_incident_id"]
    marker = root / "flags" / (oid + ".json")
    if marker.exists():
        saved = read_json(marker)
        if saved.get("status") != "done" or saved.get("version") != VERSION:
            raise ValueError("Preparation marker not complete")
        return saved
    start = time.monotonic()
    parent = path(c["parent"])
    if read_json(parent / "export_flags" / (oid + ".json"))["status"] != "done":
        raise ValueError("Parent public export uncommitted")
    bundle = read_json(parent / "public" / (oid + ".json"))
    clock = verify_clock(c, row, bundle)
    groups, audit = exps.comparison_candidates(bundle["evidence"], clock)
    texts = exps.compile_texts(bundle, groups)
    evidence, designs = exps.designs(bundle, groups)
    prepared = {"version": VERSION, "system": bundle["system"], "candidates": bundle["candidates"],
                "facts_hash": bundle["facts_hash"], "groups": groups, "texts": texts, "images": {}}
    audit["visible_audit"] = exps.visible_audit(bundle, prepared)
    from RQs.RQ3_8.src.main import render_capture
    for arm, design in designs.items():
        inputs = root / "render_inputs" / oid / arm
        immutable_json(inputs / "evidence.json", evidence)
        immutable_json(inputs / "design.json", design)
        output = root / "renders" / oid / arm
        if not (output / "manifest.json").exists() or read_json(output / "manifest.json").get("status") != "passed":
            if output.exists():
                output.rename(output.with_name(arm + ".interrupted." + str(time.time_ns())))
            manifest = render_capture(inputs / "evidence.json", inputs / "design.json", output)
        else:
            manifest = read_json(output / "manifest.json")
        if (manifest.get("status") != "passed" or manifest["evidence_hash"] != stable_hash(evidence)
                or manifest["design_hash"] != stable_hash(design)):
            raise ValueError("Renderer failed or rendered different observations")
        prepared["images"][arm] = {"path": str((output / "dashboard.png").relative_to(root)),
                                    "sha256": manifest["png_sha256"]}
    # Deduplicate no-operation cells BEFORE dispatch to avoid concurrent copies.
    identities, canonical = {}, {}
    for arm in ARMS:
        png = (root / prepared["images"][arm]["path"]).read_bytes() if arm in prepared["images"] else None
        parts = exps.parts_for(prepared, arm, png)
        signature = stable_hash([{**p, "png": stable_hash(p["png"])} if "png" in p else p for p in parts])
        canonical[arm] = identities.setdefault(signature, arm)
    prepared["canonical_arms"] = canonical
    immutable_json(root / "public" / (oid + ".json"), prepared)
    write_json(root / "audit" / (oid + ".json"), audit)
    # Scoring data enters only AFTER public text/PNG construction; never an
    # argument to the evidence compiler or renderer.
    immutable_json(root / "private" / (oid + ".json"), read_json(parent / "private" / (oid + ".json")))
    done = {"version": VERSION, "status": "done", "case": oid, "seconds": time.monotonic()-start,
            "groups": len(groups), "kinds": audit["selected_kinds"], "canonical_arms": canonical,
            "parent_public_sha256": sha_file(parent / "public" / (oid + ".json"))}
    write_json(marker, done)
    log("prepared", **done)
    return done


def prepare(c):
    from vlmrca.run_state import pinned_process_map
    from RQs.RQ3_8.src.utils import interleaved
    reg = register(c)
    with exclusive(path(c["preparation"]) / "prepare.lock"):
        results = pinned_process_map(prepare_one, [(c, r) for r in interleaved(reg["cases"])], max_workers=c["workers"])
    summary = {"status": "complete", "cases": len(results),
               "group_counts": dict(Counter(r["groups"] for r in results)),
               "comparison_kinds": dict(Counter(k for r in results for k in r["kinds"])),
               "group_counts_by_dataset": {ds: dict(Counter(r["groups"] for r in results
                    if next(v for v in reg["cases"] if v["opaque_incident_id"] == r["case"])["dataset"] == ds))
                    for ds in c["datasets"]}}
    write_json(path(c["results"]) / "qualification" / "eligibility.json", summary)
    return summary


def execute(c, row, arm, root, ledger):
    from RQs.RQ3_1.src.main import (_request_envelope, bind_task_request, run_registered_call,
                                   score_response_callback)
    from RQs.RQ3_3.src.exps import request_descriptor
    from RQs.RQ3_3.src.main import timeout_exception
    oid = row["opaque_incident_id"]
    if flag(root, oid, arm) is not None:
        return
    if shutil.disk_usage(root).free < 10 * 1024**3:
        raise OSError("Disk reserve reached")
    prep = path(c["preparation"])
    public = read_json(prep / "public" / (oid + ".json"))
    png = (prep / public["images"][arm]["path"]).read_bytes() if arm in public["images"] else None
    parts = exps.parts_for(public, arm, png)
    envelope = _request_envelope(MODEL, system=public["system"])
    envelope["policy_version"] = VERSION
    actual = request_descriptor(parts, public["system"], envelope, MODEL)
    projection = {"original_facts": public["facts_hash"], "request": stable_hash(actual)}
    task = {"experiment": ("smoke_" if root.name == "smoke" else "") + c["experiment"],
            "model": MODEL, "case": row, "dimensions": {"arm": arm, "replicate": 0}}
    bound = bind_task_request(task, actual, stable_hash(projection), projection=projection,
                              adapter_version=VERSION, version=VERSION)
    common = {"case": oid, "arm": arm, "model": MODEL, "call_key": bound["call_key"],
              "logical_key": logical_key(oid, arm), "request_hash": stable_hash(actual),
              "facts_hash": public["facts_hash"], "groups": len(public["groups"])}
    private = read_json(prep / "private" / (oid + ".json"))
    bound["fault_type"] = private.get("fault_type", "unavailable")  # evaluator output only
    write_json(root / "submissions" / (common["logical_key"] + ".json"), {**common, "time": time.time()})
    log("submitting", case=oid, arm=arm)
    try:
        out = run_registered_call(bound, parts, envelope, root, ledger=ledger,
                                  score_response=score_response_callback(private, public["candidates"]))
        result = {**common, "status": "done", "model_status": out["status"], "new_calls": 1}
    except Exception as exc:
        if timeout_exception(exc):
            result = {**common, "status": "fail", "failure_class": "request_timeout", "error": str(exc)}
        elif isinstance(exc, ValueError) and str(exc).startswith("input exceeds context:"):
            result = {**common, "status": "design_infeasible", "reason": str(exc), "new_calls": 0}
        else:
            write_json(root / "flags" / (common["logical_key"] + ".json"),
                       {**common, "status": "fail", "failure_class": "infrastructure", "error": repr(exc)})
            raise
    write_json(root / "flags" / (common["logical_key"] + ".json"), result)
    log("terminal", case=oid, arm=arm, status=result["status"])


def run(c, smoke=False):
    from vlmrca.run_state import DurableCallRegister, audit_call_artifacts
    from .gates import summarize
    reg = register(c)
    root = path(c["results"]) / ("smoke" if smoke else "formal")
    rows = reg["smoke"] if smoke else reg["cases"]
    runtime(c)
    with exclusive(root / "runner.lock"):
        # Fast flags first. Completed cases never load context or reconstruct requests.
        tasks, aliases = [], []
        for row in rows:
            oid = row["opaque_incident_id"]
            pending = [a for a in ARMS if flag(root, oid, a) is None]
            if not pending:
                continue
            marker = read_json(path(c["preparation"]) / "flags" / (oid + ".json"))
            for a in pending:
                canonical = marker["canonical_arms"][a]
                if canonical == a:
                    tasks.append((row, a))
                else:
                    aliases.append((row, a, canonical))
        ledger = DurableCallRegister(root / "calls.sqlite", scope=VERSION,
                                     limit=c["smoke_attempt_limit"] if smoke else c["formal_attempt_limit"])
        recovery = ledger.recover_persisted(root, audit=audit_call_artifacts)
        write_json(root / "recovery.json", recovery)
        log("queue_started", targets=len(tasks), references=len(aliases), smoke=smoke)
        stop = threading.Event()
        old = {s: signal.signal(s, lambda *_: stop.set()) for s in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1)}
        errors = []
        try:
            # Interleave arms across datasets to avoid making the fourth condition
            # a chronologically different batch. All 12 smoke paths run concurrently.
            tasks.sort(key=lambda x: stable_hash([42, "dispatch", x[0]["opaque_incident_id"], x[1]]))
            iterator = iter(tasks)
            with ThreadPoolExecutor(max_workers=c["concurrency"]) as pool:
                active = set()
                def refill():
                    while not stop.is_set() and len(active) < c["concurrency"]:
                        item = next(iterator, None)
                        if item is None:
                            break
                        active.add(pool.submit(execute, c, *item, root, ledger))
                refill()
                while active:
                    completed, active = wait(active, timeout=5, return_when=FIRST_COMPLETED)
                    for future in completed:
                        try:
                            future.result()
                        except Exception as exc:
                            errors.append(repr(exc))
                            stop.set()
                    refill()
        finally:
            for sig, handler in old.items():
                signal.signal(sig, handler)
        for row, arm, canonical in aliases:
            source = flag(root, row["opaque_incident_id"], canonical)
            if source is not None:
                value = {**source, "arm": arm, "logical_key": logical_key(row["opaque_incident_id"], arm),
                         "reference_arm": canonical, "new_calls": 0, "no_op": True}
                write_json(root / "flags" / (value["logical_key"] + ".json"), value)
        report = summarize(c, smoke)
        report.update(errors=errors, accounting=ledger.summary())
        if errors:
            report["status"] = "failed"
        write_json(root / "phase.json", report)
        if errors:
            raise RuntimeError(errors[0])
        return report


def supervise(c, smoke=False):
    started = time.monotonic()
    from RQs.RQ3_6.src.utils import model_probe, endpoint_vacant, stop_owned
    from .gates import require_qualification
    root = path(c["results"]) / ("smoke" if smoke else "formal")
    rows = register(c)["smoke" if smoke else "cases"]
    with exclusive(root / "supervisor.lock"):
        if all(flag(root, r["opaque_incident_id"], a) is not None for r in rows for a in ARMS):
            log("already_complete", smoke=smoke)
            return
        require_qualification(c, smoke)
        loaded, spec = runtime(c)
        if not endpoint_vacant(spec):
            raise RuntimeError("Port occupied; will not stop or attach to another server")
        deadline = started + c["smoke_seconds"] if smoke else float("inf")
        stop = threading.Event()
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
            signal.signal(sig, lambda *_: stop.set())
        server = runner = None
        status = "complete"
        (root / "logs").mkdir(parents=True, exist_ok=True)
        stamp = str(time.time_ns())
        write_json(root / "supervisor.json", {"status": "starting", "started": time.time(), "smoke": smoke})
        try:
            with (root / "logs" / ("server." + stamp + ".log")).open("w") as serverlog:
                server = subprocess.Popen(["bash", "scripts/vllm_vlm/serve_canvasrca_local.sh", MODEL],
                                          cwd=ROOT, stdout=serverlog, stderr=subprocess.STDOUT, start_new_session=True)
                while not model_probe(spec):
                    if server.poll() is not None:
                        raise RuntimeError("Model startup exited: " + str(server.returncode))
                    if stop.is_set() or time.monotonic() >= deadline:
                        status = "interrupted" if stop.is_set() else "bounded_timeout"
                        break
                    stop.wait(2)
                if status == "complete":
                    # Reuse the proven attestation implementation, supplement with
                    # the new experiment's own complete source contract.
                    from RQs.RQ3_8.src.gates import attest
                    os.environ["CANVASRCA_RQ38_DEPLOYMENT"] = "local"
                    attestation = attest(c, root, MODEL, server.pid)
                    attestation["rq39_source_contract"] = source_contract()
                    write_json(root / "attestation.json", attestation)
                    log("ready", elapsed=time.monotonic()-started, model=MODEL)
                    write_json(root / "supervisor.json", {"status": "ready", "smoke": smoke,
                               "server_pid": server.pid, "ready_at": time.time()})
                    command = [sys.executable, "-m", "RQs.RQ3_9.src.main", "run"] + (["--smoke"] if smoke else [])
                    with (root / "logs" / ("runner." + stamp + ".log")).open("w") as driverlog:
                        runner = subprocess.Popen(command, cwd=ROOT, stdout=driverlog,
                                                  stderr=subprocess.STDOUT, start_new_session=True)
                        write_json(root / "supervisor.json", {"status": "runner_started", "smoke": smoke,
                                   "server_pid": server.pid, "runner_pid": runner.pid, "time": time.time()})
                        while runner.poll() is None and not stop.is_set() and time.monotonic() < deadline:
                            if server.poll() is not None:
                                raise RuntimeError("Model server died during inference")
                            stop.wait(2)
                        if runner.poll() is None:
                            status = "interrupted" if stop.is_set() else "bounded_timeout"
                            os.kill(runner.pid, signal.SIGTERM)
                            try:
                                runner.wait(timeout=2 if smoke else 330)
                            except subprocess.TimeoutExpired:
                                stop_owned(runner)
                        elif runner.returncode:
                            raise RuntimeError("Request runner exited: " + str(runner.returncode))
                        else:
                            status = read_json(root / "phase.json")["status"]
        except Exception as exc:
            write_json(root / "supervisor.json", {"status": "failed", "error": repr(exc),
                       "smoke": smoke, "elapsed": time.monotonic()-started})
            raise
        finally:
            if runner is not None and runner.poll() is None:
                stop_owned(runner)
            if server is not None:
                stop_owned(server)
        if status == "bounded_timeout":
            for p in (root / "partial").glob("*.json"):
                record = read_json(p)
                record["supervisor_status"] = "timeout_partial"
                write_json(p, record)
        report = {"status": status, "smoke": smoke, "elapsed": time.monotonic()-started,
                  "deadline_seconds": c["smoke_seconds"] if smoke else None}
        write_json(root / "supervisor.json", report)
        return report


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["register", "static", "prepare", "cpu", "supervise", "run", "review-smoke", "status", "analyze"])
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    c = config()
    from . import gates, tests
    if args.command == "register":
        result = register(c)
        runtime(c)
        result = {"status": "registered", "cases": len(result["cases"]), "positions": c["formal_positions"]}
    elif args.command == "static":
        result = gates.static(c)
    elif args.command == "prepare":
        result = prepare(c)
    elif args.command == "cpu":
        result = tests.cpu(c)
    elif args.command == "supervise":
        result = supervise(c, args.smoke)
    elif args.command == "run":
        result = run(c, args.smoke)
    elif args.command == "review-smoke":
        result = gates.review_smoke(c)
    elif args.command == "analyze":
        result = gates.analyze(c)
    else:
        result = gates.summarize(c, args.smoke)
    log("finished", command=args.command, result=result)


if __name__ == "__main__":
    cli()

"""RQ3.8 CLI: public export, bounded preparation, qualification and execution."""
from pathlib import Path
import argparse
import json
import os
import pickle
import shutil
import time
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

from . import exps, gates
from .utils import (ROOT, MODELS, VERSION, config, exclusive, immutable_json,
                    interleaved, load_roster, make_profile, path, prior_calls,
                    read_json, sha_file, stable_hash, write_json, logical_key, read_flag,
                    bind_client_endpoint, supervisor_failure_record, case_arms, base_arm, experiment_for, ALL_ARMS,
                    FORMAL_ROSTER, formal_rows)


def initialize(c):
    root = path(c["results"])
    # Keep the smoke-era three-shard roster immutable. The four-job successor
    # changes only operational case ownership, never cohort or model input.
    roster_path = path(c["preparation"])/FORMAL_ROSTER
    if not roster_path.exists():
        immutable_json(roster_path, load_roster(c))
    roster = read_json(roster_path)
    budget_path = root/"budget_formal4_q3g1.json"
    if not budget_path.exists():
        prior = prior_calls(c)
        # Disjoint job caps include interrupted attempts, not just outcomes.
        reserve = c["budget"]["reserve"]
        jobs = [(m,s) for m in MODELS for s in range(c["execution"]["formal_shards"][m])]
        caps = {f"{m}_s{s}": sum(len(case_arms(c,r)) for r in formal_rows(c,roster,m,s))
                + reserve//len(jobs) + int(i < reserve % len(jobs))
                for i,(m,s) in enumerate(jobs)}
        planned = sum(len(case_arms(c,r)) for r in roster["cases"])*len(MODELS)
        if planned != c["budget"]["formal_upper"] or sum(caps.values()) + 18 > c["budget"]["new_round_limit"]:
            raise ValueError("Expanded roster exceeds registered new-round budget")
        immutable_json(budget_path, {"prior": prior, "caps": caps, "smoke_cap": 18,
                                    "hard_limit": c["budget"]["new_round_limit"], "planned": planned,
                                    "historical_ledger": c["old_ledger"],
                                    "historical_snapshot_not_all_project_calls": True,
                                    "authority": c["budget"]["authority"],
                                    "maximum_plus_prior_snapshot": prior+sum(caps.values())+18})
    runtime = make_profile(c, root/c["runtime_profile"])
    return {"roster": roster, "runtime": runtime, "budget": read_json(budget_path)}


def inherited_export(c, row):
    """Read the exact prior public anchor; do not silently reselect on test.

    Eval uses the portable export. Test uses committed RQ3.7 public caches.
    Missing predecessor data is a preparation blocker, never a request-time
    fallback or permission to invent/reconstruct a different comparison arm.
    """
    oid = row["opaque_incident_id"]
    source_root = path(c["parent_export"])
    if (source_root/"public"/(oid+".json")).exists():
        parent = read_json(source_root/"public"/(oid+".json"))
        provenance = read_json(source_root/"audit"/(oid+".json"))
        # Imported immutable audit records retain their original workstation
        # path. Rebase only that known repository prefix; verify bytes below.
        source_name = str(provenance["source_context"])
        source_name = source_name.removeprefix("/home/lglsj/CanvasRCA_nibi/")
        source = path(source_name)
        if sha_file(source) != provenance["context_sha256"]:
            raise ValueError("Parent public context differs from frozen export")
        context = pickle.loads(source.read_bytes())
        return parent, context, source, source_root/"private"/(oid+".json")
    if row.get("cohort") != "test":
        raise FileNotFoundError("Missing frozen eval public export: "+oid)
    prior = ROOT/"RQs/RQ3_7/results/fusion_v2_pruned"
    registration = read_json(prior/"registration.json")
    from RQs.RQ3_7.src.utils import digest as predecessor_digest
    cache = prior/"public_cache"/predecessor_digest(registration["contract"])/(oid+".pkl")
    if not cache.exists():
        raise FileNotFoundError("Locked regression requires frozen RQ3.7 public_cache (copy it to Nibi, no reselection): "+str(cache))
    stored = pickle.loads(cache.read_bytes())
    view = stored["view"]
    parent = {"system": view.system, "parts": list(view.parts), "metrics": list(view.metric_facts),
              "candidates": list(view.candidates), "selected_relations": list(view.relations), "full_relations": []}
    roots = (ROOT/"RQs/RQ3_4/results/integrated_v1", prior)
    for base in roots:
        source = base/"contexts"/(oid+".pkl")
        marker = base/"preparation_flags"/(oid+".json")
        if source.exists() and marker.exists() and read_json(marker).get("status") == "done":
            context = pickle.loads(source.read_bytes())
            if context.get("opaque_incident_id") != oid or context["prepared"].private:
                raise ValueError("Wrong/private predecessor context")
            private = next((b/"private"/(oid+".json") for b in roots if (b/"private"/(oid+".json")).exists()), None)
            if private is None:
                raise FileNotFoundError("Missing evaluator-private predecessor record: "+oid)
            return parent, context, source, private
    raise FileNotFoundError("Missing committed predecessor context: "+oid)


def export_one(args):
    c, row = args
    root = path(c["preparation"])
    oid = row["opaque_incident_id"]
    flag = root/"export_flags"/(oid+".json")
    if flag.exists():
        return read_json(flag)
    started = time.monotonic()
    parent, context, source, private_path = inherited_export(c, row)
    from renderer.exps import export_public_case
    evidence, audit = export_public_case(row, context, source)
    bundle = exps.public_bundle(parent, evidence)
    validation = gates.check_visible_bundle(bundle)
    immutable_json(root/"public"/(oid+".json"), bundle)
    write_json(root/"audit"/(oid+".json"), {"source": audit, "validation": validation,
                                         "parent_public_hash": stable_hash(parent),
                                         "features": exps.public_features(evidence)})
    # Only after the public compiler finishes: isolated evaluator data, never
    # passed into renderer/model_parts. Kept out of HTML and public artifacts.
    private = read_json(private_path)
    immutable_json(root/"private"/(oid+".json"), private)
    result = {"status": "done", "case": oid, "cards": len(evidence["cards"]),
              "seconds": time.monotonic()-started, "facts_hash": bundle["facts_hash"]}
    write_json(flag, result)
    print(json.dumps({"export": result}), flush=True)
    return result


def render_capture(evidence_path, design_path, output):
    """One bounded retry for Chromium's demonstrated transient screenshot error."""
    import subprocess
    from renderer.main import render
    for attempt in range(2):
        try:
            result = render(evidence_path, design_path, output)
            result["capture_attempts"] = attempt+1
            write_json(output/"manifest.json", result)
            return result
        except subprocess.CalledProcessError:
            log = output/"browser.log"
            if attempt or not log.exists() or "Unable to capture screenshot" not in log.read_text():
                raise
            # Same inputs, font, browser, geometry and scale. Keep the failure.
            output.rename(output.with_name(output.name+".capture_failed."+str(time.time_ns())))


def render_one(args):
    c, row = args
    root = path(c["preparation"])
    oid = row["opaque_incident_id"]
    flag = root/"render_flags"/(oid+".json")
    if flag.exists():
        return read_json(flag)
    bundle = read_json(root/"public"/(oid+".json"))
    arms = {}
    cache = {}
    # Mechanism PNGs only for its hash subset (plus shared smoke cases).
    needed = set(ALL_ARMS if row.get("smoke_case") else case_arms(c,row))
    for arm in sorted(needed & exps.GRAPHICAL):
        try:
            evidence, design = exps.fixed_slot_design(bundle["evidence"], arm)
        except exps.CapacityError as exc:
            arms[arm] = {"status": "design_infeasible", "reason": str(exc)}
            continue
        signature = stable_hash([evidence, design])
        if signature in cache:
            arms[arm] = {**cache[signature], "intervention": base_arm(arm),
                         "shared_with": next(k for k,v in arms.items() if v.get("png") == cache[signature]["png"])}
            continue
        inputs = root/"render_inputs"/oid/arm
        immutable_json(inputs/"evidence.json", evidence)
        immutable_json(inputs/"design.json", design)
        out = root/"renders"/oid/arm
        if (out/"manifest.json").exists() and read_json(out/"manifest.json").get("status") == "passed":
            report = read_json(out/"manifest.json")
            if report["evidence_hash"] != stable_hash(evidence) or report["design_hash"] != stable_hash(design):
                raise ValueError("Existing render has different public content/design")
        else:
            # Preserve interrupted/failed renders as a scoped recoverable sibling.
            if out.exists():
                out.rename(out.with_name(arm+".incomplete."+str(time.time_ns())))
            report = render_capture(inputs/"evidence.json", inputs/"design.json", out)
        if report["status"] != "passed":
            raise ValueError("Browser artifact qualification failed")
        entry = {"png": str((out/"dashboard.png").relative_to(root)),
                 "png_sha256": report["png_sha256"], "source_png": report["source_png"],
                 "evidence_hash": stable_hash(evidence), "design_hash": stable_hash(design),
                 "suppressed_visual_bindings": report.get("suppressed_visual_bindings", []),
                 "intervention": base_arm(arm), "renderer_seconds": report.get("renderer_seconds")}
        arms[arm] = entry
        cache[signature] = entry
    result = {"status": "done", "case": oid, "arms": arms, "facts_hash": bundle["facts_hash"]}
    write_json(flag, result)
    print(json.dumps({"rendered": oid, "unique_images": len(cache)}), flush=True)
    return result


def prepare(c, rows, mode, shard=None):
    from vlmrca.run_state import pinned_process_map
    root = path(c["preparation"])
    # Formal shards are disjoint. Smoke retains its own lock and cannot race
    # with an active formal allocation under the registered queue order.
    lock = mode+(".s"+str(shard) if shard is not None else "")+".lock"
    with exclusive(root/lock):
        if mode == "export":
            return pinned_process_map(export_one, [(c,r) for r in interleaved(rows)], max_workers=8)
        return pinned_process_map(render_one, [(c,r) for r in interleaved(rows)], max_workers=8)


def terminal(root, model, oid, arm, smoke):
    key = logical_key(model, oid, arm, smoke)
    flag = read_flag(root/"flags"/(key+".json"))
    if flag is not None:
        if flag.get("logical_key") != key:
            raise ValueError("Terminal identity mismatch")
        if flag["status"] == "fail" and flag.get("failure_class") != "request_timeout":
            raise RuntimeError("Recorded infrastructure failure needs diagnosis, not automatic retry")
    return flag


def pending_rows(root, rows, model, arms, smoke):
    # No public context, PNG, output or large-file hash reads on this path.
    return [r for r in rows if any(terminal(root, model, r["opaque_incident_id"], a, smoke) is None
                                  for a in (arms(r) if callable(arms) else arms))]


def execute_case(c, row, model, arms, root, ledger, stop, smoke):
    from RQs.RQ3_1.src.main import (_request_envelope, bind_task_request,
                                   run_registered_call, score_response_callback)
    from RQs.RQ3_3.src.exps import request_descriptor
    from RQs.RQ3_3.src.main import timeout_exception
    oid = row["opaque_incident_id"]
    if not pending_rows(root, [row], model, arms, smoke):
        return
    prep = path(c["preparation"])
    bundle = read_json(prep/"public"/(oid+".json"))
    renders = read_json(prep/"render_flags"/(oid+".json"))
    seen = {}
    for arm in arms:
        repeat = arm.endswith("_REPEAT")
        previous = terminal(root, model, oid, arm, smoke)
        if previous is not None:
            if previous.get("request_hash") and previous["status"] == "done" and not repeat:
                seen[previous["request_hash"]] = previous
            continue
        if stop.is_set():
            return
        if shutil.disk_usage(root).free < c["execution"]["min_free_disk_gib"]*1024**3:
            raise OSError("Disk reserve reached; stop submitting and drain")
        key = logical_key(model, oid, arm, smoke)
        entry = renders["arms"].get(arm)
        if entry and entry.get("status") == "design_infeasible":
            write_json(root/"flags"/(key+".json"), {"logical_key":key,"case":oid,"model":model,"arm":arm,
                "status":"design_infeasible","reason":entry["reason"],"new_calls":0,"end_to_end_mrr":0})
            continue
        png = (prep/entry["png"]).read_bytes() if arm in exps.GRAPHICAL else None
        parts = exps.model_parts(bundle, arm, png)
        envelope = _request_envelope(model, system=bundle["system"])
        envelope["policy_version"] = VERSION
        actual = request_descriptor(parts, bundle["system"], envelope, model)
        projection = {"facts": bundle["facts_hash"], "request": stable_hash(actual)}
        task = {"experiment": ("smoke_" if smoke else "")+experiment_for(c,row,arm), "model": model,
                "case": row, "dimensions": {"arm": arm, "replicate": int(repeat)}}
        bound = bind_task_request(task, actual, stable_hash(projection), projection=projection,
                                  adapter_version=VERSION, version=VERSION)
        common = {"logical_key": key, "case": oid, "model": model, "arm": arm,
                  "request_hash": stable_hash(actual), "facts_hash": bundle["facts_hash"]}
        if common["request_hash"] in seen and not repeat:
            source = seen[common["request_hash"]]
            result = {**common, "status": "done", "call_key": source["call_key"],
                      "reference_logical_key": source["logical_key"], "new_calls": 0}
        else:
            # Public compilation has finished. Only the scoring callback sees labels.
            private = read_json(prep/"private"/(oid+".json"))
            write_json(root/"submissions"/(key+".json"), {**common, "call_key":bound["call_key"], "at": time.time()})
            print(json.dumps({"submitting": oid, "model": model, "arm": arm}), flush=True)
            try:
                output = run_registered_call(bound, parts, envelope, root,
                    score_response=score_response_callback(private, bundle["candidates"]), ledger=ledger)
                result = {**common, "status": "done", "call_key": output["call_key"],
                          "model_status": output["status"]}
            except Exception as exc:
                if timeout_exception(exc):
                    result = {**common, "status": "fail", "failure_class": "request_timeout",
                              "call_key": bound["call_key"], "error": str(exc)}
                elif isinstance(exc, ValueError) and str(exc).startswith("input exceeds context:"):
                    # Proven by the live canonical tokenizer, not a render/parser error.
                    result = {**common, "status": "design_infeasible", "reason": str(exc),
                              "new_calls": 0, "end_to_end_mrr": 0}
                else:
                    stop.set()
                    write_json(root/"flags"/(key+".json"), {**common, "status": "fail",
                        "failure_class": "infrastructure", "call_key": bound["call_key"],
                        "error": f"{type(exc).__name__}: {exc}"})
                    raise
        # The shared transaction drained response/conversation/score/cost first.
        write_json(root/"flags"/(key+".json"), result)
        if result["status"] == "done" and not repeat:
            seen[result["request_hash"]] = result
        print(json.dumps({"terminal": result}), flush=True)


def run_model(c, model, shard, *, smoke=False):
    from vlmrca.run_state import DurableCallRegister, audit_call_artifacts
    init = initialize(c)
    endpoint = bind_client_endpoint(model, init["runtime"]["models"][model])
    print(json.dumps({"client_endpoint": endpoint}), flush=True)
    base = path(c["results"])
    job = "smoke" if smoke else f"{model}_s{shard}"
    root = base/job
    rows = init["roster"]["smoke"] if smoke else formal_rows(c,init["roster"],model,shard)
    arms = lambda row: case_arms(c,row,smoke)
    cap = init["budget"]["smoke_cap"] if smoke else init["budget"]["caps"][job]
    with exclusive(root/"runner.lock"):
        remaining = pending_rows(root, rows, model, arms, smoke)
        if not remaining:
            return {"status": "complete", "new_work": 0}
        ledger = DurableCallRegister(root/"calls.sqlite", limit=cap, scope=VERSION)
        # Only unfinished transactions are recovered; complete flags are untouched.
        recovery = ledger.recover_persisted(root, audit=audit_call_artifacts)
        write_json(root/f"recovery.{model}.json", recovery)
        stop = threading.Event()
        old_handlers = {sig: signal.signal(sig, lambda *_: stop.set())
                        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1)}
        errors = []
        iterator = iter(interleaved(remaining))
        try:
            with ThreadPoolExecutor(max_workers=c["execution"]["concurrency"]) as pool:
                active = set()
                def replenish():
                    while not stop.is_set() and len(active) < c["execution"]["concurrency"]:
                        row = next(iterator, None)
                        if row is None:
                            break
                        active.add(pool.submit(execute_case, c, row, model, arms(row), root, ledger, stop, smoke))
                replenish()
                while active:
                    finished, active = wait(active, timeout=30, return_when=FIRST_COMPLETED)
                    for future in finished:
                        try:
                            future.result()
                        except Exception as exc:
                            stop.set()
                            errors.append(f"{type(exc).__name__}: {exc}")
                    replenish()
        finally:
            for sig, old in old_handlers.items():
                signal.signal(sig, old)
        missing = pending_rows(root, rows, model, arms, smoke) if not errors else []
        report = {"status": "failed" if errors else "interrupted" if missing else "complete",
                  "errors": errors, "model": model, "remaining_cases": len(missing),
                  "accounting": ledger.summary()}
        write_json(root/f"phase.{model}.json", report)
        if errors:
            raise RuntimeError(errors[0])
        return report


def supervisor_deadline(c, started, smoke):
    """Smoke lifetime belongs to Slurm, not a second hidden script timer."""
    return float("inf") if smoke else started+c["execution"]["max_job_seconds"]-360


def supervise(c, model=None, shard=0, smoke=False):
    """Bounded process lifecycle, readiness and work submission are distinct."""
    import subprocess
    import sys
    from RQs.RQ3_6.src.utils import model_probe, endpoint_vacant, stop_owned
    init = initialize(c)
    base = path(c["results"])
    root = base/("smoke" if smoke else f"{model}_s{shard}")
    with exclusive(root/"supervisor.lock"), supervisor_failure_record(root, smoke):
        gates.require_execution(c, smoke=smoke)
        start = time.monotonic()
        deadline = supervisor_deadline(c, start, smoke)
        if smoke:
            write_json(root/"supervisor.json", {"status": "running", "qualification": "incomplete",
                       "smoke": True, "job_id": os.environ.get("SLURM_JOB_ID"),
                       "internal_deadline_seconds": None, "started": time.time()})
        stop = threading.Event()
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
            signal.signal(sig, lambda *_: stop.set())
        models = MODELS if smoke else [model]
        outcome = "complete"
        for tag in models:
            rows = init["roster"]["smoke"] if smoke else formal_rows(c,init["roster"],model,shard)
            arms = lambda row: case_arms(c,row,smoke)
            remaining = pending_rows(root, rows, tag, arms, smoke)
            if not remaining:
                continue
            if not smoke:
                gates.require_prepared(c, remaining)
            if stop.is_set() or time.monotonic() >= deadline:
                outcome = "bounded_timeout" if smoke else "interrupted"
                break
            spec = init["runtime"]["models"][tag]
            endpoint = bind_client_endpoint(tag, spec)
            write_json(root/"endpoints"/(tag+".json"), endpoint)
            print(json.dumps({"allocated_endpoint": endpoint}), flush=True)
            if not endpoint_vacant(spec):
                raise RuntimeError("Allocated port is occupied; will not attach to or kill another service")
            (root/"logs").mkdir(parents=True, exist_ok=True)
            stamp = str(time.time_ns())
            server = runner = None
            try:
                with (root/"logs"/f"server.{tag}.{stamp}.log").open("w") as log:
                    server = subprocess.Popen(["bash", "RQs/RQ3_8/scripts/serve.sh", tag],
                                              cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    while not model_probe(spec):
                        if server.poll() is not None:
                            raise RuntimeError(f"vLLM startup exited {server.returncode}; inspect server log")
                        if stop.is_set() or time.monotonic() >= deadline:
                            break
                        stop.wait(min(5, max(0, deadline-time.monotonic())))
                    if stop.is_set() or time.monotonic() >= deadline:
                        outcome = "bounded_timeout" if smoke else "interrupted"
                        break
                    gates.attest(c, root, tag, server.pid)
                    print(json.dumps({"ready": tag, "elapsed": time.monotonic()-start}), flush=True)
                    command = [sys.executable, "-m", "RQs.RQ3_8.src.main", "run", "--model", tag, "--shard", str(shard)]
                    if smoke:
                        command.append("--smoke-cases")
                    with (root/"logs"/f"runner.{tag}.{stamp}.log").open("w") as driverlog:
                        runner = subprocess.Popen(command, cwd=ROOT, stdout=driverlog,
                                                  stderr=subprocess.STDOUT, start_new_session=True)
                        while runner.poll() is None and not stop.is_set() and time.monotonic() < deadline:
                            stop.wait(min(5, max(0, deadline-time.monotonic())))
                        if runner.poll() is None:
                            outcome = "bounded_timeout" if smoke else "interrupted"
                            if smoke:
                                os.kill(runner.pid, signal.SIGTERM)
                                try:
                                    runner.wait(timeout=10)
                                except subprocess.TimeoutExpired:
                                    stop_owned(runner)
                            else:
                                os.kill(runner.pid, signal.SIGTERM)
                                try:
                                    runner.wait(timeout=330)
                                except subprocess.TimeoutExpired:
                                    stop_owned(runner)
                            break
                        if runner.returncode:
                            raise RuntimeError(f"Inference driver exited {runner.returncode}")
            finally:
                if runner is not None and runner.poll() is None:
                    stop_owned(runner)
                if server is not None:
                    stop_owned(server)
        report = {"status": outcome, "seconds": time.monotonic()-start, "smoke": smoke}
        if smoke and stop.is_set():
            report["status"] = outcome = "interrupted"
        if smoke:
            report.update(gates.finish_smoke(c, root, outcome))
        write_json(root/"supervisor.json", report)
        if smoke and report["qualification"] != "passed":
            raise RuntimeError("Smoke incomplete or failed; inspect supervisor.json and server logs")
        return report


def submit(c, mode, attempt=1):
    import subprocess
    root = path(c["results"])
    authority = c["submission_authorization"]
    allowed = authority["status"] == "runtime_authorized" or (
        mode == "smoke" and authority["status"] == "smoke_only_authorized")
    if not allowed:
        raise RuntimeError("Only the explicitly authorized submission mode is allowed; CPU/formal jobs await separate instruction.")
    account = os.environ.get("CANVASRCA_SLURM_ACCOUNT")
    if not account:
        raise ValueError("Set the authorized CANVASRCA_SLURM_ACCOUNT explicitly")
    maximum = c["cpu_qualification"]["max_jobs"] if mode == "cpu" else c["smoke"]["max_jobs"] if mode == "smoke" else 1
    if not 1 <= attempt <= maximum:
        raise ValueError("User-authorized submission limit exceeded")
    initialize(c)
    # Authorized direct smoke prepares inputs and checks actual processors in
    # its GPU allocation; it does not run or claim a CPU regression pass.
    if mode == "formal":
        gates.require_execution(c, smoke=False)
        # Each allocation prepares only its own disjoint cases before it starts
        # vLLM. The supervisor checks those durable flags before model loading.
    else:
        gates.require_static(c)
    jobs = ([(m,s) for m in MODELS for s in range(c["execution"]["formal_shards"][m])]
            if mode == "formal" else [(mode,0)])
    history_roots = [root.parent/name/"slurm" for name in c["submission_authorization"]["qualification_roots"]]
    with exclusive(root/"submissions.lock"):
        submitted_qwen = {}
        if mode == "smoke" and authority["status"] == "smoke_only_authorized":
            current = list((root/"slurm").glob("rq38*-smoke-attempt*.json"))
            requested = root/"slurm"/f"rq38v7-smoke-attempt{attempt}.json"
            if requested not in current and len(current) >= authority["new_smoke_jobs"]:
                raise RuntimeError("The specifically authorized v7 smoke job has already been submitted")
        for model, shard in jobs:
            name = f"rq38v7-{model}-{shard}" if mode == "formal" else f"rq38v7-{mode}-attempt{attempt}"
            destination = root/"slurm"/(name+".json")
            if destination.exists():
                state = read_json(destination)
                if state.get("job_id"):
                    print(json.dumps({"already_submitted":state}), flush=True)
                    continue
                raise RuntimeError("Unacknowledged submission intent: query Slurm by unique job name before retry")
            if mode == "formal":
                previous = [p for folder in history_roots for p in folder.glob("rq38*-*.json")
                            if any(tag in p.name for tag in MODELS)]
                if len(previous) >= c["execution"]["max_formal_jobs"]:
                    raise RuntimeError("Four formal-job allowance exhausted across version roots")
            else:
                # Count intentions too: an interrupted sbatch acknowledgement
                # must not accidentally permit another allocation.
                previous = [p for folder in history_roots for p in folder.glob(f"rq38*-{mode}-attempt*.json")]
                if len(previous) >= maximum:
                    raise RuntimeError("Qualification job allowance exhausted")
                for previous_path in previous:
                    prior = read_json(previous_path)
                    if prior.get("job_id"):
                        queue = subprocess.run(["squeue", "-h", "-j", prior["job_id"], "-o", "%T"], capture_output=True, text=True)
                        if queue.returncode and "Invalid job id" not in queue.stderr:
                            raise RuntimeError("Cannot establish previous job state: "+queue.stderr)
                        if queue.stdout.strip():
                            raise RuntimeError("Previous qualification job is still active; do not duplicate")
                        accounting = subprocess.check_output(["sacct", "-X", "-n", "-P", "-j", prior["job_id"], "-o", "State"], text=True)
                        terminal_states = {"FAILED", "COMPLETED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE", "CANCELLED"}
                        state_names = [line.strip().split("|")[0].split()[0] for line in accounting.splitlines() if line.strip()]
                        if not state_names or any(state not in terminal_states for state in state_names):
                            raise RuntimeError("Previous job not confirmed terminal by Slurm accounting")
                    elif prior.get("status") != "rejected":
                        raise RuntimeError("Resolve ambiguous previous submission first")
            (root/"logs").mkdir(parents=True, exist_ok=True)
            command = ["sbatch", "--parsable", "--account", account, "--job-name", name,
                       "--output", str(root/"logs"/(name+"-%j.log"))]
            if mode == "cpu":
                command += ["--partition", "cpubase_bycore_b1", "RQs/RQ3_8/scripts/cpu_job.sh"]
            elif mode == "smoke":
                command += ["--partition", "gpubase_bygpu_b1", "--time=00:30:00", "RQs/RQ3_8/scripts/gpu_job.sh", "smoke"]
            else:
                command += ["--partition", "gpubase_bygpu_b2", "--time=08:00:00", "--mem=192G", "--signal=B:USR1@360"]
                # Qwen first prepares the same shard's public inputs. Gemma
                # follows even if a Qwen inference fails; it may then reuse or
                # finish preparation without racing the same source files.
                if model == "gemma-4-31b":
                    predecessors = []
                    for q_shard in range(c["execution"]["formal_shards"]["qwen3.8-27b"]):
                        predecessor = submitted_qwen.get(q_shard)
                        if predecessor is None:
                            predecessor_path = root/"slurm"/(f"rq38v7-qwen3.8-27b-{q_shard}.json")
                            predecessor = read_json(predecessor_path).get("job_id") if predecessor_path.exists() else None
                        if not predecessor:
                            raise RuntimeError("Qwen predecessor job has no acknowledged ID")
                        predecessors.append(predecessor)
                    command.append("--dependency=afterany:"+":".join(predecessors))
                command += ["RQs/RQ3_8/scripts/gpu_job.sh", "formal", model, str(shard)]
            write_json(destination, {"status":"submission_intent", "command":command,"time":time.time()})
            submitted = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
            if submitted.returncode:
                write_json(destination, {"status":"rejected", "command":command,"error":submitted.stderr})
                raise RuntimeError(submitted.stderr)
            job_id = submitted.stdout.strip().split(";")[0]
            if not job_id.isdigit():
                raise RuntimeError("Unknown sbatch acknowledgement; do not automatically duplicate job")
            write_json(destination, {"status":"submitted", "job_id":job_id, "command":command, "time":time.time()})
            if mode == "formal" and model == "qwen3.8-27b":
                submitted_qwen[shard] = job_id
            print(json.dumps({"submitted":name,"job_id":job_id}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "static", "export", "render", "preflight", "run", "supervise", "analyze", "submit", "seal-cpu"])
    parser.add_argument("--smoke-cases", action="store_true")
    parser.add_argument("--model", choices=MODELS)
    parser.add_argument("--shard", type=int, choices=range(3), default=0)
    parser.add_argument("--mode", choices=["cpu", "smoke", "formal"], default="cpu")
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    c = config()
    if args.command == "static":
        result = gates.require_static(c)
        print(json.dumps({"status": result["status"], "source_lines": result["source_lines"]}))
        return
    init = initialize(c)
    rows = init["roster"]["smoke" if args.smoke_cases else "cases"]
    if args.command == "init":
        print(json.dumps({"cases": len(init["roster"]["cases"]), "budget": init["budget"]}))
    elif args.command in {"export", "render"}:
        if args.smoke_cases:
            selected = rows
        elif args.model:
            selected = formal_rows(c,init["roster"],args.model,args.shard)
        else:
            parser.error("Formal preparation requires --model and --shard")
        prepare(c, selected, args.command, None if args.smoke_cases else args.shard)
    elif args.command == "preflight":
        result = gates.processor_preflight(c, path(c["preparation"]), rows)
        print(json.dumps({"status": result["status"], "seconds": result["seconds"]}))
        if result["status"] != "passed":
            raise SystemExit(1)
    elif args.command in {"run", "supervise"}:
        if not args.smoke_cases and not args.model:
            parser.error("Formal runs require --model")
        if args.command == "run":
            if not args.model:
                parser.error("Model worker requires --model")
            run_model(c, args.model, args.shard, smoke=args.smoke_cases)
        else:
            supervise(c, args.model, args.shard, smoke=args.smoke_cases)
    elif args.command == "submit":
        submit(c, args.mode, args.attempt)
    elif args.command == "seal-cpu":
        write_json(path(c["results"])/"qualification/cpu-source.json", gates.source_contract())
    else:
        gates.analyze(c)


if __name__ == "__main__":
    main()

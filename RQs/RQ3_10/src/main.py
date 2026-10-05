"""Explicit commands; static/register cannot launch preparation or model processes."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
import os
import pickle
import shutil
import signal
import subprocess
import sys
import threading
import time

from . import exps
from .utils import (ROOT, VERSION, MODEL, ARMS, METRICS, config, path, register, runtime, flag, logical_key,
                    stable_hash, sha_file, read_json, write_json, immutable_json, exclusive, source_contract, log)

CALL_IDENTITIES = {}  # Request bookkeeping only, populated before each real call.


def load_public_pool(c, row, bundle):
    """Only committed project-owned public pickle. No private file is opened."""
    oid = row["opaque_incident_id"]
    audit = read_json(path(c["parent_export"]) / "audit" / (oid+".json"))
    name = audit["source_context"].removeprefix(str(ROOT)+"/")
    file = path(name)
    # Targeted preparation check only; skipped entirely after its small commit.
    if sha_file(file) != audit["context_sha256"]:
        raise ValueError("Frozen full public context changed")
    context = pickle.loads(file.read_bytes())
    if context.get("opaque_incident_id") != oid:
        raise ValueError("Full-pool context identity mismatch")
    pool = exps.pool_from_public(bundle, context)
    return pool, {"context_path": str(file.relative_to(ROOT)), "context_sha256": audit["context_sha256"]}


def measured_controls(c, row, bundle, pool):
    """Read exactly one per-case Metrics projection; never logs, traces or raw tables."""
    import numpy as np
    import pandas as pd
    import pyarrow.parquet as pq
    selected, selection = exps.select_controls(pool, c)
    if not selected:
        return [], {"selection": selection, "metric_source": None}
    audit = read_json(path(c["parent"]) / "audit" / (row["opaque_incident_id"]+".json"))
    directory = Path(audit["source"]["topology"]["source_directory"])
    if not directory.is_absolute():
        directory = ROOT/directory
    expected = ROOT/"build/local_processed_v3/public"/row["dataset"]/"cases"/row["opaque_incident_id"]
    if directory.resolve()!=expected.resolve():
        raise ValueError("Unexpected canonical public Metrics source")
    file = directory/"metrics.parquet"
    available = set(pq.read_schema(file).names)
    columns = {o["source_key"] for o in selected}
    entities = {o["entity"] for o in selected}
    counters = {o["source_key"] for o in pool.observations if o["region"]=="M"
                and o["entity"] in entities and o["semantic"] in c["activity_counters"]}
    if not columns.issubset(available):
        raise ValueError("Full-pool anonymous binding has no corresponding source column")
    columns |= counters & available
    frame = pq.read_table(file, columns=["timestamp", *sorted(columns)]).to_pandas()
    clock = pd.to_numeric(frame["timestamp"], errors="coerce").to_numpy(dtype=float)
    finite = clock[np.isfinite(clock)]
    if not finite.size:
        raise ValueError("No public observation clock")
    clock = clock-float(np.min(finite))
    if not pool.window[0] == 0 or not 0<pool.window[1]<pool.window[2]<=float(np.max(clock[np.isfinite(clock)]))+1:
        raise ValueError("Public context window is outside source clock")
    for col in columns:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    activities = exps.activity_for(pool, selected, frame, clock, c)
    records, refs = [], []
    for o in selected:
        r = exps.measure(o, frame[o["source_key"]].to_numpy(dtype=float), clock, pool.window, activities[o["entity"]], c)
        if any(r[name]!=o["values"][name] for name in ("reference_samples","current_samples")):
            raise ValueError("Cached public split and source sampling coverage differ")
        # Full-pool extraction records 8-significant-digit medians. Check binding
        # against that known precision; do not alter the new actual operands.
        for key, name in (("reference", "reference_median"), ("current", "current_median")):
            previous = o["values"].get(name)
            if previous is not None and r[key] is not None and not np.isclose(previous, r[key], rtol=2e-7, atol=1e-12):
                raise ValueError("Full-pool/source entity or public window mismatch")
        records.append(r)
        refs.append({"id": r["id"], "source_column": o["source_key"], "source_observation": o["id"]})
    return records, {"selection": selection, "metric_source": str(file), "columns_read": len(columns)+1,
                     "rows_read": len(frame), "provenance": refs, "source_window": list(pool.window),
                     "source_metric_columns":len(available)-1,
                     "cached_metric_observations":sum(o["region"]=="M" for o in pool.observations)}


def prepare_one(args):
    c, row = args
    root, oid = path(c["preparation"]), row["opaque_incident_id"]
    marker = root/"flags"/(oid+".json")
    if marker.exists():
        saved = read_json(marker)
        if saved.get("status")!="done" or saved.get("version")!=VERSION:
            raise ValueError("Noncommitted or foreign preparation flag")
        return saved
    started = time.monotonic()
    parent = path(c["parent"])
    if read_json(parent/"export_flags"/(oid+".json"))["status"]!="done":
        raise ValueError("Predecessor public export not committed")
    bundle = read_json(parent/"public"/(oid+".json"))
    from RQs.RQ3_8.src.gates import check_visible_bundle
    check_visible_bundle(bundle)
    pool, provenance = load_public_pool(c, row, bundle)
    records, measurement_audit = measured_controls(c, row, bundle, pool)
    payload, cpu = exps.visible_payload(pool, records, c)
    public = {"version": VERSION, "system": bundle["system"], "candidates": bundle["candidates"],
              "facts_hash": bundle["facts_hash"], "base_evidence": bundle["evidence"], "payload": payload,
              "texts": exps.compile_texts(bundle, payload), "images": {}, "infeasible": {}}
    audit = {"source": provenance, "measurement": measurement_audit,
             "visible": exps.visible_audit(public), "cpu_ranking": cpu}
    try:
        evidence, designs = exps.designs(payload, c)
    except ValueError as exc:
        if str(exc)!="scope footprint exceeds registered 8192px":
            raise
        evidence, designs = None, {}
        public["infeasible"] = {a: str(exc) for a in exps.VISUAL}
    from RQs.RQ3_8.src.main import render_capture
    for arm, design in designs.items():
        inputs = root/"render_inputs"/oid/arm
        immutable_json(inputs/"evidence.json", evidence)
        immutable_json(inputs/"design.json", design)
        output = root/"renders"/oid/arm
        if output.exists() and (not (output/"manifest.json").exists() or read_json(output/"manifest.json").get("status")!="passed"):
            output.rename(output.with_name(arm+".interrupted."+str(time.time_ns())))
        manifest = read_json(output/"manifest.json") if output.exists() else render_capture(inputs/"evidence.json", inputs/"design.json", output)
        if (manifest.get("status")!="passed" or manifest["evidence_hash"]!=stable_hash(evidence)
                or manifest["design_hash"]!=stable_hash(design)):
            raise ValueError("Actual render disagrees with its complete evidence/design")
        public["images"][arm] = {"path": str((output/"dashboard.png").relative_to(root)), "sha256": manifest["png_sha256"]}
    identities, canonical = {}, {}
    for arm in ARMS:
        if arm in public["infeasible"]:
            canonical[arm] = arm
            continue
        png = (root/public["images"][arm]["path"]).read_bytes() if arm in public["images"] else None
        parts = exps.parts_for(public, arm, png)
        signature = stable_hash([{**p, "png": stable_hash(p["png"])} if "png" in p else p for p in parts])
        canonical[arm] = identities.setdefault(signature, arm)
    public["canonical_arms"] = canonical
    immutable_json(root/"public"/(oid+".json"), public)
    write_json(root/"audit"/(oid+".json"), audit)
    # Deliberately AFTER all model-visible facts and images have been built.
    immutable_json(root/"private"/(oid+".json"), read_json(parent/"private"/(oid+".json")))
    done = {"status": "done", "version": VERSION, "case": oid, "seconds": time.monotonic()-started,
            "observations": len(records), "hypotheses": len(payload["hypotheses"]), "canonical_arms": canonical,
            "infeasible": public["infeasible"], "context_excluded": {}, "parent_public_sha256": sha_file(parent/"public"/(oid+".json"))}
    write_json(marker, done)
    log("prepared", **done)
    return done


def prepare(c,smoke=False):
    from vlmrca.run_state import pinned_process_map
    from RQs.RQ3_8.src.utils import interleaved
    rows = register(c)["smoke" if smoke else "cases"]
    with exclusive(path(c["preparation"])/"prepare.lock"):
        results = pinned_process_map(prepare_one, [(c,r) for r in interleaved(rows)], max_workers=c["workers"])
    report = {"status": "complete", "cases": len(results), "no_op_cases": sum(not r["observations"] for r in results),
              "preparation_seconds_sum": sum(r["seconds"] for r in results)}
    write_json(path(c["results"])/"qualification"/("preparation_smoke.json" if smoke else "preparation.json"), report)
    return report


def eligibility_one(args):
    """CPU-only source applicability audit; no private labels, images or calls."""
    from collections import Counter
    c,row=args; oid=row["opaque_incident_id"]
    bundle=read_json(path(c["parent"])/"public"/(oid+".json"))
    pool,_=load_public_pool(c,row,bundle)
    records,measurement=measured_controls(c,row,bundle,pool)
    payload,_=exps.visible_payload(pool,records,c)
    return {"dataset":row["dataset"],"case":oid,"observations":len(records),"no_anchor":not records,
            "status":dict(Counter(r["status"] for r in records)),
            "reasons":dict(Counter(r["reason"] for r in records)),
            "active_observations":sum(r["activity"]["status"]=="observed_active" for r in records),
            "testable":any(h["support"] or h["soft_conflict"] for h in payload["hypotheses"]),
            "soft_conflict":any(h["soft_conflict"] for h in payload["hypotheses"]),
            "stable_active_observations":sum(r["status"]=="stable" for r in records),
            "shared_stable_conflict":any(h["kind"]!="local_instance" and h["soft_conflict"] for h in payload["hypotheses"]),
            "testable_by_kind":{kind:any(h["kind"]==kind and (h["support"] or h["soft_conflict"]) for h in payload["hypotheses"])
                                for kind in ("local_instance","shared_service","shared_host")},
            "source_samples":[[r["reference_samples"],r["current_samples"],r["coverage"]] for r in records],
            "metric_count":measurement.get("source_metric_columns"),"selection":measurement["selection"]}


def eligibility(c):
    from collections import Counter
    from vlmrca.run_state import pinned_process_map
    from RQs.RQ3_8.src.utils import interleaved
    started=time.monotonic()
    rows=pinned_process_map(eligibility_one,[(c,r) for r in interleaved(register(c)["cases"])],max_workers=c["workers"])
    summary={}
    for ds in c["case_counts"]:
        subset=[r for r in rows if r["dataset"]==ds]
        summary[ds]={"cases":len(subset),"no_anchor_cases":sum(r["no_anchor"] for r in subset),
                     "testable_cases":sum(r["testable"] for r in subset),
                     "soft_conflict_cases":sum(r["soft_conflict"] for r in subset),
                     "observations":sum(r["observations"] for r in subset),
                     "active_observations":sum(r["active_observations"] for r in subset),
                     "stable_active_observations":sum(r["stable_active_observations"] for r in subset),
                     "shared_stable_conflict_cases":sum(r["shared_stable_conflict"] for r in subset),
                     "testable_by_kind":{kind:sum(r["testable_by_kind"][kind] for r in subset)
                                         for kind in ("local_instance","shared_service","shared_host")},
                     "reasons":dict(sum((Counter(r["reasons"]) for r in subset),Counter()))}
    report={"status":"complete","source_contract":source_contract(),"cases":rows,"summary":summary,
            "seconds":time.monotonic()-started,"gpu_calls":0,"scope":"public source eligibility only, not formal preparation or full CPU capacity qualification"}
    write_json(path(c["results"])/"qualification/eligibility_audit.json",report)
    return {k:v for k,v in report.items() if k not in {"cases","source_contract"}}


def execute(c, row, arm, public, root, ledger):
    from RQs.RQ3_1.src.main import (_request_envelope, bind_task_request, run_registered_call, score_response_callback)
    from RQs.RQ3_3.src.exps import request_descriptor
    from RQs.RQ3_3.src.main import timeout_exception
    oid = row["opaque_incident_id"]
    if flag(root, oid, arm) is not None:
        return flag(root, oid, arm)
    key = logical_key(oid, arm)
    common = {"case": oid, "arm": arm, "model": MODEL, "logical_key": key}
    excluded = public["infeasible"].get(arm) or public.get("context_excluded", {}).get(arm)
    if excluded:
        value={**common, "status": "design_infeasible", "reason": excluded, "new_calls": 0}
        write_json(root/"flags"/(key+".json"), value)
        return value
    if shutil.disk_usage(root).free<10*1024**3:
        raise OSError("Disk reserve reached; stop submission")
    prep = path(c["preparation"])
    png = (prep/public["images"][arm]["path"]).read_bytes() if arm in public["images"] else None
    parts = exps.parts_for(public, arm, png)
    envelope = _request_envelope(MODEL, system=public["system"])
    envelope["policy_version"] = VERSION
    actual = request_descriptor(parts, public["system"], envelope, MODEL)
    projection = {"base_facts": public["facts_hash"], "payload": stable_hash(public["payload"]), "request": stable_hash(actual)}
    task = {"experiment": ("smoke_" if root.name=="smoke" else "")+c["experiment"],
            "model": MODEL, "case": row, "dimensions": {"arm": arm, "replicate": 0}}
    bound = bind_task_request(task, actual, stable_hash(projection), projection=projection, adapter_version=VERSION, version=VERSION)
    common.update(call_key=bound["call_key"], request_hash=stable_hash(actual), facts_hash=public["facts_hash"])
    CALL_IDENTITIES[bound["call_key"]] = dict(common)
    private = read_json(prep/"private"/(oid+".json"))
    bound["fault_type"] = private.get("fault_type", "unavailable")
    write_json(root/"submissions"/(key+".json"), {**common, "time": time.time()})
    log("submitting", case=oid, arm=arm)
    try:
        result = run_registered_call(bound, parts, envelope, root, ledger=ledger,
            score_response=score_response_callback(private, public["candidates"]))
        score=result["score"]
        value = {**common, "status": "done", "model_status": result["status"], "metrics":score.get("metrics",score)}
    except Exception as exc:
        if timeout_exception(exc):
            value = {**common, "status": "fail", "failure_class": "request_timeout", "error": str(exc)}
        elif isinstance(exc, ValueError) and str(exc).startswith("input exceeds context:"):
            value = {**common, "status": "design_infeasible", "reason": str(exc), "new_calls": 0}
        else:
            write_json(root/"flags"/(key+".json"), {**common, "status": "fail", "failure_class": "infrastructure", "error": repr(exc)})
            raise
    write_json(root/"flags"/(key+".json"), value)
    log("terminal", case=oid, arm=arm, status=value["status"])
    return value


def run(c, smoke=False):
    from vlmrca.run_state import DurableCallRegister, audit_call_artifacts
    from .gates import summarize, require_runtime_attestation, require_qualification
    root = path(c["results"])/("smoke" if smoke else "formal")
    rows = register(c)["smoke" if smoke else "cases"]
    require_qualification(c,smoke)
    runtime(c)
    require_runtime_attestation(c, root)
    from .utils import runtime_io_adapter
    with exclusive(root/"runner.lock"), runtime_io_adapter(root, CALL_IDENTITIES):
        tasks, aliases, inputs, terminal = [], [], {}, {}
        for row in rows:
            oid = row["opaque_incident_id"]
            # ALL terminal flags inspected first. No completed context/request
            # rebuilding, tokenizer, PNG reads, or historical large-file audit.
            states={a:flag(root,oid,a) for a in ARMS}
            terminal.update({logical_key(oid,a):v for a,v in states.items() if v is not None})
            pending = [a for a,v in states.items() if v is None]
            if not pending:
                continue
            marker = read_json(path(c["preparation"])/"flags"/(oid+".json"))
            inputs[oid] = read_json(path(c["preparation"])/"public"/(oid+".json"))
            inputs[oid]["context_excluded"] = marker["context_excluded"]
            for arm in pending:
                canonical = marker["canonical_arms"][arm]
                (tasks if canonical==arm else aliases).append((row,arm) if canonical==arm else (row,arm,canonical))
        ledger = DurableCallRegister(root/"calls.sqlite", scope=VERSION,
                                     limit=c["smoke_attempt_limit"] if smoke else c["formal_attempt_limit"])
        # Only unresolved started calls are reconciled. Completed attempts are
        # never traversed or rehashed; this remains bounded by36 active requests.
        write_json(root/"recovery.json", ledger.recover_persisted(root, audit=audit_call_artifacts))
        log("queue_started", pending=len(tasks), references=len(aliases), smoke=smoke)
        last_report=-1
        def progress(force=False):
            nonlocal last_report
            count=len(terminal); total=len(rows)*len(ARMS); step=int(20*count/total)
            if not force and step<=last_report:
                return
            last_report=step
            metrics={}
            for a in ARMS:
                scored=[v["metrics"] for v in terminal.values() if v["arm"]==a and v.get("metrics")]
                metrics[a]={"n":len(scored),**{m:sum(v[m] for v in scored)/len(scored) if scored else None for m in METRICS}}
            log("progress",completed_positions=count,registered_positions=total,
                bar="["+"#"*step+"-"*(20-step)+"]",percent=100*count/total,metrics_by_arm=metrics,
                scope="operational only; no paired efficacy analysis; only committed flag metrics, no historical request rebuilding")
        progress(True)
        stop = threading.Event()
        old = {s: signal.signal(s, lambda *_: stop.set()) for s in (signal.SIGTERM,signal.SIGINT,signal.SIGUSR1)}
        errors = []
        try:
            tasks.sort(key=lambda x: stable_hash([c["seed"], "dispatch", x[0]["opaque_incident_id"], x[1]]))
            iterator = iter(tasks)
            with ThreadPoolExecutor(max_workers=c["concurrency"]) as executor:
                active = set()
                def refill():
                    while not stop.is_set() and len(active)<c["concurrency"]:
                        item = next(iterator, None)
                        if item is None:
                            break
                        r,a = item
                        active.add(executor.submit(execute,c,r,a,inputs[r["opaque_incident_id"]],root,ledger))
                refill()
                while active:
                    done, active = wait(active, timeout=5, return_when=FIRST_COMPLETED)
                    for job in done:
                        try:
                            value=job.result()
                            if value:
                                terminal[value["logical_key"]]=value
                            progress()
                        except Exception as exc:
                            errors.append(repr(exc)); stop.set()
                    refill()
        finally:
            for sig, handler in old.items():
                signal.signal(sig, handler)
        for r,a,canonical in aliases:
            value = flag(root,r["opaque_incident_id"],canonical)
            if value is not None:
                reference = {**value, "arm":a, "logical_key":logical_key(r["opaque_incident_id"],a),
                             "reference_arm":canonical, "no_op":True, "new_calls":0}
                write_json(root/"flags"/(reference["logical_key"]+".json"),reference)
                terminal[reference["logical_key"]]=reference
        progress(True)
        report = {**summarize(c,smoke), "accounting":ledger.summary(), "errors":errors}
        if errors:
            report["status"]="failed"
        write_json(root/"phase.json",report)
        if errors:
            raise RuntimeError(errors[0])
        return report


def supervise(c, smoke=False):
    """Owned process groups; no model service or formal run on import/static."""
    from RQs.RQ3_6.src.utils import model_probe, endpoint_vacant, stop_owned
    from .gates import require_qualification
    started=time.monotonic()
    root=path(c["results"])/("smoke" if smoke else "formal")
    with exclusive(root/"supervisor.lock"):
        require_qualification(c,smoke)
        rows=register(c)["smoke" if smoke else "cases"]
        if all(flag(root,r["opaque_incident_id"],a) is not None for r in rows for a in ARMS):
            from .gates import summarize
            return {**summarize(c,smoke),"launched_model":False,"reason":"all registered flags terminal"}
        _,spec=runtime(c)
        if not endpoint_vacant(spec):
            raise RuntimeError("Selected port occupied; never kill an unrelated job")
        if smoke:
            # A restart cannot grant another600 seconds to the logical smoke.
            window=root/"logical_smoke_window.json"
            if not window.exists():
                immutable_json(window,{"started_unix_s":time.time(),"seconds":c["smoke_seconds"]})
            saved=read_json(window)
            if saved["seconds"]!=c["smoke_seconds"]:
                raise ValueError("Logical smoke wall budget changed")
            remaining=saved["started_unix_s"]+saved["seconds"]-time.time()
            deadline=time.monotonic()+max(0,remaining)
            if remaining<=0:
                raise RuntimeError("Logical smoke wall budget exhausted; review preserved outcome, never reset")
        else:
            deadline=float("inf")
        stop=threading.Event()
        old={s:signal.signal(s,lambda *_:stop.set()) for s in (signal.SIGTERM,signal.SIGINT,signal.SIGUSR1)}
        server=runner=None
        status="complete"
        (root/"logs").mkdir(parents=True,exist_ok=True)
        stamp=str(time.time_ns())
        try:
            with (root/"logs"/("server."+stamp+".log")).open("w") as file:
                server=subprocess.Popen(["bash","scripts/vllm_vlm/serve_canvasrca_local.sh",MODEL],cwd=ROOT,
                    stdout=file,stderr=subprocess.STDOUT,start_new_session=True)
                write_json(root/"supervisor.json",{"status":"starting","server_pid":server.pid,"smoke":smoke,"started":time.time()})
                while not model_probe(spec):
                    if server.poll() is not None:
                        raise RuntimeError("Model startup exited: "+str(server.returncode))
                    if stop.is_set() or time.monotonic()>=deadline:
                        status="interrupted" if stop.is_set() else "bounded_timeout"; break
                    stop.wait(2)
                if status=="complete":
                    from RQs.RQ3_8.src.gates import attest
                    report=attest(c,root,MODEL,server.pid)
                    report["rq310_source_contract"]=source_contract()
                    write_json(root/"attestation.json",report)
                    log("ready",elapsed=time.monotonic()-started)
                    command=[sys.executable,"-m","RQs.RQ3_10.src.main","run","--execute"]+(["--smoke"] if smoke else [])
                    with (root/"logs"/("runner."+stamp+".log")).open("w") as out:
                        runner=subprocess.Popen(command,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
                        write_json(root/"supervisor.json",{"status":"runner_started","server_pid":server.pid,"runner_pid":runner.pid,
                                                         "time":time.time(),"smoke":smoke})
                        while runner.poll() is None and not stop.is_set() and time.monotonic()<deadline:
                            if server.poll() is not None:
                                raise RuntimeError("Model server died")
                            stop.wait(2)
                        if runner.poll() is None:
                            status="interrupted" if stop.is_set() else "bounded_timeout"
                            os.kill(runner.pid,signal.SIGTERM)
                            try:
                                runner.wait(timeout=0.1 if smoke else 330)
                            except subprocess.TimeoutExpired:
                                stop_owned(runner)
                        elif runner.returncode:
                            raise RuntimeError("Runner exited: "+str(runner.returncode))
                        else:
                            status=read_json(root/"phase.json")["status"]
        except Exception as exc:
            write_json(root/"supervisor.json",{"status":"failed","smoke":smoke,"error":repr(exc),"elapsed":time.monotonic()-started})
            raise
        finally:
            if runner is not None and runner.poll() is None:
                stop_owned(runner)
            if server is not None:
                stop_owned(server)
            for s,handler in old.items():
                signal.signal(s,handler)
        result={"status":status,"smoke":smoke,"elapsed":time.monotonic()-started,
                "deadline_seconds":c["smoke_seconds"] if smoke else None}
        if smoke:
            # Runner and server have stopped; checkpoint writes cannot race us.
            for file in (root/"partial_responses").glob("*.json"):
                partial=read_json(file)
                if partial.get("status") in {"streaming", "interrupted"}:
                    partial["status"]="timeout_partial" if status=="bounded_timeout" else "interrupted_partial"
                    write_json(file,partial)
        write_json(root/"supervisor.json",result)
        return result


def cli():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["static","register","prepare","cpu","eligibility","supervise","run","review-smoke","status","analyze","report"])
    parser.add_argument("--smoke",action="store_true")
    parser.add_argument("--execute",action="store_true",help="Explicit future user-authorized inference only")
    args=parser.parse_args(); c=config()
    from . import gates,tests
    if args.command in {"supervise","run"} and not args.execute:
        parser.error("No automatic GPU/formal launch; an explicit --execute instruction is required")
    if args.command=="static": result=gates.static(c)
    elif args.command=="register": result={"status":"registered","cases":len(register(c)["cases"])}
    elif args.command=="prepare": result=prepare(c,args.smoke)
    elif args.command=="cpu": result=tests.cpu(c,args.smoke)
    elif args.command=="eligibility": result=eligibility(c)
    elif args.command=="supervise": result=supervise(c,args.smoke)
    elif args.command=="run": result=run(c,args.smoke)
    elif args.command=="review-smoke": result=gates.review_smoke(c)
    elif args.command=="analyze": result=gates.analyze(c)
    elif args.command=="report": result=gates.report_complete(c)
    else: result=gates.summarize(c,args.smoke)
    log("finished",command=args.command,result=result)


if __name__=="__main__":
    cli()

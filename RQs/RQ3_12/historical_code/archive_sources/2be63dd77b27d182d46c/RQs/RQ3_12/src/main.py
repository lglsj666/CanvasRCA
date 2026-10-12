"""Explicit commands; static/register cannot launch preparation or model processes."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
import os
import shutil
import signal
import subprocess
import sys
import threading
import time

from . import exps
from .utils import (ROOT, VERSION, MODEL, ARMS, METRICS, config, path, register, runtime, flag, logical_key,
                    phase_arms, stable_hash, sha_file, read_json, write_json, immutable_json, exclusive, source_contract, log)

CALL_IDENTITIES = {}  # Request bookkeeping only, populated before each real call.


def prepare_one(args):
    c, row = args
    root, oid = path(c["preparation"]), row["opaque_incident_id"]
    marker = root/"flags"/(oid+".json")
    if marker.exists():
        saved = read_json(marker)
        if saved.get("status")!="done" or saved.get("version")!=VERSION:
            raise ValueError("Foreign/incomplete preparation marker")
        return saved
    started=time.monotonic()
    parent=path(c["parent"])
    if read_json(parent/"export_flags"/(oid+".json"))["status"]!="done":
        raise ValueError("Parent public export not committed")
    source=parent/"public"/(oid+".json")
    bundle=read_json(source)
    compiler_started=time.monotonic()
    public,audit=exps.compile_public(bundle,c)
    compiler_seconds=time.monotonic()-compiler_started
    render_started=time.monotonic()
    from RQs.RQ3_8.src.main import render_capture
    for family,(evidence,design) in exps.designs(public["payload"],c).items():
        inputs=root/"render_inputs"/oid/family
        immutable_json(inputs/"evidence.json",evidence)
        immutable_json(inputs/"design.json",design)
        output=root/"renders"/oid/family
        if output.exists() and (not (output/"manifest.json").exists() or read_json(output/"manifest.json").get("status")!="passed"):
            output.rename(output.with_name(family+".interrupted."+str(time.time_ns())))
        manifest=read_json(output/"manifest.json") if output.exists() else render_capture(inputs/"evidence.json",inputs/"design.json",output)
        if manifest.get("status")!="passed" or manifest["evidence_hash"]!=stable_hash(evidence) or manifest["design_hash"]!=stable_hash(design):
            raise ValueError("Actual matrix render identity mismatch")
        public["images"][family+"_VISUAL"]={"path":str((output/"dashboard.png").relative_to(root)),"sha256":manifest["png_sha256"]}
    identities,canonical={},{}
    for arm in ARMS:
        png=(root/public["images"][arm]["path"]).read_bytes() if arm in public["images"] else None
        parts=exps.parts_for(public,arm,png)
        signature=stable_hash([{**p,"png":stable_hash(p["png"])} if "png" in p else p for p in parts])
        canonical[arm]=arm if arm=="EXACT_REPEAT" else identities.setdefault(signature,arm)
    public["canonical_arms"]=canonical
    exps.visible_audit(public)
    immutable_json(root/"public"/(oid+".json"),public)
    write_json(root/"audit"/(oid+".json"),{"model":audit,"source_public_sha256":sha_file(source)})
    # Evaluator is materialized only after all inputs and PNGs are committed.
    immutable_json(root/"private"/(oid+".json"),read_json(parent/"private"/(oid+".json")))
    saved={"status":"done","version":VERSION,"case":oid,"seconds":time.monotonic()-started,
           "compiler_seconds":compiler_seconds,"render_and_commit_seconds":time.monotonic()-render_started,
           "observations":12,"canonical_arms":canonical,"infeasible":{},"context_excluded":{},
           "parent_public_sha256":sha_file(source),"preparation_source_contract":source_contract(),
           "public_sha256":sha_file(root/"public"/(oid+".json")),"private_sha256":sha_file(root/"private"/(oid+".json"))}
    write_json(marker,saved);log("prepared",**saved)
    return saved


def prepare(c,smoke=False):
    current=source_contract()
    review=read_json(path(c["results"])/"qualification/static.json")
    if review.get("status")!="passed" or review.get("source_contract")!=current:
        raise RuntimeError("Current source-only gate required before preparation")
    from .gates import require_renderer_build
    require_renderer_build()
    from vlmrca.run_state import pinned_process_map
    from RQs.RQ3_8.src.utils import interleaved
    rows=register(c)["smoke" if smoke else "cases"]
    with exclusive(path(c["preparation"])/"prepare.lock"):
        results=pinned_process_map(prepare_one,[(c,r) for r in interleaved(rows)],max_workers=c["workers"])
    report={"status":"complete","cases":len(results),"unique_pngs":2*len(results),
            "preparation_seconds_sum":sum(r["seconds"] for r in results)}
    write_json(path(c["results"])/"qualification"/("preparation_smoke.json" if smoke else "preparation.json"),report)
    return report


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
    if arm in public["images"] and sha_file(prep/public["images"][arm]["path"])!=public["images"][arm]["sha256"]:
        raise ValueError("Pending-call PNG identity differs from committed preparation")
    parts = exps.parts_for(public, arm, png)
    envelope = _request_envelope(MODEL, system=public["system"])
    envelope["policy_version"] = VERSION
    actual = request_descriptor(parts, public["system"], envelope, MODEL)
    projection = {"base_facts": public["facts_hash"], "payload": stable_hash(public["payload"]), "request": stable_hash(actual)}
    task = {"experiment": ("smoke_" if root.name=="smoke" else "")+c["experiment"],
            "model": MODEL, "case": row, "dimensions": {"arm": arm, "replicate": int(arm=="EXACT_REPEAT")}}
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
    committed_phase=root/("phase_complete."+MODEL+".json")
    if committed_phase.exists():
        return {**read_json(committed_phase),"resumed_complete_phase":True}
    rows = register(c)["smoke" if smoke else "cases"]
    arms = phase_arms(c,smoke)
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
            states={a:flag(root,oid,a) for a in arms}
            terminal.update({logical_key(oid,a):v for a,v in states.items() if v is not None})
            pending = [a for a,v in states.items() if v is None]
            if not pending:
                continue
            marker = read_json(path(c["preparation"])/"flags"/(oid+".json"))
            for category in ("public","private"):
                if sha_file(path(c["preparation"])/category/(oid+".json"))!=marker[category+"_sha256"]:
                    raise ValueError("Pending-case input/evaluator identity changed")
            inputs[oid] = read_json(path(c["preparation"])/"public"/(oid+".json"))
            inputs[oid]["context_excluded"] = marker["context_excluded"]
            for arm in pending:
                canonical = marker["canonical_arms"][arm]
                if canonical not in arms:
                    canonical=arm  # Smoke covers its registered paths, no outside-arm references.
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
            count=len(terminal); total=len(rows)*len(arms); step=int(20*count/total)
            if not force and step<=last_report:
                return
            last_report=step
            metrics={}
            for a in arms:
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
        if report["status"]=="complete":
            immutable_json(committed_phase,{**report,"version":VERSION,"config_hash":stable_hash(c)})
        return report


def supervise(c, smoke=False):
    """Owned process groups; no model service or formal run on import/static."""
    from RQs.RQ3_6.src.utils import model_probe, endpoint_vacant, stop_owned
    from .gates import require_qualification
    started=time.monotonic()
    root=path(c["results"])/("smoke" if smoke else "formal")
    with exclusive(root/"supervisor.lock"):
        committed_phase=root/("phase_complete."+MODEL+".json")
        if committed_phase.exists():
            return {**read_json(committed_phase),"launched_model":False,"reason":"atomic model-phase marker"}
        rows=register(c)["smoke" if smoke else "cases"]
        if all(flag(root,r["opaque_incident_id"],a) is not None for r in rows for a in phase_arms(c,smoke)):
            from .gates import summarize
            return {**summarize(c,smoke),"launched_model":False,"reason":"all registered flags terminal"}
        require_qualification(c,smoke)
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
                    report["rq312_source_contract"]=source_contract()
                    write_json(root/"attestation.json",report)
                    log("ready",elapsed=time.monotonic()-started)
                    command=[sys.executable,"-m","RQs.RQ3_12.src.main","run","--execute"]+(["--smoke"] if smoke else [])
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
    parser.add_argument("command",choices=["static","register","prepare","cpu","build-renderer","supervise","run","review-smoke","status","analyze","freeze","accept-review"])
    parser.add_argument("--review-kind",choices=["scientific","visual","smoke","budget"])
    parser.add_argument("--review-file")
    parser.add_argument("--smoke",action="store_true")
    parser.add_argument("--execute",action="store_true",help="Explicit future user-authorized inference only")
    args=parser.parse_args(); c=config()
    from . import gates,tests
    if args.command in {"prepare","cpu","build-renderer","supervise","run","review-smoke","freeze","analyze","accept-review"} and not args.execute:
        parser.error("Runtime is pending user authorization; explicit --execute is required")
    if args.command=="static": result=gates.static(c)
    elif args.command=="register": result={"status":"registered","cases":len(register(c)["cases"])}
    elif args.command=="prepare": result=prepare(c,args.smoke)
    elif args.command=="cpu": result=tests.cpu(c,args.smoke)
    elif args.command=="build-renderer": result=gates.build_renderer(c)
    elif args.command=="supervise": result=supervise(c,args.smoke)
    elif args.command=="run": result=run(c,args.smoke)
    elif args.command=="review-smoke": result=gates.review_smoke(c)
    elif args.command=="analyze": result=gates.analyze(c)
    elif args.command=="freeze": result=gates.freeze(c)
    elif args.command=="accept-review":
        if not args.review_kind or not args.review_file: parser.error("Review kind/file required")
        result=gates.accept_review(c,args.review_kind,args.review_file)
    else: result=gates.summarize(c,args.smoke)
    log("finished",command=args.command,result=result)


if __name__=="__main__":
    cli()

"""Bounded CPU audit of an already completed, exposed development stage."""

import argparse
import collections
import json
import statistics
import threading
import time
from pathlib import Path

import z3

from .exps import (
    compile_public,
    output_contract_findings,
    screen_reason,
    verified_twin_parts,
)
from .gates import ClaimVerifier
from .utils import digest, input_parts, read_json, save_json

ROOT = Path(__file__).resolve().parents[3]
_AUDIT_LOCK = threading.Lock()


def artifact(row, folder):
    return Path(row["artifact_root"]) / folder / (row["call_key"] + ".json")


def aggregate(records):
    groups = collections.defaultdict(list)
    for record in records:
        for population in [record["dataset"], "pooled"] + (
            ["aiops_combined"] if record["dataset"].startswith("aiops") else []
        ):
            groups[record["model"], record["arm"], population].append(record)
    result = []
    for (model, arm, population), rows in sorted(groups.items()):
        audited = [r for r in rows if r["status"] == "audited"]
        marked = [
            r
            for r in audited
            if r["contract_errors"]
            or any(c["result"]["verdict"] == "refuted" for c in r["screened_claims"])
        ]
        result.append(
            {
                "model": model,
                "arm": arm,
                "population": population,
                "units": len(rows),
                "audited": len(audited),
                "contract_error_units": sum(
                    bool(r["contract_errors"]) for r in audited
                ),
                "literal_refutation_review_units": sum(
                    any(
                        c["result"]["verdict"] == "refuted"
                        for c in r["screened_claims"]
                    )
                    for r in audited
                ),
                "screened_claims": sum(len(r["screened_claims"]) for r in audited),
                "mean_historical_mrr": statistics.mean(
                    r["historical_mrr"] for r in audited
                )
                if audited
                else None,
                "marked_historical_ac1": sum(r["historical_ac1"] for r in marked),
                "marked_units": len(marked),
            }
        )
    return result


def audit(config, root=ROOT):
    started = time.monotonic()
    run = root / config["source_run"]
    out = root / config["output_root"]
    if (out / "summary.json").exists():
        raise FileExistsError(
            "Completed audit exists; use a new version, do not overwrite"
        )
    stage = read_json(run / "analysis" / (config["stage"] + ".json"))
    if (
        read_json(run / "formal_queue_status.json")["state"]
        != "completed_negative_development"
    ):
        raise ValueError("Source is not the registered completed RQ3.3 run")
    rows = stage["rows"]
    index = {(r["case_id"], r["model"], r["dimensions"]["arm"]): r for r in rows}
    if len(index) != len(rows):
        raise ValueError("Duplicate source units")
    records = []
    inputs = {}

    def parts(row):
        path = artifact(row, "inputs")
        if path not in inputs:
            inputs[path] = input_parts(read_json(path))
        return inputs[path]

    for i, row in enumerate(rows):
        if time.monotonic() - started > config["wall_timeout_sec"]:
            break
        record = {
            "case_id": row["case_id"],
            "model": row["model"],
            "dataset": row["dataset"],
            "arm": row["dimensions"]["arm"],
            "call_key": row["call_key"],
            "input_path": str(artifact(row, "inputs")),
            "output_path": str(artifact(row, "outputs")),
        }
        if row["status"] != "done":
            flag = read_json(run / "flags" / (row["logical_key"] + ".json"))
            record.update(status="source_incomplete", source_flag=flag)
            records.append(record)
            continue
        t0 = time.monotonic()
        try:
            original = parts(row)
            public = original
            twin_status = "text_only"
            provenance = {"input_path": record["input_path"]}
            if any(p["type"] == "image" for p in original):
                wt = index.get((row["case_id"], row["model"], "W_T"))
                wg = index.get((row["case_id"], row["model"], "W_G"))
                if wt and wg:
                    public, twin_status = verified_twin_parts(
                        original, parts(wt), parts(wg)
                    )
                    if twin_status == "paired_ledger_same_image":
                        provenance["ledger_input_path"] = str(artifact(wt, "inputs"))
                        provenance["paired_visual_input_path"] = str(
                            artifact(wg, "inputs")
                        )
                        ledger_part = next(
                            i
                            for i, p in enumerate(parts(wt))
                            if p.get("text", "").startswith("G: calls ")
                        )
                        provenance["part_origins"] = {
                            str(len(original)): {
                                "artifact": str(artifact(wt, "inputs")),
                                "part": ledger_part,
                            }
                        }
                else:
                    twin_status = "unavailable"
            evidence = compile_public(public, provenance)
            verifier = ClaimVerifier(evidence, config["solver_timeout_ms"])
            # The compiler and verifier never receive the scored output object.
            response = read_json(artifact(row, "outputs"))["response"]
            try:
                reply = json.loads(response)
            except (ValueError, TypeError):
                reply = None
            claims = screen_reason(
                reply.get("reason", "") if isinstance(reply, dict) else ""
            )
            checked = [
                {"claim": claim, "result": verifier.verify(claim)} for claim in claims
            ]
            record.update(
                status="audited",
                input_digest=digest(original),
                provenance=provenance,
                twin_status=twin_status,
                contract_errors=output_contract_findings(reply, evidence),
                screened_claims=checked,
                reason=reply.get("reason") if isinstance(reply, dict) else None,
                answer=reply.get("services") if isinstance(reply, dict) else None,
                kb_status=str(verifier.base_status),
                candidate_count=len(evidence.candidates),
                quantity_count=len(evidence.numbers),
                observed_relation_count=len(evidence.relations),
                type_contract_available=bool(evidence.types),
                compiler_warnings=evidence.warnings,
                # Score attachment follows checking; never used to choose a rule or claim.
                historical_mrr=row["metrics"]["mrr"],
                historical_ac1=row["metrics"]["ac@1"],
            )
        except (ValueError, KeyError, OSError, TypeError) as exc:
            record.update(
                status="artifact_or_compiler_error",
                error=f"{type(exc).__name__}: {exc}",
            )
        record["audit_wall_seconds"] = time.monotonic() - t0
        records.append(record)
        if (i + 1) % 100 == 0:
            save_json(
                out / "progress.json",
                {
                    "processed": i + 1,
                    "planned": len(rows),
                    "elapsed_s": time.monotonic() - started,
                },
            )
    statuses = collections.Counter(r["status"] for r in records)
    times = sorted(
        r["audit_wall_seconds"] for r in records if "audit_wall_seconds" in r
    )
    summary = {
        "schema_version": "claim-audit-result-v1",
        "experiment": config["experiment"],
        "state": "complete"
        if len(records) == len(rows) and not statuses["artifact_or_compiler_error"]
        else "incomplete",
        "planned_units": len(rows),
        "processed_units": len(records),
        "status_counts": dict(statuses),
        "unique_cases": len({r["case_id"] for r in records}),
        "model_calls": 0,
        "z3_version": z3.get_version_string(),
        "config": config,
        "source_stage_digest": digest(stage),
        "source_code_digests": {
            p.name: digest(p.read_text()) for p in Path(__file__).parent.glob("*.py")
        },
        "elapsed_seconds": time.monotonic() - started,
        "per_unit_seconds": {
            "median": statistics.median(times),
            "p95": times[int(0.95 * (len(times) - 1))],
            "maximum": max(times),
        },
        "contract_errors": dict(
            collections.Counter(
                e["kind"] for r in records for e in r.get("contract_errors", [])
            )
        ),
        "literal_screen_verdicts": dict(
            collections.Counter(
                c["result"]["verdict"]
                for r in records
                for c in r.get("screened_claims", [])
            )
        ),
        "twin_status_counts": dict(
            collections.Counter(r.get("twin_status", "not_audited") for r in records)
        ),
        "kb_status_counts": dict(
            collections.Counter(r.get("kb_status", "not_audited") for r in records)
        ),
        "scope": "Partial literal claim audit, not a hallucination-rate estimate or rescoring",
        "grouped": aggregate(records),
    }
    save_json(out / "records.json", records)
    save_json(out / "summary.json", summary)
    print(
        json.dumps(
            {
                k: v
                for k, v in summary.items()
                if k not in {"grouped", "source_code_digests", "config"}
            },
            indent=2,
        )
    )
    return summary


def prepare_case(args):
    import os
    import pickle

    from RQs.RQ3_3.src.utils import OfflineTokens
    from vlmrca.run_state import atomic_write

    from .exps import prepare_integrated
    from .utils import (
        metric_selection_metadata,
        registered_source_context,
        runtime_config,
    )

    row, config, directory = args
    root = Path(directory)
    opaque = row["opaque_incident_id"]
    flag = root / "preparation_flags" / (opaque + ".json")
    if flag.exists():
        return read_json(flag)
    started = time.monotonic()
    try:
        context, private = registered_source_context(row, config)
        inherited = time.monotonic()
        context["selection_metadata"] = metric_selection_metadata(context, row, config)
        metrics_at = time.monotonic()
        tokens = OfflineTokens(runtime_config(config))
        context["integrated"] = prepare_integrated(context, tokens, config)
        atomic_write(
            root / "contexts" / (opaque + ".pkl"), pickle.dumps(context, protocol=5)
        )
        save_json(root / "private" / (opaque + ".json"), private)
        value = {
            "status": "done",
            "opaque_incident_id": opaque,
            "elapsed_s": time.monotonic() - started,
            "inherited_context_s": inherited - started,
            "metrics_s": metrics_at - inherited,
            "selection_s": time.monotonic() - metrics_at,
            "cpu_affinity": sorted(os.sched_getaffinity(0)),
            "observations": len(context["observations"]),
            "packs": context["integrated"]["pool_count"],
            "selected": {
                k: [p["id"] for p in v["packs"]]
                for k, v in context["integrated"].items()
                if k.startswith("P")
            },
        }
        save_json(flag, value)
        return value
    except Exception as exc:
        save_json(
            flag,
            {
                "status": "fail",
                "opaque_incident_id": opaque,
                "error": f"{type(exc).__name__}: {exc}",
                "elapsed_s": time.monotonic() - started,
            },
        )
        raise


def prepare_integrated_cases(config, registration, root, rows=None):
    import concurrent.futures as cf
    import multiprocessing as mp

    from RQs.RQ3_3.src.main import exclusive, interleaved_sources
    from vlmrca.run_state import physical_cpu_ids, pin_process_to_core

    from .gates import qualification_rows

    rows = rows if rows is not None else qualification_rows(config, registration)
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
            if not cores:
                raise RuntimeError("No free affinity-eligible physical cores")
            for core in cores:
                queue.put(core)
            pool = cf.ProcessPoolExecutor(
                len(cores),
                mp_context=ctx,
                initializer=pin_process_to_core,
                initargs=(queue,),
            )
            try:
                tasks = [
                    pool.submit(prepare_case, (r, config, str(root))) for r in pending
                ]
                for future in cf.as_completed(tasks):
                    print(json.dumps(future.result(), ensure_ascii=False), flush=True)
            except BaseException:
                owned = list(pool._processes.values())
                pool.shutdown(wait=False, cancel_futures=True)
                for process in owned:
                    if process.is_alive():
                        process.terminate()
                for process in owned:
                    process.join(timeout=2)
                    if process.is_alive():
                        process.kill()
                        process.join(timeout=2)
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
        raise ValueError(
            "Failed preparation is terminal; inspect, then use a repaired version"
        )
    return flags


def load_integrated_context(root, row):
    import pickle

    opaque = row["opaque_incident_id"]
    if read_json(root / "preparation_flags" / (opaque + ".json"))["status"] != "done":
        raise ValueError("Preparation not committed")
    with (root / "contexts" / (opaque + ".pkl")).open("rb") as stream:
        context = pickle.load(stream)
    if context["opaque_incident_id"] != opaque or "integrated" not in context:
        raise ValueError("Wrong integrated context")
    if context["integrated"].get("clock_projection_version") != "relative_clock_v1":
        raise ValueError("Stale preparation: explicit relative-clock repair required")
    return context, read_json(root / "private" / (opaque + ".json"))


def compile_integrated_unit(task, context, private, config, tokens):
    import hashlib

    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    from RQs.RQ3_1.src.main import _request_envelope, bind_task_request
    from RQs.RQ3_3.src.exps import request_descriptor
    from RQs.RQ3_3.src.utils import ContextInfeasible
    from unified_scripts import stable_hash

    from .exps import arm_factors, assert_no_absolute_clock, integrated_parts
    from .utils import VERSION

    arm = task["dimensions"]["arm"]
    parts = integrated_parts(context, arm)
    assert_no_absolute_clock(parts)
    system = context["sircl_system"] if arm.startswith("SIRCL_") else RCA_SYSTEM_ROLE
    okay, counts = tokens.fits(parts, system)
    if not okay:
        raise ContextInfeasible("Registered intact input exceeds context")
    selection = None
    block = "none"
    if not arm.startswith("SIRCL_") and arm not in {"TPV", "P0_MORE_TRUE"}:
        p, h, _carrier, block = arm_factors(arm)
        selection = context["integrated"][f"P{p}H{h}"]
    envelope = _request_envelope(task["model"], system=system)
    envelope["policy_version"] = VERSION
    if envelope["effective_server"]["max_tokens"] != 8192:
        raise ValueError("Inherited request adapter changed output ceiling")
    actual = request_descriptor(parts, system, envelope, task["model"])
    projection = {
        "schema_version": "RQ34ProjectionV1",
        "arm": arm,
        "model_token_counts": counts,
        "source_hashes": context["source_hashes"],
        "selected_packs": selection["packs"] if selection else [],
        "raw_appendix_hash": digest(selection["raw_text"]) if selection else None,
        "block": block,
        "relation_claims": selection["relation_blocks"]["claims"] if selection else [],
        "image_hashes": [
            hashlib.sha256(p["png"]).hexdigest() for p in parts if p["type"] == "image"
        ],
        "scope_candidates": selection["scope_candidates"] if selection else 0,
        "scope_selected": selection["scope_selected"] if selection else 0,
    }
    bound = bind_task_request(
        task,
        actual,
        stable_hash(projection),
        projection=projection,
        adapter_version=VERSION,
        version=VERSION,
    )
    # The audit gets a same-image provenance ledger, not extra model evidence.
    from RQs.RQ3_3.src.exps import g_ledger

    ledger = g_ledger(context["prepared"].public["packet"])
    return {
        "parts": parts,
        "envelope": envelope,
        "task": bound,
        "actual": actual,
        "input_identity": stable_hash(actual),
        "projection": projection,
        "private": private,
        "candidates": context["candidates"],
        "g_ledger": ledger,
    }


def response_audit(request, response):
    """Partial literal review only; original answer/score are never modified."""
    # Z3's default context is not thread safe. Serialize millisecond audits,
    # not generation or artifact writing, under this one process-local lock.
    with _AUDIT_LOCK:
        parts = [
            {"type": "text", "text": p["text"]}
            for p in request["parts"]
            if p["type"] == "text"
        ]
        if any(p["type"] == "image" for p in request["parts"]):
            parts.append({"type": "text", "text": request["g_ledger"]})
        try:
            public = compile_public(parts)
        except ValueError as exc:
            # Native SIRCL uses a different candidate declaration. Explicit
            # partial coverage, not a fabricated zero hallucination count.
            return {
                "status": "unsupported_input_grammar",
                "reason": str(exc),
                "review_required": True,
            }
        verifier = ClaimVerifier(public)
        try:
            reply = json.loads(response)
        except (ValueError, TypeError):
            reply = {}
        if not isinstance(reply, dict):
            reply = {}
        reason = reply.get("reason", "")
        claims = [{**c, "check": verifier.verify(c)} for c in screen_reason(reason)]
        return {
            "status": "partial_literal_audit",
            "contract_errors": output_contract_findings(reply, public),
            "claims": claims,
            "review_required": True,
            "reason_characters": len(reason) if isinstance(reason, str) else 0,
            "quantities_compiled": len(public.numbers),
            "relations_compiled": len(public.relations),
            "base_status": str(verifier.base_status),
            "unparsed_claim_coverage": "unknown_not_zero",
            "image_provenance": "frozen_parent_G_same_image_ledger"
            if request["projection"]["image_hashes"]
            else "text_only",
        }


def import_prior_accounting(config, root):
    import sqlite3

    from vlmrca.run_state import DurableCallRegister

    ledger = DurableCallRegister(root / "calls.sqlite", limit=40000)
    records = []
    for name in config["implementation"]["prior_call_ledgers"]:
        with sqlite3.connect(f"file:{ROOT / name}?mode=ro", uri=True) as db:
            records.extend(
                (name, int(row[0])) for row in db.execute("SELECT id FROM calls")
            )
    with ledger.connect() as db:
        previous = db.execute(
            "SELECT value FROM settings WHERE name='rq34_prior_count'"
        ).fetchone()
        if previous is not None:
            if previous[0] != len(records):
                raise ValueError("Prior run accounting changed; reconcile explicitly")
            return len(records)
        db.execute("BEGIN IMMEDIATE")
        for name, ident in records:
            db.execute(
                "INSERT INTO calls(call_key,request_hash,role,state,result,started) VALUES (?,?,?,'complete',?,0)",
                (
                    "prior/" + digest([name, ident]),
                    digest([name, ident]),
                    "historical_accounting",
                    json.dumps(
                        {
                            "source_ledger": name,
                            "source_id": ident,
                            "not_a_new_request": True,
                        }
                    ),
                ),
            )
        db.execute(
            "INSERT INTO settings VALUES ('rq34_prior_count',?)", (len(records),)
        )
    return len(records)


def smoke_policy(root, stage, repair=False):
    """One explicit user exception; ordinary smoke limits remain unchanged."""
    if not repair:
        return {"stem": stage, "scope_limit": 18}
    if repair == "clock":
        approval = read_json(root / "clock_authorization.json")
        limits = {
            "exp_contract_alignment": (18, 6),
            "exp_evidence_reasoning_factorial": (18, 4),
            "exp_verified_visual_binding": (25, 6),
            "exp_integrated_locked_check": (18, 2),
        }
        before, additional = limits[stage]
        if (
            not approval.get("user_approved")
            or approval.get("kind") != "relative_clock_v1_targeted_gpu_repair"
            or approval.get("max_new_calls") != 18
            or approval.get("per_experiment_seconds") != 600
            or approval["experiments"][stage]
            != {"previous_calls": before, "additional_calls_max": additional}
        ):
            raise ValueError("Missing or mismatched clock repair approval")
        return {
            "stem": stage + "_clock_repair_v1",
            "scope_limit": before + additional,
            "calls_before": before,
            "additional_calls_max": additional,
            "prior_elapsed_s": approval.get("prior_execution_seconds", {}).get(
                stage, 0
            ),
        }
    if stage != "exp_verified_visual_binding":
        raise ValueError("Repair authorization is limited to visual binding")
    approval = read_json(root / "repair_authorizations" / "visual_binding_v1.json")
    if approval != {
        "experiment": stage,
        "user_approved": True,
        "previous_calls": 9,
        "additional_calls_max": 16,
        "window_seconds": 600,
        "original_report_hash": digest(read_json(root / "smokes" / (stage + ".json"))),
    }:
        raise ValueError("Missing or mismatched one-time repair approval")
    return {"stem": stage + "_repair_v1", "scope_limit": 25}


def execute_integrated(task, request, config, root, repair=False):
    import fcntl

    from RQs.RQ3_1.src.main import run_registered_call, score_response_callback
    from RQs.RQ3_3.src.main import timeout_exception
    from vlmrca.run_state import DurableCallRegister

    flag = root / "flags" / (task["logical_key"] + ".json")
    if flag.exists():
        return read_json(flag)
    key = request["task"]["call_key"]
    destination = root / "stages" / task["stage"] / task["model"]
    reuse = digest(
        [
            request["input_identity"],
            task["case"]["opaque_incident_id"],
            task["ledger_scope"],
        ]
    )
    (root / "reuse").mkdir(parents=True, exist_ok=True)
    with (root / "reuse" / (reuse + ".lock")).open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        index = root / "reuse" / (reuse + ".json")
        if index.exists():
            prior = read_json(index)
            value = {
                **prior,
                "logical_key": task["logical_key"],
                "reused_from": prior["logical_key"],
                "new_generation_calls": 0,
            }
            save_json(flag, value)
            return value
        ledger = DurableCallRegister(
            root / "calls.sqlite",
            limit=40000,
            scope=task["ledger_scope"],
            scope_limit=smoke_policy(root, task["experiment"], repair)["scope_limit"]
            if task["stage"].startswith("smoke_")
            else None,
        )
        try:
            save_json(
                destination / "projections" / (key + ".json"), request["projection"]
            )
            result = run_registered_call(
                request["task"],
                request["parts"],
                request["envelope"],
                destination,
                score_response=score_response_callback(
                    request["private"], request["candidates"]
                ),
                ledger=ledger,
            )
            audit = response_audit(request, result["response"])
            save_json(destination / "audits" / (key + ".json"), audit)
            cost = read_json(destination / "cost" / (key + ".json"))
            metrics = result["score"].get("metrics") or result["score"]
            value = {
                "status": "done",
                "logical_key": task["logical_key"],
                "call_key": key,
                "artifact_root": str(destination),
                "input_identity": request["input_identity"],
                "model_status": result["status"],
                "audit_status": audit["status"],
                "metrics": {
                    k: metrics[k]
                    for k in ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")
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
            }
            save_json(index, value)
            save_json(flag, value)
            return value
        except Exception as exc:
            timeout = timeout_exception(exc)
            value = {
                "status": "fail",
                "logical_key": task["logical_key"],
                "call_key": key,
                "artifact_root": str(destination),
                "failure_class": "request_timeout" if timeout else "infrastructure",
                "error": f"{type(exc).__name__}: {exc}",
                "auto_retry": False,
            }
            save_json(flag, value)
            if not timeout:
                raise
            return value


def run_integrated(config, registration, root, stage, model, smoke=False, repair=False):
    import concurrent.futures as cf
    import signal
    import threading

    from RQs.RQ3_3.src.main import exclusive
    from RQs.RQ3_3.src.utils import OfflineTokens

    from .gates import integrated_tasks
    from .utils import runtime_config

    if repair:
        if not smoke:
            raise ValueError("Repair is not a formal execution permission")
        smoke_policy(root, stage, repair)
    if not smoke and not config["execution_enabled"]:
        raise ValueError(
            "Formal execution remains disabled; user authorized qualification only"
        )
    if not smoke:
        qualification = read_json(root / "qualification" / (stage + ".json"))
        if qualification["status"] != "passed" or qualification[
            "contract_hash"
        ] != digest(registration["contract"]):
            raise ValueError("Missing current qualification")
        if (
            stage == "exp_integrated_locked_check"
            and not read_json(root / "expansion_decision.json")["passed"]
        ):
            raise ValueError("Locked check not admitted")
    from vlmrca.eval.scoring import is_granularity_aware_hit

    if not is_granularity_aware_hit("preflight", "preflight"):
        raise ValueError("Scorer unavailable")
    tasks = integrated_tasks(config, registration, stage, model, smoke)
    with exclusive(root / "run.lock"):
        pending = [
            t
            for t in tasks
            if not (root / "flags" / (t["logical_key"] + ".json")).exists()
        ]
        if not pending:
            return {"status": "already_terminal", "units": len(tasks)}
        from vlmrca.run_state import DurableCallRegister

        ledger = DurableCallRegister(
            root / "calls.sqlite", limit=40000, scope=pending[0]["ledger_scope"]
        )
        # Only unresolved attempts in this scope; never scan/rebuild done cases.
        with ledger.connect() as db:
            prefix = pending[0]["ledger_scope"] + "/"
            db.execute(
                "UPDATE calls SET state='interrupted',result=? WHERE state='started' AND substr(call_key,1,?)=?",
                (
                    json.dumps({"reason": "prior owner stopped before commit"}),
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
        pool = cf.ThreadPoolExecutor(max_workers=36)
        inflight = {}
        current = None
        completed = len(tasks) - len(pending)
        fatal = None
        try:
            for task in pending:
                if stop.is_set():
                    break
                while len(inflight) >= 36:
                    done, _ = cf.wait(inflight, return_when=cf.FIRST_COMPLETED)
                    for f in done:
                        f.result()
                        inflight.pop(f)
                        completed += 1
                opaque = task["case"]["opaque_incident_id"]
                if current != opaque:
                    context, private = load_integrated_context(root, task["case"])
                    current = opaque
                request = compile_integrated_unit(
                    task, context, private, config, tokens
                )
                f = pool.submit(execute_integrated, task, request, config, root, repair)
                inflight[f] = task
                for f in [f for f in inflight if f.done()]:
                    f.result()
                    inflight.pop(f)
                    completed += 1
                print(
                    f"{task['stage']} {model}: terminal={completed}/{len(tasks)} inflight={len(inflight)}",
                    flush=True,
                )
            for f in cf.as_completed(inflight):
                f.result()
                completed += 1
        except BaseException as exc:  # noqa: BLE001 -- persist failure and re-raise after drain
            fatal = exc
            stop.set()
            for f in inflight:
                f.cancel()
        finally:
            pool.shutdown(wait=True, cancel_futures=True)
            for s, handler in previous.items():
                signal.signal(s, handler)
            save_json(
                root / "stages" / tasks[0]["stage"] / (model + "_progress.json"),
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


def integrated_smoke(config, registration, root, stage, repair=False):
    """Independent bounded smoke, no formal scheduling; owned servers only."""
    import os
    import signal
    import subprocess
    import sys
    import urllib.error
    import urllib.request

    from unified_scripts.vllm_inference import VLLMInferenceConfig
    from vlmrca.run_state import DurableCallRegister

    from .gates import integrated_tasks

    cpu = read_json(root / "cpu_qualification.json")
    if cpu["status"] != "passed" or cpu["contract_hash"] != digest(
        registration["contract"]
    ):
        raise ValueError("Current CPU qualification required before GPU")
    policy = smoke_policy(root, stage, repair)
    if repair == "clock":
        inherit_clock_smoke_units(config, registration, root)
    stem = policy["stem"]
    destination = root / "smokes" / (stem + ".json")
    if destination.exists():
        raise ValueError(
            "Logical smoke already recorded; inspect rather than spending another 18 calls"
        )
    ledger = DurableCallRegister(root / "calls.sqlite", limit=40000)
    prefix = "rq34_smoke:" + stage + "/"
    with ledger.connect() as db:
        calls_before = db.execute(
            "SELECT count(*) FROM calls WHERE substr(call_key,1,?)=?",
            (len(prefix), prefix),
        ).fetchone()[0]
    if repair:
        expected_before = policy.get("calls_before", 9)
        if calls_before != expected_before:
            raise ValueError("Repair prior attempt count differs from approval")
        # Reserve this repair window before starting any process. No second window.
        marker = root / "smokes" / (stem + "_started.json")
        marker.parent.mkdir(parents=True, exist_ok=True)
        with marker.open("x") as handle:
            json.dump(
                {"started_unix": time.time(), "calls_before": calls_before}, handle
            )
    started = time.monotonic()
    prior_elapsed = policy.get("prior_elapsed_s", 0)
    remaining = 600 - prior_elapsed
    if not 0 < remaining <= 600:
        raise ValueError("Authorized repair time budget exhausted")
    deadline = started + remaining
    runtime = VLLMInferenceConfig.load(ROOT / config["unified"]["inference"])
    report = {"status": "complete", "contract_hash": digest(registration["contract"])}
    if repair:
        report.update(
            repair_of=stage + ".json",
            calls_before=calls_before,
            additional_calls_max=policy.get("additional_calls_max", 16),
            cumulative_calls_max=policy["scope_limit"],
        )
    owned = []
    handles = []

    def cleanup():
        for process in reversed(owned):
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        owned.clear()

    def alarm(*_):
        raise TimeoutError("600-second logical smoke deadline")

    previous = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        for model in config["models"]:
            if repair == "clock" and all(
                (root / "flags" / (t["logical_key"] + ".json")).exists()
                for t in integrated_tasks(config, registration, stage, model, True)
            ):
                continue
            spec = runtime.model(model)
            req = urllib.request.Request(
                spec["base_url"].rstrip("/") + "/models",
                headers={
                    "Authorization": "Bearer " + os.environ.get("VLLM_API_KEY", "EMPTY")
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=2):
                    pass
            except urllib.error.URLError as exc:
                if not isinstance(exc.reason, ConnectionRefusedError):
                    raise RuntimeError(  # noqa: TRY004
                        "Endpoint occupancy cannot be established"
                    ) from exc
            else:
                raise RuntimeError(
                    "Existing server owns the endpoint; leave it untouched"
                )
            path = root / "smokes" / (stem + "_" + model + "_server.log")
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = path.open("ab")
            handles.append(handle)
            server = subprocess.Popen(
                ["bash", "scripts/vllm_vlm/serve_canvasrca_local.sh", model],
                cwd=ROOT,
                stdout=handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            owned.append(server)
            while True:
                if server.poll() is not None:
                    raise RuntimeError("Smoke server exited; inspect server log")
                try:
                    with urllib.request.urlopen(req, timeout=2) as response:
                        names = [m["id"] for m in json.load(response)["data"]]
                    if names != [spec["served_model_name"]]:
                        raise RuntimeError("Wrong served model")
                    break
                except urllib.error.URLError:
                    time.sleep(5)
            log = (root / "smokes" / (stem + "_" + model + "_runner.log")).open("ab")
            handles.append(log)
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "RQs.RQ3_4.src.main",
                    "run",
                    "--experiment",
                    stage,
                    "--model",
                    model,
                    "--smoke",
                    *(
                        ["--clock-repair"]
                        if repair == "clock"
                        else ["--repair"]
                        if repair
                        else []
                    ),
                ],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            owned.append(child)
            returncode = child.wait(timeout=max(0.1, deadline - time.monotonic()))
            if returncode:
                raise RuntimeError(
                    f"Smoke model phase failed (exit {returncode}); inspect runner and kernel logs"
                )
            cleanup()
    except (TimeoutError, subprocess.TimeoutExpired):
        report["status"] = "bounded_timeout_only"
    except BaseException as exc:  # noqa: BLE001 -- failure report survives interrupt; caller raises
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        cleanup()
        for handle in handles:
            handle.close()
        flags = [
            read_json(root / "flags" / (t["logical_key"] + ".json"))
            for t in integrated_tasks(config, registration, stage, smoke=True)
            if (root / "flags" / (t["logical_key"] + ".json")).exists()
        ]
        if any(f["status"] == "fail" for f in flags):
            report["status"] = "failed"
        ledger = DurableCallRegister(root / "calls.sqlite", limit=40000)
        prefix = "rq34_smoke:" + stage + "/"
        with ledger.connect() as db:
            report["initiated_calls"] = db.execute(
                "SELECT count(*) FROM calls WHERE substr(call_key,1,?)=?",
                (len(prefix), prefix),
            ).fetchone()[0]
        report["completed_units"] = [
            f["logical_key"] for f in flags if f["status"] == "done"
        ]
        report["flags"] = flags
        report["newly_initiated_calls"] = report["initiated_calls"] - calls_before
        if report["initiated_calls"] > policy["scope_limit"]:
            report.update(status="failed", error="Logical smoke call limit exceeded")
        report["elapsed_s"] = time.monotonic() - started
        if repair == "clock":
            report["prior_execution_seconds"] = prior_elapsed
            report["aggregate_repair_execution_seconds"] = (
                prior_elapsed + report["elapsed_s"]
            )
        save_json(destination, report)
    if report["status"] == "failed":
        raise RuntimeError("Logical smoke failed")
    return report


def inherit_clock_smoke_units(config, registration, root):
    """Reuse only complete, identical requests; leave all old flags untouched."""
    from .gates import integrated_tasks

    approval = read_json(root / "clock_authorization.json")
    parent = ROOT / approval["parent_root"]
    identities = {
        (u["case"], u["arm"], u["model"]): u["input_identity"]
        for u in read_json(root / "cpu_qualification.json")["units"]
    }
    tasks = [
        t
        for spec in config["experiments"]
        for t in integrated_tasks(config, registration, spec["id"], smoke=True)
    ]
    task_index = {t["logical_key"]: t for t in tasks}
    reusable = {}
    for owner in (parent, root):
        for path in sorted((owner / "flags").glob("*.json")):
            flag = read_json(path)
            if flag["status"] == "done" and flag["logical_key"] in task_index:
                task = task_index[flag["logical_key"]]
                reusable[
                    flag["input_identity"],
                    task["case"]["opaque_incident_id"],
                    task["model"],
                ] = flag
    inherited = []
    for spec in config["experiments"]:
        for task in integrated_tasks(config, registration, spec["id"], smoke=True):
            path = root / "flags" / (task["logical_key"] + ".json")
            if path.exists():
                continue
            identity = identities[
                task["case"]["opaque_incident_id"],
                task["dimensions"]["arm"],
                task["model"],
            ]
            reuse_key = (identity, task["case"]["opaque_incident_id"], task["model"])
            if reuse_key not in reusable:
                continue
            prior = reusable[reuse_key]
            completion = (
                Path(prior["artifact_root"])
                / "completed"
                / (prior["call_key"] + ".json")
            )
            if not completion.is_file():
                raise ValueError("Identical-input source has no durable completion")
            save_json(
                path,
                {
                    **prior,
                    "logical_key": task["logical_key"],
                    "reused_from": prior["logical_key"],
                    "new_generation_calls": 0,
                    "clock_repair_input_identity_checked": True,
                },
            )
            inherited.append(task["logical_key"])
    return inherited


def setup_clock_smoke(config, parent):
    """One authorized repair, isolated records and shared unreset call register."""
    import shutil

    from .gates import integrated_contract
    from .tests import integrated_cpu_qualification

    before = read_json(parent / "registration.json")
    if (
        digest(before["contract"])
        != "ffd6e79eb3ed84278a2392447feb50db649bea81cabfc0e3da0a36cbfda2de11"
    ):
        raise ValueError("Not the reviewed relative-clock CPU predecessor")
    current = integrated_contract(config)
    changed = {
        p
        for p in current.keys() | before["contract"].keys()
        if current.get(p) != before["contract"].get(p)
    }
    if changed != {
        "RQs/RQ3_4/src/main.py",
        "RQs/RQ3_4/src/tests.py",
        "RQs/RQ3_4/scripts/clock_qualification.sh",
    }:
        raise ValueError("Clock smoke setup contains non-operational source changes")
    if config != before["config"] or config["execution_enabled"]:
        raise ValueError("Clock supplement cannot change design or enable formal work")
    root = parent / "repairs/relative_clock_gpu_v1"
    root.mkdir(parents=True, exist_ok=False)
    shutil.copy2(parent / "registration.json", root / "registration_before.json")
    for name in ("contexts", "private", "preparation_flags"):
        shutil.copytree(parent / name, root / name)
    root.joinpath("calls.sqlite").symlink_to(parent / "calls.sqlite")
    registration = {**before, "contract": current}
    save_json(root / "registration.json", registration)
    approval = {
        "kind": "relative_clock_v1_targeted_gpu_repair",
        "user_approved": True,
        "user_instruction": "好的，再做一下定向gpu补验吧。",
        "parent_root": str(parent.relative_to(ROOT)),
        "max_new_calls": 18,
        "per_experiment_seconds": 600,
        "formal_authorized": False,
        "experiments": {
            s: {"previous_calls": before_calls, "additional_calls_max": extra}
            for s, before_calls, extra in (
                ("exp_contract_alignment", 18, 6),
                ("exp_evidence_reasoning_factorial", 18, 4),
                ("exp_verified_visual_binding", 25, 6),
                ("exp_integrated_locked_check", 18, 2),
            )
        },
    }
    failed_controller = (
        parent
        / "repairs/relative_clock_gpu_v1_controller_attempt1/smokes/exp_contract_alignment_clock_repair_v1.json"
    )
    if failed_controller.exists():
        prior = read_json(failed_controller)
        if prior["status"] != "failed" or prior["newly_initiated_calls"] != 0:
            raise ValueError(
                "Only the recorded pre-request controller failure can resume"
            )
        approval["prior_execution_seconds"] = {
            "exp_contract_alignment": prior["elapsed_s"]
        }
        approval["prior_failure_report"] = str(failed_controller.relative_to(ROOT))
    save_json(root / "clock_authorization.json", approval)
    cpu = integrated_cpu_qualification(config, registration, root)
    old_units = read_json(parent / "cpu_qualification.json")["units"]
    identity = lambda rows: {
        (u["case"], u["arm"], u["model"]): u["input_identity"] for u in rows
    }
    if identity(cpu["units"]) != identity(old_units):
        raise ValueError("Operational repair entry changed scientific inputs")
    inherited = inherit_clock_smoke_units(config, registration, root)
    if len(inherited) != 54:
        raise ValueError("Expected 54 identical-input inherited smoke units")
    save_json(
        root / "setup.json",
        {
            "status": "passed",
            "changed_files": sorted(changed),
            "input_equivalence_units": len(old_units),
            "inherited_units": len(inherited),
            "pending_logical_units": 18,
            "new_calls_upper": 18,
            "new_calls_expected_after_exact_reuse": 16,
            "contract_hash": digest(current),
            "formal_enabled": False,
        },
    )
    return {"status": "ready", "root": str(root), "inherited": len(inherited)}


def repair_clock_preparation(config, root):
    """Explicit CPU-only migration of the three qualification contexts.

    No inference, old result edits, whole-corpus rebuild, or implicit migration
    during resume. Original inputs and checkpoints remain in the archive.
    """
    import pickle
    import shutil
    from copy import deepcopy

    from RQs.RQ3_3.src.utils import OfflineTokens
    from vlmrca.run_state import atomic_write

    from .exps import prepare_integrated
    from .gates import integrated_contract, qualification_rows
    from .tests import integrated_cpu_qualification
    from .utils import runtime_config

    before = read_json(root / "registration.json")
    predecessor = "49a754e7cf3729cb139b30b6cb0150c64ea4cc44d0f292d1ffe95cfbd5b85f6a"
    if digest(before["contract"]) != predecessor:
        raise ValueError("Not the registered pre-clock-repair predecessor")
    without_policy = deepcopy(config)
    without_policy["method"].pop("clock_projection")
    if without_policy != before["config"] or config["execution_enabled"]:
        raise ValueError(
            "Clock repair must not change other contracts or enable formal execution"
        )
    current = integrated_contract(config)
    changed = {
        k
        for k in set(current) | set(before["contract"])
        if current.get(k) != before["contract"].get(k)
    }
    expected = {
        "RQs/RQ3_4/src/main.py",
        "RQs/RQ3_4/src/exps.py",
        "RQs/RQ3_4/src/tests.py",
        "RQs/RQ3_4/configs/integrated_round_v1.json",
    }
    if changed != expected:
        raise ValueError("Unexpected source change during clock repair")
    destination = root / "repairs/relative_clock_v1"
    if destination.exists():
        raise ValueError("Clock repair already attempted; inspect its artifacts first")
    destination.mkdir(parents=True)
    previous = destination / "previous"
    previous.mkdir()
    for name in (
        "registration.json",
        "cpu_qualification.json",
        "contexts",
        "private",
        "preparation_flags",
        "cpu_examples",
        "qualification",
    ):
        p = root / name
        if p.is_dir():
            shutil.copytree(p, previous / name)
        else:
            shutil.copy2(p, previous / name)
    started = time.monotonic()
    registration = {**before, "config": config, "contract": current}
    save_json(destination / "registration.json", registration)
    rows = qualification_rows(config, registration)
    tokens = OfflineTokens(runtime_config(config))
    selection_changes = []
    for row in rows:
        opaque = row["opaque_incident_id"]
        with (previous / "contexts" / (opaque + ".pkl")).open("rb") as stream:
            context = pickle.load(stream)
        old = context["integrated"]
        context["integrated"] = prepare_integrated(context, tokens, config)
        for name in ("P0H0", "P0H1", "P1H0", "P1H1"):
            if old[name]["packs"] != context["integrated"][name]["packs"]:
                selection_changes.append({"case": opaque, "selection": name})
        atomic_write(
            destination / "contexts" / (opaque + ".pkl"),
            pickle.dumps(context, protocol=5),
        )
        save_json(
            destination / "private" / (opaque + ".json"),
            read_json(previous / "private" / (opaque + ".json")),
        )
        save_json(
            destination / "preparation_flags" / (opaque + ".json"),
            {
                **read_json(previous / "preparation_flags" / (opaque + ".json")),
                "clock_projection_version": "relative_clock_v1",
                "reused_full_pool_and_metadata": True,
                "selected": {
                    k: [p["id"] for p in context["integrated"][k]["packs"]]
                    for k in ("P0H0", "P0H1", "P1H0", "P1H1")
                },
            },
        )
    cpu = integrated_cpu_qualification(config, registration, destination)
    old_units = {
        (u["case"], u["arm"], u["model"]): u
        for u in read_json(previous / "cpu_qualification.json")["units"]
    }
    impacted = [
        u
        for u in cpu["units"]
        if u["input_identity"]
        != old_units[(u["case"], u["arm"], u["model"])]["input_identity"]
    ]
    if any(u["arm"] in {"TPV", "P0_MORE_TRUE"} for u in impacted):
        raise ValueError("Unexpected immutable backbone/bridge change")
    affected_smoke = []
    keys = {(u["case"], u["arm"], u["model"]) for u in impacted}
    from .gates import integrated_tasks

    for spec in config["experiments"]:
        for task in integrated_tasks(config, registration, spec["id"], smoke=True):
            if (
                task["case"]["opaque_incident_id"],
                task["dimensions"]["arm"],
                task["model"],
            ) in keys:
                affected_smoke.append(
                    {
                        "experiment": spec["id"],
                        "logical_key": task["logical_key"],
                        "case": task["case"]["opaque_incident_id"],
                        "model": task["model"],
                        "arm": task["dimensions"]["arm"],
                    }
                )
    migration = {
        "status": "cpu_passed_gpu_pending",
        "before_contract": digest(before["contract"]),
        "after_contract": digest(current),
        "changed_files": sorted(changed),
        "requests_checked": len(cpu["units"]),
        "changed_requests": impacted,
        "unchanged_requests": len(cpu["units"]) - len(impacted),
        "selection_changes": selection_changes,
        "affected_smoke_units": affected_smoke,
        "elapsed_s": time.monotonic() - started,
        "new_model_calls": 0,
        "formal_enabled": False,
        "old_inference_artifacts_unchanged": True,
    }
    save_json(destination / "migration.json", migration)
    # Promote only after the whole CPU matrix passes. The explicit archive permits
    # recovery of a partial promotion; ordinary resume never accepts stale caches.
    for name in ("contexts", "private", "preparation_flags", "cpu_examples"):
        shutil.copytree(destination / name, root / name, dirs_exist_ok=True)
    save_json(root / "cpu_qualification.json", cpu)
    save_json(root / "registration.json", registration)
    for spec in config["experiments"]:
        path = root / "qualification" / (spec["id"] + ".json")
        prior = read_json(previous / "qualification" / path.name)
        count = sum(x["experiment"] == spec["id"] for x in affected_smoke)
        save_json(
            path,
            {
                **prior,
                "status": "cpu_fixed_gpu_pending" if count else prior["status"],
                "contract_hash": digest(current),
                "clock_repair": "repairs/relative_clock_v1/migration.json",
                "affected_units": count,
                "formal_authorized": False,
            },
        )
    return migration


def formal_phase_state(config, registration, root, stage, model):
    """Read only small commit flags; never rebuild completed model inputs."""
    from .gates import integrated_tasks

    tasks = integrated_tasks(config, registration, stage, model)
    counts = collections.Counter()
    for task in tasks:
        path = root / "flags" / (task["logical_key"] + ".json")
        status = read_json(path)["status"] if path.exists() else "pending"
        if status not in {"done", "fail", "pending"}:
            raise ValueError("Unrecognized formal commit status")
        counts[status] += 1
    return {"planned": len(tasks), "pending": counts["pending"], **dict(counts)}


def activate_formal(config, root):
    """One authorized operational successor; retain original smoke evidence."""
    import ast
    from copy import deepcopy

    from .gates import integrated_contract
    from .tests import integrated_cpu_qualification

    directory = root / "contract_migrations/formal_activation_v1"
    previous = directory / "previous"
    old = read_json(previous / "registration.json")
    old_hash = digest(old["contract"])
    if old_hash != "b6b8da780cf8141b844db782873647b84e9a729b149092697d9234eef77a132b":
        raise ValueError("Unexpected qualification predecessor")
    if (directory / "activation.json").exists():
        raise ValueError("Already activated; use queue to resume")
    expected = deepcopy(old["config"])
    expected.update(status="qualified_formal_authorized", execution_enabled=True)
    expected["implementation"]["qualification_only_authorized"] = False
    if config != expected:
        raise ValueError("Activation cannot change scientific configuration")
    contract = integrated_contract(config)
    changes = {
        k
        for k in set(contract) | set(old["contract"])
        if contract.get(k) != old["contract"].get(k)
    }
    allowed = {
        "RQs/RQ3_4/src/main.py",
        "RQs/RQ3_4/src/tests.py",
        "RQs/RQ3_4/configs/integrated_round_v1.json",
        "RQs/RQ3_4/scripts/formal_queue.sh",
    }
    if not changes <= allowed:
        raise ValueError(f"Unreviewed source changes: {changes - allowed}")

    def functions(path):
        return {
            n.name: ast.dump(n, include_attributes=False)
            for n in ast.parse(path.read_text()).body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    before = functions(previous / "main.py")
    after = functions(ROOT / "RQs/RQ3_4/src/main.py")
    unchanged = [name for name in before if name not in {"main", "integrated_cli"}]
    if any(before[name] != after.get(name) for name in unchanged):
        raise ValueError("Existing runtime/compiler functions changed")
    qualifications = {
        e["id"]: read_json(previous / "qualification" / (e["id"] + ".json"))
        for e in config["experiments"]
    }
    if any(
        q["status"] != "passed" or q["contract_hash"] != old_hash
        for q in qualifications.values()
    ):
        raise ValueError("Predecessor qualification incomplete")
    current = {**old, "config": config, "contract": contract}
    cpu = integrated_cpu_qualification(config, current, root)
    old_cpu = read_json(previous / "cpu_qualification.json")
    if cpu["status"] != "passed" or cpu["units"] != old_cpu["units"]:
        raise ValueError("Operational activation changed tested inputs")
    import_prior_accounting(config, root)
    from vlmrca.run_state import DurableCallRegister

    with DurableCallRegister(root / "calls.sqlite", limit=40000).connect() as db:
        spent = db.execute("SELECT count(*) FROM calls").fetchone()[0]
    if spent + config["budget"]["formal_calls_upper"] > 40000:
        raise ValueError("Insufficient registered call budget")
    save_json(root / "registration.json", current)
    for stage, original in qualifications.items():
        save_json(
            root / "qualification" / (stage + ".json"),
            {
                **original,
                "contract_hash": digest(contract),
                "formal_authorized": True,
                "inherited_qualification_contract": old_hash,
                "operational_activation": "contract_migrations/formal_activation_v1/activation.json",
            },
        )
    result = {
        "status": "authorized",
        "from_contract": old_hash,
        "contract_hash": digest(contract),
        "changed_files": sorted(changes),
        "unchanged_existing_functions": unchanged,
        "identical_cpu_requests": len(cpu["units"]),
        "unit_tests": cpu["unit_tests"],
        "prior_calls": spent,
        "additional_formal_upper": config["budget"]["formal_calls_upper"],
        "user_instruction": "Start formal experiments, then stop assistant monitoring",
        "scientific_inputs_changed": False,
        "new_smoke_calls": 0,
        "activated_unix": time.time(),
    }
    save_json(directory / "activation.json", result)
    return result


def integrated_formal_queue(config, registration, root):
    """Sequential background lifecycle, resumable flags and owned cleanup."""
    import os
    import signal
    import subprocess
    import sys
    import urllib.error
    import urllib.request

    from RQs.RQ3_3.src.main import exclusive
    from unified_scripts.vllm_inference import VLLMInferenceConfig

    from .gates import analyze_integrated

    if not config["execution_enabled"]:
        raise ValueError("Formal execution not enabled")
    activation = read_json(
        root / "contract_migrations/formal_activation_v1/activation.json"
    )
    if activation["contract_hash"] != digest(registration["contract"]):
        raise ValueError("Activation contract differs")
    for stage in config["experiments"]:
        q = read_json(root / "qualification" / (stage["id"] + ".json"))
        if q["status"] != "passed" or q["contract_hash"] != activation["contract_hash"]:
            raise ValueError("Current qualification missing")
    stop = threading.Event()
    old_handlers = {
        s: signal.signal(s, lambda *_: stop.set())
        for s in (signal.SIGTERM, signal.SIGINT)
    }
    runtime = VLLMInferenceConfig.load(ROOT / config["unified"]["inference"])
    logdir = root / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    stamp = str(time.time_ns())
    state = {
        "pid": os.getpid(),
        "attempt": stamp,
        "contract_hash": activation["contract_hash"],
        "started_unix": time.time(),
    }
    cli = [sys.executable, "-u", "-m", "RQs.RQ3_4.src.main"]
    owned_queue = False

    def update(status, **fields):
        state.update(state=status, updated_unix=time.time(), **fields)
        save_json(root / "formal_queue_status.json", state)
        save_json(logdir / ("queue_" + stamp + ".json"), state)
        print(json.dumps(state), flush=True)

    def terminate_group(process):
        # Only groups created by this supervisor, never global pkill.
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

    def command(arguments, label, graceful=False):
        with (logdir / (stamp + "_" + label + ".log")).open("ab") as stream:
            child = subprocess.Popen(
                cli + arguments,
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
                        raise InterruptedError("User paused the queue")
                if child.returncode:
                    raise RuntimeError(
                        f"{label} exited {child.returncode}; see {stream.name}"
                    )
            finally:
                terminate_group(child)
        if stop.is_set():
            raise InterruptedError("User paused the queue")

    def model_phase(stage, model):
        if not formal_phase_state(config, registration, root, stage, model)["pending"]:
            update("phase_already_terminal", experiment=stage, model=model)
            return
        spec = runtime.model(model)
        req = urllib.request.Request(
            spec["base_url"].rstrip("/") + "/models",
            headers={
                "Authorization": "Bearer " + os.environ.get("VLLM_API_KEY", "EMPTY")
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=2):
                pass
        except urllib.error.URLError as exc:
            if not isinstance(exc.reason, ConnectionRefusedError):
                raise RuntimeError("Cannot establish vacant endpoint") from exc  # noqa: TRY004
        else:
            raise RuntimeError("Existing server left untouched; endpoint occupied")
        update("starting_model", experiment=stage, model=model)
        prefix = stamp + "_" + stage + "_" + model
        with (logdir / (prefix + "_server.log")).open("ab") as stream:
            server = subprocess.Popen(
                ["bash", "scripts/vllm_vlm/serve_canvasrca_local.sh", model],
                cwd=ROOT,
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            update(
                "starting_model",
                server_pid=server.pid,
                server_log=str(Path(stream.name)),
            )
            try:
                deadline = time.monotonic() + spec["wait_timeout_sec"]
                while True:
                    if stop.is_set():
                        raise InterruptedError("User paused during model startup")
                    if server.poll() is not None:
                        raise RuntimeError("Owned vLLM exited during startup")
                    try:
                        with urllib.request.urlopen(req, timeout=2) as response:
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
                        "profile": config["unified"]["inference"],
                        "effective": spec,
                        "argv": runtime.server_argv(model),
                        "contract_hash": activation["contract_hash"],
                        "pid_operational_only": server.pid,
                        "server_log": str(Path(stream.name)),
                        "ready_unix": time.time(),
                    },
                )
                update("running", child_pid=None)
                command(
                    ["run", "--experiment", stage, "--model", model],
                    stage + "_" + model,
                    True,
                )
                phase = formal_phase_state(config, registration, root, stage, model)
                if phase["pending"]:
                    raise InterruptedError("Runner drained before all units completed")
                save_json(
                    root / "stages" / stage / (model + "_phase_complete.json"), phase
                )
            finally:
                terminate_group(server)
                update("model_stopped", server_pid=None, child_pid=None)

    try:
        with exclusive(root / "formal_queue.lock"):
            owned_queue = True
            update("starting", child_pid=None, server_pid=None)
            prepared_cohort = None
            for stage in config["experiments"]:
                if stop.is_set():
                    raise InterruptedError("User paused the queue")
                if stage.get("conditional"):
                    update("deciding", experiment=stage["id"], model=None)
                    decision = analyze_integrated(
                        config,
                        registration,
                        root,
                        "exp_evidence_reasoning_factorial",
                        decide=True,
                    )
                    if not decision["passed"]:
                        update("completed_negative_development", decision=decision)
                        return dict(state)
                if prepared_cohort != stage["cohort"]:
                    update(
                        "preparation",
                        cohort=stage["cohort"],
                        experiment=stage["id"],
                        model=None,
                    )
                    command(
                        ["prepare", "--cohort", stage["cohort"]],
                        "prepare_" + stage["cohort"],
                    )
                    prepared_cohort = stage["cohort"]
                for model in config["models"]:
                    model_phase(stage["id"], model)
                update("analyzing", experiment=stage["id"], model=None)
                analyze_integrated(config, registration, root, stage["id"])
            update("completed")
            return dict(state)
    except InterruptedError as exc:
        update("paused", error=str(exc))
        return dict(state)
    except BaseException as exc:
        if owned_queue:
            update("failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        for s, handler in old_handlers.items():
            signal.signal(s, handler)


def integrated_cli(argv):
    from RQs.RQ3_3.src.main import configure_environment

    from .gates import integrated_contract, register_integrated
    from .utils import integrated_config, runtime_config, stage_spec

    parser = argparse.ArgumentParser(
        description="RQ3.4 integrated experiment; no implicit formal launch"
    )
    parser.add_argument(
        "command",
        choices=[
            "activate-formal",
            "queue",
            "register",
            "cpu-check",
            "repair-clocks",
            "setup-clock-smoke",
            "prepare",
            "run",
            "smoke",
            "review",
            "decide",
            "analyze",
        ],
    )
    parser.add_argument("--experiment")
    parser.add_argument("--model")
    parser.add_argument("--cohort", choices=["screen", "check"], default="screen")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--clock-repair", action="store_true")
    args = parser.parse_args(argv)
    if args.clock_repair:
        if args.repair or args.command not in {"smoke", "run", "review"}:
            parser.error(
                "--clock-repair applies only to smoke/run/review and cannot combine with --repair"
            )
        args.repair = "clock"
    if args.repair and args.command not in {"smoke", "run", "review"}:
        parser.error("--repair only applies to smoke, its run child, or review")
    config = integrated_config()
    configure_environment(runtime_config(config))
    root = ROOT / config["implementation"]["output_root"]
    if args.command == "activate-formal":
        print(json.dumps(activate_formal(config, root), indent=2), flush=True)
        return
    if args.command == "setup-clock-smoke":
        print(json.dumps(setup_clock_smoke(config, root), indent=2), flush=True)
        return
    if args.clock_repair:
        root = root / "repairs/relative_clock_gpu_v1"
        if read_json(root / "setup.json")["status"] != "passed":
            raise ValueError("Clock qualification setup is incomplete")
    if args.command == "repair-clocks":
        print(json.dumps(repair_clock_preparation(config, root), indent=2), flush=True)
        return
    if args.command == "register":
        result = register_integrated(config, root)
        print(
            json.dumps(
                {
                    "status": "registered",
                    "cohorts": {k: len(v) for k, v in result["rosters"].items()},
                },
                indent=2,
            )
        )
        return
    registration = read_json(root / "registration.json")
    if registration["config"] != config or registration[
        "contract"
    ] != integrated_contract(config):
        raise ValueError(
            "Source/config changed since registration; explicit successor required"
        )
    if args.command == "queue":
        result = integrated_formal_queue(config, registration, root)
    elif args.command == "cpu-check":
        from .tests import integrated_cpu_qualification

        result = integrated_cpu_qualification(config, registration, root)
    elif args.command == "prepare":
        result = prepare_integrated_cases(
            config, registration, root, registration["rosters"][args.cohort]
        )
    elif args.command == "run":
        stage_spec(config, args.experiment)
        if args.model not in config["models"]:
            raise ValueError("Choose a registered model")
        import_prior_accounting(config, root)
        result = run_integrated(
            config,
            registration,
            root,
            args.experiment,
            args.model,
            args.smoke,
            args.repair,
        )
    elif args.command == "smoke":
        stage_spec(config, args.experiment)
        import_prior_accounting(config, root)
        result = integrated_smoke(
            config, registration, root, args.experiment, args.repair
        )
    elif args.command == "review":
        from .tests import review_integrated_smoke

        result = review_integrated_smoke(
            config, registration, root, args.experiment, args.repair
        )
    else:
        from .gates import analyze_integrated

        result = analyze_integrated(
            config, registration, root, args.experiment, args.command == "decide"
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str), flush=True)


def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in {
        "activate-formal",
        "queue",
        "register",
        "cpu-check",
        "repair-clocks",
        "setup-clock-smoke",
        "prepare",
        "run",
        "smoke",
        "review",
        "decide",
        "analyze",
    }:
        return integrated_cli(sys.argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="RQs/RQ3_4/configs/claim_audit_v4.json")
    args = parser.parse_args()
    result = audit(read_json(ROOT / args.config))
    if result["state"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

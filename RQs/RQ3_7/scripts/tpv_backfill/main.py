"""User-authorized 120-call TPV supplement; frozen A/B code remains untouched."""

import argparse
import concurrent.futures as cf
import fcntl
import json
import os
import pickle
import shutil
import signal
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path

from RQs.RQ3_7.src import exps, gates
from RQs.RQ3_7.src import main as parent
from RQs.RQ3_7.src.utils import (
    METRICS,
    ROOT,
    call_count,
    digest,
    read_json,
    runtime_config,
    save_json,
    sha,
    terminal_flag,
)

ID = "rq37_tpv_reference_backfill_v1"
MODULE = "RQs.RQ3_7.scripts.tpv_backfill.main"
BASE = ROOT / "RQs/RQ3_7/results/fusion_v2_pruned"
OUT = ROOT / "RQs/RQ3_7/results/tpv_reference_backfill_v1"
_TOKENS = None


def state(value, **extra):
    save_json(OUT / "queue_status.json", {
        "state": value, "pid": os.getpid(), "updated_unix": time.time(), **extra,
    })


def register():
    """Freeze only the 60 screen cases with old-unit TPV results, two models."""
    path = OUT / "registration.json"
    if path.exists():
        return checked()
    inherited = read_json(BASE / "registration.json")
    config = inherited["config"]
    gates.assert_current(config, inherited)
    old = ROOT / "RQs/RQ3_5/results/outcome_linked_v1"
    old_reg = read_json(old / "registration.json")
    screen = {r["opaque_incident_id"] for r in old_reg["rosters"]["screen"]}
    entries = {}
    for model in config["models"]:
        folder = old / "stages/screen_exp_outcome_linked_evidence" / model
        for p in sorted((folder / "outputs").glob("*.json")):
            record = read_json(p)
            if record.get("dimensions", {}).get("arm") != "TPV":
                continue
            key = record["call_key"]
            if (folder / "completed" / (key + ".json")).exists():
                entries[(model, record["opaque_incident_id"])] = {
                    "root": str(folder.relative_to(ROOT)), "call_key": key,
                }
    targets = []
    for original in gates.tasks(config, inherited, "A"):
        row, model = original["case"], original["model"]
        if original["dimensions"]["arm"] != "TPV_REF" or row["opaque_incident_id"] not in screen:
            continue
        flag = terminal_flag(BASE, original)
        if not flag or flag.get("failure_class") != "reference_unavailable":
            raise ValueError("Supplement must not rerun an already usable baseline")
        source = entries[(model, row["opaque_incident_id"])]
        task = {**original, "experiment_id": "TPV_BACKFILL",
                "experiment": "exp_numeric_relation_fusion_tpv_backfill",
                "stage": "formal_A_tpv_backfill", "reference_only": False,
                "ledger_scope": ID,
                "logical_key": digest([ID, model, row["opaque_incident_id"]])}
        targets.append({"task": task, "original_task": original, "source": source})
        save_json(OUT / "original_reference_flags" / (original["logical_key"] + ".json"), flag)
    if len(targets) != 120 or Counter(
        (t["task"]["model"], t["task"]["case"]["dataset"]) for t in targets
    ) != {(m, d): 20 for m in config["models"] for d in ("aiops2022", "aiops2025", "aegislab")}:
        raise ValueError("Expected exactly 60 cases / 120 targets, not the three timeouts")
    shared = ROOT / config["implementation"]["shared_ledger"]
    (OUT / "calls.sqlite").symlink_to(shared)
    value = {"schema_version": "RQ37TPVBackfillV1", "user_authorized": True,
             "authorization": "Add the 120 historical baseline reruns to the queue",
             "max_new_calls": 120, "scope": ID, "targets": targets,
             "parent_registration": str(BASE / "registration.json"),
             "parent_contract_hash": digest(inherited["contract"]),
             "script_sha256": sha(Path(__file__)), "created_unix": time.time(),
             "qualification_basis": "Unchanged RQ3.6 corrected TPV recipe and RQ3.7 runtime; CPU exact-input checks before submission",
             "cumulative_calls_at_registration": call_count(BASE),
             "planned_line_upper_after_amendment": config["budget"]["planned_new_upper"] + 120}
    save_json(path, value)
    state("registered", targets=120, new_calls=0)
    return value


def checked():
    r = read_json(OUT / "registration.json")
    p = read_json(r["parent_registration"])
    gates.assert_current(p["config"], p)
    if not r["user_authorized"] or r["max_new_calls"] != 120 or len(r["targets"]) != 120:
        raise ValueError("Backfill authorization changed")
    if r["script_sha256"] != sha(Path(__file__)) or r["parent_contract_hash"] != digest(p["contract"]):
        raise ValueError("Supplement source contract changed")
    if (OUT / "calls.sqlite").resolve() != (BASE / "calls.sqlite").resolve():
        raise ValueError("Supplement must share the existing cumulative ledger")
    for experiment in ("A", "B"):
        gates.authorize(p["config"], p, BASE, experiment)
    return r


def compile_pair(items):
    """Compare corrected saved inputs with the qualified recipe, without rendering."""
    global _TOKENS
    from RQs.RQ3_3.src.utils import OfflineTokens
    from RQs.RQ3_6.src.exps import parent_unit_labels
    from vlmrca.run_state import atomic_write

    registration = read_json(BASE / "registration.json")
    config = registration["config"]
    if _TOKENS is None:
        _TOKENS = OfflineTokens(runtime_config(config))
    context = parent.source_context(config, items[0]["task"]["case"], _TOKENS)
    parts, system = parent.reference_input(context, "TPV_REF", None, _TOKENS)
    # Saved requests exclude obsolete attention bookkeeping. Compare/send only
    # actual model-visible text and original PNG bytes; do not collect attention.
    parts = [{"type": p["type"], **({"text": p["text"]} if p["type"] == "text"
                                   else {"png": p["png"]})} for p in parts]
    identities = []
    for item in items:
        task = item["task"]
        old_parts, prompt = parent.bridge_parts(item["source"])
        corrected = parent_unit_labels(old_parts, context["rq36_parent_trace_unit"])
        if parts != corrected or system != prompt["system"]:
            raise ValueError("TPV changed beyond the registered unit-label substitutions")
        request = exps.compile_request(task, parts, context["candidates"], system, {
            "arm": "TPV_REF", "backfill_authorization": ID,
            "original_prompt_source": item["source"],
            "unit_adapter": "parent_trace_unit_labels_v1",
            "exact_corrected_parent_recipe": True,
        }, _TOKENS)
        key = task["logical_key"]
        atomic_write(OUT / "prepared" / (key + ".pkl"), pickle.dumps(request, protocol=5))
        save_json(OUT / "prepared" / (key + ".json"), {
            "status": "done", "logical_key": key, "input_identity": request["input_identity"],
            "model_token_counts": request["projection"]["model_token_counts"],
            "exact_corrected_parent_recipe": True,
        })
        identities.append(key)
    return identities


def prepare(registration, limit=None):
    from RQs.RQ3_6.src.main import close_pool, cpu_pool

    groups = defaultdict(list)
    for item in registration["targets"]:
        task = item["task"]
        if terminal_flag(OUT, task) is None and not (OUT / "prepared" / (task["logical_key"] + ".json")).exists():
            groups[task["case"]["opaque_incident_id"]].append(item)
    pairs = list(groups.values())
    if limit:
        pairs = [next(p for p in pairs if p[0]["task"]["case"]["dataset"] == d)
                 for d in ("aiops2022", "aiops2025", "aegislab")]
    if not pairs:
        return
    pool, core_queue, _ = cpu_pool(min(8, len(pairs)))
    failed = True
    try:
        for keys in pool.map(compile_pair, pairs):
            print(json.dumps({"prepared": len(keys), "case_pair_complete": True}), flush=True)
        failed = False
    finally:
        close_pool(pool, core_queue, abort=failed)


def execute(item, config, ledger):
    from RQs.RQ3_1.src.main import run_registered_call, score_response_callback
    from RQs.RQ3_3.src.main import timeout_exception

    task = item["task"]
    prior = terminal_flag(OUT, task)
    if prior:
        return prior
    request = pickle.loads((OUT / "prepared" / (task["logical_key"] + ".pkl")).read_bytes())
    destination = OUT / "stages" / task["stage"] / task["model"]
    key = request["task"]["call_key"]
    common = {"logical_key": task["logical_key"], "dimensions": task["dimensions"],
              "case": task["case"]["opaque_incident_id"], "model": task["model"],
              "experiment": "TPV_BACKFILL", "artifact_root": str(destination),
              "call_key": key, "input_identity": request["input_identity"]}
    projection = destination / "projections" / (key + ".json")
    save_json(projection, request["projection"])
    try:
        private = parent.private_for(config, BASE, task["case"])
        save_json(OUT / "activity" / (task["model"] + ".json"),
                  {"state": "submitting_request", "unix": time.time(), "key": key})
        result = run_registered_call(request["task"], request["parts"], request["envelope"],
            destination, ledger=ledger,
            score_response=score_response_callback(private, request["candidates"]))
        cost = read_json(destination / "cost" / (key + ".json"))
        metrics = result["score"].get("metrics") or result["score"]
        flag = {**common, "status": "done", "model_status": result["status"],
                "projection_path": str(projection), "metrics": {k: metrics[k] for k in METRICS},
                **{k: cost.get(k) for k in ("input_tokens", "output_tokens", "image_tokens", "text_tokens", "wall_time_s")},
                "new_generation_calls": cost.get("new_generation_calls", 1)}
    except Exception as exc:
        timeout = timeout_exception(exc)
        flag = {**common, "status": "fail", "failure_class": "request_timeout" if timeout else "infrastructure",
                "error": f"{type(exc).__name__}: {exc}", "auto_retry": False}
        save_json(OUT / "flags" / (task["logical_key"] + ".json"), flag)
        if not timeout:
            raise
        return flag
    save_json(OUT / "flags" / (task["logical_key"] + ".json"), flag)
    return flag


def run(model):
    from RQs.RQ3_3.src.main import exclusive
    from RQs.RQ3_6.src.utils import interrupted_calls
    from vlmrca.run_state import DurableCallRegister

    r = checked()
    config = read_json(BASE / "registration.json")["config"]
    if model not in config["models"]:
        raise ValueError("Unknown model")
    pending = [i for i in r["targets"] if i["task"]["model"] == model and terminal_flag(OUT, i["task"]) is None]
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    with exclusive(OUT / "run.lock"):
        interrupted_calls(OUT, ID)
        ledger = DurableCallRegister(OUT / "calls.sqlite", limit=40000, scope=ID, scope_limit=120)
        done = 60 - len(pending)
        with cf.ThreadPoolExecutor(max_workers=36) as pool:
            items, active = iter(pending), set()
            try:
                while True:
                    if shutil.disk_usage(OUT).free < config["execution"]["min_free_disk_gib"] * 1024**3:
                        raise OSError("Low disk; drain without new submissions")
                    while not stop.is_set() and len(active) < 36:
                        item = next(items, None)
                        if item is None:
                            break
                        active.add(pool.submit(execute, item, config, ledger))
                    if not active:
                        break
                    completed, active = cf.wait(active, timeout=1, return_when=cf.FIRST_COMPLETED)
                    for future in completed:
                        future.result()
                        done += 1
                    if completed:
                        save_json(OUT / "progress" / (model + ".json"), {"terminal": done, "total": 60, "active": len(active)})
                        print(json.dumps({"model": model, "terminal": done, "total": 60}), flush=True)
            except BaseException:
                stop.set()
                for future in active:
                    future.cancel()
                raise
        if stop.is_set():
            raise InterruptedError("Backfill paused; done/fail records retained")


def publish(registration):
    """Attach the supplement only after all 120 units terminate and writers drain."""
    for item in registration["targets"]:
        f = terminal_flag(OUT, item["task"])
        if not f or f.get("failure_class") == "infrastructure":
            raise ValueError("Incomplete backfill cannot replace reference placeholders")
    for item in registration["targets"]:
        original = item["original_task"]
        old_path = OUT / "original_reference_flags" / (original["logical_key"] + ".json")
        current = terminal_flag(BASE, original)
        if current != read_json(old_path) and current.get("supplemental_authorization") != ID:
            raise ValueError("Unexpected concurrent reference replacement")
        f = terminal_flag(OUT, item["task"])
        save_json(BASE / "flags" / (original["logical_key"] + ".json"), {
            **f, "logical_key": original["logical_key"], "experiment": "A",
            "dimensions": original["dimensions"], "supplemental_authorization": ID,
            "supplemental_flag": str(OUT / "flags" / (item["task"]["logical_key"] + ".json")),
            "original_reference_flag": str(old_path),
        })
    save_json(OUT / "publication.json", {"status": "complete", "targets": 120,
              "initiated_calls": call_count(OUT, ID), "original_results_modified": False})


def queue():
    from RQs.RQ3_3.src.main import exclusive

    r = checked()
    def interrupt(*_):
        raise InterruptedError("Supplement queue paused")
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, interrupt)
    try:
        with exclusive(OUT / "queue.lock"), (BASE / "queue.lock").open("a") as predecessor:
            state("waiting_for_A_B", max_new_calls=120)
            fcntl.flock(predecessor.fileno(), fcntl.LOCK_EX)  # Blocking wait; no polling/server.
            p = read_json(BASE / "registration.json")
            q = read_json(BASE / "queue_status.json")
            if q != {"state": "passed", "experiment": "B", "smoke": False}:
                raise ValueError("Predecessor did not finish A/B normally; do not auto-resume it")
            if any(terminal_flag(BASE, t) is None for e in ("A", "B") for t in gates.tasks(p["config"], p, e)):
                raise ValueError("Predecessor has uncommitted targets")
            checked()
            state("preparing", max_new_calls=120)
            prepare(r)
            # Reuse the already qualified server lifecycle; override only the child CLI module.
            parent.MODULE = MODULE
            for model in p["config"]["models"]:
                if any(i["task"]["model"] == model and terminal_flag(OUT, i["task"]) is None for i in r["targets"]):
                    state("running", model=model, max_new_calls=120)
                    parent.launch_model(p["config"], p, OUT, "TPV_BACKFILL", model, time.time() + 365 * 86400)
            publish(r)
            state("complete", targets=120, initiated_calls=call_count(OUT, ID))
    except BaseException as exc:
        state("paused" if isinstance(exc, InterruptedError) else "failed", error=f"{type(exc).__name__}: {exc}")
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "check", "queue", "run"))
    parser.add_argument("--model")
    parser.add_argument("--experiment", choices=("TPV_BACKFILL",), default="TPV_BACKFILL")
    args = parser.parse_args()
    if args.action == "register":
        r = register()
        print(json.dumps({"registered": len(r["targets"]), "additional_calls_max": 120}))
    elif args.action == "check":
        prepare(checked(), limit=3)
        print(json.dumps({"cpu_cases": 3, "model_requests_checked": 6, "new_calls": 0}))
    elif args.action == "queue":
        queue()
    else:
        run(args.model)


if __name__ == "__main__":
    main()

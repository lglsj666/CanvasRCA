"""Additive C activation: terminal aliases, boundary checks, cold preparation.

Frozen source, completed inputs/outputs and roster remain unchanged. Cold
contexts use the separately recorded, source-bound nested-log-clock repair.
Run as a module after scripts/env_local.sh. No model calls in this module.
"""

import argparse
import concurrent.futures as cf
import signal
import time
from collections import Counter, defaultdict

from RQs.RQ3_7.src import gates
from RQs.RQ3_7.src.main import compile_case
from RQs.RQ3_7.src.tests import persist_cpu_input
from RQs.RQ3_7.src.utils import (
    ROOT,
    call_count,
    digest,
    load_config,
    read_json,
    runtime_config,
    save_json,
    sha,
    terminal_flag,
)


def compile_prepared(arguments):
    """Fill the missing parent intermediate before the frozen C compiler.

    Only cold case contexts change from absent to complete. The original parent
    chooses MORE cumulatively at 1024 then 2048. Its integrated preflight still
    checks the inherited P/H cells; no such model calls are scheduled. Existing
    A/B public caches and all frozen source are untouched.
    """
    import pickle

    from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
    from RQs.RQ3_3.src.exps import choose_parent_tail
    from RQs.RQ3_3.src.utils import OfflineTokens, prepare_public_context
    from RQs.RQ3_4.src.exps import assert_no_absolute_clock, prepare_integrated
    from RQs.RQ3_4.src.utils import metric_selection_metadata
    from RQs.RQ3_7.scripts.stage_c.clock_projection import project_log_clocks
    from RQs.RQ3_7.src import main as runner
    from vlmrca.run_state import atomic_write

    config, _registration, targets = arguments
    root = ROOT / config["implementation"]["output_root"]
    row = targets[0]["case"]
    oid = row["opaque_incident_id"]
    parent_root = ROOT / config["implementation"]["source_run"]
    local = root / "contexts" / (oid + ".pkl")
    marker = root / "preparation_flags" / (oid + ".json")
    if not (parent_root / "contexts" / (oid + ".pkl")).exists() and not (
        local.exists() and marker.exists()
    ):
        started = time.monotonic()
        base = runtime_config(config)
        if runner._TOKENS is None:
            runner._TOKENS = OfflineTokens(base)
        tokens = runner._TOKENS
        context, private = prepare_public_context(row, base)
        context["observations"], clock_audit = project_log_clocks(context["observations"])
        if clock_audit["observations"]:
            save_json(root / "diagnostics/log_clock_projection" / (oid + ".json"), clock_audit)
        parent = read_json(ROOT / "RQs/RQ3_4/configs/integrated_round_v1.json")
        more = []
        context["selections"] = {}
        for budget in sorted(map(int, base["witness"]["budget_pack_limits"])):
            if budget > 2048:
                break
            more = choose_parent_tail(context, tokens, budget, RCA_SYSTEM_ROLE, more)
            context["selections"][f"{budget}:more"] = {"items": more}
        context["selection_metadata"] = metric_selection_metadata(context, row, parent)
        try:
            context["integrated"] = prepare_integrated(context, tokens, parent)
        except Exception as exc:
            # Preserve the exact offending public line, never a private object.
            detail = {"case": oid, "error": f"{type(exc).__name__}: {exc}",
                      "helper_sha256": sha(__file__)}
            trace = exc.__traceback__
            while trace:
                frame = trace.tb_frame
                if frame.f_code.co_name == "assert_no_absolute_clock":
                    detail["public_line"] = frame.f_locals.get("line")
                trace = trace.tb_next
            save_json(root / "diagnostics" / "preparation_errors" / (oid + ".json"), detail)
            raise
        assert not context["prepared"].private
        atomic_write(local, pickle.dumps(context, protocol=5))
        save_json(root / "private" / (oid + ".json"), private)
        save_json(marker, {"status": "done", "case": oid,
                           "adapter": "rq37_c_parent_intermediate_v1",
                           "clock_projection": clock_audit["version"],
                           "clock_projection_sha256": sha(ROOT / "RQs/RQ3_7/scripts/stage_c/clock_projection.py"),
                           "helper_sha256": sha(__file__),
                           "elapsed_s": time.monotonic() - started})
    compiled = compile_case(arguments)
    for _task, request in compiled:
        if "parts" in request:
            assert_no_absolute_clock(request["parts"])
    return compiled


def scope():
    config = load_config()
    root = ROOT / config["implementation"]["output_root"]
    registration = read_json(root / "registration.json")
    gates.assert_current(config, registration)
    return config, registration, root


def identity(task):
    return (task["model"], task["case"]["opaque_incident_id"],
            task["dimensions"]["arm"], task["dimensions"]["encoding"],
            task["dimensions"]["replicate"])


def initialize(config, registration, root):
    started = time.monotonic()
    recommendation = read_json(root / "analysis/expansion.json")
    assert recommendation["recommend_expand"]
    assert recommendation["contract_hash"] == digest(registration["contract"])
    assert not registration["rosters"]["fresh"]
    sources = {identity(t): t for t in gates.tasks(config, registration, "A")}
    aliases, existing = [], 0
    for task in gates.tasks(config, registration, "C"):
        if terminal_flag(root, task) is not None:
            existing += 1
            continue
        source = sources.get(identity(task))
        if source is None:
            continue
        flag = terminal_flag(root, source)
        if flag is None:
            raise ValueError("A must be complete before C activation")
        assert flag["case"] == task["case"]["opaque_incident_id"]
        assert flag["model"] == task["model"]
        assert {k: v for k, v in flag["dimensions"].items() if k != "cohort"} == {
            k: v for k, v in task["dimensions"].items() if k != "cohort"}
        value = {**flag, "logical_key": task["logical_key"], "experiment": "C",
                 "dimensions": task["dimensions"], "new_generation_calls": 0,
                 "reused_from": source["logical_key"],
                 "terminal_alias_contract": digest(registration["contract"])}
        save_json(root / "flags" / (task["logical_key"] + ".json"), value)
        aliases.append({"source": source["logical_key"], "target": task["logical_key"],
                        "status": value["status"], "failure_class": value.get("failure_class")})
    targets = gates.tasks(config, registration, "C")
    pending = [t for t in targets if terminal_flag(root, t) is None]
    spent = call_count(root)
    if spent + len(pending) + 18 > config["budget"]["hard_limit"]:
        raise ValueError("C conservative budget does not fit shared ceiling")
    result = {"status": "initialized", "contract_hash": digest(registration["contract"]),
              "helper_sha256": sha(__file__), "logical_total": len(targets),
              "existing_terminal": existing, "new_aliases": aliases,
              "pending_upper": len(pending), "cumulative_calls": spent,
              "elapsed_s": time.monotonic() - started,
              "fresh_status": registration["fresh_status"],
              "old_artifacts_opened": "small terminal flags only; no contexts or requests"}
    destination = root / "stage_c_activation.json"
    if not destination.exists():
        save_json(destination, result)
    return {k: v for k, v in result.items() if k != "new_aliases"} | {"aliased": len(aliases)}


def work(config, registration, root, check):
    from RQs.RQ3_3.src.main import exclusive, interleaved_sources
    from RQs.RQ3_6.src.main import close_pool, cpu_pool

    started = time.monotonic()
    report_path = root / ("stage_c_boundary_check.json" if check else "stage_c_preparation.json")
    if report_path.exists():
        old = read_json(report_path)
        if old.get("status") == "passed" and old["contract_hash"] == digest(registration["contract"]):
            return {"status": "already_complete", "report": str(report_path)}
        save_json(root / "diagnostics/preparation_attempts" / (digest(old) + ".json"), old)
    targets = gates.tasks(config, registration, "C")
    targets = [t for t in targets if terminal_flag(root, t) is None]
    groups = defaultdict(list)
    for task in targets:
        groups[task["case"]["opaque_incident_id"]].append(task)
    rows = [v[0]["case"] for v in groups.values()]
    if check:
        # Three cold primary test cases and the two new RE2 schema paths.
        rows = [min((r for r in rows if r["dataset"] == dataset and
                     r["partition"] == ("eval" if dataset.startswith("re2") else "test")),
                    key=lambda r: digest([42, "rq37_c_boundary", r["opaque_incident_id"]]))
                for dataset in ("aiops2022", "aiops2025", "aegislab", "re2_ob", "re2_tt")]
        # CPU-only execution safety; no labels/outcomes influence selection or method.
    else:
        cache = root / "public_cache" / digest(registration["contract"])
        rows = [r for r in rows if not (cache / (r["opaque_incident_id"] + ".pkl")).exists()]
    ordered = interleaved_sources(rows)
    report = {"status": "running", "contract_hash": digest(registration["contract"]),
              "helper_sha256": sha(__file__), "cases": len(rows), "completed": [],
              "dataset_counts": dict(Counter(r["dataset"] for r in rows)),
              "model_calls": 0}
    pool = queue = None
    previous = {}

    def halt(*_):
        raise InterruptedError("CPU preparation interrupted; completed per-case cache preserved")

    try:
        with exclusive(root / "stage_c_preparation.lock"):
            if not check:
                save_json(root / "queue_status.json", {
                    "state": "preparing", "experiment": "C", "smoke": False,
                    "preparation_progress": report_path.name, "remaining_cases": len(rows)})
            for sig in (signal.SIGTERM, signal.SIGINT):
                previous[sig] = signal.signal(sig, halt)
            if check:
                previous[signal.SIGALRM] = signal.signal(signal.SIGALRM, halt)
                signal.setitimer(signal.ITIMER_REAL, 1800)
            if ordered:
                pool, queue, workers = cpu_pool(min(8, len(ordered)))
                report["workers"] = workers
                waiting = iter(ordered)
                active = {}
                while True:
                    while len(active) < workers:
                        row = next(waiting, None)
                        if row is None:
                            break
                        tasks = groups[row["opaque_incident_id"]]
                        if not check:
                            # Materialize the one shared public view, not all renderings.
                            tasks = [next(t for t in tasks if t["dimensions"]["arm"] == "T_MATCH")]
                        future = pool.submit(compile_prepared, (config, registration, tasks))
                        active[future] = row
                    if not active:
                        break
                    done, _ = cf.wait(active, return_when=cf.FIRST_COMPLETED)
                    for future in done:
                        row = active.pop(future)
                        try:
                            compiled = future.result()
                        except Exception:
                            report["failed_case"] = row["opaque_incident_id"]
                            report["failed_dataset"] = row["dataset"]
                            raise
                        for task, request in compiled:
                            if check:
                                persist_cpu_input(root, task, request)
                            if "reference_unavailable" in request or "design_infeasible" in request:
                                raise ValueError(f"Boundary requires review: {row['opaque_incident_id']} {request}")
                            if check:
                                assert request["envelope"]["effective_server"]["max_tokens"] == 8192
                                assert not request["projection"]["attention"]
                        report["completed"].append({"case": row["opaque_incident_id"],
                                                    "requests": len(compiled)})
                        report["elapsed_s"] = time.monotonic() - started
                        save_json(report_path, report)
                        print(f"CPU {'check' if check else 'prepare'} {len(report['completed'])}/{len(rows)} "
                              f"{row['dataset']} {row['opaque_incident_id']}", flush=True)
            report["status"] = "passed"
    except BaseException as exc:
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if check:
            signal.setitimer(signal.ITIMER_REAL, 0)
        if pool:
            close_pool(pool, queue, abort=report["status"] != "passed")
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        report["elapsed_s"] = time.monotonic() - started
        save_json(report_path, report)
        if not check:
            save_json(root / "queue_status.json", {
                "state": "preparation_complete" if report["status"] == "passed" else "failed",
                "experiment": "C", "smoke": False,
                "preparation_progress": report_path.name,
                "completed_this_attempt": len(report["completed"]),
                "error": report.get("error"), "failed_case": report.get("failed_case")})
    return {k: v for k, v in report.items() if k != "completed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("initialize", "check", "prepare"))
    args = parser.parse_args()
    config, registration, root = scope()
    if args.action == "prepare":
        gates.authorize(config, registration, root, "C")
    print(initialize(config, registration, root) if args.action == "initialize"
          else work(config, registration, root, args.action == "check"), flush=True)

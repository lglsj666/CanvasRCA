"""Command-line entry point for RQ3.2 registration, preparation, smoke, and runs."""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

from RQs.RQ3_1.src.main import aggregate_result_summary, run_registered_call
from RQs.RQ3_1.src.utils import read_json
from unified_scripts import stable_hash
from vlmrca.run_state import DurableCallRegister, write_json

from .contracts import (
    CONFIG,
    CONTEXTS,
    LEDGER,
    REDUNDANT_NOISE_POLICY_VERSION,
    audit_config,
    load_config,
    dimensions,
    roster,
    smoke_dimension,
    smoke_roster,
    source_hashes,
    task_matrix,
)
from .experiments import ContextStore, DesignNotApplicable, prepare_contexts, run_cpu_qualification
from .representation import build_context_safe_selection_request, build_request

RESUME_VERIFICATION_LIMIT_S = 900.0


def _is_request_timeout(exc: BaseException) -> bool:
    """Recognize a model-request transport timeout through wrapper exceptions."""
    seen: set[int] = set()
    current: BaseException | None = exc
    timeout_names = {
        "apitimeouterror", "connecttimeout", "pooltimeout", "readtimeout",
        "timeoutexception", "timeout", "timeouterror", "writetimeout",
    }
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        message = str(current).lower()
        if "smoke deadline" in message or "smoke window" in message:
            return False
        if isinstance(current, TimeoutError) or type(current).__name__.lower() in timeout_names:
            return True
        current = current.__cause__ or current.__context__
    return False


def _failure_disposition(exc: BaseException) -> tuple[str, bool]:
    """Return the terminal flag status and whether submission must stop."""
    return ("request_timeout", False) if _is_request_timeout(exc) else ("failed", True)


def _logical_task_key(task):
    """Cheap identity used only to avoid rebuilding completed requests."""
    identity = {"registration": "rq32_signal_cover_v2", "adapter": "rq32_solver_request_v2",
        "experiment": task["experiment"], "model": task["model"],
        "case": task["case"]["opaque_incident_id"],
        "dimensions": dict(sorted(task["dimensions"].items()))}
    if (task["experiment"] == "exp_signal_mechanisms" and
            task["dimensions"].get("condition") == "REDUNDANT_NOISE"):
        identity["intervention_version"] = REDUNDANT_NOISE_POLICY_VERSION
    return stable_hash(identity)


def _resume_journal_path(output: Path, model: str) -> Path:
    return Path(output) / "resume" / f"{model}.jsonl"


def _load_resume_journal(output: Path, experiment: str, model: str) -> dict[str, dict[str, str]]:
    """Read an append-only logical-key index; never hash historical artifacts."""
    path = _resume_journal_path(output, model); entries = {}
    if not path.is_file(): return entries
    lines = path.read_text().splitlines()
    for number, line in enumerate(lines, 1):
        if not line.strip(): continue
        try: row = json.loads(line)
        except json.JSONDecodeError:
            if number == len(lines): break
            raise ValueError("corrupt non-terminal resume journal row")
        if (row.get("schema_version") != "RQ32ResumeJournalV1" or
                row.get("experiment") != experiment or row.get("model") != model):
            raise ValueError("resume journal belongs to another phase")
        logical = str(row.get("logical_key")); entry = {
            "status": str(row.get("status", "complete")), "call_key": str(row.get("call_key", ""))}
        if entry["status"] == "retry_authorized":
            # A failed unit remains terminal by default.  Only an explicit,
            # append-only tombstone written after a reviewed implementation or
            # infrastructure repair may return it to the pending queue.
            if logical not in entries or entries[logical]["status"] != "failed":
                raise ValueError("retry authorization does not supersede a failed unit")
            entries.pop(logical)
            continue
        if logical in entries and entries[logical] != entry:
            raise ValueError("resume journal maps one logical task to multiple calls")
        entries[logical] = entry
    return entries


def _resume_entry_ready(output: Path, logical: str, entry: dict[str, str]) -> bool:
    if entry.get("status") == "not_applicable":
        path = Path(output) / "interventions" / f"{logical}.json"
        return path.is_file()
    if entry.get("status") in {"model_failure", "request_timeout", "failed"}:
        return (Path(output) / "failed" / f"{logical}.json").is_file()
    call_key = entry.get("call_key", "")
    marker = Path(output) / "completed" / f"{call_key}.json"
    # The marker is the atomic transaction boundary and was hash-audited when
    # it was committed. Resume deliberately performs existence checks only;
    # reconstructing or re-hashing every completed request made restarts take
    # hours without adding scientific evidence.
    return marker.is_file()


def _append_resume_journal(output: Path, task, call_key: str = "", *, status: str = "complete") -> None:
    path = _resume_journal_path(output, task["model"]); path.parent.mkdir(parents=True, exist_ok=True)
    row = {"schema_version": "RQ32ResumeJournalV1", "experiment": task["experiment"],
        "model": task["model"], "logical_key": _logical_task_key(task), "call_key": call_key}
    row["status"] = status
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def run_experiment(experiment: str, contexts: Path, output: Path, *, model: str,
                   smoke: bool = False, concurrency: int = 36, deadline: float | None = None):
    config = load_config()
    store = ContextStore(contexts, max_cached_cases=config["artifacts"]["context_cache_cases"])
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    method_lock = None
    if experiment == "exp_signal_locked_generalization" and not smoke:
        lock_path = Path(__file__).resolve().parents[3] / config["artifacts"]["formal_root"] / "method_lock.json"
        if not lock_path.is_file() or read_json(lock_path).get("status") != "frozen_before_locked_generalization":
            raise ValueError("locked generalization requires the frozen RQ3.2 method/budget lock")
        method_lock = read_json(lock_path)
    cases = smoke_roster(config) if smoke else None
    dimension = smoke_dimension(config, experiment) if smoke else None
    tasks = task_matrix(config, experiment, cases, models=[model], one_dimension=dimension)
    ledger = DurableCallRegister(LEDGER, limit=config["budget"]["hard_limit"],
        scope=f"smoke:{config['registration_id']}:{experiment}" if smoke else experiment,
        scope_limit=config["smoke"]["max_calls_per_experiment"] if smoke else None)
    if not smoke:
        # A stopped owner may leave spent calls in ``started``. They have no
        # atomic logical completion flag and are therefore the exact units the
        # user requires us to rerun. This is a constant-time SQLite update, not
        # artifact reconstruction or historical request verification.
        ledger.interrupt_scope("prior formal owner stopped without terminal logical flag")
    state_path = output / f"state.{model}.json"
    state = {"schema_version": "RQ32RunStateV1", "experiment": experiment, "model": model,
             "registered": len(tasks), "started_at": time.time(), "status": "running", "failures": []}
    write_json(state_path, state)

    def submit(task):
        if deadline is not None and time.monotonic() >= deadline: raise TimeoutError("smoke deadline reached")
        context = store[task["case"]["opaque_incident_id"]]
        if method_lock is not None: context["_locked_arm"] = method_lock["winner"]
        request, scorer = build_request(task, context); bound = request["task"]
        complete = output / "completed" / f"{bound['call_key']}.json"
        if complete.is_file(): return read_json(output / "outputs" / f"{bound['call_key']}.json")
        # ``run_registered_call`` is the sole persistence owner for prompts and
        # image bytes.  A former pre-write created ``.<index>.png`` here and the
        # canonical transaction then wrote an identical ``_<index>.png`` copy.
        # Keeping one owner avoids duplicate formal renders while preserving
        # the same request parts and model-visible PNG bytes.
        try:
            return run_registered_call(bound, request["parts"], request["envelope"], output,
                score_response=scorer, ledger=ledger,
                scope_limit=config["smoke"]["max_calls_per_experiment"] if smoke else None)
        except ValueError as exc:
            if ("input exceeds context:" not in str(exc) or
                    task["experiment"] != "exp_signal_selection"):
                raise
            request, scorer = build_context_safe_selection_request(
                task, context, max_tokens=config["request"]["max_tokens"],
                overflow_request=request)
            bound = request["task"]
            write_json(output / "capacity" / f"{bound['call_key']}.json", {
                "schema_version": "RQ32TextCapacityRecordV1",
                "experiment": task["experiment"], "model": task["model"],
                "case": {key: task["case"].get(key) for key in
                         ("dataset", "opaque_incident_id")},
                "dimensions": dict(task["dimensions"]),
                "call_key": bound["call_key"],
                "request_hash": bound["request_hash"],
                "projection_hash": bound["projection_hash"],
                "capacity_adapter": dict(bound["capacity_adapter"]),
            })
            return run_registered_call(bound, request["parts"], request["envelope"], output,
                score_response=scorer, ledger=ledger,
                scope_limit=config["smoke"]["max_calls_per_experiment"] if smoke else None)

    journal = _load_resume_journal(output, experiment, model)
    ready = {_logical_task_key(task): journal[_logical_task_key(task)] for task in tasks
             if _logical_task_key(task) in journal and
             _resume_entry_ready(output, _logical_task_key(task), journal[_logical_task_key(task)])}
    completed_keys = {entry["call_key"] for entry in ready.values()
                      if entry["status"] in {"complete", "model_failure"}}
    model_failures = sum(entry["status"] == "model_failure" for entry in ready.values())
    request_timeouts = sum(entry["status"] == "request_timeout" for entry in ready.values())
    failed_terminal = sum(entry["status"] == "failed" for entry in ready.values())
    not_applicable = sum(entry["status"] == "not_applicable" for entry in ready.values())
    completed = len(completed_keys)
    pending = iter([(task, _logical_task_key(task)) for task in tasks
                    if _logical_task_key(task) not in ready])
    active = {}; abort_submission = False
    try:
        with ThreadPoolExecutor(max_workers=min(concurrency, len(tasks))) as executor:
            while True:
                while not abort_submission and len(active) < concurrency:
                    try: task, logical = next(pending)
                    except StopIteration: break
                    if deadline is not None and time.monotonic() >= deadline: break
                    active[executor.submit(submit, task)] = (task, logical)
                if not active: break
                timeout = None if deadline is None else max(0.0, deadline - time.monotonic())
                done, _ = wait(active, timeout=timeout, return_when=FIRST_COMPLETED)
                if not done: raise TimeoutError("smoke deadline reached")
                for future in done:
                    task, logical = active.pop(future)
                    try:
                        result = future.result(); completed += 1; completed_keys.add(result["call_key"])
                        result_status = "model_failure" if result.get("status") == "model_failure" else "complete"
                        entry = {"status": result_status, "call_key": result["call_key"]}
                        if journal.get(logical) != entry:
                            if result_status == "model_failure":
                                write_json(output / "failed" / f"{logical}.json", {
                                    "schema_version": "RQ32TerminalFailureFlagV1", "status": "model_failure",
                                    "experiment": experiment, "model": model,
                                    "case": {key: task["case"].get(key) for key in ("dataset", "opaque_incident_id")},
                                    "dimensions": task["dimensions"], "call_key": result["call_key"],
                                    "automatic_retry": False})
                                model_failures += 1
                            _append_resume_journal(output, task, result["call_key"], status=result_status)
                            journal[logical] = entry
                    except DesignNotApplicable as exc:
                        intervention = {"schema_version": "RQ32InterventionNonCallV1", "status": "not_applicable",
                            "experiment": experiment, "model": model,
                            "case": {key: task["case"].get(key) for key in ("dataset", "opaque_incident_id")},
                            "dimensions": task["dimensions"], "reason": str(exc), "model_calls": 0}
                        write_json(output / "interventions" / f"{logical}.json", intervention)
                        _append_resume_journal(output, task, status="not_applicable")
                        journal[logical] = {"status": "not_applicable", "call_key": ""}
                        not_applicable += 1
                    except Exception as exc:
                        failure_status, should_abort = _failure_disposition(exc)
                        is_request_timeout = failure_status == "request_timeout"
                        failure = {"schema_version": "RQ32TerminalFailureFlagV1", "status": failure_status,
                            "experiment": experiment, "model": model,
                            "case": {key: task["case"].get(key) for key in ("dataset", "opaque_incident_id")},
                            "dimensions": task["dimensions"], "error": f"{type(exc).__name__}: {exc}",
                            "failure_class": "request_timeout" if is_request_timeout else "infrastructure_or_implementation",
                            "automatic_retry": False}
                        write_json(output / "failed" / f"{logical}.json", failure)
                        _append_resume_journal(output, task, status=failure_status)
                        journal[logical] = {"status": failure_status, "call_key": ""}
                        if is_request_timeout:
                            request_timeouts += 1
                        else:
                            state["failures"].append(failure); failed_terminal += 1
                        if should_abort:
                            abort_submission = True
                if abort_submission and not active:
                    break
    except TimeoutError:
        state["status"] = "timeout" if not state["failures"] else "failed"
    else:
        terminal = completed + not_applicable + request_timeouts + failed_terminal
        state["status"] = ("complete" if terminal == len(tasks) and not state["failures"] else
                           "complete_with_failures" if terminal == len(tasks) else "incomplete")
    state.update(completed=completed, model_failures=model_failures, request_timeouts=request_timeouts,
        failed_terminal=failed_terminal, not_applicable=not_applicable,
        terminal_units=completed + not_applicable + request_timeouts + failed_terminal,
        ended_at=time.time(), artifact_hash=stable_hash({"experiment": experiment, "model": model,
        "completed": completed, "not_applicable": not_applicable,
        "request_timeouts": request_timeouts, "failed_terminal": failed_terminal,
        "failures": state["failures"]}))
    write_json(state_path, state)
    if completed_keys:
        summary = aggregate_result_summary(output, completed_keys, experiment=experiment)
        summary["rq32_status"] = state["status"]
        summary["not_applicable"] = not_applicable
        summary["model_failures"] = model_failures
        summary["request_timeouts"] = request_timeouts
        summary["terminal_failures"] = failed_terminal
        summary["submitted_model_calls"] = completed
        write_json(output / f"summary.{model}.json", summary)
        if state["status"] in {"complete", "complete_with_failures"} and summary.get("status") == "complete":
            write_json(output / f"phase_complete.{model}.json", {
                "schema_version": "RQ32PhaseCompletionV1", "status": state["status"],
                "experiment": experiment, "model": model, "registered": len(tasks),
                "submitted_model_calls": completed, "model_failures": model_failures,
                "request_timeouts": request_timeouts, "terminal_failures": failed_terminal,
                "not_applicable": not_applicable})
    return state


def phase_status(config, experiment: str, model: str, output: Path) -> dict[str, object]:
    """Bounded existence-only resume check used before starting vLLM."""
    expected = len(roster(config, experiment)) * len(dimensions(config, experiment))
    marker = Path(output) / f"phase_complete.{model}.json"
    if marker.is_file():
        value = read_json(marker)
        if (value.get("schema_version") == "RQ32PhaseCompletionV1" and
                value.get("status") in {"complete", "complete_with_failures"} and
                value.get("experiment") == experiment and value.get("model") == model and
                int(value.get("registered", -1)) == expected):
            return {"status": "complete", "expected": expected,
                    "completed": int(value.get("submitted_model_calls", 0)),
                    "request_timeouts": int(value.get("request_timeouts", 0)),
                    "terminal_failures": int(value.get("terminal_failures", 0)),
                    "not_applicable": int(value.get("not_applicable", 0)),
                    "verification_seconds": 0.0, "mode": "phase_marker"}
        raise ValueError("phase completion marker is inconsistent with the registered phase")
    started = time.monotonic(); journal = _load_resume_journal(output, experiment, model)
    ready_calls = ready_non_calls = ready_timeouts = ready_failures = 0
    for task in task_matrix(config, experiment, models=[model]):
        logical = _logical_task_key(task); entry = journal.get(logical)
        if entry and _resume_entry_ready(output, logical, entry):
            if entry["status"] == "not_applicable": ready_non_calls += 1
            elif entry["status"] == "request_timeout": ready_timeouts += 1
            elif entry["status"] == "failed": ready_failures += 1
            else: ready_calls += 1
        if time.monotonic() - started > RESUME_VERIFICATION_LIMIT_S:
            return {"status": "verification_too_slow", "expected": expected,
                    "verification_seconds": time.monotonic() - started}
    elapsed = time.monotonic() - started
    return {"status": "incomplete", "expected": expected, "completed": ready_calls,
            "not_applicable": ready_non_calls, "request_timeouts": ready_timeouts,
            "terminal_failures": ready_failures,
            "pending": expected - ready_calls - ready_non_calls - ready_timeouts - ready_failures,
            "verification_seconds": elapsed, "mode": "journal_existence_scan"}


def freeze_method(formal_root: Path):
    root = Path(formal_root); lock_path = root / "method_lock.json"
    if lock_path.exists(): raise ValueError("RQ3.2 method lock is immutable once written")
    selection = root / "exp_signal_selection"; representation = root / "exp_signal_representation"
    for model in ("qwen3.8-27b", "gemma-4-26b-a4b"):
        for stage in (selection, representation):
            if read_json(stage / f"summary.{model}.json").get("rq32_status") != "complete":
                raise ValueError("method lock requires complete selection and representation phases")
    rows = read_json(selection / "summary.qwen3.8-27b.json")["records"]
    primary = {"aegislab", "aiops2022", "aiops2025"}; scores = {}
    for arm in ("SC_FULL", "SC_MORE"):
        grouped = {dataset: [] for dataset in primary}
        for row in rows:
            if row.get("dimensions", {}).get("arm") == arm and row.get("dataset") in primary:
                grouped[row["dataset"]].append(float(row["metrics"]["mrr"]))
        if any(not values for values in grouped.values()): raise ValueError(f"incomplete lock evidence for {arm}")
        scores[arm] = sum(sum(values) / len(values) for values in grouped.values()) / len(primary)
    winner = "SC_FULL" if scores["SC_FULL"] >= scores["SC_MORE"] - .01 else "SC_MORE"
    lock = {"schema_version": "RQ32MethodLockV1", "status": "frozen_before_locked_generalization",
            "winner": winner, "rule": "qwen_three_primary_equal_macro_mrr_then_smaller_budget_within_0.01",
            "scores": scores, "selection_summary_hash": stable_hash(rows), "frozen_at": time.time()}
    lock["lock_hash"] = stable_hash(lock); write_json(lock_path, lock); return lock


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("static", "prepare", "qualify", "freeze", "run", "phase-status"))
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--contexts", type=Path, default=CONTEXTS)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--experiment", choices=("exp_signal_selection", "exp_signal_representation",
                        "exp_signal_mechanisms", "exp_signal_locked_generalization"))
    parser.add_argument("--model", choices=("qwen3.8-27b", "gemma-4-26b-a4b"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--smoke-contexts", action="store_true")
    parser.add_argument("--partition", choices=("eval", "test"), default="eval")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--concurrency", type=int, default=36)
    parser.add_argument("--deadline-seconds", type=int)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    if args.command == "static":
        print(json.dumps({**audit_config(config), "source_hashes": source_hashes()}, indent=2)); return 0
    if args.command == "prepare":
        rows = smoke_roster(config) if args.smoke_contexts else None
        result = prepare_contexts(config, args.contexts, rows=rows, partition=args.partition, workers=args.workers)
        print(json.dumps({"status": result["status"], "cases": len(result["cases"]),
                          "path": str(args.contexts)}, indent=2)); return 0
    if args.command == "qualify":
        if not args.output: parser.error("qualify requires --output")
        result = run_cpu_qualification(config, args.contexts, args.output)
        print(json.dumps({"status": result["status"], "requests": len(result["requests"]),
                          "model_calls": 0}, indent=2)); return 0
    if args.command == "freeze":
        root = args.output or Path(config["artifacts"]["formal_root"])
        print(json.dumps(freeze_method(root), indent=2)); return 0
    if args.command == "phase-status":
        if not args.experiment or not args.model or not args.output:
            parser.error("phase-status requires --experiment, --model, and --output")
        result = phase_status(config, args.experiment, args.model, args.output)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "complete" else 4 if result["status"] == "verification_too_slow" else 3
    if not args.experiment or not args.model or not args.output:
        parser.error("run requires --experiment, --model, and --output")
    deadline = time.monotonic() + args.deadline_seconds if args.deadline_seconds else None
    result = run_experiment(args.experiment, args.contexts, args.output, model=args.model,
                            smoke=args.smoke, concurrency=args.concurrency, deadline=deadline)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in {"complete", "timeout"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""RQ3.1 registration and resumable execution boundary."""
from __future__ import annotations

import argparse
import hashlib
import math
import os
import pickle
import time
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from threading import Event
from typing import Any

from unified_scripts import stable_hash

from .gates import (
    HARD_CALL_LIMIT,
    audit_call_artifacts,
    audit_completion_artifacts,
    audit_method_lock,
    audit_registration,
    audit_research_config,
    audit_resume_identity,
)
from .utils import (
    ROOT,
    compact_status,
    exact_write,
    json_bytes,
    read_json,
    sha_file,
    verify_source_hashes,
)

SOLVER_SYSTEM = "You are an expert Site Reliability Engineer performing root cause analysis."
_ARM_IDS = frozenset(("T", "V", "TPV", "T_COMPACT", "P0_T_CAL", "P0_V_STANDARD",
                      "P0_V_CONTRAST", "X_T", "X_C", "X_C_TABLE", "X_C_TABLE_S", "X_S", "X_V_STANDARD",
                      "X_V_CONTRAST", "X_MTEXT", "SIRCL_TEXT"))

DEFAULT_CONFIG = ROOT / "RQs/RQ3_1/configs/data_split_v1.json"
DEFAULT_OUTPUT = ROOT / "RQs/RQ3_1/results/data_registration_v1"
RESEARCH_CONFIG = ROOT / "RQs/RQ3_1/configs/research_v2.json"
RESEARCH_OUTPUT = ROOT / "RQs/RQ3_1/results/team_stage2_direct_text_contrast"
RQ_LEDGER = ROOT / "RQs/RQ3_1/results/team_stage1/rq31_call_ledger.sqlite"
STOP_REQUESTED = Event()

# SIRCL's native MET-Z comparator has no output-row bound.  Text payloads at
# or below the high watermark are left byte-for-byte unchanged.  Larger
# payloads are reduced to the qualified low watermark by removing complete,
# lowest-deviation MET-Z rows while retaining every section, candidate, task
# instruction, topology row, and at least one metric row per entity.  The two
# watermarks were checked with both registered local processors; the lower one
# leaves room below the shared 40,960 - 8,192 input ceiling.
_SIRCL_CAPACITY_TRIGGER_CHARS = 49_500
_SIRCL_CAPACITY_TARGET_CHARS = 48_000


def _smoke_scope(config: Mapping[str, Any], experiment: str) -> str:
    """Version smoke accounting so a changed implementation cannot reuse old calls."""
    return f"smoke:{config['registration_id']}:{experiment}"


def materialize(config_path: Path = DEFAULT_CONFIG, output: Path = DEFAULT_OUTPUT, *, check: bool = False):
    """Register or byte-check the CPU-only data split (legacy entry point)."""
    from .exps import build_registration
    config = read_json(config_path)
    before = verify_source_hashes(config)
    bundle = build_registration(config)
    audit = audit_registration(bundle, config)
    provenance = {
        "schema_version": "RQ31DataRegistrationProvenanceV1",
        "source_hashes_before": before,
        "source_hashes_after": verify_source_hashes(config),
        "shared_grouping": {"module": "src/unified_scripts/dataset_segmentation.py",
                            "functions": ["connected_row_groups", "allocate_intact_groups"],
                            "adapter": "allocator validation bucket renamed test; no alternate grouping algorithm"},
        "aegislab_source_proof": (
            "AegisLabLoader indexes one datapack/case_dir and loads six telemetry files from it. "
            "Registration verifies those physical file identities are unique, but groups repeated env collection "
            "envelopes (namespace plus normal/abnormal bounds) as one source and also joins equal injection_id aliases; "
            "it neither assumes unique case_dir means independent nor uses one corpus-wide source."),
        "privacy": ("only six allowlisted source/window members were decoded from Aegis source_metadata; "
                    "labels, ground-truth-derived metadata, and all other values were lexically skipped"),
        "audit": audit,
    }
    artifacts = {output / "registration.json": bundle["public"], output / "summary.json": bundle["summary"],
                 output / "private/split.json": bundle["private"], output / "private/provenance.json": provenance}
    if check:
        changed = [str(path.relative_to(ROOT)) for path, value in artifacts.items()
                   if not path.is_file() or path.read_bytes() != json_bytes(value)]
        if changed:
            raise ValueError(f"registration check differs or is incomplete: {changed}")
    else:
        for path, value in artifacts.items():
            exact_write(path, value)
    if before != verify_source_hashes(config):
        raise ValueError("protected sources changed during registration")
    return {**audit, "mode": "check" if check else "register",
            "artifacts": [str(path.relative_to(ROOT)) for path in artifacts]}


def _eval_rows(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Read only evaluator metadata; prospective test rows are never opened."""
    return _partition_rows(config, "eval")


def _partition_rows(config: Mapping[str, Any], partition: str) -> list[dict[str, Any]]:
    """Read public identities for one registered partition only."""
    split = read_json(ROOT / str(config["data"]["registration"]))
    rows = [dict(row) for row in split.get("partitions", {}).get(partition, [])]
    expected = int(config["data"]["eval_cases"] if partition == "eval" else config["data"]["test_cases"])
    if len(rows) != expected:
        raise ValueError(f"research registration does not contain the registered {partition} population")
    identities = [(row.get("dataset"), row.get("opaque_incident_id")) for row in rows]
    if any(not dataset or not opaque for dataset, opaque in identities) or len(set(identities)) != len(identities):
        raise ValueError(f"registered {partition} identities are incomplete or duplicated")
    return rows


def smoke_roster(config: Mapping[str, Any], rows: Iterable[Mapping[str, Any]] | None = None) -> list[dict[str, str]]:
    """Select one case per smoke dataset from eval by seed/hash."""
    rows = list(rows if rows is not None else _eval_rows(config))
    selected = []
    for dataset in tuple(config["smoke"]["datasets"]):
        pool = [r for r in rows if r.get("dataset") == dataset]
        if not pool:
            raise ValueError(f"smoke dataset is absent from eval: {dataset}")
        row = min(pool, key=lambda r: stable_hash([config["seed"], dataset, r["opaque_incident_id"]]))
        opaque = str(row["opaque_incident_id"])
        selected.append({"dataset": str(dataset), "opaque_incident_id": opaque,
                        # Public registration intentionally has no private case
                        # path/telemetry fields; opaque ID is sufficient for a
                        # call identity and is never sent as evidence.
                        "case_id": str(row.get("case_id", opaque))})
    return selected


def build_research_registration(config: Mapping[str, Any]) -> dict[str, Any]:
    """Build an immutable, model-free registration from the current eval pool."""
    audit = audit_research_config(dict(config))
    rows = _eval_rows(config)
    payload = {"schema_version": "RQ31ResearchExecutionRegistrationV2",
               "registration_id": config["registration_id"],
               "status": "registered_cpu_only_model_execution_not_started",
               "config_hash": stable_hash(config), "data_registration": config["data"]["registration"],
               "eval_cases": len(rows), "models_in_order": list(config["models"]["order"]),
               "arm_ids": [row["id"] for row in config["arms"]],
               "logical_experiments": [dict(row) for row in config["logical_experiments"]],
               "experiments": [{"id": row["id"], "calls": row["calls"]} for row in config["experiments"]],
               "smoke": {"source_partition": "eval", "cases": smoke_roster(config, rows),
                         "max_calls": config["smoke"]["max_calls"], "max_seconds": config["smoke"]["max_seconds"],
                         "model_order": list(config["smoke"]["model_order"])},
               "selector": dict(config["selector"]),
               "budget": dict(config["budget"]), "selection_rule": dict(config["selection_rule"]), "audit": audit}
    payload["registration_hash"] = stable_hash(payload)
    return payload


def register_research(config_path: Path = RESEARCH_CONFIG, output: Path = RESEARCH_OUTPUT, *, check: bool = False):
    config = read_json(config_path)
    registration = build_research_registration(config)
    target = Path(output) / "research_registration_v2.json"
    if check:
        if not target.is_file() or target.read_bytes() != json_bytes(registration):
            raise ValueError(f"research registration differs or is incomplete: {target}")
    else:
        exact_write(target, registration)
    display_path = str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else str(target)
    return {"status": "passed", "mode": "check" if check else "register",
            "path": display_path, "registration_hash": registration["registration_hash"],
            "model_calls_started": False}


def _dimension_rows(config: Mapping[str, Any], experiment: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    exp = next((dict(row) for row in config["experiments"] if row["id"] == experiment), None)
    if exp is None:
        raise ValueError(f"unregistered RQ3.1 experiment: {experiment}")
    if experiment == "exp_contrastive_rca_effectiveness":
        dimensions = [{"arm": arm["id"]} for arm in config["arms"]]
    elif experiment == "exp_visual_diagnostic_mechanisms":
        dimensions = [{"condition": row["id"], "representation": rep}
                      for row in config["mechanisms"] for rep in row["representations"]]
    elif experiment == "exp_replicate_stability":
        dimensions = [{"condition": condition, "replicate": replicate}
                      for condition in ("X_C", "X_V_STANDARD", "X_V_CONTRAST") for replicate in (1, 2)]
    elif experiment == "exp_transfer_and_diagnostic_robustness":
        dimensions = [{"transform": transform, "representation": representation}
                      for transform in ("REANONYMIZE", "CANDIDATE_REORDER")
                      for representation in ("X_C", "X_V_CONTRAST")]
    elif experiment == "exp_budget_curve":
        dimensions = [{"budget": budget, "representation": representation}
                      for budget in (0.5, 0.75)
                      for representation in ("X_C", "X_C_TABLE", "X_V_CONTRAST")]
    elif experiment == "exp_redundant_load":
        dimensions = [{"load": load, "representation": representation}
                      for load in (0.25, 0.5)
                      for representation in ("X_C", "X_C_TABLE", "X_V_CONTRAST")]
    elif experiment == "exp_table_screenshot":
        dimensions = [{"representation": "X_C_TABLE_S"}]
    else:
        dimensions = [{"method": method} for method in config["final_methods"]]
    return exp, dimensions


def build_call_key(experiment: str, model: str, case: Mapping[str, Any], dimensions: Mapping[str, Any], *,
                   actual_request: Any | None = None, projection_hash: str | None = None,
                   adapter_version: str = "rq31_solver_request_v1", replicate: Any = 0,
                   version: str = "rq31_research_v1") -> str:
    """Stable identity bound to request, projection, adapter and replicate."""
    request_digest = (actual_request if isinstance(actual_request, str) and len(actual_request) == 64
                      else stable_hash(actual_request if actual_request is not None else dict(sorted(dimensions.items()))))
    identity = {"experiment": experiment, "model": model,
                "case": str(case.get("opaque_incident_id", case.get("case_id"))),
                "dimensions": dict(sorted(dimensions.items())),
                "actual_request_digest": request_digest,
                "projection_hash": projection_hash or "unbound",
                "adapter_version": adapter_version, "replicate": replicate, "registration_version": version}
    return stable_hash(identity)


def bind_task_request(task: Mapping[str, Any], actual_request: Any, projection_hash: str, *,
                      projection: Any | None = None,
                      adapter_version: str = "rq31_solver_request_v1", version: str = "rq31_research_v1") -> dict[str, Any]:
    """Bind a registered logical task to the exact public request/projection."""
    if not projection_hash or len(str(projection_hash)) != 64 or any(c not in "0123456789abcdef" for c in str(projection_hash)):
        raise ValueError("actual representation projection hash is required")
    if projection is not None and stable_hash(projection) != str(projection_hash):
        raise ValueError("representation projection hash does not match the actual projection")
    bound = dict(task)
    bound["request_hash"] = stable_hash(actual_request)
    bound["projection_hash"] = str(projection_hash)
    bound["adapter_version"] = adapter_version
    bound["registration_version"] = version
    bound["replicate"] = task.get("dimensions", {}).get("replicate", 0)
    bound["call_key"] = build_call_key(task["experiment"], task["model"], task["case"], task["dimensions"],
                                        actual_request=bound["request_hash"], projection_hash=projection_hash,
                                        adapter_version=adapter_version, replicate=bound["replicate"], version=version)
    bound["bound"] = True
    return bound


def audit_actual_request(task: Mapping[str, Any], request: Mapping[str, Any]) -> None:
    """Check that an injected A/B request is the request this task names."""
    for field in ("parts", "envelope", "actual_request", "projection_hash"):
        if field not in request:
            raise ValueError(f"actual request is missing {field}")
    actual = request["actual_request"]
    if not isinstance(actual, Mapping):
        raise TypeError("actual_request must be a mapping")
    if str(actual.get("model")) != str(task.get("model")):
        raise ValueError("actual request model does not match registered task")
    actual_dimensions = dict(request.get("dimensions") or {})
    if actual_dimensions != dict(task.get("dimensions") or {}):
        raise ValueError("actual request dimensions do not match registered task")
    envelope = request["envelope"]
    if not isinstance(envelope, Mapping):
        raise TypeError("request envelope must be a mapping")
    effective = envelope.get("effective_server")
    if not isinstance(effective, Mapping):
        raise TypeError("request envelope lacks effective server attestation")
    from unified_scripts.vllm_inference import VLLMInferenceConfig
    runtime_config = VLLMInferenceConfig.load()
    runtime = runtime_config.model(str(task["model"]))
    if str(effective.get("served_model_name")) != str(runtime.get("served_model_name")):
        raise ValueError("request is bound to the wrong served model")
    if int(effective.get("max_model_len", -1)) != int(runtime["max_model_len"]):
        raise ValueError("request is bound to the wrong effective context length")
    if str(effective.get("config_hash")) != stable_hash(runtime_config.data):
        raise ValueError("request lacks the current effective vLLM config hash")
    visible = [{"type": p["type"], "text": p.get("text")} if p["type"] == "text" else
               {"type": "image", "sha256": hashlib.sha256(p["png"]).hexdigest()} for p in request["parts"]]
    if (actual.get("parts") != visible or actual.get("system") != envelope.get("system") or
            actual.get("schema") != envelope.get("schema") or actual.get("effective_server") != effective):
        raise ValueError("request digest does not describe the actual submitted payload")


def expand_call_tasks(config: Mapping[str, Any], experiment: str, cases: Iterable[Mapping[str, Any]], *, allow_test: bool = False,
                      method_lock: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Expand a registered matrix and prove that every logical key is unique."""
    exp, dimensions = _dimension_rows(config, experiment)
    case_rows = list(cases)
    if exp["population"] == "test" and not allow_test:
        raise ValueError("test task expansion is disabled until methods are frozen")
    if exp["population"] == "test":
        if method_lock is None:
            raise ValueError("final test requires a frozen method lock")
        audit_method_lock(dict(method_lock), dict(config))
    if len(case_rows) != int(exp["cases"]):
        raise ValueError(f"{experiment} requires exactly {exp['cases']} registered cases")
    partition = "test" if exp["population"] == "test" else "eval"
    registered = {(str(row["dataset"]), str(row["opaque_incident_id"])) for row in _partition_rows(config, partition)}
    provided = [(str(row.get("dataset", "")), str(row.get("opaque_incident_id", ""))) for row in case_rows]
    if any(not dataset or not opaque for dataset, opaque in provided) or len(set(provided)) != len(provided):
        raise ValueError("task matrix contains incomplete or duplicate case identities")
    if experiment == "exp_contrastive_rca_effectiveness" and set(provided) != registered:
        raise ValueError("effectiveness matrix must cover the complete registered eval population")
    if not set(provided) <= registered:
        raise ValueError("task matrix contains a case outside its registered partition")
    if exp["population"] == "eval_mechanism_subset" and set(provided) != {
        (row["dataset"], row["opaque_incident_id"]) for row in experiment_roster(config, experiment)
    }:
        raise ValueError("mechanism tasks must use the frozen balanced hash subset")
    tasks = []
    for model in config["models"]["order"]:
        for case in sorted(case_rows, key=lambda r: str(r.get("opaque_incident_id", r.get("case_id")))):
            for dimension in dimensions:
                tasks.append({"experiment": experiment, "model": model, "case": dict(case), "dimensions": dimension,
                              "call_key": build_call_key(experiment, model, case, dimension,
                                                          adapter_version=config["request_adapter"]["version"]),
                              "adapter_version": config["request_adapter"]["version"], "bound": False,
                              "max_new_calls": 1})
    if len(tasks) != int(exp["calls"]):
        raise ValueError(f"expanded task count differs from registration: {len(tasks)} != {exp['calls']}")
    if len({task["call_key"] for task in tasks}) != len(tasks):
        raise ValueError("duplicate logical call key in registered matrix")
    return tasks


def select_main_method(rows: Iterable[Mapping[str, Any]], *, config: Mapping[str, Any] | None = None) -> str:
    """Apply the preregistered Qwen five-dataset macro/tie rule only."""
    cfg = config or read_json(RESEARCH_CONFIG)
    rule = cfg["selection_rule"]
    candidates = tuple(rule["candidates"])
    datasets = ("aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt")
    grouped = {m: {d: [] for d in datasets} for m in candidates}
    expected_ids = {(str(row["dataset"]), str(row["opaque_incident_id"])) for row in _eval_rows(cfg)}
    for row in rows:
        if row.get("model") == rule["score_model"] and row.get("method") in candidates and row.get("dataset") in datasets:
            grouped[str(row["method"])][str(row["dataset"])].append(row)
    stats = {}
    for method in candidates:
        identities = [(str(row.get("dataset", "")), str(row.get("opaque_incident_id", row.get("case_id", ""))))
                      for dataset in datasets for row in grouped[method][dataset]]
        if set(identities) != expected_ids or len(identities) != len(set(identities)):
            raise ValueError(f"selection rows incomplete for {method}")
        if any(any(row.get(field) is None or not isinstance(row.get(field), (int, float)) or
                   not math.isfinite(float(row.get(field)))
                   for field in ("input_tokens", "output_tokens", "baseline_input_tokens", "baseline_output_tokens"))
               for dataset in datasets for row in grouped[method][dataset]):
            raise ValueError(f"selection costs incomplete for {method}")
        per_dataset = {d: sum(float(r["mrr"]) for r in grouped[method][d]) / len(grouped[method][d]) for d in datasets}
        ratios = []
        for dataset in datasets:
            own = grouped[method][dataset]
            cost = sum(float(r["input_tokens"]) + float(r["output_tokens"]) for r in own) / len(own)
            base = sum(float(r["baseline_input_tokens"]) + float(r["baseline_output_tokens"]) for r in own) / len(own)
            if base <= 0:
                raise ValueError(f"non-positive T baseline cost for {method}/{dataset}")
            ratios.append(cost / base)
        stats[method] = {"macro": sum(per_dataset.values()) / len(datasets),
                         "aiops_min": min(per_dataset["aiops2022"], per_dataset["aiops2025"]),
                         "relative_cost": sum(ratios) / len(ratios)}
    best = max(v["macro"] for v in stats.values())
    tied = [m for m in candidates if best - stats[m]["macro"] <= float(rule["tie_tolerance"])]
    return min(tied, key=lambda m: (-stats[m]["aiops_min"], stats[m]["relative_cost"], m))


def _read_eval_inventory(inventory: Path | Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], Path]:
    """Read a persisted, complete eval summary; never accept caller-made rows."""
    if not isinstance(inventory, (str, Path)):
        raise TypeError("method freezing requires a persisted eval inventory path")
    path = Path(inventory)
    if path.is_dir():
        path = path / "summary.json"
    if not path.is_file():
        raise ValueError("eval inventory summary is missing")
    payload = read_json(path)
    rows = payload.get("records") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list) or payload.get("status") != "complete":
        raise ValueError("eval inventory must be a complete persisted summary")
    return [dict(row) for row in rows], path.parent


def _normalise_eval_inventory(rows: Iterable[Mapping[str, Any]], cfg: Mapping[str, Any], root: Path) -> list[dict[str, Any]]:
    """Verify complete Qwen candidate/T cohort and derive an immutable ledger snapshot."""
    registration = read_json(ROOT / str(cfg["data"]["registration"]))
    expected_ids = {(str(row["dataset"]), str(row["opaque_incident_id"]))
                    for row in registration["partitions"]["eval"]}
    candidates = tuple(cfg["selection_rule"]["candidates"])
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("model")) != str(cfg["selection_rule"]["score_model"]):
            continue
        dimensions = row.get("dimensions") or {}
        method = row.get("method") or dimensions.get("method") or dimensions.get("arm")
        if method not in (*candidates, "T"):
            continue
        metrics = row.get("metrics") or row.get("score") or {}
        mrr = row.get("mrr", metrics.get("mrr"))
        case = (str(row.get("dataset", "")), str(row.get("opaque_incident_id", "")))
        if case not in expected_ids or not isinstance(mrr, (int, float)) or not math.isfinite(float(mrr)):
            raise ValueError("eval inventory contains an invalid case or MRR")
        input_tokens, output_tokens = row.get("input_tokens"), row.get("output_tokens")
        if not all(isinstance(value, (int, float)) and math.isfinite(float(value))
                   for value in (input_tokens, output_tokens)):
            raise ValueError("eval inventory lacks actual token accounting")
        call_key = str(row.get("call_key", ""))
        if not call_key or Path(call_key).name != call_key:
            raise ValueError("eval inventory lacks a safe persisted call key")
        # A summary row is accepted only when its completion surface exists
        # beside the summary. This prevents an in-memory/fabricated inventory.
        if row.get("status") == "design_infeasible":
            terminal = read_json(root / "interventions" / f"{call_key}.json")
            if (terminal.get("status") != "design_infeasible" or terminal.get("model") != row["model"] or
                    terminal.get("case", {}).get("opaque_incident_id") != case[1] or
                    terminal.get("dimensions") != dimensions or any((mrr, input_tokens, output_tokens))):
                raise ValueError("design-failure summary lacks its terminal source")
        else:
            audit_completion_artifacts(root, call_key)
            committed = read_json(root / "outputs" / f"{call_key}.json")
            cost = read_json(root / "cost" / f"{call_key}.json")
            actual_metrics = committed["score"].get("metrics", committed["score"])
            if (committed.get("opaque_incident_id") != case[1] or committed.get("dataset") != case[0]
                    or committed.get("model") != row["model"] or actual_metrics.get("mrr") != mrr
                    or committed.get("dimensions") != dimensions or cost.get("input_tokens") != input_tokens
                    or cost.get("output_tokens") != output_tokens):
                raise ValueError("summary row differs from its committed result")
        normalized.append({"method": str(method), "model": str(row["model"]),
                           "dataset": case[0], "opaque_incident_id": case[1], "mrr": float(mrr),
                           "input_tokens": float(input_tokens), "output_tokens": float(output_tokens),
                           "baseline_input_tokens": float(input_tokens),
                           "baseline_output_tokens": float(output_tokens), "call_key": call_key})
    by_method = {method: [row for row in normalized if row["method"] == method] for method in (*candidates, "T")}
    for method, method_rows in by_method.items():
        identities = {(row["dataset"], row["opaque_incident_id"]) for row in method_rows}
        if identities != expected_ids or len(method_rows) != len(expected_ids):
            raise ValueError(f"eval inventory cohort is incomplete for {method}")
    # Replace each candidate's baseline cost with the paired T row for the
    # same case before applying the registered selection rule.
    baseline = {(row["dataset"], row["opaque_incident_id"]): row for row in by_method["T"]}
    for row in normalized:
        if row["method"] != "T":
            base = baseline[(row["dataset"], row["opaque_incident_id"])]
            row["baseline_input_tokens"] = base["input_tokens"]
            row["baseline_output_tokens"] = base["output_tokens"]
    return normalized


def freeze_main_method(eval_inventory: Path | Iterable[Mapping[str, Any]], output: Path = RESEARCH_OUTPUT, *,
                       method: str | None = None, eval_registration_hash: str | None = None,
                       code_hash: str | None = None, prompt_hash: str | None = None,
                       config_hash: str | None = None, roster_hash: str | None = None,
                       results_hash: str | None = None, ledger_hash: str | None = None) -> dict[str, Any]:
    """Freeze the recomputed eval champion and immutable source snapshot."""
    cfg = read_json(RESEARCH_CONFIG)
    audit_research_config(cfg)
    rows, inventory_root = _read_eval_inventory(eval_inventory)
    normalized = _normalise_eval_inventory(rows, cfg, inventory_root)
    selected = select_main_method(normalized, config=cfg)
    if method is not None and str(method) != selected:
        raise ValueError("caller method disagrees with recomputed eval champion")
    registration = read_json(ROOT / str(cfg["data"]["registration"]))
    registration_hash = str(registration.get("registration_hash", ""))
    if eval_registration_hash is not None and str(eval_registration_hash) != registration_hash:
        raise ValueError("caller registration hash disagrees with frozen eval registration")
    output = Path(output); lock_path = output / "method_lock.json"
    if lock_path.exists():
        raise ValueError("method lock already exists and is immutable")
    from .utils import implementation_hash
    actual_code_hash = implementation_hash()
    from RQs.RQ3_1.src.utils import rq31_solver_read_guide, rq31_solver_system_prompt
    actual_prompt_hash = stable_hash({"system": rq31_solver_system_prompt(),
                                      "guides": {arm: rq31_solver_read_guide(arm) for arm in sorted(_ARM_IDS)}})
    actual_config_hash = stable_hash(cfg)
    actual_roster_hash = stable_hash(registration)
    actual_results_hash = stable_hash(normalized)
    actual_ledger_hash = stable_hash({"scope": "eval_subset", "records": [
        {"call_key": row["call_key"], "case": [row["dataset"], row["opaque_incident_id"]],
         "method": row["method"]} for row in normalized]})
    supplied = (("code_hash", code_hash, actual_code_hash), ("prompt_hash", prompt_hash, actual_prompt_hash),
                ("config_hash", config_hash, actual_config_hash), ("roster_hash", roster_hash, actual_roster_hash),
                ("results_hash", results_hash, actual_results_hash), ("ledger_hash", ledger_hash, actual_ledger_hash))
    for name, claimed, actual in supplied:
        if claimed is not None and str(claimed) != actual:
            raise ValueError(f"caller {name} disagrees with recomputed source digest")
    # Any final-test ledger row or committed final-test output means the
    # pre-test freeze window has passed, even if a caller supplies false bools.
    import sqlite3
    if Path(RQ_LEDGER).is_file():
        with sqlite3.connect(RQ_LEDGER) as db:
            if db.execute("SELECT 1 FROM calls WHERE call_key LIKE 'exp_final_test/%' LIMIT 1").fetchone():
                raise ValueError("cannot freeze after final-test ledger activity")
            ledger_high_water = int(db.execute("SELECT COALESCE(MAX(id), 0) FROM calls").fetchone()[0])
    else:
        ledger_high_water = 0
    test_root = output / "exp_final_test"
    if test_root.is_dir() and any(test_root.rglob("*.json")):
        raise ValueError("cannot freeze after final-test artifacts exist")
    lock = {"schema_version": "RQ31MethodLockV1", "method": selected,
            "model": cfg["selection_rule"]["score_model"], "eval_registration_hash": registration_hash,
            "code_hash": actual_code_hash, "prompt_hash": actual_prompt_hash,
            "config_hash": actual_config_hash, "roster_hash": actual_roster_hash,
            "results_hash": actual_results_hash, "ledger_hash": actual_ledger_hash,
            "eval_inventory": str(Path(eval_inventory).resolve()),
            "eval_inventory_sha256": sha_file(Path(eval_inventory) if Path(eval_inventory).is_file()
                                               else Path(eval_inventory) / "summary.json"),
            "output_root": str(output.resolve()),
            "ledger_high_water": ledger_high_water,
            "test_outcomes_present": False, "frozen_before_test": True}
    lock["lock_hash"] = stable_hash(lock)
    exact_write(lock_path, lock)
    return lock


def score_bound_response(response: str, candidates: Iterable[str], numeric_to_natural: Mapping[str, str],
                         accepted: Iterable[str]) -> dict[str, Any]:
    """Use the project granularity-aware scorer for evaluator-private labels."""
    from RQs.RQ2.src.exps import rca_schema
    from unified_scripts.rca_scorer import RCAScorer, RCAScorerConfig
    from unified_scripts.rca_scorer import score_bound_response as _score
    schema = rca_schema()["json_schema"]["schema"]
    scorer = RCAScorer(RCAScorerConfig.load())
    return _score(response, list(candidates), dict(numeric_to_natural), list(accepted), schema, scorer)




def _request_envelope(model: str, *, system: str | None = None) -> dict[str, Any]:
    """Return the one-call Solver envelope shared by every RQ3.1 arm."""
    from RQs.RQ2.src.exps import rca_schema
    from RQs.RQ3_1.src.utils import rq31_solver_system_prompt
    from unified_scripts.vllm_inference import VLLMInferenceConfig

    cfg = read_json(RESEARCH_CONFIG)
    runtime_config = VLLMInferenceConfig.load()
    runtime = runtime_config.model(model)
    return {
        "system": system or rq31_solver_system_prompt(),
        "schema": rca_schema(),
        "policy_version": cfg["request_adapter"]["version"],
        "effective_server": {"max_model_len": int(runtime["max_model_len"]),
                             "max_tokens": cfg["request_adapter"]["max_tokens"],
                             "served_model_name": runtime["served_model_name"],
                             "gpu_memory_utilization": runtime.get("gpu_memory_utilization"),
                             "dtype": runtime.get("dtype"),
                             "quantization": runtime.get("quantization"),
                             # Record the deployment profile that was actually loaded.
                             # DEFAULT_PATH names the historical/Nibi profile even when
                             # CANVASRCA_VLLM_CONFIG selects the local WSL profile.
                             "config_source": str(runtime_config.source),
                             "config_hash": stable_hash(runtime_config.data)},
    }


def _parts_from_twin(arm: str, twin: Any) -> list[dict[str, Any]]:
    """Map a compiled B twin to one registered arm using the parent RCA shell."""
    from RQs.RQ3_1.src.utils import rq31_solver_read_guide
    from vlmrca.vlm.client import image_part, text_part

    twin.validate()
    parts: list[dict[str, Any]] = [text_part(rq31_solver_read_guide(arm))]
    if arm in {"X_T", "P0_T_CAL"}:
        parts.extend([text_part(twin.natural_text), text_part(twin.candidate_text)])
    elif arm == "X_C":
        parts.extend([text_part(twin.compact_compare_text), text_part(twin.candidate_text)])
    elif arm == "X_C_TABLE":
        parts.extend([text_part(twin.direct_compare_table_text), text_part(twin.candidate_text)])
    elif arm == "X_S":
        parts.append(image_part(twin.require_image("screenshot")))
        parts.append(text_part(twin.candidate_text))
    elif arm == "X_C_TABLE_S":
        parts.append(image_part(twin.require_image("direct_compare_table_screenshot")))
        parts.append(text_part(twin.candidate_text))
    elif arm in {"X_V_STANDARD", "P0_V_STANDARD"}:
        parts.append(image_part(twin.require_image("standard")))
        parts.append(text_part(twin.candidate_text))
    elif arm in {"X_V_CONTRAST", "P0_V_CONTRAST"}:
        parts.append(image_part(twin.require_image("contrast")))
        parts.append(text_part(twin.candidate_text))
    elif arm == "X_MTEXT":
        parts.append(text_part(twin.mtext_text))
        mtext_status = (twin.manifests.get("carrier_status", {}).get("mtext", {})
                        if isinstance(twin.manifests, Mapping) else {})
        if mtext_status.get("status") == "unavailable":
            # Preserve B's typed capacity error for a requested unavailable
            # carrier; silently dropping it would alter the registered X arm.
            parts.append(image_part(twin.require_image("mtext")))
        elif mtext_status.get("status") == "available" and twin.mtext_png is not None:
            parts.append(image_part(twin.require_image("mtext")))
        parts.append(text_part(twin.candidate_text))
    else:
        raise ValueError(f"twin does not provide registered arm {arm}")
    parts.append(text_part("Based on the above, identify the root cause."))
    return parts


def _bound_sircl_text(text: str) -> tuple[str, dict[str, Any] | None]:
    """Bound only an over-cap native SIRCL payload at whole evidence rows."""
    if len(text) <= _SIRCL_CAPACITY_TRIGGER_CHARS:
        return text, None
    lines = text.splitlines()
    metric_title = "=== Per-service metrics: 3σ-fluctuating columns vs baseline (CSV) ==="
    trace_title = "=== Per-(service, operation) span anomaly scores ==="
    log_title = "=== Per-service error-keyword frequency-ratio score ==="
    topology_title = "=== SERVICE CALL GRAPH ==="
    try:
        metric_start = lines.index(metric_title)
        trace_start = lines.index(trace_title)
        log_start = lines.index(log_title)
        topology_start = lines.index(topology_title)
    except ValueError as exc:
        raise ValueError("over-cap SIRCL payload lacks a registered section boundary") from exc
    if not metric_start < trace_start < log_start < topology_start:
        raise ValueError("over-cap SIRCL payload has reordered evidence sections")

    # Native MET-Z emits services in stable order and each service's rows in
    # descending 3-sigma deviation. A row is the smallest independently
    # meaningful block. Preserve the first (strongest) row for every entity,
    # then remove deepest within-entity ranks first. This uses the native order
    # without inventing a new cross-entity score from rounded display values.
    removable: list[tuple[int, int]] = []
    group_starts = [index for index in range(metric_start + 1, trace_start)
                    if lines[index].startswith("--- ") and lines[index].endswith(" ---")]
    for position, start in enumerate(group_starts):
        stop = group_starts[position + 1] if position + 1 < len(group_starts) else trace_start
        header = next((index for index in range(start + 1, stop)
                       if lines[index] == "key,regular_mean,regular_std_dev,current_mean,current_std_dev"), None)
        if header is None:
            continue
        rows: list[int] = []
        for index in range(header + 1, stop):
            value = lines[index].strip()
            if not value:
                continue
            fields = value.split(",")
            if len(fields) != 5:
                continue
            rows.append(index)
        if len(rows) > 1:
            removable.extend((rank, index) for rank, index in enumerate(rows[1:], start=2))

    removed: set[int] = set()
    current_chars = len(text)
    for _rank, index in sorted(removable, key=lambda row: (-row[0], row[1])):
        if current_chars <= _SIRCL_CAPACITY_TARGET_CHARS:
            break
        removed.add(index)
        current_chars -= len(lines[index]) + 1
    bounded = "\n".join(line for index, line in enumerate(lines) if index not in removed)
    if len(bounded) > _SIRCL_CAPACITY_TARGET_CHARS:
        raise ValueError("SIRCL MET-Z whole-row capacity reduction was insufficient")
    audit = {
        "schema_version": "RQ31SIRCLTextCapacityV1",
        "policy": "remove_deepest_native_rank_complete_MET_Z_rows_preserve_first_per_entity",
        "trigger_chars": _SIRCL_CAPACITY_TRIGGER_CHARS,
        "target_chars": _SIRCL_CAPACITY_TARGET_CHARS,
        "original_chars": len(text),
        "bounded_chars": len(bounded),
        "removed_metric_rows": len(removed),
        "original_text_hash": stable_hash(text),
        "bounded_text_hash": stable_hash(bounded),
    }
    return bounded, audit


def _parts_from_sircl(sircl: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Expose the source-adapted SIRCL comparator as its sole user payload."""
    from vlmrca.vlm.client import text_part

    payload = sircl.get("model_payload") if isinstance(sircl, Mapping) else None
    if not isinstance(payload, Mapping) or not isinstance(payload.get("text"), str):
        raise TypeError("SIRCL comparator is missing its source-adapted model payload")
    if payload.get("system_role") and not isinstance(payload.get("system_role"), str):
        raise TypeError("SIRCL comparator has an invalid system role")
    # The adapted MET-Z/TRC-L/LOG-R text is the complete user payload.  Do not
    # prefix it with the RQ3.1 guide or a P0 packet (that would be a different
    # comparator and would invalidate the registered arm).
    bounded, _audit = _bound_sircl_text(payload["text"])
    return [text_part(bounded)]


def _parts_from_prepared(arm: str, prepared: Any) -> list[dict[str, Any]]:
    """Use the frozen parent request builder for inherited controls."""
    from RQs.RQ1_1.src.exps import compact_evidence_text, direct_rca_parts
    if arm in {"T", "V", "TPV"}:
        # TPV is the inherited parent topology-visual arm. Do not silently
        # replace it with H (the hybrid control); this distinction is part of
        # the registered factorial topology.
        mapped = {"P0_T_CAL": "T", "P0_V_STANDARD": "V"}.get(arm, arm)
        return direct_rca_parts(mapped, prepared)
    if arm == "T_COMPACT":
        from RQs.RQ1_1.src.exps import (
            _common_shell,
            direct_rca_prompt,
            tagged_text_part,
        )
        packet = prepared.public["packet"]
        return [tagged_text_part(direct_rca_prompt(packet), "task_question"),
                tagged_text_part(compact_evidence_text(packet), "evidence_header"),
                tagged_text_part(_common_shell(packet), "common"),
                tagged_text_part("Based on the above, identify the root cause.", "task_question")]
    raise ValueError(f"prepared case does not provide registered arm {arm}")


def build_solver_request(task: Mapping[str, Any], *, twin: Any | None = None,
                         prepared: Any | None = None, sircl: Mapping[str, Any] | None = None,
                         projection: Any | None = None,
                         adapter_version: str | None = None) -> dict[str, Any]:
    """Build and bind one actual model-visible request for every registered arm."""
    arm = str(task.get("dimensions", {}).get(
        "arm", task.get("dimensions", {}).get("method",
        task.get("dimensions", {}).get("representation",
        task.get("dimensions", {}).get("condition", "")))))
    if arm not in _ARM_IDS:
        raise ValueError(f"unregistered RQ3.1 arm: {arm}")
    if arm == "SIRCL_TEXT":
        if sircl is None:
            raise RuntimeError("source-adapted SIRCL comparator is required; no packet fallback is allowed")
        parts = _parts_from_sircl(sircl)
        payload = sircl["model_payload"]
        envelope = _request_envelope(str(task["model"]), system=str(payload.get("system_role") or ""))
        projection = {"bridge": "rq31_sircl_text_adapter_v1",
                      "model_payload_hash": sircl.get("model_payload_hash"),
                      "adapter_hash": sircl.get("adapter_hash"),
                      "parts": [{"type": p.get("type"), "text": p.get("text")} for p in parts]}
        _bounded_text, capacity_audit = _bound_sircl_text(payload["text"])
        if capacity_audit is not None:
            projection["capacity_adapter"] = capacity_audit
    elif arm in {"P0_T_CAL", "P0_V_STANDARD", "P0_V_CONTRAST", "X_T", "X_C", "X_C_TABLE",
                 "X_C_TABLE_S", "X_S", "X_V_STANDARD", "X_V_CONTRAST", "X_MTEXT"}:
        if twin is None:
            raise RuntimeError("representation twin is pending; capacity/materialization must be supplied")
        parts = _parts_from_twin(arm, twin)
        twin_projection = twin.to_manifest()
        if projection is not None and stable_hash(projection) != stable_hash(twin_projection):
            raise ValueError("supplied projection does not match the compiled representation twin")
        projection = twin_projection
        envelope = _request_envelope(str(task["model"]))
    else:
        if prepared is None:
            raise RuntimeError(f"frozen prepared case is required for {arm}; no placeholder request is allowed")
        parts = _parts_from_prepared(arm, prepared)
        inherited_projection = {
            "bridge": "rq1_1_direct_rca_parts_v14", "arm": arm,
            "parts": [{"type": p.get("type"), "text": p.get("text"),
                       "png_sha256": hashlib.sha256(p["png"]).hexdigest() if p.get("type") == "image" else None}
                      for p in parts],
        }
        if projection is not None and stable_hash(projection) != stable_hash(inherited_projection):
            raise ValueError("supplied projection does not match inherited RQ1.1 request")
        projection = inherited_projection
        from RQs.RQ1_1.src.exps import RCA_SYSTEM_ROLE
        envelope = _request_envelope(str(task["model"]), system=RCA_SYSTEM_ROLE)
    if not parts or not any(p.get("type") in {"text", "image"} for p in parts):
        raise ValueError("request builder produced no model-visible parts")
    visible = [{"type": p["type"], "text": p.get("text")} if p["type"] == "text"
               else {"type": "image", "sha256": hashlib.sha256(p["png"]).hexdigest()}
               for p in parts]
    actual = {"schema_version": "RQ31ActualSolverRequestV1",
              "model": str(task["model"]), "system": envelope["system"],
              "parts": visible, "schema": envelope["schema"],
              "effective_server": envelope["effective_server"],
              "adapter_version": adapter_version or "rq31_solver_request_v1"}
    return {"parts": parts, "envelope": envelope, "actual_request": actual,
            "dimensions": dict(task.get("dimensions") or {}),
            "projection": projection, "projection_hash": stable_hash(projection),
            "adapter_version": adapter_version or "rq31_solver_request_v1",
            "registration_version": "rq31_research_v1"}


def reorder_candidate_ids(candidates: Iterable[str], opaque_incident_id: str) -> list[str]:
    """Apply the registered case-local candidate-order nuisance transform."""
    values = [str(value) for value in candidates]
    if not values or len(values) != len(set(values)):
        raise ValueError("candidate reorder requires a complete unique candidate list")
    if any(not value.isdigit() or len(value) not in {3, 4, 5} for value in values):
        raise ValueError("candidate reorder requires typed numeric candidate IDs")
    for salt in ("primary", "alternate", "final"):
        reordered = sorted(values, key=lambda value: stable_hash([
            "rq31_candidate_reorder_v1", salt, str(opaque_incident_id), value,
        ]))
        if len(values) == 1 or reordered != values:
            return reordered
    raise RuntimeError("candidate reorder could not produce a distinct complete permutation")




def build_mechanism_request(task: Mapping[str, Any], context: Mapping[str, Any], *,
                            semantic_budget: int | None,
                            max_payload_char_delta_fraction: float | None = None) -> dict[str, Any]:
    """Consume only an A/B-attested mechanism request; never approximate one."""
    raw_condition = str(task.get("dimensions", {}).get("condition", ""))
    condition, embedded_representation = (raw_condition.split(":", 1) + [""])[:2] if ":" in raw_condition else (raw_condition, "")
    representation = str(task.get("dimensions", {}).get("representation", "")) or embedded_representation
    if condition not in {"NO_CONTRAST_SELECTION", "NO_GROUPING", "NO_SHARED_TIME",
                         "REMOVE_TARGET_BUNDLE", "REMOVE_NON_TARGET_BUNDLE"}:
        raise ValueError(f"unregistered mechanism condition: {condition}")
    if representation not in {"X_C", "X_V_CONTRAST"}:
        raise ValueError("mechanism representation must be X_C or X_V_CONTRAST")
    from RQs.RQ3_1.src.utils import compile_representation_twin
    if condition == "NO_CONTRAST_SELECTION":
        if semantic_budget is None:
            raise RuntimeError("standard semantic budget remains pending A/B capacity resolution")
        pool, bundles = context.get("pool"), context.get("bundles")
        if pool is None or bundles is None:
            raise RuntimeError("A/B contrast pool and bundles are required for no-contrast selection")
        from RQs.RQ3_1.src.exps import (
            materialize_contrast_selection,
            select_contrast_bundles,
        )
        selection = select_contrast_bundles(
            pool, bundles, semantic_budget=int(semantic_budget),
            contrast_gain_enabled=False, pool_prevalidated=True,
            bundles_prevalidated=True,
        )
        visible = materialize_contrast_selection(pool, bundles, selection)
        twin = compile_representation_twin(
            visible, candidates=tuple(context.get("candidates") or ()),
            display_reference_schedule=context.get("display_reference_schedule") or (),
        )
        request = build_solver_request(task, twin=twin, projection=twin.to_manifest())
        request["ab_attested"] = True
        return request
    # These two renderer interventions are fully implemented by B.  The public
    # facts/bins remain byte-identical; only the registered rendering flags
    # change.  The selector and matched-removal implementations below are
    # supplied by A; no evaluator-side target/control guess is permitted.
    if condition in {"NO_GROUPING", "NO_SHARED_TIME"}:
        materialized = context.get("materialized")
        if not isinstance(materialized, Mapping):
            raise RuntimeError(f"A/B materialization is required for {condition}")
        from RQs.RQ3_1.src.exps import plan_representation_intervention
        from RQs.RQ3_1.src.utils import compile_representation_twin
        plan = plan_representation_intervention(materialized, condition)
        parameters = dict(plan["renderer_parameters"])
        twin = compile_representation_twin(
            materialized,
            candidates=tuple(context.get("candidates") or ()),
            renderer_parameters=parameters,
            display_reference_schedule=context.get("display_reference_schedule") or (),
        )
        request = build_solver_request(task, twin=twin, projection=twin.to_manifest())
        request["ab_attested"] = True
        return request
    if condition in {"REMOVE_TARGET_BUNDLE", "REMOVE_NON_TARGET_BUNDLE"}:
        materialized = context.get("materialized")
        private = context.get("private") or {}
        candidates = context.get("candidates")
        numeric_to_natural = private.get("numeric_to_natural")
        accepted = private.get("accepted_labels") or private.get("accepted")
        tolerance = context.get("max_payload_char_delta_fraction", max_payload_char_delta_fraction)
        if (not isinstance(materialized, Mapping) or not candidates or
                not isinstance(numeric_to_natural, Mapping) or not accepted):
            raise RuntimeError(f"A/B private pairing inputs are required for {condition}")
        if tolerance is None:
            raise RuntimeError("matched-removal payload tolerance remains pending protocol freeze")
        from RQs.RQ3_1.src.exps import (
            apply_matched_bundle_removal,
            plan_matched_bundle_removal,
        )
        plan = plan_matched_bundle_removal(
            materialized, candidates=tuple(map(str, candidates)),
            numeric_to_natural=numeric_to_natural, accepted_labels=tuple(map(str, accepted)),
            max_payload_char_delta_fraction=float(tolerance),
        )
        removal = "target" if condition == "REMOVE_TARGET_BUNDLE" else "non_target"
        applied = apply_matched_bundle_removal(materialized, plan, removal=removal)
        if applied.get("status") in {"not_applicable", "no_op_no_unique_root_associated_facts",
                                      "no_op_no_unique_facts"}:
            # This is a valid evaluator-side non-applicability result, not a
            # request. Callers persist this marker and skip model execution.
            return {"schema_version": "RQ31InterventionSkipV1", "status": "skipped",
                    "intervention_status": applied.get("status"), "condition": condition,
                    "plan_hash": plan.get("plan_hash"), "reason": applied.get("reason")}
        visible = applied.get("materialized")
        if not isinstance(visible, Mapping):
            raise RuntimeError(f"{condition} did not produce a materialized public view")
        twin = compile_representation_twin(
            visible, candidates=tuple(candidates),
            display_reference_schedule=context.get("display_reference_schedule") or (),
        )
        request = build_solver_request(task, twin=twin, projection=twin.to_manifest())
        request["ab_attested"] = True
        request["intervention_plan_hash"] = plan.get("plan_hash")
        return request
    raise AssertionError("registered mechanism dispatch is incomplete")


def score_response_callback(private: Mapping[str, Any], candidates: Iterable[str]) -> Callable[[str], Mapping[str, Any]]:
    """Bind canonical granularity-aware scoring to evaluator-private labels."""
    numeric_to_natural = private.get("numeric_to_natural") or {}
    accepted = private.get("accepted_labels") or private.get("accepted")
    if not isinstance(numeric_to_natural, Mapping) or not accepted:
        raise ValueError("private evaluator binding requires numeric_to_natural and accepted_labels")
    candidate_values = [str(value) for value in candidates]
    def score(response: str) -> Mapping[str, Any]:
        return score_bound_response(response, candidate_values, numeric_to_natural, accepted)
    return score


def aggregate_result_summary(output: Path, expected_keys: Iterable[str], *, experiment: str,
                             model: str | None = None) -> dict[str, Any]:
    """Reconstruct a summary from atomically committed per-call artifacts."""
    expected = set(map(str, expected_keys)); rows: list[dict[str, Any]] = []; missing: list[str] = []
    for key in sorted(expected):
        # ``completed/<key>.json`` is the transaction commit boundary. Resume
        # deliberately trusts its atomic presence; re-hashing every prompt,
        # render, conversation and response made a restart spend hours on CPU
        # while an already loaded VLM sat idle. New calls are still audited at
        # commit time by ``run_registered_call``.
        if not (Path(output) / "completed" / f"{key}.json").is_file():
            missing.append(key); continue
        try:
            result = read_json(Path(output) / "outputs" / f"{key}.json")
            cost = read_json(Path(output) / "cost" / f"{key}.json")
        except (OSError, ValueError, TypeError):
            missing.append(key); continue
        score = result.get("score") or {}; metrics = score.get("metrics") or score
        row = {"call_key": key, "model": result.get("model", model), "dataset": result.get("dataset"),
               "opaque_incident_id": result.get("opaque_incident_id"),
               "fault_type": result.get("fault_type", "unavailable"), "dimensions": result.get("dimensions", {}),
               "status": result.get("status"),
               "score_status": score.get("status"), "error": score.get("error"),
               "input_tokens": cost.get("input_tokens"), "output_tokens": cost.get("output_tokens"),
               "total_tokens": cost.get("total_tokens"), "wall_time_s": cost.get("wall_time_s"),
               "metrics": {name: metrics.get(name) for name in
                           ("ac@1", "ac@3", "ac@5", "avg@3", "avg@5", "mrr")}}
        rows.append(row)
    numeric_names = ("input_tokens", "output_tokens", "total_tokens", "wall_time_s", "mrr",
                     "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")
    values = {name: [] for name in numeric_names}
    for row in rows:
        for name in numeric_names:
            value = row["metrics"].get(name) if name in row["metrics"] else row.get(name)
            if isinstance(value, (int, float)):
                values[name].append(float(value))
    averages = {f"avg_{name}": (sum(items) / len(items) if items else None) for name, items in values.items()}
    def grouped(field: str) -> dict[str, Any]:
        groups: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            value = row.get(field) or "unavailable"
            metric = row["metrics"].get("mrr")
            if isinstance(metric, (int, float)):
                groups[str(value)].append(float(metric))
        return {key: sum(items) / len(items) for key, items in sorted(groups.items()) if items}
    errors = sum(row.get("status") not in {"complete", "model_failure", "cpu_simulated"} or
                 row.get("score_status") not in {"complete", "model_failure"} for row in rows)
    summary = {"schema_version": "RQ31ResultSummaryV1", "experiment": experiment, "model": model,
               "status": "complete" if not missing and len(rows) == len(expected) else "incomplete",
               "expected_records": len(expected), "records": rows, "missing_call_keys": missing,
               "error_records": errors, "error_rate": errors / len(rows) if rows else None,
               "averages": averages, "per_dataset": grouped("dataset"), "per_fault_type": grouped("fault_type"),
               "cost_accounting": {"input_tokens": sum(values["input_tokens"]),
               "output_tokens": sum(values["output_tokens"]), "total_tokens": sum(values["total_tokens"])},
               "artifact_hash": stable_hash(rows)}
    from vlmrca.run_state import write_json
    write_json(Path(output) / "summary.json", summary)
    return summary


def _resume_inventory_path(output: Path, model: str) -> Path:
    return Path(output) / f"logical_inventory.{model}.json"


def _read_resume_inventory(output: Path, experiment: str, model: str, registered_tasks: int):
    """Read bookkeeping only; never hash or reopen committed response artifacts."""
    path = _resume_inventory_path(output, model)
    if not path.is_file():
        return {}, []
    payload = read_json(path)
    if (payload.get("schema_version") != "RQ31LogicalInventoryV1" or
            payload.get("experiment") != experiment or payload.get("model") != model or
            int(payload.get("registered_tasks", -1)) != int(registered_tasks)):
        raise ValueError("resume inventory identity does not match the registered model phase")
    units = payload.get("units") or {}
    noncalls = payload.get("noncalls") or []
    if not isinstance(units, Mapping) or not isinstance(noncalls, list):
        raise ValueError("resume inventory has an invalid bookkeeping shape")
    return {str(key): dict(value) for key, value in units.items()}, list(map(str, noncalls))


def _scan_atomic_commits(output: Path, experiment: str, model: str):
    """One-time index recovery from atomic markers, without artifact verification.

    Normal restarts use the compact logical inventory. This scan is needed only
    when an older runner did not persist that inventory incrementally (or
    overwrote it during the now-removed bulk verification pass). It reads small
    result headers solely to recover logical-to-content-addressed keys; it does
    not hash, rewrite or otherwise validate historical artifacts.
    """
    root = Path(output)
    units: dict[str, dict[str, Any]] = {}
    noncalls: list[str] = []
    for path in (root / "outputs").glob("*.json"):
        key = path.stem
        if not (root / "completed" / f"{key}.json").is_file():
            continue
        try:
            row = read_json(path)
            if row.get("model") != model or row.get("call_key") != key:
                continue
            case = {"opaque_incident_id": str(row["opaque_incident_id"])}
            dimensions = dict(row.get("dimensions") or {})
            logical = build_call_key(experiment, model, case, dimensions)
        except (KeyError, OSError, TypeError, ValueError):
            continue
        units[logical] = {"status": "bound", "call_key": key}
    for path in (root / "interventions").glob("*.json"):
        try:
            row = read_json(path)
            if row.get("model") != model or row.get("experiment") != experiment:
                continue
            status = str(row.get("status", ""))
            if status not in {"not_applicable", "design_infeasible"}:
                continue
            logical = build_call_key(experiment, model, row["case"], row["dimensions"])
            key = str(row["call_key"])
        except (KeyError, OSError, TypeError, ValueError):
            continue
        units[logical] = {"status": status, "artifact": key,
                          **({"mrr": 0.0} if status == "design_infeasible" else {})}
        noncalls.append(key)
    return units, sorted(set(noncalls))


def fast_phase_status(config: Mapping[str, Any], experiment: str, model: str, output: Path,
                      *, method_lock: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Skip a complete model before loading vLLM; rebuild only cheap bookkeeping."""
    root = Path(output)
    marker = root / f"phase_complete.{model}.json"
    if marker.is_file():
        row = read_json(marker)
        if (row.get("schema_version") == "RQ31PhaseCompletionV1" and
                row.get("status") == "complete" and row.get("experiment") == experiment and
                row.get("model") == model):
            return {"status": "complete", "model": model, "source": "phase_marker",
                    "registered_tasks": int(row["registered_tasks"])}
        raise ValueError("phase completion marker identity is invalid")
    cases = experiment_roster(config, experiment)
    tasks = expand_call_tasks(config, experiment, cases, allow_test=experiment == "exp_final_test",
                              method_lock=method_lock)
    tasks = [task for task in tasks if task["model"] == model]
    expected = {build_call_key(task["experiment"], model, task["case"], task["dimensions"])
                for task in tasks}
    units, noncalls = _scan_atomic_commits(root, experiment, model)
    units = {key: value for key, value in units.items() if key in expected}
    inventory = {"schema_version": "RQ31LogicalInventoryV1", "experiment": experiment,
                 "model": model, "registered_tasks": len(tasks), "units": units,
                 "noncalls": noncalls}
    from vlmrca.run_state import write_json
    write_json(_resume_inventory_path(root, model), inventory)
    status = "complete" if len(units) == len(expected) else "incomplete"
    if status == "complete":
        write_json(marker, {"schema_version": "RQ31PhaseCompletionV1", "status": "complete",
                            "experiment": experiment, "model": model,
                            "registered_tasks": len(tasks)})
    return {"status": status, "model": model, "source": "atomic_commit_index",
            "registered_tasks": len(tasks), "committed": len(units)}


def run_registered_call(task: Mapping[str, Any], parts: list[dict[str, Any]], envelope: Mapping[str, Any], output: Path,
                        *, score_response: Callable[[str], Mapping[str, Any]] | None = None,
                        retry: bool = False, ledger: Any | None = None,
                        scope_limit: int | None = None, reused_record=None) -> dict[str, Any]:
    """Execute one injected request through shared client/writer/scorer stack."""
    import shutil

    from RQs.RQ2.src.utils import AsyncWriter
    from vlmrca.run_state import DurableCallRegister, persisted_model_call
    from vlmrca.vlm.configs import get_config
    output = Path(output); key = str(task["call_key"]); model = str(task["model"]); output.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output).free < 2 * 1024**3:
        raise OSError("less than 2 GiB free; stop submissions and drain completed artifacts")
    if score_response is None:
        raise ValueError("formal RQ3.1 execution requires the granularity-aware scorer; empty scoring is not complete")
    if not task.get("bound") or not task.get("request_hash") or not task.get("projection_hash"):
        raise ValueError("execution requires a task bound to the complete actual request and representation projection")
    expected_key = build_call_key(task["experiment"], model, task["case"], task["dimensions"],
                                  actual_request=str(task["request_hash"]), projection_hash=str(task["projection_hash"]),
                                  adapter_version=str(task.get("adapter_version", "")),
                                  replicate=task.get("replicate", task["dimensions"].get("replicate", 0)),
                                  version=str(task.get("registration_version", "rq31_research_v1")))
    if expected_key != key:
        raise ValueError("call key is not bound to the actual request/projection/adapter identity")
    manifest = {"schema_version": "RQ31InputV1", "call_key": key, "parts": []}
    if task.get("method_lock_hash"):
        manifest["method_lock_hash"] = str(task["method_lock_hash"])
        manifest["config_hash"] = str(task["research_config_hash"])
    for part in parts:
        if part.get("type") == "image":
            manifest["parts"].append({"type": "image", "sha256": hashlib.sha256(part["png"]).hexdigest()})
        else:
            manifest["parts"].append({"type": part.get("type"), "text": str(part.get("text", ""))})
    writer = AsyncWriter(2); writer.json(output / "inputs" / f"{key}.json", manifest); writer.drain()
    ledger = ledger or DurableCallRegister(RQ_LEDGER, limit=HARD_CALL_LIMIT,
                                           scope=str(task.get("ledger_scope", task["experiment"])),
                                           scope_limit=(scope_limit if scope_limit is not None else
                                                        (18 if str(task["experiment"]).startswith("smoke") else None)))
    latest_state = ledger.latest_states().get(key)
    reused = latest_state == "complete" or reused_record is not None
    retry = retry or latest_state in {"interrupted", "infrastructure_failure"}
    wall_started = time.monotonic()
    try:
        # The RQ3.1 solver request adapter intentionally caps completion at
        # 8192; do not inherit the shared model registry's larger ceiling.
        record = reused_record or persisted_model_call(get_config(model, max_tokens=8192), parts, dict(envelope), ledger, key, "solver", output,
                                      retry=retry, prompt_ids=None, writer_factory=AsyncWriter,
                                      artifact_audit=audit_call_artifacts,
                                      raw_processor=lambda raw, root, artifact: (raw or {}, []),
                                      record_hook=lambda rec, response: [])
        score = dict(score_response(record.get("response", "")))
        result = {"schema_version": "RQ31OutputV1", "call_key": key, "model": model,
                  "dataset": task["case"].get("dataset"), "opaque_incident_id": task["case"].get("opaque_incident_id"),
                  "fault_type": task.get("fault_type"),
                  "dimensions": dict(task.get("dimensions") or {}),
                  "response": record.get("response", ""), "score": score,
                  "record_hash": record.get("record_hash"),
                  "reuse_reference": record.get("reuse_reference"),
                  "status": "complete" if score.get("status") == "complete" else "model_failure"}
        output_writer = AsyncWriter(2)
        output_writer.json(output / "outputs" / f"{key}.json", result)
        input_tokens, output_tokens = int(record.get("input_tokens", 0)), int(record.get("output_tokens", 0))
        output_writer.json(output / "cost" / f"{key}.json", {"schema_version": "RQ31CostV1", "call_key": key, "model": model,
                    "status": "complete", "input_tokens": input_tokens, "text_tokens": int(record.get("text_tokens", 0)),
                    "image_tokens": int(record.get("image_tokens", 0)), "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "wall_time_s": float(record.get("latency_s", 0.0)),
                    "postprocessing_wall_s": time.monotonic() - wall_started,
                    "gpu_metadata": {"cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                                     "configured_gpu_memory_utilization":
                                     envelope.get("effective_server", {}).get("gpu_memory_utilization")},
                    "reused": reused, "new_generation_calls": 0 if reused else 1})
        output_writer.drain()
        # This marker is the RQ-local commit boundary. It is intentionally
        # written only after response, score, output and cost persistence; a
        # ledger-complete response without it is safe to replay from cache.
        commit_writer = AsyncWriter(2)
        commit_writer.json(output / "completed" / f"{key}.json", {
            "schema_version": "RQ31CompletionV1", "call_key": key,
            "inputs_sha256": sha_file(output / "inputs" / f"{key}.json"),
            "outputs_sha256": sha_file(output / "outputs" / f"{key}.json"),
            "cost_sha256": sha_file(output / "cost" / f"{key}.json"),
            "conversation_path": f"conversations/{record.get('artifact_key', key)}.md",
            "conversation_sha256": sha_file(output / "conversations" / f"{record.get('artifact_key', key)}.md"),
            "response_artifact_hashes": record.get("artifact_hashes"),
            "record_hash": record.get("record_hash"), "status": "complete"})
        commit_writer.drain()
        audit_completion_artifacts(output, key)
        return result
    except Exception as exc:
        # Keep any accounting already emitted by the shared client (including a
        # response that failed only during scoring/artifact verification). A
        # transport failure with no measured usage gets an explicit zero row.
        cost_path = output / "cost" / f"{key}.json"
        prior_cost = read_json(cost_path) if cost_path.is_file() else {}
        prior_cost.update({"schema_version": "RQ31CostV1", "call_key": key, "model": model,
                           "status": "infrastructure_failure", "error": f"{type(exc).__name__}: {exc}"})
        for field in ("input_tokens", "output_tokens", "total_tokens", "text_tokens", "image_tokens", "wall_time_s"):
            prior_cost.setdefault(field, None)
        failure_writer = AsyncWriter(2)
        failure_writer.json(cost_path, prior_cost)
        failure_writer.drain()
        raise


def run_deduplicated_call(task, parts, envelope, root, *, score_response, scope_limit=None):
    """Same complete request and replicate reuse one response, with logical-arm provenance."""
    import fcntl

    from vlmrca.run_state import atomic_write, write_json
    identity = stable_hash([task["model"], task["case"]["opaque_incident_id"], task["request_hash"],
                            task.get("replicate", 0), task.get("ledger_scope", "formal")])
    cache = RESEARCH_OUTPUT / "response_reuse"
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / f"{identity}.lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        index = cache / f"{identity}.json"
        record = None
        if index.exists():
            source = read_json(index)
            source_root, source_key = Path(source["root"]), source["call_key"]
            if source_root.resolve() != Path(root).resolve() or source_key != task["call_key"]:
                audit_completion_artifacts(source_root, source_key)
                answer = read_json(source_root / "outputs" / f"{source_key}.json")
                cost = read_json(source_root / "cost" / f"{source_key}.json")
                completion = read_json(source_root / "completed" / f"{source_key}.json")
                originals = [p for p in completion["response_artifact_hashes"] if p.endswith(".raw.json")]
                if len(originals) != 1:
                    raise ValueError("reusable response lacks its unique raw record")
                raw_record = read_json(source_root / originals[0])
                key = task["call_key"]
                persisted, files = [], []
                for i, part in enumerate(parts):
                    row = dict(part)
                    if "png" in row:
                        path = Path(root) / "renders" / f"{key}_{i}.png"
                        atomic_write(path, row.pop("png"))
                        row["image_path"] = str(path.relative_to(root))
                        files.append(path)
                    persisted.append(row)
                prompt = Path(root) / "prompts" / f"{key}.json"
                write_json(prompt, {**envelope, "parts": persisted})
                conversation = Path(root) / "conversations" / f"{key}.md"
                body = f"# {key}\n\n## System\n\n{envelope['system']}\n\n## User\n\n"
                body += "\n\n".join(row.get("text", f"![dashboard](../{row.get('image_path', '')})") for row in persisted)
                if (raw_record.get("raw") or {}).get("reasoning_text"):
                    body += f"\n\n## Assistant reasoning (model-generated text)\n\n{raw_record['raw']['reasoning_text']}\n"
                body += f"\n\n## Assistant\n\n{answer['response']}\n"
                atomic_write(conversation, body.encode())
                record = {"call_key": key, "artifact_key": key, "request_hash": task["request_hash"],
                          "response": answer["response"], "role": "solver", "attempt_id": "reused",
                          "raw": raw_record.get("raw"), "performance": raw_record.get("performance"),
                          "policy_version": envelope["policy_version"], "reuse_reference": source,
                          "latency_s": cost["wall_time_s"], **{name: cost[name] for name in
                          ("input_tokens", "output_tokens", "text_tokens", "image_tokens")}}
                record["record_hash"] = stable_hash(record)
                raw_path = Path(root) / "trajectories" / f"{key}.json"
                write_json(raw_path, record)
                record["artifact_hashes"] = {str(path.relative_to(root)): sha_file(path)
                                             for path in [prompt, conversation, raw_path, *files]}
        result = run_registered_call(task, parts, envelope, root, score_response=score_response,
                                     scope_limit=scope_limit, reused_record=record)
        if not index.exists():
            write_json(index, {"root": str(Path(root).resolve()), "call_key": task["call_key"],
                               "request_hash": task["request_hash"], "identity": identity})
        return result


def build_context_request(task, context, config):
    """Single request path for planned checks, formal calls and every intervention."""
    from .exps import (
        materialize_contrast_selection,
        plan_redundant_bundle_load,
        reanonymize_materialized_evidence,
        sanitize_parent_calibration,
        select_contrast_bundles,
        semantic_budget_from_fraction,
    )
    from .utils import compile_representation_twin
    dimensions = task["dimensions"]
    private = dict(context.get("private") or {})
    candidates = tuple(context.get("candidates") or private.get("numeric_to_natural", {}))
    budget = config["selector"].get("standard_semantic_budget") or config["selector"]["candidate_semantic_budget"]
    condition = dimensions.get("condition", "")
    if condition and condition not in _ARM_IDS:
        request = build_mechanism_request(
            task, context, semantic_budget=budget,
            max_payload_char_delta_fraction=config["selector"]["matched_removal_max_payload_char_delta_fraction"])
    else:
        materialized = context.get("materialized")
        schedule = context.get("display_reference_schedule") or ()
        arm = dimensions.get("arm", dimensions.get("method", dimensions.get("representation", condition)))
        twin = context.get("p0_twin") if str(arm).startswith("P0_") else context.get("twin")
        changed = False
        if "budget" in dimensions:
            selection = select_contrast_bundles(
                context["pool"], context["bundles"],
                semantic_budget=semantic_budget_from_fraction(budget, dimensions["budget"]),
                pool_prevalidated=True, bundles_prevalidated=True,
            )
            materialized = materialize_contrast_selection(context["pool"], context["bundles"], selection)
            changed = True
        elif "load" in dimensions:
            plan = plan_redundant_bundle_load(context["pool"], context["bundles"], context["selection"],
                                              load_fraction=dimensions["load"])
            if plan["status"] != "applicable":
                return {"status": "skipped", "intervention_status": plan["status"], "reason": plan.get("reason")}, None
            schedule = plan["display_reference_schedule"]
            changed = True
        elif dimensions.get("transform") == "CANDIDATE_REORDER":
            candidates = tuple(reorder_candidate_ids(candidates, task["case"]["opaque_incident_id"]))
            changed = True
        elif dimensions.get("transform") == "REANONYMIZE":
            transformed = reanonymize_materialized_evidence(
                materialized, candidates=candidates, numeric_to_natural=private["numeric_to_natural"])
            materialized, candidates = transformed["materialized"], tuple(transformed["candidates"])
            private["numeric_to_natural"] = transformed["private_numeric_to_natural"]
            changed = True
        elif dimensions.get("transform"):
            raise ValueError("unregistered request transform")
        is_p0 = str(arm).startswith("P0_")
        if is_p0:
            materialized = sanitize_parent_calibration(context["p0_materialized"])
        needs_twin = is_p0 or str(arm).startswith("X_")
        if needs_twin and not materialized.get("facts"):
            from .renderer.contrast import RepresentationCapacityError
            raise RepresentationCapacityError("no whole eligible evidence bundle fits the registered budget")
        if needs_twin and twin is None:
            changed = True
        if changed:
            twin = compile_representation_twin(materialized, candidates=candidates,
                                               display_reference_schedule=schedule)
            if is_p0:
                from dataclasses import replace

                from RQs.RQ1_1.src.exps import _common_shell
                twin = replace(twin, candidate_text=_common_shell(context["prepared"].public["packet"]))
            if not any(key in dimensions for key in ("budget", "load", "transform")) and isinstance(context, dict):
                context["p0_twin" if is_p0 else "twin"] = twin
        request = build_solver_request(task, twin=twin, prepared=context.get("prepared"), sircl=context.get("sircl"))
    if request.get("status") == "skipped":
        return request, None
    scorer = context.get("score_response") if not private else score_response_callback(private, candidates)
    if scorer is None:
        raise ValueError("request has no private scoring binding")
    return request, scorer


def experiment_roster(config, experiment):
    """A shared frozen hash subset, not the first 100 records of eval."""
    specification, _ = _dimension_rows(config, experiment)
    if specification["population"] != "eval_mechanism_subset":
        return _partition_rows(config, specification["population"])
    rows = _eval_rows(config)
    return [row for dataset in sorted({row["dataset"] for row in rows})
            for row in sorted((row for row in rows if row["dataset"] == dataset),
                              key=lambda row: stable_hash([config["seed"], "mechanisms", row["opaque_incident_id"]]))[:20]]


def _persist_noncall(root, task, reason, *, infeasible=False):
    """Explicit terminal logical unit: no request, no fabricated model output."""
    from vlmrca.run_state import write_json
    key = build_call_key(task["experiment"], task["model"], task["case"], task["dimensions"])
    record = {"schema_version": "RQ31NonCallV1", "call_key": key, **dict(task),
              "status": "design_infeasible" if infeasible else "not_applicable", "reason": reason}
    write_json(root / "interventions" / f"{key}.json", record)
    return key


def run_registered_experiment(config, experiment, cases, contexts, output, *, execute=True,
                              tasks_override=None, deadline=None, model_filter=None, method_lock=None):
    """Bounded producer/inference pipeline; every registered logical unit is accounted for."""
    from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

    from vlmrca.run_state import write_json

    from .renderer.contrast import RepresentationCapacityError
    cfg = dict(config)
    audit_research_config(cfg)
    tasks = list(tasks_override) if tasks_override is not None else expand_call_tasks(
        cfg, experiment, list(cases), allow_test=experiment == "exp_final_test", method_lock=method_lock)
    if execute and tasks_override is not None:
        allowed = {row["opaque_incident_id"] for row in smoke_roster(cfg)}
        if deadline is None or experiment not in cfg["smoke"]["experiments"] or any(
            task["case"]["opaque_incident_id"] not in allowed or
            task.get("ledger_scope") != _smoke_scope(cfg, experiment) for task in tasks
        ):
            raise ValueError("live overrides are restricted to the bounded registered smoke")
    if experiment == "exp_final_test":
        if not method_lock:
            raise ValueError("final test requires an explicit method lock")
        audit_method_lock(dict(method_lock or {}), cfg)
        tasks = [{**task, "method_lock_hash": method_lock["lock_hash"],
                  "research_config_hash": stable_hash(cfg)} for task in tasks]
    if model_filter is not None:
        if model_filter not in cfg["models"]["order"]:
            raise ValueError("model filter is unregistered")
        tasks = [task for task in tasks if task["model"] == model_filter]
    if not tasks:
        raise ValueError("empty task matrix")
    # The lifecycle wrapper owns model startup/switching. A runner cannot silently
    # send the second model's tasks to the first model's server.
    if execute and len({task["model"] for task in tasks}) != 1:
        raise ValueError("execute one model phase at a time")
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    prior_units, prior_noncalls = ({}, [])
    if execute and model_filter is not None:
        prior_units, prior_noncalls = _read_resume_inventory(
            root, experiment, model_filter, len(tasks))
    state_path = root / f"supervisor.{model_filter or tasks[0]['model']}.json"
    state = {"schema_version": "RQ31SupervisorV3", "experiment": experiment, "status": "running",
             "registered_tasks": len(tasks), "submitted": 0, "completed": 0,
             "resumed_completed": 0, "started_at": time.time()}
    expected, failures, terminal, unit_map, pending = [], [], list(prior_noncalls), dict(prior_units), {}
    write_json(state_path, state)
    timed_out = False
    def complete(future):
        bound = pending.pop(future)
        try:
            future.result()
            state["completed"] += 1
        except Exception as exc:
            failures.append({"call_key": bound["call_key"], "error": f"{type(exc).__name__}: {exc}"})
        write_json(state_path, state)
    # At most eight materialized requests + current context reside in memory.
    # Request construction proceeds while already submitted calls use the GPU.
    inference_workers = 8
    cpu_ids = _physical_cpu_ids(inference_workers)
    from itertools import cycle
    with ThreadPoolExecutor(max_workers=inference_workers if deadline is None else 1,
                            thread_name_prefix="rq31-call",
                            initializer=_pin_inference_thread,
                            initargs=(cycle(cpu_ids),)) as executor:
        for task in tasks:
            if failures or STOP_REQUESTED.is_set():
                break
            if deadline is not None and time.monotonic() >= deadline:
                timed_out = True
                break
            logical = build_call_key(task["experiment"], task["model"], task["case"], task["dimensions"])
            prior = unit_map.get(logical)
            if execute and prior:
                status = prior.get("status")
                key = str(prior.get("call_key") or prior.get("artifact") or "")
                committed = status == "bound" and key and (root / "completed" / f"{key}.json").is_file()
                terminal_record = (status in {"not_applicable", "design_infeasible"} and key and
                                   (root / "interventions" / f"{key}.json").is_file())
                if committed or terminal_record:
                    if committed:
                        expected.append(key)
                    elif key not in terminal:
                        terminal.append(key)
                    state["completed"] += 1
                    state["resumed_completed"] += 1
                    if state["completed"] % 64 == 0:
                        write_json(state_path, state)
                    continue
                # A stale bookkeeping row is not a completion. Drop only that
                # row and reconstruct/submit the registered unit normally.
                unit_map.pop(logical, None)
            try:
                context = contexts[task["case"]["opaque_incident_id"]]
                request, scorer = build_context_request(task, context, cfg)
                if request.get("status") == "skipped":
                    terminal.append(_persist_noncall(root, task, request))
                    unit_map[logical] = {"status": "not_applicable", "artifact": terminal[-1]}
                    continue
                audit_actual_request(task, request)
                bound = bind_task_request(task, request["actual_request"], request["projection_hash"],
                                          projection=request["projection"],
                                          version=str(cfg["registration_id"]))
                bound["fault_type"] = (context.get("private") or {}).get("fault_type")
                key = bound["call_key"]
                expected.append(key)
                unit_map[logical] = {"status": "bound", "call_key": key}
                if not execute:
                    write_json(root / "planned" / f"{key}.json",
                               {"task": bound, "request": request["actual_request"], "projection": request["projection"]})
                    continue
                if deadline is not None:
                    import signal
                    previous = signal.getsignal(signal.SIGALRM)
                    prior_remaining, prior_interval = signal.getitimer(signal.ITIMER_REAL)
                    prior_expiry = time.monotonic() + prior_remaining
                    def expired(_signal, _frame):
                        raise TimeoutError("logical smoke deadline reached")
                    signal.signal(signal.SIGALRM, expired)
                    signal.setitimer(signal.ITIMER_REAL, max(.001, deadline - time.monotonic()))
                    try:
                        state["submitted"] += 1
                        result = run_deduplicated_call(bound, request["parts"], request["envelope"], root,
                                            score_response=scorer, scope_limit=18)
                        if result["status"] == "model_failure":
                            raise ValueError("smoke response failed the output-schema contract")
                        state["completed"] += 1
                    finally:
                        signal.setitimer(signal.ITIMER_REAL, 0)
                        signal.signal(signal.SIGALRM, previous)
                        if prior_remaining and prior_expiry > time.monotonic():
                            signal.setitimer(signal.ITIMER_REAL, max(.001, prior_expiry - time.monotonic()), prior_interval)
                else:
                    while len(pending) >= inference_workers:
                        done, _ = wait(pending, return_when=FIRST_COMPLETED)
                        for future in done:
                            complete(future)
                    future = executor.submit(run_deduplicated_call, bound, request["parts"], request["envelope"],
                                             root, score_response=scorer)
                    pending[future] = bound
                    state["submitted"] += 1
            except RepresentationCapacityError as exc:
                terminal.append(_persist_noncall(root, task, str(exc), infeasible=True))
                unit_map[logical] = {"status": "design_infeasible", "artifact": terminal[-1], "mrr": 0.0}
            except TimeoutError:
                if deadline is None:
                    raise
                timed_out = True
                break
            except Exception as exc:
                failures.append({"logical_key": logical, "error": f"{type(exc).__name__}: {exc}"})
                unit_map[logical] = {"status": "infrastructure_failure"}
                # Implementation errors require diagnosis, not running the remaining
                # thousands of identical broken paths. Already submitted calls drain.
                break
            write_json(state_path, state)
        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                complete(future)
    manifest = {"schema_version": "RQ31LogicalInventoryV1", "experiment": experiment,
                "model": model_filter or tasks[0]["model"],
                "registered_tasks": len(tasks), "units": unit_map, "noncalls": terminal}
    manifest_path = root / f"logical_inventory.{model_filter or tasks[0]['model']}.json"
    write_json(manifest_path, manifest)
    # Read both persisted model inventories so the second phase cannot overwrite
    # or silently omit the completed first model.
    manifests = [read_json(path) for path in sorted(root.glob("logical_inventory.*.json"))]
    all_keys = {unit["call_key"] for item in manifests for unit in item["units"].values() if "call_key" in unit}
    summary = aggregate_result_summary(root, all_keys, experiment=experiment) if execute else {"status": "planned"}
    complete_matrix = len(unit_map) == len(tasks) and not failures and summary["status"] == "complete"
    state.update(status="incomplete" if failures else "planned" if not execute else "timeout" if timed_out else
                 "complete" if complete_matrix else "incomplete", ended_at=time.time(), failures=failures,
                 expected_call_keys=expected, logical_inventory=str(manifest_path))
    write_json(state_path, state)
    if execute and state["status"] == "complete" and model_filter is not None:
        write_json(root / f"phase_complete.{model_filter}.json", {
            "schema_version": "RQ31PhaseCompletionV1", "status": "complete",
            "experiment": experiment, "model": model_filter,
            "registered_tasks": len(tasks)})
    if execute:
        summary["logical_inventories"] = manifests
        summary["noncall_records"] = [read_json(root / "interventions" / f"{key}.json")
                                      for item in manifests for key in item["noncalls"]]
        for row in summary["noncall_records"]:
            if row["status"] == "design_infeasible":
                summary["records"].append({"call_key": row["call_key"], "model": row["model"],
                    "dataset": row["case"]["dataset"], "opaque_incident_id": row["case"]["opaque_incident_id"],
                    "dimensions": row["dimensions"], "status": "design_infeasible", "score_status": "not_called",
                    "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                    "metrics": {name: 0.0 for name in ("mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5")}})
        summary["artifact_hash"] = stable_hash(summary["records"])
        summary["averages_population"] = "submitted requests only; include design_infeasible zero rows for end-to-end scores"
        summary["status"] = ("complete" if not failures and all(
            len(item["units"]) == item["registered_tasks"] and all(
                unit["status"] != "infrastructure_failure" for unit in item["units"].values())
            for item in manifests) and summary["status"] == "complete" else "incomplete")
        summary["models_complete"] = sorted({task["model"] for item in manifests
            if len(item["units"]) == item["registered_tasks"] for task in summary["records"]
            if task["model"] == item.get("model")})
        if summary["status"] == "complete" and set(summary["models_complete"]) != set(cfg["models"]["order"]):
            summary["status"] = "model_phase_complete"
        write_json(root / "summary.json", summary)
    return {**state, "summary": summary}


def run_smoke_supervisor(config, contexts, output, *, execute=True, started_at_wall=None):
    """One immutable 600-second/18-call window per logical experiment, including model startup."""
    import signal
    import subprocess

    from vlmrca.run_state import DurableCallRegister, write_json

    from .utils import implementation_hash
    cfg = dict(config)
    audit_research_config(cfg)
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    state_path = root / "supervisor.json"
    state = read_json(state_path) if state_path.exists() else {
        "schema_version": "RQ31LogicalSmokeSupervisorV2", "status": "running",
        "config_hash": stable_hash(cfg), "implementation_hash": implementation_hash(), "experiment_results": []}
    if state.get("config_hash") != stable_hash(cfg) or state.get("implementation_hash") != implementation_hash():
        raise ValueError("existing smoke belongs to different code; explicit repair qualification is required")
    roster = smoke_roster(cfg)
    dimensions = ({"arm": "X_C_TABLE"},
                  {"representation": "X_C_TABLE_S"},
                  {"transform": "CANDIDATE_REORDER", "representation": "X_C"})
    for index, experiment in enumerate(cfg["smoke"]["experiments"]):
        prior = next((r for r in state["experiment_results"] if r["experiment"] == experiment), None)
        if prior and prior["status"] in {"complete", "timeout"}:
            continue
        if prior and prior.get("failures"):
            raise ValueError("prior smoke failed; do not relabel it timeout-only or silently reset its window")
        stage_root = root / experiment
        stage_root.mkdir(parents=True, exist_ok=True)
        window_path = stage_root / "window.json"
        window = read_json(window_path) if window_path.exists() else {
            "started_at": started_at_wall if index == 0 and started_at_wall else time.time()}
        write_json(window_path, window)
        remaining = max(0.0, float(cfg["smoke"]["max_seconds"]) - (time.time() - window["started_at"]))
        deadline = time.monotonic() + remaining
        result = {"experiment": experiment, "status": "running", "failures": [],
                  "completed": 0, "models": [], "deadline_wall": window["started_at"] + 600}
        server = None
        previous = signal.getsignal(signal.SIGALRM)
        def expired(_signum, _frame):
            raise TimeoutError("logical smoke deadline reached")
        try:
            if remaining <= 0:
                raise TimeoutError("registered smoke window exhausted")
            if execute:
                signal.signal(signal.SIGALRM, expired)
                signal.setitimer(signal.ITIMER_REAL, remaining)
            for model in cfg["models"]["order"]:
                if execute:
                    # An existing unrelated listener is never killed or adopted.
                    import socket

                    from unified_scripts.vllm_inference import VLLMInferenceConfig
                    runtime = VLLMInferenceConfig.load().model(model)
                    with socket.socket() as sock:
                        if sock.connect_ex(("127.0.0.1", int(runtime["port"]))) == 0:
                            raise RuntimeError("Solver port already occupied; refusing to replace its owner")
                    env = {**os.environ, "CANVASRCA_ATTENTION_MODE": "off"}
                    with (stage_root / f"{model}.server.log").open("ab") as log:
                        server = subprocess.Popen(["bash", "scripts/vllm_vlm/serve_canvasrca_local.sh", model],
                            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                    wait_process = subprocess.Popen(
                        [os.environ.get("CANVASRCA_PYTHON", os.sys.executable), "-m", "RQs.RQ2_1.src.main",
                         "wait-server", "--model", model, "--pid", str(server.pid)],
                        cwd=ROOT, env=env, start_new_session=True)
                    try:
                        if wait_process.wait(timeout=max(.001, deadline-time.monotonic())) != 0:
                            raise RuntimeError("canonical server readiness failed")
                    finally:
                        if wait_process.poll() is None:
                            os.killpg(wait_process.pid, signal.SIGKILL)
                            wait_process.wait()
                smoke_scope = _smoke_scope(cfg, experiment)
                tasks = [{"experiment": experiment, "ledger_scope": smoke_scope,
                          "model": model, "case": case, "dimensions": dimensions[index]} for case in roster]
                phase = run_registered_experiment(cfg, experiment, roster, contexts, stage_root,
                    execute=execute, tasks_override=tasks, deadline=deadline, model_filter=model)
                result["models"].append(phase)
                result["completed"] += phase["completed"]
                result["failures"].extend(phase.get("failures", []))
                if server is not None:
                    os.killpg(server.pid, signal.SIGTERM)
                    try:
                        server.wait(timeout=max(.001, min(15.0, deadline-time.monotonic())))
                    except subprocess.TimeoutExpired:
                        os.killpg(server.pid, signal.SIGKILL)
                        server.wait()
                    server = None
                if phase["status"] == "timeout":
                    raise TimeoutError("bounded model phase reached deadline")
                if phase["status"] not in {"complete", "planned"}:
                    raise RuntimeError("smoke model phase incomplete")
            result["status"] = "complete" if execute else "planned"
        except (TimeoutError, subprocess.TimeoutExpired):
            result["status"] = "failed" if result["failures"] else "timeout"
        except Exception as exc:
            result["status"] = "failed"
            result["failures"].append({"error": f"{type(exc).__name__}: {exc}"})
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
            if server is not None and server.poll() is None:
                os.killpg(server.pid, signal.SIGKILL)
                server.wait()
        if execute:
            smoke_scope = _smoke_scope(cfg, experiment)
            ledger = DurableCallRegister(RQ_LEDGER, limit=cfg["budget"]["hard_limit"],
                                         scope=smoke_scope, scope_limit=18)
            ledger.recover_persisted(stage_root, audit=audit_call_artifacts)
            with ledger.connect() as database:
                result["initiated_calls"] = database.execute(
                    "SELECT count(*) FROM calls WHERE call_key LIKE ?", (f"{smoke_scope}/%",)).fetchone()[0]
        state["experiment_results"] = [r for r in state["experiment_results"] if r["experiment"] != experiment] + [result]
        write_json(state_path, state)
        if result["status"] == "failed":
            break
    state["status"] = ("complete" if len(state["experiment_results"]) == 3 and all(
        row["status"] in {"complete", "timeout"} for row in state["experiment_results"]) else "incomplete")
    write_json(state_path, state)
    return state






def recover_run(output: Path, experiment: str, *, limit: int = HARD_CALL_LIMIT) -> dict[str, Any]:
    """Recover only committed response artifacts; never stitch partial text."""
    from vlmrca.run_state import DurableCallRegister
    ledger = DurableCallRegister(RQ_LEDGER, limit=limit, scope=experiment)
    return ledger.recover_persisted(Path(output), audit=audit_call_artifacts)


def reconcile_interrupted(output: Path, experiment: str, owner_state: Mapping[str, Any]) -> dict[str, Any]:
    """Mark spent started calls interrupted only after live-owner verification."""
    identity = audit_resume_identity(dict(owner_state), expected_command=owner_state.get("expected_command"))
    if identity["status"] == "owner_alive":
        raise RuntimeError("owner is still alive; do not interrupt or resume")
    from vlmrca.run_state import DurableCallRegister
    ledger = DurableCallRegister(RQ_LEDGER, limit=HARD_CALL_LIMIT, scope=experiment)
    ledger.interrupt_scope(str(owner_state.get("reason", "owner_stopped_before_commit")))
    return {"status": "reconciled", "identity": identity, "ledger": ledger.summary()}


class LazyExecutionContexts(Mapping[str, Mapping[str, Any]]):
    """Lazy, hash-checked view over per-case serialized execution contexts."""

    def __init__(self, index_path: Path, *, compatible_implementations: Iterable[str] = ()):
        self.index_path = Path(index_path)
        self.root = self.index_path.parent
        self.index = read_json(self.index_path)
        if self.index.get("schema_version") != "RQ31ExecutionContextIndexV1":
            raise ValueError("unsupported RQ3.1 execution-context cache")
        recorded_hash = self.index.get("index_hash")
        if not recorded_hash:
            raise ValueError("execution-context index has no committed hash")
        if recorded_hash:
            unsigned = dict(self.index)
            unsigned.pop("index_hash", None)
            if recorded_hash != stable_hash(unsigned):
                raise ValueError("execution-context index hash mismatch")
        self.entries = {str(row["opaque_incident_id"]): dict(row)
                        for row in self.index.get("cases", ())}
        if len(self.entries) != len(self.index.get("cases", ())):
            raise ValueError("execution-context cache has duplicate opaque identities")
        self._loaded_key: str | None = None
        self._loaded: Mapping[str, Any] | None = None
        from .utils import implementation_hash
        allowed = {implementation_hash(), *map(str, compatible_implementations)}
        if self.index.get("contract", {}).get("implementation") not in allowed:
            raise ValueError("execution contexts belong to a different implementation")

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)

    def __getitem__(self, opaque: str) -> Mapping[str, Any]:
        key = str(opaque)
        if key == self._loaded_key and self._loaded is not None:
            return self._loaded
        entry = self.entries[key]
        path = (self.root / str(entry["cache_path"])).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():
            raise ValueError("execution-context cache path is unsafe or missing")
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != entry.get("sha256"):
            raise ValueError(f"execution-context cache hash mismatch: {key}")
        value = pickle.loads(payload)
        if not isinstance(value, Mapping) or value.get("schema_version") != "RQ31ExecutionContextV1":
            raise ValueError("execution-context payload schema mismatch")
        if str(value.get("opaque_incident_id")) != key:
            raise ValueError("execution-context identity mismatch")
        if value.get("contract") != self.index.get("contract"):
            raise ValueError("execution-context source contract mismatch")
        context = dict(value)
        context.pop("schema_version", None)
        context.pop("opaque_incident_id", None)
        self._loaded_key, self._loaded = key, context
        return context


def _write_context_cache_payload(path: Path, payload: Mapping[str, Any]) -> str:
    encoded = pickle.dumps(dict(payload), protocol=5)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("wb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)
    directory = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return hashlib.sha256(encoded).hexdigest()


def _compatible_predecessor_context(
    existing: Mapping[str, Any], current: Mapping[str, Any], config: Mapping[str, Any],
) -> bool:
    """Allow only the pinned validator-only predecessor cache to resume.

    The successor adds inference-time carriers, corrects a field-aware
    validation false positive, and bounds only an over-cap SIRCL payload at the
    request boundary. It does not change any serialized public fact, bundle,
    selection, parent bridge, scorer binding, or stored SIRCL payload. Both
    implementation hashes are pinned so a later source edit cannot inherit
    this exception accidentally.
    """
    compatibility = config.get("context_compatibility") or {}
    from .utils import implementation_hash
    if implementation_hash() != compatibility.get("successor_implementation_hash"):
        return False
    if existing.get("config") != compatibility.get("predecessor_config_hash"):
        return False
    if existing.get("implementation") != compatibility.get("predecessor_implementation_hash"):
        return False
    return all(existing.get(key) == current.get(key)
               for key in ("split", "partition", "budget", "method_lock"))


def _physical_cpu_ids(limit=8):
    """Choose one schedulable logical CPU from each physical core."""
    allowed = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else list(range(os.cpu_count() or 1))
    selected, seen = [], set()
    for cpu in allowed:
        topology = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology")
        try:
            key = ((topology / "physical_package_id").read_text().strip(),
                   (topology / "core_id").read_text().strip())
        except OSError:
            key = ("logical", str(cpu))
        if key not in seen:
            seen.add(key)
            selected.append(cpu)
        if len(selected) >= limit:
            break
    return selected or [0]


def _pin_preparation_worker(cpu_ids):
    """Pin each process-pool worker to a distinct physical core when supported."""
    import multiprocessing
    identity = multiprocessing.current_process()._identity
    index = (identity[0] - 1 if identity else os.getpid()) % len(cpu_ids)
    if hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, {int(cpu_ids[index])})


def _pin_inference_thread(cpu_cycle):
    """Bind each of the eight request workers to a distinct physical CPU core."""
    import threading
    if hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(threading.get_native_id(), {int(next(cpu_cycle))})


def _verify_parent_bridge_reference(prepared, row, rq21_config):
    """Compare the RQ3.1-local bridge with immutable RQ1.1 eval artifacts."""
    parent = ROOT / str(rq21_config["data"]["parent_prepared"])
    index = read_json(parent / "prepared/index.json")
    recorded = index.get("index_sha256")
    unsigned = dict(index)
    unsigned.pop("index_sha256", None)
    if recorded != stable_hash(unsigned) or not index.get("preparation_complete"):
        raise ValueError("RQ1.1 bridge reference index is incomplete or corrupt")
    matches = [item for item in index.get("cases", ())
               if item.get("opaque_incident_id") == row["opaque_incident_id"]]
    if len(matches) != 1:
        raise ValueError("RQ1.1 bridge reference case is absent or duplicated")
    item = matches[0]
    public_path = parent / item["public"]
    image_path = parent / item["full_image"]
    if sha_file(public_path) != item["public_sha256"] or sha_file(image_path) != item["full_image_sha256"]:
        raise ValueError("RQ1.1 bridge reference artifact hash mismatch")
    reference = read_json(public_path)
    checks = {
        "packet": stable_hash(prepared.public["packet"]) == stable_hash(reference["packet"]),
        "dashboard": hashlib.sha256(prepared.full_png).hexdigest() == item["full_image_sha256"],
        "crop_geometry": stable_hash(prepared.public["region_crop_audit"])
        == stable_hash(reference["region_crop_audit"]),
    }
    if not all(checks.values()):
        raise ValueError(f"RQ3.1 bridge differs from its frozen RQ1.1 reference: {checks}")
    return {"status": "byte_semantic_match", "checks": checks,
            "reference_index_sha256": recorded, "reference_public_sha256": item["public_sha256"],
            "reference_image_sha256": item["full_image_sha256"]}


def _prepare_context_worker(arguments):
    """Prepare and atomically persist one independent case in a worker process."""
    row, _slot, budget, contract, target, rq1_config, rq21_config, verify_parent = arguments

    from .exps import (
        build_contrast_bundles,
        build_contrast_evidence_pool_from_v3,
        build_parent_bridge_from_v3,
        build_public_source,
        build_sircl_text_comparator_from_v3,
        materialize_contrast_selection,
        materialize_parent_calibration,
        select_contrast_bundles,
        simple_ranking_controls,
    )
    opaque = row["opaque_incident_id"]
    started = time.monotonic()
    stage_seconds = {}
    last_mark = started

    def stage(name):
        nonlocal last_mark
        now = time.monotonic()
        stage_seconds[name] = now - last_mark
        last_mark = now

    source = build_public_source(opaque, rq21_config, identity=row)
    stage("normalized_per_case_source")
    pool = build_contrast_evidence_pool_from_v3(opaque, rq21_config, source=source)
    stage("independent_X_extraction")
    prepared = build_parent_bridge_from_v3(row["dataset"], row["case_id"], opaque, rq1_config)
    stage("parent_bridge")
    if list(pool.candidates) != sorted(prepared.public["packet"]["candidates"]):
        raise ValueError("independent X/P0 candidate mappings differ; do not silently drop source entities")
    bridge_reference = (
        _verify_parent_bridge_reference(prepared, row, rq21_config)
        if verify_parent else None
    )
    stage("parent_bridge_reference")
    bundles = build_contrast_bundles(pool, pool_prevalidated=True)
    stage("contrast_bundles")
    selection = select_contrast_bundles(
        pool, bundles, semantic_budget=budget,
        pool_prevalidated=True, bundles_prevalidated=True,
    )
    stage("contrast_selection")
    materialized = materialize_contrast_selection(pool, bundles, selection)
    stage("materialization")
    sircl = build_sircl_text_comparator_from_v3(opaque, rq21_config, source=source)
    stage("sircl_comparator")
    payload = {"schema_version": "RQ31ExecutionContextV1", "opaque_incident_id": opaque,
               "contract": contract, "prepared": prepared, "pool": pool, "bundles": bundles,
               "selection": selection, "materialized": materialized,
               "cpu_rankings": simple_ranking_controls(pool, bundles, source),
               "p0_materialized": materialize_parent_calibration(prepared.public["packet"]),
               "candidates": list(pool.candidates), "private": dict(prepared.private), "sircl": sircl,
               "bridge_reference": bridge_reference,
               "source": {"dataset": row["dataset"], "case_id": row["case_id"],
                          "opaque_incident_id": opaque, "source_group": row.get("source")}}
    stage("payload")
    payload["preparation_performance"] = {
        "stage_seconds": stage_seconds,
        "total_s": time.monotonic() - started,
    }
    path = Path(target) / "cases" / f"{opaque}.pkl"
    digest = _write_context_cache_payload(path, payload)
    return {"opaque_incident_id": opaque, "dataset": row["dataset"],
            "source_group": row.get("source"), "cache_path": str(path.relative_to(target)),
            "sha256": digest, "preparation_performance": payload["preparation_performance"]}


def prepare_contexts(config, output, *, limit=None, partition="eval", method_lock=None, opaque_ids=None,
                     max_workers=8, verify_parent_bridge=False):
    """Build one partition-bound source and durable context per case; never touch another partition."""
    from RQs.RQ1_1.src.utils import load_yaml
    from vlmrca.run_state import write_json

    from .utils import implementation_hash
    if partition not in {"eval", "test"}:
        raise ValueError("unregistered preparation partition")
    if partition == "test":
        audit_method_lock(dict(method_lock or {}), dict(config))
    registration_path = ROOT / str(config["data"]["registration"])
    private_path = registration_path.parent / "private/split.json"
    rows = read_json(private_path)["partitions"][partition]
    public_ids = {(r["dataset"], r["opaque_incident_id"]) for r in _partition_rows(config, partition)}
    if {(r["dataset"], r["opaque_incident_id"]) for r in rows} != public_ids or len(rows) != len(public_ids):
        raise ValueError("private/public preparation roster mismatch")
    rows = sorted(rows, key=lambda r: r["opaque_incident_id"])
    if opaque_ids is not None:
        requested = {str(value) for value in opaque_ids}
        rows = [row for row in rows if row["opaque_incident_id"] in requested]
        if {row["opaque_incident_id"] for row in rows} != requested:
            raise ValueError("requested qualification cases are absent from the authorized partition")
    if limit is not None:
        if type(limit) is not int or limit < 1:
            raise ValueError("preparation limit must be positive")
        rows = rows[:limit]
    budget = config["selector"].get("standard_semantic_budget") or config["selector"]["candidate_semantic_budget"]
    current_contract = {"config": stable_hash(config), "implementation": implementation_hash(),
                        "split": sha_file(private_path), "partition": partition, "budget": budget,
                        "method_lock": (method_lock or {}).get("lock_hash")}
    contract = current_contract
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    index_path = target / "index.json"
    existing = read_json(index_path) if index_path.exists() else {}
    compatibility_attestation = None
    if existing and existing.get("contract") != current_contract:
        if not _compatible_predecessor_context(existing.get("contract") or {}, current_contract, config):
            raise ValueError("context contract changed; preserve this cache and choose a new versioned output")
        contract = dict(existing["contract"])
        compatibility_attestation = {
            "schema_version": "RQ31ContextCompatibilityV1",
            "status": "pinned_predecessor_accepted",
            "predecessor_contract_hash": stable_hash(contract),
            "successor_contract_hash": stable_hash(current_contract),
            "scope": config["context_compatibility"]["scope"],
        }
    entries = {r["opaque_incident_id"]: r for r in existing.get("cases", [])}
    rq1_config = load_yaml(ROOT / "RQs/RQ1_1/configs/rq1.yaml")
    rq21_config = load_yaml(ROOT / "RQs/RQ2_1/configs/rq2_1.yaml")
    def commit(status):
        value = {"schema_version": "RQ31ExecutionContextIndexV1", "status": status,
                 "contract": contract, "requested_cases": len(rows),
                 "cases": [entries[key] for key in sorted(entries)]}
        if compatibility_attestation:
            value["compatibility_attestation"] = compatibility_attestation
        value["index_hash"] = stable_hash(value)
        write_json(index_path, value)
    pending = []
    for slot, row in enumerate(rows):
        opaque = row["opaque_incident_id"]
        path = target / "cases" / f"{opaque}.pkl"
        if opaque in entries:
            if not path.is_file() or sha_file(path) != entries[opaque]["sha256"]:
                raise ValueError(f"corrupt context needs explicit repair: {opaque}")
        elif path.is_file():
            # A worker writes its payload atomically before the parent records
            # the index entry.  Power loss or a fail-fast sibling can therefore
            # leave a complete, durable payload orphaned from the partial index.
            # Adopt it only after validating the complete source/contract
            # binding; never trust a filename or silently rebuild valid work.
            encoded = path.read_bytes()
            payload = pickle.loads(encoded)
            required = {
                "prepared", "pool", "bundles", "selection", "materialized",
                "private", "sircl", "source", "preparation_performance",
            }
            if (not isinstance(payload, Mapping)
                    or payload.get("schema_version") != "RQ31ExecutionContextV1"
                    or payload.get("opaque_incident_id") != opaque
                    or payload.get("contract") != contract
                    or not required <= set(payload)):
                raise ValueError(f"unindexed context is not safely adoptable: {opaque}")
            source = payload["source"]
            if (not isinstance(source, Mapping)
                    or source.get("dataset") != row["dataset"]
                    or source.get("opaque_incident_id") != opaque
                    or source.get("case_id") != row["case_id"]):
                raise ValueError(f"unindexed context has the wrong source binding: {opaque}")
            entries[opaque] = {
                "opaque_incident_id": opaque,
                "dataset": row["dataset"],
                "source_group": row.get("source"),
                "cache_path": str(path.relative_to(target)),
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "preparation_performance": payload["preparation_performance"],
            }
        else:
            pending.append((slot, row))
    workers = min(max(1, int(max_workers)), 8, len(pending)) if pending else 0
    if workers:
        from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
        cpu_ids = _physical_cpu_ids(workers)
        pending.sort(key=lambda item: (str(item[1].get("source", "")), item[0]))
        queues: dict[str, list[tuple[int, Mapping[str, Any]]]] = {}
        for item in pending:
            queues.setdefault(str(item[1].get("source", item[1]["dataset"])), []).append(item)
        ordered = []
        while queues:
            for source in sorted(tuple(queues)):
                ordered.append(queues[source].pop(0))
                if not queues[source]:
                    del queues[source]
        with ProcessPoolExecutor(max_workers=workers, initializer=_pin_preparation_worker,
                                 initargs=(cpu_ids,)) as executor:
            active = {}
            iterator = iter(ordered)
            exhausted = False
            while active or not exhausted:
                while len(active) < workers and not exhausted and not STOP_REQUESTED.is_set():
                    try:
                        slot, row = next(iterator)
                    except StopIteration:
                        exhausted = True
                        break
                    arguments = (row, slot, budget, contract, target, rq1_config, rq21_config,
                                 bool(verify_parent_bridge))
                    active[executor.submit(_prepare_context_worker, arguments)] = row
                if not active:
                    break
                done, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in done:
                    row = active.pop(future)
                    entry = future.result()
                    entries[row["opaque_incident_id"]] = entry
                    commit("partial")
    complete = {r["opaque_incident_id"] for r in rows} <= set(entries)
    commit("complete" if complete else "partial")
    return {"status": "complete" if complete else "partial", "cases": len(entries), "path": str(index_path)}


def _processor_token_preflight(config, samples):
    """Apply both real local processors to complete requests without loading weights."""
    import io

    from PIL import Image
    from transformers import AutoProcessor

    from unified_scripts.vllm_inference import VLLMInferenceConfig

    runtime = VLLMInferenceConfig.load()
    rows = []
    for model in config["models"]["order"]:
        spec = runtime.model(model)
        processor = AutoProcessor.from_pretrained(
            runtime.model_path(model), local_files_only=True,
            trust_remote_code=spec.get("trust_remote_code", True),
            **(spec.get("mm_processor_kwargs") or {}),
        )
        for sample in (row for row in samples if row["model"] == model):
            content = []
            image_count = 0
            for part in sample["parts"]:
                if part["type"] == "text":
                    content.append({"type": "text", "text": part["text"]})
                else:
                    image_count += 1
                    content.append({"type": "image", "image": Image.open(io.BytesIO(part["png"])).convert("RGB")})
            kwargs = dict(spec.get("default_chat_template_kwargs") or {})
            if model.startswith("qwen") and kwargs.get("enable_thinking") is False:
                kwargs["preserve_thinking"] = False
            batch = processor.apply_chat_template(
                [{"role": "system", "content": [{"type": "text", "text": sample["system"]}]},
                 {"role": "user", "content": content}],
                tokenize=True, add_generation_prompt=True, return_dict=True,
                return_tensors="pt", **kwargs,
            )
            count = int(batch["input_ids"].shape[-1])
            rows.append({"model": model, "case": sample["case"], "arm": sample["arm"],
                         "input_tokens": count, "image_count": image_count,
                         "fits": count + int(config["request_adapter"]["max_tokens"]) <= int(spec["max_model_len"]),
                         "geometry": {key: list(value.shape) for key, value in batch.items()
                                      if key in {"image_grid_thw", "image_position_ids", "num_soft_tokens_per_image"}}})
        del processor
    return {"schema_version": "RQ31ProcessorPreflightV1", "status": "passed" if all(
        row["fits"] and row["image_count"] <= 1 for row in rows) else "failed", "rows": rows,
        "model_weights_loaded": False, "model_calls": 0}


def run_cpu_qualification(config, output, pytest_report: Path):
    """Create code-bound CPU/visual acceptance; this never starts a model server."""
    import xml.etree.ElementTree as ET

    from vlmrca.run_state import write_json

    from .utils import implementation_hash
    cfg = dict(config)
    audit_research_config(cfg)
    report = Path(pytest_report)
    if not report.is_file():
        raise FileNotFoundError("current CPU qualification requires a persisted pytest JUnit report")
    suites = ET.parse(report).getroot()
    nodes = [suites] if suites.tag == "testsuite" else suites.findall("testsuite")
    failures = sum(int(node.get("failures", 0)) + int(node.get("errors", 0)) for node in nodes)
    tests = sum(int(node.get("tests", 0)) for node in nodes)
    if failures or tests < 77:
        raise ValueError("current RQ3.1 CPU regression suite is incomplete or failed")
    root = Path(output) / "cpu_qualification_v2"
    cache = root / "context_cache"
    roster = smoke_roster(cfg)
    prepared = prepare_contexts(cfg, cache, partition="eval",
                                opaque_ids={row["opaque_incident_id"] for row in roster},
                                verify_parent_bridge=True)
    if prepared["status"] != "complete" or prepared["cases"] != 3:
        raise ValueError("three-case CPU qualification preparation is incomplete")
    contexts = load_execution_contexts(cache, config=cfg)
    arms = [row["id"] for row in cfg["arms"]] + ["X_C_TABLE_S"]
    samples, renders, determinism, sources = [], [], [], []
    for case in roster:
        context = contexts[case["opaque_incident_id"]]
        source = context["sircl"]["source_manifest"]["vendored_reference"]
        if source.get("runtime") != "actual copied MET-Z/TRC-L/LOG-R callables":
            raise ValueError("native SIRCL source parity was not established")
        sources.append({"case": case["opaque_incident_id"], "manifest": source})
        for model in cfg["models"]["order"]:
            for arm in arms:
                task = {"experiment": "cpu_qualification", "model": model, "case": case,
                        "dimensions": {"arm": arm}}
                request, scorer = build_context_request(task, context, cfg)
                if scorer is None:
                    raise ValueError("qualified request lacks a private scorer binding")
                audit_actual_request(task, request)
                repeated, _ = build_context_request(task, context, cfg)
                if request["actual_request"] != repeated["actual_request"] or request["projection_hash"] != repeated["projection_hash"]:
                    raise ValueError("request construction is not deterministic")
                determinism.append({"case": case["opaque_incident_id"], "model": model, "arm": arm,
                                    "request_hash": stable_hash(request["actual_request"])})
                image_parts = [part for part in request["parts"] if part["type"] == "image"]
                if len(image_parts) > 1:
                    raise ValueError("RQ3.1 request contains more than one image")
                if image_parts:
                    render = root / "renders" / case["dataset"] / case["opaque_incident_id"] / f"{arm}.png"
                    if not render.exists():
                        exact_write(render, image_parts[0]["png"])
                    elif render.read_bytes() != image_parts[0]["png"]:
                        raise ValueError("qualification rerender differs from committed PNG")
                    renders.append({"case": case["opaque_incident_id"], "arm": arm,
                                    "path": str(render.relative_to(ROOT)), "sha256": sha_file(render)})
                samples.append({"case": case["opaque_incident_id"], "model": model, "arm": arm,
                                "system": request["envelope"]["system"], "parts": request["parts"]})
    token_report = _processor_token_preflight(cfg, samples)
    if token_report["status"] != "passed":
        raise ValueError("one or more complete requests exceed processor/context capacity")
    index = read_json(cache / "index.json")
    if index.get("status") != "complete" or len(index.get("cases", ())) != 3:
        raise ValueError("qualification context cache is not resume-complete")
    artifacts = {
        "cpu": root / "cpu_regression.json", "visual": root / "visual.json",
        "token_preflight": root / "token_preflight.json", "source_parity": root / "source_parity.json",
        "resume": root / "resume.json",
        "static": ROOT / "RQs/RQ3_1/descriptions/RQ3_1_static_review_20260916_native.md",
    }
    write_json(artifacts["cpu"], {"status": "passed", "tests": tests, "junit_sha256": sha_file(report),
                                  "model_calls": 0})
    write_json(artifacts["visual"], {"status": "passed", "renders": renders,
                                     "deterministic_requests": determinism, "model_calls": 0})
    write_json(artifacts["token_preflight"], token_report)
    write_json(artifacts["source_parity"], {"status": "passed", "cases": sources, "model_calls": 0})
    write_json(artifacts["resume"], {"status": "passed", "index_hash": index["index_hash"],
                                     "case_hashes": {row["opaque_incident_id"]: row["sha256"] for row in index["cases"]},
                                     "model_calls": 0})
    acceptance = {"schema_version": "RQ31CPUAcceptanceV1", "status": "passed",
                  "config_hash": stable_hash(cfg), "implementation_hash": implementation_hash(),
                  "semantic_budget": cfg["selector"]["candidate_semantic_budget"],
                  "checks": {name: "passed" for name in artifacts},
                  "artifact_hashes": {str(path.relative_to(ROOT)): sha_file(path) for path in artifacts.values()},
                  "cases": roster, "model_calls": 0}
    write_json(RESEARCH_OUTPUT / "cpu_acceptance.json", acceptance)
    return acceptance


def load_execution_contexts(path: Path, *, config=None, method_lock=None):
    """Load only source-bound contexts; test authorization precedes any pickle load."""
    path = Path(path) / "index.json" if Path(path).is_dir() else Path(path)
    cfg = config or read_json(RESEARCH_CONFIG)
    from .utils import implementation_hash
    index = read_json(path)
    contract = index.get("contract", {})
    current_contract = {"config": stable_hash(cfg), "implementation": implementation_hash(),
        "split": contract.get("split"), "partition": contract.get("partition"),
        "budget": contract.get("budget"), "method_lock": contract.get("method_lock")}
    predecessor = contract.get("config") != stable_hash(cfg)
    if predecessor:
        # A completed cache may already carry the durable acceptance issued
        # when the registered successor first adopted this exact predecessor.
        # Later runner/resume-only source edits must not force preparation to
        # be regenerated or require changing the scientific config (and hence
        # request identities).  Trust only a self-binding acceptance record;
        # an unattested predecessor still uses the pinned one-time migration.
        attestation = index.get("compatibility_attestation") or {}
        accepted = (
            attestation.get("schema_version") == "RQ31ContextCompatibilityV1"
            and attestation.get("status") == "pinned_predecessor_accepted"
            and attestation.get("predecessor_contract_hash") == stable_hash(contract)
        )
        if not accepted and not _compatible_predecessor_context(contract, current_contract, cfg):
            raise ValueError("execution-context configuration mismatch")
    if contract.get("partition") == "test":
        audit_method_lock(dict(method_lock or {}), dict(cfg))
        if contract.get("method_lock") != method_lock["lock_hash"]:
            raise ValueError("test contexts belong to a different method lock")
    elif contract.get("partition") != "eval":
        raise ValueError("execution contexts have no authorized partition")
    compatible = [contract.get("implementation")] if predecessor else []
    return LazyExecutionContexts(path, compatible_implementations=compatible)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--experiment", type=str)
    parser.add_argument("--model", type=str, help="run one registered model phase")
    parser.add_argument("--owner-state", type=Path)
    parser.add_argument("--contexts", type=Path)
    parser.add_argument("--method-lock", type=Path, help="frozen method lock required for final-test execution")
    parser.add_argument("--inventory", type=Path, help="complete persisted eval summary for method freezing")
    parser.add_argument("--pytest-report", type=Path, help="current JUnit XML required by CPU qualification")
    parser.add_argument("--smoke-started-at", type=float,
                        help="wall timestamp captured before server startup/readiness")
    parser.add_argument("--planned", action="store_true", help="build/persist no model requests")
    parser.add_argument("--limit", type=int, help="limit context preparation to the first cases")
    parser.add_argument("--partition", choices=("eval", "test"), default="eval")
    parser.add_argument("command", nargs="?", choices=("split", "register-research", "validate-research", "qualify-cpu", "prepare-contexts", "smoke", "run", "phase-status", "recover", "reconcile", "freeze"), default="split")
    args = parser.parse_args(argv)
    if args.output is None:
        args.output = DEFAULT_OUTPUT if args.command == "split" else RESEARCH_OUTPUT
        if args.command == "smoke":
            args.output = RESEARCH_OUTPUT / "smoke"
        elif args.command == "prepare-contexts":
            args.output = RESEARCH_OUTPUT / "context_cache"
    exit_status = 0
    owner_handle = None
    if args.command in {"run", "smoke", "recover", "reconcile", "prepare-contexts", "qualify-cpu"}:
        import fcntl
        import signal

        from vlmrca.run_state import write_json

        from .gates import process_identity
        args.output.mkdir(parents=True, exist_ok=True)
        lock_root = args.output if args.command == "prepare-contexts" else RESEARCH_OUTPUT
        lock_root.mkdir(parents=True, exist_ok=True)
        owner_handle = (lock_root / "owner.lock").open("a")
        fcntl.flock(owner_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        write_json(args.output / "owner.json", {**process_identity(os.getpid()), "pid": os.getpid()})
        signal.signal(signal.SIGTERM, lambda *_: STOP_REQUESTED.set())
        signal.signal(signal.SIGINT, lambda *_: STOP_REQUESTED.set())
        os.environ.update(CANVASRCA_ATTENTION_MODE="off", CANVASRCA_ATTENTION_PROBE="0",
                          CANVASRCA_ATTENTION_PROBE_REQUIRED="0")
    if args.command == "register-research":
        print(compact_status(register_research(RESEARCH_CONFIG, args.output, check=args.check)))
    elif args.command == "validate-research":
        print(compact_status(audit_research_config(read_json(RESEARCH_CONFIG))))
    elif args.command == "qualify-cpu":
        if not args.pytest_report:
            parser.error("qualify-cpu requires --pytest-report from the current full RQ3.1 CPU suite")
        print(compact_status(run_cpu_qualification(read_json(RESEARCH_CONFIG), args.output, args.pytest_report)))
    elif args.command == "prepare-contexts":
        cfg = read_json(RESEARCH_CONFIG)
        lock = read_json(args.method_lock) if args.method_lock else None
        print(compact_status(prepare_contexts(cfg, args.output, limit=args.limit,
                                             partition=args.partition, method_lock=lock)))
    elif args.command == "freeze":
        if not args.inventory:
            parser.error("freeze requires --inventory pointing to a complete eval summary")
        print(compact_status(freeze_main_method(args.inventory, args.output)))
    elif args.command in {"run", "smoke"}:
        if not args.contexts:
            parser.error(f"{args.command} requires --contexts (evaluator-owned A/B contexts)")
        cfg = read_json(RESEARCH_CONFIG)
        method_lock = read_json(args.method_lock) if args.method_lock else None
        contexts = load_execution_contexts(args.contexts, config=cfg, method_lock=method_lock)
        if args.command == "smoke":
            result = run_smoke_supervisor(cfg, contexts, args.output, execute=not args.planned,
                                          started_at_wall=args.smoke_started_at)
            print(compact_status(result))
            exit_status = 0 if result["status"] in {"complete", "planned"} else 2
        else:
            if not args.experiment:
                parser.error("run requires --experiment")
            cases = experiment_roster(cfg, args.experiment)
            if args.experiment == "exp_final_test":
                if not args.method_lock or not args.method_lock.is_file():
                    parser.error("final-test run requires --method-lock pointing to a frozen lock")
                method_lock = read_json(args.method_lock)
            result = run_registered_experiment(cfg, args.experiment, cases, contexts, args.output,
                                               execute=not args.planned, model_filter=args.model, method_lock=method_lock)
            print(compact_status(result))
            exit_status = 0 if result["status"] in {"complete", "planned"} else 2
    elif args.command == "phase-status":
        if not args.experiment or not args.model or not args.output:
            parser.error("phase-status requires --experiment, --model and --output")
        cfg = read_json(RESEARCH_CONFIG)
        lock = read_json(args.method_lock) if args.method_lock else None
        result = fast_phase_status(cfg, args.experiment, args.model, args.output, method_lock=lock)
        print(compact_status(result))
        exit_status = 0 if result["status"] == "complete" else 3
    elif args.command == "recover":
        if not args.experiment:
            parser.error("recover requires --experiment")
        print(compact_status(recover_run(args.output, args.experiment)))
    elif args.command == "reconcile":
        if not args.experiment or not args.owner_state:
            parser.error("reconcile requires --experiment and --owner-state")
        print(compact_status(reconcile_interrupted(args.output, args.experiment,
                                                   read_json(args.owner_state))))
    else:
        print(compact_status(materialize(args.config, args.output, check=args.check)))
    if owner_handle is not None:
        owner_handle.close()
    return exit_status


if __name__ == "__main__":
    raise SystemExit(main())

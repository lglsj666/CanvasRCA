"""RQ3.2 durable context preparation and registered experiment projections."""
from __future__ import annotations

import os
import pickle
from collections import OrderedDict
from collections.abc import Mapping
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any

from RQs.RQ3_1.src.exps import reanonymize_materialized_evidence
from RQs.RQ3_1.src.utils import ROOT, exact_write, read_json, sha_file
from unified_scripts import stable_hash

from .contracts import (
    CONTEXTS,
    REDUNDANT_NOISE_MAX_FACTS,
    REDUNDANT_NOISE_MAX_LOG_FACTS,
    load_config,
    partition_rows,
    smoke_roster,
)
from .selector import build_aligned_pool, materialize_x_aligned, select_signal_cover


class DesignNotApplicable(ValueError):
    """Registered evaluator-private intervention has no valid target in a case."""


def preparation_config_hash(config: Mapping[str, Any]) -> str:
    """Hash only inputs that can change an RQ3.2 prepared context.

    Request timeouts, model-serving settings, output budgets, smoke limits, and
    result locations do not participate in CPU context construction.  Keeping
    those operational fields out of this identity lets a formal run resume
    after an operational amendment without rebuilding all 480 contexts, while
    data-source or selector changes still fail closed.
    """
    return stable_hash({
        "schema_version": config.get("schema_version"),
        "registration_id": config.get("registration_id"),
        "seed": config.get("seed"),
        "data": config.get("data"),
        "selector": config.get("selector"),
    })


def _legacy_index_matches_runtime_only_amendment(
        prior: Mapping[str, Any], config: Mapping[str, Any]) -> bool:
    """Recognize exactly the pre-timeout registration, and nothing broader."""
    legacy = deepcopy(dict(config))
    legacy.get("request", {}).pop("timeout_seconds", None)
    return prior.get("config_hash") == stable_hash(legacy)


def _load_parent(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        value = pickle.load(handle)
    if value.get("schema_version") != "RQ31ExecutionContextV1":
        raise ValueError("RQ3.2 requires an RQ3.1 direct-per-case public context")
    return value


def _reservoir(pool, selected_ids: set[str], limit: int = 48) -> list[dict[str, Any]]:
    from RQs.RQ3_1.src.exps import _solver_payload
    relevance = pool.public_statistics["fact_relevance"]
    candidates = [fact for fact in pool.facts if fact["region"] in "MRL" and fact["fact_id"] not in selected_ids]
    candidates.sort(key=lambda fact: (abs(float(relevance.get(fact["fact_id"], 0))),
                                      stable_hash([pool.pool_hash, "noise", fact["fact_id"]])))
    result = []
    for fact in candidates[:limit]:
        result.append({"fact_id": "SC:NOISE:" + str(fact["fact_id"]), "region": fact["region"],
            "field": fact["field"], "entity_ids": list(fact.get("entity_ids") or ()),
            "relative_bins": list(fact.get("relative_bins") or ()), "unit": fact.get("unit") or "public_value",
            "payload": _solver_payload(fact)})
    return result


def _worker(args):
    row, config, target, cpu = args
    try:
        os.sched_setaffinity(0, {cpu})
    except (AttributeError, OSError):
        pass
    from RQs.RQ1_1.src.utils import load_yaml
    rq21 = load_yaml(ROOT / "RQs/RQ2_1/configs/rq2_1.yaml")
    opaque = row["opaque_incident_id"]
    parent_root = ROOT / config["data"]["rq31_eval_contexts" if row.get("_partition", "eval") == "eval"
                                                            else "rq31_test_contexts"]
    parent_path = parent_root / "cases" / f"{opaque}.pkl"
    parent = _load_parent(parent_path)
    pool, bundles, split_audit = build_aligned_pool(parent, rq21)
    p0 = deepcopy(parent["p0_materialized"])
    materialized = {
        "P0_CAL": p0,
        "X_NATIVE_CAL": deepcopy(parent["materialized"]),
        "X_ALIGNED": materialize_x_aligned(pool, bundles),
    }
    selector_audits = {}
    specifications = {
        "SC_COVER": ("cover", False), "SC_FULL": ("full", False),
        "SC_NO_BACKBONE": ("no_backbone", False), "SC_NO_STRATA": ("no_strata", False),
        "SC_STRICT_PAIR": ("strict_pair", False), "P0_MORE": ("p0_more", True),
        "SC_MORE": ("full", True),
    }
    for arm, (mode, more) in specifications.items():
        materialized[arm], selector_audits[arm] = select_signal_cover(pool, p0, mode, more=more)
    selected_ids = {fact["fact_id"].removeprefix("SC:NEW:")
                    for fact in materialized["SC_FULL"]["facts"] if fact["fact_id"].startswith("SC:NEW:")}
    payload = {"schema_version": "RQ32ExecutionContextV1", "opaque_incident_id": opaque,
        "source": {key: row.get(key) for key in ("dataset", "case_id", "opaque_incident_id", "source")},
        "candidates": list(parent["candidates"]), "private": dict(parent["private"]),
        "prepared": parent["prepared"], "sircl": parent["sircl"], "materialized": materialized,
        "selector_audits": selector_audits, "split_audit": split_audit,
        "noise_reservoir": _reservoir(pool, selected_ids), "parent_context_sha256": sha_file(parent_path),
        "contract": {"config_hash": stable_hash(config),
                     "preparation_config_hash": preparation_config_hash(config),
                     "selector": config["selector"]["version"],
                     "partition": row.get("_partition", "eval")}}
    target_path = Path(target) / "cases" / f"{opaque}.pkl"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    data = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    exact_write(target_path, data)
    return {"opaque_incident_id": opaque, "dataset": row["dataset"],
            "path": str(target_path.relative_to(target)), "sha256": sha_file(target_path)}


def _physical_cpus(count: int) -> list[int]:
    allowed = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else list(range(os.cpu_count() or 1))
    siblings = {}
    for cpu in allowed:
        path = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/core_id")
        core = path.read_text().strip() if path.exists() else str(cpu)
        package = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/physical_package_id")
        key = (package.read_text().strip() if package.exists() else "0", core)
        siblings.setdefault(key, cpu)
    values = list(siblings.values())
    if len(values) < count:
        values = allowed
    return values[:count]


def prepare_contexts(config: Mapping[str, Any], target: Path = CONTEXTS, *, rows=None,
                     partition: str = "eval", workers: int = 8) -> dict[str, Any]:
    if workers < 1 or workers > 8:
        raise ValueError("RQ3.2 preparation requires 1..8 workers")
    rows = [dict(row, _partition=partition) for row in (rows or partition_rows(config, partition))]
    target = Path(target); target.mkdir(parents=True, exist_ok=True)
    index_path = target / "index.json"
    prior = read_json(index_path) if index_path.exists() else {}
    expected_preparation_hash = preparation_config_hash(config)
    if prior:
        recorded_preparation_hash = prior.get("preparation_config_hash")
        compatible = (recorded_preparation_hash == expected_preparation_hash
                      if recorded_preparation_hash is not None
                      else _legacy_index_matches_runtime_only_amendment(prior, config))
        if not compatible:
            raise ValueError("existing RQ3.2 contexts belong to another preparation config")
    entries = {row["opaque_incident_id"]: row for row in prior.get("cases", ())}
    pending = [row for row in rows if row["opaque_incident_id"] not in entries]
    cpus = _physical_cpus(workers)
    # Round-robin source groups keeps concurrently opened AIOPS cloudbed tables distinct when possible.
    pending.sort(key=lambda row: (stable_hash([row.get("source"), row["opaque_incident_id"]]), row["opaque_incident_id"]))
    def commit(status):
        value = {"schema_version": "RQ32ContextIndexV1", "status": status,
                 "config_hash": stable_hash(config), "partition": partition,
                 "preparation_config_hash": expected_preparation_hash,
                 "requested_cases": len(rows), "cases": [entries[key] for key in sorted(entries)]}
        value["index_hash"] = stable_hash(value)
        from vlmrca.run_state import write_json
        write_json(index_path, value)
    commit("partial")
    if pending:
        with ProcessPoolExecutor(max_workers=min(workers, len(pending))) as executor:
            active, cursor = {}, iter(enumerate(pending))
            while True:
                while len(active) < workers:
                    try: slot, row = next(cursor)
                    except StopIteration: break
                    active[executor.submit(_worker, (row, dict(config), target, cpus[slot % len(cpus)]))] = row
                if not active: break
                done, _ = wait(active, return_when=FIRST_COMPLETED)
                for future in done:
                    row = active.pop(future); entry = future.result()
                    entries[row["opaque_incident_id"]] = entry; commit("partial")
    commit("complete" if {row["opaque_incident_id"] for row in rows} <= set(entries) else "partial")
    return read_json(index_path)


class ContextStore:
    """Thread-safe, bounded cache for the large durable per-case contexts.

    Formal tasks are ordered by case, so a small LRU retains cross-arm reuse
    without keeping the complete multi-gigabyte corpus resident.  Loading is
    serialized to prevent concurrent misses from materializing duplicate
    copies of the same context.
    """
    def __init__(self, path: Path, *, max_cached_cases: int):
        if max_cached_cases < 1:
            raise ValueError("ContextStore requires at least one cached case")
        self.root = Path(path); self.index = read_json(self.root / "index.json")
        self.max_cached_cases = int(max_cached_cases)
        self.cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._lock = RLock()
        if self.index.get("status") not in {"partial", "complete"}: raise ValueError("invalid RQ3.2 context index")
    def __getitem__(self, opaque: str):
        with self._lock:
            if opaque in self.cache:
                value = self.cache.pop(opaque)
                self.cache[opaque] = value
                return value
            with (self.root / "cases" / f"{opaque}.pkl").open("rb") as handle:
                value = pickle.load(handle)
            self.cache[opaque] = value
            while len(self.cache) > self.max_cached_cases:
                self.cache.popitem(last=False)
            return value


def _clean_materialized(materialized: Mapping[str, Any], keep_ids: set[str]) -> dict[str, Any]:
    result = deepcopy(dict(materialized))
    result["facts"] = [fact for fact in result["facts"] if fact["fact_id"] in keep_ids]
    result["bundles"] = [bundle for bundle in result["bundles"] if set(bundle["fact_ids"]) <= keep_ids]
    result["relations"] = [row for row in result["relations"] if row["fact_id"] in keep_ids]
    return result


def mechanism_materialized(context: Mapping[str, Any], condition: str) -> tuple[dict[str, Any], tuple[str, ...], dict[str, Any]]:
    base = deepcopy(context["materialized"]["SC_FULL"])
    candidates = tuple(context["candidates"])
    private = dict(context["private"])
    if condition in {"NO_GROUPING", "REPLICATE_1", "REPLICATE_2"}: return base, candidates, private
    if condition == "REANONYMIZE":
        transformed = _reanonymize_signal_cover(base, candidates=candidates,
            numeric_to_natural=context["private"]["numeric_to_natural"])
        private["numeric_to_natural"] = transformed["private_numeric_to_natural"]
        return transformed["materialized"], tuple(transformed["candidates"]), private
    if condition == "REDUNDANT_NOISE":
        existing = {fact["fact_id"] for fact in base["facts"]}
        additions = []
        log_facts = 0
        for fact in context["noise_reservoir"]:
            if fact["fact_id"] in existing:
                continue
            if fact["region"] == "L" and log_facts >= REDUNDANT_NOISE_MAX_LOG_FACTS:
                continue
            additions.append(fact)
            log_facts += int(fact["region"] == "L")
            if len(additions) >= REDUNDANT_NOISE_MAX_FACTS:
                break
        base["facts"].extend(additions)
        return base, candidates, private
    accepted = set(context["private"].get("accepted_label_numeric_ids", {}).values())
    facts = [fact for fact in base["facts"] if fact["region"] in "MRL"]
    target = next((fact for fact in facts if accepted & set(fact.get("entity_ids") or ())), None)
    if target is None: raise DesignNotApplicable("no root-associated selected fact")
    if condition == "REMOVE_TARGET": remove = target
    elif condition == "REMOVE_MATCHED_NONTARGET":
        remove = next((fact for fact in facts if fact["region"] == target["region"] and fact["field"] == target["field"]
                       and not accepted.intersection(fact.get("entity_ids") or ())), None)
        if remove is None: raise DesignNotApplicable("no matched non-target fact")
    else: raise ValueError(f"unknown mechanism condition {condition}")
    keep = {fact["fact_id"] for fact in base["facts"]} - {remove["fact_id"]}
    return _clean_materialized(base, keep), candidates, private


def _reanonymize_signal_cover(materialized: Mapping[str, Any], *, candidates,
                              numeric_to_natural: Mapping[str, str]) -> dict[str, Any]:
    """Extend the frozen parent transform for RQ3.2's typed comparison bundle.

    The parent utility remains authoritative for facts, relations, candidates,
    private scorer bindings, and its four historical bundle mechanisms.  The
    only RQ3.2-local addition is ``same_semantics_competing_entities``, whose
    comparison key is ``[region, semantic, left_entity, right_entity]``.
    """
    source = deepcopy(dict(materialized)); positions = []
    native = []
    for index, bundle in enumerate(source.get("bundles") or ()):
        if bundle.get("mechanism") == "same_semantics_competing_entities":
            positions.append((index, deepcopy(bundle)))
        else:
            native.append(bundle)
    source["bundles"] = native
    result = reanonymize_materialized_evidence(
        source, candidates=candidates, numeric_to_natural=numeric_to_natural)
    mapping = result["mapping"]
    # Native bundles retain their relative positions; insert the RQ3.2 bundles
    # after rewriting only their explicitly typed entity positions.
    native_iter = iter(result["materialized"].get("bundles") or ())
    rebuilt = []
    sc_by_index = {index: bundle for index, bundle in positions}
    for index in range(len(native) + len(positions)):
        if index not in sc_by_index:
            rebuilt.append(next(native_iter)); continue
        bundle = sc_by_index[index]
        key = list(bundle.get("comparison_key") or ())
        if len(key) != 4 or any(str(key[pos]) not in mapping for pos in (2, 3)):
            raise ValueError("SignalCover comparison key lacks typed competing entities")
        key[2], key[3] = mapping[str(key[2])], mapping[str(key[3])]
        bundle["comparison_key"] = key
        for side_name in ("side_a", "side_b"):
            side = bundle.get(side_name) or {}
            side["entity_ids"] = [mapping[str(value)] for value in side.get("entity_ids") or ()]
        rebuilt.append(bundle)
    result["materialized"]["bundles"] = rebuilt
    result["result_materialized_hash"] = stable_hash(result["materialized"])
    return result


def qualification_rows(config=None):
    return smoke_roster(config or load_config())


def run_cpu_qualification(config: Mapping[str, Any], contexts: Path, output: Path) -> dict[str, Any]:
    """Build every smoke request twice and apply both real processors; no model call."""
    from RQs.RQ3_1.src.main import _processor_token_preflight
    from vlmrca.run_state import write_json

    from .contracts import smoke_dimension
    from .representation import build_request
    store = ContextStore(contexts, max_cached_cases=config["artifacts"]["context_cache_cases"])
    cases = smoke_roster(config); samples = []; requests = []
    for experiment in config["experiments"]:
        dimension = smoke_dimension(config, experiment)
        for model in config["models"]["order"]:
            # One case per experiment/model is enough for processor qualification;
            # the separate live smoke covers all three registered smoke datasets.
            case = cases[0]
            task = {"experiment": experiment, "model": model, "case": case, "dimensions": dimension}
            first, scorer = build_request(task, store[case["opaque_incident_id"]])
            second, _ = build_request(task, store[case["opaque_incident_id"]])
            if first["actual_request"] != second["actual_request"] or first["projection_hash"] != second["projection_hash"]:
                raise ValueError("RQ3.2 request construction is not deterministic")
            if scorer is None or sum(part["type"] == "image" for part in first["parts"]) > 1:
                raise ValueError("RQ3.2 request lacks scorer or exceeds one image")
            samples.append({"case": case["opaque_incident_id"], "model": model,
                            "arm": f"{experiment}:{stable_hash(dimension)[:8]}",
                            "system": first["envelope"]["system"], "parts": first["parts"]})
            requests.append({"experiment": experiment, "model": model,
                             "request_hash": stable_hash(first["actual_request"]),
                             "projection_hash": first["projection_hash"]})
    translated = {**dict(config), "request_adapter": {"max_tokens": config["request"]["max_tokens"]}}
    tokens = _processor_token_preflight(translated, samples)
    if tokens["status"] != "passed": raise ValueError("RQ3.2 processor/context preflight failed")
    result = {"schema_version": "RQ32CPUQualificationV1", "status": "passed",
              "cases": cases, "requests": requests, "token_preflight": tokens, "model_calls": 0}
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    write_json(output / "cpu_qualification.json", result)
    return result

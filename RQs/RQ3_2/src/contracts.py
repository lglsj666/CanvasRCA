"""Frozen registration, rosters, task matrices, and static RQ3.2 checks."""
from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from RQs.RQ3_1.src.utils import ROOT, read_json
from unified_scripts import stable_hash

CONFIG = ROOT / "RQs/RQ3_2/configs/research_v2.json"
RESULTS = ROOT / "RQs/RQ3_2/results"
CONTEXTS = RESULTS / "contexts_v1"
LEDGER = RESULTS / "rq32_call_ledger.sqlite"
ADAPTER_VERSION = "rq32_solver_request_v2"
REGISTRATION_VERSION = "rq32_signal_cover_v2"
REDUNDANT_NOISE_POLICY_VERSION = "region_capped_v2"
REDUNDANT_NOISE_MAX_FACTS = 12
REDUNDANT_NOISE_MAX_LOG_FACTS = 2


def load_config(path: Path = CONFIG) -> dict[str, Any]:
    config = read_json(path)
    audit_config(config)
    return config


def audit_config(config: Mapping[str, Any]) -> dict[str, Any]:
    if config.get("schema_version") != "RQ32ResearchRegistrationV2":
        raise ValueError("RQ3.2 config schema drift")
    experiments = config.get("experiments") or {}
    expected = {"exp_signal_selection", "exp_signal_representation", "exp_signal_mechanisms",
                "exp_signal_locked_generalization"}
    if set(experiments) != expected:
        raise ValueError("RQ3.2 must register exactly four experiments")
    selection = experiments["exp_signal_selection"]
    if len(selection["arms"]) != 10 or selection["calls"] != 10 * 480 * 2:
        raise ValueError("selection matrix differs from preregistration")
    representation = experiments["exp_signal_representation"]
    if len(representation["selectors"]) * len(representation["representations"]) != 8:
        raise ValueError("representation matrix differs from preregistration")
    mechanisms = experiments["exp_signal_mechanisms"]
    if len(mechanisms["conditions"]) * len(mechanisms["representations"]) != 14:
        raise ValueError("mechanism matrix differs from preregistration")
    expected_noise_policy = {
        "version": REDUNDANT_NOISE_POLICY_VERSION,
        "max_facts": REDUNDANT_NOISE_MAX_FACTS,
        "max_log_facts": REDUNDANT_NOISE_MAX_LOG_FACTS,
        "order": "frozen_noise_reservoir_order",
    }
    if mechanisms.get("redundant_noise_policy") != expected_noise_policy:
        raise ValueError("redundant-noise intervention policy drift")
    if config["budget"]["hard_limit"] != 40000 or config["budget"]["planned_core_calls"] != 28432:
        raise ValueError("RQ3.2 call accounting drift")
    if (config["request"]["max_tokens"] != 8192 or
            config["request"].get("timeout_seconds") != 300 or
            config["request"].get("request_timeout_policy") != "record_terminal_and_continue" or
            config["request"].get("other_infrastructure_policy") != "strict_fail_fast" or
            config["request"]["attention"] != "disabled"):
        raise ValueError("RQ3.2 request contract drift")
    if config.get("artifacts", {}).get("context_cache_cases") != 8:
        raise ValueError("RQ3.2 bounded context-cache contract drift")
    smoke = config["smoke"]
    if smoke["calls_per_experiment"] > smoke["max_calls_per_experiment"]:
        raise ValueError("smoke exceeds its registered call bound")
    if smoke["max_seconds_per_experiment"] != 600:
        raise ValueError("smoke must use the project-wide 600-second bound")
    return {"status": "passed", "config_hash": stable_hash(config),
            "experiments": sorted(experiments), "planned_calls": config["budget"]["planned_core_calls"]}


def partition_rows(config: Mapping[str, Any], partition: str) -> list[dict[str, Any]]:
    private = read_json(ROOT / config["data"]["private_registration"])
    rows = [dict(row) for row in private["partitions"][partition]]
    expected = config["data"][f"{partition}_cases"]
    if len(rows) != expected:
        raise ValueError(f"{partition} roster size differs from registration")
    identities = [(row["dataset"], row["opaque_incident_id"]) for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("partition contains duplicate case identities")
    return sorted(rows, key=lambda row: row["opaque_incident_id"])


def smoke_roster(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = partition_rows(config, "eval")
    selected = []
    for dataset in config["smoke"]["datasets"]:
        pool = [row for row in rows if row["dataset"] == dataset]
        selected.append(min(pool, key=lambda row: stable_hash(
            [config["seed"], "rq32-smoke", dataset, row["opaque_incident_id"]])))
    return selected


def mechanism_roster(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = partition_rows(config, "eval")
    return [row for dataset in sorted({row["dataset"] for row in rows})
            for row in sorted((row for row in rows if row["dataset"] == dataset),
                               key=lambda row: stable_hash([config["seed"], "rq32-mechanism", row["opaque_incident_id"]]))[:20]]


def dimensions(config: Mapping[str, Any], experiment: str) -> list[dict[str, Any]]:
    spec = config["experiments"][experiment]
    if experiment == "exp_signal_selection":
        return [{"arm": arm} for arm in spec["arms"]]
    if experiment == "exp_signal_representation":
        rows = [{"selector": selector, "representation": representation}
                for selector in spec["selectors"] for representation in spec["representations"]]
        rows.extend({"bridge": method} for method in spec["bridge_methods"])
        return rows
    if experiment == "exp_signal_mechanisms":
        return [{"condition": condition, "representation": representation, "replicate":
                 int(condition.rsplit("_", 1)[1]) if condition.startswith("REPLICATE_") else 0}
                for condition in spec["conditions"] for representation in spec["representations"]]
    return [{"method": method} for method in spec["methods"]]


def roster(config: Mapping[str, Any], experiment: str) -> list[dict[str, Any]]:
    if experiment == "exp_signal_mechanisms":
        return mechanism_roster(config)
    if experiment == "exp_signal_locked_generalization":
        return partition_rows(config, "test")
    return partition_rows(config, "eval")


def smoke_dimension(config: Mapping[str, Any], experiment: str) -> dict[str, Any]:
    return {
        "exp_signal_selection": {"arm": "SC_FULL"},
        "exp_signal_representation": {"selector": "SC", "representation": "M_TEXT"},
        "exp_signal_mechanisms": {"condition": "REDUNDANT_NOISE", "representation": "M_TEXT", "replicate": 0},
        "exp_signal_locked_generalization": {"method": "SC_C_CONTRAST"},
    }[experiment]


def call_key(experiment: str, model: str, case: Mapping[str, Any], dimension: Mapping[str, Any],
             request_hash: str, projection_hash: str) -> str:
    return stable_hash({"version": REGISTRATION_VERSION, "adapter": ADAPTER_VERSION,
        "experiment": experiment, "model": model, "case": case["opaque_incident_id"],
        "dimensions": dict(sorted(dimension.items())), "request_hash": request_hash,
        "projection_hash": projection_hash, "replicate": dimension.get("replicate", 0)})


def source_hashes() -> dict[str, str]:
    paths = [CONFIG, ROOT / "docs/CanvasRCA_RQ3_2_Research_Plan_2026-09-20.md"]
    paths.extend(sorted((ROOT / "RQs/RQ3_2/src").glob("*.py")))
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def task_matrix(config: Mapping[str, Any], experiment: str, cases: Iterable[Mapping[str, Any]] | None = None,
                *, models: Iterable[str] | None = None, one_dimension: Mapping[str, Any] | None = None):
    case_rows = list(cases if cases is not None else roster(config, experiment))
    dims = [dict(one_dimension)] if one_dimension is not None else dimensions(config, experiment)
    models = list(models or config["models"]["order"])
    return [{"experiment": experiment, "model": model, "case": dict(case), "dimensions": dict(dimension)}
            for model in models for case in case_rows for dimension in dims]

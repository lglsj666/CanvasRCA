#!/usr/bin/env python3
"""Fail-closed static feasibility check for the DD-35 RQ2a contract."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from rq2lib.factorial import (
    FACTOR_LEVELS,
    FACTOR_ORDER,
    SALIENCE_SCHEMA,
    SALIENCE_WEIGHTS,
    enumerate_factorial_cells,
    main_effect_pairs,
    two_factor_anchors,
)

ROOT = Path(__file__).resolve().parents[3]
RQ_ROOT = ROOT / "RQs/RQ2"
DEFAULT_CONFIG = RQ_ROOT / "configs/rq2a_factorial_v1.yaml"
REQUIRED_DIRS = {"descriptions", "results", "scripts", "src", "findings", "configs"}
LOCKED_RQ1_GATES = {
    "rq1b2_gate_private_v1.json",
    "rq1b3_gate_private_v1.json",
}
DATASETS = {"aegislab", "aiops2022", "aiops2025"}


class StaticContractError(ValueError):
    """Raised when static RQ2 authorization requirements are not satisfied."""


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise StaticContractError(f"config is not a mapping: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise StaticContractError(f"JSON artifact is not an object: {path}")
    return data


def _assert_layout() -> dict[str, Any]:
    actual = {path.name for path in RQ_ROOT.iterdir() if path.is_dir()}
    missing = REQUIRED_DIRS - actual
    if missing:
        raise StaticContractError(f"RQ2 directories missing: {sorted(missing)}")
    root_files = [path.name for path in RQ_ROOT.iterdir() if path.is_file()]
    if root_files:
        raise StaticContractError(f"RQ2 root has files outside six directories: {root_files}")
    if any((RQ_ROOT / "src").iterdir()):
        raise StaticContractError("RQs/RQ2/src must remain empty before final approval")
    return {"required_dirs": sorted(REQUIRED_DIRS), "src_empty": True}


def _assert_config(config: dict[str, Any]) -> dict[str, Any]:
    if config.get("schema_version") != "RQ2AFactorialConfigV1":
        raise StaticContractError("unexpected RQ2a config schema")
    execution = config.get("execution") or {}
    if execution.get("enabled") is not False or execution.get("inference_authorized") is not False:
        raise StaticContractError("RQ2 inference must remain locked")
    factors = (config.get("factorial") or {}).get("factors") or {}
    if tuple(factors) != FACTOR_ORDER:
        raise StaticContractError("factor order differs from the frozen M/G/A/O contract")
    for factor in FACTOR_ORDER:
        observed = (factors[factor].get("minus"), factors[factor].get("plus"))
        if observed != FACTOR_LEVELS[factor]:
            raise StaticContractError(f"factor {factor} treatment levels drifted")
    salience = config.get("label_blind_salience") or {}
    if salience.get("schema_version") != SALIENCE_SCHEMA:
        raise StaticContractError("salience schema drifted")
    observed_weights = salience.get("weights") or {}
    if observed_weights != SALIENCE_WEIGHTS or not math.isclose(
        sum(float(value) for value in observed_weights.values()), 1.0
    ):
        raise StaticContractError("salience weights differ or do not sum to one")
    inference = config.get("inference") or {}
    required_inference = {
        "backend": "vllm",
        "dtype": "bfloat16",
        "quantization": None,
        "max_model_len": 32768,
        "max_tokens": 16384,
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": 42,
        "thinking": False,
        "enforce_eager": True,
        "enable_prefix_caching": False,
        "enable_chunked_prefill": False,
        "gpu_memory_utilization": 0.65,
    }
    mismatch = {
        key: (inference.get(key), value)
        for key, value in required_inference.items()
        if inference.get(key) != value
    }
    if mismatch:
        raise StaticContractError(f"unified inference contract drifted: {mismatch}")
    return {
        "schema_version": config["schema_version"],
        "inference_locked": True,
        "salience_weights_sum": sum(SALIENCE_WEIGHTS.values()),
    }


def _assert_factorial() -> dict[str, Any]:
    cells = enumerate_factorial_cells()
    level_counts = {
        factor: Counter(cell.level(factor) for cell in cells) for factor in FACTOR_ORDER
    }
    if any(counts != Counter({-1: 8, 1: 8}) for counts in level_counts.values()):
        raise StaticContractError(f"factorial is not balanced: {level_counts}")
    for factor in FACTOR_ORDER:
        for minus, plus in main_effect_pairs(factor):
            for other in FACTOR_ORDER:
                if other != factor and minus.level(other) != plus.level(other):
                    raise StaticContractError("main-effect pair changes another factor")
    interaction_counts = {
        f"{first}{second}": len(two_factor_anchors(first, second))
        for index, first in enumerate(FACTOR_ORDER)
        for second in FACTOR_ORDER[index + 1 :]
    }
    return {
        "cell_count": len(cells),
        "main_effect_anchor_pairs": {factor: 8 for factor in FACTOR_ORDER},
        "two_factor_anchor_groups": interaction_counts,
    }


def _roster_ids(path: Path) -> set[str]:
    roster = _load_json(path)
    return {
        str(row["private_case_id"])
        for row in roster.get("cases", [])
        if row.get("private_case_id")
    }


def _assert_data_feasibility(config: dict[str, Any]) -> dict[str, Any]:
    ledger_path = ROOT / str(config["data"]["exposure_ledger_source"])
    ledger = _load_json(ledger_path)
    eligible = [
        row
        for row in ledger.get("exposures", [])
        if row.get("exposure_status") == "exposed"
        and row.get("eligibility_status") == "eligible"
        and "rq1_exposed_development" in (row.get("allowed_uses") or [])
        and row.get("analysis_dataset") in DATASETS
    ]
    roster_paths = sorted((ROOT / "RQs/RQ1/configs/rosters").glob("*private*.json"))
    if not LOCKED_RQ1_GATES <= {path.name for path in roster_paths}:
        raise StaticContractError("locked RQ1 gate roster is missing")
    all_roster_ids: set[str] = set()
    executed_roster_ids: set[str] = set()
    for path in roster_paths:
        ids = _roster_ids(path)
        all_roster_ids |= ids
        if path.name not in LOCKED_RQ1_GATES:
            executed_roster_ids |= ids
    unused = [row for row in eligible if row["private_case_id"] not in all_roster_ids]
    executed = [row for row in eligible if row["private_case_id"] in executed_roster_ids]
    unused_counts = Counter(row["analysis_dataset"] for row in unused)
    executed_counts = Counter(row["analysis_dataset"] for row in executed)
    if any(executed_counts[dataset] < 20 for dataset in DATASETS):
        raise StaticContractError(f"fewer than 20 reusable development cases: {executed_counts}")
    if any(unused_counts[dataset] < 80 for dataset in DATASETS):
        raise StaticContractError(
            "insufficient unused exposed cases for 50-case gate plus 30-case lock: "
            f"{unused_counts}"
        )
    return {
        "eligible_exposed_total": len(eligible),
        "reusable_executed_by_dataset": dict(sorted(executed_counts.items())),
        "unused_outside_every_frozen_roster_by_dataset": dict(
            sorted(unused_counts.items())
        ),
        "unused_total": len(unused),
        "locked_gate_rosters_preserved": sorted(LOCKED_RQ1_GATES),
    }


def _assert_power(config: dict[str, Any]) -> dict[str, Any]:
    gates = config["gates"]
    development = gates["development"]
    independent = gates["independent"]
    dev_mde = (1.96 + 0.84) * float(development["planning_paired_sd"]) / math.sqrt(60)
    gate_low = (1.96 + 0.84) * 0.36 / math.sqrt(150)
    gate_high = (1.96 + 0.84) * 0.50 / math.sqrt(150)
    if not math.isclose(float(development["approximate_mde"]), dev_mde, abs_tol=0.001):
        raise StaticContractError("development MDE does not match the frozen equation")
    frozen_range = [float(value) for value in independent["planning_mde_range"]]
    if not math.isclose(frozen_range[0], gate_low, abs_tol=0.001) or not math.isclose(
        frozen_range[1], gate_high, abs_tol=0.001
    ):
        raise StaticContractError("independent MDE range does not match the frozen equation")
    return {
        "development_mde": round(dev_mde, 6),
        "independent_mde_sd_0.36": round(gate_low, 6),
        "independent_mde_sd_0.50": round(gate_high, 6),
    }


def build_report(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = _load_yaml(config_path)
    return {
        "schema_version": "RQ2AStaticQualificationV1",
        "status": "passed_static_contract_only",
        "inference_authorized": False,
        "layout": _assert_layout(),
        "config": _assert_config(config),
        "factorial": _assert_factorial(),
        "data_feasibility": _assert_data_feasibility(config),
        "power": _assert_power(config),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    print(json.dumps(build_report(args.config), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

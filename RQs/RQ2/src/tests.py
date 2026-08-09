"""CPU-only checks for the compact RQ2 design implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .exps import FACTOR_ORDER, SalienceInput, cells, main_effect_pairs, salience_order
from .gates import validate_gates
from .utils import DEFAULT_CONFIG, load_config, unified_contracts


def run_static_checks(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = load_config(config_path)
    contracts = unified_contracts(config)
    assert len(cells()) == 16
    assert all(len(main_effect_pairs(factor)) == 8 for factor in FACTOR_ORDER)
    rows = (
        SalienceInput("101", (0.0, 8.0, 9.0), (True, False, False), 1),
        SalienceInput("102", (0.0, 1.0, 0.0), (True, True, True), 5),
    )
    assert set(salience_order(rows)) == {"101", "102"}
    return {
        "passed": True,
        "model_calls": 0,
        "factorial": validate_gates(config),
        "unified": {key: value.audit_record() for key, value in contracts.items()},
    }


if __name__ == "__main__":
    print(json.dumps(run_static_checks(), indent=2, sort_keys=True))


from __future__ import annotations

from collections import Counter

from freeze_rq1b2_rosters import DATASETS, select_rq1b2_cases
from rq1lib.roster import DEVELOPMENT_USE


def _ledger(per_dataset: int = 12):
    rows = []
    for dataset in DATASETS:
        for index in range(per_dataset):
            rows.append(
                {
                    "private_case_id": f"{dataset}-case-{index:02d}",
                    "analysis_dataset": dataset,
                    "exposure_status": "exposed",
                    "eligibility_status": "eligible",
                    "allowed_uses": [DEVELOPMENT_USE],
                }
            )
    rows.append(
        {
            "private_case_id": "aegislab-embargoed",
            "analysis_dataset": "aegislab",
            "exposure_status": "exposed",
            "eligibility_status": "embargoed",
            "allowed_uses": [DEVELOPMENT_USE],
        }
    )
    return {"exposures": rows}


def test_rq1b2_selection_is_deterministic_balanced_disjoint_and_exclusion_aware():
    ledger = _ledger()
    excluded = {"aegislab-case-00", "aiops2022-case-00", "aiops2025-case-00"}
    first = select_rq1b2_cases(
        ledger,
        excluded_case_ids=excluded,
        seed=42,
        development_per_dataset=3,
        gate_per_dataset=5,
    )
    second = select_rq1b2_cases(
        ledger,
        excluded_case_ids=excluded,
        seed=42,
        development_per_dataset=3,
        gate_per_dataset=5,
    )
    assert first == second
    development, gate = first
    assert not (set(development) & set(gate))
    assert not ((set(development) | set(gate)) & excluded)
    assert "aegislab-embargoed" not in development + gate
    assert Counter(value.split("-case-")[0] for value in development) == {
        dataset: 3 for dataset in DATASETS
    }
    assert Counter(value.split("-case-")[0] for value in gate) == {
        dataset: 5 for dataset in DATASETS
    }


def test_successor_experiment_key_changes_order_without_weakening_exclusions():
    ledger = _ledger(per_dataset=30)
    excluded = {
        "aegislab-case-00",
        "aiops2022-case-00",
        "aiops2025-case-00",
    }
    rq1b2_development, rq1b2_gate = select_rq1b2_cases(
        ledger,
        excluded_case_ids=excluded,
        seed=42,
        development_per_dataset=5,
        gate_per_dataset=8,
        experiment_key="rq1b2",
    )
    rq1b3_development, rq1b3_gate = select_rq1b2_cases(
        ledger,
        excluded_case_ids=excluded,
        seed=42,
        development_per_dataset=5,
        gate_per_dataset=8,
        experiment_key="rq1b3",
    )
    assert (rq1b2_development, rq1b2_gate) != (
        rq1b3_development,
        rq1b3_gate,
    )
    assert not ((set(rq1b3_development) | set(rq1b3_gate)) & excluded)
    assert not (set(rq1b3_development) & set(rq1b3_gate))
    assert Counter(value.split("-case-")[0] for value in rq1b3_development) == {
        dataset: 5 for dataset in DATASETS
    }
    assert Counter(value.split("-case-")[0] for value in rq1b3_gate) == {
        dataset: 8 for dataset in DATASETS
    }

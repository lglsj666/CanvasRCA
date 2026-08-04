#!/usr/bin/env python3
"""Freeze outcome-blind, disjoint RQ1b successor development/gate rosters."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from rq1lib.contracts import stable_hash
from rq1lib.roster import (
    DEVELOPMENT_USE,
    PARTITION,
    SELECTION_SCHEMA,
    RosterContractError,
    build_frozen_rosters,
    validate_exposure_ledger,
    write_frozen_roster_pair,
)

DATASETS = ("aegislab", "aiops2022", "aiops2025")
PROTOCOL = "RQs/RQ1/descriptions/rq1b2_compositional_complexity_protocol_v1.md"
EXPERIMENT_KEY = "rq1b2"


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RosterContractError(f"{path} is not a JSON object")
    return value


def _hash_order(
    seed: int, experiment_key: str, role: str, dataset: str, case_id: str
) -> str:
    return hashlib.sha256(
        f"{seed}:{experiment_key}:{role}:{dataset}:{case_id}".encode()
    ).hexdigest()


def select_rq1b2_cases(
    ledger: Mapping[str, Any],
    *,
    excluded_case_ids: set[str],
    seed: int,
    development_per_dataset: int,
    gate_per_dataset: int,
    experiment_key: str = EXPERIMENT_KEY,
) -> tuple[list[str], list[str]]:
    """Select two disjoint roles using only frozen exposure metadata."""

    eligible: dict[str, list[str]] = defaultdict(list)
    for row in ledger.get("exposures", []):
        if not isinstance(row, Mapping):
            raise RosterContractError("exposure ledger contains a non-object row")
        dataset = str(row.get("analysis_dataset") or "")
        case_id = str(row.get("private_case_id") or "")
        if (
            dataset in DATASETS
            and case_id not in excluded_case_ids
            and row.get("exposure_status") == "exposed"
            and row.get("eligibility_status") == "eligible"
            and DEVELOPMENT_USE in (row.get("allowed_uses") or [])
        ):
            eligible[dataset].append(case_id)

    development: list[str] = []
    for dataset in DATASETS:
        ordered = sorted(
            eligible[dataset],
            key=lambda case_id: (
                _hash_order(seed, experiment_key, "development", dataset, case_id),
                case_id,
            ),
        )
        if len(ordered) < development_per_dataset + gate_per_dataset:
            raise RosterContractError(
                f"{dataset} has only {len(ordered)} eligible unused cases; "
                f"need {development_per_dataset + gate_per_dataset}"
            )
        development.extend(ordered[:development_per_dataset])

    development_set = set(development)
    gate: list[str] = []
    for dataset in DATASETS:
        remaining = [
            case_id for case_id in eligible[dataset] if case_id not in development_set
        ]
        ordered = sorted(
            remaining,
            key=lambda case_id: (
                _hash_order(seed, experiment_key, "gate", dataset, case_id),
                case_id,
            ),
        )
        if len(ordered) < gate_per_dataset:
            raise RosterContractError(
                f"{dataset} has only {len(ordered)} post-development cases; "
                f"need {gate_per_dataset}"
            )
        gate.extend(ordered[:gate_per_dataset])

    if set(development) & set(gate):
        raise RosterContractError("RQ1b2 development and gate selections overlap")
    return development, gate


def _selection(
    *,
    case_ids: Sequence[str],
    seed: int,
    role: str,
    per_dataset: int,
    experiment_key: str,
    protocol: str,
) -> dict[str, Any]:
    policy = {
        "method": (
            f"exclude all prior RQ1b rosters; per dataset sort eligible exposed cases "
            f"by SHA256({seed}:{experiment_key}:{role}:dataset:case_id), "
            f"first {per_dataset}"
        ),
        "outcome_blind": True,
        "power_analysis_reference": protocol,
        "experiment_key": experiment_key,
        "role": role,
        "per_dataset": per_dataset,
    }
    payload = {
        "schema_version": SELECTION_SCHEMA,
        "status": "frozen",
        "seed": seed,
        "partition": PARTITION,
        "selection_policy": policy,
        "private_case_ids": list(case_ids),
    }
    payload["selection_hash"] = stable_hash(
        {
            "schema_version": SELECTION_SCHEMA,
            "seed": seed,
            "partition": PARTITION,
            "private_case_ids": list(case_ids),
            "selection_policy": policy,
        }
    )
    return payload


def _write_private_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _freeze_role(
    *,
    role: str,
    case_ids: Sequence[str],
    per_dataset: int,
    seed: int,
    draft: Path,
    ledger: Path,
    selection_path: Path,
    private_path: Path,
    public_path: Path,
    experiment_key: str,
    protocol: str,
) -> dict[str, Any]:
    selection = _selection(
        case_ids=case_ids,
        seed=seed,
        role=role,
        per_dataset=per_dataset,
        experiment_key=experiment_key,
        protocol=protocol,
    )
    _write_private_json(selection_path, selection)
    private, public = build_frozen_rosters(
        draft_path=draft,
        ledger_path=ledger,
        selection_path=selection_path,
    )
    write_frozen_roster_pair(
        private_path=private_path,
        public_path=public_path,
        private_roster=private,
        public_roster=public,
    )
    return {
        "role": role,
        "n_cases": public["n_cases"],
        "assignment_hash": public["assignment_hash"],
        "selection_hash": selection["selection_hash"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument(
        "--exclude-private-roster", type=Path, action="append", default=[]
    )
    parser.add_argument("--selection-dir", type=Path, required=True)
    parser.add_argument("--roster-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--development-per-dataset", type=int, default=30)
    parser.add_argument("--gate-per-dataset", type=int, default=50)
    parser.add_argument("--experiment-key", default=EXPERIMENT_KEY)
    parser.add_argument("--protocol", default=PROTOCOL)
    parser.add_argument("--output-prefix", default=EXPERIMENT_KEY)
    args = parser.parse_args()

    ledger, _lineage = validate_exposure_ledger(args.ledger)
    excluded: set[str] = set()
    for path in args.exclude_private_roster:
        roster = _load_object(path)
        if roster.get("private") is not True:
            raise RosterContractError(f"exclusion roster is not private: {path}")
        excluded.update(str(row["private_case_id"]) for row in roster["cases"])
    development, gate = select_rq1b2_cases(
        ledger,
        excluded_case_ids=excluded,
        seed=args.seed,
        development_per_dataset=args.development_per_dataset,
        gate_per_dataset=args.gate_per_dataset,
        experiment_key=args.experiment_key,
    )

    records = []
    for role, cases, count in (
        ("development", development, args.development_per_dataset),
        ("gate", gate, args.gate_per_dataset),
    ):
        records.append(
            _freeze_role(
                role=role,
                case_ids=cases,
                per_dataset=count,
                seed=args.seed,
                draft=args.draft,
                ledger=args.ledger,
                selection_path=args.selection_dir
                / f"{args.output_prefix}_{role}_v1.json",
                private_path=args.roster_dir
                / f"{args.output_prefix}_{role}_private_v1.json",
                public_path=args.roster_dir
                / f"{args.output_prefix}_{role}_public_v1.json",
                experiment_key=args.experiment_key,
                protocol=args.protocol,
            )
        )
    print(json.dumps({"status": "frozen", "roles": records}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

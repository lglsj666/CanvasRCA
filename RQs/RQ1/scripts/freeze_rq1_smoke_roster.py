#!/usr/bin/env python3
"""Freeze the exact three validation cases required by the RQ1 smoke contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from rq1lib.contracts import canonical_json, stable_hash
from rq1lib.roster import (
    PRIVATE_ROSTER_SCHEMA,
    PUBLIC_ROSTER_SCHEMA,
    SMOKE_PARTITION,
    SMOKE_USE,
    _assignment_payload,
    validate_exposure_ledger,
    validate_frozen_roster_pair,
    write_frozen_roster_pair,
)
from vlmrca.render.dashboard import opaque_incident_id

ROOT = Path(__file__).resolve().parents[3]
DATASET_ORDER = ("re2_ob", "aiops2022", "aiops2025")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} is not a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--source-partition-roster", type=Path, required=True)
    parser.add_argument("--selection-out", type=Path, required=True)
    parser.add_argument("--private-out", type=Path, required=True)
    parser.add_argument("--public-out", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.selection_out, args.private_out, args.public_out):
        if path.exists():
            raise SystemExit(f"refusing to overwrite frozen smoke artifact {path}")

    ledger, lineage = validate_exposure_ledger(args.ledger)
    source_bytes = args.source_partition_roster.read_bytes()
    source = _load(args.source_partition_roster)
    validation = source["partitions"]["validation"]
    case_ids: list[str] = []
    for dataset in DATASET_ORDER:
        rows = validation.get(dataset)
        if not isinstance(rows, list) or len(rows) != 1:
            raise SystemExit(
                f"validation roster must contain exactly one {dataset} case"
            )
        case_ids.append(str(rows[0]))

    selection = {
        "schema_version": "RQ1SmokeSelectionV1",
        "status": "frozen",
        "seed": 42,
        "partition": SMOKE_PARTITION,
        "selection_rule": "reuse exact RQ0 validation case for re2_ob, aiops2022, aiops2025",
        "source_partition_roster_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "private_case_ids": case_ids,
    }
    selection["selection_hash"] = stable_hash(selection)
    args.selection_out.parent.mkdir(parents=True, exist_ok=True)
    args.selection_out.write_text(canonical_json(selection) + "\n", encoding="utf-8")
    selection_file_sha256 = hashlib.sha256(args.selection_out.read_bytes()).hexdigest()

    by_id = {row["private_case_id"]: row for row in ledger["exposures"]}
    private_rows: list[dict[str, Any]] = []
    for case_id in case_ids:
        entry = by_id.get(case_id)
        if (
            entry is None
            or entry["eligibility_status"] != "eligible"
            or SMOKE_USE not in entry["allowed_uses"]
        ):
            raise SystemExit(
                f"case is not authorized for RQ1 validation smoke: {case_id}"
            )
        private_rows.append(
            {
                "private_case_id": case_id,
                "opaque_incident_id": opaque_incident_id(case_id),
                "analysis_dataset": entry["analysis_dataset"],
                "analysis_leakage_group_id": entry["analysis_leakage_group_id"],
            }
        )
    opaque_ids = [row["opaque_incident_id"] for row in private_rows]
    assignment_hash = stable_hash(
        _assignment_payload(
            seed=42,
            opaque_incident_ids=opaque_ids,
            lineage=lineage,
            partition=SMOKE_PARTITION,
        )
    )
    draft_sha256 = stable_hash(
        {
            "selection_hash": selection["selection_hash"],
            "partition": SMOKE_PARTITION,
        }
    )
    transition = {
        "from": "draft_unfrozen",
        "to": "frozen",
        "draft_sha256": draft_sha256,
        "transition_id": stable_hash(
            {
                "draft_sha256": draft_sha256,
                "assignment_hash": assignment_hash,
                "ledger_file_sha256": lineage["ledger_file_sha256"],
            }
        ),
    }
    public = {
        "schema_version": PUBLIC_ROSTER_SCHEMA,
        "status": "frozen",
        "seed": 42,
        "partition": SMOKE_PARTITION,
        "exposure_ledger_lineage": lineage,
        "assignment_hash": assignment_hash,
        "cases": [{"opaque_incident_id": value} for value in opaque_ids],
        "n_cases": 3,
        "status_transition": transition,
        "execution_allowed": True,
        "model_visible": False,
        "note": "Public RQ1 validation smoke roster; excluded from efficacy analysis.",
    }
    private = {
        "schema_version": PRIVATE_ROSTER_SCHEMA,
        "status": "frozen",
        "seed": 42,
        "partition": SMOKE_PARTITION,
        "exposure_ledger_lineage": lineage,
        "assignment_hash": assignment_hash,
        "private_assignment_hash": stable_hash(
            {
                "seed": 42,
                "partition": SMOKE_PARTITION,
                "cases": private_rows,
                "ledger_assignment_hash": lineage["exposure_assignment_hash"],
                "selection_file_sha256": selection_file_sha256,
            }
        ),
        "selection_file_sha256": selection_file_sha256,
        "cases": private_rows,
        "n_cases": 3,
        "status_transition": transition,
        "execution_allowed": False,
        "private": True,
        "note": "Evaluator-only RQ1 validation smoke mapping.",
    }
    validate_frozen_roster_pair(
        public_roster=public,
        private_roster=private,
        ledger=ledger,
        lineage=lineage,
    )
    write_frozen_roster_pair(
        private_path=args.private_out,
        public_path=args.public_out,
        private_roster=private,
        public_roster=public,
    )
    print(
        json.dumps(
            {
                "status": "frozen",
                "n_cases": 3,
                "assignment_hash": assignment_hash,
                "datasets": list(DATASET_ORDER),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

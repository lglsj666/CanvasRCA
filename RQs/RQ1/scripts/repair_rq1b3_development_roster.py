#!/usr/bin/env python3
"""Repair the RQ1b3 development roster using label-blind task eligibility."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from prepare_rq1_visops import _real_case_ceb
from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash
from rq1lib.evidence import build_evidence_store_v2
from rq1lib.roster import (
    DEVELOPMENT_USE,
    PARTITION,
    SELECTION_SCHEMA,
    build_frozen_rosters,
    canonical_opaque_incident_id,
    validate_exposure_ledger,
    write_frozen_roster_pair,
)
from rq1lib.visops import build_two_stage_onset_tasks_v2

DATASETS = ("aegislab", "aiops2022", "aiops2025")
EXPECTED_DEFICITS = {"aegislab": 4, "aiops2022": 5, "aiops2025": 4}
PROTOCOL = "RQs/RQ1/descriptions/rq1b3_two_stage_onset_ledger_protocol_v2.md"


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path} is not a JSON object")
    return value


def development_order_key(seed: int, dataset: str, case_id: str) -> tuple[str, str]:
    digest = hashlib.sha256(
        f"{seed}:rq1b3:development:{dataset}:{case_id}".encode()
    ).hexdigest()
    return digest, case_id


def rank_candidates(
    rows: Sequence[Mapping[str, Any]], *, excluded: set[str], seed: int
) -> dict[str, list[str]]:
    ranked: dict[str, list[str]] = {}
    for dataset in DATASETS:
        eligible = [
            str(row["private_case_id"])
            for row in rows
            if row.get("analysis_dataset") == dataset
            and str(row.get("private_case_id") or "") not in excluded
            and row.get("exposure_status") == "exposed"
            and row.get("eligibility_status") == "eligible"
            and DEVELOPMENT_USE in (row.get("allowed_uses") or [])
        ]
        ranked[dataset] = sorted(
            eligible, key=lambda case_id: development_order_key(seed, dataset, case_id)
        )
    return ranked


def _task_eligible(dataset: str, case_id: str) -> tuple[bool, str]:
    try:
        ceb, dense, private_markers = _real_case_ceb(dataset, case_id)
        store = build_evidence_store_v2(
            ceb, dense, private_markers=private_markers
        )
        tasks = build_two_stage_onset_tasks_v2(store)
    # Qualification must fail closed for any dataset/compiler defect; only the
    # categorical outcome is recorded, never exception text or private data.
    except Exception:  # noqa: BLE001
        return False, "compiler_rejected"
    if len(tasks) != 1:
        return False, "no_single_registered_task"
    task = tasks[0]
    if task.query.operation != "panel_onset_ledger_high_compact":
        return False, "wrong_operation"
    if int(task.query.parameters.get("series_count", -1)) != 12:
        return False, "wrong_series_count"
    return True, "eligible_exactly_one_12_panel_task"


def _selection_payload(case_ids: Sequence[str], *, seed: int) -> dict[str, Any]:
    policy = {
        "method": (
            "DD-33: retain task-eligible original RQ1b3 development cases; "
            "replace only 4/5/4 dataset deficits by the frozen "
            "SHA256(42:rq1b3:development:dataset:case_id) order after excluding "
            "all prior RQ1 private-roster cases and the unopened RQ1b3 gate; "
            "accept only exactly one frozen v2 12-panel task"
        ),
        "outcome_blind": True,
        "power_analysis_reference": PROTOCOL,
        "experiment_key": "rq1b3",
        "role": "development_roster_repair",
        "per_dataset": 30,
        "task_eligibility": "exactly_one_two_stage_onset_ledger_v2_12_panel_task",
        "root_cause_label_read": False,
        "model_output_read": False,
    }
    payload: dict[str, Any] = {
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


def _exclusive_write(path: Path, payload: Mapping[str, Any], *, private: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600 if private else 0o644,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(canonical_json(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--original-private-roster", type=Path, required=True)
    parser.add_argument("--exclude-private-roster", type=Path, action="append", default=[])
    parser.add_argument("--selection-output", type=Path, required=True)
    parser.add_argument("--private-roster-output", type=Path, required=True)
    parser.add_argument("--public-roster-output", type=Path, required=True)
    parser.add_argument("--private-audit-output", type=Path, required=True)
    parser.add_argument("--public-audit-output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    ledger, lineage = validate_exposure_ledger(args.ledger)
    original = _load_object(args.original_private_roster)
    if original.get("private") is not True or original.get("n_cases") != 90:
        raise ContractError("original roster must be the private frozen 90-case roster")

    original_by_dataset: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in original["cases"]:
        original_by_dataset[str(row["analysis_dataset"])].append(
            {
                "private_case_id": str(row["private_case_id"]),
                "opaque_incident_id": str(row["opaque_incident_id"]),
            }
        )
    if {key: len(value) for key, value in original_by_dataset.items()} != {
        dataset: 30 for dataset in DATASETS
    }:
        raise ContractError("original roster must contain 30 cases per dataset")

    original_audit: dict[str, list[dict[str, str]]] = defaultdict(list)
    retained: dict[str, list[str]] = defaultdict(list)
    for dataset in DATASETS:
        for row in original_by_dataset[dataset]:
            eligible, reason = _task_eligible(dataset, row["private_case_id"])
            original_audit[dataset].append(
                {
                    **row,
                    "status": "eligible" if eligible else "unsupported",
                    "reason": reason,
                }
            )
            if eligible:
                retained[dataset].append(row["private_case_id"])

    deficits = {dataset: 30 - len(retained[dataset]) for dataset in DATASETS}
    if deficits != EXPECTED_DEFICITS:
        raise ContractError(
            f"original task-eligibility deficits differ from registered DD-33: {deficits}"
        )

    excluded: set[str] = set()
    for path in args.exclude_private_roster:
        roster = _load_object(path)
        if roster.get("private") is not True:
            raise ContractError(f"exclusion roster is not private: {path}")
        excluded.update(str(row["private_case_id"]) for row in roster["cases"])
    excluded.update(
        str(row["private_case_id"]) for row in original["cases"]
    )
    ranked = rank_candidates(ledger["exposures"], excluded=excluded, seed=args.seed)

    scans: dict[str, list[dict[str, str]]] = defaultdict(list)
    accepted: dict[str, list[str]] = defaultdict(list)
    for dataset in DATASETS:
        for case_id in ranked[dataset]:
            eligible, reason = _task_eligible(dataset, case_id)
            record = {
                "private_case_id": case_id,
                "opaque_incident_id": canonical_opaque_incident_id(case_id),
                "status": "accepted" if eligible else "rejected",
                "reason": reason,
            }
            scans[dataset].append(record)
            if eligible:
                accepted[dataset].append(case_id)
                if len(accepted[dataset]) == deficits[dataset]:
                    break
        if len(accepted[dataset]) != deficits[dataset]:
            raise ContractError(
                f"{dataset} produced only {len(accepted[dataset])}/{deficits[dataset]} replacements"
            )

    final_ids: list[str] = []
    for dataset in DATASETS:
        final_ids.extend([*retained[dataset], *accepted[dataset]])
    if len(final_ids) != 90 or len(set(final_ids)) != 90:
        raise ContractError("repaired selection is not 90 unique cases")

    selection = _selection_payload(final_ids, seed=args.seed)
    _exclusive_write(args.selection_output, selection, private=True)
    private_roster, public_roster = build_frozen_rosters(
        draft_path=args.draft,
        ledger_path=args.ledger,
        selection_path=args.selection_output,
    )
    write_frozen_roster_pair(
        private_path=args.private_roster_output,
        public_path=args.public_roster_output,
        private_roster=private_roster,
        public_roster=public_roster,
    )

    private_audit: dict[str, Any] = {
        "schema_version": "RQ1b3DevelopmentRosterRepairPrivateAuditV1",
        "status": "qualified_frozen",
        "decision": "DD-33",
        "root_cause_label_read": False,
        "model_output_read": False,
        "task_profile": "two_stage_onset_ledger_v2",
        "seed": args.seed,
        "lineage": lineage,
        "original_roster_sha256": sha256_bytes(
            args.original_private_roster.read_bytes()
        ),
        "selection_hash": selection["selection_hash"],
        "deficits": deficits,
        "original": dict(original_audit),
        "candidate_scans": dict(scans),
        "accepted_counts": dict(
            Counter(
                next(
                    row["analysis_dataset"]
                    for row in private_roster["cases"]
                    if row["private_case_id"] == case_id
                )
                for case_id in final_ids
            )
        ),
        "private_roster_assignment_hash": private_roster["private_assignment_hash"],
    }
    private_audit["audit_hash"] = stable_hash(private_audit)
    _exclusive_write(args.private_audit_output, private_audit, private=True)

    def public_rows(rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
        return [
            {
                "opaque_incident_id": row["opaque_incident_id"],
                "status": row["status"],
                "reason": row["reason"],
            }
            for row in rows
        ]

    public_audit: dict[str, Any] = {
        "schema_version": "RQ1b3DevelopmentRosterRepairPublicAuditV1",
        "status": "qualified_frozen",
        "decision": "DD-33",
        "root_cause_label_read": False,
        "model_output_read": False,
        "task_profile": "two_stage_onset_ledger_v2",
        "seed": args.seed,
        "deficits": deficits,
        "original": {dataset: public_rows(original_audit[dataset]) for dataset in DATASETS},
        "candidate_scans": {dataset: public_rows(scans[dataset]) for dataset in DATASETS},
        "final_counts": {dataset: 30 for dataset in DATASETS},
        "selection_hash": selection["selection_hash"],
        "roster_assignment_hash": public_roster["assignment_hash"],
        "private_audit_file_sha256": None,
    }
    public_audit["private_audit_file_sha256"] = sha256_bytes(
        args.private_audit_output.read_bytes()
    )
    public_audit["audit_hash"] = stable_hash(public_audit)
    _exclusive_write(args.public_audit_output, public_audit, private=False)

    print(
        json.dumps(
            {
                "status": "qualified_frozen",
                "deficits": deficits,
                "candidate_scans": {
                    dataset: len(scans[dataset]) for dataset in DATASETS
                },
                "final_counts": {dataset: 30 for dataset in DATASETS},
                "selection_hash": selection["selection_hash"],
                "roster_assignment_hash": public_roster["assignment_hash"],
                "public_audit": str(args.public_audit_output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

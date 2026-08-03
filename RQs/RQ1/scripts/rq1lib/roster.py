"""Fail-closed exposure and roster contracts for provisional RQ1 work.

This module intentionally does not discover exposure by scanning the dataset or
guessing from a case identifier.  A case is eligible only when a frozen,
project-wide exposure ledger explicitly marks it as exposed, eligible, and
authorized for RQ1 development.  Absence from that ledger means "unknown" and
is therefore a hard failure.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from vlmrca.render.dashboard import opaque_incident_id as canonical_opaque_incident_id

from .contracts import ContractError, assert_label_blind, canonical_json, stable_hash

LEDGER_SCHEMA = "CanvasRCAExposureLedgerV2"
SELECTION_SCHEMA = "RQ1PrivateExposedSelectionV1"
PUBLIC_ROSTER_SCHEMA = "RQ1PublicRosterV1"
PRIVATE_ROSTER_SCHEMA = "RQ1PrivateRosterV1"

LEDGER_SCOPE = "project_history_complete_through_cutoff"
DEVELOPMENT_USE = "rq1_exposed_development"
PARTITION = "exposed_development_only"
SMOKE_USE = "rq1_validation_smoke"
SMOKE_PARTITION = "validation_smoke_only"

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
GIT_COMMIT_RE = re.compile(r"^[a-f0-9]{7,64}$")
OPAQUE_ID_RE = re.compile(r"^INC-[A-F0-9]{12}$")


class RosterContractError(ContractError):
    """An exposure-ledger or roster-freeze invariant was violated."""


def _load_object(path: Path, *, kind: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RosterContractError(f"cannot read {kind}: {exc}") from exc
    if not isinstance(value, dict):
        raise RosterContractError(f"{kind} must be a JSON object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RosterContractError(f"{field} must be a non-empty string")
    return value


def _require_exact_keys(
    value: Mapping[str, Any], expected: set[str], *, kind: str
) -> None:
    actual = set(value)
    if actual != expected:
        raise RosterContractError(
            f"{kind} fields differ from the frozen schema: "
            f"missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
        )


def _exposure_assignment_payload(ledger: Mapping[str, Any]) -> dict[str, Any]:
    exposures = ledger.get("exposures")
    if not isinstance(exposures, list):
        raise RosterContractError("exposure ledger exposures must be a list")
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(exposures):
        if not isinstance(raw, Mapping):
            raise RosterContractError(f"exposures[{index}] must be an object")
        _require_exact_keys(
            raw,
            {
                "private_case_id",
                "analysis_dataset",
                "analysis_leakage_group_id",
                "exposure_status",
                "eligibility_status",
                "allowed_uses",
                "sources",
            },
            kind=f"exposures[{index}]",
        )
        case_id = _require_string(
            raw.get("private_case_id"), field=f"exposures[{index}].private_case_id"
        )
        analysis_dataset = _require_string(
            raw.get("analysis_dataset"), field=f"exposures[{index}].analysis_dataset"
        )
        leakage_group = raw.get("analysis_leakage_group_id")
        if leakage_group is not None and (
            not isinstance(leakage_group, str) or not leakage_group.strip()
        ):
            raise RosterContractError(
                f"exposures[{index}].analysis_leakage_group_id must be null or non-empty"
            )
        if raw.get("exposure_status") != "exposed":
            raise RosterContractError(
                f"exposures[{index}].exposure_status must be 'exposed'"
            )
        eligibility = raw.get("eligibility_status")
        if eligibility not in {"eligible", "invalid", "embargoed"}:
            raise RosterContractError(
                f"exposures[{index}].eligibility_status is unsupported"
            )
        allowed_uses = raw.get("allowed_uses")
        if not isinstance(allowed_uses, list) or any(
            not isinstance(item, str) or not item for item in allowed_uses
        ):
            raise RosterContractError(
                f"exposures[{index}].allowed_uses must be strings"
            )
        if len(allowed_uses) != len(set(allowed_uses)):
            raise RosterContractError(f"exposures[{index}].allowed_uses has duplicates")
        sources = raw.get("sources")
        if (
            not isinstance(sources, list)
            or not sources
            or any(not isinstance(item, str) or not item for item in sources)
        ):
            raise RosterContractError(
                f"exposures[{index}].sources must contain at least one string"
            )
        if len(sources) != len(set(sources)):
            raise RosterContractError(f"exposures[{index}].sources has duplicates")
        normalized.append(
            {
                "private_case_id": case_id,
                "analysis_dataset": analysis_dataset,
                "analysis_leakage_group_id": leakage_group,
                "exposure_status": "exposed",
                "eligibility_status": eligibility,
                "allowed_uses": sorted(allowed_uses),
                "sources": sorted(set(sources)),
            }
        )
    ids = [row["private_case_id"] for row in normalized]
    if len(ids) != len(set(ids)):
        raise RosterContractError(
            "exposure ledger contains duplicate private_case_id values"
        )
    return {
        "schema_version": LEDGER_SCHEMA,
        "scope": LEDGER_SCOPE,
        "cutoff_git_commit": ledger.get("cutoff_git_commit"),
        "unknown_case_policy": "reject",
        "unused_policy": "terminal_embargo",
        "exposures": sorted(normalized, key=lambda row: row["private_case_id"]),
    }


def validate_exposure_ledger(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate an explicitly authoritative ledger and return its safe lineage.

    The legacy RQ0 ledger intentionally fails this contract: it predates later
    formal runs and does not attest complete project history, case eligibility,
    or authorized uses.
    """

    ledger = _load_object(path, kind="exposure ledger")
    _require_exact_keys(
        ledger,
        {
            "schema_version",
            "status",
            "scope",
            "cutoff_git_commit",
            "unknown_case_policy",
            "unused_policy",
            "exposure_assignment_hash",
            "exposures",
        },
        kind="authoritative exposure ledger",
    )
    if ledger.get("schema_version") != LEDGER_SCHEMA:
        raise RosterContractError(
            f"authoritative exposure ledger must use {LEDGER_SCHEMA}; "
            "legacy or RQ-scoped ledgers cannot unlock RQ1"
        )
    if ledger.get("status") != "frozen":
        raise RosterContractError("authoritative exposure ledger must be frozen")
    if ledger.get("scope") != LEDGER_SCOPE:
        raise RosterContractError(
            "exposure ledger does not attest complete project history"
        )
    if ledger.get("unknown_case_policy") != "reject":
        raise RosterContractError(
            "unknown cases must be rejected, never inferred exposed"
        )
    if ledger.get("unused_policy") != "terminal_embargo":
        raise RosterContractError("unused cases must remain under terminal embargo")
    commit = _require_string(ledger.get("cutoff_git_commit"), field="cutoff_git_commit")
    if not GIT_COMMIT_RE.fullmatch(commit.lower()):
        raise RosterContractError("cutoff_git_commit is not a Git object identifier")
    payload = _exposure_assignment_payload(ledger)
    expected = stable_hash(payload)
    if ledger.get("exposure_assignment_hash") != expected:
        raise RosterContractError(
            "exposure_assignment_hash does not match ledger contents"
        )
    if not payload["exposures"]:
        raise RosterContractError("authoritative exposure ledger is empty")
    lineage = {
        "schema_version": LEDGER_SCHEMA,
        "ledger_file_sha256": _sha256_file(path),
        "exposure_assignment_hash": expected,
        "cutoff_git_commit": commit.lower(),
        "scope": LEDGER_SCOPE,
    }
    return ledger, lineage


def validate_draft_roster(path: Path) -> tuple[dict[str, Any], str]:
    draft = _load_object(path, kind="draft roster")
    _require_exact_keys(
        draft,
        {
            "schema_version",
            "status",
            "seed",
            "partition",
            "exposure_ledger_lineage",
            "assignment_hash",
            "cases",
            "execution_allowed",
            "note",
        },
        kind="draft roster",
    )
    if draft.get("schema_version") != "RQ1RosterV1":
        raise RosterContractError("unsupported draft roster schema")
    expected = {
        "status": "draft_unfrozen",
        "partition": PARTITION,
        "execution_allowed": False,
        "exposure_ledger_lineage": None,
        "assignment_hash": None,
    }
    mismatches = {
        key: (draft.get(key), value)
        for key, value in expected.items()
        if draft.get(key) != value
    }
    if mismatches:
        raise RosterContractError(f"unsafe roster status transition: {mismatches}")
    if draft.get("cases") != []:
        raise RosterContractError(
            "draft roster must be empty before its one-way freeze"
        )
    if not isinstance(draft.get("seed"), int):
        raise RosterContractError("draft roster seed must be an integer")
    return draft, _sha256_file(path)


def validate_private_selection(path: Path, *, seed: int) -> tuple[dict[str, Any], str]:
    selection = _load_object(path, kind="private selection")
    _require_exact_keys(
        selection,
        {
            "schema_version",
            "status",
            "seed",
            "partition",
            "selection_policy",
            "private_case_ids",
            "selection_hash",
        },
        kind="private selection",
    )
    if selection.get("schema_version") != SELECTION_SCHEMA:
        raise RosterContractError(f"private selection must use {SELECTION_SCHEMA}")
    if selection.get("status") != "frozen":
        raise RosterContractError("private selection must be frozen")
    if selection.get("partition") != PARTITION:
        raise RosterContractError(f"private selection partition must be {PARTITION}")
    if selection.get("seed") != seed:
        raise RosterContractError("private selection seed differs from draft roster")
    ids = selection.get("private_case_ids")
    if not isinstance(ids, list) or not ids:
        raise RosterContractError("private selection must contain at least one case")
    if any(not isinstance(item, str) or not item for item in ids):
        raise RosterContractError("private_case_ids must be non-empty strings")
    if len(ids) != len(set(ids)):
        raise RosterContractError("private selection contains duplicate case IDs")
    policy = selection.get("selection_policy")
    if not isinstance(policy, Mapping) or not policy:
        raise RosterContractError("private selection must record a selection_policy")
    if policy.get("outcome_blind") is not True:
        raise RosterContractError("private selection must attest outcome_blind=true")
    _require_string(policy.get("method"), field="selection_policy.method")
    _require_string(
        policy.get("power_analysis_reference"),
        field="selection_policy.power_analysis_reference",
    )
    if selection.get("selection_hash") != stable_hash(
        {
            "schema_version": SELECTION_SCHEMA,
            "seed": seed,
            "partition": PARTITION,
            "private_case_ids": ids,
            "selection_policy": policy,
        }
    ):
        raise RosterContractError("private selection_hash does not match its contents")
    return selection, _sha256_file(path)


def _assignment_payload(
    *,
    seed: int,
    opaque_incident_ids: Sequence[str],
    lineage: Mapping[str, Any],
    partition: str = PARTITION,
) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_ROSTER_SCHEMA,
        "seed": seed,
        "partition": partition,
        "opaque_incident_ids": list(opaque_incident_ids),
        "exposure_assignment_hash": lineage["exposure_assignment_hash"],
    }


def build_frozen_rosters(
    *,
    draft_path: Path,
    ledger_path: Path,
    selection_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build, but do not write, a private/public frozen roster pair."""

    draft, draft_sha256 = validate_draft_roster(draft_path)
    ledger, lineage = validate_exposure_ledger(ledger_path)
    selection, selection_sha256 = validate_private_selection(
        selection_path, seed=int(draft["seed"])
    )
    by_id = {row["private_case_id"]: row for row in ledger["exposures"]}
    private_rows: list[dict[str, Any]] = []
    for case_id in selection["private_case_ids"]:
        exposure = by_id.get(case_id)
        if exposure is None:
            raise RosterContractError(
                "selected case is absent from the authoritative ledger; "
                "unknown does not mean exposed"
            )
        if exposure["exposure_status"] != "exposed":
            raise RosterContractError("selected case is not explicitly exposed")
        if exposure["eligibility_status"] != "eligible":
            raise RosterContractError("selected case is invalid or embargoed")
        if DEVELOPMENT_USE not in exposure["allowed_uses"]:
            raise RosterContractError(
                "selected case is not authorized for RQ1 development"
            )
        private_rows.append(
            {
                "private_case_id": case_id,
                "opaque_incident_id": canonical_opaque_incident_id(case_id),
                "analysis_dataset": exposure["analysis_dataset"],
                "analysis_leakage_group_id": exposure["analysis_leakage_group_id"],
            }
        )
    opaque_ids = [row["opaque_incident_id"] for row in private_rows]
    if len(opaque_ids) != len(set(opaque_ids)):
        raise RosterContractError(
            "canonical opaque-ID collision; widen the shared ID format"
        )
    if any(not OPAQUE_ID_RE.fullmatch(value) for value in opaque_ids):
        raise RosterContractError("generated opaque incident ID is malformed")

    assignment_payload = _assignment_payload(
        seed=int(draft["seed"]),
        opaque_incident_ids=opaque_ids,
        lineage=lineage,
        partition=PARTITION,
    )
    assignment_hash = stable_hash(assignment_payload)
    private_assignment_hash = stable_hash(
        {
            "seed": draft["seed"],
            "partition": PARTITION,
            "cases": private_rows,
            "ledger_assignment_hash": lineage["exposure_assignment_hash"],
            "selection_file_sha256": selection_sha256,
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
    public_roster: dict[str, Any] = {
        "schema_version": PUBLIC_ROSTER_SCHEMA,
        "status": "frozen",
        "seed": draft["seed"],
        "partition": PARTITION,
        "exposure_ledger_lineage": lineage,
        "assignment_hash": assignment_hash,
        "cases": [{"opaque_incident_id": value} for value in opaque_ids],
        "n_cases": len(opaque_ids),
        "status_transition": transition,
        "execution_allowed": True,
        "model_visible": False,
        "note": (
            "Public RQ1 roster: contains only opaque incident IDs. Config, evidence, "
            "smoke, and run-contract gates remain independently binding."
        ),
    }
    private_roster: dict[str, Any] = {
        "schema_version": PRIVATE_ROSTER_SCHEMA,
        "status": "frozen",
        "seed": draft["seed"],
        "partition": PARTITION,
        "exposure_ledger_lineage": lineage,
        "assignment_hash": assignment_hash,
        "private_assignment_hash": private_assignment_hash,
        "selection_file_sha256": selection_sha256,
        "cases": private_rows,
        "n_cases": len(private_rows),
        "status_transition": transition,
        "execution_allowed": False,
        "private": True,
        "note": "Evaluator-only mapping; never attach this roster to model-visible artifacts.",
    }
    validate_frozen_roster_pair(
        public_roster=public_roster,
        private_roster=private_roster,
        ledger=ledger,
        lineage=lineage,
    )
    return private_roster, public_roster


def validate_frozen_roster_pair(
    *,
    public_roster: Mapping[str, Any],
    private_roster: Mapping[str, Any],
    ledger: Mapping[str, Any],
    lineage: Mapping[str, Any],
) -> None:
    """Validate consistency, exposure eligibility, and public/private isolation."""

    if public_roster.get("schema_version") != PUBLIC_ROSTER_SCHEMA:
        raise RosterContractError("unsupported public roster schema")
    if private_roster.get("schema_version") != PRIVATE_ROSTER_SCHEMA:
        raise RosterContractError("unsupported private roster schema")
    _require_exact_keys(
        public_roster,
        {
            "schema_version",
            "status",
            "seed",
            "partition",
            "exposure_ledger_lineage",
            "assignment_hash",
            "cases",
            "n_cases",
            "status_transition",
            "execution_allowed",
            "model_visible",
            "note",
        },
        kind="public roster",
    )
    _require_exact_keys(
        private_roster,
        {
            "schema_version",
            "status",
            "seed",
            "partition",
            "exposure_ledger_lineage",
            "assignment_hash",
            "private_assignment_hash",
            "selection_file_sha256",
            "cases",
            "n_cases",
            "status_transition",
            "execution_allowed",
            "private",
            "note",
        },
        kind="private roster",
    )
    partition = public_roster.get("partition")
    if partition not in {PARTITION, SMOKE_PARTITION}:
        raise RosterContractError("public roster has an unsupported partition")
    if private_roster.get("partition") != partition:
        raise RosterContractError("private/public roster partitions differ")
    required_use = DEVELOPMENT_USE if partition == PARTITION else SMOKE_USE
    for name, roster in (("public", public_roster), ("private", private_roster)):
        if roster.get("status") != "frozen":
            raise RosterContractError(f"{name} roster is not frozen")
        if roster.get("partition") != partition:
            raise RosterContractError(f"{name} roster has the wrong partition")
        if roster.get("exposure_ledger_lineage") != lineage:
            raise RosterContractError(f"{name} roster exposure lineage mismatch")
        transition = roster.get("status_transition")
        if not isinstance(transition, Mapping):
            raise RosterContractError(f"{name} roster lacks a status transition")
        _require_exact_keys(
            transition,
            {"from", "to", "draft_sha256", "transition_id"},
            kind=f"{name} roster status_transition",
        )
        if (
            transition.get("from") != "draft_unfrozen"
            or transition.get("to") != "frozen"
        ):
            raise RosterContractError(f"{name} roster has an invalid status transition")
        if not SHA256_RE.fullmatch(str(transition.get("draft_sha256") or "")):
            raise RosterContractError(f"{name} roster has an invalid draft hash")
        if not SHA256_RE.fullmatch(str(transition.get("transition_id") or "")):
            raise RosterContractError(f"{name} roster has an invalid transition ID")
    if public_roster.get("seed") != private_roster.get("seed"):
        raise RosterContractError("private/public roster seeds differ")
    if public_roster.get("status_transition") != private_roster.get(
        "status_transition"
    ):
        raise RosterContractError("private/public status transitions differ")
    if public_roster.get("execution_allowed") is not True:
        raise RosterContractError("public roster must explicitly permit roster use")
    if private_roster.get("execution_allowed") is not False:
        raise RosterContractError("private roster must never be passed to a runner")
    if private_roster.get("private") is not True:
        raise RosterContractError("private roster is not marked private")

    public_cases = public_roster.get("cases")
    private_cases = private_roster.get("cases")
    if not isinstance(public_cases, list) or not public_cases:
        raise RosterContractError("public roster cases must be non-empty")
    if not isinstance(private_cases, list) or len(private_cases) != len(public_cases):
        raise RosterContractError("private/public roster sizes differ")
    if public_roster.get("n_cases") != len(public_cases):
        raise RosterContractError("public roster n_cases mismatch")
    if private_roster.get("n_cases") != len(private_cases):
        raise RosterContractError("private roster n_cases mismatch")

    allowed = {row["private_case_id"]: row for row in ledger["exposures"]}
    public_ids: list[str] = []
    private_ids: list[str] = []
    raw_markers: list[str] = []
    for index, (public, private) in enumerate(zip(public_cases, private_cases)):
        if not isinstance(public, Mapping) or set(public) != {"opaque_incident_id"}:
            raise RosterContractError(
                f"public cases[{index}] may contain only opaque_incident_id"
            )
        if not isinstance(private, Mapping) or set(private) != {
            "private_case_id",
            "opaque_incident_id",
            "analysis_dataset",
            "analysis_leakage_group_id",
        }:
            raise RosterContractError(f"private cases[{index}] has unexpected fields")
        opaque = _require_string(
            public.get("opaque_incident_id"),
            field=f"public cases[{index}].opaque_incident_id",
        )
        if not OPAQUE_ID_RE.fullmatch(opaque):
            raise RosterContractError(f"public cases[{index}] has malformed opaque ID")
        if private.get("opaque_incident_id") != opaque:
            raise RosterContractError("private/public opaque-ID order mismatch")
        raw = _require_string(
            private.get("private_case_id"),
            field=f"private cases[{index}].private_case_id",
        )
        entry = allowed.get(raw)
        if entry is None:
            raise RosterContractError(
                "private roster contains a case unknown to the ledger"
            )
        if (
            entry["eligibility_status"] != "eligible"
            or required_use not in entry["allowed_uses"]
        ):
            raise RosterContractError("private roster contains an unauthorized case")
        if private.get("analysis_dataset") != entry["analysis_dataset"]:
            raise RosterContractError(
                "private roster analysis_dataset differs from ledger"
            )
        if (
            private.get("analysis_leakage_group_id")
            != entry["analysis_leakage_group_id"]
        ):
            raise RosterContractError(
                "private roster analysis_leakage_group_id differs from ledger"
            )
        if canonical_opaque_incident_id(raw) != opaque:
            raise RosterContractError(
                "opaque incident ID differs from the canonical renderer mapping"
            )
        public_ids.append(opaque)
        private_ids.append(raw)
        raw_markers.extend((raw, str(entry["analysis_dataset"])))
        if entry["analysis_leakage_group_id"] is not None:
            raw_markers.append(str(entry["analysis_leakage_group_id"]))
    if len(public_ids) != len(set(public_ids)) or len(private_ids) != len(
        set(private_ids)
    ):
        raise RosterContractError("roster contains duplicate incident IDs")

    expected_assignment = stable_hash(
        _assignment_payload(
            seed=int(public_roster["seed"]),
            opaque_incident_ids=public_ids,
            lineage=lineage,
            partition=str(partition),
        )
    )
    if public_roster.get("assignment_hash") != expected_assignment:
        raise RosterContractError("public assignment_hash mismatch")
    if private_roster.get("assignment_hash") != expected_assignment:
        raise RosterContractError("private assignment_hash mismatch")
    selection_sha256 = str(private_roster.get("selection_file_sha256") or "")
    if not SHA256_RE.fullmatch(selection_sha256):
        raise RosterContractError("private selection_file_sha256 is malformed")
    expected_private_assignment = stable_hash(
        {
            "seed": private_roster["seed"],
            "partition": partition,
            "cases": list(private_cases),
            "ledger_assignment_hash": lineage["exposure_assignment_hash"],
            "selection_file_sha256": selection_sha256,
        }
    )
    if private_roster.get("private_assignment_hash") != expected_private_assignment:
        raise RosterContractError("private_assignment_hash mismatch")
    transition = public_roster["status_transition"]
    expected_transition_id = stable_hash(
        {
            "draft_sha256": transition["draft_sha256"],
            "assignment_hash": expected_assignment,
            "ledger_file_sha256": lineage["ledger_file_sha256"],
        }
    )
    if transition.get("transition_id") != expected_transition_id:
        raise RosterContractError(
            "status transition ID does not bind the frozen assignment"
        )
    assert_label_blind(
        public_roster,
        private_markers=raw_markers,
        context="public RQ1 roster",
    )


def validate_frozen_roster_files(
    *,
    public_path: Path,
    private_path: Path,
    ledger_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ledger, lineage = validate_exposure_ledger(ledger_path)
    public_roster = _load_object(public_path, kind="public roster")
    private_roster = _load_object(private_path, kind="private roster")
    validate_frozen_roster_pair(
        public_roster=public_roster,
        private_roster=private_roster,
        ledger=ledger,
        lineage=lineage,
    )
    return private_roster, public_roster


def write_frozen_roster_pair(
    *,
    private_path: Path,
    public_path: Path,
    private_roster: Mapping[str, Any],
    public_roster: Mapping[str, Any],
) -> None:
    """Create both rosters without overwriting either destination."""

    if private_path.resolve() == public_path.resolve():
        raise RosterContractError("private and public roster paths must differ")
    if private_path.exists() or public_path.exists():
        raise RosterContractError("refusing to overwrite an existing roster")
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    blobs = {
        private_path: (canonical_json(private_roster) + "\n").encode("utf-8"),
        public_path: (canonical_json(public_roster) + "\n").encode("utf-8"),
    }
    temporary: dict[Path, Path] = {}
    linked: list[Path] = []
    try:
        for destination, blob in blobs.items():
            fd, raw_temp = tempfile.mkstemp(
                prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
            )
            temp_path = Path(raw_temp)
            temporary[destination] = temp_path
            try:
                os.write(fd, blob)
                os.fsync(fd)
            finally:
                os.close(fd)
            os.chmod(temp_path, 0o600 if destination == private_path else 0o644)
        for destination, temp_path in temporary.items():
            os.link(temp_path, destination)
            linked.append(destination)
    except Exception:
        for destination in linked:
            destination.unlink(missing_ok=True)
        raise
    finally:
        for temp_path in temporary.values():
            temp_path.unlink(missing_ok=True)

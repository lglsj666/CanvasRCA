from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest
from rq1lib.contracts import stable_hash
from rq1lib.roster import (
    DEVELOPMENT_USE,
    LEDGER_SCHEMA,
    LEDGER_SCOPE,
    PARTITION,
    SELECTION_SCHEMA,
    RosterContractError,
    _exposure_assignment_payload,
    build_frozen_rosters,
    validate_exposure_ledger,
    validate_frozen_roster_files,
    validate_frozen_roster_pair,
    write_frozen_roster_pair,
)
from vlmrca.render.dashboard import opaque_incident_id

ROOT = Path(__file__).resolve().parents[4]
SCHEMAS = ROOT / "RQs/RQ1/configs/schemas"
LEGACY_LEDGER = ROOT / "RQs/RQ0/configs/exposure_ledger.json"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _fixture_files(tmp_path: Path) -> dict[str, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    draft = {
        "schema_version": "RQ1RosterV1",
        "status": "draft_unfrozen",
        "seed": 42,
        "partition": PARTITION,
        "exposure_ledger_lineage": None,
        "assignment_hash": None,
        "cases": [],
        "execution_allowed": False,
        "note": "test draft",
    }
    exposures = [
        {
            "private_case_id": "private-case-alpha",
            "analysis_dataset": "private-dataset-a",
            "analysis_leakage_group_id": "private-group-a",
            "exposure_status": "exposed",
            "eligibility_status": "eligible",
            "allowed_uses": [DEVELOPMENT_USE],
            "sources": ["historical-run-contract-a"],
        },
        {
            "private_case_id": "private-case-beta",
            "analysis_dataset": "private-dataset-b",
            "analysis_leakage_group_id": None,
            "exposure_status": "exposed",
            "eligibility_status": "eligible",
            "allowed_uses": [DEVELOPMENT_USE, "power_analysis"],
            "sources": ["historical-render-b"],
        },
        {
            "private_case_id": "private-case-embargoed",
            "analysis_dataset": "private-dataset-c",
            "analysis_leakage_group_id": "private-group-c",
            "exposure_status": "exposed",
            "eligibility_status": "embargoed",
            "allowed_uses": [],
            "sources": ["terminal-embargo-record"],
        },
    ]
    ledger = {
        "schema_version": LEDGER_SCHEMA,
        "status": "frozen",
        "scope": LEDGER_SCOPE,
        "cutoff_git_commit": "abcdef1234567890",
        "unknown_case_policy": "reject",
        "unused_policy": "terminal_embargo",
        "exposure_assignment_hash": "pending",
        "exposures": exposures,
    }
    ledger["exposure_assignment_hash"] = stable_hash(
        _exposure_assignment_payload(ledger)
    )
    policy = {
        "method": "preapproved exposed-only fixture",
        "outcome_blind": True,
        "power_analysis_reference": "fixture-power-v1",
    }
    selected = ["private-case-beta", "private-case-alpha"]
    selection = {
        "schema_version": SELECTION_SCHEMA,
        "status": "frozen",
        "seed": 42,
        "partition": PARTITION,
        "selection_policy": policy,
        "private_case_ids": selected,
        "selection_hash": stable_hash(
            {
                "schema_version": SELECTION_SCHEMA,
                "seed": 42,
                "partition": PARTITION,
                "private_case_ids": selected,
                "selection_policy": policy,
            }
        ),
    }
    paths = {
        "draft": tmp_path / "draft.json",
        "ledger": tmp_path / "private-ledger.json",
        "selection": tmp_path / "private-selection.json",
        "private": tmp_path / "private-roster.json",
        "public": tmp_path / "public-roster.json",
    }
    _write_json(paths["draft"], draft)
    _write_json(paths["ledger"], ledger)
    _write_json(paths["selection"], selection)
    return paths


def _build(paths: dict[str, Path]) -> tuple[dict, dict]:
    return build_frozen_rosters(
        draft_path=paths["draft"],
        ledger_path=paths["ledger"],
        selection_path=paths["selection"],
    )


def test_freeze_produces_private_mapping_and_opaque_public_roster(tmp_path: Path):
    paths = _fixture_files(tmp_path)
    private, public = _build(paths)

    public_blob = json.dumps(public, sort_keys=True)
    assert "private-case" not in public_blob
    assert "private-dataset" not in public_blob
    assert all(set(row) == {"opaque_incident_id"} for row in public["cases"])
    assert public["status_transition"]["from"] == "draft_unfrozen"
    assert public["status_transition"]["to"] == "frozen"
    assert private["execution_allowed"] is False
    assert [row["private_case_id"] for row in private["cases"]] == [
        "private-case-beta",
        "private-case-alpha",
    ]

    public_schema = json.loads((SCHEMAS / "public_roster_v1.schema.json").read_text())
    private_schema = json.loads((SCHEMAS / "private_roster_v1.schema.json").read_text())
    jsonschema.validate(public, public_schema)
    jsonschema.validate(private, private_schema)


def test_write_is_exclusive_and_permissions_separate_private_from_public(
    tmp_path: Path,
):
    paths = _fixture_files(tmp_path)
    private, public = _build(paths)
    write_frozen_roster_pair(
        private_path=paths["private"],
        public_path=paths["public"],
        private_roster=private,
        public_roster=public,
    )
    assert paths["private"].stat().st_mode & 0o077 == 0
    assert paths["public"].stat().st_mode & 0o444 == 0o444
    validate_frozen_roster_files(
        public_path=paths["public"],
        private_path=paths["private"],
        ledger_path=paths["ledger"],
    )
    with pytest.raises(RosterContractError, match="overwrite"):
        write_frozen_roster_pair(
            private_path=paths["private"],
            public_path=paths["public"],
            private_roster=private,
            public_roster=public,
        )


def test_legacy_rq0_ledger_cannot_unlock_rq1():
    with pytest.raises(RosterContractError, match="authoritative exposure ledger"):
        validate_exposure_ledger(LEGACY_LEDGER)


@pytest.mark.parametrize(
    ("selected_id", "message"),
    [
        ("unknown-private-case", "unknown does not mean exposed"),
        ("private-case-embargoed", "invalid or embargoed"),
    ],
)
def test_unknown_or_embargoed_cases_fail_closed(
    tmp_path: Path, selected_id: str, message: str
):
    paths = _fixture_files(tmp_path)
    selection = json.loads(paths["selection"].read_text())
    selection["private_case_ids"] = [selected_id]
    selection["selection_hash"] = stable_hash(
        {
            "schema_version": SELECTION_SCHEMA,
            "seed": 42,
            "partition": PARTITION,
            "private_case_ids": [selected_id],
            "selection_policy": selection["selection_policy"],
        }
    )
    _write_json(paths["selection"], selection)
    with pytest.raises(RosterContractError, match=message):
        _build(paths)


def test_exposed_but_unauthorized_case_is_not_implicitly_development(tmp_path: Path):
    paths = _fixture_files(tmp_path)
    ledger = json.loads(paths["ledger"].read_text())
    ledger["exposures"][0]["allowed_uses"] = ["historical_analysis_only"]
    ledger["exposure_assignment_hash"] = stable_hash(
        _exposure_assignment_payload(ledger)
    )
    _write_json(paths["ledger"], ledger)
    selection = json.loads(paths["selection"].read_text())
    selection["private_case_ids"] = ["private-case-alpha"]
    selection["selection_hash"] = stable_hash(
        {
            "schema_version": SELECTION_SCHEMA,
            "seed": 42,
            "partition": PARTITION,
            "private_case_ids": ["private-case-alpha"],
            "selection_policy": selection["selection_policy"],
        }
    )
    _write_json(paths["selection"], selection)
    with pytest.raises(RosterContractError, match="not authorized"):
        _build(paths)


def test_tampering_assignment_or_public_mapping_is_detected(tmp_path: Path):
    paths = _fixture_files(tmp_path)
    private, public = _build(paths)
    _, lineage = validate_exposure_ledger(paths["ledger"])
    ledger = json.loads(paths["ledger"].read_text())

    bad_hash = copy.deepcopy(public)
    bad_hash["assignment_hash"] = "0" * 64
    with pytest.raises(RosterContractError, match="assignment_hash"):
        validate_frozen_roster_pair(
            public_roster=bad_hash,
            private_roster=private,
            ledger=ledger,
            lineage=lineage,
        )

    leaked = copy.deepcopy(public)
    leaked["cases"][0]["private_case_id"] = "private-case-beta"
    with pytest.raises(RosterContractError, match="only opaque_incident_id"):
        validate_frozen_roster_pair(
            public_roster=leaked,
            private_roster=private,
            ledger=ledger,
            lineage=lineage,
        )

    bad_private = copy.deepcopy(private)
    bad_private["private_assignment_hash"] = "0" * 64
    with pytest.raises(RosterContractError, match="private_assignment_hash"):
        validate_frozen_roster_pair(
            public_roster=public,
            private_roster=bad_private,
            ledger=ledger,
            lineage=lineage,
        )


def test_opaque_ids_match_renderer_and_analysis_fields_stay_private(tmp_path: Path):
    paths = _fixture_files(tmp_path)
    private, public = _build(paths)
    for private_row, public_row in zip(private["cases"], public["cases"]):
        assert public_row["opaque_incident_id"] == opaque_incident_id(
            private_row["private_case_id"]
        )
        assert set(public_row) == {"opaque_incident_id"}
    public_blob = json.dumps(public, sort_keys=True)
    assert "analysis_dataset" not in public_blob
    assert "analysis_leakage_group_id" not in public_blob
    assert private["cases"][0]["analysis_dataset"] == "private-dataset-b"
    assert private["cases"][0]["analysis_leakage_group_id"] is None


def test_ledger_hash_and_draft_status_transition_are_binding(tmp_path: Path):
    paths = _fixture_files(tmp_path)
    ledger = json.loads(paths["ledger"].read_text())
    ledger["exposures"][0]["sources"].append("late-exposure")
    _write_json(paths["ledger"], ledger)
    with pytest.raises(RosterContractError, match="exposure_assignment_hash"):
        _build(paths)

    paths = _fixture_files(tmp_path / "second")
    draft = json.loads(paths["draft"].read_text())
    draft["status"] = "frozen"
    _write_json(paths["draft"], draft)
    with pytest.raises(RosterContractError, match="status transition"):
        _build(paths)

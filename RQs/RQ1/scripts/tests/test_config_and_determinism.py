from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from rq1lib.artifacts import prepare_store
from rq1lib.contracts import ContractError
from rq1lib.evidence import build_evidence_store_from_ceb, synthetic_ceb
from rq1lib.settings import (
    assert_runner_may_execute,
    assert_static_config,
    load_yaml_config,
    validate_schema_files,
)
from run_rq1_visops import _assert_execution_store_is_qualified

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / "RQs/RQ1/configs/rq1_visops_v1.yaml"


def test_config_and_json_schemas_are_valid_and_execution_is_locked():
    config = load_yaml_config(CONFIG)
    assert_static_config(config)
    schemas = validate_schema_files(config, ROOT)
    store = build_evidence_store_from_ceb(synthetic_ceb())
    item = prepare_store(store)[0]
    jsonschema.validate(item.task.query.public_dict(), schemas["query_spec_schema"])
    jsonschema.validate(item.paired_audit, schemas["paired_view_schema"])
    jsonschema.validate(
        item.task.private_answer_key.private_dict(),
        schemas["private_answer_key_schema"],
    )
    roster_path = ROOT / config["data"]["roster"]
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    with pytest.raises(ContractError):
        assert_runner_may_execute(config, roster, explicit_execute=True)


def test_full_task_text_png_and_audit_are_deterministic():
    left = prepare_store(build_evidence_store_from_ceb(synthetic_ceb()))
    right = prepare_store(build_evidence_store_from_ceb(synthetic_ceb()))
    assert len(left) == len(right)
    for a, b in zip(left, right):
        assert a.task.public_contract() == b.task.public_contract()
        assert a.text_view.artifact_bytes == b.text_view.artifact_bytes
        assert a.visual_view.artifact_bytes == b.visual_view.artifact_bytes
        assert a.paired_audit == b.paired_audit


def test_qualification_only_store_cannot_be_promoted_by_flipping_execution_flag():
    config = load_yaml_config(CONFIG)
    qualification_call = {"evidence_store_schema": "CanonicalEvidenceStoreV1"}
    with pytest.raises(ContractError, match="qualification-only"):
        _assert_execution_store_is_qualified([qualification_call], config)

    qualified_call = {
        "evidence_store_schema": config["contracts"][
            "canonical_source_required_for_execution"
        ]
    }
    _assert_execution_store_is_qualified([qualified_call], config)

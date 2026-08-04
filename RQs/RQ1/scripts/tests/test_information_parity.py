from __future__ import annotations

import dataclasses

import pytest
from rq1lib.artifacts import prepare_store
from rq1lib.contracts import ContractError
from rq1lib.evidence import build_evidence_store_from_ceb, synthetic_ceb
from rq1lib.prompts import (
    ANSWER_TYPE_BY_OPERATION,
    audit_paired_views,
    structured_answer_contract,
)


def _prepared():
    return prepare_store(build_evidence_store_from_ceb(synthetic_ceb()))


def test_all_arms_reconstruct_the_exact_same_fact_inventory():
    for item in _prepared():
        expected = set(item.task.query.fact_ids)
        assert set(item.paired_audit["arms"]["text"]["fact_ids"]) == expected
        assert set(item.paired_audit["arms"]["visual"]["fact_ids"]) == expected
        assert set(item.paired_audit["arms"]["bounded_hybrid"]["fact_ids"]) == expected
        assert set(item.text_view.location_map) == expected
        assert set(item.visual_view.location_map) == expected


def test_hybrid_is_exact_A_plus_B_without_rewrite_or_deduplication():
    for item in _prepared():
        assert item.prompts.hybrid_a_plus_b.parts == (
            item.prompts.visual_a.parts + item.prompts.text_b.parts
        )
        assert item.paired_audit["prompt_composition"]["order"] == "A_PLUS_B"


def test_every_operation_has_a_strict_public_answer_shape():
    prepared = _prepared()
    seen: set[str] = set()
    for item in prepared:
        operation = item.task.query.operation
        contract = structured_answer_contract(operation)
        seen.add(str(contract["answer_type"]))
        schema = contract["response_format"]["json_schema"]["schema"]
        assert schema["type"] == "object"
        assert schema["required"] == ["answer"]
        assert schema["additionalProperties"] is False
        assert set(schema["properties"]) == {"answer"}
        assert contract == item.prompts.answer_contract
        assert "answer" not in contract
    assert {item.task.query.operation for item in prepared} <= set(
        ANSWER_TYPE_BY_OPERATION
    )
    assert seen == {
        "number",
        "sorted_string_set",
        "ordered_path",
        "directed_edge",
    }


def test_answer_shapes_are_type_specific_without_revealing_cardinality():
    set_schema = structured_answer_contract("earliest_onset")["response_format"][
        "json_schema"
    ]["schema"]["properties"]["answer"]
    path_schema = structured_answer_contract("multi_hop_path")["response_format"][
        "json_schema"
    ]["schema"]["properties"]["answer"]
    edge_schema = structured_answer_contract("directed_edge")["response_format"][
        "json_schema"
    ]["schema"]["properties"]["answer"]
    assert set_schema == {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 1,
    }
    assert path_schema == {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 2,
    }
    assert edge_schema["required"] == ["caller", "callee"]
    assert edge_schema["additionalProperties"] is False


def test_text_prompt_excludes_audit_only_provenance_lineage():
    for item in _prepared():
        payload = item.text_view.artifact_bytes
        assert b'"derived_from"' not in payload
        assert b'"provenance_hash"' not in payload
        assert b'"source_pointer"' not in payload
        assert b'"fact_id"' in payload


def test_tampered_model_visible_fact_fails_closed():
    item = _prepared()[0]
    blob = item.text_view.artifact_bytes.decode("utf-8")
    tampered = blob.replace('"value":', '"value":"tampered","discarded":', 1)
    text_view = dataclasses.replace(
        item.text_view, artifact_bytes=tampered.encode("utf-8")
    )
    with pytest.raises((ContractError, ValueError)):
        audit_paired_views(
            item.task,
            text_view=text_view,
            visual_view=item.visual_view,
            prompts=item.prompts,
        )


def test_multi_hop_path_is_an_explicit_fact_in_every_arm():
    item = next(
        value for value in _prepared() if value.task.query.operation == "multi_hop_path"
    )
    path_ids = {
        fact.fact_id for fact in item.task.facts if fact.field == "multi_hop_path"
    }
    assert path_ids
    for arm in ("text", "visual", "bounded_hybrid"):
        assert path_ids <= set(item.paired_audit["arms"][arm]["fact_ids"])

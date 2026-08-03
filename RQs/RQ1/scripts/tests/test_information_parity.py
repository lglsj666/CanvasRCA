from __future__ import annotations

import dataclasses

import pytest
from rq1lib.artifacts import prepare_store
from rq1lib.contracts import ContractError
from rq1lib.evidence import build_evidence_store_from_ceb, synthetic_ceb
from rq1lib.prompts import audit_paired_views


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

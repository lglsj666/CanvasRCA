from __future__ import annotations

import dataclasses

import pytest
from rq1lib.contracts import ContractError, validate_evidence_ledger
from rq1lib.evidence import build_evidence_store_from_ceb, synthetic_ceb
from rq1lib.visops import build_visops_tasks


def test_query_is_public_and_answer_key_is_structurally_private():
    store = build_evidence_store_from_ceb(synthetic_ceb())
    task = build_visops_tasks(store)[0]
    public = task.public_contract()
    assert "private_answer_key" not in public
    assert "answer" not in public
    assert task.private_answer_key.query_hash == task.query.query_hash
    assert set(task.private_answer_key.supporting_fact_ids) <= set(task.query.fact_ids)


def test_fact_id_is_semantic_but_inventory_changes_with_value():
    store = build_evidence_store_from_ceb(synthetic_ceb())
    original = store.facts[0]
    changed = dataclasses.replace(original, value={"index": 0, "service": "svc-z"})
    assert changed.fact_id == original.fact_id
    from rq1lib.contracts import fact_inventory_hash

    assert fact_inventory_hash((changed,)) != fact_inventory_hash((original,))


def test_ledger_rejects_unknown_fact_and_candidate():
    store = build_evidence_store_from_ceb(synthetic_ceb())
    task = build_visops_tasks(store)[0]
    first = task.query.fact_ids[0]
    ledger = {
        "schema_version": "EvidenceLedgerV2",
        "selected_fact_ids": [first],
        "observations": [
            {
                "claim": "observation",
                "fact_ids": ["F000000000000"],
                "source_representation": "visual",
                "confidence": 0.5,
            }
        ],
        "temporal_relations": [],
        "directed_edges": [],
        "candidate_support": {"not-a-candidate": [first]},
        "candidate_opposition": {},
        "conflicts": [],
        "missing_evidence": [],
    }
    with pytest.raises(ContractError):
        validate_evidence_ledger(
            ledger,
            allowed_fact_ids=task.query.fact_ids,
            candidates=["svc-a"],
        )

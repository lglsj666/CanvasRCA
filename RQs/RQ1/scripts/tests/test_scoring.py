from __future__ import annotations

import pytest
from rq1lib.contracts import ContractError
from rq1lib.scoring import (
    normalize_panel_onset_ledger,
    parse_visops_response,
    score_visops_answer,
    select_earliest_panels,
)
from rq1lib.two_stage import build_stage2_prompt, invalid_stage1_ledger


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('{"answer": 3.5}', 3.5),
        ('```json\n{"answer": ["svc-a", "svc-b"]}\n```', ["svc-a", "svc-b"]),
        ('result follows: {"answer": "svc-a -> svc-b"}', "svc-a -> svc-b"),
    ],
)
def test_strict_answer_parser_accepts_one_answer_object(raw, expected):
    answer, ok = parse_visops_response(raw)
    assert ok is True
    assert answer == expected


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        '{"answer": 1, "reason": "extra model field"}',
        '[{"answer": 1}]',
        "",
    ],
)
def test_strict_answer_parser_rejects_invalid_schema(raw):
    answer, ok = parse_visops_response(raw)
    assert ok is False
    assert answer is None


@pytest.mark.parametrize(
    ("predicted", "key", "correct"),
    [
        (4.0, {"answer": 4.0, "answer_type": "number"}, True),
        (
            ["svc-b", "svc-a"],
            {"answer": ["svc-a", "svc-b"], "answer_type": "sorted_string_set"},
            True,
        ),
        (
            "svc-a -> svc-b -> svc-c",
            {"answer": ["svc-a", "svc-b", "svc-c"], "answer_type": "ordered_path"},
            True,
        ),
        (
            {"caller": "svc-a", "callee": "svc-b"},
            {
                "answer": {"caller": "svc-a", "callee": "svc-b"},
                "answer_type": "directed_edge",
            },
            True,
        ),
        (
            "svc-b -> svc-a",
            {
                "answer": {"caller": "svc-a", "callee": "svc-b"},
                "answer_type": "directed_edge",
            },
            False,
        ),
    ],
)
def test_private_evaluator_is_deterministic(predicted, key, correct):
    result = score_visops_answer(predicted, key)
    assert result["correct"] is correct
    assert result["score"] == float(correct)


def _ledger():
    return {
        "panels": [
            {
                "panel_id": f"P{index:02d}",
                "onset": 4 if index in {2, 7} else None,
                "support_bins": [4, 5] if index in {2, 7} else [],
                "sign": "positive" if index in {2, 7} else None,
            }
            for index in range(1, 13)
        ]
    }


def test_panel_ledger_validation_selection_and_stage2_evidence_boundary():
    ledger = _ledger()
    normalized = normalize_panel_onset_ledger(ledger)
    assert len(normalized) == 12
    assert select_earliest_panels(ledger) == ["P02", "P07"]
    stage2 = build_stage2_prompt(ledger)
    assert stage2["prompt_contract"]["original_evidence_access"] is False
    assert stage2["prompt_contract"]["ledger_status"] == "valid"
    assert len(stage2["parts"]) == 1
    assert stage2["parts"][0]["type"] == "text"
    assert "PERSISTED_STAGE1_LEDGER" in stage2["parts"][0]["text"]

    reversed_ledger = {"panels": list(reversed(ledger["panels"]))}
    with pytest.raises(ContractError, match="natural numeric order"):
        normalize_panel_onset_ledger(reversed_ledger)


def test_compact_panel_ledger_expands_to_the_full_persisted_schema():
    compact = {
        "panels": [
            f"M{index}:positive@4" if index in {2, 7} else f"M{index}:null"
            for index in range(1, 13)
        ]
    }
    expanded = normalize_panel_onset_ledger(compact)
    assert expanded[1] == {
        "panel_id": "M2",
        "onset": 4,
        "support_bins": [4, 5],
        "sign": "positive",
    }
    assert expanded[0] == {
        "panel_id": "M1",
        "onset": None,
        "support_bins": [],
        "sign": None,
    }
    assert select_earliest_panels(compact) == ["M2", "M7"]

    malformed = {"panels": [*compact["panels"][:-1], "M12:positive@15"]}
    with pytest.raises(ContractError, match="malformed"):
        normalize_panel_onset_ledger(malformed)


def test_invalid_stage1_marker_preserves_stage2_call_without_evidence():
    marker = invalid_stage1_ledger(response_sha256="a" * 64, reason="parse_failure")
    stage2 = build_stage2_prompt(marker)
    assert stage2["prompt_contract"]["ledger_status"] == "invalid"
    assert "invalid_stage1_ledger" in stage2["parts"][0]["text"]
    assert "__NO_VALID_SELECTION__" in stage2["system"]

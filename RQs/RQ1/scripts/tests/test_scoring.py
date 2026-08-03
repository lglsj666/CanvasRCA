from __future__ import annotations

import pytest
from rq1lib.scoring import parse_visops_response, score_visops_answer


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

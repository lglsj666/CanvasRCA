"""Deterministic evaluator for private RCA-VisOps answer keys."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from typing import Any

from .contracts import ContractError

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def parse_visops_response(text: str) -> tuple[Any, bool]:
    """Parse only the public ``{"answer": ...}`` result object."""

    stripped = str(text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        decoded = json.loads(stripped)
    except json.JSONDecodeError:
        decoded = None
    else:
        if isinstance(decoded, dict) and set(decoded) == {"answer"}:
            return decoded["answer"], True
        return None, False

    candidates: list[str] = []
    match = _JSON_OBJECT.search(stripped)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and set(payload) == {"answer"}:
            return payload["answer"], True
    return None, False


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value.strip()}
    if isinstance(value, list):
        return {str(item).strip() for item in value}
    raise ContractError("set answer must be a string or list")


def _path(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value]
    if isinstance(value, str):
        return [
            item.strip() for item in re.split(r"\s*(?:->|→)\s*", value) if item.strip()
        ]
    raise ContractError("path answer must be a list or arrow-separated string")


def _edge(value: Any) -> dict[str, str]:
    if isinstance(value, Mapping) and {"caller", "callee"} <= set(value):
        return {
            "caller": str(value["caller"]).strip(),
            "callee": str(value["callee"]).strip(),
        }
    path = _path(value)
    if len(path) == 2:
        return {"caller": path[0], "callee": path[1]}
    raise ContractError("directed-edge answer must contain exactly caller and callee")


def score_visops_answer(
    predicted: Any,
    private_answer_key: Mapping[str, Any],
    *,
    numeric_abs_tolerance: float = 1e-6,
) -> dict[str, Any]:
    expected = private_answer_key.get("answer")
    answer_type = str(private_answer_key.get("answer_type") or "")
    try:
        if answer_type == "number":
            correct = math.isclose(
                float(predicted),
                float(expected),
                rel_tol=0.0,
                abs_tol=numeric_abs_tolerance,
            )
        elif answer_type == "sorted_string_set":
            correct = _string_set(predicted) == _string_set(expected)
        elif answer_type == "ordered_path":
            correct = _path(predicted) == _path(expected)
        elif answer_type == "directed_edge":
            correct = _edge(predicted) == _edge(expected)
        else:
            raise ContractError(f"unknown VisOps answer type {answer_type!r}")
    except (ContractError, TypeError, ValueError):
        correct = False
    return {
        "correct": bool(correct),
        "score": float(bool(correct)),
        "answer_type": answer_type,
    }

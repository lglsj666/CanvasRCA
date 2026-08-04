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


def _natural_panel_key(value: str) -> tuple[str, int, str]:
    match = re.fullmatch(r"([^0-9]*)([0-9]+)(.*)", value)
    if match is None:
        return (value, -1, "")
    return (match.group(1), int(match.group(2)), match.group(3))


def normalize_panel_onset_ledger(value: Any) -> list[dict[str, Any]]:
    """Validate and normalize one complete natural-order 12-panel ledger."""

    if not isinstance(value, Mapping) or set(value) != {"panels"}:
        raise ContractError("panel onset ledger must contain only panels")
    panels = value["panels"]
    if not isinstance(panels, list) or len(panels) != 12:
        raise ContractError("panel onset ledger must contain exactly 12 panels")
    if all(isinstance(row, str) for row in panels):
        expanded: list[dict[str, Any]] = []
        for entry in panels:
            match = re.fullmatch(
                r"([^:]+):(null|(positive|negative)@([0-9]|1[0-4]))", entry
            )
            if match is None:
                raise ContractError("compact panel onset entry is malformed")
            panel_id, encoded, sign, onset_text = match.groups()
            if encoded == "null":
                expanded.append(
                    {
                        "panel_id": panel_id,
                        "onset": None,
                        "support_bins": [],
                        "sign": None,
                    }
                )
            else:
                onset = int(onset_text)
                expanded.append(
                    {
                        "panel_id": panel_id,
                        "onset": onset,
                        "support_bins": [onset, onset + 1],
                        "sign": sign,
                    }
                )
        panels = expanded
    elif any(isinstance(row, str) for row in panels):
        raise ContractError("panel onset ledger mixes compact and expanded entries")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in panels:
        required = {"panel_id", "onset", "support_bins", "sign"}
        if not isinstance(row, Mapping) or set(row) != required:
            raise ContractError("panel onset entry has unexpected fields")
        panel_id = str(row["panel_id"]).strip()
        if not panel_id or panel_id in seen:
            raise ContractError("panel onset ledger has blank or duplicate panel ID")
        seen.add(panel_id)
        onset = row["onset"]
        support = row["support_bins"]
        sign = row["sign"]
        if onset is None:
            if support != [] or sign is not None:
                raise ContractError("null onset requires empty support and null sign")
        else:
            if isinstance(onset, bool) or not isinstance(onset, int):
                raise ContractError("panel onset must be an integer or null")
            if onset < 0 or onset > 14:
                raise ContractError("panel onset is outside the 16-bin range")
            if support != [onset, onset + 1]:
                raise ContractError("support bins do not match the onset pair")
            if sign not in {"positive", "negative"}:
                raise ContractError("valid onset requires a positive/negative sign")
        normalized.append(
            {
                "panel_id": panel_id,
                "onset": onset,
                "support_bins": list(support),
                "sign": sign,
            }
        )
    expected_order = sorted(
        (row["panel_id"] for row in normalized), key=_natural_panel_key
    )
    if [row["panel_id"] for row in normalized] != expected_order:
        raise ContractError("panel onset ledger is not in natural numeric order")
    return normalized


def select_earliest_panels(value: Any) -> list[str]:
    """Select the complete lexical tie set at the minimum non-null onset."""

    panels = normalize_panel_onset_ledger(value)
    eligible = [row for row in panels if row["onset"] is not None]
    if not eligible:
        raise ContractError("panel onset ledger contains no valid onset")
    earliest = min(int(row["onset"]) for row in eligible)
    return sorted(
        str(row["panel_id"]) for row in eligible if int(row["onset"]) == earliest
    )


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
        elif answer_type == "panel_onset_ledger":
            correct = normalize_panel_onset_ledger(
                predicted
            ) == normalize_panel_onset_ledger(expected)
        else:
            raise ContractError(f"unknown VisOps answer type {answer_type!r}")
    except (ContractError, TypeError, ValueError):
        correct = False
    return {
        "correct": bool(correct),
        "score": float(bool(correct)),
        "answer_type": answer_type,
    }

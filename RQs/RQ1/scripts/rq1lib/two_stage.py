"""Frozen RQ1b3 Stage-2 ledger-selection prompt and invalid-ledger policy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from vlmrca.vlm.client import text_part

from .contracts import canonical_json, sha256_bytes, stable_hash
from .prompts import structured_answer_contract
from .scoring import normalize_panel_onset_ledger

STAGE2_SCHEMA = "RQ1B3Stage2PromptV1"
INVALID_LEDGER_SCHEMA = "RQ1B3InvalidStage1LedgerV1"


def invalid_stage1_ledger(*, response_sha256: str, reason: str) -> dict[str, Any]:
    """Return the common no-information marker used after a Stage-1 failure."""

    return {
        "schema_version": INVALID_LEDGER_SCHEMA,
        "status": "invalid_stage1_ledger",
        "response_sha256": str(response_sha256),
        "reason": str(reason),
    }


def build_stage2_prompt(
    ledger: Mapping[str, Any],
    *,
    compact_transport: bool = False,
    panel_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build a Stage-2 prompt that contains only the persisted same-arm ledger."""

    if ledger.get("schema_version") == INVALID_LEDGER_SCHEMA:
        normalized: dict[str, Any] = dict(ledger)
        ledger_status = "invalid"
    else:
        normalized = {"panels": normalize_panel_onset_ledger(ledger)}
        ledger_status = "valid"
        if not panel_ids:
            panel_ids = tuple(str(row["panel_id"]) for row in normalized["panels"])
    operation = (
        "select_earliest_from_ledger_compact"
        if compact_transport
        else "select_earliest_from_ledger"
    )
    answer_contract = structured_answer_contract(operation, panel_ids=panel_ids)
    system = (
        "You are Stage 2 of a label-free telemetry evidence operation. Use only "
        "the persisted Stage-1 ledger supplied below; do not infer or reconstruct "
        "the original image or text. Select the minimum non-null onset and return "
        "every panel tied at that onset in lexicographic order. If the supplied "
        "record is explicitly marked invalid or contains no usable onset, return "
        '["__NO_VALID_SELECTION__"]. Return exactly one JSON object and nothing '
        "else: no analysis, preamble, markdown, or code fence. The "
        f"{answer_contract['instruction']}. Required shape example: "
        f"{answer_contract['example']}"
    )
    evidence = "PERSISTED_STAGE1_LEDGER " + canonical_json(normalized)
    parts = [text_part(evidence)]
    prompt_contract = {
        "schema_version": STAGE2_SCHEMA,
        "stage": "stage2_select_from_frozen_ledger",
        "original_evidence_access": False,
        "ledger_status": ledger_status,
        "ledger_sha256": stable_hash(normalized),
        "system_sha256": sha256_bytes(system.encode()),
        "evidence_sha256": sha256_bytes(evidence.encode()),
        "answer_contract": answer_contract,
    }
    prompt_contract["prompt_contract_sha256"] = stable_hash(prompt_contract)
    return {
        "system": system,
        "parts": parts,
        "ledger": normalized,
        "answer_contract": answer_contract,
        "prompt_contract": prompt_contract,
    }

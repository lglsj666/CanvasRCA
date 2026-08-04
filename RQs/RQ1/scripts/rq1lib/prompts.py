"""Strict A/B prompt fragments and independent paired-view parity audits."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from vlmrca.vlm.client import image_part, text_part

from .contracts import (
    ContractError,
    assert_label_blind,
    canonical_json,
    sha256_bytes,
    stable_hash,
)
from .views import (
    ViewArtifact,
    parse_text_view_inventory,
    parse_visual_view_inventory,
)
from .visops import VisOpsTask

PROMPT_SCHEMA = "RQ1VisOpsPromptV2StructuredOutput"
AUDIT_SCHEMA = "PairedViewAuditV1"
VISUAL_LEGEND = (
    "Visual evidence fragment A. Read every printed value, direction, "
    "missingness cell, and legend exactly as shown."
)

ANSWER_TYPE_BY_OPERATION = {
    "metric_exact_lookup": "number",
    "log_exact_lookup": "number",
    "trace_exact_lookup": "number",
    "earliest_onset": "sorted_string_set",
    "longest_persistence": "sorted_string_set",
    "directed_edge": "directed_edge",
    "multi_hop_path": "ordered_path",
    "entity_modality_alignment": "sorted_string_set",
    "metric_missingness": "sorted_string_set",
    "raw_temporal_onset_low": "sorted_string_set",
    "raw_temporal_onset_high": "sorted_string_set",
    "panel_onset_ledger_high": "panel_onset_ledger",
    "panel_onset_ledger_high_compact": "panel_onset_ledger",
    "select_earliest_from_ledger": "sorted_string_set",
    "select_earliest_from_ledger_compact": "sorted_string_set",
    "directed_shortest_path_low": "ordered_path",
    "directed_shortest_path_high": "ordered_path",
}

def _compact_panel_ledger_regex(panel_ids: Sequence[str]) -> str:
    onset = "([0-9]|1[0-4])"
    value = f"(null|positive@{onset}|negative@{onset})"
    entries = ",".join(
        f'"{re.escape(panel_id)}:{value}"' for panel_id in panel_ids
    )
    return rf'\{{"answer":\{{"panels":\[{entries}\]\}}\}}'


def _compact_panel_selection_regex(panel_ids: Sequence[str]) -> str:
    panel = "(" + "|".join(
        (*[re.escape(panel_id) for panel_id in panel_ids], "__NO_VALID_SELECTION__")
    ) + ")"
    maximum_remainder = max(0, len(panel_ids) - 1)
    return rf'\{{"answer":\["{panel}"(,"{panel}"){{0,{maximum_remainder}}}\]\}}'


def panel_ids_from_public_facts(facts: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """Recover the complete ordered public panel vocabulary for a compact task."""

    panel_ids: list[str] = []
    for fact in facts:
        value = fact.get("value")
        if isinstance(value, Mapping) and value.get("panel_id") is not None:
            panel_id = str(value["panel_id"])
            if panel_id not in panel_ids:
                panel_ids.append(panel_id)
    def natural_key(value: str) -> tuple[str, int, str]:
        match = re.fullmatch(r"([^0-9]*)([0-9]+)(.*)", value)
        if match is None:
            return (value, -1, "")
        return (match.group(1), int(match.group(2)), match.group(3))

    return tuple(sorted(panel_ids, key=natural_key))


def structured_answer_contract(
    operation: str, *, panel_ids: Sequence[str] = ()
) -> dict[str, Any]:
    """Return the public answer-shape instruction and vLLM JSON schema."""

    answer_type = ANSWER_TYPE_BY_OPERATION.get(operation)
    if answer_type is None:
        raise ContractError(f"unknown VisOps operation {operation!r}")
    panel_ids = tuple(str(panel_id) for panel_id in panel_ids)
    if operation in {
        "panel_onset_ledger_high_compact",
        "select_earliest_from_ledger_compact",
    } and (len(panel_ids) != 12 or len(set(panel_ids)) != 12):
        raise ContractError("compact onset transport requires 12 unique panel IDs")
    if answer_type == "number":
        answer_schema: dict[str, Any] = {"type": "number"}
        example = '{"answer": 1.25}'
        instruction = "answer must be one JSON number"
    elif answer_type == "sorted_string_set":
        answer_schema = {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        }
        example = '{"answer": ["service-a", "service-b"]}'
        instruction = (
            "answer must be a lexicographically sorted JSON array containing every "
            "tied service exactly once; use no prose inside an item"
        )
    elif answer_type == "ordered_path":
        answer_schema = {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
        }
        example = '{"answer": ["caller", "middle", "callee"]}'
        instruction = "answer must be the ordered caller-to-callee JSON string array"
    elif answer_type == "panel_onset_ledger" and operation.endswith("_compact"):
        answer_schema = {
            "type": "object",
            "properties": {
                "panels": {
                    "type": "array",
                    "prefixItems": [
                        {
                            "type": "string",
                            "description": f"{panel_id}:null or {panel_id}:SIGN@ONSET",
                        }
                        for panel_id in panel_ids
                    ],
                    "minItems": 12,
                    "maxItems": 12,
                }
            },
            "required": ["panels"],
            "additionalProperties": False,
        }
        example = (
            '{"answer":{"panels":["M1:null","M2:positive@4",'
            '"M3:negative@7","M4:null",...,"M12:null"]}}'
        )
        instruction = (
            "answer must contain exactly M1 through M12 in natural numeric order; "
            "encode no onset as PANEL:null and a valid onset as "
            "PANEL:positive@BIN or PANEL:negative@BIN, where BIN is 0 through 14"
        )
    elif answer_type == "panel_onset_ledger":
        answer_schema = {
            "type": "object",
            "properties": {
                "panels": {
                    "type": "array",
                    "minItems": 12,
                    "maxItems": 12,
                    "items": {
                        "type": "object",
                        "properties": {
                            "panel_id": {"type": "string"},
                            "onset": {
                                "anyOf": [
                                    {"type": "integer", "minimum": 0, "maximum": 14},
                                    {"type": "null"},
                                ]
                            },
                            "support_bins": {
                                "type": "array",
                                "items": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 15,
                                },
                                "minItems": 0,
                                "maxItems": 2,
                            },
                            "sign": {
                                "enum": ["positive", "negative", None],
                            },
                        },
                        "required": [
                            "panel_id",
                            "onset",
                            "support_bins",
                            "sign",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["panels"],
            "additionalProperties": False,
        }
        example = (
            '{"answer": {"panels": [{"panel_id": "M1", "onset": null, '
            '"support_bins": [], "sign": null}]}}'
        )
        instruction = (
            "answer must be one complete panel-onset ledger in natural numeric "
            "panel order; include every supplied panel exactly once; a valid onset "
            "uses its two support bins and positive/negative sign, while no onset "
            "uses null, an empty support_bins array, and null sign"
        )
    else:
        answer_schema = {
            "type": "object",
            "properties": {
                "caller": {"type": "string"},
                "callee": {"type": "string"},
            },
            "required": ["caller", "callee"],
            "additionalProperties": False,
        }
        example = '{"answer": {"caller": "service-a", "callee": "service-b"}}'
        instruction = "answer must be one JSON object with exact caller and callee keys"
    top_level_schema = {
        "type": "object",
        "properties": {"answer": answer_schema},
        "required": ["answer"],
        "additionalProperties": False,
    }
    guided_regex = None
    if operation == "panel_onset_ledger_high_compact":
        guided_regex = _compact_panel_ledger_regex(panel_ids)
    elif operation == "select_earliest_from_ledger_compact":
        guided_regex = _compact_panel_selection_regex(panel_ids)
    response_format = None
    if guided_regex is None:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": f"rq1_visops_{answer_type}",
                "description": "One machine-verifiable RCA-VisOps answer object.",
                "schema": top_level_schema,
                "strict": True,
            },
        }
    transport = (
        "vllm_structured_outputs_regex_no_whitespace"
        if guided_regex is not None
        else "openai_response_format_json_schema"
    )
    contract = {
        "operation": operation,
        "answer_type": answer_type,
        "instruction": instruction,
        "example": example,
        "response_format": response_format,
        "response_format_sha256": stable_hash(response_format),
    }
    if guided_regex is not None:
        contract["response_format_sha256"] = None
        contract["guided_regex"] = guided_regex
        contract["guided_regex_sha256"] = stable_hash(guided_regex)
        contract["structured_output_transport"] = transport
        contract["panel_ids"] = list(panel_ids)
    return contract


def _part_contract(part: Mapping[str, Any]) -> dict[str, Any]:
    if part.get("type") == "text":
        raw = str(part.get("text") or "").encode("utf-8")
        return {"type": "text", "sha256": sha256_bytes(raw), "length": len(raw)}
    if part.get("type") == "image":
        raw = bytes(part.get("png") or b"")
        return {"type": "image", "sha256": sha256_bytes(raw), "length": len(raw)}
    raise ContractError(f"unknown prompt part type {part.get('type')!r}")


def prompt_parts_hash(parts: Sequence[Mapping[str, Any]]) -> str:
    return stable_hash([_part_contract(part) for part in parts])


@dataclass(frozen=True)
class PromptFragment:
    name: str
    parts: tuple[Mapping[str, Any], ...]

    @property
    def fragment_sha256(self) -> str:
        return prompt_parts_hash(self.parts)

    def contract(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "fragment_sha256": self.fragment_sha256,
            "parts": [_part_contract(part) for part in self.parts],
        }


@dataclass(frozen=True)
class PromptBundle:
    system: str
    visual_a: PromptFragment
    text_b: PromptFragment
    hybrid_a_plus_b: PromptFragment
    answer_contract: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.hybrid_a_plus_b.parts != self.visual_a.parts + self.text_b.parts:
            raise ContractError("hybrid prompt is not an exact A+B part concatenation")
        expected = structured_answer_contract(
            str(self.answer_contract["operation"]),
            panel_ids=tuple(self.answer_contract.get("panel_ids") or ()),
        )
        if dict(self.answer_contract) != expected:
            raise ContractError("structured answer contract drifted")

    def public_contract(self) -> dict[str, Any]:
        return {
            "schema_version": PROMPT_SCHEMA,
            "system_sha256": sha256_bytes(self.system.encode("utf-8")),
            "composition": "A_PLUS_B",
            "visual_a": self.visual_a.contract(),
            "text_b": self.text_b.contract(),
            "hybrid_a_plus_b": self.hybrid_a_plus_b.contract(),
            "exact_part_concatenation": True,
            "answer_contract": dict(self.answer_contract),
        }


def build_prompt_bundle(
    task: VisOpsTask,
    *,
    text_view: ViewArtifact,
    visual_view: ViewArtifact,
) -> PromptBundle:
    """Build A, B, and exactly A+B with no hybrid-only instruction."""

    if text_view.query_hash != task.query.query_hash:
        raise ContractError("text view belongs to another query")
    if visual_view.query_hash != task.query.query_hash:
        raise ContractError("visual view belongs to another query")
    registered_answer_type = ANSWER_TYPE_BY_OPERATION.get(task.query.operation)
    if registered_answer_type != task.private_answer_key.answer_type:
        raise ContractError(
            "public operation and evaluator-private answer type differ: "
            f"{task.query.operation} -> {registered_answer_type!r}, "
            f"private={task.private_answer_key.answer_type!r}"
        )
    bundle = build_prompt_bundle_from_artifacts(
        operation=task.query.operation,
        question=task.question,
        text_bytes=text_view.artifact_bytes,
        png_bytes=visual_view.artifact_bytes,
        panel_ids=panel_ids_from_public_facts(
            [fact.model_visible_dict() for fact in task.facts]
        ),
    )
    visible = {
        "system": bundle.system,
        "visual_text_parts": [
            part["text"] for part in bundle.visual_a.parts if part.get("type") == "text"
        ],
        "text_parts": [
            part["text"] for part in bundle.text_b.parts if part.get("type") == "text"
        ],
    }
    assert_label_blind(visible, context=f"prompt {task.query.query_id}")
    return bundle


def build_prompt_bundle_from_artifacts(
    *,
    operation: str,
    question: str,
    text_bytes: bytes,
    png_bytes: bytes,
    panel_ids: Sequence[str] = (),
) -> PromptBundle:
    """Rebuild frozen prompt fragments from persisted public artifacts."""

    answer_contract = structured_answer_contract(operation, panel_ids=panel_ids)
    system = (
        "You are solving a label-free telemetry evidence operation. "
        "Use only the supplied view. All time is relative to window start t=0; "
        "caller -> callee means caller invokes callee; missing is not normal.\n"
        f"Question: {question}\n"
        "Return exactly one JSON object and nothing else: no analysis, preamble, "
        "markdown, code fence, or self-correction. "
        f"The {answer_contract['instruction']}. Required shape example: "
        f"{answer_contract['example']}"
    )
    visual = PromptFragment(
        name="A_visual",
        parts=(image_part(png_bytes), text_part(VISUAL_LEGEND)),
    )
    text = PromptFragment(
        name="B_text",
        parts=(text_part(text_bytes.decode("utf-8")),),
    )
    hybrid = PromptFragment(name="A_PLUS_B", parts=visual.parts + text.parts)
    return PromptBundle(
        system=system,
        visual_a=visual,
        text_b=text,
        hybrid_a_plus_b=hybrid,
        answer_contract=answer_contract,
    )


def audit_paired_views(
    task: VisOpsTask,
    *,
    text_view: ViewArtifact,
    visual_view: ViewArtifact,
    prompts: PromptBundle,
    private_markers: Iterable[Any] = (),
) -> dict[str, Any]:
    """Reconstruct each arm's inventory and fail on any mismatch or leakage."""

    failures: list[str] = []
    expected = tuple(sorted(task.query.fact_ids))
    parsed_text_facts = parse_text_view_inventory(text_view.artifact_bytes)
    text_ids = tuple(sorted(str(fact["fact_id"]) for fact in parsed_text_facts))
    visual_ids = parse_visual_view_inventory(visual_view.primitive_manifest)
    hybrid_ids = tuple(sorted(set(visual_ids) | set(text_ids)))
    for name, ids in (
        ("text", text_ids),
        ("visual", visual_ids),
        ("bounded_hybrid", hybrid_ids),
    ):
        if ids != expected:
            failures.append(f"{name}_fact_inventory_mismatch")
    expected_public_hashes = {
        fact.fact_id: sha256_bytes(
            canonical_json(fact.model_visible_dict()).encode("utf-8")
        )
        for fact in task.facts
    }
    text_public_hashes = {
        str(fact["fact_id"]): sha256_bytes(canonical_json(fact).encode("utf-8"))
        for fact in parsed_text_facts
    }
    visual_public_hashes = dict(
        visual_view.primitive_manifest.get("public_fact_hashes") or {}
    )
    if text_public_hashes != expected_public_hashes:
        failures.append("text_public_fact_value_mismatch")
    if visual_public_hashes != expected_public_hashes:
        failures.append("visual_public_fact_value_mismatch")
    if prompts.hybrid_a_plus_b.parts != prompts.visual_a.parts + prompts.text_b.parts:
        failures.append("hybrid_not_exact_A_plus_B")

    visible_payload = {
        "query": task.query.public_dict(),
        "question": task.question,
        "text": text_view.artifact_bytes.decode("utf-8"),
        "visual_manifest": visual_view.primitive_manifest,
        "visual_visible_text": list(visual_view.visible_text),
        "system": prompts.system,
        "prompt_text_parts": [
            part["text"]
            for part in prompts.hybrid_a_plus_b.parts
            if part.get("type") == "text"
        ],
    }
    try:
        assert_label_blind(
            visible_payload,
            private_markers=private_markers,
            context=f"paired views {task.query.query_id}",
        )
        leakage_ok = True
    except ContractError as exc:
        leakage_ok = False
        failures.append(str(exc))

    arms = {
        "visual": {
            "fact_inventory_hash": task.query.fact_inventory_hash,
            "fact_ids": list(visual_ids),
            "location_map": dict(visual_view.location_map),
            "artifact_sha256": visual_view.artifact_sha256,
        },
        "text": {
            "fact_inventory_hash": task.query.fact_inventory_hash,
            "fact_ids": list(text_ids),
            "location_map": dict(text_view.location_map),
            "artifact_sha256": text_view.artifact_sha256,
        },
        "bounded_hybrid": {
            "fact_inventory_hash": task.query.fact_inventory_hash,
            "fact_ids": list(hybrid_ids),
            "location_map": {
                fact_id: {
                    "visual": visual_view.location_map.get(fact_id),
                    "text": text_view.location_map.get(fact_id),
                }
                for fact_id in hybrid_ids
            },
            "artifact_sha256": prompts.hybrid_a_plus_b.fragment_sha256,
        },
    }
    audit = {
        "schema_version": AUDIT_SCHEMA,
        "query_id": task.query.query_id,
        "query_hash": task.query.query_hash,
        "fact_inventory_hash": task.query.fact_inventory_hash,
        "fact_count": len(expected),
        "arms": arms,
        "prompt_composition": {
            "order": "A_PLUS_B",
            "a_sha256": prompts.visual_a.fragment_sha256,
            "b_sha256": prompts.text_b.fragment_sha256,
            "hybrid_sha256": prompts.hybrid_a_plus_b.fragment_sha256,
            "exact_part_concatenation": True,
        },
        "parity_ok": not any(
            "inventory" in item or "exact_A" in item for item in failures
        ),
        "leakage_ok": leakage_ok,
        "failures": failures,
    }
    if failures:
        raise ContractError(f"paired-view audit failed: {'; '.join(failures)}")
    return audit

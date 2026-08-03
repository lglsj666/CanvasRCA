"""Strict A/B prompt fragments and independent paired-view parity audits."""

from __future__ import annotations

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

PROMPT_SCHEMA = "RQ1VisOpsPromptV1"
AUDIT_SCHEMA = "PairedViewAuditV1"
VISUAL_LEGEND = (
    "Visual evidence fragment A. Read every printed value, direction, "
    "missingness cell, and legend exactly as shown."
)


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

    def __post_init__(self) -> None:
        if self.hybrid_a_plus_b.parts != self.visual_a.parts + self.text_b.parts:
            raise ContractError("hybrid prompt is not an exact A+B part concatenation")

    def public_contract(self) -> dict[str, Any]:
        return {
            "schema_version": PROMPT_SCHEMA,
            "system_sha256": sha256_bytes(self.system.encode("utf-8")),
            "composition": "A_PLUS_B",
            "visual_a": self.visual_a.contract(),
            "text_b": self.text_b.contract(),
            "hybrid_a_plus_b": self.hybrid_a_plus_b.contract(),
            "exact_part_concatenation": True,
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
    bundle = build_prompt_bundle_from_artifacts(
        question=task.question,
        text_bytes=text_view.artifact_bytes,
        png_bytes=visual_view.artifact_bytes,
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
    question: str,
    text_bytes: bytes,
    png_bytes: bytes,
) -> PromptBundle:
    """Rebuild frozen prompt fragments from persisted public artifacts."""

    system = (
        "You are solving a label-free telemetry evidence operation. "
        "Use only the supplied view. All time is relative to window start t=0; "
        "caller -> callee means caller invokes callee; missing is not normal.\n"
        f"Question: {question}\n"
        'Return only one JSON object: {"answer": <value>}'
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
    text_ids = tuple(sorted(fact.fact_id for fact in parsed_text_facts))
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
        fact.fact_id: sha256_bytes(canonical_json(fact.public_dict()).encode("utf-8"))
        for fact in task.facts
    }
    text_public_hashes = {
        fact.fact_id: sha256_bytes(canonical_json(fact.public_dict()).encode("utf-8"))
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

#!/usr/bin/env python3
"""Prove that an RQ1 output-contract rerun did not change its evidence inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rq1lib.contracts import ContractError, canonical_json, sha256_bytes, stable_hash

ROOT = Path(__file__).resolve().parents[3]
UNCHANGED_PUBLIC_FILES = {
    "task",
    "text",
    "visual",
    "visual_manifest",
    "paired_audit",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractError(f"{path} is not a JSON object")
    return payload


def _case_roots(prepared: Path) -> dict[str, Path]:
    roots = {
        path.name: path
        for path in sorted(prepared.resolve().glob("INC-*"))
        if (path / "manifest.json").is_file()
    }
    if not roots:
        raise ContractError(f"no prepared incidents under {prepared}")
    return roots


def _task_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["query_id"]): row for row in manifest.get("tasks") or []}


def _prompt_invariants(prompt: dict[str, Any]) -> dict[str, Any]:
    return {
        "composition": prompt.get("composition"),
        "visual_a": prompt.get("visual_a"),
        "text_b": prompt.get("text_b"),
        "hybrid_a_plus_b": prompt.get("hybrid_a_plus_b"),
        "exact_part_concatenation": prompt.get("exact_part_concatenation"),
    }


def compare_inputs(left: Path, right: Path) -> dict[str, Any]:
    left_roots = _case_roots(left)
    right_roots = _case_roots(right)
    if set(left_roots) != set(right_roots):
        raise ContractError("v1/v2 prepared incident rosters differ")

    task_count = 0
    prompt_changes = 0
    unchanged_files = 0
    for opaque_id in sorted(left_roots):
        left_root = left_roots[opaque_id]
        right_root = right_roots[opaque_id]
        left_manifest = _load(left_root / "manifest.json")
        right_manifest = _load(right_root / "manifest.json")
        for field in ("opaque_incident_id", "evidence_store", "task_count", "status"):
            if left_manifest.get(field) != right_manifest.get(field):
                raise ContractError(f"{opaque_id} manifest differs at {field}")
        left_tasks = _task_index(left_manifest)
        right_tasks = _task_index(right_manifest)
        if set(left_tasks) != set(right_tasks):
            raise ContractError(f"{opaque_id} query inventories differ")
        left_private = _load(left_root / "private/index.json")
        right_private = _load(right_root / "private/index.json")
        if left_private != right_private:
            raise ContractError(f"{opaque_id} private-answer indexes differ")

        for query_id in sorted(left_tasks):
            task_count += 1
            left_task = left_tasks[query_id]
            right_task = right_tasks[query_id]
            for field in (
                "query_id",
                "query_hash",
                "operation",
                "family",
                "fact_inventory_hash",
            ):
                if left_task.get(field) != right_task.get(field):
                    raise ContractError(
                        f"{opaque_id}/{query_id} task metadata differs at {field}"
                    )
            for name in UNCHANGED_PUBLIC_FILES:
                left_bytes = (left_root / left_task["public_files"][name]).read_bytes()
                right_bytes = (
                    right_root / right_task["public_files"][name]
                ).read_bytes()
                if left_bytes != right_bytes:
                    raise ContractError(
                        f"{opaque_id}/{query_id} evidence artifact differs: {name}"
                    )
                unchanged_files += 1

            left_prompt = _load(
                left_root / left_task["public_files"]["prompt_contract"]
            )
            right_prompt = _load(
                right_root / right_task["public_files"]["prompt_contract"]
            )
            if _prompt_invariants(left_prompt) != _prompt_invariants(right_prompt):
                raise ContractError(f"{opaque_id}/{query_id} A/B/H fragments differ")
            if left_prompt == right_prompt:
                raise ContractError(
                    f"{opaque_id}/{query_id} lacks the registered prompt repair"
                )
            if (
                right_prompt.get("schema_version")
                != "RQ1VisOpsPromptV2StructuredOutput"
                or not right_prompt.get("answer_contract", {}).get(
                    "response_format_sha256"
                )
            ):
                raise ContractError(
                    f"{opaque_id}/{query_id} lacks the v2 answer contract"
                )
            prompt_changes += 1

            private_record = next(
                row
                for row in left_private["records"]
                if row["query_id"] == query_id
            )
            relative_answer = private_record["answer_key"]
            if (left_root / relative_answer).read_bytes() != (
                right_root / relative_answer
            ).read_bytes():
                raise ContractError(
                    f"{opaque_id}/{query_id} private answer key differs"
                )

    left_index = _load(left.resolve() / "index.json")
    right_index = _load(right.resolve() / "index.json")
    report = {
        "schema_version": "RQ1InputEquivalenceAuditV1",
        "status": "passed",
        "left_experiment_id": left_index.get("experiment_id"),
        "right_experiment_id": right_index.get("experiment_id"),
        "left_artifact_inventory_hash": left_index.get("artifact_inventory_hash"),
        "right_artifact_inventory_hash": right_index.get("artifact_inventory_hash"),
        "roster_assignment_hash": right_index.get("roster_assignment_hash"),
        "incidents": len(left_roots),
        "tasks": task_count,
        "unchanged_evidence_artifacts": unchanged_files,
        "changed_prompt_contracts": prompt_changes,
        "ceb_equal": True,
        "query_equal": True,
        "fact_inventory_equal": True,
        "text_equal": True,
        "image_equal": True,
        "visual_manifest_equal": True,
        "paired_audit_equal": True,
        "private_answer_equal": True,
        "prompt_fragments_a_b_h_equal": True,
        "only_registered_prompt_output_contract_changed": True,
    }
    report["audit_sha256"] = stable_hash(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare_inputs(args.left, args.right)
    output = args.output.resolve()
    results_root = (ROOT / "RQs/RQ1/results").resolve()
    if results_root not in output.parents:
        raise ContractError("input-equivalence audit must be written under RQ1 results")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(report) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    print(f"output_sha256={sha256_bytes(output.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

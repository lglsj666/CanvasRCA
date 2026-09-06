#!/usr/bin/env python3
"""Repair RQ1.1 QA schedules that used representation-specific row order.

The script edits only QA schedule sidecars and their prepared index.  With
``--apply`` it also removes completed Direct-QA matched groups whose public or
private question changed.  Direct-RCA trajectories and large prepared evidence
artifacts are never touched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from unified_scripts import stable_hash
from RQs.RQ1_1.src.exps import Question, questions_for_case
from RQs.RQ1_1.src.utils import ROOT, write_json


DEFAULT_PREPARED = ROOT / "RQs/RQ1_1/results/rq1_1_v3_rq480_prepared_balanced_v1"
DEFAULT_RESULTS = ROOT / "RQs/RQ1_1/results/rq1_1_v3_formal_480_v1"


def _public(question: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in question.items()
        if key not in {"answer_steps", "supporting_fact_ids"}
    }


def _replacement(old: Mapping[str, Any], candidates: Iterable[Question]) -> Question:
    path = tuple(map(str, old["region_path"]))
    reasoning = int(old["reasoning_difficulty"])
    pool = list(candidates)
    if not pool:
        raise RuntimeError(f"P{old['perception_difficulty']} has no eligible replacement")
    return min(pool, key=lambda question: (
        question.reasoning_difficulty != reasoning,
        question.regions != path,
        abs(question.reasoning_difficulty - reasoning),
        sum(left != right for left, right in zip(question.regions, path, strict=True)),
        question.query_id,
    ))


def _scheduled(question: Question, old: Mapping[str, Any]) -> dict[str, Any]:
    value = question.private()
    value.update(
        requested_reasoning_difficulty=int(
            old.get("requested_reasoning_difficulty") or old["reasoning_difficulty"]
        ),
        requested_region_path=list(
            old.get("requested_region_path") or old["region_path"]
        ),
    )
    value["selection_fallback"] = (
        value["reasoning_difficulty"] != value["requested_reasoning_difficulty"]
        or value["region_path"] != value["requested_region_path"]
    )
    return value


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _safe_unlink(root: Path, path: Path) -> None:
    resolved_root, resolved = root.resolve(), path.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise RuntimeError(f"refusing to delete outside result root: {resolved}")
    if path.is_file() or path.is_symlink():
        path.unlink()


def _remove_group(
    result_root: Path, opaque: str, level: int, audit: list[dict[str, Any]],
) -> int:
    removed = 0
    trajectory_root = result_root / "trajectories/direct_qa"
    for path in sorted(trajectory_root.glob(f"*/{opaque}__L{level}_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        audit.append({
            "path": str(path.relative_to(result_root)),
            "record_sha256": record.get("record_sha256"),
            "arm": record.get("arm"),
            "model": record.get("model"),
        })
        for value in _strings(record):
            if value.startswith("attention/"):
                _safe_unlink(result_root, result_root / value)
        _safe_unlink(result_root, path.with_suffix(".md"))
        _safe_unlink(result_root, path)
        removed += 1
    return removed


def _balance_audit(schedules: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]:
    levels: dict[str, Any] = {}
    for level in range(1, 5):
        counts = Counter(
            (int(question["reasoning_difficulty"]), "".join(question["region_path"]))
            for questions in schedules.values() for question in questions
            if int(question["perception_difficulty"]) == level
        )
        values = list(counts.values())
        levels[str(level)] = {
            "eligible_cases": sum(
                any(int(question["perception_difficulty"]) == level for question in questions)
                for questions in schedules.values()
            ),
            "covered_cells": len(counts),
            "minimum_cell_count": min(values) if values else 0,
            "maximum_cell_count": max(values) if values else 0,
            "reasoning_counts": {
                str(reasoning): sum(
                    count for (actual, _), count in counts.items() if actual == reasoning
                )
                for reasoning in (1, 2, 3)
            },
            "cell_counts": {
                f"R{reasoning}:{path}": count
                for (reasoning, path), count in sorted(counts.items())
            },
        }
    return {"schema_version": "RQ1_1QABalanceAuditV1", "levels": levels}


def repair(prepared_root: Path, result_root: Path, apply: bool) -> dict[str, Any]:
    index_path = prepared_root / "prepared/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    unsigned = dict(index); recorded = unsigned.pop("index_sha256", None)
    if stable_hash(unsigned) != recorded:
        raise RuntimeError("prepared index hash mismatch before repair")

    changes: list[dict[str, Any]] = []
    schedules: dict[str, list[dict[str, Any]]] = {}
    updates: list[tuple[dict[str, Any], Path, Path, dict[str, Any], dict[str, Any]]] = []
    for entry in index["cases"]:
        opaque = str(entry["opaque_incident_id"])
        public_case_path = prepared_root / entry["public"]
        if hashlib.sha256(public_case_path.read_bytes()).hexdigest() != entry["public_sha256"]:
            raise RuntimeError(f"public case hash mismatch: {opaque}")
        packet = json.loads(public_case_path.read_text(encoding="utf-8"))["packet"]
        public_path = prepared_root / entry["qa_public_schedule"]
        private_path = prepared_root / entry["qa_private_schedule"]
        old_public = json.loads(public_path.read_text(encoding="utf-8"))
        old_private = json.loads(private_path.read_text(encoding="utf-8"))
        templates, _ = questions_for_case(packet, opaque)
        by_level: dict[int, list[Question]] = defaultdict(list)
        for question in templates:
            by_level[question.perception_difficulty].append(question)
        new_private_questions: list[dict[str, Any]] = []
        for old_question in old_private.get("selected_questions") or ():
            replacement = _scheduled(
                _replacement(old_question, by_level[int(old_question["perception_difficulty"])]),
                old_question,
            )
            new_private_questions.append(replacement)
            if replacement != old_question:
                changes.append({
                    "opaque_incident_id": opaque,
                    "perception_difficulty": int(old_question["perception_difficulty"]),
                    "old": _public(old_question),
                    "new": _public(replacement),
                })
        new_private_questions.sort(key=lambda row: int(row["perception_difficulty"]))
        new_public_questions = [_public(question) for question in new_private_questions]
        common = {
            "schema_version": "RQ1_1QASelectionScheduleV2",
            "opaque_incident_id": opaque,
            "selection_policy": "roster_balanced_visible_eligibility_v1_anchor_repair",
        }
        public_payload = {**common, "selected_questions": new_public_questions}
        private_payload = {**common, "selected_questions": new_private_questions}
        schedules[opaque] = new_private_questions
        updates.append((entry, public_path, private_path, public_payload, private_payload))

    changed_groups = {(row["opaque_incident_id"], row["perception_difficulty"]) for row in changes}
    removed_records: list[dict[str, Any]] = []
    removed_count = 0
    if apply:
        for entry, public_path, private_path, public_payload, private_payload in updates:
            write_json(public_path, public_payload); write_json(private_path, private_payload)
            entry["qa_public_schedule_sha256"] = hashlib.sha256(public_path.read_bytes()).hexdigest()
            entry["qa_private_schedule_sha256"] = hashlib.sha256(private_path.read_bytes()).hexdigest()
            entry["qa_question_schedule"] = [{
                key: question[key] for key in (
                    "query_id", "perception_difficulty", "reasoning_difficulty",
                    "reasoning_family", "region_path", "requested_reasoning_difficulty",
                    "requested_region_path", "selection_fallback",
                )
            } for question in public_payload["selected_questions"]]
        index["qa_balance_audit"] = _balance_audit(schedules)
        repair_entry = {
            "schema_version": "RQ1_1QADisplayOrderRepairV1",
            "date": "2026-09-05",
            "reason": "remove representation-specific trace-row/topology-edge order cues in favor of visible content anchors",
            "changed_matched_groups": len(changed_groups),
            "large_evidence_artifacts_rewritten": False,
        }
        history = list(index.get("qa_schedule_repairs") or ())
        prior = index.pop("qa_schedule_repair", None)
        if prior and prior not in history:
            history.append(prior)
        history.append(repair_entry)
        index["qa_schedule_repairs"] = history
        index.pop("index_sha256", None); index["index_sha256"] = stable_hash(index)
        write_json(index_path, index)
        for opaque, level in sorted(changed_groups):
            removed_count += _remove_group(result_root, opaque, level, removed_records)
        for pattern in (
            "run_direct_qa_*.json", "summary_direct_qa.json",
            "summary_perception_rca_joint.json", "verification.json",
        ):
            for path in result_root.glob(pattern):
                _safe_unlink(result_root, path)
        audit_root = result_root / "repair_audits"
        audit_root.mkdir(parents=True, exist_ok=True)
        existing = sorted(audit_root.glob("2026-09-05_qa_display_order_repair*.json"))
        suffix = "" if not existing else f"_{len(existing) + 1:02d}"
        write_json(audit_root / f"2026-09-05_qa_display_order_repair{suffix}.json", {
            "schema_version": "RQ1_1QADisplayOrderRepairV1",
            "prepared_root": str(prepared_root.relative_to(ROOT)),
            "changed_groups": changes,
            "removed_records": removed_records,
            "unaffected_direct_rca_preserved": True,
            "index_sha256_after": index["index_sha256"],
        })

    return {
        "apply": apply,
        "cases": len(index["cases"]),
        "changed_matched_groups": len(changed_groups),
        "changed_question_records": len(changes),
        "affected_levels": dict(sorted(Counter(level for _, level in changed_groups).items())),
        "removed_direct_qa_records": removed_count,
        "direct_rca_touched": False,
        "index_sha256_after": index.get("index_sha256"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared-root", type=Path, default=DEFAULT_PREPARED)
    parser.add_argument("--result-root", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(repair(args.prepared_root, args.result_root, args.apply), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

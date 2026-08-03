#!/usr/bin/env python3
"""Combine the two nonredundant modality-allocation development runs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
RESULT_ROOT = ROOT / "RQs/RQ0/results/rq0_nonredundant_modality_allocation_v1"
MODELS = ("qwen3.6-27b", "gemma-4-26b-a4b")
ARMS = ("allocated_visual_text", "duplicated_visual_text", "full_text_only")


def _rows(path: Path) -> List[Dict[str, Any]]:
    return [
        row
        for line in path.read_text(errors="replace").splitlines()
        if (row := json.loads(line)).get("record_type") == "episode"
    ]


def _integrity(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_case: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_case.setdefault(row["case_id"], []).append(row)
    return {
        "n_calls": len(rows),
        "n_cases": len(by_case),
        "three_arms_each": all(
            {row["arm"] for row in values} == set(ARMS) and len(values) == 3
            for values in by_case.values()
        ),
        "common_summary_equal_each_case": all(
            len({row["common_summary_sha256"] for row in values}) == 1
            for values in by_case.values()
        ),
        "source_inventory_equal_each_case": all(
            len({row["source_fact_inventory_hash"] for row in values}) == 1
            for values in by_case.values()
        ),
        "a_b_text_equal_each_case": all(
            next(row for row in values if row["arm"] == "duplicated_visual_text")[
                "prompt_text_sha256"
            ]
            == next(row for row in values if row["arm"] == "full_text_only")[
                "prompt_text_sha256"
            ]
            for values in by_case.values()
        ),
        "d_a_image_equal_each_case": all(
            next(row for row in values if row["arm"] == "allocated_visual_text")[
                "image_sha256"
            ]
            == next(row for row in values if row["arm"] == "duplicated_visual_text")[
                "image_sha256"
            ]
            for values in by_case.values()
        ),
        "all_leakage_audits_pass": all(row["leakage_audit_ok"] for row in rows),
        "all_server_tokens_match": all(row["server_token_count_match"] for row in rows),
        "all_scoring_contracts_match": len({row["scoring_contract"] for row in rows}) == 1,
        "order_counts": dict(sorted(Counter(row["arm_order"] for row in rows[::3]).items())),
    }


def main() -> int:
    report: Dict[str, Any] = {
        "schema_version": "RQ0AllocationCrossModelAnalysisV1",
        "scope": "exposed_development_only_nonconfirmatory",
        "models": {},
    }
    for model in MODELS:
        run_dir = RESULT_ROOT / f"{model}__development__main"
        summary_path = run_dir / "summary.json"
        trajectory_path = run_dir / "trajectories/episodes.jsonl"
        if not summary_path.exists() or not trajectory_path.exists():
            report["models"][model] = {"status": "missing"}
            continue
        summary = json.loads(summary_path.read_text())
        rows = _rows(trajectory_path)
        report["models"][model] = {
            "status": "complete" if len(rows) == 72 else "incomplete",
            "summary": summary,
            "integrity": _integrity(rows),
        }
    complete = [
        value
        for value in report["models"].values()
        if value.get("status") == "complete"
    ]
    integrity_pass = all(
        all(
            value
            for key, value in model["integrity"].items()
            if key != "order_counts"
        )
        and model["integrity"]["order_counts"]
        == {order: 4 for order in ("DAB", "DBA", "ADB", "ABD", "BDA", "BAD")}
        for model in complete
    )
    both_model_gate = (
        len(complete) == 2
        and integrity_pass
        and all(model["summary"]["gate"]["pass_for_this_model"] for model in complete)
    )
    report["cross_model_gate"] = {
        "pass": both_model_gate,
        "integrity_pass": integrity_pass if len(complete) == 2 else False,
        "decision": (
            "eligible_for_separately_preregistered_fresh_replication"
            if both_model_gate
            else "stop_this_representation_without_reserve_calls"
        ),
    }
    output = RESULT_ROOT / "analysis"
    output.mkdir(parents=True, exist_ok=True)
    (output / "analysis.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )

    lines = [
        "# Nonredundant modality-allocation development result",
        "",
        "This is an exposed-development mechanism screen, not confirmatory evidence.",
        "",
        "| model | D MRR | A MRR | B MRR | D−B | improve/degrade/tie | D−A | gate |",
        "|---|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for model, value in report["models"].items():
        if value.get("status") != "complete":
            lines.append(f"| {model} | — | — | — | — | — | — | incomplete |")
            continue
        summary = value["summary"]
        arms = summary["arms"]
        db = summary["comparisons"]["D_minus_B"]
        da = summary["comparisons"]["D_minus_A"]
        lines.append(
            f"| {model} | {arms['allocated_visual_text']['mrr']:.4f} | "
            f"{arms['duplicated_visual_text']['mrr']:.4f} | "
            f"{arms['full_text_only']['mrr']:.4f} | {db['delta_mrr']:+.4f} | "
            f"{db['improved']}/{db['degraded']}/{db['tied']} | "
            f"{da['delta_mrr']:+.4f} | "
            f"{'pass' if summary['gate']['pass_for_this_model'] else 'fail'} |"
        )
    lines.extend(
        [
            "",
            f"Cross-model gate: **{'PASS' if both_model_gate else 'FAIL'}**.",
            "",
            (
                "A pass only permits a separately preregistered fresh replication."
                if both_model_gate
                else "Do not spend reserve cases on this representation."
            ),
            "",
        ]
    )
    (output / "summary.md").write_text("\n".join(lines))
    print(json.dumps(report["cross_model_gate"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


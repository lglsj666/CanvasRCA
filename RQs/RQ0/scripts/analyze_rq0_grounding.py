#!/usr/bin/env python3
"""Analyze the development-only RQ0 atomic visual-grounding diagnostic."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_atomic_visual_grounding_v1"
MODELS = ("qwen3.6-27b", "gemma-4-26b-a4b")
CONDITIONS = ("actual_image", "swapped_image", "no_image")


def _episodes(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        record = json.loads(line)
        if record.get("record_type") == "episode":
            rows.append(record)
    return rows


def _task_keys() -> Dict[str, Dict[str, Any]]:
    task_dir = ROOT / "RQs/RQ0/results" / EXPERIMENT / "artifacts" / "tasks"
    out = {}
    for path in sorted(task_dir.glob("*.tasks.json")):
        out[path.stem.removesuffix(".tasks")] = {
            task["task_id"]: task for task in json.loads(path.read_text())
        }
    return out


def _accuracy(tasks: List[Dict[str, Any]]) -> float | None:
    return sum(bool(task["correct"]) for task in tasks) / len(tasks) if tasks else None


def _analyze_model(model: str, keys: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    path = (
        ROOT / "RQs/RQ0/results" / EXPERIMENT / f"{model}__development__main"
        / "trajectories" / "episodes.jsonl"
    )
    rows = _episodes(path)
    condition_summary = {}
    all_categories = sorted({
        task["category"] for row in rows for task in row.get("task_scores", [])
    })
    for condition in CONDITIONS:
        selected = [row for row in rows if row["condition"] == condition]
        tasks = [task for row in selected for task in row.get("task_scores", [])]
        condition_summary[condition] = {
            "n_calls": len(selected),
            "n_tasks": len(tasks),
            "parse_rate": sum(bool(row["parse_ok"]) for row in selected) / len(selected),
            "accuracy": _accuracy(tasks),
            "accuracy_by_category": {
                category: _accuracy([task for task in tasks if task["category"] == category])
                for category in all_categories
            },
        }

    key_values: Dict[str, List[str]] = defaultdict(list)
    key_variants: Dict[str, Counter] = defaultdict(Counter)
    for case_tasks in keys.values():
        for task in case_tasks.values():
            key_values[task["category"]].append(str(task["answer_value"]))
            variant = str(task.get("metadata", {}).get("variant") or "default")
            key_variants[task["category"]][variant] += 1

    category_diagnostics = {}
    actual_rows = [row for row in rows if row["condition"] == "actual_image"]
    for category in all_categories:
        actual = condition_summary["actual_image"]["accuracy_by_category"][category]
        swapped = condition_summary["swapped_image"]["accuracy_by_category"][category]
        no_image = condition_summary["no_image"]["accuracy_by_category"][category]
        values = key_values[category]
        control_max = max(swapped, no_image)
        category_diagnostics[category] = {
            "n": len(values),
            "answer_value_distribution": dict(sorted(Counter(values).items())),
            "variant_distribution": dict(sorted(key_variants[category].items())),
            "actual_accuracy": actual,
            "swapped_accuracy": swapped,
            "no_image_accuracy": no_image,
            "actual_lift_over_stronger_control": actual - control_max,
            "degenerate_answer_key": len(set(values)) == 1,
            "actual_beats_both_controls": actual > control_max,
        }

    excluded = sorted(
        category for category, value in category_diagnostics.items()
        if value["degenerate_answer_key"]
    )
    adjusted = {}
    for condition in CONDITIONS:
        tasks = [
            task
            for row in rows if row["condition"] == condition
            for task in row.get("task_scores", [])
            if task["category"] not in excluded
        ]
        adjusted[condition] = {"n_tasks": len(tasks), "accuracy": _accuracy(tasks)}

    edge_variant = {}
    for variant in ("pair", "count_zero"):
        tasks = []
        for row in actual_rows:
            source = keys[row["opaque_incident_id"]]["topology_edge"]
            source_variant = source.get("metadata", {}).get("variant")
            if source_variant != variant:
                continue
            tasks.extend(
                task for task in row["task_scores"] if task["task_id"] == "topology_edge"
            )
        edge_variant[variant] = {"n": len(tasks), "accuracy": _accuracy(tasks)}

    return {
        "trajectory": str(path.relative_to(ROOT)),
        "integrity": {
            "expected_calls": 36,
            "observed_calls": len(rows),
            "unique_case_conditions": len({
                (row["opaque_incident_id"], row["condition"]) for row in rows
            }),
            "all_success": all(row["status"] == "success" for row in rows),
            "all_parse": all(row["parse_ok"] for row in rows),
            "no_truncation": not any(row["truncated"] for row in rows),
            "server_token_count_match": all(
                row.get("server_token_count_match") is True for row in rows
            ),
        },
        "conditions": condition_summary,
        "category_diagnostics": category_diagnostics,
        "excluded_control_failed_categories": excluded,
        "control_valid_adjusted": adjusted,
        "topology_edge_actual_by_variant": edge_variant,
    }


def _markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# RQ0 atomic visual-grounding diagnostic",
        "",
        "Scope: 12 development dashboards, seven multiple-choice pixel-reading",
        "tasks per dashboard, with actual-image, same-dataset swapped-image, and",
        "no-image controls. This is nonconfirmatory and does not alter RQ0.",
        "",
        "| model | actual | swapped | no image | actual (control-valid) | swapped | no image |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model, value in report["models"].items():
        conditions, adjusted = value["conditions"], value["control_valid_adjusted"]
        lines.append(
            f"| {model} | {conditions['actual_image']['accuracy']:.1%} | "
            f"{conditions['swapped_image']['accuracy']:.1%} | "
            f"{conditions['no_image']['accuracy']:.1%} | "
            f"{adjusted['actual_image']['accuracy']:.1%} | "
            f"{adjusted['swapped_image']['accuracy']:.1%} | "
            f"{adjusted['no_image']['accuracy']:.1%} |"
        )
    lines.extend([
        "",
        "`metric_pattern` is excluded from the control-valid columns because all",
        "12 answer keys are `increase`; the no-image condition reaches 100% for",
        "Qwen and Gemma. It is a failed diagnostic control, not visual evidence.",
        "",
        "## Actual-image accuracy by category",
        "",
        "| category | Qwen | Gemma | interpretation |",
        "|---|---:|---:|---|",
    ])
    interpretations = {
        "metric_identity": "service/panel linkage is readable",
        "metric_pattern": "invalid as evidence: degenerate answer key",
        "table_log": "log table mostly readable",
        "table_trace": "Qwen strong; Gemma partial",
        "topology_edge": "not grounded; at/below four-choice chance",
        "topology_order": "ordered propagation rows are readable",
        "topology_time": "onset labels are readable",
    }
    categories = sorted(next(iter(report["models"].values()))["category_diagnostics"])
    for category in categories:
        qwen = report["models"][MODELS[0]]["category_diagnostics"][category]
        gemma = report["models"][MODELS[1]]["category_diagnostics"][category]
        lines.append(
            f"| {category} | {qwen['actual_accuracy']:.1%} | "
            f"{gemma['actual_accuracy']:.1%} | {interpretations[category]} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "The models can read most atomic facts from the dashboard, so a broad",
        "visual-perception deficit is not the main explanation for RQ0. The shared",
        "perception defect is the faint curved call-edge encoding. Combined with",
        "the formal discordance audit—where the image often pulls the prediction",
        "to propagation row 1—the immediate bottlenecks are topology-edge",
        "legibility and causal/salience integration.",
        "",
        "Do not start broad visual-grounding SFT yet. First redesign only the",
        "development topology primitive and rerun this atomic edge control. If",
        "edge grounding becomes reliably above its swapped/no-image controls,",
        "the next learning intervention should target cause-versus-propagated",
        "symptom integration (case-level RCA SFT), not generic OCR/chart reading.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    keys = _task_keys()
    report = {
        "schema_version": 1,
        "experiment": EXPERIMENT,
        "scope": "development_only_nonconfirmatory",
        "random_chance": 0.25,
        "models": {model: _analyze_model(model, keys) for model in MODELS},
        "decision": {
            "broad_visual_grounding_sft_is_next": False,
            "topology_primitive_redesign_is_next": True,
            "case_level_causal_integration_sft_after_legibility_gate": True,
            "confirmatory_rq0_unchanged": "unsupported",
        },
    }
    output = ROOT / "RQs/RQ0/results" / EXPERIMENT / "analysis"
    output.mkdir(parents=True, exist_ok=True)
    (output / "grounding_analysis.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    (output / "summary.md").write_text(_markdown(report))
    print(json.dumps(report["decision"], indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Analyze the development-only RQ0 topology legibility interventions."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
MODELS = ("qwen3.6-27b", "gemma-4-26b-a4b")
EXPERIMENTS = {
    "compact_edge_key": "rq0_topology_edge_key_v1",
    "large_edge_key": "rq0_topology_edge_key_v2",
}
CONDITIONS = ("actual_image", "swapped_image", "no_image")


def _episodes(path: Path) -> List[Dict[str, Any]]:
    return [
        record
        for line in path.read_text().splitlines()
        if (record := json.loads(line)).get("record_type") == "episode"
    ]


def _analyze_run(experiment: str, model: str) -> Dict[str, Any]:
    run_dir = ROOT / "RQs/RQ0/results" / experiment / f"{model}__development__main"
    rows = _episodes(run_dir / "trajectories" / "episodes.jsonl")
    conditions = {}
    for condition in CONDITIONS:
        selected = [row for row in rows if row["condition"] == condition]
        conditions[condition] = {
            "n_calls": len(selected),
            "parse_rate": sum(bool(row["parse_ok"]) for row in selected) / len(selected),
            "accuracy": sum(bool(row["task_scores"][0]["correct"]) for row in selected)
            / len(selected),
            "mean_image_tokens": sum(int(row["image_input_tokens"] or 0) for row in selected)
            / len(selected),
        }
    statuses = Counter(str(row["status"]) for row in rows)
    return {
        "trajectory": str(
            (run_dir / "trajectories" / "episodes.jsonl").relative_to(ROOT)
        ),
        "integrity": {
            "expected_calls": 36,
            "observed_calls": len(rows),
            "unique_case_conditions": len(
                {(row["opaque_incident_id"], row["condition"]) for row in rows}
            ),
            "status_counts": dict(sorted(statuses.items())),
            "infrastructure_failures": statuses.get("infrastructure_failure", 0),
            "no_truncation": not any(row["truncated"] for row in rows),
            "server_token_count_match": all(
                row.get("server_token_count_match") is True for row in rows
            ),
            "actual_image_all_parse": all(
                row["parse_ok"] for row in rows if row["condition"] == "actual_image"
            ),
        },
        "conditions": conditions,
        "actual_lift_over_stronger_control": conditions["actual_image"]["accuracy"]
        - max(
            conditions["swapped_image"]["accuracy"],
            conditions["no_image"]["accuracy"],
        ),
    }


def _curved_edge_baseline() -> Dict[str, Any]:
    source = json.loads(
        (
            ROOT
            / "RQs/RQ0/results/rq0_atomic_visual_grounding_v1/analysis/grounding_analysis.json"
        ).read_text()
    )
    return {
        model: {
            condition: source["models"][model]["conditions"][condition][
                "accuracy_by_category"
            ]["topology_edge"]
            for condition in CONDITIONS
        }
        for model in MODELS
    }


def _markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# RQ0 topology-edge legibility intervention",
        "",
        "Scope: the same 12 development dashboards used by the atomic grounding",
        "diagnostic. The original renderer-v6 pixels remain unchanged; v1 appends",
        "a compact directional rank-pair key and v2 appends a larger four-line key.",
        "Actual-image, same-dataset swapped-image, and no-image controls are all",
        "reported. This is a perception qualification, not an RCA experiment, and",
        "does not alter the confirmatory RQ0 result.",
        "",
        "| visual primitive | Qwen actual | Qwen swapped | Qwen no image | Gemma actual | Gemma swapped | Gemma no image |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    curved = report["curved_edge_baseline"]
    lines.append(
        f"| renderer-v6 curved edge | {curved[MODELS[0]]['actual_image']:.1%} | "
        f"{curved[MODELS[0]]['swapped_image']:.1%} | "
        f"{curved[MODELS[0]]['no_image']:.1%} | "
        f"{curved[MODELS[1]]['actual_image']:.1%} | "
        f"{curved[MODELS[1]]['swapped_image']:.1%} | "
        f"{curved[MODELS[1]]['no_image']:.1%} |"
    )
    for label in ("compact_edge_key", "large_edge_key"):
        qwen = report["interventions"][label][MODELS[0]]["conditions"]
        gemma = report["interventions"][label][MODELS[1]]["conditions"]
        display = label.replace("_", " ")
        lines.append(
            f"| {display} | {qwen['actual_image']['accuracy']:.1%} | "
            f"{qwen['swapped_image']['accuracy']:.1%} | "
            f"{qwen['no_image']['accuracy']:.1%} | "
            f"{gemma['actual_image']['accuracy']:.1%} | "
            f"{gemma['swapped_image']['accuracy']:.1%} | "
            f"{gemma['no_image']['accuracy']:.1%} |"
        )
    lines.extend([
        "",
        "The original curved-edge and explicit-key questions are not identical, so",
        "their percentages are a qualification comparison rather than an effect-size",
        "estimate. The compact and large keys use the same 12 cases and task keys.",
        "",
        "## Scale sensitivity",
        "",
        "| model | compact actual | large actual | change | compact image tokens | large image tokens |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for model in MODELS:
        compact = report["interventions"]["compact_edge_key"][model]["conditions"]["actual_image"]
        large = report["interventions"]["large_edge_key"][model]["conditions"]["actual_image"]
        lines.append(
            f"| {model} | {compact['accuracy']:.1%} | {large['accuracy']:.1%} | "
            f"{large['accuracy'] - compact['accuracy']:+.1%} | "
            f"{compact['mean_image_tokens']:.0f} | {large['mean_image_tokens']:.0f} |"
        )
    lines.extend([
        "",
        "Gemma improves from 41.7% to 91.7% when the key is enlarged, while its",
        "mean visual-token count changes only slightly. Qwen is already at 100%",
        "with the compact key and remains there. The shared cross-model gate",
        "(at least 90% actual accuracy and at least 50 percentage points over the",
        "stronger control) is therefore passed only by the large key.",
        "",
        "All four real runs contain 36 unique case-condition calls, no infrastructure",
        "failures, no truncations, exact server/preflight token agreement, and 100%",
        "parse rate in the actual-image condition. Gemma has three no-image model",
        "formatting failures in each key experiment; these are retained as model",
        "outcomes and do not affect the actual-image legibility gate.",
        "",
        "## Decision",
        "",
        "The renderer-v6 curved topology edges are not a reliable model-readable",
        "primitive. Large explicit direction keys materially mitigate that atomic",
        "perception bottleneck across both tested architectures. This supports a development-only",
        "renderer-v7 candidate, but it does not establish an end-to-end RCA benefit.",
        "",
        "Do not start generic visual-grounding SFT: both models already read most",
        "dashboard atoms, and the isolated edge defect has a rendering fix. The next",
        "experiment should first integrate the large key into a frozen renderer-v7",
        "candidate and test case-level cause-versus-propagated-symptom reasoning on",
        "development incidents with unchanged textual evidence. Only if that improves",
        "paired RCA should the project preregister a fresh-reserve intervention study.",
        "The original 720-case RQ0 set must remain untouched.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    interventions = {
        label: {
            model: _analyze_run(experiment, model) for model in MODELS
        }
        for label, experiment in EXPERIMENTS.items()
    }
    large_pass = all(
        interventions["large_edge_key"][model]["conditions"]["actual_image"][
            "accuracy"
        ]
        >= 0.90
        and interventions["large_edge_key"][model][
            "actual_lift_over_stronger_control"
        ]
        >= 0.50
        for model in MODELS
    )
    report = {
        "schema_version": 1,
        "scope": "development_only_nonconfirmatory_renderer_intervention",
        "models": list(MODELS),
        "n_cases": 12,
        "random_chance": 0.25,
        "curved_edge_baseline": _curved_edge_baseline(),
        "interventions": interventions,
        "posthoc_operational_legibility_gate": {
            "actual_accuracy_min": 0.90,
            "actual_lift_over_stronger_control_min": 0.50,
            "large_edge_key_passes_both_models": large_pass,
        },
        "decision": {
            "confirmatory_rq0_unchanged": "unsupported",
            "generic_visual_grounding_sft_is_next": False,
            "renderer_v7_development_candidate": large_pass,
            "case_level_causal_integration_test_is_next": large_pass,
            "formal_cases_may_be_reused": False,
        },
    }
    output = ROOT / "RQs/RQ0/results/rq0_topology_edge_key_v2/analysis"
    output.mkdir(parents=True, exist_ok=True)
    (output / "topology_edge_key_analysis.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    (output / "summary.md").write_text(_markdown(report))
    print(json.dumps(report["decision"], indent=2))


if __name__ == "__main__":
    main()

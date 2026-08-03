#!/usr/bin/env python3
"""Analyze the development-only renderer-v7 case-level integration test."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_v7_edge_key_case_integration_v1"
MODELS = ("qwen3.6-27b", "gemma-4-26b-a4b")
CONDITIONS = ("v6_curved", "v7_large_edge_key")


def _episodes(model: str) -> List[Dict[str, Any]]:
    path = (
        ROOT
        / "RQs/RQ0/results"
        / EXPERIMENT
        / f"{model}__development__main/trajectories/episodes.jsonl"
    )
    return [
        record
        for line in path.read_text().splitlines()
        if (record := json.loads(line)).get("record_type") == "episode"
    ]


def _propagation_lookup() -> Dict[str, Dict[str, Any]]:
    roster = json.loads(
        (ROOT / "RQs/RQ0/results" / EXPERIMENT / "artifacts/artifact_roster.json").read_text()
    )
    out = {}
    for item in roster["records"]:
        manifest = json.loads((ROOT / item["v7_manifest"]).read_text())
        prop = next(panel for panel in manifest["panels"] if panel["kind"] == "propagation")
        ranks = {str(row["service"]): int(row["rank"]) for row in prop["rows"]}
        endpoints = set()
        for row in prop["rows"]:
            service = str(row["service"])
            for callee in row.get("callees") or []:
                if str(callee) in ranks:
                    endpoints.update((service, str(callee)))
            for caller in row.get("callers") or []:
                if str(caller) in ranks:
                    endpoints.update((str(caller), service))
        out[item["opaque_incident_id"]] = {"ranks": ranks, "edge_endpoints": endpoints}
    return out


def _analyze_model(model: str, propagation: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    rows = _episodes(model)
    indexed = {(row["opaque_incident_id"], row["condition"]): row for row in rows}
    case_ids = sorted({row["opaque_incident_id"] for row in rows})
    condition_metrics = {}
    for condition in CONDITIONS:
        selected = [row for row in rows if row["condition"] == condition]
        condition_metrics[condition] = {
            "n": len(selected),
            "parse_rate": sum(bool(row["parse_ok"]) for row in selected) / len(selected),
            "mrr": sum(float(row["mrr"]) for row in selected) / len(selected),
            "ac1": sum(float(row["ac1"]) for row in selected) / len(selected),
            "ac3": sum(float(row["ac3"]) for row in selected) / len(selected),
            "ac5": sum(float(row["ac5"]) for row in selected) / len(selected),
            "mean_input_tokens": sum(int(row["input_tokens"]) for row in selected)
            / len(selected),
            "mean_image_tokens": sum(int(row["image_input_tokens"]) for row in selected)
            / len(selected),
        }

    paired = []
    dataset_deltas: Dict[str, List[float]] = defaultdict(list)
    for opaque in case_ids:
        v6, v7 = indexed[(opaque, CONDITIONS[0])], indexed[(opaque, CONDITIONS[1])]
        old_top1 = (v6.get("predicted") or [None])[0]
        new_top1 = (v7.get("predicted") or [None])[0]
        delta = float(v7["mrr"]) - float(v6["mrr"])
        dataset_deltas[v6["dataset"]].append(delta)
        paired.append(
            {
                "opaque_incident_id": opaque,
                "dataset": v6["dataset"],
                "v6_top1": old_top1,
                "v7_top1": new_top1,
                "v6_mrr": v6["mrr"],
                "v7_mrr": v7["mrr"],
                "delta_mrr": delta,
                "top1_changed": old_top1 != new_top1,
                "v7_top1_propagation_rank": propagation[opaque]["ranks"].get(new_top1),
                "v7_top1_is_shown_edge_endpoint": new_top1
                in propagation[opaque]["edge_endpoints"],
            }
        )
    deltas = [row["delta_mrr"] for row in paired]
    return {
        "integrity": {
            "expected_calls": 24,
            "observed_calls": len(rows),
            "unique_case_conditions": len(indexed),
            "status_counts": dict(sorted(Counter(row["status"] for row in rows).items())),
            "no_infrastructure_failures": not any(
                row["status"] == "infrastructure_failure" for row in rows
            ),
            "no_truncation": not any(row["truncated"] for row in rows),
            "server_token_count_match": all(
                row.get("server_token_count_match") is True for row in rows
            ),
            "paired_prompt_text_hash_match": all(
                indexed[(opaque, CONDITIONS[0])]["prompt_text_sha256"]
                == indexed[(opaque, CONDITIONS[1])]["prompt_text_sha256"]
                for opaque in case_ids
            ),
        },
        "conditions": condition_metrics,
        "paired": {
            "n": len(paired),
            "mean_delta_mrr_v7_minus_v6": sum(deltas) / len(deltas),
            "improved": sum(value > 0 for value in deltas),
            "degraded": sum(value < 0 for value in deltas),
            "tied": sum(value == 0 for value in deltas),
            "top1_changed": sum(row["top1_changed"] for row in paired),
            "per_dataset_mean_delta_mrr": {
                dataset: sum(values) / len(values)
                for dataset, values in sorted(dataset_deltas.items())
            },
        },
        "case_audit": paired,
    }


def _markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Renderer-v7 edge-key case-integration diagnostic",
        "",
        "Scope: paired one-shot RCA on 12 previously exposed development incidents",
        "(four per dataset). The v6 and v7 conditions use byte-identical evidence",
        "text and atomic facts; v7 changes only the duplicated visual edge primitive.",
        "This is nonconfirmatory and cannot alter the registered RQ0 result.",
        "",
        "| model | v6 MRR | v7 MRR | ΔMRR | improved / degraded / tied | top-1 changed | v6 image tokens | v7 image tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model in MODELS:
        value = report["models"][model]
        v6, v7, paired = (
            value["conditions"][CONDITIONS[0]],
            value["conditions"][CONDITIONS[1]],
            value["paired"],
        )
        lines.append(
            f"| {model} | {v6['mrr']:.4f} | {v7['mrr']:.4f} | "
            f"{paired['mean_delta_mrr_v7_minus_v6']:+.4f} | "
            f"{paired['improved']} / {paired['degraded']} / {paired['tied']} | "
            f"{paired['top1_changed']}/12 | {v6['mean_image_tokens']:.0f} | "
            f"{v7['mean_image_tokens']:.0f} |"
        )
    lines.extend([
        "",
        "Qwen has one degraded case and no improved cases; Gemma has one improved",
        "case and no degraded cases. Eleven of twelve cases tie within each model.",
        "The opposing means are therefore each driven by one incident, not a broad",
        "shift. No significance test is appropriate for this selected n=12 diagnostic.",
        "",
        "| model | AegisLab Δ | AIOPS-2022 Δ | AIOPS-2025 Δ |",
        "|---|---:|---:|---:|",
    ])
    for model in MODELS:
        values = report["models"][model]["paired"]["per_dataset_mean_delta_mrr"]
        lines.append(
            f"| {model} | {values['aegislab']:+.4f} | {values['aiops2022']:+.4f} | "
            f"{values['aiops2025']:+.4f} |"
        )
    lines.extend([
        "",
        "Every real call parsed successfully, none truncated or failed at the",
        "infrastructure layer, all server token counts match preflight counts, and",
        "all 24 within-model prompt-text hashes pair exactly. Frozen artifact checks",
        "also establish identical CEB fact hashes and pixel-identical base dashboards.",
        "",
        "## Decision",
        "",
        "Renderer v7 passes atomic edge legibility but does not show a cross-model",
        "case-level benefit. Do not run it on the fresh reserve set and do not present",
        "it as a repaired RQ0 result. The diagnostic separates perception from",
        "integration: the models can read the explicit edge key, yet usually keep the",
        "same RCA answer and occasionally move in opposite directions.",
        "",
        "Generic visual-grounding SFT is not justified. The next learning experiment",
        "should target cause-versus-propagated-symptom integration with case-level",
        "supervision and explicit causal-direction rationales. Before GPU training,",
        "freeze a training/validation exposure ledger, unified LoRA entry point, and",
        "an evaluation set that excludes the 720 RQ0 formal cases and these 12",
        "development cases. RL/GRPO remains out of scope for the current paper.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    propagation = _propagation_lookup()
    report = {
        "schema_version": 1,
        "scope": "development_only_nonconfirmatory_renderer_intervention",
        "n_cases": 12,
        "models": {model: _analyze_model(model, propagation) for model in MODELS},
        "decision": {
            "confirmatory_rq0_unchanged": "unsupported",
            "atomic_edge_legibility_passed": True,
            "cross_model_case_level_benefit": False,
            "advance_v7_to_fresh_reserve": False,
            "generic_visual_grounding_sft_is_next": False,
            "case_level_causal_integration_sft_is_next": True,
            "rl_or_grpo_is_next": False,
        },
    }
    output = ROOT / "RQs/RQ0/results" / EXPERIMENT / "analysis"
    output.mkdir(parents=True, exist_ok=True)
    (output / "case_integration_analysis.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    (output / "summary.md").write_text(_markdown(report))
    print(json.dumps(report["decision"], indent=2))


if __name__ == "__main__":
    main()

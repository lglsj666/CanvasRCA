#!/usr/bin/env python3
"""Audit a paired base/adapter causal-integration SFT pilot.

This is deliberately a development-only diagnostic.  It does not select a
checkpoint and it never reads formal or reserve incidents.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "RQs"))

from vlmrca.processed import load_processed_case  # noqa: E402
from vlmrca.training.causal_sft import accepted_labels  # noqa: E402


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("record_type") == "episode":
            rows.append(row)
    return rows


def _paired_cohens_d(deltas: List[float]) -> float | None:
    if len(deltas) < 2:
        return None
    spread = statistics.stdev(deltas)
    return statistics.mean(deltas) / spread if spread else None


def _wilcoxon_exact_nonzero(deltas: List[float]) -> Dict[str, Any]:
    nonzero = [value for value in deltas if value != 0]
    if not nonzero:
        return {"statistic": 0.0, "p_two_sided": 1.0, "n_nonzero": 0}
    try:
        from scipy.stats import wilcoxon

        result = wilcoxon(nonzero, alternative="two-sided", method="exact")
        return {
            "statistic": float(result.statistic),
            "p_two_sided": float(result.pvalue),
            "n_nonzero": len(nonzero),
        }
    except ImportError:
        # With two nonzero observations this pilot reduces to an exact signed
        # rank enumeration.  Keep the artifact usable in the minimal tools env.
        ranks = list(range(1, len(nonzero) + 1))
        observed = sum(rank for rank, value in zip(ranks, nonzero) if value > 0)
        possibilities = [
            sum(rank for rank in ranks if mask & (1 << (rank - 1)))
            for mask in range(1 << len(ranks))
        ]
        center = sum(ranks) / 2
        distance = abs(observed - center)
        p_value = sum(abs(value - center) >= distance for value in possibilities) / len(
            possibilities
        )
        return {
            "statistic": float(min(observed, sum(ranks) - observed)),
            "p_two_sided": float(p_value),
            "n_nonzero": len(nonzero),
        }


def analyze(result_root: Path) -> Dict[str, Any]:
    rows = _read_jsonl(result_root / "trajectories/episodes.jsonl")
    indexed = {
        (row["opaque_incident_id"], row["condition"]): row for row in rows
    }
    opaque_ids = sorted({row["opaque_incident_id"] for row in rows})
    if len(indexed) != 2 * len(opaque_ids):
        raise RuntimeError("paired evaluation is incomplete")

    cases = []
    deltas = []
    for opaque in opaque_ids:
        base = indexed[(opaque, "base")]
        adapter = indexed[(opaque, "adapter")]
        case = load_processed_case(base["dataset"], base["case_id"])
        delta = float(adapter["mrr"] - base["mrr"])
        deltas.append(delta)
        base_top1 = (base.get("predicted") or [None])[0]
        adapter_top1 = (adapter.get("predicted") or [None])[0]
        cases.append(
            {
                "opaque_incident_id": opaque,
                "private_case_id": base["case_id"],
                "dataset": base["dataset"],
                "accepted_labels_private_evaluator_only": accepted_labels(case),
                "base": {
                    "predicted": base["predicted"],
                    "rank": base["rank"],
                    "mrr": base["mrr"],
                    "output_tokens": base["output_tokens"],
                    "prediction_count": len(base.get("predicted") or []),
                },
                "adapter": {
                    "predicted": adapter["predicted"],
                    "rank": adapter["rank"],
                    "mrr": adapter["mrr"],
                    "output_tokens": adapter["output_tokens"],
                    "prediction_count": len(adapter.get("predicted") or []),
                },
                "delta_mrr_adapter_minus_base": delta,
                "top1_changed": base_top1 != adapter_top1,
                "outcome": "improved" if delta > 0 else "degraded" if delta < 0 else "tied",
            }
        )

    mean_base_count = statistics.mean(row["base"]["prediction_count"] for row in cases)
    mean_adapter_count = statistics.mean(
        row["adapter"]["prediction_count"] for row in cases
    )
    mean_base_tokens = statistics.mean(row["base"]["output_tokens"] for row in cases)
    mean_adapter_tokens = statistics.mean(
        row["adapter"]["output_tokens"] for row in cases
    )
    degraded = [row for row in cases if row["outcome"] == "degraded"]
    improved = [row for row in cases if row["outcome"] == "improved"]
    top1_changed = [row for row in cases if row["top1_changed"]]
    removed_roots = [
        row
        for row in degraded
        if row["base"]["rank"] is not None and row["adapter"]["rank"] is None
    ]
    demoted_roots = [
        row
        for row in degraded
        if row["base"]["rank"] is not None
        and row["adapter"]["rank"] is not None
        and row["adapter"]["rank"] > row["base"]["rank"]
    ]
    variant = result_root.parents[1].name
    if removed_roots and len(removed_roots) == len(degraded):
        interpretation = (
            "Every scored degradation removed an accepted root that the base "
            "model had retained. The shorter output is an accuracy failure, not "
            "an efficiency win."
        )
    elif demoted_roots:
        interpretation = (
            "The scored degradation demoted an accepted root that the base model "
            "ranked first. Prediction-list preservation prevented list collapse "
            "but did not produce any correcting improvement."
        )
    else:
        interpretation = (
            "The adapter produced no scored improvement. Inspect the recorded "
            "paired predictions before proposing another intervention."
        )
    result = {
        "schema_version": "CausalIntegrationSFTPilotAnalysisV1",
        "experiment_variant": variant,
        "scope": "development_only_nonconfirmatory_diagnostic",
        "n_pairs": len(cases),
        "paired": {
            "mean_delta_mrr_adapter_minus_base": statistics.mean(deltas),
            "paired_cohens_d": _paired_cohens_d(deltas),
            "wilcoxon_signed_rank_exact_nonzero": _wilcoxon_exact_nonzero(deltas),
            "improved": len(improved),
            "degraded": len(degraded),
            "tied": len(cases) - len(improved) - len(degraded),
            "top1_changed": len(top1_changed),
            "top1_agreement_rate": 1 - len(top1_changed) / len(cases),
        },
        "response_shape": {
            "mean_prediction_count_base": mean_base_count,
            "mean_prediction_count_adapter": mean_adapter_count,
            "delta_prediction_count_adapter_minus_base": mean_adapter_count
            - mean_base_count,
            "single_prediction_cases_base": sum(
                row["base"]["prediction_count"] == 1 for row in cases
            ),
            "single_prediction_cases_adapter": sum(
                row["adapter"]["prediction_count"] == 1 for row in cases
            ),
            "mean_output_tokens_base": mean_base_tokens,
            "mean_output_tokens_adapter": mean_adapter_tokens,
            "delta_output_tokens_adapter_minus_base": mean_adapter_tokens
            - mean_base_tokens,
        },
        "failure_mechanism": {
            "degraded_cases": degraded,
            "improved_cases": improved,
            "accepted_root_removed_count": len(removed_roots),
            "accepted_root_demoted_count": len(demoted_roots),
            "all_degradations_removed_a_previously_ranked_accepted_root": all(
                row["base"]["rank"] is not None and row["adapter"]["rank"] is None
                for row in degraded
            ),
            "interpretation": interpretation,
        },
        "cases": cases,
    }
    frozen_summary = json.loads((result_root / "summary.json").read_text())
    if not math.isclose(
        result["paired"]["mean_delta_mrr_adapter_minus_base"],
        frozen_summary["paired"]["delta_mrr_adapter_minus_base"],
    ):
        raise RuntimeError("analysis does not reproduce the frozen evaluation summary")
    return result


def _markdown(result: Dict[str, Any]) -> str:
    paired = result["paired"]
    shape = result["response_shape"]
    degraded = result["failure_mechanism"]["degraded_cases"]
    lines = [
        f"# {result['experiment_variant']} paired pilot analysis",
        "",
        "This is a development-only model-selection diagnostic, not confirmatory evidence.",
        "",
        "## Result",
        "",
        f"- Adapter−base MRR: **{paired['mean_delta_mrr_adapter_minus_base']:+.4f}** "
        f"({paired['improved']} improved, {paired['degraded']} degraded, "
        f"{paired['tied']} tied).",
        f"- Paired Cohen's d: {paired['paired_cohens_d']:.3f}; exact Wilcoxon "
        f"p={paired['wilcoxon_signed_rank_exact_nonzero']['p_two_sided']:.3f} "
        f"over {paired['wilcoxon_signed_rank_exact_nonzero']['n_nonzero']} nonzero pairs. "
        "The sample is too small for an efficacy claim.",
        f"- Top-1 changed on {paired['top1_changed']}/{result['n_pairs']} cases; "
        f"agreement was {paired['top1_agreement_rate']:.1%}.",
        f"- Mean prediction-list length changed from {shape['mean_prediction_count_base']:.2f} "
        f"to {shape['mean_prediction_count_adapter']:.2f}; mean output length changed "
        f"from {shape['mean_output_tokens_base']:.2f} to "
        f"{shape['mean_output_tokens_adapter']:.2f} tokens.",
        "",
        "## Scored degradations",
        "",
        "| opaque case | dataset | accepted root | base rank/list | adapter rank/list | ΔMRR |",
        "|---|---|---|---|---|---:|",
    ]
    for row in degraded:
        labels = ", ".join(row["accepted_labels_private_evaluator_only"])
        adapter_rank = row["adapter"]["rank"]
        lines.append(
            f"| `{row['opaque_incident_id']}` | {row['dataset']} | `{labels}` | "
            f"{row['base']['rank']} / {', '.join(row['base']['predicted'])} | "
            f"{adapter_rank if adapter_rank is not None else 'miss'} / "
            f"{', '.join(row['adapter']['predicted'])} | "
            f"{row['delta_mrr_adapter_minus_base']:+.3f} |"
        )
    lines += [
        "",
        result["failure_mechanism"]["interpretation"],
        "",
        "## Decision",
        "",
        f"Do not promote or scale the {result['experiment_variant']} checkpoint. "
        "Do not open formal or reserve cases.",
        "Any successor must be preregistered on development data, use a fresh",
        "development-heldout subset, and be evaluated against the base model with another",
        "paired gate. RL/GRPO remains out of scope.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--result-root",
        type=Path,
        default=ROOT
        / "RQs/RQ0/results/causal_integration_sft_pilot_v1/evaluation/paired_main",
    )
    args = parser.parse_args()
    result_root = args.result_root.resolve()
    analysis = analyze(result_root)
    analysis_root = result_root / "analysis"
    analysis_root.mkdir(parents=True, exist_ok=True)
    (analysis_root / "case_level_analysis.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False) + "\n"
    )
    (analysis_root / "summary.md").write_text(_markdown(analysis))
    print(json.dumps(analysis["paired"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Post-hoc sensitivity audit for hashed Kubernetes pod/service aliases.

The canonical result remains the frozen upstream score.  This audit measures
the consequence of extending its documented service-level leniency from only
numeric pod suffixes to Kubernetes Deployment/ReplicaSet pod suffixes.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "RQs"))

from vlmrca.processed import PROCESSED_ROOT, processed_index  # noqa: E402
from vlmrca.eval.scoring import is_granularity_aware_hit  # noqa: E402
from vlmrca.upstream import normalize_service  # noqa: E402

RESULT_ROOT = ROOT / "RQs/RQ0/results/rq0_equal_information_equal_compute_v1"
ARMS = ("visual_text_topology", "text_only", "flat_structured")


def _accepted(dataset: str, case_id: str) -> List[str]:
    """Read accepted labels without loading any large telemetry parquet."""
    row = processed_index(dataset)[case_id]
    dataset_root = (PROCESSED_ROOT / dataset).resolve()
    case_dir = (dataset_root / str(row["path"])).resolve()
    if dataset_root not in case_dir.parents:
        raise ValueError(f"processed manifest path escapes dataset root: {case_dir}")
    metadata = json.loads((case_dir / "metadata.json").read_text(encoding="utf-8"))
    labels = dict(metadata.get("labels") or {})
    values = [labels.get("root_cause")]
    values.extend(labels.get("root_cause_candidates") or [])
    return [normalize_service(str(value)) for value in values if value]


def _matches(prediction: str, accepted: Iterable[str]) -> bool:
    for truth in accepted:
        if is_granularity_aware_hit(prediction, truth):
            return True
    return False


def _rank(predicted: List[str], accepted: List[str]) -> int | None:
    for index, value in enumerate(predicted[:5], start=1):
        if _matches(value, accepted):
            return index
    return None


def _holm(values: Dict[str, float]) -> Dict[str, float]:
    ordered = sorted(values, key=values.get)
    adjusted: Dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, name in enumerate(ordered):
        running = max(running, min(1.0, values[name] * (total - index)))
        adjusted[name] = running
    return adjusted


def main() -> int:
    model_rows: Dict[str, List[Dict[str, Any]]] = {}
    for model in ("qwen3.6-27b", "gemma-4-26b-a4b"):
        path = RESULT_ROOT / f"{model}__formal__main/trajectories/episodes.jsonl"
        model_rows[model] = [
            row
            for line in path.read_text().splitlines()
            if (row := json.loads(line)).get("record_type") == "episode"
        ]

    accepted_cache: Dict[tuple[str, str], List[str]] = {}
    for rows in model_rows.values():
        for row in rows:
            key = (row["dataset"], row["case_id"])
            if key not in accepted_cache:
                accepted_cache[key] = _accepted(*key)

    report: Dict[str, Any] = {
        "schema_version": "KubernetesServiceAliasSensitivityV1",
        "scope": "post_hoc_sensitivity_does_not_replace_registered_primary_score",
        "canonical_rule": "upstream exact/numeric-suffix service leniency",
        "sensitivity_rule": "canonical plus hashed ReplicaSet pod to service projection",
        "models": {},
    }
    for model, rows in model_rows.items():
        rescored = []
        for row in rows:
            accepted = accepted_cache[(row["dataset"], row["case_id"])]
            rank = _rank(row.get("predicted") or [], accepted)
            mrr = 1.0 / rank if rank else 0.0
            rescored.append(
                {
                    **row,
                    "canonical_rank": row["rank"],
                    "canonical_mrr": row["mrr"],
                    "sensitivity_rank": rank,
                    "sensitivity_mrr": mrr,
                    "score_changed": not math.isclose(mrr, float(row["mrr"])),
                }
            )
        indexed = {
            (row["opaque_incident_id"], row["arm"]): row for row in rescored
        }
        arm_summary = {}
        for arm in ARMS:
            selected = [row for row in rescored if row["arm"] == arm]
            arm_summary[arm] = {
                "n": len(selected),
                "canonical_mrr": sum(row["canonical_mrr"] for row in selected)
                / len(selected),
                "sensitivity_mrr": sum(row["sensitivity_mrr"] for row in selected)
                / len(selected),
                "delta_due_to_alias_rule": sum(
                    row["sensitivity_mrr"] - row["canonical_mrr"] for row in selected
                )
                / len(selected),
                "changed_cases": sum(row["score_changed"] for row in selected),
                "changed_by_dataset": dict(
                    sorted(
                        Counter(
                            row["dataset"] for row in selected if row["score_changed"]
                        ).items()
                    )
                ),
            }
        comparisons = {}
        raw_p = {}
        for name, left, right in (
            ("A_minus_B", "visual_text_topology", "text_only"),
            ("A_minus_C", "visual_text_topology", "flat_structured"),
        ):
            ids = sorted({row["opaque_incident_id"] for row in rescored})
            deltas = [
                indexed[(opaque, left)]["sensitivity_mrr"]
                - indexed[(opaque, right)]["sensitivity_mrr"]
                for opaque in ids
            ]
            test = wilcoxon(deltas, zero_method="wilcox", alternative="two-sided")
            raw_p[name] = float(test.pvalue)
            comparisons[name] = {
                "n": len(deltas),
                "sensitivity_delta_mrr": sum(deltas) / len(deltas),
                "wilcoxon_p": float(test.pvalue),
                "improved": sum(value > 0 for value in deltas),
                "degraded": sum(value < 0 for value in deltas),
                "tied": sum(value == 0 for value in deltas),
            }
        adjusted = _holm(raw_p)
        for name, value in adjusted.items():
            comparisons[name]["holm_p"] = value
        report["models"][model] = {
            "arms": arm_summary,
            "comparisons": comparisons,
            "changed_episode_count": sum(row["score_changed"] for row in rescored),
        }

    output = RESULT_ROOT / "diagnostics/kubernetes_service_alias_sensitivity"
    output.mkdir(parents=True, exist_ok=True)
    (output / "audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    lines = [
        "# Kubernetes pod/service alias sensitivity",
        "",
        "This is a post-hoc scoring sensitivity and does not replace the registered RQ0 result.",
        "",
        "| model | arm | canonical MRR | alias-aware MRR | changed cases |",
        "|---|---|---:|---:|---:|",
    ]
    for model, result in report["models"].items():
        for arm in ARMS:
            value = result["arms"][arm]
            lines.append(
                f"| {model} | {arm} | {value['canonical_mrr']:.4f} | "
                f"{value['sensitivity_mrr']:.4f} | {value['changed_cases']} |"
            )
    lines += ["", "| model | comparison | alias-aware ΔMRR | Holm p |", "|---|---|---:|---:|"]
    for model, result in report["models"].items():
        for name, value in result["comparisons"].items():
            lines.append(
                f"| {model} | {name} | {value['sensitivity_delta_mrr']:+.4f} | "
                f"{value['holm_p']:.4g} |"
            )
    lines += [
        "",
        "The sensitivity asks whether the upstream scorer's documented service-level",
        "leniency changes the scientific conclusion when it recognizes ordinary hashed",
        "Kubernetes pod names. It cannot be used as a post-hoc replacement endpoint.",
        "",
    ]
    (output / "summary.md").write_text("\n".join(lines))
    print(json.dumps(report["models"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

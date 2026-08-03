#!/usr/bin/env python3
"""Descriptive, label-blind-content audit of formal RQ0 A/B discordances.

Ground truth is used only to assign the registered correctness-discordance
groups.  The emitted case roster deliberately omits the label and fault type;
all explanatory features come from the already-frozen CEB and model response.
This is a post-hoc diagnostic, never a new confirmatory analysis.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from vlmrca.upstream import is_service_level_hit, normalize_service

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = "rq0_equal_information_equal_compute_v1"
A = "visual_text_topology"
B = "text_only"

REASON_CUES = {
    "onset": re.compile(r"\b(onset|earliest|preced(?:e|es|ed|ing)|first)\b", re.I),
    "topology": re.compile(
        r"\b(topolog|call(?:er|ee)?|edge|upstream|downstream|propagat|cascade|depend)",
        re.I,
    ),
    "metric": re.compile(
        r"\b(metric|cpu|memory|latency|utilization|usage|disk|network|z[ =-])",
        re.I,
    ),
    "log": re.compile(r"\b(log|error line|exception|timeout|refused|fatal|panic)\b", re.I),
    "trace": re.compile(r"\b(trace|span|p95)\b", re.I),
}


def _episodes(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("record_type") == "episode":
            rows.append(row)
    return rows


def _same_service(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    a, b = normalize_service(left), normalize_service(right)
    return bool(
        is_service_level_hit(a, b)
        or is_service_level_hit(b, a)
    )


def _rank_for_service(entries: Iterable[Dict[str, Any]], service: str | None) -> int | None:
    if not service:
        return None
    for index, entry in enumerate(entries, start=1):
        if _same_service(str(entry.get("service") or ""), service):
            return int(entry.get("rank") or index)
    return None


def _roles(ceb: Dict[str, Any], service: str | None) -> Dict[str, Any]:
    metrics = ceb.get("metric_series") or []
    propagation = ceb.get("propagation", {}).get("services") or []
    logs = ceb.get("log_summary", {}).get("entries") or []
    traces = ceb.get("trace_summary", {}).get("entries") or []
    severity_order = sorted(
        propagation,
        key=lambda row: (
            -float(row.get("severity_z") or 0.0),
            str(row.get("service") or ""),
        ),
    )
    edges = ceb.get("propagation", {}).get("directed_call_edges") or []
    metric_rank = _rank_for_service(metrics, service)
    propagation_rank = _rank_for_service(propagation, service)
    severity_rank = _rank_for_service(severity_order, service)
    log_rank = _rank_for_service(logs, service)
    trace_rank = _rank_for_service(traces, service)
    return {
        "metric_rank": metric_rank,
        "propagation_onset_rank": propagation_rank,
        "propagation_severity_rank": severity_rank,
        "log_rank": log_rank,
        "trace_rank": trace_rank,
        "incident_to_drawn_edge": bool(
            service
            and any(
                _same_service(str(edge.get("caller") or ""), service)
                or _same_service(str(edge.get("callee") or ""), service)
                for edge in edges
            )
        ),
        "is_metric_rank1": metric_rank == 1,
        "is_propagation_onset_rank1": propagation_rank == 1,
        "is_propagation_severity_rank1": severity_rank == 1,
        "is_log_rank1": log_rank == 1,
        "is_trace_rank1": trace_rank == 1,
    }


def _group(a: Dict[str, Any], b: Dict[str, Any]) -> str:
    a_ok, b_ok = bool(a.get("ac1")), bool(b.get("ac1"))
    if b_ok and not a_ok:
        return "b_correct_a_wrong"
    if a_ok and not b_ok:
        return "a_correct_b_wrong"
    if a_ok and b_ok:
        return "both_correct"
    return "both_wrong"


def _cue_flags(response: str) -> Dict[str, bool]:
    return {name: bool(pattern.search(response or "")) for name, pattern in REASON_CUES.items()}


def _fraction(records: List[Dict[str, Any]], pointer: str) -> float | None:
    if not records:
        return None
    keys = pointer.split(".")
    values = []
    for record in records:
        value: Any = record
        for key in keys:
            value = value[key]
        values.append(bool(value))
    return sum(values) / len(values)


def _aggregate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    groups = Counter(row["group"] for row in records)
    changed = [row for row in records if row["top1_changed"]]
    by_group: Dict[str, Any] = {}
    for group in sorted(groups):
        selected = [row for row in records if row["group"] == group]
        selected_changed = [row for row in selected if row["top1_changed"]]
        by_group[group] = {
            "n": len(selected),
            "top1_changed_n": len(selected_changed),
            "a_new_top1_salience": {
                field: _fraction(selected_changed, f"a_top1_roles.{field}")
                for field in (
                    "is_metric_rank1",
                    "is_propagation_onset_rank1",
                    "is_propagation_severity_rank1",
                    "is_log_rank1",
                    "is_trace_rank1",
                    "incident_to_drawn_edge",
                )
            },
            "a_reason_cue_rate": {
                cue: _fraction(selected, f"a_reason_cues.{cue}") for cue in REASON_CUES
            },
            "b_reason_cue_rate": {
                cue: _fraction(selected, f"b_reason_cues.{cue}") for cue in REASON_CUES
            },
        }
    return {
        "n_cases": len(records),
        "top1_changed_n": len(changed),
        "top1_changed_rate": len(changed) / len(records) if records else None,
        "group_counts": dict(sorted(groups.items())),
        "by_dataset": {
            dataset: dict(
                sorted(Counter(row["group"] for row in records if row["dataset"] == dataset).items())
            )
            for dataset in sorted({row["dataset"] for row in records})
        },
        "by_group": by_group,
    }


def _markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# RQ0 A/B discordance audit",
        "",
        "This is a descriptive post-hoc diagnostic. Ground truth was used only to",
        "assign correctness groups; the case-level audit roster contains no label or",
        "fault type and was not used to modify the formal experiment.",
        "",
        "| model | top-1 changed | B correct/A wrong | A correct/B wrong | both wrong |",
        "|---|---:|---:|---:|---:|",
    ]
    for model, summary in report["models"].items():
        groups = summary["aggregate"]["group_counts"]
        lines.append(
            f"| {model} | {summary['aggregate']['top1_changed_n']}/720 "
            f"({summary['aggregate']['top1_changed_rate']:.1%}) | "
            f"{groups.get('b_correct_a_wrong', 0)} | "
            f"{groups.get('a_correct_b_wrong', 0)} | "
            f"{groups.get('both_wrong', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Salience signatures when the image breaks a text-correct answer",
            "",
            "Fractions below describe the new A top-1 target among cases where B was",
            "top-1 correct and A was wrong. Rank-1 fields are derived from the frozen",
            "CEB; they are not causal attributions.",
            "",
            "| model | metric #1 | onset #1 | severity #1 | log #1 | trace #1 | drawn-edge endpoint |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    fields = (
        "is_metric_rank1",
        "is_propagation_onset_rank1",
        "is_propagation_severity_rank1",
        "is_log_rank1",
        "is_trace_rank1",
        "incident_to_drawn_edge",
    )
    for model, summary in report["models"].items():
        group = summary["aggregate"]["by_group"].get("b_correct_a_wrong", {})
        salience = group.get("a_new_top1_salience", {})
        values = [salience.get(field) for field in fields]
        formatted = ["n/a" if value is None else f"{value:.1%}" for value in values]
        lines.append(f"| {model} | " + " | ".join(formatted) + " |")
    lines.extend(
        [
            "",
            "Machine-readable aggregates and the label-omitting case roster are in",
            "`discordance_audit.json`. These patterns are hypothesis-generating only.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models", nargs="+", default=["qwen3.6-27b", "gemma-4-26b-a4b"]
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "RQs/RQ0/results" / EXPERIMENT / "diagnostics" / "discordance",
    )
    args = parser.parse_args()

    qualification = ROOT / "RQs/RQ0/results" / EXPERIMENT / "qualification_formal" / "evidence"
    report: Dict[str, Any] = {
        "schema_version": 1,
        "scope": "posthoc_descriptive_label_blind_content_audit",
        "formal_results_are_read_only": True,
        "selection_uses_ground_truth_only_for_correctness_group": True,
        "case_roster_omits_ground_truth_and_fault_type": True,
        "models": {},
    }
    for model in args.models:
        trajectory = (
            ROOT
            / "RQs/RQ0/results"
            / EXPERIMENT
            / f"{model}__formal__main"
            / "trajectories"
            / "episodes.jsonl"
        )
        rows = _episodes(trajectory)
        index = {(row["opaque_incident_id"], row["arm"]): row for row in rows}
        records = []
        for opaque_id in sorted({row["opaque_incident_id"] for row in rows}):
            a, b = index[(opaque_id, A)], index[(opaque_id, B)]
            a_top = (a.get("predicted") or [None])[0]
            b_top = (b.get("predicted") or [None])[0]
            ceb = json.loads((qualification / f"{opaque_id}.ceb.json").read_text())
            records.append(
                {
                    "opaque_incident_id": opaque_id,
                    "dataset": a["dataset"],
                    "group": _group(a, b),
                    "top1_changed": not _same_service(a_top, b_top),
                    "a_top1": a_top,
                    "b_top1": b_top,
                    "a_mrr": float(a["mrr"]),
                    "b_mrr": float(b["mrr"]),
                    "a_top1_roles": _roles(ceb, a_top),
                    "b_top1_roles": _roles(ceb, b_top),
                    "a_reason_cues": _cue_flags(a.get("response") or ""),
                    "b_reason_cues": _cue_flags(b.get("response") or ""),
                    "ceb_hash": ceb["ceb_hash"],
                }
            )
        report["models"][model] = {
            "trajectory": str(trajectory.relative_to(ROOT)),
            "aggregate": _aggregate(records),
            "case_roster": records,
        }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "discordance_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    (args.output / "summary.md").write_text(_markdown(report))
    print(json.dumps({
        "output": str(args.output),
        "models": {
            model: value["aggregate"]["group_counts"]
            for model, value in report["models"].items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()

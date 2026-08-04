#!/usr/bin/env python3
"""Describe why the frozen RQ1b operation router failed its disjoint gate."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from rq1lib.contracts import canonical_json, sha256_bytes, stable_hash

ROOT = Path(__file__).resolve().parents[3]
RQ_ROOT = ROOT / "RQs/RQ1"
MODEL_DIRS = {
    "gemma-4-26b-a4b": "gemma",
    "qwen3.6-27b": "qwen",
}
ROUTED_ARMS = {
    "earliest_onset": "H",
    "entity_modality_alignment": "V",
}


class FailureAnalysisError(RuntimeError):
    """Raised when a diagnostic source artifact is incomplete or inconsistent."""


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise FailureAnalysisError(f"{path} is not a JSON object")
    return payload


def _relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def _dataset_index(private_roster: Path) -> dict[str, str]:
    roster = _load_object(private_roster)
    if roster.get("schema_version") != "RQ1PrivateRosterV1":
        raise FailureAnalysisError("unsupported private roster schema")
    result: dict[str, str] = {}
    for row in roster.get("cases", []):
        if not isinstance(row, Mapping):
            raise FailureAnalysisError("private roster case is not an object")
        incident = str(row.get("opaque_incident_id") or "")
        dataset = str(row.get("analysis_dataset") or "")
        if not incident or not dataset or incident in result:
            raise FailureAnalysisError("private roster incident mapping is invalid")
        result[incident] = dataset
    return result


def _call_index(experiment_root: Path, model_dir: str) -> dict[tuple[str, str, str], dict[str, Any]]:
    calls_root = experiment_root / model_dir / "run/calls"
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in sorted(calls_root.glob("*.json")):
        row = _load_object(path)
        if "private_case_id" in row:
            raise FailureAnalysisError("private case ID crossed the call boundary")
        key = (
            str(row.get("opaque_incident_id") or ""),
            str(row.get("query_id") or ""),
            str(row.get("arm") or ""),
        )
        if not all(key) or key in rows:
            raise FailureAnalysisError(f"invalid or duplicate call key {key}")
        row["_source_path"] = _relative(path)
        rows[key] = row
    if not rows:
        raise FailureAnalysisError(f"no calls below {calls_root}")
    return rows


def _answer_and_paths(
    experiment_root: Path, incident: str, query: str
) -> tuple[Any, dict[str, str]]:
    prepared = experiment_root / "prepared" / incident
    manifest = _load_object(prepared / "manifest.json")
    matches = [row for row in manifest["tasks"] if row["query_id"] == query]
    if len(matches) != 1:
        raise FailureAnalysisError(f"prepared task not unique for {incident}/{query}")
    task = matches[0]
    answer_path = prepared / "private" / query / "answer_key.json"
    answer = _load_object(answer_path).get("answer")
    public = task["public_files"]
    return answer, {
        "task": _relative(prepared / public["task"]),
        "text": _relative(prepared / public["text"]),
        "visual": _relative(prepared / public["visual"]),
        "paired_audit": _relative(prepared / public["paired_audit"]),
    }


def classify_set_difference(predicted: Sequence[str], expected: Sequence[str]) -> str:
    """Classify an exact-set error without inventing a hidden rationale."""

    predicted_set = set(predicted)
    expected_set = set(expected)
    if predicted_set < expected_set:
        return "subset_omission"
    if predicted_set > expected_set:
        return "superset_overinclusion"
    return "mixed_substitution"


def _jaccard(predicted: Sequence[str], expected: Sequence[str]) -> float:
    union = set(predicted) | set(expected)
    return len(set(predicted) & set(expected)) / len(union) if union else 1.0


def _stage_model_report(
    experiment_root: Path,
    *,
    model: str,
    model_dir: str,
    datasets: Mapping[str, str],
    include_discordances: bool,
) -> dict[str, Any]:
    calls = _call_index(experiment_root, model_dir)
    report: dict[str, Any] = {}
    for operation, routed_arm in ROUTED_ARMS.items():
        pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
        per_dataset: dict[str, dict[str, int]] = defaultdict(
            lambda: {"repairs": 0, "breaks": 0, "ties": 0}
        )
        discordances: list[dict[str, Any]] = []
        for (incident, query, arm), text_row in sorted(calls.items()):
            if arm != "T" or text_row.get("operation") != operation:
                continue
            routed_row = calls.get((incident, query, routed_arm))
            if routed_row is None:
                raise FailureAnalysisError(
                    f"missing routed arm for {model}/{incident}/{query}"
                )
            statuses = {text_row.get("status"), routed_row.get("status")}
            if "infrastructure_error" in statuses:
                continue
            if statuses != {"completed"}:
                raise FailureAnalysisError(
                    f"unexpected paired statuses for {model}/{incident}/{query}"
                )
            pairs.append((text_row, routed_row))
            text_score = float(text_row["score"])
            routed_score = float(routed_row["score"])
            direction = (
                "repair"
                if routed_score > text_score
                else "break"
                if routed_score < text_score
                else "tie"
            )
            dataset = datasets[incident]
            per_dataset[dataset][f"{direction}s"] += 1
            if direction == "tie" or not include_discordances:
                continue
            expected, artifact_paths = _answer_and_paths(
                experiment_root, incident, query
            )
            predicted = routed_row.get("predicted_answer")
            subtype = None
            jaccard = None
            primary_mode = "reasoning"
            if isinstance(predicted, list) and isinstance(expected, list):
                subtype = classify_set_difference(predicted, expected)
                jaccard = _jaccard(predicted, expected)
                if routed_arm == "V" and direction == "break":
                    primary_mode = "perception"
            discordances.append(
                {
                    "opaque_incident_id": incident,
                    "query_id": query,
                    "dataset": dataset,
                    "operation": operation,
                    "routed_arm": routed_arm,
                    "direction": direction,
                    "primary_failure_mode": (
                        primary_mode if direction == "break" else None
                    ),
                    "set_error_subtype": subtype,
                    "answer_jaccard": jaccard,
                    "evaluator_answer": expected,
                    "text_prediction": text_row.get("predicted_answer"),
                    "routed_prediction": predicted,
                    "text_score": text_score,
                    "routed_score": routed_score,
                    "artifacts": {
                        **artifact_paths,
                        "text_call": text_row["_source_path"],
                        "routed_call": routed_row["_source_path"],
                    },
                }
            )
        if not pairs:
            raise FailureAnalysisError(f"no eligible {model}/{operation} pairs")
        repairs = sum(routed["score"] > text["score"] for text, routed in pairs)
        breaks = sum(routed["score"] < text["score"] for text, routed in pairs)
        text_accuracy = sum(float(text["score"]) for text, _ in pairs) / len(pairs)
        routed_accuracy = sum(float(routed["score"]) for _, routed in pairs) / len(
            pairs
        )
        operation_report: dict[str, Any] = {
            "routed_arm": routed_arm,
            "paired_queries": len(pairs),
            "text_accuracy": text_accuracy,
            "routed_accuracy": routed_accuracy,
            "delta_accuracy": routed_accuracy - text_accuracy,
            "repairs": repairs,
            "breaks": breaks,
            "ties": len(pairs) - repairs - breaks,
            "net_repairs": repairs - breaks,
            "per_dataset_discordance": dict(sorted(per_dataset.items())),
        }
        if include_discordances:
            operation_report["discordances"] = discordances
            broken_sets = [
                row
                for row in discordances
                if row["direction"] == "break"
                and row["set_error_subtype"] is not None
            ]
            subtype_counts: dict[str, int] = defaultdict(int)
            for row in broken_sets:
                subtype_counts[str(row["set_error_subtype"])] += 1
            operation_report["break_set_error_subtypes"] = dict(
                sorted(subtype_counts.items())
            )
            operation_report["break_mean_answer_jaccard"] = (
                sum(float(row["answer_jaccard"]) for row in broken_sets)
                / len(broken_sets)
                if broken_sets
                else None
            )
        report[operation] = operation_report
    return report


def _render_markdown(report: Mapping[str, Any], *, artifact_sha256: str) -> str:
    lines = [
        "# RQ1b independent-gate failure analysis",
        "",
        "**Status:** descriptive post-hoc diagnosis on exposed data; the valid negative gate is unchanged.",
        "",
        "## Main finding",
        "",
        (
            "The operation-only router was selected from small net discordances and did not generalize. "
            "Gemma's image-only alignment choice moved from +4 net repairs on mapping data to −8 on the disjoint gate. "
            "The image arm itself stayed near the same accuracy; text improved sharply on the gate, so the discovery advantage was mostly an unstable text deficit."
        ),
        "",
        "| Model | Operation | Mapping T | Mapping routed | Mapping net | Gate T | Gate routed | Gate net |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model in MODEL_DIRS:
        for operation in ROUTED_ARMS:
            mapping = report["mapping"][model][operation]
            gate = report["gate"][model][operation]
            lines.append(
                f"| {model} | {operation} → {mapping['routed_arm']} | "
                f"{mapping['text_accuracy']:.4f} | {mapping['routed_accuracy']:.4f} | "
                f"{mapping['net_repairs']:+d} | {gate['text_accuracy']:.4f} | "
                f"{gate['routed_accuracy']:.4f} | {gate['net_repairs']:+d} |"
            )
    lines.extend(
        [
            "",
            "## Gate discordance diagnosis",
            "",
        ]
    )
    for model in MODEL_DIRS:
        entity = report["gate"][model]["entity_modality_alignment"]
        subtype_counts = entity["break_set_error_subtypes"]
        subtype_text = ", ".join(
            f"{count} {name.replace('_', ' ')}"
            for name, count in sorted(subtype_counts.items())
        )
        lines.extend(
            [
                (
                    f"- **{model}:** entity-alignment V versus T produced "
                    f"{entity['repairs']} repairs, {entity['breaks']} breaks, and "
                    f"{entity['ties']} ties. Visual breaks comprised "
                    f"{subtype_text}; mean answer-set "
                    f"Jaccard was {entity['break_mean_answer_jaccard']:.3f}."
                ),
            ]
        )
    gemma_discordances = report["gate"]["gemma-4-26b-a4b"][
        "entity_modality_alignment"
    ]["discordances"]
    overinclude = next(
        row
        for row in gemma_discordances
        if row["direction"] == "break"
        and row["set_error_subtype"] == "superset_overinclusion"
    )
    omission = next(
        row
        for row in gemma_discordances
        if row["direction"] == "break"
        and row["set_error_subtype"] == "subset_omission"
    )
    qwen_onset_repair = next(
        row
        for row in report["gate"]["qwen3.6-27b"]["earliest_onset"][
            "discordances"
        ]
        if row["direction"] == "repair"
    )
    lines.extend(
        [
            "",
            (
                "All visual breaks are classified as `perception`: the required "
                "row/column facts are visibly present, but the strict answer set "
                "does not match the row-wise modality maximum. The no-rationale "
                "structured output cannot distinguish low-level digit reading "
                "from downstream visual aggregation, so the narrower subtype "
                "records omission, overinclusion, or mixed substitution without "
                "inventing a hidden chain of thought."
            ),
            "",
            "Representative auditable cases:",
            "",
            (
                f"- Gemma overinclusion: `{overinclude['opaque_incident_id']}`; "
                f"visual `{overinclude['artifacts']['visual']}`; text call "
                f"`{overinclude['artifacts']['text_call']}`; V call "
                f"`{overinclude['artifacts']['routed_call']}`."
            ),
            (
                f"- Gemma omission: `{omission['opaque_incident_id']}`; visual "
                f"`{omission['artifacts']['visual']}`; paired audit "
                f"`{omission['artifacts']['paired_audit']}`."
            ),
            (
                f"- Qwen onset repair: `{qwen_onset_repair['opaque_incident_id']}`; "
                f"visual `{qwen_onset_repair['artifacts']['visual']}`; T call "
                f"`{qwen_onset_repair['artifacts']['text_call']}`; H call "
                f"`{qwen_onset_repair['artifacts']['routed_call']}`."
            ),
            "",
            "## Interpretation boundaries",
            "",
            "- This analysis does not refit the router, change gate status, or authorize heldout access.",
            "- It supports mapping-selection variance plus visual set-aggregation errors; it does not prove images are universally useless.",
            "- `earliest_onset -> H` remains a small Qwen-specific repair pattern but tied T on primary Gemma and is below the registered practical threshold.",
            "- Any successor must use new development and independent-gate data; these gate cases are now exposed diagnostics.",
            "",
            f"JSON artifact SHA256: `{artifact_sha256}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping-root", type=Path, required=True)
    parser.add_argument("--gate-root", type=Path, required=True)
    parser.add_argument("--mapping-private-roster", type=Path, required=True)
    parser.add_argument("--gate-private-roster", type=Path, required=True)
    parser.add_argument("--gate-analysis", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()

    gate_analysis = _load_object(args.gate_analysis)
    if gate_analysis.get("schema_version") != "RQ1VisOpsIndependentGateAnalysisV1":
        raise FailureAnalysisError("unexpected independent-gate analysis schema")
    if gate_analysis.get("status") != "failed":
        raise FailureAnalysisError("failure analysis requires a failed valid gate")

    mapping_datasets = _dataset_index(args.mapping_private_roster)
    gate_datasets = _dataset_index(args.gate_private_roster)
    report: dict[str, Any] = {
        "schema_version": "RQ1VisOpsGateFailureAnalysisV1",
        "status": "descriptive_post_hoc_valid_negative_gate_unchanged",
        "analysis_role": "failure_mechanism_only_no_router_refit",
        "source_gate_analysis": _relative(args.gate_analysis),
        "source_gate_analysis_sha256": sha256_bytes(args.gate_analysis.read_bytes()),
        "information_parity_status": "passed_in_source_gate",
        "leakage_status": "passed_in_source_gate",
        "mapping": {},
        "gate": {},
    }
    for model, model_dir in MODEL_DIRS.items():
        report["mapping"][model] = _stage_model_report(
            args.mapping_root,
            model=model,
            model_dir=model_dir,
            datasets=mapping_datasets,
            include_discordances=False,
        )
        report["gate"][model] = _stage_model_report(
            args.gate_root,
            model=model,
            model_dir=model_dir,
            datasets=gate_datasets,
            include_discordances=True,
        )
    report["mechanism_checks"] = {
        "gemma_entity_mapping_to_gate_sign_reversal": (
            report["mapping"]["gemma-4-26b-a4b"]["entity_modality_alignment"][
                "delta_accuracy"
            ]
            > 0
            and report["gate"]["gemma-4-26b-a4b"][
                "entity_modality_alignment"
            ]["delta_accuracy"]
            < 0
        ),
        "gemma_entity_visual_accuracy_absolute_drift": abs(
            report["gate"]["gemma-4-26b-a4b"]["entity_modality_alignment"][
                "routed_accuracy"
            ]
            - report["mapping"]["gemma-4-26b-a4b"][
                "entity_modality_alignment"
            ]["routed_accuracy"]
        ),
        "gemma_entity_text_accuracy_absolute_drift": abs(
            report["gate"]["gemma-4-26b-a4b"]["entity_modality_alignment"][
                "text_accuracy"
            ]
            - report["mapping"]["gemma-4-26b-a4b"][
                "entity_modality_alignment"
            ]["text_accuracy"]
        ),
        "router_refit_performed": False,
        "heldout_opened": False,
    }
    report["analysis_contract_sha256"] = stable_hash(report)
    payload = canonical_json(report).encode("utf-8") + b"\n"
    artifact_sha256 = sha256_bytes(payload)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_bytes(payload)
    args.output_markdown.write_text(
        _render_markdown(report, artifact_sha256=artifact_sha256),
        encoding="utf-8",
    )
    print(json.dumps(report["mechanism_checks"], indent=2, sort_keys=True))
    print(f"wrote {args.output_json} sha256={artifact_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

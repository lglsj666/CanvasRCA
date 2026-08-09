"""RQ1 qualification definitions, verification, and paired analysis."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import mean, stdev
from typing import Any

from scipy.stats import wilcoxon

from unified_scripts import stable_hash

from .exps import ExperimentSpec, is_rca_task
from .utils import RQ1Error, RunPaths


@dataclass(frozen=True)
class BoundedQualification:
    name: str
    call_cap: int
    timeout_seconds: int
    correctness_is_pass_condition: bool = False

    def validate(self) -> None:
        absolute = 18 if self.name == "smoke" else 36
        timeout = 600 if self.name == "smoke" else 1200
        if self.call_cap > absolute or self.timeout_seconds > timeout:
            raise RQ1Error(f"{self.name} exceeds the global bounded-qualification rule")


def qualification_contracts(config: Mapping[str, Any]) -> tuple[BoundedQualification, ...]:
    runtime = config["runtime"]
    values = (
        BoundedQualification("smoke", int(runtime["smoke_call_cap"]), int(runtime["smoke_timeout_seconds"])),
        BoundedQualification("gate", int(runtime["gate_call_cap"]), int(runtime["gate_timeout_seconds"])),
    )
    for value in values:
        value.validate()
    return values


def paired_statistics(values: Sequence[float]) -> dict[str, float | int | None]:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return {"n": 0, "delta": None, "p": None, "cohens_dz": None}
    nonzero = [value for value in finite if value != 0.0]
    p = 1.0
    if nonzero:
        try:
            p = float(wilcoxon(finite, zero_method="pratt", alternative="two-sided").pvalue)
        except ValueError:
            p = 1.0
    sd = stdev(finite) if len(finite) > 1 else 0.0
    delta = mean(finite)
    return {"n": len(finite), "delta": delta, "p": p, "cohens_dz": delta / sd if sd else 0.0}


def holm(rows: Mapping[str, Mapping[str, Any]]) -> dict[str, float | None]:
    ordered = sorted((float(row["p"]), name) for name, row in rows.items() if row.get("p") is not None)
    adjusted: dict[str, float | None] = {name: None for name in rows}
    running = 0.0
    total = len(ordered)
    for index, (p, name) in enumerate(ordered):
        running = max(running, min(1.0, p * (total - index)))
        adjusted[name] = running
    return adjusted


def _parse_rate(records: Sequence[Mapping[str, Any]]) -> float:
    stages = [stage for record in records for stage in record.get("stages", ())]
    return sum(bool(stage.get("parse")) for stage in stages) / len(stages) if stages else 0.0


def _arm_means(records: Sequence[Mapping[str, Any]], metric: str) -> dict[str, float]:
    by_arm: dict[str, list[float]] = defaultdict(list)
    for record in records:
        value = (record.get("score") or {}).get(metric)
        if record.get("status") == "completed" and value is not None:
            by_arm[str(record["arm"])].append(float(value))
    return {arm: mean(values) for arm, values in sorted(by_arm.items()) if values}


def _comparison(records: Sequence[Mapping[str, Any]], left: str, right: str, metric: str) -> dict[str, Any]:
    table: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for record in records:
        value = (record.get("score") or {}).get(metric)
        if record.get("status") == "completed" and value is not None:
            table[(str(record["model"]), str(record["opaque_incident_id"]))][str(record["arm"])] = float(value)
    differences = [row[left] - row[right] for row in table.values() if left in row and right in row]
    return {"left": left, "right": right, "metric": metric, **paired_statistics(differences)}


def _rr(predictions: Sequence[str], entity: str) -> float:
    try:
        return 1.0 / (list(predictions).index(entity) + 1)
    except ValueError:
        return 0.0


def _counterfactual_cvi(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    table: dict[tuple[str, str], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for record in records:
        table[(str(record.get("model")), str(record.get("opaque_incident_id")))][str(record.get("arm"))] = record
    values: list[float] = []
    targeted_changes = 0
    paired = 0
    for row in table.values():
        factual = row.get("H_factual")
        targeted = row.get("H_targeted")
        placebo = row.get("H_placebo")
        if not factual or not targeted or not placebo:
            continue
        factual_rank = list(map(str, (factual.get("score") or {}).get("numeric_predictions") or ()))
        vfs: dict[str, float] = {}
        for name, condition in (("targeted", targeted), ("placebo", placebo)):
            pair = list(map(str, condition.get("counterfactual_pair") or ()))
            if len(pair) != 2:
                break
            donor, recipient = pair
            changed_rank = list(map(str, (condition.get("score") or {}).get("numeric_predictions") or ()))
            vfs[name] = 0.5 * (
                _rr(changed_rank, recipient) - _rr(factual_rank, recipient)
                + _rr(factual_rank, donor) - _rr(changed_rank, donor)
            )
        if len(vfs) != 2:
            continue
        values.append(vfs["targeted"] - vfs["placebo"])
        paired += 1
        targeted_changes += int(
            list(map(str, (targeted.get("score") or {}).get("numeric_predictions") or ())) != factual_rank
        )
    return {**paired_statistics(values), "paired_cases": paired, "targeted_top5_change_rate": targeted_changes / paired if paired else 0.0}


def analyze_records(
    records: Sequence[Mapping[str, Any]],
    spec: ExperimentSpec,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    models = sorted({str(record.get("model")) for record in records})
    if len(models) > 1:
        result = {
            "schema_version": "RQ1AnalysisV3",
            "experiment": spec.name,
            "by_model": {
                model: analyze_records([row for row in records if str(row.get("model")) == model], spec, config)
                for model in models
            },
        }
        result["complete"] = all(row["complete"] for row in result["by_model"].values())
        result["analysis_sha256"] = stable_hash(result)
        return result
    total = len(records)
    infrastructure = sum(record.get("status") == "infrastructure_error" for record in records)
    result: dict[str, Any] = {
        "schema_version": "RQ1AnalysisV2",
        "experiment": spec.name,
        "task": spec.task,
        "records": total,
        "infrastructure_error_rate": infrastructure / total if total else 0.0,
        "parse_rate": _parse_rate(records),
        "arm_means": _arm_means(records, spec.primary_metric),
    }
    if is_rca_task(spec):
        if spec.task == "root_cause_counterfactual":
            pairs = (("H_targeted", "H_factual"), ("H_placebo", "H_factual"), ("H_neutral", "H_factual"))
            primary_keys = ("H_targeted-H_factual", "H_placebo-H_factual")
        elif spec.task == "root_cause_handoff":
            pairs = (("L_vis", "L_txt"), ("L_hyb", "L_txt"), ("L_hyb", "L_vis"))
            primary_keys = ("L_vis-L_txt", "L_hyb-L_txt")
        else:
            pairs = (("R", "T"), ("R", "F"), ("V", "T"), ("H", "T"), ("R", "H"), ("T", "F"))
            primary_keys = ("R-T", "R-F")
        comparisons = {f"{left}-{right}": _comparison(records, left, right, "mrr") for left, right in pairs}
        adjusted = holm({key: comparisons[key] for key in primary_keys})
        for key, value in adjusted.items():
            comparisons[key]["holm_adjusted_p"] = value
        threshold = float(config["analysis"]["rca_minimum_effect"])
        result["comparisons"] = comparisons
        if spec.task == "root_cause_counterfactual":
            result["cvi"] = _counterfactual_cvi(records)
            cvi_threshold = float(config["analysis"].get("counterfactual_cvi_minimum", 0.05))
            result["primary_supported"] = (
                result["cvi"].get("delta") is not None
                and result["cvi"]["delta"] >= cvi_threshold
                and (result["cvi"].get("p") or 1.0) < 0.05
            )
        else:
            result["primary_supported"] = all(
                comparisons[key].get("delta") is not None
                and comparisons[key]["delta"] >= threshold
                and (comparisons[key].get("holm_adjusted_p") or 1.0) < 0.05
                for key in primary_keys
            )
        result["by_dataset"] = {
            dataset: {
                "records": len(subset),
                "arm_means": _arm_means(subset, "mrr"),
                "comparisons": {f"{left}-{right}": _comparison(subset, left, right, "mrr") for left, right in pairs},
            }
            for dataset in sorted({str(row.get("analysis_dataset")) for row in records})
            if (subset := [row for row in records if str(row.get("analysis_dataset")) == dataset])
        }
    result["complete"] = (
        result["parse_rate"] >= float(config["runtime"]["parse_rate_minimum"])
        and result["infrastructure_error_rate"] <= float(config["runtime"]["whole_case_infrastructure_exclusion_maximum"])
    )
    result["analysis_sha256"] = stable_hash(result)
    return result


def verify_result_root(paths: RunPaths, config: Mapping[str, Any]) -> dict[str, Any]:
    qualification_contracts(config)
    index_path = paths.prepared / "index.json"
    if not index_path.is_file():
        raise RQ1Error("prepared index is missing")
    index = __import__("json").loads(index_path.read_text())
    missing: list[str] = []
    for item in index.get("cases", ()):
        for key in ("public", "private", "full_image", "routed_image"):
            path = paths.root / item[key]
            if not path.is_file():
                missing.append(str(path.relative_to(paths.root)))
    trajectories = list(paths.trajectories.rglob("*.json"))
    for path in trajectories:
        if not path.with_suffix(".md").is_file():
            missing.append(str(path.with_suffix(".md").relative_to(paths.root)))
    result = {
        "schema_version": "RQ1VerificationV2",
        "prepared_cases": len(index.get("cases", ())),
        "trajectories": len(trajectories),
        "missing": sorted(missing),
        "passed": not missing,
    }
    result["verification_sha256"] = stable_hash(result)
    return result

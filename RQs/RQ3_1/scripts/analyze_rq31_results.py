#!/usr/bin/env python3
"""Reproducible quantitative and qualitative analysis for completed RQ3.1.

This script is deliberately read-only with respect to experiment artifacts.  It
reconstructs tables from per-call summaries, uses evaluator-private context only
for offline stratification, and writes derived analysis assets under docs/.
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import wilcoxon

from vlmrca.eval.scoring import is_granularity_aware_hit

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "RQs/RQ3_1/results/formal_direct_per_case_v3_text_contrast"
CONTEXTS = ROOT / "RQs/RQ3_1/results/formal_contexts_test_direct_per_case_v3_text_contrast/cases"
SPLIT = ROOT / "RQs/RQ3_1/results/data_registration_v1/private/split.json"
DEFAULT_OUT = ROOT / "docs/RQ3_1_Results_Analysis_2026-09-19_assets"

MODELS = ("qwen3.8-27b", "gemma-4-26b-a4b")
FINAL_ARMS = (
    "T", "T_COMPACT", "TPV", "SIRCL_TEXT", "X_C", "X_C_TABLE",
    "X_V_CONTRAST", "X_MTEXT",
)
VISUALS = ("X_V_CONTRAST", "X_MTEXT")
CONTROLS = ("T", "T_COMPACT", "TPV", "SIRCL_TEXT", "X_C", "X_C_TABLE")


def load_summary(experiment: str) -> dict[str, Any]:
    return json.loads((RUN / experiment / "summary.json").read_text())


def records_frame(experiment: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for record in load_summary(experiment)["records"]:
        row = {
            "experiment": experiment,
            "case": record["opaque_incident_id"],
            "dataset": record["dataset"],
            "fault_type": record.get("fault_type"),
            "model": record["model"],
            "status": record["status"],
            "score_status": record["score_status"],
            "error": record.get("error"),
            "input_tokens": record.get("input_tokens"),
            "output_tokens": record.get("output_tokens"),
            "total_tokens": record.get("total_tokens"),
            "wall_time_s": record.get("wall_time_s"),
        }
        row.update(record.get("dimensions") or {})
        row.update(record.get("metrics") or {})
        rows.append(row)
    return pd.DataFrame(rows)


def load_final_calls() -> pd.DataFrame:
    root = RUN / "exp_final_test"
    rows: list[dict[str, Any]] = []
    for output_path in sorted((root / "outputs").glob("*.json")):
        output = json.loads(output_path.read_text())
        key = output["call_key"]
        cost = json.loads((root / "cost" / f"{key}.json").read_text())
        response = output.get("response") or ""
        parsed: dict[str, Any] = {}
        try:
            parsed = json.loads(response)
        except (TypeError, json.JSONDecodeError):
            pass
        services = parsed.get("services") if isinstance(parsed, dict) else None
        if not isinstance(services, list):
            services = []
        reason = parsed.get("reason", "") if isinstance(parsed, dict) else ""
        if not isinstance(reason, str):
            reason = str(reason)
        metrics = output["score"]["metrics"]
        rows.append({
            "call_key": key,
            "case": output["opaque_incident_id"],
            "dataset": output["dataset"],
            "fault_type": output.get("fault_type"),
            "model": output["model"],
            "arm": output["dimensions"]["method"],
            "status": output["status"],
            "score_status": output["score"]["status"],
            "error": output["score"].get("error"),
            **metrics,
            "input_tokens": cost["input_tokens"],
            "text_tokens": cost.get("text_tokens", cost["input_tokens"]),
            "image_tokens": cost.get("image_tokens", 0),
            "output_tokens": cost["output_tokens"],
            "total_tokens": cost["total_tokens"],
            "wall_time_s": cost["wall_time_s"],
            "reused": bool(cost.get("reused")),
            "predicted_count": len(services),
            "predicted_ids": json.dumps(services, ensure_ascii=False),
            "reason": reason,
            "reason_entity_ids": json.dumps(sorted(set(re.findall(r"(?<!\d)\d{3,5}(?!\d)", reason)))),
            "reason_observation_refs": len(set(re.findall(r"\b[OC]\d{1,3}\b", reason))),
            "conversation_path": str((root / "conversations" / f"{key}.md").resolve()),
            "render_glob": str((root / "renders" / f"{key}_*.png").resolve()),
        })
    return pd.DataFrame(rows)


def accepted_ids(private: dict[str, Any]) -> set[str]:
    accepted = tuple(map(str, private.get("accepted_labels_all") or private["accepted_labels"]))
    return {
        str(entity_id)
        for entity_id, natural in private["numeric_to_natural"].items()
        if any(is_granularity_aware_hit(str(natural), label) for label in accepted)
    }


def root_granularity(private: dict[str, Any]) -> str:
    granularities = {
        str(private["entity_granularity"].get(label, "unknown"))
        for label in (private.get("accepted_labels_all") or private["accepted_labels"])
    }
    return next(iter(granularities)) if len(granularities) == 1 else "mixed"


def context_metadata() -> pd.DataFrame:
    split = json.loads(SPLIT.read_text())
    split_by_case = {
        row["opaque_incident_id"]: row
        for row in split["partitions"]["test"]
    }
    rows: list[dict[str, Any]] = []
    for path in sorted(CONTEXTS.glob("*.pkl")):
        with path.open("rb") as handle:
            context = pickle.load(handle)
        case = context["opaque_incident_id"]
        private = context["private"]
        target_ids = accepted_ids(private)
        x_facts = list(context["materialized"].get("facts") or ())
        p0_facts = list(context["p0_materialized"].get("facts") or ())
        x_root_facts = [
            fact for fact in x_facts
            if target_ids.intersection(map(str, fact.get("entity_ids") or ()))
        ]
        p0_root_facts = [
            fact for fact in p0_facts
            if target_ids.intersection(map(str, fact.get("entity_ids") or ()))
        ]
        bundles = list(context["materialized"].get("bundles") or ())
        root_bundles = [
            bundle for bundle in bundles
            if target_ids.intersection(
                str(entity)
                for side in (bundle.get("side_a") or {}, bundle.get("side_b") or {})
                for entity in (side.get("entity_ids") or ())
            )
        ]
        split_row = split_by_case[case]
        row = {
            "case": case,
            "dataset": private["dataset"],
            "fault_type": private["fault_type"],
            "root_granularity": root_granularity(private),
            "candidate_count": len(context["candidates"]),
            "x_pool_fact_count": len(context["pool"].facts),
            "x_selected_fact_count": len(x_facts),
            "x_selected_bundle_count": len(bundles),
            "x_root_evidence_visible": bool(x_root_facts),
            "x_root_fact_count": len(x_root_facts),
            "x_root_modalities": "+".join(sorted({str(f["region"]) for f in x_root_facts})) or "none",
            "x_root_bundle_visible": bool(root_bundles),
            "p0_root_evidence_visible": bool(p0_root_facts),
            "p0_root_fact_count": len(p0_root_facts),
            "p0_root_modalities": "+".join(sorted({str(f["region"]) for f in p0_root_facts})) or "none",
            "original_validation": bool(split_row.get("original_validation")),
            "exposure_stratum": "legacy_validation140" if split_row.get("original_validation") else "added220",
        }
        for method in ("ANOMALY_MAGNITUDE", "ANOMALY_COUNT", "X_INTERNAL"):
            ranking = list(context["cpu_rankings"][method]["ranking"])[:5]
            rank = next((index for index, entity in enumerate(ranking, 1) if entity in target_ids), None)
            row[f"{method}_mrr"] = 0.0 if rank is None else 1.0 / rank
            row[f"{method}_ac1"] = float(rank == 1)
            row[f"{method}_ac3"] = float(rank is not None and rank <= 3)
            row[f"{method}_ac5"] = float(rank is not None and rank <= 5)
        rows.append(row)
    return pd.DataFrame(rows)


def aggregate_metrics(df: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    return (
        df.groupby(groups, dropna=False)
        .agg(
            n=("mrr", "size"),
            MRR=("mrr", "mean"),
            AC1=("ac@1", "mean"),
            AC3=("ac@3", "mean"),
            AC5=("ac@5", "mean"),
            AVG3=("avg@3", "mean"),
            AVG5=("avg@5", "mean"),
            input_tokens=("input_tokens", "mean"),
            output_tokens=("output_tokens", "mean"),
            total_tokens=("total_tokens", "mean"),
            wall_time_s=("wall_time_s", "mean"),
            model_failures=("score_status", lambda x: int((x != "complete").sum())),
        )
        .reset_index()
    )


def paired_stats(left: pd.DataFrame, right: pd.DataFrame, *, label: str) -> dict[str, Any]:
    keys = ["case", "model"]
    merged = left[keys + ["mrr"]].merge(
        right[keys + ["mrr"]], on=keys, suffixes=("_left", "_right"), validate="one_to_one"
    )
    diff = (merged["mrr_left"] - merged["mrr_right"]).to_numpy(float)
    if len(diff) == 0:
        return {"comparison": label, "n": 0}
    if np.all(diff == 0):
        p = 1.0
        dz = 0.0
    else:
        p = float(wilcoxon(diff, zero_method="pratt", alternative="two-sided").pvalue)
        sd = float(np.std(diff, ddof=1)) if len(diff) > 1 else math.nan
        dz = float(np.mean(diff) / sd) if sd > 0 else math.nan
    left_top1 = merged["mrr_left"] == 1.0
    right_top1 = merged["mrr_right"] == 1.0
    return {
        "comparison": label,
        "n": len(merged),
        "left_mrr": float(merged["mrr_left"].mean()),
        "right_mrr": float(merged["mrr_right"].mean()),
        "delta_mrr": float(diff.mean()),
        "wilcoxon_p": p,
        "cohen_dz": dz,
        "top1_repairs": int((left_top1 & ~right_top1).sum()),
        "top1_breaks": int((~left_top1 & right_top1).sum()),
        "rr_improved": int((diff > 0).sum()),
        "rr_degraded": int((diff < 0).sum()),
        "rr_tied": int((diff == 0).sum()),
    }


def holm_adjust(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid = [(i, float(row["wilcoxon_p"])) for i, row in enumerate(rows) if "wilcoxon_p" in row]
    ordered = sorted(valid, key=lambda item: item[1])
    adjusted = [math.nan] * len(rows)
    running = 0.0
    m = len(ordered)
    for rank, (index, p_value) in enumerate(ordered):
        running = max(running, min(1.0, (m - rank) * p_value))
        adjusted[index] = running
    for index, row in enumerate(rows):
        row["holm_p"] = adjusted[index]
        row["practical_significant_gain"] = bool(
            row.get("delta_mrr", -math.inf) >= 0.05
            and not math.isnan(adjusted[index]) and adjusted[index] < 0.05
        )
    return rows


def final_family(final: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for model in MODELS:
        model_df = final[final.model == model]
        for visual in VISUALS:
            for control in CONTROLS:
                row = paired_stats(
                    model_df[model_df.arm == visual],
                    model_df[model_df.arm == control],
                    label=f"{model}:{visual}-{control}",
                )
                row.update({"model": model, "visual": visual, "control": control})
                rows.append(row)
    return pd.DataFrame(holm_adjust(rows))


def eval_family(eval_df: pd.DataFrame) -> pd.DataFrame:
    renamed = eval_df.rename(columns={"arm": "condition"})
    rows: list[dict[str, Any]] = []
    for model in MODELS:
        model_df = renamed[renamed.model == model]
        for visual in VISUALS:
            for control in CONTROLS:
                row = paired_stats(
                    model_df[model_df.condition == visual],
                    model_df[model_df.condition == control],
                    label=f"{model}:{visual}-{control}",
                )
                row.update({"model": model, "visual": visual, "control": control})
                rows.append(row)
    return pd.DataFrame(holm_adjust(rows))


def comparison_against_clean(
    treatment: pd.DataFrame,
    clean: pd.DataFrame,
    treatment_groups: list[str],
    clean_condition_column: str = "arm",
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for values, group in treatment.groupby(["model"] + treatment_groups, dropna=False):
        if not isinstance(values, tuple):
            values = (values,)
        model = values[0]
        dims = dict(zip(treatment_groups, values[1:]))
        representation = str(dims.get("representation") or dims.get("condition"))
        if representation not in ("X_C", "X_C_TABLE", "X_V_CONTRAST", "X_V_STANDARD"):
            representation = str(dims.get("representation", "X_V_CONTRAST"))
        base = clean[(clean.model == model) & (clean[clean_condition_column] == representation)]
        row = paired_stats(group, base, label=f"{model}:{dims}-{representation}@clean")
        row.update({"model": model, "baseline": representation, **dims})
        rows.append(row)
    return pd.DataFrame(rows)


def mechanism_tables(eval_df: pd.DataFrame) -> pd.DataFrame:
    outputs: list[pd.DataFrame] = []
    specs = [
        ("exp_visual_diagnostic_mechanisms", ["condition", "representation"]),
        ("exp_budget_curve", ["budget", "representation"]),
        ("exp_redundant_load", ["load", "representation"]),
        ("exp_transfer_and_diagnostic_robustness", ["transform", "representation"]),
        ("exp_table_screenshot", ["representation"]),
        ("exp_replicate_stability", ["condition", "replicate"]),
    ]
    for experiment, dims in specs:
        treatment = records_frame(experiment)
        # Screenshot is compared to direct table; replicate conditions name their baseline directly.
        if experiment == "exp_table_screenshot":
            treatment = treatment.assign(condition="X_C_TABLE_S", representation="X_C_TABLE")
            table = comparison_against_clean(treatment, eval_df, ["condition", "representation"])
        elif experiment == "exp_replicate_stability":
            table = comparison_against_clean(treatment, eval_df, dims)
        else:
            table = comparison_against_clean(treatment, eval_df, dims)
        table.insert(0, "experiment", experiment)
        outputs.append(table)
    return pd.concat(outputs, ignore_index=True, sort=False)


def reason_and_failure_table(final: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    merged = final.merge(metadata, on=["case", "dataset", "fault_type"], validate="many_to_one")
    merged["reason_entity_count"] = merged.reason_entity_ids.map(lambda value: len(json.loads(value)))
    merged["valid_answer"] = merged.score_status == "complete"
    return (
        merged.groupby(["model", "arm"], dropna=False)
        .agg(
            n=("case", "size"),
            valid_answer_rate=("valid_answer", "mean"),
            mean_candidates_returned=("predicted_count", "mean"),
            one_candidate_rate=("predicted_count", lambda x: float((x == 1).mean())),
            mean_reason_entity_mentions=("reason_entity_count", "mean"),
            mean_observation_refs=("reason_observation_refs", "mean"),
            mean_output_tokens=("output_tokens", "mean"),
        )
        .reset_index()
    )


def visibility_table(final: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    merged = final.merge(metadata, on=["case", "dataset", "fault_type"], validate="many_to_one")
    x = merged[merged.arm.isin(("X_C", "X_C_TABLE", "X_V_CONTRAST", "X_MTEXT"))].copy()
    return (
        x.groupby(["model", "arm", "x_root_evidence_visible"], dropna=False)
        .agg(n=("case", "size"), MRR=("mrr", "mean"), AC1=("ac@1", "mean"), AC5=("ac@5", "mean"))
        .reset_index()
    )


def subgroup_tables(final: pd.DataFrame, metadata: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    merged = final.merge(metadata, on=["case", "dataset", "fault_type"], validate="many_to_one")
    granularity = aggregate_metrics(merged, ["model", "arm", "root_granularity"])
    exposure = aggregate_metrics(merged, ["model", "arm", "exposure_stratum"])
    fault = aggregate_metrics(merged, ["model", "arm", "dataset", "fault_type"])
    return granularity, exposure, fault


def cpu_baselines(metadata: pd.DataFrame) -> pd.DataFrame:
    baro = json.loads((RUN / "baro_component_v2/summary.json").read_text())
    rows = [{"baseline": baro["method"], "dataset": "pooled360", **baro["averages"]}]
    for dataset, metrics in baro["per_dataset"].items():
        rows.append({"baseline": baro["method"], "dataset": dataset, **metrics})
    # The other CPU controls were extracted from the same contexts with the
    # exact candidate/root binding while constructing metadata.
    methods = ("ANOMALY_MAGNITUDE", "ANOMALY_COUNT", "X_INTERNAL")
    for method in methods:
        for dataset, frame in [("pooled360", metadata), *metadata.groupby("dataset")]:
            rows.append({
                "baseline": method,
                "dataset": dataset,
                "mrr": float(frame[f"{method}_mrr"].mean()),
                "ac@1": float(frame[f"{method}_ac1"].mean()),
                "ac@3": float(frame[f"{method}_ac3"].mean()),
                "ac@5": float(frame[f"{method}_ac5"].mean()),
            })
    return pd.DataFrame(rows)


def transition_table(final: pd.DataFrame, left: str, right: str) -> pd.DataFrame:
    keys = ["model", "dataset", "case", "fault_type"]
    a = final[final.arm == left][keys + ["mrr", "ac@1", "ac@5", "call_key", "reason"]]
    b = final[final.arm == right][keys + ["mrr", "ac@1", "ac@5", "call_key", "reason"]]
    merged = a.merge(b, on=keys, suffixes=(f"_{left}", f"_{right}"), validate="one_to_one")
    merged["delta_mrr"] = merged[f"mrr_{left}"] - merged[f"mrr_{right}"]
    merged["top1_transition"] = np.select(
        [
            (merged[f"ac@1_{left}"] == 1) & (merged[f"ac@1_{right}"] == 0),
            (merged[f"ac@1_{left}"] == 0) & (merged[f"ac@1_{right}"] == 1),
        ],
        ["repair", "break"],
        default="tie",
    )
    return merged


def save_plots(final_metrics: pd.DataFrame, eval_metrics: pd.DataFrame, pairwise: pd.DataFrame,
               transitions: pd.DataFrame, out: Path) -> None:
    sns.set_theme(style="whitegrid", context="talk")
    arm_order = list(FINAL_ARMS)
    model_labels = {"qwen3.8-27b": "Qwen3.8-27B", "gemma-4-26b-a4b": "Gemma-4-26B"}

    # MRR by dataset/arm/model.
    table = final_metrics[final_metrics.dataset != "pooled360"].copy()
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), constrained_layout=True)
    for ax, model in zip(axes, MODELS):
        pivot = table[table.model == model].pivot(index="arm", columns="dataset", values="MRR").reindex(arm_order)
        sns.heatmap(pivot, annot=True, fmt=".3f", cmap="viridis", vmin=0, vmax=max(.6, float(pivot.max().max())), ax=ax)
        ax.set_title(model_labels[model]); ax.set_xlabel(""); ax.set_ylabel("")
    fig.suptitle("Final test MRR by dataset")
    fig.savefig(out / "final_mrr_heatmap.png", dpi=180)
    plt.close(fig)

    # Accuracy at k.
    pooled = final_metrics[final_metrics.dataset == "pooled360"].copy()
    melted = pooled.melt(id_vars=["model", "arm"], value_vars=["AC1", "AC3", "AC5"], var_name="metric", value_name="accuracy")
    fig, axes = plt.subplots(2, 1, figsize=(16, 12), constrained_layout=True)
    for ax, model in zip(axes, MODELS):
        sns.barplot(data=melted[melted.model == model], x="arm", y="accuracy", hue="metric", order=arm_order, ax=ax)
        ax.set_title(model_labels[model]); ax.set_ylim(0, .65); ax.tick_params(axis="x", rotation=25); ax.set_xlabel("")
    fig.savefig(out / "final_topk_accuracy.png", dpi=180)
    plt.close(fig)

    # Accuracy-cost scatter.
    fig, axes = plt.subplots(1, 2, figsize=(17, 7), constrained_layout=True)
    for ax, model in zip(axes, MODELS):
        data = pooled[pooled.model == model]
        sns.scatterplot(data=data, x="total_tokens", y="MRR", hue="arm", s=160, ax=ax)
        for _, row in data.iterrows():
            ax.annotate(row.arm, (row.total_tokens, row.MRR), xytext=(4, 4), textcoords="offset points", fontsize=9)
        ax.set_title(model_labels[model]); ax.get_legend().remove()
    fig.suptitle("Final test accuracy–token trade-off (mean per call)")
    fig.savefig(out / "accuracy_token_tradeoff.png", dpi=180)
    plt.close(fig)

    # Eval-to-test shift for the three common datasets.
    eval_primary = eval_metrics[eval_metrics.dataset.isin(("aegislab", "aiops2022", "aiops2025"))]
    common = eval_primary.merge(
        final_metrics[final_metrics.dataset != "pooled360"], on=["model", "arm", "dataset"],
        suffixes=("_eval", "_test"), validate="one_to_one"
    )
    common["delta"] = common.MRR_test - common.MRR_eval
    fig, axes = plt.subplots(1, 2, figsize=(18, 8), constrained_layout=True)
    for ax, model in zip(axes, MODELS):
        pivot = common[common.model == model].pivot(index="arm", columns="dataset", values="delta").reindex(arm_order)
        sns.heatmap(pivot, annot=True, fmt="+.3f", center=0, cmap="vlag", ax=ax)
        ax.set_title(model_labels[model]); ax.set_xlabel(""); ax.set_ylabel("")
    fig.suptitle("MRR shift: test360 minus exposed eval primary-dataset cases")
    fig.savefig(out / "eval_to_test_shift.png", dpi=180)
    plt.close(fig)

    # Repair/break counts for visual vs direct comparison table.
    counts = transitions.groupby(["model", "top1_transition"]).size().unstack(fill_value=0).reindex(columns=["repair", "break", "tie"], fill_value=0)
    fig, ax = plt.subplots(figsize=(11, 6), constrained_layout=True)
    counts[["repair", "break"]].rename(index=model_labels).plot.bar(ax=ax, color=["#2ca02c", "#d62728"])
    ax.set_title("X_V_CONTRAST versus X_C_TABLE: top-1 repairs and breaks")
    ax.set_ylabel("cases"); ax.set_xlabel(""); ax.tick_params(axis="x", rotation=0)
    fig.savefig(out / "visual_vs_table_repairs_breaks.png", dpi=180)
    plt.close(fig)

    # Final family deltas and adjusted significance.
    fig, axes = plt.subplots(1, 2, figsize=(17, 8), constrained_layout=True)
    for ax, model in zip(axes, MODELS):
        data = pairwise[pairwise.model == model].copy()
        data["label"] = data.visual + " − " + data.control
        data = data.sort_values("delta_mrr")
        colors = np.where(data.holm_p < .05, "#d62728", "#7f7f7f")
        ax.barh(data.label, data.delta_mrr, color=colors)
        ax.axvline(0, color="black", linewidth=1); ax.axvline(.05, color="#2ca02c", linestyle="--", linewidth=1)
        ax.set_title(model_labels[model]); ax.set_xlabel("paired ΔMRR")
    fig.suptitle("Prespecified final visual comparisons (red: Holm p<0.05)")
    fig.savefig(out / "final_pairwise_deltas.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)

    final = load_final_calls()
    metadata_cache = out / "test_case_metadata.csv"
    metadata = pd.read_csv(metadata_cache) if metadata_cache.exists() else context_metadata()
    eval_df = records_frame("exp_contrastive_rca_effectiveness").rename(columns={"arm": "arm"})

    final_pooled = aggregate_metrics(final, ["model", "arm"])
    final_pooled.insert(2, "dataset", "pooled360")
    final_by_dataset = aggregate_metrics(final, ["model", "arm", "dataset"])
    final_metrics = pd.concat([final_pooled, final_by_dataset], ignore_index=True)
    eval_pooled = aggregate_metrics(eval_df, ["model", "arm"])
    eval_pooled.insert(2, "dataset", "pooled480")
    eval_by_dataset = aggregate_metrics(eval_df, ["model", "arm", "dataset"])
    eval_metrics = pd.concat([eval_pooled, eval_by_dataset], ignore_index=True)

    pairwise = final_family(final)
    eval_pairwise = eval_family(eval_df)
    mechanisms = mechanism_tables(eval_df)
    reason_failures = reason_and_failure_table(final, metadata)
    visibility = visibility_table(final, metadata)
    granularity, exposure, faults = subgroup_tables(final, metadata)
    cpus = cpu_baselines(metadata)
    transitions = transition_table(final, "X_V_CONTRAST", "X_C_TABLE")
    transitions_t = transition_table(final, "X_V_CONTRAST", "T")

    files = {
        "final_call_records.csv": final,
        "test_case_metadata.csv": metadata,
        "final_arm_metrics.csv": final_metrics,
        "eval_arm_metrics.csv": eval_metrics,
        "final_pairwise_holm.csv": pairwise,
        "eval_pairwise_holm.csv": eval_pairwise,
        "mechanism_comparisons.csv": mechanisms,
        "reason_and_failure_summary.csv": reason_failures,
        "root_evidence_visibility.csv": visibility,
        "root_granularity_metrics.csv": granularity,
        "exposure_stratum_metrics.csv": exposure,
        "fault_type_metrics.csv": faults,
        "cpu_baselines.csv": cpus,
        "visual_vs_table_transitions.csv": transitions,
        "visual_vs_T_transitions.csv": transitions_t,
    }
    for name, frame in files.items():
        frame.to_csv(out / name, index=False)

    save_plots(final_metrics, eval_metrics, pairwise, transitions, out)

    audit = {
        "schema_version": "RQ31ResultsAnalysisV1",
        "source_summary_hashes": {
            experiment: load_summary(experiment)["artifact_hash"]
            for experiment in (
                "exp_contrastive_rca_effectiveness", "exp_visual_diagnostic_mechanisms",
                "exp_replicate_stability", "exp_budget_curve", "exp_table_screenshot",
                "exp_transfer_and_diagnostic_robustness", "exp_redundant_load", "exp_final_test",
            )
        },
        "final_records": len(final),
        "final_unique_cases": int(final.case.nunique()),
        "final_models": sorted(final.model.unique()),
        "final_arms": sorted(final.arm.unique()),
        "metadata_cases": len(metadata),
        "baro_artifact_hash": json.loads((RUN / "baro_component_v2/summary.json").read_text())["artifact_hash"],
        "derived_files": sorted(files),
    }
    (out / "analysis_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()

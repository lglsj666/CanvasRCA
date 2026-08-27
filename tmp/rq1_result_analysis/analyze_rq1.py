#!/usr/bin/env python3
"""Consolidate the formal RQ1 result lineages into auditable tables and figures.

This is an offline analysis program.  It does not call a model, mutate result
artifacts, or treat attention as causal evidence.
"""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import orjson
import pandas as pd
import seaborn as sns
from scipy.stats import wilcoxon


ROOT = Path("/home/lglsj/CanvasRCA_nibi")
MAIN = ROOT / "RQs/RQ1/results"
SHADOW = ROOT / "tmp/rq1_matched_rca_local/project/RQs/RQ1/results"
OUT = ROOT / "tmp/rq1_result_analysis"
ASSETS = ROOT / "docs/RQ1_report_assets"
OUT.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

DATASETS = ["aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt"]
HEADLINE = {"aegislab", "aiops2022", "aiops2025"}
ARMS = {
    "legacy_q9": ["T", "P", "V", "H"],
    "cross_region": [
        f"M{m}-R{r}-L{l}-G{g}"
        for m in "tv" for r in "tv" for l in "tv" for g in "tv"
    ] + ["P", "V", "H"],
    "typed_two_stage": [
        f"M{m}-R{r}-L{l}-G{g}"
        for m in "tv" for r in "tv" for l in "tv" for g in "tv"
    ] + ["P", "V", "H"],
    "direct_rca": ["T", "F", "V", "P", "H", "R"],
    "matched_rca": ["T", "F", "V", "P", "H", "R"],
    "visual_counterfactual_rca": [
        "H_factual", "H_targeted", "H_placebo", "H_neutral"
    ],
    "ledger_handoff_rca": ["L_txt", "L_vis", "L_hyb"],
}
QA_EXPERIMENTS = {"legacy_q9", "cross_region", "typed_two_stage"}
RCA_EXPERIMENTS = set(ARMS) - QA_EXPERIMENTS
MODELS = ["qwen3.6-27b", "gemma-4-26b-a4b", "qwen3.8-27b"]
DISPLAY_MODELS = ["gemma-4-26b-a4b", "qwen3.6-27b", "qwen3.8-27b"]
MODEL_LABELS = {
    "gemma-4-26b-a4b": "Gemma",
    "qwen3.6-27b": "Qwen3.6",
    "qwen3.8-27b": "Qwen3.8",
}
COST_REFERENCES = {
    "legacy_q9": "T",
    "cross_region": "Mt-Rt-Lt-Gt",
    "typed_two_stage": "Mt-Rt-Lt-Gt",
    "direct_rca": "T",
    "matched_rca": "T",
    "visual_counterfactual_rca": "H_factual",
    "ledger_handoff_rca": "L_txt",
}

SOURCES = [
    # Historical Qwen3.6 and Gemma formal QA lineages downloaded from Nibi.
    (MAIN, "rq1_v22b_formal_469_20260813__shard-*-of-0024", [
        "legacy_q9", "cross_region", "typed_two_stage"
    ], ["qwen3.6-27b", "gemma-4-26b-a4b"]),
    (MAIN, "rq1_v23_visual_cf_formal_469_20260814__shard-*-of-0024", [
        "visual_counterfactual_rca"
    ], ["qwen3.6-27b", "gemma-4-26b-a4b"]),
    # Local formal successors and local completion of downloaded partials.
    (SHADOW, "rq1_v22b_formal_469_20260813__shard-*-of-0024", [
        "direct_rca", "matched_rca", "ledger_handoff_rca"
    ], ["qwen3.6-27b", "gemma-4-26b-a4b"]),
    (SHADOW, "rq1_v23_qwen38_formal_469_20260817__shard-*-of-0024", list(ARMS), [
        "qwen3.8-27b"
    ]),
]


def read_json(path: Path):
    return orjson.loads(path.read_bytes())


def mean(values):
    values = [float(v) for v in values if v is not None and not pd.isna(v)]
    return float(np.mean(values)) if values else np.nan


def first_service_label(meta: dict) -> str:
    labels = meta.get("accepted_labels") or []
    granularity = meta.get("entity_granularity") or {}
    for label in labels:
        if granularity.get(label) == "service":
            return label
    return labels[0] if labels else "unknown"


def load_private():
    paths = sorted(SHADOW.glob("rq1_v22b_prepared_shared_469_20260813__shard-*/private/*.json"))
    result = {}
    for path in paths:
        x = read_json(path)
        case = x["opaque_incident_id"]
        x["canonical_root_label"] = first_service_label(x)
        result[case] = x
    if len(result) != 469:
        raise RuntimeError(f"Expected 469 private records, got {len(result)}")
    return result


def classify_error(record: dict) -> str:
    status = str(record.get("status", ""))
    error = str(record.get("error", "")).lower()
    stages = record.get("stages") or []
    if status == "protocol_ineligible":
        return "protocol_ineligible"
    if "exceeds context" in error or "context length" in error or "maximum context" in error:
        return "input_context_overflow"
    if "timeout" in error or "timed out" in error:
        return "timeout"
    if status not in {"completed", "protocol_ineligible"}:
        if any(w in error for w in ("vllm", "http", "connection", "request", "server", "abort")):
            return "vllm_response_failure"
        return "infrastructure_other"
    if any(bool(s.get("truncated")) or str(s.get("finish_reason")) == "length" for s in stages):
        return "output_truncation"
    if any(s.get("parse") is False for s in stages):
        return "parse_failure"
    return "none"


def stage_cost(stages):
    keys = ["text_tokens", "image_tokens", "input_tokens", "output_tokens", "total_tokens"]
    return {k: sum(float(s.get(k) or 0) for s in stages) for k in keys}


def stage_attention(stages, shard_root: Path):
    """Return request-level attention summaries and an artifact inventory."""
    requests = []
    for s in stages:
        if float(s.get("image_tokens") or 0) <= 0:
            continue
        probe = s.get("attention_probe") or {}
        artifacts = probe.get("artifacts") or []
        row = {
            "status": probe.get("status", "missing_status"),
            "image_artifacts": len(artifacts),
            "grid_refs": 0,
            "grid_exists": 0,
            "overlay_refs": 0,
            "overlay_exists": 0,
            "raw_probe_exists": 0,
        }
        ds = []
        raw_parents = set()
        for art in artifacts:
            diag = art.get("diagnostics") or {}
            ds.append((art.get("image_index", len(ds)), diag))
            gp = art.get("grid_path")
            op = art.get("overlay_path")
            if gp:
                row["grid_refs"] += 1
                full = shard_root / gp
                row["grid_exists"] += int(full.is_file())
                raw_parents.add(full.parent)
            if op:
                row["overlay_refs"] += 1
                row["overlay_exists"] += int((shard_root / op).is_file())
        raw_files = [p / "raw_probe.json" for p in raw_parents if (p / "raw_probe.json").is_file()]
        row["raw_probe_exists"] = len(raw_files)
        group_mass = {}
        if raw_files:
            raw = read_json(raw_files[0])
            for idx, group in enumerate(raw.get("image_groups") or []):
                group_mass[idx] = float(sum(group.get("weights") or []))
        total_group_mass = sum(group_mass.values())
        if total_group_mass <= 0:
            group_mass = {idx: 1.0 for idx, _ in ds}; total_group_mass = max(1, len(ds))
        weights = {idx: group_mass.get(idx, 0.0) / total_group_mass for idx, _ in ds}
        for metric in ("normalized_attention_entropy", "blank_attention_mass",
                       "top_10pct_evidence_precision", "required_region_attention_mass"):
            values = [(weights[idx], d.get(metric)) for idx, d in ds if d.get(metric) is not None]
            denom = sum(w for w, _ in values)
            row[metric] = sum(w * float(v) for w, v in values) / denom if denom else np.nan
        region = defaultdict(list)
        focus = defaultdict(list)
        for idx, d in ds:
            for key, value in (d.get("region_attention_mass") or {}).items():
                region[key].append(float(value) * weights[idx])
            for key, value in (d.get("normalized_region_focus") or {}).items():
                focus[key].append((weights[idx], value))
        for key, values in region.items():
            row[f"attn_{key}"] = float(sum(values))
        for key, values in focus.items():
            denom = sum(w for w, _ in values)
            row[f"focus_{key}"] = sum(w * float(v) for w, v in values) / denom if denom else np.nan
        requests.append(row)
    return requests


def load_shared_stage1():
    shared = {}
    for base, pattern, experiments, models in SOURCES:
        if "ledger_handoff_rca" not in experiments:
            continue
        for shard in sorted(base.glob(pattern)):
            for model in models:
                folder = shard / "trajectories/ledger_handoff_rca" / model / "_shared_stage1"
                for path in folder.glob("*.json"):
                    x = read_json(path)
                    key = (x["model"], x["opaque_incident_id"])
                    call = x.get("call") or {}
                    shared[key] = {
                        **stage_cost([call]),
                        "parse": bool(x.get("parse")),
                        "truncated": bool(call.get("truncated")),
                        "status": x.get("status"),
                        "attention": stage_attention([call], shard),
                    }
    return shared


def load_records(private):
    rows, attention_rows = [], []
    seen = set()
    duplicate_count = 0
    for base, pattern, experiments, models in SOURCES:
        for shard in sorted(base.glob(pattern)):
            for exp in experiments:
                for model in models:
                    folder = shard / "trajectories" / exp / model
                    if not folder.is_dir():
                        continue
                    for path in folder.glob("*.json"):
                        x = read_json(path)
                        key = (exp, model, x.get("opaque_incident_id"), x.get("arm"))
                        if key in seen:
                            duplicate_count += 1
                            continue
                        seen.add(key)
                        case = x.get("opaque_incident_id")
                        meta = private.get(case, {})
                        stages = x.get("stages") or []
                        score = x.get("score") or {}
                        cost = stage_cost(stages)
                        row = {
                            "experiment": exp,
                            "model": model,
                            "case": case,
                            "arm": x.get("arm"),
                            "dataset": meta.get("dataset", x.get("analysis_dataset", "unknown")),
                            "fault_type": meta.get("fault_type", x.get("analysis_fault_type", "unknown")),
                            "root_service": meta.get("canonical_root_label", "unknown"),
                            "accepted_label_count": len(meta.get("accepted_labels") or []),
                            "status": x.get("status"),
                            "error": x.get("error"),
                            "error_class": classify_error(x),
                            "stage_count": len(stages),
                            "parse_failure": int(any(s.get("parse") is False for s in stages)),
                            "output_truncation": int(any(bool(s.get("truncated")) or str(s.get("finish_reason")) == "length" for s in stages)),
                            "model_calls": len([s for s in stages if s.get("input_tokens") is not None]),
                            **cost,
                        }
                        for metric in ("complete_chain_accuracy", "correct_prefix_accuracy", "step_accuracy",
                                       "query_membership_valid", "level_1_complete_chain_accuracy",
                                       "level_2_complete_chain_accuracy", "level_3_complete_chain_accuracy",
                                       "ac@1", "ac@3", "ac@5", "avg@3", "avg@5", "mrr", "rank",
                                       "unknown_prediction_count"):
                            row[metric] = score.get(metric)
                        preds = score.get("natural_predictions") or []
                        row["top1_prediction"] = preds[0] if preds else None
                        row["template_scores"] = json.dumps(score.get("template_complete_chain_accuracy") or {}, sort_keys=True)
                        # Binding quality is relevant to the typed handoff, not a result gate.
                        supported, unsupported = 0, 0
                        for s in stages:
                            audit = (s.get("normalized") or {}).get("binding_audit") or {}
                            supported += int(audit.get("supported_steps") or audit.get("supported_selectors") or 0)
                            unsupported += int(audit.get("unsupported_steps") or audit.get("unsupported_selectors") or 0)
                        row["binding_supported"] = supported
                        row["binding_unsupported"] = unsupported
                        attn = stage_attention(stages, shard)
                        row["visual_request_count"] = len(attn)
                        row["attention_collected_count"] = sum(a["status"] == "collected_same_prefill" for a in attn)
                        if attn:
                            for col in ("normalized_attention_entropy", "blank_attention_mass",
                                        "top_10pct_evidence_precision", "required_region_attention_mass",
                                        "attn_M", "attn_R", "attn_L", "attn_G", "attn_ledger",
                                        "focus_M", "focus_R", "focus_L", "focus_G", "focus_ledger"):
                                row[col] = mean([a.get(col) for a in attn])
                            for i, a in enumerate(attn, 1):
                                attention_rows.append({
                                    "experiment": exp, "model": model, "case": case,
                                    "arm": x.get("arm"), "dataset": row["dataset"],
                                    "fault_type": row["fault_type"], "root_service": row["root_service"],
                                    "request_index": i, **a,
                                })
                        rows.append(row)
    df = pd.DataFrame(rows)
    return df, pd.DataFrame(attention_rows), duplicate_count


def add_ledger_costs(df, shared):
    """Attach shared stage-1 costs without pretending it was called per arm."""
    for idx, row in df[df.experiment == "ledger_handoff_rca"].iterrows():
        s = shared.get((row.model, row.case))
        if not s:
            continue
        for key in ("text_tokens", "image_tokens", "input_tokens", "output_tokens", "total_tokens"):
            df.loc[idx, f"incremental_{key}"] = row[key]
            df.loc[idx, key] = row[key] + s[key]
            df.loc[idx, f"amortized_{key}"] = row[key] + s[key] / 3.0
        df.loc[idx, "model_calls"] = row.model_calls + 1
        df.loc[idx, "amortized_model_calls"] = row.model_calls + 1 / 3.0
    return df


def expected_table(private):
    rows = []
    for exp, arms in ARMS.items():
        for model in MODELS:
            for case, meta in private.items():
                for arm in arms:
                    rows.append({"experiment": exp, "model": model, "case": case, "arm": arm,
                                 "dataset": meta["dataset"], "fault_type": meta["fault_type"],
                                 "root_service": meta["canonical_root_label"]})
    return pd.DataFrame(rows)


def scopes(df):
    parts = []
    for ds in DATASETS:
        x = df[df.dataset == ds].copy(); x["dataset_scope"] = ds; parts.append(x)
    x = df[df.dataset.isin(HEADLINE)].copy(); x["dataset_scope"] = "headline_289"; parts.append(x)
    x = df.copy(); x["dataset_scope"] = "all_469"; parts.append(x)
    return pd.concat(parts, ignore_index=True)


def aggregate_tables(df, expected):
    completed = df[df.status == "completed"].copy()
    perf_rows = []
    for keys, g in scopes(completed).groupby(["experiment", "model", "arm", "dataset_scope"], dropna=False):
        row = dict(zip(["experiment", "model", "arm", "dataset_scope"], keys))
        row["n"] = len(g); row["case_n"] = g.case.nunique()
        metrics = ["complete_chain_accuracy", "correct_prefix_accuracy", "step_accuracy",
                   "query_membership_valid", "level_1_complete_chain_accuracy",
                   "level_2_complete_chain_accuracy", "level_3_complete_chain_accuracy",
                   "ac@1", "ac@3", "ac@5", "avg@3", "avg@5", "mrr"]
        for metric in metrics:
            row[metric] = g[metric].mean() if metric in g else np.nan
        perf_rows.append(row)
    performance = pd.DataFrame(perf_rows).sort_values(["experiment", "model", "dataset_scope", "arm"])

    cost_rows = []
    for keys, g in scopes(completed).groupby(["experiment", "model", "arm", "dataset_scope"], dropna=False):
        row = dict(zip(["experiment", "model", "arm", "dataset_scope"], keys))
        row["n"] = len(g)
        for metric in ("text_tokens", "image_tokens", "input_tokens", "output_tokens", "total_tokens", "model_calls"):
            row[f"mean_{metric}"] = g[metric].mean()
            row[f"sum_{metric}"] = g[metric].sum()
        for metric in ("incremental_total_tokens", "amortized_total_tokens", "amortized_model_calls"):
            if metric in g and g[metric].notna().any():
                row[f"mean_{metric}"] = g[metric].mean()
        cost_rows.append(row)
    cost = pd.DataFrame(cost_rows).sort_values(["experiment", "model", "dataset_scope", "arm"])

    merged = expected.merge(df, on=["experiment", "model", "case", "arm", "dataset", "fault_type", "root_service"], how="left")
    merged["error_class"] = merged.error_class.fillna("missing_record")
    runtime_rows = []
    for keys, g in scopes(merged).groupby(["experiment", "model", "arm", "dataset_scope"], dropna=False):
        row = dict(zip(["experiment", "model", "arm", "dataset_scope"], keys))
        row["expected_n"] = len(g)
        # Infrastructure classes are mutually exclusive.  Truncation and parse
        # failure are independent model-output properties and can co-occur.
        for cls in ["missing_record", "vllm_response_failure", "input_context_overflow", "timeout",
                    "infrastructure_other", "protocol_ineligible"]:
            n = int((g.error_class == cls).sum())
            row[f"{cls}_n"] = n; row[f"{cls}_rate"] = n / len(g)
        for cls in ["output_truncation", "parse_failure"]:
            n = int(g[cls].fillna(0).astype(bool).sum())
            row[f"{cls}_n"] = n; row[f"{cls}_rate"] = n / len(g)
        infrastructure = g.error_class.isin(["missing_record", "vllm_response_failure", "input_context_overflow", "timeout", "infrastructure_other"])
        protocol = g.error_class.eq("protocol_ineligible")
        model_output = g.output_truncation.fillna(0).astype(bool) | g.parse_failure.fillna(0).astype(bool)
        clean = ~(infrastructure | protocol | model_output)
        row["none_n"] = int(clean.sum()); row["none_rate"] = float(clean.mean())
        row["infrastructure_error_rate"] = float(infrastructure.mean())
        row["model_output_error_rate"] = float(model_output.mean())
        row["any_problem_rate"] = float((infrastructure | model_output).mean())
        runtime_rows.append(row)
    runtime = pd.DataFrame(runtime_rows).sort_values(["experiment", "model", "dataset_scope", "arm"])
    return performance, cost, runtime, merged


def paired_stats(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a - b
    non_nan = ~(np.isnan(a) | np.isnan(b)); d = d[non_nan]
    if len(d) == 0:
        return dict(n=0, delta=np.nan, p=np.nan, cohen_dz=np.nan, improve=0, degrade=0, tie=0)
    if np.allclose(d, 0):
        p = 1.0
    else:
        try: p = float(wilcoxon(d, zero_method="pratt", alternative="two-sided").pvalue)
        except ValueError: p = 1.0
    sd = float(np.std(d, ddof=1)) if len(d) > 1 else 0.0
    dz = float(np.mean(d) / sd) if sd > 0 else (0.0 if np.mean(d) == 0 else math.copysign(math.inf, np.mean(d)))
    return dict(n=len(d), delta=float(np.mean(d)), p=p, cohen_dz=dz,
                improve=int((d > 0).sum()), degrade=int((d < 0).sum()), tie=int((d == 0).sum()))


def holm(pvals):
    n = len(pvals); order = np.argsort(pvals); out = np.ones(n); running = 0.0
    for rank, idx in enumerate(order):
        value = min(1.0, (n - rank) * pvals[idx]); running = max(running, value); out[idx] = running
    return out


def comparison_tables(df, expected_merged):
    done = df[(df.status == "completed") & (df.dataset.isin(HEADLINE))].copy()
    infra_classes = {"missing_record", "vllm_response_failure", "input_context_overflow", "timeout", "infrastructure_other"}
    bad = (expected_merged[expected_merged.error_class.isin(infra_classes)]
           .groupby(["experiment", "model"]).case.apply(set).to_dict())
    done = done[done.apply(lambda r: r.case not in bad.get((r.experiment, r.model), set()), axis=1)]
    rows = []

    def add(exp, model, arm_a, arm_b, metric, family, label=None):
        x = done[(done.experiment == exp) & (done.model == model) & (done.arm.isin([arm_a, arm_b]))]
        p = x.pivot_table(index="case", columns="arm", values=metric, aggfunc="first")
        if arm_a not in p or arm_b not in p: return
        stat = paired_stats(p[arm_a], p[arm_b])
        rows.append({"experiment": exp, "model": model, "comparison": label or f"{arm_a} - {arm_b}",
                     "arm_a": arm_a, "arm_b": arm_b, "metric": metric, "family": family, **stat})

    for model in MODELS:
        for a in ["P", "V", "H"]: add("legacy_q9", model, a, "T", "complete_chain_accuracy", "legacy_controls")
        for exp in ["cross_region", "typed_two_stage"]:
            for a in ["P", "V", "H"]:
                add(exp, model, a, "Mt-Rt-Lt-Gt", "complete_chain_accuracy", f"{exp}_controls")
        for exp in ["direct_rca", "matched_rca"]:
            for a, b in [("P", "T"), ("V", "T"), ("H", "T"), ("R", "T"), ("F", "T"), ("R", "F"), ("V", "P")]:
                family = f"{exp}_primary" if (a, b) in {("R", "T"), ("R", "F")} else f"{exp}_secondary"
                add(exp, model, a, b, "mrr", family)
        for a, b in [("H_targeted", "H_factual"), ("H_placebo", "H_factual"),
                     ("H_neutral", "H_factual"), ("H_targeted", "H_placebo")]:
            add("visual_counterfactual_rca", model, a, b, "mrr", "counterfactual")
        for a, b in [("L_vis", "L_txt"), ("L_hyb", "L_txt"), ("L_hyb", "L_vis")]:
            add("ledger_handoff_rca", model, a, b, "mrr", "ledger_handoff")

        # Registered cross-region depth claims use Level 2+3, not the three-
        # question packet average.  P2 is the interaction of arm effect with
        # reasoning depth: (H-T)_L3 - (H-T)_L1.
        for exp in ["cross_region", "typed_two_stage"]:
            text_arm = "Mt-Rt-Lt-Gt"
            x = done[(done.experiment == exp) & (done.model == model) & done.arm.isin(["H", text_arm])]
            p = x.pivot_table(index="case", columns="arm", values=["level_1_complete_chain_accuracy",
                                                                    "level_2_complete_chain_accuracy",
                                                                    "level_3_complete_chain_accuracy"], aggfunc="first")
            needed = [(m, a) for m in ["level_1_complete_chain_accuracy", "level_2_complete_chain_accuracy", "level_3_complete_chain_accuracy"] for a in ["H", text_arm]]
            if all(k in p.columns for k in needed):
                h23 = (p[("level_2_complete_chain_accuracy", "H")] + p[("level_3_complete_chain_accuracy", "H")]) / 2
                t23 = (p[("level_2_complete_chain_accuracy", text_arm)] + p[("level_3_complete_chain_accuracy", text_arm)]) / 2
                stat = paired_stats(h23, t23)
                rows.append({"experiment": exp, "model": model, "comparison": "P1: H-T on Level2+3",
                             "arm_a": "H", "arm_b": text_arm, "metric": "mean_level2_3_accuracy",
                             "family": f"{exp}_reasoning_primary", **stat})
                h_effect_l3 = p[("level_3_complete_chain_accuracy", "H")] - p[("level_3_complete_chain_accuracy", text_arm)]
                h_effect_l1 = p[("level_1_complete_chain_accuracy", "H")] - p[("level_1_complete_chain_accuracy", text_arm)]
                stat = paired_stats(h_effect_l3, h_effect_l1)
                rows.append({"experiment": exp, "model": model, "comparison": "P2: (H-T)L3 - (H-T)L1",
                             "arm_a": "depth_interaction", "arm_b": "zero", "metric": "accuracy_interaction",
                             "family": f"{exp}_reasoning_primary", **stat})

    # Factorial visual main effects are matched within case over the eight other contexts.
    for exp in ["cross_region", "typed_two_stage"]:
        for model in MODELS:
            x = done[(done.experiment == exp) & (done.model == model) & done.arm.str.match(r"^M[tv]-R[tv]-L[tv]-G[tv]$")]
            for factor in "MRLG":
                vals = []
                for case, g in x.groupby("case"):
                    v = g[g.arm.str.contains(fr"{factor}v")].complete_chain_accuracy.mean()
                    t = g[g.arm.str.contains(fr"{factor}t")].complete_chain_accuracy.mean()
                    vals.append((case, v, t))
                if vals:
                    stat = paired_stats([z[1] for z in vals], [z[2] for z in vals])
                    rows.append({"experiment": exp, "model": model,
                                 "comparison": f"{factor}_visual_main_effect", "arm_a": f"{factor}v",
                                 "arm_b": f"{factor}t", "metric": "complete_chain_accuracy",
                                 "family": f"{exp}_factorial_main_effects", **stat})

    # Cross-experiment stage effects, arm-by-arm.
    for model in MODELS:
        for a in ARMS["cross_region"]:
            x = done[(done.model == model) & (done.arm == a) & done.experiment.isin(["cross_region", "typed_two_stage"])]
            p = x.pivot_table(index="case", columns="experiment", values="complete_chain_accuracy", aggfunc="first")
            if {"cross_region", "typed_two_stage"}.issubset(p.columns):
                stat = paired_stats(p.typed_two_stage, p.cross_region)
                rows.append({"experiment": "typed_vs_cross", "model": model, "comparison": f"{a}: typed - direct",
                             "arm_a": a, "arm_b": a, "metric": "complete_chain_accuracy",
                             "family": "typed_vs_cross", **stat})
        for a in ARMS["direct_rca"]:
            x = done[(done.model == model) & (done.arm == a) & done.experiment.isin(["direct_rca", "matched_rca"])]
            p = x.pivot_table(index="case", columns="experiment", values="mrr", aggfunc="first")
            if {"direct_rca", "matched_rca"}.issubset(p.columns):
                stat = paired_stats(p.matched_rca, p.direct_rca)
                rows.append({"experiment": "matched_vs_direct", "model": model, "comparison": f"{a}: two-stage - direct",
                             "arm_a": a, "arm_b": a, "metric": "mrr", "family": "matched_vs_direct", **stat})

    result = pd.DataFrame(rows)
    result["p_holm"] = np.nan
    for _, idx in result.groupby(["experiment", "model", "family"]).groups.items():
        ids = list(idx); result.loc[ids, "p_holm"] = holm(result.loc[ids, "p"].fillna(1).to_numpy())
    return result.sort_values(["experiment", "model", "family", "comparison"])


def detailed_statistics(df):
    done = df[df.status == "completed"].copy()
    rca = done[done.experiment.isin(RCA_EXPERIMENTS)].copy()
    rca["outcome_class"] = np.select(
        [rca["parse_failure"].eq(1), rca["output_truncation"].eq(1), rca["ac@1"].eq(1),
         rca["rank"].isin([2, 3]), rca["rank"].isin([4, 5])],
        ["parse_failure", "output_truncation", "top1_correct", "rank_2_3", "rank_4_5"],
        default="top5_miss")
    fault = (rca.groupby(["experiment", "model", "arm", "dataset", "fault_type"], dropna=False)
             .agg(n=("case", "size"), ac1=("ac@1", "mean"), ac3=("ac@3", "mean"),
                  ac5=("ac@5", "mean"), mrr=("mrr", "mean"), unknown_ids=("unknown_prediction_count", "sum"))
             .reset_index())
    service = (rca.groupby(["experiment", "model", "arm", "dataset", "root_service"], dropna=False)
               .agg(n=("case", "size"), ac1=("ac@1", "mean"), mrr=("mrr", "mean"))
               .reset_index())
    errors = (rca.groupby(["experiment", "model", "arm", "dataset", "outcome_class"], dropna=False)
              .size().rename("n").reset_index())
    predictions = (rca.groupby(["experiment", "model", "arm", "dataset", "top1_prediction"], dropna=False)
                   .agg(n=("case", "size"), correct_n=("ac@1", "sum"), mrr=("mrr", "mean"))
                   .reset_index().sort_values("n", ascending=False))
    qa = done[done.experiment.isin(QA_EXPERIMENTS)].copy()
    levels = (qa.groupby(["experiment", "model", "arm", "dataset"], dropna=False)
              .agg(n=("case", "size"), overall=("complete_chain_accuracy", "mean"),
                   level1=("level_1_complete_chain_accuracy", "mean"),
                   level2=("level_2_complete_chain_accuracy", "mean"),
                   level3=("level_3_complete_chain_accuracy", "mean"),
                   query_id_valid=("query_membership_valid", "mean"),
                   step_accuracy=("step_accuracy", "mean")).reset_index())
    template_rows = []
    for _, r in qa.iterrows():
        for template, value in json.loads(r.template_scores or "{}").items():
            template_rows.append({"experiment": r.experiment, "model": r.model, "arm": r.arm,
                                  "dataset": r.dataset, "template": template, "score": value})
    templates = (pd.DataFrame(template_rows).groupby(["experiment", "model", "arm", "dataset", "template"])
                 .agg(n=("score", "size"), accuracy=("score", "mean")).reset_index()) if template_rows else pd.DataFrame()
    binding = (done[done.binding_supported + done.binding_unsupported > 0]
               .groupby(["experiment", "model", "arm", "dataset"])
               .agg(n=("case", "size"), supported=("binding_supported", "sum"), unsupported=("binding_unsupported", "sum"))
               .reset_index())
    if not binding.empty:
        binding["binding_rate"] = binding.supported / (binding.supported + binding.unsupported)
    return fault, service, errors, predictions, levels, templates, binding


def attention_tables(df, attention_requests):
    visual = df[df.visual_request_count.fillna(0) > 0].copy()
    metrics = ["normalized_attention_entropy", "blank_attention_mass", "top_10pct_evidence_precision",
               "required_region_attention_mass", "attn_M", "attn_R", "attn_L", "attn_G", "attn_ledger",
               "focus_M", "focus_R", "focus_L", "focus_G", "focus_ledger"]
    summary = visual.groupby(["experiment", "model", "arm", "dataset"], dropna=False).agg(
        n=("case", "size"), visual_requests=("visual_request_count", "sum"),
        collected=("attention_collected_count", "sum"), **{m: (m, "mean") for m in metrics}).reset_index()
    summary["collection_rate"] = summary.collected / summary.visual_requests
    fault = (visual.groupby(["experiment", "model", "arm", "dataset", "fault_type"], dropna=False)
             .agg(n=("case", "size"), **{m: (m, "mean") for m in metrics}).reset_index())
    service = (visual.groupby(["experiment", "model", "arm", "dataset", "root_service"], dropna=False)
               .agg(n=("case", "size"), **{m: (m, "mean") for m in metrics}).reset_index())
    rca = visual[visual.experiment.isin(RCA_EXPERIMENTS) & visual["ac@1"].notna()].copy()
    rca["top1_outcome"] = np.where(rca["ac@1"] == 1, "correct", "incorrect")
    correctness = (rca.groupby(["experiment", "model", "arm", "dataset", "top1_outcome"])
                   .agg(n=("case", "size"), **{m: (m, "mean") for m in metrics}).reset_index())
    inventory = (attention_requests.groupby(["experiment", "model", "arm"], dropna=False)
                 .agg(visual_request_n=("case", "size"), collected_n=("status", lambda s: int((s == "collected_same_prefill").sum())),
                      image_artifacts=("image_artifacts", "sum"), grid_refs=("grid_refs", "sum"),
                      grid_exists=("grid_exists", "sum"), overlay_refs=("overlay_refs", "sum"),
                      overlay_exists=("overlay_exists", "sum"), raw_probe_exists=("raw_probe_exists", "sum"))
                 .reset_index())
    inventory["collection_rate"] = inventory.collected_n / inventory.visual_request_n
    inventory["grid_presence_rate"] = inventory.grid_exists / inventory.grid_refs.replace(0, np.nan)
    inventory["overlay_presence_rate"] = inventory.overlay_exists / inventory.overlay_refs.replace(0, np.nan)
    return summary, fault, service, correctness, inventory


def modifier_and_transition_tables(df, invalid_sets):
    done = df[(df.status == "completed") & df.dataset.isin(HEADLINE)].copy()
    done = done[done.apply(lambda r: r.case not in invalid_sets.get((r.experiment, r.model), set()), axis=1)]
    modifier_rows, transition_rows = [], []
    pairs = {
        "direct_rca": [("R", "T"), ("V", "T"), ("H", "T")],
        "matched_rca": [("R", "T"), ("V", "T"), ("H", "T")],
        "ledger_handoff_rca": [("L_vis", "L_txt"), ("L_hyb", "L_txt")],
    }
    for exp, arm_pairs in pairs.items():
        for model in MODELS:
            base = done[(done.experiment == exp) & (done.model == model)]
            for arm_a, arm_b in arm_pairs:
                x = base[base.arm.isin([arm_a, arm_b])]
                for dimension in ("dataset", "fault_type", "root_service"):
                    a = x[x.arm == arm_a][["case", dimension, "mrr", "ac@1"]].rename(columns={"mrr": "mrr_a", "ac@1": "ac1_a"})
                    b = x[x.arm == arm_b][["case", dimension, "mrr", "ac@1"]].rename(columns={"mrr": "mrr_b", "ac@1": "ac1_b"})
                    p = a.merge(b, on=["case", dimension], how="inner").dropna(subset=["mrr_a", "mrr_b"])
                    for value, g in p.groupby(dimension):
                        stat = paired_stats(g.mrr_a, g.mrr_b)
                        aa, bb = g.ac1_a, g.ac1_b
                        modifier_rows.append({"experiment": exp, "model": model, "comparison": f"{arm_a} - {arm_b}",
                                              "dimension": dimension, "value": value,
                                              "repair_n": int(((aa == 1) & (bb == 0)).sum()),
                                              "break_n": int(((aa == 0) & (bb == 1)).sum()), **stat})
                p = x.pivot_table(index="case", columns="arm", values=["mrr", "ac@1"], aggfunc="first")
                if ("ac@1", arm_a) in p and ("ac@1", arm_b) in p:
                    p = p.dropna(subset=[("ac@1", arm_a), ("ac@1", arm_b)])
                    aa, bb = p[("ac@1", arm_a)], p[("ac@1", arm_b)]
                    transition_rows.append({"experiment": exp, "model": model, "comparison": f"{arm_a} - {arm_b}",
                                            "n": len(p), "both_correct": int(((aa == 1) & (bb == 1)).sum()),
                                            "repair": int(((aa == 1) & (bb == 0)).sum()),
                                            "break": int(((aa == 0) & (bb == 1)).sum()),
                                            "both_incorrect": int(((aa == 0) & (bb == 0)).sum()),
                                            "net_correction": int(((aa == 1) & (bb == 0)).sum() - ((aa == 0) & (bb == 1)).sum())})
    return pd.DataFrame(modifier_rows), pd.DataFrame(transition_rows)


def save_csv(df, name):
    df.to_csv(OUT / name, index=False, float_format="%.8g")


def _weighted_attention_matrix(table, label, top_n=15, min_total=30):
    cols = ["attn_M", "attn_R", "attn_L", "attn_G"]
    rows = []
    for value, g in table.groupby(label):
        total = int(g.n.sum())
        if total < min_total: continue
        row = {label: value, "n": total}
        for col in cols:
            z = g.dropna(subset=[col])
            row[col] = float((z[col] * z.n).sum() / z.n.sum()) if len(z) else np.nan
        rows.append(row)
    if not rows: return pd.DataFrame()
    x = pd.DataFrame(rows).nlargest(top_n, "n").set_index(label)[cols]
    return x


def _plot_arm_input_cost(cost: pd.DataFrame, experiment: str) -> None:
    """Plot one readable arm-first heatmap; models remain controlled columns."""
    x = cost[(cost.dataset_scope == "all_469") & (cost.experiment == experiment)].copy()
    if x.empty:
        return
    ref_arm = COST_REFERENCES[experiment]
    refs = x[x.arm == ref_arm].set_index("model").mean_input_tokens.to_dict()
    x["reference_pct"] = x.apply(
        lambda row: 100.0 * row.mean_input_tokens / refs[row.model], axis=1
    )
    arms = [arm for arm in ARMS[experiment] if arm in set(x.arm)]
    models = [model for model in DISPLAY_MODELS if model in set(x.model)]
    ratio = (x.pivot(index="arm", columns="model", values="reference_pct")
             .reindex(index=arms, columns=models))
    tokens = (x.pivot(index="arm", columns="model", values="mean_input_tokens")
              .reindex(index=arms, columns=models))
    ratio.columns = [MODEL_LABELS[model] for model in ratio.columns]
    tokens.columns = ratio.columns
    annotations = tokens.copy().astype(object)
    for arm in ratio.index:
        for model in ratio.columns:
            token_value = tokens.loc[arm, model]
            pct_value = ratio.loc[arm, model]
            annotations.loc[arm, model] = (
                "NA" if pd.isna(token_value) else f"{token_value / 1000:.1f}k\n{pct_value:.0f}%"
            )
    height = max(3.0, 1.15 + 0.48 * len(arms))
    plt.figure(figsize=(8.2, height))
    sns.heatmap(
        ratio, cmap="RdYlGn_r", vmin=0,
        vmax=max(200.0, float(np.nanmax(ratio.to_numpy()))), center=100,
        annot=annotations, fmt="", linewidths=0.7, linecolor="white",
        cbar_kws={"label": f"Input tokens as % of {ref_arm}"},
    )
    plt.title(
        f"{experiment}: input-token cost by arm\n"
        f"cell = mean input tokens (percent of {ref_arm})"
    )
    plt.xlabel("Model (compare arms down each column)")
    plt.ylabel("Experimental arm")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(ASSETS / f"cost_by_arm_{experiment}.png", dpi=180, bbox_inches="tight")
    plt.close()


def plot_tables(perf, cost, runtime, comparisons, attn_summary, attn_fault, attn_service, attn_correctness, records):
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams["font.family"] = ["Droid Sans Fallback", "DejaVu Sans"]
    # RCA MRR on the non-saturated headline set.
    x = perf[(perf.dataset_scope == "headline_289") & perf.experiment.isin(RCA_EXPERIMENTS)].copy()
    if not x.empty:
        g = sns.catplot(data=x, kind="bar", x="arm", y="mrr", hue="model", col="experiment",
                        col_wrap=2, sharex=False, height=3.4, aspect=1.35, errorbar=None)
        g.set_axis_labels("Arm", "MRR"); g.set_titles("{col_name}"); g.fig.suptitle("RQ1 RCA performance — headline 289", y=1.02)
        g.savefig(ASSETS / "rca_headline_mrr.png", dpi=180, bbox_inches="tight"); plt.close(g.fig)
    # QA levels.
    q = perf[(perf.dataset_scope == "headline_289") & perf.experiment.isin(QA_EXPERIMENTS)]
    q = q.melt(id_vars=["experiment", "model", "arm"], value_vars=["level_1_complete_chain_accuracy", "level_2_complete_chain_accuracy", "level_3_complete_chain_accuracy"], var_name="level", value_name="accuracy").dropna()
    if not q.empty:
        q["level"] = q.level.map({
            "level_1_complete_chain_accuracy": "Level 1",
            "level_2_complete_chain_accuracy": "Level 2",
            "level_3_complete_chain_accuracy": "Level 3",
        })
        q = q.groupby(["experiment", "model", "level"], as_index=False).accuracy.mean()
        experiments = ["legacy_q9", "cross_region", "typed_two_stage"]
        fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.4), sharey=True)
        handles = labels = None
        for ax, experiment in zip(axes, experiments, strict=True):
            subset = q[q.experiment == experiment]
            order = [level for level in ["Level 1", "Level 2", "Level 3"] if level in set(subset.level)]
            sns.barplot(data=subset, x="level", y="accuracy", hue="model", hue_order=DISPLAY_MODELS,
                        order=order, errorbar=None, ax=ax)
            ax.set_title(experiment); ax.set_xlabel(""); ax.set_ylabel("Complete-chain accuracy" if ax is axes[0] else "")
            current = ax.get_legend()
            if current is not None:
                handles, labels = ax.get_legend_handles_labels(); current.remove()
        if handles:
            fig.legend(handles, [MODEL_LABELS.get(label, label) for label in labels],
                       loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.02))
        fig.suptitle("QA accuracy by reasoning level (averaged across arms)", y=1.09)
        fig.tight_layout()
        fig.savefig(ASSETS / "qa_accuracy_by_level.png", dpi=180, bbox_inches="tight"); plt.close(fig)
    # Arm-first token cost. One image per experiment prevents dense factorial
    # names from collapsing into an unreadable omnibus x-axis.
    c = cost[(cost.dataset_scope == "all_469")].copy()
    if not c.empty:
        for experiment in ARMS:
            _plot_arm_input_cost(c, experiment)
    # Runtime errors by experiment/model (aggregate arms).
    r = runtime[runtime.dataset_scope == "all_469"].copy()
    count_cols = ["missing_record_n", "vllm_response_failure_n", "input_context_overflow_n", "timeout_n",
                  "output_truncation_n", "parse_failure_n", "infrastructure_other_n"]
    friendly_errors = ["Missing", "Server", "Context", "Timeout", "Truncated", "Parse", "Other infra"]
    if not r.empty:
        z = r.groupby(["experiment", "model"])[["expected_n", *count_cols]].sum().reset_index()
        for count_col, label in zip(count_cols, friendly_errors, strict=True):
            z[label] = z[count_col] / z.expected_n
        z["label"] = z.experiment + " — " + z.model.map(MODEL_LABELS)
        pivot = z.set_index("label")[friendly_errors]
        pivot = pivot[pivot.max(axis=1) > 0]
        pivot = pivot.loc[:, pivot.max(axis=0) > 0]
        if not pivot.empty:
            annotations = pivot.map(lambda value: f"{100 * value:.2f}%" if value else "0")
            plt.figure(figsize=(11.5, max(4.0, 0.52 * len(pivot) + 1.7)))
            sns.heatmap(pivot, cmap="Reds", annot=annotations, fmt="", linewidths=0.7,
                        cbar_kws={"label": "Fraction of registered records"})
            plt.title("Nonzero runtime and model-output error rates\n(all omitted rows and error classes are zero)")
            plt.xlabel("Error class"); plt.ylabel(""); plt.yticks(rotation=0)
            plt.tight_layout(); plt.savefig(ASSETS / "runtime_errors.png", dpi=180, bbox_inches="tight"); plt.close()
    # Paired deltas.
    z = comparisons[(comparisons.n >= 50) & comparisons.experiment.isin(["direct_rca", "matched_rca", "ledger_handoff_rca", "visual_counterfactual_rca"])].copy()
    if not z.empty:
        z["label"] = z.experiment + ": " + z.comparison
        plt.figure(figsize=(12, max(6, len(z) * .19)))
        sns.barplot(data=z, y="label", x="delta", hue="model", errorbar=None)
        plt.axvline(0, color="black", lw=1); plt.xlabel("Paired mean delta"); plt.ylabel(""); plt.title("Headline-289 paired arm effects")
        plt.tight_layout(); plt.savefig(ASSETS / "paired_deltas.png", dpi=180); plt.close()
    # Attention region mass: only rows with a real region atlas, excluding ledger pixels.
    full = (
        (records.experiment.isin(["legacy_q9", "direct_rca", "matched_rca"]) & records.arm.isin(["V", "H"])) |
        (records.experiment.isin(["cross_region", "typed_two_stage"]) & records.arm.isin(["V", "H"])) |
        records.experiment.eq("visual_counterfactual_rca")
    )
    full_records = records[full & records.attn_M.notna()].copy()
    a = full_records.groupby("model")[["attn_M", "attn_R", "attn_L", "attn_G"]].mean().reset_index()
    if not a.empty:
        a = a.groupby(["model"])[["attn_M", "attn_R", "attn_L", "attn_G"]].mean().reset_index().melt("model", var_name="region", value_name="attention_mass")
        a.region = a.region.str.replace("attn_", "", regex=False)
        plt.figure(figsize=(8, 5)); sns.barplot(data=a, x="region", y="attention_mass", hue="model", errorbar=None)
        plt.xlabel("Dashboard region (M/R/L/G)"); plt.ylabel("Mean attention mass"); plt.title("Same-prefill attention distribution by dashboard region")
        plt.tight_layout(); plt.savefig(ASSETS / "attention_region_mass.png", dpi=180); plt.close()
    # Attention by experiment.
    a = attn_summary.groupby(["experiment", "model"])[["normalized_attention_entropy", "blank_attention_mass", "top_10pct_evidence_precision"]].mean().reset_index()
    if not a.empty:
        metrics = [
            ("normalized_attention_entropy", "Attention entropy"),
            ("blank_attention_mass", "Blank-canvas mass"),
            ("top_10pct_evidence_precision", "Top-10% evidence precision"),
        ]
        fig, axes = plt.subplots(1, 3, figsize=(15.5, 6.2))
        experiment_order = list(ARMS)
        for index, (ax, (metric, title)) in enumerate(zip(axes, metrics, strict=True)):
            pivot = (a.pivot(index="experiment", columns="model", values=metric)
                     .reindex(index=experiment_order, columns=DISPLAY_MODELS))
            pivot = pivot.dropna(how="all")
            pivot.columns = [MODEL_LABELS[model] for model in pivot.columns]
            sns.heatmap(pivot, cmap="viridis", annot=True, fmt=".3f", linewidths=0.7,
                        cbar=False, ax=ax)
            ax.set_title(title); ax.set_xlabel("Model"); ax.set_ylabel("Experiment" if index == 0 else "")
            ax.tick_params(axis="y", rotation=0)
        fig.suptitle("Same-prefill attention diagnostics by experiment and model", y=1.01)
        fig.tight_layout(); fig.savefig(ASSETS / "attention_diagnostics_by_experiment.png", dpi=180, bbox_inches="tight"); plt.close(fig)
    # Correct-vs-incorrect attention, associations only.
    if not attn_correctness.empty:
        a = attn_correctness.groupby(["model", "top1_outcome"])[["normalized_attention_entropy", "blank_attention_mass", "top_10pct_evidence_precision"]].mean().reset_index()
        g = sns.catplot(data=a.melt(["model", "top1_outcome"], var_name="metric", value_name="value"), kind="bar",
                        x="top1_outcome", y="value", hue="model", col="metric", sharey=False, height=3.5, aspect=1.2, errorbar=None)
        g.savefig(ASSETS / "attention_correct_vs_incorrect.png", dpi=180, bbox_inches="tight"); plt.close(g.fig)
    # Frequent fault types, M/R/L/G mass.
    a = (full_records.groupby("fault_type")
         .agg(n=("case", "size"), attn_M=("attn_M", "mean"), attn_R=("attn_R", "mean"),
              attn_L=("attn_L", "mean"), attn_G=("attn_G", "mean")).reset_index())
    a = a[a.n >= 30].nlargest(15, "n").set_index("fault_type")[["attn_M", "attn_R", "attn_L", "attn_G"]]
    if not a.empty:
        plt.figure(figsize=(8, max(5, len(a) * .35))); sns.heatmap(a, cmap="viridis", annot=True, fmt=".2f")
        plt.title("Attention-region associations by fault type"); plt.xlabel("Region"); plt.ylabel("Fault type")
        plt.tight_layout(); plt.savefig(ASSETS / "attention_fault_type_heatmap.png", dpi=180); plt.close()
    a = (full_records.groupby("root_service")
         .agg(n=("case", "size"), attn_M=("attn_M", "mean"), attn_R=("attn_R", "mean"),
              attn_L=("attn_L", "mean"), attn_G=("attn_G", "mean")).reset_index())
    a = a[a.n >= 30].nlargest(15, "n").set_index("root_service")[["attn_M", "attn_R", "attn_L", "attn_G"]]
    if not a.empty:
        plt.figure(figsize=(8, max(5, len(a) * .35))); sns.heatmap(a, cmap="magma", annot=True, fmt=".2f")
        plt.title("Attention-region associations by canonical root label"); plt.xlabel("Region"); plt.ylabel("Canonical root label")
        plt.tight_layout(); plt.savefig(ASSETS / "attention_root_service_heatmap.png", dpi=180); plt.close()


def copy_representative_overlays(df):
    copied = []
    for model in MODELS:
        candidates = df[(df.model == model) & (df.experiment == "direct_rca") & (df.arm == "V") & (df.status == "completed")]
        if candidates.empty: continue
        # Locate the artifact afresh from the selected source; only one opaque case is copied.
        case = candidates.iloc[0].case
        for base, pattern, exps, models in SOURCES:
            if "direct_rca" not in exps or model not in models: continue
            for shard in base.glob(pattern):
                p = shard / "trajectories/direct_rca" / model / f"{case}__V.json"
                if not p.is_file(): continue
                x = read_json(p)
                arts = ((x.get("stages") or [{}])[0].get("attention_probe") or {}).get("artifacts") or []
                if arts and arts[0].get("overlay_path"):
                    src = shard / arts[0]["overlay_path"]
                    if src.is_file():
                        dest = ASSETS / f"attention_overlay_{model}.png"; shutil.copy2(src, dest); copied.append(str(dest))
                break
            if copied and copied[-1].endswith(f"attention_overlay_{model}.png"): break
    return copied


def main():
    print("Loading private evaluation metadata...")
    private = load_private()
    print("Loading formal trajectory lineages...")
    df, attention_requests, duplicate_count = load_records(private)
    shared = load_shared_stage1()
    df = add_ledger_costs(df, shared)
    expected = expected_table(private)
    print(f"Loaded {len(df):,} records, {len(attention_requests):,} visual requests, {len(shared):,} shared ledgers")
    performance, cost, runtime, expected_merged = aggregate_tables(df, expected)
    infra_classes = {"missing_record", "vllm_response_failure", "input_context_overflow", "timeout", "infrastructure_other"}
    invalid_sets = (expected_merged[expected_merged.error_class.isin(infra_classes)]
                    .groupby(["experiment", "model"]).case.apply(set).to_dict())
    paired_complete_df = df[df.apply(
        lambda r: r.case not in invalid_sets.get((r.experiment, r.model), set()), axis=1
    )].copy()
    performance_complete, cost_complete, _, _ = aggregate_tables(paired_complete_df, expected)
    comparisons = comparison_tables(df, expected_merged)
    fault, service, errors, predictions, levels, templates, binding = detailed_statistics(df)
    attn_summary, attn_fault, attn_service, attn_correctness, attn_inventory = attention_tables(df, attention_requests)
    modifiers, transitions = modifier_and_transition_tables(df, invalid_sets)

    # Complete-case exclusion audit by experiment/model.
    infra_classes = {"missing_record", "vllm_response_failure", "input_context_overflow", "timeout", "infrastructure_other"}
    case_status = (expected_merged.groupby(["experiment", "model", "case"])
                   .agg(any_problem=("error_class", lambda s: any(x in infra_classes for x in s)),
                        all_protocol_ineligible=("error_class", lambda s: all(x == "protocol_ineligible" for x in s)))
                   .reset_index())
    eligibility = (case_status.groupby(["experiment", "model"])
                   .agg(case_n=("case", "size"), excluded_cases=("any_problem", "sum"),
                        all_ineligible_cases=("all_protocol_ineligible", "sum")).reset_index())
    eligibility["exclusion_rate"] = eligibility.excluded_cases / eligibility.case_n
    eligibility["passes_5pct"] = eligibility.exclusion_rate <= .05

    save_csv(performance, "performance.csv")
    save_csv(performance_complete, "performance_paired_complete.csv")
    save_csv(cost, "cost.csv")
    save_csv(cost_complete, "cost_paired_complete.csv")
    save_csv(runtime, "runtime.csv")
    save_csv(comparisons, "comparisons.csv")
    save_csv(fault, "statistics_fault_type.csv")
    save_csv(service, "statistics_service.csv")
    save_csv(errors, "statistics_error_reason.csv")
    save_csv(predictions, "statistics_prediction_service.csv")
    save_csv(levels, "qa_reasoning_levels.csv")
    save_csv(templates, "qa_templates.csv")
    save_csv(binding, "stage1_binding.csv")
    save_csv(attn_inventory, "attention_inventory.csv")
    save_csv(attn_summary, "attention_summary.csv")
    save_csv(attn_fault, "attention_fault_type.csv")
    save_csv(attn_service, "attention_service.csv")
    save_csv(attn_correctness, "attention_correctness.csv")
    save_csv(eligibility, "eligibility.csv")
    save_csv(modifiers, "effect_modifiers.csv")
    save_csv(transitions, "arm_transitions.csv")
    # Compact record-level file excludes prompts/responses but enables re-analysis.
    df.to_parquet(OUT / "records.parquet", index=False, compression="zstd")

    plot_tables(performance, cost, runtime, comparisons, attn_summary, attn_fault, attn_service, attn_correctness, df)
    representative = copy_representative_overlays(df)
    summary = {
        "schema": "RQ1ResultAnalysisV1",
        "formal_records": len(df),
        "duplicate_records_skipped": duplicate_count,
        "private_cases": len(private),
        "dataset_counts": Counter(x["dataset"] for x in private.values()),
        "model_counts": df.model.value_counts().to_dict(),
        "experiment_counts": df.groupby(["experiment", "model"]).size().rename("n").reset_index().to_dict("records"),
        "attention_visual_requests": len(attention_requests),
        "attention_collected": int((attention_requests.status == "collected_same_prefill").sum()),
        "attention_grid_refs": int(attention_requests.grid_refs.sum()),
        "attention_grid_exists": int(attention_requests.grid_exists.sum()),
        "attention_overlay_refs": int(attention_requests.overlay_refs.sum()),
        "attention_overlay_exists": int(attention_requests.overlay_exists.sum()),
        "representative_overlays": representative,
        "eligibility": eligibility.to_dict("records"),
        "limitations": [
            "Attention is correlational and cannot establish causal feature use.",
            "The atlas has M/R/L/G or ledger region masks, not entity-level service masks.",
            "Wall time is intentionally excluded from cost comparisons because hardware differs.",
            "Accepted aliases are not interpreted as independent multi-root labels.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()

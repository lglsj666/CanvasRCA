"""Offline A/B screen report; never calls a model or rewrites experiment records.

Run from repo root after sourcing scripts/env_local.sh. Source scores are
immutable. Derived root granularity uses evaluator-private accepted labels,
not the runner's entity->type dictionary mistakenly labeled granularity.
"""

import json
from collections import Counter
from itertools import chain
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from RQs.RQ3_5.src.utils import ROOT, digest, read_json
from vlmrca.eval.scoring import is_granularity_aware_hit

RUN = ROOT / "RQs/RQ3_5/results/outcome_linked_v1"
OUT = ROOT / "docs/experiment_reports/RQ3_5_Screen_Analysis_2026-09-26_assets"
OUT.mkdir(exist_ok=True)
EXPS = {"A": "exp_evidence_instruction_cross", "B": "exp_outcome_linked_evidence"}
ARMS = {
    "A": ["E_P_D_P", "E_P_D_S", "E_S_D_P", "E_S_D_S", "T_NATIVE", "SIRCL_IDS_NATIVE"],
    "B": ["TPV", "MORE", "W_NO_K", "J_MARG", "J_JOINT", "J_COND"],
}
MODELS = ["qwen3.8-27b", "gemma-4-26b-a4b"]
DATASETS = ["aiops2022", "aiops2025", "aegislab"]
METRICS = ["mrr", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5"]
reg = read_json(RUN / "registration.json")
assert read_json(RUN / "formal_queue_status.json")["state"] == "completed_screen_ab"
private = {
    r["opaque_incident_id"]: read_json(
        RUN / "private" / (r["opaque_incident_id"] + ".json")
    )
    for r in reg["rosters"]["screen"]
}
analyses = {
    e: read_json(RUN / "analysis" / ("screen_" + name + ".json"))
    for e, name in EXPS.items()
}


def save(name, value):
    (OUT / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n"
    )


def table(name, records):
    pd.DataFrame(records).to_csv(OUT / (name + ".csv"), index=False)


def nested_values(obj, key):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                yield v
            else:
                yield from nested_values(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from nested_values(v, key)


def root_hit(case, entity):
    p = private[case]
    return any(
        is_granularity_aware_hit(p["numeric_to_natural"].get(entity, "UNKNOWN"), g)
        for g in p["accepted_labels"]
    )


def visible_identity(prompt):
    return {
        "system": prompt["system"],
        "parts": [
            ("text", p["text"]) if p["type"] == "text" else ("image", p["image_sha256"])
            for p in prompt["parts"]
        ],
    }


rows, raw_index, prompts, outputs = [], {}, {}, {}
integrity = {
    "expected_units": 1440,
    "contract_hash": digest(reg["contract"]),
    "warnings": [],
    "artifact_presence_checked": 0,
    "source_score_mismatches": 0,
}
for exp, analysis in analyses.items():
    assert len(analysis["rows"]) == 720
    for item in analysis["rows"]:
        r = {k: v for k, v in item.items() if k not in {"metrics", "granularity"}}
        p = private[r["case"]]
        r.update(
            experiment=exp,
            granularity="+".join(
                sorted(
                    {
                        p["entity_granularity"].get(g, "unknown")
                        for g in p["accepted_labels"]
                    }
                )
            ),
        )
        key = (exp, r["model"], r["case"], r["arm"])
        assert key not in raw_index
        raw_index[key] = item
        d, call = Path(r["artifact_root"]), r["call_key"]
        if r["status"] == "done":
            for folder, suffix in [
                ("outputs", ".json"),
                ("prompts", ".json"),
                ("conversations", ".md"),
                ("trajectories", ".json"),
                ("trajectories", ".raw.json"),
                ("completed", ".json"),
            ]:
                assert (d / folder / (call + suffix)).is_file(), (key, folder)
                integrity["artifact_presence_checked"] += 1
            o = read_json(d / "outputs" / (call + ".json"))
            prompt = read_json(d / "prompts" / (call + ".json"))
            outputs[key], prompts[key] = o, prompt
            assert prompt["effective_server"]["max_tokens"] == 8192
            for part in prompt["parts"]:
                if part["type"] == "image":
                    assert (d / part["image_path"]).is_file()
            for metric in METRICS:
                assert item["metrics"][metric] == o["score"]["metrics"][metric]
                r[metric] = item["metrics"][metric]
            raw = read_json(d / "trajectories" / (call + ".raw.json"))
            r["finish_reason"] = ";".join(
                str(v) for v in nested_values(raw, "finish_reason")
            )
            try:
                answer = json.loads(o["response"])
                predicted = answer.get("services", [])
                r["json_parsed"] = isinstance(predicted, list)
            except (ValueError, AttributeError):
                predicted, r["json_parsed"] = [], False
            r["predictions"] = json.dumps(predicted)
            r["n_candidates"] = len(predicted)
            r["unknown_ids"] = sum(x not in p["numeric_to_natural"] for x in predicted)
            r["duplicate_ids"] = len(predicted) - len(set(predicted))
            r["predicted_kind"] = (
                p["entity_granularity"].get(
                    p["numeric_to_natural"].get(predicted[0], ""), "unknown"
                )
                if predicted
                else "none"
            )
            r["score_error"] = str(o["score"].get("error") or "")
            r["reuse"] = bool(o.get("reuse_reference"))
            r["reason"] = (
                answer.get("reason", "") if r["json_parsed"] else o["response"]
            )
            a = read_json(d / "audits" / (call + ".json"))
            verdicts = Counter(
                c.get("check", {}).get("verdict", "uncompiled")
                for c in a.get("claims", [])
            )
            r["literal_refuted"] = verdicts["refuted"]
            r["literal_supported"] = verdicts["supported"]
            r["literal_claims"] = len(a.get("claims", []))
            r["audit_verdicts"] = json.dumps(dict(verdicts))
        rows.append(r)
df = pd.DataFrame(rows)
assert len(df) == 1440
assert set(df["status"]) <= {"done", "fail"}
assert (df.loc[df.status == "fail", "failure_class"] == "request_timeout").all()
table("per_record", rows)
table("failures", df[df.status == "fail"].to_dict("records"))
save(
    "provenance.json",
    {
        "registration": str(RUN / "registration.json"),
        "contract_hash": digest(reg["contract"]),
        "source_analyses": {
            k: str(RUN / "analysis" / ("screen_" + v + ".json"))
            for k, v in EXPS.items()
        },
        "status": "completed repeated-exposed screen60; not check120 or test",
        "models": reg["config"]["models"],
        "script": str(Path(__file__).resolve()),
        "no_new_model_calls": True,
        "scoring": "original granularity-aware per-call scores unchanged",
        "qualifications": {
            c["id"]: read_json(RUN / "qualification" / (c["id"] + ".json"))
            for c in reg["config"]["experiments"][:2]
        },
    },
)

# Common complete cases for fair arm ranking; registered hypothesis families
# retain their own previously registered complete-case sets in separate tables.
denoms, summaries, strata = {}, [], []
for exp in EXPS:
    for model in MODELS:
        group = df[(df.experiment == exp) & (df.model == model)]
        bad = set(group.loc[group.status != "done", "case"])
        good = group[~group.case.isin(bad)]
        denoms[exp + "/" + model] = {
            "excluded": sorted(bad),
            "n": good.case.nunique(),
            "per_dataset": good.drop_duplicates("case")
            .dataset.value_counts()
            .to_dict(),
        }
        for arm in ARMS[exp]:
            ar = good[good.arm == arm]
            for label in ["macro", "pooled", "aiops_combined", *DATASETS]:
                s = (
                    ar
                    if label in {"macro", "pooled"}
                    else ar[ar.dataset.str.startswith("aiops")]
                    if label == "aiops_combined"
                    else ar[ar.dataset == label]
                )
                agg = (
                    s.groupby("dataset")[METRICS].mean().mean()
                    if label == "macro"
                    else s[METRICS].mean()
                )
                summaries.append(
                    {
                        "experiment": exp,
                        "model": model,
                        "arm": arm,
                        "scope": label,
                        "n": len(s),
                        **agg.to_dict(),
                        "mean_candidates": s.n_candidates.mean(),
                        "single_candidate": int((s.n_candidates == 1).sum()),
                        **{
                            k: s[k].mean()
                            for k in [
                                "input_tokens",
                                "output_tokens",
                                "image_tokens",
                                "text_tokens",
                                "wall_time_s",
                            ]
                        },
                    }
                )
            for strat in ["granularity", "fault_type"]:
                for value, s in ar.groupby(strat):
                    strata.append(
                        {
                            "experiment": exp,
                            "model": model,
                            "arm": arm,
                            "stratum": strat,
                            "value": value,
                            "n": len(s),
                            **s[METRICS].mean().to_dict(),
                        }
                    )
save("denominators.json", denoms)
table("paired_arm_metrics", summaries)
table("fault_granularity", strata)
summary = pd.DataFrame(summaries)

tests = []
for exp, a in analyses.items():
    for t in chain(a["primary_family"], *a["secondary_families"].values()):
        tests.append(
            {"experiment": exp, **{k: v for k, v in t.items() if k != "cases"}}
        )
table("registered_tests", tests)
save("registered_tests.json", tests)
group_tests = []
for t in tests:
    g = t["event_group_sensitivity"]
    group_tests.append(
        {
            **{k: t[k] for k in ["experiment", "family", "model", "contrast"]},
            **{k: g[k] for k in ["groups", "delta_mrr", "paired_dz", "p"]},
        }
    )
for experiment, family in {(t["experiment"], t["family"]) for t in group_tests}:
    group = [
        t for t in group_tests if (t["experiment"], t["family"]) == (experiment, family)
    ]
    maximum = 0.0
    for i, t in enumerate(sorted(group, key=lambda t: t["p"])):
        maximum = max(maximum, min(1.0, t["p"] * (len(group) - i)))
        t["holm_sensitivity"] = maximum
table("event_group_sensitivity", group_tests)


def contrast(exp, model, newer, base, cases=None):
    eligible = sorted(
        set(
            df[
                (df.experiment == exp)
                & (df.model == model)
                & (df.status == "done")
                & (df.arm == newer)
            ].case
        )
        & set(
            df[
                (df.experiment == exp)
                & (df.model == model)
                & (df.status == "done")
                & (df.arm == base)
            ].case
        )
    )
    if cases is not None:
        eligible = [c for c in eligible if c in cases]
    a = {c: raw_index[exp, model, c, newer]["metrics"] for c in eligible}
    b = {c: raw_index[exp, model, c, base]["metrics"] for c in eligible}
    delta = np.array([a[c]["mrr"] - b[c]["mrr"] for c in eligible])
    vals = {
        d: [a[c]["mrr"] - b[c]["mrr"] for c in eligible if private[c]["dataset"] == d]
        for d in DATASETS
    }
    return {
        "experiment": exp,
        "model": model,
        "contrast": newer + "-" + base,
        "n": len(eligible),
        "delta_pooled": float(delta.mean()) if len(delta) else None,
        "delta_macro": float(np.mean([np.mean(v) for v in vals.values() if v]))
        if len(delta)
        else None,
        "delta_by_dataset": {
            d: float(np.mean(v)) if v else None for d, v in vals.items()
        },
        "repair1": sum(a[c]["ac@1"] > b[c]["ac@1"] for c in eligible),
        "break1": sum(a[c]["ac@1"] < b[c]["ac@1"] for c in eligible),
        "within_top5_to_top1": sum(
            a[c]["ac@1"] and not b[c]["ac@1"] and b[c]["ac@5"] for c in eligible
        ),
        "new_top5": sum(a[c]["ac@5"] > b[c]["ac@5"] for c in eligible),
        "lost_top5": sum(a[c]["ac@5"] < b[c]["ac@5"] for c in eligible),
        "mrr_better": int((delta > 1e-10).sum()),
        "mrr_worse": int((delta < -1e-10).sum()),
        "identical_responses": sum(
            outputs[exp, model, c, newer]["response"]
            == outputs[exp, model, c, base]["response"]
            for c in eligible
        ),
        "p_exploratory": float(wilcoxon(delta, zero_method="pratt").pvalue)
        if np.any(delta)
        else 1.0,
        "dz": float(delta.mean() / delta.std(ddof=1))
        if len(delta) > 1 and delta.std(ddof=1) > 0
        else None,
        "cases": eligible,
    }


extra = [
    contrast(e, m, a, b)
    for e, pairs in {
        "A": [
            ("E_S_D_P", "E_P_D_P"),
            ("E_S_D_S", "E_P_D_S"),
            ("E_P_D_S", "E_P_D_P"),
            ("E_S_D_S", "E_S_D_P"),
        ],
        "B": [
            ("J_COND", "TPV"),
            ("J_JOINT", "TPV"),
            ("J_MARG", "TPV"),
            ("J_COND", "MORE"),
            ("W_NO_K", "TPV"),
        ],
    }.items()
    for m in MODELS
    for a, b in pairs
]
for e in EXPS:
    group = [t for t in extra if t["experiment"] == e]
    maximum = 0.0
    for i, t in enumerate(sorted(group, key=lambda t: t["p_exploratory"])):
        maximum = max(maximum, min(1.0, t["p_exploratory"] * (len(group) - i)))
        t["holm_exploratory"] = maximum
save("conditional_contrasts.json", extra)
table(
    "conditional_contrasts",
    [{k: v for k, v in t.items() if k != "cases"} for t in extra],
)

# Per-case availability and actual model-visible input manipulations.
profiles, packs, audits = [], [], []
for row in reg["rosters"]["screen"]:
    c, d = row["opaque_incident_id"], row["dataset"]
    pool = read_json(RUN / "pool_audits" / (c + ".json"))
    selected = pool["selected"]
    profiles.append(
        {
            "case": c,
            "dataset": d,
            "selected": len(selected),
            "request_pool": pool["request_packs"],
            "scope_pool": pool["scope_packs"],
            "no_op": not selected,
            "root_local_selected": any(root_hit(c, p["entity"]) for p in selected),
            "root_entry_selected": any(
                root_hit(c, p["entry_entity"]) for p in selected
            ),
            "request_audit": pool["request_audit"],
            "source_audit": pool["source_audit"],
        }
    )
    for p in selected:
        a, b, cc, dd = p["counts"]
        packs.append(
            {
                "case": c,
                "dataset": d,
                "id": p["id"],
                "entity": p["entity"],
                "entry": p["entry_entity"],
                "family": p["family"],
                "x": p["x"],
                "y": p["y"],
                "operation": p["operation"],
                "counts": p["counts"],
                "a": a,
                "b": b,
                "c": cc,
                "d": dd,
                "delta": a / (a + b) - cc / (cc + dd),
                "min_group": min(a + b, cc + dd),
                "same_entity_entry": p["entity"] == p["entry_entity"],
                "root_local": root_hit(c, p["entity"]),
                "root_entry": root_hit(c, p["entry_entity"]),
            }
        )
    for m in MODELS:
        available = {
            a: visible_identity(prompts["B", m, c, a])
            for a in ARMS["B"]
            if ("B", m, c, a) in prompts
        }
        if "TPV" in available:
            for arm in ["J_MARG", "J_JOINT", "J_COND"]:
                if arm not in available:
                    continue
                base, changed = available["TPV"], available[arm]
                same = base == changed
                assert same == (not selected), (c, m, arm, "unexpected no-op")
                restored = (
                    changed["parts"]
                    if same
                    else changed["parts"][:-2] + changed["parts"][-1:]
                )
                assert restored == base["parts"], (c, m, arm, "changed base")
                audits.append(
                    {
                        "case": c,
                        "model": m,
                        "arm": arm,
                        "same_as_tpv": same,
                        "tpv_backbone_preserved": True,
                    }
                )
        for ev in ["P", "S"]:
            keys = [("A", m, c, f"E_{ev}_D_{x}") for x in ["P", "S"]]
            if all(k in prompts for k in keys):
                a, b = [visible_identity(prompts[k]) for k in keys]
                assert (
                    a["parts"][:1] + a["parts"][2:] == b["parts"][:1] + b["parts"][2:]
                )
                assert a["parts"][1] != b["parts"][1]
                audits.append(
                    {
                        "case": c,
                        "model": m,
                        "arm": "A_D_" + ev,
                        "facts_same": True,
                        "instruction_changed": True,
                    }
                )
    for exp in EXPS:
        for arm in ARMS[exp]:
            keys = [(exp, m, c, arm) for m in MODELS]
            if all(k in prompts for k in keys):
                assert visible_identity(prompts[keys[0]]) == visible_identity(
                    prompts[keys[1]]
                ), (c, arm, "cross-model input mismatch")
save("source_profiles.json", profiles)
table("selected_packs", packs)
table("manipulation_audit", audits)
active = {p["case"] for p in profiles if not p["no_op"]}
subgroups = []
for model in MODELS:
    for label, cases in [
        ("active", active),
        ("no_op", set(private) - active),
        (
            "root_local_selected",
            {p["case"] for p in profiles if p["root_local_selected"]},
        ),
        (
            "no_root_local_selected",
            {p["case"] for p in profiles if not p["root_local_selected"]},
        ),
    ]:
        for arm in ["J_MARG", "J_JOINT", "J_COND"]:
            subgroups.append(
                {"subgroup": label, **contrast("B", model, arm, "TPV", cases)}
            )
save("availability_subgroups.json", subgroups)
table(
    "availability_subgroups",
    [{k: v for k, v in t.items() if k != "cases"} for t in subgroups],
)

# Cross-experiment baseline comparisons are exploratory and use all-12 common
# cases, not inconsistent stage-specific denominators.
cross = []
for m in MODELS:
    good = set(private) - set(df[(df.model == m) & (df.status != "done")].case)
    for e, arm in [
        ("A", "E_S_D_P"),
        ("A", "T_NATIVE"),
        ("A", "SIRCL_IDS_NATIVE"),
        ("B", "TPV"),
        ("B", "MORE"),
        ("B", "W_NO_K"),
        ("B", "J_COND"),
    ]:
        s = df[
            (df.model == m)
            & (df.experiment == e)
            & (df.arm == arm)
            & df.case.isin(good)
        ]
        cross.append(
            {
                "model": m,
                "experiment": e,
                "arm": arm,
                "n": len(s),
                **s.groupby("dataset")[METRICS].mean().mean().to_dict(),
                **{d: s[s.dataset == d].mrr.mean() for d in DATASETS},
            }
        )
table("cross_stage_common", cross)

# Deterministic selection from actual repair/break groups, not compelling prose.
samples = []
for exp, newer, base in [
    ("A", "E_S_D_P", "E_P_D_P"),
    ("A", "E_S_D_P", "E_S_D_S"),
    ("B", "J_COND", "TPV"),
    ("B", "W_NO_K", "TPV"),
]:
    for model in MODELS:
        for label, test in [
            ("repair", lambda a, b: a["ac@1"] > b["ac@1"]),
            ("break", lambda a, b: a["ac@1"] < b["ac@1"]),
        ]:
            eligible = [
                c
                for c in private
                if (exp, model, c, newer) in outputs
                and (exp, model, c, base) in outputs
                and test(
                    raw_index[exp, model, c, newer]["metrics"],
                    raw_index[exp, model, c, base]["metrics"],
                )
            ]
            if not eligible:
                continue
            c = min(
                eligible, key=lambda c: digest([42, exp, model, newer, base, label, c])
            )
            records = []
            for arm in [base, newer]:
                k = (exp, model, c, arm)
                item = raw_index[k]
                d = Path(item["artifact_root"])
                call = item["call_key"]
                records.append(
                    {
                        "arm": arm,
                        "metrics": item["metrics"],
                        "response": outputs[k]["response"],
                        "prompt": str(d / "prompts" / (call + ".json")),
                        "conversation": str(d / "conversations" / (call + ".md")),
                        "audit": read_json(d / "audits" / (call + ".json")),
                    }
                )
            samples.append(
                {
                    "case": c,
                    "dataset": private[c]["dataset"],
                    "model": model,
                    "experiment": exp,
                    "type": label,
                    "contrast": newer + "-" + base,
                    "root": private[c]["accepted_labels"],
                    "root_ids": private[c]["accepted_label_numeric_ids"],
                    "fault_type": private[c]["fault_type"],
                    "records": records,
                    "packs": [p for p in packs if p["case"] == c],
                }
            )
save("qualitative_samples.json", samples)

# Diagnostics count model outcomes; literal extraction is partial, not a
# calibrated hallucination detector, and unknown claims are never called false.
diag = []
for (e, m, a), s in df[df.status == "done"].groupby(["experiment", "model", "arm"]):
    diag.append(
        {
            "experiment": e,
            "model": m,
            "arm": a,
            "n": len(s),
            "model_failures": int((s.model_status == "model_failure").sum()),
            "unknown_outputs": int((s.unknown_ids > 0).sum()),
            "parse_failures": int((~s.json_parsed.astype(bool)).sum()),
            "duplicates": int((s.duplicate_ids > 0).sum()),
            "mean_candidates": s.n_candidates.mean(),
            "single_candidate": int((s.n_candidates == 1).sum()),
            "reason_refuted": int((s.literal_refuted > 0).sum()),
            "top1": int(s["ac@1"].sum()),
            "rank2_5": int(((s["ac@5"] == 1) & (s["ac@1"] == 0)).sum()),
            "outside5": int((s["ac@5"] == 0).sum()),
            "finish": dict(Counter(s.finish_reason)),
            "new_calls": int(s.new_generation_calls.sum()),
        }
    )
table("output_diagnostics", diag)
save("output_diagnostics.json", diag)
costs = []
for (e, m, a), s in df.groupby(["experiment", "model", "arm"]):
    costs.append(
        {
            "experiment": e,
            "model": m,
            "arm": a,
            "planned": len(s),
            **{
                k + "_" + suffix: v
                for k in [
                    "input_tokens",
                    "output_tokens",
                    "image_tokens",
                    "text_tokens",
                    "wall_time_s",
                ]
                for suffix, v in [
                    ("n", int(s[k].notna().sum())),
                    ("mean", s[k].mean()),
                    ("median", s[k].median()),
                    ("p95", s[k].quantile(0.95)),
                ]
            },
        }
    )
table("cost_runtime", costs)
integrity.update(
    done=int((df.status == "done").sum()),
    fail=int((df.status == "fail").sum()),
    new_formal_calls=int(df.new_generation_calls.fillna(0).sum())
    + int((df.status == "fail").sum()),
    unique_complete_requests=len(
        {(r["model"], r["call_key"]) for r in rows if r["status"] == "done"}
    ),
    source_availability=read_json(RUN / "analysis/source_availability.json")["summary"],
    selected_packs=len(packs),
    paired_input_audits=len(audits),
    raw_finish_reasons=dict(Counter(df[df.status == "done"].finish_reason)),
    scope_packs=sum(p["family"] == "scope" for p in packs),
)
integrity["warnings"].append(
    "Runtime granularity summary used an entity map, not gold-root type; offline strata corrected without changing scores."
)
save("integrity.json", integrity)

# Figures use recorded scores without CIs or resampled pseudo-cases.
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "figure.dpi": 150})
colors = ["#2A6F97", "#E29536"]
fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
for ax, e in zip(axes, EXPS):
    x = np.arange(len(ARMS[e]))
    for i, m in enumerate(MODELS):
        s = (
            summary[
                (summary.experiment == e)
                & (summary.model == m)
                & (summary.scope == "macro")
            ]
            .set_index("arm")
            .loc[ARMS[e]]
        )
        bars = ax.bar(
            x + (i - 0.5) * 0.36, s.mrr, 0.36, label=m.split("-")[0], color=colors[i]
        )
        ax.bar_label(bars, fmt="%.3f", fontsize=8, padding=2)
    ax.set_xticks(x, ARMS[e], rotation=32, ha="right")
    ax.set_ylim(0, 0.55)
    ax.set_ylabel("Dataset-macro MRR")
    ax.set_title(
        "A: evidence / instruction" if e == "A" else "B: outcome-linked evidence"
    )
    ax.legend()
fig.tight_layout()
fig.savefig(OUT / "01_mrr.png")
plt.close(fig)
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for i, e in enumerate(EXPS):
    for j, m in enumerate(MODELS):
        ax = axes[i, j]
        s = summary[
            (summary.experiment == e)
            & (summary.model == m)
            & summary.scope.isin(DATASETS)
        ]
        mat = s.pivot(index="arm", columns="scope", values="mrr").reindex(
            index=ARMS[e], columns=DATASETS
        )
        im = ax.imshow(mat, vmin=0, vmax=0.65, cmap="YlGnBu", aspect="auto")
        for row in range(len(mat)):
            for col in range(3):
                ax.text(
                    col,
                    row,
                    f"{mat.iloc[row, col]:.3f}",
                    ha="center",
                    va="center",
                    color="white" if mat.iloc[row, col] > 0.4 else "black",
                )
        ax.set_yticks(range(len(mat)), mat.index)
        ax.set_xticks(range(3), DATASETS)
        ax.set_title(e + " / " + m)
fig.tight_layout()
fig.savefig(OUT / "02_datasets.png")
plt.close(fig)
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, m in zip(axes, MODELS):
    s = summary[
        (summary.experiment == "A") & (summary.model == m) & (summary.scope == "macro")
    ].set_index("arm")
    for ev, col in [("P", colors[0]), ("S", colors[1])]:
        y = [s.loc[f"E_{ev}_D_{d}", "mrr"] for d in ["P", "S"]]
        ax.plot([0, 1], y, "o-", label=ev + " evidence", color=col)
    ax.set_xticks([0, 1], ["Parent discipline", "SIRCL discipline"])
    ax.set_ylim(0.15, 0.48)
    ax.set_title(m)
    ax.set_ylabel("Macro MRR")
    ax.legend()
fig.tight_layout()
fig.savefig(OUT / "03_factorial.png")
plt.close(fig)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
avail = pd.DataFrame(profiles)
counts = [sum((avail.dataset == d) & ~avail.no_op) for d in DATASETS]
axes[0].bar(DATASETS, counts, label="J active", color=colors[0])
axes[0].bar(
    DATASETS,
    20 - np.array(counts),
    bottom=counts,
    label="Exact TPV no-op",
    color="#bbbbbb",
)
axes[0].set_ylabel("Cases")
axes[0].legend()
axes[0].set_title("Actual intervention coverage")
for j, m in enumerate(MODELS):
    ts = [
        next(
            t
            for t in subgroups
            if t["model"] == m
            and t["contrast"] == a + "-TPV"
            and t["subgroup"] == "active"
        )
        for a in ["J_MARG", "J_JOINT", "J_COND"]
    ]
    axes[1].bar(
        np.arange(3) + (j - 0.5) * 0.36,
        [t["delta_pooled"] for t in ts],
        0.36,
        label=m.split("-")[0],
        color=colors[j],
    )
axes[1].axhline(0, color="black", linewidth=0.6)
axes[1].set_xticks(range(3), ["J_MARG", "J_JOINT", "J_COND"])
axes[1].set_ylabel("Active-case paired delta MRR")
axes[1].legend()
axes[1].set_title("Not dilution by no-ops alone")
fig.tight_layout()
fig.savefig(OUT / "04_joint_coverage.png")
plt.close(fig)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
diagnostic = pd.DataFrame(diag)
for ax, m in zip(axes, MODELS):
    s = diagnostic[diagnostic.model == m].set_index("arm").loc[ARMS["A"] + ARMS["B"]]
    bottom = np.zeros(len(s))
    for col, color in [
        ("top1", "#2a9d8f"),
        ("rank2_5", "#e9c46a"),
        ("outside5", "#e76f51"),
    ]:
        values = s[col] / s.n
        ax.bar(np.arange(len(s)), values, bottom=bottom, label=col, color=color)
        bottom += values
    ax.set_xticks(range(len(s)), s.index, rotation=65, ha="right", fontsize=8)
    ax.set_title(m)
    ax.set_ylabel("Fraction of completed responses")
    ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "05_rank_depth.png")
plt.close(fig)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, m in zip(axes, MODELS):
    s = summary[(summary.model == m) & (summary.scope == "macro")]
    for _, v in s.iterrows():
        ax.scatter(
            v.input_tokens, v.mrr, color=colors[0] if v.experiment == "A" else colors[1]
        )
        ax.annotate(
            v.arm,
            (v.input_tokens, v.mrr),
            fontsize=7,
            xytext=(3, 3),
            textcoords="offset points",
        )
    ax.set_title(m)
    ax.set_xlabel("Mean input tokens (image included)")
    ax.set_ylabel("Macro MRR")
fig.tight_layout()
fig.savefig(OUT / "06_cost.png")
plt.close(fig)

with (OUT / "full_tables.md").open("w") as stream:
    stream.write("# RQ3.5 A/B screen60 full tables\n\n")
    for name, data in [
        ("Paired performance", summaries),
        ("Registered tests", tests),
        ("Root/fault strata", strata),
        ("Output diagnostics", diag),
        ("Cost/runtime", costs),
    ]:
        stream.write(
            "## " + name + "\n\n" + pd.DataFrame(data).to_markdown(index=False) + "\n\n"
        )
print(json.dumps(integrity, ensure_ascii=False, indent=2))
print(
    "MACRO\n",
    summary[summary.scope == "macro"][
        ["experiment", "model", "arm", "n", "mrr", "ac@1", "ac@5", "mean_candidates"]
    ].to_string(index=False),
)

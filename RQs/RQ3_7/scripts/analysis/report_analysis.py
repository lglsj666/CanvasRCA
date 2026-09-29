"""Offline, evaluator-private RQ37 report supplement; no inference/runtime edits.

Run from repository root with the tools environment. Reads completed artifacts;
writes only report assets. Registered tests are copied unchanged. Additional
tests are explicitly exploratory and use rounded paired differences for ties.
"""

import hashlib
import json
import re
import shutil
import sqlite3
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from scipy.stats import binomtest, wilcoxon

ROOT = Path(__file__).resolve().parents[4]
RUN = ROOT / "RQs/RQ3_7/results/fusion_v2_pruned"
OUT = ROOT / "docs/experiment_reports/RQ3_7_Results_Analysis_2026-09-28_assets"
MODELS = ["qwen3.8-27b", "gemma-4-26b-a4b"]
ARMS = [
    "TPV_REF",
    "B3_G_REF",
    "T_MATCH",
    "REMOTE_ID",
    "REMOTE_LINK",
    "LOCAL_ID",
    "LOCAL_LINK",
]
CORE = ARMS[2:]
DATASETS = ["aiops2022", "aiops2025", "aegislab"]


def read(path):
    return json.loads(Path(path).read_text())


def save(name, value):
    (OUT / (name + ".json")).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=lambda x: x.item())
        + "\n"
    )


def test(values):
    a = np.round(np.asarray(values, dtype=float), 12)
    sd = a.std(ddof=1) if len(a) > 1 else 0
    return {
        "n": len(a),
        "delta": float(a.mean()),
        "p": float(wilcoxon(a, zero_method="pratt").pvalue) if np.any(a) else 1.0,
        "dz": float(a.mean() / sd) if sd > 1e-12 else None,
    }


def holm(rows):
    prev = 0
    for i, r in enumerate(sorted(rows, key=lambda x: x["p"])):
        prev = max(prev, min(1.0, r["p"] * (len(rows) - i)))
        r["holm_p"] = prev


def paired(core, model, baseline):
    f = core[core.model.eq(model)]
    x = f[f.arm.eq("LOCAL_LINK")].set_index("case")
    y = f[f.arm.eq(baseline)].set_index("case")
    ids = sorted(set(x.index) & set(y.index))
    a, b = x.loc[ids], y.loc[ids]
    o = a[["dataset", "level", "fault_type", "group"]].copy()
    o["new"], o["old"] = a.mrr, b.mrr
    o["delta"] = o.new - o.old
    o["repair"] = (a["ac@1"] == 1) & (b["ac@1"] == 0)
    o["break"] = (a["ac@1"] == 0) & (b["ac@1"] == 1)
    o["new_top5"] = (a["ac@5"] == 1) & (b["ac@5"] == 0)
    o["lost_top5"] = (a["ac@5"] == 0) & (b["ac@5"] == 1)
    o["tail_to_top"] = (b.mrr > 0) & (b.mrr < 1) & (a.mrr == 1)
    o["out_to_top"] = (b.mrr == 0) & (a.mrr == 1)
    return o


def main():
    OUT.mkdir(exist_ok=True)
    f = pd.read_csv(RUN / "analysis/per_case.csv", keep_default_na=False)
    for c in [
        "mrr",
        "ac@1",
        "ac@3",
        "ac@5",
        "avg@3",
        "avg@5",
        "input_tokens",
        "output_tokens",
        "image_tokens",
        "text_tokens",
        "wall_time_s",
        "candidate_count",
        "unknown_id_count",
    ]:
        f[c] = pd.to_numeric(f[c], errors="coerce")
    priv = {
        c: read(ROOT / "RQs/RQ3_4/results/integrated_v1/private" / (c + ".json"))
        for c in f.case.unique()
    }

    def level(c):
        p = priv[c]
        ls = {p["entity_granularity"].get(x, "unknown") for x in p["accepted_labels"]}
        return "/".join(sorted(ls))

    f["level"] = f.case.map(level)
    # The inherited analyzer calls mixed accepted service/pod aliases 'unknown'.
    # Report them explicitly; never change the frozen scoring/accepted labels.
    save(
        "granularity_resolution",
        [
            {
                "case": c,
                "level": level(c),
                "accepted": priv[c]["accepted_label_numeric_ids"],
            }
            for c in priv
        ],
    )
    a = f[f.experiment.eq("A")]
    cores = []
    excluded = {}
    for m in MODELS:
        g = a[a.model.eq(m)]
        bad = set(g[g.arm.isin(CORE) & g.mrr.isna()].case)
        excluded[m] = sorted(bad)
        cores.append(g[~g.case.isin(bad) & g.mrr.notna()])
    core = pd.concat(cores)
    core.to_csv(OUT / "A_core_records.csv", index=False)
    summary = read(RUN / "analysis/summary.json")
    for n in [
        "summary",
        "comparisons",
        "granularity",
        "robustness_statistics",
        "expansion",
    ]:
        save("registered_" + n, read(RUN / "analysis" / (n + ".json")))
    pd.DataFrame(summary).to_csv(OUT / "all_metrics.csv", index=False)

    pairs, strata, movement, all7, case_choices = [], [], [], [], []
    for m in MODELS:
        for base in ["TPV_REF", "B3_G_REF", "T_MATCH", "REMOTE_ID"]:
            p = paired(core, m, base)
            pairs.append(
                {
                    "model": m,
                    "baseline": base,
                    "new_mean": p.new.mean(),
                    "old_mean": p.old.mean(),
                    **test(p.delta),
                }
            )
            movement.append(
                {
                    "model": m,
                    "baseline": base,
                    "n": len(p),
                    **{
                        k: int(p[k].sum())
                        for k in [
                            "repair",
                            "break",
                            "tail_to_top",
                            "out_to_top",
                            "new_top5",
                            "lost_top5",
                        ]
                    },
                    "rr_up": int((p.delta > 1e-10).sum()),
                    "rr_down": int((p.delta < -1e-10).sum()),
                }
            )
            for axis in ["dataset", "level", "fault_type"]:
                for name, g in p.groupby(axis):
                    strata.append(
                        {
                            "model": m,
                            "baseline": base,
                            "axis": axis,
                            "stratum": name,
                            "new_mean": g.new.mean(),
                            "old_mean": g.old.mean(),
                            "repair": int(g.repair.sum()),
                            "break": int(g["break"].sum()),
                            **test(g.delta),
                        }
                    )
            for direction, selector in [("repair", p.repair), ("break", p["break"])]:
                for dataset in DATASETS:
                    s = p[selector & p.dataset.eq(dataset)]
                    if len(s):
                        c = min(
                            s.index,
                            key=lambda x: hashlib.sha256(x.encode()).hexdigest(),
                        )
                        case_choices.append(
                            {
                                "model": m,
                                "baseline": base,
                                "direction": direction,
                                "case": c,
                                **s.loc[c].to_dict(),
                            }
                        )
        g = core[core.model.eq(m)]
        ids = set.intersection(*(set(g[g.arm.eq(arm)].case) for arm in ARMS))
        for arm, sub in g[g.case.isin(ids)].groupby("arm"):
            all7.append({"model": m, "arm": arm, "n": len(sub), "mrr": sub.mrr.mean()})
    holm(pairs)
    for axis in ["dataset", "level", "fault_type"]:
        holm([r for r in strata if r["axis"] == axis])
    save("primary_rounded_tie_sensitivity", pairs)
    save("exploratory_strata", strata)
    pd.DataFrame(strata).to_csv(OUT / "exploratory_strata.csv", index=False)
    save("rank_movement", movement)
    save("all_seven_common_sensitivity", all7)
    save("case_review_sampling", case_choices)

    levels = (
        core.groupby(["model", "arm", "level"])
        .agg(n=("mrr", "size"), mrr=("mrr", "mean"), ac1=("ac@1", "mean"))
        .reset_index()
    )
    levels.to_csv(OUT / "level_performance.csv", index=False)
    faults = (
        core.groupby(["model", "arm", "dataset", "fault_type"])
        .agg(n=("mrr", "size"), mrr=("mrr", "mean"), ac1=("ac@1", "mean"))
        .reset_index()
    )
    faults.to_csv(OUT / "fault_performance.csv", index=False)

    # Integrity: inventory small completion manifests, not a resume revalidation.
    unique = f[f.status.eq("done")].drop_duplicates(["artifact_root", "call_key"])
    missing, parse_states, finish_states = [], Counter(), Counter()
    for _, r in unique.iterrows():
        root, key = Path(r.artifact_root), r.call_key
        completion = root / "completed" / (key + ".json")
        if not completion.exists():
            missing.append(str(completion))
            continue
        c = read(completion)
        paths = [
            "inputs/" + key + ".json",
            "outputs/" + key + ".json",
            "cost/" + key + ".json",
            *c.get("response_artifact_hashes", {}).keys(),
        ]
        missing += [str(root / p) for p in paths if not (root / p).is_file()]
        o = read(root / "outputs" / (key + ".json"))
        parse_states[o.get("score", {}).get("status", "unknown")] += 1
        cost = read(root / "cost" / (key + ".json"))
        finish_states[
            str(cost.get("raw", {}).get("finish_reason", "unrecorded_here"))
        ] += 1
    flags = [read(p) for p in (RUN / "flags").glob("*.json")]
    formal_flags = [
        r
        for r in flags
        if r.get("experiment") in ["A", "B"]
        and r.get("dimensions", {}).get("cohort") in ["development", "robustness"]
    ]
    assert len(formal_flags) == 4140, len(formal_flags)
    flagidx = {
        (
            x["experiment"],
            x["model"],
            x["case"],
            x["dimensions"]["arm"],
            x["dimensions"]["encoding"],
        ): x
        for x in formal_flags
    }
    save(
        "integrity",
        {
            "rows": len(f),
            "unique_success_artifacts": len(unique),
            "missing_paths": missing,
            "output_score_status": dict(parse_states),
            "cost_finish_status": dict(finish_states),
            "A_excluded_cases": excluded,
            "terminal_status_counts": f.groupby(
                ["experiment", "model", "status", "failure_class"]
            )
            .size()
            .reset_index(name="n")
            .to_dict("records"),
        },
    )
    f[f.status.ne("done")].to_csv(OUT / "failures.csv", index=False)
    output_stats = (
        core.groupby(["model", "arm"])
        .agg(
            n=("case", "size"),
            mean_predictions=("candidate_count", "mean"),
            illegal_ids=("unknown_id_count", "sum"),
        )
        .reset_index()
    )
    output_stats["single_prediction"] = [
        int(
            (
                (core.model == r.model)
                & (core.arm == r.arm)
                & core.candidate_count.eq(1)
            ).sum()
        )
        for r in output_stats.itertuples()
    ]
    output_stats.to_csv(OUT / "output_quality.csv", index=False)
    type_checks = []
    for r in core.itertuples():
        p = priv[r.case]
        mentions = re.findall(
            r"\b(service|pod|node)\s+(\d{3,5})\b", str(r.reason), re.IGNORECASE
        )
        mistakes = []
        for label, ident in mentions:
            natural = p["numeric_to_natural"].get(ident)
            actual = p["entity_granularity"].get(natural)
            if actual and label.lower() != actual:
                mistakes.append(
                    {"id": ident, "claimed": label.lower(), "actual": actual}
                )
        type_checks.append(
            {
                "model": r.model,
                "arm": r.arm,
                "case": r.case,
                "mentions": len(mentions),
                "mistakes": mistakes,
                "mismatch": bool(mistakes),
            }
        )
    save("explicit_entity_type_scan", type_checks)
    pd.DataFrame(type_checks).groupby(["model", "arm"]).agg(
        n=("case", "size"), explicit_mismatch=("mismatch", "sum")
    ).reset_index().to_csv(OUT / "explicit_type_summary.csv", index=False)

    # Every five-arm case's fact/panel/geometry identities and actual pixel actions.
    audits, features = [], []
    for case in sorted(priv):
        projections = {}
        for arm in CORE:
            flag = flagidx.get(("A", MODELS[0], case, arm, "NATIVE"))
            if not flag or not flag.get("projection_path"):
                flag = flagidx.get(("A", MODELS[1], case, arm, "NATIVE"))
            if flag and flag.get("projection_path"):
                projections[arm] = read(flag["projection_path"])
        if "LOCAL_LINK" not in projections:
            continue
        p = projections["LOCAL_LINK"]
        audits.append(
            {
                "case": case,
                "n_projections": len(projections),
                **{
                    field + "_count": len(
                        {x[field] for x in projections.values() if field in x}
                    )
                    for field in ["fact_hash", "panel_hash"]
                },
                "visual_geometry_count": len(
                    {
                        x["geometry_hash"]
                        for k, x in projections.items()
                        if k != "T_MATCH"
                    }
                ),
                "visual_pixel_count": len(
                    {x["image_hash"] for k, x in projections.items() if k != "T_MATCH"}
                ),
                "cross_model_same_pixels": all(
                    not (other := flagidx.get(("A", MODELS[1], case, k, "NATIVE")))
                    or read(other["projection_path"])["image_hash"] == x["image_hash"]
                    for k, x in projections.items()
                ),
            }
        )
        feat = p["numeric_applicability"].copy()
        gold = set(priv[case]["accepted_label_numeric_ids"].values())
        panels = {
            x["entity"] for x in p["primitives"] if x["kind"] in ["readings", "bars"]
        }
        feat.update(
            case=case,
            dataset=priv[case]["dataset"],
            level=level(case),
            gold_direct_panel=bool(gold & panels),
            gold_isolated_panel=bool(gold & set(feat["isolated_panel_owners"])),
            isolated_panel_count=len(feat["isolated_panel_owners"]),
            nodes=sum(x["kind"] == "entity" for x in p["primitives"]),
        )
        flag = flagidx[("A", MODELS[0], case, "LOCAL_LINK", "NATIVE")]
        if not flag.get("artifact_root") or not flag.get("call_key"):
            flag = flagidx[("A", MODELS[1], case, "LOCAL_LINK", "NATIVE")]
        pngs = list(
            (Path(flag["artifact_root"]) / "renders").glob(flag["call_key"] + "*.png")
        )
        if pngs:
            with Image.open(pngs[0]) as im:
                feat["width"], feat["height"] = im.size
        features.append(feat)
    save("manipulation_audit", audits)
    feat = pd.DataFrame(features)
    feat.to_csv(OUT / "public_features_private_annotation.csv", index=False)
    feature_tests = []
    for m in MODELS:
        for base in ["T_MATCH", "REMOTE_ID", "B3_G_REF"]:
            p = paired(core, m, base).join(
                feat.set_index("case").drop(columns=["dataset", "level"])
            )
            for axis in ["gold_direct_panel", "gold_isolated_panel"]:
                for v, g in p.groupby(axis):
                    feature_tests.append(
                        {
                            "model": m,
                            "baseline": base,
                            "feature": axis,
                            "value": bool(v),
                            "new_mean": g.new.mean(),
                            "old_mean": g.old.mean(),
                            **test(g.delta),
                        }
                    )
    holm(feature_tests)
    save("feature_strata", feature_tests)
    bar_strata = []
    for m in MODELS:
        for base in ["T_MATCH", "REMOTE_ID", "B3_G_REF"]:
            p = paired(core, m, base).join(
                feat.set_index("case")[["continuous_bar_glyphs"]]
            )
            p = p[p.dataset == "aegislab"]
            for yes, g in p.groupby(p.continuous_bar_glyphs.gt(0)):
                bar_strata.append(
                    {
                        "model": m,
                        "baseline": base,
                        "has_bars": bool(yes),
                        "new_mean": g.new.mean(),
                        "old_mean": g.old.mean(),
                        **test(g.delta),
                    }
                )
    holm(bar_strata)
    save("aegis_bars_strata", bar_strata)

    # Robustness uses the registered common A/B cohort. Tests vs REPEAT are new,
    # exploratory; no multiple arm observations treated as independent cases.
    rob = pd.DataFrame(read(RUN / "analysis/robustness_pairs.json"))
    eligible, flip_tests = [], []
    for m in MODELS:
        for arm in ["T_MATCH", "REMOTE_ID", "LOCAL_LINK"]:
            g = rob[(rob.model == m) & (rob.arm == arm)]
            rep = g[g.encoding == "REPEAT"].set_index("case")
            for enc in ["SCIENTIFIC", "UNIT_EQUIVALENT"]:
                s = g[g.encoding == enc].set_index("case")
                if enc == "UNIT_EQUIVALENT":
                    s = s[s.transform_applicable]
                ids = sorted(s.index)
                r = rep.loc[ids]
                fl = s.first_rank_flip.astype(bool)
                rf = r.first_rank_flip.astype(bool)
                b = int((fl & ~rf).sum())
                c = int((~fl & rf).sum())
                eligible.append(
                    {
                        "model": m,
                        "arm": arm,
                        "encoding": enc,
                        "n": len(s),
                        "flips": int(fl.sum()),
                        "repeat_flips_same_cases": int(rf.sum()),
                        "mean_absolute_delta": s.delta_mrr.abs().mean(),
                        **test(s.delta_mrr),
                    }
                )
                flip_tests.append(
                    {
                        "model": m,
                        "arm": arm,
                        "encoding": enc,
                        "n": len(s),
                        "transform_only_flip": b,
                        "repeat_only_flip": c,
                        "p": binomtest(b, b + c, 0.5).pvalue if b + c else 1.0,
                    }
                )
    holm(flip_tests)
    save("applicable_robustness", eligible)
    save("exploratory_flip_vs_repeat", flip_tests)

    db = sqlite3.connect("file:" + str(RUN / "calls.sqlite") + "?mode=ro", uri=True)
    rows = db.execute(
        "select id,call_key,state,result,started from calls where call_key like '%rq37%' order by id"
    ).fetchall()
    db.close()
    accounting = []
    for i, key, state, result, started in rows:
        obj = json.loads(result) if result else {}
        accounting.append(
            {
                "id": i,
                "key": key,
                "state": state,
                "started": started,
                "input": obj.get("input_tokens"),
                "output": obj.get("output_tokens"),
                "image": obj.get("image_tokens"),
            }
        )
    save("call_accounting", accounting)
    case_assets(f)

    # Compact publication-oriented plots; no CIs or fabricated uncertainty bars.
    plt.rcParams.update(
        {"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}
    )
    s = pd.DataFrame(summary)
    s = s[(s.experiment == "A") & (s.encoding == "NATIVE")]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.7), sharey=True)
    for ax, m in zip(axes, MODELS):
        for j, d in enumerate(DATASETS):
            z = s[(s.model == m) & (s.subset == d)].set_index("arm").loc[ARMS]
            ax.bar(np.arange(7) + (0.24 * (j - 1)), z.mrr, 0.24, label=d)
        ax.set_xticks(np.arange(7), ARMS, rotation=35, ha="right")
        ax.set_title(m)
        ax.set_ylim(0, 0.75)
    axes[0].set_ylabel("MRR")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(OUT / "01_mrr_by_dataset.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, m in zip(axes, MODELS):
        g = (
            levels[levels.model == m]
            .pivot(index="arm", columns="level", values="mrr")
            .reindex(ARMS)
        )
        im = ax.imshow(g, vmin=0, vmax=0.8, cmap="YlGnBu")
        ax.set_xticks(range(len(g.columns)), g.columns)
        ax.set_yticks(range(7), g.index)
        ax.set_title(m)
        for i in range(7):
            for j in range(len(g.columns)):
                ax.text(
                    j,
                    i,
                    f"{g.iloc[i, j]:.3f}",
                    ha="center",
                    va="center",
                    color="white" if g.iloc[i, j] > 0.5 else "black",
                )
    fig.tight_layout()
    fig.savefig(OUT / "02_root_level.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, m in zip(axes, MODELS):
        z = [x for x in movement if x["model"] == m]
        x = np.arange(4)
        ax.bar(x - 0.18, [r["repair"] for r in z], 0.36, label="AC@1 repair")
        ax.bar(x + 0.18, [-r["break"] for r in z], 0.36, label="AC@1 break")
        ax.axhline(0, color="black", lw=0.7)
        ax.set_xticks(x, [r["baseline"] for r in z], rotation=15)
        ax.set_title(m)
    axes[0].set_ylabel("Cases: LOCAL_LINK vs baseline")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(OUT / "03_repair_break.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, m in zip(axes, MODELS):
        for j, enc in enumerate(["SCIENTIFIC", "UNIT_EQUIVALENT", "REPEAT"]):
            values = []
            for arm in ["T_MATCH", "REMOTE_ID", "LOCAL_LINK"]:
                z = rob[(rob.model == m) & (rob.arm == arm) & (rob.encoding == enc)]
                if enc == "UNIT_EQUIVALENT":
                    z = z[z.transform_applicable]
                values.append(z.first_rank_flip.mean())
            ax.bar(np.arange(3) + (j - 1) * 0.25, values, 0.25, label=enc)
        ax.set_xticks(range(3), ["T_MATCH", "REMOTE_ID", "LOCAL_LINK"])
        ax.set_title(m)
    axes[0].set_ylabel("First-ID flip rate (UNIT: applicable only)")
    axes[1].set_ylim(0, 0.24)
    axes[1].legend(fontsize=8, loc="upper center", ncol=3)
    fig.tight_layout()
    fig.savefig(OUT / "04_numeric_robustness.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, m in zip(axes, MODELS):
        z = s[(s.model == m) & (s.subset == "pooled")].set_index("arm").loc[ARMS]
        for i, (arm, r) in enumerate(z.iterrows()):
            ax.scatter(r.input_tokens / 1000, r.mrr, s=65)
            label = arm
            offset = (5, 5)
            if arm == "TPV_REF":
                offset = (5, -16)
            if arm == "LOCAL_ID":
                offset = (5, -12)
            if m == MODELS[1] and arm == "REMOTE_ID":
                label = "REMOTE_ID / LOCAL_LINK"
            if m == MODELS[1] and arm == "LOCAL_LINK":
                continue
            ax.annotate(
                label,
                (r.input_tokens / 1000, r.mrr),
                xytext=offset,
                textcoords="offset points",
                fontsize=8,
            )
        ax.set_xlabel("Mean input tokens (thousands)")
        ax.set_ylabel("MRR")
        ax.set_title(m)
        ax.margins(x=0.3, y=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "05_accuracy_input_cost.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, m in zip(axes, MODELS):
        g = core[(core.model == m) & core.arm.isin(CORE)]
        cats = ["1", "2-3", "4-5", "outside top5"]
        values = np.array(
            [
                [
                    sum(g[g.arm == a].mrr == 1),
                    sum((g[g.arm == a].mrr >= 1 / 3 - 1e-9) & (g[g.arm == a].mrr < 1)),
                    sum((g[g.arm == a].mrr > 0) & (g[g.arm == a].mrr < 1 / 3 - 1e-9)),
                    sum(g[g.arm == a].mrr == 0),
                ]
                for a in CORE
            ]
        )
        bottom = np.zeros(5)
        for j, c in enumerate(cats):
            ax.bar(range(5), values[:, j], bottom=bottom, label=c)
            bottom += values[:, j]
        ax.set_xticks(range(5), CORE, rotation=30, ha="right")
        ax.set_title(m)
    axes[0].set_ylabel("Ground-truth rank: cases")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "06_root_rank.png", dpi=170)
    plt.close(fig)
    save(
        "analysis_manifest",
        {
            "source": str(RUN),
            "source_csv_sha256": hashlib.sha256(
                (RUN / "analysis/per_case.csv").read_bytes()
            ).hexdigest(),
            "scoring": "unchanged frozen per-case metrics",
            "inference_calls": 0,
            "A_core_n": {
                m: int(core[(core.model == m) & (core.arm == "T_MATCH")].shape[0])
                for m in MODELS
            },
            "exploratory_families": {
                "strata": "each of dataset/level/fault_type, all 4 baselines x 2 models in one family per axis",
                "flip_vs_repeat": "12 exact paired McNemar/binomial comparisons",
            },
            "granularity": "mixed accepted pod/service aliases kept in separate pod/service group, not recoded as pod or service",
        },
    )
    print(
        json.dumps(
            {
                "assets": str(OUT),
                "unique_artifacts": len(unique),
                "missing_paths": len(missing),
                "calls": len(accounting),
            },
            ensure_ascii=False,
        )
    )


def case_assets(f):
    """Fixed reviewed examples, exact originals plus clearly named report crops."""
    cases = [
        "INC-38A22FDFB326",
        "INC-B63AC53AB86F",
        "INC-77C683F9B6C0",
        "INC-FDC8B6B87BEB",
        "INC-6E6E1B20F2D5",
        "INC-992C09A89DC9",
        "INC-B77D2FD0C248",
        "INC-331437929E47",
        "INC-491E85FD6009",
    ]
    review = []
    lines = [
        "# RQ3.7 案例原始回答与输入索引",
        "",
        "这是 evaluator-private 分析附件，不是给模型的输入。MRR 未重新评分。",
        "",
    ]
    for c in cases:
        pr = read(ROOT / "RQs/RQ3_4/results/integrated_v1/private" / (c + ".json"))
        lines += [
            "## " + c,
            "",
            f"数据集：{pr['dataset']}；fault：{pr['fault_type']}；可接受标签：{pr['accepted_label_numeric_ids']}。",
            "",
        ]
        sample = f[
            (f.case == c)
            & (f.status == "done")
            & f.arm.isin(["T_MATCH", "REMOTE_ID", "LOCAL_LINK", "B3_G_REF", "TPV_REF"])
        ]
        for r in sample.itertuples():
            root = Path(r.artifact_root)
            key = r.call_key
            parsed = read(root / "outputs" / (key + ".json"))
            conv = root / "conversations" / (key + ".md")
            raw = parsed["response"]
            assert raw in conv.read_text(), str(conv)
            lines += [
                f"### {r.experiment} / {r.model} / {r.arm} / {r.encoding}；MRR={r.mrr:.4f}",
                "",
                f"[完整 conversation]({conv}) · [模型输入]({root / 'inputs' / (key + '.json')})",
                "",
                "```json",
                raw[:5000] + (" [报告节选，完整输出见链接]" if len(raw) > 5000 else ""),
                "```",
                "",
            ]
            review.append(
                {
                    "case": c,
                    "model": r.model,
                    "experiment": r.experiment,
                    "arm": r.arm,
                    "encoding": r.encoding,
                    "mrr": r.mrr,
                    "conversation": str(conv),
                    "input": str(root / "inputs" / (key + ".json")),
                }
            )
        if c in ["INC-6E6E1B20F2D5", "INC-331437929E47"]:
            for arm in ["REMOTE_ID", "LOCAL_LINK"]:
                rr = sample[
                    (sample.experiment == "A")
                    & (sample.model == MODELS[0])
                    & (sample.arm == arm)
                ].iloc[0]
                source = next(
                    (Path(rr.artifact_root) / "renders").glob(rr.call_key + "*.png")
                )
                target = OUT / (c + "_" + arm + ".png")
                shutil.copyfile(source, target)
                with Image.open(source) as im:
                    if c == "INC-6E6E1B20F2D5" and arm == "LOCAL_LINK":
                        im.crop((350, 2140, 1260, 2700)).save(
                            OUT / "case_node_cpu_crop.png"
                        )
                    if c == "INC-331437929E47" and arm == "LOCAL_LINK":
                        im.crop((350, 1940, 1260, 3510)).save(
                            OUT / "case_memory_bars_crop.png"
                        )
                review.append(
                    {
                        "source_png": str(source),
                        "copied_png": str(target),
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    }
                )
    (OUT / "case_evidence.md").write_text("\n".join(lines) + "\n")
    save("case_artifact_index", review)


if __name__ == "__main__":
    main()

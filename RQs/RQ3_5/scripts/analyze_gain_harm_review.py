"""Offline, post-hoc, symmetric review of published report CSVs; no model calls.

Families: report-stage × axis, across all listed contrasts, subgroups and models.
Only n>=10 strata tested. Missing infrastructure outcomes are never zero-filled.
Case-complete cohort is frozen across the named arms within each report-stage.
Fault-label strata are evaluator-private explanations, never routing features.
"""

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / "docs/experiment_reports"
OUT = ROOT / "docs/experiment_plans/RQ3_6_gain_harm_assets"
MAIN = ["aiops2022", "aiops2025", "aegislab"]

# Fixed before inspecting this script's subgroup p-values. Historical registered
# families are not replaced. Stage cohorts here can differ from historical ones.
SPECS = [
    (
        "RQ1.1",
        "RQ1_1_RQ2_1_findings/assets/per_record.csv",
        "scope",
        "rq1_rca",
        [("TPV", "T"), ("V", "T"), ("MV", "T"), ("TCV", "T")],
    ),
    (
        "RQ2.1-selection",
        "RQ1_1_RQ2_1_findings/assets/per_record.csv",
        "scope",
        "selection",
        [
            ("P_TRACE_SC__T", "P0__T"),
            ("P_DIVERSITY__T", "P0__T"),
            ("P_SIGMA__T", "P0__T"),
        ],
    ),
    (
        "RQ2.1-encoding",
        "RQ1_1_RQ2_1_findings/assets/per_record.csv",
        "scope",
        "silhouette",
        [("S_G_LAYERED", "S0"), ("S_TABLE", "S0")],
    ),
    (
        "RQ2.1-layout",
        "RQ1_1_RQ2_1_findings/assets/per_record.csv",
        "scope",
        "composition",
        [("D_SCALE_150", "D0"), ("D_TOPOLOGY_CENTER", "D0"), ("D_PORTRAIT", "D0")],
    ),
    (
        "RQ3.2-selection",
        "RQ3_2_Results_Analysis_2026-09-22_assets/scored_cases_enriched.csv",
        "phase",
        "selection",
        [
            ("SC_FULL", "P0_CAL"),
            ("SC_FULL", "SC_NO_BACKBONE"),
            ("SC_FULL", "SC_NO_STRATA"),
            ("SC_MORE", "SC_FULL"),
        ],
    ),
    (
        "RQ3.3-check",
        "RQ3_3_Results_Analysis_2026-09-24_assets/response_audit.csv",
        "stage",
        "check",
        [("W_G", "TPV"), ("W_G", "W_T"), ("W_G", "P0_MORE_TRUE")],
    ),
    (
        "RQ3.4-check",
        "RQ3_4_Results_Analysis_2026-09-25_assets/response_audit.csv",
        "stage",
        "check",
        [("P1H1K0_G", "TPV"), ("P1H1K1_G", "P1H1K0_G"), ("P1H1K1_G", "P1H1K1_T")],
    ),
    (
        "RQ3.5-A",
        "RQ3_5_Screen_Analysis_2026-09-26_assets/per_record.csv",
        "experiment",
        "A",
        [
            ("E_S_D_P", "E_P_D_P"),
            ("E_P_D_S", "E_P_D_P"),
            ("E_S_D_S", "E_S_D_P"),
            ("E_P_D_P", "T_NATIVE"),
        ],
    ),
    (
        "RQ3.5-B",
        "RQ3_5_Screen_Analysis_2026-09-26_assets/per_record.csv",
        "experiment",
        "B",
        [("W_NO_K", "TPV"), ("J_COND", "TPV"), ("J_COND", "J_JOINT")],
    ),
]


def holm(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values)
    adjusted = np.maximum.accumulate(
        values[order] * (len(values) - np.arange(len(values)))
    )
    result = np.empty(len(values))
    result[order] = np.minimum(adjusted, 1.0)
    return result


def summarize(data, delta_col="delta"):
    delta = data[delta_col].to_numpy(float)
    n = len(delta)
    sd = float(delta.std(ddof=1)) if n > 1 else np.nan
    # Explicit asymptotic Pratt handling: tie/zero-heavy RR, not an exact test.
    p = np.nan
    if n >= 10:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            p = (
                float(wilcoxon(delta, zero_method="pratt", method="approx").pvalue)
                if np.any(delta)
                else 1.0
            )
    return {
        "n": n,
        "baseline_mrr": float(data.baseline.mean()),
        "new_mrr": float(data.new.mean()),
        "delta": float(delta.mean()),
        "dz": float(delta.mean() / sd) if sd > 0 else np.nan,
        "delta_ac1": float(
            (data.new.eq(1).astype(float) - data.baseline.eq(1).astype(float)).mean()
        ),
        "delta_tail_rr": float(
            (
                data.new.where(data.new.lt(1), 0)
                - data.baseline.where(data.baseline.lt(1), 0)
            ).mean()
        ),
        "p_raw": p,
        "improved": int((delta > 1e-9).sum()),
        "worsened": int((delta < -1e-9).sum()),
        "repair": int(((data.new == 1) & (data.baseline < 1)).sum()),
        "break_count": int(((data.baseline == 1) & (data.new < 1)).sum()),
        "new_top5": int(((data.new > 0) & (data.baseline == 0)).sum()),
        "lost_top5": int(((data.baseline > 0) & (data.new == 0)).sum()),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    metadata_path = (
        REPORTS / "RQ3_2_Results_Analysis_2026-09-22_assets/case_metadata.csv"
    )
    meta = pd.read_csv(metadata_path).set_index("case")
    assert meta.index.is_unique

    # A few old metadata rows say 'mixed' even when only service gold IDs
    # remain. Derive from the frozen 3/4/5-digit root-ID type contract and
    # cross-check against the newer reports' evaluator-private label audit.
    def root_type(value):
        types = {{3: "service", 4: "node", 5: "pod"}[len(x)] for x in value.split("|")}
        return "+".join(sorted(types))

    meta["root_granularity"] = meta.root_ids.map(root_type)
    for rel, key, kind in [
        (
            "RQ3_4_Results_Analysis_2026-09-25_assets/response_audit.csv",
            "case_id",
            "root_kind",
        ),
        (
            "RQ3_5_Screen_Analysis_2026-09-26_assets/per_record.csv",
            "case",
            "granularity",
        ),
    ]:
        audit = pd.read_csv(REPORTS / rel).drop_duplicates(key).set_index(key)[kind]
        assert audit.eq(meta.loc[audit.index, "root_granularity"]).all()
    records, pairs, groups, cohorts = [], [], [], []
    sources = {metadata_path}
    for stage, relative, stage_col, stage_value, contrasts in SPECS:
        source = REPORTS / relative
        sources.add(source)
        d = pd.read_csv(source, low_memory=False).rename(columns={"case_id": "case"})
        d = d[d[stage_col].eq(stage_value)].copy()
        if "terminal_status" in d:
            d = d[d.terminal_status.isin(["complete", "model_failure"])]
        elif "status" in d:
            d = d[
                d.status.isin(
                    [
                        "completed",
                        "reused",
                        "model_failure",
                        "design_infeasible",
                        "done",
                    ]
                )
            ]
        needed = sorted({a for contrast in contrasts for a in contrast})
        # All registered stage arms define the complete cohort for RQ3.3–3.5.
        cohort_arms = (
            sorted(d.arm.unique())
            if stage.startswith(("RQ3.3", "RQ3.4", "RQ3.5"))
            else needed
        )
        for model, md in d.groupby("model"):
            assert not md.duplicated(["case", "arm"]).any(), (stage, model)
            pivot = md.pivot(index="case", columns="arm", values="mrr")
            complete = pivot[cohort_arms].dropna().index
            cohorts.append(
                {
                    "stage": stage,
                    "model": model,
                    "n": len(complete),
                    "arms": cohort_arms,
                    "excluded": sorted(set(pivot.index) - set(complete)),
                }
            )
            for arm, baseline in contrasts:
                z = pivot.loc[complete, [arm, baseline]].rename(
                    columns={arm: "new", baseline: "baseline"}
                )
                z = z.join(
                    meta[["dataset", "fault_type", "root_granularity", "leakage_group"]]
                )
                assert z.dataset.notna().all()
                assert (
                    z[["new", "baseline"]].ge(0).all().all()
                    and z[["new", "baseline"]].le(1).all().all()
                )
                z["delta"] = (z.new - z.baseline).round(12)
                identity = {
                    "stage": stage,
                    "model": model,
                    "arm": arm,
                    "baseline_arm": baseline,
                }
                pairs.extend(z.reset_index().assign(**identity).to_dict("records"))
                subsets = [
                    ("overall", "main3", z[z.dataset.isin(MAIN)]),
                    ("overall", "aiops_combined", z[z.dataset.isin(MAIN[:2])]),
                    ("overall", "all_available", z),
                ]
                subsets += [
                    ("dataset", key, part) for key, part in z.groupby("dataset")
                ]
                main = z[z.dataset.isin(MAIN)]
                for axis in ["root_granularity", "fault_type"]:
                    subsets += [(axis, key, part) for key, part in main.groupby(axis)]
                for axis, key, part in subsets:
                    if part.empty:
                        continue
                    records.append(
                        {**identity, "axis": axis, "subgroup": key, **summarize(part)}
                    )
                    # Equal event-group weights, sensitivity only; no CI.
                    g = part.groupby(["dataset", "leakage_group"])[
                        ["new", "baseline", "delta"]
                    ].mean()
                    groups.append(
                        {**identity, "axis": axis, "subgroup": key, **summarize(g)}
                    )
    for name, data in [("subgroup_tests", records), ("group_sensitivity", groups)]:
        result = pd.DataFrame(data)
        result["p_holm"] = np.nan
        for indices in (
            result[result.p_raw.notna()].groupby(["stage", "axis"]).groups.values()
        ):
            result.loc[indices, "p_holm"] = holm(result.loc[indices, "p_raw"])
        if name == "group_sensitivity":
            # A group's mean RR=1 is not a case-level AC@1 observation.
            result = result.drop(
                columns=[
                    "delta_ac1",
                    "delta_tail_rr",
                    "improved",
                    "worsened",
                    "repair",
                    "break_count",
                    "new_top5",
                    "lost_top5",
                ]
            )
        result.to_csv(OUT / f"{name}.csv", index=False)
    plot_review(pd.read_csv(OUT / "subgroup_tests.csv"))
    pd.DataFrame(pairs).to_csv(OUT / "paired_deltas.csv", index=False)
    (OUT / "cohorts.json").write_text(json.dumps(cohorts, indent=2), encoding="utf-8")
    provenance = {
        "kind": "posthoc_hypothesis_generation_not_confirmation",
        "calls": 0,
        "test": "two-sided asymptotic Pratt-Wilcoxon; Holm per stage x axis across models/contrasts",
        "n_min": 10,
        "root_and_fault_axes": "main three datasets only; evaluator-private",
        "group_note": "RQ3.2 frozen leakage_group metadata; sensitivity, not new independence assertion",
        "granularity": "gold root_ids mapped by registered 3/4/5-digit type, checked against RQ3.4/3.5 private-label audit",
        "sources": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(sources)
        },
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "provenance.json").write_text(
        json.dumps(provenance, indent=2), encoding="utf-8"
    )
    result = pd.DataFrame(records)
    print(
        f"Wrote {len(result)} subgroup rows and {len(pairs)} paired case contrasts to {OUT}"
    )


def plot_review(table):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    selected = [
        ("RQ3.3-check", "qwen3.8-27b", "W_G", "W_T", "3.3 Q: G - text"),
        ("RQ3.4-check", "qwen3.8-27b", "P1H1K1_G", "P1H1K1_T", "3.4 Q: G - text"),
        ("RQ3.4-check", "qwen3.8-27b", "P1H1K1_G", "P1H1K0_G", "3.4 Q: add K"),
        ("RQ3.3-check", "qwen3.8-27b", "W_G", "TPV", "3.3 Q: add W"),
        ("RQ3.5-A", "qwen3.8-27b", "E_S_D_P", "E_P_D_P", "3.5 Q: S - P evidence"),
        ("RQ3.5-A", "gemma-4-26b-a4b", "E_S_D_P", "E_P_D_P", "3.5 Gm: S - P evidence"),
        (
            "RQ3.5-A",
            "gemma-4-26b-a4b",
            "E_S_D_S",
            "E_S_D_P",
            "3.5 Gm: S - P instructions",
        ),
    ]
    columns = [("dataset", x) for x in MAIN] + [
        ("root_granularity", x) for x in ["node", "pod", "service"]
    ]
    values = np.empty((len(selected), len(columns)))
    labels = []
    for i, (stage, model, arm, baseline, label) in enumerate(selected):
        labels.append(label)
        part = table[
            (table.stage == stage)
            & (table.model == model)
            & (table.arm == arm)
            & (table.baseline_arm == baseline)
        ]
        for j, (axis, subgroup) in enumerate(columns):
            row = part[(part.axis == axis) & (part.subgroup == subgroup)].iloc[0]
            values[i, j] = row.delta
    fig, ax = plt.subplots(figsize=(12, 5.7))
    picture = ax.imshow(values, cmap="RdBu", vmin=-0.3, vmax=0.3)
    for i, (stage, model, arm, baseline, _) in enumerate(selected):
        for j, (axis, subgroup) in enumerate(columns):
            row = table[
                (table.stage == stage)
                & (table.model == model)
                & (table.arm == arm)
                & (table.baseline_arm == baseline)
                & (table.axis == axis)
                & (table.subgroup == subgroup)
            ].iloc[0]
            star = "*" if row.p_holm < 0.05 else ""
            ax.text(
                j,
                i,
                f"{row.delta:+.3f}{star}\nn={int(row.n)}",
                ha="center",
                va="center",
                fontsize=9,
                color="white" if abs(row.delta) > 0.19 else "black",
            )
    ax.set_xticks(
        range(len(columns)),
        ["AIOPS-22", "AIOPS-25", "AegisLab", "node", "pod", "service"],
    )
    ax.set_yticks(range(len(labels)), labels)
    ax.set_title(
        "Exploratory gain/harm map: paired MRR changes, not independent replications"
    )
    fig.colorbar(picture, ax=ax, label="Delta MRR")
    fig.text(
        0.02,
        0.015,
        "* Holm p<.05 within report-stage x subgroup axis; n<10: descriptive only.\nQ=Qwen; Gm=Gemma. Different rows retain their own frozen cohorts; do not pool them.",
        fontsize=9,
    )
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(OUT / "gain_harm_map.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()

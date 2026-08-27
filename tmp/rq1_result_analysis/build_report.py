#!/usr/bin/env python3
"""Build the human-readable RQ1 report from analyze_rq1.py outputs."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/home/lglsj/CanvasRCA_nibi")
ANA = ROOT / "tmp/rq1_result_analysis"
REPORT = ROOT / "docs/RQ1_report.md"
HEADLINE = {"aegislab", "aiops2022", "aiops2025"}
QA = {"legacy_q9", "cross_region", "typed_two_stage"}
RCA = {"direct_rca", "matched_rca", "visual_counterfactual_rca", "ledger_handoff_rca"}
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
COST_ARM_ORDER = {
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
    "visual_counterfactual_rca": ["H_factual", "H_targeted", "H_placebo", "H_neutral"],
    "ledger_handoff_rca": ["L_txt", "L_vis", "L_hyb"],
}


def load(name):
    return pd.read_csv(ANA / name)


def tidy(df, digits=4):
    x = df.copy()
    for c in x.select_dtypes(include="number"):
        if c.endswith("_n") or c in {"n", "case_n", "expected_n", "improve", "degrade", "tie", "repair", "break", "both_correct", "both_incorrect", "net_correction"}:
            x[c] = x[c].map(lambda v: "" if pd.isna(v) else f"{int(v):,}")
        else:
            x[c] = x[c].map(lambda v: "" if pd.isna(v) else f"{v:.{digits}f}")
    return x


def md(df, digits=4):
    return tidy(df, digits).to_markdown(index=False)


def weighted_runtime(runtime):
    x = runtime[runtime.dataset_scope == "all_469"].copy()
    count_cols = [c for c in x if c.endswith("_n") and c != "expected_n"]
    out = x.groupby(["experiment", "model"])[["expected_n", *count_cols]].sum().reset_index()
    out["infra_rate"] = (out.missing_record_n + out.vllm_response_failure_n + out.input_context_overflow_n + out.timeout_n + out.infrastructure_other_n) / out.expected_n
    out["trunc_rate"] = out.output_truncation_n / out.expected_n
    out["parse_rate"] = out.parse_failure_n / out.expected_n
    return out


def compact_arm_cost(cost):
    cols = ["experiment", "model", "arm", "n", "mean_text_tokens", "mean_image_tokens", "mean_input_tokens", "mean_output_tokens", "mean_total_tokens", "mean_model_calls"]
    return cost[cost.dataset_scope == "all_469"][cols].sort_values(["experiment", "model", "arm"])


def arm_input_cost(cost):
    """Return an arm-first table; models are columns, never aggregation targets."""
    x = cost[cost.dataset_scope == "all_469"].copy()
    rows = []
    for experiment in COST_REFERENCES:
        subset = x[x.experiment == experiment]
        if subset.empty:
            continue
        refs = (subset[subset.arm == COST_REFERENCES[experiment]]
                .set_index("model").mean_input_tokens.to_dict())
        for arm in COST_ARM_ORDER[experiment]:
            if arm not in set(subset.arm):
                continue
            row = {"experiment": experiment, "arm": arm, "reference": COST_REFERENCES[experiment]}
            arm_rows = subset[subset.arm == arm].set_index("model")
            for model in DISPLAY_MODELS:
                label = MODEL_LABELS[model]
                if model not in arm_rows.index or model not in refs:
                    row[f"{label} input"] = np.nan
                    row[f"{label} %ref"] = np.nan
                    continue
                value = float(arm_rows.loc[model, "mean_input_tokens"])
                row[f"{label} input"] = value
                row[f"{label} %ref"] = 100.0 * value / refs[model]
            rows.append(row)
    return pd.DataFrame(rows)


def rca_dataset_table(perf):
    x = perf[perf.experiment.isin(RCA) & perf.dataset_scope.isin(["aegislab", "aiops2022", "aiops2025", "re2_ob", "re2_tt", "headline_289"])].copy()
    p = x.pivot_table(index=["experiment", "model", "arm"], columns="dataset_scope", values="mrr", aggfunc="first").reset_index()
    order = ["experiment", "model", "arm", "aegislab", "aiops2022", "aiops2025", "headline_289", "re2_ob", "re2_tt"]
    return p[[c for c in order if c in p]].sort_values(["experiment", "model", "arm"])


def full_dashboard_attention(records):
    full = (
        (records.experiment.isin(["legacy_q9", "direct_rca", "matched_rca"]) & records.arm.isin(["V", "H"])) |
        (records.experiment.isin(["cross_region", "typed_two_stage"]) & records.arm.isin(["V", "H"])) |
        records.experiment.eq("visual_counterfactual_rca")
    )
    cols = ["attn_M", "attn_R", "attn_L", "attn_G", "focus_M", "focus_R", "focus_L", "focus_G",
            "normalized_attention_entropy", "blank_attention_mass", "top_10pct_evidence_precision"]
    x = records[full & records.attn_M.notna()]
    return x.groupby("model")[cols].mean().reset_index().rename(columns={
        "attn_M": "M_mass", "attn_R": "R_mass", "attn_L": "L_mass", "attn_G": "G_mass",
        "focus_M": "M_focus", "focus_R": "R_focus", "focus_L": "L_focus", "focus_G": "G_focus",
        "normalized_attention_entropy": "entropy", "blank_attention_mass": "blank_mass",
        "top_10pct_evidence_precision": "top10_evidence_precision"})


def routed_attention(records):
    x = records[records.experiment.isin(["direct_rca", "matched_rca"]) & records.arm.eq("R") & records.attn_M.notna()]
    return x.groupby("model")[["attn_M", "attn_G", "blank_attention_mass", "top_10pct_evidence_precision"]].mean().reset_index().rename(columns={
        "attn_M": "M_mass", "attn_G": "G_mass", "blank_attention_mass": "blank_mass",
        "top_10pct_evidence_precision": "top10_evidence_precision"})


def headline_qa(perf):
    cols = ["experiment", "model", "arm", "n", "complete_chain_accuracy", "level_1_complete_chain_accuracy",
            "level_2_complete_chain_accuracy", "level_3_complete_chain_accuracy", "step_accuracy", "query_membership_valid"]
    return perf[(perf.dataset_scope == "headline_289") & perf.experiment.isin(QA)][cols].sort_values(["experiment", "model", "arm"])


def headline_rca(perf):
    cols = ["experiment", "model", "arm", "n", "ac@1", "ac@3", "ac@5", "avg@3", "avg@5", "mrr"]
    return perf[(perf.dataset_scope == "headline_289") & perf.experiment.isin(RCA)][cols].sort_values(["experiment", "model", "arm"])


def key_comparisons(comp):
    wanted = (
        comp.comparison.isin(["R - T", "R - F", "H - T", "V - T", "P - T", "L_vis - L_txt", "L_hyb - L_txt",
                              "H_targeted - H_factual", "H_placebo - H_factual", "H_neutral - H_factual",
                              "P1: H-T on Level2+3", "P2: (H-T)L3 - (H-T)L1"]) |
        comp.comparison.str.contains("visual_main_effect", na=False)
    )
    cols = ["experiment", "model", "comparison", "metric", "n", "delta", "p", "p_holm", "cohen_dz", "improve", "degrade", "tie"]
    return comp[wanted][cols].sort_values(["experiment", "model", "comparison"])


def root_fault_summary(records):
    x = records[(records.experiment == "matched_rca") & (records.model == "qwen3.8-27b") & (records.arm == "R") & records.dataset.isin(HEADLINE) & (records.status == "completed")]
    fault = x.groupby("fault_type").agg(n=("case", "size"), correct_n=("ac@1", "sum"), ac1=("ac@1", "mean"), mrr=("mrr", "mean")).reset_index()
    fault["wrong_n"] = fault.n - fault.correct_n
    fault = fault[fault.n >= 5].sort_values(["mrr", "n"], ascending=[False, False])
    service = x.groupby("root_service").agg(n=("case", "size"), correct_n=("ac@1", "sum"), ac1=("ac@1", "mean"), mrr=("mrr", "mean")).reset_index()
    service["wrong_n"] = service.n - service.correct_n
    service = service[service.n >= 5].sort_values(["mrr", "n"], ascending=[False, False])
    return fault, service


def main():
    perf = load("performance_paired_complete.csv")
    cost = load("cost.csv")
    runtime = load("runtime.csv")
    eligibility = load("eligibility.csv")
    comparisons = load("comparisons.csv")
    transitions = load("arm_transitions.csv")
    modifiers = load("effect_modifiers.csv")
    binding = load("stage1_binding.csv")
    inventory = load("attention_inventory.csv")
    attn_correct = load("attention_correctness.csv")
    records = pd.read_parquet(ANA / "records.parquet")

    runtime_summary = weighted_runtime(runtime)
    cost_arm_table = arm_input_cost(cost)
    attn_inventory = inventory.groupby("model").agg(
        visual_requests=("visual_request_n", "sum"), collected=("collected_n", "sum"),
        grids=("grid_refs", "sum"), grids_present=("grid_exists", "sum"),
        overlays=("overlay_refs", "sum"), overlays_present=("overlay_exists", "sum"),
        raw_probe_present=("raw_probe_exists", "sum")).reset_index()
    attn_inventory["raw_probe_missing"] = attn_inventory.visual_requests - attn_inventory.raw_probe_present
    bind = binding.groupby(["experiment", "model"]).agg(supported=("supported", "sum"), unsupported=("unsupported", "sum")).reset_index()
    bind["binding_rate"] = bind.supported / (bind.supported + bind.unsupported)
    fault, service = root_fault_summary(records)
    mod = modifiers[(modifiers.experiment == "matched_rca") & (modifiers.comparison == "R - T") & (modifiers.dimension == "dataset")]
    trans = transitions[(transitions.experiment == "matched_rca") & (transitions.comparison == "R - T")]

    text = f"""# RQ1 formal result report

Generated: 2026-08-26  
Scope: all locally available formal RQ1 result sets for Qwen3.6-27B, Gemma-4-26B-A4B-it, and Qwen3.8-27B. Preliminary smoke tests, qualification gates, pilots, and results from the superseded inference-v1 runtime are excluded.

## Reader's guide (no project background assumed)

CanvasRCA studies whether a vision-language model (VLM) can diagnose a microservice incident more accurately when the same telemetry is presented as a real dashboard instead of, or in addition to, text. A **case** is one incident. Its telemetry contains metrics (numeric time series), traces (request-flow and latency records), logs (event messages), and a directed service-call topology. **Root-cause analysis (RCA)** asks the model to rank up to five candidate entities from most to least likely to have originated the incident.

The report covers two different endpoints:

- **Question answering (QA)** asks narrowly scoreable questions about visible telemetry, such as reading one displayed value or linking a metric observation to a topology neighbor. It measures perception and cross-region reasoning; it is not an RCA score.
- **RCA** asks for the ranked root-cause list. Its main score is mean reciprocal rank (MRR), explained in Section 3.6.

An **experimental arm** is one controlled way of presenting an otherwise matched case to the model. For example, `T` presents incident evidence as natural-language text, while `V` presents it as a real rendered dashboard. One **case-arm record** is the saved outcome for one incident under one such condition. The compact arm codes are fully expanded in Section 3.2; they are labels for input representations, not model names or performance metrics.

All ordinary representation comparisons preserve the same model-visible atomic incident facts: the same candidates, displayed values and precision, time bins, missing-value markers, concrete caller-to-callee edges, and legends. What changes is how those facts are represented. `H` intentionally repeats the same facts in both image and text, while the counterfactual experiment intentionally manipulates only the image to test causality. **Label-blind** construction means the code selecting, rendering, or manipulating evidence cannot read the evaluator's ground-truth root cause. **Frozen** or **preregistered** means a roster, rule, or threshold was fixed before inspecting the corresponding result. A positive difference written as `A-B` means arm A scored higher than arm B.

The **headline set** contains 289 cases from AegisLab, AIOPS-2022, and AIOPS-2025. RE2-OB is reported separately because text baselines nearly saturate it, and RE2-TT is a separate out-of-distribution (OOD) slice, meaning its conditions differ from the primary evaluation distribution. Results described as *Qwen3.8-specific* were reproduced for that model but not for both Qwen and Gemma architectures.

## 1. Executive summary

This audit consolidates **85,827 formal case-arm records** over 469 frozen evaluation cases (96 AegisLab, 100 AIOPS-2022, 93 AIOPS-2025, 90 RE2-OB, 90 RE2-TT). The inferential headline set is the 289 non-saturated AegisLab/AIOPS cases; RE2-OB is a saturated pipeline reference and RE2-TT is OOD.

The strongest positive RCA result is narrow but real: in two-stage `matched_rca`, Qwen3.8's routed visual-text arm `R` (metric charts and topology as images; logs and traces as text) reaches headline MRR **0.3807**, versus **0.3192** for natural-language text `T` and **0.3182** for flat structured JSONL `F`. The paired gains are `R-T=+0.0615` (Holm `p=0.0056`, `dz=0.173`) and `R-F=+0.0625` (Holm `p=0.0056`, `dz=0.162`). It clears the registered `+0.05` effect threshold, and no headline dataset has an effect at or below `-0.05`. This is therefore a **Qwen3.8-specific routed visual-text result**, not a cross-architecture result: Gemma has `R-T=-0.0307`, while Qwen3.6 has `+0.0113` on an incomplete 414-case run.

The broader evidence is mixed. The real-dashboard-only arm `V` and redundant image-plus-identical-text hybrid `H` usually do not beat text on RCA; pixel-text `P` (the text evidence rendered into an image without charts) is generally weakest. Cross-region QA does contain a second, task-specific positive result: one-stage Gemma passes both registered depth hypotheses on jointly scoreable Level-2/3 cases (`H-T=+0.1087`) and the Level-3-versus-Level-1 interaction (`+0.1667`), both statistically significant after Holm correction for multiple comparisons. Its factorial visual main effects nevertheless stay below the registered +0.10 region threshold, and the pattern does not transfer to the Qwen models. The causal counterfactual RCA experiment changes rankings but does not produce a statistically reliable causal visual benefit.

Attention is genuinely present and nearly complete: all **73,936 visual requests** have diagnostics collected during the same prompt-processing forward pass (“same-prefill”), and all **188,806 grids and overlays** exist. Qwen3.6 lacks 48 raw token-vector files in the counterfactual result set, but their grids, overlays, and embedded regional diagnostics remain. On full dashboards, the final prompt query puts most mass on metrics, then topology, with very little on traces/logs. Attention distributions for correct and incorrect RCA outputs are nearly identical, so attention alone does not explain success.

## 2. Status and validity

The 5% rule applies only to missing/infrastructure cases: if more than 5% of whole cases lack a complete matched set of arms because the serving or execution infrastructure failed, that model-experiment combination is formally incomplete. Parse failures (the model did not produce the required JSON) and output truncations (generation hit its output-token ceiling) remain model outcomes and are not silently excluded. In the table, `case_n` is the number of registered cases, `excluded_cases` counts distinct cases with an infrastructure problem in at least one required arm, `passes_5pct` reports the infrastructure gate, and `all_ineligible_cases` counts cases that were label-blindly ineligible for every arm of an intervention rather than lost to runtime failure.

{md(eligibility[["experiment", "model", "case_n", "excluded_cases", "exclusion_rate", "passes_5pct", "all_ineligible_cases"]])}

`matched_rca / qwen3.6-27b` is the only combination over the infrastructure ceiling: 55 distinct cases (11.73%) have input-context overflow. Its registered claim is incomplete; its numbers are descriptive and comparisons use the 414 whole-case complete subset (234 headline cases). Counterfactual `protocol_ineligible` records are label-blind eligibility outcomes, not runtime failures.

## 3. Experiments and arm semantics

### 3.1 What each experiment asks

| Experiment | Pipeline | Representation conditions | Plain-language purpose and scored endpoint |
|---|---|---|---|
| `legacy_q9` | one model call | `T/P/V/H` | Nine direct-reading QA operations. Tests whether the model can read facts that are explicitly visible; exact answer accuracy is not RCA accuracy. |
| `cross_region` | one model call | 16 M/R/L/G text-versus-visual combinations, plus `P/V/H` | QA at reasoning Levels 1–3. Tests whether the model can read one region and connect facts across two or three telemetry regions. |
| `typed_two_stage` | Stage 1 selector, then Stage 2 answerer | the same 19 conditions as `cross_region` | Repeats the cross-region QA through an intermediate typed evidence ledger to measure evidence-selection and handoff loss. It still does not diagnose root causes. |
| `direct_rca` | one model call | `T/F/V/P/H/R` | The model reads the original representation and directly returns a ranked top-five root-cause list. |
| `matched_rca` | Stage 1 selector, then Stage 2 diagnosis | `T/F/V/P/H/R` | End-to-end RCA through a compact grounded evidence ledger; the final endpoint is the ranked top-five root-cause list. |
| `visual_counterfactual_rca` | Stage 1, then Stage 2 | `H_factual/H_targeted/H_placebo/H_neutral` | Holds hybrid text fixed while manipulating the image, testing whether image semantics causally move the evidence ledger and RCA ranking. |
| `ledger_handoff_rca` | one shared Stage 1, then three Stage 2 handoffs | `L_txt/L_vis/L_hyb` | Gives Stage 2 the same normalized ledger in text, pixels, or both, isolating whether ledger representation changes RCA after evidence selection. |

A **one-stage** pipeline directly produces the QA answer or RCA ranking from the original evidence. A **two-stage** pipeline first asks the model to select observations (Stage 1), then a deterministic label-blind binder copies the exact public facts into a normalized **evidence ledger**. Stage 2 receives only that ledger, the same candidate list, and the common task instructions; it cannot reopen the original dashboard or text. Thus a two-stage failure can arise from evidence selection, binding, handoff compression, or final reasoning. “Calls per case-arm” counts model requests, not CPU preprocessing; ordinary two-stage arms use two requests.

### 3.2 Main representation-arm dictionary

| Code | Full name | What the model sees | What the comparison is intended to isolate |
|---|---|---|---|
| `T` | natural-language **text-only** | The complete incident evidence serialized as deterministic prose in metrics → traces → logs → topology order. No incident dashboard image is supplied. | The primary non-visual baseline. |
| `F` | **flat structured text** | The same atomic facts as stable, ordered JSON Lines (JSONL) records: one machine-readable fact object per line. There is no narrative and no visual/spatial layout. | Whether structure alone, without prose or dashboard layout, explains an effect. |
| `V` | real **visual dashboard only** | The renderer-v12 telemetry dashboard with metric curves, trace/log tables, propagation plot, and the concrete directed edge key. It receives the common task shell and candidates but no incident-evidence prose. | The effect of genuine dashboard encoding. |
| `P` | **pixel-text pseudo-dashboard** | The exact `T` incident-fact lines rendered into image pages, with only headings and lossless wrapping added. It contains no metric curves or graph layout. | A control for moving text through the visual/optical-character-recognition (OCR) channel; `P` must not be called a real dashboard. |
| `H` | redundant **hybrid image + text** | Image first, then strict `A+B`: `A` is byte/hash-identical to the `V` image and `B` is byte-identical to `T`. The same facts are intentionally encoded twice. | Incremental value of adding the real dashboard when the complete text is already present. |
| `R` | **routed visual-text** | Metrics and directed topology are visual; logs and traces are text. Each incident fact appears exactly once rather than being duplicated. | Whether assigning each evidence type to a selected representation is better than all-text or flat structured input. |

The raw QA protocol calls the four global arms `T_QA`, `P_QA`, `V_QA`, and `H_QA`; the tables shorten them to `T`, `P`, `V`, and `H`. Every arm also receives the same candidate order, task definition, field legends, answer schema, and decoding contract.

### 3.3 M/R/L/G region notation and the 16 factorial cells

The cross-region experiments divide telemetry into four evidence regions:

- `M` = **metrics**: numeric time-series panels and their displayed summaries;
- `R` = **traces**: request/span counts, errors, latency, and operation-flow evidence;
- `L` = **logs**: event/error counts and normalized log-template evidence;
- `G` = **directed topology graph**: concrete caller → callee edges and neighbor relationships.

The four-letter region order is always `M-R-L-G`. A lowercase suffix `t` means that region is supplied as text; `v` means it is supplied as a crop from the real dashboard. Therefore `Mt-Rt-Lt-Gt` means all four regions are textual, `Mv-Rt-Lt-Gt` means only metrics are visual, and `Mv-Rv-Lv-Gv` means all four controlled regions are visual. These 16 combinations form a 2×2×2×2 factorial design, allowing one region's average visual effect to be estimated across the eight matched settings of the other three regions.

Two symbols that both use the letter `R` must not be confused: a standalone RCA arm named `R` means **routed visual-text**, while `R` inside `Mt-Rv-Lt-Gt` means the **trace region**. The all-visual factorial crop cell `Mv-Rv-Lv-Gv` is also not the same as global arm `V`: the former is a controlled four-crop canvas, whereas `V` preserves the complete real-dashboard layout.

### 3.4 Counterfactual image conditions

All four counterfactual conditions start from hybrid `H`, keep its text, candidates, prompt, layout, and request budget fixed, and change only the image:

| Code | Meaning | Why it exists |
|---|---|---|
| `H_factual` | the correctly matched real dashboard | Reference condition. |
| `H_targeted` | a label-blind swap of the complete visual identities of a high-evidence and a low-evidence candidate | Tests whether a semantically directed image change moves the ledger/ranking in the predicted direction. It never uses the ground-truth root label to choose the swap. |
| `H_placebo` | a matched swap between similarly weak candidates | Controls for generic disruption caused by swapping equally sized/structured visual content. |
| `H_neutral` | a neutral sham canvas with incident visual evidence removed while geometry and visual budget are preserved | Tests how much of the result remains when the image carries no incident evidence. |

Changing a ranking under these conditions demonstrates visual sensitivity. It demonstrates useful causal visual evidence only if the targeted change exceeds the placebo/sham behavior in the registered direction; it does not by itself show higher factual RCA accuracy.

### 3.5 Ledger-handoff conditions

Here `L_` means **ledger**, not the log region:

- `L_txt`: the normalized Stage-1 evidence ledger supplied to Stage 2 as typed text;
- `L_vis`: the same ledger rendered losslessly as pixels;
- `L_hyb`: the ledger image first, followed by byte-identical ledger text.

Stage 1 is physically shared across these three conditions, so any Stage-2 difference concerns transport/representation of the same selected evidence, not different original observations.

### 3.6 Metrics and statistical notation

**QA metrics.** At the question level, `complete_chain_accuracy` is 1 only when the complete answer chain is exactly correct. The reported case value is the mean across that case's eligible questions, and the table averages those case values, so it may lie between 0 and 1. Level 1 reads one region directly; Level 2 uses an answer from one region to query a second; Level 3 makes a dependent chain across three distinct regions. `step_accuracy` scores individual steps, while `correct-prefix accuracy` asks how far the chain remains correct before its first error. `query_membership_valid` checks that returned answer slots correspond to the supplied questions; the short query IDs are bookkeeping labels, not evidence the model must infer.

**RCA metrics.** At the case level, `AC@K` (accuracy at K) is 1 when any accepted root-cause label appears within the first K ranked predictions and 0 otherwise; the table reports its mean, i.e. the fraction of cases solved within K. `AVG@K` is the mean of cumulative `AC@1` through `AC@K`; for example, a root ranked second has `AVG@3=(0+1+1)/3`. `MRR` (mean reciprocal rank) averages `1/rank` of the first accepted prediction, with 0 for a top-five miss. Thus rank 1 contributes 1.0, rank 2 contributes 0.5, and rank 5 contributes 0.2. These metrics use the granularity-aware scorer: service-level aliases are handled as registered, while pod/node labels retain their stricter matching rules.

**Paired comparisons.** `A-B` is computed case by case, so a positive delta favors A. `n` is the number of paired scoreable cases. `p` is the paired Wilcoxon signed-rank p-value; `p_holm` is the value after Holm correction for the registered family of multiple comparisons. Paired Cohen's `dz` is a standardized effect size. `improve`, `degrade`, and `tie` count cases where A scores above, below, or equal to B. For top-1 transitions, a `repair` is wrong in the baseline but correct in the comparison arm, a `break` is the reverse, and `net_correction=repair-break`.

The preregistered cross-region labels `P1`, `P2`, and `P3` are **hypotheses**, not representation arms: P1 tests the hybrid-minus-text gain on jointly scoreable Level-2/3 cases; P2 tests whether that gain is larger at Level 3 than Level 1; P3 tests visual main effects of individual M/R/L/G regions.

## 4. Performance

All full per-dataset/per-arm metrics are in [performance.csv](../tmp/rq1_result_analysis/performance.csv); the whole-case paired version used below is [performance_paired_complete.csv](../tmp/rq1_result_analysis/performance_paired_complete.csv). “Whole-case paired” means a case enters an arm comparison only when every required arm has a terminal record. `accuracy` in QA means exact complete-chain question accuracy, not RCA `AC@1`. The `headline_289` rows pool only the three primary datasets defined in the reader's guide.

### 4.1 RCA headline results

{md(headline_rca(perf))}

![RCA MRR](RQ1_report_assets/rca_headline_mrr.png)

### 4.2 RCA dataset heterogeneity

Cells are MRR. AC@1/3/5 and AVG@3/5 for every dataset remain in the complete CSV above.

<details><summary>Show all RCA experiment × model × arm dataset MRR</summary>

{md(rca_dataset_table(perf))}

</details>

The routed-arm-minus-text (`R-T`) Qwen3.8 gain is concentrated in AegisLab (`+0.1181`), but remains positive on AIOPS-2022 (`+0.0383`) and AIOPS-2025 (`+0.0280`). Gemma reverses on AegisLab (`-0.0642`). In the following modifier table, `value` is the dataset name, `delta` is paired `R-T` MRR, and `repair_n`/`break_n` count top-1 corrections/regressions.

{md(mod[["model", "value", "n", "delta", "p", "cohen_dz", "repair_n", "break_n"]])}

### 4.3 QA headline results

<details><summary>Show all Legacy-Q9, cross-region and typed-two-stage arms</summary>

{md(headline_qa(perf))}

</details>

![QA by reasoning level](RQ1_report_assets/qa_accuracy_by_level.png)

Legacy natural-language text `T` is already very strong (headline exact accuracy: Gemma 0.9343, Qwen3.6 0.9246, Qwen3.8 0.8970). Hybrid image-plus-text `H` is approximately tied only for the two Qwen models and is lower for Gemma; real-dashboard-only `V` and pixel-text `P` are lower for all three. In one-stage cross-region QA, `H` improves the per-case question-packet average by +0.0421 for Gemma and +0.0375 for Qwen3.6 but hurts Qwen3.8 by -0.1038. The preregistered depth test is different from that packet average: on cases where both Level 2 and Level 3 are jointly scoreable, Gemma has hypothesis P1 `+0.1087` (`n=138`, Holm `p<0.0001`) and hypothesis P2 `+0.1667` (Holm `p=0.00026`), so Gemma alone supports those two depth hypotheses. Qwen3.6 and Qwen3.8 do not pass both. Typed handoff improves the packet average for selected Qwen visual conditions, but no model reaches both +0.10 depth thresholds.

## 5. Paired arm and experiment comparisons

Tests use paired Wilcoxon signed-rank with Pratt zeros and paired Cohen's `dz`; Section 3.6 explains these columns. No confidence intervals are reported. Holm families follow the registered primary/secondary groupings, preventing a large menu of arm comparisons from being treated as independent chances to find significance.

<details><summary>Show registered and mechanism comparisons</summary>

{md(key_comparisons(comparisons), 5)}

</details>

![Paired deltas](RQ1_report_assets/paired_deltas.png)

For matched RCA `R-T`, top-1 repairs exceed breaks only for Qwen3.8 (33 vs 19; net +14) and Qwen3.6 (24 vs 19; net +5, incomplete run). Gemma breaks 35 cases while repairing 25.

{md(trans[["model", "n", "both_correct", "repair", "break", "both_incorrect", "net_correction"]])}

The full machine-readable paired table is [comparisons.csv](../tmp/rq1_result_analysis/comparisons.csv); fault/service/dataset effect modifiers are in [effect_modifiers.csv](../tmp/rq1_result_analysis/effect_modifiers.csv), and repair/break transitions in [arm_transitions.csv](../tmp/rq1_result_analysis/arm_transitions.csv).

## 6. Cost

The scientific cost comparison is **between arms within the same model**, not between models. Gemma and Qwen use different tokenizers and visual processors, so a raw Gemma-versus-Qwen token difference is not evidence that one representation is cheaper. The figures below therefore put arms on rows and models in separate columns. Each cell shows mean input tokens and, underneath, that arm's percentage of the experiment's all-text reference. Values below 100% save input tokens; values above 100% use more. Color is also keyed to this within-model percentage.

The reference is `T` for Legacy-Q9/direct/matched RCA, all-text `Mt-Rt-Lt-Gt` for cross-region and typed-two-stage QA, factual hybrid `H_factual` for counterfactual RCA, and text ledger `L_txt` for ledger handoff. Counterfactual arms are expected to be cost-matched rather than cheaper because they change image semantics while holding the input budget fixed.

### 6.1 Input-token cost by experimental arm

![Legacy-Q9 arm cost](RQ1_report_assets/cost_by_arm_legacy_q9.png)

![Cross-region arm cost](RQ1_report_assets/cost_by_arm_cross_region.png)

![Typed two-stage arm cost](RQ1_report_assets/cost_by_arm_typed_two_stage.png)

![Direct RCA arm cost](RQ1_report_assets/cost_by_arm_direct_rca.png)

![Matched RCA arm cost](RQ1_report_assets/cost_by_arm_matched_rca.png)

![Counterfactual RCA arm cost](RQ1_report_assets/cost_by_arm_visual_counterfactual_rca.png)

![Ledger-handoff arm cost](RQ1_report_assets/cost_by_arm_ledger_handoff_rca.png)

The main arm-level patterns are stable within each model. Real-dashboard `V` uses only 8–16% of the all-text input in Legacy-Q9/cross-region QA, 21–31% in direct RCA, and 35–42% in matched RCA. Routed `R` uses 30–40% of text input in direct RCA and 43–49% in matched RCA. Hybrid `H` costs 3–17% more input than the corresponding text baseline because it adds the image without removing text. Pixel-text `P` is tokenizer/processor dependent: it is cheaper for Gemma, but costs about 114% of text in Qwen QA, 182% in Qwen direct RCA, and 166–169% in Qwen matched RCA. The visual and hybrid ledger handoffs do not save tokens over `L_txt`.

The most important accuracy–cost joint result is Qwen3.8 matched RCA `R`: it raises MRR over `T` by +0.0615 while using **47.5%** of `T`'s mean input tokens. This is a within-model Pareto improvement for that experiment. It does not imply that all visual arms, or other model architectures, have the same benefit.

<details><summary>Show arm-centred mean input tokens and percent of reference (models are columns)</summary>

{md(cost_arm_table, 1)}

</details>

`mean_text_tokens` and `mean_image_tokens` are the two input components, `mean_input_tokens` is their recorded request-level input total, `mean_output_tokens` is generated text, and `mean_total_tokens` is input plus output. `mean_model_calls` distinguishes one-stage from two-stage pipelines. The following detailed table retains all components and uses one row per experiment/model/arm, but it is secondary to the arm-first comparison above.

<details><summary>Show every arm's full all-469 token components</summary>

{md(compact_arm_cost(cost))}

</details>

For ledger handoff, the table's pipeline cost assigns the shared Stage 1 to each arm for an end-to-end arm comparison. The physical experiment called Stage 1 once and reused it across three handoffs; [cost.csv](../tmp/rq1_result_analysis/cost.csv) also records incremental and one-third-amortized totals. Wall time is intentionally not compared because some calls ran on H100 and others on RTX Pro 6000. No cost number includes wall time.

## 7. Runtime and output integrity

The runtime columns separate causes rather than merging them into one “error rate.” `expected_n` is the number of registered case-arm records expected for that experiment/model. `missing_record_n` means no terminal artifact exists; `vllm_response_failure_n` means the inference server failed to return a usable response; `input_context_overflow_n` means prompt plus reserved output exceeded the model context; `timeout_n` means the request exceeded its allowed time; `output_truncation_n` means generation reached its output ceiling; `parse_failure_n` means the returned text did not satisfy the required JSON schema; `infrastructure_other_n` covers other execution failures; and `protocol_ineligible_n` is a preregistered, label-blind inability to construct a valid intervention rather than a runtime error. `infra_rate` includes only infrastructure exclusions. Despite its compact historical name, `parse_rate` is the **parse-failure fraction**, not the parse-success fraction; `trunc_rate` is likewise the output-truncation fraction.

{md(runtime_summary[["experiment", "model", "expected_n", "missing_record_n", "vllm_response_failure_n", "input_context_overflow_n", "timeout_n", "output_truncation_n", "parse_failure_n", "infrastructure_other_n", "protocol_ineligible_n", "infra_rate", "trunc_rate", "parse_rate"]])}

![Runtime errors](RQ1_report_assets/runtime_errors.png)

There are no missing records, vLLM response failures, timeouts, or uncategorized infrastructure failures in the consolidated lineages. The only infrastructure class is 55 Qwen3.6 matched-RCA context overflows (`prompt + 8192 > 32768`). The largest model-output issue is Gemma typed-two-stage (15 truncations, 19 parse failures; some overlap), still far below 5% and scored as model behavior. Qwen3.8 direct RCA has 14 parse failures, four of which are truncated. Detailed per-arm/per-dataset rates are in [runtime.csv](../tmp/rq1_result_analysis/runtime.csv).

## 8. Detailed case statistics

### 8.1 Typed Stage-1 binding

{md(bind)}

The **binding rate** is the fraction of Stage-1 selectors that a deterministic program can match to an exact public evidence record. It is high for RCA (96.4–99.3%) but materially lower for typed QA: Gemma 72.96%, Qwen3.6 85.60%, Qwen3.8 86.79%. This helps explain why typed QA can underperform direct QA even when its Stage 2 is well-formed. A failed individual binding is recorded as `unsupported` rather than invalidating an entire ledger; `supported` and `unsupported` in the table are selector counts, not case counts.

### 8.2 Fault types and canonical root labels

For the strongest formal cell (`matched_rca`, Qwen3.8, `R`, headline), the following tables show groups with at least five cases. `root_service` is the first registered service-level accepted label when available, otherwise the first accepted label. Accepted aliases are not treated as independent multi-root causes.

<details><summary>Fault-type outcomes</summary>

{md(fault)}

</details>

<details><summary>Canonical-root outcomes</summary>

{md(service)}

</details>

Complete outcome tables are [statistics_fault_type.csv](../tmp/rq1_result_analysis/statistics_fault_type.csv), [statistics_service.csv](../tmp/rq1_result_analysis/statistics_service.csv), [statistics_error_reason.csv](../tmp/rq1_result_analysis/statistics_error_reason.csv), and [statistics_prediction_service.csv](../tmp/rq1_result_analysis/statistics_prediction_service.csv). The error taxonomy distinguishes top-1 correct, rank 2–3, rank 4–5, top-5 miss, parse failure, and truncation. A universal semantic “reasoning error” label cannot be inferred from root/injection labels alone and is therefore not invented.

## 9. Attention analysis

### 9.1 What was actually captured

{md(attn_inventory)}

The probe is from the same generation **prefill** (the forward pass that processes the prompt before output tokens are generated), not a second model call. It averages per-head softmax attention from the final prompt query to visual-token keys at the registered layer, then maps tokens to 16×16 image grids. `visual_requests` counts requests containing an image; `collected` counts embedded attention summaries; `grids_present` and `overlays_present` count stored heatmap artifacts; `raw_probe_present` counts retained token-level vectors. All grids and overlays exist. Qwen3.6's 48 missing raw probes are confined to 12 cases × four counterfactual conditions; their derived grids, overlays, and regional diagnostics are still present. Token-level re-analysis is unavailable for those 48 only.

### 9.2 Full-dashboard distribution

`mass` is the probability mass across the four dashboard regions and sums to one: for example, `M_mass` is attention assigned to metric panels. `focus` divides mass by the region's share of image area, so 1 means proportional-to-area, values above 1 are over-focus, and values below 1 are under-focus. `entropy` measures how diffuse the attention map is, `blank_mass` is attention on blank canvas, and `top10_evidence_precision` is the fraction of the most-attended 10% of patches that overlap an evidence-bearing region.

{md(full_dashboard_attention(records))}

![Attention region mass](RQ1_report_assets/attention_region_mass.png)

Across models, metrics receive 62.4–66.8% of full-dashboard attention and topology 27.7–30.8%; logs and traces each receive only about 2–4%. Area-normalized focus changes the interpretation: topology is consistently over-focused (1.09–1.21), metrics roughly area-proportional, while logs/traces are under-focused. Qwen3.8 is the most metric-heavy and gives the least mass to logs/traces.

Routed `R` exposes only metrics and topology visually:

{md(routed_attention(records))}

### 9.3 Attention, correctness, fault type, and service

![Attention diagnostics](RQ1_report_assets/attention_diagnostics_by_experiment.png)

![Correct versus incorrect](RQ1_report_assets/attention_correct_vs_incorrect.png)

![Fault-type attention](RQ1_report_assets/attention_fault_type_heatmap.png)

![Root-label attention](RQ1_report_assets/attention_root_service_heatmap.png)

The correct/incorrect curves are nearly indistinguishable: entropy, blank mass, and top-10%-patch evidence precision differ by only a few thousandths after aggregation. Fault- and root-label heatmaps reveal associations with the composition of those cases, not attention *to* the named service. The current atlas has region masks but no entity/service spatial masks, so claims such as “the model attended to service X” are not supported. Full tables are [attention_summary.csv](../tmp/rq1_result_analysis/attention_summary.csv), [attention_fault_type.csv](../tmp/rq1_result_analysis/attention_fault_type.csv), [attention_service.csv](../tmp/rq1_result_analysis/attention_service.csv), and [attention_correctness.csv](../tmp/rq1_result_analysis/attention_correctness.csv).

Representative same-prefill overlays are shown full-width rather than compressed into a three-column panel:

**Qwen3.6**

![](RQ1_report_assets/attention_overlay_qwen3.6-27b.png)

**Gemma**

![](RQ1_report_assets/attention_overlay_gemma-4-26b-a4b.png)

**Qwen3.8**

![](RQ1_report_assets/attention_overlay_qwen3.8-27b.png)

### 9.4 Interpretation limits from prior work

Raw attention is not a causal explanation. [Jain and Wallace (NAACL 2019)](https://aclanthology.org/N19-1357/) show that attention can be weakly related to gradient importance and that different distributions can yield equivalent outputs. [Abnar and Zuidema (ACL 2020)](https://aclanthology.org/2020.acl-main.385/) explain that information mixes across layers and find rollout/flow closer to ablation and gradient measures than raw single-layer attention. [NOTICE (NAACL 2025)](https://aclanthology.org/2025.naacl-long.571/) further shows that grounding roles differ across VLM architectures. Accordingly, this report treats attention as a descriptive diagnostic and relies on factual/targeted/placebo/neutral counterfactuals for causal visual influence.

The result pattern is also consistent with two broader warnings: [Parcalabescu and Frank (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/37294f033582ac0064bf90fa557c2573-Abstract-Conference.html) find text contributions dominate images in tested VLM decoders, and [VLM2-Bench (ACL 2025)](https://aclanthology.org/2025.acl-long.372/) identifies persistent difficulty linking explicit visual cues. [DashboardQA (Findings EACL 2026)](https://aclanthology.org/2026.findings-eacl.177/) independently reports that real dashboard grounding and reasoning remain difficult.

## 10. Findings by experiment

### Legacy-Q9

**Performance.** Text solves most direct-reading questions. Hybrid roughly preserves Qwen performance but does not improve it materially; image-only and pixel-text are worse. This is a perception baseline, not RCA evidence.

**Cost.** Within each model, image-only `V` uses only 8.3% (Gemma), 15.6% (Qwen3.6), and 15.0% (Qwen3.8) of the all-text `T` input tokens. That compression is accompanied by lower accuracy, so it is a cost-only saving rather than an accuracy–cost improvement. Redundant hybrid `H` costs 4.9–11.6% more input than `T`. Pixel-text `P` is tokenizer-dependent: it costs only 38.0% of `T` for Gemma but about 114% for both Qwen models, while remaining less accurate.

### Cross-region one-stage QA

**Performance.** Hybrid helps Gemma and Qwen3.6 modestly on the packet average but hurts Qwen3.8. Level 3 is much harder than Level 1. Gemma alone passes the registered P1 and P2 depth tests (`+0.1087` and `+0.1667`); neither Qwen model passes both, and no factorial region main effect reaches the registered +0.10 P3 threshold. Factorial signs are unstable: Gemma benefits from visual traces but loses from visual logs/topology; Qwen3.8 benefits from visual metrics but loses from visual traces/logs. The defensible result is Gemma-specific multimodal depth complementarity, not an architecture-general region benefit.

**Cost.** Full visual `V` uses 7.4% (Gemma), 14.6% (Qwen3.6), and 14.1% (Qwen3.8) of the all-text factorial reference input. The factorial map shows that most of this compression comes from rendering the metrics region visually; switching only the smaller log, trace, or topology regions has a much smaller and architecture-dependent token effect. Hybrid `H` costs 4.9–11.8% more than all-text. Its modest Gemma/Qwen3.6 gains therefore buy accuracy with extra tokens, while Qwen3.8 pays extra and loses accuracy; there is no architecture-general Pareto improvement.

### Typed two-stage QA

**Performance.** Typed handoff improves selected Qwen visual conditions but generally reduces direct QA accuracy for Gemma and Qwen3.6. Its binding deficit, especially Gemma's 72.96%, is a real mechanism bottleneck. It should not replace direct perception measurement.

**Cost.** Full visual `V` uses 17.3% (Gemma), 25.5% (Qwen3.6), and 24.7% (Qwen3.8) of the all-text input; hybrid `H` costs 3.2–10.3% more than all-text. Pixel-text costs 40.8% for Gemma but about 112% for the Qwen models. The cheaper visual transport does not offset the observed accuracy and binding losses, so the typed visual arms are not an accuracy–cost win.

### Direct RCA

**Performance.** No model supports a positive routed-dashboard claim. `T` or `F` is best/near-best; `P` is worst. Qwen3.8 `R-T=-0.0046`, Gemma `-0.0666`, Qwen3.6 `-0.0309`. One-stage visual evidence does not improve RCA.

**Cost.** Routed `R` reduces mean input to 29.6% (Gemma) and 39.5% (both Qwen models) of `T`; full visual `V` reduces it further to 20.5% and 30.6%. Flat structured `F` costs approximately the same as `T`, while redundant `H` costs 8.1–17.2% more. These are substantial token savings for `R/V`, but because MRR does not improve they support only a cost–accuracy trade-off, not a superior RCA representation. `P` is especially inefficient for Qwen at about 182% of `T` while also performing worst.

### Matched two-stage RCA

**Performance.** Qwen3.8 is the single positive result (`R-T=+0.0615`, `R-F=+0.0625`, both Holm-significant); the net top-1 correction is +14. Gemma is negative and Qwen3.6 is small, non-significant, and formally incomplete due to 11.73% infrastructure exclusion. Therefore the supported claim is model- and pipeline-specific.

**Cost.** Routed `R` uses 42.5% (Gemma), 49.4% (Qwen3.6), and 47.5% (Qwen3.8) of `T` input; full visual `V` uses 35.2–41.6%. Qwen3.8 `R` is therefore the one clear accuracy–cost Pareto improvement in RQ1: it raises MRR while cutting input tokens by 52.5% relative to `T`. Gemma receives a similar token reduction but loses MRR, and Qwen3.6 remains formally incomplete. Hybrid costs 6.4–14.1% more than `T`, while Qwen pixel-text costs 165.7–168.9% and provides no compensating gain.

### Visual counterfactual RCA

**Performance.** Targeted transplant lowers Qwen3.8 MRR by 0.0263 relative to factual, more than placebo (-0.0055), but the registered paired tests are not significant after Holm correction. Gemma and Qwen3.6 show no coherent targeted effect. Images influence rankings, but the current experiment does not establish reliable causal benefit.

**Cost.** Factual, targeted, placebo, and neutral conditions all consume approximately 99.9–100.0% of factual input within each model. This is the intended matched-cost control: the observed ranking changes cannot be attributed to one counterfactual condition receiving a materially different token budget. The experiment is a causal sensitivity probe, not a token-saving method.

### Ledger handoff RCA

**Performance.** Text ledger is equal or better than visual ledger across models. Hybrid ledger recovers some visual loss; Qwen3.8 `L_hyb-L_vis=+0.0415` is significant, but `L_hyb-L_txt≈0`. Pixelizing a structured ledger adds no independent value.

**Cost.** Visual ledger `L_vis` costs 2.3% (Gemma), 6.5% (Qwen3.6), and 9.9% (Qwen3.8) more input than text ledger `L_txt`; hybrid ledger costs 24.4–29.8% more. Because `L_txt` is also equal or better in RCA performance, it dominates the visual ledger on both accuracy and token cost. Qwen3.8's hybrid recovery over `L_vis` is not a Pareto gain over `L_txt`: it returns to approximately the same MRR while spending 24.4% more input.

## 11. Cross-experiment conclusions

1. **Representation routing matters more than simply adding an image.** Only Qwen3.8's two-stage routed arm clears the RCA threshold; full `V`, redundant `H`, and pseudo-dashboard `P` do not.
2. **Two stages are not automatically better.** Matched-vs-direct changes vary by arm/model and mostly fail multiplicity correction. The benefit appears when Qwen3.8 combines typed evidence selection with the routed representation.
3. **Visual contribution is architecture-dependent.** Gemma, Qwen3.6, and Qwen3.8 frequently disagree on the sign of visual main effects.
4. **The visual bottleneck is cross-region use, not merely perception.** Level-1 text accuracy is near saturation, while Level-3 and typed binding fall sharply; the Gemma P1/P2 result shows that hybrid evidence can partially repair this on scoreable deep chains without making the effect architecture-general.
5. **Attention exposure is not sufficient evidence of useful reasoning.** Models heavily attend to metrics/topology, yet correct and incorrect cases have almost identical attention diagnostics.
6. **Pixel-text is a useful negative control.** It usually costs many visual tokens while losing accuracy, showing that “text rendered as an image” is not the dashboard advantage claimed by the project.
7. **Token compression and accuracy must be reported separately.** Real visual and routed arms frequently reduce input tokens by 50–90%, but most also lose performance. The only clear joint improvement is Qwen3.8 matched two-stage `R`; the counterfactual arms correctly hold cost constant, and text ledger dominates visual/hybrid ledger handoff.

## 12. Missing data and non-claims

- Qwen3.6 matched RCA exceeds the 5% infrastructure ceiling and cannot support a formal claim; its complete-subset numbers are retained for diagnosis.
- Forty-eight Qwen3.6 counterfactual requests lack raw token vectors. Their derived grids/overlays exist, but token-level re-analysis is impossible.
- There is no service/entity spatial atlas; attention can be grouped by cases whose root label is X, but cannot be localized to X.
- Root cause and injection labels do not define causal propagation paths, anomaly duration, or semantic reasoning-error classes. Those labels were not fabricated.
- Accepted labels are aliases/granularity alternatives, not evidence of multi-root incidents; Recall@K is therefore not reported as an independent metric.
- Wall-time comparisons are omitted because hardware differs. GPU active time is preserved in trajectories but is not used as a cross-hardware cost claim.
- Results use repeated exposed evaluation data, not a newly untouched confirmation set.
- Attention is single registered-layer/final-query attention, not rollout, gradient attribution, or activation patching.

## 13. Reproducibility artifacts

- Analysis program: [analyze_rq1.py](../tmp/rq1_result_analysis/analyze_rq1.py)
- Report builder: [build_report.py](../tmp/rq1_result_analysis/build_report.py)
- Record-level compact table: [records.parquet](../tmp/rq1_result_analysis/records.parquet)
- Artifact audit: [summary.json](../tmp/rq1_result_analysis/summary.json)
- Performance: [performance.csv](../tmp/rq1_result_analysis/performance.csv)
- Cost: [cost.csv](../tmp/rq1_result_analysis/cost.csv)
- Runtime: [runtime.csv](../tmp/rq1_result_analysis/runtime.csv)
- Paired statistics: [comparisons.csv](../tmp/rq1_result_analysis/comparisons.csv)
- Attention inventory: [attention_inventory.csv](../tmp/rq1_result_analysis/attention_inventory.csv)

All tables and figures are regenerated from immutable trajectory/private artifacts; no model inference was performed for this report.
"""
    REPORT.write_text(text, encoding="utf-8")
    print(REPORT)


if __name__ == "__main__":
    main()

---
name: experiment
description: Design, configure, launch and log a single VLM-RCA experiment (RQ1 dashboard axis, RQ2 controller, RQ3 model, RQ4 ablation). Use when starting a new experimental cell, writing a config YAML, submitting a SLURM job, or recording an experiment's outcome.
---

# Experiment manager

One experiment = one cell = one YAML in
`RQs/<rq>/configs/experiments/<name>.yaml`, one
output directory under `results/<name>/`, one devlog entry. Adapted from the
upstream project's conventions so both papers report comparable numbers.

## Naming

`rq1_<axis>_<level>` · `rq2_<controller>` · `rq3_<model>_<config>` · `rq4_ablate_<component>`

## Config schema

```yaml
name: rq1_ranker_coverage
parent_rq: RQ1
hypothesis: >
  Coverage-balanced KPI selection beats plain top-K because top-K can spend the
  whole panel budget on one noisy service and hide the true root cause.
design_axis: A_kpi_selection

variables:
  independent: {ranker: [ksigma, coverage]}
  dependent: [mrr, top1, top3, top5, total_tokens]
  controlled: {panel_budget: 12, topology: colored, modality: hybrid, long_side_px: 1568}

dataset: {tags: [re2_ob, aegislab, aiops2022, aiops2025, re2_tt], n_per_dataset: 20}
model: {primary: claude-sonnet-5, comparators: [qwen2.5-vl-72b]}
seed: 42
decision_rule: >
  Adopt a level over the incumbent when the paired point ΔMRR ≥ +0.03 with a
  Wilcoxon p < 0.05/k (k = non-control levels on the axis) and the sign does not
  reverse on the secondary dataset; report Cohen's d and flag |d| < 0.2 as fragile.
output_dir: RQs/RQ1/results/rq1_ranker_coverage
```

Everything under `controlled:` must be a real `DashboardConfig` / agent field —
if it is not, the control is fiction.

## Run

```bash
source scripts/env.sh
python scripts/smoke_e2e.py --model claude-sonnet-5 --dataset aegislab --n 20 \
    --experiment rq1_ranker_coverage --config coverage
```

For GPU/self-hosted models, start the vLLM server first (see the **vlm-serve**
skill), then point `VLLM_BASE_URL` at it.

## Cost discipline

The evaluation ladder exists because agentic runs on 480 cases cost real money:

| Rung | Cases | Purpose |
|---|---|---|
| L0 | 20 | parse-rate gate; catches broken configs before spending |
| L1 | 100 | all iteration and screening; Sonnet + one self-hosted model |
| L2 | 480 | frozen configs only — **never iterate at this rung** |

Budget for the whole project is ~$200–400. One-shot on 480 is ~$5–15 per model;
agentic multi-turn on 480 is ~$30–80 per model per condition, so only the best
1–2 API models get the agentic L2 run.

Rendering is CPU-only and cheap — pre-render with `scripts/prerender_config.py`
so GPU/API jobs are pure inference and resumable.

## Quality gates (all mandatory)

1. Point ΔMRR + paired Wilcoxon + Cohen's d for every A-vs-B claim
   (`RQs/vlmrca/eval/metrics.py`); per-dataset and per-fault breakdowns mandatory.
2. Per-dataset and per-fault-bucket breakdown, not just the pooled number.
3. Trajectories archived as JSONL, one line per case, with the upstream commit stamped.
4. The config YAML committed to git before the run, not written afterwards.
5. Token and wall-clock cost reported, **including image tokens**.
6. Paired Wilcoxon (`paired_compare`) for any A-vs-B claim; Bonferroni across a family.
7. Any coverage cap (top-N, sampling, skipped cases) stated explicitly in the devlog.

## After the run

Record the outcome with the **devlog** skill, and if the result settles a
design question, add an entry to `plans/design_decisions.md`.

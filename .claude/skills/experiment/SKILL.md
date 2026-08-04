---
name: experiment
description: Design, register, launch, resume, verify, and report a CanvasRCA RQ experiment. Use when creating an experimental cell, freezing prompts and configs, running inference or training, or deciding the next registered step.
---

# Experiment workflow

Read `Codex.md`, the target RQ description, latest applicable plan, findings,
and status authority before acting.

## Prepare and freeze

1. Put the config in `RQs/<rq>/configs/`, mutable runner/analysis code in
   `RQs/<rq>/scripts/`, and outputs in
   `RQs/<rq>/results/<experiment>/`. Do not touch frozen `src/`.
2. Freeze roster/partition, opaque IDs, model and tokenizer, BF16 checkpoint,
   vLLM/runtime configuration, prompts, evidence schema, renderer, scorer,
   retry/exclusion policy, code commit, and all dependent hashes.
3. Run label-leakage and model-visible OCR audits before a model call.
4. For modality/representation comparisons, require an exact atomic-fact
   inventory match. If image-only prompt is `A` and text-only prompt is `B`,
   freeze hybrid as exactly `A+B` or exactly `B+A`; do not rewrite or deduplicate
   the two arm prompts inside hybrid.
5. Use the RQ's preregistered hypotheses, thresholds, statistical family, and
   stopping rule. Do not substitute a generic effect threshold.

## Qualify

Run the partition-aware three-real-case smoke described by the `smoke` skill.
Use the same compiler, renderer, client, writer, evaluator, verifier, 32k
context, and 16k output ceiling as the planned run. Correctness is not a smoke
gate.

## Execute

- Use the unified client and canonical unquantized BF16 vLLM configuration.
- Run long jobs in the background with contract-compatible resume and unique
  call/episode keys.
- Monitor closely until stable, then poll approximately every 360 seconds.
- Do not inspect partial formal results to tune prompts, replace cases, select
  checkpoints, or stop early.
- Drain the asynchronous writer and verify the complete artifact inventory at
  lifecycle boundaries.
- Apply paired whole-case infrastructure exclusion, with the frozen threshold
  (default maximum 5%). Keep parse failures and truncations as model outcomes.

## Analyse and report

Use paired cases, per-dataset and per-fault breakdowns, the registered Wilcoxon
test and effect size, and complete token/GPU accounting. Do not report
confidence intervals. Record the result and its evidentiary status under the RQ
tree; promote a conclusion to `findings/` only after all registered gates pass.

---
name: experiment
description: Design, register, launch, resume, verify, and report a CanvasRCA RQ experiment.
---

# Experiment workflow

Read `Codex.md`, the target RQ's three description files, experiment finding,
latest applicable plan, and status artifacts.

## Prepare and freeze

1. Put RQ config in `RQs/<rq>/configs/`, Python logic in the five functional
   modules under `RQs/<rq>/src/`, shell triggers in `RQs/<rq>/scripts/`, and
   outputs in `RQs/<rq>/results/<experiment>/`. Preserve the file/line limits.
2. Freeze roster/partition, opaque IDs, checkpoint/tokenizer, the three global
   configs, explicit adapters, prompts, evidence schema, renderer, scorer,
   retry/exclusion policy, code commit, and dependent hashes.
3. Run leakage/OCR audits and exact atomic-fact parity before a model call.
4. If image-only is A and text-only is B, hybrid is exactly A+B or B+A in one
   frozen order.
5. Use the experiment's own registered hypotheses, threshold family, and stop
   rule; do not substitute a generic effect threshold.

## Qualify and execute

Use the bounded smoke from the `smoke` skill. Correctness is not a smoke gate.
Heavy runs use the shared client and an explicitly selected deployment profile:
`configs/vllm_inference.yaml` plus the Nibi launcher for Slurm, or
`configs/vllm_inference_local.yaml` plus the direct local launcher for WSL.
Local runs never invoke `sbatch`. Require a live attestation, background
execution, resumable call keys, asynchronous writes, and complete artifact
verification. Monitor closely until stable, then at the interval registered in
`Codex.md`. Do not tune from partial formal results. Pair whole-case
infrastructure exclusions and retain parse failures and truncations as model
outcomes.

## Analyse and report

Use paired cases, per-dataset/per-fault breakdowns, registered Pratt Wilcoxon,
paired Cohen's dz, and token/GPU accounting. Do not report confidence
intervals. Update the experiment's one `exp_<experiment>_findings.md` whether
the outcome is passed, failed, blocked, incomplete, static-only, or not run.

# RQ1 whole-experiment local heldout: `ledger_handoff_rca`

## Authority and scope

`ledger_handoff_rca` is assigned entirely to local execution. This is not a
shard-level split, and Nibi must submit no further shard for either model. The
local execution owns:

- experiment: `ledger_handoff_rca`;
- models: `qwen3.6-27b` and `gemma-4-26b-a4b`;
- shards: all 24, numbered 0 through 23;
- roster: all 469 frozen eligible cases;
- handoff arms: `L_txt`, `L_vis`, and `L_hyb`;
- the shared Stage-1 selector, host binding, all Stage-2 calls, scoring,
  attention artifacts, and verification.

This assignment changes only the execution site. It does not authorize any
prompt, evidence, representation, ledger, schema, model, sampling, scorer,
roster, shard, analysis, or stopping change. Local and Nibi must never execute
the same unfinished target.

## Existing Nibi checkpoint that must be reused

Nibi job 19772050 completed Qwen shard 0 normally with exit `0:0` under
`def-jacobsen_gpu`. Its aggregate summary records 17 assigned cases, 51/51
formal handoff targets, zero infrastructure errors, and 68 model calls: one
shared Stage-1 call plus three handoff Stage-2 calls per case. An independent
hash/status scan found all 68 trajectory JSON records completed and hash-valid,
with zero infrastructure, integrity, unknown-status, parse, or model-length
failures.

These are valid resumable checkpoints, not a complete experiment and not a
scientific result. Transfer them locally and do not intentionally repeat them.
The reusable paths are:

```text
RQs/RQ1/results/rq1_v22b_prepared_shared_469_20260813__shard-*/prepared/
RQs/RQ1/results/rq1_v22b_formal_469_20260813__shard-0000-of-0024/trajectories/ledger_handoff_rca/qwen3.6-27b/
RQs/RQ1/results/rq1_v22b_formal_469_20260813__shard-0000-of-0024/run_ledger_handoff_rca_qwen3.6-27b_shard000-of-024.json
RQs/RQ1/results/rq1_v22b_formal_469_20260813__shard-0000-of-0024/ledger_handoff_rca.qwen3.6-27b.*
RQs/RQ1/configs/rosters/rq1_frozen_eval_469_private_v1.json
```

Transfer all 24 prepared shard roots and the evaluator-private roster through
an appropriately protected channel. Use the same formal base ID so the
content-addressed runner recognizes Qwen shard 0. When results return, merge
only ledger-handoff-specific trajectories, conversations, summaries, logs,
runtime/server attestations, GPU records, and attention artifacts; do not
overwrite another experiment's content in the shared shard roots.

## Frozen scientific contract

Use these existing lineages:

```text
formal base:   rq1_v22b_formal_469_20260813
prepared base: rq1_v22b_prepared_shared_469_20260813
shards:        __shard-0000-of-0024 through __shard-0023-of-0024
runtime freeze: ba25fe1dcfbce970fe2da07c298a4132fb3b7df3833c2b44483434c0e72f0118
```

The scientific source hashes at handoff are:

```text
configs/vllm_inference.yaml             90de521cc56f93a8ed6c0530b79dd4c87a14f13c09d15eb9eb2b7bfd45cddd60
configs/dataset_segmentation.yaml       52ff16908335420bbaf98ff12b53996913c9ea2e18f90aa381ebb598dc99744b
configs/rca_scorer.yaml                 8f31970302ff5c840144c1de2ba48c716da7c3b223bf90e03a5bd31aed97c915
RQs/RQ1/configs/rq1.yaml                9ba849d32de71c47b0c24a4ccfa3c15c9d4750d526698bd25cb7d5b0767aa3d1
RQs/RQ1/src/main.py                     90086a7156c857fe517f8ef50762e9ff3fe2d91c868603c99447d0cf92c10a50
RQs/RQ1/src/exps.py                     1e62bc6262b44d209d726eb91c29f4421db19ff8261ce63acefcca33120b3de3
RQs/RQ1/src/gates.py                    5afbcfd7fa765b96ae2ce713ad1d770f750f65ccfd3336c3168224aaed3d53c1
RQs/RQ1/src/utils.py                    6d5cd5f83c12f05f29dfcbf1d3779ccdee81b77988ecfb3cf06ec8e5f8f14b31
RQs/RQ1/src/tests.py                    938e6102ea4d6e75a3150e7fede0daa9f019b621c38a00b5c52cf4d9dced089b
```

Required settings include:

- the exact registered unquantized BF16 Qwen and Gemma checkpoints;
- seed 42, temperature 1.0, top-p 0.95, thinking disabled;
- 40,960-token context and the unchanged uniform RQ1 8,192-token request ceiling;
- xgrammar structured output with arbitrary JSON whitespace disabled;
- the registered model-specific image and chunked-prefill policies;
- `request_concurrency=4`, while preserving within-case Stage-1-to-Stage-2
  dependencies and handoff-arm order;
- `CompactRecordKeyLedgerV4`, its deterministic label-blind binder, and the
  frozen top-five RCA scorer;
- one shared grounded Stage-1 selector set compiled into semantically identical
  normalized text, lossless pixel-ledger, and strict pixel-plus-text handoffs;
- the same candidate order and Stage-2 task shell across `L_txt`, `L_vis`, and
  `L_hyb`;
- same-prefill model-internal attention artifacts for every successful visual
  request;
- the frozen 469-case roster and 24-shard assignment.

A local deployment adapter may override paths, ports, environments, process
supervision, and GPU discovery. It must import this worktree and must not edit
the scientific prompts, arms, renderer, ledger, schema, model recipe, scorer,
roster, or shard assignment. Do not commit site-specific absolute paths into
project source or configuration.

## Execution outline for the local agent

1. Check out the exact current `canvasrca_nibi` scientific source and run
   `source scripts/env.sh`.
2. Install an inference environment compatible with the frozen vLLM stack and
   project-owned same-prefill attention hook; do not silently substitute a
   different inference stack.
3. Copy and verify all 24 prepared roots, the private roster, and the complete
   Qwen shard-0 checkpoint above. Do not rerun preparation or completed calls.
4. Start and attest one registered model server at a time.
5. Resume unfinished Qwen targets for shards 0--23 by content-addressed key,
   then execute Gemma shards 0--23. Restart only an interrupted target from its
   beginning; never splice a partial response or repeat a hash-valid terminal
   record.
6. Preserve the formal base ID, 24-shard assignment, request budgets, and
   registered arm/stage order. Do not inspect partial scientific scores to tune
   the experiment.
7. After all 48 model-shard units finish, drain writers, verify every shard,
   consolidate the experiment, and run only the preregistered analysis.

The core runner interface remains:

```bash
python -m RQs.RQ1.src.main run \
  "rq1_v22b_formal_469_20260813__shard-SSSS-of-0024" \
  ledger_handoff_rca MODEL --execute \
  --prepared-experiment-id \
  "rq1_v22b_prepared_shared_469_20260813__shard-SSSS-of-0024" \
  --shard-index SHARD_INDEX --shard-count 24
```

Run verification after each completed model-shard unit:

```bash
python -m RQs.RQ1.src.main verify \
  "rq1_v22b_formal_469_20260813__shard-SSSS-of-0024" \
  --prepared-experiment-id \
  "rq1_v22b_prepared_shared_469_20260813__shard-SSSS-of-0024"
```

Replace placeholders through the external local deployment adapter; do not
rewrite the experiment implementation.

## Completion and return criteria

The heldout is complete only when both models have a complete summary for all
24 shards and all expected target and shared-ledger records are hash-valid or
carry a registered terminal model outcome. There must be no unresolved
infrastructure, integrity, persistence, or unknown-status error. Conversations,
raw responses, prompts, token/time accounting, server attestations, GPU
metadata, and required visual-attention artifacts must be present.

Report the 289-case primary set and AegisLab, AIOPS-2022, AIOPS-2025, RE2-OB,
and RE2-TT slices under the existing RQ1 analysis contract. Before returning
artifacts, produce a manifest containing every file path, size, and SHA-256.
Nibi-side merge verification must reject duplicate call keys, conflicting
records, source/config mismatches, or results produced under changed scientific
logic.

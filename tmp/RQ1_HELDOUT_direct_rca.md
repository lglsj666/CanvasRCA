# RQ1 whole-experiment local heldout: `direct_rca`

## Authority and scope

`direct_rca` is assigned entirely to local execution. This is not a shard-level
split and Nibi must submit none of it. The local execution owns:

- experiment: `direct_rca`;
- models: `qwen3.6-27b`, followed by `gemma-4-26b-a4b`;
- shards: all 24, numbered 0 through 23;
- roster: all 469 frozen eligible cases;
- arms: `T`, `F`, `V`, `P`, `H`, and `R`;
- the registered one-stage diagnosis call, scoring, attention artifacts, and
  verification.

This is the natural one-stage RCA experiment. Each case/arm directly emits the
frozen top-five RCA JSON in one model call. It does not create a Stage-1 ledger
or make a Stage-2 call.

## Local execution baseline

Run the complete direct-RCA inference locally for both models and all 24
shards under the frozen contract below.

The shared CPU preparation is not a model result. A hash-valid preparation
already produced locally for the exact frozen roster and runtime freeze may be
reused after full verification; otherwise regenerate all 24 prepared shard
roots locally.

Use the existing final formal lineage so returned experiment-specific records
can be merged without rewriting other experiments:

```text
formal base:   rq1_v22b_formal_469_20260813
prepared base: rq1_v22b_prepared_shared_469_20260813
shards:        __shard-0000-of-0024 through __shard-0023-of-0024
```

## Frozen scientific contract

Check out the current `canvasrca_nibi` branch and preserve runtime-freeze
SHA-256:

```text
ba25fe1dcfbce970fe2da07c298a4132fb3b7df3833c2b44483434c0e72f0118
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
- Qwen native image processing with chunked prefill disabled;
- Gemma `max_soft_tokens=1120` with chunked prefill enabled;
- `request_concurrency=4`, with one asynchronous writer per concurrent case;
- the frozen candidate order, task guide, top-five diagnosis schema, scorer,
  renderer-v12, and equal-fact `T/F/V/P/H/R` representations;
- same-prefill attention artifacts for every successful visual request;
- the frozen 469-case roster and 24-shard assignment.

A local deployment adapter may override paths, ports, environments, process
supervision, and GPU discovery. It must import this worktree and must not edit
the scientific prompts, arms, renderer, schema, model recipe, scorer, roster,
or shard assignment. Do not commit site-specific absolute paths into project
source or configuration.

## Required execution order

This heldout follows experiment-major execution:

1. Verify or generate all 24 shared prepared roots with zero model calls.
2. Start only the registered Qwen server.
3. Run all 24 `direct_rca` Qwen shards from zero and verify every shard.
4. Stop Qwen and confirm that no Qwen process remains.
5. Start only the registered Gemma server.
6. Run all 24 Gemma shards from zero and verify every shard.
7. Stop Gemma, drain artifact writers, and run the final aggregate audit.

Never run Qwen and Gemma concurrently. Do not switch to another local
experiment after only a few direct-RCA shards. A timeout may resume only
missing/nonterminal targets within this experiment; a hash-valid truncation or
parse failure is a terminal scientific outcome, not a timeout checkpoint.

The core per-shard runner interface is:

```bash
python -m RQs.RQ1.src.main run \
  "rq1_v22b_formal_469_20260813__shard-SSSS-of-0024" \
  direct_rca MODEL --execute \
  --prepared-experiment-id \
  "rq1_v22b_prepared_shared_469_20260813__shard-SSSS-of-0024" \
  --shard-index SHARD_INDEX --shard-count 24
```

Run verification after each completed model/shard unit:

```bash
python -m RQs.RQ1.src.main verify \
  "rq1_v22b_formal_469_20260813__shard-SSSS-of-0024" \
  --prepared-experiment-id \
  "rq1_v22b_prepared_shared_469_20260813__shard-SSSS-of-0024"
```

Replace placeholders through the local deployment adapter. Do not change the
experiment implementation to fit the machine.

## Completion and return criteria

The local heldout is complete only when both models have a complete summary for
each of the 24 shards and all of the following hold:

- every expected case/arm record is hash-valid or has a registered terminal
  model outcome;
- no unresolved infrastructure, integrity, persistence, or unknown-status
  error remains;
- conversations, prompts, raw responses, tokens, timing, server attestation,
  GPU metadata, and required visual-attention artifacts are present;
- Qwen and Gemma checkpoint/tokenizer/config hashes match the frozen contract;
- results cover the 289-case primary set and retain separate AegisLab,
  AIOPS-2022, AIOPS-2025, RE2-OB, and RE2-TT reporting;
- the registered MRR, AC@1/3/5, AVG@3/5, parse/truncation, token, GPU-time, and
  wall-time outputs are reproducibly derived by the current verifier/scorer.

Before returning artifacts to Nibi, produce a manifest containing every
returned file path, size, and SHA-256. Return only direct-RCA-specific
trajectories, conversations, attention artifacts, summaries, runtime/server
attestations, and logs. Do not overwrite another experiment's content in the
shared shard roots. Nibi-side merge verification must reject duplicate call
keys, conflicting records, source/config mismatches, or any result produced
under changed scientific logic.

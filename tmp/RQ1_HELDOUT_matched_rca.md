# RQ1 whole-experiment heldout: `matched_rca`

## Status and scope

`matched_rca` is the first whole RQ1 experiment held out from Nibi for local
execution. This is not a shard-level split. The local execution owns all of:

- experiment: `matched_rca`;
- models: `qwen3.6-27b`, followed by `gemma-4-26b-a4b`;
- shards: all 24, numbered 0 through 23;
- roster: all 469 frozen eligible cases;
- arms: `T`, `F`, `V`, `P`, `H`, and `R`;
- both registered stages, scoring, attention artifacts, and verification.

Nibi must not submit any new `matched_rca` shard for either model. The other
RQ1 experiments remain assigned to Nibi. This heldout assignment changes only
the execution site; it does not authorize a prompt, representation, schema,
model, sampling, scorer, roster, shard, or question change.

## Existing Nibi work that must be reused

Nibi jobs 19784134 (Qwen shard 0) and 19784138 (Qwen shard 1) were canceled
while pending. Both have `Start=None` and made zero model calls.

Earlier Qwen job 19772048 reached the registered thirty-minute payload cutoff
on shard 0. Its timeout classification proves 61 completed, hash-valid
`matched_rca` records, with zero infrastructure, integrity, unknown-status,
parse, or model-length failures. These are valid checkpoints, not a completed
shard and not a scientific result. Copy and resume them locally; do not delete
or intentionally repeat them.

The reusable paths are:

```text
RQs/RQ1/results/rq1_v22b_prepared_shared_469_20260813__shard-*/prepared/
RQs/RQ1/results/rq1_v22b_formal_469_20260813__shard-0000-of-0024/trajectories/matched_rca/qwen3.6-27b/
RQs/RQ1/configs/rosters/rq1_frozen_eval_469_private_v1.json
```

Transfer all 24 prepared shard roots and the evaluator-private roster through
an appropriately protected channel. Transfer the existing shard-0 matched-RCA
trajectory directory before launching local inference. Use the same formal
base ID, `rq1_v22b_formal_469_20260813`, so content-addressed resume can
recognize those records. When results return to Nibi, synchronize only
`matched_rca`-specific trajectories, conversations, summaries, logs, runtime
attestations, and attention artifacts; do not overwrite other experiments'
content in the shared shard roots.

## Frozen scientific contract

The local deployment must preserve runtime-freeze SHA-256
`ba25fe1dcfbce970fe2da07c298a4132fb3b7df3833c2b44483434c0e72f0118` and
the prepared indexes that cite it. Required scientific settings include:

- unquantized BF16 registered Qwen and Gemma checkpoints;
- seed 42, temperature 1.0, top-p 0.95, thinking disabled;
- 40,960-token context and the unchanged uniform RQ1 8,192-token request ceiling;
- xgrammar structured output with arbitrary JSON whitespace disabled;
- the registered model-specific image/chunked-prefill policies;
- `request_concurrency=4`, with arms and Stage 1 -> Stage 2 serial per case;
- the exact `CompactRecordKeyLedgerV4` binder and frozen RCA scorer;
- renderer-v12 and equal-fact `T/F/V/P/H/R` representations;
- same-prefill model-internal attention artifacts for every visual request;
- Qwen and Gemma phases sequential, never concurrent.

The local agent may create an external deployment adapter for paths, ports,
environment locations, GPU discovery, and process supervision. It must import
this worktree's code and must not edit the scientific experiment to fit the
local machine. Record the actual GPU, count, driver/CUDA stack, module or
package freeze, model hashes, effective config hash, adapter hash, peak memory,
and termination reason. A missing required attention artifact or a freeze/hash
mismatch is an infrastructure/integrity error, not a wrong model answer.

## Execution outline for the local agent

1. Check out the exact current Nibi scientific source and load project-relative
   environment variables with `source scripts/env.sh`.
2. Install an inference environment compatible with the frozen vLLM stack and
   the project-owned same-prefill attention hook; do not silently substitute
   another inference stack.
3. Copy the 24 prepared shard roots, private roster, and 61 existing Qwen
   shard-0 records described above. Do not rerun preparation.
4. Start and attest one registered model server at a time.
5. Run all unfinished `matched_rca` targets for Qwen shards 0--23, then run
   Gemma shards 0--23. Resume by content-addressed target; restart only an
   interrupted case/arm call, never a hash-valid completed record.
6. Preserve the 24-shard assignment and formal base ID. Do not resample cases,
   inspect partial scores to tune the run, or combine local and Nibi calls for
   the same unfinished target.
7. Run the project verifier and registered paired analysis only after all 48
   model-shard units are complete.

The core runner interface, after the local model server and deployment adapter
are ready, remains conceptually:

```bash
python -m RQs.RQ1.src.main run \
  "rq1_v22b_formal_469_20260813__shard-SSSS-of-0024" \
  matched_rca MODEL --execute \
  --prepared-experiment-id \
  "rq1_v22b_prepared_shared_469_20260813__shard-SSSS-of-0024" \
  --shard-index SHARD_INDEX --shard-count 24
```

Replace placeholders through the local deployment adapter; do not rewrite the
experiment implementation.

## Completion and return criteria

The heldout is complete only when both models have a complete summary for each
of the 24 shards, every expected case/arm record is hash-valid or carries a
registered terminal model outcome, infrastructure errors are resolved, writers
have drained, and required conversation, token/time, server-attestation, GPU,
and visual-attention artifacts exist. Report the 289-case primary datasets and
RE2-OB/RE2-TT slices under the existing RQ1 analysis contract.

Before merging, produce a manifest of every returned file and its SHA-256.
Nibi-side verification must reject duplicate call keys, conflicting records,
source/config mismatches, or results produced with changed scientific logic.

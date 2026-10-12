# 2026-09-29 — RQ3.8 v7 formal submission

## Scope and status

RQ3.8 `ops_components_v7`; 480 exposed eval and 360 exposed test cases. The four formal jobs are **submitted/pending**, not completed results. The current source contract and the operational adoption of the passed 18/18-call GPU smoke are recorded in `smoke/artifact_review.json`; `qualification/static.json` passed. CPU regression was explicitly waived by the user and is recorded as **not run**.

## What happened

- Synchronized the frozen RQ3.8 parent export (480 public cases), RQ3.4 contexts (180), RQ3.7 contexts (660), RQ3.7 locked public caches, and canonical public per-case data from the local worktree to `/scratch/lglsj/CanvasRCA` on Nibi. Both transfer processes exited 0.
- Checked all 840 roster entries for their required canonical graph, metadata, metrics, traces and logs files, plus their frozen parent or predecessor context, public cache, preparation flag and private evaluator record. Missing dependency count: **0**. This is a presence check, not a new full-hash or CPU regression run; export will verify critical source hashes when jobs prepare inputs.
- Nibi accepted four eight-hour H100 jobs: Qwen shard 0 `22945130`, shard 1 `22945133`, shard 2 `22945134`; Gemma full-cohort shard `22945136`. Gemma has an `afterany` dependency on all three Qwen jobs to avoid preparation writes racing. Slurm reported all four pending immediately after submission.
- Planned formal positions remain 19,440 across both models and all registered arms; **zero formal model calls had completed at submission time**. Each allocation prepares its own assigned cases before loading vLLM.

### Transfer incident and correction

The first multi-source `rsync` omitted `-R`, flattening roughly 31 GB of
RQ3.4/RQ3.7 source files into new paths at the Nibi repository root instead
of their required RQ-local directories. The transfer was stopped. After
checking that the root-level `contexts/`, `registration.json`, `export_v1/`,
`public_cache/`, `preparation_flags/` and `private/` targets were only this
attempt's misplaced copies, those exact targets were removed. No source cache,
correct RQ-local target, model or experiment result was deleted. The successful
retry used `rsync -aR --partial`; the canonical public tree was separately
sent to its explicit target parent. The predecessor SQLite ledger required
`-aL` because its local path was an absolute symlink. The final transfers
both exited 0, and the roster-path check above was performed **after** them.
The generalizable failure mode and recovery checks are in
`docs/issues/RQ3_8_nibi_startup_2026-09-29.md`.

## Validity and caveats

The 18/18-call smoke is qualification evidence, not formal efficacy evidence. The transfer and roster-presence check do not prove that all 840 future exports, renders or context-window checks will pass. The smoke throughput also does not guarantee that the four eight-hour allocations can finish 19,440 positions. No arm, case, model input, scorer or renderer was changed during the transfer and submission.

The earlier zero-call smoke jobs and the v6 over-context attempt remain failed
historical attempts; they are not reclassified by v7's passage. Nibi SSH/MFA
expiry is an access interruption, not an inference failure. The acceptance of
four Slurm job IDs does not establish that any formal request has started.

## Decisions

The user authorized skipping CPU regression and using at most four eight-hour formal jobs. The documented three-Qwen/one-Gemma operational split covers every registered case and arm without changing their scientific definitions. See `RQs/RQ3_8/descriptions/RQ3_8_experiments.md` DD-20260929-07.

## Blockers

None at submission. The jobs are waiting for Slurm resources and dependencies.

## Next steps

Check job and preparation logs after allocations start; if an eight-hour allocation ends before its shard is complete, report the remaining work and request authorization before any additional formal job.

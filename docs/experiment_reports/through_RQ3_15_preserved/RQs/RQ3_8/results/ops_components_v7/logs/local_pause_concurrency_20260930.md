# 2026-09-30 — Local Gemma force stop and concurrency amendment

## Scope and status

RQ3.8 `ops_components_v7`, reduced local queue. Qwen's three shards had
completed; Gemma's single shard was interrupted by explicit user instruction.
This is an operational handoff, not a completed efficacy result.

## What happened

Gemma used 36 driver request/case tasks and the shared 300-second request
timeout. Server logs showed mostly 1–2 requests running and about 33–34
waiting. At inspection, completed requests had 292.6-second median time to
first output, and 66/66 inspected timeout partials had zero output chunks.
The user first requested a safe pause, then requested an immediate force stop.
The exact local RQ3.8 runner, vLLM service and queue were killed. A stop-time
snapshot counted 231 done, 78 request-timeout fail, 47 design-infeasible flags,
and 7 submitted targets without terminal flags. GPU service processes exited.

## Validity and caveats

No completed artifact was deleted or reclassified. Terminal timeout flags
remain skipped by the existing resume logic; unflagged submissions are
incomplete. Force stopping can leave partial files, which are not completed
answers. The 36-to-8 change is an untested operational mitigation, not proof
that all later Gemma requests will finish within 300 seconds.

## Decision and next step

`concurrency_by_model` now limits Gemma to 8 while Qwen remains 36. No GPU
smoke or formal run was started after the change. Wait for the user's explicit
instruction before resuming or revisiting earlier timeout failures.

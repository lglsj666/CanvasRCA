# 2026-09-23 — Stage timeout continuation repair

## Scope and status

RQ3.3 witness_v2 calibration-to-screen transition; operational repair, not an
efficacy analysis. Calibration is terminal: 478 done and 2 classified request
timeouts across 480 logical units. All 60 screen contexts remain prepared.

## What happened

The request runner continued after timeout, but the next stage rejected any
failed_units count. Variant/budget/check decisions also rejected any excluded
case, creating the same mismatch later. Fixed classification and common-case
decision handling; updated supervisor step before checking a new stage so its
failure report no longer points to the previous analyze command.

## Validity and decisions

Requests, evidence, model recipes, per-case scorer, thresholds and tie-breaks
unchanged. Timeouts remain fail, are not retried and are not zero-imputed.
Decision cohorts exclude each timeout-affected case jointly across compared
conditions; record excluded IDs and paired_n. Budget levels also share one
cohort. Unknown/non-timeout errors, missing cells and unavailable primary
conditions still block. No 5% failure gate. No completed result or preparation
was deleted; no original smoke record rewritten. Decision-cohort clarification
is registered before any formal screen outcome, not chosen from its scores.

## Validation

65 synthetic tests, Ruff E9/F, shell syntax and whitespace checks pass. A
one-time 15.004-second CPU repair audit reproduces all 90 original smoke input
identities, preserves terminal flags, and confirms actual calibration admission.
The latter reads tiny flags only and takes 0.023 seconds; the larger repair
audit is not part of future resume. No new GPU smoke calls.

Contract: `569ba594f36c0074e788153d0c2f22da30f2153c822ee267cd1684880d194aa9`.
Prior qualifications and registration preserved under
`contract_migrations/stage_timeout_continuation_v1/before/`; CPU proof and
explicit adoption record stored alongside them. Qualification inherits original
live smoke coverage, not a claim of new live testing.

## Next step

Resume the existing sequential queue. Skip completed calibration and contexts,
then run screening; retain registered scientific admission rules for later
expansion. Runtime status is authoritative in `formal_queue_status.json`.

## Resume observation

21:27:38 local time: resumed queue PID126989, supervisor
`logs/formal_queue/supervisor_20260923_212738_stage_timeout_resume.log`.
Calibration skipped immediately with all 480 flags retained; prepared screen
contexts reused. Qwen screen started at 21:29:19. At 21:30:37, 14/540 Qwen
screen logical units were done, none failed, and 36 runner tasks were in flight;
Gemma screen remains queued. New chat completions returned HTTP200 and GPU
utilization snapshot was 99%. This establishes startup and new persistence,
not a guarantee against future failures. An optional deep_gemm import warning
occurred during initialization; engine startup and subsequent inference
continued, so it was not the cause of the diagnosed stage-transition exit.

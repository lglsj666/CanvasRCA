# 2026-09-20 — RQ3.2 identifier-boundary repair

## Scope and status

`exp_signal_selection`, Qwen formal eval phase, incomplete at diagnosis.  The
480-case preparation was complete.  The queue had committed 29 model requests
and stopped after seven implementation failures were recorded.

## What happened

The model-visible representation audit rejected one cached Denum log template
containing a raw Kubernetes service DNS name and one cached trace operation
containing a UUID path component.  The DNS-bearing fact occurred in six
registered arms of one AIOPS-2022 case; the UUID-bearing fact occurred in the
P0 arm of one AegisLab case.  All seven failures happened before model-call
submission.  One separate committed model-output failure is unrelated and is
retained as a model outcome.

RQ3.2 now applies the existing deterministic typed infrastructure-identifier
sanitizer immediately before compiling every text/image twin.  Targeted
request construction passed for all seven affected units.  The relevant
RQ3.1/RQ3.2 regression set passed (28/28 representation tests, followed by
12/12 focused execution and leakage tests).

The first restart attempt also exposed that an externally written PID could
refer to a short-lived launcher rather than the detached queue shell.  No new
request had been submitted.  The orphaned model-loading process was stopped,
and the formal queue now atomically owns its real PID marker and rejects a
second live runner.  Shell syntax and the complete RQ3.2 execution test module
then passed (11/11).

## Validity and caveats

The durable selection contexts were not modified or regenerated.  Selection,
fact inventory, numeric telemetry, candidates, units, ordering, and relation
semantics are unchanged; only raw infrastructure strings are represented by
case-local typed aliases.  A scan of all 29 persisted prompts from before the
stop found no raw IP, UUID, Kubernetes DNS, or cluster-local identifier, so
those committed results remain valid and are not rerun.

## Decisions

Only the seven reviewed implementation failures are authorized for retry.  An
append-only `retry_authorized` journal tombstone supersedes each active failure
entry; the original flags are moved to a repair-history directory.  General
`failed` flags remain terminal and are never retried automatically.

## Blockers

None after retry authorization and queue restart.

## Next steps

Resume the existing formal queue.  Skip all committed/model-failure units by
their atomic flags, rerun only the seven repaired logical units, and continue
the registered experiment order.

## Restart outcome

The detached queue restarted with its self-owned PID and resumed
`exp_signal_selection`.  All seven repaired logical units subsequently reached
`complete`; no new implementation-failure flag was created.  The one active
failure flag that remains is the pre-existing committed model-output failure,
which is intentionally retained.  The queue continued submitting the remaining
registered units.

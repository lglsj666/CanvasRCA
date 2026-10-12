# 2026-09-30 — Reduced local v7 continuation

## Scope and status

User-approved scheduling reduction, DD-20260930-10. Original local queue
stopped via its USR1 handler; inference requests and writers drained, then
the owned server stopped. No original result or flag was removed.

## What happened

- Stop snapshot:1284 initiated calls,1278 complete,6 infrastructure timeouts,
  zero started transactions. Terminal flags:1283 done (including5 references),
  6 fail and56 design-infeasible logical cells.
- Active schedule:A7680+B600+C1440=9720 positions, preserving840 unique cases.
- 603 already-spent calls fall outside the retained schedule and remain in
  cost accounting. Logical schedule+sunk+18 v7 smoke gives10341 conservative
  positions/attempts; existing PNG dedup and design skips suggest about10137
  requests, before any further runtime capacity exclusions. Not a guarantee.
- Config uses an explicit queue subset; original definitions and ledger caps
  remain historical authorities. VERSION, call IDs and completion flags remain.
- Static checks passed.15 small synthetic scheduling/resume/timeout/dedup tests
  passed in0.49s. No full CPU regression or new GPU smoke was run.
- Full-roster terminal flag scan took0.025s; preparation commit scan0.264s.
  Neither opened completed public inputs, PNGs, trajectories or raw data.

## Validity and caveats

No interim diagnostic scores informed the reduction. Request compiler and
effective runtime file hashes are unchanged (see adjacent JSON receipt).
Reduced branches are incomplete exploratory evidence; do not fabricate their
remaining results or treat their persisted rows as a complete comparison.
Design-infeasible exclusion remains DD-09; update the old analysis zero-fill
before a future scientific report. Exposed test is not independent validation.
Nibi jobs are outside this local continuation and were not changed.

## Next steps

Start the existing local queue with CANVASRCA_RQ38_RESUME_PREPARED=1, skipping
export/render; continue Qwen shards0–2 then dense Gemma31 shard0. Check startup
and first new reduced-schedule submissions, then return control to the user.

## Startup confirmed — 00:07 EDT

Started in tmux `canvasrca-rq38-local-full` at00:04 EDT. Qwen readiness took
140.13s. Runner reports `reduced_20260929`, shard0 target1644 and162 pending
cases. The first36 fresh submissions are all retained arms; no fresh
infrastructure failure was recorded at inspection. vLLM reports6 running and
30 waiting requests, GPU99%, confirming inference rather than mere residency.
The server emitted an operational Triton warmup/JIT warning, not a fatal error.
No extended monitoring performed. Queue log: `local_reduced_20260930.log`.

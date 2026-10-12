# 2026-09-08 — Preserve answer attention across KV-cache recomputation

## Scope and status

Qwen, formal evidence selection. The first phase stopped with 601 complete,
3 model-failure and 28 design-infeasible terminal records. Four additional
requests had complete persisted RCA responses but failed required attention
persistence; 7,044 targets were not started. Model failures are unknown candidate
IDs, not infrastructure failures and not retry targets.

## Cause and fix

All four affected probe payloads report recomputed prompt tokens. The live hook
published answer attention, then overwrote its payload with a prefill-only
snapshot when vLLM recomputed the prompt after preemption. The answer snapshot
was not republished because the answer-token count had not changed.

The shared hook now retains the first valid prefill payload, consistent with
its existing first-observation Q/K/V policy, and does not overwrite it on
recomputation. This changes diagnostics only: no input, sampling, model recipe,
processor geometry, evidence selection or RCA scoring is modified.

## Verification, preservation and recovery

A CPU tensor regression reproduces the missing generation profile under the
old code for both text-only and image-bearing prompts; both pass after the
one-condition fix. The 48 RQ2.1 CPU tests pass. Current qualification is an
explicit CPU follow-up, not a claim of extra live-smoke coverage.

The 604 successful/model-failure RCA terminal records retain their original
bytes. The 28 zero-call design markers are archived because their signatures
include runtime code; unchanged CPU constraints regenerate their metadata,
without spending calls. All 480 prepared cases are retained. The four failed
raw responses and partial diagnostics are moved, not deleted, to
`exp_evidence_selection_formal_v1/infrastructure_attempts/attention_preemption_repair/`.
Their original attempts remain charged against the call ceiling. Missing true
attention cannot be reconstructed from response text, so only these four targets
need new calls from the registered repair reserve. No output is invented or
silently presented as having attention it lacks.

## Next steps

Resume the registered full supervisor, verify these four repaired targets and
resume 15-minute monitoring. The guard leaves model input bytes unchanged;
the remaining valid records are not re-run. Evidence is in `before.json`,
`probe_test_before.log`, `probe_test.log`, `cpu_tests.log` and `proof.json`.

16:30 UTC follow-up: all four retry targets completed with persisted prefill
and answer attention. The 604 prior model outcomes were skipped on resume;
the phase continued beyond its previous stop without a new infrastructure
error. The four new requests consume four calls from the repair reserve.

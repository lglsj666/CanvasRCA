# 2026-09-29 — RQ3.8 v7 local full queue launch

## Scope and status

Local WSL execution of the registered RQ3.8 v7 matrix (eval480 plus exposed
test360, Qwen3.8-27B and Gemma-4-31B-it). The queue has started; preparation
is in progress. This is not a completed result.

## What happened

- The user requested direct local full execution, including preparation,
  following the successful Nibi v7 smoke. The Nibi jobs remain independent.
- A local-only deployment adapter selects the existing local BF16 inference
  recipe, the local model directories and RTX PRO 6000. Scientific arms,
  evidence, rendering, requests, output ceiling, scorer and case roster stay
  unchanged. No attention is recorded.
- Static source/shell checks passed; queue initialization registered 840 cases
  and 19,440 planned logical positions. The background tmux session is
  `canvasrca-rq38-local-full`; its log is `local_formal_20260929.log`.
- The queue prepares Qwen shards 0–2 before starting either model. It then
  executes Qwen shards 0–2 and Gemma shard 0 in sequence. Completion flags
  permit resuming only unfinished work.
- The first export attempt stopped before any GPU call when a public
  `propagation_service` row had `onset_rel_min_display: null`. The exact-match
  ledger used a string method on that null field. The corrected matcher now
  fails closed and retains the full event card; it does not infer a time or
  delete evidence. A focused pure-function check and renewed static check
  passed. The queue restarted and reused only completed export flags.

## Validity and caveats

Local CPU regression and local GPU smoke were **not repeated** at the user's
direction; the Nibi smoke is prior request-path evidence, not a local hardware
attestation. Startup will separately record the live local device and model
identity. A preparation/runtime failure stops the queue and must be diagnosed;
it is not an RCA outcome. Local hardware timing must not be pooled with H100.

## Decisions

The local queue has no Slurm allocation or internal eight-hour stage deadline.
The Nibi per-job limit is not a local execution requirement. Results remain in
the local worktree; no automatic merge with Nibi result files is authorized.

## Blockers

None at launch. GPU inference has not yet begun because CPU export/render is
still running.

## Next steps

Inspect `local_formal_20260929.log` and terminal flags for progression. If the
queue stops, diagnose the first failing stage and resume from durable flags.

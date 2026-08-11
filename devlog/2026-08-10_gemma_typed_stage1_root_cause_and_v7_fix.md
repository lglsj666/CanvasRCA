# 2026-08-10 — Gemma typed Stage-1 root cause and v7 fix

## Scope

Diagnosed the latest local formal RQ1 typed runs, audited official Qwen/Gemma
serving guidance, and changed only the successor typed Stage-1 transport in the
Nibi repository. Existing VisOps, perception, renderer, RCA, scorer, and result
artifacts were not rewritten.

## Evidence

- Latest local formal development: Gemma Stage-1 failure marker in 629/1530
  case-arm cells (41.1%); Qwen was approximately 0.3%.
- Latest local formal independent: Gemma 654/1530 (42.75%); Qwen approximately
  0.5%.
- The old schema allowed generic one-to-three-step ledgers, required long raw
  sequence copies, and rejected the whole ledger after one missing step.
- A matched Gemma `top_k=0` versus official `top_k=64` diagnostic returned
  byte-identical 4,239-token responses with the same omitted Level-3 steps.
- Official guidance recommends Gemma `temperature=1.0/top_p=0.95/top_k=64`.
  Qwen non-thinking guidance recommends `0.7/0.8/top_k=20` with
  `presence_penalty=1.5`. The active sampling protocol was not silently changed.

## Change

Protocol `rq1_typed_selector_binding_v9` fixes q1/q2/q3 and every required step
in the grammar. The model selects visible public row keys; the host copies exact
values from `qa_packet`. Unsupported selectors remain isolated. The binder
normalizes only the fixed visual labels `bins/events/errors/spans/p95ms` and
`neighbor_roles`; it never reads labels, answers, or evaluator mappings.

## Verification

- Python compile, complete RQ1/project static checks, and `git diff --check`
  passed with zero model calls.
- RQ1 functional source total: 4,145 lines, below the 5,000-line limit.
- Three-case Gemma T/V/H smoke: six calls; 3/3 Stage-1 parse and 3/3 Stage-2
  parse; all finish reasons `stop`; Stage-1 output 303–351 tokens.
- The first selector grammar incorrectly made every entity/edge nullable. This
  was a schema regression, not a visual-capability result: the latest formal
  all-visual runs had IDs in 90/90 development and 90/90 independent cases.
- V9 makes the public-template-required identifier mandatory and explicitly
  represents a verified visible entity with zero G edges. The successor smoke
  and post-hoc rebinding support all 6/6 steps in T, V, and H.

## Status and next step

The required-identifier selector grammar was live-qualified; v9's explicit
zero-edge binder was static-tested and post-hoc verified on the unchanged raw
T response without another model call. The smoke is diagnostic only and does
not establish RQ1 efficacy. Future formal
Nibi runs require fresh preparation/runtime hashes and a new result ID. Any
change from the common project sampling recipe to model-specific official
recipes requires a separate explicit protocol decision.

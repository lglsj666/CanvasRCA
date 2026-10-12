# Composer learning — SFT complete; utility learning not yet evaluated

## Current evidence — 2026-09-11

Format SFT completed update 320 (9,600 examples across two epochs). The
checkpoint-320 Composer-only validation completed all 140 held-out validation
cases: 70 AIOPS-2022 and 70 AIOPS-2025. JSON syntax passed 140/140, schema/card
binding 136/140, and actual rendering 110/140 (48/70 and 62/70 respectively).
All replies ended with `stop`; no Solver request was made in this phase.
[Original validation audit](../results/formal_balanced_v1/logs/sft_validation_20260911.md).

These are tool-use/format outcomes, not RCA MRR or measured BASE-to-SFT gains.
There is no matched BASE validation on those 140 inputs. Do not infer that SFT
improved dashboard quality, selection utility or RCA from its low training loss.

The separately versioned CPU failure replay reproduced the original outcomes.
A forward height-aware metric-label fix makes five more saved proposals
drawable, while preserving the 110 original successful PNGs byte-for-byte.
Three other original metric-label failures reach a later log-capacity failure.
Thus 115/140 is a **counterfactual tool-replay** result, not the original SFT
validation score or a new model-generation result. Long log-card capacity and
unobservable layout constraints remain unresolved; stability is not established.
[CPU replay](../results/readable_layout_repair_v1/summary.json).

All older paragraphs below retain their historical status. Their statements
that training had not run describe those earlier dates, not the current state.

## Latest qualification review — 2026-09-10

Forward repair v3 passed in 305.24 seconds with seven new calls (thirteen
cumulative in this logical smoke), a real disposable optimizer update, one
drawable BASE proposal and two harness Solver controls. All call/attention
inventories and the sampled complete I/O review passed. No formal training has
run. [Current manual review](../results/exp_composer_learning_smoke_repair_v3/review.md)
supersedes the pending-repair status in the historical paragraph below.

The balanced 300-train/140-validation split is materialized. A disposable
train-only optimizer update and six inference calls completed in learning repair
v2; no formal SFT/RL has run. Manual input review found epoch-valued clock metric
summaries, so the automated transport pass does not qualify formal inputs.
RQ3-only relative-clock projection and fresh qualification are in progress.
Original records and six consumed calls remain unchanged. Detailed evidence:
[repair-v2 review](../results/exp_composer_learning_smoke_repair_v2/review.md).

## Current qualification status — 2026-09-09

No training has run. This experiment's first logical smoke initiated zero
calls because its readiness probe lacked local authentication; the original
timeout-only status is overridden by manual review. The bug is fixed and
later independent smokes exercised the repaired common path, but this first
logical smoke was not reset or declared passed. The current isolated split
is 251 train / 90 validation; catalogue inputs are 16,246/16,261 tokens.
See [qualification handoff](../descriptions/RQ3_qualification_20260909.md).

The material below is the earlier pre-smoke state, retained as history.

No SFT, RL, winner-imitation training or model-calling smoke has run.
No learning, RCA gain, or cost-reduction claim is available. The approved
protocol is in `../descriptions/RQ3_experiments.md`.

CPU work implements grouped data isolation, the full-pool/DSL interface,
selection/design interventions, durable call accounting and SFT/RLOO update
primitives. The end-to-end training orchestrator is **not qualified or complete**.
The exhaustive v1 Composer catalogue failed the context preflight. DD-148's
explicit balanced candidate directory now fits on the same two AIOPS
validation pools (16,346 and 16,292 input tokens). This is a CPU capacity
result, not a model-calling smoke or a learning result. It does not demonstrate
that the candidate retrieval preserves all useful root evidence; that coverage
and end-to-end performance must still be measured.

# RQ1 Experiments

RQ1 has six registered experiments implemented by the compact engine in
`RQs/RQ1/src/`. They reuse the unified inference, segmentation, and RCA-scoring
contracts in `configs/`. Every experiment is rerun on Nibi under a new result
ID; historical local results remain context rather than final evidence.

## Final evaluation roster

Use all 469 eligible cases from the long-frozen project evaluation roster:

| Dataset | Eligible cases | Reporting role |
|---|---:|---|
| AegisLab | 96 | primary |
| AIOPS-2022 | 100 | primary |
| AIOPS-2025 | 93 | primary |
| RE2-OB | 90 | separate saturated-domain slice |
| RE2-TT | 90 | separate final OOD slice |

The eleven cases carrying the existing invalid status are excluded without
replacement. The headline inferential set is the 289 primary cases. RE2-OB and
RE2-TT are reported separately and never pooled into the headline effect.
Every model and arm uses the same case roster and paired exclusion policy.

## `legacy_q9`

Nine direct operations test whether the model can read individual metric, log,
trace, and topology facts. T/V/H provide text-only, image-only, and strict
image-first A+B inputs. Exact-match accuracy is perception evidence, not RCA
accuracy.

## `cross_region`

Level-1 direct reads, level-2 two-region joins, and level-3 three-region joins
test composition across M/L/R/G. Sixteen text-versus-visual factorial cells
plus strict A+B localize representation effects. Short question identifiers
only associate outputs with questions; complete-chain and step accuracy score
the reasoning result.

## `typed_two_stage`

The cross-region packets run through a typed observation ledger before the
answer stage. This measures extraction, grounding, and handoff attrition. It is
an agent-mechanism experiment rather than an RCA endpoint.

## `matched_rca`

This end-to-end RCA experiment compares five equal-source arms: complete text
`T`, stable flat JSONL `F`, renderer-v12 image-only `V`, strict image-first
`H=A+B`, and routed `R` with metrics/topology visual and logs/traces textual.
Stage 1 produces a normalized evidence ledger; Stage 2 sees only that ledger
and the common candidate/task shell and returns ranked top-five RCA JSON.
Paired `R-T` and `R-F` MRR comparisons are primary; AC@1/3/5 and AVG@3/5 are
secondary.

## `visual_counterfactual_rca`

This experiment tests whether image semantics causally move the final RCA
ranking rather than merely changing prose. Starting from the strict hybrid,
keep its text, candidates, prompt, layout, and compute fixed while comparing:

- the factual image;
- a label-blind targeted transplant that swaps complete visual identities of a
  high-evidence and low-evidence entity;
- a matched placebo transplant between similarly weak entities; and
- a neutral sham that preserves the canvas and visual budget but removes
  incident evidence.

The intervention selector uses only frozen model-blind telemetry/graph
statistics and never root labels. Primary mechanism outcomes are the
target-minus-placebo directional rank shift, top-1/top-5 changes, and ledger
changes. Factual RCA MRR remains separately reported; output sensitivity alone
is not an accuracy benefit.

## `ledger_handoff_rca`

This experiment isolates whether a useful visual observation survives the
Stage-1-to-Stage-2 boundary. From one grounded Stage-1 observation set, compile
three semantically identical handoffs: normalized typed text, a fixed visual
ledger, and strict image-first visual-ledger-plus-byte-identical-text. Stage 2
uses the same candidates, task shell, decoding budget, and top-five schema in
all cells and cannot reopen the original evidence. Compare transfer/grounding,
unsupported claims, ranking disagreement, and final MRR. This distinguishes an
upstream perception failure from a lossy textual handoff and tests whether a
visual intermediate representation adds value after evidence extraction.

## Related-work boundary

CodeShrink ([arXiv:2607.29637](https://arxiv.org/abs/2607.29637)) is a 2026
preprint about code-image compression, not an RCA method. Its transferable idea
is to spend a fixed visual canvas on readable evidence rather than blank space.
CanvasRCA does not adopt its attention/KV pruning, training, or learned
configuration machinery. A fixed-fact blank-space compaction experiment is
deferred to RQ2, where layout is the controlled variable. RQ1 instead adds the
counterfactual-influence and handoff experiments above because they directly
test representation use without changing dashboard content.

Heavy execution, bounded qualification, and artifact verification occur on
Nibi. The WSL preparation does not produce scientific model results.


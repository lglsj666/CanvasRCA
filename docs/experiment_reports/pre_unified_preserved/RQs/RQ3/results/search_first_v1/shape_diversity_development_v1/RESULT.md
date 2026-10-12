# SEARCH37 — Soft within-owner curve diversity

2026-09-12. Completed **train-only exploration**, not a promoted pipeline.
Reference: SEARCH34 native top24 on the same additional24 training cases,
12 per AIOPS dataset. No validation/eval, Composer, SFT/RL or attention.

## Intervention and integrity

Keep24 metric slots and the native renderer, axes, labels, static prompt,
candidate list, model recipe and scorer. Penalize highly correlated curves
from the same owner using the registered relevance/diversity weight .75.
Original source facts are retained unchanged when selected; trace/log selection
is unchanged. Selected-owner G context can change. This is a selection-policy
contrast, not an equal-information modality comparison.

The initial CPU gallery rejected canonical numeric strings before any call.
The strict numeric decoder was corrected and tested without filling missing
values or accepting non-finite strings. Preserve gallery_v1 and its review.
Final341 CPU checks pass. All24 public input/selection/primitive audits pass;
six old/new PNGs were replayed and three actual new PNGs inspected. All24
complete PNGs differ from the reference, requiring24 new calls.

Work spec: `effbf617a5496455d0c68d95e643a9893be4bbafd0478dbb92ce58570ac9bf4f`.
The24 calls completed in380.019 seconds. No transport, schema, truncation or
persistence errors; all finish reasons are stop, all return five distinct
allowed IDs. Maximum output898 tokens. All272 frozen dependencies still match
after execution. Every new answer was read in full;48 paired record inventories,
canonical hashes, conversations, actual requests, image bindings and scorer
recomputations pass. The common prompt and09ED full conversation were inspected.
No post-score response replacement or correctness retries.

## Performance and cost

| Dataset (12 train cases each) | Native MRR | Diversity MRR | AC@1 native → new | AC@3 native → new | AC@5 native → new | Mean input | Mean output native → new |
|---|---:|---:|---:|---:|---:|---:|---:|
| AIOPS-2022 | .423611 | .479167 | .3333 → .4167 | .4167 → .5000 | .6667 → .5833 | 17,754 unchanged | 252.08 → 281.08 |
| AIOPS-2025 | .298611 | .236111 | .1667 → .1667 | .4167 → .3333 | .5000 → .3333 | 17,649.5 unchanged | 261.17 → 317.67 |

Both have16,002 image tokens per call. Mean output increases29.0 and56.5
tokens. Pooled MRR .361111 → .357639, not an overall gain. Exact per-fault and
granularity breakdowns are in `metrics_breakdown.json`.

| Dataset | RR repairs | RR breaks | Ties | Delta MRR | Pratt p | Holm p | Paired dz |
|---|---:|---:|---:|---:|---:|---:|---:|
| AIOPS-2022 | 3 | 2 | 7 | +.055556 | .75 | 1 | .12196 |
| AIOPS-2025 | 1 | 3 | 8 | −.062500 | .50 | 1 | −.29678 |

Repeated small training-set exploration: these descriptive effects and
exploratory tests do not establish the requested final performance targets.
Root-associated direct telemetry remains selected in18/24 cases in both
conditions (11 A22,7 A25). This coarse coverage indicator neither measures
diagnostic sufficiency nor implies that all selected evidence is equally useful.

## What the complete answers show

- 7CE improves .25→1 and C86 .3333→1. C86 identifies the large GetProduct local
  latency as relevant, instead of relying solely on noisy resource counters.
  Some causal assertions are still unsupported; correct ranking does not make
  every sentence correct.
- 33C drops1→0: the answer prefers JVM class loading as a resource fault over
  the visible node IO evidence. Shape diversity can replace context with
  semantically weak but distinct signals; novelty is not diagnostic utility.
- B324 drops.5→0 and calls service346 the origin because it is an upstream
  caller. It treats traffic direction as causal direction, despite the common
  guide warning against that inference.
- 740 improves0→.5 but favors a tiny GC-duration change because of its large
  z-score and early onset. C76 and209 likewise interpret moderate resource
  changes as exhaustion without establishing capacity limits or hosting.
- 17BB calls a three-digit service ID a four-digit node and attributes a
  different row's resource value to it. This is an observable owner/type error,
  not a source-identity change introduced by the selector.
- 987 invents a relationship between a normalized log suffix and a candidate
  pod ID. Such a relationship is not supplied by the prompt or identity map.
- 09ED produces898 tokens, a normal completion rather than runaway truncation.
  Its ending prose proposes a different ranking from the already emitted
  `services` array. The registered array is scored unchanged. Prior SEARCH17
  already tested reason-first ordering and did not improve its small cohort;
  this observation alone is not a reason to repeat that same intervention.

## Decision

Do not promote shape-diversity .75 as the shared method: A25 worsens, pooled
MRR is slightly lower and output cost rises. Retain this explicit continuous
action and all failures/results for later controlled analysis. Do not change
the reference or old result status. Keep SEARCH34 as the additional24 anchor.
Next investigate a distinct evidence/solver mechanism, checking prior trials
before spending new calls. No full evaluation or training starts from this result.

Evidence: `paired_review.json`, `metrics_breakdown.json`, private full-answer
and coverage reviews, `qualification.json`, `runtime.json`, original raw and
partial responses, and `private/source_snapshot.tar.gz`. Source and public
input CPU audits are in the sibling `shape_diversity_gallery_v2` directory.

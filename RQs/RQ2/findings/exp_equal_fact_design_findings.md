# `exp_equal_fact_design` findings

Status: complete and verified. The development run contains 5,760 trajectories
and the independent run contains 4,800 trajectories. Infrastructure error rate
is 0 in both. Parse rates are 0.9896 and 0.9881, respectively; parse failures
remain scored model-output failures rather than being retried.

## What was tested

The experiment changed dashboard encoding, spatial layout, ordering, density,
resolution, typography and related design factors while holding the visible
evidence facts fixed. `Dxxx` is an opaque design-cell ID, not a quality rank.
The 60-case development set selected one fixed dashboard, `D006`, before the
150-case independent results were examined.

`D006` uses a 10×10 modality-grouped grid, 256-pixel cells, small-multiple
metric lines, a directed node-link topology, stable anonymous-ID ordering,
balanced card footprints and the canonical visual skin. Development macro MRR
was 0.2944. `D037` was numerically higher at 0.2979, but the preregistered
within-0.01 tie-break selected `D006` because its mean input cost was lower
(8,147.5 versus about 9,984 tokens across the two model tokenizers).

## Independent result

| Model | `D006` MRR | Best observed fixed cell | Best-cell MRR |
|---|---:|---|---:|
| Gemma-4-26B-A4B-it | 0.2017 | `D021` | 0.2533 |
| Qwen3.8-27B | 0.2400 | `D031` | 0.2433 |

The selected design generalized closely to Qwen's best fixed cell, but not to
Gemma's. No registered development main effect survived Holm correction; all
adjusted p-values were 1.0. The largest positive descriptive effects were the
detailed footprint policy (+0.0504 MRR), edge-table topology (+0.0273),
entity-grouped layout (+0.0262), and metric-line encoding (+0.0223). These are
hypothesis-generating observations, not confirmed causal recommendations.

The independent observed-outcome oracle gaps are large: 0.200/0.200/0.213 for
Gemma and 0.190/0.208/0.222 for Qwen on AegisLab/AIOPS-2022/AIOPS-2025. This
oracle assigns each case the design that already happened to score best, so it
is deliberately optimistic and is not a deployable selector. It nevertheless
shows that a single fixed dashboard leaves substantial case-dependent
headroom.

## Interpretation

There is no evidence that one fixed redesign reliably improves RCA across both
models. Dashboard design matters at the case level, but the preferred design
is model- and incident-dependent. The result supports studying identifiable
component contributions and, later, an out-of-sample adaptive selector; it does
not justify deploying `D006` as a universal best dashboard.
# Abandoned / superseded by RQ2.1 — 2026-09-07

The historical numerical findings below are preserved. This experiment is no
longer executable or a successor-selection authority. See
[RQ2 retirement audit](exp_retirement_audit_findings.md) for validity limits,
known implementation pitfalls and generated-artifact retirement.

# `direct_qa` findings

Status: **final inference, visibility-aware post-hoc rescoring, and the
visibility-clean 96-case L4 successor are complete**. The unified L1–L4
artifact is the result authority. RQ1.1 remains exploratory rather than an
untouched confirmation.

## Final visibility-qualified result

The final scorer does not rerun a model or rewrite any trajectory. It excludes
one paired `case + query` group from both models and all conditions when its
complete answer is not visually recoverable. Of 1,141 positive-support
questions, 381 are excluded: 117 require a metric label elided by the actual
renderer and 296 request a TRC-L `entry_index` absent from the canvas; the
reasons overlap. The retained denominators are L1=426, L2=214, L3=96 and
L4=24. Every retained question has all expected paired arms for both models,
giving 3,752 records per model.

T, S and ContextV use high-precision text gold; V and PathV use gold generated
from the renderer's displayed precision. Old entity-only questions accept all
visibly permitted rows. The scorer also accepts deterministic formatting,
numeric-notation, missing-value, direction, set/list and topology-marker
equivalences. It repairs 812 semantic-v1 complete-chain failures. It also
breaks 79 semantic-v1 passes because the old single gold sometimes contradicted
the public row-selection wording; the old scores remain available as audit
views rather than being overwritten.

Visibility-aware complete-chain case-macro accuracy is:

| Model | Scope | T | V | S | PathV | ContextV |
|---|---|---:|---:|---:|---:|---:|
| Qwen3.8 | L1 | 53.29% | 56.34% | 8.69% | 61.97% | 53.05% |
| Qwen3.8 | L2 | 42.93% | 26.96% | 6.02% | 38.48% | 43.46% |
| Qwen3.8 | L3 | 31.76% | 16.47% | 2.35% | 22.35% | 29.41% |
| Qwen3.8 | L4 | 4.17% | 8.33% | 4.17% | — | — |
| Gemma | L1 | 51.17% | 33.57% | 0.47% | 61.74% | 53.99% |
| Gemma | L2 | 32.98% | 14.66% | 0.00% | 22.77% | 37.96% |
| Gemma | L3 | 18.24% | 5.88% | 0.00% | 1.76% | 25.88% |
| Gemma | L4 | 8.33% | 0.00% | 0.00% | — | — |

The revision materially changes the magnitude but not the central mechanism.
PathV is competitive with T at Qwen L2 (−0.0445, Holm-adjusted `p=0.5983`),
and required-region vision improves L1 for both models. Nevertheless, full V
remains below T on L2–L3: Qwen `−0.1956` (`p=8.18e-06`) and Gemma `−0.1832`
(`p=2.15e-07`). ContextV remains approximately neutral for Qwen (`+0.0034`,
`p=0.984`) and positive for Gemma (`+0.0570`, `p=0.0128`). S remains a poor
transport control. Vision therefore helps direct and selectively routed
perception, but the complete dashboard still weakens multi-region composition.

These results are exploratory and post-hoc. Exclusion destroys the extension's
original exact path balance: retained L2 paths contain 6–28 questions, L3
contains 19 of 24 paths with 1–9 questions, and L4 contains only 24 questions
over 16 paths. Path-stratified tables and actual denominators are mandatory;
L4 is descriptive only.

Authoritative report and machine-readable artifacts:

`RQs/RQ1_1/results/rq1_1_direct_qa_final_rescore_20260829/l1_l3_visibility_aware_v2/`

## Final visibility-clean L4 successor result

The existing visibility-qualified L4 denominator is only 24. A new
response-blind manifest retains those 24 questions and adds 72 clean questions
so the future combined L4 corpus has 96 unique cases and exactly four
questions for each of the 24 ordered M/R/L/G paths. Static qualification found
zero metric-name elisions, zero references to unprinted indices or
representation-specific row/edge positions, zero literal missing answers,
and zero absent required visual fields among the additions. Trace questions
use unique displayed count/baseline-ExL content anchors; topology questions
use explicit displayed caller-to-callee edges. Manifest SHA256:
`8e992ed2c795f97477ad6db3e38e594914c97b3e188769f9f18c3ae5af50a1fb`.

An initial partial launch exposed a display-order mismatch and was stopped;
those partial trajectories are archived as invalid development evidence and
are excluded. The corrected successor completed 216/216 calls per model (72
questions × T/V/S), with zero infrastructure errors and zero truncations in
the new records. Qwen had 6 strict output/region-order failures (2.78%); Gemma
had none.

After merging the 72 successor cases with the 24 retained cases, the final L4
corpus contains 96 unique cases, exactly four for each of the 24 ordered paths.
Visibility-aware complete-chain accuracy is:

| Model | T: all text | V: real dashboard | S: text screenshot |
|---|---:|---:|---:|
| Qwen3.8-27B | 0.1667 | 0.1042 | 0.0104 |
| Gemma-4-26B-A4B-it | 0.0729 | 0.0104 | 0.0000 |

For Qwen, `V−T=-0.0625` (`Holm p=0.2207`) and `S−T=-0.1563`
(`Holm p=0.00055`). For Gemma, `V−T=-0.0625` (`Holm p=0.0339`) and
`S−T=-0.0729` (`Holm p=0.0163`). The real dashboard therefore preserves much
more four-region perception than rendering serialized text as pixels, but it
does not outperform natural-language text on complete L4 chains. This is a
perception result, not an RCA metric.

The final paired analysis is under:

`RQs/RQ1_1/results/rq1_1_direct_qa_final_rescore_20260829/l4_96_visibility_aware_v1/`

The unified L1-L4 report and machine-readable tables are under:

`RQs/RQ1_1/results/rq1_1_direct_qa_final_rescore_20260829/unified_l1_l4_visibility_aware_v1/`

This unified artifact reruns the same deterministic visibility-aware scorer
over all retained trajectories and replaces the split reporting layout. Final
eligible denominators are L1=426 questions, L2=214, L3=96 and L4=96. Unified
`summary.json` SHA256:
`44739c5f3b8c015fcc149cb965131b1151b44d75521f70a24cf430f4ebce8bb6`.
Qwen L4-V has 7/96 strict output/region-order parse failures, below the 0.95
parse-rate requirement; that cell remains exploratory and cannot by itself
support a formal positive claim.

Analysis summary SHA256:
`115d56fa9cf77a0f9d90c87f9699b14e9aac0ad7f043a31b3ebb0464af96d6c9`.

## Root-connected call-graph QA versus RCA

A post-hoc, model-free analysis isolated questions containing a topology step
whose registered displayed `caller -> callee` support touched the accepted
root service family. This is a root-connected **call-graph proxy**, not a
verified causal propagation path: RQ1.1 has root labels and displayed directed
edges, but no ground-truth propagation-chain annotation.

On the three headline datasets, case-level QA accuracy did not show a stable
positive relationship with the paired RCA reciprocal rank. For the broad
root-connected subset (`54` cases per model), Spearman correlation was
`-0.154` for Qwen (`p=0.266`) and `+0.136` for Gemma (`p=0.328`). Correlation
between representation-induced changes in QA and changes in RCA was `+0.152`
for Qwen (`p=0.272`) and `-0.088` for Gemma (`p=0.528`). Within cases that had
both correct and wrong QA observations, mean `RR(correct)-RR(wrong)` was
`-0.031` for Qwen (`n=31`, Pratt-Wilcoxon `p=0.460`) and `+0.003` for Gemma
(`n=24`, `p=0.871`).

The strict multi-region L2-L4 subset had only `17` headline cases, disagreed in
sign across models, and also produced no reliable change-score association.
The defensible finding is therefore narrow: **accuracy on the available
root-connected call-graph questions was not a stable positive case-level proxy
for one-stage RCA performance.** It does not prove that true causal-chain
perception is irrelevant to RCA. Full tables and source hashes are under
`tmp/rq1_1_root_chain_analysis/`.

## Earlier semantic-v1 audit view

The remainder of this file preserves the earlier all-positive-support
semantic-v1 result for audit. Its absolute visual scores are superseded by the
visibility-aware result above; it must not be quoted as the final QA estimate.

## What was combined

The immutable frozen questions contribute 469 L1, 135 L2, 53 L3 and 24 L4
all-positive-support questions. The response-blind successor contributes 201
L2, 163 L3 and 96 L4 questions. The final cross-region corpus is exactly
balanced over ordered region paths:

- L2: 28 questions for each of 12 paths, 336 total over 311 cases;
- L3: 9 questions for each of 24 paths, 216 total over 170 cases;
- L4: 5 questions for each of 24 paths, 120 total over 109 cases.

Both Qwen3.8 and Gemma have all 5,465 expected L1–L4 representation records.
Every selected source record passed its stored SHA256 check, the two models
use the same question/condition keys, and no selected record is an
infrastructure-error placeholder. Repeated questions from a case are averaged
within case before inference.

The registered strict score remains immutable. The separately reported
semantic sensitivity score is deterministic and accepts only presentation
equivalences: displayed numeric notation, missing aliases, direction aliases,
set/list formatting and the frozen terminal-topology marker mismatch. It uses
no model judge and repaired 736 strict failures with zero strict-pass breaks.

## Main results

Semantic complete-chain case-macro accuracy:

| Model | Scope | T | V | S | PathV | ContextV |
|---|---|---:|---:|---:|---:|---:|
| Qwen3.8 | L2 | 47.59% | 3.38% | 4.98% | 5.95% | 48.07% |
| Qwen3.8 | L3 | 32.65% | 1.18% | 2.94% | 1.18% | 32.65% |
| Qwen3.8 | L4 | 23.85% | 0.00% | 0.46% | — | — |
| Gemma | L2 | 39.39% | 1.61% | 0.00% | 2.25% | 44.21% |
| Gemma | L3 | 16.18% | 0.00% | 0.00% | 0.00% | 22.06% |
| Gemma | L4 | 12.39% | 0.00% | 0.00% | — | — |

For L2–L4, V−T is −0.4398 for Qwen and −0.3372 for Gemma, with
Holm-adjusted paired Wilcoxon p-values `4.11e-39` and `1.48e-32`. S is also
substantially below T. The current all-visual dashboard and pixel-text
screenshot are therefore not adequate substitutes for textual evidence in
positive multi-region composition.

This does **not** imply that every visual region is useless. At L1, Qwen's
direct topology score is 52.00% under V versus 22.40% under T; its PathV log
score is 81.75% versus 78.57%. Gemma's PathV topology score is 39.20% versus
31.20%. Metrics and traces are much weaker visually. The decisive bottleneck
is composing required facts from pixels across regions, not merely accepting
an image in the prompt.

ContextV supports that mechanism. It keeps required regions textual while
visualizing irrelevant context. On L2–L3 it is statistically indistinguishable
from T for Qwen (45.91% versus 46.14%, adjusted `p=0.762`) and is higher for
Gemma (40.63% versus 35.51%, delta `+0.0512`, adjusted `p=0.00632`). Thus the
large V/PathV loss occurs when needed evidence must be read visually, rather
than from image presence alone.

The token tradeoff is also representation-specific. On L2–L3, V reduces mean
input tokens relative to T by 69.23% for Qwen and 78.49% for Gemma, but its
semantic accuracy collapses to 2.72% and 1.09%; this is harmful compression.
ContextV reduces tokens by 15.15% and 23.95% while preserving or improving
accuracy, making selective compression of irrelevant context the only current
perception Pareto candidate. Absolute token counts are not compared across
models because their tokenizers and visual processors differ.

## Limits and source sensitivity

This is conditional accuracy on questions whose full gold chain has visible
support; it is neither an unconditional 469-case accuracy nor an RCA metric.
The balanced extension uses explicit positive anchors and is easier than many
frozen hash-selected questions—for example, Qwen semantic T on L2 is 61.19%
for extension questions versus 25.93% for frozen questions. The merged corpus
is correctly path-balanced, but absolute performance mixes two question
construction generations. T/ContextV remain strongest and V/S/PathV remain
weak in both source strata.

Full report and machine-readable tables:

`RQs/RQ1_1/results/rq1_1_v12_direct_qa_balanced_positive_extension_20260829/analysis/combined_final_positive_qa/`

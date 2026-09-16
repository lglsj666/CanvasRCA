# DD-RQ3-SEARCH-37 — Soft within-owner shape diversity

2026-09-12; adopted for bounded training-only exploration, before new calls.
Reference: SEARCH34 native24, on the same additional24 cases (12 per AIOPS
dataset), not SEARCH36's axis-floor variant. No validation/eval or training.

## Evidence and decision

A public-only audit of the native24 plots finds 2–14 lanes per case with a
same-owner earlier lane at Pearson correlation >=.95. Require at least eight
common finite bins and overlap >=80% of the more-observed series. For example,
error/client_error and their ratios repeat highly similar shapes. Different
names/units can still supply different diagnostic meaning: correlation is a
redundancy proxy, not semantic equivalence or permission to erase evidence.
SEARCH35's compulsory owner coverage hurt both datasets. Instead test a soft
trade-off, preserving the opportunity to show several signals from one owner.

Use native order over the full public pool. Relevance at zero-based position i
is 1/log2(i+2). Iteratively select the largest
`lambda * relevance - (1-lambda) * max_similarity_to_selected`.
First registered lambda=.75; the continuous allowed interval is [0,1].
At lambda=1 the selected sequence must exactly recover native top-k.
Ties use native order (already rank/fact-ID deterministic).

Similarity is zero across owners. Within an owner, use simultaneous existing
64-bin values, without interpolation, zero fill, or time shifting. Insufficient
overlap gives zero similarity. After positive Pearson correlation r,
similarity=clip((r-.95)/.05,0,1). Distinct constants are not duplicates; exactly
equal constant values with identical finite masks may receive similarity one.
Anti-correlated series are not duplicates. Normalize before arithmetic to avoid
overflow. Reject malformed/non-finite source numbers rather than invent zeros.

Keep24 metric slots, native renderer/axes, static prompt, candidate set/order,
trace/log selection, source timestamps, projections, request and scorer.
Existing selected-entity G/onset/membership rules may change downstream facts.
This is a selection-policy experiment, not equal information with native24.
All retained source facts remain intact. Scores, witnesses and selection steps
are CPU-side audit only; do not present them as a root recommendation.

## Literature and boundaries

Carbonell and Goldstein, *The Use of MMR, Diversity-Based Reranking for
Reordering Documents and Producing Summaries*, SIGIR1998, author-hosted
[two-page paper](https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf).
Read abstract, introduction, formula, retrieval/summarization evaluations and
conclusion on2026-09-12. Its tunable relevance/novelty criterion is transferable;
its five-user pilot and text-summary results do not establish telemetry/RCA
benefit. Summary lengths differed in one evaluation. This is a project-owned
MMR-inspired selector, not a reproduction of that text retrieval system.

Revisited Sieve's metric-reduction method and threshold-sensitivity discussion;
the complete earlier reading is in [its source record](RQ3_Sieve_review_20260912.md).
It motivates examining same-component shape redundancy, but uses k-Shape,
controlled loads, lag matching and spline reconstruction, unlike this adapter.
Do not claim Sieve reproduction, infer physical causality from correlation, or
transfer its efficiency numbers to our downstream VLM.

MetricSifter was screened via its official repository during this search.
Full paper and source algorithms have not been reviewed; no implementation or
performance claim is adopted from it in SEARCH37.

## Checks and run

Keep panel-selection math in the existing RQ3-local kpi_select module, which
already owns native panel rankings; the five-module search dispatcher only
binds public data and config. Renderer drawing behavior must remain unchanged.
CPU cover lambda bounds, native endpoint, ties, sparse/empty/constant/huge bins,
positive/negative correlation, owner isolation, immutable input, exact count,
determinism and a constructed real selection difference. Audit all24 source
packets, projection, static prompts, true primitive binding, and native PNG
replay. Inspect three real dense/sparse images before calls. Save source/config
snapshot and all actual selected inputs. Preserve failures, never resample for
correctness. Exact full-input no-ops may reference existing responses.

At most24 new local Qwen calls, concurrency4,3600-second bounded development
batch. No attention, Composer, raw-data regeneration, new SFT/RL or eval.
Report paired MRR/AC/AVG, input/output tokens, repair/break/tie, all full answers,
selection/rank/overlap changes and evaluator-private coverage. One exploratory
two-dataset Pratt-Wilcoxon/dz/Holm family; no small-sample promotion claim.

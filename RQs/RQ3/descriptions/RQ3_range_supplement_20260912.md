# DD-RQ3-SEARCH-29 — Coverage bottleneck and range-complement prototype

Date: 2026-09-12. Status: CPU prototype rejected for advancement; zero model calls.

## CPU outcome and rejection

The 24 training-case probe added 12 metrics per case. All 288 selected range
ratios were exactly 1.0: a zero lower quantile and positive upper quantile
saturate this formula. The proposed new ranking therefore mostly reduced to
its coverage/native-rank tie breakers. Do not advance this version to GPU or
describe it as a discriminative anomaly score. Keep its code and artifacts.
Direct-root-associated coverage changed from 10 to 11 of 12 A22 cases and
from 9 to 10 of 12 A25 cases. This is private offline coverage, not an RCA gain.

The initial CPU run rejected valid numeric strings in the canonical series.
A strict numeric-string parser fixed that schema mismatch without filling
missing bins; overflow-safe quantiles and 16 unit tests passed. The saturation
is a method limitation, not evidence that those observed zeros are missing.
Artifacts: `../results/search_first_v1/range_supplement_cpu_v1/`;
prototype/test: `../scripts/probe_range_supplement.py` and
`../scripts/test_range_supplement.py`. Revisit only with a separately defined
score that passes nondegeneracy and semantic checks; do not overwrite this run.

## Evidence and decision
SEARCH28 did not improve either dataset. Offline inspection of the SEARCH23
24-case training anchor finds all24 have accepted candidates and direct-root-
associated M/R/L telemetry in the full public pool. Direct association survives
selection in10/12 A22 and9/12 A25. Five cases lack it entirely. Root association
is not causal sufficiency; indirect evidence may still support a diagnosis.
The private audit never becomes a selector input. Native-rank-only supplementation
of12 uncovered metric owners would cover two of the five omissions but not the
other three. This is CPU feedback, not measured RCA improvement.

Prototype a public-only complementary selection rule before spending more GPU
calls. Preserve every reference selected fact and add at most12 resource/latency
series. Use the existing public resource-family classifier. For each full-pool
metric with at least8 finite displayed bins, compute linear-interpolated q05 and
q95 on those observed bins and `(q95-q05)/(abs(q95)+abs(q05))`, zero if the
denominator is zero. This dimensionless within-series range is not a fault
probability. Do not fill absent bins, re-anchor time or reinterpret units.

Exclude the classifier's `other` family from supplements, not from the existing
anchor. Select deterministically, preferring unrepresented `(owner,family)`
pairs, then greater range ratio, native rank and fact ID; add only positive-range
series, at most one new series per owner/family pair. Added facts retain exact
payloads; R/L/G, existing metadata, candidates and source corpus stay unchanged.
No new selection score enters a Solver prompt or image. Quantiles use the
existing displayed projection; this does not claim raw-sample quantile precision.

This is a project-owned heuristic, not Sieve or BARO reproduction. It can still
favor ordinary load changes and lose a short burst in the quantiles. Source
inspection, deterministic/constant/NaN/scaling tests, root-associated coverage,
native anchor retention and CPU rendering feasibility decide whether to advance
the prototype, not whether it has already met an MRR target. Any subsequent
live comparison gets a registered config, pixel review and bounded train batch.
No validation/eval/SFT/RL and no candidate pruning in this prototype.

## Literature screening, not an imported algorithm
Question: can representative selection retain informative variation without
letting redundant high-z metrics occupy the limited visual budget?
Queries included Sieve microservices metric reduction and RCA metric selection.
Primary sources checked on2026-09-12:
[Sieve project](https://sieve-microservices.github.io/),
[Middleware2017 paper](https://sieve-microservices.github.io/assets/sieve-middleware-2017.pdf),
[official clustering/Granger code](https://github.com/sieve-microservices/scalegraph-scripts).
Title: *Sieve: Actionable Insights from Monitored Metrics in Distributed Systems*;
Thalheim et al.; DOI10.1145/3135974.3135977. Project and paper identify Middleware2017.
Abstract/introduction and metric-reduction method screened; the entire evaluation
has not been read in this pass. Do not claim a full-paper replication assessment.
Sieve separates metric reduction and dependency extraction, using k-Shape and
controlled-load observations. We do not have its controlled-load experiment and
will not fabricate a causal graph or transfer its accuracy claims. The present
quantile-range supplement is independently defined above, not their k-Shape code.
Full paper/code review is required before any later Sieve component adaptation.
Follow-up: the main paper and repository README review are now completed in
[Sieve review](RQ3_Sieve_review_20260912.md); algorithm code and the extended
technical report remain unaudited. This does not promote the rejected prototype.

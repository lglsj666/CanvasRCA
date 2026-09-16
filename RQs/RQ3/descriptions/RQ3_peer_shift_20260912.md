# DD-RQ3-SEARCH-39 — Native anchor plus peer-relative evidence

2026-09-12 Toronto. Registered before calls; train-only development.

## Motivation and sources

SEARCH38 completed but is not promoted: MRR .423611→.433333 / .298611→.269444
on 12 cases per AIOPS dataset, with higher output cost. Keep the original
non-thinking profile. The complete answers repeatedly equate large deviations
and broadly shared symptoms with initiating faults.

Question: can evidence selection distinguish an unusually changing component
from similarly changing components without removing the strongest native facts?
Search scope: peer comparison and correlated-failure diagnosis, plus authoritative
metric-type semantics. Prefer primary methods, not product performance claims.

Pertet et al.'s **Fingerpointing Correlated Failures in Replicated Systems**
(authors: Soila Pertet, Rajeev Gandhi, Priya Narasimhan), SysML 2007 workshop,
compares local anomaly signatures across replicated nodes. Its method and
experiments show that asymmetric manifestations can help localization, while
shared packet-loss symptoms remain difficult. It used Spread/BFT, four replicas,
three injected fault types and heuristic/k-means/kNN comparisons—not VLMs,
microservice dashboards or our datasets. Full primary paper read, including
results and limitations. [Paper](https://www.usenix.org/legacy/event/sysml07/tech/full_papers/pertet/pertet_html/),
[author venue record](https://www.cs.cmu.edu/~priya/publications.html).

Our selector is a new, explicitly **inspired** adaptation, not its reproduced
algorithm or a literature-backed guarantee. Exact metric name/unit/granularity
does not guarantee interchangeable workload; diverse peers and simultaneous
faults can defeat it. No causal or health label is assigned by the selector.

Do not infer counter type from a suffix alone or blindly differentiate a source
series. Prometheus distinguishes monotonic counters from gauges and restricts
rate semantics accordingly. Our source lacks a trusted per-series counter/gauge
declaration, so no rate transformation is registered here.
[Metric types](https://prometheus.io/docs/concepts/metric_types/).

## Fixed algorithm

Use the complete public metric pool and unchanged public SIRCL pre/current
summary fields. Same-name, same-unit, same owner-granularity series form groups.
No labels, dataset identity, accepted IDs, hosting inference or absolute time.

For each series, compute the signed bounded own-baseline shift:

`u = (current_mean - regular_mean) / max(abs(current_mean)+abs(regular_mean), 2*regular_std_dev)`.

All-zero summaries have u=0. Missing/nonfinite/negative-spread summaries are
ineligible; they are not replaced with zero. The numeric calculation rescales
first to avoid intermediate overflow. Values are the existing public summaries,
not reconstructed unrounded data or a new analysis window.

Reduce duplicate observations of one owner to its median u. Require at least
two other distinct owners. Exclude the current owner, then compute:

`peer_residual = abs(u - median(other_owner_u)) / 2`.

Native ordinal i starts at 1 in the original rank/fact-ID ordering. Keep the
native first eight metric series. Fill the remaining sixteen slots by:

`priority = 0.5/sqrt(i) + 0.5*peer_residual`.

Ineligible peer comparisons retain `priority=1/sqrt(i)` rather than treating
unmeasured evidence as normal. Break ties by original native order. The
fallback deliberately protects singleton metric semantics; report its frequency.

Only selection changes. Original 64-bin values, labels, fields, candidate order,
R/L selection, typed-owner renderer, 3996×4088 capacity, trace projection,
prompt, non-thinking presence1.5 request and scorer stay unchanged. Existing
selected-entity G/onset/member rules can change their selected facts too; this
is a complete selection-policy intervention, not an equal-information claim.
New residuals/priorities remain CPU audit data and are not Solver root scores.

## Checks and run

Same SEARCH34 cohort C: 12 distinct training groups per AIOPS dataset, 24 calls,
four concurrent requests, 3600-second development bound, pure image diagnostic
evidence plus text candidates/guidance. No attention, new corpus, eval, SFT/RL.

CPU checks: old native selection and packet replay; formatted/invalid numbers;
own-baseline scale invariance; missing peers; duplicate-owner independence;
opposite changes; simultaneous shifts; immutable source facts; real selection
change under 24 slots; no context/renderer/scorer change. Inspect actual PNGs
for sparse/dense selected evidence and complete source/visible binding.

Freeze source, inputs and cohort before inference. Preserve all outcomes and
complete conversations. Report paired MRR/AC/AVG/input-output cost, peer
eligibility, selected-fact changes and evaluator-only root coverage; two
per-dataset Pratt/dz comparisons share one Holm family. If there is no joint
improvement, retain the negative result rather than selecting favorable cases.

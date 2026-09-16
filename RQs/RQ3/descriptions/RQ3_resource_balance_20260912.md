# DD-RQ3-SEARCH-18 — Public resource-balanced metric coverage

Date: 2026-09-12. Status: registered before implementation/live calls.

## Evidence and hypothesis

SEARCH-17 neither met the targets nor promoted a policy. A separate zero-call,
evaluator-private audit of the same twelve training cases found six with
root-associated public M/R/L facts in the pool but none directly selected.
This is a selection observation, not proof that showing a root guarantees RCA.
The audit and labels must never be read by the selector or renderer.

The inherited metric order ranks maximum baseline-standardized deviation;
capacity/counter changes and almost-flat baselines can occupy many top slots.
Test coverage of resource/latency families instead of global top-eight alone.
Preserve all native values, native ranking metadata, public analysis windows,
R/L selection, candidate inventory and the existing figure/prompt recipes.

## Fixed public rule

`resource_balance_v1` reserves eight metric slots in this order:
CPU node, CPU service/pod, memory node, memory service/pod, latency twice,
IO twice. Node versus workload comes from the existing public 4-digit versus
3/5-digit anonymous identity type, never from labels or candidate position.
CPU means utilization/load/throttling metrics, memory means used/available/
working-set/RSS/usage metrics, latency means RRT/latency/response-time metrics,
and IO means wait/queue/IO-utilization/raft-apply-wait/WAL-write metrics.
The versioned regex definitions are the executable ontology; they are a
project heuristic, not an assertion that every source metric is covered.

Within each slot use the unchanged native peak-ranking order. Prefer a new
entity within each repeated family before a second series of the same entity.
Empty slots are deferred; fill all unfilled capacity from original native
order after all reserved slots. Never duplicate a fact or invent a value.
Preserve eight total metrics when the pool has at least eight. This does not
ban excluded categories from the pool or fallback. Native MET-Z values and
scores are not recalculated or silently replaced by a new anomaly statistic.
Edges/onset/name-group context follows the existing public selected-entity
binding rule; its resulting changes are audited as part of this selector.

## Sources and interpretation

- [Brendan Gregg's USE Method](https://www.brendangregg.com/usemethod.html):
  primary practitioner source; inspect resource utilization, saturation and
  errors rather than assuming the largest arbitrary metric is causal.
- [Google SRE monitoring chapter](https://sre.google/sre-book/monitoring-distributed-systems/):
  primary systems guidance, including latency and saturation. It does not
  validate this eight-slot policy or establish RCA performance.
- The locally vendored SIRCL `metrics_ma.py` was inspected. Its current-mean
  versus baseline-standard-deviation statistic differs from the inherited
  maximum-deviation panel selector. Do not call our new coverage rule native
  SIRCL, BARO, or a paper-faithful algorithm reproduction.

## Bounded paired execution

Use the same twelve isolated train cases (six each AIOPS2022/2025), with
`ranked_membership_v1` control and `resource_balance_v1`: 24 calls maximum,
four concurrent, one-hour development supervisor. Same evidence-bound
membership prompt and services-first `card_nonthinking_v1`; BF16 frozen
checkpoint, 8,192 output ceiling, no attention. The complete candidate list
stays only in the prompt. One image contains all incident diagnostic evidence.

CPU qualification checks slot capacities, deterministic ties, absent classes,
small pools, immutability, primitive binding, candidate transport, unchanged
R/L, unchanged native numerical facts, two-model-independent public selection,
raw/partial/conversation persistence and resume. Open actual rendered PNGs
from both datasets before calls. Inspect every response afterwards. Compare
paired MRR and separate input/output tokens; no confidence intervals. Twelve
repeatedly explored train cases support only development decisions. If useful,
next test a broader train cohort and a validation shortlist, not immediate
full480 evaluation or SFT/RL. Preserve all prior attempts and shared defaults.

## Qualified for the bounded development batch

239 CPU regressions passed in 76.14 seconds; functional source count 5,939.
Independent review checked all 24 previews against original public pools.
All twelve changed metric sets and actual PNG pixels, retained numerical
facts and R/L, and kept candidates exclusively in prompt. Existing control
PNG bytes match SEARCH-17. Four new PNGs opened (C034, 303, 34F, 8AB):
readable chart/owner/axis structure, no candidate panel. Near-constant selected
series remain a declared limitation to measure, not a success claim.
Gallery summary hash:
`943abc4e92df1b75fc47b91013c607af465e8b93d346c8b18d8349782e90feac`.

## Completed — not promoted

24/24 completed in 240.705 seconds; zero RR repairs and three breaks.
A22 MRR .2222→.2083, A25 .3667→.1667. Input unchanged at fixed image size;
A22 output increased 244.3→334.2, A25 decreased 287.7→265.7. No schema,
transport or truncation error; all raw responses and persistent artifacts
reviewed. Both adjusted p-values are 1 on this exploratory small train set.
Root availability alone does not establish causal signal sufficiency; owner
and relationship misbinding persists. Preserve the control and negative
result. See `resource_balance_development_v1/paired_review.json` and its
`logs/20260912_review.md` for every paired case and the next safe step.

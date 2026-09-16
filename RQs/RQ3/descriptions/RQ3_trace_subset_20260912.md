# DD-RQ3-SEARCH-16 — Trace-centered modality subsets

Date: 2026-09-12. Status: CPU/visual-qualified train-only development, not promoted.

## Motivation and decision

The source-correct field dictionary in SEARCH-15 failed to improve MRR and
added 456 input tokens. Full answers still prioritized capacity/counter changes
over local trace latency and confused reporters with origin entities. Instead
of lengthening guidance further, directly test the authorized modality-subset
card family. This is an evidence-selection/composition intervention, not an
equal-information modality claim or proof that metrics are generally harmful.

Run the same twelve registered training cases, six per AIOPS dataset:

| Policy | Selected public evidence |
|---|---|
| trace_only_v1 | Up to eight trace operations, unchanged native TRC-L rank |
| trace_graph_v1 | Same traces plus six relevant exact call edges and public name groups |
| trace_logs_graph_v1 | Same traces, two native-ranked distinct log templates, relevant exact edges and name groups |

All three omit metric facts and the metric-derived onset summary. Graph edges
use the existing rank by number of endpoints in the selected diagnostic owners,
then native edge index and fact ID; adding logs can thus change the local graph
context. Name groups touch selected trace/log owners only. No host inference.
An empty trace pool fails explicitly rather than fabricating evidence or using
private labels. Fewer than eight eligible operations remain fewer than eight.
No renderer-side filtering. The same eight trace facts, source values, units,
candidates, model recipe and static guide are retained across the three arms.
The guide describes M/R/L/G conventions; only actual supplied panels constitute
incident evidence. Candidate arrays stay in the prompt, never in image panels.

One existing deterministic modality card per included region, same one-image
pixel budget and painter. Omitting cards gives the others more space via the
existing layout solver. Consequently this measures the whole deployable subset
policy, not a pure information-removal effect at fixed panel size. Relative to
the preceding full dashboard, trace capacity also changes four→eight. Report
that explicitly rather than assign a gain to deleting M alone.

## Qualification and scope

Thirty-six actual Solver calls maximum, concurrency four, one-hour bounded
development supervisor, same non-thinking profile. This is train exploration,
not a new logical formal smoke. No attention, Composer call, validation, eval,
SFT/RL, shared-model change or processed-data rewrite. All prior results remain.

CPU regressions must check candidates unchanged, no mutation, native top-eight
trace identity, absent M/onset facts, exact fact/primitive binding, real PNG
changes, complete conversation and partial-output persistence. Open representative
actual PNGs from both datasets before preparing live work. The pure log-wrap
test moves unchanged into its genuine renderer-owned test suite; selection and
training tests remain in the five-module core. Report all results and failures,
including unrenderable designs, without selecting cases by outcome.

The small repeatedly explored train subset cannot establish either dataset's
target or generalization. Any promising policy next needs broader train checks
and the registered validation shortlist before a frozen full-eval request.

## Qualification completed

229 CPU tests passed in 75.65 seconds. Source audit is 5,988 functional lines.
All 36 previews rendered; the independent source audit checked exact native
top-eight trace membership, unit projection, all selected visible primitives,
candidate preservation, identical text parts, no M/onset facts and three real
PNG interventions per case. Four actual PNGs were opened across all conditions
and both datasets. Review summary hash:
`c86e9a6a75607f2470aa5fb7a3d0ef0a664e8a4357ed038ee8378d39eb574371`.
Only the registered 36-call train-development batch may proceed.

## Completed — no subset promoted

All 36 calls completed without timeout, schema, transport or truncation error
in 297.441 seconds. A22 MRR is .1667 for R, RG and RLG; A25 is .3333, .3333
and .2500 respectively. The previous full control was .2222/.3667. Strong
trace cases can improve, while removing IO/raft evidence loses other correct
cases. Input tokens stay unchanged at fixed canvas size. Every raw response
was read; see `trace_subset_development_v1/logs/20260912_review.md` and its
paired review. No validation/eval/training advancement is justified yet.

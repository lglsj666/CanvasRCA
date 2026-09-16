# Selection/design attribution — not run

## Current qualification status — 2026-09-10

Clock-safe repair v3 passed eight calls in 287.64 seconds, with full sampled
input/output and PNG review. U00/U01/U11 and Text/Screenshot paths ran; U10
was retained as infeasible under its fixed footprint without dropping evidence.
The explicitly reused legal BASE program came from the reviewed learning-v3
smoke, not a trained policy or a substituted fresh failure. See
[manual review](../results/exp_selection_design_attribution_smoke_repair_v3/review.md).
All formal attribution outcomes remain unexecuted.

## Predecessor qualification — 2026-09-09

No formal attribution study has run. This inference smoke completed 9 calls
in 290 seconds, both roles, without infrastructure or schema errors. One BASE
program was drawable; one overflowed its log card and remained a failure.
The drawable case exercised U00/U10/U01/U11, Text and Screenshot; all facts,
pixels, raw responses, conversations and same-call attention were retained.
All seven Solver rankings missed the root: this is qualification on two
cases with sparse/untrained inputs, not a downstream-utility estimate.
Manual review found stale visual-guide prose, fixed after this attempt and
CPU-tested; the latest wording is not live-requalified. See
[full coverage and examples](../descriptions/RQ3_qualification_20260909.md).

The material below is the earlier pre-smoke state, retained as history.

CPU tests cover portable selection/design replacement, the additive 2×2
decomposition and real pixel changes under raster interventions. No Solver
counterfactual outcomes or attention-based conclusions are available.

The approved attribution budget and reference conditions are registered in
`../descriptions/RQ3_experiments.md`. Full Canvas/Text/Screenshot semantic
qualification and local-control execution remain prerequisites, not assumed
successes. No causal or training benefit is claimed from the unit tests.

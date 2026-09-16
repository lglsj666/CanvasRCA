# DD-SEARCH-13 — Public hosting support and explicit trace axes

Date: 2026-09-12. Status: implemented successor under CPU qualification; no
model calls or efficacy claim at registration. Source: the twelve fixed train
cases in `search_first_v1/selection_gallery_v2/cohort.json`.

## Decision and evidence

The full low-thinking trace review found repeated guesses about node/pod
ownership and mistaken interpretation of horizontal trace position. All twelve
public cases contain node→pod metadata, but the selected diagrams contained no
hosting facts. Identity v2 corrects public master-node typing first. Preserve
the previous source corpus, pools, requests, responses and default recipes.

Compile every public hosting relation as a distinct typed G fact. A hosting
relation is not a call edge or a fault propagation claim. Register two paired
conditions: `ranked_v1` (same prior evidence selection) and `ranked_hosting_v1`
(same selection plus all public hosting relations). Both use identity v2 and
the same new labeled trace-latency axis. The common reading guide explains both
grammars conditionally. No model is told a selector or a preferred answer.

Candidates remain complete prompt text; image entity IDs belong to actual
telemetry or deployment facts, not an exhaustive candidate-list panel. The
hosting condition does add information, so it is not an equal-information
modality comparison. All other selected facts, candidate ordering, prompts,
sampling and trace-axis policy must match across the pair.

Trace values and source time are unchanged. The new painter explicitly labels
the horizontal log(1+latency) axis in milliseconds, shows baseline/current
colors and values, and never uses horizontal trace position as time. It cannot
drop rows to fit. Mixed G space changes to accommodate deployment; this is a
combined hosting-support intervention, not an isolated pixel-layout claim.

## Implementation and checks

The generic existing epoch-gauge projector is extracted unchanged into
`vlmrca.metric_calendar`; RQ3 retains column-owner binding. This removes generic
clock arithmetic from the constrained five-module experiment implementation;
no selection/training logic is moved outside that boundary. Source contracts
include the helper. Original source-clock CPU tests must still pass.

Validate public node/pod roles, no labels, candidate text-only, all selected
hosting facts painted, call direction unchanged, exact pairing of non-hosting
facts, deterministic PNGs, legible trace ticks, no clipping/overlap, source
hashes, and safe resumed preparation. Read actual previews before model calls.

After CPU and PNG qualification, allow at most 24 non-thinking Qwen Solver
calls: 12 train cases × 2 conditions, four requests in flight, 3,600-second
batch limit. No new attention, validation, eval, SFT or RL. Record every attempt
and all existing shared runtime checks; do not retry model mistakes. Compare
per-case RR and input/output tokens to each other; older profile numbers are
background, because identity and trace grammar changed.

This step does not yet solve the separate metric-selection dominance by
constant/capacity gauges or aggregate repeated log evidence across time. Those
remain subsequent development questions, not secretly changed in this pair.

## CPU qualification update

`cpu_hosting_axis_v2.xml`: 222 tests passed in 78.68 seconds, source audit
5,992 functional lines. The first run retained 220 passes and two test failures:
its test module had been loaded before trace-point geometry changed from scalar
x fields to scalable point objects; a fresh complete run verified the aligned
code. Do not treat the first run as passed.

All twelve isolated training pools completed using four separate physical cores
(0/2/4/6). Native completed-resume verified all twelve in 7.607 seconds without
recompiling any case. Explicit cohort truncation and stale non-hosting pool
use were rejected before rendering/model calls. Artifacts remain in
`search_first_v1/hosting_axis_pools_v1` and the two negative-check directories.

## Completed live development — not promoted

All 24 requests finished normally in 237.897 seconds under the checked local
non-thinking profile. Same case/condition prompt candidates remain text-only;
no attention was collected. No hosting vs all hosting MRR: A22 0.3333→0.2500,
A25 0.2500→0.0556. Zero RR repairs, three breaks, nine ties. Input tokens were
identical within pairs; output changed 269.0→277.7 and 280.2→249.3 respectively.

All 24 responses were manually read. New hosting facts are correctly bound and
visible, but several responses claim co-location contrary to the actual ledger.
Small capacity/usage shifts continue to be called saturation. The all-hosting
condition is not adopted as the main pipeline. Preserve the capability and
results; next target diagnostic contrast and value/owner interpretation, not
additional exhaustive metadata. Full audit and per-case notes:
`search_first_v1/hosting_axis_development_v1/logs/20260912_review.md`.

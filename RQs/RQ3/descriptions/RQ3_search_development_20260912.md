# RQ3 search development batch 1 — 2026-09-12

Completion: 72 calls, no infrastructure failures, all stop-terminated; two
invalid-entity model outputs remain zero-scored. Full results and review:
`../results/search_first_v1/selection_development_v1/`. Do not promote this
small train result into a validated policy. DD-RQ3-SEARCH-5 adopts continued
search, not SFT/RL: peak/onset heuristics and the static grounding addition did
not reliably solve evidence loss or incorrect entity/relationship reading.
Candidate lists stay in prompt text. No new attention was captured.

DD-RQ3-SEARCH-4. This is train-only development after the completed eight-call
four-family live qualification, not another nominal smoke or final evaluation.
The active search-first user instruction supersedes the old format-only path.
No attention, training, eval, model-weight or shared inference changes.

## Cohort and design

Choose six registered train cases per AIOPS dataset (12 total) using SHA256
seed 42 and opaque ID, preferring an as-yet-unrepresented source table and
requiring a distinct connected leakage group. Register identities before
reading any scores. This modest source-balanced sample does not establish
full-population performance. All selected cases must have their existing
full-pool preparation; never substitute cases based on outcome or rendering.

Three explicit public selection policies, crossed with two static prompts:

- `ranked_v1`: first eight metrics by inherited peak-deviation rank.
- `coverage_v1`: prefer a new metric entity, then new metric family, then
  inherited rank. This can deliberately include a normal comparison entity.
- `local_contrast_v1`: prefer not-yet-covered entities from the four strongest
  available TRC-L operations, then a new resource/latency-related metric family,
  then native MET-Z mean-shift magnitude and inherited rank. Missing/nonfinite
  mean-shift ranks as zero; this is a project policy, not a claimed SIRCL replica.

All three retain up to four TRC-L entries, two distinct entity/template log
rows (diagnostic-keyword first, LOG-R score, event count, stable fact ID), six
concrete call edges prioritizing selected endpoints, and four public metric
onset rows prioritizing selected entities. Numeric-log summary v1 is explicit
and unchanged. Counts can be lower when the public pool has fewer candidates.
This batch does not add deployment edges or fabricate them from identifier shape.

The two prompts are `inherited_v1` and `grounded_v1`. The latter appends a
static explanation of exclusive versus inclusive latency, resource-spike
interpretation, ordinary request logs, and the prohibition on invented edges
or interval comparisons. It does not contain case-specific diagnosis or labels.
Each pair shares exactly the same PNG. Both retain the frozen top-five JSON
schema, scorer, 8192 output cap, and unchanged current Solver recipe.

Only selected diagnostic facts are painted in one image. The full public
candidate list appears exclusively in prompt text, not as a list in the image.
This is a modality-card batch using per-series raw axes, measured card capacity,
and an 8×8 base canvas. No layout search is implied by this batch.

Maximum 72 new local Solver calls, concurrency 4, bounded to one hour including
startup/drain. Durable request keys, preserved raw/partial responses, complete
conversations and old results remain mandatory. No correctness-based retries.
If the deadline is reached, completed work remains resumable; do not call
partial development coverage a completed experiment. Inspect PNGs and input
integrity before committing the batch; failures are retained, not omitted.

## Implementation retirement

The completed predecessor `preview`, `smoke_worker` and `qualify_storage`
helpers are archived verbatim in
`results/search_first_v1/predecessor_qualification_helpers.py.txt` and active
entry points now fail closed. They were tied to the retired qualification
supervisor, old catalog and old text/attention controls. Their completed
artifacts remain unchanged. The actual SFT/RLOO functions/checkpoints and the
new search route remain implemented; this is not a placeholder replacement
for training. The retirement removes an obsolete alternate execution path
within the six-thousand-line module boundary.

The CPU regression found that `qualification_reference` is still independently
tested as a historical input-identity validator. Its archived original body was
restored unchanged; keeping that validator does not reactivate the supervisor.
The first full regression (149 passed, one retirement mismatch) is retained.

Before any model call, visual review of the first gallery found a redundant
LOG-R mini-chart intruding on the time-axis footer when its log text was long.
The new `capacity_safe` option reserves height for two bar rows and their labels;
if that redundant chart cannot fit, its already-visible textual rates remain.
Old default rendering is unchanged. The incomplete first gallery is preserved,
not approved for inference; new images use a separate versioned directory.

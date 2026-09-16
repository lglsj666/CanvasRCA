# DD-RQ3-SEARCH-17 — Public trace-strength routing and output-field order

Date: 2026-09-12. Status: registered, awaiting CPU/image checks and development.

SEARCH-16 repaired two trace-latency cases but lost two IO/raft cases when M
was removed universally. Some raw answers also revised their preferred origin
inside `reason` after already emitting a different first `services` item.
These are training observations, not proof of either mechanism. Test two
explicit factors on the same twelve source/group-balanced training cases.

## Fixed rules before calls

Evidence factor:

- `ranked_membership_v1`: existing complete M/R/L/G control, unchanged.
- `trace_strength_route_v1`: inspect the eight highest native TRC-L ranked
  operations; if any has native `latency_lfc >= 3` (approximately eightfold
  local latency after the native smoothing) and at least twenty observed spans
  in BOTH periods, use existing `trace_only_v1`; otherwise use the complete
  `ranked_membership_v1`. An empty trace pool therefore keeps the complete
  baseline. This is a heuristic, not a significance test or asserted physical
  fault detector. Native summaries and their time split are not recomputed.
  The rule is dimensionless and does not mistake the historical raw trace
  microsecond payloads for milliseconds. Display still uses the separately
  qualified source-unit projection. Audit both the rule and actual route.

Output factor:

- Existing `evidence_bound_membership_v1` / `card_nonthinking_v1`.
- `evidence_reason_first_v1` / `card_nonthinking_reason_first_v1`: same task,
  guide, candidate list, image and sampling; only change the example/required
  JSON field order to reason, services, confidence. Request the same brief
  evidence summary, NOT a free-form chain of thought or longer analysis. The
  response schema has identical field meanings/constraints; its ordered
  properties and required-field list are changed together. Preserve actual raw
  emission order and check whether the server honors it. Shared schema,
  scorer, model checkpoint and default runtime configuration remain untouched.

Forty-eight calls maximum, four concurrent, one-hour development supervisor.
Full/routed conditions that produce the same input are registered sampled
replicates, not independent cases or new evidence manipulations; retain both
results to expose stochastic variation. Do not select the better replicate.
Report full/routed and output-order contrasts separately and their interaction.
Do not treat post-hoc route-matched previous scores as a new policy evaluation.

## Checks and boundaries

Test strong/weak/low-count/empty traces and source immutability, selected-child
policy equality, no private fields in the route, candidate prompt-only delivery,
one image, unchanged facts/pixels between output orders, identical effective
sampling and different durable request fingerprints. Test interrupted/resumed
requests and raw/partial/conversation persistence through the existing suite.
Inspect both routed and retained-M actual PNGs before calls. Existing native
processor/cache/resume CPU tests belong under shared `tests/`, not the RQ3 core;
move their bodies unchanged and retain them in the full regression invocation.

No validation/eval, Composer, SFT, RL or attention. Twelve repeatedly exposed
train cases cannot establish the targets. Any useful result must next survive
a broader train check and the registered validation shortlist. Preserve every
old artifact and avoid changing the source corpus or earlier RQs.

## Pre-live qualification

238 full CPU regressions passed in 76.17 seconds. Six shared May-processor test
instances moved to `tests/test_raw_aiops_may.py`; extracted test/fixture bodies
are byte-identical and all remained in the executed regression command. Core
source count is 5,893. All 48 previews passed independent source, candidate,
fact/primitive, exact child-PNG and prompt-order checks. Four actual PNGs opened
across both datasets, including retained-M and trace-only routes. Five of twelve
cases route to R; seven retain full M/R/L/G. No outcome-based route override.
Gallery summary hash:
`e64bf10b1d1230204d20561fdd14b74942caa1ae70a9e1e2bd91e7063d6a2d36`.
The first review script invocation preceded gallery completion and found no
summary; it spent zero calls. Retried only after the same gallery handle exited.

## Completed — not promoted

48/48 calls completed in 335.025 seconds. All actual field orders matched the
registered factors, no errors/truncation, longest output 343 tokens. Full vs
routed services-first MRR: A22 .2222→.1667, A25 .3667→.5000. Reason-first
reduced full MRR to .0556/.2083 and routed MRR to .1667/.3333. All raw answers
and persisted input/partial/usage/candidate artifacts checked. Useful trace
cases improve, but the public trigger also discards decisive IO evidence for
a node fault. Neither intervention becomes the default; next investigate
metric evidence semantics/selection and attention-free visual emphasis while
retaining complementary signals. See `signal_routing_development_v1/RESULT.md`,
`paired_review.json` and `logs/20260912_review.md`. No target is achieved.

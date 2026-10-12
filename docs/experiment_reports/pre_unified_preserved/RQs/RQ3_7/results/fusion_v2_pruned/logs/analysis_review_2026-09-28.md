# 2026-09-28 — completed RQ3.7 A/B analysis handoff

## Scope and status

Single-agent offline analysis; no inference, training, renderer edits or stage C.
Contract1a8d2032bb94718e3a23b62d1a62e331b0b1b671410312b78e22b1dc756997a2.
Repeated-exposed primary development180; robustness90. TPV120 supplement complete
and published; original historical answers preserved.

## What happened

Ran registered `analyze` and added a nested report-only analysis script. Preserved
all4140 logical terminal rows. Inventoried3727 distinct successful-return artifact
groups and found no missing paths in their small commit manifests. No wholesale
PNG rehash/re-render or resume change. Physical new calls3174 including36 smoke;
shared cumulative24643. Formal physical timeouts8; logical A/B timeout positions
11 because no-op reuse propagates3 old timeouts. Historical references still
missing3. Two model-failure outputs remain scored zeros.

Produced detailed Chinese report, six statistical figures, two original dashboard
pairs and explicitly marked report crops, all metrics/fault/level CSVs, registered
and exploratory test JSON, reproducible code and nine-case evidence appendix.
Used baseline/agent-trace for paired scope and source grounding, dashboard skill
for actual saved-PNG inspection (not new renderer qualification), devlog for handoff.

## Validity and caveats

All180case fact/panel inventories agree across five new arms, all visual geometry
identities agree, four pixel hashes differ, and corresponding source PNGs agree
across models. Registration CPU/smoke and sampled real PNG/conversation review
support this audit; it is not a claim of exhaustive human OCR verification.
Only44cases have bars; unit changes apply to22/23 cases in Qwen/Gemma common cohorts.
Fifteen cases with accepted service/pod aliases are reported separately rather than
misclassified unknown. No scorer/label changes. Rounded-difference statistical
sensitivity agrees with registered primary conclusions.

One Gemma streaming answer lasted879.4seconds with8192 output tokens and
finish_reason=length. Source client passes300seconds to SDK timeout but does not
wrap streaming in an absolute wall deadline. Record this distinction rather than
claiming300seconds is a hard per-generation bound. No retrospective invalidation,
repair or rerun; future absolute deadline would need an explicit contract decision.

## Decisions

Qwen LL−TPV+.077143 passes primary Holm(.017080), but the same-content contrast
and independent proximity/link contributions are unconfirmed; Gemma does not gain.
Numeric-equivalence sensitivity survives visualization. Recommend the already
locked C for confirmation if the user authorizes it, not a newly selected layout.
All C cost-control checks pass, which does not itself authorize model calls.

## Blockers and next steps

No unexplained stage omissions. C remains unrun; no independent-test efficacy.
Report: docs/experiment_reports/RQ3_7_Results_Analysis_2026-09-28.md.
Raw results, timeouts, model errors and negative findings remain intact.

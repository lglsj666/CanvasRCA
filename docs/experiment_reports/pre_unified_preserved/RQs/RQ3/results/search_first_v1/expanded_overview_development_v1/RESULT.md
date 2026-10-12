# SEARCH33 — The previous small-cohort leader weakens on additional train cases

2026-09-12. Complete **train-only development**, not validation, 480-case eval,
or trained Composer performance. All24 new Solver calls completed in368.525s;
no infrastructure/model-format errors or truncation, maximum331 output tokens.
All24 full answers were read, all48 old/new artifact inventories and scores
were checked with the actual standalone scorer used by the inference worker.

## Method and data

Exactly SEARCH22's node_overview_v1 + typed_owner_v1 +
evidence_bound_membership_v1 + card_nonthinking_v1. One real PNG, candidate
enumeration only in prompt, no attention. Native top8 metric series plus each
node's available CPU/memory representatives; native selected R/L/G and public
service–pod membership. No label-based selection or per-case method changes.

The additional24 were fixed using the registered source-coverage/group/hash
ordering at offset18,12 per dataset. They share no search case or connected
event group with the earlier cohorts. The old24 had already informed many
adaptations; the new24 therefore provide a useful development stress check,
not an untouched final test. Retain every old score and new failure.

| Cohort | Dataset | n | MRR | AC@1 | AC@3 | AC@5 | Mean input incl. image | Mean output |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Original | AIOPS2022 |12|.520833|.416667|.583333|.666667|17754|255.000|
| Additional | AIOPS2022 |12|.354167|.166667|.416667|.666667|17754|271.417|
| Combined | AIOPS2022 |24|.437500|.291667|.500000|.666667|17754|263.208|
| Original | AIOPS2025 |12|.429167|.333333|.416667|.666667|17648.833|270.583|
| Additional | AIOPS2025 |12|.194444|.166667|.250000|.250000|17649.500|244.583|
| Combined | AIOPS2025 |24|.311806|.250000|.333333|.458333|17649.167|257.583|

Combined48 MRR=.374653. Image input is16002tokens per request. This is a
cohort expansion, not a paired treatment contrast: do not attach a paired
Wilcoxon test to old/new cases or claim another policy wins on unmeasured cases.
Full AVG@3/5, fault-type, accepted-root-granularity and cost rows are in
`metrics_breakdown.json`. None of the target scores has been established.

## What the failure review found

Candidate omission is not the cause: all24 new cases have scorer-compatible
root identities in the prompt candidates. All24 have root-associated eligible
direct telemetry in the CPU pool, but only19 retain such telemetry in the
selected packet (A22:11/12; A25:8/12). The five without it all have RR0.
Here “root-associated” means a metric/trace/log row belongs to a scorer-matched
root entity; it does **not** mean that row necessarily reveals the fault or
is sufficient to diagnose it. Related upstream/downstream clues may still exist.

Selection is not the only limitation: with root-associated direct telemetry
selected, new-cohort MRR is .386364 on11 A22 cases and .291667 on8 A25 cases.
The new24 explicit reasons mention earliest/onset priority in11 cases and
z-score language in13 (conservative literal matchers; not a measurement of
hidden reasoning). Actual examples:

- **7CE:** chooses a JVM thread spike with z999 and onset0.3m, despite the
  static guide warning that start-of-recording events and z alone are weak
  causal support. The accepted root remains rank4. Several pod IDs are
  incorrectly described as services in its prose, although emitted IDs are legal.
- **CC8:** reads node7984's load curve as a rise to58:58 is the neighboring
  memory lane's value. The load lane actually falls near1.37→.96. This is a
  concrete cross-lane reading error in the unchanged dense layout, not an
  inference-server failure. The accepted node is rank4.
- **00B/819:** favors nodes based on modest absolute CPU/memory changes and
  invents or hypothesizes hosting-related causality; accepted application/pod
  alternatives are rank2. Large normalized deviations are overinterpreted.
- **CD9:** treats “Background saving started” plus a volume-drop descriptor as
  stronger origin evidence than it warrants; the node root is missed entirely.
- **CAF:** picks a memory change and the earliest listed entity; the accepted
  TiKV root is outside its top5. This needs selection/identity-level follow-up,
  not a prompt trained on that case's private answer.
- **252:** gets an accepted root top1 but its reason calls log2-change10.8
  “smaller” than8.17 and conflates caller/callee interpretation. Correct ranking
  alone is not proof of a correct diagnostic explanation.

Actual sparse case F911 has no source spans/log events and no call edges;
the current layout leaves a large G area for onset/member entries. Preserve this
as a content-adaptivity weakness, not a reason to silently redraw this batch.

## Decision and next direction

Do not promote SEARCH22 to full eval or training on the strength of its former
.475 common24 average. Keep it as an observed reference; the expanded result
shows that its usefulness is not yet robust across training events. Prioritize
both (a) retaining useful application/pod evidence without flooding the chart
with incidental node variation, and (b) compact, unambiguous owner/value
binding and counterevidence. More identical title/layout tweaks on the old24
alone would not address these failures. Future variants must be trained/tested
label-blind and versioned; no private-root-specific rules or selective reruns.

Evidence: `expanded_review.json`, `metrics_breakdown.json`,
`private/coverage_review.json`, `private/answers_review.md`, `qualification.json`,
and `logs/20260912_review.md`. Old24 records were read, never rewritten.

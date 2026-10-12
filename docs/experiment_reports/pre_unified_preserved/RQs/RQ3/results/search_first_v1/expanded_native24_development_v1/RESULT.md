# SEARCH34 — Broader native selection partially recovers the new-cohort loss

2026-09-12. **Train-only exploratory paired comparison**,12 AIOPS2022 and12
AIOPS2025 cases; exactly SEARCH33's additional cohort. Not validation, eval,
trained Composer performance or an established shared winner.24/24 calls
completed in357.131s, all stop, five distinct allowed candidate IDs, maximum302
output tokens. No infrastructure, schema or truncation errors.

## What actually changed

Replace native top8 plus compulsory per-node CPU/memory representatives with
native top24 metrics (`ranked_membership_v1`, limit24). Same full public pool,
native ranking, public timing, source precision, trace-unit projection, actual
renderer, typed owner labels, one3996×4088 PNG, prompt-only candidates, static
instructions, request adapter and scorer. No attention or Composer calls.
R/L selection is unchanged; the existing selected-entity rules also change
some G/onset/member facts. This is a whole evidence-policy comparison, not an
equal-information representation experiment. All24 selected fact inventories
and actual PNGs differ. Old counts20(A22)/29–30(A25) become24 throughout.

## Paired outcomes

| Dataset | n | Overview MRR | Native24 MRR | Delta | AC@1 old→new | AC@3 old→new | AC@5 old→new | Repair/break/tie |
|---|---:|---:|---:|---:|---|---|---|---|
| AIOPS2022 |12|.354167|.423611|+.069444|.166667→.333333|.416667→.416667|.666667→.666667|5/2/5|
| AIOPS2025 |12|.194444|.298611|+.104167|.166667→.166667|.250000→.416667|.250000→.500000|3/2/7|

Pooled24 MRR .274306→.361111. Both exploratory Holm-adjusted p=.875;
paired dz=.147805/.283234. These observations are not significant evidence
of a population gain after repeated development. Neither dataset target is
met. Do not compare this24-case score directly with SEARCH22's other24 or
impute this policy's unmeasured scores to its48-case combined reference.

| Dataset | Mean input incl. image, both | Image tokens, both | Mean output overview→native24 | AVG@3 new | AVG@5 new |
|---|---:|---:|---|---:|---:|
| AIOPS2022 |17754|16002|271.417→252.083|.361111|.483333|
| AIOPS2025 |17649.500|16002|244.583→261.167|.305556|.383333|

Input unchanged; output savings are not consistent across datasets. Full
dataset/fault/granularity tables: `metrics_breakdown.json`. Per-case pairing:
`paired_review.json`. Actual requests and complete conversations are retained.

## Mechanism and limitations observed in the complete answer review

All24 new complete answers were read. All48 paired conversations were checked
against their complete recorded text/image request and raw response. The
B324 actual conversation was additionally read end-to-end.271 frozen
dependencies and archived source/configuration bytes rechecked with zero
mismatches; unified scorer recomputation matches every stored outcome.

- **CC8, .25→1:** native selection retains the true node CPU curves and drops
  some incidental resource lanes. Its reason now reads the1523 CPU event,
  rather than borrowing the neighboring memory lane's58 value as load.
  However, its claimed node→service causal link is still not established by
  the call graph; improved ranking is not proof of correct causal reasoning.
- **819 and00B, .5→1:** ranking moves from an infrastructure-first explanation
  to the accepted application/pod.00B still incorrectly calls a5-digit ID a
  service and claims stronger resource-failure evidence than warranted.
- **B324,0→.5:** the accepted node6421 is now second. The first-ranked node is
  justified by a stated47.3→47.3 change and z999 as “exhaustion”, despite the
  unchanged prompt explicitly warning against this inference.
- **CD9,0→1:** the answer switches from a routine background-save log to
  measured node4359 CPU/network activity. Selection/context matters, but the
  asserted propagation chain remains stronger than the visible evidence.
- **C0,1→0:** native24 removes all directly root-owned metric/trace/log rows
  that the overview retained. A competing node's disk/inode pattern dominates.
- **740,.5→0 and252,1→.5:** even with root-associated rows still selected,
  JVM/resource patterns redirect attention to other entities. Repeated
  correlated series from one entity can consume many of the24 slots.
- **7CE, C86, F5, BAC:** large z/early-onset claims still dominate, sometimes
  interpreting one started thread or inventory growth as resource exhaustion.
- **09ED,0→0:** its reason diagnoses nodes2134/5414 but its actual ranking
  contains neither. It also invents co-location/shared-volume explanations.

Offline private owner association: root-associated direct telemetry is
selected19/24 in the overview and18/24 in native24 (A22 11→11; A25 8→7).
684 gains it; C0 and17BB lose it. All six native24 cases without it score0.
Owner association is not proof that a row contains diagnostic fault evidence,
and indirect clues may still be present. Since coverage slightly falls while
MRR rises, the improvement cannot be summarized as “more root coverage”.

## Decision

Keep native24 as a useful paired development candidate, not a promoted
winner. The node overview is not uniformly beneficial, but naive expansion
of anomaly-ranked curves also repeats noisy features and can lose important
node evidence. Next selection work should control redundant owner/metric
families and preserve genuinely informative cross-level coverage using public
data only. Separately test owner/value readability and misleading prominence
of normalized peaks; do not encode these cases' private answers into rules.
No validation/eval or SFT/RL begins on these scores.

Protocol/source rationale: `RQs/RQ3/descriptions/RQ3_experiments.md`, SEARCH34.
CPU/visual qualification and the zero-call gallery interruption are in
`../expanded_native24_gallery_v1/`. All negative outcomes are preserved.

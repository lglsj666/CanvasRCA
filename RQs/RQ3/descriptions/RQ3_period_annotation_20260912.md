# DD-RQ3-SEARCH-27 — Explicit metric period comparisons

Date: 2026-09-12. Status: completed train-only development; not promoted.

## Decision and evidence
SEARCH26's two MET-Z selectors worsened both dataset means. Keep SEARCH23's
native node-overview selection and owner-header reference. SEARCH20 already
tested zero-origin axes without changing reciprocal rank; do not repeat it.
Current answers sometimes conflate a peak, a period mean and capacity exhaustion.
The 24-case public packet audit found all four MET-Z mean/std fields on all599
selected metric rows;140 rows have equal rounded period-mean labels. Never infer
zero change from equal rounded labels or calculate ratios from those labels.

Add a measured text annotation **inside the PNG**, below each existing metric
curve: regular-to-current mean and standard deviation. Keep the stored labels
unchanged, including suffixes/scientific notation. Display the public MET-Z
comparison interval in the metric context, separate from its heuristic shaded
window. No new statistics, window, candidate policy, evidence selection, curve
coordinates, layout, axis or prompt recipe. This exposes existing selected
packet statistics that the reference painter did not explicitly display; it is
visual evidence augmentation, not an equal-visible-fact encoding-only claim.

## Related reading
Zhang, Yang, Inala, Singh, Gao, Su and Wang, *Towards Understanding Graphical
Perception in Large Multimodal Models*, arXiv2503.10857v1,13March2025; **preprint**
(no verified conference acceptance), checked12September2026.
[Paper](https://arxiv.org/html/2503.10857),
[official code](https://github.com/microsoft/lmm-graphical-perception).
Read main sections1–8, inspected appendix evaluation/inference notes and
detailed tables, plus official README. The study tests
14 chart types and ten tasks on1000 VisText-derived datasets with GPT-4o,
InternVL2,Phi3.5 and ChartAssistant. Table3 shows annotation-dependent accuracy;
section6 also shows deterioration as data density grows. Its GPT-4o judge and
simple-chart tasks differ from our deterministic RCA scorer and dense telemetry.
The repository exposes chart generation/evaluation notebooks and an occlusion
probe, not our RCA implementation. Borrow the annotation hypothesis only;
neither RCA improvement nor our target-model behavior is established. No
attention/occlusion calls or external API runtime dependency are introduced.

## Intervention and checks
`metric_annotation_policy=metz_periods_v1`, versus default `none`. Allowed only
for separate metric lanes. Preserve base/peak/z, all64 source bin coordinates,
owner/name text and every other card. Use existing display values directly;
reject malformed numeric labels and non-relative/inconsistent interval metadata.
No synthetic values for absent statistics. Fit annotation in the existing
bottom strip with measured bounds and a fixed readable font; reject overflow,
do not shrink text, overwrite curves or silently discard fields.

Require CPU unit tests, full suite, original24 PNG byte replay, selected packet
and static prompt equality, geometry/primitive comparison, actual pixel-change
locality and real dense/sparse PNG inspection. No reference result is rewritten.
All model-visible source/candidate identities stay anonymous. Candidate list
appears only in prompt. Existing guide already explains MET-Z mean/std.

## Batch, statistics and next action
Reuse exactly SEARCH23's24 train cases (12 per AIOPS dataset,offset6), same
isolated split/public pools. One new condition: at most24 Solver calls,
concurrency4,3600seconds,card_nonthinking_v1 with8192 output maximum.
No Composer call,attention,validation,eval,SFT or RL. Compare each dataset
against completed owner_header_development_v1; two exploratory Pratt-Wilcoxon
contrasts with Holm and paired dz, no confidence interval. Report MRR,tokens,
repair/break/tie and rendering/model failures. Read every complete answer and
actual persisted prompt/PNG/partial/accounting. No correctness-driven retries.
Tiny repeated-training-cohort scores do not meet full evaluation targets.

## CPU review progress
Targeted24 tests pass. Broader CPU checks comprise212 tests plus134 renderer,
identity,clock,checkpoint,launcher and streaming tests:346 unique tests pass,
including every test in the preceding327-test qualification. XML files are
`results/search_first_v1/cpu_period_{targeted,full,extended}_v1.xml`.
The initial static pixel-audit draft used outer-card coordinates for the context
mask; corrected it to the actual M-facet coordinates before executing the audit.
No experimental pixels or model inputs changed for that audit-script correction.
The two reference-guide copies had three pre-existing literature entries only
in the Nibi checkout; appended the new paper entry to both without overwriting
those unrelated differences. New paper metadata remains explicitly preprint.

All24 public-source, source-bin, actual pixel-locality and reference PNG replay
checks passed. Dense A22/A25 and sparse actual PNGs were opened and inspected;
the A25 original-detail viewer reports a3996x4088→3136x3208 display resize.
Review hash binding is stored in `period_gallery_v1/review.json`. No model
request was made before these checks passed. Proceed with the registered24
train-only calls under the existing qualified card_nonthinking_v1 recipe.

## Completed result and decision
All24 calls completed in341.055 seconds with no errors/truncation,max349 output
tokens. A22 MRR .506944→.451389;A25 .440278→.405556. One repair,two breaks,
21 ties;both exploratory Holm p=1. Actual input tokens unchanged. All full
answers,prompts,images and persistence checked;cross-row numeric attribution
and unsupported exhaustion/hosting claims remain. Do not promote. See
`results/search_first_v1/period_development_v1/logs/20260912_review.md` and paired
review. No validation/eval/training or target attainment.

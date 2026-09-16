# DD-RQ3-SEARCH-20 — Source-value-preserving zero-axis intervention

Date: 2026-09-12. Status: completed train-only development; not promoted.

## Context and decision

SEARCH-19 complete answers repeatedly equate tiny node resource changes with
exhaustion. Current local raw axes expand each row's numeric min/max to its
full height. Test `zero_origin_raw`: preserve every selected source value,
64-bin location, title, base/peak/z, unit and metadata; extend each raw axis
to include zero. Signed series still include their negative values; all-zero
or all-absent sequences have a safe [0,1] display range. This does not imply
that zero is always the best monitoring baseline or that a small change is
irrelevant. No percentage capacity is invented, and no measured point is
clipped or deleted. Existing native and robust-z defaults are unchanged.

Keep SEARCH-19 node overview, owner row order, 3996×4088 layout, image-only
facts, candidate prompt, static guide, services-first output and runtime.
Reuse the twelve completed SEARCH-19 overview answers as the fixed control;
first verify original PNG byte-reproduction and full selected packet/prompt
identity. Do not rerun controls to select favorable replicates. New batch is
twelve calls, one per previously registered train case, no validation/eval,
Composer or training. Current guide already describes per-lane source units
and asks to read numerical magnitudes; image header explicitly identifies the
new axis. No case-specific hints are inserted into prompt.

## Evidence source and transfer boundary

Focused literature check asks whether visual scale may change interpretation
without changing facts. Read Mahbub et al., *The Perils of Chart Deception*,
[author paper](https://arxiv.org/html/2508.09716v1), introduction, taxonomy,
paired-chart methods, results and conclusion; [official code](https://github.com/vis-nlp/visDeception)
and [IEEE VIS award record](https://mf.ieeevis.org/year/2025/info/awards/best-paper-awards).
The paper studies paired charts and ten VLMs, finding sensitivity to several
axis manipulations. Its truncation experiment concerns bars, not these RCA
line plots. Complex dashboards were excluded and RCA was not measured.
Therefore this supports testing an axis intervention, not claiming that zero
axes improve RCA or declaring all earlier min/max plots defective. The code
is a reference, not a new runtime dependency or reproduction.

Rejected source: arXiv 2504.13916 is an unrelated household-robot questioning
paper, not this visualization study; do not cite it for the present decision.

## Qualification and acceptance

CPU checks: nonnegative/negative/signed/zero/all-absent/gapped values,
source immutability, identical bin values, finite pixels, no clipping,
fingerprint change, incompatible overlay rejection and old-default PNG
regression. Verify twelve actual image pairs, static prompt/candidate identity,
no pixels outside M changed, all facts bound to visible primitives and one
image. Open actual PNGs before calls. Preserve partial outputs and all failures.
Report paired train MRR and separate input/output cost, not success guarantees.
Following this local check, broaden the isolated train cohort before any
validation shortlist; do not endlessly tune this twelve-case sample.

## Qualification completed

251 CPU tests passed in 74.06 seconds, source count 5965. All twelve new
previews preserve packets, static prompts, candidates, source bin values and
non-M pixels. Two native-control PNGs reproduced byte-identically. Actual
C034 (A22) and 8AB (A25) PNGs opened and reviewed. Gallery summary hash:
`bde1d63b539e6fe678f611db4c31bf037c66511341589cb7736187c8a41060d0`.
An early reviewer invocation before the gallery finished stopped at absent
summary.json; no model call was attempted. The complete-gallery audit passed.

## Observed outcome and next decision

12/12 new calls completed in 224.280 seconds, with no transport, schema,
context or output truncation errors. All twelve complete raw answers were
read. Five distinct legal candidate IDs were returned in every answer;
actual full candidate enumeration remains prompt-only. Actual request text,
effective server/sampling, selected facts and token limits match the fixed
SEARCH-19 overview control. No attention was collected. Largest output 314.

A22 MRR remains .3750; A25 remains .2417. Every per-case reciprocal rank is
unchanged, despite some changes in candidate lists and explanations. Mean
output tokens are 264.8/262.2 versus 259.2/310.3; image tokens remain 16,002.
This small repeated-train result does not establish invariance generally.
The axis intervention is not promoted. Resource saturation and entity-role
claims remain unreliable in several answers. Next widen the isolated train
cohort rather than continue tuning these same twelve cases. Artifacts and
independent paired audit: `results/search_first_v1/zero_origin_development_v1/`.

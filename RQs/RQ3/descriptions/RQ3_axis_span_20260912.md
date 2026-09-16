# DD-RQ3-SEARCH-36 — A continuous minimum raw-axis span

Date: 2026-09-12. Status: adopted for bounded training-subset exploration,
before calls; not a promoted pipeline or a correction of old result status.

## Question and decision

SEARCH34/35 full-answer review found small absolute changes being described
as large resource failures. Raw per-series min/max axes can visually amplify
such changes; z labels and causal reasoning may also be responsible. Isolate
the axis contribution, without changing selection, labels or instructions.

Add `metric_range_floor_fraction`, a finite continuous number in [0,2], default
0. For finite source-bin values v, a nonzero setting expands an undersized raw
axis symmetrically around (min(v)+max(v))/2 until its span is at least
`fraction * median(abs(v))`. Never contract the original domain or clip a bin.
Preserve the inherited empty/constant fallback where representable; fail closed
on unrepresentable numeric domains. The setting is allowed only for separate
raw line/heatmap lanes. It does not change z-normalized or overlay rendering.

First registered point is **0.5**, on the same SEARCH33/34/35 additional24
training cases (12 per AIOPS dataset). Baseline is SEARCH34 native24, not the
entity-coverage policy. Fixed source pools, selection, metadata, candidates,
prompts, source values, labels, static reading guide, PNG dimensions, R/L/G,
request recipe, output contract and scorer. This is one visual-amplitude
intervention; there is no added diagnostic instruction. Candidate enumeration
remains prompt-only; diagnostic evidence remains in one real PNG.

The parameter controls visual relative amplitude, not diagnostic importance.
Small absolute changes may genuinely matter; suppressing their prominence can
harm RCA. Unlike SEARCH17 this does not require every axis to contain zero.
Unlike SEARCH31 it keeps z/onset text. One tested nonzero point cannot establish
a continuous response trend, general robustness, or the best parameter value.

## Focused literature record

Mahbub et al., *The Perils of Chart Deception: How Misleading Visualizations
Affect Vision-Language Models*, arXiv:2508.09716v1 (13 August2025), revisited
2026-09-12. The existing library records IEEE VIS2025 short-paper status.
Read introduction, method, evaluation, results and conclusion. Its 800 paired
charts span eight manipulations and ten VLMs; paired Likert judgments and
Wilcoxon tests show sensitivity to axis/shape manipulation. It is not RCA,
does not evaluate our Qwen3.8 or this range-floor formula, and excludes complex
multi-view dashboards. Transfer is a hypothesis about visual prominence, not
an established improvement. [Paper](https://arxiv.org/html/2508.09716v1).

The [author repository](https://github.com/vis-nlp/visDeception) has separate
ShortPaper and ExtendedBenchmark directories; its current README also describes
a later2026 study. Do not conflate their results. No external code is imported.
The official2025 program URL returned a transient error on this revisit; no
new venue upgrade is made. This is an existing-library paper, not a new entry.

## Qualification and execution

CPU checks cover fractions0,.25,.5,1,2; bool/NaN/Inf/out-of-range rejection;
negative, mixed-sign, constant, zero, tiny, huge, sparse and empty values;
unchanged values/order/x positions; finite non-clipped y positions; explicit
geometry and source binding. Replay native PNGs byte-for-byte. Audit all24
source packets and static prompts, unchanged non-M region pixels, and inspect
three actual PNGs (dense, small-change and sparse). Preserve audit failures.

One24-call local Qwen batch, concurrency4,3600-second maximum. No attention,
Composer, raw-data regeneration, validation/eval or training. Preserve all
completed/failed calls; no correctness retries. Freeze and archive source,
config, cohort and reviewed inputs before inference. Use registered resume.

Pre-inference audit found two natural identical-input cases. Reuse their
existing native24 responses, with explicit same-input/model reference mapping,
so this remains24 logical paired cases but requires22 new calls. This decision
uses input identity, not scores; do not remove no-ops from effectiveness metrics.

Compare paired MRR/AC/AVG/cost with SEARCH34; exploratory Pratt-Wilcoxon,
paired dz and one two-dataset Holm family. Report axis expansion prevalence,
relative curve height, full answer review, repair/break/tie and failures.
No label-specific selection or post-score axis changes. Record negative as
well as positive results; source facts and earlier artifacts remain untouched.

# SEARCH36 — A continuous axis-span floor does not give a shared improvement

2026-09-12. Complete train-only paired development:12 AIOPS2022 and12
AIOPS2025 cases.22 new Qwen3.8 Solver calls plus2 explicitly referenced
byte-identical inputs. No Composer, training, attention, validation or eval.
The new calls completed in329.398seconds; no infrastructure/schema errors or
output truncation, maximum343 output tokens. Every answer and all48 logical
paired inputs/scores were inspected;278 frozen dependencies remain unchanged.

## What changed

Keep SEARCH34 native24 selection, public source statistics, source values,
one3996x4088 PNG, typed owner labels, complete prompt-only candidates,
all static instructions and request/scorer recipe. Set the new continuous
`metric_range_floor_fraction=0.5`: extend a narrow raw y-domain symmetrically
to at least half the median absolute source-bin value, without contracting
domains, clipping or dropping bins. Default0 preserves native rendering.

The actual audit proves identical24 packets and text requests, identical
non-metric-lane pixels, and six exact native/new PNG replays.159/576 curve
lanes change y coordinates; all original values, bins and x coordinates remain.
Two cases (819F72DDB48B and987C8AAB3A59) are complete input no-ops and reuse
their old results. They stay in the24-case analysis; calls are not counted twice.
The309-test CPU suite passed. Configuration-inheritance, invocation-environment
and overly strong no-op audit assertions were caught/repaired before inference;
see the gallery's IMPLEMENTATION_REVIEW.md. They did not change old results.

## Paired performance

| Dataset | n | Native24 MRR | Span-floor MRR | Delta | AC@1 | AC@3 | AC@5 | AVG@3 | AVG@5 | Repair/break/tie | Holm p | dz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| AIOPS2022 |12|.423611|.444444|+.020833|.333333|.500000|.666667|.416667|.516667|2/2/8|1.000000|.068099|
| AIOPS2025 |12|.298611|.245833|-.052778|.166667|.250000|.416667|.222222|.283333|1/4/7|.750000|-.126130|

Pooled24 MRR .361111 -> .345139. Exploratory paired Pratt-Wilcoxon raw
p-values1.0/.375, one two-dataset Holm family; repeated training-subset search,
not confirmatory efficacy. Three repairs,six breaks,15 ties. No shared gain,
no target achieved, and no promotion to training/full evaluation.

| Dataset | Mean input incl. image, both | Image tokens, both | Mean output native -> floor |
|---|---:|---:|---:|
| AIOPS2022 |17754|16002|252.083 ->259.000|
| AIOPS2025 |17649.500|16002|261.167 ->248.750|

Input cost is unchanged. Output changes are small and inconsistent by dataset;
do not claim a cost-saving pipeline. Full fault/granularity/metric rows are in
metrics_breakdown.json; reused responses are included in per-diagnosis cost but
excluded from newly consumed generation in reuse.json/qualification.json.

## What the complete response review shows

The floor visibly reduces small-change prominence, but it does not repair
all owner binding, semantics or origin/victim reasoning:

- **7CE,.25 ->1:** the answer now uses a pod's connection/configuration errors
  together with exclusive latency increases. This is a useful ranking repair,
  but one sampled response does not prove that the single changed lane caused
  all improvements in its reasoning.
- **09ED,0 ->1:** combines CPU/process changes with service-linked trace latency
  and ranks accepted service/pod aliases. The former node-only story disappears.
- **B324,.5 ->0:** the old nearly unchanged filesystem curve is now flat, yet
  the new answer attributes M03's disk-write values to service346. The actual
  printed owner is NODE3184. It chooses the visible graph's upstream service
  and transfers unrelated node evidence to it. The full conversation and PNG
  confirm an output grounding error, not a changed input or schema failure.
- **C86,1/3 ->0:** explicitly interprets a thread count0 ->1 as resource
  exhaustion/thread leakage. The metric's median is zero, so this floor need
  not damp it. Relative deviation and metric semantics remain unresolved.
- **CD9,1 ->.2:** recognizes node CPU/memory strain but ranks application pods
  before the accepted node, partly using unsupported infrastructure association.
- **00B,1 ->.5:** prioritizes node I/O contention despite acknowledging no
  visible hosting link. The accepted pod remains second.
- **C0,0 ->0:** the reason centers on node7425 while ranking five pods and
  misreads public NAME GROUPS as hosting evidence. Actual static instructions
  explicitly say they are not node-hosting relationships.
- **209,.25 ->0:** earliest-onset and disk-write language still outweigh the
  alternative node. Removing visual exaggeration does not prevent onset shortcuts.

Root-associated direct telemetry is identical to native24:11/12 A22 and7/12
A25. It is an offline owner-association measure, not proof that the selected
rows contain enough diagnostic evidence. Candidate sets and coverage did not
change. Correct top1 also does not establish correct causal reasoning.

## Decision

Retain the opt-in continuous parameter and its tested bounds, but do not make
0.5 the default or call it an improvement. Keep original plots/results intact.
This candidate tests an idea motivated by the chart-deception literature, not
a reproduction of its method; the paper does not establish an RCA benefit.
Full protocol/source record:
[axis-span protocol](../../../../../../../../RQs/RQ3/descriptions/RQ3_axis_span_20260912.md).

Further search should address evidence ownership and metric semantics together
with selection redundancy; merely flattening quiet lanes is insufficient.
Do not encode these cases' private roots into selection/prompt rules or repeat
failed answers until correct. No full-eval or training authorization is inferred
from this completed small batch. The main performance/efficiency goal is open.

Artifacts: paired_review.json, private/answers_review.md, private/coverage_review.json,
private/source_snapshot.tar.gz, reuse.json, qualification.json and the gallery's
CPU/visual review. Owned experiment/server processes stopped normally.

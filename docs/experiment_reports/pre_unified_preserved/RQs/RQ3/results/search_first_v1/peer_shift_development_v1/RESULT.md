# SEARCH39 — Peer-relative selection, train cohort C

24/24 completed in363.138s. No errors, timeout, truncation or candidate-format
failures; maximum393 output tokens. The source verification checks all273
frozen dependencies unchanged. All24 complete answers and48 paired request/
conversation/scorer records were reviewed. No new attention, eval or training.

| Dataset | N | Native24 MRR | Peer MRR | Repair / break / tie | Input tokens, both | Output native → peer |
|---|---:|---:|---:|---:|---:|---:|
| AIOPS-2022 | 12 | .423611 | .361111 | 3 / 5 / 4 | 17,754 | 252.08 → 274.83 |
| AIOPS-2025 | 12 | .298611 | .333333 | 2 / 2 / 8 | 17,649.5 | 261.17 → 248.00 |

Pratt-Wilcoxon raw p=.5/.875, both Holm-adjusted p=1; paired dz=-.1632/.1156.
This small train-only contrast does not support joint improvement. Keep the
negative/mixed result, not just repaired examples. **Not promoted.**

## What changed and what the complete answers show

All24 selection sets and actual PNGs changed at fixed24 metric lanes. Native
first eight survive in every case; original R/L facts, candidate set/order,
public projection, static prompt, image geometry and request recipe match.
Existing G/onset/name-group selection may change with selected owners.

Root-associated direct metric/trace/log coverage changes11→10 in A22 and7→8
in A25: pooled coverage remains18/24. Coverage alone is not causal sufficiency.
The generic peer hypothesis is asymmetric: same metric names can describe
different workload; common failures can affect multiple peers similarly.

Full responses continue to call page faults, modest capacity changes, JVM
class/thread activity and disk-byte changes resource exhaustion without enough
support. Several invent hosting relationships even though the static prompt
forbids that inference. A22 INC-7CE00360E043 repairs RR .25→1 but contains
unsupported interpretations too; correct ranking is not evidence of faithful
reasoning. A25 INC-BF5E3D25D876 repairs .3333→1; INC-209913B37F61 loses .25→0
while treating a small disk-time change as proof of an initiating disk failure.

Artifacts: `paired_review.json`, `metrics_breakdown.json`,
`private/coverage_review.json`, `private/answers_review.md`,
`source_verification.json`. Gallery preflight failures/corrections are retained;
no model request was made before those checks passed. The original full
processed corpus and prior batches were not modified.

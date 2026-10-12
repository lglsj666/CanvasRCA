# 2026-10-01 — RQ3.11 final result analysis

## Scope and status

`rq311_protected_compression_v2`, exposed development eval: 60 AIOPS-2022,
60 AIOPS-2025 and 20 AegisLab cases. All 1,120 positions are terminal;
1,108 have results, including 17 references, and 12 requests timed out.
This is a complete queue with explicitly missing responses, not an independent test.

## What happened

Full offline artifact, numerical input, checkpoint and unchanged-score audits
passed. Four primary and three secondary Pratt/Holm comparisons were independently
rechecked. The preselected HIGH visual method has AIOPS MRR 0.2840 versus exact
text 0.2792: paired delta +0.004861, Holm p=1, total tokens +3.103%.
It has no positive mean advantage over equivalent encoded text, even under
the known-side timeout bounds. No registered contrast is significant.

Reviewed 24 paired explanation entries across 12 cases and four complete PNGs.
Unit, chronology, instance-binding and attribution faults persist. Remaining
67 queue entries were not semantically adjudicated. The finite numeric signatures
are preserved for all 3,360 budget-series, which does not certify RCA or explanations.

## Validity and caveats

Original answers and scores remain unchanged. Two duplicate-ID answers retain
zero scores. Twelve timeout usages remain unknown; known experiment token totals
are lower bounds. The batch is exposed development data and budgets couple
resolution with quantization. Runtime source authority is the original 85-file
archive; only offline reporting main/gates differ after execution.

## Decisions

Do not recommend preselected HIGH for deployment. Retain the public numerical
codec and its audit guarantees. LOW is a development signal, not a retroactive
replacement candidate. No new request, retry, training or successor experiment ran.

## Blockers and next steps

No blocker to delivery of this report. Future budget/readability research needs
a separate registration and execution authorization; no new method is implemented here.

Detailed report: `docs/experiment_reports/RQ3_11_Qwen_Analysis_2026-10-01.md`.
Reproducible tables, PNG/SVG, manual notes, statistics verification, report validation
and academic disposition: `results/protected_v2/analysis_reviewed_v1/`.

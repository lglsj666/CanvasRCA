# 2026-09-08 — Finite-series / undefined-baseline rendering recovery

## Scope and status

RQ2.1 formal selection preparation, CPU-only. No formal Solver request had
started. The supervisor stopped after 178 reported cases; 188 completed case
summaries had been persisted while in-flight workers drained.

## What happened

`INC-3BFC24F5D6E5` includes a selected metric with finite later observations but
no finite baseline mean. The inherited deviation-peak annotation applied
`nanargmax` to an all-NaN deviation array and raised `ValueError`.

The RQ2.1-local renderer now skips only that undefined peak annotation. Actual
observations, connected curves, source statistics, selectors, prompts, model
recipes and RQ1.1 remain unchanged. The repaired case's random-selection PNG
was inspected, including its formerly failing metric panel.

## Verification and validity

All 47 CPU tests pass, including an explicit finite-observation/nonfinite-baseline
regression. The real case completed all selection artifacts. Completed prior
inputs could not have traversed the formerly crashing branch; their artifact
bytes are retained. Cache metadata and current qualification follow-ups adopt
the repair with archived prior summaries and a scoped compatibility proof.
The two previously successful live-repair requests were re-materialized and
their text and image hashes match exactly. The execution gate passes. No
additional model call, historical result rewrite or case exclusion was needed.

## Decision and next steps

Resume the registered full suite from completed caches. Do not replace the
baseline with zero, drop the series, add a new model-facing explanation, or
repeat otherwise unchanged smoke calls. Monitor subsequent CPU preparation and
continue the existing sequential-model experiment schedule.

Evidence: `before.json`, `proof.json`, `cpu_tests.log`, `real_case.log` and the
archived `summaries_before/` in this directory.

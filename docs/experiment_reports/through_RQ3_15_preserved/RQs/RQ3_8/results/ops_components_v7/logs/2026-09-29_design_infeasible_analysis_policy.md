# 2026-09-29 — Design-infeasible analysis policy

## Scope and status

RQ3.8 `ops_components_v7`, local and Nibi formal-result analysis. Adopted
analysis decision; the experiment remains in progress. This record changes no
model-visible input and is not an efficacy result.

## What happened

During local Qwen shard 0, 56 logical cells across six AegisLab cases were
marked `design_infeasible` because their shared fixed-slot dashboards required
8194--8318 pixels, above the registered 8192-pixel canvas limit. No model calls
were initiated for these cells. Earlier code attached an operational
`end_to_end_mrr: 0` field under the superseded analysis rule.

## Validity and caveats

The user explicitly decided that an unconstructable dashboard is unavailable
data, not an incorrect model diagnosis. It must therefore be excluded from all
accuracy denominators. The capacity limitation remains visible through counts
and executable rates; it is not deleted or relabeled as a successful result.

## Decisions

- Exclude `design_infeasible` from MRR, AC@1/3/5, AVG@3/5, macro/pooled means,
  paired tests, repair/break and accuracy-bound calculations.
- Pair a contrast only on cases where all arms required by that contrast are
  executable. An unrelated infeasible arm does not exclude the case.
- Report excluded design-infeasible counts and executable rates separately by
  model, dataset, cohort and arm.
- Ignore any legacy zero-MRR field on these flags during scientific analysis.
- Continue treating request timeouts as infrastructure missingness and
  completed malformed/illegal model outputs under the frozen scorer.

## Blockers

None for the running inference queue. Final aggregation code must implement
and audit DD-20260929-09 before an RQ3.8 report is accepted.

## Next steps

Let the unchanged formal queue finish. At analysis time, enforce the recorded
exclusion policy and include an explicit executable-coverage table.

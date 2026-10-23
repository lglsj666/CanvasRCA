# RQ4.5 roadmap

**Current endpoint (2026-10-19): local full experiment and final analysis completed.**
1560 formal positions, 1538 actual formal calls, 22 references; plus 18 local
smoke calls. Both nominees fail the advancement targets. No new experiment
is activated. [Final report](../../../docs/experiment_reports/RQ4_5_Qwen_Analysis_2026-10-19.md).

## Historical CPU qualification checkpoint

1. Plan/protocol/code and static checks: complete.
2. Complete 220-case CPU processor/source/geometry/context/cost qualification: passed.
3. Independent QA input preparation, one-example-per-arm/dataset visual review, boundary review and actual deterministic repaint: passed.
4. Unit27, runtime30 and actual passive-region transport-invariance audit: passed. All inputs, source/config and checkpoint provenance frozen; new model calls 0. [Qualification report](../../../docs/experiment_reports/RQ4_5_CPU_Qualification_2026-10-19.md).
5. Stop. GPU smoke is not run and requires separate authorization/activation; formal also requires passed smoke. Do not infer GPU qualification or ranking gains from CPU passage.

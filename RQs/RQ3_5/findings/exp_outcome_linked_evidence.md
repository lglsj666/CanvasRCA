# Outcome-linked evidence

## Current outcome — 2026-09-26

Status: formal A/B screen60 completed; repeated-exposed screening only. B has
719 done and one Qwen request timeout across 720 planned logical units.
All three J arms preserve original TPV; 32 no-op cases reuse exact requests,
accounting for 192 logical reuses across three arms and two models.

J_COND versus TPV macro MRR is 0.3387 vs 0.3411 for Qwen (59 common cases),
0.1833 vs 0.1722 for Gemma (60). No registered J gain survives Holm correction.
Actual interventions occur in 28/60 cases: AIOPS-2022 20, AIOPS-2025 5,
AegisLab 3. All 105 selected packs are request-family, with zero eligible scope
packs. Active-only J_COND delta is -0.0062 / +0.0238; no-ops alone do not
explain the weak results. Qwen W_NO_K remains a stronger descriptive comparator.

The same added statistics can repair one model and break the other. Reviewed
reasons sometimes ignore negative associations or cite only pre-existing facts;
successful rank movement is not proof of conditional-probability reasoning.
Do not automatically expand J visualization or C/D/check/test from these results.

Full report and reproducible artifacts:
[screen report](../../../docs/experiment_reports/RQ3_5_Screen_Analysis_2026-09-26.md).

## Historical qualification status (superseded operationally)

At the time of the following notes, no formal efficacy findings existed.

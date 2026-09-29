# Evidence × instruction

## Current outcome — 2026-09-26

Status: formal A/B screen60 completed; repeated-exposed screening, not check120
or test. All 720 A logical units are terminal: 718 done and two Qwen request
timeouts. Model-output failure remains scored; infrastructure timeouts are
excluded through matched family/common-case sets rather than counted as wrong.

On the six-arm common set (Qwen 58, Gemma 60), E_S_D_P has dataset-macro MRR
0.4006 / 0.3836 versus E_P_D_P 0.3191 / 0.3039. Positive evidence effects are
not Holm-significant. Gemma's registered instruction effect is -0.0692,
case-level Holm p=0.0241, but event-group sensitivity Holm p=0.0727. Its
candidate count and AC@5 shrink under the SIRCL instruction, while S-evidence
AC@1 remains 0.2833 under both instructions. Do not equate this with uniform
Top-1 reasoning deterioration.

The evidence factor includes native statistics/serialization, not only selection.
A reviewed AegisLab example also shows different duration projections between
P0 and SIRCL. It requires an explicitly aligned control before pure-selector
attribution, not a silent historical rewrite. E_S_D_P warrants bounded follow-up;
no next experiment is started or promoted by this analysis.

Full paired statistics, figures, fault/root strata and reviewed conversations:
[screen report](../../../docs/experiment_reports/RQ3_5_Screen_Analysis_2026-09-26.md).

## Historical qualification and restart notes

2026-09-26 status: formal screen paused after an input-capacity failure. The
lossless-block input repair passed static and CPU checks. Of 38 completed formal
units, 26 crossed-input records are retained as predecessor-version evidence
and 12 native-control records remain reusable. All preparation is preserved.
The repaired crossed inputs still require a separately approved 12-call GPU
supplement; no repaired-version formal efficacy results exist yet. See
[qualification audit](../../../docs/issues/RQ3_5_qualification_2026-09-25.md).

Later user override: all 38 preceding formal outputs have now been deleted at
the user's request, including the otherwise reusable native results. Preparation
and call accounting are retained. The approved 12-call block supplement
completed, but review found an unprojected last-GC epoch metric; A is
`failed_model_input_audit` and formal restart is pending correction and a new
explicitly authorized targeted qualification. No formal efficacy findings exist.

Latest status, 2026-09-26: the user-approved last-GC display repair passed 28
unit tests, the 120-request CPU matrix, the complete 60-case scope/capacity audit,
and four targeted GPU calls (213.02 s). Actual inputs and outputs were reviewed.
The A/B screen queue is restarted from zero under the repaired contract;
all 60 preparations remain reusable. This supersedes the preceding qualification
block, not any historical result status. No formal efficacy conclusion yet.

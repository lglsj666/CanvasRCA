# RQ3.1 — Contrastive evidence selection and verifiable visual diagnosis

Status (2026-09-16, plan revision 8): documentation update only, then stop.
Direct-per-case branches retain their existing registration/runtime history;
new direct-table controls are implemented and statically checked, but not yet CPU/smoke qualified. The
earlier revision-7 static pause was superseded by later user authorization and
does not report current process state. The complete scientific plan is
[research-plan revision 8](../../../docs/CanvasRCA_Research_Plan_2026-09-15.md).

The research studies whether source-bound evidence comparing competing root
causes, and its visual organization, improve a frozen one-call RCA solver's
accuracy, evidence reliability and cost. It does not train a Composer/Solver in
the first paper and does not resume the old tournament.

RQ480 supplies method-development and selection feedback. The final test role
is separate from subsequent development but includes explicitly retained prior
validation exposure; it is not described as wholly untouched. Dataset roles and
the stage-qualified work are registered in
[experiments](RQ3_1_experiments.md). Original RQ1.1/RQ2.1/RQ3 data and results
retain their history and original status.

The central visual question is whether a dashboard adds diagnostic value over
direct textual contrast using the same selected observations and comparisons.
Keep X_C's reference/catalogue implementation; plan X_C_TABLE with locally
available comparison values plus its screenshot control. Same-content tests,
controlled input interventions, budget/load curves and locked test outcomes
must establish the scope of any visual benefit. A better selector or a visual
ablation alone cannot establish that benefit.

This paper requires no engineer recruitment, user study or independent human
annotation campaign. Machine RCA quality, source-bound checkable assertions,
robustness and cost are its endpoints. Automatic checks do not establish full
reasoning fidelity or human verification efficiency. Preserve null and negative
findings, and narrow the visual claim if strong text performs as well or better.

# Frozen Solver generalization — formal experiment not run

## Current qualification status — 2026-09-10

Repair v3 passed eight calls in 303.73 seconds and its manual input/output
review. Six Text/Compact/Canvas harness Solver calls persisted attention;
two disposable QUAL_LORA programs failed legality, honestly retained. The
same adapter's vLLM/training token-logprob replay passed the registered mean
tolerance without new generation. See [manual review](../results/exp_frozen_solver_generalization_smoke_repair_v3/review.md).
These are qualification controls, not formal learned-policy or strong-baseline
results. Full generalization orchestration remains unexecuted.

## Predecessor qualification — 2026-09-09

No formal generalization comparison has run. The bounded smoke completed
two Composer calls and one Solver Text call, then failed at the default
scorer's legacy external import. Saved responses/conversations survived.
The existing standalone granularity matcher now supplies the unified scorer;
the later attribution smoke demonstrated successful scoring. This original
failed logical smoke is preserved, not reset or mislabeled passed. See
[qualification handoff](../descriptions/RQ3_qualification_20260909.md).

## Earlier pre-smoke state (superseded status, retained history)

The existing 480-case evaluation roster is retained unchanged and has not
been used to tune RQ3. All TrainTicket cases remain excluded from training
and validation. No RQ3 formal inference or transfer result exists.

T_FIXED/C_FIXED/TPV_FIXED/D_FIXED and six Composer strategies are registered,
but their complete evaluation orchestration and baseline request compatibility
still require qualification. Historical RQ1.1/RQ2 scores are background,
not substituted RQ3 outcomes.

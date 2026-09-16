# RQ3 — Transferable, interpretable dashboard Composer learning

**Latest operational boundary:** eight additional selection mechanisms have been
implemented for static review only. The user requests a pause before all tests,
preparation and model calls. See [successor v4](RQ3_experiments.md#selection-successor-v4);
its catalogue is not an automatically authorized run queue.

**Latest authority, 2026-09-14:** the current work is the full-remaining,
two-model AC@1 discovery tournament, with **evidence selection only** changed
after round 16. No model training, attention or preliminary inference subsets.
The older search/training route below is historical, not the next run queue.
See [the current contract](RQ3_experiments.md#selection-only).

Current authority (2026-09-12): [search-first successor](RQ3_experiments.md#search-first).
First test evidence policies, continuous composition and versioned Solver
instructions on small training subsets. Freeze the shortlist before the full
480-case pre-training evaluation; only after its target passes proceed to
small SFT/RL, then freeze a training recipe before full SFT/RL. The old action space and
execution schedule below are predecessor context. The user removed the total
call cap; all attempts must still be recorded. Existing results stay intact.

Status: **registered design; implementation and qualification in progress**.
The current user goal authorizes full SFT/RL/evaluation after CPU and bounded
live qualification pass. The former post-smoke stop boundary is superseded;
execution remains disabled until those prerequisites actually pass.

> Can a learned dashboard composer improve a frozen RCA solver's
> accuracy–cost trade-off, generalize to a training-held-out microservice
> application, and expose which evidence-selection and visualization
> decisions account for its gains?

Only Qwen3.5-9B, the Composer, is trained. It selects evidence cards and emits
a structured drawing program. A deterministic, RQ3-local renderer produces
one real telemetry dashboard. Frozen Qwen3.8-27B, the Solver, makes one RCA
call and returns the unchanged top-five JSON. This is not a multi-stage Solver
and does not train a critic, reward model, scorer, or the Solver itself.

The complete eligible evidence pool stays CPU-side. Under the user-approved
budget amendment, the Composer receives a deterministic, region/entity-diverse
candidate directory within its input budget, not every raw fact or card.
Directory coverage and exclusions are explicit; all selected card facts remain
unchanged. This retrieval boundary is part of the method and its limitations.

The main transport is purely visual incident evidence, with the shared task,
field explanations and exhaustive anonymous candidate list in text. A
screenshot of text is a separate control, not a real dashboard. Three-, four-
and five-digit case-local identities denote services, nodes and pods.

The 480 evaluation cases remain evaluation-only. All AegisLab and RE2-TT
cases are excluded from Composer training, validation and tuning because
both contain the TrainTicket application. Their evaluation cases remain in
the 480. TrainTicket is training-held-out for this study, not claimed unseen
in foundation-model pretraining or the project's past research.

## Why study this?

The completed fixed-P0 RQ2.1 experiments strengthen the case for testing a
learned policy without assuming it will win. Random evidence selection harms
both models; re-encoding the same facts as tables also harms both. Increasing
source resolution helps Qwen more than Gemma, while topology-centered layout
substantially harms Gemma. Content, representation and Solver interact: a
visually plausible design is not automatically a better diagnostic input.
See [current RQ2.1 findings](../../RQ2_1/findings/) and the detailed numerical
refinement in `RQ3_experiments.md`. Some selection canvases are infeasible:
their end-to-end zeros are not evidence that a model read them and reasoned
incorrectly. Strong text/TPV controls and legality reporting remain essential.

Event/window-connected groups are built before eval exclusion. Current targets
are 150 train / 70 validation per AIOPS dataset (300/140 total), with 38,000
planned calls plus 2,000 reserve. The earlier materialized split was 251/90;
the new split has passed complete May-source V3 processing and isolation checks.
It is registered in `results/registration_balanced_v3/`. Format SFT and its
140-case Composer validation are complete; RL and formal RCA evaluation remain
pending. Format/render success is not evidence of RCA improvement or transfer.

The clean-V3 [RQ1.1/RQ2.1 report](../../../docs/RQ1_1_RQ2_1_findings/findings.md) finds a useful
Qwen topology-visual baseline, substantial retrospective design headroom,
and no general guarantee that all-visual evidence improves diagnosis or
output-token cost. It also exposes tool profiles whose actual inputs were
identical. RQ3 therefore requires action-to-input observability, strong text
and TPV comparisons, strict training isolation and complete two-model cost
accounting. Historical oracle performance is not an expected learned result.

DashBot already studied RL dashboard generation. The contribution sought
here is verifiable utility for a frozen diagnostic Solver, transfer across
applications, and controlled separation of evidence choice and presentation.

This RQ explicitly supersedes the previous roadmap's allocation of
contribution identification and Composer RL to separate future RQs. It does
not revise the findings, code, inputs, or results of RQ1.1/RQ2.

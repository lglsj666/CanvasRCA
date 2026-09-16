# RQ3 qualitative roadmap

Current pause: implement and statically inspect the complementary selection
catalogue → report → wait for the user's instruction. Do not turn design
completion into automatic testing, rendering, inference or training.

Current route: [selection-only full-remaining tournament](RQ3_experiments.md#selection-only).
Review complementary diagnostic mechanisms → check public selection and actual
inputs → register one method on every remaining case for each model → record
newly covered signals and failures. Keep the last dashboard and Solver fixed.
Earlier small-subset and training routes below are superseded for current work.

Latest route: [search-first successor](RQ3_experiments.md#search-first).
Explore useful evidence policies and constrained continuous designs, shortlist
on validation, freeze a pipeline and complete its pre-training eval. Only after
the target is met, qualify small SFT/RL work and then freeze full training. Preserve
the earlier route below as predecessor context, not an automatic run queue.

Status: balanced data materialized; implementation and qualification in progress.
Earlier split artifacts remain historical. No formal run is enabled yet.
Numerical thresholds and budgets live in `RQ3_experiments.md`. The current goal
authorizes all registered work after CPU/live prerequisites actually pass.

| Evidence at the decision point | Next action |
|---|---|
| Isolated processed data cannot fill the equal dataset quotas | Extend and validate the registered source; never borrow eval or silently reduce one dataset |
| The mandatory shell or balanced catalogue cannot fit the budget | Stop before requests; never truncate candidates or open eval for tuning |
| Important root evidence exists in the pool but not the admitted catalogue | Attribute the failure to candidate retrieval; assess coverage before blaming Composer selection or Solver reasoning |
| A declared drawing action does not change evidence or pixels | Correct execution and audit no-ops before learning |
| Format is unreliable | Improve legal SFT examples/harness; do not claim poor RCA is merely infrastructure |
| Format works but RCA feedback adds no validation gain | Keep fixed and imitation baselines; investigate evidence selection and rendering instead of scaling blindly |
| Validation improves, but strong TPV or fixed controls win on eval | Report model/setting-limited result; do not promote the Composer |
| Seen-application gains fail on training-held-out TrainTicket | Report transfer failure without fine-tuning on its eval cases |
| Rendering gains depend on learned content | Explain the conditional interaction; do not assign context-free component credit |
| Solver tokens shrink but total system cost rises | Do not claim end-to-end savings; report the trade-off and deployment amortization |
| Stable quality/cost and transfer gains appear | Consider a later deployment/RQ, after attribution and failure review |

Predecessor sequence, superseded by the search-first route above: format SFT → utility RL and
equal-budget controls → validation-only checkpoint lock → one-time 480-case
comparison and registered interventions → three findings and project decision.
No training scorer, interactive Solver, or additional learning stage is
implicitly authorized by this roadmap.

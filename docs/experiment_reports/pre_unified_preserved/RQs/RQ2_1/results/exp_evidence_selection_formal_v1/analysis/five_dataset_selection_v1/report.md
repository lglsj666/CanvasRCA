# Five-dataset champion-selection audit

Date: 2026-09-09 UTC. Status: **offline, post-hoc, exploratory; no promotion**.
No model calls were made. Experiments remain user-paused. Existing inference,
the original 90-case selection artifact, and downstream results are unchanged.

## Method and scope

The audit uses all 480 cases, both models, and all eight **Vision** selection
policies: 7,680 logical result records. Vision remains the registered objective
for choosing the selector used by later dashboard experiments. Text results
remain mechanism controls; this audit does not choose a text-policy champion.

All five datasets participate. Compute the mean reciprocal rank (MRR: higher
means the correct root cause appears nearer the top) separately within each
model/dataset, then average the ten means equally. Dataset weights therefore
do not depend on whether that dataset contains 90 or 100 cases. Keep the
existing 95% legality/parse threshold, 0.05 per-cell adverse-delta veto, 0.01
MRR tie band, relative total-token cost and deterministic tie breakers.

For grouped five-fold assessment, each fold contains 96 cases: 20 per primary
dataset and 18 per RE2 dataset. In each round, select using the other 384,
then assess that selected policy on the 96 excluded cases. Related source
events stay together. Source groups are: AegisLab 98 (largest 2 cases),
AIOPS-2022 72 (largest 4), AIOPS-2025 100, RE2-OB 30 (3 each), and RE2-TT 30
(3 each). RE2 grouping includes repeated collection-condition identity and
overlapping telemetry intervals; private source metadata never enters models.

Also select on four complete datasets and assess the omitted fifth; repeat for
each dataset. A separate sensitivity leaves AegisLab and RE2-TT out together,
because both use TrainTicket. No seed, threshold or policy was tuned from these
checks. The all-data result's inherited `selection_only` field refers to the
explicitly supplied selection subset, **not** the superseded original 90 cases.

## All-data descriptive results

Each model column is an equal-weight average across five datasets. The joint
column averages the two model columns. These scores include registered model
failures and design-infeasible outcomes; no successful-cases-only filtering.

| Policy | Meaning | Qwen MRR | Gemma MRR | Joint MRR | Admissible under existing safeguards? |
|---|---|---:|---:|---:|---|
| P0 | Parent R1-PanelSelect-v14 | 0.366419 | 0.349111 | **0.357765** | Yes |
| P_TRACE_SC | Native trace support/confidence selection | 0.364593 | 0.348222 | 0.356407 | No |
| P_BARO_RS | BARO RobustScorer metric selection | 0.369167 | 0.314667 | 0.341917 | No |
| P_LOG_FREQ | Native log-template frequency selection | 0.324419 | 0.293222 | 0.308820 | No |
| P_DIVERSITY | Relevance/redundancy selection | 0.318593 | 0.295333 | 0.306963 | No |
| P_SIGMA | Native sigma metric selection | 0.311778 | 0.248778 | 0.280278 | No |
| P_COVERAGE | Entity/type coverage selection | 0.239241 | 0.191111 | 0.215176 | No |
| P_RANDOM | Hash-random selection | 0.147889 | 0.092000 | 0.119944 | No |

**P0 is both the unfiltered empirical joint-score leader and the only
admissible shared policy under these safeguards.** This is not a significance
claim. In particular, P0 exceeds P_TRACE_SC by only 0.001357 joint MRR.
P_TRACE_SC also falls from 0.45 to 0.39 for Gemma/AegisLab: a -0.06 change,
which crosses the pre-existing -0.05 veto. Every other challenger also crosses
the adverse-delta veto in at least one model/dataset cell. The veto is an
observed operational selection constraint, not proof of population-level harm.

| Assessment | Selected policy | Assessment delta versus P0 |
|---|---|---:|
| Five-fold grouped assessment | P0 in all five folds | 0.000000 |
| Five separate dataset-held-out checks | P0 in all five checks | 0.000000 |
| TrainTicket application-held-out sensitivity | P0 | 0.000000 |

All cross-fitted predictions reuse P0 outcomes because every fold selects P0.
The zero change is therefore an identity, not five independent replications
establishing statistical equivalence. These checks support retaining P0 under
this rule; **they do not demonstrate a new strategy that improves other data**.

For context, exploratory paired fixed-policy tests over all 480 cases give
P_TRACE_SC versus P0 Holm-adjusted p=1.0 for both models (14-comparison family).
Those pooled case-weighted tests have a different aggregation from the
five-dataset macro selection objective and do not prove equivalence. Full
per-dataset exploratory statistics are in `analysis.json`.

## Interpretation and limits

- An empirical champion, stability of a selection procedure, and demonstrated
  superiority on future data are different claims. No selector can guarantee
  the latter from these finite existing results.
- Cross-validation evaluates the **selection procedure** outside each fold's
  selection data. It is not an independent test of the final policy selected
  using all 480 cases.
- These project outcomes had already been inspected. This new analysis is
  post-hoc/exploratory, not restored preregistration or untouched confirmation.
- This audit retains a shared two-model Vision champion. It does not establish
  that P0 maximizes every individual model, dataset or text-only condition.
- Changing champion selection requires no new evidence-selection inference.
  Any future activation must separately reconcile the original P_TRACE_SC
  champion and partially completed downstream stage; nothing resumes here.

## Verification and reproduction

Ten CPU tests passed: grouping/coverage, deterministic folds, explicit RE2
participation, equal dataset weights, exclusion of held-out scores from
selection, failures retained, no-admissible handling, case-level cross-fitting,
application-held-out scope, and timestamp statistics validation. Terminal record
hashes, model/case/arm identities and full Vision target coverage were checked;
this was not a new rehash of every PNG, prompt and attention file.

- Code and protocol: `tmp/rq21_champion_selection/` from the repository root.
- Detailed immutable analysis: `analysis.json` in this directory, including
  fold membership, source identity hashes, result hashes and method hashes.
- [Cawley and Talbot, JMLR 2010](https://www.jmlr.org/papers/v11/cawley10a.html)
  explains finite-sample selection overfitting.
- [scikit-learn selection/evaluation example](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html)
  explains evaluating a selection procedure outside its selection data.
- [Grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html#group-k-fold)
  explains keeping related observations in one fold.

# Registered experiment

The [full plan](../../../docs/experiment_plans/RQ4_8_Card_Selection_Hybrid_Recovery_and_Valid_QA_Plan_2026-10-20.md)
and `configs/protocol_v1.json` define the experiment. Existing RCA answers are
historical engineering references. New QA on those inputs is a new measurement.
No private root, previous rank or previous QA error participates in compilation.

The single-call selector retains half the optional cards, matching hash modality
quotas. Global public identity/window cards use the G quota; observed-source
summaries use their explicit M/R source field, pair-statistic cards use R, metric
identity records use M, and log metadata use L. Only exhaustive candidates and
the public observation window are protected; other inventory cards are optional.

Rendering uses additive unified operations `card_subset` and
`card_statistic_label_swap`. Fixed and packed views retain original card pixels.
Packing compacts original columns and preserves original column-major ordering.
The small static prompt change replaces "complete/all incident observations"
with "supplied/available incident observations" for all new visual RCA conditions.
Time-restored hybrid instructions explicitly state that original sequences are
present. No additional diagnostic strategy is introduced by either correction.

Selection and QA output budgets are 2,048 tokens; final diagnosis remains 8,192.
These ceilings and unconstrained QA/selection generation are frozen before calls.
RCA retains the existing greedy services-array decoder and central scoring.
All model selection failures with no valid diagnostic card terminate without a
second call. Actual selected cardinality, display, token sets and costs are saved.

QA targets are chosen before card selection. All generated core questions are
single-answer, with accepted alternatives where required by visible relations.
The scorer additionally implements the user's required-multiple-values half-credit
policy and preserves strict/full correctness. Missing target support is recorded
separately from inability to read a retained target.

Primary families and all call budgets are fixed in the plan. A model-error zero
is different from an infrastructure unknown. Qualification failures do not
authorize outcome-driven retries or changes to the cohort.

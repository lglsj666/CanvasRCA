# exp_numeric_encoding_robustness

Status (2026-09-28): completed90-case development subset; paired common A/B
cohorts Qwen84/Gemma90. Earlier static-only status is historical.

See [full report](../../../docs/experiment_reports/RQ3_7_Results_Analysis_2026-09-28.md).

- Registered twelve-test equivalence MRR family: no adjusted significance.
- Qwen scientific-notation first-ID flips: T_MATCH12/84 vs repeat1/84;
  LOCAL_LINK10/84 vs repeat0/84. Added exploratory paired flip-vs-repeat
  twelve-test family gives Holm .011719/.021484 respectively. The image does
  not remove numeric lexical sensitivity. No oracle use of repeats.
- Actual unit applicability: Qwen22/Gemma23 common cases, all AegisLab; no-ops
  reuse native answers. LOCAL_LINK applicable-only MRR deltas−.106061/−.130435,
  not confirmed population effects. Small eligibility cohorts must be exposed.
- One Gemma REMOTE_ID UNIT answer reaches8192 output tokens, repeats zeros and
  has invalid JSON; original model-failure zero is retained. No resampling.
- One repeat is not the complete sampling distribution; label-free transforms
  still alter words/tokens/pixels even when numeric semantics and geometry agree.

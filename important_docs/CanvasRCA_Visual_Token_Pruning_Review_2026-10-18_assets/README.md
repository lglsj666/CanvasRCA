# Visual-token pruning retrospective — 2026-10-18

Companion to [the Chinese report](../CanvasRCA_Visual_Token_Pruning_Review_2026-10-18.md).
No new model calls, changed scores, experiments or diagnostic dashboards.

- `all_methods_metrics.csv`: independently reaggregated full-denominator
  metrics/costs for RQ4.1 references and 16 pruning conditions, 18 RQ4.3
  pruning-containing conditions and three RQ4.4 conditions, by dataset and ALL.
- `actual_mask_audit.csv`: 220 cases × six methods, intersecting actual
  committed indices with the same original A/E support. Outside A/E is not
  asserted to be semantically empty or exclusively blank pixels.
- `actual_mask_summary.csv`: per-case ratios averaged by dataset/ALL. The
  optional-slot fraction is defined only when all anchors are retained.
- `paired_valid_sensitivity.csv`: outcome-conditioned descriptive sensitivity;
  never a replacement for the 220-case main denominator.
- `retrospective_all_136_pairs.csv`: complete retrospective family for 16
  pruning conditions plus V_FULL. v11 and Pratt tests have distinct nulls;
  neither this family nor its significance replaces registered decisions.
- `descriptive_token_frontier.csv`: point-estimate token/MRR dominance across
  37 conditions; backend, evidence and rounding differences prevent a causal
  cross-run efficiency interpretation. Tiny output-token differences are not
  substantive system improvements.
- Six PNG figures: report graphics, not model inputs.
- `verification.json`: exact source hashes, aggregation checks and audit scope.
  Original response rescoring was done in the cited experiment reports; this
  new script checks their derived scores and actual selection records.

Reproduce from the repository root with existing NumPy/SciPy/Matplotlib:

```bash
PYTHONPATH=src python3 important_docs/CanvasRCA_Visual_Token_Pruning_Review_2026-10-18_assets/analyze.py
python3 important_docs/CanvasRCA_Visual_Token_Pruning_Review_2026-10-18_assets/populate_tables.py
OPENBLAS_NUM_THREADS=1 python3 important_docs/CanvasRCA_Visual_Token_Pruning_Review_2026-10-18_assets/diagnosis_mechanisms.py
OPENBLAS_NUM_THREADS=1 python3 important_docs/CanvasRCA_Visual_Token_Pruning_Review_2026-10-18_assets/diagnostic_output_audit.py
```

The scripts access no pretrained weights, make no network requests, change no
historical inputs/outputs, and import statistical utilities from `src/scorer`.
These are ordinary, directly readable report artifacts, not compressed archives
or copied historical conversations/images.

The deeper diagnostic analysis adds `mechanism_case_metrics.csv` (3,740
mask/response pairs), summaries and fault strata, exact rank transitions,
output-ID patterns and mask agreement. All are descriptive, retrospective
measurements; geometric support is not recoverability or semantic truth.
`mechanism_example_selection.json` records the outcome-stratified deterministic
selection, including empty strata. Six selected cases have 48 compact example
answers saved; 42 answers across seven arms were read for the new qualitative
audit. `mechanism_manual_case_audit.json` records checked source facts, paths,
limitations, three inspected original PNG hashes and a direct-distance
cross-check. It is not a population explanation-error-rate estimate.

`mechanism_verification.json` records source hashes and the exact accounting
identity separating tolerant-score differences from whole-answer validation
penalties. This identity is not a causal mediation analysis. Private accepted
IDs are used only for offline evaluation descriptions, never model inputs.

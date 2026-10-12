# Original champion: reporting-set check

Status: interim user-requested analysis of completed evidence selection; RQ2.1 is paused and the full suite is unfinished. No new champion is selected.

The original P_TRACE_SC winner was chosen on 90 cases (30 per primary dataset), Vision only. This analysis compares it with P0 on the other 210 primary cases (70 per dataset). RE2 eligibility has subsequently been amended; that does not retroactively change this historical winner or turn this into a five-dataset selection.

| Model | Paired cases | P0 V MRR | P_TRACE_SC V MRR | Delta | Raw Pratt p | Holm p | Paired dz | RR improved/worsened/tied |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| qwen3.8-27b | 210 | 0.275794 | 0.276190 | 0.000397 | 0.734350 | 1.000000 | 0.001283 | 28/25/157 |
| gemma-4-26b-a4b | 210 | 0.276190 | 0.238095 | -0.038095 | 0.116664 | 1.000000 | -0.108647 | 9/17/184 |

Neither model meets the registered +0.05 MRR and adjusted p<0.05 improvement rule. Qwen has a negligible observed positive difference; Gemma has an observed negative difference, not a statistically established harm. The equal-model reporting delta is -0.018849; models are not treated as independent extra cases for a pooled significance test.

Holm follows the existing analysis implementation: seven challengers, two representations and two models (28 contrasts), separately per dataset and reporting aggregate. Both primary Vision contrasts are already nonsignificant before correction. No confidence intervals are reported.

All 15,360 terminal trajectory hashes/identities passed; no whole-case infrastructure exclusion was required. Qwen P0 V retains one parse-failure outcome; champion Vision has none. No truncation or design infeasibility occurs in these paired P0/champion Vision rows. Valid reused calls remain paired outcomes, not new independent requests. The focused check did not repeat every image/attention artifact audit.

The companion JSON retains selection scores, all per-dataset T/V champion comparisons, error accounting, tokens, effect sizes and the full p-value families. Data were previously exposed in project research, so these are cases outside the original current-stage selection, not globally untouched confirmation. Do not switch champions using this reporting result and call that an independent validation. A failed superiority check does not invalidate the experimental records.

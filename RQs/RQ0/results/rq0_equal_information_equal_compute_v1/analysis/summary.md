# RQ0 equal-information/equal-compute results

Models analyzed: qwen3.6-27b, gemma-4-26b-a4b

| model | A MRR | B MRR | C MRR | Δ A−B | p Holm | Δ A−C | p Holm | supported |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| qwen3.6-27b | 0.3984 | 0.4113 | 0.3954 | -0.0129 | 0.3634 | +0.0030 | 0.642 | no |
| gemma-4-26b-a4b | 0.3901 | 0.4013 | 0.3623 | -0.0112 | 0.248 | +0.0278 | 0.02387 | no |

The table follows the preregistered +0.05 practical-effect threshold, paired Wilcoxon tests with Holm correction, per-dataset reversal gate, and parse/infrastructure completeness gates. No confidence intervals are reported.

Cross-architecture generalized support: **no**.

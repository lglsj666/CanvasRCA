# Kubernetes pod/service alias sensitivity

This is a post-hoc scoring sensitivity and does not replace the registered RQ0 result.

| model | arm | canonical MRR | alias-aware MRR | changed cases |
|---|---|---:|---:|---:|
| qwen3.6-27b | visual_text_topology | 0.3984 | 0.4046 | 9 |
| qwen3.6-27b | text_only | 0.4113 | 0.4161 | 7 |
| qwen3.6-27b | flat_structured | 0.3954 | 0.3995 | 6 |
| gemma-4-26b-a4b | visual_text_topology | 0.3901 | 0.3915 | 2 |
| gemma-4-26b-a4b | text_only | 0.4012 | 0.4075 | 9 |
| gemma-4-26b-a4b | flat_structured | 0.3623 | 0.3637 | 2 |

| model | comparison | alias-aware ΔMRR | Holm p |
|---|---|---:|---:|
| qwen3.6-27b | A_minus_B | -0.0115 | 0.4987 |
| qwen3.6-27b | A_minus_C | +0.0051 | 0.4987 |
| gemma-4-26b-a4b | A_minus_B | -0.0160 | 0.06467 |
| gemma-4-26b-a4b | A_minus_C | +0.0278 | 0.02278 |

The sensitivity asks whether the upstream scorer's documented service-level
leniency changes the scientific conclusion when it recognizes ordinary hashed
Kubernetes pod names. It cannot be used as a post-hoc replacement endpoint.

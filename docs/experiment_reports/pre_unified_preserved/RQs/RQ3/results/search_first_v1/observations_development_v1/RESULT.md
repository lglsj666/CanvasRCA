# SEARCH31 — Observed-value dashboard without metric z labels

Completed train-only exploration: 24 cases, 12 per AIOPS dataset. This is not
validation/evaluation or a target-achievement result. The same-window control
is `../unanchored_development_v1/`. Source facts and selected series stayed
unchanged; this explicitly registered derived-summary ablation withheld printed
metric signed-z labels and removed their static explanation.

| Dataset | N | Control MRR | New MRR | AC@1 | AC@3 | AC@5 | Input tokens | Output tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AIOPS-2022 | 12 | .381944 | .375000 | .333333 | .416667 | .416667 | 17725.00 | 274.08 |
| AIOPS-2025 | 12 | .500000 | .416667 | .333333 | .416667 | .583333 | 17619.83 | 266.58 |

One RR repair, two breaks, 21 ties. Both exploratory Pratt and Holm-adjusted
p-values are 1. Input is 50 static-guide tokens shorter per case; image tokens
remain 16,002. Outputs increased from 262.17/262.75 respectively. No promotion.

All 24 calls completed in 371.347 seconds; maximum 351 output tokens. No
infrastructure, parse, unknown-ID or truncation failure. All responses contain
five distinct allowed IDs. Full answers and one full conversation were read;
all 24 request/image/conversation/response hashes passed the artifact audit.
CPU regression: 244 passed. See `paired_review.json`, `metrics_breakdown.json`
and `logs/20260912_review.md`. No attention, Composer calls, training or eval.

# causal_integration_sft_pilot_v2_1 paired pilot analysis

This is a development-only model-selection diagnostic, not confirmatory evidence.

## Result

- Adapter−base MRR: **-0.0417** (0 improved, 1 degraded, 11 tied).
- Paired Cohen's d: -0.289; exact Wilcoxon p=1.000 over 1 nonzero pairs. The sample is too small for an efficacy claim.
- Top-1 changed on 1/12 cases; agreement was 91.7%.
- Mean prediction-list length changed from 4.33 to 4.83; mean output length changed from 112.92 to 103.42 tokens.

## Scored degradations

| opaque case | dataset | accepted root | base rank/list | adapter rank/list | ΔMRR |
|---|---|---|---|---|---:|
| `INC-622440744221` | aegislab | `ts-station-food-service` | 1 / ts-station-food-service, ts-food-service, ts-ui-dashboard | 2 / ts-station-food-service-cb9656f7b-nl4cb, ts-station-food-service, ts-food-service, ts-ui-dashboard, ts-order-service | -0.500 |

The scored degradation demoted an accepted root that the base model ranked first. Prediction-list preservation prevented list collapse but did not produce any correcting improvement.

## Decision

Do not promote or scale the causal_integration_sft_pilot_v2_1 checkpoint. Do not open formal or reserve cases.
Any successor must be preregistered on development data, use a fresh
development-heldout subset, and be evaluated against the base model with another
paired gate. RL/GRPO remains out of scope.

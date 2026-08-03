# Causal-integration SFT v1 paired pilot analysis

This is a development-only model-selection diagnostic, not confirmatory evidence.

## Result

- Adapter−base MRR: **-0.0694** (0 improved, 2 degraded, 10 tied).
- Paired Cohen's d: -0.418; exact Wilcoxon p=0.500 over 2 nonzero pairs. The sample is too small for an efficacy claim.
- Top-1 changed on 5/12 cases; agreement was 58.3%.
- Mean prediction-list length changed from 4.17 to 3.42; mean output length changed from 114.75 to 91.33 tokens.

## Scored degradations

| opaque case | dataset | accepted root | base rank/list | adapter rank/list | ΔMRR |
|---|---|---|---|---|---:|
| `INC-55AAEAD2FF27` | aiops2022 | `cartservice` | 3 / node-1, shippingservice, cartservice, paymentservice, emailservice | miss / shippingservice | -0.333 |
| `INC-A37C0F9830EB` | aegislab | `ts-security-service` | 2 / ts-admin-travel-service, ts-security-service, ts-ui-dashboard | miss / ts-admin-travel-service | -0.500 |

In both degradations the adapter returned one service and removed an accepted
root that the base model had retained lower in its ranking. There were no scored
improvements. The shortened output is therefore not an efficiency win: it is the
observed failure mechanism.

## Decision

Do not promote or scale the v1 checkpoint. Do not open formal or reserve cases.
Any v2 must first freeze a conservative preservation/correction target that retains
a five-service ranking, balances base-correct preservation with base-wrong
correction examples, uses a fresh development-heldout subset, and is evaluated
against the base model with another paired gate. RL/GRPO remains out of scope.

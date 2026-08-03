# 2026-07-31 Causal-integration SFT v2.1 result

**Scope:** development-only model-selection pilot  
**Decision:** rejected; no adapter promoted  
**Effect on RQ0:** none

## Why v2.1 was run

The v1 pilot taught only a two-service answer and caused prediction-list
collapse. Version 2 replaced that target with a five-service
preservation/correction ranking: the accepted root is first, while the
remaining positions preserve useful base alternatives and hard
symptom/evidence candidates. It also balances base-correct preservation cases
with base-wrong correction cases.

Before any optimizer step or v2 heldout call, a frozen 134-case base rollout
showed that AegisLab contained only three usable base-wrong development cases,
not the six required by the original symmetric roster. The feasibility result
was recorded rather than hidden or duplicated. The v2.1 amendment therefore
used 3 preservation + 3 correction AegisLab cases and retained 6 + 6 for each
of AIOPS-2022 and AIOPS-2025, for 30 training cases total. Correctness was not
redefined. The 12-case heldout set remained frozen and untouched.

The declared candidate-plan hash is
`aab989e2ba43b61c349dc52a5765a138ac32b895941f0137d21ef30d62ffb20a`;
the declared roster hash is
`3170e8acf21bfc1ca9b377c07df2350756938500051f79f7087548494053d239`.
Training/evaluation overlap, v1 model-selection overlap, and formal/reserve
overlap are all zero.

## Frozen recipe

- Base checkpoint: unquantized `models/Qwen3.6-27B`, BF16.
- LoRA: rank 8, alpha 16, dropout 0.05, language linear projections only.
- Sequence length 16,384; micro-batch 1; gradient accumulation 4.
- AdamW fused, learning rate `5e-5`, eight optimizer steps, checkpoints every
  two steps.
- Supervision: five ranked services for every preservation and correction
  example.
- Evaluation: paired base versus final adapter on 12 fresh
  `development_heldout_v2` incidents, four per primary dataset, with balanced
  condition order.
- Promotion gate: adapter-base macro MRR at least +0.05, parse rate at least
  0.95, no dataset delta below -0.10, and zero infrastructure failures.

No text-only SFT arm was run. This is a model-development pilot for the fixed
visual-text-topology pipeline, not an RQ0 modality comparison.

## Qualification and training

The exact three-partition optimizer smoke completed one optimizer step on one
RE2-OB, one AIOPS-2022, and one AIOPS-2025 development case. It passed protocol
qualification; neither correctness nor teacher-forced loss magnitude was a
gate. Wall time was 445.39 seconds and sampled physical GPU use peaked at
96,210 MiB.

The 30-case pilot completed all eight optimizer steps in 5,055.13 seconds. It
trained 58,363,904 of 27,415,092,464 parameters and sampled a physical GPU peak
of 96,213 MiB. The mean teacher-forced loss was 2.1258, recorded only as a
training diagnostic. The final diagnostic checkpoint is
`models/checkpoints/causal_integration_sft_pilot_v2_1/pilot_main/step-0008`;
its adapter SHA-256 is
`40f27ebaad3b64c71547e9002f96206c285966b10533952f54760ea7f5b5c42b`.

## Independent paired result

All 24 inference calls completed, all parsed, and none had an infrastructure
failure.

| condition | MRR | AC@1 | AC@3 | AC@5 | AVG@3 | AVG@5 | output tokens | wall time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 0.5444 | 0.5000 | 0.5833 | 0.6667 | 0.5278 | 0.5667 | 112.92 | 10.49 s |
| adapter | 0.5028 | 0.4167 | 0.5833 | 0.6667 | 0.5000 | 0.5500 | 103.42 | 12.88 s |

Adapter-base MRR was **-0.0417**: zero improved cases, one scored degradation,
and eleven ties. The exact Wilcoxon p-value is 1.000 over the single nonzero
pair and paired Cohen's d is -0.289. Per-dataset deltas were -0.1250 on
AegisLab and 0 on both AIOPS datasets. The pilot fails the registered macro
gate and the no-dataset-reversal gate.

Version 2 did fix the v1 failure mechanism: average answer-list length increased
from 4.33 for the base to 4.83 for the adapter, so there was no prediction-list
collapse. It nevertheless produced no correcting improvement. In the only
scored degradation, the adapter put a standard hashed Kubernetes pod for the
correct service first and the service itself second. The frozen upstream scorer
awarded rank 2 because its documented service-level leniency recognizes numeric
pod suffixes but not ordinary Deployment/ReplicaSet hashes. A post-hoc
Kubernetes-aware projection makes this pair a tie, not an improvement; the
adapter would still miss the +0.05 gate. The canonical pilot score is therefore
left unchanged while the evaluator mismatch is audited separately.

## Decision

Do not promote or scale v2.1. Nothing is copied to `models/best/`; formal and
reserve incidents remain unopened. Two conservative SFT pilots have now failed
to show any paired improvement, so case-level SFT is no longer the immediate
next experiment and RL/GRPO remains out of scope.

The subsequent audit rescored all 4,320 stored RQ0 trajectories. Alias-aware
A−B remained negative for Qwen (−0.0115) and Gemma (−0.0160), so the mismatch
does not explain RQ0. Future work must still freeze the corrected granularity,
but the next scientific step is to redirect VisionRCA toward a new,
independently testable visual contribution rather than rerunning adapters until
a positive number appears.

## Artifacts

- Configuration: `RQs/RQ0/configs/training/causal_integration_sft_v2_1.yaml`
- Frozen roster: `RQs/RQ0/configs/training/causal_integration_sft_v2_1_roster.json`
- Base rollout: `RQs/RQ0/results/causal_integration_sft_v2/base_rollouts/main/`
- Smoke: `RQs/RQ0/results/causal_integration_sft_smoke_v2_1/smoke_main/`
- Training: `RQs/RQ0/results/causal_integration_sft_pilot_v2_1/pilot_main/`
- Paired evaluation and analysis:
  `RQs/RQ0/results/causal_integration_sft_pilot_v2_1/evaluation/paired_main/`

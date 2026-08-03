# 2026-07-31 Case-level causal-integration SFT protocol and smoke

## Scope

The RQ0 confirmatory experiment did not support an accuracy advantage for the
visual-text topology-aware representation. The controlled follow-up showed
that both tested VLMs can read most atomic dashboard facts, while image-induced
case-level ranking changes more often broke a correct text answer than repaired
one. The next intervention is therefore **case-level causal-integration SFT**,
not generic chart-reading or atomic-grounding SFT.

This is a development-only, non-confirmatory training pilot. It does not use
any RQ0 formal or reserve incident and does not alter `dataset/`.

## Frozen data contract

The source is the already exposed `development` partition in
`RQs/RQ0/configs/partition_roster.json`. A deterministic seed-42 split was made
before evidence qualification. Cases used in the earlier v7 diagnostic were
prevented from entering the new development-heldout subset.

| Dataset | Total | Train | Development-heldout | Eligible total | Eligible train | Eligible heldout |
|---|---:|---:|---:|---:|---:|---:|
| AegisLab | 100 | 80 | 20 | 31 | 25 | 6 |
| AIOPS-2022 | 100 | 80 | 20 | 87 | 69 | 18 |
| AIOPS-2025 | 93 | 74 | 19 | 61 | 48 | 13 |
| RE2-OB | 90 | 90 | 0 | 90 | 90 | 0 |
| **Total** | **383** | **324** | **59** | **269** | **232** | **37** |

The frozen roster is
`RQs/RQ0/configs/training/causal_integration_sft_v1_roster.json`, with declared hash
`4b22295b74b3395e9b01f3e88a7356994981660756a32f2b3d333584325e2f74`.
The formal/reserve overlap is zero.

### Supervision eligibility

The label-blind model input is compiled first from renderer v7 and
`CanonicalEvidenceBundleV1`. Ground truth is consulted only afterward to make
the assistant target and decide eligibility. An example is retained only when:

1. its accepted labels collapse to one service-level root;
2. that root has an exact or evaluator-equivalent candidate identifier;
3. the input contains visible root evidence; and
4. the propagation panel contains a visible non-root symptom that can be used
   as a hard ranking contrast.

Of 114 exclusions, 87 had ambiguous multi-root labels and 27 had no visible
root evidence. Among the 269 retained examples, 173 contain a visible
caller-to-root path; the other 96 supervise the registered distinction that
propagation onset rank is not causal rank. The target ranks the accepted root
first and one evidence-visible hard symptom second. It never invents a metric,
edge, onset, or symptom that is absent from the input.

## Frozen pilot selections

- Optimizer smoke: exactly one train case from RE2-OB, AIOPS-2022, and
  AIOPS-2025 (three examples).
- Pilot train: eight eligible train examples per primary dataset, 24 total.
- Pilot evaluation: four eligible development-heldout examples per primary
  dataset, 12 total.

Pilot train and pilot evaluation are disjoint. The 24 training inputs range
from 9,095 to 13,669 tokens; the 12 evaluation inputs range from 9,056 to
13,139. All are below the frozen 16,384-token training limit. The smoke's
longest example was 14,283 tokens, so the pilot does not exceed the already
qualified memory workload.

## Training implementation

The project-owned entry point is:

```bash
venvs/train/bin/python -m vlmrca.training.train \
  --config RQs/RQ0/configs/training/causal_integration_sft_v1.yaml \
  --mode smoke|pilot
```

It uses the local unquantized Qwen3.6-27B checkpoint in BF16, rank-8 LoRA over
all 496 language-layer linear projections, gradient checkpointing, one
multimodal example per microbatch, and a fused AdamW optimizer. There are
58,363,904 trainable parameters out of 27,415,092,464 total (0.213%). The
vision encoder and all non-adapter base weights remain frozen.

FlashAttention 2 is used for full-attention layers. The Gated DeltaNet chunk
operator uses `flash-linear-attention` 0.5.2. The host does not have local
`nvcc`, so `causal-conv1d` could not be built and that small depthwise
convolution uses the Transformers PyTorch fallback; this exception is recorded
in `RQs/RQ0/configs/training/software_lock.json` and every run contract. No
quantization or artificial GPU-memory-fraction cap is used.

Each run freezes config, selected opaque IDs and artifact hashes, roster and
split hashes, checkpoint lock, local source hashes, environment versions, and
the effective LoRA recipe before the optimizer. It writes per-case
conversations and trajectories plus detailed/brief logs asynchronously.

## Three-case optimizer smoke result

The registered smoke at
`RQs/RQ0/results/causal_integration_sft_smoke_v1/smoke_main` passed with no protocol,
numerical, or infrastructure failure:

- three required datasets and three frozen train cases were exercised;
- all inputs completed forward and backward passes;
- all teacher-forced losses were finite;
- one gradient-accumulated optimizer step completed;
- the adapter and resumable optimizer checkpoint were saved under
  `models/checkpoints/causal_integration_sft_smoke_v1/smoke_main/step-0001`;
- accuracy and loss magnitude were not used as pass criteria.

The three per-case losses were 2.2801, 1.9159, and 2.4856; their mean was
2.2272. These values only establish numerical integrity.

PyTorch's CUDA allocator reported more virtual reserved bytes than the physical
device capacity, so that counter must not be described as physical residency.
Direct `nvidia-smi` observation reached about 96.1 GiB used including display
processes. The pilot runner therefore records both allocator bookkeeping and a
separate 0.5-second physical-memory sample stream.

## Pilot decision rule

After the 24-example pilot, the frozen 12-case development-heldout set will run
paired base and adapter inference through the unified vLLM client. Promotion
requires all of:

- adapter minus base macro MRR at least +0.05;
- adapter parse rate at least 0.95;
- no dataset MRR delta below -0.10; and
- zero infrastructure failures.

This gate only decides whether to continue the SFT direction and save the
adapter under `models/best/`. It is not evidence for RQ0 and does not authorize
opening formal or reserve incidents.

## Completed pilot training

The 24-example pilot completed at
`RQs/RQ0/results/causal_integration_sft_pilot_v1/pilot_main`:

- six optimizer steps completed in 2,925.65 seconds (48.76 minutes);
- the mean teacher-forced loss was 1.8211, reported only as a training-integrity
  observation rather than an independent quality metric;
- all 24 episodes produced finite losses and full conversation/trajectory
  artifacts;
- the sampled physical peak was 96,252 MiB including display processes;
- checkpoints were saved at steps 2, 4, and 6; and
- the step-6 adapter SHA-256 is
  `c523ef4224c006c4884f11aed6bd8627fcfe7d13beca8523924cfc9d5dc6e8ce`.

The final checkpoint was loaded beside the base model through vLLM. vLLM
accepted every language-layer adapter target and ignored no target that exists
in the adapter. The paired evaluator then made 24 successful calls, with an
exactly balanced base/adapter call order and matching preflight/server token
counts.

## Independent paired evaluation

| condition | MRR | AC@1 | AC@3 | AC@5 | AVG@3 | AVG@5 | parse | output tokens | wall time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 0.5444 | 0.4167 | 0.6667 | 0.7500 | 0.5556 | 0.6167 | 1.000 | 114.75 | 9.46 s |
| adapter | 0.4750 | 0.4167 | 0.5000 | 0.5833 | 0.4722 | 0.5000 | 1.000 | 91.33 | 11.52 s |

Adapter−base MRR was **−0.0694**: zero cases improved, two degraded, and ten
tied. Top-1 changed in 5/12 cases. The two-sided exact Wilcoxon result over the
two nonzero pairs is p=0.500 and paired Cohen's d is −0.418; this small pilot is
not an efficacy test, but the direction is sufficient to reject promotion under
the frozen development gate.

Per-dataset adapter−base MRR was −0.1250 on AegisLab, −0.0833 on AIOPS-2022,
and 0.0000 on AIOPS-2025. The gate failed both its +0.05 macro requirement and
its no-dataset-below-−0.10 requirement. Parse and infrastructure requirements
passed. No adapter was copied to `models/best/`.

## Failure analysis and decision

The trained target contains exactly two services: the accepted root and one
hard propagated symptom. On evaluation, the adapter reduced the average
prediction-list length from 4.17 to 3.42 and the output length from 114.75 to
91.33 tokens. In both scored degradations it collapsed to a single service and
removed an accepted root that the base model had retained at rank 2 or 3. There
were no offsetting improvements. The apparent brevity is therefore the observed
accuracy failure mechanism, not an efficiency win.

The checkpoint is rejected. Do not scale v1, do not open formal/reserve cases,
and do not introduce RL/GRPO. A possible v2 must first freeze a conservative
preservation/correction design: retain a five-service target, balance
base-correct preservation examples against base-wrong correction examples, use
a fresh development-heldout subset, and apply another paired base/adapter gate.
The current 12 evaluation incidents are now development-exposed and cannot be
reused for v2 model selection.

The machine-readable and human-readable case audit is under
`RQs/RQ0/results/causal_integration_sft_pilot_v1/evaluation/paired_main/analysis/`.

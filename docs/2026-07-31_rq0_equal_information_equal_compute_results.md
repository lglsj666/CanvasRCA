# RQ0 equal-information/equal-compute confirmatory results

**Completed:** 2026-07-31  
**Experiment:** `rq0_equal_information_equal_compute_v1`  
**Registered plan:** `plans/2026-07-29_rq0_equal_information_equal_compute_plan.md`

## Executive conclusion

RQ0 is **not supported** for either tested VLM, and therefore is not supported
as a cross-architecture claim.

Under the registered equal-information and equal-inference-opportunity protocol,
the visual–text topology-aware arm (A) did not outperform the byte-identical
text arm (B):

- Qwen3.6-27B: ΔMRR A−B = **−0.0129**, Holm-adjusted p = 0.3634.
- Gemma-4-26B-A4B-it: ΔMRR A−B = **−0.0112**, Holm-adjusted p = 0.2480.

Against the flat structured arm (C), A was nearly tied on Qwen
(ΔMRR = +0.0030, adjusted p = 0.6420) and had a statistically detectable but
small advantage on Gemma (ΔMRR = +0.0278, adjusted p = 0.0239). The Gemma
effect is below the preregistered minimum practically important effect of
+0.05 and cannot satisfy RQ0 because A also failed to beat B.

This is evidence against the claim that adding the current dashboard image to
the same textual evidence improves frozen-model RCA. It is not proof that
visual observability can never help after different visual grounding,
representation learning, or agentic interaction.

## Confirmatory protocol and integrity

- Data: 240 previously unexposed incidents from each of AegisLab, AIOPS-2022,
  and AIOPS-2025; 720 incidents total.
- Arms per incident:
  - A: visual–text topology-aware dashboard plus the common evidence text.
  - B: the exact same deterministic evidence text without an image.
  - C: stable JSONL records generated from the same atomic facts.
- Formal calls: 720 × 3 = 2,160 per model; 4,320 total.
- Models: unquantized BF16 Qwen3.6-27B and Gemma-4-26B-A4B-it.
- Decoding: one shot, temperature 0, top-p 1, seed 42, 32,768 context and
  16,384 maximum output tokens.
- All 720 CEBs passed leakage, atomic-fact parity, deterministic rendering,
  serializer round-trip, and token-budget checks.
- Both models passed 60-pair same-process and 60-pair cross-process
  determinism gates with exact inputs, responses, predictions, and MRR.
- Qwen produced 2,154 parseable results and six model parse failures
  (99.72% parse rate); Gemma produced 2,160/2,160 parseable results.
- There were no infrastructure-result rows, no truncations, no unpaired
  case-arm records, and no protocol-integrity failures.
- The three arms each contain 720 records, and each dataset contributes 720
  arm-level records per model.

The registered compute definition fixes the checkpoint, hardware, precision,
context/output ceilings, one-shot opportunity, decoding, and retry policy. It
does not claim identical realized FLOPs. Actual tokens and GPU/wall time are
reported below.

## Primary results

| Model | Arm | MRR | AC@1 | AC@3 | AC@5 |
|---|---|---:|---:|---:|---:|
| Qwen3.6-27B | A — visual+text+topology | 0.3984 | 0.3000 | 0.4819 | 0.5528 |
| Qwen3.6-27B | B — text-only | **0.4113** | **0.3222** | **0.4875** | 0.5569 |
| Qwen3.6-27B | C — flat structured | 0.3954 | 0.2889 | 0.4653 | **0.5861** |
| Gemma-4-26B-A4B-it | A — visual+text+topology | 0.3901 | 0.2847 | 0.4708 | 0.5722 |
| Gemma-4-26B-A4B-it | B — text-only | **0.4013** | **0.3000** | **0.4778** | **0.5833** |
| Gemma-4-26B-A4B-it | C — flat structured | 0.3623 | 0.2611 | 0.4347 | 0.5444 |

| Model | Comparison | ΔMRR | Cohen's dz | Wilcoxon p | Holm p | Registered decision |
|---|---|---:|---:|---:|---:|---|
| Qwen3.6-27B | A−B | −0.0129 | −0.0573 | 0.1817 | 0.3634 | not supported |
| Qwen3.6-27B | A−C | +0.0030 | +0.0112 | 0.6420 | 0.6420 | not supported |
| Gemma-4-26B-A4B-it | A−B | −0.0112 | −0.0505 | 0.2480 | 0.2480 | not supported |
| Gemma-4-26B-A4B-it | A−C | +0.0278 | +0.1062 | 0.0119 | 0.0239 | positive but below +0.05 |

No confidence intervals are reported, as preregistered.

### Per-dataset ΔMRR

| Model | Comparison | AegisLab | AIOPS-2022 | AIOPS-2025 |
|---|---|---:|---:|---:|
| Qwen3.6-27B | A−B | +0.0092 | −0.0084 | −0.0394 |
| Qwen3.6-27B | A−C | +0.0263 | +0.0064 | −0.0237 |
| Gemma-4-26B-A4B-it | A−B | −0.0101 | −0.0221 | −0.0013 |
| Gemma-4-26B-A4B-it | A−C | +0.0333 | +0.0394 | +0.0107 |

The failure to beat text is not caused by one isolated dataset: Gemma is
negative on all three, while Qwen has only a +0.0092 AegisLab difference and is
negative on both AIOPS datasets.

## Did the models use the image?

The answer is “sometimes, but not beneficially enough.”

In the formal runs, A and B top-1 predictions agree on 74.4% of Qwen cases and
69.6% of Gemma cases. Thus, the image-conditioned arm often changes the model's
decision. The changes are not directionally helpful:

- Qwen A vs B: A fixes 20 B errors but breaks 36 B-correct cases.
- Gemma A vs B: A fixes 22 B errors but breaks 33 B-correct cases.

The nonconfirmatory 12-case development probes support the same interpretation.
Whole-image swaps reduced exact full-ranking agreement to 16.7% for both
models, although top-1 agreement remained 91.7% for Qwen and 75.0% for Gemma.
Changing image/text order also changed rankings. These probes show visual/order
sensitivity, not a confirmatory accuracy benefit, and were not used to change
the formal input.

## Realized compute and efficiency

| Model | Arm | Mean input tokens | Mean output tokens | Mean wall time | Sampled GPU-active time |
|---|---|---:|---:|---:|---:|
| Qwen3.6-27B | A | 10,598.5 | 112.1 | 8.27 s | 6.15 s |
| Qwen3.6-27B | B | 9,028.5 | 114.2 | 7.96 s | 6.17 s |
| Qwen3.6-27B | C | 9,670.1 | 104.6 | 7.55 s | 5.72 s |
| Gemma-4-26B-A4B-it | A | 9,680.1 | 80.5 | 3.64 s | 1.48 s |
| Gemma-4-26B-A4B-it | B | 9,418.1 | 81.3 | 2.95 s | 1.65 s |
| Gemma-4-26B-A4B-it | C | 10,105.2 | 78.2 | 2.89 s | 1.54 s |

A is not accuracy/latency Pareto-superior to B for either model. Qwen A also
uses more input tokens than both baselines. Gemma A uses fewer input tokens than
C but takes longer and gains only +0.0278 MRR, so this is a trade-off rather
than a Pareto result.

## Pre-formal runtime amendments

The planned CUDA-graph runtime failed Qwen's cross-process determinism gate.
With CUDA graphs, asynchronous scheduling disabled, fixed cuBLAS workspace, and
the first valid Triton configuration pinned, 7/60 predictions still differed
across process restarts and two changed MRR. vLLM 0.24.0's supported online
batch-invariant mode cannot be used because it explicitly rejects Qwen3.6's
`GDN_ATTN`.

Before formal inference, the runtime was therefore amended to eager execution.
Under eager execution, both same-process and cross-process gates passed 60/60
exactly for both models. This change applies equally to all arms and preserves
the checkpoint, BF16 precision, evidence, prompts, decoding, and inference
budgets; it trades throughput for reproducibility.

Gemma initially selected a FlashInfer CUTLASS MoE kernel that attempted a local
nvcc JIT. This host has the CUDA runtime/driver but not nvcc. Before any Gemma
result was produced, its MoE backend was fixed to vLLM's Triton implementation
and unused video input was disabled. The 0.65 GPU-memory ceiling was not raised.

## Interpretation

1. The current frozen VLMs do not convert redundant visual encoding into better
   RCA than a complete natural-language serialization of the same evidence.
2. Natural-language evidence is the strongest representation in both models.
   B−C is +0.0159 MRR for Qwen and +0.0390 for Gemma (descriptive, not a
   registered primary comparison).
3. Gemma's A−C result indicates that A can be better than flat JSONL, but A
   differs from C in both natural-language form and image availability. Because
   A loses to byte-identical B, this result cannot be attributed to a useful
   image increment.
4. The image is not simply ignored: it changes rankings. The problem is that
   its changes help fewer cases than they hurt against text-only.
5. AIOPS-2025 remains the hardest dataset for every arm and is where Qwen's
   visual increment is most negative. The result is consistent with weak
   topology/evidence alignment being a limiting condition, but modifier
   analyses are descriptive and do not rescue the primary hypothesis.

## Decision and next work

1. Treat frozen-model RQ0 as answered: **unsupported**, not “rerun until
   positive.” Do not tune prompts/renderers on these 720 formal cases or replace
   them with reserve cases.
2. Perform a label-blind descriptive audit of the registered discordant sets,
   especially the 36 Qwen and 33 Gemma cases where B is top-1 correct and A is
   wrong, versus the smaller A-helped sets. This should diagnose whether the
   image causes severity salience, topology-direction, or onset-order errors.
3. Add development-only atomic visual grounding tests: read panel values,
   compare onset order, identify directed edges, and link a chart to its service.
   These tests separate perception failure from RCA reasoning failure.
4. If the project continues to pursue a visual advantage, make it a new,
   explicitly preregistered intervention question. The most defensible next
   intervention is visual atomic-grounding SFT followed by case-level RCA SFT,
   evaluated on genuinely fresh reserve incidents. The current RQ0 result
   cannot be overwritten by that follow-up.
5. Treat image/text ordering and agentic zoom as separate future RQs with equal
   tool/call budgets. The 12-case order probe is hypothesis-generating only.

### Follow-up status

The discordance audit, atomic grounding tests, topology-edge legibility
intervention, and paired renderer-v7 development RCA test are now complete.
The large edge key makes topology readable but does not yield a stable
cross-model case-level benefit. See
[`2026-07-31_rq0_followup_grounding_topology_and_v7_results.md`](2026-07-31_rq0_followup_grounding_topology_and_v7_results.md).

### Post-hoc Kubernetes service-alias sensitivity

The frozen upstream scorer's documented service-level leniency recognizes
numeric pod suffixes but not ordinary Kubernetes Deployment/ReplicaSet hashes.
This mismatch was discovered during the later SFT v2.1 failure audit. A read-only
post-hoc sensitivity rescored all 4,320 stored trajectories with the canonical
rule plus hashed-pod-to-service projection, while retaining exact matching for
pod-level and node-level ground truth.

| model | A alias-aware MRR | B alias-aware MRR | C alias-aware MRR | A−B | A−C |
|---|---:|---:|---:|---:|---:|
| Qwen3.6-27B | 0.4046 | 0.4161 | 0.3995 | −0.0115 | +0.0051 |
| Gemma-4-26B-A4B-it | 0.3915 | 0.4075 | 0.3637 | −0.0160 | +0.0278 |

The extension changes 22/2,160 Qwen episodes and 13/2,160 Gemma episodes, all
on AegisLab. It does not rescue the visual arm: A remains below B for both
architectures, and no A comparison reaches the registered +0.05 threshold.
Therefore this genuine evaluator defect does **not** explain the unsupported
RQ0 result. The registered endpoint remains the primary result; the full
sensitivity artifact is under
`RQs/RQ0/results/rq0_equal_information_equal_compute_v1/diagnostics/kubernetes_service_alias_sensitivity/`.

## Artifacts

- Machine-readable analysis: `RQs/RQ0/results/rq0_equal_information_equal_compute_v1/analysis/rq0_analysis.json`
- Compact generated summary: `RQs/RQ0/results/rq0_equal_information_equal_compute_v1/analysis/summary.md`
- Qwen formal trajectories: `RQs/RQ0/results/rq0_equal_information_equal_compute_v1/qwen3.6-27b__formal__main/trajectories/episodes.jsonl`
- Gemma formal trajectories: `RQs/RQ0/results/rq0_equal_information_equal_compute_v1/gemma-4-26b-a4b__formal__main/trajectories/episodes.jsonl`
- Qualification reports and frozen artifacts: `RQs/RQ0/results/rq0_equal_information_equal_compute_v1/qualification_formal/`
- Determinism reports: `RQs/RQ0/results/rq0_equal_information_equal_compute_v1/qualification_determinism/`
- Development perception probes: `RQs/RQ0/results/rq0_equal_information_equal_compute_v1/qualification_perception/`

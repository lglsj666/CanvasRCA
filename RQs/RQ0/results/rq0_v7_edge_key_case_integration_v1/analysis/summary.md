# Renderer-v7 edge-key case-integration diagnostic

Scope: paired one-shot RCA on 12 previously exposed development incidents
(four per dataset). The v6 and v7 conditions use byte-identical evidence
text and atomic facts; v7 changes only the duplicated visual edge primitive.
This is nonconfirmatory and cannot alter the registered RQ0 result.

| model | v6 MRR | v7 MRR | ΔMRR | improved / degraded / tied | top-1 changed | v6 image tokens | v7 image tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen3.6-27b | 0.3542 | 0.3333 | -0.0208 | 0 / 1 / 11 | 1/12 | 1570 | 1962 |
| gemma-4-26b-a4b | 0.2986 | 0.3611 | +0.0625 | 1 / 0 / 11 | 3/12 | 262 | 272 |

Qwen has one degraded case and no improved cases; Gemma has one improved
case and no degraded cases. Eleven of twelve cases tie within each model.
The opposing means are therefore each driven by one incident, not a broad
shift. No significance test is appropriate for this selected n=12 diagnostic.

| model | AegisLab Δ | AIOPS-2022 Δ | AIOPS-2025 Δ |
|---|---:|---:|---:|
| qwen3.6-27b | +0.0000 | -0.0625 | +0.0000 |
| gemma-4-26b-a4b | +0.0000 | +0.0000 | +0.1875 |

Every real call parsed successfully, none truncated or failed at the
infrastructure layer, all server token counts match preflight counts, and
all 24 within-model prompt-text hashes pair exactly. Frozen artifact checks
also establish identical CEB fact hashes and pixel-identical base dashboards.

## Decision

Renderer v7 passes atomic edge legibility but does not show a cross-model
case-level benefit. Do not run it on the fresh reserve set and do not present
it as a repaired RQ0 result. The diagnostic separates perception from
integration: the models can read the explicit edge key, yet usually keep the
same RCA answer and occasionally move in opposite directions.

Generic visual-grounding SFT is not justified. The next learning experiment
should target cause-versus-propagated-symptom integration with case-level
supervision and explicit causal-direction rationales. Before GPU training,
freeze a training/validation exposure ledger, unified LoRA entry point, and
an evaluation set that excludes the 720 RQ0 formal cases and these 12
development cases. RL/GRPO remains out of scope for the current paper.

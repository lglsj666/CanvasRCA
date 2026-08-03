# RQ0 follow-up: grounding, topology legibility, and renderer-v7 integration

**Completed:** 2026-07-31  
**Scope:** development-only, nonconfirmatory follow-up  
**Confirmatory RQ0 status:** unchanged — unsupported

## Executive conclusion

The current VLMs can read most dashboard facts, and a large explicit edge key
makes topology direction readable to both architectures. That perception fix
does **not** produce a stable case-level RCA improvement.

- Qwen3.6-27B, paired v7−v6 on 12 development incidents: ΔMRR **−0.0208**
  (0 improved, 1 degraded, 11 tied).
- Gemma-4-26B-A4B-it: ΔMRR **+0.0625**
  (1 improved, 0 degraded, 11 tied).

Each mean is driven by one incident, and the directions disagree. Renderer v7
therefore remains a useful development artifact but does not advance to the
fresh reserve set. The next bottleneck is cause-versus-propagated-symptom
integration, not generic OCR or chart grounding.

## Why this follow-up was needed

The confirmatory RQ0 experiment found that visual+text did not beat
byte-identical text on either architecture. It also showed that the image was
not simply ignored: visual input changed the formal top-1 prediction in 21–22%
of cases and broke more text-correct predictions than it repaired.

The follow-up therefore asked three sequential diagnostic questions:

1. What visual salience signatures accompany harmful changes?
2. Can the models read the dashboard's individual facts?
3. If the shared unreadable primitive is repaired, does that improve RCA?

This sequence was run only on already exposed development incidents. The 720
formal incidents were not rerendered, tuned on, or reused.

## 1. Formal discordance audit

| model | top-1 changed | text correct / visual wrong | visual correct / text wrong |
|---|---:|---:|---:|
| Qwen3.6-27B | 153/720 (21.2%) | 36 | 20 |
| Gemma-4-26B-A4B-it | 158/720 (21.9%) | 33 | 22 |

Among text-correct/visual-wrong cases, the new visual top-1 was propagation
onset rank 1 and severity rank 1 in 41.7% of Qwen cases and 75.0% of Gemma
cases. This is descriptive rather than causal, but it identifies a consistent
salience risk: the image can pull the model toward the most visually prominent
propagated symptom.

## 2. Atomic visual-grounding diagnostic

Twelve development dashboards (four per dataset) were tested with seven
multiple-choice pixel-reading tasks under actual-image, same-dataset
swapped-image, and no-image conditions. This produced 72 model calls and 504
scored task answers.

| model | actual, all tasks | swapped | no image | actual, valid controls | swapped | no image |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.6-27B | 85.7% | 36.9% | 34.5% | 83.3% | 29.2% | 23.6% |
| Gemma-4-26B-A4B-it | 64.3% | 36.9% | 28.6% | 61.1% | 30.6% | 16.7% |

`metric_pattern` is excluded from the valid-control columns: all 12 keys were
`increase`, and both no-image models reached 100%. It is a failed diagnostic,
not visual evidence.

Actual-image accuracy by task shows a localized defect rather than broad
perception failure:

| task | Qwen | Gemma |
|---|---:|---:|
| metric identity | 100.0% | 75.0% |
| log table | 83.3% | 66.7% |
| trace table | 91.7% | 50.0% |
| propagation order | 100.0% | 91.7% |
| propagation time | 100.0% | 75.0% |
| curved topology edge | **25.0%** | **8.3%** |

The models read ordered propagation rows and times but cannot reliably recover
the faint curved call edges.

## 3. Explicit topology-edge intervention

The renderer-v6 image was left pixel-identical and a visual-only directional
rank-pair key was appended. The compact and large variants used the same 12
cases, task keys, actual/swapped/no-image controls, and deterministic decoding.

| visual primitive | Qwen actual | Qwen swapped | Qwen no image | Gemma actual | Gemma swapped | Gemma no image |
|---|---:|---:|---:|---:|---:|---:|
| renderer-v6 curved edge | 25.0% | 0.0% | 16.7% | 8.3% | 16.7% | 0.0% |
| compact edge key | 100.0% | 0.0% | 8.3% | 41.7% | 8.3% | 0.0% |
| large edge key | **100.0%** | 25.0% | 8.3% | **91.7%** | 0.0% | 0.0% |

Gemma's actual-image accuracy rises by 50 percentage points when the key is
enlarged, even though its mean image-token count changes only from 268 to 272.
Qwen is already at 100% with the compact key. The large key passes the post-hoc
operational cross-model legibility criterion (at least 90% actual accuracy and
at least 50 points over the stronger control).

The original curved-edge and explicit-key questions are not identical, so this
is a qualification comparison rather than a causal effect estimate. It
nonetheless establishes that scale and density are material for topology
readability.

## 4. Renderer-v7 case-level integration

The qualified large key was moved from the diagnostic script into
`DashboardConfig.topology_edge_key` and frozen as the development-only
`rq0_v7_edge_key` preset. Renderer version was advanced to 7. The default is
`none`, so the key is an explicit ablation axis rather than an implicit visual
change.

For every paired incident:

- the v6 base dashboard and the base portion of v7 are pixel-identical;
- both conditions have the same CEB atomic-fact inventory hash;
- both prompts contain byte-identical evidence text and instructions;
- the key only repeats directed edges already present in the CEB and common
  text;
- condition order is balanced deterministically by opaque incident hash.

| model | v6 MRR | v7 MRR | ΔMRR | improved / degraded / tied | top-1 changed | v6 image tokens | v7 image tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.6-27B | 0.3542 | 0.3333 | −0.0208 | 0 / 1 / 11 | 1/12 | 1,570 | 1,962 |
| Gemma-4-26B-A4B-it | 0.2986 | 0.3611 | +0.0625 | 1 / 0 / 11 | 3/12 | 262 | 272 |

Per-dataset means expose the single-case dependence: Qwen changes only on
AIOPS-2022 (mean Δ −0.0625), while Gemma changes only on AIOPS-2025
(+0.1875). AegisLab is exactly tied for both. This selected n=12 diagnostic is
not suitable for a significance test or a general accuracy claim.

## Integrity and compute

The follow-up produced 264 real model calls:

- atomic grounding: 72;
- compact and large edge-key qualification: 144;
- paired case-level v6/v7 RCA: 48.

All actual-image atomic/key calls parsed. All 48 case-level calls parsed, with
no infrastructure failures or truncations and exact server/preflight token
agreement. Gemma produced three formatting failures in each no-image edge-key
control; these were retained as model outcomes and do not affect the
actual-image qualification.

All calls used the unified BF16, unquantized, eager vLLM recipe with 32,768
context, 16,384 maximum output tokens, temperature 0, top-p 1, seed 42, and
`gpu_memory_utilization=0.65`. No model training was run. Shutdown-time vLLM
`EngineDeadError` messages occurred only after SIGINT on idle servers and are
not experiment failures.

## Decision and next work

1. RQ0 remains **unsupported**. Renderer tuning cannot overwrite a completed
   confirmatory result.
2. Do not run renderer v7 on fresh reserve incidents yet. Atomic readability
   is necessary but was not sufficient for a cross-model RCA benefit.
3. Do not start generic visual-grounding SFT. Most dashboard atoms are already
   readable, and the isolated edge defect has a rendering intervention.
4. The next learning experiment should be case-level causal-integration SFT:
   supervise the distinction between an origin and a visually severe/onset-early
   propagated symptom, with explicit caller→callee reasoning.
5. Before training, freeze a unified LoRA entry point, train/validation exposure
   ledger, supervision schema, and a genuinely unused evaluation set excluding
   the 720 formal cases and these 12 development cases.
6. RL/GRPO remains outside the current paper, consistent with `Codex.md`.

## Artifacts

- Discordance audit:
  `RQs/RQ0/results/rq0_equal_information_equal_compute_v1/diagnostics/discordance/`
- Atomic grounding:
  `RQs/RQ0/results/rq0_atomic_visual_grounding_v1/analysis/`
- Topology qualification:
  `RQs/RQ0/results/rq0_topology_edge_key_v2/analysis/`
- Renderer-v7 paired RCA:
  `RQs/RQ0/results/rq0_v7_edge_key_case_integration_v1/analysis/`
- Frozen v6/v7 artifacts and equality audit:
  `RQs/RQ0/results/rq0_v7_edge_key_case_integration_v1/artifacts/`
- Per-case conversations, detailed logs, and trajectories:
  `RQs/RQ0/results/rq0_v7_edge_key_case_integration_v1/<model>__development__main/`

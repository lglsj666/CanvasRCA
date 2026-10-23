# RQ4.5 CPU qualification on Nibi — 2026-10-19

**Status: passed and frozen. GPU smoke was not run; formal inference was not started. New model calls: zero.**

This is an implementation and CPU qualification report, not an RCA performance report. The user authorizes continued CPU repair until checks pass, and permits unequal evidence inventories across methods. Comparisons with different evidence evaluate whole methods; within-arm cross-modal nonduplication and private-label isolation remain required. This implementation repair retains its diagnostic evidence rather than using that permission to delete it.

The approved six arms and 220 exposed development cases remain: 60 AIOPS-2022, 60 AIOPS-2025 and 100 AegisLab. Formal registration remains 1560 logical positions, with a 1700-attempt ceiling including future smoke and recovery. Historical baselines are reused, not rerun. Codex.md is unchanged.

## Passed checks

| Check | Actual scope and evidence |
|---|---|
| Static | Python/TypeScript/configuration/import checks; 2032 functional nonblank/noncomment lines; 175 protected historical/default source files |
| Unit | 27 tests, zero failures/errors; numeric spellings, ownership, selection, instruction boundaries, source dispatch, gather, recovery/references/repeats, QA tolerance and passive region mapping |
| Boundary preflight | Six real cases, including the former oversized, data-empty and structured-endpoint failures |
| Full processor audit | 220 cases × six RCA conditions = 1320 requests; image/context and new-image legibility gates passed |
| QA input preparation | 33 cases × six conditions = 198 requests: 180 registered formal QA inputs plus 18 inputs for three smoke-only identities; no QA answers generated |
| CPU runtime | 30 actual packet probes, including twelve zero-image hybrid applicability requests; independent gather/context checks |
| Passive transport repair | Actual four-image old/new CPU packets have identical pixels, input tensors, token IDs, gather and multi-axis rotary position encoding (MRoPE); only attention-region attribution differs |
| Visual review | Sixteen actual PNGs inspected and hashes matched on Nibi; representative three-dataset image sets and boundary examples |
| Determinism | Actual unified-renderer repaint of the long-operation/extreme-duration PAIR02 example has exactly the qualified PNG hash |
| Freeze | 1560 formal and 18 future-smoke positions frozen; both queue hashes verified after writing; 139 frozen source/config files match the local workspace |
| Model provenance | 27 checkpoint/processor files hash-verified, totaling 55,582,674,402 bytes; weights referenced, not copied or executed |

Final Slurm job **24546402** completed with exit code **0:0** in **4m45s**. It requested eight CPUs and 64 GiB, without GPU resources. CPU preparation used eight distinct physical cores. Population and QA preparation dispatched eight distinct registered source groups first; the runtime subset had only three available groups and used all three.

## Failures, repairs and retained evidence

1. CPU v1 passed 20 units and three preflight cases, then failed 127 population cases: 122 oversized image requests, four cases without an eligible graphic transfer target, and one operation-bound endpoint shape. The new complete-marginal component counted both phase row totals despite parallel columns. Correct its height and remove redundant per-sample axes; retain exact samples/statistics. Parse endpoint operations and support counts explicitly.
2. Register the genuinely empty-transfer hybrid limit. Four AIOPS-2025 cases have neither qualified pairs nor observed topology. Their three hybrid conditions share the complete residual-text request with zero images and explicit applicability metadata. No empty warning panel or relation is fabricated. Pure-visual arms still require their unchanged original dashboard. Capacity/rendering errors cannot take this path; all 220 cases remain in the denominator.
3. CPU v2 passed 22 units, six boundary cases and all 220 population cases. The complete input-cost gate failed only H_TOPOLOGY/AegisLab: **1.31% above** frozen T_FULL input. Preserve that failure rather than relaxing the gate.
4. Consolidate the five shared non-diagnostic task/reading/output sections. All 220 original rule-block sets have one identical hash. Preserve the SIRCL* diagnostic order, source/unit/scope/causality caveats, two private verification checks, citations and five-distinct-ID JSON contract. Reject mixed diagnostic/instruction sections or unknown variants. Every hybrid request saves exactly **522 actual processor tokens**. The independent comparison verified 660 unchanged pure-visual generation identities, 660 unchanged hybrid image/grid/gather sets, and 660 byte-identical diagnostic bodies after removing only the registered static-rule transformation.
5. Fix CPU source interleaving for QA preparation as well as full preparation. This changes preparation order, not cohorts, questions or the formal model-call order.
6. Before GPU collection, correct the inherited attention mapper: RQ4.5 has several independent dashboards, so every image header needs its own region. Later headers were previously labelled background. Add two-image and empty-transfer regressions and an actual packet comparison. No attention measurements or model answers existed to repair.

The last repair affects passive measurement only. Reconstruct the prior complete source fingerprint; verify unchanged compiler, renderer/configuration, model-affecting packet AST and recipe; compare all **1518** request payloads. Only unexecuted request identity metadata is rekeyed for the changed transport-source hash. Carry forward unaffected input/geometry/cost/QA/repaint evidence with its original source hash and explicit `rerun: false`; rerun units, runtime and actual transport checks. Do not describe reused tests as newly executed. The guard forbids this operation after model activation/attempts.

Original failure reports/code are retained under `qualification/history_v1`, `history_v2` and `history_v3` on Nibi. No thresholds, cases, diagnostic values, sampling rules, model recipe or scores were relaxed/changed to pass.

## Actual input budgets

Negative percentages mean fewer language-model input tokens than the frozen historical reference. Counts include text, retained image tokens, templates and image boundaries; original-image and context limits are checked separately.

| Dataset | Arm | Mean actual input | Versus T_FULL | Versus MARGINAL_FIVE |
|---|---|---:|---:|---:|
| AIOPS-2022 | H_MARGINAL | 21,441.23 | -4.63% | -8.26% |
| AIOPS-2022 | H_TOPOLOGY | 20,636.88 | -8.21% | -11.70% |
| AIOPS-2022 | H_TOPO_MARGINAL | 19,998.18 | -11.05% | -14.43% |
| AIOPS-2025 | H_MARGINAL | 17,964.22 | -6.12% | -9.95% |
| AIOPS-2025 | H_TOPOLOGY | 18,457.17 | -3.54% | -7.48% |
| AIOPS-2025 | H_TOPO_MARGINAL | 17,704.67 | -7.47% | -11.25% |
| AegisLab | H_MARGINAL | 21,927.09 | -6.91% | -10.17% |
| AegisLab | H_TOPOLOGY | 23,341.62 | -0.91% | -4.37% |
| AegisLab | H_TOPO_MARGINAL | 22,104.75 | -6.16% | -9.44% |

These are **input-only** costs. Output tokens, deployment time and ranking remain unmeasured. The 522-token reduction comes from generic instruction consolidation and must not be attributed to visual compression. Rewording may also affect diagnosis. Historical comparisons therefore assess the complete revised method, not a pure modality intervention; a text system could also apply this generic optimization.

The preselected H_TOPO_MARGINAL already reduced input before instruction consolidation by 8.73%, 4.75% and 3.94% relative to T_FULL on the three datasets. Its current reductions are 11.05%, 7.47% and 6.16%. In contrast, standalone topology on AegisLab needed the generic instruction saving to cross the registered frozen-baseline input gate. CPU passage establishes no MRR improvement and no measured total-cost reduction.

## Artifacts and next boundary

- [Machine-readable qualification receipt](../../RQs/RQ4_5/findings/nibi_cpu_qualification.json).
- [Unique current findings](../../RQs/RQ4_5/findings/exp_exclusive_spatial_findings.md).
- [Approved plan and implementation amendments](../experiment_plans/RQ4_5_Exclusive_Modality_Spatial_Pruning_Plan_2026-10-18.md).
- Nibi authoritative root: `/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1`.
- Reports/credentials: `qualification/`; exact input payloads: `inputs/` and `mechanism/`; frozen queues/source/model provenance: `frozen/`; job logs: `logs/`.

Dense node-link crossings and inherited smaller U fonts remain documented limits; the ≥18px requirement applies to newly rendered hybrid graphics. Correctness/legibility checks do not establish that the model will read or diagnose accurately. Attention remains registered only at layer 3's last-prompt and first-decode queries, not the final ranking tokens. No actual attention capture or runtime-overhead measurement occurred in CPU qualification.

**Stop here.** GPU smoke and formal scopes have no activation credentials. Their compatibility, accuracy, output cost, attention collection and final retained-artifact density require the later authorized stages.

Deployment fingerprint: `64676ea19b7d0f6d98c6d39e6bc3eeb33b70a3514f9798fe134295c87eb74879`.

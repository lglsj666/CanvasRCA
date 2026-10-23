# RQ4.5: Exclusive source ownership and spatially covered visual pruning

**Authority:** user-approved implementation on 2026-10-18. This delivery ends after code and static checks. CPU regression, preparation, renderer/browser execution, processor counting, features, smoke and inference are NOT authorized now. The hybrid exception applies to this experiment; `Codex.md` is unchanged. All diagnosis remains single-call, frozen-model RCA.

## Motivation and scope

Two parallel objectives: retain approximately 0.50 hybrid MRR with lower actual deployment token cost; improve pure visual RCA from A_UNIFORM_E50. Six new main arms, evenly divided. Use the same exposed 220 development cases (AIOPS-2022 60, AIOPS-2025 60, AegisLab 100), fixed candidates, five distinct output IDs, public windows and frozen RQ3.16-derived facts. Complete here means the frozen evidence, not the entire canonical telemetry corpus.

Reuse T_FULL, MARGINAL_FIVE and A_UNIFORM_E50 answers and costs. Do not run bulk bridge or baseline repeats. Historical backend, prompt and time differences remain limitations.

| Evidence | Design consequence |
|---|---|
| MARGINAL_FIVE MRR 0.5054 repeats image facts in full text | Transfer whole source groups; old performance is not a new-method result |
| TPV and some RQ3.6/3.7 relationship gains; RQ3.17 combination failed | Separate topology, durations and their combination |
| RQ3.19 small field handoff did not offset image cost | Transfer complete records, statistics and derivatives |
| RQ3.21 compact strings saved tokens but hurt ranking | Preserve residual text organization, number spelling and rules |
| U spatial gaps small despite weaker role coverage | Test source geometry and context, not saturated feature proxies |
| RQ4.4 duplicate high-resolution cards increased cost without gain | No duplicate overview/detail atlas |

SeeRepo motivates division between structural relationships and precise content, but its savings largely involve multistep exploration and do not establish single-call RCA savings: [paper](https://arxiv.org/html/2606.14061v4). FEATHER motivates localization/grounding checks in addition to mean task scores: [paper](https://arxiv.org/abs/2412.13180). Neither hybrid input nor uniform sampling alone is a novelty claim. Candidate contribution is auditable, source-complete exclusive modality assignment and source-geometric visual compression, conditional on measured performance/cost.

## Main arms

| Arm | Definition |
|---|---|
| H_MARGINAL | Whole request-pair records, samples and statistics in images; remaining original M/R/L/G in text |
| H_TOPOLOGY | Whole public topology records and their derivatives in images; remaining facts, including pairs, in text |
| **H_TOPO_MARGINAL** | Both transfers; hybrid nominee |
| V_DOMAIN_FULL | Original U PNG; retain all mandatory anchors A and optional registered evidence E |
| **V_SOURCE_UNIFORM** | Original U PNG; retain A and q=ceil(len(E)/2) source-geometric E tokens; visual nominee |
| V_CONTEXT_FILL | Exact historical U keep set plus local context, with total count equal to V_DOMAIN_FULL |

Pair selection remains at most two relationships, with at most 32 real rank-sampled pairs per phase. No changed selection, sample count, anomaly scores or inferred causal edges. Calls and deployment are separate node-and-arrow graphs using existing registered components. The combined arm reuses exactly the same component images as the individual transfers, without a new composition search.

If no qualified pair exists, H_MARGINAL and H_TOPO_MARGINAL use the exact H_TOPOLOGY request and reference its answer. This data fallback does not excuse capacity/rendering failures. Keep all 220 cases and separately report pair-applicable cases.

Hybrid images retain full A union E; no E50 confound. All pixels still pass the original visual encoder before post-merger gather. Pure visual arms retain the exact original image, coordinates, positional encoding and encoder; change only the gather set.

### Deterministic source-local selection

Group by original source record, not entity. Shared optional tokens support all true owners and cost once. Preserve A without treating it as optional-graphic coverage. Prioritize untouched sources, ordered by stable source ID. First E position is nearest the source geometric center (token-index tie). Then choose the source with largest squared distance from its farthest E to already selected E in that source, normalized by its E bounding-box squared diagonal (floor 1); source ID then token index break ties. Continue to q. No feature cosine, attention, anomaly magnitude, labels or historical correctness.

CONTEXT_FILL starts from the complete historical U gather. Eligible additions are outside A union E, inside the same original card, at Euclidean merged-grid distance at most one from E in that card. Deterministic spatial farthest-point additions use the current kept set; index breaks ties. If exhausted, fill from remaining E. Keep true original embeddings and original order. DOMAIN_FULL/CONTEXT_FILL may cost more than U; only SOURCE_UNIFORM matches U's count.

## Exclusive ownership and renderer

`ModalityOwnershipPacketV1` records original occurrences, source/derivative groups, ownership, display binding and exact lexical numbers. `VisualSelectionPlanV1` records A/E, source supports, original indices and selection reasons.

All samples, statistics and summaries of one source group move together. Entity IDs, units, phase labels and reference IDs may repeat only as joins. Remove transferred copies from every text section and candidate annotation. Equal numbers are not equal facts. Distinct observations retain source identity and multiplicity. Public dependency assertions must be explicit; unknown structures fail closed. Scalar observations in a graph-oriented text section do not become relationship-derived facts merely because of that section's name.

The old marginal plots omit exact pairing and statistics. Add only the necessary `trace_joint.complete_marginals` component in `src/renderer/`: parent/child distributions, aligned numbered samples with exact values, total/sample counts, thresholds, binary joint counts, quantiles and available conditional summaries. Numbers are visible beside real glyphs; tooltip/HTML-only values do not count. No old-prompt screenshot. Existing components/default semantics and missing-point bridging remain unchanged.

Later CPU qualification must establish full source union, empty cross-modal diagnostic intersection, unchanged numbers/units/directions/phases/candidates/occurrences, actual new-graphic processed fonts >=18 px and strokes >=1.5 px, each side <=8192, unchanged processor pixel policy, <=16384 original image tokens and input+8192<=40960. Each dataset hybrid mean input must be below both historical T_FULL and MARGINAL_FIVE. Failures block qualification; no deleting facts, shrinking fonts or relaxed thresholds. Historical U is reused without silently redrawing its smaller effective fonts.

## Calls and measurements

| Allocation | Max |
|---|---:|
| Six arms x 220 | 1320 |
| Six independent QA conditions x 30 fixed cases | 180 |
| Two nominees x 30 independent repeats | 60 |
| One future logical smoke, 15 minutes (900 seconds) | 18 |
| Infrastructure recovery reserve | 122 |
| **Total** | **1700** |

Formal positions: 1560; main matrix 84.6%. Fixed hash chooses 10 cases per dataset, favoring distinct event groups, without scores. At most six shared semantic QA targets per case: numbers, source/unit binding and phase/relationship comparison. Mark unavailable targets, never replace cases based on success. QA has no diagnosis instructions and its outputs never feed RCA. Repeats make genuinely independent calls; exact ordinary requests reuse committed results. Invalid model responses remain zero, infrastructure missing remains unknown. No correctness retries.

Primary contrasts: H_TOPO_MARGINAL−H_MARGINAL; H_TOPO_MARGINAL−H_TOPOLOGY; V_SOURCE_UNIFORM−V_DOMAIN_FULL; V_CONTEXT_FILL−V_DOMAIN_FULL. Event-group two-sided Pratt-zero Wilcoxon, four-way Holm; case analysis separately, differences rounded to 12 decimals, paired dz, no CI. The third changes count and selection, so is a complete performance-cost comparison, not an isolated algorithm effect.

Hybrid advance: actual input+output decreases in every dataset relative to both text and MARGINAL_FIVE (aim >=10%), ranking retains strong-text level and aims to exceed 0.5054. Pure nominee: aim U+0.02 MRR with total tokens <=1.05 U. Report per-dataset MRR/AC@5 and repeat direction. Recognize whole-system progress while limiting unestablished component claims.

Report strict/tolerant MRR, AC, Precision, AVG, repairs/breaks, illegal IDs, full failure denominators/unknown bounds, original and retained image tokens, text/output tokens and measured preprocessing/runtime. Read fixed QA/RCA answers for wrong values, wrong real sources and reason/rank contradictions. Attention reuses mechanism cases' actual calls only; report true query coverage, not final-decision attention if only initial queries were collected.

## Implementation and stopping boundary

Five functional modules in `RQs/RQ4_5/src/`, <=7500 nonblank noncomment lines; new scoring imports only `scorer`. Retain BF16 Qwen/vLLM, existing rank decode, 8 distinct physical-core workers, concurrency 8, GPU memory utilization 0.8, context 40960/output 8192. Preserve atomic commits, interruption recovery, exact references, independent repeats and bounded RAM prefetch. CPU, smoke and formal launch switches default closed and require source-matched independent authorizations/credentials.

This delivery writes plan/protocol, compiler/selector/runtime/analysis and future tests, then runs only AST/syntax, TypeScript type checking, configuration/registration/import, source protection, line-budget/private-boundary and default-switch static checks. Do not run tests, preparation, renderer/browser, processor, features, CPU regression or GPU smoke. Final state: code implemented, static passed; CPU/GPU qualification pending.

Retention: <=2,500,000 bytes per actual completed call and <=1 decimal GB attention per 10,000 calls, including sidecars/dependencies. Preserve directly readable exact prompts/images/outputs/conversations, scores, mappings, token operations, accounting and all attention actually collected. Verified references/hardlinks; no archives. Cleanup only after commits/writers drain and reference/hash verification. Do not mutate historical records.

## Authorized implementation amendments — 2026-10-18

The user subsequently authorizes CPU regression and implementation repair on Nibi until all CPU checks pass; GPU smoke and formal inference are not authorized in this session. The initial static-only boundary above records the original delivery, not the current CPU authorization.

The user also removes strict cross-arm information equality. Methods may select different public evidence or detail levels, with explicit per-arm retained/transferred/omitted inventories. A comparison that changes evidence availability evaluates the whole method; it does not isolate modality. Private-label isolation, the original case denominator, single-call RCA, actual-cost accounting and within-arm cross-modal nonduplication remain in force. This does not require removing evidence: the current compiler repairs retain the original frozen records. The size, context and legibility limits remain unchanged.

CPU v1 exposed three implementation classes: excessive pair-canvas height (122 cases), a data-empty transfer limit with no eligible pair or observed graph (four cases), and operation-bound parent/child endpoint lists (one case). The revised C39 component counts parallel phase rows once and removes redundant per-sample axis lines; it preserves exact sample labels and statistics. Endpoint parsing preserves both operations and support counts. With no eligible transfer target, the three hybrid conditions share the complete residual-text request with zero images and are explicitly flagged as data-empty applicability cases; no graph is fabricated, no warning panel is drawn, and no rendering/capacity error can use this path. Pure-visual conditions still require their unchanged original PNG. Report the actual carrier and this limit separately.

Failed reports and renders remain available. The staged source hash proof and unchanged topology renders remain reusable; changed pair graphics receive versioned content-addressed paths. Repaired input and runtime checks must pass before CPU qualification is complete.

### CPU v3 instruction revision

The complete v2 capacity/legibility/context audit passed 220/220 cases. The remaining input gate failed only for H_TOPOLOGY/AegisLab (T_FULL ratio 1.0130625). Before any model call, consolidate the five duplicate non-diagnostic task/reading/output blocks using `RQs/RQ4_5/configs/hybrid_instructions_v2.json`; retain every diagnostic record, original diagnostic number/string/order, and qualified image. The source blocks have the same hash across all 220 cases. Preserve the existing diagnostic discipline and unique reading rules; reject unreviewed source variants. Do not label this rewording behaviorally inert: historical contrasts evaluate the whole method with this explicit interface revision. All hybrid arms share it; pure visual and independent QA are unchanged. Recheck actual processor inputs, full cost gates and runtime; do not loosen thresholds. See DD-RQ45-6 for the failure evidence and detailed semantic inventory. CPU authorization continues; GPU remains closed.

### Passive attention correction and scoped CPU evidence reuse

RQ4.5 uses multiple independent dashboards, so every image header receives its own attention region. The inherited image-0-only rule is repaired before any collection. Add two-image/empty-transfer mapping tests and actual CPU old/new packet comparison; keep all model inputs, positions, selections, solver and query/layer policy unchanged. Preserve successful v3 input/geometry/budget/QA/repaint evidence with source/hash provenance and unchanged-payload verification; rerun affected unit/runtime/transport checks, not the complete data batch. Request recipe identity metadata is updated before any model activation because the transport function's source hash changes, without changing model-visible payloads. GPU remains closed. See DD-RQ45-7.

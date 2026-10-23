# RQ4.6 — Pod-bound relation joins and uniform-pruning support closure

**Status: the user authorizes CPU qualification, GPU smoke, repairs and then formal launch. No formal call is allowed before the registered qualifications pass. The cost-first hybrid revision below is registered before any new model call.**

## Decision and evidence

Keep two routes: improve hybrid performance/cost from RQ4.5 H_MARGINAL, and improve pure vision from RQ4.1 A_UNIFORM_E50 (U). Both remain one-call diagnoses. The user's explicit RQ4.5 hybrid authorization is continued for this experiment; Codex.md is not edited. The user explicitly requests both pruning and hybrid extensions grounded in paired historical failures. The final prospective registration has **ten new RCA arms: five hybrid and five pure visual**. It supersedes the initial four-arm and intermediate seven-arm draft before execution. The ten-arm registration preceded preparation. Subsequent CPU-only corrections and the explicitly authorized hybrid summary projection are recorded below; no new model call preceded them.

RQ4.5 H_MARGINAL attained standard MRR **0.4912**, mean input+output **20,915.9 tokens**, 5.97% below historical T_FULL. Its benefit is heterogeneous: AIOPS-2022/2025 lose 0.0189/0.0275 MRR against text while AegisLab gains 0.0423. Static instruction consolidation explains part of the cost reduction; adding its 522 tokens back still leaves approximately 3.62% savings. It is a useful engineering point, not a demonstrated universal winner. H_TOPO_MARGINAL reached 0.4736; additional complete topology was not beneficial overall.

In the fixed reading subset, H_MARGINAL answered 51/58 complete one-hop relation questions under tolerant scoring, versus 0/58 and 1/58 for the topology-image hybrids. Those questions require a complete endpoint set. Zero exact-set accuracy does **not** mean no edges were read, nor prove global clutter is the cause. RQ4.4 also showed local numeric reading can improve without diagnostic improvement. New pure pruning variants (0.3105–0.3302) did not beat historical U (0.3517); their results do not justify replacing U with those failed algorithms. The new refinements below preserve U as their starting mask and require a distinct intervention.

**Hypothesis:** explicitly sharing the pod identity between its observed service-instance and node-hosting edges can reduce relationship lookup/association errors, under matched selected hybrid evidence, without adding inferred causal relationships. The pure-visual controls continue to preserve complete original evidence. Measure whether this improves ranking and whether it remains economical. This is an input representation intervention, not a new causal estimator.

This is deliberately narrower than “topology helps.” Full call/deployment graphs, matrices, owner-group layouts, entity grouping and scope competition have already been tried. The new element is a **pod-keyed join of two recorded edge types**, with a matched separate-relations control. This experiment does not claim that relational joins or node-link drawings are new inventions.

## Ten new arms

| Arm | Input | Question |
|---|---|---|
| H_DEPLOY_ONLY | Pod-keyed deployment graphic; budgeted pair observations, calls and retained summaries stay in text | Does a partial TPV-style deployment handoff work without adding marginal graphics? |
| H_MARGINAL_PHASE | Complete marginal graphics with endpoint-bound reference/current population comparisons; all topology stays text | Improve marginal readout without simultaneously changing topology ownership |
| **H_POD_PHASE** | H_MARGINAL_PHASE plus the same pod-keyed deployment graphic | **Hybrid nominee**: improve phase comparison and deployment joins together |
| H_POD_BRIDGE | Budgeted pair graphics; deployment facts moved from text to a pod-keyed graphic; retained observations in original text order | Can selective deployment transfer improve the hybrid operating point? |
| H_POD_SEPARATE | Same hybrid facts, pair graphics and instructions; deployment shown as separate service→pod and node→pod lists of edges | Does explicit visual joining outperform looking up the same pod in separate relation sets? |
| **V_POD_BRIDGE** | U's complete dashboard, replacing only its deployment panel with the pod-keyed component; original U selection rule | Can the same association aid pure vision without another token-selection change? |
| V_POD_SEPARATE | Same complete pure-visual facts and layout, separate deployment relations component | Pure-visual representation control |
| P_U_VALUE_BLOCK | Original U PNG and prompt; same A/E and exact U budget; complete local numerical-value supports | Does retaining whole numeric supports outperform scattered fragments? |
| P_U_NEIGHBOR_PAIR | Original U PNG and prompt; same budget; prioritize pairs of adjacent positions within the same registered graphic | Does local co-retention help while preserving U's spatial coverage? |
| **P_U_COMBINED** | Equal normalized combination of those two objectives, same budget and constraints | Preselected pruning candidate; do the two requirements complement each other? |

The bold conditions are the three preselected candidates. The pruning arms do **not** inherit the new deployment drawing: they use the exact original U PNG, avoiding a simultaneous layout change. Historical **H_MARGINAL, U, T_FULL and MARGINAL_FIVE** are reused, including cost; no new unchanged baseline calls. They remain historical system comparisons, with model/prompt/backend/time differences disclosed. MARGINAL_FIVE (0.5054) contains duplicated textual and graphical pair facts; H_MARGINAL is source-exclusive.

### Graphics and facts

Add opt-in unified renderer components `graph.pod_bridge` and `graph.pod_separate`, backed by one geometry implementation, plus `trace_joint.phase_marginals` for complete population-phase comparisons. Existing components and defaults remain unchanged. Existing `deployment_groups` groups by owner and repeats shared pods; `edge_pairs` displays independent edges. Neither directly offers the proposed shared-pod join and its separate-relation comparison at this scale.

Bridge: service on the left → pod in the middle ← node on the right. Arrows preserve actual stored direction and typed labels (`hosts`, `owns`, `has_instance`). No service→node edge is invented. Multiple owners, parallel source occurrences and isolated graph nodes are retained. Stable source order determines pod order. Separate: service→pod and node→pod edges in independent lanes, ordered by source then target; complete labels are retained. Both components use the same minimum typography, edge colors and outer panel area. Label multiplicity and alignment differ; the comparison is a **whole representation contrast**, not a pure isolated attention or alignment intervention.

For hybrid, transfer the retained deployment and/or request-pair records according to the arm table. All deployment and call/request-parent records and support counts remain available in their assigned modality. Keep the original at-most-two relation selection and all population/conditional statistics; the authorized budget projection retains eight original sampled pairs per phase and omits raw metric arrays. Retained numeric spellings are unchanged. No cross-modal diagnostic duplication; identity/unit/source labels may link modalities. An unrecognized or mixed source record fails explicitly rather than being partially transferred. No-pair cases still show deployment if present; no transferable graphic yields the complete remaining text for hybrid only. Pure vision never falls back to text.

Pure arms retain the original evidence packet, viewport, candidate order and all other component choices. Replace only the deployment component. Recompute actual ink support for the new pixels, then apply the historical U algorithm: protected anchors A plus deterministic farthest-point selection of ceil(|E|/2), initialized by A. The **rule**, not old pixel indices, is inherited because the panel pixels changed. No feature extraction, new attention operator or encoder pruning. Record A/E and retained counts separately; a different graph can change counts, so visual comparisons do not claim identical retained embeddings.

New deployment labels target nominal 28px and processed ≥18px; strokes processed ≥1.5px. Existing non-deployment pure dashboard text retains U's known readability limitations. Do not claim the whole old dashboard has ≥18px processed text. Preserve the old fixed panel; if content cannot fit, CPU qualification blocks this version rather than deleting edges, shrinking labels or silently rearranging other panels.

### Authorized hybrid cost revision — 2026-10-19, before model calls

The user explicitly permits aggressive evidence removal for hybrid, with cost reduction as a primary contribution and no desired performance loss. This supersedes the earlier complete-source retention requirement **for hybrid only**. Do not weaken historical controls or silently apply this deletion to pure vision.

The common deterministic projection is `HybridSummaryBudgetV1`:

- Keep all candidate identities and entity coverage. For the twelve core metric records, retain baseline/peak, deviation and regular/current summaries, and full-window first/last/min/max with original positions. Omit raw 64-bin value arrays and missing-position codecs.
- Keep all auxiliary metric identities and native units; replace each raw auxiliary sequence by its actual observed first, last, minimum and maximum and original bins. This can remove shape information and is explicitly lossy. It is not the reversible string packing tested in RQ3.21.
- Keep all trace summaries, log contents, population/joint/conditional statistics and all observed relationships. Select eight of the original pair samples per phase using deterministic equally spaced ranks including both endpoints; preserve original sample IDs. The text-only carrier in H_DEPLOY_ONLY uses the exact same subset.
- Record omissions and the canonical source identity in `hybrid_projection.json`; preserve original source dependencies for audit. Model-visible input history is the actual reduced request, never reconstructed as if omitted evidence had been shown.
- Explain the available summaries and sample subset correctly in new hybrid instructions. Remove the old auxiliary paragraph's inapplicable claim that raw series and reference-ridge probes are supplied.

New explicit `trace_joint.budget_complete` and `trace_joint.budget_phase` components accept the registered observed-rank subset, reusing the existing drawing bodies. Existing 32-sample contracts and components remain unchanged. Pod graphics use a 1024px hybrid canvas, variable row height only where a role wraps, and omit empty decorative node-box ink; identities, role labels, arrows and 28px labels remain. Pure dashboards retain their original panel positions and complete evidence.

All five hybrid arms use this same projection; their within-family representation contrasts therefore remain matched on selected information. Hybrid-versus-pure and historical comparisons are complete-system performance/cost comparisons with different evidence. Do not call them same-fact modality effects. The coupled-support optimizer revision changes candidate swaps, not the source objectives, exact U budget or intervention thresholds. Value-only and neighbor-only use at most64 strict-improvement steps; the two-objective combined arm uses at most128, as registered after the full CPU difference audit and before any model call. CPU-only mask probes motivated this search repair; no ranking feedback was used.

### Hybrid revision: differential evidence and concrete optimizations

The paired hybrid review is incorporated in the review attachment below; its full case table and eight contrasted response sets are [evaluator-only JSON](../../RQs/RQ4_6/findings/historical_hybrid_review.json). Deleted early raw results are not reconstructed. RQ1.1 TPV handed topology to images, RQ3.16/17 repeated graphical facts alongside text, and RQ4.5 transferred complete sources exclusively. These are distinct interventions.

- RQ3.16 marginal versus same-fact text: **52 improved / 43 worse / 125 tied**. Marginal versus markless: **8 / 3 / 209**. Benefits do not establish that every point or every marginal fact is helpful.
- RQ4.5 combination versus marginal: **24 / 37 / 159**, including AIOPS-2022 **14 / 7 / 39**, AIOPS-2025 **2 / 6 / 52**, AegisLab **8 / 24 / 68**.
- The same contrast is **8 / 1 / 14** in 23 pod-only cases (ΔMRR +0.2101), but **14 / 32 / 106** in 152 service-only cases (−0.0588). These label-bearing strata are explanatory development evidence, never inputs or a deployment selector.
- Combination versus topology alone improves **26** cases and harms **22**. In the 28 node-only cases, there are **0 improvements / 2 regressions / 26 ties**. Marginal graphics are not automatically beneficial even when all original resource text survives.
- Read responses include false causal claims from the deepest callee, choosing a service instead of an observed host resource fault, and mistaking a parent threshold for a change between phases. Correct-ranked answers also confuse p50 and p95; they are not explanation gold standards.

**Optimization 1: selective deployment transfer.** Both new deployment encodings retain all observed membership records; call/request-parent records stay text. H_DEPLOY_ONLY retains complete pair records in text, so H_POD_BRIDGE−H_DEPLOY_ONLY isolates the complete pair handoff within the new deployment interface. It is a partial TPV successor, not a claim to rerun original full-topology TPV. No labels, resource anomaly scores or inferred causal edges enter the graph.

**Optimization 2: direct population phase comparison.** Add opt-in `trace_joint.phase_marginals`. For each actual parent/child endpoint, put reference and current **of the same percentile** on one common log1p(ms) axis, retaining original exact values and explicit phase labels. Separate population p50/p95 from thresholds, conditional summaries and sampled requests. Preserve every selected sample pair and its original ID, plus all population counts, operations, statistics and retained numerical spellings. The eight-sample subset is identical across hybrid carriers and does not change population statistics. Sample rows remain separate by phase; never connect reference and current samples as if they were the same request. Parent and child quantiles are not subtracted into a fabricated local duration. This directly addresses observed cross-phase/quantile substitutions; it does not prove those were the cause of the historical ranking loss.

**Optimization 3: controlled composition.** H_POD_PHASE combines the two changes. H_POD_PHASE−H_MARGINAL_PHASE measures deployment transfer under the improved marginal view; H_POD_PHASE−H_POD_BRIDGE measures population comparison under fixed deployment ownership. The two existing bridge/separate arms remain the join-layout control. All five use the same task rules, with arm-correct evidence-location declarations; no case-specific advice is introduced. H_POD_PHASE replaces H_POD_BRIDGE as the hybrid nominee now, before preparation or any new answers.

No-pair cases retain the other applicable transfer only. No-deployment cases retain all other original records. Empty image transfers can yield a complete text request in the hybrid family and are explicitly identified; they never justify text fallback for pure vision. Exact identical requests may be referenced, not rerun. Capacity errors are not data-absence fallbacks. The new marginal component is additive; historical complete_marginals and all old defaults remain unchanged. Its actual geometry, readability, cost and ability to change rankings remain **unqualified** until future authorized checks.

### Pruning revision: evidence, limits and deterministic rules

A fresh offline split of the existing 220 U−V_FULL outcomes gives **76 improvements / 33 regressions / 111 ties**; top-1 repairs/breaks are **35/5**. AIOPS-2022 has 19/7/34, AIOPS-2025 20/7/33, AegisLab 37/19/44. Of the 76 improvements, 60 are jointly valid answers and 16 include an interface repair; of the 33 regressions, 29 are jointly valid and four include a new U interface failure. Ranking effects are not just whole-answer rejection.

The improved and worsened groups have essentially identical zero-optional-role fractions (**0.3288 vs 0.3295**) and mean nearest retained-grid distance (**0.4998 vs 0.4998**). There is no demonstrated deployment-time rule saying “more missing roles means U will fail.” Do not fit or use an outcome-conditioned route on these cases.

All five top-1 regressions were read and checked against their public source records. Failures include confusing operation-name IDs with the trace owner, swapping trace cards, substituting another card's magnitude, and calling a ~0.42% GC-memory change severe because standardized deviation is large. Winning full-vision answers can also contain incorrect reasons. These observations motivate source-local numeric support and neighborhood hypotheses; they do not prove pruning caused each claim or identify particular causal tokens. [Audit with exact answers, source hashes and counts](../../RQs/RQ4_6/findings/historical_uniform_review.json).

Keep **every A**, use only **E**, and keep **exactly the same K** as historical U. Start from its actual U mask. Require every E position to remain within one merged-token grid step of a retained A/E position, so refinement cannot destroy its measured spatial-cover advantage. Preserve original positions, embeddings, order, image bytes and prompt.

- **Value blocks:** use actual non-anchor support for registered numeric detail-value targets (`part=value`). A block scores only when its entire optional support is retained, not when a single representative token touches it. Do not use the numerical magnitude, abnormality score, cause label or model answer in selection. This does not guarantee a complete original character is encoded: the support is the renderer's measured merged-patch support.
- **Neighbor pairs:** form horizontal/vertical adjacent optional positions within the same registered graphic role. Both positions must be retained to score. This is local co-retention, not a claim to reconstruct an entire curve or to infer a data-time adjacency from image position.
- Deduplicate identical support groups and charge shared tokens once. Normalize each objective by its own group count. The combined arm weights the two normalized objectives equally.
- Deterministic closure search: at most 64 accepted rounds; consider original groups and unions of two overlapping groups (at most six slots, at most four currently missing slots). Order the top 32 proposals by registered objective gain per added slot, then missing count and stable indices. Add an entire proposal, remove lowest marginal-score-loss optional positions while preserving A, K and one-grid coverage; break ties by token index. Accept only strict objective improvement; choose the highest resulting objective, then lexicographic retained indices. No parameter/seed tuning from new MRR.

This differs from RQ4.5 source-uniform (which reallocates coverage from scratch), CVC/UNARY (feature-surrogate/role-touch coverage), V_DOMAIN_FULL (larger budget), and V_CONTEXT_FILL (extra domain-external tokens). It is still a hypothesized engineering optimization, not an established new theory. **Not all unretained patches are blank, and preserving more role counts is not the goal.**

Future CPU intervention gates: each pruning arm must replace ≥10% of U's optional slots with strict registered-objective improvement in ≥50% of each dataset's full denominator. Each pair of new pruning arms must differ by ≥10% of optional slots in ≥50% of the full cohort. These are anti-redundancy engineering gates, not evidence of RCA utility. Failure blocks that registration before model calls; cancel/revise the affected condition explicitly, never rerun a nearly identical arm or relax gates silently. No masks or gates have been evaluated in this static-only delivery.

### Prompt correction

Remove the exact registered obsolete instruction `All original telemetry, additional operands, logs, relations and candidates remain in text.` **only in an identified static instruction section**, and replace it with a declaration consistent with actual ownership. Do not globally replace matching strings inside logs or other evidence. Apply the correction to both RCA and independent QA. Verify residual payload contains no conflicting instruction. The old RQ4.5 inputs/results are immutable; the stale wording does not change their classification as actual topology-image hybrids. Its effect was not measured and is not offered as the explanation for their scores. No extra calls are scheduled solely to repair the old prompt.

## Mechanism and budget

Use the same exposed 220 development cases (60 AIOPS-2022, 60 AIOPS-2025, 100 AegisLab). Independently hash-select 30 cases, ten per dataset, prioritizing distinct event groups; selection uses no historical answers or labels.

The two pure deployment arms receive six standalone relation questions: two direct sets, two inverse sets and two pod-mediated joins. The five hybrid arms instead share **two deployment questions (inverse and pod join) plus four population-reading questions** (parent/child p95 and p50 in reference/current order). All hybrid conditions answer exactly the same questions from the same public sources; only their carriers differ. Questions are instantiated by fixed hash, not historical errors. Absent pairs yield null population questions, not replacement cases. Use typed relation or numeric answers in a fixed six-question schema, independently of RCA instructions. No answer cards, numeric unit ambiguity, or forced-current shortcut. Verify any cross-family relation target exists in both sources before comparing it. The full six-question hybrid and pure QA means are different constructs and are not pooled; report shared relation and hybrid numeric fields separately.

Report exact-set accuracy and a preregistered tolerant normalization (whitespace/type prefix only), plus endpoint precision/recall to distinguish incomplete from wholly wrong answers. Cases, not individual questions, are the statistical unit. Read the actual QA and paired RCA responses for all 30 cases: endpoint/source correctness, use of relationships in reasons, and consistency between reason and ranked IDs. A generated reason is not a faithful internal reasoning trace.

The three pruning arms plus **U_QA** receive the same six numeric/source QA questions on these 30 cases: two exact metric detail values, two trace owner/value reads, and two reference/current value pairs. Select targets from public rendered detail fields by fixed hash, not from failures. Asking for both values avoids an always-current answer shortcut. Score numeric correctness, owner, and unit separately, and jointly; only preregistered unit aliases (µs/μs/us/microseconds, ms/milliseconds) are tolerant. Do not let QA answers enter RCA. U_QA is a **new measurement task on the original U image/mask**, not another U diagnosis or duplicate historical QA task. Relation and numeric QA have different targets and are not directly pooled as one ability score.

Each of the three nominees gets an independent full single-call repeat on these 30 cases. Attention reuses these calls only; retain the existing actual layer/query coverage (last prompt and first decode at layer 3), not a claim about final-ranking attention. No replay solely for collection.

| Allocation | Maximum calls |
|---|---:|
| Ten arms × 220 RCA | 2,200 |
| Five hybrid + two relation + four numeric conditions × 30 QA | 330 |
| Three nominees × 30 independent repeats | 90 |
| Later shared smoke | 18 |
| Infrastructure recovery reserve | 112 |
| **Total ceiling** | **2,750** |

Formal positions: **2,620**. Exact requests may share committed answers; repeats always call anew. No additional control or enlarged sweep is automatic. The unspent earlier budget does not authorize calls now.

## Analysis and advancement

Primary contemporaneous comparisons: H_POD_BRIDGE−H_POD_SEPARATE; H_POD_BRIDGE−H_DEPLOY_ONLY; H_POD_PHASE−H_POD_BRIDGE; H_POD_PHASE−H_MARGINAL_PHASE; V_POD_BRIDGE−V_POD_SEPARATE; P_U_COMBINED−P_U_VALUE_BLOCK; P_U_COMBINED−P_U_NEIGHBOR_PAIR. Event-group two-sided Pratt-zero Wilcoxon, seven-comparison Holm family; case-level analysis separately, differences rounded to 12 decimals, paired dz, no confidence intervals. Signed-rank is not an arbitrary mean-null test. Report standard/tolerant MRR, AC@1/3/5, AVG, central-scorer precision, macro/per-dataset metrics, repairs/breaks, invalid answers, original denominators, and unknown-result tight bounds. Count invalid model answers as zero, infrastructure omissions as unknown.

Hybrid QA contrasts (H_POD_BRIDGE−H_POD_SEPARATE, H_POD_PHASE−H_POD_BRIDGE, H_POD_PHASE−H_MARGINAL_PHASE), the pure relation contrast and each pruning QA versus U_QA form one separate seven-comparison exploratory family; repeats quantify ranking and endpoint stability. Compare reading and RCA changes descriptively, without treating 30 cases as adequate proof of mediation. Report applicability and degree/graph size strata determined from public inputs, not outcome-selected “success” cases.

Implementation clarification before any calls: generation identity and scoring-context identity are separate. Reused answers retain the destination case/task's scoring context. With incomplete results, case comparisons use observed pairs and report tight original-denominator bounds; event-group inference uses fully observed paired groups, alongside bounds retaining all registered groups. Complete-data hypotheses and comparison families remain unchanged.

Engineering targets (not CPU gates or guaranteed outcomes): hybrid ≥H_MARGINAL+0.02 overall MRR, no dataset MRR/AC@5 loss, total tokens ≤0.80×H_MARGINAL as the aggressive cost target; pure pod nominee and pruning nominee each ≥U+0.02, no dataset MRR/AC@5 loss, total tokens ≤1.10×U under the user’s explicit pure-visual cost flexibility. Report the two pure candidates separately; do not choose one after outcomes and call it the sole preregistered candidate. Continue reporting T_FULL and MARGINAL_FIVE. A complete-method improvement is progress even if a component attribution remains inconclusive. Correct-join claims require the corresponding paired control evidence. Do not adopt a post-hoc winner or search more layouts automatically if neither route advances.

CPU input gates: hybrid per-dataset mean ≤0.90×T_FULL and ≤0.90×H_MARGINAL; pure ≤1.10×U under the user’s latest explicit cost flexibility (pruning arms still retain exactly U’s K). The hybrid engineering target is at least 20% lower actual total input+output than H_MARGINAL, with no per-dataset MRR/AC@5 loss. The original lower-cost pure-visual route receives no aggressive evidence deletion. Each input+8192≤40960; original image token sum≤16384; each image side≤8192; unchanged processor limits. Record actual text/image/input/output, precomputation, encoding, prefill/generation and deployment time. Token savings do not imply encoder or wall-time savings.

## Implementation and later qualification

Five functional modules under `RQs/RQ4_6/src`, ≤7,500 functional lines; centralized `scorer`; no external RCA repository. Freeze non-scoring inherited transport dependencies. Keep BF16 Qwen and local Blackwell RQ4.4/RQ4.5 vLLM recipe, CPU eight distinct physical cores, GPU concurrency eight, utilization 0.8. Heavy source compilation, browser rendering and full CPU audit finish before any later GPU allocation; bounded RAM runtime preparation, no disk spool. New Nibi deployment requires its own backend qualification.

Future separately authorized CPU gates: source closure/occurrence multiplicity, actual component edge/node bindings and directions, direct/inverse/join QA oracle, duplicate IDs/edges/multiple owners/isolates/long names/zero-edge cases, same non-deployment raster and geometry, actual processor support/size/readability, no stale prompt instructions, deterministic reconstruction, atomic commits/references/repeats/crash recovery, complete 220-case population/budget, and fixed visual review. No runtime pass is inherited from static checks.

Future smoke: 18 calls total, 15-minute scheduler allocation when authorized; startup overhead and missing coverage reported, no hidden 600-second timer. Ten RCA conditions, five QA calls covering all three QA schemas (H_DEPLOY_ONLY, H_MARGINAL_PHASE, H_POD_PHASE, V_POD_BRIDGE, P_U_COMBINED), and three independent repeats, distributed across the three fixed cases. This smoke is interface coverage, not every arm-by-task-by-dataset cell; complete input coverage belongs to CPU qualification. No accuracy-based re-answering. Formal runs require CPU, visual and smoke credentials bound to the frozen version, and are hash-interleaved with balanced arm rotation.

Keep ordinary directly readable deduplicated inputs/images/outputs/conversations, scoring context, manifests and all collected attention with mappings. After drained finalization, ≤25 decimal GB/10,000 actual completed calls; attention≤1 GB/10,000. References do not enlarge the denominator. Verify hashes/references before removing runtime caches; interrupted finalization must resume without inference.

**Current authorized endpoint: complete CPU and bounded GPU smoke qualification, inspect artifacts, repair affected paths, then launch the frozen formal queue and stop after startup is confirmed. Performance remains unmeasured until actual formal results exist.**

## Sources and review trail

See [review and design-difference attachment](../../RQs/RQ4_6/descriptions/RQ4_6_references.md), the [RQ4.5 complete report](../experiment_reports/RQ4_5_Qwen_Analysis_2026-10-19.md), and [SeeRepo supplied PDF](../LLM_Agents_Can_See_Code_Repositories_2606.14061v4.pdf).


## Full CPU audit revision before model calls — 2026-10-19

All220 cases passed source, renderer, geometry and actual processor/context checks. Hybrid inputs were33–42% below historical H_MARGINAL. Two prospective eligibility failures were preserved: V_POD_SEPARATE averaged1.0581×U input on AIOPS-2022, and combined versus value-only masks differed by the registered10% in only32/220 cases.

The user explicitly allows relaxed pure-visual cost; the input and engineering total-cost limits become1.10×U, with no diagnostic evidence removed from pure vision. No ranking result motivated this change. Hybrid limits remain0.90×T_FULL and0.90×H_MARGINAL.

The combined search had exhausted its64-step bound while still improving both registered objectives. Its bound becomes128; the two single-objective arms remain64. Exact K, protected anchors, one-grid coverage, objectives and all anti-redundancy thresholds remain unchanged. Three fixed CPU-only probes produced18.98–24.66% combined/value mask differences. Full220-case affected-mask/processor regression is required; these probes are not qualification.

The private scoring reader now uses small hash-verified retained contexts instead of rereading a109MB historical index per answer. All220 candidate/normalization/label contexts are byte-identity-audited against their original semantic hashes; scoring and model inputs do not change. Static checks, scoped source/AST comparison, affected unit tests, full combined-mask refresh and evaluator checks qualify this repair. Unchanged source/render/capacity checks are explicitly carried with provenance rather than rerendering220 identical dashboards. QA/runtime/determinism gates still run on the final version.


## Qualification and launch update — 2026-10-19

The final frozen implementation passes39 unit regressions, complete220-case eligibility, all affected pruning/evaluator checks,32-case mechanism preparation,43 runtime checks, passive-measurement invariance, deterministic repaints and actual visual review. Post-drain retention now retires verified duplicate preparation manifests and unreachable test-only image objects; actual committed inputs/outputs/attention remain complete. Only affected lifecycle regressions reran after that storage repair, with source/AST compatibility proofs for unchanged qualifications.

GPU smoke committed all18 calls in168.91s including startup. Exact request/image hashes, independent rescoring, token accounting, attention mappings and ledger drain were checked. QA accuracy errors remain outcomes; no method was tuned on smoke performance. Formal activation is separately credentialed and the2620-position frozen queue has been launched locally. See the current findings for authoritative runtime status; this paragraph reports execution and does not revise the registered scientific comparisons.

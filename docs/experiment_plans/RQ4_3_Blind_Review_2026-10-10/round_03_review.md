# Independent review of RQ4.3 v4 — round 03

Reviewer: `rq43_blind_03`. Date: 2026-10-10. Assessment is of the frozen research plan and technical contract, not an implemented method or completed experiment.

**Research-plan readiness: 8.1/10. Bounded verdict: ready for the specified feasibility and CPU qualification work, if separately authorized.** I find no remaining fundamental design defect requiring another redesign before that work. Several essential qualifications remain unperformed; this verdict does not permit model calls, rendering, tests, training, or implementation in the current documentation-only session. It is not a claim that the nine optimization positions will survive qualification or improve RCA.

**Publication readiness: not established.** There are no RQ4.3 results, no demonstrated quality–cost improvement, and no independently confirmed mechanism. I do not predict acceptance. The strongest plausible contribution is an empirical account of when evidence selection, readable token allocation, and recurrent visual-prefix processing help a fixed VLM. A collection of adaptations without a supported joint finding would be a substantially weaker paper.

## Independence, evidence, and limits

I selected the Phase A literature before receiving the proposal. The verbatim preparation record and fixed rubric are in [round_03_phase_a.md](round_03_phase_a.md). It records four primary papers, the portions actually read, publication verification, and two actual OpenReview discussions. OpenReview access was indexed-only: live pages were challenged and the API returned 403. I did not inspect rendered paper figures because screenshots failed. Those limits remain applicable.

For Phase B I read the complete [frozen plan](round_03_input_plan.md) and [authoritative technical contract](round_03_input_contract.md), including their selection formulas, interventions, failure policies, statistical families, qualification gates, and accounting. I read the full substantive reports for [RQ4.1](../../experiment_reports/RQ4_1_Qwen_Analysis_2026-10-09.md), [RQ4.2](../../experiment_reports/RQ4_2_Qwen_Analysis_2026-10-10.md), [RQ3.16](../../experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md), [RQ3.21](../../experiment_reports/RQ3_21_Qwen_Analysis_2026-10-06.md), and [RQ3.20](../../experiment_reports/RQ3_20_Qwen_Analysis_2026-10-06.md). A truncated portion of RQ3.20 §6 was retrieved separately before completing this review.

I read the current authority section of `Codex.md` (lines 1–180), the complete `important_docs/CanvasRCA_Pure_Visual_Direction_2026-10-06.md`, and only §3 of the superseded source-local draft for operator lineage. I did not treat its old arm matrix as current. I did not read other reviewers, dispositions, `protocol.md`, `manifest.json`, other round snapshots, or the later optional claim-to-comparison table.

I independently inspected installed `transformers/models/qwen3_5/modeling_qwen3_5.py` at lines 240–565 and 604–724. Its SHA256 matches the contract: `0e2cd8dc50885b2701d26b116c585eedcdc62a24080ec34345af55b963126ded`. This directly supports the descriptions of the torch chunk/recurrent fallback, q/k normalization, head repetition, post-convolution recurrence inputs, recurrent-state update, GQA, attention gating, and output projection. I did not import or execute the package, verify actual dispatch, reproduce report statistics, or inspect historical per-call trajectories. Reported historical numbers below are read evidence, not independent recomputation. The only files created are my two review documents.

## Fixed-rubric assessment

| Dimension | Weight | Score | Reason |
|---|---:|---:|---|
| Novelty and claim precision | 15% | 7.0 | Mechanisms and claim limits are explicit; many ingredients are adaptations, and a distinctive scientific finding remains conditional on results. |
| Fair baselines | 20% | 8.5 | Strong text, strongest historical pure visual, and hybrid context retain their actual statuses. Compatibility failure explicitly removes historical inferential claims. |
| Attribution and visual reliance | 20% | 8.5 | Hash, guide, offset, background allocation, forward, sham, global, order, and fixed factorial comparisons answer useful bounded questions. Some effects intentionally remain bundled. |
| Statistics and selection integrity | 15% | 8.0 | Fixed families, event grouping, paired contrasts, full denominators, exposed-development labeling, and a separate confirmation gate are credible. Power and future cohort availability remain limitations. |
| Actual deployment cost | 15% | 8.5 | Cold case processing, full vision encoding, operator work, failures, tokens, memory, and current-stack controls are included. The initial 12-case timing gate is only a screen. |
| Feasibility and reproducibility | 10% | 7.5 | The tensor and cache definitions are implementable at source level, but geometry, applicability, runtime, and equivalence qualifications have not passed. |
| Scope and failure analysis | 5% | 8.5 | Numerical reading, binding, temporal comparison, relationships, invalid output, applicability, and dataset variation are explicitly separated. |

Weighted score: **8.10/10**. None of my Phase A caps applies to this planned, gated study: the central comparison is specified, development exposure is acknowledged, and the operator has a concrete supported implementation route. This does not certify that historical compatibility or a fresh confirmation cohort exists. The later user instruction excludes confidence intervals; I honor that instruction without changing rubric weights or requesting intervals. The planned effect sizes, paired analyses, sensitivity analysis, and failure bounds provide the remaining statistical evidence, with their stated limits.

## Historical evidence and fair interpretation

The historical record argues for modest expectations. RQ4.1's CVC MRR .3332 lost to uniform .3517 and text .4846, despite large token reductions. Its coverage proxy was nearly saturated and its rewiring control barely altered token membership. Those results do not establish that saliency, source coverage, or anchor attention explains success. RQ4.3 appropriately moves to stronger interventions and measures actual incremental observation slots. U is the justified pure-visual starting point; the proposal does not promote the weaker CVC merely because its mechanism sounds attractive.

RQ4.2's semantic grouping (.3084), geometric grouping (.3088), and native-four control (.3235) all fell below U. Its semantic intervention was in the vision encoder; RQ4.3's local recurrence is in early language layers after the encoder. That is a substantive architectural distinction, not evidence that grouping will now work. SHAM and GLOBAL are necessary to distinguish source membership from extra recurrence and changed context length. Their qualified interpretations are adequate; GLOBAL is not a compute-matched control.

RQ3.16's .5054 MARGINAL_FIVE result remains hybrid evidence. The small difference from its markless variant does not establish useful reliance on detailed graphics, and five-slot results also had dataset/top-five tradeoffs. RQ3.21 shows that mathematically recoverable packed evidence can remain poorly readable and that order changes can move rankings without proving a unidirectional benefit. RQ3.20 shows why successful schema rejection and available ledger facts do not imply useful evidence acquisition. Its invalid action IDs and narrow detail budget are relevant warnings; its closed two-call architecture is not a candidate to revive.

The current plan uses these negative findings without treating their explanations as settled facts. It does not rerun the old matrices. Definition and coverage audits before admitting S are appropriate protection against disguised repetition.

Historical U/T reuse is the most consequential validity condition. A hash of the current library and agreement on 12 or 60 outputs cannot prove historical execution equivalence. Contract D explicitly requires a dependency-specific compatibility certificate and sets affected primary, optimization, and factorial tests to fixed p=1 when it cannot be supplied. This is acceptable provided it is enforced literally. In that case the old-system differences remain descriptive, current paired controls retain their narrower role, and only an eligible newly frozen cohort can furnish a new matched U/T efficacy comparison. No silent full baseline rerun is needed or justified by this review.

## Selection, rendering, and attribution

The S definitions are sufficiently concrete to implement without outcome-driven choices. Exact comparability keys, type-7 quantiles, explicit phase semantics, missing-dimension signatures, packet/card closure, and protected entity-by-modality cells address important binding and omission risks. The pair enumeration in DISTINGUISH/JOINT matters because an edge contributes only when both endpoints are selected. The fixed hash baseline shares the same protection and geometric budget. Geometry cost is correctly distinguished from retained-token count and deployment cost.

Their likely failure mode is lack of useful discretionary selection: closure may absorb most evidence, exact operation/template keys may yield many singletons, and protection can consume the opportunity for the objective to act. DISTINGUISH also values inter-entity difference, not causal relevance. These are empirical applicability and hypothesis risks. The registered cancellation and near-duplicate checks handle them without tuning a new selector until it looks different. They do not require another arm now.

R_PATCH_PACK is a finite search against the actual processor grid with preserved label binding. The processed 18px requirement is a meaningful response to historical readability problems, but fitting larger labels in fixed cards may be impossible on many dense cases. Its limited shift search and mandatory original geometry may also fail to reduce anchors by 10%. Qualification can legitimately cancel the factor and dependent combinations. The plan should report that as a failed feasibility hypothesis, not as missing experimental success to repair by expanding canvases or shrinking fonts.

HORIZON has a reproducible two-band definition, true coordinate and missing-sample behavior, preserved exact labels, and explicit high-offset/small-change boundary checks. Zero-centered magnitude folding may be a poor encoding of some telemetry even when it conserves values. This remains an appropriate falsifiable rendering candidate, not an assumed perceptual improvement.

The R comparisons explicitly bundle minimum readability, layout/encoding, and consequent token allocation. READ_GUIDE controls the changed instructions; OFFSET and BG_FILL address narrower allocation questions. BG_FILL uses real background features that can carry globally mixed information, so it cannot prove a pixel-local causal mechanism. Its stated incremental-allocation claim is defensible. No extra font-only or generic blank-image arm is necessary for the claims retained in this plan.

The fixed 2³ table uses U, S_JOINT, R_PATCH_PACK, and P_LOCAL_BI plus the four combinations. It supports interactions among those complete interventions, including the R reading guide, not an optimized 3³ search or a universal interaction across all choices. Fixed X_SRP protects the deployment objective from post-hoc winner replacement. These distinctions should remain visible in the results.

## Internal processing and runtime feasibility

The installed source supports the proposed implementation route. Its torch chunk fallback accepts but does not use arbitrary `cu_seqlens` kwargs; batching independent groups is therefore the right explicit isolation mechanism. Padding q/k/v/beta/g with zero, reversing all five tensors together, preserving real position restoration, and checking tiny FP32 reference recurrence are meaningful requirements. The fallback itself contains chunk-level work and a fixed within-chunk loop; fewer retained tokens or a small λ does not imply cheap execution.

LOCAL_BI keeps the native causal convolution and globally mixed visual features. It therefore tests a source-organized recurrent supplement, not a source-isolated image representation or a fully bidirectional model. FORWARD, SHAM, and GLOBAL appropriately narrow its interpretation. The frozen sham membership-change threshold prevents another nearly unchanged rewiring control while retaining the full denominator.

SOFT_IMAGE specifies allowed keys, native Q/K normalization and MRoPE, two separately normalized attention paths, and a single existing output gate/projection. It is an adaptation rather than exact SoFA. Materializing attention could be expensive; the production implementation and peak-memory measurements still need qualification. The combined P_DUAL does not inherit a performance guarantee from either component.

The cache contract is coherent: modified visual-prefix outputs influence later-layer inputs and their native caches; temporary local recurrence state is not a decode state. λ=0 should bypass the branch, whereas λ>0 needs comparison with the same modified-prefill reference, not with an untouched model. The registered full-prompt-prefill restriction avoids quietly claiming support for segmented image prefill. The order experiment appropriately admits that convolution, recurrence, and later causal processing all change.

These are source-level plausibility findings. Numeric equivalence, GPU memory, latency, actual branch triggering, and absence of cache regressions are outstanding gates. Their failure would prevent model execution or eliminate an arm; it would not retroactively make the proposed test scientifically incoherent.

## QA, statistics, accounting, and the main objective

The QA design repairs the earlier confused task format and avoids turning arm omissions into easier denominators. Questions come from the original public pool, remain fixed across arms, and missing or unretained target evidence scores zero when the question structurally exists. Structural NA, applicability, common-visible reading, and full-denominator utility are separate quantities. The six-item case score avoids pretending that six related responses are six independent cases. Marked QA geometry has its own frozen grouping, so the plan does not claim exact RCA-token identity.

The plan does not infer that a weak QA–MRR correlation proves independence. Order flip effects are compared with repeat variability on the same 60 cases, and invalid-output handling is explicit. Attention is optional and descriptive, not proof of a GDN mechanism or a necessary condition for continuing the study.

Event-group inference is the appropriate primary level for 220 cases in 193 groups. The plan distinguishes mean ΔMRR from the signed-rank location hypothesis and retains per-case/dataset effects. Its separate Holm families answer distinct questions; they do not jointly establish an experiment-wide 5% familywise error rate. Reporting must retain all registered families and nonresults. The planning simulation warns that +.03 effects can have low power; it supplies neither observed power nor CPU qualification. A nonsignificant contrast cannot establish equivalence.

The call arithmetic is internally consistent: 4,400 development RCA positions, 816 mechanism/repeat/timing positions, up to 1,080 conditional confirmation calls, and 252 bounded smoke/recovery positions give 6,548, leaving 1,452 unallocated under the 8,000 ceiling. Exact-request references are not new calls or independent replicates. Historical requests count as no new research calls but not as free deployment. Invalid model output and unresolved infrastructure outcomes have different scoring/accounting roles. The 18-call/600-second smoke must demonstrate its required paths or stop; it cannot be reset to acquire more qualification calls.

The cost definition is substantially stronger than the historical token-only savings claim: it includes case preparation, rendering, full vision processing, retained-token handling, modified prefill, decoding, and saving. Timing uses a preloaded model with case caches disabled, attention off, and current matched U/X/T conditions. The 12-case Latin-square timing screen is too small to establish deployment reliability or tail behavior; the plan properly reserves the stronger claim for matched confirmation measurements. Both U and T cost ratios must pass, by dataset. Increasing latency while reducing decoder tokens cannot be reported as achieving the main objective.

Despite its breadth, the design still serves MRR/cost: three positions in each requested family, a fixed deployed combination, factor-specific controls, explicit cancellation, and an independent gate before larger confirmation. I recommend no added calls to consume the remaining ceiling.

## Blocking conditions and optional improvements

**Fatal or must-fix design issues before bounded CPU qualification: none identified.** No fundamental redesign is required on the evidence reviewed.

The following are mandatory execution gates already in the plan, not claims that they have passed: historical compatibility classification; selector distinctness and real discretionary coverage; legal/readable R geometry; verified source ownership and meaningful sham changes; operator/reference/cache agreement; actual resource feasibility; valid QA tasks and denominators; and the bounded smoke. Where a gate fails, apply its cancellation, descriptive-only, or stop policy without changing the method in response to RCA outcomes. Current authorization remains documentation only.

Optional improvements require no additional model calls:

- Present each result with its allowed claim level: current matched intervention, historically compatible comparison, or descriptive historical-system difference.
- Put per-dataset applicability and exact-reference/fallback proportions beside headline MRR. This will show whether a nominal optimization was often the old method in practice.
- For the selector audit, summarize how many optional closures are genuinely comparable, singleton-only, or protected. That will distinguish a null scientific result from an objective with little opportunity to operate.
- Preserve the complete quality–cost frontier and failed factors in the eventual paper, while leading the deployment conclusion with the preselected X and its gates.

My recommendation is therefore to retain the frozen study and proceed only to its bounded qualification stage when the user authorizes it. Positive performance, operational qualification, historical causal comparability, and publication contribution remain separate questions requiring new evidence.

# Independent blind review — round 2

Reviewer: rq43_blind_02. Date: 2026-10-10. The Phase A rubric was fixed before proposal disclosure and is preserved separately verbatim. I have not read another review, score, disposition, or round's proposal. References in the disclosed plan to a previous revision were unavoidable parts of this input; they did not supply another review's findings or score.

**Research-plan readiness: 7.6/10. CPU-ready verdict: yes for bounded feasibility work, after authorization; not yet a completely frozen model-call protocol.** The remaining specification corrections below can be made before the affected implementation or first call without adding algorithms. There is no scientific reason to demand successful GPU results before permitting the registered small CPU prototypes. This review itself authorizes no execution.

## Read record and limits

I read the complete `round_02_input_plan.md` (§§1–8.5) and complete `round_02_input_contract.md` (§§A–G), treating the latter as authoritative. I did not follow their links to other review-folder files. I read all substantive sections of these five reports, including their validity and cost discussions; long case/stratum appendix tables were read as aggregate evidence rather than independently recomputed:

- `docs/experiment_reports/RQ4_1_Qwen_Analysis_2026-10-09.md`.
- `docs/experiment_reports/RQ4_2_Qwen_Analysis_2026-10-10.md`.
- `docs/experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md`.
- `docs/experiment_reports/RQ3_21_Qwen_Analysis_2026-10-06.md`.
- `docs/experiment_reports/RQ3_20_Qwen_Analysis_2026-10-06.md`.

I read §3 of `docs/experiment_plans/RQ4_3_Source_Local_Visual_Prefill_Draft_2026-10-10.md`, the complete `important_docs/CanvasRCA_Pure_Visual_Direction_2026-10-06.md`, and the applicable `Codex.md` authorities: latest balance/scorer/RQ4/pure-visual/single-stage/attention/renderer rules, unified contracts, local execution and inference, segmentation/privacy, scoring/equal-information, artifacts and smoke/monitoring bounds. Historical RQ3 execution instructions do not authorize this RQ4 experiment. The supplied current task governs this review's no-execution boundary and permitted selection differences.

For the requested installed-kernel check, I performed static reads only of `/home/lglsj/CanvasRCA/venvs/infer/lib/python3.12/site-packages/transformers/models/qwen3_5/modeling_qwen3_5.py`: import availability branches, `torch_chunk_gated_delta_rule`, native GDN forward/cache handling, eager attention, and `Qwen3_5Attention.forward`. Its SHA256 exactly matches contract C1: `0e2cd8dc50885b2701d26b116c585eedcdc62a24080ec34345af55b963126ded`. Package metadata confirms torch 2.11.0 and transformers 5.14.1. No model import, tensor computation, test, renderer, GPU process, or qualification ran. Model configuration dimensions and historical runtime identity remain contract/report evidence; I did not load the checkpoint or independently reconstruct historical environments. The package-file inventory did not reveal FLA/causal-conv1d metadata, which is not equivalent to a runtime import probe.

The Phase A access limits remain: actual indexed OpenReview review/discussion excerpts were read, while live forum/API access was blocked. The four papers provide standards and nearby concepts, not exhaustive novelty clearance for this exact proposal.

## Assessment against history and contribution

U is the defensible starting point. RQ4.1 reports U MRR .3517 versus T_FULL .4846; RQ4.2's SEM and NATIVE4, approximately .3084 and .3235, do not justify replacing U. RQ4.1 also shows why protecting anchors is insufficient: anchors occupy approximately 86%–90% of retained tokens, while almost saturated structural coverage does not establish successful reading. Its large token reduction produced only a small measured online-time reduction, and its historical timing omitted parts of the newly proposed cold path. Those are concrete reasons for the new geometry and cost measurements.

The .5054 MARGINAL_FIVE reference is correctly described as a historical mixed-input system. RQ3.16's comparison with MARKLESS_FIVE (.4963) gives only .0091 MRR, with 209/220 reciprocal ranks unchanged; the full improvement cannot be credited to distribution marks. RQ3.21 further warns that retaining information through a compact encoding does not preserve model accessibility: CV roughly .4180 versus RAW_VISUAL .4934, plus reading and stage-comparison losses. RQ3.20's invalid acquisitions and almost empty extra evidence make a repaired two-stage pipeline a different historical question, not an authorized successor. The present plan correctly avoids reviving it.

The plausible contribution is narrow: source-audited local bidirectional supplementation of a frozen hybrid language backbone, and measured allocation of a fixed retained-token budget through renderer geometry. Facility-location-like selection, rank differences, horizon graphs, and bidirectionality are not themselves novel. The plan acknowledges this. A coherent negative finding is possible if valid extra local context fails to improve reading/RCA, or if grid savings fail to repay compilation and inference overhead. A broad claim that visual representation intrinsically beats textual telemetry would remain unsupported.

The nine optimization positions meet the requested three directions without a parameter sweep. The simple controls are useful, particularly GLOBAL_BI and BG_FILL. They need not all survive applicability and redundancy checks. Cancelling an infeasible direction, including the preselected X that depends on it, is a legitimate outcome; substituting a successful exploratory winner into confirmation would not be.

## Must fix before the affected implementation or first model call

### 1. Write the exact SOFT_IMAGE output equation, including the installed attention gate

Contract C2 says to normalize the two outputs separately before mixing. That is not an executable definition: separate softmax normalization of logits is different from L2/RMS normalization of output vectors. The installed attention implementation also computes a query-dependent gate, multiplies the attention output by `sigmoid(gate)`, and then applies `o_proj`. C2 specifies Q/K normalization and cache handling but does not locate its mixture relative to this gate/projection.

A minimal resolution is an explicit equation such as `o_proj(sigmoid(gate) * ((1-lambda)*softmax(L_native)V + lambda*softmax(L_aux)V))` for eligible image queries, preserving all original reshapes, Q/K normalization, MRoPE, scale, and native text-query computation. If a different vector normalization is intended, name its dimension, epsilon, parameters and exact placement. Do not silently invent an extra normalization while coding. This clarification governs P_SOFT_IMAGE and P_DUAL; it does not block unrelated S/R CPU work or the well-defined local GDN prototype.

### 2. Freeze the sham permutation and forward-only formula

“Fixed-seed regrouping with equal group sizes” leaves several materially different controls: which token permutation generator and seed derivation, whether the same mapping persists across layers, how positions within a sham group are ordered, and what happens when the draw leaves true memberships unchanged. Register one deterministic mapping algorithm and hash its realized groups before calls; require the already stated real intervention, without searching multiple seeds for favorable outcomes. Use the same eligible set and group-size multiset as P_LOCAL_BI. Explicitly state the C_LOCAL_FORWARD fusion, presumably `(1-lambda)*native + lambda*forward`, rather than leaving open whether a removed reverse term is still divided by two. These are definitions of existing controls, not requests for more arms.

### 3. Make the primary QA denominator executable when S removes a target

Contract E commendably distinguishes target coverage, fixed-question end-to-end accuracy and common-visible reading accuracy. However, its “case-level primary QA score is the proportion correct among applicable questions,” together with F's comparisons on “applicable common cases,” does not identify which of these becomes each registered Holm contrast. The treatment of a structurally valid but omitted target and an `unavailable` response needs to be explicit.

Freeze structural target applicability from the original pool; record visibility separately. Define one primary score, including whether an omitted original target contributes zero to end-to-end accuracy, and keep honest unavailability/conditional reading as separate reports. Specify common-visible intersections at the question level, how case means are constructed, and how a case with no jointly visible questions is handled. Do not credit unavailability as correct reading of a missing value or discard omitted targets from the end-to-end denominator. This can be resolved entirely before model responses exist. The current coverage safeguards are good, so this is a remaining ambiguity rather than evidence of actual selective reporting.

### 4. Extend the historical-identity gate explicitly to factorial and order claims

Contract D correctly refuses exact computational equivalence if historical libraries differ. Apply that rule explicitly to all U-containing factorial contrasts, optimization comparisons and order-versus-repeat inferences, not only to the headline P comparison. A common runtime effect does not cancel when U is historical and the other factorial cells are current. For a simple additive current-stack shift `c`, `SR-S-R+U` contains `-c`, and the three-way contrast contains `+c`.

The minimally sufficient rule is: report these as scientific intervention/interaction tests only when the relevant baseline generation identity is demonstrated compatible. Otherwise retain descriptive historical-system comparisons and current-versus-current contrasts, mark the affected causal interpretations ineligible, and say whether the composite contribution can still be evaluated. Do not use a few matching greedy outputs as proof of universal equivalence. No full baseline rerun is demanded. The planned 60 current U repeats can provide diagnostic evidence on their registered subset, but they do not silently replace the historical 220-cell factorial design.

This conditional safeguard is already supported in spirit by D; making its reach explicit prevents the existing invalid-comparison cap in my rubric from being triggered later. I have not established that a mismatch actually exists.

### 5. Align R's stated intervention with the mandatory font enlargement

Contract B requires all new R diagnostic text to be at least 18 processor pixels, starting from U's roughly 12–16 pixels. Consequently R_HORIZON does not merely replace a metric encoding while leaving every other component visually unchanged: trace/log/identity typography can also change. R-versus-READ_GUIDE includes readability, encoding/layout, and token-allocation differences. It cannot independently identify horizon encoding or grid packing as the cause of a gain.

Keep the existing arms and accurately name that compound intervention. OFFSET and BG_FILL retain the successful R typography and support their narrower phase/allocation comparisons; neither isolates the general font-enlargement effect against U. A font-matched extra baseline is optional and unnecessary for the bounded system claim. Narrowing the mechanism claim is preferable to automatically expanding this matrix.

### 6. Reconcile attention overhead measurement with the fixed smoke, and state the timing threshold's aggregation

G1 promises a paired attention-on/off smoke measurement, but plan §8.3 spends all 18 slots on different listed requests, with no identifiable same-input on/off pair. Register where that pair comes from within the existing cap, or remove the unsupported promise and disable optional collection when overhead cannot be qualified. Do not add an informal nineteenth generation or call a different-arm comparison an instrumentation-overhead measurement.

Also state unambiguously whether the 1.05 cold-latency gate is the pooled mean over 12 pairs or a separate mean for each four-case dataset slice. Contract G1 reads as the pooled 12-case gate; §8.4 can be read as a per-dataset gate. Both are measurable engineering policies, but implementation must not choose after seeing timing. Report all individual ratios and dataset counts either way.

## Installed-kernel and practical feasibility assessment

The local GDN contract is substantially coherent. The installed torch fallback accepts and ignores miscellaneous kwargs, so packing sources with `cu_seqlens` would not establish isolation. C1 instead uses the batch dimension and length buckets, which is a defensible design. The source confirms q/k L2 normalization with epsilon 1e-6, float32 internal accumulation, internal chunk padding, and native state updates. Reversing q/k/v/g/beta together and preventing local temporary states from replacing native caches are the right distinctions. The method is deliberately applied after the original causal short convolution; it is not permutation invariant, and the plan correctly avoids that claim.

“Chunked” should not be mistaken for a fused fast path. The inspected fallback contains a 63-step triangular-update Python loop per invocation and a loop over sequence chunks. This does not violate the ban on writing a new per-token production loop, but many small groups and padded batches can be expensive. The extra q/k/v materialization, per-group state, float32 intermediates, scatter/gather, and allocator overhead must enter peak-memory and wall-time measurements. Batch grouping is a plausible prototype, not demonstrated 5%-overhead feasibility.

R has a severe but empirical feasibility risk: simultaneously enlarge diagnostic text, preserve wrapping/card dimensions/plot dimensions, restrict moves to ±16 processor pixels, and reduce anchors by at least 10% in half of each dataset. Crowded original cards may simply fail. That is precisely what the proposed fixed and dense/long-name CPU fixtures should decide before preparing 220 images. Likewise, S may lose most optional freedom through protected entity×modality coverage and indivisible-card closure, or its strict comparability keys may leave objectives dominated by deterministic filling. Those are legitimate CPU cancellation tests, not reasons to relax protection or invent new feature semantics.

The frozen X_SRP depends on all three directions. If one fails its registered applicability rule, the main combined-method objective ends; surviving exploratory arms can still produce useful, honestly scoped findings. The plan should preserve that consequence rather than treating every direction as guaranteed viable.

## Statistics, confirmation and deployment claims

The statistical plan is considerably more careful than using 220 independent incidents by default. It distinguishes 193 event groups, case-weighted ΔMRR, equal-group effects and dataset macro averages; states the signed-rank null; handles zero/tied/constant differences; registers contrast families and fixed missing-test placeholders; and retains unknown-outcome bounds. Shared source environments still limit independence and transfer beyond these corpora. The signed-rank result supports its stated symmetric location hypothesis, not an arbitrary mean-effect claim. Strong asymmetry or sparse discordances should restrict interpretation, especially for the discrete flip endpoint.

I respect the prohibition on confidence intervals. I do not recommend adding them. Within that rule, raw paired effects, group/distribution summaries, effect sizes, explicit test assumptions, unknown-outcome bounds and the stated simulation sensitivity provide useful reporting. The residual limitation is that the precision of estimated general-population performance and cost will remain less directly quantified. No significant-difference result should be rewritten as equivalence, and a nonnegative subgroup point estimate is not statistical proof of no harm.

The supplied planning simulation is appropriately labelled a scenario analysis. At a +.03 group effect, approximately 20%–54% detection in its two historical-amplitude scenarios is weak power, not successful justification for confidently excluding smaller gains. It also does not establish simultaneous power for X beating both U and T, power for 11/12-member secondary families, or transfer to the optional new cohort. I would keep the limited claims rather than spend the remaining budget on more arms. Freeze the new-cohort sample size and attainable power/sensitivity before confirmation calls, and specify what constitutes a successful confirmation separately from its entry rule. The present “at least 30 per dataset” is a feasibility floor, not an adequacy proof.

The confirmation proposal is a real strength: fixed X, new audited event groups, label-blind selection, paired U/T on the same new identities, no winner substitution, and a stop if sufficient unexposed groups do not exist. The exposure audit must cover prior tournament/search/qualification feedback as well as formal report rosters; “unused” is not sufficient. If confirmation is unavailable, this remains exposed development evidence.

The cost design now measures the same proposed deployed configuration, from public-package reading through answer validation with case caches off, and separates model loading. This directly addresses the DaSS/FastV standards fixed in Phase A. Include operator/compiler overhead even if artifacts are usually prepared in advance; additionally describe warm reuse if useful. The 12 current-stack U/T/X pairs are a sensible bounded compatibility/timing check, but four cases per dataset cannot support precise general speedup or reliable tail-latency claims. The full new-arm timings are informative, while historical U/T timings must remain separate. Passing the small engineering gate is evidence to proceed, not proof that population deployment cost is within 5%.

## What not to add; optional improvements

Do not add another model, training, textual diagnostic fallback, a model-driven selection stage, more intensity settings, another selector to force differences, a full historical baseline rerun, or new algorithms to fill cancellation slots. Do not turn 60 marked QA cases into a general chart-reasoning benchmark or attention into a causal explanation. Do not require GPU success before the bounded CPU stage.

Useful optional work, without new model arms, is a compact claim-to-contrast table; static estimates of group-length/padding/state-memory distributions; an operator-cost breakdown for the finite label search; and a prespecified table of applicability versus density/entity count. A focused final novelty comparison with the closest source-aware visual compression and frozen bidirectional-inference methods will be needed for a paper. My four-paper Phase A is deliberately not an exhaustive novelty search.

## Frozen-rubric scoring and decision

| Dimension | Weight | Score / 10 | Reason |
|---|---:|---:|---|
| Scientific question and contribution | 15% | 7.0 | Clear falsifiable local contribution; originality and consequential benefit remain unestablished. |
| Meaningful interventions and mechanism | 15% | 7.5 | Useful source/global/sham/forward and allocation controls; exact operators and compound R interpretation need correction. |
| Fair controls and baseline fidelity | 20% | 8.0 | Strong baselines and input accounting; historical compatibility must explicitly gate factorial claims. |
| Statistical validity and selection discipline | 15% | 7.5 | Fixed effects/families, grouping and confirmation are strong; low small-effect power and QA-primary ambiguity remain. |
| End-to-end deployment efficiency | 15% | 8.0 | Continuous cost and current paired timing are planned; small timing coverage and real fallback overhead limit claims. |
| Robustness and transfer | 10% | 7.0 | Relevant boundary cases and subgroup reporting; one architecture and exposed development data limit transfer. |
| Reproducibility and feasibility | 10% | 7.5 | Detailed finite contracts, budget and fallback identities; several exact definitions and material empirical feasibility remain. |

Weighted score = **7.55, reported as 7.6/10**. No rubric override is applied: I found no demonstrated label leakage, no presently asserted invalid comparison, a total-cost measurement is planned, and causal claims can be restricted to their discriminating controls. If historical identity is incompatible and U-containing contrasts are nevertheless asserted as intervention effects, the invalid-comparison override would apply; this review does not pre-approve that interpretation.

**Hard blockers to bounded CPU work: none identified. Hard blockers to freezing affected model calls: the unresolved operator/control/QA definitions and smoke accounting above.** Historical computational identity and renderer/kernel feasibility remain explicit gates with stop/narrow-claim outcomes; they need not already be empirically successful for CPU work to be informative. All current activity remains review-only until the parent/user authorizes the next stage.

**Publication recommendation, separately:** not submission-ready and no acceptance prediction. Even a cleanly executed study could yield incremental or inconclusive results. A credible paper would require a meaningful accuracy–actual-cost result or a well-supported, consequential mechanism/negative finding, faithful historical/current comparison labels, and appropriately bounded confirmation. Readiness measures whether the proposed study can now be made executable and informative, not whether it will produce favorable scores.

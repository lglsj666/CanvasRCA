# RQ2.1 registered experiments and execution contract

## DD-RQ21-ANCHOR-04: Fixed parent anchors; resume authorized

**Date:** 2026-09-09. **Status:** adopted; supersedes SELECT-01/02/03
champion execution and the earlier pause, not their historical observations.

**Decision.** Keep selection at P×S0×D0. Run silhouettes at P0×S×D0,
and composition at P0×S0×D. All existing arms, facts, rendering operations,
prompts, models, request adapter and scoring stay unchanged. No champion is
chosen or consumed; the champion-based cube is not run. P0 is the inherited
reference, not a new efficacy claim. No QA or training is added.

**Data and analysis.** All 480 cases from all five datasets are included.
Report each dataset and an equal-five-dataset descriptive macro, separately by
model; also retain pooled case-weighted summaries as explicitly descriptive.
The old 90/210 roles remain immutable historical strata, not selection criteria.
Same-case tests, error policies and comparisons to the current stage baseline
remain; all-cases per-dataset families are primary for this amendment. Legacy
subset tables are supplementary. These are repeated-exposed, not untouched,
evaluations. No combined-champion or universal-component claim is available.

**Execution.** Completed selection stays in `exp_evidence_selection_formal_v1`.
The old partial silhouette run used P_TRACE_SC (1,459 terminal outcomes).
The user authorizes removal of its owned formal outputs, but not shared
preparation, selection results or initiated-call history. New namespaces are
`exp_silhouette_encoding_formal_p0_v2` and
`exp_canvas_composition_formal_p0_v2`. Exact-request reuse from retained valid
records remains allowed. Preserve the old champion artifact as inactive history.

**Budget.** Planned formal calls are 15,360 + 10,560 + 9,600 = 35,520.
The aggregate cap stays 39,999, including already spent, removed-result calls,
smokes and repairs. The 4,425 nominal repair/successor allowance is not fresh
credit: actual initiated counts always determine remaining capacity.

**Qualification.** The user waives another smoke for this baseline-only change.
Static/CPU verification and unchanged input-producing/scoring/runtime functions
are required. Retain the actual prior smokes without relabeling them as fresh.
Run both models of silhouettes, then both models of composition, in the original
model order. Monitor every 900 seconds and audit one new completed case hourly.

**Consequences.** This design measures conditional changes around P0/S0/D0;
it does not assemble a claimed best pipeline. RQ3 is refined only after final
RQ2.1 analysis, then reviewed and smoke-tested, with no training launch.

All champion, cube, split-selection and paused-execution text below is retained
as superseded protocol history wherever inconsistent with this amendment.

## DD-RQ21-SELECT-03: Offline five-dataset selection audit

**Date:** 2026-09-09 (UTC)
**Status:** analysis completed; replacement production protocol not activated.

The user requested a selector that includes all datasets and tests whether its
choice remains useful outside the cases used to choose it. Implement
`FiveDatasetGroupedSelectionV1` as an offline analysis in
`tmp/rq21_champion_selection/`: equal weights for five datasets and two models,
the existing Vision objective and admissibility/tie rules, grouped five-fold
assessment, complete-dataset holdout checks, and a joint TrainTicket holdout
sensitivity. Source groups are formed before reading scores. Do not promise
guaranteed superiority, optimize fold seeds, or force selection of a new policy.

All 480 cases' completed Vision records are available. P0 is the all-data
empirical macro-MRR leader (0.357765 versus P_TRACE_SC 0.356407) and the only
admissible shared policy. Every cross-validation fold and dataset/application
holdout check selects P0; their paired improvement over P0 is therefore zero,
not evidence of a new strategy's advantage. Ten CPU tests passed; zero model
calls were made. Detailed results and limitations are in
`RQs/RQ2_1/results/exp_evidence_selection_formal_v1/analysis/five_dataset_selection_v1/report.md`.

This is post-hoc/exploratory: earlier outcomes were already inspected. Grouped
cross-validation assesses the selection procedure, not an independently tested
all-data fixed champion. The original P_TRACE_SC artifact and all inputs,
outputs and partially completed downstream results remain unchanged. This
analysis neither overwrites that artifact nor resumes execution. Dataset
eligibility follows DD-RQ21-SELECT-02; adoption of the full replacement rule and
its downstream consequences still requires resolving the current user pause.

## DD-RQ21-SELECT-02: Include both RE2 datasets in champion selection

**Date:** 2026-09-09 (UTC)
**Status:** adopted for dataset eligibility; replacement selection protocol pending.

**Context.** The user paused execution to reconsider champion selection. The
earlier three-dataset scope inherited a historical saturation assumption; that
assumption does not establish saturation for the current models and visual
conditions.

**Decision.** RE2-OB and RE2-TT must participate in champion selection. This
supersedes the dataset-exclusion clauses below. The user is still discussing
whether to retain a selection/report split or use all cases; no replacement
quota, weighting, or champion has been adopted.

**Evidence.** Completed P0 results include all 90 cases per RE2 dataset and
model. Their visual MRR ranges from 0.3556 to 0.6000, so a blanket saturation
argument does not justify excluding these datasets. These observations do not
establish a new winner or an accuracy-gain claim.

**Alternatives rejected.** Continuing to exclude both RE2 datasets solely on
the historical saturation rationale was rejected by the user. Retaining a
selection/report split versus selecting on all 480 remains unresolved.

**Consequences.** Execution remains user-paused. The configuration and runner
still implement the preceding selection protocol and must not resume until the
replacement is agreed and implemented. Preserve all completed inputs/outputs
and the original P_TRACE_SC champion artifact as evidence of the previous
rule; do not relabel it as a five-dataset winner. No inference rerun or scientific
input change is authorized by this eligibility amendment alone. The execution
status and selection clauses below describe the preceding protocol wherever
they conflict with this amendment.

Status: original smokes plus authorized two-call repaired-overlay supplement
and current-version artifact reviews passed on 2026-09-08; formal execution is
enabled. Original qualification history remains intact. This explicitly
supersedes the earlier pre-smoke user hold. The user-approved
2026-09-07 plan supersedes RQ2. Three experimental stages share a 39,999 initiated
call hard cap, including smoke and repair; planned formal maximum is 39,360
after the user-approved 2026-09-08 compact-density amendment.

## Common controls

Reuse canonical public V3 cases and the original RQ480: primary datasets have
100 cases each, RE2-OB/TT 90 each. Use the unified segmentation identity mapping.
Group source-event aliases and transitive same-source overlapping windows,
hash-sort groups with seed 42 and select exactly 30 per primary dataset without
splitting groups. The remaining 210 primary cases and 180 RE2 cases never choose
champions. All 480 run all registered conditions. Register both partitions before
new calls and call this repeated-exposed evaluation.

The unified local Qwen3.8/Gemma runtime is unchanged. Both use the inherited
`context_safe_output_v1` adapter, actual maximum output 8,192 and input at most
32,768, not the global 16,384 output ceiling. Candidates and case-local numeric
service/node/pod IDs (3/4/5 digits) are identical across models and arms. The
granularity-aware top-five JSON scorer and scientific SIRCL VERIFY procedure,
M→R→L→G reading order, labels/private isolation and same-call attention remain.
Text never receives image-only reading instructions. No arm/tool/champion name
is model-visible. Missing values are not zero. No injected time enters input.

The CPU-only complete public universe is computed once per case. A selector
returns item identities/native ranks; fixed field/time/precision/missingness
projection produces selected evidence; fixed grouping produces cards; a
silhouette encodes each card; the compositor arranges whole silhouettes.
The renderer must not secretly select again or omit facts to fit. Full telemetry
is never serialized into an enormous Solver prompt.

Interfaces: EvidenceUniverseV1, SelectionResultV1, SelectedEvidenceV1,
SilhouetteSpecV1, CompositionSpecV1, BridgeReferenceV1 and ManipulationAuditV1.
The last traces native ranks → selected IDs → semantic facts → ordered text →
decoded PNG pixels → complete request, not merely metadata/config hashes.

## Bridge and calibration

P0 is `R1-PanelSelect-v14`, the actual parent selection and displayed projection:
12 k-sigma-ranked metric series with 64 bins; TRC-L displayed ranks/capacity;
LOG-R entity priority plus frequency fill and bounded Denum previews; original
propagation/subgraph/edge capacities, ties, omissions, windows and precision.
It is not full raw data or a generic weighted four-region top-k.

B_T/B_V reference original RQ1.1 T/V requests and results in place. Never rerun,
rewrite or relabel them. T0_CAL/V0_CAL use P0 and a neutralized RQ2.1 description
layer; V0 retains S0/D0 diagnostic pixels except explicitly registered policy
captions. A single conditional visual grammar covers every new encoding.
Scientific reasoning, evidence and output instructions otherwise stay fixed.
Reuse T0 if its complete request equals B_T. Report calibration minus bridge
separately; new stage comparisons use calibration, not an inaccurate old guide.

## Experiment 1 — exp_evidence_selection

Eight selectors, each with T/V twins of the same selected evidence using the
parent display projection, hold S0/D0 and the new common
guide fixed. Maximum 8×2×480×2 = 15,360 calls, including calibration.

| Policy | Registered action |
|---|---|
| P0 | original selection/display projection |
| P_SIGMA | native SIRCL three-sigma metric ranking, M only |
| P_BARO_RS | official BARO 0.1.9 RobustScorer, M only |
| P_TRACE_SC | SIRCL anomalous-span support/confidence harmonic ranking, R only |
| P_LOG_FREQ | SIRCL Drain template-frequency ranking, L only |
| P_COVERAGE | maximize uncovered entities/families/operations/templates/graph endpoints |
| P_DIVERSITY | fixed relevance/novelty trade-off |
| P_RANDOM | hash(seed, opaque case, region, item) ordering |

Vendor originals with file hashes, license, version and dependency closure
before minimal adaptation. Change paths/schema, public analysis-split injection
and structured-output bindings only, plus documented correctness repairs. Do not
claim SIRCL adapters are original paper implementations or RobustScorer alone
reproduces BARO's full detection/RCA system. Preserve BARO's `max(scaled_current)`,
not an absolute maximum. Expose native scores only to audit, not the Solver.

All strategies use the same parent per-case region capacities: M12×64;
R/L/G inherit visible item/entity/edge capacity. Native insufficient valid
rankings fill by P0 order and report fill rate; exceptions are not successful
fallbacks. Drain-to-Denum bindings use source-event indices, not guessed string
similarity. The statistical split, units and displayed fields do not change.

Coverage first adds entities, then new semantic families/operations/templates;
G adds endpoints/components. Ties use parent relevance then frozen hash.
Diversity uses λ=0.5: normalized regional relevance minus maximum similarity.
M uses positive correlation on common finite bins for same-semantic/same-unit
series; negative correlation is not redundancy, and only identical constants
are duplicate constants. R uses entity/operation identity; L token Jaccard;
G endpoint overlap. No NaN-to-zero similarity. These are declared project
adaptations of MMR, not an externally validated RCA benefit.

Formal-capacity fixtures must show actual selection differences. Natural
identical selections remain in the primary denominator. If final requests are
identical, reuse a same-model result with logical-arm aliases and no false
independent samples; metadata/PNG metadata differences do not qualify as changes.

## Experiment 2 — exp_silhouette_encoding

Fix P*, D0, facts, card membership, regional positions, canvas and guide. A
metric horizontal row may be one multi-plot card; R/L/G are whole-region cards.
Grouping is frozen once, then never split or merged to fit a later design.
S0 is reused; eleven new conditions cost at most 10,560 calls.

| Design | Encoding change |
|---|---|
| S_M_HEATMAP | all 64 time bins as annotated heatmap |
| S_M_TIME_BARS | all 64 time bins as bars, not a distribution histogram |
| S_M_OVERLAY | up to three compatible curves per axis; otherwise facets |
| S_R_PAIRED_BARS | baseline/current bars |
| S_R_DUMBBELL | baseline/current joined points |
| S_L_MATRIX | template×time matrix plus retained template/count/numeric fields |
| S_G_MATRIX | directed adjacency with all node/edge/propagation metadata |
| S_G_LAYERED | directed layered graph retaining cycles, isolated nodes and cross-edges |
| S_TABLE | organized exact-fact table, not a screenshot of T |
| S_COMPACT_MIX | metric heatmap, trace dumbbell, log and topology matrices |
| S_DENSITY_COMPACT | S0 encodings with tighter internal gaps; no new facts or smaller fonts |

### Overlay rendering amendment — 2026-09-08

For `S_M_OVERLAY`, connect adjacent finite observations at their original
time-bin positions, retaining small observation markers.
This user-selected line rendering supersedes the intermediate point-with-gaps
repair. Underlying values, time bins and the inherited S0 renderer are unchanged.
The subsequent user amendment removes the extra missing-bin crosses and their
axis legend from the new metric encodings, and removes their explanation from
the common visual guide. Keep ordinary axis labels and original values; do not
fill missing bins or add an explanation about connecting across them. Historical
inputs remain unchanged; qualification uses the updated guide and images.

### Compact-density amendment — 2026-09-08

Compare `P*,S_DENSITY_COMPACT,D0` with the already registered `P*,S0,D0`.
This is one extra condition in this experiment, not a fourth experiment/smoke.
It adds at most 480×2=960 calls, leaves the total hard limit at 39,999 and
reduces retry/repair reserve from 1,545 to 585. The prior 38,400-call formal
registration is superseded by 39,360, not enlarged beyond the hard cap.

Keep selected facts, card membership/outer boxes, chart encoding, axes,
colors, glyph sizes, source resolution and every prompt byte fixed. Compact
only exact uniform-background internal corridors: between complete metric mini-panels,
between text rows in R/L, and between rows in the G edge ledger. The connected
G plot stays intact. Halve eligible gaps with a six-pixel safety floor; move
whole pixel strips without interpolation, scaling, recoloring or removal of
any non-background pixel. Existing panel frames are preserved by a four-pixel
interior inset on framed L/G ledger cards. The freed area remains neutral inside the same card;
never fill it with additional evidence. Record strip translations, unchanged
ink content, internal occupied extent and actual/no-op changes per card.
This tests local packing/readability, not an increase in facts per outer-card
pixel or a uniform density change in every modality. Cases without eligible
gaps stay in the denominator; identical requests are reused normally.

`S_COMPACT_MIX` changes encodings and is not this density control.
`D_COMPACT`/`D_AIRY` still control perimeter space in the composition stage.
The new S condition participates in the existing silhouette-vs-S0 Holm family,
shared-champion selection and downstream composition/cube if selected. It
inherits S0 feasibility and cannot repair an incomplete S0 evidence carrier.

Overlay requires matching units/semantics/time, no dual axes; record effective
overlay coverage. Neither matrix nor graph may hide direction/onset/severity or
other registered fields. A fact must bind to a genuinely drawn primitive.
Changing readability is a treatment; not drawing required evidence is a bug.

## Experiment 3 — exp_canvas_composition

Fix P*, S* and cards. D0 retains parent coordinates; deterministic integer-grid
packing moves whole cards without deleting/splitting facts or changing axes.
Ten new conditions cost at most 9,600 calls.

| Design | Change |
|---|---|
| D_COMPACT / D_AIRY | non-content gutters/padding ×0.5 / ×1.5 |
| D_ENTITY | order whole cards by minimum numeric entity anchor |
| D_TOPOLOGY_CENTER | topology centered, related cards around it |
| D_ONSET_ORDER | earliest public onset; unknown last |
| D_LANDSCAPE / D_PORTRAIT | 4:3 / 2:3, integer dimensions within parent pixel count |
| D_SCALE_075 / 125 / 150 | raster scale .75 / 1.25 / 1.5; D0 supplies 1.0 |

Record aspect rounding error, original pixels and actual processor geometry,
image tokens and glyph/line sizes. Four scale points support descriptive trends,
not a global resolution optimum. Entity ordering does not promise one entity's
complete evidence on a single row.

Complete P0/P* × S0/S* × D0/D*: reuse 000/100/110/111 and add 010/001/011/101,
at most 3,840 calls. Degenerate winners reuse outcomes. Report conditional
main effects, two-way and three-way interactions; any Shapley decomposition
applies only to these registered two-level anchors.

## Champions and statistics

Choose one shared Vision champion per stage from selection cases only, with
equal weights for each model×primary dataset. A ≥.05 MRR loss in any such cell
vetoes a challenger. Within .01 of the best MRR, choose lower relative input+
output tokens, fewer parent changes, then lexical ID. Keep the baseline eligible.
Never select using success-only cases or change a winner using reporting data.

Primary MRR; secondary AC@1/3/5, AVG@3/5, repair/break/rank movement, input/image/
output tokens separately, existing latency/GPU metrics. Case-level paired
Pratt-Wilcoxon and Cohen's dz, no CI. Each stage's new-vs-baseline contrasts
across both models form one declared Holm family; original-bridge contrasts
form a separate family. ΔMRR≥.05 and adjusted p<.05 are required for an
improvement claim. Grouped sensitivity analyses cover AIOPS-2022/AegisLab.
Same-policy V−T contrasts form their own mechanism family, jointly across
both models, and use the same whole-case exclusion mask as the stage analysis.
Report selection 90, main reporting 210 and all-480 descriptions separately.
Small effects may be inconclusive. RE2 never supports the headline inference.

Mechanism analysis follows public-pool availability → selection → actual
visibility → public reason citation → rank change. Labels/fault/granularity
are evaluator-private only. Report coverage, redundancy, fill, root-associated
availability/citation, unsupported claims, missingness and density strata.
Attention uses actual processor geometry and exact pixel overlap, area-normalized
visual density and token-normalized text density; header/blank are separate.
It is neither a reward nor causal proof. Input savings are not output savings;
cross-model cost comparisons use ratios to each model's baseline. No claim of
beating all text compression without an equal-content compact-text control.

## Outcome, recovery and call accounting

All generation uses locally deployed Qwen/Gemma through the local vLLM server.
There are no Nibi jobs or paid remote model services. The local call register
is an execution/recovery record and call-count guard, not a financial ledger.

Wrong roots/fewer than five candidates are normal outcomes. Model truncation
and malformed answers remain terminal results, not invitations to resample.
Checked geometric/context infeasibility makes no model call, is separately
reported, and has zero end-to-end utility. It must not conceal implementation
errors. Infrastructure/persistence/hash failures are diagnosed then retried
with the same input; residual paired whole-case exclusion is at most 5% per
experiment/model. Parse rate below .95 makes that model's conclusion incomplete.

Budget: 39,360 formal + at most 54 smoke + 585 repair = 39,999. Every initiated
retry counts; reuse does not authorize extra arms. Durable request keys include
model/effective recipe, full input, adapter, schema and replicate. No cross-model
reuse. Interruptions restart only unfinished/damaged units, not valid other arms.

## Six reviews, qualification and execution

Three distinct logic passes: scientific controls/selection; tool/data semantics;
representation/card/interactions. Three code passes: numeric/schema/cache keys;
renderer/attention geometry; scheduling/persistence/resume/budgets. Each has its
own checklist and recorded findings, not six executions of one linter.

CPU checks compare original/adapted tools, real-capacity interventions, no-ops,
T/V facts/candidates/precision/missingness, fixed statistics windows, all cube
conditions, long names/constants/missing baselines/isolated nodes/cycles/duplicate
span IDs, both model token budgets, complete conversations/attention and recovery.
Inspect three hash-random selection cases per primary dataset across key design
families (nine distinct cases), including sparse/dense/long/missing conditions.

Each experiment has one bounded smoke: two sequential models, aggregate at most
18 initiated calls and 600 seconds including startup/switch/drain. Use one fixed
selection case per primary dataset, no RE2; remaining combinations get CPU
coverage. Assign arms within these same three cases using CPU-only geometric
feasibility before the supervisor starts; never replace a selected case or
drop an arm. Retain original and qualified assignments. Formal infeasible
outcomes are unaffected. Timeout-only follows project passage rules but cannot attest unrun
paths. Any non-timeout infrastructure, parity, leakage or persistence issue
blocks formal execution. Inspect every completed input, PNG, conversation,
raw/partial output and accounting. Root accuracy is not a smoke gate.

After all three smokes pass: selection Qwen then Gemma → freeze P*; silhouettes
both models → freeze S*; compositions both models → freeze D*; missing cube
conditions; then unseal reporting accuracy and analyze all candidates. No
cross-experiment model overlap. CPU up to eight physical cores, 36 requests,
eight attention writers, bounded memory/prefetch and pre-submit disk guard.

Operational follow-up (2026-09-08): the 36-request upper limit also uses FIFO
KV-token admission, reserving actual input plus the unchanged output ceiling.
The live server's published KV capacity determines a conservative token budget;
this controls submission timing only, not experimental evidence or decoding.

Smoke monitoring 600 seconds; stable formal 900 seconds; hourly one new complete
case audit of all finished records/conversations/PNG. Sleep is idle; watchdog
is auxiliary. Runtime audits do not display labels or tune to reporting MRR.
Record all issues. Sustained >5% abnormal output caused by a demonstrated
prompt/code defect pauses affected paths; low MRR by itself does not.

## Sources and limits

### 2026-09-08 log-calendar safety correction

Hourly input inspection found calendar metadata inside some Denum templates,
including calendar components represented as numeric preview variables. The
RQ2.1 public projection removes identifiable calendar spans and their preview
variables, without refilling previews or changing diagnostic numbers, relative
bins, multiplicity, LOG-R, selection order, source bindings or quotas. Text and
image use the same corrected rows. No extra Solver instruction is introduced.
Original source graphs and RQ1.1 bridge records remain immutable. Calibration
is now also responsible for this public-metadata safety correction where needed;
it is not attributed to a selector/encoding improvement. Only completed requests
whose actual text/image changes are superseded and rerun. The scoped inventory,
tests and input comparisons live in
`RQs/RQ2_1/results/qualification/log_calendar_repair/`.

[BARO 0.1.9 source](https://github.com/phamquiluan/baro/tree/0c270feae637f000a72edf33a8cd1423672b2c95)
defines the RobustScorer component, not our final RCA policy. SIRCL sources are
vendored local reference code, not relabeled original paper implementations.
[MMR](https://www.cs.cmu.edu/afs/cs/Web/People/jgc/publication/MMR_DiversityBased_Reranking_SIGIR_1998.pdf)
motivates relevance/novelty; our telemetry similarity is an explicit adaptation.
[Vega-Lite](https://vis.mit.edu/pubs/vega-lite/) and
[Draco](https://www.domoritz.de/papers/2018-Draco-InfoVis.pdf) motivate explicit
encoding/constraint separation, not proven RCA benefit.
[NIST factorial design](https://www.itl.nist.gov/div898/handbook/pri/section3/pri333.htm)
supports the small anchor cube's interaction contrasts, not exhaustive design
optimization. These sources provide methods, not promised positive outcomes.

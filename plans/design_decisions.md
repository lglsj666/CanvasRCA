# CanvasRCA project-wide design decisions

## DD-20260930-QWEN-ONLY: Defer multi-model validation until the pipeline matures

**Date:** 2026-09-30  
**Status:** adopted; revisit only on explicit user direction

**Context.** Current RQ3.8 local Qwen execution completed, whereas the dense
Gemma-4-31B-it execution was interrupted after frequent request timeouts.
The project has not yet established a high-performing main RCA pipeline.

**Decision.** Use Qwen3.8-27B as the sole Solver for new development
experiments. Defer Gemma and other-model validation until the method and
experimental findings are substantially stronger. Do not erase or reinterpret
prior Gemma artifacts. New experiments must state their single-model scope;
they cannot claim cross-model generality.

**Evidence.** RQ3.8 DD-20260930-12 records the stop snapshot and artifact
handling. The Gemma results are incomplete and affected by infrastructure
timeouts, so they do not support a model-quality comparison or rejection.

**Alternatives rejected for now.** Continuing Gemma immediately would spend
resources on transfer before the primary method is settled. Deleting historical
Gemma results would destroy auditability and is not authorized.

**Consequences.** The local 31B checkpoint was removed and would need to be
downloaded again for renewed validation. The original RQ3.8 dual-model
registration remains historical; its incomplete Gemma arm is not silently
completed or replaced by Qwen. Remote Nibi artifacts/jobs are untouched until
access and exact targets are confirmed. Cross-model claims remain unavailable.

## DD-20260930-QWEN-REPORTS: Reanalyze the reports as a Qwen-only study

**Status:** adopted by explicit user request; amends the reporting-scope clause
of DD-20260930-QWEN-ONLY, not historical raw-artifact status.

The user requested an intact backup followed by a Qwen-only edition of every
experiment report, with conclusions determined solely from Qwen evidence. The
user specifically requested recomputation rather than retaining adjustment
families containing an out-of-scope model. Positive Qwen findings do not need
cross-model agreement; later comparable-model validation is separate work.

All `docs/` files were copied to
`/home/lglsj/CanvasRCA-report-backup-20260930.zJzQJW/docs` and compared with no
differences before editing. The new report edition retains the full Qwen
contrast sets, original case masks, scoring and error policies; recomputes
available case contrasts and Qwen-only Holm families; and distinguishes
case-level, event-group and exploratory evidence. This is a documented
retrospective reanalysis, not a new preregistration. No inference or experiment
job is authorized by this reporting task.

The active reports may replace earlier interpretations based on cross-model
agreement. The backup and original `RQs/*/results` remain unchanged, including
negative results and failed/incomplete status. Reanalysis must not claim that
a previous run used a different model, nor infer general reasoning capability
from active parameter count alone. Future multi-model work requires its own design.

## DD-20260930-GAP-REVIEW: Prioritize evidence-use mechanisms over more design search

**Status:** research recommendation only; not an adopted runtime protocol or a
new experiment authorization. Retain all existing registrations and artifacts.

**Evidence.** The current Qwen reports establish selective-visual positive
results as well as evidence-selection, node-scope, perception and cost harms.
RQ3.7-C has 4,200 terminal logical targets and the reduced local RQ3.8 Qwen
queue completed, but their complete analyses remain outstanding. The literature
review covers 23 works from 2024–2026 with publication and reading-level labels.
FoundRoot, TORAI, MoCE, FAMOS and the latest DecompRCA preprint already address
several previously broad candidate gaps; dashboard block/graph representations
also have direct prior work.

**Recommendation.** First analyze the already-produced Qwen RQ3.7-C and RQ3.8
results. Test whether real graphics improve a specific diagnostic comparison
beyond matched text, duplicate presentation and factual/statistical changes.
Only then select one or two observable mechanisms for a bounded successor
experiment. Do not claim that generic retrieval/reranking decomposition,
multi-source fusion, graph use, one-shot reasoning or a component library is
novel by itself. Maintain separate claims for ranking, grounding, feasibility,
cost, independent generalization and eventual human/recovery outcomes.

**Alternatives not recommended.** Another broad selector/layout tournament,
automatic training/multi-agent expansion, or immediately scheduling more arms
before analyzing the completed batches. These would not resolve current
attribution and novelty uncertainty.

**Revisit conditions.** The full latest results may support a visual method,
only a restricted conditional benefit, or a negative empirical conclusion.
The recommendation must change with that evidence rather than forcing a
visual-success storyline. No inference, tests or jobs were started by this
review. Details and source links:
[literature gaps and storyline](../docs/CanvasRCA_Literature_Gaps_and_Storyline_2026-09-30.md).

## DD-20260930-C38-ANALYSIS: Preserve conditional fusion evidence; do not promote the full dashboard

**Status:** evidence-backed research recommendation; no new registration,
runtime change, inference, or job authorization.

**Context.** The user requested complete analysis of the already finished Qwen
RQ3.7-C and reduced RQ3.8 before choosing another experiment. The analysis
reads all 9,060 active logical positions, preserves model-output failures,
and excludes RQ3.8 design-infeasible cells under its DD-09. Earlier A/B
results and stopped branches keep their original evidentiary scope.

**Evidence.** Three-main-dataset Qwen results: RQ3.7-C fusion versus old TPV
has eval macro delta +0.0631 (case Holm p=0.00574), but test fusion versus
separate panels is only +0.0032 (p=0.7866). Versus matched text, test macro
delta is +0.0490 (case Holm p=0.0532; event-group p=0.0420). RQ3.8 full
dashboard versus matched text has eval/test macro deltas -0.0716/-0.0771
(Holm p=0.0379/0.00112); test event-group p=0.000679. Specified marks,
M/R factorials and corruption-versus-repeat comparisons do not identify a
reliable positive graphical mechanism. Report denominators, all contrasts,
costs, capacity exclusions, 60-case sample and scoped qualitative reviews
are preserved in the linked report/assets.

**Recommendation.** Do not scale the present FULL dashboard or automatically
complete stopped branches. Retain strong text, TPV and separate numeric
panels as anchors. First identify an observable source/victim or host/instance
comparison failure on existing evidence; only then propose a bounded visual
intervention. Neither a favorable subgroup nor a correct answer with a faulty
reason proves the mechanism. This does not reject visual RCA in general.

**Alternatives not recommended.** Another broad layout/selector search,
promoting LOCAL_LINK's attribution lines as established causal contributors,
or treating graph perturbation response as proof of useful visual reasoning.

**Consequences/revisit.** No executable experiment changes now. Revisit after
a specific controlled diagnostic operation improves matched-text RCA and
passes node/top-five harm checks. Independent-event validation remains absent;
both eval and test are exposed. Results and sources:
[complete Qwen analysis](../docs/experiment_reports/RQ3_7C_RQ3_8_Qwen_Analysis_2026-09-30.md).

## DD-20261001-RENDERER-COMPATIBILITY: Additive design space; correct the metric-clock statement

The user explicitly permits extending the unified renderer's component and
operation libraries, but forbids removing existing entries because historical
experiments depend on them. Preserve component IDs, operation IDs, their
implementations and historical defaults. New behavior must be opt-in through
new components/operations or versioned parameters; do not silently change old
experiment rendering. Existing results, configurations and generated pictures
remain untouched.

Correction to the earlier chat claim: `0..63` is a bin index rather than an
elapsed-time label, but that does NOT imply independently stretched metric
windows. The inspected producer in `RQs/RQ1_1/src/renderer/dashboard.py`
passes the same `metrics_df` to every selected metric. In `panels.py`, bin
boundaries are computed from finite timestamps of that common frame, not
from the nonmissing values of each metric. `src/renderer/exps.py` passes those
bins unchanged into the unified renderer. On that verified same-case data
path, equal metric-bin indices refer to equal time intervals, including when
some series have missing values. This is not a pre-v4-versus-v4 distinction,
nor evidence of a historical metric alignment defect. Do not invalidate or
rerun old results on the basis of the earlier mistaken statement.

This conclusion does not by itself align different cases, trace window
summaries, log bins or onset-minute axes. RQ3.9 checks the public producer and
case timestamp provenance before asserting metric-clock alignment. No ground
truth or injection time is used in that check.

## DD-20261001-RQ39: Bounded Qwen joint-comparison pilot

Following the complete Qwen RQ3.7-C/RQ3.8 analysis and the user's approval to
launch the next experiment, register120 exposed eval cases (40 per primary
dataset), four same-fact conditions and at most480 formal initiated calls.
TEXT_FLAT/TEXT_JOINT differ only in fact ordering; VIS_SEPARATE/VIS_JOINT add
the same ≤6 selected numeric cards and differ only in fixed-slot placement.
The complete original text remains. Existing unified components/operations
are reused without modification; missing-bin sequences use the existing time
bars instead of silently changing the historical line component.

Public preparation found106 cases with eligible comparison groups and14 with
none. The latter remain no-op controls and reuse one generated answer across
identical requests. Planned formal generation is438 unique requests, not480
necessarily-new calls; interrupted attempts still count toward the480 cap.
No test, independent-event, Gemma, SFT/RL, attention or multi-agent expansion.
Qualify once with three development cases and12 planned smoke calls under
the existing18-call/600s bound, then launch in background after inspection.

The exact hypothesis, historical-overlap audit, limitations and statistics are
in `RQs/RQ3_9/descriptions/` and the linked RQ3.9 plan. This is a pilot,
not evidence that the new representation is useful, until results support it.

## DD-20261001-RQ39-HOLD: Formal execution requires a new user instruction

The user withdrew the launch authorization: do not start formal experiments;
if already started, close them and wait for an explicit instruction. This
supersedes the automatic post-qualification launch step in DD-20261001-RQ39
and the RQ3.9 execution notes, without changing the scientific protocol.

The formal supervisor had already submitted36 requests when the stop was
processed. Stop signals prevented new submissions; the remaining runner was
terminated and its owned vLLM server closed. After shutdown, the immutable
call ledger contains5 complete and31 started/interrupted attempts, with5
persisted done flags. Preparation, qualification and partial outputs remain
in place. The supervisor records `interrupted`; its runner/server processes
and port21939 are no longer active. No automatic restart is authorized.
The interrupted attempts remain counted; do not erase them or label this as
a run with zero formal calls. A future resume requires the user's instruction.

## DD-20261001-RQ310: Separate observations, qualified scope tests and visual use

User approved implementation and static checks only after the conversation_oct_01
review and noted the main bottlenecks are the two AIOPS datasets. Register a new
RQ3.10 rather than editing qualified/paused RQ3.9. Use60+60 AIOPS exposed eval
cases and20 Aegis protection cases, six conditions,840 formal positions; total
new initiated-call ceiling900 including18 smoke and42 recovery-only reserve.
No results are opened for roster/parameter selection. Formal execution is NOT
authorized now; neither CPU regression nor GPU smoke/preparation starts now.

Preserve the complete frozen base text. Read the complete cached public Metrics
directory, not its selected top-k, and only selected per-case source columns.
Normal-looking peers count as soft conflict only with comparable metric/unit,
window, coverage and positive independently observed activity. Missing or
inactive evidence is unknown. Root label granularity is not impact scope;
these are measured-resource-scope tests, not causal counterfactual predictions.

Six cells separate extra controls, positive support, soft conflict/unknown,
same-computation strong text, shared-coordinate graphics and unorganized tiles.
Same-evidence CPU ranking is an obligatory non-LLM diagnostic. Add two unified
renderer components; delete/change no existing component or operation behavior.
Do not tune with the five interrupted-batch RQ3.9 outcomes. Complete protocol:
docs/experiment_plans/CanvasRCA_RQ3_10_Scope_Competition_Plan.md.

User's overlap reminder prompted a second source/report audit. RQ3.6-B2 already
uses the name scope_competition and comparable same-host peer selection;
HOST_PEER−ANCHOR pooled paired deltas were only+.0123 Graph and+.0059 Text,
both Holm1. Extra peers, scope wording and positive support are calibration,
not new contributions. Novel hypotheses are qualified stable-active soft
conflict/unknown and its same-computation visual use. Before future formal
execution, report actual eligibility on the full roster to the user; do not
automatically run a mostly inapplicable design or weaken criteria to force it.

Static implementation review corrections: a changed anchor alone contributes
no scope vote, including local-instance scope. Shared-scope positive peers
must change in the same direction; opposite directions stay unknown. The
positive-only condition contains no soft-conflict rule text. Thresholds,
coverage operands and actual activity counts are common to all supplemental
conditions. Nonfinite derived statistics become explicit unknown, not infinity
or a healthy assertion. Source sample counts and rounded medians must match
the committed public binding. Request timeouts remain missing, not zero.

Additive scope cells share deterministic geometry/font scaling and DOM overflow
checks. The bundle is recompiled for new components; legacy component/operation
implementations stay untouched. Historical RQ3.9 qualification/results are not
reclassified or resumed by the new shared-source hash. All initiated attempt
costs, including partial failures, are inventoried; unavailable token usage is
explicitly unknown, never silently omitted or fabricated as zero.

Six exposed-development conditions are840 formal positions, not840 independent
cases. Their strongest text has the same computation and facts as the visual
conditions. This design tests a narrow mechanism; it does not establish final
superiority to TPV/LOCAL_LINK, novelty against the entire literature, or test
generalization. Those claims require a separately compatible paired bridge
and independent evaluation after evidence of useful applicability/efficacy.

### 2026-10-01 RQ3.10 qualification/execution authorization

Latest user authorizes CPU regression and GPU smoke, followed by preparation
and formal execution after passing. Prepare/check only the registered three
smoke cases first; remaining preparation reuses their small commit flags.
Scoped `cpu_smoke.json` cannot substitute for the140-case `cpu.json` required
by formal execution. This is scheduling/qualification scope only; no evidence,
threshold, roster, arm, runtime recipe or call budget changes. Actual
applicability remains a pre-inference scientific check, not a score-based gate.

### 2026-10-01 RQ3.10 actual qualification blocks inference

Three-case CPU regression/capacity passes do not authorize full execution:
the140-case public source audit reports zero testable scope/soft-conflict cases,
all489 selected readings fail64-bin coverage, and73 cases have no eligible
resource anchor. Source acquisition is too sparse for the registered80%
64-bin occupancy criterion. The whitelist/anchor/activity assumptions also
restrict applicability. Actual MATRIX PNG is1800×7894 with excessive blank
cells. Therefore visual/scientific qualification is blocked; do not initiate
GPU smoke or full inference on this version. No GPU calls were spent. Preserve
three prepared cases and CPU/source-audit evidence. Measurement/anchor/activity
and compact-layout proposals are pending, not adopted. Details and source
positions: docs/issues/RQ3_10_qualification_2026-10-01.md.

## DD-20261005-WWW-SPRINT: Fixed paper decisions and a method-freeze deadline
**Date:** 2026-10-05
**Status:** adopted for workflow; scientific candidate remains provisional

**Context.** The user targets WWW 2027, with the official 2026-10-18 abstract
and 2026-10-25 full-paper deadlines, and requests faster, purpose-driven
progress. Continuing component/layout exploration without a frozen paper
claim would consume the remaining validation and writing time.

**Decision.** Keep the existing scientific objective: evidence-preserving,
selective visual RCA must establish separable ranking value over same-fact
strong text before cost reduction is claimed. RQ3.18 is a component test,
not by itself a paper contribution. Complete its frozen matrix and adoption
decision; end open-ended method search by 2026-10-07 18:00 Toronto, with an
explicit go/no-go on the single method and central claim. Internal abstract
and final-paper targets are October16 and October23. Write while the
registered GPU queue runs; use one primary agent.

**Evidence.** RQ1.1 TPV-T supports selective visual presentation in its own
Qwen family (primary300 MRR .3819 vs .3093). RQ3.14's supported window-summary
gain is textual, not a curve effect. RQ3.16's marginal .5054 vs markless .4963
has not established point contribution; RQ3.17's preselected complete
combination failed its registered adoption rule. RQ3.18 results are still
incomplete and are not used to select a winner. RQ3.7/3.8 report both eval480
and test360 as exposed, with no qualified fresh roster; confirmation claims
need a separate exposure audit. These results have different protocols and
denominators and are not a cross-experiment leaderboard.

**Alternatives rejected.** Another automatic topology/layout grid; treating
the highest historical MRR as a deployable method; renaming existing compiler
engineering as an algorithmic contribution; guaranteeing acceptance or a
target MRR by the submission date; relabelling exposed test as fresh.

**Consequences.** No current experiment/config/source/recipe/threshold change.
The existing RQ3.18 budget2500 and full matrix remain in force. Future calls
require a concrete missing claim, minimal matched controls, source/data
qualification and a registered allocation, not this scheduling document
alone. Core result tables precede long narrative reports, while source,
statistics and explanation validity remain explicit. If no candidate and
technical distinction support a method paper at the decision deadline,
record that outcome and make an explicit paper-scope decision; do not
automatically start another search or silently switch tracks.

Project plan and claim ledger:
`docs/experiment_plans/CanvasRCA_WWW2027_Submission_Sprint_2026-10-05.md`.
Official sources: https://www2027.thewebconf.org/important-dates/ and
https://www2027.thewebconf.org/research-track-papers/ .

## DD-20261005-EMPIRICAL-METHOD: Joint accuracy/cost and an empirical mechanism before another visual method
**Date:** 2026-10-05
**Status:** adopted for research objectives; proposed compiler remains provisional

**Context.** The user requests a strong empirical contribution as the basis of
a substantive new method, with MRR around0.60 and at most5% added actual cost.
This prospectively supersedes the cost-later priority of DD-20261005-WWW-SPRINT,
not its freeze deadline or any registered experiment's adoption rules.

**Decision.** Study when complete encoded observations remain usable for the
fixed RCA model. Propose one bounded candidate: offline measurement of joint
entity/unit/phase/statistic reading errors guides evidence-carrier allocation
under actual processor budgets, with one diagnostic call at deployment.
Compare against equally engineered compact text, fixed hybrid allocation and
single-value-only calibration. Keep method utility distinct from component
attribution; neither requires claiming every engineering part is separately
significant. No new experiment or model call is initiated by this decision.

**Evidence.** The historical report review spans RQ1.1/RQ2.1, search/tournament,
RQ3.1–3.17 and current RQ3.18 status. RQ3.11 already tested numerical-operator
protection and exact patches; generic compression is not new. RQ3.14 supports
window summary text, not its curves. RQ3.16 paired220 MARGINAL_FIVE versus
PAIR_FIVE gives .5053788 versus .4436364, with logical mean total-token ratio
1.0388738; versus BASE_FLEX the ratio is1.1839632 with content/output changes.
This descriptive cost audit does not reverse original nonsignificant mechanism
tests or failed coverage gates. RQ3.17 full combinations failed adoption.
Primary research already covers chart perception, modality preference,
visual-text compression, evidence grouping and adaptive reliable reasoning.

**Alternatives rejected.** Another topology/style search; generic deduplication
as core novelty; renaming RQ3.11; two-call verification by default; a new
training/co-evolution program; treating poor comparator engineering as proof
of vision; calling an empirical paper a guaranteed fallback.

**Consequences.** Preserve RQ3.18 source contract
a71275854a446e551776a8c134080620f69773150e12aaf18065d739ec43a49e,
all in-flight inputs, gates, accounting and original statistics. The proposed
2,880-call successor envelope is not a reset or execution allocation. Before
implementation/launch, specify a concrete capability table and binding-aware
allocation, prove public facts and budgets on CPU, register new contrasts and
audit exposure/compatibility. If perception improvements do not transfer to
RCA, stop this candidate. No independent confirmation claim without eligible
events. Review and project-level objectives are under docs; shared reference
guide and historical reports remain unchanged.

Artifacts: important_docs/CanvasRCA_Empirical_to_Method_2026-10-05.md;
important_docs/CanvasRCA_Empirical_Literature_Review_2026-10-05.md; derived cost audit
and report SHA manifest in the proposal's assets directory.

## DD-20261005-COUNTERINTUITIVE: Prioritize substantial anomalies before another method
**Date:** 2026-10-05
**Status:** adopted (research prioritization; mechanisms remain provisional)

**Context.** The user requests recording QA/RCA dissociation and dashboard
header attention, then narrows scope to substantial findings worth scarce
research time. A long catalogue of small MRR differences would not help.

**Decision.** Retain those two observations with explicit measurement limits,
plus one additional priority: semantic-equivalent scientific notation causes
more first-choice flips than independent repeats. This qualifies the earlier
DD-20261005-EMPIRICAL-METHOD proposal: QA-guided allocation remains a candidate,
not a selected algorithm; establish diagnostic relevance before investing in
its proposed full matrix. No runtime authority changes.

**Evidence.** Historical Qwen semantic-v2 primary293 visual QA/RR rho=.0212,
paired-change rho=.0511 (original 237-test family pH=1); header per-pixel density
lift6.1578/2.0822 at the single registered attention layer; RQ3.7 common84
scientific-notation/repeat flips12/1 for T_MATCH and10/0 for LOCAL_LINK,
original six-test exploratory paired-flip Holm p=.005859/.009766. MRR changes
for those encoding contrasts remain nonsignificant. Independent recomputation
of the six flip tests and Holm adjustment matches source tables. No new effect
size or causal claim is inferred from nonsignificant correlations.

**Alternatives rejected.** Promoting tiny layout/mark-ablation differences to
new research directions; treating QA improvement as RCA improvement; deriving
causal importance from averaged attention; opening broad attention collection.
Complete historical comparisons remain available, including negative results.

**Consequences.** Use existing artifacts first; distinguish reading, measured
attention, semantic stability and diagnostic utility. Keep current RQ3.18
frozen and do not create additional model calls. Findings, source hashes and
limits are in important_docs/CanvasRCA_Counterintuitive_Findings_2026-10-05.md and its
assets directory; project log is devlog/2026-10-05_counterintuitive_findings.md.

**Same-day user-directed extension.** The user asks to add the two substantial
interventions discussed after the initial three-entry record. CF-04 retains
RQ3.8's complete-text-plus-dashboard decline (exposed test342 macro
delta−.0771, case/group pH=.001115/.000679); CF-05 retains RQ3.6-A's text
interface-package gain (common97 pooled delta+.1017, pH=.002771/.004863).
The record now contains five priorities. Preserve their original families,
missing/design-infeasible denominators and package-level interpretation; do not
claim either has CF-03's matched independent-repeat perturbation control.
CF-04 is a diagnostic-interference question, CF-05 an interface control for
fair comparison. This extension changes documentation only, not experiment
authorization or the provisional status of any successor method.

## DD-20261005-ATTENTION: Bounded attention summaries and a sink intervention candidate
**Date:** 2026-10-05
**Status:** provisional (documented direction; not an activated protocol)

**Context.** The user supports two complementary research tracks and requests
a standalone record of low-storage attention and visual attention sink work.
Historical archive receipts total 111,453,790,762 bytes across seven trees.
Header attention density is an observation, not an established harmful sink.

**Decision.** Document online FP32 summaries, bounded detail sampling and
shared-input references, with a calculated 860,880,896-byte peak envelope for
10,000 attempts. Treat selective sink masking/redistribution as a future
controlled candidate, with an original and equal-count random-mask control.

**Evidence.** The old probe already averages bounded answer-token queries;
storage savings also require changing persisted representations. The proposed
capacity is arithmetic, not a measured implementation result. ICLR 2025
VisAttnSink distinguishes activation-based sink identification, diagnostic
masking and VAR redistribution; it does not establish CanvasRCA RCA gains.

**Alternatives rejected.** Promising 100-fold lossless compression, recording
every tensor, declaring a sink from a bright heatmap, deleting highest-weight
tokens without controls, or claiming VAR itself as a new algorithm.

**Consequences.** Future qualification must measure storage, runtime and memory,
respect the hybrid model architecture, and version passive logging separately
from inference interventions. No current code, recipe, run or attention switch
is changed. Details and source hashes are under
important_docs/CanvasRCA_Attention_Storage_and_Sink_2026-10-05.md and its artifact
directory. Existing frozen experiments and historical measurements are preserved.

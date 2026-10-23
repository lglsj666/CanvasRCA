# CanvasRCA project-wide design decisions

## DD-20261019-RQ45-CPU: Complete CPU qualification; preserve explicit comparison scope

**Date:** 2026-10-19
**Status:** adopted for the current RQ4.5 revision

The user authorizes CPU repair until all checks pass and removes strict cross-arm information equality. Methods may select different public evidence with explicit retained/omitted inventories; changed evidence supports whole-method comparisons. Within-arm cross-modal nonduplication, single-call RCA, private-label isolation and the unified renderer remain required. Codex.md is unchanged.

CPU qualification is now passed and frozen. Correct the new marginal geometry, endpoint format, empty-transfer applicability limit, static-rule repetition, CPU source interleaving and passive multi-image header attribution. Preserve all diagnostic records across the instruction repair; actual hybrid requests save 522 tokens each. Generic instruction savings are not a visual-compression contribution, and rewritten instructions may affect diagnosis. Historical baselines stay unchanged and are reused with their comparability limits disclosed.

Reuse unaffected qualification evidence only with the original report/source hashes and unchanged-payload/model-code proof; rerun affected checks. No model calls occurred. GPU smoke/formal remain closed pending separate authorization. [CPU qualification](../docs/experiment_reports/RQ4_5_CPU_Qualification_2026-10-19.md) · [Current state](../RQs/RQ4_5/findings/exp_exclusive_spatial_findings.md).

## DD-20261018-RQ45-SCOPE: Reopen exclusive hybrid research alongside pure visual optimization

**Date:** 2026-10-18
**Status:** adopted for RQ4.5 only

**Context.** The user requests half hybrid and half pure-visual arms after reviewing historical marginal/topology performance and pruning failures.

**Decision.** Implement the approved six-arm RQ4.5 plan. Hybrid moves complete source records and their derived statistics into exactly one modality; necessary identity/unit/phase joins may repeat. Single-call diagnosis and the unified renderer remain mandatory. This is an explicit scoped exception to the older prospective pure-visual-only direction, not a rewrite of Codex.md or historical experiments.

**Evidence.** Historical MARGINAL_FIVE 0.5054 is a hybrid duplicate-evidence result, U 0.3517 is pure visual; these are development references, not current-run efficacy. New inputs, costs and rendering remain empirically unqualified at static delivery. [Plan](../docs/experiment_plans/RQ4_5_Exclusive_Modality_Spatial_Pruning_Plan_2026-10-18.md).

**Alternatives rejected.** Repeating the same full text in images would violate the requested ownership/cost design. New two-stage acquisition remains closed. Bulk historical baseline reruns are unnecessary.

**Consequences.** Stop after static checks. CPU/GPU activation requires a later instruction and source-bound qualification. Keep hybrid and pure-visual claims separate; no performance or cost improvement is inferred from code completion.


## DD-20261006-STAGE-PRIORITIES: Prioritize MRR and cost; retain a smaller mechanism track

**Date:** 2026-10-06
**Status:** adopted for the current stage; revisable, not a permanent project constraint

**Context.** The user prioritizes obtaining a strong single-stage "golden
pipeline" that raises MRR while avoiding cost increases and preferably reducing
cost. Research into counterintuitive observations remains important, but should
not dominate development before that pipeline exists. The user explicitly
requires this allocation to stay outside Codex.md because later stages may need
a different balance.

**Decision.** Allocate approximately 80% of the current stage's experimental
effort to improving MRR and cost, and 20% to investigating counterintuitive
phenomena and their mechanisms. For budgeting, translate this approximate
allocation into planned new model calls, while also reporting actual token and
compute costs; arm counts alone do not measure resource allocation. Register
shared controls once and reuse compatible observations across both tracks.
Do not create unnecessary calls merely to attain an exact percentage.

Retain the approximately 0.50-MRR single-stage method as a performance reference
alongside strong text controls. Evaluate complete-pipeline performance and cost
directly; a full explanation of every component's contribution is not a
prerequisite for method progress. Continue bounded mechanism work in parallel,
preferably with interventions that can inform the main method. Deeper causal
explanation can receive greater emphasis once the pipeline is established.
Input integrity, fair comparisons, qualification and honest reporting remain
necessary in both tracks.

**Evidence.** This is a user-directed resource and priority decision, not a
statistical finding that 80/20 is optimal. The completed exposed-eval RQ3.16
report records MARGINAL_FIVE MRR 0.5054 and its independent repeat 0.5039;
RQ3.17's native marginal control records 0.5048 on 219 known results. Their
original adoption and mechanism limitations remain unchanged. See
[RQ3.16](../docs/experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md) and
[RQ3.17](../docs/experiment_reports/RQ3_17_Qwen_Analysis_2026-10-04.md).

**Alternatives rejected for this stage.** Making comprehensive mechanism
explanation the first priority would delay the user's performance/cost goal.
Abandoning counterintuitive findings entirely would lose potentially useful
method guidance. Encoding 80/20 in Codex.md would turn a temporary allocation
into an unnecessarily durable rule, contrary to the user's explicit instruction.

**Consequences.** Future stage plans should state their method/mechanism budget
and prioritize a stronger, cost-conscious single-call pipeline. Reassess this
allocation at the next stage transition or on user direction, especially after
a golden pipeline is established. This entry supersedes earlier recommendations
that would prioritize a comprehensive explanation before method improvement;
it does not rewrite historical protocols or results, change the single-stage
RCA requirement, allocate an additional call budget, or launch an experiment.
Codex.md is not modified by this decision.

## DD-20261006-SINGLE-STAGE-RCA: Close model-driven multi-stage diagnosis

**Date:** 2026-10-06
**Status:** adopted by explicit user instruction

**Context.** The user recalls that two-stage RCA had already been explored and
abandoned for weak gains, and now explicitly requires single-stage RCA for all
future work. RQ3.20 included three single-call controls (F/ST/SV), but its
preselected V and text-fetch T used a selector call followed by a diagnostic
call. Their repeat and acquisition-intervention arms inherited that structure.

**Decision.** One model call performs each future RCA diagnosis. Do not pursue
another model-driven selection/fetch/composition stage followed by a ranking
call, including a repaired or renamed RQ3.20 successor. CPU evidence preparation
and the unified renderer remain available. Separate QA/attention measurements
do not become stages in an RCA inference chain.

**Evidence.** The completed, exposed-eval RQ3.20 v3 report records V−F paired
MRR −0.069617 on209 cases, case/event-group Holm p .003751/.001732 and paired
dz −0.20147; known paired total-token use declined16.86%. Current contract:
`8650bf95d932d26b352ed6cd390764a9e07309ab4f0405be495398f4e5cc82ce`.
The large selector validity problem limits general mechanism conclusions, but
does not override the user's research-scope decision. This is not a proof that
every conceivable multi-stage RCA method fails.
See [full report](../docs/experiment_reports/RQ3_20_Qwen_Analysis_2026-10-06.md).

**Alternatives rejected.** Repairing selector IDs and automatically rerunning
the two-stage method would continue the direction the user has closed.
Renaming acquisition or hiding its first call in preprocessing would violate
the same single-call requirement.

**Consequences.** Codex.md records the latest authority. Future plans preserve
the joint MRR/cost and mechanism objectives within single-call RCA. Earlier
report suggestions to repair the acquisition workflow are historical and no
longer an execution roadmap. Preserve all completed data and code; no new
experiment, repair qualification, or deletion is authorized by this decision.

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

## DD-20261005-DUAL-TRACK: Visual replacement and new diagnostic QA interventions
**Date:** 2026-10-05
**Status:** provisional method/protocol; user-confirmed parallel research direction

**Context.** The user requests a next-stage plan informed by all historical
reports and explicitly requires accuracy/cost work alongside investigation of
counterintuitive phenomena. The latest correction requires new lightweight
QA experiments, rather than archival analysis alone.

**Decision.** Propose one four-arm method candidate: contemporary full strong
text, lossless compact text, compact text plus a fixed image, and explicit
fact transfer from compact text into that same image. Add 60 paired cases of
reading/binding/comparison QA and correct-readout interventions, sharing the
main RCA controls. Attention qualification is conditional and cannot block
the method and QA work. No QA-based routing is selected before transfer to
diagnostic outcomes is tested.

**Evidence.** Completed RQ3.18 reports paired FP-F +.021991 (216 pairs;
case/group primary Holm not significant), positive AIOPS directions and
Aegis harm, with additive input overhead rather than compression. Historical
QA/RCA correlations near zero do not establish independence. RQ3.6 shows
text-interface sensitivity, RQ3.8 additive-image harm, and RQ3.11 the limits of
operator-preserving quantization. Exact values in DOM metadata are not visible
image evidence. Source hashes and review scope accompany the plan.

**Alternatives rejected.** Another layout/markless/topology grid; calling
generic compact text or source deduplication novel; weakening the text
baseline; equating QA with RCA utility; interpreting high attention as a
causal sink; treating exposed test360 as untouched confirmation.

**Consequences.** The proposed 3,000-attempt ceiling includes a 1,480-call
core, qualification, conditional baselines/validation, and bounded retries.
It is a resource plan, not execution authorization. Whole-method evidence and
mechanism-specific claims have separate decision rules. All existing runs,
code, inputs, answers and findings remain unchanged. New code, CPU/GPU tests,
attention collection and formal calls have not started. Full plan:
[dual-track next stage](../docs/experiment_plans/CanvasRCA_Dual_Track_Next_Stage_2026-10-05.md).


## DD-20261006-METHOD-PRIORITY: Prioritize single-call accuracy and cost, with scoped mechanism work
**Date:** 2026-10-06
**Status:** adopted for the current development phase; revisit with user direction

**Context.** The user prioritizes increasing MRR while keeping actual deployment cost within5% or reducing it. Historical rounds contain useful improvements, but changed inputs and exposed cases prevent treating all cross-round increments as one controlled cumulative result. Two-stage RCA is separately prohibited by the latest Codex authority.

**Decision.** Keep the current approximate80/20 method/mechanism priority in planning records, not Codex.md. Require each new condition to support a deployment decision or a specific mechanism question. Reuse traceable historical anchors when the user chooses cross-round comparison over a contemporary repeat; retain explicit scope and matched new controls. Do not consume an available call budget merely to fill it.

**Evidence.** RQ3.21 static, complete220-case CPU, actual image review and version freeze passed with0 new model calls. Historical anchor220 input/recipe/scorer/commit identities and input-token usage were verified. Compact entity visual input is16.35–17.82% below the historical anchor and13.32–14.32% below RAW_TEXT; this is CPU input evidence, not measured accuracy or total generated-token savings. The detailed qualification report records failures and forward repairs.

**Alternatives rejected.** Recalling an unchanged historical anchor after the user selected reuse; keeping every cell of a factorial design without sufficient decision value; presenting source-text QA as isolated image-reading ability; adding another two-stage selector, topology, layout or attention experiment.

**Consequences.** The approved RQ3.21 pruning keeps six new main arms and the existing480 mechanism positions:1800 new positions,1940 total attempt ceiling, with a73.3% main-matrix share explicitly disclosed. Conditional ablations replace full-factorial mean-effect claims. This round is frozen at CPU qualification; GPU and formal execution require later user instruction. The permanent constraints file was not changed. RQ-specific definitions remain in RQs/RQ3_21/descriptions/ and the [approved plan](../docs/experiment_plans/RQ3_21_Compact_Evidence_Entity_Organization_Plan_2026-10-06.md); results/limits are in the [CPU qualification report](../docs/experiment_reports/RQ3_21_CPU_Qualification_2026-10-06.md).
## DD-20261006-PURE-VISUAL: Pure-visual method development; cancel RQ3.22
**Date:** 2026-10-06
**Status:** adopted input constraint; provisional method direction

**Context.** The user explicitly rejects further hybrid method development,
asks to beat strong text using purely visual diagnostic evidence, and orders
the complete deletion of RQ3.22, including CPU/smoke artifacts. The supplied
`important_docs/conversation_oct_06` proposes provenance-aware visual operators
but still includes an exact-text side channel in its final sketch.

**Decision.** All subsequent research starts under RQ4; the original RQ3 route
is discontinued. Pure visual limits diagnostic evidence, not necessary textual
RCA task, dashboard-reading and output-format instructions. Codex.md now requires
all incident evidence to enter future method
candidates through unified-renderer images. Static task/schema instructions
remain allowed; text systems are evaluation baselines, not method components.
Remove the proposed side channel and full-text fallback. RQ3.22, its plans,
reports, code, tests, preparations, freezes, smoke records and Windows galleries
were deleted under explicit authority; retain only minimal deletion accounting
and the 54 already spent-call count. Preserve RQ3.21 and earlier work.

**Evidence.** RQ1.1 pure vision reduced input tokens but underperformed text;
RQ2.1 resolution gains incurred more input tokens. RQ3.21 compact entity visual
MRR was 0.41795 versus 0.44356 text and 0.50538 historical hybrid anchor, despite
lower token cost. These are historical development results, not confirmation of
the new pure-visual hypothesis. TokenPacker and LLaVA-Mini require learned
modules; SaMer is a close object-aware compression precedent in retrieval.

**Alternatives rejected.** More marginal-card/layout variants as the primary
contribution; simply deleting text from an unchanged two-card dashboard;
calling a prompt screenshot a new visual algorithm; weakening text baselines;
assuming pooled region features can be injected into frozen Qwen unchanged.

**Consequences.** First evaluate the feasibility of preserving entity/signal/
phase structure through visual token compression. RQ4 has a documentation-only namespace; no replacement implementation, training,
GPU qualification or model run is launched. The scoped direction and primary
sources are recorded in [pure-visual direction](../important_docs/CanvasRCA_Pure_Visual_Direction_2026-10-06.md).
Earlier hybrid allowances are superseded prospectively; historical conclusions
keep their original scopes. The current approximate80/20 resource preference
remains a planning choice outside Codex.md.


## DD-20261006-BLIND-PLAN-REVIEW: Fresh independent literature-first plan review
**Date:** 2026-10-06
**Status:** adopted research-planning workflow at the user's explicit request

**Context.** The user asks that future plans center on a defensible core innovation and receive independent criticism informed by real OpenReview reviews and neighboring original papers, before an expensive experiment is launched.

**Decision.** For each substantive plan/revision, initialize a fresh `gpt-6-astra` reviewer with `xhigh` reasoning and no conversation fork. First provide only broad related research areas and ask it to learn from actual public reviews and primary literature; withhold the project, proposal, history, scores and previous critiques. Only after that stage finishes disclose the standalone proposal. Preserve its independent review, answer substantive criticism and revise. Retire the reviewer and use a fresh instance for the next revision. This user authorization is scoped to independent plan review; it does not revive the old multi-agent implementation/experiment team.

**Evidence.** The first application and all favorable/unfavorable reviews are retained under the target RQ's own planning-review artifacts. Agent review scores describe design appraisal, not measured effectiveness, publication acceptance probabilities or runtime qualification. Reviewers report which actual review threads or author-hosted exports they could access and the coverage limitations; author responses are not reviewer opinions.

**Alternatives rejected.** Letting an implementation agent evaluate its own revisions; teaching a reviewer previous favorable scores; changing scientific claims to obtain an endorsement; deleting unfavorable review evidence; treating a high score as permission to run models.

**Consequences.** Keep reviewer identities isolated, record the revision/criticism trail and preserve the actual stopping rationale. The tool API can stop an agent but cannot delete its stored session; do not claim deletion. New instances use no conversation fork and receive no earlier review material. This workflow has planning-agent token cost, separate from the local scientific LLM-call ledger. GPU/formal activation still follows the current user instruction and the qualified experiment protocol.

The same-day user amendment caps the current plan-review iteration at reviewer06; finalize after that review and disclose unresolved findings. This is a stopping instruction for this planning session, not a request for favorable ratings or an automatic limit on every future review.

## DD-RQ41-CENTRAL-SCORER — 2026-10-06

**Authority.** The user requires all new scoring imports to come from
`src/scorer/`, without backward-compatible aliases at old paths. Existing RQ2.1
and historical scoring source stay in place unchanged. External RCA checkouts
are not dependencies for the new execution path. Previously passed CPU checks
remain valid and must not be rerun.

**Decision.** Copy the existing local scorer and matching helpers into the new
package with provenance; change RQ4.1 imports and the configured canonical
matching function to `scorer`. Preserve exact candidate/rank/metric semantics.
The failed transaction check and new import-isolation check form the future
repair queue; retain 41 prior unit passes, 37 renderer passes and completed
source/encoder/selector qualification. No compatibility shims, external-root
fallback, retrospective rescoring or automatic experiment resumption.

**Status.** Implementation and static checks only; runtime checks remain paused.
See `src/scorer/PROVENANCE.json` and RQ4.1 v7 repair records.

## DD-RQ41-ATLAS-COLUMNS — 2026-10-06

**Authority.** The user explicitly requests refactoring CONTRAST_ATLAS to fit
the existing canvas. CPU qualification remains paused for visual inspection.

**Decision.** Replace padded per-entity eight-cell rows with an ordered
eight-column partition. Retain candidate order, original facts, derived values,
font and minimum component dimensions; keep same-entity source/contrast bundles
together. Reuse the unified renderer's existing layout and component library.

**Evidence and limits.** All 220 layouts fit at heights no greater than 5,971 px;
three dataset examples and the largest layout render successfully. The 155 old
atlas evidence packets match exactly. Layout sizing and previews do not certify
full CPU/GPU qualification or performance. No experiments are resumed.

**Record.** See the RQ4.1 atlas layout amendment and
`atlas_layout_repair_v9/layout_capacity.json`; old failures remain preserved.

## DD-20261010-HISTORICAL-CONTROLS: Retain strong text and the high-performing hybrid reference
**Date:** 2026-10-10
**Status:** adopted by explicit user instruction for RQ4.2 and subsequent experiments

**Context.** The user requests that future experiments include both the historical
approximately 0.51 MRR method and strong full text, and that RQ4.2 include both
now by reusing completed answers instead of rerunning them.

**Decision.** Include `RQ3.16/MARGINAL_FIVE` and `RQ4.1/T_FULL` as named historical
reference arms in comparison tables. MARGINAL_FIVE is full diagnostic text plus
native marginal graphics, not a pure-visual method. T_FULL is the full-text
system baseline. Retain the strongest compatible completed pure-visual reference
as well; these references do not consume new optimization-arm calls. Reuse
original answers, scores and measured usage, preserving generation identities.

**Evidence.** The completed source tables yield MRR 0.5053787879 for
MARGINAL_FIVE and 0.4846212121 for T_FULL, each over the same 220 exposed
development identities (60 AIOPS-2022, 60 AIOPS-2025, 100 AegisLab). On
2026-10-10 both full rosters were matched against RQ4.2's frozen RCA queue, with
no missing or duplicate identities. See the [RQ3.16 report](../docs/experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md),
[RQ4.1 report](../docs/experiment_reports/RQ4_1_Qwen_Analysis_2026-10-09.md), and
[RQ4.2 historical-reference supplement](../RQs/RQ4_2/descriptions/RQ4_2_Historical_Controls_2026-10-10.md).
These are historical system results, not new contemporaneous calls or evidence
that pure visual has reached 0.51. No new significance tests were run here.

**Alternatives rejected.** Omitting the strong text reference; rerunning unchanged
historical requests; treating the hybrid anchor as a pure-visual method; comparing
an incomplete current subset against a different historical denominator.

**Consequences.** Report absolute and paired performance and actual deployment
token cost for compatible shared cases, retaining failures and original full
denominators. Historical reuse has zero new inference expenditure but does not
make the baseline's deployment cost zero. Preserve and disclose model, prompt,
evidence, decoding, scorer and backend differences. If a later cohort changes,
report the compatible overlap and coverage; do not assume a historical answer
exists for an unseen case. Any necessary rescoring is offline through `scorer`,
with old scores retained. RQ4.2's added hybrid comparison is an explicitly dated
reporting supplement made during execution, not a retroactive preregistered
primary comparison. Frozen methods, statistical families, gates and execution
queue remain unchanged. This decision adds no model calls and does not change
Codex.md.

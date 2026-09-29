# CanvasRCA Project Rules

## RQ3.1 fast resume — 2026-09-17 latest authority

The user removes RQ3.1's bulk restart verification after it kept the loaded
Qwen server idle for more than two hours. A successfully written
`completed/<call_key>.json` is the atomic per-call commit boundary and a
`phase_complete.<model>.json` marker is the model-phase boundary. Resume must
trust these markers, skip a complete model before starting vLLM, and skip
previously committed units before loading/materializing their contexts. It
must not re-hash, rewrite or reopen the full prompt/render/conversation/
trajectory graph merely because a process restarted. An older run without a
phase marker may rebuild only the small logical-key index from result headers
plus completion-marker presence; this is bookkeeping, not artifact validation.
New calls retain their normal pre-submit identity checks and commit-time
integrity audit. Missing commit markers remain incomplete and are rerun under
the existing call-accounting rules. This operational change does not alter
model inputs, outputs, scoring, existing scientific results or call budgets.

## RQ3.1 call-budget authority — 2026-09-16

The user removes the lower agent-drafted cap. RQ3.1 uses the user's explicit
40,000-call per-major-RQ ceiling, including prior calls, smoke and retries.
Do not attribute the removed restriction to a user decision. Current cumulative
core allocation is 23,752, leaving 16,248 unallocated. This does not increase
the registered experiment matrix, relax the 18-call/600-second logical-smoke
limits, reset spent calls or authorize execution; the static-only pause remains.

## RQ3.1 direct-per-case revision — current stopping boundary

The latest user instruction authorizes experiment-code changes and static
checks only, followed by a pause. Do not run CPU tests, preparation, rendering,
smoke, inference or training in this revision. P0 and SIRCL own their analyzer
branches; X starts independently from per-case public telemetry. The shared
layer may normalize schema/clocks/identities but must not filter through
MET-Z/TRC-L/LOG-R/Denum/topology analyzers. Earlier smoke success applies only
to its earlier code/config; current runtime qualification is pending. Attention
remains disabled. This paragraph supersedes conflicting execution permissions
below without changing historical records, model recipes or data partitions.

## Single-agent execution — 2026-09-16 latest authority

Current stopping boundary: finish code and static source/configuration checks,
then pause. Do not run CPU tests, preparation, rendering, smoke, inference or
training in this work session. Runtime qualification remains pending and must
not be inferred from static-check success.

The user subsequently authorizes the next qualification step and raises the
five-module limit to 7,500 lines. CPU preparation may use at most eight process
workers pinned to distinct physical cores. Dispatch AIOPS cases from distinct
registered source/cloudbed groups first whenever possible; source reuse is
allowed only when the available roster cannot fill the workers otherwise.
After CPU bugs are repaired and all CPU qualification checks pass, run the
registered bounded smokes. This paragraph supersedes only the stopping boundary
above; single-agent execution and all scientific/runtime gates remain active.

The user ended the active multi-agent workflow because its token cost was too
high. From this point, one primary agent owns implementation, CPU review,
qualification, experiment operation, statistics and academic critique. Do not
start or resume A--E subagents unless the user later explicitly reauthorizes a
multi-agent workflow. Preserve their completed source edits and handoffs as
historical implementation evidence; do not repeat completed work merely because
the worker session ended. This changes collaboration only: the registered
RQ3.1 scientific design, data roles, call budget, review standards, local-only
runtime and stage gates remain in force. The primary agent must still perform
the previously assigned statistical and reviewer checks at the corresponding
stage boundaries.

## RQ3.1 autonomous research execution — 2026-09-15 latest authority

The user now authorizes implementing, qualifying and executing the current
RQ3.1 first-paper research plan with a native multi-agent team. This supersedes
earlier planning-only, data-only and stop-after-qualification restrictions for
RQ3.1; historical RQ/tournament/training statuses remain unchanged. The first
paper uses frozen one-call Solvers and no new SFT/RL. Preserve the registered
train300/eval480/test360/unused1403 identities. Use eval for method development;
freeze the recommended method and all test comparisons before new test scores.
Do not repeatedly tune on test until a requested performance threshold passes.

A owns evidence engineering, B representation, C execution/evaluation. D may
start only after a predefined complete experimental batch has durable outputs,
drained writers and no unexplained omissions, confirmed by the leader or C.
E performs read-only academic review at every completed substantive stage;
result-bearing stages require D's finished analysis first. Each assignment has
an explicit deliverable and stopping boundary. No idle D/E warm-up or monitoring.

The leader owns scientific registration, integration and acceptance. The first
stage is executable method/protocol implementation with CPU and visual checks;
its E review precedes model qualification. Later stages are complete eval
development/selection, complete mechanism/robustness evidence, and final locked
test plus synthesis. Stage reviews and dispositions are kept separately under
RQ3.1 results; the project-wide log remains devlog/CONSOLIDATED.md.

The requested completion target is a single preselected deployed method using
the primary Qwen Solver: test360 MRR at least 0.65 and AIOPS-2022/AIOPS-2025
test MRR each at least 0.60, together with completed necessary experiments and
a credible publication evidence chain. Gemma is reported separately as transfer
evidence. These are measured goals, not guarantees or reasons to change scores,
test identities or failure denominators. The current 40,000-call RQ3.1 budget
still applies; all attempts and qualification count.

RQ3.1 may implement its explicitly inherited local renderer snapshot at
RQs/RQ3_1/src/renderer/ under the existing renderer exception. Its remaining
code follows the five-module, 7,500-line rule. Shared recipes, earlier RQs and
the canonical processed corpus remain protected. New qualification uses three
primary-dataset eval cases because validation is retired; test is never smoke.
Existing aggregate smoke limits remain 18 initiated calls and 600 seconds per
registered experiment. Do not start model calls before integrated checks and
the first-stage review are complete.

## First-paper train/eval/test/unused — 2026-09-15 latest amendment

The first paper does not train SFT/RL models. RQ480 is now explicitly the
method-development/selection **eval**, not an untouched confirmation set.
The latest user explicitly supersedes the earlier 480-test target: use **360
test cases, 120 each AIOPS-2022, AIOPS-2025 and AegisLab**. Include all old
validation identities (70 per AIOPS), then add 50 each AIOPS and 120 AegisLab.
Keep historical train 300 and RQ480 identities unchanged; all remaining corpus
cases become unused. There is no active validation partition. Old excluded
non-eval cases also become unused but retain overlap/eligibility annotations;
unused does not mean unseen or safe to train on. All RE2 stay in eval.
Preserve old manifests/results and known validation exposure; the test is not
described as wholly untouched. Use deterministic intact event groups and audit
train/eval/test separation. Methods must be frozen before new test outcomes;
report the former-validation 140 separately from the added 220. Later training may use RQ480 for
checkpoint/model evaluation or selection, never optimizer examples; selection
feedback is validation, not independent test evidence. This role amendment
does not launch experiments, change historical statuses, overwrite historical data manifests,
or authorize new data collection. It authorizes a versioned data splitter and
CPU checks only. See the latest research plan and the consolidated devlog.

## Tournament stopped; analysis delivered — 2026-09-15

The user ended the elimination tournament after 38 committed rounds. This
supersedes the continuation/threshold instructions below: do not start another
round, implement/test the proposed X method, or train without a new request.
Preserve all completed results. The authoritative final coverage and failure
analysis, including AC@1/3/5, is
`docs/Tournament_Analysis_2026-09-15.md`; its derived tables are offline,
label-bearing evaluator artifacts, never model inputs.

## Selection-only tournament successor — 2026-09-14

The latest user narrows future rounds to evidence selection only. Preserve the
round-16 candidate-bound dashboard, pure-visual transport, prompts, candidates,
public projection and model recipes. Change only which existing public facts
are selected, with the same per-case field budgets and membership closure rule.
Use the pending catalogue `RQs/RQ3/configs/selection_only_suite_v1.yaml`; historical
display, transport and modality-dropping configurations are not its queue.
Every actual round still registers and runs ALL unretired cases per model,
sequentially, with no training or attention. A CPU inspection subset is never
an inference cohort. See the selection-only decision in RQ3_experiments.md.
The updated goal allows new selectors and silhouette drawing changes only if
the pending selectors are exhausted before reaching the stopping thresholds;
dashboard layout stays fixed. This does not change any completed-round input.

## Tournament transport allowance — historical; superseded for future selection-only rounds

Each successor method may keep all diagnostic evidence in one dashboard PNG or
move at most one of M/R/L/G into an adjacent text evidence block; the other
three modalities remain in the single PNG. Candidates and static instructions
remain text. This supersedes the older tournament-wide pure-vision sentence,
but does not authorize two or more text evidence modalities, multiple images,
training, attention collection, private-label access, or a changed RCA task
structure. Each method still runs every case unretired for that model.

## Tournament resumed by user — latest 2026-09-13

The user explicitly says to resume. This lifts the round-4 pause below.
Reuse the completed 323-case gallery and registered full remaining cohorts
(265 per model); do not regenerate it or repeat rounds 1–3. Complete the
pending CPU/visual and input-integrity checks, then run Qwen and Gemma
sequentially. Continue full-remaining rounds with 900-second monitoring and
no work during sleeps. No attention or training during the tournament;
per-dataset 80% AC@1 union remains the stopping criterion for both models.

## Tournament user pause after round-4 rendering — latest 2026-09-13

The user requests a pause after the fourth round's gallery finishes to use the
GPU for another task. All 323 unique round-4 PNGs have been generated; no
round-4 inference has started. Do not start GPU services, inference, training
or subsequent rounds until the user resumes. Preserve the complete gallery,
registered Qwen/Gemma cohorts (265 cases each), and all completed round 1–3
results. Round-4 CPU/visual review and inference are pending. This operational
pause supersedes the earlier continuous-monitoring instruction, not the
full-remaining tournament design. See round-4 `PAUSED_20260913.md`.

## Full-remaining tournament reset — latest 2026-09-13 amendment

The tournament itself IS exploration. There is no preliminary model-inference
subset and no score-based decision whether to expand a method. After CPU and
visual correctness checks, each new method must include ALL currently unretired
cases independently for Qwen and Gemma, then finish both models before changing
method. CPU test fixtures and visual spot checks do not authorize smaller
inference cohorts. New registration enforces `all_unretired_v1`.

The user explicitly orders deletion of rounds 2–10 and their derived retirement
state, retaining round 1, canonical data and source code. Restart at round 2
from the preserved first-round outcomes: Qwen 314 and Gemma 345 unresolved.
Deleted results are not reusable or evidence of current coverage. Preserve a
minimal deletion/protection audit, not backups of the deleted responses.
Use `RQs/RQ3/configs/tournament_full_remaining_v3.yaml` and its method successors.
The per-dataset 80% AC@1-only stopping rule remains; no training during the
tournament. This supersedes ALL older small-subset exploration instructions.
See `RQs/RQ3/descriptions/RQ3_full_remaining_reset_20260913.md`.

## Tournament stops at per-dataset AC@1 coverage — latest 2026-09-13 amendment

Each model finishes the tournament once AC@1 union coverage reaches at least
80/100 in AIOPS-2022, AIOPS-2025 and AegisLab, and 72/90 in each RE2 dataset.
**There is no subsequent AC@5 retirement phase.** Both Qwen and Gemma must
meet all five thresholds. Continue recording successful methods at AC@1/3/5,
but AC@3/5 do not determine completion. This supersedes the intermediate
transition amendment immediately below. The successor config is
`RQs/RQ3/configs/tournament_ac1_v2.yaml`; its immutable completion-policy
overlay reuses verified rounds 1–9 without rewriting their contracts or calls.
New method configs inherit this successor. A completed model has an empty
eligible cohort, while its unresolved cases remain explicitly recorded;
do not mislabel those cases as solved. Tournament completion never
automatically launches SFT/RL.

## Tournament threshold amendment — 2026-09-13, per dataset (transition superseded)

The latest user goal replaces the pooled 240/300 primary-case transition.
For **each model independently**, top-1 union coverage must reach at least
80% in **every dataset**: AIOPS-2022 80/100, AIOPS-2025 80/100, AegisLab
80/100, RE2-OB 72/90 and RE2-TT 72/90. Only then does that model switch to
AC@5 retirement. Both models must finish. RE2 now participates in the
transition requirement; neither averaging datasets nor combining models
can satisfy it. This supersedes the threshold statements below.

Preserve original method registrations, responses and AC@1/3/5 success maps.
Adopt a versioned coverage-policy successor without rewriting historical
contracts or making new requests for completed inputs. The in-flight round 9
keeps its frozen evidence, prompt, recipe and records; transition-policy
migration occurs at its verified completion boundary. No training is authorized
by this amendment. Record the migration and per-dataset counts explicitly.

## RQ3 adaptive elimination tournament — 2026-09-12 (current authority)

The user's 2026-09-13 goal amendment temporarily raises the RQ3 functional
source-line limit to **10,000**, superseding the 6,000-line limit for RQ3 only.
Keep the existing module layout and RQ-local renderer exception; this does not
raise another RQ's limit or authorize training during the tournament.

The latest user amendment requires both Qwen3.8-27B and Gemma-4-26B-A4B-it
in the tournament. Run them sequentially for each registered method, with
separate model-specific success/retirement sets and the same public inputs
where their eligible cases overlap. Both must finish before the tournament is
complete; one model's success never retires a case for the other. Existing
model-specific recipes remain distinct. Prioritize evidence-selection methods
from related work, faithfully adapted and audited, in subsequent rounds.

The latest user goal authorizes an adaptive RQ480 discovery tournament,
superseding the train-only/deferred-evaluation boundary below. Start with one
frozen, previously explored method on all 480 cases, then run changed methods
only on cases not yet retired. The final user correction sets the AC@1 union
threshold to **80% of the 300 non-RE2 cases (240 cases)**. Earlier 75% and 70%
interpretations are superseded; neither was used to retire a case. At that
threshold switch to AC@5 retirement. Save all per-case successful method IDs
at AC@1/3/5 and full immutable inputs/outputs; no correctness retries or labels
in model-visible inputs. This is adaptive discovery/union coverage, not the
accuracy of a single deployed method or untouched evaluation.

Updated post-SFT/RL objectives are **AIOPS-2022 MRR >0.65, AIOPS-2025 MRR
>0.65, and 480-case overall MRR >0.75**, with Composer plus Solver token cost
reported. RQ480 and TrainTicket remain excluded from optimizer training;
adaptive exposure must remain explicit in later performance interpretation.
Preserve all old results, processed data, checkpoints and source snapshots.
Use local, unquantized models and exactly one real diagnostic PNG; collect no
new attention. The latest user amendment restores pure-visual diagnostic
evidence, superseding the intervening one-text-modality permission. All selected
M/R/L/G evidence is in that PNG; candidates and global instructions stay in the
prompt. Choose a template structure from the RQ1.1/RQ2.1 visual arms before the
first tournament call, then keep that structure fixed across rounds. Evidence
and public candidate policies may vary, but do not tune the RCA procedure.
Register the successor explicitly; do not rewrite SEARCH22's original prompts.
Stable monitoring
is every 600 seconds, with no work during sleeps. Register each round before
calling models. Tournament completion does not automatically make the old
training lifecycle compatible. Protocol: `RQs/RQ3/descriptions/RQ3_experiments.md#tournament`.

The tournament itself performs no model training. Use the existing `tools`
environment for CPU preparation/rendering/analysis and `infer` for local vLLM;
do not launch SFT/RL or update the 9B/27B checkpoints during this stage. CPU
unit tests that require PyTorch may use the existing `train` environment with
CUDA disabled; these synthetic tests are not model training or qualification.

## RQ3 search resumed; RQ480 evaluation deferred — 2026-09-12

The latest user instruction resumes train-only exploration toward the unchanged
research targets. It supersedes the pause below and defers the intervening
request to evaluate the typed-overview method on RQ480. No RQ480 calls were
started for that request. Continue bounded, versioned training-subset searches
and their full artifact reviews; do not use eval answers for tuning or launch
the old training lifecycle. Preserve all existing results and checkpoints.
The later same-day goal amendment changes stable search monitoring from
1,200 to 600 seconds; do no other work during monitoring sleeps.

## RQ3 search user pause — 2026-09-12

The latest user instruction pauses all exploration and requests a complete
method/result recap. SEARCH37 is complete and preserved. SEARCH38's CPU tests
passed but its preview-only process was stopped before any model call; keep its
partial gallery. No model/training/formal run or automatic continuation is
authorized until the user resumes. This supersedes the search-first execution
continuation below, not its research objective or data-protection rules.
Pause evidence: `RQs/RQ3/results/search_first_v1/PAUSED_20260912.md`.

## RQ3 search-first pipeline successor — 2026-09-12

Latest same-day amendment: new RQ3 exploration and training collect **no
attention**. Preserve old attention artifacts and historical contracts. The
successor main path is strictly visual for diagnostic evidence: diagnostic
facts are painted in the single image. The candidate entity list stays in the
prompt, NOT the image, alongside static task/format/reading instructions.
Candidate-list policies may be explored using public metadata only, never
private roots; record coverage and keep case-local IDs consistent with the image.
First search on small training subsets and validate a shortlist.
Freeze the candidate policy/version before the authorized complete 480-case
pre-training eval. If it meets the target, proceed to small SFT/RL tests, then
freeze the training recipe before full SFT/RL. Evaluation answers never enter
model inputs or training. Preserve failed eval outcomes; do not repeatedly
retune on their case-level answers or call an already exposed set untouched.

The latest user goal supersedes the stop-after-BASE/SFT boundary below. First
develop and test evidence selection, visual encoding, continuous composition
and Solver-prompt/configuration combinations on small isolated development
subsets; then perform Composer SFT and actual RCA-utility RL. Do not restart
the old full lifecycle automatically. RQ3-local successor source, renderer,
prompts and inference-profile changes are authorized, but must be versioned
and qualified; do not change earlier RQs or the shared default Solver recipe.
Preserve the completed SFT checkpoint, old results, processed corpus, RQ480,
TrainTicket training holdout and connected event/window isolation.

The unchanged scorer and private-label boundary remain mandatory. The user
explicitly removed the RQ3-wide 40,000-call cap on 2026-09-12. Preserve consumed
call records; use bounded small representative search batches, with durable
method/input/output/cost/failure records for every attempt. Do not interpret
the uncapped total as a reason for full-dataset grid searches. Final targets after
SFT+RL are AIOPS-2022 MRR >0.54, AIOPS-2025 MRR >0.54 and overall MRR >0.65;
they are measured objectives, not guaranteed outcomes. Freeze the selected
pipeline before using the 480 eval cases. Stable running experiments are
checked every 600 seconds, with no other work during monitoring sleeps.
Current design and execution authority:
`RQs/RQ3/descriptions/RQ3_experiments.md#search-first`.

The same-day user refinement defines four card/silhouette families: one
modality, one chronological interval/snapshot (with a large order index), one
case's selected abnormal evidence, or an explicit evidence combination. Each
card corresponds to exactly one silhouette and vice versa; mixed-modality
content is permitted inside a single card. Old per-modality-only card typing
does not constrain the RQ3 successor. Preserve fact binding and source-time
semantics; do not assign untimed case-wide statistics to a fabricated instant.

## RQ3 paired BASE/SFT comparison first — 2026-09-11

Completion: all 140 BASE calls and 280 paired CPU program checks completed.
Using the same current renderer, BASE constructed 71/140 dashboards and SFT
135/140; this is tool/render validity, not RCA performance. Original SFT
responses were reused unchanged. Owned services stopped normally. See
`RQs/RQ3/results/base_sft_comparison_v1/report.md`. No follow-on is running.

Latest user override: STOP after this comparison and its report. Do not resume
failure diagnosis, renderer repair, training, RL or full evaluation until the
user gives a new instruction. This supersedes the continuation sentence below
and the older full-RQ3 goal for the current execution boundary.

The user prioritizes a matched training-effect comparison before further SFT
failure diagnosis or layout repair. Freeze the current renderer and preserve
all old artifacts. Reuse the 140 completed SFT responses; run BASE on their
exact original system/user messages, per-case seeds and decoding recipe, then
score both with the same current renderer. This is a Composer-only diagnostic,
not Solver/RL/eval execution or qualification of the new capacity-aware input.
Use a separately scoped script/manifest and resumable call accounting; never
replace old records with replay results. After the comparison, report the
paired results and then return to the requested failure/renderer work.
Protocol: `RQs/RQ3/descriptions/RQ3_BASE_SFT_comparison_20260911.md`.

## RQ3 SFT-failure diagnostic successor — 2026-09-11

The latest user goal requests investigating SFT failures and making dashboard
generation reliable and non-overlapping, then finishing RQ3 after checks pass.
Preserve the completed step-320 SFT and original 140-case validation. Those
results are not overwritten by CPU re-execution under a corrected renderer.
The forward metric-label height fix changes no Composer input or model recipe;
its exact compatibility proof preserves preparation, not Solver qualification.
Log-card capacity/constraint visibility remain unresolved. Do not launch the
old activation into RL or evaluation while these repairs are unqualified.
Future stable formal monitoring is every 1,200 seconds with an hourly new-case
audit and no work during sleeps. See the current RQ3 experiment contract and
`RQs/RQ3/results/readable_layout_repair_v1/` for evidence and remaining work.

## RQ3 SFT-format validation only — 2026-09-11

Completion update: all 140 Composer validation cases finished at 20:11:50 UTC.
Complete artifact audit passed; 140/140 JSON syntax, 136/140 schema/binding,
110/140 actual rendering success. Owned GPU services stopped automatically.
This phase is complete; await user authorization for any subsequent phase.
Evidence: `RQs/RQ3/results/formal_balanced_v1/logs/sft_validation_20260911.md`.

The user now authorizes the existing 140-case SFT Composer validation phase:
AIOPS-2022 and AIOPS-2025, 70 validation cases each, final SFT checkpoint 320.
Run `RQs/RQ3/scripts/validate_sft_local.py` locally, retaining registered call
keys, prompts, sampling, adapter hashes and resumable records. This phase uses
the previously qualified 9B LoRA-serving route and CPU rendering checks only.
It does not authorize Solver calls, the pending renderer-only Solver follow-up,
RL, imitation, another SFT run or 480-case evaluation. Do not launch the full
lifecycle supervisor. On interruption, preserve completed responses and only
finish missing work; on completion, stop the owned server and await the user.
See `RQs/RQ3/descriptions/RQ3_SFT_validation_20260911.md`.

## RQ3 stop after current SFT — 2026-09-11 16:19 UTC

Completion update: SFT exited normally at 2026-09-11 17:50:59 UTC after update
320/320 (9,600/9,600 scheduled examples). Final checkpoint hashes, CPU-loaded
optimizer/RNG state and native completed-resume detection passed. No downstream
phase is running. Work is now paused as requested; do not restart qualification,
validation, RL or eval without new user authorization. Evidence:
`RQs/RQ3/results/formal_balanced_v1/SFT_COMPLETION_REVIEW.md`.

The user's latest instruction supersedes the full-lifecycle continuation below:
allow the current format SFT to finish, verify its durable final checkpoint and
process exit, then stop and wait for further instructions. Do not launch the
pending renderer qualification, validation, RL, imitation or final evaluation.
The active wrapper runs only SFT and has no automatic next-stage command.
Preserve all checkpoints under the rolling retention rule and all preparations.
This is a post-SFT pause, not an instruction to interrupt the current update.

## RQ3 resumed authorization — 2026-09-11

The user explicitly authorizes resuming the complete registered RQ3 lifecycle.
This supersedes the user-pause instructions below. Restore the newest verified
full checkpoint, never a hardcoded historical step; the observed restart point
was SFT update 78. Preserve latest-plus-every-20 retention and all preparations.
The already-qualified, unchanged SFT path may resume now. Complete the pending
bounded renderer-only Solver follow-ups before refreshing forward activation
and advancing to validation/RL/eval. Do not bypass that scientific boundary.
Monitor stable formal work every 1,200 seconds and inspect one newly completed
case each 3,600 seconds, with no other work during sleeps. Continue until all
registered RQ3 work and final artifact/analysis checks are complete.

## RQ3 user pause — 2026-09-10 16:00 UTC

The user explicitly paused current execution. RQ3 SFT and its supervisor have
stopped safely at the verified step-78 checkpoint (2,340/9,600 examples).
Do not restart training, qualification, formal inference or automatic monitoring
until the user authorizes resumption. Preserve preparations and the retained
checkpoints under the rolling policy below.
The full goal is unfinished. Resume context and the outstanding forward-renderer
qualification are recorded in
`RQs/RQ3/results/formal_balanced_v1/PAUSED_BY_USER.md`.

## RQ3 rolling checkpoint retention — 2026-09-10 (DD-151)

At every completed optimizer update, durably save the complete latest adapter,
optimizer and RNG state before removing its non-periodic predecessor. Keep
every positive multiple of 20 updates plus the latest complete checkpoint, for
SFT, imitation and each RL branch independently. Do not overwrite the sole
latest checkpoint in place. RL pruning follows durable phase commit; preserve
small phase-referenced markers and one validation-best inference-only adapter,
not its historical optimizer state. Validation schedule and model selection
are unchanged. This storage change does not authorize resuming execution.

## RQ3 execution authorization — 2026-09-10

The active user goal now authorizes completing the balanced 150/70 data
extension, CPU repairs/rechecks, bounded repair qualification, then full RQ3
SFT/RL/evaluation only after all prerequisites pass. This supersedes the earlier
post-smoke stopping boundary, not data isolation, model recipes or the 40,000
call cap. Preserve original failed smoke artifacts and consumed calls. Repair
qualification gets a newly recorded bounded window, never a reset of historical
results. Each experiment's cumulative smoke calls remain within 18.
Monitor smoke every 600 seconds; stable formal work every 1,200 seconds and
audit one newly completed case every 3,600 seconds. Do no other work during
monitoring sleeps. All registered RQ3 experiments must finish before completion
is claimed. Keep execution disabled until actual prerequisites are established.

## RQ3 balanced-data and budget override — 2026-09-10 (DD-150)

The user now adopts **150 train and 70 validation per AIOPS dataset**:
300 train / 140 validation total. This supersedes earlier future split targets,
including the interrupted 210/70 amendment; historical manifests keep their
actual counts. Preserve all 480 eval identities, TrainTicket training holdout,
and connected event/window isolation. Never silently reduce just one dataset
or split an overlap group to fill quotas. The enlarged AIOPS-2022 split is now
materialized after all 241 May events passed canonical V3 processing and source
verification. The 300-train/140-validation registration lives under
`RQs/RQ3/results/registration_balanced_v3/`; old manifests remain historical.

Keep three RL traversals, all three branches and four validation checkpoints,
the complete eval/attribution design, and all model settings unchanged. Planned
generation is **38,000**; **2,000** are reserved for all past/future smoke,
retries and necessary repair within the unchanged **40,000** hard cap.
Budget readiness is not experiment readiness. Execution remains disabled;
this amendment launches no preparation, smoke, SFT, RL or formal evaluation.
Details: `RQs/RQ3/descriptions/RQ3_experiments.md`.

## RQ3 qualification-only update — 2026-09-09

RQ2.1 fixed-anchor inference and final analysis are complete. Preserve outputs.
For RQ3, form full connected event/window groups before excluding groups that
contain eval. Actual isolated counts are 251 train (21 AIOPS-2022, 230 AIOPS-2025)
and 90 validation (20/70), with all 480 eval and all TrainTicket/RE2 excluded
from training/smokes. Earlier RQ3 direct-overlap CPU splits/previews are obsolete;
no model was trained on them. Planned calls shrink to 32,472; hard cap stays
40,000 including local Composer/Solver attempts, not monetary billing.
Complete distinct reviews and bounded inference smokes, then STOP. Training
and formal RQ3 remain disabled. Shared model projections and previous RQs do
not change. Current detailed protocol is the 2026-09-09 refinement in
`RQs/RQ3/descriptions/RQ3_experiments.md`.

## RQ2.1 fixed-anchor override — 2026-09-09

The user replaces sequential champion selection with independent fixed-anchor
studies: selection varies P at S0/D0; silhouette varies S at P0/D0; composition
varies D at P0/S0. No champion or champion cube controls execution. All five
datasets and all 480 cases remain evaluated; earlier selection/report roles
are historical strata, not gates for choosing a new design. This supersedes
the champion and RE2-exclusion instructions below for RQ2.1 only.

Preserve completed evidence-selection results and canonical/parent preparation.
The user authorizes deletion of the P_TRACE_SC formal silhouette output tree,
after recording ownership/counts, and rerunning those targets under P0. Keep
initiated-call accounting, including deleted outputs' calls. New follow-up
results use the `formal_p0_v2` namespaces. The revised planned formal ceiling
is 35,520; the unchanged aggregate ceiling is 39,999 including prior calls.

The user explicitly waives another RQ2.1 smoke for this baseline-only amendment.
Verify unchanged scientific input/compiler/renderer/model/scoring functions and
the fixed-arm dispatch with static/CPU checks; retain original smoke evidence
without claiming new live qualification. Run silhouette Qwen then Gemma,
followed by composition Qwen then Gemma. Direct assistant monitoring is every
900 seconds with one new completed-case audit every 3,600 seconds; do nothing
during monitoring sleeps. Do not launch RQ1.1 reruns or RQ3 training.

After RQ2.1 completes, use its results and RQ1.1 findings to refine RQ3, perform
three distinct logic reviews and three distinct bug/syntax reviews, then its
bounded smokes. Inspect each smoke's full inputs, outputs and conversations.
Stop after RQ3 smoke review; no long SFT, RL or formal RQ3 execution is authorized.

## RQ2.1 override — 2026-09-07

The 2026-09-08 user instruction supersedes the earlier pre-smoke review hold:
run all three bounded smokes, inspect their complete artifacts, repair demonstrated
issues, then enable formal execution only after every qualification passes.
Continue the RQ2.1 formal suite and direct assistant monitoring until completion.
This authorizes neither the abandoned RQ2 nor RQ3 training.

The user-approved contract in `RQs/RQ2_1/descriptions/` supersedes all earlier
RQ2 execution and preservation instructions. RQ2 is abandoned in its entirety;
retain its source, findings and report dependencies but remove its owned
generated results/preparation after the retirement audit and scoped inventory.
Preserve all RQ1.1, the canonical V3 corpus, RQ480, models, unified inference
recipes and RQ3 source. RQ3 remains separately disabled.

RQ2.1 reuses the 480 RQ1.1 cases and the original direct-RCA T/V records as
read-only bridge references. It runs selection, silhouette and composition
experiments, no QA, training or multi-stage RCA. Grouped 30-per-primary-dataset
selection cases choose shared champions; other outcomes remain sealed until
selection is over. This is repeated-exposed evaluation, not fresh confirmation.
Use the same public analysis window, numeric anonymity, source precision,
granularity-aware scoring and `context_safe_output_v1` 8,192 output-token
request adapter. Never replace this with the global 16,384 ceiling.

The five RQ2.1 modules plus `__init__.py` obey the 6,000-source-line rule.
`RQs/RQ2_1/src/renderer/` is an explicit RQ-local inherited-renderer exception;
vendored native algorithms live under `packages/` with license and provenance.
No external SIRCL runtime dependency, global renderer or dormant old dispatcher
is allowed. Copy provenance precedes modifications.

Three experiment smokes each share at most 18 calls and 600 seconds across
sequential Qwen/Gemma phases, including startup/switching/persistence. Their
cases are one from each primary dataset's selection set, explicitly replacing
the older RE2 smoke requirement. The RQ2.1-wide hard cap is 39,999 initiated
calls including smoke and retries; formal planned maximum is 39,360. The
2026-09-08 density amendment adds only `S_DENSITY_COMPACT` versus the reusable
S0 baseline inside the existing silhouette experiment: 960 additional calls,
at most 54 smoke calls overall, and 585 calls reserved for retries/repair.
Evidence, encoding, card footprints, prompt and model recipes stay fixed;
only safe internal whitespace is compacted. No fourth smoke is registered.
All three
smokes and reviews must pass before formal execution. Timeout-only passage
must report actual live coverage, not claim unexecuted paths passed.

The user subsequently authorized a one-time repaired-overlay supplement:
at most two additional silhouette calls (one per model), together within
600 seconds. Preserve the original smoke and its failed visual review.
The three initial smokes initiated 52 calls, so this supplement can bring
their actual total to 54 without changing the RQ-wide 39,999-call cap.
This is not a general exemption from the per-experiment 18-call smoke rule.

Run locally, sequential models, up to eight core-pinned CPU workers, 36
concurrent requests and unchanged 256 scheduler capacity. Preserve image/text
attention from the same call. Monitor smoke every 600 seconds; stable formal
every 900 seconds, with one new case audit per hour. No other work during
monitoring sleep. Formal execution follows qualification under the resumed
authorization above. It never authorizes automatic RQ3 training.

RQ2.1 uses locally deployed open-weight models only: no Nibi jobs and no paid
remote inference service. Its SQLite call register tracks completed requests,
recovery, deduplication and the user-set call-count limit; it is not billing.

Keep Solver-facing dashboards and prompts focused on diagnostic evidence and
necessary reading instructions. Do not automatically expose internal QA/debug
annotations or add explanations of implementation details (such as missing-bin
crosses). Retain source-data and integrity diagnostics offline, without changing
source values or manufacturing observations. Do not add model-facing clutter
merely because an internal check records it.

## RQ3 override — 2026-09-07

The user-approved RQ3 contract in `RQs/RQ3/descriptions/` supersedes the older
future-only Composer/RL roadmap for this RQ. Train only Qwen3.5-9B as a
dashboard Composer; keep Qwen3.8-27B as the frozen one-call Solver. Its
existing unified inference projection and the Gemma recipe must not change.
The new 9B recipe is RQ3-local. Renderer code is an RQ3-local byte-inherited
RQ2 snapshot before explicitly recorded correctness/interface adaptations.

All 480 eval cases and their event/window overlaps are forbidden in SFT,
rollout/reward, validation, checkpoint or hyperparameter selection. Exclude
all AegisLab and RE2-TT from those activities because TrainTicket is held out
from this Composer training. Evaluation still includes both datasets.
Use only isolated AIOPS training/validation cases for RQ3 smokes; this is an
explicit override of the older RE2-inclusive smoke-selection rule.

Each experiment has one logical smoke with at most 18 aggregate 9B+27B calls
and 600 seconds from supervisor start. Monitor live smoke every 600 seconds,
doing no other work while waiting. Count every initiated call, including
retries, against the RQ3-wide 40,000-call hard limit. Never silently truncate
a catalogue, substitute a default dashboard, or relabel a failed preflight
as timeout-only success.

The user subsequently authorized **DD-148's budgeted catalogue**. Keep the
complete eligible evidence pool CPU-side; the model-visible directory is an
explicit, deterministic, label-blind shortlist with recorded omissions and
coverage. It is not a lossless view of every card. Target at most 16,384 whole
Composer-chat input tokens, reserve the unchanged 4,096 output tokens plus
1,024 guard tokens, and enforce the smaller limit if model context is reduced.
The actual tokenizer and chat template must count instructions, JSON schema,
candidates and directory together. Never crop serialized requests, silently
drop evidence from selected cards, or shrink the output budget to make them
fit. All learned policies use this same directory. Only advertised card IDs
are selectable; the renderer retrieves their complete original payloads.
This amendment changes no 27B Solver setting and authorizes no full run.

Current authorization ends after implementation, checks and bounded smokes.
Do not begin long SFT, RL, or formal evaluation automatically. Keep
`RQs/RQ3/configs/rq3.yaml` execution disabled and preserve RQ1.1/RQ2 sources,
reports, processed data and valid results. The five functional RQ3 modules
plus `__init__.py` follow the existing 6,000-line limit; its local inherited
renderer is the explicit directory exception.

CanvasRCA studies whether vision-language models can diagnose microservice
incidents from rendered telemetry dashboards. The dashboard is an experimental
representation, not decoration. Scientific claims must distinguish visual
readability, agent-output influence, and final root-cause ranking.

This file is the single authoritative project-guidance document. `AGENTS.md`
must remain a symbolic link to this file.

## Portable project root

All paths in code, configuration, documentation, contracts, and commands must
be project-relative or supplied through environment variables. Never commit a
user home directory, workstation path, cluster account, or site-specific
absolute path.

The repository root is discovered from the current Git worktree. The standard
environment is loaded with:

```bash
source scripts/env.sh
```

`CANVASRCA_ROOT`, `CANVASRCA_ENV`, `CANVASRCA_PROCESSED_ROOT`,
`CANVASRCA_QWEN_MODEL`, `CANVASRCA_GEMMA_MODEL`, and `RL_SLM_RCA_ROOT` may
override deployment locations. An override is runtime metadata and must be
recorded in a heavy-run contract.

## Canonical layout

```text
configs/                    three scientific contracts plus one local deployment projection
src/unified_scripts/        four reusable global Python implementations
src/vlmrca/                 shared main-pipeline Python package
src/cli/                    shared project-wide Python entry points
scripts/                    shared shell entry points only
RQs/RQx/configs/            RQ-specific configuration only
RQs/RQx/descriptions/       exactly three canonical RQ documents
docs/RQ1_1_RQ2_1_findings/ one consolidated RQ1.1/RQ2.1 findings document and assets
RQs/RQx/scripts/            RQ-specific shell entry points only
RQs/RQx/src/                compact RQ-specific Python package
RQs/RQ1_1/src/renderer/     active provisional renderer inherited from RQ1
RQs/RQx/results/            RQ-specific generated artifacts
requirements/               environment dependency sets
devlog/CONSOLIDATED.md      compact chronological implementation/experiment log
docs/                       project-wide reports and deployment notes
build/                      generated build artifacts only
```

The repository-root `src/` tree contains only Python source files. The
repository-root `scripts/` tree contains only `.sh` files. Python logic must not
be hidden in shell heredocs, and shell launch logic must not be hidden in Python
modules merely to evade this separation.

## Unified global contracts

The repository-root `configs/` directory contains exactly three portable
scientific contract files:

1. `configs/vllm_inference.yaml`
2. `configs/dataset_segmentation.yaml`
3. `configs/rca_scorer.yaml`

It additionally contains `configs/vllm_inference_local.yaml`, an explicitly
authorized local deployment projection of `vllm_inference.yaml`. It is not a
fourth scientific contract and may differ only in deployment paths and the
registered local VRAM fraction. No other root YAML is allowed.

Their only global Python authorities are:

1. `src/unified_scripts/raw_data_processor.py`
2. `src/unified_scripts/vllm_inference.py`
3. `src/unified_scripts/dataset_segmentation.py`
4. `src/unified_scripts/rca_scorer.py`

The raw-data processor has no dataset-specific root YAML. It converts the
complete raw loader index into the one V3 per-case corpus before any RQ roster
is applied. Roster materialization then selects frozen IDs from that complete
corpus under `configs/dataset_segmentation.yaml`. Its vendored
SIRCL loader implementation lives only in
`src/unified_scripts/sircl_data/`; formal processing must not import a sibling
repository or select an alternate loader/fallback at runtime.

The main pipeline and every RQ must use these contracts. An RQ config may
reference them and may contain RQ-specific settings, but it must not copy their
fields into a second nominally unified config.

The global classes are frozen bases, not rigid dead ends. An experiment may
subclass a public class or supply an explicit adapter mapping. Every adapter
must be named, versioned, hash-recorded, limited to the registered experiment,
and included in the effective run contract. A fairness-sensitive override
creates a new protocol; it must never be applied silently.

Generated locks, attestations, split manifests, and migration records are
artifacts rather than configs. Store them under `artifacts/` or the applicable
RQ result root, never as a fourth file in `configs/`.

## Required RQ structure

Every active `RQs/RQx/` directory has `configs/`, `descriptions/`, `scripts/`,
`src/`, and `results/`. Completed RQ1.1/RQ2.1 conclusions are the explicit
exception: they share the single consolidated findings folder under `docs/`.

### Descriptions

`RQs/RQx/descriptions/` contains exactly:

- `RQx_statement.md`: the question and its interpretation;
- `RQx_experiments.md`: experiments, purposes, arms, and expected evidentiary
  scope;
- `RQx_roadMap.md`: a qualitative high-level design and decision map.

The road map must remain qualitative. Do not pretend to know every outcome
before experimentation or hard-code an unnecessary numerical branch tree.
Registered numerical thresholds belong in the experiment config or protocol
section of `RQx_experiments.md`.

### Findings

Each registered experiment has exactly one finding file named
`exp_<experiment>_findings.md`. Every experiment must have a finding file,
including a static-only, blocked, failed, incomplete, or not-yet-run
experiment; the file must state that status without inventing a result. Do not
split one experiment's conclusion across multiple finding documents.

### Shell scripts

`RQs/RQx/scripts/` contains only `.sh` files that trigger runs, tests, smokes,
or gates. It may contain at most ten files and at most 800 total lines. Shared
shell behavior belongs in repository-root `scripts/`.

### Python source

`RQs/RQx/src/` normally contains exactly five functional modules plus the package marker:

```text
main.py       experiment flow and CLI
utils.py      RQ-specific utility functions
exps.py       arms, representations, schemas, and experiment logic
tests.py      smoke and other test definitions
gates.py      gate definitions, verification, and decision metrics
__init__.py   package marker with version information in comments
```

The five functional modules together may not exceed 7,500 nonblank,
non-comment source lines (docstrings count as source). Do not evade
the limit with generated source, embedded code strings, hidden RQ packages, or
copies under `src/vlmrca/`. Move genuinely global, reusable behavior into the
three unified scripts or the shared main pipeline; delete obsolete duplicated
RQ versions once their successor preserves the required behavior.

The only current exception is `RQs/RQ1_1/src/renderer/`. It contains the
versioned, provisional dashboard implementation being evaluated by RQ1.1 and is
counted separately from the five-module 7,500-line limit. This exception must
not be used for unrelated experiment code or as a line-limit escape hatch.

`RQs/RQx/configs/` contains only RQ-specific configuration. It references the
three root unified configs by relative path.

## Shared main pipeline

Reusable model-client, evaluation, training, caching, and trajectory logic
belongs in `src/vlmrca/`. Shared Python command-line utilities belong in
`src/cli/`; shared shell wrappers belong in `scripts/`. RQ-specific mutable
logic belongs only in that RQ's five functional modules.

There is no project-global renderer and no global renderer configuration while
dashboard design remains an open research variable. The authoritative parent
baseline is `RQs/RQ1_1/src/renderer/`; it was initially
copied byte-for-byte from the latest RQ1 renderer before RQ1.1 changes began.
The registered renderer-v14 includes the user-authorized, RQ1.1-local
finite-trace-time, topology-context, negative-zero, and SIRCL* analyzer display fixes documented
in `RQs/RQ1_1/descriptions/RQ1_1_experiments.md`. The initial-copy hashes remain
provenance evidence, not an assertion that the current tree is unchanged. Code
that needs the current dashboard must import that package explicitly.
`src/vlmrca/render/`, a
symlink or wrapper under that path, and any other global renderer authority are
forbidden. RQ2 and later RQs must copy or explicitly inherit the exact frozen
RQ1.1 renderer snapshot. RQ2 records that byte-identical parent provenance and
implements its authorized design interventions only under
`RQs/RQ2/src/renderer/`. The previous RQ2 tree, rosters, contracts, hashes, and
results are fully superseded and are not authorities for the clean RQ2 lineage.
RQ2 may reuse RQ1.1's local vLLM runtime, request adapter, unified client/scorer
and frozen model checkpoints. Its common RCA prompt must be an explicit,
RQ2-local, versioned and hash-recorded minimal adaptation of the selected
SIRCL* scientific prompt used by RQ1.1; it must not import the RQ1.1 prompt at
runtime or silently drift to a different diagnostic method. Only wording that
is required by RQ2's variable metric-card count and registered content/design
controls may differ. The M/R/L/G analyzer order, MET-Z/TRC-L/LOG-R semantics,
verify-and-revise procedure, candidate contract and JSON output contract remain
aligned with the SIRCL* parent. RQ2 owns its separate dashboard grammar because
it studies different encodings, arrangements and scale controls. The common
scientific task text is fixed across all RQ2 cells; visual arms receive the
RQ2-local decoding addendum, while text twins receive no dashboard-only
grammar.
RQ2 must not retain copied RQ1.1 experiment registries, arm dispatchers,
multi-stage planners/tools, or RQ1.1 task prompts as dormant fallbacks. Delete
such code from RQ2 once the RQ2-local replacement exists;
`RQs/RQ1_1/` is the immutable backup and audit authority. Intentional
inheritance is limited to the recorded parent-renderer/evidence primitives,
the unified runtime, request adapter, client, scorer, roster cases, frozen
model checkpoints, and the registered SIRCL* scientific wording through the
explicit RQ2-local adaptation above.

RQ2 is RCA-only. Its RQ2-local packed-QA/perception implementation is retained
solely as explicitly abandoned audit code at the user's request. It must not be
scheduled by an active config, smoke or formal queue; select D* or C*; enter an
active verifier denominator or analysis; or support an RQ2 claim. Existing QA
artifacts remain archived. This exception preserves code but does not create a
fallback or authorize reactivation. RQ2 one-stage RCA continues to record image
and text attention in the original model call.

RQ2 may run registered deterministic evidence-selection tools before the one
Solver call. These tools operate only on the canonical public packet, make no
model call, use no labels, share a fixed selection budget, and must emit an
auditable selected-fact inventory. Every tool output is compared through an
exact-fact natural-language TextTwin and CanvasTwin. Within-tool Canvas−Text
isolates representation; between-tool comparisons intentionally change
evidence selection. This exception does not authorize an interactive tool
agent, multiple Solver stages, or import-time dependence on an external RCA
repository.

RQ2's active dashboard-design language is the evidence-card/silhouette grid
contract. Public M/R/L/G facts are partitioned exactly once into selectable
`EvidenceCardV1` objects. Every selected evidence card must convert to exactly
one `SilhouetteV1`, and the two objects must carry the same fact-inventory hash.
A silhouette may be a plot, heatmap, matrix, graph, timeline, or another
registered visual encoding, but it must not merge cards, split one card across
several silhouettes, duplicate evidence, or allow content to leave its integer
grid footprint. The dashboard compositor places whole silhouettes on a finite
`m×n` square grid with hard bounds and non-overlap checks. Evidence selection
precedes silhouette selection and placement. Packing occupancy is optimized
only after the evidence set is fixed; empty-space penalties must never reward
adding diagnostically irrelevant cards. RQ2 manifests retain the complete
`fact_id → evidence card → silhouette → pixel bbox` mapping and exact action
history so later SFT, RL, and contribution analysis can distinguish information
selection from visual composition.
`RQs/RQ1/` is historical audit material and is not an
active implementation dependency. A renderer change is allowed only when the user
authorizes an experiment about dashboard design; it then requires an RQ-local
version, a new hash/contract, visual inspection, leakage audit, determinism
check, and cross-arm atomic-fact equality audit. An RQ-local change must never
silently mutate a renderer used by another RQ.

`src/vlmrca/upstream.py` is the only sanctioned import boundary into the
optional RL-SLM-RCA sibling checkout. Never modify that sibling from this
project and never insert its path elsewhere. Deployment paths are supplied by
`RL_SLM_RCA_ROOT`.

## Local-only execution

The `_nibi` worktree name is historical. All new preparation, smoke, formal
inference, analysis and training run directly on local WSL. Do not submit Slurm
jobs or select a cluster inference profile. Historical cluster scripts may
remain as source provenance, but they are not current execution instructions.

## Unified vLLM inference policy

All new project-owned inference uses `src/vlmrca/vlm/client.py` and the local
deployment projection of the unified RQ1.1 recipe:

- Local WSL: `configs/vllm_inference_local.yaml` with
  `scripts/vllm_vlm/serve_canvasrca_local.sh` after sourcing
  `scripts/env_local.sh`.

`configs/vllm_inference.yaml` and any historical cluster launcher are retained
only to interpret historical artifacts. They must not be selected for a new
run under the local-only policy.

`CANVASRCA_VLLM_CONFIG` is the only authorized profile selector. Never infer a
profile from a hostname and never copy model-specific sampling or processor
settings into an experiment script. Every runner, client, server attestation,
and run contract must resolve and hash the same selected profile.

The registered open-weight models are Qwen3.8-27B and
Gemma-4-26B-A4B-it. Both use unquantized BF16, seed 42, temperature 1.0, top-p
0.95, a 40,960-token context, a 16,384-token output ceiling, thinking disabled,
prefix caching disabled, and a maximum scheduler capacity of 256 sequences.
Sampling means exact byte repetition is not a validity gate.

These two 27B models are the frozen RCA actors and use the checkpoints under
`/home/lglsj/CanvasRCA/models/`. RQ2 also registers a distinct future Dashboard
Composer: Qwen3.5-9B at
`/home/lglsj/Downloads/self-evolving-RCA-updated/models/Qwen3.5-9B/`, with
`CANVASRCA_COMPOSER_MODEL` as its deployment override. RQ2 may export typed SFT
traces for this Composer but must not train or run it. Later Composer SFT/RL
must not alter the frozen RCA actors or their RQ1.1 inference configuration.

RQ1.1 retains the uniform `context_safe_output_v1` request adapter: every RQ1.1
model, experiment, arm, case, and stage requests at most 8,192 output tokens,
leaving up to 32,768 tokens for model-visible input. The
`max_num_seqs=256` field changes server scheduling capacity only; it does not
change prompts, evidence, output budgets, decoding, or scoring. Its effective
value must still be hash-recorded. Output truncation and parse failure are
model outcomes and must be recorded rather than repaired with a case-specific
budget.

The 2026-08-15 capacity successor increased only `max_model_len` from 32,768
to 40,960. The user explicitly retained every hash-valid completed predecessor
result and waived a replacement smoke: prompts, evidence, output ceilings,
sampling, schemas, and scoring did not change, and each retained request had
already fit and terminated under the smaller context. Runtime-freeze hashes
remain truthful audit metadata but are not validity, comparability, or resume
gates. A runner skips an earlier target after validating its record hash,
self-consistent call key, model/experiment identity, and completed terminal
status; it does not require a matching freeze or compatibility manifest.
Infrastructure errors are not completed outcomes and must be rerun from the
beginning. Removing this gate is status-preserving: every historical record
already accepted as completed remains valid.

Qwen uses the official `Qwen/Qwen3.8-27B` checkpoint at revision
`1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`, stored by default at
`models/Qwen3.8-27B`. Qwen uses its native image-processor policy and receives no project-level
`min_pixels`, `max_pixels`, or other image pixel-budget override. Qwen keeps
chunked prefill disabled unless a new versioned decision changes it. Because
Qwen3.8 enables thinking and preservation of prior thinking by default, both
`enable_thinking=false` and `preserve_thinking=false` must be explicit in the
server and request chat-template kwargs. Qwen3.6 is not an active model,
checkpoint, launcher target, cache target, or queue target. Historical Qwen3.6
records that are inside the explicitly protected RQ1 audit set retain their
original model label and bytes; they must never satisfy or be written into an
RQ1.1 Qwen3.8 result target.

Both Qwen and Gemma use xgrammar structured output with arbitrary JSON
whitespace disabled. This prevents an otherwise schema-valid decoder path from
sampling unbounded spaces or newlines between JSON tokens. Gemma additionally
uses `max_soft_tokens=1120` and chunked prefill enabled.

For local WSL, `gpu_memory_utilization` is exactly `0.75`. The local profile
uses `/home/lglsj/CanvasRCA/venvs/infer/` and the Qwen3.8/Gemma checkpoints
under `/home/lglsj/CanvasRCA/models/`. Record the exact local profile,
checkpoint identity/revision, BF16 precision, context/output limits,
temperature, top-p, seed, thinking/template kwargs, xgrammar, image processor,
chunked prefill, prefix caching, scheduler capacity, request timeouts and VRAM
fraction. The VRAM fraction is operational metadata, not a scientific variable.
Local WSL never submits a Slurm job; launch directly with
`scripts/vllm_vlm/serve_canvasrca_local.sh` or
`RQs/RQ1_1/scripts/run_local.sh`, using `nohup`/ordinary shell backgrounding
only when persistence is needed.
Local canonical V3 preparation runs directly through
`RQs/RQ1_1/scripts/prepare_local.sh` and writes under
`build/local_processed_v3/`; it must not read a retired V2 or single-layer
processed corpus as an experimental fallback.

Every run records the effective global config hash, adapter hash if any, actual
text/image/input/output tokens, wall time, GPU-active time when available, peak
memory, finish reason, parse status, and infrastructure status.

RQ1.1 and RQ2 record image and text attention in the original model call. The
registered first full-attention layer supplies (a) the final prompt query and
(b) generated tokens inside the registered answer arrays. These are
`services` and `values` for the shared RCA/generic schemas. The retained,
abandoned RQ2 packed-QA code also knows the historical fields
`metric_read`, `trace_read`, `log_read`, `temporal_onset`, `directed_path`,
`cross_source_alignment`, and `missingness`, but no active RQ2 call uses them.
Each experiment must enumerate all answer-bearing schema fields explicitly; a
generic field name must not silently omit experiment-specific answer tokens.

Both query types are measured against prior prompt keys. The hook observes but never
changes Q/K/V tensors, logits, sampling, prompts, or model-call count. Persist
the prefill vector and the mean registered-answer-token vector separately.
For visual requests also persist image-token weights, value norms,
prefill-only pre-output-projection attention-weighted value norms, 16x16 grids,
hash-matched overlays, and M/R/L/G region diagnostics. Record first-patch rank
and peak-to-median ratios.

Visual attention geometry must come from the effective processor, never from a
guessed token grid: use Qwen's actual `image_grid_thw`-equivalent post-merge
grid and Gemma's actual image-position/post-pooling grid. Integrate source-token
mass into semantic regions and mesh cells by exact pixel overlap. Because
M/R/L/G occupy unequal areas, raw accumulated mass is not the primary regional
comparison. Report `region_attention_per_pixel = region_mass / region_pixels`
and normalize it by the mean attention per pixel across the actual visual
evidence regions in that image. Header, blank and unassigned areas are reported
separately and excluded from this evidence-density reference. Retain raw mass
only for conservation and total-allocation reporting.
Map text tokens to the system/task shell, candidates/common text, M/R/L/G
evidence, tool history, and unassigned control tokens. Report both raw mass and
token-count-normalized focus because a longer span otherwise receives more
mass by construction. Missing required attention is an artifact-integrity
error for the new attention-enabled protocol. If the model emits no
alphanumeric value token in any registered answer array, generation-time
answer-token attention is structurally not applicable rather than missing:
retain the empty model output and prompt-query attention, and report that
diagnostic absence instead of retrying it as infrastructure. Attention remains correlational:
it may describe where the model looked, but it cannot by itself establish
causal use, correctness, representation benefit, or an attention sink. A sink
claim requires registered content- and position-intervention evidence.

RQ1.1 is not an attempt to prove that images improve RCA. Its purpose is to
measure how representations affect one-stage RCA, cross-region perception,
visible evidence use, attention allocation, and token cost, and how perception
changes relate to RCA outcomes. Positive,
negative, null, mixed, and architecture-specific effects are all valid results.

## Dataset segmentation and privacy

Experiments read only processed per-case data under `dataset/processed/` or the
path supplied by `CANVASRCA_PROCESSED_ROOT`. The complete `dataset/` tree is
read-only. Do not modify raw or processed data.

The only authorized loader schema is `CanvasRCAProcessedPublicCaseV3`, with
losslessly retained SIRCL DataCase columns, relative public clocks, and
physically isolated private labels. Its sole producer is
`src/unified_scripts/raw_data_processor.py`; the removed
`src/cli/process_cases.py` path must not be recreated. Legacy processed-root
environment variables, local-preparation adapters, fallbacks, and silent
schema conversion are forbidden. A missing canonical case or manifest fails
closed before any model call.

All splits and rosters originate from
`src/unified_scripts/dataset_segmentation.py` and
`configs/dataset_segmentation.yaml`. Public rosters contain opaque incident
identities. Source case IDs and labels remain in physically separate
evaluator-private artifacts. RQ quotas and label-blind strata are explicit
adapters; an RQ must not resample cases after seeing model results.

After full V3 regeneration, the RQ1.1 successor must reuse all 480 identities
in the long-frozen project evaluation manifest: 100 AegisLab, 100 AIOPS-2022,
100 AIOPS-2025, 90 RE2-OB, and 90 RE2-TT. The earlier 469-case adapter and its
eleven exclusions are historical pre-V3 audit artifacts, not successor
execution authority. The 300 cases from the first three datasets are the only
headline inferential set. RE2-OB is a separately reported saturated-domain reference, and RE2-TT is
the separately reported final OOD slice; neither may be pooled into the
headline result. This registered final-run use does not authorize RE2 cases for
development, prompt selection, renderer selection, or ordinary gates. RE2-TT
remains embargoed until its first complete frozen final-OOD execution.

RQ2 deliberately reuses all 300 RQ1.1 headline cases. They are assigned once,
without consulting labels or model results, to mutually exclusive RQ2 roles:
60 development cases (20 per dataset), 150 independent cases (50 per dataset),
and 90 downstream-lock cases (30 per dataset). Its deterministic-tool ×
representation study additionally uses all 480 RQ1.1 identities while keeping
RE2-OB and RE2-TT in separate reference/OOD strata.
This reuse enables paired empirical comparison with RQ1.1; it must be described
as repeated-exposed design evaluation rather than untouched confirmation.

## RCA scoring

All root-cause results use `src/unified_scripts/rca_scorer.py` and
`configs/rca_scorer.yaml`. The model output is frozen ranked top-five JSON:

```json
{"services":["..."],"reason":"...","confidence":"high|medium|low"}
```

The primary metric is MRR. Record AC@1, AC@3, AC@5, AVG@3, and AVG@5 per case
and in aggregate. Recall@K is recorded only for a separately registered true
multi-root evaluation. Unknown candidate IDs are misses; never guess or repair
them into known services.

Representation comparisons use paired cases, a Pratt-zero Wilcoxon signed-rank
test, and paired Cohen's dz. Report per-dataset and per-fault breakdowns. Do not
report confidence intervals under the current project policy.

## Label leakage and equal information

The renderer receives only `CaseRenderView`; it never receives a root label.
Ground truth and absolute injection time may be read only after every
model-visible evidence artifact has been created, solely for private scoring.

Model-visible images, OCR text, prompts, manifests, metadata, and filenames
must exclude raw case IDs, dataset names, fault types, ground truth, accepted
labels, absolute times, source paths, and label-derived metadata. A registered
relative incident anchor and relative time bins are allowed.

Every compared representation is compiled from one canonical evidence packet.
Candidates, complete metric sequences, missingness, logs, traces, concrete
caller-to-callee edges, units, precision, bins, and legends must have identical
semantic fact inventories across arms. A fact may move between pixels and text
but may not disappear or appear only in one arm.

A real dashboard, a text-on-canvas/pixel-text representation, and pure text are
distinct representations. Never call the text-on-canvas artifact a rendered
telemetry dashboard: the real dashboard must contain the registered plots and
graphical encodings. Any comparison among these representations is permitted
only after their model-visible atomic fact inventories, numeric precision,
bins, missingness, candidates, concrete edges, and legends are proven equal.
For the registered RQ1.1 `S` pixel-text control, render the frozen T-arm
natural-language incident-fact lines themselves, preserving their order and
partitioning them only with region page headings. Under the current RQ1.1
protocol, text-bearing incident evidence is ordered M/metrics, R/traces,
L/logs, then G/topology; the real dashboard keeps its frozen spatial layout.
Do not source that control from JSONL or from a newly written summary. RQ1.1
has no legacy flat-JSONL arm. T remains the sole natural-language serializer.
The separately registered `C` control is a deterministic concise typed-tuple
projection of the same canonical facts, with schema
`[region, field, entity_ids, relative_bins, unit, payload]`; it is not a second
preparation path and must expose no fact IDs or private metadata. Require a
semantic round-trip equality audit. Use C−T to measure nonvisual
structure/compression and V−C to distinguish spatial visual organization from
ordinary prose verbosity.

Every service, pod, and node identity visible to a model or returned by a tool
must be a deterministic case-local numeric ID: three digits for service, four
for node, and five for pod. Each case receives a new one-to-one mapping.
Natural identities remain evaluator-private. Operation, metric, and template
semantics remain diagnostic public fields, but an exact embedded entity name
must be replaced by its numeric ID.

RQ1.1 logs use `DenumReadableLogGraphV1`, which adopts Denum's numeric-token
parsing and repeated-structure separation without binary output. The canonical
graph preserves template text, typed diagnostic numbers, relative bins,
severity, and multiplicity. `DenumLogTextV1`, the renderer log rows, and
`search_logs` must derive from that one graph and pass semantic round-trip and
fact-inventory equality checks.

If image-only evidence is fragment A and text-only evidence is fragment B, the
hybrid prompt is exactly A+B or exactly B+A. Freeze one order. Do not rewrite,
summarize, deduplicate, or add a hybrid-only instruction. Prompt wording,
candidate order, task shell, output schema, retry policy, and inference config
remain identical across compared arms.

RCA prompts must explain the model-visible evidence fields, relative-time and
missingness semantics, caller/callee direction, the RCA objective, and how to
distinguish an originating fault from propagated symptoms. Non-RCA Q&A prompts
explain their M/R/L/G data structures and fields but must not add an RCA guide.
The registered final RCA JSON schema remains frozen.

Representation decoding is separated from the shared scientific task prompt.
The shared RCA/QA field semantics, question, candidate/output contract, and RCA
method where applicable must be representation-neutral. A pure-text arm must
never receive instructions that imply a dashboard, image, pixel, chart, crop,
canvas, color, line, or spatial layout is present. An arm that actually carries
the real RQ-local dashboard receives the registered dashboard-decoding addendum
covering every visible field and graphical convention; a pixel-text screenshot
receives a distinct addendum that explicitly says it is not a telemetry
dashboard. In mixed arms, the addendum must state which M/R/L/G regions are
visual and that neutral image locations are supplied as text rather than
missing. These addenda may explain representation grammar but must not add an
incident-specific fact, label, candidate, edge, value, hint, or RCA strategy.
H remains strict image-first A+B at the incident-fragment layer: the common
visual grammar may precede A, but A and B themselves may not be rewritten,
deduplicated, reordered, or supplemented.

RQ1.1 direct RCA uses the locked SIRCL* design supplied with the project as a
prompt/analyzer reference: MET-Z, TRC-L, LOG-R, evidence order M/R/L/G,
U-BASE, and VERIFY. The selected source files are preserved byte-for-byte under
`packages/SIRCL_selected_reference/` and must never be imported as a hidden
runtime dependency. The active renderer-v14/text adapter computes the selected
analyzers from public telemetry: MET-Z pre/current mean and standard deviation,
TRC-L operation-level exclusive-latency/count log-fold rank, and LOG-R
error/log-rate shift with readable Denum templates. SIRCL's original
`case.timestamp` split is prohibited because it is label-time knowledge; use
only the registered trace-derived relative split and deterministic public-data
fallbacks. U-BASE places background/task/output instructions before evidence
in the user message; VERIFY is internal because the output remains frozen JSON.
This adaptation must not
change arm fact inventories, candidate ordering, scoring, or the model-specific
inference recipe. Similar text-only performance is a diagnostic comparison,
not a smoke gate or a promise, because datasets, anonymity, model checkpoints,
candidate universes, and scorers may differ.

RQ1.1 is restricted to one-stage RCA and at most one dashboard PNG per visual
call. The retained `multi_stage_rca` implementation is abandoned for this
paper: it must not appear in active smoke plans, formal queues, result
aggregation, or RQ1.1 claims. Multi-stage visual RCA and interactive dashboard
use are future work unless a later explicit user decision reopens them.

The active direct-RCA design is the complete 16-cell M/R/L/G text/visual
factorial plus C (equal-fact compact typed text), S (exact T evidence rendered
as pixels), and H (strict image-first A+B redundant encoding). The active
direct-QA design uses T/V/S/PathV/ContextV
for L1–L3 and the three unique T/V/S conditions for L4. QA and RCA must share
the same case, packet, renderer, model, and representation mapping so their
case-level outcomes can be joined.

The final visible `reason` may be deterministically bound to public entity,
panel, template, edge, bin and value facts and visualized as an
evidence→modality→ranking graph. This is an audit of explicit model output, not
a recovered hidden chain-of-thought. Do not claim to record, visualize, or
interpret hidden internal reasoning states.

RQ1.1 additionally registers `one_stage_counterfactual_rca` as a separate
mechanism experiment. It must use only the RQ1.1 renderer-v14, SIRCL-adapted
one-stage prompt, canonical packet, full 480-case V3 roster, model recipes and scorer;
it must never import an RQ2 renderer, selected design, content policy or
result. Its factual, targeted identity-transplant, matched placebo-transplant
and neutral-image conditions share one call and one image per arm. Pair
selection is label-blind and same-granularity. This experiment remains
non-executable until RQ2 finishes; only then may its static checks and bounded
smoke run, followed by formal execution if verification passes. Directed rank
movement is evidence of visual-semantic sensitivity, not by itself evidence of
accuracy gain or faithful causal reasoning.

RQ1.1 may initiate at most 40,000 formal model calls in total across all of its
subexperiments; its current registration is 39,360. RQ2 independently has one
aggregate 40,000-call ceiling across all of its subexperiments; its current
design/content/transfer/tool registration is 31,560. These are major-RQ
budgets, not per-subexperiment allowances.

## Experiments and artifacts

**非必要，一定要避免重跑任何东西。** Before submitting preparation,
smoke, gate, or formal work, inventory the scheduler and existing on-disk
artifacts. Reuse every compatible completed artifact and resume incomplete
content-addressed work. A completed unit may be rerun only when concrete
evidence shows that its required artifact is missing, corrupt, scientifically
invalid, or incompatible with a load-bearing changed contract. An operational
optimization that leaves model-visible evidence, prompts, schemas, inference,
and scoring unchanged does not invalidate completed preparation or smoke
artifacts. Record the evidence and the smallest necessary rerun scope before
submitting an authorized rerun.

All new long runs execute locally as ordinary background processes and must
never submit a Slurm job. Pre-render CPU artifacts before allocating a GPU.
RQ1.1 does not reuse historical RQ1 preparation or inference records. Its
formal order is `direct_rca`, then `direct_qa`. For each
experiment, run Qwen3.8 to completion and verification before Gemma; do not
condition the second model on the first model's outcome. Results live only
under `RQs/RQ1_1/results/` and never mix with protected RQ1 audit artifacts.
The later `one_stage_counterfactual_rca` successor runs only after the active
RQ2 formal suite and its own qualification are complete; it uses a new result
and prepared-artifact namespace and never resumes into the earlier RQ1.1 runs.

Successor local work is resumable by content-addressed target. Refill eligible
work only from the one active experiment, complete Qwen3.8 before starting Gemma,
and do not overlap the two models. Cross-experiment fill remains forbidden
until both models for the current experiment are complete and verified. A
registered scheduler or payload timeout resubmits the same unit, skips only
hash-valid completed case/arm targets, and restarts an interrupted target from
the beginning rather than splicing a partial response.
A non-timeout failure must be diagnosed before that unit is automatically
retried. Hash-valid model outcomes such as output-length termination,
truncation, or parse failure remain terminal scientific outcomes and must never
be relabeled as a job-timeout checkpoint. Before an automatic timeout resume,
classify existing artifacts; any infrastructure error, hash/integrity error, or
unknown status pauses automatic retry for diagnosis. Smoke, preparation,
static-test, gate, merge, and other non-formal jobs are outside the twelve-job
formal window.
Use no more than eight CPU preprocessing or artifact-writer workers and monitor
host memory. Assign each preprocessing worker to a different physical CPU core;
do not count simultaneous-multithreading siblings as independent cores. RQ1 and
RQ2 model-request concurrency is a separate frozen field:
`request_concurrency=36`. Model-request driver threads are not CPU preparation
or artifact-writer workers: the latter remain capped at eight. The RQ2 formal
runner uses up to eight core-pinned materializer processes, at most 36 simultaneous
vLLM requests, and at most eight simultaneous attention-postprocessing tasks.
It may maintain additional lightweight network/semaphore-waiting driver threads
so completed-response postprocessing cannot occupy every request driver, but
the request semaphore must continue to enforce the registered 36-request limit.
The formal runner processes different cases concurrently while preserving the
registered arm order within each case. The smoke flattens its registered
case-arm cells per model into the same bounded request scheduler so that the
qualification measures the production queue rather than a serial surrogate.
This queue depth overlaps token preflight, attention aggregation and artifact
persistence with GPU inference; it does not alter model-visible inputs,
decoding, outputs or scoring. Attention probe vectors must be transferred and
serialized in batches rather than by per-token scalar GPU synchronizations.
Attention pixel integration must visit only source-patch/mesh-cell pairs that
can geometrically overlap; rescanning every visual token for every mesh cell is
forbidden because it starves the GPU without changing the registered
overlap-weighted statistic.

`max_num_seqs` is server scheduling capacity, not generated load. Before a
heavy RQ run, a CPU-only matrix must compile every registered experiment/arm
against both effective model contracts. Every registered experiment has
exactly one independent logical smoke; that experiment's smoke must exercise
both registered models and every distinct request path and response schema that
fits within the shared call cap. Statically equivalent paths are covered by CPU
checks rather than extra calls. Do not combine several experiments into an
omnibus smoke, and do not spend a separate model call on every statically
equivalent arm. During stable inference, record request queue/running depth
with GPU utilization and throughput. Repeated GPU-idle intervals while
runnable cases remain are an operational throughput defect; startup, shutdown,
model-switch, and naturally drained-queue intervals are not. GPU utilization
percentage is not a scientific validity metric and must not be used to
reclassify an otherwise valid result.

Each experiment stores artifacts under `RQs/RQx/results/<experiment>/`:

```text
trajectories/    per-case JSON plus one conversation Markdown file per case/arm
renders/         model-visible images and render manifests
private/         evaluator-only mappings and labels
logs/            detailed and brief operational logs
summary.json     aggregate scientific metrics and validity status
```

Writes may be asynchronous, but writers must drain and verify persistence at a
lifecycle boundary. Preserve input/output/token/time/error metrics per case.
Brief logs are monitoring aids; missing brief-log fields are warnings rather
than automatic scientific invalidation when raw trajectories and summaries are
complete.

RQ1.1 and RQ2 successor calls also record client-observed TTFT, receiver
end-to-end latency, decode duration, TPOT, output-token rate, and streaming-chunk
inter-arrival summaries. Do not mislabel TTFT as pure prefill: queueing and
transport are inseparable at the client, so unavailable server-only prefill
must remain null. Chunk inter-arrival is only an ITL proxy because one stream
chunk need not equal one token. Run-level operational telemetry records
attempted/goodput requests per second, sampled GPU utilization, peak VRAM,
vLLM KV-cache high-water mark, utilization-weighted GPU-seconds, sampled-power
energy, and preparation/render time. These quantities must never block or
change inference if monitoring fails. Compare hardware timing/energy only under
the same runtime and device; token counts are the portable cost measure.

Do not inspect partial formal outcomes to tune prompts, replace cases, change
stopping, or choose an architecture. Infrastructure failures use paired
whole-case exclusion under the registered limit. Parse failures and
truncations remain model outcomes.

## Smoke and gate bounds

A registered experiment has exactly one logical smoke. Its Qwen3.8 and Gemma
phases share **one aggregate budget of at most 18 LLM/VLM calls** across all
cases, arms, stages, retries, and processes. The two model phases run
sequentially, never concurrently. The complete two-model smoke shares one
600-second wall-clock timeout measured from the logical smoke supervisor start,
including model startup, model switching, requests, persistence, and
verification. Multiple experiments do not share one smoke budget, and one
experiment may not be split into several nominal smokes.

A timeout-only outcome passes for the complete logical smoke;
any other protocol, numerical, integrity, persistence, or infrastructure error
does not. Correctness is not a smoke pass condition.

Every model call made by a bounded smoke must use streaming transport and
atomically checkpoint the accumulated response under that experiment's
`partial_responses/` tree while generation is in progress. The checkpoint must
identify the case, arm, stage, model and request, and preserve the response text
already received, chunk count and timestamps. When the phase supervisor reaches
its timeout, it must terminate outstanding work and mark these checkpoints as
`timeout_partial`; it must not discard an unfinished response merely because no
final SDK response object was returned. Streaming is a smoke observability
mechanism only: it does not change the registered prompt, sampling parameters,
output ceiling, schema, model or scientific status, and it does not add a model
call.

A complete logical model-calling gate may initiate at most 36 aggregate calls
and has a 1,200-second total timeout. At timeout, terminate outstanding work and
calculate the registered gate metrics from completed cases. Do not split one
logical smoke or gate into nominal subruns to evade either cap.

After a smoke, inspect the summary, verifier, logs, conversation histories, raw
responses, prompts, truncations, and accounting for hidden problems. Record a
hidden issue without halting routine progress. If it is safely fixable, fix it
and continue; stop only when the problem is material and cannot be resolved.

The local-only execution policy forbids switching a new run to a cluster
profile. The local profile may change only deployment paths and
`gpu_memory_utilization`; it must
not rewrite prompts, renderer, arms, scorer, roster semantics, model-specific
inference fields, or prepared evidence. Local smokes and gates remain subject
to the same aggregate call and timeout bounds above. Hardware/runtime metadata
must identify local WSL; a local artifact must never be represented as a
cluster job.

## Monitoring and decisions

Monitor a new local heavy job frequently until stable, then poll it once every
600 seconds (`sleep 600`) unless the user gives a different interval. Do not
high-frequency poll a healthy long run.

Every material project, protocol, implementation, validity, or next-step
decision is recorded with its evidence and reason. The latest project-wide
authority belongs in the current research plan and `devlog/CONSOLIDATED.md`;
RQ-specific protocols remain in the three canonical description files. Final
RQ1.1/RQ2.1 conclusions live in the single consolidated findings folder.
Supersede older policy explicitly, retain important reversals and validity
changes once, and rely on Git history plus immutable experiment artifacts for
discarded detail.

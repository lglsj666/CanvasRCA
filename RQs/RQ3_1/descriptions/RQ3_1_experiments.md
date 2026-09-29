# RQ3.1 protocol — contrastive evidence and verifiable visual diagnosis

## Status and boundary

### DD-RQ31-17: replace only the NaN-unsafe CPU BARO control

**Date:** 2026-09-19. **Status:** adopted for post-run analysis.

**Context.** Final-test preparation computed `BARO_COMPONENT` as an auxiliary
zero-LLM ranking control.  The adapter called the vendored `robust_scorer`
directly on sparse per-case metrics and thereby bypassed BARO's original input
boundary, which applies forward fill followed by zero fill.  Consequently,
baseline-only or current-only series reached `RobustScaler` as all-NaN slices.

**Decision.** Preserve the completed model experiment and exclude the embedded
NaN-unsafe BARO rankings from scientific statistics.  Before reporting the CPU
baseline, produce a versioned CPU-only successor over the same public test360
cases and candidate bindings, faithfully applying the vendored BARO missing-
value input preprocessing.  Keep the predecessor rankings for audit.  No
prompt, evidence selection, dashboard, model response, context cache or model
call is regenerated.

**Evidence.** Both model supervisors completed 2,880/2,880 calls with no
failures; the final summary contains 5,760/5,760 records, zero errors and no
missing call key.  None of the eight GPU/VLM methods consumes BARO output.  A
read-only audit of test360 found no metric column that was all-NaN for its
whole case, but 295,007/32,985,418 metric cells (0.8944%) were missing.  Forty-
eight cases contained 5,044 otherwise observed series with no baseline value,
and 40 cases contained 2,037 series with no current value.  The condition was
absent from AegisLab and concentrated in AIOPS-2022/2025.  The vendored BARO
loader explicitly performs `ffill()` and `fillna(0)`; the RQ3.1 adapter omitted
that boundary.

**Alternatives rejected.** Rerunning Qwen/Gemma cannot repair a CPU-only
control and would waste valid calls.  Reusing the embedded BARO rankings would
retain order-dependent NaN scores.  Dropping all simple controls would remove
a useful check against anomaly-only ranking when a faithful zero-call repair
is available.

**Consequences.** All 5,760 final-test model outcomes remain valid and require
no rerun.  Only the BARO CPU baseline needs a bounded recomputation before the
final statistical report; the other three CPU controls remain unchanged.

**Execution result.** The versioned successor completed all 360 test cases with
eight core-pinned workers in 103.48 seconds, zero model calls, zero failed or
missing records, and artifact hash
`a853e5925a8df108ef6c403481931e5f42e77b6f87980df17f08712da1d0df69`.
The correction changed the full entity ranking in 157 cases and the top five in
117.  None of the 149 NaN-free cases changed.  The corrected pooled metrics are
MRR 0.26264, AC@1 0.13333, AC@3 0.33889 and AC@5 0.53056.  This completes the
CPU-control repair; it does not alter or supersede any Solver outcome.

### DD-RQ31-16: selective successor rerun for the ten affected identities

**Date:** 2026-09-19. **Status:** adopted; supersedes only DD-RQ31-15's
initial no-rerun consequence.

**Decision.** At the user's request, all active eval outputs whose model-visible
candidate typing can change under DD-RQ31-15 are replaced by successor calls.
The repair cohort is frozen as eight eval identities and two not-yet-inferred
test identities.  It covers 240 effectiveness calls plus 108 calls in the six
registered 100-case follow-up experiments.  The other 472 eval identities and
their completed calls remain unchanged.

Old calls remain charged to the durable 40,000-call budget and their artifacts
are moved to a versioned audit archive rather than erased.  Active logical
inventories retire only the affected call keys.  Repaired requests obtain new
content-addressed keys, summaries are rebuilt from the mixed unchanged/new
active inventory, the deployment rule is recomputed, and a successor method
lock is issued before test preparation.  No test model call existed, so the two
test identities require preparation repair but no response invalidation.

### DD-RQ31-15: public hosting metadata determines node/pod type

**Date:** 2026-09-19. **Status:** adopted and implemented before final-test calls.

**Context.** Test preparation stopped after 19 indexed cases when the SIRCL
topology adapter encountered `ts-auth-service-79b77c-89cp5` in the public
`node_pod_map`.  The legacy name-shape fallback accepts only an 8--10 character
ReplicaSet hash, so this real pod received a three-digit service alias.  The
hosting validator correctly rejected the resulting `node hosts service-ID`
row.  A full public-metadata audit found this condition in 8/480 eval cases and
2/360 test cases, all in AegisLab.

**Decision.** RQ3.1 now treats public `node_pod_map` keys and values as the
authoritative node and pod types.  Name-shape inference applies only to
entities outside that relation.  The numeric sampling recipe is otherwise
unchanged, so unaffected cases retain the same aliases.  The validator remains
strict; it is not relaxed to accept a three-digit hosted pod.

**Evidence.** The failing test case now assigns the affected pod a five-digit
alias, produces a valid SIRCL comparator, and preserves exact X/P0 candidate
equality.  The eight eval occurrences were all non-root distractor pods and
were never emitted in the top five by either model in any of their 240
effectiveness calls.  Reapplying the registered selection rule after whole-case
removal of those eight cases still selects `X_V_CONTRAST` (macro MRR 0.446210;
runner-up `X_MTEXT` 0.431028).  This is a bounded sensitivity result, not a
claim that the old type display was correct.

**Consequences.** The initial sensitivity analysis supported retaining the
completed responses, but the user subsequently authorized the narrower repair
in DD-RQ31-16.  Test has no model calls yet and uses the corrected mapping.  The
partial pre-fix test context cache is preserved as predecessor preparation and
is not eligible for final-test inference under the successor lock.

### DD-RQ31-14: candidate identity is shared; X evidence remains direct-per-case

**Date:** 2026-09-18. **Status:** adopted and implemented before final-test calls.

**Context.** Final-test preparation failed closed on one AIOPS-2022 case because
the direct X loader promoted metric endpoint prefixes such as
`adservice-grpc` and `frontend-http` into new RCA candidates.  P0 correctly did
not contain those endpoint labels, so X had 85 candidates while the frozen task
had 74; the extra names also shifted later numeric aliases.

**Decision.** Candidate identity remains the shared frozen RCA task contract
and is taken from the exact parent public entity universe.  X still extracts
its selectable facts independently from the complete per-case metric, trace,
log and topology tables.  Metric endpoint aggregates with the registered
`-grpc` and `-http` suffixes bind to their owning candidate service while
retaining the suffix in the metric name; no endpoint label may be promoted to
a candidate.  Any other unbound metric is counted and source-hashed in the
preparation audit instead of being silently invented or dropped without a
record.

**Evidence and consequences.** The failing case now has the same 74 candidate
aliases in X and P0, binds all 4,718 metric columns, and retains 377,572 direct
public facts.  The focused evidence suite passes 29/29.  No final-test model
call or artifact existed.  Because the repair changes the implementation hash,
the ten partial test-context payloads made under the predecessor lock are
discarded and rebuilt; completed eval/mechanism model results are unchanged.
The method is re-frozen from the same complete eval inventory before test
preparation resumes.

### DD-RQ31-13: consistent prompt-guide lock and final-test restart

**Date:** 2026-09-18. **Status:** adopted and implemented.

**Context.** All eval and mechanism experiments completed, but final-test
preparation stopped before opening test telemetry because method-lock validation
recomputed the prompt digest over the 15 effectiveness arms while the freezing
path had correctly included the additional `X_C_TABLE_S` mechanism guide.

**Decision.** The validator now imports and uses the same canonical `_ARM_IDS`
set as the freezer. The original lock is preserved as
`method_lock.v1_pre_prompt_set_fix.json`; before any final-test call, a successor
lock was recomputed from the unchanged complete eval inventory.

**Evidence.** The predecessor and successor both select `X_V_CONTRAST` and have
the same prompt, config, roster, normalized-result and eval-ledger digests. The
successor differs only in its code digest, lock hash and later ledger
high-water mark. Full `audit_method_lock` passed and no final-test ledger row or
artifact existed before the new freeze.

**Consequences.** Completed eval/mechanism results remain unchanged and are not
rerun. Final-test preparation and inference bind to the successor lock. Any
future prompt-guide digest must use the one canonical arm set in both paths.

### DD-RQ31-12: atomic-marker fast resume, no bulk artifact revalidation

**Date:** 2026-09-17. **Status:** adopted and implemented.

**Context.** Restarting the interrupted effectiveness run entered the already
complete 7,200-unit Qwen phase and re-hashed/reopened its persisted artifact
graph. The process spent more than two hours on CPU bookkeeping while the
loaded Qwen server occupied about 78.8 GiB VRAM and performed no new inference.

**Decision.** Treat the atomically written per-call completion marker as the
resume commit boundary and add a model-phase completion marker. A complete
model is skipped before vLLM startup. An incomplete model reads its compact
logical inventory and skips committed units before context loading or request
materialization. Restart no longer re-hashes or rewrites completed prompts,
renders, conversations, trajectories, costs or outputs. Legacy output trees
without a phase marker may undergo a one-time logical-index rebuild using only
small output headers and completion-marker presence.

**Evidence.** The stopped verifier had run for about 7,300 seconds and reached
only 4,696/7,200 Qwen units, with zero new generations. The replacement
one-time Qwen index rebuild recovered 7,200/7,200 committed units in 1.05
seconds; the subsequent phase-marker check exited in 0.04 seconds without
starting vLLM. Gemma bookkeeping recovered its existing 2,971/7,200 commits
in 0.35 seconds. The removed verifier had also overwritten 4,696 Qwen cost
rows as cache reuse. Their output records contained no reuse reference, so the
two reuse fields were restored; the overwritten post-processing-only duration
is explicitly unavailable. Responses, token counts, model latency and scores
were unchanged.

**Consequences.** New requests retain request-identity checks, the durable call
register and commit-time integrity audit. Missing completion markers are not
accepted as complete. This is an operational resume change only: no prompt,
evidence, PNG, inference recipe, response, score or completed result changes.
The lifecycle wrapper also treats a completed 480-case context index as durable
preparation and does not re-enter the builder on ordinary restart. A context
index whose predecessor acceptance was already written as a self-binding
attestation remains usable after runner/resume-only source edits; mutable source
hashes are not a second restart gate. Unattested or incomplete contexts still
fail closed or enter the resumable builder as applicable.

**2026-09-16 implementation amendment:** DD-RQ31-09 is now implemented in the
versioned `research_v2.json` successor registration. It contains 15 eval arms,
the table-screenshot mechanism batch, three-carrier budget/load comparisons and
eight final-test methods. Source and contract static checks pass; the earlier
bounded smoke remains the applicable end-to-end smoke evidence. The prior
141-case context cache is preserved under a two-hash, validation-only
compatibility contract. No formal model inference has started.

**Historical direct-per-case revision boundary:** static-only, runtime
requalification required. At that point the instruction authorized changes and static checks, then a pause;
do not run CPU tests/preparation/rendering/smoke/inference. The earlier version
completed 18 smoke calls. Its formal preparation subsequently began, was stopped
on request, and only the two newly generated formal directories were deleted;
no formal model call occurred. Earlier qualification remains historical evidence,
not acceptance of this changed code/config.

### DD-RQ31-10: remove automatic qualification blocking

**Date:** 2026-09-16. **Status:** adopted and implemented.

**Context.** A preparation-only validator and recovery correction changed the
aggregate implementation hash even though it did not change the model request,
renderer, prompt, scorer or inference configuration. The automatic
qualification gate consequently rejected previously completed smoke evidence
for a reason unrelated to what that smoke exercised.

**Decision.** Remove the RQ3.1 automatic qualification command and all launch-
path calls to it. CPU qualification and bounded smoke artifacts remain auditable
evidence and can still be run explicitly, but their hashes no longer determine
whether a registered run may start.

**Evidence.** The earlier smoke completed all three registered logical smoke
experiments without a recorded failure. The successor change is confined to
field-aware preparation validation and recovery of atomically persisted,
unindexed contexts.

**Alternatives rejected.** Re-running model smoke solely to refresh a whole-
source hash would consume inference without exercising a changed model-visible
path. Adding another narrow hash exception would retain the same brittle class
of automatic gate.

**Consequences.** Launches still enforce registration, partitions, method lock,
request identity, call budget, model-phase isolation, persistence and result
integrity. Removing this gate does not relabel failed artifacts or authorize
changing model inputs after a formal run begins.

### DD-RQ31-09: strong direct-text contrast and no participant study

**Date:** 2026-09-16. **Status:** adopted and implemented; CPU/smoke qualification
pending. Supersedes human-study and
mandatory two-annotator requirements in older plans, not prior result status.

**Evidence and rationale.** The user has no resources for an engineer/user
study and identifies direct textual contrast as a potentially fatal alternative
explanation. Source inspection of `renderer/contrast.py::project_compact_comparative_text`
shows that X_C supplies bundle references followed by an observation catalogue.
It supplies comparison semantics, but is not a fully inline comparison table.
`main.py::_parts_from_twin` actually sends this projection; a method name alone
does not establish fair reading effort. No experimental advantage is inferred.

**Planned controls.** Preserve X_C; add X_C_TABLE, a compact direct-comparison
table from exactly the same selected facts/bundles as Contrast, to eval480 and
test360 for both models. Supply actual comparable values locally with explicit
entity/field/unit/time binding. Keep all selected standalone context, frozen
RCA shell, candidates, inference and scoring. No hidden summarization, selector
change, output-limit reduction, artificial verbosity or test-driven formatting.
Audit unique facts and presentation occurrences separately. Repeated values
are the same observation, not new events. Capacity and failure denominators
remain visible; context overflow is not evidence of superior graphic reasoning.

On the existing fixed 100-case mechanism subset, add X_C_TABLE_S: one readable
screenshot of the full X_C_TABLE incident fragment, preserving text/order and
using only lossless wrapping. It is not a dashboard, never replaces X_S, and is
not an extra deployment candidate. Compare table/its screenshot/Contrast to
separate plausible pixel-transport and graphic-organization effects; unequal
geometry or token counts prevent claims of a uniquely identified pure effect.
Add X_C_TABLE at both lower budgets and both duplicate-load levels using the
existing per-case selections and repeated bundle schedules. Other existing
interventions remain their registered X_C/vision comparisons, not table tests.

**Planned incremental allocation:** 960 eval + 720 test + 200 screenshot + 400
lower-budget + 400 duplicate-load = **2,680**. Resulting formal allocation is
**26,360**; with the existing 54 qualification allowance and 18 earlier calls,
cumulative planned core is **26,432**, leaving **13,568** within 40,000. These
are allocations, not actual spending or an authorization to reset old attempts.
There remain three logical experiments, with additions attached to existing
qualification scopes. Existing calls count against their bounds; any necessary
supplement must be registered under an allowed repair/qualification route and
charged before use. No previous smoke automatically certifies new inputs.

**Planned statistical successor, frozen before new test outcomes:** two visual
conditions against six controls (T/T_COMPACT/TPV/SIRCL_TEXT/X_C/X_C_TABLE), two
models: one 24-test final-effectiveness Holm family. Keep the original eval-only
visual deployment selection rule; do not choose a weaker text comparator or a
new visual winner on test. Screenshot-vs-table and Contrast-vs-screenshot give
four secondary comparisons across models. For each of budget and duplicate
load: 12 within-representation comparisons across three carriers/two levels/two
models, plus four Contrast-vs-X_C_TABLE paired change-score comparisons, one
16-test family. Old executed contracts/results remain versioned. Case-level
Pratt-Wilcoxon, paired dz, exposure strata and no-CI policy remain.

**Automatic evidence, not human claims.** Cancel participant recruitment and
the mandatory 600-output independent annotation task. No LLM judge or simulated
engineers replace them. Rule-bound checks classify explicit, attributable
assertions as supported, contradicted, absent from visible evidence or unresolved;
report counts, coverage, empty reasons and N/A denominators. A raw-pool fact not
shown to the Solver cannot retroactively ground its answer. Validate matcher
scope with deterministic positive/negative/ambiguous fixtures. These checks do
not score full reasoning sufficiency. Matched root-associated vs non-target
bundle removal measures output dependence, not true causal fault propagation
or hidden reasoning fidelity. Author visual QA remains engineering validation.

**Claim gate.** Visual contribution requires the direct table comparison, not
only an X_C win, selection benefit or visual ablation. Cost, ranking, redundancy
sensitivity and checkable assertions are separate endpoints; none implies
engineer productivity/MTTR. Null/negative visual outcomes narrow the storyline.
The full design, interpretation matrix and budget are in research-plan revision
8, sections 4.6, 5--7 and 11.5. Updating documentation alone never appends an arm
to an active immutable run or triggers a rerun. Future implementation must use
new request identities, preserve compatible outputs, qualify additions and lock
the expanded final-test contract before use.

### DD-RQ31-07: independent per-case evidence branches (2026-09-16)

**Status: adopted.** Supersedes the common-analyzer/common-projection approach
in the historical handoff below. The code path previously supplied X metrics
through parent metric projections and logs through the parent's Denum graph,
then rebound P0 calibration values to X. This confounds the intended comparison.

**Current implementation:**

- `build_public_source` loads the canonical per-case files; only schema, clocks,
  candidate identities and public source bindings are shared. No MET-Z/TRC-L,
  LOG-R/Denum or topology anomaly analyzer runs at this entry.
- Original T/V/TPV/T_COMPACT and P0 calibration own the inherited P0 pipeline.
  Calibration preserves its own selected facts/statistics and never binds to X.
- `SIRCL_TEXT` independently invokes its vendored analyzer closure on normalized
  per-case telemetry; its public inferred analysis split belongs to that branch.
- `SIRCL_TEXT` keeps its native payload byte-for-byte when it fits the shared
  context. Because native MET-Z has no row cap, a payload above the qualified
  49,500-character high watermark is reduced below 48,000 characters only by
  removing complete deepest native-ranked MET-Z rows, while retaining every task
  instruction, candidate, evidence section, topology relation and at least one
  metric row per represented entity. This deterministic, label-blind capacity
  adapter is shared by both models. It does not modify any image arm or claim
  that the SIRCL and visual branches select identical facts.
- X starts independently from all per-case metric columns, trace/log rows,
  graph nodes/edges and public hosting relations. It uses an explicit reference
  split at the observation interval midpoint, not a label or injection time.
  This boundary is an X method decision, not a shared preprocessing filter.
- X metrics retain constant, sparse and falling series; no positive-change,
  >3-sigma or usable-baseline threshold excludes a column. Only columns with no
  finite timestamped observation lack a numeric fact, with coverage recorded.
  X computes median/MAD excursion summaries and a 64-bin maximum-absolute-
  excursion projection, with sample counts and whole-series extrema.
- X traces use all operation/service groups in the baseline/current union,
  source-attested duration units and trace-scoped child-interval unions; absent
  trace IDs preclude the exclusive proxy, not counts/inclusive durations.
- X logs group exactly equal sanitized messages by entity/relative bin/level,
  preserve diagnostic numbers and multiplicity, and expose observed counts.
  There is no Denum template/preview or LOG-R error-keyword prefilter in X.
- X graph facts preserve concrete nodes (including isolates), edges (including
  self edges) and hosting/membership relations, not an anomaly-ranked subgraph.
- One quarter of the fixed semantic budget admits standalone source observations
  by field/entity coverage and relevance, including facts unable to form a
  bilateral comparison. These are not labeled as contrast bundles. The remainder
  selects complete registered contrast bundles; no extra LLM call is introduced.
- Each selected X fact set is shared by its T/C/S/V/mixed representations. P0,
  SIRCL and X need not select equal information. P0↔X is an end-to-end evidence
  processing policy effect (extraction + selection + reference partition), not
  a pure ranking-only effect. Standard↔Contrast within each policy isolates
  organization. No claim is made that X's finite summaries preserve every raw
  signal or that a complete source inventory fits the prompt.

**Consequences:** earlier contexts/gates cannot be reused as current inputs or
runtime proof; implementation/config hashes fail closed. Candidate universes
must match, otherwise preparation explicitly fails rather than omitting entities.
No old RQ, canonical processed file or shared Solver configuration is changed.

### Recomputed call allocation

| Work | Cases × conditions × models | Maximum calls |
|---|---|---:|
| Eval effectiveness | 480 × 14 × 2 | 13,440 |
| Mechanism interventions | 100 × 8 × 2 | 1,600 |
| Additional repeats | 100 × 3 × 2 repeats × 2 | 1,200 |
| Non-semantic robustness | 100 × 4 × 2 | 800 |
| Lower evidence budgets | 100 × 2 budgets × 2 representations × 2 | 800 |
| Redundant display load | 100 × 2 loads × 2 representations × 2 | 800 |
| Locked final test | 360 × 7 × 2 | 5,040 |
| **Formal total** | | **23,680** |
| Future qualification allowance | 3 × ≤18 | ≤54 |
| **Prospective core** | | **23,734** |
| Earlier initiated smoke calls (all complete) | read-only call-register count | 18 |
| **Cumulative core allocation** | | **23,752** |
| Repair/retry reserve | 40,000 − 23,752 | **16,248** |

The hard ceiling remains **40,000**, including earlier calls and every retry.
Three currently planned six-call smokes would consume 18 rather than 54; the
table reserves the full registered cap. Request reuse/N/A can reduce actual
calls but does not authorize extra arms. No calls are launched by this revision.

### Historical implementation handoff — superseded by DD-RQ31-07

- One request builder serves main arms, interventions, budget/load conditions,
  transformations and replicates. Full telemetry is prepared once per case;
  only selected evidence enters prompts. Test loading requires a valid method
  lock before public telemetry is opened.
- Original T/V/TPV retain their inherited construction. P0 calibration keeps
  the parent's selected item identities but binds them to the same current
  public fact projection used by X (units, trace interval semantics and fields).
  Thus P0/X selection comparisons do not silently mix two statistical
  definitions. P0 calibration versus original baselines measures adaptation
  as a whole, not only wording. Missing source bindings fail explicitly.
  Original requests, records and earlier RQ source are not modified.
- Four CPU ranking controls (anomaly magnitude, anomaly count, native BARO
  component and X internal ranking) are preserved in private execution context
  for later offline scoring, not added to model inputs.
- Execution uses a bounded eight-request worker queue and asynchronous
  persistence. Each request worker is pinned to a distinct physical CPU core;
  preparation likewise uses eight core-pinned processes and source-interleaved
  scheduling.
  Exact-input reuse is model-, case-, replicate- and smoke-scope-aware; logical
  comparisons retain separate records with explicit reuse references.
  Retry conversations, raw responses and artifact hashes are committed and
  verified; combined summaries retain both model phases.
- Static completion does not qualify candidate semantic budget 96. The
  registered standard budget remains unset until capacity/readability and
  processor-space checks pass. A code/config-bound `cpu_acceptance.json` with
  static, CPU, visual, token-preflight, source-parity and resume evidence is
  required before smoke; all three smoke records are required before formal.
- Static handoff: `../results/team_stage1/static_review_20260916.md`.
  Earlier component CPU passes and the interrupted 2/9-case capacity audit
  predate this integration and do not certify it.

### Historical qualification outcome — earlier implementation only

- The integrated CPU qualification passed 78/78 regressions, source parity,
  resume, visual, static and both-model processor token-preflight checks. Its
  authoritative gate is `../results/team_stage1/cpu_acceptance.json`.
- The three registered smoke experiments completed 18/18 requests across
  Qwen3.8 and Gemma, with no infrastructure, schema, truncation, persistence,
  candidate-ID or leakage error. Complete conversations and three dataset
  dashboards were inspected.
- Attention was disabled by protocol. No attention artifact was generated and
  every raw smoke trajectory has a null attention probe.
- All smoke RCA scores were zero on the three hash-selected qualification
  cases. This is retained as model behavior, not used as an infrastructure
  gate or an efficacy claim.
- vLLM's `EngineDeadError` lines occur only after successful HTTP responses,
  when the supervisor sends `SIGTERM` to stop each completed model phase; they
  are shutdown noise rather than failed inference.
- Review: `../results/team_stage1/smoke/review_20260916.md`. Formal execution
  remains stopped pending an explicit next instruction.

## Data roles

| Dataset | Train (unchanged) | Eval (RQ480, unchanged) | Test | Registered unused |
|---|---:|---:|---:|---:|
| AIOPS-2022 | 150 | 100 | 120 | 171 |
| AIOPS-2025 | 150 | 100 | 120 | 30 |
| AegisLab | 0 | 100 | 120 | 1202 |
| RE2-OB | 0 | 90 | 0 | 0 |
| RE2-TT | 0 | 90 | 0 | 0 |
| Total | 300 | 480 | 360 | 1403 |

These registered counts were independently verified against the generated files. All 2,543 current V3 identities occur in
exactly one of train/eval/test/unused. There is no active validation/excluded
partition. The underlying processed files are not moved.

Test must contain all former validation identities (70 per AIOPS), plus 50
former-unused identities per AIOPS and 120 AegisLab. RE2 is eval-only. Remaining
corpus cases, including former excluded non-eval cases, are unused; preserve
their source/window overlap and eligibility annotations. Unused is a role,
not a certificate that a case is unexposed or eligible for training.

## Selection and isolation

- Seed 42; label-blind stable identity hashes and intact-group subset-sum.
- Reuse unified segmentation through an explicit RQ-local adapter. Do not change
  the established global allocator, old data config or historical split.
- Reconstruct source/event/window connected components before excluding eval
  neighbours. No natural singleton assumption for missing group IDs.
- Source/window metadata may be used only for evaluator-side isolation; labels,
  root granularity, fault type, scores, model answers and rendering success are
  not selection criteria. Do not inspect prospective test telemetry for tuning.
- Preserve all existing train/eval identities. Test must not share an identity
  or connected source/event group with either. Unused may retain neighbours of
  eval and must be marked accordingly; those are not eligible test substitutes.
- Exact quotas cannot override isolation. Failure to reach a quota is a blocker,
  not permission to split a connected group or select an easier case.

## Exposure and analysis

The user explicitly reassigns the old 140 validation identities to test. They
were previously used for Composer validation and renderer failure diagnosis;
retain their origin metadata, do not rewrite their history, and stop using them
for future method development. Report overall 360, old-validation 140, added
220 and per-dataset results. Additional cases' historical exposure is not
inferred solely from the old unused name; unknown coverage stays unknown.

Freeze methods/prompts/thresholds before obtaining new test outcomes. RQ480 can
select methods now and evaluate/select checkpoints in a future learning study,
but never becomes training data merely by renaming the role. Reusing test
feedback to revise a later method changes the evidentiary status of that later
evaluation. This protocol does not promise unseen-application generalization.

## Artifacts and required checks

Adapter config: `RQs/RQ3_1/configs/data_split_v1.json`.
New registration root: `RQs/RQ3_1/results/data_registration_v1/`.
Public identities and evaluator-private windows/provenance remain separate.
Source manifests and old train/eval/validation split hashes are recorded and
must be unchanged after generation.

Checks: full-corpus coverage, no duplicate assignment, exact per-dataset counts,
old validation inclusion, preserved train/eval identities, source/group
separation, public-field allowlist, deterministic rerun, conflict rejection,
and persistence. G and C independently recomputed the outputs; five CPU
regressions and a byte-identical `--check` passed. No smoke or model test is
part of this data-only task.

The planned seven-method/two-model final test costs at most 5,040 new calls;
the prospective core is 23,734; including earlier calls the core allocation is
23,752 and the total ceiling remains 40,000.
These are allocated ceilings, not a claim that executable qualification has
already been completed.

## Team stages and acceptance

| Stage | Complete deliverable | Review boundary |
|---|---|---|
| 1. Executable method/protocol | Public evidence pool; complete comparison bundles; deterministic selector; corresponding text/visual projections; registry, scoring, budget and recovery; CPU/visual checks | E reviews the integrated stage before first model qualification; no D |
| 2. Eval development/selection | Full registered eval batch for both models, any preregistered bounded revision, durable artifact inventory and selected deployment version | Leader/C certify completeness; D analyses; E reviews; method chosen without test feedback |
| 3. Mechanism and robustness | Complete registered interventions, repeats, budget/load and non-semantic transformations on the fixed eval subset | Leader/C certify; D analyses; E reviews; lock final method and test protocol |
| 4. Locked test and synthesis | All registered test methods/models, source-exposure strata, failure denominators, costs and reproducible conclusions | Leader/C certify; D analyses; E reviews paper-readiness |

A owns `exps.py` evidence additions; B owns representation additions in
`utils.py` and the explicit RQ-local `renderer/`; C owns `main.py`, `gates.py`,
`tests.py`, experiment configs and launchers. Existing split functions remain
compatible. The leader coordinates scientific docs and interfaces. Global
runtime/scoring and historical RQ sources are not changed as implementation
shortcuts. Each child stops when its bounded deliverable is saved. D/E have no
idle monitoring role; reviews are separate per major stage under results.

## Registered experiment scope

The protocol has three logical experiments. The seven `exp_*` identifiers below
are execution batches within those logical experiments, not seven independent
claims or seven smoke studies:

| Logical experiment | Execution batches | Smoke parent |
|---|---|---|
| Effectiveness | `exp_contrastive_rca_effectiveness` | effectiveness |
| Mechanisms | `exp_visual_diagnostic_mechanisms`, `exp_replicate_stability`, `exp_budget_curve` | mechanisms |
| Robustness | `exp_transfer_and_diagnostic_robustness`, `exp_redundant_load`, `exp_final_test` | robustness |

Each logical experiment has exactly one parent smoke, capped at 18 initiated
calls and 600 seconds. Batch-level call counts remain explicit for durable
resume and accounting, while the qualification boundary is the three logical
parents above.

1. `exp_contrastive_rca_effectiveness`: all eval480, both models, 14 logical
   conditions: `T`, `V`, `TPV`, `T_COMPACT`, `P0_T_CAL`, `P0_V_STANDARD`,
   `P0_V_CONTRAST`, `X_T`, `X_C`, `X_S`, `X_V_STANDARD`, `X_V_CONTRAST`,
   `X_MTEXT`, `SIRCL_TEXT`. A compatible original request/result may be reused
   with an explicit logical mapping; a changed request gets a new version.
2. `exp_visual_diagnostic_mechanisms`: fixed hash-selected 20 eval cases per
   dataset, 100 total. Eight intervention conditions, three prespecified
   conditions with two extra replicates, and two lower semantic budgets for
   compact text and Contrast vision. The four P0/X by Standard/Contrast anchors
   reuse the first experiment. Replicates have distinct identities and are not
   independent cases.
3. `exp_transfer_and_diagnostic_robustness`: four re-anonymization/candidate-order
   conditions and four duplicate-load conditions on the same eval subset;
   seven methods on all test360 after method lock. Test methods are `T`, `T_COMPACT`,
   `TPV`, `SIRCL_TEXT`, `X_C`, `X_V_CONTRAST`, `X_MTEXT`. Natural event-pair
   analysis is evaluator-only and conditional on genuine eligible pairs.

No QA, learned reward/scorer or extra diagnostic model turn is introduced.
Each method uses one Solver call and at most one image. Selection-only CPU
baselines consume no model calls. The exact four mechanism implementations,
weights, capacities and tie-breaking are frozen in executable registration
before model execution, with source-semantic fixtures and manipulation tests.

### Mechanism matching and display-load rules (2026-09-16)

Target removal is constructed only by the private evaluator using the frozen
granularity-aware root mapping. The selector and Solver never see this label.
Match the non-target control on removed unique-fact count, modality counts,
series/point slots, relation counts and scalar-value counts; allow at most a
0.10 relative difference in the serialized public-payload character scale,
then choose the closest eligible control with a frozen hash tie-break. This is
a deterministic approximate display-scale match, not evidence of perfectly
equal pixel salience. Report realized text/pixel differences in the analysis.
The relative character difference is `abs(a-b) / max(1,a,b)` and is saved
alongside both original character counts.
No match means not applicable, not permission to select the last bundle.

Remove only facts that no retained bundle/context needs. If this leaves all
facts intact, record a semantic no-op rather than pretending a diagnostic
observation was removed; do not make an extra request merely to obtain a new
answer. The text/vision intervention pair uses the same removed observations.

Duplicate load chooses a seeded complete-bundle prefix targeting 0.25 or 0.50
of the clean semantic presentation cost. Include the first complete bundle
crossing the requested cost, with no further additions. Report requested and
realized costs, overshoot and all source references. The pressure is repeated
presentation of the same observed evidence, not extra fabricated events:
counts, values, units and time stay unchanged. Ordinary clean rendering still
deduplicates facts; pressure rendering deliberately repeats the chosen readable
evidence and identifies it as the same observation. Short reference labels
alone are not a substitute for repeated evidence. Equal resulting complete
requests reuse one outcome with two logical mappings; no-op levels are reported
as degenerate rather than additional independent interventions.

Time-alignment and grouping interventions change renderer organization only.
Never rotate, relabel or shift actual observation times. Re-anonymization is a
bijection over the entire candidate set, preserves service/node/pod type and
digit widths, and updates observations, relations, candidates and private
scoring bindings together; diagnostic numeric values are not entity IDs.

## Budget and qualification

**DD-RQ31-08 (2026-09-16, adopted):** remove the narrower agent-drafted budget
restriction and restore the user's 40,000-call per-major-RQ ceiling. The earlier
plan wording does not establish that the user independently chose the lower
number. Config, runner fallback/recovery limits and persistent call-register
settings must agree; consumed calls and historical scientific artifacts remain
unchanged. The registered conditions and data populations are not enlarged.

Budget-impact audit: 18 submitted calls, all complete smoke calls, zero formal
submissions. The current 23,680-call formal matrix was not blocked by exhaustion.
However, the earlier plan ruled out guaranteeing a full six-X-arm revision of
5,760 calls based on its smaller reserve. That planning restriction is removed:
the present 16,248 reserve can accommodate it with 10,488 left, if such a revision
is scientifically necessary and registered. This is not automatic rerun approval.

The prospective core allocation is 23,734 initiated calls: 13,440 effectiveness;
1,600 mechanism interventions; 1,200 additional repeats; 800 reduced-budget;
800 non-semantic robustness; 800 duplicate-load; 5,040 test; 54 qualification.
Earlier 18 calls remain charged, making the cumulative core allocation 23,752.
The total ceiling remains 40,000 including repair/retry and bounded eval
revision. Actual complete-request reuse reduces calls but does not authorize
new unregistered arms. A durable budget register counts every submission
attempt before network dispatch. No paid remote inference is used.

Each of the three experiments has one logical smoke, at most 18 calls and
600 seconds including startup/switching/persistence. Use seed-selected eval
cases from the three primary datasets (one each); no test and no retired
validation partition. Both models run sequentially. Timeout-only status keeps
the project's bounded-smoke semantics while reporting actual live coverage.
Implementation, persistence, numerical and data-validity failures need repair.
Inspect complete conversations and PNGs after every smoke.

## Statistical and deployment boundary

The unit is case. Report all five eval datasets separately, their equal-weight
macro, pooled480 and the two AIOPS datasets together and separately. Test is
balanced360, with per-dataset and legacy-validation140/added220 strata.
Pratt-Wilcoxon, paired Cohen's dz and preregistered Holm families are used;
confidence intervals are not reported under the project contract. Failed model
outputs remain scored outcomes; infrastructure omissions are accounted for
separately with the paired exclusion policy. No unexplained missing records
are allowed at a statistical handoff.

The primary Solver is Qwen3.8. A single visual deployment policy is selected
on eval and locked before new test outcomes; Gemma is independent cross-model
evidence. No per-test-case choice, best-of-repeats or cross-model answer union
can satisfy the performance goal. Required final targets are test MRR>=0.65
and AIOPS-2022/AIOPS-2025 test MRR each >=0.60, plus the complete scientific
evidence chain. Failure to reach a target is retained rather than corrected
by changing test membership/scoring. Model/arm comparison families and the
deterministic eval recommendation rule are fixed before inference.

### Executable naming and recommendation rule

`T_COMPACT` is the plan's compact-original-T control (formerly written `C`),
not a new condition. `X_C` remains the strong comparative compact-text twin of
the new selected evidence. These two controls must not share an alias.

Choose one deployment condition from `X_V_CONTRAST` and `X_MTEXT` using the
complete Qwen eval480 batch. Rank by equal-weight five-dataset macro MRR. When
the difference is at most 0.01, compare the minimum of the two AIOPS MRRs,
then the dataset-macro ratio of mean input-plus-output tokens to `T`, then
condition ID. This is one frozen rule, not a choice between aggregate metrics
after seeing results. Selection requires paired complete accounting for every
registered identity; known model failures remain outcomes. Unknown missing
scores or token accounting cannot be replaced by default values. The selected
Qwen policy is also evaluated on Gemma without choosing a new Gemma winner.

### Prespecified statistical families

Each family uses two-sided paired tests on reciprocal-rank differences and
Holm correction within the full stated family, including both models. Effect
size is paired Cohen's dz (mean difference / sample standard deviation of
differences). For all-zero differences report p=1 and dz=0; for a nonzero
constant difference dz is undefined, with the reason recorded rather than a
fabricated finite value. AC and cost differences are reported separately and
cannot replace an unsuccessful MRR primary comparison.

- **Final effectiveness:** on test360, each of the two fixed visual conditions
  (`X_V_CONTRAST`, `X_MTEXT`) against each of `T`, `T_COMPACT`, `TPV`,
  `SIRCL_TEXT`, `X_C`: 20 hypotheses across the two models. The deployment
  recommendation remains the eval-selected condition, regardless of the other
  condition's test score. In particular, a favorable X-visual vs X_C difference
  is a same-content comparison; X-visual vs original T is not.
- **Eval factorial anchors:** P0/X selection by Standard/Contrast organization
  gives the selection main contrast, organization main contrast, and their
  interaction per model: six hypotheses. Compute each contrast per case from
  the four actual outcomes before testing. The exposed eval status is retained.
- **Mechanism interventions:** the eight registered interventions versus their
  appropriate clean X_C or X_V_CONTRAST counterpart: 16 hypotheses. Target and
  matched-control removal also get two direct removal-difference contrasts
  (text/vision), four hypotheses across models as a separate family.
- **Budget:** 0.50 and 0.75 versus 1.00 for X_C and X_V_CONTRAST, both models:
  eight hypotheses. **Duplicate load:** 0.25 and 0.50 versus zero, the same
  conditions/models: another eight. **Non-semantic transformations:** two
  transformations by two representations by two models: another eight.

Eval comparisons of the two prospective visual conditions against the five
strong controls use the same 20-comparison family, but are explicitly
development results, not independent confirmation. Other arms, dataset,
granularity, fault-type, coverage and failure-mode tables remain fully reported;
unregistered discoveries are labelled exploratory. Repeats estimate variability
and never supply extra independent cases. Macro and pooled point estimates are
both shown; the final balanced test's pooled and three-dataset macro coincide.

Known model failures, unknown IDs and truncated/invalid outputs retain the
registered scorer behavior and failure status; never resample for correctness.
Confirmed design-capacity failures remain end-to-end outcomes with zero utility
and no invented token usage. Infrastructure failures are not diagnosis failures:
retry the identical version when safe, then apply an explicitly reported paired
whole-case exclusion across the compared conditions if necessary (maximum 5%
per experiment/model). More than 5% unresolved infrastructure loss or parse
rate below 0.95 makes that model's evidence incomplete. All failure reasons,
attempt costs and excluded identities remain available to D.

The performance target is an observed score of the single locked main method,
not a significance test or a license for test-directed iteration. Human
independent-annotator/user-study evidence requires actual authorized human
participation; subagents cannot stand in as human participants.

## Power-loss and team recovery

Persist a team assignment/status file and incremental A/B/C handoffs in the
stage result root. Source changes and completed preparation are saved before
a child exits; no assumption of session-memory survival is permitted. On
resumption, inspect actual process identity/liveness and saved artifacts,
then continue the saved next task without duplicating a live process.

Experiment recovery uses the atomically persisted completion marker and compact
logical inventory. It does not bulk re-hash completed artifacts after restart.
Submission, streaming partial response and completion remain distinct states;
interrupted answers are never stitched to another call. Complete outputs
survive a missing aggregate summary and can reconstruct it from committed
result/cost rows.
Test CPU interruption points before dispatch, during a response, after a
record commit and before summary commit. Explicit pause stops new submissions
and drains completed writes. A hard reboot reruns only uncommitted or corrupt
targets and keeps attempt accounting, including unknown in-flight outcomes.

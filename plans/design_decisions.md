# Design decisions

This file records the newest operative load-bearing decision for each topic.
When a decision changes, preserve the necessary context and evidence in its
newest authority and remove the superseded entry. Surviving IDs are not
renumbered because artifacts, findings, and devlogs may cite them. Historical
detail remains available in Git history and the dated project records.

---

## DD-13a: Keep plain top-K because selector effects are unresolved

**Date:** 2026-07-27
**Status:** adopted after all registered selector cells completed

**Context.** Coverage-first selection increased the number of represented
services, but early Gemma-only results overclaimed that depth was better than
breadth. The completed cross-model comparison is the authority.

**Decision.** Keep plain top-K as the default selector by the registered
simpler-on-a-draw rule. Retain `cov12` and `cov30` only as ablation presets.
Do not claim that coverage helps or that depth is generally superior.

**Evidence.** On the equal-density `cov12 - v0` comparison, the five paired
MRR deltas were -0.079, -0.052, -0.034, -0.034, and +0.050. Four of five were
negative, but the sign test was not significant (`p=0.188`) and every effect
was below the approximately 0.10 resolution of the 100-case comparison. Qwen
3.6-27B produced the lone positive result and the highest individual open-model
cell, so neither a universal selector effect nor a model-family effect is
supported.

**Alternatives rejected.** Coverage-first was not promoted because its measured
benefit was unresolved. A general “depth beats breadth” conclusion was rejected
because it was inferred before the Qwen cells completed.

**Consequences.** Selector choice is not treated as a settled performance lever.
Any future promotion needs a newly registered, adequately powered comparison;
the current RQ1 final run keeps its frozen renderer unchanged.

---

## DD-35: Start RQ2 with a staged factorial design study, not another RQ1 rescue
**Date:** 2026-08-04
**Status:** adopted for static implementation; inference locked

**Context.** The completed RQ1 mechanism screens did not establish stable
visual complementarity, but they also did not establish that every dashboard
design is useless. The RQ1b3 row-order sham
shows that arrangement substantially changes the model's ledger and final
selection, while the negative accuracy result shows that influence alone is
not benefit. The project roadmap separately defines RQ2 as the causal study of
dashboard content, encoding, arrangement, and interactions. The exposure audit
contains 318 eligible exposed incidents outside every frozen private roster and
locked RQ1 gate (94 AegisLab, 115 AIOPS-2022, 109 AIOPS-2025), enough for a
150-case independent RQ2a gate and a later disjoint 90-case downstream
development cell. RQ2 development can reuse already executed exposed RQ1 cases
without consuming new evidence.

**Decision.** Adopt
`RQs/RQ2/descriptions/rq2_master_protocol_v1.md` as the RQ2 research structure.
Begin with RQ2a: a full `2^4` equal-fact factorial over metric encoding, graph
encoding, cross-source arrangement, and entity ordering. Use answer-hidden,
machine-scored temporal, relational, alignment, missingness, and exact-lookup
operations. Estimate each design action through within-incident anchor-state
relative credit, averaging over the other factor contexts. Keep content
presence/absence in a separate RQ2b unequal-content study and downstream RCA in
RQ2c, so new facts, visual encoding, and layout are never collapsed into one
ambiguous effect.

RQ2a development reuses 60 already executed exposed incidents and Gemma only.
It is a spending screen, not evidence. A disjoint 150-case gate runs both Gemma
and Qwen only if the complete development rule passes. The screen requires at
least one target-family main effect of +0.10, repairs over breaks, lookup
degradation above −0.05, no dataset at or below −0.10, parse at least 0.95,
infrastructure exclusion at most 5%, and complete integrity. At n=60 and paired
SD 0.36, the approximate 80%-power MDE is 0.130, so no development p-value is
used. The n=150 gate requires +0.10 and Holm-adjusted paired Pratt-Wilcoxon
p<0.05 plus the registered safeguards; its planning MDE is 0.082–0.114 for SD
0.36–0.50.

This decision authorizes directories, contracts, renderer variants, compilers,
tests, read-only feasibility checks, and static qualification only. No RQ2
model request is authorized until a later decision attests the frozen roster,
facts, renderers, salience formula, prompt, answers, leakage/parity audit,
manual review, smoke, analysis code, and runtime tree.

**Alternatives rejected.** Re-running RQ1b3 with a relaxed parser would be
outcome-driven and remains negative under sensitivity analysis. Moving directly
to RQ1c/RL/training violates three failed complementarity mechanisms. Testing
all dashboard changes in one end-to-end RCA comparison would confound content,
encoding, and arrangement. Treating the row sham as proof of benefit confuses
causal influence with correct influence. Opening heldout data before design
qualification would spend confirmatory evidence on an unproven renderer.

**Consequences.** RQ2 now owns six project-standard directories and a frozen
master protocol. `RQs/RQ2/src/` remains untouched. The immediate task is static
RQ2a implementation and qualification; GPU inference remains locked. RQ0/RQ1
results, locked RQ1 gate rosters, reserve, and heldout partitions are unchanged.

**Initial execution evidence.** The six-directory layout, frozen YAML contract,
16-cell factorial enumerator, eight matched anchor pairs per main effect, four
anchor quadruples per two-factor interaction, label-blind salience function,
and order-insensitive set canonicalizer are implemented under RQ2's mutable
`scripts/` tree. Nine RQ2 tests and targeted Ruff checks pass. The read-only
feasibility audit confirms 991 eligible exposed incidents, 373 cases reusable
from executed rosters, and 318 cases outside every frozen roster (94/115/109),
while preserving both locked RQ1 gates. The static qualification artifact is
SHA256 `9bf784b2ffa8135c017e45481c0d89ef97283e07c32422543c41c172cc43f7db`.
Its status is explicitly `passed_static_contract_only`; the listed renderer,
compiler, roster, audit, review, smoke, analysis, and runtime blocks still
prevent inference.

---

## DD-52: Reassign two unopened RQ1 gate rosters to preserve the RQ2 sample design

**Date:** 2026-08-05
**Status:** Accepted for RQ2a static implementation; inference remains locked
**Supersedes:** Only the data-source clause in RQ2 master protocol v1 that
required the independent and downstream pools to lie outside every historical
RQ1 roster

**Context.** The RQ2 v1 static check assumed at least 80 eligible exposed cases
per dataset remained outside every RQ1 private roster: 50 for the independent
gate and 30 for a downstream lock. After the later RQ1b6–b9 roster freezes,
the actual outside-roster counts are only AegisLab 20, AIOPS-2022 41 and
AIOPS-2025 35. Shrinking the 150-case gate would materially weaken its planned
MDE and asymmetric per-dataset capacity would break the balanced design.

**Decision.** Preserve the 60-case RQ2 development screen on already executed
exposed RQ1 incidents. Reassign the unopened, disjoint
`rq1b2_gate_private_v1.json` roster—exactly 50 cases per primary dataset—as the
source of the 150-case RQ2a independent gate. Reassign the separate unopened
`rq1b3_gate_private_v1.json` roster as the downstream-lock source, selecting
30 of its 50 cases per dataset by the frozen RQ2 hash and retaining the other
20 per dataset as an unopened buffer. Create new RQ2-owned rosters with hashes
and lineage; do not edit or execute the historical RQ1 roster files. This
permanently retires those rosters from their old RQ1 gate roles and does not
reopen RQ1.

**Evidence.** The exposure ledger contains 318/340/333 eligible exposed cases
for AegisLab/AIOPS-2022/AIOPS-2025. The union of all current RQ1 private rosters
leaves only 20/41/35 outside it. Each reassigned gate roster contains 150 unique
cases, 50 per dataset; every one of its cases is absent from every other RQ1
private roster. Neither roster has any opaque incident directory anywhere
under `RQs/RQ1/results/`, and RQ1 has no corresponding gate result directory:
only its development and smoke predecessors exist. Thus no model outcome,
render or trajectory was observed for either pool.

**Alternatives rejected.** Lowering the gate to 20 cases per dataset would
raise the approximate paired MDE and remove the planned 90-case downstream
lock. Opening reserve, heldout or RE2-TT would violate partition rules. Treating
prior RQ1 execution as automatically disqualifying would discard two perfectly
unopened exposed pools for historical names rather than scientific exposure.

**Consequences.** RQ2 must version the data contract and make the reassignment
explicit in its protocol, config, static checker and generated roster lineage.
The 60/150/90 sample sizes, model roles, statistical thresholds and all
information/leakage rules remain unchanged. The reassigned independent and
downstream cases may not be inspected for RQ2 model outcomes before their
registered stage. This decision authorizes only static roster construction and
qualification; a later decision is still required before model inference.

**Static completion.** The v2 roster generator and its drift-check mode passed
the 10-test RQ2 static suite and lint. The frozen manifest is
`RQs/RQ2/configs/rosters/rq2a_roster_bundle_v2.json`, with canonical bundle
hash `c304f3c0831b5b47c9ee4c10527760206b6a362626c0c0ab02ab762fc9eb1bc4`
and file SHA-256
`b27b87c68b466d160aa2e735d244cffbe1f294d02608bd1047064561e17b0711`.
It freezes 60 development, 150 independent-gate, 90 downstream-lock and 60
buffer cases; all four private sets are pairwise disjoint. The generated
contract remains `frozen_static_inference_locked` and does not authorize a
model call.

## DD-54: Use a canonical vLLM scheduling capacity of 64 sequences

**Date:** 2026-08-05
**Status:** adopted

**Context.** An earlier runtime used `max_num_seqs=8`, and the GPU was
frequently underfilled. The field limits scheduler capacity rather than
requiring every batch to contain that many sequences.

**Decision.** Set the maximum scheduler capacity to 64 sequences for both
Qwen3.6-27B and Gemma-4-26B-A4B-it. This decision changes no other inference
field; the current global unified config remains authoritative for precision,
sampling, context, output, image processing, chunked prefill, structured output,
and memory behavior. Historical run contracts remain immutable.

**Evidence.** The user reported prior stable use of 64 with both model classes,
and the smaller capacity visibly underfilled the GPU. The current Nibi v12
smoke and v7 live server attestations exercise the unified 64-sequence config
with the exact registered models and no capacity-related infrastructure error.

**Alternatives rejected.** Keeping 8 was rejected because it unnecessarily
constrained batching and left the GPU underutilized. Changing additional
runtime fields was rejected because the request was limited to this single
capacity parameter.

**Consequences.** Every future run records 64 in its effective configuration
and still requires ordinary live attestation and bounded qualification.

## DD-62: Bound diagnostic calls and time, then inspect their artifacts

**Date:** 2026-08-06
**Status:** adopted

**Context.** Earlier copied diagnostic protocols expanded to hundreds of model
calls and ran for hours. A small diagnostic can also look healthy in a brief log
while a persisted conversation, prompt, response, or accounting record exposes
a hidden bug.

**Decision.** One complete logical smoke may initiate at most 18 aggregate
LLM/VLM calls and has a 600-second supervisor timeout. One complete logical
model-calling gate may initiate at most 36 aggregate calls and has a 1,200-second
timeout. Each bound covers every model, case, arm, stage, retry, and process;
splitting or renaming a logical diagnostic does not reset it. At timeout,
terminate outstanding work and preserve completed artifacts. A timeout-only
smoke passes; any other protocol, integrity, persistence, numerical, or
infrastructure error does not.

Enforce the time bound with ordinary monotonic or process wall-clock time;
second-level precision is sufficient. After every smoke, inspect the summary,
verifier, logs, prompts, raw responses, conversations, truncations, and
accounting rather than relying on the brief operational log.

Every hidden issue is recorded. A safely repairable issue triggers a
forward-versioned fix, affected contract/hash refresh and verification, after
which work continues. The agent stops only when the issue is material and
remains unsolved after reasonable in-scope diagnosis and repair; the blocker,
evidence and affected scope must then be recorded.

**Evidence.** A copied RQ1 smoke completed 204 calls and a following perception
gate planned 144, directly demonstrating unbounded diagnostic cost. Later
failures were visible in detailed trajectories rather than high-level progress
lines. The qualified Nibi v12 smoke stayed below the cap with 13 initiated
calls, passed under the timeout-only rule for Qwen, completed normally for
Gemma, and passed complete post-smoke artifact review.

**Consequences.** Diagnostic implementations remain small and locally timed.
An automated inventory may support review but cannot replace inspection of the
persisted evidence. Fixable issues receive a forward-versioned repair and
refreshed contract; unresolved material issues are recorded as blockers.

## DD-64: Retry transient NVML failures without changing the RQ1 experiment

**Date:** 2026-08-07
**Status:** Adopted; Qwen formal rerun restarting under a model-specific
operational runtime freeze

**Context.** The RQ1b9 typed inference-v2 Qwen development rerun remained
healthy at the canonical vLLM endpoint, but its per-call 50 ms NVML sampler
converted transient WSL/NVML `The operating system has blocked the request`
responses into infrastructure failures. The first terminal-attached attempt was
already invalid after its server lifecycle ended. A subsequent fully detached
four-runner attempt produced 630 completed call records and six NVML failures
affecting five of 90 cases. Its 5.56% affected-case fraction exceeded the frozen
5% whole-case exclusion ceiling, so the attempt was stopped and archived before
analysis.

**Decision.** Preserve every failed attempt and restart Qwen from empty
authoritative shard roots. Amend only `GPUAccounting`: retry transient NVML
query errors at the existing 50 ms sampling interval, allow 30 seconds for the
first valid sample, make a bounded five-second final-sample attempt, record the
number of transient errors, and continue to fail closed if fewer than two
samples exist or the sampler cannot stop. Keep at most four runner processes.
Do not change any prompt, evidence artifact, roster, condition order,
checkpoint/tokenizer, inference-v2 model setting, typed two-stage handoff,
response schema, scoring rule, exclusion threshold or statistical analysis.

Gemma retains its completed old-accounting cells. Before changing the runtime
tree, a dedicated fail-closed verifier sealed all three Gemma cells against the
then-current runtime and raw artifacts. Qwen receives a distinct
`runtime_freeze_qwen_accounting_v2.json`; final joint verification must validate
the sealed Gemma verification and current Qwen runtime separately before
requiring cross-model case identity.

**Evidence.** The invalid detached attempt is recorded at
`RQs/RQ1/results/rq1b9_legacy_typed_development_v3/_invalid_attempt_qwen_nvml_exclusion_ceiling_20260807/attempt_status.json`.
Gemma's sealed verification hashes are
`eaf2adfbd89e76a9cf2dccc8abb110768b3aa540ce87b41ef808df072bf9f583`
(development),
`9d3b60bb05f7eabc04395eb97a1ea414f77cbc16a291cf0236ba62097115769c`
(independent), and
`49254a3440e3ffa139879a5165e59d8aba2f5090ff87d9c69bdbed6e9b7dbffa`
(transfer). The accounting unit/regression suite passed 31 tests. A live
four-process, 15-second probe against the resident Qwen server produced 298
samples per process, zero transient errors and clean reports. The new Qwen
freeze hashes are `f0bc76cc…e2bb04` (development),
`ac16399e…21b5aa` (independent), and `a57a6892…b6767` (transfer).

**Alternatives rejected.** Counting NVML failures as model outcomes was
rejected because no model response or parse failure caused them. Continuing
after five affected cases was rejected by the registered 5% ceiling. Removing
GPU accounting was rejected because token/GPU/cost accounting remains part of
the experiment contract. Reducing concurrency alone was rejected because four
runners already respected the project maximum and still encountered global
transient NVML events. Rerunning Gemma was rejected because its complete cells
had zero infrastructure errors and were sealed under their original runtime
before the operational patch.

**Consequences.** The three archived Qwen attempts remain invalid and cannot be
mixed with the replacement. Qwen restarts all three scopes and records
`gpu_accounting_transient_errors` per successful call. Any call still lacking a
complete accounting report remains an infrastructure failure under the same
paired-case exclusion policy. Final RQ1 claims remain blocked until Qwen's
development, independent and transfer scopes complete and joint verification
and preregistered analysis pass.

## DD-43: Adopt a compact Nibi-portable source and global-contract layout

**Date:** 2026-08-09
**Status:** adopted

**Context.** The WSL implementation accumulated multiple copied generations of
RQ1 tooling: the retained RQ1 packages alone contained roughly 25,000 lines of
Python, while experiment configs, descriptions, findings, and launchers mixed
historical and current protocols. The layout also embedded workstation paths,
stored Python entry points under shell-script directories, and treated serving,
splitting, and scoring as partially independent per-RQ contracts. This was hard
to audit and unsuitable for a clean Nibi deployment.

**Decision.** Supersede the previous directory convention in this clean
workspace. Shared Python lives under `src/`; shell entry points live under
`scripts/`. The only root configs are the unified vLLM, dataset segmentation,
and RCA scorer YAML files, backed by extensible classes in
`src/unified_scripts/`. Every RQ has exactly three description documents, one
finding document per experiment, no more than ten/800 lines of shell launchers,
and five functional Python modules plus `__init__.py`, with a 2,500-line
functional-source ceiling. The shared `vlmrca` package moves from the RQ tree to
`src/vlmrca/`. RQ-specific adapters remain explicit and hash-recorded.

The Nibi serving contract omits `--gpu-memory-utilization`; no CanvasRCA VRAM
fraction cap is imposed. The model-specific Qwen/Gemma processing differences,
unquantized BF16, sampling, context/output ceilings, and scheduler capacity are
otherwise preserved. Build tooling uses the Alliance module and wheelhouse
workflow and Slurm shell launchers. This local preparation is static-only.

**Evidence.** Before cleanup, the RQ1 `rq1c_rca_v1`, `legacy_typed_v3`, and
`rq1lib` Python trees contained about 8,035, 6,153, and 11,098 lines
respectively. The refactored five RQ1 functional modules contain 1,286 lines;
four short RQ1 shell entry points contain 73 lines. Root `configs/` contains
exactly three files. Alliance documentation establishes Lmod modules, the
Alliance Python wheelhouse, Apptainer rather than Docker, Slurm batch execution,
and Nibi H100 resources.

**Alternatives rejected.** Moving copied RQ1 packages under the shared source
tree would satisfy the directory shape while preserving the maintenance
problem. Keeping separate frozen per-RQ inference/split/scorer configs would
allow fairness-critical drift. Setting GPU memory utilization to `1.0` would
still impose a project cap and increase OOM risk; omission expresses the user's
requested no-cap policy without falsifying physical memory limits.

**Consequences.** Historical copied code is recoverable from Git but is not part
of the Nibi worktree. RQ1 retains its experiment semantics through one
configuration-driven engine and four consolidated findings. Deployment must
build a new environment, freeze new hashes and rosters, run the bounded smoke,
and use new result IDs. A future RQ may subclass the unified contracts, but any
fairness-sensitive change requires a named adapter and a new protocol decision.

## DD-67: Finalize six RQ1 experiments on the eligible frozen evaluation roster

**Date:** 2026-08-09
**Status:** adopted

**Context.** The Nibi refactor consolidated four RQ1 experiments but the final
program still needed (a) a causal check that visual semantics, rather than mere
prompt perturbation, move the agent's evidence and ranking and (b) a check of
whether useful evidence is lost at the two-stage handoff. The project already
has a long-frozen 480-case evaluation roster; eleven cases carry an existing
invalid status. CodeShrink (arXiv:2607.29637) offered an analogy about spending
a fixed image canvas on readable content, but it is a 2026 preprint about
code-image compression rather than RCA.

**Decision.** Register `visual_counterfactual_rca` and `ledger_handoff_rca`
alongside `legacy_q9`, `cross_region`, `typed_two_stage`, and `matched_rca`.
Rerun all six on Nibi under new result IDs using all 469 eligible frozen cases:
96 AegisLab, 100 AIOPS-2022, 93 AIOPS-2025, 90 RE2-OB, and 90 RE2-TT. Exclude
the eleven invalid cases without replacement. Headline inference uses only the
289 AegisLab/AIOPS cases; RE2-OB and final-OOD RE2-TT remain separate slices.

The counterfactual experiment holds text and compute fixed while comparing the
factual image with label-blind targeted, placebo, and neutral interventions.
The handoff experiment compares semantically identical typed-text, visual, and
strict redundant handoffs before a common RCA stage. Fixed-fact blank-space
compaction is deferred to RQ2 because it changes layout, an RQ2 design axis.

**Evidence.** The roster arithmetic is 96+100+93+90+90=469, with 289 primary
cases. Existing RQ1 experiments distinguish direct perception, cross-region
composition, typed transfer, and end-to-end RCA but do not isolate controlled
visual influence or the representation of the intermediate ledger. CodeShrink
supports only the high-level fixed-canvas analogy; it supplies no RCA evidence
and has not been treated as such.

**Alternatives rejected.** Replacing invalid cases was rejected because it
would silently change a frozen evaluation roster. Pooling saturated RE2 slices
into the headline was rejected because it would distort the main-dataset
effect. Copying CodeShrink's attention/KV pruning or training machinery was
rejected because it changes effective information/compute and is not an RCA
intervention. Adding blank-space compaction to RQ1 was rejected to keep content
and layout redesign out of the representation-value claim.

**Consequences.** RQ1 now has exactly six finding authorities and three
canonical description files. Historical local outcomes remain historical;
final claims require complete, paired, newly identified Nibi artifacts. RQ2
does not begin until these RQ1 results are verified and the representation
decision is recorded.

## DD-68: Freeze the Nibi deployment and continue all six RQ1 experiments

**Date:** 2026-08-09
**Status:** adopted before the first Nibi model call
**Supersedes:** DD-43's static-only deployment state and any gate-based stopping
interpretation for the final RQ1 sequence

**Context.** Direct Nibi qualification found that the supplied raw benchmark
trees were not the processed per-case schema consumed by CanvasRCA. It also
found deployment incompatibilities: the available Pillow build differed from
an impossible requirement pin, the upstream loader modules had moved, an
installed wheel could not resolve worktree-relative configs, and the first
Nibi dashboard exposed a natural ingress-service alias in propagation rows.
The final study must execute all six registered experiments. Scientific gate
thresholds are decision evidence, not authorization to truncate that sequence.

**Decision.** Use separate base and inference virtual environments built from
the Nibi module stack and Alliance wheelhouse. Freeze base Pillow at the exact
available 12.1.0 build; keep the registered inference stack at vLLM 0.24.0,
Torch 2.11.0, Transformers 5.14.1, and xgrammar 0.2.3. Stage both official
model repositories at their recorded immutable revisions and require their
download manifests in every runtime freeze.

Use the named `src_data_cache_v1` upstream adapter and the
`processed_public_private_v2` case adapter. Write only derived public/private
per-case artifacts to `CANVASRCA_PROCESSED_ROOT`; retain source datasets as
read-only. Public telemetry uses relative time and canonical salted opaque
incident IDs, while labels, source IDs, fault types, and absolute times stay in
physically separate evaluator-private files. Freeze renderer-v16, which extends
case-local numeric identity substitution through projected graph, metric, log,
trace, and pod-to-service aliases.

Run the registered three-case, 18-call smoke on two simultaneous 30-minute
H100 allocations. After infrastructure qualification, pre-render all 469
eligible frozen cases on CPU and submit every combination of six experiments
and two models in resumable H100 arrays. Repair and resume bugs, mismatches,
and infrastructure failures. Record a scientific threshold miss as a negative
result but continue the remaining experiment sequence unchanged. The current
resource policy is recorded separately in DD-74.

**Evidence and reasons.** CPU jobs 19388694, 19388696, 19388697, 19388698,
and 19388700 converted all five datasets; jobs 19389686 through 19389690
migrated the generated identity mapping without changing source data. The
validator checked 469 exact roster entries and 1,407 timestamp ranges with no
public privacy or schema error. Model jobs 19388701 and 19388703 completed
revision, byte-inventory, and full SHA-256 manifests. Representative
AIOPS-2022, AIOPS-2025, and RE2-OB renderer-v16 dashboards and alternate
presets were visually inspected; all identities are numeric and the prior
alias is absent. The RQ1 static suite passes with zero model calls and confirms
all six experiments, 469 roster entries, source/layout limits, unified server
arguments, and scorer semantics. The inference environment imports the full
RQ1 path at the exact registered versions and has no broken requirements.

**Consequences.** CPU preparations from renderer-v12 through v15 and any
preparation made before `execution_enabled: true` are diagnostic artifacts,
not legal inference inputs. Every GPU run must match a freshly prepared
runtime-freeze hash. RE2-OB and RE2-TT remain separately reported; RE2-TT is
not inspected or used for development. Failure to satisfy an efficacy
threshold does not relax any validity rule and does not halt the six-experiment
run.

## DD-69: Isolate concurrent Nibi vLLM servers by task-local ports

**Date:** 2026-08-09
**Status:** adopted
**Supersedes:** the assumption in DD-68 that one fixed localhost port is
isolated by a one-GPU Slurm allocation

**Context.** Nibi can place several independent one-GPU Slurm jobs on the same
multi-GPU physical node. GPU isolation does not create a separate network
namespace. The first final arrays launched all vLLM servers on port 8000; on a
shared host, one launcher could therefore reach another allocation's server.
The live attestation caught Qwen jobs whose models endpoint exposed Gemma, but
fixed-port operation is invalid for concurrent arrays.

**Decision.** Keep port 8000 as the portable global default and treat the
actual localhost port as recorded deployment metadata. Each Nibi task derives
a candidate from its unique `SLURM_JOB_ID`, verifies that it is currently
unbound, exports `CANVASRCA_VLLM_PORT` and the matching `VLLM_BASE_URL`, and
uses that effective port consistently for server arguments, readiness,
attestation, tokenization, and inference. Record both values in the heavy-run
runtime contract. This changes no model, decoding, prompt, evidence, or
scoring field.

**Evidence.** In v4, Qwen tasks `19392682_2`, `19392682_3`, and
`19392684_2` were co-located with Gemma work and failed attestation with served
model `google/gemma-4-26B-A4B-it`. The active jobs were cancelled immediately.
Static tests now verify that a port override changes both `--port` and the
effective base URL; simulated task IDs select distinct endpoints.

**Consequences.** The v4 inference artifacts are diagnostic and cannot enter
analysis. Because launcher and unified-source hashes changed, both bounded
smoke and all 469-case preparations must be regenerated before the full arrays
are resubmitted. Any future multi-job local service must likewise avoid a
shared fixed port or use an allocation-specific network namespace.

## DD-70: Use a uniform context-safe RQ1 output adapter

**Date:** 2026-08-09
**Status:** adopted for the replacement final RQ1 execution
**Supersedes:** the use of the complete 16,384-token global output ceiling as
the requested budget for every RQ1 call

**Context.** The v5 arrays demonstrated that the global inference ceiling is
not a feasible per-request budget for every frozen case. Three long RE2-TT
text packets in the completed Gemma `legacy_q9` shards had at least 16,385
live-tokenized input tokens. Requesting the full 16,384-token output ceiling
therefore exceeded the 32,768-token context and vLLM correctly returned HTTP
400 for both T and H. This is a deterministic request-contract failure, not a
model-quality result. Independently, the ledger handoff exposed a Unicode
font bug. Once both defects were known, all remaining v5 arrays were cancelled
so partial outcomes could not become a mixed-protocol final result.

**Decision.** Register `context_safe_output_v1`, version 1, as an RQ1-specific
inference adapter. Keep the global context and output ceilings at 32,768 and
16,384 tokens respectively, but set the actual requested RQ1 output budget to
8,192 tokens uniformly for both registered models, every experiment, every
arm, every case, and every stage. The runner uses the live server tokenizer
before every call and refuses a request unless input tokens plus 8,192 fit the
context. Record the adapter and its hash in the runtime freeze and each stage.

**Evidence and reasons.** The failed prompts required only a feasibility
correction: their model-visible evidence, candidates, question bytes, and arm
ordering were complete and remain unchanged. An 8,192-token budget reserves
half of the fixed context for input while remaining far above the observed
thinking-disabled structured responses. Applying one budget globally avoids
an arm-, case-, dataset-, or model-specific compute difference. Deleting or
summarizing evidence would violate equal information; dynamically shrinking
only long cells would create an avoidable fairness difference; increasing the
context would change the registered model-serving protocol and its memory
profile.

**Consequences.** Every v5 trajectory is diagnostic and excluded from final
analysis, including successful calls. A fresh bounded two-model smoke and a
fresh 469-case preparation are required because the config, runner, and ledger
renderer hashes changed. The six mandatory experiments then restart under one
new immutable freeze. A scientific threshold miss remains non-stopping, while
any further mismatch, bug, or infrastructure error is repaired and rerun.

## DD-74: Give full GPU shards one day and 100 GiB

**Date:** 2026-08-10
**Status:** adopted

**Context.** Completed RQ1 v7 shards showed that some full experiments need
more than twelve hours but finish within one day. Seventy remaining v7 shards
were still pending under oversized three-day, 240-GiB requests after all active
tasks had completed.

**Decision.** This is the sole current Slurm resource-allocation decision.
Full GPU submissions that divide work into resumable shards request one day per
array element, one H100, 14 CPUs, and 100 GiB of host RAM, with at most four
simultaneous tasks per array. H100 smokes retain their registered 30-minute
bounds and use at most 100 GiB. CPU preparation, dataset-processing, and model-
download jobs retain their smaller registered requests.

**Evidence.** All 26 v7 tasks that had started completed with exit code zero;
several Qwen shards required roughly 20--23 hours. The exact 70 still-pending
elements of parents `19397355`--`19397366` were cancelled and replaced by
arrays `19466700`--`19466711`. Slurm receipts confirm `1-00:00:00`, 100 GiB,
14 CPUs, one H100, and array throttle four. This is operational evidence only;
no partial scientific outcome was inspected.

**Alternatives rejected.** Twelve hours would force predictable timeout-and-
resume churn. Three days and 240 GiB reserve more scheduler capacity than the
observed work requires. Editing the freeze-covered launcher before completing
v7 would invalidate its prepared runtime contract, so the replacement arrays
use explicit Slurm resource overrides instead.

**Consequences.** The replacements resume into the existing v7 shard roots
under runtime freeze `73f2667a...47a`; completed shards are not rerun. Until
that lifecycle closes, every further v7 repair uses explicit
`--time=1-00:00:00 --mem=100G` overrides and records the effective receipt.
The launcher default changes only with a newly prepared runtime freeze.

# Current design decisions

This file contains only the latest operative decision for each project topic.
Superseded intermediate decisions have been consolidated into their final
authority. Historical detail remains available in Git history, dated devlogs,
findings, and experiment artifacts.

Existing final IDs are retained so older references remain interpretable.
The consolidated lineage is:

| Earlier decisions | Current authority |
|---|---|
| DD-35 | DD-52 — RQ2 staged design and roster policy |
| DD-54, DD-64, DD-68, DD-69, DD-70, DD-74, DD-76 runtime clause, DD-77, DD-78 | DD-91 — Nibi runtime, context capacity, and concurrency |
| DD-67 | DD-86 — final RQ1 experiment program |
| DD-75, DD-84 | DD-85 — renderer, representations, and prompt contract |
| DD-79, DD-80 | DD-83 — typed Q&A selector contract |
| DD-62, DD-81, DD-82 | DD-88 — bounded smoke/gate and response preservation |
| DD-76 attention clause | DD-87 — same-prefill visual diagnostics |
| DD-89 | DD-90 — visible record-key RCA selector |

---

## DD-13a: Keep plain top-K as the default selector

**Date:** 2026-07-27  
**Status:** adopted

**Decision.** Keep plain top-K as the default telemetry selector. Retain
coverage-first presets only as ablations and make no general claim that either
depth or breadth is superior.

**Reason.** The completed equal-density comparison was model-dependent and
statistically unresolved: four of five paired MRR deltas favored plain top-K,
while Qwen produced the one positive coverage-first result. The evidence does
not justify promoting a more complex selector.

**Consequence.** A future selector promotion requires a newly registered,
adequately powered comparison. Current RQ1 rendering remains frozen.

---

## DD-43: Use the compact Nibi-portable project layout

**Date:** 2026-08-09  
**Status:** adopted

**Decision.** Keep shared Python under `src/`, shell entry points under
`scripts/`, and exactly three global configs and implementations for vLLM
inference, dataset segmentation, and RCA scoring. Each RQ has the canonical
descriptions/configs/findings/scripts/src/results structure. Its five functional
Python modules stay within 5,000 lines; RQ1's provisional renderer is the only
current RQ-local package exception.

Global contracts are extensible frozen bases. An experiment-specific adapter
must be named, versioned, scoped, and hash-recorded. Paths remain project-
relative or environment-supplied. Nibi deployment uses Slurm, Lmod, the
Alliance wheelhouse, and Apptainer-compatible workflows.

**Reason.** The prior copied RQ1 generations were difficult to audit and
allowed fairness-critical runtime, split, and scorer settings to drift.

**Consequence.** Do not recreate copied legacy packages or a global renderer.
Any portability or fairness-sensitive adapter advances the protocol and hash
chain.

---

## DD-52: Keep RQ2 staged and preserve its independent sample design

**Date:** 2026-08-05  
**Status:** adopted for static preparation; inference remains locked

**Decision.** RQ2 begins only after RQ1 is finalized. It first studies a
controlled equal-fact factorial over dashboard encoding and arrangement,
separates unequal-content experiments, and delays downstream RCA until the
design mechanisms are understood.

Use 60 exposed cases for development, the unopened former RQ1b2 gate roster
for a disjoint 150-case independent gate, and 90 cases selected from the
unopened former RQ1b3 gate roster for the downstream lock. Retain the remaining
60 as an unopened buffer. Do not edit or execute the historical RQ1 roster
files under their old roles.

**Reason.** The outside-roster pool was too small for the planned balanced
gate, whereas the reassigned rosters were frozen, disjoint, and never exposed
to model outcomes. Reassignment preserves power without opening reserve,
heldout, or RE2-TT.

**Consequence.** RQ2 inference requires its own current roster lineage,
renderer/fact parity audit, prompt, analysis contract, bounded smoke, and a
separate authorization decision.

---

## DD-91: Freeze the current Nibi runtime, context capacity, and case concurrency

**Date:** 2026-08-15
**Status:** adopted

**Context.** Under the 32,768-token predecessor, full-roster Gemma tokenization
produced 30 deterministic `input + 8192 > 32768` infrastructure errors in
`legacy_q9` T/H while Qwen fit the same evidence. Completed Gemma answers used
at most 375 output tokens; the failure occurred before inference and was not a
model outcome.

**Decision.** Use the unified Nibi vLLM contract with unquantized BF16,
40,960-token context, the model-specific Qwen/Gemma processor recipes, no
CanvasRCA VRAM-fraction argument, and scheduler capacity
`max_num_seqs=128`. RQ1 requests keep the uniform 8,192-token context-safe
output adapter; the global 16,384-token ceiling is also unchanged. Prompts,
evidence, schemas, arms, sampling, scoring, and checkpoints remain unchanged.

The user explicitly retains every hash-valid predecessor result whose recorded
request fit and terminated within 32,768 tokens and waives a replacement smoke.
Retained records keep their predecessor runtime freeze; new calls use the
40,960-token freeze. An explicit compatibility manifest validates and joins
the two freezes. Old-context infrastructure errors are rerun from the beginning
and never counted as model outcomes.

Both registered models use xgrammar structured decoding with arbitrary JSON
whitespace disabled. Qwen previously inherited vLLM's `auto` backend and
`disable_any_whitespace=false`; its typed Stage-2 smoke then emitted 3,690
whitespace tokens after a 28-token answer prefix until the phase timeout.
Compact JSON removes only schema-irrelevant whitespace choices and is applied
uniformly to Qwen and Gemma; prompts, schemas, semantic values, sampling
temperature/top-p, and scoring remain unchanged.

The formal RQ1 runner processes at most four different cases concurrently.
Within a case, registered arm order and Stage-1-to-Stage-2 dependencies remain
serial. Each concurrent case has one asynchronous writer. Servers use
task-local ports and record effective configuration and queue/running depth. A
single job and every registered smoke remain one-model and sequential; DD-86
separately permits independent Qwen and Gemma formal jobs from the same active
experiment to overlap during model-tail scheduling.

Transient NVML accounting reads may be retried without repeating model
inference; an unresolvable accounting record remains an infrastructure error.
CPU preparation requests 00:30:00 and 100 GiB. One non-array job uses at most
four case-preparation processes, checkpoints each completed case atomically,
and resumes from hash-matched artifacts. One smoke preparation is shared by
all seven experiment result IDs. One formal preparation writes the exact 24
deterministic `__shard-xxxx-of-xxxx` roots that GPU arrays consume; it is not a
Slurm array and never rerenders a case once per experiment. The frozen
469-case roster remains split into 24 deterministic inference shards,
approximately one third the size of the predecessor eight-shard deployment.
Formal inference wall times and scheduler-window composition are governed by
DD-86. Both registered duration wrappers reserve cleanup time before Slurm's
hard cutoff and retry the same experiment ID against content-addressed targets,
so only missing, invalid, or incomplete case/arm targets run again. Job-timeout
resumption is explicitly distinct from model outcomes: hash-valid length
termination, truncation, and parse failure remain terminal results. An existing
infrastructure error, integrity/hash failure, or unknown status blocks
automatic timeout retry for diagnosis rather than being misclassified as the
timeout cursor.

**Evidence.** In one paired case, identical T evidence encoded to 20,191 Qwen
tokens but 25,482 Gemma tokens; H encoded to 22,202 and 26,564 tokens. Across
the first three Gemma shards, failing prompts ranged from 25,374 to 28,466
tokens. With the unchanged 8,192 allowance, the largest observed request needs
36,658 tokens and fits the authorized 40,960 limit.

**Alternatives rejected.** Evidence compression would change model-visible
facts. A case-specific output budget would create case-dependent compute.
Lowering the uniform output ceiling would alter a frozen generation condition.
Discarding affected cases would turn a deterministic infrastructure defect into
exclusions.

**Consequences.** Four concurrent cases use vLLM batching without the host pressure
of eight. Scheduler capacity is not generated load. Task-local ports prevent
cross-job server collisions, and the uniform output adapter prevents
case-specific compute drift. The installed vLLM/xgrammar sources confirm that
the prior default allowed unlimited whitespace between JSON elements; the
Qwen timeout artifact reproduced that failure directly.

The successor requires new effective-config hashes and live attestation.
Preparation bytes are reused through a hash-audited refreeze because inference
capacity does not affect rendering. The user-authorized compatibility manifest
prevents unnecessary repetition of completed model calls. GPU utilization is
operational evidence, not a scientific validity metric.

---

## DD-83: Use fixed public-bound selectors for typed Q&A

**Date:** 2026-08-10  
**Status:** adopted; current typed interface is v22

**Decision.** `typed_two_stage` keeps fixed step slots for every case-eligible
query in the supplied public contract. Each slot
selects one visible public record key (`M1`, `L:<entity>`, `R:<entity>`,
`G:<entity>`, or `G:<caller>-><callee>`) plus an optional visible field. A
label-blind binder copies only matching public records and preserves an
unsupported slot without guessing. Verified absence of an incident edge is an
explicit public fact. M/L/R→G questions require directed neighbor traversal,
and Level 3 always traverses three distinct regions.
`entity_id` is the only canonical selector name for a record's visible numeric
identity. The label-blind binder reads it from the public fact envelope;
arbitrary aliases and invalid record keys remain unsupported.

Question eligibility is frozen before inference from renderer-visible facts.
Every case has one Level-1 question; Level-2 and Level-3 are included only when
the case exposes a real dependent two-region or strict three-distinct-region
chain. Missing levels are absent from that case's schema and score denominator,
never fabricated or scored as model errors. A 469-packet no-call audit found
316 cases with Levels 1/2/3, 132 with Levels 1/2, and 21 with Level 1 only.

Qwen and Gemma receive the same scientific prompt, evidence, questions,
Stage-2 contract, and scorer. Do not add model-specific prompt repairs.

**Reason.** Query/step membership is orchestration metadata and should not
consume model memory. Public binding separates perception errors from copied-
value hallucination and prevents a nullable grammar shortcut.

**Consequence.** This mechanism is a Q&A/handoff diagnostic, not an RCA result.
Any syntax or binder change requires a forward protocol and new qualification.

---

## DD-85: Freeze the RQ1 renderer, representations, and prompt semantics

**Date:** 2026-08-11
**Status:** adopted; Q&A representation correction current in v22

**Decision.** RQ1 owns the only provisional renderer at
`RQs/RQ1/src/renderer/`: the restored renderer-v12 snapshot. There is no
project-global renderer. Later RQs must copy or explicitly inherit this exact
snapshot unless the user authorizes an RQ-local dashboard-design experiment.

The RCA representation family is:

- `T`: complete natural-language evidence;
- `F`: the same facts as stable flat JSONL;
- `V`: the real renderer-v12 telemetry dashboard;
- `P`: the T natural-language evidence rendered as M/R/L/G pixel pages;
- `H`: strict image-first A+B, where A is exactly V and B is byte-identical T;
- `R`: metrics/topology visual with logs/traces textual, exact-once by fact.

The formal Q&A family is `T_QA` (pure renderer-visible evidence text), `P_QA`
(that exact text rendered as pixels), `V_QA` (the real renderer-v12 dashboard),
and strict image-first `H_QA=V_QA+T_QA`. Q&A factorial visual cells use only
deterministic renderer-v12 M/R/L/G source crops; the full-dashboard `V_QA`
remains separate. The former Controlled M/L/R/G text canvas is archived as a
synthetic spatial-formatting diagnostic and cannot support a real-dashboard
efficacy claim. Level 4–6 is recorded as absent from the synced implementation;
the 4/6/4 counts refer only to Level-1/2/3 templates.

Q&A preparation preserves every inherited RCA renderer artifact byte-for-byte.
When renderer-v12 creates a service-level topology alias that was absent from
the inherited entity map, the Q&A render deterministically assigns that alias
an unused three-digit service ID before compiling its common evidence index.
An explicitly empty directed-edge key is serialized as the visible fact
`status=none`; it does not make a frozen case ineligible.

Every comparison requires equal model-visible atomic facts, precision, bins, missingness,
candidates, concrete edges, and legends. Text-bearing evidence is ordered
M/metrics, R/traces, L/logs, then G/topology. RCA prompts explain field
semantics and origin-versus-symptom reasoning and use the SIRCL-inspired
internal `INITIAL -> VERIFY -> REVISE` check while emitting only the frozen
top-five JSON. Q&A prompts explain fields but contain no RCA guide.

The structured Q&A grammar uses ordered `prefixItems` to bind every answer to
the supplied public query contract: exactly nine answers for `legacy_q9` and
the exact one-to-three case-eligible questions for cross-region packets, with
the exact query ID, step count, step number, region, and (for typed Stage 2)
value kind at each position.
The host independently validates the same contract. A generic answer count or
generic one-to-three-step item grammar is forbidden: both previously allowed a
schema-valid response that the host then rejected, confounding a model outcome
with an orchestration mismatch.

The v22 Q&A evidence index excludes high-precision raw metric arrays that the
dashboard does not print. It compiles each curve into its 64
observed/missing plot-point pixel coordinates, visible y-axis tick labels,
printed baseline/peak/deviation, and displayed fault-band coordinates from the
same renderer-v12 axes. The acceptance audit verifies this display contract,
T=P source-byte equality, H=V+T hashes, crops, printed table cells, and directed
edges. A common upstream source alone never sets an equality flag.

**Reason.** The exact-text `P_QA` is the only valid pixel-transport control.
The old Controlled canvas independently reformatted and rearranged evidence,
so treating it as either `P_QA` or a real dashboard confounded the RQ1 claim.
A global mutable renderer or representation-specific prompt would add another
confound.

**Qualification evidence.** Predecessor v17 artifacts remain diagnostic only.
V22 requires a new zero-call matrix and fresh bounded dual-model smoke for the
two Q&A experiments whose runtime request schema changed (`cross_region` and
`typed_two_stage`). The other five experiments reuse their already-inspected
v21 logical smokes because their prompts, evidence, schemas, scoring, and model
paths are unchanged. Formal submission still requires the shared 469-case
preparation, visual inspection, verifier, and content-addressed freeze.

**Consequence.** Renderer, serializer, prompt, or evidence changes require a
new protocol, parity/leakage audit, visual inspection, hashes, and result IDs.

---

## DD-86: Run the final seven-experiment RQ1 program

**Date:** 2026-08-15
**Status:** adopted; whole-experiment split-site final results pending

**Decision.** RQ1 contains exactly seven experiments:

1. `legacy_q9` — direct M/R/L/G reading;
2. `cross_region` — Level-1/2/3 joins;
3. `typed_two_stage` — extraction and handoff behavior;
4. `direct_rca` — natural one-call RCA reference;
5. `matched_rca` — equal-fact T/F/V/P/H/R two-stage RCA;
6. `visual_counterfactual_rca` — factual/targeted/placebo/neutral visual
   influence;
7. `ledger_handoff_rca` — text/visual/hybrid encoding of one normalized ledger.

Run both registered models on all 469 eligible frozen cases: 96 AegisLab, 100
AIOPS-2022, 93 AIOPS-2025, 90 RE2-OB, and 90 RE2-TT. Do not replace the eleven
already-invalid cases. Headline inference uses only the 289 AegisLab/AIOPS
cases; report RE2-OB and final-OOD RE2-TT separately. `matched_rca`,
`direct_rca`, and `ledger_handoff_rca` are whole-experiment local heldouts,
each covering all 24 shards and both registered models; Nibi submits none of
these experiments. The other four experiments remain Nibi-owned. The
`matched_rca` return must preserve the
exact frozen contract and content-addressed checkpoints described in
`tmp/RQ1_HELDOUT_matched_rca.md`. The complete local `direct_rca` deployment
and return contract is recorded in `tmp/RQ1_HELDOUT_direct_rca.md`. The
ledger-handoff deployment, checkpoint-transfer, and return contract is recorded
in `tmp/RQ1_HELDOUT_ledger_handoff_rca.md`.

The paired `direct_rca` versus `matched_rca` analysis is descriptive rather
than a strict causal stage-count ablation because the latter also adds
selection, binding, compression, and a second decoding opportunity.

Formal execution is strictly experiment-major at each site. Nibi completes and
verifies all 24 shards for both registered models of one experiment before
activating another Nibi experiment. Cross-experiment tail fill is not allowed.
Local and Nibi may process different whole experiments concurrently, but
neither site may split an experiment with the other. Within the one active Nibi
experiment, Qwen has submission priority. When fewer eligible Qwen units remain
than the twelve scheduler positions, Gemma units from that same experiment fill
the unused positions in independent one-model jobs. The same shard is not run
for both models concurrently because its verifier and operational metadata
share one result root.

Submit formal work through twelve scheduler positions, all requesting
`00:30:00`; no new eight-hour formal jobs are submitted. Count only `RUNNING`,
`PENDING`, and `COMPLETING` jobs; completed jobs do not consume a position.
Keep twelve thirty-minute jobs active whenever enough eligible work from the
active experiment remains. Refill unfinished or safely resumable Qwen units
first and use Gemma units from the same experiment for the remaining positions.
The wrapper interrupts its scientific
payload after 25 minutes and reserves up to two minutes for process cleanup and
artifact-writer drain before its Slurm cutoff. A registered timeout retries the
same Nibi unit from its hash-valid completed case/arm artifacts; the interrupted call starts again
rather than splicing a partial response. Hash-valid model truncation/parse
outcomes stay terminal, while infrastructure, integrity, or unknown-status
errors require diagnosis before automatic retry. Preparation, smoke, static
tests, gates, and merge jobs do not consume the formal window. Each job loads
exactly one model and requests one H100. Same-experiment model tail filling
changes scheduling only; it does not change prompts, evidence, schemas,
sampling, scoring, content-addressed keys, or result validity.

The transition canceled four unstarted eight-hour jobs—19827718, 19827719,
19827720, and 19833959—after confirming `PENDING`, zero elapsed time, and no
model call. Replacement thirty-minute jobs 19846079--19846083 reuse the same
content-addressed artifacts. This changes scheduling and interruption cadence
only; it does not change the scientific runtime freezes or any completed model
outcome.

The later clarification makes `visual_counterfactual_rca` the active whole
experiment through both model families. Its Qwen work retained submission
priority over Gemma before any new `legacy_q9` submission. Legacy-Q9 jobs that
were already submitted remain untouched and their compatible results are
preserved, but opened positions are not refilled with legacy-Q9 work. This
transition exception does not reinstate cross-experiment tail filling.

The `visual_counterfactual_rca` non-timeout failure in job 19772049 was a
control-flow defect: protocol-ineligible cases reached targeted/placebo image
lookup before their registered no-call exclusion. Its corrected Nibi execution
uses the dedicated v23 runtime freeze. Existing eligible completed calls may be
migrated only after exact prompt, representation, schema, arm-order, record-
hash and attention-artifact equivalence checks; obsolete partial-case no-call
markers are not migrated. This operational recovery does not change eligible
model requests or rerun compatible completed calls.

**Reason.** Perception scores cannot substitute for RCA, output influence
cannot substitute for accuracy, and handoff loss must be separated from
upstream visual reading.

**Alternatives rejected.** Leaving scheduler positions idle until every Qwen
shard finished was unnecessarily rigid once only six Qwen units remained for
`legacy_q9`. Cross-experiment filling remains rejected because it would split
execution attention across experiments and complicate local/Nibi ownership.
Continuing `ledger_handoff_rca` on Nibi was rejected after the user reassigned
the complete experiment to local execution; Nibi job 19772050 remains a
transferable frozen checkpoint rather than permission for more Nibi shards.

**Consequence.** RQ1 is not complete until all seven experiments across both
execution sites, both models, artifact verification, paired analysis, and
findings are complete. Historical local or predecessor-protocol results remain
diagnostic only. A full 24-shard Nibi array must not be submitted as one pending
block; Nibi formal launch and monitoring maintain twelve thirty-minute jobs and
submit no new eight-hour formal job. One experiment's two verified model result
sets must finish before the next experiment is activated.

---

## DD-87: Collect visual diagnostics during the original prefill

**Date:** 2026-08-10  
**Status:** adopted

**Decision.** Every successful visual request records model-internal
Q-to-visual-K attention from the registered first full-attention layer after
multimodal fusion during that request's original prefill. Persist the raw token
vector, request/layer metadata, 16x16 grid, image/hash-matched heatmap, and
region diagnostics. Text-only calls record non-applicability.

The hook adds no model call, replay, pruning, changed tensor, changed logit, or
scientific arm. Renderer density and Stage-1 region selection remain separate,
call-free diagnostics.

**Reason.** A replay would double execution and would not describe the exact
generation path. Attention is useful for interpretation but is correlational.

**Consequence.** Attention cannot tune prompts, renderers, cases, stopping, or
efficacy conclusions. `visual_counterfactual_rca`, not attention, remains the
causal visual-influence test.

---

## DD-88: Use one bounded, inspectable smoke per experiment

**Date:** 2026-08-11  
**Status:** superseded by DD-97 for future smokes; historical statuses unchanged

**Decision.** Every registered experiment has exactly one logical smoke formed
from exactly two non-array Slurm jobs: one Qwen job and one Gemma job. A job
loads exactly one model. Schedule all Qwen phases before any Gemma phase so the
two model families never overlap. Each model independently receives at most 18
calls and a 600-second phase timeout. Do not combine experiments into an
omnibus smoke, shard either model phase, or split a model phase to reset its
budget. A model-calling gate has at most 36 aggregate calls and 1,200 seconds.

Every smoke request streams the unchanged registered generation and atomically
checkpoints accumulated text. At timeout, terminate outstanding work, preserve
completed artifacts, and mark unfinished text `timeout_partial`. A timeout-only
phase passes when no other error occurred. Correctness, MRR, parse success, and
grounding quality are diagnostics rather than smoke passage criteria.

After every smoke, inspect the summary, verifier, prompts, full conversations,
raw and partial responses, truncation, accounting, and hidden issues. Fix a
safe hidden issue under a forward protocol; preserve material unresolved issues
as blockers.

A smoke qualifies the same shared compiler, renderer, prompts, schemas, model
client, persistence, scorer, and runner behavior used by its corresponding
full experiment. When a smoke exposes a defect in any shared path, repair that
shared implementation rather than adding a smoke-only workaround. Advance the
affected runtime/protocol contract, regenerate any preparation whose freeze or
artifacts changed, and rerun the affected logical smoke before submitting its
full experiment. A purely external launch precondition may be corrected
without regenerating preparation only when the recorded freeze remains exactly
unchanged and the failed attempt made no model call.

Every shared ledger-handoff Stage-1 record and every downstream handoff record
must carry the effective runtime-freeze hash, representation hash, and
content-addressed call key. The verifier accepts an explicit shared preparation
ID for smoke roots and validates those artifacts against that authority; it
must not silently skip verification because preparation lives in a different
result root.

Before any preparation, smoke, gate, or formal submission, inventory existing
jobs and artifacts. Reuse compatible completed artifacts and resume incomplete
content-addressed units. Rerun a completed unit only after recording concrete
evidence that it is missing, corrupt, invalid, or incompatible with a
load-bearing contract change, and rerun only the smallest affected scope. A
pure operational optimization that preserves evidence, prompts, schemas,
inference, and scoring does not invalidate completed preparation or smoke.

**Reason.** Earlier diagnostics spent hundreds of calls or discarded useful
unfinished output. Static exhaustive arm compilation plus bounded live path
coverage is sufficient for infrastructure qualification.

**Consequence.** Partial responses are never parsed or scored as complete
answers. A passed smoke is qualification evidence only, never efficacy. A
failed smoke blocks the corresponding full experiment until its shared-path
cause is repaired and requalified; the full path is never kept artificially
frozen merely to avoid invalidating preparation. Completed work is not repeated
for convenience, scheduler bookkeeping, or operational-only optimization.

---

## DD-90: Use visible record keys for two-stage RCA selection

**Date:** 2026-08-11  
**Status:** adopted as `rq1_record_key_stage1_v16`; implemented but unqualified

**Decision.** RCA Stage 1 returns `CompactRecordKeyLedgerV4` with at most 16
selectors. Each selector contains only a nonempty `record_key` and
`relative_bins`, capped at four. The shared key grammar is:

- `M1` for a visible metric panel;
- `L:<entity>` for a log row;
- `R:<entity>` for a trace row;
- `G:<entity>` for a propagation row;
- `G:<caller>-><callee>` for a directed edge;
- `L:missing` or `R:missing` for explicit absence.

Nonmetric bins must be empty. The model does not transcribe facts or emit
nullable identity tuples, candidate-support lists, opaque fact IDs, values,
attributes, units, or relation arrays. The label-blind host builds a unique
index over public facts, rejects duplicate or unknown keys, copies exact public
values for one match, and derives topology/onset relations only from selected
facts. Harmless panel-zero-padding, whitespace, and arrow typography may be
canonicalized without guessing an unmentioned record.

**Reason.** V15 fixed excessive 5k–8k-token telemetry transcription but its
nullable identity schema and adjacent `supports/opposes` fields produced poor
binding in both models. Gemma grounded V=0/16, R=5/16, T=10/16; Qwen grounded
V=2/14, R=0/7, T=6/8. Its panel pattern also required two digits while the
dashboard visibly uses `M1` through `M12`.

**Consequence.** This changes only Stage 1 of `matched_rca`,
`visual_counterfactual_rca`, and `ledger_handoff_rca`. Renderer-v12,
T/F/V/P/H/R evidence, strict H=A+B, Stage 2, scorer, Q&A, attention, data, and
vLLM remain unchanged. V16 has not been tested per user instruction; Nibi must
run static checks and fresh bounded dual-model smokes before any heavy RCA run.

---

## DD-92: Replace the active Qwen endpoint with Qwen3.8-27B

**Date:** 2026-08-17
**Status:** adopted; supersedes Qwen3.6 as the active Qwen endpoint

**Decision.** Use the official unquantized BF16 `Qwen/Qwen3.8-27B` checkpoint
at revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` as model key
`qwen3.8-27b`. Keep the existing scientific RQ1 prompts, renderer,
representations, arm order, Stage-1/Stage-2 contracts, schemas, scorer,
40,960-token context, 8,192-token RQ1 output request, temperature 1.0, top-p
0.95, and seed 42 unchanged. Explicitly set both `enable_thinking=false` and
`preserve_thinking=false`; retain native Qwen image processing and disabled
chunked prefill.

Run all seven registered RQ1 experiments locally on the frozen 469-case roster
under a new Qwen3.8 result lineage. Reuse the existing model-independent
prepared packets without re-preparation. The user explicitly waives replacement
smoke for this successor and authorizes direct full execution. A hashed
preparation-only compatibility manifest may bridge the old preparation freeze
to the new runtime freeze, but it returns only the new freeze as eligible for
completed targets. It must never make a Qwen3.6 trajectory resumable as a
Qwen3.8 trajectory.

**Evidence.** The official repository is public, ungated, has no
`quantization_config`, identifies `Qwen3_5ForConditionalGeneration`/
`qwen3_5`, stores text weights as BF16, and retains image token ID 248056. It
therefore follows the already pinned Qwen3.5-family vLLM and same-pass attention
paths. The official model card states that thinking and preserved thinking are
enabled by default, so both must be explicitly disabled to retain the registered
non-thinking protocol.

**Reason.** The user selected the newly released stronger checkpoint and wants
the complete RQ1 matrix measured on it. Preparation is independent of model
weights, while generated outputs are not; separating those two facts avoids
both unnecessary CPU work and invalid reuse of predecessor answers.

**Consequence.** Historical Qwen3.6 results remain in their current directories,
retain the `qwen3.6-27b` label and their prior validity scope, and are never
overwritten or reclassified. New Qwen3.8 artifacts use distinct experiment IDs
and `qwen3.8-27b` model directories. The waiver is specific to this transition
and is not a general exception for future model replacements.

---

## DD-93: Resume Qwen3.8 counterfactual RCA after the eligibility-order fix

**Date:** 2026-08-20
**Status:** adopted; operational correctness fix only

**Decision.** In `visual_counterfactual_rca`, evaluate the frozen label-blind
counterfactual eligibility flag before resolving a targeted or placebo image.
For an ineligible case, write one hash-valid `protocol_ineligible` terminal
record per registered arm with zero model calls. Resume the existing Qwen3.8
lineage by call key, retaining predecessor-freeze completed records through a
signed, versioned compatibility manifest.

**Evidence and reason.** Preparation is internally consistent: 430 of 469
cases contain all four registered counterfactual variants, while 39 cases are
intentionally ineligible and contain only the neutral control. The runner had
attempted to load the deliberately absent targeted/placebo PNG before checking
that flag, causing `missing counterfactual image 'placebo'`. A separate shell
cleanup defect referenced an unset local server PID after the primary error.

**Consequence.** The fix changes neither eligible-case evidence nor any
model-visible prompt, image, renderer, scorer, sampling parameter, or output.
The 48 completed Qwen3.8 records remain valid and resumable. Ineligible cases
consume no inference calls and are excluded by the pre-existing registered
whole-case analysis rule. The cleanup now guards the server PID. The resumed
run uses a new runtime freeze while accepting only the explicitly named prior
Qwen3.8 result freeze; Qwen3.6 records remain ineligible for reuse.

---

## DD-94: Treat runtime-freeze hashes as audit metadata rather than validity gates

**Date:** 2026-08-20
**Status:** adopted; supersedes the freeze-matching and compatibility-manifest
requirements in DD-91, DD-92, and DD-93

**Context.** The Nibi `typed_two_stage` Gemma run has 6,053 completed records
and 428 infrastructure-error records already materialized locally. Resuming on
the workstation exposed that a whole-runtime source-tree hash can change even
when the model-visible evidence, prompt, model checkpoint, request parameters,
and scorer needed by a target remain unchanged. Treating that aggregate hash
as a hard gate would unnecessarily repeat completed model calls.

**Decision.** Runtime-freeze hashes remain recorded for audit and provenance,
but matching them is no longer a validity, comparability, preparation-reuse, or
resume requirement. A prior target is reusable when its record hash and call
key are self-consistent, its model/experiment/arm identity matches its result
path, and its status is `completed`. Existing Nibi completed records retain
their validity. Infrastructure errors, corrupt records, aborted calls, missing
targets, and model-identity mismatches are not reusable and must run again.

**Evidence.** The downloaded Gemma lineage contains 6,481 JSON records:
6,053 completed outcomes and 428 infrastructure errors. The completed records
carry self-consistent content-addressed call keys and record hashes. The user
explicitly authorized removal of the runtime-freeze gate and preservation of
these completed outcomes.

**Alternatives rejected.** Requiring a newly signed compatibility manifest for
every source-tree hash transition was rejected because it turns broad
provenance metadata into an unrelated experimental gate. Reusing every file
that merely exists was also rejected because it would incorrectly retain
infrastructure failures or corrupt artifacts.

**Consequences.** Resume code ignores runtime-freeze equality while retaining
the freeze value in every record. Model checkpoints and model-specific result
directories remain strict boundaries; this decision does not allow Qwen3.6
outputs to satisfy Qwen3.8 targets. Prompt, renderer, evidence, scoring, and
sampling changes still require distinct experiment/version decisions even
though freeze equality itself is not enforced.

---

## DD-95: Establish RQ1.1 as the single-preparation representation successor

**Date:** 2026-08-26
**Status:** adopted; RQ1.1 remains unfrozen until its bounded live smokes pass

**Decision.** Preserve the latest RQ1 formal shards, local heldout outcomes,
result analysis, and `docs/RQ1_report.md` byte-for-byte as historical audit
evidence. Build `RQs/RQ1_1/` from a verified byte-identical copy of the current
RQ1 code, then limit the active successor to one Nibi public/private
preparation path, one inherited renderer-v12 snapshot, Qwen3.8 and Gemma, and
three experiments: `direct_qa`, `direct_rca`, and a fixed three-step
ReAct-like `multi_stage_rca`. The RCA representation arms are T, V, S, LV, MV,
TCV, and TPV; the JSONL, hybrid-duplication, and predecessor two-stage ledger
arms are not part of RQ1.1. Attention collection is removed from active runs.

Every model-visible service, pod, and node name is replaced by a deterministic
case-local numeric ID (three, five, and four digits respectively). Each case
uses a new mapping, while its text, images, tools, candidate set, and private
scorer mapping remain internally one-to-one. Operation names, metric names,
and normalized log templates remain visible unless they themselves contain an
entity name, in which case only that entity substring is anonymized.

RQ1.1 adopts ReAct only as a method/prompt reference and adopts Denum's numeric
token/template separation as `DenumReadableLogGraphV1`; neither third-party
repository is a runtime dependency. Logs remain directly readable text/graph
data, retain typed diagnostic numbers and multiplicity, and never use a binary
round trip. All seven representation arms derive from the same atomic fact
inventory, and S is a lossless pixel rendering of T's incident fragment.

**Evidence and reason.** The prior RQ1 corpus mixed preparation lineages and
accumulated overlapping experimental paths. The user requested a clean
successor without rewriting the newest results. Initial RQ1→RQ1.1 copy
manifests are identical; the inherited renderer trees are source-equivalent
after normalizing the required `RQs.RQ1`→`RQs.RQ1_1` package-import rewrite; and
the serialized non-attention inference projection is identical before and
after active attention removal. Static checks cover the 4/12/24/24 ordered QA
template pools, seven-arm fact equality, anonymization/leakage boundaries,
four deterministic public tools, readable-log semantic round-trip, and the
unchanged model-specific Qwen3.8/Gemma recipes.

**Consequences.** Old RQ1 results keep their existing interpretation and are
never promoted as RQ1.1 outcomes. RQ1.1 preparation and inference records use
new result IDs under `RQs/RQ1_1/results/`; historical prepared inputs and model
answers are not resumed. Formal execution stays disabled until each of the
three experiments passes its bounded, shared-budget two-model smoke and completed outputs
are manually inspected. Later SFT/post-training may reuse the anonymization
contract, but no training is authorized by this decision. RQ2 and later work
may inherit the exact RQ1.1 renderer snapshot but cannot edit it silently.

---

## DD-96: Use explicit Nibi and local deployment profiles for one inference recipe

**Date:** 2026-08-26
**Status:** adopted; both profiles remain part of the unfrozen RQ1.1 successor

**Context.** RQ1.1 will switch between Nibi H100 execution and the local WSL
workstation. Nibi must not impose a project VRAM fraction, while local inference
must reserve capacity by setting `gpu_memory_utilization=0.65`. Inferring a
configuration from the hostname or maintaining two experiment implementations
would recreate the ambiguity that RQ1.1 is intended to remove.

**Decision.** Keep one unified loader, client, runner, prompts and scientific
inference recipe with two explicit YAML deployment profiles. Nibi uses
`configs/vllm_inference.yaml`; local WSL uses
`configs/vllm_inference_local.yaml`, selected only through
`CANVASRCA_VLLM_CONFIG`. The local profile points to the inference environment
and Qwen3.8/Gemma checkpoints under `/home/lglsj/CanvasRCA/` and sets
`gpu_memory_utilization=0.65`. Nibi retains relative cluster paths and a null
VRAM fraction, so its launcher omits the flag. Run contracts hash and name the
profile actually used.

**Evidence.** The Nibi and local source hashes at adoption are respectively
`f3609c325a8b9a3a88d63783302dd8d2b604980a4cedfad904dae4760b384877`
and `5af1b30f28aa3c3e22042838555c38e7bafe070cb6b84528793bb87ff11ae4ac`.
The static parity test normalized only `deployment`, model paths and
`gpu_memory_utilization` and found every remaining field equal. Generated Qwen
argv omitted `--gpu-memory-utilization` on Nibi and emitted
`--gpu-memory-utilization 0.65` locally. Both local checkpoint `config.json`
files, the local inference Python and the local vLLM executable exist.

**Alternatives rejected.** Hostname-based auto-selection was rejected because
it is implicit and difficult to audit. Copying RQ code or prompts into a local
adapter was rejected because it can create scientific drift. Adding a 0.65 cap
to Nibi was rejected because the user requires the H100 profile to retain its
existing uncapped operational configuration.

**Consequences.** Deployment location and VRAM fraction are recorded
operational metadata, not representation variables. Any profile difference
beyond deployment paths and the VRAM fraction fails static qualification and
requires a new decision. Local artifacts must identify local execution and may
not be represented as Nibi jobs; scientific comparisons remain governed by the
same prompts, evidence, model-specific processors, decoding and scorer.
Local WSL launches the shared runner directly and never invokes `sbatch` or
contains Slurm account, array, dependency, or submission logic. Those controls
belong exclusively to the Nibi entry points.

---

## DD-97: Restore one shared 18-call and 600-second budget per two-model smoke

**Date:** 2026-08-26
**Status:** adopted; supersedes the per-model smoke budgets in DD-88 and the
initial RQ1.1 implementation notes

**Decision.** One experiment has one logical smoke covering Qwen3.8 and Gemma.
The two models run sequentially and share at most 18 initiated LLM/VLM calls
and one 600-second wall-clock timeout measured from the smoke supervisor start,
including both model startups, switching, inference, persistence, and
verification. A smoke may not be split to reset either bound.

**Reason.** Smoke is an infrastructure and artifact-path qualification, not an
efficacy experiment. The shared limit prevents two-model startup and broad arm
coverage from consuming more time than the formal work it is meant to protect.
Statically equivalent request paths remain covered by CPU tests; the bounded
live sample exercises both models and the distinct schemas/state transitions
that fit within the shared budget.

**Consequence.** `direct_qa` uses eight calls across both models and
`direct_rca` uses fourteen. `multi_stage_rca` assigns one complete three-step V
trajectory to each model and uses the remaining six calls for selected
first-step paths, for exactly eighteen calls total. A timeout-only result still
passes; any non-timeout infrastructure, integrity, persistence, numerical, or
protocol error prevents passage. Historical smoke results retain their prior
status and are not rerun solely because the future budget changed.

---

## DD-98: Make the RQ1.1 candidate list the complete label-blind entity universe

**Date:** 2026-08-27
**Status:** adopted; supersedes the candidate-source detail in DD-95 without
changing its anonymization, representation, renderer, or inference decisions

**Context.** The first local RQ1.1 `direct_rca` diagnostic batch showed that
AIOPS-2022's inherited renderer-manifest `services` field contained pods and
nodes but omitted service identities that were legitimately visible in
metrics, traces, logs, topology, and tool outputs. Calling that subset
"exhaustive" made a visible service ID illegal to rank and made service-level
evidence impossible to connect directly to a valid service candidate.

**Decision.** Generate the ordered candidate set from the complete label-blind
entity universe already used for case-local anonymization: every eligible
service, pod, node, telemetry entity, graph node, and deployment identity.
Require every model-visible fact entity to be a member of that set before any
model call. Tool rows remain derived from the same mapping and are audited for
the same coverage. Keep all IDs case-local and evaluator mapping private.

**Evidence.** The stopped diagnostic produced 164 records, of which 27 were
rejected for an unknown case-local ID; all 27 occurred on AIOPS-2022 and each
contained at least one model-visible service ID omitted from the 45–46 item
legacy candidate subset. In `aiops2022_2022-03-20-cloudbed2_009`, the repaired
label-blind universe contained 85 candidates, covered all 85 fact identities
and all 63 tool-returnable identities, and contained the private evaluator's
accepted root service after the public input had already been compiled. The
seven-arm inventory remained unique and equal, `S=T` remained true, renderer
version remained 13, and static hash
`6f4c07b25fe7b1d2d8a04b2832444ea6fbda65a521ac2f4cd95635fd2c6814d7`
passed.

**Alternatives rejected.** Silently dropping unknown IDs would discard part of
a model ranking and change scoring semantics. Publishing natural service-to-pod
names would weaken case-local anonymization. Retaining the legacy subset would
make valid observable entities impossible outputs on one dataset. Using the
private root label to add a candidate was rejected as label-dependent input
construction.

**Consequences.** The stopped v1 diagnostic and its preparation are invalid for
performance or modality claims and remain audit-only. All 469 cases are
regenerated under a new v2 contract and result ID. No renderer, prompt,
sampling, checkpoint, model processor, tool permission, or scorer change is
authorized by this decision. The formal queue retains the order
`direct_rca` → `direct_qa` → `multi_stage_rca`, completing Qwen3.8 and then
Gemma inside each experiment.

---

## DD-99: Measure image and text attention without a directional RQ1 objective

**Date:** 2026-08-27
**Status:** adopted; supersedes only the attention-removal clause in DD-95 and
extends DD-87 from visual-only keys to all prior prompt keys

**Context.** Historical RQ1 same-prefill overlays established where visual
attention was allocated, but they could not compare image attention with text
evidence or explain correctness. The user clarified that RQ1 is no longer
intended to prove that images are useful and requested a neutral mechanism
measurement over both modalities.

**Decision.** Restart RQ1.1 under an attention-enabled successor protocol.
Every request records the final prompt query's attention to all prior prompt
keys at the first registered full-attention layer. Persist raw prompt-token
weights and semantic text-span aggregates for all arms; visual arms also store
image grids and overlays. Attention collection occurs in the original prefill,
adds no model call, and does not modify generation. Interpret it only as a
correlational diagnostic. RQ1.1 compares representation effects on RCA,
cross-region reasoning, tool use, attention, and cost without a preferred sign.

**Evidence.** The historical report contains complete same-prefill visual
diagnostics for 73,936 requests. It shows 62.4–66.8% of full-dashboard visual
attention on metrics and 27.7–30.8% on topology, but correct and incorrect
attention distributions are almost indistinguishable. This demonstrates both
the diagnostic value and the causal limitation of raw attention. A raw audit
of the report's representative case found that the first row of the old 16×16
visual grid held 41.1% of Qwen3.6's visual-conditional mass, 41.4% of Qwen3.8's,
and 27.3% of Gemma's. The concentration is therefore present in the captured
visual weights, but the old plot exaggerates its apparent absolute importance:
it softmax-normalized over visual keys only, scaled opacity by each image's own
maximum, and spatially expanded a coarse grid. The new protocol reports an
explicit first-grid-row `dashboard_header_band`, the top-left cell, and their
absolute all-prompt mass separately from M/R/L/G. The band is deliberately
described as grid-resolution, not as a pixel-exact title segmentation. It also
stores per-patch value norms and pre-output-projection attention-weighted value
norms, first-patch rank, and peak-to-median ratios. These diagnostics distinguish
a high-weight/low-contribution sink candidate from a token carrying a large
value contribution, but they do not authorize a sink claim without subsequent
content and position interventions.

**Alternatives rejected.** Visual-only attention cannot test whether a model
substitutes text for pixels. A second forward replay would not describe the
exact generation path and would double compute. Treating attention as proof of
visual benefit is unsupported by the historical correctness comparison.

**Consequences.** The interrupted attention-free RQ1.1 run and all RQ1.1 result
artifacts were deleted at the user's direction; protected historical RQ1
results and `docs/RQ1_report.md` remain unchanged. Preparation is regenerated
from the same canonical inputs because it was stored inside the deleted result
root, not because attention changes evidence. New smokes must verify both
models, text-only and visual attention artifacts, raw vectors, span mapping,
image overlays, hashes, and unchanged model inference fields before the formal
queue restarts.

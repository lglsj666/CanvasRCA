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
| DD-54, DD-64, DD-68, DD-69, DD-70, DD-74, DD-76 runtime clause, DD-77 | DD-78 — Nibi runtime and concurrency |
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

## DD-78: Freeze the current Nibi runtime and case concurrency

**Date:** 2026-08-12
**Status:** adopted

**Decision.** Use the unified Nibi vLLM contract with unquantized BF16,
32,768-token context, the model-specific Qwen/Gemma processor recipes, no
CanvasRCA VRAM-fraction argument, and scheduler capacity
`max_num_seqs=128`. RQ1 requests keep the uniform 8,192-token context-safe
output adapter.

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
task-local ports, record effective configuration and queue/running depth, and
never run Qwen and Gemma concurrently for a registered sequential workflow.

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

**Reason.** Four concurrent cases use vLLM batching without the host pressure
of eight. Scheduler capacity is not generated load. Task-local ports prevent
cross-job server collisions, and the uniform output adapter prevents
case-specific compute drift. The installed vLLM/xgrammar sources confirm that
the prior default allowed unlimited whitespace between JSON elements; the
Qwen timeout artifact reproduced that failure directly.

**Consequence.** Runtime changes require new effective-config hashes,
attestation, preparation, result IDs, and bounded qualification. GPU utilization
is operational evidence, not a scientific validity metric.

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

**Date:** 2026-08-14
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
cases; report RE2-OB and final-OOD RE2-TT separately. `matched_rca` and
`direct_rca` are whole-experiment local heldouts, each covering all 24 shards
and both sequential models; Nibi submits none of either experiment. The other
five experiments remain Nibi-owned. The `matched_rca` return must preserve the
exact frozen contract and content-addressed checkpoints described in
`tmp/RQ1_HELDOUT_matched_rca.md`. The completed Nibi `direct_rca` Qwen shard 0
was explicitly invalidated and deleted at the user's direction, so the local
`direct_rca` run starts from scratch. Its local deployment guide remains
intentionally unwritten until the user finishes synchronizing the code and
requests it.

The paired `direct_rca` versus `matched_rca` analysis is descriptive rather
than a strict causal stage-count ablation because the latter also adds
selection, binding, compression, and a second decoding opportunity.

Formal execution is experiment-major at each site. Nibi activates one formal
experiment at a time, finishes and verifies all 24 Qwen shards, then finishes
and verifies all 24 Gemma shards, and only then activates the next Nibi
experiment. All Nibi `RUNNING`, `PENDING`, and `COMPLETING` formal jobs must
belong to that one active experiment; never interleave a few shards from
several experiments. Local and Nibi may process different whole experiments
concurrently, but neither site may split an experiment with the other.

Within the active Nibi experiment, submit formal work through twelve scheduler
positions split into independent duration lanes: eight `08:00:00` jobs and
four `00:30:00` jobs. Count
`RUNNING`, `PENDING`, and `COMPLETING` jobs. Refill an eight-hour position only
with an eight-hour job and a thirty-minute position only with a thirty-minute
job, keeping 8+4 active whenever enough eligible work from that experiment
remains. The eight-hour
wrapper interrupts its scientific payload after 7 hours 55 minutes, and the
thirty-minute wrapper interrupts after 25 minutes; each reserves up to two
minutes for process cleanup and artifact-writer drain before its Slurm cutoff.
A registered timeout retries the same Nibi unit within its duration lane from its
hash-valid completed case/arm artifacts; the interrupted call starts again
rather than splicing a partial response. Hash-valid model truncation/parse
outcomes stay terminal, while infrastructure, integrity, or unknown-status
errors require diagnosis before automatic retry. Preparation, smoke, static
tests, gates, and merge jobs do not consume the formal window. Within each
experiment, Qwen must finish before Gemma starts; the two model families never
overlap for that experiment.

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

**Consequence.** RQ1 is not complete until all seven experiments across both
execution sites, both models, artifact verification, paired analysis, and
findings are complete. Historical local or predecessor-protocol results remain
diagnostic only. A full 24-shard Nibi array must not be submitted as one pending
block; Nibi formal launch and monitoring maintain the eight-eight-hour plus
four-thirty-minute mixed window for only the current experiment. Partial
progress in one experiment never justifies switching Nibi to another; a switch
requires complete two-model verification of the current experiment.

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
**Status:** adopted

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

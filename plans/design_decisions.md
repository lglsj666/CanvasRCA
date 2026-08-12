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
CPU preparation requests 00:30:00 and 100 GiB. All preparations for a launch
batch run serially inside one non-array CPU job; each preparation covers its
complete roster and is never divided into Slurm shards. Full GPU inference
requests 07:59:00 and 100 GiB per task; the frozen 469-case roster remains
split into 24 deterministic, resumable inference shards, approximately one
third the size of the predecessor eight-shard deployment. Many same-model
inference shards may be queued at once, subject to the array concurrency cap.
The complete Gemma array waits for the complete Qwen array through an `afterok`
dependency, so the two models never run concurrently.

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
**Status:** adopted; current typed interface is v10

**Decision.** `typed_two_stage` keeps fixed q1/q2/q3 step slots. The model
selects public entity, edge, panel, and bin identifiers; a label-blind binder
copies exact displayed values and preserves unsupported steps rather than
invalidating the whole ledger. Required identifiers are non-null according to
the public question template. Entity IDs are three-to-five digits, edge IDs
use `E##`, and metric panels use the visible bounded panel syntax. Verified
absence of an incident edge is represented explicitly rather than treated as
an unbound hallucination.

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
**Status:** adopted; Q&A representation correction current in v17

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

Every comparison requires equal atomic facts, precision, bins, missingness,
candidates, concrete edges, and legends. Text-bearing evidence is ordered
M/metrics, R/traces, L/logs, then G/topology. RCA prompts explain field
semantics and origin-versus-symptom reasoning and use the SIRCL-inspired
internal `INITIAL -> VERIFY -> REVISE` check while emitting only the frozen
top-five JSON. Q&A prompts explain fields but contain no RCA guide.

**Reason.** The exact-text `P_QA` is the only valid pixel-transport control.
The old Controlled canvas independently reformatted and rearranged evidence,
so treating it as either `P_QA` or a real dashboard confounded the RQ1 claim.
A global mutable renderer or representation-specific prompt would add another
confound.

**Qualification evidence.** Zero-call static job `19558580` passed. CPU
preparation job `19558566` completed three cross-dataset cases in 53 seconds
with 100 GiB and passed the artifact verifier. For all three cases,
`H_QA.image_sha256 == V_QA.image_sha256`,
`H_QA.text_sha256 == P_QA.source_text_sha256 == T_QA.text_sha256`, the crop
source hash equals the full renderer-v12 image hash, and the controlled canvas
is absent from formal arms. Visual inspection also fixed and requalified the
G/L boundary so the complete propagation legend belongs only to G and the log
table begins cleanly in L.

**Consequence.** Renderer, serializer, prompt, or evidence changes require a
new protocol, parity/leakage audit, visual inspection, hashes, and result IDs.

---

## DD-86: Run the final seven-experiment RQ1 program

**Date:** 2026-08-10  
**Status:** adopted; final Nibi results pending

**Decision.** RQ1 contains exactly seven experiments:

1. `legacy_q9` — direct M/R/L/G reading;
2. `cross_region` — Level-1/2/3 joins;
3. `typed_two_stage` — extraction and handoff behavior;
4. `direct_rca` — natural one-call RCA reference;
5. `matched_rca` — equal-fact T/F/V/P/H/R two-stage RCA;
6. `visual_counterfactual_rca` — factual/targeted/placebo/neutral visual
   influence;
7. `ledger_handoff_rca` — text/visual/hybrid encoding of one normalized ledger.

Run both registered models on all 469 eligible frozen cases under new Nibi
result IDs: 96 AegisLab, 100 AIOPS-2022, 93 AIOPS-2025, 90 RE2-OB, and 90
RE2-TT. Do not replace the eleven already-invalid cases. Headline inference
uses only the 289 AegisLab/AIOPS cases; report RE2-OB and final-OOD RE2-TT
separately.

The paired `direct_rca` versus `matched_rca` analysis is descriptive rather
than a strict causal stage-count ablation because the latter also adds
selection, binding, compression, and a second decoding opportunity.

**Reason.** Perception scores cannot substitute for RCA, output influence
cannot substitute for accuracy, and handoff loss must be separated from
upstream visual reading.

**Consequence.** RQ1 is not complete until all seven experiments, both models,
artifact verification, paired analysis, and findings are complete. Historical
local or predecessor-protocol results remain diagnostic only.

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

**Reason.** Earlier diagnostics spent hundreds of calls or discarded useful
unfinished output. Static exhaustive arm compilation plus bounded live path
coverage is sufficient for infrastructure qualification.

**Consequence.** Partial responses are never parsed or scored as complete
answers. A passed smoke is qualification evidence only, never efficacy.

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

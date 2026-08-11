# RQ1 Experiments

RQ1 has seven registered experiments implemented by the compact engine in
`RQs/RQ1/src/`. They reuse the unified inference, segmentation, and RCA-scoring
contracts in `configs/`. Every experiment is rerun on Nibi under a new result
ID; historical local results remain context rather than final evidence.

## Semantic-restoration authority

The current successor is `rq1_record_key_stage1_v16`. It retains the v15
compact-output objective, v14 same-prefill attention runtime, v13
seven-experiment registry, v12
SIRCL-adapted Stage-2 prompt, renderer-v12 and all representation facts, while
replacing only the RCA two-stage evidence-transfer protocol. The first
Nibi refactor shortened load-bearing prompts and replaced parts of the old
controlled evidence/task compiler with approximate summaries. Any Nibi model
trajectory produced by that predecessor implementation is archived diagnostic
evidence and is invalid for scientific claims. DD-84 subsequently superseded
the v17 renderer choice: the authorized dashboard is now the old repository's
renderer-v12 implementation, relocated into `RQs/RQ1/src/renderer/` with only
package-import changes and verified by byte-identical real-case renders.
The v12 prompt amendment retains that renderer and evidence packet while
partially superseding v11's inherited serializer *ordering*: model-visible text
now follows the locked SIRCL* sequence M/metrics → R/traces → L/logs →
G/topology. No fact, precision, bin, candidate, or edge changes with the order.

At the 2026-08-11 handoff, the v16 code and contract edits were complete but
deliberately not tested at the user's request. Nibi must run the static suite
and each affected experiment's bounded dual-model smoke before any heavy run.

The restored contract requires all of the following before a replacement run:

- public/private physical separation and a fail-closed leakage audit;
- case-local numeric identities in every M/L/R/G representation, including
  entity mentions inside normalized log templates;
- one controlled 16-bin fact packet shared by text, visual, factorial, and
  strict image-first A+B arms;
- four Level-1, six Level-2, and four Level-3 templates whose later lookup
  scope depends on the preceding region result;
- trace edge IDs in R without endpoints, with caller/callee resolution only in
  G, so `R→G` is a real cross-region join rather than an answer in the prompt;
- complete visible-fact equality for RCA T/F/V/P/H/R arms, a typed Stage-1
  binder, and Stage 2 access only to the normalized ledger;
- `CompactRecordKeyLedgerV4`: at most 16 unique public-record keys, at most four
  selected metric bins per metric key, no nullable identity tuple,
  candidate-support list, model-transcribed value, attribute, unit or relation
  array, and deterministic host binding to exact public facts before Stage 2;
- one visible key grammar shared by every representation: `M1`, `L:<entity>`,
  `R:<entity>`, `G:<entity>`, `G:<caller>-><callee>`, `L:missing`, or
  `R:missing`; preparation fails on a duplicate public key;
- inheritance of the old T natural-language and F flat-JSONL field semantics,
  intentionally reordered M/R/L/G under v12; P renders the exact current T
  fact lines as M/R/L/G pixel pages without creating a new summary or consuming F;
- RCA text/flat records contain no panel metadata absent from the image;
  controlled-QA-only onset and persistence values remain confined to the
  controlled canvas where they are explicitly printed;
- case-balanced arm order, paired whole-case exclusion, headline inference on
  AegisLab/AIOPS-2022/AIOPS-2025 only, and separate RE2-OB/RE2-TT reporting;
- label-blind counterfactual eligibility with a hard failure on no-op swaps,
  plus lossless multi-page visual-ledger handoff and shared Stage-1 accounting.

The CPU suite proves that all 14 reasoning templates are reachable and that
strict A+B, exact-once routed transport, scorer semantics, pagination, resume
keys, and model-specific unified inference arguments hold. A local legacy-data
reader may be enabled only through the explicit environment adapter described
in `Codex.md`; it changes paths/schema access, not scientific facts.

## Prompt and modality-order authority

SIRCL's repository contains no aggregate result table, but it explicitly locks
`SIRCL_STAR` as `MET-Z`, `TRC-L`, `LOG-R`, sequence
`MET → TRC → LOG`, `U-BASE`, and `VERIFY`. RQ1 adopts only the transferable
prompt principles: M/R/L evidence order with topology last, explicit field
semantics, origin-versus-symptom guidance, and the
`INITIAL → VERIFY → REVISE` check. It does not claim that CanvasRCA implements
SIRCL's analyzers or single-call architecture.

All representation arms receive one byte-identical system/task guide. RCA
prompts explain M/R/L/G fields, relative time, missingness, caller/callee
semantics, the RCA objective, and how to distinguish an origin from propagated
symptoms. Stage 2 also explains the normalized ledger and internally tests
exactly two evidence-answerable questions about its preliminary top-1 before
revising. Only the frozen top-five JSON is emitted. Q&A/VisOps prompts explain
the same data fields but deliberately omit the RCA method and VERIFY guide.

T, F, P, Q&A text fragments, and region-bearing Stage-2 ledger rows use
M → R → L → G. The real and controlled visual renderers retain their frozen
spatial layouts; a prompt-order amendment is not a dashboard-layout experiment.
H remains strictly image-first `A+B`: its image bytes equal V and its incident
text bytes equal T, with no hybrid-only prompt instruction.

Source provenance for the adopted reasoning/order is:

- `SIRCL-for-RCL/src/prompts/design.py` SHA-256
  `ebe137b8c930d14e921d08d3eca458c896396c283a23b2581074f2639a6277fc`;
- `SIRCL-for-RCL/src/prompts/scaffolds/verify.py` SHA-256
  `968fcfc7840fa70fd1c192ffdf48e385e8c37d65e284ce4ef3edff31b1dac2a6`;
- `SIRCL-for-RCL/README.md` SHA-256
  `3d83d85c195752465c9249396661b41cd2c7715a5545e8c8b298a5f27d67d0f5`.

## Final evaluation roster

Use all 469 eligible cases from the long-frozen project evaluation roster:

| Dataset | Eligible cases | Reporting role |
|---|---:|---|
| AegisLab | 96 | primary |
| AIOPS-2022 | 100 | primary |
| AIOPS-2025 | 93 | primary |
| RE2-OB | 90 | separate saturated-domain slice |
| RE2-TT | 90 | separate final OOD slice |

The eleven cases carrying the existing invalid status are excluded without
replacement. The headline inferential set is the 289 primary cases. RE2-OB and
RE2-TT are reported separately and never pooled into the headline effect.
Every model and arm uses the same case roster and paired exclusion policy.

## Nibi qualification and execution order

Every experiment uses the first frozen eligible case from RE2-OB, AIOPS-2022,
and AIOPS-2025 in roster order for its one registered smoke. The Qwen phase runs
first; only after it exits does the Gemma phase start. Each model phase has an
independent ceiling of 18 calls and 600 seconds, including server readiness,
requests, persistence, and verification. The CPU-only matrix compiles all
56 arms, while the live plans use these per-model call counts:

| Experiment | Calls/model |
|---|---:|
| `legacy_q9` | 9 |
| `cross_region` | 3 |
| `typed_two_stage` | 6 |
| `direct_rca` | 3 |
| `matched_rca` | 6 |
| `visual_counterfactual_rca` | 8 |
| `ledger_handoff_rca` | 6 |

No predecessor smoke or runtime freeze authorizes the restored code. All seven
full experiments remain mandatory after new infrastructure qualification.
A scientific gate or analysis threshold that is not met is reported as a
negative outcome and is non-stopping. A rejection caused by a protocol
mismatch, implementation defect, persistence failure, or unexpected
infrastructure error must be repaired and rerun before progression. This rule
does not alter any registered threshold or recode a negative result as a pass.

The final replacement execution uses the named, versioned
`context_safe_output_v1` RQ1 inference adapter. The global 16,384-token output
ceiling remains unchanged, but every actual RQ1 request in both models, every
arm, and both stages requests at most 8,192 output tokens. Before each call,
the live server tokenizer must confirm that input tokens plus 8,192 do not
exceed the frozen 32,768-token context. The adapter changes no evidence,
prompt wording, arm, schema, decoding distribution, or scoring rule; it is a
uniform feasibility correction after the earlier 16,384-token request made
three complete long-text prompts impossible to submit. Its content and hash
are stored in the runtime freeze and every completed stage record.

The global `max_num_seqs=128` amendment changes only vLLM scheduling capacity.
The 16,384-token global ceiling and 8,192-token RQ1 request adapter are
unchanged from the restored protocol.

The formal runner consumes the frozen `request_concurrency=4` contract at case
granularity. Up to four different cases may issue requests at once;
all arms and both stages within one case remain sequential in their registered
order. Worker residue partitions are disjoint and resumable, and the runner
performs a call-free consolidation scan after every worker drains.

Each registered experiment has exactly one independent logical smoke. Its
Qwen and Gemma each receive up to 18 calls and a separate 600-second phase
timeout within the smoke. The two model phases run sequentially, never in
parallel. Budgets are not pooled across experiments, and several
experiments must not be disguised as one omnibus smoke. A CPU-only exhaustive matrix separately
compiles every registered arm/cell and both effective model contracts. Each
experiment's live smoke therefore spends calls on its distinct request paths,
response schemas, and representative representation types rather than trying
to call every statically equivalent factorial cell.

Smoke transport streams the otherwise unchanged response and atomically
checkpoints accumulated text under `partial_responses/`. If the phase reaches
its wall-clock bound, the supervisor preserves and marks unfinished text as
`timeout_partial` for failure analysis. This adds no request and supplies no
score; formal experiment transport and all scientific settings remain
unchanged.

## `legacy_q9`

Nine direct operations test whether the model can read individual metric, log,
trace, and topology facts. T/V/H provide text-only, image-only, and strict
image-first A+B inputs. Exact-match accuracy is perception evidence, not RCA
accuracy. The nine operations are exact metric-bin lookup, exact log-bin
lookup, exact trace-bin lookup, earliest onset, longest persistence, directed
edge lookup, explicit multi-hop path, cross-region entity alignment, and
metric missingness. They are not replaced by panel-owner or row-count proxy
questions.

## `cross_region`

Level-1 direct reads, level-2 two-region joins, and level-3 three-region joins
test composition across M/L/R/G. Sixteen text-versus-visual factorial cells
plus strict A+B localize representation effects. Short question identifiers
only associate outputs with questions; complete-chain and step accuracy score
the reasoning result. The exact template registry is 4/6/4: M/L/R/G direct;
M↔L, M↔R, M↔G, L↔R, L↔G, R↔G; and M→L→R, M→G→L,
M→R→G, L→R→G. Every first-region anchor is unique at displayed precision;
later lookup scope is determined by the preceding answer. Template selection
is deterministic among the templates eligible for that case, because a case
with no trace or no qualifying graph join cannot support every family.

## `typed_two_stage`

The cross-region packets run through a host-bound typed ledger before the
answer stage. The public question contract fixes q1/q2/q3, the exact number of
steps, and each M/L/R/G path. Stage 1 selects only a visible entity or edge,
panel/row, field, and relative bins in those fixed slots. A deterministic
label-blind binder then copies the exact displayed values and units from the
same public packet. Unsupported selectors remain explicit step records rather
than invalidating all three questions. Stage 2 receives the question contracts
plus this normalized ledger and returns typed step values. This measures
extraction, grounding, and handoff attrition without testing memory for opaque
IDs or raw-sequence transcription. It is an agent-mechanism experiment rather
than an RCA endpoint.

## `direct_rca`

This is the natural one-stage RCA reference requested after the Q&A
single-stage/two-stage distinction became useful. For every case it uses the
same six T/F/V/P/H/R representations, common evidence shell, candidate order,
field/RCA guide, internal SIRCL-style VERIFY procedure, diagnosis schema,
private ID mapping, and granularity-aware scorer as the current RCA family.
The model reads the original representation and directly emits the frozen
top-five RCA JSON in one call; no ledger, binder, or second call is involved.

Its main outputs are per-arm MRR, AC@1/3/5, AVG@3/5, parse/truncation rates,
tokens, calls, GPU time, and wall time. After both experiments finish, the
`compare-stages` analysis pairs `direct_rca` and `matched_rca` by model, case,
dataset, and arm and reports `two-stage minus one-stage` performance and cost.
This comparison is deliberately descriptive: the two-stage condition also
introduces evidence selection, deterministic binding, ledger compression, and
a second output opportunity, so a difference cannot be attributed solely to
the integer number of stages.

## `matched_rca`

This end-to-end RCA experiment compares six equal-source arms: complete text
`T`, stable flat JSONL `F`, the real renderer-v12 telemetry dashboard `V`, a
pixel-text pseudo-dashboard `P`, strict image-first `H=A+B`, and routed `R`
with metrics/topology visual and logs/traces textual. `P` deterministically
draws the T natural-language incident-evidence semantics in M/R/L/G image pages; it
does not contain telemetry plots and must never be called the real dashboard.
T/P/V share one atomic fact inventory, displayed precision, bins,
missingness, candidates, concrete edges, and legends. `V-P` tests whether the
actual visual encodings outperform merely moving natural-language evidence
into pixels; `P-T` isolates the effect of pixel transport without dashboard design.
Stage 1 selects at most 16 diagnostically strongest records without copying
telemetry arrays. The label-blind host binds each selector to one public fact,
copies its scalar fields and at most four selected metric-bin values, and
derives edge/onset relations only from selected topology facts. Stage 2 sees
only that compact normalized ledger and the common candidate/task shell and
returns ranked top-five RCA JSON.
Paired `R-T` and `R-F` MRR comparisons are primary; AC@1/3/5 and AVG@3/5 are
secondary. `V-T`, `P-T`, and `V-P` are registered secondary comparisons and
cannot replace the primary routed-arm claims.

## `visual_counterfactual_rca`

This experiment tests whether image semantics causally move the final RCA
ranking rather than merely changing prose. Starting from the strict hybrid,
keep its text, candidates, prompt, layout, and compute fixed while comparing:

- the factual image;
- a label-blind targeted transplant that swaps complete visual identities of a
  high-evidence and low-evidence entity;
- a matched placebo transplant between similarly weak entities; and
- a neutral sham that preserves the canvas and visual budget but removes
  incident evidence.

The intervention selector uses only frozen model-blind telemetry/graph
statistics and never root labels. All swap endpoints are RCA candidates of the
same entity granularity. Primary mechanism outcomes are the target-minus-
placebo directional rank shift, top-1/top-5 changes, finite RBO@5 distance, and
semantic ledger-fact changes. Factual RCA MRR remains separately reported;
output sensitivity alone is not an accuracy benefit.

## `ledger_handoff_rca`

This experiment isolates whether a useful observation survives the
Stage-1-to-Stage-2 boundary. From one compact, grounded Stage-1 selector set, compile
three semantically identical handoffs: normalized typed text, a lossless
pixel rendering of the same canonical JSON ledger, and strict image-first
pixel-ledger-plus-byte-identical-text. The visual cell is deliberately an OCR/
pixel-transport control, not a claim that the JSON has become a semantic graph
diagram. Stage 2
uses the same candidates, task shell, decoding budget, and top-five schema in
all cells and cannot reopen the original evidence. Compare transfer/grounding,
unsupported claims, ranking disagreement, and final MRR. This distinguishes an
upstream perception failure from a lossy textual handoff and tests whether a
visual intermediate representation adds value after evidence extraction.

## Related-work boundary

CodeShrink ([arXiv:2607.29637](https://arxiv.org/abs/2607.29637)) is a 2026
preprint about code-image compression, not an RCA method. CanvasRCA transfers
only its diagnostic definition: at the first registered full-attention layer
after multimodal fusion, score visual keys from the final prompt query,
softmax across visual tokens per head, then average heads. A project-owned
vLLM 0.24 hook performs this calculation from Q/K tensors already produced by
the normal prefill. It neither repeats the forward nor adds a model call, and
it does not prune tokens, KV state, evidence, or canvas content.

Every visual request in all seven experiments writes the raw token vector,
request/layer metadata, a hash-matched 16×16 image-space grid, and a heatmap;
text-only requests explicitly record non-applicability. The existing
model-call-free renderer atlas (blank/evidence density and M/L/R/G coverage)
and Stage-1 region-selection statistics remain distinct diagnostics. Attention
is correlational rather than causal and cannot select cases or change an RCA/
Q&A score. The visual-counterfactual experiment remains the causal test.
Fixed-fact blank-space compaction remains deferred to RQ2.

Heavy execution, bounded qualification, and artifact verification occur on
Nibi. The WSL preparation does not produce scientific model results.

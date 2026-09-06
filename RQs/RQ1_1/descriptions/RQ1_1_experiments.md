# RQ1.1 experiments

## Shared contract

The two primary successor experiments and the registered counterfactual
successor target all 480 identities in the frozen manifest after canonical V3
regeneration,
private labels only at evaluation, the renderer-v14 snapshot, case-local
numeric service/node/pod identities, the unified scorer and VLM client, and the
unchanged Qwen3.8/Gemma inference recipes. M/R/L/G mean metrics, traces, logs,
and directed topology. Every visual call contains at most one PNG.

Except for H's intentional duplicate encoding, compared representations expose
the same atomic facts, values, precision, bins, missingness, candidates,
legends, and concrete edges exactly once. S is an exact pixel rendering of the
T incident fragment. Denum-inspired logs remain directly readable text/graph;
no binary payload is model-visible.

`direct_rca` additionally adopts the locked best design declared by the
supplied SIRCL artifact: `MET-Z + TRC-L + LOG-R`, evidence order
metrics→traces→logs→topology, `U-BASE`, and `VERIFY`. The unmodified reference
files and per-file hashes live under `packages/SIRCL_selected_reference/`.
CanvasRCA's active one-call prompt is a constrained adaptation: numeric
case-local IDs and the frozen JSON-only output replace SIRCL's natural
identifiers/free prose. U-BASE is implemented in its source-defined position:
background, task, and output instructions occur at the start of the user
message, before incident evidence. VERIFY becomes an internal
INITIAL→VERIFY→REVISE check because the frozen endpoint cannot emit SIRCL's
free-prose sections.

Renderer-v14 and the natural-language serializer compute the selected
analyzers rather than merely relabeling predecessor facts. A trace-derived,
label-blind relative split replaces SIRCL's private `case.timestamp`; when no
trace onset is usable, the public telemetry window and then the observation
midpoint are deterministic fallbacks. MET-Z prints pre/current mean and
standard deviation for every selected metric. TRC-L ranks operations by the
positive log2 fold changes of call count and exclusive-latency p95, after
subtracting child-span duration. LOG-R compares per-service error-keyword and
log-volume rates across the identical split while retaining readable Denum
templates and diagnostic numeric variables. The same derived fields are
serialized in text and drawn in visual arms, preserving cross-arm fact
equality. Topology remains the project-required fourth region after SIRCL's
M→R→L sequence.
The shared incident serializer itself uses a neutral `canonical order` heading,
so non-RCA QA never receives the SIRCL name or any RCA-specific instruction.
The supplied paper reports SIRCL* at macro MRR 0.596, A@1 0.545, and A@3
0.660 on its four held-out test sets with Qwen3.5-9B. Those numbers identify
the selected reference configuration; they are not a CanvasRCA target or
qualification threshold. T-arm proximity is an external diagnostic only,
with differences in roster, anonymous identities, checkpoint, candidate
universe, topology input, and scorer stated explicitly. Formal cases may not
be tuned to reproduce the paper.

### Representation-specific prompt decoding

The task shell, evidence semantics, RCA method, candidate/output contract and
sampling remain shared. The shared text is representation-neutral: it never
claims that a dashboard, image, pixel, chart, crop or canvas exists. A pure
text RCA or QA request therefore receives no visual-navigation instruction.

Requests that actually contain the real renderer-v14 dashboard receive a
non-incident-specific decoding addendum. It explains the relative-time header,
anonymous entity digits, M1–M12 curves/MET-Z summaries, shaded fault window,
propagation rows and source suffixes, TRC-L columns, LOG-R/Denum rows, concrete
caller→callee edge key, omission/missingness semantics, and neutral regions in
a mixed arm. The addendum names exactly which M/R/L/G regions are visual and
which are supplied as text. It adds no case value, candidate, edge or label.

S/S_QA receive a different addendum stating that their pixels are only a
lossless screenshot of the T evidence and have no chart or spatial-topology
semantics. H's incident-specific fragments remain strictly the V image A
followed by T's byte-identical evidence B; its visual decoding addendum is task
metadata outside A+B and does not rewrite or deduplicate either fragment.
Direct QA retains the same non-RCA question and field semantics across its
conditions; its common system role is representation-neutral.

## Experiment 1: `direct_rca`

One call returns the frozen top-five RCA JSON. The main design is the complete
`2^4=16` text/visual factorial:

- `T`: M/R/L/G text.
- Single visual region: `MV`, `TCV`, `LV`, `TPV`.
- Two visual regions: `V_MR`, `V_ML`, `V_MG`, `V_RL`, `V_RG`, `V_LG`.
- Three visual regions: `V_MRL`, `V_MRG`, `V_MLG`, `V_RLG`.
- `V`: M/R/L/G all visual in the real dashboard.

Three controls are outside the 16-cell visual factorial:

- `C`: the same complete atomic facts as T serialized as stable, concise typed
  JSON tuples `[region, field, entity_ids, relative_bins, unit, payload]`.
  It is readable structured text, not the retired flat-JSONL arm: it exposes no
  fact IDs, labels, paths, or extra facts. `C−T` measures whether structure and
  reduced prose repetition improve accuracy or token efficiency; `V−C` asks
  whether spatial visual organization adds value beyond nonvisual compression.

- `S`: T's incident evidence, in the same byte order, rendered into one
  pixel-text atlas.
- `H`: complete dashboard A followed by byte-identical T evidence B. H is
  strictly image-first A+B and intentionally repeats facts.

Mixed arms use a fixed-size dashboard canvas. Selected regions are copied
pixel-for-pixel from V; nonselected regions are neutral and their facts appear
as text. Primary RCA outcome is MRR; secondary outcomes include AC@1/3/5,
AVG@3/5, ranking flips/overlap, repair/break, evidence grounding, token cost,
regional conditional main effects, second-order interactions, and Shapley
contributions to MRR, tokens, and infrastructure error.

The common one-call instruction applies SIRCL*'s INITIAL→VERIFY→REVISE
discipline before the final answer. Because the project output contract is a
strict three-field JSON object, the working steps are not emitted; `reason`
contains only the concise strongest verified evidence. This is a prompt
procedure, not a claim that hidden chain-of-thought was recovered.

The model-visible `reason` is deterministically bound to known entity IDs,
metric panels, log templates, directed edges, and public fact IDs. The derived
`ReasoningTraceViewV1` connects visible reason evidence to M/R/L/G and the
top-five ranking. It is a visualization-ready audit of the model's explicit
answer, not a reconstruction of hidden chain-of-thought.

## Experiment 2: `direct_qa`

The current V3 registry separates two difficulty axes that the old L1–L4
protocol conflated:

- **Perception difficulty P1–P4** is exactly the number of distinct evidence
  regions that must be read. P1 has four possible single-region paths, P2 has
  all 12 ordered two-region paths, and P3/P4 have 24 paths each.
- **Reasoning difficulty R1–R3** is the effective public program, not question
  length. R1 performs independent direct lookups; R2 derives an entity from a
  visible anchor and uses it in a dependent sequence; R3 performs a
  deterministic regional argmax and aggregates the regional winners.

This produces at most 12/36/72/72 answerable templates for P1/P2/P3/P4. A
response-blind SHA256 policy requests a reasoning tier and ordered path for
each case/P level, then chooses the closest fully eligible template if sparse
telemetry makes that exact combination impossible. The final prepared-corpus
audit reports the realized P×R×path distribution; it must be reasonably
balanced and any fallback rate must be explicit. All conditions and both
models receive the identical selected question for a given case/P level.

Every question is an executable public-fact program with private expected
steps and supporting fact IDs. Registration rejects a template if any answer
is `missing`, `none`, `nan`, empty, unprinted, or derived from a middle-elided
metric name. It never asks for internal `entry_index` or `edge_index`. Trace
anchors use unique displayed ExL/score pairs; log anchors use unique displayed
LT/bin/level/count tuples; topology anchors use unique visible edge endpoints.
R3 may read a displayed score to choose an entity, but returns the entity ID
rather than a higher-precision hidden number. Thus an ideal reader can recover
every gold step from either the text or the actual canvas.

For P1–P3 the conditions are:

- `T_QA`: all evidence text.
- `V_QA`: complete real dashboard.
- `S_QA`: exact pixel-text screenshot.
- `PathV`: only the regions required by the ordered question path are visual.
- `ContextV`: required regions are text; only irrelevant context regions are
  visual.

For P4, PathV equals V and ContextV equals T, so only T/V/S are run. Outcomes
are complete-chain, step, and correct-prefix accuracy; region/path accuracy;
direction asymmetry; repair/break; unsupported values; and token/attention
cost. PathV−T measures required-region visualization, ContextV−T measures
irrelevant visual noise, V−PathV measures extra visual context, and S−T
separates pixel transport from chart encoding. The arm names retain `L1`–`L4`
only as a backward-compatible transport label; in new artifacts they mean
P1–P4 perception difficulty and never reasoning difficulty.

### Superseded pre-V3 QA protocol (historical audit only)

The following three amendments describe the deleted pre-V3, 469-case result
lineage. They are retained to explain earlier reports but are not an active
question registry, scorer, denominator, or execution authority. V3 replaces
them with the orthogonal P×R registry and fail-closed visibility contract
above.

#### Positive-chain eligibility amendment (2026-08-29)

The prepared corpus revealed that a hash-selected higher-level path can carry
an entity into a region with no displayed supporting row. Such a question can
measure missingness detection, but it is not a positive cross-region evidence
composition task. Existing trajectories remain immutable and are retained for
the all-question audit. The primary perception subset now requires every step
of a selected `case × level` question to have at least one private
`supporting_fact_id`. Eligibility is computed before looking at any model
response and is identical across T/V/S/PathV/ContextV and both models.

The deleted pre-V3 corpus historically contained 469 eligible L1 questions,
135 L2, 53 L3, and 24 L4 under this all-positive-support rule. Those counts are
audit context, not current execution authority. V3 regeneration re-evaluates
eligibility on all 480 frozen identities before any model call. The semantic
scorer must report both all-question and positive-chain results and always
state the retained denominator; conditional positive-chain accuracy must not
be presented as overall 480-case accuracy.

#### Balanced positive-question extension

The frozen questions and their results are never changed or removed. A
successor extension may only add new response-blind, all-positive-support
questions. In the final combined positive-question corpus, every ordered
region path at the same reasoning level must have exactly the same number of
valid questions. Paths are directional: for example, `M->L` and `L->M` are
different L2 paths.

The target is at least 200 valid questions per higher level, rounded upward to
an equal per-path quota. Existing positive questions count toward that quota.
Because the frozen L2 corpus already contains 28 valid `R->G` questions, the
smallest non-destructive balanced L2 corpus has 28 questions for each of the
12 paths: 336 total, requiring 201 additions. L3 uses 9 questions for every
one of its 24 paths: 216 total, requiring 163 additions. Because only 120
distinct cases contain any supported four-region chain under the current
visible evidence, L4 uses the user-approved target of 5 questions for each of
its 24 paths: 120 total, requiring 96 additions. Existing missingness questions
remain in the audit corpus but do not count toward these positive-support
quotas.

New anchors and question instances must be derived only from model-visible
public facts and selected before reading any model response or private RCA
label. Repeated questions from one case do not create independent statistical
units: the balanced L4 assignment has 120 question instances over 109 unique
cases. Analysis reports both denominators and first macro-averages within case
before paired case-level inference. The extension
uses a new result namespace and does not alter or resume into the current
formal result root.

#### Visibility-aware scoring amendment (2026-08-29)

The registered exact score and the first semantic sensitivity score remain
immutable audit views. The final post-hoc perception estimand adds a
response-blind visual-answerability check at the `opaque case + query` level.
The decision is applied identically to both models and every representation
condition before any response is inspected.

A question is excluded from the final summary when a complete answer cannot be
read from the registered visual representation: its required full metric name
was middle-elided by renderer-v14, it selects a TRC-L `entry_index` that is not
printed on the canvas, or another required field is absent. The trajectory is
retained for audit. When old wording identifies an entity but permits several
visible rows, every permitted row is a valid gold answer rather than a reason
to exclude the question.

Retained questions have representation-specific gold precision. T, S and
ContextV use the high-precision values present in their visible text. V and
PathV use values deterministically derived from the renderer-v14 display
contract, such as text `57329.15` versus canvas `57.3k`. Rounding therefore
does not count as missing diagnostic information. The deterministic semantic
matcher additionally accepts only registered presentation equivalences:
numeric notation, missing aliases, direction aliases, set/list formatting,
field prefixes and the frozen terminal-topology marker. No model judge is
used and no model call is rerun.

#### Visibility-clean L4 successor extension (2026-08-29)

The first visibility-aware analysis retains only 24 L4 questions across 16 of
the 24 ordered M/R/L/G paths. A response-blind successor therefore preserves
those 24 questions and adds 72 new instances, producing exactly 96 L4
questions: four for each ordered four-region path. The 96 questions use 96
different cases, so no incident is repeated in the L4 case-level estimand.

Every new question is rejected before inference if any answer step contains
`missing`, `null`, `n/a` or `unavailable`; if a required metric label is
middle-elided by renderer-v14; if a required canvas field is absent; or if the
public wording refers to an internal `entry_index`/`edge_index` or to a
representation-specific row/edge position. Trace anchors instead use a
globally or entity-locally unique combination of displayed baseline/fault
count and baseline ExL values; topology anchors name a concrete displayed
`caller -> callee` edge. These content anchors have the same semantics in the
natural-language and visual representations. The same frozen
manifest is used by Qwen3.8 and Gemma, and the three L4 conditions remain
T/V/S. Existing questions, prompts, trajectories and scores are not changed.

The prepared manifest adds 72 questions, or 216 calls per model and 432 calls
for both models. Preparation and static audits are complete under
`rq1_1_v13_direct_qa_visibility_clean_l4_extension_20260829`. An initial
partial launch using display positions was stopped and excluded before any
analysis after a T/V ordering mismatch was found; the successor manifest was
regenerated with content anchors. The corrected run completed 216/216 records
per model with zero infrastructure errors. The final analysis combines the 72
new cases with the 24 retained cases, giving 96 unique L4 cases and exactly
four cases for every ordered M/R/L/G path.

## Joint perception–RCA analysis

QA and RCA share case, model, packet and renderer. T/V/S map directly; PathV
maps to the factorial cell containing the required visual regions, and ContextV
maps to its complement. `PerceptionProfileV1` records L1–L4 results, regional
step accuracy, prefix performance, relevant/irrelevant attention density,
hallucination status and tokens beside RCA reciprocal rank, top-1 correctness,
evidence grounding and visible reasoning trace.

Analyses include aggregate and change-score Spearman correlations,
`P(RCA@1 | QA correct/incorrect)`, level- and region-specific relations, and
four paired quadrants: perception/RCA both improve, perception improves while
RCA degrades, perception degrades while RCA improves, and both degrade. These
are association and controlled-representation diagnostics, not causal
mediation claims.

## Experiment 3: `one_stage_counterfactual_rca`

This independent, versioned mechanism experiment keeps the one-call RCA
endpoint and the complete RQ1.1 visual dashboard. It has four paired image
conditions:

- `V_FACTUAL`: the correctly matched renderer-v14 dashboard.
- `V_TARGETED`: a label-blind complete identity transplant between the
  highest-scoring and lowest-scoring same-granularity visual-evidence
  candidates. Evidence attached to the donor ID is attributed to the
  recipient ID, and vice versa, across M/R/L/G.
- `V_PLACEBO`: the same operation applied to two weak same-granularity
  candidates matched as closely as possible on visible fact count and graph
  degree.
- `V_NEUTRAL`: the same PNG dimensions and transport with all
  incident-specific evidence removed.

The selector uses only public rendered/serialized facts, never root cause,
fault type, injection time, model output, or RQ2 results. Each case is either
eligible for both targeted and placebo pairs or excluded label-blind before
any call. All arms receive the same RQ1.1 prompt, candidates, output schema,
sampling and scorer; the arm name is not shown to the model. The existing
480-case roster is retained, with its 300 headline cases as the inferential
set and RE2 reported separately.

The primary mechanism quantity is `CVI = VFS_targeted - VFS_placebo`, where
VFS measures reciprocal-rank movement from donor toward recipient after the
identity transplant. It is accompanied by top-1 and top-5 change, `1-RBO@5`,
factual-versus-neutral change, visual benefit/harm, MRR, grounding and
attention. Positive CVI shows directed sensitivity to image semantics; it
does not by itself show factual-image accuracy gain or correct causal-chain
recovery. The registered minimum effect is +0.05 with paired Pratt-Wilcoxon
testing.

This experiment remains `qualification_pending_rq2_completion`. Its code and
tests may be prepared while RQ2 runs, but no test, smoke or model call begins
until RQ2 is complete. It then receives one shared two-model smoke of eight
planned calls (within 18 calls and 600 seconds), artifact verification, and
only after passage a new resumable formal result root.

## Attention and token efficiency

The original call records two attention views at the first registered
full-attention layer without an extra model call:

1. the final prompt query over prior prompt keys;
2. the mean query attention of generated tokens inside the registered
   `services` or `values` answer fields.

Text attention maps to exact semantic spans. Image attention uses the actual
Qwen `image_grid_thw`-equivalent or Gemma post-pooling geometry. Source-token
mass is integrated by exact pixel overlap. The primary regional comparison is

```text
region attention per pixel = region attention mass / region pixel area
region density lift = region attention per pixel /
                      mean attention per pixel across actual visual-evidence regions
```

Header, blank and unassigned pixels are reported separately and excluded from
the M/R/L/G density reference. Raw mass remains only for conservation and for
showing how much total attention a region received. Attention is correlational
and never treated as hidden reasoning or causal proof.

Token reporting includes paired reduction versus T, facts per input token, MRR
per 1,000 input tokens, tokens per accumulated reciprocal rank, tokens per
correct QA chain, regional token main/Shapley effects, and MRR/QA token Pareto
frontiers. Absolute token counts are not compared across model tokenizers;
relative-to-own-T ratios are.

Every request also records client-observed TTFT (time to first streamed content
chunk), receiver end-to-end latency, decode duration, TPOT, output-token rate,
and transport-chunk inter-arrival summaries. Because an HTTP client cannot
separate server queueing from prefill, `prefill_time` is explicitly unavailable
rather than estimated from TTFT; the inter-arrival metric is labelled as a
transport-chunk proxy, not exact per-token ITL. A one-second run monitor records
request throughput/goodput, GPU utilization-weighted seconds, peak VRAM, vLLM
KV-cache high-water mark, and estimated energy from sampled board power.
Preparation records stage and total time, including renderer work. These timing
and hardware measurements are operational: compare them within the same machine
and runtime only, never as hardware-independent evidence that one representation
is scientifically better.

## Inactive future work

`multi_stage_rca` source remains in the repository but is **abandoned for this
paper**. It has no active smoke plan, formal queue entry, summary, or claim.
Multi-stage visual RCA and interactive dashboard use are future work.

## Qualification and execution

Static checks cover arm equality, one-image transport, H=A+B, S=T source,
PathV/ContextV complements, QA↔RCA mapping, anonymization/leakage, processor
geometry, area-integration conservation, answer-token alignment, reasoning
trace binding, persistence and scoring. They also fail if a T/T_QA prompt
contains visual-representation instructions, if a real-dashboard request lacks
the complete decoding grammar, or if S is described as a telemetry dashboard.
Each active experiment has one bounded
two-model smoke: at most 18 aggregate calls and 600 seconds. After both pass and
their conversations are inspected, formal order is `direct_rca` then
`direct_qa`, Qwen3.8 then Gemma within each. Direct RCA contains 18,240 calls
(480 cases × 19 arms × 2 models); Direct QA contains 17,280 calls. The
counterfactual successor contains 3,840 calls (480 × 4 × 2), for an aggregate
RQ1.1 maximum of **39,360 calls**. The 40,000-call ceiling applies to the whole
major RQ1.1, not independently to each subexperiment.

### V3 qualification record

The retained prepared input is `rq1_1_v3_rq480_prepared_balanced_v1`
(480/480 cases; semantic index SHA256
`25dd503cb6900267dc267273ee6f8bb6a572ec0a2bed6ba024a7cbd6f4f8994b`).
The bounded dual-model successor smokes `rq1_1_direct_rca_smoke_v4` and
`rq1_1_direct_qa_smoke_v5_anchor_repair` each completed all 18 registered calls with parse
rate 1.0, zero infrastructure errors, no truncation, and passing post-hoc
verification. Completed conversations, prompts, raw responses,
attention/performance accounting, and persistence were manually inspected.
This qualifies only Direct RCA and Direct QA. Counterfactual RCA remains
deferred until RQ2 is complete, and multi-stage RCA remains abandoned.

Direct-QA R1 questions never refer to a representation-specific first row or
first edge. Trace anchors use a unique displayed ExL-p95/rank-score pair;
topology anchors use a unique displayed callee; fact storage-order reversal is
a static invariance test. The 2026-09-05 repair changed only the small QA
schedule sidecars. Existing Direct-RCA results remain untouched. A predecessor
Direct-QA terminal is retained only if its complete model-visible request and
current private score reproduce exactly; every changed matched group is rerun.

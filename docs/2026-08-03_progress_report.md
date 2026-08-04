# CanvasRCA incremental progress report — 2026-08-03

**Reporting boundary:** this document primarily records work completed after
[`progress_report.md`](progress_report.md). Section 3 also includes a concise
recap of the completed equal-information RQ0 because it is needed as meeting
context and was explicitly requested; the earlier bake-off and renderer/SFT
development history is not repeated in full.

**Meeting status:** RQ1b mapping v2 and its disjoint independent gate are now
complete. Mapping was valid for both architectures and froze the preregistered
Gemma-derived router (`earliest_onset -> H`,
`entity_modality_alignment -> V`, all other operations -> T). The new 90-case
gate is also technically valid, but the router **failed efficacy validation**:
Gemma structural routed-minus-T was −0.0562 (Pratt p=0.0112), and Qwen was
−0.0227 (p=0.3698). DD-27 therefore rejects the router and keeps RQ1b
factorial, RQ1c, RQ1d, training, and heldout RCA blocked.

After that decision, the separately registered DD-28/RQ1b2 mechanism study
completed implementation, every pre-inference qualification, and its 90-case
Gemma development run. The run is technically valid but failed all three
promotion conditions: high-complexity `V-T=-0.3250`, paired complexity
interaction `0.0000`, and only 4 visual repairs versus 30 breaks. DD-29 closes
this mechanism without running Qwen or opening the locked 150-case gate.

DD-30's narrower RQ1b3 two-stage successor repaired a JSON-whitespace defect,
passed its complete 33-call validation smoke, and then completed the full
90-case Gemma development cell. All 990 calls finished with zero infrastructure
failures, truncations, or paired exclusions, but every promotion condition
failed: final H−T was −0.0333, Stage-1 ledger H−T was −0.0028, repairs/breaks
were 10/13, H ledger error was worse than T, and oracle Stage-2 accuracy was
0.8000. DD-34 therefore closes RQ1b3 without Qwen or the locked 150-case gate
and moves the next preregistration target to RQ2 dashboard design effects.

## 1. Executive update

The project has moved from asking whether a static dashboard helps *on average*
to asking which concrete RCA operations benefit from visual, textual, or
combined representation when the underlying facts are identical.

The main progress since the previous report is therefore not another renderer
tuning pilot. It is a new, auditable RQ1b experiment with:

- a project-history-complete exposure ledger;
- disjoint 90-case mapping and 90-case independent-gate rosters;
- nine automatically scored, root-label-blind RCA visual operations;
- exact semantic fact equality across text, image, and hybrid arms;
- a renderer that exposes every model-citable atomic `fact_id`;
- hard leakage, parity, determinism, context-window, smoke, pairing, and GPU
  accounting checks;
- complete Gemma and Qwen mapping runs plus a strict per-operation analysis.

Mapping v1 remains an incomplete diagnostic because Gemma violated its frozen
parse gate. The narrowly controlled v2 repair resolved that integrity problem
without changing any evidence, question, private answer, image, text, or A+B
fragment. V2 did **not** show a useful pooled hybrid-over-text effect:
case-macro H−T was +0.0030 for Gemma and +0.0027 for Qwen, with p=0.580 and
p=0.604. More importantly, its two operation-specific non-text choices did not
generalize on the disjoint gate. The image-only alignment choice reversed
against T on both architectures, while the hybrid earliest-onset choice tied T
for Gemma. The current protocol therefore yields a valid negative result rather
than an infrastructure failure or an inconclusive unrun gate.

The final RQ1b3 development result strengthens that conclusion. Explicitly
separating complete onset extraction from final selection did not produce a
hybrid-over-text advantage. It did reveal two mechanisms worth preserving:
visual ledgers are highly sensitive to row arrangement, and a semantically
set-valued output should not be rejected for natural numeric ordering. Neither
diagnostic rescues efficacy; even an order-insensitive sensitivity analysis
keeps H below T and oracle selection far below its qualification threshold.

## 2. Repository and governance changes

### 2.1 RQ-owned layout

RQ-related material now lives under `RQs/<RQ>/`. Each active RQ owns six
directories:

```text
descriptions/  research questions, protocols, registrations
configs/       RQ-specific frozen configuration and rosters
scripts/       provisional experiment and analysis tooling
results/       generated experiment artifacts
findings/      accepted findings and final summaries
src/           submission-grade final code only
```

`RQs/RQ1/src/` remains intentionally empty and locked. RQ1 is still deciding
the final method; provisional code belongs in `RQs/RQ1/scripts/` and cannot be
promoted to `src/` before the solution is accepted. Project-root `configs/` is
reserved for genuinely unified configuration shared by the mainline and every
RQ.

Legacy RQ directories were separated from active work, and old RQ1/RQ3 bundles
that cannot support current information-equality or leakage guarantees are
being removed from the active evidence tree. This cleanup does not rewrite
history: a valid historical result stays valid, and an invalid result is not
rehabilitated by moving files or changing hashes.

### 2.2 Project rename and shared skills

Active branding and executable paths were normalized to `CanvasRCA` and
`/home/lglsj/CanvasRCA`. The technical Python package name `vlmrca` is retained
because it is an import/distribution and contract identifier, not the old
repository name.

The nine project workflow skills under `.claude/skills/` were updated and made
available to both Claude and Codex from one canonical source. The shared rules
are loaded through `AGENTS.md -> Codex.md`; this avoids separate, drifting
Claude/Codex operating procedures.

### 2.3 Rules strengthened by failed experiments

The following are now project-level invariants:

1. A representation comparison is valid only if every arm receives the same
   model-visible semantic facts. A legend saying “A→B means A calls B” cannot
   replace the incident's concrete edges; summaries cannot replace complete
   queried sequences when the image exposes their shape.
2. For image fragment `A` and text fragment `B`, the hybrid prompt must be the
   literal ordered composition `A+B` (image first), not a rewritten hybrid
   prompt.
3. Raw case IDs, dataset names, fault type, labels, injection/absolute times,
   file paths, and private roster fields cannot enter prompts, PNG/OCR text, or
   public manifests.
4. Audit lineage such as `source_pointer`, provenance hashes, and
   `derived_from` is evaluator-only. Exposing it only in text would itself
   create information inequality.
5. Process-ID equality is not an experiment-validity criterion. Effective
   inference configuration and artifact contracts matter; a redundant PID gate
   was removed without changing any historical experiment status.
6. `gpu_memory_utilization=0.65` is the canonical operational ceiling, but a
   different historical memory ceiling alone neither invalidates nor makes
   incomparable an otherwise matched inference result.
7. Whole-case infrastructure exclusion above 5% makes a cell incomplete.
   Parse failures and output truncations are model outcomes, not infrastructure
   exclusions.

## 3. Completed RQ0 result — meeting context

### 3.1 Question and metric

The completed formal question was:

> **RQ0. Under equal-information and equal-compute conditions, does
> visual-text, topology-aware observability improve VLM-based RCA over
> text-only and flat structured representations?**

RQ0 is a root-cause **ranking** experiment. Its primary metric is **MRR** (mean
reciprocal rank): if an accepted root cause is ranked at position `r`, that
incident receives `1/r`; a root outside the returned top five receives zero;
MRR is the mean over incidents. `AC@1`, `AC@3`, and `AC@5` are the proportions
of incidents whose accepted root appears within the first 1, 3, or 5 ranked
positions. These RCA ranking metrics are different from the atomic-task
`accuracy` used in the new RQ1b mapping (explained in Section 7).

### 3.2 Formal protocol

- 720 incidents: 240 each from AegisLab, AIOPS-2022, and AIOPS-2025;
- three fact-equal arms per incident:
  - A: visual-text topology-aware dashboard plus common evidence text;
  - B: byte-identical common evidence text without the image;
  - C: flat structured JSONL from the same atomic facts;
- 2,160 calls per model, 4,320 calls total;
- Qwen3.6-27B and Gemma-4-26B-A4B-it, unquantized BF16;
- deterministic one-shot inference with 32k context and 16k output ceiling;
- full leakage, fact parity, deterministic-render, pairing, and runtime
  qualification.

#### 3.2.1 Why RQ0 included the flat-structured arm

The intuitive `text-only / image-only / image+text` trio answers a useful but
different question: whether an image can replace text, and whether the two
modalities are complementary. RQ0's primary estimand was narrower: **does
adding a topology-aware dashboard to an already complete text representation
improve RCA, and does the resulting visual-text interface beat a common
non-visual machine-readable representation?** This is why its third arm was
flat structured rather than image-only.

The three RQ0 arms separate two baselines:

- `A versus B` is the clean incremental-image comparison. A is the dashboard
  followed by exactly the same deterministic evidence text used by B. Any
  paired difference is therefore caused by adding the image and its interaction
  with the unchanged text.
- `A versus C` asks whether the complete visual-text, topology-aware interface
  outperforms a flat telemetry-record interface. JSON/JSONL-style records are a
  realistic input to an LLM/agent, so beating only prose text would not establish
  that the proposed interface is better than a direct structured-data baseline.
- `B versus C` is secondary and diagnostic. It estimates the effect of
  natural-language organization versus flat structured serialization without
  an image; it is not one of the two primary RQ0 hypotheses.

Without C, a positive A−B result could support “the image helps this prose
prompt,” but it would not show that the proposed visual-text observability is
better than simply passing the same telemetry as stable structured records.
Conversely, A−C alone cannot prove that the image caused the improvement,
because A differs from C in both image availability and natural-language
organization. That is why RQ0 required **both** A−B and A−C to exceed the
registered practical and statistical thresholds.

The `flat_structured` arm was implemented as follows:

1. It starts from the identical `CanonicalEvidenceBundleV1` used by A and B.
2. It receives the same system task, common RCA instructions, candidate order,
   evidence semantics, decoding configuration, and final top-five JSON schema.
3. It receives no PNG. Its incident evidence is emitted as deterministic JSONL:
   canonical JSON keys are sorted, encoding is compact, and the lines are
   stably sorted by `record_type` and then by canonical record content.
4. The records include the incident/relative fault window and missingness,
   candidates, every selected metric series with the lossless 64-bin compact
   transport, log entries and log metadata, trace entries and trace metadata,
   propagation-service records, propagation metadata, and every concrete
   directed caller-to-callee edge.
5. Metric arrays remain inside their owning `metric_series` record. They are
   not expanded into thousands of scalar JSON-pointer lines, which would make
   serialization overhead rather than evidence dominate the context.
6. It deliberately has no dashboard geometry, visual proximity, arrow layout,
   section narrative, or prose evidence storyline. The semantic facts remain;
   the topology is represented by explicit edge records rather than a drawn
   graph.
7. The representation audit maps all three arms back to the same scalar atomic
   fact inventory and checks the same inventory hash. Thus “flat” means a flat
   **representation**, not reduced or less informative evidence.

Image-only was not a formal RQ0 arm because the registered dashboard was a
redundant visual supplement, not a separately qualified lossless carrier of
every scalar CEB fact. Removing the complete text would have changed both the
modality and the available transport unless a new image-only parity contract
were built. It would also estimate image *sufficiency/replacement*, not the
incremental value of adding an image to text. The current RQ1 mapping now
includes a fully fact-paired visual-only arm for exactly that complementary
question.

#### 3.2.2 RQ0 decision thresholds and their mathematical basis

RQ0 did not define success as merely “A has a larger sample mean.” A model
supported RQ0 only if **all** of the following preregistered conditions held:

| Gate | Frozen threshold | What it protects against |
|---|---:|---|
| Practical effect, A−B | ΔMRR ≥ +0.05 | A statistically detectable but negligible image increment |
| Practical effect, A−C | ΔMRR ≥ +0.05 | Claiming the visual-text interface is useful while it barely differs from structured input |
| Statistical evidence | both Holm-adjusted p < 0.05 | Sampling noise across the two primary comparisons |
| Dataset safety | no primary dataset ΔMRR ≤ −0.05 | A pooled gain that hides a practically important regression on one dataset |
| Parse completeness | every arm parse rate ≥ 0.95 | An apparent modality effect caused by failure to produce the requested output |
| Infrastructure pairing | unpaired infrastructure cases ≤ 1% | A result dominated by post-failure complete-case selection |
| Protocol integrity | parity, leakage, rendering, pairing and runtime checks pass | Confounding by extra information, leaked labels, or changed execution |

The `+0.05` threshold is the **smallest effect of practical interest**, not a
p-value. MRR lies in `[0,1]`, so +0.05 means five additional hundredths of
reciprocal-rank performance—for example, a net change equivalent to moving
roughly 5% of cases from outside the returned ranking to rank 1, although the
same mean can arise from many smaller rank movements. Requiring +0.05 prevents
a large sample from turning a tiny, publication-friendly difference into a
claim of operational value.

The sample size was checked before inference using the paired normal
approximation

```text
MDE ≈ (z_(1−α/2) + z_power) × paired_sd / sqrt(n)
    ≈ (1.96 + 0.84) × paired_sd / sqrt(n)
```

where two-sided `α=0.05`, power is 0.80, and `n=720` paired incidents. The
historical planning SD of approximately 0.38–0.46 implied an MDE near
0.045–0.055 MRR, so +0.05 was both scientifically meaningful and close to what
the design was expected to resolve. This equation is a planning approximation;
the final hypothesis test is paired Wilcoxon because per-case MRR differences
are discrete, zero-heavy, and need not be normally distributed.

The realized paired SDs were smaller, 0.222–0.269, giving approximate achieved
MDEs of 0.023–0.028. That increases sensitivity but does **not** permit lowering
the preregistered practical threshold after seeing the data. Gemma A−C is the
illustrative case: adjusted `p=0.0239` establishes that the observed positive
difference is unlikely to be pure paired sampling noise under the null, but
`ΔMRR=+0.0278` is below +0.05 and therefore not large enough for the registered
claim.

Two primary comparisons create two chances for a false positive. Holm's
step-down correction sorts their raw p-values and compares them to progressively
less stringent cutoffs, controlling the probability of at least one false RQ0
claim—the family-wise error rate—at 0.05 without assuming independent tests.
The separate `−0.05` per-dataset boundary is a robustness rule, not another
hypothesis test: it makes the practical harm tolerance symmetric with the
required practical benefit.

The 0.95 parse floor bounds malformed model outcomes to at most 5% of an arm.
Because both MRR and the RQ1 binary score are bounded by one, a 5% differential
failure mass can itself shift an average by as much as 0.05; beyond that point,
output compliance could be as large as the claimed practical effect. RQ0's
historical 1% infrastructure ceiling retained at least 99% of the 720-case
paired design (at most seven exclusions), making the standard-error inflation
at the boundary only about `sqrt(720/713)−1 ≈ 0.5%`. RQ0 actually had zero
infrastructure exclusions, so this threshold did not affect its result. The
project later standardized future small development cells to a 5% ceiling;
that governance change does not rewrite the completed RQ0 contract or status.

### 3.3 Formal result

| Model | A visual+text MRR | B text MRR | C flat MRR | A−B | A−C |
|---|---:|---:|---:|---:|---:|
| Qwen3.6-27B | 0.3984 | **0.4113** | 0.3954 | −0.0129 | +0.0030 |
| Gemma-4-26B-A4B-it | 0.3901 | **0.4013** | 0.3623 | −0.0112 | +0.0278 |

| Model | Comparison | Holm-adjusted p | Registered decision |
|---|---|---:|---|
| Qwen3.6-27B | A−B | 0.3634 | not supported |
| Qwen3.6-27B | A−C | 0.6420 | not supported |
| Gemma-4-26B-A4B-it | A−B | 0.2480 | not supported |
| Gemma-4-26B-A4B-it | A−C | 0.0239 | statistically detectable but below the registered +0.05 practical threshold; RQ0 still not supported |

Headline AC values were also consistent with the MRR conclusion:

| Model | Arm | AC@1 | AC@3 | AC@5 |
|---|---|---:|---:|---:|
| Qwen3.6-27B | A | 0.3000 | 0.4819 | 0.5528 |
| Qwen3.6-27B | B | **0.3222** | **0.4875** | 0.5569 |
| Qwen3.6-27B | C | 0.2889 | 0.4653 | **0.5861** |
| Gemma-4-26B-A4B-it | A | 0.2847 | 0.4708 | 0.5722 |
| Gemma-4-26B-A4B-it | B | **0.3000** | **0.4778** | **0.5833** |
| Gemma-4-26B-A4B-it | C | 0.2611 | 0.4347 | 0.5444 |

The registered RQ0 conclusion is therefore **unsupported for both
architectures**. Adding the current static dashboard to complete text did not
improve frozen-model RCA. Gemma's A−C advantage cannot be attributed solely to
the image because A also includes natural-language text and loses to the
byte-identical text-only arm B.

The image was not simply ignored. Against B, A changed top-1 on 153/720 Qwen
incidents and 158/720 Gemma incidents, but it broke more text-correct cases than
it repaired (Qwen 36 broken versus 20 repaired; Gemma 33 versus 22). Later
development diagnostics showed that the models could read most visual facts
and that a large explicit edge key repaired topology-edge perception, but the
12-case renderer-v7 RCA effect remained unstable and architecture-dependent
(Qwen −0.0208 MRR, Gemma +0.0625, each driven by one incident). Causal-SFT and
nonredundant-allocation pilots also failed their registered cross-model gates.

RQ0 remains frozen as this negative result. RQ1 is a new operation-level
question, not a rerun intended to replace RQ0 with a positive number.

## 4. RQ1 and why it is needed

The active question is:

> **RQ1. Under equal evidence access and matched investigation budgets, when
> and how does visual-text, topology-aware observability provide incremental
> value for VLM-based root-cause analysis?**

RQ1 does not overwrite the completed RQ0 result. RQ0 already showed that adding
a redundant static dashboard to complete text did not improve average RCA for
either tested architecture. RQ1 asks a narrower mechanistic question: visual
representations may help temporal scanning, graph/path reasoning, alignment, or
missingness inspection while text remains better for exact lookup. A pooled
average can hide this operation-dependent complementarity.

The registered sequence is:

1. **RQ1a:** retain RQ0 as the historical negative static-augmentation result;
2. **RQ1b:** map operation-specific utility under text, image, and exact hybrid
   views, then validate the learned router on disjoint exposed cases;
3. **RQ1c:** only after RQ1b passes, test operation/context-aware investigation
   routing against fixed modality allocations;
4. **RQ1d:** only after the routed observer passes, test causal influence with
   semantic visual interventions and shams.

RQ1c and RQ1d remain blocked. No SFT, LoRA, GRPO, or other training is part of
the current mapping experiment.

## 5. What was implemented for RQ1b

### 5.1 Dense, label-blind evidence store

`CanonicalEvidenceStoreV2WithDenseLogAndTraceTimeSlices` combines qualified
64-bin metrics with complete relative-time log bins, trace-service bins,
caller-to-callee trace-edge bins, explicit zero coverage, complete directed
edges, and derived paths. Absolute clocks and raw trace correlation IDs are
removed before the public store is created.

Each task is generated from one immutable `QuerySpecV1` and an ordered
`AtomicFactV1` inventory. Public facts expose only semantic fields needed by
the model:

```text
fact_id, domain, field, entity, relative_bin, value, unit
```

Private source lineage and automatically derived answer keys are stored in a
physically separate evaluator tree.

### 5.2 Nine RCA-VisOps

RCA-VisOps is not another root-cause benchmark. It is an automatically
generated diagnostic-perception benchmark that asks whether a model can
recover small, objectively checkable operations that an RCA investigator needs
before ranking a root cause. It separates failures to *read or connect the
evidence* from failures in the later RCA judgement.

#### 5.2.1 How the automatic question/answer pairs are built

For each rostered incident, the compiler first produces the frozen,
root-label-blind evidence store described in Section 5.1. The task generator
then follows this sequence:

1. Enumerate only model-visible `AtomicFactV1` records. The generator never
   reads the root-cause label, accepted answer aliases, injection type, raw
   case ID, dataset name, or absolute clock when selecting a question.
2. Test the eligibility rule for each of the nine operation templates. For
   example, a path question requires an observed multi-hop path and its parent
   directed edges; a missingness question requires at least two series with
   unequal missing-bin counts.
3. Select eligible targets deterministically. Hash selection uses the source
   artifact hash and a fixed operation-specific salt; comparison tasks use
   frozen sorting and tie policies. Recompiling the same case therefore yields
   the same question and answer.
4. Build one immutable `QuerySpecV1`: operation, family, entity scope,
   relative-bin scope, aggregation rule, parameters, and the exact ordered
   `fact_id` inventory.
5. Derive the answer mechanically from those facts. All ties are retained and
   sorted where the answer is a set. The private answer and its derivation are
   written to a physically separate evaluator tree, never to a model prompt.
6. Render the *same query facts* twice: once as text fragment `B` and once as
   visual fragment `A`. Independent parsers reconstruct both inventories and
   require identical fact IDs and identical public fact values before the task
   qualifies. Hybrid is constructed only as exact `A+B` concatenation.

Tasks unsupported by the incident are omitted rather than filled with guessed
facts. Consequently, each case can have fewer than nine questions; the 90-case
mapping roster produced 708 qualified questions rather than 810. This is also
why the later inferential analysis first averages within an incident instead
of allowing cases with more eligible questions to receive more weight.

#### 5.2.2 The nine questions

The wording below is the actual frozen template, with incident-specific names,
fields, bins, and endpoints substituted automatically.

| Family / operation | What is shown and asked | Private answer form | Why it is included |
|---|---|---|---|
| Exact lookup — metric | A hash-selected non-missing point from one metric series: “What exact value does `<metric>` for `<service>` have at relative bin `<b>` (center `t=+<s>s`)?” | Number at that bin | Tests precision reading of a plotted/serialized value. It is a registered negative control because text commonly has an advantage for exact lookup. |
| Exact lookup — log | One eligible log time-slice record, preferring populated `event_count`, `error_count`, or `dominant_template_count`: “What exact `<field>` value is supplied for `<service>` at relative bin …?” | Number | Verifies that event density or error evidence can be located without asking the model to infer a root cause. |
| Exact lookup — trace | One eligible trace-service time slice, preferring populated `span_count`, `error_count`, or `latency_p95_ms`, with the same exact-value question form. | Number | Tests precise trace reading and prevents topology performance from hiding a basic trace-perception failure. |
| Temporal scanning — earliest onset | Up to four eligible metric series from different services: “Which service or tied services have the earliest anomaly onset?” | Exact set of all services tied at minimum `onset_rel_s` | Tests scanning and comparison across panels, where aligned visual position may plausibly help. |
| Temporal scanning — longest persistence | The same bounded comparison structure: “Which service or tied services have the longest anomaly persistence?” | Exact set of all services tied at maximum `persistence_bins` | Tests interval/shape comparison rather than a one-cell lookup; all ties are retained to avoid arbitrary labels. |
| Topology/path — directed edge | A deterministically selected observed edge plus up to seven local edge distractors: “For the observed connection between `<A>` and `<B>`, what is the caller -> callee direction?” | Exact `{"caller": A, "callee": B}` | Tests arrow-direction reading, a prerequisite for propagation reasoning and a common visual-graph failure mode. |
| Topology/path — multi-hop path | One label-blind shortest path, its parent edges, and nearby distractor edges: “What explicit observed caller -> callee path connects `<source>` to `<target>`?” | Exact ordered node sequence | Tests whether the model can connect several directed edges. Order matters because an unordered service set is not a propagation path. |
| Cross-modal alignment — entity/modality | For up to eight candidates, a service-by-`metric/log/trace` availability matrix: “Which service or tied services have evidence available in the greatest number of supplied modalities?” | Exact set tied at the maximum modality count | Tests linking the same entity across evidence panels instead of treating each modality independently. |
| Missingness — metric | Per-bin missing masks for contrasting series: “Which service or tied services have the most missing metric bins?” | Exact set tied at the maximum missing-bin count | Tests whether the model distinguishes absent telemetry from a normal zero; this is necessary for calibrated RCA under incomplete evidence. |

The counts generated in the current mapping roster are reported in Section
6.2. Earliest-onset and missingness have fewer eligible tasks because the
compiler refuses cases without a valid comparison; it does not manufacture an
answer to make the operation counts equal.

#### 5.2.3 Why this design is useful for RQ1

RQ0 asked the model to jump directly from a large dashboard or text dump to a
root-cause ranking. A null result could not reveal whether the image was
unreadable, whether topology was misunderstood, whether the visual facts were
read correctly but integrated badly, or whether text was simply better for
that operation. RCA-VisOps makes those mechanisms measurable.

The operation set deliberately mixes likely visual opportunities with controls:

- temporal scanning, path following, cross-panel alignment, and missingness
  inspection express the hypothesized visual inductive advantages;
- the three exact lookups test the opposite possibility and protect against a
  one-sided design that assumes images must win;
- directed edges and ordered paths distinguish seeing topology from merely
  recognizing service names;
- exact, automatically derived answers remove subjective annotation and make
  every error auditable back to supporting `fact_id`s;
- root-label-blind construction prevents the VisOps benchmark itself from
  leaking the answer to the downstream RCA problem;
- strict T/V/H fact parity means an arm can win only through representation or
  multimodal composition, not because it received additional evidence.

The mapping cell therefore learns *which representation, if any, is best for
each operation*. That rule must then be frozen and tested on the disjoint gate
roster. RCA-VisOps accuracy is evidence about perception and evidence
operations; it is not itself evidence that root-cause ranking improved.

### 5.3 Three strictly paired arms

- `T`: complete text fragment `B`;
- `V`: complete visual fragment `A`;
- `H`: exact ordered composition `A+B`.

The common system/task shell, answer schema, entity scope, candidate ordering,
relative bins, precision, units, missingness, concrete directed edges, paths,
and fact inventory are identical. Every task carries `fact_id -> text span`,
`fact_id -> visual primitive`, prompt-part hashes, image/text hashes, and a
paired-view audit.

### 5.4 Execution infrastructure

The existing CanvasRCA loader, renderer foundations, vLLM client, and scoring
utilities were reused where their contracts were safe. RQ1 added only the
minimum necessary provisional tooling:

- fail-closed exposure-ledger and roster builders;
- deterministic task/artifact preparation;
- renderer-v4 operation views;
- a resumable atomic result writer;
- a live-tokenizer context preflight for every frozen prompt;
- synchronous first/final GPU samples so even sub-50 ms calls have complete
  accounting;
- strict parsing/scoring for numeric, set, directed-edge, and ordered-path
  answers;
- a paired analyzer using incident-level aggregation, Wilcoxon Pratt tests,
  Cohen's dz, repair/break/net effects, and token/time accounting.

Three local commits freeze the executable implementation:

```text
392e4f0  Register RQ1 visual operations experiment
9cf71de  Preflight RQ1 context and isolate audit lineage
baf3bb0  Account for sub-interval RQ1 requests
```

The original RQ1b-local test suite, lint, and compilation checks passed with
**76 tests** after paired whole-incident context-preflight coverage was added.
The current provisional suite, including the answer-hidden RQ1b2 compiler,
renderer, runner, smoke, and registered analysis checks, passes **86 tests**;
lint and compilation also pass.

## 6. Data split and qualification

### 6.1 Outcome-blind exposed split

The completed RQ0 formal incidents are already exposed development data. They
were split without reading any new model outcome:

- mapping: 30 AegisLab + 30 AIOPS-2022 + 30 AIOPS-2025;
- independent gate: a disjoint 30 + 30 + 30 from the same exposed pool;
- RE2-OB: infrastructure smoke only;
- RE2-TT: still embargoed.

Mapping and gate membership are fixed by separate seed-42 SHA256 orderings.
No untouched reserve or heldout case has been opened for this work.

### 6.2 Mapping artifact inventory

The 90 mapping cases yielded **708 eligible tasks**, hence
`708 × 3 = 2,124` calls per model.

| Operation | Eligible tasks |
|---|---:|
| directed edge | 90 |
| earliest onset | 54 |
| entity modality alignment | 90 |
| log exact lookup | 90 |
| longest persistence | 88 |
| metric exact lookup | 90 |
| metric missingness | 26 |
| multi-hop path | 90 |
| trace exact lookup | 90 |

Critical frozen identifiers:

```text
mapping config hash:    bfe7632648473a1ddd1a9798de1cb20bf889f09f325e7a79ea5189dd1899e9fc
artifact inventory:     87dcecb34bf6b96a10147048e1e27aa59d508be842381f34ee91f6da6cb17d20
roster assignment hash: 8b1557ac619f33c13546b94f29a4332747ca1ad52e01d581c0114381300e3b7b
```

### 6.3 Renderer and determinism qualification

Four hash-selected cases from each primary dataset were inspected in contact
sheets, plus a dedicated AIOPS-2022 ANSI/control-character log stress case.
All seven render kinds were covered:

```text
metric point, log summary, trace summary, temporal summary,
topology, entity-modality matrix, missingness matrix
```

Fixes made before freezing included wrapped long logs, canonical control-
character escaping, topology label wrapping, margin correction, readable
multi-hop paths, and explicit model-visible `fact_id`s. Legitimate zero values
and missing facts remain visible rather than being mistaken for blank panels.

The complete static qualifier then verified all 708 images and 4,170 public
artifacts, exact cross-arm fact parity, leakage absence, PNG integrity, and
nonblank pixels. It recompiled 12 cases directly from raw telemetry and matched
all task, image, public, and private-answer hashes exactly. Qualification
status: **passed**.

### 6.4 Model smoke qualification

Both models used the canonical local recipe: unquantized BF16, 32,768 context,
16,384 output ceiling, temperature 0, top-p 1, seed 42, thinking off, eager
execution, prefix caching off, chunked prefill off, and
`gpu_memory_utilization=0.65`.

Each model ran 25 eligible tasks from one real RE2-OB, AIOPS-2022, and
AIOPS-2025 case, for 75 T/V/H calls.

| Model | Calls | Complete pairs | Infrastructure failures | Truncations | Smoke status |
|---|---:|---:|---:|---:|---|
| Gemma-4-26B-A4B-it | 75/75 | 25/25 | 0 | 0 | passed |
| Qwen3.6-27B | 75/75 | 25/25 | 0 | 0 | passed |

Smoke correctness and parse rate are diagnostic only; they were not used to
select prompts, renderer settings, tasks, or models.

### 6.5 RQ1 thresholds and why they differ from RQ0

RQ1b has two stages with different statistical roles. The 90-case **mapping**
set discovers one arm per operation; it has no p-value-based success threshold,
because testing a rule on the same cases that selected it would be optimistic.
Mapping chooses the highest Gemma operation accuracy, with the preregistered
cost-aware tie order `T > V > H`. The rule may become evidence only on the
disjoint 90-case independent gate.

The independent gate requires all of the following:

| Gate | Frozen threshold | Rationale |
|---|---:|---|
| Routed vs T on selected structural operations | Δ case-macro accuracy ≥ +0.10 and Pratt-Wilcoxon p < 0.05 | Show a practically large, paired visual benefit over the text baseline |
| Cross-dataset direction | positive in at least 2/3 datasets; none ≤ −0.10 | Prevent one dataset from carrying the pooled result while another is materially harmed |
| Exact-lookup negative control | T is not worse than V by >0.05 | Ensure the finding is operation-dependent complementarity, not that one arm is universally superior |
| Routed vs best fixed T/V/H arm | Δ ≥ +0.05 and Pratt-Wilcoxon p < 0.05 | Show routing adds value beyond simply using the strongest single representation everywhere |
| Parse rate | ≥0.95 in every arm/model cell | Keep malformed-output mass below the five-percentage-point practical scale |
| Whole-incident infrastructure exclusion | ≤5% | Retain at least 95% of paired incidents while tolerating occasional operational faults |
| Pairing/parity/leakage/runtime | all pass | Ensure the estimated difference is attributable to representation policy |

For `n=90`, the same planning approximation gives

```text
MDE ≈ (1.96 + 0.84) × paired_sd / sqrt(90).
```

The previously observed paired SD of 0.36 gives `MDE≈0.106`; a conservative
bounded-score SD of 0.50 gives `MDE≈0.148`. This is why the main structural
threshold is +0.10 rather than an attractive but poorly resolvable +0.03 or
+0.05. A positive effect below +0.10 that is not significant is reported as
**inconclusive**, not as proof of no effect. The +0.05 routed-versus-best-fixed
threshold serves a different purpose: it is the minimum worthwhile policy
gain. It still must achieve `p<0.05`, so it can pass only when the paired
differences are sufficiently consistent or their realized variance is below
the conservative planning value.

The paired Wilcoxon test ranks nonzero within-incident differences rather than
treating every query as independent. Pratt handling retains zero-difference
incidents in the rank accounting, which is appropriate because many exact
operations tie across arms. Averaging queries within incident first avoids
pseudoreplication: a case with nine eligible questions must not carry more
inferential weight than a case with seven.

The 5% infrastructure ceiling means at least 86 of 90 incidents remain paired;
four exclusions give 4.44%, while five would give 5.56% and fail. At the
boundary the normal-approximation standard error grows by only
`sqrt(90/86)−1 ≈ 2.3%`. This is a quality/robustness compromise rather than a
theorem-derived universal constant. Infrastructure failures remove the whole
T/V/H incident tuple; parse failures and truncations stay as zero-scored model
outcomes. The 0.95 parse rule is likewise a preregistered integrity policy, but
it has a useful bounded-outcome interpretation: allowing more than 5%
malformed outputs could by itself create an arm difference larger than the
+0.05 practical policy gain.

Finally, the smoke gate is deliberately different: it requires complete
pairing, zero infrastructure failures, full accounting, and—in v2—acceptance
of every strict answer schema, but correctness is not a pass condition. A
three-case smoke can establish that the pipeline works; it cannot estimate
efficacy with meaningful power.

## 7. RQ1b mapping results and run status

### 7.1 What `accuracy` means here

The `accuracy` in this section is **neither RCA AC@1 nor MRR**. RQ1b mapping
does not ask the model for a ranked root-cause list. Each call asks one
machine-verifiable atomic question and returns exactly:

```json
{"answer": ...}
```

The deterministic scorer assigns binary `score=1` only for an exact correct
answer, otherwise `score=0`:

- numbers must match within absolute tolerance `1e-6`;
- string sets must have exactly the same members (order ignored);
- directed edges must have the exact caller and callee;
- multi-hop paths must contain the exact ordered node sequence;
- parse failures receive zero;
- there is no partial credit.

The runner's arm-level `accuracy` is the fraction of completed query calls with
`score=1`. Thus Gemma H accuracy 0.7825 means that **78.25% of its 708 hybrid
VisOps questions were answered exactly correctly**. It does not mean that
78.25% of incidents had the root cause at rank 1.

For inferential gate comparisons, the analyzer first averages binary query
scores within each opaque incident and then compares those **case-macro
accuracies**. This prevents a case with more eligible operations from receiving
more statistical weight. Per-operation mapping accuracy remains the exact
query-level fraction for that registered operation.

### 7.2 Gemma mapping — execution complete, integrity gate incomplete

Gemma completed **2,124/2,124** registered calls in approximately 9,935 seconds
(2 h 46 min). Every one of the 708 tasks has exactly one T, V, and H result;
all 2,124 call keys are unique, and all rows share one config, runtime, roster,
and qualification contract.

| Arm | Accuracy | Parse rate | Mean input tokens | Mean output tokens | Mean wall time |
|---|---:|---:|---:|---:|---:|
| H — exact image+text | **0.7825** | 0.9350 | 1,676.9 | 100.9 | 4.40 s |
| T — complete text | 0.7797 | 0.8941 | 1,400.7 | 207.8 | 7.08 s |
| V — complete image | 0.6568 | 0.9364 | 377.9 | 63.6 | 2.55 s |

Run integrity:

- infrastructure failures: **0**;
- paired units missing an arm: **0**;
- output truncations: **3/2,124**; all retained as model outcomes;
- GPU accounting failures: **0**.

The pooled H−T difference is only **+0.0028 accuracy**. More importantly, all
three parse rates are below the preregistered 0.95 minimum. The run itself and
its artifacts remain complete and auditable, but Gemma's mapping cell is
formally `incomplete_parse_rate`; its numbers cannot authorize a router or the
independent gate.

### 7.3 Qwen mapping — complete and model-level valid

Qwen persisted all **2,124/2,124** registered calls in approximately 11,505
seconds (3 h 12 min). Five requests had infrastructure errors across four
unique incidents. The frozen paired policy therefore excludes all three arms
for those four incidents, leaving 86 paired cases. The whole-incident exclusion
rate is **4/90 = 4.44%**, below the registered 5% ceiling.

| Arm | Raw query accuracy | Parse rate | Completed calls | Infrastructure-error calls |
|---|---:|---:|---:|---:|
| H — exact image+text | **0.9105** | 1.0000 | 704 | 4 |
| T — complete text | 0.8628 | 1.0000 | 707 | 1 |
| V — complete image | 0.7387 | 0.9958 | 708 | 0 |

One output reached the frozen 16,384-token ceiling and remains a model outcome.
The five infrastructure failures came from the GPU-accounting boundary rather
than model parsing; they are not silently scored as wrong. After the registered
whole-case exclusion, Qwen passes its parse, truncation, pairing, and 5%
infrastructure gates.

### 7.4 Strict paired v1 analysis

The authoritative analysis is:

```text
RQs/RQ1/results/rq1b_visops_mapping_v1/analysis/paired_analysis_v3.json
SHA256 ee8ef2452952e43959b99c4d5af7e5a7b231b4a6af25aac1db6d0e4828e166cb
```

The analyzer averages query scores within each incident before paired testing.
It uses the frozen two-sided Wilcoxon signed-rank test with Pratt zero handling
and reports paired Cohen's dz.

| Model | Included cases | H case-macro | T case-macro | V case-macro | H−T | Pratt p | Cohen's dz | Model status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Gemma | 90 | 0.7810 | 0.7787 | 0.6607 | +0.0023 | 0.5990 | 0.052 | incomplete parse rate |
| Qwen | 86 | 0.9098 | 0.8595 | 0.7425 | **+0.0503** | **9.79e-7** | 0.586 | valid |

For Qwen, H improved 34 incidents, degraded 5, and tied 47 relative to T.
Its H−V difference was +0.1672 (`p=3.19e-15`), while V−T was −0.1169
(`p=3.49e-10`). This means the visual representation was most useful when
combined with the complete text, not as a replacement for it.

Per-operation accuracies reveal the mechanism and the reason a router remains
plausible:

| Operation | Gemma T | Gemma V | Gemma H | Qwen T | Qwen V | Qwen H |
|---|---:|---:|---:|---:|---:|---:|
| directed edge | 0.9778 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| earliest onset | **0.5741** | 0.0000 | 0.5370 | 0.5769 | 0.1731 | 0.5769 |
| entity/modality alignment | 0.1000 | 0.1000 | 0.1000 | 0.6163 | 0.1744 | **0.9767** |
| log exact lookup | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| longest persistence | 0.6023 | 0.0341 | 0.6023 | 0.6071 | 0.4286 | **0.6786** |
| metric exact lookup | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| metric missingness | **0.5769** | 0.1154 | 0.5000 | **0.7917** | 0.4583 | 0.5833 |
| multi-hop path | 0.9556 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| trace exact lookup | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

These are diagnostic mapping accuracies on exposed data, not heldout RCA
performance. The strong Qwen alignment result is evidence that A+B can improve
a concrete evidence operation. It does not override Gemma's integrity failure
or establish that a learned operation router improves root-cause ranking.

### 7.5 Why Gemma failed the parse gate and what is changing

Gemma produced 166 malformed outputs: 99 began with fenced JSON and then added
self-corrections or additional objects, while 67 began with prose. Among those
166 outputs, 158 contained at least two answer objects, six contained one
object embedded in extra material, and two contained none. Failures were
concentrated in set-valued alignment and persistence questions. The generic v1
instruction required `{"answer": <value>}` but did not say that tied services
must be represented by one JSON array; prompt-only compliance also did not
prevent multiple answer objects.

Post-hoc selection of the first or last embedded object is forbidden because
it would change the evaluator after seeing results. Lowering the 0.95 threshold
or advancing a Qwen-only router would likewise violate the registered design.
DD-25 therefore preserves v1 as incomplete and registers mapping v2 on the
identical 90 exposed cases. V2 changes only two public output-contract details:

1. the prompt states the exact answer shape for numeric, tied-set, path, or
   directed-edge tasks;
2. the same shape is enforced through vLLM's OpenAI-compatible strict JSON
   schema response format.

Facts, questions, private answers, T/V/H views, exact A+B composition,
renderer, roster, checkpoints, 32k/16k inference opportunity, scorer, and
statistical rules remain unchanged. Both Gemma and Qwen must be rerun after
static qualification and partition-aware smoke.

### 7.6 Mapping v2 — complete, valid, and router frozen

The registered repair is now complete. Its input-equivalence audit compared
all 708 tasks and proved equality of every CEB, query, fact inventory, private
answer, text view, image view, visual manifest, paired-view audit, and A+B
prompt fragment. It also checked 3,540 unchanged evidence artifacts. The only
changed objects are the public prompt/output-contract hashes required to state
and enforce the operation-specific answer shape.

```text
V2 config hash:
2ac662944cceb2beea7c7cc25c963b2d92f41a40a4622a86ec63265d1eb8f6f0

V1/V2 input-equivalence SHA256:
35ad2584ab3e3270ccd8b27d75895a28be0ab01ac6c7a72dfa8b582d20a871f9

V2 qualification SHA256:
b6335b1ab0f478a8c9d3bdf62a5720231642065a1e98a24921aceda63074c997
```

Both model-specific v2 smokes passed 75/75 calls, exercised all four answer
types, and had zero infrastructure failures or truncations. The full mapping
then produced:

| Model | Calls | H query accuracy | T query accuracy | V query accuracy | Parse rate | Infra | Truncation |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gemma | 2,124/2,124 | 0.9590 | 0.9562 | 0.9082 | 1.000 in H/T/V | 0 | 0 |
| Qwen | 2,124/2,124 | 0.9732 | 0.9703 | 0.9266 | 1.000 in H/T/V | 0 | 0 |

The server-enforced schema did more than improve formal compliance. Gemma's
mean output fell from 100.9/207.8/63.6 tokens in v1 H/T/V to
17.0/16.8/18.1 in v2; its total run fell from about 2 h 46 min to about
41 min. Qwen's v2 mean outputs are about 16.3--16.4 tokens per arm. These are
efficiency results of the output-contract repair, not evidence of visual
benefit.

The authoritative v2 paired analysis is:

```text
RQs/RQ1/results/rq1b_visops_mapping_v2/analysis/paired_analysis_v3.json
SHA256 ac14861f85c4be16606e402e611e44babe1cacf5dd54d027fd98038c2b259f2e
```

| Model | Cases | H case-macro | T case-macro | V case-macro | H−T | Pratt p | Cohen's dz | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Gemma | 90 | 0.9588 | 0.9558 | 0.9091 | +0.0030 | 0.5801 | 0.060 | valid |
| Qwen | 90 | 0.9738 | 0.9712 | 0.9273 | +0.0027 | 0.6045 | 0.054 | valid |

For Gemma, H−V is +0.0496 (`p=1.19e-6`) and V−T is −0.0466
(`p=2.09e-6`). For Qwen, H−V is +0.0466 (`p=1.25e-7`) and V−T is
−0.0439 (`p=2.31e-6`). Thus image-only remains worse than complete text on
average, while adding the image to complete text changes little at the pooled
level. The valid v2 result supersedes v1 for router discovery but does not
erase v1's documented contract failure.

The preregistered rule uses **Gemma only**, selects the highest operation
accuracy, and resolves exact ties using `T > V > H`:

| Operation | Gemma T | Gemma V | Gemma H | Frozen arm |
|---|---:|---:|---:|---|
| directed edge | 1.0000 | 1.0000 | 1.0000 | T (tie) |
| earliest onset | 0.9815 | 0.6481 | **1.0000** | **H** |
| entity/modality alignment | 0.8000 | **0.8444** | 0.8222 | **V** |
| log exact lookup | 1.0000 | 1.0000 | 1.0000 | T (tie) |
| longest persistence | 1.0000 | 0.8750 | 1.0000 | T (tie) |
| metric exact lookup | 1.0000 | 1.0000 | 1.0000 | T (tie) |
| metric missingness | **0.5385** | 0.1923 | 0.5000 | T |
| multi-hop path | 1.0000 | 1.0000 | 1.0000 | T (tie) |
| trace exact lookup | 1.0000 | 1.0000 | 1.0000 | T (tie) |

Qwen must use this same rule. Its own operation accuracies are reported only
as an architecture-interaction diagnostic; they cannot optimize a second
router. Because the mapping set selected the rule, neither the small pooled
H−T value nor an in-sample routed score is a valid success/failure test. DD-26
therefore freezes the rule and opens only the already registered disjoint
development gate.

### 7.7 Disjoint independent gate — complete, valid, and failed

The independent gate used 90 different already-exposed incidents, 30 per main
dataset, and 711 root-label-blind questions. It reused the frozen v2 evidence,
T/V/H representations, exact A+B prompt composition, renderer, scorer, router,
checkpoints, decoding settings, and analysis thresholds. It did not refit the
router or replace cases.

Live-tokenizer preflight identified prompts that could not reserve the full
16,384-token output ceiling inside the fixed 32,768-token context. The
registered whole-incident policy was applied before generation:

| Model | Requested incidents | Paired incidents | Context exclusions | Fraction | Ceiling |
|---|---:|---:|---:|---:|---:|
| Gemma | 90 | 89 | 1 | 1.11% | 5% |
| Qwen | 90 | 88 | 2 | 2.22% | 5% |

No replacement incident was selected. Every task and all three arms belonging
to an affected incident were marked as infrastructure-excluded. Across the
remaining 2,106 Gemma and 2,079 Qwen requests, parse rate was 1.000, with zero
truncations and zero additional infrastructure failures. Thus the gate is
valid for inference; its failure is an efficacy result.

Authoritative artifact:

```text
RQs/RQ1/results/rq1b_visops_independent_gate_v2/analysis/gate_analysis_v1.json
SHA256 4a8ba8d40af584ac2dbb60d7ed17846ed64a2c935d20d18083b6dba6764a7552
analysis contract aa037f5140e24130db4b71b2f1f69dee4f692779cf07d70164794d0d00a33365
```

| Primary gate quantity | Frozen requirement | Gemma | Qwen | Outcome |
|---|---:|---:|---:|---|
| Structural routed−T | Δ≥+0.10 and p<0.05 | **−0.0562**, p=0.0112 | −0.0227, p=0.3698 | failed; Gemma difference is significant in the harmful direction |
| Positive datasets | at least 2/3 | 1/3 | 1/3 | failed |
| Worst dataset | none ≤−0.10 | AIOPS-2025 **−0.1167** | AIOPS-2022 −0.0690 | Gemma failed material-reversal gate |
| Exact-lookup V−T | ≤+0.05 | +0.0037 | 0.0000 | passed negative control |
| Routed−best fixed | Δ≥+0.05 and p<0.05 | **−0.0118**, p=0.0104 | −0.0046, p=0.3622 | failed; best fixed arm is T |
| Integrity | all checks pass | passed | passed | valid negative test |

The apparently contradictory phrase “p=0.0112 but failed” is important. The
Wilcoxon test asks whether paired differences are centered away from zero; it
does not decide whether the direction is desirable. Gemma's negative estimate
is statistically detectable, so it is evidence that this frozen visual router
harms the selected structural operations—not evidence for the registered
positive hypothesis.

The mechanism is visible in the per-operation replication:

| Operation selected as non-text | Mapping Gemma T/V/H | Gate Gemma T/V/H | Gate Qwen T/V/H | Interpretation |
|---|---:|---:|---:|---|
| earliest onset → H | 0.9815 / 0.6481 / **1.0000** | **1.0000** / 0.7143 / **1.0000** | 0.9636 / 0.9455 / **1.0000** | H does not beat T for primary Gemma; small Qwen-only improvement |
| entity/modality alignment → V | 0.8000 / **0.8444** / 0.8222 | **0.9326** / 0.8427 / 0.8989 | **0.9205** / 0.8636 / 0.9091 | mapping-selected V reverses and is worse than T on both models |

This is consistent with mapping-selection variance and a text-ceiling problem:
the selected V advantage for alignment was only +0.0444 on the discovery set,
then reversed by −0.0899 on Gemma gate cases. The result does not show that
images can never help RCA. It shows that this renderer/task/router combination
does not supply a stable operation-level advantage strong enough to justify the
downstream routed agent.

An exposed-only trajectory analysis makes that mechanism more precise:

```text
RQs/RQ1/results/rq1b_visops_independent_gate_v2/analysis/failure_analysis_v1.json
SHA256 2a479b0b1baf4000696024084a662082d4af6931467278fed40c7a0a7f23ad99
```

- Gemma alignment V accuracy was nearly unchanged from mapping to gate
  (0.8444→0.8427; absolute drift 0.00175), while T rose sharply
  (0.8000→0.9326; drift 0.1326). The discovery “visual win” therefore came
  mainly from an unstable text deficit, not a visual improvement that later
  disappeared.
- Mapping V versus T had six repairs and two breaks, a net +4; the gate had one
  repair and nine breaks, a net −8. The mapping rule selected the arm from only
  four net discordant successes among 90 cases, with no shrinkage or minimum
  per-operation margin.
- Of the nine Gemma visual alignment breaks, six omitted at least one tied
  service and three overincluded services; mean predicted/true set Jaccard was
  0.514. Qwen had two repairs and seven breaks, with five overinclusions, two
  omissions, and mean Jaccard 0.375.
- Manual inspection confirmed that representative grids visibly contain the
  needed 0/1 cells and readable row labels. Because strict structured outputs
  contain no rationale, the safe diagnosis is a visual perception/set-
  aggregation failure; it cannot be narrowed further to digit reading versus
  downstream aggregation without inventing hidden reasoning.
- Qwen's hybrid onset arm did repair two text errors without breaking any gate
  case, but Gemma H and T were both perfect on this operation. That signal is
  architecture-specific, below the registered +0.10 practical gate, and cannot
  rescue the failed router.

### 7.8 RQ1b2 answer-hidden complexity development — complete, valid, and failed

DD-28's successor removed the main measurement ambiguity in the earlier
VisOps: no arm was shown the derived onset, persistence, winning entity, or
precomputed path. T and V received identical raw normalized facts, while H was
the strict image-first `A+B` composition. After the symmetric `+/-99.9`
robust-z display fix, all artifacts were regenerated and the old inventory was
quarantined. The final qualification passed 366-query fact parity, leakage,
answer-separation, PNG/nonblank checks, 12 manual reviews, and 12 deterministic
raw-telemetry recompilations. The Gemma smoke completed 36/36 calls with parse
1.000 and no infrastructure failure or truncation.

The development run then completed all **1,098/1,098** registered calls—366
per arm—in 1,287.7 seconds. All arms parsed at 1.000; there were zero
infrastructure exclusions, zero truncations, and complete GPU/token accounting.
The raw all-query accuracies were H 0.8251, T 0.8169, and V 0.6230. These pooled
figures mix controls and task families, so the registered decision uses the 80
incidents with paired low/high temporal-composition questions:

| Registered development quantity | Result | Promotion requirement | Status |
|---|---:|---:|---|
| High-complexity temporal V−T | **−0.3250** (V 0.1625, T 0.4875) | ≥ +0.05 | failed |
| Paired `(V−T)_high − (V−T)_low` | **0.0000** | > 0 | failed |
| High-complexity visual repairs / breaks | **4 / 30** | repairs > breaks | failed |
| Fixed `low→T, high→V` minus best fixed arm | **−0.1812** (policy 0.4188, fixed H 0.6000) | development diagnostic | harmful |

The negative high-complexity direction appeared in every dataset: AegisLab
−0.4286, AIOPS-2022 −0.2800, and AIOPS-2025 −0.2593. Its descriptive paired
Pratt-Wilcoxon p-value is `8.24e-6` and Cohen's dz is −0.571, but no p-value was
needed to reject promotion because the practical effect points strongly in the
wrong direction. Low-complexity V−T was also −0.3250, hence the zero pooled
interaction.

The controls rule out the claim that Gemma simply could not see or parse any
image content. Exact metric lookup was T/H 1.0000 and V 0.9889. Low-complexity
topology paths were T/H 1.0000 and V 0.9884. When AegisLab paths increased to
three-to-five hops, however, V fell to 0.4333 while T/H remained 1.0000.
Similarly, temporal H−T was +0.0500 at low complexity but −0.0125 at high
complexity. The supported interpretation is therefore narrow: the current
visual encoding is readable for simple lookup, but image-only composition
degrades with difficulty and adding it to complete text does not improve the
registered high-complexity endpoint.

DD-29 marks this development cell **valid and failed**. Per the frozen
conditional design, Qwen development is not run, the unused 150-case gate
remains unopened, and RQ1c/RQ1d/training/heldout work remains blocked. This is
not a resource-based early stop or a post-hoc model choice; it is the
preregistered consequence of all three Gemma mechanism conditions failing.

Authoritative artifacts:

```text
analysis JSON SHA256: bab07f7e721af803642a913ddae48fb25aae96c372091659679b67f1ae67a8ee
analysis Markdown:    7d9f63f82449ef693650d65aa69f814d6ebd494f05e3a26364a2584047dce608
run summary:          4891706c211437193891e0c6c74234bf0ca7e1296d661c17cfbe1bb1084ef463
```

The bounded post-hoc trajectory analysis does not alter that decision. It
finds that V selected at least one panel with no valid sustained onset in
25/80 high-complexity cases, returned a singleton in 58/80 despite only 45
singleton gold answers, and included the top rendered row in 30/80 versus
15/80 gold answers. A representative break selects a one-bin `99.9` spike
instead of the actual two-bin run; a representative repair uses a clear early
two-cell color block to correct T's later choice. H repaired eight T errors but
broke nine, with seven of eight repairs concentrated in AIOPS-2022. These are
post-outcome diagnostics—not eligible subgroup claims—but they isolate
singleton salience, row position, tie under-selection, and missing intermediate
composition as candidate failure mechanisms. The artifact SHA256 is
`6530012a568da3926b3b1c817d83466e925bab83f56bec87a986896ab570e43b`.

### 7.9 RQ1b3 implementation and v1 interface smoke — qualification failed

RQ1b3 implements the registered separation between evidence acquisition and
selection. Stage 1 must externalize the onset or null state of all 12 panels;
Stage 2 receives only that persisted same-arm ledger and returns the earliest
panel plus all ties. New disjoint 90-case development and 150-case gate rosters
were frozen, with zero overlap with earlier RQ1 rosters and the unopened RQ1b2
gate. The compiler produced exact T/V/H fact parity, natural numeric panel order
for the main condition, and a deterministic full-row permutation for the sham.
All six validation images passed leakage, nonblank, deterministic-render, and
manual readability checks.

The first Gemma Stage-1 smoke is informative but does not measure whether H
beats T:

| Condition | Requests | Parsed | Truncated | Status |
|---|---:|---:|---:|---|
| main T/V/H | 9/9 | 9/9 | 0 | interface path passed |
| row-sham V/H | 6/6 | 5/6 | 1 | frozen smoke gate failed |

The failed sham response emitted a valid ledger prefix through `"sign":` and
then generated grammar-legal whitespace until the 16,384-token ceiling. A
separate minimal probe reproduced the behavior after `"answer":`, while a
strict no-whitespace regex returned valid JSON in 11 tokens. This localizes the
failure to the whitespace-permissive JSON serialization path. It is not input
truncation, insufficient evidence, a GPU fault, or a reason to increase the
unified output budget.

DD-31 freezes the repair boundary. V1 artifacts and hashes remain immutable and
its smoke remains failed. V2 changes only the response transport: compact
entries such as `M7:positive@4` or `M7:null` are constrained by a task-specific
regex with no whitespace path, then deterministically expanded to the same full
`PanelOnsetLedgerV1` before persistence and Stage 2. Facts, prompts A/B and
strict A+B composition, images, questions, onset rule, models, vLLM sampling
configuration, scores, rosters, and every statistical threshold remain
unchanged.

That complete v2 smoke has now passed:

| Cell | Calls | Parse | Truncation | Infrastructure failure |
|---|---:|---:|---:|---:|
| main Stage 1, T/V/H | 9 | 1.000 | 0 | 0 |
| row-sham Stage 1, V/H | 6 | 1.000 | 0 | 0 |
| main Stage 2, T/V/H + oracle | 12 | 1.000 | 0 | 0 |
| row-sham Stage 2, V/H | 6 | 1.000 | 0 | 0 |

All Stage-1 responses were compact and contained no whitespace; the longest was
103 tokens rather than 16,384. All token/GPU accounting fields were complete,
Stage 2 was verified not to access original text or images, and oracle Stage-2
exact accuracy was 1.000, exceeding the frozen 0.95 interface threshold.
Correctness on the three smoke incidents is explicitly diagnostic, so the
observed arm accuracies are not used for model/arm selection or efficacy claims.
DD-32 therefore authorizes the frozen 90-case Gemma development run and nothing
beyond it.

### 7.10 RQ1b3 Gemma development — complete, valid, and failed

The repaired roster retained all 77 eligible original selections and added
only the required label-blind 4/5/4 replacements, producing exactly 30 cases
per dataset with zero overlap with the unopened gate. Its 90-query preparation
passed exact T/V/H fact parity, leakage, 13-image manual review, and 12/12
real-telemetry deterministic recompilations before inference.

The full registered cell then completed 990/990 calls:

| Cell | Calls | Infrastructure failure | Truncation | Paired exclusion |
|---|---:|---:|---:|---:|
| main Stage 1, T/V/H | 270 | 0 | 0 | 0 |
| main Stage 2, T/V/H + oracle | 360 | 0 | 0 | 0 |
| row-sham Stage 1, V/H | 180 | 0 | 0 | 0 |
| row-sham Stage 2, V/H | 180 | 0 | 0 | 0 |

The registered promotion table is unambiguous:

| Gate | Threshold | Observed | Result |
|---|---:|---:|:---:|
| Final H−T exact-set accuracy | ≥ +0.05 | −0.0333 | fail |
| Stage-1 panel-macro H−T | ≥ +0.05 | −0.0028 | fail |
| H repairs vs breaks | repairs > breaks | 10 vs 13 | fail |
| H vs T ledger error | H < T | 0.0774 vs 0.0668 | fail |
| Oracle Stage-2 accuracy | ≥ 0.95 | 0.8000 | fail |
| Integrity | all cells pass | Stage-2 parse below 0.95 | fail |

Final exact-set accuracy was T=0.6222, H=0.5889, and V=0.1667. Stage-1
panel-macro onset/null accuracy was T=0.8944, H=0.8917, and V=0.5083. The
diagnostic paired Pratt-Wilcoxon comparison for final H−T gave p=0.5316 and
paired Cohen's dz=−0.0657; as explained in Section 9, this n=90 development
screen intentionally has no p-value promotion rule because its planning MDE is
about 0.106, much larger than the +0.05 signal used only to decide whether an
independent test is worth spending.

The dataset directions were heterogeneous but do not authorize a subgroup:
AegisLab H−T was −0.1333, AIOPS-2022 −0.0333, and AIOPS-2025 +0.0667. Selecting
only AIOPS-2025 after observing this table would be post-hoc outcome selection.

Stage-2 parse failures were complete, non-truncated JSON arrays whose panel
sets sometimes used natural numeric order instead of Python lexicographic
order—for example `M6` before `M10`. The registered parse flags and result are
preserved. An explicitly post-hoc order-insensitive sensitivity check raises
T/H/V/oracle correct counts from 56/53/15/72 to 58/56/17/74 out of 90, but H−T
remains negative at −0.0222, repairs/breaks remain non-positive at 10/12, and
oracle remains only 0.8222. Consequently the interface convention does not
explain or rescue the failed efficacy mechanism.

The row sham did establish output influence: exact Stage-1 main/sham ledger
agreement was only 0.4556 for H and 0.0556 for V; final-answer agreement was
0.6556 and 0.3000. This is strong arrangement sensitivity, but sham-minus-main
accuracy was −0.0222 for H and +0.0333 for V, so sensitivity must not be
reported as beneficial visual use.

DD-34 closes RQ1b3 before Qwen and before the locked 150-case gate. The next
authorized research work is an independently preregistered RQ2 study of
dashboard content, encoding, arrangement, and interactions—not another attempt
to retune this RQ1 result.

## 8. What can and cannot be concluded today

### Supported operational findings

1. Exact model-visible information parity is feasible for numeric, temporal,
   topology/path, alignment, and missingness tasks.
2. Mapping v2 is complete and model-level valid for both architectures: all
   4,248 calls completed, every arm parsed at 1.000, and no infrastructure
   failure or truncation occurred.
3. A type-specific server-enforced schema removed the v1 ambiguity while
   preserving every experimental input and reduced long self-correction
   outputs by roughly an order of magnitude.
4. The disjoint independent gate is valid for both architectures: 89/90 Gemma
   and 88/90 Qwen incidents remained fully paired, every executed output parsed,
   and no output truncated.
5. Image-only can be token-efficient, but its pooled operation accuracy is below
   complete text. Efficiency and accuracy remain separate outcomes.
6. The valid pooled A+B increment is very small on mapping data (Gemma +0.0030;
   Qwen +0.0027), and the independent operation router does not generalize.
7. On the primary Gemma gate, the frozen visual router is significantly harmful
   on selected structural operations (−0.0562, p=0.0112); the Qwen control is
   also negative (−0.0227) but not statistically significant.
8. The failed generalization is driven mainly by entity/modality alignment:
   image-only beat text by +0.0444 during mapping but lost by −0.0899 on the
   Gemma gate. This is evidence against treating a small in-sample visual lead
   as a stable modality rule.
9. A subsequent code-and-artifact audit explains why the other structural
   operations cannot rescue the router: the old `multi_hop_path` input visibly
   contained the already-derived path, and the temporal inputs visibly
   contained the already-derived onset/persistence scalar. Their near-perfect
   scores are valid lookup/readability measurements, but not evidence of
   multi-step graph or time-series composition.
10. RQ1b2 removed those visible answers and is technically valid: 1,098/1,098
    calls completed, all arms parsed, and no infrastructure exclusion or
    truncation occurred.
11. Simple visual lookup is nearly perfect, but visual-only compositional
    accuracy falls sharply with complexity: exact lookup V=0.9889, low topology
    V=0.9884, high topology V=0.4333, and high temporal V=0.1625.
12. The RQ1b2 image-only complexity mechanism fails consistently: high
    temporal V−T is −0.3250 overall and negative in all three datasets; the
    paired high-minus-low interaction is 0.0000.
13. RQ1b3 is complete and technically interpretable as a failed development
    gate: all 990 calls completed without infrastructure exclusion or
    truncation, and H did not improve either the final set or Stage-1 ledger.
14. The row sham shows that visual arrangement causally changes ledgers and
    selections, but those changes do not improve accuracy. Output influence
    and beneficial visual contribution are therefore empirically distinct.
15. Oracle Stage 2 reaches only 0.8000 registered accuracy (0.8222 under the
    order-insensitive sensitivity check), proving that final selection remains
    a separate reasoning bottleneck even when perception is perfect.
16. The lexicographic-versus-natural-order mismatch is an interface defect,
    not an efficacy explanation; correcting it post-hoc leaves H below T and
    every promotion gate failed.

### Rejected or not yet supported

- that visual evidence improves RCA in general;
- that an operation router beats text-only or the best fixed arm;
- that image-only evidence becomes more useful than complete text as temporal
  or topological composition becomes harder under the current renderer;
- that the registered `low→T, high→V` access policy deserves an independent
  gate;
- that a complete two-stage onset ledger makes the current H arm outperform T;
- that row-order sensitivity is evidence of beneficial visual use;
- that the result generalizes to heldout incidents;
- that training is required or authorized.

The old router, the answer-hidden complexity mechanism, and the two-stage
onset-ledger successor are rejected, not merely waiting for more calls. Their
artifacts remain valid with different roles: mapping documents rule discovery,
the old disjoint gate provides a negative generalization test, RQ1b2 provides a
negative answer-hidden development test, and RQ1b3 separates perception from
selection while exposing arrangement and interface sensitivity. None may be
relabeled or selectively pooled to authorize downstream work.

## 9. DD-28 execution, thresholds, and registered next steps

1. Preserve the mapping and independent-gate artifacts and DD-27 without
   refitting the router or changing their statuses. The descriptive failure
   analysis is complete and remains post-hoc diagnosis only.
2. DD-28 registers a separate RQ1b2 answer-hidden complexity study. It supplies
   identical raw facts to T/V/H but never exposes the derived answer, a
   precomputed path, a winning entity, or a precomputed onset/persistence
   scalar. Low/high variants test whether visual utility grows with entity,
   edge, and distractor complexity.
3. Freeze 90 new exposed development incidents (30 per dataset) and 150
   additional disjoint exposed gate incidents (50 per dataset), excluding all
   old RQ1b cases. Do not open heldout, reserve, RE2, or unknown cases.
4. Implement and statically qualify raw temporal-onset, directed-shortest-path,
   and exact-lookup-control tasks. Preserve fact equality, T/V/H, strict A+B,
   evaluator-private answers, answer-separation tests, leakage audits, and
   renderer determinism.
5. The 90-case data-only preparation yielded paired low/high temporal tasks for
   80 incidents—28 AegisLab, 25 AIOPS-2022, and 27 AIOPS-2025—and the exact
   control for all 90. High three-to-five-hop topology exists for 30 AegisLab
   incidents but none in the other two datasets. Therefore temporal composition
   is frozen as the P1-P3 endpoint and topology remains secondary; mixing both
   would confound dataset with task family.
6. Manual perception review found that a near-zero baseline/MAD could display
   finite telemetry changes as robust-z values near `5e8`. Before any model
   call, the public transform was amended to winsorize all T/V/H normalized
   facts symmetrically at `+/-99.9`. Because the onset rule uses only sign and
   `|z|>=3`, this cap is mathematically answer-preserving. All 90 cases were
   regenerated, and the pre-fix artifacts were quarantined so they cannot be
   mixed with the qualified inventory.
7. The regenerated 366-query inventory passed exact T/V/H fact parity,
   leakage and answer-separation audits, nonblank rendering checks, 12-case
   manual review, and 12 deterministic raw-telemetry recompilations. The
   partition-aware Gemma smoke then completed all 36/36 calls with parse rate
   1.000, zero infrastructure failures, zero truncations, and all three answer
   types exercised. Its 0.8056 atomic accuracy is diagnostic only and was not
   used to choose the protocol. One earlier launch used the tools environment
   instead of the inference environment and failed before receiving any model
   response; it is explicitly invalidated and excluded rather than counted as
   an experiment.
8. Gemma development started only after those gates and a runtime tree freeze.
   It completed 1,098/1,098 calls with full integrity but failed all three
   promotion conditions: high V−T −0.3250, interaction 0.0000, and 4 repairs
   versus 30 breaks.
9. DD-29 therefore stops RQ1b2 before Qwen and before the 150-case gate. Keep
   the old RQ1b factorial, RQ1c, RQ1d, SFT/LoRA/GRPO, reserve, and heldout RCA
   branches blocked. The immediate authorized work is bounded descriptive
   failure analysis on these exposed trajectories and preparation of a distinct
   preregistered hypothesis; the unused gate roster remains unopened.
10. DD-30 registers that distinct hypothesis as RQ1b3. It keeps identical raw
    facts and all T/V/H arms, but separates per-panel onset extraction from
    final tie selection with a complete `PanelOnsetLedgerV1`. H−T is primary,
    image-only remains mandatory secondary evidence, and a deterministic
    row-order sham tests the observed position-bias mechanism. A new 90-case
    Gemma development roster and separate 150-case gate must exclude every old
    RQ1 roster, including the unopened RQ1b2 gate. No inference is authorized
    before implementation, parity/leakage/answer-separation qualification,
    oracle-selector qualification, smoke, and runtime freeze.
11. DD-33 repairs the task-ineligible 4/5/4 dataset deficits without model
    outcomes, labels, private answers, or gate reuse. The repaired 30/30/30
    roster passes every preparation and runtime qualification.
12. RQ1b3 completes 990/990 calls and fails all six registered development
    conditions. The registered `valid_failed` result remains authoritative.
13. The Stage-2 set-order parser is corrected forward-only after a bounded
    sensitivity analysis. Historical parse flags and scores are not rewritten,
    and no rerun is authorized because the forgiving analysis also fails.
14. DD-34 stops Qwen and both unopened RQ1b3/RQ1b2 150-case gates, closes the
    current RQ1 visual-complementarity route, and authorizes only separate RQ2
    protocol work before any further model inference.

The RQ1b2 **development** gate is a one-way mechanism screen, not a
confirmatory hypothesis test. On the 90 exposed Gemma cases it requires
high-complexity temporal `V−T >= +0.05`, a strictly positive paired interaction
`(V−T)_high − (V−T)_low`, and more visual repairs than breaks. The `+0.05`
floor matches the project's smallest practically interesting accuracy scale;
the interaction condition asks whether visual benefit actually increases with
the registered composition difficulty rather than reflecting a generic arm
advantage; repairs greater than breaks requires a positive net count of cases
where vision fixes rather than damages the text answer. There is deliberately
no development p-value gate: at `n=90`, plausible paired SD 0.36 gives
`MDE≈0.106`, so demanding confirmatory significance at `+0.05` would make the
screen internally underpowered. Passing only authorizes a fresh disjoint test;
it cannot support a paper claim. Failing stops the mechanism and avoids spending
Qwen and independent-gate compute on a direction that lacks even this minimum
signal.

The confirmatory RQ1b2 thresholds are deliberately stricter than that
development promotion signal: on 150 gate incidents, temporal high-complexity V−T and
the paired temporal high-minus-low interaction must each be at least +0.10 with
two-sided Pratt-Wilcoxon p<0.05, while the fixed `low -> T, high -> V` policy
must exceed the best fixed arm by at least +0.05 with p<0.05. With paired SD
0.36, `(1.96+0.84)*0.36/sqrt(150)=0.082`; with conservative SD 0.50 the MDE is
0.114. Thus +0.10 lies near the powered resolution and denotes practical—not
merely statistical—value. At least two datasets must be positive, none may be
at or below −0.10, parse rate must be at least 0.95 per arm, and paired
infrastructure exclusion must remain at or below 5%.

RQ1b3 uses the same development-versus-confirmation statistical separation.
Its 90-case development screen requires both final H−T and Stage-1
incident-macro panel accuracy H−T to be at least +0.05, H repairs greater than
breaks, lower H ledger error, oracle-ledger Stage-2 accuracy at least 0.95, and
complete integrity. It uses no promotion p-value for the same `MDE≈0.106`
reason. The two +0.05 development floors reuse the project's smallest practical
effect scale: one applies to the downstream answer and the other prevents a
final-answer fluctuation from passing without measurably better evidence
acquisition. `repairs > breaks` is the exact discrete condition for positive
net correction. Requiring lower mean ledger error prevents H from passing on
coarse exact matches while making larger onset mistakes elsewhere.

The oracle threshold is 0.95 because Stage 2 is supposed to be a nearly
transparent selector once given the correct ledger. An oracle error mass above
5% is already as large as the +0.05 development effect being sought, so it
could mask or manufacture the entire claimed increment. This 0.95 boundary has
the same bounded-outcome interpretation as the parse floor; it is an interface
qualification rule rather than a universal psychometric constant.

If development had promoted, the 150-case gate would have required final H−T
at least +0.10 and ledger H−T at least +0.05, each with paired Pratt-Wilcoxon
`p<0.05`, plus a 75% ledger-mediation consistency rule, cross-dataset
safeguards, parse at least 0.95, and no more than 5% paired infrastructure
exclusion. The final +0.10 threshold is placed near the 0.082–0.114 planning
MDE range; the ledger threshold is smaller because each incident averages 12
panel decisions but is still tested at the incident level rather than treating
panels as independent samples. The 75% mediation requirement demands that the
arm with the correct final answer also have the lower ledger error in at least
three of every four informative discordances. It is a preregistered strong
majority, deliberately well above the 50% direction expected from an
uninformative correspondence; it is not presented as an exact binomial cutoff
because the number of discordant incidents is not fixed in advance.

## 10. Meeting-ready summary

| Item | Status | Takeaway |
|---|---|---|
| Previous static RQ0 | complete, unsupported | Redundant dashboard augmentation did not improve average RCA |
| RQ1 protocol and code | frozen provisional implementation | Tests *when* a representation helps, not whether images are universally good |
| Information/leakage audit | passed | Same semantic facts in T/V/H; root labels and private metadata excluded |
| 90-case mapping qualification | passed | 708 tasks, 7 render kinds, 12-case deterministic recompilation |
| Mapping v1 | preserved incomplete diagnostic | Gemma parse failure prevents using its apparent Qwen-only signal |
| Mapping v2 Gemma | complete and valid | H 0.9588 vs T 0.9558 case-macro; Δ +0.0030, p=0.5801; parse 1.000 |
| Mapping v2 Qwen | complete and valid | H 0.9738 vs T 0.9712; Δ +0.0027, p=0.6045; parse 1.000 |
| Frozen router | rejected by DD-27 after valid test | earliest onset -> H tied T on primary Gemma; alignment -> V reversed against T |
| Independent gate Gemma | complete, valid, failed | structural routed−T −0.0562, p=0.0112; significant harmful direction; AIOPS-2025 −0.1167 |
| Independent gate Qwen | complete, valid, failed | structural routed−T −0.0227, p=0.3698; same negative direction |
| RQ1b factorial / RQ1c / RQ1d | blocked | Current visual routing premise did not earn promotion |
| Failure diagnosis | complete | Old visual win was a selection-variance/text-deficit effect; several “structural” tasks exposed their derived answer |
| RQ1b2 qualification | passed | 366 queries; exact parity/leakage/answer-separation passed; 12 manual reviews and 12 deterministic recompilations passed |
| RQ1b2 Gemma smoke | passed | 36/36 calls, parse 1.000, zero infrastructure failures and truncations; correctness diagnostic only |
| RQ1b2 Gemma development | complete, valid, failed | 1,098/1,098; high V−T −0.3250; interaction 0.0000; 4 repairs vs 30 breaks |
| DD-29 / Qwen and 150-case gate | stopped before inference | All promotion conditions failed; unused independent roster remains unopened |
| DD-30 / RQ1b3 | implemented and statically qualified | Two-stage complete onset ledger; primary H−T; V mandatory secondary; new disjoint rosters |
| RQ1b3 v1 Gemma smoke | valid interface diagnostic, failed gate | main 9/9 parsed; row sham 5/6 parsed; one unbounded JSON-whitespace truncation |
| DD-31 / RQ1b3 v2 | complete smoke passed | 33/33 parsed; zero truncation/infra failure; oracle Stage 2 1.000; no original-evidence access in Stage 2 |
| DD-32 / Gemma development | completed under its authorization | Frozen 90-case cell ran in full; no authorization was extended to Qwen or gate |
| DD-33 roster repair and qualification | complete, outcome-blind | Retained 77 originals; repaired 30/30/30 roster has zero gate overlap; 90-query parity/leakage, 13-image review and 12-case determinism gates passed |
| RQ1b3 Gemma development | complete, valid, failed | 990/990; final H−T −0.0333; ledger H−T −0.0028; repairs/breaks 10/13; oracle 0.8000 |
| Row-order sham | complete diagnostic | Strong ledger/output sensitivity, but no beneficial accuracy mechanism |
| DD-34 / Qwen and 150-case gate | stopped before inference | All six promotion conditions failed; current RQ1 route is closed |
| Next registered direction | RQ2 protocol work only | Study dashboard content/encoding/arrangement effects before any further inference |

The most accurate one-sentence update for the meeting is:

> **RQ1 now has three valid negative mechanism results after RQ0: the disjoint
> operation router harms Gemma, answer-hidden image-only composition is 0.3250
> below text at high complexity, and the complete two-stage onset ledger still
> gives H−T=−0.0333 final and −0.0028 at Stage 1. All 990 RQ1b3 calls completed,
> but all six promotion gates failed; row order strongly changes output without
> improving accuracy. DD-34 therefore stops Qwen, both locked 150-case gates,
> RQ1c/training/heldout, and moves the next preregistration to RQ2 dashboard
> design effects.**

### 10.1 Post-report execution note: development-roster qualification

The first RQ1b3 development preparation attempt stopped before any model
request. Of the frozen 90 incidents, 77 supported the registered 12-panel
onset-ledger task: 26 AegisLab, 25 AIOPS-2022, and 26 AIOPS-2025. Thirteen
incidents failed the registered task predicate—at least 12 qualified normalized
series and at least one valid sustained onset—(4/5/4 by dataset).
This is a roster-qualification failure, not an efficacy result, parse failure,
or infrastructure exclusion. No development score exists yet.

DD-33 preserves that roster and registers an outcome-blind repair. It retains
all 77 supported incidents and fills the 4/5/4 deficits by the already frozen
development SHA256 ordering, after excluding every prior RQ1 roster and the
entire unopened 150-case gate. A candidate is accepted only when the frozen v2
compiler yields exactly one 12-panel task; the predicate uses telemetry shape
but no root-cause label, private answer, or model output. The repaired n=90
cell must receive a new inventory, qualification and runtime freeze. This
changes none of the thresholds described above and none of the statuses of
RQ0, RQ1b, RQ1b2, or the completed RQ1b3 v2 smoke.

The registered repair has now completed. It examined 5 AegisLab, 8
AIOPS-2022, and 4 AIOPS-2025 candidates in frozen order to accept the required
4/5/4 replacements. The new roster contains exactly 30 qualified incidents
per dataset, has zero overlap with the unopened gate, and preserves every one
of the 77 supported original incidents. The public audit contains only opaque
identifiers and has SHA256
`e8bd389352e53a503399c4f935acdf4f27739649ac85dddf5f13faf0173476fb`.
Full preparation and qualification have now passed: 90 cases, 90 queries,
180 main/sham images, exact parity and leakage checks, 13 manually reviewed
images, and 12/12 deterministic real-telemetry recompilations. The qualified
inventory hash is
`30ba90a4313866418783c95368f6efb1b2ecbe8cc373296d6d61b765024b8e28`;
the qualification report SHA256 is
`9881c82166cd073e4f6b17749e9c08fbf71ed757c609c50bb9c341a2de702344`.
The runtime tree was frozen at
`a951f5215bbeb170854bde7a725e161b0b50c1d55d9f3ddf0c1f8fac65c3c344`,
and the live Gemma server attestation and both dry-runs passed. The subsequently
authorized development execution completed every registered call and is now
reported in Sections 7.10 and 10. Its authoritative analysis SHA256 is
`de0e304616cce1dcd09fa2440ee471adfc9b9c83fec0da38f452c0f04e92216a`;
DD-34 freezes the result as `valid_failed` and stops all downstream RQ1b3
inference.

### 10.2 DD-35 next step: RQ2 static implementation, inference still locked

The next action is now recorded rather than left implicit. RQ2 separates three
causal questions that RQ1 could not answer cleanly: whether a telemetry content
family is present, how identical facts are visually encoded, and how identical
primitives are arranged. Its first study is a `2^4` equal-fact factorial over
metric encoding, graph encoding, cross-source arrangement, and entity order,
using answer-hidden operations and within-incident anchor-state relative credit.

RQ2a development will reuse 60 already executed exposed incidents, so it does
not consume fresh evidence. Only a complete development pass can authorize a
new 150-case independent operation gate. The 318 eligible exposed incidents
outside every prior private roster and locked gate are sufficient for that gate
and a later disjoint 90-case downstream development cell. RQ1's locked gates,
reserve, heldout, and RE2-TT remain unopened.

The development screen requires at least one target-family effect of +0.10,
repairs over breaks, lookup degradation above −0.05, no dataset effect at or
below −0.10, parse at least 0.95, infrastructure exclusion at most 5%, and
complete integrity. At n=60 and paired SD 0.36, the approximate 80%-power MDE
is 0.130, so the +0.10 criterion is only a compute-spending signal and has no
p-value gate. A promoted n=150 comparison would require +0.10 and Holm-adjusted
paired Pratt-Wilcoxon p<0.05; its planning MDE is approximately 0.082–0.114 for
paired SD 0.36–0.50.

DD-35 authorizes only RQ2 directories, contracts, code, tests, feasibility, and
static qualification. No RQ2 model inference is authorized until a later
decision freezes and attests every roster, renderer, prompt, answer, leakage/
parity audit, manual review, smoke, analyzer, and runtime artifact.

That initial static milestone is now complete. RQ2 owns all six required
directories while `src/` remains empty; the YAML contract, full 16-cell
factorial, eight matched anchors per main effect, four anchor groups per
two-factor interaction, label-blind salience ordering, and order-insensitive
set canonicalizer are implemented in the mutable scripts tree. Nine tests and
targeted Ruff pass. The status artifact is
`passed_static_contract_only` (SHA256
`9bf784b2ffa8135c017e45481c0d89ef97283e07c32422543c41c172cc43f7db`),
not an inference or efficacy result.

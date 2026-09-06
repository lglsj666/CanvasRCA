# RQ2 experiments

## Shared contract

RQ2 studies frozen one-stage VLM Solvers and deterministic dashboards. It does
not train the Qwen3.5-9B Composer. After full V3 regeneration, all 300 RQ1.1
headline incidents are reused and assigned label-blindly to 60 development,
150 independent, and 90 downstream-lock cases. The deterministic-tool study
uses the full frozen 480-case RQ1.1 manifest; RE2-OB and RE2-TT remain separately
reported reference/OOD strata rather than headline evidence. Qwen3.8 and Gemma receive the same public facts, task,
candidate order, and output schema; their official tokenizers and vision
processors remain model-specific.

The only active model endpoint is one-stage RCA. The previously implemented
seven-operation packed QA/perception endpoint is **abandoned**: its code and
archived artifacts remain for audit, but it is never scheduled or used in
selection, verification, analysis, or RQ2 claims. This scope change follows
RQ1.1's finding that generic perception QA—including the root-connected
call-graph subset—was not a stable positive case-level proxy for RCA. RCA
attention collection remains mandatory and occurs in the original call.

### Common SIRCL* RCA prompt

All three active experiments use the same RQ2-local RCA prompt. Its parent is
the selected SIRCL* adaptation used by RQ1.1, and its parent UTF-8 SHA256 is
`ce48089072fbbbaef28e6e0d6fdfe2a4d9db1eb9f7d669835536fa6ab1b1b90f`.
RQ2 does not import that prompt at runtime. Instead, the local copy makes
exactly two registered adaptations:

1. “twelve selected entity/metric series” becomes “the supplied selected
   entity/metric series”, because RQ2 legitimately varies card budgets and has
   a dense top-24 condition;
2. one representation-neutral paragraph states that card selection, encoding,
   position, size, order, style and rasterization are experimental controls,
   and that omitted/blank evidence is unavailable rather than zero or negative
   evidence.

The SIRCL* `M → R → L → G` analyzer order, MET-Z/TRC-L/LOG-R
semantics, `INITIAL → VERIFY → REVISE` internal checking procedure,
candidate restriction, compact reason and top-five JSON output remain
unchanged. The common prompt is fixed across every design and content arm.
Only requests containing an actual dashboard receive the RQ2 visual-field
dictionary; pure-text twins never receive image, chart, color or layout
instructions. Thus an RQ2 comparison changes the registered evidence/design
condition without also substituting a different RCA reasoning recipe.

`EvidenceCardV1` partitions the public M/R/L/G facts into human-readable
composite panels. One card can contain several compatible atomic facts, while
each atomic fact belongs to exactly one card and each selected card maps to one
equal-fact `SilhouetteV1`. Visual encoding cannot add, split, duplicate, or
delete facts. All service/node/pod identities remain case-local 3/4/5-digit
IDs. The old one-fact-per-panel layout remains only as an explicit sparse
negative control and is excluded from D* selection.

Before a model call, primitive-level audits require:

- metric facts map to points/heatmap cells, explicit missing gaps, printed
  scale, and a printed compact peak value;
- trace facts map to exact baseline/fault value rows and visual marks;
- log facts map to template/count/bin text plus a timeline or matrix cell;
- directed edges map to arrowheads, matrix cells, or edge-table rows;
- every selected fact appears exactly once in Canvas and Text twins;
- no raw case ID, dataset, label, fault type, absolute time, or path is visible.

## Experiment 1 — `exp_equal_fact_design`

Purpose: estimate how visual encoding, coordination, packing, legibility, and
processor-effective resolution change one-stage RCA when FULL content is fixed.

Registered factors include:

| Family | Values |
|---|---|
| Metric encoding | four-series aligned baseline-deviation lanes; four-row 64-bin heatmap; up-to-eight-series color/marker overlay on one shared baseline-z axis |
| Trace encoding | multi-operation baseline/fault dumbbells; paired baseline/fault bars |
| Log encoding | multi-template frequency timeline; template-by-time matrix |
| Topology encoding | directed node-link plus exact edge ledger; adjacency matrix; explicit edge table |
| Propagation encoding | exact rows; onset timeline |
| Layout | modality-grouped; entity-grouped; salience-first; topology-centered |
| Entity order | stable ID; label-blind salience/onset; topology BFS |
| Footprint allocation | compact; balanced; detail-first constrained allocation |
| Coordination | none; shared anonymous-entity cue; shared relative-time ruler |
| Metric scale | per-card raw; common robust scale |
| Grid | `10×10`; `12×8`; `16×6` |
| Logical cell size | 160–448 px |
| Raster scale | 0.75–1.50, after logical rendering |
| Relative legibility | 0.80–1.25 applied above the frozen 1.18 readability baseline |
| Gutter | 4–32 logical px |
| Skin | canonical; colorblind-safe |

Short metric gaps are shown as dashed bridges and missing-bin marks; longer
gaps remain open. Extreme values are displayed on a baseline-standardized,
clipped axis with an off-scale triangle while exact raw baseline and peak values
remain printed. This avoids turning sparse sampling into meaningless fragments
or allowing one outlier to flatten the rest of a series.

Footprint allocation no longer changes encoding. Any capacity downgrade is
recorded explicitly in the manifest rather than hidden. `raster_scale` changes
the raster while preserving logical geometry; `legibility_scale` separately
changes relative text/mark size. Analyses use actual processor geometry and
visual-token counts, not nominal PNG size alone.

The typography baseline applies to both ordinary and dense dashboards. Axis
labels, `b0/b63`, legends and detail rows use larger native glyphs; overlay
description, scale/window context and legends occupy separate vertical bands.
Sparse log cards reuse their internal whitespace for a visual comparison of
the existing LOG-R baseline/fault rates. This is an encoding change only: it
does not add, repeat or remove an atomic fact.

Every visual request receives the frozen RQ2 dashboard field dictionary. It
defines every rendered heading, symbol, unit and abbreviation, including
`b0/b63`, `onset +Xm`, `z`, `src M/R`, `Δlog2`, `p95`, `LOG-R`, template
placeholders, missingness Booleans, omission counts and caller→callee matrix
orientation. It explicitly states that the displayed fault window and onsets
are telemetry-derived rather than ground-truth injection labels. Pure-text
requests do not receive dashboard-layout instructions; the common RCA task,
candidate contract and telemetry semantics remain representation-neutral.

The dictionary also fixes the grammar of compound row labels. A metric label is
`M<panel-number> <entity-ID> · <metric-name>`: in
`M16 7425 · system.net.udp.out_datagrams`, `M16` is the case-local metric-panel
identifier, `7425` is the anonymous four-digit node ID, and the entire suffix is
the metric key rather than an operation name. A trace label is
`<entity-ID> · <operation-name>`. Standalone anonymous IDs use exactly three
digits for services, four for nodes and five for pods (including leading
zeroes). Numbers embedded inside a metric or operation name do not change the
owner entity's granularity.

The development panel contains 48 constrained exact D-optimal programs with
registered curve anchors. It is not a Cartesian grid. Development freezes D*,
one geometry-distant D_ALT, and 16 pre-result independent confirmation designs.
Independent therefore validates frozen contrasts instead of re-running all 48
designs.

Every design receives one one-stage RCA call. D* selection uses only RCA MRR;
when macro MRR differs by at most 0.01, lower RCA input-token cost and then
lexicographic cell ID break the tie. Neither packed QA nor a perception proxy
can select a dashboard.

```text
development: 48 × 60 × 2 models = 5,760
independent: 16 × 150 × 2 models = 4,800
total = 10,560 calls
```

## Experiment 2 — `exp_content_budget_twins`

Purpose: separate evidence selection, visual transport, and reclaimed screen
space.

Policies are:

```text
FULL
B25/B50/B75 × {COVERAGE, SALIENCE, DIVERSITY, RANDOM}
DENSE_M24
```

`B25/B50/B75` target minimum silhouette-area budget, not raw card count.
`RANDOM` is an opaque-hash, label-blind negative control. Every policy runs:

- `TextTwin`: selected facts as natural language;
- `CanvasReflow`: the same facts repacked into the freed space; remaining cards
  first use their largest already-qualified legal silhouettes and shrink only
  when required by capacity or packing feasibility.

`DENSE_M24` is an expanded-evidence mechanism condition, not a deletion budget
and not a C* candidate. The normal FULL representation retains the frozen top
12 metric series. `DENSE_M24` applies the same label-blind metric ranking and
retains top 24 (n=12 plus m=12), while keeping every trace, log, topology and
common fact byte-identical to normal FULL. It has two equal-information twins:

- `DenseText`: all top-24 metric facts and the unchanged R/L/G facts in natural
  language;
- `DenseCanvas`: the same top-24 facts, with up to eight color/marker-coded
  metric series sharing each baseline-z plot and an exact legend.

This registers two separate mechanisms. Top-12 overlay cells in Experiment 1
isolate the effect of visual overlay at fixed information. `DenseText−FULL TextTwin`
isolates the effect of adding 12 metric series in text. `DenseCanvas−DenseText`
isolates visual organization for the expanded fact set. The
`DenseCanvas−normal Canvas` difference is deliberately a combined
content-plus-compression effect and must never be called equal-information.

At B50, every selector additionally runs:

- `CanvasBlank`: omitted cards leave their FULL-layout slots blank;
- `CanvasAlt`: the same selected facts use frozen D_ALT for RCA only.

Blank versus reflow separates evidence deletion from space reallocation.
D* versus D_ALT measures a sparse content×design crossover.

```text
14 policies × Text/Reflow × 150 × 2 models = 8,400 calls
B50 Blank × 4 policies × 150 × 2 models = 1,200 calls
B50 D_ALT × 4 policies × 150 × 2 models = 1,200 calls
total = 10,800 calls
```

## Experiment 3 — `exp_downstream_transfer`

The 90-case downstream lock runs fourteen frozen RCA arms:

| Arm | Meaning |
|---|---|
| `T_FULL` | complete natural-language evidence |
| `C_FULL` | exactly the T_FULL facts as concise typed tuples `[region, field, entity_ids, relative_bins, unit, payload]` |
| `S_FULL` | byte-identical T evidence rendered as pixels |
| `V0` | frozen RQ1.1 renderer-v14 dashboard |
| `D_STAR` | best fixed full-card RQ2 program |
| `D_STAR_SKIN` | palette/line-style perturbation |
| `D_STAR_SPATIAL_SHAM` | fixed non-semantic placement perturbation |
| `C_STAR_TEXT` | selected C* facts as text |
| `C_STAR_COMPACT` | exactly the C* facts as concise typed tuples |
| `C_STAR_SCREENSHOT` | byte-identical C* text rendered as pixels |
| `C_STAR_CANVAS` | the same C* facts as silhouettes |
| `DENSE_TEXT` | expanded top-24 metrics plus unchanged R/L/G as natural language |
| `DENSE_COMPACT` | exactly the Dense Text facts as concise typed tuples |
| `DENSE_CANVAS` | exactly the Dense Text facts, with the 24 metrics compressed into shared-axis overlay silhouettes |

The C* three-way comparison separates text length, pixel transport, and true
visual organization. The spatial sham probes position bias without changing
facts, encodings, footprints, or candidates.

The compact arms are nonvisual structure/compression controls rather than a
second evidence pipeline. They are generated from the same canonical fact
objects, omit private fact IDs, and pass a semantic round-trip equality audit.
`C_FULL−T_FULL` measures the effect of replacing repeated prose with typed
structure. Within selected and dense content, Compact versus Text measures
serialization efficiency, while Canvas versus Compact tests spatial visual
organization after accounting for concise nonvisual structure. Without this
control, a dashboard could appear efficient merely because ordinary prose is
verbose.

```text
14 × 90 × 2 models = 2,520 calls
```

## Experiment 4 — `exp_tool_representation`

Purpose: test whether deterministic evidence-selection tools help text and
vision in the same way. This is not an interactive or multi-stage agent. A
host-side tool reads only the canonical public packet, selects a bounded fact
subset without labels or model calls, and then the frozen Solver receives that
subset in one of two exactly matched representations:

- `text`: natural-language TextTwin;
- `canvas`: the same selected atomic facts rendered with frozen D*.

Four profiles share an eight-entity budget and fixed per-region row caps:

| Tool profile | Selection emphasis | Motivation |
|---|---|---|
| `SIRCL_STAR_FUSED` | balanced M/R/L/G rank fusion | the existing MET-Z + TRC-L + LOG-R discipline plus graph context |
| `MET_R_ADAPT` | robust metric anomalies | metric-ranking/BARO-style localization without comparing unlike raw units |
| `TRC_G_ADAPT` | trace-local latency and graph context | TraceDiag/MicroDig-style local-vs-downstream evidence |
| `LOG_T_ADAPT` | log-template bursts and diagnostic counts | Denum/SimpleRCA/TORAI-inspired readable log evidence |

These are explicitly CanvasRCA adaptations, not claims of byte-identical
reimplementation of the cited systems. Modality scores are converted to ranks
before weighted fusion, so milliseconds, counts, z-scores and graph signals are
never treated as commensurate raw numbers. All ties use stable anonymous IDs.

Within a tool profile, `canvas − text` isolates representation under identical
selected facts. Between profiles, the fact set intentionally changes and the
contrast measures evidence selection. The difference-in-differences asks
whether a selection profile benefits vision more than text. The tool identity
is recorded for audit but is not supplied as diagnostic evidence.

```text
4 profiles × 2 representations × 480 cases × 2 models = 7,680 calls
```

The registered RQ2 total is therefore:

```text
10,560 + 10,800 + 2,520 + 7,680 = 31,560 model calls
```

This is one RQ2-wide budget and remains below the **40,000-call cap for the
entire major RQ**, not a separate allowance for every subexperiment.

## Outcomes and qualification

RCA reports MRR, AC@1/3/5, AVG@3/5, evidence grounding, unsupported claims,
root-evidence citation, repair/break, tokens, and errors. Design analysis
reports response curves, main effects, interactions, occupancy,
footprint downgrades, effective processor geometry, tokens, and robustness.

Every request additionally records client-observed TTFT, receiver end-to-end
latency, decode duration, TPOT, output-token rate, and transport-chunk
inter-arrival summaries. `prefill_time` remains explicitly unavailable because
the client cannot separate server queueing and transport from prefill; chunk
inter-arrival is a proxy rather than exact token ITL. A one-second run monitor
records throughput/goodput, utilization-weighted GPU seconds, peak VRAM, vLLM
KV-cache high-water mark, and estimated energy from sampled power. Preparation
and per-unit materialization record stage/renderer timing. These measurements
are operational and may be compared only under the same hardware/runtime; token
counts remain the portable representation-cost measure.

Attention remains a same-call diagnostic. Region and card density use exact
pixel overlap and processor geometry; attention never selects D* and is not
causal evidence. The case is the statistical unit. Paired inference uses
Pratt-Wilcoxon, paired Cohen's dz, Holm families, no confidence intervals, and
the registered `ΔMRR ≥ +0.05` material threshold.

### V3 qualification record

Four retained prepared inputs passed index, hash, completeness, partial-file,
and path audits: `rq2_clean_v3_development_prepared` (60/60; semantic index
SHA256 `b70ffddd44ac6e681c4ed4dd0d4e63b953ca677b8167158a2ab6cf12cc153165`),
`rq2_clean_v3_independent_prepared` (150/150;
`1fec2035a7a3fac0ff97f4567c9d3464fd99ceb1a495fe9415a22d8a1f503b93`),
`rq2_clean_v3_downstream_lock_prepared` (90/90;
`eb053d90cd9f64b7a76696bd97c8195768582d74c3cab4b38bd56887801bc4b8`),
and `rq2_clean_v3_tool_full_prepared` (480/480;
`a9ac909d1968c0e36769e9f353a4362274d4975755a2c95bf7d6bc69150cc855`).

The bounded dual-model smokes `rq2_exp_equal_fact_design_smoke_v10` (8 calls),
`rq2_exp_content_budget_twins_smoke_v10` (18),
`rq2_exp_downstream_transfer_smoke_v10` (18), and
`rq2_exp_tool_representation_smoke_v10` (16) all passed. Across them, all 60
initiated requests produced terminal trajectory records, parse rate was 1.0,
and no infrastructure error or truncation occurred. Completed conversations,
prompts, raw responses, attention/performance accounting, and persistence were
manually inspected. These smokes contain RCA only and do not reactivate the
abandoned packed-QA task.

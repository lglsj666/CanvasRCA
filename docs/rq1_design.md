# RQ1 experiment design — the dashboard as a token budget

*Design document. No results here — this specifies what to run, in what order,
under what decision rule. Written 2026-07-23, after the CI-removal and render-cache
changes and before the open-model bake-off has been scored.*

**RQ1 — How should all key telemetry be compiled into a single dashboard image?**

Prerequisite reading: [`docs/dashboard_design.md`](dashboard_design.md) for what the
renderer does today and which choices are settled versus default-awaiting-evidence.

## Terms used in this document

- **MRR (Mean Reciprocal Rank)** — the accuracy score. For one case it is 1.0 if the
  correct culprit service is ranked first, 0.5 if second, 0.33 if third, and 0 if it
  is not in the model's top five. Averaged over cases. Higher is better.
- **Token** — the unit models read text and images in, and the unit they are billed
  in. An image costs "image tokens"; the text prompt costs text tokens. "Cheaper"
  below means fewer total tokens per case.
- **Modality** — which inputs the model is given: `image_only` (the dashboard picture
  alone), `text_only` (the same data written out as text tables), or `hybrid` (both).
- **Vision-language model** — a model that reads images together with text.
- **Pareto frontier** — the set of settings where you cannot get more accuracy without
  spending more tokens (and vice versa): the "best trade-off" curve. A single figure
  plotting accuracy against token cost.
- **Axis, level, cell** — an *axis* is one design choice (e.g. image resolution); a
  *level* is one of the three budget tiers below (B0/B1/B2); a *cell* is one concrete
  configuration that actually gets run and scored.
- **One-axis-at-a-time (OAT)** — a screening method that changes a single setting at a
  time. The earlier plan used it; §1 explains why the budget framing improves on it.
- **n=100 / n=20** — the number of cases in a run.
- **S1 / S2** — the two screening datasets: S1 = AegisLab (primary), S2 = AIOps-2025
  (secondary check). Both are microservice-incident datasets reused from the sibling
  text project.
- **SOTA (state of the art)** — the best previously published score on a dataset.
- **Sonnet-5 (claude-sonnet-5)** — a frontier Anthropic model, used here as a
  high-quality reference and as the final confirmation model.
- **Zero-shot** — the model is given the task with no worked examples.
- **Statistics in the decision rule (§5):** the **Wilcoxon signed-rank test** asks
  whether two settings' per-case score differences lean consistently one way (it
  returns a *p-value*: small p = unlikely to be chance). **Cohen's d** says how large
  the difference is, in standard-deviation units. The **Bonferroni correction**
  divides the significance threshold by the number of settings compared, so testing
  many of them does not produce a false "winner" by luck. **Spearman rank
  correlation** (−1 to +1) measures how similarly two models order the same settings.
- **DD-N** — "design decision N," a numbered entry in
  [`plans/design_decisions.md`](../plans/design_decisions.md).

---

## 1. The reframing: prioritization under a token budget

The sketched plan (`plans/action_plan.md`, M2) screened one axis at a time from a
fixed baseline and asked, per axis, "does this level raise MRR?" That treats every
`DashboardConfig` axis as independent and free. Two facts break that framing:

1. **A dashboard costs tokens, and the cost is the point.** Image tokens count in
   every number (invariant 5). A 2048px dashboard with 20 panels and every aux panel
   is not "the 1024px/6-panel dashboard but better" — it is a *different point on a
   cost curve*. The sibling text project reports MRR-per-token rows; the only claim a
   dashboard can make that a text system cannot is **"here is what a visual token
   buys."** That claim is a Pareto frontier, not a single winning config.

2. **The axes interact, and they interact through the budget.** At 6 panels every
   wasted panel is fatal, so *selection quality* dominates. At 20 panels selection
   barely matters but *legibility and layout* do. Screening `ranker` at a fixed
   budget answers the wrong question, because the best ranker at budget 6 need not be
   the best at budget 20.

So RQ1 is organised as **three budget levels**, each a named preset family with its
own prioritization logic — *what earns space first when space is scarce* changes with
how much space there is. Within each level we screen the axes that actually bite at
that budget; across levels we read off the accuracy-vs-token frontier.

This also makes the modality question (axis G) sharper. DD-11 hinted the metric
panels may not be load-bearing on AegisLab. If that is true, the interesting result
is not "images lose" but "**images only start paying above budget B1**" — a
budget-dependent answer that the level structure is built to surface and the flat OAT
sweep would have missed.

---

## 2. The three budget levels

Budget = total tokens/case = image tokens + prompt text tokens, both already measured
by the pipeline. The image-token figures below are approximate Anthropic-tile
estimates for the given `long_side_px`; the runner records the true per-case count.

### B0 — Lean (~1k image tokens/case)
*One small image, nothing that does not earn its pixels.*
`long_side_px=1024`, `panel_budget=6`, `layout=small_multiples`,
`topology=colored`, `show_legend_table=False`, `show_logs=False`,
`show_traces=False`.

**Prioritization:** colored topology first (one glance = which service), then the
top-6 anomalous KPIs; everything else is dropped. With six panels, *which six* is
almost the entire result, so **selection is the axis that bites** — B0 screens A
(`panel_budget` small values × `ranker`) and A′ (caps), and little else.
**Hypothesis:** if a lean dashboard is within noise of a rich one, the project's
efficiency story is its headline.

### B1 — Standard (~2.5k image tokens/case)
*The current v0 family — room to compose.*
`long_side_px=1568`, `panel_budget=12`, `topology=colored`, legend on, logs+traces
on. This is today's default and the config behind the Sonnet-5 0.797 AegisLab number.

**Prioritization:** balanced — metrics grid, topology, and both aux panels coexist.
With room to compose, **composition is what bites**: B1 screens B (layout), C
(topology style and labels), D (annotation). Selection is held at the B0 winner.

### B2 — Rich (~5k image tokens/case)
*Spend tokens to never omit the true cause's evidence.*
`long_side_px=2048`, `panel_budget=20`, everything on; optionally 2-tile.

**Prioritization:** recall — the true cause's evidence must be on the page even at the
cost of clutter. **What bites is whether more actually helps or hurts via
distraction**: B2 screens E (resolution/tiling), F (aux panels — is each pulling its
weight), and re-tests A′ caps (does redundancy hurt more when there is more of it).

### Cross-level — modality (axis G), run at every level
`hybrid` vs `image_only` vs `text_only`, at B0, B1, and B2. This is the thesis test,
and its answer may be budget-dependent. It is the highest-priority axis and runs
first (see §4).

---

## 3. What is screened where

| Axis | `DashboardConfig` field(s) | B0 Lean | B1 Standard | B2 Rich |
|---|---|:--:|:--:|:--:|
| A — selection | `panel_budget`, `ranker` | ✅ primary | fixed at B0 winner | ✅ large budgets |
| A′ — caps | `max_per_family`, `max_per_service` | ✅ | — | ✅ re-test |
| B — layout | `layout`, `grid_cols` | — | ✅ | — |
| C — topology | `topology`, `topology_labels`, `max_topology_nodes`, `max_propagation_rows` | — | ✅ | — |
| D — annotation | `shade_fault_window`, `annotate_extremes`, `normalize_panels` | — | ✅ | — |
| E — resolution | `long_side_px` (+ tiling) | (fixed 1024) | (fixed 1568) | ✅ |
| F — aux panels | `show_logs`, `show_traces`, `show_legend_table` | (off) | — | ✅ |
| G — modality | prompt-side | ✅ | ✅ | ✅ |

An axis is screened at the budget where it is load-bearing, not everywhere — that is
what keeps the cell count sane while still catching the interactions that a flat
per-axis sweep misses. Concretely, ≈10–12 cells per level including controls.

**Two amendments from 2026-07-28** (`RENDERER_VERSION` 5):

*Axis C gained a fourth level, `topology="propagation"`* (DD-18): the call-graph
thumbnail is replaced by services in rows ordered by anomaly onset, earliest
first. It is the only level that orders by *time* rather than by magnitude, which
is what distinguishes an origin from its victims, so the C screen is now
"which ordering principle earns the slot" rather than "how to draw a graph".
Presets `prop12` and `prop30`. Note the confound to control for: both presets
also drop the legend, whose job the strip does inline.

*Every modality result at this level predates a fixed renderer* (DD-17). The
metric grid was blank on AegisLab — sparse columns broke the line at every NaN —
so the `image_only` arms behind DD-16 were reading a topology thumbnail and two
tables, not a metric grid. **Axis G has to be re-run before its numbers mean what
they say.** That re-run is now more informative than it was, since the image
genuinely contains the metric evidence for the first time.

---

## 4. Protocol

**Screening model:** the winner of the six-model AegisLab bake-off. That bake-off has
since been run (see the devlogs for 2026-07-23 and 2026-07-24). With reasoning
("thinking mode") properly disabled, the strongest open models on AegisLab were
**qwen3.6-27b** (MRR 0.658, but slow at ~52 seconds per case) and **gemma-4-e4b**
(MRR 0.508, but fast at ~6 seconds per case) — an accuracy-versus-speed choice that
is still open. Whichever is chosen, it is self-hosted, so running it costs no API
money — that is what makes 100-case screening across two datasets affordable.

**Screening sets.** S1 = **AegisLab n=100** (primary ranking; RE2-OB/TT are saturated
at ≈0.99 and cannot separate configs). S2 = **AIOPS-2025 n=100** (secondary; text
SOTA 0.390, unexplored, guards against AegisLab-specific overfitting). Cases drawn
from the frozen `configs/case_manifest_480.json` so every cell sees identical cases.

**Stage order.**
1. **Stage 0 — perception prefilter ($0, no inference).** For every candidate level,
   pre-render an 8-case AegisLab gallery (`scripts/prerender_config.py`, to be added)
   and have the **render-reviewer** agent run its legibility + perception probe. Drop
   levels that fail human legibility before spending any inference — expected
   casualties: 1024px with 20 panels, overplot on 40-service AegisLab, `names` labels
   at 25 nodes. Paper-defensible exclusion, saves whole cells.
2. **Stage 1 — modality at each level (the thesis test).** hybrid / image_only /
   text_only at B0, B1, B2, on S1+S2, with the screening model **and** a Sonnet-5
   arm. The Sonnet hybrid-B1 AegisLab slice doubles as the mandated 100-case
   promotion run for the existing 20-case Sonnet-5 result (MRR 0.797). **Gate:** if
   `text_only` scores about the same as `hybrid` on
   the discriminating datasets, or the two models rank modalities differently, stop
   and escalate before spending Stage 2 — the central claim is in question.
3. **Stage 2 — within-level screens.** Run each level's bitting axes (§3) on S1+S2
   with the screening model. Per axis, apply the decision rule (§5). Freeze the
   winning level-config.
4. **Stage 3 — cross-level Pareto + frontier confirmation.** Place the B0/B1/B2
   winners on the MRR-vs-tokens/case plane. Re-run the frontier configs (and any
   candidate `v3`) on Sonnet-5, AegisLab n=100, paired, to confirm the ordering
   transfers to a frontier model; report Spearman rank correlation of the two models'
   config orderings — the empirical answer to "does open-model screening transfer."

**Bookkeeping.** One YAML per cell in `RQs/RQ1/configs/experiments/`, named
`rq1_<level>_<axis>_<cell>.yaml` (e.g. `rq1_b0_selection_b06_coverage.yaml`),
committed before the run (experiment-skill gate). Every axis outcome — including
nulls — recorded in `plans/design_decisions.md`; a devlog entry per session. Renders
served from the content-addressed render cache (`results/render_cache/`), so all
models in a cell see byte-identical images.

---

## 5. Decision rule (no confidence intervals)

Confidence intervals (a statistical "the true value is probably in this range" band,
computed by resampling — "bootstrap") have been removed from the evaluation
(`RQs/vlmrca/eval/metrics.py`). Instead, a claim that one setting beats another rests on
the paired Wilcoxon signed-rank test and Cohen's d (both defined in Terms above),
matched case-by-case. Per-case MRR is still saved in every run, so a confidence
interval can be recomputed later if a reviewer asks — it is simply no longer reported.

In the rule below, **ΔMRR** ("delta MRR") means the change in MRR when switching to
the new setting; the **incumbent** is the current best setting; and a level is
**adopted** only if *all* the listed conditions hold.

> **Adopt** a new level over the incumbent only if, on dataset S1 (compared
> case-by-case): the MRR improvement is at least **+0.03**, AND the Wilcoxon test
> p-value is below **0.05 ÷ k** (where k = the number of non-control levels tested on
> that axis — dividing by k is the Bonferroni correction, so testing several levels
> does not hand us a false winner), AND the improvement does not flip to a loss on
> the second dataset S2 (its change stays above −0.02). Report Cohen's d as well; if
> a "winning" result has an effect size **|d| < 0.2** (very small), flag it as
> **fragile**. If the MRR change is smaller than 0.02, or the p-value is not small
> enough, the result is a **draw**; on any draw or tie, **keep the simpler/cheaper
> level** (fewer tokens, fewer panels, simpler layout). Declaring an overall RQ1
> winner (the frozen config, called `v3`) additionally requires it to beat the
> current B1 default by at least +0.02 MRR, with a small p-value, on the Sonnet-5
> confirmation run.

The "prefer cheaper on a tie" clause is what makes this a budget-aware design rather
than an accuracy-only one: a config that matches the incumbent for fewer tokens *is*
a win, and the frontier records it as one.

### 5.1 Where the +0.03 threshold comes from (added 2026-07-26)

The +0.03 figure above was chosen before anything had measured how much a number
moves between two runs of the *same* config. That measurement now exists, and it
changes what the rule can and cannot do.

Two terms, since they carry the argument. **Replicate noise** is how much a score
changes when you re-run an identical setup — pure measurement error. **Minimum
detectable effect (MDE)** is the smallest true difference a test can reliably find
at a given number of cases; below it, a real improvement usually gets reported as a
draw. Both are in MRR units.

What was measured, all on AegisLab with 20 cases:

| pair | what it isolates | paired sd |
|---|---|---|
| two Sonnet-5 runs, same config | replicate noise alone | 0.255 |
| Sonnet-5, caps on vs off (DD-11) | config effect **+** replicate noise | 0.262 |
| two open-weight runs, DD-12 recipe | replicate noise alone | **0.000** |

The two Sonnet rows are nearly equal, and that is the whole finding. Subtracting
the variances leaves an estimated **config-effect sd of about 0.060** — meaning
roughly *all* the spread in the DD-11 A/B was the model disagreeing with itself,
and almost none of it was the two dashboards differing. What follows:

| decoding | MDE at n=100 | MDE at n=480 | cases needed for +0.03 |
|---|---|---|---|
| stochastic (Sonnet, as measured) | 0.073 | 0.034 | **598** |
| deterministic (open weight, estimated) | 0.017 | 0.008 | **32** |

The estimate above suggested the threshold survives under deterministic
decoding, detectable at n≈32. **That estimate was wrong, and the direct
measurement below supersedes it.** It is left in place because the way it failed
is instructive.

### 5.2 The measured config-effect sd, and what it costs the rule (2026-07-26)

Array A's selector A/B is the direct measurement §5.1 called for: same model,
same 100 cases, two dashboard configs (`cov30` vs `v0`), deterministic decoding,
so the only thing varying is the dashboard.

| source | config-effect paired sd |
|---|---|
| §5.1 estimate (variance subtraction, n=20) | 0.060 |
| measured, gemma-4-e4b | **0.396** |
| measured, gemma-4-26b-a4b | **0.328** |

The estimate was low by a factor of six. **Why it failed is worth keeping:** it
subtracted two nearly-equal variances, 0.262² − 0.255² = 0.0036, each estimated
from 20 cases. The sampling error on a variance at n=20 is roughly ±32%, i.e.
about ±0.02 on quantities near 0.065 — an order of magnitude larger than the
0.0036 difference being extracted. The subtraction was numerically meaningless.
It was labelled fragile and a conclusion was drawn from it anyway; that is the
actual mistake, not the arithmetic.

What follows, using the measured sd ≈ 0.36:

| | MDE at n=100 | MDE at n=480 | cases needed for +0.03 |
|---|---|---|---|
| measured | **0.101** | **0.046** | **1142** |

**The +0.03 adoption threshold is not achievable — determinism does not rescue
it.** The whole frozen pool is 480 cases across five datasets; a +0.03 effect
would need more than twice that in a single cell. Determinism was still worth
doing, and for a different reason than power: it makes runs comparable across
jobs and days, which is what lets Array B pair against Array A at all. But the
dominant variance is genuine case-to-case heterogeneity in how two dashboards
perform, and no amount of decoding hygiene touches it.

**The rule must change, not the decoding.** Three options, in preference order:

1. **Adopt on what is resolvable.** At n=100 that is ≈ +0.10; on the full 480
   pool, ≈ +0.05. Set the threshold from the design's power, not from taste.
2. **Report effect sizes with intervals and stop significance-gating** the grid.
   Screening is a ranking problem, not a hypothesis test — a config that is
   consistently better across cells is worth adopting even if no single cell
   clears α, and Bonferroni across the axes makes that worse, not better.
3. **Raise n per cell**, which trades directly against the number of axes the
   grid can afford and is the least attractive.

Whichever is chosen, **every comparison reports its own paired sd and implied
MDE alongside ΔMRR** — `scripts/compare_runs.py` prints both and flags a delta
smaller than the comparison can resolve. That flag is what turned this up.

**One clause above is not achievable as written.** The rule requires the final
Sonnet-5 confirmation run to beat B1 by +0.02. Per DD-14, Sonnet-5 cannot be run
deterministically — Bedrock rejects `temperature` for that model generation — so
its replicate noise is irreducible. Detecting +0.02 against it needs ~1345 cases;
even the entire 480-case pool only reaches an MDE of 0.034. The options are to
average k repeated runs (k=4 over the full pool reaches 0.018, at four times the
cost) or to treat the confirmation as directional — same sign, Wilcoxon
significant — without a magnitude threshold. **Recommended: directional, on the
full 480 pool.** The magnitude claim belongs to the deterministic open-weight
screening run; the frontier model's job is to confirm the ordering transfers, and
asking it for a precise magnitude is asking the noisier instrument for the finer
measurement.

---

## 6. Deliverables

1. **The accuracy-vs-tokens/case Pareto frontier** across B0/B1/B2 winners — the one
   figure no prior multimodal RCA system can produce, and the answer to "what does a
   dashboard token buy."
2. **The modality-by-budget table** — hybrid/image_only/text_only × B0/B1/B2 — the
   direct test of "the dashboard is the representation," with its budget dependence
   made explicit.
3. **A frozen `v3` config** (or a per-budget family of frozen configs) carried into
   RQ2/RQ3/RQ4, with each axis decision and every null recorded in
   `plans/design_decisions.md`.
4. **The rank-transfer result** (open model vs Sonnet-5 Spearman) — a reusable
   methods paragraph justifying free open-model screening for the rest of the project.

---

## 7. Tooling this design assumes (to build before Stage 0)

Small, listed so the design is executable rather than aspirational:

- `RQs/vlmrca/render/presets.py` — `DASHBOARD_PRESETS` (B0/B1/B2 field sets) +
  `make_dashboard_config(name, overrides)` that **errors** on an unknown preset or an
  unknown field name (so a "controlled" variable that is fiction fails loudly). Kept
  out of `dashboard.py` to preserve renderer purity.
- `scripts/smoke_e2e.py` / runner — resolve `--config` through the preset registry
  and accept repeatable `--set field=value`. (Today `--config` only sets the config
  *name*, silently keeping every default — a trap this closes.)
- `scripts/prerender_config.py` — config/preset → gallery PNGs for Stage 0.
- `scripts/run_cell.py` — run one `RQs/RQ1/configs/experiments/<name>.yaml` cell with
  `--resume` by `case_id`, using the render cache.
- `scripts/vllm_vlm/run_rq1_batch.sbatch` — serve the screening model, poll until
  healthy, run the queued cells on localhost, exit.

None of these change the renderer or the frozen output format; they are the harness
that turns the level definitions above into committed, resumable, byte-reproducible
runs.

# How the dashboard is built

*As-built description of the telemetry-dashboard renderer, with the reasoning
behind each design choice. Current as of 2026-07-23. Source of truth is the code;
this document explains it. When they disagree, the code wins and this document is
stale — fix it.*

The idea behind this project is that **the dashboard is the representation**: a site
reliability engineer (the on-call engineer who diagnoses production incidents)
figures out what broke by looking at a wall of charts, so we give a vision-language
model the same rendered wall of charts instead of feeding it metric numbers as text
tables. A vision-language model is an AI model that reads images together with text.
This document is about the code that produces that wall of charts — `RQs/vlmrca/render/`.
It answers two questions: what does the renderer actually do to a case, and why is it
built that way.

## Terms used in this document

- **Vision-language model (VLM)** — an AI model that takes images plus text as input.
  Here it reads the dashboard image and names which service caused the incident.
- **Root cause analysis** — working out which service caused an incident.
- **Series** — one metric's values over time (for example, one service's request
  latency). A case has thousands of these.
- **KPI (key performance indicator)** — a metric worth showing; used here as a
  synonym for "series."
- **Panel** — one small chart on the dashboard (one series drawn over time).
- **z-score** — how far a value sits from its normal (pre-incident) baseline, measured
  in standard deviations. A big z-score means "unusually high or low," i.e. suspicious.
- **`ksigma` and `robust` rankers** — two ways to score how anomalous a series is.
  `ksigma` uses the average and standard deviation; `robust` uses the median and MAD
  (median absolute deviation), a spread measure that outliers throw off less.
- **Topology** — the service call graph: which service calls which.
- **Manifest** — a small JSON file saved next to each image, listing everything drawn,
  so a case can be replayed later without re-generating the picture.
- **MRR (Mean Reciprocal Rank)** — the accuracy score used throughout the project.
  For one case it is 1.0 if the true culprit service is ranked first, 0.5 if second,
  0.33 if third, and 0 if it is not in the model's top five. Averaged over all cases.
- **Design decision N (written "DD-N")** — a numbered entry in
  [`plans/design_decisions.md`](../plans/design_decisions.md) recording why a choice
  was made and what evidence backed it.
- **Ablation** — turning one feature off to measure how much it was contributing.
- **A/B comparison** — running two dashboard settings on the same cases and comparing
  scores. Whether a difference is real is judged with the **Wilcoxon signed-rank
  test** (a paired test that asks whether the per-case differences lean consistently
  one way) and **Cohen's d** (how large the difference is, in standard-deviation
  units).
- **RQ1 and RQ4** — two of the project's research questions. RQ1: "how should all the
  telemetry be laid out in one dashboard image?" RQ4: the study that turns each
  feature off in turn to measure its contribution.

---

## 1. The pipeline, end to end

One case becomes one PNG plus a JSON manifest. The entry point is
[`compile_dashboard(view, cfg)`](../RQs/vlmrca/render/dashboard.py) in
`RQs/vlmrca/render/dashboard.py`; it is **pure and deterministic in `(view, cfg)`** —
same inputs, byte-comparable output — which is what makes golden-image tests, the
render cache, and A/B comparisons valid (invariant 3).

```
DataCase
  │  CaseRenderView.from_case      (leakage gate: strips every label-bearing field)
  ▼
CaseRenderView  ── metrics_df, logs_df, traces_df, graph, services, safe metadata
  │  score_series                 (rank ~50–5000 series by peak deviation)
  │  select_panels                (keep panel_budget of them)
  │  service_anomaly_scores       (per-service score → topology colouring)
  │  infer_fault_window           (estimate the disturbance band from telemetry)
  ▼
matplotlib figure — metrics grid (left 2/3) + auxiliary column (right 1/3)
  ▼
(PNG bytes, panel manifest)
```

### 1.1 The leakage gate — `CaseRenderView.from_case`

`compile_dashboard` **never receives a labelled `DataCase`.** It receives a
[`CaseRenderView`](../RQs/vlmrca/render/dashboard.py), a struct that structurally has
no `ground_truth` field. The only place a labelled case is narrowed to unlabelled
telemetry is `CaseRenderView.from_case`, which drops a `BANNED` set from metadata
(`ground_truth`, `ground_truth_candidates`, `root_cause`, `injection`,
`injection_point`, `cmdb_id`, `fault_type`, `failure_type`, `level`).

*Why structural, not disciplined:* a renderer feature added a year from now cannot
accidentally draw the answer, because the answer is not in the object it is handed.
`tests/test_no_leakage.py` enforces this (invariant 2). Note the true service
*name* legitimately appears among the candidates on the dashboard — what must never
appear is anything marking it *as* the answer.

### 1.2 KPI selection — the highest-leverage step

Selection, not rendering, is what decides whether the evidence is even visible: an
AegisLab case has ~1150 metric series and the panel budget is 12. This lives in
[`RQs/vlmrca/render/kpi_select.py`](../RQs/vlmrca/render/kpi_select.py).

**Scoring (`score_series`).** Each numeric column is scored by its *peak deviation
from a pre-fault baseline*. The baseline is the first 50% of the window
(`_baseline_slice`, `fault_frac=0.5`) — upstream loaders centre each case on the
injection, so the leading half is nominal; a *fraction* rather than a fixed index
keeps this correct across datasets with different window lengths. The `ksigma`
ranker uses mean/std; the `robust` ranker uses median and MAD×1.4826 (mirroring the
upstream BaroAnalyzer). Deviation keeps its **sign** (`signed_z`) because a metric
dropping to zero is as diagnostic as one spiking.

Two numerical guards, each a real bug that was fixed (see DD-4 and DD-10):
- **Spread floor.** A perfectly flat baseline makes z undefined; dividing by a raw
  epsilon yields ~1e9 "scores" that swamp the ranking and print as nonsense. The
  spread is floored at `SPREAD_FLOOR_FRAC` (1e-3) of the series' own magnitude, so
  a counter that sits at 0 then ticks to 2 scores highly but *comparably*.
- **Z cap.** Scores are clipped at `Z_CAP=999`, and the clip is rendered as
  "≥999z (flat baseline)", never as a measurement — a clipped score means "baseline
  had no variance", which is *weaker* evidence than a large finite z, not stronger.

**Budget (`select_panels`).** Given the scored list and `panel_budget`:
- Default (`ksigma`/`robust`) — plain top-K by score.
- `coverage` ranker — round-robin: every service gets one panel before any service
  gets a second, so one noisy service cannot consume the whole budget.
- Optional redundancy caps `max_per_family` / `max_per_service` (both off by
  default — see DD-11 below), with **overflow refill** so a too-aggressive cap
  never renders a half-empty grid.

`metric_family` collapses percentile and trailing-numeric suffixes, so
`..._p50_seconds`, `..._p90_seconds`, `..._p99_seconds` count as one family. (These
are the 50th-, 90th-, and 99th-percentile values of the same latency metric — three
views of one thing, which should not consume three of the twelve panels.)

### 1.3 Fault window — `infer_fault_window`

The shaded band is estimated from telemetry alone (never from the label — that would
paint the answer onto the image). It expands **outward from the single most
anomalous series' peak** while deviation stays above `max(3.0, 0.25 × peak)`, then
pads by `n/60`. Taking min/max over several series' peaks was rejected: two series
peaking at opposite ends would shade almost the whole canvas, which tells the model
nothing.

### 1.4 Layout and panels

The canvas is a matplotlib gridspec at aspect 0.66: **metric small-multiples fill
the left `grid_cols` columns; a narrower auxiliary column stacks on the right** in
this order — topology, legend table, logs, traces (each present only if its config
flag is on). A header line states case identity, how many of how many series are
shown, the ranker, and the reading key (shaded band = fault window, red trace =
|z|≥`HOT_Z`=10, x-axis = minutes from window start). The header never states the
label.

Panel renderers ([`RQs/vlmrca/render/panels.py`](../RQs/vlmrca/render/panels.py)):
- **`render_metric_panel`** — one series over elapsed time (DD-8: elapsed seconds,
  not row index, so the x-axis is physically meaningful), optional peak annotation,
  optional fault shading, optional per-panel normalisation; red trace when
  |z|≥`HOT_Z`.
- **`render_topology_panel`** — the service call graph. Nodes drawn
  least-anomalous-first so the most anomalous lands *on top* (not occluded), with
  overlap relaxation after `spring_layout`, coloured by **within-case rank** (not
  raw magnitude, which saturated most nodes to one colour), label colour chosen by
  fill luminance. Labels are `numbered` (with a legend table) or full `names` (DD-9).
- **`render_legend_panel`** — maps node numbers → service + absolute z, so
  rank-colouring does not lose the magnitude.
- **`render_log_panel` / `render_trace_panel`** — show the *change* across the fault
  window rather than the absolute level (DD-5): the log panel shows the shift in log
  volume, and the trace panel shows the change in p95 latency (the 95th-percentile
  request time — a standard "slow request" measure) before versus during the
  incident. Their clocks are aligned to the metric charts' time axis by matching
  overlapping windows (DD-6).

### 1.5 The manifest

Alongside the PNG, `compile_dashboard` emits a JSON manifest: case id, config +
fingerprint, image px, services, fault window, per-service anomaly scores, and one
entry per drawn panel with a stable `panel_id` (`M1…`, `T1`, `L1`, `G1`, `R1`).
This is what the agentic controller (RQ2) will address when it says "zoom panel M7",
and what lets a trajectory be replayed without re-rendering.

---

## 2. The design space — every `DashboardConfig` field

Every rendering behaviour is a field on
[`DashboardConfig`](../RQs/vlmrca/render/dashboard.py) (invariant 4: a behaviour without
a field cannot be ablated, and RQ4 is the ablation matrix). An ablation is one field
flipped — no new code. The fields, grouped by axis:

| Axis | Field | Default | What it does |
|---|---|---|---|
| — | `name` | `"v0"` | human label, written into the manifest |
| **A** selection | `panel_budget` | `12` | how many series earn a panel (of ~50–5000) — the highest-leverage knob |
| | `ranker` | `"ksigma"` | scoring/selection: k-sigma z · robust MAD · per-service coverage round-robin |
| | `max_per_family` | `0` (off) | cap panels per metric family; 0 = plain top-K |
| | `max_per_service` | `0` (off) | cap panels per service; 0 = off |
| **B** layout | `layout` | `"small_multiples"` | grid of per-series panels vs all series z-scored on one shared axis |
| | `grid_cols` | `3` | columns in the metric grid |
| **C** topology | `topology` | `"colored"` | draw the call graph: none · plain · rank-coloured |
| | `topology_labels` | `"numbered"` | node labels: index+legend vs full service names |
| | `max_topology_nodes` | `25` | truncate the drawn graph (AegisLab has 40–104 services) |
| | `show_legend_table` | `True` | side table mapping node number → service + absolute z |
| **D** annotation | `shade_fault_window` | `True` | shade the inferred fault band on each panel |
| | `annotate_extremes` | `True` | annotate each panel's peak value |
| | `normalize_panels` | `False` | z-score each panel's y-axis vs show raw units |
| **E** resolution | `long_side_px` | `1568` | output long-side px (1568 ≈ 1.15k image tokens on Anthropic) |
| **F** aux panels | `show_logs` | `True` | include the log-change panel |
| | `show_traces` | `True` | include the trace-delta panel |

`fingerprint()` is a 10-char md5 of the config; it keys the render cache and result
directories. **Modality** (`hybrid` / `image_only` / `text_only`) is *not* a
`DashboardConfig` field — it is prompt-side, passed to `run_experiment`. It is RQ1
axis G and is treated as one in the RQ1 design.

---

## 3. Why it is built this way

The load-bearing choices, each traceable to a recorded design decision in
[`plans/design_decisions.md`](../plans/design_decisions.md) and, for most of them,
to a bug found by *looking at a rendered image*.

- **Selection is the contribution, not rendering.** With 12 panels out of thousands,
  the question "which series does an SRE need to see" is the whole game. That is why
  `ranker` and `panel_budget` are axis A and why the scoring guards (DD-4, DD-10)
  matter: a single mis-scored flat counter can push the true root cause off the page.

- **Small multiples by default, overplot as the comparator.** Per-series panels with
  their own y-axis are legible at 7pt (the enforced font floor); overplotting many
  z-scored series on shared axes is denser but risks illegibility. Which one a VLM
  reads better is an open RQ1 question (axis B), so both exist and neither is assumed.

- **Colored topology, numbered labels, legend table (DD-9).** The topology panel
  exists to communicate one thing: which service is most disturbed and where it sits
  in the call graph. Occlusion, colour saturation, and unreadable labels each
  independently destroyed that on real cases. Rank-colouring uses the whole colour
  ramp regardless of score distribution; numbering + a legend keeps dense graphs
  legible while preserving the absolute magnitude.

- **Auxiliary panels show change, not state (DD-5); clocks aligned by overlap
  (DD-6).** A log or trace panel showing absolute volume tells the model nothing
  about the incident; showing the shift across the fault window does. The three
  telemetry streams carry different clocks, aligned by window overlap rather than by
  magnitude.

- **1568px long side (axis E, default).** ≈1.15k image tokens on Anthropic — enough
  to keep 12 panels plus the aux column legible, without paying for resolution the
  model cannot use. Whether 1024 saves tokens for free or 2048 buys accuracy is
  exactly what axis E screens; the default is a starting point, not a finding.

- **Redundancy caps default OFF (DD-11).** This is the one place where reasoning and
  measurement disagreed, and it is instructive. Capping *looked* obviously right:
  without it, one AegisLab case (104 services, 1154 series) filled all 12 panels with
  HTTP latency percentiles of one request path while the true cause, `mysql`, got no
  panel. With caps `(3,4)` the same case shows HTTP latency (3), JVM CPU (3),
  **mysql memory (2)**, filesystem (4) — the ground truth is represented. But the one
  A/B (Sonnet-5, AegisLab, n=20) gave capped **0.746** vs uncapped **0.797** (paired
  Δ −0.052, Wilcoxon p=0.345, d=−0.14) — within noise, point estimate mildly
  negative. A change justified by reasoning and weakly contradicted by the only
  measurement does not ship as a default; it stays an RQ1 axis to screen at n=100.
  *(That A/B originally reported a bootstrap CI; per the current metrics policy, A/B
  claims now rest on the paired Wilcoxon p and Cohen's d, both shown here.)*

- **Pure, deterministic, label-blind (invariants 2–3).** Seeded layout and sorted
  iteration make the renderer reproducible, which is what lets an A/B attribute a
  score difference to the config rather than to render noise, and what lets the
  render cache serve byte-identical images to every model in a bake-off.

### The working note that governs everything

Six real renderer bugs on the first day were found by *looking at the rendered
images*, not by tests or metrics — including a coordinate mismatch that made the
dashboard contradict its own ground truth, and a selection failure that filled every
panel with one metric family while the true cause got none. **The test suite passed
throughout.** The order is therefore fixed: **render, look, then measure.** Any
renderer change ends by regenerating a gallery and having the render-reviewer agent
run a perception probe before a single inference dollar is spent.

---

## 4. What is design vs. what is default-awaiting-evidence

To be honest about the current state, so RQ1 does not mistake a default for a
finding:

**Settled (measured or structurally required):** the leakage gate; the scoring
guards (DD-4, DD-10); elapsed-time x-axis (DD-8); topology draw order, overlap
relaxation, and rank colouring (DD-9); aux panels showing change with overlap-aligned
clocks (DD-5, DD-6); purity/determinism.

**Default, not yet evidence-backed (these are the RQ1 axes):** `panel_budget=12` and
`ranker=ksigma` (only one selection setting has been run); caps off (one n=20 A/B,
null); `small_multiples` (overplot never benchmarked); `long_side_px=1568`
(resolution never swept); the aux panels all on (never ablated individually); and
above all **modality** — the DD-11 result hints the metric panels may not be
load-bearing on AegisLab and the hybrid text may carry the signal, which is the
single most important thing RQ1 has to resolve because it bears on the central claim.

Untested at scale: dense AegisLab topologies (40–104 services) against
`max_topology_nodes=25`, and the coverage ranker at that service count.

See [`docs/rq1_design.md`](rq1_design.md) for how these open axes are turned into a
budget-structured experiment.

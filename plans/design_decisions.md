# Design decisions

Record of load-bearing choices. Never delete an entry; supersede it and link forward.

---

## DD-1: Reuse RL-SLM-RCA through a sys.path shim, not pip/vendor/submodule
**Date:** 2026-07-22 · **Status:** adopted

**Context.** This project must reuse the upstream project's dataset loaders,
task framing and scoring functions to be comparable with its published numbers.

**Decision.** A single module, `RQs/vlmrca/upstream.py`, inserts the upstream repo
root on `sys.path` and re-exports the permitted surface. It is the only
sanctioned import path; nothing else in the repo touches `sys.path`.

**Rationale.** Upstream has no `pyproject.toml`/`setup.py` and its importable
package is literally named `src` (verified: `src/__init__.py` exists, internals
use relative imports). `pip install -e` would therefore require editing the
upstream repo and would install a package called `src` into the environment,
colliding with anything. Vendoring would copy ~3k lines of actively-maintained
loaders and drift. A git submodule duplicates a large repo on shared scratch and
still needs the same path trick because of the package name.

**Alternatives rejected.** pip -e (impossible without editing upstream, pollutes
namespace) · vendoring (divergence) · submodule (duplication, no benefit).

**Consequences.** Upstream drift is a real risk, mitigated by
`check_upstream_pin()` warning on mismatch and every trajectory stamping the
observed commit. If genuine divergence ever occurs, vendor *then*, as a new DD.

---

## DD-2: Use the cached loader family (`src.baselines.dataset_loaders`)
**Date:** 2026-07-22 · **Status:** adopted

**Context.** Upstream has two loader families producing the same `DataCase`:
`src.data.*` and `src.baselines.dataset_loaders.*`.

**Decision.** Use `src.baselines.dataset_loaders.*`.

**Rationale.** Only that family memoises `DataCase` objects as pickles under
`$SCRATCH/eda_cache`. Measured: 0.45 s to load a cached RE2-OB case versus tens
of seconds of parquet parsing. 1141 cases are already cached. The RQ1 grid
re-loads the same cases many times, so this is the difference between a
tractable and an intractable screening loop.

**Consequences.** Depends on `$SCRATCH/eda_cache` staying populated; the loaders
fall back to parsing raw data if it is not, so this degrades rather than breaks.

---

## DD-3: Materialise and commit a frozen 480-case manifest
**Date:** 2026-07-22 · **Status:** adopted

**Context.** Upstream's `src/baselines/shared_scripts/case_sets.py:12` points
`DEFAULT_RQ_MANIFEST` at `configs/experiments/openrca_rq_case_manifest.json`,
which **does not exist on disk** (nor do the two held-out ID lists it falls back
to). Upstream pools were regenerated per run from seeded sampling.

**Decision.** Regenerate the pool once with the same seeded calls
(`stratified_sample`/`load_split`, seed 42, sizes 100/100/100/90/90) and commit
the result as `configs/case_manifest_480.json`.

**Rationale.** Seeded sampling is only reproducible if the underlying index
order is stable, and that order comes from directory scans. Committing the
resolved case ids makes the pool reproducible regardless. Every experiment then
provably scores the same cases.

**Consequences.** Exact set parity with upstream's runs is *assumed, not
verified*. If a like-for-like claim against a specific upstream table is needed,
cross-check case ids against upstream trajectories in `$SCRATCH/results/` first.

---

## DD-4: Bound anomaly scores; floor the spread by series magnitude
**Date:** 2026-07-22 · **Status:** adopted

**Context.** The first working renderer ranked `checkoutservice·socket` top with
a z-score of 2.0e9 and printed "max|z|=2000000000.0" on the panel.

**Decision.** When a baseline is perfectly flat, floor the spread at
`SPREAD_FLOOR_FRAC` (1e-3) of the series' own magnitude rather than an absolute
epsilon, and clip all scores at `Z_CAP` (999).

**Rationale.** Dividing by a raw epsilon turns any constant-then-moving counter
into a ~1e9 pseudo-z that swamps the ranking and renders unreadable captions.
Flooring by the series' own scale keeps such series ranked highly but
commensurably. After the fix the same case ranked `checkoutservice·cpu` first at
z=248 — which is the actual injected fault.

**Consequences.** Scores above `Z_CAP` are indistinguishable. Acceptable: the
ranking only needs to order panels, not quantify extreme excursions.

---

## DD-5: Auxiliary panels show change, not absolute state
**Date:** 2026-07-22 · **Status:** adopted

**Context.** The first log panel rendered "no error-level log lines matched" for
every RE2-OB case, and the trace panel showed absolute p95 latency. Inspection
showed RE2-OB logs are purely informational (zero occurrences of
error/exception/fail) and all trace status codes are 0.0.

**Decision.** The log panel falls back to per-service log-volume shift
(pre-window vs in-window) when the corpus has no error lines; the trace panel
reports p95 before vs during with a percentage delta instead of absolute p95.

**Rationale.** An error-only panel is permanently blank on such datasets — a
wasted sixth of the canvas. Volume shift is the signal that exists there, and it
generalises: a service that stops logging is as diagnostic as one that starts
erroring. Absolute p95 mostly encodes which service is intrinsically slow;
the delta encodes what the incident did, which is the question being asked.

**Consequences.** Both panels depend on a fault-window estimate. When none is
detectable the renderer falls back to splitting at the window midpoint.

---

## DD-6: Resolve log/trace time by overlap, not by magnitude
**Date:** 2026-07-22 · **Status:** adopted

**Context.** RE2-OB traces leave `timestamp` entirely NaN and keep the real
clock in `startTime` (microseconds), while its logs use nanosecond `timestamp`
and metrics use second-resolution `timestamp`. A magnitude-threshold heuristic
silently produced an empty during-fault group, showing "n/a" for every service.

**Decision.** `panels.resolve_time_seconds` tries each candidate time column at
each unit scale (1, 1e3, 1e6, 1e9) and keeps whichever places the most rows
inside the known metric window.

**Rationale.** Self-correcting rather than assumption-driven, and a genuine
failure to align surfaces as "no overlap" instead of a silently empty group —
which had already produced a plausible-looking but meaningless panel.

---

## DD-7: Sonnet for iteration, Opus for headline runs
**Date:** 2026-07-22 · **Status:** adopted

**Context.** M1 smoke ran on `claude-opus-4-7`. The RQ1 grid needs many more
calls, and the budget for the project is ~$200–400.

**Decision.** `claude-sonnet-5` (verified working via Bedrock) is the default
for RQ1/RQ2 screening; Opus and the rest of the panel are reserved for frozen
configs at L2 (480 cases).

**Rationale.** Screening decisions are relative comparisons between dashboard
configs, which do not need the strongest model. Self-hosted Qwen2.5-VL-72B is
the zero-marginal-cost alternative once the vLLM path is verified.

**Consequences.** A dashboard axis that helps Sonnet but not Opus would be
mis-screened. RQ3 re-runs the frozen configs across the full panel, which
surfaces such an interaction if it exists.

---

## DD-8: Plot metric panels against elapsed time, not row index
**Date:** 2026-07-22 · **Status:** adopted

**Context.** The render-reviewer agent found that in one RE2-OB case the shaded
fault window sat at 73–78% of the axis while the manifest placed it at 93–100%.
That case carries 1186 rows spanning 929 s with a duplicate-timestamp tail: the
series was plotted at `arange(len(ts))` while the band came from
`searchsorted(ts, window)`, so uneven sampling silently decoupled the two.

**Decision.** Plot against `(ts - ts[0]) / unit`, shade with the same
coordinate, and derive tick labels from it. Also draw thin lines at the window
edges so short windows stay locatable.

**Rationale.** The consequence was not cosmetic: the true root cause's CPU
excursion appeared to begin *two minutes before* the fault window, so a model
following the dashboard's own legend would reason its way to rejecting the
correct answer. One shared coordinate for data, band and ticks removes the
entire class of bug. Tick labels were wrong for the same reason and are fixed
by the same change.

**Consequences.** Panels for cases with clustered sampling now show visible
density variation, which is honest — the previous uniform spacing was a lie
about when samples were taken.

---

## DD-9: Draw topology nodes anomaly-ascending, with overlap relaxation and rank colouring
**Date:** 2026-07-22 · **Status:** adopted

**Context.** Review found the highest-anomaly node occluded by an unrelated
neighbour in 3 of 4 sampled dashboards. `spring_layout` allowed overlaps, and
nodes were drawn in alphabetical order, so which node got buried was arbitrary.
Separately, `log1p` colour mapping saturated 8 of 11 nodes to the same maroon on
one case, and dark fills carried near-black labels.

**Decision.** Relax overlaps after layout (minimum centre separation), draw
nodes least-anomalous first so the most anomalous lands on top, colour by
within-case rank rather than magnitude, choose label colour by fill luminance,
disable clipping and add axes margins.

**Rationale.** The topology panel exists to communicate one thing — which
service is most disturbed and how it sits in the call graph. Occlusion,
saturation and unreadable labels each independently destroy that. Rank mapping
uses the whole colour ramp regardless of how scores are distributed, which
neither linear nor log mapping does.

**Consequences.** Node colour now encodes ordering, not magnitude; the legend
table still prints absolute z so the magnitude is not lost.

---

## DD-10: Never print the score clip sentinel as a measurement
**Date:** 2026-07-22 · **Status:** adopted

**Context.** `Z_CAP` (999) rendered as "peak +999.0z", out-ranking a genuine
419z excursion that was the true root cause.

**Decision.** Render clipped scores as ">=999z (flat baseline)".

**Rationale.** The clip means "the baseline had no variance, so z is undefined",
which is weaker evidence than a large finite z, not stronger. Printing it as a
number invites exactly the wrong inference.

**Consequences.** Ranking still places clipped series first. Down-weighting them
in `kpi_select` — particularly integer counter series such as socket counts,
which produced several spurious 250–500z panels — is an open RQ1 question, not
yet decided.

---

## DD-11: Panel-redundancy caps exist as an RQ1 axis, default OFF
**Date:** 2026-07-22 · **Status:** provisional — implemented, not adopted as default

**Context.** Rendering an AegisLab case (104 services, 1154 metric series) showed
all 12 panels occupied by `hubble_http_request_duration_p{50,90,99}_seconds`
across a handful of services — twelve views of one phenomenon. The case's ground
truth was `mysql`, which received no panel at all.

**Decision.** `select_panels` gained `max_per_family` and `max_per_service`,
both `DashboardConfig` fields, **both defaulting to 0 (off)**. Families are
computed by stripping percentile and trailing-numeric suffixes.

**Rationale.** The panel budget should maximise information, not maximise z.
Correlated percentile variants of one metric are near-duplicates, and spending
the budget on them is what made the true cause invisible. After the change the
same case shows HTTP latency (3), JVM CPU (3), **mysql memory (2)** and
filesystem (4) — the ground truth is represented.

**Measured, and it did not help.** AegisLab, 20 cases, claude-sonnet-5,
caps (3, 4) vs uncapped:

| condition | MRR | 95% CI | Top@1 | parse |
|---|---|---|---|---|
| capped | 0.746 | [0.558, 0.917] | 0.700 | 0.95 |
| uncapped | **0.797** | [0.653, 0.933] | 0.700 | 1.00 |

Paired over the same 20 cases: delta -0.052, CI [-0.177, 0.046], Wilcoxon
p=0.345, d=-0.14. Within noise, point estimate mildly negative.

**Therefore the default stays off.** The reasoning for capping was sound and the
"true cause has no panel" observation was real, but a change justified by
reasoning and contradicted (weakly) by the only measurement should not ship as a
default. It stays as an RQ1 axis to screen at n=100.

**What this hints at, and what to test next.** If filling the panel budget with
twelve near-duplicate latency percentiles costs nothing, the metric panels may
not be what the model is actually using on AegisLab — the log/trace tables and
topology in the hybrid text may be carrying the signal. That is directly
testable with the RQ1 modality axis (`image_only` vs `hybrid` vs `text_only`)
and should be run early, because it bears on the project's central claim.

**Open.** Several AegisLab panels are integer counters with flat baselines that
clip at `Z_CAP` and outrank finite excursions; whether to down-weight them is
still undecided (see DD-10).

---

## DD-12: Reproducible decoding is a serving-flag problem, and it is a precondition for RQ1

**Date:** 2026-07-26 · **Status:** adopted

**Context.** Nothing had ever run the same configuration twice. Two
`claude-sonnet-5` runs of one dashboard config over the same 20 AegisLab cases
(`smoke_aegislab_sonnet` 0.817, `aegis_dedup_off` 0.798) turned out to disagree
on **5 of 20 cases** — paired sd 0.255, a ±0.112 MRR replicate band at n=20 and
±0.050 at n=100. [docs/rq1_design.md](../docs/rq1_design.md) §5 adopts a
dashboard level at ΔMRR ≥ +0.03. Against that much noise the rule needs n ≈ 570
before it can fire, so the RQ1 grid was not viable as designed.

Two causes, both silent. `_call_openai` never passed `cfg.temperature`, so vLLM
applied each model's shipped `generation_config.json` — the Gemma bake-off cells
ran at temperature 1.0 / top_k 64 / top_p 0.95 (vLLM logged the override) while
the Qwens ran greedy via `VLMConfig.extra`. The Bedrock path passed no
temperature at all.

**Decision.** Sampling parameters are real `VLMConfig` fields passed explicitly
on every backend, `extra` is empty in the registry, and servers run:

    --generation-config vllm --seed 42
    --no-enable-prefix-caching --no-enable-chunked-prefill

**Rationale, and the part that was not obvious.** Fixing the client was
necessary but not sufficient. With prefix caching on, two identical
`gemma-4-e4b` runs still disagreed on **16 of 20** cases: the second ran against
a KV cache the first had warmed, and the changed reduction order flips a token
that then cascades through the rest of an autoregressive answer. With the cache
flags off the same check is **0 of 20, paired sd 0.0000**.

`--enforce-eager` is *not* required — ablated separately, it also passes but
costs 19.0 s/case against 5.9, a 3.2× tax for no gain.

**Consequences.**

- The two recipes are each internally reproducible yet give **different MRRs on
  the same 20 cases** (0.529 with CUDA graphs, 0.475 with `--enforce-eager`),
  because the kernel paths differ. Determinism makes a recipe's numbers
  repeatable, not recipe-independent. The recipe is therefore part of the
  experiment definition and must be held identical across every arm.
- `gemma-4-26b-a4b` could be rescued from its DNF by `--enforce-eager` skipping
  the MoE autotune, but it would then be the only model on a different kernel
  path. It gets a longer health deadline instead, and leaves the panel if that
  is not enough rather than being bought back with a confound.
- **The +0.03 threshold in `docs/rq1_design.md` §5 was chosen before anything
  measured run-to-run noise and should be re-derived**, now that the replicate
  band is 0.0000, from the observed between-config spread. Not yet done.
- Every A/B before this date carries sampling noise of roughly this size. The
  DD-11 caps result (Δ −0.052, p 0.345) is well inside a ±0.112 band and should
  be treated as un-measured rather than as a weak negative.

**Cross-job verification (added 2026-07-26, after the fact).** The gate proves
*within-job* reproducibility: two replicates against one server process. What the
design actually needs is stronger, because arms are compared across jobs — Array
B's thinking-on runs are paired against Array A's thinking-off runs, submitted
separately and possibly days apart.

Checked directly: gate job 18552813 and array job 18553844 task 4, separate SLURM
jobs with separate vLLM server processes, agree on **20 of 20 shared cases**
(gemma-4-e4b, cov30, `RENDERER_VERSION` 4). So the recipe is reproducible across
processes and allocations, not merely within one. Numbers from different jobs are
directly comparable, which is what makes the paired designs in this plan valid.

---

## DD-13: Panel selection reserves slots for distinct services; coverage is a budget problem

**Date:** 2026-07-26 · **Status:** adopted (as an axis; `cov30` is the working default)

**Context.** DD-11 recorded one AegisLab case where all 12 panels went to one
metric family and the true cause got none. Measured across the whole screening
set, that is not an anecdote: at `v0` the injected service gets **no metric
panel on 34 of 100 cases**, is in neither metrics nor topology on 6, and appears
in no panel at all on 2. The 12-panel budget reaches a median of 6 distinct
services, and on one case exactly 1.

Running the modality arms — the thesis test — on a dashboard that omits the
answer a third of the time would understate the representation rather than
measure it.

**What was measured before choosing.** The ranking is not at fault. The injected
service's median rank among ~51 services is 3–4, it is **never** unrankable, and
no alternative service-level score (sum of top 3, mean of top 3, count above
z=10, median) beats the incumbent max. Coverage is bounded by how many services
the budget can reach:

| selector | GT gets a panel | services shown | services with ≥2 panels |
|---|---|---|---|
| budget 12, top-K (`v0`) | 66% | 6.0 | 2.4 |
| budget 12, round-robin (`cov12`) | 82% | 12.0 | **0.0** |
| budget 30, top-K | 82% | 12.1 | 5.3 |
| budget 30, reserve 20 (`cov30`) | **90%** | 20.3 | 3.7 |
| budget 30, round-robin (`cov30f`) | 96% | 30.0 | **0.0** |

**Decision.** `selector="coverage_first"` with `coverage_services` as the dial:
reserve that many slots for distinct services (best series of each), spend the
rest on plain top-K. `cov30` is the working default.

**Rationale.** Full round-robin — which is what the pre-existing but never-used
`ranker="coverage"` did — buys its last points of coverage by destroying depth
entirely, and several correlated series moving together is often exactly what
marks an origin rather than a victim. The dial keeps both extremes reachable, so
plain top-K remains the RQ4 ablation baseline.

**Consequences and the caveat that matters.** `cov30` changes coverage (66% →
90%) *and* density (6.0 → 20.3 services shown) at once. A null result on
`cov30` vs `v0` is therefore ambiguous between "coverage does not help" and "the
added density costs what the coverage gains". `cov12` — round-robin at the
`v0` budget, 82% coverage at unchanged density — is the pre-registered follow-up
that separates them. This is written down before the run, not after.

Note also that "no metric panel" is not a blackout: on
`aegislab_ts4-ts-auth-service-corrupt-pldpdm`, missed by both configs, the trace
table still surfaces the true cause at the top with a 126918% latency delta. The
`image_only` arm should be read with that in mind.


**First measured evidence, 2026-07-26 (n=100, Array A).** The coverage argument
above was made from render statistics alone -- no model had yet been run on the
two configs. The first two completed model pairs let it be tested directly.
`hybrid` minus `text_only` on cov30, per fault bucket, against that bucket's
coverage:

| fault bucket | n | cov30 coverage | delta gemma-4-e4b | delta gemma-4-26b-a4b |
|---|---|---|---|---|
| K8s_Control | 11 | 100% | +0.394 | +0.333 |
| JVM | 20 | 100% | +0.181 | +0.300 |
| HTTP | 54 | 87% | -0.060 | +0.108 |
| Network | 15 | 80% | -0.120 | -0.267 |
| **all** | 100 | **90%** | **+0.029** | **+0.115** |

**CORRECTION, same day, before this was used for anything.** The paragraph
below over-claims. The correlation is real but mostly **confounded with case
difficulty**, and the causal effect is far smaller.

The test: `text_only` never sees the dashboard, so if coverage were about the
dashboard, coverage should not predict `text_only` accuracy. It does, strongly:

| model | text_only on covered (n=90) | on uncovered (n=10) | gap |
|---|---|---|---|
| gemma-4-e4b | 0.442 | 0.145 | +0.297 |
| gemma-4-12b | 0.561 | 0.050 | +0.511 |
| gemma-4-26b-a4b | 0.354 | 0.150 | +0.204 |

The mechanism is obvious in hindsight and is a property of the selector: panels
are chosen by anomaly score, so a case whose true service shows a strong anomaly
both *gets a panel* and *is easy for every modality*. A case whose true service
is quiet gets no panel and is hard for everything. "Covered" is close to a
restatement of "easy".

The causal quantity is the difference-in-differences -- (hybrid - text_only) on
covered cases minus the same on uncovered cases: **+0.14, -0.01, +0.24** for the
three models. Positive for two of three, but an order of magnitude less
impressive than the raw correlation, and computed against only 10 uncovered
cases, so all three are individually worthless as estimates.

**The design conclusion reverses.** Coverage is not the lever it looked like.
See the cov12 result recorded below, which tests it directly and finds that
*raising* coverage makes things worse.

---

The ordering is monotonic in coverage for **both** models independently. Where
every case has an accepted answer on the dashboard, the image is worth +0.18 to
+0.39; in the worst-covered bucket it is *negative* in both. That is the first
evidence in this project tying a renderer design parameter to task accuracy, and
it says the dashboard does not merely fail when it omits the answer -- it
actively misleads, presumably by drawing attention to the services it does show.

Two consequences. Panel coverage becomes a first-class objective rather than a
hygiene property, which is an argument for pushing past cov30. And the pooled
thesis-gate number is a **cancellation**: for gemma-4-e4b the positive and
negative buckets contribute +0.080 and -0.050 against a net of +0.029, so the
absolute contributions are 4.5x the net. Reporting only a pooled modality delta
would have hidden an effect that is large and real in half the data.

**A measurement note worth keeping.** The 66%/90% figures above are *lenient*:
a case counts as covered when any accepted ground-truth candidate has a panel,
which is the same rule upstream's scorer applies. Measured strictly against the
single primary `ground_truth`, the same renders give 56% and 79%. The gap is
large because **69 of 100** AegisLab cases are multi-label -- the fault injection
names both a source and a target service. Quote the lenient numbers, because
they are the ones consistent with how the answers are scored, but state which
definition is in use: the two differ by 11 points and are easy to conflate.


## DD-13a — Depth beats breadth: coverage-first selection is withdrawn

**Date.** 2026-07-27. Supersedes the coverage argument in DD-13.

**What was run.** The `cov12` arm DD-13 pre-registered, plus the `cov30` arms,
each paired against `v0` on the same 100 AegisLab cases with the same model and
the same decoding. `cov12` differs from `v0` in exactly one field, the selector,
holding panel count (12), pixels (1568) and grid (3 columns) fixed -- so only
*which series occupy the panels* changes.

| config | panels | distinct services | services with >=2 panels | coverage |
|---|---|---|---|---|
| v0 | 12 | 6.0 | 2.4 | 66% |
| cov12 | 12 | 12.0 | **0.0** | 82% |
| cov30 | 30 | 20.3 | 3.7 | 90% |

**Result — six paired comparisons, all negative.**

| model | cov12 - v0 | cov30 - v0 |
|---|---|---|
| gemma-4-e4b | **-0.079** (p=0.032) | -0.014 |
| gemma-4-12b | -0.034 | -0.005 |
| gemma-4-26b-a4b | -0.052 | -0.057 |

Sign test over all six: p = 0.016. Individually most are below the resolution of
an n=100 comparison (~0.10), but nothing favours coverage-first anywhere.

**Decision.** `selector="coverage_first"` is withdrawn as a default. `v0`'s plain
top-K remains the incumbent. `cov12`/`cov30` stay in the preset table as RQ4
ablation levels, since knowing that coverage costs accuracy is itself a result.

**Why, and this is the part worth carrying forward.** DD-13 argued that spending
panels on distinct services buys coverage cheaply. It does buy coverage -- 66% to
82% at identical density, exactly as designed. It just is not worth what it
costs. Top-K puts ~2.4 panels on each of ~6 services; round-robin puts exactly
one on each of 12. **Several correlated series moving together on one service is
what distinguishes an origin from a victim.** One anomalous chart each for twelve
services is twelve equally plausible suspects. DD-13 named this risk when it
chose the reserve dial over full round-robin, then the coverage statistics
argued past it; the measurement settles it in favour of the original worry.

The corollary for RQ1: **the dashboard's value is in depth per service, not
breadth of services.** That is a directly testable follow-up -- raise panel
budget while holding services shown fixed -- and a better use of the RQ1 grid
than further coverage tuning.


### DD-13a amendment — the effect is Gemma-only, and the claim is weakened

**Date.** 2026-07-27, a few hours after DD-13a was written. The Qwen arms of
Array A had not finished when it was recorded.

DD-13a said "six paired comparisons, all negative, sign test p = 0.016". That was
true of the six that existed — but all six were **the same model family**: three
Gemmas crossed with two configs. With the Qwens in, the sign reverses:

| model | cov12 - v0 | cov30 - v0 |
|---|---|---|
| gemma-4-e4b | -0.079 | -0.014 |
| gemma-4-12b | -0.034 | -0.005 |
| gemma-4-26b-a4b | -0.052 | -0.057 |
| qwen3.5-4b | *(not run)* | **+0.013** |
| qwen3.6-27b | *(not run)* | **+0.024** |

Eight comparisons, six negative: sign test p = 0.145, **not significant**. And
every one of the eight is below the resolution of an n=100 comparison (~0.10),
so none is individually meaningful either.

**Revised conclusion.** Plain top-K stays the incumbent, but on much weaker
grounds than DD-13a claimed: the Gemma family consistently prefers it, the two
Qwens marginally prefer cov30, and nothing is resolvable. "Depth beats breadth"
is a Gemma-family observation, not an established property of the task.

**What would settle it.** `cov12` was only ever run on the three Gemmas, which is
exactly the comparison that isolates coverage from density — so the family split
is measured on the confounded axis (cov30) and unmeasured on the clean one.
Running `cov12` on the two Qwens is the cheap next step, ~1 GPU-hour, and it is
the difference between "a family quirk" and "a design principle".

**A note on how this went, since it is the third time today.** The +0.03
threshold estimate, the coverage-accuracy claim, and now this were each recorded
from real measurements and each had to be weakened or reversed when more data
arrived. In all three the error was the same shape: a clean pattern across
everything available, where "everything available" was a biased slice — one
n=20 pair, one selector's easy cases, one model family. The lesson is not "wait
for all the data", which would stop all recording. It is that a claim should
carry the slice it was measured on **in the claim itself**, so the next reader
sees the boundary without re-deriving it.


### DD-13a second amendment — there is no reliable selector effect

**Date.** 2026-07-27, after `qwen3.6-27b` completed the last `cov12` arm.

The first amendment said the effect was Gemma-only and pointed at `cov12` on the
Qwens as the missing evidence, because `cov12` is the arm that isolates the
selector from density. Both Qwen `cov12` arms have now run. The clean axis, all
five models with a usable pair:

| model | cov12 - v0 |
|---|---|
| gemma-4-e4b | -0.079 (p=0.032, flagged underpowered) |
| gemma-4-26b-a4b | -0.052 |
| gemma-4-12b | -0.034 |
| qwen3.5-4b | -0.034 |
| **qwen3.6-27b** | **+0.050** |

Sign test 4 of 5: **p = 0.188, not significant.** Every one of the five is below
the ~0.10 that an n=100 paired comparison can resolve, and the only nominally
significant one carries the underpowered flag, meaning its magnitude is likely
inflated.

**Final position: there is no reliable selector effect at this sample size.**
Not "depth beats breadth" (DD-13a), not "coverage helps" (DD-13). Plain top-K
stays the incumbent by the tie-break rule in `docs/rq1_design.md` §5 — prefer the
simpler and cheaper level on a draw — and not because it was shown better.

**The result that does stand out.** `qwen3.6-27b` with `cov12` scores **0.524**,
the highest MRR of any open-model arm anywhere in this cell, above its own `v0`
(0.474) and `cov30` (0.499). One cell, one model, unresolvable on its own — but
the strongest model in the panel preferring the selector the other four dislike
is the opposite of a family story, and it is worth a targeted re-run before the
selector is written off.

**Process note, since this is the second amendment to one DD in one day.** After
the first amendment I wrote that a claim should carry the slice it was measured
on. The direct application was to wait ~30 minutes for the fifth model rather
than record "all four negative on the clean axis", which is what four of five
points supported and what I was about to write. The fifth reversed it. The
waiting cost nothing and the claim would have been wrong; that is the whole
argument for the rule, now with an instance attached.

---

## DD-14 — The Claude 5 reference arms cannot be made deterministic

**Date.** 2026-07-26.

**Context.** DD-12 closed the ±0.112 MRR replicate band by sending explicit
sampling parameters and turning off vLLM's prefix caching and chunked prefill.
That fix was written to apply to every backend, including the Bedrock path used
for the frontier reference arms. A 2-case probe before submitting the reference
job returned a parse rate of 0.000:

```
ValidationException ... The model returned the following errors:
`temperature` is deprecated for this model.
```

**What was measured.** Probing each Bedrock model in the registry with a bare
`inferenceConfig` and again with `temperature: 0.0`:

| model | no sampling params | `temperature: 0.0` | `topP: 1.0` |
|---|---|---|---|
| claude-opus-4-7 | OK | **rejected** | **rejected** |
| claude-sonnet-5 | OK | **rejected** | **rejected** |
| claude-sonnet-4-6 | OK | OK | — |
| claude-sonnet-4-5 | OK | OK | — |

The split is generational: the Claude 5 models accept neither parameter.

**Decision.** `VLMConfig.temperature` and `top_p` become `Optional[float]`,
where `None` means *omit the key entirely* — an explicit `null` is still a
rejected parameter. Both are `None` for `claude-opus-4-7` and `claude-sonnet-5`.
Two tests pin it, because the failure mode is a full paid reference run that
returns nothing.

**The consequence, which is a design constraint rather than a bug.** The
frontier reference arms cannot be run greedy. The replicate band measured on
Sonnet-5 — 5 of 20 cases differing between two runs of one config, ±0.112 MRR at
n=20 and ±0.050 at n=100 — is **irreducible on that path**. It was previously
recorded as a defect that DD-12 fixed; for these two models it is not fixable.

Three things follow, and they are not all bad:

1. **The open-weight path is the deterministic one** (0 of 20 differing under the
   DD-12 recipe). That is now an argument *for* screening the RQ1 grid on an open
   model, independent of cost — the original argument was only about GPU-hours.
2. **The paired tests remain valid.** Stochastic decoding adds noise to each
   case's score; it does not bias the paired difference. A Wilcoxon over n=100
   still tests the right null, with less power than it would have had.
3. **Point estimates from Sonnet carry ±0.050 and must be reported with it.**
   This bites hardest on the selector A/B (`cov30` vs `v0`), whose expected
   effect is the same order as the band. The thesis gate — hybrid vs text_only —
   is expected to be much larger than 0.050, so it survives; if it comes back
   small, replicate-averaging the two arms is the escalation, at roughly the cost
   of the run again.

**Also corrected here.** The rank-transfer check in the plan was a Spearman
correlation over three modality arms. With n=3 there are only six orderings, so
the smallest attainable p-value is 0.167 — the check as specified could not
return a significant result under any outcome. The reference arms now mirror
Array A's four arms exactly, which takes the floor to 0.042. That is still
descriptive; the load-bearing transfer evidence is the paired selector A/B, which
has n=100 on both models.

---

## DD-15 — Thinking mode: the small Qwens do not terminate, at any budget tried

**Date.** 2026-07-27.

**Context and the mistake being corrected.** The 2026-07-24 devlog concluded
"thinking hurts the small Qwens and should stay off". Earlier today I argued that
conclusion rested on an artifact: `qwen3.5-9b` had hit `stop_reason=length` at
exactly 16384 on 8 of 20 cases, and on the 12 that finished it scored 0.694 with
thinking against 0.417 without. I wrote that "the budget, not the reasoning, was
the problem" and re-ran the axis with the ceiling doubled to 32768 and the
context window raised to 49152 so a chain of thought could terminate.

**What happened.** Measured ~2.5 hours in, before the arms completed:

| arm | truncated | parsed | median output tokens |
|---|---|---|---|
| think qwen3.5-4b | **11 / 11** | **0** | 32768 (the ceiling) |
| think qwen3.5-9b | **10 / 10** | 1 | 32768 |
| think qwen3.6-27b | 2 / 9 | 7 | 14603 |

Doubling the budget did not let the small models finish; it let them generate
twice as much before being cut off. They expand to fill whatever they are given.
Tasks 0 and 1 were cancelled at that point rather than spending ~25 more
GPU-hours to produce an arm of zeros. The 27b terminates normally and continues.

**Decision.** Thinking stays **off** for `qwen3.5-4b` and `qwen3.5-9b` — which is
where 2026-07-24 landed, so that conclusion is reinstated. It is kept as a live
axis for `qwen3.6-27b`, the only Qwen that finishes.

**The correction that matters more than the decision.** My argument for re-opening
this was itself confounded, in the same way as the coverage claim in DD-13. The
"0.694 with thinking vs 0.417 without" was computed on the 12 of 20 cases where
thinking *happened to terminate*. Termination is not random: a model finishes
quickly on cases it finds easy and loops on cases it finds hard. So conditioning
on "the trace finished" conditions on "the case was easy", and the surviving
subset flatters thinking exactly as "GT got a panel" flattered coverage. Both
times the fix was to find a quantity that is not selected on the outcome —
here, that no budget produces termination at all.

**The generalisable rule.** Before comparing a subset that survived some filter,
ask whether the filter is correlated with the outcome. If it is, the comparison
measures the filter. Two of today's findings failed this test, so
`scripts/compare_runs.py` now prints truncation counts on every comparison and
recomputes the delta on non-truncated cases.

**Open and not settled by this.** Whether thinking helps *when it terminates* is
still unmeasured for the small Qwens, and cannot be measured this way. Options,
none run: a hard stop sequence that forces an answer, a two-stage prompt that
separates reasoning from the final JSON, or accepting non-termination as the
measured property of these models on this task and reporting it as such.


### DD-15 amendment — the 27b fails too; the axis is unmeasurable

**Date.** 2026-07-27, after `qwen3.6-27b`'s thinking arm completed (14h33m).

DD-15 kept thinking as a live axis for `qwen3.6-27b` on the grounds that it was
"the only Qwen that finishes". That was read at n=9, where it had truncated 2.
At n=50 it had truncated **21 — 42%** — with parse rate 0.580, so the arm is
excluded by the same parse-rate rule that excluded the others.

| | n | MRR | parse | truncated | output tokens | s/case |
|---|---|---|---|---|---|---|
| thinking OFF | 100 | 0.499 | 1.000 | 0 | 1576 | 65 |
| thinking ON | 50 | 0.420 | 0.580 | 21 | 20484 | 1030 |

The paired difference reads -0.253 (p=0.0018) but is truncation-driven; on the
29 cases where both terminated it is -0.040. **Neither number is usable**, and
the second is the exact selection bias DD-15 itself warned about: conditioning on
"the trace finished" conditions on "the case was easy".

**Revised decision.** Thinking is **off for all three Qwens**, and the axis is
**unmeasurable in this design** rather than measured and rejected. Every budget
tried — 16384, then 32768 — is filled rather than used. The 16x wall-clock cost
(1030 vs 65 s/case) means re-running at a larger budget is not worth it on a
guess; the open options from DD-15 stand (a forced stop sequence, a two-stage
prompt that separates reasoning from the final JSON, or reporting
non-termination as a measured property).

**And it is the fourth instance of the same error in one day.** "The 27b
terminates normally" was generalised from 9 episodes. The others were one n=20
pair, one selector's easy cases, and one model family. The rule written after the
third — carry the slice inside the claim — would have caught this one too, had it
been applied to a sentence written in passing rather than to a recorded finding.
That is the refinement worth keeping: the rule is not for DDs, it is for any
claim, including the ones that feel like status updates.

---

## DD-16 — The thesis gate tests the wrong axis; the dashboard's case is efficiency

**Date.** 2026-07-27.

**The gate as written.** `docs/rq1_design.md` §4 and the DD-13 cell config both
define the thesis test as `MRR(hybrid) > MRR(text_only)`: does adding the
dashboard to the evidence text improve accuracy. Across four clean open models
the answer is no — mean +0.026, nothing significant after Bonferroni — and the
report prints STOP AND ESCALATE.

**What the `image_only` arms show instead.** Those arms exist to separate "cannot
localise" from "cannot read the chart", and were described in the array header as
"diagnostic rather than decisive". They turn out to be the decisive ones.

| model | image only | tokens | text only | tokens | token ratio | accuracy kept |
|---|---|---|---|---|---|---|
| qwen3.5-4b | 0.398 | 5074 | 0.413 | 8330 | 1.6x | **96%** |
| qwen3.6-27b | 0.429 | 5074 | 0.482 | 8330 | 1.6x | **89%** |
| gemma-4-26b-a4b | 0.257 | 2755 | 0.333 | 9252 | 3.4x | 77% |
| gemma-4-12b | 0.168 | 2755 | 0.510 | 9252 | 3.4x | 33% |
| gemma-4-e4b | 0.112 | 2751 | 0.412 | 9248 | 3.4x | 27% |

For the three models that can read a chart at all, a **rendered dashboard alone
reaches 88% of the accuracy of the full serialised telemetry using half the input
tokens**, and none of the three per-model differences is resolvable at n=100.

**Why this matters more than the gate result.** "The dashboard is the
representation" was operationalised as *more accurate than text*. The measurement
says it is *comparably accurate at roughly half the cost*, which is a different
and defensible claim — and it is the one CLAUDE.md already names as the M5
headline deliverable: "the accuracy-vs-tokens/case Pareto frontier ... the answer
to what does a dashboard token buy." The gate was never testing that.

**Decision.** The thesis test is restated on two axes rather than one:

1. **Accuracy** — does hybrid beat text_only? Currently no, for open models.
2. **Efficiency** — does image_only reach comparable accuracy at materially fewer
   tokens? Currently yes, for models that can read charts.

Failing (1) while passing (2) is a result, not a refutation. The escalation in
`RQs/RQ3/scripts/rq3_screening_report.py` should say so instead of reading a null on axis
1 as the project's central claim being in question.

**Caveats, none of which the above should be quoted without.** `image_only` is
*lower* in every one of the five models — the claim is efficiency, not parity.
"Not significant" here partly means "n=100 cannot resolve 0.05". And two of five
models score 0.11-0.17 from the image alone, so this depends entirely on the
model being able to read a chart.

**A concrete follow-up this exposes.** Gemma spends 2755 image tokens on the same
dashboard that Qwen spends 5074 on, and Gemma is the family that cannot read it
(27%, 33%, 77% against Qwen's 96% and 89%). That is consistent with Gemma
downsampling the 2048px render past legibility rather than lacking the
capability. Rendering at a resolution matched to each vision encoder, and
re-measuring `image_only`, is the cheapest way to find out — and if it is a
tokenization artifact, the Gemma numbers throughout this cell are understated.

---

## DD-17 — The metric grid was blank on the sparse datasets, and the scorer preferred it that way

**Date.** 2026-07-28 · **Status.** adopted · `RENDERER_VERSION` 4 → 5

**What was wrong.** Asked to look at the dashboards, the user's first observation
was that most panels were "just a single bar in the plot with y axis is
different". That is exactly what they were, and it was three defects compounding.

1. **The data was invisible.** `metrics_df` is a pivot over a *union* timestamp
   index, so each column carries values only on the timestamps its own scraper
   wrote. On AegisLab that is 8–96 valid samples in a 1064-row frame — the HTTP
   latency family has 10. `render_metric_panel` handed the raw array to
   `ax.plot`, which breaks a line at every NaN, so ten samples became ten
   zero-length segments and the panel drew no trace at all.
2. **The ranker preferred exactly those columns.** `score_series` accepted any
   column with three non-NaN baseline points, and three samples of a slow counter
   look perfectly flat, so the spread collapsed to the magnitude floor and the
   series scored `>=999z` on noise. A quarter of all v0 panels carried that
   sentinel. The columns least able to be drawn were the ones most likely to win
   a panel.
3. **The band was the bar.** `infer_fault_window` expanded in row space, where
   one NaN neighbour halts the walk immediately. Median shaded width was 2.6% of
   the window — about 8 px in a 324 px column.

**Fixes.** Plot the finite samples (with point markers below
`SPARSE_MARKER_MAX`, so interpolation is distinguishable from measurement);
require `MIN_BASELINE_VALID = 8` baseline points before trusting a column's own
spread and otherwise borrow the median relative spread of its metric family
(`FAMILY_FLOOR_FRAC`), declining to score a thinly-sampled column with no
comparable sibling; expand the fault window between *samples* via a shared
`valid_deviation` helper; and floor the drawn band at `MIN_BAND_FRAC` of the axis
while leaving the manifest's inferred timestamps untouched.

**Measured on AegisLab, v0, before → after.** Sentinel share 25% → 11% (n=6) and
21% at n=40; median band width 2.6% → 37.6%; median valid samples per panel 95;
and — unplanned — **injected-service panel coverage 66% → 77.5%**. The DD-11
pathology fixed itself: on `ts0-mysql-partition` the true `mysql` cause
previously got no panel at all while twelve HTTP-latency percentiles took the
grid; it now holds two.

**What this invalidates.** Every committed result. More pointedly, it is a live
confound for DD-16: the `image_only` arms were scored against a dashboard whose
metric grid was, on AegisLab, essentially empty. That arm was measuring the
topology thumbnail and the two aux tables. The efficiency claim is not thereby
wrong, but it was measured on less image than intended and should be re-run.

**Rejected: recalibrating `HOT_Z` in the same change.** Red is supposed to mark
severe excursions and currently fires on 98.5% of AegisLab panels, so it carries
no information. But the measurement refuses a fixed replacement: median |z| among
*selected* panels is 17.8 on RE2-OB, 177.6 on AegisLab and 206.8 on AIOPS-22.
No single constant discriminates on all three. The honest options are a
within-case rank threshold (the DD-9 precedent) or a per-dataset constant, and
both are rendering-behaviour changes that deserve their own config axis and their
own screening rather than a free ride on this version bump. Left at 10 and
recorded as an open RQ1 axis.

---

## DD-18 — Anomaly onset as a first-class signal, and the propagation panel

**Date.** 2026-07-28 · **Status.** adopted, unscreened · new axis C level

**The question it answers.** Every ordering the dashboard offered was by
*magnitude* — panel rank, node shade, legend `z=`. Magnitude cannot separate an
origin from its victims, and routinely inverts them: a saturated dependency moves
its own metrics a little while every service queued behind it moves a lot. What
separates them is order of arrival, and nothing in the pipeline computed it.

**New module `RQs/vlmrca/render/onset.py`.** Per-service onset, traces first:
`service_name`-keyed p95 span latency in bins of `clip(span/48, 5, 60)` seconds,
first crossing of `mu + 3 sigma` with a persistence requirement. Traces are the
only usable clock on the datasets that matter — AegisLab's metrics arrive every
15 s and its inferred fault window is a median 12 s wide, which is one sample and
orders nothing. Metrics fill in the services that emit no spans (databases,
brokers), at a stricter threshold. `pod_to_service` and
`service_level_projection` reconcile the three naming universes (metric entities,
trace `service_name`, graph nodes) and drop worker-hosting edges, which describe
which machine ran a pod rather than who called whom.

**Two calibration findings, both from measurement rather than reasoning.**

* *The metric path had to be held to a much stricter rule than the trace path.*
  At a 3-sigma floor with a 0.25-of-peak threshold, dozens of services in a
  104-service case "onset" in the first seconds on their own baseline noise and
  filled every row ahead of the services that actually broke. Requiring
  `MIN_METRIC_ONSET_SCORE = 10`, half the eventual peak, persistence, and a
  crossing after the baseline region fixed it. That last clause matters on its
  own: crossings inside the baseline produced onsets at "+0.0m" — a fault
  beginning before the window did — which then sorted to the top row.
* *The trace baseline must end at the fault window, not at a fixed leading
  fraction.* Cutting earlier gives onsets more room to spread out and order
  themselves, which sounds strictly better. It measured worse: these traces carry
  real pre-injection wander, an earlier cut reads that wander as onset, and on
  `ts0-mysql-partition` it promoted eight merely-noisy services and pushed the
  injected `mysql` out of the panel entirely — from first place. The cost of the
  correct choice is that onsets bunch in the first bins after the cut, which is
  mostly honest: an injected fault reaches what it reaches within a bin or two,
  and call-graph propagation is sub-second, which no 10 s binning resolves. This
  panel shows *which services were affected and the coarse order*, not a
  millisecond causal chain, and the guide text says so.

**The panel** (`topology="propagation"`, `max_propagation_rows`, presets
`prop12`/`prop30`). Rows are services in onset order, earliest at top, on the
same elapsed-minutes axis as the metric panels; marker at onset, bar to window
end shaded by within-panel severity rank, right-hand readout giving onset, peak z
and source (`t`/`m`). Curved arrows link call edges, preferring pairs whose
onsets actually differ — an edge between two services that crossed in the same
bin depicts no step in time, and spending the budget on those drew a dozen arcs
that all said "these two are related" and none that said "this one moved first".

**Why a row strip rather than a graph drawing.** The existing spring layout is a
hairball at AegisLab's 104 nodes; ordered rows of labelled text are the one
structure this project has evidence VLMs read reliably. It also degrades where a
graph cannot: AIOPS-2025's call graph has 15 edges over 61 nodes, and roughly one
case in twelve on the AIOPS sets has no traces at all. No onsets anywhere falls
back to anomaly-rank order with the caption saying so and `mode="rank_fallback"`
in the manifest.

### The measurement that changed the design: onset is not a better locator

The panel was first built to *select* rows by earliest onset — the opposite of
the topology panel's rule, on the reasoning that magnitude truncation is exactly
what discards a quiet early origin. The pilot supported it: on
`ts0-mysql-partition`, the case that motivated the whole redesign, `mysql` went
from having no panel at all to being row 1.

At n=30 on AegisLab that reverses. Ranking the *same* shown services by magnitude
instead of onset finds the injected service at **median rank 2.0 against onset's
5.5** (top-3 **79% vs 42%**, top-1 29% vs 13%), onset worse on 15 of 20
discordant pairs, **Wilcoxon p = 0.014**. Selecting on onset also dropped the
true cause out of the panel entirely on 6 of 30 cases.

So the premise is refuted in the form it was built. The mysql result was an
anecdote, and the pilot of 12 cases across four datasets (8 present, 5 in the top
3) was too small to see it.

**Revised design: select by severity, display by onset.** The rows are the
`max_propagation_rows` most anomalous services, drawn in onset order. Onset
remains the display axis because it is information the severity ranking does not
carry, and because vertical order plus the dot's horizontal position are the two
channels that express the temporal story. Severity stays legible on every row
through the colour ramp and the printed z.

Two corrections were needed before that worked, both found by a vision review of
the rendered galleries rather than by any test:

* *Having an onset cannot be a condition of appearing.* A service can deviate
  enormously and still have no detectable onset — it emits no spans, and its
  metric crossing fails the stricter rule. On two AIOPS-2022 cases the single
  worst-deviating service was dropped for exactly that reason while fourteen
  milder ones filled the rows, which made the panel strictly worse than the
  Service index it replaces. Such services now take rows, ordered last and
  labelled "no onset".
* *Severity must mean the same thing it means elsewhere on the dashboard.*
  Ranking on the onset-derived z rather than the per-service anomaly score behind
  the panel ranking and the legend selected a visibly different set, with the
  same effect.

Injected-service coverage on AegisLab: 80% → 83.3% → **93.3%** across the two
corrections.

**What may and may not be claimed.** The panel adds onset timing, its measurement
source, and call edges to a slot that previously held an unreadable 104-node
hairball, and its rows contain the true cause 93% of the time on AegisLab. It is
**not** a better ranking of root-cause likelihood than the magnitude ordering the
dashboard already had — measured, on the primary screening dataset, it is
significantly worse, and nothing downstream should describe "earliest onset" as
"most likely cause". Whether the extra evidence helps a VLM reason is a separate
question this measurement does not answer: config-effect sd is 0.36, an n=100 A/B
cannot resolve below ~0.10 MRR, and screening waits for the held Sonnet-5 batch.

---

## DD-19 — The metadata filter was a blacklist, and it was leaking

**Date.** 2026-07-28 · **Status.** adopted

`CaseRenderView.from_case` filtered `case.metadata` against a set of banned key
names, matched exactly. Upstream loaders do not restrict themselves to those
names. Measured directly: AegisLab passes `injection_ground_truth` — a dict
holding the answer service outright — and AIOPS-2025 passes `service`,
`instance`, `fault_description`, `fault_category`, `key_metrics`,
`key_observations` and `anomaly_description`. None of them matched a banned key.
All of them reached the view.

No run leaked, because nothing read `view.metadata`. That is luck, not design,
and it was about to run out: `node_pod_map` — the natural source for
pod-to-service reconciliation — lives in that same dict.

**Decision.** Whitelist. `SAFE_META` is `{"node_pod_map"}` and every other key is
dropped whatever it is called. `tests/test_no_leakage.py` now asserts
`set(view.metadata) <= SAFE_META` structurally, and runs over AegisLab,
AIOPS-2022 and AIOPS-2025 as well as RE2-OB — the hole was invisible for exactly
as long as that file loaded only RE2-OB, which happens to carry none of these
keys.

**The general lesson, which is the same one as the four v4 render bugs.** A
blacklist can only exclude what someone thought of in advance; a whitelist fails
closed. Any future filter over upstream-controlled keys should be written the
same way.

---

## DD-20 — The side column was never as wide as the code thought

**Date.** 2026-07-28 · **Status.** adopted · folded into `RENDERER_VERSION` 5

A vision review of the v5 galleries turned up a defect in **v0**, the incumbent
config, that every AegisLab run to date has carried: in the Service index, a long
name in the left text column printed straight through the right column's row
number. `2. ts-admin-basic-info-service z=152` ran into `15. ts-price-service`
and rendered as `...z=1521ts-price-service`, destroying both that row's score and
the neighbour's index number. Reproducible in every case with 25 entries and a
name near the budget; invisible in RE2-OB, which is why the golden test never saw
it and why `ambiguous_names` did not catch it — the *names* were distinct, they
merely overlapped on screen.

**Cause.** The character budget was derived from

```python
side_px = width_px * (right - left) * 1.25 / (cols + 1.25)
```

which apportions the grid by width ratio and ignores `wspace` entirely.
matplotlib does not take gutter space from somewhere else — it sizes gutters as a
fraction of the mean axes width and shrinks every column to pay for them. Measured
against what matplotlib actually draws, that formula **overstates the side column
by 23–25%**: 434px predicted against 354px real at 1568px/3 columns, and 385
against 308 at 2048px/5. The legend was budgeting 38 monospace characters into
room for 31.

The metric-panel titles use the same geometry and did *not* fail, because
`TITLE_CHAR_EM` was calibrated against a rendered image (DD-3 era) and quietly
absorbed the error into the constant. The legend used a derived 0.602 em advance
for monospace, correct in itself, so the geometry error passed straight through.
A calibrated fudge factor hid a bug in the thing it was calibrated against.

**Decision.** `_side_column_px` solves the gutter equation properly and both the
legend and the propagation panel's name gutter derive from it.
`test_side_column_width_matches_matplotlib` pins the prediction against a real
`get_position()` at three layouts, and `test_legend_rows_fit_their_column`
asserts every rendered row fits the half-column it is drawn in — so this class of
defect now fails a test instead of needing another pair of eyes.

**Standing lesson, third instance.** DD-13/14 fixed panel titles and legend rows
budgeted against the wrong container; this is the same bug one level up, in the
container measurement itself. Anything that converts a layout fraction into a
character count should be checked against a rendered `get_position()`, not
against arithmetic on the gridspec arguments.

---

## DD-21 — Readable topology is necessary but not sufficient for RCA

**Date.** 2026-07-31 · **Status.** adopted for development; not advanced to reserve

The confirmatory equal-information experiment found no visual increment over
byte-identical text. A post-hoc atomic grounding diagnostic then isolated one
shared perception failure: renderer-v6's curved propagation edges were read at
25.0% by Qwen and 8.3% by Gemma, while ordered rows, onset times, metric identity,
and tables were substantially more readable.

**Intervention.** Append an explicit caller-rank→callee-rank key containing only
edges already present in the common CEB/text. A compact key reached 100% on Qwen
but only 41.7% on Gemma. Enlarging and wrapping the same key reached 100% and
91.7%, with swapped/no-image controls at or below chance. This establishes a
scale/density defect rather than an inability to use topology.

The qualified primitive is now the explicit
`DashboardConfig.topology_edge_key` axis and development-only
`rq0_v7_edge_key` preset. The default remains `none`; renderer version 7 and its
fingerprint/golden are pinned. The core renderer and diagnostic reuse one
implementation.

**Case-level result.** On the same 12 exposed development incidents, with
pixel-identical base dashboards, identical atomic facts, byte-identical text and
hash-balanced condition order, v7−v6 MRR is −0.0208 for Qwen (0 improved, 1
degraded, 11 tied) and +0.0625 for Gemma (1 improved, 0 degraded, 11 tied).
The architecture directions disagree and each mean is one-case-driven.

**Decision.** Do not advance v7 to fresh reserve incidents and do not describe
it as a repaired RQ0 result. Generic visual-grounding SFT is also withdrawn as
the immediate next step: most atomic facts are already readable, and the isolated
edge defect has a rendering solution. The next training intervention, after its
data/entry-point contracts are frozen, should supervise case-level distinction
between an origin and severe/early propagated symptoms with explicit causal-edge
reasoning. RL/GRPO remains outside the current paper.

---

## DD-22 — Causal SFT must preserve a useful ranking before it tries to correct one

**Date.** 2026-07-31 · **Status.** adopted after development pilot; v1 rejected

The unified BF16 LoRA path is now implemented and qualified. A rank-8 adapter
trained for six optimizer steps on 24 frozen, label-audited development cases;
an independent paired evaluation used 12 disjoint development-heldout cases.
Training, serving, parsing, token accounting, and artifact persistence all
passed. The adapter did not: MRR changed from 0.5444 to 0.4750 (−0.0694), with
zero improvements, two degradations, and ten ties. AegisLab was −0.1250, beyond
the registered −0.10 reverse-effect boundary. No best model was saved.

Both degradations expose the same target-design error. v1 always teaches a
two-service list — root first, one hard symptom second. The trained model emitted
shorter lists, and in both scored failures collapsed to one wrong service,
deleting a true root that the base model had kept at rank 2 or 3. This was not a
failure to parse or a switch to the supervised symptom in every case; it was a
loss of the base model's useful uncertainty under sparse, highly diverse
supervision.

**Decision.** Do not scale or promote v1, do not open reserve/formal incidents,
and do not answer the regression with RL. A v2 is eligible for a new pilot only
after freezing a preservation/correction contract: always supervise a
five-service ranking; include base-correct cases whose ranking should be
preserved as well as base-wrong cases that need correction; prevent current
model-selection cases from re-entering a future heldout set; and use a fresh
paired base/adapter gate. Shorter output is not an efficiency improvement when
it achieves that saving by dropping previously ranked accepted roots.

---

## DD-23 — Preservation fixed list collapse, but v2.1 supplied no causal correction

**Date.** 2026-07-31 · **Status.** adopted after development pilot; v2.1 rejected

Version 2 implemented DD-22 directly: every target contains five services and
training balances base-correct preservation examples against base-wrong
correction examples. A frozen 134-case rollout found only three usable
AegisLab correction cases. This was discovered before optimization and before
opening the new heldout set, so v2.1 transparently amended that dataset to
3+3 while retaining 6+6 for each AIOPS dataset. The resulting 30-case rank-8
BF16 LoRA completed eight optimizer steps.

On 12 fresh development-heldout cases, base/adapter MRR was 0.5444/0.5028
(−0.0417; zero improved, one scored degradation, eleven ties). Average list
length increased from 4.33 to 4.83: ranking preservation eliminated v1's list
collapse. It did not, however, create any correcting improvement. The sole
canonical degradation placed a hashed Kubernetes pod of the accepted service
first and the service second. A service-aware sensitivity makes the pair a tie,
which still leaves adapter−base at zero and below the +0.05 gate.

**Decision.** Reject v2.1 and save no best adapter. Do not spend formal/reserve
cases, do not add a text-only arm to a non-confirmatory training pilot, and do
not escalate to RL/GRPO. Before any further model intervention, audit and freeze
the intended service/pod scoring granularity. Two conservative case-level SFT
pilots have now failed to produce a paired improvement; a successor needs a new
mechanistic hypothesis and a fresh gate, not another unregistered hyperparameter
variation.

---

## DD-24 — Hashed pod aliases are a real scorer defect, not an RQ0 explanation

**Date.** 2026-07-31 · **Status.** adopted for future runs; historical endpoint frozen

The upstream scorer says that a pod prediction should match a service-level
label, but its implementation recognizes only numeric suffixes. It misses
ordinary Kubernetes Deployment/ReplicaSet pod names such as
`service-cb9656f7b-nl4cb`. A post-hoc audit extended only that documented
leniency, retained exact matching for pod/node ground truth, and rescored all
4,320 stored RQ0 trajectories.

The extension changed 22 Qwen and 13 Gemma episode scores, all on AegisLab. It
did not change the conclusion: alias-aware A−B is −0.0115 for Qwen and −0.0160
for Gemma; A−C is +0.0051 and +0.0278, respectively. None reaches the registered
+0.05 practical threshold. The scorer defect therefore cannot be used to
reinterpret RQ0 as positive.

**Decision.** Leave the registered RQ0 endpoint unchanged and label the new
numbers post-hoc sensitivity. Future CanvasRCA experiments must use and record
the project-owned granularity-aware matcher in `RQs/vlmrca/eval/scoring.py`, whose
tests require hashed pods to match service labels while pod and node labels
remain exact. Do not modify the read-only upstream repository.

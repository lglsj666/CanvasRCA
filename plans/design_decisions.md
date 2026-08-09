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

---

## DD-25: Rerun RQ1b mapping with a type-specific structured-output contract
**Date:** 2026-08-04
**Status:** adopted

**Context.** RQ1b mapping v1 completed all 2,124 registered T/V/H calls for
each of Gemma-4-26B-A4B-it and Qwen3.6-27B, but the frozen analysis cannot
authorize the independent gate. Gemma's H/T/V parse rates were
0.9350/0.8941/0.9364, all below the registered 0.95 minimum. The problem is
concentrated in set-valued operations: 166 Gemma outputs violated the single
`{"answer": ...}` object contract; 99 began with a fenced object and then
self-corrected, while 67 began with prose. Of the 166, 158 contained two or
more answer objects, six contained one object embedded in extra output, and
two contained none. Three Gemma outputs were truncated. The existing generic
`<value>` prompt did not state whether a tied-service answer must be a JSON
array, and prompt-only compliance was insufficient to prevent multiple answer
objects.

The strict V3 analysis is
`RQs/RQ1/results/rq1b_visops_mapping_v1/analysis/paired_analysis_v3.json`
(SHA256 `ee8ef2452952e43959b99c4d5af7e5a7b231b4a6af25aac1db6d0e4828e166cb`).
It correctly marks the overall cell `incomplete_model_gate`. Qwen alone passed
its parse gate and retained 86 incidents after four whole-incident
infrastructure exclusions (4.44%, below the frozen 5% ceiling). Its diagnostic
case-macro H−T result was +0.0503, Wilcoxon Pratt p=9.79e-7, Cohen's dz=0.586;
the largest operation-specific signal was entity/modality alignment
(H=0.9767, T=0.6163). These results justify repairing the output contract but
cannot substitute for the primary Gemma gate.

**Decision.** Preserve mapping v1 as an incomplete diagnostic artifact and do
not freeze its operation router or open the disjoint gate. Register RQ1b
mapping v2 on the identical already-exposed 90-case mapping roster and the
same atomic facts, T/V/H arms, A+B composition, renderer, checkpoints,
decoding parameters, 32k context, and 16k output ceiling. Change only the
answer transport contract: state the exact answer shape for each operation
(`number`, sorted string array, ordered string path array, or caller/callee
object) and enforce that single-object schema through vLLM structured output.
Run partition-aware smoke and then rerun the complete Gemma and Qwen cells;
only a v2 analysis that passes every registered parse, pairing, leakage, and
infrastructure gate may freeze a router.

**Evidence.** Mapping config hash
`bfe7632648473a1ddd1a9798de1cb20bf889f09f325e7a79ea5189dd1899e9fc`;
roster assignment hash
`8b1557ac619f33c13546b94f29a4332747ca1ad52e01d581c0114381300e3b7b`;
Gemma 2,124/2,124 calls with zero infrastructure exclusions and 166 parse
failures; Qwen 2,124/2,124 persisted records, five failed calls across four
incidents, three parse failures among included outputs, and one truncation.
The V3 analyzer added the previously missing per-operation report and passed
18 focused analysis tests before regenerating the preserved analysis artifact.

**Alternatives rejected.** Lowering the 0.95 parse threshold would alter a
frozen gate after seeing results. Leniently selecting the first or last object
would rehabilitate outputs that explicitly violated the registered one-object
schema and introduce a post-hoc choice. Freezing a router from the valid Qwen
cell would replace the preregistered primary architecture and optimize the
architecture control. Opening the independent gate anyway would spend its
disjoint cases on a rule whose prerequisite is not satisfied. Rerunning only
Gemma would leave the two architectures under different output contracts.

**Consequences.** Mapping v1 remains auditable and its results may be reported
only as incomplete/diagnostic. V2 reuses exposed development cases and opens
no heldout or gate incident. Both architectures incur another full mapping
run, but server-enforced termination should remove the long self-correction
tails and reduce runtime. If structured-output smoke is unsupported by either
checkpoint/vLLM path, or if v2 still misses the parse gate, stop before gate
inference and reconsider the task/output interface rather than weakening the
acceptance rules.

---

## DD-26: Freeze the Gemma RQ1b operation router and open the disjoint gate
**Date:** 2026-08-04
**Status:** adopted

**Context.** DD-25 required an otherwise identical RQ1b mapping rerun with a
type-specific, server-enforced JSON output contract before any operation
router or independent gate could be authorized. Mapping v2 completed all
2,124 registered calls for each architecture. Both Gemma-4-26B-A4B-it and
Qwen3.6-27B retained all 90 incidents and 708 eligible queries, with 1.000
parse rate in every T/V/H arm, zero infrastructure failures, and zero
truncations. The v1/v2 equivalence audit proves that all 708 CEBs, questions,
fact inventories, private answers, text views, image views, A+B fragments, and
3,540 evidence artifacts are unchanged; only the public answer contract and
its prompt/schema hashes changed.

Mapping v2 is a rule-discovery cell, not the independent test of the rule.
Gemma's case-macro H/T/V accuracies were 0.9588/0.9558/0.9091; H−T was
+0.0030, Wilcoxon Pratt p=0.5801, Cohen's dz=0.060. Qwen's corresponding
accuracies were 0.9738/0.9712/0.9273; H−T was +0.0027, p=0.6045,
dz=0.054. These pooled differences do not establish a general hybrid benefit.
The preregistered operation rule nevertheless identifies two non-text Gemma
choices: `earliest_onset -> H` (T/V/H=0.9815/0.6481/1.0000) and
`entity_modality_alignment -> V` (0.8000/0.8444/0.8222). Every other operation
selects T, either because T is best or because an exact tie is resolved by the
frozen cost order `T > V > H`.

**Decision.** Accept mapping v2 as the valid replacement for the incomplete v1
mapping, deterministically freeze the complete Gemma operation-to-arm rule,
and authorize preparation and execution of the already locked, disjoint
90-case RQ1b independent gate. Qwen must use the same Gemma-derived router and
must not receive an architecture-specific mapping. The gate keeps the frozen
+0.10 routed-versus-text structural threshold, +0.05 routed-versus-best-fixed
threshold, paired Pratt-Wilcoxon p<0.05 requirements, dataset-direction and
exact-lookup controls, 0.95 parse floor, and 5% whole-incident infrastructure
ceiling. No heldout or reserve data is opened.

**Evidence.** The authoritative v2 paired analysis is
`RQs/RQ1/results/rq1b_visops_mapping_v2/analysis/paired_analysis_v3.json`
(SHA256 `ac14861f85c4be16606e402e611e44babe1cacf5dd54d027fd98038c2b259f2e`).
The v1/v2 input-equivalence artifact has SHA256
`35ad2584ab3e3270ccd8b27d75895a28be0ab01ac6c7a72dfa8b582d20a871f9`;
the v2 qualification report has SHA256
`b6335b1ab0f478a8c9d3bdf62a5720231642065a1e98a24921aceda63074c997`.
The mapping config hash is
`2ac662944cceb2beea7c7cc25c963b2d92f41a40a4622a86ec63265d1eb8f6f0`,
and the unchanged roster assignment hash is
`8b1557ac619f33c13546b94f29a4332747ca1ad52e01d581c0114381300e3b7b`.

**Alternatives rejected.** Stopping because the pooled H−T mapping effect is
small would use the rule-discovery set as an unregistered efficacy gate and
would leave the preregistered operation-dependent hypothesis untested.
Selecting H globally would ignore the near-zero pooled increment and the
operation mapping. Optimizing a separate Qwen router would turn the
architecture control into another discovery analysis. Lowering the independent
gate thresholds after observing mapping v2 would be outcome-dependent protocol
drift. Opening heldout RCA data at this point would skip the disjoint
development gate that was designed to protect it.

**Consequences.** The next work item is a fail-closed router-freeze artifact,
followed by gate-roster preparation, parity/leakage/determinism qualification,
Gemma and Qwen T/V/H inference, and a router-aware case-level analysis. If the
independent gate fails, RQ1b does not authorize the modality factorial or RQ1c;
the negative result must be recorded without retuning the router on gate cases.
If it passes for Gemma, the registered RQ1b factorial may proceed, with Qwen
determining whether the finding is architecture-specific or replicated.

---

## DD-27: Reject the frozen RQ1b router after its disjoint independent gate
**Date:** 2026-08-04
**Status:** adopted

**Context.** DD-26 froze the Gemma-derived operation router on the 90-case
mapping roster and authorized one test on a disjoint, already-exposed 90-case
gate roster. Both model cells completed under the same frozen CEB, T/V/H prompt
composition, renderer, scorer, router, BF16 checkpoints, and vLLM contract.
Live-tokenizer preflight found one Gemma incident and two Qwen incidents whose
complete 16,384-token output allowance would exceed the fixed 32,768-token
context. Each affected incident's entire T/V/H query set was recorded as a
paired infrastructure exclusion without replacement. The resulting 1.11% and
2.22% whole-incident fractions are below the preregistered 5% ceiling. Every
actually executed request parsed, no output truncated, and the parity, leakage,
pairing, runtime, and exact-lookup controls passed.

The frozen rule failed on its primary Gemma architecture. On the selected
structural operations, routed minus T case-macro accuracy was **−0.0562**, not
the required +0.10; the two-sided Pratt-Wilcoxon p-value was 0.0112, so the
detected effect was significantly harmful rather than beneficial. Dataset
effects were AegisLab −0.0690, AIOPS-2022 +0.0167, and AIOPS-2025 −0.1167; the
last also violated the frozen −0.10 material-reversal boundary. Routed minus
the best fixed arm T was −0.0118 (p=0.0104), not the required +0.05. The
architecture control also failed: Qwen structural routed-minus-T was −0.0227
(p=0.3698), and routed-minus-best-fixed-T was −0.0046 (p=0.3622).

The failure is localized and interpretable. On the independent gate,
`earliest_onset -> H` tied T for Gemma (both 1.0000) and improved Qwen only from
0.9636 to 1.0000. In contrast, the mapping-selected
`entity_modality_alignment -> V` reversed: Gemma T/V was 0.9326/0.8427 and
Qwen T/V was 0.9205/0.8636. Thus the non-text mapping choice did not generalize;
the best fixed representation for both tested architectures was T.

**Decision.** Reject the frozen router and mark the registered RQ1b independent
gate failed. Do not refit the router on gate outcomes, do not open heldout or
reserve data, and do not advance the blocked RQ1b factorial, RQ1c routed agent,
RQ1d causal intervention, SFT, LoRA, or GRPO branches under this protocol.
Preserve mapping v2 as valid rule-discovery evidence and the gate as valid
negative validation evidence. The next authorized work is descriptive failure
analysis on now-exposed mapping/gate trajectories, followed by a separately
registered development hypothesis if the analysis identifies a new mechanism;
the independent gate cannot be reused as confirmation for that successor.

**Evidence.** The authoritative independent-gate analysis is
`RQs/RQ1/results/rq1b_visops_independent_gate_v2/analysis/gate_analysis_v1.json`
(SHA256 `4a8ba8d40af584ac2dbb60d7ed17846ed64a2c935d20d18083b6dba6764a7552`;
internal analysis-contract SHA256
`aa037f5140e24130db4b71b2f1f69dee4f692779cf07d70164794d0d00a33365`).
It includes 89 paired Gemma incidents and 88 paired Qwen incidents from the 90
requested cases. The frozen router contract SHA256 is
`0dc7459e489c1f22446247566f5105c858c30c0f2eaf44b96db0c55fcbc2a427`,
and the source call-inventory SHA256 is
`8584a573ccc0bb98e914397b0542146d3d3dd92641a1f346b621ec51affe53f2`.

**Alternatives rejected.** Replacing the failed V choice with T or H after
seeing gate outcomes would fit the validation set. Treating p<0.05 as success
would ignore that the significant effect has the wrong sign and misses both
practical thresholds. Pooling query rows as independent observations would
inflate precision and violate the incident-level analysis contract. Dropping
AIOPS-2025 would hide the preregistered material reversal. Proceeding to RQ1c
because H remains strong in absolute accuracy would confuse a high-performing
baseline with evidence that visual routing adds value.

**Consequences.** RQ1b now provides a strong negative generalization result:
the current image representation changes operation behavior, but the
mapping-derived visual policy is unstable and inferior to text on new exposed
cases. Future work must improve or reformulate the visual mechanism on separate
development data and earn a new independent gate before any RCA efficacy or
causal-agent claim is attempted.

---

## DD-28: Replace answer-visible lookup tasks with an answer-hidden complexity mechanism study
**Date:** 2026-08-04
**Status:** adopted

**Context.** The DD-27 failure analysis showed that the visual choice for
`entity_modality_alignment` was selected from a mapping-set text deficit and
reversed on the independent gate. A code-and-artifact audit also identified a
more general measurement limitation: the old `multi_hop_path` query supplied an
explicit derived path as a model-visible fact, while `earliest_onset` and
`longest_persistence` supplied the already-derived scalar for every row. Their
near-perfect scores therefore establish lookup/readability, not multi-step
visual graph or time-series reasoning. This does not invalidate the completed
gate—the frozen benchmark measured what its contract specified—but it makes
rerouting those same operations scientifically uninformative.

**Decision.** Keep the old mapping and gate frozen as valid negative evidence,
and register a separate exposed-development successor, RQ1b2. RQ1b2 hides the
derived answer from all arms, supplies only identical raw atomic facts, and asks
the model to compose a temporal or relational answer. It pairs low- and
high-complexity variants so the primary mechanism is not merely `V > T`, but
whether `V-T` increases with entity/edge/distractor complexity. T, V, and exact
`A+B` H remain mandatory. The development roster contains 90 new exposed cases;
a disjoint 150-case gate is locked in advance. The old 180 mapping/gate cases,
heldout, reserve, RE2, and unknown cases are excluded.

The complete protocol and thresholds are frozen in
`RQs/RQ1/descriptions/rq1b2_compositional_complexity_protocol_v1.md`. Gemma is
the development architecture. Only a positive development gate authorizes the
complete Gemma-plus-Qwen independent gate. The confirmatory thresholds are
temporal high-complexity `V-T >= +0.10`, temporal complexity interaction at
least `+0.10`, and a fixed temporal `low -> T, high -> V` policy at least `+0.05` above the best fixed arm,
each with the registered paired test. Failure of any mechanism condition leaves
RQ1c/RQ1d blocked.

Label-blind preparation subsequently confirmed 80 paired temporal incidents
(AegisLab 28, AIOPS-2022 25, AIOPS-2025 27), but high-complexity unique
three-to-five-hop topology tasks only in 30 AegisLab incidents. Before any
model call, the protocol therefore fixed temporal composition as P1-P3 and
kept topology as a secondary dataset-specific result. This avoids pooling a
task-family change with a dataset comparison; it is a qualification decision,
not an outcome-dependent amendment.

The pre-inference perception review then found robust-z display magnitudes near
`5e8` when both the baseline and MAD were effectively zero. Before any model
call, the public transformation was amended to symmetrically winsorize robust-z
at `+/-99.9` in every T/V/H arm. The task threshold is `|z|>=3` and the cap
preserves sign, so this transformation cannot change any sustained-onset answer.
All 90 development artifacts must be regenerated under the amended hash; the
pre-amendment artifacts are qualification failures and cannot be mixed into a
run. This is a perception/numerical-stability correction made without model
outcomes, not an empirical threshold change.

**Alternatives rejected.** Replacing the failed V choice with T after seeing
the independent gate would overfit validation. Repeating more answer-visible
lookup tasks would increase sample size without measuring the desired visual
reasoning mechanism. Advancing directly to RQ1c would violate its prerequisite.
Opening heldout data would spend confirmatory evidence before a development
mechanism exists. Treating H as the only visual comparison would confound
visual encoding with redundant context, so V-T remains primary and H is
reported as a mandatory secondary arm.

**Consequences.** RQ1 work returns to a bounded, exposed-only development stage.
The next implementation must preserve old code paths and historical validity,
add answer-separation tests, freeze new disjoint rosters outcome-blind, qualify
the renderer without RCA labels, and run Gemma development before any new gate
or downstream agent experiment. A positive result would justify a
complexity-aware access policy; a negative result would close this mechanism
rather than trigger another router rescue.

---

## DD-29: Close the RQ1b2 image-only complexity mechanism after the registered development gate
**Date:** 2026-08-04
**Status:** adopted

**Context.** DD-28 registered a fresh, answer-hidden and fact-equal mechanism
study on 90 exposed Gemma development incidents. Before inference, the compiler,
renderer, prompt fragments, answer-separation checks, leakage/parity audits,
12-case manual review, 12 deterministic recompilations, live-tokenizer context
preflight, model smoke, and runtime tree freeze all passed. The qualified
inventory contained 366 queries and generated exactly 1,098 T/V/H calls. All
1,098 calls completed, all outputs parsed, no request truncated, no incident
was excluded, and no infrastructure or accounting failure occurred.

On the 80 incidents with paired low/high temporal tasks, the primary
high-complexity image-only effect was `V-T = -0.3250`, rather than the required
`+0.05`; V accuracy was 0.1625 and T accuracy 0.4875. Vision repaired four T
errors but broke 30 T-correct answers. Low-complexity `V-T` was also `-0.3250`,
so the paired complexity interaction was exactly 0.0000, not positive. The
frozen `low -> T, high -> V` policy scored 0.4188 and was 0.1812 below the best
fixed arm H at 0.6000. All three development promotion conditions therefore
failed. The high-complexity direction was negative in every dataset: AegisLab
`-0.4286`, AIOPS-2022 `-0.2800`, and AIOPS-2025 `-0.2593`.

The controls make the result more specific than a general inability to parse
the visual interface. On the 90 exact metric lookups, T/H were 1.0000 and V was
0.9889. For low-complexity topology, T/H were 1.0000 and V was 0.9884; for the
30 AegisLab high-complexity paths, T/H remained 1.0000 while V fell to 0.4333.
For temporal composition, H-T was +0.0500 at low complexity but -0.0125 at high
complexity. Thus adding the same image to text does not rescue the registered
high-complexity endpoint, and image-only performance degrades as composition
becomes harder even though simple visual lookup is nearly perfect.

**Decision.** Mark the RQ1b2 Gemma development gate valid and failed. Close the
registered image-only complexity/access-policy mechanism. Do not run the Qwen
development cell, do not prepare or open the locked 150-case independent gate,
and do not advance RQ1c, RQ1d, SFT/LoRA/GRPO, reserve, or heldout RCA under
DD-28. Preserve the unused gate roster as unopened. Subsequent work may inspect
the now-exposed Gemma trajectories descriptively, but any new visual mechanism
must be separately registered on disjoint exposed development data and may not
reinterpret this failed gate as confirmation.

**Evidence.** The authoritative analysis is
`RQs/RQ1/results/rq1b2_compositional_development_v1/analysis/development_analysis_v1.json`
(SHA256 `bab07f7e721af803642a913ddae48fb25aae96c372091659679b67f1ae67a8ee`).
Its meeting summary has SHA256
`7d9f63f82449ef693650d65aa69f814d6ebd494f05e3a26364a2584047dce608`,
and the complete run summary has SHA256
`4891706c211437193891e0c6c74234bf0ca7e1296d661c17cfbe1bb1084ef463`.
The qualified prepared inventory is
`7e3b50973f3181b8d8a59f88d39a80fc93bf74ae41ed0ac59663c4295afeb3f7`;
the frozen runtime tree is
`8705cf227cfc0a18ac33a8b3754e281b3d60197d2ac7bc64e6018580acf576e3`.

**Alternatives rejected.** Running Qwen despite the failed Gemma promotion
gate would convert a preregistered conditional control into outcome-driven
model shopping. Opening the 150-case roster would spend independent evidence
after all development mechanism conditions failed. Promoting H because its
pooled raw accuracy is highest would change the registered V-T complexity
hypothesis and ignore that high-complexity H-T is negative. Retuning the
renderer or onset threshold on these outcomes would fit the development
answers; any such successor needs a new hypothesis, artifacts, and roster.

**Consequences.** DD-28 is resolved as a valid negative development result, not
an incomplete infrastructure attempt. The immediate authorized work is bounded
failure analysis and planning on already exposed artifacts. Further long-form
inference remains blocked until a distinct mechanism earns a new registered
development path.

---

## DD-30: Test a complete two-stage onset ledger before abandoning visual evidence acquisition
**Date:** 2026-08-04
**Status:** adopted

**Context.** The bounded DD-29 failure analysis explains why another direct
H/T/V rerun is not justified. On the 80 high-complexity tasks, V selected a
panel without any valid sustained onset 25 times, returned a singleton in 58
cases although only 45 gold answers were singleton, and included the top
rendered row 30 times although gold did so only 15 times. A representative
break chose one isolated `99.9` cell instead of a true two-bin same-sign run.
At the same time, a representative repair used a clear connected early color
block to correct T's later choice. H repaired eight T errors and broke nine;
direct fusion is not positive, but the errors show that value reading,
per-panel composition, tie aggregation, and final selection are currently
collapsed into one opaque answer.

No trustworthy post-hoc router emerged. Seven of eight H repairs were in
AIOPS-2022, and exploratory clutter/service-count bins were small and selected
after outcomes. They cannot authorize a subgroup claim. The remaining exposed
pool is nevertheless sufficient for an independent successor: after excluding
all old private rosters and the unopened RQ1b2 gate, 571 eligible cases remain
(178/200/193 across AegisLab/AIOPS-2022/AIOPS-2025).

**Decision.** Register RQ1b3 as a new exposed-only mechanism study under
`RQs/RQ1/descriptions/rq1b3_two_stage_onset_ledger_protocol_v1.md`. Keep the
same raw 12×16 facts and mandatory T/V/H arms, but require one Stage-1 call to
externalize every panel's onset/null ledger and one Stage-2 call that sees only
that persisted ledger and selects the minimum plus all ties. H remains exact
image-first `A+B`; H−T final accuracy and ledger quality are primary, while V
remains a complete secondary arm. Use numeric panel order and a separately
registered deterministic row-shuffle sham to test the position-bias mechanism
without selecting the better order by outcome.

Freeze a new 90-case development roster and a disjoint 150-case gate, excluding
every old RQ1 case and the RQ1b2 gate roster. Gemma development promotes only if
H−T final accuracy and Stage-1 panel accuracy are each at least +0.05, H repairs
exceed breaks, H ledger error is lower, oracle-ledger Stage-2 accuracy is at
least 0.95, and all integrity gates pass. Otherwise stop without Qwen or gate
inference. The confirmatory gate retains incident-level Pratt-Wilcoxon tests,
practical thresholds, dataset safeguards, parse floor, and 5% paired
infrastructure ceiling specified in the protocol.

**Evidence.** The post-hoc diagnostic is
`RQs/RQ1/results/rq1b2_compositional_development_v1/analysis/failure_analysis_v1.md`
(SHA256 `6530012a568da3926b3b1c817d83466e925bab83f56bec87a986896ab570e43b`).
The authoritative failed RQ1b2 analysis remains SHA256
`bab07f7e721af803642a913ddae48fb25aae96c372091659679b67f1ae67a8ee`.

**Alternatives rejected.** A dataset-specific H router would overfit the seven
AIOPS-2022 repairs. Reordering rows and keeping whichever version scores higher
would tune on development outcomes, so numeric order is fixed and the shuffle
is a sham diagnostic only. Highlighting the derived winning run would turn the
task back into answer-visible lookup. Reusing the locked RQ1b2 gate would spend
or repurpose independent evidence after its parent mechanism failed. Advancing
directly to RQ1c/RQ1d or RCA would violate the roadmap's complementarity gate.

**Consequences.** RQ1b3 may proceed through roster freeze, implementation,
static qualification, and smoke. No model inference is authorized before those
contracts pass. RQ1c, RQ1d, training, reserve, and heldout remain blocked. A
failed Gemma development cell closes this two-stage mechanism; a pass only
authorizes the new disjoint Gemma-plus-Qwen gate, not a paper-level RCA claim.

---

## DD-31: Replace RQ1b3's whitespace-permissive JSON transport before development
**Date:** 2026-08-04
**Status:** adopted

**Context.** RQ1b3 v1 passed static parity, leakage, deterministic-render, and
manual visual qualification. Gemma then completed all nine registered main
Stage-1 smoke calls, but one of six row-sham calls stopped at the 16,384-token
ceiling. The response had already emitted a valid ledger prefix through
`"sign":` and then generated only grammar-legal whitespace. A separate
non-experimental minimal probe reproduced the same failure immediately after
`"answer":`. Thus the issue is not insufficient output budget, missing visual
evidence, or an infrastructure interruption: the JSON-schema grammar leaves an
unbounded whitespace path that Gemma can follow forever. The v1 sham parse rate
is 5/6, below its frozen requirement that every Stage-1 smoke output parse.

**Decision.** Preserve RQ1b3 v1 as a technically valid failed interface smoke;
it is not an efficacy experiment and authorizes no development inference.
Register RQ1b3 v2 with unchanged incidents, facts, T/V/H arms, images, text,
questions, onset definition, two stages, scores, and decision thresholds. Only
the output transport changes. Stage 1 emits the same semantic ledger in compact
natural-order entries such as `M7:positive@4` or `M7:null`; a task-specific
vLLM guided regex admits no whitespace and the evaluator deterministically
expands every valid entry to the full persisted `PanelOnsetLedgerV1`, including
support bins `[onset,onset+1]`. Stage 2 also uses a no-whitespace guided regex
while reading only that expanded same-arm persisted ledger.

The unified vLLM model and sampling configuration remains unchanged. The
transport and regex hashes must be stamped in every new prompt/run contract.
V1 artifacts and hashes are immutable and may not be relabelled as v2. The
unopened 90-case development and 150-case gate rosters may be reused because no
development or gate model request has yet been sent.

**Evidence.** The failed v1 sham call is
`RQs/RQ1/results/rq1b3_two_stage_smoke_v1/gemma/sham_stage1/calls/4b0b177b78f13600b42de6bb.json`.
It records `finish_reason=length`, 16,384 output tokens, and the incomplete
ledger prefix. Main Stage 1 completed 9/9 with parse 1.000; sham Stage 1
completed 6/6 requests but parsed 5/6. A request-level
`disable_any_whitespace=true` probe was rejected when supplied without a
constraint, and was accepted but ineffective when combined with a JSON
constraint under the server's automatic structured-output backend. A strict
regex probe returned compact valid JSON in 11 tokens.

**Alternatives rejected.** Raising the output ceiling cannot remove an
unbounded grammar path and would violate the 32k contract. Counting the
truncated result as infrastructure failure would misclassify a model/output
interface outcome. Lowering the parse gate would admit a known avoidable
failure before a 90-case run. Changing the global structured-output backend or
canonical vLLM flags is broader than necessary. Dropping the sham after it
found the bug would be outcome-dependent protocol weakening.

**Consequences.** RQ1b3 development remains blocked until v2 passes the same
static, perception, main/sham Stage-1, main/sham Stage-2, oracle, accounting,
and determinism smoke gates. This repair changes no status of RQ0, RQ1b,
RQ1b2, or any other completed experiment.

---

## DD-32: Accept the complete RQ1b3 v2 smoke and authorize Gemma development
**Date:** 2026-08-04
**Status:** adopted

**Context.** The DD-31 v2 repair passed 102 automated tests, static preparation
qualification, real-telemetry deterministic recompilation, exact parity and
leakage checks, and byte-identical reuse of the six manually reviewed v1 PNGs.
The complete Gemma validation smoke then executed 33/33 calls: main Stage 1
9/9, row-sham Stage 1 6/6, main Stage 2 12/12 including three oracle calls, and
row-sham Stage 2 6/6. Every call completed and parsed; there were zero
truncations and zero infrastructure failures, all token/GPU accounting fields
were present, Stage 2 had no original image/text access, and oracle Stage-2
exact accuracy was 1.000.

**Decision.** Accept RQ1b3 v2 as interface-qualified and authorize preparation,
qualification, runtime freeze, and execution of the preregistered 90-case
Gemma development cell. Smoke accuracy is diagnostic only and must not be used
to select an arm, alter a threshold, or claim efficacy. Qwen and the disjoint
150-case gate remain blocked until the Gemma development promotion rule passes
in full.

**Evidence.** The authoritative smoke qualification is
`RQs/RQ1/results/rq1b3_two_stage_smoke_v2/qualification/smoke_qualification.json`
(file SHA256 `0d024dab2720f4765ce7574785d3cc12bda92e81402dd0e6830a54948b12f60a`,
internal qualification SHA256
`b001a019fc77488a23fabd6fd93a2a4e4c494501d3c8a2e74c95a832833ea029`).
The prepared inventory is
`f57a009f6b484f610d6bcd386703c54e7eb698327962c6eb2acc3e5db7128cfc`.

**Consequences.** The next valid action is the 90-case Gemma development run
under the unchanged v2 protocol. Its promotion decision requires final H−T
and incident-macro ledger H−T each at least +0.05, H repairs greater than
breaks, lower H ledger error, oracle Stage-2 accuracy at least 0.95, and all
integrity gates. There is no development p-value gate because n=90 has an
approximate 80%-power MDE near 0.106 for paired SD 0.36.

---

## DD-33: Repair the RQ1b3 development roster by label-blind task eligibility
**Date:** 2026-08-04
**Status:** adopted

**Context.** The first full preparation attempt for the frozen 90-case RQ1b3
development roster stopped before any model request. Seventy-seven incidents
compiled into the registered 12-panel onset-ledger task, while thirteen did
not support that task: four AegisLab, five AIOPS-2022, and four AIOPS-2025.
The exposure ledger's generic `eligibility_status=eligible` means that an
incident is authorized for RQ1 development; it does not guarantee the
RQ1b3-specific requirement of exactly twelve qualified normalized metric
series. Treating the thirteen incidents as model errors, silently reducing
the denominator to 77, or borrowing cases from the independent gate would
violate the registered design.

**Decision.** Preserve the original 90-case v1 roster and its failed
pre-inference qualification record. Register a repaired development roster
that retains all 77 task-eligible original incidents and replaces only the
thirteen unsupported incidents. Replacement is dataset-stratified (4/5/4),
uses no model output and no private RCA answer, and is selected by the already
frozen development ordering
`SHA256(42:rq1b3:development:dataset:private_case_id)`. Starting after the
original selections, scan the remaining exposed, development-authorized
incidents in that order and accept the first incidents for which the frozen
v2 compiler deterministically yields exactly one 12-panel task. Exclude every
prior RQ1 private roster, all original RQ1b3 development cases, and the entire
unopened 150-case RQ1b3 gate. Record every accepted or rejected candidate in a
private qualification audit and publish only opaque identifiers and counts.

The scientific protocol, H/T/V facts and prompts, output transport, model,
thresholds, dataset balance, and n=90 do not change. The v2 smoke and its
hashes remain valid because its validation roster and runtime are immutable;
the repaired development receives a new config, roster, preparation inventory,
qualification, and runtime freeze before inference.

**Alternatives rejected.** Reducing n weakens the planned screen and makes
dataset weights unequal. Lowering the twelve-panel requirement changes the
task after registration. Using gate incidents spends independent evidence.
Selecting replacements by root cause, observed answer, renderer quality, or
model accuracy would be outcome-dependent. Rebuilding all 90 cases would
discard valid frozen selections without necessity.

**Consequences.** No RQ1b3 development inference is authorized until the
repaired roster has 30 task-eligible incidents per dataset and passes the same
parity, leakage, determinism, manual-review, and runtime-freeze gates. This
qualification repair changes no completed experiment status and does not
authorize Qwen or gate inference.

**Execution evidence.** The frozen repair retained 77 original incidents and
needed only 5/8/4 ordered candidate checks to accept 4/5/4 replacements. The
result contains 30 incidents per dataset and has zero overlap with the unopened
RQ1b3 gate. The public audit SHA256 is
`e8bd389352e53a503399c4f935acdf4f27739649ac85dddf5f13faf0173476fb`;
the public roster SHA256 is
`0e197ef5139d3e3ebc3dd3a5a7590af3ecbf678c24dff78c1a97a24207203e8e`.
The repaired roster assignment hash is
`faf3d4ccbea649e8be947a048fe2aab5e93e5c3fa595cd171dd00745df2d306e`.

---

## DD-34: Close RQ1b3 and the current visual-complementarity route after the complete development gate
**Date:** 2026-08-04
**Status:** adopted

**Context.** The repaired and fully qualified RQ1b3 Gemma development cell
completed every registered request: 270 main Stage-1, 360 main Stage-2
including oracle, 180 row-sham Stage-1, and 180 row-sham Stage-2 calls. There
were zero infrastructure failures, truncations, or paired exclusions. The
registered result is `valid_failed`. Final accuracy was T=0.6222, H=0.5889,
and V=0.1667, so final H−T was −0.0333 rather than at least +0.05. Stage-1
panel-macro accuracy was T=0.8944, H=0.8917, and V=0.5083, so ledger H−T was
−0.0028 rather than at least +0.05. H repaired 10 T errors but broke 13; its
normalized ledger error was 0.0774 versus T's lower 0.0668. Oracle Stage-2
accuracy was 0.8000 rather than at least 0.95. All six promotion requirements
failed.

Stage-2 integrity also failed because the registered strict parser required
Python lexicographic list order, whereas Gemma sometimes returned a correct
set in natural numeric panel order. This was an avoidable output-interface
convention: 21/360 main and 13/180 sham responses were rejected without being
malformed, truncated, or interrupted. A post-hoc order-insensitive sensitivity
analysis is deliberately not substituted for the registered result. It raises
T/H/V/oracle correct counts only to 58/56/17/74 out of 90; H−T remains −0.0222,
repairs still do not exceed breaks (10/12), and oracle remains only 0.8222.
The interface issue therefore does not explain or rescue the failed mechanism.

**Decision.** Close RQ1b3 as a valid negative exposed-development result. Do
not run Qwen, do not open the locked 150-case RQ1b3 gate, and do not advance
RQ1c, RQ1d, Observer SFT, LoRA, GRPO, reserve, or heldout RCA under this
mechanism. Together with the valid failed independent router and RQ1b2
complexity study, this fails the roadmap's visual-operation complementarity
gate for the current renderer and frozen-model interface. Stop further
outcome-driven RQ1 rescue experiments.

The set-order parser is repaired forward-only: future set-valued interfaces
accept any complete duplicate-free allowed-ID array and canonicalize it
numerically. Historical call records, parse flags, scores, runtime freeze, and
the `valid_failed` decision remain unchanged. The analysis script's config-key
typo was likewise repaired only after inference; it changed no call, threshold,
or stored outcome. The next authorized research action is to preregister RQ2's
controlled content/encoding/arrangement study on exposed data, because that
question can identify which dashboard design choices help or hurt without
claiming that the current dashboard already improves RCA. No RQ2 model run is
authorized until its own fact-equality, leakage, budget, solver, statistical,
and stopping contracts are frozen.

**Evidence.** The authoritative registered analysis is
`RQs/RQ1/results/rq1b3_two_stage_development_v3/analysis/analysis_v1.json`
(SHA256 `de0e304616cce1dcd09fa2440ee471adfc9b9c83fec0da38f452c0f04e92216a`).
The bounded post-hoc diagnosis is
`RQs/RQ1/results/rq1b3_two_stage_development_v3/analysis/failure_analysis_v1.md`
(SHA256 `85d7b497afa4614c9a356a0a2caf90f2493ce9a471aef54dabb76ca880ed6a07`).
The analysis/runtime provenance record has SHA256
`0fc854011d41204c2c5c789ba0e128b914d80adc5e670e2ffc93a25f08162df7`.
The frozen inference tree remains
`a951f5215bbeb170854bde7a725e161b0b50c1d55d9f3ddf0c1f8fac65c3c344`.

**Alternatives rejected.** Re-running after relaxing array order would be a
post-outcome rescue and still would not meet a single efficacy gate under the
order-insensitive sensitivity result. Running Qwen after the registered Gemma
stop would turn a mandatory conditional control into model shopping. Opening
the 150-case gate would spend independent evidence on a mechanism that failed
all development conditions. Choosing AIOPS-2025 because its H−T was +0.0667
would be a post-hoc dataset subgroup and ignores AegisLab's −0.1333 result.
Proceeding to training would use supervision to conceal an unproven visual
complementarity premise.

**Consequences.** RQ1 now has a coherent negative evidence chain: redundant
static augmentation failed, the learned operation router failed on a disjoint
gate, answer-hidden image-only composition failed, and explicit two-stage
hybrid evidence acquisition failed. This is informative evidence about the
current representation, not proof that every possible visualization is
useless. Future work moves one level earlier—to controlled dashboard design
effects in RQ2—rather than changing the RQ1 outcome or consuming heldout data.

---

## DD-35: Start RQ2 with a staged factorial design study, not another RQ1 rescue
**Date:** 2026-08-04
**Status:** adopted for static implementation; inference locked

**Context.** DD-34 closes the current RQ1 visual-complementarity path but does
not establish that every dashboard design is useless. RQ1b3's row-order sham
shows that arrangement substantially changes the model's ledger and final
selection, while the negative accuracy result shows that influence alone is
not benefit. The project roadmap separately defines RQ2 as the causal study of
dashboard content, encoding, arrangement, and interactions. The exposure audit
contains 318 eligible exposed incidents outside every frozen private roster and
locked RQ1 gate (94 AegisLab, 115 AIOPS-2022, 109 AIOPS-2025), enough for a
150-case independent RQ2a gate and a later disjoint 90-case downstream
development cell. RQ2 development can reuse already executed exposed RQ1 cases
without consuming new evidence.

**Decision.** Adopt
`RQs/RQ2/descriptions/rq2_master_protocol_v1.md` as the RQ2 research structure.
Begin with RQ2a: a full `2^4` equal-fact factorial over metric encoding, graph
encoding, cross-source arrangement, and entity ordering. Use answer-hidden,
machine-scored temporal, relational, alignment, missingness, and exact-lookup
operations. Estimate each design action through within-incident anchor-state
relative credit, averaging over the other factor contexts. Keep content
presence/absence in a separate RQ2b unequal-content study and downstream RCA in
RQ2c, so new facts, visual encoding, and layout are never collapsed into one
ambiguous effect.

RQ2a development reuses 60 already executed exposed incidents and Gemma only.
It is a spending screen, not evidence. A disjoint 150-case gate runs both Gemma
and Qwen only if the complete development rule passes. The screen requires at
least one target-family main effect of +0.10, repairs over breaks, lookup
degradation above −0.05, no dataset at or below −0.10, parse at least 0.95,
infrastructure exclusion at most 5%, and complete integrity. At n=60 and paired
SD 0.36, the approximate 80%-power MDE is 0.130, so no development p-value is
used. The n=150 gate requires +0.10 and Holm-adjusted paired Pratt-Wilcoxon
p<0.05 plus the registered safeguards; its planning MDE is 0.082–0.114 for SD
0.36–0.50.

This decision authorizes directories, contracts, renderer variants, compilers,
tests, read-only feasibility checks, and static qualification only. No RQ2
model request is authorized until a later decision attests the frozen roster,
facts, renderers, salience formula, prompt, answers, leakage/parity audit,
manual review, smoke, analysis code, and runtime tree.

**Alternatives rejected.** Re-running RQ1b3 with a relaxed parser would be
outcome-driven and remains negative under sensitivity analysis. Moving directly
to RQ1c/RL/training violates three failed complementarity mechanisms. Testing
all dashboard changes in one end-to-end RCA comparison would confound content,
encoding, and arrangement. Treating the row sham as proof of benefit confuses
causal influence with correct influence. Opening heldout data before design
qualification would spend confirmatory evidence on an unproven renderer.

**Consequences.** RQ2 now owns six project-standard directories and a frozen
master protocol. `RQs/RQ2/src/` remains untouched. The immediate task is static
RQ2a implementation and qualification; GPU inference remains locked. RQ0/RQ1
results, locked RQ1 gate rosters, reserve, and heldout partitions are unchanged.

**Initial execution evidence.** The six-directory layout, frozen YAML contract,
16-cell factorial enumerator, eight matched anchor pairs per main effect, four
anchor quadruples per two-factor interaction, label-blind salience function,
and order-insensitive set canonicalizer are implemented under RQ2's mutable
`scripts/` tree. Nine RQ2 tests and targeted Ruff checks pass. The read-only
feasibility audit confirms 991 eligible exposed incidents, 373 cases reusable
from executed rosters, and 318 cases outside every frozen roster (94/115/109),
while preserving both locked RQ1 gates. The static qualification artifact is
SHA256 `9bf784b2ffa8135c017e45481c0d89ef97283e07c32422543c41c172cc43f7db`.
Its status is explicitly `passed_static_contract_only`; the listed renderer,
compiler, roster, audit, review, smoke, analysis, and runtime blocks still
prevent inference.

---

## DD-36: Fail the numeric service-ID interface before the missing RQ1 modality factorial
**Date:** 2026-08-04
**Status:** adopted; stop pending user review

**Context.** The RQ1 RoadMap includes a still-unrun `2x2x2` factorial over
whether metrics, logs, and traces/topology are represented visually or as
text. Before authorizing that experiment, the user asked for a direct test of
whether a VLM can combine renderer-v7's numbered propagation rows with its
numeric `CALLER RANK -> CALLEE RANK` key. Earlier RQ0 perception work showed
that the enlarged key made the numeric pair itself legible, but did not test
the necessary composition from each number to an exact service name. The user
explicitly required work to stop after this test if a model showed clear
mapping difficulty.

**Decision.** Treat RQ1b4 as a prerequisite perception qualification rather
than an efficacy experiment. Use 12 already-exposed incidents balanced across
the three primary datasets, actual/swapped/no-image conditions, and two exact
tasks: display-ID to service name and numeric edge to service-name edge. Stop
the sequence as soon as a completed required-model cell fails the frozen 0.80
macro, 0.75 per-task, and +0.40 visual-control-lift criteria.

The complete Gemma cell scored 0.4167 on actual-image macro accuracy, 0.4167 on
ID lookup, and 0.4167 on composed edge mapping. Both controls scored 0.0. All
36 calls succeeded and parsed without truncation, exact token and image hashes
matched, and the canonical Gemma batch-invariant runtime was attested. This is
a clear perception-gate failure. Do not run Qwen or the RQ1 factorial. Do not
interpret the positive visual-control lift as adequate accuracy or as an RCA
benefit.

Before reconsidering the factorial, remove the numeric indirection with a
separately approved label-blind renderer change—preferably direct service-name
caller/callee edges or a larger dedicated ID/name mapping region—and repeat an
independent mapping qualification. This decision does not itself authorize
that implementation or experiment.

**Evidence.** The authoritative analysis is
`RQs/RQ1/results/rq1b4_service_display_id_mapping_v1/analysis/analysis.json`;
the finding is
`RQs/RQ1/findings/rq1b4_service_display_id_mapping_finding.md`; the complete
Gemma trajectory has 36 unique episodes. Actual-image per-dataset ID/edge
accuracies are AegisLab 0.25/0.50, AIOPS-2022 0.75/0.25, and AIOPS-2025
0.25/0.50. Errors are dominated by service-name transcription and wrong-row
selection rather than infrastructure, parsing, truncation, or text priors.

**Relationship to prior decisions.** DD-34's historical RQ1b3 closure and all
earlier result statuses remain unchanged. This user-authorized missing-interface
qualification strengthens, rather than reverses, its prohibition on advancing
the current visual-complementarity mechanism. DD-35's RQ2 static-only status
also remains unchanged; no RQ2 inference was opened.

**Consequences.** The missing RQ1 factorial remains incomplete and blocked.
RQ1c, RQ1d, training, reserve, and heldout work remain closed. The project is
paused at the requested reporting point.

---

## DD-37: Open a forward-only RQ1 cross-region reasoning mechanism for implementation and smoke
**Date:** 2026-08-04
**Status:** adopted for implementation and Rule-16 smoke only

**Context.** DD-34 closed the failed RQ1b3 evidence-acquisition mechanism, and
DD-36 blocked the missing three-factor modality experiment after renderer-v7's
numeric-ID-to-service-name interface failed its registered perception gate.
Neither experiment tested a dependency chain in which the answer found in one
information region determines what must be read from a second or third region.
The user has now authorized a new, forward-only mechanism that measures direct,
two-region, and three-region reasoning and separates metrics, logs, traces, and
topology into four representation factors. Renderer-v12 has separately passed
CPU render qualification for an explicit numeric-ID explanation, balanced
typography, deterministic rendering, and boundary safety; that qualification
does not itself establish model perception or efficacy.

**Decision.** Adopt
`RQs/RQ1/descriptions/new_RQ1_plan.md` as the protocol authority for two new
experiments: RQ1b6, the cross-region reasoning ladder, and RQ1b7, the full
`2^4` metrics/logs/traces/topology representation factorial. Reasoning level is
the number of sequentially dependent distinct information regions, not graph
hop count. Each case contains one Level-1, one Level-2, and one Level-3 task;
each factorial cell answers the three-question packet in one call. The 16
nonredundant cells expose every incident fact exactly once. The additional H
cell is fixed as the all-visual image fragment A followed by the byte-identical
all-text fragment B, with no rewriting or deduplication.

This decision authorizes only provisional implementation under
`RQs/RQ1/scripts/`, frozen disabled full-run configurations, static/CPU tests,
and one registered Rule-16 smoke: exactly one validation case from RE2-OB,
AIOPS-2022, and AIOPS-2025, 17 conditions, and both Gemma and Qwen, for 102
requests total. Smoke correctness, parse success, and truncation are diagnostic
model outcomes rather than passage criteria; complete paired artifacts, frozen
hashes, accounting, writer drain, resume verification, and zero infrastructure
failures determine passage. Stop immediately after smoke verification.

For this new mechanism only, this user authorization narrowly supersedes the
parts of DD-34 and DD-36 that prohibited any further RQ1 implementation or
smoke. It does not reopen, rerun, reinterpret, repair, or rehabilitate their
failed mechanisms or artifacts. All historical RQ0/RQ1 statuses and evidence
scopes remain unchanged. DD-35 and RQ2's static-only status are also unchanged.

**Evidence.** The authority is the user's 2026-08-04 directive and the adopted
protocol named above. Renderer-v12's applicable but limited CPU evidence is
recorded in
`RQs/RQ1/findings/rq1b5_numeric_entity_id_explanation_renderer_v12_finding.md`;
it is renderer qualification only. No model perception, factorial, transfer,
development, independent-gate, heldout, or efficacy result exists for RQ1b6 or
RQ1b7 at adoption time.

**Alternatives rejected.** Reinterpreting Legacy-Q9 as multi-region reasoning
would change a historical task after outcome observation. Reusing the old
three-factor bundle would prevent traces and topology from having separate
estimands. Mapping numeric IDs back to natural service names would reintroduce
the failed DD-36 interface; the new exact-match tasks instead answer in
case-local numeric IDs while preserving an evaluator-private one-to-one map.
Splitting the three questions into separate model calls would triple the
registered compute and break the one-packet comparison. Opening a 12-case
perception gate or 90-case experiment before the new pipeline passes smoke
would spend evidence on unqualified infrastructure.

**Consequences.** `RQs/RQ1/src/` remains frozen. Legacy-Q9 and every historical
run remain byte-for-byte and status-preserving. The only permitted GPU work is
the isolated 102-request smoke under
`RQs/RQ1/results/rq1b6_b7_cross_region_smoke_v1/`. The 12-case perception gate,
both 90-case rosters, 30-case full-dashboard transfer, heldout/reserve access,
RQ1c/RQ1d, SFT, LoRA, GRPO, and all other training remain blocked until a later
explicit decision.

**Implementation clarification (2026-08-04, before smoke freeze).** The new
controlled-task eligibility universe uses all metric series from the
structurally label-free `CaseRenderView`, not the legacy full-dashboard CEB's
top-12 selected panels. The latter is a representation projection and omitted
real topology endpoints in the only authorized AIOPS validation cases. The
frozen selector is outcome-blind: one highest-ranked usable series per entity,
then the existing 64-to-16 robust-z transformation. If a telemetry family has
no display-unique first-step anchor, template selection rotates within the
registered level's template list from an opaque-hash start and accepts the
first exactly scoreable task; it never invents uniqueness. This clarification
preserves fact equality because the selected facts, values, precision, and
missingness remain identical across all 17 cells. It changes no historical
artifact or status and does not expand the authorized GPU scope.

**Runtime compatibility clarification (2026-08-04, before a valid smoke).**
Freeze `mm_processor_cache_gb=0` for both required models and every condition.
The first real image requests showed that vLLM 0.24's live multimodal
`/tokenize` preflight populated the API-process mirrored LRU without a matching
engine receiver entry, after which generation failed with `Expected a cached
item for mm_hash`; the text-only cell completed. Disabling this officially
supported CPU-side preprocessing cache makes token preflight and generation
process each image directly. It does not change the checkpoint, BF16 precision,
image facts or pixels, image encoder, decoding parameters, context/output
ceilings, or per-arm call budget. The setting is symmetric across Gemma/Qwen
and all 17 conditions and must be recorded by server attestation. The failed
diagnostic attempts remain excluded infrastructure artifacts and provide no
accuracy evidence.

**Cross-tokenizer context clarification (2026-08-04, before a valid smoke).**
Freeze the all-text serializer as `RQ1CrossRegionLosslessJSONRowsV1`: one
column-order declaration per M/L/R/G section followed by one canonical JSON
array per atomic fact in `[entity, field, relative_bin, value, unit]` order;
the section header supplies domain. The initial Qwen preflight found that the
semantically correct but verbose per-fact JSON-object form placed 12 of 51
prompts at 16,565–18,573 input tokens. With the frozen 32,768 context and
16,384 requested output ceiling, vLLM correctly rejects inputs over 16,384
before generation. No Qwen generation occurred. Compact rows remove only
repeated key spellings: all facts, values, units, precision, bins,
missingness, per-fact location mappings, image bytes, H=A+B composition and
question bytes remain intact. Lowering output limits per cell, deleting facts,
or relaxing the preflight is prohibited. The completed predecessor Gemma
diagnostic and failed Qwen preflight remain archived and cannot be mixed with
the newly frozen two-model smoke; both models must rerun on the same compact
prepared inputs.

**Execution result (2026-08-04).** The newly frozen smoke completed and passed
its post-hoc verifier. Gemma and Qwen each produced 51 completed trajectories
covering three validation cases by all 17 conditions; the combined artifact
contains 102 unique calls, complete pairing, zero infrastructure failures,
zero truncations, drained writers, complete token/GPU/wall-time accounting and
verified config, model, roster, prompt, fact, image, code and resume hashes.
The authoritative report is
`RQs/RQ1/results/rq1b6_b7_cross_region_smoke_v1/qualification/smoke_qualification.json`
with `status=passed` and verification hash
`7d26181628e62f412c8736944b824fe8a0b6dbc7a1dc7850d0f43584df105381`.
Gemma/Qwen complete-chain exact-match accuracies of 0.3595/0.8105 and parse
rates of 0.9412/0.9804 are diagnostic smoke outcomes over only three cases;
they are not RCA AC@1/MRR, do not test P1–P3 and cannot authorize an efficacy
claim. The three Gemma duplicate-value schema failures and one Qwen
wrong-step-count failure remain model outcomes. In accordance with the frozen
stop boundary, no perception gate, 90-case run, transfer, heldout access or
training follows automatically from this passage.

---

## DD-38: Promote the passed RQ1b6/b7 smoke into the registered gated execution sequence
**Date:** 2026-08-04
**Status:** adopted; perception gate authorized, later stages remain conditional

**Context.** DD-37 authorized implementation and the Rule-16 smoke only. That
smoke has now passed with 102/102 complete calls, zero infrastructure failures,
complete pairing, frozen hashes, and verified accounting. The user explicitly
authorized continued RQ1 execution and requested that each qualified stage
proceed to the next without an informal pause. The registered
`new_RQ1_plan.md` nevertheless makes perception a prerequisite for the larger
factorial, so authorization cannot erase its scientific stop condition.

**Decision.** Adopt
`RQs/RQ1/descriptions/rq1b6_b7_execution_protocol_v1.md` as the execution
transition for RQ1b6/RQ1b7. Before opening any newly selected artifact, freeze
four mutually disjoint, exposed-only roles after excluding all pre-existing
RQ1 private rosters: 12 perception cases, 90 development cases, 90 independent
gate cases, and 30 transfer cases, each balanced across AegisLab, AIOPS-2022,
and AIOPS-2025. Run the 12-case perception gate first on both Gemma and Qwen
using factual, deterministic same-dataset swapped-image, and neutral-image
conditions. The negative controls are perception controls and must not be
treated as information-equal efficacy arms.

Promotion to the 90-case development factorial requires the frozen primary
Gemma perception thresholds. Qwen must complete and its architecture-specific
gate result must be reported, but a Qwen-only failure does not veto the Gemma
primary experiment and does not permit omitting Qwen later. A failed primary
gate blocks the efficacy sequence; it may be debugged only under a new
versioned exposed-development protocol. If the primary gate passes, run the
90-case development factorial, then the disjoint independent gate only after
analysis choices are frozen, and finally the 30-case T/V/H transfer. Never
open heldout, reserve, RE2-TT, or training data in this sequence.

**Evidence.** The preceding smoke verification and hashes are recorded under
DD-37. The new roster assignment hashes are `4acf7bff...` (perception),
`5e593bf0...` (development), `55e15dfb...` (independent gate), and
`f08fc4f3...` (transfer); their complete values live in the frozen public
rosters under `RQs/RQ1/configs/rosters/`. The 12 prepared perception inputs
passed schema, information-parity, exact A+B, repeat-render, leakage,
answer-material, and compiler clipping qualification before any model call.

**Consequences.** DD-37's smoke-only stop is superseded only for this ordered
sequence. Historical RQ0/RQ1 statuses remain unchanged and `RQs/RQ1/src/`
remains frozen. The next authorized GPU action is the 72-call two-model
perception gate; downstream calls remain conditional on its registered result.

**Execution result.** The perception run completed 72/72 registered calls with
zero infrastructure failures and zero truncations, but the scientific gate
failed. Gemma actual Level-1/Level-2 complete-chain accuracy was 0.083/0.333;
Qwen was 0.833/0.917. Gemma actual-minus-control was 0.083 versus the required
0.40. Qwen showed a large 0.875 visual-control lift but failed the direct-edge
family and all-condition parse criteria. The authoritative amended verifier is
`RQs/RQ1/results/rq1b6_b7_cross_region_perception_gate_v1/analysis/perception_gate_verification_v2.json`
with hash `fc1f4d02cb078e7b5ac4695a7f647a437b0d211d02d054f145edc28d9a276809`.
The 90-case factorial, independent gate, and transfer are therefore blocked.

---

## DD-39: Diagnose the architecture-specific perception failure with fixed region crops
**Date:** 2026-08-04
**Status:** adopted for exposed-development diagnosis only

**Context.** Perception gate v1 establishes that the controlled facts are
visually usable by Qwen but not by primary Gemma. Qwen factual Level-1/2
case-macro accuracy was 0.875 versus 0.000 for both negative controls, whereas
Gemma scored 0.208 versus 0.125 for the stronger control. Gemma trajectories
show pervasive small-number and wrong-row errors across all four regions. The
single 3072x2048 image is therefore a plausible architecture-specific
downsampling bottleneck. The direct-neighbor task also has an avoidable output
convention ambiguity around absent directions and `:` versus `=`.

**Decision.** Adopt
`RQs/RQ1/descriptions/rq1b6_b7_region_crop_recovery_protocol_v1.md`. On only the
already exposed v1 perception cases, run a 36-call Gemma renderer-development
diagnostic separating full-canvas prompt clarification, four lossless fixed
region crops, and crops plus clarification. Select by the frozen accuracy,
minimum-family, Level-3, token, and intervention ordering in that protocol.
This diagnostic cannot support an RQ1 claim.

If and only if a candidate passes its development screen, implement that
representation consistently in all 17 cells, preserve exact fact equality and
H=A+B, rerun a two-model Rule-16 smoke, and then use a fresh outcome-blind
12-case subset from the already frozen exposed-development roster for a
two-model independent perception gate at the original thresholds. Do not
reclassify the failed v1 gate and do not open heldout, reserve, RE2-TT, or
training data.

**Consequences.** RQ1b6/RQ1b7 remain open but blocked from efficacy-scale
execution. RQ2 and later RQs do not start yet because RQ1 has not established a
qualified representation. `RQs/RQ1/src/` remains frozen.

**Execution result.** The diagnostic completed all 36 registered Gemma calls
with complete three-condition pairing, zero infrastructure failures, zero
truncations, drained asynchronous writes, and verified crop/source hashes. The
best condition was `four_region_crops_clarified`: Level-1/2/3 complete-chain
accuracy was 0.500/0.667/0.500, compared with 0.167/0.167/0.000 for the
clarified single canvas. The crop therefore repaired a substantial part of
the architecture-specific small-text failure, but it did not pass the frozen
screen: direct-edge accuracy remained 0.000 and parse rate was 0.833. The
authoritative analysis is
`RQs/RQ1/results/rq1b6_b7_region_crop_recovery_v1/analysis/analysis.json` with
hash `424e780ea319a6ebddabc4272db137f34e4aaa5044e9ea2131b872cde25d0dbd`.
No downstream roster is opened by this result.

---

## DD-40: Localize packet structural failures and teach target-relative edge semantics
**Date:** 2026-08-05
**Status:** adopted for a second exposed-development recovery diagnostic only

**Context.** DD-39 showed that fixed lossless region crops improve Gemma's
cross-region perception but leave two separable blockers. First, the v1 packet
parser converts one question's wrong step region or step count into a global
`parse_ok=false`, after which all three questions in the call score zero. That
is stricter than the registered inferential design: the questions are scored
separately and only the case is the statistical unit. A structurally valid
answer to one query must not be erased by a different query's semantic path
error. Second, direct-edge inspection shows genuine target-relative direction
errors even though the G crop visibly lists `CALLER -> CALLEE`. One output was
semantically correct but used colon spelling; the other responses frequently
reported the target itself as its own neighbor or added an unsupported
direction.

**Decision.** Adopt
`RQs/RQ1/descriptions/rq1b6_b7_topology_semantics_recovery_protocol_v2.md`.
Keep every historical v1 artifact and status unchanged. Add a forward-only v2
packet parser that reserves packet parse failure for invalid JSON/schema,
duplicate/missing query IDs, or another packet-wide structural defect. Step
count, step index, and registered-region mismatch are scored as failures only
for the affected query. Do not normalize colon spelling, remove extra values,
or otherwise repair model answers.

On the same 12 already exposed perception cases, run Gemma with the four exact
lossless M/L/R/G crops under two conditions: the DD-39 clarification control
and a candidate that additionally gives a label-blind target-relative edge
rule plus a synthetic notation example. The rule states that `U -> X` yields
`upstream=U` for target X, `X -> D` yields `downstream=D`, the target is not a
neighbor absent a visible self-loop, and separate neighbors must be separate
strings using equals signs. It does not name any incident entity, select or
highlight a supporting row, reorder evidence, or expose an answer. Promotion
uses the existing DD-39 development thresholds and requires the candidate—not
merely the control—to pass.

**Alternatives rejected.** Post-hoc punctuation normalization would conceal a
real output-contract failure. Highlighting the queried topology row would make
the task answer-directed and violate the registered no-answer-highlight rule.
Dropping the direct-neighbor family after observing its failures would change
the question roster to fit results. Opening the 90-case factorial because the
crop improved aggregate accuracy would bypass the registered minimum-family
gate.

**Consequences.** This is still exposed renderer/prompt development, not RQ1
evidence. It authorizes no independent, heldout, transfer, training, or
90-case execution. If the candidate passes, it must be implemented symmetrically
in all relevant T/V/H and factorial prompts, followed by a new two-model
Rule-16 smoke and a fresh two-model independent perception gate. If it fails,
RQ1b6/RQ1b7 remain blocked and the failure must be recorded before any further
mechanism is proposed.

**Execution result.** ParserV2 behaved as intended: both 12-call conditions
had packet parse rate 1.000 with zero infrastructure failures. The topology
tutorial raised direct-edge accuracy from 0.000 to 0.667, showing that the
caller/callee pixels are readable and the missing operation is endpoint-relative
semantics. It nevertheless failed promotion: Level-1/2 accuracy was
0.667/0.417 and trace-edge-to-topology accuracy was 0.500. Paired trajectories
show that the long global tutorial changed answers to unrelated M/L/R questions,
so it is an attention/prompt-interference mechanism rather than a generally
qualified repair. The authoritative analysis is
`RQs/RQ1/results/rq1b6_b7_topology_semantics_recovery_v2/analysis/analysis.json`
with hash `7eceb0b3eb683470da93045302988adbaa8684fafba863357eddaefc1eea448b`.

---

## DD-41: Encode endpoint-relative direction inside each topology edge row
**Date:** 2026-08-05
**Status:** adopted for exposed renderer development only

**Context.** DD-40 proved that explicit endpoint semantics can repair Gemma's
direct-edge operation, but its long global example distracts unrelated
questions. The G crop has ample unused space, and each edge is already one
atomic fact with caller and callee. A compact, row-local redundant encoding can
make the same fact operational without highlighting a queried edge or adding a
case-specific fact.

**Decision.** Adopt
`RQs/RQ1/descriptions/rq1b6_b7_topology_endpoint_encoding_recovery_protocol_v3.md`.
For every displayed topology edge `U -> D`, keep the existing edge-ID/caller/
callee row and add a second line inside the same fact primitive:
`upstream of D: U | downstream of U: D`. Update the common legend for every
text and visual condition to the equivalent concise rule. Do not include a
worked example, queried target, highlight, answer-dependent ordering, or
support marker. The fact ID, caller, callee, edge ID, inventory, precision, and
source selection remain unchanged; the visual row is only a redundant encoding
of that same edge fact, while text arms receive the edge and common rule.

Run one 12-call Gemma diagnostic on the same exposed cases with exact M/L/R/G
region crops and ParserV2. Promotion requires the full existing development
screen. This is the final prompt/renderer recovery attempt on the v1 case set;
if it fails, do not keep tuning against these cases. Instead report that the
primary Gemma architecture has not qualified for this operation and seek a new
preregistered RQ1 design decision.

**Consequences.** Historical renderers, v1/v2 runs, and their statuses remain
unchanged. The renderer identifier is versioned forward. No 90-case,
independent, transfer, heldout, reserve, or training execution is authorized by
this decision. A pass still requires a new two-model Rule-16 smoke and fresh
two-model independent perception gate before efficacy-scale work.

**Execution result.** The v3 source compiler passed all 12-case/17-condition
schema, exact-information, H=A+B, determinism, leakage, fact-location and
clipping checks, and the crop artifacts passed exact pixel/inventory checks.
All 12 Gemma calls completed with parse 1.000 and zero infrastructure failures,
but the scientific screen failed: Level-1/2/3 accuracy was
0.583/0.417/0.417; direct-edge, metric-to-topology and
trace-edge-to-topology accuracy was 0.333/0.333/0.250. The authoritative
analysis is
`RQs/RQ1/results/rq1b6_b7_topology_endpoint_encoding_recovery_v3/analysis/analysis.json`
with hash `4d20a0a1555c757798e20195ee60fbdee65bae86f560ec518429dcbaaf54bbad`.
Per the preregistered stop rule, no further prompt or renderer tuning may use
the v1 perception cases.

---

## DD-42: Replace single-turn packet answering with matched two-stage observation
**Date:** 2026-08-05
**Status:** adopted for forward-only implementation and Rule-16 smoke

**Context.** Three bounded recovery attempts establish that region crops make
Gemma's visual facts more readable and explicit direction rules can repair a
specific operation, but single-turn joint perception and three-question
reasoning remains unstable. Continuing to tune the same cases would overfit.
The RQ1 roadmap already distinguishes evidence acquisition from diagnostic or
cross-region reasoning through an `Observe and Connect -> Diagnose` boundary.
The failed mechanism combined both inside one response, so it did not test
that registered agent decomposition.

**Decision.** Introduce RQ1b8, a two-stage cross-region Observer, under
`RQs/RQ1/descriptions/rq1b8_two_stage_observer_protocol_v1.md`. Stage 1 receives
the complete question packet and exactly one representation cell, then emits a
strict evidence ledger containing raw displayed M/L/R rows and G caller/callee
rows relevant to each registered step. It may not emit the final normalized
answer. Stage 2 receives only the ledger, common question packet and output
schema; it never reopens the images or source text. Every cell uses exactly two
model calls with identical limits and stopping rules.

Visual regions are supplied as fixed M/L/R/G crops in canonical order; text
regions use the lossless serializer. Non-H factorial cells encode each fact
exactly once, and H is the exact ordered concatenation of the all-visual crop
parts A and byte-identical all-text part B. The endpoint semantics remain a
common legend, not an answer highlight. ParserV2 is used; historical artifacts
are not rescored.

First implement only provisional code and a new two-model Rule-16 smoke on the
same three authorized validation cases, covering all 17 cells and both stages
(204 calls). Smoke passage remains infrastructure/artifact based, not
correctness based. If it passes, freeze an outcome-blind 12-case subset from
the previously frozen, unused 90-case exposed-development roster and run a
fresh two-model observation gate. No v1 perception case may be used for tuning
or selection. The 90-case factorial remains blocked until this fresh gate
passes.

**Alternatives rejected.** Splitting the three questions into three independent
calls would triple the already large 17-cell budget and would not expose a
shared evidence ledger. Training another case-level root-ranker would not
address the demonstrated perception/reasoning coupling. Promoting Qwen alone
after observing the Gemma failure would make architecture selection
outcome-dependent. Relaxing the family gates would hide rather than fix the
failed operation.

**Consequences.** RQ1b6/RQ1b7 single-turn results remain failed qualification
evidence. RQ1b8 is a distinct forward mechanism, not a rehabilitation. The
next authorized GPU work is the two-model Rule-16 smoke only; `src/`, heldout,
reserve, RE2-TT, training, RQ2 and all efficacy-scale calls remain blocked.
### DD-43 — Promote RQ1b8 from Rule-16 smoke to a fresh two-stage perception gate

**Date:** 2026-08-05
**Status:** Accepted; limited promotion only
**Supersedes:** None; executes the conditional next step in DD-42

**Decision.** The RQ1b8 two-stage observer mechanism passed its registered
Rule-16 smoke and is promoted only to a fresh 12-case exposed-development
perception gate. The new roster must contain four cases from each of AegisLab,
AIOPS-2022 and AIOPS-2025, be selected outcome-blind from the already frozen
90-case development roster, and be disjoint from the 12 cases used by the
single-turn perception/recovery sequence. Both Gemma and Qwen must run factual,
same-dataset swapped-visual and neutral-visual controls through both stages.
The 90-case development factorial, independent gate, transfer experiment,
heldout data and training remain blocked.

**Evidence.** `rq1b8_two_stage_observer_smoke_v1` completed and post-hoc
verified all `204/204` registered calls with zero infrastructure failures,
complete model/case/cell/stage pairing, drained asynchronous writers, and
matching config, roster, prompt, fact, image, ledger-transfer, scoring and code
hashes. Gemma Stage-1/Stage-2 parse rates were `1.000/0.961`; Qwen rates were
`0.922/0.980`. Qwen produced four Stage-1 length truncations at the registered
16,384-token ceiling; these are preserved model outcomes and did not affect
Rule-16 passage. Smoke accuracy is diagnostic only and is not efficacy
evidence.

**Reason.** Infrastructure and artifact integrity are qualified, while the
fresh perception gate is the smallest registered experiment that can test
whether the observer actually extracts visual evidence better than matched
controls. Advancing directly to 90 cases would confound a mechanism failure
with the factorial efficacy test and waste substantially more Qwen compute.

**Revisit condition.** Unlock the 90-case development factorial only if the
fresh primary-model gate passes its frozen perception, control-lift, parse and
integrity thresholds. A failed gate returns the mechanism to exposed-only
development and cannot be repaired by opening the independent or heldout sets.

### DD-44 — Add label-blind task eligibility to the fresh RQ1b8 roster

**Date:** 2026-08-05
**Status:** Accepted before any perception-gate model call

**Decision.** Preserve the first fresh roster and its partial preparation as a
failed static attempt. Freeze a version-2 roster from the same development-90
source and the same per-dataset outcome-blind hash order, but require the exact
packet compiler to produce a valid Level-1/2/3 packet at the case's prospective
assignment index. Record every examined case and rejection reason in a private
eligibility audit. Do not change prompts, questions, controls, thresholds,
models, or inference settings.

**Evidence and reason.** Preparation stopped on the sixth v1 case because no
Level-1 template had a display-unique anchor at the frozen 16-bin precision.
No VLM server was running and no model call or result existed. Task
scoreability is a deterministic property of label-blind supplied facts, so it
must be resolved before roster freeze rather than converted to an
infrastructure/model failure or replaced after observing an outcome.

**Consequences.** The v1 roster assignment `5a0b479b...` is static-ineligible
and never evidentiary. The v2 roster remains exposed-development only and must
still be disjoint from old perception cases. The 90-case factorial remains
blocked until the unchanged primary-model perception thresholds pass.

**Freeze result.** The eligibility-aware v2 roster examined 13 candidates and
froze 12 cases (four per dataset) with assignment hash
`2dc7ca3cc5ba5e448bf6d84548d9824f08e9bda77d5696806cc5a1d1177e7960`.
Exactly one candidate was rejected by the label-blind compiler. Its private
audit is `RQs/RQ1/configs/selections/rq1b8_perception_eligibility_audit_v2.json`.

### DD-45 — Reject RQ1b8 promotion and isolate the typed handoff bottleneck

**Date:** 2026-08-05
**Status:** Accepted; RQ1 efficacy-scale execution remains blocked
**Supersedes:** The conditional promotion branch in DD-43; DD-42 remains valid
as historical motivation and a completed mechanism test

**Decision.** RQ1b8 failed its fresh two-stage scientific gate. Do not launch
the 90-case RQ1b6/RQ1b7 factorial, independent gate, full-dashboard transfer,
heldout evaluation, training or RQ2 efficacy chain from this mechanism. Keep
all 144 complete two-model calls as valid exposed-development perception and
mechanism evidence. Authorize only a forward-versioned RQ1 exposed-development
intervention that replaces the free-form Stage-1 row strings with a typed,
lossless series/edge ledger and adds public per-step answer-kind contracts.
The new contract must carry all 16 displayed bins, constrain allowed output
shapes without enumerating answer values, preserve the same atomic facts and
remain disjoint from every case used to derive this change.

**Evidence.** The authoritative verification is
`RQs/RQ1/results/rq1b8_two_stage_perception_gate_v2/analysis/two_stage_perception_gate_verification.json`
with verification hash
`dd1ee2f4460f9b02e300cd1cfc41ef91b2d27320069d41ac762b69dd1a798e04`.
Both models completed 72/72 calls with zero infrastructure failures and zero
truncations. Gemma factual Level-1/2 accuracy was `0.750/0.333`; Qwen was
`0.917/0.500`. Both failed the direct-edge and trace-edge-to-topology family
requirements. Nevertheless, factual minus strongest-control Level-1+2 accuracy
was `+0.542` for Gemma and `+0.667` for Qwen, so correct images clearly supplied
usable case-specific evidence.

The post-hoc attrition diagnostic has report hash
`404366c8adc0170a2b7edca51ba318adb39a346460c0cca5aba7f7923f3fe47b`.
It does not rescore the gate. Stage-1 support completeness was `0.861` for
Gemma and `0.833` for Qwen, but `0.323` and `0.233` of support-complete queries
respectively were lost in Stage 2. Most topology failures already contained the
correct caller/callee row; models then emitted the wrong target-relative role
or an unregistered value label. In addition, the ledger schema's eight-string
limit bound two Gemma 16-bin steps and one Qwen step. The observed failure is
therefore a mixed handoff-capacity and answer-semantics defect, not evidence
that the pixels contain no usable signal.

**Verifier correction.** The first combined verifier invocation failed before
analysis because it requested the nonexistent configuration key
`models.required_models`; the frozen contract uses `models.execution_order`.
The post-hoc verifier now reads that already-frozen two-model order. This is a
non-scientific schema repair: it changes no model output, metric, threshold,
case, prompt or gate decision and is regression-tested.

**Alternatives rejected.** Relaxing the frozen thresholds would convert a
failed gate into an outcome-selected pass. Normalizing or stripping the
existing model answers post hoc would conceal real contract failures. Running
the factorial because control lift passed would ignore the registered
operation-reliability criteria. Reusing the same 12 cases for another prompt
iteration would overfit the mechanism to observed trajectories.

**Revisit condition.** A typed successor may reopen the factorial only after
its own two-model Rule-16 smoke and a fresh, disjoint, template-balanced
two-model perception gate both pass their preregistered integrity, perception,
family, control-lift and parse thresholds. Until then, RQ1 remains at
exposed-development qualification and RQ2 may be planned but not justified as
the downstream efficacy continuation.

### DD-46 — Bound an unparseable Stage-1 handoff before rerunning RQ1b9 smoke

**Date:** 2026-08-05
**Status:** Accepted after the failed v1 implementation qualification
**Supersedes:** Only the unbounded parse-failure transfer in RQ1b9 v1; DD-45,
the typed evidence/answer contracts, scientific thresholds and blocked
efficacy-scale work remain unchanged

**Decision.** Preserve `rq1b9_typed_handoff_smoke_v1` as an incomplete failed
implementation attempt and do not resume or overwrite it. Register a v2
Rule-16 smoke on the same authorized validation roster. When Stage 1 parses,
v2 transfers the complete typed ledger exactly as before. When Stage 1 does
not parse, v2 transfers only a bounded, deterministic failure marker containing
status, parse error, finish reason, truncation flag, raw-response byte length
and SHA-256. It must not transfer the raw failed response, synthesize a ledger,
repair an answer, reopen the original image/text evidence or alter the private
score. Stage 2 therefore records an ordinary model-outcome failure using only
the public questions and the marker while remaining inside the registered
32,768/16,384 context budget.

**Evidence and reason.** Gemma v1 completed 19 of its 102 requested calls with
zero service failures before the runner failed closed. Its ninth completed
Stage-1 call generated the full 16,384-token ceiling, was recorded as
`finish_reason=length`, `truncated=true`, and could not be parsed. The v1
fallback serialized the entire 440,598-byte response into Stage 2. Token
preflight then correctly rejected `17,146 + 16,384 > 32,768` before issuing the
Stage-2 request. This is an implementation defect in failure propagation, not
a model-quality, information-equality or GPU failure. Carrying a hash-bound
failure marker preserves provenance without spending context on unusable
malformed output.

**Consequences.** V1 is diagnostic only and cannot satisfy Rule 16. V2 must
repeat the complete two-model 204-call smoke under a new experiment ID, output
root, config hash and runtime freeze. Smoke correctness and parse remain
non-gating, while zero infrastructure failure and complete pairing remain
mandatory. The fresh 12-case perception gate, 90-case factorial, independent
gate, transfer, heldout, training and RQ2 efficacy work remain blocked until a
v2 smoke passes and the unchanged scientific gate subsequently passes.

### DD-47 — Promote RQ1b9 v2 only to a fresh typed perception gate

**Date:** 2026-08-05
**Status:** Accepted; limited promotion only
**Supersedes:** None; executes the conditional next step in DD-46

**Decision.** RQ1b9 v2 passed its two-model Rule-16 smoke. Promote only the
typed, bounded-failure two-stage mechanism to the preregistered fresh 12-case
exposed-development perception gate. Freeze four cases per primary dataset,
disjoint from every prior single-turn and RQ1b8 perception/recovery case, using
label-blind task eligibility and a template-balanced roster fixed before any
new model call. Run factual, within-dataset matched swapped-visual and neutral
controls through both stages for Gemma and Qwen. Preserve the unchanged
thresholds in the v1/v2 typed protocol. Do not launch the 90-case factorial,
independent gate, full-dashboard transfer, heldout, training or RQ2 efficacy
work unless the primary Gemma scientific gate passes.

**Evidence.** The authoritative report is
`RQs/RQ1/results/rq1b9_typed_handoff_smoke_v2/qualification/smoke_qualification.json`
with qualification hash
`222753b1d31905dccce9b1583a47696415310f85f6eaacae6f47b220600022ec`.
It verifies 204/204 calls, complete model/case/cell/stage pairing, zero
infrastructure failures, exact config/roster/prompt/fact/image/transfer/code
hashes, conversation histories, accounting and drained writers. Gemma
Stage-1/Stage-2 parse counts were 48/51 and 51/51; one Gemma Stage-1 output
reached the frozen 16,384-token ceiling and was safely propagated through the
359-byte hash-bound failure marker. Qwen parsed 51/51 calls at both stages and
had no truncation. Diagnostic complete-chain accuracy was 0.739 for Gemma and
0.863 for Qwen, but correctness was not a smoke passage criterion.

**Reason.** The bounded transfer is now infrastructure-qualified, while a
matched negative-control gate is still required to establish that factual
visual evidence, rather than schema compliance or language priors, supports
the registered operations. A 12-case balanced gate is the smallest authorized
scientific discriminator before the 90-case factorial budget.

**Revisit condition.** Unlock the 90-case factorial only if Gemma passes every
frozen Level-1, Level-2, family, control-lift, parse and infrastructure
criterion. A failure preserves the typed route as negative mechanism evidence
and cannot be repaired on the same cases or by selecting Qwen alone.

### DD-48 — Reject the first RQ1b9 gate roster before rendering

**Date:** 2026-08-05
**Status:** Accepted before any roster-v1 render or model call
**Supersedes:** Only the incomplete Level-1 balancing rule in the first DD-47
roster-freeze implementation

**Decision.** Preserve `rq1b9_typed_perception_*_v1.json` as a frozen but
static-ineligible roster attempt. It must not be rendered, prepared or used for
inference. Freeze a v2 roster from the same development-90 source, the same
prior-case exclusions and the same label-blind compiler/rank rule, while
requiring the eight non-topology Level-1 tasks to cover M, L and R with counts
2/3/3 in any deterministic permutation. Keep all other quotas unchanged:
four cases per dataset, four G-direct, four M-to-G, four R-to-G, four other
Level-2, three of every Level-3 template, and within-dataset G/all-Level-2
coverage.

**Evidence and reason.** The first solver froze 12 disjoint cases with roster
hash `81d3b6aa273090166e60ef1e2c853a19b59812a4999828327f71c1400fdd0bd3`
and audit hash
`2a87ab5f87cf88243493eff15183503d921a4220779e5eb9d7f34812c9045f0f`.
It satisfied every implemented quota, but its Level-1 counts were G=4, L=3,
R=5 and M=0. The registered protocol says the other eight questions cover
M/L/R numeric direct reads; omitting M would make the direct-read and later
factorial interpretation incomplete. This was detected from public template
metadata before rendering or inference and uses no label or model outcome.

**Consequences.** V1 remains non-evidentiary and cannot be rehabilitated. The
v2 freeze is a static protocol correction, not outcome-driven case replacement.
All GPU work remains blocked until v2 passes exact balance, disjointness,
information-parity and leakage qualification.

### DD-49 — Freeze the balanced RQ1b9 v2 gate roster and register execution

**Date:** 2026-08-05
**Status:** Accepted; preparation and the two-model typed perception gate are
authorized, but efficacy-scale work remains blocked
**Supersedes:** The blocked v2-roster state at the end of DD-48; it does not
relax DD-45 or DD-47

**Decision.** Use only `rq1b9_typed_perception_*_v2.json` for the RQ1b9
typed-handoff perception gate. Register the gate under
`rq1b9_typed_perception_gate_v1` with an independent deterministic swap salt,
the already-qualified lossless/bounded typed transfer, and the unchanged RQ1b8
scientific thresholds. Authorize static preparation, qualification, canonical
Gemma inference, canonical Qwen inference, and the combined verifier. Do not
run the 90-case factorial or any later experiment until the combined verifier
applies the preregistered Gemma promotion rule.

**Evidence.** The roster contains 12 fresh exposed-development cases, four per
dataset, and has zero overlap with the single-turn perception roster and both
RQ1b8 perception rosters. Its assignment hash is
`b7cc195bf2e7000194ded55088807ccd74462626dbc4fe914712877bc1e4beca`,
selection hash is
`b72670f320cf82c7c9a9934c6c0de105cbe5c58456cd9e52d9c584a560d7aa6d`,
and label-blind eligibility-audit hash is
`f24ba3cfd859cceffe21663797a6094d9ce9851c0e79d5301d13af35a2bbc463`.
The frozen Level-1 counts are G/M/L/R = 4/2/3/3; M-to-G, R-to-G and other
Level-2 counts are 4/4/4; every Level-3 template has three cases; every dataset
contains G-direct and both registered topology-link Level-2 families. All 77
eligible nonexcluded candidates compiled; no label, fault type, root cause or
model outcome entered selection.

**Reason.** The v2 roster repairs the pre-inference coverage omission detected
in DD-48 while preserving the same source pool, exclusions and outcome-blind
selection mechanism. The separate swap salt makes the new donor map an
explicit versioned contract without changing historical RQ1b8 behavior.

**Revisit condition.** Only a complete, integrity-passing two-model run whose
primary Gemma result passes every unchanged scientific threshold may unlock a
typed 90-case development factorial. Otherwise this mechanism route stops and
the same 12 cases may not be tuned or replaced using observed outcomes.

**Preparation and runtime freeze.** All 12 realized packets reproduced the
registered template balance. Static qualification passed schema, 17-cell fact
parity, strict A+B, leakage, answer-material separation, renderer determinism,
typed contracts and clipping checks across 432 image parts. The project and RQ1
test selection passed 269 tests. An initial runtime freeze was created before a
new test file's import-order lint was corrected; it was never used for a model
call and is preserved only as an operational predecessor. The sole authoritative
execution freeze is `contracts/runtime_freeze_v2.json`, with freeze hash
`00427feb027299ea8de90a68cb6fa7bc8b1848de4b48888a66b0d7eb4cc7447f`
and runtime-tree hash
`c81dd7f7a6153fb7004cda8f3764925c122123257ac2a96d3c7ceb4b1274dd36`.

### DD-50 — Stop the RQ1b9 typed two-stage route after the primary gate failure

**Date:** 2026-08-05
**Status:** Accepted; RQ1b6/RQ1b7 efficacy-scale execution remains blocked
**Supersedes:** The conditional promotion branch in DD-47 and DD-49; it does
not alter the validity or historical status of any completed artifact

**Context.** RQ1b9 tested whether the capacity-safe typed Stage-1 handoff could
make the controlled visual operations reliable enough to justify the 90-case
reasoning/factorial experiment. Gemma was frozen as the primary promotion
authority and Qwen as the mandatory architecture control. Promotion required
the primary model to pass every unchanged perception, family, control-lift,
parse and infrastructure threshold.

**Decision.** Reject promotion of the typed two-stage mechanism. Do not run the
90-case RQ1b6/RQ1b7 factorial, independent gate, full-dashboard transfer,
heldout evaluation, training or RQ2 efficacy continuation with this mechanism.
Keep all 144 calls as valid exposed-development perception/mechanism evidence.
Record Qwen's pass as architecture-specific evidence, not as authority to
replace the preregistered primary model. Do not tune another handoff or prompt
on these 12 observed cases.

**Evidence.** The authoritative verification is
`RQs/RQ1/results/rq1b9_typed_perception_gate_v1/analysis/typed_handoff_perception_gate_verification.json`
with verification hash
`44e63019ef925f45e494d2eb606d72d2e629b737c1fa8356380c83b2ed350794`.
Both models completed 72/72 calls with complete pairing and zero
infrastructure failures. Gemma factual Level-1/Level-2 accuracy was
`0.583/0.417`, direct-edge was `0.000`, metric-to-topology was `0.250`, and
parse rate was `0.931`; all five are below their frozen requirements. Its
factual-control lift passed at `+0.417`. Qwen passed every identical criterion:
Level 1 `0.917`, Level 2 `1.000`, direct-edge `0.750`, both topology-link
families `1.000`, control lift `+0.833`, parse `1.000`, and zero infrastructure
failure. This proves the gate is attainable but not cross-architecture stable.

The post-hoc failure analysis has report hash
`4ebca915ae674cb084c9e3f4b61bff7e7b4f0a470cc1eb6ce606c455658ee14d`.
Among Gemma's 19 incorrect factual questions, six belonged to two complete
Stage-1 call failures (one 16,384-token truncation and one duplicate-query-ID
schema failure), seven lost later registered regions, two omitted or misread a
required fact, and four failed after complete supporting facts reached Stage 2.
Three of the four direct-edge questions had the correct typed edges in Stage 1
but failed target-relative neighbor selection in Stage 2. Lowering parse from
0.95 to 0.90 would not change the Level-1, Level-2 or topology-family failures.

**Alternatives rejected.** Relaxing thresholds after seeing the result would
be outcome-selected. Switching the primary model to Qwen would violate the
frozen architecture role. Running only Qwen's 90-case factorial would provide
neither the planned Gemma-primary result nor cross-architecture evidence.
Another prompt/ledger iteration on the same cases would tune to exposed errors.

**Consequences.** The two proposed large RQ1 experiments remain intentionally
unexecuted because their prerequisite failed; this is a protocol outcome, not
unfinished inference. Any future attempt must begin from a new mechanistic
hypothesis and fresh outcome-unseen exposed data. A direct single-stage solver
or a deterministic, task-scoped extraction interface may be planned as a new
version, but it cannot inherit promotion from Qwen's result or reuse these 12
cases for selection. RQ2 may be planned as dashboard-design research, but it
must not be justified as an efficacy continuation of a mechanism that failed
the primary gate.

### DD-51 — Close RQ1 under its sequential stopping rules and begin RQ2a static implementation

**Date:** 2026-08-05
**Status:** Superseded by DD-53 for every model-inference conclusion; its
static implementation history remains auditable and RQ2 inference remains
locked

**Context.** RQ1 now has two independent negative decision paths. The disjoint
Legacy RCA-VisOps gate found text to be the best fixed arm for both models and
found no beneficial frozen routing effect. The newer cross-region/four-region
route passed infrastructure smoke but failed its primary perception
prerequisite after multiple exposed-only mechanism interventions. The last
typed gate produced a Qwen-specific pass but a Gemma-primary failure.

**Decision.** Treat RQ1 as completed under the registered sequential decision
tree, with the main efficacy claim unsupported. The blocked 90-case factorial,
independent transfer and heldout branches are not missing experiments: their
prerequisite failure is the registered terminal outcome. Keep `RQs/RQ1/src/`
frozen because no submission-ready RQ1 implementation was approved. Begin the
next roadmap question only through the already registered RQ2a static
implementation and qualification scope. Do not authorize RQ2 model inference,
RQ2b, RQ2c, training or downstream efficacy claims in this decision.

**Evidence.** The RQ1 synthesis is
`RQs/RQ1/findings/rq1_final_synthesis_2026-08-05.md`. The Legacy independent
gate file SHA-256 is
`4a8ba8d40af584ac2dbb60d7ed17846ed64a2c935d20d18083b6dba6764a7552`.
Gemma routed-minus-T was `-0.0118` (`p=0.0104`) and structural routed-minus-T
was `-0.0562` (`p=0.0112`); Qwen's corresponding effects were `-0.0046`
(`p=0.3622`) and `-0.0227` (`p=0.3698`). RQ1b9's authoritative verification
hash is `44e63019ef925f45e494d2eb606d72d2e629b737c1fa8356380c83b2ed350794`:
Qwen passed every perception criterion, while Gemma failed Level 1, Level 2,
direct-edge, metric-to-topology and parse requirements.

**Alternatives rejected.** Running the factorial despite the gate would break
the preregistration. Declaring RQ1 generally positive from Qwen alone would
ignore the frozen primary architecture and the independent router failure.
Declaring that images are useless would ignore the large factual-control lifts
and Qwen's complete gate pass. Promoting provisional code into `src/` would
mistake mechanism exploration for a settled method.

**Consequences.** RQ1's defensible conclusion is architecture-specific visual
usability without stable cross-architecture performance benefit. RQ2 must ask
the narrower causal design question—how encoding and arrangement affect
answer-hidden evidence operations—and must state explicitly that a positive
design effect is not yet a text-baseline or RCA-efficacy win. RQ2a static work
may freeze rosters, facts, renderer cells, answer separation, parity, leakage,
analysis and smoke contracts. A later explicit decision is still required
before any RQ2 model request.

### DD-52 — Reassign two unopened RQ1 gate rosters to preserve the RQ2 sample design

**Date:** 2026-08-05
**Status:** Accepted for RQ2a static implementation; inference remains locked
**Supersedes:** Only the data-source clause in RQ2 master protocol v1 that
required the independent and downstream pools to lie outside every historical
RQ1 roster

**Context.** The RQ2 v1 static check assumed at least 80 eligible exposed cases
per dataset remained outside every RQ1 private roster: 50 for the independent
gate and 30 for a downstream lock. After the later RQ1b6–b9 roster freezes,
the actual outside-roster counts are only AegisLab 20, AIOPS-2022 41 and
AIOPS-2025 35. Shrinking the 150-case gate would materially weaken its planned
MDE and asymmetric per-dataset capacity would break the balanced design.

**Decision.** Preserve the 60-case RQ2 development screen on already executed
exposed RQ1 incidents. Reassign the unopened, disjoint
`rq1b2_gate_private_v1.json` roster—exactly 50 cases per primary dataset—as the
source of the 150-case RQ2a independent gate. Reassign the separate unopened
`rq1b3_gate_private_v1.json` roster as the downstream-lock source, selecting
30 of its 50 cases per dataset by the frozen RQ2 hash and retaining the other
20 per dataset as an unopened buffer. Create new RQ2-owned rosters with hashes
and lineage; do not edit or execute the historical RQ1 roster files. This
permanently retires those rosters from their old RQ1 gate roles and does not
reopen RQ1.

**Evidence.** The exposure ledger contains 318/340/333 eligible exposed cases
for AegisLab/AIOPS-2022/AIOPS-2025. The union of all current RQ1 private rosters
leaves only 20/41/35 outside it. Each reassigned gate roster contains 150 unique
cases, 50 per dataset; every one of its cases is absent from every other RQ1
private roster. Neither roster has any opaque incident directory anywhere
under `RQs/RQ1/results/`, and RQ1 has no corresponding gate result directory:
only its development and smoke predecessors exist. Thus no model outcome,
render or trajectory was observed for either pool.

**Alternatives rejected.** Lowering the gate to 20 cases per dataset would
raise the approximate paired MDE and remove the planned 90-case downstream
lock. Opening reserve, heldout or RE2-TT would violate partition rules. Treating
prior RQ1 execution as automatically disqualifying would discard two perfectly
unopened exposed pools for historical names rather than scientific exposure.

**Consequences.** RQ2 must version the data contract and make the reassignment
explicit in its protocol, config, static checker and generated roster lineage.
The 60/150/90 sample sizes, model roles, statistical thresholds and all
information/leakage rules remain unchanged. The reassigned independent and
downstream cases may not be inspected for RQ2 model outcomes before their
registered stage. This decision authorizes only static roster construction and
qualification; a later decision is still required before model inference.

**Static completion.** The v2 roster generator and its drift-check mode passed
the 10-test RQ2 static suite and lint. The frozen manifest is
`RQs/RQ2/configs/rosters/rq2a_roster_bundle_v2.json`, with canonical bundle
hash `c304f3c0831b5b47c9ee4c10527760206b6a362626c0c0ab02ab762fc9eb1bc4`
and file SHA-256
`b27b87c68b466d160aa2e735d244cffbe1f294d02608bd1047064561e17b0711`.
It freezes 60 development, 150 independent-gate, 90 downstream-lock and 60
buffer cases; all four private sets are pairwise disjoint. The generated
contract remains `frozen_static_inference_locked` and does not authorize a
model call.

### DD-53 — Replace the local Qwen/Gemma inference recipe and invalidate protocol-v1 model results

**Date:** 2026-08-05
**Status:** Accepted; static migration complete, all successor model execution
locked pending requalification
**Supersedes:** The vLLM-inference-v1 runtime in all earlier decisions and the
model-outcome-dependent conclusions or promotions in DD-25 through DD-51. It
does not invalidate CPU-only renderer qualifications, static rosters,
partition assignments, checkpoint bytes, external-API experiments, or the
data-reallocation facts in DD-52.

**Context.** The user selected a new canonical decoding and multimodal serving
recipe after the Gemma failure analysis: `temperature=1.0`, `top_p=0.95`,
Gemma `max_soft_tokens=1120`, Qwen `min_pixels=65536` and
`max_pixels=2580480`, Gemma xgrammar with
`disable_any_whitespace=true`, and chunked prefill enabled for Gemma. These are
substantive runtime changes, not a relocation-only migration. The old local
results therefore cannot be relabeled as if they used the new configuration.

**Decision.** Adopt `vllm-inference-v2` as the sole configuration for new
project-local Qwen3.6-27B and Gemma-4-26B-A4B-it calls. Keep both models
unquantized BF16 with the existing 32,768 context, 16,384 output ceiling, seed
42, thinking disabled, and `gpu_memory_utilization=0.65`. Freeze separate
model-specific server contracts:

- Qwen uses `min_pixels=65536`, `max_pixels=2580480`, batch-invariant off, and
  chunked prefill off.
- Gemma uses `max_soft_tokens=1120`, batch-invariant on, chunked prefill on,
  and xgrammar with arbitrary JSON whitespace disabled.

The Qwen pixel cap equals the source-pixel coverage associated with Gemma's
1,120-soft-token budget (`1120 × 3² × 16² = 2,580,480`). This freezes matched
source-pixel coverage; it does not assert equal architecture-specific image
token counts, so actual image tokens remain a required per-call measurement.
Because temperature 1.0 enables sampling, exact output repetition is not a
validity gate; paired arms must instead share the registered sampling and
replicate policy.

Archive every prior local Qwen/Gemma result made under inference-v1 in place,
without deleting, moving, or rewriting raw trajectories, logs, contracts,
hashes, or analyses. The authoritative inventory contains 30 current RQ0/RQ1
result roots and 46 legacy local-vLLM roots. They are invalid for scientific,
qualification, routing, promotion, or efficacy claims and may not be resumed.
External Claude/API runs and CPU/static artifacts are outside this
runtime-specific invalidation. RQ0 and RQ1 are reopened; their former empirical
endpoints are withdrawn. RQ2 had no model calls, so only its old static runtime
contract is superseded.

**Implementation evidence.** The pinned local environment is vLLM 0.24.0,
xgrammar 0.2.3, Transformers 5.14.1, and PyTorch 2.11.0. The requested flags
parse in that environment. Gemma's supported soft-token budgets include 1,120,
and the explicit xgrammar backend is required for the whitespace restriction.
vLLM accepts the selected Qwen chunked-prefill setting but emits an upstream
GDN warning that disabling it may crash or produce incorrect output. The
setting remains user-selected and frozen, but this warning makes a new live
attestation and Rule-16 smoke mandatory before Qwen inference; it must not be
silenced by changing the flag without another versioned decision.

The canonical configuration SHA-256 is
`0e8c51ed8e8723665da59151432675b755ed2183b5522acf1d61d09fcd4488a9`.
The generated static lock file SHA-256 is
`3c536f4d98c5582037321e6e7b4bfdf6b0da12c6d5e17a661e8dc8b0a5097f44`
and its canonical content hash is
`861b44779af8fe6db7f2cd96556995c3ef9f079d71cf702d3de2fda480957695`.
The migration registry SHA-256 is
`85d9a5c43493b5d608248964a229f860468a747c9e2ebce8071524460fc7fb3e`.
The RQ0 and RQ1 successor-protocol hashes are respectively
`de9413712790d02d9a6c9487bbb58d626dd6fca019e8eaa67c81eb8cbece3aa3`
and
`9737262c64502dc1b6b055a29a44d4e81e77939701ddfee9e0ff203802d16abb`.
The RQ0, RQ1, and legacy archive-manifest hashes are respectively
`9db3bfb62ddcc59a903674be65a098817ae471f8e2475ad386463e7812fe6cae`,
`70ebbfbbfcb585f631942ac37544f6d6336ef5076bbdbfb09d4824b829c2236e`,
and
`3abb9080697c7b5dfd66ad79248fe5d82345d64394990a19be76af72790b0fd0`.

RQ2 was regenerated as static contract V3 without model calls. Its config,
roster-bundle file, and qualification hashes are respectively
`6209efac67024560a2f12281bd5062903466de2cc01412d02cd5b4360b24a380`,
`38d1c2450f205015ab25a00bd95dfa45e4126d6dfd775327927e199ca725082a`,
and
`01be52f1aa3ca5c0d387aade2dc1c0bd942de0ca8b836bbf5406b801d3ac3719`.

The static lock also covers the RQ0 adapter launcher and the legacy SLURM
entry point. The latter is deliberately a fail-closed, non-authoritative stub;
the former still requires a separately enabled experiment-bound adapter
contract and live attestation before use.

**Consequences.** Old server attestations, token-budget reports, runtime
freezes, smokes, gates, and run contracts remain immutable evidence of what was
actually run, but none can authorize or qualify a v2 experiment. Successor
protocols are explicitly unfrozen and `execution_authorized=false`. Before any
new model call, create a new experiment ID/result root, regenerate the
model-specific live server attestation and image-token/context preflight,
freeze a new experiment-bound runtime contract/hash, and pass a new
partition-aware Rule-16 smoke. Partial old outcomes may not choose rerun order,
prompts, cases, or settings.

**Revisit condition.** A runtime value may change only through another
versioned decision that identifies affected experiments and creates new
contracts/hashes. Historical inference-v1 results remain archived invalid even
if a future recipe resembles their old settings.

**Post-decision lightweight smoke.** A two-call runtime diagnostic subsequently
confirmed that both model-specific launchers start and accept one real-image
strict-JSON request. Gemma completed with effective `max_soft_tokens=1120`,
chunked prefill on, and the registered xgrammar whitespace restriction; Qwen
completed with the registered pixel limits and chunked prefill off. Both calls
returned HTTP 200 with finish reason `stop`, and both services were then
stopped. This diagnostic is recorded under
`RQs/RQ1/results/rq1_vllm_inference_v2_runtime_smoke_v1/`. It is not the
partition-aware three-case Rule-16 smoke and therefore does not change
`execution_authorized=false` or unlock any full experiment.

### DD-54 — Increase canonical vLLM scheduling capacity to 64 sequences

**Date:** 2026-08-05
**Status:** Adopted; operational amendment to DD-53

**Context.** The DD-53 runtime used `max_num_seqs=8`. The user observed that
experiments were slower than expected and the GPU was frequently underfilled,
and reported prior successful use of 64 with these models in another project.
This field limits vLLM's concurrent sequence scheduling capacity.

**Decision.** Change only `max_num_seqs` from 8 to 64 for both Qwen3.6-27B and
Gemma-4-26B-A4B-it. Keep every other DD-53 runtime field unchanged, including
temperature, top-p, image budgets, chunked-prefill choices, BF16 precision,
context/output limits, thinking state, structured-output policy and GPU-memory
utilization. `Codex.md` was updated before the implementation, followed by the
unified config, canonical launcher, RQ0 adapter launcher, runtime validator,
RQ1 runtime expectations and generated hash lock. Historical experiment
configs and run contracts remain immutable.

**Evidence.** The new unified-config SHA-256 is
`0c868ef495782d00207f5b0d206558f3f6d19c6cd75e79d11e425398b20637c2`.
The generated lock file SHA-256 is
`893eaf47f0d3ae32a24a1e6478208c7c5e649dc947021732c2d7ba90558648c6`,
with canonical content hash
`a43b388ce95f85e7276c2f3307e5359b1270119a890477a5530f328309d65d3d`.
The migration-registry SHA-256 is
`5cc5ea9346881a0baca08ad9e2cbe35d68b294b67dbf9c1792421bcbfb35b77f`.
The administratively rebound RQ2 static-report SHA-256 is
`a0f8bc740963baef6e0f0e38debbbf8179493ef334e7bf1f61cbd865f4db6d51`.
The user explicitly waived static checks and smoke for this one-field capacity
amendment; none were run. The previous lightweight two-call diagnostic used 8
and remains historical diagnostic evidence rather than an attestation of 64.

**Alternatives rejected.** Keeping 8 was rejected because it unnecessarily
constrained batching and left the GPU underutilized. Changing additional
runtime fields was rejected because the request was limited to this single
capacity parameter.

**Consequences.** No scientific result had been generated under the
intermediate inference-v2 capacity setting, so the DD-53 invalidation manifests
and the reopened status of RQ0/RQ1 are unchanged. Future runs must record 64 in
their effective configuration. This waiver avoids an immediate standalone
check or smoke solely for the capacity change; it does not remove the ordinary
Rule-16 qualification required before a future full experiment.

### DD-55 — Authorize the inference-v2 RQ0-to-RQ1 rerun and make RQ1 perception non-stopping

**Date:** 2026-08-05
**Status:** Accepted and executing
**Supersedes:** The execution locks in the RQ0/RQ1 inference-v2 migration
interlocks and only the stop-after-perception ordering clause of
`RQs/RQ1/descriptions/rq1b6_b7_execution_protocol_v1.md`. It does not change
the registered perception thresholds, information-equality contract, RQ1
hypotheses, scoring, rosters, or the invalid status of inference-v1 results.

**Context.** DD-53 invalidated all local Qwen/Gemma model outcomes generated
under inference-v1 and reopened RQ0/RQ1. DD-54 then raised the canonical
scheduling capacity to 64 without changing the scientific request contract.
The user has now explicitly authorized a continuous rerun from RQ0 through
the end of RQ1 using inference-v2, including both RQ1b6 cross-region reasoning
and RQ1b7 four-region factorial experiments, regardless of whether the
diagnostic perception gate meets its promotion thresholds.

**Decision.** Execute only versioned successor result roots. RQ0 reruns its
registered 720-case, three-arm paired experiment for Qwen3.6-27B followed by
Gemma-4-26B-A4B-it after a model-specific live attestation, 720-case token
preflight and partition-aware Rule-16 smoke. The old RQ0 roster is now exposed;
therefore this rerun is a valid repeated-roster comparison under the new
runtime but not a fresh untouched confirmation.

For RQ1, run a new two-model Rule-16 smoke, then the complete 12-case
actual/swapped/neutral perception experiment, the 90-case development utility
map, and the disjoint 90-case independent gate. The perception thresholds and
result interpretation remain exactly registered, but their result is
diagnostic and non-stopping: failure must be reported and cannot be hidden,
yet it cannot prevent execution of RQ1b6/RQ1b7. The 17-cell full runs jointly
answer the reasoning-level question and estimate the M/L/R/G visual main
effects; they are not two selectively launched protocols. Both models must
complete every registered stage. No heldout, reserve, RE2-TT, training, SFT,
LoRA, or GRPO is authorized.

**Operational implementation.** Use the canonical unquantized BF16
inference-v2 contract with `max_num_seqs=64`. Multiple resumable case shards
may feed the one frozen server concurrently so that the scheduling capacity is
actually used. Sharding is operational only: every call remains bound to the
same roster, prompt, facts, model runtime, response schema and scorer, and the
post-hoc verifier requires complete unique pairing before analysis. Whole-case
infrastructure exclusions retain the project-wide 5% maximum. Partial results
may be monitored but cannot choose prompts, cases, thresholds, model order or
whether the second model runs.

**Evidence at authorization.** The inference-v2 config SHA-256 is
`0c868ef495782d00207f5b0d206558f3f6d19c6cd75e79d11e425398b20637c2`.
After adding the shared live-server attester, the static lock file SHA-256 is
`9781816f31552f8b5791c546f43640c3985942ef825a26736b73ca4feac64e14`
and its content hash is
`9be87f5009c2839722968db87567efd9f728ea954555b257da3839326918e55a`.
RQ0's 720-case static qualification, representation transport audit and
artifact inventory passed with 720/720 cases, zero failures and 2,880 frozen
case artifacts. Qwen's live attestation recorded `max_num_seqs=64`, the
registered pixel budget and chunked-prefill off; its token preflight passed all
2,160 prompts with maximum input counts 15,741/14,171/14,798 for A/B/C, and
its Rule-16 smoke passed all 9 calls with zero infrastructure failures.

**Consequences.** A negative perception result remains important evidence
that visual reading is weak and constrains causal interpretation, but it no
longer censors the factorial outcome. A positive factorial or H-versus-T result
must still be interpreted together with perception and information-parity
evidence. Conversely, a failed perception gate cannot be silently renamed a
pass merely because a downstream accuracy contrast is positive. Final
conclusions and next-step decisions must be recorded after both models and the
independent gate complete.

### DD-56 — Make cross-region task eligibility template-local

**Date:** 2026-08-05
**Status:** Accepted; implementation correction before any RQ1 inference-v2
model call

**Context.** During preparation of the inference-v2 90-case development
roster, case `INC-1CE353424263` stopped at packet compilation. The compiler
eagerly required a display-unique metric anchor before it knew which template
was being tested. Consequently, a valid topology-only Level-1 task, trace to
topology Level-2 task, or log to trace to topology Level-3 task could be
rejected merely because the metric region contained displayed-value ties. Two
Level-3 fallbacks also described an anchor as unique without verifying that it
was unique at displayed precision.

**Decision.** Eligibility is evaluated separately for each registered
template. A template may require only the regions and dependency anchors that
it actually reads. Every first-step anchor must be unique at model-visible
precision; `M→G→L` specifically requires a unique metric anchor for the
protected caller, and `M/L→R→G` requires a unique first-region anchor whose
trace association resolves to exactly one supplied edge. No answer, label,
fault type, model output or RCA correctness is used by this correction.

The partially prepared development and independent input trees were preserved
with the suffix `inputs.superseded-eager-anchor-20260805`; they are not
executable artifacts. The earlier smoke and perception runtime freezes were
likewise preserved with a superseded suffix. All executable RQ1 stages must be
prepared or re-frozen against the corrected implementation before their first
model call.

**Evidence.** The corrected compiler passes the complete RQ1/project static
test command. A new regression fixture proves that G-only, R→G and L→R→G
tasks remain eligible when every displayed metric value ties, while M→G→L
correctly fails without a unique metric anchor. The real case that exposed the
defect now compiles label-blind tasks `L_direct_bin`, `L_G_link` and
`L_R_G_chain`.

The subsequent complete scan found one genuinely ineligible case in the
independent roster. The DD-56 outcome-blind repair preserved every eligible
v1 row and replaced only that case with the first eligible otherwise-unused
case in the original role/dataset hash order. The v2 assignment hash is
`99e13fc85f2d9e9be1046a68961240a1d3f3288f250ae74c1a2a539031ef31d2`
and the private audit hash is
`11df80ad21d0a82557356824e345c85efc7b8b2c2b52a7ddead5405f5c9ead93`.
Both 90-case inputs then passed exact information parity, strict A+B,
answer-material isolation, leakage, clipping, schema and repeat-compilation
qualification. Smoke and perception artifacts were requalified unchanged.
The successor runtime-freeze hashes are `b68ead4f…80354` (smoke),
`ded90369…08050` (perception), `1c6e66d1…5e7aa` (development) and
`5d6aba01…f923e` (independent).

**Consequences.** This repair changes no RQ1 hypothesis, representation cell,
fact inventory, response schema, model configuration, roster count or
threshold. It prevents false case ineligibility and false uniqueness claims.
RQ0 is unaffected. If a case still has no eligible template at a required
reasoning level after this correction, it must fail closed and may only be
replaced through a separately frozen, label-blind eligibility-aware roster;
the compiler must never fabricate uniqueness.

### DD-57 — Retain the negative RQ0 inference-v2 result and proceed to decomposed RQ1

**Date:** 2026-08-05
**Status:** Accepted; RQ0 inference-v2 complete

**Context.** DD-55 authorized a full repeated-roster RQ0 rerun after the
inference-v2 migration. Qwen3.6-27B and Gemma-4-26B-A4B-it each completed all
720 cases and all three equal-information arms. The rerun had zero
infrastructure exclusions and zero truncations; Qwen had five model parse
failures and Gemma had none. All registered static, leakage, token, smoke,
pairing, and artifact checks passed.

**Decision.** RQ0 remains not supported. For Qwen, macro-dataset MRR was
0.3848/0.4083/0.3772 for visual-text/text-only/flat structured, giving A−B
−0.0236 (Holm p=0.0897) and A−C +0.0076 (Holm p=0.5136). For Gemma the
corresponding MRR was 0.3677/0.3933/0.3652, giving A−B −0.0256 (Holm
p=0.0102) and A−C +0.0025 (Holm p=0.8634). Neither model met the registered
`+0.05` practical-effect threshold against either baseline. The current RQ0
dashboard must not be described as improving RCA.

Proceed with the already registered RQ1b6/b7 execution. This is not a rescue
reinterpretation of RQ0: RQ1 asks the narrower mechanistic questions of which
M/L/R/G encodings help and whether visual effects grow with cross-region
reasoning depth. Its perception result remains mandatory to report but
non-stopping under DD-55.

**Evidence and validity.** The merged Qwen and Gemma trajectory hashes are
`2f6ab904b24bc5d2cb889dff351156b9ef13554295fd1d2b11a73012b6e3889c`
and `2c7613265f1b58c57941a5658482e3e31e67d50bb187c9cae7a8832e58692ff7`.
Because the 720-case roster was previously exposed, the outcome is valid as a
new-runtime repeated-roster comparison but is not an untouched confirmation.
An analysis-only stale renderer check was also repaired: the analyzer now
compares every trajectory's renderer identity to the corresponding frozen CEB
instead of requiring historical renderer v6. The repair changed no model
artifact or numerical result.

**Consequences.** RQ0 is closed for this inference-v2 rerun. No further RQ0
prompt, renderer, or model tuning is selected from these outcomes. Any future
claim that vision improves RCA must rest on a separately registered successor
experiment and cannot erase or relabel this negative result.

### DD-58 — Close RQ1 inference-v2 with Gemma-specific complementarity and proceed to RQ2

**Date:** 2026-08-06
**Status:** Accepted; RQ1 inference-v2 execution complete

**Context.** DD-55 authorized the complete RQ1b6 reasoning ladder and RQ1b7
M/L/R/G factorial regardless of the perception result, while retaining all
registered thresholds and interpretations. Both models completed the 12-case
perception experiment, 90-case development map, disjoint 90-case independent
gate, and registered 30-case renderer-v12-layout T/V/H transfer under the
canonical inference-v2 runtime. Static information equality, leakage,
pairing, hash, writer and verification checks passed.

**Decision.** Close the registered RQ1 inference-v2 execution without claiming
a universal visual advantage. In the 90-case independent gate, Gemma passed
P1: H minus T on Level 2+3 complete-chain accuracy was `+0.1111`
(`p=0.00473`, paired `d_z=0.318`). The 30-case full-dashboard transfer repeated
the direction and practical magnitude (`+0.1500`, `p=0.04166`). However,
Gemma failed the depth-interaction P2 and every positive M/L/R/G visual-main-
effect test. Qwen failed P1 and P2 in both runs; its independent and transfer
parse rates also fell below 0.95. Both models failed the preregistered
perception gate, although factual images outperformed swapped/neutral controls.

The accepted result is therefore Gemma-specific multimodal complementarity:
redundantly adding an image to byte-identical text can improve cross-region
question answering for Gemma. It is not evidence that all-visual input beats
text, that gain grows with reasoning depth, that one visual region is
individually beneficial, that the result generalizes to Qwen, or that RQ0's
negative RCA MRR conclusion has changed.

**Evidence.** The independent analysis authority is
`RQs/RQ1/results/rq1b6_b7_cross_region_independent_gate_v2/analysis/cross_region_analysis.json`;
its integrity verification hash is
`1214b9686b296aded0363ebf3f45d37dc4049a1515821be0edd4ffb7fbe52225`.
The transfer analysis authority is
`RQs/RQ1/results/rq1b6_b7_full_dashboard_transfer_v2/analysis/full_dashboard_transfer_analysis.json`;
the transfer integrity verification hash is
`74984b6b97268115c8915f4580a748cd5e7ff9585b06221ff34c411e58c2e7bf`.
Both transfer models completed all 90 calls with zero infrastructure
exclusions. The current full finding is
`RQs/RQ1/findings/rq1_inference_v2_cross_region_and_transfer_finding_2026-08-06.md`.

**Alternatives rejected.** Promoting Gemma's P1 into a cross-architecture RQ1
claim was rejected because Qwen did not reproduce it and failed the parse
gate. Treating V as the preferred representation was rejected because V was
usually worse than T and sharply worse at difficult levels. Continuing to
tune RQ1 on its independent/transfer outcomes was rejected because those sets
are now exposed and such tuning would contaminate a successor confirmation.

**Consequences.** Keep `RQs/RQ1/src/` frozen; the current solution is not a
settled submission implementation. Proceed to RQ2 dashboard-design effects,
targeting the observed perception weakness, harmful G/L/R visual effects and
Qwen output instability while preserving equal information. RQ2 may use RQ1
as prior evidence but must use newly registered development and confirmation
artifacts and must not rewrite RQ0 or RQ1 conclusions.

### DD-59 — Remove the Qwen project pixel cap and rerun RQ1 with the copied legacy typed two-stage logic

**Date:** 2026-08-06
**Status:** Accepted; implementation and successor qualification in progress
**Supersedes:** DD-58 only as the current RQ1 endpoint and next-action decision,
and the Qwen equal-source-pixel-cap clause of DD-53. It does not reclassify or
rerun RQ0, alter RQ0's negative result, or modify any archived raw artifact.

**Context.** The completed RQ1 inference-v2 sequence used the single-call
cross-region answer path, whereas the last user-selected legacy mechanism was
RQ1b9's typed two-stage `Observe/Connect -> Answer` path. The user authorized
the vLLM and renderer changes but did not authorize replacing that experiment
logic. The user also directed CanvasRCA to stop imposing Qwen
`min_pixels/max_pixels`, so Qwen may use its native image processor rather than
the project-level `65536/2580480` override.

**Decision.** Future Qwen runs pass no `--mm-processor-kwargs`; Gemma remains at
its supported `max_soft_tokens=1120`. Native processor, context and hardware
limits still apply, and every call records actual image tokens. Preserve the
completed RQ1 inference-v2 roots in place but archive their current-evidence
role through
`RQs/RQ1/results/_archive_inference_v2_single_stage_20260806/manifest.json`.
RQ0 is explicitly excluded and remains valid under its own frozen capped-Qwen
contract.

Create a forward-versioned RQ1 successor by mechanically copying the RQ1b9
typed two-stage implementation rather than editing the original. Its
one-time implementation-migration audit permits only: (1) the user-approved
current dashboard revision, and (2) the current user-approved vLLM runtime.
Existing legacy behavior, questions, typed handoff, scoring, thresholds and
information contract remain unchanged. Operational sharding/resume may be
added only when it provably leaves the model-visible prompt, stages, schemas
and scores unchanged. This allowlist is a developer-side code-review check,
not an experiment gate or runtime contract. After it passes, remove the
temporary checker and retain only its read-only audit report; formal configs,
runners and result acceptance must not depend on it.

**Evidence.** The archived sequence included the two-model Rule-16 smoke,
12-case perception gate, 90-case development map, disjoint 90-case gate and
30-case transfer recorded by DD-58. Their nine retained roots contain 31,244
files and approximately 1.81 GB; per-root immutable tree hashes are recorded in
the archive manifest. The new unified runtime config SHA-256 after removing the
Qwen override is
`b8e0a9db71bbf2be7ee644da5ccb6340086dd75c83d78afeeb69c54d1990d4a1`.
The initially generated lock will be rebound after the copied-code and archive
hash chains are final; no long-run contract may freeze against an intermediate
lock.

**Alternatives rejected.** Reusing the single-stage RQ1-v2 results as the final
endpoint was rejected because it does not implement the intended legacy agent
logic. Editing the old RQ1b9 files in place was rejected because it would erase
provenance and make the old result unauditable. Retrospectively assigning the
uncapped Qwen runtime to RQ0 was rejected because it would rewrite a substantive
model-input contract rather than preserve history.

**Consequences.** RQ1 is reopened. The archived RQ1-v2 numbers may be described
only under their original contract and may not select or validate the new
successor. Because the development, independent and transfer rosters have been
seen, their successor reruns are repeated-roster corrected-logic evidence, not
fresh untouched confirmation. New result IDs, copied-code provenance, updated
hashes, live attestations and Rule-16 smoke are mandatory before long runs.
`RQs/RQ1/src/` remains frozen and RQ2 efficacy inference remains paused until
this RQ1 correction is resolved.

### DD-60 — Cap aggregate model calls for every smoke and gate

**Date:** 2026-08-06
**Status:** Adopted
**Supersedes:** Every prior smoke or gate call budget that exceeds the limits
below, including the 204-call RQ1 successor smoke and 144-call RQ1 perception
gate inherited under DD-59. DD-59 otherwise remains in force.

**Context.** The copied RQ1 typed two-stage successor mechanically inherited a
17-condition Rule-16 smoke. Across three cases, two stages and two models this
expanded into 204 model calls. It then inherited a 12-case, three-control,
two-stage, two-model perception gate requiring another 144 calls. These
diagnostic workloads consumed hours that should have been reserved for the
actual experiment. They exceeded the user's instruction that smoke should only
establish that the code and end-to-end path work.

**Decision.** Retain smoke tests and experimental gates, but impose absolute
aggregate budgets. One complete logical smoke may initiate at most 18 LLM/VLM
calls. One complete logical gate may initiate at most 36 LLM/VLM calls. Each cap
applies across all models, cases, stages, arms, conditions, processes and
retries; infrastructure-failed initiated requests also count. No protocol may
evade a cap by splitting, renaming, chaining or repeating one logical smoke or
gate. An inherited plan, config or contract above the applicable cap is
non-executable and must be redesigned before any model call.

**Evidence.** `rq1b9_legacy_typed_smoke_v3` completed 204 calls and therefore
demonstrated the cost failure directly, even though its post-hoc integrity
qualification passed. The subsequent
`rq1b9_legacy_typed_perception_v3` completed Gemma's 72 calls and only part of
Qwen's planned 72 calls before it was stopped. These artifacts retain only
their already established diagnostic or incomplete scope; this decision does
not turn them into efficacy evidence and does not retroactively alter any
headline RQ result.

**Alternatives rejected.** Keeping the full factorial inside smoke was rejected
because it duplicates the experiment instead of cheaply qualifying the path.
Treating a per-model call allowance as the cap was rejected because adding
models would silently multiply diagnostic cost. Removing gates entirely was
rejected because small targeted gates still provide useful infrastructure and
mechanism checks.

**Consequences.** The stopped 144-call RQ1 perception contract must not be
resumed as the active gate. Before further model execution, RQ1 must register a
replacement smoke/gate design that fits the 18/36 aggregate limits while
preserving the relevant compiler, renderer, client, writer, evaluator and
verification paths. Existing results retain their prior validity and scope;
only future execution authority and budgets change.

### DD-61 — Bound smoke and gate wall-clock execution

**Date:** 2026-08-06
**Status:** Adopted
**Supersedes:** DD-60 and prior protocols only where they require a smoke or
gate to wait for all planned units. DD-60's 18-call smoke cap and 36-call gate
cap remain unchanged.

**Context.** Call-count caps prevent diagnostic protocols from expanding across
cases, conditions and models, but a small number of requests can still consume
hours when a VLM produces a long output. A smoke or gate must therefore be
bounded in both request count and elapsed execution time.

**Decision.** One experiment's complete logical smoke has a 600-second
aggregate wall-clock limit measured from the start of its supervisor, including
preflight, requests, retries, persistence and verification. It exits
immediately if completed earlier. At timeout, outstanding work is terminated
and completed artifacts are preserved. If the timeout is the only error, the
smoke passes; any other error still prevents passage.

One complete logical gate has a 1200-second aggregate wall-clock limit, also
measured from the start of its supervisor and exited immediately when completed
earlier. At timeout, no remaining gate units are launched. Gate metrics and
registered thresholds are computed using all and only cases whose complete
required arm/condition/stage set finished before timeout. A partial case is not
scored as complete, and the registered timeout is not an infrastructure or
model error.

**Evidence.** The RQ1 copied typed two-stage smoke and perception sequence
showed that individual Qwen Stage-1 calls can run for many minutes even after
call budgets are reduced. An explicit wall-clock limit is therefore necessary
to make diagnostic cost predictable. This is an operational policy decision;
the interrupted perception artifacts remain incomplete diagnostic evidence and
are not converted into an efficacy result.

**Alternatives rejected.** A per-call timeout alone was rejected because many
individually legal calls can still make a smoke or gate too long. Waiting for
every registered diagnostic unit was rejected because completion of the
diagnostic workload is not more important than beginning the actual experiment.
Treating the registered timeout as a smoke failure was rejected because the
timeout is the mechanism that enforces the intended bounded qualification.

**Consequences.** Future smoke and gate supervisors must enforce both the DD-60
call caps and the DD-61 aggregate wall-clock limits. Existing configs or
contracts that assume full diagnostic completion beyond these limits are
non-executable until redesigned. These timeouts do not shorten or censor formal
experiment calls; they apply only to smoke and gate execution.

### DD-62 — Use simple diagnostic timing and require post-smoke artifact review

**Date:** 2026-08-06
**Status:** Adopted
**Amends:** DD-61 implementation details without changing its 600/1200-second
limits; adds the hidden-issue handling workflow to Rule-16 qualification.

**Context.** The diagnostic bounds prevent smoke and gate workloads from
consuming experimental time; they do not require precise clock
synchronization. A smoke can also look healthy in a brief log while a persisted
conversation, raw response, prompt or accounting record reveals a hidden bug.

**Decision.** Enforce the bounds with ordinary process wall-clock or monotonic
time and at most a small run-local state/supervisor. Second-level precision is
sufficient. Do not modify WSL, the host clock, kernel or services and do not add
distributed/high-precision timing infrastructure. After every smoke attempt,
the acting agent must inspect the persisted summary/verifier output and every
completed trajectory and conversation, not only the operational log, and must
record the review under that smoke root.

Every hidden issue is recorded. A safely repairable issue triggers a
forward-versioned fix, affected contract/hash refresh and verification, after
which work continues. The agent stops only when the issue is material and
remains unsolved after reasonable in-scope diagnosis and repair; the blocker,
evidence and affected scope must then be recorded.

**Evidence.** The earlier RQ1 diagnostic sequence showed both kinds of failure:
large diagnostic workloads delayed formal work, while important model-output
and handoff defects were visible in detailed trajectories rather than in a
high-level progress line. A simple timer controls cost; complete artifact review
controls hidden correctness risk.

**Consequences.** RQ1's successor smoke/gate implementation must remain small
and locally timed. An automated inventory may support the review but cannot
replace reading the persisted conversations. Fixable findings do not pause
progress merely for confirmation; unresolved material findings do.

### DD-63 — Do not rerun RQ1 diagnostics already exercised by the long v3 attempts

**Date:** 2026-08-06
**Status:** Adopted by explicit user direction
**Amends:** DD-60 through DD-62 only for whether a replacement RQ1b9 smoke or
perception gate must now be executed. Their limits still govern every future
smoke/gate that is actually launched.

**Context.** The v3 RQ1b9 smoke and perception attempts already spent many
hours exercising the compiler, renderer, typed two-stage client, persistence
and diagnostic paths. The new caps were introduced to prevent repeating that
cost, not to demand another diagnostic rerun merely because the policy changed.

**Decision.** Do not rerun a v4 replacement for the corresponding RQ1b9 smoke
or perception gate. Preserve all v3 artifacts and their immediately preceding
status/scope; the policy change neither upgrades nor invalidates them. Make the
bounded v4 config copies the active defaults used by the current copied RQ1
code, while leaving them unscheduled (`new_model_calls_required: false`). Thus
any newly authorized future diagnostic obeys 18/36 calls, 600/1200 seconds and
post-smoke artifact review from its first request, without another immediate
diagnostic run.

**Evidence.** The v3 smoke completed its very large planned diagnostic workload;
the v3 perception attempt completed Gemma and a substantial part of Qwen before
being stopped. These runs already exposed the diagnostic code paths and the
cost problem. Repeating them would add no proportional infrastructure evidence.

**Consequences.** No LLM/VLM call, preparation rerun or result reclassification
is required for this policy implementation. Existing formal work may use its
separately registered authority without waiting for a v4 diagnostic. Any later
decision to run a new smoke/gate requires an explicit forward config and remains
subject to the absolute limits.

### DD-64 — Retry transient NVML failures without changing the RQ1 experiment

**Date:** 2026-08-07
**Status:** Adopted; Qwen formal rerun restarting under a model-specific
operational runtime freeze

**Context.** The RQ1b9 typed inference-v2 Qwen development rerun remained
healthy at the canonical vLLM endpoint, but its per-call 50 ms NVML sampler
converted transient WSL/NVML `The operating system has blocked the request`
responses into infrastructure failures. The first terminal-attached attempt was
already invalid after its server lifecycle ended. A subsequent fully detached
four-runner attempt produced 630 completed call records and six NVML failures
affecting five of 90 cases. Its 5.56% affected-case fraction exceeded the frozen
5% whole-case exclusion ceiling, so the attempt was stopped and archived before
analysis.

**Decision.** Preserve every failed attempt and restart Qwen from empty
authoritative shard roots. Amend only `GPUAccounting`: retry transient NVML
query errors at the existing 50 ms sampling interval, allow 30 seconds for the
first valid sample, make a bounded five-second final-sample attempt, record the
number of transient errors, and continue to fail closed if fewer than two
samples exist or the sampler cannot stop. Keep at most four runner processes.
Do not change any prompt, evidence artifact, roster, condition order,
checkpoint/tokenizer, inference-v2 model setting, typed two-stage handoff,
response schema, scoring rule, exclusion threshold or statistical analysis.

Gemma retains its completed old-accounting cells. Before changing the runtime
tree, a dedicated fail-closed verifier sealed all three Gemma cells against the
then-current runtime and raw artifacts. Qwen receives a distinct
`runtime_freeze_qwen_accounting_v2.json`; final joint verification must validate
the sealed Gemma verification and current Qwen runtime separately before
requiring cross-model case identity.

**Evidence.** The invalid detached attempt is recorded at
`RQs/RQ1/results/rq1b9_legacy_typed_development_v3/_invalid_attempt_qwen_nvml_exclusion_ceiling_20260807/attempt_status.json`.
Gemma's sealed verification hashes are
`eaf2adfbd89e76a9cf2dccc8abb110768b3aa540ce87b41ef808df072bf9f583`
(development),
`9d3b60bb05f7eabc04395eb97a1ea414f77cbc16a291cf0236ba62097115769c`
(independent), and
`49254a3440e3ffa139879a5165e59d8aba2f5090ff87d9c69bdbed6e9b7dbffa`
(transfer). The accounting unit/regression suite passed 31 tests. A live
four-process, 15-second probe against the resident Qwen server produced 298
samples per process, zero transient errors and clean reports. The new Qwen
freeze hashes are `f0bc76cc…e2bb04` (development),
`ac16399e…21b5aa` (independent), and `a57a6892…b6767` (transfer).

**Alternatives rejected.** Counting NVML failures as model outcomes was
rejected because no model response or parse failure caused them. Continuing
after five affected cases was rejected by the registered 5% ceiling. Removing
GPU accounting was rejected because token/GPU/cost accounting remains part of
the experiment contract. Reducing concurrency alone was rejected because four
runners already respected the project maximum and still encountered global
transient NVML events. Rerunning Gemma was rejected because its complete cells
had zero infrastructure errors and were sealed under their original runtime
before the operational patch.

**Consequences.** The three archived Qwen attempts remain invalid and cannot be
mixed with the replacement. Qwen restarts all three scopes and records
`gpu_accounting_transient_errors` per successful call. Any call still lacking a
complete accounting report remains an infrastructure failure under the same
paired-case exclusion policy. Final RQ1 claims remain blocked until Qwen's
development, independent and transfer scopes complete and joint verification
and preregistered analysis pass.

### DD-65 — Add an isolated end-to-end RCA representation experiment to RQ1

**Date:** 2026-08-08
**Status:** Adopted for implementation and bounded smoke; long runs disabled
**Amends:** RQ1's mechanism-only VisOps/perception program by adding a distinct
RCA endpoint. It does not supersede or modify any earlier RQ1 artifact or
finding.

**Context.** The current RQ1 VisOps, perception, cross-region, and typed-handoff
experiments diagnose whether models can read and combine dashboard regions.
Their accuracy is question exact match, not RCA AC@K or MRR. Consequently they
cannot establish that a representation improves root-cause ranking. RQ0 also
cannot substitute for the missing RQ1 endpoint because its scope, renderer,
and historical validity limitations differ from the current protocol.

**Decision.** Add `RQ1c — Matched-plan evidence-grounded RCA` as an isolated,
forward-versioned experiment. From one label-blind renderer-v12 evidence packet
it produces five equal-fact arms: text `T`, flat JSONL `F`, image-only `V`,
strict image-first `H=A+B`, and a fixed routed `R` that presents metrics and
topology visually and logs/traces as text. Every arm uses two calls: a typed
Observe/Connect ledger followed by a common text-only Diagnose stage that
returns the frozen top-five RCA JSON. The model never has to preserve query or
fact hashes; a deterministic host binder assigns short observation IDs after
Stage 1. The main comparisons are paired MRR `R-T` and `R-F`, each requiring an
effect of at least `+0.05`, Holm-adjusted `p<0.05`, and no main-dataset reverse
effect of `-0.05` or worse.

Implementation is confined to `RQs/RQ1/scripts/rq1c_rca_v1/` and new RQ1c
configs, schemas, rosters, descriptions, and results. Existing VisOps,
perception, cross-region, typed-handoff, and frozen `RQs/RQ1/src/` content must
remain byte-identical. The development and locked-evaluation rosters contain
90 and 300 disjoint exposed cases respectively, so their future conclusions
are repeated-exposed rather than untouched confirmation. Full execution stays
disabled in this implementation round.

**Evidence and reasons.** True RCA must be judged at the root-cause ranking
endpoint; perception accuracy and ledger integrity only explain mechanisms.
The fixed router tests the observed complementarity hypothesis without giving
any arm extra facts, while `H` distinguishes useful redundancy from selective
routing. Removing opaque identifiers from the model-facing handoff directly
addresses the query-binding attrition seen in RQ1b9 without changing the old
experiment. A 12-call, 600-second Rule-16 smoke covers both models, all three
authorized validation datasets, both stages, and all five arms while remaining
within DD-60 through DD-62.

**Consequences.** RQ1 cannot claim representation value for RCA from VisOps
alone; it needs this distinct endpoint or a later successor. The new experiment
must consume the unified inference-v2 configuration, preserve per-arm atomic
fact equality, and use the granularity-aware scorer after evaluator-private ID
mapping. No model-calling perception gate is added. After static qualification,
the only currently authorized model work is the bounded smoke, and it must wait
until the already-running RQ1 sequence releases the service. Long development
or evaluation inference requires a separate explicit authorization.

### DD-66 — Define RQ1c parity as matched source semantics and require unique grounded handoff

**Date:** 2026-08-08
**Status:** Adopted before any RQ1c model call
**Amends:** DD-65's “equal-fact” wording and its initial Stage-1/runtime
implementation details; the five arms, two-stage compute, hypotheses, rosters,
and RCA endpoint remain unchanged.

**Context.** A CPU-only adversarial review showed that fact-ID location parity
was too weak to establish literal cross-transport information equality. Text
and flat records still contained internal metric sample counts and exact bin
centers that renderer-v12 did not print, while precomputed onset/persistence and
multi-hop paths could become textual reasoning shortcuts. The first binder also
allowed a generic or empty observation to match a record family and could omit
the metric/panel identity needed by Stage 2. Separately, shared inference-v2
lock drift was caught by the standalone static checker but had not yet been
made unavoidable in every live and post-hoc path.

**Decision.** Operationalize RQ1c parity as compilation from the same
label-blind source-semantic packet, not identical raster/text perceptual
decodability. Remove `observed_counts`, exact bin centers, unrounded values,
precomputed metric onset/persistence, and precomputed multi-hop paths from all
model arms. Preserve direct displayed edges and displayed propagation onset,
so models may derive paths and temporal conclusions themselves. Keep the
source-lineage map, strict `H=A+B`, and routed exact-once guarantees, but never
describe those checks alone as pixel-level information equality.

Require every Stage-1 observation to contain at least one readable named
attribute such as panel, metric, service, entry, caller, or callee. Forward an
observation and its candidate support only if all coordinates match exactly one
atomic record. Keep empty, ambiguous, unmatched, invalid-candidate, free-form
conflict, and unverified relation claims in the private audit rather than the
Stage-2 evidence ledger. Use one versioned RQ1c v2 attestation schema with
separate effective-YAML and runtime-source hashes, checkpoint/tokenizer locks,
and exact model-specific runtime fields. Invoke the shared implementation-lock
validator during runtime freeze, live attestation, execution, and post-hoc
verification. An architecture bundle is incomplete whenever either registered
model is incomplete, even if the other model passes both primary hypotheses.

**Evidence and reasons.** The review reproduced an empty/generic metric
observation being marked grounded and identified fields that existed only in
serialized evidence. New regression tests now reject empty and ambiguous
observations, filter invented edges/temporal/missing/conflict claims, require
both architectures for aggregation, and fail closed on attestation/config
drift. Three authorized validation cases were regenerated CPU-only from the
amended packet and passed source-lineage, strict-hybrid, routed-exact-once,
schema, privacy, and public leakage checks. The shared runtime lock still
correctly blocks complete qualification because its runtime-validator hash is
stale.

**Consequences.** Earlier CPU-prepared RQ1c candidates are preserved under the
smoke root's `cpu_prequalification_archive/` and are not resumable inputs. The
current prepared indexes and resolved config hashes supersede them. No RQ1c
smoke or efficacy result is invalidated because zero model calls have occurred.
Smoke remains disabled and the aggregate live supervisor remains intentionally
unwired until the active experiment releases the runtime, the shared lock is
deliberately reconciled, CPU static qualification passes, and the user again
authorizes model execution.
## DD-43: Adopt a compact Nibi-portable source and global-contract layout

**Date:** 2026-08-09
**Status:** adopted

**Context.** The WSL implementation accumulated multiple copied generations of
RQ1 tooling: the retained RQ1 packages alone contained roughly 25,000 lines of
Python, while experiment configs, descriptions, findings, and launchers mixed
historical and current protocols. The layout also embedded workstation paths,
stored Python entry points under shell-script directories, and treated serving,
splitting, and scoring as partially independent per-RQ contracts. This was hard
to audit and unsuitable for a clean Nibi deployment.

**Decision.** Supersede the previous directory convention in this clean
workspace. Shared Python lives under `src/`; shell entry points live under
`scripts/`. The only root configs are the unified vLLM, dataset segmentation,
and RCA scorer YAML files, backed by extensible classes in
`src/unified_scripts/`. Every RQ has exactly three description documents, one
finding document per experiment, no more than ten/800 lines of shell launchers,
and five functional Python modules plus `__init__.py`, with a 2,500-line
functional-source ceiling. The shared `vlmrca` package moves from the RQ tree to
`src/vlmrca/`. RQ-specific adapters remain explicit and hash-recorded.

The Nibi serving contract omits `--gpu-memory-utilization`; no CanvasRCA VRAM
fraction cap is imposed. The model-specific Qwen/Gemma processing differences,
unquantized BF16, sampling, context/output ceilings, and scheduler capacity are
otherwise preserved. Build tooling uses the Alliance module and wheelhouse
workflow and Slurm shell launchers. This local preparation is static-only.

**Evidence.** Before cleanup, the RQ1 `rq1c_rca_v1`, `legacy_typed_v3`, and
`rq1lib` Python trees contained about 8,035, 6,153, and 11,098 lines
respectively. The refactored five RQ1 functional modules contain 1,286 lines;
four short RQ1 shell entry points contain 73 lines. Root `configs/` contains
exactly three files. Alliance documentation establishes Lmod modules, the
Alliance Python wheelhouse, Apptainer rather than Docker, Slurm batch execution,
and Nibi H100 resources.

**Alternatives rejected.** Moving copied RQ1 packages under the shared source
tree would satisfy the directory shape while preserving the maintenance
problem. Keeping separate frozen per-RQ inference/split/scorer configs would
allow fairness-critical drift. Setting GPU memory utilization to `1.0` would
still impose a project cap and increase OOM risk; omission expresses the user's
requested no-cap policy without falsifying physical memory limits.

**Consequences.** Historical copied code is recoverable from Git but is not part
of the Nibi worktree. RQ1 retains its experiment semantics through one
configuration-driven engine and four consolidated findings. Deployment must
build a new environment, freeze new hashes and rosters, run the bounded smoke,
and use new result IDs. A future RQ may subclass the unified contracts, but any
fairness-sensitive change requires a named adapter and a new protocol decision.

## DD-67: Finalize six RQ1 experiments on the eligible frozen evaluation roster

**Date:** 2026-08-09
**Status:** adopted

**Context.** The Nibi refactor consolidated four RQ1 experiments but the final
program still needed (a) a causal check that visual semantics, rather than mere
prompt perturbation, move the agent's evidence and ranking and (b) a check of
whether useful evidence is lost at the two-stage handoff. The project already
has a long-frozen 480-case evaluation roster; eleven cases carry an existing
invalid status. CodeShrink (arXiv:2607.29637) offered an analogy about spending
a fixed image canvas on readable content, but it is a 2026 preprint about
code-image compression rather than RCA.

**Decision.** Register `visual_counterfactual_rca` and `ledger_handoff_rca`
alongside `legacy_q9`, `cross_region`, `typed_two_stage`, and `matched_rca`.
Rerun all six on Nibi under new result IDs using all 469 eligible frozen cases:
96 AegisLab, 100 AIOPS-2022, 93 AIOPS-2025, 90 RE2-OB, and 90 RE2-TT. Exclude
the eleven invalid cases without replacement. Headline inference uses only the
289 AegisLab/AIOPS cases; RE2-OB and final-OOD RE2-TT remain separate slices.

The counterfactual experiment holds text and compute fixed while comparing the
factual image with label-blind targeted, placebo, and neutral interventions.
The handoff experiment compares semantically identical typed-text, visual, and
strict redundant handoffs before a common RCA stage. Fixed-fact blank-space
compaction is deferred to RQ2 because it changes layout, an RQ2 design axis.

**Evidence.** The roster arithmetic is 96+100+93+90+90=469, with 289 primary
cases. Existing RQ1 experiments distinguish direct perception, cross-region
composition, typed transfer, and end-to-end RCA but do not isolate controlled
visual influence or the representation of the intermediate ledger. CodeShrink
supports only the high-level fixed-canvas analogy; it supplies no RCA evidence
and has not been treated as such.

**Alternatives rejected.** Replacing invalid cases was rejected because it
would silently change a frozen evaluation roster. Pooling saturated RE2 slices
into the headline was rejected because it would distort the main-dataset
effect. Copying CodeShrink's attention/KV pruning or training machinery was
rejected because it changes effective information/compute and is not an RCA
intervention. Adding blank-space compaction to RQ1 was rejected to keep content
and layout redesign out of the representation-value claim.

**Consequences.** RQ1 now has exactly six finding authorities and three
canonical description files. Historical local outcomes remain historical;
final claims require complete, paired, newly identified Nibi artifacts. RQ2
does not begin until these RQ1 results are verified and the representation
decision is recorded.

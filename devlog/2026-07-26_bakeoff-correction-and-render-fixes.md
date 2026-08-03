# 2026-07-26 — Correcting the bake-off: decoding, coverage, and four text-budget bugs

*Term definitions (MRR, parse rate, chain-of-thought, DNF, and so on) are in the
2026-07-23 devlog's "Terms" block. "Design decision (DD)" = a numbered, recorded
choice in `plans/design_decisions.md`. **Paired sd** = the standard deviation of
the per-case differences between two runs. **MDE** (minimum detectable effect) =
the smallest true difference a test can reliably find at a given number of cases.*

## What this session was for

The 2026-07-24 devlog left the screening-model choice open, with `gemma-4-e4b`
(MRR 0.508, 5.7 s/case) and `qwen3.6-27b` (0.658, 51.8 s/case) as finalists. The
task was to continue with `gemma-4-e4b` — but re-reading the eight bake-off cells
first showed the ranking could not support that choice, or any choice.

**The headline: no number produced before today is reproducible as recorded.**
Not because of one bug, but because of three independent ones that each look
small in isolation.

## 1. The models were not decoding the same way

`results/sbatch_logs/bakeoff_gemma-*.server.log` contains vLLM's own warning:

> `Default vLLM sampling parameters have been overridden by the model's`
> `generation_config.json: {'temperature': 1.0, 'top_k': 64, 'top_p': 0.95}`

The three Gemma entries carried no `extra`, and `_call_openai` passed only
`max_completion_tokens` and `**cfg.extra` — so **`cfg.temperature` was dead
code**. The Gemma cells were single random draws at temperature 1.0; the Qwens
ran greedy through `extra`. The head-to-head was never a comparison.

The client now builds sampling parameters explicitly for all four backends, and
the servers run `--generation-config vllm`.

## 2. That was not enough — and the ablation mattered

With explicit greedy sampling, two identical `gemma-4-e4b` runs **still disagreed
on 16 of 20 cases** (MRR 0.4392 vs 0.4792). The cause is server-side: with prefix
caching and chunked prefill on, the second run hits a KV cache the first warmed,
the changed reduction order flips a token, and an autoregressive answer cascades
from there.

Turning both caches off gives **0 of 20 differing, paired sd 0.0000**.

I had assumed `--enforce-eager` was also required and changed four flags at once,
then went back and ablated:

| recipe | differing | s/case |
|---|---|---|
| caches off, CUDA graphs on | 0/20 | **5.9** |
| caches off + `--enforce-eager` | 0/20 | 19.0 |

A 3.2× tax for nothing, so it is out. But note the two recipes give **different
MRRs on the same cases** (0.529 vs 0.475) because the kernel paths differ.
Determinism makes a recipe repeatable, not recipe-independent — whichever is
chosen must be used for every arm. Recorded as DD-12.

## 3. The frontier models cannot be fixed this way at all

A 2-case probe before submitting the Sonnet-5 reference run came back with parse
rate **0.000**:

> `ValidationException: `temperature` is deprecated for this model.`

Probing the registry:

| model | no sampling params | `temperature: 0.0` |
|---|---|---|
| claude-opus-4-7 | OK | **rejected** |
| claude-sonnet-5 | OK | **rejected** |
| claude-sonnet-4-6 | OK | OK |
| claude-sonnet-4-5 | OK | OK |

The split is generational. So the fix in §1, written to apply everywhere, *broke*
the path it was supposed to help. `temperature` and `top_p` are now `Optional`,
where `None` means omit the key entirely — an explicit `null` is still a rejected
parameter.

**The consequence outlives the fix.** Those two models cannot be run greedy, so
their replicate noise is irreducible: ±0.050 MRR at n=100. Three things follow,
and they are not all bad. Paired tests stay valid (this is noise, not bias) but
lose power. Point estimates must be reported with the band. And the open-weight
path being deterministic becomes an argument for screening the RQ1 grid there on
its own merits, not merely on GPU cost. Recorded as DD-14.

*Why this was caught:* a 2-case probe before a 400-call job. The probe cost about
30 seconds and would otherwise have been a paid run returning nothing.

## 4. What the noise floor actually implies for the design

`smoke_aegislab_sonnet` and `aegis_dedup_off` turn out to be an accidental
replicate — same model, same 20 cases, functionally identical dashboard. They
disagree on 5 of 20. That gives a decomposition worth having:

| pair | isolates | paired sd |
|---|---|---|
| two Sonnet runs, same config | replicate noise alone | 0.255 |
| Sonnet, caps on vs off (DD-11) | config effect **+** noise | 0.262 |
| two open-weight runs, DD-12 recipe | replicate noise alone | **0.000** |

The two Sonnet rows are nearly equal, and that is the finding: subtracting
variances leaves a config-effect sd of roughly **0.060**, meaning almost all the
spread in DD-11's A/B was the model disagreeing with itself rather than the two
dashboards differing.

| decoding | MDE at n=100 | cases needed for +0.03 |
|---|---|---|
| stochastic (as measured) | 0.073 | **598** |
| deterministic (estimated) | 0.017 | **32** |

`docs/rq1_design.md` §5 adopts a dashboard level at ΔMRR ≥ +0.03. **Under the
decoding every previous run used, that rule could never have fired** on
AegisLab's 100 cases — the grid would have returned "draw" for every level
whatever the dashboards did. The threshold survives; decoding was the thing that
had to change. Written up as §5.1, with the caveat that 0.060 is a difference of
two near-equal variances from n=20 and that the first deterministic config A/B
measures it directly.

One clause did not survive: the rule's requirement that the Sonnet-5 confirmation
beat B1 by +0.02. Per DD-14 that needs ~1345 cases; even the full 480-case pool
only reaches an MDE of 0.034. Recommended replacement is directional confirmation
on the full pool — the noisier instrument should not be the one asked for the
finer measurement.

## 5. "Thinking hurts" was two artifacts

The 2026-07-24 conclusion rested on two runs that measured nothing:

- `qwen3.5-9b` hit `stop_reason=length` at **exactly 16384** on 8 of 20 cases —
  chains of thought truncated mid-sentence and scored 0. Paired on the 12 that
  finished: **0.694 with thinking vs 0.417 without**, and 0.694 is above the
  AegisLab text SOTA of 0.679.
- `qwen3.6-27b` lost its server after case 3 and failed 18 of 20 with connection
  errors and zero output tokens. Its 0.050 is an infrastructure failure.

On `qwen3.5-4b`, where thinking almost always fit, it was worth **+0.22 MRR**
paired. So the budget was the problem, not the reasoning. Thinking is restored as
a per-model axis with a real budget (context 49152, output 32768 — the old run
served 32768 total while asking for 16384 output, which is exactly why it
truncated).

The 27b failure pattern is worth recording even though it is not fully
root-caused: every failed case took **exactly 7.0 s**, which is 1+2+4 s of retry
backoff against instant refusals. The server log stops mid-normal-logging with no
error. The pipeline's response is fixed — the runner now aborts after consecutive
backend failures and marks the summary `aborted`, instead of scoring 17 cases
zero and producing a publishable-looking 0.050.

## 6. The dashboard often did not contain the answer

Measured across all 100 AegisLab cases: the injected service gets **no metric
panel in 34 of them**; it is in neither metrics nor topology in 6; it is nowhere
in 2. Running the modality arms — the thesis test — on a dashboard that omits the
answer a third of the time would understate the representation rather than
measure it.

The ranking is not at fault: the true service's median rank among ~51 is 3–4, it
is never unrankable, and no alternative scoring beats the incumbent `max`. It is a
budget problem, so the fix is a selector, not a better score:

| selector | GT gets a panel | services shown | services with ≥2 panels |
|---|---|---|---|
| budget 12, top-K (`v0`) | 66% | 6.0 | 2.4 |
| budget 30, reserve 20 (`cov30`) | **90%** | 20.3 | 3.7 |
| budget 30, round-robin (`cov30f`) | 96% | 30.0 | **0.0** |

`coverage_first` reserves N slots for distinct services and spends the rest on
top-K, so both extremes stay reachable and plain top-K remains the RQ4 ablation
baseline. `cov30` is the working default. DD-13 records the caveat that it changes
coverage *and* density at once, and pre-registers `cov12` as the follow-up that
separates them.

## 7. Four renderer bugs, all the same class

Found by the **render-reviewer** agent across two passes, both of which also
returned GO — the defects came from looking at panels nobody asked about.

All four are *text budgeted without reference to the container it has to fit in*:

- Topology caption overlapped by a node → reserve margin from the axis limits.
- Panel titles cut at a constant 52 characters regardless of column width →
  derive from the figure geometry.
- Legend rows at a constant 26 or 34 characters → derive from the side column.
- **The one that matters:** at the resulting 16-character name budget,
  `ts-consign-price-service` and `ts-consign-service` both render as
  `ts-cons~-service` with the same index number. **95 of 100 cases** in both
  configs. The Service index is what makes a numbered topology readable at ~50
  services, so it was silently failing at its only job in every run to date.

The mechanism is a good trap: `_elide` truncates from the middle, "keeping the
distinguishing tail" — correct for metric names, where the percentile
discriminates, and exactly wrong for AegisLab service names, where everything
ends in `-service`. The docstring describes a deliberate choice that happens to be
inverted for this data.

Fixed by geometry-derived widths (16 → 28 chars at `v0`) plus `_elide_distinct`,
which re-cuts colliding groups from the head. **95/100 → 0/100 on both configs.**
The manifest now carries `ambiguous_names`, so the next such defect is greppable
from results instead of needing another pair of eyes.

`RENDERER_VERSION` is now 4 and participates in the config fingerprint — without
that, the render cache would have served pre-fix PNGs under an unchanged key and
two runs would have reported the same fingerprint having seen different
dashboards.

## 8. Repo hygiene worth noting

- `.gitignore` ended with a blanket `*.json` / `*.jsonl` (no trailing newline),
  silently untracking every experiment summary and trajectory — including
  `configs/case_manifest_480.json`. The "trajectories (git)" convention in
  CLAUDE.md was simply not in force. Removed.
- `paired_compare` had **zero callers**. Invariant 6 (paired Wilcoxon + Cohen's d
  for every A-vs-B claim) had never been exercised; DD-11's statistics were
  computed ad hoc. `scripts/compare_runs.py` is its first caller, validated by
  reproducing DD-11's published numbers from the archived trajectories.
- `configs/experiments/` was empty, and `--config` only set
  `DashboardConfig(name=...)` while keeping every default — so any "controlled
  variables" block would have been fiction. Real presets now, with `--set`
  overrides that raise on an unknown field.
- The determinism gate **destroyed its own evidence**: job 18544462 was the
  failing pre-fix run and job 18545267 overwrote its trajectories with a passing
  one. The finding that justifies the entire recipe survives only in a `.out`
  log. `RUN_TAG` now defaults to the job id.
- `configs/upstream_pin.yaml` does not exist, so `check_upstream_pin()` is a
  silent no-op. Flagged, not fixed.
- Scoring leniency was checked and is **upstream's intent, not a bug**: 16 of 100
  AegisLab cases have a second accepted label via `ground_truth_candidates`.
  Invariant 1 freezes the scorer, so this is reported and left alone.

## What is running

Determinism gate on the final recipe and the v4 renders, with Array A
(6 models × 4 arms, AegisLab n=100) queued behind `--dependency=afterok`. The
Sonnet-5 reference arms are written and **not** submitted, at the user's
instruction.

## What this produces

1. **Screening model**, chosen on `MRR(hybrid) − MRR(text_only)` — dashboard
   sensitivity, not raw MRR. A model that scores the same without the image
   cannot separate dashboard designs whatever its absolute accuracy. Ties broken
   on GPU-hours.
2. **The thesis gate.** If `text_only ≈ hybrid` for the open models *and*
   Sonnet-5, stop and escalate before M2 — the central claim is in question and
   no amount of grid work fixes that.
3. **The selector A/B** (`cov30` vs `v0`, both hybrid), which also gives the first
   direct measurement of the config-effect sd that §4's threshold rests on.
4. **The thinking axis**, paired against Array A's hybrid arm on identical cases.

## Lesson

Every one of the three decoding problems was invisible in the results and visible
in a log or a probe: vLLM printed the override warning, the failing gate printed
16/20, Bedrock printed the ValidationException on the second call. The metrics
looked fine throughout — 0.508 and 0.658 are perfectly plausible numbers. The
renderer half repeats the standing lesson from CLAUDE.md: four defects, a green
test suite, and the only thing that found them was looking at the pixels.

---

# Results (2026-07-27)

Array A completed: 6 models x 4 arms, AegisLab n=100, 24 usable arms and 4
excluded. Plus a `cov12` follow-up and a thinking axis. What follows is what the
runs actually said, including the parts that contradicted what I recorded
earlier the same day.

## The headline, and it is not the one the gate was built to test

The thesis gate asks whether adding the dashboard to the evidence text improves
accuracy. Across four clean models it does not:

| model | hybrid | text_only | delta |
|---|---|---|---|
| gemma-4-26b-a4b | 0.448 | 0.333 | +0.115 (p=0.012) |
| gemma-4-e4b | 0.441 | 0.412 | +0.029 |
| qwen3.6-27b | 0.499 | 0.482 | +0.017 |
| gemma-4-12b | 0.452 | **0.510** | -0.058 |

Mean +0.026, nothing significant after Bonferroni. The report prints STOP AND
ESCALATE, which is what it was designed to do.

But the `image_only` arms — written off in the array header as "diagnostic
rather than decisive" — say something the gate never asked:

| model | image only | tokens | text only | tokens | tokens saved | accuracy kept |
|---|---|---|---|---|---|---|
| qwen3.5-4b | 0.398 | 5074 | 0.413 | 8330 | 1.6x | **96%** |
| qwen3.6-27b | 0.429 | 5074 | 0.482 | 8330 | 1.6x | **89%** |
| gemma-4-26b-a4b | 0.257 | 2755 | 0.333 | 9252 | 3.4x | 77% |
| gemma-4-12b | 0.168 | 2755 | 0.510 | 9252 | 3.4x | 33% |
| gemma-4-e4b | 0.112 | 2751 | 0.412 | 9248 | 3.4x | 27% |

For the three models that can read a chart at all, **a rendered dashboard alone
reaches 88% of the full serialised telemetry's accuracy on half the input
tokens**, and none of the three differences is resolvable at n=100. That is the
accuracy-vs-tokens Pareto claim CLAUDE.md already names as the M5 deliverable.
The gate was operationalising "the dashboard is the representation" as *more
accurate than text* when the defensible claim is *comparably accurate, far
cheaper*. Recorded as DD-16.

The caveat that must travel with it: `image_only` is lower in all five models, so
this is efficiency and not parity.

## Everything is below the baseline it has to beat

Every open model is **0.17 to 0.35 MRR below the AegisLab text SOTA of 0.679, in
every modality**. Best open `text_only` is 0.510; best open `hybrid` is 0.499.
Whether a dashboard helps a model that far from competent is a different question
from whether it helps a competent one, and this panel cannot answer the second.
The Sonnet-5 reference is held at the user's instruction and remains the only
thing that separates "the representation is weak" from "the panel is weak".

## The selector: coverage-first is withdrawn

`cov12` differs from `v0` in one field — the selector — at identical panel count,
pixels and grid, so it isolates coverage from density. It **loses in all four
models tested** (-0.079, -0.034, -0.052, -0.034), Gemma and Qwen alike.

`cov30` looked like a family split (Gemmas negative, Qwens positive) until the
clean axis was run. `cov30` changes three things at once — selector, budget
12->30, and image size 1568->2048px — and the Qwens are the family that can read
charts, so the likeliest explanation for their gain is the **bigger image**, not
the selector. If that holds, resolution is a far better RQ1 lever than coverage
tuning, and it is cheap to test.

## Thinking: the small Qwens never terminate

Doubling the output ceiling from 16384 to 32768 did not let `qwen3.5-4b` or
`qwen3.5-9b` finish a chain of thought — they truncated 11/11 and 10/10 at the
*new* ceiling. Cancelled both rather than spend ~25 GPU-hours on arms of zeros.
`qwen3.6-27b` terminates normally and is still running. So the 2026-07-24
conclusion stands for the small Qwens, and my argument for overturning it was
wrong (DD-15).

Truncation is a Qwen-family property here, not a task property: no Gemma arm
truncates at all. It cost four arms to the parse-rate exclusion.

## Five things the apparatus caught that the metrics did not

1. **Bedrock rejects `temperature` for Claude 5** — found by a 2-case probe
   before a 400-call run. The Claude 5 models cannot be run greedy at all, so
   their +/-0.050 replicate band is irreducible (DD-14).
2. **A port collision and a trap that killed sibling servers.** SLURM packed four
   single-GPU tasks onto one node while the script hardcoded port 8000, and the
   EXIT trap `pkill`ed every vLLM the user owned on that host.
3. **`paired_compare` returned reduced dicts** on exactly the branches that fire
   on real data — identical runs, and buckets under 5 cases, which every
   per-fault breakdown produces.
4. **The screening report was deciding from in-flight runs**, reporting
   `delta=-0.247, p=0.035` off 25 of 100 cases. `qwen3.6-27b` read 0.674 at n=47
   and finished at **0.499** — a partial would have been wrong by 0.175.
5. **Truncation hid a sign flip.** `qwen3.5-4b` reported a perfect +0.000 null;
   on the 82 cases where both arms terminated it is -0.037. 17 text_only
   truncations against 3 hybrid, and unparsed answers score 0.

## Three claims I recorded and then had to weaken

Worth writing down as a pattern rather than three separate embarrassments.

- **The +0.03 threshold survives under determinism.** It does not. The measured
  config-effect sd is 0.36, not the 0.060 I estimated by subtracting two
  variances measured at n=20 — a difference of 0.0036 extracted from quantities
  whose own sampling error is +/-0.02. MDE at n=100 is 0.101 and +0.03 would
  need 1142 cases.
- **Dashboard value tracks panel coverage.** Mostly confounded. `text_only`,
  which never sees the dashboard, scores +0.20 to +0.51 higher on "covered"
  cases — panels are picked by anomaly score, so "covered" nearly restates
  "easy". The causal difference-in-differences is much smaller and rests on 10
  cases.
- **Coverage-first loses in six of six comparisons.** All six were one model
  family. With the Qwens it was six of eight, p=0.145 — until the clean axis
  reversed the reading again.

All three failed the same way: a clean pattern across everything available, where
"everything available" was a biased slice — one n=20 pair, one selector's easy
cases, one model family. The fix is not "wait for all the data", which would stop
all recording. It is to **carry the slice inside the claim**, so the next reader
sees the boundary without re-deriving it.

The same shape appears in the thinking analysis (conditioning on "the trace
finished" conditions on "the case was easy") and in the coverage analysis. A
standing check now: *before comparing a subset that survived a filter, ask whether
the filter correlates with the outcome.*

## Still open

- `qwen3.6-27b` cov12 and thinking arms running.
- Sonnet-5 reference: written, not submitted, held.
- Resolution-matched rendering per vision encoder — the Gemma family spends 2755
  image tokens where Qwen spends 5074 on the same dashboard and is the family
  that cannot read it. If that is downsampling rather than incapability, every
  Gemma number here understates.
- `configs/upstream_pin.yaml` still does not exist, so `check_upstream_pin()`
  remains a silent no-op.

# 2026-07-27 — The corrected bake-off: final results

*Terms are defined in the 2026-07-23 devlog's "Terms" block. **Paired sd** = the
standard deviation of the per-case differences between two runs. **MDE** (minimum
detectable effect) = the smallest true difference a test can reliably find at a
given number of cases; below it, a real effect is usually reported as a draw.
The correction work that made these runs possible is in the
[2026-07-26 entry](2026-07-26_bakeoff-correction-and-render-fixes.md).*

## What ran

| array | job | contents | outcome |
|---|---|---|---|
| A — model × modality | 18553844 | 6 models × 4 arms, AegisLab n=100 | all 6 completed |
| B — thinking axis | 18554163 | 3 Qwens, thinking on | 2 cancelled, 1 completed-but-unusable |
| cov12 follow-up | 18555711, 18562465 | 5 models, selector isolated | all completed |

Behind a determinism gate that passed 0/20, and — checked afterwards — **0/20
across separate SLURM jobs and server processes**, which is the property the
paired designs actually need since arms are compared across jobs.

24 usable arms. 5 excluded on parse rate, all Qwen truncation.

## The result that matters

The thesis gate asks whether adding the dashboard to the evidence text improves
accuracy. Across four clean models, no:

| model | hybrid | text_only | Δ |
|---|---|---|---|
| gemma-4-26b-a4b | 0.448 | 0.333 | +0.115 (p=0.012) |
| gemma-4-e4b | 0.441 | 0.412 | +0.029 |
| qwen3.6-27b | 0.499 | 0.482 | +0.017 |
| gemma-4-12b | 0.452 | **0.510** | −0.058 |

Mean +0.026; nothing significant after Bonferroni (α = 0.0083). The report prints
STOP AND ESCALATE, as designed.

**But the `image_only` arms — written off in the array header as "diagnostic
rather than decisive" — answer a question the gate never asked:**

| model | image only | tokens | text only | tokens | tokens saved | accuracy kept |
|---|---|---|---|---|---|---|
| qwen3.5-4b | 0.398 | 5074 | 0.413 | 8330 | 1.6× | **96%** |
| qwen3.6-27b | 0.429 | 5074 | 0.482 | 8330 | 1.6× | **89%** |
| gemma-4-26b-a4b | 0.257 | 2755 | 0.333 | 9252 | 3.4× | 77% |
| gemma-4-12b | 0.168 | 2755 | 0.510 | 9252 | 3.4× | 33% |
| gemma-4-e4b | 0.112 | 2751 | 0.412 | 9248 | 3.4× | 27% |

For the three models that can read a chart at all, **a rendered dashboard alone
reaches 88% of the full serialised telemetry's accuracy on half the input
tokens**, and none of those three differences is resolvable at n=100.

That is the accuracy-vs-tokens Pareto claim CLAUDE.md already names as the M5
headline deliverable. "The dashboard is the representation" had been
operationalised as *more accurate than text*; the measurement supports *comparably
accurate, materially cheaper*. Recorded as DD-16. The caveat that must travel
with it: `image_only` is lower in all five models, so this is efficiency, not
parity.

## The caveat that limits every conclusion here

Every open model is **0.17–0.35 MRR below the AegisLab text SOTA of 0.679, in
every modality**. Best open `text_only` 0.510; best open `hybrid` 0.499.

Whether a dashboard helps a model that far short of competent is a different
question from whether it helps a competent one. This panel cannot answer the
second. The Sonnet-5 reference — written, costed at ~$16–20, no GPU — is held at
the user's instruction and remains the only thing separating "the representation
is weak" from "the panel is weak".

## The selector: no reliable effect

`cov12` differs from `v0` in one field, the selector, at identical panel count,
pixels and grid — so it isolates coverage from density:

| model | cov12 − v0 |
|---|---|
| gemma-4-e4b | −0.079 (p=0.032, flagged underpowered) |
| gemma-4-26b-a4b | −0.052 |
| gemma-4-12b | −0.034 |
| qwen3.5-4b | −0.034 |
| **qwen3.6-27b** | **+0.050** |

Sign test 4 of 5: **p = 0.188**. All five below the ~0.10 an n=100 comparison
resolves. Neither DD-13's "coverage helps" nor DD-13a's "depth beats breadth"
survives. Plain top-K stays incumbent by the prefer-the-simpler-level tie-break,
not because it won.

One thing should not be buried in that null: **`qwen3.6-27b` with `cov12` scores
0.524, the highest MRR of any open-model arm in the cell**, above its own `v0`
(0.474) and `cov30` (0.499). The strongest model preferring the selector the
other four dislike is the opposite of a family story and deserves a targeted
re-run.

## Thinking: unmeasurable, not measured

All three Qwens fill whatever output budget they are given rather than using it.

| arm | n | truncated | parse | s/case |
|---|---|---|---|---|
| qwen3.5-4b | 11 | 11 | 0.00 | — (cancelled) |
| qwen3.5-9b | 10 | 10 | 0.10 | — (cancelled) |
| qwen3.6-27b | 50 | 21 | 0.58 | 1030 |

Doubling the ceiling from 16384 to 32768 did not help; it produced twice as much
before the cut. The 4b and 9b were cancelled rather than spend ~25 GPU-hours on
arms of zeros. The 27b ran 14h33m to an unusable arm at 16× the wall-clock of its
thinking-off run (1030 vs 65 s/case).

So thinking is **off for all three**, and the axis is unmeasurable in this design
rather than measured and rejected (DD-15 and its amendment).

## What the apparatus caught that the metrics did not

1. **Bedrock rejects `temperature` for Claude 5** — found by a 2-case probe
   before a 400-call run. Those models cannot be run greedy at all, so their
   ±0.050 replicate band is irreducible (DD-14).
2. **A port collision and a trap that killed sibling servers.** SLURM packed four
   single-GPU tasks onto one node while the script hardcoded port 8000, and the
   EXIT trap `pkill`ed every vLLM the user owned on that host.
3. **`paired_compare` returned reduced dicts** on exactly the branches that fire
   on real data — identical runs, and buckets under 5 cases, which every
   per-fault breakdown produces.
4. **The report was deciding from in-flight runs.** `qwen3.6-27b` read 0.674 at
   n=47 and finished at **0.499** — a partial would have been wrong by 0.175.
5. **Truncation hid a sign flip.** `qwen3.5-4b` reported a perfect +0.000 null;
   on the 82 cases where both arms terminated it is −0.037.

## Four claims recorded and then weakened, all the same shape

- **"+0.03 survives under determinism."** It does not. Measured config-effect sd
  is 0.36, not the 0.060 estimated by subtracting two variances from n=20 samples
  — extracting 0.0036 from quantities whose own sampling error is ±0.02. MDE at
  n=100 is 0.101; +0.03 would need 1142 cases.
- **"Dashboard value tracks coverage."** Mostly confounded: `text_only`, which
  never sees the dashboard, also scores +0.20–0.51 higher on "covered" cases.
  Panels are picked by anomaly score, so "covered" nearly restates "easy".
- **"Coverage-first loses 6 of 6."** All six were one model family; then 6 of 8;
  then 4 of 5 on the clean axis, p = 0.188.
- **"The 27b terminates normally."** Read at n=9. At n=50 it had truncated 42%.

Each was a clean pattern across everything available, where "everything
available" was a biased slice — one n=20 pair, one selector's easy cases, one
model family, nine episodes. The fix is not "wait for all the data", which would
stop all recording. It is to **carry the slice inside the claim**, so the next
reader sees the boundary without re-deriving it.

The fourth instance refines it: the rule is not only for design decisions. "The
27b terminates normally" was a sentence written in passing, and it was wrong in
exactly the same way.

Related, and now a standing check: **before comparing a subset that survived a
filter, ask whether the filter correlates with the outcome.** Two of today's
findings failed this — coverage ("covered" ≈ "easy") and thinking ("finished" ≈
"easy"). `scripts/compare_runs.py` now prints truncation counts and recomputes
the delta on non-truncated cases on every comparison.

## Where this leaves the project

**Settled.** The measurement apparatus: deterministic across jobs, truncation-
audited, partial-run-safe, parse-rate-gated. Decoding recipe fixed and ablated.
Renderer text budgets derived from geometry. Every claim above is reproducible
from committed trajectories.

**Open, in priority order.**

1. **The Sonnet-5 reference.** The single highest-information run left; the only
   way to tell a weak representation from a weak panel. Held.
2. **Resolution-matched rendering.** Gemma spends 2755 image tokens where Qwen
   spends 5074 on the identical dashboard, and Gemma is the family that cannot
   read it (27%, 33%, 77% vs 96%, 89%). Consistent with downsampling past
   legibility rather than incapability — and if so, every Gemma number here
   understates. Cheap to test.
3. **`qwen3.6-27b` × `cov12` at 0.524**, the best arm in the cell, unexplained.
4. **The adoption rule.** §5.2 gives three options; none is chosen yet. At the
   measured sd, +0.03 is unreachable and the rule needs re-basing on the design's
   power (~+0.10 at n=100, ~+0.05 at 480) or on effect-size estimation instead of
   significance gating.
5. `configs/upstream_pin.yaml` still does not exist, so `check_upstream_pin()`
   remains a silent no-op.

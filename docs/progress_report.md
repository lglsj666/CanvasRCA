# CanvasRCA — progress report and knowledge transfer

> **2026-07-31 RQ0 update.** The equal-information/equal-inference-opportunity
> confirmatory experiment is complete: 720 incidents × 3 arms × 2 VLMs
> (4,320 formal calls). Visual+text+topology did not beat byte-identical text on
> Qwen3.6-27B (ΔMRR −0.0129) or Gemma-4-26B-A4B-it (−0.0112). It beat flat
> structured input only on Gemma (+0.0278, Holm p=0.0239), below the registered
> +0.05 practical threshold. RQ0 is therefore **unsupported**. See
> [the complete confirmatory report](2026-07-31_rq0_equal_information_equal_compute_results.md).
>
> **2026-07-31 follow-up.** Atomic controls show that both models read most
> dashboard facts but not renderer-v6's curved topology edges. A large explicit
> edge key lifts edge reading to 100% on Qwen and 91.7% on Gemma; however, paired
> case-level v7−v6 RCA on 12 development incidents is −0.0208 for Qwen and
> +0.0625 for Gemma, each driven by one case. The fix does not show a stable
> cross-model RCA benefit and will not advance to the reserve set. Next work is
> case-level causal-integration SFT preparation, not generic visual-grounding
> SFT or GRPO. See [the follow-up report](2026-07-31_rq0_followup_grounding_topology_and_v7_results.md).
>
> **2026-07-31 SFT pilot.** The project-owned BF16 rank-8 LoRA path passed its
> three-case optimizer smoke and completed a 24-example causal-integration
> pilot. On 12 disjoint development-heldout incidents, base/adapter MRR was
> 0.5444/0.4750 (Δ −0.0694; 0 improved, 2 degraded, 10 tied). Both degradations
> were prediction-list collapse: the adapter removed roots the base model had
> retained at rank 2 or 3. The checkpoint failed its registered promotion gate,
> nothing was saved to `models/best/`, and formal/reserve data remain unopened.
> See [the SFT protocol and result](2026-07-31_causal_integration_sft_protocol_and_smoke.md).
>
> **2026-07-31 SFT v2.1.** A five-service preservation/correction target fixed
> v1's prediction-list collapse, but did not improve RCA. After a 134-case base
> rollout, a preregistered feasibility amendment selected 30 development-only
> training cases. The eight-step BF16 LoRA completed and scored base/adapter MRR
> 0.5444/0.5028 on 12 fresh development-heldout incidents (Δ −0.0417; 0
> improved, 1 scored degradation, 11 tied). The sole degradation is a standard
> hashed pod/service scoring mismatch; alias-aware sensitivity makes it a tie,
> still with no improvement. v2.1 failed promotion, nothing was saved to
> `models/best/`, and formal/reserve remained unopened. See
> [the v2.1 report](2026-07-31_causal_integration_sft_v2_1_results.md).
>
> **2026-07-31 scoring audit.** The upstream service-level matcher misses
> ordinary hashed Kubernetes pod names. Alias-aware sensitivity changed
> 35/4,320 formal episode scores but left visual−text negative for Qwen
> (−0.0115) and Gemma (−0.0160). The defect is fixed for future project-owned
> scoring; historical registered results are unchanged (DD-24).
>
> **2026-07-31 nonredundant-allocation follow-up.** A frozen 24-case exposed
> development screen compared allocated image+summary (D), duplicated
> image+full text (A), and full text-only (B). Qwen D−B was −0.0292; Gemma was
> +0.1563. D−B simultaneously changes transport modality and redundancy, so it
> cannot identify an image-presence effect. The cross-model gate failed and no
> reserve/formal case was used or authorized. See
> [the allocation report](2026-07-31_nonredundant_modality_allocation_results.md).

**Written 2026-07-28.** For someone picking this project up with no prior
context. It says what the project is trying to prove, what has actually been
built and measured, what is known to be false, and what to do next.

Everything here is traceable to a numbered design decision in
[plans/design_decisions.md](../plans/design_decisions.md) (referred to below as
**DD-1** … **DD-24**) or to a dated entry in [devlog/](../devlog/). Where a
number is quoted, the caveat that bounds it is quoted with it — that habit is
itself one of the project's hard-won conventions (see §9).

---

## 1. Terms used in this document

Defined on first use, and collected here for reference.

| Term | Meaning |
|---|---|
| **RCA** | Root cause analysis — given an incident, name the service that caused it |
| **VLM** | Vision-language model: a model that takes images *and* text as input |
| **LLM** | Large language model (text only) |
| **SRE** | Site reliability engineer — the human whose job this automates |
| **Telemetry** | The three data streams a running system emits: metrics (numbers over time), logs (text lines), traces (records of one request crossing several services) |
| **Span** | One trace record: one service handling one request, with a start time, a duration, and a pointer to its parent span |
| **Microservice** | One deployable component; the systems here have 10–104 of them calling each other |
| **Call graph / topology** | Which service calls which. `A → B` means A calls B |
| **Fault injection** | The experiment method behind every dataset: deliberately break one service, record the telemetry, label which one it was |
| **Ground truth** | The label — the service that was actually broken |
| **MRR** | Mean reciprocal rank. The model returns a ranked list of 5 guesses; it scores 1 if the true cause is first, ½ if second, ⅓ if third, and 0 if absent. Averaged over cases. The project's headline metric |
| **top-1 / top-3** | Share of cases where the true cause is the first / within the first three guesses |
| **z-score (z)** | How far a value sits from its own normal level, measured in standard deviations. "z = 40" means forty times its usual wobble |
| **p95** | The 95th percentile — the value 95% of samples fall below. Standard for latency, because averages hide the slow tail |
| **NaN** | "Not a number" — a missing sample in a data table |
| **KPI** | Key performance indicator; here, one metric series chosen to occupy a dashboard panel |
| **Onset** | The moment a service's telemetry first crosses its anomaly threshold. Computed in this project by `RQs/vlmrca/render/onset.py` |
| **RQ1–RQ4** | The project's four research questions (§2) |
| **DD-n** | Numbered design decision, in `plans/design_decisions.md` |
| **Wilcoxon signed-rank test** | A paired statistical test for "is A better than B on the same cases"; makes no assumption that the differences are bell-shaped |
| **Bonferroni correction** | When running *k* tests at once, demand *k* times more evidence from each, so that testing many things does not manufacture a false positive |
| **sd** | Standard deviation — how much a quantity varies |
| **MDE** | Minimum detectable effect: the smallest true difference an experiment of a given size could reliably notice. Anything smaller is invisible no matter what you do |
| **Greedy decoding** | Making the model always pick its single most likely next word, so the same input gives the same output every time. The alternative (sampling) makes runs non-reproducible |
| **vLLM** | The server software used to run open-weight models on the cluster's own GPUs |
| **SLURM** | The cluster's job scheduler |
| **Bedrock** | Amazon's hosted-model service, used here for the Claude models |
| **Open-weight model** | A model whose parameters can be downloaded and self-hosted (Qwen, Gemma), as opposed to an API-only model (Claude) |
| **Image tokens** | The units a VLM charges an image in. A dashboard picture costs 2 700–5 100 of them depending on the model's vision encoder |
| **Golden test** | A test that pins the rendered image's hash, so any unintended visual change fails loudly |
| **Manifest** | A machine-readable description emitted alongside each rendered dashboard, listing every panel and its numbers |

---

## 2. What this project is

**The thesis: the dashboard is the representation.**

Human SREs diagnose incidents by looking at a wall of charts, not by reading
serialised tables of numbers. Every existing multimodal RCA system (TrioXpert,
LLMRCA, TAMO, OpsAgent) fuses raw metrics, logs and traces through learned
encoders or by flattening them into text. **None uses a rendered dashboard image
as the perception layer.** That gap is the contribution.

So the pipeline is: take one incident's telemetry → *render it as a dashboard
picture* → show that picture to a vision-language model → ask which service
broke → score the answer.

### The four research questions

- **RQ1** — How should all key telemetry be compiled into a single dashboard image?
- **RQ2** — What agentic loop (zoom, expand, traverse, re-render) improves accuracy from that first view?
- **RQ3** — Which VLM is best at this task?
- **RQ4** — What does each component contribute? (the ablation matrix)

### Relationship to the sibling project

`/home/tianyifa/projects/def-jacobsen/tianyifa/RL-SLM-RCA` does the **text**
version of the same task (one-shot context engineering, targeting ICSE 2027).
This project deliberately reuses its datasets, task statement, answer format and
scoring functions **verbatim**, so that "dashboard 0.6 vs text 0.605" is a
comparison of *representations* rather than of prompt wording.

**The shim contract.** [RQs/vlmrca/upstream.py](../RQs/vlmrca/upstream.py) is the *only*
sanctioned import path into that repo. Never `sys.path.insert` anywhere else,
never modify the upstream repo. The reason is mechanical: upstream has no
`pyproject.toml` and its package is literally named `src`, so `pip install -e`
is impossible without editing it and would install a package called `src` into
the environment (DD-1).

---

## 3. How the system works

```
DataCase  ──▶  CaseRenderView  ──▶  compile_dashboard  ──▶  PNG + manifest
(labelled)     (label stripped)      (pure, deterministic)         │
                                                                  ▼
                                                    prompt assembly ──▶ VLM
                                                                  │
                                                                  ▼
                                                  parse ──▶ score (upstream fns)
```

| Path | Role |
|---|---|
| `RQs/vlmrca/upstream.py` | The import boundary into the sibling repo |
| `RQs/vlmrca/cache.py` | Manifest-driven case loading |
| `RQs/vlmrca/render/` | **The dashboard compiler — the contribution** |
| `RQs/vlmrca/render/kpi_select.py` | Scores every metric series, picks which earn a panel, infers the fault window |
| `RQs/vlmrca/render/panels.py` | Draws each panel kind; returns a manifest entry per panel |
| `RQs/vlmrca/render/onset.py` | Per-service anomaly onset (added 2026-07-28) |
| `RQs/vlmrca/render/presets.py` | Named configurations (`v0`, `cov30`, `prop12`, …) |
| `RQs/vlmrca/vlm/` | Model clients and prompt assembly |
| `RQs/vlmrca/agent/` | Trajectory logging; RQ2 controllers (not yet built) |
| `RQs/vlmrca/eval/` | Pipeline runner and statistics |
| `plans/design_decisions.md` | Why things are the way they are |
| `devlog/` | Dated session log |

### The dashboard, as currently rendered

One PNG per case. Left two-thirds: a grid of small metric charts, each titled
`[M1] service · metric`, ordered by how far the series departs from its own
pre-fault baseline, with the exact deviation printed beneath it. A shaded
vertical band marks the estimated fault window. Right-hand column: either a
service call graph or (new) an anomaly-propagation strip, plus a numbered
service index and log/trace summary tables.

### Five invariants that must not be broken

1. **The output format is frozen** — a ranked top-5 JSON object,
   `{"services": [...], "reason", "confidence"}`, parsed and scored with
   upstream's own functions. Do not "improve" it.
2. **The renderer never sees a label.** `compile_dashboard` takes a
   `CaseRenderView`, which *structurally* has no ground-truth field.
   `tests/test_no_leakage.py` enforces this. Note what is *not* leakage: the
   true service's name legitimately appears among the candidates, because the
   model is asked to name a service. What must never appear is anything
   marking it as the answer.
3. **The renderer is pure and deterministic** in `(view, config)`. Seeded
   layout, sorted iteration. Every A/B comparison depends on this.
4. **Every rendering behaviour is a config field.** A behaviour without a field
   cannot be ablated, and RQ4 *is* the ablation matrix.
5. **Image tokens count** in every cost number, and **per-dataset and per-fault
   breakdowns always**. Any A-vs-B claim rests on a paired Wilcoxon test matched
   by case, plus effect size — not on confidence intervals.

---

## 4. The data

Raw data lives in `/scratch/tianyifa/data/{aegislab,aiops2022,aiops2025,rcaeval}`.
Parsed cases are cached as pickles in `$SCRATCH/eda_cache` (~0.5 s to load a
case, versus ~30 s of re-parsing) (DD-2).

The evaluation pool is **frozen** in
[configs/case_manifest_480.json](../configs/case_manifest_480.json) — 480 cases:
100 AegisLab + 100 AIOPS-2022 + 100 AIOPS-2025 + 90 RE2-OB + 90 RE2-TT, seed 42
(DD-3).

### Dataset difficulty is wildly uneven — this shapes every claim

Best published **text**-based accuracy, per dataset:

| Dataset | Text SOTA (MRR) | Character |
|---|---|---|
| AegisLab | 0.679 | The primary screening dataset. 104 graph nodes, ~1 500 metric series, 15-second metric sampling |
| AIOPS-2022 | 0.532 | 46 services, ~4 600 metric series, 60-second sampling |
| AIOPS-2025 | 0.390 | Hardest. Its call graph is nearly useless — 15 edges over 61 nodes, 49 of them isolated |
| RE2-OB | 0.994 | **Saturated.** 10 services, 1-second sampling |
| RE2-TT | 0.994 | **Saturated** |

**RE2-OB and RE2-TT are solved.** A near-1.0 result there means the pipeline
works, not that the method is good. **Every claim must rest on AegisLab and the
AIOPS sets.**

### What each dataset can actually support

All five have traces with usable parent-child links (86 000 – 1 200 000 spans
per case). But metric-entity names and call-graph node names are partly
different naming universes, which limits how much can be joined:

| Dataset | Metric entities in the call graph |
|---|---|
| AegisLab | 30 of 98 |
| AIOPS-2022 | 40 of 63 |
| AIOPS-2025 | 10 of 59 |
| RE2-OB | 7 of 10 |

Roughly one case in twelve on the AIOPS sets has no traces at all. Any feature
built on traces needs a graceful fallback.

---

## 5. What has been built

| Milestone | State |
|---|---|
| **M0 — scaffold** | ✅ Done. Package, shim, frozen manifest, environment script, tests, skills, agents. The GPU half closed 2026-07-23: the cluster's vLLM serves the open-weight panel with images |
| **M1 — smoke pipeline** | ✅ Done. `case → dashboard → VLM → parse → score` end to end |
| **M1.5 — corrected open-weight bake-off** | ✅ Done 2026-07-27. Not in the original plan; added because the first bake-off could not support the decision it was run to make |
| **M2 — RQ1 dashboard design grid** | ⬜ Not started. Design written in [docs/rq1_design.md](rq1_design.md) |
| **M3 — RQ2 agentic loop** | ⬜ Not started |
| **M4 — RQ3 model panel** | ⬜ Partially pre-empted by the bake-off |
| **M5 — RQ4 + paper** | ⬜ Not started |

**Renderer version 5** is current (`v0` preset fingerprint `3b3e178c56`).
65 tests pass. The version number participates in every cache key, so bumping it
correctly invalidates all previously rendered images.

---

## 6. What has been measured

### 6.1 The corrected open-weight bake-off (2026-07-27)

Six open-weight models × four arms, AegisLab, 100 cases each, greedy decoding
behind a determinism gate that holds *across* separate cluster jobs. 24 usable
arms; 5 excluded for failing to produce parseable answers (all Qwen output
truncation).

**The modality table — the most important result in the project so far.**
"Keep" is image-only accuracy as a share of text-only accuracy.

| Model | hybrid | text only | image only | image tokens | text tokens | keep |
|---|---|---|---|---|---|---|
| gemma-4-e4b | 0.441 | 0.412 | 0.112 | 2 751 | 9 248 | 27% |
| gemma-4-12b | 0.452 | 0.510 | 0.168 | 2 755 | 9 252 | 33% |
| gemma-4-26b-a4b | 0.448 | 0.333 | 0.257 | 2 755 | 9 252 | 77% |
| qwen3.5-4b | 0.413 | 0.413 | 0.398 | 5 074 | 8 330 | 96% |
| qwen3.5-9b | 0.337 | 0.374 | 0.330 | 5 074 | 8 330 | 88% |
| qwen3.6-27b | 0.499 | 0.482 | 0.429 | 5 074 | 8 330 | 89% |

Other axes:

| Axis | Result |
|---|---|
| hybrid vs text-only | mean **+0.026**; nothing survives Bonferroni correction |
| image-only vs text-only | **~88% of the accuracy on ~half the tokens**, for the three models that can read a chart |
| Selector (`cov12` vs `v0`) | 4 of 5 negative, p = 0.188 — **no reliable effect** (DD-13a, twice amended) |
| Thinking mode (Qwen) | **Unmeasurable** — all three fill whatever output budget they are given (DD-15) |

Best single open-model arm anywhere in the cell: `qwen3.6-27b × cov12 = 0.524`,
unexplained, deserves a targeted re-run.

### 6.2 The thesis gate tested the wrong axis (DD-16)

The gate was written as `MRR(hybrid) > MRR(text_only)`. It **fails**. But the
`image_only` arms — originally dismissed as merely diagnostic — show a rendered
dashboard alone reaching ~88% of full serialised-telemetry accuracy on about half
the input tokens, for models that can read charts.

**Decision: the thesis is restated on two axes.**

1. **Accuracy** — does the dashboard beat text? *Currently no, for open models.*
2. **Efficiency** — does it reach comparable accuracy at materially fewer
   tokens? *Currently yes, for models that can read charts.*

Failing (1) while passing (2) is a result, not a refutation — and (2) is exactly
the accuracy-versus-tokens Pareto frontier already named as the M5 deliverable.

### 6.3 The bound on all of it

**The whole open-weight panel sits 0.17–0.35 MRR below AegisLab's text SOTA of
0.679, in every modality.** Best open text-only is 0.510; best hybrid 0.499.
Whether a dashboard helps a model that far from competent is not the question
the project is asking. This is why the **Sonnet-5 reference run** matters: it is
the only thing that separates "the representation is weak" from "the panel is
weak."

### 6.4 The statistical reality that constrains M2

Measured config-effect **sd = 0.36**, not the 0.060 originally assumed. So at
n = 100 the **MDE is ~0.101 MRR**, and the planned "adopt a level at ΔMRR ≥ +0.03"
rule would need **1 142 cases** per comparison. *The adoption rule as written is
not achievable.* M2 must either screen far larger, accept larger effects only, or
lead with the $0 perception-based screening described in `docs/rq1_design.md`.

Separately, the Claude 5 models reject the decoding parameters that would make
them reproducible, so those arms carry an **irreducible ±0.050 MRR band at
n = 100** (DD-14). The open-weight path is the deterministic one.

### 6.5 The 2026-07-28 renderer work

**The metric grid was blank on the sparse datasets, and every result above was
scored against it (DD-17).** Three compounding defects:

1. Metric tables are pivots over a *union* timestamp index, so each column holds
   values only on the timestamps its own scraper wrote — 8–96 valid samples in a
   1 064-row AegisLab table. The plotting library breaks a line at every missing
   value, so nothing was drawn.
2. The scorer *preferred* those columns: three flat baseline points give a
   microscopic spread and a maxed-out z-score. A quarter of all panels went to
   series that could not be drawn.
3. The fault-window band expanded row-by-row, where one missing neighbour halts
   the walk — collapsing it to ~2.6% of the window, about 8 pixels.

Fixes measured on AegisLab: maxed-out-score share 25% → 21%, band width
2.6% → 37.6%, and **injected-service panel coverage 66% → 77.5%**. A
long-standing selection pathology (DD-11) fixed itself as a side effect.
**This is a live confound for §6.2** — the `image_only` arms were reading a
dashboard whose metric grid was empty, so that arm was measuring the topology
thumbnail and two tables.

**Anomaly onset is now computed and rendered (DD-18).** `RQs/vlmrca/render/onset.py`
derives per-service onset from binned p95 span latency, with a metric fallback.
`topology="propagation"` (presets `prop12`, `prop30`) replaces the call-graph
thumbnail with services in rows on the metric panels' own time axis.

**Its premise was tested and refuted.** The idea was that onset order surfaces
the origin better than magnitude, since a saturated dependency moves its own
metrics less than everything queued behind it. Measured on 30 AegisLab cases,
ranking the *same* services by magnitude finds the injected one at **median rank
2.0 against onset's 5.5** (top-3 79% vs 42%, Wilcoxon p = 0.014). The panel was
rebuilt to **select by severity and display by onset**; its rows now contain the
true cause **93%** of the time. Onset is shown because it is evidence magnitude
does not carry — *not* because it ranks better. **Nothing should describe
"earliest onset" as "most likely cause."**

Also closed: a metadata leak that had not yet fired (DD-19 — the renderer's
filter was a blacklist matching key names exactly, and AegisLab passes
`injection_ground_truth`, the answer spelled out), and a layout-geometry error
that garbled the service index in every 25-entry AegisLab case (DD-20).

---

## 7. Design decisions, one line each

| DD | Subject |
|---|---|
| 1 | Reuse the sibling repo through a single import shim, not pip/vendor/submodule |
| 2 | Use the cached loader family (0.45 s/case instead of tens of seconds) |
| 3 | Freeze and commit the 480-case manifest |
| 4 | Bound anomaly scores; floor the spread by the series' own magnitude |
| 5 | Auxiliary panels show *change* across the fault window, not absolute state |
| 6 | Resolve log/trace timestamps by window overlap, not by magnitude heuristics |
| 7 | Sonnet-5 for screening, Opus for frozen headline runs |
| 8 | Plot metric panels against elapsed time, not row index |
| 9 | Colour topology nodes by within-case *rank*, not raw magnitude |
| 10 | Never print the score-clipping sentinel as though it were a measurement |
| 11 | Redundancy caps exist as an axis but default off (capping *looked* right, measured worse) |
| 12 | Reproducible decoding is a serving-flag problem; explicit recipe recorded |
| 13 | Coverage-first selection — adopted, then self-corrected |
| 13a | "Depth beats breadth" — withdrawn; the effect was one model family, then **no reliable effect** at n=100 |
| 14 | Claude 5 rejects the reproducibility parameters; those arms carry ±0.050 |
| 15 | Thinking mode is off for all Qwens and the axis is unmeasurable in this design |
| 16 | **The thesis gate tested the wrong axis** — restated on accuracy *and* efficiency |
| 17 | **The metric grid was blank on the sparse datasets** and the scorer preferred it that way |
| 18 | **Anomaly onset as a first-class signal**; its ranking premise refuted; select by severity, display by onset |
| 19 | The metadata filter was a blacklist and it was leaking |
| 20 | The side column was never as wide as the code thought |
| 21 | Readable topology is necessary but not sufficient for RCA |
| 22 | Causal SFT must preserve a useful ranking before trying to correct it |
| 23 | Preservation fixed list collapse, but v2.1 supplied no causal correction |
| 24 | Hashed pod aliases are a real scorer defect, not an RQ0 explanation |

---

## 8. What to do next, in priority order

1. **Keep RQ0 frozen as unsupported.** Renderer v7, two SFT pilots, and the
   hashed-pod sensitivity all failed to produce a stable visual-over-text gain.
   Do not reuse formal/reserve data to search for a positive number.
2. **Use the corrected entity-granularity scorer for all new experiments.** It
   is frozen in `RQs/vlmrca/eval/scoring.py`; historical primary numbers remain
   upstream-scored and immutable.
3. **Keep the completed allocation result bounded.** D−B simultaneously changes
   modality and redundancy, and the cross-model gate failed. It cannot support
   an image-presence claim and cannot authorize reserve use.
4. **Require exact model-visible fact parity before every modality comparison.**
   The text arm must receive the same complete sequences, actual directed edges,
   paths, missingness and auxiliary evidence visible in the image arm.
5. **Keep agentic zoom and the Sonnet reference separate.** They answer different
   questions and cannot overwrite RQ0. RL/GRPO remains outside the first paper.

---

## 9. Lessons this project has already paid for

These are the conventions that exist because something went wrong. They are the
most valuable part of this document.

### Render, look, then measure

**Six real renderer bugs in the first day were found by looking at the rendered
images — not by tests, not by metrics.** The test suite passed throughout. One
made the dashboard contradict its own ground truth; another filled every panel
with a single metric family while the true cause got none.

**Three more on 2026-07-28, the same way.** The metric panels were *empty* on
AegisLab and had been for every run to date. No test noticed, because a blank
chart is a valid image.

### Text budgeted without reference to its container — four times now

- **2026-07-26:** panel titles cut at a constant 52 characters regardless of
  column width; legend rows at a constant 26. The worst made
  `ts-consign-price-service` and `ts-consign-service` both render as
  `ts-cons~-service` with the same index number, in **95 of 100 cases** — so the
  service index silently failed at its only job for every run to date.
- **2026-07-28:** the propagation panel reproduced the class exactly (row names
  budgeted against the wrong figure, onset readouts clipped by the figure edge),
  and then DD-20 found the same bug *one level up*: the container-width formula
  itself was wrong by 23–25%, because it ignored the gutters between columns.

Two rules follow. Prefer collision-aware elision for anything a reader must match
against something else. And **check any layout arithmetic against what the
plotting library actually draws**, not against arithmetic on its arguments — a
hand-calibrated constant had been silently absorbing the error, concealing a bug
in the very thing it was calibrated against.

### Carry the slice inside the claim

Four separate claims have been recorded and then weakened, all the same shape:
*a clean pattern across a biased slice.* "Depth beats breadth" lost 6 of 6 paired
comparisons — all six were one model family, and with the others included the
sign reversed. Before comparing a subset that survived a filter, ask whether the
filter correlates with the outcome.

### A small clean result is not a result

The propagation panel's premise looked confirmed on the case that motivated it
(the true cause went from invisible to first place) and on a 12-case pilot. At
n=30 it reversed, significantly, in the opposite direction. **Test the premise
against the alternative it claims to beat, on enough cases to see it.**

### Whitelists, not blacklists

DD-19's leak survived because a blacklist can only exclude the names someone
thought of, and the upstream loaders are free to invent more. Any filter over
keys someone else controls should fail closed.

### Put the audit field in the manifest

After the 95-of-100 elision defect, the render manifest carries `ambiguous_names`
so the next such failure is greppable from results instead of needing another
pair of eyes. Do this for every new invariant that a human currently has to look
for.

---

## 10. Working with the code

```bash
source scripts/env.sh          # venv + PYTHONPATH for the cluster's arrow module
PYTHONPATH=. venvs/tools/bin/pytest -q  # includes RQ0, v7, scoring, allocation, and causal-SFT coverage
python scripts/render_gallery.py --dataset aegislab --n 8 --contact-sheet
python scripts/selection_stats.py --dataset aegislab --n 30 --config prop12
python scripts/gen_case_manifest.py --check
```

`pyarrow` cannot be pip-installed on this cluster and `module load arrow` does
not reach a virtual-environment interpreter, so `env.sh` puts the arrow module's
site-packages on `PYTHONPATH`. Without it the AegisLab and AIOPS-2025 loaders
fail at construction. API credentials load from the sibling repo's `.env`.

**Rendering is cheap CPU work; inference is not.** Pre-render, then run inference
as a separate resumable job. Iterate at 20 and 100 cases; run all 480 only on
frozen configurations.

### After any renderer change

1. Add the config field *first* — a behaviour without a field cannot be ablated.
2. Render a gallery and **look at the images**, or hand them to the
   `render-reviewer` agent, which also runs a perception probe.
3. Check: nothing below 7pt, no clipped or overlapping text, colour carries
   meaning, nothing silently truncated without saying so, no leakage, under
   5 s/case.
4. Bump `RENDERER_VERSION` and re-record goldens — **never re-record a golden
   without looking at what changed** — then write the design decision.

### Helpers

Skills in `.claude/skills/`: **dashboard**, **smoke**, **experiment**,
**vlm-serve**, **baseline**, **agent-trace**, **devlog**, **status**,
**design-decision**. Agents in `.claude/agents/`: **render-reviewer** (vision QA;
use after every renderer change), **trajectory-analyst** (failure modes),
**results-analyst** (statistics and paper tables).

---

## 11. The honest summary

The pipeline works end to end and is reproducible. The corrected renderer,
formal equal-information comparison, topology qualification, scorer audit, two
SFT pilots, and nonredundant-allocation mechanism screen are complete.

The strongest registered result is negative: adding a dashboard to lossless
byte-identical text did not improve either open-weight model. The strongest new
positive clue is narrower: with byte-identical short summary text, adding the
image improved Gemma by +0.0694 MRR on 24 exposed development cases and harmed
Qwen by −0.0292. The Gemma effect is direct and integrity-clean, but post-hoc,
sparse, and architecture-specific. It is a reason to formulate a fresh test,
not permission to claim that images generally improve RCA.

The next high-value action is a research decision: either preregister an
architecture-interaction replication that transparently treats Gemma as a
post-result hypothesis, or reformulate VisionRCA around an independently
supported visual function such as efficient or interactive evidence navigation.
Continuing to search the existing reserve for a positive frozen-model number is
not a valid option.

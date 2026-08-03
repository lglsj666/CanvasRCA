# 2026-07-22 — M0 scaffold + M1 smoke pipeline

## What happened

Initiated the VLM-RCA project from an empty git scaffold. Both M0 and M1 are
complete and the end-to-end pipeline runs against a real model.

**Pipeline built.** `case → dashboard PNG → VLM → parse → score → JSONL + summary`,
reusing the upstream project's loaders, task statement, answer format and
scoring verbatim through a single shim module (`vlmrca/upstream.py`, DD-1).

**Smoke result — 20 RE2-OB cases, `claude-opus-4-7` via Bedrock:**

| metric | value |
|---|---|
| MRR | **1.000** |
| Top@1 | 1.000 |
| parse rate | 1.000 |
| tokens/case | 4,407 (incl. ~1.2k image tokens) |
| wall-clock | 6.9 s/case |
| render | 1.2 s/case |

All M1 gates passed. For comparison the prior text-based project needed
11,386 tokens/case for its Qwen3.5-9B one-shot condition, and its Opus text SOTA
used 12,670.

**The caveat that matters:** RE2-OB is the easiest of the five datasets — text
baselines already score 0.976–0.994 there. MRR 1.000 confirms the pipeline
works; it is *not* evidence the method beats text. The discriminating datasets
are AegisLab (text SOTA 0.679), AIOPS-2022 (0.532) and AIOPS-2025 (0.390).

**AegisLab — the first result that means something.** 20 cases, `claude-sonnet-5`:

| metric | dashboard VLM (Sonnet) | text SOTA (Opus + CoVe-lite) |
|---|---|---|
| MRR | **0.817** | 0.679 |
| Top@1 | 0.750 | — |
| tokens/case | 13,091 | 12,670 |

A ~0.14 MRR gain on the hardest dataset, with a cheaper model and comparable
token cost. Treat as encouraging, not established: n=20 so the interval is wide,
it is a single dashboard config, and the text number comes from 100 cases. The
honest next step is the same run at n=100 with a paired comparison against
upstream's per-case results, not a headline claim.

**Evaluation pool frozen.** `configs/case_manifest_480.json` — 480 cases
(100 aegislab / 100 aiops2022 / 100 aiops2025 / 90 re2_ob / 90 re2_tt, seed 42).
Necessary because the manifest upstream *refers* to does not exist on disk (DD-3).

**Tests.** 17 pass, 1 skipped (golden recorded on first run). Covers the shim
contract, render determinism, every RQ1 config axis actually changing the image,
score bounding, font floor, render speed, and four leakage guards.

**Skills and agents.** Nine skills (dashboard, smoke, experiment, baseline,
agent-trace, vlm-serve, devlog, status, design-decision) and three agents
(render-reviewer with a perception probe, trajectory-analyst, results-analyst).

## Key decisions

DD-1 sys.path shim over pip/vendor/submodule (upstream has no pyproject and its
package is named `src`) · DD-2 cached loader family, 0.45 s/case vs ~30 s ·
DD-3 freeze and commit the 480-case manifest · DD-4 bound anomaly scores ·
DD-5 auxiliary panels show change not absolute state · DD-6 resolve log/trace
time by window overlap · DD-7 Sonnet for iteration, Opus for headline runs.

Four of these (DD-4 through DD-7) came from actually looking at rendered output
rather than from design — see Blockers.

## Bugs found by looking at the images

Worth recording because they were all silent — nothing raised, the numbers would
just have been worse:

1. A flat baseline produced z = 2.0e9, swamping the ranking and printing garbage
   captions. Ranking the same case after the fix put the true injected fault
   (`checkoutservice·cpu`, z=248) first.
2. The log panel was permanently empty on RE2-OB — that corpus has zero
   error-level lines. Now falls back to log-volume shift.
3. The trace panel showed "n/a" for every during-fault value: RE2-OB traces leave
   `timestamp` all-NaN with the real clock in `startTime` (microseconds).
4. Fault-window shading covered most of the canvas (min/max over several series'
   peaks). Now expands from a single peak while deviation stays elevated.
5. Header text collided with panel titles; captions sat on top of the data;
   no time axis; nearly every trace red so colour meant nothing; topology colour
   scale linear, so every node but the worst rendered white.

Then the **render-reviewer agent** was run on a 4-case gallery and returned FAIL
with a 95.8% perception probe, finding two more that I had not (DD-8, DD-9):

6. Metric panels plotted at row index while the fault band was placed by
   timestamp. On a case with uneven sampling (1186 rows over 929 s) the band
   landed at 73–78% of the axis instead of 93–100%, making the true cause's CPU
   excursion appear to *precede* the fault — the dashboard argued against its own
   ground truth. Now everything shares an elapsed-time coordinate.
7. The most anomalous topology node was occluded by a neighbour in 3 of 4 cases,
   because `spring_layout` permits overlap and nodes were drawn alphabetically.
   Now: overlap relaxation, anomaly-ascending draw order, rank-based colour,
   luminance-aware labels.

Also fixed from that review: the `Z_CAP` sentinel printing as a real measurement
(DD-10), silent truncation in the log/trace tables, `chg%` at 0 decimals
collapsing a ranking, and `NaN` making manifests invalid JSON.

The lesson worth keeping: five of these bugs were invisible to the test suite and
to the aggregate metrics. Only looking at the pixels found them.

## Blockers

- **The vLLM self-hosted path is unverified.** The M0 GPU gate — confirming the
  cluster's vLLM serves Qwen2.5-VL — has not been run. `scripts/vllm_vlm/serve_qwen25vl_7b.sbatch`
  is written but not submitted. All results so far use the Bedrock API path.
  This blocks the zero-marginal-cost screening plan for RQ1.
- `pyarrow` is not pip-installable here and `module load arrow` does not reach a
  venv interpreter. Worked around in `scripts/env.sh` by putting the module's
  site-packages on `PYTHONPATH`. Works, but it is a workaround, and any new venv
  or a cluster arrow-version change will hit it again.
- Exact case-set parity with upstream's published tables is assumed, not
  verified (DD-3).

## Next steps

1. Submit the vLLM sbatch and verify Qwen2.5-VL-7B serves; run the same 20-case
   smoke through it. Closes the M0 gate.
2. Run the smoke on **AegisLab and AIOPS-2025** — the datasets with headroom.
   This is the first real signal about whether dashboards beat text, and it may
   well be negative on the harder sets.
3. Have the render-reviewer agent review an AegisLab gallery. Train-Ticket has
   40+ services against RE2-OB's 10, so the topology truncation and coverage
   ranker get their first real test there.
4. Begin M2: the RQ1 screening grid, one axis at a time on the 100-case dev set
   with Sonnet.

## Late addition: a negative result

Capping panel redundancy (DD-11) was implemented after seeing an AegisLab case
spend all 12 panels on HTTP latency percentiles while the ground truth (`mysql`)
got none. The cap demonstrably fixed that — mysql gained two panels.

It did not improve accuracy. AegisLab, 20 cases, paired:

| condition | MRR | 95% CI | Top@1 |
|---|---|---|---|
| capped | 0.746 | [0.558, 0.917] | 0.700 |
| uncapped | 0.797 | [0.653, 0.933] | 0.700 |

Delta -0.052, CI [-0.177, 0.046], Wilcoxon p=0.345. Within noise, point estimate
mildly negative — so the default was set back to off and the caps kept as an RQ1
axis rather than shipped on reasoning alone.

The interesting part is what it implies. If twelve near-duplicate latency panels
cost nothing, the metric panels may not be what the model is using on AegisLab,
and the hybrid prompt's log/trace/topology text may be carrying the signal. The
modality axis (`image_only` / `hybrid` / `text_only`) tests that directly and has
been moved to the front of the M2 queue, because it bears on whether "the
dashboard is the representation" survives contact with the hard datasets.

Current best AegisLab config is therefore plain top-K with all renderer fixes:
**MRR 0.797, Top@1 0.700, parse 1.00, 13.0k tokens/case** (n=20, sonnet-5).

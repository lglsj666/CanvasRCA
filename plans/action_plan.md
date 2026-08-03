# VLM-RCA action plan

Milestone sequence. Status as of 2026-07-26.

## M0 — Scaffold ✅ done

Repo structure, `vlmrca` package, upstream shim, frozen 480-case manifest,
environment script, tests, skills and agents.

GPU half of the M0 gate **closed 2026-07-23**: the cluster's vLLM serves the
open-weight panel over the OpenAI-compatible endpoint with images. See the
**vlm-serve** skill for the registry and the reproducible decoding recipe.

## M1 — Smoke pipeline ✅ done (API path)

`case → dashboard → VLM → parse → score`. 20 RE2-OB cases, `claude-opus-4-7`:
MRR 1.000, parse 1.000, 4.4k tokens/case, 6.9 s/case. All gates passed.

Read that result as "the pipeline is sound", not "the method wins" — RE2-OB is
saturated for text baselines too (0.994).

## M1.5 — Corrected open-weight bake-off ⬅ in flight (2026-07-26)

Not in the original sequence; added because the first bake-off could not support
the screening-model choice it was run to make. Three confounds and a gap: the
Gemma cells decoded stochastically while the Qwens were greedy, n=20 gave every
model overlapping intervals, "thinking hurts" generalised from a truncation
artifact and a dead server, and no run had ever omitted the image.

Now: AegisLab n=100, one decoding recipe, four arms per model
(`cov30`×{hybrid, text_only, image_only} plus `v0`×hybrid), behind a determinism
gate. Delivers three things M2 needs — the screening model (chosen on
`MRR(hybrid) − MRR(text_only)`, not raw MRR), the selector A/B, and the first
measurement of the config-effect sd that M2's adoption rule depends on.

**This contains a stop condition.** If `text_only ≈ hybrid` for both the open
models and Sonnet-5, the claim that the dashboard is the representation is in
question and no amount of grid work fixes it. Escalate before starting M2.

## M2 — RQ1: dashboard design grid

Screen one axis at a time from the v1 baseline on a stratified dev subset, with a
single fixed model. Adopt a level when its paired point ΔMRR ≥ +0.03 with Wilcoxon
p < 0.05/k and no sign reversal on the secondary dataset (report Cohen's d).
Record each outcome in `plans/design_decisions.md`, including the axes that changed
nothing.

*The +0.03 rule is only viable under deterministic decoding* — see
`docs/rq1_design.md` §5.1. Under the stochastic decoding every earlier run used,
it needed ~600 cases and would have returned "draw" for every level regardless of
what the dashboards did. Every comparison reports its own paired sd and implied
minimum detectable effect alongside ΔMRR.

Axes: KPI budget × ranker · layout · topology panel and labelling · annotation ·
resolution · single vs split image · modality (image-only / hybrid / text-only).

Pre-render with a batch job so inference is pure and resumable. Freeze the
winner as **v3**.

*Screen on AegisLab, not RE2-OB* — RE2-OB is saturated and cannot separate
configs. AIOPS-2025 (text SOTA 0.390) has not been run at all yet and should be.

*Run the modality axis first.* Capping panel redundancy changed AegisLab MRR by
-0.05 (CI spanning zero) even though it demonstrably put the true root cause on
the dashboard where it previously had no panel. That is a hint the metric panels
may not be load-bearing there, and the hybrid prompt's log/trace/topology text is
doing the work. `image_only` vs `hybrid` vs `text_only` tests it directly and
bears on the project's central claim, so it should not wait behind the other
axes.

## M3 — RQ2: agentic loop

Tools: `zoom_panel`, `expand_service`, `traverse`, `show_logs`, `show_traces`,
`rerender`, `final_answer`. Controllers: C0 one-shot (control) · C1 fixed
pipeline · C2 free agent (max 8 turns) · C3 ZoomEye-style tree search only if C2
proves unstable. Keep the global dashboard plus the two most recent tool images
in context; older images collapse to a one-line summary; hard per-case token cap
forces an answer. Compare on the dev set, freeze the best.

## M4 — RQ3: model panel

Frozen one-shot and agentic configs across: Qwen3.5-4B/9B, Qwen3.6-27B,
Gemma-4-E4B/12B/26B-A4B (self-hosted); Claude Opus/Sonnet, GPT-5.4,
Gemini 3.1 Pro (API). The panel is what M1.5 actually serves — the earlier list
(Qwen2.5-VL-72B, InternVL3-38B) named models that were never served.
Ladder: L0-20 parse gate → L1-100 iteration → L2-480 frozen only.
Budget ~$200–400: one-shot on 480 for the whole panel; agentic on 480 for the
best 1–2 API models plus self-hosted.

*API models cannot be replicated.* Per DD-14, Bedrock rejects `temperature` for
the Claude 5 generation, so those arms carry an irreducible ±0.050 MRR band at
n=100. Report it with every API number; magnitude claims belong to the
deterministic self-hosted arms.

## M5 — RQ4: ablations + paper

One config toggle per row on the frozen pipeline, 480 cases: topology off ·
anomaly colouring off · shading off · direct labels → legend · hybrid → image
only · image off (cite the prior text row, no re-run) · ranker → random-K ·
loop off · zoom depth · log/trace tools off.

Report ΔMRR, paired Wilcoxon, Cohen's d, and **per-fault-type MRR** —
VisualTimeAnomaly predicts images help sustained/range faults and hurt point
spikes, and that split is the paper's most interesting figure if it holds.

## Standing risks

- Dense AegisLab topology (40+ services) versus RE2-OB's 10 — the topology
  truncation and coverage ranker are untested at that scale.
- Saturated RE2-OB/TT can inflate any pooled number; always report per-dataset.
- Renderer regressions are silent; the render-reviewer agent and golden hashes
  are the only guard. Four text-budget defects on 2026-07-26 — one of which broke
  the Service index in 95 of 100 cases — passed the whole test suite and were
  found only by looking at the images.
- Upstream repo drift (pinned, warned on, not prevented). Note the pin is
  currently a no-op: `configs/upstream_pin.yaml` does not exist, so
  `check_upstream_pin()` silently passes.
- Every result committed before 2026-07-26 was produced under stochastic
  decoding at `RENDERER_VERSION` 1. None is reproducible as recorded; treat the
  0.797 AegisLab headline as provisional until it is re-run.

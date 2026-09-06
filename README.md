# CanvasRCA

**Vision-language root-cause analysis over rendered microservice telemetry
dashboards.**

CanvasRCA measures how the visual organization used by human SREs—metric
curves, trace summaries, logs, and directed service topology—changes root-cause
analysis, attention allocation, and token cost relative to semantically equal
text. The study has no precommitted positive
direction. Labels, source case IDs, fault types, absolute injection times,
dataset names, paths, and natural entity names are evaluator-private.

The active study is **RQ2**, a clean dashboard-design study built on the
completed RQ1.1 empirical representation study. Historical RQ1/RQ1.1 results
and reports remain audit evidence; RQ2 does not rewrite or reuse their model
outputs.

## RQ1.1 experiments

All experiments use the single canonical `CanvasRCAProcessedPublicCaseV3` loader,
the full frozen 480-case target roster after V3 regeneration, the unified scorer
and VLM client, and a byte-inherited renderer-v14 snapshot under
`RQs/RQ1_1/src/renderer/`.

| Experiment | Design | Endpoint |
|---|---|---|
| `direct_rca` | One call over a complete 16-cell M/R/L/G text/visual factorial plus C, S, and H controls | MRR, AC@1/3/5, AVG@3/5, grounding, attention, tokens, request/runtime cost |
| `direct_qa` | Matched T/V/S/PathV/ContextV L1–L4 M/R/L/G questions | Complete-chain, step, prefix, attention, and QA–RCA relation |
| `one_stage_counterfactual_rca` | Post-RQ2 factual/targeted/placebo/neutral renderer-v14 image intervention | CVI, rank movement, MRR, grounding, attention |

The main RCA factorial contains all 16 combinations of M/R/L/G as text or
visual. Its anchors and controls are:

- `T`: all evidence as natural-language text.
- `C`: the same facts as concise typed structured text; it controls for prose
  verbosity and nonvisual compression.
- `V`: the full real telemetry dashboard.
- `S`: an exact screenshot of the T incident fragment.
- `LV`: logs visual; metrics, traces, and topology text.
- `MV`: metrics visual; traces, logs, and topology text.
- `TCV`: traces visual; metrics, logs, and topology text.
- `TPV`: topology visual; metrics, traces, and logs text.
- `V_MR` … `V_RLG`: every registered two- and three-region visual subset.
- `H`: complete dashboard A followed by byte-identical T evidence B.

Mixed-arm images are source-pixel crops from V. A fact appears exactly once in
each arm. Every service, node, and pod uses a fresh case-local numeric identity
(three, four, and five digits respectively); only the private evaluator can
map it back.

Logs use `DenumReadableLogGraphV1`, a readable adaptation of Denum's numeric
token parsing and repeated-structure separation. It preserves diagnostic
numbers, templates, relative bins, severity, and multiplicity as text/graph
data. CanvasRCA does not create or decode Denum binary output. The third-party
ReAct and Denum snapshots under `packages/` are pinned method references, not
runtime dependencies.

The supplied SIRCL artifact's locked `SIRCL*` prompt/analyzer source is also
preserved byte-for-byte under `packages/SIRCL_selected_reference/`. RQ1.1
adapts its MET-Z/TRC-L/LOG-R, M→R→L→G, U-BASE, VERIFY discipline to the
label-blind relative-window and numeric-ID contract. Renderer-v14 and the text
serializer compute MET-Z pre/current distribution statistics, TRC-L
exclusive-latency/count log-fold ranks, and LOG-R rate shifts from the same
public trace-derived split. The reference code is not imported at runtime
because its split uses private `case.timestamp`. The supplied paper's macro
MRR 0.596 identifies the reference selection but is only a contextual
post-run diagnostic here; CanvasRCA differs in roster, anonymity, evidence,
candidate universe, model, and scorer. Neither model's vLLM recipe changed.

Every RQ1.1 model call records attention from the final prompt query and the
generated `services`/`values` answer-field tokens to prior prompt keys at the
first registered full-attention layer.
Text attention is mapped to semantic prompt spans; visual calls also persist
raw grids, image overlays, and absolute all-prompt mass for the dashboard header
band and M/R/L/G regions. Visual records also include value norms,
attention-weighted value norms, first-patch rank, and peak-to-median ratios so a
positional sink candidate is not mistaken for semantic evidence use. Regional
attention is compared as mass per exact pixel area, normalized by the mean
density over actual M/R/L/G visual-evidence regions; raw mass is retained only
for conservation and total-allocation reporting. These
diagnostics add no model call and do not alter generation. They are
correlational descriptions, not causal explanations.

## RQ2 experiments

RQ2 reuses all 300 RQ1.1 headline incidents after V3 regeneration so
dashboard-design changes can be paired against the established empirical
sample. They are repartitioned into 60 development, 150 independent, and 90
downstream-lock cases. A fourth deterministic-tool study uses all 480 frozen
RQ1.1 identities, with RE2 reported separately. This is
repeated-exposed design evaluation, not a fresh heldout confirmation.

RQ2 represents incident information as selectable `EvidenceCardV1` modules.
Every selected card becomes exactly one equal-fact visual `SilhouetteV1` with a
registered integer footprint, and complete silhouettes are packed without
overlap on an `m×n` square grid. The manifest preserves
`fact → card → silhouette → pixel bbox`, so information selection is separable
from visual encoding and placement.

RQ2 runs four one-stage RCA experiments: a 48-program development design panel over encoding,
footprints, deterministic packing, ordering, grid shape, cell resolution,
gutter and skin (followed by 16 frozen confirmation programs); fourteen full,
budgeted, and dense evidence-card policies with matched
Canvas/Text twins; and a locked transfer comparison among full text,
pixel-text, the RQ1.1 parent dashboard, the selected fixed design, a
non-semantic skin perturbation, selected content twins, and equal-fact compact
text controls at full, selected, and dense content; and four deterministic
public-evidence selectors crossed with exact-fact Text/Canvas twins. Registered
resolution/spacing curves plus mixed maximin legal programs replace both an
infeasible Cartesian grid and the superseded continuous region-weight design.

RQ2 inherits RQ1.1's local vLLM runtime, request adapter, unified client/scorer
and frozen 27B checkpoints. It owns a local, hash-recorded minimal adaptation
of the same selected SIRCL* one-stage RCA prompt used by RQ1.1, so dashboard
comparisons do not also change the diagnostic method. Only the variable
evidence-card/design-control wording differs. RQ2 separately owns the visual
grammar that explains every registered encoding and layout. The common task
text is fixed across RQ2 designs; text twins never receive dashboard-only
instructions. Packed QA/perception is abandoned in RQ2:
its code is retained for audit, but it is absent from active smokes, formal
queues, selection, verification and claims. RCA attention remains active.

The prior RQ2 implementation, roster, contracts, and results are superseded and
are not authorities for this clean lineage. The full protocol is under
`RQs/RQ2/descriptions/`.

RQ1.1 and RQ2 record client-observed TTFT, decode duration, TPOT, receiver
end-to-end latency, output-token rate, run throughput/goodput, peak VRAM and
KV-cache usage, utilization-weighted GPU-seconds, sampled energy, and
preparation/render timing. Prefill is deliberately reported as unavailable
because the client cannot separate it from queue and transport time. Hardware
timings are operational and only comparable within a matched runtime; token
counts remain the portable cost measure.

## Data and evaluation

The V3 successor targets all 480 frozen cases:

- AegisLab: 100
- AIOPS-2022: 100
- AIOPS-2025: 100
- RE2-OB: 90 (saturated reference, reported separately)
- RE2-TT: 90 (OOD, reported separately)

Only the first 300 cases form the headline inferential set. RCA uses ranked
top-five JSON and the unified granularity-aware scorer. MRR is primary; paired
representation claims use Pratt-zero Wilcoxon tests, paired Cohen's dz, Holm
correction, and a minimum practical MRR difference of 0.05. Confidence
intervals are not reported under the project contract.

## Repository layout

```text
configs/                    three unified YAML contract families
src/unified_scripts/        raw processing plus the three reusable contract implementations
src/vlmrca/                 shared client, evidence, scoring, and pipeline code
src/cli/                    shared Python command-line entry points
scripts/                    shared shell entry points only
RQs/RQ1/                    protected historical RQ1 code and formal results
RQs/RQ1_1/                  completed empirical-study configs, code, and results
RQs/RQ1_1/src/renderer/     renderer-v14 snapshot with package-local imports
RQs/RQ2/                    active dashboard-design study and RQ2-local renderer
packages/                   pinned method-reference source snapshots
plans/design_decisions.md   consolidated project decisions
devlog/CONSOLIDATED.md      compact chronological implementation/experiment log
docs/                       project reports
```

There is deliberately no global renderer. Later RQs must copy or explicitly
inherit the RQ1.1 snapshot unless the user authorizes a dashboard-design
experiment.

## Unified inference configuration

The active models are Qwen3.8-27B and Gemma-4-26B-A4B-it. Both use unquantized
BF16, seed 42, temperature 1.0, top-p 0.95, a 40,960-token context, a
16,384-token server output ceiling, an 8,192-token RQ adapter, thinking off,
prefix caching off, xgrammar structured JSON, and `max_num_seqs=256`.

- Qwen3.8 uses its native image processor and chunked prefill off.
- Gemma uses `max_soft_tokens=1120` and chunked prefill on.
- Local WSL uses `gpu_memory_utilization=0.75`, the inference environment under
  `/home/lglsj/CanvasRCA/venvs/infer/`, and checkpoints under
  `/home/lglsj/CanvasRCA/models/`.

All successor work runs on local WSL. The repository's `_nibi` suffix and Nibi
launchers are historical provenance only. New preparation, inference,
analysis, SFT and RL must not use `sbatch` or another Slurm entry point.

The future Dashboard Composer is fixed to the locally downloaded
`Qwen3.5-9B` checkpoint at
`/home/lglsj/Downloads/self-evolving-RCA-updated/models/Qwen3.5-9B/`. RQ2 does
not train it: RQ2 exports typed, replayable tool traces and contribution
anchors. Later tool-grounding SFT teaches only legal dashboard-program calls;
later outcome-grounded RL optimizes a frozen 27B RCA actor under a token budget.

These model-specific processor differences are official frozen recipes, not a
claim of identical visual-token counts. Actual text and image tokens are
recorded for every call.

Inspect local server arguments without loading a model:

```bash
source scripts/env_local.sh
python -m unified_scripts.vllm_inference qwen3.8-27b --format argv
python -m unified_scripts.vllm_inference gemma-4-26b-a4b --format argv
```

Launch the local profile:

```bash
source scripts/env_local.sh
python -m unified_scripts.vllm_inference qwen3.8-27b --format argv
scripts/vllm_vlm/serve_canvasrca_local.sh qwen3.8-27b
```

Prepare the canonical V3 corpus and RQ1.1 artifacts locally:

```bash
RQs/RQ1_1/scripts/prepare_local.sh rq1_1_formal_local_v1
```

## RQ1.1 workflow

Static qualification:

```bash
source scripts/env.sh
RQs/RQ1_1/scripts/run.sh static
```

After the V3 corpus and 480-case successor roster are generated, prepare the
canonical run locally:

```bash
RQs/RQ1_1/scripts/prepare_local.sh rq1_1_formal_local_v1
```

Each experiment has exactly one bounded smoke. Qwen and Gemma run sequentially
and share at most 18 calls and one 600-second total timeout. Formal execution remains
disabled until both two-model experiment smokes pass, conversations are
inspected, and the v1 contract is frozen.

After freeze, run experiments in this order:

1. `direct_rca`
2. `direct_qa`

Within each experiment, finish Qwen3.8 before Gemma. `multi_stage_rca` is
retained only as abandoned future-work source and is not queued. All long jobs are
background, resumable, and verified before findings are written.
The separately versioned `one_stage_counterfactual_rca` successor remains
qualification-pending until RQ2 completes; it is tested and run afterward in a
new namespace and never imports an RQ2 renderer or design.

See [Codex.md](Codex.md) for the authoritative rules and
[RQ1.1 experiments](RQs/RQ1_1/descriptions/RQ1_1_experiments.md) for the full
protocol.

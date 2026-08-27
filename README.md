# CanvasRCA

**Vision-language root-cause analysis over rendered microservice telemetry
dashboards.**

CanvasRCA measures how the visual organization used by human SREs—metric
curves, trace summaries, logs, and directed service topology—changes root-cause
analysis, cross-region reasoning, attention allocation, tool use, and cost
relative to semantically equal text. The study has no precommitted positive
direction. Labels, source case IDs, fault types, absolute injection times,
dataset names, paths, and natural entity names are evaluator-private.

The active study is **RQ1.1**, a clean successor to RQ1. Historical RQ1 formal
results and the existing `docs/RQ1_report.md` are preserved as audit evidence;
RQ1.1 never rewrites or reuses their prepared inputs or inference records.

## RQ1.1 experiments

All experiments use the single Nibi `CanvasRCAProcessedPublicCaseV2` loader,
the same 469-case roster, the unified scorer and VLM client, and a byte-inherited
renderer-v13 snapshot under `RQs/RQ1_1/src/renderer/`.

| Experiment | Design | Endpoint |
|---|---|---|
| `direct_qa` | One real dashboard; one deterministic L1/L2/L3/L4 M/R/L/G question per case | Complete-chain, step, and prefix accuracy |
| `direct_rca` | One call over seven equal-fact representations | MRR, AC@1/3/5, AVG@3/5, tokens |
| `multi_stage_rca` | Three fixed ReAct-like steps; planner → host tool → ranking update | RCA plus tool-use and interaction cost |

The seven RCA representations are:

- `T`: all evidence as natural-language text.
- `V`: the full real telemetry dashboard.
- `S`: an exact screenshot of the T incident fragment.
- `LV`: logs visual; metrics, traces, and topology text.
- `MV`: metrics visual; traces, logs, and topology text.
- `TCV`: traces visual; metrics, logs, and topology text.
- `TPV`: topology visual; metrics, traces, and logs text.

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

Every RQ1.1 model call records same-prefill attention from the final prompt
query to all prior prompt keys at the first registered full-attention layer.
Text attention is mapped to semantic prompt spans; visual calls also persist
raw grids, image overlays, and absolute all-prompt mass for the dashboard header
band and M/R/L/G regions. Visual records also include value norms,
attention-weighted value norms, first-patch rank, and peak-to-median ratios so a
positional sink candidate is not mistaken for semantic evidence use. These
diagnostics add no model call and do not alter generation. They are
correlational descriptions, not causal explanations.

## Data and evaluation

The active roster contains 469 cases:

- AegisLab: 96
- AIOPS-2022: 100
- AIOPS-2025: 93
- RE2-OB: 90 (saturated reference, reported separately)
- RE2-TT: 90 (OOD, reported separately)

Only the first 289 cases form the headline inferential set. RCA uses ranked
top-five JSON and the unified granularity-aware scorer. MRR is primary; paired
representation claims use Pratt-zero Wilcoxon tests, paired Cohen's dz, Holm
correction, and a minimum practical MRR difference of 0.05. Confidence
intervals are not reported under the project contract.

## Repository layout

```text
configs/                    three unified contract families; explicit deployment profiles
src/unified_scripts/        their reusable Python implementations
src/vlmrca/                 shared client, evidence, scoring, and pipeline code
src/cli/                    shared Python command-line entry points
scripts/                    shared shell entry points only
RQs/RQ1/                    protected historical RQ1 code and formal results
RQs/RQ1_1/                  active RQ1.1 configs, docs, code, scripts, results
RQs/RQ1_1/src/renderer/     renderer-v13 snapshot with package-local imports
packages/                   pinned method-reference source snapshots
plans/design_decisions.md   consolidated project decisions
devlog/                     dated implementation and experiment logs
docs/                       project reports
```

There is deliberately no global renderer. Later RQs must copy or explicitly
inherit the RQ1.1 snapshot unless the user authorizes a dashboard-design
experiment.

## Unified inference configuration

The active models are Qwen3.8-27B and Gemma-4-26B-A4B-it. Both use unquantized
BF16, seed 42, temperature 1.0, top-p 0.95, a 40,960-token context, a
16,384-token server output ceiling, an 8,192-token RQ adapter, thinking off,
prefix caching off, xgrammar structured JSON, and `max_num_seqs=128`.

- Qwen3.8 uses its native image processor and chunked prefill off.
- Gemma uses `max_soft_tokens=1120` and chunked prefill on.
- Nibi omits `gpu_memory_utilization`; the H100 allocation supplies the
  physical memory boundary.
- Local WSL uses `gpu_memory_utilization=0.65`, the inference environment under
  `/home/lglsj/CanvasRCA/venvs/infer/`, and checkpoints under
  `/home/lglsj/CanvasRCA/models/`.

The Nibi and local profiles differ only in deployment paths and the operational
VRAM fraction. A static parity check rejects changes to any scientific or
model-specific inference field. Local WSL runs directly and never uses
`sbatch`; Slurm submission scripts are Nibi-only.

These model-specific processor differences are official frozen recipes, not a
claim of identical visual-token counts. Actual text and image tokens are
recorded for every call.

Inspect server arguments without loading a model:

```bash
source scripts/env.sh
python -m unified_scripts.vllm_inference qwen3.8-27b --format argv
python -m unified_scripts.vllm_inference gemma-4-26b-a4b --format argv
```

Inspect or launch the local profile without changing the Nibi profile:

```bash
source scripts/env_local.sh
python -m unified_scripts.vllm_inference qwen3.8-27b --format argv
scripts/vllm_vlm/serve_canvasrca_local.sh qwen3.8-27b
```

Prepare the canonical V2 corpus and RQ1.1 artifacts locally without Slurm:

```bash
RQs/RQ1_1/scripts/prepare_local.sh rq1_1_formal_local_v1
```

## RQ1.1 workflow

Static qualification:

```bash
source scripts/env.sh
RQs/RQ1_1/scripts/run.sh static
```

Prepare the canonical 469-case run into 24 shards:

```bash
sbatch RQs/RQ1_1/scripts/prepare_nibi.sh rq1_1_formal_v1
```

Each experiment has exactly one bounded smoke. Qwen and Gemma run sequentially
and share at most 18 calls and one 600-second total timeout. Formal execution remains
disabled until all six model-experiment smoke phases pass, conversations are
inspected, and the v1 contract is frozen.

After freeze, run experiments in this order:

1. `direct_qa`
2. `direct_rca`
3. `multi_stage_rca`

Within each experiment, finish Qwen3.8 before Gemma. All long jobs are
background, resumable, and verified before findings are written.

See [Codex.md](Codex.md) for the authoritative rules and
[RQ1.1 experiments](RQs/RQ1_1/descriptions/RQ1_1_experiments.md) for the full
protocol.

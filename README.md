# CanvasRCA

**Vision-language root-cause analysis over rendered microservice telemetry
dashboards.**

CanvasRCA studies a simple but under-tested idea: the dashboard is the
representation. Human SREs diagnose incidents by connecting patterns across
metric charts, logs, traces, and service topology. This project tests whether a
VLM can use the same visual organization to improve ranked root-cause analysis
over text-only and flat structured evidence under controlled information and
compute.

Every visual request also records a same-prefill, model-internal
Q-to-visual-key attention sidecar and image-space heatmap. This diagnostic adds
no model call, does not change generation, and is interpreted as correlational
only; controlled visual counterfactuals remain the causal test.

The repository is currently prepared for deployment on the Digital Research
Alliance Nibi cluster. The Nibi refactor and CPU-only static qualification are
complete; no model inference, smoke, gate, training, or GPU experiment has been
run from this worktree.

## Research workflow

```mermaid
flowchart LR
    D[Read-only processed incident] --> S[Unified deterministic split]
    S --> E[Label-blind evidence packet]
    E --> T[Text / flat / visual / hybrid representation]
    T --> V[One- or two-stage VLM agent]
    V --> P[Private ID mapping]
    P --> C[Unified RCA scorer]
    C --> R[Paired RQ results and findings]
```

Labels, raw case identities, fault types, absolute injection times, dataset
names, and source paths are evaluator-private. Every compared representation is
compiled from the same incident fact inventory.

## Current research questions

### RQ1 — Representation value

> Under equal-information and equal-compute conditions, does visual–text,
> topology-aware observability improve VLM-based root-cause ranking over
> text-only and flat structured representations, and which observability
> operations exhibit stable modality complementarity?

RQ1 contains seven related but distinct experiments. All seven receive final Nibi
reruns on the same eligible evaluation roster:

| Experiment | Purpose | Scientific endpoint |
|---|---|---|
| `legacy_q9` | Direct metric, log, trace, and topology reading | Perception mechanism only |
| `cross_region` | Level-1/2/3 joins across M/L/R/G regions | Cross-region mechanism only |
| `typed_two_stage` | Measure evidence extraction and handoff attrition | Agent mechanism only |
| `direct_rca` | Directly rank roots from T/F/V/P/H/R in one call | One-stage RCA reference |
| `matched_rca` | Compare T/F/V/P/H/R equal-fact representations | Ranked RCA: MRR and AC/AVG@K |
| `visual_counterfactual_rca` | Test whether controlled image semantics causally move evidence and rankings | Visual influence plus RCA |
| `ledger_handoff_rca` | Test whether visual evidence survives the Stage-1/Stage-2 boundary | Handoff mechanism plus RCA |

The six end-to-end RCA arms are:

- **T:** complete deterministic natural-language evidence;
- **F:** the same facts as stable flat JSONL records;
- **V:** the real renderer-v12 telemetry dashboard with metric curves and the
  registered topology/log/trace panels;
- **P:** the T natural-language evidence divided into M/R/L/G and drawn as pixels (a text-on-canvas
  pseudo-dashboard, not a telemetry dashboard);
- **H:** strict image-first `A+B`, where A is exactly V and B is byte-identical
  to T;
- **R:** metrics and topology visually, with logs and traces supplied as text.

The current v16 prompt contract follows locked SIRCL* ordering for every
text-bearing transport: metrics, traces, logs, then topology. RCA prompts add
shared field semantics, origin-versus-symptom guidance, and an internal
`INITIAL → VERIFY → REVISE` check while preserving the frozen final JSON.
Two-stage RCA uses at most 16 compact visible record keys and four metric bins
per metric key; the host binds exact facts instead of asking the model to
retranscribe full arrays or nullable identity tuples. Q&A prompts explain fields only, and H remains strict
image-first A+B.

The frozen project evaluation roster has 469 eligible cases after excluding 11
already-invalid cases without replacement: 96 AegisLab, 100 AIOPS-2022, 93
AIOPS-2025, 90 RE2-OB, and 90 RE2-TT. Headline inference uses only the 289
primary-dataset cases; the saturated RE2-OB and final-OOD RE2-TT slices are
reported separately. Historical local mechanism evidence remains context, not
the final Nibi result. See
[RQ1 statement](RQs/RQ1/descriptions/RQ1_statement.md),
[experiments](RQs/RQ1/descriptions/RQ1_experiments.md),
[road map](RQs/RQ1/descriptions/RQ1_roadMap.md), and
[findings](RQs/RQ1/findings/).

### RQ2 — Dashboard design effects

RQ2 studies how metric encoding, graph encoding, cross-source arrangement, and
entity ordering affect RCA, grounding, robustness, and cost. Its current
implementation is a complete two-level, four-factor design with 16 cells and
eight matched anchors per factor. The static contract is ready; no qualified
model-outcome result exists yet. See [RQ2 statement](RQs/RQ2/descriptions/RQ2_statement.md)
and [experiments](RQs/RQ2/descriptions/RQ2_experiments.md).

## Repository layout

```text
configs/                    exactly three unified project configs
src/unified_scripts/        extensible implementations of those contracts
src/vlmrca/                 shared client, evaluation, and training
src/cli/                    shared Python command-line entry points
scripts/                    shared shell entry points only
RQs/RQx/configs/            RQ-specific configuration only
RQs/RQx/descriptions/       statement, experiments, and qualitative road map
RQs/RQx/findings/           one findings document per experiment
RQs/RQx/scripts/            RQ shell triggers only
RQs/RQx/src/                five compact functional modules plus __init__.py
RQs/RQ1/src/renderer/       provisional RQ1-owned renderer-v12 snapshot
RQs/RQx/results/            generated experiment artifacts
requirements/               Nibi dependency sets
```

RQ1 was reduced from roughly 25,000 lines of duplicated experiment code to
1,286 lines across its five functional Python modules. Shared inference,
segmentation, scoring, client, and artifact behavior is reused
instead of copied into each experiment.

There is deliberately no project-global renderer while dashboard design is an
open research variable. RQ1 owns the provisional renderer-v12 snapshot; later
RQs must copy or explicitly inherit it unchanged unless the user authorizes a
dashboard-design experiment.

The complete directory and integrity rules are authoritative in
[Codex.md](Codex.md).

## Unified global contracts

The root `configs/` directory contains exactly three YAML files:

| Contract | Config | Reusable implementation |
|---|---|---|
| vLLM inference | [`configs/vllm_inference.yaml`](configs/vllm_inference.yaml) | [`src/unified_scripts/vllm_inference.py`](src/unified_scripts/vllm_inference.py) |
| Dataset segmentation | [`configs/dataset_segmentation.yaml`](configs/dataset_segmentation.yaml) | [`src/unified_scripts/dataset_segmentation.py`](src/unified_scripts/dataset_segmentation.py) |
| RCA scoring | [`configs/rca_scorer.yaml`](configs/rca_scorer.yaml) | [`src/unified_scripts/rca_scorer.py`](src/unified_scripts/rca_scorer.py) |

These classes are frozen global bases but remain extensible through named,
versioned, hash-recorded subclasses or adapter mappings. An RQ may reference or
adapt a contract; it may not silently fork a second unified implementation.

## Registered inference configuration

Both supported models use unquantized BF16, seed 42, temperature 1.0, top-p
0.95, a 32,768-token context, a 16,384-token output ceiling, thinking disabled,
prefix caching disabled, and `max_num_seqs=128`. RQ1 uniformly requests at
most 8,192 output tokens through its context-safe adapter.

- **Qwen3.6-27B:** native image-processor policy, no CanvasRCA pixel-budget
  override, chunked prefill disabled.
- **Gemma-4-26B-A4B-it:** `max_soft_tokens=1120`, xgrammar structured output,
  chunked prefill enabled.

For Nibi, `gpu_memory_utilization` is `null`, so the canonical launcher omits
`--gpu-memory-utilization`. This removes the project-imposed VRAM fraction cap;
it does not remove the physical limits of the H100 allocation, model, context,
or vLLM runtime.

Inspect the effective server arguments without starting a model:

```bash
python -m unified_scripts.vllm_inference qwen3.6-27b --format argv
python -m unified_scripts.vllm_inference gemma-4-26b-a4b --format argv
```

## Static development setup

From the repository root:

```bash
source scripts/env.sh
scripts/static_checks.sh
```

The static entry point checks Python syntax, directory constraints, global
configuration expansion, scorer definitions, factorial cells, numeric-ID
rules, and shell-visible contracts. It makes zero LLM/VLM calls.

The latest WSL qualification passed with:

- exactly three root configs;
- only Python source under `src/`;
- only shell files under root and RQ `scripts/`;
- all 57 Python files parsed;
- RQ1 and RQ2 static contracts passed;
- fatal Ruff, new-module unused-import, shell syntax, packaging metadata, and
  diff-whitespace checks passed.

## Nibi setup

The build is Lmod- and Alliance-wheelhouse-first:

```bash
scripts/build_nibi.sh base
scripts/build_nibi.sh inference
source scripts/env.sh
```

The two build modes use separate `.venv-base` and `.venv-inference`
environments. CPU preparation and rendering use the base environment; Slurm
model jobs select the inference environment and consume pre-rendered artifacts.

The wrapper loads the Nibi module hierarchy (`StdEnv/2023`, `gcc/12.3`,
`python/3.11.5`, `arrow/25.0.0`, and `opencv/4.13.0` plus `cuda/12.6` for
inference) before creating the isolated environment. Slurm entry points load
the same stack. Module overrides are available through the
`CANVASRCA_*_MODULE` environment variables and must be recorded in a heavy-run
contract.

If the exact compiled inference stack is not available from the Alliance
wheelhouse, stage a compatible bundle and set:

```bash
export CANVASRCA_WHEEL_DIR=wheelhouse
scripts/build_nibi.sh inference
```

Deployment paths can be supplied without editing committed files:

```bash
export CANVASRCA_PROCESSED_ROOT=dataset/processed
export CANVASRCA_QWEN_MODEL=models/Qwen3.6-27B
export CANVASRCA_GEMMA_MODEL=models/gemma-4-26B-A4B-it
export RL_SLM_RCA_ROOT=../self-evolving-RCA-rwrl
```

See the [Nibi preparation guide](docs/nibi_preparation.md) for wheelhouse,
Apptainer, Slurm, model/data staging, and deployment details.

## Preparing a registered run

Generate deterministic segmentation artifacts after the read-only processed
corpus is available:

```bash
# Model-safe manifest.
scripts/segment_dataset.sh \
  --out artifacts/segmentation/public_manifest.json

# Physically separate evaluator-private manifest with source case IDs.
scripts/segment_dataset.sh --private \
  --out artifacts/segmentation/private_manifest.json
```

Freeze the effective serving implementation:

```bash
scripts/freeze_vllm_contract.sh
```

Heavy work must run through Slurm rather than a login node. The RQ1 H100 job
template is [`RQs/RQ1/scripts/submit_nibi.sh`](RQs/RQ1/scripts/submit_nibi.sh).
Long execution remains disabled in the committed RQ configs; a deployment
agent must first freeze rosters and a new result ID, attest the live server,
enable the registered successor config, and pass the bounded smoke.

## Scientific integrity

The most important rules are:

1. The renderer never sees root labels or absolute injection times.
2. Compared arms contain identical incident facts, candidates, precision,
   bins, missingness, edges, and legends.
3. Hybrid evidence is strictly `A+B` or `B+A` with one frozen order.
4. Unknown output IDs are scored as misses and retain their original rank.
5. End-to-end RCA uses ranked top-five JSON and the unified scorer.
6. MRR is primary; AC@1/3/5 and cumulative AVG@3/5 are also recorded.
7. Representation claims use paired cases, Pratt-zero Wilcoxon tests, paired
   Cohen's dz, and per-dataset/per-fault reporting.
8. Perception and agent-output changes explain mechanisms but cannot replace an
   RCA accuracy result.
9. A smoke is capped at 18 aggregate model calls and 600 seconds; a
   model-calling gate is capped at 36 calls and 1,200 seconds.
10. Partial formal outcomes cannot be used to tune prompts, rosters, stopping,
    or model selection.

See [Codex.md](Codex.md) for the complete authoritative rules.

## Project status and handoff

- **Phase:** Nibi-portable implementation and static qualification complete.
- **Strongest current evidence:** architecture-dependent perception and
  cross-region mechanism results; no current end-to-end RQ1 RCA conclusion.
- **RQ1 next step:** deploy exact dependencies/data/models, freeze the existing
  469-case eligible roster and contracts, run bounded qualification, then rerun
  all seven registered experiments under new result IDs.
- **RQ2 next step:** begin only after RQ1 produces a verified representation
  decision suitable for controlled dashboard-design experiments.
- **Current blocker:** Nibi deployment artifacts and live qualification have not
  yet been created.

Implementation details and caveats are recorded in the
[2026-08-09 static handoff](devlog/2026-08-09_nibi_refactor_static_handoff.md);
project-wide rationale is in
[DD-43](plans/design_decisions.md#dd-43-adopt-a-compact-nibi-portable-source-and-global-contract-layout).

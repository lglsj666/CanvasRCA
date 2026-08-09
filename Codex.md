# CanvasRCA Project Rules

CanvasRCA studies whether vision-language models can diagnose microservice
incidents from rendered telemetry dashboards. The dashboard is an experimental
representation, not decoration. Scientific claims must distinguish visual
readability, agent-output influence, and final root-cause ranking.

This file is the single authoritative project-guidance document. `AGENTS.md`
must remain a symbolic link to this file.

## Portable project root

All paths in code, configuration, documentation, contracts, and commands must
be project-relative or supplied through environment variables. Never commit a
user home directory, workstation path, cluster account, or site-specific
absolute path.

The repository root is discovered from the current Git worktree. The standard
environment is loaded with:

```bash
source scripts/env.sh
```

`CANVASRCA_ROOT`, `CANVASRCA_ENV`, `CANVASRCA_PROCESSED_ROOT`,
`CANVASRCA_QWEN_MODEL`, `CANVASRCA_GEMMA_MODEL`, and `RL_SLM_RCA_ROOT` may
override deployment locations. An override is runtime metadata and must be
recorded in a heavy-run contract.

## Canonical layout

```text
configs/                    exactly three global unified YAML configs
src/unified_scripts/        three reusable global Python implementations
src/vlmrca/                 shared main-pipeline Python package
src/cli/                    shared project-wide Python entry points
scripts/                    shared shell entry points only
RQs/RQx/configs/            RQ-specific configuration only
RQs/RQx/descriptions/       exactly three canonical RQ documents
RQs/RQx/findings/           one finding document per experiment
RQs/RQx/scripts/            RQ-specific shell entry points only
RQs/RQx/src/                compact RQ-specific Python package
RQs/RQx/results/            RQ-specific generated artifacts
requirements/               Nibi dependency sets
plans/design_decisions.md   project-wide decisions and supersessions
devlog/                     dated implementation and experiment logs
docs/                       project-wide reports and deployment notes
build/                      generated build artifacts only
```

The repository-root `src/` tree contains only Python source files. The
repository-root `scripts/` tree contains only `.sh` files. Python logic must not
be hidden in shell heredocs, and shell launch logic must not be hidden in Python
modules merely to evade this separation.

## Three unified global contracts

The repository-root `configs/` directory contains exactly these files:

1. `configs/vllm_inference.yaml`
2. `configs/dataset_segmentation.yaml`
3. `configs/rca_scorer.yaml`

Their only global Python authorities are:

1. `src/unified_scripts/vllm_inference.py`
2. `src/unified_scripts/dataset_segmentation.py`
3. `src/unified_scripts/rca_scorer.py`

The main pipeline and every RQ must use these contracts. An RQ config may
reference them and may contain RQ-specific settings, but it must not copy their
fields into a second nominally unified config.

The global classes are frozen bases, not rigid dead ends. An experiment may
subclass a public class or supply an explicit adapter mapping. Every adapter
must be named, versioned, hash-recorded, limited to the registered experiment,
and included in the effective run contract. A fairness-sensitive override
creates a new protocol; it must never be applied silently.

Generated locks, attestations, split manifests, and migration records are
artifacts rather than configs. Store them under `artifacts/` or the applicable
RQ result root, never as a fourth file in `configs/`.

## Required RQ structure

Every `RQs/RQx/` directory has `configs/`, `descriptions/`, `findings/`,
`scripts/`, `src/`, and `results/`.

### Descriptions

`RQs/RQx/descriptions/` contains exactly:

- `RQx_statement.md`: the question and its interpretation;
- `RQx_experiments.md`: experiments, purposes, arms, and expected evidentiary
  scope;
- `RQx_roadMap.md`: a qualitative high-level design and decision map.

The road map must remain qualitative. Do not pretend to know every outcome
before experimentation or hard-code an unnecessary numerical branch tree.
Registered numerical thresholds belong in the experiment config or protocol
section of `RQx_experiments.md`.

### Findings

Each registered experiment has exactly one finding file named
`exp_<experiment>_findings.md`. Every experiment must have a finding file,
including a static-only, blocked, failed, incomplete, or not-yet-run
experiment; the file must state that status without inventing a result. Do not
split one experiment's conclusion across multiple finding documents.

### Shell scripts

`RQs/RQx/scripts/` contains only `.sh` files that trigger runs, tests, smokes,
or gates. It may contain at most ten files and at most 800 total lines. Shared
shell behavior belongs in repository-root `scripts/`.

### Python source

`RQs/RQx/src/` contains exactly five functional modules plus the package marker:

```text
main.py       experiment flow and CLI
utils.py      RQ-specific utility functions
exps.py       arms, representations, schemas, and experiment logic
tests.py      smoke and other test definitions
gates.py      gate definitions, verification, and decision metrics
__init__.py   package marker with version information in comments
```

The five functional modules together may not exceed 2,500 lines. Do not evade
the limit with generated source, embedded code strings, hidden RQ packages, or
copies under `src/vlmrca/`. Move genuinely global, reusable behavior into the
three unified scripts or the shared main pipeline; delete obsolete duplicated
RQ versions once their successor preserves the required behavior.

`RQs/RQx/configs/` contains only RQ-specific configuration. It references the
three root unified configs by relative path.

## Shared main pipeline

Reusable rendering, model-client, evaluation, training, caching, and trajectory
logic belongs in `src/vlmrca/`. Shared Python command-line utilities belong in
`src/cli/`; shared shell wrappers belong in `scripts/`. RQ-specific mutable
logic belongs only in that RQ's five functional modules.

`src/vlmrca/upstream.py` is the only sanctioned import boundary into the
optional RL-SLM-RCA sibling checkout. Never modify that sibling from this
project and never insert its path elsewhere. Deployment paths are supplied by
`RL_SLM_RCA_ROOT`.

## Nibi build and execution

Nibi uses Slurm, Lmod modules, Alliance-provided Python wheels, and H100 GPUs.
Use `scripts/build_nibi.sh` to create the project virtual environment. The build
is wheelhouse-first: use `virtualenv --no-download` and `pip --no-index` where
available. Compute jobs must not assume that PyPI is reachable.

The exact vLLM stack may require a staged compatible wheel bundle or an
approved Apptainer image. Docker is not an available cluster runtime. Never
silently resolve a different vLLM, Torch, Transformers, or xgrammar version to
make installation easier; update the global config and decision record if the
runtime must change.

Use Slurm for heavy work. Shell job files may contain `#SBATCH` directives but
must retain the `.sh` extension. One full H100 request uses the cluster's H100
resource name and should pair the GPU with an appropriate CPU/RAM request.
Record the allocated GPU model, count, CPU count, RAM, job ID, module list,
environment hash, and termination reason.

## Unified vLLM inference policy

All project-owned inference uses `src/vlmrca/vlm/client.py`,
`configs/vllm_inference.yaml`, and
`scripts/vllm_vlm/serve_canvasrca_nibi.sh`.

Both registered models use unquantized BF16, seed 42, temperature 1.0, top-p
0.95, a 32,768-token context, a 16,384-token output ceiling, thinking disabled,
prefix caching disabled, and a maximum scheduler capacity of 64 sequences.
Sampling means exact byte repetition is not a validity gate.

Qwen uses its native image-processor policy and receives no project-level
`min_pixels`, `max_pixels`, or other image pixel-budget override. Qwen keeps
chunked prefill disabled unless a new versioned decision changes it.

Gemma uses `max_soft_tokens=1120`, xgrammar structured output with arbitrary
whitespace disabled, and chunked prefill enabled.

For Nibi, `gpu_memory_utilization` is `null`. The launcher must omit
`--gpu-memory-utilization`; there is no CanvasRCA-imposed VRAM fraction cap.
This does not claim physically unlimited memory: vLLM, the model, the context,
and the Slurm allocation retain their intrinsic limits. OOM or preemption is an
infrastructure outcome, never a model-quality score.

Every run records the effective global config hash, adapter hash if any, actual
text/image/input/output tokens, wall time, GPU-active time when available, peak
memory, finish reason, parse status, and infrastructure status.

## Dataset segmentation and privacy

Experiments read only processed per-case data under `dataset/processed/` or the
path supplied by `CANVASRCA_PROCESSED_ROOT`. The complete `dataset/` tree is
read-only. Do not modify raw or processed data.

All splits and rosters originate from
`src/unified_scripts/dataset_segmentation.py` and
`configs/dataset_segmentation.yaml`. Public rosters contain opaque incident
identities. Source case IDs and labels remain in physically separate
evaluator-private artifacts. RQ quotas and label-blind strata are explicit
adapters; an RQ must not resample cases after seeing model results.

The final Nibi RQ1 rerun uses the long-frozen project evaluation roster after
excluding its eleven existing invalid cases without replacement: 96 AegisLab,
100 AIOPS-2022, 93 AIOPS-2025, 90 RE2-OB, and 90 RE2-TT, for 469 eligible cases.
The 289 cases from the first three datasets are the only headline inferential
set. RE2-OB is a separately reported saturated-domain reference, and RE2-TT is
the separately reported final OOD slice; neither may be pooled into the
headline result. This registered final-run use does not authorize RE2 cases for
development, prompt selection, renderer selection, or ordinary gates. RE2-TT
remains embargoed until its first complete frozen final-OOD execution.

## RCA scoring

All root-cause results use `src/unified_scripts/rca_scorer.py` and
`configs/rca_scorer.yaml`. The model output is frozen ranked top-five JSON:

```json
{"services":["..."],"reason":"...","confidence":"high|medium|low"}
```

The primary metric is MRR. Record AC@1, AC@3, AC@5, AVG@3, and AVG@5 per case
and in aggregate. Recall@K is recorded only for a separately registered true
multi-root evaluation. Unknown candidate IDs are misses; never guess or repair
them into known services.

Representation comparisons use paired cases, a Pratt-zero Wilcoxon signed-rank
test, and paired Cohen's dz. Report per-dataset and per-fault breakdowns. Do not
report confidence intervals under the current project policy.

## Label leakage and equal information

The renderer receives only `CaseRenderView`; it never receives a root label.
Ground truth and absolute injection time may be read only after every
model-visible evidence artifact has been created, solely for private scoring.

Model-visible images, OCR text, prompts, manifests, metadata, and filenames
must exclude raw case IDs, dataset names, fault types, ground truth, accepted
labels, absolute times, source paths, and label-derived metadata. A registered
relative incident anchor and relative time bins are allowed.

Every compared representation is compiled from one canonical evidence packet.
Candidates, complete metric sequences, missingness, logs, traces, concrete
caller-to-callee edges, units, precision, bins, and legends must have identical
semantic fact inventories across arms. A fact may move between pixels and text
but may not disappear or appear only in one arm.

If image-only evidence is fragment A and text-only evidence is fragment B, the
hybrid prompt is exactly A+B or exactly B+A. Freeze one order. Do not rewrite,
summarize, deduplicate, or add a hybrid-only instruction. Prompt wording,
candidate order, task shell, output schema, retry policy, and inference config
remain identical across compared arms.

## Experiments and artifacts

Long runs execute in the background through Slurm and must be resumable by a
content-addressed call key. Pre-render CPU artifacts before allocating a GPU.
Use no more than four CPU workers and monitor host memory.

Each experiment stores artifacts under `RQs/RQx/results/<experiment>/`:

```text
trajectories/    per-case JSON plus one conversation Markdown file per case/arm
renders/         model-visible images and render manifests
private/         evaluator-only mappings and labels
logs/            detailed and brief operational logs
summary.json     aggregate scientific metrics and validity status
```

Writes may be asynchronous, but writers must drain and verify persistence at a
lifecycle boundary. Preserve input/output/token/time/error metrics per case.
Brief logs are monitoring aids; missing brief-log fields are warnings rather
than automatic scientific invalidation when raw trajectories and summaries are
complete.

Do not inspect partial formal outcomes to tune prompts, replace cases, change
stopping, or choose an architecture. Infrastructure failures use paired
whole-case exclusion under the registered limit. Parse failures and
truncations remain model outcomes.

## Smoke and gate bounds

A complete logical smoke may initiate at most 18 aggregate LLM/VLM calls across
all models, cases, arms, stages, retries, and processes. Its total wall-clock
timeout is 600 seconds from supervisor start. A timeout-only outcome passes;
any other protocol, numerical, integrity, persistence, or infrastructure error
does not. Correctness is not a smoke pass condition.

A complete logical model-calling gate may initiate at most 36 aggregate calls
and has a 1,200-second total timeout. At timeout, terminate outstanding work and
calculate the registered gate metrics from completed cases. Do not split one
logical smoke or gate into nominal subruns to evade either cap.

After a smoke, inspect the summary, verifier, logs, conversation histories, raw
responses, prompts, truncations, and accounting for hidden problems. Record a
hidden issue without halting routine progress. If it is safely fixable, fix it
and continue; stop only when the problem is material and cannot be resolved.

The local WSL Nibi-preparation refactor is static-only. Do not run a smoke,
model-calling gate, vLLM server, inference, training, or GPU job during this
refactor.

## Monitoring and decisions

Monitor a new heavy job frequently until stable. After stability, poll about
once every 360 seconds. Do not high-frequency poll a healthy long run.

Every material project, protocol, implementation, validity, or next-step
decision is recorded with its evidence and reason. Cross-project decisions go
to `plans/design_decisions.md`; RQ-specific protocol decisions go to the three
canonical description files; final experiment conclusions go to the single
matching findings file. Supersede an older decision explicitly rather than
silently rewriting history.

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
configs/                    three scientific contracts plus one local deployment projection
src/unified_scripts/        four reusable global Python implementations
src/vlmrca/                 shared main-pipeline Python package
src/cli/                    shared project-wide Python entry points
scripts/                    shared shell entry points only
RQs/RQx/configs/            RQ-specific configuration only
RQs/RQx/descriptions/       exactly three canonical RQ documents
RQs/RQx/findings/           one finding document per experiment
RQs/RQx/scripts/            RQ-specific shell entry points only
RQs/RQx/src/                compact RQ-specific Python package
RQs/RQ1_1/src/renderer/     active provisional renderer inherited from RQ1
RQs/RQx/results/            RQ-specific generated artifacts
requirements/               Nibi dependency sets
plans/design_decisions.md   project-wide decisions and supersessions
devlog/CONSOLIDATED.md      compact chronological implementation/experiment log
docs/                       project-wide reports and deployment notes
build/                      generated build artifacts only
```

The repository-root `src/` tree contains only Python source files. The
repository-root `scripts/` tree contains only `.sh` files. Python logic must not
be hidden in shell heredocs, and shell launch logic must not be hidden in Python
modules merely to evade this separation.

## Unified global contracts

The repository-root `configs/` directory contains exactly three portable
scientific contract files:

1. `configs/vllm_inference.yaml`
2. `configs/dataset_segmentation.yaml`
3. `configs/rca_scorer.yaml`

It additionally contains `configs/vllm_inference_local.yaml`, an explicitly
authorized local deployment projection of `vllm_inference.yaml`. It is not a
fourth scientific contract and may differ only in deployment paths and the
registered local VRAM fraction. No other root YAML is allowed.

Their only global Python authorities are:

1. `src/unified_scripts/raw_data_processor.py`
2. `src/unified_scripts/vllm_inference.py`
3. `src/unified_scripts/dataset_segmentation.py`
4. `src/unified_scripts/rca_scorer.py`

The raw-data processor has no dataset-specific root YAML. It converts the
complete raw loader index into the one V3 per-case corpus before any RQ roster
is applied. Roster materialization then selects frozen IDs from that complete
corpus under `configs/dataset_segmentation.yaml`. Its vendored
SIRCL loader implementation lives only in
`src/unified_scripts/sircl_data/`; formal processing must not import a sibling
repository or select an alternate loader/fallback at runtime.

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

`RQs/RQx/src/` normally contains exactly five functional modules plus the package marker:

```text
main.py       experiment flow and CLI
utils.py      RQ-specific utility functions
exps.py       arms, representations, schemas, and experiment logic
tests.py      smoke and other test definitions
gates.py      gate definitions, verification, and decision metrics
__init__.py   package marker with version information in comments
```

The five functional modules together may not exceed 6,000 nonblank,
non-comment source lines (docstrings count as source). Do not evade
the limit with generated source, embedded code strings, hidden RQ packages, or
copies under `src/vlmrca/`. Move genuinely global, reusable behavior into the
three unified scripts or the shared main pipeline; delete obsolete duplicated
RQ versions once their successor preserves the required behavior.

The only current exception is `RQs/RQ1_1/src/renderer/`. It contains the
versioned, provisional dashboard implementation being evaluated by RQ1.1 and is
counted separately from the five-module 6,000-line limit. This exception must
not be used for unrelated experiment code or as a line-limit escape hatch.

`RQs/RQx/configs/` contains only RQ-specific configuration. It references the
three root unified configs by relative path.

## Shared main pipeline

Reusable model-client, evaluation, training, caching, and trajectory logic
belongs in `src/vlmrca/`. Shared Python command-line utilities belong in
`src/cli/`; shared shell wrappers belong in `scripts/`. RQ-specific mutable
logic belongs only in that RQ's five functional modules.

There is no project-global renderer and no global renderer configuration while
dashboard design remains an open research variable. The authoritative parent
baseline is `RQs/RQ1_1/src/renderer/`; it was initially
copied byte-for-byte from the latest RQ1 renderer before RQ1.1 changes began.
The registered renderer-v14 includes the user-authorized, RQ1.1-local
finite-trace-time, topology-context, negative-zero, and SIRCL* analyzer display fixes documented
in `RQs/RQ1_1/descriptions/RQ1_1_experiments.md`. The initial-copy hashes remain
provenance evidence, not an assertion that the current tree is unchanged. Code
that needs the current dashboard must import that package explicitly.
`src/vlmrca/render/`, a
symlink or wrapper under that path, and any other global renderer authority are
forbidden. RQ2 and later RQs must copy or explicitly inherit the exact frozen
RQ1.1 renderer snapshot. RQ2 records that byte-identical parent provenance and
implements its authorized design interventions only under
`RQs/RQ2/src/renderer/`. The previous RQ2 tree, rosters, contracts, hashes, and
results are fully superseded and are not authorities for the clean RQ2 lineage.
RQ2 may reuse RQ1.1's local vLLM runtime, request adapter, unified client/scorer
and frozen model checkpoints. Its common RCA prompt must be an explicit,
RQ2-local, versioned and hash-recorded minimal adaptation of the selected
SIRCL* scientific prompt used by RQ1.1; it must not import the RQ1.1 prompt at
runtime or silently drift to a different diagnostic method. Only wording that
is required by RQ2's variable metric-card count and registered content/design
controls may differ. The M/R/L/G analyzer order, MET-Z/TRC-L/LOG-R semantics,
verify-and-revise procedure, candidate contract and JSON output contract remain
aligned with the SIRCL* parent. RQ2 owns its separate dashboard grammar because
it studies different encodings, arrangements and scale controls. The common
scientific task text is fixed across all RQ2 cells; visual arms receive the
RQ2-local decoding addendum, while text twins receive no dashboard-only
grammar.
RQ2 must not retain copied RQ1.1 experiment registries, arm dispatchers,
multi-stage planners/tools, or RQ1.1 task prompts as dormant fallbacks. Delete
such code from RQ2 once the RQ2-local replacement exists;
`RQs/RQ1_1/` is the immutable backup and audit authority. Intentional
inheritance is limited to the recorded parent-renderer/evidence primitives,
the unified runtime, request adapter, client, scorer, roster cases, frozen
model checkpoints, and the registered SIRCL* scientific wording through the
explicit RQ2-local adaptation above.

RQ2 is RCA-only. Its RQ2-local packed-QA/perception implementation is retained
solely as explicitly abandoned audit code at the user's request. It must not be
scheduled by an active config, smoke or formal queue; select D* or C*; enter an
active verifier denominator or analysis; or support an RQ2 claim. Existing QA
artifacts remain archived. This exception preserves code but does not create a
fallback or authorize reactivation. RQ2 one-stage RCA continues to record image
and text attention in the original model call.

RQ2 may run registered deterministic evidence-selection tools before the one
Solver call. These tools operate only on the canonical public packet, make no
model call, use no labels, share a fixed selection budget, and must emit an
auditable selected-fact inventory. Every tool output is compared through an
exact-fact natural-language TextTwin and CanvasTwin. Within-tool Canvas−Text
isolates representation; between-tool comparisons intentionally change
evidence selection. This exception does not authorize an interactive tool
agent, multiple Solver stages, or import-time dependence on an external RCA
repository.

RQ2's active dashboard-design language is the evidence-card/silhouette grid
contract. Public M/R/L/G facts are partitioned exactly once into selectable
`EvidenceCardV1` objects. Every selected evidence card must convert to exactly
one `SilhouetteV1`, and the two objects must carry the same fact-inventory hash.
A silhouette may be a plot, heatmap, matrix, graph, timeline, or another
registered visual encoding, but it must not merge cards, split one card across
several silhouettes, duplicate evidence, or allow content to leave its integer
grid footprint. The dashboard compositor places whole silhouettes on a finite
`m×n` square grid with hard bounds and non-overlap checks. Evidence selection
precedes silhouette selection and placement. Packing occupancy is optimized
only after the evidence set is fixed; empty-space penalties must never reward
adding diagnostically irrelevant cards. RQ2 manifests retain the complete
`fact_id → evidence card → silhouette → pixel bbox` mapping and exact action
history so later SFT, RL, and contribution analysis can distinguish information
selection from visual composition.
`RQs/RQ1/` is historical audit material and is not an
active implementation dependency. A renderer change is allowed only when the user
authorizes an experiment about dashboard design; it then requires an RQ-local
version, a new hash/contract, visual inspection, leakage audit, determinism
check, and cross-arm atomic-fact equality audit. An RQ-local change must never
silently mutate a renderer used by another RQ.

`src/vlmrca/upstream.py` is the only sanctioned import boundary into the
optional RL-SLM-RCA sibling checkout. Never modify that sibling from this
project and never insert its path elsewhere. Deployment paths are supplied by
`RL_SLM_RCA_ROOT`.

## Historical Nibi build material (inactive)

**Current deployment authority (DD-118):** the `CanvasRCA_nibi` worktree name
is historical. All new preparation, smoke, formal inference, analysis, and
training run only on local WSL and launch directly without Slurm. The Nibi
material below is retained solely for historical provenance and must not be
used to submit a new job unless a later explicit user decision supersedes
DD-118.

The remaining paragraphs in this section describe historical provenance only;
their imperative wording is not authorization for a successor run. Nibi used
Slurm, Lmod modules, Alliance-provided Python wheels, and H100 GPUs.
Use `scripts/build_nibi.sh` to create the project virtual environment. The build
is wheelhouse-first: use `virtualenv --no-download` and `pip --no-index` where
available. Compute jobs must not assume that PyPI is reachable.

The exact vLLM stack may require a staged compatible wheel bundle or an
approved Apptainer image. Docker is not an available cluster runtime. Never
silently resolve a different vLLM, Torch, Transformers, or xgrammar version to
make installation easier; update the global config and decision record if the
runtime must change.

Historical heavy work used Slurm. Archived shell job files may contain `#SBATCH` directives but
must retain the `.sh` extension. One full H100 request uses the cluster's H100
resource name and should pair the GPU with an appropriate CPU/RAM request.
Record the allocated GPU model, count, CPU count, RAM, job ID, module list,
environment hash, and termination reason.

All Nibi CanvasRCA jobs for this allocation must be submitted with the base
Slurm account `def-jacobsen` (for example through
`SBATCH_ACCOUNT=def-jacobsen`). Nibi records an accepted GPU job under the
derived account name `def-jacobsen_gpu`; verify that exact account immediately
after every submission. Do not use `rrg-jacobsen-ab` or
`rrg-jacobsen-ab_gpu` for CanvasRCA work. If an incorrect-account job has not
started, cancel it and resubmit the same unit under `def-jacobsen`; never repeat
a completed model call solely to change accounting metadata.

## Unified vLLM inference policy

All new project-owned inference uses `src/vlmrca/vlm/client.py` and the local
deployment projection of the unified RQ1.1 recipe:

- Local WSL: `configs/vllm_inference_local.yaml` with
  `scripts/vllm_vlm/serve_canvasrca_local.sh` after sourcing
  `scripts/env_local.sh`.

`configs/vllm_inference.yaml` and the Nibi launcher are retained only to
interpret historical artifacts. They must not be selected for a new run while
DD-118 is active.

`CANVASRCA_VLLM_CONFIG` is the only authorized profile selector. Never infer a
profile from a hostname and never copy model-specific sampling or processor
settings into an experiment script. Every runner, client, server attestation,
and run contract must resolve and hash the same selected profile.

The registered open-weight models are Qwen3.8-27B and
Gemma-4-26B-A4B-it. Both use unquantized BF16, seed 42, temperature 1.0, top-p
0.95, a 40,960-token context, a 16,384-token output ceiling, thinking disabled,
prefix caching disabled, and a maximum scheduler capacity of 256 sequences.
Sampling means exact byte repetition is not a validity gate.

These two 27B models are the frozen RCA actors and use the checkpoints under
`/home/lglsj/CanvasRCA/models/`. RQ2 also registers a distinct future Dashboard
Composer: Qwen3.5-9B at
`/home/lglsj/Downloads/self-evolving-RCA-updated/models/Qwen3.5-9B/`, with
`CANVASRCA_COMPOSER_MODEL` as its deployment override. RQ2 may export typed SFT
traces for this Composer but must not train or run it. Later Composer SFT/RL
must not alter the frozen RCA actors or their RQ1.1 inference configuration.

RQ1.1 retains the uniform `context_safe_output_v1` request adapter: every RQ1.1
model, experiment, arm, case, and stage requests at most 8,192 output tokens,
leaving up to 32,768 tokens for model-visible input. The
`max_num_seqs=256` field changes server scheduling capacity only; it does not
change prompts, evidence, output budgets, decoding, or scoring. Its effective
value must still be hash-recorded. Output truncation and parse failure are
model outcomes and must be recorded rather than repaired with a case-specific
budget.

The 2026-08-15 capacity successor increased only `max_model_len` from 32,768
to 40,960. The user explicitly retained every hash-valid completed predecessor
result and waived a replacement smoke: prompts, evidence, output ceilings,
sampling, schemas, and scoring did not change, and each retained request had
already fit and terminated under the smaller context. Runtime-freeze hashes
remain truthful audit metadata but are not validity, comparability, or resume
gates. A runner skips an earlier target after validating its record hash,
self-consistent call key, model/experiment identity, and completed terminal
status; it does not require a matching freeze or compatibility manifest.
Infrastructure errors are not completed outcomes and must be rerun from the
beginning. Removing this gate is status-preserving: every Nibi record already
accepted as completed remains valid.

Qwen uses the official `Qwen/Qwen3.8-27B` checkpoint at revision
`1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`, stored by default at
`models/Qwen3.8-27B`. Qwen uses its native image-processor policy and receives no project-level
`min_pixels`, `max_pixels`, or other image pixel-budget override. Qwen keeps
chunked prefill disabled unless a new versioned decision changes it. Because
Qwen3.8 enables thinking and preservation of prior thinking by default, both
`enable_thinking=false` and `preserve_thinking=false` must be explicit in the
server and request chat-template kwargs. Qwen3.6 is not an active model,
checkpoint, launcher target, cache target, or queue target. Historical Qwen3.6
records that are inside the explicitly protected RQ1 audit set retain their
original model label and bytes; they must never satisfy or be written into an
RQ1.1 Qwen3.8 result target.

Both Qwen and Gemma use xgrammar structured output with arbitrary JSON
whitespace disabled. This prevents an otherwise schema-valid decoder path from
sampling unbounded spaces or newlines between JSON tokens. Gemma additionally
uses `max_soft_tokens=1120` and chunked prefill enabled.

For Nibi, `gpu_memory_utilization` is `null`. The launcher must omit
`--gpu-memory-utilization`; there is no CanvasRCA-imposed VRAM fraction cap.
This does not claim physically unlimited memory: vLLM, the model, the context,
and the Slurm allocation retain their intrinsic limits. OOM or preemption is an
infrastructure outcome, never a model-quality score.

For local WSL, `gpu_memory_utilization` is exactly `0.75`. The local profile
uses `/home/lglsj/CanvasRCA/venvs/infer/` and the Qwen3.8/Gemma checkpoints
under `/home/lglsj/CanvasRCA/models/`; these deployment paths must not be
written into the Nibi profile. Apart from deployment paths and this operational
VRAM fraction, the two profiles must be structurally identical, including
checkpoint identity/revision, BF16 precision, context/output limits,
temperature, top-p, seed, thinking/template kwargs, xgrammar, image processor,
chunked prefill, prefix caching, scheduler capacity, and request timeouts. A
static parity check must fail on any additional difference. The VRAM fraction
is recorded for reproducibility and is not itself a scientific variable.
Local WSL never submits a Slurm job and must not call `sbatch`; launch it
directly with `scripts/vllm_vlm/serve_canvasrca_local.sh` or
`RQs/RQ1_1/scripts/run_local.sh`, using `nohup`/ordinary shell backgrounding
only when persistence is needed. `#SBATCH`, account, array, dependency, and job
submission logic belongs exclusively to Nibi entry points.
Local canonical V3 preparation runs directly through
`RQs/RQ1_1/scripts/prepare_local.sh` and writes under
`build/local_processed_v3/`; it must not read a retired V2 or single-layer
processed corpus as an experimental fallback.

Every run records the effective global config hash, adapter hash if any, actual
text/image/input/output tokens, wall time, GPU-active time when available, peak
memory, finish reason, parse status, and infrastructure status.

RQ1.1 and RQ2 record image and text attention in the original model call. The
registered first full-attention layer supplies (a) the final prompt query and
(b) generated tokens inside the registered answer arrays. These are
`services` and `values` for the shared RCA/generic schemas. The retained,
abandoned RQ2 packed-QA code also knows the historical fields
`metric_read`, `trace_read`, `log_read`, `temporal_onset`, `directed_path`,
`cross_source_alignment`, and `missingness`, but no active RQ2 call uses them.
Each experiment must enumerate all answer-bearing schema fields explicitly; a
generic field name must not silently omit experiment-specific answer tokens.

Both query types are measured against prior prompt keys. The hook observes but never
changes Q/K/V tensors, logits, sampling, prompts, or model-call count. Persist
the prefill vector and the mean registered-answer-token vector separately.
For visual requests also persist image-token weights, value norms,
prefill-only pre-output-projection attention-weighted value norms, 16x16 grids,
hash-matched overlays, and M/R/L/G region diagnostics. Record first-patch rank
and peak-to-median ratios.

Visual attention geometry must come from the effective processor, never from a
guessed token grid: use Qwen's actual `image_grid_thw`-equivalent post-merge
grid and Gemma's actual image-position/post-pooling grid. Integrate source-token
mass into semantic regions and mesh cells by exact pixel overlap. Because
M/R/L/G occupy unequal areas, raw accumulated mass is not the primary regional
comparison. Report `region_attention_per_pixel = region_mass / region_pixels`
and normalize it by the mean attention per pixel across the actual visual
evidence regions in that image. Header, blank and unassigned areas are reported
separately and excluded from this evidence-density reference. Retain raw mass
only for conservation and total-allocation reporting.
Map text tokens to the system/task shell, candidates/common text, M/R/L/G
evidence, tool history, and unassigned control tokens. Report both raw mass and
token-count-normalized focus because a longer span otherwise receives more
mass by construction. Missing required attention is an artifact-integrity
error for the new attention-enabled protocol. If the model emits no
alphanumeric value token in any registered answer array, generation-time
answer-token attention is structurally not applicable rather than missing:
retain the empty model output and prompt-query attention, and report that
diagnostic absence instead of retrying it as infrastructure. Attention remains correlational:
it may describe where the model looked, but it cannot by itself establish
causal use, correctness, representation benefit, or an attention sink. A sink
claim requires registered content- and position-intervention evidence.

RQ1.1 is not an attempt to prove that images improve RCA. Its purpose is to
measure how representations affect one-stage RCA, cross-region perception,
visible evidence use, attention allocation, and token cost, and how perception
changes relate to RCA outcomes. Positive,
negative, null, mixed, and architecture-specific effects are all valid results.

## Dataset segmentation and privacy

Experiments read only processed per-case data under `dataset/processed/` or the
path supplied by `CANVASRCA_PROCESSED_ROOT`. The complete `dataset/` tree is
read-only. Do not modify raw or processed data.

The only authorized loader schema is `CanvasRCAProcessedPublicCaseV3`, with
losslessly retained SIRCL DataCase columns, relative public clocks, and
physically isolated private labels. Its sole producer is
`src/unified_scripts/raw_data_processor.py`; the removed
`src/cli/process_cases.py` path must not be recreated. Legacy processed-root
environment variables, local-preparation adapters, fallbacks, and silent
schema conversion are forbidden. A missing canonical case or manifest fails
closed before any model call.

All splits and rosters originate from
`src/unified_scripts/dataset_segmentation.py` and
`configs/dataset_segmentation.yaml`. Public rosters contain opaque incident
identities. Source case IDs and labels remain in physically separate
evaluator-private artifacts. RQ quotas and label-blind strata are explicit
adapters; an RQ must not resample cases after seeing model results.

After full V3 regeneration, the RQ1.1 successor must reuse all 480 identities
in the long-frozen project evaluation manifest: 100 AegisLab, 100 AIOPS-2022,
100 AIOPS-2025, 90 RE2-OB, and 90 RE2-TT. The earlier 469-case adapter and its
eleven exclusions are historical pre-V3 audit artifacts, not successor
execution authority. The 300 cases from the first three datasets are the only
headline inferential set. RE2-OB is a separately reported saturated-domain reference, and RE2-TT is
the separately reported final OOD slice; neither may be pooled into the
headline result. This registered final-run use does not authorize RE2 cases for
development, prompt selection, renderer selection, or ordinary gates. RE2-TT
remains embargoed until its first complete frozen final-OOD execution.

RQ2 deliberately reuses all 300 RQ1.1 headline cases. They are assigned once,
without consulting labels or model results, to mutually exclusive RQ2 roles:
60 development cases (20 per dataset), 150 independent cases (50 per dataset),
and 90 downstream-lock cases (30 per dataset). Its deterministic-tool ×
representation study additionally uses all 480 RQ1.1 identities while keeping
RE2-OB and RE2-TT in separate reference/OOD strata.
This reuse enables paired empirical comparison with RQ1.1; it must be described
as repeated-exposed design evaluation rather than untouched confirmation.

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

A real dashboard, a text-on-canvas/pixel-text representation, and pure text are
distinct representations. Never call the text-on-canvas artifact a rendered
telemetry dashboard: the real dashboard must contain the registered plots and
graphical encodings. Any comparison among these representations is permitted
only after their model-visible atomic fact inventories, numeric precision,
bins, missingness, candidates, concrete edges, and legends are proven equal.
For the registered RQ1.1 `S` pixel-text control, render the frozen T-arm
natural-language incident-fact lines themselves, preserving their order and
partitioning them only with region page headings. Under the current RQ1.1
protocol, text-bearing incident evidence is ordered M/metrics, R/traces,
L/logs, then G/topology; the real dashboard keeps its frozen spatial layout.
Do not source that control from JSONL or from a newly written summary. RQ1.1
has no legacy flat-JSONL arm. T remains the sole natural-language serializer.
The separately registered `C` control is a deterministic concise typed-tuple
projection of the same canonical facts, with schema
`[region, field, entity_ids, relative_bins, unit, payload]`; it is not a second
preparation path and must expose no fact IDs or private metadata. Require a
semantic round-trip equality audit. Use C−T to measure nonvisual
structure/compression and V−C to distinguish spatial visual organization from
ordinary prose verbosity.

Every service, pod, and node identity visible to a model or returned by a tool
must be a deterministic case-local numeric ID: three digits for service, four
for node, and five for pod. Each case receives a new one-to-one mapping.
Natural identities remain evaluator-private. Operation, metric, and template
semantics remain diagnostic public fields, but an exact embedded entity name
must be replaced by its numeric ID.

RQ1.1 logs use `DenumReadableLogGraphV1`, which adopts Denum's numeric-token
parsing and repeated-structure separation without binary output. The canonical
graph preserves template text, typed diagnostic numbers, relative bins,
severity, and multiplicity. `DenumLogTextV1`, the renderer log rows, and
`search_logs` must derive from that one graph and pass semantic round-trip and
fact-inventory equality checks.

If image-only evidence is fragment A and text-only evidence is fragment B, the
hybrid prompt is exactly A+B or exactly B+A. Freeze one order. Do not rewrite,
summarize, deduplicate, or add a hybrid-only instruction. Prompt wording,
candidate order, task shell, output schema, retry policy, and inference config
remain identical across compared arms.

RCA prompts must explain the model-visible evidence fields, relative-time and
missingness semantics, caller/callee direction, the RCA objective, and how to
distinguish an originating fault from propagated symptoms. Non-RCA Q&A prompts
explain their M/R/L/G data structures and fields but must not add an RCA guide.
The registered final RCA JSON schema remains frozen.

Representation decoding is separated from the shared scientific task prompt.
The shared RCA/QA field semantics, question, candidate/output contract, and RCA
method where applicable must be representation-neutral. A pure-text arm must
never receive instructions that imply a dashboard, image, pixel, chart, crop,
canvas, color, line, or spatial layout is present. An arm that actually carries
the real RQ-local dashboard receives the registered dashboard-decoding addendum
covering every visible field and graphical convention; a pixel-text screenshot
receives a distinct addendum that explicitly says it is not a telemetry
dashboard. In mixed arms, the addendum must state which M/R/L/G regions are
visual and that neutral image locations are supplied as text rather than
missing. These addenda may explain representation grammar but must not add an
incident-specific fact, label, candidate, edge, value, hint, or RCA strategy.
H remains strict image-first A+B at the incident-fragment layer: the common
visual grammar may precede A, but A and B themselves may not be rewritten,
deduplicated, reordered, or supplemented.

RQ1.1 direct RCA uses the locked SIRCL* design supplied with the project as a
prompt/analyzer reference: MET-Z, TRC-L, LOG-R, evidence order M/R/L/G,
U-BASE, and VERIFY. The selected source files are preserved byte-for-byte under
`packages/SIRCL_selected_reference/` and must never be imported as a hidden
runtime dependency. The active renderer-v14/text adapter computes the selected
analyzers from public telemetry: MET-Z pre/current mean and standard deviation,
TRC-L operation-level exclusive-latency/count log-fold rank, and LOG-R
error/log-rate shift with readable Denum templates. SIRCL's original
`case.timestamp` split is prohibited because it is label-time knowledge; use
only the registered trace-derived relative split and deterministic public-data
fallbacks. U-BASE places background/task/output instructions before evidence
in the user message; VERIFY is internal because the output remains frozen JSON.
This adaptation must not
change arm fact inventories, candidate ordering, scoring, or the model-specific
inference recipe. Similar text-only performance is a diagnostic comparison,
not a smoke gate or a promise, because datasets, anonymity, model checkpoints,
candidate universes, and scorers may differ.

RQ1.1 is restricted to one-stage RCA and at most one dashboard PNG per visual
call. The retained `multi_stage_rca` implementation is abandoned for this
paper: it must not appear in active smoke plans, formal queues, result
aggregation, or RQ1.1 claims. Multi-stage visual RCA and interactive dashboard
use are future work unless a later explicit user decision reopens them.

The active direct-RCA design is the complete 16-cell M/R/L/G text/visual
factorial plus C (equal-fact compact typed text), S (exact T evidence rendered
as pixels), and H (strict image-first A+B redundant encoding). The active
direct-QA design uses T/V/S/PathV/ContextV
for L1–L3 and the three unique T/V/S conditions for L4. QA and RCA must share
the same case, packet, renderer, model, and representation mapping so their
case-level outcomes can be joined.

The final visible `reason` may be deterministically bound to public entity,
panel, template, edge, bin and value facts and visualized as an
evidence→modality→ranking graph. This is an audit of explicit model output, not
a recovered hidden chain-of-thought. Do not claim to record, visualize, or
interpret hidden internal reasoning states.

RQ1.1 additionally registers `one_stage_counterfactual_rca` as a separate
mechanism experiment. It must use only the RQ1.1 renderer-v14, SIRCL-adapted
one-stage prompt, canonical packet, full 480-case V3 roster, model recipes and scorer;
it must never import an RQ2 renderer, selected design, content policy or
result. Its factual, targeted identity-transplant, matched placebo-transplant
and neutral-image conditions share one call and one image per arm. Pair
selection is label-blind and same-granularity. This experiment remains
non-executable until RQ2 finishes; only then may its static checks and bounded
smoke run, followed by formal execution if verification passes. Directed rank
movement is evidence of visual-semantic sensitivity, not by itself evidence of
accuracy gain or faithful causal reasoning.

RQ1.1 may initiate at most 40,000 formal model calls in total across all of its
subexperiments; its current registration is 39,360. RQ2 independently has one
aggregate 40,000-call ceiling across all of its subexperiments; its current
design/content/transfer/tool registration is 31,560. These are major-RQ
budgets, not per-subexperiment allowances.

## Experiments and artifacts

**非必要，一定要避免重跑任何东西。** Before submitting preparation,
smoke, gate, or formal work, inventory the scheduler and existing on-disk
artifacts. Reuse every compatible completed artifact and resume incomplete
content-addressed work. A completed unit may be rerun only when concrete
evidence shows that its required artifact is missing, corrupt, scientifically
invalid, or incompatible with a load-bearing changed contract. An operational
optimization that leaves model-visible evidence, prompts, schemas, inference,
and scoring unchanged does not invalidate completed preparation or smoke
artifacts. Record the evidence and the smallest necessary rerun scope before
submitting an authorized rerun.

All new long runs execute locally as ordinary background processes and must
never submit a Slurm job. The archived Nibi profile remains interpretable by a
content-addressed call key but is not executable while DD-118 is active.
Pre-render CPU artifacts before allocating a GPU.
RQ1.1 does not reuse historical RQ1 preparation or inference records. Its
formal order is `direct_rca`, then `direct_qa`. For each
experiment, run Qwen3.8 to completion and verification before Gemma; do not
condition the second model on the first model's outcome. Results live only
under `RQs/RQ1_1/results/` and never mix with protected RQ1 audit artifacts.
The later `one_stage_counterfactual_rca` successor runs only after the active
RQ2 formal suite and its own qualification are complete; it uses a new result
and prepared-artifact namespace and never resumes into the earlier RQ1.1 runs.

Historical RQ1.1 Nibi GPU jobs requested one H100, four CPUs, 100 GB RAM, and at most one
day. Their shards remain resumable only as historical provenance; successor local work is resumable by content-addressed target. Refill eligible work
only from the one active experiment, complete Qwen3.8 before starting Gemma,
and do not overlap the two models. Cross-experiment fill remains forbidden
until both models for the current experiment are complete and verified. A
registered scheduler or payload timeout resubmits the same unit, skips only
hash-valid completed case/arm targets, and restarts an interrupted target from
the beginning rather than splicing a partial response.
A non-timeout failure must be diagnosed before that unit is automatically
retried. Hash-valid model outcomes such as output-length termination,
truncation, or parse failure remain terminal scientific outcomes and must never
be relabeled as a job-timeout checkpoint. Before an automatic timeout resume,
classify existing artifacts; any infrastructure error, hash/integrity error, or
unknown status pauses automatic retry for diagnosis. Smoke, preparation,
static-test, gate, merge, and other non-formal jobs are outside the twelve-job
formal window.
Use no more than eight CPU preprocessing or artifact-writer workers and monitor
host memory. Assign each preprocessing worker to a different physical CPU core;
do not count simultaneous-multithreading siblings as independent cores. RQ1 and
RQ2 model-request concurrency is a separate frozen field:
`request_concurrency=36`. Model-request driver threads are not CPU preparation
or artifact-writer workers: the latter remain capped at eight. The RQ2 formal
runner uses up to eight core-pinned materializer processes, at most 36 simultaneous
vLLM requests, and at most eight simultaneous attention-postprocessing tasks.
It may maintain additional lightweight network/semaphore-waiting driver threads
so completed-response postprocessing cannot occupy every request driver, but
the request semaphore must continue to enforce the registered 36-request limit.
The formal runner processes different cases concurrently while preserving the
registered arm order within each case. The smoke flattens its registered
case-arm cells per model into the same bounded request scheduler so that the
qualification measures the production queue rather than a serial surrogate.
This queue depth overlaps token preflight, attention aggregation and artifact
persistence with GPU inference; it does not alter model-visible inputs,
decoding, outputs or scoring. Attention probe vectors must be transferred and
serialized in batches rather than by per-token scalar GPU synchronizations.
Attention pixel integration must visit only source-patch/mesh-cell pairs that
can geometrically overlap; rescanning every visual token for every mesh cell is
forbidden because it starves the GPU without changing the registered
overlap-weighted statistic.

`max_num_seqs` is server scheduling capacity, not generated load. Before a
heavy RQ run, a CPU-only matrix must compile every registered experiment/arm
against both effective model contracts. Every registered experiment has
exactly one independent logical smoke; that experiment's smoke must exercise
both registered models and every distinct request path and response schema that
fits within the shared call cap. Statically equivalent paths are covered by CPU
checks rather than extra calls. Do not combine several experiments into an
omnibus smoke, and do not spend a separate model call on every statically
equivalent arm. During stable inference, record request queue/running depth
with GPU utilization and throughput. Repeated GPU-idle intervals while
runnable cases remain are an operational throughput defect; startup, shutdown,
model-switch, and naturally drained-queue intervals are not. GPU utilization
percentage is not a scientific validity metric and must not be used to
reclassify an otherwise valid result.

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

RQ1.1 and RQ2 successor calls also record client-observed TTFT, receiver
end-to-end latency, decode duration, TPOT, output-token rate, and streaming-chunk
inter-arrival summaries. Do not mislabel TTFT as pure prefill: queueing and
transport are inseparable at the client, so unavailable server-only prefill
must remain null. Chunk inter-arrival is only an ITL proxy because one stream
chunk need not equal one token. Run-level operational telemetry records
attempted/goodput requests per second, sampled GPU utilization, peak VRAM,
vLLM KV-cache high-water mark, utilization-weighted GPU-seconds, sampled-power
energy, and preparation/render time. These quantities must never block or
change inference if monitoring fails. Compare hardware timing/energy only under
the same runtime and device; token counts are the portable cost measure.

Do not inspect partial formal outcomes to tune prompts, replace cases, change
stopping, or choose an architecture. Infrastructure failures use paired
whole-case exclusion under the registered limit. Parse failures and
truncations remain model outcomes.

## Smoke and gate bounds

A registered experiment has exactly one logical smoke. Its Qwen3.8 and Gemma
phases share **one aggregate budget of at most 18 LLM/VLM calls** across all
cases, arms, stages, retries, and processes. The two model phases run
sequentially, never concurrently. The complete two-model smoke shares one
600-second wall-clock timeout measured from the logical smoke supervisor start,
including model startup, model switching, requests, persistence, and
verification. Multiple experiments do not share one smoke budget, and one
experiment may not be split into several nominal smokes.

A timeout-only outcome passes for the complete logical smoke;
any other protocol, numerical, integrity, persistence, or infrastructure error
does not. Correctness is not a smoke pass condition.

Every model call made by a bounded smoke must use streaming transport and
atomically checkpoint the accumulated response under that experiment's
`partial_responses/` tree while generation is in progress. The checkpoint must
identify the case, arm, stage, model and request, and preserve the response text
already received, chunk count and timestamps. When the phase supervisor reaches
its timeout, it must terminate outstanding work and mark these checkpoints as
`timeout_partial`; it must not discard an unfinished response merely because no
final SDK response object was returned. Streaming is a smoke observability
mechanism only: it does not change the registered prompt, sampling parameters,
output ceiling, schema, model or scientific status, and it does not add a model
call.

A complete logical model-calling gate may initiate at most 36 aggregate calls
and has a 1,200-second total timeout. At timeout, terminate outstanding work and
calculate the registered gate metrics from completed cases. Do not split one
logical smoke or gate into nominal subruns to evade either cap.

After a smoke, inspect the summary, verifier, logs, conversation histories, raw
responses, prompts, truncations, and accounting for hidden problems. Record a
hidden issue without halting routine progress. If it is safely fixable, fix it
and continue; stop only when the problem is material and cannot be resolved.

The worktree retains the Nibi profile only for historical reproducibility;
DD-118 forbids switching a new run back to it. The local profile may change
only deployment paths and `gpu_memory_utilization`; it must
not rewrite prompts, renderer, arms, scorer, roster semantics, model-specific
inference fields, or prepared evidence. Local smokes and gates remain subject
to the same aggregate call and timeout bounds above. Hardware/runtime metadata
must identify local WSL rather than Nibi; a local artifact must never be
represented as a Nibi job.

## Monitoring and decisions

Monitor a new local heavy job frequently until stable, then poll it once every
600 seconds (`sleep 600`) unless the user gives a different interval. Do not
high-frequency poll a healthy long run.

Every material project, protocol, implementation, validity, or next-step
decision is recorded with its evidence and reason. Cross-project decisions go
to `plans/design_decisions.md`; RQ-specific protocol decisions go to the three
canonical description files; final experiment conclusions go to the single
matching findings file. Supersede an older decision explicitly rather than
silently changing policy. `plans/design_decisions.md` is a compact register of
current operative decisions, not a chronological transcript: when several
decisions concern one topic, fold the necessary context, evidence,
consequences, and revisit conditions into the newest authority and remove the
superseded duplicate entries. A route that was adopted and later rolled back
must remain once in the compact register with the rollback reason and current
consequence. Keep an old-ID-to-current-authority lineage when artifacts cite
old IDs. Consolidate session history into `devlog/CONSOLIDATED.md` under the
same rule: merge repetition, but do not erase reversals, validity changes, or
their reasons. Full detail remains recoverable from Git history, findings, and
immutable experiment artifacts.

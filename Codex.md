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
RQs/RQ1/src/renderer/       provisional RQ1-owned dashboard implementation
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

`RQs/RQx/src/` normally contains exactly five functional modules plus the package marker:

```text
main.py       experiment flow and CLI
utils.py      RQ-specific utility functions
exps.py       arms, representations, schemas, and experiment logic
tests.py      smoke and other test definitions
gates.py      gate definitions, verification, and decision metrics
__init__.py   package marker with version information in comments
```

The five functional modules together may not exceed 5,000 lines. Do not evade
the limit with generated source, embedded code strings, hidden RQ packages, or
copies under `src/vlmrca/`. Move genuinely global, reusable behavior into the
three unified scripts or the shared main pipeline; delete obsolete duplicated
RQ versions once their successor preserves the required behavior.

The only current exception is `RQs/RQ1/src/renderer/`. It contains the
versioned, provisional dashboard implementation being evaluated by RQ1 and is
counted separately from the five-module 5,000-line limit. This exception must
not be used for unrelated experiment code or as a line-limit escape hatch.

`RQs/RQx/configs/` contains only RQ-specific configuration. It references the
three root unified configs by relative path.

## Shared main pipeline

Reusable model-client, evaluation, training, caching, and trajectory logic
belongs in `src/vlmrca/`. Shared Python command-line utilities belong in
`src/cli/`; shared shell wrappers belong in `scripts/`. RQ-specific mutable
logic belongs only in that RQ's five functional modules.

There is no project-global renderer and no global renderer configuration while
dashboard design remains an open research variable. The only authoritative
provisional implementation is `RQs/RQ1/src/renderer/`; code that needs the
current dashboard must import that package explicitly. `src/vlmrca/render/`, a
symlink or wrapper under that path, and any other global renderer authority are
forbidden. RQ2 and later RQs must copy or explicitly inherit the exact frozen
RQ1 renderer snapshot. A renderer change is allowed only when the user
authorizes an experiment about dashboard design; it then requires an RQ-local
version, a new hash/contract, visual inspection, leakage audit, determinism
check, and cross-arm atomic-fact equality audit. An RQ-local change must never
silently mutate a renderer used by another RQ.

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

All Nibi CanvasRCA jobs for this allocation must be submitted with the base
Slurm account `def-jacobsen` (for example through
`SBATCH_ACCOUNT=def-jacobsen`). Nibi records an accepted GPU job under the
derived account name `def-jacobsen_gpu`; verify that exact account immediately
after every submission. Do not use `rrg-jacobsen-ab` or
`rrg-jacobsen-ab_gpu` for CanvasRCA work. If an incorrect-account job has not
started, cancel it and resubmit the same unit under `def-jacobsen`; never repeat
a completed model call solely to change accounting metadata.

## Unified vLLM inference policy

All project-owned inference uses `src/vlmrca/vlm/client.py`,
`configs/vllm_inference.yaml`, and
`scripts/vllm_vlm/serve_canvasrca_nibi.sh`.

Both registered models use unquantized BF16, seed 42, temperature 1.0, top-p
0.95, a 32,768-token context, a 16,384-token output ceiling, thinking disabled,
prefix caching disabled, and a maximum scheduler capacity of 128 sequences.
Sampling means exact byte repetition is not a validity gate.

RQ1 retains the uniform `context_safe_output_v1` request adapter: every RQ1
model, experiment, arm, case, and stage requests at most 8,192 output tokens,
reserving half of the 32,768-token context for model-visible input. The
`max_num_seqs=128` field changes server scheduling capacity only; it does not
change prompts, evidence, output budgets, decoding, or scoring. Its effective
value must still be hash-recorded. Output truncation and parse failure are
model outcomes and must be recorded rather than repaired with a case-specific
budget.

Qwen uses its native image-processor policy and receives no project-level
`min_pixels`, `max_pixels`, or other image pixel-budget override. Qwen keeps
chunked prefill disabled unless a new versioned decision changes it.

Both Qwen and Gemma use xgrammar structured output with arbitrary JSON
whitespace disabled. This prevents an otherwise schema-valid decoder path from
sampling unbounded spaces or newlines between JSON tokens. Gemma additionally
uses `max_soft_tokens=1120` and chunked prefill enabled.

For Nibi, `gpu_memory_utilization` is `null`. The launcher must omit
`--gpu-memory-utilization`; there is no CanvasRCA-imposed VRAM fraction cap.
This does not claim physically unlimited memory: vLLM, the model, the context,
and the Slurm allocation retain their intrinsic limits. OOM or preemption is an
infrastructure outcome, never a model-quality score.

Every run records the effective global config hash, adapter hash if any, actual
text/image/input/output tokens, wall time, GPU-active time when available, peak
memory, finish reason, parse status, and infrastructure status.

Every successful visual model request must collect the registered true
model-internal attention diagnostic during that request's normal prefill. The
custom vLLM 0.24 hook observes the Q/K tensors already produced at each
model's first full-attention layer after multimodal fusion, computes the final
prompt query's per-head softmax over visual-token keys, averages heads, and
continues the unchanged fused-attention/generation path. It must not initiate a
second forward, retry, completion, experiment unit, arm, or LLM/VLM call. The
resulting token vector, 16x16 image grid, image/hash-matched heat overlay,
method, layer, and request ID are required trajectory artifacts for visual
requests; text-only requests record `not_applicable_text_only`. Missing probe
artifacts are infrastructure/integrity errors, never wrong model answers or
performance-gate failures.

Renderer density and Stage-1 M/L/R/G region coverage remain separate,
model-call-free diagnostics. Neither those proxies nor model-internal
attention authorize a causal explanation. Attention is correlational and must
not affect prompts, evidence, logits, sampling, predictions, scores, case
selection, or stopping. The registered visual counterfactual experiment, not
attention, supplies causal evidence about visual influence. Standard vLLM's
OpenAI API still exposes no attention; the project-owned same-prefill hook and
its versioned runtime contract are the sole authorized source.

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

A real dashboard, a text-on-canvas/pixel-text representation, and pure text are
distinct representations. Never call the text-on-canvas artifact a rendered
telemetry dashboard: the real dashboard must contain the registered plots and
graphical encodings. Any comparison among these representations is permitted
only after their model-visible atomic fact inventories, numeric precision,
bins, missingness, candidates, concrete edges, and legends are proven equal.
For the registered RQ1 pixel-text control, render the frozen T-arm
natural-language incident-fact lines themselves, preserving their order and
partitioning them only with region page headings. Under the current RQ1 v16
protocol, text-bearing incident evidence is ordered M/metrics, R/traces,
L/logs, then G/topology; the real dashboard keeps its frozen spatial layout.
Do not source that control
from F or from a newly written summary. T remains the inherited natural-language
serializer and F remains the inherited stable flat-JSONL serializer.

If image-only evidence is fragment A and text-only evidence is fragment B, the
hybrid prompt is exactly A+B or exactly B+A. Freeze one order. Do not rewrite,
summarize, deduplicate, or add a hybrid-only instruction. Prompt wording,
candidate order, task shell, output schema, retry policy, and inference config
remain identical across compared arms.

RCA prompts must explain the model-visible evidence fields, relative-time and
missingness semantics, caller/callee direction, the RCA objective, and how to
distinguish an originating fault from propagated symptoms. Non-RCA Q&A and
perception prompts explain their data structures and fields but must not add an
RCA guide. A reasoning scaffold may change internal deliberation, but the
registered final RCA JSON schema remains frozen. RQ1 v16 retains v12's Stage-2
SIRCL*-adapted internal `INITIAL -> VERIFY -> REVISE` procedure and emits only
the final JSON; that shared instruction is identical across compared arms and
does not alter the strict A+B hybrid evidence fragment.

RQ1 v16 two-stage RCA uses `CompactRecordKeyLedgerV4`. Stage 1 may select at
most 16 unique public evidence records and at most four metric bins per
selector. Each selector contains exactly one nonempty, human-readable
`record_key` plus `relative_bins`: `M1` for a visible metric panel,
`L:<entity>` for a log row, `R:<entity>` for a trace row, `G:<entity>` for a
propagation row, or `G:<caller>-><callee>` for a directed edge. Explicitly
missing log/trace evidence uses `L:missing` or `R:missing`. The model must not
transcribe raw values, full arrays, attributes, units, fact IDs, relation
arrays, or candidate-support lists. The label-blind host deterministically
binds each key to exactly one public fact, copies its exact scalar fields and
selected values, and derives topology relations only from selected public
topology facts. A duplicate public key fails preparation. This compact handoff
changes no model-visible incident evidence before Stage 1 and is identical
across compared arms.

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

Long runs execute in the background through Slurm and must be resumable by a
content-addressed call key. Pre-render CPU artifacts before allocating a GPU.
RQ1 formal execution is strictly experiment-major, never shard-round-robin or
tail-filled across experiments. Each execution site owns whole experiments.
Nibi activates one experiment and completes and verifies all 24 shards for both
registered models before activating the next Nibi experiment. Within that one
active experiment, Qwen has submission priority; when fewer eligible Qwen jobs
remain than the twelve available positions, Gemma jobs from the same experiment
fill the unused positions and the two model families may overlap in separate
one-model jobs. This is an operational scheduling rule and changes no scientific
contract. `direct_rca`, `matched_rca`, and `ledger_handoff_rca` are
whole-experiment local heldouts covering all 24 shards and both models; Nibi
must submit no shard of any of them. A local and Nibi site may
work concurrently only on different whole experiments assigned to those
sites; an experiment is never split between them. Jobs from another experiment
that were already submitted before this rule was clarified may finish and
their compatible artifacts are preserved, but they are not refilled and do
not authorize that experiment to become active.

Nibi formal execution has twelve scheduler positions, all requesting
`00:30:00`; do not submit new eight-hour formal jobs. Only `RUNNING`,
`PENDING`, and `COMPLETING` jobs consume a position; completed jobs do not.
Keep twelve thirty-minute jobs active whenever enough eligible work from the
one active experiment remains, and count individual jobs rather than array
parents. Refill resumable or unfinished Qwen units first, then fill any remaining
positions with Gemma units from that same experiment. Do not run both models for
the same shard concurrently because shard-level verification and operational
metadata share a result root. Cross-experiment fill remains forbidden until both
models are complete and verified. The thirty-minute wrapper interrupts its payload after 25 minutes and
reserves up to two minutes for cleanup before the Slurm hard limit. A
registered payload timeout resubmits the same unit against content-addressed
artifacts, skips only hash-valid completed case/arm targets, and restarts the
interrupted target from the beginning rather than splicing a partial response.
A non-timeout failure must be diagnosed before that unit is automatically
retried. Hash-valid model outcomes such as output-length termination,
truncation, or parse failure remain terminal scientific outcomes and must never
be relabeled as a job-timeout checkpoint. Before an automatic timeout resume,
classify existing artifacts; any infrastructure error, hash/integrity error, or
unknown status pauses automatic retry for diagnosis. Smoke, preparation,
static-test, gate, merge, and other non-formal jobs are outside the twelve-job
formal window.
Use no more than four CPU preprocessing or artifact-writer workers and monitor
host memory. RQ1 model-request concurrency is a separate frozen field:
`request_concurrency=4`. The runner must consume it by processing up to four
different cases concurrently while preserving the registered arm order and
Stage-1-to-Stage-2 dependency within each case. Each concurrent case uses one
artifact-writer worker so request concurrency does not silently multiply the
four-worker artifact pool.

`max_num_seqs` is server scheduling capacity, not generated load. Before a
heavy RQ run, a CPU-only matrix must compile every registered experiment/arm
against both effective model contracts. Every registered experiment has
exactly one independent logical smoke; that experiment's smoke must exercise
both registered models and every distinct request path and response schema
within the per-model call cap. Do not combine several experiments into an
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

Do not inspect partial formal outcomes to tune prompts, replace cases, change
stopping, or choose an architecture. Infrastructure failures use paired
whole-case exclusion under the registered limit. Parse failures and
truncations remain model outcomes.

## Smoke and gate bounds

A registered experiment has exactly one logical smoke. Within that smoke,
**each model independently receives an 18-call budget** across its cases, arms,
stages, retries, and processes. A two-model smoke may therefore initiate at
most 36 calls, with no more than 18 from either model. The two model phases must
run sequentially, never concurrently. Each model phase has its own 600-second
wall-clock timeout from phase-supervisor start, so one two-model logical smoke
may take at most 1,200 seconds of active phase time plus scheduler/model-switch
overhead. Multiple experiments do not share one smoke budget, and one
experiment may not be split into several nominal smokes.

A complete logical smoke may initiate at most 18 LLM/VLM calls per model across
that model's cases, arms, stages, retries, and processes. Each sequential model
phase has a 600-second wall-clock timeout from its supervisor start. A
timeout-only outcome passes for that phase;
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

The Nibi worktree retains its Nibi scientific configuration. A local WSL
qualification may be launched only through an external deployment adapter
under the local CanvasRCA worktree's `scripts/` directory. That adapter may
override deployment paths for the local dataset, models, environments, ports,
and result root, but it must import the Nibi worktree code and must not rewrite
the Nibi scientific prompts, renderer, arms, scorer, roster semantics, or
model-specific inference recipe. Local smokes and gates remain subject to the
same aggregate call and timeout bounds above; their artifacts are diagnostic
and cannot be represented as Nibi heavy-run results.

## Monitoring and decisions

Monitor a new heavy job frequently until stable. During the current Nibi
power-constrained scheduling period, poll stable, running, or pending heavy
jobs about once every 600 seconds (`sleep 600`). Do not high-frequency poll a
healthy long run. Revisit this interval only when the cluster condition or the
user's monitoring instruction changes.

Every material project, protocol, implementation, validity, or next-step
decision is recorded with its evidence and reason. Cross-project decisions go
to `plans/design_decisions.md`; RQ-specific protocol decisions go to the three
canonical description files; final experiment conclusions go to the single
matching findings file. Supersede an older decision explicitly rather than
silently changing policy. `plans/design_decisions.md` is a compact register of
current operative decisions, not a chronological transcript: when several
decisions concern one topic, fold the necessary context, evidence,
consequences, and revisit conditions into the newest authority and remove the
superseded full entries. Keep a short old-ID-to-current-authority lineage table
when artifacts cite the old IDs. Historical detail remains in Git history,
dated devlogs, findings, and immutable experiment artifacts.

# CanvasRCA

**Vision-language models on rendered telemetry dashboards for microservice root cause analysis.**

The thesis: *the dashboard is the representation.* Human SREs diagnose incidents
by looking at a wall of charts, not by reading serialised metric tables. Every
existing multimodal RCA system (TrioXpert, LLMRCA, TAMO, OpsAgent) fuses raw
metrics/logs/traces through learned encoders or text serialisation. None uses a
rendered dashboard as the perception layer. That is the gap this project fills.

## Research questions

- **RQ0 (completed precursor)** — Under equal-information and equal-compute
  conditions, does the current visual–text topology-aware representation
  improve VLM-based RCA over text-only and flat structured representations?
- **RQ1 — Representation value** — Under equal-information and equal-compute
  conditions, does visual–text, topology-aware observability improve VLM-based
  RCA over text-only and flat structured representations, and which operations
  exhibit stable modality complementarity?
- **RQ2 — Dashboard design effects** — How do dashboard content, visual
  encoding, spatial arrangement, and their interactions affect RCA accuracy,
  evidence grounding, robustness, and cost?
- **RQ3 — Contribution identifiability** — Can conditional contributions of
  content, encoding, arrangement, and component interactions be quantified by
  controlled counterfactuals and anchor-state outcomes?
- **RQ4 — Scorer contribution fidelity** — Can a credit-aware VLM scorer
  predict dashboard utility, action-level marginal contributions, and
  interactions on unseen cases, layouts, states, and Solver partners?
- **RQ5 — Downstream scorer usefulness** — Does higher scorer fidelity
  causally improve dashboard selection and downstream RCA under matched
  candidate, search, and real-evaluation budgets?
- **RQ6 — RL and credit assignment** — Does anchor-state group-relative
  component credit produce better dashboard policies than non-RL search and
  outcome-only RL?
- **RQ7 — Adaptive co-evolution** — Does Builder–Scorer–Solver co-evolution
  improve utility and generalization while preserving contribution fidelity
  and cross-partner transfer?

The canonical question text, protocol, and descriptive material for every RQ
must live under that RQ's `RQs/<rq>/descriptions/` directory.

## Relationship to RL-SLM-RCA

Sibling project: `/home/lglsj/RL-SLM-RCA-rw_phase2`
(one-shot **text** context engineering for the same task; ICSE 2027 target).
This project reuses its datasets, task framing, scoring and baseline numbers so
the two are directly comparable.

**The shim contract:** [RQs/vlmrca/upstream.py](RQs/vlmrca/upstream.py) is the *only*
sanctioned import path into that repo.

- Never `sys.path.insert` to it anywhere else. Import from `vlmrca.upstream`.
- Never modify the upstream repo.
- Why a shim: upstream has no `pyproject.toml` and its package is literally named
  `src`, so `pip install -e` is impossible without editing it and would install a
  package named `src` into the environment. See DD-1.

Task statement, answer format and scoring functions are reused **verbatim**.
That is deliberate — it makes "dashboard 0.6x vs text 0.605" a comparison of
representations rather than of prompt wording.

## Environment

```bash
cd /home/lglsj/CanvasRCA
source venvs/tools/bin/activate
export CANVASRCA_ROOT=/home/lglsj/CanvasRCA
export RL_SLM_RCA_ROOT=/home/lglsj/RL-SLM-RCA-rw_phase2
```

Project-owned environments are `venvs/tools/` for tools and auxiliary package
needs, `venvs/infer/` for inference, and `venvs/train/` for training. API
credentials load from the sibling repo's `.env` via
`vlmrca.vlm.configs.load_env` when that file is present — one set of secrets,
one thing to rotate.

## Data

Raw: `/home/lglsj/CanvasRCA/dataset/raw/{aegislab,aiops2022,aiops2025,rcaeval}`.
Experiments use the processed per-case data under
`/home/lglsj/CanvasRCA/dataset/processed/`.

Evaluation pool is frozen in [configs/case_manifest_480.json](configs/case_manifest_480.json)
(480 cases: 100 aegislab + 100 aiops2022 + 100 aiops2025 + 90 re2_ob + 90 re2_tt,
seed 42). Regenerate or verify with
`python scripts/gen_case_manifest.py [--check]`.

**Dataset difficulty is wildly uneven.** Text-based SOTA per dataset:
AegisLab 0.679 · AIOps-22 0.532 · AIOps-25 0.390 · RE2-OB 0.994 · RE2-TT 0.994.
RE2-OB/TT are saturated — a near-1.0 result there means the pipeline works, not
that the method is better. Claims must rest on AegisLab and the AIOPS sets.

## Invariants

1. **Output format is frozen** — ranked top-5 JSON `{"services": [...], "reason", "confidence"}`,
   parsed and scored with upstream's functions. Do not "improve" it.
2. **The renderer never sees a label.** `compile_dashboard` takes a
   `CaseRenderView`, which structurally has no `ground_truth` field.
   `tests/test_no_leakage.py` enforces this structural boundary, but that check
   is necessary rather than sufficient: every model-visible PNG, OCR string,
   prompt, manifest and metadata field must also exclude raw case IDs, dataset
   names, fault types, absolute times, file paths and label-derived metadata.
   Note that the true service *name* legitimately appears among the candidates
   — what must never appear is anything distinguishing it as the answer.
3. **The renderer is pure and deterministic** in `(view, DashboardConfig)`.
   Seeded layout, sorted iteration. A/B comparisons depend on it.
4. **Every rendering behaviour is a `DashboardConfig` field.** A behaviour without
   a field cannot be ablated, and RQ4 is the ablation matrix.
5. **Image tokens count** in every cost number.
6. **Per-dataset and per-fault breakdowns always.** Any A-vs-B claim rests on a
   paired Wilcoxon signed-rank test (matched by `case_id`) plus Cohen's d, not on
   confidence intervals — per-case MRR stays in every trajectory, so an interval
   is recomputable offline if ever needed, but it is not a reported field.

## Layout

```
RQs/vlmrca/upstream.py the shim (import boundary)
RQs/vlmrca/cache.py    manifest-driven case loading
RQs/vlmrca/render/     dashboard compiler — the contribution
RQs/vlmrca/vlm/        model clients + prompt assembly
RQs/vlmrca/agent/      shared agent infrastructure and trajectory utilities
RQs/vlmrca/eval/       pipeline runner + statistics
scripts/               shared project entry points and infrastructure utilities
configs/               unified configuration used by the main pipeline and every RQ
RQs/<rq>/              descriptions/, results/, scripts/, src/, findings/, configs/
plans/design_decisions.md   shared project-wide design decisions
devlog/                project-wide, non-RQ dated session log
docs/progress_report.md     shared full-project knowledge transfer
```

## Working conventions

Project skills are authored once under `.claude/skills/` for Claude compatibility
and exposed to Codex through the repository discovery alias
`.agents/skills -> ../.claude/skills`. The available skills are **dashboard**
(renderer work), **smoke** (pipeline qualification), **experiment** (registered
cells and configs), **vlm-serve** (self-hosted VLMs), **baseline** (comparison
tables), **agent-trace** (failure analysis), **literature-review** (primary-source
search, verification, and synthesis), plus **devlog**, **status**, and
**design-decision**. Keep the alias intact and edit only the canonical files
under `.claude/skills/`, so the two agents cannot drift onto different rules.

`AGENTS.md -> Codex.md` is the Codex project-guidance entry point. `Codex.md`
remains the single authoritative rules file.

Every material project, research, protocol, implementation, validity, or
next-step decision must be recorded immediately after it is made, together
with the evidence and reasons for choosing it. Do not leave a decision only in
chat, terminal output, or an informal progress update. Record project-wide and
cross-RQ decisions in `plans/design_decisions.md`; record RQ-specific protocol
and preregistration decisions under `RQs/<rq>/descriptions/`; record final RQ
conclusions under `RQs/<rq>/findings/`. When a decision changes or rejects an
earlier decision, preserve history by explicitly superseding the earlier entry
and documenting the consequences and revisit conditions.

Claude-only profiles remain in `.claude/agents/`: **render-reviewer** (vision QA
+ perception probe), **trajectory-analyst** (failure-mode classification), and
**results-analyst** (statistics and paper tables). Codex must use the equivalent
workflow embedded in the project skills and, when useful, an ordinary read-only
subagent; it must not assume that `.claude/agents/` is a Codex discovery path.

Rendering is cheap CPU work; inference is not. Pre-render, then run inference as
a separate resumable job. Iterate at 20 and 100 cases; run 480 only on frozen
configs.

## Project regulations

The following is the CanvasRCA-applicable subset of
[docs/regulations.md](docs/regulations.md). Unless an absolute path is shown,
all paths are relative to `/home/lglsj/CanvasRCA`.

### Runtime and configuration

1. You must use vLLM in project-owned VLM inference through
   `RQs/vlmrca/vlm/client.py`, with model configuration in
   `RQs/vlmrca/vlm/configs.py`. Shared project-owned vLLM launchers belong
   under `scripts/vllm_vlm/`; an RQ-specific launcher belongs under
   `RQs/<rq>/scripts/vllm_vlm/`.

2. You must use FlashAttention in VLM training when it is supported by the
   selected model and multi-image training stack. Any required fallback must be
   recorded explicitly.

3. As the datasets are huge, you need to use more than 1 workers. The maximum
   worker number is 4. When you are using multiple workers, pay attention to CPU
   memory to avoid OOM.

4. For all inferences, we should use the unified inference path
   `RQs/vlmrca/vlm/client.py` and the same configuration to ensure that all
   comparisons are fair, subject only to the explicit
   `gpu_memory_utilization` exception in Runtime and Configuration Rule 5:

   ```yaml
   model_path: models/Qwen3.6-27B
   served_model_name: Qwen/Qwen3.6-27B
   base_url: http://127.0.0.1:8000/v1
   host: 0.0.0.0
   port: 8000
   vllm_python: venvs/infer/bin/python
   dtype: bfloat16
   seed: 42
   generation_config: vllm
   max_model_len: 32768
   max_tokens: 16384
   temperature: 0.0
   top_p: 1.0
   request_timeout_sec: 1800
   wait_timeout_sec: 1800
   async_scheduling: false
   gpu_memory_utilization: 0.65
   max_num_seqs: 8
   tensor_parallel_size: 1
   max_images_per_prompt: 8
   max_videos_per_prompt: 0
   disable_thinking: true
   enable_prefix_caching: false
   enable_chunked_prefill: false
   use_flashinfer_sampler: false
   batch_invariant: false  # Qwen3.6; required because GDN rejects this mode
   cublas_workspace_config: ":4096:8"
   gdn_prefill_backend: triton
   moe_backend: triton
   triton_force_first_config: true
   enforce_eager: true
   trust_remote_code: true
   enable_log_requests: false
   extra_server_args: []
   ```

   Gemma-4-26B-A4B-it must use the same recipe except
   `batch_invariant: true`. vLLM 0.24 supports batch-invariant execution for
   Gemma-4 on the project GPU. Qwen3.6 must keep it disabled because vLLM
   rejects batch-invariant execution for its GDN attention.
   This model-specific compatibility setting is a deterministic runtime
   control, not an experimental arm or a model-quality variable. Every run
   must record and verify its effective value.

   Process identity, shared residency, repeated inference, and exact-output
   repetition are not experimental-validity or comparability criteria. With
   respect to these removed criteria, an otherwise protocol-compliant run is
   assessed through its frozen effective configuration and registered artifact
   hashes, including the model checkpoint, tokenizer, precision, vLLM/runtime
   parameters, prompts, evidence artifacts, output constraints, and scoring
   contract. This rule does not override any other registered protocol,
   integrity, partition, scoring, exclusion, or artifact-status requirement. A
   PID may be recorded only as operational metadata for health checks and
   lifecycle management; it must never enter a validity, comparability, or
   result-acceptance decision.

   Removing or relaxing an operational gate is strictly status-preserving for
   historical experiments unless the user explicitly authorizes a separate
   reclassification. The 2026-08-02 removal of the PID/process-identity and
   exact-repeat gates changes only future execution prerequisites. Every
   pre-existing artifact retains its immediately preceding status and
   evidentiary scope: valid or passed remains valid or passed; invalid, failed,
   superseded, incomplete, or excluded remains so; and pilot, smoke,
   diagnostic, screening, or qualification evidence does not become an
   efficacy or confirmatory result. A successor verifier's inability to parse
   or validate an older schema does not itself invalidate the historical run.
   The gate removal neither invalidates an accepted run nor rehabilitates a
   rejected or superseded run. Future agents must consult the original
   artifact-specific status authority; they must not use a successor
   verifier/schema mismatch to reclassify a predecessor artifact.

   `max_tokens: 16384` is the maximum model-output length for one request.
   Smoke tests and formal experiments must use the same values, including the
   same `max_model_len` and `max_tokens`, except that
   `gpu_memory_utilization` is governed by Runtime and Configuration Rule 5.
   The configuration above must remain synchronized with
   `RQs/vlmrca/vlm/configs.py` and every applicable shared or RQ-specific
   launcher under `scripts/vllm_vlm/` or `RQs/<rq>/scripts/vllm_vlm/`, and each
   run must record its
   effective configuration.

5. All newly launched project-owned vLLM runs must use
   `gpu_memory_utilization: 0.65` by default. `gpu_memory_utilization` is an
   operational vLLM capacity limit, not an experimental variable. Its
   configured value, including a difference between historical and current
   runs, does not determine whether a result is valid and does not affect
   whether results are comparable. A run must not be excluded, invalidated or
   declared incomparable solely because it used a different
   `gpu_memory_utilization` value. The effective value must still be recorded
   for operational reproducibility. OOMs, preemptions, request failures or
   truncations are handled by their existing integrity and error rules; they
   are not converted into model-quality outcomes.

6. Post-training has reached two development-only case-level causal-integration
   SFT pilots. The earlier first-paper roadmap included visual atomic-grounding
   SFT and case-level RCA SFT. The 2026-07-31 controlled follow-up showed that
   most atomic dashboard facts are already readable and that the isolated
   topology edge defect has a renderer intervention; generic visual-grounding
   SFT is therefore not the immediate experiment. The unified CanvasRCA
   training entry point is `python -m vlmrca.training.train`, with project-owned
   training and adapter architecture under `RQs/vlmrca/training/` and frozen
   configurations under `RQs/RQ0/configs/training/`. The first 24-example BF16 LoRA
   pilot failed its paired promotion gate (adapter−base MRR −0.0694). A
   five-service preservation/correction v2.1 then completed 30 training cases
   and another fresh paired gate; it prevented list collapse but still scored
   −0.0417 (zero improvements, one scored degradation, eleven ties). Neither
   checkpoint may be scaled or promoted and no formal/reserve data may be
   opened for them. Before a new learning intervention, freeze the intended
   pod/service evaluation granularity and require a new mechanistic hypothesis,
   fresh development-heldout data, and a paired gate. RL remains reserved for
   the second or third paper rather than the current first-paper phase.

7. The frozen upstream scorer's service-level leniency does not recognize
   ordinary hashed Kubernetes pod names. Historical results retain their
   registered upstream scores. All new CanvasRCA experiments must use
   `vlmrca.eval.scoring.is_granularity_aware_hit`, record that scoring contract,
   accept hashed pod predictions for service-level labels, and keep pod-level
   and node-level labels exact. The upstream repository remains read-only. The
   post-hoc RQ0 sensitivity changed 35/4,320 episode scores but left A−B
   negative for both models, so it must not be cited as rescuing RQ0.

### Experiments

1. When doing experiments, the full conversation history (including tool
   calls) should be recorded in md files. Each case should have a seperate
   conversation history.

2. We should have detailed logs, brief logs and reasoning traces. For detailed
   logs, we should just record every thing. For brief log, we only need to
   display some high-level progress and important messages, along with a tqdm
   bar indicating the current progress. Also, in brief logs, after every 5% of
   progree, a brief summary of metrics such as reward(train only), loss(train
   only), Learning Rate(Train only), AC@1, AC@3, AC@5, AVG@3, AVG@5 and MRR must
   be displayed. Recall@1, Recall@3 and Recall@5 should additionally be
   displayed only when a registered multi-root evaluation applies; for a
   single-root case, Recall@K and AC@K are the same quantity and must not be
   treated as independent evidence. Brief logs are operational monitoring
   artifacts rather than scientific source records: an absent brief log, an
   imperfect reporting cadence, or a missing display field must be recorded as
   an audit warning and repaired when practical, but must not invalidate an
   otherwise complete run whose raw trajectories, per-case records, summary,
   hashes, pairing, and registered metrics pass verification.

3. Metrics to record for each case: Total input tokens, total output tokens,
   total tokens, wall time, status (error or not, and whether any unexpected
   issue, such as a tool failure or implementation bug, occurred during the
   process), AC@1, AC@3, AC@5, AVG@3, AVG@5 and MRR. Recall@1, Recall@3 and
   Recall@5 are additionally recorded only for a registered multi-root
   evaluation.

4. Metrics to record for summarization: Avg input tokens, Avg output tokens, Avg
   total tokens, Avg wall time, Error rate, Avg AC@1, Avg AC@3, Avg AC@5, Avg
   AVG@3, Avg AVG@5 and Avg MRR. Avg Recall@1, Avg Recall@3 and Avg Recall@5
   apply only to a registered multi-root evaluation.

5. Results, logs and conversation histories for an RQ experiment must be
   recorded under `RQs/<rq>/results/<experiment>/`, with trajectories under
   `RQs/<rq>/results/<experiment>/trajectories/`, renders under
   `RQs/<rq>/results/<experiment>/renders/`, and the aggregate summary at
   `RQs/<rq>/results/<experiment>/summary.json`. Result recording must remain
   asynchronous and may run in parallel with training or evaluation; an epoch,
   case or iteration must not block on each individual artifact write. Writers
   must still drain pending writes and verify persistence at the appropriate
   lifecycle boundary.

6. For models trained as part of an RQ experiment, save the best models under
   `RQs/<rq>/results/<experiment>/models/best/` and checkpoints under
   `RQs/<rq>/results/<experiment>/models/checkpoints/`.

7. Experiments (including training and evaluations) should be based on per-case
   data under `dataset/processed/`, not the original raw data under
   `dataset/raw/`. The complete `dataset/` tree is read-only and must not be
   modified.

8. For Python environments, use `venvs/infer/` for inference, `venvs/tools/`
   for tools and auxiliary package needs, and `venvs/train/` for training.

9. `RQs/vlmrca/` is used for storing the shared main and formal pipeline for this
   project, and the main pipeline will be the final structure of the project,
   which will be written in the paper and submitted to top conferences. Before
   you can decide what the main pipeline should be, you write RQs and do
   experiments. Reusable project-wide library code belongs under `RQs/vlmrca/`,
   and reusable project-wide command-line and batch entry points belong under
   `scripts/`. Mutable RQ-specific experiment, analysis, utility, and launcher
   scripts belong under `RQs/<rq>/scripts/`. These shared and experimental
   locations must not be used to bypass the RQ organization rule: only the
   approved, submission-ready RQ-specific implementation belongs under
   `RQs/<rq>/src/`, subject to its freeze rule.

10. Label leakage is strictly prohibited. Label leakage includes the leakage of
    both the absolute injection time (the time when the root cause
    entered/injected/appeared in the system) and the ground truth root cause.
    When doing experiments, make sure that they are only used in the evaluation
    process to judge the answer from the agents, but not known by the agents.
    The registered relative incident anchor `t=0` and relative times around it
    are permitted; the absolute timestamp is not.

11. When the experiment is running, you can watch the experiment lively in a
    regular basis. For example, you can watch the experiment every 6 minutes.
    You don't need to watch the experiment running all the time, otherwise a lot
    of your tokens will be consumed. But at first, when the experiment is not
    running stably, you can watch more frequently. And once it's stable, you can
    then switch to a regular watching mode.

12. All experiments should be running in the background to prevent themselves
    from being interupted.

13. The whole device, including CPU and GPU, used in this experiment are part my
    personal properties, you can use it as you want. There will be no extra
    charges.

14. Do not use quantization for training or inference. SFT must use a
    frozen BF16 or FP16 LoRA configuration through the project-owned training
    entry point under `RQs/vlmrca/training/`; the training process has no
    artificial
    GPU-memory-fraction cap. The canonical vLLM inference runtime remains the
    unquantized BF16 configuration recorded in the Runtime and Configuration
    section with `gpu_memory_utilization=0.65`. A one-pass sequential workflow
    may stop vLLM between stages. For repeated rollout/training cycles or
    parallel workflows, keep vLLM resident and let the uncapped trainer use the
    remaining device memory when measured memory is sufficient; do not
    repeatedly reload the base model. Every such run must record process
    co-residency, peak GPU memory, and the exact adapter version used for each
    rollout.

15. If the training process also involves repeated vLLM inference, then keep
    vLLM live in the background when the measured memory budget permits; don't
    kill it and start it over and over again unnecessarily. An idle vLLM server
    does not perform inference compute, but it still reserves its configured GPU
    memory.

16. Before every full-scale experiment, run a partition-aware three-case
    end-to-end smoke qualification through `scripts/smoke_e2e.py`. Using the
    preregistered seed, select exactly one real case from each of `re2_ob`,
    `aiops2022`, and `aiops2025` from the stage-authorized development
    partition: use `train` for optimizer or training smoke tests and
    `validation` for inference or evaluator smoke tests. Real `aegislab` and
    `re2_tt` cases, synthetic substitutes, `test`, `heldout`, and `unused` cases
    must not be used as smoke or canary inputs. Cases retaining an `.invalid`
    marker must not participate in any experiment. Under dataset split v2, the
    Train Ticket target domain remains fully embargoed until the final frozen
    OOD evaluation, where every eligible real target-domain case is treated as
    a formal evaluation case from its first execution.

    Before any model call or optimizer step, freeze the selection seed, selected
    opaque case IDs, stage-authorized roster and split-assignment hashes, code
    commit, and effective inference or training configuration. An
    inference/evaluator smoke test must exercise the same compiler, renderer,
    `RQs/vlmrca/vlm/client.py` runner, asynchronous writer, evaluator, artifact
    inventory, and post-hoc verifier as its planned full run, using the vLLM
    configuration recorded in the Runtime and Configuration section without
    shortening `max_model_len` or `max_tokens`; only
    `gpu_memory_utilization` may differ under Runtime and Configuration Rule 5
    without affecting validity or comparability. Passing is determined solely
    by protocol, numerical, and infrastructure integrity. Root-cause
    correctness, reward, structured-output acceptance, or the magnitude of a
    finite training loss must never determine smoke-test passage or subsequent
    case selection. Smoke executions belong in isolated registered diagnostic
    roots beneath `RQs/<rq>/results/<registered-smoke-experiment>/` and are
    excluded from formal metrics and model selection.

17. RQs aren't limited to what are written in the roadmap or phase plans. There
    can be sub RQs. Sub RQs are routes to main RQs, or they support main RQs.

18. When doing trajectory sampling, to ensure the diversity of trajectories,
    change temperature to 0.65 and top_p to 0.85.

19. Long-running experiment supervisors must support safe, contract-compatible
    resume. The mere presence of an existing registered output directory or
    operational log is not a reason to reject a run. Resume is allowed only
    when the authoritative call and episode trajectories identify the current
    frozen contract, roster, model, scope, partition and request design, and
    their registered keys are unique and internally consistent. A partially
    completed run continues only missing units; a complete but unverified run
    runs verification only; an already verified run is skipped. Unknown
    artifacts, damaged or duplicate trajectories, stale contracts,
    contradictory completion state, and a completed run with a failed
    verification must fail closed and must never be overwritten or silently
    mixed. A restarted server must match the frozen effective-configuration
    attestation, but its PID is operational metadata only. Server, launcher and
    analysis logs from earlier attempts must be preserved using deterministic
    `.resume-NNN` suffixes, and a valid current-contract analysis must not be
    rewritten.

20. Infrastructure failures must follow the experiment's registered paired-case
    exclusion policy rather than being converted into model errors. If any
    stage or arm for an opaque incident has a recorded infrastructure failure,
    exclude that incident's complete registered arm/condition set from every
    paired analysis for that model and report the incident IDs, excluded count,
    requested count, and resulting fraction. The run may proceed only when that
    case-level fraction is no greater than the frozen maximum; exceeding it
    makes the result incomplete. Parse failures, truncations, and invalid model
    outputs remain model outcomes and are not infrastructure exclusions. Unless
    a stricter threshold is preregistered, the maximum whole-case infrastructure
    exclusion fraction is `0.05`.
    Rule-16 smoke remains a zero-infrastructure-failure qualification because
    its purpose is to qualify the infrastructure itself.

21. Information equality is mandatory for every modality or representation
    comparison. Every compared arm must expose the same incident-specific
    atomic facts, selected from the same source data by the same label-blind
    rules, at the same precision and temporal resolution. This includes the
    complete candidate set and order, every concrete directed call edge and
    multi-hop path fact, every selected metric sequence and its missingness,
    timestamps or relative bins, onset and persistence values, log/trace facts,
    units, fault-window facts, and all legends or semantics needed to interpret
    them. A visual arm may encode a fact redundantly in pixels and text, but a
    text-only or structured arm must still receive that fact explicitly at
    least once.

    Explaining that `A -> B` means "A calls B" is only a notation rule; it is
    not a substitute for supplying the incident's actual `caller -> callee`
    edges. Likewise, baseline/peak/onset summaries are not substitutes for a
    full metric sequence when the visual arm can see the sequence shape. A
    shortened companion summary that omits any visual fact must never be used
    as a text-only baseline. Before any model call, generate a model-visible
    atomic-fact inventory and a `fact_id -> arm location` mapping for every arm;
    after ignoring duplicate encodings within an arm, the inventories must be
    exactly equal. Any mismatch must fail closed. A run that violates this rule
    is invalid for efficacy, modality, representation, or causal claims and
    must not be rehabilitated by a post-hoc disclaimer or analysis.

### Directory paths

1. After completing an RQ milestone, store its experiment log under the
   corresponding `RQs/<rq>/results/<experiment>/` tree. Store only
   project-wide, non-RQ development logs under `devlog/`.

2. The project-level `configs/` directory is reserved exclusively for unified
   configuration used by the main pipeline and all RQs. Examples include the
   frozen common VLM inference/vLLM configuration, the shared evaluation case
   manifest, and the shared upstream pin. An experiment-, training-, or
   RQ-specific configuration must not be stored there; it belongs under
   `RQs/<rq>/configs/`.

3. All content related to an RQ must be stored under `RQs/<rq>/`. Every RQ must
   have the following six required subdirectories:

   - `descriptions/` stores the research question itself and its descriptions,
     protocol, and preregistration material.
   - `results/` stores all experiment-generated outputs, including logs,
     conversations, trajectories, renders, summaries, checkpoints, and trained
     model artifacts.
   - `scripts/` stores mutable or provisional RQ-specific experiment,
     analysis, utility, and launcher scripts. These scripts may be changed
     while the RQ is still in progress, but they are not the finalized source
     submitted with the paper.
   - `src/` stores the finalized RQ-specific scripts and source code intended
     for submission.
   - `findings/` stores the final findings, conclusions, and experiment
     summaries established by the completed RQ.
   - `configs/` stores that RQ's experiment, training, roster, lock, and other
     RQ-specific configuration files. It must not contain unified configuration
     that is shared by the main pipeline and every RQ.

   Until the RQ is complete and its final solution has been settled, `src/` is
   frozen: do not create, modify, move, or delete content inside it. Only after
   the final solution is approved may submission-ready code be placed or
   changed there. Experimental or provisional code must remain in
   `RQs/<rq>/scripts/` and must never be staged in `src/` before that point. Do
   not place RQ-related material in the
   project-level `results/`, `plans/`, `docs/`, or `devlog/` trees.

4. Shared dataset loading and caching code is under `RQs/vlmrca/cache.py`, shared
   inference code is under `RQs/vlmrca/vlm/`, shared evaluation code is under
   `RQs/vlmrca/eval/`, and shared training code is under
   `RQs/vlmrca/training/`. Shared command-line and batch entry points are under
   `scripts/`. RQs and the main pipeline should import and reuse these modules
   without introducing machine-specific paths. Mutable RQ-specific scripts
   belong under `RQs/<rq>/scripts/`; finalized RQ-specific code must follow
   Directory Rule 3 and must not be written before that RQ's `src/` directory
   is unlocked. The project-root `scripts/` directory is the canonical location
   for shared scripts and is not a compatibility symlink. The project-root
   `vlmrca` entry is a compatibility symlink only; canonical shared Python
   package content lives under `RQs/vlmrca/`. New documentation and commands
   must use `scripts/...` for shared entry points and
   `RQs/<rq>/scripts/...` for RQ-specific entry points.

5. The shared base model is stored at the project-relative path
   `models/Qwen3.6-27B`. Models and checkpoints produced by an RQ experiment
   must be saved under that experiment's
   `RQs/<rq>/results/<experiment>/models/` tree as required by Experiment
   Rule 6.

6. A relocation-only migration of configurations, scripts, or result artifacts
   may update stored paths, file hashes, self-hashes, and dependent run
   contracts only when it is documented by a machine-readable migration
   manifest. If that manifest provides the old-to-new mappings and explicitly
   records that model inputs, model/checkpoint, decoding, scoring, and execution
   semantics are unchanged, every historical experiment covered by the
   manifest is deemed to have executed under the migrated contract and remains
   valid and comparable. This rule does not authorize retrospective validation
   of substantive changes to configuration values, code behavior, evidence,
   prompts, models, decoding, or scoring.

## Status

**Current authority as of 2026-08-04:** RQ0 completed 4,320 formal calls and did
not support a static visual-text advantage. RQ1 subsequently produced three
valid negative mechanism results: its operation router failed on the disjoint
Gemma/Qwen gate, RQ1b2 answer-hidden visual composition failed Gemma
development, and RQ1b3's complete two-stage Gemma cell failed all six promotion
requirements after 990/990 calls. DD-34 stops Qwen/gate follow-up for RQ1b3 and
keeps RQ1c/RQ1d, training, reserve, and heldout inference blocked. DD-35 starts
RQ2 static protocol implementation; its initial 16-cell factorial contract and
feasibility checks pass, but **no RQ2 model inference is authorized yet**. See
`docs/2026-08-03_progress_report.md` and `plans/design_decisions.md`. Historical
status notes below are retained as an implementation chronology and must not
override this paragraph.

RQ0 confirmatory inference completed on 2026-07-31 with 4,320 formal calls and
did not support a visual-text-topology accuracy advantage. The subsequent
renderer-v7 topology repair was perceptually qualified but had no stable
cross-model RCA benefit. A development-only case-level causal-integration SFT
pilot then passed all infrastructure gates but failed model promotion: Qwen
base/adapter MRR was 0.5444/0.4750 on 12 disjoint development-heldout cases.
A preservation/correction v2.1 also failed on a fresh 12-case heldout set:
base/adapter MRR was 0.5444/0.5028, with no improvements. Both checkpoints
remain diagnostic under `models/checkpoints/`; no best model was saved and
formal/reserve cases were not used. A later hashed-pod scoring sensitivity left
visual-minus-text negative for both architectures; RQ0 remains unsupported.

M0 scaffold and M1 smoke complete (2026-07-22). vLLM self-hosted path verified
2026-07-23, closing the GPU half of the M0 gate. Decoding made reproducible and
the renderer's text budgets fixed on 2026-07-26 (DD-12, DD-13, DD-14).

| run | model | n | MRR | note |
|---|---|---|---|---|
| RE2-OB | claude-opus-4-7 | 20 | 1.000 | saturated dataset; validates the pipeline |
| AegisLab | claude-sonnet-5 | 20 | 0.797 | text SOTA on this dataset is 0.679 (Opus) |

**Treat every number above as provisional.** All of them predate the 2026-07-26
corrections and none is reproducible as recorded:

- They ran under stochastic decoding. Two Sonnet-5 runs of one config disagreed
  on 5 of 20 cases — a ±0.112 MRR band at n=20, which is most of the margin over
  the text baseline. For the Claude 5 models this is irreducible (DD-14).
- They ran at `RENDERER_VERSION` 1, whose dashboards had a Service index that
  could not disambiguate two services in 95 of 100 AegisLab cases, and panel
  titles clipped past the column edge. Current renders are v4.
- The first open-weight bake-off (8 cells, 2026-07-23/24) is void as a ranking:
  the Gemma cells ran at temperature 1.0 while the Qwens ran greedy.

**The corrected bake-off is done** (2026-07-27): 6 models × 4 arms, AegisLab
n=100, greedy, behind a determinism gate that also holds *across* jobs. 24 usable
arms; 5 excluded on parse rate, all Qwen truncation.

| axis | result |
|---|---|
| `hybrid` vs `text_only` | mean **+0.026**, nothing significant after Bonferroni |
| `image_only` vs `text_only` | **88% of the accuracy on half the tokens** for the 3 models that read charts |
| selector (`cov12` vs `v0`) | 4 of 5 negative, p=0.188 — **no reliable effect** |
| thinking (Qwen) | **unmeasurable** — all three fill any output budget given |

**The gate tested the wrong axis (DD-16).** "The dashboard is the representation"
was operationalised as *more accurate than text*; the measurement supports
*comparably accurate, materially cheaper* — which is the accuracy-vs-tokens
Pareto frontier already named as the M5 deliverable. Failing on accuracy while
passing on efficiency is a result, not a refutation.

**What bounds every one of those numbers:** the whole open panel is 0.17–0.35 MRR
below the AegisLab text SOTA of 0.679 *in every modality*. Whether a dashboard
helps a model that far from competent is not the question the project is asking.

**The metric grid was blank on the sparse datasets, and every result above was
scored against it** (DD-17, 2026-07-28, `RENDERER_VERSION` 5). `metrics_df` is a
pivot over a union timestamp index, so a column carries values only on the
timestamps its own scraper wrote — 8–96 valid samples in a 1064-row AegisLab
frame. `ax.plot` breaks a line at every NaN, so those samples drew nothing; the
scorer meanwhile *preferred* such columns, because three flat baseline points
give a microscopic spread and a `>=999z` score, and the fault band had collapsed
to one sample wide. Three fixes: plot the finite samples with markers when
scarce, require 8 baseline points before trusting a column's own spread (else
borrow its metric family's), and expand the window between samples. Sentinel
share 25% → 21%, band width 2.6% → 37.6%, and **injected-service panel coverage
66% → 77.5%** — the DD-11 pathology fixed itself. This is a live confound for
DD-16: the `image_only` arms were reading a dashboard with an empty metric grid.

**Anomaly onset is now computed and rendered** (DD-18).
`RQs/vlmrca/render/onset.py`
derives per-service onset from binned p95 span latency, with a metric fallback;
`topology="propagation"` (presets `prop12`/`prop30`) replaces the call-graph
thumbnail with services in rows ordered by onset, earliest first, on the metric
panels' own time axis. **The premise that onset ranks the origin better than magnitude was tested and
refuted**: ranking the same services by magnitude finds the injected one at
median rank 2.0 against onset's 5.5 (top-3 79% vs 42%, Wilcoxon p=0.014, n=30
AegisLab). The panel was rebuilt to *select by severity and display by onset* —
rows contain the true cause 83% of the time, and onset is shown because it is
evidence magnitude does not carry, not because it ranks better. Do not describe
"earliest onset" as "most likely cause". **No accuracy claim** — config-effect sd
is 0.36, so n=100 cannot resolve below ~0.10 MRR.

Next, in priority order: **re-run the DD-16 modality comparison** on the fixed
renderer (the old `image_only` number was measured against a blank grid); the
**Sonnet-5 reference** (written, ~$16–20, no GPU, currently held) — the only
thing separating a weak representation from a weak panel; then
**resolution-matched rendering** (Gemma spends 2755 image tokens where Qwen
spends 5074 on the same dashboard, and Gemma is the family that cannot read it);
then M2. `HOT_Z` is now a known-open axis: red fires on 98.5% of AegisLab panels,
but median |z| among selected panels is 17.8 on RE2-OB against 206.8 on
AIOPS-22, so no single constant discriminates and the fix needs its own screening.

### A working note

Six real bugs in the first day's renderer were found by *looking at the rendered
images*, not by tests or metrics — including a coordinate mismatch that made the
dashboard contradict its own ground truth, and a selection failure that filled
every panel with one metric family while the true cause got none. The test suite
passed throughout. Render, look, then measure.

Three more on 2026-07-28, and the same rule caught them: the metric panels were
*empty* on AegisLab and had been for every run to date, which no test noticed
because a blank axes is a valid image. The propagation panel then reproduced the
2026-07-26 class exactly — row names budgeted against the legend's two-column
figure rather than their own gutter, so they overran into the metric grid, and
the onset readouts were clipped by the figure edge. Both were found by rendering
and looking, in the first image.

Four on 2026-07-26, all the same class: **text budgeted without reference to
the container it has to fit in.** Panel titles were cut at a constant 52
characters regardless of column width; legend rows at a constant 26 or 34. The
worst of them made `ts-consign-price-service` and `ts-consign-service` both
render as `ts-cons~-service` with the same index number, in 95 of 100 cases —
so the Service index failed at its only job, silently, for every run to date.
The fix is to derive each budget from the figure geometry. Two lessons: prefer
`_elide_distinct` (collision-aware) to `_elide` for anything a reader must match
against something else, and put the audit field in the manifest
(`ambiguous_names`) so the next such defect is greppable from results instead of
needing another pair of eyes.

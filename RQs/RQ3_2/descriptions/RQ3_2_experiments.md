# RQ3.2 experiment contract

The numerical authority is `RQs/RQ3_2/configs/research_v2.json`; the detailed
scientific preregistration is
`docs/CanvasRCA_RQ3_2_Research_Plan_2026-09-20.md`.

`research_v2.json` supersedes v1 only for execution provenance and artifact
ownership. It records the actually loaded local vLLM configuration, assigns
prompt/image persistence to the shared transaction writer alone, and requires
a terminal qualification-queue state with PID cleanup. Evidence selection,
representations, prompts, scoring, sampling, and experiment matrices are
unchanged. The shared durable ledger remains authoritative, so the successor
does not reset the 40,000-call ceiling.

## Experiments

1. `exp_signal_selection`: ten C-Flat conditions over the 480-case eval pool
   and two models. It separates native/aligned X, backbone retention, signal and
   granularity coverage, strict bilateral pairing, and equal budget expansion.
2. `exp_signal_representation`: P0 and SC each receive C-Contrast, V-Standard,
   V-Contrast, and M-Text; original T, TPV, and SIRCL_TEXT are strong bridges.
3. `exp_signal_mechanisms`: a frozen balanced 100-case hash subset receives
   target/matched removal, grouping, redundant noise, re-anonymization, and two
   independent replicates under C-Contrast and M-Text.
4. `exp_signal_locked_generalization`: after an immutable method/budget lock,
   six fixed methods run on the exposed 360-case test and later on an audited
   unused-event cohort of at most 90 cases.

The registered core maximum is 28,432 calls and the hard RQ ceiling is 40,000.
Every logical call records the full prompt, image bytes when applicable,
conversation, raw response, score, per-case metrics, token split, wall time,
failure class, and atomic completion marker. Attention is disabled.

## Qualification

The qualification queue first executes CPU regression and processor preflight
on one frozen case from RE2-OB, AIOPS-2022, and AIOPS-2025. It then runs one
sequential local smoke for each experiment. Each smoke uses one condition,
three cases, and both models (six calls, never above eighteen). The user has
allocated at most 30 minutes to each experiment-level smoke, including both
model startups, requests, and persistence.

### Successor qualification result

The `qualification_v2` successor completed on 2026-09-20:

- CPU regression: 5/5 tests passed; three real cases prepared; eight
  representative requests passed deterministic construction and processor
  checks; no model call was made.
- All four live smokes completed for Qwen and Gemma, with three registered
  cases per model and experiment (24/24 calls) and no infrastructure failure.
- All 24 completion markers passed artifact-hash audit; 24 prompts, outputs,
  and per-case conversations are present.
- Every prompt records
  `/home/lglsj/CanvasRCA_nibi/configs/vllm_inference_local.yaml` and config hash
  `76778801ff0d83aa401b05c9ba66238165043c609dbec004779861210995d84a`.
- Six visual requests produced six authoritative render files (three unique
  case images shared across models), with no second per-call PNG copy.
- The queue ended with exit code 0, wrote terminal state `complete`, removed
  its PID file, and left no vLLM process running.

Smoke scores are qualification diagnostics, not efficacy findings. The
relation graph can be spatially sparse, but its complete edge ledger remains
legible. That appearance is a registered visual condition rather than an
execution defect; changing it requires an explicit successor representation
condition, not a silent repair.

## Formal execution and restart contract

Formal execution is sequential: prepare eval contexts, selection,
representation, mechanisms, freeze the registered method/budget choice,
prepare test contexts, then locked generalization. Qwen precedes Gemma within
each experiment. The optional unused-event cohort remains unavailable until a
non-null audited manifest is registered; it is not silently substituted.

The atomic `completed/<call_key>.json` written after transaction commit is the
per-`case × condition × model` completion flag. An append-only resume journal
maps the cheap logical identity to that flag. Restart performs only journal
parsing and flag-existence checks: it does not reconstruct evidence, rerender,
retokenize, hash large artifacts, or call the model for completed units. A
whole completed model phase has a separate `phase_complete.<model>.json` flag.
The resume scan has a 900-second hard limit before model startup.

Terminal flags distinguish `complete`, `model_failure`, infrastructure or
implementation `failed`, and intervention `not_applicable`. Every terminal
flag is skipped on restart; failed units are never automatically retried.
Model-output failures retain their committed response and score. A new
infrastructure/implementation failure writes its failure flag, stops further
submission after already active requests drain, and fails the queue for human
inspection instead of repeatedly submitting the same unit or flooding the
remaining matrix with the same defect.

A worst-stage simulation with 5,280 completed units took 0.068 seconds for the
full scan (0.000141 seconds per case), far below the bound. The former request
reconstruction path took 13.6 seconds per selection case and is not used for
formal restart.

### Reviewed request-boundary repair (2026-09-20)

The first formal selection attempt stopped before submission for seven logical
units because cached public log/operation strings contained a Kubernetes DNS
name or UUID.  The already implemented deterministic typed identifier
sanitizer is now applied at the RQ3.2 representation boundary before any text
or pixel carrier is compiled.  It preserves selected facts, numeric values,
units, ordering, and relations while replacing raw infrastructure identifiers
with case-local `DNSxxx`, `UUIDxxx`, or `IPxxx` aliases.  Durable prepared
contexts are intentionally unchanged and do not require regeneration.

Failed units remain terminal by default.  A reviewed repair may append an
explicit `retry_authorized` tombstone to the resume journal; the original
failure flag is archived and only that logical unit becomes pending again.
This mechanism does not retry model-output failures and does not reconstruct
or validate completed requests.  The 29 requests committed before the stop had
no identifier match in their persisted prompts and retain their original
completion state.

An all-dimension CPU check also exposed two branches absent from the single
smoke cell. RQ3.2's typed same-semantics bundle now has an RQ-local
re-anonymization adapter. Evaluator-private removal conditions without a valid
target are persisted as `not_applicable` non-calls, as preregistered, rather
than failing the batch or fabricating evidence.

### Formal request timeout handling (2026-09-20; latest amendment)

The local and portable unified request timeout remains 300 seconds. This is an
operational failure-detection bound; it changes neither prompts, evidence,
decoding, output limits nor scoring. A model-request timeout is now written as
a distinct terminal `request_timeout` unit and skipped on resume without an
automatic retry, while the experiment continues submitting the remaining
registered units. Other infrastructure and implementation failures retain
strict fail-fast behavior: the failure is written, active requests drain,
further submission stops, and the queue awaits review. This narrowly
supersedes the earlier rule that every request timeout also stopped the phase;
it introduces no percentage-based final acceptance rule.

### Bounded context residency (2026-09-21)

Formal execution retains at most eight deserialized per-case contexts in a
thread-safe LRU. Tasks remain case-grouped, so the bound preserves adjacent-arm
reuse while preventing the complete 480-case context corpus and its runtime
representation twins from accumulating in RAM. Eviction changes only object
residency: a later access reloads the same durable pickle and therefore does
not change any evidence, prompt, image, model request, or score. The operational
cap is part of the registered artifact contract but is excluded from the
preparation identity, so this repair neither regenerates contexts nor
invalidates completed calls.

If a stopped process left an exact-scope call-ledger row in `started` without a
terminal logical flag, phase startup changes that ledger row to `interrupted`
in one SQLite transaction. The unfinished logical unit is then retried as a
new, budget-counted attempt. Completed or terminal-flagged units are not
reconstructed or reopened.

For a pure-text selection condition only, an exact live-tokenizer context
overflow activates `RQ32TextCapacityAdapterV1`. It removes reverse-selected
whole fact units while retaining at least one fact in every originally
populated M/R/L/G region, and records both removed IDs and before/after
inventory hashes in the projection. It does not alter visual carriers or
retroactively modify text requests that already fit and completed.

### Fixed-canvas redundant-noise amendment (2026-09-22)

Canvas size, raster scale, font geometry and image-processor configuration are
controlled constants in RQ3.2, not experimental factors. The original
`REDUNDANT_NOISE` intervention admitted the first twelve reservoir facts
without a regional footprint constraint. Five of the 100 registered mechanism
cases could therefore exceed the fixed log-card height in `M_TEXT` even though
the same evidence compiler succeeded elsewhere.

The versioned `region_capped_v2` intervention still admits at most twelve facts
in the frozen, label-blind reservoir order, but at most two may be log facts;
remaining positions are filled by later eligible Metrics or Trace facts. A
CPU audit constructed all 100 registered `M_TEXT` requests successfully: 99
received twelve added facts and one exhausted its public reservoir at eleven.
No canvas, resolution, font, renderer geometry, prompt, model or scorer was
changed.

Because selected evidence can change, the complete `REDUNDANT_NOISE` condition
is re-evaluated under both `C_CONTRAST` and `M_TEXT`. Its logical task identity
is versioned, while an exactly identical request may reuse its content-addressed
prior result; every changed request receives a new model call. Unrelated
mechanism units remain untouched. Predecessor results that no longer match the
new request are retained only as superseded audit evidence.

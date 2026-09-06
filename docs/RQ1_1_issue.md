# RQ1.1 Active Issues

## 2026-09-04 — Full-corpus qualification found two preparation defects before inference

- Status: fixed in the preparation successor; no LLM/VLM call used the affected
  preparation.
- Scope: CPU-only run `rq1_1_v3_rq480_prepared`.
- QA selection: all 1,900 selected questions were answerable, had non-empty
  public supporting facts, and contained no missing answer value. However,
  case-local fallback balanced requested cells rather than realized cells: 369
  questions fell back, P4/R2 had only 44 selected questions, and only 65 of the
  72 P4 `(reasoning difficulty, ordered region path)` cells appeared. The
  successor freezes a response- and label-blind roster-level scheduler that
  chooses only eligible questions and minimizes realized cell counts. On the
  frozen 480-case availability matrix it gives exact 40-per-cell P1 balance,
  13–14 P2, 6–7 P3, and covers all 72 P4 cells; P4/R2 uses all 115 cases where
  dependent bridging is actually available.
- Counterfactual selection: 391/480 nominal placebo PNGs were byte-identical to
  the factual PNG because the selector counted the candidate-set record as
  visible incident evidence. It could therefore swap two IDs that occurred
  only in the external candidate list and nowhere on the dashboard. The
  successor restricts targeted and placebo identities to M/R/L/G evidence
  actually rendered on the dashboard and verifies distinct factual, targeted,
  and placebo image hashes.
- Unaffected components: canonical processed cases, model-visible telemetry
  facts, renderer pixels, SIRCL-style prompt, RCA scorer, model configuration,
  and all direct-RCA representation definitions.
- Disposition: the affected preparation and its first development check are
  deleted rather than retained as reusable results. The corrected three-case
  CPU preparation passed schedule-hash loading, public/private isolation,
  image-distinctness, and the prepared-artifact verifier before a new full
  preparation was authorized.

## 2026-08-27 — Renderer-v14 L-region cannot fit any complete Denum row

- Status: fixed and qualified in protocol revision
  `rq1_1_v7_bounded_denum_viewport`.
- Experiment: `rq1_1_v6_single_stage_formal_469_20260827`.
- Dataset/case: AIOPS-2022, opaque ID `INC-16A4DF199613` (private source identity remains evaluator-only).
- Failure: `RQ1Error: no complete Denum visible row fits registered renderer-v14 L region`.
- Reproduction: the case fails deterministically after `denum_graph_built` when `overlay_denum_log_region` tries to place its registered log rows. The immediately preceding roster case `INC-F5B2E7B7AD42` completes, isolating the failing row.
- Classification: implementation/representation bug, not model behavior. At least one real-case log template expands to more wrapped lines than the fixed L viewport can hold; the current all-or-nothing row policy therefore selects zero rows and aborts.
- Scientific consequence: no model call occurred, so no inference result was invalidated. Formal must not resume until one deterministic bounded projection fits, remains readable, and is used identically by text and visual arms.

### Resolution

The canonical Denum graph still retains the full normalized template, but the
direct-experiment visible row now applies one registered 160-character bound.
An overlong template is replaced by its deterministic prefix plus a shortened
SHA256 marker; both text and visual arms receive that same bounded semantic
row, its `template_truncated` flag, its full template SHA256, and the same
numeric summary fields. This avoids shrinking the entire dashboard, silent
pixel clipping, or giving the text arm a hidden suffix unavailable to vision.

Static qualification passed with hash
`8efb3f67533a349d704fc7b020b3a24dedcf0e239a29c01d3379cfe9ed3659d8`.
The exact failing case was then recompiled end to end: it produced one complete
visible log row, passed semantic round-trip, and generated dashboard SHA256
`08b627ec2a145e9fbc405f5c24675c40d1a34e224c67423054cfc581e1575bad`
without clipping, overlap, natural-identity leakage, or a model call. The 110
partial v6 preparations were produced by predecessor bytes and will be removed
before a fresh v7 run.

Both successor smokes subsequently passed. Direct-RCA run
`rq1_1_v10_denum_viewport_smoke_20260827` and Direct-QA run
`rq1_1_v11_denum_viewport_smoke_20260827` each completed 18/18 aggregate calls
across Qwen3.8 and Gemma. Both had zero infrastructure, parse/schema,
token/context, truncation, timeout, transport, attention, or persistence errors,
and both verifiers passed. All 36 conversations and raw responses were checked;
no additional design or code issue was found.

## 2026-08-27 — First concurrent attention mapping hit a Transformers lazy-import race

- Status: fixed and qualified in protocol revision
  `rq1_1_v8_attention_preemption_safe`.
- Experiment: `rq1_1_v7_single_stage_formal_469_20260827`, Direct-RCA,
  Qwen3.8.
- Cell: opaque case `INC-01874CA0F78F`, arm `V`.
- Failure: `ImportError: cannot import name 'AutoTokenizer' from 'transformers'`.
- Classification: client-side infrastructure/initialization defect, not model
  behavior. The model request completed, but one of four concurrent case workers
  entered the Transformers lazy module while the shared attention text-span
  tokenizer was first being initialized. The failure occurred during
  post-response attention mapping, so the terminal record correctly contains no
  accepted stage or scientific score.
- Scope at detection: 29 completed cells and one infrastructure-error cell;
  all subsequent observed calls were completing normally and vLLM returned HTTP
  200 responses.
- Resolution: the supervisor now initializes the exact registered client-side
  attention-mapping tokenizer before it creates the four case-worker threads.
  The cached tokenizer and all subsequent token mappings are unchanged; only
  the timing of the first lazy import moves out of the concurrent section.
  Static qualification passed at hash
  `52411242bd2fb97851fdbc68db988b2a8f51aa63a452ad852c307c8e999b5b60`.
  Successor smoke `rq1_1_v13_attention_preload_smoke_20260827` completed both
  models 9/9 with no import, infrastructure, attention, parse, truncation,
  transport, context, or persistence error.

## 2026-08-27 — Attention preemption replay killed vLLM and runner flooded terminal errors

- Status: fixed and qualified in protocol revision
  `rq1_1_v8_attention_preemption_safe`.
- Experiment: `rq1_1_v7_single_stage_formal_469_20260827`, Direct-RCA,
  Qwen3.8.
- Failure time: approximately 21:55 EDT.
- Engine root cause: when GPU KV-cache pressure reached 100%, vLLM preempted
  and recomputed prompt positions for an active request. Attention-probe V3
  appended those already captured positions a second time and raised
  `attention-probe prompt positions are missing or duplicated` from inside the
  model forward path. That instrumentation exception terminated EngineCore;
  this was not an OOM and was not caused by model output.
- Runner consequence: the client had no shared-server circuit breaker. After
  vLLM died, four case workers continued traversing the roster and rapidly
  persisted 2,842 infrastructure-error cells before personal monitoring stopped
  the queue. Only 143 records had completed, so the failed inference root is
  ineligible for analysis and will be removed before restart. The completed
  469-case preparation remains byte/hash valid because neither defect affected
  evidence compilation or rendering.

### Resolution

Attention-probe V4 keeps the first K/V observation for each absolute prompt
position and counts later preemption replays without double-counting them. It
also treats probe exceptions as request-local diagnostic failures: the model
forward continues and the affected cell receives no required sidecar, rather
than the entire vLLM engine dying. The formal runner now classifies fatal shared
transport/EngineDead failures, sets a phase-wide circuit breaker, drains current
writes, persists an aborted run summary, exits nonzero, and prevents the shell
queue from starting the next model or experiment. These changes affect only
attention capture and operational failure containment; renderer, evidence,
prompts, arms, model requests, sampling and scoring are unchanged.

The final bounded successor smoke
`rq1_1_v13_attention_preload_smoke_20260827` completed 18/18 calls across
Qwen3.8 and Gemma. Its verifier passed, parse rate was 1.0, and every registered
error class was zero. Review covered all 18 conversations, raw responses,
partial-response captures, V4 raw probes, prefill attention, answer-token
attention, image grids, text mappings, and overlays; every response stopped
normally and no probe target was truncated. The final run contract is
`391a5b67599e5511e4bed98911152cf9ce41741b83b75d60f8d8bd12ec6b4493`.

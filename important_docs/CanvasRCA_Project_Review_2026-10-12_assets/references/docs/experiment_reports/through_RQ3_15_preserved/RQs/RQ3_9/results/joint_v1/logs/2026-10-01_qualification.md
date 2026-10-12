# 2026-10-01 — RQ3.9 implementation and qualification

## Scope and status

User-authorized120-case Qwen-only pilot, four conditions. Current completed
steps: source review, public preparation, CPU qualification and real-image
inspection. GPU smoke has been started; this entry does not claim its passage
or formal launch. Durable supervisor/phase/review artifacts are authoritative.

## What happened

Implemented five modules plus `__init__`, config, local queue and bounded smoke,
and registered the scientific protocol before any model call. Unified
renderer components, operations and historical defaults were not edited.
Public preparation used8 pinned workers and completed120 cases in about25s,
without re-extracting original log/trace tables. Eligibility:106 with
comparison groups,14 no-op cases. The formal queue has480 logical positions
and438 distinct inputs; no-op references are not independent replications.

CPU qualification passed on all120 cases/480 tokenized requests in22.92s;
maximum19176 input tokens plus8192 output fits40960. Three main-dataset
smoke cases and a peer example were inspected in the real image viewer.
All source/geometry/card equality checks passed; no model accuracy gate.

## Preflight fixes, not failed model experiments

The shared runtime parser requires both model recipe definitions even for a
Qwen-only dispatch. Keep the unused Gemma recipe in the projected YAML; do not
load its tokenizer or weights. The rejected preflight YAML was preserved
before correction, with zero model requests. The tools environment lacks
Transformers; processor-only CPU qualification uses the existing infer
environment with `CUDA_VISIBLE_DEVICES` empty. It does not load model weights.
Nested PNG bytes are hashed as image digests rather than JSON-serialized.
Attention is explicitly disabled in the RQ-local launcher.

## Validity and next steps

The earlier assertion that all Metrics have independently stretched0..63
windows was incorrect: the inspected common-frame producer shares bin
boundaries across metrics. Record this correction, not a historical-renderer
failure. Trace/log clocks are not automatically equivalent.

Smoke outcome, actual inputs/responses, writer completion and conversations
must be reviewed before formal launch. Preserve failed/partial artifacts;
never reinterpret small-smoke MRR as scientific evidence. Once qualified,
launch the fixed queue, confirm actual request submission, then stop operator
monitoring as requested. No test360 or automatic expansion.

## GPU qualification completed

12/12 complete,0 infrastructure/model-format failures; supervisor518.31s
including112.15s startup. Inspected all actual input records, full responses,
conversation files and image identity; artifact verifier passed. Scientific
explanation errors remain; no evidence of efficacy inferred. See `../smoke/review.md`
(relative to the experiment root: `smoke/review.md`). The read timeout is not
an absolute streaming-request wall limit: one completed response took403.3s.
All existing inference settings are retained and this limitation is explicit.

## User-requested stop after startup

The user explicitly withheld formal execution and requested shutdown if it
had already started. The formal supervisor had reached readiness and submitted
36 requests. Stop signals disabled further submissions, then the verified
RQ3.9 runner process group was terminated and its owned model service closed.
Verified that supervisor210191, runner210912, server210214 and engine210281
had exited, and port21939 was no longer listening. The supervisor's terminal
status is `interrupted`.

Final read-only accounting:5 complete/done and31 started/interrupted attempts.
All preparation, qualification, completed and partial artifacts are retained.
This is a user interruption, not a scientific failure finding. Formal execution
must wait for a new explicit user instruction; do not restart automatically.

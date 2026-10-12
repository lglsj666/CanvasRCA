# 2026-09-13 — Dual-model tournament qualification review

Status: passed qualification, not efficacy evidence or tournament retirement.
Three precommitted AIOPS training cases, two sequential models, six actual
generation requests, no retries, approximately 244.0 seconds including model
startup/switching. The 18-call/600-second aggregate limits were respected.

All six conversations were reviewed in full: their identical system/task/guide
prefix was read once and byte-identity verified across all six, and every
case-specific candidate list, image reference and complete response was read.
The three real PNGs had already been visually inspected in the linked gallery.
For each case, normalized prompt parts and PNG SHA256 agree across the models.
All precommitted artifact hashes and persisted call-artifact hashes rechecked.
All replies have five distinct in-list IDs, valid JSON, finish_reason=stop,
and 145–206 output tokens. All six attention statuses are disabled_by_protocol.

Qwen input: 18,269–18,372 tokens (16,002 image); Gemma input: 3,433–3,536
(1,091 image). Their native tokenizers/processors differ; the public inputs do
not. Request output ceiling is 8,192 for both. Each model retains its registered
sampling recipe. No optimizer or model-weight change occurred.

The per-phase accounting dictionary is cumulative across the shared SQLite
file: Qwen displays complete=3; after Gemma it displays complete=6. These are
not nine requests. There are three persisted outcomes per model and six total.
Neither model's successes retire cases for the other.

The initial plain shell-background launch left only an empty supervisor log
and the precommitted inputs; no request database, server log or result existed.
A managed persistent command session subsequently ran the unchanged code and
inputs successfully. No scientific repair or model retry was necessary.
The server logs' EngineDeadError text occurs during deliberate post-completion
shutdown/model switching, after all requests and artifacts completed; it is not
a failed inference call.

Both models sometimes misread onset/direction, confuse entity types in their
reason, or cite nonexistent sublabels. These are retained model observations;
JSON validity is not evidence-grounding correctness. Do not correct/resample
these answers or use their correctness to declare qualification passed.

Next: register the full 480-case first round, prepare/review its actual image
gallery, precommit model-specific request manifests, then run Qwen and Gemma
sequentially. No training and no new attention.

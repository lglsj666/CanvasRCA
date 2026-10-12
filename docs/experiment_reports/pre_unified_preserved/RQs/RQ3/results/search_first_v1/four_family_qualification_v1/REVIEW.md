# 2026-09-12 — Four-family live qualification review

Status: **passed interface/persistence qualification; not an efficacy result**.
Eight Qwen3.8 Solver calls on two registered training cases completed in
147.02 seconds including model startup and shutdown. No SFT, RL, validation or
480-case eval call occurred. The same unchanged BF16 local Solver recipe was
used with the RQ3 context-safe 8,192-token output ceiling and attention off.

## Input and artifact checks

- All eight actual text prompts match the committed parts. The exhaustive
  anonymous candidates are text in the prompt, not a candidate-list image.
- Every call has exactly one PNG; its bytes match its reviewed source.
- All selected diagnostic evidence is visual. Text is static task/reading
  guidance plus the public candidate list, with no per-case diagnostic prose.
- All eight conversation files include their complete submitted text, the
  correct image reference and the entire assistant response.
- All eight return `finish_reason=stop`; outputs range 96–199 tokens.
  Input counts range 7,239–7,383, including 3,620 image-associated tokens by
  the unified full-minus-text preflight count. No input/output truncation.
- No attention data was captured: `raw.attention_probe=null`, persisted status
  `disabled_by_protocol`, and no attention directory. Existing older attention
  artifacts were untouched.
- Record/artifact hashes pass the shared audit. See `artifact_review.json`,
  `summary.json`, `qualification.json`, `prompts/`, `trajectories/`, and
  `conversations/`. Accounting records eight complete calls, no failed call.

## Model behavior observed, not qualification failures

These two cases were selected for interface coverage, not representative
performance. The modality condition returns RR 1/0; per-case returns 0/0.5;
evidence-combination and log-only temporal return 0/0. No design is promoted
from this tiny sample. Temporal intentionally uses less evidence and cannot
support a same-content comparison against M/R/L/G.

Some answers contain unsupported claims despite valid JSON. Examples include
confusing node 3049 with the displayed node 5036, describing a five-digit pod
as a service, inferring deployment/call relationships not shown, treating two
adjacent log-bin counts as baseline/fault counts, and diagnosing a root solely
from a zero-baseline disk counter spike. The correct answer in one condition
also contains unsupported claims; correctness alone does not validate reasoning.

The current selection is only the previous CPU qualification's sparse cards,
not the intended high-performance evidence policy. The displayed filesystem/
disk counters and repetitive ordinary request logs are weak contrasts. Next
development should compare public-only source-diverse/contrast selection and
clearer interpretation, not simply scale this eight-call result to eval or
train the Composer to reproduce this selection.

## Operational observations

The first `nohup ... &` shell returned a PID but left no surviving supervisor,
server log, worker log or call. Its exact exit cause was not recovered; do not
label it OOM. An explicitly retained execution session then ran the owned
supervisor successfully. It acquired the GPU lease and stopped its own service
after persistence. Future detached launch needs verified survival, not PID-only
acceptance.

vLLM logged the existing disabled-chunked-prefill warning and an optional
deep_gemm import failure before readiness, then successfully used its selected
backend. Eight HTTP generation requests completed before SIGTERM. The later
EngineDeadError and semaphore warning occurred during owned server teardown,
not during an outstanding generation; they did not damage these saved outputs.
Keep these warnings for operational follow-up, not an accuracy explanation.

## Next step

Register a small representative training subset and bounded policy/prompt
search batches. Keep eval, validation tuning boundaries and TrainTicket
training exclusion. Candidate filtering, if explored, must be public-only and
recorded; the initial successful qualification used the full candidate list.
Do not start full evaluation or training from this qualification alone.

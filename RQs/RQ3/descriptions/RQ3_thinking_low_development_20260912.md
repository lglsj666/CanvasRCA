# 2026-09-12 — DD-SEARCH-11: low-effort thinking, same public visual inputs

Status: corrected twelve-call train-only development batch completed and audited;
not promoted to validation/eval/training. Initial registration made no live call.

## Decision and rationale

The 12 corrected-trace non-thinking outcomes retain A22/A25 MRR .2500/.3750.
Unit correction alone changed none of their reciprocal ranks. Actual responses
still confuse entity owners and interpret abnormal capacity/free-space values
as exhaustion. Test whether more explicit model-generated reasoning helps;
do not assume that longer reasoning is accurate or a faithful computation trace.

Use the official Qwen template's low reasoning effort first, preserving an
8,192-token total completion limit. The current official
[model card](https://huggingface.co/Qwen/Qwen3.8-27B#best-practices) specifies
thinking sampling (1.0/.95, top-k 20, min-p 0, presence penalty 0, repetition
penalty 1). The [vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-27B)
uses the qwen3 reasoning parser and documents effort levels. Both were checked
2026-09-12 against the downloaded model template and installed vLLM protocol.
The recipe's text-serving evidence is not a guarantee of this multimodal task.

This is a joint thinking/template/sampling intervention, not a pure estimate of
reasoning tokens' causal effect. Compared with the completed official
non-thinking recipe, temperature/top-p/presence penalty also change as specified
by the model card. No model weights, processor policy, BF16, context, eager mode,
batching capacity, prompt guide, scorer, candidates or image content change.

## Execution contract

- Exactly the same twelve train cases (six per AIOPS dataset), selected by the
  existing public hash/coverage rule; no validation/eval/TrainTicket data.
- Reuse the corrected trace-unit packet and ranked-eight image, regenerated
  byte-identically and checked before calls. Candidate list only in text.
- One Qwen Solver call per case, four concurrent requests, maximum twelve new
  calls and 3,600 seconds for this development batch. No hidden retries.
- RQ3-local config `search_thinking_low_v1.yaml` selects the local server recipe
  `vllm_search_thinking_low_v1.yaml`; shared YAML and other RQs remain unchanged.
- Explicit request template: enable_thinking=true, preserve_thinking=false,
  reasoning_effort=low. Token preflight must use exactly these same kwargs.
- Top-five enum binding and output scorer unchanged; only final answer JSON
  is scored. A truncated/empty final answer remains a model failure, not a
  transport retry. No attention is collected.
- Preserve reasoning text, answer text, usage, partial stream and complete
  conversation. Report generation timing across reasoning plus answer, and
  separately first-answer arrival. Do not divide answer-only duration by all
  generated tokens.

## Checks and interpretation

Before execution: CPU tests for both reasoning field aliases, normal completion,
reasoning-only length stop, transport failure, template preflight identity,
RQ3 persistence/resume, and shared recipe parity. Full source audit and existing
CPU suite must pass. Preview cohort, facts, candidates, full PNG bytes and all
user/system text must match the trace-unit baseline. The template's additional
low-effort system wording is an explicit treatment, not an evidence change.

After execution: audit all call artifacts, partial/final text, usage, input PNG,
and every conversation. Report per-case changes and all failures. Small sampled
training MRR does not qualify the full objective; no validation/eval/SFT/RL is
automatically authorized by a good number here. Stop owned serving after the
bounded batch; continue development from the actual findings.

Alternatives deferred: xhigh thinking may increase cost without quality; larger
output limits would be a separate intervention. Do not silently lengthen or
resample this batch to obtain complete/correct answers.

## First attempt: runtime mismatch, not an outcome of the intended treatment

202 CPU tests passed and all twelve PNG/packet/prompt projections matched.
`thinking_low_development_v1` completed twelve calls in 248.343 seconds, with
no transport error or length stop. However, server.log proves the sourced
`env_local.sh` overwrote the explicit profile: parser was absent and default
thinking was false. Request kwargs carried the thinking/low-effort template,
but JSON grammar ran without the required reasoning parser. All twelve
reasoning channels are empty. The numeric scores (.3333/.2556) are retained
only as runtime-mismatched diagnostics; they do not estimate thinking utility.
The initial console/RESULT interpretation is superseded by this actual audit.

Fix the shared environment's explicit-selection handling, add sourced-shell
CPU coverage, and verify the live server argv before each new search batch.
Neither default inference YAML nor the prompt/renderer/scorer is changed.
Additive generic reasoning/partial persistence is retained and CPU-tested.
Rerun the same twelve targets once as `thinking_low_development_v2`, max twelve
calls / 3,600 seconds. First-attempt records, hashes and consumed calls remain.
This is repair of an ineffective runtime treatment, not resampling to improve
correctness. No other target, model or arm is added.

## Corrected attempt completed

The sourced-environment regression and live-argv guard pass. Full CPU suite:
**205 passed, 72.81 seconds**, `results/search_first_v1/cpu_thinking_low_v2.xml`.
Five-module source count was 5,982 nonblank/noncomment lines. The actual live
command includes qwen3 reasoning parsing and thinking=true/effort=low.

`thinking_low_development_v2` completed 12/12 calls in **1,146.015 seconds**;
spec `24f2c4499b13085ac2154f5856411ec818265163eceba512cd5c8ecd4f3e11e3`.
All twelve final answers stopped normally, contain five valid distinct IDs,
and have nonempty reasoning saved identically in raw, partial and conversation
artifacts. No new attention; public candidates remain prompt-only. Public
prompt/image inputs match the non-thinking parent exactly; chat-template effort
adds 24 input tokens and is part of the registered joint treatment.

| Training dataset, six cases each | Non-thinking MRR | Thinking MRR | Mean output tokens, non-thinking → thinking |
|---|---:|---:|---:|
| AIOPS-2022 | .2500 | .3333 | 292.5 → 4919.2 |
| AIOPS-2025 | .3750 | .3611 | 253.3 → 5381.0 |

Four reciprocal ranks improve, two worsen and six tie. Output usage grows
16.82×/21.24×, including reasoning plus final answer. This small training
comparison does not justify promoting low-effort thinking: extra generation
does not produce a stable gain across both datasets. Preserve it as a measured
alternative, not a new default. No significance/target claim is made.

All twelve complete generated reasoning streams and final answers were manually
read. They show repeated hypothesis switching, some improved value reading,
but persistent guesses about hosting and resource changes. Generated reasoning
is observable model text, not a faithful readout of hidden computation.
Further investigation should improve the public evidence/identity support
before paying for more extensive thinking. Detailed durable audit and per-case
observations: `results/search_first_v1/thinking_low_development_v2/logs/20260912_review.md`.

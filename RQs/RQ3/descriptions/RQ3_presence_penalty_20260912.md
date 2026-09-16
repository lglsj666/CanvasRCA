# DD-RQ3-SEARCH-38 — Remove only the output presence penalty

2026-09-12. Registered before calls; bounded train-only exploration.

## Question and scope

SEARCH37 does not improve both datasets and is not promoted. Its full answers
retain incorrect owner references and ranking/reason inconsistencies. SEARCH17
already tested reason-first output and did not improve its cohort; do not
repeat that intervention as a new idea. Instead isolate the token presence
penalty in the existing non-thinking request profile.

Use SEARCH34 native24 images and the same additional24 training cases,12 per
AIOPS dataset. New profile `card_nonthinking_unpenalized_v1` changes only
presence_penalty1.5→0. Keep temperature.7, top_p.8, top_k20, min_p0,
repetition_penalty1, seed42, thinking off, output8192, field order, candidate
enum, all text and actual PNG bytes unchanged. No renderer or selection edits.
Shared Solver defaults and older RQs remain unchanged.

## Primary-source check and hypothesis

The [official Qwen3.8 card](https://huggingface.co/Qwen/Qwen3.8-27B#best-practices)
was revisited2026-09-12. It recommends presence1.5 for non-thinking and0 for
thinking, together with different temperatures/top-p. This probe is deliberately
not the entire official thinking recipe; no hidden reasoning is enabled.

[vLLM's sampling reference](https://docs.vllm.ai/en/latest/api/vllm/sampling_params/)
defines presence penalty over tokens already generated. Installed0.24 code
`v1/sample/ops/penalties.py` delegates to `model_executor/layers/utils.py`, which
subtracts presence_penalty times the output-token mask. It does not penalize a
token merely because it appears in the input candidate list. Repetition penalty
is a separate operation and remains neutral at1.

The transfer hypothesis is that repeated ID pieces and recurring evidence words
may be useful in a grounded ranking, whereas novelty pressure may distort them.
This is not established by the documentation or by an anecdotal wrong answer.
Removing the penalty can also increase repetitive output or harm ranking. Test
both quality and cost, preserving all failures. These are implementation/model
sources, not a newly claimed research-paper finding or venue upgrade.

## Checks and execution

Extend actual SDK-serialization CPU coverage across legacy, normal, thinking,
reason-first and new unpenalized profiles; check template, candidate enum,
attention-off persistence and completed-resume behavior. The new profile must
fail outside the authorized search path. Full existing RQ3 CPU suite must pass.
Audit all24 source packets, actual PNG bytes, text, candidate order and reference
requests. Only request adapter name and presence penalty may change. Check source
archives/hashes before inference. Existing image reviews remain applicable only
after actual byte comparison; re-open representative current PNGs as a check.

At most24 new local Solver calls, concurrency4,3600-second development bound.
No attention, Composer, new preparation, validation/eval, SFT or RL. The source
corpus and public pools are reused. Do not retry wrong or truncated answers.
After completion inspect all responses, raw/partial streams, conversations and
accounting. Report paired MRR/AC/AVG, token usage, owner/type references and
ranking/reason inconsistencies. Two per-dataset exploratory Pratt/dz contrasts
share one Holm family. No small training result establishes the final targets.

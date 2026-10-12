# Round 6 — complete remaining cohorts, trace status evidence

This round applies the registered trace-status intervention to every case that
remained after round 5. It adds observed trace status-code distributions where
the public span data contain eligible status evidence, while retaining the
registered metric, log, topology, prompt, candidate and inference contracts.
No attention or training is enabled.

The registered cohorts are all 232 unresolved Qwen cases and all 212
unresolved Gemma cases; their union contains 278 distinct cases. The gallery
was generated before inference. All 278 cases passed the source, prompt,
candidate, fact-binding, clipping, geometry and leakage CPU checks. The trace
region changed in 118 cases and the metric and log regions did not change.

Five actual generated dashboards were opened, one from each dataset:
INC-D9ABFB644D29, INC-7558C271EC45, INC-D02CFDF1A4AE,
INC-1C4333C351B0 and INC-51538C347B49. The status rows preserve the observed
bins and counts and explicitly identify the values as source status and
observed span count rather than latency. No overlap, clipping or leakage was
observed. INC-51538C347B49 has no eligible status evidence and serves as an
unchanged control.

Exact model-visible-input matching against retained rounds found 130 reusable
Qwen targets and 125 reusable Gemma targets. These are genuine unchanged
inputs, not method-name matches. They retain their earlier model outputs and
do not initiate another request. The round therefore requires 102 new Qwen
calls and 87 new Gemma calls while preserving all 444 logical targets in the
round accounting.

## Verified completion

Both registered cohorts committed and the post-run audit passed all 444
logical outcomes, including 255 exact-input reuses and 189 new model calls.
All outcomes are complete with normal `stop` finish reasons. Qwen produced no
new top-1 hits; Gemma produced seven. There were no missing records, parse
failures, length failures or infrastructure failures.

Cumulative top-1 union after this round is 248/480 for Qwen and 275/480 for
Gemma, leaving 232 and 205 cases respectively. Qwen coverage by dataset remains
AegisLab 65, AIOPS-2022 29, AIOPS-2025 34, RE2-OB 60 and RE2-TT 60. Gemma
coverage is respectively 75, 38, 38, 62 and 62. Neither model meets the
per-dataset 80% stopping contract.

Paired case INC-C58423A7459F was inspected by reading both complete
conversations, checking the persisted artifacts and opening the exact shared
PNG. The image contains the registered trace-status rows without clipping or
leakage. Gemma ranks accepted service 975 first using its two operation-level
trace rows, whereas Qwen ranks pod 59979 first from a downstream payment-error
log and omits 975 from its top five. This is a model evidence-selection and
reasoning difference on the same visible input, not a prompt, renderer,
persistence or scoring defect.

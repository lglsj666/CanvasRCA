# Round 2 — complete remaining cohorts, reset v3

2026-09-13. Adaptive elimination discovery, no training, no attention.

Registration: `5884eda4e0cdfdb8b1054def7f566262f4820fae67006a214f4a73036a1ea987`.
Qwen 314 cases; Gemma 345 cases; 385 distinct cases, 274 shared cases.
Every target is unresolved after preserved round 1, with no omissions and no
already-solved cases. The register now rejects partial new-round cohorts.

Rounds 2–10 of the preceding run were deleted on the user's explicit request.
Their results, request caches, registrations and derived success state are not
reused. The deletion removed 25,548 files / 5,232,731,446 bytes; all 14,976
protected round-1/pool files retain their bytes. See the adjacent reset audit.

The selector is the unchanged vendored native BARO signed-maximum RobustScorer,
with the previously tested finite-value adapter and 24 selected metric panels.
Native score is selection-only; the model sees measured telemetry rather than
a score-generated root recommendation. Prompt, candidate mapping, renderer,
R/L anchors, model-specific recipes and actual 8192 output-token ceiling remain.
The full-remaining change is a cohort policy, not a new algorithm. No model call
will be made before the all-gallery audit and actual-PNG review.

72 CPU tests passed in 9.58 seconds, including full-cohort enforcement,
model-asymmetric retirement, resume after one model commits, original recipe
equality for all five successor method configs, and renderer regressions.
The source/config snapshot will be made after final pre-call checks.

## Pre-call audit and launch

All 385 unique galleries passed full source/fact/candidate/prompt/geometry
checks. All 385 change selected metric panels and actual pixels versus round 1;
trace and log selections remain unchanged. Source audit: 6,260 functional lines;
14 parent integrity checks passed. Five actual PNGs were opened, one per
dataset: INC-91CC9D691CA8, INC-358CBE8D4527, INC-C2222DBA0446,
INC-C17A00DC78FC and INC-FCEC7B343F4C. Fine metric labels remain dense; no
observed new clipping or outer-card collision. This visual review is sampled;
the inference cohort is not. The native tool parity suite adds 23 passing tests.

The new second round submits 314 Qwen and 345 Gemma requests, without importing
any deleted result. Both work specs were checked against the complete
first-round failure sets. The 181-file source/config snapshot SHA256 is
`fc00c9f845c7e120d47e90e2a96d196f345e0b73d1fe228f70e9375f62f2eac8`.
Qwen spec: `98eaf60fc3e5794b687448d39ef683976ae7e77aff150ddb8d59f8138201c9fe`.
Gemma spec: `5e77ecf8517d9d51d041995dc8bedeb8d9110bd9619823b5d452a9cbb92d59f8`.
Owned sequential execution is recorded in `launch.json` and `supervisor.log`.

## First Qwen in-run semantic check

At the first ten-minute check, 54/314 outcomes were complete and no infrastructure
failure was present. Hash-selected completed case INC-133324A21C16 was checked:
the entire conversation and exact persisted PNG were read, and its artifact
inventory passed. Record `2a842674a0cf9122b3a9277e5f3824512d934737fa7d56faa3acd3519e537327`.
The reply is valid JSON, stop finish, 165 output tokens. It assigns the printed
9.75→176 ms trace row to 372 although the row's owner is 348; it also assigns
M08 to 372 although M08 is owned by 363. The diagram really contains 544→372,
but the claimed 217/544 latency comparisons are not supported as stated.
This is a model grounding/perception failure in an intact recorded input, not
an omitted case, response-storage failure or authorization to retry the answer.
The method and full cohort continue unchanged.

## Completed full round

Both model phases completed and committed all targets. Qwen: 314/314, 24 new
top-1 successes, all stop finishes. Gemma: 345/345, 37 new top-1 successes,
342 normal outputs and three model failures (two length finishes at 8192 and
one unknown/duplicate-ID output). No answer was retried for correctness. The
complete raw failures remain. This leaves Qwen 290 and Gemma 308 unresolved;
next round must include exactly those sets, not a sample of them.

Read Gemma's entire conversation for the same INC-133324A21C16 after Qwen's
review. It calls 585 the earliest onset although that ID does not appear in
the displayed onset list, treats trace owners 217/544/568 as outbound operations
of 585, and assigns parent/callee relations not supported by the shown graph.
This is an intact-input grounding failure, not a new renderer/source change.
The paired inputs will also be compared by the full post-run artifact audit.

Final audit passed: all 659 outcomes and source/request/response artifacts,
including identical model-visible inputs for all 274 shared cases. Exactly 659
new model calls, zero reused deleted responses, 6,931,964 input tokens and
128,618 output tokens. Per-case AC@1/3/5 method maps are committed. Detailed
per-dataset descriptive results remain in `analysis.json`; shrinking-cohort
MRR is not the accuracy of one method on the original full population.

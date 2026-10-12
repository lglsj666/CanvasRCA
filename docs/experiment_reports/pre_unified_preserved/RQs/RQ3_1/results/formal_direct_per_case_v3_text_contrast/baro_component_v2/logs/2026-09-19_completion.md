# 2026-09-19 — BARO CPU baseline NaN repair

## Scope and status

RQ3.1 auxiliary zero-LLM baseline, test360, complete.  Artifact hash:
`a853e5925a8df108ef6c403481931e5f42e77b6f87980df17f08712da1d0df69`.

## What happened

The predecessor adapter bypassed BARO's original forward-fill/zero-fill input
boundary.  A versioned successor recomputed all 360 rankings from canonical
processed metrics with eight core-pinned CPU workers.  It made zero model calls
and completed in 103.48 seconds.  All 360 records and hashes verified.

Pooled results: MRR 0.26264, AC@1 0.13333, AC@3 0.33889, AC@5 0.53056.
The corrected ranking changed in 157 cases and its top five changed in 117.

## Validity and caveats

No whole-case metric column was entirely NaN.  There were 295,007 missing
cells across 211 cases.  All 149 NaN-free cases reproduced their predecessor
ranking exactly.  BARO's zero fill is retained for fidelity to the vendored
input procedure; it is a baseline behavior, not CanvasRCA's missingness rule.
The old embedded rankings remain audit-only.

## Decisions

Use only `BARO_COMPONENT_V2_ORIGINAL_NAN_PREPROCESS` in formal statistics.
Preserve all 5,760 completed Qwen/Gemma final-test records without rerun.

## Blockers

None for this auxiliary baseline.

## Next steps

Include this versioned summary in the RQ3.1 statistical synthesis and exclude
the predecessor BARO ranking from reported comparisons.

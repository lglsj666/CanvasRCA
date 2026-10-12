# SEARCH38 — Output presence penalty only

Completed 24/24 train-only calls in 389.09 seconds, no infrastructure/schema
failures or truncations. The original attempted shell launch created no call;
the detached supervisor subsequently completed normally. Both datasets have
12 fixed training cases, unchanged from SEARCH34. All 48 paired records,
conversations, request envelopes and scorer outputs were audited. Exact PNG,
packet and prompt reuse passed; only presence_penalty 1.5→0 changed.

| Dataset | Reference MRR | No-penalty MRR | Repair/break/tie | Output tokens reference→new |
|---|---:|---:|---|---:|
| AIOPS-2022 | .423611 | .433333 | 3/2/7 | 252.08→281.25 |
| AIOPS-2025 | .298611 | .269444 | 1/2/9 | 261.17→302.92 |

Both exploratory Holm-adjusted p values are 1.0. Input tokens are unchanged;
maximum new output is 411 tokens. Do not promote this variant: no common
quality or cost gain. Retain the original non-thinking profile for the next
selection contrast. The complete metrics/fault/granularity tables are in
metrics_breakdown.json; paired statistics in paired_review.json.

All 24 new complete answers were read. Recurrent errors remain: inferring
exhaustion from small changes or large standardized deviations, inventing
hosting and propagation, and treating the reporter of a connection failure as
the origin. Correct rankings can also have unsupported reasons. These are
model behaviors, not grounds to rewrite scores or retry until correct.

Next: examine a peer-relative selection mechanism on public statistics. Do not
blindly convert counters to rates based on metric names: source series may
already be transformed, and a name alone does not establish counter semantics.

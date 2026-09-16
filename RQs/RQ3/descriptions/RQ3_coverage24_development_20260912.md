# RQ3 broader visual evidence — 2026-09-12

Completed: 48 calls, 402.127 seconds, no infrastructure failures or truncations;
two unknown-ID model answers remain failures. No stable improvement; no
promotion. [Full review](../results/search_first_v1/coverage24_development_v1/logs/20260912_review.md).

DD-RQ3-SEARCH-8: adopt a train-only coverage/density test, not model training.
The same twelve publicly selected training cases have 55–63 metric entities
per case. An eight-series display misses many entities. Test 24 series with
the existing ranked and coverage policies, without any private-label input.
Both policies still operate on the full preserved evidence pool. Traces,
logs and edge counts retain the previous rule; priority may change with the
newly selected entities, and the exact resulting facts are audited.

Use one 12×12 canvas, measured pixel capacity, and an explicit continuous
layout request allocating .65 of height to the full-width metrics card and
the bottom row to R/L/G. The feasible-layout projection must preserve all
selected facts and the actual projection is recorded. No hidden fact removal
is allowed to fit the image. This changes both coverage and spatial allocation
relative to the old eight-series display; comparisons to it describe a
pipeline intervention, not an isolated causal effect of metric count.

Cross both policies with the inherited prompt and the legacy/model-card
non-thinking request recipes. Maximum 48 new Solver calls, four concurrent,
one-hour bound. Same public candidate list in prompt text only. No new
attention, Composer training, validation or eval. The concise prompt's
negative results remain recorded; it is not used here.

CPU rendering, source bindings, exact fact inventory, clipping, PNG inspection
and live context preflight precede scoring. Preserve unrenderable cases as
development failures rather than replacing them by easier examples. Diagnose
genuine implementation errors; do not count them as model-quality outcomes.
If this canvas exceeds actual model context, stop its requests rather than
silently crop or drop facts. Estimated image cost is not a preflight substitute.

Report both datasets, failures and input/output costs, alongside the earlier
eight-series results. This cohort is reused training feedback, not a held-out
estimate. Root-associated coverage analysis stays evaluator-private.

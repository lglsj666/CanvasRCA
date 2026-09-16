# RQ3 trace-unit successor — 2026-09-12

## DD-RQ3-SEARCH-10: explicit Jaeger duration display units

Status: provisional train-only correctness correction; no old artifact rewrite.
Inspection found that the vendored AIOPS-2022 and AIOPS-2025 processors rename
Jaeger `duration` to `duration_ms` without scaling. Jaeger's official v1.60.0
[`model/json/model.go`](https://github.com/jaegertracing/jaeger/blob/v1.60.0/model/json/model.go)
declares duration in microseconds. AIOPS trace timestamps and durations are
different fields and need not use the same units. Sampled processed normal
span durations are thousands of source units, not necessarily seconds of RPC.

New RQ3 search uses `jaeger_us_to_ms_v1` only for these two inherited AIOPS
sources. Selected exclusive baseline/current p95 and inclusive current p95
are divided by 1,000 before painting as milliseconds. New fact IDs bind those
derived values to the original selected facts. Counts, native selection,
source-scale smoothed fold scores, time windows, entity mapping, candidates,
other modalities and the corpus remain unchanged. Applying the projection
twice, to an unqualified dataset/compiler, corrupt inventory or invalid
durations must fail. This is not a magnitude-based unit-guessing heuristic.

The scope is the current RQ3 successor; old RQ1.1/RQ2.1/SFT/source records are
not silently regenerated, rescored or reclassified. This audit does not claim
that incorrect unit labels explain all previous RCA errors or alter the task's
private root labels. Other metric-unit conventions need separate verification.

Three generic functions (language-linear LoRA target discovery, RNG seeding,
sampled-ID logprob extraction) move unchanged to shared training utilities.
No RQ policy, dataset selection or reward logic moves there. Existing RQ3
imports and CPU tests retain their APIs; no existing model/checkpoint changes.
This keeps the actual five-module implementation within 6,000 lines.

## Bounded development design

Use the same twelve train cases and ranked-eight selection as the evidence-bound
batch, model-card non-thinking recipe, unchanged full public candidates in the
prompt only, same static task/guide, same top-five enum and scorer. At most
12 new Solver calls, four concurrent, 3,600-second batch ceiling; no attention.
Compare to the already completed matching twelve answers without rerunning them.
CPU checks and source-unit audit precede gallery inspection and inference.
All actual images, prompts, complete responses, conversations and costs persist.

This isolates the trace numeric-unit projection within the current pipeline;
rendered pixel geometry may change when the numeric labels and logarithmic
positions change. Sampling is not byte-repeatable. Do not claim a target or
generalization improvement from twelve repeatedly exposed training cases.
No Composer generation, SFT/RL, validation or 480-case evaluation is authorized
by this batch registration.

## Completed development outcome

Source audit passed: 16 matched raw/processed spans across two existing train
cases, plus AIOPS-2025 raw startTime/startTimeMillis scale agreement. Full CPU
regression: 171 passed; source layout: 5,991 counted lines. The audit's pandas
C CSV parser segfaulted twice; the read-only audit then completed with Python's
CSV iterator. This was not a model request, an OOM diagnosis, or a change to
the raw-data processor. An unsupported nested YAML inheritance attempt also
stopped before gallery generation; the new config now directly extends rq3.yaml.

Twelve gallery targets passed exact non-R pixel, full-prompt and candidate
identity checks. Two actual full-resolution PNGs were opened manually. All
twelve calls completed in 172.51 seconds, with complete responses/conversations,
no truncation, no infrastructure failure and five legal IDs each. All twelve
per-case RR values were unchanged versus matching prior inputs: A22 .2500,
A25 .3750. Input means remain 6,350/6,244; output means increased to 292.5/253.3.
Keep the correct unit projection, but do not promote this pipeline as meeting
the MRR objective. Full review is in
`../results/search_first_v1/trace_units_development_v1/logs/20260912_review.md`.

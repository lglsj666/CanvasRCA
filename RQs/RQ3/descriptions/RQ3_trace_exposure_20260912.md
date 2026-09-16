# DD-RQ3-SEARCH-25 — Observed span rates with explicit period durations

Date2026-09-12; prospective train-development registration, before new calls.
Question: does distinguishing observed event totals from duration-normalized
rates reduce incorrect traffic-drop explanations while keeping local latency,
resource curves and all other selected evidence available?

## Evidence and interpretation
The read-only24-case public audit found88 selected operations with22 finite
trace observation ranges. Several current periods are much shorter than their
baseline complements. A raw total is valid as a count, but its direction need
not match a rate's direction. The audit at
`results/search_first_v1/trace_exposure_cpu_audit_20260912.json` is public-only;
it does not change historical artifacts or establish an RCA benefit.

[Prometheus documentation](https://prometheus.io/docs/prometheus/latest/querying/functions/#rate)
distinguishes elapsed-time-normalized counter rates from total increases.
This is supporting measurement vocabulary, NOT a claim that our span-event
formula reproduces PromQL rate(), which also handles counter resets and
extrapolation. We use timestamped events, not a cumulative metric counter.
An attempted OpenTelemetry HTTP-attribute page lookup failed and supplies no
claim here. No new paper/venue is inferred from this documentation.

## Registered successor
Use the same24 isolated training cases and SEARCH23 owner-header reference,
node_overview_v1, source metric values, trace selection, public analysis split,
log projection, G/membership, full prompt candidates and one-image shape.
Add duration-normalized observed span rates to R; preserve raw span counts,
exclusive p95 and native fold scores. This is an explicit derived-statistic
and corresponding visual/static-reading-guide intervention, not a claim of
pixel identity or pure prompt-only effects. No changes to the corpus/selector.

For finite public source trace timestamps spanning[a,b] and the unchanged
public current interval[s,e], current duration is length([a,b]∩[s,e]); baseline
duration is (b-a)-current duration, matching the existing complement split.
Compute baseline/current observed spans per minute as count×60/duration.
Both positive durations are mandatory where any trace row is selected.
With zero baseline count, print no finite ratio; never use a pseudocount to
fabricate a rate ratio. If there are no selected trace rows, retain the
existing explicit empty trace evidence; no rate is invented.

Display both relative durations and rate/count/latency rows. These are observed
span rates over the source range, not known true request throughput; sampling
or instrumentation can affect them. No absolute timestamp, injection time,
dataset, natural entity ID or private root enters model input. The denominator
must come from the same public trace frame, never from this offline audit file.

## Checks and execution
Keep all historical paths immutable. Source/packet binding, finite durations,
zero counts, disjoint/outside intervals, deterministic replay, no aliasing,
rate values, complete labels, context and actual PNGs are checked before calls.
Verify non-R packet facts, candidates and non-R pixels unchanged versus the
registered reference; duration metadata must not change metric coordinates.
Preserve all failed attempts and all model responses, without correctness retries.

Run at most24 Solver calls, concurrency4, bound3600 seconds, sequential local
owned server, existing card_nonthinking_v1, output8192, no attention. Inspect
all answers/partials/inputs and classify all results. Paired exploratory
statistics have one contrast per dataset, Holm across those2; no CI. Report
each dataset's MRR, tokens, repairs/breaks/ties. No validation/eval/Composer,
SFT/RL or target-attainment claim follows automatically from this batch.

## CPU implementation review
305 tests passed in78.48 seconds; targeted31 passed. Five existing state/cohort
test bodies moved out of the six core modules, with only imports qualified;
the first collection attempt revealed an incorrect load_config import, fixed
before execution. Its failed XML remains. Core source count5967.

Initial gallery replay compared an in-memory dataclass manifest to JSON using
raw Python equality: tuple/list differences triggered an audit failure. A
separate recursive inspection proved exact PNG bytes and only those12 type
differences. The audit now compares canonical serialization hashes, the actual
persisted representation; it does not remove fields or relax pixel checks.
No model calls occurred before this diagnosis. All prior images remain intact.

All24 source/pixel replays subsequently passed. Every native reference PNG
remains byte-identical under the current renderer; non-R pixels/facts and all
candidate enumerations are unchanged.22 cases have selected trace rows and
changed trace pixels;2 no-trace cases retain their images. Actual PNGs284E,
C6AD and sparse0917 were opened; the viewer downsized the full images, so this
is not a native-resolution glyph-readability guarantee. The sparse predecessor's
unused topology space remains rather than introducing an unregistered layout
change. See trace_rates_gallery_v1/cpu_review.json and review.json. Proceed
only with the registered24 train calls, retaining all outputs and failures.

## Completion decision
All24 completed in368.084 seconds. Actual requests/partials/conversations,
runtime and raw outputs passed audit; all24 complete answers were read.
Largest output388; no infrastructure or truncation errors. A22 MRR
.506944→.479167 (one repair,one break); A25 .440278→.440278 (all ties).
Both exploratory Holm p=1. Input+123 static-guide tokens, image tokens
unchanged. Do not promote; keep native reference and every attempted outcome.
See trace_rates_development_v1/paired_review.json and logs/20260912_review.md.
No validation/eval or training ran; targets remain unmet.

# Round 3: SIRCL support/confidence trace selection

Status: registered; CPU/gallery review before model calls.
Method: `SIRCL_TRACE_SC8_tournament_v1`; config `tournament_trace_sc8_v1.yaml`.
No training or attention. Fixed tournament prompt and model recipes unchanged.

## Evidence and source distinction

Round 2 BARO found four new Qwen and ten new Gemma top-1 successes, but also
degraded partial hits. Earlier trace-oriented search had complementary gains
on AIOPS-2025 and harmed some resource-driven AIOPS-2022 cases. This round
tests a different ranking of eight trace operations while retaining the original
top-eight metrics plus node CPU/memory overview, logs and graph context.

[TraceRCA, IWQoS 2021](https://netman.aiops.org/wp-content/uploads/2021/05/1570705191.pdf)
mines abnormal-versus-normal trace coverage and combines suspicious service
sets with invocation direction. Its benchmark/production experiments and
feature-selection/noise/sampling studies motivate testing occurrence patterns,
not assuming a large latency magnitude is always a local cause. Its full
multi-metric anomaly detection, set mining and service scoring are not run here.
[Original authors' code](https://github.com/NetManAIOps/TraceRCA) and
[conference program](https://duetone.org/iwqos21/iwqos21-program-at-a-glance.pdf)
verify identity and venue, not the equivalence of SIRCL's component.

Instead reuse the already byte-copied SIRCL `tracerca_scorer.py` component
under `packages/rq21_native/`, without rewriting its algorithm. It marks spans
at or above baseline mean + 3 population standard deviations, then ranks
operations by the harmonic mean of abnormal support and confidence. Its field
is called `jaccard`, but the value is the harmonic mean; do not mislabel this a
complete TraceRCA reproduction. An unchanged constant-duration operation can
qualify because the native comparison is >=; preserve and explicitly test this
behavior rather than silently changing the algorithm to obtain better scores.

## Registered adaptation and constraints

Normalize only public span clocks using the existing resolver. Use the same
telemetry-derived analysis interval and restrict the input table to its end;
never use physical injection time. Supply `_rq21_time_s` to the existing adapted
timestamp helper. Missing operations become `default`; nonfinite-time and
missing-owner rows are excluded with counts. Baseline/current span durations
retain their common native unit, which cancels in the threshold comparison.

Run the copied algorithm on the full public trace table. Map operation results
to the same public numeric identities and existing trace-pool facts. Reject
ambiguous compound identities. Record native operations outside the inherited
TRC-L eligible pool; these are not falsely claimed as displayed. Select eight
eligible native-ranked operations, filling a short list from original TRC-L
order with explicit IDs. Preserve all existing count/latency facts; apply the
already verified display-unit projection afterward. No native suspicion score
is exposed as a root-cause recommendation. Rendering order remains parent
entry order, not an unannounced native rank hint.

This is a compound trace selection/capacity intervention; graph subset may
change through the selected owners. It does not claim fixed fact equality with
prior rounds. Both models get identical public inputs for shared cases.
Use 12 currently eligible cases per primary dataset and three per RE2, sorted
by SHA256([42, opaque ID]), independently per model and frozen before calls.
Completed cases never repeat. Errors cannot trigger correctness resampling.

Validate native differential/scale/constant/missing/collision cases, eight-row
selection, pool immutability and actual rendered source bindings. Inspect the
native unbound/fill rates and actual PNGs before inference. If the existing
pool prevents substantive native selection, address that publicly reproducible
representation limitation before launching rather than calling a no-op a new
algorithm. Original sources, processed pools and old results remain untouched.

## Pre-execution checks and no-op reuse

Registration `round_0003`, hash
`278ce0b631a09c8a757db40b0391ab4ff51571685b2d9c05460ac02f519559aa`:
42 cases per model, 55 distinct images. Native selection changes trace sets and
pixels in 53/55 cases; even compared with the old top-eight rather than top-four
TRC-L list, 53/55 selected sets differ. Metric selection stays unchanged.
Native rank / pool-unbound / selected / fill totals respectively:
AegisLab 2157/810/126/2; AIOPS-2022 1626/699/128/0;
AIOPS-2025 235/79/98/6; RE2-OB 141/47/32/0; RE2-TT 371/109/32/0.
Unbound native rows are an explicit inherited representation limit, not added
model facts. The current selector is nevertheless a substantive intervention.

Two model-specific targets have the exact same image and text as round 1:
Gemma `INC-17615889CDA7`; Qwen `INC-BE6A1C89D45F`. They reuse their original
responses (including wrong rankings), with original call identity and byte-exact
artifact copies. Runtime verifies the complete model/server/schema/adapter and
message envelope before accepting reuse; mismatch fails rather than calling a
different input an alias. Thus there are 84 logical outcomes but at most 82 new
calls. No correctness resampling, original-record rewriting or new attention.

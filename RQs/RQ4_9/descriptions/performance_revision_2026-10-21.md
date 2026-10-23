# Paused-run performance revision — 2026-10-21

The user requested acceleration of the six conditions shown in the runtime
comparison: S_VIS_REDIST, S_EVID_REDIST, S_SUPPRESS, S_SHAM_REDIST, P_FULL and
F_LOCAL_MEAN. The latest user target is **either every call at most 20 seconds OR average GPU
utilization at least 82%**. The average covers the full first-invocation to
last-completion interval, including encoding, prefill, decode, admission, queue
wait and drain; model loading is reported separately. No selective high-load
window is used for acceptance. The earlier 20-second-only results remain intact. All 23 scientific conditions remain registered. Formal
execution stays paused at 178 committed positions (153 new formal generations
and 25 exact qualification references); this revision does not authorize resume.

The original mixed-batch measurements include queue interference. They establish
the operational problem but are not isolated per-arm benchmarks. In the observed
window the CPU ready queue contained 16 inputs and no thermal-throttle event was
reported. The four sink conditions perform additional work in 15 full-attention
layers on every decoded token; native attention plus a separate Python/FP32
correction, head-expanded KV copies and repeated host scalar reads were costly.

The operational successor preserves weights, BF16 inputs, FP32 accumulations,
all tokens, original gates and MRoPE, thresholds, query/layer coverage, sampling,
output ceilings and all prior outputs. It:

- reads native paged KV without expanding every grouped-query head;
- computes QK logits, redistribution and decode weighted corrections using GPU
  kernels, with FP32 logits/softmax/accumulation;
- accumulates passive intervention totals on-device and transfers them at commit;
- loads immutable protocol policy once per installed layer, outside decode;
- leaves source compilation, dashboards, facts, prompts and scoring unchanged.

Floating-point reduction order may differ. Independent tensor checks compare
actual deltas and audit values against the original probability implementation;
this is numerical equivalence within registered tolerances, not a promise of
identical sampled text. Each new record names the new runtime revision. Original
records, source snapshots, smoke windows and spent attempts remain intact.

The first bounded performance smoke is 18 calls: six conditions times the three
already registered fixed cases. It has its own 900-second window under the new
user request. Eighteen calls are transferred from unused recovery reserve; the
experiment-wide 6,000-call maximum is unchanged. All inputs are unchanged, all
calls are genuine and retained, and each collects the registered attention taps.

Report both `language_seconds` (the quantity in the earlier chat table) and
`processor_model_seconds` (online invocation, including encoding/admission).
Report every call, maximum and per-arm distributions. Startup and CPU preparation
are separately recorded; neither output truncation nor selective deletion of slow
calls may be used to claim the target. A finite smoke cannot guarantee a 20-second
bound for every future 8,192-token response. Full-run authorization is not renewed
by a performance-only smoke.

Before editing, a directly readable snapshot of source/configuration/receipts was
saved under `results/organization_v1/performance_revision_v1/before/`. New source
proofs carry forward only unchanged input/geometry/parser qualifications; affected
GPU arithmetic and runtime paths are tested separately. No full CPU rerendering,
new QA questions, extra manual image views or historical source changes are needed.

## Follow-up qualification

Two 18-call performance scopes completed without infrastructure or artifact
failures (242.75 and 244.01 seconds, including startup). Both failed the
all-calls-at-most-20-second target; their `review.json` files certify correctness,
while separate `timing_review.json` files record the failed latency gate. Old
answers, clocks and ledger entries remain intact.

A third scope adds the same 18 fixed input/arm positions, no new scientific
conditions. Across the three scopes, 54 calls were transferred from the unused
94-call recovery reserve, leaving 40 and preserving the 6,000-call ceiling.

The next revision batches equal-length fusion groups with the original FP32
mean followed by BF16 conversion. An earlier segment-reduction attempt differed
by one BF16 rounding unit in two synthetic elements; it was rejected before any
model call. The replacement passes exact BF16 comparison on variable groups and
six actual fixed-case LOCAL/SHAM grouping plans. Grouped-query FP32 measurement
avoids key/value head replication. Paged-cache numerical tests additionally cover
the real 784-position block size with shuffled blocks and a partial final block.

The timing probes retain GPU event spans and CPU dispatch spans for a few native
prefill/decode batches. Event spans include stream scheduling and are not an
independent hardware profiler of kernel occupancy. No layer, query, donor rule,
output allowance, image, input fact or weight is removed to satisfy speed.
The formal pause marker and old formal version authorization remain unchanged.

## Third-scope result and remaining bottleneck

All 18 calls completed in 234.62 seconds including startup, with zero
infrastructure/input/output/attention integrity issues. Central RCA scores
reproduce from the retained raw answers. The latency target remains **not met**.
The table uses the unchanged language clock, including time spent behind other
engine work; the online clock additionally includes admission and encoding.

| Arm | Mean language seconds | Maximum language seconds | Mean online seconds |
|---|---:|---:|---:|
| F_LOCAL_MEAN | 43.37 | 72.73 | 48.68 |
| P_FULL | 43.46 | 75.06 | 53.06 |
| S_EVID_REDIST | 62.06 | 88.92 | 74.72 |
| S_SHAM_REDIST | 64.77 | 87.74 | 69.80 |
| S_SUPPRESS | 54.10 | 79.49 | 60.69 |
| S_VIS_REDIST | 31.95 | 44.22 | 39.80 |

A 16,897-token prefill occupied 3.86 seconds of measured forward span; two
new full inputs took 7.74 seconds in a shared batch. Pure eight-request decode
spans were about 74–79 ms after the first measured step, including about
17–19 ms of correction spans. Other requests' encoding/prefill interrupts
ongoing decoding; isolated first/tail calls are not representative of a loaded
eight-request batch. This identifies significant prefill and queue overhead,
but does not establish an immutable hardware lower bound or rule out further
scheduling improvements.

Low-utilization samples also show an active engine CPU core while the eight
preparation workers were idle and the input-ready queue was nonempty. Therefore
CPU input preparation saturation does not explain those particular samples.
A fourth bounded 18-call scope records nonblocking Python stacks (py-spy in an
isolated /tmp tool directory, no model-environment installation) to identify
the engine's host work. This transfers another 18 recovery calls, leaving 22.
Its sampling overhead is disclosed; it is a diagnostic run, not an uninstrumented
throughput claim. No formal resume or scientific parameter change is made.

## Fifth scope: latest OR target and deferred passive collection

The fourth scope completed 18/18 calls without infrastructure/artifact errors.
Its stack samples identify synchronization at GPU-to-host reads and creation of
GPU indices inside model layers; a stack waiting inside a CPU API is not proof
of CPU preparation saturation. The nonblocking profiler had 1,245 failed samples
and one corrupted filename; its raw file is retained. It is diagnostic sampling,
not a CPU-cycle or GPU-occupancy measurement.

The next runtime preloads immutable query/region indices and defers passive
attention summary transfers to per-call commit. All four layers, both queries,
original distributions and sink accounting remain recorded. This affects all
six slow conditions, in addition to the already qualified sink kernels and
batched fusion. A targeted independent test verifies both the unchanged native
output and the deferred region masses.

The fifth 18-call scope is unprofiled (no Python stacks or layer timing events).
NVML telemetry samples the GPU throughout the run; acceptance uses the complete
measured inference interval, not model loading or a selected busy interval.
Eighteen calls transfer from reserve (22 -> 4); the overall 6,000-call maximum
is unchanged. The six arms, three fixed cases, eight-request maximum, evidence,
precision, sampling and output limits are unchanged. Formal remains paused.

## Final bounded performance acceptance

The fifth scope completed all 18 calls (six arms × three datasets) with no
infrastructure or artifact failures. Its full inference interval was
173.444 seconds, from the first invocation through the last completed invocation,
including encoding, admission/queue waiting, prefill, generation and drain.
One-second NVML samples (maximum gap 1.00019 seconds) give a time-weighted GPU
utilization of **87.6709%**. The user-authorized >=82% alternative therefore
passes. Model loading is excluded; no busy-only interval was selected.

The all-calls <=20-second alternative does **not** pass. Throughput over this
interval is 6.2268 calls/min; total scope time including preparation/startup/exit
is 254.696 seconds. Utilization alone does not establish lower latency or a
throughput improvement over a differently batched run. Results are for the mixed
six-arm queue, not isolated per-arm utilization.

| Arm | Mean language seconds | Mean online seconds | Maximum online seconds |
|---|---:|---:|---:|
| F_LOCAL_MEAN | 39.73 | 49.43 | 65.51 |
| P_FULL | 63.78 | 70.63 | 106.87 |
| S_EVID_REDIST | 61.09 | 71.87 | 92.33 |
| S_SHAM_REDIST | 59.82 | 70.80 | 107.39 |
| S_SUPPRESS | 74.76 | 81.07 | 102.29 |
| S_VIS_REDIST | 42.86 | 48.68 | 80.83 |

All 18 raw outputs were inspected for completion and centrally rescored. Model
claims/attribution errors remain model outcomes, not reasons to modify methods.
Each call retains all eight registered attention taps; masses, densities and
region counts pass review. Summary sizes are 7,193–12,270 bytes/call. Native
weights/BF16, gates, positions, original images/prompts, precision and output
ceilings are unchanged. No extra manual images were opened.

Static checks (3,699 functional source lines), 17 targeted regressions and
independent actual-GPU numerical checks pass. Unchanged 220-case input/geometry
qualifications were carried only with source/hash proofs; no full CPU rerun.
Five performance scopes consumed 90 new calls, preserving all prior attempts.
The total registered ceiling remains 6,000, with four recovery calls remaining.

Formal remains paused at 178/5,850 positions (153 formal generations, 25 exact
references). No new formal call was made. The smoke engine has shut down and
its writers drained. The old formal version credential is not renewed by this
performance result. Canonical receipts: `smoke_performance_v5/review.json`,
`timing_review.json`, `response_review.json`, `attention_review.json`; raw
utilization samples: `hardware.jsonl`.

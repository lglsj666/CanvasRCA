# Adaptive elimination tournament — stopped after 38 committed rounds

## Final analysis authority — 2026-09-15

The user ended the tournament. The complete current analysis is
[Tournament Analysis 2026-09-15](../../../docs/Tournament_Analysis_2026-09-15.md),
with all 38 rounds, five datasets, both AIOPS jointly, AC@1/3/5, conditional
paired statistics, observable failure stages, and a conceptual X proposal.
No new model calls or X implementation/testing were performed for that report.

Qwen cumulative coverage is 394/452/464 of 480 at K=1/3/5; Gemma is
414/454/464. These are observed multi-method unions, not one-call accuracy.
Qwen/Gemma retain 86/66 uncovered cases; 70/50 of these have previously
appeared in the top five. The remaining failures include selection omissions,
entity-level competition and unsupported explanations even in correct outputs.
The report keeps nomination separate from verified reasoning.

Authority is `results/tournament_v1/coverage/round_0001` through `round_0038`
and their referenced artifacts, not a scan of all historical result folders.
Early small-subset rounds 2–10 below were superseded and their outcomes do not
contribute to current coverage. Their historical notes remain below for audit;
later full-remaining rounds use the same round numbers but different contracts.
Round 39 rank-band rescue was rejected before inference and is not a result.

## Historical running notes — not the final coverage authority

The user-authorized tournament is adaptive method discovery, not one deployed
method's accuracy. Qwen3.8-27B and Gemma-4-26B-A4B-it have separate retirement
sets. Under the latest DD-11 amendment, each model needs top-1 union coverage
of 80/100 in each primary dataset and 72/90 in each RE2 dataset, then stops.
There is no top-5 retirement stage; AC@3/5 remain descriptive success maps.
Both models must meet all five thresholds. Earlier per-round threshold
descriptions below describe the policy then in force, not the current gate.
No training or new attention.

The first method inherits SEARCH22 selection/rendering and registers a
fixed RQ2.1-style prompt successor plus explicit visible card IDs. Prior
SEARCH22 outcomes are not its results. All 480 CPU-side pools are complete;
the preserved compiler and training-split hashes are unchanged. Forward
CPU/gallery/live qualification completed on 2026-09-13: 375 CPU/renderer tests
passed; three reviewed real training-case PNGs were used by both models in six
successful, untruncated calls, within the aggregate 600-second limit. Full
conversation and hash review is in
`../results/search_first_v1/tournament_qualification_v1/REVIEW.md`.
The 480-case pool verification checked every public/private identity and hash;
existing processed data and the split remain untouched. First-round tournament
retirement is recorded below; smoke accuracy is not a result.

First-round review identified an inherited Aegis trace-unit error after 73 Qwen
responses (plus three interrupted requests); Gemma had not started. These
attempts stay preserved but are superseded for this tournament's coverage.
Official Aegis nanosecond units and all 100 source/stored duration columns were
verified; the RQ3 display now converts stored microseconds to milliseconds.
See `../results/tournament_v1/round_0001/UNIT_CORRECTION_V2.md`.
The corrected execution is `../results/tournament_v1/round_0001_unitfix_v2/`:
100 Aegis inputs corrected, 380 other case artifacts byte-identical, all480
CPU/prompt/fact/image checks passed. No processed files, old RQ results, prompt
structure or model recipes changed.

## Corrected round 1 — 2026-09-13

Both models completed all 480 registered cases. All 960 responses, request
records and associated artifacts passed the persistence audit. All responses
ended with `stop`; none reached the output ceiling. Qwen has 480 normal model
outputs. Gemma has 479 normal outputs and one duplicate-ID model failure
(`INC-374F53762B49`: `[663,389,389,731,724]`), retained with zero score. Its
reason also calls a three-digit service a pod; this is model behavior, not a
reason to resample. No infrastructure failures remain.

| Dataset | N/model | Qwen MRR | Qwen AC@1 | Qwen AC@5 | Gemma MRR | Gemma AC@1 | Gemma AC@5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| AIOPS-2022 | 100 | .2970 | .1600 | .5200 | .2425 | .1300 | .4300 |
| AIOPS-2025 | 100 | .3147 | .2400 | .4600 | .2270 | .1500 | .3700 |
| Both AIOPS | 200 | .3058 | .2000 | .4900 | .2348 | .1400 | .4000 |
| AegisLab | 100 | .4843 | .3400 | .7600 | .4627 | .3300 | .7400 |
| Three primary datasets | 300 | .3653 | .2467 | .5800 | .3107 | .2033 | .5133 |
| RE2-OB | 90 | .7556 | .5889 | 1.0000 | .6374 | .4333 | .9667 |
| RE2-TT | 90 | .6354 | .4333 | .9333 | .5191 | .3889 | .7222 |
| All | 480 | .4891 | .3458 | .7250 | .4110 | .2813 | .6375 |

Mean actual input/output tokens: Qwen **18,264.8 / 176.2**, Gemma
**3,428.8 / 163.8**. Native image tokens are 16,002 and 1,091 respectively;
the same PNG and public text were supplied, with different native processors.
These are single-method sampled results, not a paired comparison of processors.

Durable retirement: Qwen **166/480**, of which **74/300** primary cases;
Gemma **135/480**, of which **61/300** primary cases. Remaining cohorts are
314 and 345. Neither reached the 240-primary-case transition. Original
SEARCH22's small training-subset result did not reproduce as a high all-case
score under this registered prompt successor; it remains a starting method,
not a proven optimum. Next rounds must seek complementary evidence, not count
an old method's success on a different input as a new retirement.

Detailed per-case scores and AC@3/AVG/cost summaries:
`../results/tournament_v1/round_0001_unitfix_v2/analysis.json`.
Both model commits and independent remaining sets:
`../results/tournament_v1/coverage/state.json`.

Historical AC@1/5 union coverage remains separately documented in
`docs/RQ1_1_RQ2_1_RCA_Coverage_2026-09-12.md`; it does not retire new tournament
cases or demonstrate that a single method selects the right design per case.

## Round 2 — native BARO top-24 metric selection, 2026-09-13

Method: `BARO019_FINITE_TOP24_tournament_v1`. Each model received 42 of its
remaining cases: 12 per main dataset and three per RE2 dataset. The 56 unique
images include 28 cases shared between the two models. Every shared actual
request has equal system/text/image content after removing local artifact paths;
image hashes were independently checked. All 84 outputs and their artifacts
persisted. These are adaptive eligible subsets, not representative population
MRRs or a paired comparison between models.

| Dataset | N/model | Qwen previous → BARO MRR | Qwen new top-1 | Gemma previous → BARO MRR | Gemma new top-1 |
|---|---:|---:|---:|---:|---:|
| AegisLab | 12 | .2361 → .2153 | 1 | .2139 → .3417 | 3 |
| AIOPS-2022 | 12 | .1583 → .2528 | 1 | .2042 → .2028 | 1 |
| AIOPS-2025 | 12 | .0694 → .2083 | 1 | .1944 → .4708 | 5 |
| RE2-OB | 3 | .4167 → .3611 | 0 | .3333 → .4667 | 1 |
| RE2-TT | 3 | .3444 → .4000 | 1 | .3333 → .1111 | 0 |
| All round-2 cases | 42 | .1869 → .2476 | 4 | .2226 → .3313 | 10 |

The previous scores are from round 1 on exactly each model's new 42-case
cohort, not its full-480 average. BARO gives complementary successes, especially
Gemma's AIOPS-2025 subset, but also moves previously partial hits down:
Qwen RR improves/worsens/ties on 9/10/23 cases; Gemma on 15/14/13. Neither
selector is a universal winner. This compound change also increases metrics
capacity to 24 and can change the selected owner-related G context.

Mean input/output: Qwen 18,327.7/168.0; Gemma 3,491.4/362.1. Gemma's output
mean includes one **8,192-token citation-repetition truncation** on
`INC-CCCFF766DA4B` (1/42 = 2.38%). It is retained as zero-scored model failure,
not silently retried. Full response and actual PNG were inspected: the repeated
citation sequence is generated by the model, not copied from a malformed input.
The remaining 83 replies stopped normally. There are no infrastructure failures.
Absence of infrastructure errors must not be confused with absence of model
errors. No model recipe or fixed prompt is changed on this isolated outcome.

Retired totals now: Qwen **170/480**, including **77/300 (25.67%)** primary;
Gemma **145/480**, including **70/300 (23.33%)** primary. Both remain in top-1
discovery. All method/success bindings live in the coverage register.

Evidence: `../results/tournament_v1/round_0002_baro24_v1/analysis.json` and
`../results/tournament_v1/round_0002_baro24_v1/REVIEW.md`.

## Round 3 — native SIRCL trace support/confidence, 2026-09-13

42 logical outcomes per model on its own remaining cohort. 82 new calls plus
two exact-request aliases; no new attention or training. All 84 outcomes are
complete, finish=stop, with at most 254 Qwen / 209 Gemma output tokens.
All persisted request/artifact checks pass, including 29 cross-model shared
inputs. Both models' retired sets were committed after their completed phases.

| Dataset | N/model | Qwen round-1 → trace-SC MRR | New top-1 | Gemma round-1 → trace-SC MRR | New top-1 |
|---|---:|---:|---:|---:|---:|
| AegisLab | 12 | .1944 → .2944 | 1 | .1444 → .4528 | 4 |
| AIOPS-2022 | 12 | .1583 → .2639 | 1 | .1833 → .2917 | 3 |
| AIOPS-2025 | 12 | .0694 → .1903 | 1 | .1250 → .1208 | 0 |
| RE2-OB | 3 | .4167 → .4167 | 0 | .2500 → .2889 | 0 |
| RE2-TT | 3 | .3444 → .2333 | 0 | .3333 → .0000 | 0 |
| This round | 42 | .1750 → .2603 | 3 | .1710 → .2679 | 7 |

Prior values use the exact current cohort, not round 1's population mean.
This is native trace ranking plus eight-row capacity, not the complete
TraceRCA algorithm. Metrics stay unchanged. Native ranking changes actual
trace sets versus the old top-eight on 53/55 unique cases, establishing more
than a nominal tool-name change. Some native operations cannot bind to the
inherited positive-change TRC-L pool; their omission/fill audit is retained.

Complementarity is model/dataset dependent: Gemma gains here are in AegisLab
and AIOPS-2022, whereas BARO's new successes were concentrated in AIOPS-2025.
RE2-TT loses partial hits with the expanded trace context. Across this round,
Qwen RR improves/worsens/ties in 10/8/24 cases; Gemma in 14/9/19.
These shifting eligible subsets do not support comparing aggregate round
MRRs as if they were head-to-head full-population method scores.

Mean logical input/output tokens: Qwen 18,327.3/182.9, Gemma 3,491.5/163.2.
Actual new calls together consumed 894,712 input and 14,164 output tokens;
the two reused records incur no new cost. Lifecycle durations were 477.9 s
and 172.6 s. Local candidate/global text is unchanged and diagnostic facts
remain exclusively inside the PNG.

Three full conversations and their actual images were manually inspected:
Qwen AIOPS-2025 INC-77C683F9B6C0, Gemma AIOPS-2022 INC-3BFC24F5D6E5,
and Gemma RE2-TT INC-785D78DEDF40. Correct rankings can still accompany
unsubstantiated propagation claims. In the last case, the answer assigns the
displayed earliest onset of service 371 to 525 and cites unrelated M labels;
the source PNG has the correct labels. This is model reading/reasoning error,
not a changed input or a reason to retry. It motivates further evidence/context
selection experiments, not tuning the fixed diagnostic instructions.

Cumulative retirement: Qwen **173/480 (36.04%)**, primary **80/300 (26.67%)**;
Gemma **152/480 (31.67%)**, primary **77/300 (25.67%)**. Both remain below
the independent 240/300 top-1 threshold. Evidence:
`../results/tournament_v1/round_0003_trace_sc8_v1/analysis.json` and `REVIEW.md`.

## Round 4 — native SIRCL Drain frequency, 2026-09-13

42 outcomes/model on each model's remaining cohort; 56 distinct cases, 28
shared inputs. 83 new calls and one exact-request reuse, all finish=stop and
valid format, no infrastructure error. The six-template selector binds native
source events to Denum groups exactly. All 55 cases with logs receive six
native selections without parent fill; one case has no logs and is unchanged.
Metrics/trace facts and the fixed prompt stay unchanged. More selected log
owners can change the associated topology/name-group context.

| Dataset | N/model | Qwen round-1 → log-frequency MRR | New top-1 | Gemma round-1 → log-frequency MRR | New top-1 |
|---|---:|---:|---:|---:|---:|
| AegisLab | 12 | .2153 → .3361 | 1 | .1750 → .2917 | 2 |
| AIOPS-2022 | 12 | .1417 → .1806 | 0 | .1250 → .2153 | 1 |
| AIOPS-2025 | 12 | .0903 → .1875 | 1 | .1250 → .3333 | 4 |
| RE2-OB | 3 | .4167 → .4167 | 0 | .2500 → .5833 | 1 |
| RE2-TT | 3 | .3444 → .6667 | 1 | .3333 → .4444 | 1 |
| Both AIOPS | 24 | .1160 → .1840 | 1 | .1250 → .2743 | 5 |
| Primary | 36 | .1491 → .2347 | 2 | .1417 → .2801 | 7 |
| This round | 42 | .1821 → .2786 | 3 | .1631 → .3135 | 9 |

These comparisons use the exact same-case round-1 scores; different rounds'
eligible cohorts are not a head-to-head population ranking. Qwen improves/
worsens/ties in 13/2/27 cases, Gemma 12/6/24. Native frequency produces further
complementary successes, but it can also select routine access messages and
make long templates much denser. It is not the full TORAI pipeline, and this
compound log-count/selection intervention does not isolate either factor alone.

Mean logical input/output tokens: Qwen 18327.0/167.1, Gemma 3491.9/169.0.
Actual new calls used 912968 input and 13947 output tokens, with reuse excluded.
Source image dimensions and model processor recipes are unchanged; identical
pixel counts do not imply identical diagnostic usefulness or readable detail.

Three complete conversations and actual request images were inspected. The
new log facts can support an actual observation (for example Qwen reads
pod 96629's error rate 88.9 -> 830 in INC-04317463B3D0), yet the answer can
still invent an unshown call relation. Gemma INC-93C032432E23 confuses a panel
identifier and onset value despite a correct root ranking. Gemma
INC-09BEA9D63577 attaches service 196's display rank to another pod. Thus the
new union successes demonstrate ranking coverage, not universally sound
causal explanations. Source records and scores remain unchanged.

Cumulative retirement now: **Qwen 176/480 (36.67%), primary 82/300 (27.33%);
Gemma 161/480 (33.54%), primary 84/300 (28.00%)**. Still in top-1 discovery;
the goal requires 240 primary successes independently for each model.
Evidence: `../results/tournament_v1/round_0004_log_freq6_v1/analysis.json`,
`REVIEW.md`, full native selection audits and the coverage register.

## Round 5 — native SIRCL sustained mean shift, 2026-09-13

42 cases/model, 58 distinct cases, 26 shared inputs verified. All 84 requests
and artifacts are complete; no reuse or infrastructure retry. Native MA
selects up to 24 series using an absolute before/after mean difference over
three baseline population standard deviations, unlike BARO's signed scaled
maximum. The existing R4/L2 and owner-linked G context are retained.
This is SIRCL's component, not full official ThinkFL or a pure algorithm-only
comparison against the smaller round-1 overview. Native rankings remain
private audit data; only the original selected telemetry enters the PNG.

| Dataset | N/model | Qwen round-1 → MA MRR | New top-1 | Gemma round-1 → MA MRR | New top-1 |
|---|---:|---:|---:|---:|---:|
| AegisLab | 12 | .2153 → .3250 | 2 | .1750 → .1597 | 1 |
| AIOPS-2022 | 12 | .1417 → .2917 | 1 | .1250 → .2361 | 1 |
| AIOPS-2025 | 12 | .0903 → .1167 | 0 | .0278 → .2153 | 2 |
| RE2-OB | 3 | .4167 → .3611 | 0 | .4167 → .2611 | 0 |
| RE2-TT | 3 | .3444 → .0833 | 0 | .2778 → .1667 | 0 |
| Both AIOPS | 24 | .1160 → .2042 | 1 | .0764 → .2257 | 3 |
| Primary | 36 | .1491 → .2444 | 3 | .1093 → .2037 | 4 |
| This round | 42 | .1821 → .2413 | 3 | .1433 → .2052 | 4 |

The reference is round 1 on precisely each model's current eligible cohort.
The two models' cohorts differ, and changing cohorts prevent treating this
table as a head-to-head comparison against the previous selectors. Qwen
RR improves/worsens/ties on 13/8/21 cases; Gemma on 10/9/23. Complementary
primary successes coexist with poorer RE2 partial rankings. Selecting a
sustained shift can highlight ordinary memory/uptime trends as well as a
fault; a large native anomaly score is not proof of origin.

All 58 images and metric sets change versus round 1. At equal top24 capacity,
55/58 selected sets differ from the inherited ranking: this is not only a
larger plot count. Forty-four cases have 24 native entries; 14 need 3–19
registered fill entries. All Aegis cases have full native coverage, but
AIOPS-2025 and RE2 more often need fill. Their differences in usable native
evidence must not be disguised by dropping fill cases.

All Qwen replies stop normally. Gemma has one 8,192-token citation-repetition
truncation (1/42, 2.38%), retained as a zero model outcome without resampling;
the actual image/prompt has no corresponding repeated sequence. Mean input/
output tokens: Qwen **18,327.0 / 173.9**, Gemma **3,491.2 / 369.0**. Gemma's
41 normal replies average 178.2 output tokens; the overall mean still includes
the truncation. New calls consumed 916,365 input and 22,801 output tokens.
The owned model phases lasted 484.24 and 397.63 seconds and shut down normally.

Manual actual-input review again distinguishes ranking from explanation:
Qwen correctly names service 849 in INC-EAA097A406D6 using a real dialing-error
template, but its proposed call edge is absent from the ledger. Gemma correctly
names pod 90007 in INC-17615889CDA7 while calling it a service, describing
falling transmit traffic as a spike, and inventing dependencies from a naming
membership strip. These are retained model errors in explanations, not grounds
to invalidate the correct top-1 scores or alter the frozen prompt.

Cumulative retirement: **Qwen 179/480 (37.29%), primary 85/300 (28.33%);
Gemma 165/480 (34.38%), primary 88/300 (29.33%)**. Remaining cases: 301 and
315. Both remain below their separate 240-primary top-1 transition; the
tournament and subsequent training objectives are not achieved.

Evidence: `../results/tournament_v1/round_0005_ma24_v1/analysis.json`,
`REVIEW.md`, native/CPU audits, immutable source archive, full conversations
and model-specific committed coverage. No training or new attention.

### Cumulative owner-association audit: selection is only one bottleneck

All 480 complete pools contain some root-associated M/R/L and at least one
score-acceptable candidate. This was checked with the same granularity-aware
matcher used for tournament scoring; service-level roots may match their pod
telemetry. It does not mean every pool includes the decisive fault signal.

For each model's still-unretired primary cases, use only methods that model
actually executed on that case, not another model's gallery:

| Model | Remaining primary cases | Root-associated M/R/L never selected | Selected at least once, still no top-1 |
|---|---:|---:|---:|
| Qwen | 215 | 49 | 166 |
| Gemma | 212 | 50 | 162 |

Of the never-selected cases, 26 per model are AIOPS-2025, 15 Qwen/16 Gemma
are AIOPS-2022, and eight per model are AegisLab. Including RE2 gives
52/301 Qwen and 53/315 Gemma never-selected cases. No case is classified as
having neither a score-acceptable candidate nor any owner-associated direct
telemetry in its complete pool.

This distinguishes two paths for further exploration: expose omitted owners'
signals, and improve the selection/interpretation of already exposed owners'
signals. It does **not** classify all 166/162 as reasoning errors: a selected
row can be nondiagnostic, difficult to read, or outweighed by other evidence.
G edges/onsets and indirect propagation are separately tracked, so absence
of direct M/R/L does not imply an impossible case. Evidence:
`../results/tournament_v1/diagnostics_through05/REVIEW.md`; the per-case
label-associated audit is evaluator-private, never model/training input.

## Round 6 — Same log-frequency method on its untried remainder

This is a cohort expansion of round 4, **not a sixth distinct algorithm**.
All previously executed parent-method targets (wrong answers included) and
already retired targets are excluded per model. No parameters, prompts,
renderer or recipes change. Three parent-method CPU replays reproduce PNG,
packet, manifest, prompt and native selection exactly.

265 Qwen/285 Gemma logical outcomes completed, including six exact-request
aliases: 544 new calls. All 550 finish normally with valid format; all artifact
checks and 225 shared cross-model inputs pass. No truncation, infrastructure
failure, new attention or training. 322/325 unique images change log evidence
relative to the first-round anchor, with M/R sets and static text unchanged.

| Dataset | Qwen N | Qwen round-1 → log MRR | New top-1 | Gemma N | Gemma round-1 → log MRR | New top-1 |
|---|---:|---:|---:|---:|---:|---:|
| AegisLab | 52 | .2183 → .3285 | 8 | 47 | .1979 → .3876 | 11 |
| AIOPS-2022 | 70 | .1686 → .2229 | 3 | 71 | .1239 → .2493 | 9 |
| AIOPS-2025 | 62 | .1030 → .1374 | 1 | 68 | .0716 → .1586 | 6 |
| RE2-OB | 34 | .4044 → .4520 | 2 | 47 | .3642 → .4468 | 10 |
| RE2-TT | 47 | .3543 → .5078 | 14 | 52 | .2061 → .4176 | 10 |
| Both AIOPS | 132 | .1378 → .1827 | 4 | 139 | .0983 → .2049 | 15 |
| Primary | 184 | .1605 → .2239 | 12 | 186 | .1235 → .2511 | 26 |
| This extension | 265 | .2262 → .3035 | 28 | 285 | .1782 → .3137 | 46 |

Each previous value is the same-case round-1 result. These are independent,
adaptive remaining cohorts, not full-population method accuracies or paired
model comparisons. Rank improves/worsens/ties on 73/35/157 Qwen cases and
94/40/151 Gemma cases. Expanding a complementary method reveals successes
outside the initial small cohort, while still retaining meaningful regressions.
The log method's additional primary gains are larger for Gemma in its cohort;
Qwen's extension gains are concentrated in RE2-TT and AegisLab, not AIOPS-2025.

Mean logical input/output tokens: Qwen **18,285.9 / 169.2**, Gemma
**3,431.5 / 166.2**. Actual new calls use **5,758,709 input / 91,335 output**
tokens. Local lifecycle durations are 2452.2 and 623.5 seconds. No implication
that the different image-token budgets are equal visual-processing costs.

Long Aegis access templates are very dense. Nevertheless, on the same
INC-D9ABFB644D29 image Gemma binds LT211's severe exception to pod 96209
and ranks it correctly, while Qwen attaches that log to another service and
misses the root. This is a concrete model-dependent evidence-binding example,
not proof that all log-frequency gains are faithful reasoning. Other inspected
top-1 successes contain wrong card ownership, invented edges, coincident
onsets treated as ordered, or a 15% log decline described as 30-fold. See the
four complete conversation/image audits in the round's `REVIEW.md`.

Cumulative retirement: **Qwen 207/480 (43.13%), primary 97/300 (32.33%);
Gemma 211/480 (43.96%), primary 114/300 (38.00%)**. Remaining: 273/269.
Both are below their independent 240-primary-case top-1 target. Preserve all
successful-method AC@1/3/5 bindings; union coverage is not a deployable policy.
Evidence: `../results/tournament_v1/round_0006_log_freq6_extension_v1/analysis.json`,
`REVIEW.md`, the two retirement commits and immutable source/input artifacts.

## Round 7 — unchanged native trace-SC on the untried remainder

486 logical outcomes (240 Qwen, 246 Gemma), 474 new calls, 12 exact-request
aliases. All stop normally and parse successfully; all artifacts and 192 shared
inputs verified. No residual infrastructure failures. This is an expansion of
round 3's component, not a new method or a complete TraceRCA reproduction.

| Dataset | Qwen N | Previous → trace-SC MRR | New top-1 | Gemma N | Previous → trace-SC MRR | New top-1 |
|---|---:|---:|---:|---:|---:|---:|
| AegisLab | 45 | .2089 → .4419 | 12 | 40 | .2046 → .3329 | 9 |
| AIOPS-2022 | 68 | .1613 → .2118 | 4 | 65 | .1003 → .1567 | 4 |
| AIOPS-2025 | 62 | .1016 → .1145 | 1 | 62 | .0583 → .0481 | 0 |
| RE2-OB | 32 | .4036 → .4786 | 3 | 37 | .3523 → .4387 | 6 |
| RE2-TT | 33 | .3278 → .4237 | 3 | 42 | .1897 → .4444 | 11 |
| Both AIOPS | 130 | .1328 → .1654 | 5 | 127 | .0798 → .1037 | 4 |
| Three primary | 175 | .1524 → .2365 | 17 | 167 | .1097 → .1586 | 13 |
| All eligible extension | 240 | .2100 → .2945 | 23 | 246 | .1598 → .2495 | 30 |

Previous means round 1 on exactly these new, still-unretired cases, not its
population average. RR improves/worsens/ties on Qwen 72/34/134 and Gemma
65/38/143. Trace selection is complementary on Aegis but adds almost no new
AIOPS-2025 top-1 coverage here; Gemma's AIOPS-2025 MRR even decreases. These
model-specific adaptive cohorts do not support a direct cross-model ranking.

New calls consumed 5,104,036 input and 82,924 output tokens. Mean logical
input/output: Qwen 18,287.13/186.22; Gemma 3,437.49/163.43. Lifecycle time
including startup/drain is 38.19 and 9.02 minutes respectively. No attention.

Full conversation/image review continues to find evidence-binding weaknesses
even among top-1 successes: LT213's rate can be assigned to the wrong service;
z can be read as onset time; operation endpoints can be confused with owners;
and a pod can be called a node despite the explicit numeric/type guide. In the
longest Qwen answer (1,530 tokens, not truncated), the explanation concludes
that the second-ranked pod should be first while leaving its initial list
unchanged. The frozen scorer uses that actual list (RR=.5). None is retried.
These examples motivate clearer evidence ownership/temporal organization,
not a claim that all ranking successes reflect correct causal reasoning.

Cumulative retirement: **Qwen 230/480 (47.92%), primary 114/300 (38.00%);
Gemma 241/480 (50.21%), primary 127/300 (42.33%)**. Remaining: 250/239;
both below 240 primary top-1s. Evidence: round 7 `analysis.json`, `REVIEW.md`,
the two durable commits and unchanged request/source snapshots.

## Round 8 — unchanged native BARO on untried cases

This expands round 2, not the number of distinct algorithms. Qwen/Gemma
received 220/222 previously untried eligible cases; 272 unique cases and
170 shared inputs. Three exact parent replays and all gallery/input/artifact
checks passed. All 442 requests are new; their complete outputs remain.

| Dataset | Qwen N | Round-1 → BARO MRR | New top-1 | Gemma N | Round-1 → BARO MRR | New top-1 |
|---|---:|---:|---:|---:|---:|---:|
| AIOPS-2022 | 65 | .1469 → .1754 | 3 | 62 | .0777 → .1745 | 5 |
| AIOPS-2025 | 62 | .1016 → .1395 | 4 | 64 | .0565 → .0695 | 1 |
| AegisLab | 34 | .1931 → .1941 | 1 | 33 | .2045 → .2409 | 4 |
| RE2-OB | 29 | .4080 → .3552 | 1 | 32 | .3474 → .2396 | 2 |
| RE2-TT | 30 | .3356 → .2644 | 0 | 31 | .1780 → .1973 | 3 |
| Both AIOPS | 127 | .1248 → .1579 | 7 | 126 | .0669 → .1212 | 6 |
| Three primary | 161 | .1392 → .1655 | 8 | 159 | .0955 → .1460 | 10 |
| This round | 220 | .2014 → .2040 | 9 | 222 | .1433 → .1667 | 15 |

Each baseline uses exactly that model's current cohort. BARO adds primary
coverage, particularly Gemma AIOPS-2022, but is not uniformly helpful: both
models lose RE2-OB reciprocal rank; Qwen's all-cohort mean barely changes.
RR improves/worsens/ties in 51/63/106 Qwen and 46/58/118 Gemma cases. This
extension corroborates complementarity, not a universal method improvement.

Qwen has no model failures; Gemma has two (0.90%): one truncated citation
loop and one duplicate-ID ranking. Both are retained at zero without retry.
New input/output tokens total 4,785,853 / 84,003. Mean Qwen input/output is
18,282.53 / 176.65; Gemma 3,440.08 / 203.34. No attention or training.

Six full conversations and their actual images show that correct root IDs
can coexist with wrong edge direction, mistaken numeric ownership, misread
count-change signs, and explanations preferring a different candidate than
the output ranking. In one Aegis success, the large local latency jump is
real, but the supporting caller claim is not. In one AIOPS-2025 success,
service 548 is correctly ranked while an absent 857→548 edge is asserted.
The detailed paired evidence is in round 8 `REVIEW.md`; these are model
reason-grounding weaknesses, not infrastructure failures or proof of a
correct physical causal explanation.

Cumulative retirement: **Qwen 239/480 (49.79%), primary 122/300 (40.67%);
Gemma 256/480 (53.33%), primary 137/300 (45.67%)**. Remaining: 241/224.
Neither reaches 240 primary top-1 successes. Evidence: round 8
`analysis.json`, `REVIEW.md` and model commits under `coverage/`.

## Round 9 — unchanged native MA on untried cases

All 393 outcomes (203 Qwen, 190 Gemma) are committed and artifact-verified;
147 shared inputs match across models. No aliases or infrastructure failures.
Qwen has 203 normal completions; Gemma has 189 and one output-length failure,
retained as a model outcome, not retried. New calls consumed 4,363,258 input
and 74,690 output tokens. This extends round 5's existing component rather
than introducing a new algorithm.

| Dataset | Qwen N | Round-1 → MA MRR | New top-1 | Gemma N | Round-1 → MA MRR | New top-1 |
|---|---:|---:|---:|---:|---:|---:|
| AegisLab | 31 | .2038 → .2591 | 5 | 25 | .1920 → .2067 | 3 |
| AIOPS-2022 | 60 | .1592 → .1400 | 0 | 52 | .0670 → .0859 | 1 |
| AIOPS-2025 | 55 | .1009 → .1582 | 4 | 57 | .0635 → .1336 | 4 |
| RE2-OB | 28 | .4048 → .3780 | 1 | 29 | .3402 → .3080 | 2 |
| RE2-TT | 29 | .3299 → .4017 | 2 | 27 | .1827 → .2185 | 2 |
| Both AIOPS | 115 | .1313 → .1487 | 4 | 109 | .0651 → .1109 | 5 |
| This round | 203 | .2085 → .2333 | 12 | 190 | .1405 → .1689 | 12 |

The comparison uses exactly each model's unretired cohort. MA adds complementary
AIOPS-2025 coverage, but no new Qwen AIOPS-2022 top-1 successes. Both models
lose average reciprocal rank on the sampled RE2-OB remainder. Mean improvement
and additional successes therefore do not establish a universally better
selector. Full record and cross-model input audit: round 9 `analysis.json`.
Detailed post-run conversation/image interpretation is not claimed by this
automatic integrity audit.

### Current AC@1-only stopping policy

| Dataset | Qwen cumulative top-1 | Gemma cumulative top-1 | Required per model |
|---|---:|---:|---:|
| AegisLab | 65/100 | 70/100 | 80/100 |
| AIOPS-2022 | 29/100 | 38/100 | 80/100 |
| AIOPS-2025 | 37/100 | 37/100 | 80/100 |
| RE2-OB | 60/90 | 61/90 | 72/90 |
| RE2-TT | 60/90 | 62/90 | 72/90 |

Overall union coverage is 251/480 (52.29%) and 268/480 (55.83%); neither model
has finished. The active policy ends each model directly after all five
AC@1 thresholds, not after AC@5 coverage. Coverage maps retain AC@1/3/5 and
unsolved cases; raw results are unchanged. This remains adaptive union
coverage across methods, not single-method accuracy. Migration and checks:
`../results/tournament_v1/logs/20260913_ac1_completion_policy.md`.

## Round 14 — trace-linked local metric contrast

After the later full-remaining rounds, round 14 applies a genuinely new
label-blind 24-series metric selector to every case still unretired: 132 Qwen
and 108 Gemma cases. It prioritizes public trace-associated owners, distinct
resource metric families, and stronger baseline/current contrasts while
holding R/L/G evidence, the one-image transport, prompt, candidates, model
recipes and scorer fixed. All 164 union inputs changed actual metric panels and
pixels relative to the resource-family predecessor; the static, source,
leakage, geometry and artifact audits pass.

The result is mostly negative. Qwen adds no top-one case; Gemma adds one
AIOPS-2025 case. Qwen's remaining-cohort MRR is 0.1348 versus 0.1366 in round
13, with 23/21/88 improved/worse/tied ranks. Gemma falls from 0.0931 to 0.0616,
with 9/25/74. This is useful evidence that trace-local resource coverage does
not resolve the dominant late-tournament failure mode.

The cumulative evaluator-private audit finds root-associated direct evidence
has already been selected at least once in 129/132 remaining Qwen and 104/107
remaining Gemma cases. Candidate sets remain score-capable in every case.
Therefore the next intervention should target binding and comparative
interpretation, not assume that another similar metric-ranking rule will expose
the missing answer. Full evidence: round 14 `analysis.json`, `REVIEW.md`,
`private/evidence_audit.json`, committed coverage records and source snapshot.

## Round 15 — topology text with M/R/L in one dashboard

Round 15 runs every case still unretired after round 14: 132 Qwen and 107
Gemma cases. It holds the resource-family selection fixed, moves only selected
G facts into exact typed text rows, and keeps M/R/L in one dashboard image.
All 239 model calls completed with `finish_reason=stop`; input equality on the
75 shared cases, artifact persistence and attention-off checks passed.

Qwen adds four top-one successes: two AIOPS-2022, one AIOPS-2025 and one
RE2-OB. Its same-cohort mean reciprocal rank rises from 0.1348 to 0.1694.
Gemma adds one AIOPS-2022 success and rises from 0.0528 to 0.0762 on its
same cohort. This is complementary evidence that exact topology text can
reduce some direction or identity-reading failures, not evidence that text G
is globally superior: Qwen still has 22 rank regressions and Gemma 12.

Cumulative AC@1 coverage is now Qwen 82/58/57/81/74 and Gemma
88/60/56/86/84 for AegisLab/AIOPS-2022/AIOPS-2025/RE2-OB/RE2-TT. Remaining
counts are 128 and 106. All remaining candidate sets are score-capable, and
direct root-associated public evidence has previously been selected in
125/128 Qwen and 103/106 Gemma cases. The late-stage bottleneck is therefore
mostly evidence binding and comparative interpretation rather than simple
absence of a root-owned row. Full evidence: round 15 `analysis.json`,
`REVIEW.md`, `private/evidence_audit.json`, committed coverage records and
source snapshot.

## Round 26 — incident-window pattern selection

After rounds 16–25 reduced the unretired cohorts to 97 Qwen and 77 Gemma
cases, round 26 changed only evidence selection. It ranks metric series by
robust level, peak, persistence and slope changes within the public estimated
incident window; it does not use a private injection timestamp or labels.
Renderer, layout, prompt, candidate list, model recipes and scorer stayed at
the fixed round-16 contract. Every one of the 120 unique-case fact selections
and PNGs changed relative to the anchor.

All 174 registered requests completed normally and passed persistence,
source-snapshot, scoring and cross-model-input verification. The intervention
added **zero new top-1 successes for either model**. It nevertheless changed
lower ranks: Qwen improved/worsened/tied on 10/10/77 cases and reached AC@5 on
26/97; Gemma improved/worsened/tied on 8/4/65 and reached AC@5 on 11/77.
Thus a sharper local incident-window metric ranking is not sufficient to solve
the remaining AC@1 failures, even though it can surface the root within the
lower ranking positions.

Cumulative coverage remains Qwen 383/480 and Gemma 403/480. Per-dataset AC@1
coverage remains Qwen 86/66/66/83/82 and Gemma 92/69/69/87/86 for
AegisLab/AIOPS-2022/AIOPS-2025/RE2-OB/RE2-TT. Only the two AIOPS datasets still
fail the 80% stopping threshold. Full evidence: round 26 `analysis.json`, the
two committed coverage records, full gallery review and source snapshot.

## Round 27 — source-first cross-modal bundle selection

Round 27 ran the complete post-round-26 unretired cohorts: 97 Qwen and 77
Gemma model-case units, with 54 cases shared by the two model-specific cohorts.
The selector changed only which public M/R/L/G facts entered the frozen
round-16 dashboard. It grouped incident-local metric changes, trace
local/exclusive latency, log bursts, public onset and directed neighbours by
anonymous entity, then preferred bundles whose evidence was earlier and less
consistent with a downstream-only symptom. The private label and injection
time were not selector inputs. Every one of the 120 union-case selections and
PNGs differed from the fixed anchor; prompt, candidates, renderer grammar,
layout, request recipes and scorer remained fixed.

All 174 registered model calls were persisted and the offline audit passed,
including all 54 same-case cross-model input comparisons. There were no
infrastructure failures or exact-request aliases. Two model outputs were
retained as ordinary zero-scored failures: Qwen duplicated candidate `974` in
one otherwise complete JSON response, and Gemma entered a citation repetition
loop and reached the 8,192-token request ceiling in one response. This is
2/174 model failures (1.15%), below the 5% protocol threshold; neither is a
reason to retry or alter the fixed prompt.

The selector added three Qwen top-1 successes (AegisLab 1, AIOPS-2022 1,
RE2-TT 1) and two Gemma top-1 successes (AIOPS-2025 1, RE2-TT 1). On the exact
eligible cohorts, Qwen MRR was 0.1005 versus 0.1067 under the preceding round,
with 11/15/71 rank improvements/regressions/ties. Gemma MRR was 0.0578 versus
0.0470, with 4/7/66. Source-oriented bundles therefore expose a small amount
of complementary top-1 signal, but do not act as a uniformly better ranking
rule on the already difficult remainder.

Cumulative AC@1 coverage is now Qwen **386/480** and Gemma **405/480**.
Per-dataset coverage is Qwen **87/67/66/83/83** and Gemma
**92/69/70/87/87** for AegisLab/AIOPS-2022/AIOPS-2025/RE2-OB/RE2-TT.
The remaining cohorts are therefore Qwen **94** and Gemma **75**. Both models
still fail the stopping rule on AIOPS-2022 and AIOPS-2025, so the next
registered full-remaining method is spectral-saliency selection. Full evidence:
round 27 `analysis.json`, committed coverage records, immutable source snapshot,
CPU/gallery reviews and complete trajectories/conversations.

### Selection successor v4 — implementation only, no new performance result

On 2026-09-14 eight literature-inspired selectors were implemented in the existing
RQ3 evidence-selection module and inspected statically. Their mechanisms and
limits are registered in `RQ3_experiments.md#selection-successor-v4`. The user
requested a stop before tests or execution; `selection_only_suite_v4.yaml` remains
execution-disabled. No new case has been scored or retired. Round 28's existing
spectral gallery and registration are preserved, not completed by this work.
Static code checks do not qualify these methods for inference or establish gain.

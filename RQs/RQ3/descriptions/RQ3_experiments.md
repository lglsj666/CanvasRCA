# RQ3 experiment and implementation contract

**Latest execution boundary (2026-09-15): STOPPED BY USER.** The tournament ends
at the 38 committed full-remaining rounds. No further inference, X-method
implementation/testing, or training is authorized by the analysis request.
Final descriptive coverage and failure analysis is in
[the dated report](../../../docs/Tournament_Analysis_2026-09-15.md).
The historical instructions below no longer authorize continuation.

**Historical execution boundary (2026-09-14):** the user requests the eight-method
successor's implementation and static review, then a pause. No CPU unit tests,
preparation, model requests or automatic tournament continuation in this session.
Round 28's existing spectral gallery/review and registration remain pending;
completed rounds remain untouched. See [successor v4](#selection-successor-v4).

<a id="selection-only"></a>

## DD-RQ3-TOURNAMENT-17 — Complementary evidence selectors; display fixed

**Date:** 2026-09-14. **Status:** implemented; static, CPU and preview review passed;
no new model calls made for this amendment.

The user asks for literature beyond the existing guide, permits original
selection mechanisms, and restricts subsequent rounds to evidence selection.
Round 16 is the display anchor: `candidate_binding_cards_v3`, one pure-visual
PNG, fixed numeric candidates in text, existing static tournament prompt and
model-specific inference recipes. Rounds 1–16 and their outputs stay unchanged.
This supersedes the prior permission to vary layout/transport in future rounds;
it does not invalidate those completed experiments or authorize training.
The subsequently updated user goal permits new selectors and silhouette drawing
experiments only after this pending selector catalogue is exhausted without
meeting the retirement thresholds. Dashboard layout remains fixed then as well.

### Scope and reading method

Question: which *different evidence mechanisms* could recover signals missed by
native maximum-deviation, BARO, SIRCL support/confidence/frequency, shape diversity,
peer contrast and resource-family selection already used in the tournament?
Search date: 2026-09-14. Search families included microservice RCA, propagation
analysis, trace localization, log novelty and representative selection, and
short-window change detection. Preference: primary papers, conference/publisher
records, author PDFs and official code. Include older foundational methods when
they provide a concrete different statistic. Exclude unverified venue claims,
private injection-time requirements, training-only detectors and extra LLM loops.

The existing guide was checked for SIRCL/ThinkFL, BARO, TraceRCA, Sieve,
peer-relative evidence and MicroRCA-Agent. The following reading goes beyond
that guide. Papers motivate hypotheses, not guaranteed tournament gains.

| Source and verified status | Transferable evidence | Adaptation boundary |
|---|---|---|
| [MicroHECL, ICSE 2021 **SEIP**](https://conf.researchr.org/details/icse-2021/icse-2021-Software-Engineering-in-Practice/35/MicroHECL-High-Efficient-Root-Cause-Localization-in-Large-Scale-Microservice-Systems), [paper](https://arxiv.org/html/2103.01782) | Distinguishes response-time, error-count and traffic anomalies; traverses/prunes observed service-call neighbourhoods | Our frontier selector is project-owned, not MicroHECL reproduction; no trained OC-SVM/RF or known alert service |
| [Log Clustering based Problem Identification for Online Service Systems, ICSE 2016 Companion](https://hongyujohn.github.io/LogClustering_Final.pdf), DOI 10.1145/2889160.2889232 | Recurring common events and novel discriminative events need not have the same diagnostic value | Our template burst selector uses within-case public counts, not their lab/production knowledge base or sequence-clustering algorithm |
| [Truong, Oudre & Vayatis, Selective review of offline change point detection methods](https://www.laurentoudre.fr/publis/TOG-SP-19.pdf), Signal Processing, DOI 10.1016/j.sigpro.2019.107299; [author code](https://github.com/deepcharles/ruptures) | Window discrepancy separates local distribution changes from a single global peak | Native L2 cost is copied; bin masking, multiscale scoring and RCA evidence selection are adaptations. This is a journal methods review, not an RCA accuracy result |
| [Lu et al., Beyond Fault Localization](https://arxiv.org/html/2608.21310), **preprint**, 2026-08-21 | Separates omitted evidence, misread evidence and unsupported inference; lower-tier evidence matters | Its multi-step DiagGuard is not adopted. Use the failure taxonomy to justify broadening evidence, not its private propagation annotations or output accuracy as our target |
| [MicroRank, The Web Conference 2021](https://doi.org/10.1145/3442381.3449905) — screened | Contrasts normal/abnormal traces for latency localization | Do not relabel our local-quantile heuristic as its PageRank/spectrum implementation; per-request spectra are not in the fixed selected pool |

Reading notes (method, experiments and limits):

- **MicroHECL** (Liu et al.): dynamically constructs call graphs, chooses
  propagation direction by anomaly type and ranks using metric correlation.
  Its evaluation uses Alibaba availability issues and compares MonitorRank and
  Microscope; the 75-issue study reports MRR 0.58 versus 0.37/0.44, and a pruning
  ablation varies correlation thresholds. Its historical
  training data, initial alarm and per-edge metric histories are stronger inputs
  than our current fixed pool. Adopt only a clearly labelled neighbourhood
  selection hypothesis; a call arrow is not a proven physical propagation edge.
- **LogCluster** (Lin et al.): weights events using IDF and lab/production
  contrast, clusters sequences and returns representatives not already in a
  knowledge base. Experiments cover Hadoop applications and two Microsoft
  systems; its outcomes are review workload and relevant-sequence precision,
  not LLM root-rank accuracy. We have no independent benign knowledge base, so we do not declare
  the first half of a case normal. The [LogPAI implementation](https://github.com/logpai/loglizer/blob/master/loglizer/models/LogClustering.py)
  was inspected as a third-party implementation, not falsely attributed as
  original author code. The similarly named CNSM log **parser** is a different work.
- **Change-point review** (Truong et al.): separates cost, search and penalties;
  its Eq. 24 and Algorithm Win use `cost(left+right)-cost(left)-cost(right)`.
  The review compares method assumptions/complexity rather than our RCA dataset.
  Narrow windows lose long-duration structure; wide windows blur short events.
  We use three widths, preserve physical bin locations and make no significance
  or true injection-time claim from the largest score.
- **Beyond Fault Localization** (Lu et al.): studies 3,500 trajectories across
  seven framework/model configurations and tests a failure-derived intervention
  on another model/dataset. Authors explicitly note single-topology limitations,
  subjectivity in process annotation and that characterization arms have one
  run. Their separate intervention is encouraging evidence for retrieval and
  verification, not proof that our one-shot selectors will improve AC@1.

Existing native BARO signed RobustScorer and SIRCL MA/trace-SC/log-frequency code
remain unchanged. New own-code mechanisms are not passed off as original tools.
No per-case labels, previous answers, dataset names, fault types or absolute
injection times are features of any selector. The user-provided dataset-shift
analysis informed general hypotheses, not an oracle selecting evidence by root.

### New active catalogue

`configs/selection_only_suite_v1.yaml` is the pending-method catalogue, **not**
an assertion that new rounds already ran. Each round gets its own immutable
registration only after the preceding round finishes both models. All model
cohorts are full remaining sets, not development samples. The original 12 unused
development policy IDs stay in historical code/configs, with replacement or
exclusion reasons listed once in that catalogue.

| Policy | Changes | Target signal and distinction |
|---|---|---|
| `diagnostic_cover_v2` | M selection | First cover different owners and metric families **among changed signals**, rather than allowing a few large deviations to occupy every slot. Supersedes overlapping coverage variants |
| `variance_shift_v2` | M selection | Variability changes even when the average barely changes: jitter, instability and variability collapse. Not BARO's signed maximum or MA's mean shift |
| `window_change_v2` | M selection | Local step/burst transitions at several scales, not only the inherited whole-period statistic |
| `trace_self_time_v2` | R selection | Operations with increased local/exclusive latency relative to inclusive latency, with sample support. Does not discard M/L/G as old trace-only routes did |
| `log_surprise_v2` | L selection | Template/bin concentrations beyond the entity's background template mix; not the most frequent template |
| `propagation_frontier_v2` | M/G selection | Observed edges joining changed entities, preferring a previously uncovered endpoint and nearby observed onsets; keeps endpoint metrics beside observed connectivity |

All mechanisms are deterministic. Only `window_change_v2` contains newly copied
native code: ruptures `CostL2`, commit `ee1c8ff8a548d54c641b2bb471562165931f31c7`.
Original bytes, SHA256, BSD-2-Clause license and the import-only adapted copy
live in `packages/rq3_selection_native/`. Other new mechanisms are explicitly
CanvasRCA-designed, with the inspirations above.

### Exact definitions and invariants

Use the existing public pool; do not rebuild preparation or change its admission
rules. In particular its R pool is already restricted to inherited TRC-L entries
with usable baselines/positive change. This turn does not create unobserved trace
operations. The selector cannot remedy evidence absent from this public pool.

For each case, compute the round-16 `balanced_additive_v1` selection once and
reuse its counts per M series, R operation, L template row, G edge and onset row
as the budget. Thus new methods are not rewarded by silently adding plots.
Public service–pod membership uses the same closure rule as the anchor; its
number can naturally vary with selected owners. Candidates, numeric values,
units, bins, log projection, trace unit conversion and renderer algorithms stay
fixed. Resulting pixels may change because the selected facts/owners change.

- Finite numeric parsing accepts scientific notation and k/M/G suffixes;
  unavailable, NaN, infinity and booleans are not treated as measured zero.
- **Coverage:** eligible M signals satisfy sigma deviation ≥3, normalized mean
  shift ≥0.1, or symmetric standard-deviation shift ≥0.5. Greedy priority is new
  owner, then new family, then strength, then fact ID. Strength is the largest
  of those normalized statistics, with sigma scaled/capped at 10.
- **Variance:** `abs(current_std-base_std)/(current_std+base_std)` when both
  standard deviations are finite/nonnegative. Both increases and decreases
  count; unchanged constants do not become anomalous through division by zero.
- **Window:** half-widths 4/8/16 *original bins*. Each side needs two observed
  values; gaps retain bin positions, not zero-imputed or concatenated clocks.
  Max L2 gain is normalized by total observed centered variance. Native cost
  and vectorized algebra are checked against one another. No cut is exposed as
  a new diagnosis, timestamp or annotation to the Solver.
- **Trace:** `max(0,exclusive_current-exclusive_base) / max(inclusive_current,
  exclusive_current) × n/(n+20)`, `n=min(base_count,current_count)`. It is a
  heuristic on existing p95 summaries, **not** subtraction of per-span durations
  or reconstruction of a call's critical path.
- **Logs:** aggregate same owner/template/bin across levels; for each bin,
  estimate its expected template count from the *other observed bins*, smoothed
  by 0.5/1 pseudo-counts and normalized by entity log exposure. Rank positive
  Poisson deviance and choose distinct owner/templates. A selected template is
  never truncated. Templates longer than 1,024 characters are ineligible because
  expanded response/list dumps cannot be read completely on the frozen canvas;
  short rows from the public pool fill the fixed budget. A final explicit anchor
  fallback handles any remaining measured-layout failure. A bin with no logs is
  not proof of instrumented zero traffic. This is burst/surprise prioritization,
  not a claim of a known normal baseline.
- **Frontier:** edge priority uses geometric mean of endpoint metric strength,
  `1/(1+absolute onset difference in minutes)` when both observed, otherwise a
  neutral 0.5 factor; double priority when just one endpoint was in the anchor.
  Rerank M/onset within the chosen endpoints. Preserve edge direction and cycles;
  do not invent edges or force all faults to propagate in one direction.

Insufficient positive eligible rows are filled from the existing anchor and then
the eligible public pool, with explicit fill IDs. An algorithm exception is not
normal fallback. Missing graph
support returns the anchor rather than fabricating a propagation chain. No-op
cases remain valid observations, not hidden failures or grounds for label-based
reranking. Internal selector scores and audit hashes never enter Solver prompts.

### Checks and interpretation

Check source equality, finite/constant/sparse values, per-field budgets, candidate
equality, deterministic order, native cost equivalence, full remaining-pool
selection differences and model-input changes. Inspect actual PNGs produced
by the unchanged renderer, including the bounded readable log selection. Preserve
all completed outcomes and stopping rules. This is adaptive coverage discovery,
not a randomized comparison of scores from progressively harder cohorts.

Diagnostic hypotheses can be plausible without working on a particular case.
Neither literature nor pairwise low selection overlap proves new AC@1 coverage.
The useful test remains how many *newly correct cases* each full-remaining round
adds, together with its cost and observed failure modes.

### CPU evidence and pending order

No additional inference was used in this amendment. On the complete union of
current remaining cases (158; Qwen 125, Gemma 104), all six selectors preserve
the source fact values, candidate sets and anchor field budgets. The following
counts describe changed **fact sets**, not new correct diagnoses:

| Pending order | Selector | Changed cases / 158 | Actual PNG changes in three CPU review cases |
|---|---|---:|---:|
| 1 | `diagnostic_cover_v2` | 156 | 3/3 |
| 2 | `log_surprise_v2` | 153 | 2/3 |
| 3 | `trace_self_time_v2` | 106 | 1/3 |
| 4 | `window_change_v2` | 158 | 3/3 |
| 5 | `variance_shift_v2` | 157 | 3/3 |
| 6 | `propagation_frontier_v2` | 153 | 3/3 |

The 158-case audit compares selected IDs and a deterministic textual evidence
projection; it does **not** claim that this projection is the pure-visual
Solver prompt. The separate 18-PNG audit checks actual decoded pixels, exact
static-prompt/candidate equality with round 16, fact-to-primitive binding,
clipping/geometry, source hashes and leakage. Six PNGs, spanning all policies
and three primary datasets, were also opened for visual inspection. The fixed
renderer still makes content-dependent grouping decisions: different selected
owners can move cards, without a new layout policy or renderer change.

Tests: 141 CPU regressions passed; native L2 algebra matches the vendored
component on normal/gapped inputs. Four native originals/license files match
upstream bytes. The 43 renderer/prompt/local-runtime files match the round-16
snapshot. Parent-integrity and source-layout checks pass. Input changes are real,
but common untouched regions make whole-packet overlaps large for R-only/L-only
methods. Sparse usable trace pools naturally yield unchanged selections.

Audit artifacts: `results/selection_only_review_20260914/final/summary.json`,
`gallery/input_audit.json` and `logs/review.md`. The earlier top-level CPU audit
is retained as a preliminary catalogue snapshot. Neither is an inference result.
No new round is registered by these checks. Each future registration recomputes
both models' full remaining cohorts after the preceding round is completed.

<a id="search-first"></a>

<a id="tournament"></a>

### DD-RQ3-TOURNAMENT-12 — At most one text evidence modality

**Date:** 2026-09-14. **Status:** adopted; supersedes the earlier pure-vision-only
transport restriction.

A tournament successor may place at most one of M/R/L/G in an adjacent text
evidence block while the remaining three modalities stay in the single real
dashboard image. Candidates and static instructions remain text. The RCA task,
method structure and output contract stay fixed, and each successor still runs
the complete model-specific unretired cohort. Two or more text evidence
modalities and multiple diagnostic images remain prohibited.

### DD-RQ3-TOURNAMENT-11 — End directly at per-dataset AC@1 thresholds

**Date:** 2026-09-13. **Status:** adopted; supersedes DD-10's AC@5 transition.

Both models must independently reach AC@1 union coverage of 80/100 in each
primary dataset and 72/90 in each RE2 dataset. That ends the tournament;
there is no AC@5 stage and no need to solve the remaining cases at top-5.
Keep complete AC@1/3/5 success-method maps. Completion is the conjunction of
all dataset thresholds for both models, not an empty remaining-case set.

Migrate preserved verified outcomes at the round-9 boundary without new
requests or historical rewrites. Test threshold completion with unsolved
cases remaining, no promotion to AC@5 and independent model stopping. Once
one model meets all thresholds, do not issue it further tournament requests
while the other continues. Existing training isolation and separate successor
qualification remain mandatory before SFT/RL.

Implementation: `tournament_ac1_v2.yaml` inherits the scientific configuration
unchanged and replaces only the stopping policy. `tournament-adopt-policy`
verifies the prior committed source artifacts, then creates immutable
`coverage/top1_completion_v2.json`. The old contract and all old registrations
and model commits retain their bytes; the mutable current state is replayed.
New registrations bind the policy hash. Resume checks that immutable lineage,
uses integer-ceiling per-dataset thresholds and retains complete success maps.
Reached thresholds can end the tournament with unresolved cases; those are
reported separately from genuinely retired top-1 successes. AC@5-only hits
never retire a case in this successor. No automatic training follows.

CPU review: 32 tests passed for legacy replay, threshold edges (71/90 versus
72/90 and 79/100 versus 80/100), unequal groups, model-independent stopping,
pending-round rejection, immutable/corrupt history, interrupted state-file
recovery, explicit successor routing and exact-request reuse. No model calls
were made for this policy amendment.

Migration completed after round 9: 3,665 referenced outcome sources verified;
all 28 original contract/round/commit files remain byte-identical. Policy hash
`15b792818d56f5ef073aa9e966d80e984d1b28de8e09e98a91e78a5a5b70d06c`.
Neither model yet meets the new stopping condition. The initial dry-run found
an older partition-version allowlist; it was updated to admit the explicit V2
contract with the same roster/isolation checks and received regression tests.
No model input, answer, score, prepared case or training split changed.

### DD-RQ3-TOURNAMENT-10 — Per-dataset transition threshold

**Date:** 2026-09-13. **Status:** its AC@5 transition is superseded by DD-11;
the per-dataset AC@1 thresholds are retained.

The revised goal requires each model to reach top-1 union coverage of 80/100
in each of AIOPS-2022, AIOPS-2025 and AegisLab, and 72/90 in each RE2 set.
All five requirements must hold for that model before its AC@5 stage begins.
The previous pooled primary 240/300 criterion is superseded, not combined
with or substituted for the five independent requirements. Each model's
successful case/method records remain separate; both models must finish.

Preserve the old coverage contract and round records byte-for-byte. Import
their verified outcomes into an explicitly versioned successor policy after
the active round completes; do not relabel requests, reinterpret scores or
rerun completed inputs. No input/renderer/prompt/recipe change is needed.
Test unequal dataset coverage (including a saturated RE2 and a weak AIOPS),
exact ceiling thresholds for 90 cases, independent models and replay/resume.
Do not begin training or an AC@5-only cohort under the superseded gate.

### DD-RQ3-TOURNAMENT-09 — Sustained mean-shift on untried remaining cases

**Date:** 2026-09-13. **Status:** adopted before expanded-cohort calls.

After eight execution rounds, Qwen/Gemma have 241/224 eligible cases and
122/137 primary top-1 successes. Expand the unchanged round-5 native SIRCL
MA component to their current eligible cases minus every prior MA target.
Its small initial subset added three/four top-1s; many remaining cases have
not tried its sustained mean-shift signal. This is an execution extension,
not a new algorithm, a whole ThinkFL reproduction or a universal-winner claim.

Keep original strict three-population-standard-deviation mean-shift ranking,
finite observations, public time split, zero-spread behavior, top-24 capacity,
explicit fill and inherited R/L/G projection. Native rankings stay CPU-side.
The fixed prompt, candidate policy, image transport and model recipes do not
change. Do not rerun retired cases or retry wrong/truncated earlier MA calls.

Before calls, verify three original-method CPU replays byte-for-byte, all
source/fact/prompt/PNG geometry audits and representative actual images.
Register separate model cohorts, reuse exact same-model requests from any
completed round, archive source and provenance, then run both models locally
and sequentially. Preserve failures and cost accounting. No attention or
training; stable monitoring every 600 seconds with no work during sleeps.

BARO's latest extension adds nine/fifteen top-1s but harms RE2-OB mean rank.
The native alternatives are complements, not globally ordered replacements.
After this unchanged expansion, evidence-ownership and temporal/card changes
remain candidates for substantial versioned exploration on small subsets.

### DD-RQ3-TOURNAMENT-08 — Native BARO on its untried remainder

**Date:** 2026-09-13. **Status:** adopted before expanded-cohort calls.

Seven rounds leave Qwen/Gemma 250/239 eligible cases, with primary coverage
114/300 and 127/300. Round 7's trace extension adds few AIOPS-2025 successes.
Round 2's BARO component found complementary cases, especially five Gemma
AIOPS-2025 top-1s in its initial 12-case subset, but most remaining cases have
never tried that method. Expand it without changing its algorithm or inputs
on previously tested cases. Do not infer population efficacy from the subset.

Use the same official BARO 0.1.9 signed RobustScorer maximum on finite source
series, native baseline/current public clock, top-24 selection and inherited
R/L anchors/selected-owner G. This is a component adaptation, not full BARO's
change-point-detection pipeline. No absolute-value substitution or private
injection time. Preserve the earlier sampling failure and wrong answers.

Register each model's current eligible set minus all its round-2 targets,
including failed/wrong outputs. Reproduce three original-method CPU cases
byte-for-byte, audit the complete gallery, inspect actual PNGs, and reuse any
exact same-model/same-case request already completed under another method.
Archive inherited configuration and native provenance before calls. Models
remain sequential and local, no attention or training, no prompt/recipe change.

This is a coverage extension grouped with its original method, not an eighth
independent algorithm. The separate evidence-ownership/temporal shortcomings
found during outcome review remain directions for later versioned changes,
not hidden repairs to this unchanged native-component extension.

### DD-RQ3-TOURNAMENT-07 — Trace support/confidence on untried remaining cases

**Date:** 2026-09-13. **Status:** adopted before expanded-cohort calls.

Round 6's unchanged log-method expansion yields 28/46 new Qwen/Gemma top-1
successes; remaining sets are 273/269, with primary coverage 97/300 and
114/300. Continue the shrinking-population search rather than treating the
first small subset as the only opportunity for another native method.

Expand the unchanged round-3 SIRCL trace support/confidence eight-operation
method. Its initial subset yielded three/seven complementary top-1 successes,
especially Gemma Aegis/AIOPS-2022, but also harmed some partial RE2 rankings.
This is a cohort extension, not a new algorithm or a complete TraceRCA system.
The original baseline threshold, harmonic support/confidence ranking, native
operation-to-pool binding, explicitly audited unbound/fill entries, eight-row
capacity, trace units and renderer remain unchanged. M/L anchors, candidate
list and the frozen tournament prompt/recipes are unchanged.

Register both model cohorts as current eligible cases minus every prior
round-3 target, including wrong/model-failed outcomes. Do not select by private
root or fault type. Verify three parent-method CPU replays byte-for-byte,
all-case source/input audits and representative actual PNGs before calls.
Identical full requests from any completed method reuse their original result.
Never rerun a retired case or resample a wrong answer for the same input.

Use preserved public pools, at most eight pinned CPU workers, sequential local
models, no attention or training. Native source and scientific config stay
unchanged. Log false causal/ownership claims separately from ranking hits;
observed low MRR is not an infrastructure failure. All prior outcomes remain.

### DD-RQ3-TOURNAMENT-06 — Expand a complementary method without retries

**Date:** 2026-09-13. **Status:** adopted before expanded-cohort calls.

Five completed rounds leave Qwen 301 and Gemma 315 unretired cases. Each of
the four native alternatives was explored on 42 cases/model, not all remaining
cases. Repeatedly introducing alternatives on the same hash-leading hard
subset would leave most cases without a chance to benefit from these methods.
The initial discovery-subset restriction must not silently replace the user's
shrinking-population coverage objective.

Expand the **unchanged** SIRCL Drain-frequency-six method to all currently
eligible cases not previously executed with that method for each model.
Round 4 yielded three/nine new top-1s and improved same-cohort primary MRR
for both models. This motivates expansion, not a universal-winner claim.
Prior BARO, trace-SC, MA results and negative results remain fully retained.
The new registration identity is an execution-cohort extension; group it with
its parent component method for method-diversity and success analyses.

Config: `tournament_log_freq6_extension_v1.yaml`, parent
`tournament_log_freq6_v1.yaml`. The `search`, `solver`, `harness`, native source,
prompt files and selected local inference projection must be identical.
Exclude every prior parent-method target, including wrong/failed model outputs,
and every retired target. Do not use a private root or fault type to choose the
extension cohort. Model cohorts remain independent; shared cases use identical
public inputs. Exact requests matching other rounds reuse their original
outcomes, even wrong ones. In the CPU audit, reproduce parent-method artifacts
on already-rendered cases without issuing requests, to verify identity.

Register both complete extension cohorts before preparation/calls. Use the
retained public pools, no raw preprocessing, at most eight pinned CPU workers.
Review all artifacts and representative actual PNGs before sequential local
Qwen/Gemma execution. Full conversations, zero-score model failures, input
hashes, native binding/fill audits and model-specific retirement are preserved.
No prompt/renderer change, training, attention or correctness retries.

### DD-RQ3-TOURNAMENT-05 — Native sustained mean-shift complement

**Date:** 2026-09-13. **Status:** adopted; qualify before model calls.

Four rounds yield Qwen 82/300 and Gemma 84/300 primary top-1 coverage. Prior
train-subset period-mean overview variants sometimes degraded MRR; preserve
that evidence. Test complementary native full-source mean-shift selection,
not another name for display-rounded MET-Z ranking or a promised improvement.

`SIRCL_MA_3SIGMA_TOP24_tournament_v1` uses the existing byte-preserved SIRCL MA
component: absolute current-mean minus baseline-mean strictly exceeds three
baseline population standard deviations; baseline zero spread is skipped.
Use the existing telemetry-derived public split/end, never injection labels.
Finite observations keep their values and temporal membership, without zero
imputation. Lossless column aliases avoid overlapping service-prefix matches;
native unrounded deviation orders all eligible public pool series, with ties
in inherited pool order. Select at most 24 series, explicitly fill insufficient
native rankings in original order, and retain the first-round R4/L2/context G.
Selected payloads and source plotting geometry are not recomputed by the tool.
Ranks remain CPU audit data, not root-cause advice to the Solver.

This is **SIRCL's MA adaptation**, not a reproduction of official ThinkFL.
The [ThinkFL v2 paper](https://arxiv.org/html/2504.18776v2), section 4.1.1,
describes pointwise n-sigma retrieval. Its [official tool implementation](https://github.com/LLM4AIOps/ThinkFL/blob/main/tool_server_all.py)
uses centered 20/10-minute windows and sample standard deviation, whereas
the preserved SIRCL MA uses before/after means and population deviation.
Do not silently merge these algorithms or transfer full-system MRR claims.

Keep prompt/template, recipes, candidates, renderer, clock and trace units
unchanged. Freeze 12 eligible cases per main dataset plus three per RE2/model
by hash42 before calls. Compare selected sets against both the original
overview and original top24 to distinguish count from ranking changes. Reuse
exact same-case/model requests, including wrong outputs. Inspect all source,
PNG, conversation and response hashes and several actual images. No training
or attention; archive all attempts and report insufficient-native fill rates.

### DD-RQ3-TOURNAMENT-04 — Native log-frequency complement

**Date:** 2026-09-13. **Status:** adopted; CPU and visual checks precede calls.

Round 3 commits bring primary top-1 unions to Qwen 80/300 and Gemma 77/300.
BARO and trace support/confidence yielded different dataset-specific repairs.
Test `SIRCL_DRAIN_FREQ6_tournament_v1` next: unchanged first-round M8 plus
node CPU/memory, original R4, and six distinct entity/Denum-template log rows.
Graph context follows selected owners as before. Fixed prompt, candidates,
model recipes and trace units remain unchanged; no attention or training.

Reuse the byte-preserved SIRCL Drain frequency component, not a rewritten
ranking labelled as that tool. Keep its global 30-template and per-owner five
template bounds; run on source public logs through the inherited public split.
Resolve native source-row indices to the existing Denum skeleton/entity/bin/
level identity exactly. Each native cluster keeps its original count; globally
order those clusters by descending count, numeric owner, then native ID.
Within a cluster consider highest-count Denum event groups first. Pick six
distinct entity/template pairs, one observed bin per pair. This is an explicit
representative-event selection, not the whole template timeline. Display the
original selected pool payload/count, not native ranks as root recommendations.
Native source/pool mismatches fail; insufficient native coverage may fill by
the original log priority with named fill IDs. Never substitute fuzzy matches.

The hypothesis is complementarity, not that common log messages are always
diagnostic. More log space may displace attention or amplify routine traffic.
Freeze 12 remaining cases per primary dataset and three per RE2 for each model
by SHA256([42, opaque ID]); exact-input no-ops reuse original model responses.
All valid wrong answers remain outcomes. Per-case source rankings, source-row
hashes, selected facts, actual PNGs, conversations and repair/break are retained.

Reference: [TORAI paper](https://arxiv.org/html/2604.13522v1) and
[FSE 2026 program](https://conf.researchr.org/details/fse-2026/fse-2026-research-papers/64/TORAI-Multi-Source-Root-Cause-Analysis-for-Blind-Spots-in-Microservice-Service-Call-).
TORAI transforms Drain-template occurrences into time series, then combines
severity, clustering, causal ranking and robust indicator analysis. Its 270
benchmark cases and ten production incidents motivate examining log evidence
beyond trace-visible nodes. Standalone components underperform its combined
method; a frequency selector is not a TORAI reproduction or an expected gain.
This round uses SIRCL's component adaptation only. Existing Drain3 0.9.11
and original source hashes are retained; no dependency/model updates.

### DD-RQ3-TOURNAMENT-03 — Two frozen Solvers, independent retirement

**Date:** 2026-09-12. **Status:** adopted before any tournament inference.

The latest user goal adds Gemma-4-26B-A4B-it alongside Qwen3.8-27B. Every
registered method is evaluated sequentially on each model's own unretired
cases. A shared case/method has identical image, candidate list and prompt
text; only the registered model-specific inference/template processing differs.
The first round includes all 480 cases for each model. Subsequent exploratory
subsets are frozen before calls, never selected by a private root label.

Compute AC@1/3/5 success unions separately. Each model switches from top-1 to
top-5 retirement only after its own 240/300 primary-case top-1 successes, and
immediately retires cases already successful at top-5. Both models must finish;
do not pool their successes or re-call a retired case. Commit a round only after
both model phases have terminal outcomes or an explicitly recorded unresolved
infrastructure state. A crash resumes the same registered method/input, not a
new sampling attempt on a completed wrong answer. No model training occurs.

SEARCH22 remains the first evidence/render method, with the already registered
frozen-template successor and visible card identifiers. Its Qwen request uses
the previously tested `card_nonthinking_v1` adapter; Gemma retains its own
unified non-thinking recipe, not Qwen's sampling override. Both keep the
8,192 output ceiling, candidate-bound top-five schema and no new attention.
Preserve all historical Qwen-only searches. Future evidence selectors should
prioritize source-faithful related-work components with public-only inputs;
an algorithm name without an actual selection change is not an intervention.

**Forward qualification.** One logical tournament smoke uses three frozen
training AIOPS cases (two AIOPS-2022, one AIOPS-2025, hash42/source coverage),
one method and both Solvers: six planned calls. The two sequential phases
share one 600-second monotonic deadline and at most 18 calls including retries;
neither the 9B model nor a training optimizer is started. The first qualification
checks the new fixed prompt structure, visible EC identifiers, each actual
model recipe, unified scoring and durable conversations. It is excluded from
coverage. CPU tests, including independent model retirement and interruption
recovery, cover the tournament state machine without spending eval calls.

### DD-RQ3-TOURNAMENT-02 — Pure vision and one frozen prompt structure

**Date:** 2026-09-12. **Status:** adopted before any tournament call.

**Execution boundary.** The user explicitly confirms that the tournament does
not train a model. CPU preparation and analysis use the existing tools venv;
the local vLLM server uses the existing infer venv. The train venv is reserved
for later learning, except CUDA-disabled synthetic CPU unit tests requiring
its installed PyTorch/test dependencies. No such test updates a real model.

**Decision.** The latest user goal supersedes the intervening permission for
one text-evidence modality. All selected incident evidence stays in one PNG.
Candidate entities and global instructions remain text. Select the RQ2.1 P0__V
template structure: SRE system; shared RCA procedure/output schema; visual
reading guide; single image; candidates; closing request. Freeze its text
template before the first call and preserve it across every tournament round.
Do not add new reasoning tips after inspecting each round's failures.

**Evidence and alternatives.** Matched actual Qwen and Gemma requests for
INC-AF408910E346 show identical RQ1.1/RQ2.1 system, task, candidates, closing
and part order; only the visual guide differs (4,003 versus 3,504 characters).
Thus the choice is not a measured superiority of one reasoning structure:
they are the same structure. RQ2.1's conditional visual grammar is the closer
starting point for variable encodings/layouts. Before freezing, adapt only
descriptions inconsistent with the actual RQ3 cards (variable series count,
public identity, metric units and selected log summaries). Source references
must use visible panel/card IDs, not fabricated addresses. Candidate IDs and
incident evidence remain variable input fields, never private-label hints.

**Consequences.** SEARCH22 supplies the first round's selection and rendering
method, not its old mutable exploration prompt. The first round is explicitly
`SEARCH22_typed_overview_template_successor_v1`; its scores cannot be called an
exact prompt replay of SEARCH22. Earlier results remain immutable. The generic
training-eval validation gate remains; a separate adaptive-tournament partition
opens the authorized 480 cases without granting optimizer access to them.

### DD-RQ3-TOURNAMENT-01 — Adaptive discovery and updated targets

**Date:** 2026-09-12. **Status:** adopted; execution adapter pending.

**Context and evidence.** The user explicitly replaces train-only discovery
with a shrinking RQ480 tournament. Prior train-only searches found complementary
successes, not one generally superior design. The latest explicit correction
is 80%, superseding the intervening 70% and the earlier provisional 75%; no
tournament inference or retirement used either earlier value.

**Decision.** Freeze the first method from the existing, cohort-matched AIOPS
comparison before any RQ480 call. Run it on all 480 roster identities. Thereafter
freeze each new method and its eligible cases before execution; completed
top-1 successes are retired permanently from further tournament calls. Track
deduplicated ever-success lists at AC@1, AC@3 and AC@5 for every case, together
with method/source/input/record hashes and its first successful round.

The top-1 phase ends when at least **240 of the 300** AIOPS-2022, AIOPS-2025
and AegisLab cases have a verified AC@1 success (80%). The two RE2 slices are
still executed and tracked, but do not contribute to that numerator or
denominator. At the phase transition retire remaining cases already having a
verified AC@5 success; do not call them again to rediscover the same result.
Then test only cases with no top-5 success until all remaining cases have one.
Do not reset the denominator after model errors, missing artifacts or rendering
failures. Record unresolved infrastructure separately and recover the same
input; retain wrong answers and other terminal model outcomes without retries
until correct. Judge the transition between committed batches, not from
unpersisted partial outputs. Every final first-round outcome remains available.

**Interpretation.** Tournament union coverage is an adaptive, answer-informed
discovery statistic, not a deployable selector's accuracy or evidence that the
visible reason is faithful. RQ480 is now repeatedly exposed to design feedback.
Private labels may score and retire cases but never supply renderer facts,
candidate additions, per-case prompts or the Solver answer. Global design
changes must be reproducible from public telemetry. Preserve RQ480/TrainTicket
exclusion from training examples, rollout rewards and optimizer updates; this
does not restore untouched-evaluation status after adaptive discovery.

**Success objectives after learning.** AIOPS-2022 MRR >0.65, AIOPS-2025 MRR
>0.65 and overall 480-case MRR >0.75; these supersede >0.54/>0.65 targets.
Report Composer and Solver input/output cost separately. A successful union
does not satisfy these learned single-pipeline targets. SFT and actual RL
follow only after tournament completion and their own updated qualification.

**First method and preparation.** Register SEARCH22 typed overview: native
top8 plus public node CPU/memory overview, explicit owner type in the real
dashboard, original static membership guide, original non-thinking recipe.
In the common B cohort (12 cases per dataset), its MRR .520833/.429167 gives
a joint .475000, just above owner-header .473611. On the separate C cohort
the same method only reached .354167/.194444; both results are retained and
the first-round choice is not claimed a universally best method. SEARCH40's
new citation contrast .444444/.236111 does not replace it. Do not silently add
the citation prompt to the frozen SEARCH22 round: that would be a new method.

`configs/tournament_v1.yaml` records the 4/5 threshold and updated targets.
Reuse the existing per-case pool compiler, with a separately named adaptive
tournament partition adapter, to materialize all 480 CPU-side public pools from
the retained canonical V3 corpus, using at most eight independent-core workers.
The legacy `prepare --partition eval` path correctly requires frozen trained
policies and must retain that gate; do not fabricate a validation freeze to
open it. This is not raw-data conversion, training or a model call. RQ480 calls
remain pending the resumable tournament adapter, exact-method replay, gallery
inspection and applicable qualification.

**Consequences.** All four card/silhouette families, public-only evidence and
candidate policies, renderer, prompt and RQ3-local recipe experiments remain
authorized. The latest user clarification permits at most one M/R/L/G modality
to carry diagnostic evidence in text; the remaining at least three stay in
the same single real dashboard PNG. Pure visual is still allowed. Keep the
selected modality and its actual text/image fact bindings explicit, and do not
silently change SEARCH22's pure-visual reference. Candidate lists remain text.
Keep no new attention, immutable
attempt history, bounded small representative development batches, and the
600-second monitoring interval. The RQ-wide call cap remains removed; bounded
qualification rules remain. The obsolete training dispatcher is not an
automatic successor. Do not alter old records or their scientific status.

### DD-RQ3-SEARCH-40 — Visible card references and cumulative analysis

The user requests visible unique card IDs and source references in the reason,
and also cumulative analysis of every earlier attempt. Add an explicit optional
RQ3 card-heading field and a static citation guide. Keep native24 evidence,
diagnostic pixels, candidates and non-thinking recipe fixed on cohort C. No
claim that source citation alone proves causality. Before more broad evaluation,
refresh the all-attempt matrix and study within-cohort repair/break patterns,
including complementary candidates with worse aggregate MRR. Different cohorts
and source/identity versions must not be pooled as one controlled comparison.
Protocol: [SEARCH40](RQ3_citations_20260912.md). No eval/SFT/RL.

### DD-RQ3-SEARCH-39 — Native anchor with peer-relative evidence selection

Keep native top8; fill the remaining16 metric slots using an equal blend of
native rank and leave-one-owner-out normalized mean-shift contrast. Same C
training cohort and reference recipe, no derivative/counter-type guessing.
[Algorithm, primary sources and checks](RQ3_peer_shift_20260912.md).

### Execution amendment — resume exploration, defer typed-overview RQ480

2026-09-12. The user resumes exploration toward the existing targets and defers
the intervening full-RQ480 request. That evaluation made no model calls. Resume
SEARCH38's registered training-only contrast, preserving its partial previews
and reusing exact qualified reference PNGs/packets/prompts where byte identity
is established. Inspect current actual PNGs before committing the new request.
The old pause and recap remain historical snapshots, not current execution
authority. No eval tuning or automatic old SFT/RL lifecycle is authorized.

### DD-RQ3-SEARCH-38 — Non-thinking output presence-penalty contrast

Keep SEARCH34's native24 evidence, actual PNGs, prompt and sampling except
presence1.5→0. Same additional24 train cases, no new attention or training.
[Registered rationale and checks](RQ3_presence_penalty_20260912.md).

### DD-RQ3-SEARCH-37 — Soft within-owner shape diversity

Train-only native24 paired selection test, MMR-inspired lambda=.75. Preserve
native renderer and request; change only the public selection policy and its
existing selected-entity dependencies. [Protocol](RQ3_shape_diversity_20260912.md).

### DD-RQ3-SEARCH-36 — Continuous raw-axis span floor

Train-only paired24-case test at fraction0.5 against SEARCH34 native24.
Only metric-axis prominence changes; no source, selection, prompt, request or
scorer change. Full rationale, source review, bounds and checks:
[registered axis-span protocol](RQ3_axis_span_20260912.md).

### DD-RQ3-SEARCH-35 — Entity-first coverage at fixed24 metric slots

2026-09-12; adopted train-only paired development, before calls. SEARCH34's
native24 selection partly improved the added cohort but often repeats related
series from one owner and can omit important cross-level evidence. Test the
existing greedy coverage rule with the same public membership projection as
the reference, rather than dropping that projection as legacy coverage_v1 does.

`search_expanded_coverage24_v1.yaml` selects the same SEARCH33/34 cohort and
public pools. The only resolved-config difference from SEARCH34 is selector
`coverage_membership_v1`: in each of24 slots, prioritize a previously unseen
owner, then a previously unseen metric-name family (digits replaced with#),
then native rank and the existing stable fact-ID tie order. This is the existing
project-owned coverage algorithm, not a new paper implementation or semantic
correlation clustering. Family novelty is global across selected rows; it does
not establish independence or guarantee every candidate receives a row.

The new policy differs from coverage_v1 only by including related public
service/pod name-membership facts. No old policy changes. Native24 remains
the paired reference. Keep24 metric slots, exact old renderer/prompt/recipe,
candidate set/order, timing/units/projection, and trace/log selection. Existing
selected-entity rules can change G edges/onsets/member rows. Report that full
policy intervention, not a pure M-only or equal-information contrast.

One batch:24 calls,12 per AIOPS dataset, concurrency4,3600seconds, one PNG,
no attention/Composer/training/validation/eval. Checks must establish native
baseline replay, greedy selection equivalence, unchanged source facts,
unchanged R/L, correct public membership and real selected-owner/pixel change.
Use identical three actual dense/sparse PNG checks plus CPU regression; no
selected fact may be dropped to force a layout. Retain every failure and
complete answer, no correctness retry, archive source before inference.

Compare paired MRR/AC/AVG/cost against native24, one exploratory two-dataset
Pratt-Wilcoxon/dz/Holm family. Report owner/family redundancy and evaluator-only
root association alongside failures. Neither greater owner coverage nor one
favorable small-sample score qualifies the method for480eval or SFT/RL.

### DD-RQ3-SEARCH-34 — Native24 versus compulsory node overview

2026-09-12; adopted, train-only paired development, registered before calls.
SEARCH33 weakened to .354167/.194444 on 12 additional AIOPS cases each.
Five cases omitted direct root-associated telemetry, and several answers
overinterpreted incidental node CPU/memory changes. That motivates testing
budget allocation, without encoding their private roots into a new selector.

Use `search_expanded_native24_v1.yaml` on exactly SEARCH33's 24 cases and
unchanged public pools. Replace native top8 plus per-node CPU/memory overview
with the already implemented `ranked_membership_v1`, metric_limit24. This
selects native ranked series without compulsory node additions. Keep the
same renderer, typed owner labels, static prompts, candidates, trace units,
sampling, output enum and scorer. No new production algorithm or prompt.
R/L selection is unchanged; G/onset/member selection follows the existing
public selected-entity rules and can consequently change. Report those
downstream changes: this is a whole evidence-policy contrast, not a pure
metric-encoding experiment or equal-information claim. Metric counts change
from 20–30 to at most24; chart density/readability can change as a consequence.

Hypothesis: a broader anomaly-ranked application/pod evidence allocation may
outperform compulsory node overview. The opposite result is equally retained.
This is not a reproduction of MicroRCA-Agent or its symmetric-ratio filter.
Its preprint (arXiv:2509.15635v1, sections3.4/4) motivates examining metric
selection but uses supplied fault windows and multi-stage text summaries,
which are not transferred. Its competition score is not our MRR. See the
focused source record below; the paper was already in the reference guide.

Bound:24 new local Qwen Solver calls, four concurrent, 3600-second supervisor.
No validation/eval, attention, Composer calls, SFT/RL, raw-data processing or
private-answer feedback to either selector or renderer. Precall checks replay
selection/projection, verify exact cohort and candidate identity, all source
and primitive bindings, static prompt/recipe equality and actual PNGs. Retain
render failures rather than silently drop selected facts. Archive inputs and
source bytes; preserve all completed/failed calls without correctness retry.

Report paired per-dataset MRR/AC/AVG and input/output cost versus SEARCH33,
repair/break/tie, all full answers, fault/granularity strata and offline-only
direct-root association. Pratt-Wilcoxon/dz, one two-dataset Holm family, are
exploratory after repeated development, not confirmatory significance.
Do not extrapolate this policy's24 observations onto SEARCH22's other24.

#### Focused source record: MicroRCA-Agent

Pan Tang et al., arXiv:2509.15635v1 (19 September2025), technical-report
preprint; no conference acceptance verified. [Paper](https://arxiv.org/html/2509.15635v1),
[paper-linked repository](https://github.com/tangpan360/MicroRCA-Agent).
Checked2026-09-12: abstract, preprocessing, modality methods, result analysis,
ablation and conclusion; repository identity/README, not a code reproduction.
It combines filtered logs, trace anomalies and hierarchical metric summaries.
Metric filtering compares median/p99 between supplied normal/fault periods;
the metric stage uses two LLM summaries. Its table reports log+metric51.27
versus three-modal50.71; these are competition points, not paired CanvasRCA
MRR. The paper also shows hallucinated trace relationships in failure cases.
The README and paper advertise different aggregate scores; do not resolve
that by choosing the larger one. No controlled result establishes that our
native24 selector, visual layout, or label-blind windows benefit. The present
transfer is only a hypothesis about selection and distractors, tested against
our own fixed Solver. No competition templates, fault-time inputs or external
training artifacts are imported into the runtime.

### DD-RQ3-SEARCH-33 — Broaden the best observed common-cohort policy

2026-09-12; adopted train-only development registration, not final evaluation.
SEARCH22's typed node overview has the highest observed two-dataset mean on
the common24 (.475), almost tied with owner-header (.473611). After many
adaptations on those cases, a new case slice is more informative than another
cosmetic change on the same answers. Keep SEARCH22's evidence selector,
typed metric labels, public membership, complete prompt-only candidates,
one PNG, static guide, request recipe and scorer unchanged. This is a fixed
deterministic policy test, not a claim about a trained Composer.

Use `search_expanded_overview_v1.yaml`: the only resolved-config difference
from `search_typed_overview_v1.yaml` is case_offset6 to18. The existing
hash42/source-coverage/distinct-event-group procedure selects12 training
cases per AIOPS dataset. Register identities before reading private outcomes;
assert no overlap with prior search cases/groups. No validation, eval,
TrainTicket, raw-data regeneration, attention, SFT or RL. The full existing
V3 corpus stays unchanged. Old pools without current public-identity and
membership fields are not compatible; compile only the selected24 pools.

Bound:24 new local Solver calls, concurrency4, supervisor3600seconds. Reuse
all valid completed units; preserve model failures and do not resample them.
Unchanged qualified code gets cohort, input, source, layout, leakage and
request checks plus actual PNG inspection before GPU submission. Archive
the executable sources/configs and every attempted input/output/conversation.

Report this new24 slice separately and the combined48 distinct training
cases for exactly the same policy. These are descriptive development results;
old/new differences are cohort differences, not paired treatment effects.
No superiority test against another policy that lacks the new24 observations.
Any larger sample weakness informs subsequent train-only diagnosis; it cannot
be hidden by dropping cases or selecting each dataset's best different policy.
Targets and the later shortlist/validation/frozen480eval order remain unchanged.

## RQ3 successor: search useful diagnostic programs, then learn to compose them

Date: 2026-09-12. Status: **eight-call successor interface qualification passed;
train-only policy/prompt development in progress**. The qualification is not
evidence of meeting the MRR targets. Current small-batch protocol:
[development batch 1](RQ3_search_development_20260912.md).
The latest same-day user amendment supersedes conflicting statements below:
no new attention collection; pure-vision main pipeline; exploratory search,
then one frozen candidate's complete eval **before** small SFT/RL qualification
and eventual full SFT/RL. Diagnostic text twins remain offline fidelity/debug
artifacts, not a replacement main method. The latest clarification keeps the
candidate entity list in the prompt, not in the image. Other prompt text contains
static guidance only; all selected diagnostic facts are visual. Candidate-list
policies may change through explicit public-only rules, with coverage audited
offline and no private-root-dependent filtering. Previously recorded attention
and old results remain intact. Eval is not a source of training examples or
case-level prompt-search feedback; final reporting identifies repeated exposure.
This implements the user's latest search-first objective. It supersedes the
old fixed action menu and immediate full-lifecycle schedule for future work,
not the identity or status of any completed experiment/checkpoint. The existing
`rq3.yaml` remains disabled until a successor is implemented and qualified.

### 1. Outcome and protected data

The deployed system remains a Qwen3.5-9B Composer followed by a Qwen3.8-27B
one-call Solver. First find useful **policies**, not an oracle dashboard chosen
using each evaluation answer. Then train the Composer with SFT and RL to emit
one good program without deployment-time best-of-N Solver calls.

Targets, after SFT+RL, are MRR >0.54 separately on AIOPS-2022 and AIOPS-2025,
and overall >0.65. Report both pooled-480 MRR and the equal-weight mean of the
five dataset MRRs; require both to exceed the overall target, rather than choose
the more favorable aggregation afterward. Also report the three-main-dataset
macro, per-fault and root-granularity results. Targets are not a guarantee of
attainability. A sampled development score cannot satisfy the final objective.

Keep the registered 150 train / 70 validation per AIOPS dataset. Group/window
isolation and the full TrainTicket training holdout remain unchanged. The 480
eval cases never supply search rewards, prompt examples, checkpoint selection
or failure-driven development feedback. Previously inspected validation is
development-exposed validation, not a newly untouched confirmation set.
Candidate validation may select a checkpoint, but automated mutation uses
training trajectories only, not validation answers or per-case failure traces.

### 2. Why expand more than the preset list?

Current evidence: the matched 140-case Composer comparison improved actual
render success from 71/140 BASE to 135/140 SFT. It did **not** test Solver RCA.
The old menu assigns one encoding to an entire modality and offers only three
canvas grids. Good JSON and a larger menu do not establish useful diagnosis.

RQ1.1 suggests selective topology vision can help Qwen while full vision often
does not. Its direct-root evidence coverage finding motivates auditing what
is available and selected; it does not prove that absent direct-root telemetry
means every indirect or host/child diagnostic clue is absent. RQ2.1 warns that
many visually plausible redesigns are ineffective, and metadata changes can
be mistaken for actual input changes. See the current
[combined report](../../../docs/RQ1_1_RQ2_1_Findings_2026-09-11.md).

We therefore optimize three independently recorded blocks:

1. **Evidence policy:** which public observations and relationships to show.
2. **Presentation program:** how to group, encode and allocate space to them.
3. **Solver interpretation:** task instructions and the effective inference
   recipe, versioned independently of the two Composer blocks.

### 3. Evidence policies: diagnostic contrasts, not just highest anomaly scores

The full canonical public pool remains CPU-side. No unbounded metadata dump is
allowed into either prompt. Start from the existing bounded catalog and test
public, label-blind alternatives:

- Multi-granularity coverage: preserve service, pod and host relationships and
  represent plausible resource-origin and application-origin symptoms.
- Contrast bundles: anomalous series plus comparable ordinary references;
  local versus inclusive trace latency; caller/callee or sibling comparisons.
- Temporal/propagation bundles: measured onset order and directed relationships,
  distinguishing statistical alignment from a proven causal propagation path.
- Redundancy-limited catalog retrieval: allocate finite slots across entity,
  modality and metric family before spending remaining slots on salience.

These are hypotheses, not completed tools. Existing native analyzers remain
the numerical authority; a new statistic requires a separately tested public
definition. Never promote a private root label to a card priority. Candidate
policy is a separate versioned public-only decision; selected IDs must retain
their canonical anonymous binding. Keep values, units and time semantics fixed.
A policy may select fewer facts; a renderer may not silently remove selected
facts. The text twin of a selected set distinguishes a bad selection from a
bad visual presentation. Pure-canvas remains the learned target; T and TPV are
strong controls, not discarded when they win.

### 4. Mixed symbolic/continuous design language

**User refinement, 2026-09-12 — DD-RQ3-CARD-2 (adopted).** A card and its
silhouette are equivalent information objects, with exactly one of each per
bundle. The successor supports four grouping families:

| Family | Information unit | Required rendering behavior |
|---|---|---|
| Modality | All selected facts of one M/R/L/G region | At most one outer card per included modality; absent modalities need not be added |
| Temporal | A public relative-time interval or snapshot | Order cards chronologically, show a large 1-based index and relative interval; no label-time anchor |
| Per-case | The current incident's selected abnormal evidence, any region subset | One compound card may contain several internal plots without becoming several cards |
| Evidence | An explicit selected fact or combination of abnormal facts | Mixed-region bundle permitted; facts are bound explicitly and not inferred from a free-text claim |

These replace the old assumption that every card has exactly one modality.
Internal M/R/L/G facets are drawing primitives, not additional selectable cards
or silhouettes. A compound card's full fact inventory must remain intact.
Grouping is tested independently of evidence selection: changing only grouping
keeps the same selected facts. A temporal comparison may require an explicitly
different, time-resolved evidence projection; do not claim an equal-fact
comparison after replacing a whole-case statistic with a window statistic.
The first temporal renderer accepts only facts wholly attributable to its
registered interval. Untimed or interval-spanning facts fail this check rather
than being silently assigned. Source-resolution metric/trace projection is a
separate required producer task, not an already implemented capability.

Per-case currently means the one incident being diagnosed. Cross-case retrieval
or exemplars are not introduced by this grouping rule. Any later use requires
an explicit train-only retrieval/isolation policy. No eval-case answer may enter
another case's image or prompt.

Evidence: latest user design; oversized log/blank-space CPU previews in
`results/search_first_v1/`. Rejected: merely renaming the existing regional
bundles, splitting selected facts invisibly, and adding large chronological
indices to cards without real temporal scope. Old checkpoints and results
retain their old grammar; forward SFT/RL must learn the successor grammar.

Replace the single modal preset choice with a typed **scene program**:

| Component | Action | Held fixed |
|---|---|---|
| Selection | Card set and public retrieval-policy parameters | Full source, candidates, labels inaccessible |
| Grouping | Related cards organized into a hierarchy | Card facts and identity |
| Encoding | Per-card eligible plot/matrix/table choice | Numbers, units, direction, axis meanings |
| Composition | Recursive horizontal/vertical splits with real-valued ratios | No overlap, complete cards, header exclusion |
| Emphasis | Space allocated through split ratios and grouping | No answer-derived emphasis or invented anomaly labels |
| Readability | Bounded gutter/legibility and raster scale | Complete labels and ordinary chart semantics |

The initial implementable continuous core is a **binary split tree**. Leaves
are selected card IDs; internal nodes specify axis and ratio. A ratio such as
0.613 is a request for a relative share, not an enumerated preset. Minimum
dimensions come from the same content-aware renderer capacity model. The CPU
layout compiler projects a requested split into its feasible interval and
records both requested and realized ratios. Impossible trees fail explicitly;
they are not repaired by dropping evidence. Integer pixels necessarily quantize
continuous requests. Identical realized layouts are semantic no-ops, not new
independent experimental actions.

This tree is a tractable first grammar, not every possible dashboard: it cannot
express every non-slicing floorplan. Its value is an interpretable, bounded
constraint system. Later graph-layout or local chart controls are added only
when failures show that this representation is restrictive. No arbitrary
JavaScript/Python, freely synthesized pixels, decorative texture optimization,
dual-axis deception or evidence-changing rescaling is permitted.

Scientific lineage: Penrose separates meaning from constraint-based drawing;
Scout explores high-level grouping/order/emphasis. Our exact split projection
is a new, simpler engineering implementation, not a reproduction of their
optimizers. [Penrose](https://penrose.ink/media/Penrose_SIGGRAPH2020.pdf),
[Scout](https://arxiv.org/html/2001.05424).

### 5. Search efficiently before training

#### 5.1 Work in reusable policy space

Search transferable rules such as selecting complementary temporal evidence,
putting a graph beside related traces, or enlarging a crowded log card. Do not
search fixed case-ID-to-answer mappings. A program can use only catalog IDs
resolved for its current public case. Learning data must vary anonymization
without changing physical evidence, so numeric IDs cannot become root priors.

Start with a small family covering the existing fixed/SFT path, stronger
coverage/contrast selection, geometry changes and a minimally clarified Solver
prompt. Vary one block at a time initially; then test combinations. Keep the
unchanged Solver as an anchor when its prompt/configuration is altered.
Do not sweep every parameter combination. The first actual candidates and
their exact train-case roster will be registered before their calls.

#### 5.2 Three-cost evaluation ladder

1. **CPU rejection:** binding, exact selected-fact coverage, geometry, legibility,
   leakage, deterministic rendering and prompt/context capacity. No Solver call
   for an invalid drawing; record the failure without replacement.
2. **Matched train-case racing:** all candidates at a rung use exactly the same
   balanced AIOPS cases, seeds and Solver version. Begin with small connected-
   group-compatible blocks, promote promising and behaviorally distinct
   candidates, and add cases without redoing valid requests. Preserve a small
   exploration quota so noisy early failures do not eliminate every alternative.
3. **Validation check:** evaluate a small shortlist on all 140 validation cases.
   Compare both datasets, paired gains and failure rates; a high average cannot
   hide a severe regression in one dataset. Limit validation peeking and freeze
   before eval. A winner of a tiny search batch is provisional.

Keep a verified quality/diversity archive indexed by interpretable behavior
(e.g. multigranularity coverage and topology area), alongside a quality–token
Pareto frontier. These archive bins summarize solutions; they are not a full
Cartesian grid search. Distinguish actual measured utility from a surrogate
estimate. Initially omit a learned surrogate; add a small CPU predictor only
if acquired data demonstrate useful out-of-sample ranking of candidates.

SAIL motivates expensive-evaluation allocation and inspecting encoding bias;
GEPA motivates trace-guided prompt mutation and retaining complementary
candidates. Their evaluators and tasks differ from RCA; neither promises our
target MRR. [SAIL](https://arxiv.org/html/1806.05865),
[GEPA](https://proceedings.iclr.cc/paper_files/paper/2026/hash/0e9e708b6f48e14fd0ac29e167413f76-Abstract-Conference.html).

#### 5.3 Feedback and reward separation

An optimizer may receive evaluator-produced training rewards and sanitized
failure categories. The acting Composer/Solver receives public evidence only.
Mutated global prompts must not contain case-specific answers, dataset/root
fingerprints, absolute injection time or evaluator-private features. Natural-
language reflection is a proposal mechanism, not proof of the failure cause.
Every accepted mutation still needs an actual paired Solver comparison.

### 6. Then SFT and genuine RCA RL

Format SFT for the expanded grammar reuses legal train-case examples; utility
distillation may additionally use verified train-only search winners, but is
reported separately from label-free format SFT. Preserve the old step-320
checkpoint and input contract. Do not treat new-layout replay as old inference.

RL uses the existing RLOO four-independent-program group and frozen Solver
version during an update/training branch. Scores come from the unchanged
granularity-aware top-5 RCA scorer. Start with RR-dominant utility and a bounded
cost penalty; include both models' actual input/output costs. Failed drawings
remain failures; infrastructure faults are not low-reward training data.
Record the exact sampling distribution/log probabilities; changing grammar or
decoding requires a matching policy-loss implementation and qualification.

Two RL seeds remain the main robustness check. The earlier immediate RR-only
and imitation comparison branches are **deferred**, with code preserved, to
prioritize the main pipeline. They can be added later with a written compute
allocation; the latest amendment removes the total call cap. Deployment evaluation is one Composer output
and one Solver call, not best-of-four. At least one SFT and one real utility-RL
stage must complete before claiming the user's post-training objective.

### 7. Explain improvements and failures without claiming hidden reasoning

For each executed plan record:

`public pool → catalog → selection → drawn primitives → full request → ranking`

Record absent direct entity telemetry, lost catalog coverage, selection omission,
render infeasibility, model-format failure and a wrong diagnosis after valid
rendering as distinct events. These observational categories are not causal
proofs. One-factor matched edits establish conditional input effects; a few
content×design and design×Solver anchor swaps check interactions. Keep failed
and null-result programs, not just archive winners. In particular, improving
render legality is not improving RCA, and improving an individual dataset is
not transfer. Historical attention remains diagnostic and never a reward;
the latest amendment disables its collection in this successor.

Before final evaluation, freeze which counterfactuals will be used for
interpretation. Broader ablations may follow the working main pipeline, but
the indispensable input/action/outcome trace must be recorded from the start.

### 8. Accounting and run boundaries

The read-only call database audit on 2026-09-12 found 296 Composer +25 Solver
initiated/completed calls. No training or inference process was active. Every
future model request, including a reflection/mutation request and retry, must
be recorded cumulatively. This is local compute accounting, not API billing.

**Latest user amendment:** the total 40,000-call cap is removed. The table below
is the preceding planning envelope, retained for cost estimation, not an active
hard limit. Explore small representative subsets; each batch still has an
explicit request/time envelope. Preserve old accounting and record new attempts
in successor accounting without rewriting historical call identities or results.
Every method, mutation, failure and measured effect must be saved to disk.

| Allocation | Maximum calls |
|---|---:|
| Already consumed | 321 |
| Search, including shortlist validation and prompt mutation | 8,000 |
| Two RL seeds: 300×3 traversals×4 programs×2 roles×2 seeds | 14,400 |
| Four checkpoints per RL seed on 140 validation + SFT validation | 2,520 |
| Final 480: four fixed controls + BASE/SFT/two RL seeds | 5,760 |
| Reserved matched explanation/intervention calls | 2,000 |
| Qualification, repairs and unallocated contingency | 6,999 |
| **Former envelope, no longer a hard maximum** | **40,000** |

These are estimates, not orders to spend them. Each search batch needs its own
bounded maximum and resource check. All old pending 38,000-call phase schedules
are superseded for execution; they must not run alongside this allocation.
The 480 evaluation set is not opened when search plateaus. Report failure to
reach the target honestly rather than alter scoring, exclude hard cases or
use eval to continue tuning.

Eight CPU workers may prepare bounded queues; single-GPU model switching is
batchwise, not per case. Keep checkpoints latest-plus-every-20 and preserve
optimizer/RNG/rollout version. All requests and writes are resumable. No model
calls occur until appropriate static/CPU/visual review and bounded qualification.
Stable live monitoring: every 1,200 seconds, no work during sleep.

### DD-RQ3-SEARCH-1

**Date:** 2026-09-12. **Status:** adopted for successor development.

**Decision:** search constrained, mixed discrete/continuous diagnostic programs
before a new SFT+RL run; optimize Solver instructions in a separate versioned
block. Preserve the scorer and data isolation; the latest user amendment removes
the total call cap while requiring small, fully recorded search batches.
**Evidence:** user authorization; completed BASE/SFT validity comparison;
RQ1.1/RQ2.1 conditional visual effects; literature review linked below.
**Rejected:** merely enumerating more presets; unrestricted pixel generation;
claiming reflected explanations are causal; replacing the requested RL stage
with prompt search; repeatedly tuning against the 480 eval answers.
**Consequence:** old activation remains disabled. Qualification and small
train-case search precede training. No numerical improvement is claimed yet.

See [research evidence](#design-search-literature).

<a id="design-search-literature"></a>

## RQ3 research: constrained design and efficient exploration

Verified 2026-09-12. Question: which mechanisms expand a Composer beyond fixed
presets while making successful and failed actions inspectable and reducing
expensive Solver evaluations? Scope: dashboards, computational/interface
design, vector graphics, engineering optimization, program/prompt search.
Queries included `Penrose Scout constraint layout`, `surrogate assisted
illumination design`, `GEPA ICLR 2026`, `differentiable vector graphics`,
`BOHB TuRBO expensive evaluation` and `LIDA visualization generation`.
Use primary proceedings, author papers and official code; existing references
are a discovery map, not evidence of correctness. This is not exhaustive.

### Load-bearing mechanism records

#### Penrose: separate meaning and presentation

Katherine Ye, Wode Ni, Max Krieger, Dor Ma'ayan, Jenna Wise, Jonathan Aldrich,
Joshua Sunshine and Keenan Crane. *Penrose: From Mathematical Notation to
Beautiful Diagrams*, SIGGRAPH 2020 / ACM TOG 39(4), article 144;
DOI 10.1145/3386569.3392375. [Author page](https://penrose.cs.cmu.edu/siggraph20),
[paper](https://penrose.ink/media/Penrose_SIGGRAPH2020.pdf),
[code](https://github.com/penrose/penrose).

Reviewed language/architecture, compiler, optimization, examples/performance
and limitations. Domain/Substance/Style separate relationships from drawing;
constraints and objectives become numerical optimization. Mathematical and
graphics examples plus random program stress tests show expressiveness;
constraint conflicts and optimizer cost remain limitations. Convergence is
not a feasibility certificate. RQ3 borrows typed semantics and checked layout
constraints, not the optimizer implementation or a promised RCA gain.

#### Scout: explore high-level constraints

Amanda Swearngin, Chenglong Wang, Alannah Oleson, James Fogarty and Amy J. Ko.
*Scout: Rapid Exploration of Interface Layout Alternatives through High-Level
Design Constraints*, CHI 2020; DOI 10.1145/3313831.3376593.
[Author PDF](https://chenglongwang.org/data/Swearngin_Scout_CHI_2020_v19.pdf),
[full text](https://arxiv.org/html/2001.05424),
[institutional venue record](https://dub.washington.edu/posts/2020/chi2020papers.html).
Official source repository not verified.

Reviewed method, 18-person within-subject evaluation, results and discussion.
Grouping, order, emphasis and alternatives become layout constraints. Diversity
increased; expert layout quality did not significantly improve. This motivates
searching structured alternatives, not rewarding novelty. RQ3 should preserve
failed and useful variants, then judge actual RCA utility rather than aesthetics.

#### SAIL: retain varied verified solutions

Adam Gaier, Alexander Asteroth and Jean-Baptiste Mouret. *Data-Efficient Design
Exploration through Surrogate-Assisted Illumination*, Evolutionary Computation
26(3), 381–410, 2018; DOI 10.1162/evco_a_00231.
[Institutional record](https://pub.h-brs.de/frontdoor/index/index/docId/3705),
[full text](https://arxiv.org/html/1806.05865),
[paper-linked code](https://github.com/agaier/sail_ecj2018).

Reviewed surrogate/acquisition method, airfoil and 3D engineering experiments,
encoding comparisons, measured versus predicted performance, computational cost
and discussion. The method explores diverse high-performing designs using
expensive simulation selectively. Surrogate error, scaling and infeasible
simulations matter. RQ3 can expose design-family biases through an archive;
predictions only schedule real tests, never certify RCA quality. Initially use
measured outcomes without a surrogate; add one only after ranking validation.

#### GEPA: use traces to propose, measured outcomes to accept

Lakshya A. Agrawal et al. *GEPA: Reflective Prompt Evolution Can Outperform
Reinforcement Learning*, ICLR 2026 conference.
[Proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/0e9e708b6f48e14fd0ac29e167413f76-Abstract-Conference.html),
[paper](https://proceedings.iclr.cc/paper_files/paper/2026/file/0e9e708b6f48e14fd0ac29e167413f76-Paper-Conference.pdf),
[official code](https://github.com/gepa-ai/gepa).

Reviewed formulation, reflection/mutation, Pareto sampling, six-task evaluation
and candidate-selection ablations. Experiments use Qwen3-8B and GPT-4.1 Mini,
not telemetry RCA. Complementary candidates can avoid greedy stagnation;
results depend on task, merge policy and validation budget. RQ3 can mutate
prompts from sanitized training feedback, but must verify actual paired effects.
Verbal reflection is neither hidden-thought recovery nor causal credit proof.
Search prepares rather than replaces the requested SFT and real utility RL.

### Screened complementary sources

These primary abstract/project/method descriptions were screened, not audited
as complete reproducible algorithm implementations.

| Work / verified venue | Primary source | Transfer and limitation |
|---|---|---|
| Romera-Paredes et al., FunSearch — Nature 2024, online 2023 | [Paper](https://www.nature.com/articles/s41586-023-06924-6) | Search compact policies inside a fixed evaluator; do not copy its very large cheap-evaluation budget or run arbitrary generated code. |
| Falkner, Klein, Hutter, BOHB — ICML 2018 | [Paper](https://proceedings.mlr.press/v80/falkner18a.html) | Multi-budget allocation; our first matched case-block racing is not a faithful BOHB reproduction. |
| Eriksson et al., TuRBO — NeurIPS 2019 | [Paper](https://proceedings.neurips.cc/paper/2019/hash/6c990b7aca7bc7058f5e98ea909e924b-Abstract.html) | Local continuous search; do not encode categorical layouts as ordered real numbers. |
| Victor Dibia, LIDA — ACL 2023 System Demonstrations | [Paper](https://aclanthology.org/2023.acl-demo.11/) | Modular visualization construction/refinement; generative infographics are not truthful telemetry. Demo track, not main track. |
| Li, Lukáč, Gharbi, Ragan-Kelley, diffvg — SIGGRAPH Asia 2020 / ACM TOG | [Project, paper, code](https://people.csail.mit.edu/tzumao/diffvg/) | Inspectable vector parameters; sampled RCA RR is not a differentiable raster loss and free-pixel adversarial optimization is rejected. |

Existing DashBot/Vega-Lite/Draco references supply context, not proof of RCA
gain. Secondary summaries and unverified Design Adjectives code were not used
as implementation authority. No arbitrary venue upgrades were made.

### Decision map

| Proposed action | Evidence type | Required project test |
|---|---|---|
| Semantic content plus constrained continuous layout | Penrose/Scout methods; project adaptation | Fact equality, actual pixels, clipping and readability |
| Keep multiple successful design families | SAIL/GEPA in other domains | Paired AIOPS utility and per-dataset regressions |
| Small matched blocks before scaling | Engineering inference from expensive evaluation | Growing balanced rosters, no invalid-result dropping |
| Search then SFT+RL | Our hypothesis, not proved by these papers | Frozen Solver and post-training eval |
| Explain via controlled changes | Project intervention design | Selected facts, layout, prompt and ranking provenance |

No source proves our target MRR or guarantees that extra degrees of freedom
help. The [successor plan](#search-first) defines what will be
tested. A measured failed method remains a research result and is retained.

## Current authority — 2026-09-12

[Search-first successor](RQ3_experiments.md#search-first) supersedes the older
action menu, immediate execution schedule and total call cap below for future
work. First explore small isolated training subsets, then SFT+RL; freeze before
final eval. Every attempt and effect is persisted. Historical results and
checkpoints keep their original contracts and status.

## SFT failure diagnosis and forward readability repair — 2026-09-11

The current user goal requests diagnosis and stable, non-overlapping Composer
execution, then completion of RQ3 after the real prerequisites pass. Preserve
completed SFT, all 140 original validation outcomes, and retained preparation.
Do not claim BASE→SFT gains without matched BASE observations. Neither the
old phase-limited pause nor an old activation authorizes skipping repair checks.

CPU replay reproduced the 30 validation failures and all 110 successful PNGs
byte-for-byte. Eight metric-label failures originate at an artificial two-line
limit. The RQ3-only forward renderer now permits additional lossless wrapped
lines inside the existing label column when measured glyph bounds fit above
the reserved summary. Existing fitting labels keep their layout. No source
values, selection, prompt, action grammar, sampling or checkpoint is changed.
Reject genuinely overflowing labels; do not truncate or draw into plot space.
Record the original and repaired CPU outcomes separately, not as fresh model
successes. Forward Solver qualification remains required before execution.

Log payload capacity and joint packing constraints remain under diagnosis;
do not silently omit selected facts, replace failed proposals or relabel an
invalid program as successful. Current evidence:
`results/sft_failure_diagnosis_v1/`. No additional model calls or training are
implied by the CPU replay. This is not yet a completed readiness gate.

The next forward renderer revision checks actual text/rotated-label ink on
the final drawing surface against card bounds and other labels. Offscreen
glyph masks are not treated as overlapping labels at the origin. A genuine
text-overlap/overflow error is an implementation-integrity error, never an
invalid-Composer reward. Text annotating a plot is allowed; this check does not
certify perceptual readability, semantic correctness or post-processor detail.
Pure renderer regression tests live beside that RQ-local implementation;
no experiment orchestration or training code is moved into the renderer.

## Current execution: user-authorized resumption — 2026-09-11

The new user goal explicitly supersedes the pause below and authorizes the
complete registered RQ3 run. Resume unchanged SFT from its newest verified
state (78 at the restart audit). Keep rolling retention. The first restarted
GPU phase is SFT only; no stale activation authorizes a repaired-renderer
Solver call. After SFT, complete the registered renderer-only 2/2/1 follow-ups,
review them, then issue a successor activation and recover the full lifecycle.
Do not repeat valid training updates or regenerate retained preparations.
Stable monitoring is every 1,200 seconds, with one new-case audit every 3,600
seconds; remain idle during sleeps. Historical statuses below are chronological
records, not reasons to stop an authorized, qualified successor.

## Current execution: user-paused — 2026-09-10 16:00 UTC

The explicit user pause supersedes the continue-SFT instruction below. Trainer
and controller have exited; step 78 (cursor 2,340) was rehashed after shutdown.
No partial checkpoint remains. Completed training progress and preparations are
retained; intermediate checkpoints follow the rolling policy below. Wait for
user resume authorization; then restore the latest complete checkpoint,
not BASE, and retain the pending renderer-only live qualification boundary.
See `results/formal_balanced_v1/PAUSED_BY_USER.md` for the safe recovery path.

## Checkpoint storage amendment — 2026-09-10 (DD-151)

Every completed optimizer update still publishes a full checkpoint atomically,
including adapter, optimizer, RNG, cursor and scientific-contract identity.
Only after the new checkpoint is durable and verified may the previous latest
non-periodic checkpoint be deleted. Retain updates 20, 40, 60, 80, 100, ... and
the latest update; this applies to SFT, imitation and each RL branch. The paused
run's actual latest update is 78, so its retained SFT states are 20/40/60/78,
not 77. Resume starts update 79 without repeating committed updates.

RL counts completed optimizer updates, not zero-based batch directory indices:
update 20 is `batch-019`. Cleanup runs only after durable phase commit. Small
immutable checkpoint markers remain for earlier phase references. Keep one
validation-best adapter-only artifact per branch for final evaluation; use hard
links while the original adapter exists, and never retain its old optimizer
solely for evaluation. That artifact cannot resume training. The four validation
fractions, checkpoint-selection objective, training data, model recipes and
call budgets do not change. A failed/interrupted new save leaves the preceding
latest checkpoint intact; interrupted pruning resumes from its deletion receipt.

Shared persistence lives in `src/vlmrca/training.py`; RQ3 owns the retention
integration and validation-best choice. Static/CPU evidence and the exact
cleanup inventory live under `results/checkpoint_retention_v1/`. No training,
model inference or live smoke is launched for this storage amendment.

## Hour-2 forward rendering repair — 2026-09-10

Actual format-SFT target inspection found that the inherited composite renderer
reused formatted MET-Z strings for numerical normalization. On a source-public
validation of train case INC-3A2D1FE3A4AA, mean 47.4653 displayed as 47 produces
an artificial approximately 131–134-sigma plot instead of -1.5 to +1.3 sigma.
Suffix-formatted values take a different median/MAD path. This is arithmetic
misuse of display fields, not an objection to rounded human-readable labels.

The exact owned phase supervisor is paused before any formal Solver call;
format SFT continues with unchanged messages, DSL targets and optimizer recipe.
Preserve its valid updates and existing corpus/pools/catalogues. A forward repair
must use source-numeric geometry under the same public analysis window, keep
display strings separate, verify training targets remain executable, and pass
targeted CPU/visual/bounded live qualification before formal dispatch resumes.
Do not infer exact source statistics from rounded strings or silently replace
the baseline. Preserve original smoke artifacts and consumed calls. The earlier
activation attests only its original source; refresh activation explicitly after
the repair and checks, without reclassifying old records or restarting SFT.
Detailed evidence: `results/formal_balanced_v1/audits/hour_2/review.md`.

The source-numeric repair passed 94 CPU tests and re-execution of all 4,800
unchanged format targets on 300 train cases; 440 retained train/validation
pool/catalogue pairs also match. Source-numeric geometry is computed from the
same public window and carried separately from formatted evidence labels.
The exact preparation compatibility proof is limited to those unchanged inputs;
it is not a forward inference qualification. Keep SFT running to its complete
checkpoint, then qualify the repaired visual path before Solver dispatch.

Each original logical smoke receives only its necessary renderer follow-up:
two existing AIOPS validation harness canvases for learning and generalization,
one for attribution. At most 2/2/1 new Solver calls respectively, maintaining
cumulative caps of 15/13/18. The 600-second supervisor, model recipe, original
call counts and all prior optimizer/probability evidence remain intact. This
does not retrain the qualification adapter, spend new Composer calls, or claim
the old PNGs used corrected arithmetic. The qualified successor controller must
recover completed SFT without repeating optimizer updates.

## Formal activation — 2026-09-10

The independent `results/formal_balanced_v1/` runtime is now qualified to execute
the full registered lifecycle. Its `activation.json` binds code, model recipes,
the three reviewed smokes, actual optimizer/probability qualifications, prepared
indexes, renderer repair and final 87-test CPU log. All 300 train cases have
16 committed format examples each (4,800 total; 2,400 per dataset); all 140
validation catalogues are complete. The run-local runtime YAML enables execution,
resolves the live-qualified FlashAttention2 kernel and references these exact
preparations. The tracked default YAML stays disabled; it cannot independently
launch a new unqualified run. Scientific model/request/optimizer settings remain
unchanged. The launcher rechecks activation hashes before initial start/resume.

Generation budget is 38,000 planned and 40,000 aggregate, including the existing
41 completed qualification calls. A complete activation is not completed SFT,
RL, evaluation or demonstrated efficacy. The 480 eval inputs remain closed until
validation freezes all registered policies; final findings require manual audit.

CPU fixed-design sampling also exposed an important method limitation: high-score
complete log cards can exceed their assigned silhouette. Four of six inspected
validation cases were infeasible for all twelve fixed designs; two were executable
under all twelve. Preserve those failures and full denominators, do not replace
their selections with easier examples. The registered T/C/TPV controls remain
the strong parent-derived baselines. This is render feasibility, not Solver MRR.

## Current delivery update — 2026-09-10

The full lifecycle now has CPU-tested handlers for all registered learning,
validation-freezing, evaluation, attribution and analysis phases. Earlier
"unfinished handlers" entries below describe earlier implementation states.
This is not evidence that formal training/evaluation has executed: activation
still requires complete format targets and final readiness verification.

Three repair smokes passed and their complete conversations were reviewed;
cumulative initiated calls are 13/11/17. The disposable optimizer and actual
sampled-token probability replay passed. New full pools and bounded catalogues
are complete for 300 train and 140 validation cases. Format targets are being
generated from those retained catalogues, not from reprocessed raw data.

Final entry review also corrected D_FIXED selection in validation, evaluation
and attribution to consume only admitted catalogue cards, as DD-148 requires.
The immutable full pool still supplies each card's complete facts. The strong
T/C/TPV parent controls deliberately keep their separately registered P0 rule.
This corrects an unexecuted formal handler, not an experimental arm change;
prior preparation and the explicitly named sparse smoke controls are unchanged.

A production format-target case exposed heterogeneous renderer sort keys:
topology used a string where a tied ordinary card used an integer. RQ3's local
key now uses the same typed tuple. Previously defined comparison results are
unchanged; two retained actual Solver PNGs and canonical manifests reproduced
identically. The exact before/after cache compatibility proof is stored under
`results/renderer_sort_repair_v1/`; it authorizes only this pair of identities,
not arbitrary cache reuse. Original pools/catalogues and earlier results are
not rewritten. Worker exceptions are now surfaced before waiting for other
format lanes, which checkpoint their current case before stopping.

Reanonymization preserves source-matched facts, card membership, shortlisted
card IDs and diagnostic values; only entity identity fields change. Complete
CPU replay on two validation cases verified 16,069 and 15,447 facts. Numeric
ID replacement cannot alter substrings inside diagnostic decimal values.
Generated learning/evaluation reports remain drafts until final manual review;
an execution journal alone does not declare the entire RQ complete.

## Formal preparation and update delivery — 2026-09-10

Reuse the immutable clock-safe full pools independently of the bounded Composer
catalogue. Pool identity binds the exact compiler/analyzer/loader implementation,
not unrelated training-dispatch edits. Prepare all 300 train and 140 validation
cases on four distinct physical cores, preserving each completed public/private
pair across interruption. No raw conversion or eval preparation is authorized
by this CPU step. Existing four qualified pools can be reused with their content
and identity verified; directories are generated afterwards from these pools.

Strong T_FIXED/C_FIXED/TPV_FIXED controls now use the RQ1.1 parent selection and
rendering primitives with the same RQ3 public clock projection and RCA task shell.
They do not use sparse smoke-harness packets. TPV supplies G pixels only and M/R/L
text; T and compact typed text have equal facts. Two actual isolated validation
cases passed native text/image token preflight and manual TPV image review.
These are new compatible RQ3 controls, not a claim of byte-identical historical
RQ1.1 model requests or fresh live baseline results.

RLOO updates require four completed, same-policy proposals per registered case,
bound to their actual Composer inputs, sampled IDs/probabilities and Solver
record hashes. Infrastructure failures cannot enter rewards. Only explicitly
recognized packing/readability limits are negative program outcomes; renderer
integrity errors abort preparation. SFT resume uses the latest fully committed
checkpoint; partial writes do not shadow it, but a corrupt committed checkpoint
cannot silently roll back. RL resume also binds the branch and preceding batch,
so equal seeds do not allow RR-only/cost optimizer state interchange.

Full phase handlers remain unfinished; these CPU preparations and training
entry points do not establish full formal execution readiness.

### Learning lifecycle and cache-scope refinement — 2026-09-10

The learning prefix now executes format SFT, complete validation/cost freezing,
twelve fixed-design validations, three checkpoint-bound RL branches, shared
feedback imitation and validation-only policy selection with committed phase
outputs. Its terminal status explicitly says evaluation is still pending;
finishing this prefix never claims the whole RQ3 is complete. Full evaluation,
attribution and reporting handlers must be delivered before the full-run gate.

D_FIXED is selected by two-dataset macro validation MRR, then actual total
tokens on an exact score tie, then design ID. Retain all failed-program and
context-infeasible cases with zero quality; do not use partial populations.
A design that was executable on no validation case cannot be the fixed
dashboard baseline. If none executes, fail rather than invent a baseline.

The catalogue cache now hashes its exact scientific compiler functions,
observation/schema/instructions, card/renderer dependencies, tokenization and
budget, instead of the entire mutable training/controller modules. Changing
model-visible semantics still invalidates that cache; completing an unrelated
training handler no longer forces directory regeneration. This changes only
cache identity, not pool, shortlist, card order, preview or complete prompt.
Older catalogue/qualification artifacts retain their original status and bytes.

For function identities, use the loaded callable's bytecode, constants and
argument semantics rather than looking up source lines after a file edit.
Filename/line-number movement is not a scientific change; changed operations,
constants or the explicitly listed global dependencies are. This repairs the
v1 directory job's source-position fingerprint failure without changing the
input compiler or reprocessing immutable full pools. V1 files remain preserved;
the operational successor uses `full_catalogues_balanced_v2`.

Formal GPU children inherit a process-lifetime file lease. If their supervisor
dies, a successor cannot load another model while an orphaned child still owns
the GPU workflow. Following owner shutdown, a fully persisted reply can be
reconciled without generation; otherwise interrupted requests retain spent
calls and may retry the identical input. Non-interruption infrastructure errors
still require diagnosis. Resume specifications preserve the original input and
original specification, adding only explicit retry authorization metadata.

New RQ3 attention artifacts use lossless JSON+gzip sidecars. Preserve every
recorded vector, geometry and derived diagnostic value; response records and
the call database reference the single raw-probe archive by stored and
uncompressed SHA256 rather than embedding duplicate vectors. PNG overlays stay
ordinary PNGs. Only newly created, uncommitted intermediate JSON is removed
after exact-value round-trip verification; historical files are not converted.
This is a storage representation change, not an attention approximation,
quantization, reduced sampling, new model call or inference-recipe change.
It is qualified by CPU replay of actual retained Solver artifacts.

The formal model worker now binds each task to its registered phase/partition,
committed public/private preparation, actual image bytes and active model/LoRA.
Up to 36 request threads overlap four physical-core-pinned rendering processes;
Matplotlib is never run concurrently in those request threads. A failed program
produces a zero-call Solver outcome, not a replacement canvas. A legitimate
context-infeasible canvas is retained with zero end-to-end quality and the
registered negative program reward; an integrity failure is never treated as
such a sample. No-call entries do not spend model calls, while interrupted
initiated requests remain spent. Training sample seeds are hash-derived from
the branch seed, stage, dataset/case, traversal and sample; matching COST/RR
branches share seed policy. Solver sampling remains the frozen seed 42.
This changes neither the task graph nor the inference distributions.

The shared-feedback IMITATION branch initializes from the same completed format
SFT policy as RL, with a fresh optimizer and the existing teacher-forcing
two-epoch/1e-4 recipe. Its targets are only the previously collected legal
RL_COST_42 training winners; it adds no Solver calls or new training population.
Its stage and initializer weight hashes are checkpoint-bound separately from
format SFT and RLOO, and it never updates the frozen SFT reference.

## Formal lifecycle and recovery implementation — 2026-09-10

The complete 38,000-call registration now has a deterministic 342-phase local
execution dependency graph: preparation, format SFT, pre-RL SFT validation and
fixed cost denominators, twelve fixed-design validations, the three RL branches
with 96 total update batches and four validations each, shared-feedback
imitation, validation-only policy freezing, then all 480-case evaluation and
attribution tasks and final analysis. This is not permission to omit a phase
or evidence that its execution handler already exists.

An exclusive local supervisor file lock is held across each owned run.
Completed phases require their committed file inventory and prerequisite
phases; a reboot releases the OS lock but does not reset completed work.
After workers stop, recovery may commit an already fully persisted and verified
response without a new model request. Otherwise the interrupted request stays
spent, and only an explicitly reconciled identical input may retry. Retry
conversations/responses/attention use a new attempt suffix, preserving earlier
files; no partial responses are concatenated. Wrong model answers and invalid
Composer programs remain completed outcomes, not retry candidates.

These operational changes add no scientific conditions or calls and change
no Composer/Solver sampling, model-visible prompts or evidence. Full phase
handlers, strong fixed baselines and complete training/evaluation delivery
checks remain required before `execution_enabled` can become true.

## Attribution qualification reuse — 2026-09-10

The remaining attribution repair may explicitly reuse the already persisted
legal BASE program from learning-repair-v3 on the identical isolated validation
observation. Verify its complete response/input/artifact hashes and program
binding before use. Record `intervention_reference.json`; do not attribute this
success to a new invalid proposal or a trained policy. Two fresh Composer calls,
two named harness controls and five selection/design/twin Solver interventions
still fit the remaining nine calls (18 cumulative for this logical smoke).
Reuse adds no generation and does not change formal single-sample evaluation.
This makes intervention-path qualification independent of a fresh BASE
program's stochastic legality; failures of the fresh proposals remain recorded.

## Execution and May-source implementation amendment — 2026-09-10

### LoRA serving/probability qualification refinement

Learning repair v3 completed the clock-safe train-only disposable optimizer
update and seven inference calls (thirteen cumulative learning-smoke calls).
Its manual review passed. The remaining generalization repair uses that
non-promotable adapter as an explicit `QUAL_LORA` control, not a claimed BASE
or trained SFT result. Two validation Composer calls, their drawable canvases,
and the existing T/compact/canvas harness controls remain within ten new calls
and the original eighteen-call cumulative scope.

Inside that same 600-second supervisor, after the 9B serving phase is stopped,
replay its two exact sampled-ID sequences through the training implementation
with the identical adapter. This adds zero generation calls and zero optimizer
updates. Include EOS; verify stored record/adapter hashes and the real policy
version; report mean/max token logprob discrepancy and sequence discrepancy.
The existing mean absolute logprob tolerance is 0.05. Failure pauses the next
phase for repair, not a reward or low-quality model example. The fixed 27B and
same-call attention path are unchanged. Timeout-only does not qualify an
unexecuted probability check for formal RLOO. All candidate-directory bytes are
unchanged by this execution-only extension; a catalogue reindex only refreshes
its broad code hash, not the retained clock-safe evidence pools.

### Qualification input repair: clock-valued metrics

Detailed learning-smoke review discovered epoch-valued last-seen, process-start
and last-GC metric gauges in the Composer catalogue. Relative observation
timestamps alone do not remove these values. RQ3 now projects these specifically
named clock gauges into seconds using one origin derived exclusively from their
public values: earliest positive clock minus one second. Zero/unset and NaN are
preserved; positive inter-entity/family time differences remain unchanged.
The origin is never model-visible. Explicit ns/us/ms units are converted to
seconds; ambiguous or invalid clock ranges fail rather than guessing. Duration,
latency and cumulative time counters are not clock gauges and remain untouched.
Derived metric statistics use this safe frame, uniformly across all strategies.
Names end in `_relative_s`, with identical brief semantics in Composer and
Solver inputs. Source corpus, split, raw conversion and 27B recipe do not change.

The new compiler version is `rq3_full_pool_v3_relative_metric_clocks`.
Older qualification pools cannot be reindexed into it; rebuild the four smoke
pools from retained V3 cases, preserving prior artifacts. Learning repair v2's
automated transport/optimizer pass remains historical; its manual input review
requires this forward repair before formal qualification. Six calls remain
spent, so its next attempt has at most ten new calls within the same 18-call
logical scope. The source-data repair is unrelated to model answer accuracy.
Metadata-only card previews now retain their boolean/count payload rather than
only a field name (`traces_missing:false` was previously ambiguous, not true).

The current user goal authorizes CPU repair/verification, bounded repair
qualification, then all registered SFT/RL/evaluation work. It supersedes earlier
stop-after-smoke clauses, not isolation, model recipes, outcome handling or the
40,000-call limit. Execution stays disabled until the actual prerequisites pass.
Preserve original smoke artifacts/counters; each experiment's total smoke
attempts remain within 18 calls. A newly authorized repair window is separately
recorded, bounded by 600 seconds, and never relabels an earlier failed window.
Monitor smoke every 600 seconds, stable formal every 1,200 seconds, and audit
one new completed case every 3,600 seconds. Stay silent and idle during sleeps.

`AIOPS2022MayDataset` in the sole unified raw processor adds the May release's
JSON index and date-aware source identity. It inherits the byte-preserved
native telemetry transformations; it is not a sibling-repository dependency.
Process all 241 May events before selecting the exact balanced split. Existing
March/public/private bytes, the eval480 roster and prior experiment results
are preserved. The combined manifest appends new identities only after the
whole release completes, with its original prefix preserved byte-for-byte.

For throughput, each native CSV is parsed once into a lossless, checksum-bound
Parquet cache; subsequent calls read the same inclusive native time window.
Native column types, values, normalizations and graph code remain unchanged.
Compare the first two May cases through full native CSV and cached-window
loading at complete canonical DataCase-byte level, and verify every new public
case's disk round-trip. Resume verifies completed public/private pairs, repairs
only matching staged publications, and never silently consumes corrupt cache
as missing telemetry. Full raw/source paths and label metadata remain private.

Local WSL currently exposes 45 GiB RAM rather than the machine's nominal 96 GiB.
Use two independent physical-core workers for this multi-GB full-CSV parsing
stage, bounding peak memory without shortening windows or reducing information.
The per-case completion protocol and append manifest are durable across restart.
Historical corpus summaries remain historical; the versioned
`private/aiops2022/may_extension_summary.json` attests this extension.

Training-mode repair: zero-dropout policy updates use `train()` so the inherited
gradient-checkpointed layers actually checkpoint activations; frozen-reference
scoring uses `eval()` and no gradients. Reject non-finite log probabilities or
gradient norms before optimizer publication. Seed initialization and optimizer,
RNG, data/split/recipe-bound checkpoint recovery are explicit. These are execution
correctness repairs, not changes to RLOO's sequence-level objective or the
frozen Solver. The implementation follows the registered
[TRL 0.29.1 objective](https://huggingface.co/docs/trl/v0.29.1/rloo_trainer).

Repair-smoke accounting separates an immutable attempt prefix from the shared
experiment-wide call counter. The attribution repair's maximum is nine new
calls: two Composer calls, two fixed harness canvases, and U10/U01/U11 plus
Text/Screenshot on the first case when drawable. Its original nine spent calls
remain counted; there is no 18-call reset. Learning/generalization repair plans
retain their ten-call worst-case limits. Only the current attempt's artifacts
are verified under its root; historical failures keep their original status.

**Current authority:** the [balanced-data amendment](#balanced-data-amendment--2026-09-10-dd-150)
sets current targets/budget. The 2026-09-09 refinement governs unchanged methods
and historical qualification status. Earlier split counts remain historical
evidence, not a claim that the enlarged split has been materialized.

### Materialization and optimizer qualification update

All 241 May events now passed public round-trip verification; the two registered
full-native-CSV comparisons passed. The original 300-row manifest prefix is
byte-identical, and the combined AIOPS-2022 corpus has 541 cases. Registration
`results/registration_balanced_v3/` supplies the exact 150/70-per-dataset split,
connected-event isolation/source checks and 38,000-call schedule. Its split hash
is `cd127a15494fdefb03e988c74857a5d7d4fc11184011a6d4ea4c8021949b9ef1`.
There are 62 unused AIOPS-2022 and 80 unused AIOPS-2025 cases; isolation is not
relaxed and no eval identity changes. Earlier pending-source language describes
the state before this completion, not an outstanding need to reconvert data.

The learning repair smoke additionally qualifies one disposable LoRA optimizer
update using one current **train** case per AIOPS dataset. It uses full registered
input lengths, BF16, zero dropout, gradient checkpointing and the proposed
FlashAttention kernel, exercises backward/optimizer/checkpoint/RNG restoration,
and records memory/time/finite checks. It stays inside the same 600-second
learning-smoke supervisor and adds zero generation calls. Validation examples
are never optimizer input; these smoke weights are explicitly non-promotable.
The following inference phases still use BASE and the unchanged frozen Solver.
Timeout-only qualification does not establish an unexecuted optimizer path;
formal training also requires an actual completed optimizer verification.

## Balanced-data amendment — 2026-09-10 (DD-150)

**Adopted configuration; new data processing/qualification pending.**

| Dataset | Train target | Validation target |
|---|---:|---:|
| AIOPS-2022 | 150 | 70 |
| AIOPS-2025 | 150 | 70 |
| Total | **300** | **140** |

Both datasets have equal counts within each partition; train and validation
are not required to have the same size as each other. All 480 eval identities,
TrainTicket holdout and connected-event/window isolation remain unchanged.
Seed-42 grouped selection stays label-blind. Exact quotas are required before
new execution; diagnostic inventory is not a qualified executable split.

Current AIOPS-2022 processed data provide only 41 strict-isolated March cases.
The local May release adds at most 241 labeled events; their metadata allow
150/70 allocation without splitting connected groups. They still require V3
conversion and telemetry/source validation. Its original competition
`test_data` release is a new RQ3 training source, not a new project eval set;
do not claim unseen generalization on that original competition test release.
No duplicate records, reduced windows, unlabelled normal periods or eval cases
may be used merely to meet quotas. Existing corpus and old split artifacts are
preserved, not overwritten or relabeled.

| Planned work | Maximum generation calls |
|---|---:|
| Three RL branches × 300 train × 3 traversals × 4 samples × 2 roles | 21,600 |
| Twelve fixed designs × 140 validation | 1,680 |
| Three branches × four checkpoints × 140 validation × two roles | 3,360 |
| SFT/IMITATION × 140 validation × two roles | 560 |
| Unchanged ten-arm, 480-case final comparison | 7,680 |
| Unchanged attribution and local interventions | 3,120 |
| Planned | **38,000** |
| All past/future smoke, retry and repair reserve | **2,000** |
| Aggregate hard cap | **40,000** |

This replaces the unequal historical 251/90, 32,472-call plan. The intervening
210/70-per-dataset proposal required 46,640 calls and was superseded before
processing/training. We retain 70 validation per dataset by reducing only train
targets; the three RL traversals, branches, four checkpoint evaluations and
all final comparisons remain intact. At most 4,800 format-SFT examples result;
SFT forward/backward computation is recorded but is not a generation call.
The reserve includes previously initiated calls and is not a fresh/reset
allowance. No model recipe, prompt, renderer, scorer or RQ480 change is made.
`budget.status: ready` only means the count fits. `execution_enabled: false`
and the pending source/qualification prerequisites still prohibit a full run.
This configuration amendment does not launch processing or model calls.

Version: v2-budgeted-catalogue-development, 2026-09-07. **Not live-qualified.**
The approved protocol below is distinct from implementation completion.
`configs/rq3.yaml` keeps `execution_enabled: false`; passing a smoke will not
enable training or full evaluation. See the devlog for current blockers.

## 1. Pipeline and ownership

Canonical V3 public per-case telemetry → complete CPU-side eligible evidence pool →
budgeted anonymous candidate directory → Qwen3.5-9B Composer → `ComposerProgramV1` →
deterministic renderer → one PNG → frozen Qwen3.8-27B → top-five RCA scorer.

Only the Composer language backbone receives BF16 LoRA updates. Vision
encoder, embeddings, output head and Solver are frozen. No Gemma, standalone
QA, scorer training, attention reward, or multi-stage Solver is part of RQ3.
Global processor, segmentation, client and scorer remain authoritative.
The renderer was copied byte-for-byte from RQ2 before local namespace and
correctness changes; `configs/parent_provenance.json` records every comparison.
RQ1.1/RQ2 source and numerical artifacts remain unchanged.

## 2. Dataset partitioning

Reuse `build/local_processed_v3/`; do not regenerate the corpus. Final eval
is `RQs/RQ1_1/configs/rosters/case_manifest_480_frozen_v1.json`: AegisLab 100,
AIOPS-2022 100, AIOPS-2025 100, RE2-OB 90, RE2-TT 90.

Exclude all eval IDs, their event aliases and overlapping source windows from
training and validation. Exclude *all* AegisLab and RE2-TT, not only their eval
members. No RE2 case is used for training smoke. Only AIOPS-2022/2025 may enter
SFT generation, rollout/reward, validation, fixed-design choice or checkpoint
selection. TrainTicket evaluation is AegisLab (primary) and RE2-TT
(supplementary); these are not two different unseen applications.

After exclusions, connect overlapping or same-event remaining cases into
indivisible groups. Joint bounded subset-sum allocation approaches the target
without exceeding it; seed-42 hashes settle ties. Do not split groups or relax
isolation to fill a quota. The implemented metadata audit reaches:

| Dataset | Train | Validation | Unused | Eval/overlap excluded |
|---|---:|---:|---:|---:|
| AIOPS-2022 | 70 | 20 | 5 | 205 |
| AIOPS-2025 | 230 | 70 | 0 | 100 |

Window/source identities and labels live only in `private/`. Public catalogues
and rewards never receive absolute time, fault type, natural entity names,
dataset identity or source paths. Source membership checks and downstream
TrainTicket absence are necessary even though the models may have encountered
these applications during unknown foundation pretraining.

## 3. Pool, catalogue and actions

The pool is computed from the complete canonical public case, not the old
dashboard's top-12/top-24 series. MET-Z scores all eligible metrics, TRC-L
extracts all operations eligible under the inherited positive-change rule,
LOG-R and Denum supply readable event evidence, and G retains concrete edges.
Record eligibility/coverage explicitly: an analyzer-derived pool is not a
lossless copy of every raw record. Logs retain diagnostic numeric sequences,
not merely a first/last/top-two preview.

Each card owns an exact set of facts and one silhouette. Log cards now group
adjacent relative bins within the same entity, template and severity, rather
than mixing unrelated hash-neighbor event groups. No source facts or numeric
series are removed by this regrouping. The Composer sees card IDs, entity IDs,
type, coverage, anomaly summaries, missingness, legal encodings and footprints.

### Budgeted directory — user-authorized amendment, DD-148

**Superseded v1:** advertising every card in a single call. Its two AIOPS
validation directories measured 984,884 and 832,635 tokens even after dictionary
compression. This was an unsuitable directory architecture, not an intrinsic
million-token requirement of RCA. No model call used those directories.

**Current v2:** keep the complete eligible pool outside model context and use
one deterministic budgeted candidate directory. There is no additional LLM
retrieval stage, extra call, context extension or reduced output ceiling.

| Limit | Value and meaning |
|---|---|
| Whole input target | 16,384 tokens, including system instructions, schema, candidates, cards and chat template |
| Model context | Existing 40,960 tokens, unchanged |
| Completion reservation | Existing 4,096 tokens, unchanged |
| Additional guard | 1,024 tokens |
| Effective input budget | `min(16384, max_model_len - max_tokens - 1024)` |
| Directory cap | At most 192 complete card-summary rows |
| Per-card preview | First 80 tokenizer tokens, explicitly marked when shortened; full payload remains in the pool |
| Final selected cards | Existing 1–12; every selected card is rendered with its complete facts |

Selection order is round-robin M/R/L/G, then round-robin anonymous entity
groups within each region. Public salience ranks cards *within* an entity
group; every fourth item uses a frozen seed-42 hash order for exploration.
No cross-modality anomaly-score comparison, label, private clock, Solver
result or Composer policy participates. Unused regional capacity naturally
flows to remaining regions. A complete balanced prefix is admitted subject
to the actual whole-chat token count; at least one card per available region
is required. If the mandatory task/candidates plus that minimum cannot fit,
fail before contacting a server. Never truncate serialized JSON or remove
candidates to manufacture passage.

The directory is a **bounded candidate shortlist**, not a lossless catalogue
of every card and not a second copy of all telemetry. Previews use normal
field names rather than dictionary-index pairs. They are discovery summaries:
name/value abbreviation there does not alter the selected card's Canvas,
TextTwin or ScreenshotTwin. Only IDs actually advertised in the directory
are accepted by the Composer binding interface. The original full payload is
retrieved deterministically after selection.

Persist pool/card/observation hashes, original fact bindings, total/admitted/
omitted card IDs, per-region coverage, fact coverage, token count, output
reservation, safety guard and the omission policy. Complete private source
labels stay physically isolated. Every learned strategy, format-SFT example
and policy rollout uses this same directory policy; D_FIXED also selects from
the same admitted candidates. The first analysis link is now explicitly
`pool → admitted catalogue → learned selection`; a root signal filtered out
before the Composer is a retrieval limitation, not evidence that the Composer
ignored a signal it saw. Do not claim a performance gain from lower input size
alone. Candidate-retrieval recall and end-to-end RCA still require evaluation.

CPU qualification on the same two retained public pools measured **16,346**
and **16,292** whole-input tokens, admitting 96/7,676 and 111/6,595 candidate
cards after coherent regrouping. Pool bytes are unchanged. These are input
capacity diagnostics, not model performance or a live-smoke result.

`ComposerProgramV1` has only `schema_version`, `selection`, and `design`.
Selection is a set of unique short card IDs; design is portable across card
sets. No executable code, invented data or free-form root-cause label is a
legal drawing instruction.

| Action | Registered choices |
|---|---|
| Metrics | heatmap; small-multiple lines; compatible overlay lines |
| Traces | dumbbell; baseline/current bars |
| Logs | template-frequency timeline; template-time matrix |
| Topology | node-link; adjacency matrix; edge ledger |
| Layout | modality-grouped; entity-grouped; salience-first; topology-centered |
| Ordering | stable ID; public salience/onset; topology traversal |
| Footprint | compact; balanced; detailed legal silhouettes |
| Grid | 12×8; 12×12; 18×12 |
| Raster scale | 0.75–1.50, step 0.05 |

The first harness exposes 1–12 cards per program. This displayed-content
budget is separate from the explicit candidate-directory budget above. Fonts,
colors, semantics, bins, precision and units are fixed. Resolution changes
actual PNG dimensions without changing Qwen's processor recipe.

Programs must execute their declared selection, encoding, ordering, packing
and resolution. No-op actions are audited as such. Invalid or unrenderable
programs remain end-to-end failures; no hidden default replaces them. All
selected facts must survive in Canvas/TextTwin/ScreenshotTwin. A screenshot
may not drop a page to satisfy the single-image rule. Long unbroken text must
wrap inside its card, not extend into other cards. Counterfactual designs may
fail to fit; report that coverage without secretly removing evidence.

## 4. SFT and RLOO

SFT uses at most 16 CPU-generated legal examples per training case (4,800
maximum), independent of root labels or Solver scores. Two epochs, AdamW
learning rate 1e-4, LoRA rank 16/alpha 32/dropout 0, gradient clipping 1,
gradient checkpointing, BF16 and FlashAttention where supported. Language
linear projections include GDN layers; do not tune the vision model, embedding
or output head. Report JSON, binding, execution and rendering success; this
does not establish RCA improvement.

RLOO treats the entire program as one action. Four independently sampled
programs per case, three traversals, at most 30 case groups/update, one
optimization pass, learning rate 1e-6, fixed SFT reference, KL coefficient
0.01. Keep duplicate samples. The same-case leave-one-out advantage is
`A_i = r_i - mean(other three rewards)`. Follow TRL 0.29.1's sequence-level
RLOO objective; no critic or GiGPO-style intermediate-state claim.

The new Composer sampling recipe uses temperature 1, top-p 1, no top-k/min-p
or grammar mask, and thinking off. This gives a full-support categorical
distribution whose sampled token IDs/log probabilities can be checked against
training. It is **not** a change to the Solver's top-p 0.95 recipe. Exact
sampling IDs, including stopping tokens, must be retained; retokenizing
displayed completion text is not an acceptable substitute.

The main branches are `RL_COST_42`, `RL_COST_43` and equal-budget
`RL_RR_42`, sharing the same format-SFT start. Loss and validation are
dataset-macro weighted over AIOPS-2022/2025. Save policy version, model,
optimizer, RNG, completed calls and rewards before switching batches. A
completed request is reused; unresolved requests require reconciliation.
Old rollouts must not be relabelled as on-policy.

Quality reward is per-case reciprocal rank RR. The cost variant is:

```text
c = (Ic/Ic_ref + Oc/Oc_ref + Is/Is_ref + Os/Os_ref) / 4
r = RR - 0.02 * clip(c, 0, 2)
```

C denotes Composer, S Solver; input includes image tokens. Reference means
come from the pre-RL SFT pipeline on validation and never move afterward.
Input and output each receive half the aggregate weight. The maximum cost
penalty is 0.04; this is a dimensionless preference, not dollars or FLOPs,
and does not prove average accuracy cannot fall. RR-only omits this penalty.
Invalid programs receive negative reward; Solver format failures are quality
failures. Infrastructure failures cannot become low-quality training rewards.

Single GPU phases are batched: 9B rollout → CPU render → 27B scoring → 9B
update. Do not load/unload models per case or change Solver settings to force
co-residency. Throughput is not yet measured; no week-long runtime promise.

## 5. Three experiments

### exp_composer_learning

Compare BASE, SFT, IMITATION, RL_COST_42, RL_COST_43 and RL_RR_42.
BASE has tool instructions only. SFT teaches format only. IMITATION trains on
the best legal candidates already collected by RL_COST_42, without new Solver
calls. This is shared-feedback winner distillation, not an independent online
RAFT experiment. Validate RL at 25%, 50%, 75%, 100% budget and choose each
checkpoint by its preregistered validation objective. Compare learning curves,
legality, actual action diversity, MRR, costs and train–validation gap.

### exp_frozen_solver_generalization

Evaluate all 480 cases once per method. Fixed controls are T_FIXED (natural
language), C_FIXED (equal-fact compact typed text), TPV_FIXED (strong inherited
topology-visual strategy), D_FIXED (one best fixed design selected among 12
predeclared designs on validation). Add the six learned/base strategies.
Each learned arm gets one Composer proposal and one Solver call, not eval
best-of-four. Every arm uses the frozen common SIRCL-adapted diagnostic
instructions; dashboard-reading instructions are absent from text-only arms.

Report macro results on the three primary datasets, AIOPS new-event
generalization, AegisLab application transfer, and separate RE2 references.
Reuse historical outputs only after complete request/model/schema/scorer
compatibility, not because an old arm has the same name or a good MRR.

### exp_selection_design_attribution

Use D_FIXED and RL_COST_42 to construct U00=fixed content/fixed design,
U10=learned content/fixed design, U01=fixed content/learned design,
U11=learned content/learned design. U00/U11 reuse their matched primary calls.

```text
content_at_fixed = U10 - U00
design_at_fixed = U01 - U00
interaction = U11 - U10 - U01 + U00
total = U11 - U00
```

Also report content at learned design and design at learned content. These
are conditional effects relative to a reference, not intrinsic card scores.
Add learned-selection TextTwin and ScreenshotTwin. On 120 hash-selected
cases (40 per primary dataset), roll back encoding/layout/resolution,
swap another same-dataset case's design, use hash-random legal designs,
reanonymize and repeat identical requests. The 3,120-call envelope allocates
1,920 all-eval replacement/twin calls and 1,200 local calls: seven listed
one-call controls plus a two-role reanonymized Composer pipeline and one
additional identical-input Solver repeat per local case. Select cases before
seeing outcomes, not from improvement winners.

Explain the sequence pool availability → catalogue coverage → selection →
visible/readable rendering → Solver citation → ranking change. Root labels
are used only privately for this audit. Root mention, root evidence and correct
causal reasoning are distinct. This analysis does not recover hidden thoughts
or establish the physical fault-propagation causal graph.

## 6. Endpoints, attention and statistics

Quality: MRR, AC@1/3/5, AVG@3/5, repair/break, rank movement, unknown ID,
parse failure, input/output truncation and infrastructure failure. Cost:
Composer input/output; Solver text/image input/output; whole-pipeline cost,
training cost, deployment amortization and price sensitivity. Model token
units must not be treated as equivalent hardware costs.

Same-call Solver attention retains final-query prefill and structured-answer
generation tokens. Use actual processor geometry, area-normalized image
density/lift, token-normalized text spans, and separate header/blank regions.
Attention is correlational only and never reward or evidence of correct
reasoning. Retain full conversation, partial output, raw response and request
accounting per case/arm; asynchronous writers must drain before completion.

Case is the statistical unit. Average the two main RL seeds per case and also
report each seed; never double n. Pratt-Wilcoxon, paired Cohen's dz, Holm, no
confidence intervals. Main family: RL_COST vs TPV_FIXED, D_FIXED, SFT. Transfer
family: AegisLab vs TPV_FIXED and D_FIXED. Cost-reward/IMITATION/attribution
are separate secondary families. Benefit needs ΔMRR≥0.05 and adjusted p<0.05.
Cheaper with ΔMRR>−0.05 is observed accuracy-preserving compression, not proven
statistical noninferiority. AegisLab's 100-case power limits are explicit; no
post-hoc extra cases to obtain significance. Parse<0.95 or whole-case
infrastructure exclusion>5% makes that model result incomplete.

## 7. Budget and qualification

| Scope | Maximum new generation calls |
|---|---:|
| Three RL branches | 21,600 |
| Fixed-design validation | 1,080 |
| RL checkpoint validation | 2,160 |
| SFT/IMITATION validation | 360 |
| Ten-arm final comparison | 7,680 |
| Attribution and local controls | 3,120 |
| Planned | 36,000 |
| Smoke/retry/repair reserve | 4,000 |
| Hard aggregate cap | 40,000 |

Both roles, retries and failed initiated requests count. SFT/optimization
forwards are not generation calls but still incur recorded compute. Savings
do not authorize additional experiments. Budgets shrink if isolated train
groups cannot supply the target.

Each experiment has one logical smoke, at most 18 calls and 600 seconds
across both roles. Only non-eval AIOPS training/validation cases are eligible;
this supersedes old RE2 smoke selection. Timeout-only follows the current
rule, but a failed context/leakage/equality/persistence preflight is not a
timeout-only pass. The registered budgeted directory is used identically in
smoke and formal calls; do not add smoke-only prompt truncation.
Review all completed conversations and dashboards. During live smoke, inspect
every 600 seconds and do nothing during the wait. Stop after qualification;
do not start SFT, RL or the full 480-case evaluation without a new instruction.

## Method references

- [RLOO, ACL 2024](https://aclanthology.org/2024.acl-long.662/): critic-free
  sequence-level feedback optimization; not proof of RCA superiority.
- [TRL 0.29.1 RLOO documentation](https://huggingface.co/docs/trl/v0.29.1/rloo_trainer):
  the implemented objective and fixed-reference sequence KL convention.
- [DashBot, IEEE VIS 2022](https://virtual.ieeevis.org/year/2022/paper_v-full-1033.html):
  prior RL dashboard design, delimiting the novelty claim.
- [GiGPO, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/420c9f777c0b4f78d515e53cf74d58b2-Abstract-Conference.html):
  intermediate-state credit is not claimed for independent complete programs.
# Current refinement after completed RQ2.1 — 2026-09-09

This section supersedes conflicting historical counts and qualification status
below; it does not rewrite the RQ1.1/RQ2/RQ2.1 records. Delivery remains CPU
checks plus three bounded inference smokes, followed by a stop. No optimizer
run, SFT, RL, checkpoint selection or formal evaluation is enabled now.

## Evidence-led story and testable hypotheses

RQ1.1 showed representation effects rather than a universal advantage for
images: selective topology visualization was a strong Qwen control, and lower
input cost did not imply lower output cost. Completed fixed-anchor RQ2.1 now
provides a cleaner next step: selection, encoding and composition can each
change the fixed Solver, but good choices are conditional, not universal.
Its all-five-dataset macro MRR values are descriptive, not new champions:

| Condition | Qwen3.8 | Gemma |
|---|---:|---:|
| P0 text | .5097 | .5130 |
| P0 canvas / S0 / D0 | .3664 | .3491 |
| Random selection canvas | .1479 | .0920 |
| Coverage selection canvas | .2392 | .1911 |
| Organized-table silhouette | .2880 | .2751 |
| Topology-centered composition | .3420 | .2102 |
| Raster scale 1.50 | .4137 | .3607 |

Important decomposition: LOG_FREQ, DIVERSITY, COVERAGE and RANDOM Vision
conditions have 11.875%, 13.125%, 14.375% and 18.75% geometrically infeasible
cases under the fixed parent canvas. Those outcomes consume no generation
and score zero in registered end-to-end utility. Thus their lower MRR is not
pure evidence-selection damage, and their lower mean tokens are not purely
successful compression. RQ3 must distinguish retrieval/selection, render
feasibility and conditional Solver quality. Even all-drawable T_RANDOM loses
about .20 Qwen pooled MRR, so the observed selection sensitivity is not solely
a drawing-failure artifact.

Sources: RQ2.1 `results/analysis_p0_v2/{dataset_macros,paired_comparisons}.csv`.
In pooled paired Qwen data, scale 1.50 improves MRR by .04594 (Holm p=.01231),
below the registered .05 practical-gain threshold; it costs more input tokens.
Gemma's topology-centered decline is -.13542 (Holm p=4.43e-7). These are
different aggregations from the macro table; do not subtract rounded macro
values to reconstruct pooled tests. Whole-case inference is complete, model
failures remain outcomes, and infeasible designs are not successful compression.

The RQ3 question is whether **case-specific, budgeted evidence selection and
readable encoding can recover diagnostic quality**, not whether RL can exploit
a reported oracle or make dashboards aesthetically attractive. Keep the full
action families (including weak ones) until training/validation, not eval,
determines usefulness. Do not transplant an RQ2.1 post-hoc champion into
D_FIXED. That baseline still comes from the registered 12 designs on RQ3
validation only. There is no new QA reward, attention penalty or learned critic.

Three falsifiable hypotheses organize the existing experiments:

1. Format SFT raises legal execution but utility RL must beat SFT, fixed text,
   fixed TPV and fixed dashboard on the registered held-out evaluation to
   establish downstream value. BASE failure is not hidden by default rendering.
2. Content and design affect outcomes jointly. U00/U10/U01/U11 and same-content
   twins distinguish selecting useful evidence from presenting it effectively;
   report conditional effects, non-drawable swaps and harmful choices too.
3. A learned policy transfers to Composer-training-held-out TrainTicket only
   if AegisLab itself supports the result. RE2-TT remains a separate supporting
   dataset, not a way to inflate the main transfer claim.

For credit assignment, retain one complete DSL as one RLOO action and report
controlled input interventions separately. RLOO's baseline is a variance-
reduction estimator, not a causal explanation of which JSON field mattered.
[RLOO, ACL 2024](https://aclanthology.org/2024.acl-long.662/) studies preference
rewards and leaves reward over-optimization unresolved; it does not establish
RCA efficacy. [TRL 0.29.1](https://huggingface.co/docs/trl/v0.29.1/rloo_trainer)
supports the single-update, sequence-level objective used here. [DashBot,
IEEE VIS 2022](https://virtual.ieeevis.org/year/2022/paper_v-full-1033.html)
already applies RL to dashboard creation: the contribution here must be
verified frozen-Solver diagnostic utility, costs and transfer, not 'first RL
dashboard'.

## Isolation correction and actual budget

Construct connected event/window groups over **all AIOPS windows before**
excluding any eval case. A chain through an excluded neighbour must not hide
indirect eval membership. The old direct-overlap-first split and its CPU
previews are superseded for RQ3 training/qualification only. No model used them.
This stricter audit leaves 41 AIOPS-2022 cases: 21 train and 20 validation;
AIOPS-2025 remains 230 train and 70 validation. Total: **251 train, 90
validation**, at most 4,016 format examples and **32,472 planned calls**.
The 40,000 hard limit includes all Composer/Solver attempts and smokes; savings
do not authorize new arms. All 480 eval cases and all AegisLab/RE2 cases stay
excluded from training and qualification. The corpus is not regenerated.

RQ3-only log bins now use the same public window as metrics, not their own
first/last log timestamp. Model guidance keeps SIRCL diagnosis/VERIFY and the
task-first arrangement, removes obsolete RQ2 top-12/top-24 control claims,
and explains the actual RQ3 numeric-series representation. These changes do
not change the frozen 27B effective inference projection or any prior RQ.

## Bounded qualification, not training success

Each registered experiment has one logical smoke scope, shared by 9B/27B:
18 calls maximum and 600 seconds including startup/switch/cleanup. Work ends
at 570 seconds with 30 seconds reserved for shutdown and persistence. Models
are sequential; two inference requests may batch within the Composer phase.
There is no API billing: the durable call counter prevents accidental retries
and enforces the user's compute budget. It counts local generation attempts.

- Learning smoke: four BASE proposals for one validation case, their valid
  canvases, plus one explicitly named CPU harness-control canvas for each
  AIOPS case. At most 10 calls. The harness controls are never credited to BASE.
- Generalization smoke: BASE proposal for each case, valid learned canvases,
  and T/compact/canvas harness controls for each case. At most 10 calls. These
  controls qualify transport, not the future selected D_FIXED or TPV results.
- Attribution smoke: BASE proposal for each case; fixed U00, drawable
  U10/U01/U11, and learned-content Text/Screenshot twins. At most 14 calls.

Every call preserves the raw response, conversation, request hash, partials
and tokens; Solver calls additionally preserve same-call image/text attention.
Completed outputs need their committed artifact hashes to resume. A timeout
does not attest unexecuted combinations. Illegal BASE programs, wrong RCA and
truncations are model outcomes, not excuses to substitute a better image.
No 9B optimizer step is authorized or claimed by these inference smokes;
training kernels/LoRA updates require separate qualification when training is
authorized. Full training orchestration remains disabled.

---
# Forward display correction — 2026-09-11

During authorized SFT monitoring, the RQ3 heatmap was found to collapse the
entire (-3σ,+3σ) interval to one gray. Use continuous intensity on its existing
scale, not the hidden threshold. The RQ3-only Solver guide also names the
existing trace log1p positional scale. This changes future rendered input, not
the evidence pool, Composer observation, teacher-forced program, optimizer or
completed SFT checkpoint. CPU/static checks passed (108 tests); prior forward
qualification must be supplemented by the already registered bounded renderer
follow-up before formal Solver work. Preserve the current SFT run and all
preparation. DD-152 and `devlog/2026-09-11_rq3_heatmap_review.md` contain evidence.
# Forward matrix-axis correction — 2026-09-11 (DD-153)

After a training-target image audit exposed overlapping adjacency-matrix column
IDs, the RQ3 renderer rotates full column IDs and sizes label margins from real
glyph bounds. Rows remain callers, columns remain callees; nodes, edges, exact
edge ledgers, selected facts and card layouts are unchanged. No Solver prompt,
Composer input or teacher-forced program changes in this correction. Existing
SFT continues, while later Solver execution requires the pending bounded live
renderer follow-up to cover both repaired heatmap and matrix paths. This does
not modify the RQ1.1/RQ2/RQ2.1 snapshots or authorize using stale activation.
# Forward source-bin geometry correction — 2026-09-11 (DD-154)

RQ3 plot coordinates now use the original public 64-bin medians as well as
unrounded baseline statistics. Each original bin must exactly reproduce its
retained CEB/display projection, including unavailable positions, before use.
Do not normalize rounded labels: tiny-value rounding can create false steps.
No candidate, selection, text label, Composer input, target, optimizer or
model recipe changes. SFT remains resumable under the same contract. The
pending bounded renderer-only qualification covers source bins, heatmap and
matrix corrections together; old qualification alone does not activate these
forward changes. Full evidence is in `results/source_bins_repair_v1/`.
# RQ3 capacity-aware harness successor — 2026-09-11

**Status: adopted for implementation; not live-qualified.** This follows the
user's SFT-stability goal. Preserve the original SFT and validation artifacts.
The forward catalogue and packer will share content-aware log footprint and
encoding-specific metric-overlay constraints. Full log text, numbers, entities,
and source facts remain unchanged. Existing feasible footprints are preferred;
only when none can hold a complete log card may the registered extension
`4×4, 6×4, 8×4, 8×6, 12×8, 12×12` be considered. The selected grid never grows
silently, and the final renderer still rejects label overlap and overflow.
Cards with no feasible footprint remain identifiable in the directory with an
empty encoding menu; they are not silently removed from the CPU pool.

This is a changed harness/input contract, shared by BASE, SFT, RL and fixed
dashboard policies, not a claim that the original SFT model improved. Rebuild
only forward catalogues in a new namespace; preserve the complete public pool
and all old catalogues. Current SFT weights remain an explicit warm start, not
evidence of training on the successor constraints. Recheck example feasibility,
token budgets and bounded live behaviour before deciding whether additional
format training is necessary. No grammar/sampling or Solver-recipe change.

Evidence and alternatives: original 140-case validation had 26 renderer-capacity
and four model-schema failures. The height-only CPU repair makes five additional
programs drawable; 14 of the original 17 log-failure cases contain a card that
fits none of its advertised sizes. More SFT cannot solve an impossible menu.
Dropping numeric series, substituting a default canvas, and silently enlarging
the selected grid are rejected. New observations must not reuse old model
responses as if they had seen the new constraints. Qualification and execution
activation remain disabled until the successor is checked.

## DD-RQ3-SEARCH-3: Explicit evidence projection and pixel capacity

**Date:** 2026-09-12. **Status:** provisional search implementation; no efficacy claim.

The four-family search successor keeps candidates in the text prompt and all
diagnostic facts in one image. Use the full public candidate universe in the
initial qualification; no root-informed candidate filtering. Old per-case
clock/coverage prose is not carried into the text prompt. Static RCA and
reading guidance is permitted.

The first new policy summarizes selected log variables before rendering,
retaining multiplicity, template, entity and bin, with exact small frequency
sets or numeric extrema/first/last/distinct counts. Opaque values retain counts.
This intentionally changes the selected evidence projection: it is not a
lossless claim, hidden renderer truncation, or a rewrite of the source graph.

The continuous packer may use actual painter probes to find feasible pixel
envelopes instead of requiring old discrete footprints. Final rendering still
checks every selected fact and primitive. Infeasible attempts remain failures;
this heuristic does not establish a global optimum. Local raw metric axes and
content-adaptive topology area are explicit successor fields; defaults preserve
old painter behavior. Two real parent PNG replays remain byte-identical.

Initial qualification covers four families on two already isolated AIOPS
training cases, eight planned calls within one 18-call/600-second bound. The
temporal variant currently contains only the selected, time-scoped logs and
must not be used to infer a same-content temporal-vs-modality accuracy effect.
Existing SFT, other RQs, results and full processed corpus stay unchanged.
No new attention is collected. Subsequent representative selection/encoding/
layout/prompt searches precede any new full evaluation or training promotion.
# Current tournament execution amendment — 2026-09-13

The tournament IS exploration, with no preliminary inference subsets. For each
model independently, `cohort(round n) = RQ480 - union(AC@1 successes in rounds
1..n-1)`. Run the entire cohort before the next method. Round 1 is preserved;
the user ordered results and coverage of rounds 2–10 deleted and restarted.
The full-remaining reset supersedes older small-cohort text below. Its details
and operative method configs are in [DD-RQ3-TOURNAMENT-13](RQ3_full_remaining_reset_20260913.md).

## DD-RQ3-TOURNAMENT-16: Candidate-bound evidence cards

**Date:** 2026-09-14. **Status:** registered after round 15; pre-call audits passed.

Round 16 addresses the late-tournament binding bottleneck without changing
selection. It retains the resource-family selected packet and groups its
already-selected M/R/L rows into up to eight cards headed by the public
anonymous candidate type and ID. Residual facts remain visible in `OTHER`
regional cards and G retains the complete selected directed topology. Owner
priority is deterministic and label blind: number of represented modalities,
then selected row count, then numeric ID. This is a representation-only
intervention; it is not a root score. Qwen receives all 128 and Gemma all 106
cases still unretired after round 15.

## Selection-only tournament successor v3 — 2026-09-14

After round 25, Qwen retains 97 cases and Gemma 77. A private evaluator audit
confirmed that every remaining case can be hit by its candidate inventory and
that direct root-associated public evidence has appeared in at least one prior
selected packet. Labels were used only for that retrospective classification;
they are not selector inputs. The next mechanisms therefore target signal
timing, source-versus-symptom structure and short-lived shape saliency rather
than simply increasing root evidence inclusion.

The immutable round-16 prompt, candidate binding, renderer, layout, budgets,
request profiles and attention-off setting remain fixed. Three public-only
policies are registered:

1. `incident_window_pattern_v1`: rank metric series by robust level, peak,
   persistence and slope inside the already public estimated incident window.
2. `source_first_bundle_v1`: form anonymous entity bundles from incident-local
   metrics, trace local/exclusive latency, log bursts, public onset and directed
   call neighbourhoods; prefer likely sources over late downstream symptoms.
3. `spectral_saliency_v1`: use learning-free spectral-residual saliency to find
   short or oscillatory incident-window patterns that global mean/variance
   rankings can miss.

Scores and policy names are audit-only. The Solver sees only unchanged source
facts selected into its single PNG; candidates remain text-only and identical.
The three methods run in this order, each on every case still unretired for
each model, Qwen then Gemma. Exact model-visible request identity is the only
basis for reuse. The stable CPU audit covered the current 120-case union with
zero model calls: all three changed the fact set in 120/120 cases; mean Jaccard
against the round-16 anchor was 0.4611, 0.2125 and 0.4385 respectively.

Method motivation is bounded by PatternMatcher (ISSRE 2021), MicroRCA (NOMS
2020), Microsoft's spectral-residual detector (KDD 2019) and MoCE (NSDI 2026).
These policies are adaptations, not reproduced full systems and not evidence
of efficacy until the registered tournament rounds finish.

<a id="selection-successor-v4"></a>

## DD-RQ3-TOURNAMENT-V4 — Eight complementary selection mechanisms

**Date:** 2026-09-14. **Status:** implemented, static review only; execution
disabled pending the user's next instruction. This is a provisional method
catalogue, not eight qualified or completed tournament rounds.

### Purpose and boundary

Round 27 leaves 94 Qwen and 75 Gemma cases unresolved. Earlier methods mostly
rank individual anomaly sizes, time changes, peer deviations, source-neighbour
heuristics or cross-modal agreement. These eight methods instead target
conditional relationships, multivariate residuals, local shapes, distributions,
event conservation, operation composition, multi-hop dependencies and additive
event slices. Complementarity is a hypothesis; no new success count is reported.

Only selection changes. Preserve the round-16 renderer, card grouping, layout,
single PNG, prompt, text-only candidates, public fact projection, scoring and
both models' recipes. No model training or attention. Per-case numeric entity
IDs and the existing field budgets are unchanged. Scores, partners, coefficients,
method names and explanations below are CPU/audit-only, never Solver hints.

All methods consume the complete **existing derived public pool**, not a previous
small selected packet. This pool includes analyzer-eligible facts, not every raw
row: in particular its TRC-L operation cohort is already filtered. This version
does not silently change that boundary or regenerate preparation.

The eight implementations are original project selectors inspired by the cited
papers. They are not claimed to reproduce CIRCA, MonitorRank, Spectroscope or
HotSpot end-to-end. There are no external repository imports or new dependencies.

### Literature search and novelty audit

Checked the current reference guide, RQ3 reading/protocol notes, selection suite
v1–v3 and `exps.py` before choosing sources. None of the eight mechanisms below
has a prior tournament implementation. MonitorRank was mentioned as another
paper's baseline in an old description, but no prior focused reading or
MonitorRank implementation was found. For the other seven papers no prior reading
entry was found. This is an audit of available records, not a claim to know every
previous conversation or foundation-model exposure.

Searches covered conditional root-cause recognition, robust subspaces, time-series
discords, two-sample distribution comparison, log invariants, request-flow
mutations, graph diagnosis and additive KPI localization. Primary paper method,
evaluation and relevant limitation sections were consulted; no exhaustive proof
verification or original-system reproduction was performed. Venue corrections
matter: MonitorRank is SIGMETRICS 2013, CRISP is ATC 2022, and HotSpot is IEEE
Access 2018, not KDD/ATC 2018/WWW respectively.

| New selector / changed fields | Main diagnostic question | Difference from earlier methods |
|---|---|---|
| `conditional_residual_v1` / M | Does a previously predictive relationship stop explaining this metric? | Not simply a large deviation or peer median; validates a conditional baseline relation |
| `lowrank_sparse_v1` / M | What remains after separating coordinated system movement from sparse exceptions? | Joint matrix decomposition, not per-series variance or one peer comparison |
| `subsequence_discord_v1` / M | Does the incident contain a shape unlike its earlier patterns? | Nearest baseline subsequence, not Fourier saliency or a change-point score |
| `kernel_distribution_v1` / M | Did the distribution change even when mean/variance alone is uninformative? | Kernel two-sample discrepancy rather than only first/second moments |
| `log_balance_v1` / L | Did two normally proportional event counts stop matching? | Paired conservation rather than single-template rarity/frequency |
| `operation_mix_v1` / R | Did this service's observed mix of operations change? | Compositional change, not span support/confidence or exclusive-latency rank |
| `graph_diffusion_v1` / M/R/L/G | Which dependencies receive evidence through multiple correlated hops? | Restarted graph walk, not one-hop source/frontier scores |
| `additive_ripple_v1` / L | Which event slice accounts for the observed count change? | Proportional slice repair, not isolated template burst or coverage maximization |

### A. Conditional relationship failure — `conditional_residual_v1`

Source: Mingjie Li et al., *Causal Inference-Based Root Cause Analysis for Online
Service Systems with Intervention Recognition*, KDD 2022, especially §4.2 and
Appendix C.4. CIRCA examines conditional-distribution changes and evaluates
regression-based recognition on simulations and an online-service dataset.
The appendix finds nonlinear regressors useful; the paper does not establish
that a simple local linear relation suffices for every RCA case.
[Paper](https://arxiv.org/pdf/2206.05871),
[published record](https://doi.org/10.1145/3534678.3539041),
[author code](https://github.com/NetManAIOps/CIRCA).

Our method checks each metric against metrics of the same entity and public
call/membership neighbours. It uses the first 70% of pre-window bins to shortlist
up to eight predictors with absolute correlation ≥0.6, fits one-variable affine
regression, and retains the predictor with the best held-out baseline error ratio.
There must be ≥8 fit, ≥3 validation and ≥3 current joint observations; validation
error must be less than half the baseline-median predictor's error. The incident
90th-percentile residual is scaled by held-out residual RMS (floor 0.1 in
baseline-standardized units). Relation fitting uses no current-period answers.

Select a target **and its predictor** as a two-fact bundle within the inherited
M budget. Example: latency increases far more than its usual relationship to
workload predicts. Different metrics with identical baseline shape remain eligible;
excluding them would remove exactly the relationship-break signal being sought.
No structural causal graph or causal-identification guarantee is claimed. Nonlinear
relationships that fail baseline validation do not produce a native ranking.

### B. Shared-wave separation — `lowrank_sparse_v1`

Source: Candès, Li, Ma and Wright, *Robust Principal Component Analysis?*, JACM
2011, notably the decomposition objective, empirical examples and §5 algorithms.
It separates a low-rank matrix and sparse corruption under specific assumptions;
its image/video examples do not establish that every service incident is sparse.
[Paper](https://www.cs.cornell.edu/courses/cs6241/2020sp/readings/Candes-2011-robust-PCA.pdf).

Our method baseline-standardizes each eligible series, groups by public resource
family, then deterministically blocks by metric/entity/fact ID, at most 32 series
per block. Every eligible series enters a block; blocks smaller than three are
ineligible. Fit the masked objective
`0.5 ||P_observed(X-L-S)||² + ||L||_* + lambda ||S||_1`,
`lambda=1/sqrt(max(shape))`, using ≤80 proximal iterations (step 0.5).
Missing coordinates contribute no loss and no anomaly score. Score each series
by incident sparse-residual q90 minus baseline median, scaled by baseline q90
(floor 0.1). Record iteration count and whether convergence was reached.

This is a bounded regularized approximation, not the paper's exact PCP/ALM
algorithm. It seeks localized behavior masked by broad traffic changes. Broad,
correlated faults may instead enter the low-rank component; block boundaries and
limited iterations are explicit limitations. No cross-case predictor is trained.

### C. Unfamiliar local shape — `subsequence_discord_v1`

Source: Yeh et al., *Matrix Profile I: All Pairs Similarity Joins for Time Series*,
IEEE ICDM 2016. Read subsequence/1NN definitions and empirical motif/discord
applications in the author-hosted extended version. The work supplies a general
time-series primitive, not an RCA result.
[Author page and paper](https://www.cs.ucr.edu/~eamonn/MatrixProfile.html).

For lengths 4, 8 and 12 bins, compare each wholly observed incident subsequence
against all wholly observed pre-window subsequences. Z-normalize each subsequence;
its score is the RMS distance to its nearest baseline neighbour. Use the largest
distance across the registered lengths, retaining the actual start/nearest-match
bins. Require ≥3 baseline windows; skip constant or gap-crossing windows. Separate
baseline/current windows cannot trivially match themselves.

This exact small AB-join implementation does not import STAMP or claim its large-
series acceleration. It targets oscillation, staircase and changed local shapes.
Pure level shifts with unchanged normalized shape are deliberately not its strength;
previous level-change methods already cover that mechanism.

### D. Distribution change — `kernel_distribution_v1`

Source: Gretton et al., *A Kernel Two-Sample Test*, JMLR 2012, kernel empirical
MMD and §8 experiments. The paper studies distributions, including non-RCA
structured data. Its IID significance guarantees are not inherited for correlated
telemetry bins. [Paper](https://www.jmlr.org/papers/volume13/gretton12a/gretton12a.pdf).

Compare ≥8 observed baseline bins against ≥4 observed incident bins with unbiased
RBF MMD². Fix kernel bandwidth from positive baseline pair distances (median,
floor 0.1); do not optimize it from successes. Negative finite-sample MMD² values
are retained in audit and clamped to zero only for ranking. This can notice altered
mixtures or intermittency missed by a mean-only statistic. It discards time order,
unlike C, and is reported as a discrepancy score, never a p-value or proof of cause.

### E. Broken event-count balance — `log_balance_v1`

Source: Lou et al., *Mining Invariants from Console Logs for System Problem
Detection*, USENIX ATC 2010, workflow, invariant mining and Hadoop/CloudDB
evaluation. The paper groups logs using program identifiers; inferred count
relations can reveal faults hidden in routine messages.
[Paper and venue](https://www.usenix.org/conference/usenix-atc-10/mining-invariants-console-logs-system-problem-detection).

Our existing pool does not preserve full request identity. Therefore use anonymous
entity/template counts on the existing 64-bin grid, **not fabricated request
sequences**. For every template, shortlist eight baseline-shape neighbours in its
entity. Test ratios {1/3, 1/2, 1, 2, 3}; require ≥4 active fit bins and ≥3 active
validation bins, with relative balance error ≤0.1 in ≥90% of each part. Choose
the best relation using baseline data only. Rank incident imbalance by
`sum(abs(a-r*b))/max(sum(a+r*b),1) * log1p(sum(a+r*b))`.

Select both templates, choosing the companion's closest available source bin.
No zero-valued synthetic log event is created when a completion never appears.
This seeks begin/finish or send/receive imbalance but does not infer these roles
from English keywords. Coarse bins can blur asynchronous completions; unrelated
but coincidentally proportional logs can also pass, so this remains a heuristic.

### F. Operation-mix mutation — `operation_mix_v1`

Source: Sambasivan et al., *Diagnosing Performance Changes by Comparing Request
Flows*, NSDI 2011 (Spectroscope), especially request categorization, structural
mutations, case studies and high-variance discussion. It compares traced request
behavior between executions rather than only finding rare individual requests.
[Paper and venue](https://www.usenix.org/conference/nsdi11/diagnosing-performance-changes-comparing-request-flows).

Within each entity, use all available TRC-L operation rows with valid nonnegative
baseline/current counts. Require ≥2 operations and ≥20 observations per period.
Compute smoothed operation shares (0.5 pseudo-count), each operation's nonnegative
Jensen–Shannon contribution and finite-count support `min(Nb,Nc)/(min(Nb,Nc)+20)`.
Rank R rows by contribution × support. Shares remove period-wide volume scaling.

This is **observed eligible-operation composition**, not whole-service flow
reconstruction, path criticality or Spectroscope's exact algorithm. It can expose
changed use of retry/error/expensive operations when those operations are in the
public cohort; it cannot resurrect operations removed by the inherited TRC-L
filter. Source counts, latency fields and operation names remain unchanged.

### G. Multi-hop dependency concentration — `graph_diffusion_v1`

Source: Kim, Sumbaly and Shah, *Root Cause Detection in a Service-Oriented
Architecture*, SIGMETRICS 2013 (MonitorRank), pattern similarity, random walk
and §6.3 ablation. The paper's graph walk complements pattern similarity;
its external-factor clustering is a separate component not reproduced here.
[Paper](https://netman.aiops.org/~peidan/ANM2020/7.TraceAnomalyDetection/LectureCoverage/2013SIGMETRICS13_Root%20Cause%20Detection%20in%20a%20Service-Oriented%20Architecture.pdf),
[ACM venue confirmation](https://www.sigmetrics.hosting.acm.org/awards.shtml).

Construct per-entity median absolute standardized metric envelopes, using public
pod→service membership only for grouping. Weight call edges by positive incident-
window envelope correlation (≥4 shared bins, nonconstant). Follow caller→callee
dependencies with reverse weight 0.15. Initialize from public anomaly strength;
iterate a 0.2-restart walk up to 100 iterations, L1 residual tolerance 1e-10.
Dangling nodes retain their transition mass. No external alert or private root
chooses the start node. Require at least one supported edge; otherwise record no
native graph signal rather than pretending isolated anomaly ranks are a graph walk.

Select M/R/L/propagation rows by owner mass, and G edges by endpoint mass ×
pattern similarity. This may expose dependencies shared by several symptomatic
services. Missing graph edges, constant envelopes and external common causes limit
it. Correlation and call direction do not establish physical fault causality.

### H. Additive event-slice explanation — `additive_ripple_v1`

Source: Sun et al., *HotSpot: Anomaly Localization for Additive KPIs With
Multi-Dimensional Attributes*, IEEE Access 2018, ripple effect, potential score,
hierarchical search and ablations. This is a journal article, not a top-conference
acceptance. [Author paper](https://netman.aiops.org/wp-content/uploads/2018/12/sunyq_IEEEAccess2018_HotSpot.pdf),
[publisher](https://ieeexplore.ieee.org/document/8288614/).

Use disjoint entity/template log-count leaves. Forecast incident counts with
baseline per-bin means × incident-bin count. For entity, unambiguous severity and
individual-leaf slices, redistribute each slice's observed total in proportion to
its baseline expected counts. Score the reduction in global L2 forecast error,
preferring smaller slices on ties, with a minimum-count support factor. Exclude
the trivial slice containing every leaf and zero-forecast slices. No latency
percentiles or nested span durations are summed; log events are not requests.

Select representative source rows from high-potential leaves. This tests whether
many individually modest changes jointly point to a coherent event slice. It is
a bounded project slice search, **not HotSpot MCTS**. New-only events with zero
baseline are unsupported here; earlier surprise/error-burst selectors cover them.

### Integration, audit and practical limits

Implementation: the existing `exps.py` dispatcher and pure public-pool helpers;
eight separate configs inherit the exact round-16 configuration. The v4 suite
has `execution_authorized: false`, enforced by the common selection-suite loader.
No automatic round assignment or queue transition is made. Prior suites default
to their existing authorization behavior and their files remain untouched.

Each method uses its own scores, not a renamed shared weighted sum. Selection
copies existing facts and adds only the established membership closure. Relations
use two-sided bundles; other methods use ranked source items. Unavailable native
signals use the documented anchor fill, recorded separately. Audit includes native
eligibility, selected-native count, fill IDs, actual selected relation-pair IDs,
source identity and whether the content equals the anchor. A no-op remains a
no-op; it is never evidence that a new mechanism helped.

If the source legitimately provides no public analysis window, window-dependent
methods report no native signal and use recorded anchor fill; they do not invent
a last-third split. Malformed or contradictory window values raise an error.
Operation-mix selection uses its existing baseline/current counts and does not
unnecessarily require the metric-derived window.

Baseline normalization is baseline-only; numerical clipping to ±1e6 occurs in
CPU scoring arrays only. Missing samples are neither model-visible annotations
nor fabricated measurements. The inherited output facts and all render behavior
remain untouched, including the user's existing display decisions.

No million-token catalogue, auxiliary LLM, trained detector or extra GPU is
introduced. Computational bounds include 64-bin windows, 32-series decomposition
blocks, fixed predictor shortlist and iteration limits. Relationship and log
neighbour discovery still have quadratic worst-case work inside entity groups;
static inspection is not a throughput measurement. No runtime estimate is claimed
before future authorized CPU checks.

CRISP (ATC 2022) was screened but not selected: actual critical-path extraction
requires trustworthy per-request parent/start/end spans; summary p95 subtraction
would not reproduce it. Likewise, running a new causal-discovery trainer or
enlarging the public pool is not hidden inside this selection-only amendment.

Suggested order after authorization and qualification: conditional relationships,
log balance, graph diffusion, operation mix, low-rank residuals, distribution
shift, subsequence discord, additive ripple. This does not supersede the already
prepared round-28 spectral method. Each actual round must use every remaining
case separately for each model, with no preliminary inference subset. Future
eligibility/no-op inspections can alter this order for engineering reasons, not
by reading private answers to select a favorable cohort.

### Static review and pause

Review focuses: (1) mechanism novelty and observable source binding; (2) numerical,
window, support and pair-binding edge cases; (3) configuration inheritance,
execution guard and protection of the prior renderer/prompt/method branches.
Syntax/name checks parse source only; configuration checks parse YAML and compare
resolved data, without importing the experiment pipeline. Existing unrelated
unused-import warnings are not silently fixed as part of this intervention.

No CPU unit tests, real-case selection/render checks, smoke tests or inference
were run for v4. Static review does not prove numerical correctness on real cases,
visual admissibility, method complementarity or RCA improvement. Future tests
must cover relation break vs benign coupled movement, correlated vs sparse changes,
shape-only and equal-moment distribution shifts, stable/broken log ratios, uniform
vs changed operation shares, cyclic/disconnected dependency graphs, additive slice
mass and zero-baseline behavior. Verify budget/fact/PNG/request differences before
promoting any method. The user's latest stop boundary remains in effect.

## Selection successor v5: residual evidence coverage

**Date:** 2026-09-15. **Status:** implementation and CPU qualification in progress.

After round 36, Qwen covers 394/480 cases at AC@1 and Gemma covers 412/480, but
both remain below 80% on AIOPS-2022 and AIOPS-2025. All v4 selectors have been
executed. The next eight label-blind selectors target evidence views not isolated
by the preceding magnitude, relationship, distribution, log-balance,
operation-mix and graph-diffusion rounds:

| Policy | Changed evidence-selection mechanism |
|---|---|
| `near_anchor_impulse_v1` | boundary jump and first five public incident bins |
| `sustained_tail_v1` | incident q75 magnitude and longest persistent run |
| `rank_band_rescue_v1` | middle-ranked metric band rather than another top-score list |
| `candidate_round_robin_v1` | candidate-fair allocation across M/R/L |
| `metric_family_portfolio_v1` | balanced public KPI semantic families and owners |
| `topology_separator_v1` | anomaly-weighted edge betweenness |
| `lagged_source_v1` | callee-before-caller anomaly propagation timing |
| `peer_residual_v1` | leave-one-entity-out residual among the same KPI semantic |

Every policy reads only the complete existing public pool and public estimated
incident window. Private labels and prior model outcomes may describe remaining
failure strata offline, but cannot select evidence or route a case. The round-16
renderer, layout, prompt, candidates, field budgets, source facts and model
recipes remain fixed. Selector scores and method identities are audit-only and
are not shown to the Solver. Each round runs the complete model-specific
unretired cohort; no preliminary inference subset is permitted.

The catalogue is motivated by incident-local change, persistence, coverage,
peer comparison, dependency structure and propagation-lag ideas in the existing
PatternMatcher, Sieve, MicroHECL and lag-aware RCA literature. It is a set of
project selectors, not a reproduction of those end-to-end systems. CPU evidence
that inputs differ is required before the first model call, and downstream
coverage remains unknown until each registered round completes.

# RQ3.5 preregistration — 2026-09-25

Numeric authority: `configs/outcome_linked_v1.json`. Entry:
`bash RQs/RQ3_5/scripts/entry.sh {register,cpu,smoke,run,prepare,analyze}`.

## Implemented comparisons

- A: P0/SIRCL evidence × parent/SIRCL diagnostic discipline, plus native T
  and SIRCL_IDS bridges. All four cells now use lossless region blocks, not
  an LLM summary. Native evidence grammars remain part of the evidence factor.
- B: TPV, MORE, W_NO_K, joint marginals, joint counts, joint counts plus
  conditional proportions. The last three share one selected set. Empty sets
  are exact original TPV requests and may reuse the result.
- C: G text/image × J text/image; G-image calibration uses the same compositor
  and reserved G rectangle as the joint visual condition. One image maximum.
- D: two independent repetitions, typed reanonymization, no-derived-calculation
  intervention. Later fixed six-method eval/test/fresh openings require an
  explicit audited roster and research authorization, never automatic scores.

## Scientific decisions and implementation limits

1. Public source duration conventions are inherited unchanged. Only a whitelist
   of trace fields is read; `anomal`, `data_type`, injection metadata and labels
   cannot enter OLE. No raw-log scan. Request-local absence is excluded from a
   field's denominator, not converted to health.
2. Exactly one observed root, unique trace-scoped span IDs and connected acyclic
   parents are required. Uncaptured parents are not invented entry spans.
   Entry status is preferred whenever available; small groups never trigger a
   more favorable latency definition. Fallback entry/local p95 uses >=20
   reference observations; each current outcome group >=5. Local X excludes
   the root span used for Y. This does not imply causal independence.
3. Scope uses explicit pod/service/node bindings and observed readiness or
   positive restart-counter increments; each comparable same-service group
   needs >=2 instances. Other resource summaries are not mislabeled outages.
   Ambiguous ownership, reset counters and inconsistent states are excluded.
4. Two families alternate by within-family absolute conditional difference ×
   support, four packs maximum, two/entity, 2048 tokens in both tokenizers.
   Whole packs only; no displacement of TPV. The numerator/denominator and
   observation scope are model-visible; source trace IDs remain audit-only.
5. A transplants diagnostic instructions only. SIRCL's request for reasoning
   prose preceding JSON is normalized into internal verification plus the
   common parent answer contract. It is not an output-format intervention.
6. Composite uses a fixed 1600×2700 PNG: G 1600×1100 and J 1600×1600.
   The two parent-registered G source crops (diagram and concrete-edge ledger)
   are stacked in fixed slots, omitting only masked non-G whitespace. All G
   annotations survive. This projection is identical in both G-image controls;
   the B→C calibration separately measures its effect. B's original G is unchanged.
   Text wraps without truncation, labels/counts remain visible; overflow raises
   an implementation error. No-derived removes derived bars as well as numeric
   proportions; all four joint counts remain. Native G is not changed in B.
7. RQ3.4 execution/persistence and open-world sidecar are explicit inherited
   infrastructure, not a scientific dispatcher. Audit-only J ledger supports
   literal review, never becomes additional model evidence or a ranking rule.

## Qualification and operational contract

One seeded screen case per AIOPS-2022/AIOPS-2025/AegisLab, all arms on CPU,
three registered smoke arms per experiment × three cases × two models =18
maximum initiated calls. Each complete logical smoke ≤600s including launch,
switching and persistence. Timeout-only is bounded passage, not evidence that
uncompleted cells were tested. No per-model cap resets and no automatic retry.
CPU regression budget 1800s. At most eight physically core-pinned workers;
source-interleaved dispatch and canonical per-case inputs. No whole-corpus prep.

Canonical local YAML, BF16, existing context-safe 8192 output adapter and
granularity-aware scorer are unchanged. New attention disabled. Request timeout
is terminal and recorded; other infrastructure errors fail fast. Done/fail flags
are checked before tokenizer, pickle or request construction; no bulk rehash.
Independent repeat identity bypasses reuse without changing sampling. Existing
major-RQ accounting is imported once from RQ3.4's cumulative call ledger; the
40,000 cap does not reset. No new 5% acceptance threshold.

Screen60 and check120 retain frozen identities and non-overlap group audit.
All claims remain repeated-exposed. Primary families, macro/pooled and failure
handling follow the source plan; paired Pratt-Wilcoxon/dz/Holm, no CI.
No automatic full-run queue or automatic scientific promotion is authorized.

## Qualification revision — 2026-09-25

The original four bounded smokes completed. Review then removed duplicate
`candidate_set` records from the two common P0 conditions in A; all candidates
remain in the one common candidate paragraph, and native controls are intact.
New logical keys prevent reuse of the superseded A inputs. CPU comparisons
certify unchanged B/C/D requests and preserve their GPU qualification. A
requires six additional targeted calls (three cases × two models for the
affected registered smoke arm), pending an explicit one-time exception to its
already consumed 18-call cap. Do not reset or rerun the original smoke window.
The original artifacts remain historical evidence, not current-A qualification.
Detailed checks, timing and qualification provenance are recorded in
`docs/issues/RQ3_5_qualification_2026-09-25.md`.

## DD-RQ35-01: authorized candidate-list repair supplement

Date: 2026-09-26. Status: supplement completed and qualified.
The user explicitly approves the six-call repair supplement requested above.
Only `E_P_D_P` on the same three qualification cases and two sequential models
may initiate new calls. One aggregate 600-second execution window includes
startup, switching and persistence. The existing A scope retains its original
18 calls and gets a cumulative cap of 24; the major-RQ counter is not reset.
No retry/new time window is implicit in this exception. Original inputs and
results are immutable; the repaired six records replace their qualification
references, not their files. The other 12 A smoke records and all B/C/D inputs
are retained using explicit request equivalence. Qualification-driver additions
require static/CPU checks and unchanged-input proof before GPU execution.
This authorizes neither formal experiments nor further scientific changes.

Outcome: all six requests completed in 216.813 seconds, with six `stop`
terminations and no infrastructure errors. Fifteen CPU tests and the
120-request unchanged-input check pass. A is qualified using these six repaired
units plus twelve unchanged original units; B/C/D remain qualified. Current
major-RQ spend is 6,939. This is qualification evidence, not a performance claim.

## DD-RQ35-02: A/B screen execution authorized — 2026-09-26

The user authorizes starting the described formal workflow and asks the assistant
to monitor three minutes, then stop monitoring without stopping background work.
Queue scope is source preparation/audit and A/B screen60 only: at most 1,440 new
formal calls, sequential Qwen then Gemma within each experiment. C/D, check120,
remaining eval, test and fresh events are not automatically opened. Completed
screen results require the registered research review before any expansion.

An explicit `formal_authorization.json` is the narrow runtime authority; the
configuration's broad `execution_enabled=false` is not changed into a blanket
authorization. A one-time queue activation preserves previous source snapshots,
checks unchanged existing function ASTs and 120 model inputs, and carries all
four qualifications forward without new smoke calls. Normal resume performs no
such CPU matrix or artifact rehash: it reads done/fail flags, skips completed
model phases before GPU startup, and submits only uncommitted work. Request
timeouts remain terminal; other infrastructure failures stop the owned queue.
SIGTERM stops submission and drains the runner before releasing its model.
Preparation uses up to eight distinct physical cores and existing per-case
parent artifacts, with source-interleaved scheduling. No training or attention.

## DD-RQ35-03: lossless block repair and comprehensive logic review — 2026-09-26

**Status:** user-authorized repair; formal execution remains paused pending
current-A GPU qualification. This supersedes A's per-line JSON serialization,
not its evidence selector, instructions, candidates, models or output contract.

**Evidence and decision.** A formal SIRCL-evidence case needs 38,418 Qwen /
40,691 Gemma input tokens under the JSON wrapper, despite native SIRCL fitting
at 29,824 / 32,035. Replace repeated JSON keys and escaping with one heading per
consecutive region and verbatim original records. Apply to all four crossed
conditions, not selectively to long cases. Preserve record order, empty lines,
embedded newlines, fields, values, precision, candidate order and both guides.
Do not truncate facts, shorten output, enlarge context or exclude the case.
The affected case's repaired E_S_D_P uses 29,471 / 31,687 input tokens.

**Verification and recovery.** Inspect the complete 60-case screen on both
processors, not just the three qualification cases. This is a one-time repair
check, not restart-time verification. The queue reads its small capacity-report
marker; completed requests still skip before context/tokenizer loading.
Context errors identify case, arm, counts and limits. Direct-run invocation
must use exactly one registered model and applies the same infrastructure-fail
classification as the queue. SIGTERM is checked again after waiting for request
capacity. Repeated local-reference p95 computation is memoized without changing
its input samples or values.

**Statistics.** Add missing dataset-equal macros, fault/granularity strata,
cost observation counts, A native-calibration and B joint-structure secondary
families, C compositor calibration, D registered comparisons, repair/break and
event-group sensitivity. Each hypothesis family uses one common eligible case
set per model and Holm jointly across its two models. Model failures retain
their registered scores; known failure costs remain in cost summaries. No new
5% threshold, efficacy decision or use of interim accuracy in this repair.

**Consequences.** New logical IDs isolate all four changed A conditions. Of 38
completed formal units, 26 belong to that superseded input representation and
need new requests later; 12 native-control units remain eligible. Preserve all
old files and spent calls. Preparation and B/C/D model-visible inputs remain
unchanged. CPU equivalence cannot qualify changed A prompts: the minimal live
supplement is 12 calls (the original three qualification cases × E_P_D_P and
E_S_D_S × two models), sharing at most 600 seconds and the original call scope.
A has already spent 24 qualification calls; another supplement requires an
explicit exception, not a new nominal smoke or budget reset. No GPU calls or
formal restart are performed by this repair. Metadata publication is resumable
with the completion marker written last. Original authority/qualifications and
source snapshots remain under `repairs/lossless_blocks_v3/previous/`.

## DD-RQ35-04: block supplement and complete formal reset authorized — 2026-09-26

The user now approves the twelve-call targeted GPU supplement and explicitly
orders removal of all 38 earlier formal results, including the twelve otherwise
compatible native results, followed by a fresh run. This supersedes DD-03's
preservation/reuse instruction for those 38 formal results only. Qualification,
preparation, source audits, code, configuration and all earlier RQs are retained.
Spent calls are not erased or reset.

Supplement: original three qualification cases × E_P_D_P/E_S_D_S × two sequential
models, at most twelve new calls and one 600-second aggregate window. A's
original smoke scope grows from 24 to 36 lifetime calls; this is the explicit
user exception, not a new nominal smoke. Complete conversations and raw results
are reviewed before formal restart. The driver amendment changes no model
input and is qualified by the existing 120-input CPU identity matrix.

After passage, inventory and remove the old A-screen result tree, its 38 flags,
formal-only reuse indexes and obsolete progress. Preserve a deletion manifest
with identities and sizes, not answers. Redact deleted outputs from call-cache
rows and retire their lookup keys while retaining each consumed call. Verify
zero active A/B formal completions before enabling the unchanged A/B screen60
queue. No automatic check120, C/D, test, training or attention is authorized.

## DD-RQ35-05: last-GC clock repair and four-call supplement — 2026-09-26

The user approves fixing the last-GC timestamp omission and the proposed narrow
four-call qualification before restarting A/B screen60 from zero. Display the
SIRCL `istio_agent_go_memstats_last_gc_time_seconds` means relative to the same
public, case-local origin used for the three previously registered clock fields.
Do not include last-GC in the origin's anchor set. Preserve standard deviations,
selection, numeric deltas, candidate lists and all other diagnostic fields.
This is an RQ3.5-local adapter; RQ3.4, processed data and preparation stay intact.
Unsupported schema or clock sentinels fail closed rather than guessing units.

Only E_S_D_P, E_S_D_S and SIRCL_IDS_NATIVE can change. CPU checks must confirm
the scope across all 60 prepared screen cases and preserve B/C/D input identity.
GPU supplement: original qualification case INC-0986D6C54EC6, E_S_D_S and
SIRCL_IDS_NATIVE, two sequential models, at most four calls / 600 seconds total.
The original A smoke scope retains its 36 consumed calls and has an explicitly
authorized lifetime ceiling of 40, without resetting the major-RQ accounting.
Historical qualification inputs remain archived; replace only the four affected
qualification units after persistence and actual input/output review.

The earlier 38 formal results were already deleted under DD-04. Once qualified,
restart only the original A/B screen60 queue from zero; keep all 60 preparations
and use terminal flags for normal resume, not this one-time repair audit.

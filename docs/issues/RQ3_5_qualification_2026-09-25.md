# RQ3.5 implementation and qualification — 2026-09-25

Status (updated 2026-09-26): the earlier qualifications below are historical.
The formal cohort exposed an A serialization overflow. The authorized lossless
block repair changes all four crossed A prompts and requires targeted live
requalification; old GPU passage is not automatically transferred. B/C/D and
native controls are checked for unchanged inputs. Formal execution is paused.
The final CPU review and impact inventory are recorded in the section below.

## Scope and entry points

- Implementation: `RQs/RQ3_5/src/`, five functional modules plus `__init__.py`.
- Configuration: `RQs/RQ3_5/configs/outcome_linked_v1.json`.
- Entry: `bash RQs/RQ3_5/scripts/entry.sh`.
- Artifacts: `RQs/RQ3_5/results/outcome_linked_v1/`.
- Existing RQ3.4 public preparation is inherited; only new per-case request and
  instance indices are computed. No raw-data conversion or old-RQ modification.
- Qualification only. Formal stage openings require a separate explicit
  `formal_authorization.json`; later roster openings remain unavailable.

## Findings during implementation (before GPU calls)

1. Request binder expects the unified `stable_hash`, not the RQ-local JSON
   digest. CPU regression caught the mismatch before inference; fixed the
   binding call. Selection/metric values did not change.
2. The SIRCL numeric-ID adapter inserts a separate initial text part. Selecting
   part zero as its evidence was incorrect. Now require exactly one part with
   the inspected evidence header, preserve the clock-value schema sentence,
   and separate guide/evidence/answer boundaries explicitly.
3. Initial composite shrank the parent's mostly masked canvas and wasted G
   space. The registered G chart and concrete-edge source crops are now placed
   into fixed slots. No G fact is deleted, native B requests remain unchanged,
   and both C G-image conditions use exactly the same projection. Calibration
   against native G remains necessary and is implemented.
4. Audit-side J facts are supplied only when J actually appears in the image.
   Marginal-only, TPV and other controls cannot acquire unseen joint facts
   through the sidecar. The sidecar never changes the model answer or reward.
5. Resume skips terminal done/fail markers before context/tokenizer creation;
   only uncommitted attempts in the owned scope are marked interrupted. Repeat
   identity bypasses reuse while remaining within the aggregate smoke cap.

Every pre-inference contract revision and CPU report is retained under
`preinference_revisions/`. Once any new inference starts, this convenience
cannot reset its call/time window or silently replace its contract.

## CPU evidence

13 adversarial unit tests pass. Three seeded real cases cover 20 conditions ×
two model processors =120 compiled inputs, including typed reanonymization,
paired guide changes, unchanged TPV, independent repeats and no-op equality.
All full requests fit the frozen context/output adapter; actual counts are in
`cpu_qualification.json` and each `cpu_inputs/.../projection.json`.

| Dataset | Opaque case | Cold total preparation | New index | Selected request packs |
|---|---|---:|---:|---:|
| AIOPS-2022 | INC-0986D6C54EC6 | 14.61 s | 5.63 s | 4 |
| AIOPS-2025 | INC-B8CEA35848D0 | 19.86 s | 10.94 s | 2 |
| AegisLab | INC-6A048DD0C35E | 14.70 s | 5.70 s | 0 |

Each worker was pinned to a distinct physical core. These measurements concern
three samples, not a full-corpus throughput guarantee. Scope packs are zero on
these three real samples; scope counting/eligibility has synthetic coverage,
not a claim of live real-case scope effectiveness. The AegisLab no-op retains
TPV rather than inventing successful/failed request groups.

The assistant inspected actual prompts and composite PNGs, including both
positive request-pack samples. The preregistered renderer has fixed geometry,
visible counts/denominators, labels and independent G/J controls. Renderer
quality does not imply a positive RCA result.

## GPU qualification

Four logical smokes completed sequentially, each with three cases, three
conditions, two sequential local models, ≤18 initiated calls and ≤600 seconds
including model startup/switching and persistence.

| Experiment | Completed logical units | New model calls | Wall seconds | Current qualification |
|---|---:|---:|---:|---|
| A: evidence × instruction | 18/18 | 18 | 263.506 | Original completed; repaired input pending targeted qualification |
| B: outcome-linked evidence | 18/18 | 14 | 227.004 | Passed, unchanged requests |
| C: joint representation | 18/18 | 16 | 235.724 | Passed, unchanged requests |
| D: locked mechanisms | 18/18 | 18 | 252.847 | Passed, unchanged requests |

All 72 logical units have complete outputs; identical-input reuse accounts for
66 actual new calls. There were no bounded-timeout-only completions or new
infrastructure failures. Prior major-RQ accounting is 6,867; the cumulative
counter is 6,933, not a reset 40,000-call budget. New attention is disabled.
Owned runners and model servers have exited; no formal process was launched.

Automated review checked all completed inputs, stored PNGs, conversations,
raw responses, costs and atomic status. Assistant inspection additionally read
actual A/B/C/D prompts and answers, sampled complete D conversations and its
reanonymized image, and viewed both positive request-pack cases' C composite
images. Examples live under `cpu_inputs/INC-0986D6C54EC6/` and
`cpu_inputs/INC-B8CEA35848D0/`, especially
`qwen3.8-27b/G_IMAGE_J_IMAGE/dashboard.png`; original inference artifacts remain
under `stages/smoke_<experiment>/<model>/`. This is sampled semantic/visual
review, not exhaustive proof that every model inference is correct. Some
answers overinterpret observed associations; those are model behavior, not a
reason to resample until correct or to claim established causality.

## Post-smoke correction: one candidate list in A

Review found that the common P0 text included a `candidate_set` record as well
as the common candidate paragraph. The SIRCL common condition had only the
paragraph. Removed the duplicate record in `E_P_D_P` and `E_P_D_S`; the full
ordered candidate set remains in the common paragraph. Native controls and
B/C/D inputs are unchanged. No candidate or diagnostic telemetry was removed.

The first explicit CPU revision compared all 120 requests: exactly 12 changed
(two A conditions × three cases × two models), and 108 were identical. The
affected live-smoke subset is six `E_P_D_P` units. A's logical keys are revised
so old done flags cannot incorrectly skip the repaired requests. All original
smoke artifacts, flags, failure history and call/time accounting are retained.

A second review-only correction prevents the `review` command from upgrading
an old-contract smoke to qualification for changed inputs. Another 120-input
CPU comparison found zero further changes. Explicit tests confirm that old A
review now refuses qualification, while B/C/D retain passage through the saved
input-equivalence proofs. This one-time migration is not a resume-time scan.

Proofs: `candidate_once_v2_revision/completed.json` and
`candidate_once_v2_revision_e4c24ab94bbe/completed.json` under the result root.
Current source contract:
`5b31ce3d5350af1c8aa443745a88d9836c0ec147d043dd0123de98b39e5c8919`.
Final CPU regression took 21.20 seconds with all 13 unit tests and 120 input
checks passing. Ruff checks, formatting, Python compilation and shell syntax
checks pass; the six Python files total 2,478 physical lines.

**Historical hold at 2026-09-25:** A had used its original 18-call allowance. A
request for a one-time maximum-six-call, aggregate-600-second repair check has
been sent to the user. Until approved and completed, A remains
`requires_targeted_gpu_requalification`; neither an old smoke nor CPU-only
equality for other conditions can replace it. No additional GPU calls or
full-scale experiments are automatically authorized by this record.

## 2026-09-26: authorized six-call supplement completed

The user approved the exact pending supplement. Added a qualification-only
driver with an explicit authorization file, original A call scope and cumulative
cap 24 (=18 original +6 additional). Original smoke reports, conversations and
flags are not overwritten. The supplement has its own single non-resettable
600-second window and cannot launch B/C/D or formal experiments.

Static Ruff/format/Python/shell checks pass. Fifteen unit tests include the
six-target restriction and rejection of the 25th same-scope call. The final
120-request CPU comparison took 21.35 seconds and found zero input changes
from the already repaired version. Two CPU-only contract revisions preserve
their proofs; a minor static test-style issue was corrected before GPU startup.
The final source contract is
`589aff1996c5915343471413e3a2f83af5aeaa9cccfae0a21023ad4709bf3b1e`.

| Supplement | Result |
|---|---|
| Authorized/executed requests | 6/6; Qwen 3, then Gemma 3 |
| Total wall time, including persistence review | 216.813 seconds |
| Complete / timeout / infrastructure failure | 6 / 0 / 0 |
| Raw finish reasons | Six `stop`; no length termination |
| JSON / exhaustive-candidate membership | Six valid; no unknown output IDs |
| New model calls in this supplement | 6 |
| Original A + supplement calls | 24 |
| All RQ3.5 qualification calls so far | 72 actual calls |
| Cumulative major-RQ ledger | 6,939 complete calls, including preserved historical accounting |

All six full answers were read. Persisted conversations contain every text
input and the full raw answer. Exact comparisons against their original A
inputs confirm the only change is removal of the redundant candidate record;
system, inference recipe, schema, common candidate paragraph and remaining
evidence are unchanged. Candidate sets have 85/104/63 IDs in these three cases
and remain identical across models. These A conditions are text-only; no new
dashboard or visual comparison is implied by their supplement.

Model behavior remains distinct from implementation validity: on
INC-0986D6C54EC6 both models call a five-digit pod ID a service in their reason.
On INC-6A048DD0C35E Qwen describes a trace latency as 30 seconds although the
visible inherited field is 30,006,458.63 ms; Gemma's approximately 30,000-second
conversion agrees with that displayed value. These examples are observable
type/numeric-reference errors, not evidence to resample or change scoring.
The inherited telemetry itself was not rederived by this repair. Other causal
claims remain unproven; sidecar status `partial_literal_audit` does not mean
every explanation is verified. No accuracy gate or method-promotion decision
was taken from these three cases.

Qwen startup emitted optional DeepGEMM/CUDA_HOME warnings; both services then
started and completed all requests. Gemma also recorded first-shape Triton JIT
warnings. No recipe, CUDA environment or runtime package was changed to suppress
them. Owned servers and runners exited; no GPU compute process remained at the
final check. No training, attention capture or full-scale experiment started.

Artifacts: `repairs/candidate_once_v2/{authorization,report}.json`, controller
and per-model logs; new conversations/raw outputs under
`stages/smoke_exp_evidence_instruction_cross_candidate_once_v2/`. A's current
qualification references six repaired units plus twelve unchanged original
units; B/C/D retain their original GPU records through CPU equivalence proofs.

## 2026-09-26 — Formal A input overflow discovered during requested resume

The user reported accidental Windows sign-out and requested resume without
ongoing monitoring. Read-only inspection found no remaining experiment/server
process, but the previous queue had already recorded a concrete fatal error:
`ValueError: Registered intact input exceeds context; no silent truncation`.
The runner drained to 38 `done` flags out of 360 Qwen A units and exited 1;
the supervisor then terminated its own vLLM. The later `EngineDeadError` occurs
in server shutdown and is not evidence that an engine crash caused this stop.
The log does not establish the timing or effect of Windows sign-out itself.

First pending unit: `INC-1E6DCFC0A453`, `E_S_D_P`. Targeted CPU-only token
inspection reused its existing context; no model calls, full-result validation,
preparation rebuild or result deletion was performed.

| Input | Qwen input tokens | Gemma input tokens | Fits both |
|---|---:|---:|---|
| E_S_D_P | 38,418 | 40,691 | No |
| E_S_D_S | 38,303 | 40,567 | No |
| SIRCL_IDS_NATIVE | 29,824 | 32,035 | Yes |

The unchanged 40,960 context and 8,192 output reservation leave 32,768 input
tokens. `crossed_parts` serializes each SIRCL evidence line as a separate JSON
record; the typed evidence block alone is 70,245 characters. This serializer
adds repeated wrappers/escaping to native evidence that otherwise fits. The
three qualification cases did not expose this formal-case capacity problem.

Resume was not launched because the same pending input would fail again.
All 60 prepared contexts and 38 completed formal results remain untouched.
Proposed next action requires an explicit input-contract repair: a lossless,
lower-overhead common text serialization, shared by the crossed conditions,
with targeted capacity/fact checks and truthful qualification/result scope.
Do not silently truncate evidence, reduce the output reservation, enlarge the
model context, exclude this case, or skip A to start B as a resume workaround.

## 2026-09-26 — Comprehensive logic review and lossless-block repair

Scope: all five RQ3.5 modules and config/queue, plus their inherited request
binder, model executor, scorer callback, accounting, asynchronous writer and
completion/reuse boundaries. This is static/CPU correctness work, not new RCA
efficacy evidence. No prior scientific results or shared recipes are rewritten.

| Focus | Finding / disposition |
|---|---|
| Input budget | Per-line JSON introduced unnecessary escaping and repeated keys. Replaced uniformly across the four crossed arms with region blocks preserving verbatim records. Native controls unchanged. |
| Sample coverage | Three qualification cases missed the overflow. Added an explicit whole-screen CPU capacity/equality audit, with a small stored result for queue startup; never a restart-time bulk reconstruction. |
| Resume / failure | Direct `run` formerly skipped any existing fail flag; now rejects infrastructure failures just like the queue, but retains done and request-timeout outcomes. |
| Scheduling / pause | Reject missing/unknown model instead of allowing a mixed-model task list. Recheck stop after waiting for concurrency capacity. No changes to the 36-request or 8-worker settings. |
| Performance | The same reference p95 was recomputed for every observed request. Memoize each entry/entity/operation threshold; count-equivalence and call-count tests cover this optimization. Existing preparation is reused. |
| Reporting | Added registered macros, cost/fault/granularity summaries, missing secondary comparisons, event-group sensitivity, and shared pairing sets per family. Failures do not acquire fabricated zero latency/token usage. |
| Metadata recovery | Repair publication now commits its final marker last and supports resuming interrupted publication without rerunning CPU work. Tests simulate interruption during qualification publication. |
| Scientific isolation | Only A's serialization changes. Guides, source observations, candidate order, selectors, actual model recipes, output adapter and scorer remain fixed. No dataset/label routing or new experiment arms. |
| Source / denominator logic | Reviewed explicit-status precedence, trace-scoped span uniqueness, rooted/acyclic observed graphs, reference thresholds, local-operation denominators, peer support, four-count marginals and derived proportions. Unknown/absent local observations are not treated as healthy. Existing public-field whitelists and evaluator-private labels remain separate. |
| Representation | Whole-screen CPU rendering covers registered fixed G/J composition and no-derived conditions. Counts and field inventory remain bound to visible content; no clipping or hidden evidence deletion was introduced. Typed reanonymization remains covered by the integrated qualification cases rather than claiming all-case reanonymization coverage. |
| Budget / persistence | Prior calls remain counted; no new GPU calls. Smoke and formal reuse scopes remain separate. Independent repeat identities still prevent answer-cache reuse. Flags are committed after response/scoring/artifact writes; no bulk artifact audit is added to resume. |

Changed formal scope: 26 historical Qwen A units (7 E_P_D_P, 7 E_P_D_S,
6 E_S_D_P, 6 E_S_D_S) are preserved but not eligible for repaired-arm summaries.
T_NATIVE and SIRCL_IDS_NATIVE retain six completed units each. All 60 preparation
artifacts are kept. New crossed logical IDs prevent old done markers from
skipping the repaired input. No files are deleted.

The triggering E_S_D_P request drops from 38,418 / 40,691 to 29,471 / 31,687
tokens (Qwen / Gemma), with no fact removed. The unchanged limit is 32,768 input
plus an 8,192-output reservation inside 40,960 context.

Evidence: `RQs/RQ3_5/results/outcome_linked_v1/repairs/lossless_blocks_v3/`
contains prior source and qualifications, whole-screen capacity report,
three-case integrated CPU report, request-identity comparisons and affected /
retained logical keys. Static/CPU checks cannot establish that the repaired
prompts have completed GPU qualification or improve MRR. A still requires the
explicit 12-call supplement described in DD-RQ35-03 before formal resume.

Final checks: Ruff lint and format checks plus both launcher shell syntax checks
passed; all 24 CPU unit tests passed. The whole-screen audit covered 60 cases ×
19 input conditions × two processors (2,280 capacity checks), with zero failures
in 139.87 seconds. The three-case integrated qualification covers 120 requests;
24 crossed identities changed as intended and 96 unrelated identities remained
unchanged. These are CPU input/renderer checks, not additional model calls.

Final metadata review also found inherited fields from the previous, different
GPU supplement (`approval_required=false`, old repair report and crossed units).
Publication now explicitly marks A as requiring fresh approval, keeps only the
unchanged native qualification units as current evidence, and preserves prior
metadata in `qualification_metadata_revision_previous.json`. A regression test
checks that old approval cannot carry into this changed-input qualification.
The final three-case matrix was repeated after this metadata-only correction;
all 120 current request identities are unchanged by the correction. The current
source contract is recorded in `repairs/lossless_blocks_v3/completed.json`;
formal authority deliberately remains on the predecessor until requalification.

Final integrated regression: 24 tests, zero errors/failures; 120 request builds
in 20.86 seconds. Final registered contract:
`69971928802554c40df7882542c49f8f80e97445d8378442bf473eeb34507938`.
Registration, CPU qualification, capacity marker and the four qualification
records agree on that contract. No GPU request or formal resume was initiated.

## 2026-09-26 — Authorized 12-call supplement; last-GC clock discovered in review

The user authorized the twelve-call supplement and deletion of all 38 former
formal units, not just the 26 changed crossed units. The operational driver
passed 26 CPU tests and the unchanged 120-input identity matrix (24.62 s).
Source contract: `f18fb1233248b61e801d02398afc6fb1f427d677b12a1fb1eb456dce998167c7`.
The same A qualification scope retained its 24 previous calls and initiated
exactly 12 additional calls. Qwen six and Gemma six completed in 226.149 s,
with complete conversations, valid candidate IDs and no infrastructure failure.
These A conditions are text-only; no new dashboard image was expected.

**Runtime completion is not final passage.** Assistant inspection of the actual
evidence found `istio_agent_go_memstats_last_gc_time_seconds` still expressed as
an epoch-valued metric. The
[Prometheus implementation](https://github.com/prometheus/client_golang/blob/main/prometheus/go_collector.go)
defines the underlying metric as seconds since 1970. This is an ordinary public
GC timestamp, not proof that gold root or injection time was read. Nevertheless,
it violates the registered relative-clock input rule. The inherited guard only
recognized timestamp/unixtime/start_time/boot_time/last_seen; its semantic
allowlist also omitted last-GC time. Therefore the previous static and capacity
checks did not establish complete timestamp coverage.

Scope audit using existing preparation, without new inference:

- Two of the twelve new inputs are affected: E_S_D_S on
  `INC-0986D6C54EC6`, one per model.
- Among the 60 A-screen cases, 17 AIOPS-2022 cases expose it in E_S_D_P,
  E_S_D_S and SIRCL_IDS_NATIVE (51 case/arm inputs before model duplication).
- The other three A arms do not expose this named metric in this scan. This
  is a known-field audit, not proof that no other clock-valued field exists.
- Some public reasons overstate onset/association as causality or use service
  for pod IDs. These are recorded model-behavior findings, not a reason to
  resample answers or change scores during qualification.

A is now `failed_model_input_audit`, despite its complete runtime report.
The raw supplement remains intact. Formal execution has **not** restarted.
The narrow next correction is an RQ3.5-local display translation of this clock
using the existing shared public origin, preserving means' differences and
standard deviations. It must not alter selection, drop the metric, modify the
old RQ3.4 source or regenerate preparation. After CPU scope/equality checking,
the expected minimum new live coverage is four calls: affected E_S_D_S and
native SIRCL on the same qualification case × two models. This would exceed
the just-consumed supplemental allowance and requires explicit user approval;
no such additional calls have been made.

### User-authorized deletion completed

Removed all 38 previous formal A outputs, prompts, trajectories, conversations,
completion flags, formal-only reuse indexes, obsolete progress and formal logs:
537 files, 11,710,842 bytes (about 11.17 MiB). No result backup was kept; those
answers cannot be recovered from this result root and must be inferred anew.
Their 38 SQLite rows retain consumed-call accounting, but cached responses are
redacted and lookup keys retired so native arms cannot silently reuse them.
Total consumed calls remain 6,989, including the deleted formal calls and this
supplement. All 60 preparation flags/contexts, source audits, qualification
records, models and other RQs are preserved. Active formal result count is zero.

Evidence: `repairs/lossless_blocks_v3/{report,assistant_review,last_gc_clock_audit}.json`
and `repairs/formal_reset_20260926/{manifest,completed}.json` beneath the RQ3.5
result root. The queue state is `reset_waiting_qualification_review`; it cannot
be described as running or qualified for formal restart.

## 2026-09-26 — authorized last-GC correction

The user approved the proposed last-GC repair and four-call GPU supplement.
The local adapter now translates only this metric's two CSV means using the
unchanged, previously registered public origin; standard deviations and other
metrics remain unchanged. The input safety check explicitly covers this field.
The fix applies at request construction, so the 60 prepared contexts need not
be regenerated. Three SIRCL-evidence A conditions receive a new logical version;
other arms and inherited RQ3.4 source are untouched.

Static checks and 28 focused unit tests passed. The one-time CPU request audit
and bounded four-call supplement are being executed under `repairs/gc_clock_v1/`;
do not infer qualification success or formal restart from this pending entry.
The original A smoke call scope is capped at 40 cumulative calls, including the
36 already consumed. No automatic retries or widening to other stages.

### Qualification outcome

Passed: 28 unit tests and all 120 CPU request units (25.00 s). The one-time
screen audit checked all 60 cases / 1,200 unique case-arm inputs (107.00 s):
exactly 51 inputs changed (17 AIOPS-2022 cases × three SIRCL conditions), with
1,149 unchanged. Changed lines contain only the registered last-GC means and
their relative-unit label; other lines and standard-deviation columns match.
Both tokenizers' capacity checks passed on all 180 SIRCL case-arm inputs.
B/C/D inputs and the renderer are unchanged; preparation was not regenerated.

The approved four-call GPU supplement completed in 213.02 s. All four ended
with `finish_reason=stop`, valid JSON and zero unknown candidate IDs. Actual
input review confirms relative GC rows and no displayed absolute origin;
conversations, raw responses and completion artifacts were checked. Model
answers still sometimes call pod IDs services or treat lack of stronger evidence
as evidence of health; these are observable model behaviors, not reasons to
resample or rewrite scores. These four conditions are text-only, so no new
renderer qualification was needed. A now passes under contract
`bbe9b1e3b979df891fa588f0f3565edd2e290745ad0c93d1cec5fe9d04980329`.

Before restart, all four A/B model phases showed 360 pending units each and zero
formal completions. The original A/B screen60 queue has been launched under the
repaired contract; no check120/C/D/test expansion. Prior 38 deleted calls still
count, and total consumption before this fresh queue was 6,993. Evidence:
`repairs/gc_clock_v1/{completed,capacity_audit,report,assistant_review}.json`.

## 2026-09-26 — Completed-screen analysis observations

The A/B screen is now complete (1437 done, three request timeouts); this entry
does not reopen qualification or change source result status. No runtime code
or model input was edited during analysis.

1. **Confirmed reporting-field error:** the runtime analysis row's `granularity`
   stores the full entity-to-type map, not the accepted-root type. The independent
   offline report derives root strata from evaluator-private accepted labels and
   their types; all original per-case scores remain unchanged. Do not reuse the
   map-as-category aggregate for scientific granularity claims. Repairing future
   runtime summaries is a separate implementation task, not required to rerun
   inference. Report evidence: `RQ3_5_Screen_Analysis_2026-09-26_assets/per_record.csv`.
2. **Confirmed cross-evidence projection difference; attribution scope:** in
   INC-6A048DD0C35E, P0's 807 SELECT ConsignRecord fault p95 is displayed as
   30006458.63 ms while SIRCL displays 30006.3 ms; counts/windows also differ.
   The source-attested SIRCL projection uses duration scale 0.001 in
   `RQs/RQ3_1/src/exps.py::_registered_trace_duration_projection`. The example
   proves different numerical projections, not a corpus-wide error rate or a
   new causal explanation for every rank change. Preserve these frozen inputs
   and report A as an evidence-package contrast. A future pure-selection claim
   needs an explicit duration/statistics alignment control and scope audit;
   do not silently change historical bridges or invalidate all existing results.

Full analysis and actual prompt/conversation references:
`docs/experiment_reports/RQ3_5_Screen_Analysis_2026-09-26.md`.

# RQ3.7 experimental protocol

## DD-RQ37-4 — C cold-path nested-log clock repair (2026-09-28)

User authorizes diagnosing, fixing and resuming the stopped C preparation.
The failed public input is RE2-TT `INC-12D885A5B485`: a WiredTiger message
contains `[epoch_seconds:microseconds][thread]` inside its JSON message string.
The inherited outer calendar scrubber removed `$date` but retained the embedded
seconds as `{num1}` numeric summaries. This is a real absolute clock, not a
large-memory-value false positive. An offline build also confirmed the clock
would enter C's actual ALL_ID appendix; skipping only the old P/H preflight
would not repair the issue. No C formal model call has received this input.

The additive RQ37-local `rq37_wiredtiger_relative_clock_v1` adapter recognizes
only the source-attested WiredTiger prefix/template. It translates that slot's
already-public min/median/max by one case-wide minimum public log-clock value,
labels the slot `relative_clock_seconds` and the other component
`microseconds_component`. It never combines separately aggregated components,
recovers missing precision, uses private event times, or changes counts, IDs,
ordinary numbers, templates, raw data, windows or model recipes. Original
per-slot differences and ranking axes are preserved; actual budget selection
equivalence is checked on the failing case, not assumed for arbitrary inputs.
The origin and provenance are CPU-side only. Unrecognized clocks and nonzero
WiredTiger transaction-clock fields still fail closed rather than being guessed.

This is a forward privacy-projection repair for uncommitted cold contexts,
not a retrofit of historical inputs or a new experimental arm. The frozen
scientific source/config contract remains unchanged; adapter and helper hashes
are explicitly recorded in C's preparation markers, diagnostic report and
`stage_c_clock_repair.json` amendment. Completed caches/answers are retained;
the impact audit checks the small actual public views, not bulk raw histories.
Keep C's already-completed 18-call smoke and its exact original inputs. Targeted
CPU real-case builds must pass before resume; no extra smoke calls or replacement
responses are introduced. The repair uses the same qualified request, renderer,
client, processor and writer paths. Final actual-input clock checks stay active.

See [qualification/incident record](../../../docs/issues/RQ3_7_stage_C_qualification.md)
for source evidence, checks, affected scope and continuation state.

## DD-RQ37-3 — Stage C execution authorization (2026-09-28)

The user authorizes proceeding after the completed A/B analysis. All registered
expansion checks pass under contract
`1a8d2032bb94718e3a23b62d1a62e331b0b1b671410312b78e22b1dc756997a2`.
Qualify C itself, then execute the locked five arms on eval480 and exposed
test360, Qwen followed by Gemma. Do not select another champion, tune on C,
change model recipes, or reclassify exposed data as untouched.

The immutable registration contains no fresh roster and explicitly records
`unavailable_no_complete_audit`; no complete exposure audit was located in the
registered data/result lineage. Thus this activation contains 8400 logical
eval/test units, not 9300. Fresh-event inference remains unactivated until a
complete historical-access and connected-window audit seals a separate roster
before its calls; no independent-event claim follows from this execution.

Copy only small terminal A flags to the corresponding C logical targets,
including the published 120 TPV supplement pointers and all failures. The
inputs, source contract and replicate are identical. This reuses 1800 logical
units without loading contexts, re-rendering, rescoring or re-hashing artifacts;
it does not turn a timeout into success. A/B flags and raw outputs stay intact.
The remaining maximum is 6600 formal calls plus C's single bounded smoke
(18 calls/600 seconds), against actual cumulative 24643 and shared hard40000.

Keep the frozen scientific implementation unchanged. A separately hashed,
additive stage-C operations helper records this flag aliasing, targeted CPU
checks of previously unused execution paths, and cold-context preparation.
Missing contexts are built once from canonical per-case public data, using up
to eight independently pinned workers; existing context/terminal markers are
trusted. No bulk historical request reconstruction on resume. Stop on genuine
implementation/infrastructure failures; retain request timeouts as terminal
missing results under the existing policy. A/B qualification remains historical;
C requires its own bounded smoke and saved-input/output/image review.

## DD-RQ37-2 — user-authorized TPV reference supplement (2026-09-28)

The user explicitly authorizes adding 120 corrected-unit TPV calls: the original
RQ3.5 screen60 (20 cases per primary dataset), each on Qwen and Gemma. This
supersedes DD-RQ37-1's reference-only prohibition **only for those 120 targets**.
The two historical Qwen TPV timeouts and one B3_G timeout are excluded. No
additional arms, alternative selections, model changes, repeat sampling, or C
expansion is authorized. Historical answers and prompts remain immutable.

The saved TPV prompts are compared against the current, previously qualified
RQ3.6 TPV recipe; only the documented `parent_trace_unit_labels_v1` substitutions
may differ from the old prompt. Numeric values, original G PNG, candidates,
instructions, selection, runtime and scoring remain unchanged. Checks run before
new inference; this is completion of an existing arm, not a new smoke experiment.
No extra qualification model calls are registered. Source recipes and existing
A/B qualifications remain frozen; an additive, separately hashed runner lives
under `scripts/tpv_backfill/` and writes `results/tpv_reference_backfill_v1/`.

The supplement waits on the existing A/B queue lock without polling. It starts
only after normal A/B completion; failure or pause of the predecessor does not
authorize its automatic restart. CPU checks precede sequential Qwen/Gemma runs.
All attempts count against both the shared 40,000 limit and a 120-call supplement
cap. A request timeout is terminal and is not automatically retried. Other
infrastructure errors stop the supplement. Resume reads small done/fail flags.
After all 120 targets terminate and writing drains, the A reference placeholders
are replaced with pointers to the supplement, preserving original placeholder
flags alongside the new results. The other historical results are not touched.

Budget amendment: A/B formal maximum **3420 → 3540**; all registered stages plus
planned qualification **12774 → 12894**. The increase is **120**, not 240; it
already includes both models. The cumulative major-line ceiling stays 40,000.

The [complete protocol](../../../docs/experiment_plans/CanvasRCA_RQ3_7_Research_Plan.md) is incorporated here, including historical overlap/source index, exact numerical and geometry rules, statistics, error policy, new-event isolation and implementation boundaries. Machine-readable registration is `../configs/fusion_v1.json`. The source/config contract is frozen only on the future explicit `register` command; no experimental registration or qualification is claimed by writing these files.

| Experiment | Population | Conditions | Maximum new calls |
|---|---|---|---:|
| exp_numeric_relation_fusion | B3 exposed180, 60 per main dataset | T_MATCH, REMOTE_ID, REMOTE_LINK, LOCAL_ID, LOCAL_LINK; TPV_REF/B3_G_REF are reference-only | 1800 |
| exp_numeric_encoding_robustness | fixed hash90, 30 per main dataset | T_MATCH/REMOTE_ID/LOCAL_LINK × SCIENTIFIC/UNIT_EQUIVALENT/REPEAT | 1620 |
| exp_locked_fusion_generalization | eval480, exposed test360, presealed fresh≤90 | TPV_REF, B3_G_REF, T_MATCH, REMOTE_ID, LOCAL_LINK | 9300 |

Two frozen local models. Actual compatible requests reuse original results; repeated generation has replicate=1 and must not reuse native. B original answers come from A. C remains separately closed. Qualification uses primary development cases, explicitly superseding early RE2 smoke-roster guidance for this RQ.

Budget: 12774 new including three ≤18call/600sec logicalsmokes, shared major-line hard40000; historical expected21469 is checked against actual SQLite entries, not blindly assumed. Eight pinned physical-core CPU workers maximum, concurrency36, bounded preparation, no attention. Runtime canonical local YAML and8192 adapter unchanged.

Primary8 Holm: LL−REMOTE_ID/T_MATCH/B3_G_REF/TPV_REF ×2models. Secondary6: proximity, link, interaction ×2models. Pratt/dz, noCI; event-group sensitivities; case is the unit. Model failures retained; infra common-case exclusion and missingness sensitivity, no5% gate. Root/fault information evaluator-private. Single model outputs may have fewer than5candidates under existing scorer; no post-hoc answer padding.

Expansion recommendation (not authorization): Qwen macro LL−TPV≥.03, LL−T_MATCH>0, every primary-dataset drop≤.03, Gemma macro drop≤.03, both node subgroup drop≤.05 with ≥20complete nodepairs each; insufficient subgroup is not pass. No alternate champion or per-case oracle.

Numerical whitelist begins with source-attested inherited exact metric definitions. Unknown/counter/state observations remain accurately labeled means/readings. Future qualification must quantify graphical applicability before interpretation. Correct no-op transformations reuse and report original answers; renderer bugs are never reclassified as capacity failures.

## CPU qualification repair, 2026-09-28

Real-case regression exposed inherited `k/M/G` mean strings that Decimal did not accept. RQ37 now expands the parent's decimal display suffixes exactly (1.1k=1100); this does not recover unreported precision or change original M text. Invalid/nonfinite values remain unavailable, not zero.

The inherited seven-key semantic registry did not cover the OTel metric names in the real qualification inputs. RQ37 adds an exact-key, source-attested local overlay for memory/filesystem gauges and memory ratios, verified against [OpenTelemetry kubeletstats v0.110.0 metadata](https://raw.githubusercontent.com/open-telemetry/opentelemetry-collector-contrib/v0.110.0/receiver/kubeletstatsreceiver/metadata.yaml). No fuzzy aliases, dataset routing, unit inference from `rrt`/`mrt`, altered selections, or changes to old RQs. Consequently genuine bar/convertible-unit coverage can differ by case; unknown AIOPS quantities remain labeled readings and nonapplicable unit interventions reuse the native request. Report applicability rather than claiming every case has a unit intervention or continuous bar chart. Repairs precede all RQ37 model calls; failed CPU registration/logs are archived before the new contract is registered. User now authorizes CPU, A/B smoke, then A→B formal if qualified; C remains separately closed.

Three static reviews and deferred qualification status are recorded in [static review](../../../docs/issues/RQ3_7_static_review.md). No CPU regression, actual rendering or model execution is authorized by this implementation-only delivery.

## DD-RQ37-1: Remove redundant generation, preserve necessary comparisons

**Date:** 2026-09-28. **Status:** adopted; supersedes the initial A eight-arm generation/fallback allowance before any registration or run.

**Context/evidence.** The user authorizes removing highly overlapping experiments. RQ1.1 H already tested redundant image+text; Tournament R16 and RQ3.6 B3 tested entity binding. These are not new research questions. B3_T_REF has no independent registered contrast. The numeric proximity×ownership factorial and exact numeric-equivalence robustness remain unseparated in completed history. See plan §2 for the report/source index.

**Decision.** A has five generation arms and two reference-only imports. Delete B3_T_REF as an experimental target; retain its saved public input for anchor consistency only. TPV_REF/B3_G_REF have no generation fallback in A, nor on the same development cases in C. Missing/incompatible references receive terminal reference_unavailable with no score, no new call and no automatic retry. Older artifacts are untouched. No screenshots, generic H rerun, extra selector, resolution sweep or binding-label-only arm is added.

**Alternatives rejected.** Deleting T_MATCH or one factorial cell would remove the same-content control or confound the two factors. Reusing historical REPEAT as current robustness noise would change the request being controlled. Those conditions remain. C outside development180 may require genuinely missing baselines, but is still separately closed.

**Consequences.** A maximum new calls1800, A+B3420, all stages+smokes12774 (old13854); same40000 shared hard ceiling. No claim of1080 actual saved calls if old references would have reused anyway. Five-arm A core keeps its common complete cases; each historical contrast intersects this set with available old scores. Missing comparisons stay in the eight-slot Holm family, with no zero-score imputation. Expansion uses paired macro deltas, not unmatched summary subtraction; insufficient evidence cannot pass. New registration identity v2_pruned, static-only status; CPU/GPU qualification remains unrun.

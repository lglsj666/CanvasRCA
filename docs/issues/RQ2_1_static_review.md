# RQ2.1 implementation and pre-smoke review

Date: 2026-09-07; density amendment reviewed 2026-09-08. **Delivery boundary: stop before smoke.**

The code is implemented and the focused static/CPU reviews are documented here.
This is not a live-model qualification or a performance finding. Both
`execution_enabled` and `smoke_authorized` remain false. No RQ2.1 model calls,
GPU server, champions, training or formal experiments have been started.

All future execution is local: Qwen3.8 and Gemma are served sequentially by
local vLLM. Its HTTP interface is an on-machine connection, not a paid cloud
model service. The SQLite call register records completed requests and attempts
for resume, deduplication and the 39,999-call cap; it is not a billing ledger.

## What is implemented

The complete registration is in
[RQ2.1 experiments](../../RQs/RQ2_1/descriptions/RQ2_1_experiments.md).

| Stage | Changes | Fixed controls |
|---|---|---|
| Original bridges | Reference old RQ1.1 T/V, no new calls | Original records remain untouched |
| Evidence selection | Eight policies, each as Text and Vision | Parent display projection, S0 encoding, D0 placement, common instructions |
| Silhouette encoding | Ten new encodings, one internal-density control, plus reusable S0 | Selected facts, card membership and D0 placement |
| Canvas composition | Ten new compositions plus reusable D0 | Selected facts and chosen internal encoding |
| Anchor cube | All eight P0/P* × S0/S* × D0/D* states | Four existing states reused; only missing requests added |

P means the selection policy, S the encoding inside a card, and D the placement
and raster resolution of complete cards. A star means the winner chosen on the
registered selection subset, not a globally optimal dashboard. Every candidate,
including poor and infeasible designs, remains an experimental condition.

There is no QA, multi-stage RCA, Composer training or automatic RQ3 launch.
The maximum is 39,360 formal calls and 39,999 total initiated calls, including
smoke and retries. Exactly equal complete inputs reuse the same-model result
while retaining separate logical-arm records. No cross-model result reuse.

The same RQ480 is used: 100 cases each from AegisLab, AIOPS-2022 and AIOPS-2025,
and 90 each from RE2-OB/TT. Event/window-connected groups are not split. Thirty
cases from each primary dataset choose champions; the other 210 primary and
180 RE2 cases cannot choose or revise a winner. This is repeated-exposed
evaluation, not a new untouched test set.

## Six separately focused reviews

These are six different checklists and source inspections, not six executions
of the same test or claims that six external reviewers approved the code.

| Review | Inspection and regression evidence | Result |
|---|---|---|
| Logic: scientific controls | Original request/score bridge; explicit calibration; grouped selection; both-model macro champion and veto; request adapter; formal/cumulative budgets; paired masks and Holm families | No remaining identified blocker in checked scope |
| Logic: native tools/data | Original versus adapted sigma, trace and Drain components on identical safe telemetry; BARO signed maximum; full CPU-side universe; exact source-event bindings; explicit native fill; real selection differences | No shared-sort or renamed-input fallback |
| Logic: representation/interactions | Fixed seven-card membership; treatment-specific encoding and whole-card composition; same selected inventory; calibration pixel mask; all eight cube states; encoding-specific feasibility | No hidden card deletion; incomplete carriers blocked |
| Code: schema/cache | Numeric IDs and inverse scoring; NaN/constants/signed values; public relative analysis split; source and packet checksums; manifest/request identity; local checkpoint metadata; model-specific request keys | Covered by CPU tests and real-case materialization |
| Code: renderer/attention | Actual PNG inspection; glyph-based wrapping and row height; exact pixel comparison; disjoint card layout; native visual-token geometry; area-overlap mass conservation; text token normalization | CPU checks passed; live extraction still requires smoke |
| Code: operations/recovery | Local-only endpoint; sequential models; bounded queues; SDK hidden retries disabled; scope/global attempt caps; partial stream persistence; durable raw response; terminal/SQL reconciliation; writer drain and process lock | Crash/recovery tests passed without extra fake requests |

Fixes made during review include:

- Unknown candidate IDs now follow the inherited whole-ranking failure rule.
- Same-selection V−T comparisons have a distinct paired mechanism family.
- Full input artifacts are saved **before** a model request, so a timeout does
  not leave only a response fragment without its corresponding prompt.
- A crash between terminal-file persistence and SQL update is reconciled
  before aliases are scheduled, avoiding an ordering-dependent duplicate call.
- Native SDK retries cannot bypass the explicit initiated-call counter.
- Renderer text-row height uses actual wrapping/glyph measurements.
- A failure to fit S0 no longer prevents another encoding from trying the
  same complete content. A CPU-only intermediate image is not a valid input:
  every flagged card must actually be redrawn before it can reach the Solver.

## Density amendment — 2026-09-08

`S_DENSITY_COMPACT` adds one condition versus reusable S0, not a fourth
experiment. It joins the existing silhouette comparison/champion family.
Formal 39,360 + smoke 54 + repair reserve 585 = the unchanged 39,999 ceiling.

The new renderer tightens only eligible internal background gaps between
complete metric mini-panels and text rows. Plot axes, glyph rasters, labels,
facts, card footprints, connected topology geometry and prompt stay unchanged.
Source-strip translations reconstruct the complete original card interior
byte-for-byte; freed space stays neutral. This is local packing density,
not extra evidence or more facts per full-canvas pixel. Some regions can be
unchanged; their no-op is reported instead of fabricating an intervention.

CPU review covers the original 42 tests plus two new density tests, including
determinism, reversible pixel packing, same prompts/facts/outer boxes, unchanged
header/G plot, incomplete-carrier rejection and the density winner's paths
through all registered compositions. Nine existing primary selection cases
were additionally checked with P0 and P_COVERAGE: 17 drawable inputs all
produce a real pixel change with reversible content preservation; one existing
P_COVERAGE/S0 infeasibility remains infeasible, without deleting evidence.
Three P0 images (one per primary dataset) were manually inspected; no new
clipping or glyph/axis distortion was found in those examples.

Six CPU-only native tokenizer/processor checks (three images × two models)
passed: maximum input was 5,453 tokens for Qwen and 4,498 for Gemma, with the
unchanged 8,192 output reservation. No model weights or inference were run.
All six focused reviews received an explicit incremental amendment; earlier
review records and unchanged-input evidence are retained. Strict lint passed
for the functional modules/new renderer, critical-error lint and syntax checks
passed for the entire RQ-local source. Historical inherited typing style was
not rewritten. Functional source totals 5,986 lines, below 6,000. The smoke
gate now has only `execution_disabled` as a blocker; no smoke was launched.

Review artifacts: [incremental summary](../../RQs/RQ2_1/results/qualification/density_review/review_summary.json),
[CPU tests](../../RQs/RQ2_1/results/qualification/density_review/cpu_tests.json),
[native input checks](../../RQs/RQ2_1/results/qualification/density_review/token_preflight.json).

The review caught and fixed background detection at framed-card corners:
the packer now uses the dominant sampled background, not corner color alone.
No model calls, dataset regeneration or model-recipe edits occurred. Original
bridge and earlier design artifacts remain in place. Detailed new evidence is
under `RQs/RQ2_1/results/qualification/density_review/`.

## Reproducible pre-amendment evidence

The following table records the 2026-09-07 checked scope; density additions
are reported above and do not retroactively change these historical counts.

| Check | Scope/result |
|---|---|
| CPU regression | 42 tests: registration, native differential tests, rendering contracts, statistics, persistence and recovery |
| Original bridge scoring | 1,920 T/V records; MRR, AC@1/3/5 and AVG@3/5 all unchanged; original record checksums verified |
| Inheritance | Initial eight-file renderer copy verified; parent snapshot remains unchanged; preserved primitive/native-source hashes checked |
| Real-case gallery | Nine hash-selected primary cases × 46 logical conditions: 331 PNG-bearing targets, 72 Text targets and 11 explicitly infeasible targets, including aliases |
| Input length | 54 CPU tokenizer/processor checks; Qwen maximum 14,452, Gemma maximum 15,835 input tokens; all retain 8,192 output tokens |
| Visual geometry | 36 image inputs checked against native visual-token counts; separate overlap tests verify attention-mass conservation |
| Core organization | Five functional modules plus `__init__.py`; 5,849 source lines under the project's nonblank/non-comment count; RQ-local renderer exception |
| Shell organization | Three shell files, 66 lines total; syntax checked |
| Static code | All new modules and renderer additions checked with Ruff; all 33 Python files compiled without executing models |

The exact machine reports and gallery counts are under
[qualification](../../RQs/RQ2_1/results/qualification/). Key records:

- [CPU regression log](../../RQs/RQ2_1/results/qualification/cpu_tests.log)
- [Static checks](../../RQs/RQ2_1/results/qualification/static_checks.json)
- [Bridge scores](../../RQs/RQ2_1/results/qualification/bridge_scorer_differential.json)
- [Gallery inventory](../../RQs/RQ2_1/results/qualification/gallery_summary.json)
- [Real-case pixel/fact checks](../../RQs/RQ2_1/results/qualification/gallery_contract_check.json)
- [Native input-token and geometry checks](../../RQs/RQ2_1/results/qualification/token_preflight.json)
- [Visual inspection index](../../RQs/RQ2_1/results/qualification/visual_review.json)
- [Complete Text input preview](../../RQs/RQ2_1/results/qualification/review_prompts/INC-91CC9D691CA8__T.md)
- [Complete Vision input preview](../../RQs/RQ2_1/results/qualification/review_prompts/INC-91CC9D691CA8__V.md)

These generated files are intentionally ignored by Git. The source-level review
record remains in this document. Re-run CPU qualification locally if generated
evidence is absent after a code-only clone; never manufacture a passed record.

## What the visual review does and does not establish

Nine distinct real cases were inspected across baseline lines, time bars,
compatible overlays, table/heatmap/log-matrix encodings, directed graphs and
different composition families. Additional examples cover paired trace bars,
log matrices, the small-resolution condition and a recovered alternative
encoding: 13 inspected examples across nine distinct cases. The full gallery also gets
automated selected-fact/card/pixel checks; it was not all manually inspected.

No newly identified clipping/overlap defect remains in the inspected samples.
Small-scale and topology-centered treatments can still make some cards harder
to read; changing readability is an experimental variable, not a promise that
every design is equally legible. The user's upcoming review remains important.

Some selected complete log rows genuinely exceed the fixed S0 footprint.
They are recorded as **design infeasible**, not silently shortened or counted
as infrastructure errors. Other encodings get their own feasibility check.
The gallery's sampled frequency is not an estimate of the full study's error
rate. Formal whole-case infrastructure exclusion and parse-rate rules are
separate and cannot be assessed before inference.

Attention analysis is diagnostic: area-normalized visual density and
token-normalized text density do not establish causal reasoning. Public reason
matching is explicitly a literal entity/edge audit, not unrestricted semantic
entailment or access to hidden model reasoning. No attention or quality numbers
are fabricated for this CPU-only delivery.

## Scope, dependencies and remaining user boundary

The preserved [RQ2 retirement audit](../../RQs/RQ2/findings/exp_retirement_audit_findings.md)
records the old study's input-collapse and bridge problems. Its code, derived
findings and report dependencies remain; only owned generated artifacts were
removed under the approved inventory. RQ1.1, RQ480, the full processed corpus,
models, original effective inference/scorer configs and RQ3 remain protected.

Runtime dependencies are local. BARO's original license and provenance are
retained. The supplied SIRCL snapshot lacks a license; local copying is expressly
user-authorized, but permission for public redistribution is not verified.
Original vendored sources were not reformatted merely to remove legacy style
warnings or unused imports.

After the joint review, a separate user instruction is required to enable
smoke. Each experiment gets one logical 18-call/600-second smoke across both
sequential local models. Its complete inputs, PNGs, conversations, responses,
partial outputs and accounting must then be inspected. CPU checks do not
prove that unexecuted model×arm combinations passed live qualification.

**No smoke or full run is launched by this handoff.**

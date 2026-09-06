# Consolidated design-decision register

This is the compact authority for project decisions. It preserves adopted,
superseded, rejected, and reverted routes, but merges repeated decisions into
one entry. Git history and the consolidated devlog retain additional chronology.
An earlier result is not rehabilitated merely because its protocol is mentioned
here. The latest cross-cutting authority is `Codex.md`; RQ-specific details live
under `RQs/<rq>/descriptions/`.

Two unrelated historical decisions were both numbered DD-92. They are named
DD-92a (RQ2 restart) and DD-92b (Qwen3.8) here so old references remain
interpretable.

## Foundation and historical RQ1 lineage

- **DD-13a — 2026-07-27 — adopted.** Keep plain top-K telemetry selection as
  the default and coverage-first only as an ablation. The paired bake-off was
  model-dependent and unresolved, so complexity was not promoted.

- **DD-43 — 2026-08-09 — adopted, deployment clause amended by DD-118.** Shared
  Python belongs in `src/`, shell launchers in `scripts/`, and unified inference,
  segmentation, and scoring contracts remain extensible bases. Each RQ owns its
  descriptions/configs/findings/scripts/src/results structure and a compact
  five-module source package. The original Nibi deployment instructions are now
  historical because successor execution is local only.

- **DD-52 — 2026-08-05 — fully superseded by DD-92a.** The first RQ2 plan used
  separate 60/150/90/60 development, independent, downstream, and buffer pools.
  It was abandoned when RQ2 was restarted on the RQ1.1 empirical cases; its
  rosters and artifacts have no current authority.

- **DD-83 — 2026-08-10 — historical RQ1 authority.** Typed Q&A selectors had
  to name visible public records and fields; a label-blind host performed the
  binding. This replaced opaque-ID memorization and prevented the model from
  receiving hidden answers. The interface reached v22 but is not an active
  RQ1.1/RQ2 protocol after DD-135.

- **DD-85 — 2026-08-11 — historical RQ1 authority.** RQ1 owned its renderer and
  distinguished natural text, flat JSONL, real dashboards, pixel-text, strict
  A+B hybrid, and routed visual/text representations. It also corrected Q&A
  representation equality. Later RQs copy an RQ-local renderer; none may treat
  a text screenshot as a real dashboard.

- **DD-86 — 2026-08-15 — historical program, outcomes later invalidated by
  DD-135 where reused.** RQ1 registered seven experiments: Q9, cross-region,
  typed two-stage, direct RCA, matched RCA, visual counterfactual RCA, and
  ledger handoff over 469 cases and both models. This preserved the distinction
  between perception, handoff, actual RCA, and image intervention.

- **DD-87 — 2026-08-10 — extended by DD-99.** Same-prefill visual attention was
  recorded during the original call without replay or logit changes. DD-99
  extended this to image and text keys and geometry-correct diagnostics;
  attention remains correlational.

- **DD-88 — 2026-08-11 — superseded by DD-97.** The first bounded-smoke rule
  allowed 18 calls and 600 seconds per model. It was rolled back because it made
  a nominal two-model smoke twice as large as intended. DD-97 restores one
  aggregate budget; historical smoke statuses do not change.

- **DD-90 — 2026-08-11 — historical, unqualified successor.** Two-stage RCA
  Stage 1 selected visible record keys/bins and the host copied exact public
  facts. This removed fragile transcription and opaque identifiers, but the
  two-stage route was left behind by the one-stage RQ1.1 scope.

- **DD-91 — 2026-08-15 — runtime provenance, cluster execution superseded by
  DD-118.** The then-current Nibi recipe raised context to 40,960 and recorded
  model-specific processing, concurrency, and compatibility metadata. It solved
  Gemma input-length failures without changing prompts. Current executable
  values come only from unified configs/Codex; this entry is not a launcher.

- **DD-92b — 2026-08-17 — adopted model lineage.** Replace active Qwen3.6 with
  official unquantized BF16 Qwen3.8-27B, disable thinking/preserved thinking,
  and retain scientific inputs and scorer. Historical Qwen3.6 results remain
  history only; current experiments use Qwen3.8 and Gemma.

- **DD-93 — 2026-08-20 — historical correctness repair.** Check
  counterfactual eligibility before resolving targeted/placebo images; write
  zero-call terminal records for ineligible cases. This prevented an optional
  missing image from aborting valid preparation.

- **DD-94 — 2026-08-20 — adopted.** Runtime-freeze hashes are provenance, not
  validity gates. Reuse requires a self-consistent record hash/call key and the
  correct model/experiment/arm identity. This rolled back stricter freeze
  matching in DD-91–93; it never permits mismatched prompts, evidence, model, or
  scorer to be merged.

## RQ1.1 lineage

- **DD-95 — 2026-08-26 — partly superseded by DD-98/99/102.** RQ1.1 began as a
  one-preparation successor copied from RQ1, with numeric case-local IDs,
  Qwen3.8/Gemma, direct QA, direct RCA, and three-step RCA. It initially removed
  attention and used narrower candidates. DD-98 expanded candidates, DD-99
  restored attention, and DD-102 abandoned active multi-stage RCA.

- **DD-96 — 2026-08-26 — deployment intent retained, execution narrowed by
  DD-118.** Nibi and local YAML profiles represented one scientific recipe and
  differed only in deployment paths/VRAM policy. Successor work now runs
  locally; the archived Nibi profile remains interpretable, not executable.

- **DD-97 — 2026-08-26 — adopted.** Each experiment has one logical dual-model
  smoke: at most 18 initiated calls and 600 seconds total, models sequential.
  Splitting a smoke may not reset either cap.

- **DD-98 — 2026-08-27 — adopted, artifacts reset by DD-135.** Candidates came
  from the complete label-blind service/pod/node/telemetry/graph entity universe.
  This repaired candidate omissions without consulting labels.

- **DD-99 — 2026-08-27 — adopted instrumentation contract.** Record same-call
  image/text attention, prompt-query and answer-field generation views, actual
  processor geometry, raw mass, per-pixel density/lift, entropy, Gini, and
  positional-sink diagnostics. There is no precommitted positive visual
  direction; attention alone cannot prove reasoning or causality.

- **DD-100 → DD-101 → DD-102 — 2026-08-27 — authorization/reversal chain.**
  DD-100 froze a smoke-qualified attention-enabled RQ1.1. DD-101 paused it and
  cleared results after team redesign. DD-102 reopened implementation as a
  narrower one-stage paper: Direct-RCA, Direct-QA, one dashboard maximum,
  token/attention/perception analysis, and `multi_stage_rca` retained only as
  abandoned future-work code. This was a scientific scope reduction.

- **DD-103 — 2026-08-27 — adopted method parent.** Adapt selected SIRCL*
  MET-Z/TRC-L/LOG-R, M→R→L→G, U-BASE, and VERIFY, but replace private injection
  time with a public trace-derived split and deterministic fallbacks. Preserve
  the reference byte-for-byte and never import it at runtime.

- **DD-104 — 2026-08-27 — adopted.** Separate representation-neutral task/RCA
  semantics from representation decoding. Text gets no dashboard navigation;
  real images get a field dictionary; pixel-text gets its own explanation;
  strict A+B remains intact.

- **DD-105 → DD-106 → DD-107 — 2026-08-27 — versioned repair chain, artifacts
  later invalidated by DD-135.** DD-105 authorized the single-stage successor.
  DD-106 bounded long Denum templates equally across representations. DD-107
  made attention capture preemption-safe and fail-closed. Each byte successor
  displaced only the prior execution authority, not its historical record.

- **DD-108 → DD-109 → DD-110 → DD-111 — 2026-08-27 — scheduler chain.**
  Separate four CPU preparation/writer workers from model-request depth, resume
  content-addressed work, then deepen/sustain the request queue so attention
  postprocessing cannot starve vLLM. Prompts, inputs, scores, and recipes stayed
  fixed; these were operational changes.

- **DD-112 — 2026-08-29 — historical QA analysis.** Separate missing-data
  answers from positive cross-region perception so high-level QA does not
  confound model failure with facts that were unavailable.

- **DD-113 — 2026-08-29 — historical QA extension.** Add label-blind positive,
  answerable instances balanced over each ordered M/R/L/G path. Existing
  questions remained unchanged and selection ignored model responses.

- **DD-114 → DD-115 — 2026-08-29 — scoring refinement.** DD-114 preserved
  strict/semantic scores and exposed region-specific visual failures. DD-115
  made the final estimand visibility-aware: exclude unprinted fields/truncated
  labels and use display-precision gold for visual arms while retaining raw
  records. This scorer correction did not excuse evidence inequality.

- **DD-116 — 2026-08-29 — historical completed extension.** Extend L4 to 96
  visibility-clean, path-balanced cases, four per ordered four-region path. Its
  old numeric outcomes ceased to be current after DD-135.

## RQ2, Composer, and current data lineage

- **DD-117 — 2026-09-01 — adopted future-training principle.** Composer
  training must improve RCA and expose action-level credit. SFT teaches legal
  typed tool use; later RL may optimize card selection/composition only through
  exact anchor states, paired outcomes, interactions, and residuals.

- **DD-118 — 2026-09-01 — adopted and current.** All successor CanvasRCA work
  runs locally as ordinary background processes. The `_nibi` worktree name may
  remain, but no new Slurm job is submitted. The cluster profile is archival.

- **DD-119 — 2026-09-01 — adopted, prompt clause amended by DD-137.** A local
  Qwen3.5-9B Composer emits typed dashboard programs; frozen 27B VLM actors
  render/solve them. No free-form pixels, Solver training, or outcome leakage.
  RQ2 later aligned its RCA method to SIRCL* while retaining local ownership.

- **DD-92a — 2026-09-01 — adopted clean restart; counts corrected by DD-139.**
  Delete predecessor RQ2 implementation/roster authority and reuse RQ1.1's
  headline cases, selected label-blindly. The pre-V3 289/139 count was a symptom
  of the lossy corpus and is not current authority; V3 uses all 300 headline
  cases as 60 development, 150 independent, and 90 downstream lock.
  RE2 remains saturated reference only. This reverses DD-52 because holding the
  incident population fixed improves paired interpretation.

- **DD-121 — 2026-09-01 — adopted cleanup.** Remove copied RQ1.1 experiment
  protocol from clean RQ2. Reuse unified client/scorer/runtime, but keep RQ2
  prompt, design logic, renderer, configs, and claims RQ2-local.

- **DD-122 — 2026-09-01 — adopted design language.** The Composer selects
  modular `EvidenceCardV1` objects, converts each to exactly one fact-equivalent
  `SilhouetteV1`, and packs non-overlapping silhouettes into a finite grid.
  Selection, encoding, placement, density, and clipping remain auditable.

- **DD-123 — 2026-09-01 — adopted experiment design.** Use a staged constrained
  D-optimal/mixed design with continuous resolution/spacing anchors, development
  selection, frozen independent contrasts, content twins, and transfer controls,
  not an infeasible Cartesian grid.

- **DD-124 — 2026-09-02 — adopted renderer direction.** Replace one-fact-per-
  panel sparse defaults with human-readable composite metric, trace, log, and
  topology cards. Keep sparse rendering only as a negative density control.

- **DD-125 — 2026-09-02 — adopted.** Separate fixed-fact overlay encoding from
  expanded content. FULL has top-12 metrics; `DENSE_M24` has top-24 and equal-
  fact Dense Text/Canvas twins. Dense-versus-normal is not equal-information.

- **DD-126 — 2026-09-02 — adopted.** Grid occupancy and readable internal
  density differ. Raise typography/mark size, reduce avoidable whitespace and
  overlap, and show truthful sparse evidence rather than fill space with noise.

- **DD-127 — 2026-09-02 — adopted.** Every real dashboard receives a complete,
  non-incident visual-field dictionary explaining IDs, labels, time, units,
  abbreviations, missingness, topology direction, and encodings. Text does not.

- **DD-128 → DD-129 — 2026-09-02 — authorization then validity repair.** DD-128
  authorized v7 after static/smoke. D022 overlay could not fit its generic
  silhouette, so DD-129 archived pre-fix calls and required the existing 4×4
  overlay footprint. Rerun was necessary because model-visible pixels were wrong.

- **DD-130 — 2026-09-02 — adopted operations.** Use four core-pinned
  materializers, bounded request/attention queues, and batch attention transfers
  to overlap CPU and GPU work. This cannot change inputs or classify outcomes.

- **DD-131 → DD-132 — 2026-09-02 — repair then abandonment.** DD-131 proposed
  regenerating packed-QA units missing answer-token attention. DD-132 removed
  packed QA from active RQ2 after RQ1.1 QA, including root-connected topology,
  was an unstable RCA proxy. QA code/artifacts remain audit-only; RQ2 is RCA-only.

- **DD-133 — 2026-09-03 — adopted, qualification deferred.** Register an
  RQ1.1-owned one-stage counterfactual RCA test with factual, targeted identity
  transplant, matched placebo, and neutral images. It never imports RQ2. CVI
  measures directed image sensitivity, not correctness by itself.

- **DD-134 — 2026-09-03 — superseded by DD-135 for generated artifacts.** A
  native render exposed trace-text overlap and permissive clipping/packing
  audits. The lossless successor added measured fitting and deterministic
  backtracking, invalidating earlier D* and partial runs.

- **DD-135 — 2026-09-03 — adopted; controls old-result status.** A V2 schema
  audit found material service/pod/node/process evidence loss. All generated
  RQ1.1/RQ2 results, preparations, renders, attention, smokes, analyses, and
  processed cases were removed; reports/source remain historical only. This
  supersedes every old resume/formal authority. Old output may not be rehashed
  or cited as current evidence.

- **DD-136 — 2026-09-04 — adopted current data contract; materialized.** Vendor selected
  SIRCL raw loaders under `src/unified_scripts/sircl_data/`, verify source hashes,
  and make `CanvasRCAProcessedPublicCaseV3` the only preparation schema. Preserve
  telemetry columns, graph attributes, and node/pod mappings; convert clocks to
  relative time and isolate labels, source identity, fault type, and absolute
  injection time. Two cases per dataset matched the reference and Parquet round
  trip. The complete raw indexes were then converted to 2,302 per-case records
  (1,422/300/400/90/90), and only afterward was the exact frozen RQ480 selected
  and validated. The old direct-to-subset and 469-case paths are not active.

- **DD-137 — 2026-09-04 — adopted.** RQ2 owns a local minimal adaptation of the
  RQ1.1 SIRCL* prompt: change only fixed metric-count wording and explain that
  card/design choices are controls. Preserve M→R→L→G, MET-Z/TRC-L/LOG-R,
  INITIAL→VERIFY→REVISE, candidates, and top-five schema. Dashboard grammar is
  visual-only. This removes a prompt-method confound.

- **DD-138 — 2026-09-04 — adopted; static/CPU qualified.** Add an
  equal-fact compact typed-text control and non-invasive performance telemetry
  to V3 successors. RQ1.1 adds `C` beside its 16 factorial cells and S/H; RQ2
  transfer adds compact controls at FULL, C*, and dense content. Compact rows
  are `[region, field, entity_ids, relative_bins, unit, payload]`, omit private
  fact IDs, and must round-trip to the canonical semantic inventory. C−T
  measures nonvisual structure/prose compression; V−C or Canvas−Compact measures
  spatial organization after that control.

  The same call records client-observed TTFT, receiver E2E, decode duration,
  TPOT, output-token rate, and stream-chunk timing. A background monitor records
  throughput/goodput, sampled utilization, peak VRAM/KV cache, utilization-
  weighted GPU-seconds, and sampled energy. Preparation/materialization records
  renderer time. Prefill remains null because client timing cannot separate it
  from queue/transport; chunk timing is an ITL proxy. Monitoring failures never
  alter inference. Hardware latency/energy is comparable only within a matched
  runtime; tokens remain portable. The vLLM recipe, SIRCL prompts, renderer
  facts, models, scorer, and candidates are unchanged. RQ1.1's complete static
  qualification, RQ2's 34 CPU tests, critical lint, syntax, YAML, line-limit,
  and diff-integrity checks passed. No smoke/formal run is authorized by this
  decision.

- **DD-139 — 2026-09-04 — adopted; static/CPU qualified.** RQ480 means 480
  already-processed per-case incidents. Canonical construction is therefore
  strictly `complete raw tables/directories → complete V3 per-case corpus →
  frozen RQ480 selection`; neither a raw-data sample nor a roster-directed
  partial conversion may stand in for the corpus. The selected source manifest
  remains the historical seed-42 100/100/100/90/90 identity set with SHA256
  `6dbfcc80fb4a875d2f53a7085b703d099e8210b472c5312e5da8a07ee408df48`.

  RQ1.1 Direct-QA now separates perception difficulty `P1…P4` (the number of
  distinct M/R/L/G regions that must be read) from reasoning difficulty
  `R1…R3` (independent lookup, dependent entity bridge, or regional comparison
  and aggregation). The registry contains 12/36/72/72 eligible template slots
  on a complete fixture. A response-blind schedule balances requested
  `path × reasoning` cells over RQ480; a case may fall back only to an eligible
  public-fact program, with the fallback recorded. Any `missing`, `none`,
  `nan`, `null`, `n/a`, `na`, `unavailable`, empty, unprinted, or unsupported
  gold value makes a question ineligible before inference. Both models and all
  representations receive the same selected question for a case/P level.

- **DD-140 — 2026-09-04 — adopted; operational qualification only.** Supersede
  DD-108–DD-111's four-worker preparation setting with eight workers pinned to
  eight distinct physical CPU cores. Keep model-request concurrency separate.
  Replace repeated per-entity regex scans and DataFrame row iteration with one
  compiled alternation and column-array iteration only after exact graph, JSON,
  and image-byte equality checks. Preparation now validates and resumes every
  atomically persisted case; formal resume binds both public evidence/image
  bytes and evaluator-private labels, and requires a complete conversation
  artifact. The raw processor checks a completed V3 public/private pair before
  loading the source case, so restart does not repeat expensive cloudbed reads.
  A balanced 20-case test was interrupted after three persisted cases and then
  resumed by skipping exactly those three and completing the other seventeen.
  RQ1.1 projected to 1.8–2.5 hours for RQ480; RQ2 projected below one hour. A
  full 975 MB, 20-case hash verification took 3.39 seconds (5.89 cases/s), so a
  similarly sized 2,000-case restart is about 5.7 minutes. These changes alter
  only scheduling, persistence, and verification—not evidence or experiment
  semantics. RQ1.1 also now honors the explicit local vLLM profile selector;
  the previous code silently read the inactive Nibi deployment projection.

- **DD-141 — 2026-09-04 — adopted; implementation-quality boundary.** Raise
  the five-module per-RQ ceiling from 5,000 to 6,000 nonblank/non-comment lines
  for both RQ1.1 and RQ2. The larger ceiling is headroom, not a target and not
  permission to hide duplicated or unfinished behavior. A source/registry/
  dispatch audit found no TODO/FIXME marker, empty function, ellipsis-only
  body, `NotImplementedError` skeleton, synthetic active path, or registered
  experiment without an executable prepare→materialize→run→score→verify path.
  Static regression checks now reject such implementation skeletons. RQ1.1's
  abandoned multi-stage code, RQ2's abandoned packed-QA code, and RQ2's
  data-only Composer trace exporter remain deliberately non-active provenance,
  not claimed formal endpoints. Removing unused RQ2 helpers/imports changes no
  prompt, evidence, renderer output, scorer, or model configuration.

  The in-progress RQ1.1 preparation was stopped after 186 atomically complete
  public/private pairs. Its only contract drift was the newly edited
  `tests.py`; the transition preserves both old and new contract hashes and
  explicitly records that no prepared case byte changed. Runtime, renderer,
  evidence, prompt, scorer, and configuration hashes remained identical, so
  the 186 cases remain valid and resumable rather than requiring regeneration.

- **DD-142 — 2026-09-05 — adopted; V3 formal execution authorized.** The
  canonical 480-case RQ1.1 preparation and all four RQ2 preparations completed
  with valid semantic index hashes, complete public/private inventories, zero
  missing paths, and zero temporary/partial artifacts. Full-corpus RQ1.1 QA
  eligibility, answer visibility, path/reasoning balance, counterfactual
  uniqueness, anonymization, and leakage audits passed. Current RQ1.1 and RQ2
  static suites passed after preparation.

  Six bounded dual-model smokes then completed 96 total requests: RQ1.1 Direct
  RCA and Direct QA used 18 each; RQ2 equal-fact design, content-budget twins,
  downstream transfer, and tool×representation used 8/18/18/16. Every request
  produced a terminal trajectory, every aggregate parse rate was 1.0, and
  there was no infrastructure error or truncation. Post-hoc verifiers passed,
  and completed prompts, conversations, raw responses, attention/performance
  accounting, and persistence were manually inspected. Therefore the RQ1.1
  Direct-RCA/Direct-QA successors and four RCA-only RQ2 successors are frozen
  and authorized for local formal execution. This changes only fail-closed
  execution status; model/runtime recipes, scientific prompts, renderer,
  scorer, rosters, prepared bytes, and active experiment definitions remain
  unchanged. RQ1.1 counterfactual RCA is still deferred until RQ2 completes;
  RQ1.1 multi-stage RCA and RQ2 packed QA remain abandoned.

- **DD-143 — 2026-09-05 — adopted; narrowly supersedes DD-142 for Direct-QA.**
  Full-corpus inspection found that R/G “first displayed record” wording had
  different referents because text/S ordered facts by `fact_id` while the real
  dashboard ordered trace rows and edges by semantic display indices. Fact-set
  parity therefore did not imply ordered-reference parity. Replace R anchors
  with unique visible ExL-p95/rank-score pairs, G anchors with unique visible
  callee endpoints, remove the remaining trace-row order wording, and add
  storage-order-invariance tests. The repair changed 768 of 1,920 case-level QA
  groups and removed 2,645 completed Qwen records from those groups; all 18,240
  completed Direct-RCA records and 4,246 exactly unaffected Qwen QA records were
  preserved. Large evidence/image preparation was not regenerated; only QA
  sidecars and the index changed, producing index SHA256
  `25dd503cb6900267dc267273ee6f8bb6a572ec0a2bed6ba024a7cbd6f4f8994b`.
  Predecessor QA outputs may resume only after exact reproduction of the entire
  visible request and current private score, never by old hash alone. The
  successor dual-model 18-call smoke completed with parse 1.0, no error or
  truncation, complete attention, and verifier passage under contract
  `23e6489cdefe1dfe4592099b7a6d2150472a7afaed576ac214cc006b1c9aa49a`.
  Resume repaired/unrun Direct-QA groups, then continue RQ2; do not rerun RCA.

## Current execution boundary

RQ1.1/RQ2 old numerical findings are historical and invalid under DD-135. The
V3 prepared inputs and successors listed in DD-142 and amended by DD-143 are
the only current formal authority. Direct RCA is complete and remains valid.
Resume repaired Direct QA, then run RQ2 development design selection,
independent design/content evaluation, downstream transfer, and
tool×representation. Reuse the retained evidence/image preparations.

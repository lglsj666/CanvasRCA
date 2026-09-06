# Consolidated CanvasRCA devlog

This file replaces 50 repetitive session logs with a compact chronological
record. It preserves important implementation outcomes, validity changes,
reversals, failures, and next-step boundaries. Former filenames are shown so
Git history can recover full detail. Experimental findings remain in RQ
`findings/` and reports; decisions remain authoritative in
`plans/design_decisions.md`.

## 2026-07-22 to 2026-07-28 — scaffold, bake-off, and renderer diagnosis

- **Initial scaffold and M0/M1 smoke** (`2026-07-22_m0-m1-scaffold-and-smoke.md`).
  Built case→dashboard→VLM→parse→score artifacts using an upstream shim. A real
  Bedrock smoke proved the path ran, but early small samples and renderer defects
  were diagnostic only.

- **Open-VLM bake-off and thinking study**
  (`2026-07-23_open-vlm-bakeoff-and-ci-removal.md`,
  `2026-07-24_qwen-thinking-off-rerun.md`). Self-hosted candidates were compared
  under vLLM; disabling written thinking prevented some budget-filling behavior.
  The apparent model ordering was later weakened because decoding, evidence
  coverage, and renderer inputs were not yet controlled.

- **Bake-off correction and final interpretation**
  (`2026-07-26_bakeoff-correction-and-render-fixes.md`,
  `2026-07-27_bakeoff-results-and-conclusions.md`). Aligned sampling/decoding,
  measured replicate noise, repaired text-budget/selection bugs, and found that
  every tested visual configuration remained below the text baseline. Coverage-
  first selection had no reliable advantage, so plain top-K remained default.
  Claims that “thinking hurts” or one selector wins were explicitly withdrawn.

- **Sparse-series and propagation repair**
  (`2026-07-28_sparse-series-fix-and-propagation-panel.md`). The nearly blank
  metric grid came from timestamp/window/aggregation defects rather than real
  telemetry. Repaired elapsed-time rendering, onset inference, propagation rows,
  label/OCR safety, and topology readability. Visual inspection established
  that dashboard correctness must be checked separately from code execution.

## 2026-07-31 — RQ0, allocation, SFT, and repository organization

- **Causal-integration SFT v1 and v2.1**
  (`2026-07-31_causal-integration-sft-pilot.md`,
  `2026-07-31_causal-integration-sft-v2-1.md`). Development-only LoRA pilots
  trained stably but failed to improve RCA; v1 regressed and v2.1 produced no
  promotion evidence. These inference-v1 outcomes were later archived invalid,
  and the checkpoints were never promoted.

- **Nonredundant modality allocation**
  (`2026-07-31_nonredundant-modality-allocation.md`). Tested putting dense
  temporal/topology facts in images rather than duplicating all of them in text.
  The small exposed-development result was mixed and did not justify a pipeline
  change; it motivated stronger equal-fact representation audits.

- **RQ layout migration** (`2026-07-31_rq-layout-migration.md`). Moved RQ
  descriptions/configs/findings/scripts/source/results under canonical RQ
  directories, retained shared shell utilities, updated hashes/paths, and set
  ignore rules for build/model/test/result artifacts. This was maintenance, not
  a result reinterpretation.

- **RQ0 equal-information confirmation and topology follow-up**
  (`2026-07-31_rq0-equal-information-confirmatory-results.md`,
  `2026-07-31_rq0-followup-grounding-topology-v7.md`). Equalized text/image
  facts and compute, then tested actual/swapped/no-image grounding and a more
  readable edge key. Image evidence often moved rankings but did not reliably
  improve accuracy; readable topology was necessary yet insufficient. These
  historical inference-v1 results were later invalidated and RQ0 was removed.

## 2026-08-03 to 2026-08-05 — rename, early RQ1 mechanisms, inference-v2

- **CanvasRCA rename and shared skills**
  (`2026-08-03_canvasrca-rename-and-codex-skills.md`). Updated active branding,
  project paths, Claude/Codex skill discovery, and repository guidance without
  changing experimental evidence.

- **RQ1b2 answer-hidden development**
  (`2026-08-04_rq1b2-answer-hidden-development.md`). The exposed-only Gemma cell
  passed infrastructure qualification but failed all preregistered promotion
  conditions; Qwen and the independent gate were therefore not opened.

- **RQ1b3 typed/onset ledger** (`2026-08-04_rq1b3-interface-smoke.md`). The first
  interface smoke exposed parsing/grounding defects; a repaired successor passed
  its bounded interface checks, then the 90-case development result failed its
  promotion rule. This stopped the route instead of spending the locked gate.

- **Inference-v2 migration** (`2026-08-05_vllm_inference_v2_migration.md`).
  Versioned separate Qwen/Gemma BF16 recipes, explicit sampling/thinking,
  multimodal processing, xgrammar, context/output limits, and scheduler fields.
  Earlier v1 model-call results were archived invalid; CPU-only renderer/roster
  artifacts were not invalidated merely by that change.

## 2026-08-09 to 2026-08-12 — Nibi refactor and RQ1 restoration

- **Portable refactor and Nibi deployment**
  (`2026-08-09_nibi_refactor_static_handoff.md`,
  `2026-08-09_nibi_deployment_and_rq1_execution.md`). Compact RQ packages and
  unified scripts were statically qualified; cluster environments/models/data
  were staged. Port collisions, array-release anomalies, context overflows, and
  replacement launches were logged as infrastructure, not model quality.

- **Gemma typed Stage-1 diagnosis and repair**
  (`2026-08-10_gemma_typed_stage1_root_cause_and_v7_fix.md`,
  `2026-08-10_rq1_typed_v10_cross_model_qualification.md`). Gemma’s high invalid-
  ledger rate traced to fragile selector binding/format behavior. Visible record
  keys and host binding improved cross-model transfer without exposing answers.
  The repair was qualified locally but did not retroactively validate old runs.

- **Semantic restoration after over-compression**
  (`2026-08-10_rq1_semantic_restoration.md`). Audit found the compact Nibi
  rewrite had changed prompts, renderer, and experiment meaning. All affected
  trajectories were archived invalid; successor code restored the old semantics
  plus explicitly authorized dashboard/runtime changes.

- **RQ1 shard recovery and visual diagnostics**
  (`2026-08-10_rq1_v7_pending_shard_resubmission.md`,
  `2026-08-10_visual_diagnostics_maxseq128_qualification.md`). Resubmitted only
  missing shards and separated scheduler capacity from scientific configuration.
  Added call-free visual diagnostics and found a hidden typed Stage-1 problem by
  reading smoke conversations rather than relying on pass/fail alone.

- **Same-prefill attention, timeout capture, and compact selectors**
  (`2026-08-11_same_prefill_attention_and_timeout_capture.md`). Implemented
  original-call attention sidecars and atomic partial-response checkpoints.
  Inspected long Qwen output, registered a compact selector successor, diagnosed
  binding failure, and handed off an untested repair rather than claiming it
  worked.

- **RQ1 v18 preparation/smoke repair**
  (`2026-08-12_rq1-v18-runtime-repair-and-smoke-launch.md`). Rebuilt shared
  preparation, repaired Q&A representation and execution defects, verified
  hashes/pixels, and submitted bounded model-separated smokes. No full result
  was claimed from preparation or smoke evidence.

## 2026-08-20 — Qwen3.8 and resume semantics

- **Counterfactual resume fix**
  (`2026-08-20_qwen38_counterfactual_resume.md`). The queue failed because it
  looked up targeted/placebo images before checking protocol eligibility.
  Reordered that check, preserved eligible completed records, and represented
  ineligible arms as zero-call terminal artifacts.

## 2026-08-26 to 2026-08-27 — RQ1.1 build, scope change, and operations

- **Unified RQ1.1 refactor**
  (`2026-08-26_rq1_1_unified_representation_refactor.md`). Copied RQ1 before
  editing, introduced one canonical preparation, case-local numeric IDs,
  readable Denum-style log graphs, direct QA/RCA, and an initial ReAct-like
  multi-stage experiment. Static checks passed; no model result was claimed.

- **Attention qualification and later reset**
  (`2026-08-27_rq1_1_multimodal_attention_static_qualification.md`). Added
  same-call text/image attention with processor geometry, per-pixel regional
  density, sink diagnostics, and artifact integrity. Initial qualification was
  later overridden when team redesign cleared results and narrowed the paper.

- **Scheduler qualification**
  (`2026-08-27_rq1_1_scheduler_pipeline_qualification.md`). Separated the four
  CPU workers from request concurrency, raised local serving capacity after
  measured queue behavior, and preserved scientific bytes. Utilization was
  operational evidence only.

- **Single-stage factorial and joint analysis successor**
  (`2026-08-27_rq1_1_single_stage_factorial_joint_analysis.md`). Narrowed RQ1.1
  to one-stage RCA, one image, a 16-cell M/R/L/G factorial plus controls, matched
  L1–L4 perception, token efficiency, explicit-evidence grounding, and attention.
  Multi-stage code was retained but abandoned. SIRCL* analyzers/prompts,
  representation-specific guidance, renderer-v14, and attention persistence
  required several versioned static/smoke repairs before authorization.

## 2026-08-29 to 2026-08-30 — QA rescoring and exploratory findings

- **Final Direct-QA corpus/rescore**
  (`2026-08-29_rq1_1_direct_qa_final_combined_analysis.md`). Merged frozen and
  balanced positive questions without rewriting trajectories. Visibility-aware
  scoring excluded unprinted/truncated fields, accepted display precision for
  visual answers, and balanced ordered paths. This was post-hoc exploratory
  analysis, not a new model run.

- **Direct-RCA/QA/attention report**
  (`2026-08-29_rq1_1_direct_rca_qa_attention_findings.md`). Consolidated RCA,
  QA, cost, attention, repair/break, and model/dataset results. It found visual
  effects and costs were model/region dependent, while generic QA was not a
  stable case-level proxy for RCA.

- **Deep failure analysis**
  (`2026-08-30_rq1_1_findings_deep_analysis.md`). Added topology complexity,
  missingness, evidence coverage, attention-outcome, perception–RCA, and
  quadrant analyses with reader-friendly plots/PDF. These numerical findings
  later became historical invalid evidence under the V2 schema reset.

## 2026-09-01 — clean RQ2 and Composer design language

- **Clean RQ2 restart and case reuse**
  (`2026-09-01_rq2_clean_restart_and_rq1_1_case_reuse.md`). Removed old RQ2
  authority and reused the 289 RQ1.1 headline cases as 60 development, 139
  independent, and 90 downstream-lock cases. Initial smokes passed, but all
  generated artifacts were later invalidated by the V2 schema audit.

- **Evidence-card/silhouette grid**
  (`2026-09-01_rq2_evidence_card_silhouette_grid_refactor.md`). Defined
  one-card-to-one-silhouette conversion, finite grid capacity, non-overlap,
  clipping audits, occupancy, and typed Composer actions. This separated
  evidence selection from encoding and placement.

- **Mixed design and local-only handoff**
  (`2026-09-01_rq2_mixed_design_composer_local_handoff.md`). Replaced a small
  binary design with categorical/continuous factors and a constrained mixed
  design; specified a Qwen3.5-9B Composer interface and future SFT/RL attribution.
  Decided successor execution is local because Nibi priority was unreliable.

## 2026-09-02 — RQ2 dashboard repair, controls, qualification, and scope

- **Human-readable composite redesign**
  (`2026-09-02_rq2_human_composite_dashboard_redesign.md`). Replaced visually
  incomprehensible atomic panels with aligned metric groups, trace comparisons,
  log summaries, and explicit topology. Outliers/gaps were rendered without
  flattening useful variation. No model call preceded visual review.

- **Dense dashboard and equal-fact twin**
  (`2026-09-02_rq2_dense_dashboard_and_equal_fact_twin.md`). Registered top-12
  overlays at fixed facts and a separate top-24 `DENSE_M24` condition with an
  equal-fact Dense Text twin. Dense-versus-normal was explicitly unequal-content.

- **Legibility/internal-density repair**
  (`2026-09-02_rq2_legibility_and_internal_density_repair.md`). Raised font/mark
  floors, reduced avoidable whitespace/overlap, and distinguished filled grid
  silhouettes from sparse evidence inside a valid card.

- **Visual field dictionary**
  (`2026-09-02_rq2_visual_prompt_field_dictionary.md`). Explained every ID,
  panel label, time/bin, onset, z/source, MET-Z/TRC-L/LOG-R value, missingness,
  and topology direction only to image-bearing requests.

- **Design qualification and formal launch**
  (`2026-09-02_rq2_design_repair_and_smoke_qualification.md`,
  `2026-09-02_rq2_v7_smoke_qualification_and_formal_launch.md`). A 48-program
  development/16-program confirmation design and content/transfer smokes passed.
  That authorization was later superseded first by renderer repairs and finally
  by the complete DD-135 artifact reset.

- **D022 overlay repair**
  (`2026-09-02_rq2_d022_overlay_silhouette_repair.md`). Formal inspection found
  an overlay card placed in an undersized silhouette. Archived pre-fix records,
  required the existing 4×4 footprint, and reran only affected scientific input.

- **CPU/GPU pipeline scheduler**
  (`2026-09-02_rq2_cpu_gpu_pipeline_scheduler.md`). Added four core-pinned
  materializers, a bounded request semaphore, batch attention transfers, and
  separate postprocessing capacity. A brief double-supervisor overlap was
  isolated and affected records were marked invalid.

- **RCA-only scope**
  (`2026-09-02_rq2_rca_only_and_root_chain_qa_finding.md`). Root-connected
  RQ1.1 QA still showed weak/model-unstable association with RCA. RQ2 therefore
  abandoned packed QA while retaining its code for audit and continued one-stage
  RCA plus attention.

## 2026-09-03 — renderer successor, counterfactual registration, full reset

- **Lossless renderer successor**
  (`2026-09-03_rq2_lossless_renderer_successor.md`). Native-resolution review
  found overlapping trace text and permissive clipping/packing. Stopped the run,
  archived old D*/partial results, added measured fitting/backtracking, and
  exhaustively rendered 9,552 case/design pairs without layout failure.

- **RQ2 resume and RQ1.1 counterfactual registration**
  (`2026-09-03_rq2_resume_and_rq1_1_counterfactual_registration.md`). Resumed
  content-addressed RQ2 and registered a separate RQ1.1 factual/targeted/placebo/
  neutral one-stage image mechanism test. The latter remained deferred and
  RQ1.1-owned.

- **V2 processed-schema reset**
  (`2026-09-03_rq1_1_rq2_artifact_reset.md`). Audit found material node/pod/
  process/trace evidence omissions, including accepted roots present only in
  candidates for many fine-grained cases. Removed every generated RQ1.1/RQ2
  result, preparation, render, attention artifact, smoke, analysis, and local
  processed tree. Source/docs/rosters remained historical. No old output is
  resumable or current.

## 2026-09-04 — V3 data, SIRCL prompt, compact controls, performance telemetry

- **Vendored raw processor V3**
  (`2026-09-04_vendored_raw_processor_v3.md`). Copied selected SIRCL raw loaders
  byte-for-byte into the project, verified their hashes, and made the lossless,
  privacy-projected `CanvasRCAProcessedPublicCaseV3` path the sole active
  processor. Two cases per five datasets matched the reference raw conversion
  and Parquet semantic round trip. The complete raw indexes were subsequently
  converted to 2,302 per-case records: 1,422 AegisLab, 300 AIOPS-2022, 400
  AIOPS-2025, 90 RE2-OB, and 90 RE2-TT. Only after that full conversion did the
  selector materialize the frozen 480 processed cases (100/100/100/90/90).

- **RQ2 SIRCL* prompt alignment**
  (`2026-09-04_rq2_sircl_prompt_minimal_adaptation.md`). Replaced a shortened
  provisional RQ2 method with an RQ2-local minimal adaptation of RQ1.1’s selected
  SIRCL* prompt. Only variable metric-count wording and a neutral design-control
  paragraph differ; M→R→L→G analyzers, verification, candidates, and output
  schema remain aligned. No model call was made.

- **Compact-text and performance successor (current session).** Added RQ1.1 `C`
  and RQ2 FULL/C*/dense compact typed-text controls derived from identical
  canonical facts. They distinguish nonvisual structural/prose compression from
  spatial visualization. Added client-observed TTFT/E2E/decode/TPOT/output rate,
  stream-chunk proxies, run throughput/goodput, peak VRAM/KV cache, sampled GPU-
  seconds/energy, and preparation/materialization timing. Prefill remains null
  because it is not separable client-side; hardware measures are operational.
  vLLM recipes, prompts, renderer facts, models, scorer, and labels are unchanged.
  RQ1.1 static qualification and RQ2's 34 CPU tests passed, as did syntax,
  critical lint, YAML, line-limit, and diff-integrity checks. Obsolete checks
  that depended on intentionally deleted migration artifacts were replaced by
  current source-tree and unified-inference projection checks. Smoke was
  explicitly not run.

- **Full-corpus RQ480 and answerable-QA qualification (current session).**
  Materialized and validated the exact seed-42 RQ480 from the complete V3
  corpus; the source-manifest SHA256 is
  `6dbfcc80fb4a875d2f53a7085b703d099e8210b472c5312e5da8a07ee408df48`.
  Removed obsolete 469-case and predecessor smoke rosters. Direct-QA now labels
  perception difficulty by distinct M/R/L/G region count and reasoning
  difficulty by executable program complexity. Its 12/36/72/72 template
  registry rejects all missing, unavailable, unprinted, or unsupported gold
  values before inference and schedules requested path/reasoning cells without
  labels or responses. RQ1.1 static qualification and RQ2's 36 CPU tests pass;
  full prepared-corpus QA auditing is in progress. No model call has occurred.

- **Eight-core preparation and restart qualification (current session).**
  Preparation and artifact writing now use at most eight workers pinned to
  distinct physical cores. Exact-output tests showed that the optimized Denum
  row construction and anonymization preserve the predecessor graph, public
  packet, and rendered bytes. A balanced 20-case RQ1.1 run was interrupted
  after three persisted cases and resumed by verifying/skipping those three;
  it completed 20/20 and projects RQ480 at roughly 1.8–2.5 hours. The equivalent
  RQ2 preparation finished in 112 seconds and projects below one hour. Reading
  and hashing all 975 MB of the RQ1.1 sample took 3.39 seconds. The raw V3
  processor now checks atomic completion before loading a source case. Formal
  resume additionally binds the actual prepared evidence/images, private
  labels, record hash, call identity, and conversation. Static suites pass for
  RQ1.1 and RQ2 (38 tests). The RQ1.1 runner was repaired to honor the explicit
  local vLLM profile rather than the inactive Nibi projection. No model call
  was made.

- **RQ1.1/RQ2 completeness audit and safe pause (current session).** Raised the
  RQ functional-module ceiling to 6,000 lines, then inspected both trees for
  unfinished markers, empty/ellipsis/NotImplemented functions, fake active
  paths, and config-to-dispatch gaps. RQ1.1 uses 4,960 functional lines and RQ2
  4,811; both completeness guards, syntax/critical lint, RQ1.1 static checks,
  and all 39 RQ2 CPU tests pass. Only unused RQ2 helpers/imports were removed.
  Explicitly abandoned audit code and the future Composer data harness remain
  isolated from active runs. At the user's request, the CPU-only RQ1.1
  preparation was terminated cleanly at 186/480 cases: 186 public/private
  pairs, no temporary/partial case files, no worker, vLLM, or GPU process left.
  A test-only contract transition was recorded without changing case bytes;
  three complete cases were fully hash-read and the partial index is ready for
  an ordinary resume.

## 2026-09-05 — V3 preparation and smoke qualification

- Retained the complete 480/480 RQ1.1 preparation and four complete RQ2
  preparations: 60 development, 150 independent, 90 downstream-lock, and 480
  tool-full cases. Their semantic index hashes are recorded in DD-142 and the
  RQ descriptions; no preparation has a missing path or temporary/partial
  artifact.
- Full-corpus RQ1.1 answerability, QA balance, private-label isolation,
  counterfactual uniqueness, anonymization, and leakage audits passed. Current
  RQ1.1 and RQ2 static suites passed.
- Ran and manually inspected all six active bounded smokes. RQ1.1 Direct RCA
  and Direct QA completed 18 calls each. RQ2 equal-fact, content-budget,
  transfer, and tool×representation completed 8/18/18/16 calls. All 96 requests
  persisted, parse rate was 1.0, and no infrastructure error or truncation was
  found; verifiers passed.
- Frozen and authorized the two active RQ1.1 successors and four RCA-only RQ2
  successors for local formal execution. Counterfactual RCA remains deferred
  until RQ2 completion; multi-stage RCA and packed QA remain abandoned.
- **Direct-QA ordered-reference repair.** During the partial Qwen run, a
  trajectory-level audit found that “first displayed” trace/edge questions
  referred to different rows in text/S and the real dashboard. The queue was
  stopped before Gemma QA. R/G anchors were changed to unique visible content
  keys and the residual trace-row wording was removed. Static invariance checks
  and a fresh dual-model 18-call smoke passed. Across 768 changed matched
  groups, 2,645 completed Qwen QA records were deleted with explicit manifests;
  4,246 exactly unaffected QA records and all 18,240 RCA records were retained.
  Only QA schedule sidecars were revised; full evidence/images were not rebuilt.
- **Successor completion and analysis repair.** Repaired Direct-QA completed for
  both models at 8,640 terminal records/model (Qwen: 8,548 completed, eight
  infrastructure errors, 84 protocol-ineligible; Gemma: 8,556 completed, zero
  infrastructure errors, 84 protocol-ineligible). Random audits found complete
  matched questions, conversations, dashboard inputs, and same-call attention.
  The post-run analyzer then exposed an optional-metric `float(None)` bug; it
  was corrected to average only numeric observations. Targeted regression plus
  Direct-RCA and Direct-QA analysis reruns passed without changing or rerunning
  inference. Full artifact verification precedes automatic RQ2 continuation.

## Current handoff

Old numerical findings remain historical and invalid under DD-135. Direct RCA
V3 is complete and must not be rerun. Resume repaired RQ1.1 Direct QA (Qwen,
then Gemma), verify/analyse the complete RQ1.1 result, then run RQ2 development
design selection, independent design/content evaluation, downstream transfer,
and tool×representation. Reuse the retained evidence/image preparations.

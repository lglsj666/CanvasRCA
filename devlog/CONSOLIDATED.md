# CanvasRCA consolidated devlog

## 2026-10-18 — RQ4.5 static-only implementation

Implemented the approved six-arm exclusive-hybrid/spatial-pruning plan, source ownership and selection packets, complete marginal component C39, closed execution gates, central scoring, queue/resume/storage and future offline regressions. Python/config/TypeScript/source-protection static checks are the only verification executed. No preparation, renderer/browser, actual processor count, feature extraction, CPU regression, GPU smoke or model call. Historical baseline answers are references; Codex.md and historical experiment code/config remain unchanged. Runtime dependencies are lazy so static checks do not require numba/Torch/vLLM. [Plan](../docs/experiment_plans/RQ4_5_Exclusive_Modality_Spatial_Pruning_Plan_2026-10-18.md) · [Status and static receipt](../RQs/RQ4_5/findings/exp_exclusive_spatial_findings.md).


## 2026-10-12 — RQ4.4 complete analysis delivered

Formal840/840 plus smoke18 complete; no new analysis calls. SOURCE MRR .3286 (tolerant .3431), below historical U .3517 with2.409x tokens. Both primary Holm comparisons fail to establish benefit; candidate closed under registration. All30 mechanism cases read,270 formal attention mappings verified, Precision corrected offline without changing raw scores. [Detailed report](../docs/experiment_reports/RQ4_4_Qwen_Analysis_2026-10-12.md) · [RQ-local log](../RQs/RQ4_4/results/source_views_v1/logs/2026-10-12_final_analysis.md).

## 2026-10-12 — RQ4.4 source-complete local views qualified and launched

Implemented SOURCE_ZOOM / REPEAT_VIEW / HASH_ZOOM from the unchanged historical U overview. All220 cases and660main inputs pass actual-processor CPU qualification; fixed mechanism30,18runtime probes,16offline regressions and2shared renderer checks pass. One GPU smoke18/18 completes and verifies in199.93s,zero infrastructure errors;9passive attention records3,525–3,966bytes,only layer3 last-prompt/first-decode queries. Added a registered unified renderer export operation without changing old component defaults or Codex. Storage-only post-smoke fixes cover concurrent atomic writes, reference metadata, finalization resume and retention verification; frozen requests/model/renderer/inference are unchanged and original smoke provenance remains. Formal840 positions launched withCPU8/GPU8,vLLM BF16 memory0.8; 180.30s observation after first commit passed; 37/840 committed at handoff, no infrastructure error. Optional DeepGEMM import warning is handled and not a request failure. HistoricalU/T_FULL/MARGINAL_FIVE reused,900actual-call ceiling including smoke18 and recovery42. Runtime HTML remains until drain; exactPNG/conversations/labels/attention/source maps retained with plain-file deduplication and final density audit. [Deployment report](../docs/experiment_reports/RQ4_4_GPU_Qualification_2026-10-12.md) · [Current state](../RQs/RQ4_4/findings/exp_source_views_findings.md).

## 2026-10-11 — Artifact retirement extended through RQ3.15; RQ3.16 unchanged

User explicitly requested removing all raw results, preparation, inputs, conversations, outputs and generated intermediates through RQ3.15, while preserving source/configuration, design documents, analysis reports and their figures/tables. Removed 43 further project artifact roots, retaining 32 human documents and 115 referenced report/gallery assets; HTML dependencies verified. Removed 386 clearly attributable Windows example exports for RQ3.8 and RQ3.10–12, preserving later example directories. Approximately 26.51 GB freed on the project filesystem. Every one of RQ3.16's 23,722 files and its main report remains byte-identical; 690 source/configuration files, Codex and 587 report/gallery assets verified. Old upstream preparation dependencies are intentionally unavailable; no raw-output backup was kept. No model calls or run resume; RQ4.3 remains manually paused. [Cleanup record](../docs/issues/Through_RQ3_15_Artifact_Deletion_2026-10-11.md).

## 2026-10-11 — User-authorized removal of pre-unified experiment artifacts

RQ3.8 is the first experiment using `src/renderer/`. Removed raw results, preparation, intermediate artifacts and old run caches/logs for RQ1/RQ1.1/RQ2/RQ2.1/RQ3/RQ3.1–3.7, retaining source/configuration, reports and report-linked images/tables. Relocated 190 reports and 40 attachments; verified all 538 existing local report assets, 451 old source/configuration files and 239 later source/configuration files. No new broken report-asset links; four preexisting missing links are documented. Approximately 297.12 GB (276.72 GiB) freed. Raw-result replay/rescoring is no longer available for these retired runs. RQ3.8+ artifacts and Codex unchanged; no model calls or experiment restart. RQ4.3 remains manually paused by the user. [Cleanup report](../docs/issues/Pre_Unified_Artifact_Deletion_2026-10-11.md).

## 2026-10-11 — RQ4.3 vLLM v13 resumed; startup observation completed

User waived GPU smoke and authorized direct formal resume. Static plus 14 affected offline regressions and 43 actual processor packets passed; renderer/Codex/historical commits preserved. Unified vLLM retains registered token operations, MRoPE and passive text/image attention, with eight physical-core CPU workers and actual decode batch eight. After the first new commit, 180.10 seconds of observation ended at 405/2632 with no new infrastructure failures; subsequent handoff snapshot 418/2632, running. Prior 14 infrastructure failures and nine interruptions remain charged. Startup GPU mean 82.43% is below the earlier 85.58% reference and is not a sustained speed claim. Twelve audited attention records were 793–801 bytes each; conservative 10,000-record ceiling 730,464,256 bytes. Full real-model backend numerical equivalence was not separately tested. [Deployment report](../docs/experiment_reports/RQ4_3_VLLM_Deployment_v13_2026-10-11.md); [RQ log](../RQs/RQ4_3/results/deployment_v13/logs/2026-10-11_vllm_deployment.md).


## 2026-10-11 — RQ4.3 eight-way GPU function passes; utilization target remains unmet

Later user amendment:85.58% explicitly accepted;stop further optimization.Performance is no longer blocking.Formal remains paused;this status question does not launch it.

User waived CPU rerun. Final fused BF16 smoke18/18 in284.21s,8physical CPU workers and8decode overlap;0infrastructure errors,2invalid replies retained. Eight opportunities consumed81calls. Mean active GPU85.58%,eight-inflight87.67%,below88% target. Weights/input PNGs unchanged; fused rounding alters7/15 rankings, accepted by the user's operational precision criterion. Attention803bytes; on/off reply equal. Formal281/2632 remains paused, activation disabled, no owned GPU process. [Report](../docs/experiment_reports/RQ4_3_Concurrency_GPU_Qualification_v9_2026-10-11.md) · [RQ log](../RQs/RQ4_3/results/concurrency_v9/logs/2026-10-11_concurrency_and_acceleration.md).


## 2026-10-11 — RQ4.3 v6 scoped CPU progress, full qualification pending

User-authorized layout repair is recorded in v6. S/P CPU source checks220/220,
S images440/440,18current tests and220prompt/X_SP followups pass. R fixed
prototypes fit full-image capacity but exceed retained K even before allocating
observation tokens. Two redundant S conditions cancelled;5988 allocated/8000
ceiling, zero new model calls. No Codex edit or GPU launch. [RQ-local log](../RQs/RQ4_3/results/cpu_render_v6/logs/2026-10-11_layout_repair_and_cpu.md)
· [detailed CPU report](../docs/experiment_reports/RQ4_3_CPU_Progress_2026-10-11.md).

## 2026-10-10 — RQ4.2 complete: source partitioning does not improve the strongest visual method

All 1,336 positions committed: 1,100 RCA and 236 QA, 1,328 actual calls plus 8 exact references, no infrastructure unknowns. Including prior qualification, 1,347 attempts. FULL/GEOM/SEM/SHAM/NATIVE4 MRR .2841/.3088/.3084/.3011/.3235; reused A_UNIFORM_E50 .3517, T_FULL .4846 and hybrid MARGINAL_FIVE .5054 without new calls. SEM total tokens save 24.02% versus text but cost 2.89 times uniform pruning; ranking/latency gates fail and the candidate closes. Registered primary/mechanism families do not pass Holm. Audited 109 dependencies, all submissions, 2,173 PNG checks, current and historical scores and 28 independently recomputed tests. Read 60 reasons in 12 fixed cases with 7 directed source checks; 534 attention summaries use 403,919 bytes and observe only one text layer/two query positions. Complete data, failure denominators, QA, attention, timing limits and historical comparability are documented. No new model calls, runtime edits, Codex changes or next experiment. [Detailed report](../docs/experiment_reports/RQ4_2_Qwen_Analysis_2026-10-10.md); [RQ log](../RQs/RQ4_2/results/partition_v4/logs/final_analysis_2026-10-10.md).

## 2026-10-09 — RQ4.2 best-prefix partition revision passes CPU admission

User explicitly reopened algorithm repair without GPU authorization. Deterministic capacity-feasible best-prefix moves/swaps replace strict one-step descent; gate metrics never enter objective. Unchanged thresholds, uniform edge weights, source closure, background cap, pixels and fixed SHAM seed. SEM57/60,56/60,71/100; SHAM56/60,56/60,90/100; independent recomputation and30probe/full identities pass. Reuse unchanged v3 renderer/source geometry. QA59ready/1N/A/350questions, actual CPU processor220cases/558forms, no resize, max16846 input/16384image tokens. All five offline cold paths and recovery pass; 27 RQ tests plus2new final checks pass, one historical browser check reused.111protected files/Codex unchanged.100dependencies frozen; no activation permission, GPU calls or new scientific outcomes. GPU supervisor integration and real model qualification remain later work. Stop at CPU. [Report](../docs/experiment_reports/RQ4_2_SEM_Refinement_CPU_Qualification_2026-10-09.md); [protocol](../RQs/RQ4_2/descriptions/RQ4_2_partition_refinement_v4.md).

## 2026-10-09 — RQ4.2 representation repaired; SEM intervention admission fails

User-authorized CPU revision repaired scoped-caption overflow, variable event-plot height, exhaustive-candidate directory identity and diagnostic foreground masks. Unified renderer v3 packs/renders all 220 cases; 404,452 bindings checked. Correct SEM joint admission: A22 50/60, A25 55/60, Aegis 38/100; Aegis fails the unchanged 50% gate. Ink-weighted relation allocation reaches 44/100 and is not adopted; limited three-group-cycle probe also fails to resolve it. Preserve invalidated v2 and all attempts. 50 distinct technical tests pass; 10 unrelated optional browser tests not run. Default fixture PNG byte-identical; 111 protected files unchanged. Current QA/actual-processor/full runtime admission remains unqualified; no CPU activation receipt. The candidate stops, not an RCA performance result. No GPU, model calls or attention collection. [Detailed report](../docs/experiment_reports/RQ4_2_CPU_Revision_2026-10-09.md); [revision](../docs/experiment_plans/RQ4_2_CPU_Revision_2026-10-09.md); [findings](../RQs/RQ4_2/findings/exp_partition_findings.md).

## 2026-10-09 — RQ4.2 stops at common-image CPU capacity admission

Saved the approved five-arm provenance-defined encoder partition plan and review dispositions. Implemented the CPU source/DOM admission path and numerical grouping primitives; added an explicit shared-renderer narrow-caption readability operation without changing defaults. Fixed inventory-width classification, scalar digit wrapping and graph-height measurement before rerunning affected admission. Final220-case necessary capacity passes: A22 0/60, A25 5/60, Aegis1/100;214 exceed the maximum canvas even before header, spacing and source-bundle packing. Static/type checks and37 local regressions pass;12 optional historical browser tests skipped. Three fixed cases reproduce DOM measurements; default regression PNG byte-identical.111 protected source/report/scorer/Codex hashes unchanged. Per registered stop rule, complete CPU qualification fails and downstream encoder/QA/attention/formal execution remains unimplemented/unqualified.0 new calls or GPU work; do not claim this tests the encoder hypothesis. [Report](../docs/experiment_reports/RQ4_2_CPU_Admission_2026-10-09.md); [findings](../RQs/RQ4_2/findings/exp_partition_findings.md).

## 2026-10-09 — RQ4.1 complete: compressed visual ranking loss, position sensitivity and bounded attention findings

All6100 positions terminal:6082 committed replies and18 preregistered N/A; 4840 main calls complete. Preserved36 pre-HTTP seed-validation failures and1 power-loss interruption;6119 formal attempts plus163 earlier qualification/probes. Central scoring,12164 request/trajectory hashes,881 PNGs,137 frozen dependencies and801 attention maps verified;32 independent Decimal/Holm comparisons agree. T_FULL/T_NATIVE/CVC_E50/A_UNIFORM_E50/V_FULL MRR .4846/.4861/.3332/.3517/.2209. CVC tokens save73.69%, comparable HF online wall only3.63%; cold/native workload efficiency unestablished. Six primary v11 comparisons fail; candidate closes, no posthoc winner/confirmation. Position causes47/90 top1 flips in each CVC/UNARY vs0repeat, adjusted p7.47e−13. All360 repeat rankings match but reasons differ. QA joint floor plus inherited RCA instructions in text QA prevent the intended QA–RCA inference. Attention is801 summaries of one layer/two initial queries,4.12MB allocated including maps/directories,10000-call bound730.46MB; title density is descriptive, not sink causality. Read48 reasons in12 fixed posthoc cases, checked10 directed entries in6 cases. No new inference or runtime/Codex edits; owned services stopped. [Full report](../docs/experiment_reports/RQ4_1_Qwen_Analysis_2026-10-09.md); [RQ log](../RQs/RQ4_1/results/comparison_coding_v1/logs/final_analysis_2026-10-09.md).

## 2026-10-06 — RQ3.22 cancelled and completely removed; pure-visual direction adopted

The user cancelled the unlaunched RQ3.22 and explicitly requested deletion of its entire experiment, including plans, code, test scripts, CPU/GPU smoke artifacts and examples. Removed the RQ directory, its plan/report files and assets, and the two RQ3.22 Windows galleries; no backup retained. There were no formal calls. The 54 already spent smoke attempts remain a count only in [deletion accounting](../docs/issues/RQ3_22_Deletion_Record_2026-10-06.json); their inputs/outputs and qualification receipts were deleted. RQ3.21 and earlier experiments remain intact. No model service is running. Earlier RQ3.22 qualification entries and live index links were removed to avoid suggesting resumable qualification.

All future research is now under RQ4, with a documentation-only statement/roadmap/registration-status scaffold. Necessary task, dashboard-reading and output-format text remains allowed; only incident diagnostic evidence is visual-only. Read the user-provided important_docs/conversation_oct_06. Codex.md now requires future method candidates to carry all incident-specific evidence through unified-renderer visual input, with no hybrid fallback. Static task/output instructions are allowed; strong text remains an evaluation baseline. This direction change authorizes neither a replacement experiment nor training/model calls. Next: a scoped feasibility and method decision around provenance-preserving visual representation, followed by explicit registration rather than another automatic full matrix.

## 2026-10-06 — RQ3.21 completed: cheaper encoding loses ranking; position sensitivity established

All2020 positions terminal:1767 fresh returns,21 exact-request references,220 historical anchors,12 infrastructure timeouts. Preserved35 power-loss interruptions;1814 formal attempts+18smoke=1832/1940. Owned GPU service inactive/success. Offline audit checked211 frozen dependencies,220 public/private identities,211 PNGs,1987 unique commit graphs,2008 logical inputs/token totals and20 independent case/group statistical tests. A/RT/RV/PV/EV/CT/CV MRR .5054/.4436/.4934/.4307/.4866/.4029/.4180; CV−A−.08742 (Holm case/group .02908/.06099), CV−RT−.02561. CV total tokens save16.3%–17.7% against A but ranking gates fail; no candidate adoption. Registered QA declines and excess position-induced top1 flips survive correction; strict-unit scoring ambiguity and exploratory phase-only audit disclosed. Read108 reasons in36 fixed cases; source-checked9 facts in6 cases, no population explanation-error-rate estimate. Formal known new tokens36,260,494 plus358,024smoke, unknown usage for47 interrupted/timeout attempts. No new inference/source/renderer change or automatic follow-on. [Detailed report](../docs/experiment_reports/RQ3_21_Qwen_Analysis_2026-10-06.md); [RQ log](../RQs/RQ3_21/results/compact_entity_v1/logs/2026-10-06_final_analysis.md).

## 2026-10-06 UTC — RQ3.20 complete; token savings with ranking loss and action-interface failure

Core1520 workflows terminal:1285done,205mechanism-inapplicable,30timeouts. Formal1460 actual attempts/1430 returns,16smoke,1476total; no retries or new analysis calls. Owned service inactive. Audited189 frozen sources,220 public recompilations,216 exact PNGs,1430 actual requests/scores/atomic commits and ledger;26 case/group statistics agree independently. F/ST/SV/T/V MRR .4693/.3649/.3139/.3782/.3866. Paired V−F−.0696, case/group Holm .00375/.00173; full-denominator bounds remain negative. Known paired V/F total tokens−16.86%, V/T+12.10%, output3.48x; no latency/GPU-saving claim, timeout usage unknown. All287/526 invalid selectors requested known but non-retrievable TRC/LOG IDs, causing registered whole-list rejection. QA cards improve only directly covered questions;19/60 applicable mechanisms, no reliable RR gain. Screened177 available positions in36x5 fixed-sample review, extracted6 targeted cases and checked10 source claims in5; no complete manual116-output grounding or explanation error-rate claim. Current candidate closed; conditional90/SIRCL/attention not run. [Detailed report](../docs/experiment_reports/RQ3_20_Qwen_Analysis_2026-10-06.md); [RQ log](../RQs/RQ3_20/results/budgeted_acquisition_v3/logs/2026-10-06_final_analysis.md).

## 2026-10-05 — RQ3.19 complete; visual replacement candidate closed

All1480 positions terminal:1449 unique returns,18 exact-request references,13 request timeouts;5 invalid model answers retain zero. Formal1462 attempts plus18smoke=1480 actual calls. Owned services stopped. Offline audit verified205 frozen sources,28 model files,220 public recompilations,8862 DOM bindings,1467 known inputs/scores and1449 artifact commits;18 independent Pratt tests/6 Holm families agree. F/C/A/V MRR .4562/.4308/.4569/.4139; paired V−F−.0450 (case/group pH .04340/.05099), missing-score bounds remain negative. Known paired V/F total-token cost about+2.8%, V/C+3.6%–4.3%; no saving, timeout usage unknown. QA V_Q1−V_Q0 +5.46pp, pH .000381; RCA ordering effects unestablished. Preserved QA ceiling, nominal weak positive correlation, posthoc naming sensitivity and entity-overlap limits. Screened120 C/V outputs, reviewed36 cases/71 valid reasons plus1 malformed loop structurally, checked13 directed RCA claims and3 actual PNGs. No population explanation-error-rate claim. Current V candidate ends; no posthoc winner, conditional module or new inference launched. [Canonical findings](../RQs/RQ3_19/findings/exp_visual_replacement_qa_findings.md); [RQ log](../RQs/RQ3_19/results/visual_replacement_qa_v2/logs/2026-10-05_final_analysis.md).

## 2026-10-05 — RQ3.19 core implemented, qualified and launched

Implemented frozen dual-track core1480 positions with current unified renderer; static, full220 CPU and actual visual review passed, GPU smoke18/18 complete. First launch verification: 9 committed results and36 in flight, local Qwen/.75 VRAM. Preserved failed v1 budget evidence, prospectively fixed QA unit spelling, repaired null-rank audit with explicit source compatibility/no new model calls, and relaunched the supervisor in its own OS session after an initial pre-call wrapper failure. No formal efficacy claim; conditional attention/SIRCL/extension inactive. Assistant stops after confirmed launch as requested. [RQ execution log](../RQs/RQ3_19/results/visual_replacement_qa_v2/logs/2026-10-05_qualification_launch.md); [qualification report](../docs/experiment_reports/RQ3_19_Qualification_and_Launch_2026-10-05.md).

## 2026-10-05 — RQ3.18 complete; population readout candidate closed

All2420 positions terminal:2328 unique returns,63 exact-request references,29 timeouts;10 duplicate-ID model failures retain zero. OwnedGPU service stopped. Audited197 frozen sources,220 public compilers,2328 complete artifact graphs and2391 inputs/scores;42 independent Pratt checks plus4 Holm families agree. FP MRR .4877 vsT .4243/F .4648; paired FP−F +.0220, A22/A25 +.0571/+.0483, Aegis −.0150. All registered corrected comparisons fail; R−FR −.0056 and Top5 protections fail. Known paired cost FP/F +4.15%–4.91%, FP/T +6.27%–7.18%; timeout usage unknown, no compression claim. Read393 available reasons across36 registered cases, verified22 directed claims/34 arm-claims; unsupported axes remain unknown, no population explanation-error-rate claim. Stop the preregistered candidate; no post-hoc winner, additional calls, attention or successor launch. [Full findings](../RQs/RQ3_18/findings/exp_population_readout_findings.md); [RQ analysis log](../RQs/RQ3_18/results/population_readout_v1/logs/2026-10-05_final_analysis.md).

## 2026-10-05 — Empirical evidence and a joint accuracy/cost method objective

Reviewed22 historical reports/retrospectives plus current constraints/protocol/status, and primary empirical/perception/compression literature. Saved [research objectives and provisional method](../important_docs/CanvasRCA_Empirical_to_Method_2026-10-05.md), [reading/novelty review](../important_docs/CanvasRCA_Empirical_Literature_Review_2026-10-05.md), source manifest and reproducible RQ3.16 cost audit. Paired220 MARGINAL_FIVE versus PAIR_FIVE MRR .50538/.44364 at total-token ratio1.03887; against BASE_FLEX ratio1.18396 with content/output differences. Original significance/adoption status unchanged. Latest user objective jointly targets MRR≈.60 and ≤5% added actual cost. Proposed offline joint-reading calibration and one-call representation allocation is not implemented or validated;2,880 calls are a non-authorizing envelope. Existing RQ3.18 remains frozen and running;0 additional model calls. [Project log](2026-10-05_empirical_method_review.md).

## 2026-10-04 — RQ3.17 v4 complete; combination not adopted

All3080 positions terminal:2983 responses,76 exact-input references,21 timeouts;5 duplicate-ID model failures retain zero. OwnedGPU service stopped. Full artifact/score/public-compiler audit and70 independent statistical checks passed; CPU qualification remains user-waived. C MRR .4957 vsT .4670, D .4988, N .5048; CN .4778. Primary six comparisons fail, Aegis C−T−.0340 andTop5−4pp. Research cost gate passes at1.163–1.211T but no cost saving.36-case explanation sample:503 rule screens,119 manually read reasons,12 directed source checks; not exhaustive grounding. No new model calls, frozen inference source unchanged. [Final report](../docs/experiment_reports/RQ3_17_Qwen_Analysis_2026-10-04.md); [RQ log](../RQs/RQ3_17/results/topology_marginal_v4/logs/2026-10-04_final_analysis.md). Stop current candidate; no automatic successor or post-hoc adoption.

## 2026-10-04 — RQ3.17 v4 resumed from committed pause

User explicitly resumed. Frozen source matches; existing18-call GPU smoke reused, CPU waiver preserved. Skipped phase0 and committed positions; dispatch phase1 starts770 new-call tasks plus4 references. Local Qwen service active at0.75 GPU fraction and new atomic commits verified. All historical results/timeouts and pause receipts retained. [Resume log](../RQs/RQ3_17/results/topology_marginal_v4/logs/2026-10-04_resume.md).

## 2026-10-04 — RQ3.17 v4 safely paused by user

Stopped new submissions, drained active calls and writers, verified2306 terminal positions (2288 successful incl72 references;18 request timeouts) and774 remaining. All owned GPU processes stopped; port21957 closed; SQLite quick_check and atomic commit presence passed. Resume authorization revoked until explicit user resumption. [Pause record](../RQs/RQ3_17/results/topology_marginal_v4/PAUSED_BY_USER_2026-10-04.md).

## 2026-10-03 — RQ3.17 v4 GPU qualification resumed; CPU waived by user

All220 preparations committed. User stopped remaining CPU audit after logged160/220 and explicitly requested immediate GPU smoke; no CPU-pass claim. Source-bound waiver preserves static/visual/scientific/budget/runtime gates. Smoke passed18/18 in235.28s, all14 arms covered, no infrastructure failures/truncation/invalid outputs. Formal3080-position supervisor launched;440 matrix/node bound-combination positions first. [Log](../RQs/RQ3_17/results/topology_marginal_v4/logs/2026-10-03_execution.md).

## 2026-10-03 — RQ3.17 v4 CALLS dashed width and heads3×

User narrowed scope to CALLS only and included dashed arrowheads.1.4→4.2; solid edges/heads and all DEPLOY unchanged. Static/type/build and three-case artifact comparisons passed;15 node examples differ only as requested,21 other PNGs unchanged. Examples under `Downloads/例图/10_02/RQ3_17_v4`; GPU/formal remain paused,0 calls. [Log](../RQs/RQ3_17/results/topology_marginal_v4/logs/2026-10-03_calls_dashed_width.md).

## 2026-10-03 — RQ3.17 v3 direct-color examples; paused

User requested replacing circles with direct relation colors. Unified renderer now recolors exact matrix glyphs / full directed arrows (including isolated per-edge arrowheads) and matching duration-card labels.14 arms unchanged; static/type/build,35 shared renderer tests and three-case regressions passed. Six actual matrix/node PNGs reviewed. Full CPU/GPU/formal remain paused,0 model calls. [Amendment](../docs/experiment_plans/RQ3_17_Direct_Color_Binding_2026-10-03.md); [log](../RQs/RQ3_17/results/topology_marginal_v3/logs/2026-10-03_direct_color_examples.md). Windows examples: `Downloads/例图/10_02/RQ3_17_v3/compare.html`; prior galleries preserved.

## 2026-10-03 — RQ3.17 v2 topology controls; paused for example review

Added five node-arrow counterparts (14 arms/3,080 registered positions) and numbered relation binding through the unified renderer. Code/static,35 renderer tests and three-case example checks passed; full v2 CPU, GPU and formal execution remain pending,0 model calls. Windows examples are under `Downloads/例图/10_02/RQ3_17_v2/compare.html`. v1 artifacts preserved. See [amendment](../docs/experiment_plans/RQ3_17_Topology_Encoding_Amendment_2026-10-03.md) and [RQ log](../RQs/RQ3_17/results/topology_marginal_v2/logs/2026-10-03_node_topology_examples.md). User requested review before further work; no automatic launch.

## 2026-09-29 — RQ3.8 v7 Nibi qualification, cache transfer and four formal jobs

The v7 GPU smoke job22942268 completed in25m59s with18/18 live Qwen/Gemma
calls and passed the persisted image/conversation review. Static qualification
passed. CPU regression was explicitly waived for formal execution and remains
**not run**. This is operational qualification, not an MRR result. The earlier
zero-call startup and v6 over-context attempts remain failed historical
records. See `docs/issues/RQ3_8_nibi_startup_2026-09-29.md` for the full
failure/recovery timeline and remaining startup-time caveat.

The first multi-source cache transfer omitted `rsync -R`, misplacing roughly
31GB of new copies at the Nibi checkout root. After verifying their exact
scope, only those misplaced root targets were removed; originals/results were
preserved. The retry used `rsync -aR --partial`, and the symlinked historical
SQLite ledger was dereferenced with `-aL`. Both final transfers exited0. A
lightweight presence audit found all required files for the840-case formal
roster (480 eval,360 exposed test), missing0; formal export retains its
per-case source-hash check. This does not constitute a full CPU regression or
prove all future exports will succeed.

Nibi accepted three Qwen eight-hour shard jobs22945130/22945133/22945134 and
one Gemma eight-hour full-cohort job22945136 (`afterany` dependency). At the
submission snapshot all four were pending and no formal model call was
claimed complete. Detailed receipts, evidence class, caveats and next action:
`RQs/RQ3_8/results/ops_components_v7/logs/2026-09-29_formal_submission.md`.

## 2026-09-29 — RQ3.8 v6 GPU smoke submitted:22941413

Nibi authenticated connection restored via `canvasrca-nibi-login-v7` and its
multiplexed SSH socket. SCP transfer SHA256 matched
`a86bcb903e3439fbf0fd9c71753abe15b7bac4a668ae706ffca7a104b5f0cb23`.
Code, compiled bundle and the three frozen smoke inputs were copied to
`/scratch/lglsj/CanvasRCA`; old source backup is
`build/rq38_deployment/v6-pre-sync.8Wz1hG/pre-v6.tar.gz`.
Remote static entry passed (1885 nonblank/noncomment RQ-source lines); roster
and budget initialization succeeded:19440 formal positions,18 smoke,542reserve.
This initialization is metadata only, not full840-case preparation.

Slurm acknowledged `rq38v6-smoke-attempt7`, job22941413, account
`def-jacobsen_gpu`: one fullH10080GB, eight CPU cores,96GB host RAM,30minutes.
Two models run sequentially; FULL_PAIRS/MR_NO_MARKS/METRIC_TIME_PERMUTED on
three registered development cases, at most18 initiated requests in total.
No CPU-regression/pytest job or formal job submitted. Stop after submission;
no live completion, success, numerical outcome or visual review claimed.
Next action is to inspect this job's persisted logs, conversations and PNGs
when the user requests; submission alone does not qualify formal inference.

## 2026-09-29 — RQ3.8 v6 direct GPU smoke authorization

After the static-only expansion the user authorized direct GPU smoke submission.
DD-20260929-04 records one additional Nibi30m fullH10080GB job, shared18calls,
both models sequential; no CPU regression job/pytest or formal run authorized.
The submitter permits only this one new smoke. Necessary public-input renders
and processor capacity checks are in its allocation, not local tests. A narrow
smoke-only exception records CPU regression as not run; it does not qualify
formal execution. Compiled renderer bundle is now part of source attestation.

Deployment check: existing authenticated tmux SSH no longer responds; a fresh
noninteractive connection reaches Nibi but requires interactive MFA. Asked user
to log in to `canvasrca-nibi-v6`. Submission status remains pending until an
actual Slurm acknowledgement; no job is claimed from code/static completion.

After login, Nibi's previous successful smoke was confirmed to use only the
portable v2 preparation. Package the three existing canonical/public cases,
frozen parent contexts/exports, scoring records and registration/ledger for v6;
do not rerun raw preparation. Known workstation context paths are narrowly
rebased and still hash-checked. Old ledger symlinks must be dereferenced during
copy. The first large terminal transfer lost its SSH session before extraction;
switch to a multiplexed SSH connection and SCP. No job submitted at this point.

## 2026-09-29 — RQ3.8 v6 mechanism-complete expansion (static-only)

User requests approximately20000 calls and stopping after code/static work.
Registered16 eval arms, six extra mechanism/repeat arms on hash-selected100
cases, and four locked methods on exposed test360:19440 formal +18 shared
smoke, reserve542 within a20000 new-round cap. DD-20260929-03 in RQ3.8
descriptions explains the superseded cumulative budget and retained history.
No new Slurm/CPU/GPU authorization or old-result reclassification is implied.

Implementation adds explicit renderer mark/footer switches with suppressed
binding manifests, an independently chosen edge-pairs component, shared
canvas capacity, visual-conflict probes, independent repeat identities,
cohort-aware bounded jobs and contrast-local analysis. The approved node-link,
deployment mappings and log grouping are unchanged. The same complete text
remains in all arms; deliberately corrupted visual stress is labeled as such.
The renderer/experiment/design-decision/devlog workflows informed boundaries,
history preservation and provenance; runtime/visual acceptance is deferred.

Current limitations: no new performance results; no independent heldout claim;
Nibi test360 predecessor caches and eight-hour throughput not verified in this
static-only session. Runtime qualification and any exhausted job allowance
must be resolved before launching. Old v5 gallery is not a v6 qualification.

Session completion: AST/compile and unresolved-global checks on13 Python files,
JSON/source matrix-budget checks, bash-n, TypeScript noEmit, esbuild and diff
whitespace checks passed. Regression definitions were updated but not run.
Review receipt: RQs/RQ3_8/descriptions/RQ3_8_v6_Static_Review_2026-09-29.md.
No dataset processing, browser launch, inference, Slurm submission or Nibi sync.

## 2026-09-29 — RQ3.8 G03 service→pod public identity recovery

Scope/status: RQ3.8 `ops_components_v4` source change; no v4 CPU/GPU
qualification or model efficacy result yet. No v3 model call was committed.
The prior AIOPS-2022 smoke image `INC-0060628741E9` showed an empty G03 despite
42 public `node_pod_map` pod identities. Its Trace rows omit same-row
`k8s.pod.name`, the only G03 extraction path in v3. The established RQ1.1/RQ3.1
public `pod_to_service` projection resolves all 42 hosted names to service
identities, but v3 used it only for alias registration, not relationships.

Decision: retain explicit metadata and same-row Trace relations; supplement
unbound, hosted pods with name-derived service correspondence only when both
typed aliases exist. Skip conflicting explicit/observed bindings and names
ambiguous across namespaces. Keep a separate source audit. G03 does not claim
Kubernetes ownership or create invocation edges. The common text ledger and
visual evidence both receive the corrected facts; the reading guide now uses
instance identity rather than calling every G03 pair an observed deployment
relation. The v3 config/artifacts remain historical. v4 has its own prepared
and result namespace, and old CPU/smoke evidence is not qualification for it.

Next: sync v4 source to Nibi, run static source/config checks there, then obtain
fresh Nibi renderer/CPU and live smoke qualification under the user's job limits
before formal inference. Previously exhausted CPU/GPU job allowances are not
silently reset by the new version. Existing source exports may be reused;
existing v2/v3 model outcomes may not.

## 2026-09-29 — RQ3.8 C09统一为网格布局与折线路由

用户在 smoke PNG 人工复核后决定：`graph.node_link` 只保留原有大图分支的
确定性有界网格与折线路由，删除节点数≤30时的环形布局和曲线分支。实现同时将
自环改为矩形折线；节点、边、类型、ID、证据选择和 prompt 均不改变。原先同名
组件按节点数暗中切换视觉语法的问题已移除。

该动作会改变所有 C09 PNG，故 RQ3.8 前向登记为 `ops_components_v3`，使用独立
preparation/results 根。v2 配置与 artifacts 保留为历史，不得资格证明或续跑 v3。
正式实验仍未提交；v3 在新的 renderer/CPU 和 live smoke 资格完成前不可启动。

## 2026-09-29 — RQ3.8 Nibi部署推进与空值兼容修复

最新用户追加：GPU smoke最多3个Slurm job，每个30分钟；通过后不额外提交。
CPU回归最多8个Slurm job，每个最多1小时；提交器计数且阻止重复活跃资格job。
用户明确后续测试直接在Nibi运行，本地通过不能替代远端资格。停止本地preparation，
保留已完成公共导出/渲染；剩余渲染和所有后续资格测试在Nibi Slurm上执行。
Nibi CPU job22921386失败：47pass/1fail/1skip，失败为跨机器PNG像素严格相等。
字体与web bundle两机哈希一致；不据此断言图形无问题。后继测试在Nibi从冻结原始
design/evidence生成参考图，校对原始geometry/font/bundle/CSS/依赖hash，再严格对比
同机FULL及消融留存组件像素。跨环境差图/浏览器版本仍保存并人工审查。
测试临时PNG改存job专属scratch结果，避免计算节点/tmp随job结束而不可取。
逻辑smoke仍18次/600秒，不能通过拆job重置调用数。正式job仍最多6个、各8小时。

继续ops_components_v2，不恢复被用户放弃的拓扑改动。旧Nibi登录会话仍可执行命令；
远端Qwen3.8-27B/Gemma31下载receipt complete，Qwen9B原目录保留，尚无正式job。
新增六分片独立调用计数、done/fail快速续跑、只恢复未提交事务、300秒timeout终态继续
及其他基础设施fail-fast；统一Nibi launcher允许显式版本profile和关闭attention，旧默认不变。
每分片500次中断/修复预留后累计最大38914，不能每个job重置40000预算。
48项CPU/浏览器/恢复回归通过（local_cpu.xml）；完整480公共导出首次发现log_r=null
导致成员查询TypeError，修为无统计字典时保留模板及已有计数、不虚构rate。
已完成导出可直接复用，新增空值回归待检查。GPU smoke及正式提交仍未执行。

## 2026-09-28 — RQ3.7 CPU/GPU资格通过，A→B正式已启动

用户授权回归、smoke后启动实验。真实CPU回归修复父版k/M/G数值缩写解析，补入来源核实的RQ37-local OTel精确指标定义（未修改旧证据选择/配置）；A smoke暴露并发进度写盘共用.partial的竞争，改用项目unique-temp atomic_write。修复后17个单元测试、3案例63编译目标通过，17.26秒，两processor容量检查通过。

A沿原始600秒窗口和18次累计调用上限续跑，两份已完成回答保留；最终18/18完成，529.37秒。B 18/18完成，269.33秒。两模型均实际覆盖；检查PNG、完整请求、raw回答/conversation持久化及成本，未发现阻塞问题。原失败报告及源码契约保存在pre_run_revisions，修复来源记录在smokes/A_repair.json；不抹去失败。依据字段核实单位定义，不按模型成绩修改设计。未知单位保留读数，实际柱图/换算适用率随case报告。

共享历史累计21469+资格36=21505；A+B正式新调用上限3420，已删除的重复参考不回退补跑，C不自动开启。源码契约1a8d2032bb94718e3a23b62d1a62e331b0b1b671410312b78e22b1dc756997a2。详细资格记录 `RQs/RQ3_7/results/fusion_v2_pruned/logs/qualification_review.md`。没有把smoke准确率当作方法效果，也不把smoke回答用于正式统计。

正式队列通过setsid后台启动，supervisor PID15647；确认A/Qwen runner PID16318实际提交推理，非仅服务占显存。11:35本地检查时已落盘3份新正式结果，共39次正式调用已登记（3 complete/36 started）；进度17/1260终态包含只读参考，不应把它们全算新增推理。队列按A→B自动切换，后台继续，无C授权。正式log：`RQs/RQ3_7/results/fusion_v2_pruned/logs/formal_A_B_supervisor.log`；阶段进度在同root的`progress/`。

## 2026-09-28 — RQ3.7删除重复生成条件（静态交付）

按用户精简授权，A删除B3_T_REF结果条件（保留历史公开输入锚点），TPV_REF/B3_G_REF改为只读兼容旧结果，缺失或不兼容登记reference_unavailable，不补跑、不记0、不重试。C在相同开发180上不能绕过此规则；其他病例必要基线仅在以后独立授权C时运行。四格和T_MATCH保留，B等价数字/单位及当前请求REPEAT保留，没有新增泛泛图文/绑定/布局比较。历史代码结果未删除。

同步计划、配置、任务生成/执行防回退、统计交集与配对扩量、测试定义、三份描述及静态审阅。A新增上限2880→1800，总保守新增13854→12774；A+B3420（含两smoke3456），C仍关闭。减少1080是最坏调用额度，不将本来可复用的旧回答谎称为实际节省。核心分析不受旧参考缺失牵连；历史对照单列有效配对N，Holm family不缩减。决策依据和影响见RQ3_7_experiments.md的DD-RQ37-1。

AST/本地导入符号/ruff/JSON版本和预算/bash语法静态检查通过；CPU与GPU资格均未运行，新模型调用0。新登记身份rq37_numeric_relation_fusion_v2_pruned，仅代码待后续资格，不启动任何队列。

## 2026-09-27 — RQ3.7实现与静态交付（未运行资格或实验）

落实用户批准的数值证据×实体关系融合协议：固定B3 ALL_ID公开内容，LOCAL/REMOTE×ID/LINK析因、同内容T_MATCH、数字写法/来源单位等价变换及独立REPEAT；C锁定泛化单独关闭。计划与历史去重索引在 `docs/experiment_plans/CanvasRCA_RQ3_7_Research_Plan.md`，源码为新 `RQs/RQ3_7/` 五模块+init，旧实现/结果/模型配置不改。

静态审阅修复了数值字面量、单位展示名称、附加M记录排版/同步、跨变体共同几何、重试prompt定位、timeout别名去重、历史锚点匹配及累计预算恢复风险。采用同一共享调用SQLite而不是另起计数器；未来预算最坏新增13854、历史设计基数21469、合计35323≤40000，实际登记时重新核对。终态flag先行续跑，历史结果只在请求与scorer兼容时引用；REPEAT不去重。语法/AST/导入符号/ruff/shell与静态预算检查通过，审阅详情 `docs/issues/RQ3_7_static_review.md`。

本轮没有CPU回归、preparation、真实渲染、GPU smoke、服务或正式实验，新增模型调用0。真实图形覆盖率、可读性、双processor容量、恢复与GPU链路仍待后续明确授权后的资格检查。没有将静态完成视为实验通过或有效性结论。

## 2026-09-28 — RQ3.6 mechanisms_v2 全量离线统计与案例审阅

队列于00:01:18 UTC正常完成，12240逻辑位：12196正常结果、6重复ID模型失败、38请求超时，无不明缺失。实际新增正式10500、smoke52；1740合法复用，历史加总21469。主分析按实验×模型全arm共同病例集，Qwen163/170/170、Gemma均180，模型失败保留0；超时按完整配对及零分分别敏感性，不新增5%门槛。

报告 `docs/experiment_reports/RQ3_6_Mechanisms_Analysis_2026-09-28.md`：34条件、三数据集及AIOPS合并、root/fault/复杂度、Pratt/dz/Holm、事件组敏感性、修复/破坏、成本，8统计图及10例21份输入输出/4原图。完整artifact审计97996引用/78815文件，12196分数重算一致；仅本次分析执行，不加到续跑。分析脚本与数据在报告assets，原实验源码/输入/配置/分数未改、新增推理0。

三个primary及绑定secondary无校正显著结果。Gemma B3 ALL_ID图文+.1056为探索线索：本实验图文family Holm .0451，三实验34项一起校正 .1279；service/pod有收益而node退化。BIND整体无提升，host增量不稳定。事后rank1对齐分层说明删除摘要可能伤害原正确提示，但不可用gold路由。案例暴露同图文本重复改变层次选择、真实CPU与微小高σ干扰竞争、正确ID但理由/关系错误。建议优先独立复制条件性视觉收益及公开摘要可靠性；不自动启动下一实验，不全局删onset/推广host或RL。三个对应findings已同步，保留资格历史。

## 2026-09-27 — 三个历史去重后机制实验资格通过

执行补记：15:48 UTC启动后台正式队列PID32627；首份结果15:50:34，观察至15:56:02超过五分钟，77份正式结果完整、无失败flag，HTTP200和GPU实际推理正常。下一模型/实验由队列顺序启动。保留运行，按用户要求结束监控；`mechanisms_v2/launch_handoff.json`是启动快照，实时看同目录queue status及各runner log。

最终合同78a10ce7：三focus静态检查、每实验13项单测、三例204请求与每实验180例容量检查通过。GPU三个有界smoke各18逻辑单元全部完成，新增18/16/18共52调用，两个自然同输入复用；完整公开回答和真实输入PNG人工审核通过，无基础设施故障。模型错述类型/时间/关系原样保留，不据此挑条件或修改prompt。取消0/180适用的跨宿主条件后，正式规模12240，累计调用当前10969，上限仍40000；不重新引入空干预。正式授权已登记，顺序G成分→宿主竞争→关系绑定，各Qwen→Gemma。启动后检查五分钟实际推理及新输出，再交由用户监控。详情见RQ3_6_mechanisms_v2_qualification_2026-09-27.md。

## 2026-09-27 — 用户批准历史核对后的机制后继

资格前180例CPU发现HP_CROSSHOST适用0例且全请求重复，取消其T/G两条件，12240正式、54smoke、累计最坏23211。host/peer/dedup有115/175/110例实际干预。原证据保留，修订发生于GPU0调用时，重新冻结及CPU检查；不为凑规模保留无效arm。

完成三个精确设计的实现草稿：G显式字段消融；固定pod锚点下host/peer 2×2及重复去重/跨host peer；固定观测的CALL/DEPLOY/ALL×绑定×T/G。移除通用截图/重述及泛泛补证据复测。12×180×2×3=12960正式逻辑单元、三smoke至多54，连同已耗10917最坏23931；共用预算SQLite。只读复用RQ3.4公开完整context，旗标续跑不重建旧请求，认证探测401/403 failfast。新增共同最坏尺寸预检和全部180例CPU容量检查，避免三例遗漏长图。下一步三focus静态、CPU、smoke，审核后正式启动并确认实际推理五分钟。当前尚未宣称资格通过。

## 2026-09-27 — 第二次历史核对修正扩展方向

用户要求再次判断三个问题是否已被回答。补查旧RQ3 SEARCH开发档案后，确认先前核对漏掉SEARCH13 hosting、SEARCH24整体时间/传播摘要删除、SEARCH31 M z标签移除；Tournament R16实体绑定与RQ3.4 H/K图文析因也必须直接承接。第二问题已有较充分现象证据，不能再泛泛复测；“宿主太多导致错误”的剂量机制尚未证实。第一/第三仍缺特定组成及图文交互，但不应包装为从未研究。完整核对落盘docs/issues/RQ3_6_historical_question_audit_2026-09-27.md。下方12960单元描述降为待修改草案，不是已完成注册；三个v2配置禁止执行，新增推理0。旧队列维持暂停，未启动CPU/GPU测试；后续须去重后重新冻结并资格化。

## 2026-09-27 — RQ3.6旧B停止，重设计与认证故障修复中

用户要求避免重复历史比较，登记超过12000正式调用，静态/CPU/smoke通过后全量启动并观察5分钟。旧B尚未正式调用，已安全停止且保留18次资格记录和五模块源码快照。明确起因为正式shell readiness遗漏Bearer认证，连续401却循环等待；不是模型加载慢。修复采用同一认证探测函数并测试拒绝错误，详见RQ3.6 B资格issues。

新三个实验研究G中诊断派生字段、合格补充证据的宿主/peer竞争、调用与部署关系×观测绑定×图文交互。每实验12条件×180重复暴露case×2模型，合计12960正式单元；三个600秒/18calls smoke。累计调用共享一个SQLite限额40000，继承10917不重置。无训练/attention/test/unused使用，继续保留P0基础证据与数字候选列表。旧B的原图文/换序/截图及MORE复测移除；新绘图接口的校准只服务同实验受控比较，不冒充首次图文结果。代码完成后必须再次进行已执行实验去重审计。

## 2026-09-26 — 跨实验方法能力画像（离线）

按用户要求整合RQ1.1/RQ2.1/Tournament/RQ3.1–3.6 A及已补算CPU基线：
137269逻辑记录、840唯一case、276阶段条件。新报告为
`docs/experiment_reports/Cross_Experiment_Method_Profile_2026-09-26.md`，
附6图、全方法root/fault可读表、各数据集/AIOPS合并CSV、配对Pratt/dz/Holm和
事件组敏感性。仅离线读取历史分数及public graph/metrics；8核提取840例特征
约11秒，汇总约131秒，无新模型调用、preparation、续跑校验或实验修改。

分层统一使用canonical完整标签名称集合，跨service/pod别名单列；保留RQ3.5/6
原生accepted集合分层与逐例对照，7个check病例service→混合的分母变化不改分数。
X网络/操作级改善迹象与node/资源破坏并存；最新S的pod/丢包与node/内存取舍需要
机制字段核查，不能用gold路由。图hop几乎为数据集指纹；Metrics数量不是复杂度。
数据集内关联排除无充分变异/单例高杠杆条件，2088可估、1575支持不足；无Metrics
项通过校正，2项图相关探索性关联不作为部署阈值。全阶段不重复计case、分层N/MRR
回算、来源文件hash一致性及报告链接已检查。未启动任何后续实验或多Agent。

## 2026-09-26 — RQ3.6阶段A正式完成及离线分析

按用户授权分析已完成A，不启动B–D、GPU或subagent。正式运行114.85分钟，
2640调用、2616份完整输出（含13份未知/重复候选零分）、24请求超时、无未解释
缺失；累计10899调用。Qwen超时涉及23例，共同97例，Gemma共同120例。
一次性离线核对19023项artifact hash、2603合法输出分数和1770输入一致性；
未增加任何续跑校验。注册Pratt/dz/Holm，另有事件组、超时和完整格子敏感性。
检验前差值round到12位避免浮点零值/并列误判，原始评分不变。

报告`docs/experiment_reports/RQ3_6_Stage_A_Analysis_2026-09-26.md`含7图及CSV；
复算脚本`RQs/RQ3_6/scripts/analysis/report_stage_a.py`。Qwen W macro=.4867，
Gemma E_S_D_P=.4290，但未确认跨模型统一新方法。Qwen P公共接口对原生T
pooled Δ=.1017、Holm=.0055、事件组=.0097；不是选择器/视觉贡献。S增加根因
关联记录但仍可能丢失关键内存等机制；pod/node取舍和W宿主误归因由输入轨迹
支持为后续假设，不从真实标签生成路由。W Qwen6修复/1破坏、Gemma2/5。
建议收窄B，保持原固定P0/D_P，只研究W资格、范围绑定和同事实图文；未改协议
或启动实验。findings、计划状态与报告索引同步，原结果/评分/配置均保持。

## 2026-09-26 — RQ3.6 A部署与资格通过，按要求停止

实施研究计划的A阶段11条件；B–D依赖阶段结果，未以占位分支进入dispatcher。
五模块+init、只读复用RQ3.4公共context/G图和RQ3.5精确指令块；八核心有界
预取、36并发、done/timeout fail小flag续跑，无全量缓存核验。40000累计调用
不重置，只导入RQ3.5历史8241次。未创建正式授权，未启动正式队列/训练/attention。

三轮独立静态（逻辑、运维、泄漏/语法）后运行CPU：6单元、3例×11×2=66请求，
最终9.914秒。发现并修复deferred import、projection hash序列化和GPU
post-response image_hashes接口。9个已生成Qwen回答保持原prompt/输出/评分，
仅离线完成缺失audit和flag；重测CPU后Gemma完成9次。全逻辑smoke累计18次、
原600秒窗口内558.820秒，18/18完整落盘；未重新抽样或重置时间/预算。

源单位追溯确认P0部分Trace保存微秒却命名ms，独立RQ3.6 adapter仅改unit及
字段名，不改数值/排序/选择/G图；旧代码和结果不变。已登记受影响条件不可
逐字节复用旧请求。完整会话、18回答和3图审阅通过；实体类型误述/图引用错误
保留为模型行为，S输入的literal sidecar数字/关系覆盖不足不作零幻觉宣称。
记录：docs/issues/RQ3_6_qualification_2026-09-26.md及RQ3.6 results/manual_review。
两模型服务已退出；正式A最多2640次待用户授权，未提前部署后续科学阶段。

## 2026-09-26 — RQ3.5 A/B screen60 离线分析完成

用户授权分析已完成阶段。本次不启动GPU、下一阶段或subagent，不改推理、
原始评分与结果。A/B共1440逻辑单元：1437完成、3请求超时；1248次正式新增
调用，192逻辑复用。队列正常completed_screen_ab，未进入check/C/D/test。
新增离线脚本`RQs/RQ3_5/scripts/analysis/report_screen.py`，报告与6张图及样本级
CSV在`docs/experiment_reports/RQ3_5_Screen_Analysis_2026-09-26.md`及其assets。
核对原始输入/输出、8622项必要文件存在性、得分一致性及跨模型/无操作输入。
未进行大文件全量重建。按共同完整病例和原注册family分别报告分母。

主要发现：SIRCL证据+父版指令的macro MRR为Qwen .4006/Gemma .3836，值得
复核但正向增益未获多重比较确认；Gemma换SIRCL指令平均效应-.0692，case
Holm p=.0241、事件组Holm p=.0727，伴随候选数/AC@5下降而非一致Top-1下降。
J只在28/60病例生效，105包全为request、scope为0；实际干预子组也未显示
稳定净收益。12组/10例轨迹复核显示绑定错误、显著症状竞争及模型间相反响应。
建议优先限定范围复核A，暂不自动扩张J视觉化；仅建议，未改注册或执行队列。

离线修正运行summary把entity类型表当granularity的分层错误（不改变评分）；
另记录P0/SIRCL时长投影差异的实际例子，限制纯选择器归因，保留冻结结果。
静态检查通过；报告链接和主要数表复核。历史qualification过程保留如下。

## 2026-09-26 — last-GC 时钟修复、补验通过并重启原队列

用户批准上一轮提出的遗漏GC时钟修复及4次补验。采用RQ3.5-local显示适配，
只转换两个均值，沿用原公共原点，不重新选择证据、不改标准差、不重做准备。
新输入guard覆盖last-GC；原始大内存/计数字段不按时间处理。静态及28项单测
通过，正在做120请求CPU回归、60例输入范围核对，再进行两模型共4次补验。
补验成功并检查实际输入输出后才恢复原A/B screen60；原38份结果已清除，
不再重复删除。其他RQ、模型配置、attention关闭与40000总调用上限不变。
结果：28单测、120请求CPU回归通过（25.00秒）；60例×20条件一次性范围核对
通过（107.00秒），仅17例×3个SIRCL条件改变，1149份输入不变，容量通过。
4次GPU补验全部完成（213.02秒，stop，非法ID为0），实际输入及完整输出
审阅通过。A/B正式队列已按原范围从零启动，启动前1440单元全pending。
原38次消费仍计数，重启前累计6993调用。没有新训练、attention或范围扩展。
详细协议见DD-RQ35-05，运行证据在`repairs/gc_clock_v1/`及formal_queue_status。
交接确认：队列PID37481已进入A/Qwen正式推理，新完成5/360，36请求在途；
GPU约85%，无新增错误。60份准备直接跳过，准备进程约5秒。停止人工监控，
后台队列继续；后续状态以formal_queue_status和小型done/fail标记为准。

## 2026-09-26 — 获批无损输入补验与38份正式结果清除重跑

用户批准12次定向GPU补验，并要求将此前38份正式结果全部清除后从头跑。
执行范围保持原A/B screen60，不扩至check/C/D/test。补验仍用原三例、两交叉
条件、两模型顺序运行，600秒总窗口；A累计smoke上限24→36，总调用不清零。
仅补验调度代码新增，先核对120请求身份完全一致。补验通过后删除旧正式输出、
完成标记和复用缓存，保留preparation、测试、其他RQ和累计消费记录；删除清单
及最终状态随后记录。此条是授权/计划，不提前宣称补验或重启完成。

结果：26项CPU测试、120请求身份核对通过（24.62秒）；12次补验在226.149秒
内全部完成，完整会话已检查，非法候选0。但实际输入审阅发现SIRCL路径遗漏
`istio_agent_go_memstats_last_gc_time_seconds`的相对时钟转换：补验2请求受影响，
screen中17例AIOPS-2022的3个SIRCL证据条件受影响。不是已证实读取注入时间，
但违反相对时钟契约。A标为failed_model_input_audit，未启动正式队列。
原38份正式结果已依用户指令全部删除：537文件、11,710,842字节；SQLite中的
答案缓存一并清除，消费记录保留，累计6989次。保留全部60份准备和补验记录。
最小下一步是RQ-local时钟投影修复/CPU检查，预计需另获4次定向GPU补验授权。
详情及删除清单见RQ3.5 issues和`repairs/formal_reset_20260926/`。

## 2026-09-26 — RQ3.5 全面逻辑审查及无损输入修复

用户授权修复并全面检查。覆盖五个功能模块、配置/队列及继承的请求、评分、
异步写盘和续跑边界。四个交叉条件改用分区域、逐字保留记录的文本块，消除
逐行JSON重复键与转义；未删除证据、改采样或扩大context。触发case的
E_S_D_P由Qwen38418/Gemma40691降至29471/31687输入tokens，均低于32768。
额外修复直接runner的基础设施fail跳过、模型选择和暂停提交边界；缓存重复
reference p95计算且计数等价；补齐已注册分析的macro、成本/故障分层、共同
配对集合和事件组敏感性。修复发布最终标记后置，可从中途发布恢复。

Ruff、格式及shell静态检查通过；24项CPU测试通过。60例×19条件×两模型
共2280项容量检查零失败，用时139.87秒；三例120请求集成回归通过，其中
24个交叉请求按预期改变，96个原生及B/C/D请求身份不变。最终核对还清除了
A资格中继承自上次补验的旧授权/已完成报告，避免将旧补验误读为新输入通过。

38份已完成正式结果全部保留：26份交叉结果不用于新版本，12份原生结果可复用；
60份preparation全部保留。普通续跑仍读小型状态及done/timeout flags，不加入
全量重建或重hash。A等待12次定向GPU补验的另行授权，B/C/D资格按请求一致性
证据保留；此次新增GPU调用为0，未恢复正式队列。详见
`docs/issues/RQ3_5_qualification_2026-09-25.md`及`repairs/lossless_blocks_v3/`。

## 2026-09-26 — RQ3.5 注销后恢复检查发现输入超限，尚未重启

用户要求从注销中断恢复、确认启动后停止监控。检查发现上次队列实际记录了A的
context超限退出，38/360 Qwen单元已done，60/60 preparation保留，无存活服务。
首个pending INC-1E6DCFC0A453的E_S_D_P输入Qwen38418/Gemma40691 tokens，
超过32768输入余量；原生SIRCL_IDS为29824/32035，能够装下。逐行JSON封装
增加了输入开销，并非原生证据必然超限。仅对该case做CPU tokenizer诊断，未调用
模型、修改源码、重做准备或重核验已完成结果。直接续跑会复现，因此未启动；
无损封装修订涉及模型可见输入，需确认后另行修复和核验。已记录于RQ3.5 issues。

## 2026-09-26 — RQ3.5 A/B screen 正式队列授权

用户要求启动并监控3分钟后停止助手监控，后台继续。队列限定来源准备/审计及
A、B的screen60：每项6条件×60cases×2模型，最多1440次正式调用；Qwen/Gemma
按实验顺序运行。不自动开启check120、C/D、test或新事件。复用3例准备，其余
57例仅增加所需索引；最多8个独立物理核心worker。已完成和timeout fail均读flag
跳过，其他基础设施fail需诊断；不做全量结果重建/重hash。正式模型启动前跳过
已经终结的model phase；SIGTERM停止提交、排空后释放自有服务。

新增RQ-local后台入口和小型状态文件；一次性运维激活保存旧源码/注册/资格，
检查既有函数AST与120请求身份一致后继承四项smoke，无新增smoke调用。实际启动
状态以`RQs/RQ3_5/results/outcome_linked_v1/formal_queue_status.json`为准。
静态检查、17项CPU测试及120请求身份比较通过；当前契约为
`d353320098f0020d28f3d2605f657f7d31a6e2004eb35b1f94364a1338cb79a8`。
14:44:09 UTC启动后台队列PID13906，监控约3分20秒：60/60准备完成、来源审计
正常退出，已进入A的Qwen模型启动阶段（服务PID14813），未见启动错误。
此时尚不能宣称正式推理已稳定产出；按用户要求结束助手监控，后台继续。
无训练、attention或其他项目进程操作。

## 2026-09-26 — RQ3.5 A 定向补验获授权

用户批准候选段去重后的6次GPU补验。仅原3个qualification cases × 两模型的
E_P_D_P，顺序运行，共用600秒窗口；原A的18次调用保留，同scope累计上限24，
大RQ计数不重置。新增显式补验调度及范围/预算测试，CPU核对科学输入不变后执行。
其余12份A请求及B/C/D保留，原记录不覆盖。无正式实验、训练或attention。
授权及补验产物位于`RQs/RQ3_5/results/outcome_linked_v1/repairs/candidate_once_v2/`；
结果待执行后登记，不能提前声明完成。

完成：静态检查、15项CPU测试和120请求身份一致性检查通过（21.35秒）；补验
Qwen3＋Gemma3在216.813秒内全部完成，均stop，无超时、基础设施失败或非法输出ID。
逐份确认只删除重复候选记录，其他输入、候选、schema和模型配方不变；全部会话
包含完整输入输出。A引用6新＋12原记录，B/C/D资格保留，四项当前均passed。
大RQ累计6939调用；原smoke不覆盖。reason里的类型/数值归属和因果过推问题按
模型行为保留，不用smoke成绩调参。启动警告未阻止两模型完成，无runtime修改。
自有GPU服务全部退出，未启动正式实验。详见RQ3.5资格问题记录及repair report。

## 2026-09-25 — RQ3.4四阶段完成与离线综合分析

正式队列16:05:20（America/Toronto）正常完成。3720逻辑单元＝3708 done＋12 request timeout；完整请求复用后3460唯一完整回答＋12超时＝3472次新正式调用。17份完整回答模型输出失败保留原零分，均非重试对象。原输入、图像、评分和配置未修改。

用户要求详细分析。新增 `docs/RQ3_4_Results_Analysis_2026-09-25.md` 及assets离线脚本、完整CSV/表格、八图、原G例图与conversation引用。共同病例配对、Pratt-Wilcoxon/dz/Holm、事件组敏感性、repair/break、候选提名、故障/层次/直接遥测覆盖、reason冲突告警与token成本分别分析；核对真实输入干预和六个命名case的原回答，非随机例子不作为错误率。

主方法check三数据集macro MRR为Qwen0.4219/Gemma0.3611，TPV0.4163/0.3458、MORE0.4414/0.3750；主要比较均未通过Holm。不加K的Qwen0.4468仅略高于MORE，未事后升格冠军。关系可核验与诊断相关性不同，部分类型/数值告警减少但MRR不稳定；选择性G视觉主要有排序修复线索。screen/check均已暴露开发资料，未达到独立高MRR目标。四份findings登记正式结论，历史资格过程保留。不启动新实验、训练、子agent或新的GPU调用。

## 2026-09-25 — 风扇曲线测试结束后恢复RQ3.4

用户说明暂停是为完成风扇curve测试，现明确恢复。原队列已安全paused，runner/vLLM均退出；恢复前GPU44°C、无计算进程。原60例screen准备全部保留；契约两模型360单元、因子Qwen600单元均有终结记录，因子Gemma停在37/600，无fatal。按原 `scripts/formal_queue.sh` 在独立session恢复，PID51831，日志 `RQs/RQ3_4/results/integrated_v1/logs/formal_resume_1790360297921435940.log`。跳过done/fail，不重做准备或大文件核验，不重跑smoke；Gemma剩余563单元及后续登记阶段继续执行，check120仍受原推进规则约束。未改代码、模型、输入、评分、GPU或风扇设置；停止助手监控，后台继续。

## 2026-09-25 — 用户要求立即暂停RQ3.4

用户在因子实验切换到Gemma后要求立即暂停。已向已核实归属的队列PID29135与runner PID50396发送SIGTERM，停止新提交并排空在途请求；由原supervisor清理自有vLLM组，不杀其他项目进程。此前契约两模型360单元及因子Qwen600单元已终结，其中3次request timeout按原规则保留fail。当前暂停不修改模型、输入、评分、源码或已完成结果；不允许自动继续后续阶段，需用户明确恢复。最终暂停状态和计数以 `RQs/RQ3_4/results/integrated_v1/formal_queue_status.json` 及当前模型progress为准。

## 2026-09-25 — RQ3.4正式队列获授权

用户授权正式运行并要求启动后停止助手监控。增加RQ-local后台调度，沿用已有prepare/run/analyze与40000累计计数；前三项screen60完成后，严格按原Qwen推进规则决定check120，不扩大实验矩阵。8物理核心CPU准备、Qwen/Gemma顺序运行、无attention/训练。启动前执行权限变更有独立归档及120个科学请求等价检查；旧smoke/失败/回答不覆盖。状态和日志存 `RQs/RQ3_4/results/integrated_v1/`，尚不在本条提前宣称已发起正式模型请求。运维授权与恢复方式详见DD-RQ34-07。

启动确认：静态检查、48项CPU测试及120请求身份等价全部通过；已有编译/选择/推理/评分函数AST不变，正式运维契约为 `bbab76d1f70d479ebdb27cd5d274282ffb51e0350f4efab86f734a99392abdf9`。普通shell后台首次未保留进程、日志为空且零调用，改用独立session可靠脱离终端；正式队列PID29135，准备PID29145，8个worker已启动、分别固定不同物理核。复用3例准备，补57例screen准备后自动推理；启动核查时尚未加载GPU、无新报错。助手按要求停止监控。启动前累计3395调用，最大追加正式3480；不新增smoke。入口及日志见运行根目录 `FORMAL_LAUNCH_20260925.md`。

## 2026-09-24 — 相对时钟定向 GPU 补验通过，未启动正式实验

补验入口曾把clock模式误传为旧布尔repair，Qwen启动后、请求前退出，0 calls；修正并加driver测试，45项CPU回归和120输入等价检查通过。失败105.31秒和日志保留并计入契约阶段600秒，不重置预算。之后契约6、因子4、图文6次新调用均完成，各209–211秒；锁定2单元同输入复用，0新调用。加54个未改输入引用，共72逻辑单元、36对跨模型输入核查通过；累计3,395 calls。16新回答全stop、无截断/infra失败；1非法候选、6份回答12处类型误称及其他reason错误保留为模型结果，不重试或改评分。详见`RQs/RQ3_4/results/integrated_v1/repairs/relative_clock_gpu_v1/review.md`。四项当前qualification已通过，原失败/flags/results不覆盖，所有自有服务退出；正式execution_enabled=false，无训练/attention。

## 2026-09-24 — 相对时钟定向 GPU 补验获授权并登记

用户授权补验18个改变输入的逻辑单元，不启动正式实验。四项独立smoke按原顺序、每项600秒；新增最多18次，预计两项完全相同请求可复用后实际16次。独立`repairs/relative_clock_gpu_v1/`保留补验输入输出，共用原calls.sqlite；原报告、flags和结果不覆盖，54个相同输入完成单元只引用。新增入口与复用检查经44项CPU测试、120请求身份等价检查通过；源码变化仅补验调度、相同模型/case/请求复用及测试。首次setup后只修正import静态格式，该无GPU的setup快照保留。协议详见DD-RQ34-06。结果待补验后登记，不提前宣布通过。

## 2026-09-24 — RQ3.4 时钟输入修复，CPU 通过，停止在 GPU 补验前

用户授权修复绝对时钟输入。新增 RQ3.4-local `relative_clock_v1`：三类来源明确的秒时钟共用公共 case-local 原点，仅平移模型可见值，保留前后差、跨实体差、MAD/std、选择统计与原始数据；未知时钟语义在请求前报错。真实回归发现先前遗漏的 SIRCL `container_last_seen`，三个 SIRCL 条件共同适配均值、不改标准差；旧实验代码及结果不动。

42项测试、Ruff/shell检查、三个case的120请求CPU回归通过。96请求不变、24改变；12组P/H证据集合、TPV/MORE请求和G图均不变。已执行smoke受影响18逻辑单元（契约6、因子4、图文6、check2），四项状态为cpu_fixed_gpu_pending，不能沿用旧输入资格。缓存修复与检查53.64秒，CPU资格本身16.15秒，未重新跑全量preparation。原输入、失败CPU尝试、原回答和partial均保留；本轮0模型调用，总计仍3379，无训练/attention/正式运行。详细依据及产物：`docs/issues/RQ3_4_qualification_2026-09-24.md`、`RQs/RQ3_4/results/integrated_v1/repairs/relative_clock_v1/`。本轮修复后停止，尚需有界的定向GPU补验。

## 2026-09-24 — 第三项授权补验完成，输入复查发现时钟字段阻塞

用户批准一次性≤16新增calls／≤600秒补验，仅第三项，同scope累计上限25，不重置计数。新增显式repair入口与授权约束；36项CPU检查、120份完整请求身份等价通过，操作性源码迁移单独保存。第三项18单元（16新＋2缓存）250.50秒完成；原失败及7份partial归档，两份原output字节不变。总79次新请求＝72完成＋7中断，承接历史3300次后计3379。无新Z3/infra错误，自有服务退出，没有正式实验。

完整回答/输入审阅发现新阻塞：追加观测暴露 `container_start_time_seconds=1647145400.0`，属绝对容器启动时钟，非已证实根因/注入时间泄漏。全部72完成单元中12份受影响（同一AIOPS2022 case：因子4、图文6、check2），后三项资格设为blocked_input_privacy；原运行报告不改写。需要语义感知的相对时钟投影或登记排除，保留restart信号，修复后按真实输入变化定向资格；本次GPU授权已用尽，未自行再跑，尚未修改科学输入。机器清单`RQs/RQ3_4/results/integrated_v1/smokes/absolute_clock_input_audit.json`，详见`docs/issues/RQ3_4_qualification_2026-09-24.md`。回答中的类型/因果推断错误按模型结果保留，有限核验不代表全面正确。

## 2026-09-24 — RQ3.4 合并路径实现与资格测试

用户授权完成代码、CPU 回归和 GPU smoke，未授权本轮自动正式运行。新增五模块内的 P/H/K 选择、scope 对照、真实可见事实编译、两模型共同 token 预算、独立回答核验、flag-only 恢复及分阶段分析入口；保留父版源码和全部历史结果。数值与实现边界登记 DD-RQ34-03。新命名空间 `RQs/RQ3_4/results/integrated_v1/`，正式 execution_enabled=false。

Ruff、shell 语法和 registration 通过。首次CPU资格：34项单元检查、三个真实主数据集 case 的120个 arm×model输入编译检查通过，总34.07秒；新增准备15.43/16.69/19.47秒，各绑独立物理核心，仅补读metrics，复用完整公共池／旧TPV图。P/H真实改变内容；同图复用和图文alias检查通过。查看三个原G图、追加观测、关系和完整conversations，不借资格调整画法。

契约和因子smoke各18/18完成（232.63/243.18秒）。第三项发起9次后Z3段错误，内核日志定位libz3；两份回答完整落盘、七份partial保留。默认context即使用短锁也可能在锁外析构；改每个核验器独立context、全部AST显式绑定，并记录子进程exit code。源码迁移归档，修复后35项CPU测试（含384次并发创建销毁）通过；120个完整请求身份不变，190次真实回答回放verdict一致。第四项在修复后18/18完成（250.97秒）。共63次新请求，含失败9次；已承接3300次历史计数，总3363。七条遗留started明确改为interrupted，不自动重试、不拼接partial。

第三项原failed状态不改写；完整补验需最多16次新请求，超出本项18-call上限，已请求一次性例外，未授权则保持待补验。没有全量实验，没有新attention；所有自有测试服务已结束。详细问题及下一步见 `docs/issues/RQ3_4_qualification_2026-09-24.md`。三个smoke通过不等于方法有效。

## 2026-09-24 — 原诊断路线与自动推理合并登记（未运行）

用户要求合并下一轮研究。RQ3.4 不再仅聚焦核验：输出／候选契约单独校准；证据优先级P、宿主—实例scope H、可核验关系K做全2×2×2并保留TPV/MORE；固定P1H1比较图文与普通重述；达到预登记MRR条件后才在旧check120锁定复核。主方法预先固定，避免逐阶段换冠军；MRR与解释可靠性分开，核验不改原排名。

登记 `RQs/RQ3_4/configs/integrated_round_v1.json` 与三份descriptions；四份新findings明确未运行。首轮2,094计划calls，条件式后续1,458，最多3,552，不叠加旧738-call聊天建议，不重置大RQ预算。资料均为已暴露eval开发组，不打开新test。此次只改设计文档和登记配置，未改实验实现／旧结果，未运行CPU实验或GPU。已完成的20项CPU核验回归不作为新GPU路径资格。完整说明同步到最新跨RQ计划，下一步为实现和资格测试。

## 2026-09-24 — RQ3.4 事实核验 CPU 可行性

用户授权推进下一步并推荐 CARS；在 RQ3.3 阴性开发结束后，选择先实现公开事实核验而不是扩大旧方法。新建 RQ3.4 的三份协议、五功能模块和 CPU 审计入口，旧 RQ 代码／结果／评分不动。文献核查包括 CARS（ICML 2026）、SAT-LM（NeurIPS 2023）和 LINC（EMNLP 2023 main）；不把精确约束采样或事实自洽当作 RCA 正确性保证。

最终审计 120 cases × 5 arms × 2 models：1,197 个完整回答、3 个原超时有明确记录，约 3.57 秒完成核验和汇总。14 份候选契约错误与原 scorer 检测重叠；247 份解释有字面断言冲突候选，不能称已确认幻觉率。抽查发现量的绑定歧义，后续必须保留 unknown／人工式复核。20 项 CPU 回归及 Ruff/语法检查通过；零模型调用、无训练。详细协议、独立审计版本、实现修复和 findings 位于 `RQs/RQ3_4/`，最终结果 `results/claim_audit_v4/`。下一步是强基线上有对照的事实／关系编译研究，尚未开启新 GPU 实验。

## 2026-09-23 — RQ3.3 超时配置兼容修复并续跑

用户授权修复20:20校准退出。仅允许完整配置hash精确证明的timeout1800→300变更，保留模型、采样、输出等其他差异的fail-fast；增加GPU加载前全部120条历史runtime元数据检查（111相同、9仅timeout）。51项CPU回归及Ruff/shell检查通过；定向CPU核查15.90秒，旧smoke90个完整输入不变，故障case双模型六个SC输入均编译通过。60份准备物与1份已有正式结果保留，无新增GPU smoke或全量重新准备。

显式契约承接及旧资格快照位于`RQs/RQ3_3/results/witness_v2/contract_migrations/calibration_timeout_only_v1/`，新契约`e0ab9bb7e75bbdda46d0bad8959e6e57ef30b54f1f69307590b46dc5247fdafe`。20:41:03重启队列PID105361；恢复预检及完成flag读取后约0.5秒即进入模型加载，未重建已完成请求。启动观察确认进入Qwen校准，已完成7/240逻辑单元（含原1份），5次正式调用完成、28次已提交处理中；此前故障case的GUIDE_FIXED/SOURCE_FIXED已有新结果，未再次触发runtime差异错误。日志`logs/formal_queue/supervisor_20260923_204103_timeout_compat.log`。模型结果未用于调整实验，继续既定队列，本轮启动确认后停止监控。

## 2026-09-23 — RQ3.3 队列准备中断与身份适配修复

正式队列尚未调用模型，在第19份准备物遇到旧parent数字ID与当前公开node/pod元数据冲突。修复仅落RQ3.3：兼容缓存复用，绑定不一致的case定向重建；历史SC校准/TPV_BRIDGE保留原输入及原评分映射。45项CPU回归、故障case双模型18个编译检查、旧smoke90个请求相等性检查通过；18份准备物保留，定向重建1例48.08秒。未新增GPU补验调用，未重跑/修改旧科学结果。源码迁移和原资格快照在`RQs/RQ3_3/results/witness_v2/contract_migrations/public_metadata_identity_v1/`；踩坑记录在`docs/issues/RQ3_3_implementation_review_2026-09-23.md`。用户授权修复后续跑剩余准备任务及登记的正式队列；不新增恢复时批量校验。

20:12:34本地重启队列PID93316，启动核查确认8个worker各绑定不同物理核心，正在处理screen剩余41份准备任务，已有19份跳过。状态入口`formal_queue_status.json`，日志`logs/formal_queue/supervisor_20260923_201234_identity_repair.log`（均在`RQs/RQ3_3/results/witness_v2/`）。累计调用仍139，含53历史失败/补验尝试；启动时没有新错误。准备结束后自动进入已登记顺序，本轮按用户要求启动后停止监控。

20:20再次退出的只读诊断：preparation已60/60，Qwen校准TPV_BRIDGE已完成1次；下一SC历史请求被完整配置hash检查拦截。120条manifest中9条Qwen历史配置仅因已授权的timeout1800→300改变hash（用当前配置单字段还原精确验证）；不是模型/证据变更或GPU OOM。原smoke三例均未覆盖这9例。当前尚未修复/重启，60份准备物和1份正式结果保留，累计发起调用140。详见同一RQ3.3踩坑文档最新条目。

## 2026-09-23 — RQ3.3 CPU性能与日志单位修复（资格调试）

原消息日志分组产生24万级候选；JSON键顺序/动态参数进一步碎片化模板。改为完整源行索引绑定的模板级phase统计，保留实体、状态码、数值摘要及分母；新Witness输入投影重新资格，旧正式结果不改。进一步修复P0_MORE重复tokenization（有认证边界的精确缓存）、全量Denum平方级去重、Trace反复全表扫描，以及CPU/smoke样例不一致和smoke只取旧基线的问题。数据原件、父版源文件、推理配方不动。

最终三例CPU回归106.58秒通过：AIOPS-2022从超过27分钟未完成降至89.01秒，AegisLab377.95→44.70秒，AIOPS-2025 19.88→9.73秒；包含对照准备，不是推理或系统端到端latency。32项单元检查、80项真实输入检查通过，另31项注册条件不适用；两模型各321段文本的精确缓存与完整分词一致。三例原TPV输入、父版追加候选、Trace群体及P0_MORE选择保持一致。冷日志聚合、部分截图条件不可执行和缺失来源校准manifest仍需明确处理；本轮没有GPU调用或正式实验。详见`docs/issues/RQ3_3_implementation_review_2026-09-23.md`及本RQ协议，资格产物位于`RQs/RQ3_3/results/witness_v2/`。

This is the only project-wide devlog. It keeps decisions that still affect the
current study, important reversals, validity changes, and reproducible artifact
locations. Repetitive operational narration and superseded execution plans were
removed on 2026-09-15. Detailed experiment records remain under each RQ's
machine-local `results/`; settled RQ1.1/RQ2.1 findings and retained incident
records are under `docs/`.

## RQ3.2 completed-run analysis — 2026-09-22

Offline report: `docs/RQ3_2_Results_Analysis_2026-09-22.md` (10 statistical
figures and 2 original dashboard examples). Current-task reconstruction gives
27,280 terminal units: 26,995 scored outputs including 346 model failures,
129 timeout causes and 156 non-applicable interventions; one noncurrent
output excluded, nothing deleted. SC restores node telemetry but does not
consistently beat strong baselines; full vision loses to the same SC textual
carrier; targeted deletion provides limited evidence dependence. Actual-input
audit also identifies text NO_GROUPING no-op and control/guide mismatches,
recorded in `docs/issues/RQ3_2_issues.md`. All original experiment artifacts
and scores are unchanged. No inference, training, pipeline repair or rerun
was started. Detailed per-RQ log remains with the formal run.

## Next research plan — 2026-09-20 (documentation only)

The user-confirmed RQ3.2 SignalCover plan is saved in
[CanvasRCA_RQ3_2_Research_Plan_2026-09-20.md](../docs/CanvasRCA_RQ3_2_Research_Plan_2026-09-20.md).
It uses tournament case-pattern evidence and RQ3.1's asymmetric loss/addition
of root-associated metrics to motivate P0 backbone retention, mechanism/level
coverage and bounded contrast completion, not an ensemble of past winners.
The four planned experiments separate selection, representation, mechanisms
and locked generalization; core maximum is 28,432 calls within a 40,000-call
RQ3.2 ceiling, not a new lower hard cap. Existing test360 becomes explicitly
exposed regression evidence; an unused-event audit may support up to 30 new
cases per primary dataset, without assuming unused means untouched.

This session only writes the plan and this status entry. No RQ3.2 source,
executable registration, preparation, CPU/smoke qualification, inference or
training has been performed. Prior source/results/model recipes and data
manifests remain unchanged. The plan contains the supplemental count sources
and marks the metric-coverage/MRR associations as descriptive, not causal.
RQ3.2 is the next research direction; older dated RQ3.1 execution statements
below describe their historical scope and are not RQ3.2 execution authority.

## Historical authority — 2026-09-16

- Research-plan revision 8 is implemented in `research_v2.json`: direct table
  contrast X_C_TABLE, its screenshot control and table budget/load tests;
  no engineer/user study or mandatory independent annotation. The increment is
  2,680 calls; formal 26,360; cumulative allocated core 26,432; reserve 13,568
  within 40,000. Static checks pass; CPU/smoke/model execution remain pending.
- Formal preparation did not complete: it stopped after 141/480 durable contexts
  when the old global identity scan mistook the public trace operation `set` for
  a raw entity. The successor validates TRC-L's numeric service column while
  retaining operation semantics. No formal inference call started. Existing
  context bytes are retained and may resume only between the pinned predecessor
  and successor implementation/config hashes; later changes do not inherit the
  exception automatically.
- RQ3.1 uses the user's 40,000-call ceiling. The narrower agent-drafted limit
  has been removed from active configuration, runner/recovery defaults and
  plans. Its independent user provenance was not established and must not be
  asserted. The matrix remains 23,680 formal calls; cumulative core including
  qualification and prior 18 calls is 23,752; reserve is 16,248. The earlier
  cap had not stopped a model call, but did restrict planned repair headroom.
  No inference or tests are authorized by this correction.
- CanvasRCA runs locally only. The `_nibi` worktree name is historical; no new
  Slurm/Nibi jobs or API inference are authorized.
- The first paper uses a frozen one-stage RCA Solver and studies evidence
  selection plus verifiable visual organization. Composer SFT/RL is deferred.
- RQ480 is the repeated-exposed method-development/selection eval set. It is
  not optimizer training data and is not an untouched test set.
- The registered data roles are train300 / eval480 / test360 / unused1403.
  Test contains 120 cases each from AIOPS-2022, AIOPS-2025 and AegisLab; all
  RE2 cases remain in eval. The former AIOPS validation140 is included in test
  with its exposure provenance retained. There is no active validation split.
- The current research plan is
  `docs/CanvasRCA_Research_Plan_2026-09-15.md`, revision 8. The old static pause
  was superseded by later CPU/smoke/formal authorization; runtime artifacts, not
  stale narrative status, determine actual progress. Current work is plan-only,
  then stop. New controls still require versioned implementation, registration
  and qualification; no existing smoke proves their behavior.

## 2026-09-16 — direct textual contrast and an affordable evidence chain

User identifies "why not use text for contrast?" as a central validity risk,
and has no resources for a participant study. Source inspection confirms that
X_C emits bundle references and a separate observation catalogue, not an inline
comparison table. Plan revision 8 preserves it and proposes X_C_TABLE on eval480
and test360, its exact-text screenshot on the fixed 100-case subset, and table
budget/load counterparts. Increment: 960 + 720 + 200 + 400 + 400 = 2,680 calls.
No active source/config/request or result is changed by this decision.

Visual claims must face the direct text comparator; benefits from selection,
pixel transport and visual organization are evaluated separately. Planned final
Holm family expands to 24 comparisons, with explicit secondary screenshot and
paired budget/load change-score families. Method choice remains eval-only;
test never selects the weaker comparator. Old outputs stay versioned and are
reused only when their complete contracts match.

Participant recruitment and mandatory two-annotator review of 600 responses are
removed from the paper's required work. Automatic source-bound assertion checks
report supported/contradicted/unsupported/unresolved cases with coverage and
empty-denominator handling, not complete reasoning quality. Controlled removal
measures dependence on root-associated observations, not hidden causal reasoning.
Human productivity and MTTR remain outside current claims. Author engineering
inspection of images/code is still required and is not a user study.

Decision is recorded in the latest research plan and DD-RQ31-09 in the RQ3.1
experiment description; statement and qualitative roadmap agree. This session
only edits documentation and checks its consistency. No new literature result,
model result, human annotation, implementation or qualification is claimed.
Stop after this handoff as requested; do not automatically implement the additions.

## 2026-09-16 — RQ3.1 independent per-case branches; static-only pause

User rejected the shared MET-Z/TRC-L/LOG-R/Denum candidate-pool prerequisite.
X now starts from canonical per-case public tables and graph, with its own
signed metric summaries, complete trace-group union, identical-message log
groups and concrete topology. Shared loading does not run analyzer selection.
P0/SIRCL retain their own analyzer branches; P0 calibration no longer substitutes
X statistics. Same-X representation twins remain controlled. Source-policy
comparisons include extraction, reference partition and selection, not only
ranking. Standalone observations can use the quarter-budget coverage reserve
without being mislabeled as competing-root bundles.

Formal preparation from the previous version was stopped and its two newly
generated directories removed on user request before any formal model call.
Canonical per-case data, all previous RQs and previous smoke evidence remain.
No CPU test, preparation, rendering, smoke or inference was run in this revision.
Future qualification must use the changed implementation/config hashes.

Recomputed allocation: formal 23,680; prospective qualification allowance 54;
prospective core 23,734; historical initiated calls 18; cumulative core 23,752;
hard ceiling 40,000; remaining unallocated repair reserve 16,248. Original Solver
recipes and disabled-attention setting are unchanged. Detailed contract and
static review live in `RQs/RQ3_1/descriptions/`.

## 2026-09-16 — implementation integrated; static-only handoff

Unified source-bound preparation, evidence selection, P0 calibration, all
registered request variants, bounded inference submission, exact-request reuse,
retry artifacts and two-model summary reconstruction. Removed obsolete runtime
mock/fallback paths; the mocked CPU execution helper lives only in tests.
P0 calibration now uses the same current public projection as X while retaining
parent selection; original baselines are untouched. Calibration effects must
be reported separately from selection effects.

Static checks passed for 44 Python sources, 233 local imported symbols, two JSON
configs, six shell scripts, Ruff F and changed-code import ordering, plus
`git diff --check`. The five modules plus init occupy 5,985 nonblank/noncomment
lines (docstrings included). Details are in
`RQs/RQ3_1/results/team_stage1/static_review_20260916.md`.
These checks do not execute tests or establish runtime correctness. Earlier
68-test CPU evidence predates these changes; candidate budget 96 and the
interrupted capacity audit remain unqualified. No subprocess experiment was
launched, no test telemetry opened and no shared model recipe changed.

## 2026-09-16 — active work switched to one agent

The user stopped the multi-agent workflow because of token overhead. A, B and C
had already persisted their source and CPU evidence; all child sessions are now
terminal/interrupted and must not be resumed automatically. One primary agent
inherits their work and will perform the remaining representation correction,
integration, qualification, experiment operation, statistics and stage review.
D and E were never started. This operating change does not weaken their former
quality gates: complete-result statistical analysis and stage-level academic
critique remain required, but are now performed by the primary agent.

At the switch, no GPU/model/formal experiment was running. A budget-96 CPU-only
evidence qualification process launched before the switch was stopped on the
user's subsequent pause instruction. It completed two Aegis eval cases but did
not write its complete summary; those partial files are non-authoritative and
may be resumed or rebuilt without any model call or test access. The integrated
RQ3.1 CPU suite passed 68 tests. The source package is not yet stage-complete because the standard
semantic budget remains unfrozen and processor-space readability/display-load
corrections still require final inspection. Therefore smoke and formal inference
remain unauthorized.

## 2026-09-15 — autonomous RQ3.1 team started

The clean worktree at commit `de3027724` contains a completed data registration
and five passing split tests, but no implemented contrastive RCA experiment.
No project-owned inference/training process was running at handoff. A (Sol/high)
owns evidence pools, complete contrast bundles and budgeted selection; B
(Sol/high) owns same-fact representations and a local renderer; C (Luna/high)
owns registration, execution, recovery and integrity. Their first assignments
end after runnable CPU-tested interfaces and written handoffs, without model
calls. The leader owns integration and the current protocol. D (Sol/xhigh)
starts only on complete, writer-drained experimental results; E (Astra/xhigh)
reviews each completed major stage and remains read-only.

Major stages: integrated method/protocol and CPU/visual checks; complete eval
development with method selection; mechanism/robustness evidence; locked test
and final synthesis. E reviews every stage; D precedes E for empirical stages.
Stage artifacts go under `RQs/RQ3_1/results/`, preserving the single-plan and
single-devlog cleanup. The requested final target is primary-Qwen test MRR
>=0.65 with both AIOPS datasets >=0.60, plus the complete publication evidence
chain. Target attainment must be observed, not promised. All planned controls,
negative results and test exposure provenance remain reportable. Test is not a
repeated tuning loop, and the current total budget remains 40,000 calls.

The user also requires night-time shutdown/resume. Team assignments and
incremental handoffs are durably recorded in
`RQs/RQ3_1/results/team_stage1/`; experiment recovery must pass interruption
tests before model execution. No assumption is made that an agent session
survives a reboot. Recover from saved source/artifacts/next commands and inspect
real process state before resubmitting incomplete targets.

The leader's first integration review found substantive gaps despite passing
component tests: candidate-pair semantics, residual network identifiers,
representation duplication/capacity, unknown values rendered as zero, and
experiment-matrix/resume gates. A/B/C received bounded corrections before any
model request. Stage 1 is not accepted; D/E remain unstarted. The source-level
review and each member's recovery handoff are in `results/team_stage1/`.
The experimental protocol now fixes method selection, named Holm families,
failure denominators and the `T_COMPACT` versus `X_C` distinction before new
outcomes. The sample budget is provisional, not a formal capacity decision.

On 2026-09-16 WSL restarted during the team's CPU repair stage. Live process
and agent inventories confirmed the old workers were gone, not merely slow.
All source edits and A's partial semantic-repair handoff survived. The leader
restored A/B/C from disk under the same file ownership and model settings;
there was no model call or running scientific experiment to duplicate or
invalidate. `team_state.json` records current recovery-agent identities.

The second review did not accept the first C integration: arm mapping, shared
RCA prompt, target/control removal, time-alignment/re-anonymization semantics,
and bounded supervision still had confirmed errors. Scientific intervention
implementation was reassigned to A, prompt/render changes to B, and execution
to C. All remained CPU-only. The first valid-looking capacity gallery also
retained excessive empty single-edge panels; source PNG success was not treated
as proof of VLM readability or a reason to freeze an undersized evidence budget.

The next CPU pass compacted comparison tables and shared trace/topology views
without deleting selected facts. All three saved 128-budget samples now fit;
Gemma's actual CPU image processor was inspected as well as source PNGs. A
broader nine-case CPU check is still required before budget registration.
The leader preregistered a 10% character-scale tolerance for otherwise matched
private removal controls, and complete-bundle display-load prefixes with
explicit overshoot/degenerate-level accounting. Duplicate pressure must repeat
the readable evidence, not merely add short references. A direct canonical
scorer check passed in the correctly sourced local inference environment;
the earlier missing-upstream warning was an unsourced-environment limitation,
not an absent installation. No new model call has yet run.

## 2026-07 to 2026-08 — foundation and invalidated predecessors

The repository established deterministic dashboard rendering, label-private
case views, case-local service/pod/node identifiers, unified scoring, token
accounting, resumable writers, and local vLLM recipes. Early RQ0/RQ1 work tested
text, flat, visual and mixed representations, plus several routing/two-stage
ideas. The routing and early multi-stage routes did not provide a stable gain
and were abandoned for the first paper.

All model-call results produced under the old `vllm-inference-v1` contract were
later archived as invalid for scientific claims. That decision did not alter
CPU-only renderer/data artifacts and did not rehabilitate failed or incomplete
runs. Qwen3.6 was removed from the active study; Qwen3.8-27B and
Gemma-4-26B-A4B-it became the registered frozen Solvers. Local recipes remain
model-specific and unquantized.

The project temporarily used Nibi/H100 and local hardware interchangeably.
Operational differences and preparation drift made the workflow difficult to
audit. The project subsequently standardized on local execution and stopped
using Nibi. Historical cluster scripts may remain as code provenance, but they
are not execution authority.

## 2026-08 to 2026-09 — RQ1.1

RQ1.1 narrowed the paper to one-stage RCA and tested text, screenshot, full
vision and modality-selective visual arms, along with direct QA and a bounded
counterfactual mechanism study. Image and text attention were recorded for the
completed historical experiments, but attention is treated only as a
correlational diagnostic.

A raw-to-processed consumption bug was found: an earlier consumer omitted
fields present in the source schema, weakening pod/node/process evidence. Old
derived experiments affected by that processor were cleared rather than
silently reinterpreted. The SIRCL-compatible processor was moved into the
project, made self-contained, tested against the reference transformation, and
used to build canonical V3 per-case data and the frozen RQ480 roster.

The valid RQ1.1 rerun found that visual representation can improve some RCA
arms and reduce input tokens, but full vision is not uniformly best and output
tokens do not automatically decrease. Topology-selective vision was a strong
Qwen condition. Effects varied by model, dataset, fault type and root
granularity. Direct QA exposed perception and formatting failures, but QA
accuracy— including root-connected questions—had weak association with RCA
ranking. Counterfactual inputs showed that the Solver does use visual evidence,
while also revealing shortcut and ranking failures. The consolidated numbers,
figures and caveats are in
`docs/RQ1_1_RQ2_1_findings/findings.md`; implementation incidents are retained
under `docs/issues/`.

## 2026-09 — old RQ2 abandoned and RQ2.1 completed

The first RQ2 implementation introduced a new renderer/design pipeline without
a strict RQ1.1 bridge. Its named tool profiles also collapsed to identical
model inputs, so the tool comparison could not identify tool effects. RQ2 was
abandoned in full; its source remains historical, while generated results were
removed after a retirement audit. This failure is retained because it directly
motivated input-identity checks and fixed anchors.

RQ2.1 restarted from the RQ1.1 P0 bridge and separated three interventions:
evidence selection, silhouette encoding, and canvas composition. It evaluated
both Solvers over RQ480 with fixed anchors rather than claiming a sequential
champion was globally optimal. Results showed that evidence selection matters,
but many new designs did not beat P0; encoding/layout effects were conditional
and often model-specific. Resolution and density did not yield a universal
monotonic optimum. Tool arms were audited at the actual-request level so
same-input reuse could not masquerade as an intervention. The authoritative
findings are merged with RQ1.1 in the single findings document above. RQ2/RQ2.1
operational pitfalls remain in `docs/issues/`.

## 2026-09 — RQ3 historical training branch and elimination tournament

A Qwen3.5-9B dashboard Composer was prototyped with a structured card/silhouette
DSL. Format SFT reached update 320 and improved schema/binding/render success
relative to the base model, but this did not establish downstream RCA benefit.
The proposed full RL lifecycle was therefore not promoted into the first-paper
main line. Checkpoint retention used latest-plus-every-20 during that historical
run. No current plan resumes those checkpoints automatically.

The subsequent elimination tournament explored complementary evidence
selectors without training. Each round ran only cases not previously solved by
that model; union coverage therefore measures the combined reach of many
attempts, not deployable single-call accuracy. After 38 committed rounds the
user stopped the tournament. AC@5 union coverage reached 96.7%, while persistent
AC@1 failures and many top-five-but-not-first cases pointed to competition
between plausible roots and ranking errors. The only tournament report is
`docs/Tournament_Analysis_2026-09-15.md`; it records per-round methods,
AC@1/3/5, covered/uncovered case profiles and the proposed contrastive selector.
No further tournament round is authorized.

## 2026-09-15 — RQ3.1 research direction and data roles

The new first-paper direction is a deterministic, contrastive evidence
compiler for a frozen one-shot Solver. It compares competing root explanations
using public telemetry and represents selected evidence as text, compact text,
screenshot or a real dashboard. The goal is high MRR plus grounded entity,
temporal and relational evidence—not visual novelty alone. Training is a
conditional later extension only if a fixed method first establishes useful,
case-dependent design actions.

The earlier proposal for a wholly unexposed 480-case test was infeasible with
the available AIOPS pools and was superseded by explicit user instruction.
The accepted versioned registration uses:

| Dataset | Train | Eval | Test | Unused |
|---|---:|---:|---:|---:|
| AIOPS-2022 | 150 | 100 | 120 | 171 |
| AIOPS-2025 | 150 | 100 | 120 | 30 |
| AegisLab | 0 | 100 | 120 | 1202 |
| RE2-OB | 0 | 90 | 0 | 0 |
| RE2-TT | 0 | 90 | 0 | 0 |
| **Total** | **300** | **480** | **360** | **1403** |

All 2,543 identities occur exactly once. Old train and RQ480 identities are
unchanged; all former validation140 are in test. Five CPU tests, deterministic
byte checking, independent public/private partition comparison, protected
source hashes, and Aegis source/event/window reconstruction passed. Active
train/eval/test event-window group crossings are zero. Public rows expose only
dataset and opaque ID. This accepts the data registration only; no telemetry
row, model call, renderer, smoke, training or formal experiment ran.

Artifacts:

- `RQs/RQ3_1/configs/data_split_v1.json`
- `RQs/RQ3_1/results/data_registration_v1/summary.json`
- `RQs/RQ3_1/results/data_registration_v1/registration.json`
- `RQs/RQ3_1/results/data_registration_v1/private/split.json`

## Persistent validity and operating rules

- Labels, root cause, fault type, absolute injection time, raw case identity,
  dataset name and paths remain evaluator-private and never enter model-visible
  evidence.
- Candidate identities are case-local numeric aliases. Scoring is
  granularity-aware: service predictions may resolve hashed pod aliases, while
  pod/node labels remain exact.
- Full conversations, requests, outputs, per-case metrics, failures and costs
  are recorded asynchronously for every future experiment. Infrastructure
  failures are not model-quality failures; parse/format failures remain model
  outcomes under the registered policy.
- A real dashboard, pixel screenshot and pure text are distinct. Selection must
  change actual evidence, while representation twins must preserve their
  registered semantic facts.
- Completed historical results retain their original validity class. A new
  verifier or operational rule cannot silently invalidate accepted evidence or
  rehabilitate invalid evidence.
- New inference uses local project-owned vLLM only. Model scientific settings
  remain frozen unless a new versioned experiment explicitly changes them.
- Temporary analyses belong under ignored `tmp/`; generated results, renders,
  attention, checkpoints and conversations stay machine-local and ignored.

## Current next step

Stop after the requested code/static-review handoff. Run the full CPU suite and
visual/token qualification against `research_v2.json`, then one bounded smoke
per logical experiment. If those pass, resume the 141/480 eval context cache,
complete the expanded eval and mechanism queue, freeze the visual method, and
only then prepare/open test for the eight-method final comparison. No process is
currently running and no formal model call has started.
Continue single-agent ownership. Do not restart abandoned RQ2, the tournament
or Composer training. Test remains separated from method development.

## 2026-09-16 — RQ3.1 preparation completed; P0 hostname boundary corrected

- The resumable eight-worker preparation completed all 480 eval contexts.
- Formal Qwen execution submitted four valid first-case requests, then stopped
  before submitting `P0_T_CAL` because its parent Denum template contained a raw
  Kubernetes DNS hostname. The four completed requests remain intact; the
  blocked task made no model call.
- RQ3.1 now deterministically replaces public IP, UUID and Kubernetes DNS
  strings in P0 materializations with case-local typed aliases at both fresh
  materialization and request construction. The triggering case's P0 text and
  two visual requests pass the leakage audit; focused regressions pass.
- The correction is idempotent and request-boundary compatible with all 480
  completed contexts. Preparation does not need to be rerun. Formal inference
  remains stopped pending an explicit resume.

## 2026-09-17 — RQ3.1 SIRCL text capacity repair

- Formal Qwen inference stopped after 1,215 persisted calls when AIOPS-2022
  `INC-32757906019C/SIRCL_TEXT` required 32,885 input tokens plus the frozen
  8,192-token output allowance, 117 tokens beyond the 40,960-token context.
  This was a tokenizer preflight failure, not OOM, model output, or an image
  capacity failure; the model was never called for that unit.
- Added a label-blind whole-row capacity adapter only to overlong native
  SIRCL text. It preserves the task, candidates, all modalities, topology and
  the first MET-Z row per entity, removing deepest native-ranked complete MET-Z
  rows until the qualified payload target is met. Image arms are unchanged.
- The failed request now removes 73 complete MET-Z rows and measures 29,827
  Qwen / 31,829 Gemma input tokens, leaving 2,941 / 939 tokens beyond the
  reserved completion allowance. All 80 previously completed SIRCL requests
  remain byte-identical; the other completed arms do not enter this adapter.
  Thus all 1,215 persisted calls remain reusable, and preparation remains valid.
- A four-worker read-only scan of all 480 prepared contexts found exactly three
  over-cap SIRCL payloads: `INC-D3EAA310B962`, `INC-32757906019C`, and
  `INC-4D6E62700175`. After the same shared reduction, all three fit both local
  processors with the 8,192-token completion allowance; no other arm or stored
  context was changed.
- Focused and full RQ3.1 CPU regression passed: 76 tests. No model server,
  smoke, or formal inference was started during this repair.

## 2026-09-17 — RQ3.1 capacity-case verification and formal resume

- The repaired `INC-32757906019C/SIRCL_TEXT/Qwen3.8` request completed with
  29,827 input and 87 output tokens. Artifact verification passed; the correct
  root ranked second (MRR 0.5, AC@3/5 1.0). The local server was stopped after
  this single verification call.
- Formal execution then resumed through the content-addressed full local
  supervisor. The 480-case context cache was hash-verified and reused; no
  preparation was regenerated. The pre-existing 1,215 completed calls and the
  repaired verification call remain reusable, while the old preflight failure
  is not treated as a completed model outcome.
- Resume process group 2702 is running the Qwen effectiveness phase locally
  with attention disabled. Qwen must complete before the registered Gemma
  phase and later experiment batches begin.

## 2026-09-17 — RQ3.1 user-requested safe pause

- Qwen effectiveness completed all 7,200 registered units with no failures.
- Gemma was paused after 2,971/7,200 units. The runner stopped new submissions,
  drained all eight in-flight requests and writers, and persisted 2,971/2,971
  completed units with no failures before the lifecycle wrapper shut down.
- The full supervisor, model-phase wrapper and local vLLM server are stopped;
  port 8000 is closed and no project compute process remains on the GPU. Resume
  must reuse the completed content-addressed records and continue Gemma only.

- The user subsequently resumed the run. The full local lifecycle supervisor
  restarted with the same contexts and contracts. It first revalidates Qwen's
  7,200 completed content-addressed units without new generation, then resumes
  Gemma from 2,971/7,200 and continues the remaining registered batches.

## 2026-09-17 — RQ3.1 fast atomic resume active

- The bulk restart verifier was removed. Qwen now skips before server startup
  from its model-phase marker; Gemma skips its 2,971 atomic commits before
  loading any corresponding context.
- The lifecycle wrapper now reuses the completed 480-case context index instead
  of re-entering preparation after runner-only source edits. The context loader
  trusts the index's existing self-binding predecessor-acceptance attestation;
  duplicate mutable-source-hash gating was removed while predecessor identities
  and compatibility scope remain pinned.
- Two restart attempts stopped before any new model request while these duplicate
  gates were identified. The successful attempt resumed Gemma, committed new
  units, and reached 99% GPU utilization with no runner error. Qwen responses,
  Gemma's prior 2,971 responses, prompts, evidence, scoring and inference
  settings were unchanged.

## 2026-09-17 — RQ3.1 safe pause during mechanism experiment

- The effectiveness experiment completed both model phases at 7,200/7,200
  logical units per model with no recorded failure, then the queue entered
  `exp_visual_diagnostic_mechanisms` under Qwen.
- On user request, SIGTERM was sent only to the active runner. It stopped new
  submissions, drained six in-flight requests and asynchronous writes, and
  exited with 309/309 submitted calls committed and zero failures. Together
  with 76 registered terminal non-call units, the Qwen logical inventory now
  contains 385/800 resumable units.
- The model-phase wrapper, full lifecycle supervisor and vLLM server exited;
  port 8000 is closed and GPU memory returned to the idle baseline. Resume must
  skip those 385 Qwen units and continue the remaining mechanism matrix before
  starting Gemma or later experiments.

## 2026-09-18 — RQ3.1 final-test lock repair and resume

- All seven pre-test experiment families completed with zero recorded failures,
  but test preparation stopped before reading test contexts or making a model
  call. The lock freezer hashed all 16 actual prompt guides, including the
  screenshot-table mechanism guide, while the validator incorrectly hashed
  only the 15 effectiveness arms.
- The validator now shares the freezer's canonical arm set. The immutable old
  lock is preserved as `method_lock.v1_pre_prompt_set_fix.json`; a successor
  was recomputed before test activity from the same completed eval inventory.
  It retains `X_V_CONTRAST` and the same prompt/config/roster/result/ledger
  digests. Its full audit passed.
- The background queue resumed under process group 114730. It skipped all
  completed eval phases and entered 360-case test preparation with eight
  workers. On completion it will run the locked Qwen and Gemma final-test
  phases sequentially.
# 2026-09-18 — RQ3.1 final-test candidate-identity repair

Final-test preparation failed before any test model call because X interpreted
AIOPS metric endpoint prefixes (`*-grpc`, `*-http`) as new service candidates.
The first failing case had 85 X candidates versus the frozen 74 P0 candidates,
which would also have shifted numeric aliases.  Candidate identity now reuses
the exact shared parent entity universe while X evidence extraction remains
directly based on the complete per-case telemetry.  Registered endpoint
aggregates bind to their owning service and keep the endpoint suffix in the
metric name; unresolved columns are audit-counted and source-hashed.

The real failing case now has 74/74 identical aliases, 4,718/4,718 bound metric
columns and 377,572 direct public facts.  The focused evidence suite passed
29/29, Ruff F/E9 passed and `git diff --check` passed.  No final-test request or
result existed.  The ten predecessor-lock test context payloads are therefore
stale preparation only and will be rebuilt after a successor method freeze;
all 20,600 completed eval/mechanism calls remain untouched.
# 2026-09-19 — RQ3.1 authoritative pod typing repair

The resumed test preparation stopped at 19/360 indexed cases (26 payloads
atomically written) on a SIRCL hosting row.  Public metadata identified
`ts-auth-service-79b77c-89cp5` as a pod, but the legacy 8--10-character
ReplicaSet-name fallback classified its six-character hash as a service and
gave it a three-digit alias.  This was not an OOM or storage failure.

RQ3.1 now gives the public `node_pod_map` authority over node/pod typing and
uses name inference only outside that relation.  A full metadata audit found
8/480 eval and 2/360 test cases with this short-hash condition.  All eight eval
entities were non-root distractors and none appeared in either model's top five
across their 240 effectiveness responses.  Removing all eight cases from the
registered selection calculation still selects `X_V_CONTRAST` (macro MRR
0.446210 versus 0.431028 for `X_MTEXT`).  Existing eval results are retained
with the documented limitation rather than rerun; no test model call exists.
The incomplete test context cache must be rebuilt under the successor lock.

# 2026-09-19 — RQ3.1 selective rerun authorized

The user superseded the initial no-rerun consequence and authorized a bounded
successor rerun.  A frozen repair manifest contains the eight affected eval
identities and two affected test identities.  The active eval repair comprises
240 effectiveness calls and 108 follow-up calls; all old attempts remain
charged.  A repair utility audits the exact 348 active call records, archives
their artifacts and response-reuse pointers, removes only their logical
completion bindings, and leaves every unaffected call intact.  Successor
summaries and method selection must be recomputed before a new test lock and
test preparation are produced.

## 2026-09-20 — RQ3.2 SignalCover implementation and qualification deployment

- Implemented a new RQ-local pipeline under `RQs/RQ3_2/` from the approved
  SignalCover plan. It rebuilds the complete public pool with P0's public
  telemetry boundary, keeps P0/X/SC paths distinct, and registers selection,
  representation, mechanism, and locked-generalization experiments.
- Added eight-worker resumable CPU context preparation, same-fact text/visual
  carriers, evaluator-private mechanism interventions, request-bound local vLLM
  execution, separate call accounting, prompts/renders/conversations/costs, and
  an immutable pre-generalization method lock.
- Static syntax, shell, registration, leakage-source and unit checks passed.
  CPU/processor qualification and four sequential live smokes were deployed as
  a background queue; they remain separate gates and are not formal results.

### Qualification environment correction

The first queue completed its three-case CPU preparation but stopped before any
model call because processor preflight was mistakenly launched from the tools
environment, which intentionally lacks `transformers`. The inference environment
contains the registered processors. Qualification was corrected so pytest and
preparation remain in `venvs/tools`, while processor preflight alone uses
`venvs/infer`. The three completed context artifacts are retained and reused;
the failure changed no evidence, request, renderer, model, or scientific result.

The second qualification attempt correctly used `venvs/infer` but exposed a
second operational omission before any model call: the RQ3.2 shell entrypoints
had not sourced the canonical local environment, so processor preflight resolved
the model relative to the code checkout instead of the separate local resource
root. All RQ3.2 local entrypoints now source `scripts/env_local.sh`; this supplies
the registered local config and Qwen/Gemma model paths without changing prompts,
evidence, weights, sampling, or scoring. Existing contexts remain reusable.

## 2026-09-20 — RQ3.2 qualification provenance repair and v2 passage

Post-smoke inspection found that successful requests had used the correct local
server recipe but their saved envelope named the historical default YAML. The
RQ3.2 wrapper also prewrote an image before the shared transaction wrote the
same bytes under its canonical name, and the queue left a stale PID without a
terminal status. These were audit/persistence defects, not changes to the
model-visible evidence or inference configuration.

The request envelope now records the runtime configuration source, render
persistence has one owner, and the queue atomically records `running` followed
by `complete`/`failed` and cleans its PID. The successor contract is
`research_v2.json`; its scientific matrix is unchanged and its durable call
ledger is shared with v1.

The successor qualification passed 5/5 focused tests, prepared three real
cases, qualified eight CPU requests, and completed all 24 live smoke calls
across four experiments and two models with zero infrastructure errors. Every
completion artifact hash passed. Saved prompts uniformly name
`configs/vllm_inference_local.yaml`; six visual calls have one render each, and
the queue ended cleanly with no live vLLM process.

## 2026-09-20 — RQ3.2 bounded flag-only formal resume

Before formal launch, a direct benchmark showed that reconstructing all ten
selection requests cost about 13.6 seconds per case. Although below the user's
per-case stop threshold, it could waste roughly 1.8 hours near the end of a
480-case model phase. Formal resume therefore uses an append-only mapping from
logical unit to the atomic completion flag. Completed units receive no evidence
selection, rendering, prompt assembly, tokenization, artifact hashing, or model
call during restart. Completed model phases use one phase flag. A synthetic
worst-stage scan of 5,280 flags took 0.068 seconds; the enforced pre-server
limit is 900 seconds.

The same pre-launch matrix check found that the mechanism smoke's single cell
had not exercised RQ3.2's new comparison-bundle re-anonymization or removal
non-applicability. A local typed-key adapter was added without modifying
RQ3.1. Removal conditions with no valid evaluator-private target are now
recorded as zero-call `not_applicable` units. All 14 mechanism dimensions then
constructed or terminated as registered for the three qualification cases;
focused tests passed 7/7.

The user further required failure flags to be terminal. Formal resume now
recognizes four flag states: complete, model failure, infrastructure or
implementation failure, and not applicable. None is automatically retried.
A newly observed infrastructure/implementation failure stops further
submission after in-flight calls drain and leaves the queue failed for review;
its flagged unit remains skipped on any later manually authorized resume.

## 2026-09-20 — Retired preparation, cache, and training-artifact cleanup

After an explicit read-only ownership audit and user confirmation, obsolete
RQ1.1/RQ2.1 preparation payloads, obsolete RQ3/RQ3.1 pools and context caches,
and the abandoned Composer SFT/RL route (checkpoints, adapters, optimizer
states, training runs, and their qualification artifacts) were deleted. The
operation released 148,793,065,472 bytes (about 148.79 GB / 138.58 GiB) of
filesystem capacity and is not recoverable from this worktree without an
external backup.

The cleanup retained 45,955 historical model-visible images in their original
paths (14,813,666,398 logical bytes) wherever the corresponding formal result
did not store another image copy. It also retained all old source code,
scripts, documentation, configurations, findings, Tournament/search inference
records, RQ1.1/RQ2.1/RQ3.1 formal inference results, model weights, and model
runtime caches. RQ3.2's live dependencies were explicitly protected:
`build/local_processed_v3`, RQ3.1's data registration, both formal RQ3.1 parent
context sets, and the complete RQ3.2 results tree. Post-cleanup checks found the
RQ3.2 formal queue still running in `prepare_eval` with 111 contexts committed.

## 2026-09-20 — RQ3.2 300-second request timeout and fail-fast resume

Two Qwen selection requests remained almost entirely stalled for more than 30
minutes while hundreds of later requests completed. Their prompts were within
the successful arm's size range, the server reported no CUDA/OOM/internal-core
failure, and the later `EngineDeadError` followed the wrapper's deliberate
SIGTERM shutdown. The unified local and portable request timeout is therefore
changed from 1,800 to 300 seconds. The RQ3.2 registration records the same
bound. This is operational only and does not alter completed results.

The user retains strict fail-fast behavior and explicitly rejects adding a 5%
final-acceptance rule. Existing complete/model-failure/infrastructure-failure
terminal flags remain authoritative and are skipped by the fast resume path;
new infrastructure failures stop the phase for review and are not retried
automatically. Python compilation, 11 focused RQ3.2 tests, static registration,
and effective-client projection all passed; the client resolved a 300-second
timeout from `configs/vllm_inference_local.yaml`.

The first restart attempt also exposed that the context index had incorrectly
used the entire research registration as its preparation identity.  Therefore
the operational timeout amendment was mistaken for a context-construction
change.  Preparation now has a dedicated hash over only its data source,
roster seed, registration identity, and selector contract.  The legacy index
is accepted only when it exactly matches the immediately preceding
registration with the timeout field removed; selector or data changes still
fail closed.  The existing 480-context index migrated in 0.13 seconds with no
case regeneration.  Focused tests increased to 12 passing cases and the formal
static entry point passed.  The sequential formal queue then resumed at
`exp_signal_selection`; its fast journal/terminal-flag path skips all existing
terminal units and retains strict fail-fast for the next infrastructure error.

## 2026-09-20 — RQ3.2 request-timeout continuation amendment

Repeated isolated 300-second request timeouts stopped otherwise healthy Qwen
selection runs even though vLLM continued returning HTTP 200 responses and no
CUDA, OOM, or engine-core failure preceded shutdown. The user therefore makes
request timeout the sole exception to RQ3.2 fail-fast. New request timeouts are
persisted as distinct terminal `request_timeout` units, are skipped on resume,
are not retried automatically, and do not stop submission of the remaining
matrix. Every non-timeout infrastructure or implementation error continues to
write a terminal failure and stop the phase after active requests drain. The
300-second bound, model inputs, inference recipe, scoring and prior terminal
records are unchanged.

## 2026-09-21 — RQ3.2 host-memory OOM and bounded context cache

The apparent WSL crash during Qwen signal selection was traced to a Linux host
OOM, not to vLLM or an unexplained restart. `/var/log/kern.log` records Python
PID 217567 being killed at 45,106,408 KiB anonymous RSS. RQ3.2's 480 durable
case contexts occupy about 11.35 GiB serialized, while `ContextStore` retained
every expanded object and its runtime representation twins in an unbounded
dictionary. The runner's memory therefore grew with the number of cases until
WSL's available memory and swap were exhausted.

`ContextStore` is replaced by a thread-safe eight-case LRU, with the bound in
the RQ3.2 registration and regression coverage for eviction and reload. This
is an operational object-lifetime repair: it does not alter evidence,
representation, prompt, model, decoding, or scoring. Existing atomic terminal
flags remain valid, and restart skips them without request reconstruction;
only units with no terminal flag are resubmitted. The full diagnosis and
prevention rule are recorded in `docs/issues/RQ3_2_issues.md`.

The first restart then exposed a second recovery-boundary defect: fifteen
unflagged logical units still had `started` rows in the model-call ledger and
were incorrectly converted into RQ3.2 terminal failures. Non-smoke phase start
now marks only exact-scope stale `started` rows as `interrupted`; the shared
ledger permits those spent, unfinished calls to be retried and continues to
count every attempt. The erroneous failure records are preserved and
superseded by append-only retry tombstones. This recovery is a constant-time
SQLite update and performs no historical request or artifact validation.

One concurrently discovered `P0_MORE` pure-text unit exceeded the exact model
context. RQ3.2 now applies the user-authorized context-safe fallback only after
such an exact tokenizer overflow: reverse-ranked complete evidence units are
removed until the request fits, at least one unit per populated region is
retained, and the removed IDs are recorded in the projection. Completed
requests and all visual carriers remain unchanged.

Focused static checks and 17 RQ3.2 execution tests passed. A full 480-context
memory regression peaked at about 2.01 GB, and the resumed formal runner
advanced from 4,645 to 4,655 completed selection units with about 5.2 GB RSS
under 36-way request preparation. The previously overflowing `P0_MORE` unit
also completed through the audited capacity path. The formal queue remains
active and continues only the 102 units that lacked a terminal state at that
checkpoint.

## 2026-09-21 — User-requested safe pause during mechanism evaluation

The formal queue was deliberately terminated at `exp_signal_mechanisms` before
the overnight idle period. At the pause boundary, Qwen had 745 completed calls,
78 registered non-applicable interventions, five request timeouts, no other
terminal failure, and 572 units without a terminal flag. The experiment runner,
queue wrapper, and its local vLLM server were all stopped; no CanvasRCA process
remained. Existing atomic flags and the append-only resume journal are the
resume authority, so a later restart will submit only the 572 unfinished Qwen
mechanism units before proceeding to Gemma and subsequent queued stages.

## 2026-09-22 — Fixed-canvas redundant-noise repair

The resumed mechanism phase stopped on a representation-capacity exception in
`REDUNDANT_NOISE/M_TEXT`. The old intervention could concentrate long log facts
among its first twelve additions. A complete 100-case CPU audit found five such
failures. The successor keeps the fixed canvas and twelve-fact maximum, caps
added log facts at two, and fills remaining positions in the same frozen public
reservoir order. All 100 cases now construct; 99 receive twelve additions and
one receives eleven because its reservoir is exhausted.

The mechanism condition alone receives a new logical identity. Its C-Contrast
and M-Text outputs are re-evaluated under the successor policy: byte-identical
requests reuse content-addressed results, while changed requests receive new
calls. Mismatching predecessor artifacts remain superseded audit evidence.
Every other completed condition remains resumable. Static, CPU and focused
live qualification precede formal continuation.

The gates passed: 19 focused tests and the static registration audit passed;
all 100 formal mechanism cases constructed in M-Text with no capacity error;
and the isolated live smoke completed six of six calls across both models and
three registered datasets inside 600 seconds. All completion hashes matched,
all responses parsed and scored, and the three unique fixed-canvas PNGs were
visually inspected without overlap or clipping. Formal continuation is now
authorized from the atomic resume journal.

The formal queue subsequently resumed at the mechanism stage. Its existence-
only recovery scan took about 0.02 seconds, and it reused only byte-identical
predecessor requests. Both successor representations for the original failing
case `INC-F1CD9B69032E` completed successfully; the queue continued with zero
current terminal implementation failures.

## 2026-09-22 — Evidence-backed next research plan (documentation only)

Reviewed the RQ1.1/RQ2.1 findings, Tournament, RQ3.1 and RQ3.2 reports,
relevant implementation paths, stored examples, and primary related work.
The new proposal is recorded in
[`CanvasRCA_Next_Research_Plan_2026-09-22.md`](../docs/CanvasRCA_Next_Research_Plan_2026-09-22.md).

The proposed RQ3.3 direction preserves the complete TPV backbone and appends
bounded, source-grounded scope/path/liveness witnesses. It replaces future
large-scale SC/layout exploration with semantic calibration and a small,
fixed-cohort development comparison against genuine P0 expansion. Selective
topology vision is compared with a strong same-fact text twin; one-call
deployment remains primary, with a conditional two-call diagnostic only.

The rationale is that SC improved some telemetry coverage but still deleted
valuable prior evidence and did not beat the strong baselines; several
implemented ablations also differed from their intended meaning. These
observations do not retrospectively reclassify historical results. The old
360-case test is explicitly exposed regression data, not fresh confirmation.

The proposed maximum scheduled work is 19,710 calls, including five bounded
smokes, within the existing 40,000-call new-RQ ceiling. Expansion is conditional
on development evidence, not automatically authorized by this document.
Only this plan and the brief decision log were written. No experiment code,
configuration, scorer, result status or running process was changed; no model
call, preparation, training or multi-agent task was started.

## 2026-09-23 — Next-plan v2: separate observation, computation and presentation

Status: proposed protocol, documentation only. Updated the existing
[`next research plan`](../docs/CanvasRCA_Next_Research_Plan_2026-09-22.md)
after reviewing the RQ1.1/RQ2.1, Tournament, RQ3.1 and RQ3.2 evidence again
and consulting published Nezha (FSE), MicroRank (WWW), CIRCA (KDD), Groot
(ASE), PAL (ICML) and Lost in the Middle (TACL). Reading scope, venue/track,
source links and applicability limits are recorded in the plan.

The late Tournament registry already includes residual, window, composition
and graph selectors, but their new scores/coefficients remain CPU-only and
their input is an analyzer-derived pool. The revision therefore does not
rename those algorithms as new ideas. It prioritizes explicit measurement
semantics, deterministic computations with visible operands, and qualified
request-level joint observations. It also tests appendix position because
preserving old facts does not guarantee freedom from context interference.

This supersedes only the previous proposed development matrix: an eight-arm
60-case paired screen and optional two-arm budget check select one global
configuration, then five conditions on a disjoint-group 120-case cohort
check it without reselection. A three-condition event-ledger/image mechanism
study is conditional, not an automatic replacement of the main renderer.
The worst-case schedule is now 20,430 calls (formerly 19,710); the 40,000
hard ceiling is unchanged. No retrospective result reclassification.

No experiment implementation, model recipe, scorer, results, process or data
partition was changed; no preparation, CPU experiment, model call, training
or subagent was started. Next action requires separate implementation
authorization, beginning with public-field feasibility rather than full runs.

## 2026-09-23 — RQ3.3 Witness implementation; static-only stop

Implemented the next-research plan under `RQs/RQ3_3/`: five functional modules,
versioned registration/measurement semantics, three descriptions, five not-run
findings, and opt-in CPU/smoke entry points. New public-source witnesses preserve
the TPV backbone; SEM/EXEC share observations, COHORT requires source-linked
requests, and expanded budgets preserve the small-budget prefix. Parent-native
P0_MORE, strong text/G controls, actual interventions, method locks, paired
statistics, durable call accounting and flag-only resume are implemented.

Refined the plan to v3. A new same-renderer G scene control separates redrawing
from node rearrangement (+240 planned calls: 20,670 total; 40,000 hard cap
unchanged). FRONT preserves the original candidate location. Status-available
but undersized request cohorts cannot silently change to latency cohorts.
Original baselines and all historical experiment artifacts remain unchanged.

AST, static project-import symbol checks, Ruff E9/F, JSON/budget/structure checks
and shell syntax checks passed. The implementation review and runtime boundaries
are recorded in `docs/issues/RQ3_3_implementation_review_2026-09-23.md`.
No project module/test was executed, no data registration or preparation was
run, and no CPU regression, smoke, GPU/model call, training or subagent started.
Source calibration manifests and real-input/visual/runtime qualifications remain
future evidence requirements, not claimed successes. Stop here as requested.

## 2026-09-23 — Witness v2: information-inspired controls, static-only stop

Updated the next plan to v4 and RQ3.3's protocol/config/code to `rq33_witness_v2`.
The five experiments and six deployment candidates stay fixed. Added a
same-request marginal control, RAW evidence-pair factorial, identical-caption
local/remote binding controls and a 1024/2048/4096 nested-budget comparison.
Planned calls are 23,190 (+2,520); the hard limit remains 40,000. Mechanism
controls cannot win deployment selection. Full v2 rationale, source links,
applicability and interpretation limits are in the plan and RQ description.

Static review corrected pooled-median computation, explicit cohort group labels,
PAIR removal closure/common backgrounds, budget-specific analysis identities and
actual-input intervention metadata. Report utility interactions and empirical
cost curves, not estimated mutual information/PID or Shannon rate–distortion.
New CPU regression definitions are written but not run. AST/import-symbol,
Ruff, shell, JSON/matrix and documentation-link checks passed; see the RQ3.3
implementation review. No parent renderer, model recipe, scorer, partition or
historical result changed. No registration, preparation, CPU regression, smoke,
GPU/model call, training or subagent started. Await user authorization to test.

## 2026-09-23 — Witness v2 CPU/GPU qualification and smoke repairs

Subsequent user authorization covered CPU/GPU smoke and defect repairs, not
formal experiments. Replaced fragmented full-message log candidates with
source-indexed template/phase summaries; removed repeated serialization,
tokenization and quadratic Denum selection. The latest three-case CPU run
passed in 109.59 seconds: 32 unit checks; 86 executable real conditions and
25 explicitly inapplicable conditions. Per-case earlier post-optimization
preparation was 89.01/44.70/9.73 seconds (AIOPS-2022/AegisLab/AIOPS-2025), not
full RCA latency or dataset-wide estimates.

Live smoke exposed unauthenticated readiness probes, false success on interrupt,
an unresolved local scorer path, and G graph/ledger height-allocation failure.
Fixed all four; added three focused non-network regression tests. Completed
the missing SC calibration audit by matching 120 historical requests to public
context projections and binding estimator-specific guide edits. No numerical
source correction is certified; SOURCE_FIXED therefore aliases GUIDE_FIXED.
Old evidence, results, model recipes and scoring semantics remain unchanged.

All five logical smokes completed under 18 calls/600 seconds apiece: 90 units,
86 actual calls, 234–247 seconds each. Inputs, raw outputs, full conversations,
cost and completion hashes checked; all 86 responses ended with `stop` and were
scored. Opened actual G re-layout images; retained model reasoning/identity
mistakes as outcomes, not retried failures. EVENT remains unqualified on these
samples; no claim that every optional arm is live-covered. Earlier attempts
(0+9+44 calls) remain separate; cumulative initiated calls are 139. Services
exited after testing. No formal experiment, attention collection or training.
Details: `docs/issues/RQ3_3_implementation_review_2026-09-23.md`; artifact review:
`RQs/RQ3_3/results/witness_v2/smokes/review_2026-09-23.md`.

## 2026-09-26 — All-report gain/harm review and proposed RQ3.6

Read the RQ1.1/RQ2.1, Tournament and RQ3.1–3.5 reports. User requests equal
attention to improvements and degradations, including worthwhile nonsignificant
trends. Added a reproducible offline review of 17,502 paired comparison records
(not independent cases), 3,311 subgroup rows, event-group sensitivity, complete
cohorts and source hashes. Holm families are report-stage × subgroup axis across
listed comparisons/models; n<10 remains descriptive. Gold-root type derives from
the registered numeric-ID contract and matches the newer private-label audits;
historical mixed-type metadata is not blindly propagated. No scores changed.

Exploratory Qwen RQ3.4 G-versus-text effect on AIOPS-2025: +0.1795 MRR, 39 cases,
11 Top-1 repairs/0 breaks, Holm p=.0457, same event-group sensitivity. This does
not establish a dataset interaction or independent replication across rounds.
RQ3.5's registered Gemma instruction harm and loss of lower-rank hits motivate
separating semantic guidance from verification wording; subgroup harm and small
positive trends remain explicit rather than being filtered by headline p-values.

Decision: prioritize A check replication, then qualified dynamic W/peer component
ablations with fixed G/text twins, then bounded composition and locked evaluation.
Do not automatically expand low-coverage J or add K assertions to model input.
Plan: `docs/experiment_plans/CanvasRCA_RQ3_6_Research_Plan_2026-09-26.md`.
Full conditional workload 19,272 calls before necessary repairs; this is not a
new budget authorization or a reset of the parent 40,000-call allowance.
No inference, training, preparation, runtime/scorer changes or new subagents.
Existing source/results preserved; report/plan indexes updated. Implementation
and new experiment execution remain future work.

## 2026-09-23 — RQ3.3 formal queue launch authorization

User authorizes the full sequential queue and requests no continued agent
monitoring after startup. Added an explicit RQ-local queue wrapper, preserving
all frozen inference/evidence source hashes. Four lightweight scheduler tests
pass: positive path, negative screen/check routing, and done/fail flag-only
resume without preparation or model launch. Existing evidence-backed manual
review and all five smoke reports registered as passed qualifications.

Queue prepares screen60 with eight core-pinned workers (three contexts already
committed), then calibration and screen, Qwen before Gemma per stage. The
registered budget/check decisions control later eval/mechanism/test expansion;
negative development leads only to the bounded registered diagnostic. EVENT
and fresh remain unavailable rather than silently enabled. Historical 53 model
attempts are counted once alongside 86 current smoke calls in the hard budget,
without treating those old responses as reusable results. Resume trusts small
terminal flags; no bulk artifact rehash or completed-request reconstruction.
SIGTERM drains the active runner and releases only queue-owned services.

Operational authority: `RQs/RQ3_3/results/witness_v2/formal_queue_status.json`.
Logs: `RQs/RQ3_3/results/witness_v2/logs/formal_queue/`. No scientific result or
MRR claim is implied by launching the queue.

## 2026-09-25 — RQ3.5 implementation and bounded qualification

Implemented independent RQ3.5 evidence×instruction, outcome-linked joint-count,
G/J representation and locked replication/generalization paths. Reuses RQ3.4
public contexts and persistence infrastructure; new indices read whitelisted
per-case fields without gold or raw-log expansion. Runtime/scorer remain
unchanged, attention disabled, one Solver call and at most one image.

Static checks and 13 CPU unit tests pass; three real cases compile all 20 arms
for both model processors (120 units). Final cached CPU regression: 21.37 s;
cold case preparation 14.61–19.86 s, new indices 5.63–10.94 s. Early binder-hash
and SIRCL-part-boundary bugs were caught and fixed before GPU. Composite G
uses parent-registered crops in fixed slots; native B is unchanged. Audit-only
joint evidence is restricted to facts actually visible in the corresponding
input. Pre-inference revisions retained rather than silently overwritten.

Four original GPU smokes completed 72/72 logical units in 263.51/227.00/235.72/
252.85 seconds, using 18/14/16/18 actual calls (66 total, cumulative 6,933).
Input/output/conversation persistence and sampled real PNGs were reviewed.
Post-smoke review found duplicate candidate records in A's two common P0
conditions. Removed the duplicate while preserving the common candidate list;
CPU proof shows 12 changed inputs and 108 unchanged. Native controls and B/C/D
retain their input contracts. A second review-only fix prevents old smoke
records from qualifying changed inputs; another 120-request CPU comparison
shows no further changes, all 13 unit tests pass, final CPU run 21.20 seconds.
B/C/D remain qualified. A requires six targeted calls; a one-time exception
to its exhausted original cap has been requested but not presumed authorized.
All original artifacts are preserved. Owned GPU services have exited. No
formal execution or expansion has been started. Artifact authority:
`RQs/RQ3_5/results/outcome_linked_v1/qualification/`;
implementation/issue record: `docs/issues/RQ3_5_qualification_2026-09-25.md`.

## 2026-09-23 — RQ3.3 calibration-to-screen timeout repair

Calibration completed 480 logical units (478 done, 2 request timeouts), but the
old next-stage check treated every fail as blocking. Aligned stage admission
and subsequent decision pairing with the existing timeout-continue policy;
other infrastructure errors still stop. No automatic retry or 5% gate. Common
decision cohorts and exclusion IDs are explicit, including all budget levels;
science thresholds and model inputs unchanged. 65 tests and static checks pass;
15.00-second targeted CPU audit preserves all 90 smoke input identities and
480 calibration flags. Actual tiny-flag stage check: 0.023 seconds. No new GPU
qualification calls or preparation rebuild. Full repair record:
`RQs/RQ3_3/results/witness_v2/logs/stage_timeout_repair_20260923.md`.

## 2026-09-27 — RQ3.6 B implementation and qualification; stop before formal

User authorized B plan/code/static/CPU/GPU qualification only. Preserved A
inputs/results/config/report and snapshotted its predecessor source. Added
five controls to the original nine: G order, relational text, its screenshot,
and matched typed scope text/graph. Qualified witnesses filter static/clock
anchors and incompatible peers; unrelated static companions cannot sneak in
through a dynamic host. Same-field unchanged peers remain valid controls.
No labels or response outcomes select inputs; no training or attention.

CPU caught graph/ledger overflow before inference. Registered one fixed
2304×3072 geometry with1100px graph height, unchanged20px font, no omitted
facts. Completed three-focus static review,10unit tests,84real CPU request
builds in18.351s. One logical GPU smoke completed18/18 in276.903s, both models,
without timeout/infra/parse failure. Conversations include all input text;
12saved PNGs match qualified bytes. Read all responses: unsupported causal
edges/type confusions remain model errors, not grounds to tune this smoke.

Optional deep_gemm import and Triton JIT warnings preserved; frozen serving
recipe unchanged. Total calls10917=10899prior+18smoke; newformal0. Owned
services exited. No B formal authorization, no C/D launch. Full audit:
`docs/issues/RQ3_6_stage_B_qualification_2026-09-27.md`.

## 2026-09-27 — RQ3.6 B formal launch

User separately authorized full B and no assistant monitoring after startup.
Current qualified source unchanged; authorization/flags check0.064s,245GiB
free, cumulative10917 calls before launch. Detached sequential Qwen→Gemma
queue PID4396 started14:17:54UTC; first owned server4430 loading. Scope only
180exposed cases×14arms×2models,5040 maximum newcalls; no C/D. Run-local
shell transcript/atomic status/logs in `RQs/RQ3_6/results/visual_mechanisms_v1/`.
Tiny terminal flags drive resume; no old request rebuilding. No new MRR claim.

## 2026-09-28 — Future Dashboard design: chart-first, on-call-oriented

After inspecting a real RQ3.7 LOCAL_LINK image, the user identified excessive
text and requested more attractive, realistic on-call dashboards in subsequent
iterations. Adopt chart/relationship-first presentation with concise necessary
labels, clear visual hierarchy and appropriate density; do not use long text
ledgers or experimental empty slots as the default deployment interface.
Preserve diagnostic evidence and separate selection changes from representation
changes. Appearance is not evidence of higher MRR or engineer efficiency.

Recorded the future-only direction in section 12 of
`docs/experiment_plans/CanvasRCA_RQ3_7_Research_Plan.md`. Current stage C inputs,
renderer, configuration, running processes and historical results are unchanged.
Documentation only; no tests, model calls or new experiments started.

## 2026-09-28 — Unified renderer prototype authorized (isolated)

User requested a configurable Python + React/HTML/CSS/TypeScript renderer while
RQ3.7 C continues. Initially proposed `RQs/RendererLab/`; the user then explicitly
requested `src/renderer/` instead. All renderer code, web assets, configs and
scripts now belong in that directory (authorized organization exception).
Evidence DTO, layout tree and cyclic system graph are separate. No mutation of
running experiment inputs, shared inference recipe, older renderers or results.
Decision and qualification scope: `docs/experiment_plans/CanvasRCA_Unified_Renderer_Prototype.md`.
This is a renderer prototype, not a new scientific efficacy experiment or globally
promoted pipeline. Runtime and artifact validation will be recorded on completion.

User further specified an explicit component library (one file per dashboard
component) and global operation library (spacing, relationships, resolution,
layout, indexing). New interfaces rename “silhouette” to “dashboard component”.
Component type numbers and stable instance indices are distinct; moving a panel
does not renumber it. Historical reports/configs retain their original terminology.

Completed independent implementation: 10 component files, 9 operation files,
strict public DTO, explicit layout tree, React/SVG/CSS, offline HTML + PNG exporter,
visible-field and geometry audits. Python AST/shell/TypeScript checks passed;
19 CPU/browser tests passed (6.86s), including intentional rejection paths.
Five final real-development previews passed (0.668–0.768s/export) in
`build/renderer_previews/v1/`; visual inspection covered lines, bars, heatmap,
graph/matrix and light/dark variants. Scope and adapter coverage exclusions are
recorded in `src/renderer/QUALIFICATION.md`; prototype is not whole-parent-input
equivalence or an efficacy result. No LLM/GPU inference, no attention, no old
renderer/source/config edits, and no change to the running RQ3.7 experiment.

## 2026-09-29 — Unified renderer: topology must bypass diagnostic filters

User requires complete observed relationships, connected nodes only, observable
database/external dependencies, and richer RQ1.1-like onset information. They
correctly identified that a graph built from filtered Trace summaries may omit
real connections. Replaced the prototype's filtered ALL_ID relationship source
with targeted canonical public per-case graph/metadata + full Trace identity-column
reads; M/R/L selection and all historical experiments remain untouched.

Important source finding: AegisLab's canonical graph mixes 58 call edges and 49
hosting edges in the audited development example (`sircl_data/aegislab.py` explicitly
adds both). Classify these separately in new code, not all as calls. AIOPS-2022
example has 121 observed calls vs 9 old packet rows; AegisLab has 58 vs 4. AIOPS-2025
example has no Trace rows or observed edges; do not invent connections from names.

New `topology.py`: trace-scoped parent binding, ambiguity audit, explicit client-peer
endpoints, preserved numeric aliases, dependency roles and independent six-digit
external namespace without changing candidates. New C11 `events.onset`: existing
relative time/z/source readings, no reverse causal arrows or fabricated persistence.
O10 `graph_visibility` hides only full-graph isolates; evidence cards remain. This
supersedes the prototype v1 isolate-display default, not historical results.

Static checks and 25 CPU/browser regressions passed (8.21 s); three development
examples plus network/matrix galleries rendered and visually inspected. Export
0.020–1.976 s, browser rendering 0.718–0.819 s in these individual measurements.
Final artifacts: `build/renderer_previews/full_topology_final/`; qualification and
limitations: `src/renderer/QUALIFICATION.md`. Graph completeness means observed
per-case data only; onset coverage remains the existing public P0 rows. Dense graphs
remain a readability concern, not a reason to silently drop edges. No LLM calls,
GPU use, historical renderer edits or intervention in the running experiment.

## 2026-09-29 — Pairwise relationship dashboard component

User requests a cleaner per-edge alternative while retaining the overall network.
Added `graph.edge_pairs` (C12): every original edge receives one independent
source→target tile, typed relation and unchanged numeric endpoint IDs. Cycles,
reverse edges, self-loops and typed parallel edges remain; repeated endpoints are
audited as references to the same node, not additional facts. Existing node-link
and matrix components remain available. Explicit capacity check rejects overflow,
never truncates or silently shrinks. `pairs` preset allocates space by edge count;
controlled comparisons must separately freeze sufficient common geometry.

Static checks and 28 CPU/browser regressions passed (11.39 s). Fixed an operation
audit KeyError risk for component-specific derived rectangle keys. Rendered three
existing development DTOs, plus a matched 58-edge network/pairs pair with identical
facts, canvas and outer geometry. Actual pair PNG inspected under dashboard skill.
Artifacts: `build/renderer_previews/edge_pairs_v1/`; checks/usage in renderer README
and QUALIFICATION. No RCA calls, inference changes, active-experiment modification
or claim that pairwise topology improves MRR. Its lower edge-crossing burden trades
off against repeated IDs and cross-tile multi-hop integration.

## 2026-09-29 — Deployment brace groups and service/pod correspondence

Implemented the user's node→{pods} and service→{pods} request as independent C13
`graph.deployment_groups` under `src/renderer/`; existing network/matrix/pairs remain.
Default prototype deployment cards use braces; call diagrams keep their chosen
encoding. Exact membership edges and repeated pod identities are audited, with
capacity failures rather than member truncation. Service instances are extracted
from full public per-case Trace resource attributes with compatible existing
aliases; explicit metadata preserved, ambiguous namespaces rejected, no name-based
inference. `has_instance` is not a Kubernetes ownerReference or invocation claim.
Decision registered in the unified-renderer prototype plan.

Static checks and 33 CPU/browser regressions passed (15.30 s); three development
dashboards and deployment-only galleries rendered. Actual AegisLab group PNG
inspected: 49 hosting and 30 service-instance edges; those 30 groups each have one
pod, while 19 other hosted pods lack observed service bindings. This is sample
coverage, not a dataset-wide cardinality assertion. Tests cover one-to-many and
shared-pod associations. Artifacts and limits in renderer QUALIFICATION.md and
`build/renderer_previews/deployment_groups_v1/`. No GPU/LLM calls, historical edits,
experiment restarts or active-scientific-input changes.

## 2026-09-29 — GitHub synchronization ignore audit

Expanded `.gitignore` for preparation/cache workspaces, model checkpoints,
renderer outputs, local credential filenames (including `secert.md`), and bulky
case-level report attachments. Reports, figures, aggregate tables, source and
configuration remain eligible for Git. Local artifacts were not deleted.
All 16 representative ignore checks passed; `git ls-files -ci --exclude-standard`
found no tracked files matching ignore rules. Remaining visible untracked files
have no individual file above 5 MiB. `git add --dry-run --all` passed; no actual
staging, commit, push, history rewrite or experiment intervention was performed.
Previously committed data remains in Git history; ignore rules do not erase it.
## 2026-09-29 — Nibi successor after user-requested rollback

Both worktrees were restored to Git 19c40f52e as requested; rejected RQ3.8
layout/code is not a runtime or qualification authority. The authenticated
`canvasrca-nibi-login` tmux session was rechecked live. Nibi has completed pinned
Qwen3.8-27B and Gemma-4-31B-it download receipts, no current queued jobs, and the
other-project Qwen3.5-9B directory remains untouched. The new login-2 session
is independent and still awaiting user authentication at this check.

The resumed user goal authorizes Nibi execution (superseding local-only for
this round), up to six full-H100 80GB formal jobs of eight hours each. Local
Gemma replacement is deferred until those submissions; the user's typo was
corrected to Gemma-4-31B-it. No new job/model service has been started yet.

### 2026-09-29 — RQ3.8 smoke AIOPS-2025 empty-topology source audit

The inspected 1800x3408 FULL dashboard is the smoke case
`aiops2025/INC-03A46BA87920` (`source_case_id=aiops2025_d0c7cd07-267`), not a
topology-ablation arm.  Its registered UTC telemetry window is
2025-06-13 14:56:27--15:35:27.  The canonical per-case projection contains 39
metric rows but zero trace and log rows; `graph.json` contains 58 inventory
nodes and zero edges, and public `node_pod_map` is empty.

This is not evidence that the RQ3.8 selector discarded traces.  The raw
AIOPS-2025 June-13 trace directory contains 19 Parquet files and 5,950,881
spans, but their maximum `startTimeMillis` is 2025-06-13 11:12:56.536 UTC.
The next date directory begins at 2025-06-13 17:01:01.204 UTC.  A direct
predicate over all 41 files from both dates finds exactly zero raw spans in
the case window.  The source has a telemetry coverage gap spanning the entire
incident.  Consequently the empty call graph is a faithful observability
condition; the metrics-derived onset rows do not imply trace availability.
This audit does not settle the separate cross-granularity service-to-pod
binding concern in trace-bearing cases, which remains a formal-launch hold.

New plan: docs/experiment_plans/CanvasRCA_RQ3_8_Operational_Components_Plan.md.
Use original wide topology and normal lower card grid, fixed complete text and
fixed-position visual-redundancy ablations. No added topology isolates,
ownership connectors or graph-layout algorithm. Historical Qwen findings guide
the protocol; old Gemma MoE efficacy does not. RQ3.7 ledger currently contains
28,216 calls. Planned 7,680 formal plus 18 qualification stays within the shared
40,000 ceiling. Implementation and CPU/GPU qualification remain pending.

### Nibi-only qualification follow-up

The user forbids further local testing. Local preparation was stopped; all
subsequent static/CPU/browser/processor/GPU checks use Nibi Slurm allocations.
User ceilings: eight CPU jobs <=1h each, three GPU smoke jobs <=30m each;
the single logical smoke retains its aggregate 18-call/600s bounds.

CPU job 22921386 failed only the cross-host historical PNG byte comparison
(47 passed, 1 failed, 1 skipped). Font, bundle, CSS and dependency hashes plus
design/geometry are frozen. Job 22921513 established exact same-Nibi frozen
reference/FULL equality and unchanged-component equality; historical-host
pixel differences are recorded, not silently rebaselined. Browser versions
match; the precise environmental raster difference is not yet established.
The Slurm completed-job lookup was also repaired to consult sacct when squeue
reports an expired ID; this prevents duplicate qualification submissions.

Job 22921513 exited 0 in 158s but its processor report says context_exceeded:
verbose redundant component JSON is too large (e.g. TEXT_DUP Qwen45394,
Gemma47453 input tokens). Therefore qualification is NOT complete and no GPU
job was submitted. Preflight now exits nonzero on a failed report. Before any
model call, change only the generated ledger serialization to exact reversible
tables/ranges; original ALL_ID text, evidence, PNG, model lengths and decoding
stay intact. Nibi CPU attempt3 tests this repair; no local tests are run.

CPU attempt5 (22922052): 58 regressions passed and all three-case/eight-arm/
two-model processor checks passed after reversible table encoding, excluding
unprinted internal edge IDs, exact bin-range notation and JSON whitespace-only
compaction. The original RCA wording, selected numeric quantities, relations,
sampling, dimensions and PNGs are unchanged. No model calls have started.

Its subsequent full gallery preparation stopped at 34/480 cases because
Chromium Page.captureScreenshot returned `Unable to capture screenshot` for
INC-9CE8985F3DCB/NO_ONSET. Job peak RSS was about5 GiB, not a recorded Slurm OOM.
This is a browser-capture failure, not evidence of a topology algorithm change.
Keep completed images and failed artifacts. Add a per-render browser log and
at most one fresh-browser retry for exactly that capture error, using identical
inputs; all other browser/validation errors still fail closed. Attempt6 will
qualify this operational repair and resume gallery generation on Nibi.

CPU attempt6 (22922484) completed in19m45s: 60 tests passed; both processors
passed all24 case/arm checks; all480 galleries are now persisted. Existing
successful renders were reused. The inspected FULL images for AIOPS22,
AIOPS25 and AegisLab retain the approved layout. The dense AIOPS22 graph remains
a readability limitation of the approved graph, not a newly changed routing.

GPU smoke attempt1 (22922720), full80GB H100, terminated at its600s bound with
zero model calls. The supervisor's timeout-only status does NOT establish live
inference coverage and is not sufficient for manual artifact approval. Full log
inspection found repeated FlashInfer `Could not find nvcc` and DeepGEMM CUDA
discovery warnings. Weight loading took21.99s (model-loading phase32.12s);
engine profile/warmup took292.01s. This is a project launcher environment
omission, not evidence of a defective Nibi driver or an inherently huge-model
load. The new environment loaded Arrow but omitted the CUDA toolkit. Adopt
cuda/12.9 to match installed PyTorch2.11's CUDA12.9 build; assert nvcc/headers
before serving. Retain identical models, prompt, rendering and sampling.

Also replace per-job Triton/vLLM compiler-cache roots with a persistent
RQ/runtime-specific cache. Inspection of installed Triton cache.py confirms
UUID temporary files and atomic os.replace commits. Ports stay per-job; model
outputs are never cached/reused through compiler caches. CPU attempt7 must
qualify these deployment changes on Nibi. No formal jobs have been submitted.
Any additional GPU smoke time beyond the exhausted logical600s window awaits
explicit clarification; the aggregate18-call and three-job caps remain intact.

CPU attempt7 (22923347) subsequently completed in4m32s, exit0: all61 tests
passed, including live nvcc12.9/header/PyTorch CUDA compatibility checks, and
the24 dual-processor checks passed in9.71s. All480 gallery flags remain valid
and were reused. GPU attempt1's manual artifact review is explicitly blocked:
there were no persisted model conversations to examine and deployment warnings
were found. The user correctly identified the problem as our launch code rather
than a general Nibi/H100 defect. No second GPU smoke or formal job has been
submitted, and the local Gemma model remains unchanged pending formal submission.

The user then explicitly authorized at most two additional GPU smoke attempts.
Register this narrowly under RQ3.8 descriptions: two new600s windows, <=30m
Slurm allocation each, at most three GPU smoke jobs total and the same18-call
aggregate ledger. No further CPU job or model/renderer change is needed for
attempt2; CPU job22923347 qualified the current source. Resume qualification
on Nibi, preserving attempt1's zero-call report and blocked manual review.
2026-09-29 RQ3.8 v7 capacity repair: the seventh v6 Nibi GPU smoke failed
before vLLM/model calls because a 35,011-token Qwen FULL request exceeded the
32,768-token input allowance after reserving 8,192 output tokens. User chose
to preserve the image and preserve the fixed-text/redundant-image estimand.
Implemented exact public-card duplication checks and a reversible compact G
edge ledger, shared by every arm; `TEXT_DUP` remains intentional. Reused the
same v6 three-case public/PNG preparation, without regenerating or changing
images. Nibi CPU-only audit: all non-graph cards matched existing anchor facts;
dual-processor preflight passed for 66 case×arm rows in 45.64s, zero context
failures. Qwen Aegis FULL fell from 35,011 to 27,769 input tokens. Nibi static
source check passed (2,019 source lines after targeted regression test). No new GPU smoke, model request, CPU
regression job or formal job was started. v7 qualification remains pending
fresh authorization and full prepared-case audit.

2026-09-29 RQ3.8 v7 GPU smoke submission: the user authorized one additional
30-minute job. Nibi source/static check passed; prior job22941413 was terminal
FAILED and no RQ3.8 job was active. `rq38v7-smoke-attempt8` was accepted as
Slurm job **22942268**, receipt `--time=00:30:00`. No CPU regression or formal
job was submitted. Smoke completion, model readiness and inference results
remain unverified at this handoff.

2026-09-30 Qwen-only report reanalysis (user-requested reporting scope change):
backed up the complete docs tree before editing to
`/home/lglsj/CanvasRCA-report-backup-20260930.zJzQJW/docs`; the initial recursive
comparison found no differences. Revised all 11 experiment reports and their
active scientific attachments to use Qwen only. Published 233 CSV tables and
28 Qwen-only plots; restored four exact Qwen input PNGs with source hashes.
Original results, logs, model outputs, scoring and historical validity states
under RQs were not modified. The new report index is
`docs/experiment_reports/README.md`.

Recomputed available case-paired, factorial and event-group tests and restricted
Holm families to their full Qwen comparison sets, retaining negative contrasts.
Auxiliary tests retaining an identical original Qwen raw statistic are explicitly
marked; CSV/tie-policy sensitivities are recorded separately. No claim that all
exploratory statistics were rebuilt from raw conversations. This is a documented
retrospective reanalysis, not a new preregistration. Qwen discoveries no longer
require cross-model agreement and do not claim generality beyond Qwen.

Important revised evidence: RQ3.6-A text-interface calibration has delta MRR
+0.1017, Qwen Holm p=0.00277. RQ3.6-B HP_DEDUP Graph-minus-Text has delta
+0.0750, B2 carrier-family Holm p=0.03910 (the wider carrier sensitivity remains
non-significant). RQ3.7 LOCAL_LINK-minus-TPV has delta +0.07714, Holm p=0.00854;
LOCAL_LINK-minus-T_MATCH is positive with event-group Holm p=0.03672 but
case-level Holm p=0.10392. Reports distinguish these endpoints and preserve
the node, resource-selection and visual-reading regressions.

Offline verification passed: 433 original backup files hash-checked; 141,436
Holm rows independently checked against their declared families; 493,923
model-tagged rows contain only Qwen; 145,092 source-record rows retain their
original identities/statuses/scores; no broken main-report links. Four analysis
scripts pass AST parsing. Verification and provenance live in
`docs/experiment_reports/_qwen_only_reanalysis/`.
No model service, inference/API call, experiment queue, CPU regression or GPU
smoke was launched; no experiment implementation/configuration was changed by
this reporting task. Next work, if requested, should use the revised Qwen-only
reports and explicitly separate development discoveries from later independent
and cross-model validation.

## 2026-09-30 — Qwen positive/negative findings inventory

Scope/status: cross-RQ synthesis of the 11 current Qwen-only experiment reports,
not a new experiment or inference batch. User requested short summaries of all
positive and negative discoveries, saved under docs.

Delivered `docs/Experiment_Findings_Qwen_2026-09-30.md`: 43 positive findings or
signals, 38 negative findings, 17 unresolved/null/identifiability statements,
and 12 implementation/validity observations. Every item links to its source
report. Added a navigation link in `docs/experiment_reports/README.md`.

Validity: kept case-level versus event-group significance, Holm-family scope,
pooled versus macro endpoints, post-hoc fault/granularity strata, and no-op/input
confounds explicit. Did not promote point estimates to significant findings or
interpret unexecuted mechanisms as negative results. RQ3.7-C and RQ3.8 partial
outcomes are outside this report-backed inventory. Older evidence statuses,
scores, experimental code, queues and raw outputs are unchanged.

Checks: all 110 item IDs are unique and sequential within category; all 11
source references and inline links resolve; no out-of-scope model content in
the inventory; Markdown diff whitespace check passed. Zero model calls, no
preparation, training, CPU regression, GPU smoke or experiment launch.

Next: inventory is ready for user review. Further experiments require a separate
request; the synthesis itself does not modify the research queue.

## 2026-09-30 — Findings inventory: readable configuration descriptions

User requested replacing arm shorthand with configurations understandable without
opening the experiment protocols. Updated only the findings inventory and this
log. The inventory now describes evidence selection, added observations,
text/image allocation, relation coverage, and numeric-panel placement directly
in each relevant finding. A configuration table retains source aliases solely
for traceability.

Applied the baseline skill to check names against RQ2.1 protocols, RQ3.2 selection
code, RQ3.3–3.6 input compilers and the RQ3.7 protocol. In particular, SC is a
selection policy rather than one fixed renderer; W's added observations remain
text in the compared carriers; ALL_ID retains observed call/deployment relations
and ID correspondence, not a claim of complete raw-system observability.

All 110 finding IDs, evidence-status labels, source-report references and
statistical values are preserved. Clarified that perception levels count evidence
regions, and that the scale intervention enlarges both canvas dimensions by 1.5.
This is a readability/provenance revision, not a new statistical analysis or
change to experiment validity. No experimental code, configurations, queues,
raw results, model services or inference calls were changed or started.

## 2026-09-30 — Literature gaps, current evidence and storyline review

User requested the current storyline/progress, remaining validation, and a
2024–2026 primary-literature gaps report. Applied status, literature-review,
design-decision and devlog workflows; used the PDF workflow to inspect
accessible paper text. No delegation, inference or experimental implementation.

Delivered `docs/CanvasRCA_Literature_Gaps_and_Storyline_2026-09-30.md`.
The report links all 11 Qwen-only experiment reports and reviews 23 papers,
distinguishing published proceedings, an upcoming ASE 2026 program paper and
three venue-unconfirmed preprints. Reading scope and inaccessible full-text
limitations are explicit; repository venue labels alone are not acceptance
evidence. Recorded DD-20260930-GAP-REVIEW as a recommendation, not a frozen
protocol or authorization to run.

Status checks: RQ3.7-C Qwen progress is complete with 4,200 terminal logical
targets; reduced local RQ3.8 Qwen completion is supported by its latest decision
and all three shard completions in the queue log. Terminal counts are not
successful/new-call counts. Both need complete analysis before efficacy or
generalization claims. No remote-job status was inferred from local artifacts.

Main recommendation: identify when a fixed model can use real graphics to
perform a specific diagnostic comparison beyond matched text and repetition.
Analyze RQ3.7-C/RQ3.8 first, then pursue only evidence-backed mechanisms. Keep
positive Qwen evidence, primary versus event-group uncertainty, node-scope
harms, perceptual limits and input cost explicit. No new model calls, CPU/GPU
tests, preparation, queue changes or raw-result changes were made.
# 2026-09-30 — RQ3.7-C / reduced RQ3.8 completed Qwen analysis

- Scope: offline analysis only; no inference, CPU regression, smoke, preparation,
  model service or agent launch. Original results and runtime code unchanged.
- Audited 4,200 RQ3.7-C and 4,860 reduced RQ3.8 terminal positions. Resolved
  historical references via original artifact roots. Kept model failures;
  excluded 78 RQ3.8 design-infeasible positions (20 distinct cases), separately
  from request timeouts and three unavailable historical references.
- Implemented reproducible analysis scripts under RQ3.8/scripts; Qwen-only
  paired Pratt/dz/Holm, connected-event sensitivity, missing bounds, complete
  metric tables, root/fault/observability profiles, cost and no-op audits.
  This bypasses but does not modify the old analyzer's superseded zero-fill.
- Actual delivered RQ3.8 evidence text agrees across nonduplicate conditions;
  graphical arms share full text. The fixed dashboard guide is an explicitly
  reported difference from text-only. No global large-artifact rehash performed.
- Report: docs/experiment_reports/RQ3_7C_RQ3_8_Qwen_Analysis_2026-09-30.md,
  six analytical figures, four unchanged delivered PNG examples, 60 sampled
  paired-case records; 16 pairs of reasons reviewed, four targeted fact/image
  checks. Not a double-annotator grounding study.
- Findings/recommendation: see DD-20260930-C38-ANALYSIS. RQ3.7 retains conditional
  positive evidence; current RQ3.8 FULL is worse than matched text. No new
  experimental route has been scheduled. User can inspect the report first.

# 2026-10-01 — RQ3.10 implementation and static-only handoff

- Authorization: design/implement next study and source-only checks, then stop.
  No subagents, CPU regression, case registration/preparation, browser rendering,
  tokenizer, GPU smoke, model service, formal inference or training launched.
  Qualified RQ3.9 and its interrupted artifacts remain paused/unmodified.
- User reminded that competitive-root experiments already had limited gains.
  Rechecked RQ3.6-B2 scope_competition source/report: host+peer−anchor pooled
  paired+.0123 Graph/+.0059 Text, both Holm1. RQ3.1 X also regressed. New study
  does not claim that peer addition, grouping or competition wording is novel.
- Registered narrow hypotheses: independently active stable control and
  coverage-qualified soft conflict/unknown, then exact-computation text versus
  shared service-by-host board versus the same permuted visual cells.
- Delivered RQ3.10 five modules/package marker, six-arm config, three canonical
  descriptions, plan/history audit, future preparation/CPU/smoke/formal/recovery
  and analysis entry points.140 exposed eval cases,60/60 AIOPS+20 Aegis;
  840 formal positions;900 initiated-call cap includes18 smoke+42 recovery.
- Preserved original complete text and existing renderer components/operations;
  added scope.matrix/tiles and shared glyph helper. Recompiled browser bundle;
  no actual dashboard generated or visually qualified in this session.
- Corrected untested anchor voting, negative text in positive-only rules,
  direction qualification, boundary counter resets, sample/clock binding,
  nonfinite-derived-value handling, unknown cost accounting and launch gates.
- Static outcomes: AST/bytecode/JSON/bash/import/DTO/placeholder checks,
  Ruff F-series, renderer TypeScript and bundle compilation, targeted diff
  whitespace checks. No runtime tests were substituted for static review.
  Record: RQs/RQ3_10/descriptions/static_review_2026-10-01.md and version-bound
  RQs/RQ3_10/results/scope_v1/qualification/static.json.
- Next only on user instruction: actual source/canvas/processor CPU qualification
  and independent visual review. First report real stable-active/conflict/testable
  peer counts; do not automatically spend inference on a mostly inapplicable
  design. Efficacy, baseline superiority and generalization remain unknown.

# 2026-10-01 — RQ3.10 CPU qualification and source applicability blocker

- User authorized CPU/GPU tests then preparation/formal if passed. Added
  distinct smoke-only preparation/CPU scope; formal still requires all140-case
  processor checks. No scientific rules or cohort changes.
- Repaired invalid synthetic renderer fixture; ten regression categories pass.
  Three smoke cases prepared in1.52/2.03/3.89s, CPU capacity/equality checks
  initially7.30s; maxinput28,342+8,192output fits40,960context.
- Source-only eligibility audit:140 cases,8 pinned workers,21.88s. All489
  selected readings fail64-bin coverage; zero testable scope/soft-conflict cases.
  No-anchor counts44/60 AIOPS22,10/60 AIOPS25,19/20 Aegis. This is a real
  qualification failure of the design assumptions, not a model result.
- Actual1800×7894 MATRIX inspected: excessive Cartesian-cell whitespace.
  DOM equality/overflow checks passing does not imply useful readable encoding.
- Did not lower thresholds, infer pod activity from aggregate service traces,
  relabel counters as gauges, change anchors or select convenient cases.
  GPU smoke and formal remain unstarted (0calls); RQ3.9 stays paused.
- Current blocker and proposed unadopted revisions are recorded in
  docs/issues/RQ3_10_qualification_2026-10-01.md. Scientific/visual qualification
  must be resolved by a registered revision before expensive inference.


# 2026-10-01 — RQ3.10 v2 qualified and full local experiment submitted

- Latest explicit user goal authorizes deployment, CPU/GPU regression, complete
  experiment submission and then stop. Single primary agent; local Qwen only.
  RQ3.9 stays paused; earlier reports/data/results and dirty user edits preserved.
- Adopted DD-RQ310-NATIVE-SCOPE: fixed public acquisition cadence coverage at
  the same80% threshold, exact-source gauge aliases, public-entity hash anchor
  fallback and compact matrix/tiles. Exact140-case/three-smoke roster, base text,
  six arms, scoring/model recipes and900-call ceiling preserved. v1 stays blocked
  with0 calls; no label/outcome-driven selection, health inference or interpolation.
- Full CPU regression passes12 categories/840 processor checks in73.38s;
  max29,411 input +8,192 output <40,960; no design/context exclusions.280 actual
  boards pass DOM;35 renderer tests pass; direct PNG and deterministic hash review.
- GPU smoke completed18 positions/16 actual calls/2 same-input references in
  180.25s including startup. All responses/IDs/usage/commit artifacts passed
  runtime review; output reasoning remains imperfect and is not an efficacy gate.
  Final offline partial-cost directory fix was separately checked with real and
  interrupted streams plus full CPU; byte-identical inference chain proven.
  Original smoke source/attestation retained, no replay or budget/clock reset.
- Formal queue acknowledged751 actual requests +89 references =840 positions
  over60/60/20 AIOPS22/AIOPS25/Aegis eval cases.36 request workers,8 aggregate
  writer threads. PID supervisor44540/server44548/runner45040; first
  34 atomic completions verified at receipt. Official BF16 Qwen local GPU,
  no Slurm/Gemma/training/attention/new test or automatic follow-up.
- Source archive SHA256 5f417056831fcc8c1b32116590ee81cf4a11debc8ce432cdfe3ce6d241117548;
  durable receipt RQs/RQ3_10/results/scope_v2/formal/submission.json and handoff
  RQs/RQ3_10/results/scope_v2/logs/2026-10-01_formal_submission.md. Resume entry
  `bash RQs/RQ3_10/scripts/local.sh supervise --execute` trusts committed flags;
  no completed artifact graph reconstruction. Owned server stops after queue.
- Limited mechanism applicability:23 AIOPS22 shared stable-conflict cases,0 in
  AIOPS25/Aegis. All cases are exposed eval. No final MRR/credibility/cost claim,
  no tuning with partial scores. Stopping now as requested; background run continues.


## 2026-10-01 — RQ3.10 complete analysis; RQ3.11 frozen protected compression successor

- Latest user goal explicitly requests complete analysis/report, next plan/code, static/CPU/GPU qualification, then next full submission. One primary agent, no delegation.
- RQ3.10 complete840positions/836done/4timeout,747independent completions and89references; all747calls and836positions final input/PNG/artifact/unchanged-score audits passed,84 frozen files verified. Four timeouts remain unknown, not zero; one real model failure retained zero.
- Primary AIOPS MATRIX−BASE +.0181/Holm.8626, MATRIX−TEXT +.0340/p1, MATRIX−TILES −.0078/p1; no registered contrast significant. MATRIX total-token mean23,857 vsBASE13,628, +75.1%. Limited qualified negative controls do not identify cross-dataset scope mechanism. Report docs/experiment_reports/RQ3_10_Qwen_Analysis_2026-10-01.md.
- Fixed an offline CPU reporter confidence numeric/schema error in separately derived analysis; original rankings unchanged, legal confidence="low"; original report and allVLMoutputs/scores preserved. Reviewed24pairs/10unique cases,4actual PNG crops; other queue entries are not claimed manually adjudicated. Ranking success does not establish grounded explanation.
- Next plan docs/experiment_plans/CanvasRCA_RQ3_11_Protected_Compression_Plan.md. Same140exposed eval,8arms,2fixed budgets,HIGH preselected; strong lossless exactTEXT + independent repeat, encodedTEXT twins, coarseV patch ablations. No newtest/training/attention/Gemma; formal1120positions,1180total initiated ceiling incl18smoke.
- Before any GPU call, v1 CPU showed37,906overrides and visual inputs exceeding strong exactTEXT. Preserve v1 source/plan/static/CPU/preparation; v2 removes an override only if the complete finite signature remains exact. Public numeric/cost feedback only; zeroGPU/model outcome feedback. Quantized q/design unchanged, all280compatible PNGs reused with hashes/renderer identity checked; deterministic actual repeat identicalPNG/HTML. Static passed; refreshed complete CPU qualification pending at this log boundary.


## 2026-10-01 — RQ3.11 v2 qualification passed; full queue submitted

- Static/CPU/visual/academic review passed;140×8actualprocessor checks62.93s,max18914+8192<40960,zeroexclusions;280same qPNGs/DOM records retained, source and byte hashes checked, actual direct image/deterministic review passed. Public-only redundant patch removal reduced37,906→20,121; finite signatures equal, no minimum/causality/accuracy guarantee. v1 preserved,0GPUcalls.
- GPU18/18calls completed170.24s inclstartup; all completion graphs verified270.88s<600; full responses read, enriched actual inputs/PNG/stream/conversation/scoring audit passed.18finish_stop,124–307outputtokens; confidence10high/8medium. Reason-unit and chronology/topology errors remainmodeldiagnostics; no answer-guided changes.
- Fullqueue1103actualrequests+17exactreferences=1120positions,140exposed eval,140independentTEXTrepeats; HIGHpreselected.36requestthreads,8artifactwriters, localofficialBF16Qwen/triton. Receipt at2026-10-01T19:04:58.874014+00:00 observed92atomic commits/noerrors; first3graphs separatelyaudited; GPU100%,10running/25waiting atacceptance. PIDs103303/103310/103764.
- Receipt RQs/RQ3_11/results/protected_v2/formal/submission.json; fullhandoff results/protected_v2/logs/2026-10-01_formal_submission.md. ArchiveSHA8cd66de375ff4f2cede5474d95bd8aedb6acf8cfac20d2fb9d27993d4f77fb7b; config protected_compression_v2.json. Formal1162+smoke18 total1180ceiling; oldRQ3.10consumption767preserved. No efficacy claims/partial tuning/newtest/training/attention/Gemma/follow-on. Agent stops at submission, supervisor finishes queue then closes ownedserver.


## 2026-10-01 — RQ3.11 complete result analysis and report

- Status: exposed development batch ended normally at 16:12 Toronto; 1120 terminal positions, 1108 with results including17 references, 12 explicit request timeouts. Formal1103 initiated/1091 complete, smoke18 complete. Two duplicate-ID model answers retain zero scores; no request retry or new GPU work in this analysis.
- Final offline audit reproduced all1091 unique completion graphs and1108 scores,140 public compiler inputs,280 PNGs,85 archived source files,20 checkpoint SHA256 entries and8 tokenizer/processor blob identities. Global configs/recipe/renderer/scorer and frozen roster match. Independent Pratt/Holm statistical verification passed. Reporting-only main/gates additions have separate source provenance.
- Primary AIOPS HIGH visual−exact text ΔMRR +.004861/n120/Holm1, paired total tokens +3.103%; HIGH visual−encoded text −.000700/n119/Holm1, tokens +5.704%; protected−coarseHIGH −.018091/n117/Holm.6091. LOW−HIGH +.029412/rawp.0414 but Holm.1656/group.3893. No registered comparison significant and no post-result candidate substitution.
- Known-side missing-outcome bounds keep HIGH visual−text and HIGH patch−coarse full120 mean deltas below0; these are algebraic unknown ranges, not confidence intervals. All3360 finite numerical signatures preserved,20,121 patches; neither RCA utility nor causal/explanation fidelity follows.
- Read24 paired explanation entries/12 unique cases plus4 full actual PNGs; remaining67 review-queue entries not adjudicated. Confirmed unit/chronology/binding/attribution errors include correct-ranked but faulty explanations. Confidence categories are not calibrated probabilities.
- Detailed Chinese report: docs/experiment_reports/RQ3_11_Qwen_Analysis_2026-10-01.md. Tables, PNG/SVG, audits, manual selection and reviewer disposition: RQs/RQ3_11/results/protected_v2/analysis_reviewed_v1/. Findings/roadmap/report index updated. No successor experiment, training, attention, Gemma or test initiated.


## 2026-10-01 — RQ3.12 next experiment deployed; static-only boundary complete

- User goal: synthesize historical/current results and conversation_oct_01.md, write next plan, deploy code, perform static checks, then stop. Single primary agent, no delegation.
- Adopted rq312_conditional_residual_v1: reference-only blocked-CV dependency predictions, candidate anchor profiles, observed/expected/residual/error-scale comparison and disagreement-first probes. Associations are not interventions. Preserve exact12M plus R/L/G, identities, candidates and original scorer. No healthy-peer or node-affects-all assumption.
- Six arms over the existing140 exposed eval: exactTEXT and real independent repeat, observedTEXT/VISUAL twins, conditionalTEXT/VISUAL twins; COND_VISUAL preselected. CPU residual heuristic is limited/non-CIRCA and keeps fallback applicability. Future840positions,900attempt allocation incl18smoke; current-major40000 budget review required without resetting spent calls.
- Plan, literature/claim ledger and design decision consolidated in RQs/RQ3_12/descriptions/RQ3_12_experiments.md; three canonical descriptions and one findings file. Additive diagnostic.matrix shared renderer preserves existing component semantics and source edits; prior results continue to use their original frozen archives.
- Static AST/compile, JSON, bash-n, all local exported-symbol linkage and TypeScript noEmit pass; source1589total lines, one shell. Source review/completion audit retained under results/conditional_v1/qualification/. All4 global scientific/local-projection config hashes match frozenRQ3.11 authority.
- No preparation, reference-model fitting, CPU tests, renderer build/PNG, tokenizer loading, smoke, formal, newtest, Gemma, attention or SFT/RL run. Runtime/efficacy remains pending. Stop at requested static boundary; future execution requires whole-roster CPU applicability/cost/capacity and actual visual/scientific/budget review before model qualification.


## 2026-10-01 — RQ3.12 CPU资格失败，未启动GPU

用户授权CPU回归、GPU smoke及资格通过后全量启动。六组CPU方法检查、25个renderer CPU tests、280张实际DOM及deterministic PNG、官方模型28文件身份、全840输入容量通过；两个AIOPS竞争案例各0，COND_VISUAL/ET主要范围input比1.339239，适用性/成本失败。全候选亦无两共同目标竞争对；105个参考拟合与独立NumPy一致。Aegis问号图的12条指标均参考16/32有效格，低于60%；均匀格缺失不等于原采集失败。按预注册GPU前停止规则保留失败，0模型调用；未改变阈值/队列/配方/score。已请求用户决定新版本采样支持/响应及传输修订。证据：RQs/RQ3_12/results/conditional_v1/logs/2026-10-01_cpu_qualification.md、qualification/cpu.json、diagnostic_failure.json。

## 2026-10-01 — RQ3.12 v2 删除不可计算展示，按用户要求停在代码边界

- 用户授权修改问号图相关代码、删除无诊断信息的缺失内容，随后明确“代码改完之后就先停下”。该指令暂停此前 CPU/GPU/formal 后续执行；单一主 agent，无委派。
- 新版 rq312_conditional_residual_v2 从冻结 label-free context 所绑定 canonical metrics 的 timestamp 列提取独立采样支持，覆盖率不把未采样画布格当缺失；真实采样格的 null 仍计分母。样本/CV/60%/支持域阈值不放宽，未插值或添加新指标。
- 新增 diagnostic.compact：OBS 只画 A，不可计算/conditioned 比较不绘制；删除空候选行和无观测列；整表为空不生成 PNG，保留 exact 原始文本、所有候选与病例分母。text/visual 共用稀疏表，精简重复附录和按有效行数定高；不能推定成本或预测资格已修复。
- v1 原源码/renderer/bundle 保存为 failed_cpu_source_v1.tar.gz；原 140 例/280 图/CPU 失败、预算和记录保留。v2 使用独立准备/结果目录，继承同一 900 allocation，不重置消耗。
- 静态 AST/compile、JSON/config、bash-n、模块接口、compiler 依赖边界、TypeScript noEmit 通过；新增测试定义未运行。v2 未准备/渲染/build、CPU 回归、tokenizer、GPU smoke 或全量运行，模型调用 0。代码效果、竞争覆盖和成本仍需用户继续后重新验证。记录：RQs/RQ3_12/results/conditional_v2/logs/2026-10-01_static_repair.md；qualification/static.json。

## 2026-10-01 — 按用户追加请求导出历史原图和新版三例预览

- 新请求仅授权例图与Windows文件导出，不恢复完整CPU/GPU/formal。今天RQ3.10、RQ3.11正式队列结束；RQ3.9正式中断，RQ3.12 v1 CPU方法资格失败。原有失败和分母保留。
- 历史图来自模型实际input和atomic completion对应的PNG，复制后逐张SHA核对；纯文本臂附原始输入。RQ3.11一个固定case/arm超时，按同数据集opaque排序选择另一已提交完成例并标注，不按正确率选图。
- 仅三个固定exposed-eval案例生成RQ3.12 v2六PNG。预览发现并修复新compact高度/SVG尾部空间接口问题，两次失败保留；六图DOM审计、三张COND目视和单例确定性PNG通过。观测列7/9/12、预测行0/1/0，不推定竞争覆盖/成本资格。预览使用独立bundle，canonical bundle和准备/资格不改写，0模型调用。
- Windows目的地 /mnt/c/Users/10511/Downloads/例图/10_01；共78个arm×dataset记录、30PNG、48纯文本输入，含额外v1失败对照；index.html/CSV/manifest已生成，浏览器筛选通过。记录 RQs/RQ3_12/results/conditional_v2/logs/2026-10-01_preview_export.md，完整实验目标仍暂停。

## 2026-10-01 — 用户恢复 RQ3.12 v2 资格：CPU回归通过，参考竞争适用性失败

- 用户授权CPU回归、GPU smoke，均通过后full；解除代码/例图暂停，single primary agent执行。显式canonical build→static→登记→完整140准备→CPU；八distinct physical cores，254实际PNG、13空表回退，完整病例分母不变。
- 八组方法/隔离/稀疏/commit回归、renderer25 CPU tests（10 opt-in browser tests skipped）、254实际DOM/field/SHA审计、六固定例独立PNG repeat通过。840输入零容量排除，max21206+8192≤40960；official checkpoint/tokenizer/processor28 files verified。CPU132.843s，主要input比1.134522≤1.20。
- 方法readiness失败：AIOPS2022/2025竞争案例各0/60，低于合计30/各10。全候选仅2/6例有任何预测，4/12有效预测单元，没有两个共同目标的候选对；非六行显示选择问题。Aegis3例有共同目标对，但无注册分歧竞争案例。
- 独立NumPy正规方程核对823个参考拟合一致（最大相对差3.54e−14）。观测1075/1680较v1 497改善，输入成本/图形修复没有建立候选比较适用性。保留failed report、全部准备及failed_cpu_source_v2.tar.gz，不降低门槛/改队列/做外推/试模型成绩；0模型调用，GPU smoke/full未启动。证据 RQs/RQ3_12/results/conditional_v2/logs/2026-10-01_cpu_qualification.md；下一步需版本化修订参考响应或数据支撑。


## 2026-10-01 — RQ3.12参考适用性修订完成；CPU/GPU通过，完整六臂已启动

- 用户授权先解决参考预测适用性，再启动全量；单一主agent执行，无委派。当前rq312_conditional_residual_v4从同案例完整label-free公开参考池选择受原CV/支持标准约束的共同目标与anchors，新增最多6原始操作数在六臂相同，保留原12M/R/L/G、完整候选/140exposed-eval，比较2共同目标/2candidate。旧失败/接口尝试保存，参考阈值/队列/统计/成功条件未降低；compact宽容量仅按实际列数适配，旧12列/旧matrix行为保留。
- CPU完整140/266实际PNG/840inputs，9方法组、25renderer tests/10旧opt-in skipped、266真实DOM/hash、4目视及确定性重绘通过。1120独立reference fit差7.54e-13、115068source-clock向量一致/6臂同新增事实；A22/A25竞争54/50，input CV/ET1.092284，max21940+8192<40960，0排除/28官方文件核对。CPU389.49s+三例47.83s，源94文件与3补充recipe依赖冻结。
- GPU smoke18/18完成含startup212.272s≤600，完整graphs及全部18actualinput/output阅读审核通过；18JSON/IDs有效，输出107–223tokens，15high/3medium。保留明确单位/log2/时间/理由粒度错误，不宣称信任提升，不按答案调参/重试。
- 全量840位置=811预期真实请求+29exactreferences，140独立重复真实；注册source/病例/6臂/主要统计族/CV预选保持。提交确认14原子commit/36在途、首3完整图谱审计通过，0infra失败、GPU99%，supervisor67677/server67685/runner68101。本轮全版本同一900 allocation含18smoke，旧调用保留，RQ3.1预算/旧RQ3 blanketcap权限范围纠正在协议0V3。
- Receipt RQs/RQ3_12/results/conditional_v4/formal/submission.json；交接logs/2026-10-01_formal_submission.md。后台完成队列后关闭ownedserver，agent停在全量启动确认；整批MRR/视觉价值/总成本/理由审核未完成，无新test/Gemma/attention/SFT/RL/follow-on。新版18arm×dataset例图/6PNG在Windows原目录05_RQ3.12_v4_参考预测修订，旧例图保留。


## 2026-10-02 — RQ3.12完整分析

840终态，811formal调用/801响应/10超时，18smoke。801完整graph和评分、140公开compiler parity、94冻结源/3附加runtime、实际transport及token守恒审核通过；离线operand接口修复限定report，不改变原输入/答案/分数。主要CV−ET+.0384/CV−CT+.0365/CV−OV−.0275，pH均.5671，成本+9.06%，不采用CV。参考竞争104/120但目标真实变化23/120、精确root目标0/预测行2。36case/216位置214解释阅读，未知轴保留，不宣称信任增益。报告docs/experiment_reports/RQ3_12_Qwen_Analysis_2026-10-02.md。用户授权继续结果驱动新plan/实施/全部资格及启动完整队列，single primary。


## 2026-10-02 — RQ3.13观测时间画布资格完成；按最新指令停在smoke

- 用户将目标改为代码/static/CPU/GPU smoke完成后停止，暂不启动全量。full_launch_authorized=false门禁已验证，formal0；单一主agent，无委派。
- 原始12M真实采样/观测包络，原v4全部exact事实和候选保留；同信息强文本、时间图、原文字截图及文字/时间图两类真实独立重复，140exposed-eval/未来840矩阵。无需依赖拟合或非零scale，参考仍非健康/因果认证；7空表原文回退，不排除病例。历史RQ3.12输入/分数/811+18calls不变。
- 静态1144有效行/五模块、全140准备/266独立PNG/8物理核；7回归组、1680独立数值复算最大reldiff2.78e-17、全部source timestamp、266实际像素/文字盒、六真实确定性重绘、840processor输入/28官方文件通过。A22/A25适用性57/55，input比1.087043，max22143+8192<40960。CPU141.054s+三例7.841s；8实际PNG目视、primary科学/预算审查完成，未称独立评审。
- 129文件source/runtime/font冻结；GPU18真实/18done、含加载185.152s<600，无超时/retry/infra/model格式失败。18完整graph及实际输入/body/PNG/评分/token守恒通过；输入340414=文字333979+image6435、输出3557。
- 全18解释阅读并按M/R/E01核对，单位×1000、M实体绑定、更早onset及把公共split/偏差当因果认证等反例保留。unknown轴未穷尽审核，不宣称视觉价值/可信度改善，不按smoke正确率改方案/挑重复。
- 全门禁及archive identity复核；ownedserver/runner关闭，GPU释放，无formal、新test、Gemma、attention、训练或后台后续。报告docs/experiment_reports/RQ3_13_Qualification_2026-10-02.md，计划docs/experiment_plans/RQ3_13_Observed_Excursion_Plan_2026-10-02.md，交接qualification/completion.json。


## 2026-10-02 — RQ3.13用户授权全量启动

- 最新请求“好的，现在帮我启动全量实验吧。”解除smoke停止边界，不扩大科学矩阵。冻结config/registration/preparation、原资格/18smoke及source archive保留。仅执行门禁局部后继；128其他冻结文件字节不变，非门禁AST及原资格检查结构一致。qualification/activation_v1/保存源兼容/新archive/授权receipt；静态、11授权检查、7CPU-unit组通过，0新增烟测。single primary，无委派。
- 正式140×6=840位置，819真实请求+21精确引用，280真实独立重复；A22/A25各60/Aegis20 exposed eval，Qwen本地，36并发/8writer；18既花调用在同900分配/882formal cap中保留。未改prompt/score/figure/tokenizer/模型解码或使用新test/Gemma/attention/training。
- 首次nohup launcher未存活且0调用；改用独立setsid后台会话。supervisor21497/server21505/runner21930，加载99.195秒后队列正常；启动快照25atomiccommit/36started/61initiated，0failureflags，GPU100%/78946MiB，首3完整graph/实际body/PNG/policy审计通过。
- 启动receipt RQs/RQ3_13/results/observed_excursion_v1/formal/submission.json；交接formal/logs/2026-10-02_full_submission.md。后台完成registered队列后关闭ownedserver，无后续任务。当前仅启动确认，整批MRR/成本/理由审核待完整结果；不从部分成绩改方法或扩大队列。

启动follow-up：105complete/36started/1request_timeout；已确认是登记300秒客户端超时，消费/partial/未知usage保留，未自动retry或改recipe，完整队列继续。formal/launch_followup.json记录实测，不将早期0失败快照误当持续零失败。


## 2026-10-02 — RQ3.13 full completion and quantitative status review

- User asks to check the completed run. Formal ended12:51 Toronto,4117.58s includingstartup;840terminal positions,808real responses/21references/11timeouts;6invalid-ID answers retain0,802valid.18smoke+819formal=837attempts. OwnedGPU services stopped, no unexplained missing position or active ledger call.
- Frozen source unchanged. Offline artifact/scorer/transport checks passed808graphs/bodies,829scores,140public replays/266PNGs,2x129archives and28officialmodel/tokenizer/processorfiles. Independent round12Pratt/Holm matches; per-dataset/fault/common110primary/repeat/missingbounds/fullattemptusage saved analysis_reviewed_v1. Hash definitions normalized at their own layers; scoped ledger call keys resolved to artifact keys. No model replay or source/output/score mutation.
- Primary EV−EXACT+.066377/n115/Holm.454856/group.833692;EV−TEXT+.057902/n116/Holm.454856;EV−PIXEL+.001449/n115/Holm.801547,groupdelta−.012949. DeploymentA22+.103216,A25+.030172;Aegis−.129167. Paired total EV/EXACT1.087973, no cost reduction. Registered significance gates fail; not adopted and no best-arm/repeat selection.
- Completion status was reported with216-position explanation review pending at that boundary; the former simple report is now replaced by docs/experiment_reports/RQ3_13_Qwen_Analysis_2026-10-02.md at the user's request. The detailed analysis entry below records the subsequent review. No reason-trust/calibration/independent-test or publication-ready claim. No new experiment/test/Gemma/training/attention launched.

## 2026-10-02 — RQ3.13详细分析完成；RQ3.14仅设计

- 用户要求详细分析最新实验、以详细报告替代并删除旧简报、综合历史报告并设计兼顾AIOPS/Aegis的下一轮；single primary，无委派。此次0模型调用、无CPU/GPU运行资格、准备、训练或新推理。
- 详细报告 docs/experiment_reports/RQ3_13_Qwen_Analysis_2026-10-02.md。30准确率/30成本行、6登记对比、20Aegis全病例核对原CSV；829响应副本与原输出一致、17历史报告SHA/本轮source哈希和本地链接核对。旧简报仅保留SHA/size删除审计，独立资格报告/原日志/所有模型输入输出分数不变。
- 完成登记36case/216位置解释阅读，213响应/3超时；全20Aegis扩展并集44case/264位置/260响应，定向source检查14claim：13事实/算术矛盾+1未充分支持的因果先后。未知轴保留，不宣称全量grounding率。原/新增M数字后缀映射1551/1680不一致，是真实接口歧义，不是literal-ID冲突或1551模型错误。
- A22 EV−EXACT+.103216/n57、A25+.030172/n58；Aegis−.129167/n20，4好/7坏/9同，top1修复/破坏2/5，三例1→0在截图与视觉重复重现。参考期瞬态被包络摘要压平、资源症状压过局部Trace、编号/单位/时序/排除推论问题均落盘。现有主要显著性失败、成本+8.8%，不采用EV；不把观察路径当已识别独立因果贡献。
- 回读17份canonical历史报告/综述并保存identity/read-scope；所有历史batch、smoke、exposed test及原统计族保留各自有效性边界。新完整18项数据集探索族pH均1，不以事后子组救主结论。
- 新方案 docs/experiment_plans/RQ3_14_Typed_Window_Comparison_Plan_2026-10-02.md，RQ3_14三description与provisional DD/未运行findings已建。9arms、220exposed eval（AIOPS60+60/Aegis100）、唯一编号/类型规则/全窗口摘要分开控制，预选SHAPE_VISUAL，Aegis正向增益纳入主要门槛；拟1980正式位置/2040allocation不清零历史支出、不构成执行权限。本次停在报告与设计，尚未实施或启动新实验。


## 2026-10-02 — RQ3.14用户授权替换设计并资格后全量启动

旧RQ3.14只有文档，无代码/准备/调用。删除旧未执行计划与findings并保存最小SHA审计；新计划RQ3_14_Observed_Binding_Plan_2026-10-02.md。9臂220 exposed eval，停止候选响应预测的默认主线，验证观测/绑定修复。继承基础输入与公共附加operand，不显示预测。1980正式位置，2040allocation，门禁未通过前不调用GPU。用户目标止于全量可靠启动。


## 2026-10-02 — RQ3.14 unified rewrite qualified; full supervisor submitted

Deleted bespoke RQ3.14 code was not restored. New five-module implementation uses registered metric.line/trace.paired_bars and appearance/indexing/spacing; only literal.text is added for a screenshot control. Missing positions are connected without decoration. Full220-case/9-arm CPU,660 actual PNGs,2640 numeric rows,9 deterministic rerenders and35 renderer tests passed. Input ratios1.155633/1.184700/1.154480; max23399+8192<40960, no exclusions. Official model identities and167 source files frozen. GPU18/18 completed in185.20s, no infrastructure/timeout/truncation; every actual input/output reviewed. Reasoning errors remain model outcomes, no score-based tuning. Full1980-position supervisor submitted; authoritative live receipt under RQs/RQ3_14/results/unified_observed_v1/formal/. Task stops once queue commits, not on full experiment completion. Detailed log: RQs/RQ3_14/results/unified_observed_v1/logs/2026-10-02_qualification.md.


Formal launch verified: supervisor 70617, runner 71339, server 70624 alive; 31 atomic completed markers at verification. Ledger states: {'complete': 31, 'started': 36}. No partial efficacy scores inspected. The authorized launch stopping boundary has been reached; detached full experiment continues unchanged.


## 2026-10-02 — RQ3.14显存只读检查；用户保留0.75

用户撤回降至0.65的要求；从未修改配置或重启。当前argv/YAML/metrics均为0.75。整卡约84.92/95.59GiB；Windows WSL vmwp约81.6GiB，不能仅归因桌面程序。启动weights51.1GiB、KV12.92GiB；保留池/动态分配/WSL驱动开销是待区分解释，没有worker内部allocated/reserved快照，尚未确诊。日志无CUDA OOM；另有5请求超时，未归因显存。完整原始只读证据：RQs/RQ3_14/results/unified_observed_v1/logs/vram_observation_20261002_191540.json。正式实验继续；无新调用、重试、源码或实验条件改动。

## 2026-10-02 — RQ3.14正式完成与详细分析落盘

- 用户请求完整总结与报告。single primary，无委派；仅离线分析，没有新模型调用、实验源码/输入/输出/评分改动，未恢复显存诊断。正式21:49:50 Toronto结束，自有模型服务退出。
- 全1980终态=1966真实响应+14request_timeout。WSL中断的36尝试保留并补齐未commit位置，2016formal+18smoke=2034/2040；50次失败/中断usage未知，不填0。16未知/重复实体回答保留原零分；所有1966 finish=stop，无输出截断。
- 全1966completion graph/独立评分/实际prompt，877image transport、220public invariants、167冻结文件审计通过。手工Pratt含零并列秩方差+独立Holm核对20统计项一致。分析中修正仅offline子组mask的注册分母/缺失界限记账，重建分析后校验，正式分数不变。
- V−RAW A22 +.117251/A25 −.020904/Aegis −.011167；四主要采用门槛未过。V−TEXT全体−.052294，Holm病例.113887/组.052700，均不显著；V−MARKLESS−.006957无优势。唯一显著次要TEXT−SAFE n218 +.046942，Holm病例.016502/组.014463，属于exposed-eval文本摘要收益。
- 同旧Aegis20例视觉损失−.129167→−.058333，新增80差+.000625；不是完全修复。四侧共同54个A22病例上视觉绝对MRR下降、基线也下降，净差近似不变；不宣称A22跨轮进一步进步。总token V/RAW为1.154909/1.183810/1.153888，无降本。
- 完成固定36case/324位置的321份解释阅读，3未知；15case/21response/25定向claim检查=17矛盾/6局部支持/2证据不足。未核验轴保留unknown，非盲、定向审核不估计总体错误率。源单位泛化标签357条、历史alias后缀差2429/2640仍可见；作为输入局限记录，不冒充模型错误计数。正确MRR也可能伴随错单位、时间、实体与因果理由。
- 详细报告 docs/experiment_reports/RQ3_14_Qwen_Analysis_2026-10-02.md；原始派生CSV/JSON、两组PNG/SVG及再现脚本在 RQs/RQ3_14/results/unified_observed_v1/analysis_detailed_v1/。更新findings/roadmap/报告索引。按注册边界停止本实现，不自动使用剩余6调用；RQ3整体目标尚未达成。


## 2026-10-02 — RQ3.15 implemented and qualified; stopped after smoke

User-authorized endpoint: code, full CPU, actual image review and bounded GPU smoke, then stop. Single primary agent. Implemented public RequestPairPacketV1 and two registered unified-renderer components; five modules / 1161 functional lines, 176 source files frozen. Historical source/component/operation semantics and artifacts preserved.

Full220 CPU passed: applicability A22 60/60, A25 55/60, Aegis96/100; 9 complete BASE fallbacks retained. 422 PNGs, 58496 bindings, 341635 independently checked selected population pairs; six byte-identical rerenders and 11 actual image inspections. V/BASE input ratios1.154363/1.187519/1.194581, V/PAIR_TEXT1.039072/1.042095/1.035798. All input budgets/capacity passed. GPU18/18 in203.26s, no timeout/truncation/infrastructure failure; unique real repeats and actual input/PNG/provider-usage/scorer equality audited. Local Qwen BF16, context40960/output8192, GPU memory utilization0.75. Owned service stopped and completed-phase fast resume verified.

No smoke-based tuning. Ranking/explanation contradictions and a numerical comparison error are preserved; graph understanding, RCA improvement and trustworthy explanation remain unestablished. Formal1320 positions registered only, formal calls0, full_launch_authorized=false. Stop as requested; no automatic continuation. Detailed report: docs/issues/RQ3_15_qualification_2026-10-02.md. Plan: docs/experiment_plans/RQ3_15_Request_Joint_Plan_2026-10-02.md. RQ log: RQs/RQ3_15/results/request_joint_v1/logs/qualification_20261002.md.

## 2026-10-02 — RQ3.15 full experiment explicitly authorized and started

Latest user request: “我们不是注册了最新的实验吗？而且你做的test都通过了吧。那就启动全量实验吧。” This supersedes the fulfilled post-smoke pause for this frozen matrix only. Single primary agent. Reused all220 CPU preparations, actual PNG reviews and18 measured smoke calls; no extra smoke or outcome tuning.

Operational activation modifies only two authorization/compatibility functions in RQ3_15/src/gates.py, with an explicit user receipt bound to immutable config/registration and current source.176-file set, all scientific dependencies, renderer and the rest of the gate AST are identical to the measured archive. Original seven passed reports and source archive preserved. Activation static and negative checks passed; effective source archived separately. No scientific thresholds, arm definitions, budget or model settings changed.

Detached formal launch2026-10-02 23:49:54 America/Toronto; verified23:53:42.220 cases×6 arms=1320 positions; expected first pass1284 real calls+36 no-applicability references, with genuine PAIR_REPEAT for all220. Formal limit1362+spent smoke18=total1380. Local Qwen BF16/context40960/output8192/memory-utilization0.75, canonical launcher and live attestation passed. Snapshot17 committed responses+36 in flight,0 failures; supervisor2426/server2439/runner2980 alive, GPU utilization100%. No interim efficacy scores inspected. Background supervisor will stop its owned service on completion; no automatic next experiment. RQ log: RQs/RQ3_15/results/request_joint_v1/logs/formal_launch_20261002.md. Durable launch receipt and verification: RQs/RQ3_15/results/request_joint_v1/formal/.

## 2026-10-03 — RQ3.15 safely paused at the user's request

User: “我准备睡觉了，帮我立刻安全暂停实验。” This supersedes the previous full-run execution authorization until the user explicitly resumes. Sent SIGUSR1 to the verified runner2980 and supervisor2426 at01:06:58 America/Toronto. No new calls were initiated after the pause; all36 in-flight requests completed normally, with no new failed attempts during draining.

Shutdown verified01:10:34: runner/supervisor/server2439/engine2573 gone, port21955 closed, GPU memory2421MiB for the whole device.794 real responses and24 no-op references durably committed;4 earlier request-timeout positions preserved,822 terminal positions and498 pending of1320. Formal798 attempts+smoke18=816 spent; original limits and accounting remain intact. SQLite quick check passed; every done flag has its completed marker. Phase correctly remains incomplete; no partial efficacy analysis or source/config changes. Do not restart inference, services or automatic monitoring without explicit user resumption. Evidence: RQs/RQ3_15/results/request_joint_v1/formal/pause_verification_20261003.json and PAUSED_BY_USER.md. Latest launch receipt, roadmap, findings and plan index now record the pause.

## 2026-10-03 — RQ3.15 explicitly resumed from the safe pause

Latest user: “帮我重启实验吧。” This lifts the pause for the remaining frozen matrix. Single primary agent; no source/config/model/preparation changes, additional smoke or budget reset. All source-bound qualification gates passed unchanged. Fast resume checks use small flags and completed-marker presence; no bulk historical prompt/render/conversation/trajectory verification. Prior794 responses+24 references+4 timeout outcomes retained,822 terminal positions skipped; native queue correctly reports486 pending real calls+12 references.

Detached resume10:50:22 America/Toronto, verified10:53:42. Supervisor1925/server1939/runner2338 alive, live attestation ready, actual GPU utilization parameter0.75, context40960/output8192, BF16. Snapshot804 committed responses (10 new),36 new active calls,0 new failures; no old call key resubmitted. Formal798+smoke18 previously spent remain charged, with original1362/1380 limits. No partial efficacy inspection. Owned service closes on completion; no automatic successor. Historical pause records and pre-resume operational metadata preserved. Evidence: RQs/RQ3_15/results/request_joint_v1/formal/resume_receipt.json and resumes/20261003_105022/verification.json; RQ log: results/request_joint_v1/logs/resume_20261003.md. Latest roadmap/findings/plan index now reflect running status.

## 2026-10-03 — RQ3.15正式完成，详细分析与停止决定落盘

- 用户要求详细总结分析；single primary，0新增模型调用，无源码/准备/原回答/分数改动。正式11:42:16 Toronto完成，1320终态=1279真实响应+36精确输入引用+5超时；2重复ID模型失败保留零分。1284formal+18smoke=1302/1380，已知28,467,410 tokens，5次usage未知不补0。服务退出；历史启动/暂停/恢复快照保留。
- 审核1279唯一completion graphs、1315位置的评分/实际prompt/processor token、630图像传输、220公共输入约束及176文件资格兼容。独立Pratt含零/并列秩方差和Holm一致；42汇总行独立重算，报告30准确率行和33本地链接核对通过。有效源hash d988af3aa1a701d68d1831fd7ddfa140bc3ca4a20ac37123967a8ef2735978bc 不变。
- 主要V−PAIR_TEXT+.028135/n218，V−MARGINAL−.013441/n217，V−BASE AIOPS+.042373/n118、Aegis+.000667/n100；病例/事件组Holm均不显著。Aegis实际收益门槛失败，对PAIR_TEXT−.005219；预选方法不采用。共同215例敏感性及全注册缺失紧界限不改变决定；次要比较也均不显著。
- Aegis Top-1 45%→50%，Top-5 80%→71%（修复7/破坏16），平均输出候选4.05→3.61；没有固定长度干预，不将其当完整因果解释。重复与视觉100/100 Aegis MRR相同；联合/边际206/217同MRR，二维关系独有收益未建立。
- 适用性211/220仍通过；scorer粒度root端点覆盖24/60、18/60、41/100，下降关系与故障子组仅事后描述，不可按私有标签选方法或事后筛样本。阅读固定36例216解释，重新打开6实际PNG，26定向claim核验跨15例/22响应：18矛盾、6局部支持、2因果证据不足。unknown轴、单人非盲与非总体错误率限制明示。
- V/BASE总token1.1535/1.1857/1.1945，V/PAIR_TEXT1.0403/1.0418/1.0355；通过允许开销而非降本。BASE对RQ3.14 WINDOW_TEXT220输入完全一致，218共同完成病例Δ−.000917，无明显基线漂移；已暴露eval非独立确认。
- 最终报告 docs/experiment_reports/RQ3_15_Qwen_Analysis_2026-10-03.md；派生CSV/JSON、图、脚本、审核和完成receipt在 RQs/RQ3_15/results/request_joint_v1/analysis_detailed_v1/。更新findings/roadMap/报告与计划索引；执行原注册停止条件，结束此连续配对图路线，不自动修改布局、挑最高臂或花费剩余78次。RQ3整体部署/性能/视觉贡献/解释可信目标仍未达成。详细RQ日志 results/request_joint_v1/logs/final_analysis_20261003.md。

## 2026-10-03 — RQ3.16新计划与资格完成，按用户要求停止

- 用户授权下一步设计、落盘代码、静态/CPU/GPU smoke后停止。单一主agent复核19份历史权威实验/综合报告及当前Codex、对话主线；新计划 docs/experiment_plans/RQ3_16_Marginal_Coverage_Plan_2026-10-03.md。保留RQ3.15联合图不采用结论，不追认事后最高均值。研究边际数据点增量贡献与输出候选容量，固定公共事实、原PNG、220 exposed eval及事件组。
- 八臂BASE/PAIR/MARGINAL×FLEX/FIVE，加MARKLESS_FIVE及真实MARGINAL_REPEAT。FIVE仅schema minItems1→5及全FIVE共享说明，scorer/候选/配方不变；同期FLEX重复独立计费。正式1760位置/1802attempt，仅登记；加18smoke总1820，历史消耗保留。四项主要Holm病例/组比较、七项次要MRR及AC@5族、成本和跨数据集Top5护栏预注册，失败停止候选。
- 五功能模块1192有效源行；TypeScript构建和静态通过。复用211原图、新绘211去点对照，全部统一renderer；C20接通既有presentation开关，不增加组件/操作，不改缺测规则。完整CPU220/220、422图/32624绑定、3默认历史图字节相同＋3控制重绘、12实际PNG审查通过；9病例完整回退，45精确引用不排除病例。最大输入26141，输入比率对BASE为1.1540/1.1870/1.1941、对PAIR为1.0390/1.0420/1.0357，均通过。原341635对源数据数值资格继承并明示非重新抽取。
- GPU smoke18/18完成，205.27秒执行、392.91秒含逐请求审查；12个FIVE均五个不同合法ID，9次实际PNG传输，397439总tokens，评分/请求/schema/processor/usage一致，无基础设施错误/超时/截断。仍有时间排序、列表与理由、方向和因果解释错误，保留为模型结果，不按smoke分数调参，不宣称可信度改善。
- 自有server26529/engine26689/runner27065退出，端口21956关闭；真实完成态resume不加载模型、调用数保持18。当前源码合同612c92660201ece2cd6cdbbaf7cc7b33fe31ca18deebbea824be96b3641f82d1冻结184文件。**正式调用0、全量启动关闭，已按要求停止。** 下一步须新用户明确授权，不自动跑正式或后继实验。
- 详细资格报告 docs/issues/RQ3_16_qualification_2026-10-03.md；例图库 RQs/RQ3_16/results/marginal_coverage_v1/qualification/gallery/index.html；RQ日志 RQs/RQ3_16/results/marginal_coverage_v1/logs/2026-10-03_qualification.md。工程资格、单人科学审查不等于正式性能、视觉贡献或外部独立确认。

## 2026-10-03 — 用户授权RQ3.16全量启动

用户明确“行，启动新的全量实验吧。”，解除上一阶段资格后停止边界。只修改两处权限/资格兼容函数，AST及184文件依赖证明科学代码/renderer/输入/配置/评分/配方/门槛不变，原资格与归档保留；不重复18-call smoke、不重置已花调用。新有效源hash fbd23ac5b419c2a229c667a75403c0bceb3f04a28d32c1c3cfdc6e1d39f897a1。13:22:16 Toronto后台启动原八臂220例/1760位置，预计1715真实调用＋45回退引用；formal1802加既有smoke18，总1820不变。13:25:17核验7份已提交、36在途、无失败；supervisor2175/server2182/runner2928运行，attestation ready、显存利用率参数0.75、40960/8192、BF16。抽查新完成graph、实际完整prompt/PNG及token一致；未分析部分效果。自有服务随正式队列结束关闭，无自动后继。证据 RQs/RQ3_16/results/marginal_coverage_v1/formal/launch_verification.json；RQ日志 logs/2026-10-03_full_launch.md。


## 2026-10-03 — RQ3.16完整结果分析落盘，边际候选停止

正式1760终态：1713真实响应、45精确回退引用、2超时；9重复实体model_failure保持零分。正式1715加18smoke共1733/1820，自有服务退出。完整审计220公共/1713graph/1758prompt评分processor/843PNG及36项独立Pratt/Holm通过；36固定hash病例288解释阅读与12定向核验完成，未知轴仍unknown，无信任改善声明。详细报告 docs/experiment_reports/RQ3_16_Qwen_Analysis_2026-10-03.md，离线证据 RQs/RQ3_16/results/marginal_coverage_v1/analysis_detailed_v1/。

MARGINAL_FIVE MRR .5054，PAIR_FIVE .4436，MARKLESS .4963；四主比较病例/事件组Holm均失败，去点增量+.0091未建立，A25/Aegis对PAIR Top5−3.33/−3pp。已知配对成本符合预算但A25完整BASE未知界限[1.1776,1.2072]跨1.20，不称全量预算已实测通过。固定五相对边际FLEX次要MRR+.0315和AC5+.0776显著；不将次要正结果改称视觉机制成功。按原注册停止边际耗时候选，无自动换布局/选repeat/新实验/test；RQ3整体研究目标仍未完成。冻结科学源、原始输入/图像/响应/分数/资格/历史报告保持不变，本次0模型调用。RQ日志 logs/2026-10-03_analysis.md。


## 2026-10-04 — RQ3.18归因实现、静态与完整CPU资格通过，按要求停止（旧版，后续已由用户要求删除）

> 本段为历史过程记录。旧六臂计划、代码、测试及冻结产物已按用户后续明确要求删除，不是有效恢复入口；当前唯一方案是 population_readout_v1，见文末更新。

单一主agent复核RQ1.1/RQ2.1、旧RQ3及RQ3.1—17历史报告和当前Codex，按用户批准方案实施原生边际图归因，不增加诊断机制或继续拓扑组合。计划 docs/experiment_plans/RQ3_18_Marginal_Attribution_Plan_2026-10-04.md；六臂1320位置仅登记。统一renderer新增显式neutral_canvas，保留证据/设计/被抑制字段审计；原生V/K和历史默认语义保持，未改缺测规则。

5功能模块/1459行；TypeScript/静态/37项renderer浏览器回归通过。完整220例CPU通过：适用60/60、55/60、96/100，9完整文本回退；633 PNG/32624绑定、18重绘、15实际PNG人工审查；1320输入计数，最大26632+8192=34824/40960，逐数据集各臂平均输入/T最大1.065095。原Trace抽取资格明确继承，不称重新抽取。补齐未来报告Precision@1/3并加入完整离线结果分析与分数篡改回归，重跑静态/CPU；初始失败/旧通过报告与修复日志保留。

198文件源合同 `302da6e8647cf2e3b157ef0075e8eb6c6948b1137da8cd2b3c54714f48e29b15` 已冻结，历史来源/报告保护时序限制如实记录。唯一findings、路线图、计划索引已更新；详细资格 RQs/RQ3_18/results/marginal_attribution_v1/qualification/report.md；RQ日志 logs/2026-10-04_qualification.md。当前无新MRR/解释可信/实际总成本结论。**GPU smoke未运行，正式未启动，模型调用0；两类启动权限关闭，无激活凭据，停止等待指示。** 后续先核对累计调用账本及冻结身份，不自动使用历史授权恢复运行。


## 2026-10-04 — RQ3.18替代方案完成静态与CPU资格，停止

用户否定旧六臂归因方案，明确要求先重写计划、再完全删除旧计划/代码/脚本/测试结果，并确认CPU通过后停下。新总体耗时读数方案保留完整证据，以2×4呈现矩阵+3真重复检验文本读数与可分离视觉RCA收益；11臂2420位置，总预算2500，仅登记。旧版6485文件约792MB及旧计划已删除，无备份、旧调用0；其他历史610保护哈希保持。

五模块1315行；静态、共享renderer35项回归、220例/2420输入CPU和15份实际PNG审查通过，197源文件冻结，合同 `d24634c5caf064c62d41d8df0be2b2540d87487fcff6c680681c9b256c7e6f1c`。最大输入+8192=35003；全部逐集平均输入/T≤1.10。SIGUSR1导入覆盖与smoke回退等实现问题已修复重测；27离线替身请求验证停止恢复，真实模型调用0。**GPU smoke未运行、正式未启动、入口关闭，按用户要求停止。** 无新性能结论。详见 RQs/RQ3_18/results/population_readout_v1/qualification/report.md、同目录上级logs/2026-10-04_rewrite_cpu_qualification.md，以及新计划 docs/experiment_plans/RQ3_18_Population_Readout_Plan_2026-10-04.md。


## 2026-10-04 — RQ3.18 GPU smoke通过，授权正式启动

用户明确要求GPU smoke修复通过后直接全量，取代先前CPU后停止。仅执行门禁函数变化，原197文件科学资格通过AST/依赖精确兼容保留，activation_v1单独冻结；实际输入/配方/renderer/评分/矩阵不变。GPU smoke18/18通过，246.32秒；含逐份真实输入输出/PNG/账本审查342.96秒。零基础设施错误、超时、截断或无效五候选；解释错误原样保留，不用于调参。自有smoke服务关闭。

正式supervisor PID258591于23:54:09 America/Toronto启动，11臂2420位置、预期2357新请求+63引用，concurrency36、显存0.75；smoke18已消耗，正式硬限2482/总2500。当前启动核验中，后续状态见 RQs/RQ3_18/results/population_readout_v1/logs/2026-10-04_gpu_and_formal_execution.md 和唯一findings。正式结果尚未形成，smoke不是性能结论。

RQ3.18启动核验补充：2026-10-04T23:58:42.057848-04:00确认2357真实请求+63引用队列、16份新原子提交通过审核；账本{'complete': 16, 'started': 36}、无基础设施错误。服务身份及显存0.75已验证，后台继续。启动收据位于formal/launch_verification.json。


## 2026-10-05 — WWW2027投稿冲刺与研究收敛

用户要求带明确目的加速成果。官网核实摘要10月18日、全文10月25日AoE；内部16/23日交付。项目主线仍为保留有效证据、证明同事实强文本上的选择性视觉RCA收益；10月7日18:00 Toronto设方法/论文主张决策截止。RQ3.18继续原2420矩阵和2500预算，本次没有改输入/源/模型配方/阈值，也未新增实验。现有eval480和test360均已暴露，强基线可比性、新意及可用验证事件需前置核验。计划含证据账本、最小验证、倒排日期及8页结构：docs/experiment_plans/CanvasRCA_WWW2027_Submission_Sprint_2026-10-05.md；决定DD-20261005-WWW-SPRINT；详细日志devlog/2026-10-05_www_submission_sprint.md。

## 2026-10-05 — 反直觉发现收敛为三条重点

按用户要求记录 QA–RCA 关联弱与标题带 attention 聚集，并只新增一条幅度明显、已有校正支持的现象：RQ3.7 科学计数法首选翻转12/84与10/84，相同原输入独立重复为1/84与0/84，原六项探索家族 pH=.005859/.009766。原表计数及六项配对检验/Holm独立复算一致，保存来源哈希。QA相关接近零不证明独立，标题密度6.16/2.08倍不证明有害，翻转显著不等于MRR下降。小幅图元/布局差异不扩为新任务；QA驱动表示分配仍待诊断相关性验证。记录 important_docs/CanvasRCA_Counterintuitive_Findings_2026-10-05.md，决定DD-20261005-COUNTERINTUITIVE，日志devlog/2026-10-05_counterintuitive_findings.md。更新两类索引及候选计划限定，历史完整报告保留；本次零新增模型调用，无新attention、代码、渲染或实验启动，不改变RQ3.18。

同日用户要求补入两项显著干预，现记录共五条：CF-04为RQ3.8保留完整文本再加dashboard，已暴露test342宏平均MRR .4110→.3339，病例/组pH=.001115/.000679；CF-05为RQ3.6-A同证据文本接口整包校准，共同97例pooled ΔMRR+.1017，病例/组pH=.002771/.004863。明确图像＋读法与接口整包范围，不称单一像素/标题或attention因果效果；原统计家族、缺失与不可执行分母保留。补充来源快照及索引、计划说明、决定和日志；历史原报告不变，零新增调用。


## 2026-10-05 — 三份重要文档及配套材料正式迁移

按用户“剪切粘贴”要求，研究计划、文献复核、反直觉发现三份主文档统一迁至important_docs；四份配套文件分别迁入important_docs/artifacts下与三文档同名的独立目录。文献来源review_manifest归入文献复核目录。原docs主文件及两个旧_assets目录移除，没有保留复制件或软链接；同步调整入站引用和文档相对链接，历史实验报告与原始结果保留原位。important_docs/README.md提供入口，artifacts/migration_2026-10-05.json仅记录迁移映射和哈希，无原文备份。未运行实验或增加模型调用。

## 2026-10-05 — Attention 存储与 sink 讨论单独归档

按用户要求新增 important_docs/CanvasRCA_Attention_Storage_and_Sink_2026-10-05.md，并更新目录入口。记录在线摘要、FP32二进制、有界明细、共享来源及其信息损失；10,000次尝试预算为持久化793,772,032字节、含临时文件860,880,896字节，属于可复算的设计预算，非实测压缩率。复核旧归档/采集代码、实际模型层类型及ICLR2025 VisAttnSink原文，区分识别、屏蔽与重分配；提出未来四条件诊断验证和成本要求。配套目录保存来源哈希与预算；决定DD-20261005-ATTENTION为provisional。仅文档与来源核查，未修改采集代码、启用attention或调用GPU，不改变任何既有实验。

## 2026-10-05 — Git 忽略规则补齐

用户要求检查大实验产物并提供代码同步命令。既有结果/准备/模型/缓存忽略有效；补充大型逐病例CSV、发布暂存副本和第三方数据/解压输出规则。39个已跟踪文件（46,010,689字节）仅从Git索引移除，磁盘文件逐一哈希不变；未提交、推送或改写历史。剩余Git可见大于1MiB文件仅代码notebook。详情：devlog/2026-10-05_git_artifact_hygiene.md。

## 2026-10-05 — RQ3.18 安全暂停后恢复

睡前暂停已完成排空，自有服务退出；断点1193/2420终态（1179 done含42引用、14原超时），1227 pending，无遗留started。用户上午授权继续，原资格/输入/预算不变，监督PID2517恢复1206新请求＋21引用；新服务与首批新增原子结果核验通过，显存0.75、并发36。无新增smoke或历史批量复验。当前后台运行，详情见RQ3.18唯一findings及formal/resume_verification_20261005.json。

## 2026-10-05 — 双线下一阶段计划，补入新的 QA 干预

- 范围/状态：用户要求review important_docs及RQ1.1/RQ2.1到RQ3.18历史报告后制定下一计划，并明确QA脱节须新做轻量实验。本回合单主agent、仅文档；RQ3.18当前已完成2420终态且自有服务关闭，上方恢复条目保留当时历史。
- 计划：docs/experiment_plans/CanvasRCA_Dual_Track_Next_Stage_2026-10-05.md。主线统一为“遥测表示如何影响诊断决策，并据此提高MRR、降低成本”。四臂强文本/紧凑文本/附加图像/真实视觉替换；新增60例×8调用的QA与正确读数干预，复用同期RCA对照。轻量attention先有界资格，未通过不阻塞主方法与QA。
- 证据与边界：承认RQ3.18 AIOPS正向信号及Aegis损失，保留无降本和原不采用结论。35个本地来源哈希与阅读范围落盘；长表及全部原始回答未重做完整审计。实际图上格式化数值与DOM完整值区分，移交失败不能宣称事实等价。历史压缩、分组、核验及去点实验避免重复；QA弱相关不当独立性证据。
- 预算与停止：3,000次仅资源草案，核心方法/重复/QA共1,480次，smoke另18；条件attention、baseline和扩展验证不得自动启动。已暴露test360不称独立确认。计划索引和DD-20261005-DUAL-TRACK同步；旧计划、报告及源码保持原样。
- 本次结果：新增模型调用0，未写后继实验代码，未运行CPU/GPU/渲染，attention未开启。下一步等待用户对实施的指示；文档链接、预算算式和来源快照做离线核对，不能记为实验资格通过。

## 2026-10-05 — RQ3.20 在 CPU 预算门槛停止

用户授权按预算化视觉取证计划实施；先完成计划落盘、五模块CPU编译/取回接口、静态和接口回归。220例公共来源与实际processor审核完成，文本必要条件给出的最终合格上界A22 0/60、A25 0/60、Aegis 16/100，均不足登记的50%。全部F输入计数与RQ3.19一致，独立12项processor复核一致；573个保护文件未变。修复完整G关系并集、配对points字段及嵌套codec保留，失败日志保留。按用户计划停止候选，不改0.40/0.85预算，不进入图像/GPU/正式/QA/attention，新增模型调用0；下游运行器未作为完成实现交付。这是当前编译与预算的可行性失败，不是新的MRR结果。详细状态：`RQs/RQ3_20/findings/exp_budgeted_acquisition_findings.md`；阶段日志：`RQs/RQ3_20/results/budgeted_acquisition_v1/logs/2026-10-05_cpu_feasibility.md`。

## 2026-10-05 — RQ3.20 v2 压缩修订

用户要求直接修改代码尝试满足原预算。v2命名列、常量共享、字段/窗口引用及有向关系分组保持完整公共事实，文本首轮输入减少29.48%/23.24%/20.45%；220例反解和真实processor整包取回回归通过。文本侧60/60、56/60、100/100可行，计入216张真实统一renderer PNG后共同可行0/60、1/60、0/100；视觉首轮平均43.09%/44.06%/45.67%（仅有图病例），仍超40%。静态5模块791行、三个实际例图/确定性重绘、1028项历史保护通过；全局表头与TSV探查更长未采用。原门槛、字体、图元、像素限额不变，v1结果保留；当前停止在CPU结论，新增LLM调用0，无GPU/QA/attention。报告见RQ3.20唯一findings；日志：`RQs/RQ3_20/results/budgeted_acquisition_v2/logs/2026-10-05_compression_revision.md`。


## 2026-10-05 — RQ3.20 v3 全量启动

用户将首轮门槛从40%调至50%，保留85%总预算。全220例实测资格58/60、52/60、84/100；代码、静态、CPU与16次真实GPU smoke通过。QA别名评分错误在GPU前修复；正式后台PATH错误已修复且未产生正式请求。现由 `canvasrca-rq320-v3.service` 运行1,520流程核心队列，最多2,200调用，GPU0.75/并发36。Attention不满足64KiB约束，保持关闭；SIRCL/独立确认未激活。以 [启动记录](../docs/experiment_reports/RQ3_20_Qualification_and_Launch_2026-10-05.md) 和 [启动凭据](../RQs/RQ3_20/results/budgeted_acquisition_v3/formal/launch_receipt.json) 为准；本次在正式启动核验后停止。


## 2026-10-06 — RQ3.21实现与CPU资格完成，停止

用户确认复用RQ3.16历史锚点，并同意精简为六个新主臂；单阶段完整事实压缩与实体组织已实现，保留60例QA/位置扰动/真实重复。1800新正式位置＋220历史引用，smoke18、恢复预留122，总上限1940；21个普通位置可精确引用，无重试预计1779次新正式生成。当前方法份额73.3%单独记入计划，未写Codex.md。

静态1597功能行通过；220例完整CPU163.21秒通过，最大输入26498，全部容量及逐数据集1.05预算通过。预选方法输入对历史锚点减少16.85%/17.82%/16.35%，对RAW_TEXT减少13.57%/14.32%/13.32%；不是新MRR或input＋output结果。211旧PNG复用、9回退、29248绑定、3个字节一致重绘、7张实际PNG查看、2265原始配对复算通过。220历史输入/提交/评分/原usage核验，28模型/processor文件身份复核；23离线provider测试实际事务和快速恢复，无网络/模型请求。

准备来源manifest、候选引用、AUX/events解析和历史配置哈希比较问题已修复，失败日志保留，最终版本重新完整检查。211依赖冻结归档完成。GPU smoke未运行、正式未启动、attention关闭；未生成执行授权，已按用户要求停止。计划/完整资格报告/唯一findings：docs/experiment_plans/RQ3_21_Compact_Evidence_Entity_Organization_Plan_2026-10-06.md；docs/experiment_reports/RQ3_21_CPU_Qualification_2026-10-06.md；RQs/RQ3_21/findings/exp_compact_entity_findings.md。


## 2026-10-06 — RQ3.21 GPU资格通过，正式启动完成

用户新授权GPU smoke通过后直接启动全量。冻结211依赖契约635f9be2…8754、配置、公共事实、PNG、提示及模型配方均未改变；独立执行凭据绑定本次授权和既有静态/完整CPU/视觉资格。18次真实smoke全部完整提交，无超时、格式无效或未解决基础设施错误；逐请求输入/PNG、输出、独立评分、实际usage和原子提交图核验通过，18份CPU token均与provider相同。含启动修复与人工审核407.99秒，没有重置600秒窗口。

修复两个零调用启动环境问题：共享启动器默认attention开启，显式关闭后重启；systemd缺少nvidia-smi路径，补齐infer/bin及/usr/lib/wsl/lib。失败日志与监督记录保留。两组真实独立重复输入相同且provider request ID不同，即使答案相同也没有复用输出。部分理由误读保留为模型结果，不按smoke排名调参。

正式由canvasrca-rq321-formal.service运行，Qwen本地BF16/context40960、显存0.75、并发36、RCA8192/QA1024、attention关闭。2020逻辑位置包含220历史锚点引用；1800新位置经21个精确引用预计1779新生成，正式上限1922＋smoke18＝1940。13:58:47 UTC核验13次新完成、36在途、0失败；首批6份新提交产物图和usage均通过，队列持续补入。没有重跑历史锚点或启动其他实验。

本次交付终点已满足：启动并核验正式运行，助手停止操作，后台继续冻结队列。完整记录docs/experiment_reports/RQ3_21_Qualification_and_Launch_2026-10-06.md；运行凭据RQs/RQ3_21/results/compact_entity_v1/formal/launch_receipt.json；唯一当前状态RQs/RQ3_21/findings/exp_compact_entity_findings.md。尚无正式MRR或总成本结论。


## 2026-10-06 — RQ3.21误关机后恢复

用户误关机后要求重启。原1295次完整提交、8次终态超时、220历史引用保留；35个在途中断请求仅核对自身持久化记录，标记interrupted并保留调用支出。原冻结源与资格一致，不重跑smoke、不批量重开历史输入/PNG，继续476调用＋21引用队列。

16:40:49 UTC已新增16次提交，总1311 complete、8原超时、35 interrupted旧尝试、35在途；首批5份新提交产物图和实际token核验通过，既有完整结果及终态超时均未重跑。后台canvasrca-rq321-formal.service，显存0.75、并发36、attention关闭。预计含smoke累计1832尝试，低于1940上限。详细恢复日志RQs/RQ3_21/results/compact_entity_v1/logs/2026-10-06_power_loss_resume.md；凭据formal/resume_20261006_power_loss/verified.json。恢复验证完成后助手停止操作，后台继续。




## 2026-10-06 — RQ4.1 真实权重视觉 token 接口验证

用户授权的小例子已完成：三数据集各一张既有 unified-renderer PNG，原生/identity/半量/四分之一量，共12次调用，全部提交，累计111.58秒。identity三例logits与输出均等价；半量875→438个视觉token，本次短输出不变；四分之一219个时一例实体读错。HF隔离路径通过，vLLM正式适配待做，不是MRR或正式smoke。启动缺accelerate在0调用时修复，保留失败材料，预算未重置，共享环境未修改。自有GPU进程已退出，正式实验未启动。详见[RQ内唯一报告](../RQs/RQ4_1/findings/exp_token_interface_probe_findings.md)。


## 2026-10-06 — RQ4.1在CPU角色支持门槛停止

用户最终限制画布宽/高各8192。五模块局部实现、unified renderer新增注册能力与attention有界采集基础已落盘；220张PNG及实际processor上下文通过，静态/RQ单测/renderer浏览器回归通过。但三个数据集60/60、60/60、100/100均有独立回查原始数值的空角色支持：一个token覆盖多个字段，独占最大面积归属使较小字段没有可分配支持。一次一字段的栅格复核确认具体反例；不是MRR/读取性能结果。按登记CPU门槛停止，无新增模型调用，GPU smoke未运行，正式未启动。完整比较器/运行路径仍未交付，旧12次接口探针保留。

[详细RQ日志](../RQs/RQ4_1/results/comparison_coding_v1/logs/implementation_cpu_stop_2026-10-06.md)；[唯一findings](../RQs/RQ4_1/findings/exp_comparison_coding_findings.md)。


## 2026-10-06 — RQ4.1共享token支持修订完成

用户授权取消独占归属。已归档旧失败版本，前瞻登记共享支持、唯一token计费及联合动作并集收益。静态、22项CPU单测、220例非空支持审核通过，另142个边界字段由统一renderer单独栅格确认，诊断PNG不变。所有病例的登记支持均能放入50%预算，可能使依赖对照饱和；真实encoder掩码仍未测。完整CPU/运行实现待完成，GPU smoke及正式未启动，新增模型调用0。不能以局部修复通过替代整体资格。

[本次RQ日志](../RQs/RQ4_1/results/comparison_coding_v1/logs/shared_support_revision_2026-10-06.md)；[唯一findings](../RQs/RQ4_1/findings/exp_comparison_coding_findings.md)。


## 2026-10-06 — RQ4.1饱和实测与证据预算修复

三个固定eval病例真实Qwen视觉特征确认：旧grid50下CVC、REWIRED、UNARY最终mask完全相同。前瞻登记的CVC_E50保留全部锚点并分配一半唯一可选支持，三例恢复136/106/122个差异位置；实际总图保留27.29%–31.06%。静态与25项CPU回归通过，全枚举/增量选择在真实样例一致。仅3次视觉编码前向，新增LLM调用0，自有编码进程已退出；完整CPU及注册smoke/formal仍未通过/未运行。代理仍近于饱和且UNARY略高于CVC，不能据此宣称MRR或总成本收益。

[详细RQ日志](../RQs/RQ4_1/results/comparison_coding_v1/logs/saturation_repair_2026-10-06.md)；[唯一findings](../RQs/RQ4_1/findings/exp_comparison_coding_findings.md)。

## 2026-10-06 — RQ4.1 remaining CPU regression prepared (v6)

User requests launch of the remaining CPU checks, then immediate handoff for
user monitoring. Reuse v5's completed 220-case encoder/covariate and 2,640-mask
qualification. Added source-bound anonymous QA/intervention compilers,
registered quantile-atlas renderer component, bounded passive region maps,
offline native-generation tensor/state and durable single-call lifecycle tests.
Frozen 90-case mechanism roster and 6,100 logical development positions are
CPU manifests only. No model/GPU/smoke/formal activation. Full CPU status remains
pending; actual visual review will follow generated examples. Missing published
saliency/mid-decoder paths are explicitly unqualified, not renamed surrogates.
Existing statistical calibration failure and no-confirmation state are retained.
See `RQs/RQ4_1/descriptions/RQ4_1_Remaining_CPU_2026-10-06.md` and v6 results.

RQ4.1 v6 launch receipt: background PID 374258; `cpu_remaining_v6/runner.log`, `status.json` and `pipeline.status` are authoritative. Launched after source freeze (93 files); user monitoring handoff. No inference activation.

## 2026-10-06 — User stops RQ4.1 v6 CPU work

Confirmed pipeline failed_exit_1 and no surviving owned audit/launcher processes. Preserved failed tests; 220-case dependent audit did not start. Wrote PAUSED_BY_USER.json. No fixes, restart, GPU smoke or formal calls authorized by this stop.


## 2026-10-09 — RQ4.2 GPU smoke stopped at registered deadline

CPU qualified; bounded supervisor integrated and six affected CPU checks pass. Fixed loader optional-dependency and NumPy attention hash failures within the same original smoke clock. 16 committed answers (11 RCA,5QA),17 charged attempts; AegisLab SHAM not run before600s. GPU qualification remains failed/incomplete; no formal launch. Attention16 records/12122bytes, QA3/30. OwnedGPU stopped; no persistent activation. [Detailed report](../docs/experiment_reports/RQ4_2_GPU_Smoke_2026-10-09.md).


## 2026-10-09 — RQ4.2 affected-path GPU qualification passed

User added5×18smoke opportunities; only1round/2calls used(89.03s). Reused16 compatible completions to cover original18identities; original timeout status retained.8affectedCPUchecks pass,55generation definitions unchanged. Cumulative19smokeattempts,18answers;QA6/36 remainsrisk. GPUstopped,formalnotstarted;formalCLIstillclosed. [Report](../docs/experiment_reports/RQ4_2_GPU_Smoke_Supplement_2026-10-09.md).

## 2026-10-09 — RQ4.2 formal runner and power-loss recovery qualified

User requested deployment and qualification, then stop. Formal entry point ready; 18 affected CPU checks passed, including actual SIGKILL/SIGTERM, durable reply recovery, duplicate ownership, cumulative budget and central scorer. 60 previous generation definitions and dependencies unchanged: retain CPU/GPU qualification without new model calls. 1336 positions /1328 unique calls, 142 retry reserve; no activation, no formal run, no owned GPU process. [Report](../docs/experiment_reports/RQ4_2_Formal_Readiness_2026-10-09.md).

## 2026-10-10 — RQ4.2 full experiment launched

Explicit user authorization; frozen readiness valid. Background PID 1982, monitored 193.7s without infrastructure/attention/commit errors. At handoff 5/1336 committed, one in flight; five first-case arms have valid durable results. No code or recipe change, no extra smoke. Stop monitoring and leave worker running as requested. Live status: `bash RQs/RQ4_2/scripts/status.sh`.

## 2026-10-11 — RQ4.3 v7 surviving CPU/GPU qualification

User-authorized layout repair investigated with actual scoped-label and grid-aligned renders. Corrected missed scoped foreground anchors with opt-in V3; finite R prototypes still fail N/K, so registered R dependencies including X_SRP cancelled, not replaced by a new winner. Preserved failures. S_DISTINGUISH/S_REPRESENT removed under predeclared near-duplicate rule. Nine surviving RCA conditions plus QA/order/repeat/timing total 2412 positions, smoke18+infra234 allocation2664 of permitted8000.

Inherited scoped CPU passes preserved. QA label collisions and node-occluded edge locations repaired in unified renderer; 60/60 QA and 15 cold identity checks passed. Static, TypeScript and 22 CPU regressions pass, including crash/recovery and scorer-case handling. Historical compatibility remains not_demonstrated, relevant inferential slots ineligible. Codex hash unchanged.

Bounded GPU smoke: 18/18,481.95seconds,0 infrastructure failures,2 invalid model outputs retained zero. BF16 independent kernel and lambda-zero checks passed; registered 3/1/4 branch paths and real cache lengths verified. Attention one same-seed pair output identical,ratio.9606,797bytes; conservative10k cap730464256bytes. Small timing sample not zero-overhead proof. Offline QA phase-case correction preserves generation code and original results; no new calls. Formal launch authorized by active user goal; monitor180seconds then stop.

RQ4.3 formal queue launched PID 29940; startup monitored 224.0s, 8/2412 commits, no infrastructure failure. Agent launch objective complete; experiment continues in background.

## 2026-10-11 — RQ4.3 v17 扩展与直接可读保留

八个恢复臂 CPU 全部通过、HTML smoke 8/8；4,832 位置队列恢复并完成启动监控。本次部署目标完成，正式实验继续运行。详细资格、豁免、缓存计时与最终密度待核验状态见 `docs/experiment_reports/RQ4_3_Direct_Retention_and_Extension_2026-10-11.md`。


### 2026-10-20 — Nibi-only historical pitfalls consolidation and blocked-chain repair

Created `important_docs/CanvasRCA_Nibi_Pitfalls.md` in the Nibi worktree only, covering historical RQ3.8 and RQ4.5 CPU failures, startup/JIT/module/environment issues, NFS accounting, timeouts, numerical/backend mismatches, dependency stalls, provenance and access/storage pitfalls. Job IDs, evidence, known versus unknown causes, fixes and actual verification states are explicit. CPU pass is retained; GPU smoke/throughput and formal remain unqualified/unstarted. SDPA full-encoder job24589226 failed; pending children24589420/24589619 cancelled after preserving scheduler evidence. New zero-generation FA3 padding probe24686266 pending; a draft reintroducing already unsupported FA2 was cancelled before allocation. Local code/RQ4.7 not read or changed.


### 2026-10-20 — FA3 padding probe disposition

Job24686266 completed with zero new language-generation calls. pad96 is feature-bit-identical on all three fixed actual packets, but the largest image still takes115.77s (original117.44s); the approximately1.44% aggregate single-probe timing difference is not a demonstrated throughput fix. pad128 is slower and fails the unchanged full-feature gate. Production adoption and a fresh 18-call smoke were therefore not initiated. Existing complete CPU qualifications and all42 spent attempts remain. GPU/throughput still unqualified; formal not started. Full evidence, historical issues and disposition are in `important_docs/CanvasRCA_Nibi_Pitfalls.md` and `qualification/visual_fastpath_disposition_24686266.json`. Nibi-only work; local RQ4.7 untouched.


## 2026-10-21 — Nibi operational throughput target and persistent qualification

Remote repository only. User lowers the goal to >=6 actual calls/minute. Round8:24760027 completed18/18, artifacts/answers reviewed, online3.9581/min; KV capacity79,725tokens limited actual batching to2-5. Registered operational0.90 GPU allocation profile, preserved all60 prior attempts and original failed numerical-equivalence records. Static passed; CPU facts/geometry qualifications reused with exact request-preservation proof. Round9 GPU24763295 and CPU review24763332 pending resources. Persistent180-second controller PID261939 verifies all outputs/attention plus measured throughput before submitting CPU input deployment and at most one2-hour GPU job. No full job submitted at this checkpoint. Local repository/running experiment not read or modified.

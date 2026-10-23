> Nibi integration checkpoint — 2026-10-22: this worktree combines upstream
> `67396dff` with Nibi deployment snapshot `21a385a2`. Local completed results
> and Nibi deployment checkpoints below refer to different environments.
> The running job 24832363 continues in `/home/lglsj/CanvasRCA_20261018`.
> This merged worktree has not been activated or qualified for new inference;
> old fingerprints and passed receipts remain historical evidence only.


## Nibi deployment record (preserved history)

## Current Nibi state — 2026-10-22, replacement job 24832363

The user explicitly waived new smoke and requested direct formal recovery.
One two-hour/single-H100 job 24832363 was submitted and released; it was pending
at submission. It resumes the existing queue with 262 completed positions
preserved and 1,298 pending, including eight reviewed infrastructure retries.
The 12 dispatch and 14 recovery checks passed. New GPU qualification is waived,
not claimed passed. Runtime source f7b6392635446bc424cbd7b572bb2bbda7f477d2c457e8371c3a0e12ccf8cfca.
No automatic continuation job is registered. See OPS-21 in the Nibi pitfalls.
All following status entries are historical snapshots.

## Current Nibi status — 2026-10-22, single2h job submitted


## Current Nibi state — 2026-10-22

Platform validation job24806735 failed after1h09m21s with262/1560 formal
positions committed and eight in-flight infrastructure failures. The adapter's
FULL-graph dispatch guard missed the one-token-prefill boundary. Remote-only
repair and12 targeted CPU checks passed; original outcomes and old qualifications
remain intact. New native GPU qualification has not run; no replacement job was
submitted under the already consumed one-job authorization. Inference utilization
was97.6655%, with4.17975 completed calls/min excluding startup. See
important_docs/CanvasRCA_Nibi_Pitfalls.md OPS-20 and the failure_analysis.json
under qualification/graph_dispatch_repair_24806735/. Earlier statuses below
are historical.

User explicitly withdrew the old six-calls/min threshold and accepted smoke13's measured throughput. Observations remain unchanged:18/18 actual calls,4.47955calls/min, inference-period mean GPU utilization95.3307%, zero infrastructure/attention errors and six verified attention summaries. Full operational artifact review is passed; old scientific feature-equivalence and QA limitations are preserved.

Exactly one Slurm job24806735 submitted: single H100,02:00:00 limit,12 allocation CPU cores/eight preparation workers, GPU concurrency eight, BF16 and the qualified native adapter. No separate CPU Slurm allocation, dependency chain, requeue or automatic continuation is submitted. All220 cases were already CPU-prepared; only retention/linking of those immutable inputs runs at allocation entry before model loading. This is a two-hour platform validation of the full registered queue, not a promise that all1560 positions finish in two hours.

The acceptance is explicitly bound to source5f374162e3cab486b6afa82c4c223d25a7e25c21fc03d7264c32fe2124a1e743 and smoke13; the measured numeric rate has not been changed or relabeled as six/min. Single-submission intent and receipt guard against duplicate allocation after SSH interruption. Local code and experiments untouched.

## Current Nibi status — 2026-10-22, UUID repair / smoke13

Smoke12 job24789955 failed during new NVML monitor initialization, after model compilation/warmup but before any diagnostic calls (0 calls in round12). PyTorch _CUuuid omits GPU- and NVML includes it; actual H100 probe24801112 completed successfully in20s and confirms equal canonical device identity. The monitor now compares canonical UUIDs, retains raw identity metadata, and verifies before loading weights.

Static Python/TypeScript and twelve affected UUID/telemetry checks passed in CPU job24802464; all175 protected source files remain unchanged. All1518 prepared request payloads are unchanged except the prospectively registered runtime provenance identity. Population CPU qualification retained without rerun. A duplicate __getattr__ fingerprint-key collision was repaired by recording worker_factory separately. Failed CPU adoption guards/jobs and their resolutions are documented in important_docs/CanvasRCA_Nibi_Pitfalls.md.

Current source fingerprint: 5f374162e3cab486b6afa82c4c223d25a7e25c21fc03d7264c32fe2124a1e743. Round13 smoke job24802797 and afterany artifact review job24802800 have been submitted, initially pending GPU resources. Maximum18 model calls and900s, one H100,12 allocated CPU cores/eight preparation workers, GPU concurrency eight. Historical114 attempts and failed-round clocks/artifacts are unchanged; cumulative call supplement1916 does not reset any counter.

The persistent controller polls180s and requires actual18-call integrity, attention, native compilation/gather, device-specific GPU telemetry and >=6 actual completed calls/min before exactly one2h operational validation allocation. No unqualified formal submission or automatic extra smoke. Inference utilization excludes loading/compilation/pre-first-request preparation/final drain; throughput keeps original first-reservation-through-provider-drain interval. Scientific feature-equivalence remains failed and is not relabeled. Local repository/experiments untouched.

## Current Nibi status — 2026-10-22, capture partition v3 / smoke12

Static AST/TypeScript checks and twelve affected CPU synthetic tests passed (CPU job24789642). Existing 220-case qualification retained by explicit lineage; all1518 payloads are unchanged apart from registered runtime generation identity. New fingerprint: 4f528e6cca56a0e573583e43747156c6381d24fc2b4918e46f127cedab994580.

Round12 GPU smoke submitted as job24789955 (18 calls maximum, 900 seconds, one H100, 12 CPU allocation cores, eight CPU preparation workers, GPU concurrency eight). Offline artifact/speed/utilization review job24789958 depends afterany on that job. At submission it is pending Slurm resources; no new-model completion or speed claim yet. Previous114 spent attempts remain unchanged; cumulative supplement limit1898 is not a counter reset.

Optimization: isolate the exact native layer3 attention arithmetic and passive queries into an explicitly eager compilation split installed before warmup, retaining native compilation on other layers and full decode graphs once collection completes. This remains GPU-unqualified until the new smoke actually executes.

Telemetry: one-second NVML samples by allocated GPU UUID, retained as smoke/gpu_utilization.csv plus metadata. Inference utilization report excludes startup/compilation/pre-request preparation/final drain; throughput preserves the previous first-reservation-through-provider-drain endpoint and must reach six actual completed calls/min. If all checks and speed pass, the persistent controller may submit exactly one two-hour operational validation job under existing authority. No automatic additional smokes.

Scientific feature-equivalence failure remains historical and failed; this is operational Nibi integration, not an equivalent scientific rerun. Local code and experiments untouched.

## 2026-10-22 latest measured result: round11 functional pass,4.4558/min below six

CPU check24787209, GPU smoke24787282 and offline review24787283 completed0:0.
All18 actual answers were read; six attention files were verified. Native chunked
prefill and compiled branches were exercised; no infrastructure/attention error
or preemption occurred. Online242.3792seconds yields4.4558calls/min; startup
289.3977seconds, allocation531.7769seconds. The speed target remains unmet and
no two-hour platform job is submitted. The prior4.3518/min result is preserved;
this small difference is not asserted as a stable or causal speedup.

Evidence: qualification/runtime_throughput.json,
qualification/smoke11_manual_artifact_review_20261022.json and
qualification/operational_runtime_round11_analysis.json under the Nibi result
root. See Nibi pitfalls PERF-13/14. Local experiments and source are untouched.

## 2026-10-22 active operational successor: chunked prefill and native compilation

CPU check24787209 passed: static/TypeScript checks and seven targeted attention
chunk-state cases. Unchanged220-case input qualification is carried by exact
1518-request payload lineage; no full CPU rerun. Source fingerprint
1dc6b0330250875232b3b847b1379781ba53f547ce2d89be3a0477c84198bb81.
GPU smoke24787282 (round11;18calls/900seconds;oneH100,12CPUs,128GiB) and offline
review24787283 are submitted. CPU preparation remains eight workers, with four
additional cores reserved for runtime/control. Native compilation mode3 and
8192-token chunked prefill are enabled; capture-bearing steps explicitly bypass
compilation while preserving complete prompt K and the two registered queries.
Actual runtime functionality, attention and>=6calls/min are pending measurement.
The background controller gates exactly one two-hour platform allocation on a
complete reviewed pass. Local code and experiments remain unchanged.

## 2026-10-22 current checkpoint: reviewed graph smoke passes functionality, speed gate fails

Round10 GPU24770165 and artifact review24770166 completed0:0. All18 actual
answers and6 attention files have now been reviewed. Native decode graph replay
was measured (541 batches), passive captures used nine eager batches, and no
preemption or attention error occurred. Online248.1714seconds gives4.3518calls/min,
below the current six/minute target. Startup224.1168seconds is already excluded
from that rate. No two-hour formal/platform job has been submitted.

The documentation-guided Nibi review identifies an unsupported chunked-prefill
disablement, disabled compilation, incomplete warmup, and a mislabeled empty
first-prefill profile. Cause isolation and a compatible consolidated adapter
repair are planned; none was implemented in this read-only code review. See
[Nibi pitfalls PERF-11, CPU-08 and PERF-12](../../../important_docs/CanvasRCA_Nibi_Pitfalls.md).
Functional/manual artifact pass does not waive throughput or the preserved
failed scientific feature-equivalence gate. Local code/experiments are untouched.

## 2026-10-22 operational checkpoint: functional pass, throughput still blocked

Round9 GPU24763295 and CPU review24763332 completed0:0.18/18 new calls, all actual raw answers reviewed,6attention files verified; functional/artifact checks pass. Throughput4.2446calls/min (254.4418seconds online;487.0156seconds startup) fails the latest>=6 target. KV capacity201,142tokens, actual decode batching8, no preemption. First-use JIT remains observable but its isolated contribution has not been established. Persistent controller stopped safely. No two-hour full-queue allocation has been submitted; no new calls or local edits were made during this status inspection.

## 2026-10-21 current operational validation — target six calls/minute

Round 8 GPU job 24760027 completed 18/18 actual calls; all outputs were reviewed, with no artifact/runtime failure, but online throughput 3.9581/min remained below target. Latest user target is >=6 actual completed calls/minute. Round 9 job 24763295 prospectively tests operational KV allocation 0.90 (previous 0.80), with BF16, inputs, token selection, weights, output limits and passive attention unchanged. Static checks passed; existing full CPU input qualifications are carried by exact lineage rather than rerun. Offline review job 24763332 follows afterany and fails closed. Source fingerprint: 71fa61cf1c87f4cb187f131fec055f84aed7e1b335e6a6e47d43b716b10d8fb6.

Both jobs are currently pending cluster resources. A persistent remote controller checks every180 seconds. It permits CPU deployment and exactly one two-hour GPU validation allocation only after18 new calls, full artifact integrity/attention checks and measured plus amortized throughput >=6. Software or throughput failure stops the controller without new model calls or formal submission. This validation is explicitly operational, not scientific reproduction: the earlier strict full-feature equivalence failure remains unchanged.

# RQ4.5 — unique findings and qualification state

## 2026-10-21 current Nibi platform-validation status

The current user scope is operational validation: repaired/reviewed smoke, then
exactly one two-hour full-queue job, no requeue/chain and timeout acceptable.
These results are excluded from scientific comparisons. Native BF16 TORCH_SDPA
is now prospectively registered; its old full-feature reproduction gate remains
failed and preserved. Prior1,518 CPU-qualified request payloads/pixels are
unchanged; new backend recipe identities prevent old-answer reuse. No full CPU
regression or source-data preparation was repeated. Static checks pass at
fce064569f192b570aeb785a8e5969fdf9f16eaad3f47b2cdd5774f17220094e.

New18-call smoke24760027 and dependent offline review24760032 are submitted.
The smoke is PENDING/PartitionDown: all Slurm CPU/GPU partitions are DOWN and
nodes show administrator Auto Reboot ASAP. No new model calls have begun.
A remote lightweight monitor checks every180seconds and preserves scheduler
observations. Full-queue GPU submission remains gated on clean actual artifacts,
manual answer/measurement review and measured>=7actualcalls/minute. The two-hour
job has not been submitted; the old six-block helper will not be used.

This status supersedes older chronological notes below, without changing their
recorded failures. All changes are on Nibi only; local experiments are untouched.



## 2026-10-20 authoritative Nibi continuation status

The old native-SDPA qualification chain did not pass: full encoder job24589226 failed all three unchanged numerical gates. Pending children24589420/24589619 were preserved and cancelled, not bypassed. Job24686266 is a zero-generation FA3 alignment probe, not a new inference smoke; production code/recipe remains unchanged while it runs. The complete CPU qualification is retained and must be reused by explicit lineage. No formal calls have run. Latest user authorization permits formal Nibi RQ4.5 only after clean source-matched GPU/artifact and >=7 actual calls/minute qualification; see `nibi_resumption_authority_20261020.json`. This supersedes older stop-after-qualification instructions prospectively.

All known CPU/smoke/environment failures and fixes are consolidated in [Nibi pitfalls](../../../important_docs/CanvasRCA_Nibi_Pitfalls.md). This document is on Nibi only; local RQ4.7 and local code are untouched. Guarded adoption/review scripts are staged, not evidence of a GPU pass.

**Current status: CPU qualification remains passed/frozen. GPU round 1 failed in Slurm step setup; round 2 timed out in first-time dependency initialization with zero initiated model calls. CPU-only FlashInfer compilation passed. Round 3 was cancelled before allocation to publish its hash-identical binary through the native precompiled-cache interface; round 4 reached the registered engine and real requests but was stopped for a network-filesystem accounting lock stall. Targeted CPU ledger qualification passed; round 5 was stopped by the old timeout with 5/18 committed; the user now authorizes the full 15-minute window for subsequent rounds. Formal submission remains conditional on a clean pass.**

The active user goal supersedes the five-round allowance: serial smoke rounds are now unlimited, each bounded by 18 initiated calls and 15 minutes (900 seconds); exactly one round may be live. After a clean, fully reviewed pass, submit the 1560-position formal experiment as at most six serial two-hour blocks (12 reserved GPU hours total), then stop. This is explicit formal authorization, conditional on clean smoke. No model recipe, arms, inputs or scientific gates change. See `smoke_goal_authority_20261019.json`.

Round 1, job 24548141: FAILED/1:0 after five seconds, incompatible `srun` binary/auth plugin versions (25.11.8/25.11.9); Python/model never started. Remove the nested job-step invocation and execute within the allocated batch cgroup. Round 2, job 24549086 on g4: original 600-second clock expired during software/kernel startup, completed 0/18, ledger empty. Preserve its clock/summary/logs; do not qualify a run without real requests. Actual backend logs identify BF16 vLLM 0.24.0, FlashAttention 3 and unchanged 40960 context/VRAM 0.8. Native weights load in about 37 seconds; slow shared-file imports and first FlashInfer GDN compilation dominated startup. Process traces show unbounded Ninja compilation and home-directory cache output. CPU-only dependency build job 24549904 follows the stopped GPU allocation, compiles its exact existing build graph with eight jobs and moves only this FlashInfer version cache to project cache with a path-preserving symlink. It requests no GPU, reads no case/model weights and reruns no passed CPU regression. Future launchers bound compiler jobs to eight. Build 24549904 failed before compilation because the guard compared `/project/6006115` with its `/project/def-jacobsen` alias; canonicalize both operands. Replacement CPU-only build **24550313** runs the same generated Ninja graph. The existing pending smoke round 3, job **24549987**, now depends on `afterok:24550313`; no second GPU smoke is queued. This does not reset or spend model calls.

Read-only historical comparison found that the RQ3.8 `inference.triton_v2.yaml` explicitly selected the Triton GDN prefill backend, whereas the current frozen runtime automatically selects FlashInfer. This establishes a configuration difference, not by itself a successful historical execution. A preserved log was then read from the small archived logs bundle: job **21217562**, COMPLETED after **14,273 seconds**, used vLLM 0.24.0, BF16 Qwen3.5-9B, FlashAttention 3 and automatic FlashInfer GDN, with project runtime caches. Engine initialization at 04:56:08 and HTTP startup completion by 04:58:48 confirm a successful long GPU run. Its smaller model, MIG allocation, graph/chunked-prefill settings and absent RQ4.5 adapter make it an initialization/cache reference only, not a drop-in scientific/runtime recipe. Keep the current RQ4.5 custom worker, per-image post-merger gather, original MRoPE, KV admission, structured ranking and passive attention; do not substitute a historical plain HTTP launcher.

Original five-round GPU authorization (superseded by the active goal above): the user permitted at most five rounds, 18 calls each; its obsolete time clause is removed. The unchanged frozen queue and original bounded runtime/global ledger remain protected. The Nibi launcher requests one full H100, eight physical CPU cores and 96 GiB RAM. Smoke accuracy is not a qualification criterion. The historical authority remains in `smoke_authority_20261019.json`; the current scope is in `smoke_goal_authority_20261019.json`.

This file records implementation/qualification, not RCA performance. The user authorizes continued CPU repair until all checks pass. The original static-only delivery boundary is historical. Codex.md and historical experiment sources remain unchanged.


## Local experiment record (preserved history)

# RQ4.5 — unique findings and qualification state

## Current status — full local results and analysis complete, 2026-10-19

**1560/1560 logical positions complete; 1538 actual formal calls plus 22 references.**
Local smoke adds 18 calls. No infrastructure-unknown results or output-limit
truncations; GPU service has exited. Formal throughput is 10.3316 actual calls
per minute over 8931.832 seconds. Runtime final retention passed at 3.18839 GB,
with 9.2784 MB attention accounting including mapping dependencies.

Standard / tolerant MRR: H_MARGINAL 0.4912 / 0.4912; H_TOPOLOGY
0.4592 / 0.4592; H_TOPO_MARGINAL 0.4736 / 0.4736; V_DOMAIN_FULL
0.3302 / 0.3499; V_SOURCE_UNIFORM 0.3105 / 0.3348; V_CONTEXT_FILL
0.3208 / 0.3325. H_MARGINAL costs 5.97% fewer total tokens than historical
T_FULL, with AegisLab gains but AIOPS regressions. All four registered primary contrasts have Holm-adjusted p-values above .05
in both event-group and case analyses.
Neither nominee meets the advancement goals; no post-hoc winner adoption.

All 180 QA outputs received structured field analysis; 54 complete QA/RCA
pairs from nine disclosed cases were individually read. Unit-alias sensitivity
is explicitly post-hoc and does not replace registered scores. Relationship
QA is much weaker with the current image-carried topology. A stale generic
reading sentence remains in the hybrid prompt; this is a minor unmeasured
instruction limitation, not a change in actual modality ownership. Topology
is carried by images in H_TOPOLOGY/H_TOPO_MARGINAL; no textual topology copy
is inferred from that stale sentence. This follows the user's clarification.

412 actual formal attention records cover only layer 3's last prompt and
first decode queries. No final-decision attention claim. Report and
reproducible, read-only analysis:
[final detailed report](../../../docs/experiment_reports/RQ4_5_Qwen_Analysis_2026-10-19.md).
Historical checkpoints below remain intact; no new model call or runtime-code
change was made for this report.


## Historical qualification and execution checkpoints (superseded by the complete-results status above)

**Historical status: CPU qualification remains passed/frozen. GPU round 1 failed in Slurm step setup; round 2 timed out in first-time dependency initialization with zero initiated model calls. CPU-only FlashInfer compilation passed. Round 3 was cancelled before allocation to publish its hash-identical binary through the native precompiled-cache interface; round 4 reached the registered engine and real requests but was stopped for a network-filesystem accounting lock stall. Targeted CPU ledger qualification passed; round 5 was stopped by the old timeout with 5/18 committed; the user now authorizes the full 15-minute window for subsequent rounds. Formal submission remains conditional on a clean pass.**

The active user goal supersedes the five-round allowance: serial smoke rounds are now unlimited, each bounded by 18 initiated calls and 15 minutes (900 seconds); exactly one round may be live. After a clean, fully reviewed pass, submit the 1560-position formal experiment as at most six serial two-hour blocks (12 reserved GPU hours total), then stop. This is explicit formal authorization, conditional on clean smoke. No model recipe, arms, inputs or scientific gates change. See `smoke_goal_authority_20261019.json`.

Round 1, job 24548141: FAILED/1:0 after five seconds, incompatible `srun` binary/auth plugin versions (25.11.8/25.11.9); Python/model never started. Remove the nested job-step invocation and execute within the allocated batch cgroup. Round 2, job 24549086 on g4: original 600-second clock expired during software/kernel startup, completed 0/18, ledger empty. Preserve its clock/summary/logs; do not qualify a run without real requests. Actual backend logs identify BF16 vLLM 0.24.0, FlashAttention 3 and unchanged 40960 context/VRAM 0.8. Native weights load in about 37 seconds; slow shared-file imports and first FlashInfer GDN compilation dominated startup. Process traces show unbounded Ninja compilation and home-directory cache output. CPU-only dependency build job 24549904 follows the stopped GPU allocation, compiles its exact existing build graph with eight jobs and moves only this FlashInfer version cache to project cache with a path-preserving symlink. It requests no GPU, reads no case/model weights and reruns no passed CPU regression. Future launchers bound compiler jobs to eight. Build 24549904 failed before compilation because the guard compared `/project/6006115` with its `/project/def-jacobsen` alias; canonicalize both operands. Replacement CPU-only build **24550313** runs the same generated Ninja graph. The existing pending smoke round 3, job **24549987**, now depends on `afterok:24550313`; no second GPU smoke is queued. This does not reset or spend model calls.

Read-only historical comparison found that the RQ3.8 `inference.triton_v2.yaml` explicitly selected the Triton GDN prefill backend, whereas the current frozen runtime automatically selects FlashInfer. This establishes a configuration difference, not by itself a successful historical execution. A preserved log was then read from the small archived logs bundle: job **21217562**, COMPLETED after **14,273 seconds**, used vLLM 0.24.0, BF16 Qwen3.5-9B, FlashAttention 3 and automatic FlashInfer GDN, with project runtime caches. Engine initialization at 04:56:08 and HTTP startup completion by 04:58:48 confirm a successful long GPU run. Its smaller model, MIG allocation, graph/chunked-prefill settings and absent RQ4.5 adapter make it an initialization/cache reference only, not a drop-in scientific/runtime recipe. Keep the current RQ4.5 custom worker, per-image post-merger gather, original MRoPE, KV admission, structured ranking and passive attention; do not substitute a historical plain HTTP launcher.

Original five-round GPU authorization (superseded by the active goal above): the user permitted at most five rounds, 18 calls each; its obsolete time clause is removed. The unchanged frozen queue and original bounded runtime/global ledger remain protected. The Nibi launcher requests one full H100, eight physical CPU cores and 96 GiB RAM. Smoke accuracy is not a qualification criterion. The historical authority remains in `smoke_authority_20261019.json`; the current scope is in `smoke_goal_authority_20261019.json`.

This file records implementation/qualification, not RCA performance. The user authorizes continued CPU repair until all checks pass. The original static-only delivery boundary is historical. Codex.md and historical experiment sources remain unchanged.

## Implemented scope

Six registered arms: H_MARGINAL, H_TOPOLOGY, H_TOPO_MARGINAL, V_DOMAIN_FULL, V_SOURCE_UNIFORM and V_CONTEXT_FILL. Historical T_FULL, MARGINAL_FIVE and U answers/costs are reused; no baseline reruns. The formal matrix remains 1560 logical positions with a 1700-attempt ceiling including the future 18-call smoke and recovery reserve.

Source ownership, exact diagnostic-number handling, preserved residual records, original-image source-local pruning and same-count context controls are implemented. All graphics use the unified renderer; only the new opt-in C39 complete marginal component is added. Existing component behavior is protected. Runtime supports one-call diagnosis, central scoring, exact references, genuine fresh-call repeats, atomic commits, pause/recovery and bounded RAM preparation.

The user removes strict cross-arm fact equality. Record evidence differences and interpret changed evidence as a whole-method contrast; within-arm cross-modal nonduplication and private-label isolation remain. The current CPU repair does not remove diagnostic records.

## Actual CPU history

| Cycle | Observed outcome |
|---|---|
| v1 | 20 unit tests and the original three-case preflight passed. Population: 93/220 passed; 122 original-image-budget failures, four no-transfer-target cases and one operation-bound endpoint parsing error. Dependent jobs cancelled. |
| v2 | 22 unit tests, six-case boundary preflight and all 220 population cases passed. All 1320 actual RCA processor inputs met image/context/legibility gates. The independent full input-cost check failed only H_TOPOLOGY/AegisLab: T_FULL ratio 1.0130625. Other hybrid/dataset means were below both references. QA/runtime continuation cancelled for repair. |
| v3 | Unit25, preflight6, population220, budget, QA-input33, runtime30 and actual repaint passed. Stop before completion to repair passive multi-image header attribution; preserve its evidence. |
| v4 | **24546402 COMPLETED / exit 0:0**. Unit27, runtime30 and actual old/new four-image packet comparison passed; unaffected evidence revalidated with provenance. All CPU credentials/queues/source/model provenance frozen and verified. No GPU requested. |

v1 reports/cases are retained in `qualification/history_v1/`; v2 reports/cases and hard-linked request snapshots are in `qualification/history_v2/` under `/project/def-jacobsen/canvasrca_cache/RQ4_5/cpu_v1/`. Existing logs and failed renders are preserved. The immutable source transfer (3302 files, 1,437,905,855 bytes) was hash-verified and that unchanged-manifest proof is reused.

## Repairs and protocol amendments

- Correct parallel-phase row height and remove redundant per-sample axes in the new C39 component; retain original sample labels/statistics.
- Parse operation-bound endpoints, preserving operations, direction and support counts.
- Explicitly register four genuinely data-empty hybrid transfer cases; all three hybrid conditions share complete residual text with zero images. This is not a rendering/capacity fallback. Pure visual still requires its original PNG. Report this applicability limit separately.
- Consolidate the five shared non-diagnostic task/reading/output sections in `hybrid_instructions_v2.json`. All 220 sources have the same original rule-block hash. Preserve unique source-reading/SIRCL/output rules; reject mixed or unreviewed instruction sections. Diagnostic text records/order/numerical spellings and images are unchanged. The tokenizer precheck saves about 520 tokens; actual full-request processor costs must pass. Rewording can affect behavior, so historical contrasts include this explicit interface revision.
- Interleave registered source groups for all CPU phases, including QA preparation; keep eight independent physical cores. This does not alter cohorts, QA targets or formal model-call ordering.

## Verification and remaining boundary

Static Python/TypeScript/config/import/source-protection checks pass: **2032 functional nonblank/noncomment lines**, **175 protected files**. Local deployment fingerprint `c292ee33475e0dbedda4e518812b223c23a319d4baa461c5895d6adb6f4dbc49`; Nibi fingerprint `64676ea19b7d0f6d98c6d39e6bc3eeb33b70a3514f9798fe134295c87eb74879` differs because deployment paths are explicitly bound.

The primary agent actually inspected **16 PNGs** covering the three fixed dataset examples, all their hybrid image sets, unchanged pure-visual PNGs, long operations, extreme durations and operation support. Nibi hashes match the inspected bytes. Dense node-link crossings and inherited smaller U fonts are recorded limitations; visual inspection does not establish model accuracy. The deterministic repaint is a separate CPU check.

Complete CPU qualification now has passed source-matched unit, population, cost, QA-input, runtime, transport-invariance, repaint and visual-review reports plus a verified frozen request/source/model manifest. GPU scopes remain closed. Actual output cost, ranking, attention collection, GPU compatibility and final retention density remain unmeasured until their authorized stages.

[Plan](../../../docs/experiment_plans/RQ4_5_Exclusive_Modality_Spatial_Pruning_Plan_2026-10-18.md) · [Protocol decisions](../descriptions/RQ4_5_experiments.md) · [Static receipt](static_check.json) · [Nibi submission](nibi_cpu_submission.json)

## Final CPU completion — 2026-10-19

[Detailed CPU qualification report](../../../docs/experiment_reports/RQ4_5_CPU_Qualification_2026-10-19.md) · [Machine receipt](nibi_cpu_qualification.json). All 1518 input payloads are preserved across the passive-mapping revision; only unexecuted recipe identity metadata changes. Frozen source/config files match locally and on Nibi (139/139). Actual checkpoint/processor SHA verification covers 27 files / 55,582,674,402 bytes. No MRR or actual output-cost result exists for this experiment yet. Next action requires separate GPU authorization.

## Dependency-cache publication — 2026-10-19

Build 24550313 COMPLETED / 0:0 in 775 seconds, CPU only. Inspection showed that FlashInfer resolves generated Ninja paths, so a relocated cache could otherwise rebuild. Publish the exact resulting `gdn_prefill_sm90.so` via the installed library's supported `flashinfer_jit_cache.get_jit_cache_dir()` interface. Native and published SHA-256: `8be70538b629d46a1745332113b616732ac9feb33f3cad79d05675ad29b25a8a`. The cache provider is an explicit local index, not an installed-package patch or different kernel; native interface compatibility was checked without Torch, GPU or model calls. Model weights, BF16, CPU-qualified requests, RQ4.5 worker/gather/MRoPE/attention and generation configuration stay unchanged. Both formal and smoke launchers select this same provider. Round 3 job 24549987 was cancelled while held, with elapsed time 0 and no calls/clock. Round 4 uses its own newly registered clock; prior evidence remains.

## Round 4 accounting failure and forward repair

Job 24552318 used the original adapter, loaded all BF16 weights (51.1 GiB), initialized/profiled the engine in 18.73 seconds and started real requests. The large FlashInfer compile did not recur. Then progress stayed unchanged for about 150 seconds; the parent was in uninterruptible NFS `rpc_wait_bit_killable`, first in `fcntl(F_SETLK)` (syscall 72), then `close` (syscall 3), while concurrent accounting connections were opening/closing. No completed answer had committed. Cancel the allocation: CANCELLED, elapsed 419 seconds, batch killed after drain wait. Preserve its original clock, requests, collected files and every reserved/spent ledger row.

Forward repair is isolated to RuntimeSession accounting: one process-wide owner, one persistent SQLite connection, an in-process RLock, durable DELETE/FULL journaling and SQLite `nolock=1` under the exclusive owner. This removes redundant NFS byte-range locks without delaying reservation commits or using RAM/disk request buffers. Each future smoke round has an independent 18-call scope; global accounting still preserves prior rows and the explicit user goal governs the reviewed budget supplement. Local eight-thread, duplicate-owner and power-loss/reference/repeat tests passed (three targeted tests). Nibi CPU validation will run all unit cases plus 36 real project-mount simulated ledger transactions; unchanged processor/image/fact qualifications are carried forward only after AST, recipe and exact frozen-queue invariance checks. No GPU starts before that qualification passes.

## Targeted Nibi ledger qualification

CPU-only job **24553260 COMPLETED / 0:0**, 46 seconds. All **29 unit tests** passed; eight concurrent project-mount producers completed **36 durable ledger transactions in 1.3037 seconds**. All prior spent rows were retained, unresolved started rows were classified interrupted only after the owner was terminal, and the old WAL/database/shm bytes were preserved. The single durable ledger keeps global attempt IDs and counters; round 5 uses its independent 18-call scope. A reviewed user-goal supplement registers 5×18 smoke places plus the unchanged 1560 formal / 122 recovery positions (1772 total maximum; no counter reset). Exact frozen queues and generation recipe match the prior CPU-qualified bytes; compiler, renderer, tokenizer/gather/MRoPE, model worker, prompts, scores and all remaining production AST are unchanged. Revalidated 1518 input qualifications are explicitly marked reused; affected ledger tests actually reran. No new model calls occurred in CPU qualification. An additional local real-process-kill/hot-journal check preserved the committed record and rolled back the uncommitted transaction.

## Explicit smoke time revision — 2026-10-19

The user removes the shorter timeout from local and Nibi rules and runtime. Codex.md/AGENTS.md, the smoke skill, shared supervisor, RQ4.5 protocol, runtime clock, qualification and launcher are aligned to the full 15-minute window. Existing completed/failed attempt records and immutable source snapshots are not rewritten. Round 5 committed five answers before its original deadline; eight additional started attempts remained unresolved when Slurm terminated the worker. No timeout-only passage and no formal activation are claimed. A separate round 6 is allowed after targeted time-control regression and unchanged-input/recipe checks; every spent call is retained.

### User-directed continuation

CPU timing-validation job 24554294 was cancelled before execution. Additional Nibi CPU regression is explicitly waived, with previously passed science/input qualification carried forward. The next GPU allocation continues only the 13 unfinished smoke positions; all five existing answers, their original attention/usage/scoring and every spent call remain. The new window is 900 seconds. Review reports must separate the old and continuation clocks and actual call counts. A clean complete 18-position artifact review is still required before formal submission.

## Latest stopping state and throughput target

Job 24554682 TIMEOUT. Eight of eighteen positions are committed, including five retained answers and three new ones. Round 6 initiated eleven calls: three complete and eight timeout failures; two planned positions were never initiated. The new three responses reproduce their stored scores, match frozen inputs and retained PNGs, and have no detected commit/token/attention integrity error. This does not qualify the ten missing positions.

The user closes further smoke and sets Nibi formal inference target to **>=7 completed calls/minute**. Current measured continuation throughput is 0.200 including startup / 0.272 after the first request; the batch is small and timeout-censored. Formal execution is not submitted. Host export is moved ahead of GPU submission; no runtime source/model input changes are deployed from the bottleneck assessment. The next decision requires resolving GPU vision/transport, worker scheduling and environment differences rather than repeating heavy telemetry CPU preparation, which is already complete. No further model calls are authorized by this note.

## Current forward authority and native-backend qualification chain

The subsequent user goal reopens unlimited serial smoke rounds, max18 calls
and 900 seconds each, until measured online/formal-amortized throughput reaches
at least seven completed calls/minute. Stop after qualification, without formal
submission. This supersedes the preceding closure prospectively; failed calls,
clocks and answers remain preserved. See DD-RQ45-13/14 and
`smoke_goal_authority_20261019.json`.

Native kernel job 24586861 passes all three BF16 tensor comparisons; the large
FA3 operation takes 4.319 seconds versus 0.0794 seconds for Torch Flash SDPA.
This explains the observed approximately 117-second / 27-block vision path but
does not qualify end-to-end speed. Imports (24587191) and all nine targeted
old/new processor packets (24585721) pass, with actual import paths and the two
dependency-metadata warnings disclosed. Bulk runtime copying caused zero-call
job 24586948 to time out; the common loader now activates the verified shared
environment directly. Scientific inputs, renderer, weights, dtype, token
selection, MRoPE and scoring remain unchanged.

The user resumes the next step. Queued chain: **24589226** full native-encoder
comparison → **24589420** source-bound forward freeze plus static checks →
**24589619** registration/submission of an unprofiled, max18-call round 8.
Each dependency uses `afterok`; numerical failures, source/input drift or static
failure prevent the next stage. Round 8 gets an offline artifact/timing review;
manual answer/measurement reading is still required. No full CPU regression,
telemetry preparation, rendering or formal inference is queued. Every earlier
CPU pass remains explicitly reused, not rerun.

Current status is **waiting for H100 allocation**, not runtime qualification
passed. The ledger still preserves 42 prior attempts (10 complete, 26
infrastructure failures, six interrupted); this revision has made zero new
language-generation calls. See `nibi_native_runtime_chain_20261019.json` and the
detailed investigation in `docs/issues/RQ4_5_Nibi_Runtime_Investigation_2026-10-19.md`.


## Nibi deployment record (preserved history)


### 2026-10-20 — FA3 padding probe disposition

Job24686266 completed with zero new language-generation calls. pad96 is feature-bit-identical on all three fixed actual packets, but the largest image still takes115.77s (original117.44s); the approximately1.44% aggregate single-probe timing difference is not a demonstrated throughput fix. pad128 is slower and fails the unchanged full-feature gate. Production adoption and a fresh 18-call smoke were therefore not initiated. Existing complete CPU qualifications and all42 spent attempts remain. GPU/throughput still unqualified; formal not started. Full evidence, historical issues and disposition are in `important_docs/CanvasRCA_Nibi_Pitfalls.md` and `qualification/visual_fastpath_disposition_24686266.json`. Nibi-only work; local RQ4.7 untouched.


### 2026-10-20 — resumed FA3 dispatch testing

Login remains valid. No outstanding jobs were duplicated. Submitted zero-generation
probe 24719764 to compare explicit split counts and a dense FA3 path on fixed
8192/65160-token tensors. Existing complete CPU preparation is reused. No
production backend, formal call or new language smoke is activated. The existing
full-encoder numeric and >=7 actual calls/minute requirements remain.


### 2026-10-21 — dispatch probe AST repair

24719764 failed before kernel execution because a dynamically generated tuple AST
lacked lineno metadata. The exact construction was repaired and compiled/evaluated
against all37 installed operator arguments. Replacement 24724822 is submitted.
No production or local code changed, no new generation calls, no repeated CPU
population work. Candidate numeric and >=7/min qualification are still pending.


2026-10-22: round12 staged, not yet submitted. Native layer3 capture split and allocated-GPU NVML telemetry require affected CPU checks then one actual 18-call/900-second GPU smoke. All round11 outcomes and spent calls remain preserved. Local repository and running experiments untouched.

## Local experiment record (preserved history)

## Local fallback qualification in progress — 2026-10-19

The latest user goal supersedes the local stopping boundary: qualify locally,
then launch the local formal queue. Nibi jobs 24589226/24589420/24589619 remain
pending and unchanged. The local Blackwell runtime preserves RQ4.4's native
backend selection; the H100-specific provisional SDPA change is not applied.
Local actual static and 32-unit checks pass, as does six-case boundary preflight.
The 220-case CPU population audit is now running with eight distinct physical
cores. GPU smoke and formal are not yet activated. No new model call has run.
DD-RQ45-15 records the authority and isolated results root.

## Local qualification passed; formal queue running — 2026-10-19

The current local fallback goal is achieved. Actual local CPU checks pass:
32 units, 220 population cases / 1320 RCA inputs, 33 mechanism cases / 198
QA inputs, 30 runtime probes, input budget, transport invariance, deterministic
repaint and twelve-image manual review. Frozen fingerprint:
`d2299620a4c36294113dcced4e222b76e50e85b378ae55c41678c2cab0e55dac`.

The real local smoke completes 18/18 in 209.5913 seconds, including 100.8999
seconds to the first durable call reservation. Online completion rate is 9.9364
calls/minute; including startup it is 5.1529. Mean vision/transport is 1.4414
seconds. Every answer and all six actual attention summaries were inspected;
input/PNG/trajectory identities, scorer reproduction, ledger, token counts and
BF16/no-preemption checks pass. Model errors remain scored outcomes, not
qualification retries. Attention records are 690–3657 bytes and cover only the
registered two early queries at layer 3, not final-decision attention.

Local formal owner PID 114471 is live, with eight active requests, bounded RAM
lookahead and real committed results. Three initial commits were independently
verified against their saved request/trajectory hashes and durable ledger. The
registered queue retains all 1560 logical positions and supports resume from
atomic completion markers. Native FlashAttention 2 is confirmed in the actual
Blackwell engine log; no provisional H100 SDPA change is applied locally.
Nibi jobs 24589226/24589420/24589619 remain queued unchanged; no Nibi formal
job was submitted. Previous Nibi attempts remain in their separate ledger.

[Local CPU receipt](local_cpu_qualification_20261019.json) ·
[Verified formal launch](local_formal_launch_20261019.json).
Runtime logs, exact inputs/outputs/conversations, scores and measured attention
are under `results/exclusive_spatial_v1/`. Final lossless retention and complete
analysis run after formal calls and writers drain; no final MRR is claimed now.

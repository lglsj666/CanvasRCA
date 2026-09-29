# RQ3.8 experimental contract

## DD-20260929-07: four-job formal authorization with explicit CPU waiver

**Authority.** After v7 smoke job 22942268 completed all 18/18 registered
calls without an infrastructure or artifact error, the user explicitly waived
CPU regression and authorized at most **four** formal Nibi jobs, each limited
to **eight hours**, to cover every registered A/B/C arm on both models. The
waiver is recorded as *not run*, not as a passed CPU test. It supersedes the
older six-job planning limit and the previous smoke-only submission status.

**Operational mapping.** The unchanged 840-case roster membership, case arms,
images, fixed text, inference and scoring are divided into three deterministic
case shards for Qwen and one complete cohort for Gemma. The previous
three-shard smoke-era roster and budget files remain immutable; the four-job
successor uses separate `roster_formal4_q3g1.json` and
`budget_formal4_q3g1.json`. The smoke measured Qwen's concurrent nine-request
batch at roughly 220 seconds/request versus Gemma's roughly 20 seconds; this
supports spending three allocations on Qwen rather than a symmetric 2+2 split,
but is not a formal throughput guarantee. Each allocation prepares its own
cases from frozen public per-case caches before loading vLLM. Gemma waits for
all three Qwen allocations to end, avoiding concurrent writes to the same
preparation targets. A Qwen inference failure does not condition or cancel
Gemma: the Slurm dependency is `afterany`.

**Smoke compatibility boundary.** Formal scheduling/authorization changes
modify RQ3.8 control-plane source hashes but do not modify the request
compiler, renderer, vLLM client, model recipe or scorer. An explicit persisted
artifact review must record the original smoke contract, the exact changed
file allowlist and the current source contract before formal submission.
This is an operational compatibility adoption of the 18 completed live
requests, not a claim that a new smoke or CPU regression ran. Formal cases
still receive live tokenizer context checks; individual capacity failures
retain their registered design-infeasible status.

**Resource caution.** The smoke contains only nine concurrent requests per
model; it is not a reliable proof that 19,440 formal positions will all finish
within 32 allocated GPU-hours. The four jobs have bounded, resumable targets;
if their allocations expire, no fifth formal job is authorized by this entry.
Actual throughput and remaining work must be reported rather than silently
dropping arms or exceeding the job cap.

## DD-20260929-06: one 30-minute v7 GPU smoke allocation

**Authority.** User explicitly authorized one new 30-minute smoke job for the
v7 lossless fixed-text compression successor. This raises the cumulative
RQ3.8 Nibi smoke-allocation cap from seven to eight, and allows exactly one
new v7 submission. It does not authorize a formal job or a CPU-regression job.

**Scope.** The attempt uses the same three registered development cases, two
sequential models, three registered arms per case and the shared <=18 model-call
limit. `sbatch --time=00:30:00` is authoritative; no image, model recipe,
scoring, selection, or dashboard code changes accompany the authorization.
Static/source qualification and the real dual-processor 66-row capacity check
passed before submission. Fresh GPU execution and persisted artifact review
remain necessary; job acceptance alone is not smoke passage.

**Prior state.** Nibi job 22941413 is `FAILED` (2m15s, exit 1) before any model
request. No other current RQ3.8 job was queued/running when this decision was
made. Its artifacts and failure classification remain intact.

**Submission.** Nibi accepted `rq38v7-smoke-attempt8` as job **22942268**;
the receipt records `--time=00:30:00`. This is an accepted submission, not a
completed or passed smoke. Inspect its persisted processor, live inference,
conversation and artifact-review records after it reaches a terminal state.

## DD-20260929-05: v7 lossless shared-text compaction after capacity failure

**Status:** implemented, static and three-case dual-processor preflight passed;
GPU smoke and formal efficacy **not** qualified. Supersedes v6 only for future
requests; the failed v6 smoke and its zero initiated model calls remain archived.

**Context/evidence.** The seventh GPU smoke stopped before vLLM at the real
processor check: AegisLab `INC-01BF937825D4`, Qwen `FULL`, had 35,011 input
tokens against 32,768 available after the unchanged 8,192-output reservation.
The old successful smoke used a shorter 6,180px image; v6's fixed canvas was
7,742px. The user explicitly chose to keep the image, to compress text, and
then clarified that text/image repetition is permitted because the registered
question is the incremental value of a dashboard with **fixed text**.

**Decision.** Do not alter any renderer, PNG, image processor, arm, sampling,
model, output ceiling, or the fixed-text design. In every arm, the shared text
ledger now omits a metric, trace, log or onset card only if its exact entity,
readings and unit/identity can be checked against the existing public anchor.
Unmatched cards stay. Graph rows use a reversible directed typed edge-list:
node types follow the registered ID-length rule, connected endpoints are
recoverable from edges, and nonempty node roles remain explicit. `TEXT_DUP`
still repeats this shared compact ledger by design. No label, case-specific
answer or dataset identity informs compression. The immutable v6 public/PNG
preparation is reused as a read-only visual source; requests and qualification
are versioned under `ops_components_v7`.

**Measured check.** On Nibi, all three existing smoke cases had zero unproven
non-graph cards. The AegisLab component ledger shrank from 19,315 to 4,491
characters. Actual Qwen `FULL` input fell from 35,011 to 27,769 tokens,
leaving 4,999 tokens under the registered input ceiling; `FULL_PAIRS` was also
27,769. The three-case, all-22-arm, two-model processor check covered 66
case×arm rows, found zero context failures, and took 45.64 seconds. Static
source check passed. This is a *capacity qualification*, not an RCA result or
a GPU smoke; unprepared formal cases remain unqualified.

**Consequences.** Repeated telemetry text is removed uniformly from every arm,
so comparisons still hold original text fixed while varying graphics. The
prompt surface changed, so v6's historical smoke cannot be promoted to v7.
No eighth GPU smoke or formal job is authorized by this decision. CPU/browser
regression and fresh persisted GPU smoke review remain required before formal
inference; do not treat processor passage as model-readability evidence.

## DD-20260929-04: One direct GPU smoke after the v6 static pass

**Authority:** the user subsequently instructed: after code and static checks,
directly submit GPU smoke. This supersedes DD-03's stop-after-static boundary
only for one new Nibi GPU qualification job, not for formal inference.

**Decision:** one additional30-minute full80GB H100 job (attempt7 after the
previous six-attempt allowance), both models sequential, the same shared18-call
cap and the three registered development cases. Prepare current inputs and run
the real processor capacity checks inside that allocation; do not submit a CPU
job or run pytest. Record CPU regression as **not run**, never as passed. The
direct-smoke exception cannot satisfy the formal CPU qualification requirement.
No internal600s timeout is reinstated; Slurm still bounds the entire job30m.

The submitter permits only smoke, counts old intentions across version roots,
and permits at most one new v6 submission. Source attestation now includes the
compiled browser bundle in addition to its source files, preventing a source/
bundle mismatch from being silently accepted. No scientific arm, model recipe,
sampling, evidence or budget changes accompany this operational authorization.
An expired SSH/MFA session blocks deployment, not scientific qualification.

Deployment audit found that Nibi's successful old smoke used a portable prepared
snapshot, not the local RQ3.4 contexts or RQ3.7 registration/ledger. Transfer
only the three smoke cases' existing canonical public data, frozen contexts,
parent exports/private scoring records, and the small registration/roster plus
ledger snapshot. No raw-data preparation is rerun. Resolve the ledger symlink
to its actual bytes when packaging; do not copy a dangling workstation link.
On input import, rebase only the known `/home/lglsj/CanvasRCA_nibi/` prefix to
the current checkout and verify the frozen context hash. No fact is rewritten.
This three-case deployment does not establish availability of the full840-case
preparation on Nibi; that remains a prerequisite to any formal submission.

## DD-20260929-03: Mechanism-complete expansion to approximately20000 calls

**Status:** adopted for implementation; runtime unqualified and not launched.
**Authority:** user requests additional registered experiments, updated code,
static checks, then stop. Config `ops_components_v6.json` supersedes v5 for
future work; the historical entries below are preserved.

**Decision/evidence.** RQ3.7 Qwen's LOCAL_LINK–TPV benefit does not establish
link-specific or real-dashboard value. RQ1.1 already tested redundant hybrid
and screenshots; RQ3.6 CALL/DEPLOY changed factual content. Add only controlled
visual-replica mechanisms: marks×footers, calls×deployment, network versus
edge-pairs, graphical corruption versus same-request replication, then locked
exposed-test regression. Keep selection, original text, models and task frozen.
Do not characterize contradictory graphic stress as equal-information images.

**Scope.** A480×16×2=15360; B100×6×2=1200; C360×4×2=2880;
one shared smoke<=18, total19458. Reserve542, new-round hard cap20000. The
user's expansion supersedes the earlier cumulative40000 planning constraint
for this round; historical calls remain recorded, not reset or hidden.
Job authority is NOT expanded: six formal8h full80GB H100 allocations maximum;
previous CPU/GPU qualification intentions count across every version root.

**Alternatives rejected.** Generic text/image/screenshot retest, another
selector, learned router, resolution sweep, and per-case oracle would either
repeat answered questions or obscure attribution. Independent unused events
are not assumed available; exposed test remains exposed.

**Consequences.** Separate v6 results/preparation; source-bound qualification
required later. Shared G01 area accommodates both network and pair tiles,
without changing node_link's approved routing. No new model calls or render
qualification this turn. C requires exact committed prior public views and
contexts; absent artifacts block preparation rather than silently rebuilding
a different anchor. Runtime source/runtime-budget/job availability must be
checked on Nibi before submitting; static checks cannot establish throughput.
Full current arms, estimands, statistics, no-op semantics and caveats are in
the v6 section of the plan. This decision does not promote any old smoke.

## Historical v5 registration

Experiment: exp_operational_component_utility. Version: rq38_ops_components_v5.
Complete scientific protocol, duplicate-history audit, statistical families,
roster, failure semantics and resource limits are registered in
docs/experiment_plans/CanvasRCA_RQ3_8_Operational_Components_Plan.md and
RQs/RQ3_8/configs/ops_components_v5.json. Changes require a new registration;
do not silently migrate the user-rejected predecessor layout or its tests.

## DD-20260929-01: Reference call graph and evidence-preserving pod fallback
**Date:** 2026-09-29  
**Status:** adopted; supersedes v3's all-size lattice C09 for v5

**Context.** The v4 AIOPS-2022 gallery showed a dense pod-level call graph
whose orthogonal routes obscured endpoints. The user identified a prior
AegisLab reference image as the desired C09 drawing and directed that C09 use
that single drawing grammar at every graph size. The same user subsequently
clarified that the call graph may retain pod nodes when public ownership is
insufficient; forcing service-only edges would discard legitimate observations.

**Decision.** Restore the reference image's radial coordinates and direct
quadratic links exactly for its original first two rings; extend that same
grammar to later rings rather than switching to the lattice at 30 nodes. G01
projects pod calls to service calls only through unambiguous public G03
service→pod edges. Ambiguous or unmapped pod endpoints remain pods in G01.
Repeated projected edges collapse to one overview edge; the shared text ledger
retains all original directed pod-level calls. G02 node→pod and G03
service→pod cards and their separate deployment-group renderer are unchanged.

**Evidence.** Re-rendering the reference AegisLab case
`INC-01BF937825D4` with its original v2 evidence/design and restored code
produced an identical PNG SHA-256
`a2e159e3bd71ca34342e1ec0da398f2979c743d534b5ef1f73e647a188088017`.
The inspected AIOPS-2022 case `INC-0060628741E9` has 42 hosted pods, 42
public service→pod associations and zero unmapped hosted pods; its G01 overview
reduced 121 pod calls to 28 distinct service-level edges across 20 services.
The fresh five-dataset CPU gallery contains 150 PNGs, not model-call evidence.

**Alternatives rejected.** Keeping the all-size orthogonal lattice leaves
unreadable overlapping routes; forcing service-only G01 would silently omit
pod calls when public ownership is incomplete; guessing owners violates the
public-evidence contract.

**Consequences.** Version v5 changes model-visible PNGs. It cannot resume v4
render/model targets or inherit v4 qualification. The immutable parent export
can be reused, but v5 requires its own preparation, CPU/browser review and
live GPU smoke before any formal inference. The Windows example gallery is
for human inspection only, not qualification or efficacy evidence.

## DD-20260929-02: Log detail side grouping

**Date:** 2026-09-29  
**Status:** adopted as renderer revision `log-detail-sides-v1` within the
still-unqualified v5 design; previous v5 smoke images do not qualify this
revised renderer.

The previous two-column log details pushed left-column values toward the
center, immediately beside right-column labels. The user observed that this
made unrelated fields look paired. Log details now keep each label and value
together: odd rows hug the left edge, even rows hug the right edge. Metric and
trace detail layout, evidence, field order, units, values, card dimensions and
all experimental arms are unchanged. The renderer source fingerprint includes
the new CSS and TypeScript; fresh PNGs and normal qualification are required
before formal use. The 150-image Windows gallery was regenerated from the same
v5 evidence/design inputs for human inspection.

## Service→pod correspondence successor (2026-09-29)

The v3 smoke-image review found that AIOPS-2022 `INC-0060628741E9` has 42
publicly hosted pods, yet G03 was empty because its Trace rows did not carry
`k8s.pod.name` on the same row as `service_name`. The existing RQ1.1/RQ3.1
public identity rule projects all 42 pod names to registered service identities.
Version v4 therefore supplements, but does not replace, explicit metadata and
same-row Trace witnesses with this deterministic name-derived correspondence.
It operates only on hosted pod identities with a matching typed service alias;
conflicting explicit/observed bindings or ambiguous namespaces are skipped.
The audit records each source separately. No call edge is synthesized from a
service→pod identity. The same supplemented G03 is present in the common text
ledger and visual conditions; the static reading guide now describes instance
identity without claiming that every pair was directly observed in Trace.

This is a model-visible fact change relative to v3, not merely a bug fix to
pixels. v2/v3 artifacts cannot be resumed or used as v4 qualification. The
reusable immutable per-case parent export is unchanged; v4 must build its own
public bundle, renders, CPU/processor qualification and live smoke before any
formal call. No v3 model calls were committed at this decision point.

## Historical C09 v3 visual-grammar successor (2026-09-29; superseded by v5)

The user rejects C09's hidden node-count switch. `graph.node_link` now always
uses the existing bounded connected-component lattice and orthogonal polyline
routing, including rectangular polyline self-loops. The ring layout and curved
edge branch are removed rather than retained as a fallback. This changes PNGs
but not evidence, edges, node IDs, prompts or scores, so it is registered as v3
and requires fresh renderer/CPU and live smoke qualification. All v2 artifacts
remain historical and cannot qualify or resume a v3 target.

TEXT/TEXT_DUP, MR00/MR10/MR01/FULL, NO_LOG/NO_ONSET all retain the complete
common public text. Only redundant graphical components are ablated. Empty
slots and stable indices preserve remaining component geometry. FULL is the
preregistered method. RQ480 is repeated-exposed; no untouched-test claim.

One logical two-model smoke is bounded by 18 initiated calls. The latest user
amendment below removes the internal600s deadline and authorizes attempt4;
Slurm still limits each GPU smoke job to30 minutes. Earlier attempts remain
archived under their original time limits; the cumulative call ledger is not reset.
CPU qualification is separately capped at eight jobs, each at most one hour.
Formal launch requires static, CPU/browser, processor and smoke checks plus
actual artifact review. Six formal jobs maximum, each one full80GB H100, ≤8h.
Runtime adapter gives dense Gemma31 its true identity and official high-detail
1120 image-token setting; other frozen model fields are inherited explicitly.
Keep history and accounting. No attention, training, API services or Qwen9B use.

## Nibi deployment correction (2026-09-29)

CPU job22922484 passed60 tests and completed480 galleries. GPU job22922720
used a full80GB H100 but completed no calls within600s. Its timeout-only
supervisor status is not a live inference attestation. Full server-log review
also found missing-nvcc/DeepGEMM discovery warnings; no efficacy conclusions
or formal submission may be based on this attempt.

The project entrypoint omitted CUDA toolkit loading. Add cuda/12.9, matching
the installed PyTorch2.11 CUDA12.9 build, and check nvcc plus headers explicitly.
Use persistent runtime-specific Triton/vLLM compilation caches instead of
per-job roots; installed Triton's writer uses unique temporary files and
atomic replacement. Keep ports per-allocation. This repairs deployment and
compilation reuse, not scientific inputs, graphical layout or decoding.
CPU job22923347 qualifies the correction. Do not infer that it supplies GPU
qualification. Preserve all predecessor logs and successful rendered inputs.

## Explicit GPU requalification authorization (2026-09-29)

After the deployment repair and CPU job22923347 (61 tests and24 processor
checks passed), the user explicitly authorized at most TWO additional GPU
smoke attempts. This supersedes the exhausted single600s time-window rule for
these two repair attempts only. Each additional supervisor remains bounded by
600s, including startup and switching; each Slurm job remains <=30 minutes.
There are at most THREE GPU smoke jobs total including22922720. The SAME
18-initiated-call ledger is retained across all attempts; successful responses
are not resampled. Attempt1 initiated zero model calls. Preserve each attempt's
supervisor report and review before replacing the current summary. Stop
submitting qualification jobs as soon as sufficient live validation passes.

## Final authorized supplementary submission (2026-09-29)

GPU attempt2, job22923667, reached its600s supervisor bound without initiating
a model call. Weight loading took15.47s (model-loading phase23.112s). The
missing-nvcc warnings were resolved. New FlashInfer GDN object files and its
build.ninja show compilation was still occurring; Slurm MaxRSS100660820K was
close to the96GiB allocation. There is no confirmed OOM or driver failure.

For attempt3 only, inherit MAX_JOBS=8 to bound Ninja compilation concurrency
to the allocated CPU count, and request192GiB host RAM through the sbatch
environment override SBATCH_MEM_PER_NODE=196608. Keep one full80GB H100,
eight CPU cores, <=30m Slurm allocation,600s supervisor, the same aggregate
18-call ledger, and all source, renderer, model/backend and sampling settings.
This is an operational resource adjustment, not a scientific intervention or
a claim that startup is now fixed. Preserve attempt2 reports before submission.
At the user's request, stop immediately after obtaining the attempt3 job ID;
do not monitor it, launch formal jobs, or change local model files this turn.

## Post-attempt3 review and formal-launch hold (2026-09-29)

User authorized formal submission conditional on successful qualification.
Job22927066 exited0 after10m06s; supervisor600.227s is bounded_timeout with
qualification=passed, but accounting is empty, actual_completed=0 and
live_coverage=[]. No runner log, server attestation or conversation exists.
This preserves timeout-only passage without misreporting live validation.

Weights loaded in21.11s, model loading26.625s. No ERROR/Traceback/OOM or
server-ready line was found. The last ordinary server message is encoder
profiling. FlashInfer selected auto GDN JIT; its Ninja log contains newly built
objects from this allocation, whereas the shared library still has its older
August timestamp. This supports incomplete startup compilation as a blocker,
not slow checkpoint loading or a demonstrated driver/OOM failure. Peak RSS was
105453752K within192GiB. More host RAM did not establish service readiness.

Artifact review remains blocked: no actual model input/output can be reviewed,
and Gemma has not started. Do not submit six formal jobs to diagnose this
unresolved startup path. All three authorized smoke submissions are consumed;
additional live qualification needs explicit authorization. Preserve all logs,
reports, prepared inputs and compiler-cache objects; no renderer/model changes,
new jobs or local model deletion are performed by this review.

## User-authorized startup repair and attempt4 (2026-09-29; current)

**Evidence.** Local RQ3.7 A Qwen logs show Triton/FLA with auto, weight load
32.51s and engine profile/cache/warmup24.66s. Nibi attempts2/3 show FlashInfer
with auto, weights15.47/21.11s, but no ready endpoint before the old deadline.
The installed vLLM0.24 resolver unconditionally selects FlashInfer for SM90
when requested=auto; it does not choose that branch on local SM12x. FlashInfer
0.6.12's generator iterates two dtypes and five Boolean options (64 CUDA kernel
instantiations plus launchers). Ninja object timestamps confirm compilation in
both interrupted allocations; there is no proven driver defect, OOM or TP
deadlock. TP=1, so a published multi-worker deadlock is not our diagnosis.

**Decision.** Use a new immutable runtime/inference.triton_v2.yaml via
NibiGemma31QwenTritonV2: only explicitly pin Qwen gdn_prefill_backend=triton
in addition to the already registered Gemma31/deployment adapter. This uses
the same backend family as the successful local run and avoids the specific
SM90 FlashInfer C++ JIT, not all compilation. Preserve the prior profile and
all logs. Sampling, weights, BF16, context, image policy, evidence and rendering
stay fixed; kernel choice is recorded and must receive fresh GPU qualification.
Numerically identical outputs are not presumed across backend/hardware changes.

**Authorization.** The user requests a new job after repair and removal of the
script-internal time limit. Exactly one additional GPU smoke (attempt4) is
authorized, cumulative max_jobs=4. Remove the600s supervisor deadline AND the
early24-minute Slurm USR1 signal for smoke. Retain Slurm30m,18 aggregate calls,
300s per-request timeout, sequential models, full80GB H100 and eight CPU cores.
Use remaining CPU allocation8 (<=1h) to qualify source/runtime changes before
GPU submission. Formal jobs retain their separate8h and drain-window policy.

**Status semantics.** A new smoke is passed only after all planned logical
targets persist, both model attestations exist, and no integrity/infrastructure
error occurs. Interruption/zero-call completion is incomplete, not passed;
interrupted streaming checkpoints are retained. Historical timeout-only statuses
are not retroactively changed. Formal inference remains disabled until review.

Primary implementation reference: installed qwen_gdn_linear_attn.py resolver,
and [vLLM upstream source](https://github.com/vllm-project/vllm/blob/v0.24.0/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py).
Related report (different TP setup; corroborates workaround, not our cause):
[vLLM issue41865](https://github.com/vllm-project/vllm/issues/41865).

CPU repair qualification job22930024 completed in2m08s, exit0:68 tests passed
in59.95s and all24 case/arm dual-processor checks passed in7.93s. Static checks
passed for1295 source lines. No local tests or new gallery generation occurred.
Submit attempt4 with192GiB host RAM, eight cores and one full80GB H100; its
Slurm limit remains30m and no script-internal smoke deadline remains. The
submission receipt supplies the job ID; live success is not yet established.

## User-authorized endpoint repair and attempt5 (2026-09-29; current)

Attempt4/job22930381 FAILED after7m13s. Qwen reached ready at395.32s, but the
live tokenizer used inherited VLLM_BASE_URL:8000 while server/probe used the
allocation port30381. Three TEXT targets failed before generation accounting;
zero generation calls were initiated and Gemma never started. Supervisor's
exception path left a stale running marker; that is not a successful smoke.

User explicitly authorizes repair and exactly ONE new job. Cumulative GPU
smoke allowance becomes5; CPU-only allocation allowance remains8 (exhausted).
Attempt5/job22932223 was held and cancelled before allocation. The user then
explicitly ordered an immediate replacement GPU smoke with NO CPU regression.
Attempt6 is that replacement and runs the GPU smoke directly under the same
30-minute limit. Existing CPU/browser/processor results remain historical
qualification evidence, but current-source CPU proof is waived for this smoke
only; formal execution still requires it. No separate ninth CPU job, extra
generation request, internal600s deadline or formal submission is added.

The RQ endpoint adapter synchronizes VLLM_BASE_URL from the selected runtime
spec before service/driver launch; the shell entry also projects the job port
to VLLM_BASE_URL. Attestation requires the SDK and server addresses to match.
Tests capture probe/tokenizer/SDK endpoints for both models and two nondefault
ports. Tokenizer failures log only endpoint, exception type and HTTP status,
never prompts, response bodies or credentials. Supervisor exceptions commit
failed status. No scientific input, renderer, model profile or sampling change.

Archive attempt4 artifacts/source before clearing ONLY its three confirmed
pre-generation TEXT failure flags. Preserve calls.sqlite, all previous job
receipts, logs, prepared inputs and accounting; no automatic retry rule is
changed. The logical smoke still has18 aggregate generation calls. Stop after
receiving the single new job's submission ID; GPU success remains unclaimed.

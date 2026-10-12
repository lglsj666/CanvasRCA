# RQ3.8 experimental contract

Experiment: exp_operational_component_utility. Version: rq38_ops_components_v2.
Complete scientific protocol, duplicate-history audit, statistical families,
roster, failure semantics and resource limits are registered in
docs/experiment_plans/CanvasRCA_RQ3_8_Operational_Components_Plan.md and
RQs/RQ3_8/configs/ops_components_v2.json. Changes require a new registration;
do not silently migrate the user-rejected predecessor layout or its tests.

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
Attempt5 runs CPU/browser regression and dual-processor checks INSIDE the same
30-minute GPU allocation with CUDA disabled for those checks, then requires
their current-source receipt before starting vLLM. Submission-time static
checks authorize allocation only, not inference. No separate ninth CPU job,
extra generation request, internal600s deadline or formal submission is added.

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

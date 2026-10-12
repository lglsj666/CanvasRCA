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

One logical two-model smoke is bounded by 18 initiated calls and 600 seconds.
The user additionally caps GPU smoke submissions at three jobs, each with a
30-minute Slurm walltime. This does not reset the logical call/time budget.
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

# RQ4.5 Nibi runtime investigation — 2026-10-19

## Authority and stopping point

The active user goal permits environment changes and unlimited **serial** smoke
rounds of at most 18 initiated calls, with the existing 15-minute allocation
limit per round. Preserve every spent attempt and committed answer. Qualify
formal-equivalent throughput of at least **7 actual completed calls/minute**;
then stop. This goal does not launch the formal experiment. The earlier closure
after round 6 is superseded prospectively, not erased from history.

## Official documentation reviewed before diagnosis

The browser search service received an access-denied page. Direct HTTPS retrieval
from WSL succeeded; the complete page bodies were read, including installation,
module hierarchy, virtual environments and troubleshooting. Local retrieval cache:
`/tmp/canvasrca-alliance-docs/` (temporary research material, not experiment input).

| Primary source | Relevant guidance |
| --- | --- |
| [Nibi](https://docs.alliancecan.ca/wiki/Nibi) | H100 SXM 80 GB nodes; distinguish full GPUs from MIG; node-local storage exists; shared `/home`, `/project` and `/scratch` use VAST storage. |
| [Python](https://docs.alliancecan.ca/wiki/Python), revision 201101 | Load a compatible Python module; use `virtualenv --no-download`; load the same modules before activation; prefer Alliance wheels through `pip --no-index`; use a node-local environment to avoid many small shared-filesystem reads. Do not place a persistent environment in scratch because of purge risk. Avoid modifying module-provided Python paths. |
| [Using modules](https://docs.alliancecan.ca/wiki/Using_modules), revision 159471 | Module loading changes paths and library configuration; the hierarchy controls compatible compiler/library combinations; load modules explicitly in batch scripts. |
| [Standard software environments](https://docs.alliancecan.ca/wiki/Standard_software_environments), revision 193658 | StdEnv/2023 uses the GCC 12.3 family and AVX2-compatible software; compiler/CUDA dependencies belong to its module hierarchy. |
| [AI and Machine Learning](https://docs.alliancecan.ca/wiki/AI_and_Machine_Learning), revision 199595 | Prefer virtualenv over Anaconda; stage suitable runtime dependencies to node-local storage; separate local storage from durable experiment records. |
| [PyTorch](https://docs.alliancecan.ca/wiki/PyTorch) | Prefer Alliance PyTorch wheels; H100 requires a sufficiently new Torch; distinguish CPU input feeding from GPU computation. |
| [Installing software](https://docs.alliancecan.ca/wiki/Installing_software_in_your_home_directory), revision 194398 | Use module-provided libraries and EBROOT paths; do not inject system libraries ahead of the CVMFS RUNPATH. |

The older [Compute Canada Python presentation](https://indico.cism.ucl.ac.be/event/4/contributions/33/attachments/33/65/Python_at_Compute_Canada1.pdf)
was also read as background. Current official documentation takes precedence over
its older toolchain examples.

## Measured baseline; do not confuse these timing scopes

Round 6 job **24554682** timed out. Eight of the frozen 18 smoke positions are
committed across rounds 5–6. Round 6 initiated 11 calls: three completed and eight
reached the deadline; two remaining positions were never initiated. The global
ledger retains 32 attempts. No formal call has run.

- Startup to first new call: **238.337 seconds**.
- Remaining request window: **661.663 seconds**.
- Three new commits: **0.200/minute** including startup, **0.272/minute** after
  the first request. This censored small batch is not steady formal throughput.
- Three completed calls took **1.34–1.58 seconds** of CPU packet preparation.
- Worker encoder/transport measurements were **13.765**, **17.718** and
  **116.792 seconds**. These include transfer and embedding work, not only the
  vision kernel.
- Recorded language intervals were **47.731–534.532 seconds**, but include
  admission, scheduling and finish-RPC waiting. They are not isolated decoder
  timings. No KV preemption was observed; maximum observed decode batch was 4.

The completed local RQ4.4 formal run achieved **840 / 6252.56 seconds = 8.06
calls/minute**. Its mean vision/transport interval was approximately 3.08 seconds.
Its hardware, software environment and evidence differ, so it is a deployment
reference, not an interchangeable controlled timing measurement.

## Hypotheses to test, not established causes

1. The current interpreter lives in a shared scratch environment; eight spawned
   CPU workers and the engine repeatedly import its many small package files.
   This can explain startup, but cannot alone explain all online latency.
2. The GPU batch scripts replace `PYTHONPATH` instead of preserving the module
   initialization path. Package versions and actual imported library locations
   need to be audited before rebuilding anything.
3. Batch scripts set `VLLM_TRITON_FORCE_FIRST_CONFIG=1` and
   `CUBLASLT_WORKSPACE_SIZE=1`, unlike the successful local launcher. Installed
   vLLM source confirms the first flag bypasses normal autotuning in favour of
   the first runnable configuration. Its speed impact and the workspace flag's
   actual effect must be measured, not assumed.
4. GPU vision encoding and its CPU transport use a collective worker RPC that
   can delay ongoing decode. Admission reserves each request's full 8192-token
   output allowance, limiting effective concurrency on the measured KV cache.
   Neither fact justifies changing the output limit, evidence or model precision.

`profile_runtime_nibi.sbatch` measures imports and representative BF16 linear /
Flash-SDPA kernels with the old and default workspace settings. It does not load
model weights, generate an answer or consume a model call. At creation its shell
and embedded Python passed syntax checks; execution is pending SSH access.

## Access interruption

The multiplex socket responds locally but the existing remote transport no
longer responds to commands or terminal input. A fresh direct connection reaches
Nibi and requests MFA. A new `reconnect` window in the existing WSL tmux session
is waiting for the user's login. Independent local research and source checking
continue; no remote deployment or fresh timing result is claimed while access
is unavailable.

## First measured environment/primitive qualification

Access resumed after the user's new MFA login. H100 job **24585258** completed
successfully in 2:16 with zero model calls. The three sequential subprocesses
used the same original environment:

| Measurement | Old flags, first process | Default workspace, next process | Module paths + normal tuning, third process |
| --- | ---: | ---: | ---: |
| Total imports of Torch, Transformers, vLLM, XGrammar and FlashInfer | 88.03 s | 21.12 s | 18.42 s |
| BF16 linear, 4096 × 5120 × 15360 | 0.817 ms | 0.813 ms | 0.813 ms |
| Flash SDPA, 16 heads, length 8192 | 1.287 ms | 1.287 ms | 1.288 ms |

**Interpretation:** import costs are substantial and strongly cache-sensitive.
Because process order was fixed and filesystem caches warmed, the import
difference cannot be attributed solely to the environment flags. These sampled
GPU primitives run at normal speed and show no large workspace-related slowdown.
They do not qualify the complete model's encoder or decoder. Actual requests
still need profiling. CUDA/library paths and package versions are preserved in
the three directly readable JSON records under
`RQs/RQ4_5/findings/nibi_runtime_profile_24585258/`.

CPU environment build job **24585280** failed before model use: exact old pins
NumPy 2.3.5, SciPy 1.16.3 and XGrammar 0.2.3 are absent from the current Alliance
wheelhouse. The blocked dependency job 24585461 was cancelled. Successor build
job **24585572** uses available exact Alliance wheels for the rest and copies
every installed RECORD file of those three exact old packages with SHA-256
verification. The actually imported old Pillow is 12.1.0; stale Pillow-SIMD
metadata is omitted from the new environment. OpenCV uses its proper module and
the Alliance placeholder wheel rather than a foreign binary installation.
Targeted old/new processor-byte equivalence remains mandatory.

Diagnostic smoke **round 7, job 24585685**, resumes the ten unfinished positions,
preserving the eight completed answers and all 32 previously spent attempts.
Only the first encoder and first prefill are profiled; early Python execution
statistics and bounded operator tables identify online waiting/computation.
This profiled round is explicitly ineligible to establish final throughput.
Its operational wrapper and receipt are retained; model math, prompts, token
selection, position mapping and decoding remain unchanged. Formal stays closed.

## Round 7 outcome and measured vision-kernel discrepancy

Round 7 reached the allocation deadline. It initiated ten additional attempts,
committed two answers, and leaves **10/18** original smoke positions complete.
The lifetime ledger contains **42** attempts: ten complete, 26 infrastructure
failures and six interrupted. No formal calls have run. The two new raw answers,
cost records and their original request identities remain at their atomic
commit paths. Profiling is diagnostic evidence, not throughput qualification.

The first real encoder took 18.57 seconds inside the worker. Its 27 FA3 calls
accounted for 17.078 seconds of self GPU time, approximately 99% of recorded GPU
time. GPU GEMM self time was only 51 milliseconds; the much larger CPU linear
interval includes waiting for the preceding attention kernels. Three later
large-image encodes took 115.92–117.29 seconds each. Hence import/weight-loading
overhead cannot explain the online bottleneck.

H100 primitive job **24586776** tested the actual vision head dimension, 72,
with independent random Q/K/V tensors, 16 heads and length 8192, all BF16:

| Backend | Repeated kernel times | Numerical comparison |
| --- | ---: | --- |
| Installed vLLM FA3 | 71.34–72.69 ms | Reference |
| PyTorch Flash SDPA | 1.38–1.42 ms | Maximum absolute difference 0.0004883; mean 0.00000460; passed predeclared rtol 0.02 / atol 0.002 |

This is a roughly 50-fold **kernel-level** discrepancy, not a 50-fold pipeline
speedup claim. The same diagnostic's FA2 alternative hit an unsupported-PTX-
toolchain CUDA error and the process subsequently exited unsuccessfully. Its
partial measurements are preserved. Successor job **24586861** omits FA2 and
tests FA3 versus Torch Flash SDPA at lengths 8192, 45824 and 65160. It performs
no language generation. Its pending allocation was shortened to five minutes
for this small primitive benchmark; the RCA smoke retains its full 15 minutes.

The local GPU is RTX PRO 6000 Blackwell, SM120. Installed vLLM's default flash
version selection chooses FA2 for that family and FA3 for Hopper SM90, absent
an override. This code-level difference is consistent with the measured slow
Nibi path; the historical local run has no equivalent per-kernel profiler trace,
so it is not a controlled attribution of the entire historical timing gap.

Related upstream reports support checking native kernel choice, not assuming
that nominal package version implies identical performance:
[vLLM issue 39323](https://github.com/vllm-project/vllm/issues/39323) describes
an older Qwen/H100 FA3 regression, but uses FP8 and another release, so it does
not establish the cause of our BF16 result. We do not adopt its quantization.

Full native-encoder qualification job **24586948** is queued after the long-
shape test and processor-environment equivalence. It compares three fixed
real input packets, including a large pure-visual input, using the same loaded
weights and original geometry. The candidate is vLLM's native
`mm_encoder_attn_backend=TORCH_SDPA`, with unchanged BF16 precision and no
quantization. Predeclared feature tolerances are relative RMS error ≤0.01 and
cosine similarity ≥0.9999; maximum/mean error and actual timings are also
reported. It generates no diagnosis and restores the original worker settings.

`adopt_runtime_backend_nibi.sh` is written and syntax-checked but **not executed**.
It requires the numerical and processor qualifications, archives the previous
frozen recipe and answers, and changes generation identities prospectively.
Unchanged population CPU evidence is reused explicitly, never reported as a new
CPU regression. A clean, unprofiled 18-call smoke and complete artifact review
remain necessary. Neither the native backend nor the new environment has been
declared qualified for formal execution.

## Successor primitive results and environment staging repair

Job **24586861 COMPLETED / 0:0** in 44 seconds. The same-input native BF16
comparison passed at every predeclared length:

| Patches | FA3 seconds/block | Torch Flash SDPA seconds/block |
| ---: | ---: | ---: |
| 8192 | 0.07079–0.07272 | 0.001383–0.001417 |
| 45824 | 2.13689–2.13705 | 0.03898–0.03925 |
| 65160 | 4.31906–4.31919 | 0.07938–0.07954 |

The last FA3 value times 27 blocks reproduces approximately 116.6 seconds,
consistent with the real large-image encoder. This identifies a dominant
kernel path, but is still not a measured full-model speedup. The larger-shape
maximum absolute output difference was 0.0002442; the original rtol/atol
criteria were not changed after seeing the numbers.

Environment import job **24587191 COMPLETED / 0:0** in 86 seconds. It resumes
the already installed package set after build 24585572 stopped at dependency
metadata checking; no package reinstall, fake metadata or PIL replacement was
used. Its receipt explicitly retains the two exact metadata warnings and
records the actual Alliance OpenCV module and qualified Pillow implementation.
Processor equivalence job **24585721 COMPLETED / 0:0** in 200 seconds; all nine
actual packet tensors and metadata are byte-identical across environments.

Full-encoder job **24586948 TIMEOUT**, with zero language-generation calls and
no numerical comparison produced. Inspection at 13 minutes found its `cp`
process in uninterruptible file-read wait, before the Python/model entry.
This was a new, avoidable deployment bottleneck introduced by copying the
entire runtime environment for every allocation. Remove that copy and activate
the already qualified persistent environment directly, preserving the module
initialization paths. Import/startup costs are measured once per process.

User explicitly resumes the next step. Successor full-encoder job **24589226**
uses the direct environment and the same three preselected real packets and
unchanged numerical criteria. It still generates no RCA answer. The complete
unprofiled smoke is not submitted until the encoder result and source-bound
forward freeze pass. Existing full-population CPU evidence remains reused;
no telemetry preparation or dashboard regeneration is scheduled.

The guarded CPU freeze is job **24589420**, `afterok:24589226`; it changes only
the native vision backend in the scientific configuration, preserves the old
source/recipe/requests, verifies every unchanged payload and reruns static
checks. CPU-only job **24589619**, `afterok:24589420`, registers the next exact
18-call supplement without changing existing rows, submits round 8 and queues
offline artifact/timing checks after successful smoke completion. Those checks
report both complete-allocation and online rates, plus a clearly labelled
1560-call startup-amortized projection. They cannot grant formal authorization
or mark manual answer reading complete. If an earlier stage fails, Slurm's
dependencies prevent downstream execution.

The last scheduler estimate is 2026-10-19 **17:01:51 America/Toronto** for the
encoder allocation; this is a queue estimate and can change with backfill.
No model operation or fresh language generation has started while it is pending.


## 2026-10-20 remote-only continuation

Full native encoder comparison **24589226 failed** unchanged numerical gates on all three real packets (relative RMS 0.0175–0.0358; cosine below 0.9999). Do not adopt TORCH_SDPA. The unexecuted afterok children 24589420/24589619 were recorded and cancelled. Existing population CPU qualifications remain valid with their lineage; no population rerun or language generation was started. A zero-generation FA3 head-padding candidate probe replaces a pending draft: 24686204 cancelled before allocation, successor **24686266** tests original FA3 and pad96/pad128 while retaining the original scale and trimming to head_dim72. Full feature tolerances remain RMS≤0.01 and cosine≥0.9999. No production adoption or speed pass is claimed.

The user's latest instruction authorizes the Nibi RQ4.5 formal run only after clean qualification and ≥7 actual calls/min, superseding the earlier stop-after-qualification boundary prospectively. Work is remote-only; local RQ4.7 is untouched. All known historical CPU, smoke and operational issues are consolidated in [the Nibi pitfalls record](../../important_docs/CanvasRCA_Nibi_Pitfalls.md), which must be updated for new issues.


### 2026-10-20 — FA3 padding probe disposition

Job24686266 completed with zero new language-generation calls. pad96 is feature-bit-identical on all three fixed actual packets, but the largest image still takes115.77s (original117.44s); the approximately1.44% aggregate single-probe timing difference is not a demonstrated throughput fix. pad128 is slower and fails the unchanged full-feature gate. Production adoption and a fresh 18-call smoke were therefore not initiated. Existing complete CPU qualifications and all42 spent attempts remain. GPU/throughput still unqualified; formal not started. Full evidence, historical issues and disposition are in `important_docs/CanvasRCA_Nibi_Pitfalls.md` and `qualification/visual_fastpath_disposition_24686266.json`. Nibi-only work; local RQ4.7 untouched.

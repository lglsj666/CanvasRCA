---
name: vlm-serve
description: Launch, verify, monitor, or debug the canonical CanvasRCA local vLLM server for Qwen3.6-27B and Gemma-4-26B-A4B-it. Use for project-owned VLM inference, adapter serving, GPU-memory issues, startup failures, or effective-configuration audits.
---

# Canonical vLLM serving

Read `Codex.md` and the target run contract before launching. Use
`venvs/infer/bin/python`, the unified client in `RQs/vlmrca/vlm/client.py`, and
the applicable shared or RQ-specific launcher. Do not launch if the effective
configuration differs from the frozen contract.

As of the 2026-08-03 audit, `scripts/vllm_vlm/serve_vllm.sbatch` is a legacy
SLURM launcher and does not satisfy the full frozen local recipe. Do not use it
as a canonical launcher until it is explicitly reconciled. The existing
`RQs/RQ0/scripts/vllm_vlm/serve_rq0_local.sh` matches the core base-model recipe
for RQ0; another RQ must register its own applicable launcher or a corrected
shared launcher.

## Frozen inference recipe

Use unquantized BF16 with:

```yaml
max_model_len: 32768
max_tokens: 16384
temperature: 0.0
top_p: 1.0
seed: 42
generation_config: vllm
gpu_memory_utilization: 0.65
max_num_seqs: 8
tensor_parallel_size: 1
max_images_per_prompt: 8
max_videos_per_prompt: 0
disable_thinking: true
async_scheduling: false
enable_prefix_caching: false
enable_chunked_prefill: false
use_flashinfer_sampler: false
cublas_workspace_config: ":4096:8"
gdn_prefill_backend: triton
moe_backend: triton
triton_force_first_config: true
enforce_eager: true
trust_remote_code: true
enable_log_requests: false
```

Serve Qwen from `models/Qwen3.6-27B` as `Qwen/Qwen3.6-27B` with
`batch_invariant: false`; its GDN attention rejects that mode. Serve
Gemma-4-26B-A4B-it with the same recipe except `batch_invariant: true`. Record
the effective value.

`gpu_memory_utilization` is an operational capacity setting. New runs default
to 0.65, but a historical difference alone does not invalidate or make results
incomparable. OOMs and request failures remain infrastructure outcomes.

## Launch and verify

1. Confirm the local checkpoint and tokenizer hashes and available GPU memory.
2. Compare the launcher, client, and frozen contract field by field.
3. Start the server in the background and preserve its log.
4. Query `http://127.0.0.1:8000/v1/models`, then run the registered image-capable
   smoke through the real client.
5. Record effective flags, versions, model path, served name, precision, image
   limit, and termination reason.
6. Monitor frequently during startup; after stable operation, poll about every
   360 seconds.

PID, shared residency, and exact repeated output may be recorded for operations
but are not validity or comparability gates. Resume after restart only when the
new server matches the frozen effective configuration. Preserve old logs with
deterministic resume suffixes and never mix artifacts from different contracts.

For startup OOM, diagnose actual reservation, context length, concurrency, and
other resident processes before changing the registered configuration. Never
switch to quantization to make a run fit.

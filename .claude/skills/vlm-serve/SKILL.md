---
name: vlm-serve
description: Launch, verify, monitor, or debug the canonical CanvasRCA Nibi or local vLLM server for Qwen3.8-27B and Gemma-4-26B-A4B-it.
---

# Canonical vLLM serving

Read `Codex.md`, the selected global inference profile, and the target run
contract. Use `src/vlmrca/vlm/client.py`. Nibi uses
`configs/vllm_inference.yaml` with
`scripts/vllm_vlm/serve_canvasrca_nibi.sh`; local WSL uses
`configs/vllm_inference_local.yaml` with
`scripts/vllm_vlm/serve_canvasrca_local.sh` after sourcing
`scripts/env_local.sh`. `CANVASRCA_VLLM_CONFIG` is the explicit selector.
Never infer the profile from the hostname or substitute a copied RQ launcher.

Both models use unquantized BF16, 40960 context, 16384 output ceiling,
temperature 1.0, top-p 0.95, seed 42, thinking off, prefix caching off, and
`max_num_seqs=128`. Both models use xgrammar with arbitrary JSON whitespace
disabled. Qwen3.8 is pinned to official revision
`1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`, has no project pixel-budget
override, explicitly disables both thinking and preserved thinking, and keeps
chunked prefill disabled. Gemma uses `max_soft_tokens=1120` and chunked prefill
enabled.

The Nibi global config sets `gpu_memory_utilization: null`. Confirm that the
effective argv contains no `--gpu-memory-utilization` flag. This removes the
CanvasRCA fraction cap; it does not remove physical or vLLM limits. Diagnose
OOMs from the allocation, resident processes, context, scheduling capacity, and
actual image tokens. Never use quantization as a workaround.

The local profile points to the project resources under
`/home/lglsj/CanvasRCA/` and sets `gpu_memory_utilization: 0.65`; confirm that
its effective argv emits `--gpu-memory-utilization 0.65`. A static parity check
must show that the two profiles differ only in deployment paths and this VRAM
fraction. Every attestation and run contract records the profile actually used.

Before a full run, record the Slurm allocation, modules, environment,
model/tokenizer, global config, launcher, client, and adapter hashes. Start the
server in the background, preserve its log, verify the models endpoint, write a
live attestation, and run the bounded smoke. Monitor startup closely, then poll
about every 360 seconds.

PID and exact repeated output are operational metadata, not validity gates.
Sampled decoding does not promise byte-identical repetition. Resume only when
the server matches the frozen effective contract.

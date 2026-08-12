---
name: vlm-serve
description: Launch, verify, monitor, or debug the canonical CanvasRCA Nibi vLLM server for Qwen3.6-27B and Gemma-4-26B-A4B-it.
---

# Canonical Nibi vLLM serving

Read `Codex.md`, `configs/vllm_inference.yaml`, and the target run contract.
Use `src/vlmrca/vlm/client.py` and
`scripts/vllm_vlm/serve_canvasrca_nibi.sh`. Never substitute a copied RQ
launcher or unrecorded server flag.

Both models use unquantized BF16, 32768 context, 16384 output ceiling,
temperature 1.0, top-p 0.95, seed 42, thinking off, prefix caching off, and
`max_num_seqs=128`. Both models use xgrammar with arbitrary JSON whitespace
disabled. Qwen has no project pixel-budget override and keeps chunked prefill
disabled. Gemma uses `max_soft_tokens=1120` and chunked prefill enabled.

The Nibi global config sets `gpu_memory_utilization: null`. Confirm that the
effective argv contains no `--gpu-memory-utilization` flag. This removes the
CanvasRCA fraction cap; it does not remove physical or vLLM limits. Diagnose
OOMs from the allocation, resident processes, context, scheduling capacity, and
actual image tokens. Never use quantization as a workaround.

Before a full run, record the Slurm allocation, modules, environment,
model/tokenizer, global config, launcher, client, and adapter hashes. Start the
server in the background, preserve its log, verify the models endpoint, write a
live attestation, and run the bounded smoke. Monitor startup closely, then poll
about every 360 seconds.

PID and exact repeated output are operational metadata, not validity gates.
Sampled decoding does not promise byte-identical repetition. Resume only when
the server matches the frozen effective contract.

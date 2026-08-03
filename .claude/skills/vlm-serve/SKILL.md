---
name: vlm-serve
description: Serve an open-weight VLM (Qwen3.5/3.6, Gemma 4) with vLLM on the cluster's H100 GPUs for self-hosted inference. Use when running RQ3 open-weight models, setting up the GPU serving path, or debugging vLLM startup, OOM, non-reproducible decoding, or multi-image limits.
---

# Serving open-weight VLMs

Self-hosted models carry no per-token cost, which is why RQ1/RQ2 screening runs
on an open model rather than an API one. As of DD-14 there is a second and
stronger reason: **open-weight models can be made bitwise reproducible and the
Claude 5 API models cannot.** Bedrock rejects `temperature` for that generation,
so their replicate noise is irreducible (±0.050 MRR at n=100), while the recipe
below gives 0 of 20 differing rankings.

The client talks to vLLM through its OpenAI-compatible endpoint, so
`RQs/vlmrca/vlm/client.py` needs no special backend — just `VLLM_BASE_URL`.

## The reproducible decoding recipe — use this verbatim

Non-negotiable for any run whose numbers get compared to another run:

```
--generation-config vllm --seed 42 \
--no-enable-prefix-caching --no-enable-chunked-prefill
```

Each flag earns its place, and this was ablated rather than assumed:

- `--generation-config vllm` stops the model's shipped `generation_config.json`
  from overriding the request. Without it the Gemma bake-off cells silently ran
  at temperature 1.0 / top_k 64 / top_p 0.95 while the Qwens ran greedy — vLLM
  logs the override, and nobody read the log. **Always grep the server log for
  `sampling parameters have been overridden`.**
- The two cache flags are what actually close it. With explicit greedy sampling
  but caches on, two identical runs still disagreed on 16 of 20 cases: the second
  run hits a KV cache the first warmed, the changed reduction order flips a
  token, and an autoregressive answer cascades from there.
- `--enforce-eager` is **not** required. Caches off with CUDA graphs on gives
  0/20 and 5.9 s/case; adding it also gives 0/20 but costs 19.0 s/case, a 3.2×
  tax for nothing.

The two recipes give *different* MRRs on the same cases (0.529 vs 0.475) because
the kernel paths differ. Determinism makes a recipe repeatable, not
recipe-independent — so whichever is chosen must be used for **every** arm.

Gate it before trusting anything: `sbatch RQs/RQ3/scripts/vllm_vlm/determinism_gate.sbatch`
runs the same model twice over the same cases and asserts identical rankings.
Submit real arrays behind it with `--dependency=afterok:<gate job>`.

## Model → GPU registry

The RQ3 panel, all single-H100:

| Model | tag | GPU-mem-util | Notes |
|---|---|---|---|
| Qwen/Qwen3.5-4B | `qwen3.5-4b` | 0.90 | fastest Qwen |
| Qwen/Qwen3.5-9B | `qwen3.5-9b` | 0.90 | |
| Qwen/Qwen3.6-27B | `qwen3.6-27b` | 0.92 | `--max-num-seqs 8` |
| google/gemma-4-12B-it | `gemma-4-12b` | 0.90 | |
| google/gemma-4-E4B-it | `gemma-4-e4b` | 0.90 | fastest overall (~5.7 s/case); the determinism-gate subject |
| google/gemma-4-26B-A4B-it | `gemma-4-26b-a4b` | 0.92 | slow cold start — allow a 3600 s health timeout (see below) |

Only the Qwens expose a thinking switch (`enable_thinking` via chat template).
The Gemmas have no equivalent and passing one is an error — `get_config` raises
rather than letting a "thinking" arm silently equal its control.

## Launch

Prefer the job arrays; they start the server, health-check it, run every arm and
tear down. One model per array task, port is task-local:

```bash
sbatch RQs/RQ3/scripts/vllm_vlm/run_rq3_modality_array.sbatch    # model x modality
sbatch RQs/RQ3/scripts/vllm_vlm/run_thinking_array.sbatch        # Qwen thinking axis
```

For interactive work, `serve_vllm.sbatch` then:

```bash
squeue -u $USER                        # note the node
export VLLM_BASE_URL=http://<node>:8000/v1
curl -s $VLLM_BASE_URL/models | head   # health check
```

Pre-render before submitting — rendering is cheap CPU work and inference is not,
so GPU tasks should be pure inference against a warm cache:

```bash
python scripts/prerender_config.py --dataset aegislab --n 100 --config cov30
```

## Flags that matter

- `--limit-mm-per-prompt '{"image": 8}'` — **JSON since vLLM 0.25**; the old
  `image=8` form is silently ignored on current versions.
- `--max-model-len` — must cover prompt **plus** output. The prompt is ~9.4k
  tokens, so a 32768-token thinking budget needs ≥42k; 49152 is what the
  thinking array uses. Getting this wrong is what truncated 8 of 20 traces at
  exactly 16384 and produced the bogus "thinking hurts" conclusion.
- `--tensor-parallel-size` — must match `--gres=gpu:h100:N`.
- `--dtype bfloat16` on H100.

## Common failures

- **`ModuleNotFoundError: pyarrow`** — not a vLLM problem. `pip install pyarrow`
  fails on this cluster; `source scripts/env.sh` adds the arrow module's
  site-packages to `PYTHONPATH`.
- **OOM at startup** — lower `--gpu-memory-utilization` (0.85), or raise TP.
- **OOM mid-run, multi-turn only** — the image-retention policy is not dropping
  old images; check the controller's context trimming rather than the server.
- **Model loads but every image request 400s** — usually `--limit-mm-per-prompt`
  syntax (see above) or a vLLM build without that architecture's vision support.
  Verify on a single image before blaming the pipeline.
- **Every failed case takes exactly 7.0 s** — that is 1+2+4 s of retry backoff
  against instant refusals, i.e. the server is gone, not slow. The runner now
  aborts after consecutive backend failures instead of scoring the rest zero;
  a run that ends this way carries `aborted` in its summary and **must be
  excluded from analysis**, not reported as a low score.
- **Two runs disagree** — see the recipe above; check the server log for the
  `generation_config` override line first.
- **Health check times out but the server log looks fine** — compare the log's
  first timestamp against the job's start time before blaming model load. When
  `gemma-4-26b-a4b` DNF'd at 1800 s, its whole server log spanned six minutes and
  ended in "Application startup complete" about two minutes after the harness
  gave up: ~24 minutes went by before vLLM logged anything at all, most likely
  cold library import from the shared filesystem with six tasks starting at once.
  Raise the deadline. **Do not** reach for `--enforce-eager` to "skip the MoE
  autotune" — that autotune takes 25 ms, and the flag changes the kernel path and
  therefore the decoding recipe (DD-12). It is a confound, not a fix.

## M0 gate — CLOSED

The cluster's vLLM serves the panel above over the OpenAI-compatible endpoint
with images; verified 2026-07-23 and exercised by every bake-off run since.

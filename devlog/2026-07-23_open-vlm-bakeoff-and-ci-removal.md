# 2026-07-23 — Open-weight VLM bake-off, vLLM 0.25 serving, CI removal, design docs

## Terms (for this and the sibling devlogs)

- **VLM** — vision-language model (reads images + text).
- **Open-weight** — a model whose weights are public and can be self-hosted (vs. an
  API-only model like Claude).
- **vLLM** — the open-source server we use to run those models on our GPUs.
- **Bake-off** — running several candidate models on the same cases to pick one.
- **MRR (Mean Reciprocal Rank)** — accuracy: 1.0 if the true culprit service is ranked
  first, 0.5 if second, and so on; 0 if not in the top five. Averaged over cases.
- **Top1** — fraction of cases where the true culprit was ranked first.
- **parse (parse rate)** — fraction of cases where the model returned a valid,
  machine-readable answer at all (0 answers = a pipeline failure, not a wrong answer).
- **tok/s** — tokens generated per second (decode speed). **s/case** — wall-clock
  seconds per case. **out-tok** — output tokens produced.
- **Chain-of-thought (CoT), "thinking mode"** — the model writing out its reasoning
  before the final answer. Long reasoning = many tokens = slow.
- **DNF** — "did not finish": the model failed to serve or crashed, so it has no score.
- **OOM** — out of memory (GPU ran out of VRAM, its onboard memory).
- **CI (confidence interval)** — a statistical range around a number; being removed
  from the evaluation this session.
- **H100** — the NVIDIA data-center GPU each model runs on (80 GB of memory).

## What happened

Closed the GPU half of the project's first milestone check ("M0 gate"): self-hosted
vLLM now serves open-weight VLMs on the cluster's H100 GPUs, verified end-to-end
through the smoke test (the case → dashboard → model → parse → score pipeline). Along
the way: removed confidence intervals from the evaluation, added a render cache,
wrote two design docs, and ran a six-model bake-off.

**Bake-off — 20 AegisLab cases, default dashboard settings, hybrid modality (image +
text), one H100 per model, output capped at 16,384 tokens.** Reference point:
claude-sonnet-5 scored 0.797; the best previously published *text-only* score on this
dataset ("text SOTA," state of the art) is 0.679.

| model | MRR | Top1 | parse | median out-tok | tok/s | s/case |
|---|---|---|---|---|---|---|
| gemma-4-e4b | 0.508 | 0.300 | 1.00 | 854 | 163 | 5.7 |
| qwen3.5-4b | 0.485 | 0.450 | 0.95 | 10024 | 96 | 133 |
| gemma-4-12b | 0.467 | 0.350 | 1.00 | 607 | 80 | 8.6 |
| qwen3.5-9b | 0.417 | 0.400 | 0.60 | 15113 | 77 | 224 |
| qwen3.6-27b | 0.050 | 0.050 | 0.10 | 0 (18/20 conn-err) | — | 82 |
| gemma-4-26b-a4b | DNF | — | — | — | — | — |

Caveats attached to those numbers: only 20 cases, one dataset, one dashboard config,
zero-shot (no worked examples given), no per-model prompt tuning. All open models
trail Sonnet-5 (0.797) here. The Gemma "parse 1.00" and the Qwen "parse
0.60/0.95/0.10" are **artifacts of how we configured the run, not the models'
quality** — see the slowness finding below. gemma-4-26b-a4b did not finish: its
startup ran past the 1800-second limit (it is a mixture-of-experts model, "MoE," and
vLLM was still auto-tuning its specialized kernels, made worse by a library
import-order bug); it is slow to warm up, not broken. qwen3.6-27b's server dropped
connections on 18 of 20 cases (the two that ran emitted 11,000-token reasoning) —
it was unstable when generations ran long.

**Why the Qwen models are so slow (the question that prompted this session).**
Not a kernel, serving, or hardware problem. vLLM-reported generation throughput is
normal and comparable across models: qwen3.5-9b 77 tok/s, qwen3.5-4b 96, gemma-4-12b
80, gemma-4-e4b 163. The slowness is **entirely output length**: the Qwen models
emit a 10–16k-token chain-of-thought before answering (qwen3.5-9b median 15,113
out-tok, 10/20 hitting the 16k cap), while the Gemma models emit ~600–850. That is
15–25× more tokens → 20–40× the wall-clock. Root cause: **Qwen3.5/3.6 default to
thinking mode** — vLLM's chat template pre-fills the opening `<think>`, so the
captured response begins mid-reasoning and only closes `</think>` + emits the JSON
thousands of tokens later (confirmed: responses contain a closing `</think>` but no
opening one). When the CoT overruns 16k, the answer never appears → the 0.60 parse
rate for qwen3.5-9b is truncated reasoning, not wrong reasoning.

**Grounding against SIRCL (RL-SLM-RCA), same qwen3.5-9b.** SIRCL's vLLM speed-bench
(570 cases) has median **516** completion tokens at **3.8 s/case** — vs our **15,113**
at **224 s**, ~30×, same model. The difference is *not* `reasoning_mode`: that is a
prompt-scaffold flag and the model still reasons with it set to `none` (confirmed —
the point raised this session). Two real levers bound SIRCL's output: (1)
`enable_thinking=False` by default in its caller (`scripts/run_eda12.py:381`,
`enable_thinking = cfg.get("enable_thinking", False)`; the template then never opens
a `<think>` block, so the model answers directly after a short reasoning), and (2)
`presence_penalty: 1.5` in its sampling config, which suppresses the repetitive
rambling that inflates an unbounded CoT. Our bake-off set neither, so Qwen ran in
full thinking mode. Honest read: the Qwen bake-off numbers reflect *default thinking
mode*, not the model's real cost on this task.

**Serving path — four bugs found and fixed, each one layer deeper than the last:**
1. The newer vLLM (0.25.0) wants the image-limit flag as JSON
   (`--limit-mm-per-prompt '{"image": 8}'`), not the old `image=8` form, so every
   server died immediately while parsing its command-line arguments.
2. The Qwen models use a specialized attention design ("Gated DeltaNet") whose GPU
   code is compiled on the fly at startup, which needs the CUDA compiler (`nvcc`) on
   the path → fixed by loading the `cuda/12.9` module.
3. Startup (compiling + a warm-up pass) takes ~770 seconds, but the health check
   gave up at 900 seconds too eagerly; worse, when it gave up it killed only the main
   server process and left vLLM's separate worker process alive, still holding ~70 GB
   of GPU memory, so the *next* model ran out of memory on startup. Fixed by: a
   1800-second timeout, a persistent compile cache so it only compiles once, killing
   the whole process group, and waiting for GPU memory to actually free (checked with
   `nvidia-smi`) before starting the next model.
4. These reasoning models used up the default 2048-token output budget before
   reaching the answer (parse rate 0.0) → raised the output cap to 16,384 tokens for
   the six open models. (The thinking-mode finding above shows that *turning
   reasoning off* is the better fix — see Next steps.)

**CI removal.** All bootstrap-CI code deleted from `vlmrca/eval/metrics.py`
(`bootstrap_ci` + `BOOTSTRAP_*` consts; `mrr_ci95`/`top1_ci95`/`delta_ci95` keys).
`paired_compare` keeps Wilcoxon p + Cohen's d + delta_mrr. Updated the prose that
mandated CIs: CLAUDE.md invariant 6, results-analyst + trajectory-analyst agents,
experiment/smoke/baseline skills, action_plan M2/M5. Historical result tables left
intact. Verified: `pytest` green, `grep -rn "ci95|bootstrap" vlmrca/ scripts/
tests/` empty, mock smoke still writes summary.json.

**Render cache.** `run_one_case`/`run_experiment` gained `render_cache_dir`
(content-addressed by `case_id` + `cfg.fingerprint()`), default on in smoke_e2e.
`compile_dashboard` is pure/deterministic, so all six models saw byte-identical
dashboards — render noise removed as a confound. Gitignored at `results/render_cache/`.

**Design docs.** `docs/dashboard_design.md` (as-built renderer + per-field
justification) and `docs/rq1_design.md` (RQ1 as budget-constrained information
prioritization: B0 Lean / B1 Standard / B2 Rich levels, each with its own axis
priorities; no computation, design only).

## Key decisions

- **Bake-off run as a SLURM job array (`--array=0-5`), not a sequential job.** One
  model per task on its own H100. ~6× faster and it eliminates the inter-model
  VRAM-leak class by construction (SLURM frees each task's GPU on exit). The
  sequential script (`smoke_bakeoff.sbatch`) is kept but the array
  (`smoke_bakeoff_array.sbatch`) is the one to use.
- **Screening-model recommendation: gemma-4-e4b (primary), gemma-4-12b
  (comparator)** — best MRR with perfect parse and 20–40× the throughput of the
  Qwens, which is what matters for an RQ1 grid of many cells. NOT yet promoted to a
  design decision: the Qwen numbers are penalized by thinking mode and deserve a
  fair re-run first (below).
- **New serving venv `$SCRATCH/venv/vlm-rca-vllm` (vLLM 0.25.0), not an in-place
  upgrade** of `rl-slm-rca-vllm`, which the sibling project depends on.

## Blockers

- **Qwen thinking mode is on by default and unbounded.** Until it is disabled (or
  bounded), Qwen bake-off numbers understate both accuracy (truncated answers) and
  speed (15k-token CoT). Worked around with `max_tokens=16384`, not fixed.
- **gemma-4-26b-a4b won't start inside 1800s.** MoE autotune + `deep_gemm`
  import fallback. Needs a longer warmup or `enforce_eager`/a tuned MoE config, or
  it stays a DNF.
- **qwen3.6-27b server instability** (connection drops on long generations) — not
  root-caused; likely tied to the 16k-token generations and worth revisiting only
  if the model is wanted.

## Next steps

1. Re-run qwen3.5-9b/4b and qwen3.6-27b with the two SIRCL levers: thinking off
   (`extra_body={"chat_template_kwargs": {"enable_thinking": false}}`) and
   `presence_penalty≈1.5`, both via `VLMConfig.extra` (which `_call_openai` already
   splats). SIRCL gets median 516 out-tok / 3.8 s/case on qwen3.5-9b this way;
   expect our outputs to drop from ~15k to a few hundred tokens, parse → ~1.0,
   s/case → single digits. Then re-decide the screening model on a fair comparison.
2. If keeping gemma-4-26b-a4b as a candidate, give it `enforce_eager` or a longer
   health timeout and confirm it serves.
3. Record the settled screening-model choice as a design decision, then start the
   RQ1 grid (docs/rq1_design.md) with that model.

# 2026-07-31 — Case-level causal-integration SFT v1 was stable but regressed

The complete protocol and result are in
`docs/2026-07-31_causal_integration_sft_protocol_and_smoke.md`.

## Work completed

- Added the unified project-owned causal SFT modules under `vlmrca/training/`
  and preparation, training, serving, evaluation, and analysis entry points.
- Froze a development-only roster derived from the RQ0 exposure ledger. It has
  zero formal/reserve overlap and keeps prior v7 diagnostic incidents out of
  the new heldout subset.
- Compiled renderer-v7/CEB inputs for 383 development incidents and retained
  269 label-audited causal-contrast examples.
- Installed and verified FlashAttention 2 and the FLA Gated DeltaNet chunk
  kernel in `venvs/train`; the causal convolution uses the recorded PyTorch
  fallback because the host has no local `nvcc`.
- Passed the mandated RE2-OB/AIOPS-2022/AIOPS-2025 three-case optimizer smoke.
- Trained rank-8 BF16 LoRA on 24 frozen examples for six optimizer steps and
  evaluated the final checkpoint against the base model on 12 disjoint
  development-heldout incidents.
- Recorded all per-case conversations, trajectories, detailed/brief logs,
  run contracts, checkpoints, GPU measurements, and a case-level failure audit.

## Runtime result

The training run completed without numerical or infrastructure failures in
2,925.65 seconds. The sampled physical GPU peak was 96,252 MiB including display
processes. vLLM loaded the step-6 adapter successfully and all 24 paired calls
completed with parse rate 1.0 and matching token accounting. Stable-stage
monitoring used low-frequency polling. No sudo command was needed.

## Quality result

Base MRR was 0.5444 and adapter MRR was 0.4750, for a paired delta of −0.0694.
There were zero improvements, two degradations, and ten ties. AegisLab reversed
by −0.1250, so the adapter failed both the registered macro and per-dataset
promotion conditions. `models/best/` remains empty; only diagnostic checkpoints
remain under `models/checkpoints/`.

Both degradations were list-collapse failures. The base model retained the
accepted root at rank 2 or 3, while the adapter emitted only one wrong service
and removed that root. The v1 two-service supervision shortened average output
from 114.75 to 91.33 tokens and average prediction count from 4.17 to 3.42, with
no scored improvement.

## Decision

Reject and do not scale v1. Do not spend formal/reserve incidents and do not
move to RL/GRPO. If causal-integration SFT continues, first preregister a v2
preservation/correction curriculum with five-service targets, base-correct
preservation examples, base-wrong correction examples, a fresh unexposed
development-heldout selection, and the same paired promotion discipline.

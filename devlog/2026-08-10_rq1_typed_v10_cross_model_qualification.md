# 2026-08-10 — RQ1 typed v10 cross-model qualification

## Scope

Qualified the shared typed Stage-1 transport on local hardware using Nibi code
and Nibi inference settings with local model/dataset adapters. Qwen and Gemma
ran sequentially. No scientific prompt, question, representation, renderer,
private answer, or scorer was changed between models.

## Runner integrity repair

- Initiated model requests now increment the bounded-smoke counter before
  dispatch, so a failed request still counts.
- Concurrent worker summaries are consolidated directly. The parent no longer
  re-enters the runner after workers finish and therefore cannot retry an
  infrastructure-error target outside the registered smoke budget.
- Static checks passed with zero model calls; the 49-arm compile matrix remains
  complete and RQ1 functional source remains below 5,000 lines.

## Typed v10 change

The shared structured-output schema now uses the finite public ID languages:
three-to-five digit entity IDs, `E##` edge IDs, and `M##` panel IDs. This bounds
Qwen's previously observed all-visual long-generation path without embedding a
correct option, changing the binder, or introducing a model-specific prompt.

## Live evidence

Each model used one three-case T/V/H smoke with two stages per case: six calls,
below the 18-call per-model ceiling and within 600 seconds. Qwen completed all
calls after its predecessor all-visual request had timed out; Gemma then ran
only after Qwen's server exited.

| Model | Calls | Stage-1 parse | Stage-2 parse | Supported steps per arm | Truncation | Infra errors |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.6-27B | 6/6 | 3/3 | 3/3 | 6/6 in T, V, H | 0 | 0 |
| Gemma-4-26B-A4B-it | 6/6 | 3/3 | 3/3 | 6/6 in T, V, H | 0 | 0 |

Every request ended with `finish_reason=stop`. Qwen Stage-1 outputs were
431--469 tokens and Gemma outputs were 349--358. Manual inspection of all six
conversation artifacts per model found no failure marker, fenced model
response, thinking trace, missing prompt, or unrecorded truncation. Matching
Stage-1 prompts were byte-identical across models; Stage-2 inputs legitimately
differ because they contain each model's own normalized ledger.

## Status

The shared v10 typed transport is qualified for the tested T/V/H paths on both
architectures. This is diagnostic evidence only and does not replace the future
formal Nibi RQ1 result. Formal execution requires fresh v10 preparation hashes
and new result IDs.

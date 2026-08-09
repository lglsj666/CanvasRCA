# 2026-08-05 — vLLM inference-v2 migration

## Outcome

CanvasRCA now has separate frozen Qwen3.6-27B and Gemma-4-26B-A4B-it
inference recipes under `configs/vllm_inference_v2.yaml`. No full experiment or
training was launched; after the static migration, only the two-call runtime
smoke documented below was executed.

The shared request settings are `temperature=1.0`, `top_p=0.95`, seed 42,
thinking off, BF16 without quantization, 32,768 context, and a 16,384 output
ceiling. Qwen uses `min_pixels=65536`, `max_pixels=2580480`, and chunked
prefill off. Gemma uses `max_soft_tokens=1120`, chunked prefill on, and
xgrammar with `disable_any_whitespace=true`.

## Historical validity action

DD-53 explicitly reclassifies all prior project-local Qwen/Gemma calls made
under vLLM-inference-v1. The artifacts were archived in place, not deleted or
rewritten:

- 9 RQ0 result roots;
- 21 RQ1 result roots;
- 46 legacy local-vLLM result roots under `RQs/OldRQs/`.

These results are invalid for scientific, qualification, promotion, routing,
or efficacy claims and cannot be resumed. CPU-only renderer outputs, static
rosters/partitions, checkpoint bytes, and external-API experiments remain
outside this runtime-specific invalidation. RQ0 and RQ1 are reopened. RQ2 had
no model calls; its static contract was regenerated as V3.

## Contracts and interlocks

- Unified config SHA-256:
  `0e8c51ed8e8723665da59151432675b755ed2183b5522acf1d61d09fcd4488a9`.
- Static lock file SHA-256:
  `3c536f4d98c5582037321e6e7b4bfdf6b0da12c6d5e17a661e8dc8b0a5097f44`.
- Static lock canonical content hash:
  `861b44779af8fe6db7f2cd96556995c3ef9f079d71cf702d3de2fda480957695`.
- Migration registry SHA-256:
  `85d9a5c43493b5d608248964a229f860468a747c9e2ebce8071524460fc7fb3e`.

The lock now includes the RQ0 adapter launcher and the legacy SLURM path. The
SLURM path is intentionally a non-authoritative fail-closed stub; the adapter
launcher remains unusable for a scientific run without an enabled,
experiment-bound successor contract and live attestation.

Historical result roots now fail closed at RQ0/RQ1 model-call entry points.
The RQ0 and RQ1 successor protocols require a new result ID and currently keep
`execution_authorized=false`. Before any new model call they require a
model-specific live V2 server attestation, regenerated image-token/context
preflight, new experiment-bound runtime freeze, and new partition-aware
Rule-16 smoke.

## Validation

- The requested vLLM CLI arguments and JSON payloads were parsed successfully
  in the pinned vLLM 0.24.0 environment.
- Python compilation and shell syntax checks passed for the migrated runtime,
  launchers, attesters, validators, and fail-closed runner interlocks.
- The generated lock reproduced exactly in `--check` mode.
- Focused v2/runtime/RQ1/RQ2 tests passed 90/90.
- The full RQ1 script suite passed 177/177.
- The RQ2 static suite passed 10/10.
- The vLLM-v2, sampling, and RQ0 evidence/grounding/topology regression
  selection passed 50/50.

## Remaining before reruns

Do not launch a model yet. Create versioned successor experiment configs and
result roots, then perform the live attestations, token preflights, runtime
freezes, and Rule-16 smokes. The pinned Qwen chunked-prefill-off recipe emits a
vLLM GDN warning, so its exact live smoke is mandatory before any longer run.

## Lightweight live runtime smoke

At the user's request, a minimal two-call diagnostic was run after the static
checks. This was deliberately not the registered three-case Rule-16 smoke and
does not authorize a full experiment.

- Gemma started with effective `max_soft_tokens=1120`, chunked prefill on, and
  xgrammar `disable_any_whitespace=true`. One real-image strict-JSON request
  returned HTTP 200/`stop`, parsed as
  `{"status":"ok","image_received":true}`, and used 1,142 input plus 14 output
  tokens in 2.269 seconds.
- Qwen started with effective `min_pixels=65536`, `max_pixels=2580480`, and
  chunked prefill off. Its analogous request returned HTTP 200/`stop`, parsed
  identically, and used 1,410 input plus 19 output tokens in 2.614 seconds.
- Qwen emitted the preregistered vLLM warning that disabling chunked prefill is
  not officially supported. The single call succeeded, but the warning remains
  a required caveat for a later registered Rule-16 smoke.
- Both servers were stopped immediately afterward; no full experiment was
  started. The diagnostic summary and conversations are under
  `RQs/RQ1/results/rq1_vllm_inference_v2_runtime_smoke_v1/`.

## DD-54 max-num-seqs capacity amendment

At the user's direction, the sole runtime-value amendment after the diagnostic
was `max_num_seqs: 8 -> 64` for both Qwen and Gemma. `Codex.md` was changed
first, followed by the unified configuration, canonical and adapter launchers,
runtime validator, RQ1 runtime expectations and generated hash lock. No prompt,
evidence, model, precision, decoding, image-budget or scoring field changed.

Current hashes are:

- unified config: `0c868ef495782d00207f5b0d206558f3f6d19c6cd75e79d11e425398b20637c2`;
- static lock file: `893eaf47f0d3ae32a24a1e6478208c7c5e649dc947021732c2d7ba90558648c6`;
- lock canonical content: `a43b388ce95f85e7276c2f3307e5359b1270119a890477a5530f328309d65d3d`;
- migration registry: `5cc5ea9346881a0baca08ad9e2cbe35d68b294b67dbf9c1792421bcbfb35b77f`;
- RQ2 hash-rebound static report:
  `a0f8bc740963baef6e0f0e38debbbf8179493ef334e7bf1f61cbd865f4db6d51`.

The user explicitly waived static checks and smoke for this one-field capacity
change based on prior successful operation with 64 in another project. None
were run. The earlier two-call diagnostic remains an immutable
`max_num_seqs=8` diagnostic and is not a current attestation. No scientific
result had been produced under the intermediate inference-v2 setting, so DD-53
archive membership and RQ0/RQ1 validity status are unchanged.

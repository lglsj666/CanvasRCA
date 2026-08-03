# 2026-07-31 — Equal information removed the apparent visual advantage

The RQ0 implementation and confirmatory run are complete. The full report is
in `docs/2026-07-31_rq0_equal_information_equal_compute_results.md`; this entry
records the engineering path and the decision it forced.

## What was built

The existing renderer/evaluator stack was extended rather than replaced:

- `CanonicalEvidenceBundleV1`, with 64-bin metric series, explicit missingness,
  logs, traces, propagation services/edges, relative onset/severity, opaque
  IDs, provenance, and hashes.
- renderer v6/RQ0 preset with no raw case IDs, dataset labels, fault labels, or
  absolute timestamps.
- three serializers from the same CEB: visual+common text, byte-identical
  text-only, and stable flat JSONL.
- fact-to-representation mappings and a full 720-case atomic-fact parity audit.
- exposure ledger and a frozen 240×3-dataset formal roster.
- resumable inference, per-call token/GPU accounting, static/token/smoke/
  determinism gates, perception probes, and paired analysis.

The final test suite has 72 passing tests. All 720 formal artifacts passed
leakage, representation parity, deterministic generation, and model-specific
32k context checks.

## Runtime failures caught before they became results

Qwen was deterministic within one server but not across restarts under CUDA
graphs. Disabling asynchronous scheduling reduced but did not remove drift.
Pinning cuBLAS and Triton still left 7/60 prediction mismatches, including two
MRR changes. vLLM's batch-invariant mode is explicitly unsupported for
Qwen3.6 GDN attention. Eager execution passed both 60-pair gates exactly, so the
runtime was amended before formal inference and used for both architectures.

Gemma's first startup selected FlashInfer CUTLASS MoE and attempted nvcc JIT.
There is no nvcc on this host. No Gemma result existed yet; the backend was
fixed to vLLM Triton, unused video input was disabled, and the model started
without changing `gpu_memory_utilization=0.65`.

These failures justify the gates: temperature zero and seed 42 were not enough
to make the original vLLM runtime scientifically reproducible.

## What ran

- 4,320 formal calls: 720 incidents × 3 arms × 2 models.
- Qwen: 2,154 successes, six model parse failures, no truncation/infrastructure
  failures.
- Gemma: 2,160 successes, no truncation/infrastructure failures.
- Every model has 720 records per arm, 240 incidents per dataset, and complete
  pairing.

## Result

| model | A visual+text | B text | C flat | ΔA−B | ΔA−C |
|---|---:|---:|---:|---:|---:|
| Qwen3.6-27B | 0.3984 | **0.4113** | 0.3954 | −0.0129 | +0.0030 |
| Gemma-4-26B-A4B-it | 0.3901 | **0.4013** | 0.3623 | −0.0112 | +0.0278 |

Neither model meets both registered +0.05 comparisons. Gemma A−C is
statistically detectable after Holm correction (p=0.0239) but too small and
does not compensate for losing to byte-identical text. RQ0 and its generalized
version are unsupported.

The image is not ignored. A/B top-1 agreement is 74.4% for Qwen and 69.6% for
Gemma, and image swaps change most full rankings. But against B, visual input
breaks more correct decisions than it repairs: 36 vs 20 for Qwen, 33 vs 22 for
Gemma.

## Decision

Do not tune on or rerun the 720 formal incidents. The next useful work is a
descriptive discordance audit and atomic visual-grounding evaluation on
development data. If visual benefit is pursued further, it becomes a new
intervention question—most plausibly visual-grounding SFT followed by RCA SFT—
and requires fresh reserve incidents. The frozen-model representation question
has been answered, even though the answer is negative.

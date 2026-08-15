# RQ1 heldout `direct_rca` local completion

Date: 2026-08-15

## Completion

- Frozen formal lineage: `rq1_v22b_formal_469_20260813`.
- Frozen preparation lineage: `rq1_v22b_prepared_shared_469_20260813`.
- Cases: 469; arms: `T/F/V/P/H/R`; models: Qwen then Gemma.
- Records: 2,814 per model and 5,628 total.
- All records are `completed`, parsed, non-truncated, and ended with `finish_reason=stop`.
- All 24 shard verifications and all 24 shard summaries pass and are complete.
- Every `V/P/H/R` record has same-prefill attention; every `T/F` record is correctly marked text-only.
- Qwen produced 4,849 attention artifacts and Gemma produced 4,849, with zero extra model calls.
- Both vLLM servers were stopped after completion.

## Headline result

The headline set contains 289 AegisLab/AIOPS-2022/AIOPS-2025 cases. The registered
`R-T` and `R-F` visual-routing advantages are unsupported for both models.

| Model | T MRR | F MRR | V MRR | P MRR | H MRR | R MRR | R-T | R-F |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.6-27B | 0.3882 | 0.3604 | 0.3511 | 0.2961 | 0.3510 | 0.3573 | -0.0309 | -0.0031 |
| Gemma-4-26B-A4B-it | 0.3889 | 0.3890 | 0.2725 | 0.2236 | 0.3557 | 0.3223 | -0.0666 | -0.0667 |

For Qwen, Holm-adjusted p-values are 0.0743 (`R-T`) and 0.4157 (`R-F`). For
Gemma, they are 0.0178 and 0.0180 respectively, indicating a statistically
significant negative routed-representation effect rather than the registered
positive effect.

## Operational note

After Qwen completed and verified, the first automatic Gemma attestation raced
with the retiring Qwen API process and correctly failed closed on a served-model
mismatch. No Gemma formal request had started. The stale service then exited,
port 8000 was confirmed clear, and the Gemma-only phase resumed under the same
frozen contract. Qwen artifacts were neither rerun nor rewritten.

## Accounting caveat

Per-request input/output/image/total tokens and wall time are present. However,
`gpu_active_time_s` and `peak_gpu_memory_bytes` are `null` for all records. The
current verifier does not reject these null fields. Accuracy, ranking, parsing,
attention, token, and wall-time conclusions remain reproducible, but this run
must not be cited as containing per-case GPU-active-time or peak-memory results.

## Artifacts

- Aggregate: `tmp/rq1_direct_rca_local_aggregate_summary.json`
- Return manifest: `tmp/rq1_direct_rca_return_manifest.jsonl`
- Manifest checksum sidecar: `tmp/rq1_direct_rca_return_manifest.sha256`
- Local adapter: `tmp/run_local_direct_rca.sh`

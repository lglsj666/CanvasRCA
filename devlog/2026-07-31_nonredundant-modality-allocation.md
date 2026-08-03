# 2026-07-31 — Nonredundant modality allocation

## Purpose

The formal equal-information RQ0 arm duplicated every dense image fact in text.
This exposed-development experiment tested whether the dashboard becomes useful
when it transports dense temporal/topology evidence rather than competing with
its complete textual duplicate.

## Implementation

- Added deterministic allocation serializers and representation audits in
  `vlmrca/rq0/evidence.py`.
- Added the frozen 24-case exposed-development roster, experiment configs,
  resumable runners, conversations, detailed/brief logs, token/GPU accounting,
  and combined analyzers.
- Used renderer v7, the project granularity-aware scorer, and the canonical
  unquantized BF16 vLLM recipe (`gpu_memory_utilization=0.65`).
- Excluded SFT heldouts and used no formal or reserve incident.

## D/A/B result

Both model smoke tests passed 9/9. The main experiment completed 144/144 calls
with parse rate 1.0 and no infrastructure failure or truncation.

| model | D allocated | A duplicated | B full text | D−B | D−A |
|---|---:|---:|---:|---:|---:|
| Qwen3.6-27B | 0.4806 | 0.4806 | 0.5097 | −0.0292 | 0.0000 |
| Gemma-4-26B-A4B-it | 0.5813 | 0.4958 | 0.4250 | +0.1563 | +0.0854 |

Gemma passed its single-model gate; Qwen failed, so the mandatory cross-model
gate failed and reserve remained closed.

## Decision

Do not open reserve or reinterpret RQ0. D−B changes both transport modality and
redundancy, so it cannot identify an image-presence effect. Any future modality
comparison must give every arm the same complete model-visible atomic facts.

No sudo, training, quantization, Git commit, or Git push was used.

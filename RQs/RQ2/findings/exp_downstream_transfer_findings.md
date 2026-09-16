# `exp_downstream_transfer` findings

Status: complete and verified. All 2,520 downstream-lock trajectories are
present, infrastructure error rate is 0, and parse rate is 0.9984.

## Main performance and cost

MRR is macro-averaged over the three headline datasets. `T_FULL` is the full
natural-language baseline; `S_FULL` is the same text rendered as pixels; `V0`
is the inherited RQ1.1 dashboard; `D_STAR` is the selected RQ2 design; `C_STAR`
uses the selected 75%-diversity content; and `DENSE` uses expanded evidence.

| Arm | Qwen MRR | Gemma MRR | Qwen input tok. | Gemma input tok. |
|---|---:|---:|---:|---:|
| `T_FULL` | 0.3148 | 0.3389 | 12,018 | 13,349 |
| `S_FULL` | 0.2111 | 0.2093 | 12,814 | 2,751 |
| `V0` | 0.2519 | 0.2556 | 4,524 | 3,608 |
| `D_STAR` | 0.2593 | 0.2444 | 11,199 | 5,095 |
| `C_STAR_TEXT` | **0.3556** | 0.2944 | 9,329 | 10,343 |
| `C_STAR_COMPACT` | 0.3389 | 0.3204 | 9,314 | 10,335 |
| `C_STAR_CANVAS` | 0.2185 | 0.2111 | 11,199 | 5,095 |
| `DENSE_TEXT` | 0.3139 | 0.3426 | 20,133 | 22,419 |
| `DENSE_COMPACT` | 0.3398 | **0.3648** | 20,088 | 22,382 |
| `DENSE_CANVAS` | 0.2593 | 0.1889 | 11,199 | 5,095 |

The absolute token counts must not be compared directly across models because
their tokenizers and image processors differ. Within a model, visual inputs can
be much shorter than full text—especially `V0`—but that compression came with
lower MRR. Output lengths remained of the same order, so the dominant saving
was in the input representation rather than decoding.

## Registered paired comparisons

Against `T_FULL`, the pooled two-model effects were:

- `D_STAR`: −0.0750 MRR, adjusted p=0.116.
- `C_STAR_CANVAS`: −0.1120, adjusted p=0.00811.
- `S_FULL`: −0.1167, adjusted p=0.00811.
- `V0`: −0.0731, adjusted p=0.164.
- `C_STAR_TEXT`: −0.0019, adjusted p=1.0.
- `C_STAR_COMPACT`: +0.0028, adjusted p=1.0.
- `DENSE_COMPACT`: +0.0255, adjusted p=0.653.

Thus no visual arm met the registered +0.05 MRR improvement rule. The compact
typed-text controls essentially preserved accuracy relative to their prose
twins, while screenshots and canvases were worse. The non-semantic skin change
was small relative to `D_STAR` for each model, but stability of a weak design is
not evidence that the design is useful.

## Interpretation

The transfer test rejects a simple “pixels save tokens and therefore improve
RCA” story. Pixels can compress the receiver context, but the current visual
organization loses or obscures usable diagnostic signal. Compact text is the
stronger current efficiency direction: it preserves most ranking quality and
avoids OCR/chart-reading overhead. Adaptive dashboard research remains
motivated by case-level headroom, not by a successful fixed RQ2 dashboard.
# Abandoned / superseded by RQ2.1 — 2026-09-07

The historical numerical findings below are preserved. This experiment is no
longer executable or a successor-selection authority. See
[RQ2 retirement audit](exp_retirement_audit_findings.md) for validity limits,
known implementation pitfalls and generated-artifact retirement.

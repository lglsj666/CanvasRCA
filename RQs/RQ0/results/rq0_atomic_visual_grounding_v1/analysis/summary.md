# RQ0 atomic visual-grounding diagnostic

Scope: 12 development dashboards, seven multiple-choice pixel-reading
tasks per dashboard, with actual-image, same-dataset swapped-image, and
no-image controls. This is nonconfirmatory and does not alter RQ0.

| model | actual | swapped | no image | actual (control-valid) | swapped | no image |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.6-27b | 85.7% | 36.9% | 34.5% | 83.3% | 29.2% | 23.6% |
| gemma-4-26b-a4b | 64.3% | 36.9% | 28.6% | 61.1% | 30.6% | 16.7% |

`metric_pattern` is excluded from the control-valid columns because all
12 answer keys are `increase`; the no-image condition reaches 100% for
Qwen and Gemma. It is a failed diagnostic control, not visual evidence.

## Actual-image accuracy by category

| category | Qwen | Gemma | interpretation |
|---|---:|---:|---|
| metric_identity | 100.0% | 75.0% | service/panel linkage is readable |
| metric_pattern | 100.0% | 83.3% | invalid as evidence: degenerate answer key |
| table_log | 83.3% | 66.7% | log table mostly readable |
| table_trace | 91.7% | 50.0% | Qwen strong; Gemma partial |
| topology_edge | 25.0% | 8.3% | not grounded; at/below four-choice chance |
| topology_order | 100.0% | 91.7% | ordered propagation rows are readable |
| topology_time | 100.0% | 75.0% | onset labels are readable |

## Decision

The models can read most atomic facts from the dashboard, so a broad
visual-perception deficit is not the main explanation for RQ0. The shared
perception defect is the faint curved call-edge encoding. Combined with
the formal discordance audit—where the image often pulls the prediction
to propagation row 1—the immediate bottlenecks are topology-edge
legibility and causal/salience integration.

Do not start broad visual-grounding SFT yet. First redesign only the
development topology primitive and rerun this atomic edge control. If
edge grounding becomes reliably above its swapped/no-image controls,
the next learning intervention should target cause-versus-propagated
symptom integration (case-level RCA SFT), not generic OCR/chart reading.

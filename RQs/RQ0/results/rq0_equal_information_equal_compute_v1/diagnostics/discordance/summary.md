# RQ0 A/B discordance audit

This is a descriptive post-hoc diagnostic. Ground truth was used only to
assign correctness groups; the case-level audit roster contains no label or
fault type and was not used to modify the formal experiment.

| model | top-1 changed | B correct/A wrong | A correct/B wrong | both wrong |
|---|---:|---:|---:|---:|
| qwen3.6-27b | 153/720 (21.2%) | 36 | 20 | 468 |
| gemma-4-26b-a4b | 158/720 (21.9%) | 33 | 22 | 482 |

## Salience signatures when the image breaks a text-correct answer

Fractions below describe the new A top-1 target among cases where B was
top-1 correct and A was wrong. Rank-1 fields are derived from the frozen
CEB; they are not causal attributions.

| model | metric #1 | onset #1 | severity #1 | log #1 | trace #1 | drawn-edge endpoint |
|---|---:|---:|---:|---:|---:|---:|
| qwen3.6-27b | 11.1% | 41.7% | 41.7% | 2.8% | 0.0% | 13.9% |
| gemma-4-26b-a4b | 12.5% | 75.0% | 75.0% | 6.2% | 0.0% | 37.5% |

Machine-readable aggregates and the label-omitting case roster are in
`discordance_audit.json`. These patterns are hypothesis-generating only.

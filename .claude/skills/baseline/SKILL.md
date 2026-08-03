---
name: baseline
description: Manage cross-method comparison tables — import the prior project's baseline numbers, append VLM rows, ensure token-fair accounting. Use when building or updating the headline results table, or comparing VLM results against text-based or classical RCA methods.
---

# Baselines and the headline table

The prior text-based project already evaluated every comparator on the same
datasets. Those numbers are **imported, not recomputed** — rerunning them would
burn budget and risk producing figures that differ from the published ones.

## Prior numbers (pooled MRR, from upstream `paper/tables/tab1_headline.md`)

| Method | Paradigm | Pooled MRR | tok/case |
|---|---|---|---|
| OpenRCA | multi-turn agent | 0.061 | 461,985 |
| Flow-of-Action | multi-turn structured | 0.559 | 3,743 |
| LocaleXpert | one-shot | 0.475 | 18,574 |
| Qwen3.5-9B + M+T+L | one-shot text | 0.605 | 11,386 |
| Claude-Opus-4.7 + B4 CoVe-lite | one-shot text | **0.706** | 12,670 |

Per-dataset MRR for the SOTA row: AegisLab 0.679 · AIOps-22 0.532 ·
AIOps-25 0.390 · RE2-OB 0.994 · RE2-TT 0.994.

**RE2-OB and RE2-TT are saturated.** Any VLM result there near 1.0 is not
evidence of an improvement. The datasets that discriminate are AegisLab,
AIOPS-2022 and AIOPS-2025.

## Appending VLM rows

Write to `paper/tables/tab1_headline_vlm.md`, marking imported rows
"prior project" and keeping identical columns: pooled MRR, Top@1/3/5,
per-dataset MRR, tokens/case, wall-clock.

## Token fairness

This is the one place a VLM comparison can quietly cheat.

- **Image tokens count.** A dashboard at 1568px is ~1.2k input tokens on
  Anthropic; omitting that makes the method look cheaper than it is. The client
  reports provider-counted `input_tokens`, which already include images — use
  those, do not recount text separately.
- **Multi-turn totals are summed across turns**, matching how upstream charged
  OpenRCA its 462k tokens/case.
- Report wall-clock as well; self-hosted models have no dollar cost but do have
  GPU-hours.

---
name: baseline
description: Build and audit CanvasRCA comparison tables against text, structured, visual, and prior RCA baselines. Use when preparing headline results, checking comparability, or reporting accuracy, efficiency, and modality effects.
---

# Baseline comparisons

Read `Codex.md`, the target RQ protocol, and each artifact's status authority.
Do not copy remembered numbers into a paper table.

## Qualification

For every row, record the source artifact, commit, roster/split, scorer,
checkpoint, prompt/evidence contract, decoding configuration, and status.
Compare rows only when the registered claim permits it.

- Require paired cases for arm comparisons.
- Require the same incident-specific atomic facts for modality or
  representation comparisons.
- Preserve candidate order, temporal resolution, topology edges, missingness,
  legends, and output schema across arms.
- Treat pilot, smoke, diagnostic, invalid, superseded, and incomplete rows only
  within their documented evidentiary scope.
- Do not use a historical result merely because its summary file exists.

If a prior-project baseline cannot be traced to a frozen artifact and scorer,
mark it unverified rather than presenting it as published ground truth.

## Reporting

Write RQ-specific tables and interpretation under `RQs/<rq>/findings/` after
the RQ is complete. Keep intermediate analyses under that RQ's result root.

Report at least:

- MRR and AC@1/3/5, plus AVG@3/5 where registered;
- per-dataset and per-fault results;
- paired delta, registered Wilcoxon test, and paired effect size;
- parse, truncation, model-error, and infrastructure-exclusion rates;
- text, image, input, and output tokens according to the recorded backend
  accounting definition;
- wall time and GPU active time when available.

Do not assume a provider's aggregate input token field includes image tokens;
verify the contract. Do not report confidence intervals under the current
project convention. Keep accuracy and efficiency as separate result axes.

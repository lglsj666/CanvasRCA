# `exp_tool_representation` findings

> **Abandoned / superseded by RQ2.1 (2026-09-07).** Numerical history below is
> retained verbatim. The profiles supplied identical inputs: their comparison
> does **not** identify selection-policy effects. See
> [retirement audit](exp_retirement_audit_findings.md) for the corrected scope.

Status: complete and verified. All 7,680 trajectories are present,
infrastructure error rate is 0, and parse rate is 0.9979.

## What was tested

Four deterministic evidence-selection profiles were crossed with equal-fact
Text and Canvas transports:

- `SIRCL_STAR_FUSED`: the inherited balanced M→R→L→G evidence tool.
- `MET_R_ADAPT`: emphasizes metrics and trace evidence.
- `LOG_T_ADAPT`: emphasizes logs and topology.
- `TRC_G_ADAPT`: emphasizes trace/topology structure.

Within a profile, Canvas minus Text isolates representation. Between profiles,
the selected evidence changes intentionally and measures the tool policy.

## Headline MRR

| Model | Profile | Text | Canvas | Canvas − Text |
|---|---|---:|---:|---:|
| Gemma | SIRCL* fused | 0.2682 | 0.2367 | −0.0315 |
| Gemma | Metrics/trace | 0.2682 | 0.2400 | −0.0282 |
| Gemma | Logs/topology | 0.2732 | 0.2400 | −0.0332 |
| Gemma | Trace/graph | 0.2598 | 0.2400 | −0.0198 |
| Qwen | SIRCL* fused | 0.2728 | 0.2372 | −0.0356 |
| Qwen | Metrics/trace | 0.2669 | 0.2417 | −0.0252 |
| Qwen | Logs/topology | 0.2736 | 0.2394 | −0.0342 |
| Qwen | Trace/graph | 0.2694 | 0.2394 | −0.0300 |

These values use AegisLab and the two AIOPS datasets. RE2 is reported only as a
saturated reference and must not inflate the headline conclusion.

All profile-versus-fused effects were tiny (absolute mean ΔMRR below 0.004) and
all Holm-adjusted p-values were 1.0. Tool×representation interactions were also
small and non-significant. On the saturated RE2 sets, Canvas losses were much
larger, reinforcing that those sets are pipeline checks rather than evidence
for a visual advantage.

Input-token cost was model-specific. On headline cases, Gemma Canvas averaged
about 5,095 tokens versus 6,092 for Text, whereas Qwen Canvas averaged 11,199
versus 5,551 for Text. This is a processor/tokenizer property, not a difference
in visible facts.

## Interpretation

None of the tested deterministic tool profiles materially improved one-stage
RCA, and no tool choice rescued the current Canvas representation. The result
narrows the next question: gains are unlikely to come from choosing one of
these four fixed selectors globally. A learned or case-conditional selector
would need out-of-sample evidence that it predicts which facts and visual form
help a particular incident.

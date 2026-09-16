# `exp_content_budget_twins` findings

Status: complete and verified. The experiment contains 10,800 independent-set
trajectories, with zero infrastructure errors and a 0.9972 parse rate.

## What was tested

Each content policy chose a fraction and selection rule for public telemetry
facts. Its `TextTwin` and `CanvasTwin` contained the same selected facts. At
50% budget, `blank` left removed space empty while `reflow` enlarged/repacked
the remaining cards; this separates information removal from layout reuse.
`DENSE_M24` intentionally contains more metric evidence than `FULL`, but its
own Text/Canvas twins remain equal-information.

The preregistered selector chose `B75_DIVERSITY` as `C*`: it retained a
diverse 75% evidence budget, had combined Canvas macro MRR 0.2317, and its
worst model×dataset change from FULL was −0.040, inside the −0.05 material-harm
boundary. `B75_SALIENCE` was almost tied at 0.2311. Lower budgets did not meet
the registered cross-model/cross-dataset safeguard.

## Canvas versus equal-fact text

Every policy's Canvas-minus-Text mean MRR was negative. Important pooled
paired contrasts over both models are:

| Content policy | Canvas − Text MRR | Holm-adjusted p |
|---|---:|---:|
| `FULL` | −0.0990 | 0.00523 |
| `B75_DIVERSITY` (`C*`) | −0.0743 | 0.02805 |
| `DENSE_M24` | −0.1262 | 0.000276 |
| `B50_DIVERSITY`, reflow | −0.1044 | 0.00523 |

Reflow-minus-blank effects at 50% budget were close to zero and non-significant
(for example, −0.0086 for diversity, adjusted p=1.0). Merely giving surviving
cards more screen space therefore did not recover the representation loss.

The fixed-resolution Canvas conditions also did not reliably reduce processor
token cost when facts were removed: image tokenization is driven mainly by
canvas geometry. This is why `C*` was selected primarily by the registered
accuracy safeguard rather than by a large realized visual-token reduction.

## Interpretation

Aggressive removal is unsafe, and the present dashboard renderer does not turn
the same evidence into a better RCA representation than natural-language text.
The useful signal is instead that evidence selection is case-dependent and
that dense text can exploit additional facts without the same visual penalty.
Future selection work must optimize content and representation jointly rather
than assuming that freed canvas area is automatically valuable.
# Abandoned / superseded by RQ2.1 — 2026-09-07

The historical numerical findings below are preserved. This experiment is no
longer executable or a successor-selection authority. See
[RQ2 retirement audit](exp_retirement_audit_findings.md) for validity limits,
known implementation pitfalls and generated-artifact retirement.

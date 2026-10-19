# C39: trace_joint.complete_marginals

RQ4.5 needs to transfer an entire frozen request-pair source out of diagnostic text. C20 (`trace_joint.marginals`) does not carry exact sample pairing, thresholds, binary counts, quantiles or conditional summaries. C39 is an opt-in extension; C19/C20 inputs, field bindings and drawing behavior remain unchanged.

The `trace_joint` DTO accepts `complete: CompleteMarginalsV1` only with C39; other components reject that payload. The object contains original lexical numeric strings, sample references, thresholds and phase statistics. Positions are computed from the original finite numbers while visible labels preserve spelling. Sample rows join parent and child endpoints; two phase columns show source distributions without fabricating time paths. Quantile glyphs and joint-count cells distinguish statistics from sampled observations. A conditional statistic absent from source remains null in audit and is not marked as missing on the image.

`complete_marginals.py` validates counts, numeric lexemes, phase order, paired labels and explicit per-statistic bindings. `CompleteMarginals.tsx` paints all non-null bound fields. Renderer-level overflow/binding checks and source-view DOM audits remain required. Registration/typechecking is not visual qualification; no new rendering has been run for this delivery.

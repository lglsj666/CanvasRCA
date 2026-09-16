# Round 16: candidate-bound evidence cards

**Status:** registered implementation; no model call is permitted before the
full static, gallery, prompt, leakage, visual and cohort audits pass.

Round 16 keeps the round-10 resource-family evidence selection, one-image
transport, frozen RCA task, candidate order, prompt structure, model recipes
and scorer. It changes only the grouping of already selected public evidence.
Selected M/R/L rows owned by the same anonymous candidate are placed in one
card whose heading states its public type and numeric ID, for example
`SERVICE 123`, `NODE 1234` or `POD 12345`. Remaining facts stay in explicit
`OTHER M/R/L/G` cards, so no selected fact is discarded. The complete directed
topology remains visible in G.

Owner ranking is deterministic and label blind: more represented modalities,
then more selected facts, then numeric identity. At most eight owner cards are
formed so that all residual modality cards still fit the registered twelve-card
renderer limit. This is a representation/binding intervention, not a new
selector and not a candidate root score. Every still-unretired case is included
independently for Qwen and Gemma.

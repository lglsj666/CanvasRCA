# Pre-inference visual review

Reviewed with the actual PNG viewer, not just manifests: both VIS_JOINT and
VIS_SEPARATE for INC-7247EFC5F392, INC-94EB4C70EFB7 and INC-34562D2C5CC4;
additional peer-group VIS_JOINT for INC-253A865B0CF8. Read each smoke case's
public input part headings, comparison membership and retained complete fact
block; verified candidate/context preservation by CPU fact-line counters.

Findings: labels and readings are legible at native1800×1272; no observed
clipping, hidden card or swapped entity. Two visual conditions use identical
card content/area; each group becomes a vertically aligned column versus
row-major slots. Single-group cases deliberately leave half the canvas blank
under the fixed-slot control. The group may still have adjacent members in
the separated condition; the manipulation is column alignment, not a promise
that every pair has a larger Euclidean separation.

Gapped metric samples use the existing per-bin bars; nulls are not fabricated
zeros or connected across a missing segment. Independent y scales remain,
and same-unit raw magnitudes should not be inferred from cross-panel bar
heights alone. Full-precision readings remain in text. Trace panels have their
own reference/current summary meaning, not the Metrics time grid. This is
not a causal graph or a new assertion that a largest anomaly is the source.

Qualification passes for this scoped four-condition pilot. No accuracy or
mechanism claim follows. Existing renderer components and operations were
not edited or deleted in this implementation; pre-existing dirty-worktree
changes are preserved. Do not claim all historical renderer files match Git
HEAD merely because this pilot did not modify them.

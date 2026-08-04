# RQ1b2 post-hoc failure analysis v1

## Status and scope

This is a bounded, descriptive analysis of the already exposed, valid-but-
failed Gemma development cell. It was performed after the registered decision
was known. It may explain failure and motivate a separately registered
successor, but it cannot change DD-29, select a confirmatory subgroup, or
authorize Qwen/the 150-case gate.

The analysis inspects the 80 high-complexity temporal tasks. It compares exact
T/V/H predictions with the evaluator-private answer and deterministically
derives only the following descriptive properties from the same 16-bin facts:
valid sustained onset, any single-bin threshold crossing, render-row position,
answer cardinality, number of threshold cells, and number of singleton-spike
panels. No root-cause label, fault type, injection time, private case ID, or
heldout incident is used or reported.

## Registered result being explained

```text
high temporal V−T:                 −0.3250
V / T accuracy:                     0.1625 / 0.4875
V repairs / breaks relative to T:   4 / 30
paired high-minus-low interaction:  0.0000
```

## Image-only failure modes

| Diagnostic | Count / 80 | Interpretation |
|---|---:|---|
| V exact correct | 13 (16.3%) | Reproduces the registered V accuracy |
| V returns one panel | 58 (72.5%) | Gold is singleton in only 45 cases (56.2%) |
| V under-selects the tied answer | 23 (28.7%) | Multi-panel ties are often collapsed |
| V selects at least one panel with no valid sustained onset | 25 (31.2%) | A salient crossing is often mistaken for a two-bin same-sign run |
| V returns a singleton panel that has a crossing but no sustained onset | 15 (18.8%) | Direct evidence of singleton-spike capture |
| V includes the top rendered row | 30 (37.5%) | Gold includes that row in only 15 cases (18.8%) |
| V exactly matches the earliest *single-bin* threshold set | 11 (13.8%) | Ignoring the consecutive rule alone does not explain most errors |
| V emits a non-panel string | 1 (1.3%) | Rare OCR/schema-content contamination despite valid JSON |

The row-position diagnostic is not proof of a causal position effect because
row order was not experimentally randomized. It is a two-fold descriptive
imbalance that warrants a preregistered order intervention rather than an
immediate renderer claim.

### Representative break

In `INC-036C59EBD461 / Q-34114443695004FB`, the answer is `M7`. M7 contains
three consecutive positive threshold cells at bins 8–10. V instead returns
`M12`, which has one visually intense `99.9` cell at bin 8 but no second
same-sign threshold cell. T and H both return M7. The image and text contain
the same 12×16 values, and the public question explicitly requires two
consecutive observed bins with matching sign. This is therefore a composition/
selection failure, not missing information.

### Representative repair

In `INC-4F29C8F83691 / Q-81FB1371FD9620F3`, M12 has the earliest valid pair at
bins 9–10; later valid pairs appear at bins 13–14. V and H return M12, while T
returns the later pair. The connected red block is perceptually clear, showing
that the visual encoding can sometimes expose temporal continuity. Four such
V-over-T repairs are nevertheless outweighed by 30 breaks.

## Hybrid versus text diagnosis

On the same high-complexity tasks, H repaired eight T errors and broke nine
T-correct answers. H−T is therefore −0.0125. The categories are:

```text
both correct: 30
both wrong:   33
H repairs T:   8
H breaks T:    9
```

Seven of the eight repairs occur in AIOPS-2022, whereas breaks occur in all
three datasets. This is not a registered dataset interaction and must not be
used to claim a dataset-specific visual benefit.

Exploratory feature bins are likewise unstable and small. For example, cases
with at most 20 threshold cells have four H repairs and one break, while cases
with 41 or more have one repair and five breaks. Cases with at most five unique
services have four repairs and one break. These patterns suggest visual clutter
as a candidate modifier, but each was examined after outcomes and none is an
eligible router or efficacy result.

## Supported diagnosis

1. The renderer is readable for exact lookup, so the failure is not total image
   blindness.
2. Direct image-only composition is vulnerable to singleton-spike salience,
   row-position bias, and tied-answer under-selection.
3. H occasionally repairs text when a valid run is visually distinct, but the
   direct one-step prompt does not reliably connect visual threshold runs to
   the final set-valued answer.
4. No observed post-hoc subgroup is strong or independent enough to rescue
   DD-28 or to justify opening its gate.

## Implication for a successor

A scientifically distinct successor should test the failure mechanism rather
than merely rerun the same task. The smallest defensible candidate is a
fact-equal, two-stage compositional agent:

1. stage 1 records a complete per-panel onset ledger (including `null`) from
   the arm's representation;
2. stage 2 selects the minimum onset and all ties from that frozen ledger;
3. T/V/H remain mandatory, H remains exact image-first `A+B`, and H−T—not
   image-only replacement—is the primary visual-increment estimand;
4. numeric row order versus deterministic shuffled row order is crossed as a
   registered causal position check;
5. image-only remains a mandatory secondary arm, and visual influence is
   reported separately from accuracy.

This proposal is not registered by this artifact. It requires a new protocol,
disjoint exposed development roster, power analysis, renderer qualification,
and decision entry before any model call.

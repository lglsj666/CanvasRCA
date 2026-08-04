# RQ1b3 post-hoc failure analysis — Gemma exposed development

**Role:** bounded descriptive diagnosis only  
**Registered efficacy result:** unchanged (`valid_failed`)  
**Scope:** 90 exposed incidents; no subgroup or confirmatory claim

## 1. Registered outcome

All 990 registered calls completed: 270 main Stage 1, 360 main Stage 2
(including oracle), 180 row-sham Stage 1, and 180 row-sham Stage 2. There were
no infrastructure failures, truncations, or paired incident exclusions.

The registered analysis failed every promotion requirement:

| Requirement | Frozen threshold | Observed | Pass |
|---|---:|---:|:---:|
| Final H−T exact-set accuracy | at least +0.05 | −0.0333 | no |
| Stage-1 panel-macro H−T | at least +0.05 | −0.0028 | no |
| H repairs > breaks | strict positive net | 10 vs 13 | no |
| H ledger error < T | strict reduction | 0.0774 vs 0.0668 | no |
| Oracle Stage-2 accuracy | at least 0.95 | 0.8000 | no |
| All integrity gates | all pass | Stage-2 parse below 0.95 | no |

Registered final accuracy was T=0.6222, H=0.5889, and V=0.1667. Registered
Stage-1 panel-macro accuracy was T=0.8944, H=0.8917, and V=0.5083. The
diagnostic paired Pratt-Wilcoxon result for final H−T was p=0.5316; no p-value
was a development promotion gate.

## 2. Stage-2 parse failures are an ordering-contract mismatch

Every Stage-2 response was complete JSON and no response reached the output
limit. The strict parser nevertheless rejected 21/360 main and 13/180 sham
responses because it required Python lexicographic list order. With panel IDs,
that convention puts `M10` before `M6`. Gemma often returned the semantically
natural numeric order `M6,M8,M9,M10,M11,M12`.

Main-condition order-only failures were H=4, T=3, V=9, and oracle=5. A
representative oracle response is preserved at
`gemma/main_stage2/calls/13bba1d85daf5f1bba7c8fb5.json`: it returned the
correct set in natural numeric order but was registered as `parse_ok=false`.
This is an avoidable interface convention, not malformed JSON, truncation, an
infrastructure failure, or evidence that the model lacked the correct set.

The registered result must not be rewritten. Future set-valued interfaces
should accept any duplicate-free array of allowed IDs and canonicalize it in
the evaluator, because array order is not part of set semantics.

## 3. Order-insensitive sensitivity analysis does not rescue the mechanism

For diagnosis only, each complete duplicate-free response was compared as a
set, without changing any stored call record. The results become:

| Arm | Registered correct | Set-correct sensitivity | Difference |
|---|---:|---:|---:|
| T | 56/90 | 58/90 | +2 |
| H | 53/90 | 56/90 | +3 |
| V | 15/90 | 17/90 | +2 |
| Oracle | 72/90 | 74/90 | +2 |

Thus forgiving the ordering convention changes H−T from −0.0333 to −0.0222,
still far below +0.05. H repairs/breaks become 10/12, still not positive. The
oracle rises only from 0.8000 to 0.8222, still far below 0.95. Therefore an
interface-only rerun cannot plausibly satisfy the registered mechanism gates.

## 4. Oracle failures show a downstream selection problem

After ignoring order, oracle Stage 2 has 74 correct sets and 16 substantive
selection failures:

- 12 mixed wrong sets;
- 2 false `__NO_VALID_SELECTION__` answers despite usable onsets;
- 1 under-selection;
- 1 over-selection.

Examples are preserved at:

- `gemma/main_stage2/calls/f2aee87a080020ad7dfe9a6f.json`: a parsed but
  substantively wrong oracle set;
- `gemma/main_stage2/calls/0c62e10f4f53ed84a775ae35.json`: an oracle call
  that incorrectly returned `__NO_VALID_SELECTION__`.

Stage 2 saw the evaluator-correct ledger in these oracle calls, so these errors
cannot be attributed to dashboard perception or Stage-1 evidence extraction.
The two-stage decomposition exposed a genuine selector-instruction failure.

## 5. The row sham confirms position sensitivity, not visual benefit

Changing only the complete row order altered the exact Stage-1 ledger heavily:
main/sham exact-ledger agreement was 0.4556 for H and 0.0556 for V. Final-answer
agreement was 0.6556 for H and 0.3000 for V. Sham-minus-main final accuracy was
−0.0222 for H and +0.0333 for V.

This establishes substantial arrangement sensitivity. It does not establish
that visual evidence is beneficial: H still failed both accuracy and ledger
increment gates, and the protocol forbids choosing the better row order after
observing outcomes.

## 6. Decision implication

RQ1b3 is a valid negative development result. Under its preregistered stopping
rule, Qwen and the unopened 150-case gate must not run. The ordering defect
should be corrected for future set-valued interfaces, but the order-insensitive
sensitivity analysis shows that rerunning this cell would be a rescue attempt,
not a scientifically justified mechanism test. RQ1c, RQ1d, training, reserve,
and heldout RCA remain blocked by the failed visual-complementarity gate.


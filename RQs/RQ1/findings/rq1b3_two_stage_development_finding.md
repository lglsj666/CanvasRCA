# RQ1b3 finding: an explicit onset ledger does not create visual increment

**Status:** accepted exposed-development finding; not a confirmatory or
heldout claim.

On 90 disjoint exposed incidents, Gemma completed the full registered RQ1b3
two-stage T/V/H experiment and row-order sham with 990 calls, zero
infrastructure failures, zero truncations, and zero paired exclusions.

The two-stage decomposition did not make the current dashboard useful as an
increment to complete text:

- final accuracy: T=0.6222, H=0.5889, V=0.1667;
- final H−T=−0.0333 versus the +0.05 promotion threshold;
- Stage-1 panel accuracy: T=0.8944, H=0.8917, V=0.5083;
- Stage-1 H−T=−0.0028 versus the +0.05 threshold;
- H repairs/breaks=10/13;
- normalized ledger error H=0.0774 versus T=0.0668;
- oracle Stage-2 accuracy=0.8000 versus the 0.95 interface threshold.

All six registered gates failed. Row permutation strongly changed visual
ledgers and final answers, establishing arrangement sensitivity, but did not
establish beneficial visual use. A strict lexicographic-order parse convention
also rejected some semantically correct sets; an order-insensitive sensitivity
analysis still leaves H−T negative and oracle accuracy below threshold.

Therefore RQ1b3 stops before Qwen and the 150-case independent gate. Together
with the prior RQ1b and RQ1b2 failures, the current visual-operation
complementarity premise has not earned RQ1c, RQ1d, training, or heldout RCA.
The next defensible question is which dashboard content, encoding, and
arrangement choices causally help or harm, registered separately as RQ2.

Authoritative evidence:

- `results/rq1b3_two_stage_development_v3/analysis/analysis_v1.json`;
- `results/rq1b3_two_stage_development_v3/analysis/failure_analysis_v1.md`;
- DD-34 in `plans/design_decisions.md`.

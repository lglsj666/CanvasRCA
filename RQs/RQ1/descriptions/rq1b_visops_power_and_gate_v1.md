# RQ1b RCA-VisOps mapping and independent gate — frozen v1

## Purpose

RQ1b first asks whether representation utility is operation-dependent.  It does
not reuse the same cases both to discover a routing rule and to validate that
rule.  All cases in this stage were already exposed by the completed RQ0 formal
run; no untouched heldout or reserve case is opened.

## Outcome-blind split

The project-history-complete exposure ledger is frozen before preparation.  For
each of AegisLab, AIOPS-2022, and AIOPS-2025, eligible cases from the old RQ0
formal roster are ordered without reading model outcomes:

```text
mapping: SHA256("42:rq1b:mapping:<dataset>:<private_case_id>"), first 30
gate:    remove mapping, then
         SHA256("42:rq1b:gate:<dataset>:<private_case_id>"), first 30
```

This yields 90 mapping cases and 90 disjoint gate cases.  Cases containing any
`.invalid` marker are ineligible.  RE2-TT remains embargoed, and RE2-OB remains
infrastructure-only.

## Power boundary

The inferential unit is the opaque incident.  Query scores are averaged within
incident before paired tests.  With 90 paired cases, two-sided alpha 0.05 and
80% power, the normal approximation gives:

```text
MDE = (1.96 + 0.84) × paired_sd / sqrt(90)
```

The previously observed representation-effect SD of 0.36 implies an MDE of
approximately 0.106 case-macro accuracy.  A conservative bounded-score SD of
0.50 implies approximately 0.148.  Therefore effects below 0.10 that do not
reach significance are described as inconclusive, not absent.  The mapping
cell is for rule discovery and descriptive mechanism analysis; only the
independent gate evaluates the frozen operation router.

## Frozen mapping rule

For Gemma, calculate mapping-set accuracy separately for every registered
operation and arm `T`, `V`, and `H`.  Select exactly one arm per operation using
the highest mapping accuracy.  Exact ties use the cost-aware fixed order
`T > V > H`, avoiding a redundant hybrid when it provides no accuracy gain.
The complete operation-to-arm mapping, mapping accuracies, and source analysis
hash are frozen before gate inference is started.  Qwen uses the same mapping
learned from Gemma; it is an architecture-interaction control and must not get
an independently optimized router.

## Independent gate

The RCA-VisOps complementarity gate passes for the primary Gemma architecture
only when all of the following hold on the 90 disjoint gate cases:

1. At least one preregistered structural operation from temporal scanning,
   topology/path, or cross-modal alignment was assigned to `V` or `H` by the
   mapping rule, and the pooled routed-versus-`T` case-macro delta over those
   operations is at least `+0.10`, with paired Wilcoxon Pratt `p < 0.05`.
2. The routed-versus-`T` structural delta is positive in at least two of the
   three datasets, and no dataset has a delta at or below `-0.10`.
3. Across exact-lookup negative controls, `T` is not worse than `V` by more than
   `0.05`; this prevents interpreting a universally superior arm as evidence of
   operation-dependent complementarity.
4. The frozen routed policy exceeds the best single fixed arm among `T`, `V`,
   and `H` by at least `+0.05` case-macro accuracy, with paired Wilcoxon Pratt
   `p < 0.05`.
5. All parity, leakage, parse-rate, truncation, pairing, and whole-case
   infrastructure gates pass.  Infrastructure exclusion above 5% makes the
   cell incomplete; parse failures and truncations remain model outcomes.

Passing this development gate authorizes the registered RQ1b modality
factorial.  It is not itself a fresh-heldout efficacy claim.  A positive Qwen
replication supports cross-architecture operation complementarity; a negative
Qwen result leaves any conclusion Gemma-specific and is reported rather than
used to alter the mapping.

## Execution order

1. qualify and freeze the mapping artifacts;
2. run the registered three-case inference smoke;
3. run all `T/V/H` mapping calls for Gemma in balanced incident-level arm order;
4. run the same complete mapping cell for Qwen;
5. analyze without altering artifacts and freeze the Gemma mapping rule;
6. prepare the already locked disjoint gate roster;
7. run Gemma and Qwen gate cells in the same order and apply the rules above.

Partial results are operational health information only.  They must not be used
to change prompts, task eligibility, case membership, renderer behavior, or
stopping decisions.

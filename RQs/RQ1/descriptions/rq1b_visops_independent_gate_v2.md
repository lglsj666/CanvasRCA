# RQ1b RCA-VisOps independent gate v2

**Date:** 2026-08-04  
**Status:** registered; preparation and inference authorized by DD-26, subject
to qualification, code freeze, smoke, and runtime attestation

## Purpose

This cell is the independent test of the operation router selected on RQ1b
mapping v2. It uses the 90 already locked, already-exposed gate incidents that
are disjoint from the 90 mapping incidents. It does not open heldout, reserve,
RE2-TT, or training data.

The gate repeats complete T/V/H inference. The routed policy is then assembled
offline by selecting the frozen arm for each operation; it is not a fourth
model call. This preserves paired fixed-arm controls and makes every routed
answer auditable against the exact source call.

## Frozen router

The router was generated deterministically from the valid Gemma mapping-v2
analysis before any gate incident was prepared:

```text
source analysis:
RQs/RQ1/results/rq1b_visops_mapping_v2/analysis/paired_analysis_v3.json
SHA256 ac14861f85c4be16606e402e611e44babe1cacf5dd54d027fd98038c2b259f2e

router:
RQs/RQ1/results/rq1b_visops_mapping_v2/contracts/frozen_operation_router_v1.json
file SHA256 59a0a25005f7bdc75d785f5a2a344f767e3b693eaa7633f861d3d9e6ba0f6121
contract SHA256 0dc7459e489c1f22446247566f5105c858c30c0f2eaf44b96db0c55fcbc2a427
```

| Operation | Routed arm |
|---|---|
| `earliest_onset` | H |
| `entity_modality_alignment` | V |
| all other registered operations | T |

Qwen uses this exact Gemma-derived mapping. Re-optimizing by architecture,
dataset, case, or observed gate outcome is forbidden.

## Inherited representation and runtime contract

- T is complete text B, V is complete visual A, and H is exact ordered A+B.
- All arms expose the same atomic facts; no summary, edge, timestamp, entity,
  missingness value, or instruction may be available to only one arm.
- The type-specific JSON-v2 prompt, response schema, renderer, scorer, task
  eligibility, private answer derivation, and arm-order policy are unchanged
  from mapping v2.
- Gemma runs first, followed by Qwen. Both use unquantized BF16, vLLM 0.24.0,
  32,768 context, 16,384 output ceiling, temperature 0, top-p 1, seed 42,
  thinking off, and `gpu_memory_utilization=0.65`.
- Partial results may be inspected only for operational health. They cannot
  change the router, prompts, cases, tasks, renderer, stopping rule, or scorer.
- Before the first generation call, live-tokenizer context preflight is applied
  to every frozen prompt. If any query/arm exceeds the fixed 32,768-token
  context when combined with the fixed 16,384-token output ceiling, that
  incident's complete T/V/H query set is recorded as a paired infrastructure
  exclusion without replacement. The run remains complete only while this
  label-blind exclusion fraction is at most the preregistered 5% ceiling.

## Acceptance rules

The primary Gemma gate passes only if every frozen requirement in
`rq1b_visops_power_and_gate_v1.md` holds:

1. On structural operations assigned V or H, routed minus T case-macro
   accuracy is at least +0.10 with two-sided Pratt-Wilcoxon p<0.05.
2. The structural effect is positive in at least two of three datasets and no
   dataset is at or below -0.10.
3. Across exact-lookup negative controls, T is not worse than V by more than
   0.05.
4. Routed exceeds the best fixed arm among T/V/H by at least +0.05 with
   two-sided Pratt-Wilcoxon p<0.05.
5. Every parity, leakage, pairing, parse, truncation, accounting, and
   infrastructure gate passes. Parse rate must be at least 0.95 per arm; more
   than 5% whole-incident infrastructure exclusion makes the model cell
   incomplete.

The primary inferential unit is the opaque incident. Queries are averaged
within incident before testing. Query-level results are descriptive only.
Confidence intervals are not reported under the current project rule.

Passing authorizes the registered RQ1b modality factorial; it is not a fresh
heldout RCA claim. Failure blocks RQ1c/RQ1d and must not be repaired by tuning
on these gate cases.

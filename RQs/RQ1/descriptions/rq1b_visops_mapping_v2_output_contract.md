# RQ1b RCA-VisOps mapping v2 — structured-output repair

**Date:** 2026-08-04  
**Status:** registered; inference blocked until implementation tests, artifact
qualification, and partition-aware smoke pass

## Purpose and scope

Mapping v1 is preserved as an incomplete diagnostic cell. It completed all
registered calls, but the primary Gemma architecture failed the frozen 0.95
parse-rate gate. V2 repairs only the answer transport contract; it does not
change the research question, evidence, task truth, renderer, cases, arms,
model order, checkpoints, inference opportunity, or statistical rules.

V2 uses the same 90 already-exposed mapping incidents and must not open the
disjoint gate roster, heldout data, reserve data, or RE2-TT. Mapping v1 outputs
must not be reused as v2 outcomes.

## Frozen invariants inherited from v1

- `CanonicalEvidenceStoreV2WithDenseLogAndTraceTimeSlices` and every
  model-visible atomic fact remain identical.
- The nine operation eligibility rules and private answer derivations remain
  identical.
- T is complete text B, V is complete visual A, and H is exact ordered A+B.
- The prompt task/question, fact inventory, entity scope, candidate order,
  precision, units, missingness, edge direction, and relative-time semantics
  remain equal across arms.
- Renderer is `RQ1VisualViewV4`; all public/private artifact separation,
  leakage checks, location maps, and deterministic hashes remain binding.
- Gemma-4-26B-A4B-it remains the primary architecture; Qwen3.6-27B remains the
  mandatory architecture control. Gemma runs first, then Qwen.
- BF16, no quantization, 32,768 context, 16,384 output ceiling, temperature 0,
  top-p 1, seed 42, thinking off, eager execution, prefix caching off, chunked
  prefill off, and `gpu_memory_utilization=0.65` remain unchanged.
- The minimum parse rate is 0.95 per arm; whole-incident infrastructure
  exclusion remains capped at 5%. Parse failures and truncations remain model
  outcomes.

## V2 answer contract

The system prompt names the required JSON shape for the task's frozen private
answer type. The request also sends the matching OpenAI-compatible
`response_format={"type":"json_schema", ...}` to vLLM 0.24.0. The schema
requires one top-level object with exactly one property named `answer` and
forbids additional properties.

| Private answer type | Required model output |
|---|---|
| `number` | `{"answer": 1.25}` |
| `sorted_string_set` | `{"answer": ["service-a", "service-b"]}`; include every tie, with no prose inside an item |
| `ordered_path` | `{"answer": ["caller", "middle", "callee"]}` in caller-to-callee order |
| `directed_edge` | `{"answer": {"caller": "service-a", "callee": "service-b"}}` |

The schema constrains syntax and value type only. It does not reveal the
private answer, number of tied services, path length, service identity, or
correctness. Scoring remains the same deterministic numeric/set/path/edge
scorer. The 16,384-token ceiling remains recorded even though constrained
generation should normally terminate after the single object.

## Qualification and execution order

1. Add unit tests proving all four schemas reject extra top-level fields and
   that prompt A/B/H equality is unchanged.
2. Reprepare the same public/private mapping roster under a new experiment ID;
   all CEB/query/view hashes must match v1, while prompt/contract hashes must
   differ only where the answer-shape instruction and structured-output request
   are recorded.
3. Run the complete static parity, leakage, renderer, private-isolation, and
   deterministic recompilation qualifier.
4. Run partition-aware real-model smoke for Gemma and Qwen. Smoke must verify
   that vLLM accepts every answer schema and that the persisted request
   contract records its schema hash. Smoke accuracy is not a pass condition.
5. Run all 2,124 Gemma calls and then all 2,124 Qwen calls with no partial-result
   tuning or stopping decision.
6. Run the strict V3-or-later paired analyzer, including per-operation output.
   Do not freeze a router unless both model cells satisfy all registered
   integrity gates and Gemma satisfies the mapping prerequisite.

## Decision authority

This repair is adopted by DD-25 in `plans/design_decisions.md`. Lowering the
parse threshold, post-hoc lenient parsing of v1, selecting a Qwen-only router,
or opening the independent gate from v1 is forbidden.

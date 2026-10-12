# RQ4.1 uniform ranking-prefix decoder — 2026-10-07

The user explicitly authorizes a recipe change: “允许，即使改变配方也可以。”
This prospectively amends the RQ-local decoder for qualification. It does not
rewrite earlier experiments, the shared model recipe, or Codex.md. Formal
execution remains disabled.

## Registered change

Use `ranking_prefix_greedy_v25` for every matched RCA condition, including
strong text controls: from the first generated token through the closing
`services` array, choose the largest grammar-admitted logit. After that array,
retain temperature 1, top-p 0.95, top-k 0 sampling for reason and confidence.
The output limit is still 8192; context 40960; local BF16 Qwen and GPU memory
fraction 0.75 are unchanged. One generation call returns the entire answer.

The processor follows the static JSON grammar and precedes temperature/top-p.
Its only input is the generated token prefix and logits. It receives no incident
candidate strings, labels, lookup table, or previous answer. It does not repair
IDs or retry invalid rankings. The static numeric grammar admits all identifiers
in the existing public type domain; exact membership remains a host-side check.
The generated ranking itself changes decoding policy; this is not the former
sampled-ranking recipe. Earlier results cannot serve as matched decoder controls.

The frozen grammar emits `services` first. CPU checks verify that property order,
quoted closing brackets and escapes, exclusion of prompt text, greedy choice
after grammar masking, unchanged logits after release, and fail-closed batch and
configuration handling. The first qualification supports batch one only. A
batched deployment must be qualified separately. Record prefix length, release,
and processor wall time; do not infer no overhead from functional tests.

## Scope and fixed smoke

The fifth window of the user's five-window repair allowance runs 17 fresh calls,
with a shared 600-second clock and 18-call ceiling. No old answers are reused.
The same three registered eval identities are retained. Each runs V_FULL,
CVC_E50, protected SCOPE, protected S2Prune and T_FULL. Two fresh full-retention
SCOPE/S2Prune identities are compared with the new AIOPS-2022 V_FULL answer.
All 17 use the new decoder. No attention collection is added in this repair.

Use the shared protected anchors and original E50 K. The separately tested
inventory-rectangle experiment remains archived; it added no aggregate usability
improvement and is not required by this decoding intervention. The first three
prior repair windows and the rectangle window remain distinct failed variants.
Existing images, processor tensors, public facts and selection algorithms are
unchanged. Existing passed CPU qualifications remain valid for those components.

Require all committed actual-pruning answers to contain five distinct real
candidates, all matched controls to satisfy the same interface, exact retained
budgets/anchors, and both original numerical/output identity checks. Inspect
every persisted request, response, scoring and call record. Root ranking/MRR is
not a smoke gate. Missing or timed-out positions remain unqualified. Monitor
the launch for at least three minutes; preserve consumed windows and calls.

Prior initiated smoke calls: 110; separate historical model probes: 12. This
window adds at most 17. The total registered allocation ceiling remains 9,170
within the user's 12,000-call maximum. The older ten-window allowance remains
separate and is not reset.

After review, record qualified and unresolved paths explicitly. Attention-speed,
formal throughput/resource, and deployment batching gates remain separate. Do
not launch formal experiments under this repair authorization.

# RQ4.1 GPU supplement and speed review — 2026-10-07

The user authorizes continued GPU review and missing-path qualification. Formal execution remains disabled. Use the existing ten additional smoke windows: rounds 1–3 are consumed; rounds 4–5 below are registered prospectively, at most 18 initiated calls and 600 seconds each. Prior attempts and committed answers remain unchanged. The 12,000-call and 48 owned-device-hour ceilings remain in force. No whole-roster CPU or model replay, no extra datasets, and no MRR-based selection.

## Round 4: distinct prior paths

Use the same fixed AIOPS-2022, AIOPS-2025 and AegisLab cases and unchanged BASE PNGs/prompts/tensors. Reuse the committed AIOPS-2022 native greedy reference. Make two new full-retention greedy identity calls on that input: S2Prune's one-layer hybrid state adapter and SCOPE's real vision-signal observer plus pre-decoder gather. Their logits/tokens must pass the original tolerances. Then perform each prior's actual registered E50 selection and sampled generation on each of the three cases (six calls). Total: nine positions, eight new calls. Exact K, original MRoPE, consumed recurrent history, real saliency/ERC and source-image allocation are audited. No attention-proxy substitution and no external RCA repository imports.

## Round 5: separate speed effects

Six fresh calls per case, three cases, eighteen calls total. For each case: native full image (A), identity gather with measurement off (B), identity gather with measurement on (C), CVC_E50 with measurement off (D), the same CVC_E50 with measurement on (E), then native full image again (A2). All are greedy so equal-input observer comparisons must produce equal tokens and meet the registered logit tolerances. The second native call diagnoses temporal variation, not an accuracy repeat for the formal experiment. CVC selection is recomputed from the actual encoder every call; no feature/KV/answer reuse. Use the original complete generation limit, not shortened diagnostic answers.

Compare B against A/A2 for adapter cost, C against B for passive attention cost, E against D for attention on pruned input, and D/E against A/A2 for whole-method latency. Different output lengths preclude a pure algorithm-overhead interpretation of pruned versus native totals; report prefill/first-output, decode and output lengths as well. CUDA event elapsed spans include stream stalls and are not pure kernel active time. CPU selection, gather/copy, asynchronous capture and persistence remain recorded. These few samples cannot prove zero overhead; do not invent a post-hoc tolerance or equate a numerical pass with a speed pass.

## Implementation and acceptance

Wire the already CPU-qualified ScopeVisionSignal/scope_select and S2Prune hybrid generation into the smoke worker. Remove the accidental duplicate gather in the worker by passing the already prepared tensors to the same adapter, with targeted numerical tests. This changes redundant work only, not selection, positions, evidence or model recipe. Use genuine native SDPA when the passive observer is disabled; record observer GPU spans only for its two registered query reductions. New forward versions preserve all historical source snapshots.

Keep Qwen BF16, 40,960 context, 8,192 output, GPU fraction 0.75 and single-request execution. Every normal diagnostic answer, including invalid rankings, is committed once. Infrastructure errors are charged and classified explicitly. The smoke registry, conditional backend phases, exact expected slot set and expected parity pairs are frozen per window. Stop an unresolved failure; repair and rerun only affected incomplete infrastructure positions under a new authorized window.

Deliver a combined receipt distinguishing numerical correctness, prior-path coverage, attention storage/output invariance, speed evidence and formal resource feasibility. No formal experiment starts in this task. Codex.md remains unchanged.

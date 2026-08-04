# RQ1b independent-gate failure analysis

**Status:** descriptive post-hoc diagnosis on exposed data; the valid negative gate is unchanged.

## Main finding

The operation-only router was selected from small net discordances and did not generalize. Gemma's image-only alignment choice moved from +4 net repairs on mapping data to −8 on the disjoint gate. The image arm itself stayed near the same accuracy; text improved sharply on the gate, so the discovery advantage was mostly an unstable text deficit.

| Model | Operation | Mapping T | Mapping routed | Mapping net | Gate T | Gate routed | Gate net |
|---|---|---:|---:|---:|---:|---:|---:|
| gemma-4-26b-a4b | earliest_onset → H | 0.9815 | 1.0000 | +1 | 1.0000 | 1.0000 | +0 |
| gemma-4-26b-a4b | entity_modality_alignment → V | 0.8000 | 0.8444 | +4 | 0.9326 | 0.8427 | -8 |
| qwen3.6-27b | earliest_onset → H | 0.9630 | 0.9815 | +1 | 0.9636 | 1.0000 | +2 |
| qwen3.6-27b | entity_modality_alignment → V | 0.9333 | 0.8778 | -5 | 0.9205 | 0.8636 | -5 |

## Gate discordance diagnosis

- **gemma-4-26b-a4b:** entity-alignment V versus T produced 1 repairs, 9 breaks, and 79 ties. Visual breaks comprised 6 subset omission, 3 superset overinclusion; mean answer-set Jaccard was 0.514.
- **qwen3.6-27b:** entity-alignment V versus T produced 2 repairs, 7 breaks, and 79 ties. Visual breaks comprised 2 subset omission, 5 superset overinclusion; mean answer-set Jaccard was 0.375.

All visual breaks are classified as `perception`: the required row/column facts are visibly present, but the strict answer set does not match the row-wise modality maximum. The no-rationale structured output cannot distinguish low-level digit reading from downstream visual aggregation, so the narrower subtype records omission, overinclusion, or mixed substitution without inventing a hidden chain of thought.

Representative auditable cases:

- Gemma overinclusion: `INC-1DBF691A4568`; visual `RQs/RQ1/results/rq1b_visops_independent_gate_v2/prepared/INC-1DBF691A4568/public/Q-CD59F33CD3A20E45/visual_view.png`; text call `RQs/RQ1/results/rq1b_visops_independent_gate_v2/gemma/run/calls/2d41057213ab5efe1aceda43.json`; V call `RQs/RQ1/results/rq1b_visops_independent_gate_v2/gemma/run/calls/6f7031d70d206985a29d05d0.json`.
- Gemma omission: `INC-187FD47AF170`; visual `RQs/RQ1/results/rq1b_visops_independent_gate_v2/prepared/INC-187FD47AF170/public/Q-E77700DE60B6E46E/visual_view.png`; paired audit `RQs/RQ1/results/rq1b_visops_independent_gate_v2/prepared/INC-187FD47AF170/public/Q-E77700DE60B6E46E/paired_view_audit.json`.
- Qwen onset repair: `INC-6835C4E11B59`; visual `RQs/RQ1/results/rq1b_visops_independent_gate_v2/prepared/INC-6835C4E11B59/public/Q-5AA37A6E7829C0F3/visual_view.png`; T call `RQs/RQ1/results/rq1b_visops_independent_gate_v2/qwen/run/calls/b51e013d83efe2234ec66b6a.json`; H call `RQs/RQ1/results/rq1b_visops_independent_gate_v2/qwen/run/calls/93ee751187ce1f563784036f.json`.

## Interpretation boundaries

- This analysis does not refit the router, change gate status, or authorize heldout access.
- It supports mapping-selection variance plus visual set-aggregation errors; it does not prove images are universally useless.
- `earliest_onset -> H` remains a small Qwen-specific repair pattern but tied T on primary Gemma and is below the registered practical threshold.
- Any successor must use new development and independent-gate data; these gate cases are now exposed diagnostics.

JSON artifact SHA256: `2a479b0b1baf4000696024084a662082d4af6931467278fed40c7a0a7f23ad99`

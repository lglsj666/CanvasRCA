# 2026-07-31 — Preservation/correction SFT v2.1 did not improve RCA

The complete protocol and result are in
`docs/2026-07-31_causal_integration_sft_v2_1_results.md`.

## Work completed

- Added five-service preservation/correction supervision and tests.
- Collected 134 deterministic base rollouts over development candidates.
- Froze v2.1 before optimization when AegisLab supplied only three, rather than
  six, usable correction examples.
- Qualified the exact training path on the required three-partition smoke.
- Completed a 30-case, eight-step BF16 rank-8 LoRA pilot.
- Served the final adapter through vLLM and completed 12 paired base/adapter
  heldout cases (24 successful calls).
- Generalized the paired SFT analyzer and preserved the rejected checkpoint as
  a diagnostic artifact.

## Result and decision

Base/adapter MRR was 0.5444/0.5028 (delta -0.0417), with 0 improvements, 1
scored degradation, and 11 ties. Five-service targets prevented the v1
prediction-list collapse, but the adapter made no correction. The sole scored
degradation is a hashed pod/service alias mismatch; alias-aware sensitivity
turns it into a tie but still supplies no positive effect.

The adapter failed the frozen gate. No best model was saved, no formal/reserve
incident was opened, and no text-only SFT condition was needed because this was
not a modality experiment. Do not scale v2.1 and do not move to GRPO.

The follow-on audit rescored all 4,320 formal RQ0 trajectories with ordinary
hashed Kubernetes pod→service aliases. It changed only 35/4,320 episode scores
and left visual-minus-text negative on both models (Qwen −0.0115, Gemma
−0.0160). The evaluator mismatch is real but is not the cause of the RQ0 result.

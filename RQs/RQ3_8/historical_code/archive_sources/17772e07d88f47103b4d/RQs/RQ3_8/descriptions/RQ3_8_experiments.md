# RQ3.8 — operational_visual_support registration

2026-09-29: the user authorizes a new Nibi round, up to six formal GPU jobs,
each no longer than eight hours, after static, CPU and bounded GPU qualification.
Eight arms and all scientific/operational/statistical rules are defined in
`docs/experiment_plans/CanvasRCA_RQ3_8_Nibi_Plan.md`, incorporated here by reference.
The source-and-roster registration hash freezes that document before any call.
Formal authorization remains conditional on completed qualification.

Arms: T_SELECTED, T_FULL, G_SELECTED, G_FULL, READOUT_FULL, LINE_FULL,
LINE_BOUND, LINE_PAIRS. All 480 eval cases, both new registered models.
The smoke uses the smallest opaque ID in each existing primary-dataset
development roster (AIOPS-2022, AIOPS-2025, AegisLab). This explicitly inherits
the retired-validation/primary-eval smoke amendment, not the obsolete RE2 rule.
The two models share one 18-call/600-second logical smoke. No separate smoke
for individual ablations or shards.

## Model migration decision

- Qwen: retain the local Qwen3.8-27B recipe and exact checkpoint revision
  `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`.
- Gemma: **google/gemma-4-31B-it**, revision
  `842da3794eaa0b77d5f08bae87a17459d91ff475`; the user explicitly corrected the
  initially repeated 26B model name. Dense31B is a new model, not a continuation
  of old MoE results. Do not infer that architecture caused old performance.
- Limited Nibi inventory found only `/scratch/lglsj/CanvasRCA/models/Qwen3.6-27B`
  and `/scratch/lglsj/CanvasRCA/models/gemma-4-26B-A4B-it` as obsolete targets.
  Both are real directories with ordinary shard files, not shared-cache symlinks.
  User explicitly authorizes removal of these two model directories. Qwen9B at
  `/scratch/lglsj/models/qwen3.5-9b` and its other-project environment are protected.
- Do not edit archived model configurations or results. Use a new experiment-bound
  cluster configuration. All new rendered inputs use `src/renderer`.
- Local Gemma replacement happens **after formal Nibi submission**, not before.
- Nibi lists full `gpu:h100` separately from `nvidia_h100_80gb_hbm3_3g.40gb` MIG.
  Request full H100 and check actual memory before launching the unquantized model.

No new inference is authorized by the presence of this draft alone; qualification
and complete scientific registration must precede formal submission.

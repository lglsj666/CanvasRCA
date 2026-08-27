# 2026-08-26 — RQ1.1 unified representation refactor

## Scope and status

This session implemented the unfrozen RQ1.1 successor for `direct_qa`,
`direct_rca`, and `multi_stage_rca`. The work is implementation and static/CPU
qualification evidence only. No RQ1.1 VLM request, smoke result, gate result,
or efficacy result has been produced, and formal execution remains disabled.

The latest RQ1 formal shards, local heldout results, result-analysis tree, and
`docs/RQ1_report.md` remain protected historical audit artifacts. The protected
inventory contains 723,268 files and verifies against
`artifacts/rq1_1_migration/protected_files.sha256` with zero mismatches.

## What happened

- Created `RQs/RQ1_1/` from a verified byte-identical RQ1 copy. The normalized
  initial-copy manifest hash is
  `35abdcc2ff6dc5c840cd2c83422ed083b4adb38ab3ceac5cf866513f9d0d2057`.
- Preserved renderer-v12 as the RQ1.1-owned real dashboard renderer. Its active
  source remains equivalent to RQ1 after normalizing the required package-local
  import rewrite. Mixed arms use pixel crops from that same dashboard.
- Implemented T, V, S, LV, MV, TCV, and TPV with a shared atomic fact inventory.
  S is a measured, lossless screenshot of the exact T incident fragment rather
  than a newly authored summary or JSONL representation.
- Added deterministic case-local numeric anonymization: three digits for
  services, four for nodes, and five for pods. The mapping is regenerated per
  case and shared consistently by text, image, tools, candidates, and the
  evaluator-private reverse map.
- Added the 4/12/24/24 M/R/L/G direct-QA registry, one-call direct RCA, and the
  fixed three-step ReAct-like RCA state machine. Each multi-stage step uses a
  planner call, one bounded deterministic tool call, and an analysis call. The
  stateless analysis call replays the same arm evidence before consuming the
  tool observation.
- Added `DenumReadableLogGraphV1`, a readable text/graph adaptation of Denum's
  numeric-token and repeated-template separation. It has no binary model input
  or runtime dependency and passes canonical semantic round-trip checks.
- Removed active attention collection and active Qwen3.6 paths. Protected
  historical results mentioning Qwen3.6 remain unchanged.
- Added explicit Nibi and local deployment profiles for the same inference
  recipe. Nibi uses `configs/vllm_inference.yaml` with no project VRAM fraction.
  Local WSL uses `configs/vllm_inference_local.yaml`, local model/environment
  paths, and `gpu_memory_utilization=0.65`.
- Added direct local launchers. Local WSL never invokes `sbatch`, uses ordinary
  background processes when persistence is needed, and shares the same runner,
  prompts, renderer, scorer, model-specific processor settings, and prepared
  evidence as Nibi. Slurm submission remains Nibi-only.

Both Nibi-profile and local-profile static suites pass. The current outputs
report 2,660 functional Python lines, eight RQ shell files totaling 219 lines,
64 QA templates, seven registered representation arms, four public tools, and
no active legacy-preparation or attention offenders. Shell syntax checks also
pass. The static Nibi and local result hashes are respectively
`1cca708c42c6ba51611c5e1b0c268d58a9bb7f030a2f7422efc8f6254eca4b0b`
and `138e933149a449a1e79667d2c1c4f3f343d60efd2fe9dd8366e1ca3d24c7e629`.

## Validity and caveats

Static checks establish source inheritance, registered shapes, deterministic
fixtures, anonymization boundaries, synthetic fact equality, readable-log
round-trip, persistence/scoring behavior, and deployment-profile parity. They
do not establish model readability, live-server compatibility, absence of
hidden response problems, or scientific efficacy.

The Nibi and local profiles intentionally differ in deployment paths and the
operational VRAM fraction only. Their remaining inference projection is equal.
The local profile is a direct-execution profile; it is not a Slurm job and must
not be represented as one in runtime metadata.

No formal contract is frozen. No formal RQ1.1 inference may start until the
single bounded smoke for each experiment has run sequentially on Qwen3.8 and
Gemma, and the completed prompts, conversations, raw responses, tool records,
truncations, and accounting have been inspected.

## Decisions

- DD-95 establishes RQ1.1 as the single-preparation representation successor.
- DD-96 establishes explicit Nibi and local deployment profiles while keeping
  one scientific inference recipe.
- Local execution is direct and never submits a Slurm job; Nibi alone owns
  `#SBATCH`, account, array, and dependency behavior.

## Blockers

- Canonical preparation and the three shared-budget two-model logical smokes
  have not run in this implementation session.
- Formal execution is intentionally disabled until those smokes pass and their
  completed artifacts receive manual hidden-problem inspection.

## Next steps

1. Prepare the canonical 469-case RQ1.1 roster once in the selected deployment.
2. Run the `direct_qa`, `direct_rca`, and `multi_stage_rca` logical smokes;
   Qwen3.8 and Gemma run sequentially within each shared 18-call/600-second bound.
3. Inspect every completed smoke conversation and record/fix tractable hidden
   issues without expanding the experiment design.
4. Freeze the RQ1.1 v1 code, packages, preparation, renderer, prompts, tools,
   scorer, model projections, and exclusions only after all smoke phases pass.
5. Execute formal `direct_qa`, then `direct_rca`, then `multi_stage_rca`, with
   Qwen3.8 completed and verified before Gemma for each experiment.

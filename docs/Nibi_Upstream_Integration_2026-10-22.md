# Nibi upstream integration — 2026-10-22

## Scope

User requested GitHub updates while preserving Nibi deployment adaptations.
Upstream commit: `67396dffaee9e7a95d15ad62b746eb7b4069c607`.
Preserved deployment parent: `21a385a2d2c0c10a2fd0bf4573e1dcd2c193e4a8`.
Worktree: `/project/def-jacobsen/canvasrca_cache/checkouts/CanvasRCA_20261022_223228`.
Branch: `nibi-update-20261022_223228`.
The running job 24832363 retains its original directory and frozen source.
This integration does not submit jobs, enable model calls, or push to GitHub.

## Merge decisions

- Incoming RQ4.6–RQ4.10, renderer additions, reports and project documents are
  incorporated from GitHub. No new changes to project rules are authored here.
- RQ4.5 runtime source is identical to the Nibi deployment snapshot after
  reviewing each conflicting hunk and the complete post-merge difference.
  The incoming RQ4.5 general fixes were already included in that snapshot.
- Keep Nibi's 0.90 GPU allocation, native SDPA visual backend, compiled/chunked
  prefill, attention capture partition, graph dispatch repair, GPU UUID
  telemetry and append-only exact-authorized infrastructure recovery.
- Keep 12 allocated CPUs / eight preparation workers, 128 GB request, persistent
  runtime environment, source/model/result/cache paths and one-H100 launchers.
- Keep the afterany dependency review with explicit failed-parent handling and
  strict smoke-receipt filename matching; upstream older variants would
  reintroduce resolved deployment failures.
- Keep Nibi authority/qualification JSON as versioned historical receipts.
  They do not qualify this merged tree. The withdrawn throughput target is
  not reintroduced, and no extra job authority is created.
- Combine local and Nibi narrative histories rather than replacing either
  environment's report. Header notes distinguish their status and provenance.
- Installed renderer dependencies/assets, model data, preparations, runtime
  credentials and experiment results are not copied into this new checkout.
  Updating code is not equivalent to deploying or qualifying a new run.

## Conflicting files

| File | Blocks | Resolution |
| --- | ---: | --- |
| `RQs/RQ4_5/README.md` | 1 | retain both environment-specific histories |
| `RQs/RQ4_5/descriptions/RQ4_5_experiments.md` | 1 | retain both environment-specific histories |
| `RQs/RQ4_5/descriptions/RQ4_5_roadMap.md` | 1 | retain both environment-specific histories |
| `RQs/RQ4_5/findings/exp_exclusive_spatial_findings.md` | 2 | retain both environment-specific histories |
| `RQs/RQ4_5/findings/smoke_goal_authority_20261019.json` | 3 | retain reviewed Nibi-specific hunk; preserve automatic nonconflicting merge |
| `RQs/RQ4_5/findings/static_check.json` | 1 | retain reviewed Nibi-specific hunk; preserve automatic nonconflicting merge |
| `RQs/RQ4_5/scripts/gpu_smoke_nibi.sbatch` | 1 | retain reviewed Nibi-specific hunk; preserve automatic nonconflicting merge |
| `RQs/RQ4_5/scripts/review_native_smoke_nibi.sbatch` | 1 | retain reviewed Nibi-specific hunk; preserve automatic nonconflicting merge |
| `RQs/RQ4_5/scripts/review_smoke_nibi.sh` | 1 | retain reviewed Nibi-specific hunk; preserve automatic nonconflicting merge |
| `RQs/RQ4_5/scripts/submit_gpu_smoke_nibi.sh` | 2 | retain reviewed Nibi-specific hunk; preserve automatic nonconflicting merge |
| `RQs/RQ4_5/scripts/submit_native_smoke_nibi.sbatch` | 2 | retain reviewed Nibi-specific hunk; preserve automatic nonconflicting merge |
| `RQs/RQ4_5/src/exps.py` | 1 | retain reviewed Nibi-specific hunk; preserve automatic nonconflicting merge |
| `RQs/RQ4_5/src/tests.py` | 1 | retain reviewed Nibi-specific hunk; preserve automatic nonconflicting merge |
| `RQs/RQ4_5/src/utils.py` | 3 | retain reviewed Nibi-specific hunk; preserve automatic nonconflicting merge |
| `devlog/CONSOLIDATED.md` | 1 | retain both environment-specific histories |
| `docs/experiment_plans/README.md` | 1 | retain both environment-specific histories |
| `important_docs/README.md` | 1 | retain both environment-specific histories |

## Validation

Static merge verification passed: 76 Python AST/syntax checks,
112 JSON parses, 71 Bash syntax checks, and no unresolved conflict
markers. All new RQ4.6–RQ4.10, renderer and scorer files match incoming GitHub
bytes. 74 Nibi runtime/configuration/history files match the preserved
Nibi parent exactly, and the corresponding active deployment bytes remain
unchanged. TypeScript compilation and runtime qualification were not rerun.

The broad diff whitespace check reports formatting already present in imported
profiling/report artifacts. The Nibi delta has one inherited trailing space
in `gates.py`; that deployed source is preserved byte-for-byte. These findings
are not syntax failures, and historical artifacts were not reformatted. No CPU experiment regression,
renderer execution, model import, GPU smoke or inference is part of this task.
The original deployment remains the source for the currently running job.

# 2026-08-10 — RQ1 v7 pending-shard resubmission

## Scope and status

RQ1 final Nibi v7 execution remains incomplete. This is an operational
resubmission under the existing 469-case roster and runtime freeze
`73f2667acdfc03b5b32a1aa0e9c57111647941502a29ce5feecbc6e0e74a747a`;
it is not a scientific result.

## What happened

At 14:09 EDT, parents `19397355`--`19397366` had no running elements. Their 26
started elements had completed with exit code zero and matching per-shard run
summaries, while 70 elements remained pending. The exact pending element IDs
were cancelled with a `PENDING` state filter; completed elements and artifacts
were untouched.

The missing shards were resubmitted resumably:

| Experiment | Model | Old pending indices | Replacement |
|---|---|---:|---:|
| `legacy_q9` | Qwen | 4--7 | `19466700` |
| `legacy_q9` | Gemma | 4--7 | `19466701` |
| `cross_region` | Qwen | 4--7 | `19466702` |
| `cross_region` | Gemma | 4--7 | `19466703` |
| `typed_two_stage` | Qwen | 4--7 | `19466704` |
| `typed_two_stage` | Gemma | 4--7 | `19466705` |
| `matched_rca` | Qwen | 2--7 | `19466706` |
| `matched_rca` | Gemma | 0--7 | `19466707` |
| `visual_counterfactual_rca` | Qwen | 0--7 | `19466708` |
| `visual_counterfactual_rca` | Gemma | 0--7 | `19466709` |
| `ledger_handoff_rca` | Qwen | 0--7 | `19466710` |
| `ledger_handoff_rca` | Gemma | 0--7 | `19466711` |

## Validity and caveats

All eight prepared indexes remain present and share the recorded freeze. The
current effective contract recomputes to the same hash. The replacements keep
the original experiment ID, roster, model checkpoints, prompts, evidence,
renderer, scorer, and resumable result roots. No partial scientific scores or
answers were inspected. The separate Exp7 aggregate smoke was not changed.

## Decisions

Each replacement task requests one H100, 14 CPUs, 100 GiB RAM, and one day,
with at most four simultaneous tasks per array. Explicit `sbatch` overrides
preserve the freeze-covered launcher bytes while changing only deployment
resources.

## Blockers

The replacement arrays were accepted but initially remain pending for Slurm
priority. No scheduler start estimate was available at submission time.

## Next steps

After allocation, verify server attestation and stable artifact progress.
After all replacements terminate, verify every shard, merge the registered
models, and run the frozen per-dataset analysis without using partial outcomes
for tuning.

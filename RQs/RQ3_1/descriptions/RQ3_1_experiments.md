# RQ3.1 protocol — data-role registration v1

## Status and boundary

2026-09-15 user authorization covers a versioned metadata-only split adapter,
manifest generation and CPU checks. It does not authorize model requests,
training, rendering, raw-data conversion, deletion or modification of historical
artifacts. Scientific arms remain in research-plan revision 5 pending complete
executable registration. Successful split checks are not experiment qualification.

## Data roles

| Dataset | Train (unchanged) | Eval (RQ480, unchanged) | Test | Registered unused |
|---|---:|---:|---:|---:|
| AIOPS-2022 | 150 | 100 | 120 | 171 |
| AIOPS-2025 | 150 | 100 | 120 | 30 |
| AegisLab | 0 | 100 | 120 | 1202 |
| RE2-OB | 0 | 90 | 0 | 0 |
| RE2-TT | 0 | 90 | 0 | 0 |
| Total | 300 | 480 | 360 | 1403 |

These registered counts were independently verified against the generated files. All 2,543 current V3 identities occur in
exactly one of train/eval/test/unused. There is no active validation/excluded
partition. The underlying processed files are not moved.

Test must contain all former validation identities (70 per AIOPS), plus 50
former-unused identities per AIOPS and 120 AegisLab. RE2 is eval-only. Remaining
corpus cases, including former excluded non-eval cases, are unused; preserve
their source/window overlap and eligibility annotations. Unused is a role,
not a certificate that a case is unexposed or eligible for training.

## Selection and isolation

- Seed 42; label-blind stable identity hashes and intact-group subset-sum.
- Reuse unified segmentation through an explicit RQ-local adapter. Do not change
  the established global allocator, old data config or historical split.
- Reconstruct source/event/window connected components before excluding eval
  neighbours. No natural singleton assumption for missing group IDs.
- Source/window metadata may be used only for evaluator-side isolation; labels,
  root granularity, fault type, scores, model answers and rendering success are
  not selection criteria. Do not inspect prospective test telemetry for tuning.
- Preserve all existing train/eval identities. Test must not share an identity
  or connected source/event group with either. Unused may retain neighbours of
  eval and must be marked accordingly; those are not eligible test substitutes.
- Exact quotas cannot override isolation. Failure to reach a quota is a blocker,
  not permission to split a connected group or select an easier case.

## Exposure and analysis

The user explicitly reassigns the old 140 validation identities to test. They
were previously used for Composer validation and renderer failure diagnosis;
retain their origin metadata, do not rewrite their history, and stop using them
for future method development. Report overall 360, old-validation 140, added
220 and per-dataset results. Additional cases' historical exposure is not
inferred solely from the old unused name; unknown coverage stays unknown.

Freeze methods/prompts/thresholds before obtaining new test outcomes. RQ480 can
select methods now and evaluate/select checkpoints in a future learning study,
but never becomes training data merely by renaming the role. Reusing test
feedback to revise a later method changes the evidentiary status of that later
evaluation. This protocol does not promise unseen-application generalization.

## Artifacts and required checks

Adapter config: `RQs/RQ3_1/configs/data_split_v1.json`.
New registration root: `RQs/RQ3_1/results/data_registration_v1/`.
Public identities and evaluator-private windows/provenance remain separate.
Source manifests and old train/eval/validation split hashes are recorded and
must be unchanged after generation.

Checks: full-corpus coverage, no duplicate assignment, exact per-dataset counts,
old validation inclusion, preserved train/eval identities, source/group
separation, public-field allowlist, deterministic rerun, conflict rejection,
and persistence. G and C independently recomputed the outputs; five CPU
regressions and a byte-identical `--check` passed. No smoke or model test is
part of this data-only task.

The planned seven-method/two-model final test costs at most 5,040 new calls;
the complete prospective research core is 23,734 and total ceiling 28,000.
These are future allocations, not current execution permission.

# 2026-07-31 — Project-wide RQ layout migration and Git publication

## Purpose

The repository was reorganized so that RQ-specific material has one canonical
home under `RQs/<rq>/`. This was a project-wide maintenance migration, not a new
experiment and not a reinterpretation of any result.

`Codex.md` now requires every RQ to contain six directories:

- `descriptions/` for the question, protocol, and preregistration material;
- `results/` for experiment-generated artifacts;
- `scripts/` for mutable and provisional RQ-specific code and launchers;
- `src/` for the frozen, submission-ready RQ implementation;
- `findings/` for final conclusions and summaries; and
- `configs/` for RQ-specific configurations, rosters, locks, and contracts.

The `src/` directory remains frozen until the RQ is complete and its final
solution is approved. Experimental code must remain under the corresponding
RQ's `scripts/` directory until then.

## Canonical layout established

- Created the six required directories for the RQs present at migration time.
- Moved the shared Python package from `vlmrca/` to `RQs/vlmrca/` and updated
  package discovery and imports accordingly. The project-root `vlmrca` entry is
  only a compatibility symlink to `RQs/vlmrca`; it is not a duplicate source
  tree.
- Retained the project-root `scripts/` as the real canonical location for
  shared command-line and batch entry points.
- Moved mutable RQ0- and RQ3-specific scripts and launchers to
  `RQs/RQ0/scripts/` and `RQs/RQ3/scripts/` respectively.
- Moved RQ-specific configurations under the corresponding RQ. The root
  `configs/` directory now contains only the unified
  `case_manifest_480.json` and `upstream_pin.yaml` configurations.
- Moved 68 registered result directories out of the root `results/` tree:
  14 to `RQs/RQ0/results/`, eight to `RQs/RQ1/results/`, and 46 to
  `RQs/RQ3/results/`. The root tree no longer contains RQ experiment results.
- Updated project documentation, launchers, analysis tools, package metadata,
  and internal references to use the canonical paths.

## Historical contracts and hashes

The machine-readable migration record is
`RQs/RQ0/configs/contract_migration_2026-07-31.json`. It records the old-to-new
configuration, script, and result mappings; the affected hashes; and 14
affected run contracts.

The migration is explicitly metadata-only. It did not change model inputs,
models or checkpoints, decoding, scoring, prompts, evidence, or execution
semantics. Path-bearing hashes and self-hashes were recomputed where required,
while genuine historical source and implementation digests were preserved.
Accordingly, the historical experiments covered by the manifest are deemed to
have run under the relocated contract and remain valid and comparable. This
rule does not extend to any future substantive change in experiment behavior.

## Packaging and ignore policy

- `pyproject.toml` now discovers the `vlmrca` package below `RQs/` and exposes
  `RQs/` on the pytest Python path.
- Project-root `build/`, `models/`, and `tests/` are ignored by Git. Existing
  test files remain available locally but were removed from repository
  tracking as requested.
- Generated `*.egg-info/`, bytecode, render caches, scheduler output, and other
  registered transient artifacts remain ignored. A root `vlmrca.egg-info`
  directory is generated packaging metadata, not source, and may be safely
  regenerated or removed.

## Validation

The completed migration passed the following checks before publication:

- all 9,682 JSON files and 16,146 JSONL records parsed successfully;
- all 14 affected run-contract headers and dependent hash chains validated;
- canonical self-hashes and migrated path scans passed;
- the shared case manifest remained reproducible;
- Python compilation and shell syntax checks passed;
- the complete local suite passed: 90 tests in 51.39 seconds; and
- the project wheel built successfully from the relocated package.

No inference, training, GPU workload, or sudo command was run as part of this
layout migration.

## Git publication and recovery point

The migration was committed as `9384d73` (`Reorganize RQ layout and project
artifacts`). It was first published on `rq-layout-migration` and then advanced
the GitHub `main` branch from `6ceb513` to `9384d73`.

Before updating `main`, the previous main tip was preserved locally and on
GitHub as `main-backup-20260731`, which points to `6ceb513`. After publication,
local `main`, `origin/main`, `origin/rq-layout-migration`, and the migration
working branch all pointed to `9384d73`. The backup branch is the recovery point
for the pre-migration repository layout.

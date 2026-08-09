# 2026-08-09 — Nibi refactor static handoff

## Scope and status

This was project-wide Nibi preparation in the clean-copy worktree. Its
evidentiary class is implementation/static QA, not an RQ experiment. No dataset
partition was opened and no LLM/VLM, vLLM server, smoke, gate, training, or GPU
call was started. The refactor is complete and the CPU-only static checks pass.

The three frozen global config source hashes are:

- dataset segmentation: `52ff16908335420bbaf98ff12b53996913c9ea2e18f90aa381ebb598dc99744b`;
- RCA scorer: `8f31970302ff5c840144c1de2ba48c716da7c3b223bf90e03a5bd31aed97c915`;
- vLLM inference: `d768fb88f720a406489030522fbc8433198bb573242d264d6b81e214beac70f7`.

These are source-config hashes for deployment handoff. They are not live-server
attestations and do not authorize a heavy run.

## What happened

- Created exactly three root unified configs and their reusable Python bases in
  `src/unified_scripts/`. Explicit subclasses or hash-recorded adapters remain
  available without copying a global contract into an RQ.
- Moved the shared Python package to `src/vlmrca/`, shared Python commands to
  `src/cli/`, and retained only shell entry points under `scripts/`.
- Replaced the duplicated RQ1 implementation with the prescribed six-file
  package. Its five functional modules total 1,286 lines; its four shell files
  total 73 lines. The compact registry preserves Legacy-Q9, cross-region,
  typed-two-stage, and matched end-to-end RCA experiment intent.
- Normalized RQ2 to the same layout. Its five functional modules total 277
  lines and its three shell files total 27 lines.
- Normalized RQ descriptions and findings. Every registered experiment has one
  `exp_<experiment>_findings.md`, including experiments not yet run.
- Added Nibi module/wheelhouse build files, exact dependency sets, an H100 Slurm
  template, a config-generated vLLM launcher, and deployment guidance.
- Set the Nibi vLLM GPU-memory fraction field to null; generated Qwen and Gemma
  server arguments contain no `--gpu-memory-utilization` flag. Qwen retains no
  project pixel limit; Gemma retains `max_soft_tokens=1120`, xgrammar, and
  chunked prefill.
- Corrected unified `AVG@3/5` to the existing cumulative-AC definition, kept
  unknown numeric predictions at their original ranks, added deterministic
  Stage-1 observation/edge binding, and corrected the one-attempt client call
  boundary (`max_retries=1`, meaning one total request).

## Validity and caveats

Static validation passed with zero model calls:

- both RQ static entry points passed;
- all 57 Python files parsed;
- fatal Ruff rules and unused imports in the new global/RQ modules passed;
- every shell entry point passed `bash -n`;
- root `configs/` contains exactly three files, root `src/` contains only
  Python source, and root/RQ `scripts/` contain only `.sh` files;
- the 16-cell RQ1 and RQ2 factorial contracts, numeric-ID widths, global scorer
  synthetic metrics, Qwen/Gemma generated server arguments, and deterministic
  Stage-1 binding passed synthetic checks.

The inherited shared pipeline still has non-fatal style warnings under a full
Ruff ruleset. They were not mechanically rewritten because doing so would
expand scope and risk logic drift. No Nibi module, wheel availability, model
checkpoint, processed dataset, Slurm allocation, renderer output, live API,
smoke, or gate was validated from WSL.

The clean copy already contained a very large deletion set before this work;
this session did not restore deleted historical artifacts. A deployment agent
must review the final Git diff and commit scope rather than treating the source
worktree's pre-existing dirty state as a result of static validation.

## Decisions

DD-43 records the project-wide decision to use three extensible global
contracts, a `src/`-Python/`scripts/`-shell separation, compact RQ packages, and
an uncapped-by-CanvasRCA Nibi vLLM launcher. The evidence is the passing layout,
hash, scorer, factorial, and generated-argument checks above.

## Blockers

There is no blocker to packaging or deployment review. Heavy execution remains
intentionally unauthorized until Nibi has the processed data, checkpoints,
exact compatible wheels or an approved Apptainer image, frozen private rosters,
a live-server attestation, and the bounded smoke required by project rules.

## Next steps

1. Review and commit the clean-copy diff with special attention to the
   pre-existing large deletion set.
2. Transfer the repository, processed dataset, checkpoints, and dependency
   bundle to Nibi.
3. Build the Nibi environment and rerun `scripts/static_checks.sh`.
4. Generate/freeze public and evaluator-private split artifacts, then freeze a
   new experiment contract and live-server attestation.
5. Enable one new result ID, run the bounded smoke, inspect every completed
   artifact, and only then schedule the heavy RQ job.

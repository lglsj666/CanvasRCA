# 2026-08-03 — CanvasRCA rename and shared Codex/Claude skills

## Scope and status

Project-wide, non-RQ maintenance. The active project branding and executable
paths were migrated from the former repository name to `CanvasRCA`. The Claude
workflow skills were updated to the current project contract and exposed to
Codex. This work is complete locally and is not yet committed by this session.

## What happened

- Updated active documentation, package branding, agent descriptions, shell
  messages, and executable defaults to use `CanvasRCA`.
- Replaced the project environment variables with `CANVASRCA_ROOT` and
  `CANVASRCA_VENV`.
- Pointed retained launchers at `/home/lglsj/CanvasRCA/venvs/infer` and updated
  the two retained watcher scripts to resolve `/home/lglsj/CanvasRCA` through
  `CANVASRCA_ROOT`.
- Preserved `vlmrca` as the Python distribution, import package, canonical
  `RQs/vlmrca/` path, and contract identifier. Renaming it would break imports
  and historical contracts and is not part of the project-brand migration.
- Reworked all nine canonical skills under `.claude/skills/`: `agent-trace`,
  `baseline`, `dashboard`, `design-decision`, `devlog`, `experiment`, `smoke`,
  `status`, and `vlm-serve`.
- Added Codex metadata under each skill's `agents/openai.yaml`.
- Added `AGENTS.md -> Codex.md` so Codex automatically loads the project rules.
- Added `.agents/skills -> ../.claude/skills` so Claude and Codex use one
  canonical skill body instead of drifting copies.

## Validity and caveats

- No historical result trajectory, model input, model output, image path,
  run-contract hash, or artifact hash was changed. Forty-seven historical
  result files still contain the actual old scratch path by design.
- The legacy vLLM environment name in the 2026-07-23 devlog was retained as
  historical provenance.
- Renaming or recomputing hashes could not repair experiments affected by label
  leakage or unequal information. Their evidentiary status is unchanged; this
  maintenance neither invalidates accepted artifacts nor rehabilitates invalid
  ones.
- `vlmrca` remains an intentional technical package name and is not an old
  repository-brand reference.

## Validation

- All nine skills passed the official `quick_validate.py` validator.
- All nine `agents/openai.yaml` files parsed and their default prompts reference
  the correct `$skill-name`.
- `codex debug prompt-input` discovered all nine skills and loaded the complete
  `Codex.md` content through `AGENTS.md`.
- Changed shell files passed `bash -n`.
- `RQs/vlmrca` passed `python3 -m compileall -q`.
- `scripts/env.sh` resolved the new root and tools environment correctly.
- `git diff --check` passed.
- Independent forward tests confirmed that the dashboard/trajectory skills
  reject raw-ID visual results, the experiment/smoke skills refuse an
  unregistered new RQ, and the serving skill selects BF16/0.65 while detecting
  the retained shared launcher's configuration mismatch.

## Decisions

- Keep `.claude/skills/` as the single canonical cross-agent source and expose
  it to Codex with the documented repo-level `.agents/skills` path.
- Preserve raw historical artifacts until an explicit whole-artifact retention
  or deletion decision is made; do not rewrite their provenance fields.

## Blockers

None for skill discovery or the active-name migration.

## Next steps

1. Review and commit the rename, symlinks, skills, and this devlog.
2. Separately decide whether invalid historical experiment bundles should be
   retained with an invalidity manifest or removed as complete bundles.
3. Before reusing the shared legacy SLURM launcher, reconcile it with the
   canonical local vLLM configuration; the updated `vlm-serve` skill requires
   this check and will not treat a mismatched launcher as qualified.

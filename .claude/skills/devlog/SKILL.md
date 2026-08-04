---
name: devlog
description: Write a dated CanvasRCA development or experiment log with outcomes, validity status, caveats, blockers, and next steps. Use after a work session, experiment transition, failure, or handoff.
---

# Development logging

Read `Codex.md` and route the log by scope.

- Use `devlog/<YYYY-MM-DD>_<slug>.md` only for project-wide, non-RQ work.
- Put an RQ experiment log under
  `RQs/<rq>/results/<experiment>/logs/`.
- Put settled RQ conclusions under `RQs/<rq>/findings/`.

Use this structure:

```markdown
# <date> — <title>

## Scope and status
RQ/experiment, evidentiary class, partition, contract hash, and completion state.

## What happened
Concrete changes, calls completed, metrics, errors, and artifact paths.

## Validity and caveats
Leakage/equality audits, parse/truncation rates, infrastructure exclusions,
resume state, and anything sampled or skipped.

## Decisions
What changed and the evidence supporting it.

## Blockers
What prevents the next registered step.

## Next steps
Ordered actions that can be started from the recorded artifacts.
```

State negative results honestly. Never let a recent number overwrite its
status: a smoke remains a smoke, an invalid run remains invalid, and a removed
operational gate does not reclassify historical evidence.

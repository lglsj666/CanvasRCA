---
name: devlog
description: Write a dated development log entry recording what happened in a work session — decisions, results, blockers, next steps. Use at the end of a session, after an experiment completes, or when handing off work.
---

# Devlog

One file per session: `devlog/<YYYY-MM-DD>_<slug>.md`. Read the most recent
entry first so the narrative is continuous.

## Template

```markdown
# <YYYY-MM-DD> — <short title>

## What happened
Concrete outcomes. Numbers, not adjectives: "MRR 1.000 on 20 RE2-OB cases with
claude-opus-4-7, 4.4k tokens/case" rather than "smoke test went well".

## Key decisions
Each with its reason. If it settles a design question, also add it to
`plans/design_decisions.md` and reference the DD number here.

## Blockers
What is stopping progress and what would unblock it. Include things you worked
around rather than fixed — those are the ones that get forgotten.

## Next steps
Ordered, specific, each one startable without rereading this file.
```

## Rules

- State results honestly, including negative ones. A dashboard axis that made no
  difference is a finding and belongs in the paper's ablation table.
- Record caveats next to the numbers they qualify. "MRR 1.000" without "on the
  easiest dataset, which text baselines already scored 0.994 on" is misleading
  three weeks later.
- Note anything skipped, capped, or sampled. Silent truncation reads as full
  coverage when you come back to it.

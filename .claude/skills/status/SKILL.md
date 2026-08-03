---
name: status
description: Report current project status — phase, progress, open questions, blockers, next action. Use when asked "where are we", when resuming after a break, or before planning the next work session.
---

# Project status

Read, in order: `plans/action_plan.md`, the newest file in `devlog/`,
`plans/design_decisions.md`, then `results/*/summary.json` and `git log --oneline -10`.

## Output format

```
Phase:        <M0 scaffold | M1 smoke | M2 RQ1 grid | M3 RQ2 loop | M4 RQ3 panel | M5 ablations>
Progress:     <X/Y milestones>
Last result:  <the most recent number that matters, with its caveat>
Open question:<the decision blocking the next step>
Blocker:      <what is stopping work, or "none">
Next action:  <one concrete startable task>
Timeline risk:<low | medium | high, and why>
```

Keep it to that. If a section has nothing real in it, write "none" rather than
padding it.

## Milestones

- **M0** scaffold, shim, frozen manifest, venv, skills — done 2026-07-22
- **M1** dashboard v0 + smoke passing gates — done 2026-07-22 (API path; vLLM path outstanding)
- **M2** RQ1 dashboard design grid → freeze v3
- **M3** RQ2 agentic controllers → freeze best
- **M4** RQ3 model panel on 480
- **M5** RQ4 ablations + paper tables

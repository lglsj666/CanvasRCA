---
name: status
description: Report the current CanvasRCA project or RQ status from authoritative artifacts. Use when resuming work, asking what has been completed, checking blockers, or selecting the next valid action.
---

# Status reporting

Read sources in this order:

1. `Codex.md` and `git status --short --branch`;
2. the newest applicable project-wide `devlog/`, plan, and progress report;
3. the target `RQs/<rq>/descriptions/` and `RQs/<rq>/findings/`;
4. result contracts, verifier/status files, summaries, and trajectories under
   `RQs/<rq>/results/`;
5. `git log --oneline -10`.

Before accepting a Qwen/Gemma result, verify its generated contract against all
three global configs, the effective adapter, model checkpoint, prompt, evidence,
renderer, and scorer hashes. An archive directory is never resume-eligible.

Do not infer validity from recency, directory names, or a summary alone. Preserve
the recorded class: confirmatory, development, pilot, smoke, diagnostic,
invalid, superseded, incomplete, or excluded. A newer verifier that cannot read
an older schema does not automatically invalidate it.

Report concisely:

```text
Scope:          <project or RQ>
Phase:          <artifact-supported phase>
Progress:       <completed / required work>
Evidence status:<strongest valid artifact and its class>
Last result:    <number or finding with dataset, n, and caveat>
Open question:  <decision not yet settled>
Blocker:        <concrete blocker or none>
Next action:    <one registered, startable action>
Timeline risk:  <low | medium | high, with reason>
```

Never recycle stale hardcoded milestones or promote invalid/pilot results into
the current project conclusion.

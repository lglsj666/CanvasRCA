---
name: design-decision
description: Record an evidence-backed CanvasRCA design decision and its consequences. Use when choosing a load-bearing project approach, freezing a protocol, or documenting why a result changes future work.
---

# Design decisions

Read `Codex.md` and route the decision correctly:

- put project-wide, non-RQ decisions in `plans/design_decisions.md`;
- put RQ protocol and preregistration decisions in
  `RQs/<rq>/descriptions/`;
- put final RQ conclusions in `RQs/<rq>/findings/`.

Use this structure:

```markdown
## DD-<n>: <decision>
**Date:** YYYY-MM-DD
**Status:** adopted | provisional | superseded by DD-<m>

**Context.** The question and why it mattered.
**Decision.** The selected approach.
**Evidence.** Artifact status, run/contract hashes, registered statistics,
point delta, p-value, effect size, data scope, and caveats.
**Alternatives rejected.** Each alternative and why it lost.
**Consequences.** Constraints, follow-up work, and revisit conditions.
```

Do not cite a smoke, pilot, invalid, superseded, or incomplete artifact beyond
its evidentiary scope. Do not report confidence intervals under current project
rules. Preserve decisions by superseding them rather than rewriting history,
except when the user explicitly authorizes removal of unsafe or misleading
material.

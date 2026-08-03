---
name: design-decision
description: Record an irreversible or load-bearing design decision with its evidence and alternatives. Use when choosing between approaches that later work will depend on, or when a result settles a question that was previously open.
---

# Design decisions

`plans/design_decisions.md` is the project's record of *why*. It exists so a
decision is not silently re-litigated, and so the paper's methodology section
can be written from evidence rather than memory.

## When to add one

- A choice that later work depends on (reuse strategy, scoring convention, frozen config).
- A result that closes an open question (an RQ1 axis that did or did not help).
- A workaround that constrains future options (a cluster limitation, a dataset quirk).

Not for reversible implementation details.

## Format

```markdown
## DD-<n>: <decision in one line>
**Date:** YYYY-MM-DD
**Status:** adopted | superseded by DD-<m> | provisional

**Context.** What question came up and why it needed settling.

**Decision.** What was chosen.

**Rationale.** Why, with evidence — numbers, CIs, or the concrete failure that
ruled out the alternative.

**Alternatives rejected.** Each with the reason it lost.

**Consequences.** What this now constrains, and what would justify revisiting it.
```

## Rules

- Never delete a decision; supersede it and link forward. The history of what
  was tried is what stops the same dead end being explored twice.
- Cite the experiment or file that produced the evidence.
- If a decision was made on judgement rather than data, say so — a provisional
  decision flagged as such is honest; one dressed as evidence-based is not.

---
name: agent-trace
description: Inspect and classify CanvasRCA trajectories, model-visible evidence, rankings, and failure modes. Use when diagnosing an experiment, comparing paired cases, auditing visual reliance, or preparing an evidence-backed failure analysis.
---

# Trajectory analysis

Read `Codex.md` and the target RQ's description and status authority before
interpreting any score. Locate artifacts under
`RQs/<rq>/results/<experiment>/`; never assume a project-root `results/` path.

## Qualify the artifact first

1. Read the frozen run contract, roster, summary, verifier output, and hashes.
2. Establish the artifact status: confirmatory, development, pilot, smoke,
   diagnostic, invalid, superseded, incomplete, or excluded.
3. Audit the actual model-visible prompt and image payload. A trajectory's
   `turns[*].images` path is not proof that the backend received the image.
   Use the arm/stage record, request artifact, image hash, and inventory.
4. Check label blindness, opaque IDs, relative time, and atomic-fact equality.
   If leakage or unequal information affected the comparison, classify it as
   invalid for efficacy/modality claims and stop performance interpretation.
5. Separate infrastructure exclusions from model outcomes. Parse failures,
   truncations, and invalid model output remain model outcomes.

Read episodes with the shared library when the schema supports it:

```python
from vlmrca.agent.trajectory import read_episodes
episodes = read_episodes("RQs/<rq>/results/<experiment>/trajectories/episodes.jsonl")
```

Do not invalidate an older artifact merely because a newer reader cannot parse
its schema; consult its original status authority.

## Diagnose paired cases

- Match cases by opaque incident ID and registered arm/condition.
- Open the exact image artifact the model received and inspect the prompt span
  or JSON pointer for every cited `fact_id`.
- Read ground truth only in the offline evaluator/audit step; never feed a
  label-bearing index or analysis file back to the evaluated model.
- Verify scoring granularity before calling a prediction correct or wrong.

Assign one primary mode to each failure:

| Mode | Signature |
|---|---|
| `invalid-input` | leakage, unequal fact inventory, wrong prompt, or stale contract |
| `infrastructure` | backend/process/tool failure covered by paired exclusion |
| `parse` | response exists but violates the registered output schema |
| `truncation` | output reaches the registered ceiling before a valid answer |
| `selection` | required evidence never entered the canonical evidence bundle |
| `perception` | visible fact is read incorrectly |
| `reasoning` | facts are read correctly but causal conclusion is wrong |
| `victim-confusion` | downstream symptom is ranked above the origin |
| `tool-misuse` | an agent stage wastes or misroutes actions |
| `context-loss` | a needed fact disappears between stages |

Report counts by dataset, fault type, arm, and status. Cite representative
artifact paths, distinguish visual benefit from visual harm, and never promote
an anecdote or invalid run into an efficacy conclusion.

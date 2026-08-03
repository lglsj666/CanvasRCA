---
name: agent-trace
description: Inspect and classify VLM-RCA trajectories — replay a case's turns and images, diagnose why the model got a case wrong, quantify failure modes. Use when analysing experiment results, iterating on the agentic controller, or writing failure analysis for the paper.
---

# Trajectory analysis

Aggregate metrics say a config lost; trajectories say why. Failure analysis is
what turns an RQ2 iteration into a design improvement rather than a guess.

## Reading a trajectory

`results/<exp>/trajectories/<exp>__<model>.jsonl` — first line is a header
(experiment, model, dashboard config, upstream commit), then one line per case.

```python
from vlmrca.agent.trajectory import read_episodes
eps = read_episodes("RQs/RQ1/results/smoke_re2ob_opus/trajectories/smoke_re2ob_opus__claude-opus-4-7.jsonl")
wrong = [e for e in eps if e["mrr"] < 1.0]
```

Each turn carries `images` — the PNG paths the model actually saw. **Open them.**
A wrong answer whose dashboard never showed the true cause's metric is a
selection failure, not a reasoning failure, and the fix is in `kpi_select`, not
the prompt.

## Failure taxonomy

Label every wrong case with exactly one primary mode:

| Mode | Signature | Fix lives in |
|---|---|---|
| `parse` | `parse_ok=false`, prose instead of JSON | prompt / answer format |
| `selection` | true cause has no panel on the dashboard | `kpi_select`, panel budget |
| `perception` | evidence visible, model misread the chart or legend | `render/style`, resolution, labelling |
| `reasoning` | evidence read correctly, wrong causal conclusion | scaffold, topology framing |
| `victim-confusion` | named a downstream symptom-bearing service | topology emphasis, prompt guidance |
| `tool-misuse` | (agentic) wasted turns, never zoomed the right panel | controller, tool descriptions |
| `context-loss` | (agentic) dropped an image it needed | retention policy |

Report counts per mode, not anecdotes. The mode with the largest count is the
next thing to fix; everything else is a distraction.

## Cross-checking against the text baseline

The upstream project has per-case results for the same cases. A case the text
method solves and the dashboard method misses is the most informative object in
the project — it isolates what rasterisation destroyed. `victim-confusion` and
`selection` failures are where the two representations genuinely differ.

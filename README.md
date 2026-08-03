# VLM-RCA

Vision-language models on **rendered telemetry dashboards** for microservice root
cause analysis.

Existing multimodal RCA systems fuse raw metrics, logs and traces through learned
encoders or text serialisation. This project asks a different question: what if
the model looks at the dashboard, the way an SRE does?

```
DataCase ──► dashboard compiler ──► PNG + panel manifest ──► VLM ──► ranked top-5 ──► score
             (RQs/vlmrca/render/)                            (RQs/vlmrca/vlm/)   (upstream scoring)
```

## Research questions

1. **RQ1** — How should all key telemetry be compiled into a single dashboard image?
2. **RQ2** — What agentic loop (zoom, expand, traverse, re-render) improves accuracy from there?
3. **RQ3** — Which VLM is best for this task?
4. **RQ4** — What does each component contribute?

## Quick start

```bash
source scripts/env.sh
pytest tests/ -q

python scripts/render_gallery.py --dataset re2_ob --n 4   # look at the dashboards
python scripts/smoke_e2e.py --model mock --n 5            # pipeline, no credentials
python scripts/smoke_e2e.py --model claude-sonnet-5 --n 20
```

## Early results (2026-07-22, n=20 each)

| dataset | model | MRR | text-baseline MRR |
|---|---|---|---|
| RE2-OB | claude-opus-4-7 | 1.000 | 0.994 (saturated) |
| AegisLab | claude-sonnet-5 | 0.797 | 0.679 |

The AegisLab comparison is the meaningful one — that dataset has headroom, and
the dashboard result uses a cheaper model than the text baseline it beats. It is
still n=20 with a single dashboard config; treat it as a reason to run the
n=100 paired comparison, not as a result.

See [CLAUDE.md](CLAUDE.md) for conventions and invariants,
[plans/action_plan.md](plans/action_plan.md) for the milestone plan, and
[plans/design_decisions.md](plans/design_decisions.md) for why things are the way
they are.

Datasets, task framing, scoring and baseline numbers are reused from the sibling
project `RL-SLM-RCA` through a single shim, `RQs/vlmrca/upstream.py`.

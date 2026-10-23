# RQ4.9 — organization, compression and attention

Protocol: [approved plan](../../docs/experiment_plans/RQ4_9_Dashboard_Organization_Compression_and_Attention_Plan_2026-10-21.md).

This is a single-call experiment on 220 exposed development incidents. There are 23 RCA conditions and a maximum of 6,000 new calls. Hybrid evidence is explicitly authorized for this study. Historical U, T_FULL, MARGINAL_FIVE and H_MARGINAL are references, not new inference jobs.

All runtime permissions default to false. A successful static check is not permission to load a model. Version-bound CPU, runtime, visual and three separate smoke qualifications are required before formal execution.

```bash
RQs/RQ4_9/scripts/run.sh static
RQs/RQ4_9/scripts/run.sh unit
RQs/RQ4_9/scripts/run.sh prepare
RQs/RQ4_9/scripts/run.sh aggregate
RQs/RQ4_9/scripts/run.sh status
```

After qualification, `freeze --scope smoke_organization`, `smoke_operators`, or `smoke_qa` writes an explicit version-bound queue/credential. `run --scope ...` starts only that registered scope. Review all three scopes before freezing formal. Formal resumes use atomic `completed/<key>.json` files; they do not regenerate completed answers or revalidate all historical inputs at startup.

For the operator scope, run `gpu-tensor` after its freeze and before
`run --scope smoke_operators`. It checks small real-GPU fusion and redistribution
tensors against independent references inside the same 900-second window.
It uses zero model calls and does not reset or extend the smoke window.

`view --key <key>` makes a directly readable conversation page. `analyze` uses central scorer results, separate preregistered Holm families, Pratt zeros, event groups and full missing-result denominators. `retention` verifies retained objects and accounting without deleting unique data.

No test, render, CPU preparation, model loading or inference occurs merely by importing these modules. Source code is split into the five registered functional modules; the renderer extension is opt-in `study_view`.

Monitor the running formal queue:

```bash
RQs/RQ4_9/scripts/run.sh status
cat RQs/RQ4_9/results/organization_v1/formal/progress.json
tail -n 40 RQs/RQ4_9/results/organization_v1/formal/run.log
```

An existing `phase_complete.json` takes precedence over the last progress
snapshot. To request a drain-and-pause, create
`RQs/RQ4_9/results/organization_v1/formal/PAUSE`. After removing that file,
resume with `run --scope formal`; successful atomic commits are skipped.
Default GPU switches remain false: the version-bound authorization file and
all qualification receipts jointly enable this exact frozen queue.

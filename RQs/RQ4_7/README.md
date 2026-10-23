# RQ4.7 — retained single-call experiment data

**User-authorized deletion completed:** only S_COMPARE,S_GROUND,S_REASON data remain.
All three M conditions and shared action plans,including inputs,outputs,conversations,
attention,intermediates and results,were deleted without backups. Code and design
are retained. Shared public objects survive only for actual S inputs.

The retained formal subset has870 positions/750 actual calls; smoke has6 positions/5
actual calls. The original full-run queue,manifest,completion receipts and execution
authorizations are retired. Use `frozen/retained_manifest.json` for the retained
subset; it is not a runnable full-experiment freeze. No new model call is authorized.

- [Updated single-call report](../../docs/experiment_reports/RQ4_7_Qwen_Analysis_2026-10-20.md)
- [Research report](../../docs/RQ4_7_Visual_Reasoning_Research_2026-10-20.md)
- [Protocol](../../docs/experiment_plans/RQ4_7_Source_Bound_Visual_Workspace_Plan_2026-10-20.md)
- [Only findings file](findings/exp_source_workspace_findings.md)
- [Machine protocol](configs/protocol_v1.json)

Five functional modules: `exps` compiles inputs and hosts the isolated vLLM adapter;
`utils` owns transport, output adaptation, scoring, commits and retained conversations;
`gates` owns qualifications and analysis; `main` schedules dependency-aware execution;
`tests` contains offline regressions. Existing experiment/default renderer
sources are protected. Two explicit renderer exports are additive.

Static-only command (no environment/model initialization):

```bash
bash RQs/RQ4_7/scripts/static.sh
```

Operational commands (scope credentials and qualification gates still apply):

```bash
source RQs/RQ4_7/scripts/environment_local.sh
bash RQs/RQ4_7/scripts/cpu.sh unit
bash RQs/RQ4_7/scripts/cpu.sh cpu
bash RQs/RQ4_7/scripts/cpu.sh mechanism
bash RQs/RQ4_7/scripts/cpu.sh runtime
bash RQs/RQ4_7/scripts/cpu.sh freeze
bash RQs/RQ4_7/scripts/run.sh launch smoke
bash RQs/RQ4_7/scripts/run.sh review-smoke smoke
bash RQs/RQ4_7/scripts/run.sh launch formal
bash RQs/RQ4_7/scripts/run.sh pause formal
bash RQs/RQ4_7/scripts/run.sh resume formal
bash RQs/RQ4_7/scripts/run.sh status formal
```

Each CPU/model scope requires `results/source_workspace_v1/authorization/<scope>.json`
with explicit authorization and the current execution fingerprint. No credential
is created here. Formal also requires complete CPU and reviewed smoke receipts.
The `visual_review.json` and `smoke_artifact_review.json` receipts are written only
after real inspection; no placeholder can qualify.

`CANVASRCA_RQ47_ROOT`, `CANVASRCA_RQ47_SOURCE_ROOT` and `CANVASRCA_QWEN_MODEL`
permit deployment paths without mutating scientific inputs. Run the CLI in the
existing qualified environment, with `PYTHONPATH=src:.`.

## Inputs, commits and conversations

`inputs/<case>/packet.json` holds public source geometry and cached source exports.
`requests.json` contains frozen single-call/action requests. The private `evaluation/`
tree is read only after generation. An ACTION completion unlocks its three final
nodes. `completed/<key>.json` is the atomic commit; interrupted uncommitted calls
remain accounted for. No completed wrong/invalid answer is retried.

`objects/` retains exact PNGs and source dependencies by SHA256, using ordinary
files/hard links. `view --key KEY --scope formal` produces a directly readable HTML
conversation with exact prompts, source image paths, retained-token geometry,
raw response and a link to the separate original action call. The action text is
not a model-visible diagnostic reason in the second call.

`analyze` writes exact per-case CSV, JSON statistics, readable tables, QA component
scores and a qualitative-review queue. Reading the actual answer remains necessary.
`finalize` only removes runtime cache after all active scopes have atomic completion,
verified retained dependencies and ≤2.5MB/completed actual call; actual attention
is preserved with its query definitions and ≤100KB/call aggregate ceiling.

## Conditional independent validation

`confirmation_manifest.json` is an audited external selection input, not automatically
generated from exposed cases. It records 90 cases (30/dataset), source/base paths,
original-rule U retention proofs, exact full-text baseline messages, private scorer
contexts, a complete exposure registry, per-case audit hashes, event groups and
eligible frozen nominees. `prepare-confirmation` is CPU-authorized only and fails
closed if any audit or method gate is absent. Full text is permitted only in this
registered baseline, never as a method fallback. `audit-confirmation` remains read-only.

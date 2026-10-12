# 2026-09-08 — Project an entity identity once

## Scope and status

RQ2.1 CPU preparation stopped on `KeyError: example-ant`; 206 completed
selection caches and zero formal Solver calls existed.

## What happened and decision

The graph had already projected a pod such as
`example-ant-10-29153760-dkvdq` to `example-ant-10`. Passing that projected name
through the onset function's ordinal-removal step again invented `example-ant`.
The explicit `services_are_projected` argument now prevents that second step.
Raw metric/trace entities still undergo the original single projection; all
candidate IDs, private-label isolation, statistical windows and model recipes
stay unchanged. The default renderer interface is preserved for raw names.
RQ1.1 is not modified.

## Verification and impact

All 48 CPU tests and touched-core lint pass. A public-graph name audit found
this non-idempotent name pattern in 100 AIOPS-2025 cases; six had completed CPU
preparation. Those six were re-materialized, retaining their prior input copies
for the comparison. Three cases changed selected G facts or ordering under
P_RANDOM/P_DIVERSITY; the other differences were cache-signature metadata.
The remaining 200 completed caches retain all input artifact bytes.

The formerly failing `INC-375083DFDFBE` now prepares successfully; its actual
P_TRACE_SC PNG was viewed. All 56 qualified smoke logical records have exactly
the same current request parts and image hashes as before this repair. Thus no
new live call or model-output rewrite is needed. The original smoke records and
the original qualification histories remain untouched. The current execution
gate passes using this explicit CPU follow-up.

## Next steps

Resume all remaining cases and the registered formal sequence. No case is
excluded and no completed formal result needs repeating. Evidence is recorded
in `before.json`, `comparison.json`, `proof.json`, `cpu_tests.log`,
`recovery.log`, `real_case.json` and `prior_inputs/` in this directory.

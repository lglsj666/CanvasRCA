# Implementation contracts

`exps.py` owns source closure, deterministic card selection, registered renderer exports, actual processor counts, QA construction and native vLLM adaptation. `utils.py` owns immutable retention, tolerant parsing, scoring, deterministic grouping, transport and independent probability arithmetic. `gates.py` owns qualification/freeze/statistics; `main.py` owns process scheduling/resume; `tests.py` owns CPU regressions.

U28 retains whole connected source groups. The public mapping, not equality of numbers or entity names, defines source identity. Pair relation IDs partition their shared serialization tables. Mandatory candidate/window and paired sources precede stable M/R/L/G rounds; a node/resource group is retained when available. Card-count and measured-capacity skips are separate recorded reasons.

All renderer changes are explicit `study_view` exports. Existing component implementations/defaults are unchanged. Full and markless marginal views share token indices. Fusion uses FP32 accumulation, BF16 outputs and representative original coordinates. SCOPE measures real penultimate-encoder QK attention. Sink operations preserve Qwen's native attention gate and use per-request paged cache metadata rather than sharing keys between requests.

CPU may use eight distinct physical cores. GPU admission uses eight requests with a bounded 16-item/24-GB RAM preparation queue. The GPU phase consumes prepared requests and does not rebuild the telemetry source ledger. Model calls, partial outputs, infrastructure interruptions, exact-result references and independent repeats have distinct records.

### Source-label capacity repair before first model call

Original-order reflow remains the first path. If it overflows, complete card
heights are sorted deterministically; a bounded 100,000-node bin search may
redistribute them among the existing equal-width columns. It changes neither
facts, font sizes, panel widths nor the 4096-square canvas. Failure still blocks
qualification. This is capacity handling, not an outcome-guided layout search.
The pre/post renderer snapshot, version proof, failed-case regression and six
pixel-identical successful-layout witnesses are retained under `cpu/`.

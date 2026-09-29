# RQ3.1 direct-per-case revision — static review

Date: 2026-09-16. Scope: DD-RQ31-07; single-agent source review only.
Status: static checks passed; **CPU/visual/runtime qualification NOT RUN**.
Earlier 18 smoke calls remain historical, not current qualification evidence.

## Scientific and data-flow review

- The shared entry `build_public_source` has no parent packet parameter and
  does not invoke rankers, Denum, LOG-R, trace selection or anomaly topology.
- X's extractor consumes raw normalized per-case tables. It independently
  summarizes all usable metric columns, operation/service groups, identical
  messages and concrete graph/hosting relations. These summaries are an X
  method component, not a claim of lossless raw telemetry serialization.
- P0 calibration no longer substitutes X values. P0/SIRCL/X effects include
  the entire evidence-processing policy. Same-X carrier comparisons retain the
  same selected facts; the Solver recipe and scorer remain unchanged.
- Standalone observations can enter coverage selection without inventing a
  comparison partner. Selected fact closure and unique-cost validation include
  these observations explicitly.
- New logs preserve diagnostic numbers; entity references inside messages are
  explicitly typed for re-anonymization rather than replacing arbitrary numeric
  substrings. Added regression sources cover this behavior, sparse/constant/
  falling metrics, standalone observations and P0 isolation; **not executed**.
- Missing clocks are not silently classified as baseline trace observations.
  Non-finite metric columns and unbound log rows have explicit coverage counts.
  The public observation clock spans all three telemetry tables before X's
  midpoint partition is computed. No injection timestamp is consulted.

## Predecessor automated static checks (historical)

- AST parsing and in-memory Python compilation: all 20 RQ-local and regression
  source files passed; no project module imported or test executed.
- Ruff `F,E9`: passed across RQ3.1 source/renderer and three regression files.
- `bash -n`: passed separately for all seven RQ3.1 launch scripts.
- `git diff --check`: passed.
- Source dependency checks confirmed the direct entry/extraction functions do
  not call the inherited analyzer/filter functions; P0 calibration has no X
  pool argument. Existing context and smoke gates bind code/config hashes.
- Static JSON arithmetic confirms 14 eval conditions and 7 final-test methods:
  formal 23,680; future smoke allowance 54; prospective core 23,734; historical
  smoke calls 18; cumulative core 23,752; hard limit 40,000; reserve 16,248.
- Read-only call-register inspection: 18 rows, all `complete`. Nothing reset.
- Five functional modules plus `__init__`: 6,893 lines, below the 7,500 limit;
  the registered RQ-local renderer exception is separate.

## Budget correction addendum — DD-RQ31-08

Active config, source constant, runner/recovery defaults and the persistent
SQLite `settings.hard_limit` now agree on 40,000. AST/config arithmetic, Ruff
and diff whitespace checks passed; no CPU test or model call executed. The
18-call/600-second logical-smoke limits are unchanged. Only the persistent
budget setting was updated inside a transaction; all 18 `calls` rows are
byte-equivalent under canonical row serialization before/after, SHA256
`714a72f324131b5d74900a2ae2673763349cfc56ff461613b8ae7349c60e004c`.
No historical result, request, consumed count or model score was reset.

## Predecessor handoff (historical)

No preparation, rendering, CPU tests, smoke, inference or training launched.
Experiments remain paused. Static checks cannot certify real-table compatibility,
visual readability, capacity, latency or absence of runtime bugs. The next
authorized step must qualify the revised branches on bounded real cases and
versioned caches; old successful smoke records must not bypass that check.

## Direct-table successor addendum — DD-RQ31-09

The `research_v2.json` successor adds `X_C_TABLE` without renaming or replacing
the reference/catalogue `X_C` input. Its table places each comparison side's
actual selected observations next to that side and records every repeated
presentation separately while preserving one semantic fact inventory.
`X_C_TABLE_S` is generated only from those exact table bytes. Budget and
duplicate-load batches now compare X_C, X_C_TABLE and X_V_CONTRAST; final test
contains eight fixed methods. Registered formal calls are 26,360 and total
allocated core calls are 26,432 under the unchanged 40,000 ceiling.

The interrupted preparation index contains 141 hash-checked cases and no model
outputs. A false-positive global scan treated a TRC-L operation named `set` as
an entity leak. The successor keeps metric/log/topology identity scans strict,
requires every TRC-L service field to be a numeric candidate alias, and permits
operation semantics only in the operation field. Cache reuse is accepted only
for the exact recorded predecessor config/implementation and exact current
successor implementation; split, partition, budget and method lock must also
match. This is a resume compatibility decision, not a scientific result.

Python compilation, shell syntax, expanded-config audit, call-count arithmetic
and read-only predecessor-index compatibility pass. No CPU test, rendering
qualification, tokenizer preflight, smoke or inference was run for this
addendum.

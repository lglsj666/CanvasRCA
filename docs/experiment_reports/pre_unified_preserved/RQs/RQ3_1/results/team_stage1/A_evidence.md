# A evidence-engineering handoff (stage 1)

Status: stage-1 delivery complete, CPU-only, no model calls.

## Task boundary

- Preserve the existing split-registration functions in `RQs/RQ3_1/src/exps.py`.
- Add a complete-public-V3 contrast evidence pool, four source-bound bilateral
  bundle mechanisms, deterministic semantic-budget selection, a q/F-off
  ablation, and a solver-facing allowlisted materialization.
- Use RQ480/eval only for real CPU examples. Do not read test360 telemetry or
  labels for method design. Do not launch GPU, inference, training, or the old
  tournament.
- A exclusively edits `exps.py`; a targeted top-level test and this handoff are
  the only other permitted writes.

## Interface decision (2026-09-15)

The planned public API is:

- `build_contrast_evidence_pool(...) -> ContrastEvidencePoolV1`
- `build_contrast_bundles(pool) -> tuple[ContrastBundleV1, ...]`
- `select_contrast_bundles(pool, bundles, semantic_budget=...,
  contrast_gain_enabled=...) -> ContrastSelectionV1`
- `materialize_contrast_selection(pool, bundles, selection) -> dict`

Formal pool construction must reject an already-selected parent packet. A
small mapping fixture is accepted only under an explicit fixture marker. Audit
serialization retains source bindings and scores; solver materialization uses
an allowlist and excludes selector scores, paths, dataset/case identity, and
opaque incident identity.

This interface and the required stable fact shape were sent to B and C. The
four mechanism IDs are `local_execution_vs_external_wait`,
`host_vs_peer_instance`, `temporal_traffic_error_joint`, and
`discrete_state_cross_source_conflict`.

## Evidence inspected

- Fully read `Codex.md`, the 2026-09-15 research plan,
  `devlog/CONSOLIDATED.md`, the RQ3.1 descriptions, and the experiment skill.
- Inspected RQ2.1 `EvidenceUniverseV1`, its complete metric expansion, source
  binding, public analysis split, MET-Z/TRC-L/LOG-R projections, and RQ3's
  complete-pool successor.
- A live RQ480 Aegis example built from RQ2.1's verified public universe had
  17,274 source-bound items: M=1,883, R=634, L=14,650, G=107. This confirmed
  that the intended formal input is not the old 43-item rendered P0 subset.
- The trace projection contains legitimate operation-level exclusive p95 and
  count fields. No implementation may compute an alleged wait time by
  subtracting aggregate p95 values.

## Commands and results

- `wc -l ...`; `sed` reads of all required authority files: completed.
- `rg` inventory of RQ1.1/RQ2.1/RQ3 analyzers and public-pool functions:
  completed.
- RQ2.1 live public-universe probe (eval opaque `INC-DD1A8BB11CC7`) with
  `CANVASRCA_PROCESSED_ROOT=build/local_processed_v3`: completed, exit 0.
- Earlier two probes failed before data access because the worktree-local venv
  path and then `PYTHONPATH`/processed-root environment were absent; no files
  were changed and no model call occurred.
- `pytest -q tests/test_rq31_evidence.py`: five focused tests passed; after team
  integration, the combined RQ3.1 suite below passed 20 tests.
- `pytest -q tests/test_rq31_evidence.py tests/test_rq31_representation.py
  tests/test_rq31_execution.py`: 20 passed in 2.00 s.
- `ruff check --ignore TRY004 RQs/RQ3_1/src/exps.py
  tests/test_rq31_evidence.py`: passed. The ignored TRY004 warning is an
  unchanged split-parser line that predates this stage; the split functions
  were preserved.
- `py_compile` and `git diff --check` for A-owned files: passed.

Three real public eval examples were compiled without private labels or model
calls. The examples were selected by the existing RQ480 registration, one per
primary dataset; dataset identity was used only by this offline audit and is
not present in solver materialization.

| Eval audit identity | Public facts | Eligible bundles | Budget result |
|---|---:|---:|---:|
| Aegis `INC-DD1A8BB11CC7` | 18,271 | 202 | cost 127/128, 35 bundles, 55 facts |
| AIOps-2022 `INC-46EA9B460B2C` | 28,217 | 160 | cost 128/128, 10 bundles, 24 facts |
| AIOps-2025 `INC-B8CEA35848D0` | 20,704 after trace-union successor | 49 | cost 128/128 |

The final probes found 899 baseline-only and 325 current-only trace operations
in the Aegis sample, 12 baseline-only operations in AIOps-2025, and no unilateral
operation in this AIOps-2022 sample. Empty-side counts are observed zeros while
their exclusive/inclusive p95 values are `null`; all empty-side p95 fields
passed the no-missing-as-zero audit. This is why the formal adapter now requires
the RQ3.1 full baseline/current trace-union attestation rather than accepting
RQ2.1's fault-left trace projection directly.

## Changed files

- `RQs/RQ3_1/src/exps.py`: preserved all split functions and added the contrast
  pool/bundle/selection/materialization implementation.
- `tests/test_rq31_evidence.py`: five focused CPU regressions.
- `RQs/RQ3_1/results/team_stage1/A_solver_fixture.json`: small four-mechanism,
  solver-visible fixture consumed successfully by B's representation test.
- `RQs/RQ3_1/results/team_stage1/A_evidence.md`: this handoff.

## Implemented contracts and assumptions

- The formal adapter starts from the complete RQ2.1 public
  `EvidenceUniverseV1`, not its parent dashboard order. It retains all numeric
  public metric series, all Denum log event groups, all concrete call edges,
  and supplements public node→pod plus pod→service relations from V3 metadata.
- The trace successor uses the same registered per-span exclusive-duration
  computation and public analysis window, but outer-joins baseline/current
  operations. An empty observed side has count zero and unavailable p95; no
  aggregate p95 subtraction is used anywhere.
- Every fact has at least one offline source binding. Natural source names may
  exist only inside the offline `source_index`; all visible entities are
  case-local 3/4/5-digit aliases.
- Four mechanisms are supported as complete bilateral units. If either side or
  a required public relation is absent, that bundle is not generated. A real
  case need not contain every mechanism; the fixture proves all four code paths.
- Semantic costs are fixed in `_FACT_COST`. The selector reserves one quarter
  of the requested budget for mechanism/entity coverage, then uses deterministic
  saturated-F/relevance/new-coverage ranks minus redundancy per incremental
  unique-fact cost. Tie breaks are stable hashes. q/F-off changes only the
  contrast-gain term.
- `materialize_contrast_selection` is an allowlist: facts, complete bundles and
  public relations only. It excludes opaque/dataset/case identity, source IDs,
  paths, selection steps, r/d/q, costs and hashes. Full log templates replace
  the historical truncated+SHA display form. `contrast_selection_manifest`
  stores hashes, source bindings and selector diagnostics offline.

## Running processes

No background process or persistent session. Exec sessions 21809, 11114,
27819, 22728, 23052 and 57948 all exited with code 0; no PID requires recovery.

## Unfinished and next step

No A implementation is pending. One cross-team protocol value remains genuinely
unfrozen: `research_v1.json` does not yet specify the standard semantic budget
or the 0.50/0.75 integer-rounding rule. The CPU probes used 128 only as a
capacity exercise; it is not a scientific default. C/root were notified and
must freeze this before inference.

To re-run A's complete CPU handoff after a restart:

```bash
cd /home/lglsj/CanvasRCA_nibi
PYTHONPATH=src /home/lglsj/CanvasRCA/venvs/tools/bin/python -m pytest -q \
  tests/test_rq31_evidence.py tests/test_rq31_representation.py \
  tests/test_rq31_execution.py
```

## 2026-09-16 semantic-repair pass (in progress)

Root requested a second, CPU-only pass after review of the first real eval
gallery. Work currently on disk in `RQs/RQ3_1/src/exps.py`:

- case-local typed replacement of raw IP, Kubernetes DNS and UUID strings in
  the canonical pool, before any representation sees the facts;
- exact per-service trace aggregates computed from observed span exclusive
  durations, so a concrete service call edge never invents an operation-level
  traceparent pairing;
- entity-level LOG-R summaries derived from the complete source-bound log
  catalog;
- one-vs-rest instance/host candidates requiring observed pod metrics, host
  metrics, membership and hosting relations on both sides;
- complete metric-family candidate construction without hidden top-2/top-3
  truncation, with cross-unit arithmetic prohibited.

This pass is not yet handed off: solver allowlists, capacity audit, regression
fixtures, real-eval recheck and the final test run remain. No model, GPU,
test-partition telemetry or label was read. No process is running and there is
no PID/session to recover. The direct restart command is:

```bash
cd /home/lglsj/CanvasRCA_nibi && sed -n '1020,1710p' RQs/RQ3_1/src/exps.py
```

## 2026-09-16 semantic-repair completion

Status: A's CPU-only repair is complete and handed to B/C. No GPU, model call,
test360 telemetry, private label, split, historical RQ source, or unified config
was read or changed. The preceding “in progress” paragraph is retained as the
power-loss checkpoint and is superseded by this section.

### Final evidence/API changes

- Raw IPv4, Kubernetes DNS and UUID occurrences in public fact payloads now get
  deterministic case-local typed aliases before any representation projection.
  Pool validation and solver materialization both fail closed if a matching raw
  identifier remains. Repeated catalog occurrences share one alias.
- The formal trace adapter outer-joins the public baseline/current operation
  inventory and additionally computes one actual per-service aggregate from
  observed span exclusive durations. Caller/callee comparison uses those
  aggregates plus a concrete service call edge; it no longer zips arbitrary
  operation rows. An observed empty side keeps count zero and null latency.
- Host comparison enumerates every peer pair supported by a common public
  service-membership relation. Each side contains an observed pod metric, an
  observed host metric, membership and hosting. Pod-to-pod and host-to-host
  arithmetic is permitted only for identical metric semantics and units; the
  two levels are juxtaposed by metric family and are not added across units.
  Ambiguous multi-host pods remain in the CPU pool but cannot silently acquire
  an arbitrary host in a bundle.
- Traffic/error and state/log entry construction has no hidden top-2/top-3
  entry restriction. Cross-source observations with unlike semantics/units get
  `d=0`; they are not numerically added to manufacture contrast. Full templates
  replace the parent's truncated/hash display, while the nonexistent
  `full_numeric_series_available_via_search_logs` promise and audit-only fields
  are excluded by the solver payload allowlists.
- Solver materialization remains exactly one unique `facts` table, `bundles`
  that reference fact IDs, and public `relations`; it does not expand one fact
  once per bundle. `estimate_contrast_materialization_capacity(materialized)`
  now returns representation-neutral unique fact/series counts, region/field
  counts, series point slots (including missing slots), log-template characters,
  relations, bundles and scalar/character occupancy. It deliberately has no
  token estimate or acceptance threshold.
- `contrast_selection_manifest` now records every eligible-but-unselected
  bundle ID and complete-pool-but-unselected fact ID, with mechanism/field
  counts. Normal controls and decrease/stop/recovery sequences remain exact in
  the pool and in any closed selected bundle; budget omission is offline-audited
  rather than silent. A fixture verifies an exact normal→drop→stop→recovery
  series survives solver materialization without zero filling.
- The q/F-off fixture holds pool, bundle closure, cost, coverage reserve,
  relevance, redundancy and tie rules fixed, changes only the contrast-gain
  term, is deterministic, and produces a different selected peer comparison.

Stable public signatures:

```python
build_contrast_evidence_pool_from_v3(opaque_case_id, rq21_config)
build_contrast_bundles(pool)
select_contrast_bundles(pool, bundles, semantic_budget=..., contrast_gain_enabled=...)
materialize_contrast_selection(pool, bundles, selection)
estimate_contrast_materialization_capacity(materialized)
contrast_selection_manifest(pool, bundles, selection)
```

### Real eval-only CPU audits

The existing registered RQ480 identities were used only as public CPU examples.
The reported 128 value remains a non-scientific capacity probe.

| Audit identity | Complete facts | Eligible bundles | 128-probe selection |
|---|---:|---:|---:|
| `INC-DD1A8BB11CC7` | 18,332 | 14,663 (14,605 state/log; 58 call-edge aggregate) | 40 bundles, 62 unique facts, cost 128; deterministic |
| `INC-46EA9B460B2C` | 28,261 | 6,874 real peer/host comparisons; min/max bundle cost 28/36 | 9 bundles, 30 unique facts, 14 series/896 slots, cost 128; deterministic |
| `INC-B8CEA35848D0` | 20,723 | 498 (432 peer/host, 15 call-edge aggregate, 51 temporal) | 21 bundles, 39 unique facts, 7 series/448 slots, cost 128 |

The Aegis probe selected only call-edge aggregates at this arbitrary budget;
the state/log candidates remain explicit in the offline omission inventory.
This is not evidence that 128 is adequate. B is separately checking 64 and 128
on one real eval case per primary dataset with unique-fact rendering; root/C
must freeze one representation-neutral standard budget only after that evidence.

### Verification and remaining boundary

- `pytest -q tests/test_rq31_evidence.py`: **12 passed**.
- Joint A/B/C interface regression:
  `pytest -q tests/test_rq31_evidence.py tests/test_rq31_representation.py tests/test_rq31_execution.py`:
  **34 passed**.
- `ruff check --ignore TRY004`, `py_compile`, and `git diff --check` on A-owned
  source/tests: passed. TRY004 is the unchanged pre-stage split-parser warning.
- Five functional RQ3.1 modules: 3,658 nonblank/noncomment lines, under 6,000;
  the separate renderer exception is not counted.
- No A-owned background process or session remains. A is not waiting on a
  heartbeat and starts no smoke/inference. Remaining work is B's capacity/visual
  audit, root integration/acceptance and the later read-only E review. Live
  qualification and formal experiments remain unauthorized until those gates
  and the standard semantic budget are frozen.

## 2026-09-16 mechanism/robustness intervention API

Status: A's bounded CPU implementation is complete; C integration and two
scientific registration choices remain outside this handoff. No model/GPU call,
test360 telemetry/label, new dataset, formal statistic, partition, historical RQ
source, `main.py`, or unified configuration was read or changed.

New evaluator/offline APIs in `RQs/RQ3_1/src/exps.py`:

- `plan_matched_bundle_removal(materialized, *, candidates,
  numeric_to_natural, accepted_labels, max_payload_char_delta_fraction)` uses
  the canonical granularity-aware scorer and evaluator-private root binding to
  choose a root-associated bundle. It matches a non-target bundle exactly on
  the actual unique-fact deletion quantity, regions/fields, series/point slots,
  trace/log/relation/scalar counts, bundle-reference quantity and side
  modalities; the total fact-plus-reference character footprint is the only
  bounded nearest-neighbour dimension. The one plan is representation-neutral
  and is reused by Text/Vision. If no legal pair exists, it returns
  `not_applicable` rather than inventing one.
- `apply_matched_bundle_removal(materialized, plan, *, removal)` removes the
  selected bundle plus only facts not referenced by any remaining bundle. A
  root-associated bundle with no unique root-associated fact is an explicit
  no-op with the original materialization; it is never recorded as evidence
  deletion. Plans and root-derived identities are offline-only.
- `reanonymize_materialized_evidence(materialized, *, candidates,
  numeric_to_natural)` computes a deterministic bijection within each 3/4/5
  digit entity type over the complete candidate universe. It synchronizes
  typed fact payload bindings, entity lists, relation endpoints,
  mechanism-defined entity positions in comparison keys, candidate order and
  the evaluator-private numeric-to-natural scorer map. Free prose, status
  codes, metric values and other numeric strings are unchanged. The mapping is
  returned for offline audit and must not enter a request or renderer.
- `semantic_budget_from_fraction(standard_budget, fraction)` is the single
  Decimal floor rule for the 0.50/0.75 arms. It rejects a floor-to-zero budget.
- `plan_redundant_bundle_load(pool, bundles, selection, *, load_fraction)`
  builds the 0.25/0.50 common public-relevance-plus-hash prefix. Its ordered
  rows are exactly `{display_reference_id, bundle_id, occurrence_index: 2}`.
  These are display references only: no fact/payload is copied and no event,
  template or observation count changes. Complete-bundle granularity may
  overshoot the target occupancy, which is recorded.
- `plan_representation_intervention(materialized, condition)` returns only B's
  validated renderer parameters for `NO_GROUPING` or `NO_SHARED_TIME`:
  `comparison_grouping`, `shared_time_alignment`, and
  `preserve_relative_bins=True`. The observed materialization and all relative
  bins remain unchanged.

Verification:

- `pytest -q tests/test_rq31_evidence.py`: **18 passed**.
- Joint A/B/C interface regression after concurrent B/C integration: **53 passed**.
  This includes C's explicit no-op/not-applicable skip-without-call path and
  transformed private candidate binding for CPU re-anonymization replay.
- `py_compile`, `git diff --check`, and test-file Ruff passed. The only source
  Ruff finding is the unchanged pre-stage `TRY004` split-parser warning.
- Existing real eval gallery materializations for the three primary datasets
  replayed deterministically without labels: sample dimensions were
  `(85 candidates, 13 facts, 4 bundles, 6 relations)`, `(63,27,15,15)`, and
  `(104,28,16,16)`. Typed re-anonymization and both renderer-only plans passed
  and left the source materialization unchanged.
- The canonical private-root import could not be live-replayed in this Nibi
  checkout because its documented upstream RL-SLM-RCA directory is absent.
  Unit tests inject an exact evaluator stub solely to test A's pairing logic;
  formal execution must run with the sanctioned shim/upstream available and
  must not substitute a local matcher.
- The five functional modules currently total about 4,477
  nonblank/noncomment lines, under the 6,000 limit; renderer remains the
  documented exception.

Still unfrozen: root must register `max_payload_char_delta_fraction` before any
mechanism call and confirm the complete-bundle duplicate-prefix overshoot and
degenerate-identical-input reuse rule. A deliberately requires the first value
as an argument and claims no default. The standard semantic budget also remains
unfrozen as recorded above. C has removed its old first/last-bundle selection,
relative-bin rotation and cross-type ID reversal and wired these APIs; its
no-op/NA path now persists an intervention marker without initiating a model
call. Until the remaining registration values are frozen and audited,
mechanism/robustness execution is not authorized. No A-owned process/session
remains.

## 2026-09-16 trace binding, SIRCL_TEXT and full-bundle load follow-up

Status: CPU implementation and local interface qualification complete; real
three-primary-dataset SIRCL materialization remains unavailable in this Nibi
checkout because no processed telemetry tree is mounted. No model/GPU call,
test360 telemetry/label, new formal statistic, `main.py`, historical RQ source,
partition or unified configuration was read or changed.

### Trace correctness repair

`_complete_trace_items` now scopes child subtraction by
`(trace_id, span_id)`. Repeated span IDs in different traces no longer collide.
Missing trace identity, duplicate span keys and an invalid child duration make
the affected exclusive duration unavailable; invalid inclusive durations stay
missing and are never filled with zero. Counts still describe observed rows.
The source binding records either `trace_id_and_span_id` or
`unavailable_no_trace_id`.

The saved Aegis gallery example `INC-018AC5D486B5` contains service `510`
fault ExL about `2.0003e7 ms` and InL about `2.00041e7 ms`. Read-only source
inspection found that both the Canvas loader and the older Downloads checkout
convert `duration`/`duration_ms` to numeric and divide the whole column by
1,000 only when its median exceeds 10,000; the later public projection does not
rescale duration. The underlying processed/raw span rows are not present on
this machine, so the value was neither clipped nor declared a unit bug. Row
inspection remains a data-availability blocker, not grounds to alter a fact.

### SIRCL_TEXT adapter

New APIs:

- `build_sircl_text_comparator_from_v3(opaque_case_id, rq21_config)`
- `build_sircl_text_comparator(opaque_case_id, universe, native, context)`

They return `SIRCLTextComparatorV1` with a strict `model_payload` containing
`system_role`, one text payload and the exhaustive numeric candidates, plus
separate source/adapter manifests and hashes. The input is the complete RQ2.1
public telemetry/context, never a selected P0/dashboard packet. The adapter
implements the selected MET-Z/TRC-L/LOG-R sequence, U-BASE placement and VERIFY
instruction; vendored prompt constants are read from hash-verified source.
MET-Z retains every >3-sigma row, TRC-L retains the original top-40 and
60-character operation caps, and LOG-R retains every positive-score service.
No true injection time is used: all components use the registered public
telemetry-estimated split. Candidate identities, topology and hosting are
numeric and model-visible text is checked for raw IPv4, UUID, Kubernetes DNS,
dataset/path and opaque incident tokens.

The adapter manifest records all deliberate differences from the vendored
native path: public schema/split, complete numeric mapping, exhaustive
candidate line, numeric topology and trace-scoped/missing-safe ExL. The
read-only `/home/lglsj/Downloads/RL-SLM-RCA-main` checkout was also inspected;
it contains an older, hash-different prompt/tool generation and confirms the
native family binds split logic through a case timestamp. It is not imported
or treated as the selected authority; `SIRCL_selected_reference/PROVENANCE.json`
and its byte hashes remain authoritative. The
vendored artifact is incomplete as an importable runtime (`data.base`, feature
base and other modules are absent), so no external import or dependency copy
was introduced within A's exclusive-file boundary. Analyzer formulas are a
selected-only in-process adaptation bound to the vendored source hashes;
prompt constants are parsed directly from the vendored files. The CPU fixture
checks exact MET-Z, safe TRC-L and LOG-R outputs on one shared public input.
Actual original-runtime-vs-adapter replay on one eval case each from AIOps-22,
AIOps-25 and Aegis is **not claimed**: it requires the absent processed data
and, if literal native imports are required, root authorization for a complete
package closure outside A's exclusive files.

C integration contract: use `model_payload.system_role` as the SIRCL role and
`model_payload.text` as its user evidence/request. Do not prepend the Contrast
O/C reading guide and do not substitute the inherited P0 text packet. Only the
model payload is visible; source and adapter manifests remain audit metadata.

### Duplicate presentation contract

`plan_redundant_bundle_load` now emits canonical ordered rows with exactly
`display_reference_id`, `bundle_id`, `occurrence_index=2`, and
`display_scope="complete_bundle"`. It reports requested and realized semantic
costs/ratios plus the minimal complete-prefix overshoot. B confirmed that each
row restates/redraws every fact in that bundle while the canonical fact table,
payload and event counts remain unique. This supersedes the earlier three-key
short-reference wording in this log.

Verification:

- `ruff check RQs/RQ3_1/src/exps.py tests/test_rq31_evidence.py`: passed.
- A evidence tests: **21 passed**.
- Joint evidence/representation/execution interface regression: **60 passed**.
- `exps.py`: 2,975 lines, below the 6,000-line module ceiling.

No A-owned process/session remains. Formal execution is not authorized by this
CPU handoff, and the missing real three-dataset SIRCL replay must not be
silently relabelled as complete.

## 2026-09-16 native SIRCL closure and trace-semantics correction

Status: A's bounded CPU repair is complete. This section **supersedes** the
immediately preceding claims that the processed corpus was absent, that only
an in-process formula adaptation was available, and that a real three-primary
replay could not be performed. Those claims resulted from using the wrong
resource root before sourcing `scripts/env_local.sh`; they are retained above
only as recovery history. No model/GPU call, test telemetry/label, new dataset,
formal statistic, `main.py`, B/C file, partition, historical RQ source, or
unified configuration was changed.

### Actual copied native execution

`packages/rq31_sircl_native/` now contains an RQ3.1-local byte copy of the
selected SIRCL reference tree plus its MIT license, provenance, and the minimal
missing local import closure needed to execute the selected analyzers. Runtime
attestation checks every file from `packages/SIRCL_selected_reference/` against
its copied counterpart before use. The adapter imports and actually invokes
the copied native `MetricsVariantZ.get_metrics_context`,
`build_tracediag_span_features`, and `score_logs_simplerca`; it does not bind a
source hash to reimplemented formulas. The only schema bridge shifts public
relative timestamps by a fixed internal constant so the native timestamp
parser accepts them. That constant never appears in model-visible text and is
not an injection time.

The same public input is executed twice: once through the copied originals and
once through the registered duration-unit projection. MET-Z and LOG-R are
byte-equal for all three checked cases. TRC-L intentionally differs because
the native copied analyzer consumes the loader's stored duration values,
whereas the adapter converts the registered Aegis/AIOps microsecond values to
milliseconds. The model payload is produced by the adapted call to the same
native callable. Its trace preamble explicitly describes native TRC-L's
per-split, span-ID-matched summed-child subtraction as a proxy that can
double-count overlapping children and treats missing durations as zero; it is
not presented as measured local execution or downstream wait.

After `source scripts/env_local.sh`, one real public eval case from each primary
dataset built successfully from `build/local_processed_v3/` without labels:

- AIOps-22 `INC-0060628741E9`: 85 candidates, 30,788 payload characters,
  payload SHA-256 `d56ee2925e9025d174fb04f54c81a2d863dd02e76b903b28f4c1ec44a535d77c`.
- AIOps-25 `INC-01874CA0F78F`: 63 candidates, 9,675 characters, payload SHA-256
  `edc78c8b48284c4c999977ec8b994738740369a67bad697c2f8f34458513f70a`.
- Aegis `INC-018AC5D486B5`: 104 candidates, 19,330 characters, payload SHA-256
  `9182234c4824b5f9956f6e9c91250db5c8b59eee2d06e48b2d5eb408e41318e9`.

The complete machine-readable construction and source-unit audit is saved as
`A_sircl_trace_audit_v1.json`. Dotted metric and operation names such as
`101.system.cpu.iowait` and `grpc.hipstershop.891/Convert` now pass. Privacy
checking remains fail-closed for IPv4, UUID and Kubernetes service DNS and also
matches exact raw natural identities from the real context mapping, so the fix
does not disable host leakage detection.

### X trace semantics and source-unit audit

The X pool now computes its non-child-wall proxy over the complete trace frame
before assigning parent spans to baseline/current. Parent-child binding uses
`(trace_id, span_id)`, so repeated span IDs in different traces cannot collide
and a child that starts across the analysis split remains attached to its
parent. Direct-child intervals are clipped to the parent and unioned before
subtraction, preventing parallel overlap from being counted twice. Missing or
ambiguous trace identity, duplicate span keys, invalid timing/duration, and
unconfirmable intervals make the affected proxy unavailable; they do not
become zero. Fixtures cover duplicate span IDs, missing identity, a
cross-window child, and overlapping parallel children.

Because this remains a parent-wall-minus-direct-child-interval-union proxy, the
mechanism identifier is now
`trace_non_child_wall_proxy_across_call_edge`; qualifiers and analyzer text
explicitly deny that it directly measures local execution or external wait.
This correction is specific to X and does not silently alter the copied SIRCL
native algorithm.

For Aegis `INC-018AC5D486B5`, all 57,946 paired source rows satisfy stored
`duration_ms = raw duration / 1000`. The frozen source authority records raw
Aegis duration as nanoseconds, so the stored values are microseconds and RQ3.1
projects them once more by 1,000 to milliseconds. Entity `510`'s maximum span
is raw `20,006,475,731 ns`, stored `20,006,475.731 us`, and corrected
`20,006.475731 ms` (about 20.006 seconds). The formerly alarming magnitude is
therefore explained by a source-bound unit conversion, not clipped by size.

Verification after the final repair:

- `pytest -q tests/test_rq31_evidence.py`: **23 passed**.
- Ruff on A source/tests and the newly authored adapter/dependency stubs:
  passed. Byte-copied original source is intentionally not style-rewritten.
- `py_compile` and `git diff --check`: passed.
- `exps.py` is 3,120 lines; A source remains within the module ceiling.

No A-owned process/session remains. The native comparator and X repairs are
CPU construction evidence, not model qualification or an efficacy result.

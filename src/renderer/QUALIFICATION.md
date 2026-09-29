# Unified renderer v1 — implementation qualification

2026-09-28. User-authorized independent prototype. **No model calls, attention,
training, raw telemetry preparation, inference recipe changes or RQ3.7 changes.**

## Delivered structure

- `web/components/`: ten component implementations, one file per component.
  Shared primitives handle axes/coordinates/details; each component owns its marks.
- `configs/components.json`: numbered component-type catalog.
- `operations/`: nine individual operations; `configs/operations.json` catalogs arguments.
- `utils.py`: strict public DTO and deterministic layout-tree compiler.
- `web/dashboard.tsx`: instance assembly, stable indices and common card shell.
- `web/render.tsx`: offline Chromium export, visible-element audit and provenance.
- `scripts/`: isolated setup and CLI wrapper. `README.md`: usage and constraints.

New terminology is **dashboard component**, replacing silhouette for this new
interface only. Type number, instance ID and display index are distinct. Layout
reordering does not renumber instances. No arbitrary HTML or user code execution.

## Checks performed

- Python AST: 16 modules passed; shell syntax passed.
- TypeScript strict typecheck and esbuild build passed.
- CPU + browser suite: **19 passed in 6.86 seconds**. JUnit artifact:
  `build/renderer_previews/qualification.xml`.
- Exercised all ten component types and actual ownership connections; verified
  deterministic repeated PNG hash, HTML escaping, unchanged geometry for a single
  component substitution, stable numbering, no evidence mutation, theme/spacing/
  scale/index operations, negative/zero/constant/very large/very small/absent samples.
- Deliberate long-title overflow failed as expected; no hidden clipping/drop.
- Three real development cases inspected: first opaque ID in each dataset's
  existing RQ3.7 development roster, not chosen by score. No test cases used.
- Actual PNG visual inspection covered both themes, lines/bars, heatmaps,
  trace comparison and graph/matrix variants.

Issues found and fixed during qualification: React Node SSR's CJS/ESM bundling
boundary; long unit label overflow; single-component preset below minimum canvas
height. Added checks for graph node collision and connector crossing unrelated
components; separated raster scaling from logical viewport changes. These fixes
are confined to the new renderer.

## Final examples

All files are under `build/renderer_previews/v1/`; each directory contains HTML,
PNG, inputs, geometry and manifest.

| Example | Components | Bound visible fields/marks | PNG | Wall time |
|---|---:|---:|---|---:|
| `aiops2022` | 20 | 702 | 1800×3450 | 0.718 s |
| `aiops2025` | 13 | 595 | 1800×2366 | 0.668 s |
| `aegislab` | 20 | 605 | 1800×3450 | 0.718 s |
| `aegislab_matrix` | 20 | 605 | 1800×3450 | 0.718 s |
| `relations_first_light` | 20 | 605 | 2250×4313 | 0.768 s |

Times are single local measurements of browser/export invocation including startup,
not a throughput guarantee. Dependency installation and historical adapter export
are excluded. Browser GPU acceleration disabled. Node 24.20.0, React 19.3.0,
Playwright 1.63.0, Chromium 153.0.8010.12; exact package lock and per-artifact hashes
are recorded. Installed toolchain/dependencies occupy roughly 577 MiB, isolated
under `build/renderer_tooling/` and `web/node_modules/`, with no inference-venv edits.

The standard/matrix pair has identical projected evidence, inventory, bindings,
canvas size and outer component geometry, but different component implementations
and pixels (`matrix_comparison.json`). This is a compound gallery variant, not a
registered one-factor experiment.

## Scope limits

This qualifies a working renderer prototype, **not a scientific RCA comparison**.
The historical adapter projects supported public fields; its offline
`source_audit.json` enumerates exclusions. All projected fields bind to visible
elements, but that does not establish whole-parent-input equivalence, final VLM
image-token capacity, readability after processor downsampling, or higher MRR.

Geometry audits do not prove every label is perceptually clear or every edge easy
to follow. Sparse graph whitespace and dense graph edge routing remain design
issues. Ownership connectors currently reject crossings over unrelated panels;
general obstacle-avoiding routing is not implemented. Larger designs can require
explicitly larger footprints and must pass validation; facts are never deleted to
make them fit. New component families still require code plus tests.

Current RQ3.7 C and all historical renderers remain unchanged and unconnected.

## 2026-09-29 — Full observed topology qualification

This supersedes v1's **topology input adapter and default isolate display**, not
the historical experiments. There are now 11 component types and 10 operations.
See `topology.py`, `events.onset` and `graph_visibility`.

The old preview used filtered ALL_ID relations. The new adapter reads the target
public canonical graph plus all Trace identity rows, without severity/top-k
filtering. Known deployment edges are separated before graph edges are interpreted
as calls. Source evidence: `src/unified_scripts/sircl_data/aegislab.py` `_build_graph`
explicitly adds node→pod hosting edges to the same DiGraph as Trace calls. The new
prototype preserves them as hosts; no historical source or results were edited.

| Development example | Old packet call-edge rows | Full observed calls | Explicit deployment edges | Trace rows inspected | Export / render |
|---|---:|---:|---:|---:|---:|
| AIOPS-2022 | 9 | 121 | 42 | 122,394 | 1.976 / 0.769 s |
| AIOPS-2025 | 0 | 0 | 0 | 0 | 0.020 / 0.718 s |
| AegisLab | 4 | 58 | 49 | 144,221 | 1.651 / 0.819 s |

These are individual source-coverage/timing checks, not dataset-level claims.
All non-deployment graph edges in the two trace-bearing examples were independently
confirmed by trace-scoped parent joins. No database call was fabricated in those
examples: the presence of a database in the inventory alone does not establish a
call. Explicit external DB endpoints and alias/role handling are covered by tests.

Final artifacts: `build/renderer_previews/full_topology_final/`:

- `aiops2022`, `aiops2025`, `aegislab`: full dashboards, respectively
  22/15/22 components, 924/593/789 bound fields/marks.
- `aegislab_topology`: call network, deployment network and onset timeline.
- `aegislab_matrix`: same projected facts encoded in adjacency matrices; its
  preset has a different footprint, so it is a gallery, not a controlled arm.
- `*_input/source_audit.json`: public source hashes, scoped-join counts,
  filtered-vs-full provenance, hidden isolates and timing coverage boundaries.
  These offline reports are not model inputs.

Python AST, shell syntax, TypeScript typecheck/build and **25 CPU/browser tests
passed (8.21 s)**. JUnit: `build/renderer_previews/full_topology_qualification_final.xml`.
Tests cover trace-ID scoping, ambiguous parent rejection, deployment vs call typing,
unselected connections, external endpoints without candidate changes, isolate-only
visibility, DB role display, large graphs, onset bindings and existing determinism,
overflow and encoding checks. Actual final network/matrix PNGs were inspected under
the dashboard skill. Large graph edges now use gutters to avoid visually suggesting
false intermediate hops through unrelated node boxes.

Limitations: complete **observed** relations are not a guarantee of complete physical
topology. Uninstrumented relationships cannot be reconstructed without public support.
The onset component uses the existing P0 public onset rows, not all-network recomputed
onsets; graph edges do not depend on those rows. Dense call graphs still contain
crossings/shared route segments; source coverage and bounding-box checks do not prove
perfect traceability or VLM readability. Model processor qualification is not performed.
No GPU/model calls, no attention, and no changes to active experiments.

## 2026-09-29 — Pairwise topology component

Added C12 `graph.edge_pairs` in `web/components/RelationshipPairs.tsx`; C09 network
and C10 matrix are unchanged and remain selectable. Same edge list, separate
source→target tiles; no new graph selection. Added bounded compiler geometry,
redundant node-reference audit, exact DOM edge inventory and `pairs` convenience
preset. Component substitution exposed an operation-audit assumption that derived
rectangle keys never changed; corrected added/removed-key handling and tested a
round trip back to the network component.

Static Python AST, shell and TypeScript/build checks passed. CPU/browser regression:
**28 passed in 11.39 s**, JUnit `build/renderer_previews/edge_pairs_qualification.xml`.
New tests preserve cycles, self-loops, reverse edges, typed parallel relations,
database roles, isolate visibility, font 16/28, repeated IDs and deterministic PNGs.
Narrow/over-capacity components fail without dropping facts.

Real development previews reuse the previously audited full-topology DTOs; no new
per-case extraction or model calls. `build/renderer_previews/edge_pairs_v1/` contains
three full dashboards: AIOPS-2022 (163 total call/hosting edges), AIOPS-2025 (0),
AegisLab (107 total call/hosting edges). Each retains its original M/R/L/onset cards.
The full pairs preset explicitly changes footprint; not a single-factor comparison.

`calls_network` vs `calls_pairs` is a matched 58-edge AegisLab development preview:
same input hash, card inventory, field inventory, PNG dimensions and outer geometry;
only G01's component changes and pixels differ (`comparison.json`). The actual pair
PNG was visually inspected: all 58 tiles, clear source/target arrows and repeated
entity identities. This qualifies an encoding implementation, not an MRR finding.
Multi-hop visual integration, image-token budget and downstream accuracy remain
unmeasured. Running experiments and old renderers are not modified.

## 2026-09-29 — Grouped deployment and service instances

Added C13 `graph.deployment_groups`: typed node→{pods} and service→{pods} groups,
fixed font, deterministic member wrapping, bounded capacity, exact per-edge DOM
audit, repeated identities and optional isolates. Calls are rejected as membership.
All three previous graph encodings remain available and support `has_instance`.
Public service instances come from same-row Trace resource attributes or explicit
metadata, not pod-name prefix guessing. Namespace ambiguities are excluded offline.

TypeScript/build and Python AST/JSON checks passed. **33 CPU/browser tests passed
in 15.30 seconds** (`build/renderer_previews/deployment_groups_qualification.xml`).
Tests include large groups, shared members, roles, font 16/28, empty relationships,
capacity rejection, namespace ambiguity, label-independent extraction, all prior
graph encodings and deterministic PNGs. An initial capacity-test fixture reused
mutable dictionaries and generated duplicate edge IDs; corrected the fixture and
reran the complete suite successfully.

Three existing development cases exported/rendered without inference. Artifacts:
`build/renderer_previews/deployment_groups_v1/`, with separate deployment galleries
and complete dashboards. AIOPS-2022: 42 host/pod edges, no explicit service/pod
resource bindings. AIOPS-2025: no observed relationships in this example. AegisLab:
49 host/pod and 30 service/pod edges; all 30 observed service groups have one pod,
but 19 other hosted pods lack a service binding in the inspected resource columns.
This does not establish a universal one-to-one mapping. Actual group PNG visually
inspected; all 79 AegisLab membership edges visible and endpoint-audited. Complete
dashboards: 1800×4996, 1800×3408 and 1800×6180; respective render wall times
0.869, 0.718 and 0.919 seconds (individual measurements, not benchmarks).

Service correspondence is newly exposed public information, not a same-facts
rendering-only comparison with the older preview. No historical input, result,
renderer, inference service or running experiment was changed. Browser checks do
not establish post-VLM-processor readability or RCA efficacy.

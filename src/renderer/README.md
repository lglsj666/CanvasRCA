# Unified dashboard renderer (prototype)

Python validates a selected public evidence DTO and compiles an explicit layout
tree. React + SVG + CSS render cards; pinned headless Chromium exports an offline
HTML and a PNG. No LLM, GPU, raw-table scan, inference server or development server.

All renderer code and scripts live here, as requested. This prototype is **not
connected to the running RQ3.7 experiment**, and does not replace its renderer.

## Setup and use

From repository root:

```bash
bash src/renderer/scripts/setup.sh
bash src/renderer/scripts/render.sh export-development --index 0 --out build/renderer_previews/input_0
bash src/renderer/scripts/render.sh render \
  --evidence build/renderer_previews/input_0/evidence.json \
  --design build/renderer_previews/input_0/operations.json \
  --out build/renderer_previews/example_0
```

Indices 0/1/2 are fixed development examples from the three primary datasets,
chosen by opaque ID, not scores. Export uses only trusted public caches already
on disk. The CLI refuses missing/ambiguous caches rather than doing preparation.
`source_audit.json` is offline provenance and **never embedded in the HTML**.
`CANVAS_RENDER_PYTHON` can override the tools Python; `CANVAS_RENDER_NODE` can
override the isolated Node executable. Do not use an inference environment.

`render` accepts any valid `CanvasEvidenceV1`, not just that historical adapter.
Evidence fields are strictly allowlisted; callers remain responsible for truthful,
anonymized content. Private labels cannot be made safe by renaming a field.

## Component library and operation library

The user renamed **silhouettes to dashboard components**. New code/docs use the
new term; historical experimental labels are not rewritten.

`web/components/` has **one file per component**; `primitives.tsx` only shares
coordinate/axis/mark helpers, and `index.ts` registers the twelve components.
`configs/components.json` is the numbered catalog of the available design space.
`operations/` has **one file per operation**; `configs/operations.json` catalogs
the ten operations. The libraries are not hidden behind a monolithic renderer.

Three identities are deliberately separate:

- Component **type**: e.g. catalog index 1, `metric.line`.
- Evidence/instance **ID**: e.g. `M01`, preserved across component substitutions.
- Display **index**: fixed by evidence inventory (1, 2, …), not layout traversal;
  moving a component does not renumber it.

## Configuration space

| Layer | Parameters | Invariant |
|---|---|---|
| Evidence | preselected cards with typed data and numeric entity IDs | No selection in renderer |
| Layout | nested `row`, `column`, `grid`, `panel`; weights/columns | Every card exactly once |
| Component | line / time-bars / heatmap; trace bars / dumbbell / table; logs timeline / table; network / matrix / edge pairs | Same projected fields |
| Appearance | light/dark, font size, gap, padding, viewport, raster scale | No hidden auto-truncation |
| Ownership | validated card → graph entity references | Separate from calls/hosts/owns |
| Graph visibility | `graph.show_isolates` (default false) | Never deletes edges or observation cards |
| Registered diagnostic ablations | optional `presentation[card_id]` with `marks`, `details`, and optional `neutral_trace` | Explicitly audited changes, default unchanged; not equal-image-fact claims |

RQ3.8 v6 uses `presentation` only on `metric.line` and `trace.paired_bars`.
`marks=false` removes the line/sample marks or colored bars but retains axes,
printed values and their positions. `details=false` omits the statistical footer.
`neutral_trace=true` deliberately equalizes colored bar lengths while retaining
true printed values; it is a graphical-conflict diagnostic, NOT a valid telemetry
display for deployment. All switches default to the existing drawing. The emitted
`suppressed_visual_bindings` explicitly identifies removed visual encodings;
the browser does not falsely certify them as visible. Experiments using these
switches must preserve a truthful textual counterpart and register their scope.

## Complete observed topology, not selected Trace summaries

The development adapter now reads the target canonical per-case `graph.json`,
public deployment metadata and **all rows of the trace identity/endpoint columns**.
It does not reconstruct topology from selected TRC-L, MET-Z, ALL_ID or panel rows.
`topology.py` owns this extraction. Only identity columns from logs and the metric
schema are read to reproduce the existing numeric aliases; no log messages,
metric values, anomaly analyzers or raw source corpora are scanned.

Calls and deployment are separate graph instances, using the same graph component
library. Some canonical graphs contain both: known `node_pod_map` / `service_pod_map`
edges are classified as hosts/owns, **not automatically called invocation edges**.
Parent spans join on `(trace_id, span_id)`. Ambiguous parents do not produce guessed
edges. A client span's explicit peer/server endpoint may add an otherwise
uninstrumented dependency; SQL text or `db.system` alone does not identify one.
DB/cache/queue roles use explicit attributes or exact product names, never substring
matching arbitrary operations. Existing numeric IDs stay unchanged. Newly observed
external endpoints use six-digit aliases; candidates are not expanded by rendering.

`graph.show_isolates=false` hides only nodes with no edges in that full component's
observed relation set. No selected metric, trace, log or onset observation is removed.
Hidden graph IDs are recorded in `geometry.json` and `manifest.json`; setting the
flag true shows the source inventory. The `graph_visibility` operation changes it.

`events.onset` is a separate component: observed relative onset, severity reading
and source, inspired by RQ1.1. It draws no causal propagation arrow or unobserved
persistence interval. Its current adapter reuses existing P0 onset observations;
it is **not full-network anomaly recomputation**. Graph connectivity does not depend
on these selected onset rows, and equal/no onset does not suppress an edge.

"Complete" means complete **public per-case relationship evidence**, not knowledge
of unrecorded calls. Calls still require observed graph/trace edges. Service→pod
identity may additionally be derived from a hosted pod's public Kubernetes name,
using the established RQ1.1/RQ3.1 `pod_to_service` projection, only if the exact
service and pod have correctly typed case-local IDs. This is not an observed
Trace witness or a claim about Kubernetes ownerReferences. The offline audit
separates explicit, trace-observed and name-derived pairs, and records conflicts
or ambiguous namespace names excluded from the projection. An empty-Trace case
does not acquire invented call edges. Dense graphs retain all edges; their readability and eventual
VLM processor capacity remain separate checks, not assumed from source coverage.

`preset --evidence ... --name operations|relations_first|matrix|pairs --out ...` produces
an editable JSON tree. `operations` and `relations_first` move whole regions.
`matrix` is a gallery variant that changes several encodings—not a one-factor arm.
For a component-only intervention, edit just one leaf's `component` and keep all
geometry parameters fixed. Moving a tree subtree can affect siblings: compare
the emitted rectangles with `renderer.gates.compare`, not just config diffs.

### Three interchangeable topology encodings

- `graph.node_link` (C09): the reference dashboard's deterministic radial
  node placement and direct directed links. Its first two rings and link paths
  reproduce the reference-image code exactly; additional rings extend the
  same grammar for larger graphs. RQ3.8 projects pod-level calls to service
  edges only where public service→pod ownership is unambiguous; otherwise the
  pod endpoint stays visible. Raw calls remain in the common text ledger.
  Node→pod and service→pod use their separate deployment-group components unchanged.
- `graph.matrix` (C10): source rows and target columns, typed edge marks.
- `graph.edge_pairs` (C12): a separate graphical source→target tile for **every
  original edge**. A→B→C→A becomes A→B, B→C, C→A, not a spanning tree.

Pairs keep IDs, types, dependency roles, direction, self-loops, reverse edges and
multiple relation types. Repeated entities are redundant views of the same fact:
the first occurrence has `data-binding`, others have audited `data-binding-ref`.
The browser checks the displayed source/target/type against every original edge.
No edge sorting by anomaly or causal score, truncation, pagination or hidden scroll.

To replace only a graph's encoding, use the existing component operation:

```json
[{"op":"component","args":{"card":"G01","component":"graph.edge_pairs"}}]
```

The configured footprint must fit all tiles at the configured font. If it does
not, compilation fails before rendering. `preset --name pairs` explicitly creates
an edge-count-sized layout; it may be taller than the other presets. For a
controlled comparison, freeze a common sufficient footprint before substituting
components. Ownership overlays still require `graph.node_link`, because a repeated
pair endpoint is not a unique anchor; no arbitrary occurrence is chosen silently.

Example: `build/renderer_previews/edge_pairs_v1/calls_pairs/dashboard.png` and
`calls_network/dashboard.png` contain the same 58-edge development call graph,
same outer geometry, same canvas and same bound facts. `comparison.json` records
the actual differences. Pair tiles remove crossings, but reconstructing multi-hop
paths requires matching repeated IDs; neither encoding is assumed better for RCA.

Unknown encodings, duplicated/omitted cards, invalid ownership and oversized
panels fail. Long labels wrap; if the fixed footprint is insufficient, rendering
fails visibly. No automatic data deletion or global font reduction.

Example operations JSON (applied sequentially, evidence immutable):

```json
[
  {"op":"spacing","args":{"gap":24,"padding":28}},
  {"op":"component","args":{"card":"M01","component":"metric.line"}},
  {"op":"indexing","args":{"visible":true,"start":1}},
  {"op":"resolution","args":{"scale":1.25}}
]
```

```bash
bash src/renderer/scripts/render.sh operate --evidence evidence.json \
  --design design.json --operations operations.json --out modified.json
```

Every operation is validated and emits a geometry-change audit beside the new
design. Raster scale and logical viewport are separate operations. Ownership
connections are gray dashed lines labeled “observation of”, not causal arrows.

## Artifacts and validity

- `dashboard.html`: standalone offline vector/HTML dashboard, with embedded font.
- `dashboard.png`: actual Chromium screenshot at the configured DPR.
- `evidence.json`, `design.json`, `geometry.json`: reproducible public inputs.
- `manifest.json`: card/field-to-DOM mappings, overflow audit, hashes and timing.

The component library is React/TypeScript (`web/components/`); operations are
Python (`operations/`), because they transform the layout/design description
before browser rendering. Both are under `src/renderer/`; `scripts/` contains
only entry-point wrappers. Python source, bundle, dependency lock, CSS, font and
browser version are recorded for reproducibility.

Browser geometry checks are necessary, not a full proof of readability or VLM
perception. Field bindings cover the **projected DTO**, not every field in the
historical packet. The development adapter records its exclusions. Candidates
and RCA task text remain outside this dashboard. No MRR improvement is claimed.
Source PNG size does not certify post-processor token budget or readability.

New graph syntax still needs a component; parameterization covers this explicit
space, not arbitrary HTML/CSS generation. No user-supplied code is evaluated.
Ownership connectors currently require a node-link graph; paths that cross an
unrelated panel fail rather than obscure its evidence. General obstacle-avoiding
wire routing is not implemented. Sparse graphs can have substantial whitespace;
layout refinement is an explicit future design change, not automatic evidence removal.

## Grouped deployment component (C13)

`graph.deployment_groups` displays `node ID: {pod ID, …}` and
`service ID: {pod ID, …}`. Explicit brace groups wrap members without discarding
edges. It accepts only node→pod hosting and service→pod membership/instance edges;
calls cannot be substituted as deployment. Shared pods retain the same ID.
Network, matrix and edge-pair components remain selectable through the `component`
operation. `operations`, `relations_first` and `pairs` now default to brace groups
for deployment cards; the latter still uses pairwise tiles for call graphs.
For controlled comparisons, explicitly freeze shared geometry rather than comparing
different auto-sized presets.

The public adapter separates G02 (node/pod) and G03 (service/pod). `node_pod_map`
supplies observed hosting; `service_pod_map` supplies declared associations.
Complete Trace resource observations supply `has_instance` relations when the
same row binds `service_name` and `k8s.pod.name`. For hosted pods lacking such a
pair, the existing, deterministic Kubernetes pod-name projection supplies a
name-derived `has_instance` correspondence if the projected service is in the
public identity map. A name projection never overrides an explicit or observed
binding, and namespace-ambiguous names are excluded. It does not use selected
top-k trace rows, metric/log ranks, a model answer, or a private label. The
three sources are distinguished in the offline audit; G03 does not assert
ownerReferences or causal propagation.

Examples: `build/renderer_previews/deployment_groups_v1/aegislab_deployment/`
(node and service groups) and `aegislab_dashboard/` (complete dashboard).

## Regression commands

```bash
PYTHONPATH=src:RQs:. /home/lglsj/CanvasRCA/venvs/tools/bin/python -m pytest -q src/renderer/tests.py
RENDER_BROWSER_TESTS=1 PYTHONPATH=src:RQs:. /home/lglsj/CanvasRCA/venvs/tools/bin/python -m pytest -q src/renderer/tests.py
```

No inference qualification is implied by renderer tests. A future scientific
renderer snapshot needs separate model-input and experimental-contract checks.

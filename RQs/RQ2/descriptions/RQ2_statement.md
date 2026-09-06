# RQ2 — Dashboard design effects

> **RQ2. How do evidence selection—including deterministic RCA tools—card-level visual encoding, constrained spatial packing, resolution, and their interactions affect one-stage RCA accuracy, evidence grounding, attention allocation, robustness, and cost?**

RQ1.1 was an empirical representation study. After V3 processing restores the
frozen manifest, RQ2 reuses its 300 headline cases so design outcomes can be
paired with the same incident population. A separate deterministic-tool study
uses all 480 frozen RQ1.1 cases and keeps the saturated RE2 and OOD strata
separate in analysis. Old RQ2 rosters and protocols are not authorities.

RQ2 evaluates frozen Qwen3.8-27B and Gemma-4-26B-A4B-it actors. It does not train the Qwen3.5-9B Dashboard Composer, a scorer, an SFT adapter, or an RL policy. It studies one-stage RCA with at most one PNG. The two actor models inherit the RQ1.1 local runtime/client/scorer recipe. RQ2 owns a local prompt artifact, but its common scientific RCA wording is deliberately a minimal, hash-recorded adaptation of the selected SIRCL* prompt already used by RQ1.1. Only the variable metric-card count and RQ2 content/design-control semantics differ; the diagnostic method and output contract do not. RQ2 separately owns its dashboard grammar, design language, and analyses.

## Abandoned QA/perception branch

RQ2 no longer runs a packed-QA or perception endpoint. RQ1.1 already measured
direct and cross-region perception, and its case-aligned analyses did not show
that the available QA score was a stable positive proxy for one-stage RCA.
The stricter post-hoc subset whose displayed call-graph support touched the
accepted root family also showed no reproducible positive association on the
headline datasets. RQ2 therefore spends its budget on the actual RCA endpoint.

The RQ2-local packed-QA builders, schemas, scorers, and tests are preserved as
abandoned audit code. They are excluded from active configuration, smoke,
formal queues, D*/C* selection, verification denominators, findings, and
claims. Existing QA artifacts remain archived and are not reinterpreted.
This decision does not remove attention: every active RCA call still records
the registered same-call text and image attention diagnostics.

## Evidence cards and silhouettes

RQ2 treats dashboard construction as two distinct decisions:

1. **Evidence selection:** choose which label-blind public telemetry modules enter the dashboard.
2. **Visual composition:** choose how each selected module is visually encoded and where it is placed.

The selection unit is `EvidenceCardV1`, but a card is no longer synonymous with
one atomic fact. A human-readable card may contain several compatible facts:
four aligned metric series, several trace operations, several readable Denum
log patterns, or the concrete topology together with its propagation rows.
Atomic facts remain the audit and scoring units and belong to exactly one card.
Cards contain public facts only and record their entities, semantic role,
label-blind selection features, supported encodings, legal footprints, and
fact-inventory hash.

A selected card can and must be converted into exactly one `SilhouetteV1`.
“Silhouette” means the rectangular footprint occupied by that card's coordinated
visual panel. The panel may contain multiple aligned curves, multiple table
rows, a graph plus its exact edge ledger, or another compact coordinated view.
The card and silhouette share exactly the same facts and hash. A card cannot be
split across silhouettes or drawn twice, and separately selected cards cannot
be merged only after selection. The superseded one-fact-per-panel renderer is
retained solely as the explicit `sparse_atomic_control`; it is not the default
design language and cannot be selected as D*.

The dashboard is an `m×n` square grid. Every silhouette declares an integer width and height, such as `1×1`, `2×1`, or `3×2`. Its renderer must pass local clipping before composition. The host then places complete silhouettes with hard in-bounds and non-overlap constraints. Resolution is controlled by pixels per grid cell, so the same logical dashboard can be measured across a continuous pixel-density curve without changing its card geometry.

Grid occupancy and human-readable density are audited separately. A silhouette
can occupy cells while still containing truthful internal whitespace when a
case has only one retained log template or few call edges. The renderer uses a
fixed `1.18` typography readability baseline before applying the registered
relative legibility factor, separates titles, context, legends and axes into
non-overlapping bands, and uses otherwise empty sparse-log space to visualize
the already-present LOG-R rate comparison. It never repeats or invents facts
merely to remove whitespace.

Filling the canvas is a secondary packing objective, not evidence utility. The Composer first selects a legal evidence set, then minimizes unused cells and fragmentation for that fixed set. It may not add irrelevant cards simply to make the page look full.

Dense display is registered separately from ordinary packing. Normal FULL uses
the inherited top 12 metric series. The dense condition uses the same
label-blind ranking to retain top 24 and overlays up to eight series per plot.
It is compared against a Dense Text twin containing exactly the same expanded
facts. Dense versus normal is intentionally an unequal-content comparison;
within-pair Canvas versus Text comparisons remain equal-information.

## Design factors

- **Content:** full evidence; 25/50/75% minimum-silhouette-area budgets selected by balanced M/R/L/G coverage, label-blind salience, entity diversity, or opaque-hash random control; and one explicit dense top-24 metric condition paired with an equal-fact dense text twin.
- **Card encoding:** aligned robust-deviation metric lanes, heatmap rows, or
  shared-axis color/marker overlays with exact legends;
  multi-operation trace dumbbells/paired bars; multi-template log timelines or
  time matrices; and topology graph/matrix/edge table coordinated with exact
  propagation rows.
- **Footprint allocation:** compact, balanced, or detail-first constrained silhouette allocation, with every capacity downgrade explicitly recorded.
- **Packing:** modality-grouped, entity-grouped, salience-first, or topology-centered deterministic packing.
- **Ordering:** stable anonymous ID, label-blind salience/onset, or topology breadth-first order.
- **Coordination:** no extra cue, a shared anonymous-entity cue, or a shared relative-time ruler.
- **Grid geometry and legibility:** registered `10×10`, `12×8`, and `16×6` capacities with logical cell size, raster scale, relative font/mark scale, and gutter varied separately.
- **Metric scale:** per-card raw scale or common robust scale.
- **Skin:** canonical versus colorblind-safe non-semantic palette.

The formal panel uses registered continuous anchors plus a constrained exact D-optimal sample of legal programs. Development screens 48 programs; independent confirms 16 frozen decisive programs. It is not an exhaustive Cartesian search and does not claim a global optimum over every imaginable dashboard.

Service, pod, and node identities remain case-local numeric IDs. Every result preserves `fact_id → EvidenceCard → Silhouette → pixel bbox`, selection and placement actions, budgets, occupancy, renderer and prompt hashes, attention diagnostics, and RCA outcomes. Attention remains correlational. RQ3, not RQ2, will formalize contribution identification. Later SFT/RL may use these exact typed actions while keeping the RCA actors frozen.

Downstream transfer also includes an equal-fact compact structured-text
control. It separates concise nonvisual serialization from true spatial
organization, so a dashboard is not credited merely for avoiding verbose
natural-language repetition.

RQ2 additionally crosses four deterministic, label-blind public-evidence
selectors with Text and Canvas twins. This reveals whether metric-, trace/graph-,
log-, or balanced fusion tools improve RCA, and whether their benefit depends
on representation. It does not turn RQ2 into a tool-using multi-stage agent:
selection happens before the single frozen Solver call, uses a common bounded
budget, and creates no extra inference calls.

RQ2 as a whole—not each subexperiment separately—has a 40,000-call ceiling.
The registered design, content, transfer, and tool studies require at most
31,560 calls after the 480-case V3 roster is regenerated.

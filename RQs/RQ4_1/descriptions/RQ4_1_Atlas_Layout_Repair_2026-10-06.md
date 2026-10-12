# CONTRAST_ATLAS layout repair — 2026-10-06

The user explicitly authorizes refactoring this arm until its complete dashboard
fits the existing canvas limit. This amends the wildcard's candidate-row layout
and its earlier stop-at-design-infeasibility boundary for this repair only.
The other methods, facts, statistics, models, call budget and experiment gates
are unchanged. Bulk CPU qualification, GPU smoke and formal execution stay
paused while the user reviews the examples.

## Cause and replacement

The original layout allocated a separate eight-cell row to each entity and
padded every short row with empty cells. Each row used the height of its tallest
card. The resulting heights exceeded 8,192 px even though the total area of all
cards fit comfortably inside the permitted canvas.

`candidate_ordered_contiguous_columns_v2` replaces that layout with eight
columns at the original width. Read each column from top to bottom, then move
left to right. Panel indices follow this reading order. Candidate identities
come first; entity groups follow the original candidate order, with original
record order inside each group. Global/multi-entity observations remain global.

A same-entity source card and its derived quantile cards form one indivisible
bundle. Bundles are partitioned into contiguous columns with a deterministic
minimum maximum height. They are not sorted by anomaly, label or model output.
Multi-entity source panels retain their global location and their per-entity
strips retain their entity/signal identities and audit source mapping.

Original card contents and widths are identical; their allocated heights never
decrease. Derived cards retain their original fields, labels, color scale and
height rule. Font 18, scale 1, gap 16 and the 8,192×8,192 cap remain unchanged.
Only end-of-column slack is unused; no entity row reserves seven empty panels.
This uses the existing unified renderer's row, column, spacer and registered
components. No shared component or renderer semantics are changed by this
atlas repair. The separate prior QA badge repair retains its own record.

## Layout sizing and previews

Targeted layout sizing (not the paused full CPU qualification) covers all
220 registered cases:

| Dataset | Fits | Height range, px |
|---|---:|---:|
| AIOPS-2022 | 60/60 | 4,935–5,805 |
| AIOPS-2025 | 60/60 | 3,058–5,744 |
| AegisLab | 100/100 | 4,631–5,971 |

Every original card is present exactly once and unchanged, with no reduced
original dimensions. All 155 previously materialized atlas evidence packets
match the new packets exactly; only design/layout and audit layout metadata
change. Derived quantile computation and peer membership code are unchanged.

The three existing gallery cases render at 8,192×5,169, 8,192×5,744 and
8,192×5,392. The maximum-height case also renders at 8,192×5,971. Browser
geometry audits for these four previews report no issues. Source/contrast
card crops were opened for visual inspection. These previews do not establish
processor readability, full CPU qualification, GPU speed or RCA performance.

## Preservation and remaining work

Keep the old failed layouts and source snapshot under
`results/comparison_coding_v1/atlas_layout_repair_v9/before/` and the v7 failure
artifacts. Windows gallery folders retain their original rejected designs in
`旧超限设计/` alongside the new dashboard. The new targeted regression is written
but not run, respecting the user's instruction to review images before tests.

No model calls, GPU work or bulk CPU tests are started. After user review, only
affected and pending checks require qualification; retained prior passes are
not replayed. A forward source freeze is required before continuation.

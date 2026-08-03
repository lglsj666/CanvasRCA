---
name: dashboard
description: Work on the telemetry dashboard renderer — preview cases, change a DashboardConfig axis, review legibility, update goldens. Use whenever editing anything under RQs/vlmrca/render/, choosing RQ1 design-space levels, or when a rendered dashboard needs checking before an experiment runs.
---

# Dashboard renderer

The renderer is this project's contribution: it decides what the VLM can even
see. A bug here costs accuracy silently — nothing raises, the numbers are just
worse. So every renderer change ends with looking at the output.

## Contract

`compile_dashboard(view, cfg) -> (png_bytes, manifest)` in
[RQs/vlmrca/render/dashboard.py](../../../RQs/vlmrca/render/dashboard.py) is **pure and
deterministic** in its two inputs. Preserve that:

- No `Date.now()`-style nondeterminism, no unseeded layout, no dict-iteration order dependence.
- Graph layout uses `spring_layout(seed=17)` over a sorted node list. Keep it seeded.
- It takes a `CaseRenderView`, never a `DataCase`. The view has no `ground_truth`
  field by construction — that is the leakage guard, do not add a bypass.

## Preview a case

```bash
source scripts/env.sh
python scripts/render_gallery.py --dataset re2_ob --n 8 --contact-sheet
```

Writes PNGs, per-case `*.manifest.json`, and `index.json` (which *does* carry the
label, so you can check whether evidence for the true cause is visible).
Then read the images — with the Read tool, or hand them to the
**render-reviewer** agent, which also runs the perception probe.

## The RQ1 design space

Every axis is a field on `DashboardConfig`. Adding a rendering behaviour without
a config field makes it un-ablatable, so add the field first.

| Axis | Field | Levels |
|---|---|---|
| A KPI selection | `panel_budget`, `ranker` | 8/12/20 · `ksigma`/`robust`/`coverage` |
| B layout | `layout`, `grid_cols` | `small_multiples`/`overplot` |
| C topology | `topology`, `topology_labels`, `max_topology_nodes` | `none`/`plain`/`colored` · `numbered`/`names` |
| D annotation | `shade_fault_window`, `annotate_extremes`, `normalize_panels` | on/off |
| E resolution | `long_side_px` | 1024/1568/2048 |
| F aux panels | `show_logs`, `show_traces`, `show_legend_table` | on/off |
| G modality | (prompt-side) `modality` | `hybrid`/`image_only`/`text_only` |

`tests/test_renderer.py::test_config_axes_change_the_output` asserts each axis
actually changes the image. A no-op axis is a broken ablation.

## Review checklist

Before accepting any renderer change:

1. **Legibility** — no font below `style.MIN_FONT_PT` (7pt); no clipped or
   overlapping text; captions sit *below* their axes, not on the data.
2. **Colour carries meaning** — red is reserved for `|z| >= HOT_Z`. If nearly
   every trace is red, the threshold is wrong and colour is decorative.
3. **Scales discriminate** — anomaly scores span orders of magnitude, so topology
   nodes are shaded by within-case *rank*. A linear scale renders every node but
   the worst white; `log1p` saturates a cluster of high scores to one colour.
4. **Nothing silently dropped** — truncated topologies must print "N services hidden".
5. **Panel manifest present** — every panel returns its manifest entry with a
   stable `panel_id`; the RQ2 zoom tools address panels by that id.
6. **No leakage** — run `pytest tests/test_no_leakage.py`.
7. **Speed** — under 5 s/case (M1 gate).

## Updating goldens

`tests/test_renderer.py::test_golden_hash_stable` pins the render hash. When a
change is intentional:

```bash
rm tests/goldens/<name>.md5
pytest tests/test_renderer.py -q     # re-records
```

Then review the new image and add an entry to `plans/design_decisions.md`. Never
re-record a golden without looking at what changed — that is exactly the silent
regression the test exists to catch.

## Gotchas already hit

- Timestamps are inconsistent: metrics in seconds, logs in nanoseconds, RE2-OB
  traces leave `timestamp` all-NaN with the real clock in `startTime`
  (microseconds). Use `panels.resolve_time_seconds`, which picks whichever
  column and unit scale actually overlaps the metric window.
- A perfectly flat baseline makes z undefined. `kpi_select` floors the spread at
  a fraction of the series' own magnitude and clips at `Z_CAP`; without that a
  constant-zero counter scores ~1e9 and swamps the ranking.
- Several datasets (RE2-OB) have no error-level log lines at all, so the log
  panel falls back to volume shift. Do not "fix" an empty error table by
  widening the regex until it matches informational lines.
- Metric names in some datasets are long (`hubble_http_request_duration_p50_seconds`)
  and overflow panel titles. `_elide` shortens from the middle, keeping the tail
  that distinguishes one variant from another.
- Plain top-K selection is redundancy-blind: on AegisLab it filled all 12 panels
  with HTTP latency percentiles of one request path while the true cause (a
  MySQL fault) got no panel at all. `max_per_family` / `max_per_service` cap
  that; both default on, both settable to 0 to recover plain top-K for ablation.

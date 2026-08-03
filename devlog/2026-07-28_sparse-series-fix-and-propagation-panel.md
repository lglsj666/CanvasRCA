# 2026-07-28 — The metric grid was blank, and onset is a signal we never computed

Session prompt: *"Understand the latest status and improve the dashboard design.
If you look at the dashboard, most of them are just a single bar in the plot with
y axis is different, and selected metrics. Can we try construct an anomaly /
failure propagation graph or tree, and emphasis on the temporal and topological
shift in the design."*

Both halves of that turned out to be right, and the first half was worse than a
design complaint — it was a bug report.

## The single bar was three bugs

The panels really were empty. `metrics_df` is a pivot over a union timestamp
index, so a column holds values only on the timestamps its own scraper wrote: on
AegisLab, 8–96 valid samples in a 1064-row frame, and 10 for the HTTP latency
family. `ax.plot` breaks a line at every NaN, so those ten samples drew ten
zero-length segments. The only ink left on the panel was the fault band, and that
band had collapsed to one sample wide (median 2.6% of the window) because
`infer_fault_window` expanded in row space, where a single NaN neighbour halts
the walk. Meanwhile `score_series` accepted any column with three non-NaN
baseline points, and three samples of a slow counter look flat, so those columns
scored `>=999z` on noise and won the panel budget — a quarter of all v0 panels
carried the sentinel. The least drawable columns were the most likely to be
drawn.

Fixed all three (DD-17). Measured on AegisLab v0: sentinel share 21% at n=40 (was
25%), median band width 2.6% → 37.6%, and **injected-service panel coverage 66% →
77.5%**. That last one was not a goal. The DD-11 pathology fixed itself as a side
effect: on `ts0-mysql-partition` the true `mysql` cause used to get no panel at
all while twelve HTTP latency percentiles filled the grid — it now holds two.

**This is a live confound for DD-16.** The `image_only` arms were scored against a
dashboard whose AegisLab metric grid was essentially empty; that arm was
measuring the topology thumbnail and the two aux tables. The efficiency claim
isn't refuted, but it was measured on less image than intended.

## Onset, and the propagation panel

Every ordering the dashboard had was by magnitude — panel rank, node shade,
legend `z=`. Magnitude routinely inverts origin and victim: a saturated
dependency moves its own metrics a little while everything queued behind it moves
a lot. Order of arrival separates them, and nothing computed it.

`vlmrca/render/onset.py` computes per-service onset from traces (binned p95 span
latency, first persistent crossing of mu+3sigma) with a metric fallback for
services that emit no spans. Traces are the only usable clock here: AegisLab's
metrics arrive every 15 s and its inferred fault window is a median 12 s wide,
which is one sample and orders nothing. The panel (`topology="propagation"`,
presets `prop12`/`prop30`) puts services in rows ordered by onset, earliest at
top, on the same elapsed-minutes axis as the metric panels, with call-edge arrows
and a per-row readout of onset, peak z and source.

## The measurement that killed the premise (and rebuilt the panel)

Truncation was originally by earliest onset — the inverse of the topology
panel's rule, since a quiet early origin is exactly what magnitude truncation
throws away. The pilot looked like a win: on `ts0-mysql-partition`, `mysql` went
from having no panel at all to row 1, and across 12 cases on four datasets the
injected service was present in 8 and top-3 in 5 (AegisLab 1, 2, 4; RE2-OB
1, 1, 1).

Then I ranked the same shown services by magnitude instead, on 30 AegisLab cases.
**Magnitude wins, clearly**: median rank 2.0 vs onset's 5.5, top-3 79% vs 42%,
worse on 15 of 20 discordant pairs, Wilcoxon p = 0.014. Onset-based selection had
also thrown the true cause out of the panel on 6 of 30 cases.

So the premise was wrong in the form I built it, and the mysql result was an
anecdote — the twelve-case pilot was too small to see the reversal. This is the
fourth time in this project's log that a clean pattern on a small slice did not
survive the larger sample.

**Rebuilt as: select by severity, display by onset.** Rows are the most anomalous
services that have a detected onset, drawn in onset order. Severity is the better
filter and now does the filtering (coverage 80% → 83.3%); onset stays as the
display axis because it carries information severity does not, and because row
order plus dot position are what express the temporal story at all. What can be
claimed: the panel puts onset timing, its source, and call edges where an
unreadable 104-node hairball used to be, and its rows contain the true cause 83%
of the time. What cannot: that earliest onset means most likely cause. On the
primary screening dataset it is significantly worse than the ranking the
dashboard already had. Whether the added evidence helps a *model* reason is a
different question — sd 0.36, MDE ~0.10 at n=100, screening waits for Sonnet-5.

## Two calibration lessons, both from measuring rather than reasoning

**The metric onset path needed a far stricter rule than the trace path.** At a
3-sigma floor, dozens of services in a 104-service case "onset" in the first
seconds on their own baseline noise and filled every row ahead of the services
that actually broke. Needed a score floor of 10, half-the-peak threshold,
persistence, *and* a crossing after the baseline region. That last clause was its
own bug: crossings inside the baseline gave onsets at "+0.0m" — a fault starting
before the window did — which sorted straight to row 1.

**The trace baseline must end at the fault window, not at a fixed leading
fraction.** Cutting earlier gives onsets room to spread out and order themselves,
which sounds strictly better and measured worse: these traces carry real
pre-injection wander, an earlier cut reads it as onset, and on the mysql case it
promoted eight merely-noisy services and pushed `mysql` out of the panel
entirely, from first place. The cost is that onsets bunch after the cut — which
is mostly honest. An injected fault reaches what it reaches within a bin or two,
and call-graph propagation is sub-second; no 10 s binning resolves it. The panel
shows which services were affected and the coarse order, not a causal chain, and
the guide text now says exactly that.

## What the vision review then found

The render-reviewer agent passed the panel — 8/8 perception probes matched, no
clipping, no overlap, every metric panel showing real connected data across
2-to-14-row cases and three datasets — and returned three things worth acting on.

Its top finding was the one I had just found independently from the other
direction: requiring an onset to appear in the panel drops the *most severe*
candidate when that service's onset is undetectable, making the panel strictly
worse than the Service index it replaces. Fixed by letting high-severity services
take rows labelled "no onset", and by ranking on the dashboard's own per-service
anomaly score rather than the onset-derived z. AegisLab coverage 83.3% → **93.3%**.

It also found the arrows tangle in dense cases (eight arcs crossing in a 130px
band, traceable only at 4x zoom) — now only edges whose ends onset at *different*
times are drawn, which is both the readable subset and the informative one — and
that trace-derived and metric-derived z sit on one visual scale without saying
they are not comparable, now stated in the caption.

**And it found a bug in v0** that every AegisLab run to date has carried: in the
Service index, a long name in the left column prints through the right column's
row number (`...z=1521ts-price-service`). The cause is a third instance of the
project's recurring defect, one level up from the previous two: the side-column
width formula apportions the grid by ratio and ignores `wspace`, and matplotlib
pays for gutters by shrinking every column. It overstates the column by 23–25%,
so the legend budgeted 38 monospace characters into room for 31. The metric-panel
titles use the same geometry and survived only because `TITLE_CHAR_EM` had been
calibrated against a rendered image and absorbed the error — a fudge factor
hiding a bug in the thing it was calibrated against. Now derived properly, with
two tests: one pinning the prediction against a real `get_position()`, one
asserting every legend row fits its half-column (DD-20).

## A leak that hadn't fired yet

`CaseRenderView.from_case` filtered metadata against a list of banned key names,
matched exactly. AegisLab passes `injection_ground_truth` — the answer, spelled
out — and AIOPS-2025 passes `service`, `fault_description`, `key_observations`
and four more. None matched a banned name; all reached the view. Nothing read
`view.metadata`, so nothing leaked, but `node_pod_map` (which this session wanted
for pod-to-service reconciliation) lives in that same dict.

Now a whitelist (DD-19), asserted structurally, and `tests/test_no_leakage.py`
runs over all four datasets instead of RE2-OB alone — the hole was invisible for
precisely as long as that file loaded only the one dataset that happens to carry
none of these keys. Same lesson as the four v4 render bugs: a blacklist excludes
only what someone thought of; a whitelist fails closed.

## Measured but not acted on: HOT_Z

Red is meant to mark severe excursions and fires on 98.5% of AegisLab panels, so
it carries no information. But the measurement refuses a fixed replacement:
median |z| among *selected* panels is 17.8 on RE2-OB, 177.6 on AegisLab, 206.8 on
AIOPS-2022. No single constant discriminates on all three. Left at 10 and
recorded as an open RQ1 axis — the candidates (within-case rank, per-dataset
constant) are rendering-behaviour changes deserving their own axis and their own
screening, not a free ride on this version bump.

## State

`RENDERER_VERSION` 4 → 5; the render cache invalidates, intentionally. 65 tests
pass, including 12 new onset tests, two new layout-geometry tests, and the
leakage suite across four datasets. New: `vlmrca/render/onset.py`,
`scripts/selection_stats.py`, `tests/test_onset.py`.

## Next

1. **Re-run the DD-16 modality comparison** on the fixed renderer — the previous
   `image_only` result was measured against a blank metric grid.
2. The **Sonnet-5 reference** (still held) — now more informative, since both the
   metric panels and the propagation panel changed what the image contains.
3. `HOT_Z` as a proper RQ1 axis.
4. AIOPS-2022/2025 onset coverage: the injected service often isn't in the call
   graph at all, which bounds what this panel can do there.

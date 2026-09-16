# DD-RQ3-SEARCH-19 — Preserve ranked evidence and expose node resources

Date: 2026-09-12. Status: completed train-development batch, not promoted.

SEARCH-18's eight-slot replacement lost useful context and added weak signals.
The next intervention is additive: `node_overview_v1` keeps the unchanged
ranked-membership top-eight M facts and adds the highest native-ranked CPU
and memory metric for each public node having that family. Iterate all nodes
in numeric-ID order; deduplicate exact fact IDs. There is no choice based on
private root/fault type, no deletion of baseline evidence, and no promise that
one resource series describes the node's entire behavior. Classification uses
the already registered public SEARCH-18 ontology. Missing families add no
invented series. More than 64 resulting metric facts is an explicit capacity
error, never silent truncation. Preserve R/L and bind G to actual selected
owners via the existing public context rule.

Use the existing true line-chart painter, a 12x12 grid with 320px cell edges
(3996x4088 PNG), and a left M card with R/L/G stacked on the right. The
requested horizontal ratio is .6; measured constraints may project it to a
feasible ratio, recorded in the manifest. Do not force the old square panel
budget to hide newly selected facts. Metrics are ordered by owner granularity, numeric owner and
metric name to keep the same node's measurements adjacent; labels, values,
units, 64 bins and native M-series identifiers are unchanged. This row-order
option is explicit and defaults to legacy fact order for all previous runs.

Both paired conditions use this larger layout and owner ordering: ranked M8
control versus additive overview. Thus the new control is NOT byte-identical
to old small-canvas controls; old control outcomes are not substituted. Same
static guide, text-only candidate list, Qwen checkpoint and nonthinking
services-first request recipe. All diagnostic content remains in one image;
no new attention. Native processor token preflight must admit image plus
prompt and 8192 output allowance without changing the model recipe.

Begin with all twelve existing train previews and CPU tests, opening actual
PNGs before any calls. Test all-node coverage, unchanged old fact subset,
deterministic ties, source immutability, new row order and old default-pixel
regression, bounded capacity, candidate transport and geometry. Maximum next
development batch is 24 calls if previews and preflight pass. No validation,
eval, Composer or training calls are authorized by this small batch alone.

This checks whether exposing node CPU/memory beyond a global top-k helps. It
does not isolate every layout, content and pixel-budget effect relative to
SEARCH-18, nor establish that a public node anomaly is the actual origin.
Preserve all failures and then widen the train cohort before validation.

## CPU and image qualification

244 tests passed in 74.14 seconds. Initial new ordering fixture failed because
it omitted mandatory source geometry; fixed the fixture to supply actual
numeric bins/baseline, retaining the production fail-closed check. Both test
reports remain (`cpu_node_overview_v1.xml`, `cpu_node_overview_v2.xml`).
Functional core source count 5965. All 24 previews passed independent
additive-selection, original-fact, node-family coverage, owner-row order,
candidate prompt-only and pixel containment checks. Two original-resolution
PNGs opened, A22 C034 and A25 8AB. Overview contains 19-20 M rows for A22,
29-30 for A25. Two legacy default PNGs rerendered byte-identically despite the
new opt-in row-order field. No native defaults or prior artifacts replaced.
Gallery summary hash:
`463c90f2384d002307202e537b19642b82cb522225572c2a95b4f98205e21e69`.

## Outcome and decision

24/24 calls completed in 349.778 seconds under work-spec
`1e47dba0671dd05ddd51d38cc889c23e3a2887b854938c226438dbe9f82f645f`.
Independent native/artifact/partial-input audit passed. Actual image tokens
16,002; inputs A22 17,754/A25 17,651; maximum output 379. All five returned IDs
were distinct legal candidates, candidate lists were prompt-only, attention
disabled. A22 control/overview MRR .2222/.3750, A25 .2000/.2417. Three repairs,
one break, eight ties. Six-case paired contrasts are inconclusive (Holm p=1).
No evidence of full-data target attainment, and input cost is higher than the
old small-canvas recipe. Keep the additive design as a development candidate,
not a promoted pipeline. Multiple answers still conflate low-variance changes
with capacity exhaustion and invent ownership/hosting. Check numerical visual
encoding, then expand train evidence before any validation choice. No eval or
training has run in this search stage.

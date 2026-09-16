# DD-RQ3-SEARCH-26 — Period-shift ranking and entity coverage

Date2026-09-12. Provisional, prospective train-only registration before calls.

## Motivation and source
SEARCH25 added observed trace rates but produced no consistent RCA gain.
Current native metric priority comes from peak deviation over source curves;
the already compiled SIRCL-style MET-Z `deviation_sigma` instead measures
absolute regular/current mean difference divided by baseline standard deviation.
These are different estimands, not interchangeable names for the same score.
Inspect `renderer/panels.py:render_metric_panel` for the actual inherited
definition. No new injection-time anchor, raw processor or numerical statistic
is introduced. Ranking uses the retained public MET-Z projection, not private
root/fault information, and is not claimed to reproduce the complete SIRCL
system or its original unrounded ranking exactly.

The initial public-only24-case CPU probe suggested changed selection, but its
parser was subsequently found to omit k/M/G-formatted scores. Its numerical
overlap counts are not evidence for the corrected selector; a versioned probe
is required below. No accuracy is used to choose individual series.

Related reading: [Brendan Gregg's USE methodology](https://www.brendangregg.com/usemethod.html)
separates resource utilization, saturation and errors, and discusses both
resource and latency-oriented investigation. This supports checking diagnostic
meaning, not interpreting a large score as demonstrated exhaustion. Its
80% anecdotal claim is not an RCA benchmark or a predicted VLM gain. Publisher
links to ACM Queue/CACM returned403, so only the accessible author explanation
was read; no new conference/publication status is asserted. Google's
[SRE monitoring chapter](https://sre.google/sre-book/monitoring-distributed-systems/)
was screened for monitoring vocabulary, not used as algorithm evidence.

## Two fixed policies
Both start from the full public pool, keep the SEARCH23 node CPU/memory
overview, same trace/log selectors and same entity-dependent graph/onset rules:

- `metz_overview_v1`: eight metric slots by descending finite nonnegative
  MET-Z deviation; ties by native metric rank then fact ID. Missing/nonfinite
  MET-Z is placed after all usable scores and retains native ordering.
- `metz_coverage_overview_v1`: the same score, with an unrepresented metric
  owner preferred among usable entries before allocating another slot to an
  already represented owner. No dataset, natural name or private label branch.
  Missing-score entries do not displace usable duplicates just for coverage.

Then append the same native-ranked CPU and memory series per public node,
without duplicate facts. Eight is the primary metric-slot budget, not a claim
that the additive overview contains only eight curves. Capacity stays64; an
overflow fails, never silently drops series. Candidates remain the full public
enumeration in the prompt only. Existing source units, bins, statistics, panel
IDs and owner typing stay intact. Edges/onset/membership may change because
their existing selection is conditioned on selected entities; those changes
are part of the evidence-selection intervention and are audited explicitly.

Fixed: owner-header renderer and layout, one PNG, existing evidence-bound
membership prompt, card_nonthinking_v1 profile,8192 maximum output, no attention.
No rate projection from SEARCH25, no new USE prompt or visual semantics.
The baseline is the completed SEARCH23 owner-header24, not a rerun of it.

## Population, cost and acceptance
Same24 isolated train cases as SEARCH23:12 each AIOPS-2022/2025, offset6,
unchanged connected-group split. Two new conditions, at most48 Solver calls,
concurrency4,3600 seconds, sequential local owned server. No validation/eval,
Composer generation, SFT or RL. CPU tests and actual train PNG review precede
execution; source facts/selection/source-time/labels and complete inputs checked.

Register four exploratory paired contrasts: each new condition versus the
owner-header reference within each dataset, Holm across all four, Pratt
Wilcoxon and paired dz, no CI. Report MRR, actual input/image/output tokens,
RR repair/break/tie, selected coverage, capacity failures and model outcomes.
Inspect all complete answers and actual conversations; no correctness retries.
Preserve negative results, source/config hashes, prompts and every call.
Tiny-subset gains cannot meet the final targets or trigger training/eval alone.

## CPU review attempts
Initial targeted tests:24 passed,one fixture assertion failed because an
overview node already selected by coverage must not be appended twice. The
assertion now tests set coverage and uniqueness rather than assuming ten rows.
Independent logic review also found that absent MET-Z must retain native
ordering even in the coverage branch; restricted the owner preference to
usable scores and added regression coverage for all-invalid pools. No model
call was initiated; the original failed XML is retained.

The full318 tests passed, but actual-source inspection then found suffix
scores such as70.8k and334707524.3G. The initial new parser had incorrectly
treated these valid finite values as missing. Stopped CPU galleryv1 before
any Solver call; preserved its partial images with NOT_QUALIFIED status.
The corrected parser expands the inherited decimal k/M/G notation, checks
finiteness after expansion, and keeps unavailable/invalid values last. Added
real-value and valid-zero regression tests; rerun the probe and full suite.
This does not change the stored MET-Z values or reinterpret enormous scores
as physical saturation. A finite score from a near-constant baseline can be
huge; that remains an explicit limitation of this ranking hypothesis.

The corrected324-test suite passed. Actual galleryv2 found a separate painter
capacity problem: `M1553  SERVICE 188` needs269 pixels including margins,
while the old owner-header column was capped at260 regardless of canvas width.
Registered `owner_header_width_v3` measures the complete fixed-font owner and
enlarges the label column only when necessary, reserving at least192 pixels
for its plot. It never shortens an ID, changes numerical coordinates/values,
or drops a fact; horizontal plot pixel locations can shift for the enlarged
column. Existing v2 behavior remains available. New configv2 differs only in
this label-width policy. Before calls, require original baseline pixel replay
and exact replay for previously feasible MET-Z images where label width was
already sufficient; document newly feasible images separately. No extra
calibration calls or hidden case-specific rendering branch.

Final CPU qualification:327 tests passed in75.437s,source5983 lines.
Galleryv3 rendered48/48. Independent replay passed all48 source/ranking/bin,
fact/geometry and pixel checks; all24 native baseline PNGs remain exact under
the old and new width policies, and all47 formerly feasible MET-Z images
retain exact PNG bytes. One previously failed image becomes feasible.
Full static prompts/candidate lists and source geometry stay identical to
SEARCH23. Opened actual A22 long-header, A25 standard and sparse A25 images;
recorded viewer scaling in review.json. Qualified gallery summary hash:
`261c1968d2c78d635e0b6c533140e812f84974315fec60e73a05e91ff9b91ac6`.
Proceed with the registered48-call train-only development batch, not full eval.

## Outcome and decision
Completed48/48 calls in586.506s; all full answers and persisted artifacts
reviewed. MET-Z MRR A22/A25=.363889/.2875; MET-Z+coverage=.305556/.229167;
native owner reference=.506944/.440278. Four paired exploratory Holm p-values
are .53125/.375/.375/.125 in that row order. Input/image tokens unchanged;
max433 output,all legal top-five JSON,no failures/truncation. Not promoted.
These are negative small-train-subset findings,not target attainment or a
universal ranking. Source-backed interpretation errors and full CPU failure
history: `../results/search_first_v1/metz_development_v1/logs/20260912_review.md`.
No owned server,validation/eval or training phase remains active.

# RQ3.20 v2 — lossless overview compression

Date: 2026-10-05. The user explicitly requests modifying RQ3.20 to try to meet
the original 0.40 first-input, 0.85 combined-input plus 512, and 50%-per-dataset
applicability gates. This revision performs source changes, static checks and
complete CPU/actual-image feasibility, then stops. No GPU or model calls.

The v1 frozen archive, all source inputs and failed results remain untouched.
v2 has separate preparation/results, and the original strong FULL_TEXT baseline,
roster, five arms, source facts and numerical spellings remain unchanged.

Representation changes are engineering to enable the registered acquisition task:
flatten repeated nested field names into explicit column paths; share constant
fields; use source-verified field references; structure previously prose-wrapped
JSON observations; encode existing window summaries as keyed records; group typed
edges by source and target list. All overview facts, entities, units, direction,
phases, counts and ordering within observation lists must reconstruct exactly.
Arrays, observations and candidates cannot be truncated, rounded or resampled.
Original source text and complete retrievable bundles remain verbatim in the ledger.
The advertised fetch catalogue contains only packets with values deferred from the
overview: metric vectors, AUX vectors, sampled pairs and deferred component series.
Purely redundant Trace/log summaries remain available in the overview and original
ledger, but are no longer advertised as useful new details. The budget gate must fit
at least one complete informative packet, not merely a short repeated summary.
No compressed binary, base64 evidence, opaque dictionary coding or numeric notation
changes are used. Column/readout guides are counted in the real request budget.

Both text and visual workflows receive the same compressed non-graph overview and
the same detail budget. Graphs still use the existing unified renderer node-arrow
components, complete edge sets, current font/layout and processor pixel limits.
Readability and source reversibility are CPU requirements, not evidence of unchanged
model behavior or RCA performance. New request shapes require fresh qualification.

Qualification includes an independent decoder, malformed/ambiguous input checks,
all-220 source parity and processor counts, valid whole-bundle budget packing, and
actual PNG counts if the text screen passes. Inspect representative actual plots;
never infer the visual budget from text-only savings. Existing failure denominators,
cost definitions and scientific tests are not relaxed.

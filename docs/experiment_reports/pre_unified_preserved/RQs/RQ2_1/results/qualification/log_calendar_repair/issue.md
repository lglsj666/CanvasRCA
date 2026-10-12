# Log-calendar projection — 2026-09-08

Status: repaired and qualified; formal continuation resumed at 20:31 UTC. Formal admission was
safely stopped and in-flight work drained before modifying source or inputs.

The fourth full-case audit (INC-881461551C98) found an embedded JSON `time`
field whose year/month entered numeric previews despite display truncation.
A broader selected-packet check also found Redis calendar dates in log text.
This is public-event calendar metadata, not demonstrated exposure of the true
fault injection time or a root label. It nevertheless violates the registered
relative-time-only model input boundary. No private outcome was used to decide
the correction. The prior zero-match numeric ISO scan alone was insufficient:
it did not cover textual month names or split numeric placeholders.

Correct only identifiable calendar spans and corresponding numeric previews.
Preserve diagnostic values, counts, relative bins, source/template identifiers,
pool selection and all source graphs. Do not replace removed previews with
new evidence or introduce a model-facing explanation. Common T/V projection,
not an individual policy, owns the correction. Archive changed prior requests
and retain unchanged requests byte-for-byte. Original RQ1.1 remains untouched.

Final scope: 173 cases / 500 policy packets; 510 completed inputs superseded
and 4,032 completed records preserved. The 225 design-infeasible markers are
zero-call signature refreshes. Nine sanitizer tests, 48 RQ tests, twelve native
processor preflights, actual PNG review and 24/24 fresh/migrated input-file
comparisons pass. The final execution gate has no blockers. A 20:42 check
found 147 new completions, no infrastructure errors and 99% sampled GPU load.
The first corrected T and V records both stopped normally with both attention
phases; full responses are retained in `live_followup.json`. Their unsupported
diagnostic assertions are model behavior, not a reason for further resampling.

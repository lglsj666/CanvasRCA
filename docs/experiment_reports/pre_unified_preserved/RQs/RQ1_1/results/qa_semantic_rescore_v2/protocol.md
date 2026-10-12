# RQ11QASemanticRescoreV2 — offline revision, 2026-09-11

User-authorized repair of v1; zero new model calls. Preserve the full v1 source
directory, scores and report as a reproducible predecessor. Source inference,
questions, preparation, hashes, RCA scores and the existing eight-case paired
infrastructure mask remain unchanged. No new exclusions.

Primary endpoint remains all requested regional answers correct without requiring
R3 overall. Step/prefix accuracy gives credit only to explicit, complete answers.

1. For R3 Trace maxima, accept winners derived from the archived exact rank score
   and frozen one-decimal display, with the same lexical/numeric tie conventions
   as v1. Combine with permitted M display variants without mixing ID conventions.
2. Normalize only field-specific captions: peak= on peak; z=, peak, z suffix,
   the exact (flat baseline) caption and the signed >=999 saturation cap on z.
   Preserve value, sign, IDs and units; no arbitrary prose or numerical tolerance.
3. Explicit upstream/downstream labels outrank pipe separators. Within a labelled
   side, pipes separate neighbors. Without labels require one unambiguous boundary.
   Wrong direction, missing/extra neighbors and unlabelled multiple boundaries fail.
4. Duplicate/ambiguous regional answers invalidate that region, not other regions.
   Unknown/unrequested rows remain a whole-answer error, but other correct steps
   retain credit. Never choose between conflicting values using the gold answer.
5. Restrict z annotations to signed-z, preserve exact long integers and reject
   pathological exponents before arithmetic. Check optional overall only against
   interpretations consistent with the actually supplied regional answers.

Answer normalization is gold-blind; gold alternatives come only from the existing
question and packet. No model-response-dependent expansion of allowed values.
Keep wrong answers and model truncations; do not reclassify them as infrastructure.

Recompute all prior dataset/model/representation/P/R summaries, paired statistics
and case-level QA–RCA correlations. Preserve v1-to-v2 per-record and per-step delta
tables, source hashes, CPU test results and report verification. This is post-hoc
measurement repair, not a new preregistration or model-performance improvement.

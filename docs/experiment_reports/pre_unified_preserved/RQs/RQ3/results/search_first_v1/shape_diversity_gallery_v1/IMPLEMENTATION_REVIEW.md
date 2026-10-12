# SEARCH37 initial CPU gallery — 2026-09-12

Zero model calls. Targeted30 and complete338 CPU tests passed, but the first
real gallery failed before any PNG: canonical bin values are finite numeric
strings (62,860 in the first case), not only Python numbers. The new numeric
validator rejected their type. Preserve this failure/cohort/junit; no old data
or experiment was affected. Add strict finite numeric-string decoding, reject
NaN/Inf/garbage rather than filling zero, and add a canonical-string/null
regression. Corrected gallery uses shape_diversity_gallery_v2.

Source organization: existing panel-selection mathematics stays in RQ3's
kpi_select.py, not an external dependency or second renderer. The unchanged
topology-ordering regression moved from core tests to renderer tests; no test
was removed. Core functional count5998 remains within6000. Drawing behavior,
earlier RQs, shared runtime/scorer and original raw/processed data unchanged.

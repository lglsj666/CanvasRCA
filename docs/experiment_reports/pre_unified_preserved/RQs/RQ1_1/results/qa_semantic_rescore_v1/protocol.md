# RQ11QASemanticRescoreV1 — post-hoc analysis, 2026-09-11

Source: `../rq1_1_v3_formal_480_v1/trajectories/direct_qa/` and the frozen
QA schedules/packets in `../rq1_1_v3_rq480_prepared_balanced_v1/`.
Implementation: `../../../../tmp/rq11_qa_rescore_20260911/scorer.py`.

Primary endpoint: every requested regional answer correct, not requiring the
R3 aggregation field. Step and correct-prefix accuracy are retained. Explicit
incorrect/malformed aggregation is separately penalized in `overall_checked`.
Never infer a missing regional value from the aggregation answer.

Accept exact and compact-display measurements identically across conditions;
use frozen `.4g` archive/renderer formatting, finite numeric notation and fixed
suffixes. At a precision boundary retain only possible adjacent compact labels
inside the archive rounding cell. Do not approximately match entity IDs,
counts, direction, or panel identity. Caption-saturated signed-z values retain
their cap/sign semantics. For regional maxima, accept the exact and supported
displayed-precision winner interpretations, with one ID-order convention per
question. An unqualified smallest ID/LT-ID accepts lexical or numeric ordering;
explicit lexical instructions remain lexical.

Normalize only unambiguous JSON wrappers, explicit region names/order, directed
neighbor sets and their separators/side labels. Complete step objects may be
recovered from a partial outer wrapper, but unfinished values are never filled.
Conflicting region answers, absent direction boundaries, wrong values and
unparseable output remain failures. No free-text gold-driven answer search.

The original joint 8-case infrastructure mask is retained for both models.
Protocol-ineligible no-call records remain outside accuracy denominators. No
additional question exclusion; no model rerun. All original scores/hashes and
record bytes remain intact. Each sidecar points to its source hash.

Paired comparisons use case-level Pratt-Wilcoxon and paired Cohen's dz; Holm
families are dataset/model/P. QA–RCA Spearman analyses aggregate by case,
with separate absolute and matched-change families by dataset/model/score
version. No confidence intervals or causal mediation claims. Numeric summaries
are exploratory, post-hoc endpoints and must be labelled accordingly.

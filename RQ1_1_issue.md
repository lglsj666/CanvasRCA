# RQ1.1 formal-run issues

## 2026-09-05 — Unicode directed arrows are not recognized by the post-hoc reason-grounding matcher

- Run: `rq1_1_v3_formal_480_v1`
- Record: `direct_rca/qwen3.8-27b/INC-8991CE65FDA1__V_MR`
- Severity: non-fatal for the registered RCA endpoint; repair before final mechanism analysis.
- Observation: the visible reason asserted `999 → 231 → 764`, while the supplied topology contained only `764 -> 231` and `764 -> 637`. The trajectory nevertheless recorded an empty `unsupported_typed_claims` list.
- Cause: the post-hoc typed-claim regex in `RQs/RQ1_1/src/exps.py` recognizes ASCII `->`/`=>` only, not the Unicode right-arrow character emitted by the model.
- Validity impact: none on the frozen top-5 predictions, granularity-aware RCA score, MRR, AC@K, token accounting, or current model calls. It can undercount unsupported directed-edge claims in the explanatory grounding metrics.
- Action: do not interrupt or rerun formal inference. Extend the offline matcher to recognize Unicode arrow variants, add regression tests, and recompute reasoning-trace/grounding summaries from the preserved responses before final mechanism reporting.

## 2026-09-05 — Equivalent displayed numbers with SI/scientific notation are falsely marked unsupported

- Run: `rq1_1_v3_formal_480_v1`
- Record: `direct_rca/qwen3.8-27b/INC-96E8C237EFAF__T`
- Severity: non-fatal for the registered RCA endpoint; repair before final mechanism analysis.
- Observation: the reason cited a `486.9k` peak and `39.4k` baseline. The public metric fact contains the equivalent peak `4.869e+05` and the exact MET-Z regular mean `39.4k`, but the trace recorded both numeric mentions as unsupported and reported grounding precision `0.0`.
- Cause: the post-hoc matcher extracts bare numeric substrings and compares string forms; it does not canonicalize SI suffixes or equivalent scientific notation before matching.
- Validity impact: none on the model-visible evidence, top-5 prediction, MRR/AC@K, tokens, or current inference. It can substantially understate grounded numeric evidence in the explanatory mechanism metrics.
- Action: preserve and finish inference. Normalize numeric values with units/SI suffixes and registered display precision offline, add regression tests for equivalent forms, then recompute reasoning traces and grounding summaries without model reruns.

## 2026-09-05 — Decimal relative-minute and implicit edge claims are not bound to visible facts

- Run: `rq1_1_v3_formal_480_v1`
- Record: `direct_rca/gemma-4-26b-a4b/INC-D28AC6CAEFE4__MV`
- Severity: non-fatal for the registered RCA endpoint; repair before final mechanism analysis.
- Observation: the visible reason states that entity `318` has the earliest onset at `t=3.9m` and is upstream. The supplied G facts contain the exact `318 -> 575` edge and `318` onset `+3.9m`, but the derived reasoning trace has no cited facts, no mentioned relative bins, and null typed-claim precision.
- Cause: the post-hoc fact binder does not presently turn this natural-language decimal-minute/onset wording and implicit upstream wording into the corresponding typed onset/edge claims.
- Validity impact: none on the model-visible prompt or image, parsed top-5 prediction, private scorer, MRR/AC@K, tokens, or current inference. It can undercount grounded temporal/topology evidence in the explanatory mechanism analysis.
- Action: do not interrupt or rerun formal inference. Extend the offline binder for registered decimal relative-minute and implicit upstream/downstream formulations, add regression tests, and recompute reasoning traces and grounding summaries from preserved responses before final reporting.

## 2026-09-05 — Critical cross-representation display-order mismatch in Direct-QA R/G anchors

- Run: `rq1_1_v3_formal_480_v1`, Qwen Direct-QA; the queue was safely stopped at 6,891/8,640 Qwen records before Gemma Direct-QA began.
- Triggering record: `direct_qa/qwen3.8-27b/INC-C993CF5D1232__L1_S`.
- Severity: fatal for affected Direct-QA matched groups; it does not affect the completed Direct-RCA endpoint.
- Observation: the question asks for the entity in the "first displayed TRC-L row". Its registered answer is `839`, matching `entry_index=0` and the first row of the real R-region dashboard. The lossless pixel-text screenshot actually displays entity `684` first because its natural-language rows are ordered by `fact_id`. Thus the same words denote different visible rows across representations.
- Cause: `_first_region_entity` selects R/G anchors by semantic display keys (`entry_index`/`edge_index`), while `packet_text` orders otherwise-equal facts by the opaque hash-like `fact_id`. Fact-set equality is therefore satisfied while ordered question semantics are not.
- Full-corpus scope: among cases with eligible data, R first-row identity differs in 309/472 cases and G first-edge caller identity differs in 254/473 cases. These are case-level prevalence counts, not a claim that every arm in those cases is invalid.
- Completed-run scope: 868/6,891 completed Qwen QA records (12.6%) are directly contaminated in T/S/ContextV-style presentations. Correcting the question while retaining matched same-question groups requires replacing 1,403/6,891 completed records across 334 case-level groups; 5,488 completed records are unaffected by this defect, subject to normal verification. Gemma QA had not begun.
- Why qualification missed it: static parity checks compared unordered fact inventories and answer availability, not the referent of presentation-order language in every representation. The bounded smoke sampled too few case/template/condition combinations, and smoke correctness is diagnostic rather than its passage gate. Earlier visual review emphasized clipping, leakage, and readability rather than an exact question→first-visible-row→private-gold triplet audit.
- Validity action: do not repair this by representation-specific rescoring, because that would make arms answer different semantic questions. Replace order-dependent R/G anchors with presentation-invariant visible anchors, add a cross-representation referent test, version the QA preparation/contract, and rerun only the affected matched groups plus previously unexecuted groups. Preserve and verify unaffected outputs. Resume RQ2 only after the corrected RQ1.1 Direct-QA run completes.

### Resolution and final affected scope

- The initial estimate above was made before the repair was applied. The final
  implementation also removed 204 R2 prompts that said “first displayed
  TRC-L row” after the entity was already known; their answer was invariant,
  but retaining the phrase would leave an unnecessary cross-representation
  ambiguity.
- R anchors now use a unique visible pair of displayed fault-window ExL p95 and
  rank score. G anchors use a unique visible callee and ask for its caller.
  Non-anchor R2 trace steps allow any displayed row for the already specified
  entity. Reversing fact storage order must leave every R1 public question,
  answer, and supporting fact set unchanged.
- Across the complete 480-case schedule, 768 matched case-level groups changed:
  564 in the anchor repair and 204 in the residual wording repair. Exactly
  2,645 already completed Qwen trajectories from those groups, their
  conversations, and their request-specific attention artifacts were removed.
  The deletion manifests are under
  `repair_audits/2026-09-05_qa_display_order_repair*.json` in the formal result
  root. No Direct-RCA artifact was touched.
- The repaired preparation index is
  `25dd503cb6900267dc267273ee6f8bb6a572ec0a2bed6ba024a7cbd6f4f8994b`.
  The 28 GB evidence/image preparation was not regenerated; only QA schedule
  sidecars and the semantic index changed.
- Successor smoke `rq1_1_direct_qa_smoke_v5_anchor_repair` completed all 18
  calls (9 Qwen3.8, 9 Gemma), with parse rate 1.0, zero infrastructure errors,
  zero truncation, complete same-call attention artifacts, and a passing
  verifier. Its run-contract SHA256 is
  `23e6489cdefe1dfe4592099b7a6d2150472a7afaed576ac214cc006b1c9aa49a`.
- Unaffected predecessor QA terminals are reusable only when the current code
  reproduces the entire model-visible request byte-for-byte and rescoring the
  stored normalized answer against the current private answer reproduces the
  stored score. This compatibility rule is restricted to Direct-QA contract
  `b5bb3acd5766e09693277cab5800219eb33fb5c32973d067643c38c143fbe697`.

## 2026-09-05 — Analysis-only null metric aggregation failure

- Run: `rq1_1_v3_formal_480_v1`, after both Direct-QA model phases completed.
- Severity: operational only; no inference artifact was affected.
- Observation: the analysis command raised `TypeError: float() argument must be
  a string or a real number, not 'NoneType'` before RQ2 could start.
- Cause: grouped analysis discovered a metric because it was numeric in some
  completed rows, then attempted `float(None)` for completed rows where that
  optional metric was not applicable.
- Resolution: grouped means now average only rows containing a numeric value
  for the metric. A targeted mixed numeric/`None` regression passed, and both
  Direct-RCA and Direct-QA analyses completed without any model rerun.
- Validity impact: none on prompts, responses, conversations, attention,
  scoring, tokens, or pairing. The formal queue resumes only after the full
  RQ1.1 verifier passes.

## 2026-09-05 — Nine generation-target attention absences at final verification

- Scope: 9/35,520 terminal trajectories (0.025%). Prompt-query attention,
  conversations, responses, scores, and record hashes were present in all nine.
- Six are structurally inapplicable under the project rule: four Gemma outputs
  were truncated/invalid and normalized to empty value arrays, while two valid
  Qwen QA schemas contained only empty-string answer values. There is no
  alphanumeric answer token whose generation attention could be collected.
  The verifier now recognizes only this registered structural exception; it
  still requires prompt-query attention and all associated hashes.
- Three valid Qwen Direct-RCA responses did contain service IDs but lacked the
  required generation-target probe. Those three incomplete records,
  conversations, and request-specific attention directories were deleted and
  scheduled for exact-cell rerun. During that resume, the runner also retried
  the 100 pre-existing Direct-RCA infrastructure-error terminals, because they
  were never valid completed model outcomes. It did not replace any other
  completed response. The result was 102/103 complete generation-attention
  records; one newly successful retry lacked generation attention and was
  removed for one further exact-cell retry.
- Because the analysis-only repair changes the source hash, predecessor
  Direct-RCA reuse is admitted only after reconstructing the complete
  model-visible request byte-for-byte and reproducing the private score. A
  targeted positive/negative compatibility regression passed.
- RQ2 remains fail-closed until the three calls finish and the full RQ1.1
  analysis and verifier pass.

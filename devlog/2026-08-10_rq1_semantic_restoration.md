# 2026-08-10 — RQ1 semantic restoration after compact-refactor audit

## Outcome

The compact Nibi RQ1 implementation was not scientifically equivalent to the
pre-refactor experiments. All predecessor compact Nibi trajectories, including
completed and partial v7 shards, are now archived invalid. They remain on disk
for audit and must not be merged into successor results.

The replacement protocol is `rq1_semantic_restore_v3`. Renderer-v17, the
frozen 469-case roster, unified model configurations, and the separate
headline/RE2 reporting policy are retained.

## Repaired experiment semantics

- Restored the controlled four-region M/L/R/G canvas from real label-blind
  telemetry, with 16 displayed bins and one shared fact packet for text,
  visual, factorial, and strict A+B arms.
- Bound every metric fact to the exact elided name visibly rendered on its
  panel and added measured, lossless line wrapping so long log/trace records
  cannot cross or clip a controlled-canvas region.
- Restored all 14 registered question templates: four Level-1, six Level-2,
  and four Level-3 families. Trace rows disclose case-local edge IDs without
  endpoints; topology alone resolves caller/callee.
- Replaced generic Q&A prompts and flat response scoring with strict nested
  step/region/value schemas, complete-chain, prefix, and step accuracy.
- Restored RCA T/F/V/H/R visible-fact equality, two-stage isolation, a typed
  post-model binder, case-balanced arm order, paired analysis, per-dataset and
  per-fault reporting, and separate saturated/OOD slices.
- Counterfactual selection is label blind, targeted and placebo pairs are
  distinct, no-op swaps fail, ineligible cases are explicit, and the neutral
  sham preserves geometry.
- Ledger handoff is losslessly paginated across at most eight images, shares
  Stage 1 across all three handoff arms, resumes it once, and does not duplicate
  Stage-1 cost in every arm.
- Added a path-only legacy processed-data reader for local WSL qualification;
  the Nibi public/private v2 path remains primary.

## Verification

- Full CPU/static suite: passed, zero model calls.
- RQ1 functional source: 3,636 lines at the final restored pass, below the
  5,000-line ceiling.
- Template reachability: all 4/6/4 families generated and known-correct
  responses scored correctly.
- Real data preparation: representative AIOPS-2022, AIOPS-2025, and RE2-OB
  cases passed public/private separation, strict representation audit,
  renderer compilation, counterfactual eligibility, and question generation.
- Real-data checks found and repaired three pre-inference defects: fixed-canvas
  overflow on longer trace rows, a `None` private-marker false positive, and
  natural entity mentions inside normalized log templates.

### Local bounded live qualification

The explicitly path-adapted WSL qualification used the Nibi source and config,
real local processed cases, the local unquantized Gemma checkpoint, and the
Nibi Gemma serving recipe. It remained diagnostic-only and did not create a
scientific result.

The first live attempt exposed that xgrammar 0.2.3 rejected unsupported
`uniqueItems` and string-size keywords in the diagnosis schema. Those
constraints were moved to the existing deterministic post-model validator;
the set of scientifically accepted outputs did not change.

Artifact review then exposed a second hidden defect: the Stage-1 binder rejected
otherwise exact log and trace rows when the model attached a reasonable unit,
or used readable metric aliases such as `metric_name`. The binder now maps only
a small registered alias set to canonical packet keys, checks every claimed
value, copies canonical values and units from the unique matched fact, and still
rejects incorrect or ambiguous observations. Reprocessing the original raw
responses changed supported-observation counts from `0/0/5` to `13/20/20` for
the three RCA paths; incorrect visual metric readings remained unsupported.

The final run is stored locally at
`results/nibi_local_qualification/rq1_semantic_restore_live_logic_20260810T211529Z`
in the WSL repository. It completed all 10 calls in 372.7 seconds, below the
18-call and 600-second limits. All 10 responses were nonempty, parsed, ended
with `finish_reason=stop`, retained their full prompt/conversation artifact,
and were untruncated. Manual inspection found no remaining hidden transport,
ordering, candidate-ID, or persistence error. Diagnostic Q&A complete-chain
scores were 8/9 for Legacy-Q9 and 2/3 for both cross-region and typed two-stage.
All three RCA predictions contained only registered candidate IDs; their
normalized ledgers carried 13, 20, and 20 supported observations respectively.

### Renderer-v17 and final semantic-patch qualification

The renderer-v17/all-six diagnostic used the same three real cases and 10
calls. It finished in 350.4 seconds: every raw response and prompt/conversation
artifact was present, every request stopped normally, and none was truncated.
Nine responses passed diagnostic parsing. Gemma's typed Stage 1 duplicated an
`E##` edge identifier into both `entity_id` and `edge_id`, so the strict typed
validator rejected it and Stage 2 received the finite failure marker. This was
recorded as a model/schema outcome rather than silently repaired.

After restoring the final prompt wording, informative Legacy-Q9 cell
selection, unique-dependency cross-region rules, and removal of non-rendered
RCA metric metadata, a focused three-case/6-call diagnostic finished in 182.6
seconds. Again all requests were nonempty, normally stopped, prompt-recorded,
and untruncated; five of six parsed. The typed Stage 1 now respected the G-row
field contract but omitted later registered steps for two queries, so it
correctly remained a typed-ledger parse failure. All other execution paths
parsed. Post-hoc deterministic review measured Legacy-Q9 `6/9`, cross-region
complete-chain `0/3` with step accuracy `0.50`, and 15 supported versus 17
unsupported matched-RCA observations. These diagnostic accuracies are not
scientific outcomes or gates.

The two successor diagnostics initiated 16 calls total, below the aggregate
18-call bound; each used exactly the same three cases and remained below 600
seconds. The final CPU suite passed after a last fail-closed addition that
serializes every common C-region image legend/fact into the shared RCA shell.
That final common-shell equality assertion is CPU-verified but has not been
used to claim a local model result; Nibi still requires its own new runtime
freeze and Rule-16 smoke.

## Validity and next step

Static and local qualification artifacts are implementation evidence only, not
RCA or perception results. Before heavy Nibi inference, generate a new runtime
freeze and bounded Rule-16 smoke under new result IDs, inspect completed raw
responses/conversations, then rerun all six RQ1 experiments. Do not resume or
rehabilitate predecessor v7 roots.

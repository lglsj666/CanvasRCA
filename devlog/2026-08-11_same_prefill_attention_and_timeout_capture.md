# 2026-08-11 — Same-prefill attention and timeout response capture

## Scope and status

RQ1 infrastructure and diagnostic-only local WSL qualification for successor
protocol `rq1_same_prefill_attention_v14`. No formal Nibi experiment was
started. The completed direct-RCA double-model smoke and the Qwen
visual-counterfactual timeout diagnostic are smoke evidence only.

## What happened

- Added a project-owned vLLM 0.24 runtime hook that reads Qwen layer 3 and
  Gemma layer 5 query/key tensors during the original prefill, without changing
  the tensors, logits, model files or weights and without another model call.
- Every successful visual request now persists the raw attention vector, a
  per-image 16x16 grid and a PNG heatmap. The unified client joins these
  sidecars to the ordinary response by explicit request ID.
- The double-model `direct_rca` smoke
  `rq1_v14_attention_direct_smoke_20260810d` completed 3/3 requests for each
  model, with zero infrastructure errors and passing verification. Its V and R
  requests both produced required same-prefill attention artifacts.
- Qwen's subsequent matched-RCA smoke showed sustained long generation. The
  old non-streaming timeout path could not retain the unfinished response, so
  the remaining suite was stopped before further experiments.
- Added smoke-only streaming response checkpoints and supervisor finalization.
  Checkpoints include case, arm, stage, model, request IDs, accumulated text,
  chunks and timestamps; unfinished files become `timeout_partial`.
- The focused Qwen diagnostic
  `rq1_v14_partial_capture_qwen_counterfactual_20260811a` reached its 515-second
  remaining timeout, preserved six responses with zero capture errors and did
  not continue to another experiment.

## Validity and caveats

The focused diagnostic used the three authorized smoke cases and the frozen
model/prompt/schema/output settings. It is not an RCA or modality result.
`H_targeted` Stage 1 produced valid JSON with 32 observations and stopped after
5,398 tokens; `H_neutral` reached 8,192 tokens and truncated inside JSON.
Unfinished `H_placebo` and `H_factual` prefixes were preserved. The long output
was an exhaustive ledger dominated by propagation rows and full 64-bin metric
arrays, not a free-text repetition loop. Partial responses are never parsed or
scored as complete answers.

The all-remaining-smokes attempt
`rq1_v14_attention_remaining_smokes_20260810a` is an interrupted diagnostic:
Qwen matched RCA passed only by its timeout-only rule, and the following
visual-counterfactual phase was manually stopped when the missing-partial-
response observability defect was identified. It is not a qualification
authority.

## Decisions

DD-87 freezes same-prefill attention as a zero-extra-call, correlational visual
diagnostic. DD-88 freezes atomic streaming checkpoints for bounded smokes so a
timeout does not destroy already received output. Neither decision changes a
scientific arm or permits tuning on partial formal results.

## Blockers

The other six RQ1 experiments still lack their complete two-model successor
smokes under the same-prefill attention runtime. Qwen's exhaustive Stage-1
ledger can consume most or all of a smoke phase; this is a model/protocol
diagnostic to report, not an infrastructure error to hide.

## Next steps

1. Review whether the 32-observation/full-array Stage-1 ledger should remain as
   the registered scientific protocol or receive an explicitly versioned
   compact-ledger successor; do not change it implicitly.
2. After that decision, run one independent bounded two-model smoke per
   remaining experiment and inspect the captured partial/full responses.
3. Only when all intended successor smokes pass their integrity checks should
   the heavy Nibi runs be submitted.

## Compact Stage-1 successor

The user authorized the protocol change after reviewing the timeout diagnosis.
RQ1 is now `rq1_compact_stage1_v15`: RCA Stage 1 returns at most 16
human-readable public-record selectors and at most four metric bins per
selector. It no longer transcribes values, arrays, attributes, units, opaque
fact IDs or relation arrays. The label-blind host binds each selector to one
public fact, copies exact scalar/selected-bin values, rejects ambiguous or
nonexistent selectors, and derives selected topology relations. Renderer,
T/F/V/P/H/R representations, Q&A experiments, Stage 2, scorer and unified vLLM
configuration are unchanged.

The first v15 CPU suite passed all seven experiment compilers and 56 arm paths
with zero model calls; RQ1 functional source is 4,878 lines. The three affected
two-stage RCA experiments still require their independent bounded dual-model
smokes before any heavy Nibi submission.

## Final local handoff status

At the user's request, the remaining local smoke sequence was stopped and all
future smoke work was handed off to the Nibi agent. The interrupted sequence
preserves every completed artifact; nothing was deleted or reclassified.

The current RQ1 implementation status is:

- Same-prefill attention collection is integrated into the original visual
  request, adds no model call, and persists raw vectors, 16x16 grids, PNG
  heatmaps, and region diagnostics for successful visual calls.
- Bounded smoke streaming persists in-progress response text and finalizes it
  as a timeout partial when the supervisor terminates a request.
- RQ1 protocol `rq1_compact_stage1_v15` replaces exhaustive two-stage RCA
  Stage 1 with at most 16 human-readable public-record selectors and at most
  four metric bins per selector. Host-side, label-blind binding copies exact
  values from the public evidence record. It applies to `matched_rca`,
  `visual_counterfactual_rca`, and the shared Stage-1 path of
  `ledger_handoff_rca`; it does not change `direct_rca`, `legacy_q9`,
  `cross_region`, or `typed_two_stage`.
- Static qualification passed all seven experiment compilers and 56 arm
  paths, with zero model calls and 4,878 functional RQ1 source lines.
- In the partially completed affected-smoke sequence, Qwen `matched_rca`
  completed 3/3 records and 6/6 calls, and Qwen
  `visual_counterfactual_rca` completed its registered 8 calls; both had zero
  infrastructure errors and passing verifiers. Qwen `ledger_handoff_rca` was
  manually terminated when the user requested no further local smokes and is
  an interrupted diagnostic, not a passed smoke.

### Final Gemma matched-RCA smoke

The requested final local smoke is
`rq1_v15_compact_stage1_gemma_matched_smoke_20260811a`. Gemma completed 3/3
validation cases and 6/6 calls in 86.82 seconds after server readiness, with
zero infrastructure errors, no timeout, no truncation, all Stage-1 and Stage-2
responses parsed, and the verifier passed. The V and R calls also persisted
required same-prefill attention artifacts.

The compact successor eliminated the diagnosed long-output failure. Gemma
Stage-1 output lengths were 1,251 tokens for V, 1,199 for R, and 1,352 for T;
all ended with `finish_reason=stop`. This is substantially below the v14 Qwen
diagnostic's 5,398-token complete ledger and 8,192-token truncated ledger and
well below the registered 16,384-token ceiling.

Post-smoke conversation review nevertheless found a scientific interface
issue. Gemma's grounded-selector counts were V=0/16, R=5/16, and T=10/16. In
the V response, candidate IDs were placed in `supports`/`opposes` while every
public-record identity field was null, so the label-blind binder correctly
rejected rather than guessed. Qwen's completed v15 matched smoke shows the
same direction (V=2/14, R=0/7, T=6/8), making this a cross-model compact
visual-selector problem rather than a Gemma-only configuration issue.

This hidden issue does not reverse the smoke's infrastructure-passed status:
grounding quality and RCA correctness are not smoke passage criteria. It does
block a scientifically interpretable heavy `matched_rca` run until a Nibi-side
agent repairs the selector-identity interface under a forward protocol version
and reruns that experiment's bounded two-model smoke.

Detailed review:
`/home/lglsj/CanvasRCA/results/nibi_local_qualification/rq1_v15_compact_stage1_gemma_matched_smoke_20260811a/results/rq1_v15_compact_stage1_gemma_matched_smoke_20260811a__matched_rca/post_smoke_review.md`.

No vLLM server or local smoke runner remained active after the final review.
Per user direction, no additional local smoke, repair, or formal experiment was
started.

## V16 selector-binding repair — untested handoff

After the final review, the user authorized a code repair and explicitly
required that no tests or further smokes run locally. The implementation and
documentation now identify `rq1_record_key_stage1_v16` /
`CanvasRCARQ1ConfigV5`; this section is a handoff record, not qualification.

### Root causes found

1. The v15 JSON schema made `entity_id`, `panel_id`, `row_index`, `caller`, and
   `callee` nullable in every selector. A syntactically valid all-null identity
   tuple therefore reached the binder.
2. `supports/opposes` appeared beside the record identity. Gemma and Qwen often
   placed visible candidate IDs there while leaving the actual record identity
   null, so the binder correctly rejected rather than guessed.
3. The metric `panel_id` schema pattern required two digits (`M01`) while the
   frozen real dashboard displays `M1` through `M12`. The Gemma T response
   included values such as `M66`, consistent with trying to satisfy that
   incompatible grammar from visible `panel_id=M6, rank=6` evidence.

### Code and contract changes

- `RQs/RQ1/src/exps.py` replaces the RCA Stage-1 response with
  `CompactRecordKeyLedgerV4`. A selector contains only non-null `record_key`
  and `relative_bins`; the schema no longer exposes nullable identity fields or
  candidate-support lists.
- Record keys use labels already visible in every corresponding arm:
  `M1`, `L:<entity>`, `R:<entity>`, `G:<entity>`,
  `G:<caller>-><callee>`, `L:missing`, or `R:missing`.
- The host builds a unique public key index, rejects duplicate/unknown keys,
  allows bins only for metrics, and copies exact public values after a unique
  match. It performs only harmless panel-zero-padding, whitespace and arrow
  typography normalization; it does not infer a missing record from a
  candidate judgment.
- The normalized handoff advances to `NormalizedEvidenceLedgerV4`. Existing
  compatible support/opposition fields remain present but empty; Stage 2 must
  reason from the bound fact itself.
- `RQs/RQ1/src/tests.py` was updated for the v16 config, response schema and
  real one-digit metric-panel labels, but it was not executed.
- `RQs/RQ1/configs/rq1.yaml`, `RQs/RQ1/src/__init__.py`, `Codex.md`, `README.md`,
  RQ1 descriptions/findings and DD-90 were advanced to v16.

The repair does not change renderer-v12, dashboard bytes, fact inventories,
T/F/V/P/H/R serializers, H=A+B, Stage 2, RCA scorer, Q&A/perception experiments,
attention collection, model settings, data roster or runtime limits.

### Validation state and Nibi handoff

No test, static suite, smoke, gate, model call or formal experiment was run
after the v16 edit, exactly as requested. The Nibi agent must therefore:

1. review the v16 diff and run the CPU/static RQ1 suite;
2. prepare fresh v16 artifacts and confirm every selectable public record key
   is unique on the frozen roster;
3. run the independent bounded dual-model smokes for `matched_rca`,
   `visual_counterfactual_rca`, and `ledger_handoff_rca`;
4. inspect raw Stage-1 responses and require materially improved supported-key
   rates before submitting heavy runs;
5. use new result IDs and never resume or rewrite v15 artifacts.

Until those steps pass, v16 is implemented but unqualified and no heavy Nibi
RCA run is authorized by this local handoff.

## Design-decision consolidation

At the user's request, `plans/design_decisions.md` was changed from a
chronological decision transcript into a compact current-authority register.
It now contains ten operative topic decisions instead of twenty-two full
historical entries and is 316 lines rather than 1,375.

Superseded chains were folded into their final authorities: RQ2 planning into
DD-52; Nibi runtime/concurrency into DD-78; typed Q&A selectors into DD-83;
renderer/representation/prompt semantics into DD-85; the final RQ1 program into
DD-86; visual diagnostics into DD-87; smoke/gate/streaming rules into DD-88;
and RCA Stage-1 selectors into DD-90. DD-13a and DD-43 remain independent
current decisions. A short lineage table maps removed IDs to their surviving
authority so older artifact citations remain interpretable.

`Codex.md` now requires the same maintenance policy: keep only the newest
operative decision per topic, consolidate its necessary rationale and
consequences, and retain detailed history in Git, dated devlogs, findings, and
immutable experiment artifacts. No scientific code, config, test, smoke, gate,
or model execution was involved in this documentation-only consolidation.

# visual_counterfactual_rca Findings

**Status:** the corrected v23 469-case formal inference is complete for both
registered models. Qwen and Gemma each completed 24/24 shards and 1,876/1,876
terminal records with zero infrastructure errors; all 24 current shard
verifiers cover the combined two-model trajectories and report zero missing or
integrity errors. Final consolidation, registered analysis, and scientific
interpretation remain pending, so no efficacy or causal conclusion is claimed
yet. Predecessor trajectories remain diagnostic/archive evidence.

The shared RCA Stage-2 prompt now uses the registered field/RCA guide and
internal SIRCL-style VERIFY procedure. This is a successor protocol change,
not a counterfactual result; all four conditions still require a replacement run.

This file is the sole findings authority for the registered
`visual_counterfactual_rca` experiment. No scientific result is claimed before
the complete 469-case paired run, verifier, and registered analysis finish.

The final entry will report the 289-case primary headline, per-dataset effects,
the separate RE2-OB and RE2-TT slices, causal rank-shift metrics, ledger changes,
RCA metrics, integrity status, and limitations.

The local targeted-arm diagnostic completed and parsed both stages with a
candidate-scoped, same-granularity intervention. No causal effect can be
estimated from this one diagnostic cell.

## 2026-08-11 streaming-timeout diagnostic

The local diagnostic
`rq1_v14_partial_capture_qwen_counterfactual_20260811a` is smoke evidence only;
it is not an efficacy or counterfactual result. Its Qwen phase used the frozen
prompt, schema, 8,192-token RQ1 output adapter and same-pass attention runtime,
then ended by the expected bounded-smoke timeout after 515 seconds of remaining
phase time. Streaming checkpointing preserved six responses with zero capture
errors.

- `H_targeted` Stage 1 stopped normally after 5,398 output tokens. Its valid
  JSON contained the maximum 32 observations: 16 propagation-service rows,
  14 metric/missingness rows and two trace rows. Stage 2 also parsed.
- `H_neutral` Stage 1 reached the 8,192-token ceiling and truncated inside a
  JSON string after 17,616 characters; its failure marker was then handled by a
  normally completed Stage 2.
- At supervisor timeout, incomplete `H_placebo` and `H_factual` prefixes were
  retained rather than discarded.

The long generation was an exhaustive structured ledger dominated by full
64-bin numeric arrays and repeated schema fields, not a free-text or identical-
observation loop. This diagnoses output-volume and numeric-tokenization cost;
it does not justify changing the registered ledger or interpreting partial
responses as valid answers.

The user subsequently authorized v15, which removes this transcription burden:
Stage 1 now emits no raw values or relation arrays and is capped at 16 selectors
with four metric bins each. The counterfactual images, strict hybrid text,
selector algorithm, candidates and interventions are unchanged. The v14 smoke
above remains the diagnostic reason for the change and is not reinterpreted as
a v15 qualification or causal result.

The subsequent v15 matched smokes showed that the nullable identity tuple and
candidate `supports/opposes` fields still permitted poorly grounded visual
selectors. V16 therefore replaces only that selector interface with one
nonempty visible `record_key`; the counterfactual conditions and evidence are
unchanged. V16 has not yet been tested and makes no causal or efficacy claim.

## 2026-08-20 Qwen3.8 successor resume

The separate Qwen3.8 successor lineage stopped after 50 terminal records: 48
completed model outputs and two `protocol_ineligible` records. This was an
implementation-order failure, not a model or evidence failure. The runner
looked up targeted/placebo images before consulting the frozen label-blind
eligibility field; those images are intentionally absent for 39 ineligible
cases. Preparation contains the full four variants for all 430 eligible cases.

The runner now handles ineligibility before image lookup and emits zero-call,
hash-valid terminal records for every arm of such a case. Eligible prompts,
images, outputs, renderer and scorer are unchanged, so completed Qwen3.8
records retain their status and the lineage resumes by call key. This entry is
an operational finding only; no partial counterfactual efficacy result is
reported.

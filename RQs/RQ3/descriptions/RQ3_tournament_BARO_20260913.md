# Round 2: native BARO metric selection, without training

## Decision and motivation

Status: adopted for bounded adaptive discovery, 2026-09-13. Round 1 is
complete; neither model reached the 240/300 primary-case top-1 threshold.
Earlier SEARCH1–40 comparisons show that more metrics sometimes help, while
resource quotas and trace-only inputs are not consistently successful. Test a
different full-source selector instead of tuning the fixed RCA instructions.

Method ID: `BARO019_FINITE_TOP24_tournament_v1`.
Config: `../configs/tournament_baro24_v1.yaml`.
Choose 12 eligible cases per primary dataset and 3 per RE2 dataset, per model,
by ascending `SHA256([42, opaque_case_id])`. No labels or fault categories are
used for this sampling. Model retirement sets remain separate. The small round
is 42 calls/model, 84 maximum, not a new smoke or full-population estimate.
Both models run the same method; already retired cases are never re-called.

## Source and limits

BARO (Luan Pham, Huong Ha, Hongyu Zhang) is an
[FSE 2024 research paper](https://2024.esec-fse.org/details/fse-2024-research-papers/81/BARO-Robust-Root-Cause-Analysis-for-Microservices-via-Multivariate-Bayesian-Online-C),
DOI 10.1145/3660805. Its
[paper](https://arxiv.org/html/2405.09330v1) motivates median/IQR scoring when
the detected anomaly boundary is imprecise, tests three applications and four
fault types, and reports sensitivity/component experiments. Those results do
not establish VLM or dashboard gains. The paper's absolute-deviation formula
differs from its tagged code's signed maximum; this round explicitly uses the
[official 0.1.9 implementation](https://raw.githubusercontent.com/phamquiluan/baro/0.1.9/baro/root_cause_analysis.py),
not a silently corrected formula. It may miss strongly decreasing signals.
No Multivariate BOCPD, trace algorithm or full BARO system is reproduced here.
Original source, MIT license and commit provenance remain under
`packages/rq21_native/baro_original/` and `PROVENANCE.json`.

## Executed adaptation

- Read complete public processed metric series, not the previous display's
  short list. Reuse the existing public, telemetry-derived analysis interval;
  neither injection time nor root labels enter selection.
- Retain the established relative-clock projection. Per column, retain finite
  observations in each period in their original order. Require two per period;
  skip a constant period as the native component does on dense data.
- Pack unequal-length columns with trailing NaN only. No zero imputation,
  interpolation or duplicated samples. Call the unchanged native scorer once
  on that table; its RobustScaler fits baseline median/IQR and its maximum
  current scaled value supplies the ordering. The adapter does not replace it
  with a shared ranking formula. CPU dense-input and sparse-alignment parity
  tests are mandatory.
- Bind native column identities to the inherited full-pool panel IDs before
  selection. Take 24 native-ranked panels; if fewer are eligible, fill remaining
  slots from the unchanged parent order and record exact fill IDs. Exceptions
  are errors, not fallback. Original facts/values are not rewritten to carry
  BARO scores. Reject unknown/duplicate panel bindings.
- Preserve the normal four trace rows, two selected log templates and bounded
  topology/membership context. Their relevance-based edge choice may change
  when metric owners change; this is a recorded compound evidence-selection
  intervention, not an isolated one-number ablation. Candidate set, pure PNG
  transport, card labels, layout, model recipes and prompt structure stay fixed.

## Acceptance and interpretation

Before inference, inspect actual representative PNGs and verify all selected
facts, no clipping, candidate binding, source values, and unchanged prompt.
Compare the selected panel IDs and pixel hashes against round 1 for the same
cases. Native equivalence/no-op is allowed but must not be called a new signal.
No new model smoke is needed for an unchanged API/renderer/scorer route already
qualified with both models; CPU checks qualify the new selection and bindings.
The first few persisted formal replies are still manually checked.

Keep all results including model-format failures. Do not retry to get a correct
answer. Commit independent AC@1/3/5 method maps, then consider other faithful
selectors or a wider cohort of this same algorithm. No MRR is promised.
Model input, output and costs are persisted without attention. Monitor every
600 seconds and perform no work during sleeps.

Two data-independent helpers (connected row grouping and normalization of one
tokenizer output) move to the unified segmentation/training utility modules.
Their behavior is tested unchanged; they contain no RQ cohort, reward or
selection policy. No optimizer/model training is started by importing them.

The later 2026-09-13 user goal amendment raises RQ3's temporary functional-source
limit to 10,000 lines. The authority and static gate are synchronized. It does
not change model inputs or this round's scientific configuration; the valid
generic-helper refactor is retained rather than churned back solely for length.

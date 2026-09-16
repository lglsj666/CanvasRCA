# DD-RQ3-SEARCH-15 — Source-verified field dictionary, identical dashboards

Date: 2026-09-12. Status: CPU/visual qualified train-only prompt contrast; not promoted.

The previous complete 24-call membership/selection trial did not improve the
pooled training score. Read responses sometimes confused response latency with
traffic, a retained log-rate ratio with a lost fraction, and auto-ranged tiny
memory changes with exhaustion. These are observed model interpretations, not
evidence that the source values are corrupt. Keep every preceding artifact.

This iteration changes only a static reading-guide suffix. On the same twelve
registered train cases, compare evidence_bound_membership_v1 with
evidence_semantics_v1, using ranked_membership_v1 for both. All selected facts,
PNG bytes, candidate lists, task text, output contract and non-thinking recipe
must match within each pair. Twenty-four calls maximum. The control is an
explicit contemporaneous repeat, not a new independent case or hidden retry.
No attention, Composer inference, validation, eval, SFT or RL is authorized by
this contrast. Candidate lists remain exclusively in the text prompt; owner
IDs and public name-group relationships remain diagnostic image evidence.

## Source verification and interpretation boundary

- The [official AIOps 2025 sample README](https://www.aiops.cn/gitlab/aiops-live-benchmark/aiopschallengedata2025-sample/-/blame/95f9480ba102ac3bdda9b6bd8c513fcdac1f5d79/README.md)
  defines rrt as mean delay and rrt_max as maximum delay, separately from
  request/response counts. [DeepFlow's application metrics documentation](https://deepflow.io/docs/features/universal-map/application-metrics/)
  gives the corresponding latency fields. This supports the field dictionary,
  not an RCA improvement claim. No dataset name or source URL enters the model
  input. Do not infer a unit conversion from a name alone; raw plotted values
  remain unchanged.
- The actual native `RQs/RQ2/src/exps.py:build_log_r_scores` calculates
  q=current/baseline log rate, adds 30*(1-q), and prints q after
  volume_drop_x30. All error-rate bonuses and count multipliers in the new
  guide are checked against that function. It is read-only; no older RQ code
  is changed. The current RQ3 compiler already calls this native function.
- The actual RQ3 raw metric painter uses each lane's observed min/max, not a
  common zero baseline. State that behavior accurately. Zero-anchored plotting
  is a possible separate future factor, not silently added here.

## Qualification and reporting

Require all source tests, pure-vision/candidate-boundary regression, byte-equal
paired PNG/packet/candidates/task/request recipe, and actual PNG inspection.
Audit complete conversations, stop/truncation status and accounting after the
bounded run. Report all per-case pairs, both datasets, token cost and failure
patterns. The twelve repeated train cases cannot satisfy the full-evaluation
targets. A dictionary may still be ignored or impose extra context cost; do not
promote it before measuring its effect.

Qualification completed: 229 CPU tests passed in 76.18 seconds; source audit
5,981 functional lines. All 24 previews have byte-identical paired PNGs,
packets, task/candidate parts and source membership; the control also matches
the previous gallery exactly. Two actual images, one from each dataset, were
opened. The approved review is bound to gallery summary hash
`3616c16fe3c775a8c7e011541459f277d2d9d563019228d1c0af11cdce2aba57`.
One initial offline review was invoked before the gallery summary existed;
it failed without launching a model call. After normal gallery completion the
same verifier passed. No source data or preceding result was removed.

## Completed: not promoted

All 24 calls completed in 231.175 seconds with no timeout, truncation, transport
or schema failure. A22 MRR .2222→.2222; A25 .3667→.3333, no RR repairs/one
break/eleven ties. Input increases by 456 tokens per case. Source definitions
remain correct, but the guide does not improve this train subset and is not a
new default. Full answer review still finds capacity/latency/owner/causal-link
errors. See the result's `logs/20260912_review.md` and `paired_review.json`.

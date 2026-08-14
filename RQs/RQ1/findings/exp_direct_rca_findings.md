# Direct RCA Findings

**Status:** v21 successor smoke qualified; final full execution is reassigned
as a whole-experiment local heldout and has not started. The prior Nibi Qwen
shard-0 result was explicitly invalidated and deleted at the user's direction;
the local run must start from scratch. Nibi must submit no `direct_rca` shard.
No RCA efficacy or stage-architecture conclusion is currently valid.

`direct_rca` is the registered natural one-stage reference for the current RQ1
RCA family. It consumes the same T/F/V/P/H/R incident representations and
candidate shell as `matched_rca`, then directly emits and scores the frozen
top-five RCA JSON in one model call. It does not construct, bind, or transfer an
evidence ledger.

The v16 record-key Stage-1 change does not alter this one-stage path, but the
shared source/config freeze changed; therefore the earlier v14 direct smoke is
retained as diagnostic evidence and does not attest a v16 heavy run.

The eventual finding must report per-model and per-dataset MRR, AC@1/3/5,
AVG@3/5, parse/truncation/infrastructure rates, tokens, calls, GPU time, and wall
time. The paired `compare-stages` artifact reports `matched_rca` two-stage minus
`direct_rca` one-stage values for every common model/case/arm cell.

That paired difference is an agent-architecture description, not an isolated
causal effect of adding one stage: the two-stage route also adds explicit
evidence selection, deterministic fact binding, ledger compression, and a
second decoding opportunity. This file must be updated only after the complete
replacement local run, returned-artifact verification, and registered analysis
finish.

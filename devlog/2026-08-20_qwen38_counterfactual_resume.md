# 2026-08-20 — Qwen3.8 counterfactual RCA resume repair

The local Qwen3.8 all-RQ1 queue had stopped in
`visual_counterfactual_rca` with `missing counterfactual image 'placebo'`.
Inspection established that preparation was correct: 430/469 cases are
eligible and contain factual, neutral, targeted and placebo variants; the 39
label-blind ineligible cases intentionally contain only neutral evidence.

The runner performed arm image lookup before checking eligibility. It was
changed in both the authoritative Nibi tree and the local execution shadow so
that ineligible cases produce complete zero-call `protocol_ineligible`
terminals before representation construction. Resume validation now recognizes
those terminals, and summaries distinguish completed model outputs from
protocol-ineligible terminals. The shell cleanup also guards an unset server
PID, fixing the secondary error that appeared after the primary exception.

A signed compatibility bridge connects prepared freeze
`ba25fe1dcfbce970fe2da07c298a4132fb3b7df3833c2b44483434c0e72f0118`, prior
Qwen3.8 result freeze
`918f47c86f48e6c66f2fd7f5e29562bfc972d6233e3b9776eab7aa9aa470cad8`, and
successor freeze
`e66c5d7a42c3e4f1e9b6e7e3d4e36e96d54b4916d30d3f7110d6e2d03fa085a2`.
It preserves completed Qwen3.8 records but cannot authorize Qwen3.6 reuse.
Eligible model-visible inputs, prompt, renderer, scorer and inference settings
did not change.

The next action is to resume the background queue, observe ten newly completed
cases at ten-minute intervals, and then stop only active monitoring while
leaving the queue running.

## Resume observation

The repaired Qwen3.8 queue started successfully with vLLM 0.24.0 and resumed
by call key. After two ten-minute observations it had produced 18 new complete
case groups, exceeding the requested ten-case audit. The first ten comprised
seven inference-eligible cases (28 completed arm records, 56 parsed stages) and
three ineligible cases (12 zero-call terminal records). All four arms were
present per case; record hashes, Stage-1/Stage-2 parse and stop reasons,
token/latency accounting, RCA score fields, and same-prefill attention
artifacts passed inspection. No infrastructure error, truncation, traceback or
missing-image recurrence was found.

Two retained predecessor `protocol_ineligible` records omit the newer explicit
`model_calls: 0` field, but contain no stages or responses; the two newly added
arms for that same case carry the explicit zero-call field. This is recorded as
a backward-compatible schema warning and the immutable predecessor records are
not rewritten.

Active monitoring ended after this audit. The Qwen queue remains running, a
detached recovery supervisor will resume it by call key if the monitoring-owned
launcher exits prematurely, and the detached Gemma watcher remains
`waiting_for_qwen38`. Neither supervisor permits Gemma to overlap Qwen.

# 2026-07-31 — Readable topology was necessary but not sufficient

The complete scientific summary is in
`docs/2026-07-31_rq0_followup_grounding_topology_and_v7_results.md`.

## Work completed

- Audited the formal A/B discordances without modifying any formal artifact.
- Added an atomic visual-grounding task compiler, three-condition runner,
  controls, per-call conversations, and a control-valid analyzer.
- Added compact and large directional edge-key renderers and cross-model
  actual/swapped/no-image qualification runners.
- Promoted the qualified large key into
  `DashboardConfig.topology_edge_key` and the `rq0_v7_edge_key` preset.
- Bumped the renderer version to 7, pinned its fingerprint/golden hash, and
  retained `none` as the default edge-key value.
- Added a paired v6/v7 case-level RCA runner with pixel, fact-hash, prompt-text,
  token, and order audits.

The renderer code was extended rather than forked. The diagnostic edge-key
module now reuses the production primitive in `vlmrca/render/edge_key.py`, so
the tested pixels and the configured renderer pixels share one implementation.

## Runtime notes

The first topology client attempt used `venvs/infer`, which intentionally lacks
matplotlib, and failed before making any model request. All clients thereafter
used `venvs/tools`; vLLM servers continued to use `venvs/infer`.

Both servers used the frozen eager BF16 configuration and 0.65 memory ceiling.
They were polled at low frequency after startup. Shutdown emitted the familiar
vLLM asynchronous output-handler `EngineDeadError` after SIGINT; all requests
had already completed and the experiment records contain no infrastructure
failures.

## Evidence chain

1. Formal visual input changes top-1 in 21–22% of cases but breaks more correct
   text answers than it fixes.
2. Actual dashboards beat swapped/no-image controls on most atomic facts.
3. Curved topology edges are the shared exception: Qwen 25%, Gemma 8.3%.
4. The large explicit key reaches Qwen 100%, Gemma 91.7% with strong controls.
5. In paired RCA, v7 changes only one scored case per architecture, in opposite
   directions: Qwen ΔMRR −0.0208; Gemma +0.0625.

This rules out the simple story that the negative RQ0 result was merely caused
by unreadable topology edges. The edge defect was real, but repairing it did not
reliably change causal integration.

## Decision

Do not spend fresh reserve cases on renderer v7 and do not start generic visual
grounding SFT. The next intervention should target case-level causal integration
through SFT, after the project creates and freezes the unified training entry
point, exposure ledger, supervision schema, and unused evaluation split required
by `Codex.md`. GRPO remains out of scope for this paper.

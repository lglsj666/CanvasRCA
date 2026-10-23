# RQ4.10 — Evidence domain, context compression and marginal annotations

Implementation scope: 20 new single-call RCA conditions; 220 exposed development cases; 5,700 maximum new calls. The initial delivery was static-only. The user subsequently authorized CPU regression, the three registered GPU smokes, and formal launch after all pass. See current qualification receipts and findings for actual completion; authorization alone is not qualification.

The pure-visual organization baseline was corrected with explicit user approval on 2026-10-22: native RQ4.9 marginals did not have sample numeral columns. All four V organization conditions therefore share a new complete-pair baseline sourced from the frozen hybrid pair packet. Other branches retain the historical U28 image. No historical input is rewritten.

- [Approved plan](../../docs/experiment_plans/RQ4_10_Evidence_Domain_Context_and_Glyph_Plan_2026-10-22.md)
- [Protocol, differences and literature](descriptions/RQ4_10_experiments.md)
- [Implementation and qualification roadmap](descriptions/RQ4_10_roadMap.md)
- [Unique findings state](findings/exp_domain_context_findings.md)

Five functional modules: `utils.py` holds interfaces/receivers/operators and atomic records; `exps.py` compiles inputs and adapts the frozen model; `gates.py` validates, freezes, analyzes and finalizes; `main.py` owns the explicit CLI; `tests.py` contains future regressions. Scoring imports `scorer` exclusively. Additive rendering operation: `renderer.operations.domain_views` / `web/domainView.ts`.

Static entry (no browser, data preparation or model imports):

```bash
cd /home/lglsj/CanvasRCA_nibi
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python3 -m RQs.RQ4_10.src.main static
```

Commands are `unit`, `prepare`, `aggregate`, `runtime`, `visual --review-file PATH`, `freeze --scope SCOPE`, `gpu-tensor`, `run --scope SCOPE`, `review --scope SCOPE`, `analyze`, `finalize`, and `view --key KEY`. Every CPU/GPU stage requires an independently issued `authorization/<scope>.json` with `authorized:true` and the exact current `fingerprint`; GPU additionally requires complete bound qualifications and a frozen queue. No command auto-issues authorization. All execution defaults remain false.

GPU launch uses the unchanged, qualified local environment wrapper inherited from RQ4.9. It sets `VLLM_USE_FLASHINFER_SAMPLER=0`, the native allocator, offline model paths and the existing caches. A bare Python invocation misses those settings and can fail in sampler warmup while looking for `nvcc`. Wrapper hashes and the effective settings are recorded in `qualification/runtime_environment.json`.

```bash
cd /home/lglsj/CanvasRCA_nibi
source RQs/RQ4_9/scripts/environment_local.sh
python -u -m RQs.RQ4_10.src.main run --scope formal
```

The command remains gated by current qualification and authorization. Use `run --scope smoke_organization`, `smoke_operators`, or `smoke_qa` only within the corresponding registered smoke window and ledger.

Resume trusts canonical `completed/<key>.json` and `phase_complete.json`. Requests are immutable content-addressed readable JSON and PNG. Actual feature grouping, MRoPE/selection metadata, attention summaries, full raw responses, evaluator contexts and costs remain recoverable. Finalization verifies required hashes before removing only this experiment's redundant preparation/cache files; it never cleans historical experiments.

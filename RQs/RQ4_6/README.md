# RQ4.6 — pod joins and uniform support closure

**Complete CPU qualification and the18-call GPU smoke passed. The frozen local formal experiment is running.**

[Plan](../../docs/experiment_plans/RQ4_6_Pod_Bound_Relation_Join_Plan_2026-10-19.md) · [Current findings](findings/exp_pod_join_findings.md) · [Live progress](results/pod_join_v1/formal/progress.json) · [Owner/log](results/pod_join_v1/formal/owner.json)

Ten new RCA arms: five source-exclusive hybrids, two pure-visual deployment conditions and three U-budget pruning refinements. Historical T_FULL, MARGINAL_FIVE, A_UNIFORM_E50 and H_MARGINAL are references, not fresh baseline calls. Registration is2,620 formal positions,18 smoke calls and112 infrastructure-recovery slots:2,750 initiated calls maximum. U_QA is an independent reading task. References do not spend calls; repeats always invoke the model.

The user's cost-first HybridSummaryBudgetV1 removes raw metric arrays, retains existing core/window statistics, summarizes AUX series with observed first/last/extrema and retains eight original pair samples per phase. All source omissions are auditable. Pure-visual evidence is not deleted. Hybrid input gates are≤0.90×T_FULL/H_MARGINAL; the total-token target is≤0.80×H_MARGINAL without ranking loss. Under explicit user flexibility, pure cost limits are1.10×U; the three pruning conditions still retain exactly U's K.

Qualification:39 unit regressions,220-case input/source/render/processor checks,220-case affected pruning refresh and evaluator identity audit,32-case mechanism preparation,43 runtime checks, passive-input/MRoPE invariance, deterministic redraws and actual image review. Smoke18/18 committed and actual request/image hashes, rescoring, attention mappings and ledger were inspected. Model reading/ranking errors remain outcomes; smoke accuracy did not select or tune methods.

Five modules: `exps.py` compiler/selector/native adapter, `utils.py` identity/scoring/storage, `gates.py` qualification/statistics, `tests.py` regressions and `main.py` lifecycle. All graphics use registered shared `src/renderer/` components. Existing renderer defaults, historical inputs/results and Codex.md remain protected.

Local deployment: BF16 Qwen, native vLLM,40960 context/8192 output, eight CPU workers, GPU concurrency8, VRAM fraction0.8. Heavy compilation/rendering completes before GPU startup; runtime preparation uses bounded RAM, with no disk spool. No Nibi job is submitted by this launcher.

```bash
cd /home/lglsj/CanvasRCA_nibi
source RQs/RQ4_6/scripts/runtime_environment_local.sh
"$rq46_python" -B -m RQs.RQ4_6.src.main status
```

`pause` requests drain; `resume` restarts the frozen formal queue and skips atomic committed calls. `view --key <logical-key>` renders a directly readable conversation view from exact retained requests, PNGs and outputs. `analyze` and `finalize` operate offline. Source-bound CPU/smoke/formal credentials are separate; configuration defaults remain disabled.

After all formal writers drain, finalization verifies the retained reference/hash graph, retires duplicate preparation manifests and unreachable preparation images, deduplicates immutable content and removes runtime cache. Actual prompts, images, outputs, histories, scoring data, token operations and every collected attention measurement remain readable and recoverable. Limits:25 decimal GB per10,000 actual completed calls, attention1GB per10,000. The layer3 attention scope is last-prompt/first-decode only.

Historical gain/harm review JSON in `findings/` is evaluator-only and is never a selector, prompt or routing input. Formal performance is pending; all220 cases remain exposed development data.

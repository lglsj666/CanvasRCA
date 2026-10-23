# RQ4.6 findings and execution status — 2026-10-19

**Current state: all2,620 formal positions committed and detailed analysis completed; automatic storage retirement FAILED after inference and remains pending.** There are2,601 actual formal calls and19 exact references, plus18 smoke calls. No infrastructure result is missing. See the [complete report](../../../docs/experiment_reports/RQ4_6_Qwen_Analysis_2026-10-19.md), [progress](../results/pod_join_v1/formal/progress.json) and [frozen contract](../results/pod_join_v1/frozen/manifest.json). A passed inference progress marker does not qualify storage retirement.

## Complete results and decision

- Best new hybrid point estimate: H_MARGINAL_PHASE standard/tolerant MRR0.4590/0.4590,12,716.6 total tokens/case. Relative to historical H_MARGINAL:−0.0322 MRR and−39.20% tokens; A22/A25/AegisLab deltas−0.0014/+0.0050/−0.0730. This is a measured lower-cost tradeoff, not ranking-preserving compression.
- Nominees H_POD_PHASE, V_POD_BRIDGE and P_U_COMBINED attain standard MRR0.4406,0.2771 and0.3055. All fail their ranking engineering targets; cost targets pass. Best new pure arm P_U_NEIGHBOR_PAIR0.3436 remains below historical U0.3517. Do not adopt a post-hoc winner or automatically start another sweep.
- Seven-comparison event-group Holm: V_POD_BRIDGE−V_POD_SEPARATE is negative(pH0.0116), as is P_U_COMBINED−P_U_NEIGHBOR_PAIR(pH0.0139). Tolerant sensitivity attenuates the first(pH0.0691); the second remains negative(pH0.0291). Full denominators and invalid outputs are preserved.
- All2,290 RCA and330 QA outcomes were recomputed;1,928 unique visible PNGs and5,512 committed sidecars hash-verified;880 historical records verified. No model call was added for analysis. Thirty fixed QA cases plus explicit post-hoc examples show percentile/source confusions, output-interface losses and reason/ranking contradictions. Fixed AegisLab QA cases do not cover the full-cohort marginal regression.
-716 unique attention measurements cover layer3 last-prompt and first-decode queries only. Records plus deduplicated measurement mappings are about29.19MB; no claim about final ranking-token attention or causal sinks. Actual formal throughput12.12 calls/min over3h34m35s.
- Storage protection failed on preparation requests absent from the formal queue: four smoke-only and18 CPU-only mechanism requests. All formal outputs remain intact; no cleanup or new inference was performed during analysis. Current result-tree unique bytes about11.724GB exceed the6.5475GB final budget for2,619 actual completed calls; final retention is NOT qualified.

The qualification and launch details below are historical execution evidence, not the current running state. User-authorized hybrid evidence omission is a registered system comparison, not a lossless same-fact visual comparison against historical complete inputs.

## Scope and authority

Ten single-call RCA arms: five hybrid, two pure-visual deployment conditions and three U-based pruning refinements. Nominees remain H_POD_PHASE, V_POD_BRIDGE and P_U_COMBINED. Historical T_FULL, MARGINAL_FIVE, A_UNIFORM_E50 and H_MARGINAL are reused; no historical baseline is rerun. All220 cases remain exposed development data. Codex.md and historical source/default renderer semantics were not modified by this implementation.

Formal registration:2,200 RCA +330 QA +90 independent repeats =**2,620 positions**. Identical requests may reference committed answers; independent repeats always invoke the model. The experiment ceiling is**2,750 initiated calls**, including18 smoke calls and112 allowed infrastructure-recovery attempts. No new arm or accuracy retry is authorized by unspent budget.

## Authorized cost revision

The user permits aggressive hybrid evidence removal while treating retained ranking performance as the empirical objective. HybridSummaryBudgetV1 removes raw core metric arrays while retaining their original window/statistical summaries and units; AUX records retain observed first/last/minimum/maximum with source positions; each phase retains eight deterministic original request-pair samples, including endpoints, with original sample IDs. Trace, log, population and relationship facts remain. All five hybrid arms use the same projection. This is deliberately lossy, not reversible compression or a same-fact comparison against pure vision/history.

Pure-visual diagnostic evidence remains complete in the original dashboard. Under the user's explicit cost flexibility, the pure input and total-cost engineering limits are1.10×U; pruning arms still retain exactly U's token count. No pure-visual evidence was deleted to pass qualification.

Actual per-dataset H_POD_PHASE input ratios:

| Dataset | / historical H_MARGINAL | / historical T_FULL |
|---|---:|---:|
| AIOPS-2022 |0.6493|0.6192|
| AIOPS-2025 |0.6042|0.5672|
| AegisLab |0.5876|0.5469|

These are complete input counts, not measured total input+output costs or ranking improvements. All five hybrids satisfy the stricter0.90 input gates against both historical comparators. Pure pod input increases are2.45–5.81% versus U; pruning input counts equal U.

## Repairs and CPU qualification

- New opt-in pod components use per-row geometry, indivisible entity identities and explicit observed edge directions; no existing renderer component was changed. Budget marginal components explicitly register the eight-sample contract and reuse existing drawing bodies, leaving the old32-sample contract intact. Renderer caches bind their actual component/geometry source.
- The combined pruning optimizer previously stopped at64 improvements and remained too similar to value-only masks. Its registered bound becomes128; single-objective arms remain64. Exact K, anchors, objectives, one-grid coverage and anti-redundancy gates remain unchanged. The full220-case affected refresh and actual processor checks pass. Combined masks now differ by the registered10% from both single-objective masks in220/220 cases. Value-only intervention eligibility passes32/60,33/60 and97/100; the other refinements also pass their full-denominator gates. No model scores guided this repair.
- Private scoring uses small hash-verified retained contexts instead of repeatedly parsing a109MB historical index. All220 mappings and accepted-label contexts match the original semantic hashes. New scoring imports use only `scorer`.
- Earlier logic review fixed QA-context collisions, reference rescoring, incomplete source/phase checks, isolated-entity retention, cohort coverage, pause/ownership handling and interrupted finalization. Original failed/interrupted CPU stages remain documented separately.

Qualification receipts under[qualification](../results/pod_join_v1/qualification/):39 offline unit tests;220-case source/render/capacity audit;220-case affected pruning refresh;220-case evaluator identity check;32-case mechanism preparation;43 runtime checks including image-free hybrid limits; attention input/MRoPE invariance; deterministic repaints; fixed arm/dataset and public boundary visual review. Scoped source/AST and generation-identity proofs carry unchanged CPU checks after scoring/storage-only repairs; unchanged dashboards were not needlessly regenerated.

Static validation also covers TypeScript, five modules/2,835 functional lines, configuration/import boundaries and105 protected pre-existing files. All configuration execution switches remain closed by default; separate source-bound qualification credentials activate the frozen scopes.

## GPU smoke and artifact inspection

**18/18 actual calls committed; no infrastructure error; elapsed168.91s including model startup and saving.** The call window was87.85s, or12.29 calls/minute; end-to-end throughput including one-time startup was6.39 calls/minute. This small smoke is not a guarantee of full-cohort throughput.

Actual requests match the frozen smoke queue. All17 unique model-visible PNG hashes and committed sidecars pass; output/token accounting and independent standard/tolerant rescoring match. Thirteen RCA answers satisfy the registered output schema; the five QA outputs are structurally valid. QA and reasoning still contain model reading/binding errors: these remain measured outcomes, not evidence of implementation correctness or a reason to tune/re-answer smoke cases. Ranking accuracy was not a qualification gate.

All five requested attention measurements were collected and their actual region mappings reconstructed and hash-verified. Layer3 covers the last prompt and first decode query only, not final-ranking queries or full matrices. Summary plus deduplicated geometry/selection mappings total427,430 bytes across18 calls, projecting to0.2375 decimal GB/10,000 calls under the smoke mix. Formal retention still enforces the registered actual size limits.

The native vLLM smoke service shut down cleanly. It used BF16 Qwen, local Blackwell FlashAttention,40960 context/8192 output, eight CPU workers, GPU concurrency8 and utilization0.8. Optional DeepGEMM import warnings did not prevent the working FlashAttention path or any call. Detailed evidence:[smoke artifact review](../results/pod_join_v1/qualification/smoke_artifact_review.json).

## Retention and recovery

Preserve actual prompts, PNGs, selections, outputs, conversations, labels, costs/failures and every collected attention measurement in ordinary readable files. After all formal writers drain, verified duplicate prepared request manifests are retired only when their complete diagnostic inputs remain in the frozen queue and committed per-call records; unreachable preparation-only image objects are removed after reference/hash checks. Runtime caches remain until no longer needed. Actual conversation/output files and required public dependencies are never deleted. The finalizer enforces25 decimal GB per10,000 completed calls and the separate attention limit; two dedicated cleanup tests plus interrupted-finalization regressions pass.

Atomic per-call completion markers, a durable shared call ledger, phase markers, live-owner exclusion and bounded RAM prefetch support power-loss recovery. Resume skips committed calls and does not bulk revalidate old contexts. The formal queue, source and generation recipe are frozen; no partial-result tuning or automatic winner search is permitted.

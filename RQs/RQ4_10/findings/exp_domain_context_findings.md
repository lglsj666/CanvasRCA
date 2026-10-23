# RQ4.10 findings — unique current status

**Current: all CPU and GPU numerical/artifact qualifications passed; the user explicitly accepted the measured operator speed on 2026-10-22. Formal execution is running in persistent tmux; startup and initial committed inputs/outputs were verified with no runtime errors.**

Current source fingerprint: `8bca5ee08aea68122411b76fb2be23e38ff60109168d90d77526ffb5575884e6`. Frozen formal queue: 5,465 positions (4,490 RCA including repeats; 975 QA). Exact references can reduce actual model calls. Operator GPU utilization remains 81.2892%, below the original 82% measured gate; this run is authorized by the explicit user acceptance recorded in `results/domain_context_v1/authorization/operator_speed_acceptance.json`. Original measurements and the blocked-speed receipt remain intact. Runtime: qualified local BF16 Qwen/vLLM, eight CPU workers, GPU concurrency eight, memory fraction 0.8.

## Historical static-only handoff (superseded by subsequent user authorization)

Date: 2026-10-22. **Code implemented; static checks passed. STOPPED at the requested boundary.**

- 20 new RCA conditions; at most 5,480 scientific calls / 5,700 total registered calls. No calls initiated.
- Five functional modules, 2865 nonblank/noncomment source lines (limit 7,500).
- Static receipt: `static_check.json`; source fingerprint `3c2c3f6a24dcd11aaa66511174cbb70f698c2575376eb1e63063e905e62d95c7`.
- Python AST/compile/name resolution, TypeScript `tsc --noEmit`, registration/budget/default-off switches, centralized scoring imports and historical source protection passed.
- CPU regression, renderer/browser, processor token measurement, visual feature extraction, GPU smoke and formal execution: **NOT RUN**. No execution authorization was issued.

## Confirmed source correction

RQ4.9 native pure-visual marginals do not contain per-sample exact numeric columns; hybrid complete marginals do. The initial plan's assumption was incorrect. After explanation, the user explicitly approved a NEW complete-annotation V baseline on 2026-10-22.

The four V organization conditions now share matching frozen complete-pair records, including individual numeric annotations and population statistics. Source hashes and each added visible field are recorded by the compiler. Other historical facts remain; only this new baseline is re-laid out using the existing unified renderer. Its comparison with historical U28 includes the documented fact/layout change. Hybrid H_EXACT remains a historical reference. No historical source or result was rewritten.

## Qualification still required

Static success does not establish 220-case capacity, renderer pixel compatibility, actual QA visibility/precision, token budgets, native GPU numerical correctness, speed, performance or final artifact density. The new complete-pair visual baseline must fit 4096² / 28 cards without losing evidence or shrinking text; failure blocks CPU admission. These are explicit future gates, not claimed successes.

The next authorized action, when requested, is version-bound CPU qualification. No automatic launch follows this handoff.


## 2026-10-22 qualification resumed by user

Latest authority supersedes the static-only stopping point: run CPU regression, all three registered smokes, then launch formal only if passed. Fourteen offline unit regressions passed. Three real pilot cases passed after fixes to build targets, complete-card independent-column packing, fixed-height PACK glyphs, hidden-panel audit, and oracle-blind sentence/unit QA extraction. Full 220-case CPU preparation is running with eight physical-core workers. No GPU/model calls yet. Current credentials under results/domain_context_v1/authorization and logs under logs/.

## Qualification update — 2026-10-22

Current fingerprint `8bca5ee08aea68122411b76fb2be23e38ff60109168d90d77526ffb5575884e6`: static, 15 unit regressions, all 220 input cases, 33 QA preparation bundles (30 formal plus three smoke identities), offline runtime mapping and finite visual review passed. CPU full preparation took 2,220.9 seconds. Dataset counts are 60/60/100. Maximum RCA input is 23,149 tokens, plus 8,192 output reserve = 31,341. Three source-bound smoke queues contain 18 organization, 18 operator and 17 applicable QA calls. Organization smoke has been started; smoke and formal qualification are not yet declared passed.

## Current qualification state — 2026-10-22

All CPU qualifications passed: 220/220 input cases, 15 unit regressions, 33 QA preparation bundles, actual processor transport and finite image review. Three real GPU smokes committed 53 calls in total: organization 18, operators 18, QA 17 (one registered rename control was inapplicable).

- Organization: integrity passed; GPU mean 86.7857%, throughput 8.2539 calls/min.
- Operators: independent GPU numerical check and all 18 input/output/attention artifact checks passed; GPU mean 81.2892%, throughput 6.2545 calls/min. The registered speed gate is NOT passed. Initial three serial requests averaged 74.7636%; the concurrent segment averaged 84.5225%. These segments do not replace the full measured interval.
- QA: integrity/receiver/scoring passed; GPU mean 91.8%, throughput 15.0453 calls/min. Wrong-source and wrong-entity answers remain correctly scored errors. Fenced JSON, prose plus final JSON and entity-type prefixes retain valid answer credit.

Attention summaries were present for all calls and stayed between 3,620 and 12,427 bytes per call; four layers × two actual queries are recorded. These smoke file sizes alone do not establish the final experiment-wide retention density, which remains subject to final accounting including mappings.

The formal queue is frozen at 5,465 logical positions (exact references can reduce actual calls). Formal execution is NOT started. The user has been asked whether to accept the measured operator speed; until an explicit answer arrives, its speed gate remains blocked. No scope, threshold, smoke window or consumed-call ledger has been reset.


## Formal running — user speed acceptance, 2026-10-22

User explicitly accepted the measured operator speed and authorized launch. Original 81.2892% measurement and original unmet 82% gate remain intact; this is a scoped operational acceptance, not a rewritten result. At handoff, 6/5,465 positions are committed, 8 requests are active, and no runtime errors are recorded. First 6 committed request/image hashes, BF16/token accounting, raw answers and scores were checked. This is startup validation, not a full-run performance claim. See `formal/launch_attestation.json` and `formal/progress.json`. Assistant stops here; tmux keeps formal execution running with atomic resume support.

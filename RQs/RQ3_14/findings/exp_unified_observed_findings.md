# RQ3.14 unified observed binding

2026-10-02 final: all 1980 formal positions are terminal: 1966 committed responses and 14 request timeouts. The owned service exited. Formal attempts total 2016, including 36 interrupted attempts during WSL recovery; with 18 smoke attempts, cumulative use is 2034/2040. Timeouts remain unknown, and 16 invalid-entity responses retain their original zero scores.

The preselected WINDOW_VISUAL is **not adopted**. Paired V−RAW MRR is +0.117251 on AIOPS-2022, −0.020904 on AIOPS-2025, and −0.011167 on AegisLab. All four registered primary comparisons fail their adoption gates. Visual does not beat WINDOW_TEXT, WINDOW_PIXEL or WINDOW_MARKLESS; no isolated benefit of graphic marks or lower token cost is established.

The registered secondary WINDOW_TEXT−SAFE_TEXT contrast is positive: n=218, ΔMRR +0.046942, case Holm p=0.016502; equal event-group Δ +0.052604, Holm p=0.014463. This is a text-summary result on exposed eval, not success of the preselected visual method. Dataset-specific exploratory contrasts remain non-significant after their 27-test correction.

On the old 20 Aegis cases, visual-vs-raw loss narrows from −0.129167 in RQ3.13 to −0.058333; added80 cases are nearly tied (+0.000625). Matched AIOPS-2022 visual absolute performance does not improve over RQ3.13. Paired visual/raw total-token ratios are 1.154909/1.183810/1.153888. No cost-reduction or credibility claim is warranted.

All 1966 completion graphs, scores and actual saved inputs were audited; 167 frozen files remain unchanged. The registered 36-case/324-position reason review read 321 responses (3 timeouts); 25 targeted claims across 15 cases received explicit source/arithmetic checks. Unchecked axes remain unknown. Ranking correctness does not guarantee correct timing, units, entity binding or causal claims.

Canonical detailed report: [RQ3.14 Qwen analysis](../../../docs/experiment_reports/RQ3_14_Qwen_Analysis_2026-10-02.md). Reproducible tables and claim evidence: [analysis_detailed_v1](../results/unified_observed_v1/analysis_detailed_v1/). Stop this implementation under the frozen protocol; no automatic follow-on experiment, new test or training is running.

## Qualification and launch history (preserved)

At launch, all qualification gates passed and the queue was verified running with committed responses; the historical receipt remains at formal/launch_receipt.json. The sections below document that earlier qualification boundary rather than the final efficacy result.



Clean rewrite in five functional modules. Main dashboard reuses registered metric.line and trace.paired_bars; appearance/indexing/spacing operations execute through the unified registry and save their audits. Only literal.text is added for the exact-summary screenshot control; no new operations. The original line component and all old operations remain unchanged. Curves connect available measurements across missing positions without special annotations. Full original facts stay in common text; derived summaries belong to the strong-text/screenshot controls. The markless control retains numeric-label positions, so it does not remove every spatial cue.

## Verification

- Python AST/import/config/shell and critical Ruff checks; TypeScript typecheck/build: passed.
- Unified renderer:35 tests passed, including actual-browser tests, zero skipped.
- Full CPU:220 cases ×9 arms,660 actual PNG audits,134074 visible bindings,2640 independent metric checks,9 deterministic rerenders; passed in235.13s.
- Source-native Trace crosscheck:1284 records; independent raw adapter replay matches all three preselected cases. Full-roster partition/identity/event-group separation passed.
- Mean WINDOW_VISUAL/RAW input ratios: A22 1.155633; A25 1.184700; Aegis 1.154480, all<=1.20. Maximum input23399+8192 output<=40960; zero context exclusions.
- Official checkpoint/tokenizer/processor identities checked; source freeze archives167 files including renderer bundle and font. Global model/scorer/split recipes preserved.
- GPU smoke:18 real attempts,18 committed responses,0 timeouts/truncations/infrastructure failures; 185.20s of600s. All actual text parts, rendered image hashes, native processor token counts, trajectories and conversation artifacts match preparation. All18 responses inspected. Each arm appears twice; each dataset has6 arms, so not every arm×dataset pair has GPU smoke coverage. Every pair has CPU coverage.

## Repairs and caveats

The first CPU preview duplicated the summary beside the graph and exceeded the input margin on one preview. It is preserved; removing that repetition retained all original vectors. One initial preparation command omitted the local resource environment; corrected without changing data or losing eight commits. CPU qualification was restarted after adding bundle/font identity checks and aligning the SAFE description with the implemented fixed reading rules. No GPU call preceded those fixes.

Some smoke reasons still misuse log2 changes, overclaim causal timing, or disagree with their own ranking. These model outcomes are preserved; no accuracy-based retry, selection or tuning occurred. No improvement in MRR or credibility is claimed from smoke. This exposed-eval development experiment is not independent confirmation.

## Execution boundary at launch (historical)

Registered9-arm full matrix1980, plus18 smoke and42 repair reserve gives2040 total allocation; earlier RQ ledgers remain preserved separately. Full runner uses36 concurrent requests, atomic per-call/model-phase commits, streamed partials, an8-thread writer pool and lightweight resume. It shuts down its owned model server on completion. Stop agent work after the full queue demonstrably runs and commits results; do not wait for full outcomes or change methods from partial scores.

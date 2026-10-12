# 2026-10-02 — RQ3.14 unified renderer qualification

## Scope and status

Version `rq314_unified_observed_v1`. Single primary agent, local Qwen3.8-27B BF16. Full exposed eval cohort: AIOPS-2022 60, AIOPS-2025 60, AegisLab100. Static, whole-roster CPU and GPU smoke qualifications passed. Formal1980-position supervisor submitted; live start confirmation is recorded separately in formal/launch_receipt.json. These are qualification outcomes, not formal RCA results.

## Implementation

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

## Execution boundary

Registered9-arm full matrix1980, plus18 smoke and42 repair reserve gives2040 total allocation; earlier RQ ledgers remain preserved separately. Full runner uses36 concurrent requests, atomic per-call/model-phase commits, streamed partials, an8-thread writer pool and lightweight resume. It shuts down its owned model server on completion. Stop agent work after the full queue demonstrably runs and commits results; do not wait for full outcomes or change methods from partial scores.


Formal launch verified: supervisor 70617, runner 71339, server 70624 alive; 31 atomic completed markers at verification. Ledger states: {'complete': 31, 'started': 36}. No partial efficacy scores inspected. The authorized launch stopping boundary has been reached; detached full experiment continues unchanged.

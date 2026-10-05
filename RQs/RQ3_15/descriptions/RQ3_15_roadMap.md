# RQ3.15 execution state

2026-10-03 final: **formal experiment and detailed analysis complete; preselected method not adopted**.1320 terminal positions=1279 real responses+36 fallback references+5 timeouts;2 model format failures retain zero. Total1302 attempts including18 smoke. Formal completed11:42:16 America/Toronto; owned service exited. No further model work is running or scheduled by this experiment.

[Detailed report](../../../docs/experiment_reports/RQ3_15_Qwen_Analysis_2026-10-03.md) and [final findings](../findings/exp_request_joint_findings.md) supersede the operational snapshots below. All four registered primary comparisons fail case/group Holm significance; V−MARGINAL is negative and Aegis V−BASE is+.0007, below+.02. The planned stop rule closes this candidate route without automatic layout changes, retries or a successor. RQ3's overall research goals are not thereby achieved. Source, inputs, original scores, registration and frozen qualification are preserved.

## Historical execution snapshots

2026-10-03: **resumed and running**, explicitly requested by the user (“帮我重启实验吧。”); submitted10:50:22 and verified10:53:42 America/Toronto. This lifts the pause below for the remaining frozen RQ3.15 matrix. Preflight confirmed unchanged qualified source and822 terminal positions; the resumed queue correctly starts486 real calls+12 references. Verification snapshot:804 real responses committed (10 new),36 new requests active,0 new failures; prior794 responses and4 timeout outcomes remain intact and no old attempt was resubmitted. Supervisor1925/server1939/runner2338 alive; live attestation passed, actual GPU-memory-utilization0.75, GPU utilization99%. No source/config/preparation or recipe changes, no new smoke or reset budget. Current state: [resume receipt](../results/request_joint_v1/formal/resume_receipt.json). Counts are the verification snapshot; earlier pause and launch records below are historical.

2026-10-03: **safely paused by user**, requested01:06:58 and verified01:10:34 America/Toronto. No new submissions after the signal; all36 active calls drained successfully. Runner, supervisor, model server and engine exited; port21955 closed.794 real responses+24 fallback references committed;4 earlier request timeouts preserved,822/1320 terminal positions,498 pending. Formal798 attempts+smoke18 remain spent. No new failures during draining; SQLite quick check and completion-marker checks passed. **Do not resume until the user explicitly authorizes it.** Evidence: [pause verification](../results/request_joint_v1/formal/pause_verification_20261003.json), [pause instructions](../results/request_joint_v1/formal/PAUSED_BY_USER.md). The launch state below is historical.

2026-10-02 23:49:54 America/Toronto: **formal experiment running**, verified at23:53:42 after the user's explicit full-run request. The earlier post-smoke stopping boundary has been fulfilled and is superseded for execution of this frozen matrix only. The launch verification snapshot has17 committed responses,36 in-flight attempts and no failed position; it is a timestamped snapshot, not a continuously updated counter.

- 220 exposed eval cases: AIOPS-2022 60, AIOPS-2025 60, AegisLab 100; six arms, 1320 registered positions.
- First pass: 1284 real calls and 36 exact-input fallback references; all 220 PAIR_REPEAT positions remain real independent calls. All cases remain in the intended comparison denominators.
- Formal attempt limit1362; prior smoke18 remains spent; combined limit1380. No scientific, input, renderer, scorer, model recipe or threshold change.
- Operational activation changes only two functions in `src/gates.py`. Frozen config remains immutable; explicit authorization, old/new source archives, AST compatibility and negative gate checks are under `results/request_joint_v1/qualification/activation_v1/`.
- Local Qwen BF16, context40960/output8192, GPU memory utilization0.75. Detached supervisor owns its server and runner, uses atomic commits for resume, and closes its owned service on completion.
- Live state and log: [launch receipt](../results/request_joint_v1/formal/launch_receipt.json). No interim efficacy tuning; no automatic successor experiment.

## Historical qualification boundary

2026-10-02: **qualified and stopped after smoke**, as requested.

- Five functional modules implemented; 176 source files frozen.
- Full CPU: 220 cases, 211 applicable, 422 PNGs, 341,635 independently checked source pairs; all applicability, semantic, input-budget and capacity gates passed.
- Actual image review: 11 PNGs; six deterministic rerenders; all 211 joint/marginal pairs have matched common-label geometry.
- GPU smoke: 18 fresh calls completed in 203.26 seconds, including three independent repeats. No timeout, truncation or infrastructure failure. Persisted inputs, images, provider usage and canonical scores verified.
- Local Qwen used BF16, 40960 context, 8192 output adaptation and GPU memory utilization 0.75. Owned service stopped; port closed.
- Completed-phase resume skips process startup and input materialization. Formal launch remains disabled: 1320 registered positions, **0 formal calls**.

Runtime qualification does not establish graph perception, RCA improvement or explanation trustworthiness. Concrete model reasoning errors are preserved; no tuning followed smoke outcomes.

Detailed report: [CPU/GPU qualification](../../../docs/issues/RQ3_15_qualification_2026-10-02.md).
Evidence: [qualification summary](../results/request_joint_v1/qualification/qualification_summary.json), [gallery](../results/request_joint_v1/qualification/gallery.html).

Next boundary at qualification time was to await separate authorization. The user supplied that authorization above; the qualification evidence remains unchanged.

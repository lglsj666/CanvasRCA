# RQ3.9 registered protocol — 2026-10-01

The complete design and history audit are in
[the adopted plan](../../../docs/experiment_plans/CanvasRCA_RQ3_9_Joint_Comparison_Plan.md).
Executable config: `../configs/joint_comparison_v1.json`.

- 120 hash-selected exposed eval cases, 40 each AIOPS-2022/AIOPS-2025/AegisLab;
  seed42; no outcome- or label-based inclusion; no test, unused, RE2 or Gemma.
- TEXT_FLAT / TEXT_JOINT / VIS_SEPARATE / VIS_JOINT, 480 positions maximum.
- Complete inherited text survives. Two visual arms have identical component
  contents, dimensions and instructions, only component coordinates differ.
- At most two public relation-qualified comparison groups, at most three
  original observations per group; disjoint cards, deterministic ordering.
- Peer > host/pod > same-entity metric/operation > caller/callee observations;
  these are recorded associations, not invented health or cause assertions.
- Primary Holm family: joint vision versus joint text and separated vision.
  Secondary family: joint text versus flat text and separated vision versus joint text.
- Paired case Pratt-Wilcoxon and dz, no CI; dataset/macro/pooled distinct;
  event-group sensitivity and fault/granularity/eligibility exploratory breakdown.
- Design-infeasible excluded; request-timeout missing, no automatic retry;
  non-timeout infrastructure stops; invalid model outputs are outcomes.
- No-op identical requests are referenced, not re-generated or counted as
  independent repetitions. Report coverage and the full registered denominator.
- Existing unified-renderer components/operations/IDs/defaults are preserved.
  Additive extensions only. No renderer edits in this initial pilot.
- Historical Metrics share their case's wide-frame timestamp bin boundaries;
  the previous claim of per-series independently normalized clocks is retracted.
  No claim of automatic alignment across trace summaries/logs/onset units.
- Local Qwen BF16 uses the effective inherited runtime and 8192 output adapter,
  timeout300, concurrency36, no attention; CPU at most8 pinned physical cores.
- One logical smoke, three main-dataset eval cases, 12 planned/18 hard maximum
  calls and600s aggregate. No accuracy threshold for runtime qualification.
- Formal initiated-call cap480. Never reset ledgers to retry interrupted work.

These registered choices predate the first model request. Source hashes,
small roster and qualification records live in `../results/joint_v1/`.
The latest direct user authorization permits qualifying and launching this
pilot; it does not permit automatically expanding following partial outcomes.

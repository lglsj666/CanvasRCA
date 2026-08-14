# 2026-08-12 — RQ1 v18 runtime repair and smoke launch

## Scope and status

Repaired the Nibi execution and Q&A representation defects found before the
formal RQ1 rerun. No full experiment was launched. The final shared CPU
preparation completed and its artifacts passed structural, semantic, hash,
pixel-preservation, and manual visual review. Fourteen model-separated smoke
jobs were then submitted: one Qwen and one Gemma job for each of the seven RQ1
experiments, with all Gemma jobs dependent on all Qwen jobs.

## Repairs

- A single preparation command can materialize the exact base or formal shard
  roots consumed by GPU jobs. Smoke and full runners can explicitly reference
  a shared prepared experiment ID.
- Preparation preserves and validates the frozen segmentation-owned opaque
  incident ID. The renderer receives that opaque ID rather than a source case
  ID.
- Routed `R` uses the renderer's corrected propagation/log boundary and
  preserves metric, propagation, and directed-edge pixels exactly.
- Q&A metric facts now describe renderer-visible plot coordinates, ticks,
  printed summaries, and missing markers; raw 64-bin numeric values are not
  claimed as visible dashboard facts.
- Cross-region questions use directed caller-to-callee edges for topology
  traversal. Level 3 requires three distinct evidence regions and cannot fall
  back to a two-region cycle.
- Preparation uses at most four workers, atomically checkpoints completed
  cases, and resumes only under the same runtime freeze.
- The batch smoke launcher queues all Qwen phases before any Gemma phase. Each
  experiment still has exactly one logical smoke, represented by one job per
  model, and each job requests one H100.

## Qualification evidence

- Zero-call suite: passed; 61 arms compiled, 5,222 RQ1 functional source
  lines, and shell syntax/diff checks passed.
- Final preparation: Slurm `19706117`, completed in 50 seconds with exit
  `0:0`, four CPUs, 100 GB requested RAM, and about 1.52 GiB peak RSS.
- Prepared result ID: `rq1_v18c_smoke_shared_20260812`; three cases; runtime
  freeze `a7283471a7fefd0989344d724669e072fc29c147b9abcd09d6b5a635828a2abe`;
  prepared index `5f5693ead0c36e467298353b34ef26717dda021a3bbb47588156283ef73cb532`.
- All three cases retain their frozen opaque IDs and have 12 renderer-visible
  metric panels. `P_QA` source hashes equal `T_QA`; `H_QA` is strict
  image-first `V_QA + T_QA`; Level-3 region paths are distinct; routed metric,
  propagation, and edge-key pixels are unchanged.
- Manual review covered all three full dashboards and representative routed,
  M/R/L/G crop, directed-edge, and pixel-text images. The real dashboards and
  crops are legible and complete. Pixel-text is dense by construction because
  it preserves the exact frozen text without rewriting, and remains within the
  registered eight-image ceiling.
- Submitted smoke jobs are: `legacy_q9` Qwen/Gemma `19706762/19706769`,
  `cross_region` `19706763/19706770`, `typed_two_stage`
  `19706764/19706771`, `direct_rca` `19706765/19706772`, `matched_rca`
  `19706766/19706773`, `visual_counterfactual_rca`
  `19706767/19706774`, and `ledger_handoff_rca` `19706768/19706775`.
  Each requests 14 CPUs, 100 GB RAM, one H100, and 30 minutes. Every Gemma job
  has an `afterok` dependency on all seven Qwen jobs.

## Failed preparation attempts retained as diagnostics

Jobs `19703710`, `19704093`, and `19705685` did not produce valid reusable
preparation. They respectively exposed a missing deployment-path override, a
non-finite metric-coordinate conversion, and a misplaced routed-image
regression assertion. Each root cause was fixed before the final v18c freeze;
none is an authority for the submitted smoke jobs.

## Validity and next step

The preparation and static checks contain no model calls and do not constitute
scientific results. Smoke artifacts must be inspected after completion for
summary/verifier consistency, response length versus the 8,192-token RQ1
ceiling, parse/truncation state, partial-response behavior, conversations,
logs, persistence, attention artifacts, and call accounting. Full RQ1 jobs may
be considered only after those seven two-model logical smokes are qualified.

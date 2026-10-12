# 2026-09-29 — Local RQ3.8 identity-repair handoff

## Scope and status

RQ3.8 `ops_components_v7`, local WSL formal preparation on the registered 840-case eval/test roster. This is an implementation/operations record, not a model-result or scientific-efficacy finding. The repaired queue has resumed; formal model calls had not started at the time of repair. The registered RQ config SHA-256 is `bf9afca7709dea59ad30a3efdca4fa9a4879d89f2de3d512d081108f74608c5b`.

## What happened

Qwen shard 1 export stopped on AIOPS-2022 test case `INC-1D51AFFCB615` with `Public identity inventory differs from cached M/R/L`. The new topology exporter enumerated owners from **all metric column names**. The frozen parent `_entities` instead includes a metric owner only when at least one of its series survives `score_series`. Eleven `*-grpc`/`*-http` metric-column owners existed in the new enumeration but not in the parent; including them shifted 23 previously shared numeric aliases. Source graph, metadata and trace hashes matched the frozen context. This was a deterministic identity-policy mismatch, not evidence of a missing/corrupt per-case file or a model failure.

`src/renderer/topology.py` now reconstructs the exact frozen public `_entities` and case-local numeric mapping from metric values and distinct log/trace owner columns. It reads no log messages, private labels or raw data. The existing inventory and relation-binding fail-closed checks remain. The regression test `test_topology_identity_ignores_unscorable_metric_owner` covers the all-NaN metric-owner counterexample. Repaired source SHA-256: `f3d53cf0c7b589ace2378512166f68c814c9936c481ea459c7d44d27dc16b5c6`.

## Validity and caveats

Before resuming, all 398 previously committed export flags were compared against both old and corrected entity→numeric-ID mappings: **0 affected**. Thus no completed export/render needed deletion or regeneration. The failing case was exported under the repaired code: 23 cards, `facts_hash=e061800a419f88b54179b641cc3a2551d17dab1149c272c14835db3d674e82fa`. Four topology-focused CPU tests, shell syntax, Python compilation and RQ3.8 static gate passed. This targeted verification does not claim a new GPU smoke or final experiment validity.

The background queue `canvasrca-rq38-local-full` resumed in `RQs/RQ3_8/results/ops_components_v7/logs/local_formal_20260929.log`. It skips committed flags and continues export/render before Qwen then Gemma inference. At the first resumed check, export flags increased from 398 to 450 and the shard-1 export process remained active; no GPU model call had yet started.

## Decisions

Retain the 398 identity-compatible prior exports and all 282 completed renders. Do not weaken the identity guard, invent aliases for rejected metric owners, rebuild canonical per-case data, or rerun compatible artifacts. The corrected public identity rule applies to newly exported cases; no experimental arm, selected M/R/L fact, prompt, scoring rule or model recipe is changed.

## Blockers

None known for preparation after the targeted failing case passed. The queue remains subject to its normal fail-fast and artifact checks; completion and model performance are not yet established.

## Next steps

1. Observe export/render flags and the queue log for new failures.
2. Let the registered queue finish preparation, then its sequential Qwen/Gemma inference.
3. Audit complete results and failure statuses before scientific analysis.

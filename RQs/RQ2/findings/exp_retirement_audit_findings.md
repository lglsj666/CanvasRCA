# RQ2 retirement audit — superseded by RQ2.1

Status: **abandoned in its entirety by user decision, 2026-09-07**. This is an
audit experiment, not a new efficacy study. Preserve the original source and
numerical findings. Do not schedule an old RQ2 experiment or treat its selected
design/profile as an RQ2.1 authority. RQ3 is not automatically migrated or run.

## The selection experiment did not manipulate what it claimed

The consolidated report (`docs/RQ1_1_RQ2_1_findings/findings.md`, section on tool input collapse)
verified identical model-visible inputs across the four profiles for each
case, transport and model. Different answers to these requests are sampled
output variation, not evidence that a different tool changed diagnosis.

The implementation chain is reproducible from retained `src/exps.py`:

1. `build_tool_packet` receives the already selected parent packet, not the
   complete public metric/log/trace/edge universe. Missing upstream evidence
   cannot be recovered by weighting that packet.
2. `_tool_signal` accepts numeric Python values under selected key names. A
   formatted numeric string and fields such as `severity_z_display` are not
   read as the intended signal. A zero score may therefore mean adapter loss,
   not absence of telemetry. This is a schema risk, not proof every score was
   zero.
3. Profile weights change entity ranks, but selection takes eight entities.
   Where this covers the same relevant set, ordering differences do not change
   the selected set. The code explicitly converts that order to `selected_set`.
4. A shared, unweighted per-region sort and shared row caps choose the final
   facts. Weighted ordering is not propagated into model-visible evidence.
5. Profile metadata and its hash can differ even when ordered text and decoded
   PNG pixels do not. Integrity hashes alone cannot prove an intervention.
6. Small-budget synthetic tests did not establish differences at the actual
   formal eight-entity budget. Endpoint execution and successful parsing were
   mistaken for adequate scientific manipulation checks.

The old statement that none of four *different selection algorithms* improves
RCA is unsupported. Its numerical tables remain a record of the requests that
ran, not an algorithm comparison. Likewise, it cannot motivate learning on the
claim that genuinely different selectors failed. Four profiles did not faithfully
reproduce four published tools.

## Missing bridge and overloaded design variables

RQ2 introduced a new evidence-card projection, text fields/order, dashboard,
budget and decoding guide. A lower MRR than RQ1.1 cannot be attributed solely
to visual encoding. The retained cross-RQ report documents request differences
including extra fields and reordered log rows. Similar packet names, shared
models, or the same case roster do not establish equal inputs.

Dense selection changes content; reallocating cards changes screen space;
renderer clipping changes information. These must not be combined under a
claim about layout alone. An oracle over noisy outcomes is descriptive
headroom, not an available deployable policy or a promised RL improvement.

## Operational and visual pitfalls (not all invalidate complete results)

`docs/RQ2_issues.md` retains the detailed incident chronology and recovery
status. It documents inconsistent logical/raster coordinates, insufficient
clipping assertions, overlapping long labels, greedy packing failures and
stale dense-preparation caches. A manifest saying a fact exists does not prove
its text or graphic was drawn legibly. Later fixes do not retroactively prove
earlier images equivalent.

Read-stall timeouts with short partial output must not be blamed on long model
reasoning without evidence. Attention artifacts exhausted disk space and
required recovery. Valid completed requests were retained during those
recoveries; process restarts and hardware scheduling changes alone are not
scientific invalidation. Missing required attention is an artifact-integrity
issue, distinct from a wrong root prediction. Old verifiers and summary counts
must be interpreted under their own recorded recovery contract.

## RQ2.1 prevention matrix

| Pitfall | Required successor check |
|---|---|
| tools see a small preselected packet | public-pool source inventory precedes every selector |
| renamed shared weighted sorter | vendored original algorithm plus adapter equivalence tests |
| formatted fields silently score zero | explicit numeric/schema tests and original ranking audit |
| formal-budget interventions collapse | formal-capacity fixtures and real request/pixel comparisons |
| metadata hash mistaken for new input | selected IDs → facts → ordered text → pixels → request audit |
| renderer performs hidden second top-k | fixed selected-fact input and actual primitive binding |
| bridge prompt drifts | unchanged B_T/B_V references and separate T0/V0 calibration |
| selection, shape and layout confounded | fixed-stage contracts and final complete 2×2×2 anchors |
| tuning on all eval results | registered grouped 90-case selection; sealed reporting outcomes |
| partial output or duplicate resume | durable initiated-call ledger, atomic terminal records |
| low MRR used as a bug diagnosis | inspect implementation and inputs, never resample wrong roots |
| disk exhausted by attention | bounded prefetch/writers and disk-space admission before requests |

## Deletion and preservation

The user authorized deletion of RQ2-owned results, preparation, renders,
attention and caches after this audit. A scoped ownership inventory and
preservation manifest must precede deletion. No symlink target or shared tree
may be deleted. Preserve RQ2 source, findings, reports and their derived tables
and images; all RQ1.1; V3 corpus; RQ480; model/config files; and RQ3 source.
Deletion completed for the owned `results/` contents: 294,443 files totaling
132,520,699,087 bytes. The deletion manifest is
`docs/RQ2_retirement_assets/retirement_manifest.json`; it records each owned
root, a full file/size inventory and retained historical aggregate copies.
Protection hashes passed for 288 source/config/report dependency files before
the separately recorded old-RQ2 disable-config amendment. Once deleted, the original raw RQ2 conversations/attention cannot be
recomputed directly from this audit. The surviving summaries are historical
evidence, not replacement raw artifacts.

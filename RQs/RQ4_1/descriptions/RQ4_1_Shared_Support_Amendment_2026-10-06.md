# RQ4.1 — shared canonical token support, revision2

Status: user-authorized prospective implementation correction; no new model outcomes. This amendment supersedes exclusive largest-area ownership in the canonical protocol. Prior CPU failure and its exact source/config/protocol snapshot remain under `results/comparison_coding_v1/cpu_stop_source_snapshot/`. The six completed design reviews are historical; this correction is not represented as a seventh review.

## Definition

For canonical source role u, let C_u be the set of actual post-processor visual positions intersecting its registered glyph foreground. Use the already generated unified-renderer foreground/anchor rasters and the same processor transform; no changed diagnostic PNG, role identities, observations, captions or labels. Retain raster-decoding uncertainty and source binding in the audit; bounding-box whitespace never creates support.

The optional support is **R_u=C_u\A**. Supports may overlap. There is no winning role and no per-role token copy. The selected set **S** contains unique original token indices; the decoder gets each selected embedding and its original position once. Anchors belong to S once and remain excluded from optional R_u. A fully anchored role has q_u=1 under the inherited proxy; a genuinely absent unanchored role remains a failure. Shared geometry is not proof that the model read all supported operands.

The q_u formula, CVC min-over-operands objective, type weights, source-occurrence identity, unary coefficients and degree-preserving rewiring contract are unchanged. Selecting token t updates **every u with t in R_u**. No division by the number of supported roles: different original observations retain their existing semantic weights. Repeated annotation of the same source role/token is idempotent; distinct source occurrences remain distinct even when their values or geometry coincide.

Allocation overlap does not duplicate attention mass. The passive observer still partitions physical text/image keys for normalized mass accounting; any future overlapping per-role attribution must be labeled separately rather than summed as a disjoint total.

## Exact action accounting

Single-token and joint-action proposals remain registered. A proposed action is the unique union of its new indices; its cost is the union cardinality. Its gain is evaluated by applying the entire union simultaneously to all affected roles, using per-role maximum coverage before averaging. Adding individual gains would overcount when two proposed tokens improve the same role, and is prohibited. A shared token can improve both ends of a comparison at cost1. All matched controls use the same support map and unique-token budget. Stable token/role ordering and existing gain/zero-plateau tie rules remain deterministic.

For QUOTA, role quotas are support-coverage targets, not duplicated model-token reservations. Compute largest-remainder proportional targets from residual role capacities, capped by each residual size. Choose an unmet role by largest remaining integer deficit, stable role-ID tie; choose its next token by its own q improvement, stable token-index tie. Credit that unique token to every incident role. If sharing satisfies the round's targets before the unique budget is exhausted, redistribute the remaining budget over residual capacities by the same rule. Once all role supports are exhausted, fill from remaining positions by the registered spatial farthest-point rule. This makes the previous disjoint-support quota rule executable under sharing without extra tokens or inferred importance.

## Checks and evidence boundary

1. Archive the failed exclusive-support implementation before editing. Preserve all prior calls, scores and failure artifacts.
2. Independently test overlapping supports, shared-token single charging, joint-action non-additivity, anchors, empty foreground, repeated annotation, zero features, exact budgets, deterministic ties and degree-matched controls. Tiny exhaustive objectives use an independent implementation.
3. Recompute the support map on all220 exposed cases from existing actual foreground rasters. Report confirmed/uncertain support, formerly empty roles repaired, all unique union sizes and budget feasibility. Reuse unchanged PNG/processor data; this is qualification, not an inference replay.
   When a role's optional support is supported only by uncertain multicolor pixels, rerasterize that ONE already registered glyph through the same unified renderer and recover its unambiguous alpha support. Keep the original PNG byte-identical and preserve the initial uncertain record. This changes the audit's certainty, not the diagnostic chart.
4. Report whether each ratio can afford A union all R_u. If it can, both true and rewired objectives can attain1 in exact arithmetic by keeping all support. This is a feature-independent saturation certificate, **not** a measured heuristic mask difference or a new pass/fail threshold. Real encoder features and registered final-mask checks are still required before mechanism qualification.
5. Recheck static guards and affected CPU regressions. The full CPU credential, GPU smoke and formal activation stay false until every original remaining predicate passes. This repair alone does not qualify the complete22-arm runner or real-model attention/speed paths.

The220-case roster,22 arms, preselected CVC50, retained ratios25/50/75%, call limits, model/processor/context settings, canvas≤8192×8192, pure-visual single-call constraint, attention≤1GB/10,000 and stop rules are unchanged. There is no ratio/layout tuning to force the true/rewired masks apart and no new model call introduced by this revision.

## Why capacity saturation matters

If A union all R_u fits K, retaining that union makes every q_u=1 for any encoder features, so both true and rewired objectives attain their upper bound1. With distinct spatial positions and exact arithmetic, an omitted supported token still provides positive unary gain through its self-similarity; the registered greedy therefore exhausts support before its zero-gain spatial fill. Starting that fill from the same union removes an exact-arithmetic dependency effect on the final set. FP32 rounding and the actual implementation still require direct mask checks. Differences produced solely by tiny numerical plateaus would not substantiate useful comparison-dependency allocation. This is a conditional analytical warning, not a measured real-encoder result or an authorization to change the registered retention ratio.

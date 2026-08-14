# Cross-Region Findings

**Status:** v22 case-eligible one-to-three-question successor passed its fresh
dual-model logical smoke; the v22b formal rerun has started and is incomplete. Qwen jobs 19726651 and
19726652 and Gemma jobs 19726653 and 19726654 completed every registered
cross-region and typed-two-stage smoke record with zero infrastructure errors,
parse failures, truncations, or overlength responses. The inspected v21 smoke
remains valid for its three-question packets but does not exercise the new one-
and two-question schemas.
Predecessor compact and Controlled-canvas trajectories are archived diagnostic
material and cannot establish real-dashboard usefulness; this is not an RCA
result.

## Renderer coverage limitation exposed by v22 eligibility

The frozen 469-case preparation exposed an important limitation of the current
dashboard evidence selection. In some cases, the M, R, L, and G regions do not
show rows whose service or entity identifiers connect at the same granularity.
For example, a selected metric row may identify one service while the visible
trace and log rows identify different services, and the visible topology edge
endpoints may connect neither of them. In such a packet there is no honest
same-entity or caller-to-callee chain that can be followed across all requested
regions, even though the underlying raw incident may contain more telemetry.
This is a limitation of what the current canvas selects and makes visible, not
a model perception failure and not evidence that the dataset lacks those
relations.

The complete preparation audit found 316/469 cases eligible for Levels 1--3,
132/469 eligible for Levels 1--2 only, and 21/469 eligible for Level 1 only.
Thus 153 cases have no supported strict three-region chain in the frozen visible
packet, and 21 also have no supported two-region chain. The registered RQ1
handling is deliberately conservative: retain every case, ask only its
supported levels, and exclude unsupported levels from their denominators. RQ1
does not redesign the canvas in response to this observation.

A later renderer-focused RQ should test whether entity-aligned row selection,
an explicit pod-to-service mapping, or another visible cross-granularity bridge
improves cross-modal connectivity. Such a change would be a new renderer
protocol and must not be introduced into the frozen RQ1 comparison. The
authoritative evidence is
`RQs/RQ1/results/rq1_v22_prepared_shared_469_20260813/preparation_audit.json`.

Under the inference-v2 successor run, Gemma showed a narrow hybrid-over-text
gain on level-2/3 complete-chain accuracy (`+0.1111`), while the preregistered
depth interaction and individual M/L/R/G visual main effects did not pass. Qwen
did not reproduce the hybrid gain (`-0.0057`) and its aggregate parse rate was
about `0.700`, leaving its architecture-control efficacy conclusion incomplete.

The full-dashboard transfer repeated the direction for Gemma (`+0.1500` H−T on
level 2/3) but remained small and non-confirmatory. Across diagnostics, Qwen
could read several topology operations extremely well, whereas Gemma was much
less reliable. These experiments show architecture-dependent visual use and
cross-region brittleness; they do not establish improved root-cause ranking.

Renderer-v12 numeric identities and the explicit English identity explanation
are retained. Formal visual factorial cells now use actual renderer-v12 source
crops, while P is globally reserved for the exact T text rendered as pixels.
The 4/6/4 registry means Level-1/2/3 template counts; no Level 4–6 source exists
in the synced tree.

These local outcomes are not substituted for the registered final Nibi rerun.
This file will be updated with the 289-case primary headline and separate
RE2-OB/RE2-TT slices after that run is complete and verified.

The final local three-case diagnostic's one AIOPS-2025 H cell parsed with valid
query membership but scored `0/3` complete chains and `0.50` step accuracy.
This is a path check and visible warning about task difficulty, not a gate or
scientific result.

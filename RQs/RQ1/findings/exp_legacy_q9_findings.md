# Legacy Q9 Findings

**Status:** corrected v21 T/P/V/H smoke qualified. In the v22b formal rerun,
Qwen completed and persisted all 24 shards (1,876/1,876 records, zero
infrastructure errors). Gemma shards 0--2 persisted 158 valid records but also
30 deterministic infrastructure errors: the T/H prompt token count plus the
registered 8,192-token output allowance exceeded the frozen 32,768-token
context. Unstarted Gemma shards 3--5 were canceled rather than knowingly
repeating that failure. The user authorized a successor 40,960-token context
while preserving the 8,192-token RQ1 output allowance, explicitly retained
all compatible completed predecessor calls, and waived replacement smoke.
The smallest necessary formal recovery is pending. These infrastructure errors
are not model-quality outcomes. The v19 Qwen smoke is an
invalid diagnostic because its grammar permitted three steps for a Level-1
answer while the validator required one. Predecessor compact Nibi
trajectories are invalid, and Controlled-canvas trajectories are retained only
as synthetic spatial-formatting diagnostics; neither supports a real-dashboard
efficacy claim.

The nine direct questions established the distinction between dashboard
readability and RCA ranking. Numeric IDs, direct values, edge directions, logs,
and trace summaries can be tested independently, but high direct-question
accuracy does not imply that a model integrates those facts into a correct root
cause. Earlier local model calls retain their original artifact-specific
status. Nibi calls made with the semantic-compression implementation are not
promoted and cannot be merged into the replacement run.

The corrected design uses pure text T, exact-T pixel transport P, the real
renderer-v12 dashboard V, and strict image-first H=V+T. Future executions use
new result IDs. This file will report the 289-case primary headline and
separate RE2-OB/RE2-TT slices after the final rerun is complete and verified.

The archived pre-v17 local diagnostic parsed and scored `6/9` on its single
AIOPS-2022 cell. This only confirms the restored scorer/task path executes; it
is not an estimate of model performance.

# 2026-09-12 — DD-SEARCH-12: public entity typing and deployment support

Status: identity successor implemented and CPU-checked on two train cases;
deployment-evidence addition remains pending. No new model calls.

## Evidence and decision

The fixed twelve-case train audit finds eighteen `k8s-master1/2/3` entities
(three in each of six AIOPS-2025 cases) classified as services by the inherited
name regex. Five of those identities occur in the selected diagnostic facts.
Their candidate IDs are present; this is a type/legend mismatch, not a missing
root-candidate finding. Audit:
`results/search_first_v1/private/public_identity_audit_20260912.json`.

All twelve public cases also contain node→pod hosting relationships: 42 per
AIOPS-2022 case and 21–24 per AIOPS-2025 case. These relations are absent from
the current selected dashboard. Source call-graph edges do not overlap them,
so do not claim those particular hosting edges were mislabeled as calls.
Reasoning repeatedly guesses co-location instead of observing it. Explicit
deployment evidence is a separate future input intervention, not a proven fix
for low MRR or a permission to invent pod→service links.

Implement a reusable public-only identity mapper with explicit source
node/pod metadata taking precedence over the existing naming fallback. Extend
the fallback for the observed Kubernetes control-plane names. Keep the
case-local service/node/pod 3/4/5-digit convention, deterministic seed, collision
checks and complete public candidate universe. Apply the mapper before any
text/log numeric parsing, not by blindly replacing numeric substrings in old
packets: diagnostic counts and values can equal entity IDs.

RQ3 opts into this through a versioned pool-compiler policy. Older RQs and
stored pools/mappings/outputs remain untouched; no successor is concatenated
into an old run. New mapping may change other IDs within a type group because
the deterministic group allocation changes; paired analysis must use source
case identity and evaluator mapping, never assume old numeric IDs are stable.
The unchanged scorer still evaluates natural entity identity privately.

The candidate list remains in prompt text, never an image panel. Explicit
deployment edges, if added in a later checked successor, are diagnostic facts
and therefore belong in the image, with a separate meaning from call arrows.
No new attention, training, validation or eval is authorized by this decision.

## Verification and next steps

First qualify the identity mapper on ordinary names, control-plane nodes,
metadata-only nonstandard names, conflicting roles, deterministic ordering,
capacity/collisions, and legacy-compatible cases. Ensure compiler cache keys
include the chosen policy and implementation. Full-pool recompilation is only
for a small registered training subset, not the complete corpus. Preserve old
preparations. Before inference, verify every candidate/type binding and image
primitive under the new mapping, and separately audit any deployment evidence.

## Implementation and completed checks

`src/vlmrca/entity_identity.py` is the reusable public-only mapper. RQ3's pool
compiler opts in using `harness.entity_identity_policy: public_entity_identity_v2`
in `configs/search_public_identity_v1.yaml`. Other RQs and shared inference
recipes are unchanged. The compiler/cache key and search dependency chain
record the policy and helper implementation. Gallery construction and batch
registration reject a pool or gallery with the wrong identity policy, avoiding
another nominal-config change whose actual input remains old.

Full regression: **215 passed in 70.33 seconds**, no skips/failures, after the
stale-pool guards. Functional source count 5,995. The earlier pre-guard run
also passed 215 tests in 73.91 seconds; both XML files are retained. The real
old-pool/new-policy negative test was rejected before rendering/model calls.

Two train full pools were recompiled to a new directory, not overwritten:
`results/search_first_v1/public_identity_pools_v1`. Re-entering the same
preparation completed via resume without recompiling either case. The A22
pool retains all 18,694 facts byte-identically; its selected PNG is also
byte-identical. A25 retains 14,730 facts and the same 63 natural candidate
identities; only the three control-plane nodes change role. Metric/trace
statistics and per-entity/bin log event counts match the old pool. Its IDs
are reassigned consistently before log parsing; old records keep old IDs.

Both actual PNGs were opened and candidate text/primitive bindings checked:
`results/search_first_v1/public_identity_previews_v1/cpu_review.json`.
This verifies the type correction, not a performance gain or qualification of
unimplemented hosting evidence. Existing trace-axis readability and missing
deployment relationships remain follow-up topics. No Solver, Composer,
training, validation or eval was run for this successor. Search consumption
remains 224 calls. No owned GPU process remains active.

# RQ3.20 v3 — user-authorized 50% overview cap and execution

Date: 2026-10-05. The user explicitly raises the first-request input cap from
0.40F to 0.50F and authorizes GPU smoke, then formal launch after qualification.
The 0.85F combined two-input plus 512-output reservation, minimum 50% eligibility
in each dataset, original complete baseline, candidates, facts and outcomes are
unchanged. v1/v2 sources and failed qualifications remain historical artifacts.
This is a prospective, user-authorized budget amendment, not passage under 40%.

Reuse v2's compatible unified-renderer PNGs, with source/design/PNG identity checks.
The first-request cap includes the entire system/user prompt and real image tokens.
All four overview/fetch conditions share the same case-level fallback to FULL_TEXT.
The final detail budget reserves the larger text/visual selector input plus 512.

Core execution registers all five methods on 220 cases, T/V independent repeats
on the fixed 60, and the seven-call mechanism design on those same 60. Upper bound
is 2,200 formal calls; 112 infrastructure recovery calls are reserved. Smoke has
18 calls and one inclusive 600-second window. SIRCL and confirmation remain
conditional and disabled, with their 670 calls reserved, within the 3,000 total.
Ordinary exactly identical requests may reference a current-phase committed result;
independent repetitions always invoke the model afresh. Logical workflow cost
includes all stages and referenced requests, separately from actual generation cost.

Mechanism cards contain one focus and one matched control relation. Focus is
incident to an entity from V's originally accepted detail packages. Control is
disjoint from those entities, matched on relation type, endpoint entity types and
the log2(1+degree) floor-bin pair in the full public typed relation graph. Deterministic hashes
resolve ties. Both cards repeat one already available relation; neither identifies
a fault. When exact matching fails, record mechanism inapplicability without
replacing the case. Both edges are queried in every QA condition with identical
questions: return each relation's exact endpoints and type. Cards affect selector
input only, never the final text compiler; QA responses never reach diagnosis.
Aid token overhead is reserved before packing both intervention conditions under
the original pipeline budget; inability to fit is mechanism inapplicability.

Dispatch is a deterministic hash-ordered dependency queue: selector precedes its
diagnosis; original V precedes its mechanism card construction. Independent
repeats have separate call identities and do not consult baseline answers. Invalid
selection yields the unchanged text overview; unknown IDs are not repaired.
Invalid model answers commit with zero diagnostic score; infrastructure failures
stay unknown and stop new submissions for diagnosis. Atomic completions are
trusted on resume; only incomplete work is materialized.

Smoke uses the original three eval identities: each runs text fetch (2), visual
fetch (2), one direct arm (FULL_TEXT / SUMMARY_TEXT / SUMMARY_VISUAL), and one QA
condition (none / focus / control): six calls per dataset. QA matching failures
are recorded as unavailable, not replaced by outcome-selected cases. Smoke is an
infrastructure/artifact test, never an MRR gate. Output ceilings are selector 512,
QA 1024, diagnosis 8192; all retain the inherited decoding/model recipe.

Attention is auxiliary. The legacy collector must not be enabled if its raw
sidecars exceed the registered 64 KiB/call bound; collection remains off unless
a bounded, same-call implementation and overhead qualification are available.
Record that incompatibility explicitly; never report disabled collection as
successful attention measurement or delay the primary-method decision for it.

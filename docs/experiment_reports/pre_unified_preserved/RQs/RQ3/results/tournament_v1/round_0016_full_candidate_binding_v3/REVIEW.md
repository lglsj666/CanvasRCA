# Round 16 — candidate-bound evidence cards

This round is registered as
`CANDIDATE_BINDING_CARDS_RESOURCE24_full_remaining_v3` for all cases left
after round 15: 128 Qwen and 106 Gemma cases, with 161 distinct cases in their
union. No inference subset is used.

The evidence selection, candidates, pure one-image transport, RCA task, prompt,
model recipes and scorer are unchanged from the resource-family predecessor.
Only the rendering groups already-selected M/R/L facts by public anonymous
candidate. Up to eight cards carry explicit `SERVICE 123`, `NODE 1234` or
`POD 12345` headings; all residual facts remain in `OTHER M/R/L/G` cards.

Before model calls, 363 RQ3/renderer tests passed. The full 161-case gallery
rendered without failure, and its CPU audit verified source integrity, prompt
identity, exact selected facts, visible primitive bindings, geometry, clipping,
anonymization and private-label isolation. All 161 PNGs differ from the
same-fact resource-family predecessor while M/R/L/G fact IDs remain unchanged.
Five source-resolution PNGs, one per dataset, were opened manually:
`INC-B4C69A1E0459`, `INC-46EA9B460B2C`, `INC-6DCAE95A54B2`,
`INC-D25E7590F78E` and `INC-452942E7A056`. Headings and plots are readable;
no overlap, clipping or leakage was observed.

Exact same-model request matching against rounds 1–15 found no reusable
outcomes. Qwen and Gemma work specifications contain exactly 128 and 106
registered tasks. The 123-file source snapshot SHA256 is
`94a28c4e943583dd1c1c9a917f0921105108ab39edc65ad218b24e51867249cc`.

**Execution status:** ready; model inference has not started at this review
boundary.

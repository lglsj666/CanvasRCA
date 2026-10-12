# Pre-inference layout issue — 2026-09-12

INC-0917F17160F5 has selected M/G facts but no R/L cards. The explicit
four-card SEARCH-19 tree references EC03/EC04, which do not exist here.
Renderer correctly rejects it with `unknown or repeated layout card`.
This is a sparse-input layout configuration defect, not model failure and
not a missing candidate. The original full/route layouts are generated from
their actual card set and passed for all24 cases; their GPU batch continues.

After all24 previews finished, INC-CB91FA13504C is a second sparse-card
case with the same error. Total22 rendered /2 blocked, zero overview calls.

No overview call has been made. Retain the failed preview and every case.
After the running native batch finishes, add an explicitly versioned
region-aware metric-left / remaining-regions-stacked layout. It must retain
the exact previous tree and pixels for all four-card cases and all selected
facts for sparse cases, without adding empty-data prose or candidate panels.
Test all nonempty region subsets and regenerate a successor overview gallery;
do not edit the inference-frozen code during the running native batch.

Resolved after native completion: 269 CPU tests passed, including all15
nonempty region subsets. Successor `wider_overview_gallery_v2` renders24/24;
all22 formerly successful PNGs/packets/manifests/prompts are identical. Both
sparse actual PNGs were opened, all facts remain. Large sparse blank panels
are a registered layout trade-off, not an efficiency claim. No old record was
deleted or relabeled; this failure gallery remains zero-call evidence.

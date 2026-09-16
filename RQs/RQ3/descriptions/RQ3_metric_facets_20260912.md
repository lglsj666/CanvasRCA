# DD-RQ3-SEARCH-28 — Same-source metric facets

Date: 2026-09-12. Status: completed train-only exploration; not promoted.

## Decision
SEARCH27 adds period labels but does not improve either dataset mean. Its full
answers include cross-row numeric attribution errors. Test shorter, taller
metric plots in two column-major columns, with thin panel boundaries, against
SEARCH23's native single-column owner-header layout. This is a joint facet
arrangement/aspect/border intervention, not proof that any one factor causes
an effect. Curve count, source bins/values, per-series scales, base/peak/z,
owner/metric labels, outer card geometry, R/L/G, candidates and prompt stay
fixed. Do not carry over SEARCH27's added period annotations.

`metric_panel_columns=2` is a discrete probe within the existing scene program;
the outer continuous split-tree grammar is unchanged. Keep source precision,
missing-bin locations and native connecting behavior. Missingness is neither
invented nor separately added to model guidance. Candidate enumeration remains
prompt-only. This experiment adds no diagnostic evidence text or attention.

## Literature and transfer boundary
Question: can fixed-count facet arrangement reduce adjacent-row binding errors?
Include primary visualization research and explicit rendering grammar; exclude
claims that human accuracy or aesthetics directly establish frozen VLM RCA.
Searches: small multiples aspect ratio line charts perception; exact title
"Examining Limits of Small Multiples". Verified 2026-09-12.

Hosseinpour, Matzen, Divis, Castro and Padilla, *Examining Limits of Small
Multiples: Frame Quantity Impacts Judgments with Line Graphs*, IEEE VIS 2024 /
TVCG, DOI10.1109/TVCG.2024.3372620.
[Official paper page](https://content-staging.ieeevis.org/year/2024/paper_v-tvcg-20243372620.html),
[author links](https://www.heliahosseinpour.com/publications).
The official abstract reports frame-count-related accuracy deterioration in
human line-chart tasks, not a two-column RCA result. Full paper/data on OSF
could not be fetched in this review: metadata/abstract screened only, not a
complete replication or full-paper assessment. It motivates retaining count
as a control, not promising a benefit from more facets.

[Vega-Lite official facet documentation](https://vega.github.io/vega-lite/docs/facet.html)
was read completely. It distinguishes data partition from row/column placement,
spacing, headers and scale resolution. Borrow the grammar separation only;
the deterministic painter remains project-owned. Heterogeneous metrics keep
their independent raw axes, not a new shared scale. No third-party runtime or
unverified algorithm implementation is introduced.

## Checks and batch
Require strict column/encoding/capacity checks, odd/even/sparse geometries,
stable column-major owner ordering, source-bin equivalence, unmodified public
packets and exact static prompts. Re-render all24 original PNGs byte-exactly.
For new PNGs verify outer geometry, R/L/G pixels, complete labels and numeric
binding; inspect actual dense A22/A25 and sparse images. Record measured plot
aspect ratios and font sizes. A source hash alone is not a pixel review.

After passing those checks, run at most24 Solver calls on the exact SEARCH23
train cohort:12 per AIOPS dataset,offset6. Config: search_metric_facets_v1.yaml;
concurrency4,3600s,qualified card_nonthinking_v1 recipe,8192 output maximum.
No Composer,validation,eval,SFT or RL. Correctness does not authorize retries.
Read all full conversations/raw/partial responses and check artifact accounting.
Two exploratory per-dataset paired Pratt-Wilcoxon contrasts versus
owner_header_development_v1, Holm together; paired dz,MRR,AC@K,tokens,
repair/break/tie and per-fault/granularity breakdowns. Preserve negative results.
No small repeated-train-cohort score establishes the final target.

## CPU repair trail
Initial 363 tests passed after an early all-row-height rejection was added.
The full24 gallery then failed its measured-capacity allocator before any model
call. Cause: the new painter narrowed label columns at trial widths, requiring
a full-width capacity sample even though the requested half-canvas was feasible.
Retain the parent label-column width while moving plots into facets, rather
than shrinking labels. Add actual-font-scale audited-painter coverage. Preserve
galleryv1 failures; regenerate a distinct galleryv2 and recheck before calls.

Final364 unique CPU tests pass, including all346 preceding tests. All24 source,
pixel-locality, full native PNG byte replays and fixed prompt checks pass.
All599 metric rows retain their source bins and values. Dense A22/A25 and sparse
PNGs opened and reviewed. Source count5983; min owner/name font21px. Native
lane width/height12.23–19.63 becomes3.12–4.72; plot area is not identical to lane
area. Review is bound to metric_facets_gallery_v2 summary hash
`b734b655b421920ceb0b1fedaf64a6b900832482e82587e24c9a50833e331af8`.
Proceed with the registered24 train-only Solver calls; no target is achieved.

## Completed outcome
The authorized batch completed 24/24 calls in349.919 seconds, without timeout,
transport, schema or truncation failures. All responses contain five allowed
IDs; maximum341 output tokens. Full conversations and raw/partial answers were
read. Source, request, token, image and persistence checks pass.

| Dataset (12 train cases each) | Reference MRR | Facets MRR | Input tokens | Output tokens, reference → facets |
|---|---:|---:|---:|---:|
| AIOPS-2022 | .506944 | .458333 | 17754 unchanged | 253.42 → 282.58 |
| AIOPS-2025 | .440278 | .361111 | 17648.83 unchanged | 254.33 → 253.50 |

Both exploratory paired Pratt tests have raw p=.5, Holm p=1; paired dz=-.2564
and-.3616. One repair, four breaks and19 ties across24 cases. No evidence of a
shared improvement; keep the reference, not this layout, as the next anchor.
One previously observed cross-row value attribution is corrected, but ordinary
resource changes are still interpreted as exhaustion and hosting/causal claims
remain unsupported in some answers. These examples do not establish that every
wrong ranking is a perception failure. Audit public-pool/selected coverage next,
before adding further cosmetic variants. No validation/eval or training ran.
Artifacts: `../results/search_first_v1/metric_facets_development_v1/`.

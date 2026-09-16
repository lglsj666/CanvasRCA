# RQ3 qualification handoff — 2026-09-09

**Not fully qualified. No SFT, RL or formal evaluation has started.** All local
model services stopped after the bounded supervisors. RQ2.1 inference and final
analysis are complete; RQ1.1/RQ2.1 outputs and shared inference recipes remain
unchanged. This document supersedes any ambiguous claim that all smokes passed.

## Actual logical smoke attempts

| Experiment | Calls complete/initiated | Seconds | Actual result |
|---|---:|---:|---|
| Composer learning | 0/0 | 571 | Failed readiness authentication; original timeout-only marker corrected by manual review |
| Frozen Solver generalization | 3/3 | 246 | Two Composer outputs and one Solver Text output saved; then legacy scorer import failed |
| Selection/design attribution | 9/9 | 290 | Inference supervisor passed, both roles, seven Solver outcomes and same-call attention saved |

Twelve local calls were initiated in total, including all failed-attempt work.
No logical smoke was reset, split or silently granted a second 600-second
window. Post-smoke manual review found stale visual-guide wording, now fixed
but not live-requalified. A one-time bounded repair supplement requires explicit
authorization before further model calls. Training remains separately disabled.

## Repairs and demonstrated coverage

1. Readiness now uses authenticated local requests and rejects HTTP errors
   immediately. The following two smokes demonstrated both servers starting.
2. RQ3 supplies the existing standalone granularity matcher to the unchanged
   unified scorer; the attribution smoke scored all seven Solver outputs.
3. Analysis-only text spans distinguish M/R/L/G, candidates, task and guide.
   Tests prove unchanged model-visible chat bytes. Both original attention
   phases can be re-aggregated offline; no second forward pass is required.
4. The visual guide no longer describes missing-bin gray ticks or dashed gaps
   that the current connected-line renderer does not draw. Shared SIRCL RCA
   procedure and the 27B inference projection remain unchanged.
5. Screenshot attention is explicitly whole-image `pixel_text`; no fabricated
   M/R/L/G screenshot-region attribution is reported. Its raw exact-geometry
   patch map remains available. Real dashboards have actual card-region boxes.

The six original reviews and their blind spots are documented in
[the review record](RQ3_review_20260909.md). Latest CPU regression covers the
found defects: 33 tests passed, Ruff F/E9 passed, and all 14 protected parent
files retain their registered hashes. Static tests are not proof of zero bugs
or training readiness. The five functional modules total 2,251 lines, within
the 6,000-line limit; renderer remains the registered RQ-local exception.

## Inputs, outputs and attention inspection

The two AIOPS validation Composer chats use 16,246 and 16,261 input tokens,
under the 16,384 directory budget; 4,096 output tokens remain reserved.
There is no truncated million-token prompt. The complete public pool remains
on CPU; only 95/13,404 and 111/4,750 cards are advertised, with explicit
coverage/omission counts. These are not exhaustive model-visible pools.
The entire saved Composer inputs match their audited catalogue objects.

All four actual Composer responses ended normally, with 217/211 output tokens
per case. Sampled-token ID and finite logprob counts equal output usage,
including the final stop token. The AIOPS-2025 untrained BASE selected twelve
cards and rendered successfully. The AIOPS-2022 program's selected logs did
not fit and remain `invalid_program`, without a hidden replacement.

The seven attribution Solver responses have 141–218 output tokens, finish=stop,
valid schema and known candidate IDs. Full text and visual guides, selected
facts, card manifests, returned JSON and PNGs were inspected. Original request,
conversation, raw response and attention artifact hashes verify. U00/U01 share
fixed facts; U10/U11/Text/Screenshot share learned facts. Design swaps alter
pixels without secretly deleting cards. Harness controls are CPU fixtures,
not successful Composer outputs or formal optimized D_FIXED baselines.

The Solver's smoke rankings all miss the private root. Their public reasons
include invented edges, namespace/owner confusion and unsupported confident
claims. This is retained model behaviour on sparse/untrained qualification
inputs, not an efficacy result or reason to rerun until correct. Neither
smoke nor two cases establish that RL will improve performance.

Both prefill and structured-answer attention are present. Real canvases record
M/R/L/G, header and blank areas, attention per pixel and density lift, with
exact processor patch geometry. Text evidence has all four region labels.
Screenshot attention is a whole-image control, not a semantic-region analysis.
Attention is diagnostic and correlational, never a reward or correctness proof.

## Inspectable examples

- [Composer conversation](../results/exp_selection_design_attribution_smoke_v1/conversations/INC-0C24330AB85D_composer_0.md)
- [Learned canvas / Solver conversation](../results/exp_selection_design_attribution_smoke_v1/conversations/INC-0C24330AB85D_solver_U11.md)
- [Same-content Text conversation](../results/exp_selection_design_attribution_smoke_v1/conversations/INC-0C24330AB85D_solver_text.md)
- [Learned canvas PNG](../results/exp_selection_design_attribution_smoke_v1/renders/INC-0C24330AB85D_solver_U11_2.png)
- [Fixed content / learned design PNG](../results/exp_selection_design_attribution_smoke_v1/renders/INC-0C24330AB85D_solver_U01_2.png)
- [Screenshot control PNG](../results/exp_selection_design_attribution_smoke_v1/renders/INC-0C24330AB85D_solver_screenshot_2.png)

Current pools: `qualification_prepared_v6`; refreshed directory:
`qualification_catalog_v11`. Full processed corpus and RQ480 were not regenerated.
Sparse fixture canvases deliberately leave substantial blank area; no claim
that these fixtures are aesthetically or diagnostically optimal is made.

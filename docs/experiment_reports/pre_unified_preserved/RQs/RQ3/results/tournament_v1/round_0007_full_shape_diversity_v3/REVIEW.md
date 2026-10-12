# Round 7 — full remaining cohorts, metric shape diversity

This round applies `SHAPE_DIVERSITY075_TOP24_full_remaining_v3` to every case
left unresolved after round 6: 232 Qwen cases and 205 Gemma cases. Their union
contains 275 distinct cases. The intervention changes metric selection to the
registered shape-diversity selector with relevance weight 0.75 and a 24-series
capacity. The fixed prompt, candidates, trace, log, topology, scorer, model
recipes and no-attention tournament contract remain unchanged.

The complete 275-case gallery passed source binding, prompt/candidate,
geometry, clipping, determinism and leakage checks. Every case changed both
its selected metric panels and rendered pixels relative to the parent; trace
and log inputs did not change. Five actual PNGs were opened, one per dataset:
`INC-E92A6FFD9DC0`, `INC-CCCFF766DA4B`, `INC-E6D8B968F39E`,
`INC-42D9586BA9E2` and `INC-4A56695C1F2E`. The dense 24-lane metric panels,
R/L/G regions, relative axes and entity IDs were readable without overlap or
clipping. No label, dataset name, raw identifier, absolute time, filesystem
path or injection-time disclosure was found.

Exact full model-visible-request matching against rounds 1–6 found nine
reusable Qwen targets and eight reusable Gemma targets. These are same-model,
same-case byte-identical requests whose original outcomes are retained rather
than sampled again. The remaining 223 Qwen and 197 Gemma targets require new
calls. Reuse is an input identity result, not a method-name match.

Inference has not yet been counted as complete in this review. Completion,
new AC@1 retirements and cumulative per-dataset coverage will be appended only
after both model cohorts commit and the post-run artifact audit passes.

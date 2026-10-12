# Round 8 — full remaining cohorts, cross-source entity fusion

This round applies `ENTITY_CROSS_SOURCE_FUSION24_full_remaining_v3` to every
case left unresolved after round 7: 225 Qwen cases and 195 Gemma cases. Their
union contains 268 distinct cases. No inference subset is used.

The method uses only public telemetry. It selects up to 24 metric series with
a registered cross-source membership rule, then colocates M/R/L evidence for
up to three publicly identified entities with the strongest cross-modal
coverage. Remaining evidence stays in ordinary modality cards, and the full G
topology card receives a reserved lower canvas region. The candidate list,
fixed tournament prompt, scorer, model recipes and attention-off protocol are
unchanged.

The first CPU render attempt exposed two implementation constraints before any
model call: the inherited parent tree could not be explicitly replaced, and
dense owner grouping could make topology cards infeasible. The renderer was
repaired deterministically, its regression suite passed 125 tests, and the
entire union gallery was regenerated. The discarded preflight gallery
contained no inference outcomes.

All 268 final PNGs passed source binding, prompt/candidate identity, geometry,
clipping, determinism and leakage checks. Five actual images were opened, one
per dataset: `INC-DD1A8BB11CC7`, `INC-46EA9B460B2C`,
`INC-B8CEA35848D0`, `INC-495E8857529A` and `INC-452942E7A056`.
They retain readable metrics, trace, log and topology content without overlap
or clipping. No private label, raw case identity, dataset name, absolute time,
filesystem path or injection-time marker is model-visible.

Exact same-model request matching against rounds 1–7 found no reusable
outcomes. Therefore the registered 225 Qwen and 195 Gemma targets require 420
new model calls. The pre-call source snapshot contains 119 runtime source and
configuration files and has archive SHA256
`d21be0377801264fde1d5c38e4dc610d9544fa1da09bf18db9da73ae77c51ddc`.

Both model phases committed successfully. Of 420 initiated requests, 419 ended
with `stop`; one Gemma response reached the output-length limit and remains a
model failure rather than an infrastructure retry. Qwen newly retired 21 cases
(8 AegisLab, 5 AIOPS-2022, 4 AIOPS-2025, 2 RE2-OB, 2 RE2-TT), leaving 204.
Gemma newly retired 17 cases (4, 4, 3, 3, 3 respectively), leaving 178. The
post-run analysis passed shared-input and artifact checks.

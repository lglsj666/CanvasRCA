# Round 14 — full remaining cohorts, local metric contrast

This round applies `LOCAL_CONTRAST_TRACE_RESOURCE_TOP24_full_remaining_v3` to
every case left unresolved after round 13: 132 Qwen cases and 108 Gemma cases.
Their union contains 164 distinct cases; no inference subset is used.

The label-blind selector uses 24 metric slots and prioritizes public
trace-associated entities, distinct resource-relevant metric families, and
strong public baseline/current shifts. R, L, G, the frozen one-stage RCA task,
candidate list, SIRCL-style procedure, output contract, scorer, model recipes,
and attention-off protocol remain fixed. All M/R/L/G evidence is presented in
one true dashboard image.

The full static suite passed (130 tests). The complete gallery CPU audit passed
for all 164 unique inputs: every case rendered, all 164 changed actual metric
panels and pixels relative to the resource-family predecessor, while trace and
log selection stayed fixed. Prompt, source, fact, manifest, geometry, clipping,
anonymization, and private-label isolation checks passed.

Five deterministic manual reviews, one per dataset, opened the source PNG and
checked legibility, ownership, relative-time semantics, directed edges,
clipping, overlap, and leakage: `INC-B4C69A1E0459`, `INC-8682AD2CADE1`,
`INC-9DDF62CAF256`, `INC-42D9586BA9E2`, and `INC-7423A8694631`. No blocking
problem was observed.

Exact same-model request matching against rounds 1--13 found no reusable
outcomes. The two frozen work specifications contain exactly their registered
cohorts. The immutable source archive contains 122 runtime source/configuration
files and has SHA256
`382202be1dcfcf45052400f32e50c47e78439785147da535bac324531580836b`.

Model execution completed for all 240 registered targets: 132/132 Qwen and
108/108 Gemma. Every outcome is complete with `finish_reason=stop`; no request
was reused and the artifact audit passed. New calls consumed 2,791,294 input
and 40,636 output tokens. The shutdown-tail `EngineDeadError` occurred only
after all requests completed and did not affect an outcome.

The method newly retired **0 Qwen cases** and **1 Gemma case**, the latter in
AIOPS-2025. Qwen therefore remains at 132 unresolved cases. Gemma has 107.
Current cumulative AC@1 coverage is:

| model | AegisLab | AIOPS-2022 | AIOPS-2025 | RE2-OB | RE2-TT |
|---|---:|---:|---:|---:|---:|
| Qwen3.8 | 82/100 | 56/100 | 56/100 | 80/90 | 74/90 |
| Gemma | 88/100 | 59/100 | 56/100 | 86/90 | 84/90 |

Qwen rank changes were 23 improved, 21 worse, and 88 tied; its remaining-set
MRR was 0.1348 versus 0.1366 in round 13. Gemma changes were 9 improved, 25
worse, and 74 tied; its remaining-set MRR fell from 0.0931 to 0.0616. Thus the
local-contrast metric selector is not a useful general successor even though
it yielded one complementary top-one outcome.

The cumulative evaluator-private evidence audit passes. Among the remaining
cases, root-associated direct public evidence has now been selected at least
once for 129/132 Qwen and 104/107 Gemma cases. The next method should therefore
target candidate-to-evidence binding and comparative interpretation rather
than merely add another similar metric selector.

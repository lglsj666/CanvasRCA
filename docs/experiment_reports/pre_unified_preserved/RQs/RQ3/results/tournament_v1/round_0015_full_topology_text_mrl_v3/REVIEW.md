# Round 15 — topology text with M/R/L in one dashboard

This round applies `TOPOLOGY_TEXT_MRL_VISUAL_RESOURCE24_full_remaining_v3` to
every case left unresolved after round 14: 132 Qwen cases and 107 Gemma cases.
Their union contains 164 distinct cases; no inference subset is used.

The label-blind evidence selection is the registered resource-family selection.
Only selected G evidence changes transport: exact caller-to-callee edges and
public relative-onset rows are supplied as text, while M, R and L remain in one
real dashboard image. The task, candidate list, SIRCL-style RCA procedure,
output contract, scorer, model recipes, sampling and attention-off protocol
remain fixed.

The full static suite passed (131 tests). The complete gallery CPU audit passed
for all 164 unique inputs. Every image rendered, all 164 images changed relative
to the four-region image predecessor because G was removed from the raster, and
the selected M/R/L facts stayed fixed. Prompt, source, fact, geometry, clipping,
anonymization and private-label isolation checks passed.

Five deterministic manual reviews, one per dataset, opened the source PNG and
checked legibility, ownership, relative-time semantics, clipping, overlap and
leakage: `INC-97B043342751`, `INC-11AFCDDD7B6E`, `INC-AC9FBC0EC13D`,
`INC-DAC9DF6ACB55` and `INC-9095FF6F0DE1`. Their adjacent prompt artifacts
also contain explicit typed G edges and onset rows. No blocking problem was
observed.

Exact same-model request matching against rounds 1–14 found no reusable
outcomes. The two frozen work specifications contain exactly their registered
cohorts. Their hashes are
`68c4e5001a83125b61a4e97b9c14979d4dabf94bd6203d87ed84d8de2b9fd70b`
for Qwen and
`650aa396c3646eaf7f72f77fc46e04c23900f3b85700c0e08c89fde99fd5ff8b`
for Gemma. The immutable source archive contains 123 runtime
source/configuration files and has SHA256
`35c2bb19c4918a798283f1f7abe402d6804b6acca06ea484db32fb6b9b2bb15f`.

Model execution completed for all 239 registered targets: 132/132 Qwen and
107/107 Gemma. Every outcome is complete with `finish_reason=stop`; no request
was reused and the artifact audit passed. New calls consumed 2,837,463 input
and 41,504 output tokens. The shutdown-tail `EngineDeadError` occurred only
after all requests completed and did not affect an outcome.

The method newly retired **4 Qwen cases** and **1 Gemma case**. Qwen therefore
has 128 unresolved cases; Gemma has 106. Current cumulative AC@1 coverage is:

| model | AegisLab | AIOPS-2022 | AIOPS-2025 | RE2-OB | RE2-TT |
|---|---:|---:|---:|---:|---:|
| Qwen3.8 | 82/100 | 58/100 | 57/100 | 81/90 | 74/90 |
| Gemma | 88/100 | 60/100 | 56/100 | 86/90 | 84/90 |

Qwen's four new top-one cases comprise two AIOPS-2022, one AIOPS-2025 and
one RE2-OB case. Its remaining-cohort MRR rose from 0.1348 to 0.1694, with
32 improved, 22 worse and 78 tied ranks. Gemma added one AIOPS-2022 case;
its remaining-cohort MRR rose from 0.0528 to 0.0762, with 17 improved, 12
worse and 78 tied. Transporting G as exact text therefore improves some
topology-direction binding, especially for Qwen, but is far from sufficient
for the AIOPS thresholds.

The cumulative evaluator-private audit passes. Every remaining candidate list
can express a scoreable answer. Root-associated direct public evidence has
already been selected at least once for 125/128 remaining Qwen and 103/106
remaining Gemma cases; the three exceptions for each model are AIOPS-2022.
The next intervention should make candidate-to-evidence comparison more
explicit rather than repeat another near-identical metric ranking rule.

# Round 13 — full remaining cohorts, log text with M/R/G dashboard

This round applies `LOG_TEXT_MRG_VISUAL_RESOURCE24_full_remaining_v3` to every
case left unresolved after round 12: 134 Qwen cases and 108 Gemma cases. Their
union contains 166 distinct cases; no inference subset is used.

The selected log evidence is supplied as canonical readable text containing
the template ID, typed owner, relative time bin, multiplicity, severity,
normalized template, observed numeric-variable summary, and LOG-R
baseline/current statistics. Metrics, traces, and topology remain in one real
dashboard image. The selector, RCA task, SIRCL-style procedure, candidate list,
output contract, scorer, model recipes, and attention-off protocol remain
fixed.

The complete CPU audit passed for all 166 unique inputs. L text and M/R/G image
fact IDs are disjoint and their union covers the complete selected evidence;
the selected facts themselves are unchanged from round 12. Five actual images
and their prompts were opened, one per dataset: `INC-1D3579F09C93`,
`INC-2CABCD159021`, `INC-98BF3F9714D0`, `INC-E38C6642AA01`, and
`INC-02DC63A76944`. They are readable and contain no private label, natural
entity name, raw case identity, dataset name, absolute time, filesystem path,
or injection-time marker.

Exact same-model request matching against rounds 1–12 found no reusable
outcomes. The immutable source archive contains 122 runtime source and
configuration files and has SHA256
`96aa907ca0e6ac779bfb26a8e7b732979f6a18c33560d3399e546531fe153152`.
The full RQ3 static suite passed: 130 tests.

Model execution completed for every registered target: 134/134 Qwen and
108/108 Gemma outcomes, for 242/242 total. All statuses are `complete`, all
finish reasons are `stop`, no outcome was reused, and the persisted artifact
audit passed. The EngineDeadError lines in the server tails occurred only after
all requests completed, during the registered forced server shutdown, and did
not affect any outcome.

This round newly retired 2 Qwen cases (AegisLab 1, AIOPS-2022 0,
AIOPS-2025 1, RE2-OB 0, RE2-TT 0) and 0 Gemma cases. After cumulative union
with rounds 1--12, Qwen has 132 unresolved cases and Gemma has 108 unresolved
cases. The per-dataset cumulative AC@1 coverage is now:

| model | AegisLab | AIOPS-2022 | AIOPS-2025 | RE2-OB | RE2-TT |
|---|---:|---:|---:|---:|---:|
| Qwen3.8 | 82/100 | 56/100 | 56/100 | 80/90 | 74/90 |
| Gemma | 88/100 | 59/100 | 55/100 | 86/90 | 84/90 |

The 80% per-model, per-dataset stopping criterion has not been reached because
both models remain below target on AIOPS-2022 and AIOPS-2025. Making logs
readable as text did improve the rank of 15 Qwen and 18 Gemma unresolved cases,
but almost never moved the root to rank 1. The next round therefore needs a
substantially different evidence-selection or integration intervention rather
than another small transport-only variation.

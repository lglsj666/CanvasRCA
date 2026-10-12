# Round 12 — full remaining cohorts, trace text with M/L/G dashboard

This round applies `TRACE_TEXT_MLG_VISUAL_RESOURCE24_full_remaining_v3` to
every case left unresolved after round 11: 144 Qwen cases and 127 Gemma cases.
Their union contains 180 distinct cases; no inference subset is used.

The selected trace evidence is supplied as canonical text with the full
operation name, baseline/current counts, exclusive p95 latency,
current-period inclusive p95 latency, log2 changes, and TRC-L screening score.
Metrics, logs, and topology remain in one real dashboard image. The selector,
task, SIRCL-style RCA procedure, candidate list, output contract, scorer,
model recipes, and attention-off protocol remain fixed.

The complete CPU audit passed for all 180 unique inputs. R text and M/L/G image
fact IDs are disjoint and their union covers the complete selected evidence;
the selected facts themselves are unchanged from round 11. Six cases contain
no selected trace row and use the registered zero-row R representation without
dropping an available trace fact. Five actual images were opened, one per
dataset: `INC-B4C69A1E0459`, `INC-46EA9B460B2C`, `INC-6DCAE95A54B2`,
`INC-D25E7590F78E`, and `INC-452942E7A056`. They are readable and contain no
private label, raw case identity, dataset name, absolute time, filesystem path,
or injection-time marker.

Exact same-model request matching against rounds 1–11 found no reusable
outcomes. The immutable source archive contains 121 runtime source and
configuration files and has SHA256
`b972adbaec4e106e645b6a237c1eff8c35e2a1e23677653642b47a5491f56e98`.

Model execution completed for every registered target: 144/144 Qwen and
127/127 Gemma outcomes, for 271/271 total. All statuses are `complete`, all
finish reasons are `stop`, no outcome was reused, and the persisted artifact
audit passed.

This round newly retired 10 Qwen cases (AegisLab 0, AIOPS-2022 1,
AIOPS-2025 3, RE2-OB 1, RE2-TT 5) and 19 Gemma cases (AegisLab 0,
AIOPS-2022 2, AIOPS-2025 2, RE2-OB 4, RE2-TT 11). After cumulative union with
rounds 1--11, Qwen has 134 unresolved cases and Gemma has 108 unresolved
cases. The per-dataset cumulative AC@1 coverage is now:

| model | AegisLab | AIOPS-2022 | AIOPS-2025 | RE2-OB | RE2-TT |
|---|---:|---:|---:|---:|---:|
| Qwen3.8 | 81/100 | 56/100 | 55/100 | 80/90 | 74/90 |
| Gemma | 88/100 | 59/100 | 55/100 | 86/90 | 84/90 |

The 80% per-model, per-dataset stopping criterion has not been reached because
both models remain below target on AIOPS-2022 and AIOPS-2025. The experiment
therefore proceeds to another full-remaining-cohort intervention.

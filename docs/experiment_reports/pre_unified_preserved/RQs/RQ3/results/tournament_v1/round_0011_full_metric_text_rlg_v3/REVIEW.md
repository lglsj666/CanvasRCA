# Round 11 — full remaining cohorts, metric text with R/L/G dashboard

This round applies `METRIC_TEXT_RLG_VISUAL_RESOURCE24_full_remaining_v3` to
every case left unresolved after round 10: 187 Qwen cases and 164 Gemma cases.
Their union contains 232 distinct cases; no inference subset is used.

The selected metric evidence from round 10 is moved from the dashboard into a
readable canonical text block. Trace, log, and topology evidence remains in one
real dashboard image. The task, SIRCL-style RCA procedure, candidate list,
output contract, scorer, model recipes, and attention-off protocol remain
fixed. This satisfies the tournament rule that at most one evidence modality
may be textual while the other three remain visual.

The complete CPU audit passed for all 232 unique inputs. M text and R/L/G image
fact IDs are disjoint and their union covers the complete selected evidence;
R, L, and G facts are unchanged from round 10. Every rendered image changed
because the M region was removed. Five actual images were opened, one per
dataset: `INC-133324A21C16`, `INC-46EA9B460B2C`, `INC-B8CEA35848D0`,
`INC-D25E7590F78E`, and `INC-452942E7A056`. They are readable and contain no
private label, raw case identity, dataset name, absolute time, filesystem path,
or injection-time marker.

Exact same-model request matching against rounds 1–10 found no reusable
outcomes. The immutable source archive contains 120 runtime source and
configuration files and has SHA256
`b37d9a34ada86d2bb7c53b2d6687ff86e79a8df81afc151fafc8b529569d4da5`.

The first launch stopped before any model request because the worker's
candidate-binding guard still assumed the pure-visual candidate slot. The
guard now delegates to the registered pure/hybrid prompt validator; targeted
and full current-source CPU regressions passed. The failed pre-call work specs
and runtime files were removed before the work specs and source snapshot were
rebuilt.

Both model phases committed successfully. Qwen newly retired 43 cases
(1 AegisLab, 13 AIOPS-2022, 7 AIOPS-2025, 16 RE2-OB, 6 RE2-TT), leaving 144.
Gemma newly retired 37 cases (2, 10, 4, 14, 7 respectively), leaving 127.
Of 351 outcomes, 350 completed normally and one was retained as a model
failure. Every request stopped normally at the server level, and the post-run
shared-input and artifact audit passed with no infrastructure error.

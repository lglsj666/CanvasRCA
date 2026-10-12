# Round 9 — full remaining cohorts, peer-shift metric selection

This round applies `PEER_SHIFT_HALF_NATIVE_TOP24_full_remaining_v3` to every
case left unresolved after round 8: 204 Qwen cases and 178 Gemma cases. Their
union contains 244 distinct cases; no inference subset is used.

The method keeps the first eight native metric panels and fills sixteen more
slots using a frozen half-native, half peer-residual priority. It is intended
to surface entity metrics whose behavior differs from comparable peers rather
than merely repeating the globally strongest series. R, L, G, candidates,
prompt, scorer, model recipes and attention-off protocol remain unchanged.

All 244 final PNGs passed source binding, prompt/candidate identity, geometry,
clipping, determinism and leakage checks. Five actual images were opened, one
per dataset: `INC-133324A21C16`, `INC-46EA9B460B2C`,
`INC-B8CEA35848D0`, `INC-D25E7590F78E`, and `INC-452942E7A056`.
They are readable and contain no private label, raw case identity, dataset
name, absolute time, filesystem path or injection-time marker.

Exact same-model request matching against rounds 1–8 found three reusable
Qwen outcomes and two reusable Gemma outcomes. All other registered targets
require new model calls. The immutable source archive contains 119 runtime
source/configuration files and has SHA256
`903dbbc3aa692b1131a5edadf5b778ae8a571ac85ddbc95053f271366bdbe0aa`.

Both model phases committed successfully. Qwen newly retired 11 cases
(3 AegisLab, 5 AIOPS-2022, 3 AIOPS-2025, none in RE2), leaving 193. Gemma
newly retired eight cases (2, 3, 1, 1, 1 respectively), leaving 170. Of 382
logical outcomes, five were exact-request reuses; 381 completed normally and
one was retained as a model failure. The post-run shared-input and artifact
audit passed with no infrastructure error.

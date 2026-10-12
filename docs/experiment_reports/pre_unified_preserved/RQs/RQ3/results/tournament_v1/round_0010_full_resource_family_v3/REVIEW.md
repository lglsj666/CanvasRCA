# Round 10 — full remaining cohorts, resource-family metric selection

This round applies `RESOURCE_FAMILY_NODE_SERVICE_ADDITIVE_full_remaining_v3`
to every case left unresolved after round 9: 193 Qwen cases and 170 Gemma
cases. Their union contains 237 distinct cases; no inference subset is used.

The method prioritizes a broad, additive mix of resource families across
service, pod, and node owners so that CPU, memory, I/O, latency, traffic, and
related infrastructure signals are not displaced by many near-duplicate
series from one family. R, L, G, candidates, prompt, scorer, model recipes and
attention-off protocol remain unchanged.

All 237 final PNGs passed source binding, prompt/candidate identity, geometry,
clipping, determinism and leakage checks. Every case changed both the selected
metric panels and the rendered pixels relative to round 9; trace and log
content remained fixed. Five actual images were opened, one per dataset:
`INC-133324A21C16`, `INC-46EA9B460B2C`, `INC-B8CEA35848D0`,
`INC-D25E7590F78E`, and `INC-452942E7A056`. They are readable and contain no
private label, raw case identity, dataset name, absolute time, filesystem path
or injection-time marker.

Exact same-model request matching against rounds 1–9 found 19 reusable Qwen
outcomes and 16 reusable Gemma outcomes. All other registered targets require
new model calls. The immutable source archive contains 119 runtime
source/configuration files and has SHA256
`f663e8b4e56f3122f1ac2a7b19ae21ee599c74cd34ed0c1f6562e54a17ea7307`.

Both model phases committed successfully. Qwen newly retired six cases
(0 AegisLab, 2 AIOPS-2022, 3 AIOPS-2025, 1 RE2-OB, 0 RE2-TT), leaving 187.
Gemma also newly retired six cases (3, 0, 1, 2, 0 respectively), leaving 164.
Of 363 logical outcomes, 35 were exact-request reuses; 362 completed normally
and one was retained as a model failure. The post-run shared-input and artifact
audit passed with no infrastructure error.

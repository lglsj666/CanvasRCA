# Round 5 — complete remaining cohorts, native SIRCL mean shift

This round applies the faithfully adapted SIRCL moving-average/three-sigma
metric selector (`sircl_ma24_v1`) to every case that remained after round 4.
It changes the selected metric evidence to the top 24 native qualifying
series, while retaining the registered trace, log, topology, prompt, candidate
and inference contracts. No attention or training is enabled.

The registered cohorts are all 247 unresolved Qwen cases and all 227
unresolved Gemma cases; their union contains 293 distinct cases. The gallery
was generated before inference. All 293 cases passed the source, prompt,
candidate, fact-binding, native-ranking, clipping, geometry and leakage CPU
checks. Every case changed metric panels and pixels relative to the round-1
anchor; trace and log selections did not change. There are no exact-input
references to retained earlier rounds, so every logical target is a new call.

Five actual generated dashboards were opened, one deterministically selected
from each dataset: INC-A89422C045DE, INC-358CBE8D4527,
INC-C2222DBA0446, INC-C17A00DC78FC and INC-FCEC7B343F4C. Each remains a
single bounded M/R/L/G dashboard. The 24 metric lanes are intentionally dense,
but the native-resolution images retain labels, units, trace comparisons, log
details, exact edge ledgers and candidate-independent identifiers. No outer
card overlap, clipping or label leakage was observed in these samples.

Both model work specifications exactly equal their registered unresolved
cohorts. The complete 181-file source/config archive was byte-verified against
the preceding immutable snapshot before reuse; SHA256 is
`16df5fee4a4fcecd931ac9292da0632fd164e7f74c49da98c377df2762d87660`.
The models run sequentially through the existing resumable supervisor.

## First Qwen in-run inspection

At the first 15-minute check, 81/247 Qwen outcomes were complete, all with
normal status and no error; seven were new top-1 hits. Hash-selected case
INC-97B043342751 was inspected by reading its complete conversation, verifying
all four artifact hashes, and opening the exact persisted PNG. The response
has five distinct candidates, 147 output tokens and normal `stop` finish.

The response cites visible metric and topology facts, but ranks the accepted
answer fourth. It calls service 104 earlier than service 247 even though the
printed onset rows are both 7.8 minutes and the prompt explicitly says that
coincident onset does not establish ordering. This is a model reasoning error,
not a missing-input, prompt-contract, renderer, schema or persistence defect;
the valid result is retained without retry or in-flight modification.

## Verified completion

Both registered cohorts committed and the post-run audit passed all 474
outcomes and 181 overlapping Qwen/Gemma model-visible inputs. All 474 were new
calls. Qwen produced 247 normal completions and 15 new top-1 hits. Gemma
produced 225 normal completions, 15 new top-1 hits, and two registered model
failures whose responses reached the 8,192-token ceiling while repeating text.
Those two length/parse failures are 0.88% of Gemma's cohort, are scored zero,
and are retained without correctness retry. There were no missing outcomes or
infrastructure failures.

Cumulative top-1 union after this round is 248/480 for Qwen and 268/480 for
Gemma, leaving 232 and 212 cases respectively. Qwen coverage by dataset is
AegisLab 65, AIOPS-2022 29, AIOPS-2025 34, RE2-OB 60 and RE2-TT 60. Gemma
coverage is respectively 70, 38, 37, 61 and 62. Neither model meets the
per-dataset 80% stopping contract.

The paired Gemma response for inspected case INC-97B043342751 also has five
candidates, a normal stop and complete persisted artifacts, but ranks the
accepted answer third. It claims that service 952 has an onset printed in G,
although the displayed onset list contains 104, 150, 204 and 247. This is a
model grounding/hallucination outcome rather than a renderer or data-integrity
failure. As in round 4, vLLM's final `EngineDeadError` follows the explicit
post-commit SIGTERM and does not correspond to a failed request.

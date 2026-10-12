# C smoke manual review — 2026-09-28

Passed: 18/18 calls, 260.863 seconds, Qwen then Gemma, all model_status
complete, automated artifact review errors empty. These calls are qualification
only, not formal efficacy observations. Shared initiated-call count is 24661.
No attention or training, no new model recipe, no additional smoke requests.

Read every saved response, inspected conversation persistence for all eighteen
records (each contains the exact returned response and input), and checked
prompt part structure, numeric-ID candidates, unit/relative-time instructions,
text/PNG presence and absence of raw case IDs/source paths. Compared all eighteen
complete input identities to the corresponding original A input: eighteen
exact matches. This audit is qualification-specific, not a new resume gate.
Inspected actual saved LOCAL_LINK PNGs for all three cases and the REMOTE_ID
PNG for INC-07B8919442D8. Previously reviewed CPU examples also cover the two
new RE2 source schemas. The plotted means, observation ownership and complete
relation ledgers are present; common reserved blank slots remain as registered.

Input examples: INC-07B8919442D8, INC-8201EB3924F3,
INC-50C26A55D214; REMOTE_ID/T_MATCH/LOCAL_LINK, both models. Qwen inputs
14028–24738 tokens; Gemma 14723–17438; outputs 104–199 tokens. Output ceiling
remains 8192. All calls fit the unchanged model contracts.

Model-behavior caveats, not implementation repairs: Qwen described pending
finalization counts as GC pauses and asserted unsupported propagation facts;
some answers confused service and pod IDs in prose or claimed temporal order
not supported by their own cited times. Gemma frequently emitted one candidate.
Do not pad answers, change prompts, reject low-MRR samples, or retry to improve
correctness. Full outputs remain under stages/smoke_C_qualification/.

User separately authorized C; after this review its formal authorization is
enabled. CPU cold preparation precedes the sequential formal model queue.
The exposed eval/test results remain separate from unavailable fresh events.

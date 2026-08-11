# 2026-08-10 — Visual diagnostics and max-num-seqs qualification

## Scope and status

RQ1 successor implementation and local qualification. The existing six RQ1
experiments and all registered arms remain unchanged. The work adds a
model-call-free diagnostic layer and changes only the global vLLM scheduler
capacity from `max_num_seqs=64` to `max_num_seqs=128`.

## Implementation

- Added deterministic 16×16 image patch atlases for the controlled canvas,
  full dashboard, routed dashboard, and counterfactual variants.
- Added per-arm blank/evidence density and M/L/R/G coverage records.
- Added Stage-1 ledger region-selection counts/shares to analysis.
- Added an optional hash-matched external attention-artifact overlay. Standard
  vLLM attention is recorded as `not_collected`; attention is not inferred from
  pixels or ledger choices and is not used as causal evidence or a gate.
- Kept exactly six experiments. No new arm, condition, or model call was added.
- Froze `vllm-inference-v4-nibi-maxseq128` and
  `CanvasRCAVLLMLockV4`.

## Inference parameters

The user's correction was applied explicitly:

- Global `max_tokens` remains 16,384.
- RQ1 `context_safe_output_v1` remains 8,192 for every model, experiment, arm,
  case, and stage.
- Both Qwen and Gemma now use `max_num_seqs=128`.

The generated global config SHA-256 is
`1495da42cac724bba2e65175b83ca619002a26b7f7d2b65b2d1116447595cb06` and
the lock SHA-256 is
`5317da64f97b6667742612fd369940a6e2448097313083dcd35b943544be7a0b`.

## Static validation

The CPU/static suite passed with zero model calls. It parsed project Python,
verified both model server argument vectors contain `--max-num-seqs 128`,
checked the global and RQ1 token ceilings, reached all 14 registered reasoning
templates, and retained exactly six findings. The five functional RQ1 modules
contain 3,980 lines, below the 5,000-line limit. `git diff --check` passed.

## Local bounded smoke

The WSL deployment adapter ran Nibi code and configuration against local
models/data. This is diagnostic evidence, not a Nibi scientific result.

- Model: Gemma-4-26B-A4B-it.
- Cases: three prescribed local qualification cases.
- Calls: 10 of the 18-call cap.
- Wall time: 292.36 seconds of the 600-second bound.
- Effective values: global output 16,384; RQ1 requested output 8,192;
  `max_num_seqs=128`.
- All raw responses were nonempty; all prompts were recorded; all requests
  ended with `stop`; none was truncated.
- Nine of ten diagnostic responses parsed. The typed Stage-1 response omitted
  registered later steps, reproducing the known finite model-output issue; its
  failure-marker path completed and no infrastructure error occurred.
- The summary contained visual profiles for text-only, controlled H, routed R,
  targeted counterfactual, and dynamic-ledger paths. Attention was correctly
  marked uncollected.

## Client-concurrency diagnostic

A separate local four-call diagnostic compared the same two Legacy-Q9 prompts
sequentially and at client concurrency two. Both modes generated the same 853
total output tokens, normally stopped, and were untruncated.

| Mode | Wall time | Mean sampled GPU use | Peak sampled GPU use |
|---|---:|---:|---:|
| sequential | 26.32 s | 68.5% | 79% |
| concurrent 2 | 14.73 s | 77.1% | 96% |

Concurrency two produced a 1.79x wall-time speedup. Server logs showed two
simultaneously running requests. Inspection also found that the formal runner
looped serially and did not consume its existing `request_concurrency: 8`
field. The user required a repair while retaining the registered value eight.
The successor runner now partitions different cases into eight disjoint hash
residues, preserves every within-case arm/stage order, assigns one writer
thread per case worker, and performs a call-free consolidation scan.

Before live qualification, the user reduced the active request concurrency
from eight to four. The implementation remains case-level and preserves all
within-case ordering, but the successor protocol is now
`rq1_case_concurrency4_visual_diagnostics_v6` with four disjoint worker
residues. DD-78 records the change; no formal v5 result was created.

## Validity and next step

Historical results and artifacts retain their recorded status and bytes. They
are not rewritten or reclassified, and predecessor runs cannot resume into the
new code/config freeze. Before the next Nibi successor run, repeat preparation
and runtime freeze using the new hashes. The new case-concurrency-four runner
requires a bounded smoke before heavy execution.

## Hidden typed Stage-1 issue found during smoke review

The completed ten-call diagnostic contained one typed Stage-1 sample. Gemma
returned valid JSON with the registered `q1`, `q2`, and `q3` identifiers, but
included only step 1 for q2 and q3. The deterministic validator correctly
rejected it because q2 required two regions and q3 required three. The request
ended normally after 1,955 of 8,192 allowed output tokens, so this was neither
truncation nor a server/concurrency failure.

Historical typed-v3 artifacts show that Gemma Stage-1 transfer failure was
common rather than anecdotal: 629/1,530 development case-arm cells (41.1%;
79/90 cases had at least one) and 654/1,530 independent cells (42.7%; 83/90
cases had at least one) produced a failure transfer. Qwen's corresponding
rates were 7/1,530 (0.46%) and 5/1,530 (0.33%). The old dominant Gemma failure
was query-ID mismatch; short q1/q2/q3 identifiers remove that exact failure in
the new sample, but do not enforce step completeness.

Code inspection found that the server JSON schema permits one to three
observations for every ledger row; it cannot express the query-specific
requirement that q1/q2/q3 contain exactly one/two/three registered region
steps. The prompt states that every step should be copied, but Gemma did not
follow that semantic constraint. This is recorded as a Gemma-specific typed
prompt/schema contract risk. No prompt or experiment logic was changed during
this operational-concurrency task, and typed scientific execution should not
proceed without an explicit successor design and bounded qualification.

## Case-concurrency-four formal-runner smoke

The local adapter exercised the actual Nibi `prepare -> main run` path on the
three prescribed validation datasets with Legacy-Q9 T/V/H. A diagnostic-only
symlink view supplied local model files and model identity manifests without
changing Nibi configuration or model directories.

- Calls: 9 of the 18-call cap.
- Completed records/conversations: 9/9 and 9/9.
- Infrastructure errors: 0.
- Truncations: 0.
- Request concurrency recorded by the consolidated runner: 4.
- Worker partitions: 4 disjoint residues.
- Maximum observed live concurrency: 3 requests, limited by the three-case
  smoke rather than the configured ceiling.
- All query memberships parsed; correctness remained diagnostic-only.
- A second run with no live server skipped all nine hash-valid records and
  reported zero newly completed calls and zero new errors.

The server emitted a non-blocking local optional DeepGEMM import warning and
continued with the registered Triton backend. No conversation, response,
persistence, prompt, or accounting issue was found. This smoke qualifies the
case-level concurrency implementation operationally; it is not an RQ result.

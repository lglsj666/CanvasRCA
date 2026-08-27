# RQ1.1 experiments

## Shared contract

All three experiments use the frozen 469-case Nibi roster, the single
`CanvasRCAProcessedPublicCaseV2` preparation path, and the unified scorer and
vLLM client. The RQ1.1 renderer began as a byte-for-byte RQ1 renderer-v12 copy.
Renderer-v13 is its registered successor: it selects the first finite trace
timestamp source instead of fabricating time from row position, conditionally
adds the minimum label-blind topology context needed when the severity-first
display set has no direct edge, and normalizes displayed negative-zero trace
change. No metric values, candidates, labels, sampling, prompts, or scorer are
changed. Public
evidence contains no label, fault type, raw case ID, dataset name, absolute
time, path, or natural service/pod/node name.

Logs use `DenumReadableLogGraphV1`, a readable adaptation of Denum's numeric
token parsing and repeated-structure separation. It keeps templates, numeric
variables, relative bins, severity, and multiplicity in text/graph form. It
does not produce or decode binary data. Its text and visual projections share
one semantic fact inventory.

## Experiment 1: `direct_qa`

One model call reads the full real dashboard and answers one deterministic
question per level. Each answer step carries its first returned entity into
the next region, so later lookups depend on earlier visual reads. L1 has the four single-region paths. L2 contains all 12
ordered pairs of M/R/L/G; L3 all 24 ordered triples; L4 all 24 permutations of
all four regions. A label-blind SHA256 rule selects one registered template for
each case and level. Every template is deterministically scorable; an explicitly
displayed missing region yields the literal value `missing` rather than a case
or question replacement. Metrics are complete-chain, step, and correct-prefix
accuracy.

## Experiment 2: `direct_rca`

One model call returns the frozen top-five RCA JSON. The seven equal-fact arms
are:

- `T`: all M/R/L/G evidence as natural-language text.
- `V`: the complete real renderer-v13 dashboard.
- `S`: the exact T incident fragment rendered losslessly as screenshot pages.
- `LV`: only logs visual; metrics, traces, and topology are text.
- `MV`: only metrics visual; traces, logs, and topology are text.
- `TCV`: only traces visual; metrics, logs, and topology are text.
- `TPV`: only topology visual; metrics, traces, and logs are text.

Visual fragments precede text. Every mixed arm uses source-pixel crops from V;
facts encoded visually are not repeated in that arm's text. MRR is primary;
AC@1/3/5 and AVG@3/5 are secondary. Each visual arm is paired against T with
Holm correction. `S−T` is the negative-control comparison.

S uses the mature RQ1 pixel-text geometry and measured lossless line wrapping,
but its source is the exact RQ1.1 T incident fragment. It is not the real
dashboard and never reads the JSONL serializer or a second summary.

## Experiment 3: `multi_stage_rca`

The same seven arms initialize a fixed three-step state machine. Each step has
one planner call, one deterministic host tool execution, and one analysis call.
Because the two model calls are stateless API requests, the analysis request
replays the identical arm representation before adding the planner history and
tool observation; otherwise the ranking update would not have access to the
visual/text evidence that motivated the tool choice. This replay is common to
all arms and is included in token accounting.
The available tools are `search_metrics`, `search_traces`, `search_logs`, and
`search_topology`; all arms and models have identical tool data and budgets.
Step 3's temporary ranking becomes the final frozen RCA output. The experiment
uses six model calls per case/arm and reports RCA, token, tool-selection,
empty-result, invalid-call, repair, and break metrics.

Every model call records same-prefill attention at the registered first
full-attention layer. The probe stores the final prompt query's normalized
attention over all prior prompt keys, including both text and image tokens.
Visual requests additionally retain image-token weights, 16x16 grids, and
hash-matched overlays. Text attention is mapped to the system/task shell,
candidate/common text, M/R/L/G evidence spans, tool history, and unassigned
control tokens; both raw mass and token-count-normalized focus are reported.
Visual records also retain value-vector norms and pre-output-projection
attention-weighted value norms. The first grid row is reported separately as
`dashboard_header_band`, with first-patch rank and peak-to-median ratios,
instead of being counted as M/G evidence. This can identify a positional/sink
candidate, but the project will not call it an attention sink without
registered content and position interventions.
The probe does not add a model call or modify Q/K/V tensors or generation.
Attention is correlational diagnostic evidence, not a causal explanation and
not an efficacy gate. Qwen3.8 and Gemma retain their distinct,
already-approved official processor/runtime recipes; representation equality
refers to incident facts, not equal tokenizer or image-token counts.

RQ1.1 does not seek to prove a visual advantage. Its registered outcomes are
representation effects on RCA, direct cross-region reasoning, bounded tool use,
attention allocation, and cost. Negative, null, mixed, and architecture-
specific effects retain the same evidentiary status as positive effects.

## 2026-08-27 renderer-v13 protocol amendment

The user authorized this amendment after inspecting the three real-case smoke
dashboards. It supersedes only the RQ1.1 renderer-v12 qualification state; the
historical RQ1 renderer and historical RQ1 results remain unchanged. The RE2
sample exposed an all-null stored `timestamp` field despite valid
`startTime`/`startTimeMillis` fields, while the AIOPS-2022 sample exposed an
edgeless severity-selected topology subset despite valid source call edges.
The fixes are deterministic, label-blind, and represented in both visual and
text fact inventories. Existing smoke established end-to-end execution; at the
user's direction this amendment is qualified with CPU validation, determinism,
leakage/equality checks, and new human-reviewed sample renders rather than a
new model-calling smoke.

The user accepted the renderer-v13 samples on 2026-08-27. RQ1.1 v1 was therefore
qualified for the registered local 469-case formal sequence: `direct_rca`,
`direct_qa`, then `multi_stage_rca`, with Qwen3.8 followed by Gemma inside
each experiment. The accepted v13 review, prior bounded end-to-end smokes, and
unchanged model inference recipes authorize execution without another smoke.

## 2026-08-27 complete candidate-universe correction

The first 164 diagnostic `direct_rca` records exposed an input-contract defect
before the formal run was allowed to continue. On AIOPS-2022, the historical
renderer manifest's `services` field contained pod and node identities but
omitted model-visible service identities. The prompt nevertheless advertised
that subset as an exhaustive candidate list. Twenty-seven responses therefore
returned a visible service ID that the validator correctly rejected as an
unknown candidate. This was an invalid-input failure, not a vLLM, JSON,
renderer, scorer, or model-capability result; the diagnostic records remain
archived under their original run ID and cannot enter RQ1.1 statistics.

RQ1.1 v2 defines candidates as the sorted complete case-local numeric image of
the same label-blind entity universe used by the anonymizer: every telemetry,
graph, deployment, service, pod, and node identity that can appear in public
evidence or a tool result. A fail-closed compiler assertion requires every
model-visible fact entity to belong to this set. Static checks also exercise a
deliberately incomplete candidate fixture. A real AIOPS-2022 reproduction grew
the candidate set from the legacy 46-identity subset to 85 eligible entities;
all 85 visible identities and all 63 tool-returnable identities were covered,
and the evaluator-private root service had an eligible numeric candidate. The
renderer, seven representation encodings, prompts, tools, scorer, roster,
sampling, and model-specific inference recipes are unchanged. All 469 prepared
cases must be regenerated under a new v2 result ID before formal inference is
restarted in the same registered order.

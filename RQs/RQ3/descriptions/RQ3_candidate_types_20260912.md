# DD-RQ3-SEARCH32 — Explicit candidate entity types

**Status:** prospective, train-only exploration. No validation/eval or training.

The strongest mean score on the common24 train cases remains SEARCH22's typed
node overview (.520833 AIOPS-2022; .429167 AIOPS-2025). Its complete reasons and
later SEARCH31 still confuse service/node/pod identity and sometimes invent
hosting based on digits or proximity. All candidate IDs are already legal;
this is not a schema repair or grounds to invalidate/retry old answers.

Test one generic interface intervention: replace the flat candidate JSON list
by rows `[ID, entity_type]`, deriving type only from the existing public
3/4/5-digit identity convention. Preserve candidate membership and order,
and preserve the exact enum/order in the output schema. These rows disclose
neither diagnostic telemetry nor recommendations, relationships or labels.
Do not restrict alternatives to entities selected in the image. Candidates
remain exclusively in the prompt; no candidate panel is drawn.

Reuse SEARCH22's exact packets, PNG bytes, selection/projection, static task,
reading guide, output schema and Qwen card_nonthinking_v1 sampling. Only the
candidate enumeration format changes. The original pure-vision diagnostics,
no-attention rule and8192 actual output ceiling remain. Same24 training cases,
12 each, offset6 and seed42. No case-specific/private-label prompt branches.

Candidate parsing must explicitly validate the typed rows and reject malformed
types/IDs instead of silently changing the enum. Test old flat behavior and
all24 exact PNG/input comparisons. Freeze current code/config/input hashes and
archive the dependent source before calls. Use24 new calls,4 concurrent,
3600-second bounded development window. These are not nominal new smokes.

Read all complete responses after completion. Report MRR, AC@1/3/5, AVG@3/5,
input/image/output tokens, errors, paired repair/break and exploratory
Pratt-Wilcoxon/dz/Holm across two datasets. Count explicit entity-type mistakes
in reasons with a conservative deterministic matcher and manually inspect
matches; absence of such a phrase is not proof of correct entity reasoning.
No improvement or target attainment is presumed from these repeated train
cases. Preserve all outputs, including negative or null results.

## Pre-call review

21 targeted CPU tests and257 full CPU tests passed (full run74.56s). The
production five-module source audit is5995 lines. Old and typed request paths
preserve schema order, sampling, attention-off persistence and completed-call
resume. A mismatched candidate type fails before token preflight or inference.
All24 source/packet/manifest/PNG identities and unchanged non-candidate prompt
parts pass. Fresh review opened the actual inherited4BA dashboard. No renderer
modification or whole-corpus preparation is needed. The supplementary CPU
audit scripts are retained with result artifacts; runtime logic stays in the
five source modules. The unchanged canonical CLI executes the batch.

## Zero-call integration failure and repair

The first launch stopped at the worker's independent flat-list validator,
before any model request. The request-layer tests above had not exercised a
typed candidate payload through this worker boundary. Original108.137s startup
and failed qualification are retained in `candidate_types_development_v1`.
Both worker and request now use one strict candidate decoder. Typed worker
coverage and malformed/mixed/duplicate examples pass35 targeted CPU tests;
the production module count is6000. The24 prepared inputs are unchanged.
The successor run is `candidate_types_development_v2`; this is not a model
retry and does not overwrite the failed operational record.

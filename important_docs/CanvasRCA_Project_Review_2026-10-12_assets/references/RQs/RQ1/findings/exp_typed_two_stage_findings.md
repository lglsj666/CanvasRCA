# Typed Two-Stage Findings

**Status:** v22 case-eligible record-key handoff successor passed its fresh
dual-model logical smoke; the v22b formal rerun has started and is incomplete. Qwen job 19726652 and
Gemma job 19726654 completed all six case/arm records and all twelve stages per
model with zero infrastructure errors, parse failures, truncations, or
overlength responses. The inspected v21 smoke remains valid for its
three-question packets but does not exercise the new one- and two-question
schemas. Predecessor
compact and Controlled-canvas trajectories are archived diagnostic material;
the historical cross-architecture gate failed and cannot support a
real-dashboard claim.

**V20 qualification defect.** Artifact review found that Stage 1 could select
the canonical visible value kind `entity_id`, but the host binder looked only
inside region-specific payload fields. Numeric identity is stored in the
public fact envelope, so otherwise valid `M*` and `G:<entity>` selections were
misclassified as unsupported. V21 binds only the exact `entity_id` name from
that public envelope; it continues to reject aliases and invalid record keys.
All v20 smoke outputs remain diagnostic and do not qualify a formal run.

**Nibi v17 smoke correction.** Qwen Stage 2 began a valid response and then
generated 3,690 schema-legal whitespace tokens until the bounded supervisor
stopped it. The installed vLLM 0.24 configuration defaulted to
`backend=auto`, `disable_any_whitespace=false`; xgrammar consequently admitted
unbounded spaces and newlines. This phase is invalid as qualification evidence,
not a valid timeout-only pass. Runtime v6 explicitly uses xgrammar with
arbitrary JSON whitespace disabled for both models. A new bounded typed smoke
is required before formal execution.

The typed handoff removed the earlier eight-row ledger bottleneck. On the
12-case perception qualification, Qwen passed all registered mechanism checks:
level-1 accuracy was `11/12`, level-2 was `12/12`, and the required edge/link
families passed. Gemma obtained `7/12` and `5/12`, with three Stage-1
truncations; it failed the primary gate even though Stage 2 itself parsed.

The result supports a Qwen-specific claim that the supplied dashboard and typed
handoff are usable. It does not establish a cross-architecture mechanism and it
does not measure RCA MRR. The compact implementation retains a finite failure
marker so a malformed Stage-1 response cannot flood Stage 2 with raw output.

These local outcomes are not substituted for the registered final Nibi rerun.
This file will be updated with the 289-case primary headline and separate
RE2-OB/RE2-TT slices after that run is complete and verified.

Both archived predecessor diagnostics exercised the finite failure path. In the
first, Gemma duplicated an edge ID into `entity_id`; in the focused successor,
it omitted later registered steps for two queries. Stage 2 parsed the bounded
failure-marker input in both runs. The host did not repair either model error.

**Successor protocol.** Code inspection of the completed local formal runs
showed that the predecessor schema accepted one to three generic observations
per query and only rejected missing/duplicated query membership or step paths
after generation. It also required the model to transcribe complete 16-bin raw
sequences. This transport burden caused one omitted step to discard the whole
three-question ledger, while the final Stage-2 JSON could still parse. Protocol
`rq1_typed_selector_binding_v9` replaces only that transport with fixed
q1/q2/q3 step slots and a label-blind public-packet binder. VisOps questions,
private answers, representations, renderer, scoring, and the other five
experiments are unchanged. Existing results retain their recorded status; the
successor requires a new bounded qualification and new result ID.

An official-configuration audit found a separate issue: Gemma recommends
`top_k=64`, while Qwen recommends `top_k=20` and, specifically for non-thinking
mode, `temperature=0.7`, `top_p=0.8`, and `presence_penalty=1.5`. The active
project contract still intentionally uses common `temperature=1.0/top_p=0.95`
and does not silently change sampling in this transport revision. A matched
same-prompt Gemma diagnostic produced byte-identical 4,239-token outputs under
effective `top_k=0` and `top_k=64`, including the same missing Level-3 steps.
Thus the missing official `top_k` is a configuration-fidelity issue but not the
direct cause of this Stage-1 failure.

**Bounded successor qualification.** A three-case, six-call Gemma smoke covered T, V,
and H. All six requests stopped normally; Stage 1 and Stage 2 both parsed for
all three cases. Stage-1 output fell to 303–351 tokens instead of the 4,239
tokens observed in the matched predecessor diagnostic. Manual conversation
review found that the controlled visual canvas prints `bins/events/errors/
spans/p95ms`, while the text packet uses canonical `_16` field names. A frozen
public-field alias map corrected this binder-side representation mismatch.
The first schema revision exposed a new infrastructure regression: because
every identifier was nullable, Gemma filled all six image-only selectors with
null even though the latest formal all-visual runs had produced identifiers in
90/90 development and 90/90 independent cases. V9 derives from each public
template whether the step requires an entity or edge and makes that identifier
mandatory. The same three-case smoke then bound V 6/6 and H 6/6 steps. T's
remaining apparent 1/6 miss was the valid case of a visible entity with zero
incident edges; v9 represents that verified absence explicitly rather than as
an unsupported selector. Post-hoc binding of unchanged raw responses is now
6/6 for T, V, and H. The smoke validates transport integrity, not model
accuracy or the final RQ1 claim.

**Cross-model v10 qualification.** The v9 Qwen formal-path diagnostic completed
the text and hybrid cells but left the all-visual Stage-1 request generating
until the 600-second smoke bound. Protocol
`rq1_typed_selector_binding_v10` therefore constrains only the already-public
identifier syntax in the shared response grammar: entity IDs are three to five
digits, edge IDs are `E##`, and panel IDs are `M##`. It does not change the
questions, visible evidence, private answers, arm semantics, scorer, or either
model's scientific prompt.

Fresh sequential three-case formal-path smokes then exercised T, V, and H for
both architectures. Qwen and Gemma each completed all six calls with both
stages parsed, `finish_reason=stop`, zero truncation, zero infrastructure
errors, and 6/6 supported Stage-1 steps in every arm. Qwen Stage-1 completions
were 431--469 tokens; Gemma's were 349--358. Manual inspection found no failure
marker, fenced response, thinking trace, or unrecorded prompt. Matching
case/arm Stage-1 prompts were byte-identical across models. Stage-2 uses the
same system/task contract but necessarily receives the ledger produced by its
own model, so its incident prompt is not expected to be byte-identical.

This bounded predecessor evidence resolved its observed transport failures for
the tested T/V/H paths. It remains infrastructure and mechanism qualification,
not an efficacy result. The current v17 Q&A representation correction requires
fresh preparation and a new result ID.

# Train-subset development result

Exploratory 24-case search, not validation/eval and not a target-achievement claim. No attention collected.

| Dataset | Variant | N | MRR | Input tokens | Output tokens | Model failures |
|---|---|---:|---:|---:|---:|---:|
| aiops2022 | node_overview_v1__evidence_candidate_types_v1__card_nonthinking_v1 | 12 | 0.4514 | 17927.0 | 276.4 | 0 |
| aiops2025 | node_overview_v1__evidence_candidate_types_v1__card_nonthinking_v1 | 12 | 0.4167 | 17776.8 | 410.9 | 0 |

Compared with the same24 SEARCH22 typed-dashboard/flat-candidate control:
AIOPS-2022 MRR .520833→.451389; AIOPS-2025 .429167→.416667. One RR repair,
four breaks and19 ties. Both exploratory Holm p=1; this does not establish a
population-level worsening, and the candidate is not promoted.

Conservative explicit type-mention mismatch cases decreased6/24→1/24; this
counts singular service/node/pod followed by a numeric ID, not every identity
or causal claim. All matched phrases and full responses were manually read.
Correct entity-type words did not translate into higher MRR in this batch.

Input cost increased173 tokens/case in AIOPS-2022 and128 in AIOPS-2025; image
tokens stay16,002. Average output increased255→276.42 and270.58→410.92. The
largest response (1,723 tokens,4DBB) repeatedly revisited service/pod membership
inside its public `reason`, then terminated normally. No truncation or retry.

24/24 completed in439.271s. All actual request/artifact checks pass; the output
schema, candidates/order, PNGs, other prompts, model and sampling match the
control. No attention or training/evaluation calls. The first zero-call
worker-parser failure remains in `../candidate_types_development_v1/`.
Full metrics, per-fault/granularity strata, paired scores and phrase matches:
`metrics_breakdown.json`, `paired_review.json`, `logs/20260912_review.md`.

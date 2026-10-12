# Train-subset development result

Completed and fully reviewed; see [paired reasoning audit](../../../../../../../../RQs/RQ3/results/search_first_v1/thinking_low_development_v2/reasoning_audit.json)
and [case review](logs/20260912_review.md). No attention. Candidate entities are
in prompt text, not a candidate-list image panel. Public inputs match the
non-thinking parent; thinking/template/sampling is the joint intervention.

Exploratory 12-case search, not validation/eval and not a target-achievement claim. No attention collected.

| Dataset | Variant | N | MRR | Input tokens | Output tokens | Model failures |
|---|---|---:|---:|---:|---:|---:|
| aiops2022 | ranked_v1__evidence_bound_v1__card_thinking_low_v1 | 6 | 0.3333 | 6374.0 | 4919.2 | 0 |
| aiops2025 | ranked_v1__evidence_bound_v1__card_thinking_low_v1 | 6 | 0.3611 | 6268.0 | 5381.0 | 0 |

Parent non-thinking MRR was .2500/.3750, output 292.5/253.3 respectively.
Thus thinking increases output by 16.82×/21.24× without stable improvement in
both datasets. Four case RRs improve, two worsen, six tie. All final answers
stop normally; full reasoning is preserved. Targets remain unmet; no promotion
to validation/eval/training. First attempt v1 remains a separate, documented
runtime-mismatched diagnostic and is not part of this thinking effect estimate.

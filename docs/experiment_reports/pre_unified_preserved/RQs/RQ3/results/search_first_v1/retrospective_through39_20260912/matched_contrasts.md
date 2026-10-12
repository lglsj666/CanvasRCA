# All registered-reference retrospective contrasts

Matched case IDs. Compound interventions are labeled. Counts of repairs/breaks are not independent across rows.
Tests use cases; global Holm is an additional retrospective sensitivity, not replacement of original preregistration.

| Intervention | Dataset | n | Reference MRR | New MRR | Delta | Repair / break / tie | Input old → new | Output old → new |
|---|---|---:|---:|---:|---:|---|---|---|
| Grounding / ranked (prompt) | aiops2022 | 6 | 0.3333 | 0.3333 | +0.0000 | 0/0/6 | 8417 → 8590 | 209.7 → 181.2 |
| Grounding / ranked (prompt) | aiops2025 | 6 | 0.2222 | 0.3889 | +0.1667 | 1/0/5 | 8311 → 8484 | 168.8 → 175.7 |
| Grounding / coverage (prompt) | aiops2022 | 6 | 0.2083 | 0.2083 | +0.0000 | 0/0/6 | 8417 → 8590 | 192.8 → 185.2 |
| Grounding / coverage (prompt) | aiops2025 | 6 | 0.3333 | 0.3750 | +0.0417 | 1/0/5 | 8311 → 8484 | 147.0 → 176.0 |
| Grounding / local_contrast (prompt) | aiops2022 | 6 | 0.2222 | 0.3333 | +0.1111 | 1/0/5 | 8417 → 8590 | 171.3 → 172.7 |
| Grounding / local_contrast (prompt) | aiops2025 | 6 | 0.3333 | 0.0833 | -0.2500 | 0/2/4 | 8311 → 8484 | 169.2 → 173.8 |
| Selection coverage / inherited (selection) | aiops2022 | 6 | 0.3333 | 0.2083 | -0.1250 | 0/1/5 | 8417 → 8417 | 209.7 → 192.8 |
| Selection coverage / inherited (selection) | aiops2025 | 6 | 0.2222 | 0.3333 | +0.1111 | 1/1/4 | 8311 → 8311 | 168.8 → 147.0 |
| Selection local_contrast / inherited (selection) | aiops2022 | 6 | 0.3333 | 0.2222 | -0.1111 | 0/1/5 | 8417 → 8417 | 209.7 → 171.3 |
| Selection local_contrast / inherited (selection) | aiops2025 | 6 | 0.2222 | 0.3333 | +0.1111 | 3/1/2 | 8311 → 8311 | 168.8 → 169.2 |
| Selection coverage / grounded (selection) | aiops2022 | 6 | 0.3333 | 0.2083 | -0.1250 | 0/1/5 | 8590 → 8590 | 181.2 → 185.2 |
| Selection coverage / grounded (selection) | aiops2025 | 6 | 0.3889 | 0.3750 | -0.0139 | 0/1/5 | 8484 → 8484 | 175.7 → 176.0 |
| Selection local_contrast / grounded (selection) | aiops2022 | 6 | 0.3333 | 0.3333 | +0.0000 | 0/0/6 | 8590 → 8590 | 181.2 → 172.7 |
| Selection local_contrast / grounded (selection) | aiops2025 | 6 | 0.3889 | 0.0833 | -0.3056 | 1/2/3 | 8484 → 8484 | 175.7 → 173.8 |
| Nonthinking recipe (request) | aiops2022 | 6 | 0.3333 | 0.3333 | +0.0000 | 0/0/6 | 8417 → 8417 | 209.7 → 153.8 |
| Nonthinking recipe (request) | aiops2025 | 6 | 0.2222 | 0.3333 | +0.1111 | 1/1/4 | 8311 → 8311 | 168.8 → 156.3 |
| Concise / legacy (prompt) | aiops2022 | 6 | 0.3333 | 0.3333 | +0.0000 | 0/0/6 | 8417 → 7778 | 209.7 → 191.0 |
| Concise / legacy (prompt) | aiops2025 | 6 | 0.2222 | 0.2222 | +0.0000 | 0/0/6 | 8311 → 7672 | 168.8 → 238.2 |
| Concise / nonthinking (prompt) | aiops2022 | 6 | 0.3333 | 0.1667 | -0.1667 | 0/1/5 | 8417 → 7778 | 153.8 → 158.0 |
| Concise / nonthinking (prompt) | aiops2025 | 6 | 0.3333 | 0.1111 | -0.2222 | 0/2/4 | 8311 → 7672 | 156.3 → 207.3 |
| M24 coverage / legacy (selection) | aiops2022 | 6 | 0.2222 | 0.0000 | -0.2222 | 0/2/4 | 14231 → 14231 | 187.7 → 141.8 |
| M24 coverage / legacy (selection) | aiops2025 | 6 | 0.2639 | 0.2083 | -0.0556 | 1/2/3 | 14125 → 14125 | 181.8 → 170.7 |
| M8 to M24 / legacy (selection+canvas) | aiops2022 | 6 | 0.3333 | 0.2222 | -0.1111 | 1/1/4 | 8417 → 14231 | 209.7 → 187.7 |
| M8 to M24 / legacy (selection+canvas) | aiops2025 | 6 | 0.2222 | 0.2639 | +0.0417 | 1/1/4 | 8311 → 14125 | 168.8 → 181.8 |
| Bound guide + candidate enum / legacy (prompt+schema) | aiops2022 | 6 | 0.3333 | 0.3333 | +0.0000 | 0/0/6 | 8417 → 6350 | 209.7 → 296.3 |
| Bound guide + candidate enum / legacy (prompt+schema) | aiops2025 | 6 | 0.2222 | 0.2222 | +0.0000 | 0/0/6 | 8311 → 6244 | 168.8 → 279.3 |
| M24 coverage / card_nonthinking (selection) | aiops2022 | 6 | 0.3889 | 0.0000 | -0.3889 | 0/3/3 | 14231 → 14231 | 141.2 → 135.3 |
| M24 coverage / card_nonthinking (selection) | aiops2025 | 6 | 0.0000 | 0.2222 | +0.2222 | 2/0/4 | 14125 → 14125 | 145.8 → 138.3 |
| M8 to M24 / card_nonthinking (selection+canvas) | aiops2022 | 6 | 0.3333 | 0.3889 | +0.0556 | 1/0/5 | 8417 → 14231 | 153.8 → 141.2 |
| M8 to M24 / card_nonthinking (selection+canvas) | aiops2025 | 6 | 0.3333 | 0.0000 | -0.3333 | 0/2/4 | 8311 → 14125 | 156.3 → 145.8 |
| Bound guide + candidate enum / card_nonthinking (prompt+schema) | aiops2022 | 6 | 0.3333 | 0.2500 | -0.0833 | 0/1/5 | 8417 → 6350 | 153.8 → 240.2 |
| Bound guide + candidate enum / card_nonthinking (prompt+schema) | aiops2025 | 6 | 0.3333 | 0.3750 | +0.0417 | 1/0/5 | 8311 → 6244 | 156.3 → 227.0 |
| Trace microseconds to ms (unit repair) | aiops2022 | 6 | 0.2500 | 0.2500 | +0.0000 | 0/0/6 | 6350 → 6350 | 240.2 → 292.5 |
| Trace microseconds to ms (unit repair) | aiops2025 | 6 | 0.3750 | 0.3750 | +0.0000 | 0/0/6 | 6244 → 6244 | 227.0 → 253.3 |
| Low thinking (request) | aiops2022 | 6 | 0.2500 | 0.3333 | +0.0833 | 1/0/5 | 6350 → 6374 | 292.5 → 4919.2 |
| Low thinking (request) | aiops2025 | 6 | 0.3750 | 0.3611 | -0.0139 | 3/2/1 | 6244 → 6268 | 253.3 → 5381.0 |
| All public hosting (facts+canvas) | aiops2022 | 6 | 0.3333 | 0.2500 | -0.0833 | 0/1/5 | 6448 → 6448 | 269.0 → 277.7 |
| All public hosting (facts+canvas) | aiops2025 | 6 | 0.2500 | 0.0556 | -0.1944 | 0/2/4 | 6345 → 6345 | 280.2 → 249.3 |
| Cross-source selection (selection) | aiops2022 | 6 | 0.2222 | 0.1389 | -0.0833 | 2/1/3 | 6444 → 6444 | 258.0 → 283.8 |
| Cross-source selection (selection) | aiops2025 | 6 | 0.3667 | 0.3750 | +0.0083 | 2/1/3 | 6341 → 6341 | 240.0 → 257.0 |
| Field dictionary (prompt) | aiops2022 | 6 | 0.2222 | 0.2222 | +0.0000 | 0/0/6 | 6444 → 6900 | 242.7 → 233.8 |
| Field dictionary (prompt) | aiops2025 | 6 | 0.3667 | 0.3333 | -0.0333 | 0/1/5 | 6341 → 6797 | 256.3 → 270.7 |
| trace_only (selection) | aiops2022 | 6 | 0.2222 | 0.1667 | -0.0556 | 1/1/4 | 6444 → 6444 | 242.7 → 220.3 |
| trace_only (selection) | aiops2025 | 6 | 0.3667 | 0.3333 | -0.0333 | 1/1/4 | 6341 → 6341 | 256.3 → 209.8 |
| trace_graph (selection) | aiops2022 | 6 | 0.2222 | 0.1667 | -0.0556 | 1/1/4 | 6444 → 6444 | 242.7 → 268.3 |
| trace_graph (selection) | aiops2025 | 6 | 0.3667 | 0.3333 | -0.0333 | 1/1/4 | 6341 → 6341 | 256.3 → 336.8 |
| trace_logs_graph (selection) | aiops2022 | 6 | 0.2222 | 0.1667 | -0.0556 | 1/1/4 | 6444 → 6444 | 242.7 → 387.3 |
| trace_logs_graph (selection) | aiops2025 | 6 | 0.3667 | 0.2500 | -0.1167 | 1/1/4 | 6341 → 6341 | 256.3 → 250.5 |
| Trace routing / A (selection) | aiops2022 | 6 | 0.2222 | 0.1667 | -0.0556 | 1/1/4 | 6444 → 6444 | 216.2 → 221.5 |
| Trace routing / A (selection) | aiops2025 | 6 | 0.3667 | 0.5000 | +0.1333 | 1/0/5 | 6341 → 6341 | 254.2 → 231.8 |
| Reason-first / ranked_membership (prompt+schema order) | aiops2022 | 6 | 0.2222 | 0.0556 | -0.1667 | 0/1/5 | 6444 → 6444 | 216.2 → 221.8 |
| Reason-first / ranked_membership (prompt+schema order) | aiops2025 | 6 | 0.3667 | 0.2083 | -0.1583 | 1/1/4 | 6341 → 6341 | 254.2 → 232.0 |
| Reason-first / trace_strength_route (prompt+schema order) | aiops2022 | 6 | 0.1667 | 0.1667 | +0.0000 | 0/0/6 | 6444 → 6444 | 221.5 → 210.2 |
| Reason-first / trace_strength_route (prompt+schema order) | aiops2025 | 6 | 0.5000 | 0.3333 | -0.1667 | 0/1/5 | 6341 → 6341 | 231.8 → 236.3 |
| Resource slot replacement (selection) | aiops2022 | 6 | 0.2222 | 0.2083 | -0.0139 | 0/1/5 | 6444 → 6444 | 244.3 → 334.2 |
| Resource slot replacement (selection) | aiops2025 | 6 | 0.3667 | 0.1667 | -0.2000 | 0/2/4 | 6341 → 6341 | 287.7 → 265.7 |
| Node overview / A (selection) | aiops2022 | 6 | 0.2222 | 0.3750 | +0.1528 | 2/0/4 | 17754 → 17754 | 278.5 → 259.2 |
| Node overview / A (selection) | aiops2025 | 6 | 0.2000 | 0.2417 | +0.0417 | 1/1/4 | 17651 → 17651 | 250.2 → 310.3 |
| Zero-inclusive y-axis (encoding) | aiops2022 | 6 | 0.3750 | 0.3750 | +0.0000 | 0/0/6 | 17754 → 17754 | 259.2 → 264.8 |
| Zero-inclusive y-axis (encoding) | aiops2025 | 6 | 0.2417 | 0.2417 | +0.0000 | 0/0/6 | 17651 → 17651 | 310.3 → 262.2 |
| Trace routing / B (selection) | aiops2022 | 12 | 0.3403 | 0.2153 | -0.1250 | 0/3/9 | 6444 → 6444 | 268.8 → 216.9 |
| Trace routing / B (selection) | aiops2025 | 12 | 0.2986 | 0.3611 | +0.0625 | 1/0/11 | 6339 → 6339 | 266.1 → 231.8 |
| Node overview / B (selection) | aiops2022 | 12 | 0.3403 | 0.5375 | +0.1972 | 6/1/5 | 6444 → 17754 | 268.8 → 277.2 |
| Node overview / B (selection) | aiops2025 | 12 | 0.2986 | 0.3500 | +0.0514 | 3/2/7 | 6339 → 17649 | 266.1 → 273.8 |
| Typed owner in image (labels) | aiops2022 | 12 | 0.5375 | 0.5208 | -0.0167 | 2/1/9 | 17754 → 17754 | 277.2 → 255.0 |
| Typed owner in image (labels) | aiops2025 | 12 | 0.3500 | 0.4292 | +0.0792 | 1/1/10 | 17649 → 17649 | 273.8 → 270.6 |
| Balanced resource additions (selection) | aiops2022 | 12 | 0.5208 | 0.2736 | -0.2472 | 3/5/4 | 17754 → 17754 | 255.0 → 249.2 |
| Balanced resource additions (selection) | aiops2025 | 12 | 0.4292 | 0.3708 | -0.0583 | 1/4/7 | 17649 → 17649 | 270.6 → 245.7 |
| Larger owner label (labels) | aiops2022 | 12 | 0.5208 | 0.5069 | -0.0139 | 0/1/11 | 17754 → 17754 | 255.0 → 253.4 |
| Larger owner label (labels) | aiops2025 | 12 | 0.4292 | 0.4403 | +0.0111 | 1/0/11 | 17649 → 17649 | 270.6 → 254.3 |
| Whole-window guide (prompt) | aiops2022 | 12 | 0.5069 | 0.3986 | -0.1083 | 2/2/8 | 17754 → 17775 | 253.4 → 260.0 |
| Whole-window guide (prompt) | aiops2025 | 12 | 0.4403 | 0.4333 | -0.0069 | 0/1/11 | 17649 → 17670 | 254.3 → 290.1 |
| Unanchored timeline (time+encoding) | aiops2022 | 12 | 0.3986 | 0.3819 | -0.0167 | 4/3/5 | 17775 → 17775 | 260.0 → 262.2 |
| Unanchored timeline (time+encoding) | aiops2025 | 12 | 0.4333 | 0.5000 | +0.0667 | 3/1/8 | 17670 → 17670 | 290.1 → 262.8 |
| Trace count per exposure (projection+guide) | aiops2022 | 12 | 0.5069 | 0.4792 | -0.0278 | 1/1/10 | 17754 → 17877 | 253.4 → 260.2 |
| Trace count per exposure (projection+guide) | aiops2025 | 12 | 0.4403 | 0.4403 | +0.0000 | 0/0/12 | 17649 → 17772 | 254.3 → 246.4 |
| metz_overview (selection) | aiops2022 | 12 | 0.5069 | 0.3639 | -0.1431 | 3/4/5 | 17754 → 17754 | 253.4 → 281.9 |
| metz_overview (selection) | aiops2025 | 12 | 0.4403 | 0.2875 | -0.1528 | 1/5/6 | 17649 → 17649 | 254.3 → 256.7 |
| metz_coverage_overview (selection) | aiops2022 | 12 | 0.5069 | 0.3056 | -0.2014 | 1/5/6 | 17754 → 17754 | 253.4 → 263.3 |
| metz_coverage_overview (selection) | aiops2025 | 12 | 0.4403 | 0.2292 | -0.2111 | 0/6/6 | 17649 → 17649 | 254.3 → 243.4 |
| period (annotation) | aiops2022 | 12 | 0.5069 | 0.4514 | -0.0556 | 0/1/11 | 17754 → 17754 | 253.4 → 274.9 |
| period (annotation) | aiops2025 | 12 | 0.4403 | 0.4056 | -0.0347 | 1/1/10 | 17649 → 17649 | 254.3 → 244.5 |
| metric_facets (layout) | aiops2022 | 12 | 0.5069 | 0.4583 | -0.0486 | 1/2/9 | 17754 → 17754 | 253.4 → 282.6 |
| metric_facets (layout) | aiops2025 | 12 | 0.4403 | 0.3611 | -0.0792 | 0/2/10 | 17649 → 17649 | 254.3 → 253.5 |
| owner_groups (grouping) | aiops2022 | 12 | 0.5069 | 0.4792 | -0.0278 | 1/2/9 | 17754 → 17754 | 253.4 → 258.1 |
| owner_groups (grouping) | aiops2025 | 12 | 0.4403 | 0.2778 | -0.1625 | 1/3/8 | 17649 → 17649 | 254.3 → 245.6 |
| Observed-values only (fields+guide) | aiops2022 | 12 | 0.3819 | 0.3750 | -0.0069 | 1/1/10 | 17775 → 17725 | 262.2 → 274.1 |
| Observed-values only (fields+guide) | aiops2025 | 12 | 0.5000 | 0.4167 | -0.0833 | 0/1/11 | 17670 → 17620 | 262.8 → 266.6 |
| Typed candidate rows (candidate format) | aiops2022 | 12 | 0.5208 | 0.4514 | -0.0694 | 0/2/10 | 17754 → 17927 | 255.0 → 276.4 |
| Typed candidate rows (candidate format) | aiops2025 | 12 | 0.4292 | 0.4167 | -0.0125 | 1/2/9 | 17649 → 17777 | 270.6 → 410.9 |
| Native M24 / C (selection) | aiops2022 | 12 | 0.3542 | 0.4236 | +0.0694 | 5/2/5 | 17754 → 17754 | 271.4 → 252.1 |
| Native M24 / C (selection) | aiops2025 | 12 | 0.1944 | 0.2986 | +0.1042 | 3/2/7 | 17650 → 17650 | 244.6 → 261.2 |
| expanded_coverage24 (selection) | aiops2022 | 12 | 0.4236 | 0.2778 | -0.1458 | 3/6/3 | 17754 → 17754 | 252.1 → 253.1 |
| expanded_coverage24 (selection) | aiops2025 | 12 | 0.2986 | 0.2250 | -0.0736 | 1/3/8 | 17650 → 17650 | 261.2 → 253.1 |
| axis_span (encoding) | aiops2022 | 12 | 0.4236 | 0.4444 | +0.0208 | 2/2/8 | 17754 → 17754 | 252.1 → 259.0 |
| axis_span (encoding) | aiops2025 | 12 | 0.2986 | 0.2458 | -0.0528 | 1/4/7 | 17650 → 17650 | 261.2 → 248.8 |
| shape_diversity (selection) | aiops2022 | 12 | 0.4236 | 0.4792 | +0.0556 | 3/2/7 | 17754 → 17754 | 252.1 → 281.1 |
| shape_diversity (selection) | aiops2025 | 12 | 0.2986 | 0.2361 | -0.0625 | 1/3/8 | 17650 → 17650 | 261.2 → 317.7 |
| unpenalized (request) | aiops2022 | 12 | 0.4236 | 0.4333 | +0.0097 | 3/2/7 | 17754 → 17754 | 252.1 → 281.2 |
| unpenalized (request) | aiops2025 | 12 | 0.2986 | 0.2694 | -0.0292 | 1/2/9 | 17650 → 17650 | 261.2 → 302.9 |
| peer_shift (selection) | aiops2022 | 12 | 0.4236 | 0.3611 | -0.0625 | 3/5/4 | 17754 → 17754 | 252.1 → 274.8 |
| peer_shift (selection) | aiops2025 | 12 | 0.2986 | 0.3333 | +0.0347 | 2/2/8 | 17650 → 17650 | 261.2 → 248.0 |
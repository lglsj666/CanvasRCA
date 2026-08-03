# System

You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster. A fault has occurred in the system. Your task is to identify the root cause of the incident.

Root causes can occur at three levels:
- Pod level: a specific container replica (e.g., "cartservice-0")
- Service level: a microservice type (e.g., "paymentservice") — predict any pod of that service
- Node level: an infrastructure host (e.g., "node-6") — nodes appear as isolated entities with system metrics (CPU, memory, network, disk) but no application logs or traces

The system consists of multiple services communicating over HTTP/gRPC, running on shared infrastructure nodes. A fault in one component (pod, service, or node) can propagate to dependent components, causing them to appear degraded even though they are not the root cause.

Node-level faults (e.g., host memory exhaustion, CPU saturation, disk I/O) often manifest as correlated anomalies across multiple pods. If several unrelated pods show simultaneous degradation and a node shows critical system-level metrics, the node is likely the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS in downstream or co-located components.

# User

[image: dashboard.png]

Analyze this incident using only the supplied evidence. Rank the most likely
root-cause components, distinguishing the origin from propagated symptoms.

Evidence semantics shared by all representations:
- candidates are exhaustive and appear in a fixed alphabetical order;
- every metric has 64 equal-width bins from window start t=0; null means no
  observed sample in that bin and observed_count gives the number aggregated;
- shared_bin_centers_rel_s applies to all metric series; missing_mask_bits uses
  one bit per bin (1=missing, 0=observed); observed_counts_compact is either a
  comma-separated integer vector prefixed csv: or value*run pairs prefixed rle:;
- values_compact is lossless: raw: is a JSON vector, rle: is value*run pairs,
  and delta: stores the first observed value followed by cumulative deltas;
  missing_mask_bits restores null positions for delta encoding;
- signed_z is relative to the pre-incident baseline; onset and persistence are
  deterministic label-blind anomaly summaries;
- a directed edge A -> B means A calls B, so a disturbance in B can propagate
  back to A;
- propagation ranks are ordered by relative onset, not by causal likelihood;
- source t/trace and m/metric use different instruments and their z magnitudes
  must not be compared directly.


=== INCIDENT ===
schema_version: CanonicalEvidenceBundleV1
opaque_id: INC-C3A1CA82B407
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1493,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice metric=jvm_threads_state.BLOCKED baseline=0.0 peak=0.083333 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.083333,-0.083333
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=frontend-0 metric=container_cpu_cfs_throttled_seconds baseline=6.6e-05 peak=827.23184 signed_z=999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.001326,-0.001326,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.002996,597.117748,220.598649,9.512447
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=frontend-0 metric=container_cpu_user_seconds baseline=0.332 peak=26.42 signed_z=889.077 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0.385,-0.08,0.005,0.055,0.005,-0.08,0.075,-0.05,0.025,0.025,-0.065,-0.005,0,0.06,-0.04,-0.01,0.035,0.01,0.005,-0.035,-0.005,0.005,0.06,-0.08,-0.03,0.08,-0.02,-0.005,-0.01,0.055,-0.06,0,0,0.06,-0.02,-0.045,0.05,20.32,5.745,-3.615
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=frontend-0 metric=container_cpu_usage_seconds baseline=0.639501 peak=23.626229 signed_z=491.563 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:0.686357,-0.113462,0.038121,0.041815,-0.038638,-0.035892,0.122881,-0.096756,0.034264,0.094473,-0.13787,0.051167,0,0.095614,-0.152346,0.006306,0.038631,0.002621,0.001343,0.031719,-0.068054,-0.091675,0.208592,-0.12046,-0.08002,0.123228,-0.072149,0.065168,-0.02603,0.039025,0.011311,-0.087084,0.044647,0.057576,-0.027636,0.03451,-0.00872,17.909323,5.044329,-1.354292
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=frontend-0 metric=istio_request_duration_milliseconds.http.200. baseline=3979.5625 peak=87005.0 signed_z=417.068 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:3794,107.5,-211.5,267,96.5,-409.5,194.75,-33.5,542,-118.75,-168,160.25,0,-1.5,-75.25,-405.5,147,-62.5,158.5,56.25,-300.75,-43,201.5,-170,64.25,171,-418.5,494.75,-631.25,585,210,-333.75,214.5,-100.75,53.5,313.75,-178.5,27260,29653,25922.5
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=frontend-0 metric=container_memory_cache baseline=11980800.0 peak=36728832.0 signed_z=356.498 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:11980800,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,24748032,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=emailservice-0 metric=container_network_receive_MB.eth0 baseline=0.02538 peak=0.558573 signed_z=214.187 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.027278,0.000762,-0.002235,-0.004923,0.006484,-0.002092,-0.000693,0.003739,-0.006571,0.003108,-0.000345,0.003002,0,-0.003105,0.004062,-0.008644,0.008526,-0.003452,-0.00191,0.00196,-0.001103,0.003697,-0.004812,0.003782,-0.000454,-0.004705,0.537217,-0.531166,-0.002985,0.000117,0.003311,-0.002027,0.001166,-0.003954,0.006258,-0.009865,0.002871,0.003047,0.001098,-0.003244
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=frontend-0 metric=container_memory_failures.container.pgfault baseline=3186.125 peak=51158.5 signed_z=207.534 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:3344.5,-430.5,127.5,388.5,-217.5,-344.5,609,-475,221,476,-761.5,174.5,0,601,-701,77.5,45,-41.5,40.5,40.5,-134,-548.5,1267.5,-662,-622.5,663.5,-685,801,-357.5,427.5,67,-419.5,-48,424.5,-185.5,318,-26.5,47704.5,-47082,-2000
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=frontend-0 metric=container_memory_failures.hierarchy.pgfault baseline=3186.125 peak=51158.5 signed_z=207.534 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:3344.5,-430.5,127.5,388.5,-217.5,-344.5,609,-475,221,476,-761.5,174.5,0,601,-701,77.5,45,-41.5,40.5,40.5,-134,-548.5,1267.5,-662,-622.5,663.5,-685,801,-357.5,427.5,67,-419.5,-48,424.5,-185.5,318,-26.5,47704.5,-47082,-2000
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=frontend-0 metric=container_memory_usage_MB baseline=35.812988 peak=75.107422 signed_z=198.568 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:35.820312,0.080079,-0.535157,0.529297,-0.033203,-0.134766,-0.242187,0.279297,-0.25,0.544922,-0.140625,0.066406,0.025391,-0.228516,-0.037109,-0.044922,0.017578,0.095703,0.398438,-0.216797,-0.289063,0.021484,-0.236328,0.060547,0.238281,-0.126953,0.28711,-0.197266,0.058594,0.041015,0.007813,0.013672,-0.078125,-0.201172,0.019531,-0.013672,0.363282,36.773437,1.523438,0.847656
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=frontend-0 metric=container_memory_working_set_MB baseline=24.512207 peak=62.982422 signed_z=194.403 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:24.519531,0.080078,-0.535156,0.529297,-0.033203,-0.134766,-0.242187,0.279297,-0.25,0.544921,-0.140624,0.066406,0.02539,-0.228515,-0.03711,-0.044921,0.017578,0.095703,0.398437,-0.216797,-0.289062,0.021484,-0.236328,0.060547,0.238281,-0.126953,0.28711,-0.197266,0.058594,0.041015,0.007813,0.013672,-0.078125,-0.201172,0.019531,-0.013672,0.363281,35.949219,1.523438,0.847656
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=frontend-0 metric=container_memory_max_usage_MB baseline=39.503906 peak=145.230469 signed_z=182.717 onset_bin=62 onset_rel_s=2285.156 persistence_bins=2
values_compact=delta:39.503906,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,105.726563,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[2160.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":4900,"error_pct":9.01,"service":"adservice-0","total_logs":54384},{"error_logs":921,"error_pct":1.3,"service":"frontend-2","total_logs":70965},{"error_logs":816,"error_pct":1.3,"service":"frontend-0","total_logs":62841},{"error_logs":713,"error_pct":1.29,"service":"frontend-1","total_logs":55458}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":551.4,"error_pct":1.81,"p95_during_ms":299.4898,"p95_pre_ms":45.9774,"service":"frontend-0","spans":44752},{"delta_pct":26.7,"error_pct":0.0,"p95_during_ms":0.019,"p95_pre_ms":0.015,"service":"adservice-0","spans":2450},{"delta_pct":-24.4,"error_pct":0.0,"p95_during_ms":0.015,"p95_pre_ms":0.01984999999999991,"service":"adservice-2","spans":2449},{"delta_pct":-13.8,"error_pct":0.0,"p95_during_ms":2.9857,"p95_pre_ms":3.464699999999999,"service":"recommendationservice2-0","spans":3356},{"delta_pct":-11.0,"error_pct":0.0,"p95_during_ms":0.1255,"p95_pre_ms":0.141,"service":"paymentservice-2","spans":164},{"delta_pct":10.5,"error_pct":0.0,"p95_during_ms":0.021,"p95_pre_ms":0.019,"service":"adservice-1","spans":2450},{"delta_pct":-8.8,"error_pct":0.0,"p95_during_ms":0.01825,"p95_pre_ms":0.02,"service":"adservice2-0","spans":1407},{"delta_pct":-7.5,"error_pct":0.0,"p95_during_ms":0.2062,"p95_pre_ms":0.223,"service":"emailservice2-0","spans":93}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1320.0,"rank":1,"service":"shippingservice","severity_z":179.308},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":2,"service":"recommendationservice2","severity_z":61.726},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":3,"service":"paymentservice","severity_z":107.108},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":4,"service":"node-1","severity_z":67.064},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"currencyservice","severity_z":35.879},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":6,"service":"emailservice","severity_z":214.187},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":7,"service":"istio-egressgateway","severity_z":40.0},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":8,"service":"checkoutservice","severity_z":80.977},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":9,"service":"istio-ingressgateway","severity_z":41.667},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":10,"service":"recommendationservice","severity_z":35.613},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"cartservice2","severity_z":72.491},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":12,"service":"node-5","severity_z":69.046},{"evidence_source":"trace","onset_rel_s":2218.2,"rank":13,"service":"frontend","severity_z":11.873},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"adservice","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank recommendationservice2-0 first because recommendationservice2-0 has direct trace evidence; shippingservice-0 is second despite propagation rank 1 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["recommendationservice2-0","frontend-0","frontend-1","frontend-2","adservice-0"]}

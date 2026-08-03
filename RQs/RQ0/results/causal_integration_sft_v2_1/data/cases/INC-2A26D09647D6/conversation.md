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
opaque_id: INC-2A26D09647D6
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1549,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=cartservice-1 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.029439 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.029439,0,-0.029439,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=emailservice-1 metric=container_memory_usage_MB baseline=67.812402 peak=66.421875 signed_z=-999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:67.8125,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.001953,-0.001953,0,0,0,0,0,0,0,0,0,0,0,0,-0.019532,-0.496093,-0.622396,-0.111979,-0.136719,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=emailservice-1 metric=container_memory_working_set_MB baseline=62.253809 peak=61.585938 signed_z=-999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:62.253906,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.001953,-0.001953,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.226562,-0.3125,-0.054688,-0.070312,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=node-5 metric=system.disk.total baseline=4067313956.570001 peak=5144867840.0 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=5
values_compact=delta:4067313956.57,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1077553883.43,0,0,0,0,0,0,-1077553883.43,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=node-5 metric=system.disk.used baseline=3070479506.2855 peak=3940634112.0 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=5
values_compact=delta:3069122560,591579.43,172032,-528384,124635.43,281746.28,118491.43,179638.86,181394.28,188416,153600,262144,181394.29,104448,97426.29,143652.57,149796.57,-587190.86,268288,566418.29,100644.57,-70802.29,58514.29,79579.43,-318902.86,87478.86,27209.14,33938.29,58514.28,195730.29,28672,866893129.14,219904,350976,207104,240896,372736,296704,-869443364.57,113810.28
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=node-5 metric=system.fs.inodes.in_use baseline=0.98 peak=0.86 signed_z=-999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=5
values_compact=delta:0.98,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.12,0,0,0,0,0,0,0.12,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=node-5 metric=system.fs.inodes.used baseline=1465175.1495 peak=1756350.0 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:1465119.86,23,26.57,-22.72,11.72,2.57,1,-0.43,20.86,-2.86,2.86,9.71,12.86,5.71,-27,18.43,16.29,-51.14,2.85,17,4.57,0.58,-4.58,5.15,1.85,-6,4.29,1.43,6.86,-1.43,7.43,290993.71,1.5,31.88,46.62,-9.5,-4,82.5,-290975,-7.71
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=productcatalogservice-1 metric=container_fs_usage_MB./dev/vda1 baseline=29.097656 peak=629.6875 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:29.097656,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,600.589844,0,0,0,0,-600.585938,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-5 metric=system.net.tcp.out_segs baseline=370.8795 peak=8568.98 signed_z=534.818 onset_bin=54 onset_rel_s=1992.656 persistence_bins=6
values_compact=delta:431.92,-54.43,-1.3,-1.79,-2.37,-9.98,3.67,3.97,-0.72,-11.9,8.09,-7.55,18.34,-14.13,10.51,-12.35,9.94,-9.74,13.32,-7.89,6.7,-12.18,13.15,-16.35,27.69,-15.54,-0.31,-2.57,-3.94,2.54,3.87,616.18,5379.02,1721.69,-4042.44,2186.48,767.03,1572.35,-7001.52,-1205.38
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=recommendationservice-1 metric=container_memory_working_set_MB baseline=79.369922 peak=76.761719 signed_z=-510.603 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:79.347656,0.023438,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.03125,-0.015625,0,0,0,0,0,0,0,0.015625,0,0,0,-0.371094,-1.605469,-0.234375,-0.367187,0.103515,0.103516
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-5 metric=system.fs.inodes.total baseline=3096902904.686 peak=4046178048.0 signed_z=362.997 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:3101129581.71,-507026.28,-581924.57,458752,-395849.15,-1020489.14,-371565.71,-585728,-758052.57,-649216,-506441.15,-943250.28,-619081.15,-313344,-255414.85,-466066.29,-498834.28,2455552,-966948.58,-403748.57,-265947.43,392923.43,-403748.57,-209773.71,-368640,-253074.29,36864,-27501.71,-123172.57,-673792,-154770.29,954027776,-784896,-1282816,-738816,-863232,-1395968,-1091584,-952876653.71,-313344
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-5 metric=system.fs.inodes.free baseline=3095437780.1135 peak=4044421632.0 signed_z=362.888 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:3099664384,-506733.71,-582217.15,458752,-395849.14,-1020489.14,-371565.72,-585435.43,-758345.14,-649216,-506441.14,-942957.72,-619373.71,-313344,-255414.86,-466066.28,-498541.72,2455259.43,-966656,-404041.14,-265947.43,392923.43,-403748.57,-209773.72,-368347.43,-253074.28,36571.43,-27501.72,-123172.57,-673792,-154770.28,953736557.71,-784896,-1282816,-738816,-862976,-1396224,-1091584,-952585435.43,-313344
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1980.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":9,"error_pct":1.3,"service":"emailservice-0","total_logs":690},{"error_logs":5,"error_pct":0.75,"service":"emailservice-1","total_logs":669},{"error_logs":4,"error_pct":0.11,"service":"checkoutservice-0","total_logs":3759},{"error_logs":3,"error_pct":0.0,"service":"frontend-2","total_logs":77363},{"error_logs":3,"error_pct":0.08,"service":"checkoutservice-1","total_logs":3807},{"error_logs":2,"error_pct":0.0,"service":"frontend-1","total_logs":70138},{"error_logs":2,"error_pct":0.0,"service":"frontend-0","total_logs":113112},{"error_logs":2,"error_pct":0.31,"service":"emailservice-2","total_logs":643}],"mode":"errors","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":16.7,"error_pct":0.0,"p95_during_ms":0.17325000000000002,"p95_pre_ms":0.14844999999999997,"service":"paymentservice-0","spans":228},{"delta_pct":-8.8,"error_pct":0.0,"p95_during_ms":0.073,"p95_pre_ms":0.08,"service":"shippingservice-2","spans":1592},{"delta_pct":-7.8,"error_pct":0.0,"p95_during_ms":0.27880000000000005,"p95_pre_ms":0.30239999999999995,"service":"emailservice2-0","spans":82},{"delta_pct":-5.9,"error_pct":0.0,"p95_during_ms":0.111,"p95_pre_ms":0.118,"service":"currencyservice2-0","spans":6389},{"delta_pct":-4.5,"error_pct":0.0,"p95_during_ms":0.021,"p95_pre_ms":0.022,"service":"adservice-1","spans":3432},{"delta_pct":-3.5,"error_pct":0.0,"p95_during_ms":0.23119999999999996,"p95_pre_ms":0.23969999999999997,"service":"emailservice-1","spans":224},{"delta_pct":3.0,"error_pct":0.0,"p95_during_ms":0.02375,"p95_pre_ms":0.023049999999999952,"service":"adservice2-0","spans":1266},{"delta_pct":2.7,"error_pct":0.0,"p95_during_ms":0.2512,"p95_pre_ms":0.24455,"service":"emailservice-2","spans":227}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=12 omitted_edges=4
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"productcatalogservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"redis-cart2","severity_z":62.091},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":3,"service":"frontend2","severity_z":133.83},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":4,"service":"shippingservice","severity_z":101.403},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":5,"service":"checkoutservice2","severity_z":72.985},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":6,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":7,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":8,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":9,"service":"recommendationservice","severity_z":510.603},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":10,"service":"frontend","severity_z":209.023},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":11,"service":"checkoutservice","severity_z":164.171},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":12,"service":"recommendationservice2","severity_z":144.517},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":13,"service":"adservice","severity_z":78.968},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"istio-egressgateway","severity_z":90.909}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"checkoutservice2","caller":"frontend2"},{"callee":"recommendationservice2","caller":"frontend2"},{"callee":"productcatalogservice","caller":"recommendationservice"},{"callee":"productcatalogservice","caller":"recommendationservice2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice-1 first because productcatalogservice-1 has direct container_fs_usage_MB./dev/vda1 evidence (signed-z 999, persistence 3 bins); although recommendationservice-0 is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["productcatalogservice-1","node-5","emailservice-1","recommendationservice-1","cartservice-1"]}

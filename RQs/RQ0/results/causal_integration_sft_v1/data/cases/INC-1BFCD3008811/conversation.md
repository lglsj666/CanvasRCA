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
opaque_id: INC-1BFCD3008811
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1514,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=jvm_threads_started baseline=0.0 peak=0.916667 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=6
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.083333,0.833334,-0.916667,0,0,0,0,0.166667,0.666666,-0.833333,0,0,0,0.583333,-0.166666
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=currencyservice-2 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.028 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.028,-0.014,-0.014,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=frontend-0 metric=istio_request_duration_milliseconds.http.202. baseline=2.99 peak=16507.5 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=8
values_compact=delta:3.675,0,-1.05,1.05,-1.05,0.525,0,-0.525,3.15,-2.65,-0.525,0.025,-2.1,1.05,1.05,2.1,-3.15,1.05,-0.525,2.625,9042.775,7277.5,-527.5,355,177.5,177.5,-710,-355,-7272.775,-8165,-3.15,0.525,0.525,16.975,-17.5,1.575,-1.05,-0.525,3.15,-4.725
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=frontend-1 metric=istio_request_duration_milliseconds.http.202. baseline=0.91875 peak=11005.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=7
values_compact=delta:0,1.05,-0.525,0,-0.525,0,0,1.05,1.05,-2.1,0,1.05,2.625,-2.1,-1.05,0.525,-0.525,0.525,1.05,-0.525,4970,6033.425,-1597.5,1062.5,-1775,2.5,-177.5,1597.5,-4883.425,-5230.4,-3.675,1.575,-1.05,-0.525,0,1.05,-0.525,0,0.525,-1.05
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=frontend-2 metric=istio_request_duration_milliseconds.http.202. baseline=0.86375 peak=17217.5 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=10
values_compact=delta:1.05,0,0.525,0.525,-1.575,0.525,0.525,-1.05,0.5,0,-1.025,0,0,0.525,1.05,-1.05,0,0,0,1.05,4253.95,12069.475,-350,-1242.5,2485,-1952.5,177.5,-532.5,-3905,-10827.5,-177.5,1.05,0,2.1,0,-1.05,-0.525,-0.025,0,-1.025
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=frontend2-0 metric=istio_request_duration_milliseconds.http.202. baseline=1.69375 peak=17217.5 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=7
values_compact=delta:3.15,-2.625,2.075,-0.05,0.025,-1,1.05,-2.625,0,0.525,3.15,-1.575,-1.05,-0.525,2.1,-2.625,0.525,1.525,1.575,-2.05,8163.95,9051.975,-710,-1952.5,1597.5,-177.5,-355,1420,-9407.5,-7632.5,0,0.525,1.575,-1.575,0,0,0,2.05,-1,0.525
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=checkoutservice-0 metric=container_memory_usage_MB baseline=127.96237 peak=104.603516 signed_z=-655.821 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:127.910156,0.044922,-0.03125,0.0625,0.001953,0.001302,0.006511,0,-0.05599,0.05599,-0.035156,0.033203,-0.087891,0.083333,0.006511,-0.123047,0.095703,0.011719,-0.017578,-0.029297,0.060547,-0.13086,0.042969,0.023438,-0.027344,-23.298828,23.388672,-0.058594,0.0625,-0.010417,-0.001302,-0.101563,0.115235,-0.03125,-0.072266,0.066407,-0.042969,-0.003907,0.035157,0.019531
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=frontend2-0 metric=istio_request_duration_milliseconds.http.200. baseline=1607.4125 peak=82125.0 signed_z=584.883 onset_bin=36 onset_rel_s=1334.531 persistence_bins=7
values_compact=delta:1710.5,110.5,-251.5,-96.25,-124,361.25,-85,35.75,-172.75,385.5,-124.75,-50.75,-235.25,52,181.5,-202.75,224.25,-314.75,134,51.25,33917,43419.25,-9125,3575,1575,5175,-11925,13925,-42623,-37941.25,49.75,-163.5,4.5,222.25,-131.25,-69.5,87.25,66.5,-6.75,-88.25
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=adservice2 metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=39.31287 peak=39.506004 signed_z=584.549 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:39.312042,0.000036,0.000163,0.000353,0.000432,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000021,0.00004,0.000036,0.000056,0.000031,0,0,0,0,0,0,0,0.000431,0.000359,0.000011,0,0,0,0.000053,0.159959,0.031981
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=41222527.833333 peak=41425048.0 signed_z=577.139 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:41221664,32,160,332.666667,507.333333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,16,48,32,58.666667,37.333333,0,0,0,0,0,0,0,393.333333,436,10.666667,0,0,0,56,150962,50302
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=adservice2 metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=41222527.833333 peak=41425048.0 signed_z=577.139 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:41221664,32,160,332.666667,507.333333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,16,48,32,58.666667,37.333333,0,0,0,0,0,0,0,388,441.333333,10.666667,0,0,0,56,150962,50302
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=adservice2 metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=98.519309 peak=98.712448 signed_z=575.677 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:98.518486,0.000025,0.000158,0.000312,0.000489,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000015,0.000046,0.000031,0.000056,0.000035,0,0,0,0,0,0,0,0.00037,0.000416,0.000015,0,0,0,0.000045,0.143977,0.047972
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1740.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1,"error_pct":0.01,"service":"cartservice-1","total_logs":10344}],"mode":"errors","omitted_services":30,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":7827.2,"error_pct":0.0,"p95_during_ms":3925.6673,"p95_pre_ms":49.52135,"service":"frontend-1","spans":5040},{"delta_pct":6025.6,"error_pct":0.0,"p95_during_ms":2905.9279,"p95_pre_ms":47.439149999999984,"service":"frontend2-0","spans":15557},{"delta_pct":6005.8,"error_pct":0.0,"p95_during_ms":3050.711699999994,"p95_pre_ms":49.96434999999997,"service":"frontend-0","spans":15373},{"delta_pct":5813.7,"error_pct":0.0,"p95_during_ms":2970.792850000003,"p95_pre_ms":50.235499999999995,"service":"frontend-2","spans":15106},{"delta_pct":251.3,"error_pct":0.0,"p95_during_ms":0.5427999999999996,"p95_pre_ms":0.1545,"service":"paymentservice-2","spans":43},{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice-1","spans":2142},{"delta_pct":24.7,"error_pct":0.0,"p95_during_ms":0.02169999999999999,"p95_pre_ms":0.017399999999999978,"service":"adservice-1","spans":647},{"delta_pct":17.5,"error_pct":0.0,"p95_during_ms":0.09284999999999986,"p95_pre_ms":0.079,"service":"shippingservice-0","spans":301}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":1194.6,"rank":1,"service":"frontend","severity_z":774.749},{"evidence_source":"trace","onset_rel_s":1194.6,"rank":2,"service":"frontend2","severity_z":910.434},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"recommendationservice","severity_z":61.418},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"cartservice","severity_z":110.36},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":5,"service":"shippingservice2","severity_z":60.46},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"emailservice","severity_z":159.293},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"checkoutservice","severity_z":655.821},{"evidence_source":"trace","onset_rel_s":1535.4,"rank":8,"service":"adservice2","severity_z":19.208},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":9,"service":"adservice","severity_z":105.801},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":10,"service":"redis-cart2","severity_z":88.612},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"node-3","severity_z":81.846},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":12,"service":"paymentservice2","severity_z":99.328},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":13,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":14,"service":"shippingservice","severity_z":158.198}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"shippingservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank frontend-0 first because frontend-0 has direct istio_request_duration_milliseconds.http.202. evidence (signed-z 999, persistence 8 bins); frontend2-0 is second despite propagation rank 2 because onset ordering alone does not establish the causal origin.","services":["frontend-0","frontend2-0"]}

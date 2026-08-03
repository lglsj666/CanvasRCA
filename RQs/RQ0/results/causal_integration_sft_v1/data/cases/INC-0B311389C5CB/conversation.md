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
opaque_id: INC-0B311389C5CB
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1553,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=42687054.933333 peak=42888680.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:42686912,0,0,0,0,0,10.666667,53.333333,0,0,0,0,10.666667,58.666666,58.666667,144,112,0,0,0,0,0,0,9.333333,177.333334,69.333333,183370.666667,17686.666666,6.666667,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=42687046.133333 peak=42888680.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:42686912,0,0,0,0,0,0,53.333333,10.666667,0,0,0,0,48,58.666667,69.333333,202.666667,5.333333,0,0,0,0,0,0,112,133.333333,116486,84343.333334,245.333333,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice2 metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=42687053.866667 peak=42888680.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:42686912,0,0,0,0,0,10.666667,53.333333,0,0,0,0,5.333333,64,58.666667,128,128,0,0,0,0,0,0,9.333333,177.333334,69.333333,183258,17799.333333,6.666667,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice2 metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=40.709548 peak=40.901833 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:40.709412,0,0,0,0,0,0.000015,0.000046,0,0,0,0,0.00001,0.000056,0.000056,0.000142,0.000102,0,0,0,0,0,0,0.000009,0.000178,0.000057,0.190744,0.001002,0.000004,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice2 metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=99.91599 peak=100.108276 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:99.915855,0,0,0,0,0,0.000011,0.00005,0,0,0,0,0.000006,0.000055,0.000062,0.000122,0.000122,0,0,0,0,0,0,0,0.000178,0.000066,0.174768,0.016975,0.000006,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=paymentservice-2 metric=container_cpu_system_seconds baseline=0.0 peak=0.005 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.005,0,-0.005,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=frontend-0 metric=istio_request_duration_milliseconds.http.302. baseline=8.9425 peak=4575.0 signed_z=715.086 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:10.5,5.525,-10.45,10.175,-10.5,5.025,0,-0.5,0,0,0,0.725,0,10.5,-21,22,-22,1.05,0,-1.05,4575,-3050,-1525,9.775,0,-4.525,11.5,-12.225,10.5,-11,9.05,-7.825,11.5,-7.7,0,1.225,0,0.725,0,-1.95
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=adservice metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=38.502022 peak=38.694649 signed_z=690.76 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:38.501094,0.000513,0.000148,0.000163,0.000081,0.00003,0,0,0,0,0,0,0.000026,0.000056,0.000102,0,0.000061,0.000061,0,0,0,0,0,0.016007,0.175799,0.000126,0,0.00001,0.000082,0.000056,0.000081,0.000015,0,0,0,0.000032,0.000106,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=adservice metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=40372291.933333 peak=40574280.0 signed_z=674.438 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:40371290.666667,549.333333,164,177.333333,90.666667,32,0,0,0,0,0,0,21.333333,58.666667,106.666667,5.333333,58.666667,69.333333,0,0,0,0,0,46.666667,201060,149.333333,0,10.666667,80,64,80,21.333333,0,0,0,26.666667,117.333333,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=40372292.2 peak=40574280.0 signed_z=674.247 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:40371290.666667,549.333333,164,177.333333,90.666667,32,0,0,0,0,0,0,21.333333,64,101.333334,5.333333,58.666667,69.333333,0,0,0,0,0,46.666667,201060,149.333333,0,10.666667,80,64,80,21.333333,0,0,0,26.666667,117.333333,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=adservice metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=98.171427 peak=98.364059 signed_z=671.789 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:98.170469,0.000524,0.000161,0.000164,0.000087,0.000035,0,0,0,0,0,0,0.00002,0.000056,0.000102,0.000005,0.000051,0.000071,0,0,0,0,0,0.000036,0.191755,0.000136,0.000006,0.00001,0.000076,0.000056,0.000082,0.00002,0,0,0,0.00002,0.000117,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=40372265.0 peak=40574280.0 signed_z=603.304 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:40371173.333333,474.666667,314.666667,169.333333,108,64,0,0,0,0,0,0,0,64,96,32,32,80,16,0,0,0,0,0,134085.333333,67144,26.666667,0,58.666667,69.333333,85.333333,42.666667,0,0,0,0,117.333333,26.666667,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1500.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-46.2,"n_during":56,"n_pre":104,"service":"emailservice-2"},{"change_pct":-43.6,"n_during":5643,"n_pre":10008,"service":"frontend-2"},{"change_pct":-42.5,"n_during":758,"n_pre":1318,"service":"adservice-2"},{"change_pct":-41.9,"n_during":320,"n_pre":551,"service":"checkoutservice-0"},{"change_pct":-41.5,"n_during":1224,"n_pre":2091,"service":"recommendationservice-1"},{"change_pct":-41.4,"n_during":588,"n_pre":1004,"service":"adservice-0"},{"change_pct":-41.3,"n_during":1227,"n_pre":2091,"service":"recommendationservice-0"},{"change_pct":-41.2,"n_during":590,"n_pre":1004,"service":"adservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":22.1,"error_pct":0.0,"p95_during_ms":0.307,"p95_pre_ms":0.25145,"service":"emailservice-1","spans":53},{"delta_pct":19.1,"error_pct":0.0,"p95_during_ms":195.5295,"p95_pre_ms":164.22409999999996,"service":"checkoutservice-0","spans":614},{"delta_pct":17.0,"error_pct":0.0,"p95_during_ms":0.02,"p95_pre_ms":0.017099999999999966,"service":"adservice-1","spans":795},{"delta_pct":15.7,"error_pct":0.0,"p95_during_ms":0.09309999999999993,"p95_pre_ms":0.0805,"service":"shippingservice-1","spans":370},{"delta_pct":11.8,"error_pct":0.0,"p95_during_ms":0.019,"p95_pre_ms":0.017,"service":"adservice-0","spans":795},{"delta_pct":-7.5,"error_pct":0.0,"p95_during_ms":4.816299999999999,"p95_pre_ms":5.207,"service":"productcatalogservice-1","spans":7409},{"delta_pct":-7.4,"error_pct":0.0,"p95_during_ms":4.67605,"p95_pre_ms":5.0484,"service":"productcatalogservice-2","spans":7407},{"delta_pct":-6.7,"error_pct":0.0,"p95_during_ms":4.763999999999999,"p95_pre_ms":5.107749999999999,"service":"productcatalogservice2-0","spans":4537}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"frontend","severity_z":715.086},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":3,"service":"cartservice","severity_z":135.264},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"currencyservice","severity_z":104.577},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":5,"service":"redis-cart","severity_z":46.349},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"adservice","severity_z":690.76},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"recommendationservice","severity_z":44.61},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":8,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":9,"service":"paymentservice2","severity_z":215.383},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":10,"service":"checkoutservice","severity_z":48.263},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":11,"service":"istio-ingressgateway","severity_z":114.893},{"evidence_source":"trace","onset_rel_s":2218.2,"rank":12,"service":"shippingservice","severity_z":12.623},{"evidence_source":"trace","onset_rel_s":2315.4,"rank":13,"service":"emailservice","severity_z":3.058},{"evidence_source":"metric","onset_rel_s":2340.0,"rank":14,"service":"node-6","severity_z":140.044}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"currencyservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

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
opaque_id: INC-1973E78585A1
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1498,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=50023417.6 peak=50427872.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:50023408,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,64,0,0,0,0,0,0,0,213.333333,42.666667,134989.333333,67482.666667,213.333333,167509.333334,33503.333333,110,218.666667,53.333333,0,0,26.666667,37.333333,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=50023416.266667 peak=50427872.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:50023408,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,37.333333,26.666667,0,0,0,0,0,0,128,128,67498.666667,134973.333333,122.666667,100613.333333,100480,90,158,138.666667,5.333333,0,5.333333,58.666667,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice2 metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=50023417.6 peak=50427872.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:50023408,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,64,0,0,0,0,0,0,0,213.333333,42.666667,134989.333333,67482.666667,208,167514.666667,33503.333333,110,218.666667,53.333333,0,0,26.666667,37.333333,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice2 metric=java_lang_Memory_ObjectPendingFinalizationCount baseline=0.0 peak=2.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,-2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice2 metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=47.706049 peak=48.091766 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:47.706039,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000061,0,0,0,0,0,0,0,0.000204,0.000046,0.144816,0.048271,0.000203,0.175721,0.01598,0.000119,0.000194,0.000051,0,0,0.000026,0.000035,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=adservice2 metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=106.355165 peak=106.740883 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:106.355156,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.000056,0.000005,0,0,0,0,0,0,0.000183,0.000061,0.128736,0.064356,0.000184,0.159769,0.031942,0.000114,0.000204,0.000056,0,0,0.00002,0.000041,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=recommendationservice-0 metric=container_cpu_usage_seconds baseline=0.224086 peak=24.569464 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=5
values_compact=delta:0.212084,0.013006,0.009855,-0.050015,0.04648,0.005378,-0.021101,0.017197,-0.02162,0.003971,0.030102,-0.029909,0.017886,0,0.024209,-0.029332,-0.020163,0.019318,0.013617,-0.048997,0.04142,-0.005633,0.010492,11.849892,11.671748,0.404201,-1.184966,1.590344,-1.218862,-18.698827,-4.438366,-0.016,0.029702,-0.018347,0.002637,0.019917,-0.000107,-0.02371,0.021565,-0.014274
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=recommendationservice-0 metric=container_cpu_user_seconds baseline=0.17925 peak=27.245 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=5
values_compact=delta:0.165,0.015,0.005,-0.04,0.04,0.01,-0.025,0.025,-0.025,0.01,0.015,-0.015,0.005,0,0.02,-0.025,-0.01,0,0.015,-0.025,0.025,-0.005,0.01,12.43,12.415,1.24,-0.745,1.715,-1.415,-20.865,-4.79,-0.025,0.04,-0.015,-0.015,0.03,0.01,-0.03,0.02,-0.015
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=recommendationservice-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=recommendationservice-0 metric=container_fs_writes./dev/vda baseline=0.0 peak=9.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,9,-9,0,0,0,1.5,0,-1.5,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=recommendationservice-0 metric=container_fs_writes_MB./dev/vda baseline=0.0 peak=0.085938 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.085938,-0.085938,0,0,0,0.013672,0,-0.013672,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=recommendationservice-0 metric=container_memory_failures.container.pgmajfault baseline=0.0 peak=66.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,66,-66,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1560.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-56.2,"n_during":833,"n_pre":1901,"service":"checkoutservice-2"},{"change_pct":-55.1,"n_during":851,"n_pre":1897,"service":"checkoutservice-0"},{"change_pct":-55.1,"n_during":155,"n_pre":345,"service":"paymentservice-0"},{"change_pct":-54.8,"n_during":156,"n_pre":345,"service":"paymentservice-1"},{"change_pct":-54.0,"n_during":150,"n_pre":326,"service":"emailservice-1"},{"change_pct":-53.9,"n_during":152,"n_pre":330,"service":"emailservice-0"},{"change_pct":-53.7,"n_during":873,"n_pre":1887,"service":"checkoutservice-1"},{"change_pct":-53.5,"n_during":10843,"n_pre":23303,"service":"currencyservice-2"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":396.8,"error_pct":0.0,"p95_during_ms":497.43535,"p95_pre_ms":100.1294,"service":"recommendationservice2-0","spans":4880},{"delta_pct":104.0,"error_pct":0.0,"p95_during_ms":203.11605,"p95_pre_ms":99.56599999999999,"service":"recommendationservice-2","spans":5888},{"delta_pct":103.7,"error_pct":0.0,"p95_during_ms":202.83085,"p95_pre_ms":99.596,"service":"recommendationservice-0","spans":5890},{"delta_pct":102.5,"error_pct":0.0,"p95_during_ms":201.59014999999997,"p95_pre_ms":99.54,"service":"recommendationservice-1","spans":5888},{"delta_pct":-8.2,"error_pct":0.0,"p95_during_ms":0.15859999999999996,"p95_pre_ms":0.1727999999999999,"service":"paymentservice-1","spans":165},{"delta_pct":-5.2,"error_pct":0.0,"p95_during_ms":0.26080000000000003,"p95_pre_ms":0.275,"service":"emailservice-2","spans":164},{"delta_pct":-4.8,"error_pct":0.0,"p95_during_ms":0.2643,"p95_pre_ms":0.27775000000000005,"service":"emailservice2-0","spans":133},{"delta_pct":-4.6,"error_pct":0.0,"p95_during_ms":0.26594999999999996,"p95_pre_ms":0.27879999999999994,"service":"emailservice-0","spans":165}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"node-1","severity_z":151.596},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":2,"service":"emailservice","severity_z":259.961},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":3,"service":"shippingservice","severity_z":125.882},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":4,"service":"cartservice","severity_z":125.457},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":5,"service":"adservice","severity_z":114.412},{"evidence_source":"trace","onset_rel_s":1584.6,"rank":6,"service":"recommendationservice","severity_z":4.358},{"evidence_source":"trace","onset_rel_s":1584.6,"rank":7,"service":"recommendationservice2","severity_z":14.546},{"evidence_source":"trace","onset_rel_s":1584.6,"rank":8,"service":"paymentservice","severity_z":40.471},{"evidence_source":"trace","onset_rel_s":1584.6,"rank":9,"service":"frontend","severity_z":5.435},{"evidence_source":"trace","onset_rel_s":1584.6,"rank":10,"service":"frontend2","severity_z":13.947},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":12,"service":"node-4","severity_z":85.652},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":13,"service":"node-2","severity_z":64.233},{"evidence_source":"metric","onset_rel_s":2280.0,"rank":14,"service":"checkoutservice","severity_z":120.591}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"recommendationservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-1 first because node-1 has metric evidence at propagation rank 1; emailservice-0 is second despite propagation rank 2 because onset ordering alone does not establish the causal origin.","services":["node-1","emailservice-0"]}

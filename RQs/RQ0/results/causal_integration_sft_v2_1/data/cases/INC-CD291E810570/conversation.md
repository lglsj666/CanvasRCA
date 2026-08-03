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
opaque_id: INC-CD291E810570
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1602,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=41394891.466667 peak=41604074.0 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:41394800,0,0,0,32,32,0,0,0,0,0,0,0,26.666667,37.333333,0,0,0,0,426.666667,117.333333,1640,2304,0,288,950.666667,177.333333,282.666667,69.333333,200872,64,48,0,60,84,21.333333,42.666667,10.666667,128,1559.333333
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=41394880.8 peak=41603419.333333 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:41394800,0,0,0,10.666667,53.333333,0,0,0,0,0,0,0,5.333333,58.666667,0,0,0,0,256,256,394.666667,3538.666666,42.666667,0,1012,270.666667,352,133.333333,133904,67010.666667,64,5.333333,12,132,0,58.666667,5.333333,72,971.333333
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=41394891.466667 peak=41604074.0 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:41394800,0,0,0,32,32,0,0,0,0,0,0,0,26.666667,37.333333,0,0,0,0,426.666667,117.333333,1640,2304,0,288,950.666667,177.333333,282.666667,69.333333,200872,64,48,0,60,84,16,48,10.666667,118.666666,1568.666667
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=39.477245 peak=39.676886 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:39.477158,0,0,0,0.000035,0.000026,0,0,0,0,0,0,0,0.000025,0.000036,0,0,0,0,0.000407,0.000111,0.001825,0.001937,0,0.000274,0.000915,0.000161,0.00028,0.016018,0.175609,0.000056,0.000046,0,0.000057,0.00008,0.000021,0.00004,0.000016,0.000117,0.001636
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=99.146653 peak=99.346148 signed_z=999.0 onset_bin=31 onset_rel_s=1151.719 persistence_bins=21
values_compact=delta:99.146568,0,0,0,0.000031,0.00003,0,0,0,0,0,0,0,0.000021,0.00004,0,0,0,0,0.000367,0.000122,0.001569,0.002222,0,0.000184,0.000998,0.000143,0.000295,0.000067,0.191566,0.000056,0.000051,0,0.000057,0.00008,0.000015,0.000046,0.00001,0.000105,0.001505
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=cartservice-0 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=37.614375 peak=69889.2 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:34.3875,-0.7875,2.3625,-2.8875,17.75,0,-13.0375,-2.1,1.325,-1.05,2.3625,-2.1,0,0.2625,-0.3125,0.8375,-0.025,3.175,-2.625,-5.5125,69857.175,-69889.2,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101011111111110100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=cartservice-1 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=36.201875 peak=69254.5625 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=9
values_compact=delta:33.3375,1.05,0.525,-1.3125,1.575,1.575,1.05,-2.1,0.7875,0.25,0.7875,0.0125,-2.1125,1.05,-2.1,3.9375,1,-0.2625,-0.2,-6.5625,69222.275,-68923.2375,-304.8125,4.725,-3.4125,2.8125,0.3375,-1.075,0.025,1.05,-2.625,0,0.2625,0.4625
missing_mask_bits=0010010100101001010010010100101011111111110100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=cartservice-2 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=38.181875 peak=51631.425 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=4
values_compact=delta:44.9875,-11.7125,4.45,-2.65,2.6375,2.85,-1.7875,-2.075,2.7875,-2.2875,2.325,-1.275,-1.2875,2.775,-2.55,1.1,-1.575,5.6625,-1.7625,-8.125,51598.9375,-51608.9125,5.8125,3.325,1.2625,-3.325,2.875,-0.5,-0.5125,2.75,-4.3,12.825,-0.1875,-13.1625
missing_mask_bits=0010010100101001010010010100101011111111110100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=cartservice2-0 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.090581 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.090581,-0.090581,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=cartservice2-0 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=34.32375 peak=63017.275 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:32.5375,1.5375,-1.5625,-1.275,1.3,-0.05,2.1375,-5.25,2.3875,-1.3125,5.775,1.8375,1.3125,-6.825,5.5125,-2.1,5.25,-2.1,-2.3625,-9.1875,62989.7125,-62984.4625,11.8125,-8.4,2.625,0.2375,-1.2875,-1.85,-2.1,3.1625,3.125,-0.2375,1.3125,-0.2625
missing_mask_bits=0010010100101001010010010100101011111111110100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,0,0,0,0,0,0,0,0,0,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=checkoutservice-0 metric=istio_request_bytes.grpc.200.13.0 baseline=0.0 peak=1570.0 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,785,-785,0,1177.5,-785,0,785,0,-785,0,0,0,1177.5,-785,0,392.5
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=checkoutservice-0 metric=istio_request_duration_milliseconds.grpc.200.13.0 baseline=0.0 peak=11750.0 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5950,-5950,0,8675,-5650,-100,5850,100,-5950,50,0,0,8775,-6000,50,3125
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1680.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1442,"error_pct":4.44,"service":"cartservice-0","total_logs":32450},{"error_logs":298,"error_pct":0.62,"service":"frontend-2","total_logs":47782},{"error_logs":228,"error_pct":0.62,"service":"frontend-0","total_logs":36997},{"error_logs":209,"error_pct":0.62,"service":"frontend-1","total_logs":33595},{"error_logs":34,"error_pct":0.13,"service":"cartservice-1","total_logs":26093},{"error_logs":12,"error_pct":0.05,"service":"cartservice-2","total_logs":25974}],"mode":"errors","omitted_services":25,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":11387.2,"error_pct":0.0,"p95_during_ms":5893.2005,"p95_pre_ms":51.30215000000001,"service":"frontend-1","spans":23497},{"delta_pct":11210.7,"error_pct":0.0,"p95_during_ms":5896.566,"p95_pre_ms":52.1326,"service":"frontend-2","spans":33607},{"delta_pct":11210.2,"error_pct":0.0,"p95_during_ms":5889.6515,"p95_pre_ms":52.07379999999998,"service":"frontend-0","spans":25960},{"delta_pct":8988.7,"error_pct":0.0,"p95_during_ms":5996.37825,"p95_pre_ms":65.97625,"service":"checkoutservice-1","spans":1112},{"delta_pct":7561.3,"error_pct":0.0,"p95_during_ms":5943.7068,"p95_pre_ms":77.5805,"service":"checkoutservice-2","spans":1136},{"delta_pct":5818.2,"error_pct":0.0,"p95_during_ms":5953.29965,"p95_pre_ms":100.5932499999995,"service":"checkoutservice-0","spans":1144},{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":306.0,"service":"cartservice-1","spans":5140},{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":247.9499999999989,"service":"cartservice2-0","spans":5516}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":1260.0,"rank":1,"service":"node-3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":2,"service":"paymentservice","severity_z":106.384},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":3,"service":"checkoutservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"frontend2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"node-4","severity_z":52.092},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"emailservice","severity_z":132.039},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"node-2","severity_z":52.385},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":8,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"cartservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"adservice2","severity_z":72.207},{"evidence_source":"trace","onset_rel_s":1681.8,"rank":11,"service":"frontend","severity_z":4.446},{"evidence_source":"trace","onset_rel_s":1681.8,"rank":12,"service":"shippingservice","severity_z":15.656},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":13,"service":"adservice","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1779.6,"rank":14,"service":"checkoutservice","severity_z":4.093}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"cartservice2","caller":"frontend2"},{"callee":"checkoutservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank cartservice-0 first because cartservice-0 has direct istio_request_duration_milliseconds.grpc.200.0.0 evidence (signed-z 999, persistence 13 bins); although frontend-0 is salient, the caller path frontend -> cartservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["cartservice-0","node-3","paymentservice-0","checkoutservice2-0","frontend2-0"]}

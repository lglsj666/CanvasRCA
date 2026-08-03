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
opaque_id: INC-1C12DC0390F8
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1475,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=55486112.0 peak=55689344.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:55486008,0,0,0,0,0,0,0,0,69.333333,117.333334,5.333333,0,0,0,0,0,0,0,96,96,21.333333,101.333334,5.333333,0,0,234.666667,21.333333,64,1288,792,74.666667,83043.333333,117306,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice2 metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=55486105.333333 peak=55689344.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:55486008,0,0,0,0,0,0,0,0,21.333333,138.666667,32,0,0,0,0,0,0,0,37.333333,133.333334,21.333333,90.666667,37.333333,0,0,144,112,0,528,1616,32,16670.666667,183254.666666,466.666667,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice2 metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=55486112.0 peak=55689344.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:55486008,0,0,0,0,0,0,0,0,69.333333,117.333334,5.333333,0,0,0,0,0,0,0,96,96,16,106.666667,5.333333,0,0,234.666667,21.333333,64,1130.666667,949.333333,74.666667,83043.333333,117306,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice2 metric=jvm_classes_loaded baseline=5163.0 peak=0.0 signed_z=-999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:5163,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-5163,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice2 metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=52.915681 peak=53.109497 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:52.915581,0,0,0,0,0,0,0,0,0.000071,0.000112,0,0,0,0,0,0,0,0.000005,0.000086,0.000092,0.00002,0.000097,0.000005,0,0.000015,0.000209,0.00002,0.000061,0.001234,0.00075,0.000081,0.094993,0.096065,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=adservice2 metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=133.915267 peak=134.109085 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:133.915169,0,0,0,0,0,0,0,0,0.000061,0.000117,0.000005,0,0,0,0,0,0,0,0.000081,0.000102,0.000015,0.000102,0.000005,0,0,0.000219,0.000025,0.000046,0.001094,0.000905,0.000071,0.079085,0.111983,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=adservice2 metric=jvm_threads_started baseline=0.0 peak=0.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.583333,-0.166666,-0.416667,0.333333,0.333334,-0.666667,0,0,0,0,0,0,0,0,0.25,0.5,-0.75
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=adservice metric=jvm_classes_loaded baseline=5181.0 peak=0.0 signed_z=-999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=10
values_compact=delta:5181,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-5181,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=node-5 metric=system.disk.free baseline=1000377870.6285 peak=1220760832.0 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:1000634075.43,-36864,-84041.14,-48128,-40521.15,57344,-33280,-58075.43,-32256,18066.29,41910.86,-37010.29,-38326.86,-63195.42,60342.85,-34889.14,-26477.71,-91062.86,-51419.43,61952,-41398.86,-28013.71,-47177.14,41033.14,-36498.29,-67657.14,-44032,-38765.71,-327826.29,221153024,-233344,-276608,-255232,187648,-238208,-337792,-220502710.86,39570.29,-36790.86,-35693.71
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=node-5 metric=system.disk.total baseline=4067313956.570001 peak=5144867840.0 signed_z=999.0 onset_bin=49 onset_rel_s=1809.844 persistence_bins=6
values_compact=delta:4067313956.57,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1077553883.43,0,0,0,0,0,0,-1077553883.43,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=node-5 metric=system.disk.used baseline=3048820326.4005 peak=3909409024.0 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=13
values_compact=delta:3048564150.86,36864,83968,48274.28,40374.86,-57344,33353.14,57929.15,32475.42,-18139.42,-41837.72,36864,38326.86,63195.43,-60269.72,34816,26624,90989.72,51200,-61732.57,41252.57,28086.85,47104,-40960,36571.43,67584,44178.29,38619.43,327972.57,858664996.57,233472,276736,255232,-187904,238336,337664,-859315602.29,-39497.14,36864,35693.72
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-5 metric=system.fs.inodes.free baseline=3189600402.2855 peak=4172889344.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:3190267904,-128731.43,-288475.43,-175250.28,-115565.72,273261.72,-113225.15,-116150.85,-110884.57,119661.71,184905.14,-102692.57,-134875.43,-205092.57,257755.43,-92160,-90404.57,-317147.43,-159158.86,262729.15,-121709.72,-98889.14,-139556.57,180809.14,-99766.86,-254829.71,-126976,-135168,-1263908.57,985732937.14,-891392,-1092352,-982016,789504,-940032,-1311744,-983416393.14,206262.85,-131072,-97426.28
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1860.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-79.7,"n_during":24,"n_pre":118,"service":"emailservice-0"},{"change_pct":-78.8,"n_during":24,"n_pre":113,"service":"paymentservice-0"},{"change_pct":-76.0,"n_during":368,"n_pre":1532,"service":"adservice-2"},{"change_pct":-75.9,"n_during":276,"n_pre":1144,"service":"adservice-1"},{"change_pct":-75.9,"n_during":150,"n_pre":623,"service":"checkoutservice-0"},{"change_pct":-75.8,"n_during":276,"n_pre":1140,"service":"adservice-0"},{"change_pct":-75.6,"n_during":155,"n_pre":636,"service":"checkoutservice-1"},{"change_pct":-75.5,"n_during":2677,"n_pre":10918,"service":"productcatalogservice-0"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-100.0,"error_pct":0.0,"p95_during_ms":0.0,"p95_pre_ms":1.0,"service":"cartservice2-0","spans":2984},{"delta_pct":-99.4,"error_pct":0.0,"p95_during_ms":2.80765,"p95_pre_ms":481.20495,"service":"recommendationservice-0","spans":1698},{"delta_pct":-99.4,"error_pct":0.0,"p95_during_ms":2.811849999999999,"p95_pre_ms":481.2418,"service":"recommendationservice-1","spans":1696},{"delta_pct":-99.4,"error_pct":0.0,"p95_during_ms":2.82135,"p95_pre_ms":481.209,"service":"recommendationservice-2","spans":1698},{"delta_pct":-99.4,"error_pct":0.0,"p95_during_ms":2.9573499999999995,"p95_pre_ms":481.10679999999996,"service":"recommendationservice2-0","spans":2148},{"delta_pct":-47.4,"error_pct":0.0,"p95_during_ms":0.1393,"p95_pre_ms":0.2647999999999979,"service":"paymentservice-0","spans":45},{"delta_pct":20.3,"error_pct":0.0,"p95_during_ms":0.01925,"p95_pre_ms":0.016,"service":"adservice-0","spans":707},{"delta_pct":-15.6,"error_pct":0.0,"p95_during_ms":0.015199999999999988,"p95_pre_ms":0.018,"service":"adservice-1","spans":709}],"omitted_services":31,"service_count":39}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=2
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"recommendationservice2","severity_z":89.197},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"recommendationservice","severity_z":43.305},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":3,"service":"emailservice","severity_z":151.714},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":4,"service":"checkoutservice","severity_z":63.729},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":5,"service":"node-3","severity_z":104.669},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":6,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":7,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":8,"service":"istio-ingressgateway","severity_z":306.352},{"evidence_source":"trace","onset_rel_s":1925.4,"rank":9,"service":"cartservice","severity_z":4.175},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":10,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":11,"service":"frontend","severity_z":624.337},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":12,"service":"productcatalogservice","severity_z":90.234},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":13,"service":"shippingservice","severity_z":50.219},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":14,"service":"paymentservice","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"paymentservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"},{"callee":"productcatalogservice","caller":"recommendationservice2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank recommendationservice-0 first because recommendationservice-0 has direct trace evidence; although frontend-0 is salient, the caller path frontend -> recommendationservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["recommendationservice-0","frontend-0"]}

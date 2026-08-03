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
opaque_id: INC-8005DD53FE7C
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1464,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-22q7z","istio-ingressgateway-565bffd4d-4nr6v","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice-0 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=3.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,-3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice-0 metric=container_fs_usage_MB./dev/vda1 baseline=22.613281 peak=625.957031 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:22.613281,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,603.34375,0,0,0,0,0,-600.589843,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageAfterGc_used.Tenured_Gen.Copy baseline=55988359.2 peak=56191224.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:55988160,0,0,74.666667,53.333333,16,48,0,0,0,0,53.333333,10.666667,0,21.333333,42.666667,0,0,0,42.666667,21.333333,21.333333,117.333334,53.333333,0,0,0,13.333333,66.666667,0,5.333333,74.666667,48,85.333333,184558,17092.666667,208,218.666667,117.333333,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=adservice metric=java_lang_GarbageCollector_LastGcInfo_memoryUsageBeforeGc_used.Tenured_Gen.Copy baseline=55988351.466667 peak=56191224.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:55988160,0,0,21.333333,106.666667,0,53.333333,10.666667,0,0,0,26.666667,37.333333,0,0,58.666667,5.333333,0,0,21.333333,42.666667,0,101.333333,80,10.666667,0,0,0,60,20,0,42.666667,80,5.333333,117550,84071.333333,194.666667,304,117.333333,42.666667
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=adservice metric=java_lang_MemoryPool_Usage_used.Tenured_Gen baseline=55988359.2 peak=56191224.0 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:55988160,0,0,74.666667,53.333333,16,48,0,0,0,0,53.333333,10.666667,0,21.333333,42.666667,0,0,0,42.666667,21.333333,21.333333,117.333334,53.333333,0,0,0,13.333333,66.666667,0,5.333333,74.666667,48,85.333333,184558,17076.666667,224,218.666667,117.333333,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=adservice metric=jvm_memory_pool_MB_used.Tenured_Gen baseline=53.394662 peak=53.588127 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:53.39447,0,0,0.000082,0.00004,0.000021,0.00004,0,0,0,0,0.000056,0.000005,0,0.000026,0.000035,0,0,0,0.000046,0.000015,0.000026,0.000112,0.000046,0,0,0,0.000012,0.000064,0,0.000005,0.000076,0.000041,0.000102,0.191987,0.000301,0.000214,0.000203,0.000102,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=adservice metric=jvm_memory_pool_allocated_MB_total.Tenured_Gen baseline=134.11106 peak=134.304527 signed_z=999.0 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:134.11087,0,0,0.000072,0.00005,0.000016,0.000045,0,0,0,0,0.000051,0.000011,0,0.00002,0.000041,0,0,0,0.00004,0.000021,0.00002,0.000107,0.000056,0,0,0,0.000012,0.000064,0,0,0.000076,0.000046,0.000081,0.176009,0.016285,0.000199,0.000223,0.000112,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=shippingservice2-0 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.001459 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.001459,0,-0.001459,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=paymentservice-2 metric=container_network_receive_MB.eth0 baseline=0.019409 peak=0.54055 signed_z=320.283 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02283,-0.002599,-0.000024,0.001412,-0.004027,0,0.002771,0.000624,-0.00222,-0.003188,0.004101,-0.000013,0.00078,-0.000487,-0.001769,0.000081,0.001378,-0.001914,0.000485,0.002375,-0.002693,0.00135,0.521297,-0.519445,-0.001906,0.000136,-0.003886,0.007751,-0.005145,-0.001856,0.000483,0.004772,-0.00312,0.007639,-0.007568,-0.001395,0.001539,0.001696,0.001367,-0.001917
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=emailservice-1 metric=container_network_receive_MB.eth0 baseline=0.022083 peak=0.569916 signed_z=189.438 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.020177,0.002146,0.002451,-0.003836,0.000884,0,0.000024,-0.001608,0.009501,-0.01021,0.005232,0.001103,-0.00662,-0.003327,0.00584,0.000249,-0.001172,0.00062,0.004468,-0.005227,0.001687,0.000308,0.000325,0.000037,-0.002924,0.002029,0.001976,0.000433,0.003284,-0.005792,-0.006117,0.005068,0.548907,-0.547387,0.003818,-0.005514,0.001194,-0.000682,0.002636,0.00375
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=paymentservice-1 metric=container_network_receive_MB.eth0 baseline=0.020734 peak=0.549354 signed_z=181.145 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.019398,0.003375,-0.003182,0.000896,0.000224,0,-0.001151,0.00558,-0.006378,0.006279,-0.007349,0.004347,0.003055,-0.005064,-0.007464,0.007424,-0.00258,0.004776,-0.000061,0.001244,-0.00205,0.528035,-0.528973,0.004695,-0.003928,-0.001878,0.003131,-0.000566,-0.000906,-0.000445,-0.000717,0.004072,-0.00284,-0.006759,0.005543,0.001466,0.000309,0.00442,-0.009621,0.005513
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=node-6 metric=system.net.bytes_rcvd baseline=96328.497 peak=647119.92 signed_z=156.474 onset_bin=41 onset_rel_s=1517.344 persistence_bins=15
values_compact=delta:99463.15,-245.98,-2263.61,2263.59,1508.44,-9351.1,4492.31,2508.55,3790.86,-8934.54,1369.53,-1168.37,1887.49,-4382.39,9183.58,-8879.37,5072,-1863.97,6983.25,-9308.28,6724.16,141.2,-4030.6,49609.09,502550.93,-533230.87,12288.71,-5490.87,5927.85,749.31,4353.08,-15927.03,15813.32,-6905.33,4434.8,-754.41,-6170.31,7507.42,1164.68,9887.92
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1560.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":2,"service":"frontend-0"},{"change_pct":-80.5,"n_during":25,"n_pre":128,"service":"emailservice-1"},{"change_pct":-80.4,"n_during":133,"n_pre":678,"service":"checkoutservice-2"},{"change_pct":-80.3,"n_during":24,"n_pre":122,"service":"paymentservice-0"},{"change_pct":-80.3,"n_during":25,"n_pre":127,"service":"paymentservice-2"},{"change_pct":-78.6,"n_during":1779,"n_pre":8311,"service":"currencyservice-2"},{"change_pct":-78.5,"n_during":1787,"n_pre":8309,"service":"currencyservice-0"},{"change_pct":-78.3,"n_during":1806,"n_pre":8312,"service":"currencyservice-1"}],"mode":"volume","omitted_services":23,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-21.2,"error_pct":0.0,"p95_during_ms":0.1424,"p95_pre_ms":0.18070000000000003,"service":"paymentservice-1","spans":49},{"delta_pct":-18.2,"error_pct":0.0,"p95_during_ms":0.015549999999999998,"p95_pre_ms":0.019,"service":"adservice-0","spans":722},{"delta_pct":-13.6,"error_pct":0.0,"p95_during_ms":0.019,"p95_pre_ms":0.022,"service":"adservice2-0","spans":891},{"delta_pct":-11.2,"error_pct":0.0,"p95_during_ms":0.07369999999999999,"p95_pre_ms":0.083,"service":"shippingservice2-0","spans":422},{"delta_pct":9.8,"error_pct":0.0,"p95_during_ms":44.70514999999998,"p95_pre_ms":40.69855,"service":"checkoutservice2-0","spans":704},{"delta_pct":8.9,"error_pct":0.0,"p95_during_ms":0.019599999999999996,"p95_pre_ms":0.018,"service":"adservice-1","spans":722},{"delta_pct":-8.1,"error_pct":0.0,"p95_during_ms":0.22979999999999998,"p95_pre_ms":0.25,"service":"emailservice-1","spans":50},{"delta_pct":-7.3,"error_pct":0.0,"p95_during_ms":0.15389999999999998,"p95_pre_ms":0.16605,"service":"paymentservice-0","spans":48}],"omitted_services":31,"service_count":39}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=15 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"checkoutservice2","severity_z":72.791},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"node-5","severity_z":61.633},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"redis-cart","severity_z":52.711},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"node-6","severity_z":156.474},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"redis-cart2","severity_z":53.374},{"evidence_source":"trace","onset_rel_s":1681.8,"rank":7,"service":"paymentservice","severity_z":31.28},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":8,"service":"currencyservice","severity_z":83.142},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":9,"service":"cartservice2","severity_z":77.622},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":10,"service":"node-2","severity_z":100.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":11,"service":"frontend","severity_z":63.701},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":12,"service":"emailservice","severity_z":189.438},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":13,"service":"node-4","severity_z":41.36},{"evidence_source":"trace","onset_rel_s":2315.4,"rank":14,"service":"shippingservice2","severity_z":4.328}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice2","caller":"checkoutservice2"},{"callee":"shippingservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"currencyservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank adservice-0 first because adservice-0 has direct container_fs_inodes./dev/vda1 evidence (signed-z 999, persistence 0 bins); although frontend-0 is salient, the caller path frontend -> adservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["adservice-0","node-6","checkoutservice2-0","redis-cart-0","frontend-0"]}

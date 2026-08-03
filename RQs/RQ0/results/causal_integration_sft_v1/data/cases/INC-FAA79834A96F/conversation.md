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
opaque_id: INC-FAA79834A96F
observation_window={"duration_rel_s":2220.0,"source_metric_rows":38}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":519,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29178240-fgnjt","example-ant-29178240-wkc4g","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[17.344,52.031,86.719,121.406,156.094,190.781,225.469,260.156,294.844,329.531,364.219,398.906,433.594,468.281,502.969,537.656,572.344,607.031,641.719,676.406,711.094,745.781,780.469,815.156,849.844,884.531,919.219,953.906,988.594,1023.281,1057.969,1092.656,1127.344,1162.031,1196.719,1231.406,1266.094,1300.781,1335.469,1370.156,1404.844,1439.531,1474.219,1508.906,1543.594,1578.281,1612.969,1647.656,1682.344,1717.031,1751.719,1786.406,1821.094,1855.781,1890.469,1925.156,1959.844,1994.531,2029.219,2063.906,2098.594,2133.281,2167.969,2202.656]
[M1] rank=1 service=currencyservice-2 metric=pod_memory_working_set_bytes baseline=298.404211 peak=714680.48 signed_z=999.0 onset_bin=38 onset_rel_s=1335.469 persistence_bins=15
values_compact=delta:0,455.15,-214.15,100.52,-220.39,361.16,-331.62,382.83,-307.63,173.54,-399.41,723.29,-723.29,119.23,607.9,-499.3,65.24,-169.91,382.27,-6.37,2514.75,-1472.8,836.34,-691.63,1191.43,-1001.06,-23.75,448.14,-1051.38,1222.73,-1145.94,1579,711775.59,-711962.06,-447.01,279.46,64.31,-2615.18
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M2] rank=2 service=tidb-tikv metric=grpc_qps baseline=0.0 peak=3.5 signed_z=999.0 onset_bin=38 onset_rel_s=1335.469 persistence_bins=16
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.335,0.02,-0.02,0,0.155,-0.155,0,0.02,-0.02,0,0.02,-0.02,2.765,0.4,-3.165,0.045,-0.025,-0.02,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M3] rank=3 service=tidb-tikv metric=read_mbps baseline=0.0 peak=1398819.96 signed_z=999.0 onset_bin=38 onset_rel_s=1335.469 persistence_bins=16
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,68753.38,-61973.82,-2288.89,650.02,683.62,4093.42,-4087.46,62.84,-982.53,931.82,985.98,-2274.8,1694.33,1392572.05,-1393719.38,5483.95,-5726.57,293.08,-412.24
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M4] rank=4 service=tidb-tikv metric=snapshot_apply_count baseline=0.0 peak=9.91 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.24,-0.24,0,0,0,0,0,0,5.53,4.38,-9.91,0.09,-0.09,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M5] rank=5 service=tidb-tikv metric=write_wal_mbps baseline=0.0 peak=198981.73 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,56.29,-45.85,1.05,0,36.69,242.31,-280.05,2.09,-1.04,-1.05,37.85,-36.8,-1.05,198971.29,-198970.24,56.98,-37.78,62.95,-82.15
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M6] rank=6 service=redis-cart-0 metric=pod_processes baseline=1.0 peak=2.0 signed_z=500.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M7] rank=7 service=productcatalogservice-2 metric=pod_network_receive_bytes baseline=682.634211 peak=19789.65 signed_z=179.378 onset_bin=38 onset_rel_s=1335.469 persistence_bins=16
values_compact=delta:608.73,139.42,-24.78,-55.03,56.94,-20.66,-4,105.49,-213.5,199.23,-212.6,193.17,-102.07,268.37,-320.96,14.8,-92.95,-89.58,249.74,19089.89,-4013.29,1905.56,-3049.57,4919.05,-5147.22,3388.43,-6434.59,4951.35,-187.95,-885.78,1598.51,-2860.58,-103.86,1668.54,-4065.5,3234.94,484.69,-2390.94
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M8] rank=8 service=productcatalogservice-2 metric=pod_network_transmit_packets baseline=6.458421 peak=145.53 signed_z=143.428 onset_bin=38 onset_rel_s=1335.469 persistence_bins=16
values_compact=delta:6.61,1.02,-1.02,0.72,-0.53,0.17,-1.36,2.03,-0.81,0.58,-1.04,-0.36,0.37,0.98,-1.43,-0.39,0.4,-2.6,3.06,139.13,-29.46,14.71,-23.36,36.13,-38.03,24.63,-46.77,36.77,-1.42,-6.76,11.65,-21.01,-0.57,12.67,-30.61,23.71,3.86,-17.66
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M9] rank=9 service=productcatalogservice-2 metric=pod_network_receive_packets baseline=7.145789 peak=127.36 signed_z=103.169 onset_bin=38 onset_rel_s=1335.469 persistence_bins=16
values_compact=delta:6.32,1.56,-0.3,-0.72,0.7,-0.13,0.08,0.92,-2.31,2.13,-2.27,2.27,-1.26,2.98,-3.67,0.37,-1.13,-0.81,2.67,119.96,-25.81,12.79,-18.85,30.59,-32.12,20.63,-41.3,31.57,-1.08,-4.91,10.05,-18.97,0.26,10.78,-25.41,19.88,2.87,-15.01
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M10] rank=10 service=tidb-tidb metric=block_cache_size baseline=31777909.0 peak=34766213.0 signed_z=85.954 onset_bin=38 onset_rel_s=1335.469 persistence_bins=16
values_compact=delta:31777909,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2988304,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M11] rank=11 service=node-3 metric=node_network_transmit_bytes_total baseline=3362.766842 peak=3450.13 signed_z=58.962 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3363.07,-1.4,1.33,0.27,0.4,1.4,-1.67,1.87,-1,-2,-0.8,1,-3.4,2.86,-0.26,-0.07,2.27,0.46,-3.13,1.73,1.54,-2.45,-0.55,1.33,2.73,-2.2,-3.33,90.13,-84.2,-2.13,2.53,-1.33,-4.53,4.4,-0.54,6.2,-5.6,-2.53
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M12] rank=12 service=productcatalogservice-2 metric=pod_network_transmit_bytes baseline=2460.008421 peak=31658.37 signed_z=50.856 onset_bin=38 onset_rel_s=1335.469 persistence_bins=16
values_compact=delta:1865.04,1037.89,-67.4,-402.7,-49.03,514.88,-19.49,412.68,-1545.21,658.41,-248.24,1266.75,-1379.02,1332.36,-1565.97,610.16,-719.43,-201.26,1162.09,28995.86,-5895.51,3583.66,-4631.85,6932.72,-6909.95,4411.39,-10671.46,9021.14,-889.59,-585.61,2682.13,-5360.57,-280.61,2806.44,-6373.81,4904.78,742.37,-3559.11
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1800.0,1980.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":1084,"error_pct":100.0,"service":"productcatalogservice-2","total_logs":1084},{"error_logs":528,"error_pct":7.26,"service":"frontend-2","total_logs":7273},{"error_logs":250,"error_pct":5.86,"service":"frontend-0","total_logs":4267},{"error_logs":246,"error_pct":19.39,"service":"frontend-1","total_logs":1269}],"mode":"errors","omitted_services":19,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-22.7,"error_pct":0.0,"p95_during_ms":0.30935,"p95_pre_ms":0.40015,"service":"shippingservice","spans":610},{"delta_pct":-19.2,"error_pct":0.0,"p95_during_ms":14.625,"p95_pre_ms":18.092900000000004,"service":"productcatalogservice","spans":11520},{"delta_pct":16.2,"error_pct":0.0,"p95_during_ms":80.00675,"p95_pre_ms":68.83850000000002,"service":"checkoutservice","spans":1319},{"delta_pct":-14.8,"error_pct":0.0,"p95_during_ms":4.55225,"p95_pre_ms":5.3439,"service":"recommendationservice","spans":3148},{"delta_pct":-12.6,"error_pct":0.0,"p95_during_ms":4.375,"p95_pre_ms":5.002949999999991,"service":"cartservice","spans":2200},{"delta_pct":-11.5,"error_pct":0.0,"p95_during_ms":77.022,"p95_pre_ms":87.0517999999999,"service":"frontend","spans":27464},{"delta_pct":10.8,"error_pct":0.0,"p95_during_ms":3.8538499999999964,"p95_pre_ms":3.477349999999999,"service":"redis","spans":2348},{"delta_pct":-1.4,"error_pct":0.0,"p95_during_ms":0.9470000000000001,"p95_pre_ms":0.9601999999999997,"service":"emailservice","spans":124}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1140.0,"rank":1,"service":"productcatalogservice","severity_z":179.378},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":2,"service":"tidb-tidb","severity_z":85.954},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":3,"service":"adservice","severity_z":12.596},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":4,"service":"recommendationservice","severity_z":11.074},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":5,"service":"shippingservice","severity_z":15.799},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":6,"service":"tidb-pd","severity_z":28.023},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":7,"service":"node-1","severity_z":13.881},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"redis-cart","severity_z":500.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":9,"service":"node-5","severity_z":26.634},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":10,"service":"node-2","severity_z":14.881},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":11,"service":"node-3","severity_z":58.962},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":12,"service":"cartservice","severity_z":29.389},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":13,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":14,"service":"currencyservice","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

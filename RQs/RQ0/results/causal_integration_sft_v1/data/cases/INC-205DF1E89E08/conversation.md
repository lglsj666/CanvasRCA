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
opaque_id: INC-205DF1E89E08
observation_window={"duration_rel_s":1860.0,"source_metric_rows":32}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":472,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29168160-4j82d","example-ant-29168160-pkvws","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[14.531,43.594,72.656,101.719,130.781,159.844,188.906,217.969,247.031,276.094,305.156,334.219,363.281,392.344,421.406,450.469,479.531,508.594,537.656,566.719,595.781,624.844,653.906,682.969,712.031,741.094,770.156,799.219,828.281,857.344,886.406,915.469,944.531,973.594,1002.656,1031.719,1060.781,1089.844,1118.906,1147.969,1177.031,1206.094,1235.156,1264.219,1293.281,1322.344,1351.406,1380.469,1409.531,1438.594,1467.656,1496.719,1525.781,1554.844,1583.906,1612.969,1642.031,1671.094,1700.156,1729.219,1758.281,1787.344,1816.406,1845.469]
[M1] rank=1 service=paymentservice-0 metric=pod_memory_working_set_bytes baseline=1122.455 peak=503499.06 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1202.05,248,-407.28,14.19,-211.36,287.32,207.97,-396.24,809.41,-1033.17,739.88,-910.74,589.33,-66.75,174.93,-249.41,847.71,-399.91,-265.38,-294.44,421.08,-47.97,-378.37,425.3,-39.29,-852.16,697.03,900.35,-827.07,502314.05,-503371.31,-127.75
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=tidb-tikv metric=raft_propose_wait baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=k8s-master1 metric=node_disk_write_time_seconds_total baseline=0.013125 peak=0.32 signed_z=39.957 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0.01,0.02,-0.03,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0.01,-0.01,0,0,0.1,0,0.01,0.04,0.16,-0.04,-0.27
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=node-6 metric=node_disk_write_time_seconds_total baseline=0.005 peak=0.25 signed_z=16.807 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0.01,-0.01,0.01,-0.01,0,0,0,0.06,-0.06,0,0,0,0,0,0,0,0,0,0,0,0.06,-0.06,0,0,0,0.25,-0.25
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=node-4 metric=node_disk_write_time_seconds_total baseline=0.0 peak=0.03 signed_z=13.32 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.03,-0.03,0,0,0,0,0,0,0,0,0,0,0.02
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=node-5 metric=node_disk_write_time_seconds_total baseline=0.0 peak=0.06 signed_z=13.32 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.06,-0.06,0,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=adservice-0 metric=pod_cpu_usage baseline=0.0 peak=0.03 signed_z=11.872 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.03,-0.03,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=currencyservice-1 metric=rrt_max baseline=9010.125 peak=91497.0 signed_z=11.827 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:5923,3809,-3444,-408,4798,-5781,4137,-3305,-2179,772,2407,26732,-17153,-8814,717,-2285,-1510,1007,1403,84671,-86036,3711,-4302,5012,2668,-5662,-1839,2135,697,2300,-5174,-425
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=k8s-master2 metric=node_disk_write_time_seconds_total baseline=0.201875 peak=3.81 signed_z=11.276 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.02,0,0,0.1,0.14,-0.24,0,0,0.58,0.57,-1.15,0,0,0.21,0.42,-0.63,0,-0.01,0.74,3.06,-0.81,-2.99,0,0,0.54,-0.49,-0.03,0.02,-0.02,0.3,-0.31,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=paymentservice-1 metric=rrt_max baseline=2115.9375 peak=9221.0 signed_z=9.784 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1942,-211,182,-303,1391,-1135,-254,1872,-970,-922,42,111,135,-263,2420,-2360,-49,861,-966,232,-57,7523,-6761,-419,-106,456,-811,68,-5,88,-278,90
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=node-7 metric=node_disk_write_time_seconds_total baseline=0.01125 peak=0.31 signed_z=9.455 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0.06,-0.06,0,0,0,0,0.12,-0.12,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.31,-0.31,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=productcatalogservice-0 metric=rrt_max baseline=29437.75 peak=61284.0 signed_z=8.53 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:32721,-3940,77,3391,-2537,-3470,12453,-14421,225,2080,5003,-5460,958,2188,431,4944,-7182,33823,-31749,-2731,3874,-3782,5296,5532,-10987,328,-1908,4701,2245,-4867,7080,-3779
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1440.0,1860.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-80.0,"n_during":5,"n_pre":25,"service":"redis-cart-0"},{"change_pct":-77.6,"n_during":2044,"n_pre":9125,"service":"frontend-2"},{"change_pct":-76.9,"n_during":8011,"n_pre":34609,"service":"currencyservice-1"},{"change_pct":-76.9,"n_during":380,"n_pre":1646,"service":"shippingservice-0"},{"change_pct":-76.4,"n_during":890,"n_pre":3776,"service":"recommendationservice-2"},{"change_pct":-76.3,"n_during":11583,"n_pre":48843,"service":"cartservice-1"},{"change_pct":-76.1,"n_during":1170,"n_pre":4894,"service":"adservice-1"},{"change_pct":-75.2,"n_during":1690,"n_pre":6821,"service":"frontend-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-13.0,"error_pct":0.0,"p95_during_ms":0.43,"p95_pre_ms":0.494,"service":"shippingservice","spans":2716},{"delta_pct":-9.3,"error_pct":0.0,"p95_during_ms":4.375399999999997,"p95_pre_ms":4.8229,"service":"cartservice","spans":9341},{"delta_pct":-7.1,"error_pct":0.0,"p95_during_ms":3.022549999999991,"p95_pre_ms":3.255,"service":"redis","spans":10029},{"delta_pct":3.5,"error_pct":0.0,"p95_during_ms":1.0842999999999996,"p95_pre_ms":1.0476,"service":"emailservice","spans":385},{"delta_pct":-1.7,"error_pct":0.0,"p95_during_ms":127.37769999999998,"p95_pre_ms":129.55574999999996,"service":"checkoutservice","spans":4506},{"delta_pct":-1.1,"error_pct":0.0,"p95_during_ms":84.65960000000003,"p95_pre_ms":85.58559999999989,"service":"frontend","spans":113700},{"delta_pct":0.3,"error_pct":0.0,"p95_during_ms":6.001899999999998,"p95_pre_ms":5.986249999999998,"service":"recommendationservice","spans":13972},{"delta_pct":0.1,"error_pct":0.0,"p95_during_ms":15.5665,"p95_pre_ms":15.556349999999998,"service":"productcatalogservice","spans":52465}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":960.0,"rank":1,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":2,"service":"node-4","severity_z":13.32},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":3,"service":"currencyservice","severity_z":11.827},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":4,"service":"k8s-master2","severity_z":11.276},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":5,"service":"node-5","severity_z":13.32},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":6,"service":"adservice","severity_z":11.872},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":7,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":8,"service":"k8s-master1","severity_z":39.957},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":9,"service":"node-6","severity_z":16.807},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"frontend","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank checkoutservice-0 first because checkoutservice-0 has direct trace evidence; tidb-tikv is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["checkoutservice-0","tidb-tikv"]}

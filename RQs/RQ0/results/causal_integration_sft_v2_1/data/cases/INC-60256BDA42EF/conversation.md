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
opaque_id: INC-60256BDA42EF
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":489,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29182560-4gbdw","example-ant-29182560-r7p69","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=node-2 metric=node_filesystem_usage_rate baseline=29.865 peak=29.87 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:29.865,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.005,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=node-7 metric=node_network_receive_bytes_total baseline=163.87 peak=163.84 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:163.87,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.03,0.03,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=tidb-tidb metric=duration_avg baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,0,-0.02,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=tidb-tidb metric=qps baseline=0.0 peak=0.29 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.29,-0.29,0,0,0,0.22,-0.22,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=tidb-tikv metric=raft_apply_wait baseline=0.0 peak=0.04 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.04,-0.04,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=tidb-tidb metric=duration_99th baseline=0.01 peak=1.71 signed_z=994.152 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.7,-1.7,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=tidb-tidb metric=block_cache_size baseline=67665439.0 peak=3318304.0 signed_z=-950.96 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:67665439,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-64347135,65888,527104,0,230608,2472976,296496,0,0,622849,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=node-6 metric=node_disk_written_bytes_total baseline=62220.062 peak=2064793.6 signed_z=160.811 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:68403.2,-8806.4,-1194.67,5154.14,14711.46,-24200.53,15291.73,16213.34,-26726.4,921.6,-8676.68,-300.39,-9011.2,7645.87,34952.53,-25941.33,-2457.6,8465.06,-21299.2,42564.27,-26726.4,-17476.27,11195.74,-648.54,6656,273.07,2005811.2,-1996800,-14199.47,1365.34
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=tidb-tikv metric=memory_usage baseline=2099035886.933333 peak=1964441600.0 signed_z=-132.268 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2098810880,430080,1888256,-294912,-2555904,-278528,2723840,-1548288,-1191936,-151552,1175552,-524288,-8192,331776,-49152,-134316032,3850240,3190784,-86016,630784,24363008,745472,-3330048,-348160,1998848,1196032,196608,3268608,1228800,-573440
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=tidb-tikv metric=region_pending baseline=67591.333333 peak=420.0 signed_z=-80.41 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:66363,132,123,133,132,132,127,705,129,167,127,127,128,130,135,-68370,494,700,126,168,141,133,128,129,133,132,124,131,704,165
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=node-1 metric=node_disk_read_bytes_total baseline=72.818 peak=10649.6 signed_z=38.82 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,1092.27,-1092.27,0,0,0,0,0,0,0,0,0,0,0,10649.6,-10649.6,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=node-2 metric=node_disk_written_bytes_total baseline=1046.754667 peak=18496.57 signed_z=35.06 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:819.2,1774.93,-1228.8,-546.13,0,546.13,-819.2,0,819.2,-546.13,-273.07,273.07,273.07,0,0,0,-273.07,0,0,1740.8,9625.6,-10308.27,12185.6,-11946.66,16380.3,-16038.97,12185.6,-12561.07,819.2,1024
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1380.0,1740.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-75.9,"n_during":28,"n_pre":116,"service":"emailservice-2"},{"change_pct":-75.9,"n_during":56,"n_pre":232,"service":"paymentservice-2"},{"change_pct":-75.7,"n_during":164,"n_pre":674,"service":"currencyservice-0"},{"change_pct":-75.4,"n_during":1746,"n_pre":7092,"service":"cartservice-0"},{"change_pct":-75.4,"n_during":513,"n_pre":2088,"service":"cartservice-2"},{"change_pct":-75.4,"n_during":166,"n_pre":674,"service":"currencyservice-2"},{"change_pct":-75.4,"n_during":114,"n_pre":464,"service":"shippingservice-1"},{"change_pct":-75.3,"n_during":258,"n_pre":1044,"service":"checkoutservice-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-10.7,"error_pct":0.0,"p95_during_ms":3.183199999999996,"p95_pre_ms":3.566399999999998,"service":"redis","spans":11334},{"delta_pct":4.2,"error_pct":0.0,"p95_during_ms":1.1345,"p95_pre_ms":1.0892,"service":"emailservice","spans":434},{"delta_pct":-2.7,"error_pct":0.0,"p95_during_ms":0.46539999999999987,"p95_pre_ms":0.4782999999999997,"service":"shippingservice","spans":3048},{"delta_pct":-2.2,"error_pct":0.0,"p95_during_ms":4.91294999999998,"p95_pre_ms":5.024699999999993,"service":"cartservice","spans":10460},{"delta_pct":1.8,"error_pct":0.0,"p95_during_ms":5.7591,"p95_pre_ms":5.656549999999999,"service":"recommendationservice","spans":15690},{"delta_pct":-1.4,"error_pct":0.0,"p95_during_ms":13.5977,"p95_pre_ms":13.790949999999997,"service":"productcatalogservice","spans":59056},{"delta_pct":-1.3,"error_pct":0.0,"p95_during_ms":132.8849999999999,"p95_pre_ms":134.65404999999998,"service":"checkoutservice","spans":5122},{"delta_pct":-0.4,"error_pct":0.0,"p95_during_ms":89.36019999999999,"p95_pre_ms":89.74164999999996,"service":"frontend","spans":127790}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=10 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":3,"service":"node-8","severity_z":17.524},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"adservice","severity_z":12.728},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"node-2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"node-1","severity_z":38.82},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":7,"service":"node-6","severity_z":160.811},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":8,"service":"node-7","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":9,"service":"cartservice","severity_z":24.654},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"redis-cart","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"k8s-master2","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank tidb-tikv first because tidb-tikv has direct raft_apply_wait evidence (signed-z 999, persistence 0 bins); tidb-tidb is second despite propagation rank 1 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["tidb-tikv","tidb-tidb","node-8","adservice","node-2"]}

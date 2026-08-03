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
opaque_id: INC-FAF9F05B4737
observation_window={"duration_rel_s":2100.0,"source_metric_rows":36}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":469,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29158080-vxbvl","example-ant-29158080-drlxt","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[16.406,49.219,82.031,114.844,147.656,180.469,213.281,246.094,278.906,311.719,344.531,377.344,410.156,442.969,475.781,508.594,541.406,574.219,607.031,639.844,672.656,705.469,738.281,771.094,803.906,836.719,869.531,902.344,935.156,967.969,1000.781,1033.594,1066.406,1099.219,1132.031,1164.844,1197.656,1230.469,1263.281,1296.094,1328.906,1361.719,1394.531,1427.344,1460.156,1492.969,1525.781,1558.594,1591.406,1624.219,1657.031,1689.844,1722.656,1755.469,1788.281,1821.094,1853.906,1886.719,1919.531,1952.344,1985.156,2017.969,2050.781,2083.594]
[M1] rank=1 service=cartservice-2 metric=pod_cpu_usage baseline=0.01 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=currencyservice-2 metric=pod_memory_working_set_bytes baseline=1179.007222 peak=1327787.29 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,1051.77,-256.41,-2.13,502.12,11.48,-163.51,-70.88,764,-1143.01,736.71,208.01,-899.75,722.59,-313.8,110.89,-113.05,1270.95,-2140.96,1256.62,-1041.55,741.77,-207.86,1263.36,-1351.28,1286.05,-1331.16,809.58,-1270.14,2067.72,-482.45,460.74,-531.59,-412.85,1087.19,1325168.12
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=example-ant-29158080-drlxt metric=pod_network_receive_bytes baseline=9.974444 peak=5436.18 signed_z=999.0 onset_bin=53 onset_rel_s=1755.469 persistence_bins=7
values_compact=delta:6.6,-1.33,6.46,-7.02,0.86,4.78,-2.27,4.44,-4.6,0.98,1.45,3.19,1.1,-5.26,2.15,-4.75,7.52,3.07,-4.68,-7.67,1.65,4.47,8.68,-11.73,1.11,0.76,-0.07,-1.36,1261.68,1982.19,-1115.05,1607.75,354.16,-335.24,1672.16,-695.1
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=frontend-0 metric=pod_cpu_usage baseline=0.01 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0.01,0,-0.01,0.01,-0.01
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=node-1 metric=node_disk_read_bytes_total baseline=0.0 peak=162747.73 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,162747.73,-162747.73,0,0,0,0,0,0
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=node-1 metric=node_disk_read_time_seconds_total baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=example-ant-29158080-drlxt metric=pod_network_transmit_bytes baseline=9.974444 peak=294.84 signed_z=81.427 onset_bin=53 onset_rel_s=1755.469 persistence_bins=7
values_compact=delta:6.6,-1.33,6.46,-7.02,0.86,4.78,-2.27,4.44,-4.6,0.98,1.45,3.19,1.1,-5.26,2.15,-4.75,7.52,3.07,-4.68,-7.67,1.65,4.47,8.68,-11.73,1.11,0.76,-0.07,-1.36,82.43,85.74,-55.47,82.8,-19.73,-9.3,119.84,-39.38
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=shippingservice-1 metric=pod_memory_working_set_bytes baseline=787.863889 peak=177686.28 signed_z=80.724 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,160,-160,0,7824.96,-7655.78,-169.18,0,0,6027.41,-6027.41,0,0,0,0,177686.28,-177686.28,0,0,0,0,142524.29,-142524.29,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=cartservice-1 metric=rrt_max baseline=3099.666667 peak=20820.0 signed_z=36.442 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3172,-482,204,472,-454,139,1220,-1339,-424,1692,-1514,362,-254,-83,504,-388,887,-911,724,293,16530,-15233,-2053,-309,1003,-228,532,-1211,15209,-12476,-2190,-179,-30,17635,-12397,-5144
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=example-ant-29158080-drlxt metric=pod_network_receive_packets baseline=0.168889 peak=2.51 signed_z=35.569 onset_bin=53 onset_rel_s=1755.469 persistence_bins=7
values_compact=delta:0.12,-0.04,0.15,-0.16,0.01,0.1,-0.06,0.1,-0.08,0.01,0.01,0.07,0.02,-0.09,0.04,-0.1,0.15,0.05,-0.08,-0.14,0.02,0.07,0.2,-0.24,0.03,-0.01,0,-0.02,0.61,0.73,-0.35,0.6,-0.06,-0.06,0.91,-0.37
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=example-ant-29158080-drlxt metric=pod_network_transmit_packets baseline=0.168889 peak=2.44 signed_z=34.506 onset_bin=53 onset_rel_s=1755.469 persistence_bins=7
values_compact=delta:0.12,-0.04,0.15,-0.16,0.01,0.1,-0.06,0.1,-0.08,0.01,0.01,0.07,0.02,-0.09,0.04,-0.1,0.15,0.05,-0.08,-0.14,0.02,0.07,0.2,-0.24,0.03,-0.01,0,-0.02,0.61,0.73,-0.35,0.6,-0.31,0.1,0.93,-0.59
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=cartservice-0 metric=rrt_max baseline=3774.444444 peak=52912.0 signed_z=33.334 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:6303,-3524,732,-13,4,-807,407,1252,171,-2041,283,794,5182,-5396,17,-214,6,-57,-555,144,1715,-1686,625,296,-497,-671,3035,23170,-25468,-318,91,516,755,48661,-50357,175
missing_mask_bits=0010101010010101010100101010101001010101010010101010100101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1680.0,2100.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-80.0,"n_during":5,"n_pre":25,"service":"redis-cart-0"},{"change_pct":-73.9,"n_during":860,"n_pre":3300,"service":"frontend-1"},{"change_pct":-73.5,"n_during":13,"n_pre":49,"service":"emailservice-2"},{"change_pct":-73.5,"n_during":26,"n_pre":98,"service":"paymentservice-0"},{"change_pct":-72.9,"n_during":3956,"n_pre":14613,"service":"currencyservice-1"},{"change_pct":-72.9,"n_during":456,"n_pre":1680,"service":"shippingservice-1"},{"change_pct":-72.5,"n_during":78,"n_pre":284,"service":"currencyservice-2"},{"change_pct":-72.2,"n_during":243,"n_pre":873,"service":"cartservice-1"}],"mode":"volume","omitted_services":14,"service_count":22}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":36.9,"error_pct":0.0,"p95_during_ms":2525.8755499999997,"p95_pre_ms":1844.8390499999998,"service":"checkoutservice","spans":2202},{"delta_pct":-15.2,"error_pct":0.0,"p95_during_ms":0.818,"p95_pre_ms":0.9643999999999996,"service":"emailservice","spans":186},{"delta_pct":5.9,"error_pct":0.0,"p95_during_ms":0.46559999999999996,"p95_pre_ms":0.43979999999999997,"service":"shippingservice","spans":1316},{"delta_pct":3.4,"error_pct":0.0,"p95_during_ms":1.709499999999999,"p95_pre_ms":1.6530499999999997,"service":"redis","spans":4889},{"delta_pct":1.9,"error_pct":0.0,"p95_during_ms":14.152,"p95_pre_ms":13.894,"service":"productcatalogservice","spans":25503},{"delta_pct":-1.6,"error_pct":0.0,"p95_during_ms":5.0511,"p95_pre_ms":5.13205,"service":"recommendationservice","spans":6770},{"delta_pct":0.3,"error_pct":0.0,"p95_during_ms":92.7987,"p95_pre_ms":92.49639999999998,"service":"frontend","spans":55147},{"delta_pct":0.2,"error_pct":0.0,"p95_during_ms":3.0552999999999977,"p95_pre_ms":3.04775,"service":"cartservice","spans":4511}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=6 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"shippingservice","severity_z":80.724},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":2,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":3,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":4,"service":"node-1","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":5,"service":"example-ant","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":6,"service":"currencyservice","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"hipstershop","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"redis-cart","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"k8s-master2","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"tidb-tidb","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

[excluded before optimizer]

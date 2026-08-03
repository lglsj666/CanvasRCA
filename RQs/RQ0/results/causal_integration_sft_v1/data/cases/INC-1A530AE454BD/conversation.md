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
opaque_id: INC-1A530AE454BD
observation_window={"duration_rel_s":1980.0,"source_metric_rows":34}
selection_summary={"candidate_count":61,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":502,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29168160-4j82d","example-ant-10-29169600-zkv48","example-ant-29169600-8lqgx","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.469,46.406,77.344,108.281,139.219,170.156,201.094,232.031,262.969,293.906,324.844,355.781,386.719,417.656,448.594,479.531,510.469,541.406,572.344,603.281,634.219,665.156,696.094,727.031,757.969,788.906,819.844,850.781,881.719,912.656,943.594,974.531,1005.469,1036.406,1067.344,1098.281,1129.219,1160.156,1191.094,1222.031,1252.969,1283.906,1314.844,1345.781,1376.719,1407.656,1438.594,1469.531,1500.469,1531.406,1562.344,1593.281,1624.219,1655.156,1686.094,1717.031,1747.969,1778.906,1809.844,1840.781,1871.719,1902.656,1933.594,1964.531]
[M1] rank=1 service=tidb-tikv metric=raft_apply_wait baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=tidb-tikv metric=write_wal_mbps baseline=82.761176 peak=7253.8 signed_z=44.544 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:11.49,0,0,0,13.27,49.46,-62.73,0,149.8,462.2,-613.05,0,1.05,0,16.4,337.93,-349.15,-5.18,0,77.38,-77.38,0,-1.05,1.05,116.8,456.31,-419.13,-153.98,7242.31,-6570.64,77.91,-748.54,0,570.98
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=tidb-tidb metric=qps baseline=0.012353 peak=1.12 signed_z=29.203 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0.055,-0.055,0,0,0,0,0,0.155,-0.155,0,0,0,0,0,0,0,0,0.055,-0.055,1.12,-1.065,0,0,-0.055,0,0.055
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=k8s-master3 metric=node_disk_written_bytes_total baseline=140753.818824 peak=302318.93 signed_z=15.087 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:128136.53,19046.4,512,7680,-14574.93,21742.93,-16998.4,-15291.73,-1774.93,13209.6,3925.33,-2082.13,-7987.2,-4027.74,-10274.13,13004.8,19182.93,-21265.06,-8328.54,50073.6,-26931.2,-3003.73,-9011.2,-7133.87,-6246.4,18602.67,13380.27,148753.06,-182886.4,-2184.53,6724.27,4608,-2560,-17237.34
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=tidb-tikv metric=snapshot_apply_count baseline=0.094118 peak=1.36 signed_z=13.223 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.04,0,0,0,0.09,-0.09,0,0,0.29,-0.11,-0.18,0,0,0,0.09,0.18,-0.27,0,0,0.23,-0.23,0,0,0,0.14,0.09,-0.23,1.32,-1.03,-0.15,0.02,0.07,-0.23,0
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=paymentservice-1 metric=rrt baseline=1493.26 peak=4396.5 signed_z=11.707 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1864.17,-270.17,-13.75,-228.75,124.5,-161,-356.5,887.5,54.5,-475.5,-10.5,-14.5,163.25,-284.75,-61.5,598,-428.75,3010.25,-3216.17,467.17,265.5,-593,160,-659.75,466.25,178,-361,46,-55.5,552.5,-134.5,-794.5,717,0
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=tidb-tikv metric=grpc_qps baseline=0.413824 peak=1.02 signed_z=10.309 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.365,0.025,0,-0.025,0.07,-0.045,-0.025,0.025,0.175,-0.09,-0.085,0,-0.025,0.025,0.045,0.11,-0.155,0,-0.025,0.145,-0.12,-0.025,0.025,0,0.035,0.105,-0.14,0.63,-0.455,-0.12,0.02,0.065,-0.14,-0.025
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=currencyservice-1 metric=pod_memory_working_set_bytes baseline=49592.427647 peak=1637357.63 signed_z=9.271 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2384.1,3403.69,728138.99,-699584.79,-30047.63,-448.81,14104.96,-17374.3,952.96,3993.44,-930.95,296.6,4270.83,-5776.49,162.39,1882.21,-3508.8,1635439.23,-1633811.98,2360.92,-2548.74,1181.15,980601.18,-170221.57,-813197.87,181.53,51.19,681251.64,-682278.92,1740.8,-655.72,2803.69,-3268.04,3379.66
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=cartservice-1 metric=timeout baseline=0.0 peak=1.0 signed_z=8.5 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,1,-1,0
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=node-8 metric=node_disk_write_time_seconds_total baseline=0.0 peak=0.01 signed_z=8.275 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0.01
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=tidb-pd metric=memory_usage baseline=184875851.294118 peak=183808000.0 signed_z=-8.266 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:184700928,0,0,0,0,0,270336,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,290816,0,-1454080,253952,262144,0,0,0,270336,0,0
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=tidb-tidb metric=connection_count baseline=2.058824 peak=4.0 signed_z=8.25 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,1,-1,2,-2,0,1,-1,0,1,-1,0,1,-1
missing_mask_bits=0010101010101010101010101010101001010101010101010101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1560.0,1680.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":2,"error_pct":50.0,"service":"adservice-2","total_logs":4}],"mode":"errors","omitted_services":23,"service_count":24}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":32.6,"error_pct":0.0,"p95_during_ms":0.5750500000000004,"p95_pre_ms":0.43364999999999987,"service":"shippingservice","spans":1182},{"delta_pct":-31.6,"error_pct":0.0,"p95_during_ms":0.7555000000000001,"p95_pre_ms":1.10525,"service":"emailservice","spans":167},{"delta_pct":-20.6,"error_pct":0.0,"p95_during_ms":2.64,"p95_pre_ms":3.32485,"service":"redis","spans":4365},{"delta_pct":-18.4,"error_pct":0.0,"p95_during_ms":3.97985,"p95_pre_ms":4.879,"service":"cartservice","spans":4051},{"delta_pct":-5.3,"error_pct":0.0,"p95_during_ms":15.856400000000006,"p95_pre_ms":16.7415,"service":"productcatalogservice","spans":22903},{"delta_pct":1.0,"error_pct":0.0,"p95_during_ms":6.140599999999995,"p95_pre_ms":6.081,"service":"recommendationservice","spans":6074},{"delta_pct":-0.6,"error_pct":0.0,"p95_during_ms":136.81025,"p95_pre_ms":137.62385,"service":"checkoutservice","spans":1958},{"delta_pct":-0.5,"error_pct":0.0,"p95_during_ms":88.8115,"p95_pre_ms":89.24374999999993,"service":"frontend","spans":49416}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=5 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1020.0,"rank":1,"service":"paymentservice","severity_z":11.707},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":2,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":3,"service":"tidb-tidb","severity_z":29.203},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":4,"service":"k8s-master3","severity_z":15.087},{"evidence_source":"trace","onset_rel_s":1711.8,"rank":5,"service":"emailservice","severity_z":6.255},{"evidence_source":"none","onset_rel_s":null,"rank":6,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"tidb-pd","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"k8s-master2","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"checkoutservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank checkoutservice-2 first because checkoutservice-2 has direct trace evidence; paymentservice is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["checkoutservice-2","paymentservice"]}

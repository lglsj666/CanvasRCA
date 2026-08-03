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
opaque_id: INC-7109DA562329
observation_window={"duration_rel_s":1800.0,"source_metric_rows":31}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":468,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29160960-4hv7k","example-ant-29160960-lpx4l","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[14.062,42.188,70.312,98.438,126.562,154.688,182.812,210.938,239.062,267.188,295.312,323.438,351.562,379.688,407.812,435.938,464.062,492.188,520.312,548.438,576.562,604.688,632.812,660.938,689.062,717.188,745.312,773.438,801.562,829.688,857.812,885.938,914.062,942.188,970.312,998.438,1026.562,1054.688,1082.812,1110.938,1139.062,1167.188,1195.312,1223.438,1251.562,1279.688,1307.812,1335.938,1364.062,1392.188,1420.312,1448.438,1476.562,1504.688,1532.812,1560.938,1589.062,1617.188,1645.312,1673.438,1701.562,1729.688,1757.812,1785.938]
[M1] rank=1 service=node-3 metric=node_network_receive_bytes_total baseline=120.93 peak=116.53 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:120.93,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-4.4,4.4,0,0,0,0,0,-2.8,2.8,-2.8,2.8,-2.8
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=node-3 metric=node_network_receive_packets_total baseline=1.27 peak=1.2 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1.27,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.07,0.07,0,0,0,0,0,-0.07,0.07,-0.07,0.07,-0.07
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=node-3 metric=node_network_transmit_packets_total baseline=1.27 peak=1.2 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1.27,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.07,0.07,-0.07,0.07,-0.07
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=node-8 metric=node_disk_read_time_seconds_total baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=node-8 metric=node_filesystem_usage_rate baseline=53.683667 peak=81.7 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:53.71,-0.045,0.005,0.01,0.015,-0.03,0.005,0.005,0.01,0.02,-0.03,0.01,0.01,0.01,-0.03,27.995,0.01,0,0.02,-0.03,-0.87,0,0.035,0,0.015,-0.005,-0.025,0.025,0,0.01,0
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=paymentservice-0 metric=pod_memory_working_set_bytes baseline=926.078 peak=698942.75 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:659.08,25.26,-247.22,1264.76,-1034.22,1019.08,-887.4,-384.5,1044.63,-1022.1,936.2,-773,534.74,-246.56,56.38,-205.93,480.18,-682.17,371.83,83.72,38.18,417.24,-627.69,127.32,-607.72,520.1,-60.03,698142.59,-697610.42,1850.77,-927.07
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=redis-cart-0 metric=pod_fs_reads_bytes baseline=0.0 peak=266.56 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,266.56,-266.56,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=shippingservice-2 metric=pod_memory_working_set_bytes baseline=6.637333 peak=424284.61 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,99.56,-99.56,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,91.7,-91.7,0,0,0,0,0,348765.95,-348765.95,424284.61,-424284.61
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=tidb-tikv metric=raft_propose_wait baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=currencyservice-2 metric=pod_memory_working_set_bytes baseline=2406.298667 peak=424968.1 signed_z=422.411 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1390.86,585.87,-667.06,570.91,-113.67,1509.44,-589.42,-1383.32,2550.81,-3196.36,1593.69,618.01,692.18,184.39,-185.75,94.12,410.16,236.56,-732.61,421399.29,-424344.23,591.64,-444.95,1753.56,-1263.7,665.3,-432.98,208.03,899.01,465.19,-1679.55
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=node-8 metric=node_disk_read_bytes_total baseline=764.586667 peak=902758.4 signed_z=315.292 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,11468.8,-11468.8,0,0,0,0,0,0,0,0,0,0,902758.4,-884189.87,-18568.53,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=k8s-master2 metric=node_filesystem_free_bytes baseline=9502102323.2 peak=9535758336.0 signed_z=240.177 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:9502228480,0,0,-86016,20480,0,0,-65536,0,-151552,4096,434176,-483328,0,40960,20480,-147456,499712,-479232,0,-65536,0,0,33988608,-33988608,114688,0,0,0,233472,2048000
missing_mask_bits=0101010101010101101010101010101101010101010101011010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1080.0,1200.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":35,"service":"redis-cart-0"},{"change_pct":-93.6,"n_during":40,"n_pre":622,"service":"currencyservice-2"},{"change_pct":-93.5,"n_during":7,"n_pre":108,"service":"emailservice-2"},{"change_pct":-93.5,"n_during":14,"n_pre":214,"service":"paymentservice-0"},{"change_pct":-93.5,"n_during":14,"n_pre":214,"service":"paymentservice-1"},{"change_pct":-93.5,"n_during":28,"n_pre":428,"service":"shippingservice-1"},{"change_pct":-93.4,"n_during":7,"n_pre":106,"service":"emailservice-1"},{"change_pct":-93.3,"n_during":244,"n_pre":3650,"service":"shippingservice-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-27.8,"error_pct":0.0,"p95_during_ms":1.4804999999999997,"p95_pre_ms":2.0515999999999996,"service":"redis","spans":8965},{"delta_pct":-20.3,"error_pct":0.0,"p95_during_ms":2.792499999999997,"p95_pre_ms":3.505,"service":"cartservice","spans":8275},{"delta_pct":-16.5,"error_pct":0.0,"p95_during_ms":0.348,"p95_pre_ms":0.417,"service":"shippingservice","spans":2403},{"delta_pct":-6.3,"error_pct":0.0,"p95_during_ms":135.95929999999996,"p95_pre_ms":145.1329,"service":"checkoutservice","spans":4018},{"delta_pct":-4.3,"error_pct":0.0,"p95_during_ms":4.725099999999999,"p95_pre_ms":4.93625,"service":"recommendationservice","spans":12416},{"delta_pct":-3.1,"error_pct":0.0,"p95_during_ms":0.9499499999999999,"p95_pre_ms":0.980799999999999,"service":"emailservice","spans":341},{"delta_pct":-1.7,"error_pct":0.0,"p95_during_ms":13.2658,"p95_pre_ms":13.502,"service":"productcatalogservice","spans":46711},{"delta_pct":-1.0,"error_pct":0.0,"p95_during_ms":88.33199999999998,"p95_pre_ms":89.195,"service":"frontend","spans":101125}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=10 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"cartservice","severity_z":44.248},{"evidence_source":"metric","onset_rel_s":960.0,"rank":2,"service":"redis-cart","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":3,"service":"node-3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":4,"service":"currencyservice","severity_z":422.411},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"node-8","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":6,"service":"node-4","severity_z":26.702},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":7,"service":"node-1","severity_z":24.458},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":8,"service":"k8s-master2","severity_z":240.177},{"evidence_source":"trace","onset_rel_s":1406.4,"rank":9,"service":"emailservice","severity_z":13.01},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":10,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"node-6","severity_z":12.654},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":12,"service":"shippingservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":13,"service":"checkoutservice","severity_z":10.687},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":14,"service":"tidb-tikv","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-8 first because node-8 has direct node_disk_read_time_seconds_total evidence (signed-z 999, persistence 0 bins); cartservice is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["node-8","cartservice"]}

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
opaque_id: INC-44CD8272A397
observation_window={"duration_rel_s":1920.0,"source_metric_rows":33}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":467,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29158080-vxbvl","example-ant-29158080-drlxt","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.0,45.0,75.0,105.0,135.0,165.0,195.0,225.0,255.0,285.0,315.0,345.0,375.0,405.0,435.0,465.0,495.0,525.0,555.0,585.0,615.0,645.0,675.0,705.0,735.0,765.0,795.0,825.0,855.0,885.0,915.0,945.0,975.0,1005.0,1035.0,1065.0,1095.0,1125.0,1155.0,1185.0,1215.0,1245.0,1275.0,1305.0,1335.0,1365.0,1395.0,1425.0,1455.0,1485.0,1515.0,1545.0,1575.0,1605.0,1635.0,1665.0,1695.0,1725.0,1755.0,1785.0,1815.0,1845.0,1875.0,1905.0]
[M1] rank=1 service=adservice-2 metric=pod_memory_working_set_bytes baseline=6.366875 peak=11394325.24 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,101.87,-101.87,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,11394325.24,-11394325.24
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=tidb-tidb metric=qps baseline=0.0 peak=0.055 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.055,-0.055,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=k8s-master3 metric=node_disk_write_time_seconds_total baseline=0.010625 peak=0.4 signed_z=160.858 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:0.01,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0.16,0.06,0.07,-0.03,-0.13,0.08,0.13,-0.06,-0.11,-0.17,0,0.01,0.38,-0.26,0.04,0.01
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=tidb-tikv metric=read_mbps baseline=16935.35375 peak=291478.18 signed_z=66.403 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:25363.49,-10575.85,-875.17,1803.73,-1102.93,758.75,-945.31,984.53,-528.64,415.93,10536.71,-9382.64,-1774.07,-404.57,507.84,10377.56,266318.82,-276701.62,-1596.87,497.69,10168.46,-9780.33,872.56,-319.71,-392.14,144.78,777.62,-227.62,-334.53,434.35,8480.85,-7950.07,-1320.76
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=node-6 metric=node_network_transmit_bytes_total baseline=3307.25 peak=3354.67 signed_z=33.086 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3307.53,0.4,1.27,-0.33,-2.14,2.6,-0.46,-2.74,1.67,-2,1.07,-2,-0.47,2.33,1.34,-1.2,-0.87,2,0.73,-0.86,45,-3.2,0.13,2,1.53,1.34,-9.2,6.86,-44.8,2.74,-3.67,-1.07,2.07
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=node-6 metric=node_filesystem_usage_rate baseline=56.151875 peak=56.385 signed_z=28.864 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:56.15,0,0,0.01,0,-0.025,0.005,0.005,0,0.01,0,0,0,0.015,-0.015,-0.005,0.005,0.035,0,0.015,0.02,0.035,0,0.015,0.035,0.025,-0.025,0.02,0.02,0.03,0.005,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=node-6 metric=node_filesystem_free_bytes baseline=7697058816.0 peak=7571783680.0 signed_z=-23.8 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:7697858560,-20480,135168,-3674112,-155648,12435456,-1802240,-2371584,-786432,-4198400,237568,-126976,0,-8519680,-1593344,1462272,-1912832,-16805888,-2285568,-7729152,-10235904,-17092608,-69632,-8712192,-16523264,-13889536,15437824,-9183232,-10604544,-16777216,-610304,-102400,53248
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=adservice-0 metric=pod_cpu_usage baseline=0.00625 peak=0.12 signed_z=23.496 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,-0.01,0.01,0,0,-0.01,0.01,-0.01,0.01,0,0,-0.01,0,0,0.01,0.11,-0.12,0.01,0,0,0,-0.01,0.01,0,-0.01,0.01,-0.01,0.01,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=k8s-master1 metric=node_filesystem_usage_rate baseline=47.405938 peak=47.515 signed_z=20.32 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:47.4,0,0.01,0,0,0,0,0.005,-0.015,0,0,0,0.015,-0.01,0,0,0,0,0,0,0,0,0.11,-0.11,0.005,0,-0.005,0.005,-0.005,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=k8s-master1 metric=node_filesystem_free_bytes baseline=4924304640.0 peak=4868005888.0 signed_z=-16.48 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:4928307200,0,-7438336,0,0,0,53248,-360448,7823360,-180224,0,0,-8261632,4939776,-90112,-110592,0,0,-286720,20480,106496,-106496,-56410112,55595008,-516096,0,167936,-45056,49152,20480,0,0,98304
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=k8s-master1 metric=node_disk_write_time_seconds_total baseline=0.010625 peak=0.05 signed_z=16.267 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0.01,-0.01,0,0,0.04,-0.04,0.04,-0.02,-0.02,0.01,0.03,-0.02,-0.02,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=tidb-pd metric=memory_usage baseline=176754688.0 peak=177287168.0 signed_z=14.057 onset_bin=62 onset_rel_s=1875.0 persistence_bins=2
values_compact=delta:176754688,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,532480,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1680.0,1920.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":794,"error_pct":9.46,"service":"frontend-0","total_logs":8397},{"error_logs":390,"error_pct":9.57,"service":"frontend-2","total_logs":4075},{"error_logs":128,"error_pct":9.59,"service":"frontend-1","total_logs":1335},{"error_logs":6,"error_pct":0.12,"service":"adservice-0","total_logs":5127}],"mode":"errors","omitted_services":19,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":110.4,"error_pct":0.0,"p95_during_ms":536.9791000000002,"p95_pre_ms":255.241,"service":"frontend","spans":47296},{"delta_pct":-22.4,"error_pct":0.0,"p95_during_ms":1.987,"p95_pre_ms":2.559649999999999,"service":"redis","spans":4195},{"delta_pct":19.2,"error_pct":0.0,"p95_during_ms":0.49520000000000025,"p95_pre_ms":0.4155,"service":"shippingservice","spans":1124},{"delta_pct":-15.9,"error_pct":0.0,"p95_during_ms":3.436,"p95_pre_ms":4.0860499999999975,"service":"cartservice","spans":3875},{"delta_pct":3.3,"error_pct":0.0,"p95_during_ms":1.0358999999999996,"p95_pre_ms":1.0024,"service":"emailservice","spans":162},{"delta_pct":-2.0,"error_pct":0.0,"p95_during_ms":14.930299999999999,"p95_pre_ms":15.229299999999999,"service":"productcatalogservice","spans":21863},{"delta_pct":-1.4,"error_pct":0.0,"p95_during_ms":146.231,"p95_pre_ms":148.26149999999998,"service":"checkoutservice","spans":1902},{"delta_pct":-1.0,"error_pct":0.0,"p95_during_ms":4.85615,"p95_pre_ms":4.904949999999996,"service":"recommendationservice","spans":5818}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=6 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":960.0,"rank":1,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":960.0,"rank":2,"service":"tidb-tikv","severity_z":66.403},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":3,"service":"cartservice","severity_z":12.135},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":4,"service":"hipstershop","severity_z":12.135},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":5,"service":"redis-cart","severity_z":12.135},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":6,"service":"k8s-master3","severity_z":160.858},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":7,"service":"node-6","severity_z":33.086},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":8,"service":"k8s-master1","severity_z":20.32},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":9,"service":"node-2","severity_z":12.216},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":10,"service":"frontend","severity_z":10.651},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":11,"service":"tidb-pd","severity_z":14.057},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"adservice","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"recommendationservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank adservice-0 first because adservice-0 has direct pod_cpu_usage evidence (signed-z 23.5, persistence 0 bins); tidb-tidb is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["adservice-0","tidb-tidb"]}

# Causal SFT v2 base rollout — INC-F8BA24EB1F8D

## System

You are an expert Site Reliability Engineer performing Root Cause Analysis (RCA) for a microservice application deployed on a Kubernetes cluster. A fault has occurred in the system. Your task is to identify the root cause of the incident.

Root causes can occur at three levels:
- Pod level: a specific container replica (e.g., "cartservice-0")
- Service level: a microservice type (e.g., "paymentservice") — predict any pod of that service
- Node level: an infrastructure host (e.g., "node-6") — nodes appear as isolated entities with system metrics (CPU, memory, network, disk) but no application logs or traces

The system consists of multiple services communicating over HTTP/gRPC, running on shared infrastructure nodes. A fault in one component (pod, service, or node) can propagate to dependent components, causing them to appear degraded even though they are not the root cause.

Node-level faults (e.g., host memory exhaustion, CPU saturation, disk I/O) often manifest as correlated anomalies across multiple pods. If several unrelated pods show simultaneous degradation and a node shows critical system-level metrics, the node is likely the root cause.

Focus on distinguishing the ORIGIN of the fault from its SYMPTOMS in downstream or co-located components.

## User

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-F8BA24EB1F8D/dashboard.png]

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
opaque_id: INC-F8BA24EB1F8D
observation_window={"duration_rel_s":2160.0,"source_metric_rows":37}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":484,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29173920-kh429","example-ant-29173920-v886k","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[16.875,50.625,84.375,118.125,151.875,185.625,219.375,253.125,286.875,320.625,354.375,388.125,421.875,455.625,489.375,523.125,556.875,590.625,624.375,658.125,691.875,725.625,759.375,793.125,826.875,860.625,894.375,928.125,961.875,995.625,1029.375,1063.125,1096.875,1130.625,1164.375,1198.125,1231.875,1265.625,1299.375,1333.125,1366.875,1400.625,1434.375,1468.125,1501.875,1535.625,1569.375,1603.125,1636.875,1670.625,1704.375,1738.125,1771.875,1805.625,1839.375,1873.125,1906.875,1940.625,1974.375,2008.125,2041.875,2075.625,2109.375,2143.125]
[M1] rank=1 service=emailservice-0 metric=pod_memory_working_set_bytes baseline=4.592222 peak=1126296.37 signed_z=999.0 onset_bin=48 onset_rel_s=1636.875 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,82.66,-82.66,0,0,0,0,0,0,0,0,0,0,0,1126296.37,-1126296.37,0,0,0,0,0,0,873717.78,-873631.48,722549.5,-722635.8,0,0,0,0,0,170.47
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M2] rank=2 service=node-3 metric=node_disk_read_bytes_total baseline=0.0 peak=86289.07 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,86289.07,-86289.07,0,0,0,0,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M3] rank=3 service=tidb-tikv metric=write_wal_mbps baseline=31.791667 peak=18415.36 signed_z=333.105 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:31.89,-20.4,36.69,-34.6,-3.14,0,0,-10.44,35.2,211.49,-246.69,4.18,52.46,-44.11,-1.04,-1.05,-9.4,56.54,-54.71,440.4,17972.09,-18379.29,-11.31,-12.23,-1.04,-10.45,10.45,-10.45,34.16,-35.2,20.89,11,-7.13,-12.22,-2.1,1.05,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M4] rank=4 service=node-4 metric=node_network_transmit_bytes_total baseline=3508.817778 peak=3597.27 signed_z=72.82 onset_bin=32 onset_rel_s=1096.875 persistence_bins=3
values_compact=delta:3511.13,-1.93,-1.87,1.67,-1.2,1,1.73,-2.13,0.93,0,-3.13,1.2,2.07,0.33,-0.27,-2.33,1.4,1.07,-4.54,-2.66,8.06,-5.33,1,2.73,-2.46,4.26,-1.2,-0.26,2.4,85.6,-86.2,-4.54,1,2,-3.06,0.53,2.6
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M5] rank=5 service=tidb-tidb metric=qps baseline=0.028333 peak=6.0 signed_z=51.118 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0.51,-0.51,0,0,0,0,0,0,0,0.51,-0.51,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M6] rank=6 service=node-4 metric=node_disk_write_time_seconds_total baseline=0.002778 peak=0.35 signed_z=43.232 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0.03,-0.01,-0.02,0,0,0,0,0,0,0,0,0,0,0,0.03,-0.03,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.35
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M7] rank=7 service=tidb-tikv metric=read_mbps baseline=18152.201111 peak=56324.84 signed_z=31.699 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:16403.16,1562.75,3123.73,-1977.53,-459.22,-539.11,-695.71,165.51,362.31,1547.58,-2209.11,514.2,236.33,-534.53,-1203.32,2924.83,-2304.16,2988.62,-2840.64,2357.47,36901.68,-38944.31,3067.63,-1813.47,852.18,-3882,1654.71,580.93,973.31,-389.24,-744.49,3155.55,290.52,-3657.77,42.77,9.02,-617.38
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M8] rank=8 service=node-1 metric=node_disk_write_time_seconds_total baseline=0.0 peak=0.01 signed_z=31.322 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M9] rank=9 service=node-6 metric=node_disk_write_time_seconds_total baseline=0.0 peak=0.19 signed_z=31.322 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.07,-0.07,0.19,-0.19,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M10] rank=10 service=tidb-tikv metric=snapshot_apply_count baseline=0.083333 peak=1.2 signed_z=19.774 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.13,-0.09,0.14,-0.14,0,0,0,0.09,-0.09,0,0.14,-0.05,0,-0.09,0,0,0,0.14,1.02,-1.16,0.23,-0.14,0,-0.09,0,0,0,0.09,-0.09,0,0,0.09,0,-0.09,0,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M11] rank=11 service=tidb-tikv metric=grpc_qps baseline=0.3975 peak=0.965 signed_z=16.321 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.435,-0.07,0.08,-0.08,0,0.025,-0.025,0.05,-0.025,-0.025,0.09,0,-0.04,-0.05,0.025,-0.025,0,0.08,0.52,-0.6,0.165,-0.095,-0.02,-0.025,-0.025,0,0.025,0.025,-0.05,0.025,-0.025,0.07,0,-0.07,0,0.025,-0.025
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M12] rank=12 service=node-1 metric=node_network_receive_bytes_total baseline=119.488889 peak=100.8 signed_z=-13.692 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:121.2,0,0,-2.8,2.8,-2.8,2.8,-2.8,2.8,-2.8,0,2.8,-2.8,0,0,0,0,0,0,2.8,-2.8,0,2.8,-2.8,0,2.8,-2.8,0,2.8,0,0,0,0,0,-20.4,17.6,2.8
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1080.0,1200.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":30,"service":"redis-cart-0"},{"change_pct":-95.0,"n_during":3,"n_pre":60,"service":"emailservice-1"},{"change_pct":-95.0,"n_during":6,"n_pre":120,"service":"paymentservice-2"},{"change_pct":-94.9,"n_during":3,"n_pre":59,"service":"emailservice-2"},{"change_pct":-94.9,"n_during":6,"n_pre":118,"service":"paymentservice-0"},{"change_pct":-94.6,"n_during":42,"n_pre":774,"service":"shippingservice-0"},{"change_pct":-94.4,"n_during":657,"n_pre":11637,"service":"cartservice-2"},{"change_pct":-94.4,"n_during":30,"n_pre":534,"service":"checkoutservice-1"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-14.5,"error_pct":0.0,"p95_during_ms":1.8715999999999997,"p95_pre_ms":2.18815,"service":"redis","spans":4863},{"delta_pct":12.7,"error_pct":0.0,"p95_during_ms":4.275099999999998,"p95_pre_ms":3.7939999999999996,"service":"cartservice","spans":4490},{"delta_pct":-10.6,"error_pct":0.0,"p95_during_ms":0.93045,"p95_pre_ms":1.0404000000000002,"service":"emailservice","spans":188},{"delta_pct":-8.9,"error_pct":0.0,"p95_during_ms":137.49674999999996,"p95_pre_ms":150.8697499999999,"service":"checkoutservice","spans":2222},{"delta_pct":-4.0,"error_pct":0.0,"p95_during_ms":0.436,"p95_pre_ms":0.4539999999999986,"service":"shippingservice","spans":1314},{"delta_pct":2.6,"error_pct":0.0,"p95_during_ms":5.027049999999999,"p95_pre_ms":4.9014999999999995,"service":"recommendationservice","spans":6724},{"delta_pct":-0.5,"error_pct":0.0,"p95_during_ms":13.178249999999988,"p95_pre_ms":13.243750000000004,"service":"productcatalogservice","spans":25330},{"delta_pct":-0.2,"error_pct":0.0,"p95_during_ms":86.21579999999987,"p95_pre_ms":86.42675,"service":"frontend","spans":54926}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=10 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":1080.0,"rank":1,"service":"shippingservice","severity_z":13.091},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":2,"service":"emailservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"tidb-tikv","severity_z":333.105},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":4,"service":"tidb-tidb","severity_z":51.118},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":5,"service":"node-1","severity_z":31.322},{"evidence_source":"trace","onset_rel_s":1237.2,"rank":6,"service":"redis","severity_z":7.214},{"evidence_source":"trace","onset_rel_s":1237.2,"rank":7,"service":"cartservice","severity_z":6.606},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":8,"service":"node-6","severity_z":31.322},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":9,"service":"node-3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"node-4","severity_z":72.82},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"paymentservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"k8s-master2","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"currencyservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"redis","caller":"cartservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"shippingservice",
"emailservice",
"tidb-tikv",
"tidb-tidb",
"node-1"
],
"reason": "shippingservice is the root cause as it has the earliest anomaly onset (1080s) in the propagation timeline, preceding the degradation of emailservice and the database layer (tidb-tikv/tidb-tidb) by 60-120 seconds.",
"confidence": "high"
}

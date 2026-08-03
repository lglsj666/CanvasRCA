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
opaque_id: INC-A8DB96415028
observation_window={"duration_rel_s":1920.0,"source_metric_rows":33}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":466,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29158080-vxbvl","example-ant-29158080-drlxt","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.0,45.0,75.0,105.0,135.0,165.0,195.0,225.0,255.0,285.0,315.0,345.0,375.0,405.0,435.0,465.0,495.0,525.0,555.0,585.0,615.0,645.0,675.0,705.0,735.0,765.0,795.0,825.0,855.0,885.0,915.0,945.0,975.0,1005.0,1035.0,1065.0,1095.0,1125.0,1155.0,1185.0,1215.0,1245.0,1275.0,1305.0,1335.0,1365.0,1395.0,1425.0,1455.0,1485.0,1515.0,1545.0,1575.0,1605.0,1635.0,1665.0,1695.0,1725.0,1755.0,1785.0,1815.0,1845.0,1875.0,1905.0]
[M1] rank=1 service=node-1 metric=node_disk_read_bytes_total baseline=0.0 peak=1092.27 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1092.27,-1092.27,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=paymentservice-2 metric=pod_memory_working_set_bytes baseline=1406.71375 peak=446082.47 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1195.56,-154.95,220.75,231.13,-986.4,548.65,602.85,127.07,-654.03,683.65,-613.71,847.43,78.16,-581.86,-396.63,355.04,504.98,-148.7,-539.12,-121.2,-196.45,588.97,226.51,-539.78,141.37,777.74,-838.96,1356.05,443368.35,-445987.98,182.82,186.77,-130.85
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=tidb-tikv metric=raft_apply_wait baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0,-0.01,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=redis-cart-0 metric=pod_processes baseline=1.0 peak=2.0 signed_z=500.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,1,-1
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=paymentservice-2 metric=rrt_max baseline=2400.5625 peak=55478.0 signed_z=58.635 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1636,691,-448,274,-10,-243,-10,687,-409,2806,-3115,1574,-1280,-676,421,2044,-1459,263,-791,-542,490,270,37,-244,1475,-1391,720,52708,-53420,-128,-340,198,249
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=emailservice-1 metric=rrt_max baseline=3991.9375 peak=79393.0 signed_z=54.998 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:3423,5028,-5033,-18,-490,82,509,79,1868,105,-2154,381,-425,-446,1120,-306,-838,943,-273,-365,552,320,-785,76116,-73859,-1250,-644,-279,-158,1004,336,-1712,5331
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=paymentservice-2 metric=rrt baseline=1539.77875 peak=10369.33 signed_z=53.989 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1326.8,156.62,-28.36,152.77,-123.33,-103.43,54.6,363.41,-210.96,234.48,-321.74,294.06,-291.06,-245.19,225.47,225.72,-181.11,139.92,-257.1,-361.78,519.01,-50.16,-60.14,50.33,226.67,-242.9,124.76,8751.97,-8822.1,54.85,-384.29,238.13,26.87
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=paymentservice metric=rrt_max baseline=3513.5 peak=55478.0 signed_z=47.836 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2037,487,1702,1468,-1347,-1522,-824,576,415,1982,-1458,-83,1704,-2565,847,523,-686,1182,-431,1356,-1961,1056,-2248,1564,-333,-317,2753,49601,-53392,332,688,-472,4
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=paymentservice metric=rrt baseline=1621.885 peak=4865.41 signed_z=34.442 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1457.35,75.02,99.08,178.27,-137.48,-42.95,-93.54,77.92,43.87,43.76,-104.82,162.26,-56.38,-202.22,142.37,-133.26,169.47,100.78,-220.36,6.65,170,199.86,-514.62,258.66,-170.35,36.55,214.7,3104.82,-3314.43,31.56,-85.72,-11.44,5.81
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=shippingservice-0 metric=rrt_max baseline=4718.5 peak=75396.0 signed_z=32.505 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2684,-183,4136,278,-3152,6526,-7007,-63,62,929,-389,2495,-844,-2832,4909,-4632,2620,-472,-1008,13795,-14836,72380,-72431,919,38551,-38736,-473,1198,314,10542,-8451,3904,-7612
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=k8s-master1 metric=node_disk_write_time_seconds_total baseline=0.0175 peak=0.45 signed_z=25.235 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,0,0,0,0.07,-0.06,0,-0.01,0,0,0.02,-0.02,0.01,-0.01,0,0,0,0,0,0.36,-0.2,-0.03,0.19,-0.05,0.17,-0.44,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=paymentservice-2 metric=pod_cpu_usage baseline=0.0 peak=0.01 signed_z=16.126 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1320.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":6,"error_pct":0.06,"service":"adservice-0","total_logs":10043},{"error_logs":6,"error_pct":1.29,"service":"adservice-1","total_logs":465},{"error_logs":6,"error_pct":1.28,"service":"adservice-2","total_logs":467},{"error_logs":2,"error_pct":0.01,"service":"frontend-2","total_logs":16554},{"error_logs":1,"error_pct":0.01,"service":"frontend-0","total_logs":15089}],"mode":"errors","omitted_services":19,"service_count":24}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":31.9,"error_pct":0.0,"p95_during_ms":3.3959999999999804,"p95_pre_ms":2.5749999999999926,"service":"redis","spans":16602},{"delta_pct":19.0,"error_pct":0.0,"p95_during_ms":4.975799999999999,"p95_pre_ms":4.18025,"service":"cartservice","spans":15324},{"delta_pct":9.2,"error_pct":0.0,"p95_during_ms":1.1885999999999999,"p95_pre_ms":1.0888999999999998,"service":"emailservice","spans":639},{"delta_pct":6.7,"error_pct":0.0,"p95_during_ms":0.47239999999999993,"p95_pre_ms":0.44264999999999965,"service":"shippingservice","spans":4465},{"delta_pct":2.7,"error_pct":0.0,"p95_during_ms":5.385149999999999,"p95_pre_ms":5.24525,"service":"recommendationservice","spans":22956},{"delta_pct":-1.7,"error_pct":0.0,"p95_during_ms":146.90369999999996,"p95_pre_ms":149.4802999999997,"service":"checkoutservice","spans":7536},{"delta_pct":0.4,"error_pct":0.0,"p95_during_ms":13.959,"p95_pre_ms":13.897300000000003,"service":"productcatalogservice","spans":86404},{"delta_pct":0.3,"error_pct":0.0,"p95_during_ms":89.17499999999998,"p95_pre_ms":88.873,"service":"frontend","spans":187265}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1140.0,"rank":1,"service":"node-7","severity_z":13.968},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"node-8","severity_z":13.359},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"shippingservice","severity_z":32.505},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":5,"service":"k8s-master1","severity_z":25.235},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":6,"service":"tidb-tidb","severity_z":14.279},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":7,"service":"emailservice","severity_z":54.998},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":8,"service":"node-1","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":9,"service":"redis-cart","severity_z":500.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"paymentservice","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"k8s-master2","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"frontend","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank adservice first because adservice has direct log evidence; node-7 is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["adservice","node-7"]}

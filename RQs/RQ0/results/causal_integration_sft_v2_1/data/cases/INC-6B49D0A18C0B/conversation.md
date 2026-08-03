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
opaque_id: INC-6B49D0A18C0B
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":473,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29156640-92pct","example-ant-29156640-q8sgz","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=currencyservice-2 metric=pod_memory_working_set_bytes baseline=2131.335333 peak=1422658.4 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:2436.16,-914.05,767.86,-768.94,1437.16,-1796.59,1539.96,-1569.83,874.36,-77.57,-258.73,-33.79,2079.73,-914.22,-311.47,822.73,727.47,-1521.12,5102.03,-3479.06,-829.75,510.93,-27.06,-268.65,1419130.84,-1422344.24,479,378.63,976.75,298.27
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=paymentservice-2 metric=pod_memory_working_set_bytes baseline=1175.842667 peak=490761.21 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1328.51,-1328.51,1073.72,-337.38,989.41,-1001.44,650.59,-574.08,899.87,-659.95,612.21,-355.22,65.36,-262.04,615.99,-220.75,137.54,-1087.7,1034.49,-380.78,-177.29,413.66,314.77,-778.16,489788.39,-490761.21,0,0,95.72,3.95
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=tidb-tidb metric=qps baseline=0.0 peak=0.31 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.31,-0.31,0,0,0,0,0,0,0,0,0,0,0.18,-0.18,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=tidb-tikv metric=read_mbps baseline=19185.757333 peak=453627.42 signed_z=129.315 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:27549.07,-10950.09,2037.11,-273.07,-279.11,-2311.47,2728.43,-1980.58,1082.22,445.47,9054.89,-9636.27,1575.04,-734.75,1886.31,7244.84,426189.38,-435881.06,-528.47,480.38,12305.35,-11358.62,-1642.87,1495.05,1244.82,8467.02,-9073.78,62121.89,-63055.57,564.57
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=tidb-tikv metric=write_wal_mbps baseline=12.875333 peak=565.67 signed_z=69.612 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:24.76,-12.23,-2.09,0,0,-8.35,8.35,21.45,-21.45,1.05,13.27,-13.27,-1.05,-9.4,9.4,14.32,540.91,-564.63,41.29,-31.89,16.4,-16.4,1.05,1.04,-11.49,23.72,-13.27,111.89,22.8,-133.65
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=tidb-tidb metric=memory_usage baseline=864276480.0 peak=877559808.0 signed_z=46.221 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:864276480,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1105920,0,0,0,0,0,0,0,0,0,1077248,10563584,536576,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=emailservice-0 metric=rrt_max baseline=4315.8 peak=68816.0 signed_z=41.026 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:4713,-159,2413,-3164,-1019,102,788,2259,-2658,3061,-3584,4773,-4708,830,-576,-419,4797,61367,-66028,295,2465,-2650,11587,-9048,-1829,6706,-5714,-1110,-1060,797
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=node-1 metric=node_memory_MemAvailable_bytes baseline=8628003908.266666 peak=11254009856.0 signed_z=29.591 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:8646234112,145862656,-76861440,-123944960,16293888,127979520,9105408,-185520128,-14254080,-6516736,102662144,21884928,-63803392,-2400256,-151568384,9433088,133730304,-51179520,-132702208,15429632,-18436096,116297728,-29466624,-110952448,-3342336,88088576,-9658368,-14176256,2810277888,5513216
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=node-1 metric=node_memory_usage_rate baseline=50.635333 peak=34.95 signed_z=-29.528 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:50.53,-0.88,0.46,0.74,-0.09,-0.77,-0.05,1.11,0.08,0.04,-0.61,-0.13,0.38,0.01,0.91,-0.06,-0.8,0.31,0.79,-0.09,0.11,-0.7,0.18,0.66,0.02,-0.52,0.05,0.09,-16.78,-0.04
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=adservice-0 metric=rrt_max baseline=42555.666667 peak=67506.0 signed_z=25.124 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:43127,-477,368,-2377,1176,475,136,-423,1530,-924,-507,3184,-3669,1236,-510,102,-338,6724,-7501,3833,9436,-14206,-564,1743,25932,-27258,4102,413,-4484,1306
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=tidb-tikv metric=snapshot_apply_count baseline=0.064 peak=0.93 signed_z=21.759 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.13,-0.09,0,0,0,0.09,-0.09,0.09,-0.09,0,0.09,-0.09,0,0,0,0.89,-0.89,0.09,-0.09,0,0.09,-0.09,0,0,0,0.09,-0.09,0.36,-0.36,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=node-4 metric=node_memory_usage_rate baseline=49.384667 peak=25.31 signed_z=-21.527 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:47.39,0.96,-0.06,0.33,-0.14,0.12,0.91,-0.05,0.13,0.43,0.94,0.12,-1.74,0.2,2,-12.91,-13.21,-0.11,0.84,0.5,0,0.1,-0.14,0.23,0.59,0.13,-0.03,0.15,0.1,0.9
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1380.0,1500.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":19,"service":"productcatalogservice-2"},{"change_pct":-93.2,"n_during":1079,"n_pre":15846,"service":"currencyservice-0"},{"change_pct":-93.2,"n_during":7,"n_pre":103,"service":"emailservice-2"},{"change_pct":-93.2,"n_during":14,"n_pre":206,"service":"paymentservice-0"},{"change_pct":-92.9,"n_during":42,"n_pre":592,"service":"currencyservice-2"},{"change_pct":-92.7,"n_during":135,"n_pre":1845,"service":"cartservice-1"},{"change_pct":-92.7,"n_during":2627,"n_pre":36224,"service":"currencyservice-1"},{"change_pct":-92.7,"n_during":512,"n_pre":7061,"service":"frontend-2"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":30.1,"error_pct":0.0,"p95_during_ms":0.616,"p95_pre_ms":0.4735999999999999,"service":"shippingservice","spans":2281},{"delta_pct":27.0,"error_pct":0.0,"p95_during_ms":5.9921999999999995,"p95_pre_ms":4.716599999999999,"service":"cartservice","spans":7836},{"delta_pct":21.6,"error_pct":0.0,"p95_during_ms":4.0075,"p95_pre_ms":3.294499999999997,"service":"redis","spans":8490},{"delta_pct":16.1,"error_pct":0.0,"p95_during_ms":1.1737999999999997,"p95_pre_ms":1.011,"service":"emailservice","spans":324},{"delta_pct":-11.3,"error_pct":0.0,"p95_during_ms":115.337,"p95_pre_ms":130.06275,"service":"checkoutservice","spans":3812},{"delta_pct":1.7,"error_pct":0.0,"p95_during_ms":86.8686,"p95_pre_ms":85.37769999999998,"service":"frontend","spans":95847},{"delta_pct":-1.7,"error_pct":0.0,"p95_during_ms":13.4461,"p95_pre_ms":13.6755,"service":"productcatalogservice","spans":44135},{"delta_pct":0.2,"error_pct":0.0,"p95_during_ms":5.024949999999999,"p95_pre_ms":5.013,"service":"recommendationservice","spans":11728}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=1
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"frontend","severity_z":14.28},{"evidence_source":"metric","onset_rel_s":900.0,"rank":3,"service":"hipstershop","severity_z":14.28},{"evidence_source":"metric","onset_rel_s":900.0,"rank":4,"service":"checkoutservice","severity_z":14.116},{"evidence_source":"metric","onset_rel_s":960.0,"rank":5,"service":"tidb-tikv","severity_z":129.315},{"evidence_source":"metric","onset_rel_s":960.0,"rank":6,"service":"node-4","severity_z":21.527},{"evidence_source":"metric","onset_rel_s":960.0,"rank":7,"service":"node-8","severity_z":15.827},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":8,"service":"emailservice","severity_z":41.026},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":9,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":10,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":11,"service":"adservice","severity_z":25.124},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":12,"service":"recommendationservice","severity_z":11.995},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":13,"service":"node-1","severity_z":29.591},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"productcatalogservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice-2 first because productcatalogservice-2 has direct trace evidence; although frontend is salient, the caller path frontend -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["productcatalogservice-2","tidb-tidb","tidb-tikv","node-4","node-8"]}

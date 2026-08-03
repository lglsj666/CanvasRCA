# Causal SFT v2 base rollout — INC-F4FA8392F7C7

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

[image: RQs/RQ0/results/causal_integration_sft_v1/data/cases/INC-F4FA8392F7C7/dashboard.png]

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
opaque_id: INC-F4FA8392F7C7
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":509,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29168160-4j82d","example-ant-29168160-pkvws","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=node-5 metric=node_filesystem_usage_rate baseline=25.166 peak=65.69 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:25.155,0.02,-0.005,0.01,-0.03,0.02,0,0,0.01,-0.01,-0.02,0.005,0,0.03,-0.03,40.51,-0.005,0.03,-0.14,0.005,0,0.025,-0.01,-0.015,-0.01,-40.48,0.015,-0.035,0.005,0.025
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=node-7 metric=node_network_receive_bytes_total baseline=164.07 peak=164.03 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:164.07,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.04,0.04,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=paymentservice-0 metric=pod_memory_working_set_bytes baseline=423.571333 peak=459273.98 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:522.88,-522.88,637.81,-144.87,-168.09,-32.97,66.79,-358.67,1077.53,-1077.53,208.74,-208.74,1036.01,-1036.01,1402.26,-1402.26,870.66,-870.66,481.4,-481.4,0,0,0,459273.98,-459273.98,100.94,-1.82,18.39,-117.51,71.64
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=tidb-tikv metric=raft_propose_wait baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=k8s-master2 metric=node_filesystem_free_bytes baseline=9393328401.066668 peak=9453170688.0 signed_z=35.426 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:9395748864,-806912,20480,0,0,0,-253952,-1028096,-2097152,65536,-69632,-32768,0,-32768,65536,-36864,-8192,-520192,0,-28672,806912,-2052096,483328,-131072,327680,62750720,-66072576,-4079616,-139264,-45056
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=node-7 metric=node_disk_write_time_seconds_total baseline=0.000667 peak=0.07 signed_z=27.795 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,0.04,0,0.02,0,-0.07,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=k8s-master2 metric=node_filesystem_usage_rate baseline=35.38 peak=35.265 signed_z=-23.807 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:35.375,0,0,0,0,0,0,0.005,0.005,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.12,0.125,0.01,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=node-2 metric=node_disk_written_bytes_total baseline=1171.911333 peak=7099.73 signed_z=10.178 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:273.07,546.13,273.07,-273.07,273.07,273.06,0,-546.13,273.07,546.13,-853.33,-238.94,546.14,1501.86,-409.6,-648.53,375.47,443.73,-443.73,-102.4,682.66,1536,-819.2,375.47,3515.73,-3925.33,-1638.4,1911.47,-1092.27,1228.8
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=node-4 metric=node_memory_MemAvailable_bytes baseline=8477146862.933333 peak=11390021632.0 signed_z=10.009 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:8792166400,-2547712,-1835008,-14434304,14929920,21942272,-378732544,-3964928,-47624192,70230016,-958464,-385634304,27217920,-41230336,24227840,-23658496,-69545984,-647471104,-416374784,6828032,-15343616,14921728,-16093184,-261451776,-16314368,18358272,-4546560,4679270400,54927360,12763136
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=node-4 metric=node_memory_usage_rate baseline=48.556 peak=31.19 signed_z=-10.005 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:46.68,0.01,0.01,0.09,-0.09,-0.13,2.26,0.02,0.29,-0.42,0,2.3,-0.16,0.25,-0.15,0.14,0.42,3.86,2.48,-0.04,0.09,-0.08,0.09,1.56,0.1,-0.11,0.03,-27.91,-0.33,-0.07
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=node-3 metric=node_disk_write_time_seconds_total baseline=0.002667 peak=0.06 signed_z=9.997 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0.01,-0.01,0,0,0,0,0.01,-0.01,0,0,0,0,0.02,-0.02,0,0.01,0.01,-0.02,0,0,0,0,0,0.01,0,-0.01,0.06,-0.01,-0.04,0.01
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=adservice-1 metric=client_error_ratio baseline=0.092667 peak=3.49 signed_z=9.798 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.39,-1.39,0,0,0,0,0,1.83,-1.83,3.49,-3.49,0,0,1.74,-1.74,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[840.0,1500.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-48.6,"n_during":36,"n_pre":70,"service":"paymentservice-2"},{"change_pct":-45.5,"n_during":18,"n_pre":33,"service":"emailservice-0"},{"change_pct":-45.2,"n_during":51,"n_pre":93,"service":"checkoutservice-2"},{"change_pct":-44.8,"n_during":333,"n_pre":603,"service":"cartservice-1"},{"change_pct":-44.8,"n_during":74,"n_pre":134,"service":"shippingservice-0"},{"change_pct":-44.3,"n_during":108,"n_pre":194,"service":"currencyservice-1"},{"change_pct":-43.9,"n_during":333,"n_pre":594,"service":"cartservice-0"},{"change_pct":-43.9,"n_during":74,"n_pre":132,"service":"shippingservice-2"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-28.8,"error_pct":0.0,"p95_during_ms":0.8577999999999999,"p95_pre_ms":1.2052999999999996,"service":"emailservice","spans":88},{"delta_pct":-11.9,"error_pct":0.0,"p95_during_ms":107.5604999999998,"p95_pre_ms":122.07794999999999,"service":"checkoutservice","spans":1042},{"delta_pct":-6.8,"error_pct":0.0,"p95_during_ms":3.5982999999999983,"p95_pre_ms":3.8613999999999984,"service":"redis","spans":2211},{"delta_pct":-4.4,"error_pct":0.0,"p95_during_ms":16.658600000000003,"p95_pre_ms":17.419399999999996,"service":"productcatalogservice","spans":11530},{"delta_pct":-4.0,"error_pct":0.0,"p95_during_ms":87.7255,"p95_pre_ms":91.396,"service":"frontend","spans":25137},{"delta_pct":-1.3,"error_pct":0.0,"p95_during_ms":5.4906999999999995,"p95_pre_ms":5.563199999999996,"service":"cartservice","spans":2035},{"delta_pct":-1.2,"error_pct":0.0,"p95_during_ms":4.9197999999999995,"p95_pre_ms":4.97805,"service":"recommendationservice","spans":3056},{"delta_pct":-1.2,"error_pct":0.0,"p95_during_ms":0.427,"p95_pre_ms":0.4323499999999997,"service":"shippingservice","spans":606}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=9 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"node-5","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":2,"service":"node-4","severity_z":10.009},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":3,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"node-2","severity_z":10.178},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"node-7","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"k8s-master2","severity_z":35.426},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":7,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"currencyservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"frontend","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"cartservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"checkoutservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

## Assistant

{
"services": [
"node-5",
"node-4",
"node-7",
"node-2",
"node-3"
],
"reason": "The incident is a cluster-wide infrastructure failure initiated by node-5 (earliest onset at t=900s with filesystem saturation), followed by cascading resource exhaustion on nodes 4, 7, 2, and 3, which caused the observed application log volume drops and latency improvements due to service degradation.",
"confidence": "high"
}

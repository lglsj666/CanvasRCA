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
opaque_id: INC-15D9E4FC3FD0
observation_window={"duration_rel_s":1860.0,"source_metric_rows":32}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":471,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29152320-7q99m","example-ant-29152320-kszxj","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[14.531,43.594,72.656,101.719,130.781,159.844,188.906,217.969,247.031,276.094,305.156,334.219,363.281,392.344,421.406,450.469,479.531,508.594,537.656,566.719,595.781,624.844,653.906,682.969,712.031,741.094,770.156,799.219,828.281,857.344,886.406,915.469,944.531,973.594,1002.656,1031.719,1060.781,1089.844,1118.906,1147.969,1177.031,1206.094,1235.156,1264.219,1293.281,1322.344,1351.406,1380.469,1409.531,1438.594,1467.656,1496.719,1525.781,1554.844,1583.906,1612.969,1642.031,1671.094,1700.156,1729.219,1758.281,1787.344,1816.406,1845.469]
[M1] rank=1 service=adservice-0 metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,6,-6,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=adservice-0 metric=client_error_ratio baseline=0.0 peak=0.58 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.58,-0.58,0,0,0,0,0,0,0,0,0,0.56,-0.56,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=adservice-0 metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,6,-6,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=adservice-0 metric=error_ratio baseline=0.0 peak=0.58 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.58,-0.58,0,0,0,0,0,0,0,0,0,0.56,-0.56,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=adservice metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,6,-6,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=adservice metric=client_error_ratio baseline=0.0 peak=0.53 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.53,-0.53,0,0,0,0,0,0,0,0,0,0.51,-0.51,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=adservice metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,6,-6,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=adservice metric=error_ratio baseline=0.0 peak=0.53 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.53,-0.53,0,0,0,0,0,0,0,0,0,0.51,-0.51,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=hipstershop metric=client_error baseline=0.0 peak=12.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,12,-12,0,0,0,0,6,-6,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=hipstershop metric=client_error_ratio baseline=0.0 peak=0.04 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0.04,-0.04,0,0,0,0,0.02,-0.02,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=hipstershop metric=error baseline=0.0 peak=12.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,12,-12,0,0,0,0,6,-6,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=hipstershop metric=error_ratio baseline=0.0 peak=0.04 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0.04,-0.04,0,0,0,0,0.02,-0.02,0,0,0
missing_mask_bits=0101010101010101010101010101010110101010101010101010101010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[900.0,1020.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":30,"service":"redis-cart-0"},{"change_pct":-94.4,"n_during":9,"n_pre":160,"service":"emailservice-1"},{"change_pct":-94.4,"n_during":18,"n_pre":320,"service":"paymentservice-2"},{"change_pct":-94.0,"n_during":171,"n_pre":2871,"service":"cartservice-1"},{"change_pct":-94.0,"n_during":38,"n_pre":638,"service":"shippingservice-0"},{"change_pct":-94.0,"n_during":38,"n_pre":638,"service":"shippingservice-1"},{"change_pct":-93.9,"n_during":87,"n_pre":1434,"service":"checkoutservice-2"},{"change_pct":-93.9,"n_during":56,"n_pre":920,"service":"currencyservice-2"}],"mode":"volume","omitted_services":14,"service_count":22}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":19.4,"error_pct":0.0,"p95_during_ms":0.5907999999999997,"p95_pre_ms":0.495,"service":"shippingservice","spans":3496},{"delta_pct":-13.4,"error_pct":0.0,"p95_during_ms":0.9094,"p95_pre_ms":1.05,"service":"emailservice","spans":500},{"delta_pct":-7.3,"error_pct":0.0,"p95_during_ms":2.8301,"p95_pre_ms":3.052899999999998,"service":"redis","spans":12970},{"delta_pct":7.1,"error_pct":0.0,"p95_during_ms":15.615299999999998,"p95_pre_ms":14.579,"service":"productcatalogservice","spans":67519},{"delta_pct":-4.4,"error_pct":0.0,"p95_during_ms":4.461449999999998,"p95_pre_ms":4.668,"service":"cartservice","spans":11974},{"delta_pct":2.8,"error_pct":0.0,"p95_during_ms":151.30624999999998,"p95_pre_ms":147.23225,"service":"checkoutservice","spans":5888},{"delta_pct":0.8,"error_pct":0.0,"p95_during_ms":89.95689999999999,"p95_pre_ms":89.26229999999993,"service":"frontend","spans":146333},{"delta_pct":0.3,"error_pct":0.0,"p95_during_ms":5.39805,"p95_pre_ms":5.381449999999999,"service":"recommendationservice","spans":17942}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":960.0,"rank":1,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":960.0,"rank":2,"service":"node-1","severity_z":36.51},{"evidence_source":"trace","onset_rel_s":1104.6,"rank":3,"service":"emailservice","severity_z":36.972},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":4,"service":"node-3","severity_z":52.189},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":5,"service":"k8s-master2","severity_z":18.52},{"evidence_source":"trace","onset_rel_s":1220.4,"rank":6,"service":"shippingservice","severity_z":6.785},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":7,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":8,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":9,"service":"paymentservice","severity_z":96.16},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":10,"service":"tidb-tidb","severity_z":500.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":11,"service":"k8s-master3","severity_z":62.226},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":12,"service":"node-5","severity_z":20.372},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"checkoutservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"frontend","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"emailservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank shippingservice-0 first because shippingservice-0 has direct trace evidence; although checkoutservice is salient, the caller path checkoutservice -> shippingservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["shippingservice-0","checkoutservice"]}

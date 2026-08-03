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
opaque_id: INC-4C6A975CD170
observation_window={"duration_rel_s":1740.0,"source_metric_rows":30}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":527,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29158080-vxbvl","example-ant-29158080-drlxt","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[13.594,40.781,67.969,95.156,122.344,149.531,176.719,203.906,231.094,258.281,285.469,312.656,339.844,367.031,394.219,421.406,448.594,475.781,502.969,530.156,557.344,584.531,611.719,638.906,666.094,693.281,720.469,747.656,774.844,802.031,829.219,856.406,883.594,910.781,937.969,965.156,992.344,1019.531,1046.719,1073.906,1101.094,1128.281,1155.469,1182.656,1209.844,1237.031,1264.219,1291.406,1318.594,1345.781,1372.969,1400.156,1427.344,1454.531,1481.719,1508.906,1536.094,1563.281,1590.469,1617.656,1644.844,1672.031,1699.219,1726.406]
[M1] rank=1 service=adservice-2 metric=pod_memory_working_set_bytes baseline=484.571333 peak=7098904.7 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:106.56,-106.56,0,0,0,0,0,0,0,0,7162.01,-7162.01,0,0,0,0,0,0,0,0,0,0,0,0,87.28,-87.28,7098904.7,-7098904.7,0,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M2] rank=2 service=frontend-0 metric=server_error baseline=0.0 peak=16.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,16,-10,10,-10,8,-4,2,0,0,4,-10,6,-8,-4,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M3] rank=3 service=frontend-0 metric=server_error_ratio baseline=0.0 peak=0.43 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.42,-0.24,0.25,-0.26,0.2,-0.11,0.07,0.02,-0.02,0.1,-0.25,0.16,-0.23,-0.11,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M4] rank=4 service=frontend-1 metric=server_error baseline=0.0 peak=22.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,16,-14,14,-10,6,-4,4,-12,18,-18,18,-10,-12,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M5] rank=5 service=frontend-1 metric=server_error_ratio baseline=0.0 peak=0.53 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.12,0.38,-0.34,0.31,-0.23,0.12,-0.08,0.08,-0.26,0.43,-0.43,0.39,-0.18,-0.31,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M6] rank=6 service=frontend-2 metric=server_error baseline=0.0 peak=16.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,16,-6,6,-6,6,-4,2,-2,4,-6,4,0,-2,-12,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M7] rank=7 service=frontend-2 metric=server_error_ratio baseline=0.0 peak=0.37 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.37,-0.12,0.12,-0.12,0.12,-0.06,0.02,-0.05,0.08,-0.09,0.07,-0.01,-0.05,-0.28,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M8] rank=8 service=frontend metric=server_error baseline=0.0 peak=48.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,36,0,2,-2,4,-2,0,2,-8,16,-24,24,-20,-28,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M9] rank=9 service=frontend metric=server_error_ratio baseline=0.0 peak=0.41 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.31,0.01,0,-0.02,0.03,-0.02,0,0.02,-0.06,0.14,-0.2,0.18,-0.15,-0.24,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M10] rank=10 service=hipstershop metric=server_error baseline=0.0 peak=48.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,36,0,2,-2,4,-2,0,2,-8,16,-24,24,-20,-28,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M11] rank=11 service=hipstershop metric=server_error_ratio baseline=0.0 peak=0.15 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.11,0.01,0,-0.01,0.01,0,0,0,-0.02,0.05,-0.07,0.07,-0.06,-0.09,0
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1
[M12] rank=12 service=shippingservice-1 metric=pod_memory_working_set_bytes baseline=27.124 peak=117049.47 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,115.88,73.72,-88.22,-101.38,0,0,0,0,0,0,0,0,0,0,109932.79,-109932.79,82738.77,-82738.77,76.76,-76.76,117049.47,-117049.47,149.1,-27.43
missing_mask_bits=0101010101101010101011010101010110101010101101010101011010101010
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1,0,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[840.0,1680.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":86,"error_pct":0.57,"service":"frontend-2","total_logs":15210},{"error_logs":84,"error_pct":0.58,"service":"frontend-1","total_logs":14485},{"error_logs":71,"error_pct":0.55,"service":"frontend-0","total_logs":12824}],"mode":"errors","omitted_services":21,"service_count":24}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":14.1,"error_pct":0.0,"p95_during_ms":5.33075,"p95_pre_ms":4.673899999999999,"service":"cartservice","spans":12743},{"delta_pct":-13.2,"error_pct":0.0,"p95_during_ms":0.9255499999999999,"p95_pre_ms":1.0669000000000002,"service":"emailservice","spans":308},{"delta_pct":10.5,"error_pct":0.0,"p95_during_ms":3.5213999999999994,"p95_pre_ms":3.1879999999999997,"service":"redis","spans":13849},{"delta_pct":-2.7,"error_pct":0.0,"p95_during_ms":86.49159999999998,"p95_pre_ms":88.92224999999999,"service":"frontend","spans":159778},{"delta_pct":-1.4,"error_pct":0.0,"p95_during_ms":0.44579999999999975,"p95_pre_ms":0.452,"service":"shippingservice","spans":3377},{"delta_pct":-1.1,"error_pct":0.0,"p95_during_ms":139.48905,"p95_pre_ms":141.03539999999995,"service":"checkoutservice","spans":3630},{"delta_pct":0.8,"error_pct":0.0,"p95_during_ms":5.192899999999997,"p95_pre_ms":5.152299999999999,"service":"recommendationservice","spans":19380},{"delta_pct":0.6,"error_pct":0.0,"p95_during_ms":13.886399999999988,"p95_pre_ms":13.809849999999992,"service":"productcatalogservice","spans":72845}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=7 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":900.0,"rank":1,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":900.0,"rank":2,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":3,"service":"node-4","severity_z":13.81},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":4,"service":"cartservice","severity_z":20.923},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":5,"service":"node-8","severity_z":24.061},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":6,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":7,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":8,"service":"shippingservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":9,"service":"checkoutservice","severity_z":24.232},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"k8s-master1","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"k8s-master2","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"tidb-tidb","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"productcatalogservice","caller":"checkoutservice"},{"callee":"shippingservice","caller":"checkoutservice"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"productcatalogservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice first because checkoutservice has direct trace evidence; although frontend is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["checkoutservice","frontend"]}

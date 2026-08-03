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
opaque_id: INC-15255FE86B23
observation_window={"duration_rel_s":1920.0,"source_metric_rows":33}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":462,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29156640-92pct","example-ant-29156640-q8sgz","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.0,45.0,75.0,105.0,135.0,165.0,195.0,225.0,255.0,285.0,315.0,345.0,375.0,405.0,435.0,465.0,495.0,525.0,555.0,585.0,615.0,645.0,675.0,705.0,735.0,765.0,795.0,825.0,855.0,885.0,915.0,945.0,975.0,1005.0,1035.0,1065.0,1095.0,1125.0,1155.0,1185.0,1215.0,1245.0,1275.0,1305.0,1335.0,1365.0,1395.0,1425.0,1455.0,1485.0,1515.0,1545.0,1575.0,1605.0,1635.0,1665.0,1695.0,1725.0,1755.0,1785.0,1815.0,1845.0,1875.0,1905.0]
[M1] rank=1 service=adservice-0 metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=adservice-0 metric=client_error_ratio baseline=0.0 peak=0.58 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.58,-0.58,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=adservice-0 metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=adservice-0 metric=error_ratio baseline=0.0 peak=0.58 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.58,-0.58,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=adservice metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=adservice metric=client_error_ratio baseline=0.0 peak=0.53 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.53,-0.53,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=adservice metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=adservice metric=error_ratio baseline=0.0 peak=0.53 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.53,-0.53,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=hipstershop metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=hipstershop metric=client_error_ratio baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=hipstershop metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=hipstershop metric=error_ratio baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0101010101010101010101010101010101010101010101010101010101010100
observed_counts_compact=csv:1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1200.0,1320.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-94.1,"n_during":56,"n_pre":956,"service":"currencyservice-2"},{"change_pct":-93.9,"n_during":10,"n_pre":164,"service":"emailservice-0"},{"change_pct":-93.9,"n_during":10,"n_pre":164,"service":"emailservice-2"},{"change_pct":-93.9,"n_during":661,"n_pre":10913,"service":"frontend-0"},{"change_pct":-93.9,"n_during":20,"n_pre":330,"service":"paymentservice-0"},{"change_pct":-93.9,"n_during":20,"n_pre":328,"service":"paymentservice-1"},{"change_pct":-93.9,"n_during":40,"n_pre":656,"service":"shippingservice-0"},{"change_pct":-93.8,"n_during":3422,"n_pre":55116,"service":"currencyservice-1"}],"mode":"volume","omitted_services":14,"service_count":22}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":18.3,"error_pct":0.0,"p95_during_ms":5.318199999999999,"p95_pre_ms":4.494599999999999,"service":"cartservice","spans":12481},{"delta_pct":-17.7,"error_pct":0.0,"p95_during_ms":0.829,"p95_pre_ms":1.0077499999999997,"service":"emailservice","spans":521},{"delta_pct":10.7,"error_pct":0.0,"p95_during_ms":3.5919999999999996,"p95_pre_ms":3.2445000000000004,"service":"redis","spans":13527},{"delta_pct":-9.6,"error_pct":0.0,"p95_during_ms":13.228999999999996,"p95_pre_ms":14.638299999999996,"service":"productcatalogservice","spans":70360},{"delta_pct":-6.1,"error_pct":0.0,"p95_during_ms":0.49524999999999997,"p95_pre_ms":0.5275000000000001,"service":"shippingservice","spans":3642},{"delta_pct":5.5,"error_pct":0.0,"p95_during_ms":117.89775,"p95_pre_ms":111.7759500000001,"service":"checkoutservice","spans":6166},{"delta_pct":-3.8,"error_pct":0.0,"p95_during_ms":5.047,"p95_pre_ms":5.247850000000002,"service":"recommendationservice","spans":18716},{"delta_pct":-2.7,"error_pct":0.0,"p95_during_ms":79.25560000000002,"p95_pre_ms":81.42350000000006,"service":"frontend","spans":152338}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=9 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":960.0,"rank":1,"service":"currencyservice","severity_z":68.748},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":2,"service":"k8s-master2","severity_z":30.8},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":3,"service":"node-5","severity_z":12.559},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":4,"service":"recommendationservice","severity_z":10.46},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":5,"service":"cartservice","severity_z":12.032},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":6,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":7,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":8,"service":"node-6","severity_z":28.203},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":9,"service":"paymentservice","severity_z":370.277},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":10,"service":"node-3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1800.0,"rank":11,"service":"node-2","severity_z":10.755},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"tidb-tidb","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":13,"service":"redis-cart","severity_z":500.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":14,"service":"tidb-tikv","severity_z":62.044}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank node-5 first because node-5 has metric evidence at propagation rank 3; currencyservice is second despite propagation rank 1 because onset ordering alone does not establish the causal origin.","services":["node-5","currencyservice"]}

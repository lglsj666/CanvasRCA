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
opaque_id: INC-D29CEAAA1983
observation_window={"duration_rel_s":2040.0,"source_metric_rows":35}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":474,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29178240-fgnjt","example-ant-29178240-wkc4g","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.938,47.812,79.688,111.562,143.438,175.312,207.188,239.062,270.938,302.812,334.688,366.562,398.438,430.312,462.188,494.062,525.938,557.812,589.688,621.562,653.438,685.312,717.188,749.062,780.938,812.812,844.688,876.562,908.438,940.312,972.188,1004.062,1035.938,1067.812,1099.688,1131.562,1163.438,1195.312,1227.188,1259.062,1290.938,1322.812,1354.688,1386.562,1418.438,1450.312,1482.188,1514.062,1545.938,1577.812,1609.688,1641.562,1673.438,1705.312,1737.188,1769.062,1800.938,1832.812,1864.688,1896.562,1928.438,1960.312,1992.188,2024.062]
[M1] rank=1 service=adservice-2 metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=adservice-2 metric=client_error_ratio baseline=0.0 peak=0.63 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.57,-0.57,0,0,0,0,0,0,0,0,0,0,0,0,0,0.63,-0.63,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=adservice-2 metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=adservice-2 metric=error_ratio baseline=0.0 peak=0.63 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.57,-0.57,0,0,0,0,0,0,0,0,0,0,0,0,0,0.63,-0.63,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=adservice metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=adservice metric=client_error_ratio baseline=0.0 peak=0.57 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.52,-0.52,0,0,0,0,0,0,0,0,0,0,0,0,0,0.57,-0.57,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=adservice metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=adservice metric=error_ratio baseline=0.0 peak=0.57 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.52,-0.52,0,0,0,0,0,0,0,0,0,0,0,0,0,0.57,-0.57,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=hipstershop metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=hipstershop metric=client_error_ratio baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=hipstershop metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=hipstershop metric=error_ratio baseline=0.0 peak=0.02 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0,0,0,0,0,0,0,0,0,0,0,0,0,0.02,-0.02,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[960.0,1080.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-94.7,"n_during":9,"n_pre":169,"service":"emailservice-0"},{"change_pct":-94.7,"n_during":18,"n_pre":338,"service":"paymentservice-1"},{"change_pct":-94.4,"n_during":171,"n_pre":3033,"service":"cartservice-1"},{"change_pct":-94.4,"n_during":38,"n_pre":674,"service":"shippingservice-1"},{"change_pct":-94.3,"n_during":87,"n_pre":1517,"service":"checkoutservice-1"},{"change_pct":-94.3,"n_during":1449,"n_pre":25482,"service":"currencyservice-1"},{"change_pct":-94.2,"n_during":1908,"n_pre":33057,"service":"cartservice-0"},{"change_pct":-94.2,"n_during":56,"n_pre":968,"service":"currencyservice-0"}],"mode":"volume","omitted_services":14,"service_count":22}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-18.0,"error_pct":0.0,"p95_during_ms":0.36639999999999995,"p95_pre_ms":0.44659999999999994,"service":"shippingservice","spans":3698},{"delta_pct":-13.3,"error_pct":0.0,"p95_during_ms":0.8555999999999999,"p95_pre_ms":0.9871,"service":"emailservice","spans":528},{"delta_pct":8.9,"error_pct":0.0,"p95_during_ms":4.483399999999999,"p95_pre_ms":4.118,"service":"cartservice","spans":12614},{"delta_pct":7.1,"error_pct":0.0,"p95_during_ms":2.78625,"p95_pre_ms":2.600799999999999,"service":"redis","spans":13681},{"delta_pct":3.3,"error_pct":0.0,"p95_during_ms":5.660099999999999,"p95_pre_ms":5.481450000000001,"service":"recommendationservice","spans":18916},{"delta_pct":1.2,"error_pct":0.0,"p95_during_ms":91.90759999999999,"p95_pre_ms":90.831,"service":"frontend","spans":154100},{"delta_pct":-1.1,"error_pct":0.0,"p95_during_ms":145.91164999999995,"p95_pre_ms":147.49819999999997,"service":"checkoutservice","spans":6212},{"delta_pct":1.0,"error_pct":0.0,"p95_during_ms":14.7232,"p95_pre_ms":14.575,"service":"productcatalogservice","spans":71282}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1020.0,"rank":1,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":2,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":3,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":4,"service":"currencyservice","severity_z":990.873},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":5,"service":"cartservice","severity_z":15.316},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":6,"service":"node-8","severity_z":15.258},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":7,"service":"node-2","severity_z":21.526},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":8,"service":"node-7","severity_z":13.553},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":9,"service":"paymentservice","severity_z":13.564},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"k8s-master1","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"emailservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"tidb-tidb","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank tidb-tikv first because tidb-tikv has metric evidence at propagation rank 3; adservice is second despite propagation rank 1 because onset ordering alone does not establish the causal origin. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["tidb-tikv","adservice","hipstershop","currencyservice","cartservice"]}

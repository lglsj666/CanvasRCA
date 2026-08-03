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
opaque_id: INC-07D3CC94F2F8
observation_window={"duration_rel_s":2040.0,"source_metric_rows":35}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":488,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29159520-nlwlw","example-ant-29159520-w5hmd","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[15.938,47.812,79.688,111.562,143.438,175.312,207.188,239.062,270.938,302.812,334.688,366.562,398.438,430.312,462.188,494.062,525.938,557.812,589.688,621.562,653.438,685.312,717.188,749.062,780.938,812.812,844.688,876.562,908.438,940.312,972.188,1004.062,1035.938,1067.812,1099.688,1131.562,1163.438,1195.312,1227.188,1259.062,1290.938,1322.812,1354.688,1386.562,1418.438,1450.312,1482.188,1514.062,1545.938,1577.812,1609.688,1641.562,1673.438,1705.312,1737.188,1769.062,1800.938,1832.812,1864.688,1896.562,1928.438,1960.312,1992.188,2024.062]
[M1] rank=1 service=adservice-0 metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M2] rank=2 service=adservice-0 metric=client_error_ratio baseline=0.0 peak=0.76 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.76,-0.76,0,0.73,-0.73,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M3] rank=3 service=adservice-0 metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M4] rank=4 service=adservice-0 metric=error_ratio baseline=0.0 peak=0.76 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.76,-0.76,0,0.73,-0.73,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M5] rank=5 service=adservice metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M6] rank=6 service=adservice metric=client_error_ratio baseline=0.0 peak=0.68 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.68,-0.68,0,0.66,-0.66,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M7] rank=7 service=adservice metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M8] rank=8 service=adservice metric=error_ratio baseline=0.0 peak=0.68 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.68,-0.68,0,0.66,-0.66,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M9] rank=9 service=hipstershop metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M10] rank=10 service=hipstershop metric=client_error_ratio baseline=0.0 peak=0.03 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.03,-0.03,0,0.03,-0.03,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M11] rank=11 service=hipstershop metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,0,6,-6,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1
[M12] rank=12 service=hipstershop metric=error_ratio baseline=0.0 peak=0.03 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.03,-0.03,0,0.03,-0.03,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010101010101010010101010101010100101010101010100101010101010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[960.0,1080.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":13483,"error_pct":14.87,"service":"adservice-0","total_logs":90651},{"error_logs":1461,"error_pct":9.85,"service":"frontend-1","total_logs":14833},{"error_logs":967,"error_pct":9.24,"service":"frontend-0","total_logs":10464},{"error_logs":940,"error_pct":8.87,"service":"frontend-2","total_logs":10597},{"error_logs":9,"error_pct":32.14,"service":"adservice-1","total_logs":28},{"error_logs":9,"error_pct":32.14,"service":"adservice-2","total_logs":28}],"mode":"errors","omitted_services":20,"service_count":26}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":24.7,"error_pct":0.0,"p95_during_ms":0.5363999999999999,"p95_pre_ms":0.43,"service":"shippingservice","spans":2902},{"delta_pct":-18.1,"error_pct":0.0,"p95_during_ms":2.0161499999999988,"p95_pre_ms":2.4617000000000004,"service":"redis","spans":10764},{"delta_pct":-13.5,"error_pct":0.0,"p95_during_ms":3.37715,"p95_pre_ms":3.902,"service":"cartservice","spans":9939},{"delta_pct":5.1,"error_pct":0.0,"p95_during_ms":144.68594999999993,"p95_pre_ms":137.63529999999992,"service":"checkoutservice","spans":4872},{"delta_pct":-5.0,"error_pct":0.0,"p95_during_ms":1.0134999999999998,"p95_pre_ms":1.0672499999999996,"service":"emailservice","spans":417},{"delta_pct":2.7,"error_pct":0.0,"p95_during_ms":14.731649999999997,"p95_pre_ms":14.35,"service":"productcatalogservice","spans":55963},{"delta_pct":1.0,"error_pct":0.0,"p95_during_ms":5.126449999999997,"p95_pre_ms":5.075,"service":"recommendationservice","spans":14894},{"delta_pct":0.5,"error_pct":5.16,"p95_during_ms":89.28729999999999,"p95_pre_ms":88.80719999999998,"service":"frontend","spans":121311}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=8 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1020.0,"rank":1,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1020.0,"rank":2,"service":"hipstershop","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":3,"service":"currencyservice","severity_z":388.555},{"evidence_source":"metric","onset_rel_s":1080.0,"rank":4,"service":"shippingservice","severity_z":12.555},{"evidence_source":"metric","onset_rel_s":1140.0,"rank":5,"service":"recommendationservice","severity_z":12.555},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":6,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":7,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":8,"service":"k8s-master2","severity_z":13.676},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":9,"service":"node-2","severity_z":18.367},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":10,"service":"k8s-master3","severity_z":12.971},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":11,"service":"node-3","severity_z":19.751},{"evidence_source":"metric","onset_rel_s":1980.0,"rank":12,"service":"node-6","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"tidb-pd","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"emailservice","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"medium","reason":"Rank adservice first because adservice has direct client_error evidence (signed-z 999, persistence 0 bins); hipstershop is second despite propagation rank 2 because onset ordering alone does not establish the causal origin.","services":["adservice","hipstershop"]}

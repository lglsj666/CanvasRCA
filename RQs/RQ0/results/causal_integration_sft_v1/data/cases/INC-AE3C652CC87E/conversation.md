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
opaque_id: INC-AE3C652CC87E
observation_window={"duration_rel_s":2160.0,"source_metric_rows":37}
selection_summary={"candidate_count":59,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":489,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29153760-dkvdq","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[16.875,50.625,84.375,118.125,151.875,185.625,219.375,253.125,286.875,320.625,354.375,388.125,421.875,455.625,489.375,523.125,556.875,590.625,624.375,658.125,691.875,725.625,759.375,793.125,826.875,860.625,894.375,928.125,961.875,995.625,1029.375,1063.125,1096.875,1130.625,1164.375,1198.125,1231.875,1265.625,1299.375,1333.125,1366.875,1400.625,1434.375,1468.125,1501.875,1535.625,1569.375,1603.125,1636.875,1670.625,1704.375,1738.125,1771.875,1805.625,1839.375,1873.125,1906.875,1940.625,1974.375,2008.125,2041.875,2075.625,2109.375,2143.125]
[M1] rank=1 service=adservice-0 metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M2] rank=2 service=adservice-0 metric=client_error_ratio baseline=0.0 peak=1.6 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.55,-1.55,1.6,-1.6,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M3] rank=3 service=adservice-0 metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M4] rank=4 service=adservice-0 metric=error_ratio baseline=0.0 peak=1.6 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.55,-1.55,1.6,-1.6,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M5] rank=5 service=adservice metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M6] rank=6 service=adservice metric=client_error_ratio baseline=0.0 peak=1.27 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.24,-1.24,1.27,-1.27,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M7] rank=7 service=adservice metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M8] rank=8 service=adservice metric=error_ratio baseline=0.0 peak=1.27 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.24,-1.24,1.27,-1.27,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M9] rank=9 service=currencyservice-0 metric=pod_memory_working_set_bytes baseline=1080.842222 peak=2273912.13 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1999.59,-550.8,-23.89,-183.83,-987.73,1086.42,-108.11,-1231.65,979.51,-235.98,724.73,-665.77,135.69,215,-192.9,-448.28,669.99,594.65,1073.03,-1657.41,2602.95,-2106.33,-377.97,-166.23,345.26,1000.3,-1626.77,3201.81,-2433.36,2272280.21,-2273912.13,84.12,100.55,228.75,1317093.99,-1316649.67,27.69
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M10] rank=10 service=hipstershop metric=client_error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M11] rank=11 service=hipstershop metric=client_error_ratio baseline=0.0 peak=0.07 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.06,-0.06,0.07,-0.07,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1
[M12] rank=12 service=hipstershop metric=error baseline=0.0 peak=6.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,-6,6,-6,0,0
missing_mask_bits=0010101001010101001010100101010100101010010101010010101001010100
observed_counts_compact=csv:1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1800.0,1920.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-94.9,"n_during":54,"n_pre":1062,"service":"cartservice-0"},{"change_pct":-94.9,"n_during":3,"n_pre":59,"service":"emailservice-0"},{"change_pct":-94.9,"n_during":3,"n_pre":59,"service":"emailservice-1"},{"change_pct":-94.9,"n_during":137,"n_pre":2666,"service":"frontend-2"},{"change_pct":-94.9,"n_during":6,"n_pre":118,"service":"paymentservice-0"},{"change_pct":-94.9,"n_during":6,"n_pre":118,"service":"paymentservice-1"},{"change_pct":-94.9,"n_during":12,"n_pre":236,"service":"shippingservice-0"},{"change_pct":-94.7,"n_during":318,"n_pre":6023,"service":"currencyservice-0"}],"mode":"volume","omitted_services":15,"service_count":23}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":18.8,"error_pct":0.0,"p95_during_ms":189.67779999999996,"p95_pre_ms":159.64000000000001,"service":"frontend","spans":43698},{"delta_pct":-12.2,"error_pct":0.0,"p95_during_ms":97.41929999999996,"p95_pre_ms":110.90319999999997,"service":"checkoutservice","spans":1769},{"delta_pct":-11.1,"error_pct":0.0,"p95_during_ms":5.07,"p95_pre_ms":5.705499999999991,"service":"cartservice","spans":3496},{"delta_pct":-10.2,"error_pct":0.0,"p95_during_ms":0.4018,"p95_pre_ms":0.4473,"service":"shippingservice","spans":1033},{"delta_pct":-4.8,"error_pct":0.0,"p95_during_ms":3.942749999999999,"p95_pre_ms":4.139449999999997,"service":"redis","spans":3920},{"delta_pct":0.4,"error_pct":0.0,"p95_during_ms":1.0064499999999996,"p95_pre_ms":1.0019999999999998,"service":"emailservice","spans":149},{"delta_pct":0.2,"error_pct":0.0,"p95_during_ms":16.605399999999996,"p95_pre_ms":16.572899999999997,"service":"productcatalogservice","spans":20192},{"delta_pct":0.1,"error_pct":0.0,"p95_during_ms":101.79379999999999,"p95_pre_ms":101.6818,"service":"recommendationservice","spans":5491}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=9 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1080.0,"rank":1,"service":"node-3","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"node-1","severity_z":115.86},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":3,"service":"node-6","severity_z":67.187},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":4,"service":"node-8","severity_z":27.227},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"node-4","severity_z":11.337},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":6,"service":"tidb-tidb","severity_z":333.333},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":7,"service":"tidb-pd","severity_z":20.075},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":8,"service":"paymentservice","severity_z":15.601},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":9,"service":"currencyservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":10,"service":"recommendationservice","severity_z":15.945},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":11,"service":"k8s-master3","severity_z":13.339},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":12,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1860.0,"rank":13,"service":"hipstershop","severity_z":999.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"frontend","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"recommendationservice","caller":"frontend"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank recommendationservice first because recommendationservice has direct trace evidence; although frontend is salient, the caller path frontend -> recommendationservice means a disturbance in the callee can propagate back toward that caller-side symptom.","services":["recommendationservice","frontend"]}

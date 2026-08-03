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
opaque_id: INC-34DABBACCD01
observation_window={"duration_rel_s":2220.0,"source_metric_rows":38}
selection_summary={"candidate_count":60,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":514,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","cartservice","cartservice-0","cartservice-1","cartservice-2","checkoutservice","checkoutservice-0","checkoutservice-1","checkoutservice-2","currencyservice","currencyservice-0","currencyservice-1","currencyservice-2","emailservice","emailservice-0","emailservice-1","emailservice-2","example-ant-10-29171040-4jmjn","example-ant-29171040-npgll","frontend","frontend-0","frontend-1","frontend-2","hipstershop","k8s-master1","k8s-master2","k8s-master3","node-1","node-2","node-3","node-4","node-5","node-6","node-7","node-8","paymentservice","paymentservice-0","paymentservice-1","paymentservice-2","productcatalogservice","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","recommendationservice","recommendationservice-0","recommendationservice-1","recommendationservice-2","redis","redis-cart","redis-cart-0","shippingservice","shippingservice-0","shippingservice-1","shippingservice-2","tidb-pd","tidb-tidb","tidb-tikv"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[17.344,52.031,86.719,121.406,156.094,190.781,225.469,260.156,294.844,329.531,364.219,398.906,433.594,468.281,502.969,537.656,572.344,607.031,641.719,676.406,711.094,745.781,780.469,815.156,849.844,884.531,919.219,953.906,988.594,1023.281,1057.969,1092.656,1127.344,1162.031,1196.719,1231.406,1266.094,1300.781,1335.469,1370.156,1404.844,1439.531,1474.219,1508.906,1543.594,1578.281,1612.969,1647.656,1682.344,1717.031,1751.719,1786.406,1821.094,1855.781,1890.469,1925.156,1959.844,1994.531,2029.219,2063.906,2098.594,2133.281,2167.969,2202.656]
[M1] rank=1 service=node-7 metric=node_network_receive_bytes_total baseline=164.07 peak=164.04 signed_z=-999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:164.07,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-0.03,0.03,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M2] rank=2 service=paymentservice-2 metric=pod_memory_working_set_bytes baseline=1630.596316 peak=755212.76 signed_z=999.0 onset_bin=38 onset_rel_s=1335.469 persistence_bins=2
values_compact=delta:1431.25,791.12,-575.41,-916.29,1413.66,-1131.76,601.39,-147.02,376.01,-311.89,972.99,-891.03,182.09,234,-1236.82,552.8,889.3,-713.32,-16.93,-451.25,754159.87,-755212.76,241.43,-159.32,189.69,333.6,-8.23,55.19,-290.21,1185.99,-534.42,286.87,-463.28,397.19,-333.93,864.4,-544.21,642.84
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M3] rank=3 service=tidb-tikv metric=raft_propose_wait baseline=0.0 peak=0.01 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M4] rank=4 service=node-8 metric=node_disk_write_time_seconds_total baseline=0.001053 peak=0.06 signed_z=19.208 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0.01,-0.01,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.06,-0.06,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M5] rank=5 service=currencyservice-1 metric=pod_cpu_usage baseline=0.0 peak=0.01 signed_z=10.97 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M6] rank=6 service=paymentservice-2 metric=pod_cpu_usage baseline=0.0 peak=0.01 signed_z=10.97 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M7] rank=7 service=shippingservice-0 metric=rrt baseline=1209.043684 peak=3668.55 signed_z=9.014 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:1267.35,88.97,-406,128.14,359.52,-368.72,73.53,1102.96,-1008.11,-79.06,-100.01,-23.24,206.96,-16.09,-151.82,-77.88,188.98,-7.28,-147.77,43.32,82.87,-136.6,2648.53,-2535.41,-119.02,187.29,-87.74,70.4,-66.62,-189.42,145.93,-6.14,54.39,48.32,-83.27,177.36,-163.17,-113.24
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M8] rank=8 service=node-1 metric=node_disk_write_time_seconds_total baseline=0.0 peak=0.01 signed_z=8.595 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.01,-0.01,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M9] rank=9 service=productcatalogservice-0 metric=client_error_ratio baseline=0.0 peak=1.6 signed_z=8.228 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.6,-1.6,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M10] rank=10 service=productcatalogservice-0 metric=error_ratio baseline=0.0 peak=1.6 signed_z=8.228 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1.6,-1.6,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M11] rank=11 service=productcatalogservice metric=client_error_ratio baseline=0.0 peak=0.11 signed_z=8.228 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.11,-0.11,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1
[M12] rank=12 service=productcatalogservice metric=error_ratio baseline=0.0 peak=0.11 signed_z=8.228 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.11,-0.11,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010100101010010101001010010101001010100101001010100101010010100
observed_counts_compact=csv:1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1260.0]

=== LOG SUMMARY ===
{"entries":[{"change_pct":-100.0,"n_during":0,"n_pre":35,"service":"redis-cart-0"},{"change_pct":-95.6,"n_during":30,"n_pre":675,"service":"checkoutservice-1"},{"change_pct":-95.3,"n_during":10,"n_pre":212,"service":"emailservice-2"},{"change_pct":-95.3,"n_during":20,"n_pre":424,"service":"paymentservice-2"},{"change_pct":-95.2,"n_during":10,"n_pre":210,"service":"emailservice-0"},{"change_pct":-95.2,"n_during":20,"n_pre":420,"service":"paymentservice-0"},{"change_pct":-95.2,"n_during":40,"n_pre":840,"service":"shippingservice-0"},{"change_pct":-95.2,"n_during":92,"n_pre":1936,"service":"shippingservice-1"}],"mode":"volume","omitted_services":16,"service_count":24}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":17.3,"error_pct":0.0,"p95_during_ms":3.9833999999999956,"p95_pre_ms":3.3952999999999993,"service":"redis","spans":16464},{"delta_pct":15.6,"error_pct":0.0,"p95_during_ms":5.7769,"p95_pre_ms":4.998599999999999,"service":"cartservice","spans":15171},{"delta_pct":8.3,"error_pct":0.0,"p95_during_ms":103.72004999999989,"p95_pre_ms":95.74839999999999,"service":"frontend","spans":185465},{"delta_pct":-6.7,"error_pct":0.0,"p95_during_ms":0.4722999999999994,"p95_pre_ms":0.506,"service":"shippingservice","spans":4436},{"delta_pct":-6.3,"error_pct":0.0,"p95_during_ms":1.0285,"p95_pre_ms":1.0978499999999984,"service":"emailservice","spans":633},{"delta_pct":5.1,"error_pct":0.0,"p95_during_ms":196.98295,"p95_pre_ms":187.37854999999996,"service":"checkoutservice","spans":7470},{"delta_pct":2.6,"error_pct":0.0,"p95_during_ms":97.132,"p95_pre_ms":94.67715,"service":"recommendationservice","spans":22804},{"delta_pct":-0.4,"error_pct":0.0,"p95_during_ms":13.8371,"p95_pre_ms":13.898,"service":"productcatalogservice","spans":85680}],"omitted_services":0,"service_count":8}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=7 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"node-7","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"paymentservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":3,"service":"tidb-tikv","severity_z":999.0},{"evidence_source":"trace","onset_rel_s":1641.6,"rank":4,"service":"emailservice","severity_z":17.497},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":5,"service":"node-8","severity_z":19.208},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":6,"service":"currencyservice","severity_z":10.97},{"evidence_source":"none","onset_rel_s":null,"rank":7,"service":"shippingservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":8,"service":"productcatalogservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":9,"service":"adservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":10,"service":"tidb-tidb","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":11,"service":"redis-cart","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":12,"service":"recommendationservice","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":13,"service":"k8s-master1","severity_z":0.0},{"evidence_source":"none","onset_rel_s":null,"rank":14,"service":"k8s-master3","severity_z":0.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"productcatalogservice","caller":"recommendationservice"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank productcatalogservice-0 first because productcatalogservice-0 has direct client_error_ratio evidence (signed-z 8.23, persistence 0 bins); although recommendationservice is salient, the caller path recommendationservice -> productcatalogservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["productcatalogservice-0","node-7","paymentservice-2","node-8","tidb-tikv"]}

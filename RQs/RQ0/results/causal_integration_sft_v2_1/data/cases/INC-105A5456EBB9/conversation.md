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
opaque_id: INC-105A5456EBB9
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1670,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice-2 metric=container_cpu_cfs_throttled_seconds baseline=0.000245 peak=1.320444 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=4
values_compact=delta:0.004908,-0.004908,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.008899,0.136658,0,-0.145557,0,0,0,0,0,0,0,0,1.320444,-1.316446
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice2 metric=jvm_classes_loaded baseline=0.0 peak=14.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,14,-14,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101011111111100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,0,0,0,0,0,0,0,0,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice metric=jvm_classes_loaded baseline=0.0 peak=13.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,13,-13,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101011111111100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,0,0,0,0,0,0,0,0,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=cartservice-2 metric=container_fs_inodes./dev/vda1 baseline=0.0 peak=2.0 signed_z=999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,-2,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=cartservice-2 metric=container_memory_failcnt baseline=2122.0 peak=0.0 signed_z=-999.0 onset_bin=54 onset_rel_s=1992.656 persistence_bins=7
values_compact=delta:2122,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1061,-1061,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=cartservice-2 metric=istio_request_bytes.grpc.200.14.0 baseline=0.0 peak=655.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,655,0,-655,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=cartservice-2 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=50.23875 peak=135026.8125 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:39.1125,4.4625,-1.8375,-2.65,5.2625,8.1375,-0.5125,0.7875,-0.525,2.1,2.3625,-6.3,4.725,-0.525,-2.3625,3.4125,-4.2125,1.8375,-2.0875,1.3125,-1.575,-0.2625,1.575,1.3125,-4.725,3.9375,-0.525,2.075,-1.55,1.575,-1.575,-0.7875,-0.525,134975.3625,-134970.25,5.6,-1.8375,-0.5375,-7.2875,2.8875
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=cartservice-2 metric=istio_request_duration_milliseconds.grpc.200.14.0 baseline=0.0 peak=725.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,725,0,-725,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=cartservice-2 metric=istio_requests.grpc.200.14.0 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,-1,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=cartservice-2 metric=istio_response_bytes.grpc.200.14.0 baseline=0.0 peak=1250.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1250,0,-1250,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=frontend-0 metric=istio_request_bytes.grpc.200.14.0 baseline=0.0 peak=74250.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,74250,0,-63450,4050,-14850,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=frontend-0 metric=istio_requests.grpc.200.14.0 baseline=0.0 peak=55.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=3
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,55,0,-47,3,-11,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1560.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":4297,"error_pct":9.09,"service":"adservice-0","total_logs":47263},{"error_logs":1830,"error_pct":2.01,"service":"frontend-0","total_logs":91228},{"error_logs":1080,"error_pct":2.03,"service":"frontend-2","total_logs":53206},{"error_logs":933,"error_pct":1.99,"service":"frontend-1","total_logs":46826},{"error_logs":89,"error_pct":1.56,"service":"adservice-1","total_logs":5718},{"error_logs":32,"error_pct":0.66,"service":"adservice-2","total_logs":4870},{"error_logs":2,"error_pct":0.08,"service":"checkoutservice-2","total_logs":2540}],"mode":"errors","omitted_services":24,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":992.3,"error_pct":0.26,"p95_during_ms":500.142,"p95_pre_ms":45.78679999999999,"service":"frontend-2","spans":37587},{"delta_pct":991.9,"error_pct":0.25,"p95_during_ms":500.141,"p95_pre_ms":45.80394999999999,"service":"frontend-1","spans":33102},{"delta_pct":988.2,"error_pct":0.27,"p95_during_ms":500.141,"p95_pre_ms":45.958549999999995,"service":"frontend-0","spans":64905},{"delta_pct":972.1,"error_pct":0.0,"p95_during_ms":500.156,"p95_pre_ms":46.653549999999996,"service":"frontend2-0","spans":65505},{"delta_pct":-82.2,"error_pct":0.0,"p95_during_ms":36.36875,"p95_pre_ms":204.53560000000002,"service":"checkoutservice-2","spans":1797},{"delta_pct":-59.4,"error_pct":0.0,"p95_during_ms":36.75744999999999,"p95_pre_ms":90.4585,"service":"checkoutservice-0","spans":1828},{"delta_pct":-22.0,"error_pct":0.0,"p95_during_ms":37.748999999999995,"p95_pre_ms":48.40859999999977,"service":"checkoutservice2-0","spans":2629},{"delta_pct":20.4,"error_pct":0.0,"p95_during_ms":0.030099999999999995,"p95_pre_ms":0.025,"service":"adservice-1","spans":2099}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":1194.6,"rank":1,"service":"frontend","severity_z":107.778},{"evidence_source":"trace","onset_rel_s":1194.6,"rank":2,"service":"frontend2","severity_z":106.041},{"evidence_source":"trace","onset_rel_s":1340.4,"rank":3,"service":"paymentservice2","severity_z":30.418},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":4,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":5,"service":"paymentservice","severity_z":139.679},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":6,"service":"emailservice","severity_z":88.46},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":7,"service":"emailservice2","severity_z":72.916},{"evidence_source":"trace","onset_rel_s":1535.4,"rank":8,"service":"adservice","severity_z":5.245},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":9,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":10,"service":"node-6","severity_z":808.117},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":11,"service":"currencyservice2","severity_z":259.28},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":12,"service":"productcatalogservice2","severity_z":229.816},{"evidence_source":"metric","onset_rel_s":2100.0,"rank":13,"service":"recommendationservice2","severity_z":158.065},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":14,"service":"shippingservice","severity_z":57.695}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"shippingservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"currencyservice2","caller":"frontend2"},{"callee":"productcatalogservice2","caller":"frontend2"},{"callee":"recommendationservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank adservice first because adservice has direct container_cpu_cfs_throttled_seconds evidence (signed-z 999, persistence 4 bins); although frontend-0 is salient, the caller path frontend -> adservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["adservice","node-6","cartservice-2","frontend-0","frontend-2"]}

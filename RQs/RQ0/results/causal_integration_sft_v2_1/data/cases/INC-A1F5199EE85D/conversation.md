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
opaque_id: INC-A1F5199EE85D
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1603,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-zpjpg","istio-ingressgateway-565bffd4d-6bl7m","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=adservice2 metric=java_lang_Compilation_TotalCompilationTime baseline=62169.0 peak=62893.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:62169,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3.083333,45.666667,13.166667,20.083333,24.75,17.75,11.5,85.833333,120.166667,0,0,40.5,31.833333,4.166667,3.5,248.333333,49.666667,3,1
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=adservice2 metric=jvm_classes_loaded baseline=0.0 peak=5157.0 signed_z=999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5157,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=adservice metric=jvm_classes_loaded baseline=0.0 peak=5162.0 signed_z=999.0 onset_bin=59 onset_rel_s=2175.469 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5162,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=cartservice-2 metric=istio_request_duration_milliseconds.grpc.200.0.0 baseline=66.465 peak=19809.9625 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:67.5375,0.95,4.8625,-7.2625,1.2375,-3.65,4.1875,-3.6625,3.425,-2.575,2.8,-1.7875,2.575,-2.3875,-2.0125,0.825,-1.05,2.9125,-2.925,1.0625,5248.7625,7780.8375,6715.3,-9064.2125,-1986.6375,-8703.4,-4.3,-2.0625,2.0875,2.0375,-1.5125,-0.55,2.4625,-2.4375,4.65,0,1,0.4125,-4.25,4.075
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=cartservice2-0 metric=container_cpu_cfs_throttled_seconds baseline=0.0 peak=0.016754 signed_z=999.0 onset_bin=44 onset_rel_s=1627.031 persistence_bins=2
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.016754,0,-0.016754,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=cartservice2-0 metric=istio_tcp_received_bytes.- baseline=36.9 peak=7689.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=18
values_compact=delta:39,0,-7,7,0,-7,7,0,-7,7,0,-7,7,0,-7,7,0,-7,7,0,-7,40.5,1041.5,937.5,3913.5,927,-93.5,142,106,-329.5,721,-1018.5,573.5,340.5,-1442.5,0,1277.5,-706,631.5,595
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=checkoutservice-0 metric=istio_request_bytes.grpc.200.13.0 baseline=0.0 peak=785.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,785,-785,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=checkoutservice-0 metric=istio_request_duration_milliseconds.grpc.200.13.0 baseline=0.0 peak=5750.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5750,-5750,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=checkoutservice-0 metric=istio_requests.grpc.200.13.0 baseline=0.0 peak=1.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=checkoutservice-0 metric=istio_response_bytes.grpc.200.13.0 baseline=0.0 peak=2150.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2150,-2150,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=checkoutservice-1 metric=istio_request_bytes.grpc.200.13.0 baseline=0.0 peak=1570.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1570,-1570,785,-785,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=checkoutservice-1 metric=istio_request_duration_milliseconds.grpc.200.13.0 baseline=0.0 peak=15000.0 signed_z=999.0 onset_bin=None onset_rel_s=None persistence_bins=0
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,15000,-15000,8950,-8950,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1620.0,2340.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":176,"error_pct":0.41,"service":"cartservice-1","total_logs":43025},{"error_logs":168,"error_pct":0.39,"service":"cartservice-2","total_logs":43015},{"error_logs":102,"error_pct":0.11,"service":"frontend-1","total_logs":95916},{"error_logs":96,"error_pct":0.22,"service":"cartservice-0","total_logs":42681},{"error_logs":80,"error_pct":0.15,"service":"frontend-2","total_logs":54723},{"error_logs":41,"error_pct":0.08,"service":"frontend-0","total_logs":48386}],"mode":"errors","omitted_services":25,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":-34.7,"error_pct":0.0,"p95_during_ms":43.4531,"p95_pre_ms":66.57549999999972,"service":"checkoutservice2-0","spans":686},{"delta_pct":-21.8,"error_pct":0.0,"p95_during_ms":45.135049999999985,"p95_pre_ms":57.697,"service":"checkoutservice-1","spans":2064},{"delta_pct":11.0,"error_pct":0.0,"p95_during_ms":0.028850000000000025,"p95_pre_ms":0.026,"service":"adservice2-0","spans":899},{"delta_pct":8.7,"error_pct":0.0,"p95_during_ms":0.0815,"p95_pre_ms":0.075,"service":"shippingservice-2","spans":1214},{"delta_pct":8.4,"error_pct":0.0,"p95_during_ms":0.2793999999999998,"p95_pre_ms":0.25775000000000003,"service":"emailservice-0","spans":175},{"delta_pct":7.5,"error_pct":0.0,"p95_during_ms":0.085,"p95_pre_ms":0.07909999999999999,"service":"shippingservice2-0","spans":414},{"delta_pct":-6.6,"error_pct":0.0,"p95_during_ms":0.167,"p95_pre_ms":0.17875,"service":"paymentservice2-0","spans":59},{"delta_pct":-6.0,"error_pct":0.0,"p95_during_ms":43.865,"p95_pre_ms":46.661,"service":"checkoutservice-0","spans":2057}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=16 omitted_edges=0
[{"evidence_source":"metric","onset_rel_s":1200.0,"rank":1,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":2,"service":"cartservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":3,"service":"checkoutservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":4,"service":"redis-cart2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1440.0,"rank":5,"service":"frontend2","severity_z":941.284},{"evidence_source":"metric","onset_rel_s":1620.0,"rank":6,"service":"cartservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1680.0,"rank":7,"service":"node-1","severity_z":845.588},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":8,"service":"adservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":9,"service":"adservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":10,"service":"istio-egressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":11,"service":"istio-ingressgateway","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":12,"service":"node-6","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":2160.0,"rank":13,"service":"recommendationservice","severity_z":655.9},{"evidence_source":"metric","onset_rel_s":2220.0,"rank":14,"service":"node-2","severity_z":999.0}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"cartservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank cartservice-0 first because cartservice-0 has direct log evidence; although frontend-0 is salient, the caller path frontend -> cartservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["cartservice-0","cartservice-2","cartservice-1","checkoutservice-0","frontend-0"]}

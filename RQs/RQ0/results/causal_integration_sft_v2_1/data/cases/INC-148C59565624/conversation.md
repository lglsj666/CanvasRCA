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
opaque_id: INC-148C59565624
observation_window={"duration_rel_s":2340.0,"source_metric_rows":40}
selection_summary={"candidate_count":63,"hot_z_threshold":10.0,"metric_ranker":"ksigma","metric_series_scored":1619,"metric_series_shown":12}

=== CANDIDATES (fixed order) ===
["adservice","adservice-0","adservice-1","adservice-2","adservice-grpc","adservice-http","adservice2","adservice2-0","cartservice-0","cartservice-1","cartservice-2","cartservice-grpc","cartservice2-0","checkoutservice-0","checkoutservice-1","checkoutservice-2","checkoutservice-grpc","checkoutservice2-0","currencyservice-0","currencyservice-1","currencyservice-2","currencyservice-grpc","currencyservice2-0","emailservice-0","emailservice-1","emailservice-2","emailservice-grpc","emailservice2-0","frontend-0","frontend-1","frontend-2","frontend-http","frontend2-0","istio-egressgateway-7bfdcc9d86-g2d4q","istio-ingressgateway-565bffd4d-rn678","node-1","node-2","node-3","node-4","node-5","node-6","paymentservice-0","paymentservice-1","paymentservice-2","paymentservice-grpc","paymentservice2-0","productcatalogservice-0","productcatalogservice-1","productcatalogservice-2","productcatalogservice-grpc","productcatalogservice2-0","recommendationservice-0","recommendationservice-1","recommendationservice-2","recommendationservice-grpc","recommendationservice2-0","redis-cart-0","redis-cart2-0","shippingservice-0","shippingservice-1","shippingservice-2","shippingservice-grpc","shippingservice2-0"]

=== METRIC SERIES (all 64 bins; null=missing) ===
shared_bin_centers_rel_s=[18.281,54.844,91.406,127.969,164.531,201.094,237.656,274.219,310.781,347.344,383.906,420.469,457.031,493.594,530.156,566.719,603.281,639.844,676.406,712.969,749.531,786.094,822.656,859.219,895.781,932.344,968.906,1005.469,1042.031,1078.594,1115.156,1151.719,1188.281,1224.844,1261.406,1297.969,1334.531,1371.094,1407.656,1444.219,1480.781,1517.344,1553.906,1590.469,1627.031,1663.594,1700.156,1736.719,1773.281,1809.844,1846.406,1882.969,1919.531,1956.094,1992.656,2029.219,2065.781,2102.344,2138.906,2175.469,2212.031,2248.594,2285.156,2321.719]
[M1] rank=1 service=checkoutservice-0 metric=istio_request_bytes.grpc.200.13.0 baseline=0.0 peak=3925.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1962.5,785,-1570,2747.5,-2747.5,1177.5,-2355,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M2] rank=2 service=checkoutservice-0 metric=istio_request_duration_milliseconds.grpc.200.13.0 baseline=0.0 peak=132000.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,46250,20500,-6500,71750,-96250,3750,-39500,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M3] rank=3 service=checkoutservice-0 metric=istio_request_duration_milliseconds.http.202. baseline=0.365 peak=26690.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=5
values_compact=delta:1.55,0,-1.55,0,0,0,0,0,0.525,1.05,-1.575,0.525,0,-0.525,0,0,0,0,1.05,-1.05,11.5,3628.5,8290,14760,-1540,-25146.85,-1.05,-1.05,-1.05,0,0,0,0,0,0,0,0,1.05,-1.05,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M4] rank=4 service=checkoutservice-0 metric=istio_requests.grpc.200.13.0 baseline=0.0 peak=5.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2.5,1,-2,3.5,-3.5,1.5,-3,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M5] rank=5 service=checkoutservice-0 metric=istio_response_bytes.grpc.200.13.0 baseline=0.0 peak=7050.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3675,1450,-3000,4925,-4925,2225,-4350,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M6] rank=6 service=checkoutservice-1 metric=istio_request_bytes.grpc.200.13.0 baseline=0.0 peak=3925.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2747.5,-1177.5,2355,-2355,-392.5,-1177.5,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M7] rank=7 service=checkoutservice-1 metric=istio_request_duration_milliseconds.grpc.200.13.0 baseline=0.0 peak=122200.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,62300,-17300,77200,-92000,10050,-40250,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M8] rank=8 service=checkoutservice-1 metric=istio_request_duration_milliseconds.http.202. baseline=2.40375 peak=34915.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0.525,-0.525,0,0.525,0,-0.525,0,0,0,0,0,0,23.25,0,-23.25,0,0,0,0,0,0,9225,-8075,12510,21255,-27261.85,-7651.575,0,-1.575,0,0,1.575,0,-1.575,0,1.05,-1.05,0.525,0,-0.525
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M9] rank=9 service=checkoutservice-1 metric=istio_requests.grpc.200.13.0 baseline=0.0 peak=5.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.5,2.5,-1,3,-3,-0.5,-1.5,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M10] rank=10 service=checkoutservice-1 metric=istio_response_bytes.grpc.200.13.0 baseline=0.0 peak=7050.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5025,-2175,4200,-4200,-825,-2025,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M11] rank=11 service=checkoutservice-2 metric=istio_request_bytes.grpc.200.13.0 baseline=0.0 peak=2747.5 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1177.5,1570,-785,785,-2355,2355,-2747.5,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1
[M12] rank=12 service=checkoutservice-2 metric=istio_request_duration_milliseconds.grpc.200.13.0 baseline=0.0 peak=74250.0 signed_z=999.0 onset_bin=36 onset_rel_s=1334.531 persistence_bins=4
values_compact=delta:0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,25750,41000,-13000,20500,-44500,22300,-52050,0,0,0,0,0,0,0,0,0,0,0,0,0
missing_mask_bits=0010010100101001010010010100101001010010100100101001010010100100
observed_counts_compact=csv:1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1

=== ESTIMATED FAULT WINDOW (relative seconds) ===
[1140.0,1560.0]

=== LOG SUMMARY ===
{"entries":[{"error_logs":4292,"error_pct":9.0,"service":"adservice-0","total_logs":47684},{"error_logs":768,"error_pct":1.34,"service":"frontend-2","total_logs":57521},{"error_logs":715,"error_pct":1.32,"service":"frontend-1","total_logs":53990},{"error_logs":710,"error_pct":1.33,"service":"frontend-0","total_logs":53523}],"mode":"errors","omitted_services":27,"service_count":31}
=== TRACE SUMMARY ===
{"entries":[{"delta_pct":61055.9,"error_pct":0.0,"p95_during_ms":22877.148549999965,"p95_pre_ms":37.4079,"service":"checkoutservice-0","spans":1492},{"delta_pct":53399.3,"error_pct":0.0,"p95_during_ms":20000.43285,"p95_pre_ms":37.384499999999996,"service":"checkoutservice-2","spans":1528},{"delta_pct":53033.3,"error_pct":0.0,"p95_during_ms":20000.431,"p95_pre_ms":37.641999999999996,"service":"checkoutservice-1","spans":1549},{"delta_pct":26585.8,"error_pct":0.0,"p95_during_ms":20000.484650000002,"p95_pre_ms":74.948,"service":"checkoutservice2-0","spans":1460},{"delta_pct":279.4,"error_pct":0.0,"p95_during_ms":0.5467500000000001,"p95_pre_ms":0.14409999999999998,"service":"paymentservice-0","spans":125},{"delta_pct":11.4,"error_pct":0.0,"p95_during_ms":0.039,"p95_pre_ms":0.035,"service":"adservice2-0","spans":2024},{"delta_pct":-10.6,"error_pct":0.0,"p95_during_ms":0.212,"p95_pre_ms":0.23719999999999997,"service":"emailservice-0","spans":126},{"delta_pct":8.8,"error_pct":0.0,"p95_during_ms":74.44749999999956,"p95_pre_ms":68.4049999999996,"service":"frontend2-0","spans":37036}],"omitted_services":32,"service_count":40}

=== PROPAGATION SERVICES ===
mode=onset omitted_services=14 omitted_edges=0
[{"evidence_source":"trace","onset_rel_s":1194.6,"rank":1,"service":"checkoutservice","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1200.0,"rank":2,"service":"node-5","severity_z":235.929},{"evidence_source":"trace","onset_rel_s":1243.2,"rank":3,"service":"checkoutservice2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":4,"service":"frontend","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1260.0,"rank":5,"service":"frontend2","severity_z":999.0},{"evidence_source":"metric","onset_rel_s":1320.0,"rank":6,"service":"recommendationservice","severity_z":58.487},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":7,"service":"emailservice","severity_z":272.39},{"evidence_source":"metric","onset_rel_s":1380.0,"rank":8,"service":"emailservice2","severity_z":215.92},{"evidence_source":"metric","onset_rel_s":1500.0,"rank":9,"service":"redis-cart2","severity_z":75.863},{"evidence_source":"metric","onset_rel_s":1560.0,"rank":10,"service":"adservice","severity_z":74.518},{"evidence_source":"metric","onset_rel_s":1740.0,"rank":11,"service":"cartservice","severity_z":106.076},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":12,"service":"shippingservice2","severity_z":113.936},{"evidence_source":"metric","onset_rel_s":1920.0,"rank":13,"service":"istio-egressgateway","severity_z":72.727},{"evidence_source":"metric","onset_rel_s":2040.0,"rank":14,"service":"adservice2","severity_z":46.952}]
=== DIRECTED CALL EDGES (caller -> callee) ===
[{"callee":"cartservice","caller":"checkoutservice"},{"callee":"emailservice","caller":"checkoutservice"},{"callee":"emailservice2","caller":"checkoutservice2"},{"callee":"shippingservice2","caller":"checkoutservice2"},{"callee":"adservice","caller":"frontend"},{"callee":"cartservice","caller":"frontend"},{"callee":"checkoutservice","caller":"frontend"},{"callee":"recommendationservice","caller":"frontend"},{"callee":"adservice2","caller":"frontend2"},{"callee":"checkoutservice2","caller":"frontend2"},{"callee":"shippingservice2","caller":"frontend2"}]

=== EXPLICIT MISSINGNESS ===
{"logs_missing":false,"propagation_missing":false,"traces_missing":false}

Return only one JSON object, with no analysis, preamble, markdown, or code fence:
{"services":["name1","name2","name3"],"reason":"one sentence citing the strongest metric/log/topology evidence","confidence":"high|medium|low"}
The services array must be ranked, contain at most five exact candidate
identifiers, and put the most likely root cause first.

# Assistant target

{"confidence":"high","reason":"Rank checkoutservice-0 first because checkoutservice-0 has direct istio_request_bytes.grpc.200.13.0 evidence (signed-z 999, persistence 4 bins); although frontend-0 is salient, the caller path frontend -> checkoutservice means a disturbance in the callee can propagate back toward that caller-side symptom. The remaining entries preserve evidence-supported alternatives so the ranking retains calibrated uncertainty instead of collapsing to one answer.","services":["checkoutservice-0","node-5","checkoutservice-1","checkoutservice-2","frontend-0"]}
